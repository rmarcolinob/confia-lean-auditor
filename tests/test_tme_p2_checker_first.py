"""Four P2 gaps: independent mathematics, sufficiency, provenance and isolation."""
import json
from pathlib import Path
from collections import Counter

import pytest

from confia_lean_auditor.experimental.tme_p2_checker_first import components as comp
from confia_lean_auditor.experimental.tme_p2_checker_first.engine import audit_p2_checker_first, arithmetic_status, GAPS
from confia_lean_auditor.experimental.tme_p2_checker_first.registry import coverage_rows
from confia_lean_auditor.tme.obligation_experiment import primary_audit

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT/'tests/fixtures/tme2_p2_digital/cases.json').read_text())


def run(text, *, item='c', lean=False):
    return audit_p2_checker_first({item: text}, use_lean=lean, solution_id='strong-test')


def obligation(result, oid):
    return next(e for e in result['bridge']['evidence']['obligations'] if e['obligation_id'] == oid)


@pytest.mark.parametrize('payload,status,false', [
    ({'subject':'S','terms':('left','center','right')}, 'DETERMINISTIC_VERIFIED', False),
    ({'subject':'S','terms':('1','5','9')}, 'DETERMINISTIC_VERIFIED', False),
    ({'subject':'S','terms':('2/2','5','9')}, 'DETERMINISTIC_VERIFIED', False),
    ({'subject':'S','terms':('1','2','1/2')}, 'DETERMINISTIC_FAILED', True),
    ({'subject':'S','terms':('0','2','3')}, 'DETERMINISTIC_FAILED', True),
    ({'subject':'S','terms':('1','2')}, 'DETERMINISTIC_NOT_ATTEMPTED', False),
    ({'subject':'S','terms':('x','2','3')}, 'DETERMINISTIC_NOT_ATTEMPTED', False),
    ({'subject':'other','terms':('1','2','3')}, 'DETERMINISTIC_ERROR', False),
    ({'subject':'S','terms':(True,'2','3')}, 'DETERMINISTIC_ERROR', False),
    ({'subject':'S','terms':('1','2','3'),'verified':True}, 'DETERMINISTIC_ERROR', False),
])
def test_integrality_positive_false_incomplete_and_invalid(payload,status,false):
    result = comp.check_integrality(payload)
    assert result['status'] == status and result['mathematical_refutation'] is false


def test_integrality_is_checked_and_the_existing_center_dependency_is_preserved():
    text = 'balance_relation: 4*S=45+3*x\nintegral_sum: integer\ncenters: {1,5,9}'
    r = run(text, item='b')
    assert r['score'] == 4
    fact = next(c for c in r['checks'] if c['obligation_id'] == 'b.integral_sum')
    assert fact['metadata']['components'][0]['reason'] == 'integer_sum_closure'
    assert fact['metadata']['components'][0]['symbolic_integer_digits'] == ['left','center','right']
    assert obligation(run('centers: {1,5,9}',item='b'),'b.centers')['status'] == 'indeterminate'
    assert obligation(run('integral_sum: unknown',item='b'),'b.integral_sum')['status'] == 'indeterminate'


def test_exhaustive_certificate_proves_bijection_not_only_generator_size():
    c = comp.finite_certificate()
    assert (c['distributions'],c['orientations'],c['total']) == (24,16,384)
    assert c['exhaustive_candidate_states'] == 40320
    assert c['injective'] and c['surjective'] and c['inverse_verified']
    assert c['pairs'] == [[1,8],[2,7],[3,6],[4,5]]
    c['total'] = 1
    assert comp.finite_certificate()['total'] == 384


SPECS = [
    ('pair_permutations', 2, '4!=24', '24', '3!=6', '4!=20', '2^3*3=24', '4*3!=24'),
    ('pair_orientations', 2, '2^4=16', '16', '2^3=8', '2^4=8', '4+12=16', '2*2*2*2=16'),
    ('counting_product', 5, '24*16=384', '384', '24', '24*16=364', '12*32=384', '(2*2*2*2)*(4*3!)=384'),
]


@pytest.mark.parametrize('spec',SPECS,ids=[s[0] for s in SPECS])
@pytest.mark.parametrize('variant',['complete','number_only','partial','false_subclaim','wrong_argument','equivalent','irrelevant','hypothetical','negated'])
def test_each_composite_required_cases(spec,variant):
    key,points,complete,number,partial,false,wrong,equivalent = spec
    expr = dict(complete=complete, number_only=number, partial=partial, false_subclaim=false,
                wrong_argument=wrong, equivalent=equivalent, irrelevant=complete,
                hypothetical=complete, negated=complete)[variant]
    text = ('unrelated' if variant == 'irrelevant' else key)+': '+expr
    if variant == 'hypothetical': text = 'Suponha:\n'+text
    if variant == 'negated': text = 'Não é verdade:\n'+text
    r = run(text)
    expected = points if variant in {'complete','equivalent'} else 0
    assert r['score'] == expected
    e = obligation(r,'c.'+key)
    if expected:
        assert e['status'] == 'supported'
        metadata = next(c['metadata'] for c in r['checks'] if c['obligation_id'] == 'c.'+key)
        assert metadata['counting_components_verified'] and metadata['arithmetic_verified'] and metadata['relation_supported']
        assert metadata['justification_status'] == 'COMBINATORIAL_JUSTIFICATION_SUPPORTED'
    if variant == 'false_subclaim': assert e['status'] == 'refuted'
    if variant in {'number_only','wrong_argument'}:
        metadata = next(c['metadata'] for c in r['checks'] if c['obligation_id'] == 'c.'+key)
        assert metadata['arithmetic_verified'] and not metadata['relation_supported']
        assert e['status'] == 'indeterminate'  # Not a false arithmetic assertion.


@pytest.mark.parametrize('key',['integral_sum','pair_permutations','pair_orientations','counting_product'])
@pytest.mark.parametrize('prefix',['Suponha:\n','Não é verdade:\n','Tentativa descartada:\n','Citação:\n'])
def test_context_never_grants_gap_credit(key,prefix):
    text = key+': '+dict(integral_sum='integer',pair_permutations='4!=24',pair_orientations='2^4=16',counting_product='24*16=384')[key]
    item = 'b' if key == 'integral_sum' else 'c'
    assert obligation(run(prefix+text,item=item),item+'.'+key)['status'] != 'supported'


@pytest.mark.parametrize('status,false',[('FORMAL_REFUTED',True),('DETERMINISTIC_FAILED',True),('FORMAL_UNPROVED',False),('FORMAL_ERROR',False),('FORMAL_NOT_ATTEMPTED',False)])
def test_semantic_input_cannot_override_refutation_or_missing_mathematical_checker(status,false):
    rows = [comp.component('arithmetic',status,'test',false=false),
            comp.component('counting_components','DETERMINISTIC_VERIFIED','test'),
            comp.component('relation','DETERMINISTIC_VERIFIED','test')]
    r = comp.combine(rows,semantic_decision={'sufficiency':'sufficient','confidence':'high'})
    assert r['state'] != 'verified' and not r['semantic_authority']
    if false: assert r['state'] == 'refuted'


def test_semantic_input_cannot_supply_a_missing_component():
    rows = [comp.component('arithmetic','FORMAL_VERIFIED','test')]
    assert comp.combine(rows,semantic_decision={'sufficiency':'sufficient'})['state'] == 'unverified'


@pytest.mark.parametrize('check,state,status,attempted',[
    (None,'verified','DETERMINISTIC_VERIFIED',False),
    ({'lean_file':'x','lean_statement':'P'},'unverified','FORMAL_UNPROVED',True),
    ({'lean_file':None,'lean_statement':'P','failure_category':'CLAIM_NOT_GROUNDED'},'unverified','FORMAL_NOT_ATTEMPTED',False),
    ({'lean_file':'x','lean_statement':'P','failure_category':'UNKNOWN_IDENTIFIER'},'technical_error','FORMAL_ERROR',True),
    ({'lean_file':'x','lean_statement':'P','failure_category':'PROCESS_ERROR'},'technical_error','FORMAL_ERROR',None),
])
def test_execution_states_are_not_conflated(check,state,status,attempted):
    assert arithmetic_status(state,check) == (status,attempted)


def test_no_double_counting_and_numeric_score():
    r = run('pair_permutations: 4!=24\npair_orientations: 2^4=16\ntotal: 384\ncounting_product: 24*16=384')
    assert r['score'] == 5 and isinstance(r['score'],float)
    assert r['assessment']['items'][2]['children'][2]['selected_method_path'] in {'c.factorized_count_path','c.direct_product_path'}


def test_checker_error_is_visible_and_numeric_view_is_only_known_points(monkeypatch):
    from confia_lean_auditor.experimental.tme_p2_checker_first import engine
    def broken(): raise ValueError('finite_certificate_failure')
    monkeypatch.setattr(engine,'finite_certificate',broken)
    r = run('pair_permutations: 4!=24')
    assert r['score'] == 0 and r['technical_uncertainty'] and r['review_recommended']
    assert r['assessment']['score'] is None and r['score_closure']['applied']
    assert obligation(r,'c.pair_permutations')['status'] == 'technical_error'


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id'])
def test_original_p2_regressions_and_nineteen_strong_checkers_are_preserved(case):
    solution=case.get('solution',{case['item']:case['text']})
    before,score=primary_audit('TME2026P2',solution,solution_id=case['id'],use_lean=False)
    strong=audit_p2_checker_first(solution,solution_id=case['id'],use_lean=False)
    after,again=primary_audit('TME2026P2',solution,solution_id=case['id'],use_lean=False)
    assert before.model_dump(mode='json') == after.model_dump(mode='json')
    assert score.model_dump(mode='json') == again.model_dump(mode='json')
    assert float(score.items['abc'.index(case['item'])].points_awarded) == case['points']
    assert strong['score'] == float(score.score)
    old={e.obligation_id:e.model_dump(mode='json') for e in before.evidence.obligations if e.obligation_id not in GAPS}
    new={e['obligation_id']:e for e in strong['bridge']['evidence']['obligations'] if e['obligation_id'] not in GAPS}
    assert old == new


def test_checker_first_does_not_activate_llm_supplement(monkeypatch):
    from confia_lean_auditor.student_claims import semantic
    monkeypatch.setenv('CONFIA_TME_SEMANTIC_ENABLED','1')
    def forbidden(*args,**kwargs): pytest.fail('no LLM during checker-first')
    monkeypatch.setattr(semantic,'request_candidates',forbidden)
    assert run('counting_product: 24*16=384')['score'] == 5


def test_matrix_is_complete_and_has_no_semantic_route_or_gap():
    rows=coverage_rows()
    assert len(rows)==23 and len({r['obligation_id'] for r in rows})==23
    assert Counter(r['coverage'] for r in rows)=={'FORMAL_STRONG':6,'DETERMINISTIC_STRONG':14,'COMPOSITE_STRONG':3}
    assert all(not r['semantic_allowed'] for r in rows)
