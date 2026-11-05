"""Source-only providers exercise interpretation; mathematics is never mocked."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest
from confia_lean_auditor.experimental.tme_semantic_formal_p2.evidence import bind_evidence
from confia_lean_auditor.experimental.tme_semantic_formal_p2.extractor import SemanticExtractorP2
from confia_lean_auditor.experimental.tme_semantic_formal_p2.mapper import SourceDocument,ObligationMapper
from confia_lean_auditor.experimental.tme_semantic_formal_p2.registry import REGISTRY,PROBLEM_ID
from confia_lean_auditor.experimental.tme_semantic_formal_p2.engine import evaluate,award
from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.student_claims.tme2_p2_digital import VOCABULARY
from confia_lean_auditor.tme.obligation_experiment import primary_audit

ROOT=Path(__file__).resolve().parents[1]
PLACEMENT='{center:5,A:1,B:2,C:3,D:4,E:9,F:8,G:7,H:6}'
VALUES={
'a.pair_sum':('pair_sum','10'),'a.line_sum':('line_sum','15'),
'a.pairs':('pairs','{(1,9),(2,8),(3,7),(4,6)}'),
'a.placement':('placement',PLACEMENT),'a.complete_configuration':('placement',PLACEMENT),
'b.balance_relation':('balance_relation','4*S=45+3*x'),'b.sum_formula':('sum_formula','(45+3*x)/4'),
'b.integral_sum':('integral_sum','integer'),'b.modular_condition':('modular_condition','x ≡ 1 (mod 4)'),
'b.centers':('centers','{1,5,9}'),'b.admissible_center':('admissible_center','1'),
'b.center_sums':('center_sums','{(1,12),(5,15),(9,18)}'),'b.sum_at_five':('sum_at_five','15'),
'b.realizable_1':('realizable_1','{(2,9),(3,8),(4,7),(5,6)}'),
'b.realizable_5':('realizable_5','{(1,9),(2,8),(3,7),(4,6)}'),
'b.realizable_9':('realizable_9','{(1,8),(2,7),(3,6),(4,5)}'),
'c.max_center':('max_center','9'),'c.max_sum':('max_sum','18'),
'c.pairs':('pairs','{(1,8),(2,7),(3,6),(4,5)}'),
'c.pair_permutations':('pair_permutations','4!=24'),'c.pair_orientations':('pair_orientations','2^4=16'),
'c.total':('total','384=384'),'c.counting_product':('counting_product','24*16=384')}


def claim(text,oid,*,span=None,expression=None,subject=None,**changes):
    key,value=VALUES[oid];subject=subject or key
    if span is None:span=subject+': '+(expression or value)
    units=[u for u in evidence_units(text) if u.exact_text==span]
    assert len(units)==1,(span,[(u.evidence_id,u.exact_text) for u in evidence_units(text)])
    c=dict(source_evidence_ids=[units[0].evidence_id],source_span=span,normalized_claim=expression or value,
        subject=subject,claim_type=VOCABULARY[subject]['kind'],assertion_status='asserted',polarity='positive',scope='main_argument',
        hypothetical=False,abandoned=False,attributed_to_student=True,obligation_candidates=[oid],route_candidate='SEMANTIC')
    c.update(changes);return c


def provider(claims):
    def provide(payload,schema,config):
        return json.dumps({'evidence':claims}),dict(status='completed',model=config['model'],api_calls=0)
    return provide


def run(text,claims,**kwargs):
    return evaluate('unit-p2',PROBLEM_ID,text,extraction_provider=provider(claims),use_lean=False,**kwargs)


def sample(oid,value=None):
    key,expression=VALUES[oid];expression=value or expression
    lines=[];dependencies=[]
    if oid=='b.sum_formula':dependencies=['b.balance_relation']
    if oid=='b.centers':dependencies=['b.modular_condition']
    for d in dependencies:lines.append(': '.join(VALUES[d]))
    lines.append(key+': '+expression)
    text=oid[0]+') '+'\n'.join(lines)
    return text,[*(claim(text,d) for d in dependencies),claim(text,oid,expression=expression)]


@pytest.mark.parametrize('oid',list(REGISTRY))
def test_all_23_mapping_routing_and_frozen_checker_facts(oid):
    text,claims=sample(oid);r=run(text,claims)
    m=next(m for m in r['obligation_mapping'] if m['obligation_id']==oid)
    assert m['accepted'],m
    assert m['effective_route']==REGISTRY[oid].route and m['route_override_reason']=='obligation_registry'
    result=next(v for v in r['verification_results'] if v['obligation_id']==oid)
    expected={'FORMAL':'FORMAL_NOT_ATTEMPTED','DETERMINISTIC':'DETERMINISTIC_VERIFIED','COMPOSITE':'COMPOSITE_VERIFIED'}[REGISTRY[oid].route]
    assert result['status']==expected,result
    assert result.get('verification_id') and result['original_fact']
    assert isinstance(r['score'],float)
    if REGISTRY[oid].route=='FORMAL':assert not next(a for a in r['awards'] if a['obligation_id']==oid)['eligible']
    if REGISTRY[oid].route=='COMPOSITE':
        assert {s['name'] for s in result['subchecks']}=={'arithmetic','counting_components','relation'}


def test_payload_closed_and_contains_no_grading_data():
    ex=SemanticExtractorP2();payload=ex.payload(PROBLEM_ID,'c) total: 384')
    assert len(payload['obligations'])==23 and payload['full_student_solution']=='c) total: 384'
    assert payload['statement'] and ex.configuration()['model']=='gpt-6.1-sol'
    assert ex.configuration()['reasoning_effort']=='medium'
    def keys(obj):
        if isinstance(obj,dict):
            for k,v in obj.items():yield k;yield from keys(v)
        if isinstance(obj,(list,tuple)):
            for v in obj:yield from keys(v)
    assert not set(keys(payload))&{'points','score','gold','baseline','awards','expected_score'}
    schema=ex.schema('c) total: 384');props=schema['$defs']['ExtractedClaim']['properties']
    assert set(props['obligation_candidates']['items']['enum'])==set(REGISTRY)
    assert not schema['additionalProperties']


@pytest.mark.parametrize('field,value',[('source_span','fabricated'),('source_evidence_ids',['E999']),('obligation_candidates',['c.invented']),('subject','invented'),('points',20),('route_candidate','REFERENCE_LEAN')])
def test_invalid_extraction_fails_closed_and_falls_back(field,value):
    text,claims=sample('c.pair_permutations');claims[0][field]=value
    r=run(text,claims)
    assert r['fallback_used'] and r['effective_mode']=='TME_CURRENT_FALLBACK' and r['fallback_reason']
    assert not r['extracted_evidence']


def test_offsets_are_local_exact_and_duplicate_claims_are_deduplicated():
    text,claims=sample('c.pair_permutations')
    evidence=bind_evidence(json.dumps({'evidence':claims*2}),text,'test-model')
    assert len(evidence)==1
    e=evidence[0];assert text[e.source_start:e.source_end]==e.source_span
    assert e.metadata['binding']=='exact_evidence_id_envelope'
    doc=SourceDocument.parse(text+' extra')
    assert ObligationMapper().map(doc,evidence)[0]['reason']=='source_binding_changed'


@pytest.mark.parametrize('change',[
 {'assertion_status':'hypothetical'},{'assertion_status':'negated'},{'assertion_status':'abandoned'},
 {'assertion_status':'quoted'},{'assertion_status':'unclear'},{'polarity':'negative'},
 {'hypothetical':True},{'abandoned':True},{'attributed_to_student':False},{'scope':'exploration'},
 {'scope':'side_calculation'},{'scope':'unknown'}])
def test_extractor_context_veto(change):
    text,claims=sample('c.pair_permutations');claims[0].update(change);r=run(text,claims)
    assert r['score']==0 and r['verification_results'][0]['status']=='CONTEXT_REJECTED'


@pytest.mark.parametrize('prefix',['Suponha:\n','Não é verdade:\n','Tentativa descartada:\n','Citação:\n'])
def test_source_context_overrides_hostile_asserted_model(prefix):
    text='c) '+prefix+'pair_permutations: 4!=24';r=run(text,[claim(text,'c.pair_permutations')])
    assert r['score']==0 and not r['obligation_mapping'][0]['accepted']


@pytest.mark.parametrize('oid',list(REGISTRY))
def test_route_candidate_cannot_force_formal_or_bypass_registry(oid):
    text,claims=sample(oid)
    for c in claims:c['route_candidate']='DETERMINISTIC' if REGISTRY[oid].route=='FORMAL' else 'FORMAL'
    r=run(text,claims);m=next(m for m in r['obligation_mapping'] if m['obligation_id']==oid)
    assert m['effective_route']==REGISTRY[oid].route and m['route_override_reason']


@pytest.mark.parametrize('change',[
 {'obligation_candidates':['c.pair_orientations']},{'obligation_candidates':['b.sum_formula']},
 {'claim_type':'qualitative'},{'subject':'unmapped','claim_type':'qualitative'}])
def test_mapper_does_not_trust_suggested_obligation(change):
    text,claims=sample('c.pair_permutations');claims[0].update(change);r=run(text,claims)
    assert not r['fallback_used'] and r['score']==0 and not r['obligation_mapping'][0]['accepted']


@pytest.mark.parametrize('oid,span,expr',[
 ('b.balance_relation','Contando as linhas, 4*S=45+3*x.','4*S=45+3*x'),
 ('b.integral_sum','A soma S é inteiro.','integer'),
 ('c.pair_permutations','As distribuições são 4!=24.','4!=24'),
 ('c.pair_orientations','As orientações são 2^4=16.','2^4=16'),
 ('c.counting_product','O total de preenchimentos é 24*16=384.','24*16=384')])
def test_prose_interpretation_is_bound_to_written_mathematics(oid,span,expr):
    text=oid[0]+') '+span;r=run(text,[claim(text,oid,span=span,expression=expr)])
    assert r['obligation_mapping'][0]['accepted'],r['obligation_mapping']
    assert r['verification_results'][0]['status'] in {'DETERMINISTIC_VERIFIED','COMPOSITE_VERIFIED'}
    assert r['projection'][0]['source_span']==span


@pytest.mark.parametrize('oid,source,normalized',[
 ('c.pair_permutations','As distribuições são 4!=20.','4!'),
 ('c.pair_permutations','As distribuições são (4!)=20.','4!'),
 ('c.pair_orientations','As orientações são 2^4=8.','2^4'),
 ('c.counting_product','O total de preenchimentos é 24*16=364.','24*16'),
 ('c.pair_permutations','pair_permutations: 4!=20','4!=24'),
 ('c.pair_permutations','As distribuições são 24.','4!=24')])
def test_no_repair_or_truncation_of_wrong_source(oid,source,normalized):
    text='c) '+source;r=run(text,[claim(text,oid,span=source,expression=normalized)])
    assert r['score']==0 and not r['obligation_mapping'][0]['accepted']


@pytest.mark.parametrize('oid,expr',[
 ('c.pair_permutations','24'),('c.pair_permutations','2^3*3=24'),
 ('c.pair_orientations','16'),('c.pair_orientations','4+12=16'),
 ('c.counting_product','384'),('c.counting_product','12*32=384')])
def test_composite_math_alone_has_no_credit(oid,expr):
    text,claims=sample(oid,expr);r=run(text,claims)
    result=next(v for v in r['verification_results'] if v['obligation_id']==oid)
    assert result['status']=='COMPOSITE_INCOMPLETE' and not result['mathematical_refutation']
    assert r['score']==0


@pytest.mark.parametrize('oid,expr',[
 ('c.pair_permutations','4!=20'),('c.pair_orientations','2^4=8'),('c.counting_product','24*16=364')])
def test_false_composite_is_not_representation_failure(oid,expr):
    text,claims=sample(oid,expr);r=run(text,claims);v=r['verification_results'][0]
    assert v['status']=='COMPOSITE_FAILED' and v['mathematical_refutation'] and r['score']==0


def test_missing_selected_claim_does_not_credit_unselected_positive_baseline():
    text,_=sample('c.counting_product');r=run(text,[])
    assert not r['fallback_used'] and r['score']==0 and not any(a['eligible'] for a in r['awards'])


def test_unknown_qualitative_has_no_checker_no_credit():
    text='c) Este argumento está correto.'
    c=claim(text,'c.pair_permutations',span='Este argumento está correto.',expression='Este argumento está correto.')
    c.update(subject='unmapped',claim_type='qualitative');r=run(text,[c])
    assert len(r['extracted_evidence'])==1 and r['score']==0 and r['rejected_evidence']


@pytest.mark.parametrize('select_negative',[True,False])
def test_conflict_cannot_be_hidden_by_omission_or_confidence(select_negative):
    text='c) pair_permutations: 4!=24\npair_permutations: 4!=20'
    cs=[claim(text,'c.pair_permutations')]
    if select_negative:cs.append(claim(text,'c.pair_permutations',expression='4!=20'))
    r=run(text,cs)
    assert r['score']==0 and r['conflicts'][0]['status']=='CONFLICTING_EVIDENCE'
    assert not r['conflicts'][0]['resolved'] and r['review_recommended']


def test_conflicting_extractor_context_is_preserved_and_blocked():
    text,cs=sample('c.pair_permutations');cs.append(dict(cs[0],assertion_status='negated',polarity='negative'))
    r=run(text,cs)
    assert len(r['extracted_evidence'])==2 and r['conflicts'] and r['score']==0


def test_double_counting_uses_original_max_of():
    ids=['c.pair_permutations','c.pair_orientations','c.total','c.counting_product']
    text='c) '+'\n'.join(': '.join(VALUES[i]) for i in ids)
    r=run(text,[claim(text,i) for i in ids])
    assert r['score']==5 and sum(c['points'] for c in r['credits'])==5


def test_technical_error_does_not_erase_other_credits(monkeypatch):
    from confia_lean_auditor.experimental.tme_p2_checker_first import engine
    def broken():raise ValueError('test finite certificate failure')
    monkeypatch.setattr(engine,'finite_certificate',broken)
    text='a) pair_sum: 10\nc) pair_permutations: 4!=24'
    r=run(text,[claim(text,'a.pair_sum'),claim(text,'c.pair_permutations')])
    assert r['score']==1 and r['technical_uncertainty'] and r['review_recommended']
    assert r['pauta_assessment']['score'] is None
    assert next(a for a in r['awards'] if a['obligation_id']=='a.pair_sum')['eligible']
    assert not next(a for a in r['awards'] if a['obligation_id']=='c.pair_permutations')['eligible']


def test_no_checker_result_can_be_promoted_by_award_gate():
    text,cs=sample('c.pair_permutations');units=bind_evidence(json.dumps({'evidence':cs}),text,'test')
    mapping=ObligationMapper().map(SourceDocument.parse(text),units)
    _,awards=award('no-check',units,mapping,[],[])
    assert not any(a['eligible'] for a in awards)


def test_api_error_fallback_is_exact_current_and_no_second_provider_call():
    text='c) total: 384';calls=[]
    def failed(*args):calls.append(1);raise TimeoutError('secret must not be recorded')
    r=evaluate('fallback',PROBLEM_ID,text,extraction_provider=failed,use_lean=False)
    bridge,assessment=primary_audit(PROBLEM_ID,SourceDocument.parse(text).items,solution_id='fallback',use_lean=False)
    assert len(calls)==1 and r['requested_mode']=='TME_SEMANTIC_FORMAL'
    assert r['effective_mode']=='TME_CURRENT_FALLBACK' and r['fallback_reason']=='TimeoutError'
    assert r['current_bridge']==bridge.model_dump(mode='json') and r['current_assessment']==assessment.model_dump(mode='json')
    assert r['score']==1


CASES=json.loads((ROOT/'tests/fixtures/tme2_p2_digital/cases.json').read_text())
TEXT_CASES=[c for c in CASES if 'text' in c and isinstance(c['text'],str) and 'solution' not in c]
@pytest.mark.parametrize('case',TEXT_CASES,ids=lambda c:c['id'])
def test_current_wrapper_preserves_existing_text_regressions(case):
    text=case['item']+') '+case['text'];document=SourceDocument.parse(text)
    bridge,assessment=primary_audit(PROBLEM_ID,document.items,solution_id=case['id'],use_lean=False)
    def forbidden(*args):pytest.fail('baseline cannot call extractor')
    r=evaluate(case['id'],PROBLEM_ID,text,mode='tme_current',extraction_provider=forbidden,use_lean=False)
    assert r['current_bridge']==bridge.model_dump(mode='json') and r['current_assessment']==assessment.model_dump(mode='json')
    assert not r['fallback_used'] and r['extractor']['api_calls']==0


def runner():
    spec=importlib.util.spec_from_file_location('runner_p2',ROOT/'scripts/evaluation/run_tme_semantic_formal_p2.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_pilot_is_prepared_source_only_and_not_executed():
    module=runner();cases,hashes=module.load_inputs(ROOT/'tests/fixtures/tme_semantic_formal_p2/dev_sources.json',ROOT/'tests/fixtures/tme_semantic_formal_p2/dev_ids.json')
    assert len(cases)==8 and hashes and all(c.problem_id==PROBLEM_ID for c in cases)


@pytest.mark.parametrize('field',['points','gold','baseline_score','expected_score'])
def test_runner_forbids_labelled_payloads_without_loading_any_dataset(field):
    with pytest.raises(ValueError):runner().InputCase.model_validate(dict(case_id='x',problem_id=PROBLEM_ID,solution_text='',**{field:0}))


@pytest.mark.parametrize('value',['/private/tmp/holdout/absent.json','/private/tmp/gold/absent.json'])
def test_runner_refuses_forbidden_paths_before_read(value):
    with pytest.raises(ValueError,match='forbidden'):runner().load_inputs(value,'/private/tmp/nonexistent-ids.json')


def test_wrong_problem_and_item_rejected():
    with pytest.raises(ValueError):evaluate('x','TME2026P3','a) test')
    with pytest.raises(ValueError):SourceDocument.parse('d) test')


def test_native_notation_whitespace_is_not_a_mathematical_change():
    text='c) pair_permutations: 4! = 24'
    r=run(text,[claim(text,'c.pair_permutations',span='pair_permutations: 4! = 24')])
    assert r['score']==2 and r['obligation_mapping'][0]['accepted']


def test_duplicate_positive_lines_do_not_multiply_credit():
    span='pair_permutations: 4!=24';text='c) '+span+'\n'+span
    units=[u for u in evidence_units(text) if u.exact_text==span]
    template=claim('c) '+span,'c.pair_permutations')
    cs=[dict(template,source_evidence_ids=[u.evidence_id]) for u in units]
    r=run(text,cs)
    assert len(r['extracted_evidence'])==2 and r['score']==2 and sum(c['points'] for c in r['credits'])==2


def test_current_awards_and_credits_are_traceable_without_extra_verification():
    r=evaluate('baseline',PROBLEM_ID,'c) total: 384',mode='tme_current',use_lean=False)
    assert len(r['awards'])==23 and sum(c['points'] for c in r['credits'])==r['score']==1
    assert r['verification_results'][0]['status']=='DETERMINISTIC_VERIFIED'


def test_current_preserves_existing_conflicts_and_rejections_in_trace():
    text='c) pair_permutations: 4!=24\npair_permutations: 4!=20'
    r=evaluate('baseline-conflict',PROBLEM_ID,text,mode='tme_current',use_lean=False)
    assert r['score']==0 and r['conflicts'] and len(r['rejected_evidence'])==2
    assert r['conflicts'][0]['status']=='CONFLICTING_EVIDENCE'
    assert not r['conflicts'][0]['resolved']
