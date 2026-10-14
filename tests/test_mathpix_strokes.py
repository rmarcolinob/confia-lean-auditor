"""Mathpix adapter tests use only MockTransport; no external API or key fixture."""
import copy
import json
import logging
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from confia_lean_auditor.main import app
from confia_lean_auditor.recognition.execution import ProviderDeadline
from confia_lean_auditor.recognition.mathpix import MathpixRecognitionProvider, MathpixProviderError, page_payload
from confia_lean_auditor.recognition.registry import RecognitionArtifact, RecognitionInput, RecognizerRegistry, configured_registry
from confia_lean_auditor.recognition.schemas import ProviderOutput, RecognitionRequest
from confia_lean_auditor.recognition.service import RecognitionService
from confia_lean_auditor.recognition.validation import canonical_hash
from confia_lean_auditor.submissions import router
from confia_lean_auditor.submissions.schemas import CaptureSnapshot, SubmissionRequest
from confia_lean_auditor.submissions.store import SubmissionStore
from test_capture_contracts import valid_document
from test_submissions import payload as submission_payload

APP_ID = "SUPER_SECRET_APP_ID"
APP_KEY = "SUPER_SECRET_APP_KEY"


def snapshot(pages=1):
    data = valid_document()
    data.update(document_kind="local_snapshot", local_snapshot_id="snapshot:test")
    for index in range(1, pages):
        page = copy.deepcopy(data["pages"][0])
        page.update(page_id=f"page:{index + 1}", index=index)
        data["pages"].append(page)
        stroke = copy.deepcopy(data["strokes"][0])
        stroke.update(stroke_id=f"stroke:{index + 1}", page_id=page["page_id"])
        data["strokes"].append(stroke)
        operation = copy.deepcopy(data["operations"][0])
        operation.update(operation_id=f"operation:add-{index + 1}", stroke_id=stroke["stroke_id"])
        data["operations"].append(operation)
        data["active_stroke_ids"].append(stroke["stroke_id"])
    return CaptureSnapshot.model_validate(data)


def source(document):
    return RecognitionInput("sub_" + "a" * 32, (RecognitionArtifact("snapshot.json", None, "a" * 64,
                             document.model_dump_json().encode()),), ProviderDeadline.start(5))


def provider(monkeypatch, handler):
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", APP_ID)
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", APP_KEY)
    return MathpixRecognitionProvider(httpx.MockTransport(handler))


def test_payload_preserves_order_page_and_active_state():
    data = snapshot(2).model_dump(mode="json")
    data["strokes"].append({**copy.deepcopy(data["strokes"][0]), "stroke_id": "stroke:deleted"})
    # Deleted stroke has no add operation, so the existing graph stays valid.
    document = CaptureSnapshot.model_validate(data)
    first, stroke_count, point_count = page_payload(document, 0)
    second, _, _ = page_payload(document, 1)
    assert first == {"strokes": {"strokes": {"x": [[10.0, 40.0]], "y": [[20.0, 50.0]]}},
                     "metadata": {"improve_mathpix": False}}
    assert second["strokes"]["strokes"]["x"] == [[10.0, 40.0]]
    assert (stroke_count, point_count) == (1, 2)
    assert "pressure_reported" not in json.dumps(first)
    assert "t_ms" not in json.dumps(first)


def test_payload_uses_capture_stroke_order_not_active_id_order():
    data = snapshot().model_dump(mode="json")
    second = copy.deepcopy(data["strokes"][0])
    second["stroke_id"] = "stroke:2"
    second["points"] = [{"x": 100, "y": 110, "t_ms": 0}, {"x": 200, "y": 210, "t_ms": 1}]
    data["strokes"].append(second)
    operation = copy.deepcopy(data["operations"][0])
    operation.update(operation_id="operation:add-2", stroke_id="stroke:2")
    data["operations"].append(operation)
    data["active_stroke_ids"] = ["stroke:2", "stroke:1"]
    converted, _, _ = page_payload(CaptureSnapshot.model_validate(data), 0)
    assert converted["strokes"]["strokes"]["x"] == [[10.0, 40.0], [100.0, 200.0]]


@pytest.mark.parametrize("coordinate", [float("nan"), float("inf"), -1, 1201])
def test_invalid_coordinates_are_rejected(coordinate):
    data = snapshot().model_dump(mode="json")
    data["strokes"][0]["points"][0]["x"] = coordinate
    with pytest.raises(ValidationError):
        CaptureSnapshot.model_validate(data)


def test_empty_page_is_skipped_and_all_empty_fails(monkeypatch):
    data = snapshot(2).model_dump(mode="json")
    data["pages"].append({**data["pages"][-1], "page_id": "page:3", "index": 2})
    document = CaptureSnapshot.model_validate(data)
    assert page_payload(document, 2) is None
    calls = []
    adapter = provider(monkeypatch, lambda request: (calls.append(request) or httpx.Response(200, json={"text": "2 + 2 = 5"})))
    assert len(adapter.recognize(source(document)).segments) == 2
    assert len(calls) == 2
    blank = snapshot().model_dump(mode="json")
    blank.update(strokes=[], operations=[], active_stroke_ids=[])
    with pytest.raises(MathpixProviderError, match="empty_ink"):
        adapter.recognize(source(CaptureSnapshot.model_validate(blank)))


def test_multipage_segments_keep_page_order_and_distinct_requests(monkeypatch):
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={"text": f"Página {len(calls)}", "version": "SuperNet-200"})
    result = provider(monkeypatch, handler).recognize(source(snapshot(3)))
    assert [segment.page_index for segment in result.segments] == [0, 1, 2]
    assert [segment.text for segment in result.segments] == ["Página 1", "Página 2", "Página 3"]
    assert len(calls) == 3 and all(len(call["strokes"]["strokes"]["x"]) == 1 for call in calls)
    assert result.provider_version == "SuperNet-200"
    assert result.provider_request_id is None


def test_request_size_limit_prevents_external_call(monkeypatch):
    data = snapshot().model_dump(mode="json")
    many = copy.deepcopy(data["strokes"][0])
    many["points"] = [{"x": 1111.123456, "y": 1111.123456, "t_ms": i} for i in range(20_000)]
    data["strokes"][0] = many
    for i in range(1, 3):
        stroke = copy.deepcopy(many)
        stroke["stroke_id"] = f"stroke:{i + 1}"
        data["strokes"].append(stroke)
        operation = copy.deepcopy(data["operations"][0])
        operation.update(operation_id=f"operation:add-{i + 1}", stroke_id=stroke["stroke_id"])
        data["operations"].append(operation)
        data["active_stroke_ids"].append(stroke["stroke_id"])
    document = CaptureSnapshot.model_validate(data)
    with pytest.raises(MathpixProviderError, match="request_too_large"):
        page_payload(document, 0)


@pytest.mark.parametrize("body,expected", [
    ({"text": "2 + 2 = 5", "latex_styled": "2 + 2 = 5", "confidence": .75,
      "is_handwritten": True, "version": "SuperNet-200", "request_id": "req-1"}, "mixed"),
    ({"text": "Como x² = 4, temos x = 2."}, "text"),
    ({"latex_styled": "x^2+2x+1"}, "math"),
])
def test_success_preserves_recognized_content_and_optional_metadata(monkeypatch, body, expected):
    def handler(request):
        assert request.url.path == "/v3/strokes"
        assert request.headers["app_id"] == APP_ID and request.headers["app_key"] == APP_KEY
        assert json.loads(request.content)["strokes"]["strokes"]["x"] == [[10.0, 40.0]]
        return httpx.Response(200, json=body)
    result = provider(monkeypatch, handler).recognize(source(snapshot()))
    segment = result.segments[0]
    assert segment.kind == expected
    assert segment.text == body.get("text")
    assert segment.latex == body.get("latex_styled")
    assert segment.confidence == body.get("confidence")
    assert segment.source_stroke_refs is segment.source_region is None
    assert result.provider_version == body.get("version")
    assert result.provider_request_id == body.get("request_id")
    assert result.page_metadata[0].is_handwritten == body.get("is_handwritten")
    assert result.page_metadata[0].provider_version == body.get("version")


@pytest.mark.parametrize("response,category", [
    (httpx.Response(401, text=APP_KEY), "http_4xx"),
    (httpx.Response(429, text="rate limited"), "http_4xx"),
    (httpx.Response(500, text="server error"), "http_5xx"),
    (httpx.Response(200, content=b"not json"), "invalid_json"),
    (httpx.Response(200, json={"confidence": .9}), "incomplete_response"),
    (httpx.Response(200, content=b"a" * (256 * 1024 + 1)), "response_too_large"),
])
def test_http_and_response_failures_are_safe(monkeypatch, response, category, caplog):
    adapter = provider(monkeypatch, lambda _: response)
    with caplog.at_level(logging.INFO), pytest.raises(MathpixProviderError, match=category):
        adapter.recognize(source(snapshot()))
    assert APP_ID not in caplog.text and APP_KEY not in caplog.text
    assert category in caplog.records[-1].failure_category


def test_timeout_missing_credentials_and_echoed_secret(monkeypatch, caplog):
    adapter = provider(monkeypatch, lambda _: (_ for _ in ()).throw(httpx.ReadTimeout("sensitive")))
    with pytest.raises(TimeoutError):
        adapter.recognize(source(snapshot()))
    monkeypatch.delenv("CONFIA_MATHPIX_APP_KEY")
    assert "mathpix" not in configured_registry().providers()
    with pytest.raises(MathpixProviderError, match="not_configured"):
        adapter.recognize(source(snapshot()))
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", APP_KEY)
    echo = provider(monkeypatch, lambda _: httpx.Response(200, json={"text": APP_KEY}))
    with caplog.at_level(logging.INFO), pytest.raises(MathpixProviderError, match="unsafe_response") as exc:
        echo.recognize(source(snapshot()))
    assert APP_ID not in caplog.text and APP_KEY not in caplog.text
    assert APP_ID not in str(exc.value) and APP_KEY not in str(exc.value)


def test_service_replay_retry_review_and_no_audit_or_lean(tmp_path, monkeypatch):
    import confia_lean_auditor.main as main
    monkeypatch.setattr(main, "execute_audit", lambda *_: pytest.fail("recognition called Audit"))
    calls = []
    answers = [httpx.Response(500), httpx.Response(200, json={"text": "2 + 2 = 5", "confidence": .8})]
    adapter = provider(monkeypatch, lambda _: (calls.append(1) or answers.pop(0)))
    store = SubmissionStore(tmp_path / "submissions")
    sid = store.receive(SubmissionRequest.model_validate(submission_payload()))[0].submission_id
    registry = RecognizerRegistry()
    registry.register("mathpix", lambda: adapter)
    service = RecognitionService(store, registry)
    failed, created = service.recognize(sid, RecognitionRequest(provider="mathpix", idempotency_key="one"))
    assert created and failed.status == "FAILED" and failed.error_code == "PROVIDER_FAILED"
    assert service.recognize(sid, RecognitionRequest(provider="mathpix", idempotency_key="one"))[1] is False
    assert len(calls) == 1
    run, created = service.recognize(sid, RecognitionRequest(provider="mathpix", idempotency_key="two"))
    assert created and run.status == "NEEDS_REVIEW" and len(calls) == 2
    assert run.result.segments[0].text == "2 + 2 = 5"
    assert run.provenance.input_mode == "strokes"
    assert run.provenance.snapshot_id == "snapshot:test-01"
    assert run.provenance.parameters["provider_endpoint"] == "v3/strokes"
    assert len(run.provenance.artifacts) == 1 and run.provenance.artifacts[0].filename == "snapshot.json"
    history = store.transcription_history(run.transcription_id)
    assert history.revisions[0].status == "NEEDS_REVIEW"
    assert service.recognize(sid, RecognitionRequest(provider="mathpix", idempotency_key="two"))[1] is False
    assert len(calls) == 2
    for file in (tmp_path / "submissions").rglob("*.json"):
        assert APP_ID not in file.read_text() and APP_KEY not in file.read_text()
    assert not list((tmp_path / "submissions").rglob("audit*.json"))
    assert not list((tmp_path / "submissions").rglob("*.lean"))


def test_api_is_safe_and_never_accepts(monkeypatch, tmp_path):
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    adapter = provider(monkeypatch, lambda _: httpx.Response(200, json={"text": "2 + 2 = 5"}))
    registry = RecognizerRegistry()
    registry.register("mathpix", lambda: adapter)
    monkeypatch.setattr(router, "configured_registry", lambda: registry)
    client = TestClient(app)
    sid = client.post("/submissions", json=submission_payload()).json()["submission_id"]
    summary = client.post(f"/submissions/{sid}/recognitions", json={"provider": "mathpix", "idempotency_key": "ui"})
    assert summary.status_code == 201 and summary.json()["status"] == "NEEDS_REVIEW"
    run = client.get(f'/submissions/{sid}/recognitions/{summary.json()["recognizer_run_id"]}')
    revision = client.get(f'/transcriptions/{summary.json()["transcription_id"]}')
    for response in (summary, run, revision):
        assert APP_ID not in response.text and APP_KEY not in response.text
        assert "ACCEPTED" not in response.text
    for filename in ("tablet.html", "tablet.js"):
        ui = (Path(__file__).parents[1] / "app/confia_lean_auditor/static/capture" / filename).read_text()
        assert APP_ID not in ui and APP_KEY not in ui


@pytest.mark.parametrize("change", ["remove", "provider_version", "page_index"])
def test_new_mathpix_metadata_is_persisted_and_hash_bound_after_restart(tmp_path, monkeypatch, change):
    calls = []
    def handler(_):
        calls.append(1)
        return httpx.Response(200, json={
            "text": "2 + 2 = 5", "latex_styled": "2 + 2 = 5", "confidence": 0.8,
            "is_handwritten": True, "version": "SuperNet-200", "request_id": f"req-{len(calls)}",
        })
    adapter = provider(monkeypatch, handler)
    store = SubmissionStore(tmp_path / "submissions")
    request = submission_payload(2)
    request["snapshot_json"] = snapshot(2).model_dump_json()
    sid = store.receive(SubmissionRequest.model_validate(request))[0].submission_id
    registry = RecognizerRegistry()
    registry.register("mathpix", lambda: adapter)
    service = RecognitionService(store, registry)
    run, created = service.recognize(sid, RecognitionRequest(provider="mathpix", idempotency_key="new-output"))
    assert created and run.status == "NEEDS_REVIEW" and len(calls) == 2
    path = store.root / sid / "transcriptions" / run.transcription_id / "recognition.json"
    data = json.loads(path.read_bytes())
    assert [item["page_index"] for item in data["result"]["page_metadata"]] == [0, 1]
    persisted_output = {name: data["result"][name] for name in ProviderOutput.model_fields}
    assert data["result"]["output_hash"] == canonical_hash(persisted_output)
    restarted = RecognitionService(SubmissionStore(store.root), registry)
    assert restarted.get(sid, run.recognizer_run_id).result.page_metadata == run.result.page_metadata
    if change == "remove":
        data["result"].pop("page_metadata")
    elif change == "provider_version":
        data["result"]["page_metadata"][0]["provider_version"] = "changed-version"
    else:
        metadata = data["result"]["page_metadata"]
        metadata[0]["page_index"], metadata[1]["page_index"] = metadata[1]["page_index"], metadata[0]["page_index"]
    path.write_text(json.dumps(data, ensure_ascii=False))
    with pytest.raises(ValueError, match="recognition output hash mismatch"):
        restarted.get(sid, run.recognizer_run_id)
