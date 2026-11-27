from confia_lean_auditor.submissions.store import TranscriptionConflict, SubmissionConflict
"""Teacher API for preparation only. Does not route to any correction engine."""
import os
from typing import Optional, Literal
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
    from confia_lean_auditor.tme.exam_store import ExamConflict
    try:
        return operation(*args, **kwargs)
    except ProviderFailure as exc:
        raise HTTPException(503, dict(code=exc.code, message="Sugestão indisponível ou inválida. Recarregue para consultar o histórico e tente novamente.")) from None
    except FileNotFoundError:
        raise HTTPException(404, "Problema ou versão não encontrado.") from None
    except (DynamicConflict, AssessmentIntegrityConflict, TranscriptionConflict, SubmissionConflict, ExamConflict) as exc:
        message = str(exc) if isinstance(exc, DynamicConflict) else "Integridade do histórico inválida."
        raise HTTPException(409, message) from None
    except (ValidationError, ValueError):
        raise HTTPException(422, "Dados de problema ou rubrica inválidos.") from None
    except OSError:
        raise HTTPException(503, "Armazenamento Dynamic indisponível.") from None


@router.get("/problems")
def list_problems(actor=Depends(teacher_actor)):
    return guarded(dynamic_store().list, actor)


@router.get("/capabilities")
def teacher_capabilities(actor=Depends(teacher_actor)):
    """Configuration presence only; never probe paid providers or expose secrets."""
    from confia_lean_auditor.recognition.registry import configured_registry
    return dict(
        rubric_suggestion_configured=provider_available(),
        semantic_evaluation_configured=bool(os.getenv("CONFIA_SEMANTIC_LLM_ENABLED") == "1"
                                          and os.getenv("OPENAI_API_KEY")),
        handwriting_recognition_configured="mathpix_image" in configured_registry().providers(),
        configuration_only=True,
    )


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
        latest_preparation=data['current_preparation'], correction_available=data["correction_available"])


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
    raise HTTPException(409, dict(code="ACCEPTED_TRANSCRIPTION_REQUIRED",
        message="Receba a resolução em /attempts e analise sua transcrição aceita no workspace compartilhado."))


from pydantic import BaseModel, ConfigDict, Field, field_validator
from confia_lean_auditor.tme.auth import require_tme_evaluator

class DynamicAttemptRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    external_candidate_ref: str = Field(min_length=1,max_length=80,pattern=r'^[A-Za-z0-9._:/-]+$')
    solution: str = Field(min_length=1,max_length=20000)
    allow_preparation_review: bool = False
    policy_profile: Optional[Literal["FORMATIVE_LIST", "SCHOOL_EXAM"]] = None

    @field_validator('solution')
    @classmethod
    def nonblank(cls, text):
        if not text.strip(): raise ValueError('empty solution')
        return text

@router.post('/problems/{problem_id}/attempts',status_code=201)
def create_attempt(problem_id: str, body: DynamicAttemptRequest, user=Depends(require_tme_evaluator)):
    from .grading_context import resolve,evaluator_actor
    from confia_lean_auditor.tme.store import case_store
    from confia_lean_auditor.tme.models import CaseCreate
    from confia_lean_auditor.submissions.router import store
    from confia_lean_auditor.submissions.text_source import receive_text
    from confia_lean_auditor.submissions.schemas import CreateTranscriptionRequest
    actor=guarded(evaluator_actor,user)
    context=guarded(resolve,problem_id,actor,body.allow_preparation_review)[0]
    case=guarded(case_store().create,CaseCreate(problem_id=problem_id,external_candidate_ref=body.external_candidate_ref,source_mode='TEXT'),user,dynamic_context=context)
    receipt=guarded(receive_text,store(),case,user,body.solution)
    case=guarded(case_store().bind,case.case_id,receipt.submission_id,user)
    guarded(store().create_transcription,receipt.submission_id,CreateTranscriptionRequest(reviewer_reference=user.user_id,segments=[dict(segment_id='text:0',page_index=0,order=0,kind='text',text=body.solution)]))
    if body.policy_profile is not None:
        from .reconciliation_service import configure_activity
        guarded(configure_activity,case,body.policy_profile)
    return case


class IndependentReviewRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    execution_key: str = Field(min_length=1,max_length=80,pattern=r'^[A-Za-z0-9_-]+$')


def independent_review_service():
    from .review_service import DynamicReviewService
    from confia_lean_auditor.submission_audits.router import service
    return DynamicReviewService(service())


@router.get('/attempts/{case_id}/audits/{run_id}/independent-reviews')
def independent_reviews(case_id: str,run_id: str,response: Response,user=Depends(require_tme_evaluator)):
    from confia_lean_auditor.tme.router import case_for
    response.headers['Cache-Control']='no-store'
    guarded(evaluator_actor_for_review,user)
    case=case_for(case_id,user)
    return guarded(independent_review_service().list,case,run_id)


def evaluator_actor_for_review(user):
    from .grading_context import evaluator_actor
    return evaluator_actor(user)


@router.post('/attempts/{case_id}/audits/{run_id}/independent-reviews',status_code=201)
def independent_review(case_id: str,run_id: str,body: IndependentReviewRequest,response: Response,user=Depends(require_tme_evaluator)):
    from confia_lean_auditor.tme.router import case_for
    response.headers['Cache-Control']='no-store'
    guarded(evaluator_actor_for_review,user)
    case=case_for(case_id,user)
    from confia_lean_auditor.tme.human_decisions import question_lock
    with question_lock(case_id,user):
        result=guarded(independent_review_service().execute,case,run_id,body.execution_key)
        from .human_decisions import project_current, current
        reconciled=reconciliation_service().current(case,run_id)
        project_current(case,reconciled,confirmed=current(case) is not None)
        return result


from .reconciliation_models import PolicyProfile

class ConfigurePolicy(BaseModel):
    model_config=ConfigDict(extra='forbid')
    policy_profile: PolicyProfile

class ReconcileRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    independent_review_id: str = Field(pattern=r'^drev_[0-9a-f]{64}$')


def reconciliation_service():
    from .reconciliation_service import ReconciliationService
    from confia_lean_auditor.submission_audits.router import service
    return ReconciliationService(service())


def reconciliation_case(case_id,user):
    from confia_lean_auditor.tme.router import case_for
    guarded(evaluator_actor_for_review,user)
    case=case_for(case_id,user)
    if not case.dynamic_context: raise HTTPException(409,'Reconciliação exige tentativa Dynamic.')
    return case

@router.get('/attempts/{case_id}/policy')
def get_policy(case_id: str,response: Response,user=Depends(require_tme_evaluator)):
    from .reconciliation_service import activity
    response.headers['Cache-Control']='no-store'
    return guarded(activity,reconciliation_case(case_id,user))

@router.post('/attempts/{case_id}/policy',status_code=201)
def configure_policy(case_id: str,body: ConfigurePolicy,response: Response,user=Depends(require_tme_evaluator)):
    from .reconciliation_service import configure_activity
    from confia_lean_auditor.tme.human_decisions import question_lock
    case=reconciliation_case(case_id,user); response.headers['Cache-Control']='no-store'
    with question_lock(case_id,user): return guarded(configure_activity,case,body.policy_profile)

@router.get('/attempts/{case_id}/audits/{run_id}/reconciliations')
def reconciliations(case_id: str,run_id: str,response: Response,user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    return guarded(reconciliation_service().list,reconciliation_case(case_id,user),run_id)

@router.post('/attempts/{case_id}/audits/{run_id}/reconciliations',status_code=201)
def reconcile(case_id: str,run_id: str,body: ReconcileRequest,response: Response,user=Depends(require_tme_evaluator)):
    from confia_lean_auditor.tme.human_decisions import question_lock
    case=reconciliation_case(case_id,user); response.headers['Cache-Control']='no-store'
    with question_lock(case_id,user):
        result=guarded(reconciliation_service().execute,case,run_id,body.independent_review_id)
        from .human_decisions import project_current, current
        project_current(case,result["reconciliation"],confirmed=current(case) is not None)
        return result

@router.get('/attempts/{case_id}/human-decisions')
def dynamic_decisions(case_id: str,response: Response,user=Depends(require_tme_evaluator)):
    from .human_decisions import history
    response.headers['Cache-Control']='no-store'
    return guarded(history,reconciliation_case(case_id,user))


from .assessment_router import router as assessment_router
router.include_router(assessment_router)
