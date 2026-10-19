"""P2-DEC-01: institutional decisions, immutable final content and student privacy."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
from pathlib import Path

import pytest

import confia_lean_auditor.main as main
from confia_lean_auditor.core.schemas import RubricItemResult
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.auth.store import AuthStore
from confia_lean_auditor.institutional.models import Enrollment
from confia_lean_auditor.institutional.store import InstitutionalStore, current_academic_year
from confia_lean_auditor.teacher_decisions import service
from confia_lean_auditor.teacher_decisions.models import CreateDecision, TeacherDecision, suggested_points
from confia_lean_auditor.teacher_decisions.store import decision_hash, decision_store
from test_assessments import prepare, prepare_demo_seed
from test_core_auth import PASSWORD, auth_case, student_payload
from test_submission_audits import accept, result
from test_transcriptions import segments


@pytest.fixture
def case(auth_case, monkeypatch):
    _, users, clients, root = auth_case
    monkeypatch.setenv("CONFIA_ASSESSMENTS_DIR", str(root / "assessments"))
    teacher, student = clients("teacher.a"), clients("student.a")
    aid, iid = prepare(teacher)
    assert teacher.post(f"/assessments/{aid}/publish").status_code == 200
    body = student_payload("snapshot:decision-q1")
    body.pop("submitted_by_user_id")
    sent = student.post(f"/assessments/{aid}/items/{iid}/submissions", json=body)
    assert sent.status_code == 201, sent.text
    sid = sent.json()["submission_id"]
    return dict(teacher=teacher, student=student, clients=clients, users=users, root=root,
                aid=aid, iid=iid, sid=sid, target=f"/submissions/{sid}/teacher-decision",
                result_url=f"/student/assessments/{aid}/items/{iid}/result")


def audited(case, monkeypatch, score=8, maximum=10, *, technical=False, fail=False):
    def engine(request):
        if fail:
            raise RuntimeError("private diagnostic")
        response = result(request.problem_id)
        response.score, response.max_score = score, maximum
        response.feedback = "CONFIA_PRIVATE_FEEDBACK"
        if technical:
            response.rubric_assessment.items = [RubricItemResult(id="technical", description="Verificação",
                detected=False, points=None, max_points=10, verification_status="technical_error")]
        (Path(response.artifact_dir) / "audit.json").write_text(response.model_dump_json())
        return response
    monkeypatch.setattr(main, "execute_audit", engine)
    teacher = case["teacher"]
    revision = teacher.post(f"/submissions/{case['sid']}/transcriptions", json={
        "reviewer_reference": "teacher-test", "segments": segments(), "status": "NEEDS_REVIEW"}).json()
    binding = accept(teacher, case["sid"], revision)
    response = teacher.post(f"/submissions/{case['sid']}/audits", json=binding)
    assert response.status_code == 200, response.text
    return response.json(), revision


def draft(case, run=None):
    response = case["teacher"].post(case["target"], json={"audit_run_id": run["audit_run_id"]} if run else {})
    assert response.status_code in (200, 201), response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()


def patch(case, decision, **changes):
    return case["teacher"].patch(f"/teacher-decisions/{decision['decision_id']}",
        json={"expected_version": decision["version"], **changes})


def finalize(case, decision):
    return case["teacher"].post(f"/teacher-decisions/{decision['decision_id']}/finalize",
        json={"expected_version": decision["version"]})


def release(case, decision):
    return case["teacher"].post(f"/teacher-decisions/{decision['decision_id']}/release")


def finalized(case, run=None, points="4.00", reason=None):
    decision = draft(case, run)
    saved = patch(case, decision, teacher_final_points=points, teacher_feedback="Boa solução…",
                  teacher_internal_note="PRIVATE_NOTE", override_reason=reason)
    assert saved.status_code == 200, saved.text
    response = finalize(case, saved.json())
    assert response.status_code == 200, response.text
    return response.json()


def test_authorized_draft_binding_and_idempotent_creation(case):
    assert case["teacher"].get(case["target"]).json() is None
    decision = draft(case)
    assert decision["status"] == "DRAFT" and decision["teacher_final_points"] is None
    assert decision["confia_suggested_points"] is None
    assert (decision["submission_id"], decision["assessment_id"], decision["assessment_item_id"],
            decision["problem_id"], decision["teacher_user_id"]) == (
        case["sid"], case["aid"], case["iid"], "ITA2025F2Q1", case["users"]["teacher"].user_id)
    assert Decimal(decision["item_max_points"]) == 5
    assert draft(case) == decision
    assert case["teacher"].get(case["target"]).json() == decision
    assert len(list(decision_store().root.glob("dec_*.json"))) == 1


@pytest.mark.parametrize("field,value", [("submission_id", "forged"), ("assessment_id", "forged"),
    ("assessment_item_id", "forged"), ("problem_id", "forged"), ("student_user_id", "forged"),
    ("classroom_id", "forged"), ("teacher_user_id", "forged"), ("item_max_points", 100),
    ("confia_suggested_points", 5), ("audit_result_sha256", "a" * 64), ("status", "RELEASED")])
def test_client_cannot_supply_binding_or_provenance(case, field, value):
    assert case["teacher"].post(case["target"], json={field: value}).status_code == 422
    decision = draft(case)
    assert patch(case, decision, **{field: value}).status_code == 422
    assert case["teacher"].get(case["target"]).json() == decision


@pytest.mark.parametrize("login", ["teacher.b", "student.a", "student.b", "manager.a"])
def test_roles_and_classroom_scope_apply_to_every_teacher_endpoint(case, login):
    decision = draft(case)
    client = case["clients"](login)
    assert client.post(case["target"], json={}).status_code == 403
    assert client.get(case["target"]).status_code == 403
    base = f"/teacher-decisions/{decision['decision_id']}"
    assert client.patch(base, json={"expected_version": 1, "teacher_final_points": 5}).status_code == 403
    assert client.post(base + "/finalize", json={"expected_version": 1}).status_code == 403
    assert client.post(base + "/release").status_code == 403


def test_same_tenant_without_active_assignment_and_revocation_are_denied(case):
    AuthStore(case["root"] / "auth").create_user(login="teacher.same", display_name="Professor", role=Role.TEACHER,
        password=PASSWORD, tenant_id="school-a", classroom_ids=["class-a"])
    assert case["clients"]("teacher.same").post(case["target"], json={}).status_code == 403
    decision = draft(case)
    institutions = InstitutionalStore(case["root"] / "institutional")
    data = institutions.snapshot()
    data.teacher_assignments[0].active = False
    institutions.replace(data)
    assert case["teacher"].get(case["target"]).status_code == 403
    assert patch(case, decision, teacher_final_points=4).status_code == 403
    assert finalize(case, decision).status_code == 403
    assert release(case, decision).status_code == 403


def test_unauthenticated_and_disabled_auth_never_create_decisions(case, monkeypatch):
    assert case["clients"]().post(case["target"], json={}).status_code == 401
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "0")
    assert case["clients"]().post(case["target"], json={}).status_code == 401


def test_normalization_copy_suggestion_does_not_finalize_or_mutate_audit(case, monkeypatch):
    run, _ = audited(case, monkeypatch)
    audit_path = case["root"] / "audits" / f"{run['audit_run_id']}.json"
    original = audit_path.read_bytes()
    decision = draft(case, run)
    assert Decimal(decision["confia_score_raw"]) == 8
    assert Decimal(decision["confia_max_score_raw"]) == 10
    assert decision["confia_suggested_points"] == "4.00"
    assert decision["teacher_final_points"] is None
    saved = patch(case, decision, teacher_final_points=decision["confia_suggested_points"]).json()
    assert saved["status"] == "DRAFT"
    final = finalize(case, saved)
    assert final.status_code == 200 and final.json()["override_reason"] is None
    assert release(case, final.json()).status_code == 200
    assert audit_path.read_bytes() == original


@pytest.mark.parametrize("score,maximum,technical,fail", [(None, 10, False, False),
    (8, 10, True, False), (8, 0, False, False), (8, 10, False, True)])
def test_manual_finalization_without_usable_confia_score(case, monkeypatch, score, maximum, technical, fail):
    run, _ = audited(case, monkeypatch, score, maximum, technical=technical, fail=fail)
    decision = draft(case, run)
    assert decision["confia_suggested_points"] is None
    saved = patch(case, decision, teacher_final_points="3.75").json()
    assert finalize(case, saved).status_code == 200


@pytest.mark.parametrize("points", [-1, 5.01, "0.001", "NaN", "Infinity", True])
def test_invalid_teacher_points_are_rejected(case, points):
    decision = draft(case)
    response = patch(case, decision, teacher_final_points=points)
    assert response.status_code == 422, response.text
    assert case["teacher"].get(case["target"]).json() == decision


@pytest.mark.parametrize("points", ["0", "0.01", "3.75", "5.00"])
def test_decimal_bounds_accepted(case, points):
    decision = draft(case)
    saved = patch(case, decision, teacher_final_points=points)
    assert saved.status_code == 200
    assert Decimal(saved.json()["teacher_final_points"]) == Decimal(points)
    assert finalize(case, saved.json()).status_code == 200


def test_decimal_rounding_policy():
    assert suggested_points(Decimal("5"), Decimal("1"), Decimal("3")) == Decimal("1.67")
    assert suggested_points(Decimal("5"), Decimal("0.669"), Decimal("1")) == Decimal("3.35")
    assert suggested_points(Decimal("4.999"), Decimal("10"), Decimal("10")) == Decimal("4.99")


def test_override_requires_nonblank_reason_only_at_finalization(case, monkeypatch):
    run, _ = audited(case, monkeypatch)
    decision = draft(case, run)
    assert finalize(case, decision).status_code == 409
    saved = patch(case, decision, teacher_final_points="3.50", override_reason="  ").json()
    assert saved["status"] == "DRAFT"
    response = finalize(case, saved)
    assert response.status_code == 409 and "Justifique" in response.text
    saved = patch(case, saved, override_reason="Argumento parcial superestimado").json()
    assert finalize(case, saved).status_code == 200


def test_freeze_release_idempotency_hash_and_student_projection(case, monkeypatch):
    run, _ = audited(case, monkeypatch)
    decision = draft(case, run)
    assert release(case, decision).status_code == 409
    assert case["student"].get(case["result_url"]).json() is None
    final = finalized(case, run, points="3.75", reason="PRIVATE_OVERRIDE")
    assert case["student"].get(case["result_url"]).json() is None
    assert case["student"].get(f"/assessments/{case['aid']}").json()["released_results"] == []
    assert patch(case, final, teacher_feedback="replacement").status_code == 409
    assert patch(case, final, audit_run_id=None).status_code == 409
    assert finalize(case, final).json() == final
    stored = decision_store().get(final["decision_id"])
    assert stored.decision_sha256 == decision_hash(stored)
    released = release(case, final).json()
    differences = {key for key in released if released[key] != final[key]}
    assert differences == {"status", "released_at", "updated_at", "version"}
    assert release(case, released).json() == released
    assert patch(case, released, teacher_final_points=0).status_code == 409
    response = case["student"].get(case["result_url"])
    assert response.headers["cache-control"] == "no-store"
    expected = dict(assessment_id=case["aid"], item_id=case["iid"], problem_id="ITA2025F2Q1", status="corrected",
        final_points="3.75", max_points="5.0", teacher_feedback="Boa solução…", released_at=released["released_at"])
    assert response.json() == expected
    assert case["student"].get(f"/assessments/{case['aid']}").json()["released_results"] == [expected]
    assert case["student"].get("/assessments").json()[0]["released_results"] == [expected]
    for url in (case["result_url"], f"/assessments/{case['aid']}", "/assessments"):
        body = case["student"].get(url).text
        for forbidden in ("audit_run_id", "confia_score", "confia_suggested_points", "confia_max_score_raw",
                          "claims", "evidence", "lean_status", "override_reason", "teacher_internal_note",
                          "PRIVATE_NOTE", "PRIVATE_OVERRIDE", "CONFIA_PRIVATE_FEEDBACK", "decision_sha256"):
            assert forbidden not in body


def test_other_student_even_in_same_class_cannot_see_result(case):
    final = finalized(case)
    assert release(case, final).status_code == 200
    other = AuthStore(case["root"] / "auth").create_user(login="student.peer", display_name="Colega", role=Role.STUDENT,
        password=PASSWORD, tenant_id="school-a", classroom_ids=["class-a"])
    institutions = InstitutionalStore(case["root"] / "institutional")
    data = institutions.snapshot()
    data.enrollments.append(Enrollment(student_user_id=other.user_id, school_id="school-a", classroom_id="class-a",
        academic_year=current_academic_year()))
    institutions.replace(data)
    peer = case["clients"]("student.peer")
    assert peer.get(case["result_url"]).json() is None
    assert peer.get(f"/assessments/{case['aid']}").json()["released_results"] == []
    assert peer.get(case["target"]).status_code == 403
    assert case["clients"]("student.b").get(case["result_url"]).status_code == 404
    assert case["teacher"].get(case["result_url"]).status_code == 403
    assert case["clients"]("manager.a").get(case["result_url"]).status_code == 403


def make_stale(case, revision):
    response = case["teacher"].post(f"/transcriptions/{revision['transcription_id']}/revisions", json={
        "based_on_revision_number": revision["revision_number"], "reviewer_reference": "teacher-test",
        "segments": segments(), "status": "NEEDS_REVIEW"})
    assert response.status_code == 201, response.text


def test_stale_run_requires_explicit_manual_choice_or_current_run(case, monkeypatch):
    run, revision = audited(case, monkeypatch)
    decision = draft(case, run)
    saved = patch(case, decision, teacher_final_points=4).json()
    make_stale(case, revision)
    assert case["teacher"].get(case["target"]).json()["audit_state"] == "stale"
    assert finalize(case, saved).status_code == 409
    assert patch(case, saved, audit_run_id=run["audit_run_id"]).status_code == 409
    manual = patch(case, saved, audit_run_id=None).json()
    assert manual["audit_run_id"] is None and manual["confia_suggested_points"] is None
    assert finalize(case, manual).status_code == 200


def test_stale_run_cannot_create_draft(case, monkeypatch):
    run, revision = audited(case, monkeypatch)
    make_stale(case, revision)
    assert case["teacher"].post(case["target"], json={"audit_run_id": run["audit_run_id"]}).status_code == 409
    assert draft(case)["audit_run_id"] is None


def test_multiple_runs_require_explicit_selection_and_do_not_rebind_on_retry(case, monkeypatch):
    first, _ = audited(case, monkeypatch, score=8)
    second, _ = audited(case, monkeypatch, score=6)
    assert case["teacher"].post(case["target"], json={"audit_run_id": first["audit_run_id"]}).status_code == 409
    decision = draft(case, second)
    assert decision["audit_run_id"] == second["audit_run_id"] and decision["confia_suggested_points"] == "3.00"
    assert draft(case, first) == decision  # Retry returns existing; never changes provenance.


def test_run_from_another_submission_is_rejected(case, monkeypatch):
    run, _ = audited(case, monkeypatch)
    body = student_payload("snapshot:other-manuscript"); body.pop("submitted_by_user_id")
    legacy_id = case["student"].post("/submissions", json=body).json()["submission_id"]
    foreign_run, _ = audited({**case, "sid": legacy_id}, monkeypatch)
    assert case["teacher"].post(case["target"], json={"audit_run_id": foreign_run["audit_run_id"]}).status_code == 409
    assert draft(case, run)["audit_run_id"] == run["audit_run_id"]


def test_multiple_current_runs_are_never_automatically_selected(case, monkeypatch):
    first, _ = audited(case, monkeypatch)
    body = {key: first[key] for key in ("transcription_id", "revision_number", "acceptance_id")}
    second = case["teacher"].post(f"/submissions/{case['sid']}/audits", json={**body, "execution_key": "explicit-rerun"}).json()
    assert first["audit_run_id"] != second["audit_run_id"]
    assert first["stale"] is False and second["stale"] is False
    manual = draft(case)
    assert manual["audit_run_id"] is None
    selected = patch(case, manual, audit_run_id=first["audit_run_id"]).json()
    assert selected["audit_run_id"] == first["audit_run_id"]
    assert draft(case, second)["audit_run_id"] == first["audit_run_id"]
    assert patch(case, selected, audit_run_id=second["audit_run_id"]).json()["audit_run_id"] == second["audit_run_id"]


def test_release_preserves_final_decision_even_if_audit_later_stale(case, monkeypatch):
    run, revision = audited(case, monkeypatch)
    final = finalized(case, run)
    make_stale(case, revision)
    released = release(case, final)
    assert released.status_code == 200 and released.json()["decision_sha256"] == final["decision_sha256"]
    assert released.json()["audit_state"] == "stale"


def test_unavailable_audit_allows_explicit_manual_draft(case, monkeypatch):
    run, _ = audited(case, monkeypatch)
    decision = draft(case, run)
    (case["root"] / "audits" / f"{run['audit_run_id']}.json").write_text("{}")
    assert case["teacher"].get(case["target"]).json()["audit_state"] == "unavailable"
    manual = patch(case, decision, audit_run_id=None, teacher_final_points=4)
    assert manual.status_code == 200
    assert finalize(case, manual.json()).status_code == 200


def test_concurrent_creation_and_optimistic_edit_conflict(case):
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: service.create(case["users"]["teacher"], case["sid"], CreateDecision()), range(8)))
    assert sum(created for _, created in results) == 1
    assert len({decision.decision_id for decision, _ in results}) == 1
    decision = draft(case)
    assert patch(case, decision, teacher_final_points=4).status_code == 200
    assert patch(case, decision, teacher_final_points=2).status_code == 409
    assert finalize(case, decision).status_code == 409
    assert case["teacher"].get(case["target"]).json()["teacher_final_points"] == "4.00"


@pytest.mark.parametrize("field,value", [("teacher_feedback", "tampered"), ("teacher_internal_note", "tampered"),
    ("teacher_final_points", "1.00"), ("override_reason", "tampered"), ("submission_id", "sub_" + "f" * 32),
    ("finalized_at", "2000-01-01T00:00:00Z")])
def test_finalized_corruption_is_rejected_on_read_and_release(case, field, value):
    final = finalized(case)
    path = decision_store().root / f"{final['decision_id']}.json"
    raw = json.loads(path.read_text()); raw[field] = value; path.write_text(json.dumps(raw))
    assert case["teacher"].get(case["target"]).status_code == 409
    assert release(case, final).status_code == 409


def test_symlink_and_invalid_model_rejected(case):
    decision = draft(case)
    path = decision_store().root / f"{decision['decision_id']}.json"
    outside = case["root"] / "elsewhere.json"
    path.rename(outside); path.symlink_to(outside)
    assert case["teacher"].get(case["target"]).status_code == 409
    assert patch(case, decision, teacher_final_points=4).status_code == 409
    with pytest.raises(ValueError):
        TeacherDecision.model_validate({**decision, "status": "RELEASED"})


def test_legacy_submission_remains_readable_without_institutional_decision(case):
    body = student_payload("snapshot:legacy-decisions"); body.pop("submitted_by_user_id")
    sid = case["student"].post("/submissions", json=body).json()["submission_id"]
    assert case["student"].get(f"/submissions/{sid}").status_code == 200
    assert case["teacher"].get(f"/submissions/{sid}").status_code == 200
    assert case["teacher"].post(f"/submissions/{sid}/teacher-decision", json={}).status_code == 409


def test_teacher_progress_and_governance_are_scoped_and_aggregate_only(case, monkeypatch):
    def status():
        progress = case["teacher"].get(f"/assessments/{case['aid']}/progress")
        assert progress.status_code == 200, progress.text
        return progress.json()["students"][0]["correction_statuses"][case["iid"]]
    assert status() == "SUBMITTED"
    run, _ = audited(case, monkeypatch)
    assert status() == "ANALYSIS_AVAILABLE"
    decision = draft(case, run)
    assert status() == "DECISION_DRAFT"
    final = finalized(case, run, points="3.75", reason="PRIVATE_OVERRIDE")
    assert status() == "DECISION_FINALIZED"
    manager = case["clients"]("manager.a")
    metrics = manager.get("/management/overview").json()["metrics"]
    assert (metrics["decisions_finalized_count"], metrics["decisions_released_count"], metrics["override_count"]) == (1, 0, 1)
    release(case, final)
    assert status() == "RESULT_RELEASED"
    for url in ("/management/overview", "/management/schools", "/management/schools/school-a/classrooms"):
        response = manager.get(url)
        assert response.status_code == 200
        for forbidden in ("PRIVATE_NOTE", "PRIVATE_OVERRIDE", "Boa solução", "teacher_feedback", "audit_run_id", "decision_id"):
            assert forbidden not in response.text
    metrics = manager.get("/management/classrooms/class-b/overview").json()["metrics"]
    assert metrics["decisions_finalized_count"] == metrics["decisions_released_count"] == metrics["override_count"] == 0


def test_demo_end_to_end_submission_acceptance_analysis_finalization_release(auth_case, monkeypatch):
    _, users, clients, root = auth_case
    monkeypatch.setenv("CONFIA_ASSESSMENTS_DIR", str(root / "assessments"))
    scenario = {"root": root, "users": users, "client": clients}
    seed, _, _, _, _, _ = prepare_demo_seed(scenario)
    seed(output=lambda _: None)
    teacher, student = clients("professor.demo"), clients("aluno.demo")
    exam = next(view for view in student.get("/assessments").json() if view["assessment"]["title"] == "Avaliação 1")
    assert exam["classroom_name"] == "2ª série A"
    aid, iid = exam["assessment"]["assessment_id"], exam["items"][0]["assessment_item_id"]
    body = student_payload("snapshot:demo-decision"); body.pop("submitted_by_user_id")
    sent = student.post(f"/assessments/{aid}/items/{iid}/submissions", json=body)
    assert sent.status_code == 201
    sid = sent.json()["submission_id"]
    case = dict(teacher=teacher, student=student, root=root, aid=aid, iid=iid, sid=sid,
        target=f"/submissions/{sid}/teacher-decision")
    run, _ = audited(case, monkeypatch)
    final = finalized(case, run)
    assert Decimal(final["teacher_final_points"]) == 4
    assert student.get(f"/assessments/{aid}").json()["released_results"] == []
    assert release(case, final).status_code == 200
    result = student.get(f"/student/assessments/{aid}/items/{iid}/result").json()
    assert result["status"] == "corrected" and result["final_points"] == "4.00"
    assert result["teacher_feedback"] == "Boa solução…"
    assert student.get(f"/submissions/{sid}/audits").status_code == 403
    assert student.get(f"/submission-audits/{run['audit_run_id']}").status_code == 403
