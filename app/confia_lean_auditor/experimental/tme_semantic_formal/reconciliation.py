"""Reuse audit precedence/traces; C1 conflicts are explicit blocking decisions."""
import ast
from confia_lean_auditor.tme.hybrid_grader import EvidenceReconciler
from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.lean.student_claim_checkers.tme2_p1 import sides, eq, expression_syntax
from confia_lean_auditor.core.math_canonical import equivalent
from .obligation_registry import PROBLEM_ID, REGISTRY

POSITIVE = {'FORMAL_VERIFIED', 'DETERMINISTIC_VERIFIED', 'SEMANTIC_SUPPORTED'}


def conflicting_definitions(oid, math_bridge, guard_bridge):
    """Preserve the existing fresh-symbol constraint beyond selected claims."""
    if oid not in {'b.reversed_number', 'c.uses_expression', 'c.pattern_recognized'}:
        return set()
    selected = next(e for e in math_bridge.evidence.obligations if e.obligation_id == oid)
    conflicts = set()
    for record in math_bridge.auditor.records:
        if record.record_id not in selected.source_claim_ids:
            continue
        pair = sides(record)
        symbol = expression_syntax(pair[0]) if pair else None
        if not isinstance(symbol, ast.Name) or symbol.id in {'a', 'b', 'c'}:
            continue
        definitions = [r for r in guard_bridge.auditor.records if r.source.attributable
                       and r.rubric_links == (oid[0],) and sides(r) and eq(sides(r)[0], pair[0])]
        if any(equivalent(sides(r)[1], pair[1]).status == 'not_equivalent' for r in definitions):
            conflicts.update(r.record_id for r in definitions)
    return conflicts


def resolve_conflict(results, *, rule=None):
    """Only identical-bound-claim formal evidence can override semantic opinion.

    Not used automatically by C1. In particular, conflicting formal results can
    never be resolved by model confidence, order, or a preferred numeric answer.
    """
    ids = list(dict.fromkeys(i for r in results for i in r['evidence_ids']))
    decision = dict(conflicting_evidence_ids=ids, resolved=False, resolution_rule=None,
                    winning_evidence=[], rejected_evidence=[], resolution_reason='unresolved_conflict')
    if rule is None:
        return decision
    if rule != 'same_bound_claim_formal_over_semantic':
        raise ValueError('unknown_conflict_resolution_rule')
    formal = [r for r in results if r['status'] in {'FORMAL_VERIFIED', 'FORMAL_REFUTED'}]
    other = [r for r in results if r not in formal]
    binding = {r.get('claim_binding_sha256') for r in results}
    if (not formal or not other or len({r['status'] for r in formal}) != 1
            or len(binding) != 1 or None in binding
            or any(r['route'] != 'SEMANTIC' for r in other)):
        raise ValueError('resolution_requires_identical_bound_claim_and_settled_formal_result')
    return dict(decision, resolved=True, resolution_rule=rule,
                winning_evidence=list(dict.fromkeys(i for r in formal for i in r['evidence_ids'])),
                rejected_evidence=list(dict.fromkeys(i for r in other for i in r['evidence_ids'])),
                resolution_reason='Same source-bound proposition; executed formal result has precedence over semantic opinion.')


def reconcile(document, math_bridge, guard_bridge, results):
    _, inherited = EvidenceReconciler().reconcile(PROBLEM_ID, document.text, (), math_bridge, math_bridge)
    guards = {e.obligation_id: e for e in guard_bridge.evidence.obligations}
    # Translate the guard's existing digital coordinates back to original units,
    # including counterevidence the extractor did not select.
    framed_starts, offset = {}, 0
    for item in 'abcd':
        if item in document.items:
            offset += len('[' + item + ']\n')
            framed_starts[item] = offset
            offset += len(document.items[item]) + 2
    units = evidence_units(document.text)
    conflicts = []
    for oid in REGISTRY:
        rows = [r for r in results if r['obligation_id'] == oid]
        positive = any(r['status'] in POSITIVE for r in rows)
        negative = any(r.get('mathematical_refutation') or r.get('semantic_contradiction') for r in rows)
        guard = guards[oid]
        definition_conflicts = conflicting_definitions(oid, math_bridge, guard_bridge)
        guard_conflict = guard.metadata.get('reason') in {'CONFLICTING_FACT_RESULTS', 'CONFLICTING_CONDITIONAL_CONTEXTS'}
        if (positive and negative) or guard_conflict or definition_conflicts or (positive and guard.status == 'refuted') or any(
                r['status'] == 'CONFLICTING_EVIDENCE' for r in rows) or any(
                r.get('semantic_contradiction') for r in rows):
            # No silent automatic resolution. All source disagreements stay visible.
            decision = resolve_conflict(rows)
            source_ids = list(set(guard.source_claim_ids) | definition_conflicts)
            records = [r.model_dump(mode='json') for r in guard_bridge.auditor.records if r.record_id in source_ids]
            bindings = []
            for record in records:
                if len(record['rubric_links']) != 1:
                    continue
                item = record['rubric_links'][0]
                start = record['source']['source_start']
                end = record['source']['source_end']
                if start is None or end is None:
                    continue
                a = document.ranges[item][0] + start - framed_starts[item]
                b = a + end - start
                if document.text[a:b] != record['source']['raw_text']:
                    raise ValueError('guard_source_coordinate_mismatch')
                source_units = [u.evidence_id for u in units if a < u.source_end and b > u.source_start]
                bindings.append(dict(source_claim_id=record['record_id'], source_evidence_ids=source_units,
                    source_start=a, source_end=b, source_span=document.text[a:b]))
            decision['conflicting_evidence_ids'] = list(dict.fromkeys(
                decision['conflicting_evidence_ids'] + [i for b in bindings for i in b['source_evidence_ids']]))
            conflicts.append(dict(obligation_id=oid, status='CONFLICTING_EVIDENCE', **decision,
                guard_evidence=guard.model_dump(mode='json'), guard_source_records=records,
                guard_source_bindings=bindings,
                detection_reason='conflicting_written_symbol_definitions' if definition_conflicts else 'conflicting_evidence'))
    return conflicts, inherited
