"""Integrity-gated recognition and publication into the existing transcription store."""
from datetime import datetime, timezone
from concurrent.futures import TimeoutError as FutureTimeout
import hashlib
import re
from time import perf_counter
from uuid import uuid4

from pydantic import ValidationError

from confia_lean_auditor.recognition.registry import RecognitionArtifact, RecognitionInput, RecognizerRegistry
from confia_lean_auditor.recognition.execution import (
    ProviderDeadline, configured_timeout_seconds, recognition_request_lock, start_provider,
)
from confia_lean_auditor.recognition.validation import canonical_hash, input_references, validate_run_source
from confia_lean_auditor.recognition.schemas import ProviderOutput, RecognitionRequest, RecognitionResult, RecognitionRun
from confia_lean_auditor.submissions.schemas import (
    CaptureSnapshot, RecognitionProvenance, TranscriptionRecord, TranscriptionRevision, TranscriptionSegment,
)
from confia_lean_auditor.submissions.store import SubmissionIntegrityConflict, SubmissionStore, sha256


class RecognitionConflict(ValueError):
    pass



class RecognitionService:
    def __init__(self, store: SubmissionStore, registry: RecognizerRegistry, timeout_seconds=None):
        self.store, self.registry = store, registry
        self.timeout_seconds = configured_timeout_seconds(timeout_seconds)

    def _run_paths(self, submission_id, run_id):
        folder = self.store._folder(submission_id)
        return (folder / "transcriptions" / f"tr_{run_id[4:]}" / "recognition.json",
                folder / "recognitions" / f"{run_id}.json")

    def _read_run(self, submission_id, run_id):
        if not re.fullmatch(r"run_[0-9a-f]{32}", run_id):
            raise FileNotFoundError()
        success, failure = self._run_paths(submission_id, run_id)
        for path in (success, failure):
            if any(parent.is_symlink() for parent in (path, path.parent, path.parent.parent)):
                raise ValueError("invalid recognition path")
        if success.parent.exists():
            if failure.exists():
                raise ValueError("recognition has duplicate final records")
            run = self.store._read_automatic_run(success.parent)
        elif failure.is_file():
            run = RecognitionRun.model_validate_json(failure.read_bytes())
            if run.status != "FAILED":
                raise ValueError("successful recognition has no transcription revision")
            submission, _ = self.store._read(submission_id)
            run = validate_run_source(run, submission)
        else:
            raise FileNotFoundError()
        if run.submission_id != submission_id or run.recognizer_run_id != run_id:
            raise ValueError("recognition identity mismatch")
        return run

    def get(self, submission_id, run_id):
        with self.store._locked():
            return self._read_run(submission_id, run_id)

    def list(self, submission_id):
        with self.store._locked():
            folder = self.store._folder(submission_id)
            paths = list((folder / "recognitions").glob("run_*.json"))
            paths += list((folder / "transcriptions").glob("tr_*/recognition.json"))
            ids = [path.stem if path.parent.name == "recognitions" else "run_" + path.parent.name[3:] for path in paths]
            return sorted((self._read_run(submission_id, i) for i in ids), key=lambda r: r.provenance.created_at, reverse=True)

    @staticmethod
    def _validate_mapping(output, snapshot):
        pages = {p.index: p for p in snapshot.pages}
        strokes = {s.stroke_id: s for s in snapshot.strokes if s.stroke_id in snapshot.active_stroke_ids}
        for segment in output.segments:
            if segment.page_index not in pages:
                raise ValueError("unknown segment page")
            page = pages[segment.page_index]
            if segment.source_region is not None:
                region = segment.source_region
                if region.x + region.width > page.logical_width or region.y + region.height > page.logical_height:
                    raise ValueError("source region outside page")
            if segment.source_stroke_refs is not None:
                if any(ref not in strokes or strokes[ref].page_id != page.page_id for ref in segment.source_stroke_refs):
                    raise ValueError("source stroke outside active page")

    def _existing_run(self, submission_id, run_id, adapter, parameters):
        try:
            run = self._read_run(submission_id, run_id)
        except FileNotFoundError:
            return None
        p = run.provenance
        if (p.provider != adapter.provider or p.adapter != adapter.adapter
                or p.adapter_version != adapter.adapter_version or p.input_mode != adapter.input_mode
                or p.parameters != parameters):
            raise RecognitionConflict("idempotency key reused for another configuration")
        return run

    def recognize(self, submission_id: str, request: RecognitionRequest):
        adapter = self.registry.create(request.provider)
        parameters = dict(adapter.public_parameters)
        if "confia_total_timeout_seconds" in parameters:
            raise ValueError("reserved recognition execution parameter")
        parameters["confia_total_timeout_seconds"] = self.timeout_seconds
        run_id = "run_" + (hashlib.sha256(f"{submission_id}:{request.idempotency_key}".encode()).hexdigest()[:32]
                           if request.idempotency_key else uuid4().hex)
        # A completed timeout/failure can be replayed even while an uncancellable
        # worker still holds its narrow request lease. Never wait on the global lock.
        with self.store._locked():
            self.store.assert_submission_integrity(submission_id)
            existing = self._existing_run(submission_id, run_id, adapter, parameters)
            if existing is not None:
                return existing, False
        def completed():
            with self.store._locked():
                self.store.assert_submission_integrity(submission_id)
                return self._existing_run(submission_id, run_id, adapter, parameters)

        with recognition_request_lock(self.store.root, run_id, completed) as lease:
            if lease.cached_run is not None:
                return lease.cached_run, False
            # Phase 1: short shared store lock; copied immutable input and provenance.
            with self.store._locked():
                submission = self.store.assert_submission_integrity(submission_id)
                existing = self._existing_run(submission_id, run_id, adapter, parameters)
                if existing is not None:
                    return existing, False
                folder = self.store._folder(submission_id)
                snapshot_raw = (folder / "snapshot.json").read_bytes()
                if sha256(snapshot_raw) != submission.snapshot.sha256:
                    raise SubmissionIntegrityConflict()
                snapshot = CaptureSnapshot.model_validate_json(snapshot_raw)
                refs = input_references(submission, adapter.input_mode)
                artifacts = tuple(RecognitionArtifact(r.filename, r.page_index, r.sha256,
                                  (folder / r.filename).read_bytes()) for r in refs)
                if any(sha256(a.data) != r.sha256 or len(a.data) != r.size_bytes for a, r in zip(artifacts, refs)):
                    raise SubmissionIntegrityConflict()
                now = datetime.now(timezone.utc)
                provenance = RecognitionProvenance(
                    submission_id=submission_id, snapshot_id=submission.snapshot_id,
                    artifacts=refs, adapter=adapter.adapter,
                    adapter_version=adapter.adapter_version, provider=adapter.provider,
                    input_mode=adapter.input_mode, parameters=parameters, created_at=now,
                    input_hash=canonical_hash({"input_mode": adapter.input_mode,
                                              "artifacts": [r.model_dump(mode="json") for r in refs]}),
                )
            # Phase 2: no global store lock. The adapter receives an explicit deadline.
            started = perf_counter()
            deadline = ProviderDeadline.start(self.timeout_seconds)
            source = RecognitionInput(submission_id, artifacts, deadline)

            def call_provider():
                supplied = adapter.recognize(source)
                try:
                    output = ProviderOutput.model_validate(supplied.model_dump() if isinstance(supplied, ProviderOutput) else supplied)
                    self._validate_mapping(output, snapshot)
                except (ValidationError, ValueError, TypeError):
                    return None, "INVALID_PROVIDER_OUTPUT"
                return output, None

            future = start_provider(call_provider, deadline)
            try:
                output, error = future.result(timeout=deadline.remaining_seconds())
            except FutureTimeout:
                output, error = None, "PROVIDER_TIMEOUT"
                lease.retain_until_done(future)
            latency_ms = (perf_counter() - started) * 1000
            # Phase 3: short exclusive lock; revalidate before one atomic publication.
            with self.store._locked(exclusive=True):
                if self.store.assert_submission_integrity(submission_id) != submission:
                    raise SubmissionIntegrityConflict()
                existing = self._existing_run(submission_id, run_id, adapter, parameters)
                if existing is not None:
                    if existing.provenance.input_hash != provenance.input_hash:
                        raise RecognitionConflict("idempotent recognition input mismatch")
                    return existing, False
                if error is not None:
                    run = RecognitionRun(recognizer_run_id=run_id, submission_id=submission_id,
                                         status="FAILED", provenance=provenance, error_code=error)
                    path = self._run_paths(submission_id, run_id)[1]
                    if path.parent.is_symlink():
                        raise ValueError("invalid recognition directory")
                    self.store._write_atomic_new(path, run.model_dump_json(indent=2).encode())
                    return run, True
                result = RecognitionResult(
                    **output.model_dump(), recognizer_run_id=run_id, submission_id=submission_id,
                    provider=provenance.provider, adapter_version=provenance.adapter_version,
                    input_mode=provenance.input_mode, created_at=now, latency_ms=latency_ms,
                    input_hash=provenance.input_hash, output_hash=canonical_hash(output.model_dump(mode="json")),
                )
                transcription = TranscriptionRecord(
                    transcription_id=f"tr_{run_id[4:]}", submission_id=submission_id, created_at=now,
                    source="automatic", recognizer=provenance.adapter, recognizer_version=provenance.adapter_version,
                    provider=provenance.provider, recognizer_run_id=run_id, provenance=provenance,
                )
                revision = TranscriptionRevision(
                    **transcription.model_dump(), revision_number=1,
                    reviewer_reference="automatic:pending-human-review", change_type="initial_transcription",
                    segments=[TranscriptionSegment(segment_id=f"recognition:{i}", **s.model_dump()) for i, s in enumerate(result.segments)],
                    status="NEEDS_REVIEW",
                )
                run = RecognitionRun(
                    recognizer_run_id=run_id, submission_id=submission_id, status="NEEDS_REVIEW",
                    provenance=provenance, result=result, transcription_id=transcription.transcription_id, revision_number=1,
                )
                self.store._publish_transcription(transcription, revision, recognition_run=run)
                return run, True
