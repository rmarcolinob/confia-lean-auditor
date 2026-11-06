"""Three opt-in P3(b) replacements; original ten producers and scorer preserved."""
from fractions import Fraction

from confia_lean_auditor.core.math_canonical.rational import weighted_sum_matches
from confia_lean_auditor.lean.student_claim_checkers.tme2_p3 import (
    P3Checks, _a, _b, _c, quantity, written_expression, value_status,
    assertions_in_item, by_quantity,
)
from confia_lean_auditor.student_claims.tme2_p3_digital import collect_tme2_p3_digital
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.tme.obligation_experiment import deterministic_only
from confia_lean_auditor.tme.p3_machine import load_machine
from confia_lean_auditor.tme.registry import ROOT
from confia_lean_auditor.rubric.pauta import load_pauta
from confia_lean_auditor.rubric.pauta.tme2_p3 import bridge_tme2_p3
from confia_lean_auditor.rubric.pauta.engine import PautaEngine
from confia_lean_auditor.experimental.tme_semantic_formal.score_closure import ScoreClosurePolicy
from . import VERSION
from .components import (finite_certificate, component, count_relation, probability_route,
                         probability_relation, combine)

GAPS = frozenset({'b.ordered_pairs', 'b.different_favorable', 'b.second_white_probability'})
COUNT_KINDS = {'b.ordered_pairs': 'sample', 'b.different_favorable': 'different'}


def arithmetic_component(entry):
    check = entry['student_check']
    state = entry['verification'].status
    if check:
        attempted = bool(check.get('lean_file') and check.get('lean_statement'))
        formal = ('FORMAL_ERROR' if state == 'technical_error' else
                  'FORMAL_NOT_ATTEMPTED' if not attempted else
                  {'verified': 'FORMAL_VERIFIED', 'refuted': 'FORMAL_REFUTED'}.get(state, 'FORMAL_UNPROVED'))
        status = formal
    else:
        attempted, formal = False, 'FORMAL_NOT_ATTEMPTED'
        status = {'verified': 'DETERMINISTIC_VERIFIED', 'refuted': 'DETERMINISTIC_FAILED',
                  'technical_error': 'DETERMINISTIC_ERROR'}.get(state, 'DETERMINISTIC_INCOMPLETE')
    return component('arithmetic', status, 'existing_exact_arithmetic', false=state == 'refuted',
                     formal_status=formal, formal_attempted=attempted, checker_result=check,
                     verification_ref=entry['verification'].artifact_ref,
                     scope='written_arithmetic_not_probabilistic_justification')


class StrongP3Checks(P3Checks):
    def model_component(self):
        try:
            # No caller-provided certificate or conclusion can replace the enumeration.
            cert = finite_certificate(self.machine)
            return cert, component('finite_machine', 'DETERMINISTIC_VERIFIED',
                                   'two_actual_withdrawals_and_uniform_measure', certificate=cert)
        except (ValueError, TypeError, KeyError, IndexError) as error:
            return None, component('finite_machine', 'DETERMINISTIC_ERROR', type(error).__name__)

    def add_composite(self, fact, entry, rows, *, route, extra_records=()):
        refs = [self.records[i] for i in entry['source_claim_ids']]
        refs += list(extra_records)
        decision = combine(rows)
        self.add(fact, refs, decision['state'], mechanism='deterministic', metadata=dict(
            entry['metadata'], checker=VERSION, components=rows, decision=decision,
            verification_route=route, semantic_authority=False,
            result_credit_only=route == 'result_value',
            argument_satisfied=route != 'result_value' and decision['state'] == 'verified',
            sufficiency_policy='existing_b_conclusion_result_credit_only' if route == 'result_value'
                               else 'explicit_written_relation_and_independent_model',
            original_arithmetic_verification=entry['verification'].model_dump(mode='json')))

    def observe(self, fact_id, records, status, **metadata):
        if fact_id not in COUNT_KINDS:
            return super().observe(fact_id, records, status, **metadata)
        cert, model = self.model_component()
        if cert is not None:
            status = value_status(records[0], Fraction(cert['counts'][COUNT_KINDS[fact_id]]))
        super().observe(fact_id, records, status, **metadata)
        entry = self.pending.pop()
        rows = [arithmetic_component(entry), model]
        if cert is not None:
            rows.append(count_relation(COUNT_KINDS[fact_id], written_expression(records[0]), cert))
        self.add_composite(fact_id, entry, rows, route='counting_argument')

    def source_consistency(self):
        # Veto only. Correct prior answers cannot fill a missing written relation.
        relevant = {'b.ordered_pairs', 'b.different_favorable', 'b.same_compartment'}
        negatives = [p for p in self.pending if p['fact_id'] in relevant and
                     p['verification'].status in {'refuted', 'technical_error'}]
        ids = list(dict.fromkeys(i for p in negatives for i in p['source_claim_ids']))
        status = ('DETERMINISTIC_ERROR' if any(p['verification'].status == 'technical_error' for p in negatives)
                  else 'CONFLICTING_EVIDENCE' if negatives else 'DETERMINISTIC_VERIFIED')
        return component('source_consistency', status,
                         'explicit_counting_context_conflict' if negatives else 'no_negative_context',
                         veto_only=True, negative_fact_ids=[p['fact_id'] for p in negatives]), [self.records[i] for i in ids]

    def tree_relation(self, expression, cert):
        rows = assertions_in_item(self.digital, 'b')
        expected = [Fraction(p) for p in cert['branch_probabilities']]
        groups = [by_quantity(rows, f'ramo_{i}') for i in range(1, cert['choice_count'] + 1)]
        records = [r for group in groups for r in group]
        states = [value_status(r, p) for group, p in zip(groups, expected) for r in group]
        if 'refuted' in states:
            return component('written_relation', 'DETERMINISTIC_FAILED', 'false_conditional_branch', false=True), records
        if not all(groups) or 'unverified' in states:
            return component('written_relation', 'DETERMINISTIC_INCOMPLETE', 'missing_or_unverified_branch'), records
        parts = expression.split('=')
        shape = weighted_sum_matches(parts[0], [Fraction(1, cert['choice_count'])] * cert['choice_count'], expected)
        return component('written_relation', 'DETERMINISTIC_VERIFIED' if shape else 'DETERMINISTIC_INCOMPLETE',
                         'six_conditional_branches_and_weights' if shape else 'weighted_development_not_written'), records

    def numerical(self, fact_id, record, expected, **metadata):
        if fact_id != 'b.second_white_probability':
            return super().numerical(fact_id, record, expected, **metadata)
        # Keep the original source-bound rational Lean checker and its failures intact.
        super().numerical(fact_id, record, expected, **metadata)
        entry = self.pending.pop()
        cert, model = self.model_component()
        expression = written_expression(record)
        route = probability_route(expression, tree=quantity(record) == 'arvore_total')
        rows = [arithmetic_component(entry), model]
        context, refs = self.source_consistency()
        rows.append(context)
        if cert is not None:
            if expected != Fraction(cert['second_white_probability']):
                rows.append(component('model_agreement', 'DETERMINISTIC_ERROR', 'legacy_and_independent_model_disagree'))
            if route == 'conditional_tree':
                relation, branch_refs = self.tree_relation(expression, cert)
                refs += branch_refs
                rows.append(relation)
            elif route == 'counting_development':
                rows.append(probability_relation(expression, cert))
            else:
                rows.append(component('result_credit_contract', 'DETERMINISTIC_VERIFIED',
                                      'b_conclusion_explicit_result_route_no_method_credit',
                                      rule_id='b.conclusion', argument_satisfied=False))
        self.add_composite(fact_id, entry, rows, route=route, extra_records=refs)


def audit_p3_checker_first(solution, *, solution_id='p3-checker-first', use_lean=True, run_id=None, machine=None):
    """Explicit experimental entry point. No registry mutation, LLM or new rubric.

    machine is a trusted versioned problem input, never a student/extractor field.
    Default always loads the existing P3 asset. Tests may supply independent states.
    """
    if machine is None:
        machine = load_machine(ROOT / 'examples/pautas/tme2_problem3.machine.v1.json')
    with legacy.supplement_scope(deterministic_only):
        digital = collect_tme2_p3_digital(solution)
        if collect_tme2_p3_digital(solution) != digital:
            raise ValueError('digital_projection_changed')
        checks = StrongP3Checks(digital, solution_id, machine, use_lean, run_id)
        for item, checker in zip('abc', (_a, _b, _c)):
            checker(checks, assertions_in_item(digital, item))
        bundle = checks.finish()
    config = load_pauta(ROOT / 'examples/pautas/tme2_problem3.v1.json')
    bridge = bridge_tme2_p3(config, bundle)
    assessment = PautaEngine().evaluate(config, bridge.evidence)
    results = []
    for fact in bundle.facts:
        meta = fact.metadata
        results.append(dict(obligation_id=fact.fact_id, state=fact.verification.status,
                            status=meta.get('decision', {}).get('status'),
                            verification_source=fact.verification_source,
                            source_claim_ids=list(fact.source_claim_ids), metadata=meta,
                            checker_result=fact.student_check))
    conflicts = [dict(obligation_id=e.obligation_id, reason=e.metadata['reason'], resolved=False)
                 for e in bridge.evidence.obligations if e.metadata['reason'] in
                 {'CONFLICTING_FACT_RESULTS', 'CONFLICTING_CONDITIONAL_CONTEXTS'}]
    for f in bundle.facts:
        if f.metadata.get('decision', {}).get('reason') == 'conflicting_source_evidence':
            if not any(c['obligation_id'] == f.fact_id for c in conflicts):
                conflicts.append(dict(obligation_id=f.fact_id, reason='explicit_counting_context_conflict', resolved=False))
    return dict(version=VERSION, mode='P3_CHECKER_FIRST', use_lean=use_lean,
                **ScoreClosurePolicy().close(assessment, review_recommended=bool(conflicts)),
                bridge=bridge.model_dump(mode='json'), assessment=assessment.model_dump(mode='json'),
                checks=results, conflicts=conflicts,
                awards=[dict(obligation_id=e.obligation_id, eligible=e.status == 'supported',
                             status=e.status, reason=e.metadata['reason']) for e in bridge.evidence.obligations],
                semantic_checker_enabled=False)
