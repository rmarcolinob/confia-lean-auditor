"""Phase B: deterministic comparison, never reconciliation."""

from .review_models import CriterionComparison, DynamicReviewComparison
from .grader import criterion_policy


def compare_review(grader, phase, rubric, solution):
    from .semantic import enabled
    if enabled(grader.context):
        return compare_semantic_review(grader, phase, rubric)
    independent = {r.criterion_id: r for r in phase.criterion_reviews}
    checked = {
        (c.start, c.end, c.text): c for c in [*phase.claims, *phase.additional_claims]
    }
    original = {c.claim_id: c for c in grader.analysis.claims}
    decisions = {d.criterion_id: d for d in grader.decisions}
    rows = []
    for criterion in rubric.criteria:
        g = decisions[criterion.criterion_id]
        r = independent[criterion.criterion_id]
        difference = (
            float(r.proposed_points - g.suggested_points)
            if r.proposed_points is not None
            else None
        )
        kinds = []
        reasons = []
        if difference is not None and difference < 0:
            kinds.append("FALSE_CREDIT_SUSPECTED")
            reasons.append("Crédito do grader excede a proposta independente.")
        if difference is not None and difference > 0:
            kinds.append("MISSED_CREDIT_SUSPECTED")
            reasons.append(
                "Evidência independente sustenta crédito não concedido pelo grader."
            )
        if (
            r.proposed_points is None
            and r.provider_proposed_points is not None
            and r.provider_proposed_points != g.suggested_points
        ):
            kinds.append("SUFFICIENCY_DISAGREEMENT")
            reasons.append(
                "Proposta do reviewer não validada; não há pontuação independente segura para reconciliar."
            )
        policy, _ = criterion_policy(criterion)
        types = {
            "roots": {"ROOT", "ROOTS", "FORMULA"},
            "method": {"TRANSFORMATION", "FORMULA"},
            "transformation": {"TRANSFORMATION"},
            "factorization": {"TRANSFORMATION"},
            "substitution": {"SUBSTITUTION"},
        }.get(policy, set())
        contradictions = [
            c
            for c in checked.values()
            if c.adoption == "ADOPTED"
            and c.claim_type in types
            and c.verification_status == "REFUTED"
            and (policy != "factorization" or c.strategy_context == "factorization")
        ]
        if contradictions and g.suggested_points > 0 and g.sufficiency == "COMPLETE":
            kinds.extend(["MATHEMATICAL_DISAGREEMENT", "FALSE_CREDIT_SUSPECTED"])
            reasons.append(
                "Há evidência local refutada incompatível com crédito integral neste critério."
            )
        spans = []
        for cid in g.claim_ids:
            claim = original.get(cid)
            if not claim:
                kinds.append("BINDING_DISAGREEMENT")
                reasons.append("Claim citada pelo grader não existe.")
                continue
            actual = checked.get((claim.start, claim.end, claim.text))
            spans.append(claim.text)
            if solution[claim.start : claim.end] != claim.text or (
                actual and claim.normalized != actual.normalized
            ):
                kinds.append("BINDING_DISAGREEMENT")
                reasons.append(
                    "Representação do grader não coincide com a proposição na fonte."
                )
            if types and (
                not actual
                or actual.claim_type not in types
                or policy == "factorization"
                and actual.strategy_context != "factorization"
            ):
                kinds.append("BINDING_DISAGREEMENT")
                reasons.append(
                    "Evidência do grader não corresponde à obrigação deste critério."
                )
            if actual and (
                (
                    actual.verification_status == "REFUTED"
                    and g.suggested_points > 0
                    and g.sufficiency == "COMPLETE"
                )
                or actual.verification_status != claim.verification_status
            ):
                kinds.append("MATHEMATICAL_DISAGREEMENT")
                reasons.append(
                    "Resultado matemático independente diverge da evidência usada pelo grader."
                )
        if difference and r.sufficiency != g.sufficiency:
            kinds.append("SUFFICIENCY_DISAGREEMENT")
        if difference and phase.alternative_strategy:
            kinds.append("STRATEGY_DISAGREEMENT")
        kinds = list(dict.fromkeys(kinds))
        unresolved = r.review_required or g.review_required or r.proposed_points is None
        agreement = (
            "DISAGREEMENT" if kinds else "UNRESOLVED" if unresolved else "AGREEMENT"
        )
        rows.append(
            CriterionComparison(
                criterion_id=criterion.criterion_id,
                grader_points=g.suggested_points,
                reviewer_points=r.proposed_points,
                grader_status=g.sufficiency,
                reviewer_status=r.assessment,
                agreement=agreement,
                difference=difference,
                disagreement_types=kinds,
                evidence_overlap=sorted(set(spans) & set(r.evidence)),
                reason=" ".join(reasons)
                or (
                    "Mesma pontuação e suficiência verificável; concordância não constitui prova matemática."
                    if agreement == "AGREEMENT"
                    else "Há incerteza não resolvida; igualdade numérica não é concordância suficiente."
                ),
                review_required=agreement != "AGREEMENT",
            )
        )
    conflicts = [r.criterion_id for r in rows if r.agreement == "DISAGREEMENT"]
    exact = all(r.agreement == "AGREEMENT" for r in rows)
    total = (
        sum(r.difference for r in rows)
        if all(r.difference is not None for r in rows)
        else None
    )
    return DynamicReviewComparison(
        criteria=rows,
        exact_agreement=exact,
        agreement_count=sum(r.agreement == "AGREEMENT" for r in rows),
        total_point_difference=round(total, 2) if total is not None else None,
        conflicting_criteria=conflicts,
        review_required=phase.review_required or not exact,
        status=(
            "DISAGREEMENT" if conflicts else "AGREEMENT" if exact else "INCONCLUSIVE"
        ),
    )


def compare_semantic_review(grader, phase, rubric):
    """Use the same point/state comparison as reconciliation; human review is separate."""
    from types import SimpleNamespace
    from .semantic import reconcile
    rows = []
    decisions = {d.criterion_id: d for d in grader.decisions}
    independent = {r.criterion_id: r for r in phase.criterion_reviews}
    for item in reconcile(grader, SimpleNamespace(phase_a=phase, status='COMPLETED'), rubric):
        g = decisions[item.criterion_id]
        r = independent.get(item.criterion_id)
        pending = (item.technical_uncertainty or not r or r.proposed_points is None or
                   r.review_required or bool(g.semantic_trace and g.semantic_trace['decision']=='review'))
        agrees = item.status in {'AGREEMENT_SUPPORTED', 'AGREEMENT_UNVERIFIED'}
        difference = None if pending else float(r.proposed_points-g.suggested_points)
        kinds = []
        if not agrees and not pending:
            kinds.append('SUFFICIENCY_DISAGREEMENT')
            if difference:
                kinds.append('MISSED_CREDIT_SUSPECTED' if difference>0 else 'FALSE_CREDIT_SUSPECTED')
        rows.append(CriterionComparison(criterion_id=item.criterion_id,
            grader_points=item.grader_points,reviewer_points=item.reviewer_points,
            grader_status=g.sufficiency,reviewer_status=r.assessment if r else 'INSUFFICIENT',
            agreement='AGREEMENT' if agrees else 'UNRESOLVED' if pending else 'DISAGREEMENT',
            difference=difference,disagreement_types=kinds,
            evidence_overlap=sorted(set(item.grader_evidence)&set(item.reviewer_evidence)),
            reason=item.reason,review_required=item.review_required))
    conflicts=[r.criterion_id for r in rows if r.agreement=='DISAGREEMENT']
    agreement=all(r.agreement=='AGREEMENT' for r in rows)
    return DynamicReviewComparison(criteria=rows,exact_agreement=agreement,
        agreement_count=sum(r.agreement=='AGREEMENT' for r in rows),
        total_point_difference=round(sum(r.difference for r in rows),2) if all(r.difference is not None for r in rows) else None,
        conflicting_criteria=conflicts,review_required=any(r.review_required for r in rows),
        status='DISAGREEMENT' if conflicts else 'AGREEMENT' if agreement else 'INCONCLUSIVE')
