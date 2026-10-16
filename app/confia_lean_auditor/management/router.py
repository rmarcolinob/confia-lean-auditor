"""Privacy-preserving aggregates from persisted institutional and workflow records."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import Field

from confia_lean_auditor.auth.dependencies import require_any_role, require_role
from confia_lean_auditor.auth.models import AuthUser, Role
from confia_lean_auditor.institutional.models import Classroom, InstitutionalModel, School
from confia_lean_auditor.institutional.store import InstitutionalScopeError, current_academic_year, institutional_store
from confia_lean_auditor.recognition.registry import RecognizerRegistry
from confia_lean_auditor.recognition.service import RecognitionService
from confia_lean_auditor.submission_audits.router import service as audit_service
from confia_lean_auditor.submissions.router import store as submission_store

router = APIRouter(prefix="/management", tags=["institutional aggregates"])
MANAGERS = (Role.SCHOOL_MANAGER, Role.NETWORK_MANAGER)


class Metrics(InstitutionalModel):
    number_of_schools: int = Field(ge=0)
    number_of_classrooms: int = Field(ge=0)
    number_of_students: int = Field(ge=0)
    number_of_teachers: int = Field(ge=0)
    submissions_count: Optional[int] = Field(default=None, ge=0)
    transcriptions_count: Optional[int] = Field(default=None, ge=0)
    recognition_success_count: Optional[int] = Field(default=None, ge=0)
    recognition_failure_count: Optional[int] = Field(default=None, ge=0)
    audit_runs_count: Optional[int] = Field(default=None, ge=0)
    completed_audits: Optional[int] = Field(default=None, ge=0)
    inconclusive_audits: Optional[int] = Field(default=None, ge=0)


class Overview(InstitutionalModel):
    kind: str = "institutional_aggregate"
    scope: str
    academic_year: int
    network_id: Optional[str] = None
    school: Optional[School] = None
    classroom: Optional[Classroom] = None
    metrics: Metrics


class SchoolRow(InstitutionalModel):
    school: School
    metrics: Metrics


class ClassroomRow(InstitutionalModel):
    classroom: Classroom
    metrics: Metrics


def _user(user: Optional[AuthUser]) -> AuthUser:
    if user is None:
        raise HTTPException(401, "Autenticação necessária.")
    return user


def _scope_school(user: AuthUser, school_id: str) -> School:
    school = next((s for s in institutional_store().schools_for(user) if s.school_id == school_id), None)
    if school is None:
        raise HTTPException(403, "Escola fora do escopo autorizado.")
    return school


def _scope_network(user: AuthUser) -> str:
    data = institutional_store().snapshot()
    active = {n.network_id for n in data.networks if n.active}
    ids = {a.network_id for a in data.manager_assignments if a.active and a.manager_user_id == user.user_id
           and a.network_id in active}
    if len(ids) != 1:
        raise HTTPException(403, "Rede fora do escopo autorizado.")
    return next(iter(ids))


def _metrics(school_ids: set[str], classroom_ids: set[str]) -> Metrics:
    data = institutional_store().snapshot()
    year = current_academic_year()
    classes = {c.classroom_id for c in data.classrooms if c.active and c.academic_year == year
               and c.school_id in school_ids and c.classroom_id in classroom_ids}
    students = {e.student_user_id for e in data.enrollments if e.active and e.academic_year == year
                and e.classroom_id in classes}
    teachers = {a.teacher_user_id for a in data.teacher_assignments if a.active and a.academic_year == year
                and a.classroom_id in classes}
    counts = dict(number_of_schools=len(school_ids), number_of_classrooms=len(classes),
                  number_of_students=len(students), number_of_teachers=len(teachers))
    try:
        submissions = submission_store()
        records = [r for r in submissions.list() if r.school_id in school_ids and r.classroom_id in classes
                   and r.network_id is not None]
        counts["submissions_count"] = len(records)
    except (ValueError, OSError):
        records = None
    if records is None:
        return Metrics(**counts)
    try:
        counts["transcriptions_count"] = sum(len(submissions.list_transcriptions(r.submission_id)) for r in records)
    except (ValueError, OSError):
        pass
    try:
        recognitions = RecognitionService(submissions, RecognizerRegistry())
        runs = [run for r in records for run in recognitions.list(r.submission_id)]
        counts["recognition_success_count"] = sum(run.status == "NEEDS_REVIEW" for run in runs)
        counts["recognition_failure_count"] = sum(run.status == "FAILED" for run in runs)
    except (ValueError, OSError):
        pass
    try:
        audits = [run for r in records for run in audit_service().list(r.submission_id)]
        counts["audit_runs_count"] = len(audits)
        counts["completed_audits"] = sum(run.status == "COMPLETED" for run in audits)
        counts["inconclusive_audits"] = sum(run.status == "COMPLETED"
            and (run.result is None or run.result.score is None) for run in audits)
    except (ValueError, OSError):
        pass
    return Metrics(**counts)


def _school_overview(user: AuthUser, school_id: str) -> Overview:
    school = _scope_school(user, school_id)
    classes = institutional_store().classrooms_for(user, school_id)
    return Overview(scope="school", academic_year=current_academic_year(), school=school,
                    network_id=school.network_id,
                    metrics=_metrics({school_id}, {c.classroom_id for c in classes}))


def _network_overview(user: AuthUser) -> Overview:
    network_id = _scope_network(user)
    schools = [s for s in institutional_store().schools_for(user) if s.network_id == network_id]
    classes = [c for s in schools for c in institutional_store().classrooms_for(user, s.school_id)]
    return Overview(scope="network", academic_year=current_academic_year(), network_id=network_id,
                    metrics=_metrics({s.school_id for s in schools}, {c.classroom_id for c in classes}))


@router.get("/network/overview", response_model=Overview)
def network_overview(response: Response, user: Optional[AuthUser] = Depends(require_role(Role.NETWORK_MANAGER))):
    response.headers["Cache-Control"] = "no-store"
    return _network_overview(_user(user))


@router.get("/schools", response_model=list[SchoolRow])
def schools(response: Response, user: Optional[AuthUser] = Depends(require_any_role(*MANAGERS))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    return [SchoolRow(school=s, metrics=_school_overview(user, s.school_id).metrics)
            for s in institutional_store().schools_for(user)]


@router.get("/schools/{school_id}/overview", response_model=Overview)
def school_overview(school_id: str, response: Response,
                    user: Optional[AuthUser] = Depends(require_any_role(*MANAGERS))):
    response.headers["Cache-Control"] = "no-store"
    return _school_overview(_user(user), school_id)


@router.get("/schools/{school_id}/classrooms", response_model=list[ClassroomRow])
def school_classrooms(school_id: str, response: Response,
                      user: Optional[AuthUser] = Depends(require_any_role(*MANAGERS))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    _scope_school(user, school_id)
    return [ClassroomRow(classroom=c, metrics=_metrics({school_id}, {c.classroom_id}))
            for c in institutional_store().classrooms_for(user, school_id)]


@router.get("/classrooms/{classroom_id}/overview", response_model=Overview)
def classroom_overview(classroom_id: str, response: Response,
                       user: Optional[AuthUser] = Depends(require_any_role(*MANAGERS))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    data = institutional_store().snapshot()
    classroom = next((c for c in data.classrooms if c.classroom_id == classroom_id and c.active), None)
    if classroom is None:
        raise HTTPException(403, "Turma fora do escopo autorizado.")
    try:
        allowed = institutional_store().classrooms_for(user, classroom.school_id)
    except InstitutionalScopeError:
        raise HTTPException(403, "Turma fora do escopo autorizado.") from None
    if classroom not in allowed:
        raise HTTPException(403, "Turma fora do escopo autorizado.")
    school = _scope_school(user, classroom.school_id)
    return Overview(scope="classroom", academic_year=current_academic_year(), network_id=school.network_id,
                    school=school, classroom=classroom,
                    metrics=_metrics({school.school_id}, {classroom_id}))


@router.get("/overview", response_model=Overview)
def overview(response: Response, user: Optional[AuthUser] = Depends(require_any_role(*MANAGERS))):
    """Compatibility path for the existing management shell, now backed by real data."""
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    if user.role == Role.NETWORK_MANAGER:
        return _network_overview(user)
    own = institutional_store().schools_for(user)
    if len(own) != 1:
        raise HTTPException(409, "Escola de gestão ausente ou ambígua.")
    return _school_overview(user, own[0].school_id)
