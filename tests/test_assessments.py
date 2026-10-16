"""P2-ASSMT-01 API, institutional scope, immutable definition and real Submission binding."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import runpy

import pytest

from confia_lean_auditor.assessments.store import AssessmentStore, definition_hash
from confia_lean_auditor.submissions.store import SubmissionStore
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.submissions import router as submissions_router
from test_recognition_preview import PreviewAdapter
from test_core_auth import PASSWORD, auth_case, student_payload


@pytest.fixture
def scenario(auth_case, monkeypatch):
    store, users, client, root = auth_case
    monkeypatch.setenv("CONFIA_ASSESSMENTS_DIR", str(root / "assessments"))
    return {"users": users, "client": client, "root": root}


def create(client, *, start=None, end=None):
    now = datetime.now(timezone.utc)
    body = {"title": "Prova da turma", "instructions": "Mostre as etapas.",
            "school_id": "school-a", "classroom_id": "class-a",
            "opens_at": (start or now - timedelta(minutes=5)).isoformat(),
            "closes_at": (end or now + timedelta(days=7)).isoformat()}
    return client.post("/assessments", json=body)


def prepare(client):
    draft = create(client)
    assert draft.status_code == 201, draft.text
    assessment_id = draft.json()["assessment"]["assessment_id"]
    item = client.post(f"/assessments/{assessment_id}/items", json={"problem_id": "ITA2025F2Q1", "points": 5})
    assert item.status_code == 201, item.text
    return assessment_id, item.json()["items"][0]["assessment_item_id"]


def test_assessment_scope_publish_and_immutability(scenario):
    client = scenario["client"]
    teacher, student, other_student = client("teacher.a"), client("student.a"), client("student.b")
    outsider, manager = client("teacher.b"), client("manager.a")
    assessment_id, item_id = prepare(teacher)
    assert student.get("/assessments").json() == []  # DRAFT hidden.
    assert outsider.post("/assessments", json={"title": "x", "school_id": "school-a", "classroom_id": "class-a",
        "opens_at": datetime.now(timezone.utc).isoformat(), "closes_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()}).status_code == 403
    assert manager.get("/assessments").status_code == 403
    assert student.post("/assessments", json={}).status_code == 403
    assert teacher.post(f"/assessments/{assessment_id}/items", json={"problem_id": "DOES_NOT_EXIST", "points": 5}).status_code == 422
    published = teacher.post(f"/assessments/{assessment_id}/publish")
    assert published.status_code == 200, published.text
    digest = published.json()["assessment"]["definition_sha256"]
    document = AssessmentStore(scenario["root"] / "assessments").get(assessment_id)
    assert digest == definition_hash(document)
    assert teacher.get(f"/assessments/{assessment_id}").json()["assessment"]["definition_sha256"] == digest
    assert teacher.patch(f"/assessments/{assessment_id}", json={"title": "troca"}).status_code == 409
    assert teacher.patch(f"/assessments/{assessment_id}/items/{item_id}", json={"points": 8}).status_code == 409
    assert teacher.delete(f"/assessments/{assessment_id}/items/{item_id}").status_code == 409
    visible = student.get("/assessments")
    assert visible.status_code == 200 and [view["assessment"]["assessment_id"] for view in visible.json()] == [assessment_id]
    assert other_student.get("/assessments").json() == []
    assert other_student.get(f"/assessments/{assessment_id}").status_code == 404
    assert outsider.get(f"/assessments/{assessment_id}").status_code == 403


def test_bound_submission_single_item_and_teacher_progress(scenario):
    client = scenario["client"]
    teacher, student, other_student = client("teacher.a"), client("student.a"), client("student.b")
    assessment_id, item_id = prepare(teacher)
    assert teacher.post(f"/assessments/{assessment_id}/publish").status_code == 200
    target = f"/assessments/{assessment_id}/items/{item_id}/submissions"
    body = student_payload("snapshot:assessment-q1")
    body.pop("submitted_by_user_id")
    forged = {**body, "assessment_id": assessment_id, "assessment_item_id": item_id}
    assert student.post(target, json=forged).status_code == 422
    wrong = student_payload("snapshot:wrong-problem")
    wrong.pop("submitted_by_user_id")
    snapshot = json.loads(wrong["snapshot_json"])
    snapshot["problem_id"] = "ITA2025F2Q3"
    wrong["snapshot_json"] = json.dumps(snapshot, ensure_ascii=False)
    assert student.post(target, json=wrong).status_code == 409
    before = student.get("/assessments").json()[0]
    assert before["submitted_item_ids"] == []
    sent = student.post(target, json=body)
    assert sent.status_code == 201, sent.text
    receipt = sent.json()
    assert receipt["assessment_id"] == assessment_id
    assert receipt["assessment_item_id"] == item_id
    assert receipt["assessment_definition_sha256"] == before["assessment"]["definition_sha256"]
    assert receipt["problem_id"] == "ITA2025F2Q1"
    assert receipt["submitted_by_user_id"] == scenario["users"]["student_a"].user_id
    assert (receipt["network_id"], receipt["school_id"], receipt["classroom_id"]) == ("school-a", "school-a", "class-a")
    assert student.post(target, json=body).status_code == 200
    another = student_payload("snapshot:assessment-q1-second")
    another.pop("submitted_by_user_id")
    assert student.post(target, json=another).status_code == 409
    assert student.post("/submissions", json=body).status_code == 409
    assert other_student.post(target, json=another).status_code == 404
    assert len(SubmissionStore(scenario["root"] / "submissions").list()) == 1
    progress = teacher.get(f"/assessments/{assessment_id}/progress")
    assert progress.status_code == 200, progress.text
    row = next(row for row in progress.json()["students"] if row["user_id"] == scenario["users"]["student_a"].user_id)
    assert row["submissions"][item_id] == receipt["submission_id"]
    assert teacher.get(f"/submissions/{receipt['submission_id']}").status_code == 200
    assert student.get("/assessments").json()[0]["submitted_item_ids"] == [item_id]
    scoped = "?school_id=school-a&classroom_id=class-a"
    assert [view["assessment"]["assessment_id"] for view in teacher.get(f"/assessments{scoped}").json()] == [assessment_id]
    assert [record["submission_id"] for record in teacher.get(f"/submissions{scoped}").json()] == [receipt["submission_id"]]
    assert teacher.get("/institutional/classrooms/class-a/students").status_code == 200
    outsider = client("teacher.b")
    assert outsider.get(f"/assessments{scoped}").status_code == 403
    assert outsider.get(f"/submissions{scoped}").status_code == 403
    assert outsider.get("/institutional/classrooms/class-a/students").status_code == 403


def test_student_progress_uses_only_own_official_item_submissions(scenario):
    from confia_lean_auditor.auth.models import Role
    from confia_lean_auditor.auth.store import AuthStore
    from confia_lean_auditor.institutional.models import Enrollment
    from confia_lean_auditor.institutional.store import InstitutionalStore, current_academic_year

    root = scenario["root"]
    other = AuthStore(root / "auth").create_user(login="student.c", display_name="Aluno C",
        role=Role.STUDENT, password=PASSWORD, tenant_id="school-a", classroom_ids=["class-a"])
    institution = InstitutionalStore(root / "institutional")
    data = institution.snapshot()
    data.enrollments.append(Enrollment(student_user_id=other.user_id, school_id="school-a",
        classroom_id="class-a", academic_year=current_academic_year()))
    institution.replace(data)
    teacher = scenario["client"]("teacher.a")
    student = scenario["client"]("student.a")
    other_student = scenario["client"]("student.c")
    assessment_a, item_a1 = prepare(teacher)
    item_a2 = teacher.post(f"/assessments/{assessment_a}/items", json={
        "problem_id": "ITA2025F2Q3", "points": 5}).json()["items"][1]["assessment_item_id"]
    assessment_b, _ = prepare(teacher)
    teacher.post(f"/assessments/{assessment_b}/items", json={"problem_id": "ITA2025F2Q3", "points": 5})
    assert teacher.post(f"/assessments/{assessment_a}/publish").status_code == 200
    assert teacher.post(f"/assessments/{assessment_b}/publish").status_code == 200
    repository = AssessmentStore(root / "assessments")
    hashes = {assessment_id: repository.get(assessment_id).assessment.definition_sha256
              for assessment_id in (assessment_a, assessment_b)}

    def sent_ids(client, assessment_id):
        response = client.get(f"/assessments/{assessment_id}")
        assert response.status_code == 200, response.text
        return response.json()["submitted_item_ids"]

    assert sent_ids(student, assessment_a) == []
    assert sent_ids(student, assessment_b) == []
    assert sent_ids(other_student, assessment_a) == []
    body = student_payload("snapshot:progress-q1")
    body.pop("submitted_by_user_id")
    target_a1 = f"/assessments/{assessment_a}/items/{item_a1}/submissions"
    first = student.post(target_a1, json=body)
    assert first.status_code == 201, first.text
    assert sent_ids(student, assessment_a) == [item_a1]
    assert sent_ids(student, assessment_b) == []
    assert sent_ids(other_student, assessment_a) == []
    assert student.post(target_a1, json=body).status_code == 200
    assert sent_ids(student, assessment_a) == [item_a1]

    legacy = student_payload("snapshot:progress-legacy")
    legacy.pop("submitted_by_user_id")
    assert student.post("/submissions", json=legacy).status_code == 201
    assert sent_ids(student, assessment_a) == [item_a1]
    assert sent_ids(student, assessment_b) == []

    fresh_session = scenario["client"]("student.a")
    assert sent_ids(fresh_session, assessment_a) == [item_a1]
    assert student.post("/auth/logout").status_code == 204
    assert student.get(f"/assessments/{assessment_a}").status_code == 401
    assert student.post("/auth/login", json={"login": "student.a", "password": PASSWORD}).status_code == 200
    assert sent_ids(student, assessment_a) == [item_a1]
    body_q2 = student_payload("snapshot:progress-q2")
    body_q2.pop("submitted_by_user_id")
    snapshot = json.loads(body_q2["snapshot_json"])
    snapshot["problem_id"] = "ITA2025F2Q3"
    body_q2["snapshot_json"] = json.dumps(snapshot, ensure_ascii=False)
    second = fresh_session.post(f"/assessments/{assessment_a}/items/{item_a2}/submissions", json=body_q2)
    assert second.status_code == 201, second.text
    assert sent_ids(student, assessment_a) == [item_a1, item_a2]
    assert sent_ids(student, assessment_b) == []
    assert sent_ids(other_student, assessment_a) == []
    progress = teacher.get(f"/assessments/{assessment_a}/progress").json()
    row = next(entry for entry in progress["students"] if entry["user_id"] == scenario["users"]["student_a"].user_id)
    assert row["submissions"] == {item_a1: first.json()["submission_id"], item_a2: second.json()["submission_id"]}
    assert {assessment_id: repository.get(assessment_id).assessment.definition_sha256
            for assessment_id in (assessment_a, assessment_b)} == hashes


def test_window_blocks_new_delivery(scenario):
    client = scenario["client"]
    teacher, student = client("teacher.a"), client("student.a")
    now = datetime.now(timezone.utc)
    draft = create(teacher, start=now + timedelta(days=1), end=now + timedelta(days=2))
    assert draft.status_code == 201
    assessment_id = draft.json()["assessment"]["assessment_id"]
    item = teacher.post(f"/assessments/{assessment_id}/items", json={"problem_id": "ITA2025F2Q1", "points": 5}).json()["items"][0]
    assert teacher.post(f"/assessments/{assessment_id}/publish").status_code == 200
    target = f"/assessments/{assessment_id}/items/{item['assessment_item_id']}/submissions"
    assert student.post(target, json=student_payload("snapshot:too-early")).status_code == 409
    assert teacher.post(f"/assessments/{assessment_id}/close").status_code == 200
    assert student.post(target, json=student_payload("snapshot:closed")).status_code == 409


def test_assessment_uses_existing_hmer_and_teacher_detail(scenario, monkeypatch):
    registry = RecognizerRegistry()
    registry.register("mathpix", PreviewAdapter)
    monkeypatch.setattr(submissions_router, "configured_registry", lambda: registry)
    teacher, student = scenario["client"]("teacher.a"), scenario["client"]("student.a")
    assessment_id, item_id = prepare(teacher)
    assert teacher.post(f"/assessments/{assessment_id}/publish").status_code == 200
    body = student_payload("snapshot:exam-hmer")
    body.pop("submitted_by_user_id")
    preview = student.post("/submissions/recognition-preview", json={
        "snapshot_json": body["snapshot_json"], "client_preview_id": "preview:exam-hmer"})
    assert preview.status_code == 200, preview.text
    assert teacher.get(f"/assessments/{assessment_id}/progress").json()["students"][0]["submissions"] == {}
    sent = student.post(f"/assessments/{assessment_id}/items/{item_id}/submissions", json=body)
    assert sent.status_code == 201, sent.text
    sid = sent.json()["submission_id"]
    assert student.get(f"/assessments/{assessment_id}").json()["submitted_item_ids"] == [item_id]
    official = student.post(f"/submissions/{sid}/recognitions", json={
        "provider": "mathpix", "idempotency_key": "exam-hmer:1"})
    assert official.status_code == 201 and official.json()["status"] == "NEEDS_REVIEW"
    assert student.get(f"/assessments/{assessment_id}").json()["submitted_item_ids"] == [item_id]
    assert student.post(f"/submissions/{sid}/recognitions", json={
        "provider": "mathpix", "idempotency_key": "exam-hmer:1"}).status_code == 200
    assert teacher.get(f"/submissions/{sid}").status_code == 200
    transcription = teacher.get(f"/submissions/{sid}/transcriptions")
    assert transcription.status_code == 200
    assert len(transcription.json()) == 1
    assert transcription.json()[0]["latest_revision"]["status"] == "NEEDS_REVIEW"
    assert teacher.get(f"/assessments/{assessment_id}/progress").json()["students"][0]["submissions"][item_id] == sid


def prepare_demo_seed(scenario):
    root = scenario["root"]
    from confia_lean_auditor.auth.store import AuthStore
    from confia_lean_auditor.auth.models import Role
    from confia_lean_auditor.institutional.models import Enrollment, TeacherAssignment
    from confia_lean_auditor.institutional.store import InstitutionalStore, current_academic_year
    users = AuthStore(root / "auth")
    demo = users.create_user(login="professor.demo", display_name="Professor Demo", role=Role.TEACHER,
                             password=PASSWORD, tenant_id="school-a", classroom_ids=["class-a"])
    learner = users.create_user(login="aluno.demo", display_name="Aluno Demo", role=Role.STUDENT,
                                password=PASSWORD, tenant_id="school-a", classroom_ids=["class-a"])
    institution = InstitutionalStore(root / "institutional")
    data = institution.snapshot()
    school = data.schools[0].model_copy(update={"name": "CETI Centro"})
    classroom = data.classrooms[0].model_copy(update={"name": "2ª série A"})
    data.schools[0] = school
    data.classrooms[0] = classroom
    data.teacher_assignments.append(TeacherAssignment(teacher_user_id=demo.user_id,
        school_id=school.school_id, classroom_id=classroom.classroom_id, academic_year=current_academic_year()))
    data.enrollments.append(Enrollment(student_user_id=learner.user_id, school_id=school.school_id,
        classroom_id=classroom.classroom_id, academic_year=current_academic_year()))
    institution.replace(data)
    script = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "create_demo_assessments.py"))
    return script["create_demo_assessments"], script["_stable_id"], demo, learner, school, classroom


def test_demo_seed_exact_items_and_stable_dates(scenario):
    seed, _, _, _, _, _ = prepare_demo_seed(scenario)
    seed(output=lambda _: None)
    repository = AssessmentStore(scenario["root"] / "assessments")
    first = repository.list()
    assert sorted((doc.assessment.title, [item.problem_id for item in doc.items], [item.points for item in doc.items]) for doc in first) == [
        ("Avaliação 1", ["ITA2025F2Q1", "ITA2025F2Q3"], [5, 5]),
        ("Avaliação 2", ["ITA2025F2Q5", "ITA2025F2Q8"], [5, 5]),
    ]
    assert all(doc.assessment.status == "PUBLISHED" for doc in first)
    teacher_list = scenario["client"]("professor.demo").get("/assessments?school_id=school-a&classroom_id=class-a")
    assert teacher_list.status_code == 200
    assert [view["assessment"]["title"] for view in teacher_list.json()] == [
        "Avaliação 1", "Avaliação 2"]
    learner_list = scenario["client"]("aluno.demo").get("/assessments")
    assert learner_list.status_code == 200
    assert [[item["problem_id"] for item in view["items"]] for view in learner_list.json()] == [
        ["ITA2025F2Q1", "ITA2025F2Q3"], ["ITA2025F2Q5", "ITA2025F2Q8"]]
    first_view = learner_list.json()[0]
    submission = student_payload("snapshot:demo-assessment-q1")
    submission.pop("submitted_by_user_id")
    delivered = scenario["client"]("aluno.demo").post(
        f"/assessments/{first_view['assessment']['assessment_id']}/items/{first_view['items'][0]['assessment_item_id']}/submissions",
        json=submission)
    assert delivered.status_code == 201, delivered.text
    progress = scenario["client"]("professor.demo").get(
        f"/assessments/{first_view['assessment']['assessment_id']}/progress")
    assert any(row["display_name"] == "Aluno Demo" and
        row["submissions"].get(first_view["items"][0]["assessment_item_id"]) == delivered.json()["submission_id"]
        for row in progress.json()["students"])
    saved = [doc.model_dump(mode="json") for doc in first]
    seed(output=lambda _: None)
    assert [doc.model_dump(mode="json") for doc in repository.list()] == saved


def test_demo_seed_migrates_only_old_demo_titles_preserving_bindings(scenario):
    seed, stable_id, demo, _, school, classroom = prepare_demo_seed(scenario)
    repository = AssessmentStore(scenario["root"] / "assessments")
    from confia_lean_auditor.institutional.store import current_academic_year
    year = current_academic_year()
    old_definitions = (("Avaliação 1 — 2ª Fase", ("ITA2025F2Q1", "ITA2025F2Q3")),
                       ("Avaliação 2 — 2ª Fase", ("ITA2025F2Q5", "ITA2025F2Q8")))
    for number, (title, problems) in enumerate(old_definitions, 1):
        assessment_id = stable_id("asmt_", f"demo:{year}:{classroom.classroom_id}:{number}")
        now = datetime.now(timezone.utc)
        repository.create(assessment_id=assessment_id, title=title,
            instructions="Resolva cada questão no caderno e confira a prévia antes do envio.",
            teacher_user_id=demo.user_id, network_id=school.network_id, school_id=school.school_id,
            classroom_id=classroom.classroom_id, academic_year=year,
            opens_at=now - timedelta(minutes=5), closes_at=now + timedelta(days=7))
        for order, problem in enumerate(problems, 1):
            repository.add_item(assessment_id, problem, 5,
                assessment_item_id=stable_id("ait_", f"{assessment_id}:{order}:{problem}"))
        repository.publish(assessment_id)
    unrelated = repository.create(title="Avaliação 3", instructions="Outro exame.",
        teacher_user_id=demo.user_id, network_id=school.network_id, school_id=school.school_id,
        classroom_id=classroom.classroom_id, academic_year=year,
        opens_at=now - timedelta(minutes=5), closes_at=now + timedelta(days=7))
    repository.add_item(unrelated.assessment.assessment_id, "ITA2025F2Q1", 5)
    repository.publish(unrelated.assessment.assessment_id)
    before = {doc.assessment.assessment_id: doc.model_dump(mode="json") for doc in repository.list()}
    first_id = stable_id("asmt_", f"demo:{year}:{classroom.classroom_id}:1")
    first_item = repository.get(first_id).items[0].assessment_item_id
    body = student_payload("snapshot:old-demo-title")
    body.pop("submitted_by_user_id")
    delivered = scenario["client"]("aluno.demo").post(
        f"/assessments/{first_id}/items/{first_item}/submissions", json=body)
    assert delivered.status_code == 201, delivered.text
    submissions = SubmissionStore(scenario["root"] / "submissions")
    original_submission = submissions.get_record(delivered.json()["submission_id"]).model_dump(mode="json")

    seed(output=lambda _: None)
    after = {doc.assessment.assessment_id: doc.model_dump(mode="json") for doc in repository.list()}
    assert set(after) == set(before)
    for number, assessment_id in enumerate((first_id,
            stable_id("asmt_", f"demo:{year}:{classroom.classroom_id}:2")), 1):
        assert after[assessment_id]["assessment"]["title"] == f"Avaliação {number}"
        assert after[assessment_id]["assessment"]["definition_sha256"] != before[assessment_id]["assessment"]["definition_sha256"]
        for key, value in before[assessment_id]["assessment"].items():
            if key not in ("title", "definition_sha256"):
                assert after[assessment_id]["assessment"][key] == value
        assert after[assessment_id]["items"] == before[assessment_id]["items"]
        assert repository.get(assessment_id).assessment.definition_sha256 == definition_hash(repository.get(assessment_id))
    assert submissions.get_record(delivered.json()["submission_id"]).model_dump(mode="json") == original_submission
    assert original_submission["assessment_definition_sha256"] == before[first_id]["assessment"]["definition_sha256"]
    assert after[unrelated.assessment.assessment_id] == before[unrelated.assessment.assessment_id]
    assert len(repository.list()) == 3
    seed(output=lambda _: None)
    assert {doc.assessment.assessment_id: doc.model_dump(mode="json") for doc in repository.list()} == after
