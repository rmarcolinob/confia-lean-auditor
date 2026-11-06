"""Guard-only membership, source/context boundaries and controlled DEV evidence."""
from dataclasses import replace
import json
from pathlib import Path
import pytest
from test_tme_semantic_formal_p3 import claim, run, award, provider, PROBLEM_ID
from confia_lean_auditor.experimental.tme_semantic_formal_p3.engine import evaluate
from confia_lean_auditor.experimental.tme_semantic_formal_p3.conflict_guard import membership_result, conflict_guards
from confia_lean_auditor.experimental.tme_semantic_formal_p3.evidence import bind_evidence
from confia_lean_auditor.experimental.tme_semantic_formal_p3.mapper import SourceDocument, ObligationMapper
from confia_lean_auditor.tme.p3_machine import load_machine
from confia_lean_auditor.tme.obligation_experiment import primary_audit

ROOT=Path(__file__).resolve().parents[1]
POSITIVE='Ao repetir o mesmo compartimento, somente o sexto libera branca.'
FIFTH='Ao repetir o mesmo compartimento, o quinto também libera branca.'
PAYLOAD='O compartimento 5 também libera branca ao repetir o mesmo compartimento.'

def situation(negative=FIFTH, *, reverse=False, changes=None, item='b', independent=True):
    positive=('Na verdade, '+POSITIVE[0].lower()+POSITIVE[1:]) if reverse else POSITIVE
    lines=[negative,positive] if reverse else [positive,negative]
    text=('a) Há duas bolas brancas embaixo.\n' if independent else '')+item+') '+'\n'.join(lines)
    good=claim(text,'repeticao_branca','{6}',span=positive,item=item)
    bad=claim(text,'repeticao_branca',PAYLOAD,span=negative,item=item)
    bad.update(changes or {})
    claims=[bad,good] if reverse else [good,bad]
    if independent:claims.insert(0,claim(text,'inferiores_brancas','2',span='Há duas bolas brancas embaixo.'))
    return text,claims

def test_positive_exclusive_sixth_keeps_existing_credit():
    text='b) '+POSITIVE;r=run(text,[claim(text,'repeticao_branca','{6}',span=POSITIVE)])
    assert r['score']==2 and award(r,'b.same_compartment')['eligible']
    assert not r['conflicts'] and not r['conflict_guard_results']

@pytest.mark.parametrize('index',range(1,7))
def test_frozen_machine_decides_each_membership(index):
    machine=load_machine(ROOT/'examples/pautas/tme2_problem3.machine.v1.json')
    r=membership_result(index,machine)
    assert r['checker_receipt']['derived_same_white_pairs']==[[6,6]]
    assert r['status']==('DETERMINISTIC_VERIFIED' if index==6 else 'DETERMINISTIC_FAILED')
    assert r['checker_receipt']['event']['pair']==[index,index]
    assert r['mathematical_refutation']==(index!=6)

def test_membership_truth_changes_with_trusted_machine_not_literal_five():
    machine=load_machine(ROOT/'examples/pautas/tme2_problem3.machine.v1.json')
    altered=replace(machine,stacks=machine.stacks[:4]+(('gray','white'),)+machine.stacks[5:])
    assert membership_result(5,machine)['mathematical_refutation']
    changed=membership_result(5,altered)
    assert changed['status']=='DETERMINISTIC_VERIFIED'
    assert changed['checker_receipt']['derived_same_white_pairs']==[[5,5],[6,6]]

@pytest.mark.parametrize('reverse',[False,True])
def test_conflict_blocks_only_same_family_without_last_assertion_precedence(reverse):
    text,claims=situation(reverse=reverse);r=run(text,claims)
    if reverse:
        # The helper writes a same-subject 'Na verdade' correction; approved
        # source policy supersedes it even if the model did not mark abandoned.
        assert r['score']==4 and not r['conflicts']
        assert any(d['resolved_discourse_state']=='SUPERSEDED' for d in r['discourse_decisions'])
        return
    assert r['score']==2 and isinstance(r['score'],float) and not r['fallback']
    assert award(r,'a.bottom_white_count')['eligible']
    assert not award(r,'b.same_compartment')['eligible']
    assert [c['obligation_id'] for c in r['conflicts']]==['b.same_compartment','b.second_white_probability']
    g=r['conflict_guard_results'][0]
    assert g['guard_only'] and not g['award_eligible'] and not g['sufficiency_decision']['sufficient']
    assert g['status']=='DETERMINISTIC_FAILED' and g['atomic_claim']['compartment']==5
    assert g['atomic_claim']['literal_token']=='quinto' and g['source_span']==FIFTH
    assert text[g['atomic_claim']['literal_start']:g['atomic_claim']['literal_end']]=='quinto'
    assert g['atomic_claim']['kind']=='membership_claim' and 'set' not in g['atomic_claim']
    assert g['checker_receipt']['event']['second_color']=='black'
    assert any(d['provenance']['producer']=='atomic_guard' and d['hard_veto_eligible'] for d in r['veto_decisions']) and r['review_recommended']
    assert any(v['status']=='CONTEXT_REJECTED' for v in r['verification_results'])

@pytest.mark.parametrize('prefix',[
 'Talvez ', 'Beatriz disse que ', 'Pensei que fosse ', 'Tentativa descartada: ',
 'Não é verdade que ', 'Citação: ', 'Hipótese não adotada: '])
def test_context_rejected_atomic_source_does_not_block_valid_independent_span(prefix):
    negative=prefix+FIFTH[0].lower()+FIFTH[1:]
    text,claims=situation(negative)
    r=run(text,claims)
    assert r['score']==4 and award(r,'b.same_compartment')['eligible']
    assert not r['conflict_guard_results'] and not r['conflicts']

@pytest.mark.parametrize('change',[
 # Unsupported abandoned-only flags now have dedicated safety tests.
 {'assertion_status':'hypothetical'},{'hypothetical':True},
 {'attributed_to_student':False},{'polarity':'negative'},
 {'scope':'exploration'},{'scope':'side_calculation'},{'scope':'unknown'},
 {'assertion_status':'quoted'}])
def test_model_context_flags_cannot_hide_written_active_refutation(change):
    text,claims=situation(changes=change);r=run(text,claims)
    assert r['score']==2 and r['conflict_guard_results']
    assert any(d['hard_veto_eligible'] for d in r['veto_decisions'])

@pytest.mark.parametrize('change',[{'subject':'favoraveis_distintos','claim_type':'math'},
    {'obligation_candidates':['b.different_favorable']},{'item_id':'c'}])
def test_other_subject_obligation_or_item_is_not_a_same_compartment_guard(change):
    text,claims=situation(changes=change);r=run(text,claims)
    assert r['score']==4 and not r['conflict_guard_results']

def test_other_source_item_cannot_veto_b():
    text='b) '+POSITIVE+'\nc) '+FIFTH
    r=run(text,[claim(text,'repeticao_branca','{6}',span=POSITIVE),claim(text,'repeticao_branca',PAYLOAD,span=FIFTH,item='b')])
    assert r['score']==2 and not r['conflict_guard_results']

@pytest.mark.parametrize('negative',[
 'O número 5 aparece na página.',
 'Ao repetir o mesmo compartimento, o quinto também tem bolas brancas no alto.',
 'Ao repetir o mesmo compartimento, o quinto também é uma etiqueta.',
])
def test_incidental_member_or_wrong_property_does_not_generate_guard(negative):
    text,claims=situation(negative);r=run(text,claims)
    assert r['score']==4 and not r['conflict_guard_results']

def test_elliptical_member_is_bound_to_explicit_same_family_source():
    text,claims=situation('O quinto também.')
    r=run(text,claims)
    assert r['score']==2 and r['conflict_guard_results'][0]['atomic_claim']['compartment']==5
    lone='b) O quinto também.'
    r=run(lone,[claim(lone,'repeticao_branca',PAYLOAD,span='O quinto também.')])
    assert r['score']==0 and not r['conflict_guard_results']

@pytest.mark.parametrize('member', ['quinto','sexto','compartimento 5','compartimento 6'])
def test_atomic_route_never_creates_positive_credit_even_when_membership_is_true(member):
    span=f'Ao repetir o mesmo compartimento, o {member} também libera branca.'
    text='b) '+span;r=run(text,[claim(text,'repeticao_branca',span,span=span)])
    assert r['score']==0 and not any(a['eligible'] for a in r['awards'])
    g=r['conflict_guard_results'][0]
    assert g['guard_only'] and not g['award_eligible'] and g['formal_status']=='FORMAL_NOT_ATTEMPTED'
    assert g['status']==('DETERMINISTIC_VERIFIED' if member.endswith(('sexto','6')) else 'DETERMINISTIC_FAILED')

def test_guard_uses_literal_member_not_model_repaired_payload():
    text,claims=situation();claims[-1]['normalized_claim']='O compartimento 6 também libera branca.'
    r=run(text,claims)
    assert r['score']==2 and r['conflict_guard_results'][0]['atomic_claim']['compartment']==5

def test_source_binding_tampering_cannot_create_guard():
    text,claims=situation();units=bind_evidence(json.dumps({'evidence':claims}),text,'test')
    doc=SourceDocument.parse(text);mapping=ObligationMapper().map(doc,units)
    altered=[e.model_copy(update={'source_span':'invented'}) if e.subject=='repeticao_branca' else e for e in units]
    assert conflict_guards(doc,altered,mapping)==[]

def test_current_branch_preserves_baseline_facts_and_numeric_score():
    text,claims=situation()
    document=SourceDocument.parse(text)
    before=primary_audit(PROBLEM_ID,document.items,solution_id='fixed-test',use_lean=False)
    run(text,claims)
    current=evaluate('fixed-test',PROBLEM_ID,text,mode='tme_current',use_lean=False)
    after=primary_audit(PROBLEM_ID,document.items,solution_id='fixed-test',use_lean=False)
    assert [x.model_dump(mode='json') for x in before]==[x.model_dump(mode='json') for x in after]
    assert current['current_bridge']==before[0].model_dump(mode='json')
    assert current['current_assessment']==before[1].model_dump(mode='json')
    assert current['score']==float(before[1].known_points) and 'conflict_guard_results' not in current

def test_controlled_observed_partial_conflict_emerges_as_two_points(tmp_path):
    # Frozen source is read, never edited. The five interpretations below are
    # the contents observed in DEV01, including its unsupported prose payload.
    cases=json.loads((ROOT/'tests/fixtures/tme_semantic_formal_p3/dev_sources.json').read_text())
    text=next(c['solution_text'] for c in cases if c['case_id']=='p3_dev_partial_conflict')
    spans=text.splitlines()
    claims=[claim(text,'inferiores_brancas','2',span=spans[0][3:],route_candidate='DETERMINISTIC',confidence=1),
            claim(text,'repeticao_branca','{6}',span=spans[1][3:],route_candidate='DETERMINISTIC',confidence=1),
            claim(text,'repeticao_branca',PAYLOAD,span=spans[2],route_candidate='DETERMINISTIC',confidence=.98),
            claim(text,'segunda_branca','11/36',span=spans[3],scope='final_conclusion',route_candidate='COMPOSITE',confidence=1),
            claim(text,'segunda_branca','12/36',span=spans[4],scope='final_conclusion',route_candidate='COMPOSITE',confidence=1)]
    r=evaluate('controlled-observed-source',PROBLEM_ID,text,extraction_provider=provider(claims),use_lean=False)
    (tmp_path/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    assert r['score']==2 and {a['obligation_id'] for a in r['awards'] if a['eligible']}=={'a.bottom_white_count'}
    assert {c['obligation_id'] for c in r['conflicts']}=={'b.same_compartment','b.second_white_probability'}
    assert r['extractor']['api_calls']==0 and not r['fallback'] and not r['technical_uncertainty']
