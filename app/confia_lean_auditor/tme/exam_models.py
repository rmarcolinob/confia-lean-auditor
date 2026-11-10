"""D1 capture contracts. No grading state is fabricated by capture."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import Field, model_validator

from confia_lean_auditor.assessments.models import AssessmentDocument, AssessmentParticipant, CreateAssessmentItem
from confia_lean_auditor.submissions.schemas import SubmissionModel, Sha256
from .models import CorrectionCase

MAX_EXAM_PAGES = 50
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
MAX_TOTAL_BYTES = 40 * 1024 * 1024
MAX_CAPTURE_BODY = 60 * 1024 * 1024
Mime = Literal["application/pdf", "image/jpeg", "image/png", "image/webp"]


class TMEAssessmentCreate(SubmissionModel):
    title: str = Field(min_length=1, max_length=160)
    instructions: str = Field(default="", max_length=10000)
    academic_year: int = Field(ge=2000, le=2100)
    items: list[CreateAssessmentItem] = Field(min_length=1, max_length=100)


class CaptureMetadata(SubmissionModel):
    captured_at: Optional[datetime] = None
    producer: str = Field(default="confia-tme", min_length=1, max_length=80)
    producer_version: str = Field(default="1.0", min_length=1, max_length=80)


class OriginalUpload(SubmissionModel):
    media_type: Mime
    content_base64: str = Field(min_length=1, max_length=28_000_000)
    rotation_degrees: Literal[0, 90, 180, 270] = 0


class CapturePageHint(SubmissionModel):
    page_number: int = Field(ge=1, le=MAX_EXAM_PAGES)
    question_hint: Optional[str] = Field(default=None, min_length=1, max_length=80)
    transcription_candidate: Optional[str] = Field(default=None, max_length=20_000)
    transcription_provider: Optional[str] = Field(default=None, max_length=80)
    transcription_version: Optional[str] = Field(default=None, max_length=80)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)


class ExamCapturePackage(SubmissionModel):
    schema_version: Literal["exam-capture-package.v1"] = "exam-capture-package.v1"
    assessment_identifier: str = Field(pattern=r"^asmt_[0-9a-f]{32}$")
    external_participant_code: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._:/-]+$")
    external_namespace: str = Field(default="tme", min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._:-]+$")
    idempotency_key: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9._:-]+$")
    original_documents: list[OriginalUpload] = Field(min_length=1, max_length=MAX_EXAM_PAGES)
    capture_metadata: CaptureMetadata = Field(default_factory=CaptureMetadata)
    pages: list[CapturePageHint] = Field(default_factory=list, max_length=MAX_EXAM_PAGES)

    @model_validator(mode="after")
    def single_pdf_or_images(self):
        if any(doc.media_type == "application/pdf" for doc in self.original_documents) and len(self.original_documents) != 1:
            raise ValueError("send one PDF or a list of images")
        if len({p.page_number for p in self.pages}) != len(self.pages):
            raise ValueError("duplicate capture page metadata")
        return self


class ExamAsset(SubmissionModel):
    asset_id: str = Field(pattern=r"^(original|preview)_[0-9]{4}$")
    media_type: Mime
    sha256: Sha256
    byte_size: int = Field(gt=0)


class ExamPage(SubmissionModel):
    exam_page_id: str = Field(pattern=r"^page_[0-9a-f]{32}$")
    submission_id: str = Field(pattern=r"^exam_[0-9a-f]{32}$")
    page_number: int = Field(ge=1, le=MAX_EXAM_PAGES)
    original_asset_id: str
    original_page_number: int = Field(ge=1)
    preview_asset_id: str
    width: int = Field(gt=0, le=2048)
    height: int = Field(gt=0, le=2048)
    rotation_degrees: Literal[0, 90, 180, 270] = 0
    processing_state: Literal["PREVIEW_READY"] = "PREVIEW_READY"
    transformation: str


class QuestionAttemptPage(SubmissionModel):
    question_attempt_id: str = Field(pattern=r"^case_[0-9a-f]{32}$")
    exam_page_id: str = Field(pattern=r"^page_[0-9a-f]{32}$")
    order: int = Field(ge=1, le=MAX_EXAM_PAGES)


class PageMapping(SubmissionModel):
    version: int = Field(ge=1)
    bindings: list[QuestionAttemptPage] = Field(default_factory=list, max_length=5000)
    updated_at: datetime
    updated_by: str


class UpdatePageMapping(SubmissionModel):
    expected_version: int = Field(ge=1)
    bindings: list[QuestionAttemptPage] = Field(max_length=5000)


class ExamSubmission(SubmissionModel):
    schema_version: Literal["exam-submission.v1"] = "exam-submission.v1"
    submission_id: str = Field(pattern=r"^exam_[0-9a-f]{32}$")
    assessment_id: str
    assessment_definition_sha256: Sha256
    participant_id: str
    created_by_user_id: str
    created_at: datetime
    status: Literal["RECEIVED"] = "RECEIVED"
    source: Literal["PDF", "IMAGES"]
    page_count: int = Field(ge=1, le=MAX_EXAM_PAGES)
    capture_metadata: CaptureMetadata
    capture_pages: list[CapturePageHint]
    original_documents: list[ExamAsset]
    previews: list[ExamAsset]
    pages: list[ExamPage]
    question_attempt_ids: list[str]
    request_sha256: Sha256


class ExamDetail(SubmissionModel):
    submission: ExamSubmission
    assessment: AssessmentDocument
    participant: AssessmentParticipant
    question_attempts: list[CorrectionCase]
    mapping: PageMapping


class QuestionAttemptView(SubmissionModel):
    question_attempt: CorrectionCase
    pages: list[ExamPage]
    mapping_version: int
    mapping_state: Literal["UNASSIGNED", "READY"]
