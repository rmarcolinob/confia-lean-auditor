"""Product adapter for the existing accepted-source TME engine; no scoring rules.

Only immutable engine output is projected. Text offsets retain engine-input scope;
page navigation is offered only with explicit, unambiguous page provenance.
"""
import os
from confia_lean_auditor.core.public_audit import public_projection
from confia_lean_auditor.submission_audits.schemas import AuditRequest, QuestionAuditContext
from confia_lean_auditor.submission_audits.router import service as audit_service
from confia_lean_auditor.submissions.router import store as submission_store
from .exam_store import exam_store, ExamConflict
from .review_models import QuestionSourceSnapshot


LABELS = {"verified": "Verificado", "supported": "Verificado", "refuted": "Não verificado",
          "indeterminate": "Revisar", "technical_error": "Erro técnico"}


def warnings_for(run):
    return list(dict.fromkeys([w.message for w in getattr(getattr(run, "source", None), "warnings", [])] +
        list(getattr(run.result, "input_warnings", []))))


def review_reasons(run):
    reasons = []
    if run.stale:
        reasons.append("Leitura alterada: esta análise pertence a uma versão anterior.")
    if run.status == "FAILED":
        reasons.append("A análise não foi concluída por uma falha técnica.")
    elif run.result:
        if run.result.score is None:
            reasons.append("O motor não determinou uma pontuação para esta leitura.")
        if run.result.needs_review:
            reasons.append("A pauta registra evidência insuficiente, conflito ou verificação pendente.")
    facts = getattr(getattr(getattr(run.result, "bridge", None), "auditor", None), "facts", [])
    if any(f.verification.status == "technical_error" for f in facts):
        reasons.append("Uma ou mais verificações não puderam concluir por erro técnico.")
    context = getattr(run, "question_context", None)
    if context and run.result and run.result.max_score != context.max_score:
        reasons.append("A pontuação máxima da pauta difere da avaliação cadastrada; confira a configuração.")
    # These are input omission/interpretation warnings, not incidental telemetry.
    reasons.extend(warnings_for(run))
    return list(dict.fromkeys(reasons))


def context_for(case, detail):
    return QuestionAuditContext(assessment_id=detail.submission.assessment_id,
        participant_id=detail.submission.participant_id, exam_submission_id=case.exam_submission_id,
        question_attempt_id=case.case_id, max_score=float(case.max_score))


class CorrectionEngine:
    """TME_CURRENT today. Future modes must implement the same product projection."""
    def audit_question(self, case_id, request: AuditRequest, user):
        from .human_decisions import question_lock
        with question_lock(case_id, user):
            return self._audit_question(case_id, request, user)

    def _audit_question(self, case_id, request: AuditRequest, user):
        from .question_review import workspace
        # Validates ownership, frozen page mapping and source integrity. No engine
        # call occurs until the exact current version has been checked.
        exams = exam_store()
        with exams._locked():
            from .question_review import owned_case
            case = owned_case(case_id, user)
            detail = exams._detail(case.exam_submission_id, user)
            from .finalization import assert_editable
            assert_editable(case.exam_submission_id)
            case = next(c for c in detail.question_attempts if c.case_id == case_id)
            if case.status == "DECIDED" or not case.submission_id:
                raise ExamConflict("question is not available for analysis")
            histories = submission_store().list_transcriptions(case.submission_id)
            if not histories or (histories[0].transcription.transcription_id, histories[0].latest_revision.revision_number) != (request.transcription_id, request.revision_number):
                raise ExamConflict("analyze only the current reading")
            if not request.execution_key:
                raise ValueError("explicit execution key required for question analysis")
            context = context_for(case, detail)
        snapshot = workspace(case_id, user)  # also verifies frozen source against the mapping
        version = f"{request.transcription_id}:{request.revision_number}"
        if not snapshot["current_version"] or snapshot["current_version"]["version_id"] != version:
            raise ExamConflict("reading changed before analysis")
        previous = next((r for r in snapshot["audits"] if r["transcription_version_id"] != version), None)
        service = audit_service()
        # Explicit deployment configuration; never silently disable Lean on error.
        service.tme_use_lean = os.environ.get("CONFIA_TME_QUESTION_USE_LEAN", "1") != "0"
        run = service.execute(case.submission_id, request, question_context=context,
            question_event_builder=lambda run: project_audit(run, case, detail, previous=previous)["events"])
        return project_audit(run, case, detail)


def project_audit(run, case, detail, *, previous=None):
    result = run.result
    context = run.question_context or context_for(case, detail)
    if context.question_attempt_id != case.case_id or context.exam_submission_id != case.exam_submission_id or run.submission_id != case.submission_id:
        raise ExamConflict("audit belongs to another question")
    reasons, warnings = review_reasons(run), warnings_for(run)
    technical = run.status == "FAILED"
    engine_context = run.source.tme_context
    engine_version = run.auditor_version or (engine_context.auditor_version if engine_context else "legacy-unversioned")
    base = dict(schema_version="question-audit.v1", **context.model_dump(exclude={"max_score"}),
        submission_id=case.exam_submission_id, source_submission_id=run.submission_id,
        audit_run_id=run.audit_run_id, problem_id=run.problem_id,
        transcription_id=run.transcription_id, revision_number=run.revision_number,
        transcription_version_id=f"{run.transcription_id}:{run.revision_number}",
        engine_version=engine_version, engine_config={"use_lean": engine_context.use_lean if engine_context else None},
        status=run.status, analysis_status="FAILED" if run.status == "FAILED" else "COMPLETED_WITH_REVIEW" if reasons else "COMPLETED",
        stale=run.stale, suggested_score=result.score if result else None,
        max_score=result.max_score if result else context.max_score,
        review_required=bool(reasons), review_reasons=reasons, warnings=warnings,
        technical_uncertainty=technical, trace_reference=f"audit-run:{run.audit_run_id}",
        started_at=run.created_at.isoformat(), completed_at=run.completed_at.isoformat() if run.completed_at else None,
        rubric_items=[], evidences=[], checker_summary=[], error_code=run.error_code)
    if result:
        base.update(project_result(result, run, case))
        if base["technical_uncertainty"] and not any("técnic" in r for r in reasons):
            reasons.append("Uma ou mais verificações não puderam concluir por erro técnico.")
        base["review_required"] = bool(reasons)
        base["analysis_status"] = "COMPLETED_WITH_REVIEW" if reasons else "COMPLETED"
    # The predecessor snapshot is persisted in the reanalysis event. Re-reading a
    # run must never select a different predecessor after later runs are added.
    prior = next((e for e in run.question_events or [] if e["event_type"] == "question_reanalysis_requested"), None)
    comparison = None
    if previous is not None:
        comparison = dict(previous_audit_run_id=previous["audit_run_id"],
            previous_transcription_version_id=previous["transcription_version_id"],
            previous_suggested_score=previous["suggested_score"], previous_max_score=previous["max_score"],
            previous_completed_at=previous["completed_at"])
    elif prior:
        comparison = {k: prior[k] for k in ("previous_audit_run_id", "previous_transcription_version_id",
            "previous_suggested_score", "previous_max_score", "previous_completed_at")}
    if comparison:
        comparison.update(current_audit_run_id=run.audit_run_id,
            current_transcription_version_id=base["transcription_version_id"],
            current_suggested_score=base["suggested_score"], timestamp=base["completed_at"],
            score_changed=base["suggested_score"] is not None and comparison["previous_suggested_score"] is not None
                and base["suggested_score"] != comparison["previous_suggested_score"])
    base["comparison"] = comparison
    base["events"] = run.question_events if run.question_events is not None else audit_events(base)
    return public_projection(base)


def project_result(result, run, case):
    # TMEAuditResult already owns PautaDecision trees and verified claim/fact links.
    from .accepted_audit import split_accepted_items
    source = QuestionSourceSnapshot.model_validate_json((submission_store()._folder(run.submission_id) / "snapshot.json").read_bytes())
    _, _, locations = split_accepted_items(run.source)
    item_pages = {}
    for location in locations:
        item_pages.setdefault(location["item"], set()).add(location["page_index"])
    evidence, checks = [], []
    for record in result.bridge.auditor.records:
        binding = record.source
        index = getattr(binding, "page_index", None)
        scope = "explicit_page" if index is not None else None
        if index is None:
            indices = set().union(*(item_pages.get(i, set()) for i in record.rubric_links))
            if len(indices) == 1:
                index, scope = next(iter(indices)), "item_page"
        page = source.pages[index] if index is not None and 0 <= index < len(source.pages) else None
        evidence.append(dict(evidence_id=record.record_id, kind=getattr(binding, "kind", "text"),
            text=binding.raw_text, claim_type=record.claim_type,
            source_span=dict(start=binding.source_start, end=binding.source_end, scope="engine_input",
                sha256=binding.source_sha256) if binding.source_start is not None else None,
            exam_page_id=page.page_id if page else None,
            page_number=page.exam_page.page_number if page else None,
            page_reference_scope=scope if page else None,
            # Do not promote diagram-local geometry to coordinates on a whole page.
            region=None, grounding_status=binding.grounding_status))
    for fact in result.bridge.auditor.facts:
        link = fact.verification
        check = fact.student_check or {}
        formal = fact.verification_source == "student_lean"
        message = LABELS.get(link.status, "Revisar")
        if formal and link.status == "verified" and check.get("compiled") and check.get("lean_file"):
            message = "Verificação formal deste passo concluída"
        checks.append(dict(checker_id=link.verification_id, fact_id=fact.fact_id,
            checker_type=fact.verification_source, status=link.status, status_label=message,
            evidence_ids=list(fact.source_claim_ids), trace_reference=link.artifact_ref))
    rules = {}
    def index_rule(rule):
        rules[rule.id] = rule
        for child in rule.children:
            index_rule(child)
    for rule in result.pauta.items:
        index_rule(rule)
    def selected_children(decision):
        selected = decision.selected_method_path or decision.selected_band
        return [c for c in decision.children if not selected or c.item_id == selected]

    def presented_obligations(decision):
        children = selected_children(decision)
        return [o for child in children for o in presented_obligations(child)] if children else list(decision.obligations)

    def decision_view(decision, fallback_label=None):
        obligations = presented_obligations(decision)
        ids = list(dict.fromkeys(i for o in obligations for i in o.source_claim_ids))
        refs = {ref for o in obligations for ref in o.evidence_refs}
        children = selected_children(decision)
        status = "technical_error" if decision.status == "technical_error" else "indeterminate" if decision.needs_review else "supported" if decision.fully_satisfied else "refuted"
        return dict(rubric_item_id=decision.item_id, label=rules[decision.item_id].description or fallback_label or f"Item ({decision.item_id})",
            max_points=float(decision.max_points), suggested_points=float(decision.points_awarded) if decision.points_awarded is not None else None,
            status=decision.status, display_status=status, status_label=LABELS[status], review_required=decision.needs_review,
            reason=decision.reason, evidence_ids=ids,
            checker_ids=[c["checker_id"] for c in checks if c["trace_reference"] in refs],
            evidence_references=list(decision.evidence_refs), known_points=float(decision.known_points), possible_points=float(decision.possible_points),
            carry_forward_applied=decision.carry_forward_applied,
            children=[decision_view(c, f"Etapa {i + 1}") for i, c in enumerate(children)])
    return dict(rubric_items=[decision_view(d) for d in result.assessment.items], evidences=evidence,
        checker_summary=checks, technical_uncertainty=any(c["status"] == "technical_error" for c in checks)
            or any(d.status == "technical_error" for d in result.assessment.items))


def audit_events(data):
    common = {key: data[key] for key in ("assessment_id", "participant_id", "submission_id", "question_attempt_id",
        "transcription_version_id", "audit_run_id", "engine_version")}
    events = []
    def add(kind, suffix="", **fields):
        events.append(dict(**common, event_id=f'{data["audit_run_id"]}:{kind}:{suffix}', event_type=kind,
            timestamp=data["started_at"] if kind in {"audit_started", "question_reanalysis_requested"} else data["completed_at"], **fields))
    comparison = data.get("comparison")
    if comparison:
        common["previous_audit_run_id"] = comparison["previous_audit_run_id"]
        add("question_reanalysis_requested", **{k: v for k, v in comparison.items() if k.startswith("previous_") and k != "previous_audit_run_id"})
    add("audit_started")
    add("audit_failed" if data["status"] == "FAILED" else "audit_completed", status=data["status"])
    if comparison and comparison["score_changed"] and data["status"] == "COMPLETED":
        add("suggested_score_changed", old_score=comparison["previous_suggested_score"], new_score=data["suggested_score"])
    def item_events(item):
        add("rubric_item_decided", item["rubric_item_id"], rubric_item_id=item["rubric_item_id"],
            status=item["status"], suggested_points=item["suggested_points"])
        for child in item["children"]:
            item_events(child)
    for item in data["rubric_items"]:
        item_events(item)
    for check in data["checker_summary"]:
        add("checker_result_recorded", check["checker_id"], checker_type=check["checker_type"], status=check["status"], checker_id=check["checker_id"])
    # Staleness is a later reading event, not a retroactive completion event.
    nonstale_reasons = [r for r in data["review_reasons"] if not r.startswith("Leitura alterada:")]
    if nonstale_reasons:
        add("review_required", reasons=nonstale_reasons)
    return events
