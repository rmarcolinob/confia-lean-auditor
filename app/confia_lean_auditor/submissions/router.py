import os
from pathlib import Path
import zlib

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.submissions.schemas import (
    MAX_REQUEST_BYTES,
    SubmissionDetail,
    SubmissionReceipt,
    SubmissionRecord,
    SubmissionRequest,
)
from confia_lean_auditor.submissions.store import (
    InvalidSubmissionProblem,
    SubmissionConflict,
    SubmissionStore,
    SubmissionTooLarge,
)

router = APIRouter(prefix="/submissions", tags=["experimental submissions"])


def store() -> SubmissionStore:
    configured = os.environ.get("CONFIA_SUBMISSIONS_DIR")
    root = Path(configured).resolve() if configured else get_repo_root() / "runtime" / "submissions"
    return SubmissionStore(root)


def guarded(operation, *args):
    try:
        return operation(*args)
    except SubmissionConflict:
        raise HTTPException(409, "Snapshot já recebido com conteúdo diferente ou integridade divergente.") from None
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


def receive_body(raw):
    request = SubmissionRequest.model_validate_json(raw)
    return store().receive(request)


@router.post("", response_model=SubmissionReceipt)
async def receive_submission(request: Request, response: Response):
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
    receipt, created = await run_in_threadpool(guarded, receive_body, bytes(raw))
    response.status_code = 201 if created else 200
    response.headers["Cache-Control"] = "no-store"
    return receipt


@router.get("", response_model=list[SubmissionRecord])
def list_submissions(response: Response):
    response.headers["Cache-Control"] = "no-store"
    return guarded(store().list)


@router.get("/{submission_id}", response_model=SubmissionDetail)
def get_submission(submission_id: str, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return guarded(store().detail, submission_id)


@router.get("/{submission_id}/pages/{page_index}")
def get_page(submission_id: str, page_index: int):
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
def get_snapshot(submission_id: str):
    path, ref = guarded(store().artifact, submission_id)
    return FileResponse(
        path, media_type="application/json", filename=ref.filename,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
