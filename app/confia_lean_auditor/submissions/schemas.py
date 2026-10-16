from __future__ import annotations

from typing import Annotated, Literal, Optional, Union
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from confia_lean_auditor.capture.schemas import (
    CaptureDocument, Identifier, MAX_IMPORT_BYTES, MAX_PAGES, SCHEMA_VERSION,
)

MAX_PNG_BYTES = 8 * 1024 * 1024
MAX_REQUEST_BYTES = 64 * 1024 * 1024
MAX_PNG_BASE64 = ((MAX_PNG_BYTES + 2) // 3) * 4
SubmissionId = Annotated[str, StringConstraints(pattern=r"^sub_[0-9a-f]{32}$")]
TranscriptionId = Annotated[str, StringConstraints(pattern=r"^tr_[0-9a-f]{32}$")]
AcceptanceId = Annotated[str, StringConstraints(pattern=r"^acc_[0-9a-f]{32}$")]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
ReviewerReference = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
TranscriptionSource = Literal["manual", "automatic", "mathpix_strokes", "mathpix_image", "vision_model"]
TranscriptionStatus = Literal["DRAFT", "NEEDS_REVIEW", "ACCEPTED"]
EditableTranscriptionStatus = Literal["DRAFT", "NEEDS_REVIEW"]
SegmentKind = Literal["text", "math", "mixed", "diagram", "unknown"]


class SubmissionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class CaptureSnapshot(CaptureDocument):
    """Submission requires a frozen version; the capture v1 contract is unchanged."""
    document_kind: Literal["local_snapshot"]
    local_snapshot_id: Identifier


class SubmittedPage(SubmissionModel):
    page_id: Identifier
    png_base64: str = Field(min_length=1, max_length=MAX_PNG_BASE64)


class SubmissionRequest(SubmissionModel):
    # Preserve this UTF-8 string verbatim, rather than dumping a parsed model.
    snapshot_json: str = Field(min_length=1, max_length=MAX_IMPORT_BYTES)
    pages: list[SubmittedPage] = Field(min_length=1, max_length=MAX_PAGES)
    student_reference: Optional[str] = Field(default=None, min_length=1, max_length=80)


class ArtifactReference(SubmissionModel):
    filename: Annotated[str, StringConstraints(pattern=r"^(snapshot\.json|page_[123]\.png)$")]
    media_type: Literal["application/json", "image/png"]
    sha256: Sha256
    size_bytes: int = Field(gt=0)
    page_id: Optional[Identifier] = None
    page_index: Optional[int] = Field(default=None, ge=0, lt=MAX_PAGES)


class SubmissionRecord(SubmissionModel):
    submission_id: SubmissionId
    problem_id: Identifier
    snapshot_id: Identifier
    source: Literal["tablet"] = "tablet"
    capture_schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    received_at: datetime
    status: Literal["RECEIVED"] = "RECEIVED"
    snapshot: ArtifactReference
    page_images: list[ArtifactReference] = Field(min_length=1, max_length=MAX_PAGES)
    student_reference: Optional[str] = None
    student_reference_verified: Literal[False] = False
    # Absent on records created before CORE-AUTH-01; no owner is inferred.
    submitted_by_user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    network_id: Optional[str] = None
    school_id: Optional[str] = None
    classroom_id: Optional[str] = None
    # Optional for submissions received before institutional Assessment existed.
    assessment_id: Optional[str] = Field(default=None, pattern=r"^asmt_[0-9a-f]{32}$")
    assessment_item_id: Optional[str] = Field(default=None, pattern=r"^ait_[0-9a-f]{32}$")
    assessment_definition_sha256: Optional[Sha256] = None

    @model_validator(mode="after")
    def assessment_binding_is_complete(self):
        values = (self.assessment_id, self.assessment_item_id, self.assessment_definition_sha256)
        if any(value is not None for value in values) and not all(value is not None for value in values):
            raise ValueError("assessment binding must be complete")
        return self


class SubmissionReceipt(SubmissionRecord):
    receipt_version: Literal["1.0"] = "1.0"


class ArtifactIntegrity(SubmissionModel):
    filename: str
    expected_sha256: Sha256
    actual_sha256: Optional[Sha256]
    matches: bool


class SubmissionDetail(SubmissionModel):
    submission: SubmissionRecord
    receipt: SubmissionReceipt
    integrity: list[ArtifactIntegrity]


class TranscriptionSourceRegion(SubmissionModel):
    """Optional measured bounding box; omitted when the manual review has no mapping."""

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    coordinate_system: Literal["top_left_css_pixels"] = "top_left_css_pixels"


class TranscriptionSegment(SubmissionModel):
    segment_id: Identifier
    page_index: int = Field(ge=0, lt=MAX_PAGES)
    order: int = Field(ge=0)
    kind: SegmentKind
    text: Optional[str] = Field(default=None, min_length=1, max_length=20_000)
    latex: Optional[str] = Field(default=None, min_length=1, max_length=20_000)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    source_region: Optional[TranscriptionSourceRegion] = None
    source_stroke_refs: Optional[list[Identifier]] = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def validate_stroke_references(self) -> "TranscriptionSegment":
        if self.source_stroke_refs is not None and len(self.source_stroke_refs) != len(set(self.source_stroke_refs)):
            raise ValueError("source stroke references must be unique")
        return self


class RecognitionProvenance(SubmissionModel):
    submission_id: SubmissionId
    # Optional for pre-Mathpix runs already persisted by CAP-03B.
    snapshot_id: Optional[Identifier] = None
    artifacts: list[ArtifactReference] = Field(min_length=1, max_length=MAX_PAGES + 1)
    adapter: Identifier
    adapter_version: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    provider: Identifier
    input_mode: Literal["strokes", "image", "strokes_and_image"]
    # Only adapter-declared, non-secret parameters. Credentials never enter this model.
    parameters: dict[str, Union[str, int, float, bool, None]] = Field(default_factory=dict)
    created_at: datetime
    input_hash: Sha256


class TranscriptionRecord(SubmissionModel):
    transcription_id: TranscriptionId
    submission_id: SubmissionId
    created_at: datetime
    source: TranscriptionSource
    recognizer: Optional[str] = Field(default=None, min_length=1, max_length=120)
    recognizer_version: Optional[str] = Field(default=None, min_length=1, max_length=80)
    provider: Optional[Identifier] = None
    recognizer_run_id: Optional[Annotated[str, StringConstraints(pattern=r"^run_[0-9a-f]{32}$")]] = None
    provenance: Optional[RecognitionProvenance] = None

    @model_validator(mode="after")
    def automatic_provenance_required(self):
        if self.source == "automatic":
            p = self.provenance
            if (p is None or self.recognizer_run_id is None or self.provider != p.provider
                    or self.submission_id != p.submission_id or self.recognizer != p.adapter
                    or self.recognizer_version != p.adapter_version):
                raise ValueError("automatic transcription requires consistent recognition provenance")
        return self


class TranscriptionRevision(TranscriptionRecord):
    """ACCEPTED means faithful transcription only, never mathematical validity."""

    revision_number: int = Field(ge=1)
    based_on_revision_number: Optional[int] = Field(default=None, ge=1)
    reviewer_reference: ReviewerReference
    reviewer_identity_verified: Literal[False] = False
    change_type: Literal["initial_transcription", "reading_correction", "other_transcription_edit"]
    change_reason: Optional[str] = Field(default=None, min_length=1, max_length=500)
    segments: list[TranscriptionSegment] = Field(min_length=1, max_length=2_000)
    status: TranscriptionStatus

    @model_validator(mode="after")
    def validate_revision(self) -> "TranscriptionRevision":
        segment_ids = [segment.segment_id for segment in self.segments]
        if len(segment_ids) != len(set(segment_ids)):
            raise ValueError("segment IDs must be unique within a revision")
        positions = [(segment.page_index, segment.order) for segment in self.segments]
        if len(positions) != len(set(positions)):
            raise ValueError("segment order must be unique within each page")
        if self.revision_number == 1:
            if self.based_on_revision_number is not None or self.change_type != "initial_transcription":
                raise ValueError("the first revision must be an initial transcription")
        elif self.based_on_revision_number != self.revision_number - 1:
            raise ValueError("a revision must be based on its immediate predecessor")
        return self


class CreateTranscriptionRequest(SubmissionModel):
    source: Literal["manual"] = "manual"
    recognizer: None = None
    recognizer_version: None = None
    reviewer_reference: ReviewerReference
    reviewer_identity_verified: Literal[False] = False
    segments: list[TranscriptionSegment] = Field(min_length=1, max_length=2_000)
    status: EditableTranscriptionStatus = "NEEDS_REVIEW"


class CreateTranscriptionRevisionRequest(SubmissionModel):
    based_on_revision_number: int = Field(ge=1)
    reviewer_reference: ReviewerReference
    reviewer_identity_verified: Literal[False] = False
    change_type: Literal["reading_correction", "other_transcription_edit"] = "reading_correction"
    change_reason: Optional[str] = Field(default=None, min_length=1, max_length=500)
    segments: list[TranscriptionSegment] = Field(min_length=1, max_length=2_000)
    status: EditableTranscriptionStatus = "NEEDS_REVIEW"


class AcceptTranscriptionRequest(SubmissionModel):
    revision_number: int = Field(ge=1)
    reviewer_reference: ReviewerReference
    reviewer_identity_verified: Literal[False] = False
    acceptance_note: Optional[str] = Field(default=None, min_length=1, max_length=500)


class TranscriptionAcceptance(SubmissionModel):
    """Records representation fidelity; it deliberately has no mathematical result."""

    acceptance_id: AcceptanceId
    transcription_id: TranscriptionId
    submission_id: SubmissionId
    revision_number: int = Field(ge=1)
    accepted_at: datetime
    reviewer_reference: ReviewerReference
    reviewer_identity_verified: Literal[False] = False
    acceptance_note: Optional[str] = None
    meaning: Literal["faithful_representation_of_manuscript_only"] = "faithful_representation_of_manuscript_only"
    mathematical_validity_assessed: Literal[False] = False
    # Legacy events remain readable, but cannot authorize a new AuditSource.
    accepted_revision_sha256: Optional[Sha256] = None


class TranscriptionAcceptanceReceipt(SubmissionModel):
    acceptance_id: AcceptanceId
    acceptance_sha256: Sha256
    accepted_revision_sha256: Sha256
    created_at: datetime


class TranscriptionSummary(SubmissionModel):
    transcription: TranscriptionRecord
    latest_revision: TranscriptionRevision


class TranscriptionHistory(SubmissionModel):
    transcription: TranscriptionRecord
    revisions: list[TranscriptionRevision]
    acceptances: list[TranscriptionAcceptance]


class AcceptedTranscription(SubmissionModel):
    revision: TranscriptionRevision
    acceptance: TranscriptionAcceptance
