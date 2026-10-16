"""Read-only institutional context, always resolved from the server session."""
from typing import Optional
import json
import os

from pydantic import TypeAdapter

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import Field

from confia_lean_auditor.auth.dependencies import auth_store, require_any_role, require_role
from confia_lean_auditor.auth.models import AuthUser, Role
from .models import Classroom, InstitutionalContext, InstitutionalModel, School
from .store import InstitutionalScopeError, current_academic_year, institutional_store
from confia_lean_auditor.core.problem_catalog import list_problem_catalog
from confia_lean_auditor.core.paths import get_repo_root

router = APIRouter(prefix="/institutional", tags=["institutional context"])
ROLES = (Role.STUDENT, Role.TEACHER, Role.SCHOOL_MANAGER, Role.NETWORK_MANAGER)


class ClassroomStudent(InstitutionalModel):
    user_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)


class ClassroomExam(InstitutionalModel):
    """Small read-only availability manifest until Assessment owns this contract."""
    exam_id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    school_id: str = Field(min_length=1)
    classroom_id: str = Field(min_length=1)
    academic_year: int
    problem_ids: list[str] = Field(min_length=1)
    active: bool = True


def _user_or_401(user: Optional[AuthUser]) -> AuthUser:
    if user is None:
        raise HTTPException(401, "Autenticação necessária.")
    return user


@router.get("/me/schools", response_model=list[School])
def my_schools(response: Response, user: Optional[AuthUser] = Depends(require_any_role(*ROLES))):
    response.headers["Cache-Control"] = "no-store"
    try:
        return institutional_store().schools_for(_user_or_401(user))
    except InstitutionalScopeError as exc:
        raise HTTPException(exc.status_code, str(exc)) from None


@router.get("/schools/{school_id}/classrooms", response_model=list[Classroom])
def school_classrooms(school_id: str, response: Response,
                      user: Optional[AuthUser] = Depends(require_any_role(*ROLES))):
    response.headers["Cache-Control"] = "no-store"
    try:
        return institutional_store().classrooms_for(_user_or_401(user), school_id)
    except InstitutionalScopeError as exc:
        raise HTTPException(exc.status_code, str(exc)) from None


@router.get("/me/context", response_model=InstitutionalContext)
def my_context(response: Response, user: Optional[AuthUser] = Depends(require_any_role(*ROLES))):
    response.headers["Cache-Control"] = "no-store"
    try:
        return institutional_store().context_for(_user_or_401(user))
    except InstitutionalScopeError as exc:
        raise HTTPException(exc.status_code, str(exc)) from None


@router.get("/me/exams", response_model=list[ClassroomExam])
def my_exams(response: Response, user: Optional[AuthUser] = Depends(require_role(Role.STUDENT))):
    """Only explicitly published activities for the student's active enrollment."""
    response.headers["Cache-Control"] = "no-store"
    user = _user_or_401(user)
    try:
        enrollment, _ = institutional_store().student_enrollment(user)
    except InstitutionalScopeError as exc:
        raise HTTPException(exc.status_code, str(exc)) from None
    path = institutional_store().root / "exams.json"
    if not path.exists():
        return []
    if path.is_symlink():
        raise HTTPException(500, "Lista de exames inválida.")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        exams = TypeAdapter(list[ClassroomExam]).validate_python(data)
    except (OSError, ValueError):
        raise HTTPException(500, "Lista de exames inválida.") from None
    catalog_ids = {item["problem_id"] for item in list_problem_catalog(get_repo_root())}
    return [exam for exam in exams if exam.active and exam.school_id == enrollment.school_id
            and exam.classroom_id == enrollment.classroom_id and exam.academic_year == enrollment.academic_year
            and all(problem_id in catalog_ids for problem_id in exam.problem_ids)]


@router.get("/classrooms/{classroom_id}/students", response_model=list[ClassroomStudent])
def classroom_students(classroom_id: str, response: Response,
                       user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    user = _user_or_401(user)
    data = institutional_store().snapshot()
    classroom = next((c for c in data.classrooms if c.classroom_id == classroom_id and c.active
                      and c.academic_year == current_academic_year()), None)
    if classroom is None:
        raise HTTPException(403, "Turma fora do escopo autorizado.")
    try:
        allowed = institutional_store().classrooms_for(user, classroom.school_id)
    except InstitutionalScopeError:
        raise HTTPException(403, "Turma fora do escopo autorizado.") from None
    if classroom not in allowed:
        raise HTTPException(403, "Turma fora do escopo autorizado.")
    identifiers = {e.student_user_id for e in data.enrollments if e.active and e.classroom_id == classroom_id
                   and e.academic_year == classroom.academic_year}
    students = [auth_store().get_user(identifier) for identifier in sorted(identifiers)]
    return [ClassroomStudent(user_id=student.user_id, display_name=student.display_name)
            for student in students if student and student.active and student.role == Role.STUDENT]
