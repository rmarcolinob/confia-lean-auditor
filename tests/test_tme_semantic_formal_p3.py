"""Synthetic source-only providers; real frozen mathematics, no API calls."""
import copy
import json
from pathlib import Path
import pytest
from confia_lean_auditor.experimental.tme_semantic_formal_p3.engine import evaluate
from confia_lean_auditor.experimental.tme_semantic_formal_p3.evidence import bind_evidence
from confia_lean_auditor.experimental.tme_semantic_formal_p3.extractor import SemanticExtractorP3
from confia_lean_auditor.experimental.tme_semantic_formal_p3.mapper import SourceDocument,ObligationMapper
from confia_lean_auditor.experimental.tme_semantic_formal_p3.registry import REGISTRY,PROBLEM_ID
from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.student_claims.tme2_p3_digital import VOCABULARY
from confia_lean_auditor.tme.obligation_experiment import primary_audit

ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/'tests/fixtures/tme2_p3_digital/cases.json').read_text())
COMPLETE_C='''continuar: {1,2}
estrategia_1: preta
contagem_1: 3
condicional_1: 3/6=1/2
estrategia_2: cinza
contagem_2: 3
condicional_2: 3/6=1/2
total: (1/6)*(1/2)+(1/6)*(1/2)=1/6'''
VALUES={
 'a.bottom_white_count':('inferiores_brancas','2'),
 'a.first_white_probability':('primeira_branca','1/3'),
 'b.ordered_pairs':('pares_ordenados','6*6=36'),
 'b.different_favorable':('favoraveis_distintos','2*5=10'),
 'b.same_compartment':('repeticao_branca','{6}'),
 'b.second_white_probability':('segunda_branca','(10+1)/36=11/36'),
 'c.continue_compartments':('continuar','{1,2}')}

def claim(text,subject,expression,*,span=None,oids=None,item=None,index=0,**changes):
    span=span or subject+': '+expression
    units=[u for u in evidence_units(text) if u.exact_text==span];u=units[index]
    oids=oids or [o for o,s in REGISTRY.items() if subject in s.subjects]
    c=dict(source_evidence_ids=[u.evidence_id],source_span=span,item_id=item or oids[0][0],
        asserted_content=span,normalized_claim=expression,subject=subject,claim_type=VOCABULARY[subject]['kind'],
        assertion_status='asserted',polarity='positive',scope='main_argument',hypothetical=False,abandoned=False,
        attributed_to_student=True,obligation_candidates=oids,route_candidate='SEMANTIC',confidence=0.5)
    c.update(changes);return c

def typed_claims(text):
    rows=[]
    for u in evidence_units(text):
        key,sep,value=u.exact_text.partition(':')
        if sep and key in VOCABULARY: rows.append(claim(text,key,value.strip(),span=u.exact_text))
    return rows

def provider(claims):
    def provide(payload,schema,config):
        return json.dumps({'evidence':claims}),dict(status='completed',model=config['model'],api_calls=0)
    return provide

def run(text,claims=None,**kw):
    return evaluate('unit-p3',PROBLEM_ID,text,extraction_provider=provider(typed_claims(text) if claims is None else claims),use_lean=False,**kw)

def sample(oid):
    if oid.startswith('c.') and oid!='c.continue_compartments': return 'c) '+COMPLETE_C
    if oid=='b.alternative_complete': return 'b) '+next(c['text'] for c in CASES if c['id']=='b_tree')
    return oid[0]+') '+': '.join(VALUES[oid])

def award(r,oid):return next(a for a in r['awards'] if a['obligation_id']==oid)
def result(r,oid):return next(v for v in r['verification_results'] if v['obligation_id']==oid and v.get('original_fact'))

@pytest.mark.parametrize('oid',list(REGISTRY))
def test_all_thirteen_obligations_use_frozen_strong_checks(oid):
    r=run(sample(oid));v=result(r,oid)
    assert award(r,oid)['eligible'],(r['obligation_mapping'],v)
    assert v['route']==REGISTRY[oid].route and v['status'] in {'DETERMINISTIC_VERIFIED','COMPOSITE_VERIFIED'}
    assert v['verification_id'] and v['sufficiency_decision']['sufficient'] and not r['fallback']
    assert isinstance(r['score'],float) and sum(c['points'] for c in r['credits'])==r['score']

@pytest.mark.parametrize('oid',list(REGISTRY))
def test_route_suggestion_cannot_override_registry(oid):
    text=sample(oid);claims=typed_claims(text)
    for c in claims:c['route_candidate']='FORMAL'
    r=run(text,claims)
    m=next(m for m in r['obligation_mapping'] if m['obligation_id']==oid)
    assert m['accepted'] and m['effective_route']==REGISTRY[oid].route and m['route_override_reason']

@pytest.mark.parametrize('change',[
 {'assertion_status':'hypothetical'},{'assertion_status':'negated'},{'assertion_status':'abandoned'},
 {'assertion_status':'quoted'},{'assertion_status':'unclear'},{'polarity':'negative'},
 {'hypothetical':True},{'abandoned':True},{'attributed_to_student':False},
 {'scope':'exploration'},{'scope':'side_calculation'},{'scope':'unknown'}])
def test_model_flags_cannot_override_source_validated_adoption(change):
    text=sample('b.ordered_pairs');claims=typed_claims(text);claims[0].update(change)
    r=run(text,claims)
    # Approved architecture: flags are suggestions; source and checker decide.
    assert r['score']==2 and r['verification_results'][0]['status']=='COMPOSITE_VERIFIED'
    assert r['discourse_decisions'][0]['resolved_discourse_state']=='ACTIVE'

@pytest.mark.parametrize('prefix',['Suponha:\n','Não é verdade:\n','Tentativa descartada:\n','Citação:\n','Segundo João: '])
def test_source_context_overrules_hostile_model(prefix):
    text='b) '+prefix+'pares_ordenados: 6*6=36'
    span=prefix+'pares_ordenados: 6*6=36' if '\n' not in prefix else 'pares_ordenados: 6*6=36'
    r=run(text,[claim(text,'pares_ordenados','6*6=36',span=span)])
    assert r['score']==0 and r['verification_results'][0]['status']=='CONTEXT_REJECTED'

def test_rejected_context_does_not_erase_independent_valid_span():
    text='a) Hipótese não adotada: primeira_branca: 1/2\n\nMinha resposta: primeira_branca: 1/3'
    claims=[claim(text,'primeira_branca','1/2',span='Hipótese não adotada: primeira_branca: 1/2'),
            claim(text,'primeira_branca','1/3',span='Minha resposta: primeira_branca: 1/3')]
    r=run(text,claims)
    assert r['score']==2 and any(v['status']=='CONTEXT_REJECTED' for v in r['verification_results'])

@pytest.mark.parametrize('subject,expr,span,oid',[
 ('inferiores_brancas','2','Há duas bolas brancas embaixo.','a.bottom_white_count'),
 ('primeira_branca','1/3','A probabilidade da primeira branca é 1/3.','a.first_white_probability'),
 ('pares_ordenados','6*6=36','O espaço amostral de pares ordenados tem 6*6=36 possibilidades.','b.ordered_pairs'),
 ('favoraveis_distintos','2*5=10','Os casos favoráveis com compartimentos diferentes são 2*5=10.','b.different_favorable'),
 ('repeticao_branca','{6}','Ao repetir o mesmo compartimento, somente o sexto libera branca.','b.same_compartment'),
 ('segunda_branca','(10+1)/36=11/36','A probabilidade da segunda branca é (10+1)/36=11/36.','b.second_white_probability'),
 ('continuar','{1,2}','O jogo continua somente nos compartimentos 1 e 2.','c.continue_compartments')])
def test_source_bound_verbal_normalization(subject,expr,span,oid):
    text=oid[0]+') '+span;r=run(text,[claim(text,subject,expr,span=span)])
    assert award(r,oid)['eligible'],r['obligation_mapping']
    e=r['extracted_evidence'][0];assert text[e['source_start']:e['source_end']]==span

@pytest.mark.parametrize('case,color',[(1,'preta'),(2,'cinza')])
def test_state_condition_and_color_count_are_not_unadopted_hypothesis(case,color):
    span=f'Após sair branca do compartimento {case}, escolho {color}, que aparece três vezes.'
    text='c) '+span
    r=run(text,[claim(text,f'estrategia_{case}',color,span=span),claim(text,f'contagem_{case}','3',span=span)])
    assert r['score']==2 and award(r,f'c.strategy_case_{case}')['eligible']

@pytest.mark.parametrize('item,subject,expr,score',[
 ('a','primeira_branca','1/3',2),('b','segunda_branca','11/36',2),('c','total','1/6',0)])
def test_result_only_credit_matches_contract(item,subject,expr,score):
    text=item+') '+expr
    r=run(text,[claim(text,subject,expr,span=expr)])
    assert r['score']==score and isinstance(r['score'],float)
    assert all(v['formal_status']=='FORMAL_NOT_ATTEMPTED' for v in r['verification_results'])

@pytest.mark.parametrize('subject,expr', [('pares_ordenados','36'),('pares_ordenados','36=36'),
    ('favoraveis_distintos','10'),('favoraveis_distintos','10=10')])
def test_true_numbers_do_not_invent_justification(subject,expr):
    r=run('b) '+subject+': '+expr)
    assert r['score']==0 and r['verification_results'][0]['status']=='COMPOSITE_INCOMPLETE'

@pytest.mark.parametrize('subject,expr', [('pares_ordenados','6*5=30'),('favoraveis_distintos','2*6=12'),
 ('repeticao_branca','{5}'),('segunda_branca','(9+2)/36=11/36'),('segunda_branca','1/2')])
def test_falsity_is_preserved(subject,expr):
    r=run('b) '+subject+': '+expr)
    assert r['score']==0 and any(v['mathematical_refutation'] for v in r['verification_results'])

@pytest.mark.parametrize('body',[
 'segunda_branca: 11/36\nsegunda_branca: 12/36',
 'repeticao_branca: {6}\nrepeticao_branca: {5}',
 'estrategia_1: preta\nestrategia_1: cinza\ncontagem_1: 3'])
@pytest.mark.parametrize('reverse',[False,True])
def test_material_conflicts_keep_independent_credit(body,reverse):
    item='c' if 'estrategia' in body else 'b'
    if reverse:body='\n'.join(reversed(body.splitlines()))
    text='a) inferiores_brancas: 2\n'+item+') '+body;r=run(text)
    assert r['score']==2 and r['conflicts'] and r['review_recommended']
    assert award(r,'a.bottom_white_count')['eligible']
    assert any(v['mathematical_refutation'] for v in r['verification_results'])

def test_omitted_typed_negative_cannot_be_hidden_by_extractor():
    text='b) segunda_branca: 11/36\nsegunda_branca: 12/36'
    r=run(text,[typed_claims(text)[0]])
    assert r['score']==0 and r['conflicts']

def test_guard_is_veto_only_not_positive_evidence():
    r=run('a) inferiores_brancas: 2\nprimeira_branca: 1/3',[])
    assert r['score']==0 and not any(a['eligible'] for a in r['awards'])

@pytest.mark.parametrize('field,value',[('source_span','fabricated'),('source_evidence_ids',['E999']),
 ('obligation_candidates',['c.invented']),('subject','invented'),('points',20),('confidence',2)])
def test_schema_binding_failures_fallback_explicitly(field,value):
    text=sample('a.bottom_white_count');cs=typed_claims(text);cs[0][field]=value
    r=run(text,cs)
    assert r['fallback'] and r['fallback_used'] and r['effective_mode']=='TME_SEMANTIC_FORMAL_NATIVE_FALLBACK'
    assert r['fallback_reason'] and r['score']==2 and not r['extracted_evidence']

def test_api_failure_fallback_is_numeric_and_explicit():
    def unavailable(*args):raise TimeoutError('test transport only')
    r=evaluate('unavailable',PROBLEM_ID,'a) 1/3',extraction_provider=unavailable,use_lean=False)
    assert r['score']==2 and r['fallback'] and 'TimeoutError' in r['fallback_reason']

@pytest.mark.parametrize('change',[{'item_id':'c'},{'obligation_candidates':['a.first_white_probability']},
 {'subject':'primeira_branca'},{'claim_type':'qualitative'},{'normalized_claim':'2*5=10'}])
def test_wrong_item_subject_type_or_payload_cannot_award(change):
    text=sample('b.ordered_pairs');cs=typed_claims(text);cs[0].update(change);r=run(text,cs)
    assert not r['fallback'] and r['score']==0 and not r['obligation_mapping'][0]['accepted']

@pytest.mark.parametrize('source,expr',[
 ('A probabilidade da primeira branca é 2/6=1/2.','2/6'),
 ('A probabilidade da primeira branca é 2/6=1/2.','1/2'),
 ('Há doze bolas brancas embaixo.','2'),
 ('O espaço amostral de pares ordenados tem 36 possibilidades.','6*6=36')])
def test_normalization_cannot_invent_or_trim_arithmetic(source,expr):
    subject='inferiores_brancas' if 'embaixo' in source else 'pares_ordenados' if 'pares' in source else 'primeira_branca'
    item='b' if subject=='pares_ordenados' else 'a';text=item+') '+source
    r=run(text,[claim(text,subject,expr,span=source)])
    assert r['score']==0 and not r['obligation_mapping'][0]['accepted']

def test_confidence_cannot_change_credit_and_ids_are_local():
    text=sample('a.bottom_white_count');cs=typed_claims(text)
    cs[0]['confidence']=0;r0=run(text,cs);cs[0]['confidence']=1;r1=run(text,cs)
    assert r0['score']==r1['score']==2
    assert r0['extracted_evidence'][0]['evidence_id']==r1['extracted_evidence'][0]['evidence_id']
    units=bind_evidence(json.dumps({'evidence':cs*2}),text,'fake');assert len(units)==1
    bad=SourceDocument.parse(text+' extra')
    assert ObligationMapper().map(bad,units)[0]['reason']=='source_binding_changed'

def test_payload_config_no_grading_authority():
    ex=SemanticExtractorP3();p=ex.payload(PROBLEM_ID,'a) 1/3');schema=ex.schema('a) 1/3')
    assert ex.configuration()['model']=='gpt-6.1-sol' and ex.configuration()['reasoning_effort']=='medium'
    assert ex.configuration()['timeout']==180 and ex.configuration()['max_retries']==0 and ex.configuration()['store'] is False
    assert len(p['obligations'])==13 and not schema['additionalProperties']
    def keys(x):
        if isinstance(x,dict):
            for k,v in x.items():yield k;yield from keys(v)
        if isinstance(x,(list,tuple)):
            for v in x:yield from keys(v)
    assert not set(keys(p))&{'score','points','gold','awards','baseline','expected_score'}

@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id'])
def test_tme_current_preserved_exactly(case):
    text=case['item']+') '+case['text']
    before=primary_audit(PROBLEM_ID,{case['item']:case['text']},solution_id='same',use_lean=False)
    r=evaluate('same',PROBLEM_ID,text,mode='tme_current',use_lean=False)
    after=primary_audit(PROBLEM_ID,{case['item']:case['text']},solution_id='same',use_lean=False)
    assert r['score']==case['points'] and not r['fallback']
    assert before[0].model_dump(mode='json')==after[0].model_dump(mode='json')
    assert before[1].model_dump(mode='json')==after[1].model_dump(mode='json')

def test_dev_is_source_only_and_runner_loads_without_execution():
    from scripts.evaluation.run_tme_semantic_formal_p3 import load_inputs
    cases,hashes=load_inputs(ROOT/'tests/fixtures/tme_semantic_formal_p3/dev_sources.json',ROOT/'tests/fixtures/tme_semantic_formal_p3/dev_ids.json')
    assert len(cases)==8 and len(hashes)==4
    assert all(set(c.model_dump())=={'case_id','problem_id','solution_text'} for c in cases)

def test_checker_error_preserves_independent_credit(monkeypatch):
    import confia_lean_auditor.experimental.tme_p3_checker_first.engine as checker
    def fail(machine):raise ValueError('injected certificate error')
    monkeypatch.setattr(checker,'finite_certificate',fail)
    r=run('a) inferiores_brancas: 2\nb) pares_ordenados: 6*6=36')
    assert r['score']==2 and r['technical_uncertainty'] and not r['fallback']
    assert result(r,'b.ordered_pairs')['status']=='COMPOSITE_ERROR'

@pytest.mark.parametrize('subject,expr,span',[
 ('repeticao_branca','{6}','Ao repetir o mesmo compartimento, o quinto e o sexto liberam branca.'),
 ('contagem_1','3','Após sair do compartimento 2, preta aparece três vezes.'),
 ('inferiores_brancas','2','Segundo Pedro, há duas bolas brancas embaixo.'),
 ('inferiores_brancas','2','Maria afirmou: há duas bolas brancas embaixo.')])
def test_wrong_set_case_and_unadopted_attribution(subject,expr,span):
    item=next(o[0] for o,s in REGISTRY.items() if subject in s.subjects)
    text=item+') '+span;r=run(text,[claim(text,subject,expr,span=span)])
    assert r['score']==0 and not r['obligation_mapping'][0]['accepted']

def test_written_equality_keeps_formal_route_when_lean_disabled():
    text='a) primeira_branca: 2/6=1/3';r=run(text)
    v=result(r,'a.first_white_probability')
    assert v['route']=='FORMAL' and v['formal_status']=='FORMAL_NOT_ATTEMPTED'
    assert not v['formal_attempted'] and r['score']==0

def test_changed_model_polarity_is_resolved_from_written_positive_assertion():
    text='a) primeira_branca: 1/3';cs=typed_claims(text);cs.append(dict(cs[0],polarity='negative'))
    r=run(text,cs)
    assert r['score']==2 and not r['conflicts']
    assert all(d['resolved_discourse_state']=='ACTIVE' for d in r['discourse_decisions'])

@pytest.mark.parametrize('fails',[False,True])
def test_transport_configuration_and_zero_hidden_retries(monkeypatch,fails):
    import openai
    from types import SimpleNamespace
    calls=[];init=[];text='a) inferiores_brancas: 2'
    class FakeClient:
        def __init__(self,**kw):init.append(kw);self.responses=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def create(self,**kw):
            calls.append(kw)
            if fails:raise TimeoutError('no real network')
            return SimpleNamespace(output_text=json.dumps({'evidence':typed_claims(text)}),status='completed',
                                   model='gpt-6.1-sol',id='test-response',usage=None)
    monkeypatch.setattr(openai,'OpenAI',FakeClient)
    units,meta=SemanticExtractorP3().extract(PROBLEM_ID,text)
    assert len(calls)==1 and init==[dict(timeout=180,max_retries=0)]
    assert calls[0]['store'] is False and calls[0]['model']=='gpt-6.1-sol'
    assert calls[0]['reasoning']['effort']=='medium' and calls[0]['text']['format']['strict']
    assert meta['status']==('unavailable' if fails else 'completed')

def test_runner_manifest_and_separate_modes_without_pilot(monkeypatch,tmp_path):
    from scripts.evaluation import run_tme_semantic_formal_p3 as runner
    dataset=tmp_path/'source.json';ids=tmp_path/'ids.json'
    dataset.write_text(json.dumps([dict(case_id='unit-only',problem_id=PROBLEM_ID,solution_text='a) 1/3')]))
    ids.write_text(json.dumps(['unit-only']))
    called=[]
    def fake(case_id,problem_id,text,**kw):
        called.append((case_id,kw['mode']))
        return dict(case_id=case_id,score=0.,fallback_used=True,fallback_reason='injected test',
                    effective_mode='TME_CURRENT_FALLBACK',technical_uncertainty=False,configuration_hashes={},verification_results=[])
    monkeypatch.setattr(runner,'evaluate',fake)
    for mode in ('tme_current','tme_semantic_formal'):
        output=tmp_path/mode
        assert runner.main(['--mode',mode,'--dataset',str(dataset),'--ids-file',str(ids),'--output-dir',str(output)])==0
        m=json.loads((output/'run_manifest.json').read_text())
        assert m['git_sha'] and m['timestamp'] and isinstance(m['worktree_clean'],bool)
        assert m['fallback'] and m['fallback_cases'][0]['reason']=='injected test'
        assert m['state']=='completed' and m['config']['store'] is False and len(m['input_hashes'])==4
    assert len(called)==2

def test_runner_refuses_labelled_and_duplicate_inputs(tmp_path):
    from scripts.evaluation.run_tme_semantic_formal_p3 import load_inputs,safe_path
    with pytest.raises(ValueError):safe_path(tmp_path/'holdout.json')
    dataset=tmp_path/'source.json';ids=tmp_path/'ids.json';ids.write_text('["unit-only"]')
    dataset.write_text(json.dumps([dict(case_id='unit-only',problem_id=PROBLEM_ID,solution_text='a) 1/3',expected_score=2)]))
    with pytest.raises(ValueError):load_inputs(dataset,ids)

@pytest.mark.parametrize('subject,expr,span',[
 ('inferiores_brancas','2','Há três bolas brancas e duas pretas embaixo.'),
 ('contagem_1','3','Após o compartimento 1, preta aparece duas vezes; há três cores.'),
 ('primeira_branca','1/3','A probabilidade da primeira branca é 1/2; a probabilidade da segunda branca é 1/3.'),
 ('estrategia_1','preta','Após o compartimento 1, não escolho preta.')])
def test_correct_number_or_color_elsewhere_cannot_repair_written_claim(subject,expr,span):
    item=next(o[0] for o,s in REGISTRY.items() if subject in s.subjects)
    text=item+') '+span;r=run(text,[claim(text,subject,expr,span=span)])
    assert r['score']==0 and not r['obligation_mapping'][0]['accepted']
