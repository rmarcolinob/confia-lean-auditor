"""Read-only explanation of persisted Pauta decisions, never a second scorer.

Intervals describe uncertainty under the saved pauta, not independent proof of
the student's mathematics. Relevance is per rule occurrence: the same obligation
can be dispensable in one path and necessary in another. Decimal point values
are exposed as strings, exactly as in the underlying PautaAssessment.

Human confirmation history lives outside AuditRun. An explicit question_context
identifies the exam workflow, whose current finalization rule requires human
confirmation. Otherwise the requirement is UNKNOWN, even when needs_review is
false. Confirmation status itself is always unknown from AuditRun alone. This
projection never authorizes finalization or replaces that workflow.
"""
from confia_lean_auditor.rubric.pauta.models import PautaAssessment, PautaConfig
from confia_lean_auditor.semantic_policy.tme import policy_for
from confia_lean_auditor.submissions.integrity import model_sha256
from .audit_models import TMEAuditResult

VERSION = "tme-review-diagnostics.v1"
PENDING = {"indeterminate", "technical_error"}


def _empty(reason):
    return dict(
        schema_version=VERSION, scope="persisted_pauta_decisions",
        score_state="unknown", final_score=None, known_points=None,
        possible_points=None, max_score=None, reason=reason, items=[],
        mathematical_pending=dict(state="unknown", obligation_ids=[], occurrences=[]),
        nonblocking_pending=[], dispensable_alternatives=[], technical_errors=[],
        semantic_evidence_review=dict(state="unknown", occurrences=[]),
        human_review=dict(state="unknown", required=None,
                          confirmation_state="unknown", rule_id=None, scope="audit_record",
                          reason="NO_EXPLICIT_HUMAN_REVIEW_RULE_IN_AUDIT"),
    )


def _check_tree(rule, decision):
    if ((rule.id, rule.scoring_strategy, rule.max_points)
            != (decision.item_id, decision.scoring_strategy, decision.max_points)
            or len(rule.children) != len(decision.children)):
        raise ValueError("Decision tree does not match saved pauta")
    if not rule.children:
        expected = rule.carry_forward.obligation_ids() if rule.carry_forward else rule.obligation_ids
        if tuple(o.obligation_id for o in decision.obligations) != expected:
            raise ValueError("Missing or mismatched obligation decisions")
    for child, observed in zip(rule.children, decision.children):
        _check_tree(child, observed)


def project_pauta(config: PautaConfig, assessment: PautaAssessment, *, semantic_policy=None):
    """Classify saved intervals and paths without invoking PautaEngine.evaluate.

    'present' mathematical pending means an unresolved occurrence can affect the
    recorded score interval. It does not promise eligibility for GPT. Technical
    failures keep their status even when their path cannot improve the score.
    """
    try:
        config = PautaConfig.model_validate(config.model_dump())
        assessment = PautaAssessment.model_validate(assessment.model_dump())
        policy = policy_for(semantic_policy)
        if (model_sha256(config) != assessment.config_sha256
                or config.problem_id != assessment.problem_id
                or len(config.items) != len(assessment.items)):
            raise ValueError("Unbound pauta")
        for rule, decision in zip(config.items, assessment.items):
            _check_tree(rule, decision)
    except ValueError:
        return _empty("UNSUPPORTED_OR_INCONSISTENT_SAVED_DECISIONS")

    result = _empty("SAVED_SCORING_INTERVAL")
    pending, nonblocking, semantic, errors = [], [], [], []

    def visit(rule, decision, path, excluded=None, alternative=False):
        selected = decision.selected_method_path or decision.selected_band
        for child_rule, child in zip(rule.children, decision.children):
            reason, unused = excluded, alternative
            if rule.scoring_strategy in {"max_of", "banded"}:
                if child.item_id != selected and child.possible_points <= decision.known_points:
                    reason = reason or "ALTERNATIVE_CANNOT_IMPROVE_SCORE"
                    unused = True
            elif (decision.status == "decided" and child.status != "decided"):
                # An additive cap can close the parent despite an open child.
                reason = reason or "ADDITIVE_CAP_REACHED"
            visit(child_rule, child, (*path, child.item_id), reason, unused)
        if rule.children:
            return

        records = {o.obligation_id: o for o in decision.obligations}
        reason = excluded
        if (rule.carry_forward and
                records[rule.carry_forward.prior_obligation_id].effective_status == "supported"):
            reason = "CARRY_FORWARD_INAPPLICABLE_PRIOR_SUPPORTED"
        elif decision.status == "decided":
            if rule.scoring_strategy == "any_of" and any(
                    o.effective_status == "supported" for o in decision.obligations):
                reason = reason or "SATISFIED_DISJUNCTION"
                alternative = True
            elif rule.scoring_strategy == "all_of" and any(
                    o.effective_status == "refuted" for o in decision.obligations):
                reason = reason or "REFUTED_CONJUNCTION"
            else:
                reason = reason or "RULE_INTERVAL_CLOSED"

        for obligation in decision.obligations:
            unresolved = obligation.effective_status in PENDING
            occurrence = dict(
                item_id=path[0], rule_path=list(path), obligation_id=obligation.obligation_id,
                effective_status=obligation.effective_status, origin=obligation.origin,
                evidence_refs=list(obligation.evidence_refs),
                affects_score=unresolved and reason is None,
                dispensable_alternative=unresolved and alternative,
                reason=(reason or "OPEN_SCORING_INTERVAL") if unresolved else "CONCLUSIVE_EVIDENCE",
            )
            if unresolved:
                (nonblocking if reason else pending).append(occurrence)
            if obligation.effective_status == "technical_error":
                errors.append(occurrence)
            review = (policy.needs_review(obligation) if policy else
                      obligation.effective_status in {"supported", "refuted"})
            if obligation.origin in {"semantic", "secondary", "diagram"} and review:
                semantic.append({**occurrence, "decision_conclusive": not unresolved})

    for rule, decision in zip(config.items, assessment.items):
        visit(rule, decision, (rule.id,))

    determined = all(item.status == "decided" for item in assessment.items)
    # Never report a withhold subtotal as final, even if assessment.score is numeric.
    result.update(
        score_state="determined" if determined else "undetermined",
        final_score=str(assessment.score) if determined else None,
        known_points=str(assessment.known_points), possible_points=str(assessment.possible_points),
        max_score=str(assessment.max_score),
        items=[dict(item_id=i.item_id, score_state="determined" if i.status == "decided" else "undetermined",
                    points_awarded=str(i.points_awarded) if i.points_awarded is not None else None,
                    known_points=str(i.known_points), possible_points=str(i.possible_points),
                    selected_method_path=i.selected_method_path, selected_band=i.selected_band)
               for i in assessment.items],
        mathematical_pending=dict(state="present" if pending else "absent",
                                  obligation_ids=list(dict.fromkeys(o["obligation_id"] for o in pending)),
                                  occurrences=pending),
        nonblocking_pending=nonblocking,
        dispensable_alternatives=[o for o in nonblocking if o["dispensable_alternative"]],
        technical_errors=errors,
        semantic_evidence_review=dict(state="present" if semantic else "absent", occurrences=semantic),
    )
    if determined == bool(pending):
        # A future/unsupported tree must not silently clear a recorded uncertainty.
        return _empty("UNEXPLAINED_OPEN_SCORING_INTERVAL")
    return result


def diagnose_run(run):
    """Separate additive read projection; no mutation or new persisted fields."""
    saved = run.result
    if run.status != "COMPLETED" or saved is None:
        result = _empty("AUDIT_NOT_COMPLETED")
    elif not isinstance(saved, TMEAuditResult):
        result = _empty("UNSUPPORTED_RESULT_TYPE")
    else:
        result = project_pauta(saved.pauta, saved.assessment,
                               semantic_policy=saved.context.semantic_policy)
    result.update(
        audit_run_id=run.audit_run_id, problem_id=run.problem_id,
        source_result_sha256=run.result_sha256, source_hash=run.source_hash,
        stale=getattr(run, "stale", None),
        legacy=dict(status=run.status, score=saved.score if saved else None,
                    needs_review=getattr(saved, "needs_review", None),
                    verdict=saved.verdict if saved else None),
    )
    context = getattr(run, "question_context", None)
    if context is not None and context.engine_mode == "TME_CURRENT":
        # finalization._summary explicitly blocks an exam question without a
        # current HumanDecision. This is a CURRENT workflow requirement, not an
        # inference about the historical flag or whether a human already acted.
        result["human_review"] = dict(
            state="required", required=True, confirmation_state="unknown",
            scope="current_exam_finalization", rule_id="tme.finalization.current_human_decision",
            reason="EXAM_FINALIZATION_REQUIRES_CURRENT_HUMAN_DECISION",
            question_attempt_id=context.question_attempt_id,
        )
    return result
