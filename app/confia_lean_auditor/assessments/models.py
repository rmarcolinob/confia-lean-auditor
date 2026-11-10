"""P2-ASSMT-01 closed contracts. All persisted timestamps are UTC."""
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, model_serializer

from confia_lean_auditor.institutional.models import InstitutionId
from confia_lean_auditor.submissions.schemas import Sha256
from confia_lean_auditor.teacher_decisions.models import CorrectionStatus, StudentResult

AssessmentStatus = Literal["DRAFT", "PUBLISHED", "CLOSED"]


class AssessmentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Assessment(AssessmentModel):
    assessment_id: str = Field(pattern=r"^asmt_[0-9a-f]{32}$")
    title: str = Field(min_length=1, max_length=160)
    instructions: str = Field(default="", max_length=10000)
    teacher_user_id: str = Field(min_length=1, max_length=80)
    scope: Literal["INSTITUTIONAL", "TME"] = "INSTITUTIONAL"
    network_id: Optional[InstitutionId] = None
    school_id: Optional[InstitutionId] = None
    classroom_id: Optional[InstitutionId] = None
    academic_year: int = Field(ge=2000, le=2100)
    status: AssessmentStatus = "DRAFT"
    opens_at: datetime
    closes_at: datetime
    created_at: datetime
    published_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    definition_sha256: Optional[Sha256] = None
    schema_version: Literal["1.0", "2.0"] = "1.0"

    @model_serializer(mode="wrap")
    def legacy_shape(self, handler):
        data = handler(self)
        if self.scope == "INSTITUTIONAL" and "scope" not in self.model_fields_set:
            data.pop("scope", None)
        return data

    @field_validator("opens_at", "closes_at", "created_at", "published_at", "closed_at")
    @classmethod
    def utc_only(cls, value):
        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("timestamp must have timezone")
            value = value.astimezone(timezone.utc)
        return value

    @model_validator(mode="after")
    def coherent(self):
        institutions = (self.network_id, self.school_id, self.classroom_id)
        if self.scope == "INSTITUTIONAL" and not all(institutions):
            raise ValueError("institutional assessment requires network, school and classroom")
        if self.scope == "TME" and (any(institutions) or self.schema_version != "2.0"):
            raise ValueError("TME assessment requires schema 2.0 and no institutional binding")
        if self.opens_at >= self.closes_at:
            raise ValueError("opens_at must precede closes_at")
        if self.status == "DRAFT" and (self.published_at or self.closed_at or self.definition_sha256):
            raise ValueError("draft cannot carry publication data")
        if self.status != "DRAFT" and (not self.published_at or not self.definition_sha256):
            raise ValueError("published assessment requires timestamp and definition hash")
        if self.status == "CLOSED" and not self.closed_at:
            raise ValueError("closed assessment requires timestamp")
        return self


class AssessmentItem(AssessmentModel):
    assessment_item_id: str = Field(pattern=r"^ait_[0-9a-f]{32}$")
    assessment_id: str = Field(pattern=r"^asmt_[0-9a-f]{32}$")
    problem_id: str = Field(min_length=1, max_length=80)
    order: int = Field(ge=1, le=100)
    points: float = Field(gt=0, le=1000)


class AssessmentParticipant(AssessmentModel):
    """Participation is not an authentication identity. Never stores civil identity."""
    participant_id: str = Field(pattern=r"^part_[0-9a-f]{32}$")
    assessment_id: str = Field(pattern=r"^asmt_[0-9a-f]{32}$")
    participant_kind: Literal["REGISTERED_USER", "EXTERNAL_PSEUDONYM"]
    user_id: Optional[str] = Field(default=None, min_length=1, max_length=80)
    external_namespace: Optional[str] = Field(default=None, min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._:-]+$")
    external_code: Optional[str] = Field(default=None, min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._:/-]+$")
    created_at: datetime
    schema_version: Literal["1.0"] = "1.0"

    @model_validator(mode="after")
    def identity_kind(self):
        if self.participant_kind == "REGISTERED_USER":
            if not self.user_id or self.external_code is not None or self.external_namespace is not None:
                raise ValueError("registered participant requires only user_id")
        elif not self.external_code or self.user_id is not None:
            raise ValueError("external participant requires code and no user_id")
        if self.created_at.tzinfo is None:
            raise ValueError("participant timestamp requires timezone")
        return self


class AssessmentDocument(AssessmentModel):
    assessment: Assessment
    items: list[AssessmentItem] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def coherent(self):
        if any(item.assessment_id != self.assessment.assessment_id for item in self.items):
            raise ValueError("item belongs to another assessment")
        if len({item.assessment_item_id for item in self.items}) != len(self.items):
            raise ValueError("duplicate item ID")
        if len({item.problem_id for item in self.items}) != len(self.items):
            raise ValueError("duplicate problem")
        if sorted(item.order for item in self.items) != list(range(1, len(self.items) + 1)):
            raise ValueError("item order must be contiguous")
        return self


class CreateAssessment(AssessmentModel):
    title: str = Field(min_length=1, max_length=160)
    instructions: str = Field(default="", max_length=10000)
    school_id: InstitutionId
    classroom_id: InstitutionId
    opens_at: datetime
    closes_at: datetime

    @field_validator("opens_at", "closes_at")
    @classmethod
    def utc_only(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must have timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def valid_window(self):
        if self.opens_at >= self.closes_at:
            raise ValueError("opens_at must precede closes_at")
        return self


class UpdateAssessment(AssessmentModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=160)
    instructions: Optional[str] = Field(default=None, max_length=10000)
    opens_at: Optional[datetime] = None
    closes_at: Optional[datetime] = None


class CreateAssessmentItem(AssessmentModel):
    problem_id: str = Field(min_length=1, max_length=80)
    points: float = Field(gt=0, le=1000)


class UpdateAssessmentItem(AssessmentModel):
    points: float = Field(gt=0, le=1000)


class AssessmentView(AssessmentDocument):
    teacher_name: str
    classroom_name: str
    availability: Literal["RASCUNHO", "AGENDADO", "DISPONÍVEL", "ENCERRADO"]
    submitted_item_ids: list[str] = Field(default_factory=list)
    released_results: list[StudentResult] = Field(default_factory=list)


class StudentProgress(AssessmentModel):
    user_id: str
    display_name: str
    submissions: dict[str, str]
    correction_statuses: dict[str, CorrectionStatus] = Field(default_factory=dict)


class AssessmentProgress(AssessmentModel):
    assessment: Assessment
    items: list[AssessmentItem]
    students: list[StudentProgress]
