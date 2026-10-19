"""Role-specific, no-store teacher decisions and minimal student results."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError

from confia_lean_auditor.assessments.router import _student_document
from confia_lean_auditor.assessments.store import AssessmentConflict
from confia_lean_auditor.auth.dependencies import require_role
from confia_lean_auditor.auth.models import AuthUser, Role
from confia_lean_auditor.institutional.store import InstitutionalScopeError
from confia_lean_auditor.reproducibility.service import ReproducibilityIntegrityError
from confia_lean_auditor.submission_audits.errors import AuditConflict
from confia_lean_auditor.submissions.store import SubmissionIntegrityConflict, TranscriptionIntegrityConflict
from . import service
from .models import CreateDecision, FinalizeDecision, StudentResult, TeacherDecisionView, UpdateDecision
from .store import DecisionConflict, DecisionIntegrityError

router = APIRouter(tags=["teacher decisions"])


def guarded(operation, *args):
    try:
        return operation(*args)
    except HTTPException:
        raise
    except InstitutionalScopeError as exc:
        raise HTTPException(exc.status_code, str(exc)) from None
    except (DecisionIntegrityError, AssessmentConflict, SubmissionIntegrityConflict, TranscriptionIntegrityConflict):
        raise HTTPException(409, "Integridade da decisão ou do vínculo institucional inválida.") from None
    except DecisionConflict as exc:
        raise HTTPException(409, str(exc)) from None
    except (AuditConflict, ReproducibilityIntegrityError):
        raise HTTPException(409, "Não foi possível validar a análise. Escolha uma análise atual ou decisão manual.") from None
    except FileNotFoundError:
        raise HTTPException(404, "Decisão, solução ou análise não encontrada.") from None
    except (ValidationError, ValueError):
        raise HTTPException(422, "Dados da decisão inválidos. Confira a pontuação e os campos.") from None
    except OSError:
        raise HTTPException(503, "Armazenamento de decisões indisponível.") from None


@router.post("/submissions/{submission_id}/teacher-decision", response_model=TeacherDecisionView)
def create_decision(submission_id: str, body: CreateDecision, response: Response,
                    user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    decision, created = guarded(service.create, user, submission_id, body)
    response.status_code = 201 if created else 200
    return decision


@router.get("/submissions/{submission_id}/teacher-decision", response_model=Optional[TeacherDecisionView])
def get_decision(submission_id: str, response: Response,
                 user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    return guarded(service.get_for_teacher, user, submission_id)


@router.patch("/teacher-decisions/{decision_id}", response_model=TeacherDecisionView)
def update_decision(decision_id: str, body: UpdateDecision, response: Response,
                    user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    return guarded(service.update, user, decision_id, body)


@router.post("/teacher-decisions/{decision_id}/finalize", response_model=TeacherDecisionView)
def finalize_decision(decision_id: str, body: FinalizeDecision, response: Response,
                      user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    return guarded(service.finalize, user, decision_id, body)


@router.post("/teacher-decisions/{decision_id}/release", response_model=TeacherDecisionView)
def release_decision(decision_id: str, response: Response,
                     user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    return guarded(service.release, user, decision_id)


@router.get("/student/assessments/{assessment_id}/items/{item_id}/result", response_model=Optional[StudentResult])
def student_result(assessment_id: str, item_id: str, response: Response,
                   user: Optional[AuthUser] = Depends(require_role(Role.STUDENT))):
    response.headers["Cache-Control"] = "no-store"
    if user is None:
        raise HTTPException(401, "Autenticação necessária.")

    def read():
        document = _student_document(user, assessment_id)
        if item_id not in {item.assessment_item_id for item in document.items}:
            raise FileNotFoundError()
        results = service.results_for_student(user, document, service.submission_store().list())
        return next((result for result in results if result.item_id == item_id), None)
    return guarded(read)
