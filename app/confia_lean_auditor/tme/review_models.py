"""D2 source projection and workspace contracts; transcription versions are reused."""
from typing import Literal, Optional
from pydantic import Field, model_validator
from confia_lean_auditor.submissions.schemas import SubmissionModel, TranscriptionSegment
from .exam_models import ExamAsset, ExamPage


class QuestionSourcePage(SubmissionModel):
    index: int = Field(ge=0, lt=50)
    page_id: str
    exam_page: ExamPage
    original: ExamAsset
    preview: ExamAsset
    derived_width: int
    derived_height: int


class QuestionSourceSnapshot(SubmissionModel):
    schema_version: Literal["exam-question-source.v1"] = "exam-question-source.v1"
    snapshot_id: str
    question_attempt_id: str = Field(pattern=r"^case_[0-9a-f]{32}$")
    exam_submission_id: str = Field(pattern=r"^exam_[0-9a-f]{32}$")
    problem_id: str
    mapping_version: int = Field(ge=1)
    pages: list[QuestionSourcePage] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def consistent_pages(self):
        if [p.index for p in self.pages] != list(range(len(self.pages))):
            raise ValueError("source indices must be contiguous")
        if len({p.page_id for p in self.pages}) != len(self.pages):
            raise ValueError("duplicate source page")
        for p in self.pages:
            if (p.page_id != p.exam_page.exam_page_id or p.exam_page.submission_id != self.exam_submission_id
                    or p.original.asset_id != p.exam_page.original_asset_id
                    or p.preview.asset_id != p.exam_page.preview_asset_id
                    or p.preview.media_type != "image/png"
                    or (p.derived_width, p.derived_height) != (p.exam_page.width, p.exam_page.height)):
                raise ValueError("source provenance mismatch")
        return self


class CreateQuestionTranscription(SubmissionModel):
    origin: Literal["manual", "capture"] = "manual"
    expected_mapping_version: int = Field(ge=1)
    segments: Optional[list[TranscriptionSegment]] = Field(default=None, min_length=1, max_length=2000)

    @model_validator(mode="after")
    def coherent(self):
        if (self.origin == "manual") != (self.segments is not None):
            raise ValueError("manual requires segments; capture imports server-held candidates")
        return self
