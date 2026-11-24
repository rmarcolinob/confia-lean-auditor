"""Product contracts, simulated providers only. No mathematical efficacy claims."""
import json
from pathlib import Path
from types import SimpleNamespace
from decimal import Decimal
import pytest
from test_dynamic_dy3 import setup, attempt, ACTOR
from confia_lean_auditor.semantic_policy import service as semantic_service
from confia_lean_auditor.semantic_policy.service import VERSION, DYNAMIC_VERSION
from confia_lean_auditor.dynamic.store import dynamic_store
from confia_lean_auditor.dynamic.models import CreateProblem, SaveRubric, ApproveRubric

QUESTION='Um retângulo mede 3 cm por 5 cm. Determine a área e justifique a unidade.'
SOLUTION='A área é 3 × 5 = 15 cm², pois multiplicamos comprimento por largura.'
CRITERIA=[dict(criterion_id='area',title='Área',description='Calcular a área do retângulo usando suas dimensões.',max_points='6',order=1),
          dict(criterion_id='unit',title='Unidade',description='Apresentar e justificar a unidade de área.',max_points='4',order=2)]


def fake_provider(monkeypatch, grader='met', reviewer='met'):
    calls=[]
    def call(self,request):
        calls.append(request)
        decision=reviewer if request.get('stage')=='independent_reviewer' else grader
        if decision=='error':raise TimeoutError('simulated offline timeout')
        return dict(decision=decision,justification='Avaliação simulada do cumprimento do critério.',quotes=[request['solution']])
    monkeypatch.setattr(semantic_service.SemanticProvider,'__call__',call)
    return calls


def teacher_problem():
    store=dynamic_store()
    d=store.create(CreateProblem(statement=QUESTION,max_score='10',correction_mode='DYNAMIC'),ACTOR)
    pid=d['problem']['problem_id']
    d=store.save_rubric(pid,SaveRubric(expected_revision=d['revision'],statement_version=1,max_score='10',criteria=CRITERIA),ACTOR)
    return store.approve(pid,d['rubrics'][-1]['rubric_id'],ApproveRubric(expected_revision=d['revision']),ACTOR)


def test_dynamic_novel_teacher_rubric_end_to_end(setup,monkeypatch):
    root,client=setup
    monkeypatch.setenv('CONFIA_DYNAMIC_POLICY',DYNAMIC_VERSION)
    calls=fake_provider(monkeypatch)
    d=teacher_problem()
    assert d['current_preparation']['provenance']['provider']=='local_teacher_context'
    assert not d['current_preparation']['proposal']['candidate_reference_solutions']
    case,base,request=attempt(client,d,SOLUTION)
    assert client.get(base+'/original-text').json()['text']==SOLUTION
    response=client.post(base+'/audits',json=request)
    assert response.status_code==200,response.text
    run=response.json();assert run['status']=='COMPLETED',run
    assert run['result']['score']==10
    assert all(v['semantic_trace']['formal_certification'] is False for v in run['result']['decisions'])
    pid=case['case_id'];rid=run['audit_run_id']
    response=client.post(f'/dynamic/attempts/{pid}/policy',json={'policy_profile':'FORMATIVE_LIST'})
    assert response.status_code==201,response.text
    response=client.post(f'/dynamic/attempts/{pid}/audits/{rid}/independent-reviews',json={'execution_key':'offline-review'})
    assert response.status_code==201,response.text
    review=response.json()['review'];assert review['status']=='COMPLETED',review
    assert 'grader' not in review['phase_a_input'] and 'decisions' not in review['phase_a_input']
    response=client.post(f'/dynamic/attempts/{pid}/audits/{rid}/reconciliations',json={'independent_review_id':review['review_id']})
    assert response.status_code==201,response.text
    rec=response.json()['reconciliation'];assert rec['reconciled_suggested_score']=='10'
    assert {c['status'] for c in rec['criteria']}=={'AGREEMENT_UNVERIFIED'}
    assert rec['review_required'] and not rec['technical_uncertainty']
    assert len(calls)==4
    assert client.post(base+'/audits',json=request).json()['audit_run_id']==rid
    assert len(calls)==4 # immutable replay, no repeat charge
    assert client.get(f'/dynamic/attempts/{pid}/audits/{rid}/reconciliations').status_code==200
    from confia_lean_auditor.submission_audits.router import service
    saved=service().get(rid)
    assert saved.result.score==10
    monkeypatch.setenv('CONFIA_DYNAMIC_POLICY','legacy')
    assert service().get(rid).result.score==10 # rollback preserves persisted receipts


@pytest.mark.parametrize('grader,reviewer,score,technical',[
    ('met','not_met',None,False),('review','met',None,False),('error','met',None,True),('not_met','not_met','0',False)])
def test_dynamic_pending_failure_and_zero_are_distinct(setup,monkeypatch,grader,reviewer,score,technical):
    _,client=setup;monkeypatch.setenv('CONFIA_DYNAMIC_POLICY',DYNAMIC_VERSION)
    fake_provider(monkeypatch,grader,reviewer)
    case,base,request=attempt(client,teacher_problem(),SOLUTION)
    run=client.post(base+'/audits',json=request).json()
    assert run['status']=='COMPLETED',run
    if grader in {'review','error'}:assert run['result']['score'] is None
    pid,rid=case['case_id'],run['audit_run_id']
    client.post(f'/dynamic/attempts/{pid}/policy',json={'policy_profile':'SCHOOL_EXAM'})
    review=client.post(f'/dynamic/attempts/{pid}/audits/{rid}/independent-reviews',json={'execution_key':'offline'}).json()['review']
    result=client.post(f'/dynamic/attempts/{pid}/audits/{rid}/reconciliations',json={'independent_review_id':review['review_id']})
    assert result.status_code==201,result.text
    rec=result.json()['reconciliation']
    assert rec['reconciled_suggested_score']==score
    assert rec['technical_uncertainty']==technical


@pytest.mark.parametrize('raw,expected',[
    ({'decision':'met','justification':'ok','quotes':['not in source']},'review'),
    ({'decision':'met','justification':'ok','quotes':[]},'review'),
    ({'decision':'met','justification':'ok','quotes':['written'],'points':10},'review'),
    ({'decision':'not_met','justification':'Missing explanation','quotes':[]},'not_met')])
def test_no_invented_points_or_evidence(raw,expected):
    trace=semantic_service.assess({'solution':'written'},lambda _:raw)
    assert trace['decision']==expected
    assert trace['formal_certification'] is False


def test_unconfigured_provider_never_opens_client(monkeypatch):
    import openai
    monkeypatch.delenv('CONFIA_SEMANTIC_LLM_ENABLED',raising=False)
    monkeypatch.setattr(openai,'OpenAI',lambda **_:pytest.fail('network client constructed'))
    trace=semantic_service.assess({'solution':SOLUTION})
    assert trace['decision']=='review' and trace['error_type']=='RuntimeError'


@pytest.mark.parametrize('reviewer,expected', [('met',10),('review',None),('error',None),('not_met',None)])
def test_semantic_assessment_shared_workspace_and_confirmation(setup,monkeypatch,reviewer,expected):
    from test_dynamic_dy6 import activity,add_question,activities,Revision,USER,receive,audit_question
    from test_tme_finalization import summary,finalize
    root,client=setup
    monkeypatch.setenv('CONFIA_ASSESSMENTS_DIR',str(root/'assessments'))
    monkeypatch.setenv('CONFIA_DYNAMIC_POLICY',DYNAMIC_VERSION)
    fake_provider(monkeypatch,reviewer=reviewer)
    doc=add_question(activity(),teacher_problem())
    assert doc['readiness']['ready'],doc['readiness']
    doc=activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),USER)
    exam=receive(client,doc,[SOLUTION]);case=exam['question_attempts'][0]
    run=audit_question(client,case)
    assert run['suggested_score']==10
    url=f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}"
    response=client.post(url+'/independent-reviews',json={'execution_key':'semantic-review'})
    assert response.status_code==201,response.text
    response=client.post(url+'/reconciliations',json={'independent_review_id':response.json()['review']['review_id']})
    assert response.status_code==201,response.text
    rec=response.json()['reconciliation']
    workspace=client.get(f"/tme/question-attempts/{case['case_id']}/workspace")
    assert workspace.status_code==200,workspace.text
    projected=workspace.json()['audits'][0]
    assert projected['suggested_score']==expected
    assert projected['suggestion_ready']==(expected is not None)
    assert projected['technical_uncertainty']==(reviewer=='error')
    if expected is None:
        assert all(item['suggested_points'] is None for item in projected['rubric_items'])
    body=dict(audit_run_id=run['audit_run_id'],transcription_version_id=run['transcription_version_id'],
        reconciliation_id=rec['reconciliation_id'],decision_type='ACCEPT_SUGGESTION',execution_key='confirm-semantic')
    response=client.post(f"/tme/cases/{case['case_id']}/decision",json=body)
    assert response.status_code==(201 if expected is not None else 409),response.text
    eid=exam['submission']['submission_id']
    assert summary(client,eid)['ready_to_finalize']==(expected is not None)
    if expected is not None:assert finalize(client,eid)['final_total']=='10.0'
