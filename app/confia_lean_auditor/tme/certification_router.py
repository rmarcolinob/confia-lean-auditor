"""Opt-in evaluator-owned shadow certification endpoints; no anonymous new scope."""
from typing import Optional, Literal
from fastapi import APIRouter, Depends, Request, Response, Query, HTTPException
from starlette.concurrency import run_in_threadpool
from .auth import require_tme_evaluator
from .exam_router import guarded
from . import certification as cert
from . import certification_gold as gold

router=APIRouter(prefix='/assessments/{assessment_id}/certification')


@router.get('')
@router.get('/export.json')
def summary(assessment_id: str, response: Response, selection: Literal['finalized','current']='finalized',
            engine_mode: Optional[str]=Query(None,max_length=80,pattern=r'^[A-Za-z0-9_-]+$'),
            gold_version: Optional[int]=Query(None,ge=1),user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    response.headers['Content-Disposition']='attachment; filename="certification.json"'
    return guarded(cert.build,assessment_id,user,selection,engine_mode,gold_version)


@router.get('/export.csv')
def csv_export(assessment_id: str, selection: Literal['finalized','current']='finalized',
               engine_mode: Optional[str]=Query(None,max_length=80,pattern=r'^[A-Za-z0-9_-]+$'),
               gold_version: Optional[int]=Query(None,ge=1),user=Depends(require_tme_evaluator)):
    data=guarded(cert.build,assessment_id,user,selection,engine_mode,gold_version)
    return Response(cert.export_csv(data),media_type='text/csv',headers={'Cache-Control':'no-store',
        'X-Content-Type-Options':'nosniff','Content-Disposition':'attachment; filename="certification.csv"'})


@router.get('/gold')
def get_gold(assessment_id: str,response: Response,version: Optional[int]=Query(None,ge=1),user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    return guarded(cert.get_gold,assessment_id,user,version)


@router.post('/gold',status_code=201)
async def import_gold(assessment_id: str,request: Request,response: Response,
                      source_id: Optional[str]=None,dataset_version: Optional[str]=None,
                      expected_version: Optional[int]=Query(None,ge=0),user=Depends(require_tme_evaluator)):
    guarded(gold.owned_assessment,assessment_id,user)
    content_type=request.headers.get('content-type','').split(';')[0].strip().lower()
    if content_type not in {'text/csv','application/json'}:raise HTTPException(415,'Use application/json ou text/csv.')
    raw=bytearray()
    async for chunk in request.stream():
        if len(raw)+len(chunk)>2*1024*1024:raise HTTPException(413,'Payload acima do limite permitido.')
        raw.extend(chunk)
    raw=bytes(raw)
    if content_type=='text/csv':body=guarded(gold.csv_import,raw,source_id,dataset_version,expected_version)
    elif content_type=='application/json':body=guarded(gold.GoldImport.model_validate_json,raw)
    else:raise HTTPException(415,'Use application/json ou text/csv.')
    value=await run_in_threadpool(guarded,gold.import_gold,assessment_id,body,user)
    response.headers['Cache-Control']='no-store'
    return cert.gold_metadata(value)


from . import certification_runs as runs
from .certification_models import FreezeDataset, CreateCertificationRun


@router.post('/datasets',status_code=201)
def freeze_dataset(assessment_id: str,body: FreezeDataset,response: Response,user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    return guarded(runs.freeze,assessment_id,body,user)


@router.post('/runs',status_code=201)
def create_run(assessment_id: str,body: CreateCertificationRun,response: Response,user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    return guarded(runs.create,assessment_id,body,user)


@router.get('/runs')
def list_runs(assessment_id: str,response: Response,user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    return guarded(runs.listing,assessment_id,user)


@router.get('/runs/{run_id}')
@router.get('/runs/{run_id}/export.json')
def get_run(assessment_id: str,run_id: str,response: Response,user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    return guarded(runs.read,assessment_id,run_id,user)


@router.get('/runs/{run_id}/export.csv')
def run_csv(assessment_id: str,run_id: str,user=Depends(require_tme_evaluator)):
    value=guarded(runs.read,assessment_id,run_id,user)
    return Response(runs.export_csv(value),media_type='text/csv',headers={'Cache-Control':'no-store','Content-Disposition':'attachment; filename="dynamic-certification.csv"'})


@router.get('/runs/{run_id}/report.md')
def run_report(assessment_id: str,run_id: str,user=Depends(require_tme_evaluator)):
    value=guarded(runs.read,assessment_id,run_id,user)
    return Response(runs.markdown(value),media_type='text/markdown',headers={'Cache-Control':'no-store','Content-Disposition':'attachment; filename="dynamic-certification.md"'})


from . import certification_paired as paired


@router.post('/comparisons',status_code=201)
def compare_engines(assessment_id: str,body: paired.PairedRequest,response: Response,user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    return guarded(paired.compare,assessment_id,body,user)


@router.get('/comparisons/{comparison_id}')
def get_comparison(assessment_id: str,comparison_id: str,response: Response,user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    return guarded(runs.read,assessment_id,comparison_id,user)


@router.get('/datasets/{dataset_id}')
def get_dataset(assessment_id: str,dataset_id: str,response: Response,user=Depends(require_tme_evaluator)):
    response.headers['Cache-Control']='no-store'
    return guarded(runs.read,assessment_id,dataset_id,user)
