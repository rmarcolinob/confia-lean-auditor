from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import os
from pathlib import Path
import re

from confia_lean_auditor.core.schemas import AuditRequest as EngineRequest, AuditResponse
from confia_lean_auditor.submissions.store import SubmissionStore, TranscriptionIntegrityConflict
from confia_lean_auditor.submissions.integrity import model_sha256, canonical_sha256
from .artifacts import capture_manifest, validate_manifest
from .schemas import AuditRun, AuditRunView
from .source import build_source, canonical_hash, convert_segments, source_digest


class UnacceptedSource(ValueError):
    pass


class AuditService:
    def __init__(self, submissions: SubmissionStore, root: Path, engine):
        self.submissions, self.root, self.engine = submissions, root, engine

    def _source(self, submission_id, request):
        # Caller holds the submissions lock, including provenance validation.
        submission = self.submissions.assert_submission_integrity(submission_id)
        folder = self.submissions._transcription_folder(request.transcription_id)
        for directory, pattern in ((folder / "revisions", r"revision_[0-9]{6}\.json"),
                                   (folder / "acceptances", r"acceptance_[0-9]{6}\.json")):
            if directory.is_symlink():
                raise UnacceptedSource()
            if directory.exists():
                for path in directory.iterdir():
                    if path.is_symlink() or not path.is_file() or not re.fullmatch(pattern, path.name):
                        raise UnacceptedSource()
        if (folder / "transcription.json").is_symlink():
            raise UnacceptedSource()
        history = self.submissions._history_from_folder(folder)
        if history.transcription.submission_id != submission_id:
            raise UnacceptedSource()
        revision = next((item for item in history.revisions if item.revision_number == request.revision_number), None)
        acceptance = next((item for item in history.acceptances if item.acceptance_id == request.acceptance_id), None)
        if acceptance is not None and acceptance.accepted_revision_sha256 is None:
            raise TranscriptionIntegrityConflict()
        if (revision is None or acceptance is None or revision.status != "ACCEPTED"
                or acceptance.revision_number != revision.revision_number
                or acceptance.transcription_id != revision.transcription_id
                or acceptance.submission_id != submission_id
                or acceptance.accepted_at.tzinfo is None or revision.created_at.tzinfo is None
                or acceptance.accepted_at < revision.created_at
                or sum(item.revision_number == revision.revision_number for item in history.acceptances) != 1):
            raise UnacceptedSource()
        if any(getattr(revision, field) != getattr(history.transcription, field)
               for field in ("source", "recognizer", "recognizer_version", "provider", "recognizer_run_id", "provenance")):
            raise UnacceptedSource()
        self.submissions._validate_segment_pages(revision.segments, submission)
        # Hash and embed the exact persisted revision, not its projected status.
        persisted = next(item for item in self.submissions._read_revisions(folder)
                         if item.revision_number == revision.revision_number)
        receipt = self.submissions.assert_acceptance_integrity(folder, persisted, acceptance)
        return build_source(submission, persisted, acceptance, receipt)

    @staticmethod
    def _validate_artifacts(result, manifest):
        validate_manifest(result, manifest)

    def _path(self, run_id):
        if not re.fullmatch(r"aud_[0-9a-f]{64}", run_id):
            raise FileNotFoundError()
        return self.root / f"{run_id}.json"

    def _read(self, run_id):
        path = self._path(run_id)
        if self.root.is_symlink() or path.is_symlink():
            raise ValueError("invalid audit storage")
        run = AuditRun.model_validate_json(path.read_bytes())
        if run.audit_run_id != run_id or source_digest(run.source) != run.source_hash:
            raise ValueError("invalid persisted audit hash")
        if run_id != self._identity(run.source, run.execution_key):
            raise ValueError("invalid persisted audit identity")
        solution, warnings = convert_segments(run.source.provenance.revision.segments)
        if solution != run.source.solution_text or warnings != run.source.warnings:
            raise ValueError("persisted audit conversion mismatch")
        if run.status == "COMPLETED":
            self._validate_artifacts(run.result, run.required_artifacts)
        return run

    @staticmethod
    def _identity(source, execution_key):
        return "aud_" + canonical_hash({"submission_id": source.submission_id,
            "transcription_id": source.transcription_id, "revision_number": source.revision_number,
            "acceptance_id": source.acceptance_id, "source_hash": source.source_hash,
            "execution_key": execution_key})

    @contextmanager
    def _request_lock(self, run_id):
        if self.root.is_symlink():
            raise ValueError("invalid audit directory")
        locks = self.root / ".locks"
        if locks.is_symlink():
            raise ValueError("invalid audit locks")
        locks.mkdir(parents=True, exist_ok=True)
        # Keep lock inodes in place across processes and restarts.
        fd = os.open(locks / f"{run_id}.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def execute(self, submission_id, request):
        with self.submissions._locked():
            source = self._source(submission_id, request)
        run_id = self._identity(source, request.execution_key)
        with self._request_lock(run_id):
            # Recheck after waiting. Never replay a now-invalid source.
            with self.submissions._locked():
                if self._source(submission_id, request) != source:
                    raise UnacceptedSource()
            if self._path(run_id).exists() or self._path(run_id).is_symlink():
                return self.view(self._read(run_id))
            created_at = datetime.now(timezone.utc)
            try:
                result = AuditResponse.model_validate(self.engine(EngineRequest(
                    problem_id=source.problem_id, solution=source.solution_text)))
                if result.problem_id != source.problem_id:
                    raise ValueError("engine returned another problem")
                manifest = capture_manifest(result)
                self._validate_artifacts(result, manifest)
                manifest_hash = canonical_sha256([item.model_dump(mode="json") for item in manifest])
                result_hash = model_sha256(result)
                status, error_code = "COMPLETED", None
            except Exception:
                # Pipeline diagnostics can contain student content. Persist
                # only the failure category, never a fictitious result.
                result, result_hash, status, error_code = None, None, "FAILED", "AUDITOR_FAILED"
                manifest, manifest_hash = [], None
            run = AuditRun(audit_run_id=run_id, source=source, created_at=created_at,
                **{field: getattr(source, field) for field in ("submission_id", "problem_id",
                    "transcription_id", "revision_number", "acceptance_id", "source_hash")},
                status=status, result=result, artifact_dir=result.artifact_dir if result else None,
                result_sha256=result_hash,
                required_artifacts=manifest, artifact_manifest_sha256=manifest_hash,
                execution_key=request.execution_key, error_code=error_code, auditor_version=None)
            # A newer revision leaves this accepted source valid. Changed
            # originals/acceptance block publication even after engine execution.
            with self.submissions._locked():
                if self._source(submission_id, request) != source:
                    raise UnacceptedSource()
                SubmissionStore._write_atomic_new(self._path(run_id), run.model_dump_json(indent=2).encode())
            return self.view(run)

    def view(self, run):
        with self.submissions._locked():
            history = self.submissions._transcription_history(run.transcription_id)
            stale = history.revisions[-1].revision_number != run.revision_number
            folder = self.submissions._transcriptions_folder(run.submission_id)
            for other in folder.iterdir():
                if other.is_dir() and not other.is_symlink() and re.fullmatch(r"tr_[0-9a-f]{32}", other.name):
                    record = self.submissions._read_transcription_record(other)
                    stale = stale or record.created_at > history.transcription.created_at
        return AuditRunView(**run.model_dump(), stale=stale)

    def get(self, run_id):
        return self.view(self._read(run_id))

    def list(self, submission_id):
        with self.submissions._locked():
            self.submissions._read(submission_id)
        if self.root.is_symlink():
            raise ValueError("invalid audit directory")
        if not self.root.exists():
            return []
        runs = [self._read(path.stem) for path in self.root.glob("aud_*.json")]
        return [self.view(run) for run in sorted(runs, key=lambda item: item.created_at, reverse=True)
                if run.submission_id == submission_id]
