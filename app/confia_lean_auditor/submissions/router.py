from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
import zlib

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.auth.dependencies import (
    require_any_role, require_role, visible_submissions,
    student_submission_access, submission_access, teacher_submission_access,
    teacher_transcription_access,
)
from confia_lean_auditor.auth.models import AuthUser, Role
from confia_lean_auditor.recognition.registry import configured_registry, UnknownRecognizer
from confia_lean_auditor.recognition.schemas import RecognitionRequest, RecognitionResponse, RecognitionRun
from confia_lean_auditor.recognition.service import RecognitionService, RecognitionConflict
from confia_lean_auditor.recognition.preview import PreviewError, PreviewRequest, PreviewResponse, recognize_preview
from confia_lean_auditor.submissions.schemas import (
    AcceptedTranscription,
    AcceptTranscriptionRequest,
    CreateTranscriptionRequest,
    CreateTranscriptionRevisionRequest,
    MAX_REQUEST_BYTES,
    SubmissionDetail,
    SubmissionReceipt,
    SubmissionRecord,
    SubmissionRequest,
    TranscriptionHistory,
    TranscriptionRevision,
    TranscriptionSummary,
)
from confia_lean_auditor.submissions.store import (
    InvalidSubmissionProblem,
    SubmissionConflict,
    SubmissionIntegrityConflict,
    SubmissionStore,
    SubmissionTooLarge,
    TranscriptionConflict,
    TranscriptionIntegrityConflict,
)

router = APIRouter(prefix="/submissions", tags=["experimental submissions"])
transcriptions_router = APIRouter(prefix="/transcriptions", tags=["manual transcriptions"])


def store() -> SubmissionStore:
    configured = os.environ.get("CONFIA_SUBMISSIONS_DIR")
    root = Path(configured).resolve() if configured else get_repo_root() / "runtime" / "submissions"
    return SubmissionStore(root)


def guarded(operation, *args):
    try:
        return operation(*args)
    except SubmissionIntegrityConflict:
        raise HTTPException(409, "Integridade da submissão original inválida; reconhecimento, transcrição, revisão ou aceite não publicado.") from None
    except UnknownRecognizer:
        raise HTTPException(422, "Reconhecedor indisponível neste ambiente.") from None
    except RecognitionConflict:
        raise HTTPException(409, "Chave de idempotência reutilizada com outra configuração.") from None
    except SubmissionConflict:
        raise HTTPException(409, "Snapshot já recebido com conteúdo diferente ou integridade divergente.") from None
    except TranscriptionIntegrityConflict:
        raise HTTPException(409, "Integridade da revisão ou do aceite inválida; nenhum reparo automático foi realizado.") from None
    except TranscriptionConflict:
        return JSONResponse(status_code=409, content={"detail": "A transcrição foi alterada ou aceita a partir de outra versão.", "error_code": "REVISION_CONFLICT"}, headers={"Cache-Control": "no-store"})
    except SubmissionTooLarge:
        raise HTTPException(413, "Artefato acima do limite permitido.") from None
    except InvalidSubmissionProblem:
        raise HTTPException(400, "Questão não disponível no catálogo.") from None
    except FileNotFoundError:
        raise HTTPException(404, "Submissão ou artefato não encontrado.") from None
    except (ValidationError, ValueError, zlib.error):
        # Never expose validation 'input' containing handwriting in responses/logs.
        raise HTTPException(422, "Payload ou registro de submissão inválido.") from None
    except OSError:
        raise HTTPException(
            503,
            "Armazenamento de submissões indisponível. Preserve a cópia local e tente novamente.",
        ) from None


def receive_body(raw, owner):
    request = SubmissionRequest.model_validate_json(raw)
    return store().receive(request, owner)


@router.post("", response_model=SubmissionReceipt)
async def receive_submission(request: Request, response: Response,
                             user: Optional[AuthUser] = Depends(require_role(Role.STUDENT))):
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
        raise HTTPException(415, "Use application/json.")
    length = request.headers.get("content-length")
    if length is not None:
        try:
            length = int(length)
        except ValueError:
            raise HTTPException(400, "Content-Length inválido.") from None
        if length < 0 or length > MAX_REQUEST_BYTES:
            raise HTTPException(413, "Payload acima do limite permitido.")
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_REQUEST_BYTES:
            raise HTTPException(413, "Payload acima do limite permitido.")
        raw.extend(chunk)
    receipt, created = await run_in_threadpool(guarded, receive_body, bytes(raw), user)
    response.status_code = 201 if created else 200
    response.headers["Cache-Control"] = "no-store"
    return receipt


@router.get("", response_model=list[SubmissionRecord])
def list_submissions(response: Response, user: Optional[AuthUser] = Depends(
        require_any_role(Role.STUDENT, Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    records = guarded(store().list)
    return visible_submissions(user, records)


@router.get("/recognition-providers")
def recognition_providers(response: Response, _user=Depends(require_role(Role.STUDENT))):
    response.headers["Cache-Control"] = "no-store"
    registry = configured_registry()
    return [{"provider": name, "label": registry.create(name).display_label} for name in registry.providers()]


@router.post("/recognition-preview", response_model=PreviewResponse)
async def preview_recognition(request: Request, response: Response,
                              _user=Depends(require_role(Role.STUDENT))):
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
        raise HTTPException(415, "Use application/json.")
    length = request.headers.get("content-length")
    if length is not None:
        try:
            if int(length) > MAX_REQUEST_BYTES or int(length) < 0:
                raise HTTPException(413, "Payload acima do limite permitido.")
        except ValueError:
            raise HTTPException(400, "Content-Length inválido.") from None
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_REQUEST_BYTES:
            raise HTTPException(413, "Payload acima do limite permitido.")
        raw.extend(chunk)
    try:
        preview_request = PreviewRequest.model_validate_json(bytes(raw))
        result = await run_in_threadpool(recognize_preview, preview_request, configured_registry())
    except UnknownRecognizer:
        raise HTTPException(422, "Reconhecedor indisponível neste ambiente.") from None
    except PreviewError as exc:
        code = str(exc)
        status = 422 if code in {"INVALID_SNAPSHOT", "INVALID_PROVIDER", "INVALID_PROVIDER_OUTPUT"} else 503
        raise HTTPException(status, code) from None
    except (ValidationError, ValueError):
        raise HTTPException(422, "Payload de prévia inválido.") from None
    response.headers["Cache-Control"] = "no-store"
    return result


def recognize_body(submission_id, raw):
    request = RecognitionRequest.model_validate_json(raw)
    return RecognitionService(store(), configured_registry()).recognize(submission_id, request)


@router.post("/{submission_id}/recognitions", response_model=RecognitionResponse)
async def recognize_submission(submission_id: str, request: Request, response: Response,
                               _record=Depends(student_submission_access)):
    # The body limiter bounds reads. Parse within guarded so rejected extras cannot
    # echo possible secrets/manuscript in FastAPI's default validation errors.
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
        raise HTTPException(415, "Use application/json.")
    run, created = await run_in_threadpool(guarded, recognize_body, submission_id, await request.body())
    response.status_code = 201 if created else 200
    response.headers["Cache-Control"] = "no-store"
    return RecognitionResponse.from_run(run)


@router.get("/{submission_id}/recognitions", response_model=list[RecognitionRun])
def list_recognitions(submission_id: str, response: Response,
                      _record=Depends(submission_access)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(RecognitionService(store(), configured_registry()).list, submission_id)


@router.get("/{submission_id}/recognitions/{recognizer_run_id}", response_model=RecognitionRun)
def get_recognition(submission_id: str, recognizer_run_id: str, response: Response,
                    _record=Depends(submission_access)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(RecognitionService(store(), configured_registry()).get, submission_id, recognizer_run_id)


@router.get("/{submission_id}", response_model=SubmissionDetail)
def get_submission(submission_id: str, response: Response,
                   _record=Depends(submission_access)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(store().detail, submission_id)


@router.get("/{submission_id}/pages/{page_index}")
def get_page(submission_id: str, page_index: int, _record=Depends(submission_access)):
    path, ref = guarded(store().artifact, submission_id, page_index)
    return FileResponse(
        path, media_type="image/png", filename=ref.filename,
        content_disposition_type="inline",
        headers={
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
            "ETag": f'"{ref.sha256}"',
        },
    )


@router.get("/{submission_id}/snapshot")
def get_snapshot(submission_id: str, _record=Depends(submission_access)):
    path, ref = guarded(store().artifact, submission_id)
    return FileResponse(
        path, media_type="application/json", filename=ref.filename,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.post("/{submission_id}/transcriptions", response_model=TranscriptionRevision, status_code=201)
def create_transcription(submission_id: str, request: CreateTranscriptionRequest, response: Response,
                         _record=Depends(teacher_submission_access)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(store().create_transcription, submission_id, request)


@router.get("/{submission_id}/transcriptions", response_model=list[TranscriptionSummary])
def list_transcriptions(submission_id: str, response: Response,
                        _record=Depends(teacher_submission_access)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(store().list_transcriptions, submission_id)


@transcriptions_router.get("/{transcription_id}", response_model=TranscriptionHistory)
def get_transcription(transcription_id: str, response: Response,
                      _record=Depends(teacher_transcription_access)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(store().transcription_history, transcription_id)


@transcriptions_router.post("/{transcription_id}/revisions", response_model=TranscriptionRevision, status_code=201)
def create_transcription_revision(
    transcription_id: str, request: CreateTranscriptionRevisionRequest, response: Response,
    _record=Depends(teacher_transcription_access),
):
    response.headers["Cache-Control"] = "no-store"
    return guarded(store().create_transcription_revision, transcription_id, request)


@transcriptions_router.post("/{transcription_id}/accept", response_model=AcceptedTranscription)
def accept_transcription(
    transcription_id: str, request: AcceptTranscriptionRequest, response: Response,
    _record=Depends(teacher_transcription_access),
):
    response.headers["Cache-Control"] = "no-store"
    return guarded(store().accept_transcription, transcription_id, request)
