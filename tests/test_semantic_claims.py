"""Semantic interpretation is untrusted input, never a verification result."""
import json
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from confia_lean_auditor.student_claims import semantic as sem
from confia_lean_auditor.tme.registry import audit_tme
from confia_lean_auditor.core.math_canonical import parse_math
from confia_lean_auditor.core.math_canonical.normalization import mathematical_signs


def candidate(text, subject='expression', expression='x=5', mode='asserted', kind='equality', item='a'):
    return sem.SemanticClaimCandidate(candidate_id='c1',claim_kind=kind,source_text=text,source_start=0,source_end=len(text),
        normalized_payload=sem.NormalizedPayload(subject=subject,expression=expression,item_id=item),assertion_mode=mode)


def provider(monkeypatch,candidates):
    monkeypatch.setenv('CONFIA_TME_SEMANTIC_ENABLED','1')
    monkeypatch.setattr(sem,'request_candidates',lambda *args:(tuple(candidates),{'status':'completed','model':'test'}))
    sem.reset_observations()


def test_schema_strict_and_no_credit_fields():
    schema=sem.SemanticResponse.model_json_schema()
    for obj in (schema,*schema['$defs'].values()):
        if obj.get('type')=='object':
            assert obj['additionalProperties'] is False
            assert set(obj['required'])==set(obj['properties'])
    with pytest.raises(ValidationError):
        candidate('x=5').model_validate({**candidate('x=5').model_dump(),'supported':True})
    with pytest.raises(ValidationError):
        candidate('x=5').model_validate({**candidate('x=5').model_dump(),'source_start':'0'})


def test_wire_payload_and_cache(monkeypatch):
    import openai
    seen=[]
    class Client:
        def __init__(self,**kwargs):self.responses=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def create(self,**kwargs):
            seen.append(kwargs)
            return SimpleNamespace(status='completed',output=[],output_text='{"candidates":[]}',model='test',id='r',usage=None)
    monkeypatch.setattr(openai,'OpenAI',Client)
    sem.request_candidates.cache_clear()
    args=('TME2026P4','statement','text',json.dumps(sem.configuration(),sort_keys=True))
    sem.request_candidates(*args);sem.request_candidates(*args)
    assert len(seen)==1
    wire=json.loads(seen[0]['input'][1]['content'])
    assert set(wire)=={'problem_id','statement','solution_text','ontology'}
    assert set(wire['ontology']['apqr'])=={'kind','values'}
    assert seen[0]['text']['format']['strict'] and not seen[0]['store']
    sem.request_candidates.cache_clear()


@pytest.mark.parametrize('text',[
    'Não é verdade que x=5.', 'Tentei x=5, mas isso está errado.',
    'Se x=5, então...', 'A solução de João diz x=5.',
    'x=5 ... depois concluí que x=7.', 'Na página 5, o exercício fala de x.',
    'Talvez x=5.', '“x=5”.',
])
def test_adversarial_asserted_contexts_fail_closed(text):
    record,event=sem.convert_candidate('TME2_P1_PILOT',text,candidate(text),{'a':(0,len(text))})
    assert not record.source.attributable


@pytest.mark.parametrize('mode',['hypothetical','negated','rejected','quoted','uncertain'])
def test_modes_never_authorize(mode):
    r,_=sem.convert_candidate('TME2_P1_PILOT','x=5',candidate('x=5',mode=mode),{'a':(0,3)})
    assert not r.source.attributable


def test_literal_grounding_unique_relocation_and_repeated_ambiguity():
    c=candidate('x=5')
    assert sem.literal_span(c,'a: x=5')==(3,6,'unique_literal_relocation')
    assert sem.literal_span(c,'a: x=5; x=5') is None
    r,_=sem.convert_candidate('TME2_P1_PILOT','x=7',c,{'a':(0,3)})
    assert r.source.grounding_status=='unresolved' and not r.source.attributable


@pytest.mark.parametrize('text,expr',[('x=7; na página 5','x=5'),('x=12','2'),('x=5-3','x=5+3'),('x=10/30','x=1/3')])
def test_grounded_quote_does_not_license_invented_math(text,expr):
    r,_=sem.convert_candidate('TME2_P1_PILOT',text,candidate(text,expression=expr),{'a':(0,len(text))})
    assert not r.source.attributable


def test_p4_prose_reaches_existing_geometry_checker_and_pauta(monkeypatch):
    text='APQR é um paralelogramo, portanto seu perímetro é 12.'
    cs=[candidate(text,'apqr','parallelogram',kind='geometric_relation',item='b'),
        candidate(text,'perimeter_apqr','12',kind='value',item='b').model_copy(update={'candidate_id':'c2'})]
    provider(monkeypatch,cs)
    bridge,result=audit_tme('TME2026P4',{'b':text},use_lean=False)
    assert result.items[1].points_awarded==0  # Existing checker requires a written perimeter development.
    assert any(r.canonical_form.subject=="perimeter_apqr" and r.source.attributable for r in bridge.auditor.records)
    assert bridge.auditor.facts and all(f.verification_source=='deterministic' for f in bridge.auditor.facts)
    for record in bridge.auditor.records:
        assert record.source.raw_text==text
        assert record.provenance.extraction_method==sem.VERSION
    assert all(f.verification.status=='verified' for f in bridge.auditor.facts)


@pytest.mark.parametrize('prefix',['Não é verdade que ', 'Se ', 'Tentei: ', 'A solução de João diz ', 'Na página 12, '])
def test_false_credit_controls_run_through_pauta(monkeypatch,prefix):
    text=prefix+'APQR é um paralelogramo, portanto seu perímetro é 12.'
    provider(monkeypatch,[candidate(text,'apqr','parallelogram',kind='geometric_relation',item='b'),
        candidate(text,'perimeter_apqr','12',kind='value',item='b')])
    bridge,result=audit_tme('TME2026P4',{'b':text},use_lean=False)
    assert result.items[1].points_awarded==0
    assert not bridge.auditor.facts


def test_p5_qualitative_claims_retained_without_facts(monkeypatch):
    text='Números maiores que quatro podem ser melhorados. Usamos o máximo possível de 3, sobrando dois 2.'
    provider(monkeypatch,[candidate(text,'large_parts_are_improvable','maiores que quatro podem ser melhorados',kind='optimization_assertion',item='c'),
        candidate(text,'optimal_decomposition_prefers_threes','máximo possível de 3',kind='strategy',item='c').model_copy(update={'candidate_id':'c2'}),
        candidate(text,'twos_count','2',kind='count',item='c').model_copy(update={'candidate_id':'c3'})])
    bridge,result=audit_tme('TME2026P5',{'c':text},use_lean=False)
    semantic=[r for r in bridge.auditor.records if r.provenance.extraction_method==sem.VERSION]
    assert len(semantic)==3
    assert sum(r.canonical_form is None for r in semantic)==2
    assert all(not r.source.attributable for r in semantic if r.canonical_form is None)
    assert result.score==0


def test_no_invented_diagram_and_item_rerouting():
    text='O centro é 5.'
    c=candidate(text,'placement','{A:5}',kind='value')
    r,_=sem.convert_candidate('TME2026P2',text,c,{'a':(0,len(text))})
    assert not r.source.attributable
    c=candidate('x=5',item='b')
    r,_=sem.convert_candidate('TME2_P1_PILOT','x=5',c,{'a':(0,3)})
    assert not r.source.attributable


def test_deterministic_priority_and_no_second_interpretation(monkeypatch):
    from confia_lean_auditor.student_claims.tme2_p4_digital import collect_tme2_p4_digital
    text='APQR: parallelogram'
    provider(monkeypatch,[candidate(text,'apqr','parallelogram',kind='geometric_relation',item='b')])
    result=collect_tme2_p4_digital({'b':text})
    assert len(result.records)==1
    assert result.records[0].provenance.extraction_method!=sem.VERSION
    assert sem.observations()[0]['events'][0]['deduplicated']


@pytest.mark.parametrize('sign',['-','−','–'])
def test_unicode_math_signs_preserve_source(sign):
    from confia_lean_auditor.lean.student_claim_checker import _lean_int_expr
    raw=f'5{sign}3=2'
    assert parse_math(raw).status=='parsed'
    assert parse_math(raw).canonical_form==parse_math('5-3=2').canonical_form
    assert _lean_int_expr(raw)=='(5 : ℤ)-3=2'
    assert raw==f'5{sign}3=2'


def test_text_dash_not_math_operator():
    assert mathematical_signs('prova – tentativa')=='prova – tentativa'
    assert mathematical_signs('x – y')=='x – y'
    assert parse_math('prova – tentativa').status!='parsed'


def test_conflicting_named_claims_are_ambiguous(monkeypatch):
    text='O perímetro de APQR é 12. Depois concluí que o perímetro de APQR é 14.'
    cs=[candidate(text,'perimeter_apqr',str(n),kind='value',item='b').model_copy(update={'candidate_id':str(n)}) for n in (12,14)]
    provider(monkeypatch,cs)
    bridge,result=audit_tme('TME2026P4',{'b':text},use_lean=False)
    assert result.score==0 and not bridge.auditor.facts
    assert all(not r.source.attributable for r in bridge.auditor.records if r.provenance.extraction_method==sem.VERSION)


def test_semantic_projection_revalidated_before_p1_verification(monkeypatch):
    from confia_lean_auditor.student_claims.tme2_p1_digital import collect_tme2_p1_digital
    from confia_lean_auditor.lean.student_claim_checkers.tme2_p1 import verify_tme2_p1_digital
    from dataclasses import replace
    text='Os valores são {1,2,3}.'
    provider(monkeypatch,[candidate(text,'collection','{1,2,3}',kind='finite_set')])
    digital=collect_tme2_p1_digital({'a':text})
    record=next(r for r in digital.records if r.provenance.extraction_method==sem.VERSION)
    broken=record.model_copy(update={'canonicalization_reason':'forged'})
    changed=replace(digital,records=tuple(broken if r==record else r for r in digital.records))
    with pytest.raises(ValueError,match='Semantic projection'):
        verify_tme2_p1_digital(changed,'tamper',use_lean=False)


def test_provider_unavailable_keeps_deterministic_results(monkeypatch):
    from confia_lean_auditor.student_claims.tme2_p4_digital import collect_tme2_p4_digital
    monkeypatch.delenv('CONFIA_TME_SEMANTIC_ENABLED',raising=False)
    before=collect_tme2_p4_digital({'b':'APQR: parallelogram'})
    provider(monkeypatch,[])
    monkeypatch.setattr(sem,'request_candidates',lambda *args:((),{'status':'unavailable','reason':'TimeoutError'}))
    after=collect_tme2_p4_digital({'b':'APQR: parallelogram'})
    assert before==after


def test_structured_output_failure_returns_no_candidates(monkeypatch):
    import openai
    class Client:
        def __init__(self,**kwargs):self.responses=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def create(self,**kwargs):
            return SimpleNamespace(status='completed',output=[],output_text='{"candidates":[],"points":6}',model='test',id='r',usage=None)
    monkeypatch.setattr(openai,'OpenAI',Client)
    sem.request_candidates.cache_clear()
    candidates,meta=sem.request_candidates('TME2026P4','','',json.dumps(sem.configuration(),sort_keys=True))
    assert not candidates and meta['status']=='unavailable'
    sem.request_candidates.cache_clear()


@pytest.mark.parametrize('lhs,rhs,expected_status,points,mechanism', [('2*((6-x)+x)','12','verified',6,'student_lean'),('2*((6-x)+x)','13','refuted',0,'canonical_equivalence'),('2*((6-x)+x)+1','12','refuted',0,'student_lean')])
def test_semantic_math_is_checked_by_real_lean(monkeypatch,lhs,rhs,expected_status,points,mechanism):
    text=f'APQR é um paralelogramo. Seu perímetro APQR é {lhs}={rhs}.'
    provider(monkeypatch,[candidate(text,'apqr','parallelogram',kind='geometric_relation',item='b'),
        candidate(text,'perimeter_apqr',f'{lhs}={rhs}',kind='value',item='b').model_copy(update={'candidate_id':'c2'})])
    bridge,result=audit_tme('TME2026P4',{'b':text},use_lean=True)
    assert result.items[1].points_awarded==points
    fact=next(f for f in bridge.auditor.facts if f.fact_id=='b.perimeter_apqr')
    assert fact.verification.status==expected_status
    assert fact.verification_source==mechanism
    assert bool(fact.student_check)==(mechanism=='student_lean')
    assert any(i.startswith('semantic:') for i in fact.source_claim_ids)


def test_subject_schema_uses_only_declared_concepts():
    allowed=sem.response_schema('TME2026P4')['$defs']['NormalizedPayload']['properties']['subject']['enum']
    assert 'apqr' in allowed and 'perimeter_apqr' in allowed and 'unmapped' in allowed
    assert 'placement' not in sem.response_schema('TME2026P2')['$defs']['NormalizedPayload']['properties']['subject']['enum']
    assert not any(x in allowed for x in ('supported','score','points'))


def test_literal_count_needs_explicit_multiplicity():
    for text,expected in [('sobrando dois 2.',True),('Quantidade: 1013.',False)]:
        expr='2' if expected else '1013'
        r,_=sem.convert_candidate('TME2026P5',text,candidate(text,'twos_count',expr,kind='count'),{'a':(0,len(text))})
        assert r.source.attributable==expected


@pytest.mark.parametrize('problem,text,subject,expr,item',[
    ('TME2026P3','2 brancas em 6. 2/6 = 1/3','inferiores_brancas','1/3','a'),
    ('TME2026P3','(1/6)*(1/2)+(1/6)*(1/2)=1/6','condicional_2','1/6','c'),
    ('TME2026P3','Logo P = 2/6 = 1/3.','total','1/3','a'),
    ('TME2026P2','Em cada linha, troca as pontas: 2^4 = 16','counting_product','2^4','c'),
    ('TME2026P5','para n >= 5, verdade.','one_domain','n >= 5','b'),
])
def test_correct_quote_cannot_license_wrong_concept(problem,text,subject,expr,item):
    r,_=sem.convert_candidate(problem,text,candidate(text,subject,expr,item=item),{item:(0,len(text))})
    assert not r.source.attributable


@pytest.mark.parametrize('sign',['-','−','–'])
def test_unicode_subtraction_is_not_split_into_a_false_tail(sign):
    from confia_lean_auditor.student_claims.generic_math import math_runs, extract_generic_math
    raw=f'731 {sign} 137 = 594'
    assert list(math_runs(raw))==[(0,len(raw),raw)]
    claims=extract_generic_math('TME2_P1_PILOT',raw)
    assert len(claims)==1 and claims[0].raw_text==raw
    assert claims[0].data['expression']==raw
