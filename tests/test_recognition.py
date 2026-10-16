"""Recognition fidelity/provenance only; external providers and mathematical audits forbidden."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import socket

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from confia_lean_auditor.main import app
from confia_lean_auditor.recognition.fake import FakeTestRecognizer
from confia_lean_auditor.recognition.registry import configured_registry, RecognizerRegistry, UnknownRecognizer
from confia_lean_auditor.recognition.schemas import ProviderOutput, RecognitionRequest, RecognitionResult, RecognitionRun, RecognitionSegment
from confia_lean_auditor.recognition.service import RecognitionService, canonical_hash
from confia_lean_auditor.submissions import router
from confia_lean_auditor.submissions.schemas import SubmissionRequest
from confia_lean_auditor.submissions.store import SubmissionStore
from test_submissions import payload


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_ENV", "test")
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    return TestClient(app)


def submission(client, pages=1):
    response = client.post("/submissions", json=payload(pages))
    assert response.status_code == 201
    return response.json()["submission_id"]


def recognize(client, sid, **kwargs):
    return client.post(f"/submissions/{sid}/recognitions", json={"provider": "fake_test", **kwargs})


def service_case(tmp_path, adapter):
    store = SubmissionStore(tmp_path / "submissions")
    sid = store.receive(SubmissionRequest.model_validate(payload()))[0].submission_id
    registry = RecognizerRegistry()
    registry.register(adapter.provider, lambda: adapter)
    return RecognitionService(store, registry), sid


def test_registry_explicit_factory_unknown_duplicate_and_future_names():
    registry = RecognizerRegistry()
    for provider in ("mathpix_strokes", "mathpix_image", "vision_model", "fake_test"):
        class LocalAdapter(FakeTestRecognizer):
            pass
        LocalAdapter.provider = provider
        registry.register(provider, LocalAdapter)
        assert registry.create(provider).provider == provider
    assert len(registry.providers()) == 4
    with pytest.raises(UnknownRecognizer):
        registry.create("absent")
    with pytest.raises(ValueError):
        registry.register("fake_test", FakeTestRecognizer)


@pytest.mark.parametrize("env", [None, "production", "staging", "development", "test"])
def test_test_provider_environment_gate(client, monkeypatch, env):
    if env is None:
        monkeypatch.delenv("CONFIA_ENV")
    else:
        monkeypatch.setenv("CONFIA_ENV", env)
    expected = env in {"development", "test"}
    assert configured_registry().providers() == (["fake_test"] if expected else [])
    if env == "production":
        # The legacy protocol fixture explicitly disables auth; production
        # must refuse that configuration rather than expose this endpoint.
        with pytest.raises(RuntimeError, match="authentication cannot be disabled"):
            client.get("/submissions/recognition-providers")
        return
    response = client.get("/submissions/recognition-providers")
    assert response.json() == ([{"provider": "fake_test", "label": "Reconhecedor de teste"}] if expected else [])
    sid = submission(client)
    assert recognize(client, sid).status_code == (201 if expected else 422)


def test_fake_result_null_fields_provenance_hashes_and_immutable_submission(client):
    sid = submission(client, 3)
    folder = router.store().root / sid
    originals = {p.name: p.read_bytes() for p in folder.iterdir()}
    response = recognize(client, sid)
    assert response.status_code == 201, response.text
    summary = response.json()
    assert summary["status"] == "NEEDS_REVIEW" and summary["revision_number"] == 1
    run = client.get(f'/submissions/{sid}/recognitions/{summary["recognizer_run_id"]}').json()
    result = RecognitionResult.model_validate(run["result"])
    assert result.provider_version is None and result.provider_request_id is None
    assert result.latency_ms >= 0 and result.adapter_version == "1.0.0"
    assert len(result.segments) == 3
    for s in result.segments:
        assert s.latex == "2 + 2 = 5"
        assert s.confidence is s.source_region is s.source_stroke_refs is s.text is None
    assert result.output_hash == canonical_hash(ProviderOutput.model_validate(
        result.model_dump(include=set(ProviderOutput.model_fields))).model_dump(mode="json"))
    provenance = summary["provenance"]
    assert provenance["submission_id"] == sid
    assert provenance["input_hash"] == result.input_hash
    assert {a["filename"] for a in provenance["artifacts"]} == {"snapshot.json", "page_1.png", "page_2.png", "page_3.png"}
    assert provenance["parameters"]["real_ocr"] is False
    history = client.get(f'/transcriptions/{summary["transcription_id"]}').json()
    revision = history["revisions"][0]
    assert revision["source"] == "automatic" and revision["status"] == "NEEDS_REVIEW"
    assert revision["provider"] == "fake_test" and revision["recognizer_run_id"] == summary["recognizer_run_id"]
    assert revision["provenance"] == provenance
    assert history["acceptances"] == []
    assert all((folder / name).read_bytes() == data for name, data in originals.items())
    restarted = RecognitionService(SubmissionStore(router.store().root), configured_registry())
    assert restarted.get(sid, summary["recognizer_run_id"]).model_dump(mode="json") == run
    assert client.get(f"/submissions/{sid}/recognitions").json() == [run]


def test_unknown_provider_bad_request_and_no_automatic_accepted(client):
    sid = submission(client)
    for body in ({"provider": "unknown"}, {"provider": "fake_test", "status": "ACCEPTED"},
                 {"provider": "fake_test", "credentials": "secret-never-echo"}):
        response = client.post(f"/submissions/{sid}/recognitions", json=body)
        assert response.status_code == 422
        assert "secret-never-echo" not in response.text
    assert client.get(f"/submissions/{sid}/transcriptions").json() == []
    assert client.post(f"/submissions/{sid}/transcriptions", json={
        "source": "automatic", "reviewer_reference": "test", "segments": [
            {"segment_id": "s:1", "kind": "math", "page_index": 0, "order": 0, "latex": "x=1"}],
    }).status_code == 422
    with pytest.raises(ValidationError):
        ProviderOutput.model_validate({"segments": [{"page_index": 0, "order": 0, "kind": "math"}], "status": "ACCEPTED"})


@pytest.mark.parametrize("artifact", ["snapshot.json", "page_1.png", "receipt.json", "submission.json"])
def test_integrity_required_before_provider_and_on_idempotent_retry(client, monkeypatch, artifact):
    sid = submission(client)
    first = recognize(client, sid, idempotency_key="retry").json()
    path = router.store().root / sid / artifact
    path.write_bytes(path.read_bytes() + b"tampered")
    calls = []
    def forbidden(*args):
        calls.append(True)
        pytest.fail("provider must not run on tampered source")
    monkeypatch.setattr(FakeTestRecognizer, "recognize", forbidden)
    for key in ("retry", "new"):
        assert recognize(client, sid, idempotency_key=key).status_code == 409
    assert calls == []
    runs = client.get(f"/submissions/{sid}/recognitions")
    if artifact in {"receipt.json", "submission.json"}:
        assert runs.status_code == 422  # Persisted provenance must bind to readable metadata.
    else:
        assert runs.status_code == 200 and len(runs.json()) == 1
    assert first["status"] == "NEEDS_REVIEW"


def test_human_revision_acceptance_keeps_automatic_history_and_provenance(client):
    sid = submission(client)
    manual = client.post(f"/submissions/{sid}/transcriptions", json={
        "reviewer_reference": "prof:01", "segments": [{"segment_id": "manual:1", "page_index": 0, "order": 0, "kind": "text", "text": "original"}],
    }).json()
    automatic = recognize(client, sid).json()
    tid = automatic["transcription_id"]
    first = client.get(f"/transcriptions/{tid}").json()["revisions"][0]
    response = client.post(f"/transcriptions/{tid}/revisions", json={
        "based_on_revision_number": 1, "reviewer_reference": "prof:01", "segments": first["segments"],
        "status": "NEEDS_REVIEW", "change_reason": "Conferência humana.",
    })
    assert response.status_code == 201, response.text
    assert response.json()["provenance"] == first["provenance"]
    assert client.post(f"/transcriptions/{tid}/accept", json={"revision_number": 2, "reviewer_reference": "prof:01"}).status_code == 200
    history = client.get(f"/transcriptions/{tid}").json()
    assert [r["status"] for r in history["revisions"]] == ["NEEDS_REVIEW", "ACCEPTED"]
    assert history["revisions"][0] == first
    assert history["acceptances"][0]["mathematical_validity_assessed"] is False
    assert client.get(f'/transcriptions/{manual["transcription_id"]}').json()["revisions"][0]["segments"][0]["text"] == "original"
    assert len(client.get(f"/submissions/{sid}/transcriptions").json()) == 2
    run = client.get(f'/submissions/{sid}/recognitions/{automatic["recognizer_run_id"]}').json()
    assert run["status"] == "NEEDS_REVIEW"  # Immutable recognition event, independent of later human acceptance.


def test_provider_failure_is_persisted_and_safe_retry(tmp_path, caplog):
    class Failing(FakeTestRecognizer):
        calls = 0
        def recognize(self, source):
            self.calls += 1
            raise RuntimeError("credential-secret manuscript-full-payload")
    adapter = Failing()
    service, sid = service_case(tmp_path, adapter)
    request = RecognitionRequest(provider="fake_test", idempotency_key="same")
    first, created = service.recognize(sid, request)
    assert first.status == "FAILED" and first.error_code == "PROVIDER_FAILED" and created
    retry, created = service.recognize(sid, request)
    assert retry == first and not created and adapter.calls == 1
    assert service.store.list_transcriptions(sid) == []
    assert service.get(sid, first.recognizer_run_id) == first
    assert "credential-secret" not in first.model_dump_json() + caplog.text
    service.recognize(sid, RecognitionRequest(provider="fake_test", idempotency_key="another"))
    assert adapter.calls == 2


@pytest.mark.parametrize("bad", ["accepted", "duplicate", "page", "stroke", "region", "confidence"])
def test_invalid_provider_output_never_creates_revision(tmp_path, bad):
    class Invalid(FakeTestRecognizer):
        def recognize(self, source):
            segment = {"page_index": 0, "order": 0, "kind": "math", "latex": "x=1"}
            values = {"segments": [segment]}
            if bad == "accepted": values["status"] = "ACCEPTED"
            if bad == "duplicate": values["segments"].append(dict(segment))
            if bad == "page": segment["page_index"] = 2
            if bad == "stroke": segment["source_stroke_refs"] = ["not:a:stroke"]
            if bad == "region": segment["source_region"] = {"x": 0, "y": 0, "width": 9999, "height": 1}
            if bad == "confidence": segment["confidence"] = float("nan")
            return values
    service, sid = service_case(tmp_path, Invalid())
    run, _ = service.recognize(sid, RecognitionRequest(provider="fake_test"))
    assert run.status == "FAILED" and run.error_code == "INVALID_PROVIDER_OUTPUT"
    assert service.store.list_transcriptions(sid) == []


def test_parallel_idempotency_new_action_and_configuration_conflict(client):
    sid = submission(client)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: recognize(client, sid, idempotency_key="action-1"), range(2)))
    assert sorted(r.status_code for r in responses) == [200, 201]
    assert responses[0].json() == responses[1].json()
    assert len(client.get(f"/submissions/{sid}/transcriptions").json()) == 1
    assert recognize(client, sid, idempotency_key="action-2").json()["recognizer_run_id"] != responses[0].json()["recognizer_run_id"]
    class Updated(FakeTestRecognizer):
        adapter_version = "2.0.0"
    registry = RecognizerRegistry()
    registry.register("fake_test", Updated)
    from confia_lean_auditor.recognition.service import RecognitionConflict
    with pytest.raises(RecognitionConflict):
        RecognitionService(router.store(), registry).recognize(sid, RecognitionRequest(provider="fake_test", idempotency_key="action-1"))


def test_publication_failure_cannot_leave_partial_success(tmp_path, monkeypatch):
    service, sid = service_case(tmp_path, FakeTestRecognizer())
    write = service.store._write
    def fail_run(path, data):
        if path.name == "recognition.json":
            raise OSError("storage unavailable")
        return write(path, data)
    monkeypatch.setattr(service.store, "_write", fail_run)
    with pytest.raises(OSError):
        service.recognize(sid, RecognitionRequest(provider="fake_test", idempotency_key="retry"))
    assert service.list(sid) == [] and service.store.list_transcriptions(sid) == []
    monkeypatch.setattr(service.store, "_write", write)
    assert service.recognize(sid, RecognitionRequest(provider="fake_test", idempotency_key="retry"))[0].status == "NEEDS_REVIEW"


def test_no_network_audit_or_lean_in_recognition_path(client, monkeypatch):
    import confia_lean_auditor.main as main
    from confia_lean_auditor.lean import run_lean
    def forbidden(*args, **kwargs):
        pytest.fail("network/audit/Lean forbidden in recognition")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    for name in ("run_lean", "run_lean_file"):
        if hasattr(run_lean, name): monkeypatch.setattr(run_lean, name, forbidden)
        if hasattr(main, name): monkeypatch.setattr(main, name, forbidden)
    for route in app.routes:
        if getattr(route, "path", "") == "/audit":
            monkeypatch.setattr(route.dependant, "call", forbidden)
    response = recognize(client, submission(client))
    assert response.status_code == 201 and response.json()["status"] == "NEEDS_REVIEW"
    for path in Path("app/confia_lean_auditor/recognition").glob("*.py"):
        source = path.read_text()
        assert "/audit" not in source and "run_lean" not in source


def test_recognition_request_body_limit_and_safe_errors(client):
    sid = submission(client)
    assert client.post(f"/submissions/{sid}/recognitions", content=b"x" * (8 * 1024 * 1024 + 1),
                       headers={"Content-Type": "application/json"}).status_code == 413
    assert client.post(f"/submissions/{sid}/recognitions", content="secret-malformed",
                       headers={"Content-Type": "application/json"}).status_code == 422
    assert client.post(f"/submissions/{sid}/recognitions", content="{}").status_code == 415


@pytest.mark.parametrize("mode", ["strokes", "image", "strokes_and_image"])
def test_input_modes_only_record_used_artifacts_and_preserve_supplied_metadata(tmp_path, mode):
    class Measured(FakeTestRecognizer):
        input_mode = mode
        def recognize(self, source):
            assert {a.filename for a in source.artifacts} == (
                {"snapshot.json"} if mode == "strokes" else {"page_1.png"} if mode == "image" else {"snapshot.json", "page_1.png"})
            return ProviderOutput(provider_version="test-supplied-version", provider_request_id="test-request-01",
                segments=[RecognitionSegment(page_index=0, order=0, kind="math", latex="2 + 2 = 5", confidence=0.75,
                    source_region={"x": 10, "y": 20, "width": 30, "height": 30}, source_stroke_refs=["stroke:1"])])
    service, sid = service_case(tmp_path, Measured())
    run, _ = service.recognize(sid, RecognitionRequest(provider="fake_test"))
    assert run.status == "NEEDS_REVIEW"
    assert run.result.provider_version == "test-supplied-version"
    revision = service.store.transcription_history(run.transcription_id).revisions[0]
    assert revision.segments[0].confidence == 0.75
    assert revision.segments[0].source_stroke_refs == ["stroke:1"]
    assert revision.segments[0].source_region.width == 30


def test_recheck_source_before_publication(tmp_path):
    class MutatesExternally(FakeTestRecognizer):
        def recognize(self, source):
            path = service.store.root / source.submission_id / "snapshot.json"
            path.write_bytes(path.read_bytes() + b"tamper")
            return super().recognize(source)
    service, sid = service_case(tmp_path, MutatesExternally())
    from confia_lean_auditor.submissions.store import SubmissionIntegrityConflict
    with pytest.raises(SubmissionIntegrityConflict):
        service.recognize(sid, RecognitionRequest(provider="fake_test"))
    assert service.list(sid) == [] and service.store.list_transcriptions(sid) == []


def test_publisher_rejects_auto_accepted_and_contract_requires_provenance(tmp_path):
    service, sid = service_case(tmp_path, FakeTestRecognizer())
    run, _ = service.recognize(sid, RecognitionRequest(provider="fake_test"))
    history = service.store.transcription_history(run.transcription_id)
    with service.store._locked(exclusive=True), pytest.raises(ValueError):
        service.store._publish_transcription(history.transcription,
            history.revisions[0].model_copy(update={"status": "ACCEPTED"}), recognition_run=run)
    with pytest.raises(ValidationError):
        RecognitionRun.model_validate({**run.model_dump(), "status": "ACCEPTED"})
    from confia_lean_auditor.submissions.schemas import TranscriptionRecord
    with pytest.raises(ValidationError):
        TranscriptionRecord.model_validate({**history.transcription.model_dump(), "provenance": None})
    assert service.store.transcription_history(run.transcription_id).acceptances == []


def test_api_provider_failure_safe_code_and_no_revision(client, monkeypatch, caplog):
    sid = submission(client)
    def fail(*args):
        raise RuntimeError("credential-secret handwritten-student-payload")
    monkeypatch.setattr(FakeTestRecognizer, "recognize", fail)
    response = recognize(client, sid)
    assert response.status_code == 201
    assert response.json()["status"] == "FAILED" and response.json()["error_code"] == "PROVIDER_FAILED"
    assert response.json()["transcription_id"] is None
    assert "credential-secret" not in response.text + caplog.text
    assert client.get(f"/submissions/{sid}/transcriptions").json() == []


@pytest.mark.parametrize("change", ["input", "output"])
def test_persisted_result_hashes_checked(client, change):
    sid = submission(client)
    run = recognize(client, sid).json()
    path = router.store().root / sid / "transcriptions" / run["transcription_id"] / "recognition.json"
    data = json.loads(path.read_bytes())
    if change == "input":
        data["provenance"]["artifacts"][0]["sha256"] = "0" * 64
    else:
        data["result"]["segments"][0]["latex"] = "tampered"
    path.write_text(json.dumps(data))
    assert client.get(f'/submissions/{sid}/recognitions/{run["recognizer_run_id"]}').status_code == 422
