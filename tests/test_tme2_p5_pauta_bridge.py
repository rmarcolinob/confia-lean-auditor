"""P5 arithmetic, student-argument gates, unordered lists and conditional credit."""
import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from confia_lean_auditor.core.math_canonical import parse_math
from confia_lean_auditor.core.math_canonical.integer_structures import positive_multiset,product_form,multiset_product,partition_table
from confia_lean_auditor.lean.student_claim_checkers.real_algebra import lean_real_expression
from confia_lean_auditor.lean.student_claim_checkers.tme2_p5 import verify_tme2_p5_digital
from confia_lean_auditor.rubric.pauta import load_pauta
from confia_lean_auditor.rubric.pauta.bridge import record_fingerprint
from confia_lean_auditor.rubric.pauta.tme2_p5 import bridge_tme2_p5,TME2_P5_OBLIGATIONS
from confia_lean_auditor.student_claims.tme2_p5_digital import collect_tme2_p5_digital
from confia_lean_auditor.tme.p5_integer_break import partitions,sum11_maximum,normal_counts,optimal_forms,list_sum,list_size
from confia_lean_auditor.tme.registry import audit_tme,TME_PROBLEMS

ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/'tests/fixtures/tme2_p5_digital/cases.json').read_text())


def fixture(identifier):return next(c for c in CASES if c['id']==identifier)
def inputs(case):return case.get('solution',{case['item']:case['text']})
def run(item,text,*,lean=False):return audit_tme('TME2026P5',{item:text},solution_id='p5-test',use_lean=lean)
def ev(bridge,key):return next(e for e in bridge.evidence.obligations if e.obligation_id==key)


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id'])
def test_controlled_digital_solutions_and_trace(case):
    bridge,result=audit_tme('TME2026P5',inputs(case),solution_id=case['id'],use_lean=False)
    item=result.items['abcd'.index(case['item'])]
    assert item.points_awarded==case['points']
    if 'selected_path' in case:assert item.selected_method_path==case['selected_path']
    if 'carry_forward' in case:assert item.carry_forward_applied==case['carry_forward']
    digital=collect_tme2_p5_digital(inputs(case));records={r.record_id:r for r in bridge.auditor.records}
    for fact in bridge.auditor.facts:
        assert 'points' not in fact.metadata
        for id in fact.source_claim_ids:
            record=records[id]
            assert digital.source_text[record.source.source_start:record.source.source_end]==record.source.raw_text
            assert record.source.source_sha256==hashlib.sha256(digital.source_text.encode()).hexdigest()
            assert record.source.attributable and record.canonical_form
            assert record_fingerprint(record)==fact.record_fingerprints[id]
            assert fact.verification in record.verification_results
    if item.points_awarded:assert item.credit_evidence_refs


@pytest.mark.parametrize('a',['a_complete','a_structural'])
@pytest.mark.parametrize('c',['c_complete','c_general'])
def test_full_alternative_methods_score_twenty(a,c):
    solution={i:fixture(name)['text'] for i,name in [('a',a),('b','b_complete'),('c',c),('d','d_complete')]}
    _,result=audit_tme('TME2026P5',solution,use_lean=False)
    assert result.score==20 and not result.needs_review


@pytest.mark.parametrize('text',['(2,3,3,3)','(3,3,2,3)','2+3+3+3','{3:3,2:1}'])
def test_unordered_structural_lists(text):assert positive_multiset(text)=={'2':1,'3':3}


@pytest.mark.parametrize('text',['3^674','(3^674,)','{3:-674}','{3:0}','{3:1,3:674}',
    '(0,2,3)','(True,3)','{2:2,3:674} # text','[x for x in range(3)]','+'.join(['1']*400)])
def test_invalid_or_product_as_list_fails_closed(text):assert positive_multiset(text) is None


@pytest.mark.parametrize('text',['4*3^674','4*(3**674)','12*3^673','4*9^337','(2*3^337)^2','4*3^(675-1)'])
def test_products_stay_compact_and_exact(text):assert product_form(text)=={'2':2,'3':674}


@pytest.mark.parametrize('text',['4*3^673','3^674','4*3^675'])
def test_wrong_product_is_not_normalized_to_the_answer(text):assert product_form(text)!={'2':2,'3':674}


@pytest.mark.parametrize('text',['4*3^-1','4*3^1000000','4*3^0.5','4*3^n','4/3','0*3^674','__import__("os")'])
def test_product_parser_budget_and_domain(text):assert product_form(text) is None


def test_existing_general_parser_limits_and_reals_are_preserved():
    assert parse_math('4*3^674').status=='unsupported'
    assert lean_real_expression('5/3')=='((5 : ℝ) / (3 : ℝ))'
    assert lean_real_expression('5/3',number_domain='Z',variables=('n',)) is None
    assert 'ℤ' in lean_real_expression('3*(n-3)',number_domain='Z',variables=('n',))


def test_partition_checker_is_independent_and_global_forms_are_complete():
    from math import prod
    assert len(partitions(11))==56 and sum11_maximum()==54
    assert all(sum(p)==11 and list(p)==sorted(p) and min(p)>0 for p in partitions(11))
    assert [p for p in partitions(11) if prod(p)==54]==[(2,3,3,3)]
    # Exhaustively cross-check the replacement theorem on independent small totals.
    for n in range(2,19):
        best=max(prod(p) for p in partitions(n))
        maximizers={tuple(sorted(positive_multiset(str(p)).items())) for p in partitions(n) if prod(p)==best}
        assert maximizers=={tuple(sorted(c.items())) for c in optimal_forms(n)}
    assert optimal_forms(2026)==({'2':2,'3':674},{'3':674,'4':1})
    assert [list_size(c) for c in optimal_forms(2026)]==[676,675]
    assert all(list_sum(c)==2026 for c in optimal_forms(2026))
    with pytest.raises(ValueError):partitions(2026)
    with pytest.raises(ValueError):partitions(11,0)


@pytest.mark.parametrize('text',['enum_max: 54','candidate: (2,3,3,3)','product: 54=54'])
def test_engine_maximum_does_not_fabricate_student_argument(text):
    bridge,_=run('a',text)
    assert ev(bridge,'a.enumeration').status=='indeterminate'
    assert ev(bridge,'a.structural_max').status=='indeterminate'


@pytest.mark.parametrize('text,points',[('product: 6*9=54',1),
    ('product: (2*3)*(3*3)=54',1),('product: 54*1=54',0)])
def test_product_calculation_accepts_regrouping_without_fabricating_a_list(text,points):
    bridge,result=run('a',text)
    assert result.items[0].points_awarded==points
    assert ev(bridge,'a.candidate').status=='indeterminate'
    assert ev(bridge,'a.structural_max').status=='indeterminate'


@pytest.mark.parametrize('item,case',[('a','a_complete'),('b','b_complete'),('c','c_complete'),('d','d_complete')])
@pytest.mark.parametrize('prefix',['Não é verdade:\n','Suponha:\n','Tentativa descartada:\n','Citação:\n'])
def test_nonasserted_contexts_never_receive_credit(item,case,prefix):
    bridge,result=run(item,prefix+fixture(case)['text'])
    assert result.items['abcd'.index(item)].points_awarded==0
    assert not bridge.auditor.facts


@pytest.mark.parametrize('text,key',[
    ('four_sum: 4=4','four_sum'),('four_product: 4=4*1','four_product'),
    ('four_sum: 4>=2+2','four_sum'),('twos_sum: 6=6','twos_sum'),
    ('twos_gain: 8<=9','twos_gain')])
def test_numeric_truth_does_not_fabricate_the_required_local_argument(text,key):
    bridge,_=run('c',text)
    assert ev(bridge,'c.'+key).status=='indeterminate'


@pytest.mark.parametrize('text',['2>1','10>9','m+2>m+1','2*m>m'])
def test_pointwise_truth_does_not_become_the_general_one_merge_proof(text):
    bridge,result=run('c',fixture('c_general')['text'].replace('one_gain: m+1>m','one_gain: '+text))
    assert ev(bridge,'c.one_gain').status=='indeterminate'
    assert result.items[2].points_awarded==0


@pytest.mark.parametrize('field',['source','routing','canonical'])
def test_grounding_and_source_annotation_tampering_is_rejected(field):
    digital=collect_tme2_p5_digital({'a':'candidate: (2,3,3,3)'})
    record=digital.records[0]
    if field=='source':digital=replace(digital,source_text=digital.source_text.replace('2,3,3,3','2,2,3,4'))
    elif field=='routing':digital=replace(digital,records=(record.model_copy(update={'rubric_links':('d',)}),))
    else:digital=replace(digital,records=(record.model_copy(update={'canonical_form':record.canonical_form.model_copy(update={'subject':'normal_list'})}),))
    with pytest.raises(ValueError,match='projection changed'):verify_tme2_p5_digital(digital,'bad',use_lean=False)


def test_carry_forward_preserves_prior_error_and_binds_the_exact_record():
    bridge,result=audit_tme('TME2026P5',inputs(fixture('d_cf_valid')),use_lean=False)
    assert ev(bridge,'c.threes_count').status=='refuted'
    assert result.items[3].points_awarded==1 and result.items[3].carry_forward_applied
    contexts=[ev(bridge,'d.cf_'+k).conditional_on for k in ['adoption','dependency','coherence']]
    assert contexts[0]==contexts[1]==contexts[2]
    assert contexts[0].adopted_result_ref in ev(bridge,'c.threes_count').evidence_refs
    assert contexts[0].adopted_result_ref in ev(bridge,'d.cf_adoption').evidence_refs
    assert ev(bridge,'d.sizes').status=='indeterminate'  # no unconditional correct-count invention


def test_carry_forward_rejects_changed_context_at_engine_boundary():
    from confia_lean_auditor.rubric.pauta import PautaEngine
    bridge,_=audit_tme('TME2026P5',inputs(fixture('d_cf_valid')),use_lean=False)
    changed=[]
    for evidence in bridge.evidence.obligations:
        if evidence.obligation_id=='d.cf_coherence':
            evidence=evidence.model_copy(update={'conditional_on':evidence.conditional_on.model_copy(update={'adopted_result_ref':'unrelated'})})
        changed.append(evidence)
    cfg=load_pauta(ROOT/'examples/pautas/tme2_problem5.v1.json')
    result=PautaEngine().evaluate(cfg,bridge.evidence.model_copy(update={'obligations':tuple(changed)}))
    assert result.items[3].points_awarded==0 and not result.items[3].carry_forward_applied


@pytest.mark.parametrize('status',['verified','refuted','technical_error','unverified'])
def test_integer_formal_contract_and_failure_semantics(monkeypatch,tmp_path,status):
    import confia_lean_auditor.lean.student_claim_checkers.real_algebra as module
    monkeypatch.setattr(module,'CHECK_DIR',tmp_path)
    calls=[]
    def runner(path,**kwargs):
        calls.append(path)
        negative=path.stem.endswith('_refutation')
        ok=status=='verified' or status=='refuted' and negative
        error='unknown identifier unavailable' if status=='technical_error' else 'error: unsolved goals'
        return subprocess.CompletedProcess([],0 if ok else 1,'' if ok else error,'')
    monkeypatch.setattr(module,'_run_lean_file',runner)
    bridge,result=run('b','domain: n>=5\nincrease: 3*(n-3)>n',lean=True)
    fact=next(f for f in bridge.auditor.facts if f.student_check)
    assert fact.verification.status==status
    assert fact.student_check['data']['number_domain']=='Z'
    assert '∀ n : ℤ, n ≥ 5 →' in fact.student_check['lean_statement']
    assert 'ℝ' not in fact.student_check['lean_statement']
    if status=='technical_error':assert len(calls)==1 and result.items[1].points_awarded is None
    tampered=fact.model_copy(update={'student_check':{**fact.student_check,'data':{**fact.student_check['data'],'number_domain':'R'}}})
    bundle=bridge.auditor.model_copy(update={'facts':(tampered,)})
    cfg=load_pauta(ROOT/'examples/pautas/tme2_problem5.v1.json')
    assert ev(bridge_tme2_p5(cfg,bundle),'b.increase').status=='indeterminate'


def test_missing_domain_never_calls_lean_to_invent_an_assumption(monkeypatch):
    import confia_lean_auditor.lean.student_claim_checkers.tme2_p5 as module
    def forbidden(*args,**kwargs):pytest.fail('Domain must be explicitly grounded')
    monkeypatch.setattr(module,'check_real_record',forbidden)
    bridge,result=run('b','increase: 3*(n-3)>n',lean=True)
    assert result.items[1].points_awarded==0 and ev(bridge,'b.increase').status=='indeterminate'


def test_all_obligations_and_opt_in_registry():
    from confia_lean_auditor.core.problem_catalog import CATALOG
    assert 'TME2026P5' in TME_PROBLEMS and 'TME2026P5' not in CATALOG
    covered=set()
    for case in CASES:
        bridge,_=audit_tme('TME2026P5',inputs(case),use_lean=False)
        covered.update(e.obligation_id for e in bridge.evidence.obligations if e.status=='supported')
    assert covered==set(TME2_P5_OBLIGATIONS)
    with pytest.raises(ValueError):audit_tme('TME2026P6',{'a':'54'})
