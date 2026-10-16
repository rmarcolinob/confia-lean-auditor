"""P2-ASSMT-01 closed contracts. All persisted timestamps are UTC."""
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from confia_lean_auditor.institutional.models import InstitutionId
from confia_lean_auditor.submissions.schemas import Sha256

AssessmentStatus = Literal["DRAFT", "PUBLISHED", "CLOSED"]


class AssessmentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Assessment(AssessmentModel):
    assessment_id: str = Field(pattern=r"^asmt_[0-9a-f]{32}$")
    title: str = Field(min_length=1, max_length=160)
    instructions: str = Field(default="", max_length=10000)
    teacher_user_id: str = Field(min_length=1, max_length=80)
    network_id: InstitutionId
    school_id: InstitutionId
    classroom_id: InstitutionId
    academic_year: int = Field(ge=2000, le=2100)
    status: AssessmentStatus = "DRAFT"
    opens_at: datetime
    closes_at: datetime
    created_at: datetime
    published_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    definition_sha256: Optional[Sha256] = None
    schema_version: Literal["1.0"] = "1.0"

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


class AssessmentProgress(AssessmentModel):
    assessment: Assessment
    items: list[AssessmentItem]
    students: list[dict]
