"""Explicit human resolution; never a mathematical verifier or automatic score."""
from typing import Literal, Optional
from pydantic import Field, field_validator
from confia_lean_auditor.submissions.schemas import SubmissionModel, Sha256
from confia_lean_auditor.teacher_decisions.models import Points


class CriterionAdjudication(SubmissionModel):
    criterion_id: str = Field(min_length=1, max_length=100)
    final_points: Points
    justification: str = Field(min_length=1, max_length=2000)
    dependency_justification: Optional[str] = Field(default=None, max_length=2000)

    @field_validator('justification')
    @classmethod
    def nonblank(cls, value):
        if not value.strip(): raise ValueError('criterion justification required')
        return value.strip()


class HumanAdjudication(SubmissionModel):
    schema_version: Literal['dynamic-human-adjudication.v1'] = 'dynamic-human-adjudication.v1'
    rubric_sha256: Sha256
    criteria: list[CriterionAdjudication] = Field(min_length=1, max_length=100)


def validate(case, run, reconciliation, body):
    """Validate all criteria against the immutable approved rubric and source.

    Legacy links require an explicit explanation. Typed mathematical prerequisites
    enforce only their approved threshold; procedural and carry-forward conditions
    remain the teacher's explicit judgment. No dependency assigns zero by itself.
    """
    from .grading_context import case_context
    from .store import DynamicConflict
    context, _, rubric, _ = case_context(case)
    if context != run.source.dynamic_context or reconciliation['context'] != context.model_dump(mode='json'):
        raise DynamicConflict('Contexto da adjudicação divergente.')
    a = body.adjudication
    if not a or a.rubric_sha256 != context.rubric_sha256:
        raise DynamicConflict('Selecione a versão aprovada da rubrica.')
    if not (body.override_reason or '').strip(): raise ValueError('human adjudication reason required')
    rows = {c.criterion_id:c for c in a.criteria}
    if len(rows) != len(a.criteria) or set(rows) != {c.criterion_id for c in rubric.criteria}:
        raise ValueError('explicit decision required for every rubric criterion')
    for criterion in rubric.criteria:
        row = rows[criterion.criterion_id]
        if row.final_points > criterion.max_points: raise ValueError('criterion exceeds approved maximum')
        if criterion.credit_levels and row.final_points not in {0,criterion.max_points,*(v.points for v in criterion.credit_levels)}:
            raise ValueError('select an approved credit level')
        for rule in criterion.dependency_rules:
            if rule.kind=='MATHEMATICAL' and row.final_points>0:
                prerequisite=next(c for c in rubric.criteria if c.criterion_id==rule.criterion_id)
                minimum=rule.minimum_points if rule.minimum_points is not None else prerequisite.max_points
                if rows[rule.criterion_id].final_points<minimum:raise ValueError('mathematical prerequisite not satisfied')
        if criterion.dependencies and not (row.dependency_justification or '').strip():
            raise ValueError('explain application of rubric dependencies')
    if body.final_points is None or sum(c.final_points for c in a.criteria) != body.final_points:
        raise ValueError('final score must equal explicit criterion scores')
    if body.final_points > rubric.max_score: raise ValueError('final score exceeds approved maximum')
    return a


def event(decision):
    """Own event derived from an immutable signed/hashed human decision record."""
    return dict(event_type='dynamic_human_adjudicated',
        event_id=decision['human_decision_id']+':dynamic_human_adjudicated',
        timestamp=decision['decided_at'], actor_id=decision['decided_by_user_id'],
        case_id=decision['case_id'], audit_run_id=decision['audit_run_id'],
        reconciliation_id=decision['reconciliation_id'],
        independent_review_id=decision['independent_review_id'],
        transcription_version_id=decision['transcription_version_id'],
        human_decision_id=decision['human_decision_id'],
        schema_version=decision['adjudication']['schema_version'],
        rubric_sha256=decision['adjudication']['rubric_sha256'],
        criterion_ids=[c['criterion_id'] for c in decision['adjudication']['criteria']],
        reason=decision['override_reason'], final_points=decision['final_points'],
        automatic_suggested_points=decision['suggested_points'],
        origin='HUMAN_ADJUDICATION', formal_certification=False, engine_mode='DYNAMIC',
        **{k:decision[k] for k in ('assessment_id','participant_id','submission_id',
            'question_attempt_id','engine_version') if k in decision})
