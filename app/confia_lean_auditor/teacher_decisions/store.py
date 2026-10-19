"""Local repository boundary: one decision per submission and serialized mutations.

A PostgreSQL adapter can implement get/get_for_submission/create/update with a
UNIQUE(submission_id), row locks, and the same validation and lifecycle rules.
"""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import re
import tempfile

from pydantic import ValidationError

from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.submissions.integrity import canonical_sha256
from .models import TeacherDecision


class DecisionConflict(ValueError):
    pass


class DecisionIntegrityError(DecisionConflict):
    pass


def decision_store():
    configured = os.environ.get("CONFIA_TEACHER_DECISIONS_DIR")
    return TeacherDecisionStore(Path(configured).absolute() if configured
                                else get_repo_root() / "runtime" / "teacher_decisions")


def decision_id_for(submission_id):
    if not isinstance(submission_id, str) or not re.fullmatch(r"sub_[0-9a-f]{32}", submission_id):
        raise FileNotFoundError()
    return "dec_" + submission_id[4:]


def decision_hash(decision):
    # Release is an independent publication event; all final content stays hashed.
    return canonical_sha256(decision.model_dump(mode="json", exclude={
        "status", "updated_at", "released_at", "version", "decision_sha256"}))


class TeacherDecisionStore:
    def __init__(self, root: Path):
        self.root = root

    @contextmanager
    def _locked(self):
        if self.root.is_symlink():
            raise DecisionIntegrityError("invalid decision directory")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.root / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _path(self, decision_id):
        if not isinstance(decision_id, str) or not re.fullmatch(r"dec_[0-9a-f]{32}", decision_id):
            raise FileNotFoundError()
        return self.root / f"{decision_id}.json"

    @staticmethod
    def _validated(decision):
        try:
            decision = TeacherDecision.model_validate(decision.model_dump())
        except ValidationError as exc:
            raise DecisionIntegrityError("invalid decision document") from exc
        if decision.decision_id != decision_id_for(decision.submission_id):
            raise DecisionIntegrityError("decision/submission ID mismatch")
        if decision.status != "DRAFT" and decision.decision_sha256 != decision_hash(decision):
            raise DecisionIntegrityError("final decision digest mismatch")
        return decision

    def _read(self, decision_id):
        path = self._path(decision_id)
        if path.is_symlink():
            raise DecisionIntegrityError("invalid decision file")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            with os.fdopen(fd, "rb") as handle:
                decision = TeacherDecision.model_validate_json(handle.read())
        except ValidationError as exc:
            raise DecisionIntegrityError("invalid persisted decision") from exc
        if decision.decision_id != decision_id:
            raise DecisionIntegrityError("decision ID mismatch")
        return self._validated(decision)

    def _write(self, decision):
        decision = self._validated(decision)
        path = self._path(decision.decision_id)
        if path.is_symlink():
            raise DecisionIntegrityError("invalid decision file")
        fd, temporary = tempfile.mkstemp(dir=self.root, prefix=".decision-")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(decision.model_dump_json(indent=2).encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            directory_fd = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return decision

    def get(self, decision_id):
        with self._locked():
            return self._read(decision_id)

    def get_for_submission(self, submission_id):
        try:
            return self.get(decision_id_for(submission_id))
        except FileNotFoundError:
            return None

    def create(self, submission_id, factory):
        with self._locked():
            decision_id = decision_id_for(submission_id)
            try:
                return self._read(decision_id), False
            except FileNotFoundError:
                decision = factory(decision_id)
                if decision.submission_id != submission_id or decision.status != "DRAFT":
                    raise DecisionIntegrityError("invalid new decision")
                return self._write(decision), True

    def update(self, decision_id, operation):
        with self._locked():
            before = self._read(decision_id)
            after = operation(before.model_copy(deep=True))
            if (after.decision_id, after.submission_id, after.created_at) != (
                    before.decision_id, before.submission_id, before.created_at):
                raise DecisionIntegrityError("immutable decision identity changed")
            if before.status != "DRAFT" and after != before:
                allowed = before.model_copy(update={"status": "RELEASED", "released_at": after.released_at,
                    "updated_at": after.updated_at, "version": before.version + 1})
                if before.status != "FINALIZED" or after != allowed:
                    raise DecisionConflict("Decisão finalizada não pode ser editada.")
            return before if after == before else self._write(after)
