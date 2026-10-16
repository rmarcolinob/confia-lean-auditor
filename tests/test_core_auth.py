"""CORE-AUTH-01: local sessions, role boundaries and HMER ownership."""
import json
from pathlib import Path
import runpy

from fastapi.testclient import TestClient
import pytest

import confia_lean_auditor.main as main
from confia_lean_auditor.auth.dependencies import COOKIE_NAME
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.auth.store import AuthStore
from confia_lean_auditor.recognition.fake import FakeTestRecognizer
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.submissions import router as submissions_router
from confia_lean_auditor.submissions.schemas import SubmissionRequest
from confia_lean_auditor.submissions.store import SubmissionStore
from test_submissions import payload
from test_submission_audits import result
from test_recognition_preview import PreviewAdapter

ORIGIN = "http://testserver"
PASSWORD = "example-secret-for-tests"


@pytest.fixture
def auth_case(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "1")
    monkeypatch.setenv("CONFIA_COOKIE_SECURE", "0")
    monkeypatch.setenv("CONFIA_ENV", "test")
    monkeypatch.setenv("CONFIA_AUTH_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_SUBMISSION_AUDITS_DIR", str(tmp_path / "audits"))
    store = AuthStore(tmp_path / "auth")
    users = {
        "student_a": store.create_user(login="student.a", display_name="Aluno A", role=Role.STUDENT,
                                       password=PASSWORD, tenant_id="school-a", classroom_ids=["class-a"]),
        "student_b": store.create_user(login="student.b", display_name="Aluno B", role=Role.STUDENT,
                                       password=PASSWORD, tenant_id="school-a", classroom_ids=["class-b"]),
        "teacher": store.create_user(login="teacher.a", display_name="Professora A", role=Role.TEACHER,
                                     password=PASSWORD, tenant_id="school-a", classroom_ids=["class-a"]),
        "other_teacher": store.create_user(login="teacher.b", display_name="Professor B", role=Role.TEACHER,
                                           password=PASSWORD, tenant_id="school-b"),
        "manager": store.create_user(login="manager.a", display_name="Gestão A", role=Role.SCHOOL_MANAGER,
                                     password=PASSWORD, tenant_id="school-a"),
    }

    def client(login=None):
        session = TestClient(main.app, headers={"Origin": ORIGIN})
        if login:
            response = session.post("/auth/login", json={"login": login, "password": PASSWORD})
            assert response.status_code == 200, response.text
        return session

    return store, users, client, tmp_path


def student_payload(snapshot_id):
    body = payload()
    snapshot = json.loads(body["snapshot_json"])
    snapshot["local_snapshot_id"] = snapshot_id
    body["snapshot_json"] = json.dumps(snapshot, ensure_ascii=False)
    body["submitted_by_user_id"] = "forged"  # Client may not choose ownership.
    return body


def test_store_password_hash_demo_script_and_public_model(auth_case, monkeypatch):
    store, users, _, tmp_path = auth_case
    stored = json.loads((tmp_path / "auth" / "users.json").read_text())
    first = stored["student.a"]
    assert first["password_hash"] != PASSWORD and first["password_salt"]
    assert first["password_kdf"] in {"scrypt", "pbkdf2_sha256"}
    assert "password" not in first and first["role"] == "STUDENT"
    assert store.authenticate("student.a", PASSWORD) == users["student_a"]
    assert store.authenticate("student.a", "wrong") is None
    assert store.authenticate("missing", PASSWORD) is None
    assert (tmp_path / "auth" / "users.json").stat().st_mode & 0o777 == 0o600

    demo = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "create_demo_users.py"))
    demo["create_demo_users"].__globals__["auth_store"] = lambda: store
    prompts = iter(["demo-secret", "demo-secret"] * 3)
    demo["create_demo_users"](prompt=lambda _: next(prompts), output=lambda _: None)
    for login in ("aluno.demo", "professor.demo", "gestao.demo"):
        assert store.authenticate(login, "demo-secret") is not None
    assert "demo-secret" not in (tmp_path / "auth" / "users.json").read_text()


def test_login_session_cookie_logout_expiry_tamper_inactive_and_origin(auth_case, monkeypatch, caplog):
    store, users, client_factory, tmp_path = auth_case
    client = client_factory()
    assert "Confiabilidade e Explicabilidade" in client.get("/").text
    assert "profile-switch" not in client.get("/").text
    assert client.get("/auth/me").status_code == 401
    assert "login-form" in client.get("/static/index.html").text
    assert client.get("/static/capture/tablet.html").status_code == 401
    assert client.post("/auth/login", json={"login": "missing", "password": PASSWORD}).json() == {
        "detail": "Credenciais inválidas."}
    assert client.post("/auth/login", json={"login": "student.a", "password": "wrong"}).status_code == 401
    assert client.post("/auth/login", json={"login": "student.a", "password": PASSWORD,
                                            "role": "TEACHER"}).status_code == 401
    assert client.post("/auth/login", headers={"Origin": "https://evil.example"},
                       json={"login": "student.a", "password": PASSWORD}).status_code == 403
    response = client.post("/auth/login", json={"login": "student.a", "password": PASSWORD})
    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "max-age=" in cookie and "path=/" in cookie
    assert "secure" not in cookie  # Local HTTP test mode only.
    assert "password" not in response.text and "hash" not in response.text and "salt" not in response.text
    assert client.get("/auth/me").json() == users["student_a"].model_dump(mode="json")
    assert client.post("/auth/logout", headers={"Origin": ""}).status_code == 403
    assert client.get("/auth/me").status_code == 200
    assert "auth-enabled" in client.get("/").text
    assert client.get("/capture").status_code == 200
    assert client.get("/problems").status_code == 200
    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401

    expired = store.create_session(users["student_a"].user_id, lifetime=-1)
    client.cookies.set(COOKIE_NAME, expired)
    assert client.get("/auth/me").status_code == 401
    good = store.create_session(users["student_a"].user_id)
    client.cookies.set(COOKIE_NAME, good + "changed")
    assert client.get("/auth/me").status_code == 401
    client.cookies.set(COOKIE_NAME, good)
    raw = json.loads((tmp_path / "auth" / "users.json").read_text())
    raw["student.a"]["active"] = False
    (tmp_path / "auth" / "users.json").write_text(json.dumps(raw))
    assert client.get("/auth/me").status_code == 401
    assert client.post("/auth/login", json={"login": "student.a", "password": PASSWORD}).status_code == 401
    assert PASSWORD not in caplog.text

    monkeypatch.delenv("CONFIA_COOKIE_SECURE")
    secure_login = client_factory().post("/auth/login", json={"login": "teacher.a", "password": PASSWORD})
    assert "secure" in secure_login.headers["set-cookie"].lower()
    monkeypatch.setenv("CONFIA_COOKIE_SECURE", "0")
    monkeypatch.setenv("CONFIA_ENV", "production")
    with pytest.raises(RuntimeError, match="insecure cookie"):
        client_factory().post("/auth/login", json={"login": "teacher.a", "password": PASSWORD})


def test_role_matrix_object_scope_hmer_teacher_and_audit(auth_case, monkeypatch):
    _, users, client_factory, tmp_path = auth_case
    registry = RecognizerRegistry()
    registry.register("mathpix", PreviewAdapter)
    registry.register("fake_test", FakeTestRecognizer)
    monkeypatch.setattr(submissions_router, "configured_registry", lambda: registry)
    student_a = client_factory("student.a")
    student_b = client_factory("student.b")
    teacher = client_factory("teacher.a")
    other_teacher = client_factory("teacher.b")
    manager = client_factory("manager.a")

    assert student_a.get("/management/overview").status_code == 403
    assert teacher.get("/management/overview").status_code == 403
    assert manager.get("/management/overview").json()["kind"] == "demonstrative_aggregate"
    assert manager.get("/submissions").status_code == 403
    assert manager.get("/problems").status_code == 403
    assert manager.post("/audit", json={}).status_code == 403
    assert manager.get("/capture").status_code == 403
    assert teacher.get("/capture").status_code == 403
    assert teacher.get("/static/capture/tablet.html").status_code == 403
    assert student_a.get("/capture").status_code == 200
    assert student_a.get("/static/capture/tablet.html").status_code == 200
    assert student_a.get("/submissions").json() == []

    submitted = student_payload("snapshot:auth-a")
    assert student_a.post("/submissions", json=submitted).status_code == 422
    submitted.pop("submitted_by_user_id")
    preview = student_a.post("/submissions/recognition-preview", json={
        "snapshot_json": submitted["snapshot_json"], "client_preview_id": "preview:auth-test"})
    assert preview.status_code == 200, preview.text
    assert student_a.get("/submissions").json() == []
    receipt = student_a.post("/submissions", json=submitted)
    assert receipt.status_code == 201, receipt.text
    sid = receipt.json()["submission_id"]
    assert receipt.json()["submitted_by_user_id"] == users["student_a"].user_id
    assert receipt.json()["tenant_id"] == "school-a" and receipt.json()["classroom_id"] == "class-a"
    assert student_a.post("/submissions", json=submitted).status_code == 200
    assert student_b.post("/submissions", json=submitted).status_code == 409
    assert len(student_a.get("/submissions").json()) == 1
    assert student_b.get("/submissions").json() == []
    assert len(teacher.get("/submissions").json()) == 1
    assert other_teacher.get("/submissions").json() == []
    for path in (f"/submissions/{sid}", f"/submissions/{sid}/pages/0",
                 f"/submissions/{sid}/snapshot", f"/submissions/{sid}/recognitions"):
        assert student_b.get(path).status_code == 403
        assert manager.get(path).status_code == 403
        assert other_teacher.get(path).status_code == 403
    assert student_a.get(f"/submissions/{sid}/snapshot").status_code == 200
    assert teacher.get(f"/submissions/{sid}/pages/0").status_code == 200
    assert student_b.post(f"/submissions/{sid}/recognitions", json={"provider": "fake_test"}).status_code == 403
    assert teacher.post(f"/submissions/{sid}/recognitions", json={"provider": "fake_test"}).status_code == 403
    assert student_a.post(f"/submissions/{sid}/transcriptions", json={}).status_code == 403
    assert manager.get(f"/submissions/{sid}/transcriptions").status_code == 403
    assert student_a.get(f"/submissions/{sid}/audits").status_code == 403

    official = student_a.post(f"/submissions/{sid}/recognitions", json={
        "provider": "fake_test", "idempotency_key": "auth:official:0"})
    assert official.status_code == 201, official.text
    assert official.json()["status"] == "NEEDS_REVIEW"
    teacher_transcriptions = teacher.get(f"/submissions/{sid}/transcriptions").json()
    assert len(teacher_transcriptions) == 1
    assert teacher_transcriptions[0]["latest_revision"]["status"] == "NEEDS_REVIEW"
    tid = official.json()["transcription_id"]
    assert student_a.get(f"/transcriptions/{tid}").status_code == 403
    assert manager.post(f"/transcriptions/{tid}/accept", json={}).status_code == 403
    assert other_teacher.post(f"/transcriptions/{tid}/accept", json={}).status_code == 403
    acceptance = teacher.post(f"/transcriptions/{tid}/accept", json={
        "revision_number": 1, "reviewer_reference": "teacher.a"})
    assert acceptance.status_code == 200, acceptance.text
    assert student_a.post(f"/submissions/{sid}/audits", json={}).status_code == 403

    calls = []
    def engine(request):
        calls.append(request)
        return result(request.problem_id)
    monkeypatch.setattr(main, "execute_audit", engine)
    audit = teacher.post(f"/submissions/{sid}/audits", json={
        "transcription_id": tid, "revision_number": 1,
        "acceptance_id": acceptance.json()["acceptance"]["acceptance_id"]})
    assert audit.status_code == 200, audit.text
    assert len(calls) == 1
    aid = audit.json()["audit_run_id"]
    assert teacher.get(f"/submission-audits/{aid}").status_code == 200
    assert other_teacher.get(f"/submission-audits/{aid}").status_code == 403
    assert manager.get(f"/submission-audits/{aid}").status_code == 403
    assert teacher.get(f"/submission-audits/{aid}/reproducibility").status_code == 200
    original = json.loads((tmp_path / "submissions" / sid / "submission.json").read_text())
    assert original["submitted_by_user_id"] == users["student_a"].user_id


def test_teacher_detail_keeps_provider_metadata_review_and_audit_available(auth_case, monkeypatch):
    auth_store, _, client_factory, _ = auth_case
    auth_store.create_user(login="aluno.demo", display_name="Aluno Demo", role=Role.STUDENT,
                           password=PASSWORD, tenant_id="school-a", classroom_ids=["class-a"])
    auth_store.create_user(login="professor.demo", display_name="Professor Demo", role=Role.TEACHER,
                           password=PASSWORD, tenant_id="school-a", classroom_ids=["class-a"])
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", "private-test-id")
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "private-test-key")
    registry = RecognizerRegistry()
    registry.register("mathpix", PreviewAdapter)
    monkeypatch.setattr(submissions_router, "configured_registry", lambda: registry)

    student = client_factory("aluno.demo")
    teacher = client_factory("professor.demo")
    manager = client_factory("manager.a")
    assert teacher.get("/auth/me").json()["role"] == "TEACHER"
    submitted = student_payload("snapshot:teacher-regression")
    submitted.pop("submitted_by_user_id")
    receipt = student.post("/submissions", json=submitted)
    assert receipt.status_code == 201, receipt.text
    sid = receipt.json()["submission_id"]
    official = student.post(f"/submissions/{sid}/recognitions", json={
        "provider": "mathpix", "idempotency_key": "teacher-regression:0"})
    assert official.status_code == 201, official.text
    assert official.json()["status"] == "NEEDS_REVIEW"

    queue = teacher.get("/submissions")
    assert queue.status_code == 200
    assert [item["submission_id"] for item in queue.json()] == [sid]
    providers = teacher.get("/submissions/recognition-providers")
    assert providers.status_code == 200
    assert providers.json() == [{"provider": "mathpix", "label": "Mathpix"}]
    assert providers.headers["cache-control"] == "no-store"
    assert "private-test-id" not in providers.text and "private-test-key" not in providers.text
    assert student.get("/submissions/recognition-providers").json() == providers.json()
    monkeypatch.setattr(submissions_router, "configured_registry", RecognizerRegistry)
    unconfigured = teacher.get("/submissions/recognition-providers")
    assert unconfigured.status_code == 200 and unconfigured.json() == []
    monkeypatch.setattr(submissions_router, "configured_registry", lambda: registry)
    assert manager.get("/submissions/recognition-providers").status_code == 403
    assert client_factory().get("/submissions/recognition-providers").status_code == 401
    assert teacher.post("/submissions/recognition-providers", json={}).status_code == 405

    detail = teacher.get(f"/submissions/{sid}")
    assert detail.status_code == 200
    assert detail.json()["submission"]["submission_id"] == sid
    assert all(item["matches"] for item in detail.json()["integrity"])
    assert teacher.get(f"/submissions/{sid}/pages/0").status_code == 200
    summaries = teacher.get(f"/submissions/{sid}/transcriptions")
    assert summaries.status_code == 200
    assert summaries.json()[0]["latest_revision"]["status"] == "NEEDS_REVIEW"
    tid = official.json()["transcription_id"]
    history = teacher.get(f"/transcriptions/{tid}")
    assert history.status_code == 200
    assert history.json()["revisions"][0]["segments"][0]["latex"] == "2 + 2 = 5"
    assert teacher.get(f"/submissions/{sid}/audits").json() == []

    assert student.get(f"/transcriptions/{tid}").status_code == 403
    assert student.post(f"/transcriptions/{tid}/accept", json={}).status_code == 403
    assert student.post(f"/submissions/{sid}/audits", json={}).status_code == 403
    assert manager.get(f"/submissions/{sid}").status_code == 403
    assert manager.get(f"/submissions/{sid}/transcriptions").status_code == 403
    assert manager.post(f"/submissions/{sid}/audits", json={}).status_code == 403

    acceptance = teacher.post(f"/transcriptions/{tid}/accept", json={
        "revision_number": 1, "reviewer_reference": "professor.demo"})
    assert acceptance.status_code == 200, acceptance.text
    assert teacher.get(f"/transcriptions/{tid}").json()["revisions"][0]["status"] == "ACCEPTED"
    monkeypatch.setattr(main, "execute_audit", lambda request: result(request.problem_id))
    audit = teacher.post(f"/submissions/{sid}/audits", json={
        "transcription_id": tid, "revision_number": 1,
        "acceptance_id": acceptance.json()["acceptance"]["acceptance_id"]})
    assert audit.status_code == 200, audit.text
    assert audit.json()["status"] == "COMPLETED"


def test_legacy_unscoped_is_preserved_and_opt_in_teacher_read(auth_case, monkeypatch):
    _, _, client_factory, tmp_path = auth_case
    submission_store = SubmissionStore(tmp_path / "submissions")
    body = payload()
    receipt, _ = submission_store.receive(SubmissionRequest.model_validate(body))
    sid = receipt.submission_id
    before = (tmp_path / "submissions" / sid / "submission.json").read_bytes()
    teacher = client_factory("teacher.a")
    student = client_factory("student.a")
    assert teacher.get("/submissions").json() == []
    assert teacher.get(f"/submissions/{sid}").status_code == 403
    assert student.get(f"/submissions/{sid}").status_code == 403
    monkeypatch.setenv("CONFIA_AUTH_LEGACY_READ", "1")
    assert teacher.get(f"/submissions/{sid}").status_code == 200
    assert len(teacher.get("/submissions").json()) == 1
    assert student.get(f"/submissions/{sid}").status_code == 403
    assert (tmp_path / "submissions" / sid / "submission.json").read_bytes() == before
    assert json.loads(before)["submitted_by_user_id"] is None


def test_frontend_role_lock_and_production_guard(auth_case, monkeypatch):
    _, _, client_factory, _ = auth_case
    client = client_factory("student.a")
    html = client.get("/").text
    assert "data-auth-enabled=\"true\"" in html
    assert "auth-identity" in html and "auth-logout" in html
    assert "ConfIAAuthProfile" in client.get("/static/shell.js").text
    assert "profile-switch" in client.get("/static/styles.css").text
    assert "auth-enabled .profile-switch" in client.get("/static/styles.css").text
    assert 'body.auth-enabled[data-resolution-active="true"] .profile-switch { display: none; }' in client.get("/static/styles.css").text
    assert "profile !== authenticatedProfile" in client.get("/static/shell.js").text
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "0")
    monkeypatch.setenv("CONFIA_ENV", "production")
    with pytest.raises(RuntimeError, match="authentication cannot be disabled"):
        client.get("/")
