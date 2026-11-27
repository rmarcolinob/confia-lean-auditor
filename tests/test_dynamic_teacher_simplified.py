"""Real authenticated services; synthetic pages and explicitly simulated opinions."""
import base64
import pytest
from test_core_auth import auth_case
from test_tme_full_exam import png
from test_dynamic_credit_dependencies import simulated, opinion
from test_dynamic_handwriting import manual, confirm, workspace


def test_capabilities_are_role_scoped_configuration_only(auth_case, monkeypatch):
    _, _, client, _ = auth_case
    for key in ('OPENAI_API_KEY','CONFIA_MATHPIX_APP_ID','CONFIA_MATHPIX_APP_KEY'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('CONFIA_DYNAMIC_LLM_ENABLED','0')
    monkeypatch.setenv('CONFIA_SEMANTIC_LLM_ENABLED','0')
    assert client().get('/dynamic/capabilities').status_code == 401
    assert client('student.a').get('/dynamic/capabilities').status_code == 403
    r=client('teacher.a').get('/dynamic/capabilities')
    assert r.status_code == 200 and r.headers['cache-control']=='no-store'
    assert r.json()==dict(rubric_suggestion_configured=False,semantic_evaluation_configured=False,
                         handwriting_recognition_configured=False,configuration_only=True)
    assert not any(x in r.text.lower() for x in ('api_key','password','token'))


def test_teacher_two_questions_manual_rubrics_capture_review_and_divergence(auth_case,monkeypatch):
    _, _, clients, root=auth_case
    for key in ('ASSESSMENTS','ASSESSMENT_PARTICIPANTS','DYNAMIC','TME_CASES','TME_EXAMS'):
        monkeypatch.setenv('CONFIA_'+key+'_DIR',str(root/key.lower()))
    monkeypatch.setenv('CONFIA_DYNAMIC_POLICY','dynamic-semantic.v1')
    monkeypatch.setenv('CONFIA_DYNAMIC_LLM_ENABLED','0')
    calls=simulated(monkeypatch,{'fraction':'met','equation':opinion('partial','initial')},
                    {'fraction':'met','equation':'met'})
    client=clients('teacher.a');other=clients('teacher.b')
    r=client.post('/dynamic/assessments',json=dict(title='Prova sintética EF',policy_profile='SCHOOL_EXAM',feedback_policy='WITHHOLD'));assert r.status_code==201,r.text
    assessment=r.json();aid=assessment['assessment']['assessment_id']
    assert other.get('/dynamic/assessments/'+aid).status_code in (403,404)
    assert client.post(f'/dynamic/assessments/{aid}/activate',json={'expected_revision':assessment['dynamic_revision']}).status_code==409
    for cid,statement,description in [('fraction','Explique três quartos de 24.','Calcular 18 explicando partes iguais.'),('equation','Resolva 2x+6=18 e justifique.','Isolar x por operações equivalentes e calcular 6.')]:
        d=client.post('/dynamic/problems',json=dict(statement=statement,max_score='2',correction_mode='DYNAMIC')).json();pid=d['problem']['problem_id']
        assessment=client.post(f'/dynamic/assessments/{aid}/questions',json=dict(problem_id=pid,expected_revision=assessment['dynamic_revision'])).json()
        criterion=dict(criterion_id=cid,title=cid,description=description,max_points='2',order=1)
        if cid=='equation':criterion['credit_levels']=[dict(level_id='initial',points='1',description='Obter 2x=12 justificando a subtração, mas errar o cálculo final.')]
        r=client.post(f'/dynamic/problems/{pid}/rubrics',json=dict(expected_revision=d['revision'],statement_version=1,max_score='2',criteria=[criterion]));assert r.status_code==201,r.text
        d=r.json();assert d['rubrics'][-1]['status']!='APPROVED'
        r=client.post(f"/dynamic/problems/{pid}/rubrics/{d['rubrics'][-1]['rubric_id']}/approve",json=dict(expected_revision=d['revision'],acknowledge_warnings=True));assert r.status_code==200,r.text
    assessment=client.get(f'/dynamic/assessments/{aid}').json();assert assessment['readiness']['ready']
    r=client.post(f'/dynamic/assessments/{aid}/activate',json=dict(expected_revision=assessment['dynamic_revision']));assert r.status_code==200,r.text
    assert r.json()['assessment']['scope']=='TME' # no implicit institutional publication
    r=client.post('/tme/exam-submissions',json=dict(assessment_identifier=aid,external_participant_code='SYNTHETIC-01',idempotency_key='teacher-safe-upload',original_documents=[dict(media_type='image/png',content_base64=base64.b64encode(png('blue')).decode())]));assert r.status_code==201,r.text
    exam=r.json();eid=exam['submission']['submission_id'];cases=exam['question_attempts'];page=exam['submission']['pages'][0]
    assert other.get(f'/tme/exam-submissions/{eid}').status_code in (403,404)
    r=client.put(f'/tme/exam-submissions/{eid}/page-mapping',json=dict(expected_version=1,bindings=[dict(question_attempt_id=c['case_id'],exam_page_id=page['exam_page_id'],order=1) for c in cases]));assert r.status_code==200,r.text
    for case,text in zip(cases,['Divido 24 em quatro partes: 24/4=6; três partes são 3*6=18.','Subtraio 6 dos dois lados: 2x=12. Divido por 2, mas obtenho x=5.']):
        manual(client,case,[text]);assert workspace(client,case)['reading_review']['status']=='NEEDS_CONFIRMATION'
        assert confirm(client,case).status_code==200
        w=workspace(client,case);history=w['history'];tid=history['transcription']['transcription_id'];revision=history['revisions'][-1]['revision_number']
        accept=client.post(f"/tme/cases/{case['case_id']}/transcriptions/{tid}/accept",json=dict(revision_number=revision,reviewer_identity_verified=False)).json()
        r=client.post(f"/tme/cases/{case['case_id']}/audits",json=dict(transcription_id=tid,revision_number=revision,acceptance_id=accept['acceptance']['acceptance_id'],execution_key='teacher-audit'));assert r.status_code==200,r.text
        run=r.json();url=f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}"
        r=client.post(url+'/independent-reviews',json=dict(execution_key='teacher-simplified'));assert r.status_code==201,r.text
        review=r.json();r=client.post(url+'/reconciliations',json=dict(independent_review_id=review['review']['review_id']));assert r.status_code==201,r.text
        if case==cases[-1]:assert r.json()['reconciliation']['reconciled_suggested_score'] is None
        assert client.post(url+'/independent-reviews',json=dict(execution_key='teacher-simplified')).json()['review']['review_id']==review['review']['review_id']
    summary=client.get(f'/tme/exam-submissions/{eid}/correction').json()
    assert not summary['ready_to_finalize'] and not summary['current_final_correction']
    assert calls and all(c['solution'] for c in calls)
