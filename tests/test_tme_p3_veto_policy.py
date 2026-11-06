"""Direct central authority tests, including bypass and stale-receipt attempts."""
from dataclasses import replace
import copy
import pytest
from test_tme_semantic_formal_p3 import run,claim,award
from test_tme_p3_discourse_state import resolve
from confia_lean_auditor.experimental.tme_semantic_formal_p3.veto_policy import VetoEligibilityPolicy,candidate,reconcile


def setup_policy(prefix='',status='DETERMINISTIC_FAILED',producer='atomic_guard'):
    span=prefix+'Ao repetir o mesmo compartimento, o quinto também libera branca.'
    text='b) '+span
    snap,views,_,_=resolve(text,[claim(text,'repeticao_branca',span,span=span)])
    result=dict(evidence_id=views[0].evidence_id,obligation_id='b.same_compartment',
        status=status,mathematical_refutation=status=='DETERMINISTIC_FAILED',guard_id='test-checked-receipt',
        guard_only=True,checker_receipt={'finite_model_event':[5,5]})
    policy=VetoEligibilityPolicy(snap)
    return policy,candidate(result,producer)


def test_I1_guard_never_awards_even_when_true():
    span='Ao repetir o mesmo compartimento, o sexto também libera branca.'
    r=run('b) '+span,[claim('b) '+span,'repeticao_branca',span,span=span)])
    assert r['score']==0 and not any(a['eligible'] for a in r['awards'])
    assert any(g['status']=='DETERMINISTIC_VERIFIED' for g in r['conflict_guard_results'])
    assert all(g['guard_only'] and not g['award_eligible'] for g in r['conflict_guard_results'])


@pytest.mark.parametrize('prefix',['Hipótese não adotada: ','Beatriz disse que '])
def test_I2_nonadopted_checked_false_has_no_authority(prefix):
    policy,c=setup_policy(prefix);d=policy.decide(c)
    assert d['discourse_states']==['NON_ADOPTED'] and not d['hard_veto_eligible']
    assert d['reconciliation_status']=='AUDIT_ONLY' and reconcile(policy,[d])==[]


def test_I7_active_checked_refutation_is_eligible_only_in_compatible_scope():
    policy,c=setup_policy();d=policy.decide(c)
    assert d['hard_veto_eligible'] and d['reconciliation_status']=='APPLIED'
    c['obligation_id']='a.bottom_white_count'
    assert not policy.decide(c)['hard_veto_eligible']


def test_I8_local_conflict_only_reaches_contracted_dependency():
    policy,c=setup_policy();d=policy.decide(c)
    assert d['target_obligation_ids']==['b.same_compartment','b.second_white_probability']
    r=run('a) inferiores_brancas: 2\nb) repeticao_branca: {5}\nfavoraveis_distintos: 2*5=10')
    assert r['score']==4 and award(r,'a.bottom_white_count')['eligible'] and award(r,'b.different_favorable')['eligible']


def test_I9_every_automatic_veto_has_current_source_checker_policy_receipt():
    policy,c=setup_policy();d=policy.decide(c)
    assert policy.authentic(d) and d['source_ranges'] and d['checker_ref'] and d['provenance']
    assert d['ledger_revision']==policy.snapshot.ledger_revision and d['invariant']
    r=run('a) inferiores_brancas: 2')
    for a in r['awards']:
        receipt=a['decision_receipt']
        assert receipt['source_sha256'] and receipt['ledger_revision']
        if not a['eligible']:assert receipt['absence_reason']=='no_current_sufficient_checker_witness'


@pytest.mark.parametrize('producer',['positive_checker','native_checker','atomic_guard','structural_guard','regular_guard','raw_bridge'])
def test_I12_producer_cannot_bypass_central_receipt(producer):
    policy,c=setup_policy(producer=producer)
    assert reconcile(policy,[dict(c,hard_veto_eligible=True,target_obligation_ids=['b.same_compartment'])])==[]
    d=policy.decide(c)
    assert reconcile(policy,[d]) and policy.authentic(d)


def test_I13_deduplication_and_reconciliation_idempotence():
    policy,c=setup_policy();a=policy.decide(c);b=policy.decide(copy.deepcopy(c))
    assert a['decision_id']==b['decision_id']
    assert reconcile(policy,[a,a,b])==reconcile(policy,[a])==reconcile(policy,[b,a])
    text='a) inferiores_brancas: 2'
    from test_tme_semantic_formal_p3 import typed_claims
    r=run(text,typed_claims(text)*2)
    assert r['score']==2 and len([a for a in r['awards'] if a['eligible']])==1


@pytest.mark.parametrize('source,expression',[
    ('A probabilidade da primeira branca é 2/6=1/2.','2/6'),
    ('Ao repetir o mesmo compartimento, somente o quinto e o sexto liberam branca.','{6}'),
])
def test_I15_source_payload_cannot_drop_false_side_or_member(source,expression):
    item='a' if 'primeira' in source else 'b';subject='primeira_branca' if item=='a' else 'repeticao_branca'
    text=item+') '+source;r=run(text,[claim(text,subject,expression,span=source)])
    assert r['score']==0 and not any(a['eligible'] for a in r['awards'])
    assert not r['obligation_mapping'][0]['accepted']


@pytest.mark.parametrize('producer',['positive_checker','native_checker','atomic_guard','regular_guard'])
def test_I16_negative_dependency_does_not_depend_on_producer(producer):
    policy,c=setup_policy(producer=producer);d=policy.decide(c)
    assert d['hard_veto_eligible'] and d['dependency_paths']==[['b.same_compartment','b.second_white_probability']]


@pytest.mark.parametrize('status',['FORMAL_UNPROVED','FORMAL_NOT_ATTEMPTED','FORMAL_ERROR','COMPOSITE_INCOMPLETE','DETERMINISTIC_ERROR','SEMANTIC_INSUFFICIENT'])
def test_I17_no_refutation_from_unproved_incomplete_or_error(status):
    policy,c=setup_policy(status=status)
    c['mathematical_contradiction']=True  # A producer boolean alone is insufficient.
    d=policy.decide(c)
    assert d['checker_status']==status and not d['hard_veto_eligible']


def test_I19_stale_or_mutated_receipt_cannot_reach_award():
    policy,c=setup_policy();d=policy.decide(c)
    tampered=copy.deepcopy(d);tampered['target_obligation_ids'].append('a.bottom_white_count')
    assert not policy.authentic(tampered) and reconcile(policy,[tampered])==[]
    newer,_=setup_policy(prefix='Minha resposta: ')
    assert not newer.authentic(d) and reconcile(newer,[d])==[]
    broken=replace(policy.snapshot,source_sha256='changed')
    with pytest.raises(ValueError):VetoEligibilityPolicy(broken)


def test_ambiguous_refutation_receipt_remains_review_only():
    policy,c=setup_policy(prefix='Talvez ');d=policy.decide(c)
    assert d['conflict_visible'] and not d['hard_veto_eligible'] and d['reconciliation_status']=='REVIEW_ONLY'


def test_authentic_veto_cannot_be_relabelled_to_another_award():
    from confia_lean_auditor.experimental.tme_semantic_formal_p3.engine import award as decide_award
    policy,c=setup_policy();d=policy.decide(c)
    observations,awards=decide_award('forged',(),[],[],[dict(obligation_id='a.bottom_white_count',policy_decisions=[d])],policy)
    assert next(a for a in awards if a['obligation_id']=='a.bottom_white_count')['award_decision']=='no_sufficient_checker_result'
