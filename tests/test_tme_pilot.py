"""Dual-input TME pilot without external OCR calls."""
import base64
import json
from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

import confia_lean_auditor.main as main
from confia_lean_auditor.recognition.mathpix_image import MathpixImageProvider, MathpixImageError
from confia_lean_auditor.recognition.registry import RecognitionArtifact, RecognitionInput, RecognizerRegistry, configured_registry
from confia_lean_auditor.tme import router as tme_router
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.auth.store import AuthStore
from confia_lean_auditor.submission_audits import router as audits
from confia_lean_auditor.submissions import router as submissions
from test_submission_audits import result
from test_submissions import payload, png


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_TME_DEMO_NO_AUTH", "1")
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_SUBMISSION_AUDITS_DIR", str(tmp_path / "audits"))
    monkeypatch.setenv("CONFIA_TME_CASES_DIR", str(tmp_path / "cases"))
    calls = []
    def engine(request):
        calls.append(request)
        return result(request.problem_id)
    monkeypatch.setattr(main, "execute_audit", engine)
    return TestClient(main.app), calls, tmp_path


def create_case(client, mode):
    response = client.post("/tme/cases", json={"problem_id": "ITA2025F2Q1",
        "external_candidate_ref": "TME-0001", "source_mode": mode})
    assert response.status_code == 201, response.text
    return response.json()


def test_tme_shell_is_separate_and_minimal(setup):
    client, _, _ = setup
    html = client.get("/tme")
    assert html.status_code == 200
    assert "Confiabilidade e Explicabilidade" in html.text
    assert "TME" not in html.text
    assert all(label in html.text for label in ("Correções", "Nova correção", "Resultados"))
    assert all(label not in html.text for label in ("TutorIA", "Gestão escolar", "Exames escolares"))


def scan_payload(count=2):
    pages = []
    for index in range(count):
        data = png(12, 16, 250 - index)
        pages.append({"original_base64": base64.b64encode(data).decode(),
            "derived_png_base64": base64.b64encode(data).decode(), "original_mime": "image/png",
            "captured_at": datetime.now(timezone.utc).isoformat(), "rotation_degrees": index * 90,
            "derived_width": 12, "derived_height": 16})
    return {"pages": pages}


def test_scan_preserves_originals_derived_and_provenance(setup):
    client, _, root = setup
    case = create_case(client, "IMAGE_SCAN")
    upload = scan_payload()
    response = client.post(f'/tme/cases/{case["case_id"]}/scan', json=upload)
    assert response.status_code == 201, response.text
    receipt = response.json()
    sid = receipt["submission_id"]
    assert receipt["source"] == "image_scan" and receipt["tme_case_id"] == case["case_id"]
    assert receipt["capture_schema_version"] == "tme-scan-1.0"
    assert receipt["scan_originals"][0]["sha256"] == receipt["page_images"][0]["sha256"]
    assert client.get(f'/tme/cases/{case["case_id"]}/originals/0').content == png(12, 16, 250)
    assert client.get(f"/submissions/{sid}").status_code == 200
    snapshot = client.get(f"/submissions/{sid}/snapshot").json()
    assert snapshot["pages"][1]["rotation_degrees"] == 90
    assert snapshot["pages"][1]["transformation"] == "canvas-orient-and-normalize-png-v1"
    assert (root / "submissions" / sid / "original_1.bin").read_bytes() == png(12, 16, 250)
    assert client.post(f'/tme/cases/{case["case_id"]}/scan', json=upload).status_code == 409
    premature = client.post(f'/tme/cases/{case["case_id"]}/decision', json={
        "max_points": 10, "final_points": 5})
    assert premature.status_code == 409


def test_historical_submission_without_tme_fields_remains_readable(setup):
    client, _, root = setup
    sid = client.post("/submissions", json=payload()).json()["submission_id"]
    for name in ("submission.json", "receipt.json"):
        path = root / "submissions" / sid / name
        data = json.loads(path.read_text())
        data.pop("tme_case_id", None)
        data.pop("scan_originals", None)
        path.write_text(json.dumps(data))
    assert submissions.store().assert_submission_integrity(sid).source == "tablet"


def test_dual_input_accepted_text_uses_one_audit_service(setup):
    client, calls, _ = setup
    ink = create_case(client, "DIGITAL_INK")
    body = payload()
    body["student_reference"] = None
    digital = client.post(f'/tme/cases/{ink["case_id"]}/digital-submission', json=body)
    assert digital.status_code == 201, digital.text
    scan = create_case(client, "IMAGE_SCAN")
    photo = client.post(f'/tme/cases/{scan["case_id"]}/scan', json=scan_payload(1))
    assert photo.status_code == 201, photo.text
    run_ids = []
    for sid in (digital.json()["submission_id"], photo.json()["submission_id"]):
        revision = client.post(f"/submissions/{sid}/transcriptions", json={
            "reviewer_reference": "avaliador-tme", "segments": [{"segment_id": "same", "page_index": 0,
            "order": 0, "kind": "text", "text": "2 + 2 = 5"}]}).json()
        assert revision["revision_number"] == 1
        acceptance = client.post(f'/transcriptions/{revision["transcription_id"]}/accept', json={
            "revision_number": 1, "reviewer_reference": "avaliador-tme"}).json()["acceptance"]
        audit = client.post(f"/submissions/{sid}/audits", json={
            "transcription_id": revision["transcription_id"], "revision_number": 1,
            "acceptance_id": acceptance["acceptance_id"]})
        assert audit.status_code == 200, audit.text
        assert audit.json()["status"] == "COMPLETED"
        assert audit.json()["source"]["solution_text"] == "2 + 2 = 5"
        run_ids.append(audit.json()["audit_run_id"])
    assert [call.solution for call in calls] == ["2 + 2 = 5", "2 + 2 = 5"]
    chosen = client.post(f'/tme/cases/{scan["case_id"]}/decision', json={
        "audit_run_id": run_ids[1], "max_points": 10, "final_points": 5,
        "feedback": "Revisar cálculo."})
    assert chosen.status_code == 422  # A different human score needs a reason.
    chosen = client.post(f'/tme/cases/{scan["case_id"]}/decision', json={
        "audit_run_id": run_ids[1], "max_points": 10, "final_points": 5,
        "feedback": "Revisar cálculo.", "override_reason": "Passo parcial válido."})
    assert chosen.status_code == 201, chosen.text
    assert chosen.json()["suggested_points"] == "0.00"
    assert client.get(f'/tme/cases/{scan["case_id"]}').json()["status"] == "DECIDED"


def image_source(count=1):
    return RecognitionInput("sub_" + "a" * 32,
        tuple(RecognitionArtifact(f"page_{i + 1}.png", i, "a" * 64, png(12, 16, 250 - i)) for i in range(count)))


def provider(monkeypatch, handler):
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", "private-app-id")
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "private-app-key")
    return MathpixImageProvider(httpx.MockTransport(handler))


def test_image_registry_credentials(monkeypatch):
    monkeypatch.setenv("CONFIA_ENV", "production")
    monkeypatch.delenv("CONFIA_MATHPIX_APP_ID", raising=False)
    monkeypatch.delenv("CONFIA_MATHPIX_APP_KEY", raising=False)
    assert "mathpix_image" not in configured_registry().providers()
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", "id")
    assert "mathpix_image" not in configured_registry().providers()
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "key")
    assert "mathpix_image" in configured_registry().providers()


def test_image_provider_multipart_pages_and_single_document(monkeypatch):
    calls = []
    def handler(request):
        calls.append(request)
        assert request.url.path == "/v3/text"
        assert request.headers["app_id"] == "private-app-id"
        assert b'name="file"' in request.content and b'name="options_json"' in request.content
        assert b'"enable_document_layout":true' in request.content
        assert b'"improve_mathpix":false' in request.content
        return httpx.Response(200, json={"text": f"Página {len(calls)} \\(x^2\\)",
                                        "latex_styled": "x^2", "version": "v1"})
    output = provider(monkeypatch, handler).recognize(image_source(2))
    assert [s.page_index for s in output.segments] == [0, 1]
    assert [s.latex for s in output.segments] == [None, None]
    assert len(calls) == 2


def test_image_provider_accepts_jpeg_and_rejects_empty_page(monkeypatch):
    requests = []
    adapter = provider(monkeypatch, lambda request: (requests.append(request) or
        httpx.Response(200, json={"text": "x = 1"})))
    jpeg = RecognitionInput("sub_" + "a" * 32,
        (RecognitionArtifact("page_1.jpg", 0, "a" * 64, b"\xff\xd8\xffmock-jpeg"),))
    assert adapter.recognize(jpeg).segments[0].text == "x = 1"
    assert b"image/jpeg" in requests[0].content
    empty = RecognitionInput("sub_" + "a" * 32,
        (RecognitionArtifact("page_1.png", 0, "a" * 64, b""),))
    with pytest.raises(MathpixImageError, match="invalid_input"):
        adapter.recognize(empty)


@pytest.mark.parametrize("body,expected", [({"latex_styled": "x^2"}, "math"),
    ({"text": "Solução", "latex_styled": "x^2"}, "text")])
def test_image_provider_text_and_latex_fallback(monkeypatch, body, expected):
    output = provider(monkeypatch, lambda _: httpx.Response(200, json=body)).recognize(image_source())
    assert output.segments[0].kind == expected
    assert bool(output.segments[0].latex) != bool(output.segments[0].text)


@pytest.mark.parametrize("status,category", [(401, "http_401"), (429, "http_429"), (503, "http_5xx")])
def test_image_provider_http_failure_keeps_safe_category(monkeypatch, status, category):
    adapter = provider(monkeypatch, lambda _: httpx.Response(status, text="private-app-key"))
    with pytest.raises(MathpixImageError, match=category) as raised:
        adapter.recognize(image_source())
    assert "private-app-key" not in str(raised.value)


@pytest.mark.parametrize("response", [httpx.Response(200, text="bad json"), httpx.Response(200, json={}),
    httpx.Response(200, json={"text": "private-app-key"})])
def test_image_provider_invalid_response(monkeypatch, response):
    adapter = provider(monkeypatch, lambda _: response)
    with pytest.raises(MathpixImageError):
        adapter.recognize(image_source())


def test_image_provider_empty_or_timeout(monkeypatch):
    adapter = provider(monkeypatch, lambda _: httpx.Response(200, json={"text": "ok"}))
    with pytest.raises(MathpixImageError, match="invalid_input"):
        adapter.recognize(RecognitionInput("sub_" + "a" * 32, ()))
    timeout = provider(monkeypatch, lambda _: (_ for _ in ()).throw(httpx.ReadTimeout("timeout")))
    with pytest.raises(TimeoutError):
        timeout.recognize(image_source())


def test_scan_ocr_failure_preserves_pages_and_retry_publishes_revision(setup, monkeypatch):
    client, _, root = setup
    case = create_case(client, "IMAGE_SCAN")
    sid = client.post(f'/tme/cases/{case["case_id"]}/scan', json=scan_payload(2)).json()["submission_id"]
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", "id")
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "key")
    calls = []
    def handler(_):
        calls.append(1)
        return httpx.Response(503) if len(calls) == 1 else httpx.Response(200, json={"text": "x + 1 = 2"})
    registry = RecognizerRegistry()
    registry.register("mathpix_image", lambda: MathpixImageProvider(httpx.MockTransport(handler)))
    monkeypatch.setattr(tme_router, "configured_registry", lambda: registry)
    failed = client.post(f'/tme/cases/{case["case_id"]}/recognize', json={})
    assert failed.status_code == 200 and failed.json()["status"] == "FAILED"
    assert (root / "submissions" / sid / "original_1.bin").exists()
    retry = client.post(f'/tme/cases/{case["case_id"]}/recognize', json={})
    assert retry.status_code == 200 and retry.json()["status"] == "NEEDS_REVIEW"
    summary = client.get(f"/submissions/{sid}/transcriptions").json()
    assert [s["page_index"] for s in summary[0]["latest_revision"]["segments"]] == [0, 1]
    assert len(calls) == 3


def test_tme_teacher_ownership_and_no_student_access(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "1")
    monkeypatch.setenv("CONFIA_COOKIE_SECURE", "0")
    monkeypatch.setenv("CONFIA_ENV", "test")
    monkeypatch.setenv("CONFIA_AUTH_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("CONFIA_TME_CASES_DIR", str(tmp_path / "cases"))
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    auth = AuthStore(tmp_path / "auth")
    for login, role in (("teacher.one", Role.TEACHER), ("teacher.two", Role.TEACHER), ("student.one", Role.STUDENT)):
        auth.create_user(login=login, display_name=login, role=role, password="pilot-test-secret", tenant_id="test")
    def signed(login):
        session = TestClient(main.app, headers={"Origin": "http://testserver"})
        assert session.post("/auth/login", json={"login": login, "password": "pilot-test-secret"}).status_code == 200
        return session
    teacher = signed("teacher.one")
    other = signed("teacher.two")
    student = signed("student.one")
    assert student.get("/tme").status_code == 403
    case = create_case(teacher, "IMAGE_SCAN")
    assert teacher.get(f'/tme/cases/{case["case_id"]}').status_code == 200
    assert other.get(f'/tme/cases/{case["case_id"]}').status_code == 403
    receipt = teacher.post(f'/tme/cases/{case["case_id"]}/scan', json=scan_payload(1)).json()
    assert teacher.get(f'/submissions/{receipt["submission_id"]}').status_code == 200
    assert other.get(f'/tme/cases/{case["case_id"]}/originals/0').status_code == 403
