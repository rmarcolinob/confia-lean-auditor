from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import Field, StringConstraints, model_validator

from confia_lean_auditor.capture.schemas import Identifier, MAX_PAGES
from confia_lean_auditor.submissions.schemas import (
    RecognitionProvenance, SegmentKind, Sha256, SubmissionId, SubmissionModel,
    TranscriptionId, TranscriptionSourceRegion,
)

RunId = Annotated[str, StringConstraints(pattern=r"^run_[0-9a-f]{32}$")]
Version = Annotated[str, StringConstraints(min_length=1, max_length=80)]
InputMode = Literal["strokes", "image", "strokes_and_image"]


class RecognitionSegment(SubmissionModel):
    page_index: int = Field(ge=0, lt=MAX_PAGES)
    order: int = Field(ge=0)
    kind: SegmentKind
    text: Optional[str] = Field(default=None, min_length=1, max_length=20_000)
    latex: Optional[str] = Field(default=None, min_length=1, max_length=20_000)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    source_region: Optional[TranscriptionSourceRegion] = None
    source_stroke_refs: Optional[list[Identifier]] = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def unique_refs(self):
        if self.source_stroke_refs is not None and len(self.source_stroke_refs) != len(set(self.source_stroke_refs)):
            raise ValueError("duplicate stroke references")
        return self


class RecognitionPageMetadata(SubmissionModel):
    page_index: int = Field(ge=0, lt=MAX_PAGES)
    provider_version: Optional[Version] = None
    provider_request_id: Optional[str] = Field(default=None, min_length=1, max_length=120)
    is_handwritten: Optional[bool] = None


class ProviderOutput(SubmissionModel):
    provider_version: Optional[Version] = None
    provider_request_id: Optional[str] = Field(default=None, min_length=1, max_length=120)
    segments: list[RecognitionSegment] = Field(min_length=1, max_length=2_000)
    page_metadata: list[RecognitionPageMetadata] = Field(default_factory=list, max_length=MAX_PAGES)
    warnings: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def unique_positions(self):
        positions = [(s.page_index, s.order) for s in self.segments]
        if len(positions) != len(set(positions)):
            raise ValueError("duplicate segment positions")
        metadata_pages = [item.page_index for item in self.page_metadata]
        if len(metadata_pages) != len(set(metadata_pages)) or any(
                index not in {segment.page_index for segment in self.segments} for index in metadata_pages):
            raise ValueError("invalid page metadata")
        if any(len(w) > 500 for w in self.warnings):
            raise ValueError("warning too long")
        return self


class RecognitionResult(ProviderOutput):
    recognizer_run_id: RunId
    submission_id: SubmissionId
    provider: Identifier
    adapter_version: Version
    input_mode: InputMode
    created_at: datetime
    latency_ms: Optional[float] = Field(default=None, ge=0)
    input_hash: Sha256
    output_hash: Sha256


class RecognitionRequest(SubmissionModel):
    provider: Identifier
    idempotency_key: Optional[Annotated[str, StringConstraints(
        pattern=r"^[A-Za-z0-9._:-]{1,128}$"
    )]] = None


class RecognitionRun(SubmissionModel):
    recognizer_run_id: RunId
    submission_id: SubmissionId
    status: Literal["NEEDS_REVIEW", "FAILED"]
    provenance: RecognitionProvenance
    result: Optional[RecognitionResult] = None
    error_code: Optional[Literal["PROVIDER_FAILED", "INVALID_PROVIDER_OUTPUT", "PROVIDER_TIMEOUT", "PROVIDER_BUSY"]] = None
    transcription_id: Optional[TranscriptionId] = None
    revision_number: Optional[int] = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_links(self):
        if self.provenance.submission_id != self.submission_id:
            raise ValueError("provenance submission mismatch")
        if self.status == "FAILED":
            if self.result is not None or self.transcription_id is not None or self.revision_number is not None or self.error_code is None:
                raise ValueError("failed run cannot create a transcription")
        else:
            if self.result is None or self.transcription_id is None or self.revision_number != 1 or self.error_code is not None:
                raise ValueError("successful run must reference its initial review revision")
            r, p = self.result, self.provenance
            if (r.recognizer_run_id != self.recognizer_run_id or r.submission_id != self.submission_id
                    or r.provider != p.provider or r.adapter_version != p.adapter_version
                    or r.input_mode != p.input_mode or r.input_hash != p.input_hash or r.created_at != p.created_at):
                raise ValueError("result provenance mismatch")
        return self


class RecognitionResponse(SubmissionModel):
    recognizer_run_id: RunId
    status: Literal["NEEDS_REVIEW", "FAILED"]
    transcription_id: Optional[TranscriptionId]
    revision_number: Optional[int]
    error_code: Optional[str]
    provenance: RecognitionProvenance

    @classmethod
    def from_run(cls, run):
        return cls.model_validate(run.model_dump(exclude={"submission_id", "result"}))
