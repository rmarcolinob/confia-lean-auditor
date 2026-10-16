import os
from pathlib import Path

from fastapi import APIRouter, Depends, Response
from confia_lean_auditor.auth.dependencies import teacher_audit_access, teacher_submission_access
from confia_lean_auditor.core.public_audit import (
    public_audit_response, public_error_response, public_response,
    public_reproducibility, PublicReproducibilityMetadata, audit_exception_response,
)
from .errors import AuditConflict, SourceIntegrityError
from pydantic import ValidationError

from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.submissions.router import store
from confia_lean_auditor.submissions.store import SubmissionIntegrityConflict, TranscriptionIntegrityConflict
from .schemas import AuditRequest
from .service import AuditService
from confia_lean_auditor.reproducibility.service import ReproducibilityIntegrityError

router = APIRouter(tags=["accepted transcription analyses"])


def engine(request):
    # Resolve at call time to avoid a main/router cycle. No HTTP to self.
    from confia_lean_auditor.main import execute_audit
    return execute_audit(request)


def service():
    configured = os.environ.get("CONFIA_SUBMISSION_AUDITS_DIR")
    root = Path(configured).absolute() if configured else get_repo_root() / "runtime" / "submission_audits"
    return AuditService(store(), root, engine)


def guarded(operation, *args):
    try:
        return operation(*args)
    except (SubmissionIntegrityConflict, TranscriptionIntegrityConflict):
        return conflict(SourceIntegrityError.code, SourceIntegrityError.message)
    except ReproducibilityIntegrityError:
        return conflict("REPRODUCIBILITY_INTEGRITY_MISMATCH",
                        "Não foi possível validar a integridade dos metadados desta análise.")
    except AuditConflict as error:
        return conflict(error.code, error.message)
    except FileNotFoundError:
        return public_error_response(404, "AUDIT_RESOURCE_NOT_FOUND", "Fonte ou análise não encontrada.")
    except (ValidationError, ValueError):
        return conflict(AuditConflict.code, AuditConflict.message)
    except OSError:
        return public_error_response(503, "AUDIT_STORAGE_UNAVAILABLE", "Não foi possível concluir a Análise ConfIA.")
    except Exception as error:
        return audit_exception_response(error)


def conflict(code, message):
    return public_error_response(409, code, message)


def public_operation(operation, *args):
    return guarded(lambda: public_audit_response(operation(*args)))


@router.post("/submissions/{submission_id}/audits", response_model=dict)
def execute(submission_id: str, request: AuditRequest, response: Response,
            _record=Depends(teacher_submission_access)):
    response.headers["Cache-Control"] = "no-store"
    return public_operation(service().execute, submission_id, request)


@router.get("/submissions/{submission_id}/audits", response_model=list[dict])
def list_runs(submission_id: str, response: Response,
              _record=Depends(teacher_submission_access)):
    response.headers["Cache-Control"] = "no-store"
    return public_operation(service().list, submission_id)


@router.get("/submission-audits/{audit_run_id}", response_model=dict)
def get_run(audit_run_id: str, response: Response,
            _record=Depends(teacher_audit_access)):
    response.headers["Cache-Control"] = "no-store"
    return public_operation(service().get, audit_run_id)


@router.get("/submission-audits/{audit_run_id}/reproducibility", response_model=PublicReproducibilityMetadata)
def get_reproducibility(audit_run_id: str, response: Response,
                        _record=Depends(teacher_audit_access)):
    response.headers["Cache-Control"] = "no-store"
    return guarded(lambda: public_response(public_reproducibility(service().reproducibility(audit_run_id))))
