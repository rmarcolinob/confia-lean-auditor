"""P1–P5 with existing fixtures, local checks and simulated minimal providers only."""
import hashlib
import json
from pathlib import Path

import pytest

from confia_lean_auditor.semantic_policy import tme, service
from confia_lean_auditor.tme.accepted_audit import pauta_for
from confia_lean_auditor.tme.audit_models import TMEAuditResult
from confia_lean_auditor.tme.registry import audit_tme
from test_tme_accepted_integration import CASES, FULL, PARTIAL, FALSE, solution_for, offline, setup, prepare, execute

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT/'tests/fixtures/tme_p1_real_run'
ALL = [(n,c) for n in range(1,6) for c in CASES[n].values()]


def text_of(items):
    return '\n'.join(v if isinstance(v,str) else v.get('text','') for v in items.values())


def public_score(assessment):
    return float(assessment.score) if all(i.status == 'decided' for i in assessment.items) else None


def local_review(request):
    return dict(decision='review', justification='Provider simulado: pendência preservada.', quotes=[])


def review_p1(request):
    """Manual mathematical judgments for the stored source, never score outputs."""
    cid = request['criterion']['id']
    reasons = {
        'a.arithmetic_error_only': '137 foi identificado e a única operação 731−137 foi montada corretamente; 595 é um erro aritmético isolado.',
        'b.reversed_number': 'A expansão 100c+10b+a está explicitamente escrita.',
        'b.subtraction': 'As duas expansões decimais estão subtraídas na ordem correta.',
        'b.middle_cancellation': 'O texto afirma o cancelamento de 10b e mostra a subtração.',
        'b.factorization': 'O desenvolvimento escrito termina em 99a−99c=99(a−c).',
        'c.uses_expression': 'Usa o domínio de a−c para listar os múltiplos de 99, com a expressão demonstrada em (b).',
        'c.difference_domain': 'Declara os valores inteiros de 1 a 8 para a−c, compatíveis com os dígitos extremos não nulos.',
        'c.complete_list': 'Falta 792, correspondente à diferença 8; a lista não está completa.',
        'c.no_extraneous_values': 'Todos os sete valores escritos são múltiplos de 99 entre 99 e 792.',
        'c.single_list_error': 'A lista contém exatamente os sete primeiros valores; há uma única omissão, 792, sem valor indevido.',
        'd.equation': 'A equação 99(a−c)=594 está escrita.',
        'd.difference_six': 'O texto obtém a−c=6 a partir da equação.',
        'd.digit_pairs': 'Lista exatamente (7,1), (8,2) e (9,3).',
        'd.middle_choices': 'Afirma dez escolhas para o dígito central b.',
        'd.total_thirty': 'Relaciona três pares e dez escolhas ao total correto de 30.',
    }
    assert cid in reasons, 'A criterion already decided or irrelevant must not call the provider'
    evidence = request['accepted_item_evidence']
    quotes = [e['source_text'] for e in evidence if e['item_id']==cid[0]]
    if cid == 'c.uses_expression':
        quotes.extend(e['source_text'] for e in evidence if e['item_id']=='b')
    return dict(decision='not_met' if cid=='c.complete_list' else 'met',
        justification='SIMULAÇÃO OFFLINE: '+reasons[cid], quotes=quotes)


def stored_replay(provider=review_p1):
    recorded = TMEAuditResult.model_validate_json((REAL/'audit.json').read_text())
    source = (REAL/'solution.txt').read_text()
    items = json.loads((REAL/'input_mapping.json').read_text())['solution']
    # Do not execute the case/AuditService or its checkers. Only a copy of the
    # persisted mathematical result passes through the updated adapter offline.
    from confia_lean_auditor.core.problem_catalog import list_tme_problem_catalog
    statement = next(p['statement'] for p in list_tme_problem_catalog(ROOT) if p['id']=='TME2026P1')
    bridge, assessment = tme.apply(recorded.pauta, recorded.bridge, source, statement,
        provider=provider, item_sources=items)
    return recorded, bridge, assessment


def test_stored_p1_missing_facts_reach_fallback_without_rerunning_audit():
    for name,digest in json.loads((REAL/'source_manifest.json').read_text())['files'].items():
        assert hashlib.sha256((REAL/name).read_bytes()).hexdigest()==digest
    calls=[]
    def provider(request):
        calls.append(request['criterion']['id']); return review_p1(request)
    old,bridge,a=stored_replay(provider)
    assert old.score is None and old.assessment.known_points==1
    assert not any('semantic_fallback' in e.metadata for e in old.bridge.evidence.obligations)
    assert public_score(a)==18 and [i.points_awarded for i in a.items]==[2,5,5,6]
    assert a.items[0].selected_band=='a.arithmetic_only'
    assert a.items[2].children[2].selected_band=='c.list.one_error'
    assert len(calls)==len(set(calls))==15
    assert bridge.auditor==old.bridge.auditor  # No invented claim, check or proof.
    for previous,current in zip(old.bridge.evidence.obligations,bridge.evidence.obligations):
        if previous.status in {'supported','refuted'}:
            assert previous==current
        if 'semantic_fallback' in current.metadata:
            assert current.metadata['semantic_fallback']['formal_certification'] is False
            assert current.evidence_refs and current.attributable_to_student
    # Existing persisted result validation/PautaEngine binding still holds.
    updated=old.model_copy(update={'bridge':bridge,'assessment':a})
    assert TMEAuditResult.model_validate_json(updated.model_dump_json()).score==18


@pytest.mark.parametrize('n,case', ALL, ids=[f'P{n}-{c["id"]}' for n,c in ALL])
def test_all_existing_digital_fixtures_preserve_verified_results(n,case):
    items=case.get('solution',{case['item']:case['text']})
    b,a=audit_tme(f'TME2026P{n}',items,solution_id='offline-fixture',use_lean=False)
    updated,result=tme.apply(pauta_for(f'TME2026P{n}'),b,text_of(items),'Fixture existente.',
        item_sources=items,provider=local_review)
    selected=next(i for i in result.items if i.item_id==case['item'])
    assert selected.known_points==case['points']
    assert result.known_points==a.known_points
    assert updated.auditor==b.auditor
    for before,after in zip(b.evidence.obligations,updated.evidence.obligations):
        if before.status in {'supported','refuted'}:assert before==after


@pytest.mark.parametrize('n',range(1,6))
@pytest.mark.parametrize('kind',['full','partial','false'])
def test_five_problems_active_policy_acceptance_persistence(offline,monkeypatch,n,kind):
    monkeypatch.setenv('CONFIA_SPECIALIZED_POLICY',service.VERSION)
    client,_,_=offline
    items=solution_for(n,FULL[n]); changed=None
    if kind!='full':
        changed=CASES[n][PARTIAL[n] if kind=='partial' else FALSE[n]]
        items.update(solution_for(n,[changed['id']]))
    calls=[]
    def provider(self,request):
        calls.append(request['criterion']['id'])
        assert changed is not None and request['criterion']['id'].startswith(changed['item']+'.')
        # In these selected short fixtures the remaining obligations are not
        # developed. This is an explicit simulated opinion on the written item,
        # not an automatic production conversion of absence into zero.
        return dict(decision='not_met',justification='SIMULAÇÃO OFFLINE: o item desta fixture não desenvolve a obrigação solicitada.',
            quotes=[e['source_text'] for e in request['accepted_item_evidence'] if e['item_id']==changed['item']])
    monkeypatch.setattr(service.SemanticProvider,'__call__',provider)
    base,_,_,request=prepare(client,n,items)
    run,saved=execute(client,base,request)
    config=pauta_for(f'TME2026P{n}')
    expected=20 if changed is None else 20-next(i.max_points for i in config.items if i.id==changed['item'])+changed['points']
    assert saved.result.score==expected and saved.result.context.semantic_policy==service.VERSION
    assert saved.result.pauta==config
    assert len(calls)==len(set(calls))
    if kind=='full':assert calls==[]
    again=client.post(base+'/audits',json=request).json()
    assert again==run  # Persisted audit is reused; provider is not invoked twice.
    assert len(calls)==len(set(calls))


@pytest.mark.parametrize('n,case',[(2,'c_alternative'),(3,'b_tree'),(4,'b_parallelogram'),(4,'c_cases'),(5,'c_general')])
def test_complete_alternative_methods_need_no_semantic_readjudication(n,case):
    items=solution_for(n,FULL[n]);items.update(solution_for(n,[case]))
    b,_=audit_tme(f'TME2026P{n}',items,use_lean=False)
    _,a=tme.apply(pauta_for(f'TME2026P{n}'),b,text_of(items),'Fixture alternativa.',item_sources=items,
        provider=lambda _:pytest.fail('Already decided full method'))
    assert public_score(a)==20


@pytest.mark.parametrize('decision',['review','error','invalid','wrong_item'])
def test_pending_and_failures_do_not_become_zero(decision):
    def provider(request):
        if request['criterion']['id']!='b.factorization':return review_p1(request)
        if decision=='error':raise TimeoutError('offline')
        return dict(decision='review' if decision=='review' else 'met',justification='Controle simulado.',
            quotes=[] if decision=='review' else ['Não escrito.'] if decision=='invalid' else ['731 - 137 = 595'])
    old,b,a=stored_replay(provider)
    assert public_score(a) is None
    assert next(e for e in b.evidence.obligations if e.obligation_id=='b.factorization').status in {'indeterminate','technical_error'}
    assert a.items[0].points_awarded==2 and a.items[2].points_awarded==5 and a.items[3].points_awarded==6


def test_absent_item_cannot_trigger_context_fallback():
    items={'a':''};b,_=audit_tme('TME2026P1',items,use_lean=False)
    _,a=tme.apply(pauta_for('TME2026P1'),b,'','Enunciado.',item_sources=items,
        provider=lambda _:pytest.fail('No accepted item context'))
    assert public_score(a) is None


@pytest.mark.parametrize('source',[
    'Suponha que a solução seja 137.',
    'Tentativa descartada: 731-137=594.',
    '"731-137=594"',
    'Suponha por absurdo que exista solução ótima contendo k maior ou igual a 5. '
    'Troco k por 3 e k−3. A soma permanece k, mas 3(k−3)>k, pois 2k>9. '
    'Logo o produto aumenta, uma contradição com a maximalidade.',
])
def test_full_context_is_reviewed_without_promoting_hypotheses_to_verified_facts(source):
    n,item=(5,'b') if 'absurdo' in source else (1,'a')
    items={item:source};b,_=audit_tme(f'TME2026P{n}',items,use_lean=False)
    calls=[]
    def provider(request):
        calls.append(request)
        assert request['solution']==source
        assert request['accepted_item_evidence'][0]['source_text']==source
        return local_review(request)
    updated,a=tme.apply(pauta_for(f'TME2026P{n}'),b,source,'Enunciado.',item_sources=items,provider=provider)
    assert calls and updated.auditor==b.auditor and public_score(a) is None
    assert all(e.status not in {'supported','refuted'} for e in updated.evidence.obligations if e.origin=='semantic')


def test_wrong_mapping_is_rejected_before_provider_and_missing_diagram_is_not_invented():
    items=solution_for(2,['a_unconfirmed']);b,_=audit_tme('TME2026P2',items,use_lean=False)
    _,a=tme.apply(pauta_for('TME2026P2'),b,text_of(items),'Enunciado.',item_sources=items,
        provider=lambda _:pytest.fail('Diagram is not text evidence'))
    assert public_score(a) is None
    with pytest.raises(ValueError,match='SOURCE_MISMATCH'):
        tme.apply(pauta_for('TME2026P2'),b,'inventado','Enunciado.',item_sources={'a':'inventado'})


@pytest.mark.parametrize('n',range(1,6))
@pytest.mark.parametrize('outcome',['met','not_met','review','error'])
def test_each_problem_handles_external_outcomes_without_changing_other_decisions(n,outcome):
    from confia_lean_auditor.rubric.pauta.engine import PautaEngine
    items=solution_for(n,FULL[n]);config=pauta_for(f'TME2026P{n}')
    b,_=audit_tme(f'TME2026P{n}',items,use_lean=False)
    rows=list(b.evidence.obligations)
    # Find an actual verified obligation whose unavailability affects the grade.
    for index,e in enumerate(rows):
        if e.status!='supported':continue
        changed=list(rows);changed[index]=e.model_copy(update={'status':'technical_error'})
        evidence=b.evidence.model_copy(update={'obligations':tuple(changed)})
        if public_score(PautaEngine().evaluate(config,evidence)) is None:break
    else:pytest.fail('Fixture must have a meaningful verification dependency')
    altered=b.model_copy(update={'evidence':evidence});target=e.obligation_id
    calls=[]
    def provider(request):
        calls.append(request['criterion']['id'])
        if request['criterion']['id']!=target:return local_review(request)
        if outcome=='error':raise TimeoutError('offline simulated provider')
        return dict(decision=outcome,justification='Controle de integração simulado, não novo parecer sobre a fixture.',
            quotes=[request['accepted_item_evidence'][0]['source_text']])
    updated,a=tme.apply(config,altered,text_of(items),'Enunciado.',item_sources=items,provider=provider)
    changed=next(e for e in updated.evidence.obligations if e.obligation_id==target)
    assert changed.status=={'met':'supported','not_met':'refuted','review':'indeterminate','error':'technical_error'}[outcome]
    assert calls.count(target)==1
    if outcome=='met':assert public_score(a)==20
    if outcome in {'review','error'}:assert public_score(a) is None
    for before,after in zip(altered.evidence.obligations,updated.evidence.obligations):
        if before.status in {'supported','refuted'}:assert before==after


def test_decided_p1_replay_is_not_adjudicated_twice():
    old,b,a=stored_replay()
    items=json.loads((REAL/'input_mapping.json').read_text())['solution']
    again,result=tme.apply(old.pauta,b,(REAL/'solution.txt').read_text(),'Enunciado.',item_sources=items,
        provider=lambda _:pytest.fail('Already decided'))
    assert again==b and result==a


def test_valid_contradiction_proof_reaches_minimal_reviewer_and_original_pauta():
    source = ('Suponha por absurdo que exista solução ótima contendo k maior ou igual a 5. '
        'Troco k por 3 e k−3, ambos inteiros positivos. A soma permanece k, '
        'mas 3(k−3)>k, pois 2k>9. Logo o produto aumenta, uma contradição com a maximalidade.')
    items=solution_for(5,FULL[5]);items['b']=source
    bridge,_=audit_tme('TME2026P5',items,use_lean=False)
    calls=[]
    def provider(request):
        assert request['criterion']['id'].startswith('b.')
        assert request['accepted_item_evidence'][0]['source_text']==source
        calls.append(request['criterion']['id'])
        return dict(decision='met',quotes=[source],justification=(
            'SIMULAÇÃO OFFLINE: para k inteiro ≥5, 3 e k−3 são positivos, '
            'somam k e têm produto 3k−9>k; a troca contradiz a maximalidade.'))
    updated,a=tme.apply(pauta_for('TME2026P5'),bridge,text_of(items),'P5: produto máximo de parcelas inteiras positivas.',
        item_sources=items,provider=provider)
    assert calls and len(calls)==len(set(calls)) and public_score(a)==20
    assert updated.auditor==bridge.auditor
    assert next(i for i in a.items if i.item_id=='b').points_awarded==4
