"""Controlled providers only: human decisions never rewrite automatic evidence."""
from copy import deepcopy
from decimal import Decimal
from uuid import uuid4
import pytest
from test_dynamic_dy3 import setup, attempt
from test_dec10_integration import teacher_problem, fake_provider, SOLUTION
from test_dynamic_dy6 import activity, add_question, activities, Revision, USER, receive, audit_question
from confia_lean_auditor.semantic_policy.service import DYNAMIC_VERSION
from confia_lean_auditor.submission_audits.router import service
from confia_lean_auditor.tme.store import case_store
from confia_lean_auditor.dynamic.reconciliation_service import ReconciliationService


def prepare(setup, monkeypatch, grader='review', reviewer='met', standalone=False):
    root, client=setup
    monkeypatch.setenv('CONFIA_ASSESSMENTS_DIR',str(root/'assessments'))
    monkeypatch.setenv('CONFIA_DYNAMIC_POLICY',DYNAMIC_VERSION)
    fake_provider(monkeypatch,grader,reviewer)
    problem=teacher_problem()
    if standalone:
        case,base,request=attempt(client,problem,SOLUTION)
        run=client.post(base+'/audits',json=request).json()
        client.post(f"/dynamic/attempts/{case['case_id']}/policy",json={'policy_profile':'SCHOOL_EXAM'})
        exam=None
    else:
        doc=add_question(activity(),problem)
        doc=activities.activate(doc['assessment']['assessment_id'],Revision(expected_revision=doc['dynamic_revision']),USER)
        exam=receive(client,doc,[SOLUTION])
        case=exam['question_attempts'][0];run=audit_question(client,case)
    url=f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}"
    r=client.post(url+'/independent-reviews',json={'execution_key':'review'})
    assert r.status_code==201,r.text
    r=client.post(url+'/reconciliations',json={'independent_review_id':r.json()['review']['review_id']})
    assert r.status_code==201,r.text
    raw=service().get(run['audit_run_id'])
    rec=ReconciliationService(service()).current(case_store().read(case['case_id']),run['audit_run_id'])
    return client,case,raw,rec,exam


def payload(run,rec,points=('6','4'),standalone=False):
    criteria=[dict(criterion_id=c['criterion_id'],final_points=p,justification='Conferi a resolução e o critério aprovado.',dependency_justification='Conferi a relação com o critério anterior.') for c,p in zip(rec['criteria'],points)]
    body=dict(audit_run_id=run.audit_run_id,reconciliation_id=rec['reconciliation_id'],
        final_points=str(sum(Decimal(p) for p in points)),override_reason='Adjudicação docente fundamentada na resolução integral.',
        adjudication=dict(rubric_sha256=rec['context']['rubric_sha256'],criteria=criteria))
    if standalone:body['max_points']='10'
    else:body.update(transcription_version_id=rec['transcription_version_id'],decision_type='ADJUST_SCORE',execution_key=uuid4().hex)
    return body


def post(client,case,body):return client.post(f"/tme/cases/{case['case_id']}/decision",json=body)
def workspace(client,case):
    r=client.get(f"/tme/question-attempts/{case['case_id']}/workspace")
    assert r.status_code==200,r.text
    return r.json()


@pytest.mark.parametrize('grader,reviewer,points',[('review','met',('6','4')),('met','not_met',('3','2')),('error','met',('0','0'))])
def test_null_explicit_human_score_and_finalization(setup,monkeypatch,grader,reviewer,points):
    client,case,run,rec,exam=prepare(setup,monkeypatch,grader,reviewer)
    assert rec['reconciled_suggested_score'] is None
    roots=[service().root,ReconciliationService(service()).root]
    before={p:p.read_bytes() for root in roots for p in root.rglob('*.json')}
    assert workspace(client,case)['current_human_decision'] is None
    body=payload(run,rec,points)
    r=post(client,case,body);assert r.status_code==201,r.text
    d=r.json();assert Decimal(d['final_points'])==sum(Decimal(p) for p in points)
    assert d['suggested_points'] is None and d['adjustment_delta'] is None
    assert d['review_required_snapshot'] and d['rubric_decisions']
    assert post(client,case,body).json()==d
    assert all(p.read_bytes()==b for p,b in before.items())
    w=workspace(client,case)
    assert w['current_human_decision']['adjudication']==d['adjudication']
    ev=next(e for e in w['human_decision_events'] if e['event_type']=='dynamic_human_adjudicated')
    assert ev['origin']=='HUMAN_ADJUDICATION' and ev['formal_certification'] is False
    assert ev['actor_id']==d['decided_by_user_id']
    eid=exam['submission']['submission_id']
    s=client.get(f'/tme/exam-submissions/{eid}/correction');assert s.status_code==200,s.text
    assert s.json()['ready_to_finalize'],s.text
    r=client.post(f'/tme/exam-submissions/{eid}/correction/finalize',json=dict(expected_snapshot_sha256=s.json()['snapshot_sha256'],execution_key='final'))
    assert r.status_code==201,r.text
    assert r.json()['suggested_total_snapshot'] is None and r.json()['total_adjustment'] is None
    assert Decimal(r.json()['final_total'])==Decimal(body['final_points'])
    assert all(p.read_bytes()==b for p,b in before.items())
    if grader=='error':assert rec['technical_uncertainty']
    monkeypatch.setenv('CONFIA_TME_CERTIFICATION_ENABLED','1')
    aid=exam['submission']['assessment_id']
    export=client.get(f'/tme/assessments/{aid}/certification?engine_mode=DYNAMIC')
    assert export.status_code==200,export.text
    data=export.json()
    stages=data['records'][0]['dynamic_evaluation']['stages']
    assert stages['G2']['score'] is None and stages['G3']['origin']=='HUMAN_ADJUDICATION'
    assert Decimal(stages['G3']['score'])==Decimal(body['final_points'])
    assert stages['G3']['criteria'] and not stages['G3']['formal_certification']
    assert 'Adjudicação docente fundamentada na resolução integral.' not in export.text



@pytest.mark.parametrize('change,status',[
    ('missing',409),('reason',422),('criterion_reason',422),('over',422),('negative',422),('incomplete',422),
    ('duplicate',422),('sum',422),('rubric',422),('version',409),('audit',409),('reconciliation',409),('accept',422)])
def test_reject_invalid_or_stale_adjudication(setup,monkeypatch,change,status):
    client,case,run,rec,_=prepare(setup,monkeypatch)
    b=payload(run,rec)
    if change=='missing':b.pop('adjudication')
    elif change=='reason':b['override_reason']=' '
    elif change=='criterion_reason':b['adjudication']['criteria'][0]['justification']=' '
    elif change=='over':b['adjudication']['criteria'][0]['final_points']='7';b['final_points']='11'
    elif change=='negative':b['adjudication']['criteria'][0]['final_points']='-1'
    elif change=='incomplete':b['adjudication']['criteria'].pop()
    elif change=='duplicate':b['adjudication']['criteria'][1]['criterion_id']=b['adjudication']['criteria'][0]['criterion_id']
    elif change=='sum':b['final_points']='9'
    elif change=='rubric':b['adjudication']['rubric_sha256']='0'*64
    elif change=='version':b['transcription_version_id']=b['transcription_version_id'].split(':')[0]+':2'
    elif change=='audit':b['audit_run_id']='aud_'+'0'*64
    elif change=='reconciliation':b['reconciliation_id']='drec_'+'0'*64
    elif change=='accept':b['decision_type']='ACCEPT_SUGGESTION'
    r=post(client,case,b);assert r.status_code==status,r.text
    assert workspace(client,case)['current_human_decision'] is None


def test_pending_without_adjudication_and_execution_key_conflict(setup,monkeypatch):
    client,case,run,rec,exam=prepare(setup,monkeypatch)
    eid=exam['submission']['submission_id']
    assert not client.get(f'/tme/exam-submissions/{eid}/correction').json()['ready_to_finalize']
    b=payload(run,rec);r=post(client,case,b);assert r.status_code==201,r.text
    b['override_reason']='Outra decisão com a mesma chave.'
    assert post(client,case,b).status_code==409
    assert len(workspace(client,case)['human_decisions'])==1


@pytest.mark.parametrize('points',[('6','4'),('3','2'),('0','0')])
def test_standalone_uses_same_explicit_contract(setup,monkeypatch,points):
    client,case,run,rec,_=prepare(setup,monkeypatch,standalone=True)
    b=payload(run,rec,points,True)
    r=post(client,case,b);assert r.status_code==201,r.text
    assert r.json()['suggested_points'] is None
    assert post(client,case,b).json()==r.json()
    assert client.get(f"/tme/cases/{case['case_id']}/decision").json()['adjudication']==r.json()['adjudication']
    history=client.get(f"/dynamic/attempts/{case['case_id']}/human-decisions").json()
    assert history[0]['events'][0]['event_type']=='dynamic_human_adjudicated'


def test_authorization_case_isolation_and_no_implicit_human_override(setup,monkeypatch):
    from types import SimpleNamespace
    from confia_lean_auditor.tme import auth
    from confia_lean_auditor.auth.models import Role
    client,case,run,rec,_=prepare(setup,monkeypatch)
    b=payload(run,rec)
    # Actual route dependency rejects nonteachers and a teacher from another institution.
    for role,code in [(Role.STUDENT,403),(Role.SCHOOL_MANAGER,403),(Role.TEACHER,403)]:
        monkeypatch.setattr(auth,'optional_user',lambda request,role=role:SimpleNamespace(role=role,user_id='another-teacher',tenant_id='another-school'))
        assert post(client,case,b).status_code==code
    monkeypatch.setattr(auth,'optional_user',lambda request:None)
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH','0')
    assert post(client,case,b).status_code==401
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH','1')
    # Distinct case owned by the same demo teacher still cannot use this audit.
    other=client.post('/tme/cases',json=dict(problem_id='ITA2025F2Q1',external_candidate_ref='other',source_mode='IMAGE_SCAN')).json()
    assert post(client,other,b).status_code==422
    assert workspace(client,case)['current_human_decision'] is None


def test_new_independent_review_invalidates_human_decision_without_rewriting(setup,monkeypatch):
    client,case,run,rec,_=prepare(setup,monkeypatch)
    b=payload(run,rec);r=post(client,case,b);assert r.status_code==201,r.text
    folder=case_store().folder(case['case_id'])/'human_decisions'
    old=(folder/'000001.json').read_bytes()
    url=f"/dynamic/attempts/{case['case_id']}/audits/{run.audit_run_id}"
    r=client.post(url+'/independent-reviews',json={'execution_key':'new-review'});assert r.status_code==201,r.text
    w=workspace(client,case)
    assert w['current_human_decision'] is None
    assert w['human_decisions'][0]['effective_status']=='INVALIDATED_BY_RECONCILIATION'
    assert (folder/'000001.json').read_bytes()==old
    b['execution_key']='stale-confirmation'
    assert post(client,case,b).status_code==409


def test_reopen_adjudication_is_append_only(setup,monkeypatch):
    client,case,run,rec,_=prepare(setup,monkeypatch)
    b=payload(run,rec);r=post(client,case,b);assert r.status_code==201,r.text
    first=r.json();url=f"/tme/cases/{case['case_id']}"
    r=client.post(url+'/reopen',json={'human_decision_id':first['human_decision_id'],'execution_key':'reopen'});assert r.status_code==200,r.text
    b=payload(run,rec,('3','2'));b['expected_last_decision_id']=first['human_decision_id']
    r=post(client,case,b);assert r.status_code==201,r.text
    assert r.json()['supersedes_decision_id']==first['human_decision_id']
    assert len(workspace(client,case)['human_decisions'])==2


def test_dependency_application_requires_explanation(setup,monkeypatch):
    from test_dec10_integration import CRITERIA, QUESTION, ACTOR
    from confia_lean_auditor.dynamic.store import dynamic_store
    from confia_lean_auditor.dynamic.models import CreateProblem,SaveRubric,ApproveRubric
    def dependent_problem():
        s=dynamic_store();d=s.create(CreateProblem(statement=QUESTION,max_score='10',correction_mode='DYNAMIC'),ACTOR)
        criteria=deepcopy(CRITERIA);criteria[1]['dependencies']=[criteria[0]['criterion_id']]
        d=s.save_rubric(d['problem']['problem_id'],SaveRubric(expected_revision=d['revision'],statement_version=1,max_score='10',criteria=criteria),ACTOR)
        return s.approve(d['problem']['problem_id'],d['rubrics'][-1]['rubric_id'],ApproveRubric(expected_revision=d['revision']),ACTOR)
    monkeypatch.setattr(__import__(__name__),'teacher_problem',dependent_problem)
    client,case,run,rec,_=prepare(setup,monkeypatch)
    b=payload(run,rec)
    b['adjudication']['criteria'][1]['dependency_justification']=None
    assert post(client,case,b).status_code==422
    b['adjudication']['criteria'][1]['dependency_justification']='O cálculo de área foi conferido; a unidade quadrada corresponde à área.'
    assert post(client,case,b).status_code==201


def test_legacy_request_and_records_keep_wire_shape():
    from confia_lean_auditor.tme.human_decisions import HumanDecisionRequest
    from confia_lean_auditor.tme.models import EvaluatorDecision
    request=HumanDecisionRequest(audit_run_id='aud_'+'1'*64,transcription_version_id='tr_'+'2'*32+':1',decision_type='ADJUST_SCORE',final_points='0',override_reason='zero explícito',execution_key='legacy')
    assert 'adjudication' not in request.model_dump(mode='json')
    old=dict(case_id='case_'+'1'*32,decided_by_user_id='teacher',decided_at='2026-11-25T00:00:00Z',max_points='10',final_points='0',suggested_points='0')
    wire=EvaluatorDecision(**old).model_dump(mode='json')
    assert 'adjudication' not in wire
    assert EvaluatorDecision.model_validate(wire).model_dump(mode='json')==wire
