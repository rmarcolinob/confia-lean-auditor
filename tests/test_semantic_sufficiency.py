import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from confia_lean_auditor.student_claims import semantic_sufficiency as sem
from confia_lean_auditor.student_claims.sufficiency_requirements import requirements
from confia_lean_auditor.student_claims.sufficiency_context import item_regions,annotated_units,link_evidence
from confia_lean_auditor.tme.sufficiency_experiment import run_sufficiency_shadow
from confia_lean_auditor.tme.obligation_experiment import primary_audit
from test_tme_hybrid_grader import judgment


def req(oid,p='TME2026P4'):
    return next(r for r in requirements(p) if r['obligation_id']==oid)


def gate_provider(state):
    def provider(payload):
        return tuple(sem.SufficiencyDecision(obligation_id=o['obligation_id'],sufficiency=state,
            evidence_ids=[e['evidence_id'] for e in o['selected_evidence']],
            reason_code='adequate_evidence' if state=='sufficient' else 'contradictory_mathematics' if state=='contradictory' else 'missing_step',
            concise_rationale='Independent fixture judgment.') for o in payload['obligations']),dict(status='completed',api_calls=0)
    return provider


def run(text,j,*,state='sufficient',problem='TME2026P4',items=None):
    bridge,_=primary_audit(problem,items or {},solution_id='s',use_lean=False)
    return run_sufficiency_shadow(problem,text,(j,),bridge,bridge,provider=gate_provider(state))


@pytest.mark.parametrize('p',[f'TME2026P{i}' for i in range(1,6)])
def test_all_obligations_have_closed_point_free_requirements(p):
    rs=requirements(p);assert len({r['obligation_id'] for r in rs})==len(rs)
    assert {r['evidence_requirement'] for r in rs}<={'FINAL_ANSWER','FACT','INTERMEDIATE_STEP','JUSTIFICATION','COMPLETE_METHOD','ENUMERATION','STRATEGY'}
    assert not {'score','points','max_points'}&{k for r in rs for k in r}


@pytest.mark.parametrize('text',[
 '(b) abc-cba = (100a+10b+c)-(100c+10b+a)\n=99(a-c).\n(c) resultados.',
 '(b) abc − cba = 99(a − c). (c) Lista.',
 'Em (b), temos a diferença 99(a-c). Em (c), a lista.',
])
def test_algebraic_closing_parentheses_never_create_item_markers(text):
    regions=item_regions(text)
    assert [r['item_id'] for r in regions if r['item_id']] == ['b','c']
    assert next(r for r in regions if r['item_id']=='b')['end']==text.index('(c)')


def test_item_reference_does_not_restart_an_item():
    text='(b) n>=5.\n(c) Pelo item (b), removemos parcelas grandes.\n(d) Pelo item anterior, contamos.'
    assert [r['item_id'] for r in item_regions(text)]==['b','c','d']


def test_single_unit_multiple_items_has_exact_narrowed_views():
    text='(a) PQ=x. (b) APQR é um paralelogramo; o dobro dos lados x e 6-x é 12. (c) x=5/3.'
    units=annotated_units(text);unit=next(u for u in units if 'APQR' in u['exact_text'])
    assert unit['multiple_items'] and unit['item_id'] is None
    link=link_evidence(text,req('b.perimeter_apqr'),[unit['evidence_id']])
    assert link['valid']
    parts=link['bindings'][0]['authorized_slices'];assert all(p['item_id']=='b' for p in parts)
    assert all(text[p['source_start']:p['source_end']]==p['exact_text'] for p in parts)
    assert 'x=5/3' not in parts[0]['exact_text']


def test_header_only_cannot_be_repaired_from_context_even_with_hostile_gate():
    r=run('(a) lista (2,3,3,3).',judgment('a.candidate'),problem='TME2026P5')
    assert r.decisions[0].reason_code=='header_only'
    assert r.potential_assessment.score==0


def test_wrong_item_default_and_declared_or_textual_exceptions():
    text='(a) PQ=x.\n(b) Calculamos o perímetro.'
    a=next(u['evidence_id'] for u in annotated_units(text) if u['exact_text']=='PQ=x.')
    assert not link_evidence(text,req('b.ap'),[a])['valid']
    link=link_evidence(text,req('b.pq'),[a]);assert link['valid'] and link['exceptions'][0]['authorization']=='declared_cross_item_obligation'
    explicit='(a) AP=6-x.\n(b) Pelo item (a), usamos o valor.'
    a=next(u['evidence_id'] for u in annotated_units(explicit) if u['exact_text']=='AP=6-x.')
    link=link_evidence(explicit,req('b.ap'),[a]);assert link['valid'] and link['exceptions'][0]['authorization']=='explicit_textual_reference'


def test_gate_wire_is_independent_of_first_rationale_reference_and_confidence():
    text='(b) APQR é um paralelogramo, perímetro 12.'
    j=judgment('b.perimeter_apqr',('E002',),concise_rationale='SECRET_BIAS_CORRECT_ANSWER',method_path='SECRET_METHOD',confidence='low')
    payload,_,_=sem.SemanticSufficiencyGate().prepare('TME2026P4',text,(j,))
    wire=json.dumps(payload)
    assert all(v not in wire for v in ['SECRET_BIAS','SECRET_METHOD','official_reference','extracted_mathematical_statements','TeacherDecision','synthetic_expected_score','max_points','semantic_judgment'])
    assert payload['obligations'][0]['evidence_requirement']=='COMPLETE_METHOD'


@pytest.mark.parametrize('state,status,tier',[('sufficient','supported','SEMANTIC_SUPPORTED'),('insufficient','indeterminate','SEMANTIC_NOT_SUPPORTED'),('uncertain','indeterminate','INDETERMINATE'),('contradictory','indeterminate','CONFLICT')])
def test_only_independent_sufficient_can_promote_without_automatic_audit(state,status,tier):
    text='(b) APQR é um paralelogramo; perímetro é o dobro de x+(6-x), portanto 12.'
    r=run(text,judgment('b.perimeter_apqr',('E002',)),state=state)
    t=next(t for t in r.reconciliation if t['obligation_id']=='b.perimeter_apqr')
    assert t['decision']==status and t['evidence_tier']==tier
    assert r.potential_assessment.score==(2 if state=='sufficient' else 0)


@pytest.mark.parametrize('prefix,suffix',[
 ('Não é verdade que ',''),('Suponha que ',''),('Tentei: ',' mas está errado.'),
 ('João disse que ',''),('“','”'),('','\n\nIsso estava errado.'),
 ('','\n(c) Descartei o resultado anterior; estava errado.'),
 ('','\nDepois concluí que não era isso.'),
])
def test_global_negative_context_overrides_hostile_sufficiency(prefix,suffix):
    text='(b) '+prefix+'APQR é um paralelogramo; perímetro é 12.'+suffix
    r=run(text,judgment('b.perimeter_apqr',('E002',)))
    assert r.potential_assessment.score==0


@pytest.mark.parametrize('field',['score','points','supported','refuted','source_start','source_end'])
def test_gate_schema_forbids_scoring_and_offsets(field):
    d=dict(obligation_id='b.apqr',sufficiency='sufficient',evidence_ids=['E001'],reason_code='adequate_evidence',concise_rationale='ok');d[field]=1
    with pytest.raises(ValidationError):sem.SufficiencyDecision.model_validate(d)


def test_schema_requires_every_requested_obligation_and_no_new_ids():
    payload,_,_=sem.SemanticSufficiencyGate().prepare('TME2026P4','APQR é um paralelogramo.',(judgment('b.apqr'),))
    schema=sem.response_schema(payload)
    assert schema['properties']['decisions']['required']==['b.apqr']
    with pytest.raises(ValueError):sem.validate_response('{"decisions":{}}',payload)
    d=sem.SufficiencyDecision(obligation_id='b.apqr',sufficiency='sufficient',evidence_ids=['E999'],reason_code='adequate_evidence',concise_rationale='ok')
    with pytest.raises(ValueError):sem.validate_response(json.dumps({'decisions':{'b.apqr':d.model_dump()}}),payload)


def test_formal_deterministic_evidence_has_precedence_and_conditional_binding_survives():
    cases=json.loads((Path(__file__).parent/'fixtures/tme2_p5_digital/cases.json').read_text())
    items=next(c['solution'] for c in cases if c['id']=='d_cf_valid')
    text='\n'.join(f'({k}) {v}' for k,v in items.items());bridge,_=primary_audit('TME2026P5',items,solution_id='s',use_lean=False)
    r=run_sufficiency_shadow('TME2026P5',text,(),bridge,bridge,provider=gate_provider('insufficient'))
    assert r.potential_assessment.items[3].carry_forward_applied and r.potential_assessment.items[3].points_awarded==1
    old={e.obligation_id:e for e in bridge.evidence.obligations};new={e.obligation_id:e for e in r.evidence.obligations}
    assert all(old[k]==new[k] for k in ['c.threes_count','d.cf_adoption','d.cf_dependency','d.cf_coherence'])


def test_provider_failure_is_technical_not_refutation():
    text='(b) APQR é um paralelogramo.';bridge,_=primary_audit('TME2026P4',{},solution_id='s',use_lean=False)
    r=run_sufficiency_shadow('TME2026P4',text,(judgment('b.apqr',('E002',)),),bridge,bridge,
        provider=lambda p:((),dict(status='unavailable')))
    assert next(e for e in r.evidence.obligations if e.obligation_id=='b.apqr').status=='technical_error'


def test_heading_plus_actual_selected_source_is_not_rejected_as_heading_only():
    text='(a) Lista (2,3,3,3), cuja soma é 11.'
    r=run(text,judgment('a.candidate',('E001','E002')),problem='TME2026P5')
    assert r.decisions[0].sufficiency=='sufficient'
    assert r.potential_assessment.score==2


def test_provider_has_fixed_model_store_false_and_preserves_invalid_raw(monkeypatch):
    from types import SimpleNamespace
    import openai
    calls=[]
    class Client:
        def __init__(self,**kw):assert kw['max_retries']==0;self.responses=self
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def create(self,**kw):
            calls.append(kw);return SimpleNamespace(status='completed',model=kw['model'],id='fixture',output_text='{"decisions":{}}',usage=None)
    monkeypatch.setattr(openai,'OpenAI',Client)
    payload,_,_=sem.SemanticSufficiencyGate().prepare('TME2026P4','APQR é um paralelogramo.',(judgment('b.apqr'),))
    ds,meta=sem.request_sufficiency(payload)
    assert not ds and meta['raw_output']=='{"decisions":{}}' and meta['api_calls']==1
    assert calls[0]['store'] is False and calls[0]['model']=='gpt-4o-mini-2024-07-18'
