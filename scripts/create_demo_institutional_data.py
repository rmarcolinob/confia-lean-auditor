#!/usr/bin/env python3
"""Seed a small state network using existing demo identities, without passwords."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from confia_lean_auditor.auth.dependencies import auth_store  # noqa: E402
from confia_lean_auditor.auth.models import Role, StoredUser  # noqa: E402
from confia_lean_auditor.institutional.models import (  # noqa: E402
    Classroom, Enrollment, InstitutionalData, ManagerAssignment, Network, School, TeacherAssignment,
)
from confia_lean_auditor.institutional.store import current_academic_year, institutional_store  # noqa: E402


def create_demo_institutional_data(output=print):
    users = auth_store()
    with users._locked():
        accounts = {login: StoredUser.model_validate(raw).public()
                    for login, raw in users._read("users.json").items()}
    required = {"aluno.demo": Role.STUDENT, "professor.demo": Role.TEACHER,
                "gestao.demo": Role.SCHOOL_MANAGER}
    for login, role in required.items():
        if login not in accounts or accounts[login].role != role:
            raise ValueError(f"Crie primeiro a conta {login} com o papel correto.")
    year = current_academic_year()
    center_1 = f"centro-1a-{year}"
    center_2 = f"centro-2a-{year}"
    north_3 = f"norte-3a-{year}"
    managers = [ManagerAssignment(manager_user_id=accounts["gestao.demo"].user_id,
                                  school_id="ceti-centro")]
    network_user = accounts.get("rede.demo")
    if network_user and network_user.role == Role.NETWORK_MANAGER:
        managers.append(ManagerAssignment(manager_user_id=network_user.user_id, network_id="demo-pi"))
    seed = InstitutionalData(
        networks=[Network(network_id="demo-pi", name="Rede Estadual Demo")],
        schools=[
            School(school_id="ceti-centro", network_id="demo-pi", name="CETI Centro",
                   code="ceti-centro", municipality="Teresina"),
            School(school_id="ceti-norte", network_id="demo-pi", name="CETI Norte",
                   code="ceti-norte", municipality="Teresina"),
        ],
        classrooms=[
            Classroom(classroom_id=center_1, school_id="ceti-centro", name="1ª série A",
                      grade="1ª série", shift="Integral", academic_year=year),
            Classroom(classroom_id=center_2, school_id="ceti-centro", name="2ª série A",
                      grade="2ª série", shift="Integral", academic_year=year),
            Classroom(classroom_id=north_3, school_id="ceti-norte", name="3ª série A",
                      grade="3ª série", shift="Integral", academic_year=year),
        ],
        teacher_assignments=[
            TeacherAssignment(teacher_user_id=accounts["professor.demo"].user_id,
                              school_id="ceti-centro", classroom_id=class_id, academic_year=year)
            for class_id in (center_1, center_2)
        ],
        enrollments=[Enrollment(student_user_id=accounts["aluno.demo"].user_id,
                                school_id="ceti-centro", classroom_id=center_2, academic_year=year)],
        manager_assignments=managers,
    )
    institutional_store().merge_seed(seed)
    output(f"Rede demo criada/confirmada para {year}: 2 escolas, 3 turmas, vínculos ativos.")


if __name__ == "__main__":
    try:
        create_demo_institutional_data()
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
