"""Traceable Dynamic extension of the shared evaluator decision contract.

The original AuditRun is always the grader. The selected suggestion is explicitly
identified by reconciliation_id; no derived AuditRun pretends to be a new grader.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from .reconciliation_service import (
    ReconciliationService,
    activity,
    sealed_read,
    sealed_write,
)
from .store import DynamicConflict
from .grading_context import case_context
from confia_lean_auditor.submissions.integrity import canonical_sha256
from confia_lean_auditor.tme.models import EvaluatorDecision
from confia_lean_auditor.tme.human_decisions import question_lock
from confia_lean_auditor.tme.store import case_store
from confia_lean_auditor.submission_audits.router import service


def records(case):
    folder = case_store().folder(case.case_id) / "dynamic_human_decisions"
    if folder.is_symlink():
        raise DynamicConflict("Histórico de decisões inválido.")
    rows = []
    previous = None
    for i, path in enumerate(sorted(folder.glob("*.json")), 1):
        raw = sealed_read(folder, path)
        if (
            path.name != f"{i:06d}.json"
            or raw.get("sequence") != i
            or raw.get("previous_sha256") != previous
        ):
            raise DynamicConflict("Cadeia de decisões inválida.")
        try:
            d = EvaluatorDecision.model_validate(raw.get("decision"))
        except ValueError:
            raise DynamicConflict("Decisão inválida.") from None
        if (
            d.case_id != case.case_id
            or not d.reconciliation_id
            or not d.human_decision_id
        ):
            raise DynamicConflict("Decisão fora da tentativa.")
        rows.append(raw)
        previous = canonical_sha256(raw)
    return rows


def history(case):
    rows = records(case)
    result = []
    s = ReconciliationService(service())
    run = s.current_run(case) if case.submission_id else None
    reconciliation = (
        s.current(case, run.audit_run_id) if run and run.status == "COMPLETED" else None
    )
    for i, row in enumerate(rows):
        d = EvaluatorDecision.model_validate(row["decision"])
        active = bool(
            i == len(rows) - 1
            and run
            and not run.stale
            and reconciliation
            and d.audit_run_id == run.audit_run_id
            and d.reconciliation_id == reconciliation["reconciliation_id"]
        )
        if active and d.reconciliation_sha256 != canonical_sha256(reconciliation):
            raise DynamicConflict("Snapshot da sugestão alterado.")
        reason = (
            None
            if active
            else (
                "SUPERSEDED"
                if i < len(rows) - 1
                else (
                    "INVALIDATED_BY_NEW_AUDIT"
                    if run and d.audit_run_id != run.audit_run_id
                    else (
                        "INVALIDATED_BY_TRANSCRIPTION_OR_CONTEXT"
                        if not run or run.stale
                        else "INVALIDATED_BY_NEW_REVIEW"
                    )
                )
            )
        )
        result.append(
            dict(
                decision=d.model_dump(mode="json"),
                current=active,
                effective_status="CONFIRMED" if active else reason,
            )
        )
    return list(reversed(result))


def current(case):
    rows = history(case)
    found = next((r["decision"] for r in rows if r["current"]), None)
    if found:
        return EvaluatorDecision.model_validate(found)
    # DY3 decisions keep their old shape/history; never masquerade as reconciled.
    path = case_store().folder(case.case_id) / "decision.json"
    if not rows and path.exists():
        from confia_lean_auditor.submission_audits.artifacts import controlled_file

        legacy = EvaluatorDecision.model_validate_json(
            controlled_file(path.parent, str(path)).read_bytes()
        )
        if not activity(case):
            run = ReconciliationService(service()).current_run(case)
            if run and not run.stale and run.audit_run_id == legacy.audit_run_id:
                return legacy
    return None


def decide(case, body, user):
    with question_lock(case.case_id, user):
        s = ReconciliationService(service())
        if not body.audit_run_id or not body.reconciliation_id:
            raise DynamicConflict(
                "Selecione a reconciliação corrente antes de confirmar."
            )
        run = s.reviews.audit_for(case, body.audit_run_id, current=True)
        s.assert_current(case, run)
        reconciliation = s.current(case, run.audit_run_id)
        if (
            not reconciliation
            or reconciliation["reconciliation_id"] != body.reconciliation_id
        ):
            raise DynamicConflict("Sugestão mudou; confira a reconciliação corrente.")
        max_points = Decimal(reconciliation["max_score"])
        suggestion = Decimal(reconciliation["reconciled_suggested_score"])
        if body.max_points != max_points or body.final_points > max_points:
            raise ValueError("invalid maximum/final score")
        if body.final_points != suggestion and not (body.override_reason or "").strip():
            raise ValueError("override reason required")
        chain = records(case)
        previous = current(case)
        request_sha = canonical_sha256(body.model_dump(mode="json"))
        if previous:
            if chain and chain[-1]["request_sha256"] == request_sha:
                return previous
            raise DynamicConflict(
                "Confirmação corrente já registrada. Uma nova análise/revisão exige nova confirmação."
            )
        d = EvaluatorDecision(
            **body.model_dump(),
            case_id=case.case_id,
            decided_by_user_id=user.user_id,
            decided_at=datetime.now(timezone.utc),
            audit_source_sha256=run.source_hash,
            audit_result_sha256=run.result_sha256,
            suggested_points=suggestion,
            grader_suggested_points=Decimal(reconciliation["grader_score_snapshot"]),
            independent_review_id=reconciliation["independent_review_id"],
            transcription_version_id=reconciliation["transcription_version_id"],
            reconciliation_sha256=canonical_sha256(reconciliation),
            review_required_snapshot=reconciliation["review_required"],
            review_reasons_snapshot=reconciliation["review_reasons"],
            human_decision_id="hdec_" + uuid4().hex,
        )
        folder = case_store().folder(case.case_id) / "dynamic_human_decisions"
        if folder.is_symlink():
            raise DynamicConflict("Diretório inválido.")
        folder.mkdir(exist_ok=True)
        record = dict(
            sequence=len(chain) + 1,
            previous_sha256=canonical_sha256(chain[-1]) if chain else None,
            request_sha256=request_sha,
            decision=d.model_dump(mode="json"),
        )
        if case_context(case)[0] != run.source.dynamic_context:
            raise DynamicConflict("Configuração mudou.")
        with s.audits.submissions._locked(exclusive=True):
            s.assert_source_current_unlocked(case, run)
            sealed_write(folder / f"{len(chain)+1:06d}.json", record)
        project_current(case, reconciliation, confirmed=True)
        return d


def project_current(case, reconciliation=None, confirmed=False):
    """Disposable Home projection only; no authorization or scoring reads it."""
    if case.exam_submission_id: return
    from confia_lean_auditor.tme.home_summary import _publish

    def update(entries):
        e = entries[case.case_id]
        e["dynamic"] = True
        e["decided"] = confirmed
        a = e.get("audit")
        if a:
            a.setdefault("grader_score", a["score"])
            a["score"] = (
                float(reconciliation["reconciled_suggested_score"])
                if reconciliation
                else a["grader_score"]
            )
            a["inconclusive"] = (
                reconciliation["review_required"] if reconciliation else True
            )
        e["updated_at"] = datetime.now(timezone.utc).isoformat()

    _publish(update)
