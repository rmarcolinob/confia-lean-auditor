"""ID selection, source provenance, scoring isolation and historical compatibility."""
import copy,json
from pathlib import Path
import pytest
from confia_lean_auditor.rubric import secondary_adjudicator as s
from confia_lean_auditor.rubric.secondary_candidates import with_candidates,MAX_CANDIDATES,MAX_CRITERION_TEXT,candidate_binding
from tests.secondary_selection_helpers import selection
from tests.test_secondary_adjudicator_contract import payload,fake_client

def prepared():return with_candidates(payload(),s.redact)

@pytest.mark.parametrize('kind,reason',[('award','SATISFIES_CRITERION'),('deny','INSUFFICIENT_EVIDENCE'),('deny','CONTRADICTS_CRITERION'),('deny','INCOMPLETE_FOR_CRITERION')])
def test_valid_decisions_resolve_only_ids_from_source(kind,reason):
    p=prepared();d=selection(p,kind,reason);s.validate_selections(d,p);resolved=s.resolve_selections(d,p)
    s.validate_decisions(resolved,p)
    row=resolved['final_answer'];assert all(e in p['solution_text'] for e in row['evidence'])
    assert bool(row['evidence'])==(reason!='INSUFFICIENT_EVIDENCE')

@pytest.mark.parametrize('mutation,category,reason',[
    (lambda d:d['final_answer'].update(evidence_ids=[]),'invalid_evidence_ids','evidence_required'),
    (lambda d:d['final_answer'].update(evidence_ids=['E999']),'invalid_evidence_ids','unknown_id'),
    (lambda d:d['final_answer'].update(evidence_ids=['E1_1','E1_1']),'invalid_evidence_ids','duplicate_ids'),
    (lambda d:d['final_answer'].update(evidence_ids=[False]),'invalid_evidence_ids',None),
    (lambda d:d['final_answer'].update(suggested_points=1),'invalid_points',None),
    (lambda d:d['final_answer'].update(suggested_points=True),'invalid_points',None),
    (lambda d:d['final_answer'].update(decision='deny'),'decision_points_conflict',None),
    (lambda d:d['final_answer'].update(reason_code='UNRESTRICTED'),'incoherent_reason',None),
    (lambda d:d['final_answer'].update(rationale='Falta conclusão formal.'),'unauthorized_rationale',None),
    (lambda d:d['final_answer'].update(evidence=['invented quote']),'schema_failure',None),
    (lambda d:d.update(other=d.pop('final_answer')),'wrong_criterion_id',None),
])
def test_invalid_model_selections_fail_closed(mutation,category,reason):
    p=prepared();d=selection(p);mutation(d)
    with pytest.raises(s.AdjudicationError) as error:s.validate_selections(d,p)
    assert error.value.category==category and error.value.reason==reason

@pytest.mark.parametrize('reason',['CONTRADICTS_CRITERION','INCOMPLETE_FOR_CRITERION'])
def test_deny_without_ids_requires_explicit_insufficient(reason):
    p=prepared();d=selection(p,'deny',reason);d['final_answer']['evidence_ids']=[]
    with pytest.raises(s.AdjudicationError) as e:s.validate_selections(d,p)
    assert e.value.reason=='evidence_required'

@pytest.mark.parametrize('field,value',[('source_start',1),('source_end',1),('source_text','fabricated'),('grounding_status','unresolved')])
def test_candidate_binding_tampering_is_rejected_before_provider(monkeypatch,field,value):
    p=prepared();p['pending_criteria'][0]['candidate_evidence'][0][field]=value
    seen,_=fake_client(monkeypatch,[])
    with pytest.raises(s.AdjudicationError) as e:s.adjudicate(p)
    assert e.value.category=='invalid_candidate' and not seen

def test_ids_cannot_cross_criteria():
    p=payload();p['pending_criteria'].append(dict(p['pending_criteria'][0],id='other'));p=with_candidates(p,s.redact)
    d=selection(p);d['final_answer']['evidence_ids']=d['other']['evidence_ids']
    with pytest.raises(s.AdjudicationError) as e:s.validate_selections(d,p)
    assert e.value.reason=='unknown_id'

def test_resolved_text_cannot_be_substituted_after_selection():
    p=prepared();d=s.resolve_selections(selection(p),p);d['final_answer']['evidence']=['paraphrase']
    with pytest.raises(s.AdjudicationError) as e:s.validate_decisions(d,p)
    assert e.value.category=='resolved_evidence_mismatch'

def test_current_contract_never_matches_generated_text(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Text matching used by ID contract')
    monkeypatch.setattr(s,'resolve_evidence',forbidden)
    fake_client(monkeypatch,[lambda call:selection(json.loads(call['input']))])
    d,m=s.adjudicate(payload());assert m['validation_status']=='accepted'
    assert d['final_answer']['evidence_ids'] and d['final_answer']['evidence']

def test_duplicates_in_candidate_catalog_are_rejected():
    p=prepared();p['pending_criteria'][0]['candidate_evidence']*=2
    with pytest.raises(s.AdjudicationError) as e:s.validate_selections(selection(p),p)
    assert e.value.category=='invalid_candidate'

def test_current_schema_and_result_reject_free_text_provider_reply(monkeypatch):
    from tests.test_secondary_adjudicator_contract import decision
    p=payload();fake_client(monkeypatch,[decision(p),decision(p)])
    with pytest.raises(s.AdjudicationError) as e:s.adjudicate(p)
    assert e.value.diagnostics['retry_count']==1
    assert all(a['validation_error']['category']=='schema_failure' for a in e.value.diagnostics['attempt_details'])

def test_no_candidates_schema_allows_only_deny_insufficient():
    p=payload();p['solution_text']='x'*900;p=with_candidates(p,s.redact)
    assert not p['pending_criteria'][0]['candidate_evidence']
    branches=s.response_schema(p['pending_criteria'])['properties']['final_answer']['anyOf'];assert len(branches)==1
    rule=branches[0]['properties'];assert rule['decision']['enum']==['deny'] and rule['evidence_ids']['maxItems']==0
    d=selection(p,'deny');s.validate_selections(d,p)
    with pytest.raises(s.AdjudicationError):s.validate_selections(selection(p),p)

def test_bounded_relevant_candidates_and_deterministic_ids():
    p=payload();p['solution_text']='\n\n'.join(['Trecho de contexto genérico.']*100+['Logo a=-1 e b=3.'])
    a=with_candidates(p,s.redact);b=with_candidates(p,s.redact);assert a==b
    c=a['pending_criteria'][0]['candidate_evidence'];assert len(c)<=MAX_CANDIDATES
    assert sum(len(x['source_text']) for x in c)<=MAX_CRITERION_TEXT
    assert all(candidate_binding(x,p['solution_text']) for x in c)

def test_claim_span_priority_and_local_link_not_on_wire():
    p=payload();p['pending_criteria'][0]['candidate_student_checks']=[{'id':'claim-local','status':'verified',
      'grounding':{'status':'grounded','source_start':5,'source_end':9,'source_text':'a=-1'}}]
    p=with_candidates(p,s.redact);c=p['pending_criteria'][0]['candidate_evidence'][0]
    assert c['source_kind']=='grounded_claim' and c['claim_id']=='claim-local'
    from confia_lean_auditor.rubric.secondary_candidates import wire_candidates
    assert 'claim_id' not in wire_candidates([c])[0]

def test_only_candidate_source_and_no_paths_are_sent(monkeypatch):
    p=payload();p['solution_text']+='\napi_key=sk-exampleprivatecredential001 /Users/alice/private'
    seen,_=fake_client(monkeypatch,[lambda call:selection(json.loads(call['input']))]);d,m=s.adjudicate(p)
    wire=json.loads(seen[0]['input']);assert 'solution_text' not in wire
    assert all(k not in seen[0]['input'] for k in ['sk-exampleprivatecredential001','/Users/alice','candidate_student_checks','grounded_claims'])
    assert m['criteria'][0]['candidate_evidence'] and m['criteria'][0]['selected_evidence_ids']
    assert m['criteria'][0]['resolved_evidence_text']==d['final_answer']['evidence']

def test_deny_empty_keeps_indeterminate_and_coverage(monkeypatch):
    from tests.test_score_policy import inputs
    from confia_lean_auditor.rubric.scoring_policy import apply_scoring_policy
    data=inputs(['supported','indeterminate','refuted']);seen,_=fake_client(monkeypatch,[lambda call:selection(json.loads(call['input']),'deny')])
    r=apply_scoring_policy(**data);assert r.score==2 and r.coverage==pytest.approx(2/3)
    assert [i.mathematical_status for i in r.items]==['supported','indeterminate','refuted']
    assert r.items[1].scoring_evidence==[] and r.items[1].scoring_basis=='secondary_adjudication'
    assert r.items[1].points is None and r.items[1].suggested_points==0
    assert [c['id'] for c in json.loads(seen[0]['input'])['pending_criteria']]==['c1']

@pytest.mark.parametrize('schema_version', ['secondary-schema-v2', 'secondary-schema-v3'])
def test_historical_artifacts_remain_readable_without_id_fabrication(schema_version):
    from confia_lean_auditor.core.schemas import AuditResponse
    fixture = Path(__file__).parent / 'fixtures/secondary_evidence_ids/legacy_without_evidence_ids.json'
    raw = json.loads(fixture.read_text(encoding='utf-8'))
    legacy = raw['rubric_assessment']['secondary_adjudication']
    legacy['schema_version'] = schema_version
    before = copy.deepcopy(raw)

    # Both historical schemas used textual evidence, with no candidate/selection IDs.
    d = AuditResponse.model_validate(raw)
    trace = s.artifact_trace(d.rubric_assessment)
    assert trace['schema_version'] == schema_version
    assert d.model_dump()['rubric_assessment']['secondary_adjudication'] == legacy
    rows = {c['criterion_id']: c for c in trace['criteria']}
    assert set(rows) == {'first_pass', 'legacy_award'}
    assert rows['legacy_award'] == legacy['criteria'][0]
    assert rows['legacy_award']['evidence'] == ['x = 2.']
    assert rows['first_pass']['reason'] == 'first_pass_decided'
    assert all(
        field not in c
        for c in trace['criteria']
        for field in ('evidence_id', 'evidence_ids', 'selected_evidence_ids', 'candidate_evidence')
    )
    assert raw == before


@pytest.mark.parametrize('cid',['ITA2025Q1_S001_L04','ITA2025Q1_S016_L01','ITA2025Q4_S003_L04'])
def test_actual_id_contract_http_envelope_through_sdk_offline(monkeypatch,cid):
    import httpx,openai
    fixture=json.loads((Path(__file__).parent/'fixtures/secondary_evidence_03'/f'{cid}.json').read_text())
    exchanges=fixture['exchanges'];seen=[];real_client=openai.OpenAI
    def transport(request):
        entry=exchanges[len(seen)];seen.append(json.loads(request.content))
        assert request.url.host=='offline.invalid'
        assert json.loads(seen[-1]['input'])==json.loads(entry['request_body']['input'])
        return httpx.Response(entry['status_code'],json=entry['response_body'])
    def factory(**kwargs):
        return real_client(api_key='offline-only',base_url='https://offline.invalid/v1',
            http_client=httpx.Client(transport=httpx.MockTransport(transport)),**kwargs)
    monkeypatch.setenv('OPENAI_API_KEY','offline-only');monkeypatch.setattr(openai,'OpenAI',factory)
    p=json.loads(exchanges[0]['request_body']['input']);p['solution_text']=fixture['source_text']
    result,meta=s.adjudicate(p)
    assert meta['validation_status']=='accepted' and meta['retry_count']==0 and len(seen)==1
    for c in meta['criteria']:
        by_id={e['evidence_id']:e for e in c['candidate_evidence']}
        assert c['resolved_evidence_text']==[by_id[e]['source_text'] for e in c['selected_evidence_ids']]
        assert all(t in fixture['source_text'] for t in c['resolved_evidence_text'])
        if not c['selected_evidence_ids']:
            assert c['decision']=='deny' and c['reason_code']=='INSUFFICIENT_EVIDENCE'
    assert all('evidence_ids' in d for d in result.values())
