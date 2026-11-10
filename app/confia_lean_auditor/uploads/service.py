"""Upload orchestration: files -> PNG pages -> GLM-OCR -> answer without the statement."""
from __future__ import annotations

import base64
import binascii
import hashlib
import math
import os
from concurrent.futures import TimeoutError as FutureTimeout
from datetime import datetime, timezone
from threading import TIMEOUT_MAX
from typing import Optional

from confia_lean_auditor.core.paths import InvalidProblemId, get_problem_dir, get_repo_root
from confia_lean_auditor.core.problem_assets import ProblemAssetValidationError, load_problem_config
from confia_lean_auditor.core.problem_catalog import CATALOG
from confia_lean_auditor.recognition.execution import ProviderDeadline, start_provider
from confia_lean_auditor.recognition.glm_ocr import GlmOcrClient
from confia_lean_auditor.uploads.answer_extraction import extract_answer
from confia_lean_auditor.uploads.images import (
    InvalidUpload, UnsupportedUpload, UploadDependencyMissing, prepare_pages,
)
from confia_lean_auditor.uploads.schemas import (
    MAX_FILE_BYTES, RemovedText, UploadAnswersRequest, UploadAnswersResponse, UploadedPage,
)

DEFAULT_TIMEOUT_SECONDS = 300.0
MAX_SIDE_PX = 1600


class UploadError(ValueError):
    def __init__(self, code: str, status: int):
        super().__init__(code)
        self.code, self.status = code, status


def timeout_seconds() -> float:
    seconds = float(os.environ.get("CONFIA_UPLOAD_OCR_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
    if not math.isfinite(seconds) or seconds <= 0 or seconds > TIMEOUT_MAX:
        raise ValueError("upload OCR timeout must be positive and supported by the runtime")
    return seconds


def problem_statement(problem_id: str) -> str:
    if problem_id not in CATALOG:
        raise UploadError("UNKNOWN_PROBLEM", 422)
    try:
        return load_problem_config(get_problem_dir(get_repo_root(), problem_id)).statement
    except (InvalidProblemId, ProblemAssetValidationError, OSError):
        raise UploadError("UNKNOWN_PROBLEM", 422) from None


def decode_files(request: UploadAnswersRequest) -> list[bytes]:
    files = []
    for item in request.files:
        try:
            data = base64.b64decode(item.data_base64, validate=True)
        except (binascii.Error, ValueError):
            raise UploadError("INVALID_BASE64", 422) from None
        if len(data) > MAX_FILE_BYTES:
            raise UploadError("FILE_TOO_LARGE", 413)
        files.append(data)
    return files


def recognize_upload(request: UploadAnswersRequest, client: Optional[GlmOcrClient] = None) -> UploadAnswersResponse:
    statement = problem_statement(request.problem_id)
    client = client or GlmOcrClient()
    if not client.base_url:
        raise UploadError("PROVIDER_NOT_CONFIGURED", 503)
    try:
        pages = prepare_pages(decode_files(request))
    except UnsupportedUpload:
        raise UploadError("UNSUPPORTED_MEDIA_TYPE", 415) from None
    except InvalidUpload as exc:
        raise UploadError(f"INVALID_UPLOAD:{exc}", 422) from None
    except UploadDependencyMissing:
        raise UploadError("OCR_DEPENDENCIES_MISSING", 503) from None

    # One deadline for all pages; each HTTP call gets the remaining time.
    deadline = ProviderDeadline.start(timeout_seconds())

    def call_provider():
        return [client.transcribe(page.png, deadline) for page in pages], None

    future = start_provider(call_provider, deadline)
    try:
        results, error = future.result(timeout=deadline.remaining_seconds())
    except FutureTimeout:
        results, error = None, "PROVIDER_TIMEOUT"
    if error:
        raise UploadError(error, {"PROVIDER_TIMEOUT": 504, "PROVIDER_BUSY": 503}.get(error, 502))

    extraction = extract_answer([r.text for r in results], statement)
    warnings = list(extraction.warnings)
    if any(r.truncated for r in results):
        warnings.append("OCR_TRUNCATED: o OCR atingiu o limite de saída em alguma página (provável "
                        "repetição); confira o texto.")
    warnings.append("Texto de OCR: o GLM-OCR pode trocar dígitos ou omitir trechos sem sinal de dúvida; "
                    "confira cada valor antes de enviar ao /audit.")
    hashes = [hashlib.sha256(page.png).hexdigest() for page in pages]
    names = [item.filename for item in request.files]
    return UploadAnswersResponse(
        upload_id="upl_" + hashlib.sha256(":".join([request.problem_id, *hashes]).encode()).hexdigest()[:32],
        problem_id=request.problem_id,
        answer_text=extraction.answer_text,
        statement_found=extraction.statement_found,
        statement_match=extraction.statement_match,
        pages=[UploadedPage(
            page_index=i, source_file_index=page.source_index, source_filename=names[page.source_index],
            source_media_type=page.source_media_type, page_in_source=page.page_in_source, sha256=hashes[i],
            width=page.width, height=page.height, latency_ms=round(results[i].latency_ms, 1),
            truncated=results[i].truncated, answer_text=extraction.pages[i].answer_text,
        ) for i, page in enumerate(pages)],
        removed=[RemovedText(kind=b.kind, page_index=b.page_index, text=b.text) for b in extraction.removed],
        warnings=warnings,
        adapter=client.adapter, adapter_version=client.adapter_version,
        parameters={**client.public_parameters, "max_side_px": MAX_SIDE_PX},
        created_at=datetime.now(timezone.utc),
    )
