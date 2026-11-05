"""P2 total value/equality eligibility; frozen composite and baseline behavior."""
import copy
import pytest
from confia_lean_auditor.experimental.tme_semantic_formal_p2.engine import evaluate,award
from confia_lean_auditor.experimental.tme_semantic_formal_p2.registry import REGISTRY,route_for_expression,PROBLEM_ID
from confia_lean_auditor.experimental.tme_semantic_formal_p2.evidence import bind_evidence
from confia_lean_auditor.experimental.tme_semantic_formal_p2.mapper import SourceDocument,ObligationMapper
from test_tme_semantic_formal_p2 import claim,provider,run,sample
import json


def total_result(r):
    return next(v for v in r['verification_results'] if v['obligation_id']=='c.total')


@pytest.mark.parametrize('expression,score,status',[
 ('384',1,'DETERMINISTIC_VERIFIED'),('385',0,'DETERMINISTIC_FAILED'),
 ('0',0,'DETERMINISTIC_FAILED'),('-384',0,'DETERMINISTIC_FAILED'),
 ('384/1',1,'DETERMINISTIC_VERIFIED'),('24*16',1,'DETERMINISTIC_VERIFIED')])
def test_explicit_total_value_uses_exact_existing_checker(expression,score,status):
    text,claims=sample('c.total',expression);r=run(text,claims);v=total_result(r)
    assert v['status']==status and v['route']=='DETERMINISTIC'
    assert v['formal_status']=='FORMAL_NOT_ATTEMPTED' and v['formal_attempted'] is False
    assert v['checker_result'] is None and v['verification_kind']=='written_total_value'
    assert r['score']==score and isinstance(r['score'],float)
    assert v['mathematical_refutation'] is (score==0)
    if score:
        obs=next(o for o in r['evidence']['obligations'] if o['obligation_id']=='c.total')
        assert obs['origin']==obs['verification_source']=='deterministic'
        assert next(a for a in r['awards'] if a['obligation_id']=='c.total')['verification_route']=='DETERMINISTIC'


@pytest.mark.parametrize('suggested',['FORMAL','DETERMINISTIC','COMPOSITE','SEMANTIC'])
def test_route_is_selected_from_representation_not_model(suggested):
    text,claims=sample('c.total','384');claims[0]['route_candidate']=suggested
    r=run(text,claims);m=r['obligation_mapping'][0]
    assert m['effective_route']=='DETERMINISTIC' and r['score']==1
    assert m['route_override_reason']==(None if suggested=='DETERMINISTIC' else 'obligation_registry')
    assert r['extracted_evidence'][0]['route_candidate']==suggested


def test_linguistic_total_is_bound_without_inventing_an_equality():
    span='O total de preenchimentos é 384.';text='c) '+span
    r=run(text,[claim(text,'c.total',span=span,expression='384')])
    v=total_result(r)
    assert r['score']==1 and v['status']=='DETERMINISTIC_VERIFIED'
    assert r['projection'][0]['source_span']==span and r['projection'][0]['normalized_claim']=='384'
    assert v['original_fact']['student_check'] is None


@pytest.mark.parametrize('span',['384','A quantidade de orientações é 384.'])
def test_unbound_number_cannot_be_relabelled_as_total(span):
    text='c) '+span;r=run(text,[claim(text,'c.total',span=span,expression='384')])
    assert r['score']==0 and not r['obligation_mapping'][0]['accepted']


@pytest.mark.parametrize('expression',['24*16=384','24*16=364','384/1=384'])
def test_equality_never_falls_back_to_value_without_formal_execution(expression):
    text,claims=sample('c.total',expression);claims[0]['route_candidate']='DETERMINISTIC'
    r=run(text,claims);v=total_result(r)
    assert v['route']=='FORMAL' and v['status']=='FORMAL_NOT_ATTEMPTED'
    assert not v['sufficiency_decision']['sufficient'] and r['score']==0
    assert r['obligation_mapping'][0]['effective_route']=='FORMAL'


def test_only_total_gains_an_additional_allowed_route():
    assert REGISTRY['c.total'].allowed_routes==('FORMAL','DETERMINISTIC')
    for oid,spec in REGISTRY.items():
        if oid!='c.total':assert spec.allowed_routes==(spec.route,)
    assert route_for_expression('c.pair_permutations','24')=='COMPOSITE'
    assert route_for_expression('c.pair_orientations','16')=='COMPOSITE'


@pytest.mark.parametrize('oid,value',[
 ('c.pair_permutations','24'),('c.pair_orientations','16'),('c.counting_product','384')])
def test_isolated_counts_remain_composite_incomplete(oid,value):
    text,claims=sample(oid,value);r=run(text,claims)
    v=next(v for v in r['verification_results'] if v['obligation_id']==oid)
    assert v['status']=='COMPOSITE_INCOMPLETE' and r['score']==0
    relation=next(s for s in v['subchecks'] if s['name']=='relation')
    assert relation['reason']=='argument_not_established' and not v['mathematical_refutation']


@pytest.mark.parametrize('oid',['c.pair_permutations','c.pair_orientations','c.counting_product'])
def test_complete_composite_is_unchanged(oid):
    text,claims=sample(oid);r=run(text,claims)
    v=next(v for v in r['verification_results'] if v['obligation_id']==oid)
    assert v['status']=='COMPOSITE_VERIFIED'
    assert {s['name'] for s in v['subchecks']}=={'arithmetic','counting_components','relation'}


def test_partial_recovers_only_final_point_with_unchanged_baseline(tmp_path):
    text='c) pair_permutations: 24\npair_orientations: 16\ntotal: 384'
    claims=[claim(text,'c.pair_permutations',expression='24'),claim(text,'c.pair_orientations',expression='16'),claim(text,'c.total',expression='384')]
    current=evaluate('partial-control',PROBLEM_ID,text,mode='tme_current',use_lean=False)
    semantic=run(text,claims)
    after=evaluate('partial-control',PROBLEM_ID,text,mode='tme_current',use_lean=False)
    assert current['current_bridge']==after['current_bridge'] and current['current_assessment']==after['current_assessment']
    assert current['score']==5 and semantic['score']==1
    assert [(c['rule_id'],c['points']) for c in semantic['credits']]==[('c.conclusion',1.0)]
    assert {v['obligation_id']:v['status'] for v in semantic['verification_results']}=={
        'c.pair_permutations':'COMPOSITE_INCOMPLETE','c.pair_orientations':'COMPOSITE_INCOMPLETE','c.total':'DETERMINISTIC_VERIFIED'}
    (tmp_path/'partial-result.json').write_text(json.dumps(semantic,ensure_ascii=False,indent=2))


def test_route_allowlist_cannot_downgrade_an_equality_at_award_gate():
    text,claims=sample('c.total','384');r=run(text,claims)
    units=bind_evidence(json.dumps({'evidence':claims}),text,'test')
    mapping=ObligationMapper().map(SourceDocument.parse(text),units)
    # Simulate a mismatch at the gate: a formal mapping cannot be credited using
    # a deterministic result, even though both routes exist for the obligation.
    mapping[0]['effective_route']='FORMAL'
    _,awards=award('route-mismatch',units,mapping,r['verification_results'],[])
    assert not next(a for a in awards if a['obligation_id']=='c.total')['eligible']
