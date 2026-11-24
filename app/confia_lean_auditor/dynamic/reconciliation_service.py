"""Immutable associated reconciliations and explicit Assessment policy binding."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
import json
from .reconciliation_models import DynamicReconciliation, POLICY_VERSION, VERSION
from .reconciliation import reconcile_criteria
from .review_service import DynamicReviewService
from .store import DynamicConflict
from .grading_context import case_context
from confia_lean_auditor.submissions.integrity import canonical_sha256, model_sha256
from confia_lean_auditor.submissions.store import SubmissionStore
from confia_lean_auditor.submission_audits.artifacts import controlled_file


def sealed_write(path, data):
    SubmissionStore._write_atomic_new(
        path,
        json.dumps(
            {"data": data, "sha256": canonical_sha256(data)},
            ensure_ascii=False,
            indent=2,
        ).encode(),
    )


def sealed_read(root, path):
    try:
        raw = json.loads(controlled_file(root, str(path)).read_bytes())
        if not isinstance(raw["data"], dict) or raw["sha256"] != canonical_sha256(
            raw["data"]
        ):
            raise ValueError()
        return raw["data"]
    except (OSError, ValueError, KeyError, TypeError):
        raise DynamicConflict("Integridade do artefato Dynamic inválida.") from None


def activity(case):
    if case.exam_submission_id:
        from .assessment_service import pinned_activity
        return pinned_activity(case)
    from confia_lean_auditor.tme.store import case_store
    from confia_lean_auditor.assessments.store import assessment_store

    folder = case_store().folder(case.case_id)
    path = folder / "dynamic_activity.json"
    if not path.exists():
        return None
    binding = sealed_read(folder, path)
    document = assessment_store().get(binding.get("assessment_id"))
    a = document.assessment
    if (
        binding.get("case_id") != case.case_id
        or a.teacher_user_id != case.created_by_user_id
        or a.definition_sha256 != binding.get("assessment_definition_sha256")
        or len(document.items) != 1
        or document.items[0].problem_id != case.problem_id
        or a.dynamic_policy_profile != binding.get("policy_profile")
        or a.dynamic_policy_version != POLICY_VERSION
    ):
        raise DynamicConflict("Atividade/política divergente.")
    return binding


def configure_activity(case, profile):
    from confia_lean_auditor.assessments.store import assessment_store
    from confia_lean_auditor.assessments.models import CreateAssessmentItem
    from confia_lean_auditor.tme.store import case_store

    old = activity(case)
    if old:
        if old["policy_profile"] != profile:
            raise DynamicConflict(
                "Perfil publicado é imutável; crie outra atividade para mudar a política."
            )
        return old
    _, statement, rubric, _ = case_context(case)
    now = datetime.now(timezone.utc)
    document = assessment_store().create_tme(
        title=statement.title or "Atividade Dynamic",
        instructions="",
        teacher_user_id=case.created_by_user_id,
        academic_year=now.year,
        opens_at=now,
        closes_at=now + timedelta(days=365),
        items=[
            CreateAssessmentItem(
                problem_id=case.problem_id, points=float(rubric.max_score)
            )
        ],
        dynamic_policy_profile=profile,
        dynamic_policy_version=POLICY_VERSION,
    )
    a = document.assessment
    binding = dict(
        case_id=case.case_id,
        assessment_id=a.assessment_id,
        assessment_definition_sha256=a.definition_sha256,
        policy_profile=profile,
        policy_version=POLICY_VERSION,
        configured_at=now.isoformat(),
    )
    sealed_write(case_store().folder(case.case_id) / "dynamic_activity.json", binding)
    from .human_decisions import project_current

    project_current(case)
    return binding


class ReconciliationService:
    def __init__(self, audits):
        self.audits = audits
        self.reviews = DynamicReviewService(audits)
        self.root = audits.root / "reconciliations"

    def current_run(self, case):
        return next(iter(self.audits.list(case.submission_id)), None)

    def assert_current(self, case, run):
        current = self.current_run(case)
        if not current or current.audit_run_id != run.audit_run_id or current.stale:
            raise DynamicConflict(
                "Nova análise ou transcrição exige nova revisão e reconciliação."
            )

    def review(self, case, run, review_id):
        return self.reviews.read(self.reviews.root / (review_id + ".json"), case, run)

    def read(self, path, case, run):
        raw = sealed_read(self.root, path)
        try:
            record = DynamicReconciliation.model_validate(raw)
        except ValueError:
            raise DynamicConflict("Reconciliação inválida.") from None
        review = self.review(case, run, record.independent_review_id)
        binding = activity(case)
        if (
            path.stem != record.reconciliation_id
            or record.question_attempt_id != case.case_id
            or record.grader_audit_run_id != run.audit_run_id
            or record.context != run.source.dynamic_context
            or record.transcription_version_id
            != f"{run.transcription_id}:{run.revision_number}"
            or record.provenance.get("audit_sha256") != model_sha256(run)
            or record.provenance.get("review_sha256") != model_sha256(review)
            or not binding
            or record.assessment_definition_sha256
            != binding.get("assessment_definition_sha256")
            or record.assessment_id != binding.get("assessment_id")
            or record.policy_profile != binding.get("policy_profile")
        ):
            raise DynamicConflict("Vínculos da reconciliação inválidos.")
        expected = "drec_" + canonical_sha256(
            dict(
                audit=model_sha256(run),
                review=model_sha256(review),
                activity=binding,
                policy=POLICY_VERSION,
                version=VERSION,
            )
        )
        if expected != record.reconciliation_id:
            raise DynamicConflict("Identidade da reconciliação inválida.")
        return record

    def list(self, case, run_id):
        run = self.reviews.audit_for(case, run_id)
        if self.root.is_symlink():
            raise DynamicConflict("Diretório inválido.")
        rows = []
        for path in self.root.glob("drec_*.json"):
            data = sealed_read(self.root, path)
            if data.get("grader_audit_run_id") == run_id:
                rows.append(self.read(path, case, run))
        current = self.current_run(case)
        reviews = self.reviews.list(case, run_id)
        latest = reviews[0]["review"]["review_id"] if reviews else None
        return [
            dict(
                reconciliation=r.model_dump(mode="json"),
                stale=bool(
                    not current
                    or current.audit_run_id != run_id
                    or current.stale
                    or r.independent_review_id != latest
                ),
            )
            for r in sorted(rows, key=lambda r: r.completed_at, reverse=True)
        ]

    def current(self, case, run_id):
        return next(
            (r["reconciliation"] for r in self.list(case, run_id) if not r["stale"]),
            None,
        )

    def execute(self, case, run_id, review_id):
        run = self.reviews.audit_for(case, run_id, current=True)
        self.assert_current(case, run)
        review = self.review(case, run, review_id)
        views = self.reviews.list(case, run_id)
        if not views or views[0]["review"]["review_id"] != review_id:
            raise DynamicConflict("Selecione a revisão independente corrente.")
        binding = activity(case)
        if not binding:
            raise DynamicConflict(
                "Configure explicitamente o perfil da atividade antes de reconciliar."
            )
        context, statement, rubric, prep = case_context(case)
        identifier = "drec_" + canonical_sha256(
            dict(
                audit=model_sha256(run),
                review=model_sha256(review),
                activity=binding,
                policy=POLICY_VERSION,
                version=VERSION,
            )
        )
        if any(p.is_symlink() for p in [self.root, *self.root.parents]):
            raise DynamicConflict("Caminho inválido.")
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / (identifier + ".json")
        if path.exists():
            return dict(
                reconciliation=self.read(path, case, run).model_dump(mode="json"),
                stale=False,
            )
        started = datetime.now(timezone.utc)
        criteria = reconcile_criteria(
            run.result,
            review,
            statement,
            rubric,
            run.source.solution_text,
            binding.get("policy_profile"),
        )
        reasons = [
            f"{c.criterion_id}: {c.reason}" for c in criteria if c.review_required
        ]
        if prep.status == "REVIEW_REQUIRED":
            reasons.append("Preparação mantém revisão docente pendente.")
        if review.phase_a and review.phase_a.warnings:
            reasons.extend(review.phase_a.warnings)
        total = sum((c.reconciled_points for c in criteria), Decimal(0))
        old = (Decimal(str(run.result.score)) if run.result.score is not None else
               sum((d.suggested_points for d in run.result.decisions), Decimal(0)))
        from .semantic import enabled
        if enabled(context) and any(c.status in {'REVIEW_REQUIRED', 'TECHNICAL_ERROR'} for c in criteria):
            total = None
        completed = datetime.now(timezone.utc)
        events = [
            dict(
                event_type="dynamic_reconciliation_started",
                timestamp=started.isoformat(),
            )
        ]
        mapping = {
            "AUTO_ACCEPT": "criterion_auto_accepted",
            "AUTO_ADJUST_UP": "criterion_auto_adjusted_up",
            "AUTO_ADJUST_DOWN": "criterion_auto_adjusted_down",
            "REVIEW_ONLY": "criterion_review_only",
        }
        events.extend(
            dict(
                event_type=mapping[c.automation],
                criterion_id=c.criterion_id,
                old_points=str(c.grader_points),
                new_points=str(c.reconciled_points),
                reason=c.reason,
            )
            for c in criteria
        )
        if total is not None and total != old:
            events.append(
                dict(
                    event_type="reconciled_score_changed",
                    old_score=str(old),
                    new_score=str(total),
                )
            )
        if reasons:
            events.append(
                dict(event_type="reconciliation_review_required", reasons=reasons)
            )
        events.append(dict(event_type="dynamic_reconciliation_completed"))
        for i, event in enumerate(events):
            event.update(
                event_id=canonical_sha256(dict(reconciliation=identifier, index=i)),
                reconciliation_id=identifier,
                grader_audit_run_id=run_id,
                independent_review_id=review_id,
                question_attempt_id=case.case_id,
                timestamp=event.get("timestamp", completed.isoformat()),
            )
        reviewer_points = [c.reviewer_points for c in criteria]
        record = DynamicReconciliation(
            reconciliation_id=identifier,
            grader_audit_run_id=run_id,
            independent_review_id=review_id,
            question_attempt_id=case.case_id,
            transcription_version_id=f"{run.transcription_id}:{run.revision_number}",
            context=context,
            assessment_id=binding.get("assessment_id"),
            assessment_definition_sha256=binding.get("assessment_definition_sha256"),
            policy_profile=binding.get("policy_profile"),
            grader_score_snapshot=old,
            reviewer_score_snapshot=(
                sum(reviewer_points)
                if all(v is not None for v in reviewer_points)
                else None
            ),
            reconciled_suggested_score=total,
            max_score=rubric.max_score,
            criteria=criteria,
            review_required=bool(reasons),
            review_reasons=list(dict.fromkeys(reasons)),
            technical_uncertainty=any(c.technical_uncertainty for c in criteria),
            started_at=started,
            completed_at=completed,
            events=events,
            provenance=dict(
                audit_sha256=model_sha256(run),
                review_sha256=model_sha256(review),
                source_sha256=run.source_hash,
                rubric_sha256=model_sha256(rubric),
                statement_sha256=model_sha256(statement),
                preparation_sha256=model_sha256(prep),
                authority=("approved rubric + literal source evidence + blind semantic review; human confirmation, not formal certification"
                           if enabled(context) else "source spans + exact local checks + approved obligations; never opinion consensus"),
                code_content_sha256=canonical_sha256(
                    {
                        p.name: p.read_text()
                        for p in sorted(Path(__file__).parent.glob("*.py"))
                    }
                ),
            ),
        )
        self.assert_current(case, run)
        if case_context(case)[0] != context or activity(case) != binding:
            raise DynamicConflict("Configuração mudou durante reconciliação.")
        # Publication shares the submissions lock with generic audit/transcription writers.
        with self.audits.submissions._locked(exclusive=True):
            self.assert_source_current_unlocked(case, run)
            sealed_write(path, record.model_dump(mode="json"))
        return dict(reconciliation=record.model_dump(mode="json"), stale=False)

    def assert_source_current_unlocked(self, case, run):
        store = self.audits.submissions
        store.assert_tme_editable(case.submission_id)
        folder = store._transcriptions_folder(case.submission_id)
        histories = [
            store._history_from_folder(p)
            for p in folder.iterdir()
            if p.is_dir()
            and not p.is_symlink()
            and store._transcription_name_valid(p.name)
        ]
        latest = max(histories, key=lambda h: h.transcription.created_at)
        runs = [self.audits._read(p.stem) for p in self.audits.root.glob("aud_*.json")]
        newest = max(
            (r for r in runs if r.submission_id == case.submission_id),
            key=lambda r: r.created_at,
        )
        if (
            latest.transcription.transcription_id != run.transcription_id
            or latest.revisions[-1].revision_number != run.revision_number
            or newest.audit_run_id != run.audit_run_id
        ):
            raise DynamicConflict("Fonte/análise mudou antes da publicação.")
