"""Permanent regressions from the read-only P2-CAP-03B-1 audit."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from threading import Event
from uuid import uuid4

import pytest

from confia_lean_auditor.recognition import execution
from confia_lean_auditor.recognition.fake import FakeTestRecognizer
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.recognition.schemas import RecognitionRequest
from confia_lean_auditor.recognition.service import RecognitionConflict, RecognitionService
from confia_lean_auditor.submissions.schemas import SubmissionRequest, TranscriptionRecord, TranscriptionRevision
from confia_lean_auditor.submissions.store import SubmissionStore
from test_submissions import payload


REQUEST = RecognitionRequest(provider="fake_test", idempotency_key="one-action")


def setup_service(tmp_path, adapter=None, timeout=1):
    store = SubmissionStore(tmp_path / "submissions")
    sid = store.receive(SubmissionRequest.model_validate(payload(2)))[0].submission_id
    adapter = adapter or FakeTestRecognizer()
    registry = RecognizerRegistry()
    registry.register(adapter.provider, lambda: adapter)
    return RecognitionService(store, registry, timeout_seconds=timeout), sid


def original_hashes(store, sid):
    folder = store.root / sid
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()
            if p.name in {"submission.json", "receipt.json", "snapshot.json"} or p.suffix == ".png"}


def all_submission_files(store, sid):
    return {str(p.relative_to(store.root / sid)): p.read_bytes() for p in (store.root / sid).rglob("*") if p.is_file()}


def make_pair(service, sid):
    run, _ = service.recognize(sid, REQUEST)
    history = service.store.transcription_history(run.transcription_id)
    # Create a fresh consistent pair so invalid attempts cannot merely hit an existing destination.
    rid = "run_" + uuid4().hex
    tid = "tr_" + rid[4:]
    record = history.transcription.model_copy(update={"transcription_id": tid, "recognizer_run_id": rid})
    revision = history.revisions[0].model_copy(update={"transcription_id": tid, "recognizer_run_id": rid})
    result = run.result.model_copy(update={"recognizer_run_id": rid})
    run = run.model_copy(update={"transcription_id": tid, "recognizer_run_id": rid, "result": result})
    return record, revision, run


@pytest.mark.parametrize("status", ["NEEDS_REVIEW", "DRAFT", "ACCEPTED"])
def test_exact_exploit_automatic_without_run_rejected_before_any_persistence(tmp_path, status):
    service, sid = setup_service(tmp_path)
    record, revision, _ = make_pair(service, sid)
    revision = TranscriptionRevision.model_validate({**revision.model_dump(), "status": status})
    before = all_submission_files(service.store, sid)
    with service.store._locked(exclusive=True), pytest.raises(ValueError):
        service.store._publish_transcription(record, revision, recognition_run=None)
    assert all_submission_files(service.store, sid) == before
    assert not (service.store.root / sid / "transcriptions" / record.transcription_id).exists()


@pytest.mark.parametrize("status", ["DRAFT", "ACCEPTED"])
def test_automatic_with_run_cannot_publish_non_review_status(tmp_path, status):
    service, sid = setup_service(tmp_path)
    record, revision, run = make_pair(service, sid)
    revision = TranscriptionRevision.model_validate({**revision.model_dump(), "status": status})
    before = all_submission_files(service.store, sid)
    with service.store._locked(exclusive=True), pytest.raises(ValueError):
        service.store._publish_transcription(record, revision, recognition_run=run)
    assert all_submission_files(service.store, sid) == before


@pytest.mark.parametrize("change", ["submission", "transcription", "revision", "run_id", "provider", "provenance", "segments", "record", "output_hash"])
def test_cross_referenced_pair_rejected_before_persistence(tmp_path, change):
    service, sid = setup_service(tmp_path)
    record, revision, run = make_pair(service, sid)
    if change == "submission": run = run.model_copy(update={"submission_id": "sub_" + "f" * 32})
    if change == "transcription": run = run.model_copy(update={"transcription_id": "tr_" + "f" * 32})
    if change == "revision": run = run.model_copy(update={"revision_number": 2})
    if change == "run_id": revision = revision.model_copy(update={"recognizer_run_id": "run_" + "f" * 32})
    if change == "provider": revision = revision.model_copy(update={"provider": "another"})
    if change == "provenance":
        provenance = revision.provenance.model_copy(update={"parameters": {"altered": True}})
        record = record.model_copy(update={"provenance": provenance})
        revision = revision.model_copy(update={"provenance": provenance})
    if change == "segments":
        revision = revision.model_copy(update={"segments": [s.model_copy(update={"latex": "2 + 2 = 4"}) for s in revision.segments]})
    if change == "record": record = record.model_copy(update={"transcription_id": "tr_" + "f" * 32})
    if change == "output_hash": run = run.model_copy(update={"result": run.result.model_copy(update={"output_hash": "0" * 64})})
    before = all_submission_files(service.store, sid)
    with service.store._locked(exclusive=True), pytest.raises(ValueError):
        service.store._publish_transcription(record, revision, recognition_run=run)
    assert all_submission_files(service.store, sid) == before


def test_manual_cannot_publish_recognition_and_valid_pair_has_no_acceptance(tmp_path):
    service, sid = setup_service(tmp_path)
    record, revision, run = make_pair(service, sid)
    empty = {"source": "manual", "provider": None, "recognizer_run_id": None, "provenance": None, "recognizer": None, "recognizer_version": None}
    manual_record = TranscriptionRecord.model_validate({**record.model_dump(), **empty})
    manual_revision = TranscriptionRevision.model_validate({**revision.model_dump(), **empty})
    before = all_submission_files(service.store, sid)
    with service.store._locked(exclusive=True), pytest.raises(ValueError):
        service.store._publish_transcription(manual_record, manual_revision, recognition_run=run)
    assert all_submission_files(service.store, sid) == before
    with service.store._locked(exclusive=True):
        service.store._publish_transcription(record, revision, recognition_run=run)
    history = service.store.transcription_history(record.transcription_id)
    assert history.revisions[0].status == "NEEDS_REVIEW" and history.acceptances == []
    assert service.get(sid, run.recognizer_run_id) == run
    assert all(s.latex == "2 + 2 = 5" for s in history.revisions[0].segments)


@pytest.mark.parametrize("change", ["run_transcription", "run_submission", "run_revision", "run_id", "run_provider", "run_provenance", "missing_revision", "missing_run", "revision_run_id", "revision_segments", "submission_artifacts"])
def test_read_rejects_tampered_or_missing_referential_provenance(tmp_path, change):
    service, sid = setup_service(tmp_path)
    run, _ = service.recognize(sid, REQUEST)
    folder = service.store.root / sid / "transcriptions" / run.transcription_id
    path = folder / "recognition.json"
    value = json.loads(path.read_bytes())
    if change == "run_transcription": value["transcription_id"] = "tr_" + "f" * 32
    if change == "run_submission": value["submission_id"] = "sub_" + "f" * 32
    if change == "run_revision": value["revision_number"] = 2
    if change == "run_id": value["recognizer_run_id"] = "run_" + "f" * 32
    if change == "run_provider": value["result"]["provider"] = "another"
    if change == "run_provenance": value["provenance"]["parameters"]["altered"] = True
    path.write_text(json.dumps(value))
    revision_path = folder / "revisions" / "revision_000001.json"
    if change == "missing_revision": revision_path.unlink()
    if change == "missing_run": path.unlink()
    if change in {"revision_run_id", "revision_segments"}:
        revision = json.loads(revision_path.read_bytes())
        if change == "revision_run_id": revision["recognizer_run_id"] = "run_" + "f" * 32
        else: revision["segments"][0]["latex"] = "2 + 2 = 4"
        revision_path.write_text(json.dumps(revision))
    if change == "submission_artifacts":
        for name in ("submission.json", "receipt.json"):
            metadata_path = service.store.root / sid / name
            metadata = json.loads(metadata_path.read_bytes())
            metadata["page_images"][0]["sha256"] = "0" * 64
            metadata_path.write_text(json.dumps(metadata))
    before = all_submission_files(service.store, sid)
    with pytest.raises(ValueError): service.get(sid, run.recognizer_run_id)
    with pytest.raises(ValueError): service.store.transcription_history(run.transcription_id)
    assert all_submission_files(service.store, sid) == before  # No silent repair.


@pytest.mark.parametrize("stage", ["before_transcription", "during_revision", "before_run", "before_rename", "after_rename", "after_sync"])
def test_publication_failure_keeps_both_or_neither_and_restart_retry(tmp_path, monkeypatch, stage):
    service, sid = setup_service(tmp_path)
    store = service.store
    before = original_hashes(store, sid)
    write, sync = store._write, store._sync_directory
    import confia_lean_auditor.submissions.store as store_module
    replace = store_module.os.replace
    def fail_write(path, data):
        if stage == "before_transcription" and path.name == "transcription.json": raise OSError("simulated")
        if stage == "during_revision" and path.name.startswith("revision_"):
            write(path, data[:10]); raise OSError("simulated partial revision")
        if stage == "before_run" and path.name == "recognition.json": raise OSError("simulated")
        write(path, data)
    def fail_replace(source, destination):
        if stage == "before_rename": raise OSError("simulated")
        replace(source, destination)
        if stage == "after_rename": raise OSError("simulated after rename")
    def fail_sync(path):
        if stage == "after_sync" and path.name == "transcriptions": raise OSError("simulated final fsync")
        sync(path)
    with monkeypatch.context() as patcher:
        patcher.setattr(store, "_write", fail_write)
        patcher.setattr(store, "_sync_directory", fail_sync)
        patcher.setattr(store_module.os, "replace", fail_replace)
        with pytest.raises(OSError): service.recognize(sid, REQUEST)
    runs, summaries = service.list(sid), store.list_transcriptions(sid)
    count = 1 if stage in {"after_rename", "after_sync"} else 0
    assert len(runs) == len(summaries) == count
    assert not list((store.root / sid / "transcriptions").glob(".pending-*"))
    restarted = RecognitionService(SubmissionStore(store.root), service.registry, timeout_seconds=1)
    run, created = restarted.recognize(sid, REQUEST)
    assert created == (count == 0)
    assert len(restarted.list(sid)) == len(store.list_transcriptions(sid)) == 1
    assert run.transcription_id == store.list_transcriptions(sid)[0].transcription.transcription_id
    assert original_hashes(store, sid) == before


class BlockingRecognizer(FakeTestRecognizer):
    def __init__(self, fail=False):
        self.entered, self.release, self.exited = Event(), Event(), Event()
        self.calls = 0
        self.fail = fail
    def recognize(self, source):
        self.calls += 1
        self.deadline = source.deadline
        self.entered.set()
        try:
            if not self.release.wait(3): raise TimeoutError("test guard")
            if self.fail: raise RuntimeError("credential-secret manuscript stack trace")
            return super().recognize(source)
        finally: self.exited.set()


@pytest.mark.parametrize("fail", [False, True])
def test_provider_outside_global_lock_same_key_once_and_unrelated_operations(tmp_path, fail):
    adapter = BlockingRecognizer(fail)
    service, sid = setup_service(tmp_path, adapter, timeout=3)
    store = service.store
    before = original_hashes(store, sid)
    other = payload(); other["snapshot_json"] = other["snapshot_json"].replace("snapshot:test-01", "snapshot:unrelated")
    with ThreadPoolExecutor(max_workers=4) as pool:
        first = pool.submit(service.recognize, sid, REQUEST)
        assert adapter.entered.wait(1)
        second = pool.submit(RecognitionService(SubmissionStore(store.root), service.registry, timeout_seconds=3).recognize, sid, REQUEST)
        try:
            assert len(pool.submit(store.list).result(timeout=0.5)) == 1
            receipt, created = pool.submit(store.receive, SubmissionRequest.model_validate(other)).result(timeout=0.5)
            assert created
            quick_registry = RecognizerRegistry()
            quick_registry.register("fake_test", FakeTestRecognizer)
            unrelated = RecognitionService(SubmissionStore(store.root), quick_registry, timeout_seconds=1)
            assert pool.submit(unrelated.recognize, receipt.submission_id, REQUEST).result(timeout=0.5)[0].status == "NEEDS_REVIEW"
            assert service.list(sid) == [] and store.list_transcriptions(sid) == []
            assert adapter.calls == 1
        finally: adapter.release.set()
        a, b = first.result(timeout=2), second.result(timeout=2)
    assert a[0] == b[0] and sorted([a[1], b[1]]) == [False, True]
    assert adapter.calls == 1
    assert a[0].status == ("FAILED" if fail else "NEEDS_REVIEW")
    assert len(store.list_transcriptions(sid)) == (0 if fail else 1)
    assert adapter.deadline.timeout_seconds == 3
    assert original_hashes(store, sid) == before


def test_timeout_returns_failed_replays_while_worker_active_and_discards_late_output(tmp_path):
    adapter = BlockingRecognizer()
    service, sid = setup_service(tmp_path, adapter, timeout=0.05)
    before = original_hashes(service.store, sid)
    with ThreadPoolExecutor(max_workers=3) as pool:
        first = pool.submit(service.recognize, sid, REQUEST)
        assert adapter.entered.wait(1)
        second = pool.submit(RecognitionService(SubmissionStore(service.store.root), service.registry, timeout_seconds=0.05).recognize, sid, REQUEST)
        try:
            a, b = first.result(timeout=1), second.result(timeout=1)
            assert a[0] == b[0] and a[0].error_code == "PROVIDER_TIMEOUT"
            assert sorted([a[1], b[1]]) == [False, True]
            assert adapter.calls == 1 and not adapter.exited.is_set()
            assert pool.submit(service.store.list).result(timeout=0.5)
            assert service.store.list_transcriptions(sid) == []
            assert service.recognize(sid, REQUEST) == (a[0], False)
        finally: adapter.release.set()
    assert adapter.exited.wait(1)
    assert service.get(sid, a[0].recognizer_run_id) == a[0]
    assert service.store.list_transcriptions(sid) == []
    assert original_hashes(service.store, sid) == before
    assert "credential" not in a[0].model_dump_json()


def test_failed_timeout_publication_retains_narrow_lease_until_worker_finishes(tmp_path, monkeypatch):
    adapter = BlockingRecognizer()
    service, sid = setup_service(tmp_path, adapter, timeout=0.05)
    with ThreadPoolExecutor(max_workers=2) as pool:
        with monkeypatch.context() as patcher:
            patcher.setattr(service.store, "_write_atomic_new", lambda *args: (_ for _ in ()).throw(OSError("full disk")))
            first = pool.submit(service.recognize, sid, REQUEST)
            assert adapter.entered.wait(1)
            with pytest.raises(OSError): first.result(timeout=1)
        restarted = RecognitionService(SubmissionStore(service.store.root), service.registry, timeout_seconds=0.5)
        second = pool.submit(restarted.recognize, sid, REQUEST)
        try:
            assert pool.submit(service.store.list).result(timeout=0.5)
            assert adapter.calls == 1 and not second.done()
        finally: adapter.release.set()
        assert second.result(timeout=2)[0].status == "NEEDS_REVIEW"
    assert adapter.calls == 2  # Starts only AFTER the first unfinished worker completes.


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "invalid", "1e100"])
def test_timeout_configuration_invalid_never_calls_provider(tmp_path, monkeypatch, value):
    monkeypatch.setenv("CONFIA_RECOGNITION_TIMEOUT_SECONDS", value)
    with pytest.raises(ValueError): RecognitionService(SubmissionStore(tmp_path), RecognizerRegistry())


def test_timeout_configuration_recorded_and_changed_key_conflicts(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_RECOGNITION_TIMEOUT_SECONDS", "0.5")
    service, sid = setup_service(tmp_path)
    configured = RecognitionService(service.store, service.registry)
    run, _ = configured.recognize(sid, REQUEST)
    assert run.provenance.parameters["confia_total_timeout_seconds"] == 0.5
    monkeypatch.setenv("CONFIA_RECOGNITION_TIMEOUT_SECONDS", "0.6")
    with pytest.raises(RecognitionConflict): RecognitionService(service.store, service.registry).recognize(sid, REQUEST)


def test_provider_worker_capacity_fails_safely_without_execution(tmp_path, monkeypatch):
    from threading import BoundedSemaphore
    slots = BoundedSemaphore(1); slots.acquire()
    monkeypatch.setattr(execution, "_PROVIDER_SLOTS", slots)
    class Forbidden(FakeTestRecognizer):
        def recognize(self, source): pytest.fail("saturated execution must not call provider")
    service, sid = setup_service(tmp_path, Forbidden())
    try: run, _ = service.recognize(sid, REQUEST)
    finally: slots.release()
    assert run.status == "FAILED" and run.error_code == "PROVIDER_BUSY"
    assert service.store.list_transcriptions(sid) == []


def test_provider_cannot_succeed_after_deadline_even_if_observer_sees_completed_future(tmp_path, monkeypatch):
    import time
    import confia_lean_auditor.recognition.service as service_module
    class Slow(FakeTestRecognizer):
        def recognize(self, source):
            time.sleep(0.03)
            return super().recognize(source)
    service, sid = setup_service(tmp_path, Slow(), timeout=0.01)
    start = service_module.start_provider
    def delayed_observer(operation, deadline):
        future = start(operation, deadline)
        future.result(timeout=1)  # Simulate observer resuming after provider completes late.
        return future
    monkeypatch.setattr(service_module, "start_provider", delayed_observer)
    run, _ = service.recognize(sid, REQUEST)
    assert run.status == "FAILED" and run.error_code == "PROVIDER_TIMEOUT"
    assert service.store.list_transcriptions(sid) == []


def test_without_key_creates_distinct_runs_and_keyed_replay_after_restart(tmp_path):
    service, sid = setup_service(tmp_path)
    before = original_hashes(service.store, sid)
    request = RecognitionRequest(provider="fake_test")
    first, created1 = service.recognize(sid, request)
    second, created2 = service.recognize(sid, request)
    assert created1 and created2 and first.recognizer_run_id != second.recognizer_run_id
    keyed, _ = service.recognize(sid, REQUEST)
    restarted = RecognitionService(SubmissionStore(service.store.root), service.registry, timeout_seconds=1)
    assert restarted.recognize(sid, REQUEST) == (keyed, False)
    assert len(restarted.list(sid)) == len(service.store.list_transcriptions(sid)) == 3
    assert original_hashes(service.store, sid) == before
