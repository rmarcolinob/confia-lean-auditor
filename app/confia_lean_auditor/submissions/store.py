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
    ArtifactIntegrity, ArtifactReference, CaptureSnapshot, MAX_PNG_BYTES,
    SubmissionDetail, SubmissionReceipt, SubmissionRecord, SubmissionRequest,
)


class SubmissionConflict(ValueError):
    pass


class SubmissionTooLarge(ValueError):
    pass


class InvalidSubmissionProblem(ValueError):
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
