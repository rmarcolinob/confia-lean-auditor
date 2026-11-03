"""Common evidence and extraction-boundary conversions for Experiment B."""
from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    evidence_id: str = Field(min_length=1)
    claim_type: str
    normalized_payload: dict[str, Any]
    source_span: Optional[str] = None
    assertion_status: Literal["asserted", "hypothetical", "negated", "abandoned", "quoted_or_problem_text", "unclear"]
    polarity: Literal["positive", "negative", "unclear"]
    scope: Literal["main_argument", "exploration", "side_calculation", "final_conclusion"]
    hypothetical: bool
    abandoned: bool
    context_policy: Literal["legacy_context_assumed", "explicit_semantic_context"]
    extractor_mode: Literal["FORMAL_OFFLINE", "SEMANTIC_FORMAL"]
    extractor_model: Optional[str] = None
    raw_extractor_metadata: dict[str, Any] = Field(default_factory=dict)
    provenance_limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def coherent_context(self):
        if self.source_span is not None and not self.source_span.strip():
            raise ValueError("Empty source_span; use None for unavailable provenance")
        if self.assertion_status == "hypothetical" and not self.hypothetical:
            raise ValueError("Inconsistent hypothetical flag")
        if self.assertion_status == "abandoned" and not self.abandoned:
            raise ValueError("Inconsistent abandoned flag")
        return self

    def validate_source(self, problem_id: str, solution: str):
        from .semantic_student_claim import validate_payload
        if self.source_span is not None and self.source_span not in solution:
            raise ValueError("source_span is not an exact substring of student text")
        validate_payload(self.claim_type, self.normalized_payload, problem_id)
        return self

    def eligible_context(self):
        # Deliberately independent of mode, provenance and context_policy label.
        return (self.assertion_status == "asserted" and self.polarity == "positive"
                and not self.hypothetical and not self.abandoned
                and self.scope in {"main_argument", "final_conclusion"})


def from_semantic_claim(claim, problem_id, solution) -> EvidenceUnit:
    """LLM provenance is mandatory here, before the common scoring pipeline."""
    from .semantic_student_claim import SemanticStudentClaim
    parsed = SemanticStudentClaim.model_validate(claim.model_dump(mode="python"))
    parsed.validate_source(problem_id, solution)
    return EvidenceUnit.model_validate(parsed.model_dump(mode="python"))


def from_historical_claim(claim, problem_id, solution) -> EvidenceUnit:
    """No contextual inference: assign the explicitly declared legacy assumption."""
    from .semantic_student_claim import allowed_contracts, validate_payload
    if claim.problem_id != problem_id:
        raise ValueError("Historical claim problem mismatch")
    contract = allowed_contracts(problem_id).get(claim.claim_type)
    if contract is None:
        raise ValueError("Historical claim outside the closed contract")
    fields = contract["payload_schema"]["properties"]
    # Historical auxiliary strings are provenance, not checker inputs.
    payload = {key: claim.data[key] for key in fields if key in claim.data}
    validate_payload(claim.claim_type, payload, problem_id)
    span = claim.raw_text if claim.raw_text.strip() and claim.raw_text in solution else None
    result = EvidenceUnit(evidence_id=claim.id, claim_type=claim.claim_type,
        normalized_payload=payload, source_span=span, assertion_status="asserted",
        polarity="positive", scope="main_argument", hypothetical=False, abandoned=False,
        context_policy="legacy_context_assumed", extractor_mode="FORMAL_OFFLINE",
        raw_extractor_metadata={"legacy_raw_text": claim.raw_text,
            "legacy_normalized_text": claim.normalized_text, "legacy_context": claim.context,
            "legacy_data": claim.data, "context_is_inferred": False},
        provenance_limitations=[] if span is not None else ["source_span_unavailable"])
    return result.validate_source(problem_id, solution)
