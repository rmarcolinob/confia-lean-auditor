"""Grounded test inputs use the same original-text boundary as production."""
from dataclasses import replace
from confia_lean_auditor.student_claims.registry import extract_student_claims
from confia_lean_auditor.student_claims.grounding import has_valid_grounding


def grounded_claim(problem, kind, source):
    claim=next(c for c in extract_student_claims(problem,source) if c.claim_type==kind)
    assert has_valid_grounding(claim), (source,claim)
    return claim


def bind_check(check, source):
    claim=grounded_claim(check.problem_id,check.claim_type,source)
    return replace(check,data=claim.data,grounding=claim.grounding)
