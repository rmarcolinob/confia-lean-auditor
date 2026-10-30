"""Disposable operational projection. Never used for authorization or grading.

Writes consume already persisted models; Home reads one bounded-per-case metadata
index. Legacy reconstruction runs at startup/offline, never in the GET endpoint.
"""
from contextlib import contextmanager
from datetime import datetime, time, timedelta, timezone
import fcntl
import json
import logging
import os
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Literal
from uuid import uuid4
from zoneinfo import ZoneInfo

from pydantic import Field

from confia_lean_auditor.submissions.schemas import SubmissionModel
from .store import case_store

Period = Literal["today", "7d", "30d", "all"]
Status = Literal["pending", "in_progress", "inconclusive", "finalized"]
LOGGER = logging.getLogger(__name__)


class Counts(SubmissionModel):
    pending: int = 0
    inconclusive: int = 0
    finalized: int = 0
    in_progress: int = 0


class PriorityCase(SubmissionModel):
    case_id: str
    exam_code: str
    problem_id: str
    question_label: str
    source_mode: Literal["DIGITAL_INK", "IMAGE_SCAN"]
    operational_status: Status
    updated_at: datetime


class ExamProgress(SubmissionModel):
    exam_code: str
    completed_items: int
    known_items: int
    percent: float
    latest_update: datetime


class HomeSummary(SubmissionModel):
    period: Period
    counts: Counts
    priority_cases: list[PriorityCase] = Field(max_length=3)
    exam_progress: list[ExamProgress] = Field(max_length=2)
    generated_at: datetime


def instant(value):
    return datetime.fromisoformat(value) if isinstance(value, str) else value


def stamp(value):
    return instant(value).astimezone(timezone.utc).isoformat()


def touch(entry, value):
    entry["updated_at"] = max(entry["updated_at"], stamp(value))


def case_entry(case):
    return dict(case_id=case.case_id, owner=case.created_by_user_id,
                exam_code=case.external_candidate_ref, problem_id=case.problem_id,
                source_mode=case.source_mode, submission_id=case.submission_id,
                created_at=stamp(case.created_at), updated_at=stamp(case.created_at),
                decided=case.status == "DECIDED", transcription=None,
                recognition=None, audit=None)


def apply_transcription(entry, record, revision, accepted_at=None):
    current = entry["transcription"]
    candidate = dict(id=record.transcription_id, created_at=stamp(record.created_at),
                     revision=revision.revision_number)
    # Same chronology as list_transcriptions / AuditService.view; IDs break ties.
    if current and (candidate["created_at"], candidate["id"], candidate["revision"]) < (
            current["created_at"], current["id"], current["revision"]):
        return
    entry["transcription"] = candidate
    audit = entry["audit"]
    if audit and (audit["transcription_id"], audit["revision"]) != (candidate["id"], candidate["revision"]):
        entry["audit"] = None
    touch(entry, accepted_at or revision.created_at)


def apply_recognition(entry, run):
    candidate = dict(id=run.recognizer_run_id, created_at=stamp(run.provenance.created_at), status=run.status)
    previous = entry["recognition"]
    if not previous or (candidate["created_at"], candidate["id"]) > (previous["created_at"], previous["id"]):
        entry["recognition"] = candidate
        touch(entry, run.provenance.created_at)


def apply_audit(entry, run):
    current = entry["transcription"]
    if not current or (current["id"], current["revision"]) != (run.transcription_id, run.revision_number):
        return  # Historical accepted sources remain historical.
    candidate = dict(id=run.audit_run_id, created_at=stamp(run.created_at),
                     transcription_id=run.transcription_id, revision=run.revision_number,
                     status=run.status, inconclusive=bool(run.status == "COMPLETED" and run.result and
                         (run.result.score is None or run.result.verdict == "inconclusivo")))
    # Display-only summary; never consumed by decisions or grading.
    candidate["score"] = float(run.result.score) if run.result and run.result.score is not None else None
    candidate["max_score"] = float(run.result.max_score) if run.result and run.result.max_score is not None else None
    previous = entry["audit"]
    # Match the existing workspace runFor: prefer the newest current COMPLETED
    # run; a technical retry failure does not invalidate an earlier valid result.
    def rank(audit):
        return (audit["status"] == "COMPLETED", audit["created_at"], audit["id"])
    if not previous or rank(candidate) > rank(previous):
        entry["audit"] = candidate
    touch(entry, run.created_at)


class OperationalIndex:
    def __init__(self, root=None):
        self.root = Path(root) if root else case_store().root
        self.path = self.root / ".home-summary.json"
        self.dirty = self.root / ".home-summary-dirty"

    @contextmanager
    def locked(self):
        if self.root.is_symlink():
            raise ValueError("invalid operational directory")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.root / ".home-summary.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def read(self):
        if self.path.is_symlink():
            raise ValueError("invalid operational index")
        if not self.path.exists():
            return {"version": 1, "generation": 0, "complete": False, "cases": {}}
        data = json.loads(self.path.read_bytes())
        if (not isinstance(data, dict) or data.get("version") != 1
                or not isinstance(data.get("cases"), dict)
                or not isinstance(data.get("generation"), int)
                or not isinstance(data.get("complete"), bool)):
            raise ValueError("invalid operational index")
        return data

    def write(self, data):
        temporary = self.root / f".home-summary-{uuid4().hex}.pending"
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(data, handle, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def update(self, operation):
        with self.locked():
            # A failed projection must not silently publish stale indicators.
            was_dirty = self.dirty.exists()
            fd = os.open(self.dirty, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
            os.close(fd)
            data = self.read()
            operation(data["cases"])
            data["generation"] += 1
            self.write(data)
            if not was_dirty:
                self.dirty.unlink()

    def entries_for(self, owner):
        with self.locked():
            data = self.read()
            if not data["complete"] or (self.dirty.exists() or self.dirty.is_symlink()):
                raise ValueError("operational index requires reconstruction")
        return [e for e in data["cases"].values() if e["owner"] == owner]

    def summary(self, owner, period="today", now=None):
        return summarize(self.entries_for(owner), period, now)

    def listing(self, owner, view, *, page=1, size=50, search="", question="", status="", source="", exam=""):
        entries = self.entries_for(owner)
        if view == "results":
            summary = summarize(entries, "all").model_dump(mode="json")
            questions = {}
            for entry in entries:
                count = questions.setdefault(entry["problem_id"], Counts())
                key = operational_status(entry)
                setattr(count, key, getattr(count, key) + 1)
            return dict(summary=summary, questions=[dict(problem_id=key, **value.model_dump())
                        for key, value in sorted(questions.items())])
        available_questions = sorted({e["problem_id"] for e in entries})
        if exam:
            entries = list(known_questions(entries).get(exam, {}).values())
        selected = [e for e in entries if search.casefold() in e["exam_code"].casefold()
                    and (not exam or e["exam_code"] == exam)
                    and (not question or e["problem_id"] == question)
                    and (not status or operational_status(e) == status)
                    and (not source or e["source_mode"] == source)]
        if view == "exams":
            items = []
            for code, questions in known_questions(selected).items():
                done = sum(e["decided"] for e in questions.values())
                items.append(dict(exam_code=code, completed_items=done, known_items=len(questions),
                    latest_update=max(e["updated_at"] for e in questions.values()),
                    questions=[listing_case(e) for _, e in sorted(questions.items())]))
            items.sort(key=lambda e: e["exam_code"])
            items.sort(key=lambda e: e["latest_update"], reverse=True)
        else:
            selected.sort(key=lambda e: e["case_id"])
            selected.sort(key=lambda e: e["updated_at"], reverse=True)
            items = selected
        total = len(items)
        page = min(page, max(1, (total + size - 1) // size))
        items = items[(page - 1) * size:page * size]
        if view == "queue":
            items = [listing_case(e) for e in items]
        return dict(items=items, total=total, page=page, size=size, questions=available_questions)


def project_case(case, updated_at=None, root=None):
    def update(entries):
        previous = entries.get(case.case_id)
        entry = case_entry(case)
        if previous:
            entry.update({k: previous[k] for k in ("updated_at", "transcription", "recognition", "audit")})
        if updated_at:
            touch(entry, updated_at)
        entries[case.case_id] = entry
    _publish(update, root)


def project_submission(submission, *, transcription=None, revision=None, accepted_at=None, recognition=None, audit=None):
    if not submission.tme_case_id:
        return
    def update(entries):
        entry = entries[submission.tme_case_id]
        if (entry["submission_id"] != submission.submission_id or entry["owner"] != submission.submitted_by_user_id
                or entry["problem_id"] != submission.problem_id):
            raise ValueError("operational source binding mismatch")
        if transcription is not None:
            apply_transcription(entry, transcription, revision, accepted_at)
        if recognition is not None:
            apply_recognition(entry, recognition)
        if audit is not None:
            apply_audit(entry, audit)
    _publish(update)


def _publish(update, root=None):
    try:
        OperationalIndex(root).update(update)
    except (OSError, ValueError, KeyError, TypeError):
        # Primary immutable publication has succeeded. Do not change its outcome.
        # The dirty marker keeps Home unavailable until reconstruction.
        LOGGER.error("TME operational projection unavailable; rebuild required")


def operational_status(entry):
    if entry["decided"]:
        return "finalized"
    if entry["audit"] and entry["audit"]["inconclusive"]:
        return "inconclusive"
    # SOURCE_READY is the established started-case bucket of HOME-01/02.
    return "in_progress" if entry["submission_id"] else "pending"


def listing_case(entry):
    audit = entry["audit"] or {}
    return dict(case_id=entry["case_id"], exam_code=entry["exam_code"], problem_id=entry["problem_id"],
                source_mode=entry["source_mode"], operational_status=operational_status(entry),
                updated_at=entry["updated_at"], suggested_score=audit.get("score"),
                max_score=audit.get("max_score"), suggestion_available="score" in audit)


def known_questions(entries):
    groups = {}
    for e in entries:
        items = groups.setdefault(e["exam_code"], {})
        previous = items.get(e["problem_id"])
        if not previous or (e["created_at"], e["case_id"]) > (previous["created_at"], previous["case_id"]):
            items[e["problem_id"]] = e
    return groups


def summarize(entries, period="today", now=None):
    now = now or datetime.now(timezone.utc)
    # Explicit pilot timezone, independent of browser/server OS timezone.
    local = now.astimezone(ZoneInfo("America/Fortaleza"))
    cutoff = None if period == "all" else datetime.combine(
        local.date() - timedelta(days={"today": 0, "7d": 6, "30d": 29}[period]), time.min, local.tzinfo)
    counts = Counts()
    for entry in entries:
        if instant(entry["created_at"]) <= now and (cutoff is None or instant(entry["created_at"]) >= cutoff):
            status = operational_status(entry)
            setattr(counts, status, getattr(counts, status) + 1)
    # Preserve HOME-01/02 policy: source ready first, newest created first.
    # Queue/progress are global; the period only filters the overview cohort.
    ordered = sorted(entries, key=lambda e: (not bool(e["submission_id"]), -instant(e["created_at"]).timestamp(), e["case_id"]))
    priority = []
    for e in ordered:
        if e["decided"]:
            continue
        question = re.search(r"Q\d+$", e["problem_id"])
        priority.append(PriorityCase(**{k: e[k] for k in ("case_id", "exam_code", "problem_id", "source_mode", "updated_at")},
            question_label=question.group() if question else e["problem_id"], operational_status=operational_status(e)))
        if len(priority) == 3:
            break
    groups = known_questions(entries)
    progress = []
    for code, items in groups.items():
        done = sum(e["decided"] for e in items.values())
        progress.append(ExamProgress(exam_code=code, completed_items=done, known_items=len(items),
            percent=round(100 * done / len(items), 2), latest_update=max(instant(e["updated_at"]) for e in items.values())))
    progress.sort(key=lambda e: (-e.latest_update.timestamp(), e.exam_code))
    return HomeSummary(period=period, counts=counts, priority_cases=priority,
                       exam_progress=progress[:2], generated_at=now)


def rebuild_index():
    """Startup/offline migration: one audit-directory pass, no N x audit scans.

    A concurrent publication invalidates this attempt instead of overwriting it.
    Historical source/artifact bytes are only read and validated, never rewritten.
    """
    from confia_lean_auditor.submissions.router import store
    from confia_lean_auditor.submission_audits.router import service
    from confia_lean_auditor.recognition.service import RecognitionService
    from confia_lean_auditor.recognition.registry import RecognizerRegistry

    index, cases, submissions, audits = OperationalIndex(), case_store(), store(), service()
    with index.locked():
        signature = index.path.stat() if index.path.exists() else None
        try:
            generation = index.read()["generation"]
        except (ValueError, KeyError):
            generation = 0  # A corrupt disposable projection can be rebuilt.

    with cases.locked():
        records = [cases.read(p.name) for p in cases.root.iterdir() if re.fullmatch(r"case_[0-9a-f]{32}", p.name)]
    entries, by_submission = {}, {}
    for case in records:
        e = entries[case.case_id] = case_entry(case)
        if case.submission_id:
            record = submissions.get_record(case.submission_id)
            if (record.tme_case_id != case.case_id or record.submitted_by_user_id != case.created_by_user_id
                    or record.problem_id != case.problem_id
                    or record.source != ("tablet" if case.source_mode == "DIGITAL_INK" else "image_scan")):
                raise ValueError("invalid operational binding")
            by_submission[case.submission_id] = e
            touch(e, record.received_at)
            summaries = submissions.list_transcriptions(case.submission_id)
            if summaries:
                latest = max(summaries, key=lambda s: (s.transcription.created_at, s.transcription.transcription_id))
                history = submissions.transcription_history(latest.transcription.transcription_id)
                accepted = next((a.accepted_at for a in history.acceptances if a.revision_number == latest.latest_revision.revision_number), None)
                apply_transcription(e, latest.transcription, latest.latest_revision, accepted)
            runs = RecognitionService(submissions, RecognizerRegistry()).list(case.submission_id)
            if runs:
                apply_recognition(e, max(runs, key=lambda r: (r.provenance.created_at, r.recognizer_run_id)))
        decision = cases.decision(case.case_id, SimpleNamespace(user_id=case.created_by_user_id))
        if decision:
            e["decided"] = True
            touch(e, decision.decided_at)
    if audits.root.is_symlink():
        raise ValueError("invalid audit directory")
    for path in (audits.root.glob("aud_*.json") if by_submission else ()):
        if path.is_symlink():
            raise ValueError("invalid audit file")
        # Select TME records before invoking the existing integrity validator.
        raw = json.loads(path.read_bytes())
        if not isinstance(raw, dict):
            raise ValueError("invalid audit record")
        entry = by_submission.get(raw.get("submission_id"))
        if entry:
            apply_audit(entry, audits._read(path.stem))
    with index.locked():
        if (index.path.stat() if index.path.exists() else None) != signature:
            raise ConcurrentProjectionUpdate("concurrent operational update; retry reconstruction")
        index.write(dict(version=1, generation=generation + 1, complete=True, cases=entries))
        index.dirty.unlink(missing_ok=True)


class ConcurrentProjectionUpdate(ValueError):
    pass


def initialize_index():
    try:
        for attempt in range(3):
            try:
                rebuild_index()
                return
            except ConcurrentProjectionUpdate:
                if attempt == 2:
                    raise
    except (OSError, ValueError, KeyError, TypeError):
        index = OperationalIndex()
        with index.locked():
            fd = os.open(index.dirty, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
            os.close(fd)
        LOGGER.error("TME Home unavailable: operational reconstruction failed")


if __name__ == "__main__":
    rebuild_index()
