"""Approved discrete credit levels and literal evidence; DYNAMIC only."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import json
import os

from confia_lean_auditor.semantic_policy.minimal_review import PROMPT, obtain_review, digest
from confia_lean_auditor.semantic_policy.service import SemanticProvider, DYNAMIC_VERSION

VERSION = 'dynamic-credit.v1'
PROMPT_CREDIT = PROMPT + '''
Extensão DYNAMIC: você pode decidir partial SOMENTE selecionando level_id existente
em criterion.credit_levels. Não retorne pontos nem invente níveis. met exige todo
o critério; partial exige evidência matemática válida para a descrição do nível.
Diferencie VALID_ARGUMENT, MATHEMATICAL_ERROR, INCOMPLETE_DEVELOPMENT,
ABSENT_EVIDENCE e UNCERTAIN. Ausência de evidência ou incerteza: review.
Resposta final correta não sustenta um critério de desenvolvimento por si só.
Para cada dependency_rule, avalie a condition aprovada: satisfied, violated ou
unknown, com justificativa e citações literais. MATHEMATICAL exige pré-requisito
matematicamente suficiente; PROCEDURAL exige a etapa prevista, não sua nota;
CARRY_FORWARD permite continuação coerente sobre erro anterior apenas conforme a
condition aprovada. Não infira penalização para critérios independentes.
Retorne level_id null salvo partial. Mesmo partial não é prova formal.'''
SCHEMA = dict(type='object', additionalProperties=False,
    required=['decision','level_id','justification','quotes','finding','dependencies'], properties={
    'decision':dict(type='string',enum=['met','partial','not_met','review']),
    'level_id':dict(type=['string','null']), 'justification':dict(type='string'),
    'quotes':dict(type='array',items=dict(type='string')),
    'finding':dict(type='string',enum=['VALID_ARGUMENT','MATHEMATICAL_ERROR','INCOMPLETE_DEVELOPMENT','ABSENT_EVIDENCE','UNCERTAIN']),
    'dependencies':dict(type='array',items=dict(type='object',additionalProperties=False,
        required=['criterion_id','status','justification','quotes'],properties={
        'criterion_id':dict(type='string'),'status':dict(type='string',enum=['satisfied','violated','unknown']),
        'justification':dict(type='string'),'quotes':dict(type='array',items=dict(type='string'))}))})


class DynamicCreditProvider(SemanticProvider):
    """Bounded opt-in adapter; never used for SPECIALIZED or binary-only rubrics."""
    def __call__(self, request):
        if os.getenv('CONFIA_SEMANTIC_LLM_ENABLED') != '1' or not os.getenv('OPENAI_API_KEY'):
            raise RuntimeError('SEMANTIC_PROVIDER_NOT_CONFIGURED')
        from openai import OpenAI
        with OpenAI(base_url='https://api.openai.com/v1',timeout=60,max_retries=0) as client:
            response=client.responses.create(model=os.getenv('CONFIA_SEMANTIC_MODEL','gpt-6.1-sol'),
                **({'reasoning':{'effort':os.getenv('CONFIA_SEMANTIC_REASONING_EFFORT','medium')}} if os.getenv('CONFIA_SEMANTIC_REASONING_EFFORT','medium') else {}),
                store=False,max_output_tokens=4000,
                input=[dict(role='system',content=PROMPT_CREDIT),dict(role='user',content=json.dumps(request,ensure_ascii=False))],
                text={'format':dict(type='json_schema',name='dynamic_credit_decision',strict=True,schema=SCHEMA)})
        self.metadata=dict(response_id=response.id,model=response.model,status=response.status,
            usage=response.usage.model_dump(mode='json') if response.usage else None)
        if response.status != 'completed':raise ValueError('incomplete_response')
        return json.loads(response.output_text)


def extended(criterion):
    return bool(criterion.credit_levels or criterion.dependency_rules)


def assess_credit(request, provider):
    """Reuse source-quote validation, keeping the original extended response receipt."""
    raw_holder={}
    def bounded(payload):
        raw=provider(payload);raw_holder['response']=deepcopy(raw)
        if not isinstance(raw,dict) or set(raw)!=set(SCHEMA['required']):raise ValueError('response_fields')
        state=raw['decision'];level=raw['level_id'];criterion=request['criterion']
        if state not in {'met','partial','not_met','review'}:raise ValueError('decision')
        if raw['finding'] not in SCHEMA['properties']['finding']['enum']:raise ValueError('finding')
        levels={c['level_id']:Decimal(str(c['points'])) for c in criterion.get('credit_levels',[])}
        if state=='partial' and (level not in levels or not 0<levels[level]<Decimal(str(criterion['max_points']))):
            raise ValueError('unauthorized_credit_level')
        if state!='partial' and level is not None:raise ValueError('unexpected_credit_level')
        deps=raw['dependencies'];rules=criterion.get('dependency_rules',[])
        if not isinstance(deps,list) or any(not isinstance(d,dict) or set(d)!={'criterion_id','status','justification','quotes'} for d in deps):
            raise ValueError('dependency_fields')
        if len(deps)!=len(rules) or {d['criterion_id'] for d in deps}!={r['criterion_id'] for r in rules}:
            raise ValueError('dependency_scope')
        for d in deps:
            if d['status'] not in {'satisfied','violated','unknown'}:raise ValueError('dependency_status')
            checked=obtain_review(lambda _:dict(decision='met' if d['status']=='satisfied' else 'review',justification=d['justification'],quotes=d['quotes']),request)
            if checked.get('error_type'):raise ValueError('dependency_evidence')
        normalized=dict(decision='met' if state=='partial' else state,justification=raw['justification'],quotes=raw['quotes'])
        return normalized
    trace=obtain_review(bounded,request)
    if 'response' in raw_holder:
        raw=raw_holder['response']
        trace['response' if isinstance(raw,dict) else 'invalid_response']=raw
        try:trace['response_sha256']=digest(raw)
        except (TypeError,ValueError):pass
    if not trace.get('error_type'):
        raw=raw_holder['response'];trace['decision']=raw['decision']
        if raw['finding'] in {'ABSENT_EVIDENCE','UNCERTAIN'} or (raw['decision']=='met' and raw['finding']!='VALID_ARGUMENT'):
            trace.update(decision='review',gate_reason='INSUFFICIENT_MATHEMATICAL_BASIS')
        trace['level_id']=raw['level_id'];trace['finding']=raw['finding']
        trace['dependency_opinions']=deepcopy(raw['dependencies'])
    trace.update(policy=DYNAMIC_VERSION,credit_contract=VERSION,verification_level='SEMANTIC_NOT_FORMAL',
        created_at=datetime.now(timezone.utc).isoformat(),provider=getattr(provider,'metadata',{}))
    return trace


def points_for(criterion, trace):
    if trace.get('decision')=='met':return criterion.max_points
    if trace.get('decision')=='not_met':return Decimal(0)
    if trace.get('decision')=='partial':
        return next((c.points for c in criterion.credit_levels if c.level_id==trace.get('level_id')),None)
    return None


def valid_level(criterion, trace, points, sufficiency):
    expected=points_for(criterion,trace)
    return expected is not None and points==expected and sufficiency=={
        'met':'COMPLETE','partial':'PARTIAL','not_met':'NOT_SATISFIED'}.get(trace.get('decision'))
