"""Small operational envelope; the solution stays in Submission artifacts."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import os
from pathlib import Path
import re
from uuid import uuid4

from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.core.problem_catalog import CATALOG
from .models import CaseCreate, CorrectionCase, EvaluatorDecision


def case_store():
    configured = os.environ.get("CONFIA_TME_CASES_DIR")
    return CaseStore(Path(configured).resolve() if configured else get_repo_root() / "runtime" / "tme_cases")


class CaseStore:
    def __init__(self, root: Path):
        self.root = root

    @contextmanager
    def locked(self):
        if self.root.is_symlink():
            raise ValueError("invalid case directory")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        fd = os.open(self.root / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "a+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def folder(self, case_id):
        if not re.fullmatch(r"case_[0-9a-f]{32}", case_id):
            raise FileNotFoundError()
        folder = self.root / case_id
        if folder.is_symlink() or not folder.is_dir():
            raise FileNotFoundError()
        return folder

    def read(self, case_id):
        path = self.folder(case_id) / "case.json"
        if path.is_symlink():
            raise ValueError("invalid case path")
        return CorrectionCase.model_validate_json(path.read_bytes())

    def for_user(self, case_id, user):
        case = self.read(case_id)
        if user is None or case.created_by_user_id != user.user_id:
            from fastapi import HTTPException
            raise HTTPException(403, "Correção fora do escopo autorizado.")
        return case

    def create(self, body: CaseCreate, user):
        if body.problem_id not in CATALOG:
            raise ValueError("Questão não disponível no catálogo.")
        case = CorrectionCase(**body.model_dump(), case_id=f"case_{uuid4().hex}",
            created_by_user_id=user.user_id, created_at=datetime.now(timezone.utc))
        with self.locked():
            folder = self.root / case.case_id
            folder.mkdir(mode=0o700)
            fd = os.open(folder / "case.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(case.model_dump_json(indent=2).encode())
        from .home_summary import project_case
        project_case(case, root=self.root)
        return case

    def list_for_user(self, user):
        with self.locked():
            cases = [self.read(path.name) for path in self.root.iterdir()
                     if path.is_dir() and re.fullmatch(r"case_[0-9a-f]{32}", path.name)]
        return sorted((c for c in cases if c.created_by_user_id == user.user_id),
                      key=lambda c: c.created_at, reverse=True)

    def bind(self, case_id, submission_id, user):
        with self.locked():
            case = self.for_user(case_id, user)
            from confia_lean_auditor.submissions.router import store as submission_store
            record = submission_store().get_record(submission_id)
            if (record.tme_case_id != case_id or record.problem_id != case.problem_id
                    or record.submitted_by_user_id != user.user_id
                    or record.source != ("tablet" if case.source_mode == "DIGITAL_INK" else "image_scan")):
                raise ValueError("case/source binding mismatch")
            if case.submission_id is not None:
                if case.submission_id == submission_id:
                    return case
                raise ValueError("Correção já possui uma fonte imutável.")
            case = case.model_copy(update={"submission_id": submission_id, "status": "SOURCE_READY"})
            path = self.folder(case_id) / "case.json"
            temporary = path.with_suffix(".pending")
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(case.model_dump_json(indent=2).encode())
            os.replace(temporary, path)
            from .home_summary import project_case
            project_case(case, record.received_at, root=self.root)
            return case

    def decide(self, case_id, decision: EvaluatorDecision, user):
        with self.locked():
            case = self.for_user(case_id, user)
            if not case.submission_id:
                raise ValueError("Correção sem solução.")
            path = self.folder(case_id) / "decision.json"
            if path.exists():
                raise ValueError("Decisão já registrada.")
            with path.open("xb") as handle:
                handle.write(decision.model_dump_json(indent=2).encode())
                handle.flush()
                os.fsync(handle.fileno())
            case = case.model_copy(update={"status": "DECIDED"})
            temporary = self.folder(case_id) / "case.pending"
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(case.model_dump_json(indent=2).encode())
            os.replace(temporary, self.folder(case_id) / "case.json")
            from .home_summary import project_case
            project_case(case, decision.decided_at, root=self.root)
            return decision

    def decision(self, case_id, user):
        self.for_user(case_id, user)
        path = self.folder(case_id) / "decision.json"
        if not path.exists():
            return None
        if path.is_symlink():
            raise ValueError("invalid decision path")
        return EvaluatorDecision.model_validate_json(path.read_bytes())
