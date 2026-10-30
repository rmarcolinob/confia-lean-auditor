from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import Field, model_validator

from confia_lean_auditor.capture.schemas import Identifier, MAX_PAGES
from confia_lean_auditor.submissions.schemas import SubmissionModel, Sha256
from confia_lean_auditor.teacher_decisions.models import Points


class ScanPage(SubmissionModel):
    page_id: Identifier
    index: int = Field(ge=0, lt=MAX_PAGES)
    original_mime: Literal["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"]
    captured_at: datetime
    rotation_degrees: Literal[0, 90, 180, 270] = 0
    derived_mime: Literal["image/png"] = "image/png"
    derived_width: int = Field(ge=1, le=2048)
    derived_height: int = Field(ge=1, le=2048)
    transformation: Literal["canvas-orient-and-normalize-png-v1"] = "canvas-orient-and-normalize-png-v1"


class ScanSnapshot(SubmissionModel):
    schema_version: Literal["tme-scan-1.0"] = "tme-scan-1.0"
    snapshot_id: Identifier
    problem_id: Identifier
    pages: list[ScanPage] = Field(min_length=1, max_length=MAX_PAGES)

    @model_validator(mode="after")
    def contiguous(self):
        if sorted(page.index for page in self.pages) != list(range(len(self.pages))):
            raise ValueError("scan pages must be contiguous")
        if len({page.page_id for page in self.pages}) != len(self.pages):
            raise ValueError("scan page IDs must be unique")
        return self


class CaseCreate(SubmissionModel):
    problem_id: Identifier
    external_candidate_ref: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._:/-]+$")
    source_mode: Literal["DIGITAL_INK", "IMAGE_SCAN"]


class CorrectionCase(CaseCreate):
    case_id: str = Field(pattern=r"^case_[0-9a-f]{32}$")
    created_by_user_id: str
    created_at: datetime
    status: Literal["IDENTIFIED", "SOURCE_READY", "DECIDED"] = "IDENTIFIED"
    submission_id: Optional[str] = Field(default=None, pattern=r"^sub_[0-9a-f]{32}$")
    schema_version: Literal["1.0"] = "1.0"


class ScanPageUpload(SubmissionModel):
    original_base64: str = Field(min_length=1, max_length=12_000_000)
    derived_png_base64: str = Field(min_length=1, max_length=12_000_000)
    original_mime: Literal["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"]
    captured_at: datetime
    rotation_degrees: Literal[0, 90, 180, 270] = 0
    derived_width: int = Field(ge=1, le=2048)
    derived_height: int = Field(ge=1, le=2048)


class ScanUpload(SubmissionModel):
    pages: list[ScanPageUpload] = Field(min_length=1, max_length=MAX_PAGES)


class EvaluatorDecisionRequest(SubmissionModel):
    audit_run_id: Optional[str] = Field(default=None, pattern=r"^aud_[0-9a-f]{64}$")
    max_points: Decimal = Field(gt=0, le=1000, decimal_places=2)
    final_points: Points
    feedback: str = Field(default="", max_length=10000)
    override_reason: Optional[str] = Field(default=None, max_length=2000)


class EvaluatorDecision(EvaluatorDecisionRequest):
    case_id: str
    decided_by_user_id: str
    decided_at: datetime
    audit_source_sha256: Optional[Sha256] = None
    audit_result_sha256: Optional[Sha256] = None
    suggested_points: Optional[Points] = None
    schema_version: Literal["1.0"] = "1.0"
