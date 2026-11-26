#!/usr/bin/env python3
"""Opt-in smoke instrumentation. Default: print plan, no server or provider call.

Does not grade, change prompts, approve readings, or modify application contracts.
The gate reserves a pessimistic token allowance BEFORE each outbound request.
"""
import argparse
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
CAP = Decimal('6.00')
INPUT_RESERVE = 100000
MAX_JSON_BYTES = 65536
LIMITS = {'prepare': 2, 'rubric': 2, 'help2': 1, 'grader': 8, 'independent_reviewer': 8, 'ocr': 1}
RATES = {'gpt-4.1': (Decimal('2'), Decimal('8')), 'gpt-6.1-sol': (Decimal('2'), Decimal('10'))}
OUTPUTS = {'prepare': 10000, 'rubric': 10000, 'help2': 10000, 'grader': 4000, 'independent_reviewer': 4000}


def reservation(group):
    if group == 'ocr': return Decimal('0.01')
    model = 'gpt-6.1-sol' if group in {'grader', 'independent_reviewer'} else 'gpt-4.1'
    inp, out = RATES[model]
    return (INPUT_RESERVE * inp + OUTPUTS[group] * out) / 1000000


def plan():
    return dict(mode='PLAN_ONLY',api_calls=0,cap_usd=str(CAP),max_calls=sum(LIMITS.values()),
        limits=LIMITS,reservation_usd={g:str(reservation(g)) for g in LIMITS},
        maximum_reserved_usd=str(sum(LIMITS[g]*reservation(g) for g in LIMITS)),
        max_request_json_bytes=MAX_JSON_BYTES,input_token_reserve_per_llm_call=INPUT_RESERVE,
        prices_checked='2026-11-26',requires_later_explicit_authorization=True)


class StopSmoke(RuntimeError): pass


class BudgetGate:
    def __init__(self, directory):
        self.root=Path(directory);self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.ledger=self.root/'ledger.jsonl'
        # A restart must not silently reset spending; no automatic retries/resume.
        if self.ledger.exists():raise StopSmoke('Existing ledger: review it before any new authorization.')
        self.used=Decimal(0);self.counts={k:0 for k in LIMITS};self.halted=False
        self.lock=threading.Lock()
        self._event(dict(event='plan',**plan()))

    def _event(self, row):
        data=(json.dumps(row,sort_keys=True,ensure_ascii=False)+'\n').encode()
        fd=os.open(self.ledger,os.O_APPEND|os.O_CREAT|os.O_WRONLY,0o600)
        try:
            with os.fdopen(fd,'ab') as f:f.write(data);f.flush();os.fsync(f.fileno())
        except Exception:
            self.halted=True;raise

    def classify(self, request):
        url=str(request.url)
        if request.method!='POST':raise StopSmoke('Only approved POSTs are allowed.')
        if url=='https://api.mathpix.com/v3/text':return 'ocr',None,None
        if url!='https://api.openai.com/v1/responses':raise StopSmoke('Unapproved endpoint.')
        raw=request.read()
        if len(raw)>MAX_JSON_BYTES:raise StopSmoke('Request exceeds the reserved input envelope.')
        body=json.loads(raw)
        allowed={'model','store','max_output_tokens','input','text','reasoning'}
        if set(body)-allowed or body.get('store') is not False:raise StopSmoke('Unapproved request options.')
        messages=body['input']
        if len(messages)!=2 or [m['role'] for m in messages]!=['system','user']:raise StopSmoke('Unexpected prompt envelope.')
        payload=json.loads(messages[1]['content'])
        schema=body['text']['format']['name']
        if schema in {'rubric_decision','dynamic_credit_decision'}:
            group=payload['stage']
            if group not in {'grader','independent_reviewer'} or not 1<=len(payload['rubric']['criteria'])<=4:
                raise StopSmoke('Semantic scope exceeds approved four criteria.')
        else:
            group={'PreparationProposal':'prepare','SuggestedRubric':'rubric','ControlledHelpProposal':'help2'}.get(schema)
            if group is None or payload.get('context')!='SELF_STUDY':raise StopSmoke('Unapproved preparation context.')
            if group=='help2' and payload.get('level')!=2:raise StopSmoke('Only one level-2 hint is budgeted.')
        model='gpt-6.1-sol' if group in {'grader','independent_reviewer'} else 'gpt-4.1'
        if body['model']!=model or body['max_output_tokens']!=OUTPUTS[group]:raise StopSmoke('Model/output limit differs from plan.')
        if group in {'grader','independent_reviewer'}:
            if body.get('reasoning')!={'effort':'medium'}:raise StopSmoke('Unexpected reasoning configuration.')
        elif body.get('reasoning'):raise StopSmoke('Preparation reasoning configuration changed.')
        return group,model,body

    def send(self, original, client, request, **kwargs):
        with self.lock:
            if self.halted or (self.root/'STOP').exists():raise StopSmoke('Smoke stopped; no further paid request.')
            started=time.perf_counter()
            try:
                group,model,body=self.classify(request)
                amount=reservation(group)
                if self.counts[group]>=LIMITS[group] or self.used+amount>CAP:raise StopSmoke('Call or budget cap reached.')
                self.counts[group]+=1;self.used+=amount
                call=sum(self.counts.values());started=time.perf_counter()
                # Only hashes/metadata: never record credentials or request headers.
                self._event(dict(event='reserved',call=call,group=group,requested_model=model,
                    request_sha256=hashlib.sha256(request.read()).hexdigest(),reserved_usd=str(amount),total_reserved_usd=str(self.used)))
                kwargs["follow_redirects"]=False
                response=original(client,request,**kwargs)
                response.read()
                raw=response.content
                if len(raw)>3*1024*1024:raise StopSmoke('Oversized response.')
                data=json.loads(raw)
                filename=self.root/f'response_{call:03d}.json'
                fd=os.open(filename,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                with os.fdopen(fd,'wb') as f:f.write(raw)
                usage=data.get('usage') if model else None
                actual=None
                if model:
                    if not isinstance(usage,dict):raise StopSmoke('Usage missing; reserved cost retained.')
                    inp=usage['input_tokens'];out=usage['output_tokens']
                    if type(inp)!=int or type(out)!=int or not 0<=inp<=INPUT_RESERVE or not 0<=out<=OUTPUTS[group]:
                        raise StopSmoke('Usage exceeds reservation assumptions.')
                    actual=(inp*RATES[model][0]+out*RATES[model][1])/1000000
                self._event(dict(event='response',call=call,group=group,http_status=response.status_code,
                    latency_seconds=round(time.perf_counter()-started,6),response_sha256=hashlib.sha256(raw).hexdigest(),
                    returned_model=data.get('model'),response_id=data.get('id') or data.get('request_id'),
                    usage=usage,estimated_standard_cost_usd=str(actual) if actual is not None else None,
                    service_tier=data.get('service_tier'),artifact=filename.name))
                if response.status_code>=300 or data.get('error') or data.get('error_info') or model and data.get('status')!='completed':raise StopSmoke('Provider failed or incomplete; review before proceeding.')
                if model and data.get('service_tier') not in {None,'default','standard'}:raise StopSmoke('Unexpected billed service tier.')
                if model and not (data.get('model')==model or str(data.get('model','')).startswith(model+'-')):raise StopSmoke('Returned model differs; do not silently substitute.')
                return response
            except Exception as exc:
                self.halted=True
                # Fixed type only; provider exceptions can contain request secrets.
                self._event(dict(event='stopped',call=sum(self.counts.values()),latency_seconds=round(time.perf_counter()-started,6),error_type=type(exc).__name__,total_reserved_usd=str(self.used)))
                raise StopSmoke('Smoke stopped. Inspect private ledger; no automatic retry.') from None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve-after-authorization',action='store_true')
    parser.add_argument('--authorized-budget-usd')
    parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--port',type=int,default=8026)
    args=parser.parse_args()
    if not args.serve_after_authorization:print(json.dumps(plan(),indent=2));return
    if args.authorized_budget_usd!='6.00' or not args.data_dir:parser.error('Explicit USD 6.00 authorization and isolated data directory required.')
    required={'CONFIA_AUTH_ENABLED':'1','CONFIA_DYNAMIC_LLM_ENABLED':'1','CONFIA_SEMANTIC_LLM_ENABLED':'1',
        'CONFIA_DYNAMIC_MODEL':'gpt-4.1','CONFIA_SEMANTIC_MODEL':'gpt-6.1-sol','CONFIA_SEMANTIC_REASONING_EFFORT':'medium'}
    if any(os.getenv(k)!=v for k,v in required.items()):parser.error('Configuration differs from approved smoke plan.')
    if not all(os.getenv(k) for k in ('OPENAI_API_KEY','CONFIA_MATHPIX_APP_ID','CONFIA_MATHPIX_APP_KEY')):parser.error('Secure provider configuration missing.')
    import sys
    sys.path.insert(0,str(ROOT/'app'))
    data=args.data_dir.resolve()
    for store in ('AUTH','INSTITUTIONAL','ASSESSMENTS','ASSESSMENT_PARTICIPANTS','TME_EXAMS','TME_CASES','SUBMISSIONS','SUBMISSION_AUDITS','DYNAMIC','TEACHER_DECISIONS','SELF_STUDY'):
        os.environ['CONFIA_'+store+'_DIR']=str(data/store.lower())
    os.environ.update(CONFIA_ENV='development',CONFIA_COOKIE_SECURE='0',CONFIA_TME_DEMO_NO_AUTH='0',CONFIA_DYNAMIC_DEMO_ENABLED='0',CONFIA_LEAN_AUDITOR_ROOT=str(ROOT),CONFIA_DYNAMIC_REVIEWER_ENABLED='0')
    gate=BudgetGate(data/'smoke-control')
    import httpx,uvicorn
    original=httpx.Client.send
    httpx.Client.send=lambda client,request,**kwargs:gate.send(original,client,request,**kwargs)
    uvicorn.run('confia_lean_auditor.main:app',host='127.0.0.1',port=args.port,workers=1)


if __name__=='__main__':main()
