"""Case-scoped TME access to the existing submission and audit services."""
import base64
import binascii
import json
from typing import Optional, Literal
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.core.problem_catalog import list_problem_catalog, list_tme_problem_catalog
from confia_lean_auditor.recognition.registry import configured_registry, UnknownRecognizer
from confia_lean_auditor.recognition.schemas import RecognitionRequest, RecognitionResponse, RecognitionRun
from confia_lean_auditor.recognition.service import RecognitionService
from confia_lean_auditor.recognition.preview import PreviewError, PreviewRequest, PreviewResponse, recognize_preview
from confia_lean_auditor.submissions.router import store as submission_store, guarded
from confia_lean_auditor.submissions.schemas import (
    CaptureSnapshot, SubmissionRequest, MAX_REQUEST_BYTES, SubmissionDetail,
    TranscriptionSummary, TranscriptionHistory, TranscriptionRevision, AcceptedTranscription,
    CreateTranscriptionRevisionRequest, AcceptTranscriptionRequest,
)
from confia_lean_auditor.submissions.body_limit import MAX_TRANSCRIPTION_BODY_BYTES
from confia_lean_auditor.submissions.store import SubmissionTooLarge
from confia_lean_auditor.submission_audits.router import service as audit_service, public_operation
from confia_lean_auditor.submission_audits.schemas import AuditRequest
from confia_lean_auditor.teacher_decisions.service import audit_snapshot
from .models import (CaseCreate, CorrectionCase, EvaluatorDecision, EvaluatorDecisionRequest,
                     ScanPage, ScanSnapshot, ScanUpload)
from .store import case_store
from .auth import require_tme_evaluator
from .home_summary import HomeSummary, OperationalIndex, Period
from .recognition_status import recognition_feedback, failure_feedback

router = APIRouter(prefix="/tme", tags=["TME pilot"])


def case_for(case_id, user):
    try:
        case = case_store().for_user(case_id, user)
        if case.submission_id:
            record = submission_store().get_record(case.submission_id)
            if (record.tme_case_id != case_id or record.problem_id != case.problem_id
                    or record.source != ("exam_pages" if case.exam_submission_id else "tablet" if case.source_mode == "DIGITAL_INK" else "image_scan")
                    or record.submitted_by_user_id != user.user_id):
                raise ValueError("case/source binding mismatch")
        return case
    except FileNotFoundError:
        raise HTTPException(404, "Correção não encontrada.") from None
    except (ValidationError, ValueError, OSError):
        raise HTTPException(409, "Integridade da correção inválida.") from None


async def bounded_json(request, maximum=MAX_REQUEST_BYTES):
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
        raise HTTPException(415, "Use application/json.")
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > maximum:
            raise HTTPException(413, "Payload acima do limite permitido.")
        raw.extend(chunk)
    return bytes(raw)


async def parsed_body(request, model, **defaults):
    raw = await bounded_json(request, MAX_TRANSCRIPTION_BODY_BYTES)
    try:
        data = json.loads(raw)
        return model.model_validate({**defaults, **data})
    except (ValueError, TypeError):
        raise HTTPException(422, "Dados da correção inválidos.") from None


def source_for(case_id, user):
    case = case_for(case_id, user)
    if not case.submission_id:
        raise HTTPException(409, "Envie a solução antes de continuar.")
    return case.submission_id


def transcription_for(case_id, transcription_id, user):
    submission_id = source_for(case_id, user)
    history = guarded(submission_store().transcription_history, transcription_id)
    if history.transcription.submission_id != submission_id:
        raise HTTPException(404, "Transcrição não encontrada nesta correção.")
    return history


@router.get("/home-summary", response_model=HomeSummary)
def home_summary(response: Response, period: Period = "today", user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    try:
        return OperationalIndex().summary(user.user_id, period)
    except (OSError, ValueError, KeyError, TypeError):
        raise HTTPException(503, "Não foi possível carregar os indicadores.",
                            headers={"Cache-Control": "no-store"}) from None


@router.get("/problems")
def problems(response: Response, _user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    return list_problem_catalog(get_repo_root()) + list_tme_problem_catalog(get_repo_root())


@router.get("/cases/{case_id}/capture", include_in_schema=False)
def notebook(case_id: str, user=Depends(require_tme_evaluator)):
    case = case_for(case_id, user)
    if case.source_mode != "DIGITAL_INK":
        raise HTTPException(409, "Esta correção não utiliza caderno digital.")
    from confia_lean_auditor.main import STATIC_DIR
    return FileResponse(STATIC_DIR / "capture" / "tablet.html", headers={"Cache-Control": "no-store"})


@router.post("/cases/{case_id}/recognition-preview", response_model=PreviewResponse)
async def preview(case_id: str, request: Request, response: Response, user=Depends(require_tme_evaluator)):
    case = case_for(case_id, user)
    body = await parsed_body(request, PreviewRequest)
    try:
        snapshot = CaptureSnapshot.model_validate_json(body.snapshot_json)
        if case.source_mode != "DIGITAL_INK" or snapshot.problem_id != case.problem_id:
            raise ValueError("case/snapshot mismatch")
        result = await run_in_threadpool(recognize_preview, body, configured_registry())
    except UnknownRecognizer:
        raise HTTPException(503, "Reconhecimento indisponível neste ambiente.") from None
    except PreviewError as exc:
        status = 422 if str(exc) in {"INVALID_SNAPSHOT", "INVALID_PROVIDER", "INVALID_PROVIDER_OUTPUT"} else 503
        raise HTTPException(status, str(exc)) from None
    except ValueError:
        raise HTTPException(422, "Caderno ou questão inválida.") from None
    response.headers["Cache-Control"] = "no-store"
    return result


@router.get("/cases/{case_id}/submission", response_model=SubmissionDetail)
def submission(case_id: str, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(submission_store().detail, source_for(case_id, user))


@router.get("/cases/{case_id}/pages/{page_index}")
def page(case_id: str, page_index: int, user=Depends(require_tme_evaluator)):
    path, ref = guarded(submission_store().artifact, source_for(case_id, user), page_index)
    return FileResponse(path, media_type="image/png", filename=ref.filename,
        content_disposition_type="inline",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/cases/{case_id}/recognitions/{recognizer_run_id}", response_model=RecognitionRun)
def recognition(case_id: str, recognizer_run_id: str, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(RecognitionService(submission_store(), configured_registry()).get,
                   source_for(case_id, user), recognizer_run_id)


@router.get("/cases/{case_id}/recognition-status")
def recognition_status(case_id: str, response: Response, user=Depends(require_tme_evaluator)):
    case = case_for(case_id, user)
    registry = configured_registry()
    provider = "mathpix_image" if case.source_mode == "IMAGE_SCAN" else "mathpix"
    runs = guarded(RecognitionService(submission_store(), registry).list, case.submission_id) if case.submission_id else []
    response.headers["Cache-Control"] = "no-store"
    return recognition_feedback(runs[0] if runs else None, configured=provider in registry.providers())


@router.get("/cases/{case_id}/scan-manifest", response_model=ScanSnapshot)
def scan_manifest(case_id: str, response: Response, user=Depends(require_tme_evaluator)):
    case = case_for(case_id, user)
    if case.source_mode != "IMAGE_SCAN" or not case.submission_id:
        raise HTTPException(404, "Páginas não encontradas.")
    # The original timestamps/order/orientation are needed when adjusting a saved scan.
    path, _ = guarded(submission_store().artifact, case.submission_id)
    response.headers["Cache-Control"] = "no-store"
    return guarded(ScanSnapshot.model_validate_json, path.read_bytes())


@router.get("/cases/{case_id}/transcriptions", response_model=list[TranscriptionSummary])
def transcriptions(case_id: str, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(submission_store().list_transcriptions, source_for(case_id, user))


@router.get("/cases/{case_id}/transcriptions/{transcription_id}", response_model=TranscriptionHistory)
def transcription(case_id: str, transcription_id: str, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    return transcription_for(case_id, transcription_id, user)


@router.post("/cases/{case_id}/transcriptions/{transcription_id}/revisions",
             response_model=TranscriptionRevision, status_code=201)
async def revise(case_id: str, transcription_id: str, request: Request, response: Response,
                 user=Depends(require_tme_evaluator)):
    transcription_for(case_id, transcription_id, user)
    body = await parsed_body(request, CreateTranscriptionRevisionRequest, reviewer_reference=user.user_id)
    body = body.model_copy(update={"reviewer_reference": user.user_id})
    response.headers["Cache-Control"] = "no-store"
    if case_for(case_id, user).exam_submission_id:
        from .question_review import revise as revise_question
        from .exam_router import guarded as review_guarded
        return await run_in_threadpool(review_guarded, revise_question, case_id, transcription_id, body, user)
    return await run_in_threadpool(guarded, submission_store().create_transcription_revision, transcription_id, body)


@router.post("/cases/{case_id}/transcriptions/{transcription_id}/accept", response_model=AcceptedTranscription)
async def accept(case_id: str, transcription_id: str, request: Request, response: Response,
                 user=Depends(require_tme_evaluator)):
    transcription_for(case_id, transcription_id, user)
    body = await parsed_body(request, AcceptTranscriptionRequest, reviewer_reference=user.user_id)
    body = body.model_copy(update={"reviewer_reference": user.user_id})
    response.headers["Cache-Control"] = "no-store"
    return await run_in_threadpool(guarded, submission_store().accept_transcription, transcription_id, body)


@router.post("/cases/{case_id}/audits", response_model=dict)
async def execute_analysis(case_id: str, request: Request, response: Response, user=Depends(require_tme_evaluator)):
    submission_id = source_for(case_id, user)
    body = await parsed_body(request, AuditRequest)
    transcription_for(case_id, body.transcription_id, user)
    response.headers["Cache-Control"] = "no-store"
    if case_for(case_id, user).exam_submission_id:
        from .correction_engine import CorrectionEngine
        from .exam_router import guarded as review_guarded
        return await run_in_threadpool(review_guarded, CorrectionEngine().audit_question, case_id, body, user)
    return await run_in_threadpool(public_operation, audit_service().execute, submission_id, body)


@router.get("/cases/{case_id}/audits", response_model=list[dict])
def analyses(case_id: str, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    if case_for(case_id, user).exam_submission_id:
        from .question_review import workspace
        from .exam_router import guarded as review_guarded
        return review_guarded(workspace, case_id, user)["audits"]
    return public_operation(audit_service().list, source_for(case_id, user))


@router.get("", include_in_schema=False)
def home(_user=Depends(require_tme_evaluator)):
    from confia_lean_auditor.main import STATIC_DIR
    return FileResponse(STATIC_DIR / "tme" / "index.html", headers={"Cache-Control": "no-store"})


@router.post("/cases", response_model=CorrectionCase, status_code=201)
def create_case(body: CaseCreate, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    try:
        return case_store().create(body, user)
    except ValueError:
        raise HTTPException(422, "Questão ou identificação inválida.") from None


@router.get("/cases", response_model=None)
def list_cases(response: Response, user=Depends(require_tme_evaluator),
               view: Optional[Literal["queue", "exams", "results"]] = None,
               page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=100),
               search: str = Query("", max_length=80), question: str = Query("", max_length=100),
               status: Literal["", "pending", "in_progress", "inconclusive", "finalized"] = "",
               source: Literal["", "IMAGE_SCAN", "DIGITAL_INK"] = "",
               origin: Literal["", "real", "synthetic_demo"] = "",
               sample: Literal["", "selected"] = "",
               exam: str = Query("", max_length=80)):
    response.headers["Cache-Control"] = "no-store"
    if view:
        try:
            return OperationalIndex().listing(user.user_id, view, page=page, size=size,
                search=search, question=question, status=status, source=source, exam=exam, origin=origin, sample=sample)
        except (OSError, ValueError, KeyError, TypeError):
            raise HTTPException(503, "Não foi possível carregar os dados operacionais.",
                                headers={"Cache-Control": "no-store"}) from None
    return [c for c in case_store().list_for_user(user)
            if (not origin or c.data_origin == origin) and (not sample or c.demo_sample_groups)]


@router.get("/cases/{case_id}", response_model=CorrectionCase)
def get_case(case_id: str, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    return case_for(case_id, user)


@router.post("/cases/{case_id}/digital-submission")
async def digital_submission(case_id: str, request: Request, response: Response, user=Depends(require_tme_evaluator)):
    case = case_for(case_id, user)
    if case.source_mode != "DIGITAL_INK" or case.submission_id:
        raise HTTPException(409, "Esta correção não aceita novo caderno.")
    raw = await bounded_json(request)
    try:
        body = SubmissionRequest.model_validate_json(raw)
        if body.student_reference is not None:
            raise ValueError("candidate code belongs only to the case")
        if CaptureSnapshot.model_validate_json(body.snapshot_json).problem_id != case.problem_id:
            raise ValueError("question mismatch")
        receipt, created = await run_in_threadpool(submission_store().receive,
            body, user, None, None, case_id)
        case_store().bind(case_id, receipt.submission_id, user)
    except (ValidationError, ValueError):
        raise HTTPException(422, "Caderno ou questão inválida.") from None
    response.status_code = 201 if created else 200
    response.headers["Cache-Control"] = "no-store"
    return receipt


@router.post("/cases/{case_id}/scan")
async def upload_scan(case_id: str, request: Request, response: Response, user=Depends(require_tme_evaluator)):
    case = case_for(case_id, user)
    if case.source_mode != "IMAGE_SCAN" or case.submission_id or case.exam_submission_id:
        raise HTTPException(409, "Esta correção não aceita novas fotos.")
    raw = await bounded_json(request)
    try:
        body = ScanUpload.model_validate_json(raw)
        originals = [base64.b64decode(page.original_base64, validate=True) for page in body.pages]
        derived = [base64.b64decode(page.derived_png_base64, validate=True) for page in body.pages]
        snapshot = ScanSnapshot(snapshot_id=f"scan:{uuid4().hex}", problem_id=case.problem_id,
            pages=[ScanPage(page_id=f"scan-page:{index}", index=index,
                original_mime=page.original_mime, captured_at=page.captured_at,
                rotation_degrees=page.rotation_degrees, derived_width=page.derived_width,
                derived_height=page.derived_height) for index, page in enumerate(body.pages)])
        receipt = await run_in_threadpool(submission_store().receive_scan,
            snapshot, originals, derived, user, case_id)
        case_store().bind(case_id, receipt.submission_id, user)
    except SubmissionTooLarge:
        raise HTTPException(413, "Foto acima do limite de 8 MB.") from None
    except (ValidationError, ValueError, binascii.Error):
        raise HTTPException(422, "Foto inválida. Confira formato, tamanho e orientação.") from None
    response.status_code = 201
    response.headers["Cache-Control"] = "no-store"
    return receipt


@router.get("/cases/{case_id}/originals/{page_index}")
def original(case_id: str, page_index: int, user=Depends(require_tme_evaluator)):
    case = case_for(case_id, user)
    if not case.submission_id:
        raise HTTPException(404, "Página não encontrada.")
    detail = submission_store().detail(case.submission_id)
    if detail.submission.tme_case_id != case_id or detail.submission.source != "image_scan":
        raise HTTPException(409, "Fonte da correção divergente.")
    ref = next((r for r in detail.submission.scan_originals or [] if r.page_index == page_index), None)
    if ref is None or not next(i.matches for i in detail.integrity if i.filename == ref.filename):
        raise HTTPException(404, "Página não encontrada.")
    return FileResponse(submission_store()._folder(case.submission_id) / ref.filename,
        media_type=ref.media_type, content_disposition_type="inline",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@router.post("/cases/{case_id}/recognize", response_model=RecognitionResponse)
async def recognize(case_id: str, request: Request, response: Response, user=Depends(require_tme_evaluator)):
    case = case_for(case_id, user)
    if not case.submission_id and not case.exam_submission_id:
        raise HTTPException(409, "Envie a solução antes do reconhecimento.")
    provider = "mathpix_image" if case.source_mode == "IMAGE_SCAN" else "mathpix"
    body = await parsed_body(request, RecognitionRequest, provider=provider)
    if body.provider != provider:
        raise HTTPException(422, "Reconhecedor não corresponde à fonte selecionada.")
    registry = configured_registry()
    if provider not in registry.providers():
        feedback = failure_feedback("PROVIDER_NOT_CONFIGURED")
        return JSONResponse(status_code=503, content={**feedback, "detail": feedback["message"]},
                            headers={"Cache-Control": "no-store"})
    if case.exam_submission_id:
        from .question_review import recognize as recognize_question
        from .exam_router import guarded as review_guarded
        run, _ = await run_in_threadpool(review_guarded, recognize_question, case_id, body, user, registry)
    else:
        run, _ = await run_in_threadpool(guarded,
            RecognitionService(submission_store(), registry).recognize, case.submission_id, body)
    response.headers["Cache-Control"] = "no-store"
    return RecognitionResponse.from_run(run)


@router.post("/cases/{case_id}/decision", response_model=EvaluatorDecision, status_code=201)
def decide(case_id: str, body: EvaluatorDecisionRequest, response: Response, user=Depends(require_tme_evaluator)):
    case = case_for(case_id, user)
    if not case.submission_id or body.final_points > body.max_points:
        raise HTTPException(422, "Pontuação ou fonte inválida.")
    try:
        reviewed = submission_store().list_transcriptions(case.submission_id)
    except (ValueError, OSError):
        raise HTTPException(409, "Transcrição indisponível.") from None
    if not reviewed or reviewed[0].latest_revision.status != "ACCEPTED":
        raise HTTPException(409, "Confira a transcrição antes da decisão.")
    source_hash = result_hash = suggestion = None
    if body.audit_run_id:
        try:
            run = audit_service().get(body.audit_run_id)
        except (FileNotFoundError, ValueError, OSError):
            raise HTTPException(409, "Análise ConfIA indisponível.") from None
        if run.submission_id != case.submission_id or run.stale or run.status != "COMPLETED":
            raise HTTPException(409, "Análise não corresponde à transcrição atual.")
        try:
            snapshot = audit_snapshot(submission_store().get_record(case.submission_id),
                                      body.audit_run_id, Decimal(str(body.max_points)))
        except (ValueError, OSError):
            raise HTTPException(409, "Análise ConfIA indisponível.") from None
        source_hash = snapshot["audit_source_sha256"]
        result_hash = snapshot["audit_result_sha256"]
        suggestion = snapshot["confia_suggested_points"]
    if suggestion is not None and Decimal(str(body.final_points)) != suggestion and not body.override_reason:
        raise HTTPException(422, "Informe o motivo da decisão diferente da sugestão.")
    decision = EvaluatorDecision(**body.model_dump(), case_id=case_id,
        decided_by_user_id=user.user_id, decided_at=datetime.now(timezone.utc),
        audit_source_sha256=source_hash, audit_result_sha256=result_hash,
        suggested_points=suggestion)
    try:
        case_store().decide(case_id, decision, user)
    except ValueError:
        raise HTTPException(409, "Decisão já registrada ou correção inválida.") from None
    response.headers["Cache-Control"] = "no-store"
    return decision


@router.get("/cases/{case_id}/decision", response_model=Optional[EvaluatorDecision])
def get_decision(case_id: str, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    case_for(case_id, user)
    return case_store().decision(case_id, user)


from .exam_router import router as exam_router
router.include_router(exam_router)
