"""D1 APIs, protected exclusively by the existing evaluator authorization."""
from datetime import datetime, timezone
import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from confia_lean_auditor.assessments.models import AssessmentDocument, CreateAssessmentItem
from confia_lean_auditor.assessments.store import assessment_store, AssessmentConflict
from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.core.problem_catalog import list_problem_catalog, list_tme_problem_catalog
from .auth import require_tme_evaluator, demo_no_auth_enabled, DEMO_EVALUATOR_ID
from .store import case_store
from .exam_capture import CaptureError
from confia_lean_auditor.submissions.store import TranscriptionConflict, SubmissionConflict
from .exam_models import (ExamCapturePackage, ExamDetail, ExamPage, PageMapping,
    QuestionAttemptView, UpdatePageMapping, TMEAssessmentCreate, MAX_CAPTURE_BODY)
from .exam_store import exam_store, ExamConflict

router = APIRouter()


def guarded(operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(404, "Prova, avaliação ou questão não encontrada.") from None
    except CaptureError as exc:
        raise HTTPException(422, str(exc)) from None
    except (ExamConflict, AssessmentConflict, TranscriptionConflict, SubmissionConflict):
        raise HTTPException(409, "Conflito na prova ou associação. Recarregue os dados e confira o envio.") from None
    except (ValidationError, ValueError):
        raise HTTPException(422, "Dados da prova inválidos.") from None
    except OSError:
        raise HTTPException(503, "Armazenamento da prova indisponível.") from None


def create_assessment(body, user, assessment_id=None):
    available = {p["problem_id"] for p in list_problem_catalog(get_repo_root()) + list_tme_problem_catalog(get_repo_root())}
    if any(item.problem_id not in available for item in body.items):
        raise ValueError("unknown assessment problem")
    return assessment_store().create_tme(**body.model_dump(exclude={"items"}),
        teacher_user_id=user.user_id, opens_at=datetime(body.academic_year, 1, 1, tzinfo=timezone.utc),
        closes_at=datetime(body.academic_year + 1, 1, 1, tzinfo=timezone.utc),
        items=body.items, assessment_id=assessment_id)


def ensure_demo_assessment(user):
    if not demo_no_auth_enabled() or user.user_id != DEMO_EVALUATOR_ID:
        return
    config = json.loads((get_repo_root() / "examples/assessments/tme_2026_phase2.json").read_text())
    store = assessment_store()
    try:
        store.get(config["assessment_id"])
        return
    except FileNotFoundError:
        pass
    catalog = {p["problem_id"]: p for p in list_tme_problem_catalog(get_repo_root())}
    body = TMEAssessmentCreate(title=config["title"], instructions=config["instructions"],
        academic_year=config["academic_year"], items=[CreateAssessmentItem(problem_id=p,
            points=catalog[p]["max_score"]) for p in config["problem_ids"]])
    try:
        create_assessment(body, user, config["assessment_id"])
    except AssessmentConflict:
        # Concurrent demo bootstrap: the existing published definition wins.
        store.get(config["assessment_id"])


@router.get("/assessments", response_model=list[AssessmentDocument])
def assessments(response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    guarded(ensure_demo_assessment, user)
    return [doc for doc in guarded(assessment_store().list) if doc.assessment.scope == "TME"
            and doc.assessment.teacher_user_id == user.user_id and doc.assessment.status == "PUBLISHED"]


@router.post("/assessments", response_model=AssessmentDocument, status_code=201)
def new_assessment(body: TMEAssessmentCreate, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(create_assessment, body, user)


@router.post("/exam-submissions", response_model=ExamDetail)
async def receive_exam(request: Request, response: Response, user=Depends(require_tme_evaluator)):
    from .router import bounded_json
    raw = await bounded_json(request, MAX_CAPTURE_BODY)
    try:
        body = ExamCapturePackage.model_validate_json(raw)
    except ValidationError:
        raise HTTPException(422, "Pacote de captura inválido. Envie um PDF ou imagens e o código da prova.") from None
    detail, created = await run_in_threadpool(guarded, exam_store().receive, body, user)
    response.status_code = 201 if created else 200
    response.headers["Cache-Control"] = "no-store"
    return detail


@router.get("/exam-submissions")
def list_exams(response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(exam_store().list_for, user)


@router.get("/exam-submissions/{exam_id}", response_model=ExamDetail)
def get_exam(exam_id: str, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(exam_store().detail, exam_id, user)


@router.get("/exam-submissions/{exam_id}/pages", response_model=list[ExamPage])
def get_pages(exam_id: str, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(exam_store().detail, exam_id, user).submission.pages


@router.get("/exam-submissions/{exam_id}/assets/{asset_id}")
def get_asset(exam_id: str, asset_id: str, user=Depends(require_tme_evaluator)):
    data, ref = guarded(exam_store().asset, exam_id, asset_id, user)
    # Serve the exact verified bytes, avoiding a file replacement after validation.
    extension = {"application/pdf": "pdf", "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[ref.media_type]
    return Response(data, media_type=ref.media_type, headers={"Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff", "Content-Disposition": f'inline; filename="{ref.asset_id}.{extension}"'})


@router.put("/exam-submissions/{exam_id}/page-mapping", response_model=PageMapping)
def map_pages(exam_id: str, body: UpdatePageMapping, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(exam_store().update_mapping, exam_id, body, user)


@router.get("/exam-submissions/{exam_id}/question-attempts", response_model=list[QuestionAttemptView])
def questions(exam_id: str, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    store = exam_store()
    detail = guarded(store.detail, exam_id, user)
    return [guarded(store.question, exam_id, c.case_id, user) for c in detail.question_attempts]


@router.get("/question-attempts/{case_id}", response_model=QuestionAttemptView)
def question(case_id: str, response: Response, user=Depends(require_tme_evaluator)):
    response.headers["Cache-Control"] = "no-store"
    case = guarded(case_store().for_user, case_id, user)
    if not case.exam_submission_id:
        raise HTTPException(404, "A questão não pertence a uma prova completa.")
    return guarded(exam_store().question, case.exam_submission_id, case_id, user)


@router.get("/question-attempts/{case_id}/workspace", response_model=dict)
def question_workspace(case_id: str, response: Response, user=Depends(require_tme_evaluator)):
    from .question_review import workspace
    response.headers["Cache-Control"] = "no-store"
    return guarded(workspace, case_id, user)


@router.post("/cases/{case_id}/transcriptions", response_model=dict, status_code=201)
async def create_question_transcription(case_id: str, request: Request, response: Response,
                                       user=Depends(require_tme_evaluator)):
    from .router import parsed_body
    from .review_models import CreateQuestionTranscription
    from .question_review import create
    body = await parsed_body(request, CreateQuestionTranscription)
    revision = await run_in_threadpool(guarded, create, case_id, body, user)
    response.headers["Cache-Control"] = "no-store"
    return revision.model_dump(mode="json")
