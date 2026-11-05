"""Adapters to existing P1 checkers and independent semantic sufficiency."""
from __future__ import annotations

import json
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.student_claims.tme2_p1_digital import collect_tme2_p1_digital
from confia_lean_auditor.lean.student_claim_checkers.tme2_p1 import verify_tme2_p1_digital
from confia_lean_auditor.rubric.pauta.bridge import bridge_tme2_p1
from confia_lean_auditor.student_claims.hybrid_semantic import SemanticObligationJudgment
from confia_lean_auditor.student_claims.semantic_sufficiency import (
    SemanticSufficiencyGate, request_sufficiency, validate_response)
from .obligation_registry import PROBLEM_ID, REGISTRY, FORMAL_OBLIGATIONS
from .semantic_extractor import transport


def formal_execution(check):
    """Confirm execution from the existing checker contract, not just a route.

    Some technical failures can happen before subprocess creation. Their old
    contract cannot establish whether Lean started; keep that fact unknown.
    """
    if not (check and check.get('lean_statement') and check.get('lean_file')):
        return False
    if check.get('status') in {'unsupported', 'ungrounded'}:
        return False
    if check.get('failure_category') in {'INVALID_PROOF', 'PROCESS_ERROR'}:
        return None
    return True


def verification_status(route, status, *, formal_attempted=False):
    if route == 'FORMAL':
        if status == 'technical_error':
            return 'FORMAL_ERROR'
        if not formal_attempted:
            return 'FORMAL_NOT_ATTEMPTED'
        return {'verified': 'FORMAL_VERIFIED', 'refuted': 'FORMAL_REFUTED',
                'technical_error': 'FORMAL_ERROR'}.get(status, 'FORMAL_UNPROVED')
    return 'DETERMINISTIC_VERIFIED' if status == 'verified' else 'DETERMINISTIC_FAILED'


def complete_item_sufficiency(results, guard_bridge):
    """A claim projection cannot certify that no other assertion was written.

    The original single-error diagnostic inspects the entire item and number of
    claims. Require that original diagnostic for this whole-item local policy;
    other independent obligations keep their own sufficiency contracts.
    """
    guard = next(e for e in guard_bridge.evidence.obligations if e.obligation_id == 'a.arithmetic_error_only')
    for result in results:
        if (result['obligation_id'] == 'a.arithmetic_error_only' and result['route'] == 'DETERMINISTIC'
                and result['status'] == 'DETERMINISTIC_VERIFIED' and guard.status != 'supported'):
            result['sufficiency_decision'] = dict(sufficient=False,
                policy=REGISTRY['a.arithmetic_error_only'].sufficiency_policy,
                basis='original_complete_item_diagnostic_not_satisfied',
                guard_evidence=guard.model_dump(mode='json'))


class ClaimProjection:
    """Replayable semantic adapter ABI; returns only extracted eligible records.

    Generic unselected claims remain available to a separate veto audit. They
    cannot silently grant C1 credit when the extractor omitted them.
    """
    def __init__(self, document, evidence, mapping):
        self.document = document
        ids = {m['evidence_id'] for m in mapping if m['accepted'] and m['effective_route'] != 'SEMANTIC'}
        self.evidence = [e for e in evidence if e.evidence_id in ids]
        self.bindings, self.events = {}, []

    def __call__(self, problem, source, ranges, deterministic, *, observe=True):
        records, bindings, events = {}, {}, []
        for e in self.evidence:
            owner = next(k for k, (a, b) in self.document.ranges.items() if a <= e.source_start < e.source_end <= b)
            original_start = self.document.ranges[owner][0]
            a = ranges[owner][0] + e.source_start - original_start
            b = a + len(e.source_span)
            if source[a:b] != e.source_span:
                raise ValueError('coordinate_translation_failed')
            segments = [(0, len(e.source_span), e.normalized_claim)]
            # Match the baseline's adjacent-equality grammar, only within this
            # selected, unchanged written chain. Never infer endpoint equalities.
            if (owner == 'b' and e.claim_type == 'expression' and e.source_span.count('=') > 1
                    and legacy.notation_view(e.source_span).rstrip('.')
                    == legacy.notation_view(e.normalized_claim).rstrip('.')):
                from confia_lean_auditor.student_claims.generic_math import candidate_spans
                adjacent = [(x, y, data['expression']) for x, y, kind, data in candidate_spans(e.source_span)
                            if kind == 'math_relation' and data.get('expression', '').count('=') == 1]
                if len(adjacent) == e.source_span.count('='):
                    segments = sorted(adjacent)
            for index, (x, y, expression) in enumerate(segments):
                candidate = legacy.SemanticClaimCandidate(candidate_id=e.evidence_id,
                    claim_kind='finite_set' if e.claim_type == 'collection' else 'algebraic_relation',
                    source_text=e.source_span[x:y], source_start=a+x, source_end=a+y, assertion_mode='asserted',
                    normalized_payload=legacy.NormalizedPayload(subject=e.claim_type,
                        expression=expression, item_id=owner))
                record, event = legacy.convert_candidate(problem, source, candidate, ranges)
                records[record.record_id] = record
                bindings.setdefault(record.record_id, []).append(e.evidence_id)
                events.append(dict(evidence_id=e.evidence_id, **event,
                    parent_source_span=e.source_span, parent_normalized_claim=e.normalized_claim,
                    derived_source_span=e.source_span[x:y], derived_expression=expression,
                    original_source_start=e.source_start+x, original_source_end=e.source_start+y,
                    segment_index=index, segment_count=len(segments),
                    derivation='written_adjacent_equality' if len(segments) > 1 else 'selected_claim'))
        if observe:
            self.bindings, self.events = bindings, events
        return tuple(records.values()), None


def mathematical_verification(document, evidence, mapping, config, case_id, *, use_lean=True):
    session = ClaimProjection(document, evidence, mapping)
    with legacy.supplement_scope(session):
        digital = collect_tme2_p1_digital(document.items)
        bundle = verify_tme2_p1_digital(digital, case_id, use_lean=use_lean, run_id='tme-semantic-formal-c1')
    bridge = bridge_tme2_p1(config, bundle)
    candidates = {(m['evidence_id'], m['obligation_id']) for m in mapping if m['accepted']}
    results = []
    evidence_by_id = {e.evidence_id: e for e in evidence}
    # The bridge validates proof identity, source fingerprints and attribution.
    from confia_lean_auditor.rubric.pauta.bridge import _validated_status
    records = {r.record_id: r for r in bundle.records}
    from confia_lean_auditor.rubric.pauta.bridge import TME2_P1_OBLIGATIONS
    for fact in bundle.facts:
        oid = TME2_P1_OBLIGATIONS[fact.fact_id]
        ids = list(dict.fromkeys(i for rid in fact.source_claim_ids for i in session.bindings.get(rid, [])))
        if not any((i, oid) in candidates for i in ids):
            continue
        prerequisite_ids = list(dict.fromkeys(i for rid in fact.metadata.get('counting_claim_ids', [])
                                              for i in session.bindings.get(rid, [])))
        route = 'FORMAL' if oid in FORMAL_OBLIGATIONS else 'DETERMINISTIC'
        validated, reason = _validated_status(fact, [records[i] for i in fact.source_claim_ids], bundle.source_sha256)
        attempted = (route == 'FORMAL' and fact.verification_source == 'student_lean'
                     and formal_execution(fact.student_check))
        status = verification_status(route, fact.verification.status, formal_attempted=attempted)
        if validated not in {'supported', 'refuted', 'technical_error'}:
            status = ('FORMAL_UNPROVED' if attempted else 'FORMAL_NOT_ATTEMPTED') if route == 'FORMAL' else 'DETERMINISTIC_FAILED'
        if route == 'FORMAL' and not attempted and status != 'FORMAL_ERROR':
            status = 'FORMAL_NOT_ATTEMPTED'
            reason = 'formal_checker_not_executed_for_this_representation'
        results.append(dict(obligation_id=oid, evidence_ids=ids, prerequisite_evidence_ids=prerequisite_ids,
            route=route, status=status, formal_attempted=attempted,
            technical_uncertainty=fact.verification.status == 'technical_error',
            mathematical_refutation=validated == 'refuted' and (route != 'FORMAL' or status == 'FORMAL_REFUTED'),
            source_claim_ids=list(fact.source_claim_ids), verification_id=fact.verification.verification_id,
            verification_ref=fact.verification.artifact_ref, checker_result=fact.student_check,
            normalized_claims=[evidence_by_id[i].normalized_claim for i in ids], reason=reason,
            sufficiency_decision=dict(sufficient=status in {'FORMAL_VERIFIED', 'DETERMINISTIC_VERIFIED'},
                policy=REGISTRY[oid].sufficiency_policy, basis='existing_P1_fact_contract',
                logical_dependencies=list(REGISTRY[oid].logical_dependencies))))
    for m in mapping:
        if m['accepted'] and m['effective_route'] != 'SEMANTIC' and not any(
                r['obligation_id'] == m['obligation_id'] and m['evidence_id'] in r['evidence_ids'] for r in results):
            results.append(dict(obligation_id=m['obligation_id'], evidence_ids=[m['evidence_id']],
                prerequisite_evidence_ids=[], route=m['effective_route'],
                status='FORMAL_NOT_ATTEMPTED' if m['effective_route'] == 'FORMAL' else 'DETERMINISTIC_FAILED',
                formal_attempted=False,
                technical_uncertainty=False, mathematical_refutation=False,
                reason='no_existing_fact_for_selected_claim',
                sufficiency_decision=dict(sufficient=False, basis='missing_checker_fact')))
    return bridge, results, session.events


def semantic_verification(document, evidence, mapping, extractor, *, provider=None):
    by_id = {e.evidence_id: e for e in evidence}
    grouped = {}
    for m in mapping:
        if m['accepted'] and m['effective_route'] == 'SEMANTIC':
            grouped.setdefault(m['obligation_id'], []).append(m['evidence_id'])
    judgments = []
    for oid, ids in grouped.items():
        source_ids = list(dict.fromkeys(i for eid in ids for i in by_id[eid].source_evidence_ids))
        # 'satisfied' is an adapter trigger for prepare(), not an awarded result
        # or LLM mathematical verdict. Only the independent gate can support it.
        judgments.append(SemanticObligationJudgment(obligation_id=oid, semantic_judgment='satisfied',
            evidence_ids=source_ids, method_path='equivalent_alternative', assertion_mode='asserted',
            confidence='medium', concise_rationale='C1 candidate pending independent sufficiency.',
            extracted_mathematical_statements=[]))
    gate = SemanticSufficiencyGate()
    payload, local, links = gate.prepare(PROBLEM_ID, document.text, judgments)
    try:
        def remote(p):
            return request_sufficiency(p, model=extractor.model,
                request_builder=lambda r: transport(r, extractor.model, extractor.reasoning_effort))
        decisions, meta = gate.evaluate(payload, provider=provider or remote)
        if meta['status'] == 'completed':
            decisions = validate_response(json.dumps({'decisions': {d.obligation_id: d.model_dump() for d in decisions}}), payload)
        elif decisions:
            raise ValueError('failed_sufficiency_provider_supplied_decisions')
    except Exception as error:
        decisions, meta = (), dict(status='unavailable', reason=type(error).__name__, api_calls=0)
    lookup = {d.obligation_id: d for d in (*local, *decisions)}
    result = []
    for oid, ids in grouped.items():
        d = lookup.get(oid)
        sufficient = bool(d and d.sufficiency == 'sufficient')
        result.append(dict(obligation_id=oid, evidence_ids=list(dict.fromkeys(ids)), prerequisite_evidence_ids=[],
            route='SEMANTIC', status='SEMANTIC_SUPPORTED' if sufficient else 'SEMANTIC_INSUFFICIENT',
            technical_uncertainty=d is None or (d is not None and d.reason_code == 'provider_error'),
            mathematical_refutation=False, semantic_contradiction=bool(d and d.sufficiency == 'contradictory'),
            reason=d.reason_code if d else 'sufficiency_provider_error',
            sufficiency_decision=dict(sufficient=sufficient, policy=REGISTRY[oid].sufficiency_policy,
                result=d.model_dump(mode='json') if d else None)))
    return result, dict(provider=meta, payload=payload, linkage=links)
