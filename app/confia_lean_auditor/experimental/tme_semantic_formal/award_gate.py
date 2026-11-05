"""Award eligibility only. PautaEngine owns rule selection and all point values."""
from confia_lean_auditor.rubric.pauta.models import ObligationEvidence, PautaEvidence
from confia_lean_auditor.rubric.pauta.evidence_policy import HybridEvidencePolicy
from .obligation_registry import PROBLEM_ID, REGISTRY
from .reconciliation import POSITIVE, resolve_conflict


class AwardGate:
    def evaluate(self, case_id, evidence, mapping, results, conflicts):
        eligible = {(m['evidence_id'], m['obligation_id']) for m in mapping if m['accepted']}
        by_id = {e.evidence_id: e for e in evidence}
        blocked = {c['obligation_id'] for c in conflicts if not c['resolved']}
        resolved_winners = {}
        for conflict in conflicts:
            if conflict['resolved']:
                if not conflict.get('resolution_rule'):
                    raise ValueError('resolved_conflict_requires_explicit_rule')
                resolution = resolve_conflict([r for r in results if r['obligation_id'] == conflict['obligation_id']],
                                               rule=conflict['resolution_rule'])
                for field in ('winning_evidence', 'rejected_evidence', 'resolution_reason'):
                    if resolution[field] != conflict.get(field):
                        raise ValueError('conflict_resolution_does_not_match_executed_rule')
                resolved_winners[conflict['obligation_id']] = set(resolution['winning_evidence'])
        decisions, observations = [], []
        for oid in REGISTRY:
            rows = [r for r in results if r['obligation_id'] == oid]
            positive = [r for r in rows if r['status'] in POSITIVE and r['sufficiency_decision']['sufficient']
                        and any((i, oid) in eligible for i in r['evidence_ids'])]
            if oid in resolved_winners:
                positive = [r for r in positive if set(r['evidence_ids']) <= resolved_winners[oid]]
            # Defense in depth even if this class is called directly.
            positive = [r for r in positive if all(i in by_id and by_id[i].attributed_to_student
                and by_id[i].assertion_status == 'asserted' and by_id[i].polarity == 'positive'
                and not by_id[i].hypothetical and not by_id[i].abandoned
                and by_id[i].scope in {'main_argument', 'final_conclusion'} for i in r['evidence_ids'])]
            chosen = None if oid in blocked else next((r for r in positive if r['route'] != 'SEMANTIC'), None)
            chosen = chosen or (positive[0] if positive and oid not in blocked else None)
            negative = any(r.get('mathematical_refutation') for r in rows)
            technical = any(r.get('technical_uncertainty') for r in rows)
            status = 'supported' if chosen else 'indeterminate' if oid in blocked else 'refuted' if negative else 'technical_error' if technical else 'indeterminate'
            ids = list(dict.fromkeys((chosen or {}).get('evidence_ids', []) + (chosen or {}).get('prerequisite_evidence_ids', [])))
            route = chosen['route'] if chosen else next((r['route'] for r in rows if r['route']), 'DETERMINISTIC')
            origin = {'FORMAL': 'student_lean', 'DETERMINISTIC': 'deterministic', 'SEMANTIC': 'semantic'}[route]
            refs = ids or list(dict.fromkeys(i for r in rows for i in r['evidence_ids']))
            metadata = dict(c1=True, conflict=oid in blocked,
                award_decision='eligible' if chosen else 'blocked_conflict' if oid in blocked else 'no_sufficient_verified_evidence')
            if chosen and route == 'SEMANTIC':
                metadata.update(reconciliation_policy=HybridEvidencePolicy().version,
                    evidence_tier='SEMANTIC_SUPPORTED', confidence='medium', context_valid=True)
            observations.append(ObligationEvidence(obligation_id=oid, status=status, origin=origin,
                verification_source=origin, attributable_to_student=bool(chosen or negative),
                evidence_refs=tuple(refs), source_claim_ids=tuple((chosen or {}).get('source_claim_ids', [])),
                grounding_status='grounded' if refs else 'unavailable', metadata=metadata))
            decisions.append(dict(obligation_id=oid, rubric_item=REGISTRY[oid].rubric_item,
                eligible=bool(chosen), evidence_ids=ids, verification_route=chosen['route'] if chosen else None,
                verification_status=chosen['status'] if chosen else 'CONFLICTING_EVIDENCE' if oid in blocked else None,
                verification_result=chosen, sufficiency_decision=chosen['sufficiency_decision'] if chosen else None,
                conflict_decision=next((c for c in conflicts if c['obligation_id'] == oid), None),
                award_decision=metadata['award_decision'], technical_uncertainty=technical,
                bindings=[by_id[i].model_dump(mode='json') for i in ids]))
        return PautaEvidence(problem_id=PROBLEM_ID, solution_id=case_id, obligations=tuple(observations)), decisions


def credited_rules(assessment, awards):
    """Count a selected payable rule once; all_of witnesses share its points."""
    by_oid = {a['obligation_id']: a for a in awards}
    credits = []
    def visit(node, rubric_item):
        if not node.known_points:
            return
        if node.scoring_strategy in {'banded', 'max_of'}:
            selected = node.selected_band or node.selected_method_path
            for child in node.children:
                if child.item_id == selected:
                    visit(child, rubric_item)
        elif node.children:
            for child in node.children:
                visit(child, rubric_item)
        else:
            witnesses = [by_oid[o] for o in node.satisfied_obligations if by_oid[o]['eligible']]
            credits.append(dict(rubric_item=rubric_item, rule_id=node.item_id,
                points=float(node.known_points), routes=sorted({w['verification_route'] for w in witnesses}),
                obligations=witnesses))
    for item in assessment.items:
        visit(item, item.item_id)
    return credits
