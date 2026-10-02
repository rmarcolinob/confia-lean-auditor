from __future__ import annotations

from typing import Annotated, Literal, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from confia_lean_auditor.capture.schemas import (
    CaptureDocument, Identifier, MAX_IMPORT_BYTES, MAX_PAGES, SCHEMA_VERSION,
)

MAX_PNG_BYTES = 8 * 1024 * 1024
MAX_REQUEST_BYTES = 64 * 1024 * 1024
MAX_PNG_BASE64 = ((MAX_PNG_BYTES + 2) // 3) * 4
SubmissionId = Annotated[str, StringConstraints(pattern=r"^sub_[0-9a-f]{32}$")]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class SubmissionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


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
