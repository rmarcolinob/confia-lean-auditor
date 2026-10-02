import base64
import binascii
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import os
from pathlib import Path
import re
import shutil
import tempfile
from uuid import uuid4

from confia_lean_auditor.capture.schemas import MAX_IMPORT_BYTES
from confia_lean_auditor.core.problem_catalog import CATALOG
from confia_lean_auditor.submissions.png import validate_png
from confia_lean_auditor.submissions.schemas import (
    AcceptedTranscription, AcceptTranscriptionRequest, ArtifactIntegrity,
    ArtifactReference, CaptureSnapshot, CreateTranscriptionRequest,
    CreateTranscriptionRevisionRequest, MAX_PNG_BYTES, SubmissionDetail,
    SubmissionReceipt, SubmissionRecord, SubmissionRequest,
    TranscriptionAcceptance, TranscriptionHistory, TranscriptionRecord,
    TranscriptionRevision, TranscriptionSummary,
)


class SubmissionConflict(ValueError):
    pass


class SubmissionIntegrityConflict(SubmissionConflict):
    pass


class SubmissionTooLarge(ValueError):
    pass


class InvalidSubmissionProblem(ValueError):
    pass


class TranscriptionConflict(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_request(request: SubmissionRequest):
    raw = request.snapshot_json.encode("utf-8")
    if len(raw) > MAX_IMPORT_BYTES:
        raise SubmissionTooLarge()
    snapshot = CaptureSnapshot.model_validate_json(raw)
    if snapshot.problem_id not in CATALOG:
        raise InvalidSubmissionProblem()
    supplied = {page.page_id: page for page in request.pages}
    if len(supplied) != len(request.pages) or set(supplied) != {page.page_id for page in snapshot.pages}:
        raise ValueError("each capture page requires exactly one PNG")
    images = []
    for page in sorted(snapshot.pages, key=lambda item: item.index):
        try:
            data = base64.b64decode(supplied[page.page_id].png_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("invalid PNG encoding") from exc
        if len(data) > MAX_PNG_BYTES:
            raise SubmissionTooLarge()
        validate_png(data, int(page.logical_width), int(page.logical_height))
        images.append((page, data))
    return snapshot, raw, images


class SubmissionStore:
    def __init__(self, root: Path):
        self.root = root

    @contextmanager
    def _locked(self, exclusive=False):
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ".lock").open("a+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _folder(self, submission_id):
        if not re.fullmatch(r"sub_[0-9a-f]{32}", submission_id):
            raise FileNotFoundError()
        folder = self.root / submission_id
        if folder.is_symlink() or not folder.is_dir():
            raise FileNotFoundError()
        return folder

    def _read(self, submission_id):
        folder = self._folder(submission_id)
        record = SubmissionRecord.model_validate_json((folder / "submission.json").read_bytes())
        receipt = SubmissionReceipt.model_validate_json((folder / "receipt.json").read_bytes())
        if record.submission_id != submission_id or receipt.model_dump(exclude={"receipt_version"}) != record.model_dump():
            raise ValueError("inconsistent submission metadata")
        return record, receipt

    def _records(self):
        return [self._read(folder.name)[0] for folder in self.root.iterdir()
                if re.fullmatch(r"sub_[0-9a-f]{32}", folder.name)]

    @staticmethod
    def _write(path, data):
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

    @staticmethod
    def _sync_directory(path):
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    @classmethod
    def _write_atomic_new(cls, path, data):
        """Publish a complete immutable file without replacing an existing version."""
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.parent / f".{path.name}.{uuid4().hex}.pending"
        try:
            cls._write(temporary, data)
            os.link(temporary, path)
            cls._sync_directory(path.parent)
        finally:
            temporary.unlink(missing_ok=True)

    def receive(self, request: SubmissionRequest):
        snapshot, raw, images = validate_request(request)
        artifact = ArtifactReference(filename="snapshot.json", media_type="application/json", sha256=sha256(raw), size_bytes=len(raw))
        page_images = [ArtifactReference(filename=f"page_{page.index + 1}.png", media_type="image/png",
                          sha256=sha256(data), size_bytes=len(data), page_id=page.page_id, page_index=page.index)
                       for page, data in images]
        with self._locked(exclusive=True):
            for record in self._records():
                if record.snapshot_id == snapshot.local_snapshot_id:
                    if record.snapshot != artifact or record.page_images != page_images or record.student_reference != request.student_reference:
                        raise SubmissionConflict()
                    detail = self._detail(record.submission_id)
                    if not all(item.matches for item in detail.integrity):
                        raise SubmissionConflict()
                    return detail.receipt, False
            record = SubmissionRecord(submission_id=f"sub_{uuid4().hex}", problem_id=snapshot.problem_id,
                                      snapshot_id=snapshot.local_snapshot_id, received_at=datetime.now(timezone.utc),
                                      snapshot=artifact, page_images=page_images, student_reference=request.student_reference)
            receipt = SubmissionReceipt(**record.model_dump())
            pending = Path(tempfile.mkdtemp(prefix=".pending-", dir=self.root))
            try:
                self._write(pending / "snapshot.json", raw)
                for ref, (_, data) in zip(page_images, images):
                    self._write(pending / ref.filename, data)
                self._write(pending / "submission.json", record.model_dump_json(indent=2).encode("utf-8"))
                self._write(pending / "receipt.json", receipt.model_dump_json(indent=2).encode("utf-8"))
                self._sync_directory(pending)
                # One atomic publish; no separate idempotency index can get stale.
                os.replace(pending, self.root / record.submission_id)
                self._sync_directory(self.root)
            finally:
                if pending.exists():
                    shutil.rmtree(pending)
            return receipt, True

    def list(self):
        with self._locked():
            return sorted(self._records(), key=lambda item: item.received_at, reverse=True)

    def _detail(self, submission_id):
        record, receipt = self._read(submission_id)
        integrity = []
        for artifact in [record.snapshot, *record.page_images]:
            path = self._folder(submission_id) / artifact.filename
            digest = sha256(path.read_bytes()) if path.is_file() and not path.is_symlink() else None
            integrity.append(ArtifactIntegrity(filename=artifact.filename, expected_sha256=artifact.sha256,
                                               actual_sha256=digest, matches=digest == artifact.sha256))
        return SubmissionDetail(submission=record, receipt=receipt, integrity=integrity)

    def detail(self, submission_id):
        with self._locked():
            return self._detail(submission_id)

    def assert_submission_integrity(self, submission_id):
        """Validate the frozen source before writes; caller must hold the store lock.

        Unknown submissions remain 404. Missing/inconsistent artifacts or metadata
        of an existing submission are integrity conflicts, never repair requests.
        """
        folder = self._folder(submission_id)
        try:
            for name in ("submission.json", "receipt.json"):
                path = folder / name
                if path.is_symlink() or not path.is_file():
                    raise SubmissionIntegrityConflict()
            record, _ = self._read(submission_id)
            for artifact in [record.snapshot, *record.page_images]:
                path = folder / artifact.filename
                if path.is_symlink() or not path.is_file():
                    raise SubmissionIntegrityConflict()
                digest = hashlib.sha256()
                size = 0
                with path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(64 * 1024), b""):
                        digest.update(chunk)
                        size += len(chunk)
                if digest.hexdigest() != artifact.sha256 or size != artifact.size_bytes:
                    raise SubmissionIntegrityConflict()
            if (record.snapshot.filename != "snapshot.json"
                    or record.snapshot.media_type != "application/json"
                    or record.snapshot.size_bytes > MAX_IMPORT_BYTES):
                raise SubmissionIntegrityConflict()
            snapshot = CaptureSnapshot.model_validate_json((folder / "snapshot.json").read_bytes())
            if snapshot.problem_id != record.problem_id or snapshot.local_snapshot_id != record.snapshot_id:
                raise SubmissionIntegrityConflict()
            expected = {(page.index, page.page_id, f"page_{page.index + 1}.png") for page in snapshot.pages}
            actual = {(ref.page_index, ref.page_id, ref.filename) for ref in record.page_images}
            if (actual != expected or len(record.page_images) != len(expected)
                    or any(ref.media_type != "image/png" for ref in record.page_images)):
                raise SubmissionIntegrityConflict()
            return record
        except (ValueError, FileNotFoundError, IsADirectoryError) as exc:
            raise SubmissionIntegrityConflict() from exc

    def artifact(self, submission_id, page_index=None):
        with self._locked():
            detail = self._detail(submission_id)
            if page_index is None:
                ref = detail.submission.snapshot
            else:
                ref = next((item for item in detail.submission.page_images if item.page_index == page_index), None)
                if ref is None:
                    raise FileNotFoundError()
            if not next(item.matches for item in detail.integrity if item.filename == ref.filename):
                raise SubmissionConflict()
            return self._folder(submission_id) / ref.filename, ref

    @staticmethod
    def _transcription_name_valid(transcription_id):
        return re.fullmatch(r"tr_[0-9a-f]{32}", transcription_id) is not None

    def _transcriptions_folder(self, submission_id, create=False):
        folder = self._folder(submission_id) / "transcriptions"
        if folder.is_symlink():
            raise FileNotFoundError()
        if create:
            folder.mkdir(exist_ok=True)
        elif not folder.is_dir():
            return None
        return folder

    def _transcription_folder(self, transcription_id):
        if not self._transcription_name_valid(transcription_id):
            raise FileNotFoundError()
        matches = []
        for submission in self.root.iterdir():
            if not re.fullmatch(r"sub_[0-9a-f]{32}", submission.name):
                continue
            root = self._transcriptions_folder(submission.name)
            if root is None:
                continue
            candidate = root / transcription_id
            if candidate.is_dir() and not candidate.is_symlink():
                matches.append(candidate)
        if len(matches) != 1:
            raise FileNotFoundError() if not matches else ValueError("duplicate transcription ID")
        return matches[0]

    @staticmethod
    def _revision_path(folder, revision_number):
        return folder / "revisions" / f"revision_{revision_number:06d}.json"

    @staticmethod
    def _acceptance_path(folder, revision_number):
        return folder / "acceptances" / f"acceptance_{revision_number:06d}.json"

    def _read_transcription_record(self, folder):
        record = TranscriptionRecord.model_validate_json((folder / "transcription.json").read_bytes())
        if record.transcription_id != folder.name or folder.parent.parent.name != record.submission_id:
            raise ValueError("inconsistent transcription metadata")
        return record

    def _read_revisions(self, folder):
        root = folder / "revisions"
        if root.is_symlink() or not root.is_dir():
            raise ValueError("missing transcription revisions")
        revisions = []
        for path in sorted(root.glob("revision_*.json")):
            if path.is_symlink() or not re.fullmatch(r"revision_[0-9]{6}\.json", path.name):
                continue
            revision = TranscriptionRevision.model_validate_json(path.read_bytes())
            expected_number = int(path.stem.removeprefix("revision_"))
            if revision.revision_number != expected_number or revision.status == "ACCEPTED":
                raise ValueError("inconsistent persisted transcription revision")
            revisions.append(revision)
        if [revision.revision_number for revision in revisions] != list(range(1, len(revisions) + 1)):
            raise ValueError("non-contiguous transcription revisions")
        return revisions

    def _read_acceptances(self, folder):
        root = folder / "acceptances"
        if not root.exists():
            return []
        if root.is_symlink() or not root.is_dir():
            raise ValueError("invalid transcription acceptances")
        acceptances = []
        for path in sorted(root.glob("acceptance_*.json")):
            if path.is_symlink() or not re.fullmatch(r"acceptance_[0-9]{6}\.json", path.name):
                continue
            acceptance = TranscriptionAcceptance.model_validate_json(path.read_bytes())
            expected_number = int(path.stem.removeprefix("acceptance_"))
            if acceptance.revision_number != expected_number:
                raise ValueError("inconsistent transcription acceptance")
            acceptances.append(acceptance)
        return acceptances

    @staticmethod
    def _accepted_revisions(revisions, acceptances):
        accepted = {acceptance.revision_number for acceptance in acceptances}
        return [revision.model_copy(update={"status": "ACCEPTED"}) if revision.revision_number in accepted else revision
                for revision in revisions]

    @staticmethod
    def _validate_segment_pages(segments, record):
        page_indices = {page.page_index for page in record.page_images}
        if any(segment.page_index not in page_indices for segment in segments):
            raise ValueError("transcription segment references an unknown page")

    def create_transcription(self, submission_id: str, request: CreateTranscriptionRequest):
        with self._locked(exclusive=True):
            submission = self.assert_submission_integrity(submission_id)
            self._validate_segment_pages(request.segments, submission)
            now = datetime.now(timezone.utc)
            transcription = TranscriptionRecord(
                transcription_id=f"tr_{uuid4().hex}", submission_id=submission_id,
                created_at=now, source=request.source, recognizer=request.recognizer,
                recognizer_version=request.recognizer_version,
            )
            revision = TranscriptionRevision(
                **transcription.model_dump(), revision_number=1, based_on_revision_number=None,
                reviewer_reference=request.reviewer_reference,
                reviewer_identity_verified=request.reviewer_identity_verified,
                change_type="initial_transcription", segments=request.segments, status=request.status,
            )
            root = self._transcriptions_folder(submission_id, create=True)
            pending = Path(tempfile.mkdtemp(prefix=".pending-transcription-", dir=root))
            try:
                (pending / "revisions").mkdir()
                (pending / "acceptances").mkdir()
                self._write(pending / "transcription.json", transcription.model_dump_json(indent=2).encode("utf-8"))
                self._write(self._revision_path(pending, 1), revision.model_dump_json(indent=2).encode("utf-8"))
                self._sync_directory(pending / "revisions")
                self._sync_directory(pending / "acceptances")
                self._sync_directory(pending)
                os.replace(pending, root / transcription.transcription_id)
                self._sync_directory(root)
            finally:
                if pending.exists():
                    shutil.rmtree(pending)
            return revision

    def list_transcriptions(self, submission_id: str):
        with self._locked():
            self._read(submission_id)
            root = self._transcriptions_folder(submission_id)
            if root is None:
                return []
            summaries = []
            for folder in sorted(root.iterdir()):
                if not folder.is_dir() or folder.is_symlink() or not self._transcription_name_valid(folder.name):
                    continue
                history = self._history_from_folder(folder)
                summaries.append(TranscriptionSummary(
                    transcription=history.transcription, latest_revision=history.revisions[-1],
                ))
            return sorted(summaries, key=lambda item: item.transcription.created_at, reverse=True)

    def _history_from_folder(self, folder):
        record = self._read_transcription_record(folder)
        acceptances = self._read_acceptances(folder)
        revisions = self._read_revisions(folder)
        if any(
            revision.transcription_id != record.transcription_id
            or revision.submission_id != record.submission_id
            or revision.source != record.source
            for revision in revisions
        ):
            raise ValueError("revision is not bound to its transcription")
        if any(
            acceptance.transcription_id != record.transcription_id
            or acceptance.submission_id != record.submission_id
            or acceptance.revision_number > len(revisions)
            for acceptance in acceptances
        ):
            raise ValueError("acceptance is not bound to its transcription revision")
        revisions = self._accepted_revisions(revisions, acceptances)
        return TranscriptionHistory(transcription=record, revisions=revisions, acceptances=acceptances)

    def _transcription_history(self, transcription_id: str):
        return self._history_from_folder(self._transcription_folder(transcription_id))

    def transcription_history(self, transcription_id: str):
        with self._locked():
            return self._transcription_history(transcription_id)

    def create_transcription_revision(self, transcription_id: str, request: CreateTranscriptionRevisionRequest):
        with self._locked(exclusive=True):
            folder = self._transcription_folder(transcription_id)
            record = self._read_transcription_record(folder)
            submission = self.assert_submission_integrity(record.submission_id)
            self._validate_segment_pages(request.segments, submission)
            revisions = self._read_revisions(folder)
            if request.based_on_revision_number != revisions[-1].revision_number:
                raise TranscriptionConflict("revision is not based on the latest version")
            revision_number = revisions[-1].revision_number + 1
            revision = TranscriptionRevision(
                **{**record.model_dump(), "created_at": datetime.now(timezone.utc)}, revision_number=revision_number,
                based_on_revision_number=request.based_on_revision_number,
                reviewer_reference=request.reviewer_reference,
                reviewer_identity_verified=request.reviewer_identity_verified,
                change_type=request.change_type, change_reason=request.change_reason,
                segments=request.segments, status=request.status,
            )
            self._write_atomic_new(
                self._revision_path(folder, revision_number),
                revision.model_dump_json(indent=2).encode("utf-8"),
            )
            return revision

    def accept_transcription(self, transcription_id: str, request: AcceptTranscriptionRequest):
        with self._locked(exclusive=True):
            folder = self._transcription_folder(transcription_id)
            self.assert_submission_integrity(folder.parent.parent.name)
            history = self._transcription_history(transcription_id)
            revision = next((item for item in history.revisions if item.revision_number == request.revision_number), None)
            if revision is None:
                raise FileNotFoundError()
            existing = next((item for item in history.acceptances if item.revision_number == request.revision_number), None)
            if existing is not None:
                if (existing.reviewer_reference != request.reviewer_reference
                        or existing.acceptance_note != request.acceptance_note):
                    raise TranscriptionConflict("revision already accepted with different metadata")
                return AcceptedTranscription(revision=revision, acceptance=existing)
            acceptance = TranscriptionAcceptance(
                acceptance_id=f"acc_{uuid4().hex}", transcription_id=transcription_id,
                submission_id=history.transcription.submission_id,
                revision_number=request.revision_number, accepted_at=datetime.now(timezone.utc),
                reviewer_reference=request.reviewer_reference,
                reviewer_identity_verified=request.reviewer_identity_verified,
                acceptance_note=request.acceptance_note,
            )
            self._write_atomic_new(
                self._acceptance_path(folder, request.revision_number),
                acceptance.model_dump_json(indent=2).encode("utf-8"),
            )
            return AcceptedTranscription(
                revision=revision.model_copy(update={"status": "ACCEPTED"}), acceptance=acceptance,
            )
