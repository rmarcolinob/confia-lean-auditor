"""Abandonment is source-supported or remains visible to veto-only checks."""
import json
from pathlib import Path
import pytest
from test_tme_semantic_formal_p3 import claim, run, provider, award
from test_tme_p3_conflict_preservation import situation, POSITIVE, FIFTH, PAYLOAD
from confia_lean_auditor.experimental.tme_semantic_formal_p3.engine import evaluate
from confia_lean_auditor.experimental.tme_semantic_formal_p3.abandonment import conflict_visibility
from confia_lean_auditor.experimental.tme_semantic_formal_p3.mapper import SourceDocument
from confia_lean_auditor.experimental.tme_semantic_formal_p3.evidence import bind_evidence

ROOT=Path(__file__).resolve().parents[1]


def marked(text, span, value=PAYLOAD, **changes):
    fields=dict(assertion_status='abandoned',abandoned=True)
    fields.update(changes)
    return claim(text,'repeticao_branca',value,span=span,**fields)


@pytest.mark.parametrize('flags',[
    {'abandoned':True,'assertion_status':'asserted'},
    {'abandoned':False,'assertion_status':'abandoned'},
    {'abandoned':True,'assertion_status':'abandoned'},
    {'abandoned':True,'assertion_status':'abandoned','scope':'exploration'},
    {'abandoned':True,'assertion_status':'abandoned','scope':'unknown'},
])
@pytest.mark.parametrize('value',[PAYLOAD,'{5}'])
def test_inferred_abandonment_preserves_atomic_or_regular_refutation(flags,value):
    text,claims=situation();claims[-1].update(flags,normalized_claim=value)
    r=run(text,claims)
    assert r['score']==2 and isinstance(r['score'],float)
    assert award(r,'a.bottom_white_count')['eligible']
    assert not award(r,'b.same_compartment')['eligible']
    decision=r['abandonment_decisions'][0]
    assert decision['effective_conflict_visibility'] and not decision['abandonment_textually_supported']
    assert not decision['positive_credit_eligible']
    guards=r['conflict_guard_results']+r['abandonment_guard_results']
    assert any(g['mathematical_refutation'] for g in guards)
    assert all(g['guard_only'] and not g['award_eligible'] and not g['sufficiency_decision']['sufficient'] for g in guards)
    assert any(v['status']=='CONTEXT_REJECTED' for v in r['verification_results'])


@pytest.mark.parametrize('reverse',[False,True])
def test_adopted_claims_remain_conflicting_in_either_order_without_retraction(reverse):
    spans=[FIFTH,POSITIVE] if reverse else [POSITIVE,FIFTH]
    text='a) Há duas bolas brancas embaixo.\nb) '+'\n'.join(spans)
    claims=[claim(text,'inferiores_brancas','2',span='Há duas bolas brancas embaixo.'),
        claim(text,'repeticao_branca','{6}',span=POSITIVE),marked(text,FIFTH)]
    r=run(text,claims)
    assert r['score']==2 and not award(r,'b.same_compartment')['eligible']


@pytest.mark.parametrize('marker',[
    'Isso está errado.',
    'Corrigindo minha afirmação anterior:',
    'Desconsidere a minha afirmação anterior.',
    'Não, o correto é:',
])
def test_immediate_explicit_retraction_does_not_block_corrected_solution(marker):
    text='a) Há duas bolas brancas embaixo.\nb) '+FIFTH+'\n'+marker+'\n'+POSITIVE
    claims=[claim(text,'inferiores_brancas','2',span='Há duas bolas brancas embaixo.'),
        marked(text,FIFTH),claim(text,'repeticao_branca','{6}',span=POSITIVE)]
    r=run(text,claims)
    assert r['score']==4 and not r['conflicts']
    d=r['abandonment_decisions'][0]
    assert d['abandonment_textually_supported'] and not d['effective_conflict_visibility']
    assert d['retraction_source_span']
    assert any(e['abandoned'] for e in r['extracted_evidence'])


def test_na_verdade_adjacent_bound_correction_is_supported():
    text,claims=situation(reverse=True)
    claims[1].update(assertion_status='abandoned',abandoned=True)
    r=run(text,claims)
    assert r['score']==4 and not r['conflicts']
    assert r['abandonment_decisions'][0]['abandonment_reason']=='adjacent_same_subject_correction'


@pytest.mark.parametrize('intervening',[
    'Na verdade, minha anotação seguinte trata de outra questão.',
    'Considerei as duas escolhas equiprováveis.',
    'Beatriz disse que isso está errado.',
])
def test_unrelated_intervening_or_third_party_text_cannot_revoke_claim(intervening):
    text='b) '+FIFTH+'\n'+intervening+'\nNa verdade, '+POSITIVE[0].lower()+POSITIVE[1:]
    good=text.splitlines()[-1]
    r=run(text,[marked(text,FIFTH),claim(text,'repeticao_branca','{6}',span=good)])
    assert r['score']==0 and r['abandonment_decisions'][0]['effective_conflict_visibility']


@pytest.mark.parametrize('prefix',[
    'Hipótese não adotada: ', 'Tentativa abandonada: ', 'Beatriz disse que ',
])
def test_real_nonadopted_context_does_not_create_veto(prefix):
    negative=prefix+FIFTH[0].lower()+FIFTH[1:]
    text='b) '+negative+'\n\n'+POSITIVE
    r=run(text,[marked(text,negative),claim(text,'repeticao_branca','{6}',span=POSITIVE)])
    assert r['score']==2 and not r['conflicts']
    assert not r['abandonment_decisions'][0]['effective_conflict_visibility']


@pytest.mark.parametrize('value',['{6}','O sexto também libera branca ao repetir o mesmo compartimento.'])
def test_recovered_true_claim_never_becomes_positive_credit(value):
    span='Ao repetir o mesmo compartimento, o sexto também libera branca.'
    text='b) '+span
    r=run(text,[marked(text,span,value)])
    assert r['score']==0 and not any(a['eligible'] for a in r['awards'])
    assert r['abandonment_decisions'][0]['effective_conflict_visibility']
    guards=r['conflict_guard_results']+r['abandonment_guard_results']
    assert guards and all(not g['award_eligible'] for g in guards)
    assert not r['conflicts']


def test_regular_probability_refutation_is_preserved_without_membership_pattern():
    text='b) segunda_branca: 12/36\nsegunda_branca: 11/36'
    claims=[claim(text,'segunda_branca','12/36',abandoned=True,assertion_status='abandoned'),
            claim(text,'segunda_branca','11/36')]
    r=run(text,claims)
    assert r['score']==0 and not r['conflict_guard_results']
    assert any(g['mathematical_refutation'] for g in r['abandonment_guard_results'])
    assert not award(r,'b.second_white_probability')['eligible']


def test_source_binding_tampering_cannot_recover_abandoned_evidence():
    text,claims=situation();claims[-1].update(abandoned=True,assertion_status='abandoned')
    units=bind_evidence(json.dumps({'evidence':claims}),text,'test')
    units=[e.model_copy(update={'source_span':'invented'}) if e.abandoned else e for e in units]
    _,decisions=conflict_visibility(SourceDocument.parse(text),units)
    assert not decisions[0]['effective_conflict_visibility']
    assert decisions[0]['abandonment_reason']=='invalid_source_binding'


def test_current_unchanged_by_safety_views():
    text,claims=situation();claims[-1].update(abandoned=True,assertion_status='abandoned')
    before=evaluate('unchanged','TME2026P3',text,mode='tme_current',use_lean=False)
    run(text,claims)
    after=evaluate('unchanged','TME2026P3',text,mode='tme_current',use_lean=False)
    for key in ['score','current_bridge','current_assessment','awards','credits','conflicts']:
        assert before[key]==after[key]
    assert 'abandonment_decisions' not in after


@pytest.mark.parametrize('cid,expected',[('p3_rob_e02',4),('p3_rob_e04',2)])
def test_recorded_e02_e04_without_api(cid,expected,tmp_path):
    # E02=4 is the clarified retraction policy, not a rewrite of observed labels.
    sources=json.loads((ROOT/'tests/fixtures/tme_semantic_formal_p3/semantic_robustness_01/sources.json').read_text())
    text=next(s['solution_text'] for s in sources if s['case_id']==cid)
    r=evaluate('controlled-'+cid,'TME2026P3',text,extraction_provider=provider(RECORDED[cid]),use_lean=False)
    (tmp_path/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    assert r['score']==expected and not r['fallback'] and r['extractor']['api_calls']==0
    assert award(r,'a.bottom_white_count')['eligible']
    if cid.endswith('e02'):
        assert r['abandonment_decisions'][0]['abandonment_textually_supported']
        assert not r['conflicts'] and award(r,'b.same_compartment')['eligible']
    else:
        assert r['conflict_guard_results'][0]['mathematical_refutation']
        assert not award(r,'b.same_compartment')['eligible']


# Exact source-bound extraction responses saved before this fix, not new calls.
RECORDED = {'p3_rob_e02': [{'source_evidence_ids': ['E002'], 'source_span': 'Há duas bolas brancas embaixo.', 'item_id': 'a', 'asserted_content': 'Há duas bolas brancas embaixo.', 'normalized_claim': '2', 'subject': 'inferiores_brancas', 'claim_type': 'math', 'assertion_status': 'asserted', 'polarity': 'positive', 'scope': 'main_argument', 'hypothetical': False, 'abandoned': False, 'attributed_to_student': True, 'obligation_candidates': ['a.bottom_white_count'], 'route_candidate': 'DETERMINISTIC', 'confidence': 1.0}, {'source_evidence_ids': ['E004'], 'source_span': 'Ao repetir o mesmo compartimento, o quinto também libera branca.', 'item_id': 'b', 'asserted_content': 'Ao repetir o mesmo compartimento, o quinto também libera branca.', 'normalized_claim': 'Ao repetir o mesmo compartimento, o 5 também libera branca.', 'subject': 'repeticao_branca', 'claim_type': 'integer_set', 'assertion_status': 'abandoned', 'polarity': 'positive', 'scope': 'main_argument', 'hypothetical': False, 'abandoned': True, 'attributed_to_student': True, 'obligation_candidates': ['b.same_compartment'], 'route_candidate': 'DETERMINISTIC', 'confidence': 0.97}, {'source_evidence_ids': ['E005'], 'source_span': 'Na verdade, ao repetir o mesmo compartimento, somente o sexto libera branca.', 'item_id': 'b', 'asserted_content': 'Na verdade, ao repetir o mesmo compartimento, somente o sexto libera branca.', 'normalized_claim': '{6}', 'subject': 'repeticao_branca', 'claim_type': 'integer_set', 'assertion_status': 'asserted', 'polarity': 'positive', 'scope': 'final_conclusion', 'hypothetical': False, 'abandoned': False, 'attributed_to_student': True, 'obligation_candidates': ['b.same_compartment'], 'route_candidate': 'DETERMINISTIC', 'confidence': 1.0}], 'p3_rob_e04': [{'source_evidence_ids': ['E002'], 'source_span': 'Há duas bolas brancas embaixo.', 'item_id': 'a', 'asserted_content': 'Há duas bolas brancas embaixo.', 'normalized_claim': '2', 'subject': 'inferiores_brancas', 'claim_type': 'math', 'assertion_status': 'asserted', 'polarity': 'positive', 'scope': 'main_argument', 'hypothetical': False, 'abandoned': False, 'attributed_to_student': True, 'obligation_candidates': ['a.bottom_white_count'], 'route_candidate': 'DETERMINISTIC', 'confidence': 1.0}, {'source_evidence_ids': ['E004'], 'source_span': 'Ao repetir o mesmo compartimento, somente o sexto libera branca.', 'item_id': 'b', 'asserted_content': 'Ao repetir o mesmo compartimento, somente o sexto libera branca.', 'normalized_claim': '{6}', 'subject': 'repeticao_branca', 'claim_type': 'integer_set', 'assertion_status': 'asserted', 'polarity': 'positive', 'scope': 'main_argument', 'hypothetical': False, 'abandoned': False, 'attributed_to_student': True, 'obligation_candidates': ['b.same_compartment'], 'route_candidate': 'DETERMINISTIC', 'confidence': 1.0}, {'source_evidence_ids': ['E004', 'E005'], 'source_span': 'Ao repetir o mesmo compartimento, somente o sexto libera branca.\nO quinto também.', 'item_id': 'b', 'asserted_content': 'O quinto também.', 'normalized_claim': '{5, 6}', 'subject': 'repeticao_branca', 'claim_type': 'integer_set', 'assertion_status': 'asserted', 'polarity': 'positive', 'scope': 'main_argument', 'hypothetical': False, 'abandoned': False, 'attributed_to_student': True, 'obligation_candidates': ['b.same_compartment'], 'route_candidate': 'DETERMINISTIC', 'confidence': 0.93}]}
