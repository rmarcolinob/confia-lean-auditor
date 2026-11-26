"""Authenticated institutional gateway; no student privileges are elevated."""
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, Response
from pydantic import Field, model_validator
from confia_lean_auditor.auth.dependencies import require_role
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.submissions.schemas import SubmissionModel, Sha256, TranscriptionSegment
from confia_lean_auditor.submissions.reading_confirmation import ConfirmReading
from confia_lean_auditor.tme.exam_models import OriginalUpload, UpdatePageMapping
from confia_lean_auditor.tme.exam_router import guarded
from .school_contracts import SchoolPolicy
from . import school_service as service

router=APIRouter(prefix='/dynamic',tags=['Dynamic escolar'])
student=require_role(Role.STUDENT)
teacher=require_role(Role.TEACHER)

class Publication(SubmissionModel):
    school_id: str = Field(min_length=1,max_length=100)
    classroom_id: str = Field(min_length=1,max_length=100)
    opens_at: datetime
    closes_at: datetime
    source_definition_sha256: Sha256
    policy: SchoolPolicy
    execution_key: str = Field(min_length=1,max_length=100)
    @model_validator(mode='after')
    def dates(self):
        if not self.opens_at.tzinfo or not self.closes_at.tzinfo or self.closes_at<=self.opens_at:
            raise ValueError('Informe um período com fuso horário e término posterior ao início.')
        return self

class NewAttempt(SubmissionModel):
    definition_sha256: Sha256
    mode: Literal['TEXT','IMAGES','PDF']
    solutions: list[str] = Field(default_factory=list,max_length=100)
    original_documents: list[OriginalUpload] = Field(default_factory=list,max_length=50)
    execution_key: str = Field(min_length=1,max_length=100)
    @model_validator(mode='after')
    def input(self):
        if self.mode=='TEXT':
            if self.original_documents or not self.solutions or any(not s.strip() or len(s)>20000 for s in self.solutions):
                raise ValueError('Envie textos não vazios por questão.')
        elif self.solutions or not self.original_documents:raise ValueError('Envie somente os originais.')
        return self

class Reading(SubmissionModel):
    based_on_revision_number: int = Field(ge=0)
    segments: list[TranscriptionSegment] = Field(min_length=1,max_length=500)

class Release(SubmissionModel):
    final_correction_id: str = Field(min_length=1,max_length=100)
    release_grade: bool
    release_feedback: bool
    teacher_feedback: str = Field(default='',max_length=10000)

@router.post('/assessments/{identifier}/institutional-publications',status_code=201)
def publish(identifier:str,body:Publication,user=Depends(teacher)):
    return guarded(service.publish,identifier,body,user)

@router.get('/student/activities/{identifier}')
def activity(identifier:str,response:Response,user=Depends(student)):
    response.headers['Cache-Control']='no-store'
    def view():
        doc,owner,data=service.activity(identifier,user)
        data['attempts']=[service.student_view(d,owner) for d in service.attempts(doc,user,owner)]
        return data
    return guarded(view)

@router.post('/student/activities/{identifier}/attempts',status_code=201)
def create(identifier:str,body:NewAttempt,response:Response,user=Depends(student)):
    data,created=guarded(service.create_attempt,identifier,body,user)
    response.status_code=201 if created else 200
    return data

@router.get('/student/attempts/{identifier}')
def attempt(identifier:str,response:Response,user=Depends(student)):
    response.headers['Cache-Control']='no-store'
    return guarded(lambda:service.student_view(*service.owned_attempt(identifier,user)))

@router.put('/student/attempts/{identifier}/page-mapping')
def mapping(identifier:str,body:UpdatePageMapping,user=Depends(student)):
    return guarded(service.mapping,identifier,body,user)

@router.post('/student/attempts/{identifier}/questions/{case_id}/recognize')
def recognize(identifier:str,case_id:str,user=Depends(student)):
    return guarded(service.recognize,identifier,case_id,user)

@router.post('/student/attempts/{identifier}/questions/{case_id}/reading')
def reading(identifier:str,case_id:str,body:Reading,user=Depends(student)):
    return guarded(service.save_reading,identifier,case_id,body,user)

@router.post('/student/attempts/{identifier}/questions/{case_id}/confirm-reading')
def confirm(identifier:str,case_id:str,body:ConfirmReading,user=Depends(student)):
    return guarded(service.confirm_reading,identifier,case_id,body,user)

@router.post('/student/attempts/{identifier}/submit')
def submit(identifier:str,user=Depends(student)):
    return guarded(service.submit,identifier,user)

@router.get('/student/attempts/{identifier}/assets/{asset_id}')
def asset(identifier:str,asset_id:str,user=Depends(student)):
    def read():
        _,owner=service.owned_attempt(identifier,user)
        data,ref=service.exam_store().asset(identifier,asset_id,owner)
        return Response(data,media_type=ref.media_type,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
    return guarded(read)

@router.post('/school-attempts/{identifier}/release')
def release(identifier:str,body:Release,user=Depends(teacher)):
    return guarded(service.release,identifier,body,user)
