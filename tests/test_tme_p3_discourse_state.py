"""Direct architecture invariants. No model calls or benchmark label changes."""
import json
from dataclasses import replace
import pytest
from test_tme_semantic_formal_p3 import claim,typed_claims,run,award,provider,COMPLETE_C
from confia_lean_auditor.experimental.tme_semantic_formal_p3.evidence import bind_evidence
from confia_lean_auditor.experimental.tme_semantic_formal_p3.mapper import SourceDocument
from confia_lean_auditor.experimental.tme_semantic_formal_p3.discourse import DiscourseStateResolver
from confia_lean_auditor.experimental.tme_semantic_formal_p3.engine import evaluate


def resolve(text,claims=None):
    units=bind_evidence(json.dumps({'evidence':typed_claims(text) if claims is None else claims}),text,'controlled')
    return DiscourseStateResolver().resolve(SourceDocument.parse(text),units)


def test_I3_model_abandoned_is_not_discourse_or_veto_authority():
    text='b) segunda_branca: 12/36'
    plain=typed_claims(text);flagged=[dict(plain[0],abandoned=True,assertion_status='abandoned')]
    a=run(text,plain);b=run(text,flagged)
    assert a['score']==b['score']==0
    assert all(d['resolved_discourse_state']=='ACTIVE' for d in b['discourse_decisions'])
    assert all(d['checker_ref'] and d['checker_status']=='COMPOSITE_FAILED' for d in b['veto_decisions'] if d['hard_veto_eligible'])


def test_I4_superseded_native_and_semantic_cannot_block_correction():
    text='b) pares_ordenados: 6*5=30\nCorrigindo minha afirmação anterior:\npares_ordenados: 6*6=36'
    r=run(text)
    assert r['score']==2 and not r['conflicts']
    old=[d for d in r['discourse_decisions'] if d['source_range'][0]==3]
    assert len(old)==2 and {d['resolved_discourse_state'] for d in old}=={'SUPERSEDED'}
    assert len({d['canonical_id'] for d in old})==1
    for d in old:
        for receipt in d['supporting_spans']:
            a,b=receipt['marker_range']
            assert text[a:b]==receipt['marker_source']


def test_I5_ambiguous_cannot_be_positive_witness():
    span='Talvez a probabilidade da segunda branca seja 11/36.'
    text='b) '+span;r=run(text,[claim(text,'segunda_branca','11/36',span=span)])
    assert r['score']==0
    assert r['discourse_decisions'][0]['resolved_discourse_state']=='AMBIGUOUS'
    assert not r['discourse_decisions'][0]['positive_credit_eligibility']


def test_I6_ambiguous_does_not_defeat_independent_active_witness():
    span='Talvez a probabilidade da segunda branca seja 12/36.'
    text='b) segunda_branca: 11/36\n'+span
    r=run(text,[claim(text,'segunda_branca','11/36'),claim(text,'segunda_branca','12/36',span=span)])
    assert r['score']==2 and not r['conflicts'] and r['review_recommended']
    assert award(r,'b.second_white_probability')['eligible']


def test_I10_processing_order_cannot_change_graph_or_awards():
    text='a) inferiores_brancas: 2\nb) segunda_branca: 11/36\nsegunda_branca: 12/36'
    cs=typed_claims(text)
    a=run(text,cs);b=run(text,list(reversed(cs)))
    assert a['score']==b['score']==2
    assert a['ledger_revision']==b['ledger_revision']
    assert [(x['obligation_id'],x['eligible']) for x in a['awards']]==[(x['obligation_id'],x['eligible']) for x in b['awards']]
    assert {d['decision_id'] for d in a['veto_decisions']}=={d['decision_id'] for d in b['veto_decisions']}


def test_I11_overlapping_envelope_does_not_change_retraction():
    from test_tme_p3_abandonment_safety import RECORDED
    cs=json.loads(json.dumps(RECORDED['p3_rob_e02']))
    text='a) '+cs[0]['source_span']+'\nb) '+cs[1]['source_span']+'\n'+cs[2]['source_span']
    a=run(text,cs)
    cs[1]['source_span']+='\n'+cs[2]['source_span'];cs[1]['source_evidence_ids']+=cs[2]['source_evidence_ids']
    b=run(text,cs)
    assert a['score']==b['score']==4
    assert {d['canonical_id'] for d in a['discourse_decisions']}=={d['canonical_id'] for d in b['discourse_decisions']}
    assert not a['conflicts'] and not b['conflicts']


def test_I14_incorrect_correction_does_not_resurrect_true_prior():
    text='b) segunda_branca: 11/36\nCorrigindo minha afirmação anterior:\nsegunda_branca: 12/36'
    r=run(text)
    assert r['score']==0
    assert any(d['resolved_discourse_state']=='SUPERSEDED' for d in r['discourse_decisions'])
    assert any(d['hard_veto_eligible'] for d in r['veto_decisions'])
    assert all('11/36' not in x['source_span'] for x in r['projection'])


def test_I18_native_fallback_uses_policy_current_stays_legacy():
    text='b) pares_ordenados: 6*5=30\nCorrigindo minha afirmação anterior:\npares_ordenados: 6*6=36'
    def unavailable(*args):raise TimeoutError('local controlled failure')
    r=evaluate('fallback','TME2026P3',text,extraction_provider=unavailable,use_lean=False)
    c=evaluate('current','TME2026P3',text,mode='tme_current',use_lean=False)
    assert r['fallback'] and r['effective_mode']=='TME_SEMANTIC_FORMAL_NATIVE_FALLBACK' and r['score']==2
    assert r['discourse_decisions'] and r['veto_decisions']
    assert c['effective_mode']=='TME_CURRENT' and 'discourse_decisions' not in c and c['score']==0


def test_I20_composite_never_mixes_withdrawn_color_and_final_count():
    text='c) estrategia_2: preta\ncontagem_2: 2\nSubstituo essa escolha de cor e sua contagem:\nestrategia_2: cinza\ncontagem_2: 3'
    r=run(text)
    assert r['score']==2 and not r['conflicts']
    old={d['evidence_id'] for d in r['discourse_decisions'] if d['resolved_discourse_state']=='SUPERSEDED'}
    assert old
    assert not any(old.intersection(v['evidence_ids']) for v in r['verification_results'] if v.get('original_fact'))


def test_different_subject_na_verdade_is_not_retraction():
    span='Ao repetir o mesmo compartimento, o quinto também libera branca.'
    conclusion='Na verdade, a probabilidade da segunda branca é 11/36.'
    text='b) '+span+'\n'+conclusion
    r=run(text,[claim(text,'repeticao_branca',span,span=span),claim(text,'segunda_branca','11/36',span=conclusion)])
    assert r['score']==0 and all(d['resolved_discourse_state']=='ACTIVE' for d in r['discourse_decisions'])


def test_revision_chain_is_source_ordered():
    text='b) segunda_branca: 12/36\nCorrigindo:\nsegunda_branca: 10/36\nCorrigindo:\nsegunda_branca: 11/36'
    r=run(text)
    assert r['score']==2 and not r['conflicts']
    assert sum(d['resolved_discourse_state']=='SUPERSEDED' for d in r['discourse_decisions'])==4


def test_explicit_withdrawal_without_replacement_has_no_active_authority():
    text='b) segunda_branca: 12/36\nIsso está errado.'
    r=run(text)
    assert r['score']==0 and not r['conflicts']
    assert all(d['resolved_discourse_state']=='NON_ADOPTED' for d in r['discourse_decisions'])


def test_marker_for_different_intervening_property_cannot_retract_old_claim():
    text='a) inferiores_brancas: 5\nCorrigindo a probabilidade:\nprimeira_branca: 1/3\ninferiores_brancas: 2'
    r=run(text)
    assert r['score']==2 and not award(r,'a.bottom_white_count')['eligible']
    assert all(d['resolved_discourse_state']=='ACTIVE' for d in r['discourse_decisions'])


def test_adopted_negation_is_not_synonym_for_nonadopted():
    span='Não é verdade que ao repetir o mesmo compartimento o quinto também libera branca.'
    text='b) '+span;r=run(text,[claim(text,'repeticao_branca',span,span=span)])
    assert r['discourse_decisions'][0]['resolved_discourse_state']=='ACTIVE'
    assert r['score']==0 and not r['conflicts']


@pytest.mark.parametrize('header',['Transcrição do enunciado:', 'Trecho identificado como citação:', 'Helena disse:', 'Segundo Carlos:'])
def test_nonadopted_header_survives_narrow_native_and_semantic_envelopes(header):
    text='c) '+header+'\ncontinuar: {1,2}'
    r=run(text)
    assert r['score']==0 and not r['conflicts']
    assert all(d['resolved_discourse_state']=='NON_ADOPTED' for d in r['discourse_decisions'])


def test_distant_indefinite_correction_cannot_invent_retraction_target():
    text='b) segunda_branca: 1/2\n\nPreparei outros cálculos.\n\nCorrigindo um cálculo:\nsegunda_branca: 11/36'
    r=run(text)
    assert r['score']==0 and r['conflicts']
    assert all(d['resolved_discourse_state']=='ACTIVE' for d in r['discourse_decisions'])


def test_normalized_marker_offsets_are_translated_back_to_source():
    import re
    from confia_lean_auditor.experimental.tme_semantic_formal_p3.discourse import _written_range
    from confia_lean_auditor.student_claims.semantic import normalized
    text='α² e √4. Corrigindo a afirmação:'
    match=re.search('corrigindo',normalized(text))
    a,b=_written_range(text,match,0)
    assert text[a:b]=='Corrigindo'
