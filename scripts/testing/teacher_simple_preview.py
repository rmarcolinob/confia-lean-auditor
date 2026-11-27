"""Loopback-only browser acceptance fixture. Real sessions/storage, no external HTTP.

Creates NEW temporary synthetic data; never point this script at institutional data.
Run from the repository using PYTHONPATH=app. Login fixtures are documented in
tests/test_core_auth.py, not production accounts. This is not a deployment launcher.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'tests')]
for key in ('OPENAI_API_KEY','CONFIA_MATHPIX_APP_ID','CONFIA_MATHPIX_APP_KEY'):
    os.environ.pop(key,None)
os.environ.update(CONFIA_DYNAMIC_LLM_ENABLED='0',CONFIA_SEMANTIC_LLM_ENABLED='0',
                  CONFIA_ENABLE_LLM_FORMAL_STEPS='0',CONFIA_DYNAMIC_POLICY='dynamic-semantic.v1',
                  CONFIA_TME_DEMO_NO_AUTH='0',CONFIA_LEAN_AUDITOR_ROOT=str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8771)
    args=parser.parse_args()
    import pytest
    import httpx
    from test_core_auth import auth_case
    from test_dynamic_school import school,text_attempt,finish
    from confia_lean_auditor.semantic_policy.service import SemanticProvider
    from confia_lean_auditor.dynamic.semantic_credit import DynamicCreditProvider
    from confia_lean_auditor.recognition.registry import RecognizerRegistry
    from confia_lean_auditor.recognition.mathpix_image import MathpixImageProvider
    from confia_lean_auditor.tme import router
    from confia_lean_auditor.main import app
    from starlette.responses import Response
    from PIL import Image,ImageDraw,ImageFont

    data=Path(tempfile.mkdtemp(prefix='confia-teacher-synthetic-')).resolve()
    mp=pytest.MonkeyPatch()
    for key in ('AUTH','INSTITUTIONAL','ASSESSMENTS','ASSESSMENT_PARTICIPANTS','TME_EXAMS','TME_CASES','SUBMISSIONS','SUBMISSION_AUDITS','DYNAMIC','TEACHER_DECISIONS','SELF_STUDY'):
        mp.setenv('CONFIA_'+key+'_DIR',str(data/key.lower()))
    auth=auth_case.__wrapped__(data,mp)
    seeded=school.__wrapped__(auth,mp)
    attempt=text_attempt(seeded)
    result=seeded['student'].post('/dynamic/student/attempts/'+attempt['attempt_id']+'/submit')
    assert result.status_code==200,result.text
    finish(seeded,attempt)

    def semantic(self,request):
        self.metadata=dict(provider='controlled-test',model='synthetic-opinions',llm_used=False)
        text=request['solution'];levels=request['criterion'].get('credit_levels',[])
        partial='x=5' in text and bool(levels) and request['stage']!='independent_reviewer'
        decision='partial' if partial else 'met' if ('3*6=18' in text or '2x=12' in text) else 'review'
        why=('SIMULADO: a subtração está justificada, mas o resultado final está incorreto.' if partial else
             'SIMULADO: este parecer controlado é usado para testar o fluxo e as divergências, não para validar matemática.')
        response=dict(decision=decision,justification=why,quotes=[text])
        if request.get('credit_contract'):
            response.update(level_id=levels[0]['level_id'] if partial else None,
                            finding='MATHEMATICAL_ERROR' if partial else 'VALID_ARGUMENT' if decision=='met' else 'UNCERTAIN',
                            dependencies=[])
        return response
    mp.setattr(SemanticProvider,'__call__',semantic)
    mp.setattr(DynamicCreditProvider,'__call__',semantic)
    # Only controlled transports run; no real credentials or remote probes.
    mp.setenv('CONFIA_SEMANTIC_LLM_ENABLED','1');mp.setenv('OPENAI_API_KEY','synthetic-not-a-key')
    mp.setenv('CONFIA_MATHPIX_APP_ID','simulation');mp.setenv('CONFIA_MATHPIX_APP_KEY','simulation')
    reading='Q1: Divido 24 em quatro partes: 24/4=6; tres partes sao 3*6=18.\nQ2: Subtraio 6 dos dois lados: 2x=12. Divido por 2, mas obtenho x=5.'
    class SimulatedOCR(MathpixImageProvider):
        display_label='OCR SIMULADO — teste de interface'
        public_parameters={**MathpixImageProvider.public_parameters,'simulation':True}
    registry=RecognizerRegistry()
    registry.register('mathpix_image',lambda:SimulatedOCR(httpx.MockTransport(lambda _:httpx.Response(200,json={'text':reading}))))
    mp.setattr(router,'configured_registry',lambda:registry)
    def no_network(*args,**kwargs):
        raise RuntimeError('External HTTP forbidden in synthetic browser validation')
    mp.setattr(httpx.HTTPTransport,'handle_request',no_network)
    mp.setattr(httpx.AsyncHTTPTransport,'handle_async_request',no_network)

    async def identify_simulation(request,call_next):
        response=await call_next(request)
        if 'text/html' not in response.headers.get('content-type',''):
            return response
        body=b''.join([chunk async for chunk in response.body_iterator])
        banner='<aside role="status" style="padding:10px 24px;background:#fff0c2;color:#483400;text-align:center;font:600 14px system-ui">TESTE SINTÉTICO · OCR e pareceres simulados · sessões e armazenamento reais · sem chamadas pagas</aside>'
        import re
        body=re.sub(rb'(<body[^>]*>)',lambda m:m[0]+banner.encode(),body,count=1)
        headers=dict(response.headers);headers.pop('content-length',None)
        return Response(body,status_code=response.status_code,headers=headers)

    font_path=Path('/System/Library/Fonts/Supplemental/Arial.ttf')
    font=ImageFont.truetype(str(font_path),24) if font_path.exists() else ImageFont.load_default()
    pages=[]
    for number,lines in enumerate([
        ['DADOS SINTETICOS - PROVA EF','Participante: SINTETICO-01','Q1 - Tres quartos de 24','Divido em 4 partes iguais. 24/4=6.','Tres partes: 3*6=18.','Q2 - Resolva 2x+6=18','Subtraio 6 dos dois lados: 2x=12.','Divido por 2, mas obtenho x=5.'],
        ['DADOS SINTETICOS - CONTINUACAO','Q1 - Explicacao','Cada parte tem 6 unidades.','Escolho tres partes iguais: 3*6=18.']
    ],1):
        image=Image.new('RGB',(1000,1100),'white');draw=ImageDraw.Draw(image)
        for i,line in enumerate(lines):draw.text((50,60+i*75),line,fill='#15243b',font=font)
        image.save(data/f'pagina-{number}.png');pages.append(image)
    pages[0].save(data/'prova-sintetica.pdf',save_all=True,append_images=pages[1:])
    (data/'arquivo-invalido.txt').write_text('Somente teste de rejeição de arquivo.')
    print(json.dumps(dict(data_dir=str(data),url=f'http://127.0.0.1:{args.port}',mode='SYNTHETIC ONLY'),ensure_ascii=False),flush=True)
    import uvicorn
    from starlette.middleware.base import BaseHTTPMiddleware
    uvicorn.run(BaseHTTPMiddleware(app,dispatch=identify_simulation),host='127.0.0.1',port=args.port,access_log=False)


if __name__=='__main__':
    main()
