"""Authenticated self-study endpoints expose only qualitative projections."""
from fastapi import APIRouter,Depends,Response,HTTPException
from confia_lean_auditor.auth.dependencies import require_role
from confia_lean_auditor.auth.models import Role
from pydantic import ValidationError
from confia_lean_auditor.tme.exam_store import ExamConflict
from confia_lean_auditor.tme.exam_capture import CaptureError
from confia_lean_auditor.submissions.store import SubmissionConflict,TranscriptionConflict,SubmissionIntegrityConflict


def guarded(operation,*args):
    try:return operation(*args)
    except HTTPException:raise
    except FileNotFoundError:raise HTTPException(404,'Estudo, tentativa ou leitura não encontrada.') from None
    except (ExamConflict,TranscriptionConflict,SubmissionConflict,SubmissionIntegrityConflict) as exc:
        raise HTTPException(409,str(exc) or 'Integridade ou versão do estudo divergente; recarregue antes de continuar.') from None
    except (CaptureError,ValidationError,ValueError):raise HTTPException(422,'Confira os dados e arquivos do estudo.') from None
    except OSError:raise HTTPException(503,'Armazenamento do estudo indisponível; preserve sua solução.') from None
from .study_models import CreateStudy,StudyReading,ReadingSelection,PackageSelection,NewStudyAttempt,HelpRequest
from . import study_service as service

router=APIRouter(prefix='/dynamic/self-study',tags=['Estudo autônomo'])
student=require_role(Role.STUDENT)

def no_cache(response:Response):response.headers['Cache-Control']='no-store'
router.dependencies.append(Depends(no_cache))

@router.get('')
def listing(user=Depends(student)):
    return guarded(lambda:dict(catalog=service.CATALOG,studies=service.list_studies(user)))
@router.post('',status_code=201)
def create(body:CreateStudy,user=Depends(student)):return guarded(service.create,body,user)
@router.get('/{identifier}')
def view(identifier:str,user=Depends(student)):return guarded(service.view,identifier,user)
@router.post('/{identifier}/reading')
def reading(identifier:str,body:StudyReading,user=Depends(student)):return guarded(service.revise,identifier,body,user)
@router.post('/{identifier}/recognize')
def recognize(identifier:str,user=Depends(student)):return guarded(service.recognize,identifier,user)
@router.post('/{identifier}/confirm-reading')
def confirm_reading(identifier:str,body:ReadingSelection,user=Depends(student)):return guarded(service.confirm_reading,identifier,body,user)
@router.post('/{identifier}/prepare')
def prepare(identifier:str,user=Depends(student)):return guarded(service.prepare,identifier,user)
@router.post('/{identifier}/confirm-interpretation')
def confirm_interpretation(identifier:str,body:PackageSelection,user=Depends(student)):return guarded(service.confirm_package,identifier,body,user)
@router.post('/{identifier}/attempts',status_code=201)
def new_attempt(identifier:str,body:NewStudyAttempt,user=Depends(student)):return guarded(service.create_attempt,identifier,body,user)
@router.post('/{identifier}/attempts/{aid}/reading')
def attempt_reading(identifier:str,aid:str,body:StudyReading,user=Depends(student)):return guarded(service.revise,identifier,body,user,aid)
@router.post('/{identifier}/attempts/{aid}/recognize')
def attempt_recognize(identifier:str,aid:str,user=Depends(student)):return guarded(service.recognize,identifier,user,aid)
@router.post('/{identifier}/attempts/{aid}/confirm-reading')
def attempt_confirm(identifier:str,aid:str,body:ReadingSelection,user=Depends(student)):return guarded(service.confirm_reading,identifier,body,user,aid)
@router.post('/{identifier}/attempts/{aid}/analyze')
def analyze(identifier:str,aid:str,user=Depends(student)):return guarded(service.evaluate,identifier,aid,user)
@router.post('/{identifier}/attempts/{aid}/help')
def help_level(identifier:str,aid:str,body:HelpRequest,user=Depends(student)):return guarded(service.help_level,identifier,aid,body,user)
@router.get('/{identifier}/sources/{sid}/assets/{name}')
def asset(identifier:str,sid:str,name:str,user=Depends(student)):
    def load():
        data,mime=service.asset(identifier,sid,name,user)
        return Response(data,media_type=mime,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
    return guarded(load)
