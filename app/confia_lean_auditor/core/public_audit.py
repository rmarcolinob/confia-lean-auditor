"""Single public boundary for audit data and errors.

Projection never mutates persisted records or recalculates their hashes. Public
metadata has a distinct DTO: its digest describes the original internal record,
not the potentially redacted manifest included in the HTTP response.
"""
import logging
from pathlib import Path, PurePosixPath
import re
from typing import Literal, Optional

from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException

from confia_lean_auditor.reproducibility.schemas import (
    AuditReproducibilityManifest, Digest, MANIFEST_FILENAME,
)

logger = logging.getLogger(__name__)
HIDDEN_LOCAL_PATH = "[local path hidden]"
INTEGRITY_SCOPE = "persisted_internal_record"
# Recognize platforms independently, including paths embedded after punctuation.
# Fixed local roots need no delimiter; the general POSIX rule excludes URL
# separators and ordinary fractions such as a/b. Relative artifact paths are
# handled separately, using the authorized root rather than text inference.
LOCAL_PATH_PATTERNS = (
    re.compile(r"file://", re.I),
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|\\\\[^\\\s]+\\"),
    re.compile(r"(?<![\w/])/(?:Users|home|private|tmp|var|opt|etc|usr|root|Volumes|mnt|srv|run|workspace|workspaces)(?:/|(?=$|[\s\]\)}\"',;]))", re.I),
    re.compile(r"(?<![\w:/\\])/(?![/\s])[^\s\[\](){}\"',;<>]+"),
)
PATH_FIELDS = {"file", "lean_file", "refutation_lean_file"}
DIAGNOSTICS = {"stdout", "stderr", "refutation_stdout", "refutation_stderr"}


def sanitize_public_text(value: str) -> str:
    """Hide the entire affected value so spaces cannot leave a username behind.

    Never reinterpret an arbitrary diagnostic as an artifact reference.
    """
    return HIDDEN_LOCAL_PATH if any(pattern.search(value) for pattern in LOCAL_PATH_PATTERNS) else value


def sanitize_public_payload(value):
    """Detached JSON projection, including untrusted mapping keys and tuples."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            public_key = sanitize_public_text(key) if isinstance(key, str) else key
            # Preserve entries even when multiple private keys are redacted.
            if public_key != key and public_key in result:
                public_key = f"{HIDDEN_LOCAL_PATH} {len(result)}"
            result[public_key] = sanitize_public_payload(child)
        return result
    if isinstance(value, (list, tuple)):
        return [sanitize_public_payload(child) for child in value]
    return sanitize_public_text(value) if isinstance(value, str) else value


class PublicReproducibilityRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manifest: AuditReproducibilityManifest
    manifest_sha256: Digest = Field(description="SHA-256 of the persisted internal manifest, not the projected JSON.")
    filename: Literal[MANIFEST_FILENAME]
    size_bytes: int = Field(ge=0, description="Byte size of the persisted internal canonical manifest.")


class PublicReproducibilityMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["recorded", "unavailable", "legacy_unversioned"]
    record: Optional[PublicReproducibilityRecord] = None
    error_code: Optional[Literal["METADATA_COLLECTION_FAILED", "METADATA_PUBLICATION_FAILED",
                                 "METADATA_INTEGRITY_FAILED", "AUDIT_NOT_COMPLETED"]] = None
    integrity_scope: Literal["persisted_internal_record"] = INTEGRITY_SCOPE
    public_warnings: list[Literal["LOCAL_REFERENCE_WITHHELD"]] = Field(default_factory=list)


def public_reproducibility(metadata):
    raw = metadata.model_dump(mode="json") if isinstance(metadata, BaseModel) else metadata
    data = sanitize_public_payload(raw)
    redacted = data != raw
    data["integrity_scope"] = INTEGRITY_SCOPE
    data["public_warnings"] = ["LOCAL_REFERENCE_WITHHELD"] if redacted else []
    return PublicReproducibilityMetadata.model_validate(data)


def public_projection(value, artifact_root=None, artifact_ref=None):
    """Project artifact references before sanitizing the remaining text."""
    warnings = set()
    root = None
    lexical_root = None
    try:
        if artifact_root and Path(artifact_root).is_absolute():
            lexical_root = Path(artifact_root)
            root = lexical_root.resolve(strict=True)
            if not root.is_dir():
                root = None
    except (OSError, ValueError, RuntimeError):
        pass

    def relative_file(raw):
        if raw is None:
            return None
        try:
            if not isinstance(raw, str) or not raw or root is None or "\\" in raw or ":" in raw:
                raise ValueError()
            path = Path(raw)
            if ".." in path.parts:
                raise ValueError()
            candidate = path if path.is_absolute() else lexical_root / path
            relative = candidate.relative_to(lexical_root).as_posix()
            candidate.resolve(strict=True).relative_to(root)
            if not candidate.is_file() or str(PurePosixPath(relative)) != relative:
                raise ValueError()
            return relative
        except (OSError, ValueError, RuntimeError):
            warnings.add("ARTIFACT_REFERENCE_UNAVAILABLE")
            return None

    def visit(item, key=""):
        if key == "artifact_dir":
            return None
        if key in PATH_FIELDS:
            return relative_file(item)
        if key in DIAGNOSTICS:
            if item:
                warnings.add("COMPILER_DIAGNOSTICS_WITHHELD")
            return ""
        if key == "reproducibility" and item is not None:
            metadata = public_reproducibility(item)
            warnings.update(metadata.public_warnings)
            return metadata.model_dump(mode="json")
        if isinstance(item, dict):
            return sanitize_public_payload({name: visit(child, name) for name, child in item.items()})
        if isinstance(item, (list, tuple)):
            return [visit(child) for child in item]
        public = sanitize_public_payload(item)
        if isinstance(item, str) and artifact_root and str(artifact_root) in item:
            public = HIDDEN_LOCAL_PATH
        if public != item:
            warnings.add("LOCAL_REFERENCE_WITHHELD")
        return public

    data = visit(value)
    data["artifact_ref"] = artifact_ref
    data["public_warnings"] = sorted(warnings)
    return data


def public_audit_data(value):
    raw = value.model_dump(mode="json")
    run_id = raw.get("audit_run_id")
    data = public_projection(raw, raw.get("artifact_dir"), f"audit-run:{run_id}" if run_id else None)
    if run_id:
        data["integrity_scope"] = INTEGRITY_SCOPE
    return data


def public_response(data, status_code=200):
    return JSONResponse(sanitize_public_payload(data), status_code=status_code,
                        headers={"Cache-Control": "no-store"})


def public_audit_response(value):
    data = [public_audit_data(item) for item in value] if isinstance(value, list) else public_audit_data(value)
    return public_response(data)


def public_error_response(status_code, code, message, *, include_message=False):
    data = {"detail": message, "error_code": code}
    if include_message:
        data["message"] = message
    return public_response(data, status_code)


def audit_exception_response(error):
    """Only fixed diagnostics cross the HTTP/log boundary, never exception text."""
    from confia_lean_auditor.core.paths import InvalidProblemId
    from confia_lean_auditor.core.problem_assets import ProblemAssetValidationError
    from confia_lean_auditor.llm.formal_step_extractor import FormalStepExtractionError

    cause = error.__cause__ if isinstance(error, HTTPException) and error.__cause__ else error
    status, code, message = 500, "AUDIT_OPERATION_FAILED", "Não foi possível concluir a operação."
    if isinstance(cause, ProblemAssetValidationError):
        # Existing validator has one exception type. Interpret only its fixed
        # category prefix here, without exposing paths or changing the validator.
        missing = str(cause).startswith("Arquivo obrigatório não encontrado:")
        status = 400
        code = "REQUIRED_PROBLEM_ASSET_MISSING" if missing else "INVALID_PROBLEM_ASSET"
        message = "Um arquivo obrigatório da questão não está disponível." if missing else "Os arquivos da questão não passaram na validação."
    elif isinstance(cause, InvalidProblemId):
        status, code, message = 400, "INVALID_PROBLEM_ID", "Identificador da questão inválido."
    elif isinstance(cause, FormalStepExtractionError):
        status, code, message = 503, "FORMAL_EXTRACTION_UNAVAILABLE", "Não foi possível extrair os passos desta solução."
    elif isinstance(cause, NotImplementedError):
        status, code, message = 501, "AUDIT_OPERATION_UNAVAILABLE", "Esta análise não está disponível."
    elif isinstance(error, HTTPException):
        status = error.status_code
        if status == 404:
            code, message = "AUDIT_RESOURCE_NOT_FOUND", "Questão ou análise não encontrada."
    logger.warning("Audit public failure: status=%s code=%s", status, code)
    return public_error_response(status, code, message, include_message=True)


def install_audit_exception_handlers(app):
    """Cover errors raised before endpoint entry, without changing other APIs."""
    from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    def audit_path(path):
        return path == "/audit" or path.startswith("/submission-audits/") or re.fullmatch(r"/submissions/[^/]+/audits", path)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        if audit_path(request.url.path):
            return public_error_response(422, "INVALID_AUDIT_REQUEST", "Dados da requisição inválidos.", include_message=True)
        return await request_validation_exception_handler(request, error)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, error):
        if audit_path(request.url.path):
            return audit_exception_response(error)
        return await http_exception_handler(request, error)
