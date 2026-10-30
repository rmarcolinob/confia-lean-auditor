"""Real V3 evidence failures and live HTTP envelopes, replayed without network."""
import copy
import json
from pathlib import Path

import pytest
from confia_lean_auditor.rubric import secondary_adjudicator as s
from confia_lean_auditor.rubric.secondary_evidence import source_quote
from tests.test_secondary_adjudicator_contract import payload, decision, fake_client
from tests.secondary_selection_helpers import selection

FIXTURES=Path(__file__).parent/'fixtures/secondary_live_02'


@pytest.mark.parametrize('quote,source',[
    ('a=-1 e b=3.', 'a=-1\n e\tb=3.'),
    ('a=-1 e b=3.', 'a=-1\u00a0e b=3.'),
    ('conclusa\u0303o', 'conclusão'),
    ('conclusão', 'conclusa\u0303o'),
    ('“a=-1 e b=3.”', 'Logo a=-1 e b=3.'),
    ('"a=-1 e b=3."', 'Logo a=-1 e b=3.'),
    ('x \\leq y', 'x\n\\leq\ty'),
])
def test_presentation_only_returns_original_source(quote,source):
    actual=source_quote(quote,source)
    assert actual is not None and actual in source


@pytest.mark.parametrize('quote,source',[
    ('a=1', 'a=-1'), ('a=2', 'a=3'), ('x<2', 'x>2'),
    ('e injetora', 'não é injetora'), ('x=y', 'x≠y'),
    ('x=2', 'x²=2'), ('cafe', 'café'),
    ('positivos e distintos.', 'positivos e distintos, e verifico que'),
    ('x <= y', 'x \\leq y'), ('a=b', 'A=b'),
    ('x y', 'xy'), ('x*y', 'x×y'),
])
def test_no_mathematical_or_punctuation_repair(quote,source):
    assert source_quote(quote,source) is None


def test_wire_schema_closes_observed_empty_evidence_gap():
    p=payload();schema=s.legacy_text_schema(p['pending_criteria'])
    good=decision(p,'deny');rule=schema['properties']['final_answer']['properties']['evidence']
    assert rule['minItems']==1 and rule['maxItems']==3
    assert rule['items']['minLength']==1 and rule['items']['maxLength']==800 and rule['items']['pattern']==r'\S'
    for evidence in ([], [''], [' '], ['x'*801], ['a']*4):
        bad=copy.deepcopy(good);bad['final_answer']['evidence']=evidence
        with pytest.raises(s.AdjudicationError):s.validate_decisions(bad,p)
    # Source matching is deliberately a local semantic gate, not a JSON promise.
    bad=copy.deepcopy(good);bad['final_answer']['evidence']=['invented quote']
    with pytest.raises(s.AdjudicationError):s.validate_decisions(bad,p)


def test_real_v3_empty_arrays_remain_invalid_and_now_violate_wire_schema():
    rows=json.loads((FIXTURES/'v3_observed.json').read_text())
    observed=[r for r in rows if r['complete_json_available'] and r['v3_root_cause']=='SCHEMA_MISMATCH']
    assert observed
    for row in observed:
        raw=json.loads(row['excerpt']);cid=row['criterion_id'];obj=raw[cid]
        p=payload();p['pending_criteria'][0]['id']=cid
        p['pending_criteria'][0]['description']=obj['rationale'].split('«',1)[1].split('»',1)[0]
        d={cid:obj}
        rule=s.legacy_text_schema(p['pending_criteria'])['properties'][cid]['properties']['evidence']
        assert len(obj['evidence']) < rule['minItems']
        with pytest.raises(s.AdjudicationError) as error:s.validate_decisions(d,p)
        assert error.value.reason=='empty_array'


def test_literal_source_is_stored_after_presentation_recovery():
    p=payload();p['solution_text']='Logo a=-1\n e b=3.';d=decision(p)
    d['final_answer']['evidence']=['“a=-1 e b=3.”']
    s.validate_decisions(d,p)
    assert d['final_answer']['evidence']==['a=-1\n e b=3.']


def test_failed_batch_does_not_partially_mutate_candidate():
    p=payload();p['pending_criteria'].append(dict(p['pending_criteria'][0],id='other'))
    d=decision(p);d['final_answer']['evidence']=['"Logo a=-1 e b=3."'];d['other']['evidence']=[]
    before=copy.deepcopy(d)
    with pytest.raises(s.AdjudicationError):s.validate_decisions(d,p)
    assert d==before


def test_specific_retry_preserves_request_and_rubric(monkeypatch):
    p=payload();bad=selection(p);bad['final_answer']['evidence_ids']=[]
    calls,_=fake_client(monkeypatch,[bad,selection(p,'deny')]);_,meta=s.adjudicate(p)
    assert meta['retry_count']==1
    correction=calls[1]['instructions'][len(calls[0]['instructions']):]
    assert all(x in correction for x in ['final_answer','evidence_ids','evidence_required','INSUFFICIENT_EVIDENCE'])
    assert calls[0]['input']==calls[1]['input'] and calls[0]['text']==calls[1]['text']
    first=meta['attempt_details'][0]
    assert first['parsed_candidate']==bad and first['validation_errors'][0]['reason']=='evidence_required'
    assert first['schema_version']==s.SCHEMA_VERSION and first['retry_count']==0


def test_redaction_preserves_newlines_math_and_duplicate_keys(monkeypatch):
    raw='{"x":{"evidence":["são:\\n1 = (1,0)"]},"x":{"evidence":[]}}'
    cleaned=s.redacted_json_text(raw)
    assert cleaned.count('"x"')==2 and '[REDACTED_PATH]' not in cleaned
    assert json.loads(cleaned)['x']['evidence']==[]
    monkeypatch.setenv('TEST_SECRET','private-test-secret')
    raw=json.dumps({'list':[{'text':'private-test-secret'}, {'api_key':{'nested':'unknown-credential'}}],
                    'path':'/Users/alice/private','url':'https://user:password@example.com'})
    cleaned=s.redacted_json_text(raw)
    assert all(x not in cleaned for x in ['private-test-secret','unknown-credential','/Users/alice','user:password'])
    assert isinstance(json.loads(cleaned)['list'][0],dict)


def test_http_output_text_redaction_preserves_escaped_newlines():
    raw=json.dumps({'evidence':['são:\n1 = (1,0)']},ensure_ascii=False)
    body={'output':[{'content':[{'type':'output_text','text':raw}]}]}
    clean=s.trace_data(body)
    assert json.loads(clean['output'][0]['content'][0]['text'])['evidence']==['são:\n1 = (1,0)']


@pytest.mark.parametrize('case_id',['ITA2025Q1_S001_L04','ITA2025Q1_S016_L01','ITA2025Q4_S003_L04'])
def test_sdk_uses_real_live_http_response_shape_offline(monkeypatch,case_id):
    import httpx,openai
    fixture=json.loads((FIXTURES/(case_id+'.json')).read_text())
    replies=fixture['exchanges'];seen=[];real_client=openai.OpenAI
    def transport(request):
        index=len(seen);seen.append(json.loads(request.content))
        response=replies[index]
        assert request.url.path=='/v1/responses'
        return httpx.Response(response['status_code'],json=response['response_body'])
    def factory(**kwargs):
        return real_client(api_key='offline-fake-key',base_url='https://offline.invalid/v1',
                           http_client=httpx.Client(transport=httpx.MockTransport(transport)),**kwargs)
    monkeypatch.setenv('OPENAI_API_KEY','offline-fake-key');monkeypatch.setattr(openai,'OpenAI',factory)
    # Decode historical envelopes with the real SDK, then apply the retained
    # textual reader. Do not feed the obsolete provider contract into current API.
    p=json.loads(replies[0]['request_body']['input'])
    for exchange in replies:
        with factory(timeout=45,max_retries=0) as client:
            response=client.responses.create(**exchange['request_body'])
        candidate=s.parse_response(response.output_text)
        if case_id=='ITA2025Q1_S001_L04':
            s.validate_decisions(candidate,p)
            assert all(e in p['solution_text'] for d in candidate.values() for e in d['evidence'])
        else:
            with pytest.raises(s.AdjudicationError) as failure:s.validate_decisions(candidate,p)
            assert failure.value.reason=='quote_not_found'
        assert type(response).__name__=='Response'
    assert len(seen)==len(replies)
