"""Shared invariants for publication and persisted recognition provenance."""
import hashlib
import json

from confia_lean_auditor.recognition.schemas import ProviderOutput, RecognitionRun
from confia_lean_auditor.submissions.schemas import TranscriptionRecord, TranscriptionRevision, TranscriptionSegment


def canonical_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def input_references(submission, input_mode):
    refs = []
    if input_mode in {"strokes", "strokes_and_image"}:
        refs.append(submission.snapshot)
    if input_mode in {"image", "strokes_and_image"}:
        refs.extend(sorted(submission.page_images, key=lambda a: a.page_index))
    return refs


def validate_run_source(run, submission):
    run = RecognitionRun.model_validate(run.model_dump())
    p = run.provenance
    if run.submission_id != submission.submission_id or p.artifacts != input_references(submission, p.input_mode):
        raise ValueError("recognition source references mismatch")
    manifest = {"input_mode": p.input_mode, "artifacts": [a.model_dump(mode="json") for a in p.artifacts]}
    if canonical_hash(manifest) != p.input_hash:
        raise ValueError("recognition input manifest hash mismatch")
    if run.result is not None:
        output = ProviderOutput.model_validate(run.result.model_dump(include=set(ProviderOutput.model_fields)))
        if canonical_hash(output.model_dump(mode="json")) != run.result.output_hash:
            raise ValueError("recognition output hash mismatch")
    return run


def validate_automatic_pair(transcription, revision, run, submission):
    if run is None:
        raise ValueError("automatic initial revision requires a recognition run")
    transcription = TranscriptionRecord.model_validate(transcription.model_dump())
    revision = TranscriptionRevision.model_validate(revision.model_dump())
    run = validate_run_source(run, submission)
    if (transcription.source != "automatic" or revision.source != "automatic"
            or run.status != "NEEDS_REVIEW" or revision.status != "NEEDS_REVIEW"):
        raise ValueError("automatic initial revision must need human review")
    record_from_revision = TranscriptionRecord.model_validate(
        revision.model_dump(include=set(TranscriptionRecord.model_fields)))
    if record_from_revision != transcription:
        raise ValueError("initial revision transcription mismatch")
    if (run.submission_id != revision.submission_id
            or run.transcription_id != revision.transcription_id
            or run.revision_number != revision.revision_number or revision.revision_number != 1
            or run.recognizer_run_id != revision.recognizer_run_id
            or run.transcription_id != f"tr_{run.recognizer_run_id[4:]}"
            or run.provenance != revision.provenance
            or run.provenance.created_at != revision.created_at
            or run.provenance.provider != revision.provider
            or run.provenance.adapter != revision.recognizer
            or run.provenance.adapter_version != revision.recognizer_version):
        raise ValueError("recognition run initial revision mismatch")
    expected = [TranscriptionSegment(segment_id=f"recognition:{i}", **s.model_dump())
                for i, s in enumerate(run.result.segments)]
    if revision.segments != expected:
        raise ValueError("recognition output revision mismatch")
    return run
