"""DY1 lifecycle, concurrent edits, immutable provenance and teacher API boundaries."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from confia_lean_auditor.main import app
from confia_lean_auditor.dynamic.models import Actor, CreateProblem, CreateStatement, SaveRubric, ExpectedRevision, RubricContent
from confia_lean_auditor.dynamic.store import DynamicStore, DynamicConflict
from confia_lean_auditor.assessments.store import AssessmentIntegrityConflict, AssessmentStore, definition_hash
from confia_lean_auditor.core.correction_mode import CorrectionConfiguration, DynamicAuditProvenance, configured_mode, CorrectionMode
from confia_lean_auditor.submissions.integrity import canonical_sha256
from test_core_auth import auth_case

ACTOR = Actor(actor_id="teacher-dy1", kind="TEACHER", tenant_id="school-a")
CRITERIA = [dict(criterion_id=k, title=t, description=t, max_points=p, order=i)
    for i, (k,t,p) in enumerate((("structure","Fatoração/estrutura",3),("roots","Raízes",3),("conclusion","Conclusão/justificativa",4)), 1)]


def create(store):
    return store.create(CreateProblem(statement="Resolva x² - 5x + 6 = 0", title="Equação quadrática",
        max_score=10, correction_mode="DYNAMIC"), ACTOR)


def save(store, doc, criteria=None, base=None):
    return store.save_rubric(doc["problem"]["problem_id"], SaveRubric(expected_revision=doc["revision"],
        statement_version=len(doc["statements"]), max_score=doc["statements"][-1]["max_score"],
        criteria=CRITERIA if criteria is None else criteria), ACTOR, base_id=base)


def approve(store, doc):
    return store.approve(doc["problem"]["problem_id"], doc["rubrics"][-1]["rubric_id"],
        ExpectedRevision(expected_revision=doc["revision"]), ACTOR)


@pytest.fixture
def store(tmp_path):
    return DynamicStore(tmp_path / "dynamic")


def test_teacher_draft_edit_approve_and_reload_exact_package(store):
    doc = create(store)
    assert doc["problem"]["correction_mode"] == "DYNAMIC"
    assert doc["packages"][0]["preparation_status"] == "NOT_PREPARED"
    assert doc["current_configuration"] is None
    doc = save(store, doc)
    assert doc["rubrics"][0]["status"] == "DRAFT_TEACHER"
    original = deepcopy(doc["rubrics"][0])
    changed = deepcopy(CRITERIA); changed[0]["description"] = "Apresenta a estrutura da fatoração."
    doc = save(store, doc, changed, original["rubric_id"])
    assert doc["rubrics"][0] == original
    assert doc["rubrics"][-1]["status"] == "TEACHER_EDITED"
    doc = approve(store, doc)
    assert doc["rubrics"][-1]["status"] == "APPROVED"
    assert doc["rubrics"][-1]["approved_by"]["actor_id"] == ACTOR.actor_id
    configuration = CorrectionConfiguration.model_validate(doc["current_configuration"])
    assert configuration.package.rubric_version == 2
    assert configuration.package.statement_version == 1
    assert configured_mode(doc["current_configuration"]) == CorrectionMode.DYNAMIC
    assert DynamicAuditProvenance(configuration=configuration, engine_version="dy3-future.v1").engine_version
    assert DynamicStore(store.root).get(doc["problem"]["problem_id"], ACTOR) == doc
    assert {e["event_type"] for e in doc["events"]} == {"dynamic_problem_created", "problem_statement_version_created",
        "rubric_draft_created", "rubric_edited", "rubric_approved", "dynamic_problem_package_activated"}
    for event in doc["events"]:
        assert event["timestamp"] and event["actor"]["actor_id"] == ACTOR.actor_id
        assert event["package_id"] and event["package_version"] and event["statement_version"]


def test_approved_content_never_changes_and_supersede_is_lifecycle(store):
    doc = approve(store, save(store, create(store)))
    identifier = doc["problem"]["problem_id"]
    files = {p: p.read_bytes() for p in store.folder(identifier).glob("*.json")}
    first = doc["rubrics"][0]; package = doc["current_configuration"]
    changed = deepcopy(CRITERIA); changed[1]["description"] = "Identifica ambas as raízes."
    doc = save(store, doc, changed, first["rubric_id"])
    assert doc["current_configuration"] == package  # Draft cannot replace approved package.
    assert doc["rubrics"][0]["status"] == "APPROVED"
    doc = approve(store, doc)
    assert [r["status"] for r in doc["rubrics"]] == ["SUPERSEDED", "APPROVED"]
    assert sum(r["is_current"] for r in doc["rubrics"]) == 1
    assert doc["rubrics"][0]["criteria"] == first["criteria"]
    assert doc["rubrics"][0]["approved_at"] == first["approved_at"]
    assert doc["rubrics"][-1]["supersedes_id"] == first["rubric_id"]
    assert all(p.read_bytes() == content for p, content in files.items())
    with pytest.raises(DynamicConflict): approve(store, doc)


def test_statement_change_requires_new_rubric_and_keeps_old_approval(store):
    doc = approve(store, save(store, create(store)))
    old = deepcopy(doc); identifier = doc["problem"]["problem_id"]
    doc = store.statement(identifier, CreateStatement(expected_revision=doc["revision"],
        statement="Resolva em R: x² - 5x + 6 = 0", max_score=10), ACTOR)
    assert doc["current_configuration"] is None and doc["current_package_id"] is None
    assert doc["rubrics"][0]["status"] == "SUPERSEDED"
    assert doc["statements"][0] == old["statements"][0]
    with pytest.raises(DynamicConflict):
        store.approve(identifier, old["rubrics"][0]["rubric_id"], ExpectedRevision(expected_revision=doc["revision"]), ACTOR)
    with pytest.raises(DynamicConflict):
        save(store, doc, base=old["rubrics"][0]["rubric_id"])
    doc = approve(store, save(store, doc))
    assert doc["current_configuration"]["package"]["statement_version"] == 2
    assert doc["current_configuration"]["package"]["rubric_version"] == 2
    assert old["current_configuration"] != doc["current_configuration"]


@pytest.mark.parametrize("mutation", [
    lambda x: x[0].update(max_points=-1),
    lambda x: x[0].update(max_points=2),
    lambda x: x[0].update(criterion_id="roots"),
    lambda x: x[0].update(order=2),
    lambda x: x[0].update(dependencies=["missing"]),
    lambda x: x[0].update(dependencies=["structure"]),
    lambda x: x[0].update(max_points="NaN"),
    lambda x: x[0].update(max_points="3.001"),
    lambda x: x[0].update(title="  "),
])
def test_invalid_rubrics_rejected(mutation):
    criteria = deepcopy(CRITERIA); mutation(criteria)
    with pytest.raises(ValidationError): RubricContent(max_score=10, criteria=criteria)


def test_cycle_zero_points_decimal_and_empty_draft(store):
    criteria = deepcopy(CRITERIA)
    criteria[0]["dependencies"] = ["roots"]; criteria[1]["dependencies"] = ["structure"]
    with pytest.raises(ValidationError): RubricContent(max_score=10, criteria=criteria)
    criteria = deepcopy(CRITERIA)
    for row, value in zip(criteria, ["0", "0.10", "0.20"]): row["max_points"] = value
    assert RubricContent(max_score="0.30", criteria=criteria)
    doc = save(store, create(store), [])
    with pytest.raises(DynamicConflict, match="vazia"): approve(store, doc)


def test_concurrent_approval_has_one_winner_and_stale_edit_cannot_overwrite(store):
    doc = save(store, create(store))
    def run():
        try: return approve(DynamicStore(store.root), doc)
        except DynamicConflict: return None
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(lambda _: run(), range(2)))
    assert sum(result is not None for result in results) == 1
    assert len(store.get(doc["problem"]["problem_id"], ACTOR)["approvals"]) == 1
    with pytest.raises(DynamicConflict): save(store, doc, base=doc["rubrics"][-1]["rubric_id"])


def test_digest_tampering_and_symlink_rejected(store, tmp_path):
    doc = create(store); identifier = doc["problem"]["problem_id"]
    path = store.folder(identifier) / "revision_000001.json"
    data = json.loads(path.read_text()); data["document"]["statements"][0]["statement"] = "tampered"
    path.write_text(json.dumps(data))
    with pytest.raises(AssessmentIntegrityConflict): store.get(identifier, ACTOR)
    path.unlink(); path.symlink_to(tmp_path / "outside")
    with pytest.raises(AssessmentIntegrityConflict): store.get(identifier, ACTOR)


def test_history_cannot_be_rewritten_even_with_new_snapshot_digest(store):
    doc = save(store, create(store)); identifier = doc["problem"]["problem_id"]
    path = store.folder(identifier) / "revision_000002.json"
    data = json.loads(path.read_text()); data["document"]["events"][0]["reason"] = "changed history"
    data.pop("sha256"); data["sha256"] = canonical_sha256(data); path.write_text(json.dumps(data))
    with pytest.raises(AssessmentIntegrityConflict): store.get(identifier, ACTOR)


def test_mode_default_and_no_fabricated_preparation():
    assert configured_mode() == CorrectionMode.SPECIALIZED
    assert CorrectionConfiguration().model_dump(mode="json") == {"mode":"SPECIALIZED", "package":None}
    with pytest.raises(ValidationError): configured_mode(False)
    with pytest.raises(ValidationError): CorrectionConfiguration(mode="DYNAMIC")
    with pytest.raises(ValidationError): CreateProblem(statement="x", max_score=10)
    from confia_lean_auditor.dynamic.models import FuturePreparation
    with pytest.raises(ValidationError): FuturePreparation(candidate_reference_solutions=["fake"])


@pytest.fixture
def api(auth_case, monkeypatch):
    _, _, clients, root = auth_case
    monkeypatch.setenv("CONFIA_DYNAMIC_DIR", str(root / "dynamic"))
    monkeypatch.setenv("CONFIA_ASSESSMENTS_DIR", str(root / "assessments"))
    return clients, root


def api_create(client):
    response = client.post("/dynamic/problems", json=dict(statement="Resolva x² - 5x + 6 = 0", max_score=10, correction_mode="DYNAMIC"))
    assert response.status_code == 201, response.text
    return response.json()


def test_api_crud_lifecycle_and_unavailable_services(api):
    clients, root = api; client = clients("teacher.a"); doc = api_create(client)
    prefix = "/dynamic/problems/" + doc["problem"]["problem_id"]
    response = client.post(prefix + "/rubrics", json=dict(expected_revision=1, statement_version=1, max_score=10, criteria=CRITERIA))
    assert response.status_code == 201, response.text
    doc = response.json(); rid = doc["rubrics"][-1]["rubric_id"]
    response = client.patch(prefix + "/rubrics/" + rid, json=dict(expected_revision=doc["revision"], statement_version=1, max_score=10, criteria=CRITERIA))
    assert response.status_code == 200, response.text
    doc = response.json(); rid = doc["rubrics"][-1]["rubric_id"]
    response = client.post(prefix + f"/rubrics/{rid}/approve", json={"expected_revision":doc["revision"]})
    assert response.status_code == 200, response.text
    doc = response.json()
    assert client.get(prefix + "/current").json()["rubric"]["status"] == "APPROVED"
    assert client.get(prefix + "/versions").json() == doc
    assert client.get(prefix).headers["cache-control"] == "no-store"
    assert len(client.get("/dynamic/problems").json()) == 1
    assert client.post(prefix + "/rubric-suggestion").status_code == 503  # DY2: real provider requires configuration.
    assert client.post(prefix + "/corrections").status_code == 501
    assert client.get(prefix).json() == doc
    response = client.post(prefix + "/statements", json=dict(expected_revision=doc["revision"], statement="Resolva em R a equação.", max_score=10))
    assert response.status_code == 201
    assert client.get(prefix + "/current").json()["current_configuration"] is None
    assert not (root / "audits").exists()


def test_api_permissions_forgery_and_validation(api):
    clients, _ = api; teacher = clients("teacher.a"); doc = api_create(teacher)
    prefix = "/dynamic/problems/" + doc["problem"]["problem_id"]
    assert clients().get(prefix).status_code == 401
    assert clients("student.a").get(prefix).status_code == 403
    assert clients("teacher.b").get(prefix).status_code == 404
    assert clients("teacher.b").get("/dynamic/problems").json() == []
    assert clients("teacher.b").post(prefix + "/rubrics", json=dict(expected_revision=1, statement_version=1, max_score=10, criteria=CRITERIA)).status_code == 404
    assert teacher.post("/dynamic/problems", json=dict(statement="x", max_score=10, correction_mode="DYNAMIC", created_by="forged")).status_code == 422
    assert teacher.post(prefix + "/rubrics", json=dict(expected_revision=1, statement_version=1, max_score=11, criteria=CRITERIA)).status_code == 422
    assert teacher.post(prefix + "/rubrics", json=dict(expected_revision=2, statement_version=1, max_score=10, criteria=CRITERIA)).status_code == 409
    assert teacher.post(prefix + "/rubrics", json=dict(expected_revision=1, statement_version=2, max_score=10, criteria=CRITERIA)).status_code == 409
    assert teacher.post(prefix + "/rubrics", headers={"Origin":"https://elsewhere.invalid"}, json={}).status_code == 403


def test_existing_assessment_unchanged_and_reference_is_context_only(api):
    clients, root = api; teacher = clients("teacher.a")
    t = datetime.now(timezone.utc)
    response = teacher.post("/assessments", json=dict(title="Existing", school_id="school-a", classroom_id="class-a",
        opens_at=t.isoformat(), closes_at=(t + timedelta(days=1)).isoformat()))
    assert response.status_code == 201
    aid = response.json()["assessment"]["assessment_id"]
    before = (root / "assessments" / f"{aid}.json").read_bytes()
    payload = dict(statement="Novo", max_score=10, correction_mode="DYNAMIC", assessment_id=aid)
    assert teacher.post("/dynamic/problems", json=payload).status_code == 201
    assert clients("teacher.b").post("/dynamic/problems", json=payload).status_code == 403
    assert (root / "assessments" / f"{aid}.json").read_bytes() == before
    assert "correction_mode" not in json.loads(before)["assessment"]
    assert configured_mode() == CorrectionMode.SPECIALIZED


def test_demo_requires_explicit_flag_and_records_technical_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_DYNAMIC_DIR", str(tmp_path / "dynamic"))
    monkeypatch.delenv("CONFIA_DYNAMIC_DEMO_ENABLED", raising=False)
    client = TestClient(app)
    assert client.get("/dynamic/problems").status_code == 401
    monkeypatch.setenv("CONFIA_DYNAMIC_DEMO_ENABLED", "1")
    monkeypatch.setenv("CONFIA_ENV", "development")
    doc = api_create(client)
    assert doc["problem"]["created_by"] == {"actor_id":"technical-demo:dynamic", "kind":"TECHNICAL_DEMO", "tenant_id":None}
    assert "não representa uma pessoa" in doc["actor_notice"]
    monkeypatch.setenv("CONFIA_ENV", "staging")
    assert client.get("/dynamic/problems").status_code == 401
