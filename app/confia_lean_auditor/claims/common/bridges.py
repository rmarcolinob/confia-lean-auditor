"""Explicit compatibility boundaries to P0 gates and existing checker inputs."""
from confia_lean_auditor.rubric.positive_evidence import can_support_rubric_credit
from confia_lean_auditor.student_claims.grounding import source_matches
from confia_lean_auditor.student_claims.schemas import is_mathematically_refuted
from .adapters import payload_copy, project_extracted_claim, project_student_claim


def positive_credit_from_record(*, record, solution_text, **verification):
    claim = project_extracted_claim(record, solution_text=solution_text) if record is not None else None
    if record is not None and record.problem_id != verification['problem_id']:
        raise ValueError('Reference record belongs to a different problem')
    return can_support_rubric_credit(claim=claim, solution_text=solution_text, **verification)


def matching_student_check(record, check, *, solution_text, statement_text=''):
    try:
        claim = project_student_claim(record, solution_text=solution_text, statement_text=statement_text)
    except ValueError:
        return False
    data = payload_copy(check)
    return (data.get('id') == claim.id and data.get('problem_id') == claim.problem_id
            and data.get('claim_type') == claim.claim_type and data.get('data') == claim.data
            and source_matches(data, solution_text))


def record_is_mathematically_refuted(record, check, *, solution_text, statement_text=''):
    return (matching_student_check(record, check, solution_text=solution_text, statement_text=statement_text)
            and is_mathematically_refuted(check))


def checker_input_from_record(record, *, solution_text, statement_text=''):
    """Common record -> exact legacy input -> existing proposition renderer.

    No rendering, proof tactic, checker dispatch or timeout is changed here.
    References and unresolved interpretations are rejected before this boundary.
    """
    return project_student_claim(record, solution_text=solution_text, statement_text=statement_text)


def canonical_input_from_record(record, *, solution_text, statement_text=''):
    """Optional mathematical view for checkers; no proposition is changed here."""
    from .adapters import validate_projection
    from .canonical import mathematical_value
    from confia_lean_auditor.core.math_canonical.models import canonical_from_dict
    validate_projection(record, solution_text=solution_text, statement_text=statement_text)
    if record.provenance.channel=='student' and not record.source.attributable:
        raise ValueError('Canonical input still requires attributable grounding')
    data=mathematical_value(record.canonical_form)
    return canonical_from_dict(data) if data is not None else None
