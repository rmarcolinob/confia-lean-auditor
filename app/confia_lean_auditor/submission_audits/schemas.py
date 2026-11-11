from datetime import datetime
from typing import Annotated, Literal, Optional, Union

from pydantic import Field, model_validator, model_serializer
from confia_lean_auditor.submissions.integrity import model_sha256, canonical_sha256

from confia_lean_auditor.core.schemas import AuditResponse
from confia_lean_auditor.submissions.schemas import (
    AcceptanceId, ArtifactReference, Sha256, SubmissionId, SubmissionModel,
    TranscriptionAcceptance, TranscriptionAcceptanceReceipt, TranscriptionId, TranscriptionRevision,
)

from confia_lean_auditor.tme.audit_models import TMEAuditContext, TMEAuditResult

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

    tme_context: Optional[TMEAuditContext] = None

    @model_serializer(mode="wrap")
    def preserve_legacy_shape(self, handler):
        data = handler(self)
        if "tme_context" not in self.model_fields_set:
            data.pop("tme_context", None)
        return data

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
    artifact_type: Literal["export", "certificate", "formal_step", "student_proof", "refutation", "reproducibility"]
    relation_id: str
    file: str
    sha256: Sha256
    byte_size: int = Field(ge=0)


class QuestionAuditContext(SubmissionModel):
    assessment_id: str
    participant_id: str
    exam_submission_id: str
    question_attempt_id: str
    engine_mode: Literal["TME_CURRENT"] = "TME_CURRENT"
    adapter_version: Literal["question-audit.v1"] = "question-audit.v1"
    max_score: float = Field(gt=0)


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
    result: Optional[Union[TMEAuditResult, AuditResponse]] = None
    result_sha256: Optional[Sha256] = None
    required_artifacts: list[RequiredArtifact] = Field(default_factory=list)
    artifact_manifest_sha256: Optional[Sha256] = None
    artifact_dir: Optional[str] = None
    auditor_version: Optional[str] = None
    question_context: Optional[QuestionAuditContext] = None
    completed_at: Optional[datetime] = None
    question_events: Optional[list[dict]] = None
    question_events_sha256: Optional[Sha256] = None

    @model_serializer(mode="wrap")
    def preserve_pre_question_shape(self, handler):
        data = handler(self)
        for field in ("question_context", "completed_at", "question_events", "question_events_sha256"):
            if field not in self.model_fields_set:
                data.pop(field, None)
        return data

    execution_key: Optional[str] = None
    error_code: Optional[Literal["AUDITOR_FAILED", "METADATA_INTEGRITY_FAILED"]] = None
    reproducibility_status: Literal["recorded", "unavailable", "legacy_unversioned"] = "legacy_unversioned"
    reproducibility_manifest_filename: Optional[Literal["reproducibility_manifest.json"]] = None
    reproducibility_manifest_sha256: Optional[Sha256] = None

    @model_validator(mode="after")
    def coherent(self):
        if self.question_events is not None:
            if (not self.question_context or self.question_events_sha256 != canonical_sha256(self.question_events)
                    or any(event.get("audit_run_id") != self.audit_run_id
                        or event.get("question_attempt_id") != self.question_context.question_attempt_id
                        or event.get("transcription_version_id") != f"{self.transcription_id}:{self.revision_number}"
                        for event in self.question_events)):
                raise ValueError("invalid question events")
        elif self.question_events_sha256 is not None:
            raise ValueError("event digest without events")
        if self.completed_at and self.completed_at < self.created_at:
            raise ValueError("completion precedes start")
        if self.question_context and (not self.completed_at or not self.source.tme_context):
            raise ValueError("question audit requires completion and engine context")
        metadata = self.result.reproducibility if self.result else None
        record = metadata.record if metadata else None
        expected_statuses = {metadata.status} if metadata else (
            {"legacy_unversioned", "unavailable"} if self.status == "FAILED" else {"legacy_unversioned"})
        if (self.reproducibility_status not in expected_statuses
                or self.reproducibility_manifest_filename != (record.filename if record else None)
                or self.reproducibility_manifest_sha256 != (record.manifest_sha256 if record else None)):
            raise ValueError("inconsistent reproducibility binding")
        if record and record.manifest.problem_id != self.problem_id:
            raise ValueError("inconsistent reproducibility problem")
        for field in ("submission_id", "problem_id", "transcription_id", "revision_number",
                      "acceptance_id", "source_hash"):
            if getattr(self, field) != getattr(self.source, field):
                raise ValueError("inconsistent audit source binding")
        if isinstance(self.result, TMEAuditResult):
            if (self.source.tme_context != self.result.context
                    or self.auditor_version != self.result.context.auditor_version
                    or self.result.accepted_transcription_revision_id != f"{self.transcription_id}:{self.revision_number}"
                    or self.result.accepted_revision_sha256 != self.source.provenance.acceptance.accepted_revision_sha256):
                raise ValueError("inconsistent accepted TME result")
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
              or self.artifact_dir is not None or self.error_code not in {"AUDITOR_FAILED", "METADATA_INTEGRITY_FAILED"}):
            raise ValueError("failed audit cannot publish a result")
        return self


class AuditRunView(AuditRun):
    # Derived at read time; never rewrites the persisted run.
    stale: bool
