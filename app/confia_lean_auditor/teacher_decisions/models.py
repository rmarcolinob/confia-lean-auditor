"""P2-DEC-01 closed contracts. Decimal values are serialized as JSON strings."""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from confia_lean_auditor.submission_audits.schemas import AuditRunId
from confia_lean_auditor.submissions.schemas import Sha256, SubmissionId

DecisionId = Annotated[str, Field(pattern=r"^dec_[0-9a-f]{32}$")]
Points = Annotated[Decimal, Field(ge=0, le=1000, decimal_places=2)]
CENT = Decimal("0.01")


def suggested_points(points, score, maximum):
    if score is None or maximum is None or maximum <= 0:
        return None
    if score < 0 or score > maximum:
        return None
    normalized = (points * score / maximum).quantize(CENT, rounding=ROUND_HALF_UP)
    # Existing AssessmentItems can have more than two decimal places.
    return min(normalized, points.quantize(CENT, rounding=ROUND_DOWN))


class DecisionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class TeacherDecision(DecisionModel):
    decision_id: DecisionId
    submission_id: SubmissionId
    assessment_id: str = Field(pattern=r"^asmt_[0-9a-f]{32}$")
    assessment_item_id: str = Field(pattern=r"^ait_[0-9a-f]{32}$")
    assessment_definition_sha256: Sha256
    problem_id: str = Field(min_length=1, max_length=80)
    teacher_user_id: str = Field(min_length=1, max_length=80)
    audit_run_id: Optional[AuditRunId] = None
    audit_source_sha256: Optional[Sha256] = None
    audit_result_sha256: Optional[Sha256] = None
    confia_score_raw: Optional[Decimal] = None
    confia_max_score_raw: Optional[Decimal] = None
    confia_suggested_points: Optional[Points] = None
    item_max_points: Decimal = Field(gt=0, le=1000)
    teacher_final_points: Optional[Points] = None
    teacher_feedback: str = Field(default="", max_length=10000)
    teacher_internal_note: Optional[str] = Field(default=None, max_length=10000)
    override_reason: Optional[str] = Field(default=None, max_length=2000)
    status: Literal["DRAFT", "FINALIZED", "RELEASED"] = "DRAFT"
    created_at: datetime
    updated_at: datetime
    finalized_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    decision_sha256: Optional[Sha256] = None
    version: int = Field(default=1, ge=1)
    schema_version: Literal["1.0"] = "1.0"

    @field_validator("created_at", "updated_at", "finalized_at", "released_at")
    @classmethod
    def utc_only(cls, value):
        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("timestamp must have timezone")
            return value.astimezone(timezone.utc)
        return value

    @field_validator("teacher_final_points", "confia_suggested_points")
    @classmethod
    def canonical_points(cls, value):
        return value.quantize(CENT) if value is not None else None

    @model_validator(mode="after")
    def coherent(self):
        if self.teacher_final_points is not None and self.teacher_final_points > self.item_max_points:
            raise ValueError("final points exceed item points")
        if self.confia_suggested_points is not None and self.confia_suggested_points != suggested_points(
                self.item_max_points, self.confia_score_raw, self.confia_max_score_raw):
            raise ValueError("invalid normalized suggestion")
        snapshot = (self.audit_source_sha256, self.audit_result_sha256, self.confia_score_raw,
                    self.confia_max_score_raw, self.confia_suggested_points)
        if self.audit_run_id is None and any(value is not None for value in snapshot):
            raise ValueError("manual decision cannot carry audit provenance")
        if self.audit_run_id is not None and self.audit_source_sha256 is None:
            raise ValueError("audit source hash required")
        if self.updated_at < self.created_at:
            raise ValueError("invalid update timestamp")
        if self.status == "DRAFT":
            if self.finalized_at or self.released_at or self.decision_sha256:
                raise ValueError("draft cannot carry finalization data")
        else:
            if self.teacher_final_points is None or self.finalized_at is None or self.decision_sha256 is None:
                raise ValueError("final decision requires points, timestamp and digest")
            if self.is_override and not (self.override_reason or "").strip():
                raise ValueError("override reason required")
            if not self.created_at <= self.finalized_at <= self.updated_at:
                raise ValueError("invalid finalization timestamp")
            if self.status == "FINALIZED" and self.released_at is not None:
                raise ValueError("unreleased decision cannot carry release timestamp")
            if self.status == "RELEASED" and (self.released_at is None
                    or not self.finalized_at <= self.released_at <= self.updated_at):
                raise ValueError("invalid release timestamp")
        return self

    @property
    def is_override(self):
        return (self.confia_suggested_points is not None and self.teacher_final_points is not None
                and self.confia_suggested_points != self.teacher_final_points)


class TeacherDecisionView(TeacherDecision):
    audit_state: Literal["none", "current", "stale", "unavailable"]


class CreateDecision(DecisionModel):
    # Selection only: the server resolves and validates every provenance field.
    audit_run_id: Optional[AuditRunId] = None


class UpdateDecision(CreateDecision):
    expected_version: int = Field(ge=1)
    teacher_final_points: Optional[Points] = None
    teacher_feedback: str = Field(default="", max_length=10000)
    teacher_internal_note: Optional[str] = Field(default=None, max_length=10000)
    override_reason: Optional[str] = Field(default=None, max_length=2000)


class FinalizeDecision(DecisionModel):
    expected_version: int = Field(ge=1)


class StudentResult(DecisionModel):
    assessment_id: str
    item_id: str
    problem_id: str
    status: Literal["corrected"] = "corrected"
    final_points: Points
    max_points: Decimal
    teacher_feedback: str
    released_at: datetime


CorrectionStatus = Literal["SUBMITTED", "TRANSCRIPTION_REVIEW", "ANALYSIS_AVAILABLE",
                           "DECISION_DRAFT", "DECISION_FINALIZED", "RESULT_RELEASED"]
