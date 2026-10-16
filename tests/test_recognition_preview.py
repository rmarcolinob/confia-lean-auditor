"""A preview may read a frozen snapshot, but must publish no submission evidence."""
import hashlib
import json

from fastapi.testclient import TestClient
import httpx
import pytest

from confia_lean_auditor.main import app
from confia_lean_auditor.recognition.mathpix import MathpixRecognitionProvider
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.submissions import router
from test_submissions import payload


def preview_body(snapshot_json=None):
    return {"snapshot_json": snapshot_json or payload()["snapshot_json"], "client_preview_id": "preview:test-01"}


class PreviewAdapter:
    provider = "mathpix"
    display_label = "Mathpix"
    adapter = "confia_mathpix_strokes"
    adapter_version = "1.0.0"
    input_mode = "strokes"
    public_parameters = {}

    def __init__(self):
        self.calls = []
        self.fail = False

    def recognize(self, source):
        self.calls.append(source)
        if self.fail:
            raise RuntimeError("credential-secret manuscript-full-payload")
        return {"segments": [{"page_index": 0, "order": 0, "kind": "mixed",
                              "text": "2 + 2 = 5", "latex": "2 + 2 = 5"}]}


@pytest.fixture
def preview_case(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    adapter = PreviewAdapter()
    registry = RecognizerRegistry()
    registry.register("mathpix", lambda: adapter)
    monkeypatch.setattr(router, "configured_registry", lambda: registry)
    return TestClient(app), adapter, tmp_path / "submissions"


def test_preview_uses_exact_frozen_snapshot_without_publishing(preview_case):
    client, adapter, storage = preview_case
    body = preview_body()
    response = client.post("/submissions/recognition-preview", json=body)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["problem_id"] == "ITA2025F2Q1"
    assert result["snapshot_id"] == "snapshot:test-01"
    assert result["client_preview_id"] == body["client_preview_id"]
    assert result["snapshot_sha256"] == hashlib.sha256(body["snapshot_json"].encode()).hexdigest()
    assert result["page_count"] == result["active_stroke_count"] == 1
    assert result["result"]["segments"][0]["latex"] == "2 + 2 = 5"
    assert response.headers["cache-control"] == "no-store"
    assert len(adapter.calls) == 1
    assert adapter.calls[0].artifacts[0].data == body["snapshot_json"].encode()
    assert adapter.calls[0].artifacts[0].filename == "snapshot.json"
    assert not storage.exists()
    assert client.get("/submissions").json() == []


def test_preview_rejects_draft_changed_snapshot_and_bad_mapping(preview_case):
    client, adapter, storage = preview_case
    frozen = json.loads(payload()["snapshot_json"])
    draft = {**frozen, "document_kind": "draft", "local_snapshot_id": None}
    assert client.post("/submissions/recognition-preview", json=preview_body(json.dumps(draft))).status_code == 422
    frozen["active_stroke_ids"] = []
    frozen["operations"] = []
    assert client.post("/submissions/recognition-preview", json=preview_body(json.dumps(frozen))).status_code == 422
    assert adapter.calls == []
    adapter.recognize = lambda source: {"segments": [{"page_index": 2, "order": 0, "kind": "math", "latex": "x"}]}
    assert client.post("/submissions/recognition-preview", json=preview_body()).status_code == 422
    assert not storage.exists()


def test_preview_failure_is_transient_and_sanitized(preview_case):
    client, adapter, storage = preview_case
    adapter.fail = True
    response = client.post("/submissions/recognition-preview", json=preview_body())
    assert response.status_code == 503
    assert response.json() == {"detail": "PROVIDER_FAILED"}
    assert "credential-secret" not in response.text
    assert not storage.exists()


def test_preview_reuses_mathpix_stroke_conversion_and_keeps_credentials_private(preview_case, monkeypatch):
    client, _, storage = preview_case
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", "private-id")
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "private-key")
    requests = []

    def mathpix_response(request):
        requests.append(request)
        return httpx.Response(200, json={"text": "2 + 2 = 5", "latex_styled": "2 + 2 = 5"})

    adapter = MathpixRecognitionProvider(transport=httpx.MockTransport(mathpix_response))
    registry = RecognizerRegistry()
    registry.register("mathpix", lambda: adapter)
    monkeypatch.setattr(router, "configured_registry", lambda: registry)
    response = client.post("/submissions/recognition-preview", json=preview_body())
    assert response.status_code == 200, response.text
    assert response.json()["result"]["segments"][0]["latex"] == "2 + 2 = 5"
    assert len(requests) == 1
    assert json.loads(requests[0].content)["strokes"]["strokes"] == {"x": [[10.0, 40.0]], "y": [[20.0, 50.0]]}
    assert requests[0].headers["app_id"] == "private-id"
    assert "private-id" not in response.text and "private-key" not in response.text
    assert not storage.exists()
