"""P2 mathematical diagram invariants, attribution and formal/text boundaries."""
import hashlib
import json
import subprocess
from dataclasses import replace
from itertools import permutations,product
from pathlib import Path

import pytest
from pydantic import ValidationError

from confia_lean_auditor.claims.common.schemas import MathClaimRecord,SourceBinding,StructuredSourceBinding
from confia_lean_auditor.claims.common.adapters import project_student_claim
from confia_lean_auditor.core.math_canonical.combinatorial import factorial_form,lean_combinatorial_expression,two_count_factors
from confia_lean_auditor.lean.student_claim_checkers.tme2_p2 import verify_tme2_p2
from confia_lean_auditor.rubric.pauta import load_pauta
from confia_lean_auditor.rubric.pauta.bridge import record_fingerprint
from confia_lean_auditor.rubric.pauta.tme2_p2 import bridge_tme2_p2,TME2_P2_OBLIGATIONS
from confia_lean_auditor.student_claims.tme2_p2_digital import collect_tme2_p2_text,split_p2_input
from confia_lean_auditor.tme.p2_diagram import TME2P2DiagramState,inspect_diagram,feasible_pairs,admissible_cases,recognize_p2_diagram_from_image
from confia_lean_auditor.tme.registry import audit_tme,TME_PROBLEMS

ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/'tests/fixtures/tme2_p2_digital/cases.json').read_text())


def case(id):return next(c for c in CASES if c['id']==id)
def inputs(c):return c.get('solution',{c['item']:c['text']})
def run(item,text,*,lean=False):return audit_tme('TME2026P2',{item:text},solution_id='p2-test',use_lean=lean)
def ev(bridge,key):return next(e for e in bridge.evidence.obligations if e.obligation_id==key)


@pytest.mark.parametrize('c',CASES,ids=lambda c:c['id'])
def test_controlled_cases_and_full_source_chain(c):
    bridge,result=audit_tme('TME2026P2',inputs(c),solution_id=c['id'],use_lean=False)
    item=result.items['abc'.index(c['item'])]
    assert item.points_awarded==c['points']
    texts,_=split_p2_input(inputs(c));digital=collect_tme2_p2_text(texts)
    by_id={r.record_id:r for r in bridge.auditor.records}
    for fact in bridge.auditor.facts:
        assert 'points' not in fact.metadata
        for id in fact.source_claim_ids:
            r=by_id[id]
            assert r.source.attributable and r.canonical_form
            assert record_fingerprint(r)==fact.record_fingerprints[id]
            assert fact.verification in r.verification_results
            if isinstance(r.source,StructuredSourceBinding):
                assert r.source.raw_text is r.source.source_start is r.source.source_end is None
                assert r.source.source_ref and r.source.image_ref and r.source.page_index==0
                assert fact.verification_source=='deterministic'
                assert fact.metadata['verification_kind']=='deterministic_diagram'
            else:
                assert digital.source_text[r.source.source_start:r.source.source_end]==r.source.raw_text
    if item.points_awarded:assert item.credit_evidence_refs


@pytest.mark.parametrize('a',['a_diagram_only','a_text_complete','a_text_plus_diagram'])
@pytest.mark.parametrize('c',['c_complete','c_alternative','c_alternative_factorials'])
def test_full_problem_with_both_modalities_and_counting_paths(a,c):
    solution={**inputs(case(a)),**inputs(case('b_complete')),**inputs(case(c))}
    _,result=audit_tme('TME2026P2',solution,use_lean=False)
    assert result.score==20 and not result.needs_review


@pytest.mark.parametrize('center,common',admissible_cases())
def test_all_384_labelled_balanced_configurations_are_accepted(center,common):
    pairs=feasible_pairs(center,common);seen=set()
    for order in permutations(pairs):
        for flips in product((False,True),repeat=4):
            pos={}
            for (a,b),pair,flip in zip(zip('ABCD','EFGH'),order,flips):
                pos[a],pos[b]=pair[::-1] if flip else pair
            metrics=inspect_diagram(TME2P2DiagramState(center=center,positions=pos),required_center=center)
            assert metrics['valid'] and metrics['uses_1_to_9_exactly_once'] and metrics['line_sums']==[common]*4
            seen.add(tuple(pos[k] for k in 'ABCDEFGH'))
    assert len(seen)==384


def test_diagram_metrics_are_computed_not_picture_matched():
    state=case('a_diagram_only')['solution']['a']['diagrams'][0]['state']
    metrics=inspect_diagram(state,required_center=5)
    assert metrics['opposite_pairs']==[(1,9),(2,8),(3,7),(4,6)]
    assert metrics['used_values']==[5,1,2,3,4,9,8,7,6]
    altered={**state,'positions':{**state['positions'],'A':2}}
    bad=inspect_diagram(altered,required_center=5)
    assert bad['duplicates'] and not bad['uses_1_to_9_exactly_once'] and bad['line_sums'][0]==16
    assert not inspect_diagram(state,required_center=9)['valid']


@pytest.mark.parametrize('state',[{'center':True,'positions':{}}, {'center':5,'positions':{'I':1}},
    {'center':5,'positions':{'A':1.0}}, {'center':5,'positions':{'A':'1'}}])
def test_invalid_diagram_state_is_not_coerced(state):
    with pytest.raises(ValidationError):TME2P2DiagramState.model_validate(state)


def test_missing_position_is_unknown_not_a_fabricated_number():
    bridge,_=audit_tme('TME2026P2',inputs(case('a_missing_position')),use_lean=False)
    assert ev(bridge,'a.complete_configuration').status=='indeterminate'
    r=next(r for r in bridge.auditor.records if r.claim_type=='diagram_state')
    assert 'H' not in r.source.payload['positions']


def test_image_recognition_is_explicitly_unimplemented():
    with pytest.raises(NotImplementedError,match='recognition is not implemented'):
        recognize_p2_diagram_from_image('some-image.png')


def test_region_and_confidence_metadata_are_preserved_without_text_offsets():
    solution=json.loads(json.dumps(inputs(case('a_diagram_only'))))
    source=solution['a']['diagrams'][0]['source']
    source.update(regions={'center':[10,20,5,6],'A':[1,2,3,4]},confidence=.8,position_confidence={'A':.7})
    bridge,result=audit_tme('TME2026P2',solution,use_lean=False)
    r=next(r for r in bridge.auditor.records if r.claim_type=='diagram_state')
    assert r.source.regions['center']==(10,20,5,6) and r.source.position_confidence=={'A':.7}
    assert r.source.confidence==.8 and r.source.confirmed  # explicitly reviewed, not an OCR threshold
    assert r.source.source_start is None and result.items[0].points_awarded==5
    assert MathClaimRecord.model_validate(r.model_dump()).model_dump()==r.model_dump()


def test_old_text_binding_still_requires_real_text_and_offsets():
    with pytest.raises(ValidationError,match='Attribution requires'):
        SourceBinding(grounding_status='grounded',source_sha256='0'*64,attributable=True)
    old=SourceBinding(grounding_status='grounded',raw_text='1',source_start=0,source_end=1,
                      source_sha256=hashlib.sha256(b'1').hexdigest(),attributable=True)
    assert set(old.model_dump())=={'grounding_status','raw_text','source_start','source_end','source_sha256','attributable'}


@pytest.mark.parametrize('mutation',['offset','payload','type','family','legacy','reference_authority','unconfirmed'])
def test_structured_record_cannot_bypass_text_or_provenance_gates(mutation):
    bridge,_=audit_tme('TME2026P2',inputs(case('a_diagram_only')),use_lean=False)
    r=next(r for r in bridge.auditor.records if r.claim_type=='diagram_state').model_dump()
    if mutation=='offset':r['source']['source_start']=0
    elif mutation=='payload':r['source']['payload']['positions']['A']=2
    elif mutation=='type':r['claim_type']='arithmetic_equality'
    elif mutation=='family':r['canonical_form']['value']['center']=9
    elif mutation=='legacy':r['legacy_payload']={'data':{}}
    elif mutation=='reference_authority':r['source']['origin']='reference'
    else:r['source']['confirmed']=False
    with pytest.raises(ValidationError):MathClaimRecord.model_validate(r)


@pytest.mark.parametrize('mechanism',['student_lean','canonical_equivalence'])
def test_diagram_facts_cannot_be_relabelled_as_textual_or_formal_proofs(mechanism):
    bridge,_=audit_tme('TME2026P2',inputs(case('a_diagram_only')),use_lean=False)
    fact=next(f for f in bridge.auditor.facts if f.fact_id=='a.complete_configuration')
    forged=fact.model_copy(update={'verification_source':mechanism})
    bundle=bridge.auditor.model_copy(update={'facts':(forged,)})
    config=load_pauta(ROOT/'examples/pautas/tme2_problem2.v1.json')
    assert ev(bridge_tme2_p2(config,bundle),'a.complete_configuration').status=='indeterminate'


def test_diagram_never_calls_lean(monkeypatch):
    import confia_lean_auditor.lean.student_claim_checkers.tme2_p2 as module
    def forbidden(*a,**kw):pytest.fail('Lean cannot recognize a diagram')
    monkeypatch.setattr(module,'check_real_record',forbidden)
    _,result=audit_tme('TME2026P2',inputs(case('a_diagram_only')),use_lean=True)
    assert result.items[0].points_awarded==5


def test_diagram_does_not_authorize_a_missing_combinatorial_count():
    bridge,_=audit_tme('TME2026P2',inputs(case('a_diagram_only')),use_lean=False)
    fact=next(f for f in bridge.auditor.facts if f.fact_id=='a.complete_configuration')
    forged=fact.model_copy(update={'fact_id':'c.total'})
    config=load_pauta(ROOT/'examples/pautas/tme2_problem2.v1.json')
    result=bridge_tme2_p2(config,bridge.auditor.model_copy(update={'facts':(forged,)}))
    assert ev(result,'c.total').status=='indeterminate'


def test_structured_evidence_is_not_enabled_on_the_existing_p1_bridge():
    from confia_lean_auditor.rubric.pauta.bridge import bridge_tme2_p1
    bridge,_=audit_tme('TME2026P2',inputs(case('a_diagram_only')),use_lean=False)
    records=tuple(r.model_copy(update={'problem_id':'TME2_P1_PILOT'}) for r in bridge.auditor.records)
    by_id={r.record_id:r for r in records}
    original=next(f for f in bridge.auditor.facts if f.fact_id=='a.complete_configuration')
    forged=original.model_copy(update={'fact_id':'a.result_594',
        'record_fingerprints':{id:record_fingerprint(by_id[id]) for id in original.source_claim_ids}})
    bundle=bridge.auditor.model_copy(update={'problem_id':'TME2_P1_PILOT','records':records,'facts':(forged,)})
    config=load_pauta(ROOT/'examples/pautas/tme2_problem1.v1.json')
    assert ev(bridge_tme2_p1(config,bundle),'a.result_594').status=='indeterminate'


@pytest.mark.parametrize('prefix',['Não é verdade:\n','Suponha:\n','Tentativa descartada:\n','Citação:\n'])
@pytest.mark.parametrize('item,id',[('a','a_text_complete'),('b','b_complete'),('c','c_complete')])
def test_nonasserted_text_never_receives_credit(prefix,item,id):
    bridge,result=run(item,prefix+case(id)['text'])
    assert result.items['abc'.index(item)].points_awarded==0 and not bridge.auditor.facts


@pytest.mark.parametrize('expression',['4!','4! * 2^4','2**4','(4!)'])
def test_factorial_renderer_is_bounded_and_uses_real_factorial(expression):
    assert factorial_form(expression)
    assert lean_combinatorial_expression(expression)
    if '!' in expression:assert 'Nat.factorial 4' in lean_combinatorial_expression(expression)


@pytest.mark.parametrize('expression',['100!','4!!','__import__("os")','x!','4!/0','2^10000','sin(4)'])
def test_unsupported_factorial_expressions_fail_closed(expression):
    assert factorial_form(expression) is None


@pytest.mark.parametrize('expression',['24*16','16*24','4!*2^4','2^4*4!'])
def test_equivalent_direct_combinatorial_constructions(expression):assert two_count_factors(expression)


@pytest.mark.parametrize('expression',['384','12*32','384*1'])
def test_a_total_does_not_invent_the_two_counting_factors(expression):assert not two_count_factors(expression)


def test_completeness_and_hypothesis_gates_are_not_overridden_by_true_formal_implications(monkeypatch):
    import confia_lean_auditor.lean.student_claim_checkers.tme2_p2 as module
    # Extra alternatives make the necessary disjunction true but the claimed
    # exact set false. Do not submit that weaker theorem as positive evidence.
    called=[]
    def no_proof(record,*a,**kw):called.append(record.canonical_form.subject);return None
    monkeypatch.setattr(module,'check_real_record',no_proof)
    bridge,_=run('b',case('b_extra_center')['text'],lean=True)
    assert 'centers' not in called and ev(bridge,'b.centers').status=='refuted'
    called.clear()
    bridge,result=run('b','centers: {1,5,9}',lean=True)
    assert not called and result.items[1].points_awarded==0
    bridge,_=run('b','balance_relation: 4*S=45+3*x\nsum_formula: S=S',lean=True)
    assert ev(bridge,'b.sum_formula').status=='indeterminate'


@pytest.mark.parametrize('status',['verified','refuted','technical_error','unverified'])
def test_factorial_formal_binding_and_failure_semantics(monkeypatch,tmp_path,status):
    import confia_lean_auditor.lean.student_claim_checkers.real_algebra as module
    monkeypatch.setattr(module,'CHECK_DIR',tmp_path)
    calls=[]
    def runner(path,**kwargs):
        calls.append(path);negative=path.stem.endswith('_refutation')
        ok=status=='verified' or status=='refuted' and negative
        error='unknown identifier missing' if status=='technical_error' else 'error: unsolved goals'
        return subprocess.CompletedProcess([],0 if ok else 1,'' if ok else error,'')
    monkeypatch.setattr(module,'_run_lean_file',runner)
    bridge,result=run('c','pair_permutations: 4!=20',lean=True)
    fact=next(f for f in bridge.auditor.facts if f.student_check)
    assert fact.verification.status==status
    assert 'Nat.factorial 4' in fact.student_check['lean_statement'] and '(20 : ℤ)' in fact.student_check['lean_statement']
    if status=='technical_error':assert len(calls)==1 and result.items[2].points_awarded is None
    altered=fact.model_copy(update={'student_check':{**fact.student_check,'data':{**fact.student_check['data'],'number_domain':'R'}}})
    config=load_pauta(ROOT/'examples/pautas/tme2_problem2.v1.json')
    assert ev(bridge_tme2_p2(config,bridge.auditor.model_copy(update={'facts':(altered,)})),'c.pair_permutations').status=='indeterminate'


def test_digital_projection_mutation_is_rejected():
    digital=collect_tme2_p2_text({'a':'line_sum: 15'})
    with pytest.raises(ValueError,match='projection changed'):
        verify_tme2_p2(replace(digital,source_text=digital.source_text.replace('15','16')),{},'bad',use_lean=False)


def test_registry_all_obligations_and_native_diagram_projection():
    from confia_lean_auditor.core.problem_catalog import CATALOG
    assert 'TME2026P2' in TME_PROBLEMS and 'TME2026P2' not in CATALOG
    covered=set()
    for c in CASES:
        bridge,_=audit_tme('TME2026P2',inputs(c),use_lean=False)
        covered.update(e.obligation_id for e in bridge.evidence.obligations if e.status=='supported')
    assert covered==set(TME2_P2_OBLIGATIONS)
    bridge,_=audit_tme('TME2026P2',inputs(case('a_diagram_only')),use_lean=False)
    r=next(r for r in bridge.auditor.records if r.claim_type=='diagram_state')
    with pytest.raises(ValueError,match='native'):project_student_claim(r,solution_text='')
    with pytest.raises(ValueError):audit_tme('TME2026P6',{'a':'15'})
