"""The future smoke gate is exercised with local transports only."""
import importlib.util
import json
from pathlib import Path
import httpx
import pytest

spec=importlib.util.spec_from_file_location('rc1smoke',Path(__file__).resolve().parents[1]/'scripts/evaluation/dynamic_rc1_smoke.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def request(group='grader',criteria=2,extra=None):
    payload=dict(stage=group,rubric=dict(criteria=[{}]*criteria))
    body=dict(model='gpt-6.1-sol',store=False,max_output_tokens=4000,reasoning=dict(effort='medium'),
        input=[dict(role='system',content='Test only'),dict(role='user',content=json.dumps(payload))],
        text=dict(format=dict(name='dynamic_credit_decision')))
    body.update(extra or {})
    return httpx.Request('POST','https://api.openai.com/v1/responses',json=body,headers={'Authorization':'Bearer synthetic-not-a-secret'})

def response(client,req,**kwargs):
    return httpx.Response(200,request=req,json=dict(id='synthetic',status='completed',model='gpt-6.1-sol',service_tier='default',usage=dict(input_tokens=100,output_tokens=20)))

def test_plan_is_zero_call_and_bounded():
    p=m.plan();assert p['api_calls']==0 and p['max_calls']==22
    assert p['maximum_reserved_usd']=='5.25' and p['cap_usd']=='6.00'

def test_request_receipt_and_usage_preserved_without_headers(tmp_path):
    gate=m.BudgetGate(tmp_path);req=request();out=gate.send(response,None,req)
    assert out.json()['id']=='synthetic'
    rows=[json.loads(s) for s in gate.ledger.read_text().splitlines()]
    assert rows[1]['event']=='reserved' and rows[2]['usage']['input_tokens']==100
    assert rows[2]['returned_model']=='gpt-6.1-sol'
    assert 'synthetic-not-a-secret' not in gate.ledger.read_text()
    with pytest.raises(m.StopSmoke):m.BudgetGate(tmp_path)

@pytest.mark.parametrize('bad',[request(criteria=5),request(extra=dict(model='other')),request(extra=dict(tools=[{}])),request(extra=dict(input=[dict(role='user',content='x'*70000)]))])
def test_invalid_request_stops_before_transport(tmp_path,bad):
    gate=m.BudgetGate(tmp_path);calls=[]
    with pytest.raises(m.StopSmoke):gate.send(lambda *a,**k:calls.append(1),None,bad)
    assert not calls and gate.halted and gate.used==0

def test_cap_and_stop_file_prevent_any_further_call(tmp_path):
    gate=m.BudgetGate(tmp_path)
    for _ in range(8):gate.send(response,None,request())
    with pytest.raises(m.StopSmoke):gate.send(response,None,request())
    assert gate.counts['grader']==8
    other=m.BudgetGate(tmp_path/'other');(other.root/'STOP').touch()
    with pytest.raises(m.StopSmoke):other.send(response,None,request())
    assert other.used==0

def test_failure_consumes_reservation_and_halts_no_retry(tmp_path):
    gate=m.BudgetGate(tmp_path);calls=[]
    def failed(*a,**k):calls.append(1);raise TimeoutError('must not log secret headers')
    for _ in range(2):
        with pytest.raises(m.StopSmoke):gate.send(failed,None,request())
    assert len(calls)==1 and gate.used==m.reservation('grader')
    assert 'secret headers' not in gate.ledger.read_text()

def test_missing_usage_blocks_later_calls(tmp_path):
    gate=m.BudgetGate(tmp_path)
    with pytest.raises(m.StopSmoke):gate.send(lambda _,r,**k:httpx.Response(200,request=r,json=dict(status='completed')),None,request())
    assert gate.halted and gate.counts['grader']==1


def test_financial_cap_blocks_before_transport_even_with_calls_remaining(tmp_path):
    gate=m.BudgetGate(tmp_path);gate.used=m.Decimal('5.90');calls=[]
    with pytest.raises(m.StopSmoke):gate.send(lambda *a,**k:calls.append(1),None,request())
    assert not calls and gate.counts['grader']==0 and gate.used==m.Decimal('5.90')
