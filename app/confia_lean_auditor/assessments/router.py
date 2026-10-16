"""Institutional Assessment API. Session and Enrollment/Assignment own all scope."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from confia_lean_auditor.auth.dependencies import auth_store, require_any_role, require_role
from confia_lean_auditor.auth.models import AuthUser, Role
from confia_lean_auditor.core.problem_catalog import list_problem_catalog
from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.institutional.store import InstitutionalScopeError, current_academic_year, institutional_store
from confia_lean_auditor.submissions.router import guarded as submission_guarded, receive_body, store as submission_store
from confia_lean_auditor.submissions.schemas import MAX_REQUEST_BYTES, SubmissionReceipt
from .models import (AssessmentDocument, AssessmentProgress, AssessmentView, CreateAssessment,
                     CreateAssessmentItem, UpdateAssessment, UpdateAssessmentItem)
from .store import AssessmentConflict, AssessmentIntegrityConflict, assessment_store

router = APIRouter(prefix="/assessments", tags=["institutional assessments"])


def _user(user):
    if user is None:
        raise HTTPException(401, "Autenticação necessária.")
    return user


def _scope_error(exc):
    if isinstance(exc, InstitutionalScopeError):
        raise HTTPException(exc.status_code, str(exc)) from None
    if isinstance(exc, AssessmentIntegrityConflict):
        raise HTTPException(409, "Integridade da definição publicada inválida.") from None
    if isinstance(exc, AssessmentConflict):
        raise HTTPException(409, str(exc)) from None
    if isinstance(exc, FileNotFoundError):
        raise HTTPException(404, "Exame ou questão não encontrado.") from None
    if isinstance(exc, (ValidationError, ValueError)):
        raise HTTPException(422, "Dados do exame inválidos.") from None
    if isinstance(exc, OSError):
        raise HTTPException(503, "Armazenamento de exames indisponível.") from None
    raise exc


def _teacher_classroom(user, school_id, classroom_id):
    repository = institutional_store()
    if school_id not in {school.school_id for school in repository.schools_for(user)}:
        raise InstitutionalScopeError("Escola fora do vínculo docente.")
    classrooms = repository.classrooms_for(user, school_id)
    classroom = next((item for item in classrooms if item.classroom_id == classroom_id
                      and item.academic_year == current_academic_year()), None)
    if classroom is None:
        raise InstitutionalScopeError("Turma fora do vínculo docente.")
    school = next(item for item in repository.schools_for(user) if item.school_id == school_id)
    return school, classroom


def _teacher_document(user, assessment_id, *, write=False):
    document = assessment_store().get(assessment_id)
    assessment = document.assessment
    _teacher_classroom(user, assessment.school_id, assessment.classroom_id)
    if write and assessment.teacher_user_id != user.user_id:
        raise InstitutionalScopeError("Somente o professor criador pode editar este exame.")
    return document


def _student_document(user, assessment_id):
    enrollment, _ = institutional_store().student_enrollment(user)
    document = assessment_store().get(assessment_id)
    assessment = document.assessment
    if assessment.status == "DRAFT" or (assessment.school_id, assessment.classroom_id, assessment.academic_year) != \
            (enrollment.school_id, enrollment.classroom_id, enrollment.academic_year):
        raise FileNotFoundError()
    return document


def _catalog_ids():
    return {problem["problem_id"] for problem in list_problem_catalog(get_repo_root())}


def availability(assessment, now=None):
    now = now or datetime.now(timezone.utc)
    if assessment.status == "DRAFT":
        return "RASCUNHO"
    if assessment.status == "CLOSED" or now >= assessment.closes_at:
        return "ENCERRADO"
    if now < assessment.opens_at:
        return "AGENDADO"
    return "DISPONÍVEL"


def _view(document, user, records=None):
    assessment = document.assessment
    people = auth_store()
    teacher = people.get_user(assessment.teacher_user_id)
    data = institutional_store().snapshot()
    classroom = next((item for item in data.classrooms if item.classroom_id == assessment.classroom_id), None)
    records = records if records is not None else submission_store().list()
    matching = {(record.assessment_item_id, record.problem_id) for record in records
                if user.role == Role.STUDENT and record.submitted_by_user_id == user.user_id
                and record.assessment_id == assessment.assessment_id
                and (record.network_id, record.school_id, record.classroom_id) ==
                    (assessment.network_id, assessment.school_id, assessment.classroom_id)}
    submitted = [item.assessment_item_id for item in sorted(document.items, key=lambda item: item.order)
                 if (item.assessment_item_id, item.problem_id) in matching]
    return AssessmentView(assessment=assessment, items=document.items,
        teacher_name=teacher.display_name if teacher else "Professor",
        classroom_name=classroom.name if classroom else assessment.classroom_id,
        availability=availability(assessment), submitted_item_ids=submitted)


@router.get("", response_model=list[AssessmentView])
def list_assessments(response: Response, school_id: Optional[str] = None, classroom_id: Optional[str] = None,
                     user: Optional[AuthUser] = Depends(require_any_role(Role.STUDENT, Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    try:
        documents = assessment_store().list()
        if user.role == Role.STUDENT:
            if school_id or classroom_id:
                raise InstitutionalScopeError("Aluno não escolhe escola ou turma.")
            enrollment, _ = institutional_store().student_enrollment(user)
            documents = [doc for doc in documents if doc.assessment.status != "DRAFT"
                and (doc.assessment.school_id, doc.assessment.classroom_id, doc.assessment.academic_year) ==
                    (enrollment.school_id, enrollment.classroom_id, enrollment.academic_year)]
        else:
            if classroom_id and not school_id:
                raise HTTPException(422, "Informe a escola da turma.")
            if school_id and school_id not in {school.school_id for school in institutional_store().schools_for(user)}:
                raise InstitutionalScopeError("Escola fora do vínculo docente.")
            if school_id and classroom_id:
                _teacher_classroom(user, school_id, classroom_id)
            authorized = {(classroom.school_id, classroom.classroom_id)
                for school in institutional_store().schools_for(user)
                for classroom in institutional_store().classrooms_for(user, school.school_id)}
            documents = [doc for doc in documents if (doc.assessment.school_id, doc.assessment.classroom_id) in authorized
                and (school_id is None or doc.assessment.school_id == school_id)
                and (classroom_id is None or doc.assessment.classroom_id == classroom_id)]
        records = submission_store().list()
        documents.sort(key=lambda document: (document.assessment.title.casefold(), document.assessment.created_at))
        return [_view(document, user, records) for document in documents]
    except HTTPException:
        raise
    except Exception as exc:
        _scope_error(exc)


@router.get("/{assessment_id}", response_model=AssessmentView)
def get_assessment(assessment_id: str, response: Response,
                   user: Optional[AuthUser] = Depends(require_any_role(Role.STUDENT, Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    try:
        document = _student_document(user, assessment_id) if user.role == Role.STUDENT else _teacher_document(user, assessment_id)
        return _view(document, user)
    except Exception as exc:
        _scope_error(exc)


@router.post("", response_model=AssessmentView, status_code=201)
def create_assessment(body: CreateAssessment, response: Response,
                      user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    try:
        school, classroom = _teacher_classroom(user, body.school_id, body.classroom_id)
        document = assessment_store().create(title=body.title, instructions=body.instructions,
            teacher_user_id=user.user_id, network_id=school.network_id, school_id=school.school_id,
            classroom_id=classroom.classroom_id, academic_year=classroom.academic_year,
            opens_at=body.opens_at, closes_at=body.closes_at)
        return _view(document, user)
    except Exception as exc:
        _scope_error(exc)


@router.patch("/{assessment_id}", response_model=AssessmentView)
def update_assessment(assessment_id: str, body: UpdateAssessment, response: Response,
                      user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    try:
        _teacher_document(user, assessment_id, write=True)
        document = assessment_store().update(assessment_id, body.model_dump(exclude_unset=True))
        return _view(document, user)
    except Exception as exc:
        _scope_error(exc)


@router.post("/{assessment_id}/items", response_model=AssessmentView, status_code=201)
def add_item(assessment_id: str, body: CreateAssessmentItem, response: Response,
             user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    try:
        _teacher_document(user, assessment_id, write=True)
        if body.problem_id not in _catalog_ids():
            raise HTTPException(422, "Questão não disponível no catálogo.")
        return _view(assessment_store().add_item(assessment_id, body.problem_id, body.points), user)
    except HTTPException:
        raise
    except Exception as exc:
        _scope_error(exc)


@router.patch("/{assessment_id}/items/{item_id}", response_model=AssessmentView)
def update_item(assessment_id: str, item_id: str, body: UpdateAssessmentItem, response: Response,
                user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    try:
        _teacher_document(user, assessment_id, write=True)
        return _view(assessment_store().update_item(assessment_id, item_id, body.points), user)
    except Exception as exc:
        _scope_error(exc)


@router.delete("/{assessment_id}/items/{item_id}", response_model=AssessmentView)
def remove_item(assessment_id: str, item_id: str, response: Response,
                user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    try:
        _teacher_document(user, assessment_id, write=True)
        return _view(assessment_store().remove_item(assessment_id, item_id), user)
    except Exception as exc:
        _scope_error(exc)


@router.post("/{assessment_id}/publish", response_model=AssessmentView)
def publish_assessment(assessment_id: str, response: Response,
                       user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    try:
        document = _teacher_document(user, assessment_id, write=True)
        _teacher_classroom(user, document.assessment.school_id, document.assessment.classroom_id)
        if not document.items or any(item.problem_id not in _catalog_ids() for item in document.items):
            raise HTTPException(422, "O exame precisa ter questões válidas do catálogo.")
        return _view(assessment_store().publish(assessment_id), user)
    except HTTPException:
        raise
    except Exception as exc:
        _scope_error(exc)


@router.post("/{assessment_id}/close", response_model=AssessmentView)
def close_assessment(assessment_id: str, response: Response,
                     user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    try:
        _teacher_document(user, assessment_id, write=True)
        return _view(assessment_store().close(assessment_id), user)
    except Exception as exc:
        _scope_error(exc)


@router.get("/{assessment_id}/progress", response_model=AssessmentProgress)
def assessment_progress(assessment_id: str, response: Response,
                        user: Optional[AuthUser] = Depends(require_role(Role.TEACHER))):
    response.headers["Cache-Control"] = "no-store"
    user = _user(user)
    try:
        document = _teacher_document(user, assessment_id)
        data = institutional_store().snapshot()
        assessment = document.assessment
        enrolled = [item.student_user_id for item in data.enrollments if item.active
            and (item.school_id, item.classroom_id, item.academic_year) ==
                (assessment.school_id, assessment.classroom_id, assessment.academic_year)]
        records = submission_store().list()
        students = []
        for user_id in sorted(set(enrolled)):
            student = auth_store().get_user(user_id)
            if not student or not student.active or student.role != Role.STUDENT:
                continue
            submitted = {record.assessment_item_id: record.submission_id for record in records
                if record.assessment_id == assessment_id and record.submitted_by_user_id == user_id}
            students.append({"user_id": user_id, "display_name": student.display_name, "submissions": submitted})
        return AssessmentProgress(assessment=assessment, items=document.items, students=students)
    except Exception as exc:
        _scope_error(exc)


@router.post("/{assessment_id}/items/{item_id}/submissions", response_model=SubmissionReceipt)
async def submit_assessment_item(assessment_id: str, item_id: str, request: Request, response: Response,
                                  user: Optional[AuthUser] = Depends(require_role(Role.STUDENT))):
    user = _user(user)
    try:
        document = _student_document(user, assessment_id)
        assessment = document.assessment
        item = next((item for item in document.items if item.assessment_item_id == item_id), None)
        if item is None:
            raise FileNotFoundError()
        if availability(assessment) != "DISPONÍVEL":
            raise AssessmentConflict("Exame fora do período de envio.")
        if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
            raise HTTPException(415, "Use application/json.")
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > MAX_REQUEST_BYTES:
                raise HTTPException(413, "Payload acima do limite permitido.")
            raw.extend(chunk)
        binding = (assessment_id, item_id, assessment.definition_sha256, item.problem_id,
                   assessment.network_id, assessment.school_id, assessment.classroom_id,
                   assessment.academic_year)
        receipt, created = await run_in_threadpool(submission_guarded, receive_body, bytes(raw), user, binding)
        response.status_code = 201 if created else 200
        response.headers["Cache-Control"] = "no-store"
        return receipt
    except HTTPException:
        raise
    except Exception as exc:
        _scope_error(exc)
