"""P4 controlled DIGITAL solutions, attribution and real-proof contract tests."""
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from confia_lean_auditor.claims.common.adapters import project_student_claim
from confia_lean_auditor.lean.student_claim_checkers.real_algebra import lean_real_expression
from confia_lean_auditor.lean.student_claim_checkers.tme2_p4 import verify_tme2_p4_digital, sum_development
from confia_lean_auditor.rubric.pauta import load_pauta
from confia_lean_auditor.rubric.pauta.bridge import record_fingerprint
from confia_lean_auditor.rubric.pauta.tme2_p4 import bridge_tme2_p4, TME2_P4_OBLIGATIONS
from confia_lean_auditor.student_claims.tme2_p4_digital import collect_tme2_p4_digital
from confia_lean_auditor.tme.registry import audit_tme, TME_PROBLEMS
from confia_lean_auditor.tme.p4_geometry import P4Geometry

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / 'tests/fixtures/tme2_p4_digital/cases.json').read_text())


def case_text(identifier):
    return next(c['text'] for c in CASES if c['id'] == identifier)


def run(item, text, *, lean=False):
    return audit_tme('TME2026P4', {item: text}, solution_id='p4-test', use_lean=lean)


def evidence(bridge, key):
    return next(e for e in bridge.evidence.obligations if e.obligation_id == key)


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['id'])
def test_controlled_cases_and_source_chain(case):
    bridge, result = run(case['item'], case['text'])
    item = result.items['abc'.index(case['item'])]
    assert item.points_awarded == case['points']
    if 'selected_path' in case:
        assert item.selected_method_path == case['selected_path']
    source = collect_tme2_p4_digital({case['item']: case['text']}).source_text
    records = {r.record_id: r for r in bridge.auditor.records}
    for fact in bridge.auditor.facts:
        assert 'points' not in fact.metadata
        for identifier in fact.source_claim_ids:
            record = records[identifier]
            assert record.source.attributable and record.source.grounding_status == 'grounded'
            assert source[record.source.source_start:record.source.source_end] == record.source.raw_text
            assert record.canonical_form and record.provenance.origin == 'student_explicit'
            assert fact.record_fingerprints[identifier] == record_fingerprint(record)
            assert fact.verification in record.verification_results
    if item.points_awarded:
        assert item.credit_evidence_refs


@pytest.mark.parametrize('b', ['b_official', 'b_parallelogram'])
@pytest.mark.parametrize('c', ['c_complete', 'c_cases', 'c_cases_reversed'])
def test_complete_alternative_solutions_score_twenty(b, c):
    _, result = audit_tme('TME2026P4', {'a': case_text('a_complete'), 'b': case_text(b),
        'c': case_text(c)}, use_lean=False)
    assert result.score == 20 and not result.needs_review


@pytest.mark.parametrize('prefix', ['Não é verdade:\n', 'Suponha:\n', 'Tentativa descartada:\n', 'Citação:\n'])
@pytest.mark.parametrize('item,case', [('a','a_complete'), ('b','b_official'), ('c','c_complete')])
def test_hypotheses_negations_and_rejections_do_not_gain_credit(prefix, item, case):
    bridge, result = run(item, prefix + case_text(case))
    assert result.items['abc'.index(item)].points_awarded == 0
    assert not bridge.auditor.facts


def test_correct_conclusion_then_explicitly_rejected():
    bridge, result = run('c', case_text('c_complete') + '\nEsta conclusão foi rejeitada.')
    assert result.items[2].points_awarded == 0
    assert not bridge.auditor.facts


@pytest.mark.parametrize('text', ['3*x+3*(6-x)=18', 'perimetro desconhecido: 3*x+3*(6-x)=18',
    'O desenho mostra a resposta correta: 18', 'shaded_sum: 18=18'])
def test_unsupported_subjects_and_final_values_do_not_supply_geometry(text):
    _, result = run('a', text)
    assert result.items[0].points_awarded == 0


@pytest.mark.parametrize('text', ['__import__("os")', 'x/0', 'x/c', 'sqrt(x)', 'x^100', '0.333...', 'x; exact True.intro'])
def test_real_renderer_rejects_unsupported_or_unsafe_expressions(text):
    assert lean_real_expression(text) is None


def test_renderer_preserves_signs_real_domain_and_exact_fractions():
    assert lean_real_expression('-5/3') == '((-(5 : ℝ)) / (3 : ℝ))'
    assert lean_real_expression('(3*x)^2') == '(((3 : ℝ) * x) ^ 2)'
    assert 'ℤ' not in lean_real_expression('13/3')


def test_written_sum_not_numeric_total_and_expansion_supported():
    assert sum_development('3*x+18-3*x', ['3*x', '3*(6-x)'])
    assert not sum_development('18', ['3*x', '3*(6-x)'])
    assert not sum_development('3*x-3*(6-x)', ['3*x', '3*(6-x)'])


def test_geometry_is_sourced_and_computed_separately_from_formal_algebra():
    geometry = P4Geometry()
    assert geometry.lengths['AP'] == '(6-x)'
    assert geometry.perimeter('PBQ') == 'x+x+x'
    assert 'P in segment AB' in geometry.domain
    assert P4Geometry(side=7).lengths['QR'] == '(7-x)'
    bridge, _ = run('a', case_text('a_complete'))
    fact = next(f for f in bridge.auditor.facts if f.fact_id == 'a.triangle_pbq')
    assert fact.verification_source == 'deterministic'
    assert fact.metadata['verification_kind'] == 'deterministic_geometry'
    assert not fact.student_check


def test_conflicting_values_are_not_silently_selected():
    bridge, result = run('b', case_text('b_official') + '\nAP: x')
    assert evidence(bridge, 'b.ap').status == 'indeterminate'
    assert result.items[1].points_awarded == 4


@pytest.mark.parametrize('item,text,key', [
    ('b', 'AP: y', 'b.ap'),
    ('a', 'shaded_sum: h+c=18', 'a.shaded_sum'),
    ('c', 'h: h', 'c.h'),
    ('c', 'case_3x_root: y', 'c.case_3x_root'),
    ('c', 'x_candidates: {x^2,x*x,13}', 'c.x_candidates'),
])
def test_unbound_variables_and_unresolved_values_are_not_refutations(item, text, key):
    bridge, _ = run(item, text)
    assert evidence(bridge, key).status == 'indeterminate'


@pytest.mark.parametrize('field', ['source', 'route', 'canonical'])
def test_rebuilt_source_rejects_annotation_tampering(field):
    digital = collect_tme2_p4_digital({'b': 'AP: 6-x'})
    record = digital.records[0]
    if field == 'source':
        digital = replace(digital, source_text=digital.source_text.replace('6-x','5-x'))
    elif field == 'route':
        digital = replace(digital, records=(record.model_copy(update={'rubric_links': ('a',)}),))
    else:
        form = record.canonical_form.model_copy(update={'subject': 'pq'})
        digital = replace(digital, records=(record.model_copy(update={'canonical_form': form}),))
    with pytest.raises(ValueError, match='projection changed'):
        verify_tme2_p4_digital(digital, 'tampered', use_lean=False)


@pytest.mark.parametrize('outcome', ['verified', 'refuted', 'technical_error', 'unverified'])
def test_native_formal_gate_technical_failures_and_payload_binding(monkeypatch, tmp_path, outcome):
    import confia_lean_auditor.lean.student_claim_checkers.real_algebra as module
    monkeypatch.setattr(module, 'CHECK_DIR', tmp_path)
    calls = []
    def runner(path, timeout_seconds):
        calls.append(path)
        negative = path.stem.endswith('_refutation')
        success = outcome == 'verified' or outcome == 'refuted' and negative
        stderr = 'unknown identifier deliberate' if outcome == 'technical_error' else 'unsolved goals'
        return subprocess.CompletedProcess([], 0 if success else 1, '', '' if success else stderr)
    monkeypatch.setattr(module, '_run_lean_file', runner)
    bridge, result = run('a', 'shaded_sum: 3*x+3*(6-x)=18', lean=True)
    fact = next(f for f in bridge.auditor.facts if f.student_check)
    assert fact.verification.status == outcome
    assert evidence(bridge, 'a.shaded_sum').status == {'verified':'supported','refuted':'refuted',
        'technical_error':'technical_error','unverified':'indeterminate'}[outcome]
    if outcome == 'technical_error':
        assert len(calls) == 1 and result.items[0].points_awarded is None
    assert fact.student_check['data']['number_domain'] == 'R'
    native = next(r for r in bridge.auditor.records if r.record_id.startswith('native:real-'))
    with pytest.raises(ValueError, match='native'):
        project_student_claim(native, solution_text=collect_tme2_p4_digital({'a':'shaded_sum: 3*x+3*(6-x)=18'}).source_text)
    altered = fact.model_copy(update={'student_check':{**fact.student_check, 'data':{
        **fact.student_check['data'], 'number_domain':'Z'}}})
    bundle = bridge.auditor.model_copy(update={'facts': (altered,)})
    config = load_pauta(ROOT / 'examples/pautas/tme2_problem4.v1.json')
    assert evidence(bridge_tme2_p4(config,bundle), 'a.shaded_sum').status == 'indeterminate'


def test_contextual_proof_requires_existing_relations(monkeypatch):
    import confia_lean_auditor.lean.student_claim_checkers.tme2_p4 as module
    def forbidden(*args, **kwargs):
        pytest.fail('Missing context cannot become a student Lean derivation')
    monkeypatch.setattr(module, 'check_real_record', forbidden)
    bridge, result = run('c', 'h: 13\nc: 5\nx_candidates: {5/3,13/3}', lean=True)
    assert result.items[2].points_awarded == 2
    assert evidence(bridge, 'c.h_plus_c').status == 'indeterminate'
    assert all(f.verification_source != 'student_lean' for f in bridge.auditor.facts)


def test_formal_projection_records_assertion_and_actual_context(monkeypatch, tmp_path):
    import confia_lean_auditor.lean.student_claim_checkers.real_algebra as module
    monkeypatch.setattr(module, 'CHECK_DIR', tmp_path)
    monkeypatch.setattr(module, '_run_lean_file', lambda *a, **kw: subprocess.CompletedProcess([],0,'',''))
    lifecycle = module.evaluate_student_proof
    def inspect_gate(**kwargs):
        claim, valid = kwargs['claim'], kwargs['grounding_validator']
        assert valid(claim)
        assert not valid(replace(claim, data={**claim.data, 'number_domain': 'Z'}))
        assert not valid(replace(claim, raw_text='a different assertion'))
        return lifecycle(**kwargs)
    monkeypatch.setattr(module, 'evaluate_student_proof', inspect_gate)
    bridge, _ = run('c', case_text('c_complete'), lean=True)
    checks = {f.fact_id:f for f in bridge.auditor.facts if f.student_check}
    assert set(checks) == {'c.exclude_12','c.h','c.c','c.x_candidates'}
    assert '¬' in checks['c.exclude_12'].student_check['lean_statement']
    assert 'h+c=18 → h^2=c^2+144' in checks['c.h'].student_check['lean_statement']
    assert checks['c.h'].metadata['formal_context']['student_assumption_fact_ids'] == ['c.h_plus_c','c.pythagoras']
    assert 'engine_derived_premise' in checks['c.x_candidates'].metadata['formal_context']
    assert all(evidence(bridge,k).status == 'supported' for k in checks)


@pytest.mark.parametrize('case,fact_id,literal', [
    ('c_local_error', 'c.h', 'h=(12 : ℝ)'),
    ('c_wrong_roots', 'c.x_candidates', 'x=(2 : ℝ) ∨ x=(4 : ℝ)'),
])
def test_negative_candidates_formalize_the_actual_student_values(monkeypatch, tmp_path, case, fact_id, literal):
    import confia_lean_auditor.lean.student_claim_checkers.real_algebra as module
    monkeypatch.setattr(module, 'CHECK_DIR', tmp_path)
    def runner(path, **kwargs):
        negative = path.stem.endswith('_refutation')
        return subprocess.CompletedProcess([], 0 if negative else 1, '' if negative else 'error: unsolved goals', '')
    monkeypatch.setattr(module, '_run_lean_file', runner)
    bridge, _ = run('c', case_text(case), lean=True)
    fact = next(f for f in bridge.auditor.facts if f.fact_id == fact_id)
    assert literal in fact.student_check['lean_statement']
    assert fact.verification.status == 'refuted' and fact.student_check['refutation_verified']
    source = Path(fact.student_check['lean_file']).read_text()
    assert ('try linarith' in source if fact_id == 'c.h' else '| skip' in source)
    assert literal in Path(fact.student_check['refutation_lean_file']).read_text()


def test_registry_is_opt_in_and_all_obligations_covered():
    from confia_lean_auditor.core.problem_catalog import CATALOG
    assert 'TME2026P4' in TME_PROBLEMS and 'TME2026P4' not in CATALOG
    with pytest.raises(ValueError):
        audit_tme('TME2026P6', {'a':'18'})
    covered = set()
    for case in CASES:
        bridge, _ = run(case['item'],case['text'])
        covered.update(e.obligation_id for e in bridge.evidence.obligations if e.status == 'supported')
    assert covered == set(TME2_P4_OBLIGATIONS)
