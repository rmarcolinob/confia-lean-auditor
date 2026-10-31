"""Opt-in exact ℚ arithmetic using the existing student proof lifecycle.

No integer division, variables, caller-supplied tactics, or perceptual facts.
"""
import hashlib

from confia_lean_auditor.claims.common.adapters import claim_from_student
from confia_lean_auditor.claims.common.schemas import Provenance, CanonicalForm
from confia_lean_auditor.core.math_canonical import parse_math
from confia_lean_auditor.core.math_canonical.rational import closed_equality, lean_rational_expression
from confia_lean_auditor.lean.student_claim_checker import CHECK_DIR, _run_lean_file
from confia_lean_auditor.lean.student_proof import evaluate_student_proof
from confia_lean_auditor.student_claims.grounding import VERSION, _digest, _payload, source_matches
from confia_lean_auditor.student_claims.schemas import StudentClaim


def check_rational_record(record, expression, source_text, *, run_id, index, timeout_seconds=90):
    pair = closed_equality(expression)
    if pair is None:
        return None
    left, right = map(lean_rational_expression, pair)
    if left is None or right is None:
        return None
    claim = StudentClaim(id="rational-" + hashlib.sha256(record.record_id.encode()).hexdigest()[:20],
        problem_id=record.problem_id, claim_type="arithmetic_equality", raw_text=record.source.raw_text,
        normalized_text=record.source.raw_text, context=record.source.raw_text,
        data={"left_expr": pair[0], "right_expr": pair[1], "number_domain": "Q"})
    claim.grounding = dict(status="grounded", validator=VERSION, extraction_method="exact-rational-projection.v1",
        source_text=record.source.raw_text, source_start=record.source.source_start,
        source_end=record.source.source_end, source_sha256=record.source.source_sha256,
        payload_sha256=_digest(_payload(claim)))
    if not record.source.attributable or not source_matches(claim, source_text):
        return None
    projected = claim_from_student(claim, solution_text=source_text, rubric_links=record.rubric_links)
    if projected.source != record.source:
        return None
    # Keep this as a native common record. The existing legacy projection API
    # must not route a rational-domain payload to its integer-only checker.
    canonical = parse_math(expression).canonical_form.to_dict()
    projected = projected.model_copy(update={
        "record_id": "native:rational:" + claim.id,
        "provenance": Provenance(origin=projected.provenance.origin, channel="native",
            legacy_id=claim.id, extraction_method="exact-rational-projection.v1"),
        "canonical_form": CanonicalForm(family="mathematical", subject="rational_equality",
            value=canonical, mathematical_form=canonical, method="exact-rational-projection.v1"),
        "canonicalization_status": "parsed",
        "canonicalization_reason": "Exact rational equality; opt-in checker only"})
    directory = CHECK_DIR / run_id
    directory.mkdir(parents=True, exist_ok=True)
    statement = f"{left} = {right}"
    name = f"rational_check_{index}"
    code = f"import Mathlib\n\ntheorem {name} : {statement} := by\n  norm_num\n"
    negation = f"import Mathlib\n\ntheorem {name}_refutation : ¬ ({statement}) := by\n  norm_num\n"
    check = evaluate_student_proof(claim=claim, lean_file=directory / (name + ".lean"),
        lean_statement=statement, method="norm_num", lean_code=code, negation_code=negation,
        runner=_run_lean_file, timeout_seconds=timeout_seconds)
    return projected, check
