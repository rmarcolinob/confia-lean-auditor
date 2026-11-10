from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from confia_lean_auditor.auth.dependencies import require_any_role
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.core.schemas import AuditRequest
from confia_lean_auditor.recognition.glm_ocr import configured_base_url
from confia_lean_auditor.uploads.schemas import MAX_REQUEST_BYTES, UploadAnswersRequest, UploadAnswersResponse
from confia_lean_auditor.uploads.service import UploadError, recognize_upload

router = APIRouter(prefix="/uploads", tags=["upload OCR"])
any_user = require_any_role(Role.STUDENT, Role.TEACHER)


@router.get("/status")
def upload_status(response: Response, _user=Depends(any_user)):
    response.headers["Cache-Control"] = "no-store"
    return {"provider": "glm_ocr", "configured": configured_base_url() is not None,
            "accepted_media_types": ["image/png", "image/jpeg", "application/pdf"], "max_pages": 3}


@router.post("/answers", response_model=UploadAnswersResponse)
async def upload_answers(request: Request, response: Response, _user=Depends(any_user)):
    ocr = await _recognize(request)
    response.headers["Cache-Control"] = "no-store"
    return ocr


@router.post("/audits")
async def upload_and_audit(request: Request, response: Response, _user=Depends(any_user)):
    ocr = await _recognize(request)
    # The OCR result is returned even when the audit fails: it takes minutes to produce.
    audit, audit_error = await run_in_threadpool(_audit, ocr)
    response.headers["Cache-Control"] = "no-store"
    return {
        "ocr": ocr.model_dump(mode="json"),
        "audit": audit,
        "audit_error": audit_error,
        "warnings": ["AUTOMATIC_AUDIT_OF_UNREVIEWED_OCR: a correção usou o texto do OCR sem conferência "
                     "humana; um dígito lido errado muda o veredito."],
    }


async def _recognize(request: Request) -> UploadAnswersResponse:
    raw = await _read_json_body(request)
    try:
        return await run_in_threadpool(_parse_and_recognize, raw)
    except UploadError as exc:
        raise HTTPException(exc.status, exc.code) from None


def _parse_and_recognize(raw: bytes) -> UploadAnswersResponse:
    try:
        upload = UploadAnswersRequest.model_validate_json(raw)
    except ValidationError:
        # Never echo the body: it carries the student's image.
        raise UploadError("INVALID_REQUEST", 422) from None
    return recognize_upload(upload)


async def _read_json_body(request: Request) -> bytes:
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
    return bytes(raw)


def _audit(ocr: UploadAnswersResponse):
    # Resolved at call time to avoid a main/router cycle, as in submission_audits.
    from confia_lean_auditor.core.public_audit import (
        audit_exception_response, public_audit_data, sanitize_public_payload,
    )
    from confia_lean_auditor.main import execute_audit

    if not ocr.answer_text.strip():
        return None, {"status": 422, "error_code": "EMPTY_ANSWER",
                      "detail": "O OCR não encontrou resposta do aluno para corrigir."}
    try:
        result = execute_audit(AuditRequest(problem_id=ocr.problem_id, solution=ocr.answer_text))
        return sanitize_public_payload(public_audit_data(result)), None
    except Exception as error:
        failure = audit_exception_response(error)
        body = json.loads(failure.body)
        return None, {"status": failure.status_code, "error_code": body.get("error_code"),
                      "detail": body.get("detail")}
