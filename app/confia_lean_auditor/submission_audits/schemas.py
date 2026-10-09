from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import Field, model_validator
from confia_lean_auditor.submissions.integrity import model_sha256, canonical_sha256

from confia_lean_auditor.core.schemas import AuditResponse
from confia_lean_auditor.submissions.schemas import (
    AcceptanceId, ArtifactReference, Sha256, SubmissionId, SubmissionModel,
    TranscriptionAcceptance, TranscriptionAcceptanceReceipt, TranscriptionId, TranscriptionRevision,
)

AuditRunId = Annotated[str, Field(pattern=r"^aud_[0-9a-f]{64}$")]


class AuditRequest(SubmissionModel):
    transcription_id: TranscriptionId
    revision_number: int = Field(ge=1)
    acceptance_id: AcceptanceId
    # Omit for retry/double-click deduplication; a new key explicitly reruns.
    execution_key: Optional[str] = Field(default=None, min_length=1, max_length=100,
                                         pattern=r"^[a-zA-Z0-9:_-]+$")


class ConversionWarning(SubmissionModel):
    segment_id: str
    page_index: int
    code: Literal["DIAGRAM_NOT_ANALYZED", "UNKNOWN_SEGMENT", "EMPTY_SEGMENT"]
    message: str


class AuditProvenance(SubmissionModel):
    conversion_version: Literal["segments-v1"] = "segments-v1"
    original_artifacts: list[ArtifactReference]
    revision: TranscriptionRevision
    acceptance: TranscriptionAcceptance
    acceptance_receipt: TranscriptionAcceptanceReceipt


class AuditSource(SubmissionModel):
    submission_id: SubmissionId
    problem_id: str
    transcription_id: TranscriptionId
    revision_number: int = Field(ge=1)
    acceptance_id: AcceptanceId
    accepted_at: datetime
    source_hash: Sha256
    solution_text: str
    provenance: AuditProvenance
    warnings: list[ConversionWarning] = Field(default_factory=list)

    @model_validator(mode="after")
    def accepted_binding(self):
        revision, acceptance = self.provenance.revision, self.provenance.acceptance
        receipt = self.provenance.acceptance_receipt
        for field in ("submission_id", "transcription_id", "revision_number"):
            if getattr(self, field) != getattr(revision, field) or getattr(self, field) != getattr(acceptance, field):
                raise ValueError("source must reference exactly the accepted revision")
        if (revision.status not in {"DRAFT", "NEEDS_REVIEW"}
                or model_sha256(revision) != acceptance.accepted_revision_sha256
                or self.acceptance_id != acceptance.acceptance_id
                or self.accepted_at != acceptance.accepted_at):
            raise ValueError("source requires a valid acceptance")
        if (receipt.acceptance_id != acceptance.acceptance_id
                or receipt.acceptance_sha256 != model_sha256(acceptance)
                or receipt.accepted_revision_sha256 != acceptance.accepted_revision_sha256
                or receipt.created_at != acceptance.accepted_at):
            raise ValueError("source requires an intact acceptance receipt")
        return self


class RequiredArtifact(SubmissionModel):
    artifact_type: Literal["export", "certificate", "formal_step", "student_proof", "refutation"]
    relation_id: str
    file: str
    sha256: Sha256
    byte_size: int = Field(ge=0)


class AuditRun(SubmissionModel):
    audit_run_id: AuditRunId
    submission_id: SubmissionId
    problem_id: str
    transcription_id: TranscriptionId
    revision_number: int
    acceptance_id: AcceptanceId
    source_hash: Sha256
    source: AuditSource
    created_at: datetime
    status: Literal["COMPLETED", "FAILED"]
    result: Optional[AuditResponse] = None
    result_sha256: Optional[Sha256] = None
    required_artifacts: list[RequiredArtifact] = Field(default_factory=list)
    artifact_manifest_sha256: Optional[Sha256] = None
    artifact_dir: Optional[str] = None
    auditor_version: Optional[str] = None
    execution_key: Optional[str] = None
    error_code: Optional[Literal["AUDITOR_FAILED"]] = None

    @model_validator(mode="after")
    def coherent(self):
        for field in ("submission_id", "problem_id", "transcription_id", "revision_number",
                      "acceptance_id", "source_hash"):
            if getattr(self, field) != getattr(self.source, field):
                raise ValueError("inconsistent audit source binding")
        if self.status == "COMPLETED":
            if self.result is None or self.error_code is not None or not self.artifact_dir:
                raise ValueError("completed audit requires a result")
            if self.result_sha256 != model_sha256(self.result):
                raise ValueError("invalid audit result digest")
            if (not self.required_artifacts or self.artifact_manifest_sha256 != canonical_sha256(
                    [item.model_dump(mode="json") for item in self.required_artifacts])):
                raise ValueError("invalid required artifact manifest")
            if self.result.problem_id != self.problem_id or self.artifact_dir != self.result.artifact_dir:
                raise ValueError("inconsistent audit result binding")
        elif (self.result is not None or self.result_sha256 is not None or self.required_artifacts
              or self.artifact_manifest_sha256 is not None
              or self.artifact_dir is not None or self.error_code != "AUDITOR_FAILED"):
            raise ValueError("failed audit cannot publish a result")
        return self


class AuditRunView(AuditRun):
    # Derived at read time; never rewrites the persisted run.
    stale: bool
