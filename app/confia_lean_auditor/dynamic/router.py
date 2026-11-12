"""Teacher API for preparation only. Does not route to any correction engine."""
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError
from confia_lean_auditor.auth.dependencies import auth_enabled, require_role
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.assessments.store import assessment_store, AssessmentIntegrityConflict
from .models import Actor, AssessmentReference, CreateProblem, CreateStatement, SaveRubric, ExpectedRevision, PreparationRequest, SuggestionRequest, ApproveRubric
from .store import dynamic_store, DynamicConflict
from .preparation import PreparationService
from .provider import ProviderFailure, provider_available

router = APIRouter(prefix="/dynamic", tags=["Dynamic teacher preparation"])


def teacher_actor(response: Response, user=Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    if user is not None:
        return Actor(actor_id=user.user_id, kind="TEACHER", tenant_id=user.tenant_id)
    if (not auth_enabled() and os.environ.get("CONFIA_DYNAMIC_DEMO_ENABLED") == "1"
            and os.environ.get("CONFIA_ENV", "development").lower() in {"development", "test"}):
        return Actor(actor_id="technical-demo:dynamic", kind="TECHNICAL_DEMO")
    raise HTTPException(401, "Autenticação docente necessária. Demo Dynamic exige configuração explícita.")


def guarded(operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except ProviderFailure as exc:
        raise HTTPException(503, dict(code=exc.code, message="Sugestão indisponível ou inválida. Recarregue para consultar o histórico e tente novamente.")) from None
    except FileNotFoundError:
        raise HTTPException(404, "Problema ou versão não encontrado.") from None
    except (DynamicConflict, AssessmentIntegrityConflict) as exc:
        message = str(exc) if isinstance(exc, DynamicConflict) else "Integridade do histórico inválida."
        raise HTTPException(409, message) from None
    except (ValidationError, ValueError):
        raise HTTPException(422, "Dados de problema ou rubrica inválidos.") from None
    except OSError:
        raise HTTPException(503, "Armazenamento Dynamic indisponível.") from None


@router.get("/problems")
def list_problems(actor=Depends(teacher_actor)):
    return guarded(dynamic_store().list, actor)


@router.post("/problems", status_code=201)
def create_problem(body: CreateProblem, actor=Depends(teacher_actor)):
    reference = None
    if body.assessment_id:
        doc = guarded(assessment_store().get, body.assessment_id)
        if actor.kind != "TEACHER" or doc.assessment.teacher_user_id != actor.actor_id:
            raise HTTPException(403, "Avaliação fora do escopo do professor.")
        reference = AssessmentReference(assessment_id=body.assessment_id,
            assessment_definition_sha256=doc.assessment.definition_sha256)
    return guarded(dynamic_store().create, body, actor, reference)


@router.get("/problems/{problem_id}")
@router.get("/problems/{problem_id}/versions")
def get_problem(problem_id: str, actor=Depends(teacher_actor)):
    return guarded(dynamic_store().get, problem_id, actor)


@router.get("/problems/{problem_id}/current")
def current(problem_id: str, actor=Depends(teacher_actor)):
    data = guarded(dynamic_store().get, problem_id, actor)
    active = next((p for p in data['packages'] if p['is_current']), None)
    ref = active.get('preparation_reference') if active else None
    preparation = next((p for p in data['preparation_history'] if ref and p['preparation_id'] == ref['preparation_id']), None)
    return dict(current_configuration=data["current_configuration"],
        rubric=next((r for r in data["rubrics"] if r["is_current"]), None),
        preparation=preparation, preparation_status=active['preparation_status'] if active else 'NOT_PREPARED',
        latest_preparation=data['current_preparation'], correction_available=False)


@router.post("/problems/{problem_id}/statements", status_code=201)
def statement(problem_id: str, body: CreateStatement, actor=Depends(teacher_actor)):
    return guarded(dynamic_store().statement, problem_id, body, actor)


@router.post("/problems/{problem_id}/rubrics", status_code=201)
def rubric(problem_id: str, body: SaveRubric, actor=Depends(teacher_actor)):
    return guarded(dynamic_store().save_rubric, problem_id, body, actor)


@router.patch("/problems/{problem_id}/rubrics/{rubric_id}")
def edit(problem_id: str, rubric_id: str, body: SaveRubric, actor=Depends(teacher_actor)):
    return guarded(dynamic_store().save_rubric, problem_id, body, actor, base_id=rubric_id)


@router.post("/problems/{problem_id}/rubrics/{rubric_id}/approve")
def approve(problem_id: str, rubric_id: str, body: ApproveRubric, actor=Depends(teacher_actor)):
    return guarded(dynamic_store().approve, problem_id, rubric_id, body, actor)


@router.post("/problems/{problem_id}/preparations", status_code=201)
def prepare(problem_id: str, body: PreparationRequest, actor=Depends(teacher_actor)):
    return guarded(PreparationService(dynamic_store()).start, problem_id, body, actor)


@router.get("/problems/{problem_id}/preparations")
def preparations(problem_id: str, actor=Depends(teacher_actor)):
    return guarded(dynamic_store().get, problem_id, actor)["preparation_history"]


@router.get("/problems/{problem_id}/preparations/{preparation_id}")
def preparation(problem_id: str, preparation_id: str, actor=Depends(teacher_actor)):
    rows = guarded(dynamic_store().get, problem_id, actor)["preparation_history"]
    result = next((p for p in rows if p["preparation_id"] == preparation_id), None)
    if result is None: raise HTTPException(404, "Preparação não encontrada.")
    # Proposal includes candidates and strategies; analysis includes verifier plan.
    return result


@router.post("/problems/{problem_id}/rubric-suggestion")
def suggest(problem_id: str, body: Optional[SuggestionRequest] = None, actor=Depends(teacher_actor)):
    guarded(dynamic_store().get, problem_id, actor)
    if not provider_available():
        raise HTTPException(503, dict(code="PROVIDER_NOT_CONFIGURED", message="Configure o provider Dynamic para gerar sugestões reais."))
    if body is None: raise HTTPException(422, "Informe preparação e revisão esperadas.")
    return guarded(PreparationService(dynamic_store()).suggest, problem_id, body, actor)


@router.post("/problems/{problem_id}/corrections")
def correction(problem_id: str, actor=Depends(teacher_actor)):
    guarded(dynamic_store().get, problem_id, actor)
    raise HTTPException(501, dict(code="DYNAMIC_ENGINE_NOT_IMPLEMENTED",
        message="dynamic correction engine not yet implemented"))
