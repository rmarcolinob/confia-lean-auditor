"""Transient recognition of a frozen local snapshot; no institutional publication."""
from concurrent.futures import TimeoutError as FutureTimeout
from hashlib import sha256

from pydantic import Field, ValidationError

from confia_lean_auditor.capture.schemas import Identifier, MAX_IMPORT_BYTES
from confia_lean_auditor.core.problem_catalog import CATALOG
from confia_lean_auditor.recognition.execution import ProviderDeadline, configured_timeout_seconds, start_provider
from confia_lean_auditor.recognition.registry import RecognitionArtifact, RecognitionInput
from confia_lean_auditor.recognition.schemas import ProviderOutput
from confia_lean_auditor.recognition.service import RecognitionService
from confia_lean_auditor.submissions.schemas import CaptureSnapshot, Sha256, SubmissionModel


class PreviewRequest(SubmissionModel):
    snapshot_json: str = Field(min_length=1, max_length=MAX_IMPORT_BYTES)
    client_preview_id: Identifier


class PreviewResponse(SubmissionModel):
    client_preview_id: Identifier
    problem_id: str
    snapshot_id: str
    snapshot_sha256: Sha256
    page_count: int
    active_stroke_count: int
    result: ProviderOutput


class PreviewError(ValueError):
    pass


def recognize_preview(request: PreviewRequest, registry):
    raw = request.snapshot_json.encode("utf-8")
    if len(raw) > MAX_IMPORT_BYTES:
        raise PreviewError("INVALID_SNAPSHOT")
    snapshot = CaptureSnapshot.model_validate_json(raw)
    if snapshot.problem_id not in CATALOG or not snapshot.active_stroke_ids:
        raise PreviewError("INVALID_SNAPSHOT")
    adapter = registry.create("mathpix")
    if adapter.input_mode != "strokes":
        raise PreviewError("INVALID_PROVIDER")
    digest = sha256(raw).hexdigest()
    deadline = ProviderDeadline.start(configured_timeout_seconds())
    source = RecognitionInput(
        f"preview:{snapshot.local_snapshot_id}",
        (RecognitionArtifact("snapshot.json", None, digest, raw),), deadline,
    )

    def call_provider():
        supplied = adapter.recognize(source)
        try:
            output = ProviderOutput.model_validate(
                supplied.model_dump() if isinstance(supplied, ProviderOutput) else supplied)
            RecognitionService._validate_mapping(output, snapshot)
        except (ValidationError, ValueError, TypeError):
            return None, "INVALID_PROVIDER_OUTPUT"
        return output, None

    future = start_provider(call_provider, deadline)
    try:
        output, error = future.result(timeout=deadline.remaining_seconds())
    except FutureTimeout:
        output, error = None, "PROVIDER_TIMEOUT"
    if error:
        raise PreviewError(error)
    return PreviewResponse(
        client_preview_id=request.client_preview_id,
        problem_id=snapshot.problem_id, snapshot_id=snapshot.local_snapshot_id,
        snapshot_sha256=digest, page_count=len(snapshot.pages),
        active_stroke_count=len(snapshot.active_stroke_ids), result=output,
    )
