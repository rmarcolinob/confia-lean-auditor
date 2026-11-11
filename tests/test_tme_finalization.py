"""D6 closes real stable-engine questions; no mathematical fixture edits."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
from uuid import uuid4
import pytest
from test_tme_full_exam import demo, package, receive, pdf
from test_tme_question_audit import reading, request_for, analyze
from test_tme_human_confirmation import selection, confirm
from test_tme_review_workspace import workspace, revision
from test_tme_accepted_integration import solution_for, FULL


def summary(client, eid):
    r=client.get(f'/tme/exam-submissions/{eid}/correction')
    assert r.status_code==200,r.text
    return r.json()


def finalize(client,eid,data=None,status=201):
    body=data or dict(expected_snapshot_sha256=summary(client,eid)['snapshot_sha256'],execution_key=uuid4().hex)
    r=client.post(f'/tme/exam-submissions/{eid}/correction/finalize',json=body)
    assert r.status_code==status,r.text
    return r.json()


@pytest.fixture
def exam(demo,monkeypatch):
    monkeypatch.setenv('CONFIA_TME_QUESTION_USE_LEAN','0')
    client,root=demo
    doc=client.post('/tme/assessments',json=dict(title='D6 três questões',academic_year=2026,
        items=[dict(problem_id=f'TME2026P{i}',points=20) for i in (1,2,3)])).json()
    body=package(client,pdf(3));body['assessment_identifier']=doc['assessment']['assessment_id']
    detail=receive(client,body);eid=detail['submission']['submission_id'];cases=detail['question_attempts']
    r=client.put(f'/tme/exam-submissions/{eid}/page-mapping',json=dict(expected_version=1,bindings=[
        dict(question_attempt_id=c['case_id'],exam_page_id=p['exam_page_id'],order=1) for c,p in zip(cases,detail['submission']['pages'])]))
    assert r.status_code==200,r.text
    return client,root,eid,cases


def populate(exam,confirm_last=True):
    client,root,eid,cases=exam
    versions=[];runs=[];decisions=[]
    for i,c in enumerate(cases,1):
        solution=solution_for(i,FULL[i]);text='\n'.join(f'[{k}]\n{v}' for k,v in solution.items() if i!=2 or k!='a')
        rev,_=reading(client,c['case_id'],i,text);run=analyze(client,c['case_id'],request_for(client,c['case_id'],rev))
        versions.append(rev);runs.append(run)
        if i==3 and not confirm_last:continue
        body=selection(run)
        if i>1:body.update(decision_type='ADJUST_SCORE',final_points=18 if i==2 else 19,override_reason='Conferência humana do crédito parcial.')
        decisions.append(confirm(client,c['case_id'],body))
    return versions,runs,decisions


def test_pending_readiness_explicit_absence_and_blocked_event(exam):
    client,_,eid,cases=exam;s=summary(client,eid)
    assert not s['ready_to_finalize'] and s['suggested_total'] is None and s['final_total'] is None
    assert s['suggested_total_complete'] is False and s['total_adjustment'] is None
    assert len(s['blockers'])==3 and all(r['status']=='PENDING' for r in s['questions'])
    body=dict(expected_snapshot_sha256=s['snapshot_sha256'],execution_key=uuid4().hex)
    finalize(client,eid,body,409);finalize(client,eid,body,409)
    after=summary(client,eid)
    assert [e['event_type'] for e in after['events']]==['finalization_requested','finalization_blocked']
    assert after['snapshot_sha256']==s['snapshot_sha256']


def test_complete_summary_snapshots_totals_review_gold_and_finalized_list(exam):
    client,root,eid,cases=exam;_,runs,decisions=populate(exam)
    s=summary(client,eid)
    assert s['status']=='READY_TO_FINALIZE' and s['ready_to_finalize']
    assert (Decimal(s['suggested_total']),Decimal(s['final_total']),Decimal(s['total_adjustment']))==(55,57,2)
    assert s['adjusted_question_count']==2 and s['review_question_count']>=1 and s['confirmed_question_count']==3
    before={p:p.read_bytes() for p in (root/'tme_cases').glob('*/human_decisions/*.json')}
    f=finalize(client,eid)
    assert f['version']==1 and f['finalized_by']=='tme-demo-evaluator' and f['participant_code']=='PROVA-2026-001'
    assert f['suggested_total_snapshot']=='55.0' and f['final_total']=='57.0'
    assert [q['human_decision_id'] for q in f['questions']]==[d['human_decision_id'] for d in decisions]
    assert f['questions'][1]['human_decision']['suggested_points']=='15.0'
    after=summary(client,eid)
    assert after['status']=='FINALIZED' and not after['ready_to_finalize']
    assert after['current_final_correction']==f and len(after['gold_rows'])==3
    assert after['gold_rows'][1]['adjustment']=='3.0' and after['gold_rows'][2]['adjustment']=='-1.0'
    e=next(e for e in after['events'] if e['event_type']=='correction_finalized')
    assert e['final_total']=='57.0' and len(e['human_decision_ids'])==3 and e['engines']
    assert not {'name','email','cpf'} & f.keys()
    listing=next(e for e in client.get('/tme/exam-submissions').json() if e['submission_id']==eid)
    assert listing['status']=='FINALIZED' and listing['final_total']=='57.0' and listing['adjusted_question_count']==2
    assert all(p.read_bytes()==data for p,data in before.items())
    assert workspace(client,cases[0]['case_id'])['exam_finalized']


def test_unconfirmed_question_blocker_and_completion(exam):
    client,_,eid,cases=exam;_,runs,_=populate(exam,confirm_last=False)
    s=summary(client,eid)
    assert s['pending_question_count']==1 and s['blockers'][0]['question_order']==3
    assert s['final_total_complete'] is False and s['total_adjustment'] is None
    finalize(client,eid,status=409)
    confirm(client,cases[2]['case_id'],selection(runs[2]))
    assert finalize(client,eid)['confirmed_question_count']==3


def test_stale_invalidated_failed_and_new_audit_block_closure(exam,monkeypatch):
    from confia_lean_auditor.tme import accepted_audit
    client,_,eid,cases=exam;versions,runs,_=populate(exam);cid=cases[0]['case_id']
    r=revision(client,cid,versions[0]['transcription_id'],1,'[a]\n731 - 137 = 594')
    assert r.status_code==201
    s=summary(client,eid)
    assert s['questions'][0]['final_score'] is None and s['questions'][0]['suggested_score'] is None
    assert not s['suggested_total_complete'] and 'desatualizada' in s['blockers'][0]['reason']
    finalize(client,eid,status=409)
    original=accepted_audit.audit_accepted_tme_transcription
    def fail(*args):raise RuntimeError('controlled')
    monkeypatch.setattr(accepted_audit,'audit_accepted_tme_transcription',fail)
    failed=analyze(client,cid,request_for(client,cid,r.json()))
    assert failed['status']=='FAILED' and 'falhou' in summary(client,eid)['blockers'][0]['reason']
    finalize(client,eid,status=409)
    monkeypatch.setattr(accepted_audit,'audit_accepted_tme_transcription',original)
    new=analyze(client,cid,request_for(client,cid,r.json()))
    assert new['status']=='COMPLETED' and 'não confirmada' in summary(client,eid)['blockers'][0]['reason']
    finalize(client,eid,status=409)


def test_double_submit_and_stale_summary(exam):
    client,_,eid,cases=exam;_,runs,decisions=populate(exam)
    old=summary(client,eid);cid=cases[1]['case_id']
    assert client.post(f'/tme/cases/{cid}/reopen',json=dict(human_decision_id=decisions[1]['human_decision_id'],execution_key=uuid4().hex)).status_code==200
    confirm(client,cid,selection(runs[1],expected_last_decision_id=decisions[1]['human_decision_id']))
    finalize(client,eid,dict(expected_snapshot_sha256=old['snapshot_sha256'],execution_key=uuid4().hex),409)
    body=dict(expected_snapshot_sha256=summary(client,eid)['snapshot_sha256'],execution_key=uuid4().hex)
    with ThreadPoolExecutor(max_workers=2) as pool:
        fs=[pool.submit(finalize,client,eid,body) for _ in range(2)]
        a,b=[f.result(timeout=30) for f in fs]
    assert a['final_correction_id']==b['final_correction_id'] and len(summary(client,eid)['final_corrections'])==1
    finalize(client,eid,status=409)
    finalize(client,eid,{**body,'expected_snapshot_sha256':'0'*64},409)


def test_finalized_blocks_product_and_generic_writes_reopen_second_closure(exam):
    from confia_lean_auditor.submission_audits.router import service
    from confia_lean_auditor.submission_audits.schemas import AuditRequest
    from confia_lean_auditor.submissions.schemas import CreateTranscriptionRevisionRequest, CreateTranscriptionRequest
    from confia_lean_auditor.submissions.store import SubmissionConflict
    client,root,eid,cases=exam;versions,runs,decisions=populate(exam);cid=cases[0]['case_id'];rev=versions[0]
    request=request_for(client,cid,rev);f=finalize(client,eid)
    first=(root/'tme_exams'/eid/'finalizations'/'000001.json');before=first.read_bytes()
    assert revision(client,cid,rev['transcription_id'],1,'new').status_code==409
    assert client.post(f'/tme/cases/{cid}/audits',json=request).status_code==409
    confirm(client,cid,selection(runs[0]),409)
    assert client.post(f'/tme/cases/{cid}/reopen',json=dict(human_decision_id=decisions[0]['human_decision_id'],execution_key=uuid4().hex)).status_code==409
    assert client.put(f'/tme/exam-submissions/{eid}/page-mapping',json=dict(expected_version=2,bindings=[])).status_code==409
    store=service().submissions
    with pytest.raises(SubmissionConflict):store.create_transcription_revision(rev['transcription_id'],CreateTranscriptionRevisionRequest(based_on_revision_number=1,reviewer_reference='t',segments=rev['segments']))
    with pytest.raises(SubmissionConflict):store.create_transcription(rev['submission_id'],CreateTranscriptionRequest(reviewer_reference='t',segments=rev['segments']))
    with pytest.raises(SubmissionConflict):service().execute(rev['submission_id'],AuditRequest(**request))
    body=dict(final_correction_id=f['final_correction_id'],execution_key=uuid4().hex)
    for _ in range(2):assert client.post(f'/tme/exam-submissions/{eid}/correction/reopen',json=body).status_code==200
    s=summary(client,eid);assert s['status']=='REOPENED' and s['confirmed_question_count']==3 and s['ready_to_finalize']
    assert client.post(f'/tme/cases/{cid}/reopen',json=dict(human_decision_id=decisions[0]['human_decision_id'],execution_key=uuid4().hex)).status_code==200
    adjust=selection(runs[0],expected_last_decision_id=decisions[0]['human_decision_id']);adjust.update(decision_type='ADJUST_SCORE',final_points=19,override_reason='Revisão após reabertura.')
    confirm(client,cid,adjust)
    second=finalize(client,eid)
    assert second['version']==2 and second['previous_final_correction_id']==f['final_correction_id']
    assert Decimal(second['final_total'])==56 and first.read_bytes()==before
    s=summary(client,eid);assert len(s['final_corrections'])==2
    assert {'correction_reopened','final_correction_superseded'}<={e['event_type'] for e in s['events']}


def test_scope_and_integrity(exam):
    from confia_lean_auditor.main import app
    from confia_lean_auditor.tme.auth import require_tme_evaluator, TMEEvaluator
    client,root,eid,_=exam;populate(exam);finalize(client,eid)
    app.dependency_overrides[require_tme_evaluator]=lambda:TMEEvaluator('other')
    try:
        assert client.get(f'/tme/exam-submissions/{eid}/correction').status_code==403
    finally:app.dependency_overrides.pop(require_tme_evaluator)
    p=root/'tme_exams'/eid/'finalizations'/'000001.json';d=json.loads(p.read_text());d['final_correction']['final_total']='0';p.write_text(json.dumps(d))
    assert client.get(f'/tme/exam-submissions/{eid}/correction').status_code==409


def test_new_run_same_reading_requires_confirmation_and_model_is_engine_agnostic(exam):
    from confia_lean_auditor.tme.finalization import FinalCorrection
    client,_,eid,cases=exam;versions,runs,decisions=populate(exam)
    f=finalize(client,eid)
    generic=json.loads(json.dumps(f))
    for q in generic['questions']:
        q['engine_mode']=q['human_decision']['engine_mode']='FUTURE_CONTRACT_MODE'
        q['engine_version']=q['human_decision']['engine_version']='arbitrary-version'
    assert FinalCorrection.model_validate(generic).final_total==Decimal(57)
    client.post(f'/tme/exam-submissions/{eid}/correction/reopen',json=dict(final_correction_id=f['final_correction_id'],execution_key=uuid4().hex))
    cid=cases[0]['case_id'];new=analyze(client,cid,request_for(client,cid,versions[0]))
    s=summary(client,eid)
    assert s['questions'][0]['audit_run_id']==new['audit_run_id'] and s['questions'][0]['human_decision_id'] is None
    finalize(client,eid,status=409)


def test_generic_audit_started_before_finalization_cannot_publish_after_it(exam,monkeypatch):
    from threading import Event
    from confia_lean_auditor.tme import accepted_audit
    from confia_lean_auditor.submission_audits.router import service
    from confia_lean_auditor.submission_audits.schemas import AuditRequest
    from confia_lean_auditor.submissions.store import SubmissionConflict
    client,_,eid,cases=exam;versions,_,_=populate(exam)
    request=AuditRequest(**request_for(client,cases[0]['case_id'],versions[0]))
    original=accepted_audit.audit_accepted_tme_transcription
    started,release=Event(),Event()
    def slow(*args):
        started.set();assert release.wait(30)
        return original(*args)
    monkeypatch.setattr(accepted_audit,'audit_accepted_tme_transcription',slow)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(service().execute,versions[0]['submission_id'],request)
        try:
            assert started.wait(10)
            f=finalize(client,eid)
        finally:release.set()
        with pytest.raises(SubmissionConflict):pending.result(timeout=30)
    assert summary(client,eid)['current_final_correction']==f
