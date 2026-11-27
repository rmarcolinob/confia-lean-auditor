import json
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from confia_lean_auditor.student_claims import hybrid_semantic as sem
from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.tme import hybrid_grader as hybrid
from confia_lean_auditor.tme.obligation_experiment import primary_audit
from confia_lean_auditor.rubric.pauta.models import PautaEvidence, ObligationEvidence, PautaConfig
from confia_lean_auditor.rubric.pauta.engine import PautaEngine


def judgment(oid, ids=('E001',), **changes):
    return sem.SemanticObligationJudgment(**dict(dict(obligation_id=oid,semantic_judgment='satisfied',
        evidence_ids=list(ids),method_path='equivalent_alternative',assertion_mode='asserted',confidence='high',
        concise_rationale='Conteúdo matemático expresso pelo estudante.',extracted_mathematical_statements=[]),**changes))


def provider(problem,text,positives):
    return (tuple(positives.get(o['obligation_id']) or judgment(o['obligation_id'],(),semantic_judgment='not_satisfied')
                  for o in sem.catalog(problem)),dict(status='completed',api_calls=0,model='fixture'))


def run(text, positives, problem='TME2026P4', items=None, lean=False):
    return hybrid.run_hybrid_shadow(problem,items or {},text,solution_id='fixture',use_lean=lean,
        provider=lambda p,t:provider(p,t,positives))


@pytest.mark.parametrize('p',[f'TME2026P{i}' for i in range(1,6)])
def test_payload_complete_global_reference_and_no_scoring_data(p):
    w=sem.wire_payload(p,'(a) primeiro\n(b) segundo')
    assert w['full_student_solution']=='(a) primeiro\n(b) segundo'
    assert w['statement'] and w['official_reference']['solution'] and w['alternative_methods']
    def visit(v):
        if isinstance(v,dict):
            assert not set(v)&{'max_points','points','score','synthetic_expected_score','baseline_score','source_start','source_end'}
            for x in v.values():visit(x)
        elif isinstance(v,list):
            for x in v:visit(x)
    visit(w)
    schema=sem.response_schema(p,w['full_student_solution'])
    def closed(v):
        if isinstance(v,dict):
            if v.get('type')=='object':
                assert v['additionalProperties'] is False
                assert set(v['required'])==set(v['properties'])
            for x in v.values():closed(x)
        elif isinstance(v,list):
            for x in v:closed(x)
    closed(schema)


@pytest.mark.parametrize('field',['points','score','supported','refuted','award','deny','source_start','source_end','source_text'])
def test_model_never_supplies_grades_status_or_spans(field):
    j=judgment('b.apqr').model_dump();j[field]=0
    with pytest.raises(ValidationError):sem.SemanticObligationJudgment.model_validate(j)


def test_missing_foreign_duplicate_ids_and_obligations_fail_closed():
    p='TME2026P4';text='APQR é um paralelogramo.'
    js,_=provider(p,text,{'b.apqr':judgment('b.apqr')})
    for mutated in (js[:-1],js+js[:1],tuple(j.model_copy(update={'evidence_ids':['E999']}) if j.obligation_id=='b.apqr' else j for j in js)):
        with pytest.raises(ValueError):sem.validate_response(json.dumps({'judgments':[j.model_dump() for j in mutated]}),p,text)


def test_verbal_support_without_factresult_and_default_engine_isolation():
    text='Retirando três de um número pelo menos cinco e usando o restante, a soma fica igual e o produto aumenta.'
    r=run(text,{'b.increase':judgment('b.increase')},'TME2026P5')
    e=next(e for e in r.reconciled_evidence.obligations if e.obligation_id=='b.increase')
    assert e.status=='supported' and e.origin=='semantic' and e.verification_source=='semantic'
    assert not r.audit_bridge.auditor.facts
    assert r.baseline_assessment.score==0 and r.potential_assessment.score==2 and r.semantic_only_points==2
    assert PautaEngine().evaluate(sem.config_for('TME2026P5'),r.reconciled_evidence).score==0
    with pytest.raises(ValueError):hybrid.activate_hybrid(r)
    assert hybrid.activate_hybrid(r,gate_passed=True)==r.potential_assessment


def tiny_config():
    return PautaConfig.model_validate(dict(problem_id='test',title='test',max_score=1,unresolved_policy='withhold',
      obligations=[dict(id='x',description='x')],items=[dict(id='i',max_points=1,scoring_strategy='all_of',obligation_ids=['x'])]))


@pytest.mark.parametrize('confidence,review',[('high',False),('medium',True),('low',True)])
def test_review_is_conditional_not_automatic(confidence,review):
    e=ObligationEvidence(obligation_id='x',status='supported',origin='semantic',verification_source='semantic',
      evidence_refs=('E001',),grounding_status='grounded',attributable_to_student=True,
      metadata=dict(reconciliation_policy=hybrid.POLICY.version,evidence_tier='SEMANTIC_SUPPORTED',context_valid=True,confidence=confidence,conflict=False))
    ev=PautaEvidence(problem_id='test',solution_id='s',obligations=(e,))
    assert PautaEngine().evaluate(tiny_config(),ev,evidence_policy=hybrid.POLICY).needs_review is review
    assert PautaEngine().evaluate(tiny_config(),ev).score==0


@pytest.mark.parametrize('prefix,suffix',[
 ('Não é verdade que ',''),('Suponha que ',''),('Tentei: ',' Mas está errado.'),
 ('João disse que ',''),('A solução de João diz ',''),('Talvez ',''),('Na página 12, ',''),
 ('João disse:\n',''),('“','”'),('','\n\nIsso estava errado.'),
 ('Suponha o seguinte:\n',''),('','\nDepois concluí que não era isso.')])
def test_previous_context_controls_with_hostile_positive_judge(prefix,suffix):
    text=prefix+'APQR é um paralelogramo. Seu perímetro APQR é 2*((6-x)+x)=12.'+suffix
    u=next(u for u in evidence_units(text) if 'APQR' in u.exact_text)
    r=run(text,{'b.perimeter_apqr':judgment('b.perimeter_apqr',(u.evidence_id,))})
    assert r.potential_assessment.score==0


@pytest.mark.parametrize('mode',['hypothetical','rejected','negated','quoted','mixed'])
def test_assertion_modes_do_not_grant_semantic_credit(mode):
    r=run('APQR é um paralelogramo.',{'b.apqr':judgment('b.apqr',assertion_mode=mode)})
    assert next(t for t in r.reconciliation if t['obligation_id']=='b.apqr')['decision']=='indeterminate'


@pytest.mark.parametrize('text,oid,p',[
 ('É um paralelogramo.','b.perimeter_apqr','TME2026P4'),
 ('Isso é máximo porque sim.','a.structural_max','TME2026P5'),
 ('54','a.structural_max','TME2026P5'),
 ('Tentei 11/36, mas descartei.','b.second_white_probability','TME2026P3'),
 ('O perímetro APQR é 12.\nO perímetro APQR é 14.','b.perimeter_apqr','TME2026P4'),
 ('Lista: (3,3,3,2).\nLista: (4,4,3).','a.candidate','TME2026P5'),
 ('O produto é 54.\nO produto é 55.','a.product','TME2026P5'),
])
def test_new_false_credit_controls(text,oid,p):
    r=run(text,{oid:judgment(oid)},p)
    assert r.potential_assessment.score==0
    assert next(t for t in r.reconciliation if t['obligation_id']==oid)['decision']!='supported'


def test_wrong_reasoning_correct_final_is_refuted_by_real_lean():
    text='APQR é um paralelogramo.\nSeu perímetro APQR é 2*((6-x)+x)+1=12.'
    j=judgment('b.perimeter_apqr',('E002',),extracted_mathematical_statements=[dict(subject='perimeter_apqr',
        expression='2*((6-x)+x)+1=12',representation_kind='math',evidence_ids=['E002'])])
    r=run(text,{'b.perimeter_apqr':j},items={'b':text},lean=True)
    t=next(t for t in r.reconciliation if t['obligation_id']=='b.perimeter_apqr')
    assert t['decision']=='refuted' and t['evidence_tier']=='CONFLICT' and t['needs_review']
    assert t['selective_audit']['same_selected_claim']
    assert r.potential_assessment.score==0


def test_real_formal_verified_is_preserved_and_not_semantic():
    text='APQR é um paralelogramo.\nSeu perímetro APQR é 2*((6-x)+x)=12.'
    j=judgment('b.perimeter_apqr',('E002',),extracted_mathematical_statements=[dict(subject='perimeter_apqr',
        expression='2*((6-x)+x)=12',representation_kind='math',evidence_ids=['E002'])])
    r=run(text,{'b.perimeter_apqr':j},items={'b':text},lean=True)
    t=next(t for t in r.reconciliation if t['obligation_id']=='b.perimeter_apqr')
    assert t['decision']=='supported' and t['evidence_tier']=='FORMAL_VERIFIED'
    assert t['reconciled_evidence']['verification_source']=='student_lean'


def test_inline_item_unit_has_multiple_hints_no_rigid_mapping_needed():
    text='(a) PQ=x. (b) APQR é um paralelogramo e seu perímetro é o dobro de x+(6-x), logo 12.'
    u=next(u for u in evidence_units(text) if 'paralelogramo' in u.exact_text)
    r=run(text,{'b.perimeter_apqr':judgment('b.perimeter_apqr',(u.evidence_id,))})
    t=next(t for t in r.reconciliation if t['obligation_id']=='b.perimeter_apqr')
    assert t['decision']=='supported' and t['context']['cross_item']


def test_cross_item_requires_declared_dependency_and_target_evidence():
    for text in ['(a) APQR é um paralelogramo.','(c) APQR é um paralelogramo.\n(b) fim']:
        u=next(u for u in evidence_units(text) if 'APQR' in u.exact_text)
        r=run(text,{'b.apqr':judgment('b.apqr',(u.evidence_id,))})
        assert next(t for t in r.reconciliation if t['obligation_id']=='b.apqr')['decision']!='supported'


def test_carry_forward_cannot_be_fabricated_by_semantic_judge():
    text='Adoto 673 parcelas de três; as listas têm 675 e 674 termos.'
    r=run(text,{o:judgment(o) for o in ['d.cf_adoption','d.cf_dependency','d.cf_coherence']},'TME2026P5')
    assert all(t['decision']!='supported' for t in r.reconciliation if '.cf_' in t['obligation_id'])
    assert r.potential_assessment.score==0


@pytest.mark.parametrize('status,tier',[('supported','DETERMINISTIC_VERIFIED'),('refuted','CONFLICT'),('technical_error','TECHNICAL_ERROR')])
def test_audit_precedence_and_technical_failure_never_becomes_refutation(status,tier):
    text='APQR é um paralelogramo.'
    bridge,_=primary_audit('TME2026P4',{},solution_id='s',use_lean=False)
    ev=ObligationEvidence(obligation_id='b.apqr',status=status,origin='deterministic',verification_source='deterministic',
        evidence_refs=('real:checker',),attributable_to_student=True,grounding_status='grounded')
    b=bridge.model_copy(update={'evidence':bridge.evidence.model_copy(update={'obligations':(ev,)})})
    evidence,trace=hybrid.EvidenceReconciler().reconcile('TME2026P4',text,(judgment('b.apqr'),),b,b)
    t=next(t for t in trace if t['obligation_id']=='b.apqr')
    assert t['decision']==status and t['evidence_tier']==tier


def test_unavailable_provider_is_technical_not_zero_or_negative():
    r=hybrid.run_hybrid_shadow('TME2026P4',{},'texto',solution_id='s',use_lean=False,
       provider=lambda p,t:((),dict(status='unavailable')))
    assert r.potential_assessment.score is None and r.potential_assessment.needs_review
    assert all(t['evidence_tier']=='TECHNICAL_ERROR' for t in r.reconciliation)


def test_provider_store_false_model_snapshot_raw_error_and_no_retry(monkeypatch):
    import openai
    calls=[]
    class Client:
        def __init__(self,**kw):assert kw['max_retries']==0;self.responses=self
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def create(self,**kw):
            calls.append(kw)
            return SimpleNamespace(status='completed',output_text='{}',model=kw['model'],id='fixture',usage=None)
    monkeypatch.setattr(openai,'OpenAI',Client)
    js,m=sem.request_judgments('TME2026P4','texto')
    assert not js and m['raw_output']=='{}' and m['api_calls']==1
    assert calls[0]['store'] is False and calls[0]['model']=='gpt-4o-mini-2024-07-18'


def test_existing_carry_forward_binding_and_prior_error_survive_global_judge():
    from pathlib import Path
    cases=json.loads((Path(__file__).parent/'fixtures/tme2_p5_digital/cases.json').read_text())
    items=next(c['solution'] for c in cases if c['id']=='d_cf_valid')
    text='\n'.join(f'({k}) {v}' for k,v in items.items())
    r=run(text,{},'TME2026P5',items=items)
    assert r.potential_assessment.items[3].carry_forward_applied
    assert r.potential_assessment.items[3].points_awarded==1
    before={e.obligation_id:e for e in r.primary_bridge.evidence.obligations}
    after={e.obligation_id:e for e in r.reconciled_evidence.obligations}
    assert before['c.threes_count'].status==after['c.threes_count'].status=='refuted'
    assert all(before[o]==after[o] for o in ['d.cf_adoption','d.cf_dependency','d.cf_coherence'])


def test_engine_policy_cannot_rewrite_math_rules_max_of_or_caps():
    cfg=PautaConfig.model_validate(dict(problem_id='test',title='test',max_score=1,unresolved_policy='withhold',
        obligations=[dict(id='x',description='x'),dict(id='y',description='y')],
        items=[dict(id='i',max_points=1,scoring_strategy='max_of',children=[
            dict(id='method1',max_points=1,scoring_strategy='all_of',obligation_ids=['x']),
            dict(id='method2',max_points=1,scoring_strategy='all_of',obligation_ids=['y'])])]))
    evidences=tuple(ObligationEvidence(obligation_id=o,status='supported',origin='semantic',verification_source='semantic',
        evidence_refs=(o,),grounding_status='grounded',attributable_to_student=True,
        metadata=dict(reconciliation_policy=hybrid.POLICY.version,evidence_tier='SEMANTIC_SUPPORTED',context_valid=True,confidence='high',conflict=False)) for o in ['x','y'])
    result=PautaEngine().evaluate(cfg,PautaEvidence(problem_id='test',solution_id='s',obligations=evidences),evidence_policy=hybrid.POLICY)
    assert result.score==1 and not result.needs_review
