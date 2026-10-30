"""SCORE-POLICY-02: numeric suggestions, independent of mathematical verification."""
from .assessment import refresh_assessment
from . import secondary_adjudicator
from .secondary_context import prepare_payload

POLICY = "SCORE-POLICY-02"
# Invalid/unknown problem assets remain HTTP 400/404 before a rubric can be built.
# Unrecoverable pipeline failures remain HTTP errors; no fabricated AuditResponse.
UNSCORABLE_REASONS = {"EMPTY_SOLUTION", "INVALID_RUBRIC", "ADJUDICATOR_UNAVAILABLE",
    "ADJUDICATOR_TIMEOUT", "ADJUDICATOR_CONNECTION_FAILED", "ADJUDICATOR_AUTHORIZATION_FAILED", "ADJUDICATOR_RATE_LIMIT",
    "ADJUDICATOR_REQUEST_FAILED", "ADJUDICATOR_INCOMPLETE_RESPONSE",
    "ADJUDICATOR_INVALID_RESPONSE", "ADJUDICATOR_INVALID_CRITERIA",
    "ADJUDICATOR_INVALID_POINTS", "ADJUDICATOR_INVALID_EVIDENCE", "ADJUDICATOR_MISSING_RATIONALE"}


def apply_scoring_policy(*, rubric, solution, assets, claim_extraction,
                         microclaims, student_claim_checks, technical_issue=False, claim_context=None):
    refresh_assessment(rubric)
    rubric.scoring_policy = POLICY
    rubric.coverage = rubric.evaluated_max_score / rubric.max_score if rubric.max_score > 0 else 0.0
    rubric.estimated_points = None
    rubric.unscorable_reason = None
    rubric.secondary_adjudication = None
    rubric.needs_review = bool(technical_issue or any(c.get("status") not in {"verified", "refuted"}
                                                   for c in student_claim_checks) or any(
        i.points is None or i.verification_status == "technical_error" for i in rubric.items))
    for item in rubric.items:
        item.verified_points = item.points
        item.suggested_points = item.points
        item.scoring_basis = "first_pass" if item.points is not None else "unscorable"
        item.scoring_evidence = [item.evidence] if item.evidence else []
        item.scoring_rationale = ("Pontuação da primeira passagem preservada."
                                  if item.points is not None else None)
    if not solution.strip():
        return unscorable(rubric, "EMPTY_SOLUTION")
    if not rubric.items or rubric.max_score <= 0:
        return unscorable(rubric, "INVALID_RUBRIC")
    pending = [item for item in rubric.items if item.points is None]
    if pending:
        try:
            payload = prepare_payload(pending=pending, solution=solution, assets=assets,
                microclaims=microclaims, student_checks=student_claim_checks, claim_context=claim_context)
            decisions, metadata = secondary_adjudicator.adjudicate(payload)
            secondary_adjudicator.validate_decisions(decisions, payload)
        except secondary_adjudicator.AdjudicationError as exc:
            rubric.secondary_adjudication = exc.diagnostics or {
                "prompt_version": secondary_adjudicator.PROMPT_VERSION,
                "schema_version": secondary_adjudicator.SCHEMA_VERSION,
                "validation_status": "rejected", "error_code": exc.code,
                "validation_error": {"category": exc.category, "field": exc.field,
                                     "criterion_id": exc.criterion_id},
                "attempts": 0, "retry_count": 0}
            return unscorable(rubric, exc.code)
        # Apply only after the entire response passes validation. Decided criteria
        # (including formally refuted zeroes) cannot appear in this response.
        for item in pending:
            decision = decisions[item.id]
            item.suggested_points = float(decision["suggested_points"])
            item.scoring_basis = "secondary_adjudication"
            item.scoring_evidence = decision["evidence"]
            item.scoring_rationale = decision["rationale"]
        rubric.secondary_adjudication = metadata
    rubric.score = sum(item.suggested_points for item in rubric.items)
    rubric.estimated_points = rubric.score - rubric.evaluated_score
    return rubric


def unscorable(rubric, reason):
    if reason not in UNSCORABLE_REASONS:
        raise ValueError("Unknown unscorable condition")
    rubric.score = None
    rubric.estimated_points = None
    rubric.needs_review = True
    rubric.unscorable_reason = reason
    return rubric
