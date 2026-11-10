"""Real D1 capture: no OCR, mathematical fixture or fake AuthUser required."""
import base64
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from io import BytesIO
import json

import pytest
import pypdfium2 as pdfium
from PIL import Image
from fastapi.testclient import TestClient
from pydantic import ValidationError

from confia_lean_auditor.main import app
from confia_lean_auditor.assessments.models import AssessmentParticipant
from confia_lean_auditor.assessments.participants import ParticipantStore
from confia_lean_auditor.tme.auth import TMEEvaluator, require_tme_evaluator


@pytest.fixture
def demo(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_ENV", "test")
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "1")
    monkeypatch.setenv("CONFIA_TME_DEMO_NO_AUTH", "1")
    for name in ("AUTH", "INSTITUTIONAL", "ASSESSMENTS", "ASSESSMENT_PARTICIPANTS",
                 "TME_CASES", "TME_EXAMS", "SUBMISSIONS", "SUBMISSION_AUDITS"):
        monkeypatch.setenv(f"CONFIA_{name}_DIR", str(tmp_path / name.lower()))
    with TestClient(app, headers={"Origin": "http://testserver"}) as client:
        yield client, tmp_path


def pdf(pages=4):
    output = BytesIO()
    with closing(pdfium.PdfDocument.new()) as document:
        for index in range(pages):
            document.new_page(200 + index * 10, 300).close()
        document.save(output)
    return output.getvalue()


def png(color="red", size=(40, 80)):
    output = BytesIO()
    Image.new("RGB", size, color).save(output, format="PNG")
    return output.getvalue()


def package(client, data=None, media_type="application/pdf", key="capture-1"):
    response = client.get("/tme/assessments")
    assert response.status_code == 200, response.text
    return {"assessment_identifier": response.json()[0]["assessment"]["assessment_id"],
        "external_participant_code": "PROVA-2026-001", "idempotency_key": key,
        "original_documents": [{"media_type": media_type,
            "content_base64": base64.b64encode(data if data is not None else pdf()).decode()}]}


def receive(client, body=None):
    response = client.post("/tme/exam-submissions", json=body or package(client))
    assert response.status_code == 201, response.text
    return response.json()


def test_participant_invariants_uniqueness_and_no_civil_identity(tmp_path):
    store = ParticipantStore(tmp_path / "participants")
    aid = "asmt_" + "a" * 32
    registered = store.get_or_create(aid, "REGISTERED_USER", user_id="existing-user")
    assert registered.external_code is None
    def external(_):
        return store.get_or_create(aid, "EXTERNAL_PSEUDONYM", external_namespace="tme", external_code="P-1")
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(external, range(8)))
    assert len({p.participant_id for p in records}) == 1
    assert len(list(store.root.glob("part_*.json"))) == 2
    assert records[0].user_id is None
    with pytest.raises(ValidationError):
        store.get_or_create(aid, "EXTERNAL_PSEUDONYM", external_namespace=" tme ", external_code=" P-1 ")
    assert not {"name", "email", "cpf", "display_name"} & records[0].model_dump().keys()
    assert store.get_or_create(aid, "EXTERNAL_PSEUDONYM", external_namespace="other", external_code="P-1").participant_id != records[0].participant_id
    base = dict(participant_id="part_" + "b" * 32, assessment_id=aid, created_at=datetime.now(timezone.utc))
    for invalid in ({"participant_kind": "REGISTERED_USER"},
                    {"participant_kind": "REGISTERED_USER", "user_id": "u", "external_code": "P"},
                    {"participant_kind": "EXTERNAL_PSEUDONYM"},
                    {"participant_kind": "EXTERNAL_PSEUDONYM", "external_code": "P", "user_id": "u"},
                    {"participant_kind": "EXTERNAL_PSEUDONYM", "external_code": "P", "email": "private@example.org"}):
        with pytest.raises(ValidationError):
            AssessmentParticipant(**base, **invalid)


def test_pdf_original_pages_attempts_and_retry(demo):
    client, root = demo
    original = pdf()
    body = package(client, original)
    detail = receive(client, body)
    exam = detail["submission"]
    base = f'/tme/exam-submissions/{exam["submission_id"]}'
    assert exam["source"] == "PDF" and exam["page_count"] == 4
    pages = client.get(base + "/pages").json()
    assert [p["page_number"] for p in pages] == [1, 2, 3, 4]
    assert [p["original_page_number"] for p in pages] == [1, 2, 3, 4]
    assert len({p["original_asset_id"] for p in pages}) == 1
    assert [p["width"] for p in pages] == [400, 420, 440, 460]
    asset = client.get(base + "/assets/original_0001")
    assert asset.content == original and asset.headers["content-type"] == "application/pdf"
    for page in pages:
        preview = client.get(base + "/assets/" + page["preview_asset_id"])
        assert preview.content.startswith(b"\x89PNG")
    attempts = client.get(base + "/question-attempts").json()
    assert len(attempts) == 5
    assert [q["question_attempt"]["question_order"] for q in attempts] == [1, 2, 3, 4, 5]
    assert all(q["mapping_state"] == "UNASSIGNED" for q in attempts)
    assert all(q["question_attempt"]["max_score"] == "20.0" for q in attempts)
    assert detail["participant"]["participant_kind"] == "EXTERNAL_PSEUDONYM"
    assert not list((root / "auth").glob("**/users/*.json"))
    assert client.get("/tme/cases").json() == []  # Legacy queue is not a second projection.
    assert len(client.get("/tme/exam-submissions").json()) == 1
    retry = client.post("/tme/exam-submissions", json=body)
    assert retry.status_code == 200 and retry.json() == detail
    body["external_participant_code"] = "OTHER"
    assert client.post("/tme/exam-submissions", json=body).status_code == 409
    assert client.post(f'/tme/cases/{attempts[0]["question_attempt"]["case_id"]}/scan', json={}).status_code in (409, 422)


def test_images_order_rotation_and_many_to_many_mapping(demo):
    client, root = demo
    originals = [png(color) for color in ("blue", "red", "green", "yellow")]
    body = package(client, originals[0], "image/png")
    body["original_documents"] = [{"media_type": "image/png", "content_base64": base64.b64encode(data).decode(),
        "rotation_degrees": 90 if i == 0 else 0} for i, data in enumerate(originals)]
    body["pages"] = [{"page_number": 1, "question_hint": "TME2026P1", "transcription_candidate": "unverified"}]
    detail = receive(client, body)
    exam, questions = detail["submission"], detail["question_attempts"]
    base = f'/tme/exam-submissions/{exam["submission_id"]}'
    assert exam["page_count"] == 4 and exam["source"] == "IMAGES"
    assert (exam["pages"][0]["width"], exam["pages"][0]["height"]) == (80, 40)
    assert detail["mapping"]["bindings"] == []  # Hints do not become accepted mapping/transcription.
    for index, original in enumerate(originals, 1):
        assert client.get(base + f"/assets/original_{index:04d}").content == original
    bindings = [{"question_attempt_id": questions[q]["case_id"], "exam_page_id": exam["pages"][p]["exam_page_id"], "order": order}
        for q, p, order in [(0, 1, 1), (0, 0, 2), (1, 1, 1)]]
    mapped = client.put(base + "/page-mapping", json={"expected_version": 1, "bindings": bindings})
    assert mapped.status_code == 200 and mapped.json()["version"] == 2
    question = client.get('/tme/question-attempts/' + questions[0]["case_id"]).json()
    assert question["mapping_state"] == "READY"
    assert [p["page_number"] for p in question["pages"]] == [2, 1]
    second = client.get('/tme/question-attempts/' + questions[1]["case_id"]).json()
    assert second["pages"][0]["page_number"] == 2
    assert client.put(base + "/page-mapping", json={"expected_version": 1, "bindings": []}).status_code == 409
    for invalid in ([bindings[0], bindings[0]], [{**bindings[0], "order": 2}],
                    [{**bindings[0], "exam_page_id": "page_" + "f" * 32}],
                    [{**bindings[0], "question_attempt_id": "case_" + "f" * 32}]):
        assert client.put(base + "/page-mapping", json={"expected_version": 2, "bindings": invalid}).status_code == 409
    assert len(list((root / "tme_exams" / exam["submission_id"]).glob("mapping_*.json"))) == 2


def test_demo_scope_configurable_assessment_and_authorization(demo, monkeypatch):
    client, _ = demo
    assert client.get("/tme").status_code == 200
    assert client.get("/assessments").status_code == 401
    created = client.post("/tme/assessments", json={"title": "Prova configurável", "academic_year": 2026,
        "items": [{"problem_id": "ITA2025F2Q1", "points": 7}, {"problem_id": "TME2026P2", "points": 20}]})
    assert created.status_code == 201, created.text
    doc = created.json()
    assert doc["assessment"]["scope"] == "TME" and doc["assessment"]["school_id"] is None
    body = package(client)
    body["assessment_identifier"] = doc["assessment"]["assessment_id"]
    detail = receive(client, body)
    assert len(detail["question_attempts"]) == 2
    exam_id = detail["submission"]["submission_id"]
    app.dependency_overrides[require_tme_evaluator] = lambda: TMEEvaluator("other")
    try:
        assert client.get(f"/tme/exam-submissions/{exam_id}").status_code == 403
        assert client.get(f"/tme/exam-submissions/{exam_id}/assets/original_0001").status_code == 403
        assert client.get("/tme/exam-submissions").json() == []
        assert client.post("/tme/exam-submissions", json=body).status_code == 403
    finally:
        app.dependency_overrides.pop(require_tme_evaluator)
    monkeypatch.setenv("CONFIA_TME_DEMO_NO_AUTH", "0")
    assert client.get("/tme/assessments").status_code == 401
    assert client.get(f"/tme/exam-submissions/{exam_id}/pages").status_code == 401
    assert client.post("/tme/exam-submissions", json=body).status_code == 401


@pytest.mark.parametrize("kind", ["broken_pdf", "wrong_mime", "mixed", "over_50", "bad_metadata", "pii"])
def test_invalid_capture_publishes_nothing(demo, kind):
    client, root = demo
    body = package(client, png() if kind == "wrong_mime" else b"%PDF-broken" if kind == "broken_pdf" else pdf(51) if kind == "over_50" else pdf())
    if kind == "mixed":
        body["original_documents"].append({"media_type": "image/png", "content_base64": base64.b64encode(png()).decode()})
    if kind == "bad_metadata":
        body["pages"] = [{"page_number": 50}]
    if kind == "pii":
        body["email"] = "private@example.org"
    result = client.post("/tme/exam-submissions", json=body)
    assert result.status_code == 422, result.text
    assert "content_base64" not in result.text and "private@example.org" not in result.text
    assert not list((root / "tme_exams").glob("exam_*"))
    assert not list((root / "tme_cases").glob("case_*"))


def test_tampered_original_and_manifest_fail_closed(demo):
    client, root = demo
    detail = receive(client)
    eid = detail["submission"]["submission_id"]
    folder = root / "tme_exams" / eid
    (folder / "original_0001").write_bytes(b"replaced")
    assert client.get(f"/tme/exam-submissions/{eid}/assets/original_0001").status_code == 409
    manifest = json.loads((folder / "exam.json").read_text())
    manifest["data"]["submission"]["page_count"] = 1
    (folder / "exam.json").write_text(json.dumps(manifest))
    assert client.get(f"/tme/exam-submissions/{eid}").status_code == 409


def test_interrupted_publication_recovers_without_duplicate_attempts(demo, monkeypatch):
    from confia_lean_auditor.tme.store import CaseStore
    client, root = demo
    body = package(client)
    original = CaseStore.create
    calls = []
    def interrupted(self, *args, **kwargs):
        calls.append(kwargs["case_id"])
        if len(calls) == 2:
            raise OSError("simulated storage interruption")
        return original(self, *args, **kwargs)
    monkeypatch.setattr(CaseStore, "create", interrupted)
    assert client.post("/tme/exam-submissions", json=body).status_code == 503
    assert client.get("/tme/cases").json() == []
    assert client.get("/tme/exam-submissions").json() == []
    monkeypatch.setattr(CaseStore, "create", original)
    detail = receive(client, body)
    assert len(list((root / "tme_cases").glob("case_*"))) == 5
    assert detail["question_attempts"][0]["case_id"] == calls[0]
    assert not list((root / "tme_exams").glob(".pending-*"))


def test_capture_byte_limits_and_frozen_mapping(demo, monkeypatch):
    from confia_lean_auditor.tme import exam_capture
    client, root = demo
    body = package(client)
    with monkeypatch.context() as limits:
        limits.setattr(exam_capture, "MAX_DOCUMENT_BYTES", 1)
        assert client.post("/tme/exam-submissions", json=body).status_code == 422
    with monkeypatch.context() as limits:
        limits.setattr(exam_capture, "MAX_TOTAL_BYTES", 1)
        assert client.post("/tme/exam-submissions", json=body).status_code == 422
    detail = receive(client, body)
    eid = detail["submission"]["submission_id"]
    attempt = detail["question_attempts"][0]
    path = root / "tme_cases" / attempt["case_id"] / "case.json"
    raw = json.loads(path.read_text())
    raw["submission_id"] = "sub_" + "e" * 32
    path.write_text(json.dumps(raw))
    binding = {"question_attempt_id": attempt["case_id"], "exam_page_id": detail["submission"]["pages"][0]["exam_page_id"], "order": 1}
    assert client.put(f"/tme/exam-submissions/{eid}/page-mapping", json={"expected_version": 1, "bindings": [binding]}).status_code == 409


def test_institutional_serialization_and_definition_hash_match_initial_sha():
    from confia_lean_auditor.assessments.models import AssessmentDocument
    from confia_lean_auditor.assessments.store import definition_hash
    # Serialized using models from SHA 1b3daea, before introducing TME scope.
    legacy = {"assessment": {"assessment_id": "asmt_" + "1" * 32, "title": "Legacy", "instructions": "",
        "teacher_user_id": "teacher", "network_id": "network", "school_id": "school", "classroom_id": "class",
        "academic_year": 2026, "status": "DRAFT", "opens_at": "2026-01-01T00:00:00Z", "closes_at": "2026-01-02T00:00:00Z",
        "created_at": "2026-01-01T00:00:00Z", "published_at": None, "closed_at": None,
        "definition_sha256": None, "schema_version": "1.0"},
        "items": [{"assessment_item_id": "ait_" + "2" * 32, "assessment_id": "asmt_" + "1" * 32,
                   "problem_id": "ITA2025F2Q1", "order": 1, "points": 5.0}]}
    doc = AssessmentDocument.model_validate(legacy)
    assert doc.model_dump(mode="json") == legacy
    assert definition_hash(doc) == "e681264128eb81ef32accd3996e846d588de02ae618023f27d19032b167781a9"
    del legacy["assessment"]["school_id"]
    with pytest.raises(ValidationError):
        AssessmentDocument.model_validate(legacy)

