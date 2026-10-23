"""Real filesystem lifecycle, bounded Home reads, and projection reconstruction."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import pytest

import confia_lean_auditor.main as main
from confia_lean_auditor.tme.auth import TMEEvaluator
from confia_lean_auditor.tme.home_summary import (
    OperationalIndex, case_entry, rebuild_index, summarize,
)
from confia_lean_auditor.tme.models import CaseCreate, CorrectionCase
from confia_lean_auditor.tme.store import case_store
from confia_lean_auditor.submissions.router import store as submission_store
from confia_lean_auditor.submission_audits.router import service as audit_service
from test_tme_pilot import setup, create_case, scan_payload
from test_tme_audit_view import rich_result_for_request
from test_submission_audits import result


@pytest.fixture
def home(setup):
    rebuild_index()
    return setup


def summary(client, period="all"):
    response = client.get('/tme/home-summary', params={'period': period})
    assert response.status_code == 200, response.text
    assert response.headers['cache-control'] == 'no-store'
    return response.json()


def submitted(client):
    case = create_case(client, 'IMAGE_SCAN')
    base = f'/tme/cases/{case["case_id"]}'
    receipt = client.post(base + '/scan', json=scan_payload(1))
    assert receipt.status_code == 201, receipt.text
    return case, base, receipt.json()['submission_id']


def transcribed(client, sid):
    response = client.post(f'/submissions/{sid}/transcriptions', json={
        'reviewer_reference': 'test', 'segments': [
            {'segment_id': 'a', 'page_index': 0, 'order': 0, 'kind': 'text', 'text': '2 + 2 = 4'}]})
    assert response.status_code == 201, response.text
    return response.json()


def accepted(client, base, revision):
    response = client.post(f'{base}/transcriptions/{revision["transcription_id"]}/accept',
                           json={'revision_number': revision['revision_number']})
    assert response.status_code == 200, response.text
    return dict(transcription_id=revision['transcription_id'], revision_number=revision['revision_number'],
                acceptance_id=response.json()['acceptance']['acceptance_id'])


def analyzed(client, base, request, key=None):
    response = client.post(base + '/audits', json={**request, **({'execution_key': key} if key else {})})
    assert response.status_code == 200, response.text
    return response.json()


def test_zero_pending_and_scope(home):
    client, _, _ = home
    assert summary(client)['counts'] == dict(pending=0, in_progress=0, inconclusive=0, finalized=0)
    create_case(client, 'IMAGE_SCAN')
    case_store().create(CaseCreate(problem_id='ITA2025F2Q1', external_candidate_ref='other', source_mode='IMAGE_SCAN'), TMEEvaluator('other'))
    data = summary(client)
    assert data['counts']['pending'] == 1
    assert len(data['priority_cases']) == 1
    assert data['exam_progress'][0]['exam_code'] == 'TME-0001'
    assert 'owner' not in json.dumps(data)


def test_real_inconclusive_then_final_decision(home, monkeypatch):
    client, _, _ = home
    case, base, sid = submitted(client)
    assert summary(client)['counts']['in_progress'] == 1
    revision = transcribed(client, sid)
    request = accepted(client, base, revision)
    monkeypatch.setattr(main, 'execute_audit', rich_result_for_request)
    run = analyzed(client, base, request)
    assert run['status'] == 'COMPLETED' and run['result']['score'] is None
    data = summary(client)
    assert data['counts'] == dict(pending=0, in_progress=0, inconclusive=1, finalized=0)
    assert data['priority_cases'][0]['operational_status'] == 'inconclusive'
    response = client.post(base + '/decision', json={'audit_run_id': run['audit_run_id'], 'max_points': 10, 'final_points': 8})
    assert response.status_code == 201, response.text
    data = summary(client)
    assert data['counts']['finalized'] == 1 and data['counts']['inconclusive'] == 0
    assert data['priority_cases'] == []
    assert data['exam_progress'][0]['percent'] == 100
    assert data['exam_progress'][0]['latest_update'] == response.json()['decided_at']


def test_latest_valid_audit_zero_is_not_inconclusive_and_failed_run_is_not_verdict(home, monkeypatch):
    client, _, _ = home
    _, base, sid = submitted(client)
    request = accepted(client, base, transcribed(client, sid))
    monkeypatch.setattr(main, 'execute_audit', rich_result_for_request)
    analyzed(client, base, request)
    monkeypatch.setattr(main, 'execute_audit', lambda req: result(req.problem_id))
    zero = analyzed(client, base, request, 'numeric-zero')
    assert zero['result']['score'] == 0
    assert summary(client)['counts']['in_progress'] == 1
    monkeypatch.setattr(main, 'execute_audit', rich_result_for_request)
    analyzed(client, base, request, 'inconclusive-again')
    assert summary(client)['counts']['inconclusive'] == 1
    def failed(req):
        raise RuntimeError('technical failure')
    monkeypatch.setattr(main, 'execute_audit', failed)
    assert analyzed(client, base, request, 'failed')['status'] == 'FAILED'
    # Existing workspace selects the latest current COMPLETED result.
    assert summary(client)['counts']['inconclusive'] == 1
    assert sum(summary(client)['counts'].values()) == 1
    _, other_base, other_sid = submitted(client)
    other_request = accepted(client, other_base, transcribed(client, other_sid))
    assert analyzed(client, other_base, other_request)['status'] == 'FAILED'
    assert summary(client)['counts']['in_progress'] == 1
    assert summary(client)['counts']['inconclusive'] == 1


def test_new_revision_and_new_transcription_invalidate_old_audits(home, monkeypatch):
    client, _, _ = home
    _, base, sid = submitted(client)
    revision = transcribed(client, sid)
    request = accepted(client, base, revision)
    monkeypatch.setattr(main, 'execute_audit', rich_result_for_request)
    first = analyzed(client, base, request)
    path = audit_service()._path(first['audit_run_id'])
    original = path.read_bytes()
    response = client.post(f'{base}/transcriptions/{revision["transcription_id"]}/revisions', json={
        'based_on_revision_number': 1, 'change_type': 'reading_correction',
        'segments': revision['segments'], 'status': 'NEEDS_REVIEW'})
    assert response.status_code == 201, response.text
    assert summary(client)['counts']['inconclusive'] == 0
    # A late execution against an older accepted source cannot resurrect its verdict.
    assert analyzed(client, base, request, 'historical')['stale'] is True
    assert summary(client)['counts']['inconclusive'] == 0
    request2 = accepted(client, base, response.json())
    analyzed(client, base, request2)
    assert summary(client)['counts']['inconclusive'] == 1
    transcribed(client, sid)
    assert summary(client)['counts']['inconclusive'] == 0
    assert sum(summary(client)['counts'].values()) == 1
    assert path.read_bytes() == original


def test_progress_distinct_questions_and_resubmission(home):
    client, _, _ = home
    _, base, sid = submitted(client)
    accepted(client, base, transcribed(client, sid))
    assert client.post(base + '/decision', json={'max_points': 10, 'final_points': 5}).status_code == 201
    data = summary(client)
    assert data['exam_progress'][0]['completed_items'] == 1
    create_case(client, 'IMAGE_SCAN')  # New immutable case, same exam/question: retry.
    response = client.post('/tme/cases', json={'problem_id': 'ITA2025F2Q3', 'external_candidate_ref': 'TME-0001', 'source_mode': 'DIGITAL_INK'})
    assert response.status_code == 201
    data = summary(client)
    assert data['exam_progress'][0]['known_items'] == 2
    assert data['exam_progress'][0]['completed_items'] == 0
    assert data['exam_progress'][0]['percent'] == 0
    assert sum(data['counts'].values()) == 3  # Metrics count cases, progress counts distinct questions.


def test_priority_preserves_source_ready_policy_and_next_is_first(home):
    client, _, _ = home
    first, _, _ = submitted(client)
    second, _, _ = submitted(client)
    newest = [create_case(client, 'IMAGE_SCAN') for _ in range(4)]
    priority = summary(client)['priority_cases']
    assert [c['case_id'] for c in priority] == [second['case_id'], first['case_id'], newest[-1]['case_id']]
    assert set(priority[0]) == {'case_id','exam_code','problem_id','question_label','source_mode','operational_status','updated_at'}


def test_periods_midnight_fortaleza_and_global_queue():
    now = datetime(2026, 10, 22, 4, tzinfo=timezone.utc)
    entries = []
    for i, date in enumerate([now, now.replace(hour=2), now-timedelta(days=6), now-timedelta(days=29), now-timedelta(days=30)]):
        case = CorrectionCase(case_id=f'case_{i:032x}', created_by_user_id='owner', created_at=date,
            problem_id='ITA2025F2Q1', external_candidate_ref=f'exam-{i}', source_mode='IMAGE_SCAN')
        entries.append(case_entry(case))
    for period, expected in [('today',1),('7d',3),('30d',4),('all',5)]:
        data = summarize(entries, period, now)
        assert data.counts.pending == expected
        assert len(data.priority_cases) == 3
        assert len(data.exam_progress) == 2


def test_reconstruction_reads_audits_once_and_never_rewrites_history(home, monkeypatch):
    client, _, root = home
    _, base, sid = submitted(client)
    request = accepted(client, base, transcribed(client, sid))
    monkeypatch.setattr(main, 'execute_audit', rich_result_for_request)
    analyzed(client, base, request)
    expected = summary(client)
    artifacts = [p for directory in (root/'submissions', root/'audits', root/'engine-artifacts') for p in directory.rglob('*') if p.is_file()]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}
    index = OperationalIndex()
    index.path.unlink()
    assert client.get('/tme/home-summary').status_code == 503
    from confia_lean_auditor.submission_audits.service import AuditService
    original = AuditService._read
    calls = []
    def read(self, run_id):
        calls.append(run_id)
        return original(self, run_id)
    monkeypatch.setattr(AuditService, '_read', read)
    monkeypatch.setattr(AuditService, 'list', lambda *a: pytest.fail('N x audit directory scan'))
    rebuild_index()
    actual = summary(client)
    assert {k:v for k,v in actual.items() if k != 'generated_at'} == {k:v for k,v in expected.items() if k != 'generated_at'}
    assert len(calls) == 1
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}


@pytest.mark.parametrize("case_count", [5000, 25000])
def test_thousands_of_cases_single_file_read_no_domain_service_calls(home, monkeypatch, case_count):
    client, _, _ = home
    index = OperationalIndex()
    now = datetime.now(timezone.utc)
    entries = {}
    for i in range(case_count):
        case = CorrectionCase(case_id=f'case_{i:032x}', created_by_user_id='tme-demo-evaluator', created_at=now,
            problem_id=f'ITA2025F2Q{i%5+1}', external_candidate_ref=f'exam-{i//5}', source_mode='IMAGE_SCAN')
        entries[case.case_id] = case_entry(case)
    with index.locked():
        index.write(dict(version=1, generation=1, complete=True, cases=entries))
    from confia_lean_auditor.tme.store import CaseStore
    from confia_lean_auditor.submissions.store import SubmissionStore
    from confia_lean_auditor.submission_audits.service import AuditService
    from confia_lean_auditor.recognition.service import RecognitionService
    for cls, method in [(CaseStore,'list_for_user'),(CaseStore,'read'),(SubmissionStore,'list_transcriptions'),(AuditService,'list'),(AuditService,'get'),(RecognitionService,'list')]:
        monkeypatch.setattr(cls, method, lambda *a: pytest.fail('Home must read only the projection'))
    original = Path.read_bytes
    reads = []
    def read(path):
        reads.append(path)
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', read)
    data = summary(client)
    assert reads == [index.path]
    assert data['counts']['pending'] == case_count
    assert len(data['priority_cases']) == 3 and len(data['exam_progress']) == 2
    assert len(json.dumps(data)) < 2000
    assert all(e['known_items'] == 5 for e in data['exam_progress'])


def test_missing_dirty_projection_and_invalid_period_fail_safely(home):
    client, _, _ = home
    assert client.get('/tme/home-summary?period=invalid').status_code == 422
    index = OperationalIndex()
    index.dirty.touch()
    response = client.get('/tme/home-summary')
    assert response.status_code == 503 and response.json()['detail'] == 'Não foi possível carregar os indicadores.'
    assert client.get('/tme').status_code == 200
    rebuild_index()
    assert summary(client)['counts']['pending'] == 0


def test_endpoint_uses_tme_auth(home, monkeypatch):
    client, _, _ = home
    monkeypatch.setenv('CONFIA_TME_DEMO_NO_AUTH', '0')
    assert client.get('/tme/home-summary').status_code == 401


def test_multiple_recognition_runs_retry_and_latest_review(home, monkeypatch):
    import httpx
    from confia_lean_auditor.recognition.registry import RecognizerRegistry
    from confia_lean_auditor.recognition.mathpix_image import MathpixImageProvider
    from confia_lean_auditor.tme import router
    client, _, _ = home
    _, base, sid = submitted(client)
    monkeypatch.setenv('CONFIA_MATHPIX_APP_ID', 'test-id')
    monkeypatch.setenv('CONFIA_MATHPIX_APP_KEY', 'test-key')
    registry = RecognizerRegistry()
    responses = iter([httpx.Response(503), httpx.Response(200, json={'text':'2 + 2 = 4'}), httpx.Response(200, json={'text':'2 + 2 = 4'})])
    registry.register('mathpix_image', lambda: MathpixImageProvider(httpx.MockTransport(lambda _: next(responses))))
    monkeypatch.setattr(router, 'configured_registry', lambda: registry)
    failed = client.post(base + '/recognize', json={})
    assert failed.json()['status'] == 'FAILED'
    first = client.post(base + '/recognize', json={})
    assert first.json()['status'] == 'NEEDS_REVIEW'
    revision = client.get(base + '/transcriptions').json()[0]['latest_revision']
    request = accepted(client, base, revision)
    monkeypatch.setattr(main, 'execute_audit', rich_result_for_request)
    analyzed(client, base, request)
    assert summary(client)['counts']['inconclusive'] == 1
    second = client.post(base + '/recognize', json={})
    assert second.json()['status'] == 'NEEDS_REVIEW'
    assert summary(client)['counts'] == dict(pending=0, finalized=0, inconclusive=0, in_progress=1)
    before = summary(client)
    rebuild_index()
    after = summary(client)
    assert before['priority_cases'] == after['priority_cases']
    assert before['counts'] == after['counts']


def test_concurrent_publications_do_not_lose_entries(home):
    from concurrent.futures import ThreadPoolExecutor
    client, _, _ = home
    def create(i):
        return case_store().create(CaseCreate(problem_id='ITA2025F2Q1', external_candidate_ref=f'EXAM-{i}',
            source_mode='IMAGE_SCAN'), TMEEvaluator('tme-demo-evaluator'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(create, range(20)))
    assert summary(client)['counts']['pending'] == 20


def test_projection_failure_does_not_change_primary_artifacts_and_home_fails_closed(home, monkeypatch):
    client, _, _ = home
    def fail(*args):
        raise OSError('disk unavailable')
    monkeypatch.setattr(OperationalIndex, 'write', fail)
    created = create_case(client, 'IMAGE_SCAN')
    assert client.get(f'/tme/cases/{created["case_id"]}').status_code == 200
    assert client.get('/tme/home-summary').status_code == 503


def test_startup_reconstructs_legacy_data(home):
    client, _, _ = home
    create_case(client, 'IMAGE_SCAN')
    OperationalIndex().path.unlink()
    with client:
        assert summary(client)['counts']['pending'] == 1


def test_corrupted_projection_is_recoverable(home):
    client, _, _ = home
    create_case(client, 'IMAGE_SCAN')
    index = OperationalIndex()
    index.path.write_text('{broken')
    assert client.get('/tme/home-summary').status_code == 503
    rebuild_index()
    assert summary(client)['counts']['pending'] == 1


def test_concurrent_rebuild_cannot_overwrite_new_publication(home, monkeypatch):
    from confia_lean_auditor.tme.home_summary import ConcurrentProjectionUpdate, project_case
    from confia_lean_auditor.tme.store import CaseStore
    client, _, _ = home
    case = create_case(client, 'IMAGE_SCAN')
    original = CaseStore.decision
    def decision(self, case_id, user):
        # Simulate a concurrent publication after the reconstruction snapshot.
        project_case(self.read(case_id), root=self.root)
        return original(self, case_id, user)
    monkeypatch.setattr(CaseStore, 'decision', decision)
    with pytest.raises(ConcurrentProjectionUpdate):
        rebuild_index()
    assert summary(client)['priority_cases'][0]['case_id'] == case['case_id']
