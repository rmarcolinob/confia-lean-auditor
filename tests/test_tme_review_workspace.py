"""D2 exercises real stores and routes. OCR/math transports are isolated in tests."""
from pathlib import Path
import json
import pytest
from test_tme_full_exam import demo, package, receive, png
from confia_lean_auditor.submissions.router import store as submission_store
from confia_lean_auditor.tme import router as tme_router
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.recognition.mathpix_image import MathpixImageProvider
import httpx


def setup_question(client, images=False, candidate=True):
    body = package(client, png() if images else None, "image/png" if images else "application/pdf")
    if candidate:
        body["pages"] = [{"page_number":1,"question_hint":"TME2026P1", "transcription_candidate":"x = 1",
                          "confidence":0.7,"transcription_provider":"capture-provider","transcription_version":"v1"}]
    detail = receive(client, body)
    eid=detail["submission"]["submission_id"]
    cases=detail["question_attempts"]
    pages=detail["submission"]["pages"]
    bindings=[{"question_attempt_id":cases[0]["case_id"],"exam_page_id":p["exam_page_id"],"order":i+1} for i,p in enumerate(pages)]
    bindings.append({"question_attempt_id":cases[1]["case_id"],"exam_page_id":pages[0]["exam_page_id"],"order":1})
    assert client.put(f"/tme/exam-submissions/{eid}/page-mapping",json={"expected_version":1,"bindings":bindings}).status_code==200
    return detail, cases[0]["case_id"], cases[1]["case_id"]


def workspace(client,cid):
    r=client.get(f"/tme/question-attempts/{cid}/workspace")
    assert r.status_code==200,r.text
    return r.json()


def initial(client,cid,origin="capture"):
    body={"origin":origin,"expected_mapping_version":2}
    if origin=="manual":body["segments"]=[{"segment_id":"typed:0","page_index":0,"order":0,"kind":"text","text":"texto digitado"}]
    return client.post(f"/tme/cases/{cid}/transcriptions",json=body)


def revision(client,cid,tid,number,text="x = 2"):
    return client.post(f"/tme/cases/{cid}/transcriptions/{tid}/revisions",json={"based_on_revision_number":number,
        "segments":[{"segment_id":"human:0","page_index":0,"order":0,"kind":"text","text":text}]})


@pytest.mark.parametrize("images",[False,True])
def test_capture_human_versions_current_and_original_immutable(demo,images):
    client,root=demo
    detail,cid,other=setup_question(client,images)
    eid=detail["submission"]["submission_id"]
    before={p.name:p.read_bytes() for p in (root/'tme_exams'/eid).iterdir() if p.is_file()}
    empty=workspace(client,cid)
    assert empty["state"]=="PENDING" and empty["history"] is None and empty["capture_candidate_available"]
    assert not list((root/'submissions').glob('sub_*')) # GET does not freeze/import.
    r=initial(client,cid);assert r.status_code==201,r.text
    tid=r.json()["transcription_id"];sid=r.json()["submission_id"]
    v1path=root/'submissions'/sid/'transcriptions'/tid/'revisions'/'revision_000001.json'
    v1bytes=v1path.read_bytes()
    first=workspace(client,cid)
    assert first["current_version"]["origin"]=="capture"
    assert first["current_version"]["segments"][0]["exam_page_id"]==detail["submission"]["pages"][0]["exam_page_id"]
    assert first["history"]["revisions"][0]["segments"][0]["confidence"]==0.7
    assert len(first["pages"])==(1 if images else 4)
    assert first["state"]=="REVIEW" and first["audits"]==[]
    assert first["analysis_state"]=="AWAITING_ANALYSIS"
    assert initial(client,cid).status_code==409
    assert revision(client,cid,tid,1).status_code==201
    second=workspace(client,cid)
    assert second["current_version"]["version_id"]==tid+':2'
    assert second["current_version"]["origin"]=="human"
    assert second["current_version"]["created_by"]=="tme-demo-evaluator"
    assert second["current_version"]["predecessor_version_id"]==tid+':1'
    assert second["human_reviewed"] and second["reanalysis_required"]
    assert not second["audit_stale"] # No audit fabricated.
    assert second["analysis_state"]=="REANALYSIS_REQUIRED"
    assert revision(client,cid,tid,1).status_code==409 # concurrent retry cannot duplicate
    assert revision(client,cid,tid,2,"x = 3").status_code==201
    assert sum(v["current"] for v in workspace(client,cid)["versions"])==1
    assert v1path.read_bytes()==v1bytes
    assert workspace(client,other)["history"] is None
    assert before=={p.name:p.read_bytes() for p in (root/'tme_exams'/eid).iterdir() if p.is_file()}
    assert client.get('/tme/cases').json()==[]
    events=workspace(client,cid)["events"]
    assert {e['event_type'] for e in events}=={'transcription_created','transcription_activated','transcription_human_corrected'}
    assert len({e['event_id'] for e in events})==len(events)


def test_typed_initial_version_scope_and_page_validation(demo,monkeypatch):
    client,root=demo
    detail,cid,other=setup_question(client,candidate=False)
    response=initial(client,cid,"manual");assert response.status_code==201,response.text
    assert workspace(client,cid)["current_version"]["origin"]=="human"
    tid=response.json()['transcription_id']
    assert revision(client,other,tid,1).status_code in (404,409)
    bad=client.post(f'/tme/cases/{cid}/transcriptions/{tid}/revisions',json={"based_on_revision_number":1,
        "segments":[{"segment_id":"wrong","page_index":49,"order":0,"kind":"text","text":"x"}]})
    assert bad.status_code==422
    assert len(workspace(client,cid)['versions'])==1
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH','0')
    assert client.get(f'/tme/question-attempts/{cid}/workspace').status_code==401
    assert initial(client,cid).status_code==401
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH','1')
    assert client.get('/assessments').status_code==401


def test_existing_recognition_pipeline_four_pages_and_human_revision(demo,monkeypatch):
    client,root=demo
    _,cid,_=setup_question(client,candidate=False)
    monkeypatch.setenv('CONFIA_MATHPIX_APP_ID','test');monkeypatch.setenv('CONFIA_MATHPIX_APP_KEY','test')
    calls=[]
    def provider(request):
        calls.append(request)
        return httpx.Response(200,json={"text":"texto reconhecido"})
    registry=RecognizerRegistry();registry.register('mathpix_image',lambda:MathpixImageProvider(httpx.MockTransport(provider)))
    monkeypatch.setattr(tme_router,'configured_registry',lambda:registry)
    result=client.post(f'/tme/cases/{cid}/recognize',json={})
    assert result.status_code==200,result.text
    assert result.json()['status']=='NEEDS_REVIEW' and len(calls)==4
    current=workspace(client,cid)
    assert current['current_version']['origin']=='automatic'
    assert len(current['history']['revisions'][0]['segments'])==4
    tid=current['history']['transcription']['transcription_id']
    assert revision(client,cid,tid,1).status_code==201
    assert client.post(f'/tme/cases/{cid}/recognize',json={}).status_code==409
    assert len(calls)==4 # no hidden re-recognition after a human edit


def test_existing_audit_version_binding_goes_stale_without_reanalysis(demo,monkeypatch):
    from confia_lean_auditor.submission_audits.router import service
    from confia_lean_auditor.submission_audits.schemas import AuditRequest
    from confia_lean_auditor.submissions.schemas import AcceptTranscriptionRequest
    client,root=demo
    _,cid,_=setup_question(client)
    r=initial(client,cid);assert r.status_code==201,r.text
    tid,sid=r.json()['transcription_id'],r.json()['submission_id']
    accepted=submission_store().accept_transcription(tid,AcceptTranscriptionRequest(revision_number=1,reviewer_reference='reviewer'))
    audit=service()
    # Store a real failed AuditRun using the existing service, without calling a mathematical engine.
    def unavailable(*args):raise RuntimeError('engine isolated for D2 test')
    monkeypatch.setattr('confia_lean_auditor.tme.accepted_audit.audit_accepted_tme_transcription',unavailable)
    run=audit.execute(sid,AuditRequest(transcription_id=tid,revision_number=1,acceptance_id=accepted.acceptance.acceptance_id))
    assert not run.stale
    path=audit._path(run.audit_run_id);before=path.read_bytes()
    assert revision(client,cid,tid,1).status_code==201
    w=workspace(client,cid)
    assert w['audit_stale'] and w['reanalysis_required']
    assert w['audits'][0]['revision_number']==1
    assert w['audits'][0]['transcription_id']==tid
    assert path.read_bytes()==before
    assert len(list(audit.root.glob('aud_*.json')))==1
    event=next(e for e in w['events'] if e['event_type']=='audit_marked_stale')
    assert event['transcription_version_id']==tid+':2'
    assert revision(client,cid,tid,2,'x = 3').status_code==201
    assert next(e for e in workspace(client,cid)['events'] if e['event_type']=='audit_marked_stale')['event_id']==event['event_id']


def test_frozen_mapping_other_question_independence_and_owner_scope(demo):
    from confia_lean_auditor.main import app
    from confia_lean_auditor.tme.auth import require_tme_evaluator, TMEEvaluator
    client,_=demo
    detail,cid,other=setup_question(client)
    eid=detail['submission']['submission_id'];base=f'/tme/exam-submissions/{eid}'
    assert initial(client,cid).status_code==201
    old=workspace(client,cid)
    mapping=client.get(base).json()['mapping']
    q1bindings=[b for b in mapping['bindings'] if b['question_attempt_id']==cid]
    # Changing Q2 must not invalidate Q1's frozen pages/version.
    r=client.put(base+'/page-mapping',json={'expected_version':2,'bindings':q1bindings})
    assert r.status_code==200,r.text
    assert workspace(client,cid)['current_version']==old['current_version']
    assert workspace(client,other)['pages']==[]
    assert client.put(base+'/page-mapping',json={'expected_version':3,'bindings':[]}).status_code==409
    assert initial(client,other).status_code==409 # stale mapping cannot import
    app.dependency_overrides[require_tme_evaluator]=lambda:TMEEvaluator('foreign')
    try:
        assert client.get(f'/tme/question-attempts/{cid}/workspace').status_code==403
        assert initial(client,cid).status_code==403
    finally:app.dependency_overrides.pop(require_tme_evaluator)


def test_candidate_for_another_question_is_not_imported_and_bad_source_blocks_edits(demo):
    client,root=demo
    detail,cid,other=setup_question(client)
    assert initial(client,other).status_code==422
    assert workspace(client,other)['history'] is None
    r=initial(client,cid);assert r.status_code==201,r.text
    sid,tid=r.json()['submission_id'],r.json()['transcription_id']
    (root/'submissions'/sid/'page_1.png').write_bytes(b'tampered')
    assert revision(client,cid,tid,1).status_code==409
    assert client.get(f'/tme/question-attempts/{cid}/workspace').status_code==409


def test_question_states_respect_existing_audit_review_requirements():
    from types import SimpleNamespace as NS
    from confia_lean_auditor.tme.question_review import question_state
    case = NS(status="RECEIVED")
    run = NS(stale=False, status="COMPLETED", result=NS(needs_review=True, score=20))
    assert question_state(case, False, []) == "PENDING"
    assert question_state(case, True, []) == "REVIEW"
    assert question_state(case, True, [run]) == "REVIEW"
    run.result.needs_review = False
    assert question_state(case, True, [run]) == "READY"
    run.stale = True
    assert question_state(case, True, [run]) == "REVIEW"
    case.status = "DECIDED"
    assert question_state(case, True, [run]) == "CONFIRMED"
