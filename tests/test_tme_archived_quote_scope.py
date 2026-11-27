"""Archived GPT replay is separate from explicitly labelled synthetic controls.

Never call AuditService, a real provider or Lean for the archived case. Restore
only pre-fallback obligation snapshots from their persisted requests and replay
unaltered archived responses through current validation and the original pauta.
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from confia_lean_auditor.semantic_policy import tme
from confia_lean_auditor.semantic_policy.minimal_review import digest, obtain_review
from confia_lean_auditor.student_claims.sufficiency_requirements import CROSS_ITEM
from confia_lean_auditor.tme.audit_models import TMEAuditResult
from confia_lean_auditor.tme.accepted_audit import pauta_for
from confia_lean_auditor.tme.registry import audit_tme
from test_tme_minimal_functional import public_score, text_of
from test_tme_accepted_integration import FULL, solution_for

FIXTURE = Path(__file__).parent/'fixtures/tme_p1_archived_quote_scope'
TARGETS = ('c.no_extraneous_values', 'd.middle_choices')


def archived():
    old = TMEAuditResult.model_validate_json((FIXTURE/'audit.json').read_text())
    traces = {e.obligation_id:e.metadata['semantic_fallback'] for e in old.bridge.evidence.obligations
              if 'semantic_fallback' in e.metadata}
    return old, traces, (FIXTURE/'solution.txt').read_text(), json.loads((FIXTURE/'input_mapping.json').read_text())['solution']


class ArchivedProvider:
    def __init__(self, traces):
        self.traces, self.calls = traces, []

    def __call__(self, request):
        oid = request['criterion']['id']
        original = self.traces[oid]
        assert oid not in self.calls, 'No double adjudication'
        # The source, criterion, rubric and mathematical request remain the same;
        # only the evidence-scope integration metadata has been repaired.
        for key in ('solution','criterion','rubric','statement'):
            assert request[key] == original['request'][key]
        assert digest(original['response']) == original['response_sha256']
        self.calls.append(oid)
        self.metadata = dict(offline_replay=True, archived_provider=original['provider'],
                             archived_response_sha256=original['response_sha256'])
        return copy.deepcopy(original['response'])


def replay(*, resume=False):
    old, traces, solution, items = archived()
    bridge = old.bridge
    if not resume:
        rows = tuple(type(e).model_validate(traces[e.obligation_id]['request']['checks'])
                     if e.obligation_id in traces else e for e in bridge.evidence.obligations)
        bridge = bridge.model_copy(update={'evidence':bridge.evidence.model_copy(update={'obligations':rows})})
    provider = ArchivedProvider(traces)
    updated, assessment = tme.apply(old.pauta, bridge, solution, next(iter(traces.values()))['request']['statement'],
                                   item_sources=items, provider=provider)
    return old, updated, assessment, provider


def test_exact_archived_failures_are_scope_errors_not_invalid_quotes_or_provider_errors():
    old, traces, solution, items = archived()
    manifest = json.loads((FIXTURE/'source_manifest.json').read_text())
    for name, expected in manifest['files'].items():
        assert hashlib.sha256((FIXTURE/name).read_bytes()).hexdigest() == expected
    assert len(traces)==13 and old.score is None
    assert [i.points_awarded for i in old.assessment.items][:3]==[2,5,4]
    for oid in TARGETS:
        trace = traces[oid]
        assert trace['error_type']=='QuoteOutsideAuthorizedItem'
        assert trace['provider']['status']=='completed' and trace['response']['decision']=='met'
        assert digest(trace['request'])==trace['request_sha256']
        assert hashlib.sha256(solution.encode()).hexdigest()==trace['source_sha256']
        assert all(q in solution for q in trace['response']['quotes'])
        validated = obtain_review(lambda _:copy.deepcopy(trace['response']), trace['request'])
        assert validated['decision']=='met' and not validated.get('error_type')
        assert not tme.quotes_in_context(validated, trace['request']['accepted_item_evidence'])
        contexts=tme.accepted_contexts(old.bridge, solution, items)
        _, permitted=tme.obligation_contexts(old.pauta, contexts, oid)
        assert {c['item_id'] for c in permitted}=={oid[0],'b'}
        assert tme.quotes_in_context(validated, permitted)


def test_unmodified_archived_gpt_responses_produce_seventeen_with_original_pauta():
    old, updated, a, provider = replay()
    assert len(provider.calls)==13 and public_score(a)==17
    assert [i.points_awarded for i in a.items]==[2,5,4,6]
    assert all(i.status=='decided' for i in a.items)
    assert updated.auditor==old.bridge.auditor
    assert not any(e.status=='technical_error' for e in updated.evidence.obligations)
    _, traces, _, _ = archived()
    for before, after in zip(old.bridge.evidence.obligations, updated.evidence.obligations):
        if before.status in {'supported','refuted'}:
            assert before.status==after.status
        if after.obligation_id in traces:
            trace=after.metadata['semantic_fallback']
            assert trace['response']==traces[after.obligation_id]['response']
            assert trace['provider']['offline_replay'] and not trace.get('error_type')
            assert not trace['formal_certification']
    domain=next(e for e in updated.evidence.obligations if e.obligation_id=='c.difference_domain')
    assert domain.status=='refuted'  # Original PautaEngine vocabulary: criterion unmet.
    assert domain.metadata['semantic_fallback']['decision']=='not_met'
    assert 'Justifica' in traces['c.difference_domain']['request']['criterion']['description']
    assert 'afirma corretamente' in domain.metadata['semantic_fallback']['response']['justification']
    assert a.items[2].children[2].selected_band=='c.list.one_error'
    result=old.model_copy(update={'bridge':updated,'assessment':a})
    assert TMEAuditResult.model_validate_json(result.model_dump_json()).score==17


def test_old_scope_reproduces_null_and_two_technical_errors(monkeypatch):
    old_scope={k:v for k,v in CROSS_ITEM['TME2_P1_PILOT'].items() if k not in TARGETS}
    monkeypatch.setitem(CROSS_ITEM,'TME2_P1_PILOT',old_scope)
    old, updated, a, provider = replay()
    assert public_score(a) is None and len(provider.calls)==13
    assert {e.obligation_id for e in updated.evidence.obligations if e.status=='technical_error'}==set(TARGETS)
    assert [i.points_awarded for i in a.items]==[2,5,4,None]


def test_resume_only_pending_item_preserves_every_conclusive_decision():
    old, updated, a, provider = replay(resume=True)
    assert public_score(a)==17 and provider.calls==['d.middle_choices']
    for before, after in zip(old.bridge.evidence.obligations, updated.evidence.obligations):
        if before.obligation_id!='d.middle_choices':assert before==after
    # The historic error in c belongs to a discarded branch and needs no new call.
    assert next(e for e in updated.evidence.obligations if e.obligation_id==TARGETS[0]).status=='technical_error'
    _,traces,solution,items=archived()
    again,result=tme.apply(old.pauta,updated,solution,next(iter(traces.values()))['request']['statement'],item_sources=items,
                          provider=lambda _:pytest.fail('Already decided items'))
    assert again==updated and result==a


@pytest.mark.parametrize('broken_scope',[False,True])
def test_complete_list_also_needs_cross_item_context(broken_scope,monkeypatch):
    # SYNTHETIC control: a complete existing fixture with only its list-validity
    # verification unavailable, and an explicitly simulated two-item opinion.
    items=solution_for(1,FULL[1]);config=pauta_for('TME2026P1')
    b,_=audit_tme('TME2026P1',items,use_lean=False)
    oid='c.no_extraneous_values'
    rows=tuple(e.model_copy(update={'status':'indeterminate'}) if e.obligation_id==oid else e for e in b.evidence.obligations)
    b=b.model_copy(update={'evidence':b.evidence.model_copy(update={'obligations':rows})})
    if broken_scope:
        monkeypatch.setitem(CROSS_ITEM,'TME2_P1_PILOT',{k:v for k,v in CROSS_ITEM['TME2_P1_PILOT'].items() if k!=oid})
    calls=[]
    def simulated(request):
        calls.append(request['criterion']['id'])
        return dict(decision='met',justification='CONTROLE SIMULADO: lista completa dos oito múltiplos de 99 derivados em b.',quotes=[items['c'],items['b']])
    _,a=tme.apply(config,b,text_of(items),'Controle de lista completa.',item_sources=items,provider=simulated)
    assert calls==[oid] and public_score(a)==(None if broken_scope else 20)


@pytest.mark.parametrize('oid',TARGETS)
def test_scope_remains_narrow_and_cannot_fill_missing_target_item(oid):
    old,traces,solution,items=archived()
    contexts=tme.accepted_contexts(old.bridge,solution,items)
    _,permitted=tme.obligation_contexts(old.pauta,contexts,oid)
    assert not tme.quotes_in_context({'quotes':[{'text':items['a']}]},permitted)
    assert not tme.quotes_in_context({'quotes':[{'text':'citação inventada'}]},permitted)
    contexts.pop(oid[0])
    assert tme.obligation_contexts(old.pauta,contexts,oid)[1]==[]
