import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from pydantic import ValidationError

from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.submissions.router import store
from confia_lean_auditor.submissions.store import SubmissionIntegrityConflict, TranscriptionIntegrityConflict
from .schemas import AuditRequest, AuditRunView
from .service import AuditService, UnacceptedSource

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
    except SubmissionIntegrityConflict:
        raise HTTPException(409, "Os arquivos originais desta solução precisam ser conferidos.") from None
    except TranscriptionIntegrityConflict:
        raise HTTPException(409, "Integridade da revisão ou do aceite inválida; análise bloqueada.") from None
    except UnacceptedSource:
        raise HTTPException(409, "A transcrição precisa ser conferida antes da análise.") from None
    except FileNotFoundError:
        raise HTTPException(404, "Fonte ou análise não encontrada.") from None
    except (ValidationError, ValueError):
        raise HTTPException(409, "A transcrição precisa ser conferida antes da análise.") from None
    except OSError:
        raise HTTPException(503, "Não foi possível concluir a Análise ConfIA.") from None


@router.post("/submissions/{submission_id}/audits", response_model=AuditRunView)
def execute(submission_id: str, request: AuditRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return guarded(service().execute, submission_id, request)


@router.get("/submissions/{submission_id}/audits", response_model=list[AuditRunView])
def list_runs(submission_id: str, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return guarded(service().list, submission_id)


@router.get("/submission-audits/{audit_run_id}", response_model=AuditRunView)
def get_run(audit_run_id: str, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return guarded(service().get, audit_run_id)
