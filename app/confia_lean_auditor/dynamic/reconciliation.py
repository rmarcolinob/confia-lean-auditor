"""Deterministic authority gates; opinions never establish mathematical truth."""

from decimal import Decimal
from .reconciliation_models import CriterionReconciliation
from .reviewer import evidence_inventory, additional_evidence, independent_limit
from .grader import criterion_policy


class SafeAutomationPolicy:
    def __init__(self, profile):
        if profile not in {"FORMATIVE_LIST", "SCHOOL_EXAM"}:
            raise ValueError("unknown policy")
        self.profile = profile

    def decision(self, *, safe, grader, verified, material):
        if not safe or (material and self.profile == "SCHOOL_EXAM"):
            return "REVIEW_ONLY"
        if verified > grader:
            return "AUTO_ADJUST_UP"
        if verified < grader:
            return "AUTO_ADJUST_DOWN"
        return "AUTO_ACCEPT"


def reconcile_criteria(grader, review, statement, rubric, solution, profile):
    from .semantic import enabled, reconcile
    if enabled(grader.context):
        return reconcile(grader, review, rubric)
    policy = SafeAutomationPolicy(profile)
    equation, fresh, source_warnings = evidence_inventory(solution, statement)
    phase = review.phase_a
    if phase:
        extra, rejected = additional_evidence(phase.proposal, solution, equation)
        fresh.extend(extra)
    else:
        rejected = []
    # An independently validated extra claim can resolve the exact unsupported
    # source segment it covers. Other unverified source segments remain blockers.
    unresolved_source = [
        c
        for c in fresh
        if c.adoption == "ADOPTED"
        and c.verification_status not in {"VERIFIED", "REFUTED"}
        and not any(
            c.start <= a.start < a.end <= c.end
            and a.verification_status in {"VERIFIED", "REFUTED"}
            for a in (extra if phase else [])
        )
    ]
    inventory = {c.claim_id: c for c in fresh}
    opinions = {r.criterion_id: r for r in phase.criterion_reviews} if phase else {}
    comparisons = (
        {c.criterion_id: c for c in review.comparison.criteria}
        if review.comparison
        else {}
    )
    originals = {c.claim_id: c for c in grader.analysis.claims}
    decisions = {d.criterion_id: d for d in grader.decisions}
    result = []
    for criterion in sorted(rubric.criteria, key=lambda c: c.order):
        g = decisions[criterion.criterion_id]
        r = opinions.get(criterion.criterion_id)
        cmp = comparisons.get(criterion.criterion_id)
        evidence = [inventory[k] for k in r.claim_ids if k in inventory] if r else []
        limit, suff, warnings = independent_limit(criterion, evidence, equation, fresh)
        technical = review.status == "FAILED" or any(
            c.verification_status == "ERROR" for c in evidence
        )
        faithful = (
            bool(r)
            and len(evidence) == len(set(r.claim_ids)) == len(r.claim_ids)
            and all(
                c.adoption == "ADOPTED"
                and c.fidelity in {"FAITHFUL", "SUPPORTED_NORMALIZATION"}
                for c in evidence
            )
        )
        verified = bool(evidence) and all(
            c.verification_status in {"VERIFIED", "REFUTED"} for c in evidence
        )
        kinds = cmp.disagreement_types if cmp else []
        # Independent check statuses remain authoritative, even when BOTH opinions agree.
        conflict = suff == "CONFLICT"
        dependencies = any(
            not any(
                x.criterion_id == dep
                and x.automation != "REVIEW_ONLY"
                and x.sufficiency == "COMPLETE"
                for x in result
            )
            for dep in criterion.dependencies
        )
        safe = bool(
            r
            and r.proposed_points is not None
            and limit is not None
            and r.proposed_points == limit
            and faithful
            and verified
            and suff in {"COMPLETE", "PARTIAL", "NOT_SATISFIED"}
            and not conflict
            and not technical
            and not dependencies
            and not r.review_required
            and not r.uncertainty
            and not unresolved_source
            and not rejected
        )
        equal = bool(r and r.proposed_points == g.suggested_points)
        material = not equal or bool(kinds) or bool(g.review_required)
        action = policy.decision(
            safe=safe,
            grader=g.suggested_points,
            verified=limit or Decimal(0),
            material=material,
        )
        status = "REVIEW_REQUIRED"
        reason = "Evidência, interpretação ou política exige revisão; pontos provisórios preservados."
        if technical:
            status = "TECHNICAL_ERROR"
            reason = (
                "Falha técnica não refuta a resolução; pontos provisórios preservados."
            )
        elif conflict:
            status = "MATHEMATICAL_CONFLICT"
            reason = "Conclusões adotadas conflitantes; não selecionar silenciosamente a positiva."
        elif safe:
            if limit > g.suggested_points:
                status = "GRADER_MISSED_CREDIT_CONFIRMED"
                reason = "Evidência fiel e verificável satisfaz a rubrica; crédito legítimo identificado."
            elif limit < g.suggested_points:
                status = "GRADER_FALSE_CREDIT_CONFIRMED"
                reason = "Evidência fiel refutada ou parcial não sustenta o crédito original segundo a rubrica."
            elif material:
                status = "CHECKER_RESOLVED"
                reason = "Verificação local, fidelity e suficiência conferidas; pontos sustentados apesar da divergência interpretativa."
            else:
                status = "AGREEMENT_SUPPORTED"
                reason = "Concordância sustentada por fonte fiel, verificação local e obrigação aprovada."
            if action == "REVIEW_ONLY":
                reason += " Perfil SCHOOL_EXAM exige homologação da divergência; sem ajuste automático."
        elif suff == "INSUFFICIENT" and criterion_policy(criterion)[0] in {
            "method",
            "factorization",
        }:
            status = "SUFFICIENCY_DISAGREEMENT"
            reason = "Resultado verdadeiro não substitui a justificativa exigida; nenhuma mudança automática."
        elif (
            any(c.verification_status == "REFUTED" for c in evidence)
            and equal
            and g.suggested_points > 0
        ):
            status = "MATHEMATICAL_CONFLICT"
            reason = "A concordância dos agentes contradiz a evidência matemática; não é automação segura."
        elif "STRATEGY_DISAGREEMENT" in kinds:
            status = "STRATEGY_DISAGREEMENT"
        elif "SUFFICIENCY_DISAGREEMENT" in kinds:
            status = "SUFFICIENCY_DISAGREEMENT"
        elif equal:
            status = "AGREEMENT_UNVERIFIED"
            reason = "Igualdade de pontos sem todas as condições de verificação/suficiência; revisão necessária."
        elif not evidence or limit is None:
            status = "INSUFFICIENT_EVIDENCE"
        if dependencies:
            reason += " Dependência/follow-through não resolvido; sem regra genérica de crédito."
        points = g.suggested_points if action == "REVIEW_ONLY" else limit
        delta = points - g.suggested_points
        result.append(
            CriterionReconciliation(
                criterion_id=criterion.criterion_id,
                max_points=criterion.max_points,
                grader_points=g.suggested_points,
                reviewer_points=r.proposed_points if r else None,
                grader_evidence=[
                    originals[k].text for k in g.claim_ids if k in originals
                ],
                reviewer_evidence=r.evidence if r else [],
                mathematical_verification=evidence,
                fidelity_binding_state=(
                    "SUPPORTED" if faithful and limit is not None else "REVIEW_REQUIRED"
                ),
                sufficiency=suff,
                status=status,
                reconciled_points=points,
                automation=action,
                reason=reason,
                review_required=action == "REVIEW_ONLY",
                technical_uncertainty=technical,
                recovered_credit=max(delta, 0),
                points_removed=max(-delta, 0),
            )
        )
    return result
