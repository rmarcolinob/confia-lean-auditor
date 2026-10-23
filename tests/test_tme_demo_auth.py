"""Anonymous TME demo must never authorize a school API or a foreign resource."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

import confia_lean_auditor.main as main
from confia_lean_auditor.auth.dependencies import COOKIE_NAME
from confia_lean_auditor.auth.models import AuthUser, Role
from confia_lean_auditor.auth.store import AuthStore
from confia_lean_auditor.recognition.mathpix_image import MathpixImageProvider
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.submissions.router import store as submission_store
from confia_lean_auditor.submissions.schemas import SubmissionRequest, CreateTranscriptionRequest
from confia_lean_auditor.tme import router
from confia_lean_auditor.tme.auth import DEMO_EVALUATOR_ID, TMEEvaluator, require_tme_evaluator
from test_recognition_preview import PreviewAdapter, preview_body
from test_submission_audits import result
from test_submissions import payload
from test_tme_pilot import create_case, scan_payload


@pytest.fixture
def demo(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "1")
    monkeypatch.setenv("CONFIA_TME_DEMO_NO_AUTH", "1")
    monkeypatch.setenv("CONFIA_ENV", "test")
    monkeypatch.setenv("CONFIA_COOKIE_SECURE", "0")
    for name, folder in (("AUTH", "auth"), ("SUBMISSIONS", "submissions"),
                         ("SUBMISSION_AUDITS", "audits"), ("TME_CASES", "cases"),
                         ("INSTITUTIONAL", "institutional")):
        monkeypatch.setenv(f"CONFIA_{name}_DIR", str(tmp_path / folder))
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", "test-id")
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "test-key")
    registry = RecognizerRegistry()
    registry.register("mathpix", PreviewAdapter)
    registry.register("mathpix_image", lambda: MathpixImageProvider(httpx.MockTransport(
        lambda _: httpx.Response(200, json={"text": "2 + 2 = 5"}))))
    monkeypatch.setattr(router, "configured_registry", lambda: registry)
    monkeypatch.setattr(main, "execute_audit", lambda request: result(request.problem_id))
    with TestClient(main.app, headers={"Origin": "http://testserver"}) as client:
        yield client, tmp_path


@pytest.mark.parametrize("flag", [None, "0", "false"])
def test_tme_without_explicit_demo_flag_requires_session(demo, monkeypatch, flag):
    client, _ = demo
    if flag is None:
        monkeypatch.delenv("CONFIA_TME_DEMO_NO_AUTH")
    else:
        monkeypatch.setenv("CONFIA_TME_DEMO_NO_AUTH", flag)
    assert client.get("/tme").status_code == 401
    assert client.get("/static/tme/index.html").status_code == 401
    assert client.get("/tme/problems").status_code == 401
    assert client.get("/tme/cases").status_code == 401
    assert client.post("/tme/cases", json={"problem_id": "ITA2025F2Q1",
        "external_candidate_ref": "TME-1", "source_mode": "IMAGE_SCAN"}).status_code == 401
    case_path = "/tme/cases/case_" + "a" * 32
    for path in ("capture", "submission", "pages/0", "originals/0", "transcriptions", "audits", "decision", "scan-manifest", "recognition-status"):
        assert client.get(f"{case_path}/{path}").status_code == 401
    for path in ("scan", "digital-submission", "recognize", "recognition-preview", "audits",
                 "transcriptions/trn_example/accept", "transcriptions/trn_example/revisions"):
        assert client.post(f"{case_path}/{path}", json={}).status_code == 401
    # The old global legacy switch alone must not opt TME into anonymous access.
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "0")
    assert client.get("/tme").status_code == 401


@pytest.mark.parametrize("flag", ["1", "true"])
def test_demo_shell_opens_without_login_or_profile_selection(demo, monkeypatch, flag):
    client, _ = demo
    monkeypatch.setenv("CONFIA_TME_DEMO_NO_AUTH", flag)
    response = client.get("/tme", follow_redirects=False)
    assert response.status_code == 200 and "location" not in response.headers
    assert "Confiabilidade e Explicabilidade" in response.text
    assert "PILOTO ConfIA" in response.text
    assert "TME" not in response.text
    assert all(label in response.text for label in ("ConfIA", "Nova correção", "Correções", "Resultados"))
    assert all(label not in response.text for label in ("Aluno", "Professor", "Gestão", "login", "profile-switch"))
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/tme/problems").status_code == 200
    assert client.get("/static/tme/index.html").status_code == 200
    assert not client.cookies


def upload(client, mode):
    case = create_case(client, mode)
    base = f'/tme/cases/{case["case_id"]}'
    if mode == "IMAGE_SCAN":
        response = client.post(f"{base}/scan", json=scan_payload(1))
    else:
        assert client.get(f"{base}/capture").status_code == 200
        preview = client.post(f"{base}/recognition-preview", json=preview_body())
        assert preview.status_code == 200, preview.text
        body = payload()
        body["student_reference"] = None
        response = client.post(f"{base}/digital-submission", json=body)
    assert response.status_code == 201, response.text
    return case, base, response.json()


@pytest.mark.parametrize("mode", ["DIGITAL_INK", "IMAGE_SCAN"])
def test_demo_complete_flow_keeps_server_identity_and_requires_no_school(demo, mode):
    client, root = demo
    case, base, receipt = upload(client, mode)
    assert case["created_by_user_id"] == DEMO_EVALUATOR_ID
    detail = client.get(f"{base}/submission").json()["submission"]
    assert detail["submitted_by_user_id"] == DEMO_EVALUATOR_ID
    assert all(detail.get(field) is None for field in ("tenant_id", "school_id", "classroom_id", "assessment_id"))
    assert client.get(f"{base}/pages/0").status_code == 200
    if mode == "IMAGE_SCAN":
        assert client.get(f"{base}/originals/0").status_code == 200
        assert client.get(f"{base}/capture").status_code == 409
    response = client.post(f"{base}/recognize", json={"idempotency_key": "demo:1"})
    assert response.status_code == 200, response.text
    run = response.json()
    assert run["status"] == "NEEDS_REVIEW"
    assert client.post(f"{base}/recognize", json={"idempotency_key": "demo:1"}).json() == run
    assert client.get(f'{base}/recognitions/{run["recognizer_run_id"]}').status_code == 200
    summaries = client.get(f"{base}/transcriptions").json()
    transcription_path = f'{base}/transcriptions/{run["transcription_id"]}'
    assert summaries[0]["transcription"]["transcription_id"] == run["transcription_id"]
    assert client.get(transcription_path).status_code == 200
    edit = client.post(f"{transcription_path}/revisions", json={
        "based_on_revision_number": 1, "reviewer_reference": "spoofed-participant",
        "segments": [{"segment_id": "reviewed", "page_index": 0, "order": 0,
                      "kind": "text", "text": "2 + 2 = 5"}]})
    assert edit.status_code == 201, edit.text
    assert edit.json()["reviewer_reference"] == DEMO_EVALUATOR_ID
    accepted = client.post(f"{transcription_path}/accept", json={"revision_number": 2,
        "reviewer_reference": "spoofed-participant"})
    assert accepted.status_code == 200, accepted.text
    acceptance = accepted.json()["acceptance"]
    assert acceptance["reviewer_reference"] == DEMO_EVALUATOR_ID
    assert acceptance["reviewer_identity_verified"] is False
    response = client.post(f"{base}/audits", json={"transcription_id": run["transcription_id"],
        "revision_number": 2, "acceptance_id": acceptance["acceptance_id"]})
    assert response.status_code == 200, response.text
    audit = response.json()
    assert audit["status"] == "COMPLETED"
    assert audit["source"]["provenance"]["acceptance"]["reviewer_reference"] == DEMO_EVALUATOR_ID
    assert client.get(f"{base}/audits").json()[0]["audit_run_id"] == audit["audit_run_id"]
    decision = client.post(f"{base}/decision", json={"audit_run_id": audit["audit_run_id"],
        "max_points": 10, "final_points": 0, "feedback": "Conferido pelo avaliador."})
    assert decision.status_code == 201, decision.text
    assert decision.json()["decided_by_user_id"] == DEMO_EVALUATOR_ID
    assert decision.json()["audit_source_sha256"]
    assert client.get(f"{base}/decision").json() == decision.json()
    assert client.get(base).json()["status"] == "DECIDED"
    assert client.get("/tme/cases").json()[0]["case_id"] == case["case_id"]
    assert not (root / "institutional").exists()
    assert not (root / "auth").exists()  # No account, session or school role was manufactured.
    assert client.get(f'/submissions/{receipt["submission_id"]}').status_code == 401


def test_demo_does_not_grant_platform_role_or_open_school_routes(demo):
    client, _ = demo
    principal = require_tme_evaluator(Request({"type": "http", "headers": []}))
    assert isinstance(principal, TMEEvaluator) and not isinstance(principal, AuthUser)
    assert not hasattr(principal, "role") and principal.evaluator_id == DEMO_EVALUATOR_ID
    create_case(client, "IMAGE_SCAN")
    for route in ("/auth/me", "/management/overview", "/management/schools", "/assessments",
                  "/institutional/me/context", "/institutional/me/schools", "/submissions", "/capture",
                  "/submissions/recognition-providers", "/problems",
                  "/submissions/sub_example/teacher-decision", "/transcriptions/trn_example",
                  "/submission-audits/aud_example"):
        assert client.get(route).status_code == 401, route
    for route in ("/assessments", "/submissions", "/submissions/recognition-preview", "/audit",
                  "/submissions/sub_example/transcriptions", "/submissions/sub_example/recognitions",
                  "/submissions/sub_example/audits", "/submissions/sub_example/teacher-decision"):
        assert client.post(route, json={}).status_code == 401, route
    assert "login-form" in client.get("/").text
    assert "login-form" in client.get("/?area=teacher").text
    assert not client.cookies
    # The synthetic id is not a session credential.
    client.cookies.set(COOKIE_NAME, DEMO_EVALUATOR_ID)
    assert client.get("/auth/me").status_code == 401


def test_demo_cannot_read_or_edit_foreign_transcriptions_or_recognitions(demo):
    client, root = demo
    case, base, _ = upload(client, "IMAGE_SCAN")
    other, other_base, other_receipt = upload(client, "IMAGE_SCAN")
    run = client.post(f"{other_base}/recognize", json={}).json()
    tid = run["transcription_id"]
    for suffix in (f'/transcriptions/{tid}', f'/recognitions/{run["recognizer_run_id"]}'):
        assert client.get(base + suffix).status_code == 404
    assert client.post(f"{base}/transcriptions/{tid}/accept", json={"revision_number": 1}).status_code == 404
    assert client.post(f"{base}/transcriptions/{tid}/revisions", json={}).status_code == 404
    acceptance = client.post(f"{other_base}/transcriptions/{tid}/accept", json={"revision_number": 1}).json()["acceptance"]
    request = {"transcription_id": tid, "revision_number": 1, "acceptance_id": acceptance["acceptance_id"]}
    assert client.post(f"{base}/audits", json=request).status_code == 404
    audit = client.post(f"{other_base}/audits", json=request).json()
    own = client.post(f"{base}/recognize", json={}).json()
    assert client.post(f'{base}/transcriptions/{own["transcription_id"]}/accept', json={"revision_number": 1}).status_code == 200
    assert client.post(f"{base}/decision", json={"audit_run_id": audit["audit_run_id"],
        "max_points": 10, "final_points": 0}).status_code == 409
    # Even an on-disk case pointer cannot bridge into a school submission.
    school, _ = submission_store().receive(SubmissionRequest.model_validate(payload()))
    revision = submission_store().create_transcription(school.submission_id,
        CreateTranscriptionRequest(reviewer_reference="school-teacher", segments=[
            {"segment_id": "school", "page_index": 0, "order": 0, "kind": "text", "text": "school content"}]))
    assert client.get(f"{base}/transcriptions/{revision.transcription_id}").status_code == 404
    case_file = root / "cases" / case["case_id"] / "case.json"
    data = json.loads(case_file.read_text())
    data["submission_id"] = school.submission_id
    case_file.write_text(json.dumps(data))
    assert client.get(f"{base}/submission").status_code == 409


def test_authenticated_teacher_identity_wins_and_students_remain_forbidden(demo):
    client, root = demo
    store = AuthStore(root / "auth")
    teacher = store.create_user(login="evaluator", display_name="Avaliador", role=Role.TEACHER,
        password="demo-test-secret", tenant_id="test")
    student = store.create_user(login="participant", display_name="Participante", role=Role.STUDENT,
        password="demo-test-secret", tenant_id="test")
    demo_case = create_case(client, "IMAGE_SCAN")
    client.cookies.set(COOKIE_NAME, store.create_session(teacher.user_id))
    case = create_case(client, "IMAGE_SCAN")
    assert case["created_by_user_id"] == teacher.user_id
    assert client.get(f'/tme/cases/{demo_case["case_id"]}').status_code == 403
    client.cookies.clear()
    assert client.get(f'/tme/cases/{case["case_id"]}').status_code == 403
    assert [c["case_id"] for c in client.get("/tme/cases").json()] == [demo_case["case_id"]]
    client.cookies.set(COOKIE_NAME, store.create_session(student.user_id))
    assert client.get("/tme").status_code == 403
    assert client.get("/tme/cases").status_code == 403


def test_demo_mutations_still_require_same_origin(demo):
    client, _ = demo
    assert client.post("/tme/cases", headers={"Origin": "https://foreign.example"}, json={}).status_code == 403


@pytest.mark.parametrize("environment", ["production", "PRODUCTION"])
def test_production_rejects_demo_at_startup(monkeypatch, environment):
    monkeypatch.setenv("CONFIA_ENV", environment)
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "1")
    monkeypatch.setenv("CONFIA_TME_DEMO_NO_AUTH", "1")
    with pytest.raises(RuntimeError, match="CONFIA_TME_DEMO_NO_AUTH.*forbidden in production"):
        with TestClient(main.app):
            pass


def test_invalid_flag_fails_configuration(monkeypatch):
    monkeypatch.setenv("CONFIA_TME_DEMO_NO_AUTH", "yes")
    with pytest.raises(RuntimeError, match="invalid CONFIA_TME_DEMO_NO_AUTH"):
        with TestClient(main.app):
            pass
