"""D4 uses the real stable engine and stores; only controlled failures are injected."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4
import json
import pytest
from test_tme_full_exam import demo
from test_tme_question_audit import questions, reading, analyze, request_for
from test_tme_review_workspace import workspace, revision
from test_tme_accepted_integration import solution_for, FULL
from confia_lean_auditor.submission_audits.router import service
from confia_lean_auditor.tme import accepted_audit


def full_text():
    return '\n'.join(f'[{key}]\n{value}' for key,value in solution_for(1,FULL[1]).items())


def correct(client,cid,rev,text):
    response=revision(client,cid,rev['transcription_id'],rev['revision_number'],text)
    assert response.status_code==201,response.text
    return response.json()


def test_real_score_change_history_events_and_q2_isolation(questions):
    client,root,detail,cid,q2=questions
    first_reading,_=reading(client,cid,text='[a]\n731-137=594')
    first=analyze(client,cid,request_for(client,cid,first_reading))
    other_reading,_=reading(client,q2,n=2)
    other=analyze(client,q2,request_for(client,q2,other_reading))
    before={r.audit_run_id:service()._path(r.audit_run_id).read_bytes() for r in service().list(first_reading['submission_id'])+service().list(other_reading['submission_id'])}
    before_version=workspace(client,cid)['versions'][0]
    changed=correct(client,cid,first_reading,full_text())
    stale=workspace(client,cid)
    assert stale['current_audit'] is None and stale['previous_audit']['audit_run_id']==first['audit_run_id']
    assert stale['partial_suggestion']['suggested_score']==20 and stale['partial_suggestion']['awaiting_reanalysis']==1
    assert not stale['partial_suggestion']['complete']
    assert workspace(client,q2)['current_audit']['audit_run_id']==other['audit_run_id']
    assert workspace(client,cid)['reanalysis_required'] # navigation does not analyze
    assert len(service().list(first_reading['submission_id']))==1
    new=analyze(client,cid,request_for(client,cid,changed))
    assert new['audit_run_id']!=first['audit_run_id'] and new['transcription_version_id']==changed['transcription_id']+':2'
    assert new['suggested_score']==20>first['suggested_score']
    assert new['comparison']['previous_suggested_score']==first['suggested_score']
    assert new['comparison']['current_suggested_score']==20 and new['comparison']['score_changed']
    w=workspace(client,cid)
    assert w['current_audit']['audit_run_id']==new['audit_run_id'] and not w['reanalysis_required']
    assert w['audit_comparison']==new['comparison'] and w['state']=='READY'
    assert w['partial_suggestion']['suggested_score']==40 and w['partial_suggestion']['analyzed_questions']==2
    assert w['partial_suggestion']['awaiting_reanalysis']==0 and not w['partial_suggestion']['complete']
    assert w['versions'][0]['text']==before_version['text'] and not w['versions'][0]['current']
    assert w['versions'][1]['text']==full_text() and w['versions'][1]['current']
    kinds={e['event_type'] for e in w['events']}
    assert {'transcription_human_corrected','audit_marked_stale','question_reanalysis_requested','audit_started','audit_completed','suggested_score_changed'}<=kinds
    score_event=next(e for e in new['events'] if e['event_type']=='suggested_score_changed')
    assert (score_event['old_score'],score_event['new_score'])==(first['suggested_score'],20)
    for event in w['events']:
        assert event['participant_id']==detail['submission']['participant_id']
        assert event['assessment_id']==detail['submission']['assessment_id']
        assert event['submission_id']==detail['submission']['submission_id']
        assert event['timestamp'] and 'engine_version' in event
    assert all(e['previous_audit_run_id']==first['audit_run_id'] for e in new['events'])
    assert all(service()._path(rid).read_bytes()==data for rid,data in before.items())
    assert workspace(client,q2)['current_audit']['audit_run_id']==other['audit_run_id']
    assert 'external_candidate_ref' not in json.dumps(new)


def test_equal_score_has_comparison_without_score_changed_event(questions):
    client,_,_,cid,_=questions
    rev,_=reading(client,cid);first=analyze(client,cid,request_for(client,cid,rev))
    changed=correct(client,cid,rev,full_text()+'\n')
    req=request_for(client,cid,changed);new=analyze(client,cid,req)
    assert new['suggested_score']==first['suggested_score']==20
    assert new['comparison']['score_changed'] is False
    assert 'suggested_score_changed' not in {e['event_type'] for e in new['events']}
    assert analyze(client,cid,req)==new # replay does not duplicate telemetry
    third=analyze(client,cid,{**req,'execution_key':uuid4().hex})
    assert third['comparison']['previous_audit_run_id']==first['audit_run_id']
    assert workspace(client,cid)['audits'][1]['comparison']==new['comparison']


def test_failed_reanalysis_null_score_retry_and_review(questions,monkeypatch):
    client,_,_,cid,_=questions
    rev,_=reading(client,cid);first=analyze(client,cid,request_for(client,cid,rev))
    old=service()._path(first['audit_run_id']).read_bytes()
    changed=correct(client,cid,rev,'texto sem item explícito')
    req=request_for(client,cid,changed)
    original=accepted_audit.audit_accepted_tme_transcription
    def fail(*args):raise RuntimeError('controlled private failure')
    monkeypatch.setattr(accepted_audit,'audit_accepted_tme_transcription',fail)
    failed=analyze(client,cid,req)
    assert failed['status']=='FAILED' and failed['suggested_score'] is None
    assert failed['comparison']['previous_suggested_score']==20 and failed['comparison']['current_suggested_score'] is None
    assert 'audit_failed' in {e['event_type'] for e in failed['events']}
    assert 'suggested_score_changed' not in {e['event_type'] for e in failed['events']}
    w=workspace(client,cid)
    assert w['analysis_state']=='FAILED' and w['state']=='REVIEW'
    assert w['current_audit']['audit_run_id']==failed['audit_run_id']
    assert w['current_version']['version_number']==2 and w['partial_suggestion']['analyzed_questions']==0
    assert w['partial_suggestion']['awaiting_reanalysis']==1
    assert w['partial_suggestion']['suggested_score']==0 # empty aggregate, not a failed-run score
    assert analyze(client,cid,req)['audit_run_id']==failed['audit_run_id']
    monkeypatch.setattr(accepted_audit,'audit_accepted_tme_transcription',original)
    retry=analyze(client,cid,{**req,'execution_key':uuid4().hex})
    assert retry['audit_run_id']!=failed['audit_run_id'] and retry['status']=='COMPLETED'
    assert retry['review_required'] and retry['suggested_score']==0 # engine's real withhold policy
    w=workspace(client,cid)
    assert w['state']=='REVIEW' and len(w['audits'])==3
    assert service()._path(first['audit_run_id']).read_bytes()==old


def test_revision_changes_while_engine_runs_result_is_preserved_stale(questions,monkeypatch):
    client,_,_,cid,_=questions
    rev,_=reading(client,cid);request=request_for(client,cid,rev)
    started,release=Event(),Event()
    original=accepted_audit.audit_accepted_tme_transcription
    def slow(*args):
        started.set()
        assert release.wait(20)
        return original(*args)
    monkeypatch.setattr(accepted_audit,'audit_accepted_tme_transcription',slow)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(analyze,client,cid,request)
        try:
            assert started.wait(10)
            changed=correct(client,cid,rev,full_text()+'\n')
        finally:release.set()
        old=pending.result(timeout=20)
    assert old['stale'] and old['transcription_version_id']==rev['transcription_id']+':1'
    w=workspace(client,cid)
    assert w['current_audit'] is None and w['current_version']['version_number']==2
    assert w['reanalysis_required'] and w['partial_suggestion']['analyzed_questions']==0
    assert client.post(f'/tme/cases/{cid}/audits',json=request).status_code==409
    new=analyze(client,cid,request_for(client,cid,changed))
    assert not new['stale'] and new['comparison']['previous_audit_run_id']==old['audit_run_id']


def test_concurrent_same_key_executes_engine_once(questions,monkeypatch):
    client,_,_,cid,_=questions
    rev,_=reading(client,cid);request=request_for(client,cid,rev)
    started,release=Event(),Event();calls=[]
    original=accepted_audit.audit_accepted_tme_transcription
    def slow(*args):
        calls.append(1);started.set();assert release.wait(20);return original(*args)
    monkeypatch.setattr(accepted_audit,'audit_accepted_tme_transcription',slow)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first=pool.submit(analyze,client,cid,request)
        try:
            assert started.wait(10)
            second=pool.submit(analyze,client,cid,request)
        finally:release.set()
        a,b=first.result(timeout=20),second.result(timeout=20)
    assert a['audit_run_id']==b['audit_run_id'] and len(calls)==1
    assert len(workspace(client,cid)['audits'])==1
