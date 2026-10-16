"""Local Assessment repository; replaceable by a transactional database adapter."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4

from confia_lean_auditor.core.paths import get_repo_root
from .models import Assessment, AssessmentDocument, AssessmentItem


class AssessmentConflict(ValueError):
    pass


class AssessmentIntegrityConflict(AssessmentConflict):
    pass


def assessment_store():
    configured = os.environ.get("CONFIA_ASSESSMENTS_DIR")
    return AssessmentStore(Path(configured).resolve() if configured else get_repo_root() / "runtime" / "assessments")


def definition_hash(document: AssessmentDocument) -> str:
    assessment = document.assessment
    fields = ("schema_version", "assessment_id", "title", "instructions", "teacher_user_id", "network_id",
              "school_id", "classroom_id", "academic_year", "opens_at", "closes_at")
    raw = assessment.model_dump(mode="json")
    definition = {field: raw[field] for field in fields}
    definition["items"] = [item.model_dump(mode="json") for item in sorted(document.items, key=lambda x: x.order)]
    return hashlib.sha256(json.dumps(definition, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class AssessmentStore:
    def __init__(self, root: Path):
        self.root = root

    @contextmanager
    def _locked(self):
        if self.root.is_symlink():
            raise AssessmentIntegrityConflict("invalid assessment directory")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.root / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _path(self, assessment_id):
        if not isinstance(assessment_id, str) or len(assessment_id) != 37 or not assessment_id.startswith("asmt_") \
                or any(character not in "0123456789abcdef" for character in assessment_id[5:]):
            raise FileNotFoundError()
        return self.root / f"{assessment_id}.json"

    def _read(self, assessment_id):
        path = self._path(assessment_id)
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError()
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as handle:
            document = AssessmentDocument.model_validate_json(handle.read())
        if document.assessment.assessment_id != assessment_id:
            raise AssessmentIntegrityConflict("assessment ID mismatch")
        if document.assessment.status != "DRAFT" and document.assessment.definition_sha256 != definition_hash(document):
            raise AssessmentIntegrityConflict("published definition hash mismatch")
        return document

    def _write(self, document):
        path = self._path(document.assessment.assessment_id)
        if path.is_symlink():
            raise AssessmentIntegrityConflict("invalid assessment path")
        fd, temporary = tempfile.mkstemp(prefix=".asmt-", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as handle:
                os.fchmod(handle.fileno(), 0o600)
                handle.write(document.model_dump_json(indent=2).encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            dirfd = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(dirfd)
            finally:
                os.close(dirfd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def list(self):
        with self._locked():
            return [self._read(path.stem) for path in sorted(self.root.glob("asmt_*.json"))]

    def get(self, assessment_id):
        with self._locked():
            return self._read(assessment_id)

    def migrate_demo_title(self, assessment_id, *, expected_document, old_title, new_title):
        """Rename a prevalidated demo publication without changing its other fields."""
        with self._locked():
            current = self._read(assessment_id)
            if (current != expected_document or current.assessment.status != "PUBLISHED"
                    or current.assessment.title != old_title):
                raise AssessmentConflict("demo assessment changed during title migration")
            renamed = AssessmentDocument(assessment=current.assessment.model_copy(update={"title": new_title}),
                                         items=current.items)
            assessment = Assessment.model_validate({**renamed.assessment.model_dump(),
                                                    "definition_sha256": definition_hash(renamed)})
            changed = AssessmentDocument(assessment=assessment, items=current.items)
            self._write(changed)
            return changed

    def create(self, *, title, instructions, teacher_user_id, network_id, school_id, classroom_id,
               academic_year, opens_at, closes_at, assessment_id=None):
        assessment_id = assessment_id or f"asmt_{uuid4().hex}"
        with self._locked():
            if self._path(assessment_id).exists():
                raise AssessmentConflict("assessment ID already exists")
            document = AssessmentDocument(assessment=Assessment(
                assessment_id=assessment_id, title=title, instructions=instructions, teacher_user_id=teacher_user_id,
                network_id=network_id, school_id=school_id, classroom_id=classroom_id, academic_year=academic_year,
                opens_at=opens_at, closes_at=closes_at, created_at=datetime.now(timezone.utc)))
            self._write(document)
            return document

    def _edit(self, assessment_id, operation):
        with self._locked():
            document = self._read(assessment_id)
            if document.assessment.status != "DRAFT":
                raise AssessmentConflict("published assessment is immutable")
            changed = operation(document)
            self._write(changed)
            return changed

    def update(self, assessment_id, changes):
        def change(document):
            values = document.assessment.model_dump()
            values.update(changes)
            return AssessmentDocument(assessment=Assessment.model_validate(values), items=document.items)
        return self._edit(assessment_id, change)

    def add_item(self, assessment_id, problem_id, points, assessment_item_id=None):
        def change(document):
            item = AssessmentItem(assessment_item_id=assessment_item_id or f"ait_{uuid4().hex}",
                assessment_id=assessment_id, problem_id=problem_id, order=len(document.items) + 1, points=points)
            return AssessmentDocument(assessment=document.assessment, items=[*document.items, item])
        return self._edit(assessment_id, change)

    def update_item(self, assessment_id, item_id, points):
        def change(document):
            if item_id not in {item.assessment_item_id for item in document.items}:
                raise FileNotFoundError()
            return AssessmentDocument(assessment=document.assessment, items=[
                item.model_copy(update={"points": points}) if item.assessment_item_id == item_id else item
                for item in document.items])
        return self._edit(assessment_id, change)

    def remove_item(self, assessment_id, item_id):
        def change(document):
            items = [item for item in document.items if item.assessment_item_id != item_id]
            if len(items) == len(document.items):
                raise FileNotFoundError()
            return AssessmentDocument(assessment=document.assessment,
                items=[item.model_copy(update={"order": index}) for index, item in enumerate(items, 1)])
        return self._edit(assessment_id, change)

    def publish(self, assessment_id):
        def change(document):
            if not document.items:
                raise AssessmentConflict("assessment requires at least one item")
            now = datetime.now(timezone.utc)
            assessment = document.assessment.model_copy(update={"status": "PUBLISHED", "published_at": now,
                "definition_sha256": definition_hash(document)})
            return AssessmentDocument(assessment=assessment, items=document.items)
        return self._edit(assessment_id, change)

    def close(self, assessment_id):
        with self._locked():
            document = self._read(assessment_id)
            if document.assessment.status == "CLOSED":
                return document
            if document.assessment.status != "PUBLISHED":
                raise AssessmentConflict("draft cannot be closed")
            changed = AssessmentDocument(assessment=document.assessment.model_copy(update={
                "status": "CLOSED", "closed_at": datetime.now(timezone.utc)}), items=document.items)
            self._write(changed)
            return changed
