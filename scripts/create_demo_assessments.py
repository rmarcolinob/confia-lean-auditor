#!/usr/bin/env python3
"""Create the two published CETI Centro exams once, preserving their first window."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from confia_lean_auditor.assessments.store import assessment_store  # noqa: E402
from confia_lean_auditor.auth.dependencies import auth_store  # noqa: E402
from confia_lean_auditor.auth.models import Role, StoredUser  # noqa: E402
from confia_lean_auditor.core.paths import get_repo_root  # noqa: E402
from confia_lean_auditor.core.problem_catalog import list_problem_catalog  # noqa: E402
from confia_lean_auditor.institutional.store import current_academic_year, institutional_store  # noqa: E402

DEFINITIONS = (
    ("Avaliação 1", "Avaliação 1 — 2ª Fase", ("ITA2025F2Q1", "ITA2025F2Q3")),
    ("Avaliação 2", "Avaliação 2 — 2ª Fase", ("ITA2025F2Q5", "ITA2025F2Q8")),
)
DEMO_INSTRUCTIONS = "Resolva cada questão no caderno e confira a prévia antes do envio."


def _stable_id(prefix, seed):
    return prefix + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


def create_demo_assessments(output=print):
    required = {problem for _, _, problems in DEFINITIONS for problem in problems}
    catalog = {problem["problem_id"] for problem in list_problem_catalog(get_repo_root())}
    missing = sorted(required - catalog)
    if missing:
        raise ValueError(f"Questões ausentes no catálogo: {', '.join(missing)}")
    users = auth_store()
    with users._locked():
        accounts = {login: StoredUser.model_validate(raw).public()
                    for login, raw in users._read("users.json").items()}
    teacher = accounts.get("professor.demo")
    if teacher is None or not teacher.active or teacher.role != Role.TEACHER:
        raise ValueError("Crie primeiro professor.demo como TEACHER ativo.")
    data = institutional_store().snapshot()
    year = current_academic_year()
    school = next((entry for entry in data.schools if entry.active and entry.name == "CETI Centro"), None)
    classroom = next((entry for entry in data.classrooms if school and entry.active
                      and entry.school_id == school.school_id and entry.name == "2ª série A"
                      and entry.academic_year == year), None)
    if classroom is None or not any(assignment.active and assignment.teacher_user_id == teacher.user_id
                                   and assignment.school_id == school.school_id
                                   and assignment.classroom_id == classroom.classroom_id
                                   and assignment.academic_year == year for assignment in data.teacher_assignments):
        raise ValueError("CETI Centro / 2ª série A precisa de TeacherAssignment ativo para professor.demo.")
    repository = assessment_store()
    prepared = []
    for number, (title, old_title, problems) in enumerate(DEFINITIONS, 1):
        assessment_id = _stable_id("asmt_", f"demo:{year}:{classroom.classroom_id}:{number}")
        try:
            existing = repository.get(assessment_id)
        except FileNotFoundError:
            existing = None
        if existing:
            assessment = existing.assessment
            actual = (assessment.assessment_id, assessment.teacher_user_id, assessment.network_id,
                      assessment.school_id, assessment.classroom_id, assessment.academic_year,
                      assessment.status, assessment.instructions,
                      tuple((item.assessment_item_id, item.assessment_id, item.problem_id, item.order, item.points)
                            for item in existing.items))
            expected = (assessment_id, teacher.user_id, school.network_id, school.school_id,
                        classroom.classroom_id, year, "PUBLISHED", DEMO_INSTRUCTIONS,
                        tuple((_stable_id("ait_", f"{assessment_id}:{order}:{problem}"), assessment_id,
                               problem, order, 5.0) for order, problem in enumerate(problems, 1)))
            if assessment.title not in (title, old_title) or actual != expected:
                raise ValueError(f"Seed existente diverge: {assessment_id}")
        prepared.append((assessment_id, title, old_title, problems, existing))

    for assessment_id, title, old_title, problems, existing in prepared:
        if existing and existing.assessment.title == old_title:
            repository.migrate_demo_title(assessment_id, expected_document=existing,
                                          old_title=old_title, new_title=title)
            output(f"Renomeado: {title} ({assessment_id})")
            continue
        if existing:
            output(f"Preservado: {title} ({assessment_id})")
            continue
        now = datetime.now(timezone.utc)
        repository.create(assessment_id=assessment_id, title=title,
            instructions=DEMO_INSTRUCTIONS,
            teacher_user_id=teacher.user_id, network_id=school.network_id, school_id=school.school_id,
            classroom_id=classroom.classroom_id, academic_year=year,
            opens_at=now - timedelta(minutes=5), closes_at=now + timedelta(days=7))
        for order, problem_id in enumerate(problems, 1):
            item_id = _stable_id("ait_", f"{assessment_id}:{order}:{problem_id}")
            repository.add_item(assessment_id, problem_id, 5, assessment_item_id=item_id)
        repository.publish(assessment_id)
        output(f"Publicado: {title} ({assessment_id}) — {', '.join(problems)}")


if __name__ == "__main__":
    try:
        create_demo_assessments()
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from None
