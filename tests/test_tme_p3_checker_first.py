"""Bounded P3 checker contracts; no LLM and no changed historical expectations."""
from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path

import pytest
from confia_lean_auditor.experimental.tme_p3_checker_first.components import (
    finite_certificate, check_event_set, count_relation, probability_relation, combine,
)
from confia_lean_auditor.experimental.tme_p3_checker_first.engine import audit_p3_checker_first, GAPS
from confia_lean_auditor.experimental.tme_p3_checker_first.registry import coverage_rows
from confia_lean_auditor.tme.p3_machine import load_machine
from confia_lean_auditor.tme.obligation_experiment import primary_audit

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT/'tests/fixtures/tme2_p3_digital/cases.json').read_text())


@pytest.fixture
def machine():
    return load_machine(ROOT/'examples/pautas/tme2_problem3.machine.v1.json')


def run(text, item='b', **kw):
    return audit_p3_checker_first({item: text}, solution_id='p3-strengthening-test', use_lean=False, **kw)


def result(r, oid):
    return next(x for x in r['checks'] if x['obligation_id'] == oid)


@pytest.mark.parametrize('expr', ['6*6=36', '6^2=36', '36=6*6', '(6)*(6)', '6*(3+3)=36'])
def test_written_sample_space(expr):
    r=run('pares_ordenados: '+expr)
    assert r['score']==2 and result(r,'b.ordered_pairs')['status']=='COMPOSITE_VERIFIED'
    assert result(r,'b.ordered_pairs')['metadata']['argument_satisfied']


@pytest.mark.parametrize('expr', ['2*5=10', '5*2=10', '2*(6-1)=10', '10=2*5', '2*5'])
def test_written_different_partition(expr):
    r=run('favoraveis_distintos: '+expr)
    assert r['score']==2 and result(r,'b.different_favorable')['status']=='COMPOSITE_VERIFIED'


@pytest.mark.parametrize('key,expr,oid', [
 ('pares_ordenados','36','b.ordered_pairs'),('pares_ordenados','36=36','b.ordered_pairs'),
 ('pares_ordenados','12*3=36','b.ordered_pairs'),
 ('favoraveis_distintos','10','b.different_favorable'),('favoraveis_distintos','10=10','b.different_favorable'),
 ('favoraveis_distintos','4+6=10','b.different_favorable')])
def test_true_value_does_not_establish_counting_relation(key,expr,oid):
    r=run(key+': '+expr);v=result(r,oid)
    assert r['score']==0 and v['status']=='COMPOSITE_INCOMPLETE'
    assert v['metadata']['components'][0]['status']=='DETERMINISTIC_VERIFIED'
    assert v['state']=='unverified'


@pytest.mark.parametrize('text,oid',[
 ('pares_ordenados: 6*5=30','b.ordered_pairs'),('pares_ordenados: 35','b.ordered_pairs'),
 ('pares_ordenados: 2*5=10','b.ordered_pairs'),
 ('favoraveis_distintos: 2*6=12','b.different_favorable'),('favoraveis_distintos: 9','b.different_favorable'),
 ('favoraveis_distintos: 6*6=36','b.different_favorable'),
 ('segunda_branca: 1/2','b.second_white_probability'),
 ('segunda_branca: (9+2)/36=11/36','b.second_white_probability'),
 ('segunda_branca: 9/36+2/36=11/36','b.second_white_probability'),
 ('segunda_branca: (10+1)/35=11/36','b.second_white_probability')])
def test_false_count_case_or_partition_is_refuted(text,oid):
    r=run(text);v=result(r,oid)
    assert r['score']==0 and v['status']=='COMPOSITE_FAILED' and v['state']=='refuted'


@pytest.mark.parametrize('expr', ['11/36','22/72','11/36=11/36'])
def test_existing_result_credit_has_separate_non_argument_route(expr):
    r=run('segunda_branca: '+expr);v=result(r,'b.second_white_probability')
    assert r['score']==2 and v['metadata']['verification_route']=='result_value'
    assert v['metadata']['result_credit_only'] and not v['metadata']['argument_satisfied']
    assert [a['obligation_id'] for a in r['awards'] if a['eligible']]==['b.second_white_probability']
    assert v['metadata']['components'][0]['formal_status']=='FORMAL_NOT_ATTEMPTED'


@pytest.mark.parametrize('expr', ['(10+1)/36=11/36','(1+10)/36=11/36','10/36+1/36=11/36','(10+1)/36'])
def test_total_partition_is_checked_without_requiring_other_awards(expr):
    r=run('segunda_branca: '+expr);v=result(r,'b.second_white_probability')
    assert r['score']==2 and v['metadata']['argument_satisfied']
    assert not v['metadata']['result_credit_only']


@pytest.mark.parametrize('expr', ['(12-1)/36=11/36','11/(30+6)=11/36'])
def test_unrecognized_development_does_not_fall_back_to_final_number(expr):
    r=run('segunda_branca: '+expr)
    assert r['score']==0 and result(r,'b.second_white_probability')['status']=='COMPOSITE_INCOMPLETE'


@pytest.mark.parametrize('wrong', ['favoraveis_distintos: 12','repeticao_branca: {1}','pares_ordenados: 30'])
def test_correct_total_cannot_silently_bypass_false_explicit_context(wrong):
    r=run(wrong+'\nsegunda_branca: 11/36')
    assert not next(a for a in r['awards'] if a['obligation_id']=='b.second_white_probability')['eligible']
    assert any(c['obligation_id']=='b.second_white_probability' for c in r['conflicts'])
    assert r['review_recommended']


@pytest.mark.parametrize('order', [False,True])
def test_false_and_true_same_claim_remain_conflicting(order):
    lines=['segunda_branca: 11/36','segunda_branca: (9+2)/36=11/36']
    r=run('\n'.join(lines[::-1] if order else lines))
    assert r['score']==0 and r['conflicts']
    assert {v['state'] for v in r['checks']}=={'verified','refuted'}


@pytest.mark.parametrize('item', ['a','c'])
@pytest.mark.parametrize('text', ['pares_ordenados: 6*6=36','favoraveis_distintos: 2*5=10','segunda_branca: (10+1)/36=11/36'])
def test_true_claim_in_wrong_item_is_not_credited(item,text):
    r=run(text,item=item)
    assert r['score']==0 and not any(x['obligation_id'] in GAPS for x in r['checks'])


@pytest.mark.parametrize('prefix',['Suponha:\n','Não é verdade:\n','Tentativa descartada:\n'])
def test_context_is_not_promoted(prefix):
    assert run(prefix+'pares_ordenados: 6*6=36\nfavoraveis_distintos: 2*5=10')['score']==0


def test_certificate_simulates_every_event_and_probability(machine):
    c=finite_certificate(machine)
    assert c['counts']==dict(sample=36,different=10,same=1,favorable=11)
    assert c['same_white']==[[6,6]]
    assert len(c['events'])==len({tuple(e['pair']) for e in c['events']})==36
    assert sum(Fraction(e['probability']) for e in c['events'])==1
    for e in c['events']:
        i,j=e['pair'];stacks=[list(s) for s in machine.stacks]
        assert stacks[i-1].pop(0)==e['first_color'] and stacks==e['stacks_after_first']
        assert stacks[j-1].pop(0)==e['second_color'] and stacks==e['stacks_after_second']
    assert c['second_white_probability']=='11/36'


@pytest.mark.parametrize('kind,key',[('sample','ordered_pairs'),('different','different_white'),('same','same_white'),('favorable','favorable_pairs')])
def test_typed_event_subsets_match_model_not_number(kind,key,machine):
    c=finite_certificate(machine);pairs=c[key]
    assert check_event_set(kind,pairs,machine)['status']=='DETERMINISTIC_VERIFIED'
    assert check_event_set(kind,pairs[:-1],machine)['status']=='DETERMINISTIC_FAILED'
    assert check_event_set(kind,pairs+[pairs[0]],machine)['status']=='DETERMINISTIC_FAILED'
    other=c['repeated_pairs'] if kind!='same' else c['different_white']
    assert check_event_set(kind,other,machine)['status']=='DETERMINISTIC_FAILED'


@pytest.mark.parametrize('pairs', [[[True,1]],[[7,1]],[[1]],'36'])
def test_bad_event_envelope_is_error_not_refutation(pairs,machine):
    r=check_event_set('sample',pairs,machine)
    assert r['status']=='DETERMINISTIC_ERROR' and not r['mathematical_refutation']


def test_nonwhite_subset_with_same_cardinality_is_rejected(machine):
    c=finite_certificate(machine);pairs=list(c['different_white']);pairs[0]=[1,3]
    assert len(pairs)==10 and check_event_set('different',pairs,machine)['status']=='DETERMINISTIC_FAILED'


def test_model_mutation_changes_certificate_and_expected_probability(machine):
    other=replace(machine,stacks=machine.stacks[:-1]+(('black','black'),))
    c=finite_certificate(other)
    assert c['counts']['same']==0 and c['counts']['favorable']==10
    assert c['second_white_probability']=='5/18'
    assert run('segunda_branca: (10+0)/36=5/18',machine=other)['score']==2
    assert run('segunda_branca: 11/36',machine=other)['score']==0


def test_model_mutation_changes_initial_white_factors(machine):
    other=replace(machine,stacks=(('gray','black'),)+machine.stacks[1:])
    c=finite_certificate(other)
    assert len(c['initially_white'])==1 and c['counts']['different']==5
    assert run('favoraveis_distintos: 1*5=5',machine=other)['score']==2
    assert run('favoraveis_distintos: 2*5=10',machine=other)['score']==0


def test_errors_stay_technical_and_score_numeric(monkeypatch):
    import confia_lean_auditor.experimental.tme_p3_checker_first.engine as e
    def fail(_):raise ValueError('diagnostic_certificate_error')
    monkeypatch.setattr(e,'finite_certificate',fail)
    r=run('pares_ordenados: 6*6=36\nsegunda_branca: 11/36')
    assert r['technical_uncertainty'] and r['score']==0.0
    assert {v['status'] for v in r['checks']}=={'COMPOSITE_ERROR'}


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id'])
def test_historical_baseline_and_unchanged_ten_obligations(case):
    items={case['item']:case['text']}
    before=primary_audit('TME2026P3',items,solution_id='preserve',use_lean=False)
    strong=audit_p3_checker_first(items,solution_id='preserve',use_lean=False)
    after=primary_audit('TME2026P3',items,solution_id='preserve',use_lean=False)
    assert [x.model_dump(mode='json') for x in before]==[x.model_dump(mode='json') for x in after]
    assert float(before[1].items['abc'.index(case['item'])].points_awarded)==case['points']
    old={e.obligation_id:e.status for e in before[0].evidence.obligations}
    for a in strong['awards']:
        if a['obligation_id'] not in GAPS:assert a['status']==old[a['obligation_id']]
    strengthened_scores={'b_wrong_favorable':0,'b_incomplete_tree':0,'b_wrong_branch':0}
    assert strong['score']==strengthened_scores.get(case['id'],case['points'])


def test_all_13_obligations_covered_without_semantic_authority():
    positive=set()
    for c in CASES:
        r=run(c['text'],item=c['item'])
        positive.update(a['obligation_id'] for a in r['awards'] if a['eligible'])
        assert r['semantic_checker_enabled'] is False and isinstance(r['score'],float)
    rows=coverage_rows()
    assert positive=={r['obligation_id'] for r in rows} and len(rows)==13
    assert all(r['coverage'] in {'COMPOSITE_STRONG','DETERMINISTIC_STRONG','FORMAL_STRONG'} and not r['semantic_allowed'] for r in rows)


def test_value_route_never_supplies_argumentative_awards():
    r=run('pares_ordenados: 36\nfavoraveis_distintos: 10\nrepeticao_branca: {6}\nsegunda_branca: 11/36')
    assert r['score']==4
    assert {a['obligation_id'] for a in r['awards'] if a['eligible']}=={'b.same_compartment','b.second_white_probability'}


def test_caller_certificate_cannot_replace_trusted_machine(machine):
    forged={"choice_count":6,"different_white":[[1,3]]}
    assert check_event_set("different",[[1,3]],forged)["status"]=="DETERMINISTIC_ERROR"
    assert check_event_set("different",[[1,3]],machine)["status"]=="DETERMINISTIC_FAILED"
