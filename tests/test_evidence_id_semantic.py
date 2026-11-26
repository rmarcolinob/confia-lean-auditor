import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from confia_lean_auditor.student_claims import evidence_id_semantic as sem
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.student_claims.obligation_catalog import mathematical_obligations
from confia_lean_auditor.tme.evidence_id_experiment import run_shadow
from confia_lean_auditor.tme.obligation_experiment import activate_shadow


def selection(ids=('E001',), obligation='b.apqr', subject='apqr', expression='parallelogram', kind='enum', mode='asserted'):
    return sem.ObligationEvidenceSelection(obligation_id=obligation, evidence_present=True,
        evidence_ids=list(ids), assertion_mode=mode,
        mathematical_payload=sem.previous.MathematicalPayload(subject=subject, expression=expression),
        representation_kind=kind, reason_code='literal_evidence')


def provider(selections):
    return lambda *args: (selections, dict(status='completed', model='fixture', api_calls=0))


def test_units_exact_stable_unicode_context_and_repetition():
    text='(a) Tentei x=5, mas isso está errado.\r\n731 − 137 = 594\r\n\r\n731 − 137 = 594\n'
    units=evidence_units(text)
    assert units==evidence_units(text)
    assert [u.evidence_id for u in units]==['E001','E002','E003','E004']
    assert all(text[u.source_start:u.source_end]==u.exact_text for u in units)
    assert units[1].exact_text=='Tentei x=5, mas isso está errado.'
    assert units[2].exact_text==units[3].exact_text and units[2].source_start!=units[3].source_start
    assert units[2].context_ids!=units[3].context_ids
    assert 'E002' in units[2].context_ids


def test_units_preserve_every_non_whitespace_character():
    text='  (a) Uma frase. Outra frase.\n\n(b)\n 1. Lista: (2, 3, 3).\nabc\n'
    units=evidence_units(text);covered={i for u in units for i in range(u.source_start,u.source_end)}
    assert all(i in covered for i,c in enumerate(text) if not c.isspace())
    assert units[1].exact_text=='Uma frase. Outra frase.'


@pytest.mark.parametrize('field',['source_text','source_start','source_end','points','score','supported','refuted','award','deny'])
def test_output_cannot_supply_spans_or_judgments(field):
    raw=selection().model_dump();raw[field]=0
    with pytest.raises(ValidationError):sem.ObligationEvidenceSelection.model_validate(raw)


@pytest.mark.parametrize('ids',[['E999'],['E001','E001'],[]])
def test_invalid_ids_and_incoherent_presence_fail_closed(ids):
    raw=selection().model_dump();raw['evidence_ids']=ids
    with pytest.raises(ValueError):sem.validate_response(json.dumps({'selections':[raw]}),mathematical_obligations('TME2026P4'),evidence_units('APQR é um paralelogramo.'))


def test_target_kind_binding_is_strict():
    raw=selection(subject='perimeter_apqr',expression='12',kind='math').model_dump()
    with pytest.raises(ValueError,match='target_representation_mismatch'):
        sem.validate_response(json.dumps({'selections':[raw]}),mathematical_obligations('TME2026P4'),evidence_units('perímetro APQR é 12'))


@pytest.mark.parametrize('problem',[f'TME2026P{i}' for i in range(1,6)])
def test_structured_schema_links_target_kind_subject_and_has_supported_shape(problem):
    targets=mathematical_obligations(problem);schema=sem.response_schema(targets,evidence_units('texto\nlinha'))
    assert schema['type']=='object' and 'anyOf' not in schema
    props=enums=0
    def visit(node):
        nonlocal props,enums
        if isinstance(node,dict):
            assert not {'allOf','oneOf','if','then','else','discriminator','uniqueItems'}&set(node)
            if node.get('type')=='object':
                assert node['additionalProperties'] is False
                assert set(node['required'])==set(node['properties']);props+=len(node['properties'])
            enums+=len(node.get('enum',[]))
            for value in node.values():visit(value)
        elif isinstance(node,list):
            for value in node:visit(value)
    visit(schema);assert props<=5000 and enums<=1000
    allowed={t['obligation_id']:{r['subject']:r['kind'] for r in t['representations']} for t in targets}
    for branch in schema['properties']['selections']['items']['anyOf'][1:]:
        p=branch['properties'];target=p['obligation_id']['enum'][0];kind=p['representation_kind']['enum'][0]
        assert all(allowed[target][s]==kind for s in p['mathematical_payload']['properties']['subject']['enum'])


def test_multi_evidence_keeps_original_envelope_and_all_selected_units():
    text='APQR é um paralelogramo.\nO perímetro de APQR é:\n2*((6-x)+x)=12.'
    selections=[selection(),selection(('E002','E003'),'b.perimeter_apqr','perimeter_apqr','2*((6-x)+x)=12','math')]
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='multi',provider=provider(selections),use_lean=False)
    event=result.telemetry['events'][1]
    assert event['id_grounded'] and event['attributable']
    assert [u['evidence_id'] for u in event['evidence_bindings']]==['E002','E003']
    record=next(r for r in result.potential_bridge.auditor.records if r.record_id==event['record_id'])
    assert record.source.raw_text=='O perímetro de APQR é:\n2*((6-x)+x)=12.'
    assert result.assessment.score==0
    assert activate_shadow(result,gate_passed=True).score==6


def test_envelope_cannot_supply_payload_from_unselected_units():
    text='APQR tem um perímetro.\nO perímetro de APQR é 12.\nFim do cálculo de APQR.'
    s=selection(('E001','E003'),'b.perimeter_apqr','perimeter_apqr','12','math')
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='gap',provider=provider([s]),use_lean=False)
    assert not result.telemetry['events'][0]['attributable']
    assert result.telemetry['events'][0]['reason']=='payload_not_in_selected_units'


@pytest.mark.parametrize('prefix,suffix',[
    ('Não é verdade que ',''),('Suponha que ',''),('Tentei: ',' Mas está errado.'),
    ('João disse que ',''),('A solução de João diz ',''),('Talvez ',''),('Na página 12, ',''),
    ('João disse:\n',''),('“','”'),('', '\n\nIsso estava errado.'),
    ('Suponha o seguinte:\n',''),('', '\nDepois concluí que não era isso.'),
])
def test_context_controls_even_when_only_positive_line_selected(prefix,suffix):
    text=prefix+'APQR é um paralelogramo. Seu perímetro APQR é 2*((6-x)+x)=12.'+suffix
    unit=next(u for u in evidence_units(text) if 'APQR' in u.exact_text)
    cs=[selection((unit.evidence_id,)),selection((unit.evidence_id,),'b.perimeter_apqr','perimeter_apqr','2*((6-x)+x)=12','math')]
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='negative',provider=provider(cs),use_lean=False)
    assert not result.potential_bridge.auditor.facts
    assert activate_shadow(result,gate_passed=True).score==0


@pytest.mark.parametrize('mode',['negated','hypothetical','rejected','quoted','uncertain'])
def test_id_does_not_override_nonasserted_mode(mode):
    text='APQR é um paralelogramo.'
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='mode',provider=provider([selection(mode=mode)]),use_lean=False)
    assert result.telemetry['events'][0]['id_grounded']
    assert not result.potential_bridge.auditor.facts


def test_unselected_conflicting_value_blocks_favorable_selection():
    text='O perímetro de APQR é 12.\nO perímetro de APQR é 14.'
    s=selection(('E001',),'b.perimeter_apqr','perimeter_apqr','12','math')
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='conflict',provider=provider([s]),use_lean=False)
    assert not result.potential_bridge.auditor.facts
    assert result.telemetry['events'][0]['context_guard']=='unselected_conflicting_values'


@pytest.mark.parametrize('lhs,status',[('2*((6-x)+x)','verified'),('2*((6-x)+x)+1','refuted')])
def test_written_method_reaches_real_lean(lhs,status):
    text=f'APQR é um paralelogramo.\nSeu perímetro APQR é {lhs}=12.'
    cs=[selection(),selection(('E002',),'b.perimeter_apqr','perimeter_apqr',lhs+'=12','math')]
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='lean',provider=provider(cs),use_lean=True)
    fact=next(f for f in result.potential_bridge.auditor.facts if f.fact_id=='b.perimeter_apqr')
    assert fact.verification.status==status and fact.verification_source=='student_lean'
    assert activate_shadow(result,gate_passed=True).score==(6 if status=='verified' else 0)


def test_id_cannot_reroute_unmapped_or_different_item():
    text='APQR é um paralelogramo.'
    for items in ({},{'a':text}):
        result=run_shadow('TME2026P4',items,text,solution_id='mapping',provider=provider([selection()]),use_lean=False)
        assert result.telemetry['events'][0]['id_grounded']
        assert not result.potential_bridge.auditor.facts


def test_long_evidence_is_not_truncated():
    text='APQR é um paralelogramo. '+'Longo texto. '*200
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='long',provider=provider([selection()]),use_lean=False)
    assert result.telemetry['events'][0]['reason']=='evidence_envelope_too_long'
    assert not result.potential_bridge.auditor.facts


def test_shadow_isolation_and_primary_monotonicity(monkeypatch):
    from confia_lean_auditor.rubric.pauta.engine import PautaEngine
    original=PautaEngine.evaluate;calls=[]
    def spy(self,config,evidence):
        calls.append(evidence)
        assert not any(s.startswith('semantic:') for e in evidence.obligations for s in e.source_claim_ids)
        return original(self,config,evidence)
    monkeypatch.setattr(PautaEngine,'evaluate',spy)
    text='APQR: parallelogram'
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='primary',provider=provider([]),use_lean=False)
    assert len(calls)==1
    assert result.telemetry['combined_potential_supported']>=result.telemetry['baseline_supported']


def test_primary_loss_rejects_whole_supplement(monkeypatch):
    from confia_lean_auditor.tme import evidence_id_experiment as ex
    from confia_lean_auditor.tme.obligation_experiment import primary_audit
    text='APQR: parallelogram';primary=primary_audit('TME2026P4',{'b':text},solution_id='keep',use_lean=False)
    original=ex.verify_without_scoring
    def missing(*args,**kwargs):
        original(*args,**kwargs)  # produce session telemetry normally
        return primary[0].model_copy(update={'evidence':primary[0].evidence.model_copy(update={'obligations':tuple(e.model_copy(update={'status':'indeterminate'}) for e in primary[0].evidence.obligations)})})
    monkeypatch.setattr(ex,'verify_without_scoring',missing)
    result=ex.run_shadow('TME2026P4',{'b':text},text,solution_id='keep',provider=provider([]),primary=primary,use_lean=False)
    assert result.potential_bridge==primary[0] and result.telemetry['baseline_regression_blocked']


def test_provider_preserves_bad_response_and_has_no_retries_or_model_offsets(monkeypatch):
    import openai
    seen=[]
    raw=json.dumps({'selections':[selection(('E999',)).model_dump()]})
    class Client:
        def __init__(self,**kwargs):assert kwargs['max_retries']==0;self.responses=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def create(self,**kwargs):
            seen.append(kwargs)
            return SimpleNamespace(status='completed',output=[],output_text=raw,model='fixture',id='test',usage=None)
    monkeypatch.setattr(openai,'OpenAI',Client);sem.request_selections.cache_clear()
    args=('TME2026P4','APQR é um paralelogramo.',json.dumps(mathematical_obligations('TME2026P4')),json.dumps(sem.configuration()))
    cs,meta=sem.request_selections(*args);sem.request_selections(*args)
    assert not cs and meta['validation_error']=='unknown_evidence_id' and meta['raw_output']==raw and meta['response_id']=='test'
    assert len(seen)==1
    wire=json.loads(seen[0]['input'][1]['content'])
    assert set(wire)=={'problem_id','statement','target_obligations','evidence_units'}
    assert all(not {'source_start','source_end'}&set(u) for u in wire['evidence_units'])
    sem.request_selections.cache_clear()


def test_absence_requires_no_ids_and_is_not_an_assertion():
    absent=sem.ObligationEvidenceSelection(obligation_id='b.apqr',evidence_present=False,evidence_ids=[],
        assertion_mode='uncertain',mathematical_payload=sem.previous.MathematicalPayload(subject='none',expression=''),
        representation_kind='none',reason_code='no_evidence')
    text='Não escrevi uma solução.'
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='absent',provider=provider([absent]),use_lean=False)
    assert not result.potential_bridge.auditor.facts and not result.telemetry['events'][0]['id_grounded']


@pytest.mark.parametrize('subject,kind,expression,text',[
    ('product','math','54','O produto é 54.\nO produto é 55.'),
    ('candidate','positive_multiset','(3,3,3,2)','Lista: (3,3,3,2).\nLista: (4,4,3).'),
])
def test_p5_unselected_conflicts_fail_closed(subject,kind,expression,text):
    s=selection(('E001',),'a.'+subject,subject,expression,kind)
    result=run_shadow('TME2026P5',{'a':text},text,solution_id='p5-conflict',provider=provider([s]),use_lean=False)
    assert not result.telemetry['events'][0]['attributable']


def test_duplicate_selections_keep_one_record():
    text='APQR é um paralelogramo.';s=selection()
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='dup',provider=provider([s,s]),use_lean=False)
    assert len(result.potential_bridge.auditor.facts)==1
    assert any(e.get('deduplicated') for e in result.telemetry['events'])


def test_noncontiguous_ids_retain_unselected_context_without_inventing_spans():
    text='O perímetro de APQR é:\nEste é o cálculo:\n2*((6-x)+x)=12.'
    s=selection(('E001','E003'),'b.perimeter_apqr','perimeter_apqr','2*((6-x)+x)=12','math')
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='distributed',provider=provider([s]),use_lean=False)
    e=result.telemetry['events'][0]
    assert e['attributable'] and len(e['evidence_bindings'])==2
    record=next(r for r in result.potential_bridge.auditor.records if r.record_id==e['record_id'])
    assert record.source.raw_text==text


def test_checker_replay_revalidates_id_projection(monkeypatch):
    from dataclasses import replace
    from confia_lean_auditor.student_claims.tme2_p4_digital import collect_tme2_p4_digital
    from confia_lean_auditor.lean.student_claim_checkers.tme2_p4 import verify_tme2_p4_digital
    text='APQR é um paralelogramo.'
    session=sem.EvidenceProjectionSession('TME2026P4',text,mathematical_obligations('TME2026P4'),[selection()],{})
    with legacy.supplement_scope(session):
        digital=collect_tme2_p4_digital({'b':text})
        forged=digital.records[0].model_copy(update={'canonicalization_reason':'forged'})
        with pytest.raises(ValueError):verify_tme2_p4_digital(replace(digital,records=(forged,)),'tamper',use_lean=False)
