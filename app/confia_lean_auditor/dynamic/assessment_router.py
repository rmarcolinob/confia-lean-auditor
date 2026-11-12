"""DY6 preparation routes over the shared Assessment; no capture/grading mutation."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from fastapi import APIRouter, Depends, Response
from confia_lean_auditor.tme.auth import require_tme_evaluator
from . import assessment_service as service
from .router import guarded

router=APIRouter()
class Request(BaseModel):
    model_config=ConfigDict(extra='forbid')
class Create(Request):
    title: str=Field(min_length=1,max_length=160)
    instructions: str=Field(default='',max_length=10000)
    policy_profile: Literal['FORMATIVE_LIST','SCHOOL_EXAM']
    feedback_policy: Literal['WITHHOLD','AFTER_CONFIRMATION']='WITHHOLD'
class Revision(Request):
    expected_revision: int=Field(ge=0)
class Add(Revision):
    problem_id: str=Field(pattern=r'^dyn_[0-9a-f]{32}$')
class Prepare(Request):
    problem_ids: list[str]=Field(default_factory=list,max_length=100)
    generate_rubrics: bool=True
    force: bool=False
class Approval(Request):
    problem_id: str
    rubric_id: str
    expected_revision: int
    acknowledge_warnings: bool=False
class Approve(Request):
    questions: list[Approval]=Field(min_length=1,max_length=100)

@router.get('/assessments')
def listing(response:Response,user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    from confia_lean_auditor.assessments.store import assessment_store
    return [guarded(service.view,d,user) for d in assessment_store().list() if d.assessment.correction_mode=='DYNAMIC' and d.assessment.teacher_user_id==user.user_id]
@router.post('/assessments',status_code=201)
def create(body:Create,user=Depends(require_tme_evaluator)): return guarded(service.create,body,user)
@router.get('/assessments/{identifier}')
def get(identifier:str,response:Response,user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    return guarded(service.get,identifier,user)
@router.post('/assessments/{identifier}/questions',status_code=201)
def add(identifier:str,body:Add,user=Depends(require_tme_evaluator)): return guarded(service.add,identifier,body,user)
@router.post('/assessments/{identifier}/preparations')
def prepare(identifier:str,body:Prepare,user=Depends(require_tme_evaluator)): return guarded(service.prepare_many,identifier,body,user)
@router.post('/assessments/{identifier}/rubrics/approve')
def approve(identifier:str,body:Approve,user=Depends(require_tme_evaluator)): return guarded(service.approve_many,identifier,body,user)
@router.post('/assessments/{identifier}/activate')
def activate(identifier:str,body:Revision,user=Depends(require_tme_evaluator)): return guarded(service.activate,identifier,body,user)
@router.post('/assessments/{identifier}/successor',status_code=201)
def successor(identifier:str,user=Depends(require_tme_evaluator)): return guarded(service.successor,identifier,user)
@router.post('/assessments/{identifier}/close')
def close(identifier:str,user=Depends(require_tme_evaluator)):
    guarded(service.owned,identifier,user)
    from confia_lean_auditor.assessments.store import assessment_store
    guarded(assessment_store().close,identifier)
    service.record_event(identifier,'assessment_closed',user)
    return guarded(service.get,identifier,user)
