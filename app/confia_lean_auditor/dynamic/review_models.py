"""DY4: blind proposals, checked independent opinions, and immutable comparisons."""

from datetime import datetime
from typing import Literal, Optional
from pydantic import Field, model_validator, model_serializer
from .preparation_models import Evidence, GenerationProvenance
from .grading_models import DynamicGradingContext, StudentClaim
from confia_lean_auditor.teacher_decisions.models import Points
from confia_lean_auditor.submissions.schemas import Sha256

VERSION = "dynamic-reviewer.v1"


class AdditionalClaim(Evidence):
    claim_id: str = Field(pattern=r"^extra_[A-Za-z0-9_-]{1,60}$")
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    quote: str = Field(min_length=1, max_length=2000)


class CriterionProposal(Evidence):
    criterion_id: str
    assessment: Literal[
        "COMPLETE", "PARTIAL", "NOT_SATISFIED", "INSUFFICIENT", "CONFLICT"
    ]
    proposed_points: Optional[str] = Field(
        default=None, pattern=r"^(0|[1-9][0-9]{0,3})(\.[0-9]{1,2})?$"
    )
    claim_ids: list[str] = Field(max_length=80)
    explanation: str = Field(min_length=1, max_length=2000)
    uncertainty: list[str] = Field(max_length=20)


class BlindReviewProposal(Evidence):
    detected_strategy: str = Field(max_length=500)
    alternative_strategy: bool
    additional_claims: list[AdditionalClaim] = Field(max_length=40)
    criterion_reviews: list[CriterionProposal] = Field(min_length=1, max_length=100)
    warnings: list[str] = Field(max_length=30)


class CriterionReview(Evidence):
    criterion_id: str
    max_points: Points
    proposed_points: Optional[Points]
    provider_proposed_points: Optional[Points]
    assessment: str
    sufficiency: str
    claim_ids: list[str]
    evidence: list[str]
    checker_references: list[dict]
    explanation: str
    uncertainty: list[str]
    review_required: bool

    @model_validator(mode="after")
    def bounded(self):
        if any(
            value is not None and value > self.max_points
            for value in [self.proposed_points, self.provider_proposed_points]
        ):
            raise ValueError("review exceeds criterion maximum")
        return self


class IndependentPhase(Evidence):
    semantic_reviews: Optional[dict] = None

    @model_serializer(mode='wrap')
    def preserve_phase(self, handler):
        data=handler(self)
        if 'semantic_reviews' not in self.model_fields_set: data.pop('semantic_reviews',None)
        return data

    criterion_reviews: list[CriterionReview]
    claims: list[StudentClaim]
    additional_claims: list[StudentClaim]
    rejected_claims: list[dict]
    detected_strategy: str
    alternative_strategy: bool
    warnings: list[str]
    review_required: bool
    proposal: BlindReviewProposal
    provenance: GenerationProvenance
    input_sha256: Sha256
    completed_at: datetime


class CriterionComparison(Evidence):
    criterion_id: str
    grader_points: Points
    reviewer_points: Optional[Points]
    grader_status: str
    reviewer_status: str
    agreement: Literal["AGREEMENT", "DISAGREEMENT", "UNRESOLVED"]
    difference: Optional[float]
    disagreement_types: list[str]
    evidence_overlap: list[str]
    reason: str
    review_required: bool


class DynamicReviewComparison(Evidence):
    criteria: list[CriterionComparison]
    exact_agreement: bool
    agreement_count: int
    total_point_difference: Optional[float]
    conflicting_criteria: list[str]
    review_required: bool
    status: Literal["AGREEMENT", "DISAGREEMENT", "INCONCLUSIVE"]


class DynamicIndependentReview(Evidence):
    schema_version: Literal["dynamic-independent-review.v1"] = (
        "dynamic-independent-review.v1"
    )
    review_id: str = Field(pattern=r"^drev_[0-9a-f]{64}$")
    audit_run_id: str
    audit_run_sha256: Sha256
    audit_result_sha256: Sha256
    source_sha256: Sha256
    question_attempt_id: str
    transcription_version_id: str
    context: DynamicGradingContext
    reviewer_version: Literal["dynamic-reviewer.v1"] = VERSION
    execution_key: str
    started_at: datetime
    completed_at: datetime
    status: Literal["COMPLETED", "FAILED"]
    phase_a: Optional[IndependentPhase]
    comparison: Optional[DynamicReviewComparison]
    phase_a_input: dict
    context_snapshot: dict
    review_required: bool
    error_code: Optional[str] = None
    events: list[dict]

    @model_validator(mode="after")
    def coherent(self):
        if self.completed_at < self.started_at:
            raise ValueError("invalid review chronology")
        if self.status == "COMPLETED" and (
            not self.phase_a or not self.comparison or self.error_code
        ):
            raise ValueError("missing independent result")
        if self.status == "FAILED" and (
            self.phase_a
            or self.comparison
            or not self.error_code
            or not self.review_required
        ):
            raise ValueError("failed review is not agreement")
        if self.phase_a and self.phase_a.completed_at > self.completed_at:
            raise ValueError("comparison precedes independent analysis")
        return self
