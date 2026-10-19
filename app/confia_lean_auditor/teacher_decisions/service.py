"""Bindings, authorization and human decision lifecycle; never executes an audit."""
from datetime import datetime, timezone
from decimal import Decimal

from confia_lean_auditor.assessments.store import assessment_store
from confia_lean_auditor.auth.models import Role
from confia_lean_auditor.institutional.store import InstitutionalScopeError, institutional_store
from confia_lean_auditor.submission_audits.router import service as audit_service
from confia_lean_auditor.submissions.router import store as submission_store
from .models import StudentResult, TeacherDecision, TeacherDecisionView, suggested_points
from .store import DecisionConflict, DecisionIntegrityError, decision_hash, decision_store


def institutional_binding(record):
    if not record.assessment_id:
        raise DecisionConflict("Envio legado sem avaliação vinculada não possui decisão institucional.")
    document = assessment_store().get(record.assessment_id)
    assessment = document.assessment
    item = next((item for item in document.items if item.assessment_item_id == record.assessment_item_id), None)
    if (assessment.status == "DRAFT" or item is None or item.problem_id != record.problem_id
            or record.assessment_definition_sha256 != assessment.definition_sha256
            or (record.network_id, record.school_id, record.classroom_id) !=
               (assessment.network_id, assessment.school_id, assessment.classroom_id)):
        raise DecisionIntegrityError("submission/assessment binding mismatch")
    return assessment, item


def validate_binding(decision, record):
    assessment, item = institutional_binding(record)
    expected = dict(submission_id=record.submission_id, assessment_id=assessment.assessment_id,
        assessment_item_id=item.assessment_item_id, assessment_definition_sha256=assessment.definition_sha256,
        problem_id=item.problem_id, item_max_points=Decimal(str(item.points)))
    if any(getattr(decision, field) != value for field, value in expected.items()):
        raise DecisionIntegrityError("decision binding mismatch")
    return assessment, item


def teacher_record(user, submission_id):
    if user is None or user.role != Role.TEACHER:
        raise InstitutionalScopeError("Somente professor autenticado pode acessar decisões.", 401 if user is None else 403)
    record = submission_store().get_record(submission_id)
    if not institutional_store().teacher_can_view(user, record):
        raise InstitutionalScopeError("Turma fora do vínculo docente.")
    assessment, _ = institutional_binding(record)
    classes = institutional_store().classrooms_for(user, assessment.school_id, assessment.academic_year)
    if record.classroom_id not in {classroom.classroom_id for classroom in classes}:
        raise InstitutionalScopeError("Turma fora do vínculo docente no ano da avaliação.")
    return record


def audit_snapshot(record, run_id, points):
    empty = dict(audit_run_id=None, audit_source_sha256=None, audit_result_sha256=None,
                 confia_score_raw=None, confia_max_score_raw=None, confia_suggested_points=None)
    if run_id is None:
        return empty
    run = audit_service().get(run_id)
    if (run.submission_id, run.problem_id) != (record.submission_id, record.problem_id):
        raise DecisionConflict("A análise selecionada não pertence a esta solução.")
    if run.stale:
        raise DecisionConflict("Análise de transcrição anterior. Abra uma análise atual ou escolha decisão manual.")
    result = run.result
    score = Decimal(str(result.score)) if result and result.score is not None else None
    maximum = Decimal(str(result.max_score)) if result else None
    if any(value is not None and not value.is_finite() for value in (score, maximum)):
        raise DecisionIntegrityError("non-finite audit score")
    technical_error = result is not None and (
        result.rubric_assessment.assessment_status == "indeterminate"
        or any(item.verification_status == "technical_error" for item in result.rubric_assessment.items)
        or any(item.verification_status == "technical_error" for item in result.microclaims)
        or (result.pedagogical_report is not None and result.pedagogical_report.verification_status == "technical_error"))
    suggestion = suggested_points(points, score, maximum) if run.status == "COMPLETED" and not technical_error else None
    return dict(audit_run_id=run.audit_run_id, audit_source_sha256=run.source_hash,
                audit_result_sha256=run.result_sha256, confia_score_raw=score,
                confia_max_score_raw=maximum, confia_suggested_points=suggestion)


def teacher_view(decision):
    state = "none"
    if decision.audit_run_id:
        try:
            run = audit_service().get(decision.audit_run_id)
            state = "stale" if run.stale else "current"
            if (run.submission_id, run.source_hash, run.result_sha256) != (
                    decision.submission_id, decision.audit_source_sha256, decision.audit_result_sha256):
                state = "unavailable"
        except (ValueError, OSError):
            state = "unavailable"
    return TeacherDecisionView(**decision.model_dump(), audit_state=state)


def get_for_teacher(user, submission_id):
    record = teacher_record(user, submission_id)
    decision = decision_store().get_for_submission(submission_id)
    if decision is None:
        return None
    validate_binding(decision, record)
    return teacher_view(decision)


def create(user, submission_id, request):
    record = teacher_record(user, submission_id)
    assessment, item = institutional_binding(record)

    def factory(decision_id):
        now = datetime.now(timezone.utc)
        points = Decimal(str(item.points))
        return TeacherDecision(decision_id=decision_id, submission_id=submission_id,
            assessment_id=assessment.assessment_id, assessment_item_id=item.assessment_item_id,
            assessment_definition_sha256=assessment.definition_sha256, problem_id=item.problem_id,
            teacher_user_id=user.user_id, item_max_points=points, created_at=now, updated_at=now,
            **audit_snapshot(record, request.audit_run_id, points))

    decision, created = decision_store().create(submission_id, factory)
    validate_binding(decision, record)
    return teacher_view(decision), created


def _draft(decision, expected_version):
    if decision.status != "DRAFT":
        raise DecisionConflict("Decisão finalizada não pode ser editada.")
    if decision.version != expected_version:
        raise DecisionConflict("Rascunho alterado em outra sessão. Reabra a decisão antes de salvar.")


def update(user, decision_id, request):
    def operation(decision):
        record = teacher_record(user, decision.submission_id)
        validate_binding(decision, record)
        _draft(decision, request.expected_version)
        changes = request.model_dump(exclude_unset=True, exclude={"expected_version", "audit_run_id"})
        if "audit_run_id" in request.model_fields_set:
            changes.update(audit_snapshot(record, request.audit_run_id, decision.item_max_points))
        if changes.get("teacher_final_points") is not None and changes["teacher_final_points"] > decision.item_max_points:
            raise ValueError("final points exceed server maximum")
        changes.update(teacher_user_id=user.user_id, updated_at=datetime.now(timezone.utc), version=decision.version + 1)
        return TeacherDecision.model_validate({**decision.model_dump(), **changes})
    return teacher_view(decision_store().update(decision_id, operation))


def finalize(user, decision_id, request):
    def operation(decision):
        record = teacher_record(user, decision.submission_id)
        validate_binding(decision, record)
        # Retries publish the exact same final content, without another mutation.
        if decision.status != "DRAFT":
            return decision
        _draft(decision, request.expected_version)
        if decision.teacher_final_points is None:
            raise DecisionConflict("Informe a pontuação final do professor antes de finalizar.")
        if decision.is_override and not (decision.override_reason or "").strip():
            raise DecisionConflict("Justifique a alteração da pontuação sugerida antes de finalizar.")
        # Recheck freshness and provenance at finalization, without refreshing the snapshot silently.
        snapshot = audit_snapshot(record, decision.audit_run_id, decision.item_max_points)
        if any(getattr(decision, field) != value for field, value in snapshot.items()):
            raise DecisionIntegrityError("audit snapshot changed")
        now = datetime.now(timezone.utc)
        final = decision.model_copy(update=dict(status="FINALIZED", finalized_at=now,
                    updated_at=now, teacher_user_id=user.user_id, version=decision.version + 1))
        final.decision_sha256 = decision_hash(final)
        return final
    return teacher_view(decision_store().update(decision_id, operation))


def release(user, decision_id):
    def operation(decision):
        record = teacher_record(user, decision.submission_id)
        validate_binding(decision, record)
        if decision.status == "DRAFT":
            raise DecisionConflict("Finalize a decisão antes de liberar o resultado.")
        if decision.status == "RELEASED":
            return decision
        now = datetime.now(timezone.utc)
        return decision.model_copy(update=dict(status="RELEASED", released_at=now,
                    updated_at=now, version=decision.version + 1))
    return teacher_view(decision_store().update(decision_id, operation))


def student_projection(decision):
    if decision is None or decision.status != "RELEASED":
        return None
    return StudentResult(assessment_id=decision.assessment_id, item_id=decision.assessment_item_id,
        problem_id=decision.problem_id, final_points=decision.teacher_final_points,
        max_points=decision.item_max_points, teacher_feedback=decision.teacher_feedback,
        released_at=decision.released_at)


def results_for_student(user, document, records):
    assessment = document.assessment
    items = {item.assessment_item_id: item for item in document.items}
    results = []
    for record in records:
        if (record.submitted_by_user_id != user.user_id or record.assessment_id != assessment.assessment_id
                or record.assessment_item_id not in items):
            continue
        decision = decision_store().get_for_submission(record.submission_id)
        if decision is None or decision.status != "RELEASED":
            continue
        validate_binding(decision, record)
        results.append(student_projection(decision))
    return results


def correction_status(record):
    decision = decision_store().get_for_submission(record.submission_id)
    if decision:
        validate_binding(decision, record)
        return {"DRAFT": "DECISION_DRAFT", "FINALIZED": "DECISION_FINALIZED", "RELEASED": "RESULT_RELEASED"}[decision.status]
    runs = audit_service().list(record.submission_id)
    if any(not run.stale and run.status == "COMPLETED" for run in runs):
        return "ANALYSIS_AVAILABLE"
    summaries = submission_store().list_transcriptions(record.submission_id)
    return "TRANSCRIPTION_REVIEW" if summaries else "SUBMITTED"
