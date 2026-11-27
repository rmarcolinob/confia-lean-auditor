"""Obligation interpretation safety and unchanged downstream verification."""
import json
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from confia_lean_auditor.student_claims import obligation_semantic as sem
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.student_claims.obligation_catalog import mathematical_obligations
from confia_lean_auditor.tme.obligation_experiment import run_shadow,activate_shadow,primary_audit,unresolved_targets


def candidate(text,obligation='b.apqr',subject='apqr',expression='parallelogram',kind='enum',mode='asserted',full=None):
    full=full or text;start=full.index(text)
    return sem.ObligationEvidenceCandidate(obligation_id=obligation,candidate_id=subject,evidence_present=True,
        source_text=text,source_start=start,source_end=start+len(text),assertion_mode=mode,
        mathematical_payload=sem.MathematicalPayload(subject=subject,expression=expression),
        representation_kind=kind,reason_code='literal_evidence')


def provider(candidates):
    return lambda *args:(tuple(candidates),{'status':'completed','model':'fixture'})


def p4_candidates(text):
    return [candidate(text),candidate(text,'b.perimeter_apqr','perimeter_apqr','2*((6-x)+x)=12','math')]


def test_catalog_is_complete_and_only_mathematical():
    forbidden={'points','max_points','score','synthetic_expected_score','selected_band','award','deny','supported','refuted'}
    def inspect(value):
        if isinstance(value,dict):
            assert not forbidden.intersection(value)
            for x in value.values():inspect(x)
        elif isinstance(value,(list,tuple)):
            for x in value:inspect(x)
    for p,n in zip(range(1,6),(21,23,13,31,58)):
        entries=mathematical_obligations(f'TME2026P{p}');assert len(entries)==n
        inspect(entries)
        assert all(t['description']!=t['obligation_id'] for t in entries)
        assert all(r['subject']!='placement' for t in entries for r in t['representations'])
        schema=sem.response_schema(entries)
        for obj in (schema,*schema['$defs'].values()):
            if obj.get('type')=='object':
                assert obj['additionalProperties'] is False
                assert set(obj['required'])==set(obj['properties'])


@pytest.mark.parametrize('field',['supported','refuted','points','score','award','deny'])
def test_candidate_cannot_return_judgments(field):
    raw=candidate('APQR é paralelogramo.').model_dump();raw[field]=True
    with pytest.raises(ValidationError):sem.ObligationEvidenceCandidate.model_validate(raw)
    raw=candidate('APQR é paralelogramo.').model_dump();raw['mathematical_payload'][field]=1
    with pytest.raises(ValidationError):sem.ObligationEvidenceCandidate.model_validate(raw)


def test_no_evidence_is_explicit_and_never_a_record():
    c=sem.ObligationEvidenceCandidate(obligation_id='b.apqr',candidate_id='none',evidence_present=False,
        source_text='',source_start=0,source_end=0,assertion_mode='uncertain',
        mathematical_payload=sem.MathematicalPayload(subject='none',expression=''),representation_kind='none',reason_code='no_evidence')
    result=run_shadow('TME2026P4',{'b':'Nada escrito.'},'Nada escrito.',solution_id='absent',provider=provider([c]),use_lean=False)
    assert not result.potential_bridge.auditor.facts
    assert result.telemetry['events'][0]['reason']=='no_evidence'
    assert result.assessment.score==0


def test_present_qualitative_argument_remains_candidate_without_authority():
    text='Parcelas grandes podem ser trocadas por parcelas menores aumentando o produto.'
    c=candidate(text,'c.no_ge5','unmapped',text,'qualitative').model_copy(update={'reason_code':'unsupported_representation'})
    result=run_shadow('TME2026P5',{'c':text},text,solution_id='qualitative',provider=provider([c]),use_lean=False)
    event=result.telemetry['events'][0]
    assert event['evidence_present'] and event['literal_grounded']
    assert not event['canonicalized'] and not event['attributable']
    assert not result.potential_bridge.auditor.facts and result.assessment.score==0


def test_primary_resolved_obligations_are_not_sent():
    text='APQR: parallelogram'
    seen=[]
    def request(p,full,targets,config):
        seen.extend(json.loads(targets));return (),{'status':'completed'}
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='resolved',provider=request,use_lean=False)
    assert 'b.apqr' not in {t['obligation_id'] for t in seen}
    assert any(f.fact_id=='b.apqr' for f in result.primary_bridge.auditor.facts)
    with pytest.raises(ValueError,match='Unrequested'):
        sem.validate_response(json.dumps({'candidates':[candidate(text).model_dump()]}),seen)


def test_wire_full_source_allowlist_and_cache(monkeypatch):
    import openai
    seen=[]
    class Client:
        def __init__(self,**kwargs):self.responses=self
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def create(self,**kwargs):
            seen.append(kwargs)
            return SimpleNamespace(status='completed',output=[],output_text='{"candidates":[]}',model='fixture',id='r',usage=None)
    monkeypatch.setattr(openai,'OpenAI',Client);sem.request_candidates.cache_clear()
    targets=[t for t in mathematical_obligations('TME2026P4') if t['obligation_id']=='b.apqr']
    full='Texto sem item.\nAPQR é um paralelogramo.'
    args=('TME2026P4',full,json.dumps(targets),json.dumps(sem.configuration()))
    sem.request_candidates(*args);sem.request_candidates(*args)
    assert len(seen)==1
    wire=json.loads(seen[0]['input'][1]['content'])
    assert set(wire)=={'problem_id','statement','solution_text','target_obligations','source_lines'}
    assert wire['solution_text']==full
    for line in wire['source_lines']:
        assert full[line['source_start']:line['source_end']]==line['source_text']
    assert seen[0]['text']['format']['strict'] and not seen[0]['store']
    sem.request_candidates.cache_clear()


def test_wrong_offset_never_relocated_even_for_unique_quote():
    text='Introdução. APQR é um paralelogramo.';quote='APQR é um paralelogramo.'
    c=candidate(quote,full=text).model_copy(update={'source_start':0,'source_end':len(quote)})
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='badspan',provider=provider([c]),use_lean=False)
    assert result.telemetry['events'][0]['reason']=='exact_span_miss'
    assert not result.potential_bridge.auditor.facts


def test_full_source_visible_but_unmapped_evidence_cannot_be_rerouted():
    text='APQR é um paralelogramo.'
    result=run_shadow('TME2026P4',{},text,solution_id='unmapped',provider=provider([candidate(text)]),use_lean=False)
    event=result.telemetry['events'][0]
    assert event['literal_grounded'] and event['reason']=='input_mapping_miss'
    assert not result.potential_bridge.auditor.records
    result=run_shadow('TME2026P4',{'a':text},text,solution_id='wrongitem',provider=provider([candidate(text)]),use_lean=False)
    assert not result.potential_bridge.auditor.facts


def test_shadow_never_sends_semantic_facts_to_engine(monkeypatch):
    from confia_lean_auditor.rubric.pauta.engine import PautaEngine
    original=PautaEngine.evaluate;calls=[]
    def spy(self,config,evidence):
        calls.append(evidence)
        assert not any(s.startswith('semantic:') for e in evidence.obligations for s in e.source_claim_ids)
        return original(self,config,evidence)
    monkeypatch.setattr(PautaEngine,'evaluate',spy)
    text='APQR é um paralelogramo. Seu perímetro APQR é 2*((6-x)+x)=12.'
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='shadow',provider=provider(p4_candidates(text)),use_lean=False)
    assert len(calls)==1 and result.semantic_shadow and result.assessment.score==0
    assert any(f.fact_id=='b.perimeter_apqr' and f.verification.status=='verified' for f in result.potential_bridge.auditor.facts)
    with pytest.raises(ValueError):activate_shadow(result)
    monkeypatch.setattr(PautaEngine,'evaluate',original)
    assert activate_shadow(result,gate_passed=True).score==6


@pytest.mark.parametrize('prefix',[
    'Não é verdade que ', 'Suponha que ', 'Tentei: ', 'João disse que ',
    'A solução de João diz ', 'Talvez ', 'Na página 12, ',
])
def test_context_controls_even_if_model_lies_about_assertion(prefix):
    text=prefix+'APQR é um paralelogramo. Seu perímetro APQR é 2*((6-x)+x)=12.'
    if prefix=='Tentei: ':text+=' Mas está errado.'
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='control',provider=provider(p4_candidates(text)),use_lean=False)
    assert not result.potential_bridge.auditor.facts
    assert activate_shadow(result,gate_passed=True).score==0


@pytest.mark.parametrize('mode',['negated','hypothetical','rejected','quoted','uncertain'])
def test_non_asserted_modes_never_produce_facts(mode):
    text='APQR é um paralelogramo.'
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='mode',provider=provider([candidate(text,mode=mode)]),use_lean=False)
    assert not result.potential_bridge.auditor.facts


def test_conflicting_values_fail_closed():
    text='O perímetro de APQR é 12. Depois concluí que o perímetro de APQR é 14.'
    cs=[candidate(text,'b.perimeter_apqr','perimeter_apqr',str(n),'math').model_copy(update={'candidate_id':str(n)}) for n in (12,14)]
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='conflict',provider=provider(cs),use_lean=False)
    assert not result.potential_bridge.auditor.facts
    assert all(not e['attributable'] for e in result.telemetry['events'])


def test_dedup_preserves_deterministic_record_and_observes_confirmation():
    text='APQR: parallelogram';targets=mathematical_obligations('TME2026P4')
    from confia_lean_auditor.student_claims.tme2_p4_digital import collect_tme2_p4_digital
    with legacy.supplement_scope(lambda p,s,r,d,**kw:(tuple(d),None)):
        primary=collect_tme2_p4_digital({'b':text})
    session=sem.ProjectionSession('TME2026P4',text,targets,[candidate(text)],{'status':'fixture'})
    records,telemetry=session('TME2026P4',primary.source_text,primary.item_ranges,primary.records)
    assert records==primary.records and telemetry['events'][0]['deduplicated']
    assert telemetry['events'][0]['retained_record_id']==primary.records[0].record_id


def test_repeated_candidates_have_one_record():
    text='APQR é um paralelogramo.';c=candidate(text)
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='repeat',provider=provider([c,c]),use_lean=False)
    assert len(result.potential_bridge.auditor.facts)==1


@pytest.mark.parametrize('lhs,expected',[('2*((6-x)+x)','verified'),('2*((6-x)+x)+1','refuted')])
def test_existing_lean_checks_exact_written_proposition(lhs,expected):
    text=f'APQR é um paralelogramo. Seu perímetro APQR é {lhs}=12.'
    cs=[candidate(text),candidate(text,'b.perimeter_apqr','perimeter_apqr',lhs+'=12','math')]
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='formal',provider=provider(cs),use_lean=True)
    fact=next(f for f in result.potential_bridge.auditor.facts if f.fact_id=='b.perimeter_apqr')
    assert fact.verification.status==expected and fact.verification_source=='student_lean'
    assert result.assessment.score==0
    assert activate_shadow(result,gate_passed=True).score==(6 if expected=='verified' else 0)


def test_provider_failure_keeps_baseline_and_schema_failure_closed(monkeypatch):
    text='APQR: parallelogram'
    result=run_shadow('TME2026P4',{'b':text},text,solution_id='offline',provider=lambda *a:((),{'status':'unavailable'}),use_lean=False)
    assert result.potential_bridge.evidence==result.primary_bridge.evidence
    assert result.assessment.score==0
    bad=candidate('APQR é paralelogramo.','b.apqr','perimeter_apqr','12','math')
    with pytest.raises(ValueError):
        sem.validate_response(json.dumps({'candidates':[bad.model_dump()]}),mathematical_obligations('TME2026P4'))


def test_unicode_source_never_changes():
    full='731 − 137 = 594'
    c=candidate(full,'a.result_594','expression','731 - 137 = 594','math')
    session=sem.ProjectionSession('TME2_P1_PILOT',full,mathematical_obligations('TME2026P1'),[c],{})
    records,_=session('TME2_P1_PILOT','[a]\n'+full+'\n\n',{'a':(4,4+len(full))},())
    assert records[0].source.raw_text==full and records[0].source.attributable


def test_projection_revalidated_before_checker():
    from dataclasses import replace
    from confia_lean_auditor.student_claims.tme2_p4_digital import collect_tme2_p4_digital
    from confia_lean_auditor.lean.student_claim_checkers.tme2_p4 import verify_tme2_p4_digital
    text='APQR é um paralelogramo.'
    session=sem.ProjectionSession('TME2026P4',text,mathematical_obligations('TME2026P4'),[candidate(text)],{})
    with legacy.supplement_scope(session):
        digital=collect_tme2_p4_digital({'b':text})
        forged=digital.records[0].model_copy(update={'canonicalization_reason':'forged'})
        with pytest.raises(ValueError):verify_tme2_p4_digital(replace(digital,records=(forged,)),'tamper',use_lean=False)
