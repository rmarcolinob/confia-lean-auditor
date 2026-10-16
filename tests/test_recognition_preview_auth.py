"""The authenticated tablet payload and preview provider configuration boundary."""
import base64
import json
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient
import httpx
import pytest

import confia_lean_auditor.main as main
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.auth.store import AuthStore
from confia_lean_auditor.institutional.models import (Network, School, Classroom, TeacherAssignment,
    Enrollment, InstitutionalData)
from confia_lean_auditor.institutional.store import InstitutionalStore, current_academic_year
from confia_lean_auditor.recognition.mathpix import MathpixRecognitionProvider
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.submissions import router as submissions_router
from test_submissions import png

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "http://testserver"
PASSWORD = "test-password"


def tablet_preview_payload():
    """Build the exact outer JSON and frozen snapshot used by tablet.js."""
    script = """
      const M = require('./app/confia_lean_auditor/static/capture/ink-model.js');
      let draft = M.createDraft('ITA2025Q1');
      draft = M.addStroke(draft, {page_id:draft.pages[0].page_id, pointer_type:'pen',
        points:[{x:10,y:20,t_ms:0,pressure_reported:0.5},
                {x:40,y:50,t_ms:1,pressure_reported:0.5}]});
      const snapshot = M.freeze(draft);
      process.stdout.write(JSON.stringify({snapshot_json:JSON.stringify(M.exportClone(snapshot),null,2),
        client_preview_id:M.newId('preview')}));
    """
    return json.loads(subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True))


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "1")
    monkeypatch.setenv("CONFIA_COOKIE_SECURE", "0")
    monkeypatch.setenv("CONFIA_ENV", "test")
    monkeypatch.setenv("CONFIA_AUTH_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_SUBMISSION_AUDITS_DIR", str(tmp_path / "audits"))
    monkeypatch.setenv("CONFIA_INSTITUTIONAL_DIR", str(tmp_path / "institutional"))
    store = AuthStore(tmp_path / "auth")
    student = store.create_user(login="aluno.demo", display_name="Aluno Demo", role=Role.STUDENT,
                      password=PASSWORD, tenant_id="demo-pi", classroom_ids=["turma.demo"])
    teacher = store.create_user(login="professor.demo", display_name="Professor Demo", role=Role.TEACHER,
                      password=PASSWORD, tenant_id="demo-pi", classroom_ids=["turma.demo"])
    year = current_academic_year()
    InstitutionalStore(tmp_path / "institutional").replace(InstitutionalData(
        networks=[Network(network_id="demo-pi", name="Rede Demo")],
        schools=[School(school_id="ceti-centro", network_id="demo-pi", name="CETI Centro",
                        code="centro", municipality="Teresina")],
        classrooms=[Classroom(classroom_id="turma.demo", school_id="ceti-centro", name="Turma Demo",
                              grade="2ª série", shift="Manhã", academic_year=year)],
        teacher_assignments=[TeacherAssignment(teacher_user_id=teacher.user_id, school_id="ceti-centro",
                                               classroom_id="turma.demo", academic_year=year)],
        enrollments=[Enrollment(student_user_id=student.user_id, school_id="ceti-centro",
                                classroom_id="turma.demo", academic_year=year)],
    ))

    def client(login=None):
        session = TestClient(main.app, headers={"Origin": ORIGIN})
        if login:
            response = session.post("/auth/login", json={"login": login, "password": PASSWORD})
            assert response.status_code == 200, response.text
        return session

    return client, tmp_path


def test_tablet_payload_with_student_session_through_teacher_review(case, monkeypatch):
    client, tmp_path = case
    monkeypatch.setenv("CONFIA_MATHPIX_APP_ID", "test-id")
    monkeypatch.setenv("CONFIA_MATHPIX_APP_KEY", "test-key")
    provider_calls = []

    def mathpix_reply(request):
        provider_calls.append(json.loads(request.content))
        return httpx.Response(200, json={"text": "x=1", "latex_styled": "x=1"})

    registry = RecognizerRegistry()
    registry.register("mathpix", lambda: MathpixRecognitionProvider(
        transport=httpx.MockTransport(mathpix_reply)))
    monkeypatch.setattr(submissions_router, "configured_registry", lambda: registry)
    monkeypatch.setattr(main, "execute_audit", lambda _request: pytest.fail("Preview must not call Audit/Lean"))

    body = tablet_preview_payload()
    assert set(body) == {"snapshot_json", "client_preview_id"}
    student = client("aluno.demo")
    teacher = client("professor.demo")
    preview = student.post("/submissions/recognition-preview", json=body)
    assert preview.status_code == 200, preview.text
    assert preview.json()["client_preview_id"] == body["client_preview_id"]
    assert preview.json()["result"]["segments"][0]["latex"] == "x=1"
    assert len(provider_calls) == 1
    assert not (tmp_path / "submissions").exists()
    assert teacher.get("/submissions").json() == []

    snapshot = json.loads(body["snapshot_json"])
    submitted = student.post("/submissions", json={
        "snapshot_json": body["snapshot_json"],
        "pages": [{"page_id": snapshot["pages"][0]["page_id"],
                   "png_base64": base64.b64encode(png()).decode("ascii")}],
    })
    assert submitted.status_code == 201, submitted.text
    sid = submitted.json()["submission_id"]
    official = student.post(f"/submissions/{sid}/recognitions", json={
        "provider": "mathpix", "idempotency_key": "mathpix:0"})
    assert official.status_code == 201, official.text
    assert official.json()["status"] == "NEEDS_REVIEW"
    assert len(provider_calls) == 2
    queue = teacher.get("/submissions")
    assert queue.status_code == 200
    assert [row["submission_id"] for row in queue.json()] == [sid]
    transcriptions = teacher.get(f"/submissions/{sid}/transcriptions")
    assert transcriptions.status_code == 200
    assert transcriptions.json()[0]["latest_revision"]["status"] == "NEEDS_REVIEW"
    assert transcriptions.json()[0]["latest_revision"]["segments"][0]["latex"] == "x=1"
    assert teacher.get(f"/submissions/{sid}/audits").json() == []


def test_invalid_tablet_payload_is_422_but_auth_errors_are_not(case, monkeypatch):
    client, tmp_path = case
    student = client("aluno.demo")
    teacher = client("professor.demo")
    body = tablet_preview_payload()
    assert client().post("/submissions/recognition-preview", json=body).status_code == 401
    assert teacher.post("/submissions/recognition-preview", json=body).status_code == 403
    invalid = {**body, "submitted_by_user_id": "forged-client-owner"}
    response = student.post("/submissions/recognition-preview", json=invalid)
    assert response.status_code == 422
    assert response.json() == {"detail": "Payload de prévia inválido."}
    assert not (tmp_path / "submissions").exists()

    monkeypatch.delenv("CONFIA_MATHPIX_APP_ID", raising=False)
    monkeypatch.delenv("CONFIA_MATHPIX_APP_KEY", raising=False)
    missing_provider = student.post("/submissions/recognition-preview", json=body)
    assert missing_provider.status_code == 503
    assert missing_provider.json() == {"detail": "Reconhecedor indisponível neste ambiente."}
