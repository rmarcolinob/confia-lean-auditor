"""Human confirmation uses stable-engine product output and immutable local stores."""
import json
from decimal import Decimal
from uuid import uuid4
import pytest
from test_tme_full_exam import demo
from test_tme_question_audit import questions, reading, analyze, request_for
from test_tme_review_workspace import workspace, revision
from test_tme_reanalysis import correct, full_text
from confia_lean_auditor.submission_audits.router import service


def selection(run,**extra):
    return dict(audit_run_id=run['audit_run_id'],transcription_version_id=run['transcription_version_id'],
        decision_type='ACCEPT_SUGGESTION',execution_key=uuid4().hex,**extra)


def confirm(client,cid,body,status=201):
    response=client.post(f'/tme/cases/{cid}/decision',json=body)
    assert response.status_code==status,response.text
    return response.json()


def ready(questions,text=None):
    client,root,detail,cid,q2=questions
    rev,_=reading(client,cid,text=text)
    run=analyze(client,cid,request_for(client,cid,rev))
    return client,root,detail,cid,q2,rev,run


def test_accept_snapshot_confirmed_history_events_pseudonym_and_totals(questions):
    client,root,detail,cid,q2,rev,run=ready(questions)
    raw=service()._path(run['audit_run_id']).read_bytes()
    request=selection(run);decision=confirm(client,cid,request)
    assert Decimal(decision['suggested_points'])==Decimal(decision['final_points'])==20
    assert Decimal(decision['adjustment_delta'])==0 and decision['decision_type']=='ACCEPT_SUGGESTION'
    assert decision['transcription_version_id']==run['transcription_version_id']
    assert decision['engine_mode']==run['engine_mode'] and decision['engine_version']==run['engine_version']
    assert decision['participant_id']==detail['submission']['participant_id']
    assert decision['decided_by_user_id']=='tme-demo-evaluator' and decision['audit_source_sha256']
    assert decision['rubric_decisions']==[] and not decision['review_required_snapshot']
    assert confirm(client,cid,request)['human_decision_id']==decision['human_decision_id']
    confirm(client,cid,selection(run),409)
    w=workspace(client,cid)
    assert w['state']=='CONFIRMED' and w['current_human_decision']['human_decision_id']==decision['human_decision_id']
    assert Decimal(w['confirmed_total']['final_score'])==20 and Decimal(w['confirmed_total']['max_score'])==20
    assert w['confirmed_total']['confirmed_questions']==1 and w['confirmed_total']['remaining_questions']==4
    assert workspace(client,q2)['state']=='PENDING'
    assert client.get(f'/tme/cases/{cid}/decision').json()['human_decision_id']==decision['human_decision_id']
    history=client.get(f'/tme/cases/{cid}/decisions').json()
    assert len(history['human_decisions'])==1
    assert {e['event_type'] for e in history['human_decision_events']}=={'suggestion_accepted','question_confirmed'}
    for e in history['human_decision_events']:
        for key in ('assessment_id','participant_id','submission_id','question_attempt_id','transcription_version_id','audit_run_id','human_decision_id','timestamp','engine_mode','engine_version','suggested_score','final_score','adjustment_delta'):assert key in e
    assert history['human_decisions'][0]['certification']['absolute_error']=='0.0'
    assert service()._path(run['audit_run_id']).read_bytes()==raw
    assert 'external_candidate_ref' not in json.dumps(decision)


@pytest.mark.parametrize('score,reason,expected',[(0,'crédito revisto',201),(20,None,201),(18,'ajuste pedagógico',201),(21,'fora do limite',422),(-1,'negativo',422),('NaN','inválido',422),('Infinity','inválido',422),('1.001','precisão',422),(18,'   ',422),(18,None,422),('',None,422)])
def test_adjustment_bounds_precision_reason_and_negative_delta(questions,score,reason,expected):
    client,_,_,cid,_,_,run=ready(questions)
    body=selection(run);body.update(decision_type='ADJUST_SCORE',final_points=score,override_reason=reason)
    d=confirm(client,cid,body,expected)
    if expected==201:
        assert Decimal(d['final_points'])==Decimal(str(score))
        assert Decimal(d['suggested_points'])==20
        assert Decimal(d['adjustment_delta'])==Decimal(str(score))-20
    else:assert workspace(client,cid)['human_decisions']==[]


def test_positive_delta_review_allowed_reopen_and_new_decision_preserved(questions):
    client,root,_,cid,_,rev,run=ready(questions,text='[a]\n731-137=594')
    assert run['review_required'] and run['suggested_score']<18
    body=selection(run);body.update(decision_type='ADJUST_SCORE',final_points=18,override_reason='Estratégia alternativa conferida no original.')
    first=confirm(client,cid,body)
    assert Decimal(first['adjustment_delta'])>0 and first['review_required_snapshot']
    folder=root/'tme_cases'/cid/'human_decisions';before=(folder/'000001.json').read_bytes()
    request={'human_decision_id':first['human_decision_id'],'execution_key':uuid4().hex}
    assert client.post(f'/tme/cases/{cid}/reopen',json=request).status_code==200
    assert client.post(f'/tme/cases/{cid}/reopen',json=request).status_code==200
    w=workspace(client,cid)
    assert w['state']=='REVIEW' and w['current_human_decision'] is None
    assert w['human_decisions'][0]['effective_status']=='REOPENED' and w['confirmed_total']['confirmed_questions']==0
    confirm(client,cid,selection(run),409)
    second=confirm(client,cid,selection(run,expected_last_decision_id=first['human_decision_id']))
    assert second['human_decision_id']!=first['human_decision_id'] and second['supersedes_decision_id']==first['human_decision_id']
    assert (folder/'000001.json').read_bytes()==before
    w=workspace(client,cid)
    assert w['state']=='CONFIRMED' and len(w['human_decisions'])==2
    assert {'score_adjusted','adjustment_reason_recorded','question_reopened','human_decision_superseded'}<={e['event_type'] for e in w['events']}


def test_transcription_edit_invalidates_then_new_audit_requires_new_confirmation(questions):
    client,root,_,cid,q2,rev,run=ready(questions)
    r2,_=reading(client,q2,n=2);a2=analyze(client,q2,request_for(client,q2,r2));h2=confirm(client,q2,selection(a2))
    h1=confirm(client,cid,selection(run));before=(root/'tme_cases'/cid/'human_decisions'/'000001.json').read_bytes()
    changed=correct(client,cid,rev,full_text()+'\n')
    w=workspace(client,cid)
    assert w['state']=='REVIEW' and w['reanalysis_required'] and w['current_human_decision'] is None
    assert w['human_decisions'][0]['effective_status']=='INVALIDATED_BY_TRANSCRIPTION'
    assert Decimal(w['confirmed_total']['final_score'])==20
    assert client.get(f'/tme/cases/{cid}/decision').json() is None
    confirm(client,cid,selection(run,expected_last_decision_id=h1['human_decision_id']),409)
    new=analyze(client,cid,request_for(client,cid,changed))
    w=workspace(client,cid)
    assert w['state']=='READY' and w['current_human_decision'] is None and w['current_audit']['audit_run_id']==new['audit_run_id']
    assert {'confirmation_invalidated_by_transcription_change','confirmation_invalidated_by_new_audit'}<={e['event_type'] for e in w['events']}
    confirm(client,cid,selection(new,expected_last_decision_id=h1['human_decision_id']))
    assert (root/'tme_cases'/cid/'human_decisions'/'000001.json').read_bytes()==before
    assert workspace(client,q2)['current_human_decision']['human_decision_id']==h2['human_decision_id']
    assert workspace(client,cid)['confirmed_total']['confirmed_questions']==2


def test_new_audit_same_reading_invalidates_and_rejects_old_audit(questions):
    client,_,_,cid,_,rev,run=ready(questions)
    decision=confirm(client,cid,selection(run));new=analyze(client,cid,request_for(client,cid,rev))
    w=workspace(client,cid)
    assert w['current_human_decision'] is None and w['state']=='READY'
    assert w['human_decisions'][0]['effective_status']=='INVALIDATED_BY_NEW_AUDIT'
    confirm(client,cid,selection(run,expected_last_decision_id=decision['human_decision_id']),409)
    wrong=selection(new,expected_last_decision_id=decision['human_decision_id']);wrong['transcription_version_id']=rev['transcription_id']+':2'
    confirm(client,cid,wrong,409)
    confirm(client,cid,selection(new,expected_last_decision_id=decision['human_decision_id']))


def test_failed_audit_forbids_both_accept_and_manual_adjustment(questions,monkeypatch):
    client,_,_,cid,_=questions
    rev,_=reading(client,cid)
    def fail(*args):raise RuntimeError('controlled')
    monkeypatch.setattr('confia_lean_auditor.tme.accepted_audit.audit_accepted_tme_transcription',fail)
    run=analyze(client,cid,request_for(client,cid,rev))
    assert run['suggested_score'] is None
    confirm(client,cid,selection(run),409)
    body=selection(run);body.update(decision_type='ADJUST_SCORE',final_points=10,override_reason='manual')
    confirm(client,cid,body,409)
    assert workspace(client,cid)['current_human_decision'] is None


def test_history_integrity_and_scope(questions,monkeypatch):
    client,root,_,cid,q2,rev,run=ready(questions)
    request=selection(run);confirm(client,q2,request,409)
    decision=confirm(client,cid,request)
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH','0')
    assert client.get(f'/tme/cases/{cid}/decisions').status_code==401
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH','1')
    path=root/'tme_cases'/cid/'human_decisions'/'000001.json';data=json.loads(path.read_text());data['decision']['final_points']='1';path.write_text(json.dumps(data))
    assert client.get(f'/tme/question-attempts/{cid}/workspace').status_code==409


def test_concurrent_confirmation_and_new_audit_cannot_bind_old_run(questions,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from confia_lean_auditor.tme import accepted_audit
    client,_,_,cid,_,rev,run=ready(questions)
    original=accepted_audit.audit_accepted_tme_transcription
    started,release=Event(),Event()
    def slow(*args):
        started.set();assert release.wait(20)
        return original(*args)
    monkeypatch.setattr(accepted_audit,'audit_accepted_tme_transcription',slow)
    with ThreadPoolExecutor(max_workers=2) as pool:
        audit=pool.submit(analyze,client,cid,request_for(client,cid,rev))
        try:
            assert started.wait(10)
            decision=pool.submit(confirm,client,cid,selection(run),409)
        finally:release.set()
        new=audit.result(timeout=20);decision.result(timeout=20)
    assert workspace(client,cid)['current_human_decision'] is None
    assert workspace(client,cid)['current_audit']['audit_run_id']==new['audit_run_id']


def test_double_submit_serialized_and_foreign_reviewer_rejected(questions):
    from concurrent.futures import ThreadPoolExecutor
    from confia_lean_auditor.main import app
    from confia_lean_auditor.tme.auth import require_tme_evaluator, TMEEvaluator
    client,_,_,cid,_,_,run=ready(questions);body=selection(run)
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending=[pool.submit(confirm,client,cid,body) for _ in range(2)]
        a,b=[p.result(timeout=20) for p in pending]
    assert a['human_decision_id']==b['human_decision_id']
    assert len(workspace(client,cid)['human_decisions'])==1
    app.dependency_overrides[require_tme_evaluator]=lambda:TMEEvaluator('foreign-reviewer')
    try:
        assert client.get(f'/tme/cases/{cid}/decision').status_code==403
        assert client.get(f'/tme/cases/{cid}/decisions').status_code==403
        confirm(client,cid,body,403)
    finally:app.dependency_overrides.pop(require_tme_evaluator)


@pytest.mark.parametrize('operation', ['confirm', 'reopen'])
@pytest.mark.parametrize('concurrent_write', ['reading', 'audit'])
def test_generic_publication_between_snapshot_and_append_is_rejected(questions, monkeypatch, operation, concurrent_write):
    """Generic routes use submission locks, bypassing product question/exam locks."""
    from confia_lean_auditor.tme import human_decisions
    from confia_lean_auditor.submissions.schemas import CreateTranscriptionRevisionRequest
    from confia_lean_auditor.submission_audits.schemas import AuditRequest
    client, root, _, cid, _, rev, run = ready(questions)
    existing = confirm(client, cid, selection(run)) if operation == 'reopen' else None
    request = request_for(client, cid, rev)
    original = human_decisions.append_current
    def raced(case, chain, kind, decision, body, user):
        store = service().submissions
        if concurrent_write == 'reading':
            store.create_transcription_revision(rev['transcription_id'], CreateTranscriptionRevisionRequest(
                based_on_revision_number=rev['revision_number'], reviewer_reference='concurrent-teacher',
                segments=rev['segments'], change_reason='concurrent reading'))
        else:
            service().execute(rev['submission_id'], AuditRequest(**request))
        return original(case, chain, kind, decision, body, user)
    monkeypatch.setattr(human_decisions, 'append_current', raced)
    if existing:
        response = client.post(f'/tme/cases/{cid}/reopen', json={
            'human_decision_id': existing['human_decision_id'], 'execution_key': uuid4().hex})
        assert response.status_code == 409, response.text
    else:
        confirm(client, cid, selection(run), 409)
    chain = list((root/'tme_cases'/cid/'human_decisions').glob('*.json'))
    assert len(chain) == (1 if existing else 0)
    assert workspace(client, cid)['current_human_decision'] is None
