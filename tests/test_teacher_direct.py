"""Real authenticated direct intake and engines; providers OFF, no simulated opinions."""
import base64
import json
from pathlib import Path
import pytest
from test_core_auth import auth_case, PASSWORD
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.submissions.text_source import DIRECT_CONFIRMATION
from test_tme_accepted_integration import solution_for, FULL


@pytest.fixture
def direct(auth_case, monkeypatch):
    store, users, factory, root = auth_case
    for key, folder in [('CONFIA_TME_CASES_DIR','cases'),('CONFIA_DYNAMIC_DIR','dynamic'),
                        ('CONFIA_TME_EXAMS_DIR','exams'),('CONFIA_TME_INDEX_DIR','index')]:
        monkeypatch.setenv(key,str(root/folder))
    monkeypatch.setenv('CONFIA_DYNAMIC_POLICY','dynamic-semantic.v1')
    monkeypatch.setenv('CONFIA_SPECIALIZED_POLICY','semantic-b-minimal.v1')
    monkeypatch.setenv('CONFIA_SEMANTIC_LLM_ENABLED','0')
    monkeypatch.setenv('CONFIA_DYNAMIC_LLM_ENABLED','0')
    # No classroom assignment or institutional publication for this teacher.
    store.create_user(login='direct.teacher',display_name='Professor direto sintético',role=Role.TEACHER,
                      password=PASSWORD,tenant_id='direct-school',classroom_ids=[])
    return factory('direct.teacher'), factory, root


def post(client, url, body, status=200):
    response=client.post(url,json=body)
    assert response.status_code==status,response.text
    return response.json()


def receive(client, problem, text, original=None):
    body=dict(problem_id=problem,external_candidate_ref='SYNTHETIC-DIRECT',solution=text,allow_preparation_review=True)
    if original:body['original']=original
    return post(client,'/tme/direct-solutions',body,201)


def history(client, case):
    base=f"/tme/cases/{case['case_id']}"
    rows=client.get(base+'/transcriptions').json()
    tid=rows[0]['transcription']['transcription_id']
    return base,tid,client.get(base+'/transcriptions/'+tid).json()


def audit(client,case):
    base,tid,h=history(client,case);revision=h['revisions'][-1]['revision_number']
    # No audit run exists before explicit confirmation.
    assert client.get(base+'/audits').json()==[]
    accepted=post(client,f'{base}/transcriptions/{tid}/accept',dict(revision_number=revision,acceptance_note=DIRECT_CONFIRMATION))
    run=post(client,base+'/audits',dict(transcription_id=tid,revision_number=revision,acceptance_id=accepted['acceptance']['acceptance_id']))
    assert run['status']=='COMPLETED',run
    return run


def test_specialized_real_lean_direct_and_reload(direct):
    client,factory,root=direct
    solutions=solution_for(1,FULL[1])
    text='\n\n'.join(f'[{item}]\n'+(value if isinstance(value,str) else value.get('text','')) for item,value in solutions.items())
    case=receive(client,'TME2026P1',text)
    run=audit(client,case)
    assert run['result']['score'] is not None
    checks=[fact['student_check'] for fact in run['result']['bridge']['auditor']['facts'] if fact.get('student_check')]
    assert checks and all(check['status']=='verified' and check['compiled'] for check in checks)
    assert run['result']['score']==run['result']['max_score']==20
    assert run['result']['context']['use_lean'] is True
    resumed=factory('direct.teacher')
    assert resumed.get(f"/tme/cases/{case['case_id']}/original-text").json()['text']==text
    saved=resumed.get(f"/tme/cases/{case['case_id']}/audits").json()
    assert saved[0]['audit_run_id']==run['audit_run_id']
    (root/'specialized-result.json').write_text(json.dumps(run,ensure_ascii=False,indent=2))


def test_dynamic_manual_rubric_real_grader_provider_off(direct):
    client,factory,root=direct
    d=post(client,'/dynamic/problems',dict(statement='Resolva nos reais: 2y² - 14y + 24 = 0. Justifique.',max_score='10',correction_mode='DYNAMIC'),201)
    pid=d['problem']['problem_id']
    assert client.post('/tme/direct-solutions',json=dict(problem_id=pid,external_candidate_ref='NO-APPROVAL',solution='y=3')).status_code==409
    from test_dynamic_dy3 import CRITERIA, FACTOR
    d=post(client,f'/dynamic/problems/{pid}/rubrics',dict(expected_revision=d['revision'],statement_version=1,max_score='10',criteria=CRITERIA),201)
    d=post(client,f"/dynamic/problems/{pid}/rubrics/{d['rubrics'][-1]['rubric_id']}/approve",dict(expected_revision=d['revision'],acknowledge_warnings=True))
    case=receive(client,pid,FACTOR);run=audit(client,case)
    assert run['engine_mode']=='DYNAMIC'
    base=f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}"
    review=post(client,base+'/independent-reviews',dict(execution_key='teacher-simplified'),201)
    rec=post(client,base+'/reconciliations',dict(independent_review_id=review['review']['review_id']),201)
    assert rec['reconciliation']['review_required']
    assert run['result']['score'] is None
    assert rec['reconciliation']['reconciled_suggested_score'] is None
    assert client.get(f"/tme/cases/{case['case_id']}/decision").json() is None
    resumed=factory('direct.teacher')
    assert resumed.get(base+'/reconciliations').json()[0]['reconciliation']==rec['reconciliation']
    # Explicit HUMAN decision on synthetic evidence, never an automatic LLM score.
    rec_data=rec['reconciliation']
    reasons=[('method','4','A divisão por 2 e a fatoração (y-3)(y-4) preservam a equação.'),('roots','3','A fatoração apresentada fornece explicitamente as raízes 3 e 4.'),('check','3','A solução apresenta as duas substituições, ambas com resultado zero.')]
    decision=post(client,f"/tme/cases/{case['case_id']}/decision",dict(audit_run_id=run['audit_run_id'],reconciliation_id=rec_data['reconciliation_id'],max_points='10',final_points='10',override_reason='Conferência matemática humana dos três critérios, com provider desligado.',adjudication=dict(rubric_sha256=rec_data['context']['rubric_sha256'],criteria=[dict(criterion_id=cid,final_points=points,justification=why) for cid,points,why in reasons])),201)
    assert decision['suggested_points'] is None
    assert decision['review_required_snapshot'] is True
    assert float(decision['final_points'])==10
    assert client.get(base+'/reconciliations').json()[0]['reconciliation']==rec_data
    (root/'dynamic-result.json').write_text(json.dumps(dict(run=run,review=review,reconciliation=rec),ensure_ascii=False,indent=2))


def test_original_integrity_scope_confirmation_and_revision(direct):
    from test_tme_full_exam import png
    client,factory,root=direct
    raw=png('blue');original=dict(media_type='image/png',content_base64=base64.b64encode(raw).decode())
    case=receive(client,'TME2026P1','[a]\nx=2',original)
    base,tid,h=history(client,case)
    assert client.get(base+'/original-document').content==raw
    assert factory('teacher.a').get(base+'/original-document').status_code==403
    assert factory('student.a').post('/tme/direct-solutions',json={}).status_code==403
    # Technical acceptance is not the explicit confirmation required by direct intake.
    accepted=post(client,f'{base}/transcriptions/{tid}/accept',dict(revision_number=1))
    request=dict(transcription_id=tid,revision_number=1,acceptance_id=accepted['acceptance']['acceptance_id'])
    assert client.post(base+'/audits',json=request).status_code==409
    # A new revision must receive a new explicit confirmation.
    post(client,f'{base}/transcriptions/{tid}/revisions',dict(based_on_revision_number=1,segments=[dict(segment_id='new',page_index=0,order=0,kind='text',text='[a]\nx=3')]),201)
    assert client.get(base+'/audits').json()==[]
    original_path=root/'submissions'/case['submission_id']/'original_1.bin'
    original_path.write_bytes(b'changed')
    assert client.get(base+'/original-document').status_code==409


def test_invalid_original_rejected_before_case_creation(direct):
    client,_,_=direct
    before=client.get('/tme/cases').json()
    response=client.post('/tme/direct-solutions',json=dict(problem_id='TME2026P1',external_candidate_ref='INVALID',solution='x=2',original=dict(media_type='image/png',content_base64=base64.b64encode(b'not an image').decode())))
    assert response.status_code==422
    assert client.get('/tme/cases').json()==before


@pytest.mark.parametrize('media_type',['application/pdf','image/jpeg'])
def test_supported_originals_preserved_without_recognition(direct,media_type):
    from test_tme_full_exam import pdf
    from io import BytesIO
    from PIL import Image
    client,_,_=direct
    if media_type=='application/pdf':raw=pdf(2)
    else:
        stream=BytesIO();Image.new('RGB',(20,20),'white').save(stream,format='JPEG');raw=stream.getvalue()
    case=receive(client,'TME2026P1','[a]\nTexto transcrito manualmente.',dict(media_type=media_type,content_base64=base64.b64encode(raw).decode()))
    response=client.get(f"/tme/cases/{case['case_id']}/original-document")
    assert response.status_code==200 and response.content==raw
    assert response.headers['content-type'].startswith(media_type)
    _,_,h=history(client,case)
    assert not h['acceptances'] and h['transcription']['source']=='manual'
