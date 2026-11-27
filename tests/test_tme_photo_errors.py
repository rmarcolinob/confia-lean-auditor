"""Photo failures remain actionable without disclosing provider data or losing originals."""
from pathlib import Path

import httpx
import pytest

from confia_lean_auditor.recognition.mathpix_image import MathpixImageProvider
from confia_lean_auditor.recognition.registry import RecognizerRegistry, configured_registry
from confia_lean_auditor.tme import router
from test_tme_demo_auth import demo, upload


def registry_with(monkeypatch, handler):
    registry = RecognizerRegistry()
    registry.register("mathpix_image", lambda: MathpixImageProvider(httpx.MockTransport(handler)))
    monkeypatch.setattr(router, "configured_registry", lambda: registry)


def test_unconfigured_photo_provider_has_safe_503_and_preserved_source(demo, monkeypatch):
    client, root = demo
    _, base, receipt = upload(client, "IMAGE_SCAN")
    monkeypatch.delenv("CONFIA_MATHPIX_APP_KEY")
    monkeypatch.setattr(router, "configured_registry", configured_registry)
    response = client.post(f"{base}/recognize", json={})
    assert response.status_code == 503
    assert response.json()["error_code"] == "PROVIDER_NOT_CONFIGURED"
    assert "Reconhecimento por foto indisponível neste ambiente." in response.json()["detail"]
    assert client.get(f"{base}/recognition-status").json()["state"] == "FAILED"
    assert client.get(f"{base}/originals/0").status_code == 200
    assert not list((root / "submissions" / receipt["submission_id"]).glob("recognitions/*.json"))
    # Supplying both backend credentials registers the real adapter, not a fake fallback.
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "test-key")
    assert isinstance(configured_registry().create("mathpix_image"), MathpixImageProvider)


@pytest.mark.parametrize("status,body,code", [
    (401, {"error": "test-key secret-manuscript"}, "PROVIDER_UNAUTHORIZED"),
    (403, {}, "PROVIDER_FORBIDDEN"),
    (429, {}, "PROVIDER_RATE_LIMITED"),
    (503, {}, "PROVIDER_UNAVAILABLE"),
    (400, {}, "PROVIDER_REJECTED"),
    (200, {"error_info": {"id": "image_decode_error", "message": "secret-manuscript"}}, "INVALID_IMAGE"),
    (200, {"error_info": {"id": "image_no_content"}}, "INVALID_IMAGE"),
    (200, {"error_info": {"id": "http_unauthorized"}}, "PROVIDER_UNAUTHORIZED"),
    (200, {"error_info": {"id": "http_max_requests"}}, "PROVIDER_RATE_LIMITED"),
    (200, {}, "INVALID_PROVIDER_RESPONSE"),
    (200, {"text": "test-key"}, "INVALID_PROVIDER_RESPONSE"),
    (200, {"text": "x" * 20_001}, "INVALID_PROVIDER_OUTPUT"),
])
def test_photo_error_codes_round_trip_through_run_and_safe_status(demo, monkeypatch, status, body, code):
    client, root = demo
    _, base, receipt = upload(client, "IMAGE_SCAN")
    folder = root / "submissions" / receipt["submission_id"]
    before = {p.name: p.read_bytes() for p in folder.iterdir() if p.is_file()}
    registry_with(monkeypatch, lambda _: httpx.Response(status, json=body))
    response = client.post(f"{base}/recognize", json={})
    assert response.status_code == 200, response.text
    run = response.json()
    assert run["status"] == "FAILED" and run["error_code"] == code
    feedback = client.get(f"{base}/recognition-status")
    assert feedback.json()["error_code"] == code
    assert feedback.json()["state"] == "FAILED"
    assert "preservadas" in feedback.json()["message"]
    assert "test-key" not in response.text + feedback.text
    assert "secret-manuscript" not in response.text + feedback.text
    assert client.get(f"{base}/transcriptions").json() == []
    assert {name: (folder / name).read_bytes() for name in before} == before
    assert client.get(f'{base}/recognitions/{run["recognizer_run_id"]}').json()["error_code"] == code
    assert client.get(f"{base}/originals/0").content == before["original_1.bin"]


@pytest.mark.parametrize("failure,code", [
    (httpx.ReadTimeout("test-key"), "PROVIDER_TIMEOUT"),
    (httpx.ConnectError("test-key"), "PROVIDER_TRANSPORT_ERROR"),
])
def test_photo_transport_failure_and_retry(demo, monkeypatch, failure, code):
    client, _ = demo
    _, base, _ = upload(client, "IMAGE_SCAN")
    assert client.get(f"{base}/recognition-status").json()["state"] == "WAITING"
    original = client.get(f"{base}/originals/0").content
    def fail(_):
        raise failure
    registry_with(monkeypatch, fail)
    failed = client.post(f"{base}/recognize", json={}).json()
    assert failed["error_code"] == code
    registry_with(monkeypatch, lambda _: httpx.Response(200, json={"text": "2 + 2 = 5", "latex_styled": "2+2=5"}))
    succeeded = client.post(f"{base}/recognize", json={}).json()
    assert succeeded["status"] == "NEEDS_REVIEW"
    assert succeeded["recognizer_run_id"] != failed["recognizer_run_id"]
    assert client.get(f"{base}/recognition-status").json()["state"] == "RECOGNIZED"
    assert client.get(f"{base}/originals/0").content == original
    summary = client.get(f"{base}/transcriptions").json()[0]
    assert summary["latest_revision"]["segments"][0]["text"] == "2 + 2 = 5"
    assert summary["latest_revision"]["segments"][0]["latex"] is None
    tid = succeeded["transcription_id"]
    assert client.post(f"{base}/transcriptions/{tid}/accept", json={"revision_number": 1}).status_code == 200


def test_saved_scan_manifest_keeps_orientation_order_and_timestamp(demo):
    client, _ = demo
    _, base, _ = upload(client, "IMAGE_SCAN")
    manifest = client.get(f"{base}/scan-manifest")
    assert manifest.status_code == 200
    page = manifest.json()["pages"][0]
    assert page["index"] == 0 and page["original_mime"] == "image/png"
    assert page["captured_at"] and page["rotation_degrees"] == 0


def test_pilot_reuses_shared_palette_and_visible_branding(demo):
    client, _ = demo
    html = client.get("/tme").text
    assert '/static/design-system.css' in html
    assert all(label in html for label in ("ConfIA", "Confiabilidade e Explicabilidade", "PILOTO ConfIA"))
    assert "TME" not in html
    static = Path(router.__file__).parents[1] / "static"
    css = (static / "tme/tme.css").read_text()
    assert "var(--color-primary)" in css and "var(--color-primary-strong)" in css
    assert "var(--color-surface)" in css
    # HOME-04 keeps compact workspace styles intact; Home reuses the shared
    # 44px control token through its existing TME token namespace.
    home_css = (static / "tme/home.css").read_text()
    assert "var(--control-height)" in (static / "tme/tme-theme.css").read_text()
    assert "min-height: var(--confia-control-height)" in home_css
    assert "--control-height: 44px" in (static / "design-system.css").read_text()
    assert not __import__('re').search(r"#[0-9a-fA-F]{3,8}\b", css)
