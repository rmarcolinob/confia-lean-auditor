"""P2 opt-in strengthening: replace four producers, keep all 19 others intact."""
from __future__ import annotations

from confia_lean_auditor.lean.student_claim_checkers.tme2_p2 import P2Checks
from confia_lean_auditor.student_claims.tme2_p2_digital import collect_tme2_p2_text, split_p2_input
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.tme.obligation_experiment import deterministic_only
from confia_lean_auditor.tme.registry import ROOT
from confia_lean_auditor.rubric.pauta import load_pauta
from confia_lean_auditor.rubric.pauta.tme2_p2 import bridge_tme2_p2
from confia_lean_auditor.rubric.pauta.engine import PautaEngine
from confia_lean_auditor.experimental.tme_semantic_formal.score_closure import ScoreClosurePolicy
from confia_lean_auditor.core.math_canonical.rational import rational_value
from . import VERSION
from .components import check_integrality, finite_certificate, argument_relation, component, combine

GAPS = frozenset({'b.integral_sum', 'c.pair_permutations', 'c.pair_orientations', 'c.counting_product'})


def arithmetic_status(state, check):
    """Execution and truth are distinct, including unavailable subprocesses."""
    if check:
        attempted = bool(check.get('lean_file') and check.get('lean_statement'))
        if check.get('failure_category') in {'INVALID_PROOF', 'PROCESS_ERROR'}:
            attempted = None
        if check.get('failure_category') == 'CLAIM_NOT_GROUNDED':
            attempted = False
        status = ('FORMAL_ERROR' if state == 'technical_error' else
                  'FORMAL_NOT_ATTEMPTED' if not attempted else
                  {'verified': 'FORMAL_VERIFIED', 'refuted': 'FORMAL_REFUTED'}.get(state, 'FORMAL_UNPROVED'))
        return status, attempted
    return ({'verified': 'DETERMINISTIC_VERIFIED', 'technical_error': 'DETERMINISTIC_ERROR'}
            .get(state, 'DETERMINISTIC_FAILED')), False


class StrongP2Checks(P2Checks):
    def observe(self, fact, record, status, *, formal=None, mechanism='canonical_equivalence', **metadata):
        if fact not in GAPS:
            return super().observe(fact, record, status, formal=formal, mechanism=mechanism, **metadata)
        if fact == 'b.integral_sum':
            # select() already required an attributed named integral_sum enum.
            # Verify the domain theorem independently of that enum's presence.
            form = record.canonical_form
            if (form.subject != 'integral_sum' or form.value.get('value_kind') != 'enum'
                    or form.value.get('value') != 'integer'):
                rows = [component('integrality', 'DETERMINISTIC_ERROR', 'invalid_integral_record')]
            else:
                rows = [check_integrality(dict(subject='S', terms=('left', 'center', 'right')))]
            decision = combine(rows, required=('integrality',))
            self.add(fact, [record], decision['state'], mechanism='deterministic', metadata=dict(
                checker_first_version=VERSION, source_span=record.source.raw_text,
                normalized_claim='S is the sum of three integer digits', components=rows,
                decision=decision, checker='check_integrality', semantic_authority=False))
            return
        # The legacy product producer couples arithmetic to its structural gate.
        # Separate those components here: a true 12*32=384 is true arithmetic
        # but still cannot establish the P2 product argument.
        if fact == 'c.counting_product':
            values = [rational_value(p) for p in record.canonical_form.value['structure']['expanded_parts']]
            status = 'unverified' if None in values else 'verified' if all(v == 384 for v in values) else 'refuted'
        # Preserve the exact existing arithmetic/proof lifecycle and diagnostics.
        super().observe(fact, record, status, formal=formal, mechanism=mechanism, **metadata)
        arithmetic = self.pending.pop()
        check = arithmetic['student_check']; state = arithmetic['verification'].status
        epistemic, attempted = arithmetic_status(state, check)
        rows = [component('arithmetic', epistemic, 'existing_exact_written_arithmetic',
            false=state == 'refuted', route='FORMAL' if check else 'DETERMINISTIC',
            formal_attempted=attempted, formal_candidate=bool(formal),
            formal_status=epistemic if check else 'FORMAL_NOT_ATTEMPTED',
            formal_absence_reason=None if check else 'disabled_or_no_renderable_written_equality',
            checker_result=check, verification_ref=arithmetic['verification'].artifact_ref)]
        key = fact.split('.', 1)[1]
        try:
            certificate = finite_certificate()
            rows.append(component('counting_components', 'DETERMINISTIC_VERIFIED',
                'exhaustive_finite_model_and_inverse', certificate=certificate))
            rows.append(argument_relation(key, record.canonical_form.value['expression']))
        except (ValueError, TypeError, KeyError, SyntaxError, RecursionError) as error:
            rows.append(component('counting_components', 'DETERMINISTIC_ERROR', type(error).__name__))
        decision = combine(rows)
        meta = dict(metadata, checker_first_version=VERSION, checker='P2CompositeCountingChecker',
            source_span=record.source.raw_text, normalized_claim=record.canonical_form.value['expression'],
            components=rows, decision=decision, semantic_authority=False,
            justification_status='COMBINATORIAL_JUSTIFICATION_SUPPORTED' if decision['state'] == 'verified'
                                 else 'COMBINATORIAL_JUSTIFICATION_NOT_SUPPORTED',
            counting_components_verified=any(r['name'] == 'counting_components' and r['status'] == 'DETERMINISTIC_VERIFIED' for r in rows),
            arithmetic_verified=epistemic in {'FORMAL_VERIFIED', 'DETERMINISTIC_VERIFIED'},
            relation_supported=any(r['name'] == 'relation' and r['status'] == 'DETERMINISTIC_VERIFIED' for r in rows))
        # A mixed certificate is not mislabeled as a Lean proof of the whole argument.
        refs = [self.records[i] for i in arithmetic['source_claim_ids']]
        self.add(fact, refs, decision['state'], mechanism='deterministic', metadata=meta)


def audit_p2_checker_first(solution, *, solution_id='p2-checker-first', use_lean=True, run_id=None):
    """Separate entry point. No global registry switch, model call or new scoring.

Only explicit existing typed notation/confirmed diagrams is accepted. All model
certificates remain problem-context evidence, distinct from student source spans.
"""
    with legacy.supplement_scope(deterministic_only):
        texts, diagrams = split_p2_input(solution)
        digital = collect_tme2_p2_text(texts)
        if collect_tme2_p2_text(texts) != digital:
            raise ValueError('Digital source/claim projection changed')
        checks = StrongP2Checks(digital, solution_id, use_lean, run_id)
        checks.a(); checks.b(); checks.c(); checks.diagrams(diagrams)
        bundle = checks.finish()
    config = load_pauta(ROOT/'examples/pautas/tme2_problem2.v1.json')
    bridge = bridge_tme2_p2(config, bundle)
    assessment = PautaEngine().evaluate(config, bridge.evidence)
    verification = []
    for fact in bundle.facts:
        details = fact.metadata
        verification.append(dict(obligation_id=fact.fact_id,
            verification_source=fact.verification_source, state=fact.verification.status,
            source_claim_ids=list(fact.source_claim_ids), metadata=details,
            checker_result=fact.student_check))
    awarded = [dict(obligation_id=e.obligation_id, eligible=e.status == 'supported',
                    reason=e.metadata['reason'], status=e.status, evidence_refs=list(e.evidence_refs))
               for e in bridge.evidence.obligations]
    return dict(version=VERSION, mode='P2_CHECKER_FIRST', use_lean=use_lean,
        **ScoreClosurePolicy().close(assessment), bridge=bridge.model_dump(mode='json'),
        assessment=assessment.model_dump(mode='json'), checks=verification, awards=awarded,
        semantic_checker_enabled=False)
