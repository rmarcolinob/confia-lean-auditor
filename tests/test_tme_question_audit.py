"""Real stable engine + stores behind the D3 product contract. No math fixtures changed."""
import json
from pathlib import Path
from uuid import uuid4
import pytest
from test_tme_full_exam import demo
from test_tme_review_workspace import setup_question, workspace, revision
from test_tme_accepted_integration import solution_for, FULL
from confia_lean_auditor.submission_audits.router import service
from confia_lean_auditor.tme.registry import audit_tme


@pytest.fixture
def questions(demo, monkeypatch):
    monkeypatch.setenv('CONFIA_TME_QUESTION_USE_LEAN', '0')
    client, root = demo
    detail, q1, q2 = setup_question(client, candidate=False)
    return client, root, detail, q1, q2


def reading(client, cid, n=1, text=None):
    solution = solution_for(n, FULL[n])
    if text is None:
        text = '\n'.join(f'[{item}]\n{value}' for item, value in solution.items())
    r=client.post(f'/tme/cases/{cid}/transcriptions',json={'origin':'manual','expected_mapping_version':2,
        'segments':[{'segment_id':'typed:0','page_index':0,'order':0,'kind':'text','text':text}]})
    assert r.status_code==201,r.text
    return r.json(), solution


def request_for(client, cid, rev):
    r=client.post(f'/tme/cases/{cid}/transcriptions/{rev["transcription_id"]}/accept',json={'revision_number':rev['revision_number']})
    assert r.status_code==200,r.text
    return dict(transcription_id=rev['transcription_id'],revision_number=rev['revision_number'],acceptance_id=r.json()['acceptance']['acceptance_id'],execution_key=uuid4().hex)


def analyze(client, cid, request):
    r=client.post(f'/tme/cases/{cid}/audits',json=request)
    assert r.status_code==200,r.text
    return r.json()


def test_real_engine_score_rubric_evidence_events_and_exact_version(questions):
    client, root, detail, cid, other=questions
    rev,solution=reading(client,cid)
    run=analyze(client,cid,request_for(client,cid,rev))
    _,expected=audit_tme('TME2026P1',solution,use_lean=False)
    assert run['suggested_score']==float(expected.score)==20
    assert run['max_score']==20 and run['status']=='COMPLETED' and not run['review_required']
    assert run['engine_mode']=='TME_CURRENT' and run['engine_config']=={'use_lean':False}
    assert run['transcription_version_id']==f'{rev["transcription_id"]}:1'
    assert run['question_attempt_id']==cid and run['assessment_id']==detail['submission']['assessment_id']
    assert run['participant_id']==detail['submission']['participant_id']
    assert run['submission_id']==detail['submission']['submission_id']
    assert run['rubric_items'][0]['suggested_points']==float(expected.items[0].points_awarded)
    assert len(run['rubric_items'])==4 and run['evidences'] and run['checker_summary']
    checks={c['checker_id']:c for c in run['checker_summary']}
    assert all(checks[c]['fact_id']!='c.single_list_error' for c in run['rubric_items'][2]['checker_ids'])
    assert any(e['text'] and e['exam_page_id'] for e in run['evidences'])
    assert all(e['source_span']['scope']=='engine_input' for e in run['evidences'] if e['source_span'])
    assert all(e['region'] is None for e in run['evidences'])
    assert run['started_at']<=run['completed_at']
    assert {e['event_type'] for e in run['events']}=={'audit_started','audit_completed','rubric_item_decided','checker_result_recorded'}
    assert all(e['transcription_version_id']==run['transcription_version_id'] and e['timestamp'] and e['participant_id']==run['participant_id'] for e in run['events'])
    assert 'external_candidate_ref' not in json.dumps(run) and str(root) not in json.dumps(run)
    assert 'bridge' not in run and 'pauta' not in run and 'artifact_dir' not in run
    persisted=service().get(run['audit_run_id'])
    assert persisted.question_context.question_attempt_id==cid
    assert persisted.question_events==run['events'] and persisted.question_events_sha256
    assert persisted.source.provenance.revision.segments==service().get(run['audit_run_id']).source.provenance.revision.segments
    w=workspace(client,cid);assert w['state']=='READY' and w['current_audit']['audit_run_id']==run['audit_run_id']
    assert workspace(client,other)['current_audit'] is None
    assert len(service().list(rev['submission_id']))==1


def test_retry_new_run_history_q2_and_stale_are_independent(questions):
    client,root,detail,cid,other=questions
    rev,_=reading(client,cid);request=request_for(client,cid,rev)
    first=analyze(client,cid,request);path=service()._path(first['audit_run_id']);before=path.read_bytes()
    assert analyze(client,cid,request)['audit_run_id']==first['audit_run_id']
    second=analyze(client,cid,{**request,'execution_key':uuid4().hex})
    assert second['audit_run_id']!=first['audit_run_id'] and path.read_bytes()==before
    r2,_=reading(client,other,n=2);q2=analyze(client,other,request_for(client,other,r2))
    assert q2['problem_id']=='TME2026P2' and q2['audit_run_id']!=second['audit_run_id']
    assert workspace(client,cid)['current_audit']['audit_run_id']==second['audit_run_id']
    assert revision(client,cid,rev['transcription_id'],1,'[a]\n731 - 137 = 595').status_code==201
    w=workspace(client,cid)
    assert w['current_audit'] is None and w['audit_stale'] and w['reanalysis_required']
    assert len(w['audits'])==2 and all(a['stale'] for a in w['audits']) and path.read_bytes()==before
    assert client.post(f'/tme/cases/{cid}/audits',json=request).status_code==409
    assert workspace(client,other)['current_audit']['audit_run_id']==q2['audit_run_id']
    assert client.get(f'/tme/cases/{cid}/audits').json()==w['audits']
    assert len(service().list(rev['submission_id']))==2 # no automatic reanalysis
    assert first['events']==w['audits'][-1]['events'] # completion telemetry immutable across stale


def test_warning_unassigned_text_preserves_engine_withhold_score_and_review(questions):
    client,_,_,cid,_=questions
    rev,_=reading(client,cid,text='texto sem item explícito')
    run=analyze(client,cid,request_for(client,cid,rev))
    assert run['warnings'] and run['review_required']
    assert run['suggested_score']==0 and run['analysis_status']=='COMPLETED_WITH_REVIEW' # stable pauta withhold policy, not a technical fallback
    assert workspace(client,cid)['state']=='REVIEW'
    assert any(e['event_type']=='review_required' for e in run['events'])


def test_technical_failure_persists_no_fictitious_score(questions,monkeypatch):
    client,_,_,cid,_=questions
    rev,_=reading(client,cid)
    def fail(*args):raise RuntimeError('private diagnostic never returned')
    monkeypatch.setattr('confia_lean_auditor.tme.accepted_audit.audit_accepted_tme_transcription',fail)
    run=analyze(client,cid,request_for(client,cid,rev))
    assert run['status']=='FAILED' and run['technical_uncertainty'] and run['review_required']
    assert run['suggested_score'] is None and run['rubric_items']==[]
    assert 'private diagnostic' not in json.dumps(run)
    assert workspace(client,cid)['current_audit']['status']=='FAILED'
    assert service().get(run['audit_run_id']).result is None


def test_current_version_acceptance_scope_and_no_key_are_guarded(questions,monkeypatch):
    client,_,_,cid,other=questions
    rev,_=reading(client,cid);req=request_for(client,cid,rev)
    assert client.post(f'/tme/cases/{cid}/audits',json={k:v for k,v in req.items() if k!='execution_key'}).status_code==422
    assert client.post(f'/tme/cases/{other}/audits',json=req).status_code in (404,409)
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH','0')
    assert client.post(f'/tme/cases/{cid}/audits',json=req).status_code==401
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH','1')
    from confia_lean_auditor.main import app
    from confia_lean_auditor.tme.auth import require_tme_evaluator, TMEEvaluator
    app.dependency_overrides[require_tme_evaluator]=lambda:TMEEvaluator('foreign')
    try:assert client.post(f'/tme/cases/{cid}/audits',json=req).status_code==403
    finally:app.dependency_overrides.pop(require_tme_evaluator)


def test_event_integrity_and_failed_latest_do_not_reuse_older_score(questions, monkeypatch):
    client,root,_,cid,_=questions
    rev,_=reading(client,cid);req=request_for(client,cid,rev)
    first=analyze(client,cid,req)
    def fail(*args):raise RuntimeError('isolated transport')
    monkeypatch.setattr('confia_lean_auditor.tme.accepted_audit.audit_accepted_tme_transcription',fail)
    last=analyze(client,cid,{**req,'execution_key':uuid4().hex})
    w=workspace(client,cid)
    assert w['current_audit']['audit_run_id']==last['audit_run_id']
    assert w['current_audit']['suggested_score'] is None and w['state']=='REVIEW'
    assert w['audits'][1]['suggested_score']==first['suggested_score']
    path=service()._path(first['audit_run_id']);data=json.loads(path.read_text())
    data['question_events'][0]['participant_id']='tampered'
    path.write_text(json.dumps(data))
    assert client.get(f'/tme/question-attempts/{cid}/workspace').status_code==409


def test_real_capture_candidate_reuses_same_engine_and_persisted_events(demo,monkeypatch):
    from test_tme_review_workspace import initial
    monkeypatch.setenv('CONFIA_TME_QUESTION_USE_LEAN','0')
    client,root=demo
    _,cid,_=setup_question(client,candidate=True)
    rev=initial(client,cid).json()
    run=analyze(client,cid,request_for(client,cid,rev))
    assert run['status']=='COMPLETED' and run['review_required'] and run['warnings']
    stored=service().get(run['audit_run_id'])
    assert stored.source.provenance.revision.source=='capture'
    assert stored.question_events==run['events']


def test_item_across_pages_does_not_invent_visual_mapping(questions):
    client,_,_,cid,_=questions
    response=client.post(f'/tme/cases/{cid}/transcriptions',json={'origin':'manual','expected_mapping_version':2,
        'segments':[{'segment_id':'one','page_index':0,'order':0,'kind':'text','text':'[a]\n731-137=594'},
                    {'segment_id':'two','page_index':1,'order':0,'kind':'text','text':'[a]\n137'}]})
    assert response.status_code==201,response.text
    run=analyze(client,cid,request_for(client,cid,response.json()))
    assert run['evidences']
    assert all(e['exam_page_id'] is None and e['region'] is None for e in run['evidences'])
    assert any(e['source_span'] for e in run['evidences'])
