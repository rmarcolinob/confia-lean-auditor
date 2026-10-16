"""CORE-INST-01 scope, persistence and aggregate privacy contracts."""
import json
from pathlib import Path
import runpy

from pydantic import ValidationError
import pytest

from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.institutional.models import (Classroom, Enrollment, InstitutionalData,
    ManagerAssignment, Network, School, TeacherAssignment)
from confia_lean_auditor.institutional.store import InstitutionalStore, current_academic_year
from test_core_auth import auth_case, student_payload, PASSWORD


def add_north(auth_case):
    users_store, users, client, root = auth_case
    north_student = users_store.create_user(login="student.north", display_name="Aluno Norte", role=Role.STUDENT,
        password=PASSWORD, tenant_id="school-a", classroom_ids=["class-north"])
    network_manager = users_store.create_user(login="network.manager", display_name="Gestão Rede", role=Role.NETWORK_MANAGER,
        password=PASSWORD, tenant_id="school-a")
    repository = InstitutionalStore(root / "institutional")
    data = repository.snapshot()
    year = current_academic_year()
    data.networks.append(Network(network_id="outside", name="Outra rede"))
    data.schools.append(School(school_id="outside-school", network_id="outside", name="Escola Fora",
                               code="outside", municipality="Picos"))
    data.classrooms.append(Classroom(classroom_id="class-north", school_id="school-b", name="Turma Norte",
                                     grade="3ª série", shift="Manhã", academic_year=year))
    data.enrollments.append(Enrollment(student_user_id=north_student.user_id, school_id="school-b",
                                       classroom_id="class-north", academic_year=year))
    data.teacher_assignments.append(TeacherAssignment(teacher_user_id=users["other_teacher"].user_id,
        school_id="school-b", classroom_id="class-north", academic_year=year))
    data.manager_assignments.append(ManagerAssignment(manager_user_id=network_manager.user_id, network_id="school-a"))
    repository.replace(data)
    return repository, north_student, network_manager


def test_closed_models_and_local_store(auth_case):
    _, _, _, root = auth_case
    with pytest.raises(ValidationError):
        Network(network_id="demo", name="Demo", password="forbidden")
    with pytest.raises(ValidationError):
        InstitutionalData(networks=[Network(network_id="demo", name="Demo")],
            schools=[School(school_id="bad", network_id="missing", name="Bad", code="bad", municipality="Teresina")])
    directory = root / "institutional"
    assert {path.name for path in directory.glob("*.json")} == {
        "networks.json", "schools.json", "classrooms.json", "teacher_assignments.json",
        "enrollments.json", "manager_assignments.json"}
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in directory.glob("*.json"))
    repository = InstitutionalStore(directory)
    changed = repository.snapshot()
    changed.schools.append(School(school_id="orphan", network_id="missing", name="Órfã",
                                  code="orphan", municipality="Teresina"))
    with pytest.raises(ValidationError):
        repository.replace(changed)


def test_demo_seed_is_idempotent_and_uses_auth_identity(auth_case):
    users_store, _, _, root = auth_case
    for login, role in (("aluno.demo", Role.STUDENT), ("professor.demo", Role.TEACHER),
                        ("gestao.demo", Role.SCHOOL_MANAGER), ("rede.demo", Role.NETWORK_MANAGER)):
        users_store.create_user(login=login, display_name=login, role=role, password=PASSWORD, tenant_id="demo-pi")
    module = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "create_demo_institutional_data.py"))
    seed = module["create_demo_institutional_data"]
    seed.__globals__["auth_store"] = lambda: users_store
    seed.__globals__["institutional_store"] = lambda: InstitutionalStore(root / "institutional")
    seed(output=lambda _: None); seed(output=lambda _: None)
    data = InstitutionalStore(root / "institutional").snapshot()
    assert len(data.networks) == 2  # Existing test network plus demo network.
    assert len([s for s in data.schools if s.network_id == "demo-pi"]) == 2
    assert len([c for c in data.classrooms if c.school_id.startswith("ceti-")]) == 3
    assert len([a for a in data.teacher_assignments if a.school_id == "ceti-centro"]) == 2
    assert len([e for e in data.enrollments if e.school_id == "ceti-centro"]) == 1
    assert len([a for a in data.manager_assignments if a.network_id == "demo-pi"]) == 1


def test_teacher_assignments_student_enrollment_and_legacy_scope(auth_case):
    users_store, users, client, root = auth_case
    repository, north_student, _ = add_north(auth_case)
    teacher = client("teacher.a")
    teacher_north = client("teacher.b")
    student = client("student.a")
    student_north = client("student.north")
    anonymous = client()
    assert anonymous.get("/institutional/me/context").status_code == 401
    assert [s["school_id"] for s in teacher.get("/institutional/me/schools").json()] == ["school-a"]
    assert teacher.get("/institutional/schools/school-b/classrooms").status_code == 403
    assert [c["classroom_id"] for c in teacher.get("/institutional/schools/school-a/classrooms").json()] == ["class-a"]
    assert [c["classroom_id"] for c in student.get("/institutional/me/context").json()["classrooms"]] == ["class-a"]
    assert student.get("/institutional/schools/school-b/classrooms").status_code == 403
    assert student.get("/submissions?school_id=school-b").status_code == 403
    assert teacher.get("/institutional/classrooms/class-north/students").status_code == 403
    assert teacher_north.get("/institutional/classrooms/class-north/students").json() == [
        {"user_id": north_student.user_id, "display_name": "Aluno Norte"}]
    body = student_payload("snapshot:institutional-a")
    body.pop("submitted_by_user_id")
    assert student.post("/submissions", json={**body, "school_id": "school-b"}).status_code == 422
    receipt = student.post("/submissions", json=body)
    assert receipt.status_code == 201, receipt.text
    sid = receipt.json()["submission_id"]
    assert {key: receipt.json()[key] for key in ("network_id", "school_id", "classroom_id", "submitted_by_user_id")} == {
        "network_id": "school-a", "school_id": "school-a", "classroom_id": "class-a",
        "submitted_by_user_id": users["student_a"].user_id}
    assert teacher.get(f"/submissions/{sid}").status_code == 200
    assert teacher_north.get(f"/submissions/{sid}").status_code == 403
    assert student_north.get(f"/submissions/{sid}").status_code == 403
    assert teacher.get("/submissions?school_id=school-b").status_code == 403
    assert teacher.get("/submissions?school_id=school-a&classroom_id=class-b").status_code == 403
    assert [r["submission_id"] for r in teacher.get("/submissions?school_id=school-a&classroom_id=class-a").json()] == [sid]
    data = repository.snapshot()
    data.teacher_assignments.append(TeacherAssignment(teacher_user_id=users["teacher"].user_id,
        school_id="school-b", classroom_id="class-north", academic_year=current_academic_year()))
    repository.replace(data)
    assert [s["school_id"] for s in teacher.get("/institutional/me/schools").json()] == ["school-a", "school-b"]
    assert [c["classroom_id"] for c in teacher.get("/institutional/schools/school-b/classrooms").json()] == ["class-north"]
    assert teacher.get("/submissions?school_id=school-b&classroom_id=class-north").json() == []
    old = json.loads((root / "submissions" / sid / "submission.json").read_text())
    assert old["school_id"] == "school-a" and old["classroom_id"] == "class-a"


def test_management_real_zero_and_scoped_aggregates_without_individual_content(auth_case):
    _, _, client, _ = auth_case
    add_north(auth_case)
    manager = client("manager.a")
    network = client("network.manager")
    teacher = client("teacher.a")
    student = client("student.a")
    assert teacher.get("/management/schools").status_code == 403
    assert student.get("/management/network/overview").status_code == 403
    assert manager.get("/management/network/overview").status_code == 403
    assert manager.get("/management/schools/school-b/overview").status_code == 403
    assert manager.get("/management/classrooms/class-north/overview").status_code == 403
    assert [r["school"]["school_id"] for r in manager.get("/management/schools").json()] == ["school-a"]
    assert [r["school"]["school_id"] for r in network.get("/management/schools").json()] == ["school-a", "school-b"]
    assert network.get("/management/schools/outside-school/overview").status_code == 403
    overview = network.get("/management/network/overview")
    assert overview.status_code == 200
    metrics = overview.json()["metrics"]
    assert (metrics["number_of_schools"], metrics["number_of_classrooms"], metrics["number_of_students"],
            metrics["number_of_teachers"], metrics["submissions_count"]) == (2, 3, 3, 2, 0)
    assert metrics["audit_runs_count"] == 0 and metrics["recognition_failure_count"] == 0
    assert "teacher_final_score" not in overview.text
    for forbidden in ("png_base64", "snapshot_json", "solution_text", "transcription_text", "page_images"):
        assert forbidden not in overview.text
    body = student_payload("snapshot:aggregate-a"); body.pop("submitted_by_user_id")
    assert student.post("/submissions", json=body).status_code == 201
    sid = student.get("/submissions").json()[0]["submission_id"]
    assert network.get("/submissions").status_code == 403
    assert network.get(f"/submissions/{sid}").status_code == 403
    scoped = manager.get("/management/schools/school-a/overview").json()["metrics"]
    assert scoped["submissions_count"] == 1
    assert manager.get("/management/classrooms/class-a/overview").json()["metrics"]["submissions_count"] == 1
    assert manager.get("/management/classrooms/class-b/overview").json()["metrics"]["submissions_count"] == 0
    assert network.get("/management/network/overview").json()["metrics"]["submissions_count"] == 1


def test_student_exams_require_explicit_classroom_availability(auth_case):
    _, _, client, root = auth_case
    student_a = client("student.a")
    student_b = client("student.b")
    teacher = client("teacher.a")
    assert student_a.get("/institutional/me/exams").json() == []
    assert client().get("/institutional/me/exams").status_code == 401
    assert teacher.get("/institutional/me/exams").status_code == 403
    year = current_academic_year()
    exams = [
        {"exam_id": "activity-a", "title": "Atividade da turma A", "school_id": "school-a",
         "classroom_id": "class-a", "academic_year": year, "problem_ids": ["ITA2025Q1"]},
        {"exam_id": "activity-b", "title": "Atividade da turma B", "school_id": "school-a",
         "classroom_id": "class-b", "academic_year": year, "problem_ids": ["ITA2025Q1"]},
        {"exam_id": "invalid-catalog", "title": "Questão indisponível", "school_id": "school-a",
         "classroom_id": "class-a", "academic_year": year, "problem_ids": ["NOT_A_PROBLEM"]},
    ]
    (root / "institutional" / "exams.json").write_text(json.dumps(exams))
    assert [item["exam_id"] for item in student_a.get("/institutional/me/exams").json()] == ["activity-a"]
    assert [item["exam_id"] for item in student_b.get("/institutional/me/exams").json()] == ["activity-b"]
