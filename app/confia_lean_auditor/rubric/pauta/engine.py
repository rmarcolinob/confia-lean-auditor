"""Pure scoring over already assessed obligations; no upstream imports or I/O."""
from decimal import Decimal
import hashlib
import json

from .models import (
    ObligationDecision, PautaAssessment, PautaConfig, PautaDecision, PautaEvidence,
)

ZERO = Decimal(0)


def _unique(values):
    return tuple(dict.fromkeys(values))


def _fingerprint(model):
    data = json.dumps(model.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _predicate(states, *, any_of=False):
    """Four-valued evaluation. Decisive evidence can make uncertainty irrelevant."""
    if any_of:
        if "supported" in states:
            return "supported"
        if all(s == "refuted" for s in states):
            return "refuted"
    else:
        if "refuted" in states:
            return "refuted"
        if all(s == "supported" for s in states):
            return "supported"
    return "technical_error" if "technical_error" in states else "indeterminate"


class PautaEngine:
    def evaluate(self, config: PautaConfig, evidence: PautaEvidence) -> PautaAssessment:
        # Also reject invalid objects made with model_construct/model_copy.
        config = PautaConfig.model_validate(config.model_dump())
        evidence = PautaEvidence.model_validate(evidence.model_dump())
        if evidence.problem_id != config.problem_id:
            raise ValueError("Evidence belongs to a different problem")
        declarations = {o.id: o for o in config.obligations}
        observed = {e.obligation_id: e for e in evidence.obligations}
        if not set(observed) <= set(declarations):
            raise ValueError("Evidence references undeclared obligations")
        evaluator = _Evaluation(config, declarations, observed)
        items = tuple(evaluator.rule(item) for item in config.items)
        score = None if any(i.points_awarded is None for i in items) else sum(i.points_awarded for i in items)
        return PautaAssessment(
            config_sha256=_fingerprint(config), evidence_sha256=_fingerprint(evidence),
            problem_id=config.problem_id, solution_id=evidence.solution_id,
            unresolved_policy=config.unresolved_policy, max_score=config.max_score,
            score=score, known_points=sum(i.known_points for i in items),
            possible_points=sum(i.possible_points for i in items),
            needs_review=any(i.needs_review for i in items), items=items,
        )


class _Evaluation:
    def __init__(self, config, declarations, observed):
        self.config, self.declarations, self.observed = config, declarations, observed

    def observe(self, identifier, *, context=None, require_conditional=False):
        e = self.observed.get(identifier)
        if e is None:
            return ObligationDecision(obligation_id=identifier,
                effective_status="indeterminate", reason="MISSING_EVIDENCE")
        status, reason = e.status, "UPSTREAM_STATUS"
        if status in {"supported", "refuted"}:
            if not e.attributable_to_student:
                status, reason = "indeterminate", "NOT_ATTRIBUTABLE_TO_STUDENT"
            elif e.origin not in self.declarations[identifier].accepted_origins:
                status, reason = "indeterminate", "ORIGIN_NOT_ACCEPTED"
            elif require_conditional and (context is None or e.conditional_on != context):
                status, reason = "indeterminate", "CARRY_FORWARD_BINDING_MISSING_OR_MISMATCHED"
            elif not require_conditional and e.conditional_on is not None:
                status, reason = "indeterminate", "CONDITIONAL_EVIDENCE_NOT_UNCONDITIONAL"
        return ObligationDecision(obligation_id=identifier, input_status=e.status,
            effective_status=status, origin=e.origin, evidence_refs=e.evidence_refs,
            conditional_on=e.conditional_on, reason=reason)

    def decision(self, rule, lower, upper, *, records=(), children=(), technical=False,
                 credit_refs=(), selected=None, carry=False, fully_satisfied=None, reason):
        records = tuple(records) + tuple(o for c in children for o in c.obligations)
        uncertain = lower != upper
        status = ("technical_error" if technical else "indeterminate") if uncertain else "decided"
        # A technical failure is never converted to a rubric zero by withhold.
        points = lower if not uncertain or (self.config.unresolved_policy == "withhold" and not technical) else None
        categories = {s: _unique(o.obligation_id for o in records if o.effective_status == s)
                      for s in ("supported", "refuted", "indeterminate", "technical_error")}
        return PautaDecision(
            item_id=rule.id, scoring_strategy=rule.scoring_strategy,
            max_points=rule.max_points, points_awarded=points,
            known_points=lower, possible_points=upper, status=status,
            fully_satisfied=lower == rule.max_points if fully_satisfied is None else fully_satisfied,
            satisfied_obligations=categories["supported"],
            unsatisfied_obligations=categories["refuted"],
            indeterminate_obligations=categories["indeterminate"],
            technical_error_obligations=categories["technical_error"],
            selected_band=selected if rule.scoring_strategy == "banded" else None,
            selected_method_path=selected if rule.scoring_strategy == "max_of" else None,
            carry_forward_applied=carry,
            evidence_refs=_unique(ref for o in records for ref in o.evidence_refs),
            credit_evidence_refs=_unique(credit_refs),
            needs_review=uncertain or bool(categories["technical_error"]) or any(o.origin in {"secondary", "semantic", "diagram"}
                and o.effective_status in {"supported", "refuted"} for o in records),
            reason=reason, obligations=records, children=children,
        )

    def atomic(self, rule, records, states, *, any_of=False, carry=False):
        truth = _predicate(states, any_of=any_of)
        lower = rule.max_points if truth == "supported" else ZERO
        upper = ZERO if truth == "refuted" else rule.max_points
        witnesses = records
        if any_of and truth == "supported":
            witnesses = (next(o for o in records if o.effective_status == "supported"),)
        return self.decision(rule, lower, upper, records=records,
            fully_satisfied=truth == "supported",
            technical=truth == "technical_error",
            credit_refs=(ref for o in witnesses for ref in o.evidence_refs) if lower else (),
            carry=carry and truth == "supported" and lower > 0,
            reason="CARRY_FORWARD_CONTRACT_SATISFIED" if carry and truth == "supported" else truth.upper())

    def carry_forward(self, rule):
        contract = rule.carry_forward
        prior = self.observe(contract.prior_obligation_id)
        identifiers = contract.obligation_ids()[1:]
        adoption = self.observed.get(contract.adoption_obligation_id)
        context = adoption.conditional_on if adoption else None
        # Bind the adoption, dependency and conditional development to the exact
        # upstream result record whose correctness was previously refuted.
        if (context is None or context.rule_id != rule.id
                or context.prior_obligation_id != contract.prior_obligation_id
                or context.adopted_result_ref not in prior.evidence_refs
                or context.adopted_result_ref not in adoption.evidence_refs):
            context = None
        facts = tuple(self.observe(identifier, context=context, require_conditional=True)
                      for identifier in identifiers)
        # A proven prior error is a prerequisite here, never rewritten as correct.
        prior_condition = {"supported": "refuted", "refuted": "supported"}.get(
            prior.effective_status, prior.effective_status)
        return self.atomic(rule, (prior,) + facts,
                           (prior_condition,) + tuple(f.effective_status for f in facts), carry=True)

    def rule(self, rule):
        strategy = rule.scoring_strategy
        if strategy in {"all_of", "any_of"}:
            records = tuple(self.observe(i) for i in rule.obligation_ids)
            return self.atomic(rule, records, tuple(o.effective_status for o in records),
                               any_of=strategy == "any_of")
        if strategy == "carry_forward":
            return self.carry_forward(rule)
        children = tuple(self.rule(c) for c in rule.children)
        if strategy == "additive":
            lower = min(rule.max_points, sum(c.known_points for c in children))
            upper = min(rule.max_points, sum(c.possible_points for c in children))
            contributors = tuple(c for c in children if c.known_points > 0)
            technical = any(c.status == "technical_error" for c in children)
            selected = None
            reason = "CAPPED_SUM"
        else:
            # Bands are integral predicates; method paths may have partial credit.
            lower = max(c.known_points for c in children)
            upper = max(c.possible_points for c in children)
            best = next((c for c in children if c.known_points == lower
                         and (lower > 0 or c.fully_satisfied)), None)
            contributors = (best,) if best else ()
            technical = any(c.status == "technical_error" and c.possible_points > lower for c in children)
            selected = best.item_id if best else None
            reason = "HIGHEST_SATISFIED_BAND" if strategy == "banded" else "BEST_EVIDENCED_PATH"
        return self.decision(rule, lower, upper, children=children, technical=technical,
            credit_refs=(ref for c in contributors for ref in c.credit_evidence_refs),
            selected=selected, carry=any(c.carry_forward_applied for c in contributors), reason=reason)
