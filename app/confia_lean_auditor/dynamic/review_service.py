"""Associated immutable DY4 records; shared audit locks, integrity and atomic publication."""

import json
from datetime import datetime, timezone
from .review_models import DynamicIndependentReview, VERSION
from .reviewer import IndependentDynamicReviewer, blind_input
from .review_comparison import compare_review
from .review_provider import OpenAIIndependentReviewProvider
from .provider import ProviderFailure
from .grading_context import case_context
from .store import DynamicConflict
from confia_lean_auditor.submissions.integrity import model_sha256, canonical_sha256
from confia_lean_auditor.submissions.store import SubmissionStore
from confia_lean_auditor.submission_audits.artifacts import controlled_file


def now():
    return datetime.now(timezone.utc)


class DynamicReviewService:
    def __init__(self, audits, provider=None, semantic_provider=None):
        self.semantic_provider = semantic_provider
        self.audits = audits
        self.provider = provider or OpenAIIndependentReviewProvider()
        self.root = audits.root / "independent_reviews"

    def audit_for(self, case, run_id, current=False):
        run = self.audits._read(run_id)
        if (
            not case.dynamic_context
            or run.source.dynamic_context != case.dynamic_context
            or run.submission_id != case.submission_id
            or run.status != "COMPLETED"
        ):
            raise DynamicConflict(
                "Revisão exige uma auditoria Dynamic desta tentativa."
            )
        if current and self.audits.view(run).stale:
            raise DynamicConflict(
                "Fonte ou configuração mudou; analise a versão atual antes de revisar."
            )
        return run

    def identity(self, case, run, key):
        return "drev_" + canonical_sha256(
            dict(case=case.case_id, run=model_sha256(run), key=key, reviewer=VERSION)
        )

    def load_record(self, path):
        try:
            raw = json.loads(controlled_file(self.root, str(path)).read_bytes())
            record = DynamicIndependentReview.model_validate(raw["record"])
            if raw.get("sha256") != model_sha256(record):
                raise ValueError("digest mismatch")
            return raw, record
        except (ValueError, KeyError, TypeError, OSError):
            raise DynamicConflict(
                "Integridade da revisão independente inválida."
            ) from None

    def read(self, path, case, run):
        raw, record = self.load_record(path)
        if (
            raw.get("sha256") != model_sha256(record)
            or path.stem != record.review_id
            or record.review_id != self.identity(case, run, record.execution_key)
            or record.audit_run_sha256 != model_sha256(run)
            or record.audit_result_sha256 != run.result_sha256
            or record.source_sha256 != run.source_hash
            or record.context != run.source.dynamic_context
            or record.question_attempt_id != case.case_id
            or record.audit_run_id != run.audit_run_id
            or record.transcription_version_id
            != f"{run.transcription_id}:{run.revision_number}"
        ):
            raise DynamicConflict("Integridade da revisão independente inválida.")
        if (
            record.phase_a_input.get("solution") != run.source.solution_text
            or record.phase_a_input.get("source_sha256") != run.source_hash
        ):
            raise DynamicConflict("Fonte da revisão independente divergente.")
        if record.phase_a and record.phase_a.input_sha256 != canonical_sha256(
            record.phase_a_input
        ):
            raise DynamicConflict("Entrada independente alterada.")
        return record

    def envelope(self, record, run):
        stale = self.audits.view(run).stale
        return dict(
            grader_audit_run_id=run.audit_run_id,
            review=record.model_dump(mode="json"),
            stale=stale,
            review_required=stale or record.review_required,
            reconciliation=None,
        )

    def list(self, case, run_id):
        run = self.audit_for(case, run_id)
        if self.root.is_symlink():
            raise DynamicConflict("Diretório de revisões inválido.")
        rows = []
        for path in self.root.glob("drev_*.json"):
            # Read only this run's associated records, without hiding corrupt records.
            raw, _ = self.load_record(path)
            if raw.get("record", {}).get("audit_run_id") == run_id:
                rows.append(self.read(path, case, run))
        return [
            self.envelope(r, run)
            for r in sorted(rows, key=lambda r: r.completed_at, reverse=True)
        ]

    def execute(self, case, run_id, key):
        with self.audits.submissions._locked():
            self.audits.submissions.assert_tme_editable(case.submission_id)
        run = self.audit_for(case, run_id, current=True)
        context, statement, rubric, preparation = case_context(case)
        review_id = self.identity(case, run, key)
        with self.audits._request_lock(review_id):
            if self.root.is_symlink():
                raise DynamicConflict("Diretório de revisões inválido.")
            self.root.mkdir(parents=True, exist_ok=True)
            if any(p.is_symlink() for p in [self.root, *self.root.parents]):
                raise DynamicConflict("Caminho de revisão inválido.")
            path = self.root / (review_id + ".json")
            if path.exists() or path.is_symlink():
                return self.envelope(self.read(path, case, run), run)
            started = now()
            payload, equation, claims = blind_input(
                run.source, statement, rubric, preparation, context
            )
            events = [
                dict(
                    event_type="independent_review_started",
                    timestamp=started.isoformat(),
                )
            ]
            phase = None
            comparison = None
            error = None
            failure_provenance = None
            try:
                from .semantic import enabled, review_phase
                phase = (review_phase(payload, rubric, self.semantic_provider) if enabled(context) else
                    IndependentDynamicReviewer(self.provider).analyze(payload, equation, claims, rubric))
                # Only now can the comparison inspect DY3 judgments/score.
                comparison = compare_review(
                    run.result, phase, rubric, run.source.solution_text
                )
                for claim in phase.additional_claims:
                    events.append(
                        dict(event_type="reviewer_claim_added", claim_id=claim.claim_id)
                    )
                for item in comparison.criteria:
                    events.append(
                        dict(
                            event_type=(
                                "grader_reviewer_agreement"
                                if item.agreement == "AGREEMENT"
                                else (
                                    "grader_reviewer_disagreement"
                                    if item.agreement == "DISAGREEMENT"
                                    else "independent_review_uncertain"
                                )
                            ),
                            criterion_id=item.criterion_id,
                            agreement=item.agreement,
                        )
                    )
                    for kind, event in [
                        ("FALSE_CREDIT_SUSPECTED", "possible_false_credit_detected"),
                        ("MISSED_CREDIT_SUSPECTED", "possible_missed_credit_detected"),
                    ]:
                        if kind in item.disagreement_types:
                            events.append(
                                dict(event_type=event, criterion_id=item.criterion_id)
                            )
            except ProviderFailure as exc:
                error = exc.code
                failure_provenance = (
                    exc.provenance.model_dump(mode="json") if exc.provenance else None
                )
                phase = None
                comparison = None
            except (ValueError, TypeError):
                error = "REVIEWER_INVALID_OUTPUT"
                phase = None
                comparison = None
            except Exception:
                error = "REVIEWER_TECHNICAL_ERROR"
                phase = None
                comparison = None
            completed = now()
            events.append(
                dict(
                    event_type="independent_review_completed",
                    status="FAILED" if error else "COMPLETED",
                )
            )
            for i, event in enumerate(events):
                event.update(
                    event_id=canonical_sha256(
                        dict(review=review_id, index=i, event=event)
                    ),
                    review_id=review_id,
                    audit_run_id=run_id,
                    question_attempt_id=case.case_id,
                    transcription_version_id=f"{run.transcription_id}:{run.revision_number}",
                    timestamp=event.get("timestamp", completed.isoformat()),
                )
            record = DynamicIndependentReview(
                review_id=review_id,
                audit_run_id=run_id,
                audit_run_sha256=model_sha256(run),
                audit_result_sha256=run.result_sha256,
                source_sha256=run.source_hash,
                question_attempt_id=case.case_id,
                transcription_version_id=f"{run.transcription_id}:{run.revision_number}",
                context=context,
                execution_key=key,
                started_at=started,
                completed_at=completed,
                status="FAILED" if error else "COMPLETED",
                phase_a=phase,
                comparison=comparison,
                phase_a_input=payload,
                context_snapshot=dict(
                    phase_a_input_sha256=canonical_sha256(payload),
                    provider_adapter=type(self.provider).__name__,
                    failed_generation=failure_provenance,
                    statement=statement.model_dump(mode="json"),
                    rubric=rubric.model_dump(mode="json"),
                    preparation=preparation.model_dump(mode="json"),
                ),
                review_required=True if error else comparison.review_required,
                error_code=error,
                events=events,
            )
            # Optimistic publication: accepted transcription, original run and approval must still match.
            latest = self.audit_for(case, run_id, current=True)
            if (
                model_sha256(latest) != record.audit_run_sha256
                or case_context(case)[0] != context
            ):
                raise DynamicConflict(
                    "Contexto mudou durante a revisão; resultado não publicado."
                )
            with self.audits.submissions._locked(exclusive=True):
                self.audits.submissions.assert_tme_editable(case.submission_id)
                from .reconciliation_service import ReconciliationService
                ReconciliationService(self.audits).assert_source_current_unlocked(case,run)
                SubmissionStore._write_atomic_new(
                    path,
                    json.dumps(
                        dict(
                            record=record.model_dump(mode="json"),
                            sha256=model_sha256(record),
                        ),
                        ensure_ascii=False,
                        indent=2,
                    ).encode(),
                )
            return self.envelope(record, run)
