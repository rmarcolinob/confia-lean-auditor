"""Local institutional repository. Routers use this interface, never JSON files."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import tempfile

from confia_lean_auditor.auth.models import AuthUser, Role
from confia_lean_auditor.core.paths import get_repo_root
from .models import InstitutionalContext, InstitutionalData

FILES = {
    "networks": "networks.json", "schools": "schools.json", "classrooms": "classrooms.json",
    "teacher_assignments": "teacher_assignments.json", "enrollments": "enrollments.json",
    "manager_assignments": "manager_assignments.json",
}


class InstitutionalScopeError(ValueError):
    def __init__(self, message: str, status_code: int = 403):
        super().__init__(message)
        self.status_code = status_code


def current_academic_year() -> int:
    return datetime.now(timezone.utc).year


def institutional_store() -> "InstitutionalStore":
    configured = os.environ.get("CONFIA_INSTITUTIONAL_DIR")
    return InstitutionalStore(Path(configured).resolve() if configured else get_repo_root() / "runtime" / "institutional")


class InstitutionalStore:
    def __init__(self, root: Path):
        self.root = root

    @contextmanager
    def _locked(self):
        if self.root.is_symlink():
            raise ValueError("invalid institutional directory")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        fd = os.open(self.root / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _read(self) -> InstitutionalData:
        values = {}
        for field, filename in FILES.items():
            path = self.root / filename
            if path.is_symlink():
                raise ValueError("invalid institutional file")
            values[field] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        return InstitutionalData.model_validate(values)

    def snapshot(self) -> InstitutionalData:
        with self._locked():
            return self._read()

    def _write_collection(self, filename: str, values: list[dict]):
        destination = self.root / filename
        if destination.is_symlink():
            raise ValueError("invalid institutional file")
        fd, temporary = tempfile.mkstemp(prefix=".inst-", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                os.fchmod(handle.fileno(), 0o600)
                json.dump(values, handle, ensure_ascii=False, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def replace(self, data: InstitutionalData):
        """Administrative/seed operation; no public write route exposes it."""
        data = InstitutionalData.model_validate(data.model_dump(mode="json") if isinstance(data, InstitutionalData) else data)
        with self._locked():
            for field, filename in FILES.items():
                self._write_collection(filename, [item.model_dump(mode="json") for item in getattr(data, field)])

    def merge_seed(self, seed: InstitutionalData):
        """Add demo entities once while preserving existing institutional records."""
        seed = InstitutionalData.model_validate(seed.model_dump(mode="json") if isinstance(seed, InstitutionalData) else seed)
        with self._locked():
            existing = self._read()
            values = existing.model_dump(mode="json")
            keys = {
                "networks": lambda x: x["network_id"], "schools": lambda x: x["school_id"],
                "classrooms": lambda x: x["classroom_id"],
                "teacher_assignments": lambda x: (x["teacher_user_id"], x["classroom_id"], x["academic_year"]),
                "enrollments": lambda x: (x["student_user_id"], x["classroom_id"], x["academic_year"]),
                "manager_assignments": lambda x: (x["manager_user_id"], x["network_id"], x["school_id"]),
            }
            for field in FILES:
                present = {keys[field](item) for item in values[field]}
                for item in getattr(seed, field):
                    raw = item.model_dump(mode="json")
                    if keys[field](raw) not in present:
                        values[field].append(raw)
                        present.add(keys[field](raw))
            merged = InstitutionalData.model_validate(values)
            for field, filename in FILES.items():
                self._write_collection(filename, [item.model_dump(mode="json") for item in getattr(merged, field)])

    @staticmethod
    def _active(data: InstitutionalData):
        networks = {n.network_id: n for n in data.networks if n.active}
        schools = {s.school_id: s for s in data.schools if s.active and s.network_id in networks}
        classrooms = {c.classroom_id: c for c in data.classrooms if c.active and c.school_id in schools}
        return networks, schools, classrooms

    def student_enrollment(self, user: AuthUser, year: int | None = None):
        year = year or current_academic_year()
        data = self.snapshot()
        _, schools, classrooms = self._active(data)
        matches = [item for item in data.enrollments if item.active and item.student_user_id == user.user_id
                   and item.academic_year == year and item.school_id in schools
                   and item.classroom_id in classrooms]
        if len(matches) != 1:
            raise InstitutionalScopeError("Matrícula ativa ausente ou ambígua.", 409 if matches else 403)
        return matches[0], schools[matches[0].school_id]

    def schools_for(self, user: AuthUser, year: int | None = None):
        year = year or current_academic_year()
        data = self.snapshot()
        networks, schools, classrooms = self._active(data)
        if user.role == Role.STUDENT:
            enrollment, _ = self.student_enrollment(user, year)
            ids = {enrollment.school_id}
        elif user.role == Role.TEACHER:
            ids = {a.school_id for a in data.teacher_assignments if a.active and a.teacher_user_id == user.user_id
                   and a.academic_year == year and a.classroom_id in classrooms}
        elif user.role == Role.SCHOOL_MANAGER:
            ids = {a.school_id for a in data.manager_assignments if a.active and a.manager_user_id == user.user_id
                   and a.school_id is not None}
        elif user.role == Role.NETWORK_MANAGER:
            network_ids = {a.network_id for a in data.manager_assignments if a.active
                           and a.manager_user_id == user.user_id and a.network_id in networks}
            ids = {s.school_id for s in schools.values() if s.network_id in network_ids}
        else:
            ids = set()
        return sorted((s for s in schools.values() if s.school_id in ids), key=lambda s: s.name)

    def classrooms_for(self, user: AuthUser, school_id: str, year: int | None = None):
        year = year or current_academic_year()
        if school_id not in {s.school_id for s in self.schools_for(user, year)}:
            raise InstitutionalScopeError("Escola fora do escopo autorizado.")
        data = self.snapshot()
        _, _, classrooms = self._active(data)
        candidates = [c for c in classrooms.values() if c.school_id == school_id and c.academic_year == year]
        if user.role == Role.STUDENT:
            enrollment, _ = self.student_enrollment(user, year)
            candidates = [c for c in candidates if c.classroom_id == enrollment.classroom_id]
        elif user.role == Role.TEACHER:
            ids = {a.classroom_id for a in data.teacher_assignments if a.active
                   and a.teacher_user_id == user.user_id and a.academic_year == year and a.school_id == school_id}
            candidates = [c for c in candidates if c.classroom_id in ids]
        return sorted(candidates, key=lambda c: c.name)

    def context_for(self, user: AuthUser) -> InstitutionalContext:
        year = current_academic_year()
        schools = self.schools_for(user, year)
        classes = [c for s in schools for c in self.classrooms_for(user, s.school_id, year)]
        return InstitutionalContext(role=user.role.value, academic_year=year, schools=schools, classrooms=classes,
                                    selected_school_id=schools[0].school_id if len(schools) == 1 else None,
                                    selected_classroom_id=classes[0].classroom_id if len(classes) == 1 else None)

    def teacher_can_view(self, user: AuthUser, record) -> bool:
        if not all((record.network_id, record.school_id, record.classroom_id)):
            return False
        data = self.snapshot()
        _, schools, classrooms = self._active(data)
        school = schools.get(record.school_id)
        classroom = classrooms.get(record.classroom_id)
        if school is None or classroom is None or classroom.school_id != school.school_id \
                or school.network_id != record.network_id:
            return False
        return any(a.active and a.teacher_user_id == user.user_id and a.school_id == record.school_id
                   and a.classroom_id == record.classroom_id and a.academic_year == classroom.academic_year
                   for a in data.teacher_assignments)
