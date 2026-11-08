"""Multi-layer contract tests: source semantics and authority, never live API."""
import copy
import json
from dataclasses import replace
from pathlib import Path
import pytest
from test_tme_semantic_formal_p3 import run, claim, typed_claims, award, provider
from test_tme_p3_discourse_state import resolve
from confia_lean_auditor.student_claims.semantic import sha
from confia_lean_auditor.experimental.tme_semantic_formal_p3.discourse import VERSION,DiscourseSnapshot
from confia_lean_auditor.experimental.tme_semantic_formal_p3.automation import AutomationEligibilityPolicy
from confia_lean_auditor.experimental.tme_semantic_formal_p3.semantic_contracts import annotate_result,FIDELITIES,BINDINGS
from confia_lean_auditor.experimental.tme_semantic_formal_p3.veto_policy import VetoEligibilityPolicy,candidate
from confia_lean_auditor.experimental.tme_semantic_formal_p3.engine import evaluate

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(autouse=True)
def no_api(monkeypatch):
    import openai
    def forbidden(*a,**k):raise AssertionError('live API forbidden')
    monkeypatch.setattr(openai,'OpenAI',forbidden)


def snapshot_with(state='ACTIVE',fidelity='EXACT',binding='EXACT_BINDING'):
    snap,views,_,_=resolve('a) inferiores_brancas: 2')
    d=snap.decisions[0];r=d.representation_receipt;bs=d.binding_receipts
    r['representation_fidelity']=fidelity
    for b in bs:b['binding_status']=binding;b['representation_fidelity']=fidelity
    d=replace(d,state=state,representation_json=json.dumps(r),bindings_json=json.dumps(bs))
    ds=(d,)
    snap=DiscourseSnapshot(snap.source_sha256,sha([VERSION,snap.source_sha256,[x.as_dict() for x in ds]]),ds)
    return snap,d


def result(snap,d,status='DETERMINISTIC_VERIFIED'):
    return annotate_result(snap,dict(obligation_id='a.bottom_white_count',evidence_ids=[d.evidence_id],
        primary_evidence_ids=[d.evidence_id],verification_id='controlled-math-receipt',status=status,
        route='DETERMINISTIC',original_fact={'controlled_checker':True},
        mathematical_refutation=status=='DETERMINISTIC_FAILED',
        sufficiency_decision=dict(sufficient=status=='DETERMINISTIC_VERIFIED')))

@pytest.mark.parametrize('state',['ACTIVE','SUPERSEDED','NON_ADOPTED','AMBIGUOUS'])
@pytest.mark.parametrize('fidelity',FIDELITIES)
@pytest.mark.parametrize('binding',BINDINGS)
def test_F1_F6_admission_cross_product_cannot_be_elevated_by_math(state,fidelity,binding):
    snap,d=snapshot_with(state,fidelity,binding);before=copy.deepcopy(d.as_dict())
    yes=result(snap,d);no=result(snap,d,'DETERMINISTIC_FAILED')
    p=VetoEligibilityPolicy(snap)
    a=p.automation.decide(yes)
    v=p.decide(candidate(no,'controlled_checker'))
    allowed=state=='ACTIVE' and fidelity in FIDELITIES[:2] and binding in BINDINGS[:2]
    assert (a['automation_eligibility']=='AUTO_AWARD')==allowed
    assert v['hard_veto_eligible']==allowed
    assert (v['automation_decision']['automation_eligibility']=='AUTO_VETO')==allowed
    assert d.as_dict()==before


def test_F7_confidence_is_not_authority():
    text='a) inferiores_brancas: 2';cs=typed_claims(text)
    a=run(text,[dict(c,confidence=0) for c in cs]);b=run(text,[dict(c,confidence=1) for c in cs])
    assert a['score']==b['score']==2
    assert [d['automation_eligibility'] for d in a['automation_decisions']]==[d['automation_eligibility'] for d in b['automation_decisions']]


def test_F8_F9_F19_F23_review_has_no_negative_edges_or_global_gate():
    span='Talvez a probabilidade da segunda branca seja 12/36.'
    text='a) inferiores_brancas: 2\nb) segunda_branca: 11/36\n'+span
    r=run(text,typed_claims(text)+[claim(text,'segunda_branca','12/36',span=span)])
    assert r['score']==4 and not r['conflicts']
    reviews=[d for d in r['automation_decisions'] if d['automation_eligibility']=='REVIEW_ONLY']
    assert reviews and all(not d['authority_for_hard_veto'] and not d['authority_for_positive_credit'] for d in reviews)
    assert award(r,'b.second_white_probability')['eligible']


def test_F10_F18_provenance_and_tampered_input():
    snap,d=snapshot_with();r=result(snap,d);p=AutomationEligibilityPolicy(snap)
    a=p.decide(r)
    assert a['automation_eligibility']=='AUTO_AWARD'
    assert a['provenance'][0]['segment']['assertion_range']
    assert a['provenance'][0]['representation']['source_span']=='inferiores_brancas: 2'
    r['checker_input_receipt']['input_digest']='tampered'
    assert p.decide(r)['automation_eligibility']=='REVIEW_ONLY'


def test_F11_active_unrepresentable_is_not_uncertain_adoption():
    span='A probabilidade da segunda branca é a razão que calculei.'
    text='b) '+span
    r=run(text,[claim(text,'segunda_branca','minha razão',span=span,claim_type='qualitative')])
    d=r['discourse_decisions'][0]
    assert d['resolved_discourse_state']=='ACTIVE'
    assert d['representation_receipt']['representation_fidelity']=='UNSUPPORTED'
    assert r['score']==0 and not r['conflicts']

@pytest.mark.parametrize('index',[1,2,3,4,5,6])
def test_F12_F14_exact_membership_is_counterevidence_not_complete_set(index):
    span=f'Afirmo que repetir o compartimento {index} dá branca.';text='b) '+span
    c=claim(text,'repeticao_branca',span,span=span,claim_type='qualitative')
    r=run(text,[dict(c,subject='unmapped')])
    assert r['score']==0
    atom=r['representation_receipts'][0]
    assert atom['representation_fidelity']=='EXACT' and atom['proposition']['kind']=='member'
    assert bool(r['conflicts'])==(index!=6)
    assert all(not a['eligible'] for a in r['awards'])

@pytest.mark.parametrize('payload',['2/6','1/3'])
def test_F13_F22_no_strengthening_or_truncation_from_correct_number(payload):
    span='A probabilidade da primeira branca é 2/6=1/2.';text='a) '+span
    r=run(text,[claim(text,'primeira_branca',payload,span=span)])
    assert r['score']==0 and not r['conflicts']
    assert all(d['automation_eligibility']=='REVIEW_ONLY' for d in r['automation_decisions'])


def test_F15_sentence_boundary_after_fraction_and_decimal_not_split():
    from confia_lean_auditor.experimental.tme_semantic_formal_p3.segmentation import BOUNDARY
    assert [m.start() for m in BOUNDARY.finditer('0.5. 1/2. Depois')]==[3,8]
    text='a) primeira_branca: 1/2. Corrigindo: primeira_branca: 1/3'
    # Explicit controlled raw assertion spans within one evidence envelope.
    from confia_lean_auditor.student_claims.evidence_units import evidence_units
    u=evidence_units(text)[-1]
    base=dict(source_evidence_ids=[u.evidence_id],source_span=u.exact_text,item_id='a',subject='primeira_branca',claim_type='math',
        assertion_status='asserted',polarity='positive',scope='main_argument',hypothetical=False,abandoned=False,
        attributed_to_student=True,obligation_candidates=['a.first_white_probability'],route_candidate='DETERMINISTIC',confidence=1)
    cs=[dict(base,asserted_content='primeira_branca: 1/2',normalized_claim='1/2'),dict(base,asserted_content='primeira_branca: 1/3',normalized_claim='1/3')]
    r=run(text,cs)
    assert r['score']==2
    assert {d['resolved_discourse_state'] for d in r['discourse_decisions']}=={'ACTIVE','SUPERSEDED'}
    assert r['discourse_segments'][0]['assertion_range']!=r['discourse_segments'][-1]['assertion_range']


def test_F16_correction_false_final_does_not_resurrect_true_prior():
    r=run('b) segunda_branca: 11/36\nRetifico:\nsegunda_branca: 12/36')
    assert r['score']==0 and r['conflicts']
    assert any(d['resolved_discourse_state']=='SUPERSEDED' for d in r['discourse_decisions'])


def test_F17_F20_F21_F24_structural_scope_receipts_and_reconciliation():
    from confia_lean_auditor.experimental.tme_semantic_formal_p3.veto_policy import reconcile
    snap,d=snapshot_with();p=VetoEligibilityPolicy(snap);r=result(snap,d,'DETERMINISTIC_FAILED')
    v=p.decide(candidate(r,'controlled_checker'))
    assert reconcile(p,[v,v])==reconcile(p,[v])
    assert v['source_ranges'] and v['dependency_paths']==[]
    wrong=copy.deepcopy(v);wrong['target_obligation_ids']=['c.continue_compartments']
    assert reconcile(p,[wrong])==[]
    # Reconciliation is receipt-only: no SourceDocument/text argument exists.
    assert reconcile(p,[v])[0]['obligation_id']=='a.bottom_white_count'

@pytest.mark.parametrize('cid,expected,old_state',[
    ('a05',0,'ACTIVE'),('b03',2,'SUPERSEDED'),('b04',1,'SUPERSEDED'),('b05',2,'SUPERSEDED'),('b08',2,'SUPERSEDED'),('e01',4,'NON_ADOPTED')])
def test_safety03_observed_causal_regressions(cid,expected,old_state,tmp_path):
    path=ROOT/f'artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_{cid}.json'
    old=json.loads(path.read_text())
    def recorded(*a):return old['extractor']['raw_output'],dict(status='completed',api_calls=0,model='recorded')
    r=evaluate('observed-'+cid,'TME2026P3',old['source_text'],extraction_provider=recorded,use_lean=False)
    (tmp_path/(cid+'.json')).write_text(json.dumps(r,ensure_ascii=False))
    assert r['score']==expected and not r['fallback'] and not r['technical_uncertainty']
    assert any(d['resolved_discourse_state']==old_state for d in r['discourse_decisions'])
    if cid=='a05':
        assert all(d['representation_fidelity']=='EXACT' for d in r['representation_receipts'])
        assert any(d['automation_eligibility']=='AUTO_VETO' for d in r['automation_decisions'])
        assert any(g['atomic_claim']['compartment']==3 for g in r['conflict_guard_results'])
    else:assert not r['conflicts']


def test_safety03_B02_recorded_real_lean(tmp_path):
    old=json.loads((ROOT/'artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b02.json').read_text())
    def recorded(*a):return old['extractor']['raw_output'],dict(status='completed',api_calls=0,model='recorded')
    r=evaluate('multilayer-b02-real','TME2026P3',old['source_text'],extraction_provider=recorded,use_lean=True)
    (tmp_path/'real_b02.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    assert r['score']==2 and not r['conflicts'] and not r['technical_uncertainty']
    assert any(v['formal_status']=='FORMAL_VERIFIED' and v['checker_result']['compiled'] for v in r['verification_results'])


def test_negative_candidate_cannot_disagree_with_bound_checker_result():
    snap,d=snapshot_with();r=result(snap,d);p=VetoEligibilityPolicy(snap)
    c=candidate(r,'controlled_checker');c['checker_status']='DETERMINISTIC_FAILED';c['mathematical_contradiction']=True
    v=p.decide(c)
    assert not v['hard_veto_eligible'] and p.applied([v])==[]


def test_negated_numeric_assertion_is_not_positive_math_payload():
    span='Não há duas bolas brancas inferiores.';text='a) '+span
    r=run(text,[claim(text,'inferiores_brancas','2',span=span)])
    assert r['score']==0 and not r['conflicts']
    assert any(d['representation_fidelity']=='UNSUPPORTED' for d in r['representation_receipts'])


def test_claim_projection_rejects_post_admission_mutation():
    from confia_lean_auditor.experimental.tme_semantic_formal_p3.verification import ClaimProjection
    from confia_lean_auditor.experimental.tme_semantic_formal_p3.mapper import SourceDocument,ObligationMapper
    text='a) inferiores_brancas: 2';snap,views,_,_=resolve(text)
    document=SourceDocument.parse(text);mapping=ObligationMapper().map(document,views)
    changed=[views[0].model_copy(update={'normalized_claim':'3'})]
    with pytest.raises(ValueError,match='representation_changed_before_checker'):
        ClaimProjection(document,changed,mapping)


def test_inclusion_without_exclusivity_cannot_be_strengthened_to_exact_set():
    span='Ao repetir a escolha, o sexto libera branca.';text='b) '+span
    r=run(text,[claim(text,'repeticao_branca','{6}',span=span)])
    assert r['score']==0 and not r['conflicts']
    assert not award(r,'b.same_compartment')['eligible']


@pytest.mark.parametrize('cid',['p3_safe_s1_04','p3_safe_s1_06'])
def test_observed_withdrawal_preserves_previously_valid_credit(cid):
    path=ROOT/'artifacts/evaluations/tme_p3_semantic_safety_02/new32/tme_semantic_formal'/f'{cid}.json'
    old=json.loads(path.read_text())
    def recorded(*a):return old['extractor']['raw_output'],dict(status='completed',api_calls=0,model='recorded')
    r=evaluate('observed-'+cid,'TME2026P3',old['source_text'],extraction_provider=recorded,use_lean=False)
    assert r['score']==2 and not r['conflicts']
    assert any(d['resolved_discourse_state'] in {'NON_ADOPTED','SUPERSEDED'} for d in r['discourse_decisions'])


@pytest.mark.parametrize('subject,span,item,payload',[
    ('primeira_branca','A probabilidade da segunda branca é 1/3.','a','1/3'),
    ('segunda_branca','A probabilidade da primeira branca é 2/6.','b','2/6'),
])
def test_probability_binding_cannot_take_event_index_from_numerator(subject,span,item,payload):
    text=item+') '+span
    r=run(text,[claim(text,subject,payload,span=span)])
    assert r['score']==0 and not r['conflicts']
    assert not r['obligation_mapping'][0]['accepted']
    assert all(d['automation_eligibility']=='REVIEW_ONLY' for d in r['automation_decisions'])


def test_quantity_binding_does_not_transport_upper_count_to_lower():
    span='Contei 2 bolas brancas superiores e 4 bolas brancas inferiores.';text='a) '+span
    r=run(text,[claim(text,'inferiores_brancas','2',span=span)])
    assert r['score']==0 and not r['conflicts']
    assert not r['obligation_mapping'][0]['accepted']


def test_membership_adapter_cannot_silently_select_one_of_multiple_indices():
    span='Ao repetir, o quinto também libera branca e o sexto também libera branca.';text='b) '+span
    r=run(text,[claim(text,'repeticao_branca',span,span=span,claim_type='qualitative')])
    assert r['score']==0 and not r['conflicts']
    assert not r['conflict_guard_results']


def test_indefinite_article_does_not_create_compartment_one():
    span='Ao repetir, um compartimento também libera branca.';text='b) '+span
    r=run(text,[claim(text,'repeticao_branca',span,span=span,claim_type='qualitative')])
    assert not r['conflict_guard_results'] and not r['conflicts'] and r['score']==0


def test_negated_retraction_marker_cannot_supersede_prior_claim():
    text='b) segunda_branca: 11/36\nNão retiro minha afirmação anterior.\nsegunda_branca: 12/36'
    r=run(text)
    assert all(d['resolved_discourse_state']=='ACTIVE' for d in r['discourse_decisions'])
    assert r['score']==0 and r['conflicts']
