"""DY5 immutable reconciliation and explicit automation policy contracts."""

from datetime import datetime
from typing import Literal, Optional
from decimal import Decimal
from pydantic import Field, model_validator
from .preparation_models import Evidence
from .grading_models import DynamicGradingContext, StudentClaim
from confia_lean_auditor.teacher_decisions.models import Points
from confia_lean_auditor.submissions.schemas import Sha256

PolicyProfile = Literal["FORMATIVE_LIST", "SCHOOL_EXAM"]
POLICY_VERSION = "dynamic-safe-automation.v1"
VERSION = "dynamic-reconciliation.v1"
Automation = Literal["AUTO_ACCEPT", "AUTO_ADJUST_UP", "AUTO_ADJUST_DOWN", "REVIEW_ONLY"]
ReconciliationStatus = Literal[
    "AGREEMENT_SUPPORTED",
    "AGREEMENT_UNVERIFIED",
    "CHECKER_RESOLVED",
    "GRADER_FALSE_CREDIT_CONFIRMED",
    "GRADER_MISSED_CREDIT_CONFIRMED",
    "SUFFICIENCY_DISAGREEMENT",
    "STRATEGY_DISAGREEMENT",
    "MATHEMATICAL_CONFLICT",
    "INSUFFICIENT_EVIDENCE",
    "TECHNICAL_ERROR",
    "REVIEW_REQUIRED",
]


class CriterionReconciliation(Evidence):
    criterion_id: str
    max_points: Points
    grader_points: Points
    reviewer_points: Optional[Points]
    grader_evidence: list[str]
    reviewer_evidence: list[str]
    mathematical_verification: list[StudentClaim]
    fidelity_binding_state: str
    sufficiency: str
    status: ReconciliationStatus
    reconciled_points: Points
    automation: Automation
    reason: str
    review_required: bool
    technical_uncertainty: bool
    recovered_credit: Points = Decimal(0)
    points_removed: Points = Decimal(0)

    @model_validator(mode="after")
    def consistent(self):
        if max(self.grader_points, self.reconciled_points) > self.max_points:
            raise ValueError("points exceed rubric")
        delta = self.reconciled_points - self.grader_points
        if self.recovered_credit != max(delta, 0) or self.points_removed != max(
            -delta, 0
        ):
            raise ValueError("invalid credit delta")
        if self.automation == "REVIEW_ONLY" and (delta or not self.review_required):
            raise ValueError("review only preserves provisional points")
        if (
            self.automation == "AUTO_ACCEPT"
            and delta
            or self.automation == "AUTO_ADJUST_UP"
            and delta <= 0
            or self.automation == "AUTO_ADJUST_DOWN"
            and delta >= 0
        ):
            raise ValueError("invalid automation direction")
        return self


class DynamicReconciliation(Evidence):
    schema_version: Literal["dynamic-reconciliation.v1"] = VERSION
    reconciliation_id: str = Field(pattern=r"^drec_[0-9a-f]{64}$")
    grader_audit_run_id: str
    independent_review_id: str
    question_attempt_id: str
    transcription_version_id: str
    context: DynamicGradingContext
    assessment_id: str
    assessment_definition_sha256: Sha256
    policy_profile: PolicyProfile
    policy_version: Literal["dynamic-safe-automation.v1"] = POLICY_VERSION
    grader_score_snapshot: Points
    reviewer_score_snapshot: Optional[Points]
    reconciled_suggested_score: Points
    max_score: Points
    criteria: list[CriterionReconciliation]
    review_required: bool
    review_reasons: list[str]
    technical_uncertainty: bool
    provenance: dict
    started_at: datetime
    completed_at: datetime
    events: list[dict]

    @model_validator(mode="after")
    def coherent(self):
        if (
            len({c.criterion_id for c in self.criteria}) != len(self.criteria)
            or not self.criteria
        ):
            raise ValueError("invalid criterion set")
        if (
            self.reconciled_suggested_score
            != sum(c.reconciled_points for c in self.criteria)
            or self.grader_score_snapshot != sum(c.grader_points for c in self.criteria)
            or self.max_score != sum(c.max_points for c in self.criteria)
        ):
            raise ValueError("inconsistent reconciliation totals")
        if (
            self.review_required != bool(self.review_reasons)
            or self.completed_at < self.started_at
        ):
            raise ValueError("inconsistent review/chronology")
        return self
