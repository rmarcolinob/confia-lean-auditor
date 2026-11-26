"""Three basic-school questions; synthetic images and simulated OCR/LLM only."""
import base64
from decimal import Decimal
from uuid import uuid4
import httpx
import pytest
from test_dynamic_dy3 import setup
from test_dynamic_credit_dependencies import problem, criterion as base_criterion, simulated, opinion
from test_dynamic_dy6 import activity,add_question,activities,Revision,USER,audit_question
from test_tme_full_exam import png,pdf
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.recognition.mathpix_image import MathpixImageProvider
from confia_lean_auditor.submission_audits.router import service
from confia_lean_auditor.tme import router

def criterion(cid,points,order,**kw):
    description=kw.pop('description',None);c=base_criterion(cid,points,order,**kw)
    if description:c['description']=description
    return c


TEXTS=['Divido 24 em quatro partes iguais.', 'Cada parte vale 24/4=6; três partes valem 3*6=18.',
       'Subtraio 6 dos dois lados: 2x=12. Divido ambos os lados por 2; obtenho x=5.',
       'Somando 5+3=8, afirmo que o perímetro é 8 cm.']


def cohort(setup,monkeypatch,as_pdf=False):
    root,client=setup
    monkeypatch.setenv('CONFIA_ASSESSMENTS_DIR',str(root/'assessments'))
    monkeypatch.setenv('CONFIA_ASSESSMENT_PARTICIPANTS_DIR',str(root/'participants'))
    monkeypatch.setenv('CONFIA_DYNAMIC_POLICY','dynamic-semantic.v1')
    cs=[ [criterion('fraction',2,1,description='Explicar e calcular três quartos de 24.')],
        [criterion('method',1,1,description='Subtrair 6 dos dois membros e obter 2x=12.'),
         criterion('answer',1,2,description='Isolar x e calcular corretamente seu valor.',dependencies=['method'],
          credit_levels=[dict(level_id='division',points='.5',description='Indicar a divisão de ambos os membros por 2, mas errar o cálculo final.')],
          dependency_rules=[dict(criterion_id='method',kind='MATHEMATICAL',condition='Obter a equação equivalente 2x=12.')])],
        [criterion('perimeter',2,1,description='Justificar o perímetro como soma dos quatro lados e calcular 16 cm.')]]
    # criterion helper accepts a description override through kwargs.
    statements=['Calcule três quartos de 24 e explique.','Resolva 2x+6=18 explicando as operações.','Um retângulo tem lados 5 cm e 3 cm. Calcule o perímetro e justifique.']
    doc=activity('SCHOOL_EXAM')
    for criteria,statement in zip(cs,statements):doc=add_question(doc,problem(criteria,statement))
    doc=activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),USER)
    originals=[pdf(3)] if as_pdf else [png(c) for c in ['red','blue','green']]
    body=dict(assessment_identifier=doc['assessment']['assessment_id'],external_participant_code='SINTETICO-EF-01',idempotency_key='handwriting',
        original_documents=[dict(media_type='application/pdf' if as_pdf else 'image/png',content_base64=base64.b64encode(b).decode()) for b in originals])
    response=client.post('/tme/exam-submissions',json=body);assert response.status_code==201,response.text
    exam=response.json();eid=exam['submission']['submission_id'];cases=exam['question_attempts'];pages=exam['submission']['pages']
    bindings=[dict(question_attempt_id=cases[q]['case_id'],exam_page_id=pages[p]['exam_page_id'],order=i+1) for q,indices in enumerate([[0,1],[1],[2]]) for i,p in enumerate(indices)]
    assert client.put(f'/tme/exam-submissions/{eid}/page-mapping',json=dict(expected_version=1,bindings=bindings)).status_code==200
    calls=simulated(monkeypatch,{'fraction':'met','method':'met','answer':opinion('partial','division'),'perimeter':'not_met'},
        {'fraction':'met','method':'met','answer':'met','perimeter':'not_met'})
    return root,client,exam,originals,calls


def workspace(client,case):
    r=client.get(f"/tme/question-attempts/{case['case_id']}/workspace");assert r.status_code==200,r.text
    return r.json()


def manual(client,case,texts):
    w=workspace(client,case);base=f"/tme/cases/{case['case_id']}/transcriptions"
    segments=[dict(segment_id=f'page:{i}',page_index=i,order=0,kind='text',text=t) for i,t in enumerate(texts)]
    if w['history']:
        h=w['history'];r=client.post(base+f"/{h['transcription']['transcription_id']}/revisions",json=dict(based_on_revision_number=h['revisions'][-1]['revision_number'],segments=segments))
    else:r=client.post(base,json=dict(origin='manual',expected_mapping_version=w['mapping_version'],segments=segments))
    assert r.status_code==201,r.text
    return r.json()


def confirm(client,case):
    w=workspace(client,case);r=w['reading_review'];tid=w['history']['transcription']['transcription_id']
    return client.post(f"/tme/question-attempts/{case['case_id']}/transcriptions/{tid}/confirm-reading",json=dict(revision_number=r['revision_number'],revision_sha256=r['revision_sha256'],confirmed=True,question_scope_confirmed=True))


def reconcile(client,case,run):
    url=f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}"
    r=client.post(url+'/independent-reviews',json=dict(execution_key=uuid4().hex));assert r.status_code==201,r.text
    r=client.post(url+'/reconciliations',json=dict(independent_review_id=r.json()['review']['review_id']));assert r.status_code==201,r.text
    return r.json()['reconciliation']


def test_three_questions_images_ocr_scope_partial_adjudication_finalization(setup,monkeypatch):
    root,client,exam,originals,calls=cohort(setup,monkeypatch);cases=exam['question_attempts'];eid=exam['submission']['submission_id']
    responses=iter([TEXTS[0],TEXTS[1]+'\nQ2: '+TEXTS[2],TEXTS[1]+'\nQ2: '+TEXTS[2],TEXTS[3]])
    monkeypatch.setenv('CONFIA_MATHPIX_APP_ID','test');monkeypatch.setenv('CONFIA_MATHPIX_APP_KEY','test')
    registry=RecognizerRegistry();registry.register('mathpix_image',lambda:MathpixImageProvider(httpx.MockTransport(lambda _:httpx.Response(200,json={'text':next(responses)}))))
    monkeypatch.setattr(router,'configured_registry',lambda:registry)
    for case in cases:
        r=client.post(f"/tme/cases/{case['case_id']}/recognize",json={});assert r.status_code==200,r.text
        w=workspace(client,case);assert w['reading_review']['automatic'] and w['reading_review']['status']=='NEEDS_CONFIRMATION'
    for case,texts in zip(cases,[TEXTS[:2],[TEXTS[2]],[TEXTS[3]]]):
        manual(client,case,texts)
        assert confirm(client,case).status_code==200
    w=workspace(client,cases[0]);assert w['reading_review']['shared_pages']==[2]
    before={p:p.read_bytes() for p in (root/'exams'/eid).glob('original_*')}
    finals=[]
    for index,case in enumerate(cases):
        run=audit_question(client,case);rec=reconcile(client,case,run)
        raw=service().get(run['audit_run_id']);assert raw.source.provenance.reading_confirmation
        assert raw.source.provenance.reading_confirmation.case_id==case['case_id']
        w=workspace(client,case)
        assert all(e['source_pages'] for e in w['current_audit']['evidences'])
        if index==0:
            assert TEXTS[2] not in raw.source.solution_text
            assert {p['page_number'] for e in w['current_audit']['evidences'] for p in e['source_pages']}=={1,2}
        if index==1:
            assert TEXTS[1] not in raw.source.solution_text and rec['reconciled_suggested_score'] is None
            body=dict(decision_type='ADJUST_SCORE',final_points='1.5',override_reason='A operação de divisão está indicada; o cálculo final está incorreto.',
                adjudication=dict(rubric_sha256=rec['context']['rubric_sha256'],criteria=[dict(criterion_id='method',final_points='1',justification='Transformação equivalente correta.'),dict(criterion_id='answer',final_points='.5',justification='Nível parcial de divisão previsto na rubrica.',dependency_justification='A etapa anterior foi corretamente realizada.')]))
        else:body=dict(decision_type='ACCEPT_SUGGESTION')
        body.update(audit_run_id=run['audit_run_id'],transcription_version_id=run['transcription_version_id'],reconciliation_id=rec['reconciliation_id'],execution_key=uuid4().hex)
        d=client.post(f"/tme/cases/{case['case_id']}/decision",json=body);assert d.status_code==201,d.text;finals.append(Decimal(d.json()['final_points']))
    summary=client.get(f'/tme/exam-submissions/{eid}/correction').json();assert summary['ready_to_finalize']
    r=client.post(f'/tme/exam-submissions/{eid}/correction/finalize',json=dict(expected_snapshot_sha256=summary['snapshot_sha256'],execution_key='close'))
    assert r.status_code==201,r.text
    assert Decimal(r.json()['final_total'])==sum(finals) and r.json()['suggested_total_snapshot'] is None
    assert all(p.read_bytes()==b for p,b in before.items())
    for i,data in enumerate(originals,1):assert client.get(f'/tme/exam-submissions/{eid}/assets/original_{i:04d}').content==data
    assert all(TEXTS[2] not in c['solution'] for c in calls if c['criterion']['criterion_id']=='fraction')


def test_technical_acceptance_cannot_authorize_manuscript_and_revision_invalidates(setup,monkeypatch):
    _,client,exam,_,calls=cohort(setup,monkeypatch,as_pdf=True);case=exam['question_attempts'][0]
    r=manual(client,case,TEXTS[:2]);tid=r['transcription_id'];base=f"/tme/cases/{case['case_id']}"
    a=client.post(base+f'/transcriptions/{tid}/accept',json=dict(revision_number=1)).json()
    req=dict(transcription_id=tid,revision_number=1,acceptance_id=a['acceptance']['acceptance_id'],execution_key='unconfirmed')
    assert client.post(base+'/audits',json=req).status_code==409 and not calls
    assert confirm(client,case).status_code==200
    req['execution_key']='confirmed';run=client.post(base+'/audits',json=req);assert run.status_code==200,run.text
    raw=service()._path(run.json()['audit_run_id']).read_bytes()
    manual(client,case,[TEXTS[0],TEXTS[1]+' Corrigi a leitura.'])
    w=workspace(client,case);assert w['reading_review']['status']=='NEEDS_CONFIRMATION' and w['audits'][0]['stale']
    assert service()._path(run.json()['audit_run_id']).read_bytes()==raw
    assert confirm(client,case).status_code==200
    manual(client,case,[TEXTS[0],'[Trecho ilegível]'])
    assert confirm(client,case).status_code==409
    assert workspace(client,case)['reading_review']['status']=='UNRESOLVED'


def test_confirmation_scope_staleness_authorization_and_integrity(setup,monkeypatch):
    root,client,exam,_,_=cohort(setup,monkeypatch);a,b,_=exam['question_attempts']
    manual(client,a,TEXTS[:2]);manual(client,b,[TEXTS[2]])
    wa=workspace(client,a);ra=wa['reading_review'];tid=wa['history']['transcription']['transcription_id']
    body=dict(revision_number=1,revision_sha256=ra['revision_sha256'],confirmed=True,question_scope_confirmed=True)
    url=f"/tme/question-attempts/{a['case_id']}/transcriptions/{tid}/confirm-reading"
    wrong=url.replace(a['case_id'],b['case_id']);assert client.post(wrong,json=body).status_code==409
    assert client.post(url,json=dict(body,revision_sha256='0'*64)).status_code==409
    assert client.post(url,json=dict(body,confirmed=False)).status_code==422
    from confia_lean_auditor.tme.auth import require_tme_evaluator,TMEEvaluator
    from confia_lean_auditor.main import app
    app.dependency_overrides[require_tme_evaluator]=lambda:TMEEvaluator('another-teacher')
    try:assert client.post(url,json=body).status_code==403
    finally:app.dependency_overrides.pop(require_tme_evaluator)
    assert client.post(url,json=body).status_code==200
    p=next((root/'submissions').rglob('reading_confirmations/*.json'));p.write_text('{}')
    assert client.get(f"/tme/question-attempts/{a['case_id']}/workspace").status_code==409


@pytest.mark.parametrize('kind',['original','incomplete','unknown','stale_confirmation'])
def test_unresolved_or_tampered_sources_do_not_become_zero(setup,monkeypatch,kind):
    root,client,exam,_,calls=cohort(setup,monkeypatch);case=exam['question_attempts'][0]
    manual(client,case,TEXTS[:2])
    if kind=='original':
        p=root/'exams'/exam['submission']['submission_id']/'original_0001';p.write_bytes(b'tampered')
        assert confirm(client,case).status_code==409
    elif kind=='stale_confirmation':
        w=workspace(client,case);r=w['reading_review'];tid=w['history']['transcription']['transcription_id']
        manual(client,case,[TEXTS[0],TEXTS[1]+' Retifiquei a leitura.'])
        response=client.post(f"/tme/question-attempts/{case['case_id']}/transcriptions/{tid}/confirm-reading",json=dict(revision_number=r['revision_number'],revision_sha256=r['revision_sha256'],confirmed=True,question_scope_confirmed=True))
        assert response.status_code==409
    else:
        w=workspace(client,case);tid=w['history']['transcription']['transcription_id']
        segments=[dict(segment_id='p0',page_index=0,order=0,kind='text',text=TEXTS[0])]
        if kind=='unknown':segments.append(dict(segment_id='p1',page_index=1,order=0,kind='unknown',text='Sinal não legível'))
        assert client.post(f"/tme/cases/{case['case_id']}/transcriptions/{tid}/revisions",json=dict(based_on_revision_number=1,segments=segments)).status_code==201
        assert confirm(client,case).status_code==409
    assert not calls and not list((root/'audits').glob('aud_*.json'))


def test_provider_failure_after_confirmed_reading_remains_pending(setup,monkeypatch):
    _,client,exam,_,_=cohort(setup,monkeypatch);case=exam['question_attempts'][0]
    manual(client,case,TEXTS[:2]);assert confirm(client,case).status_code==200
    simulated(monkeypatch,{'fraction':'error'})
    run=audit_question(client,case);rec=reconcile(client,case,run)
    assert run['suggested_score'] is None and rec['reconciled_suggested_score'] is None
    assert rec['technical_uncertainty']
