"""Backend role and object authorization; UI state is never consulted."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, Request
from pydantic import ValidationError

from confia_lean_auditor.core.paths import get_repo_root
from .models import AuthUser, Role
from .store import AuthStore

COOKIE_NAME = "confia_session"


def auth_enabled() -> bool:
    value = os.environ.get("CONFIA_AUTH_ENABLED", "1").lower()
    if value not in {"0", "1", "false", "true"}:
        raise RuntimeError("invalid CONFIA_AUTH_ENABLED")
    enabled = value in {"1", "true"}
    if not enabled and os.environ.get("CONFIA_ENV", "development").lower() == "production":
        raise RuntimeError("authentication cannot be disabled in production")
    return enabled


def auth_store() -> AuthStore:
    configured = os.environ.get("CONFIA_AUTH_DIR")
    return AuthStore(Path(configured).resolve() if configured else get_repo_root() / "runtime" / "auth")


def optional_user(request: Request) -> Optional[AuthUser]:
    return auth_store().session_user(request.cookies.get(COOKIE_NAME)) if auth_enabled() else None


def current_user(request: Request) -> Optional[AuthUser]:
    if not auth_enabled():
        return None
    user = optional_user(request)
    if user is None:
        raise HTTPException(401, "Autenticação necessária.")
    return user


def require_any_role(*roles: Role):
    def dependency(user: Optional[AuthUser] = Depends(current_user)) -> Optional[AuthUser]:
        if auth_enabled() and user.role not in roles:
            raise HTTPException(403, "Acesso não autorizado.")
        return user
    return dependency


def require_role(role: Role):
    return require_any_role(role)


def allow_legacy_teacher_read() -> bool:
    return (os.environ.get("CONFIA_AUTH_LEGACY_READ") == "1"
            and os.environ.get("CONFIA_ENV", "development").lower() != "production")


def authorize_submission_record(user: AuthUser | None, record, *, student_write=False):
    if user is None and not auth_enabled():
        return record
    if user is None:
        raise HTTPException(401, "Autenticação necessária.")
    if user.role == Role.STUDENT:
        if record.submitted_by_user_id != user.user_id:
            raise HTTPException(403, "Acesso não autorizado.")
    elif user.role == Role.TEACHER and not student_write:
        from confia_lean_auditor.institutional.store import institutional_store
        legacy = (not all((record.network_id, record.school_id, record.classroom_id))
                  and allow_legacy_teacher_read()
                  and (record.tenant_id is None or record.tenant_id == user.tenant_id))
        if not (institutional_store().teacher_can_view(user, record) or legacy):
            raise HTTPException(403, "Acesso não autorizado.")
    else:
        raise HTTPException(403, "Acesso não autorizado.")
    return record


def visible_submissions(user: Optional[AuthUser], records):
    if not auth_enabled():
        return records
    if user.role == Role.STUDENT:
        return [record for record in records if record.submitted_by_user_id == user.user_id]
    if user.role == Role.TEACHER:
        from confia_lean_auditor.institutional.store import institutional_store
        institutions = institutional_store()
        return [record for record in records if institutions.teacher_can_view(user, record)
                or (not all((record.network_id, record.school_id, record.classroom_id))
                    and allow_legacy_teacher_read()
                    and (record.tenant_id is None or record.tenant_id == user.tenant_id))]
    raise HTTPException(403, "Acesso não autorizado.")


def _record_for_access(submission_id: str):
    from confia_lean_auditor.submissions.router import store
    submission_store = store()
    try:
        return submission_store.get_record(submission_id)
    except FileNotFoundError:
        if (submission_store.root / submission_id).exists():
            raise HTTPException(409, "Integridade da submissão inválida.") from None
        raise HTTPException(404, "Submissão não encontrada.") from None
    except (ValidationError, ValueError, OSError):
        raise HTTPException(409, "Integridade da submissão inválida.") from None


def submission_access(submission_id: str, user: Optional[AuthUser] = Depends(
        require_any_role(Role.STUDENT, Role.TEACHER))):
    if not auth_enabled():
        return None
    return authorize_submission_record(user, _record_for_access(submission_id))


def student_submission_access(submission_id: str, user: Optional[AuthUser] = Depends(
        require_role(Role.STUDENT))):
    if not auth_enabled():
        return None
    return authorize_submission_record(user, _record_for_access(submission_id), student_write=True)


def teacher_submission_access(submission_id: str, user: Optional[AuthUser] = Depends(
        require_role(Role.TEACHER))):
    if not auth_enabled():
        return None
    return authorize_submission_record(user, _record_for_access(submission_id))


def teacher_transcription_access(transcription_id: str, user: Optional[AuthUser] = Depends(
        require_role(Role.TEACHER))):
    if not auth_enabled():
        return None
    from confia_lean_auditor.submissions.router import store
    from confia_lean_auditor.submissions.store import TranscriptionIntegrityConflict
    try:
        history = store().transcription_history(transcription_id)
        record = _record_for_access(history.transcription.submission_id)
    except FileNotFoundError:
        raise HTTPException(404, "Transcrição não encontrada.") from None
    except (TranscriptionIntegrityConflict, ValidationError, ValueError, OSError):
        raise HTTPException(409, "Integridade da transcrição inválida.") from None
    return authorize_submission_record(user, record)


def teacher_audit_access(audit_run_id: str, user: Optional[AuthUser] = Depends(
        require_role(Role.TEACHER))):
    if not auth_enabled():
        return None
    from confia_lean_auditor.submission_audits.router import service
    from confia_lean_auditor.submission_audits.errors import AuditConflict, SourceIntegrityError
    from confia_lean_auditor.reproducibility.service import ReproducibilityIntegrityError
    try:
        run = service().get(audit_run_id)
        record = _record_for_access(run.submission_id)
    except FileNotFoundError:
        raise HTTPException(404, "Análise não encontrada.") from None
    except (AuditConflict, SourceIntegrityError, ReproducibilityIntegrityError,
            ValidationError, ValueError, OSError):
        raise HTTPException(409, "Integridade da análise inválida.") from None
    return authorize_submission_record(user, record)


def same_origin(request: Request) -> bool:
    origin = request.headers.get("origin", "")
    parsed = urlsplit(origin)
    return bool(parsed.scheme in {"http", "https"} and parsed.netloc
                and not parsed.username and not parsed.password
                and not parsed.path and not parsed.query and not parsed.fragment
                and parsed.scheme == request.url.scheme and parsed.netloc == request.headers.get("host"))
