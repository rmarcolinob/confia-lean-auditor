"""Bounded, opt-in provider; source-bound decisions shared by both product modes."""
import json
import os
from datetime import datetime, timezone
from .minimal_review import PROMPT, SCHEMA, obtain_review, digest

VERSION = 'semantic-b-minimal.v1'
DYNAMIC_VERSION = 'dynamic-semantic.v1'


def specialized_policy():
    value = os.getenv('CONFIA_SPECIALIZED_POLICY', VERSION)
    if value not in {VERSION, 'legacy'}:
        raise ValueError('Unknown SPECIALIZED policy')
    return value


def dynamic_policy():
    value = os.getenv('CONFIA_DYNAMIC_POLICY', DYNAMIC_VERSION)
    if value not in {DYNAMIC_VERSION, 'legacy'}:
        raise ValueError('Unknown DYNAMIC policy')
    return value


def configuration():
    return dict(policy=specialized_policy(), prompt_version=VERSION,
                model=os.getenv('CONFIA_SEMANTIC_MODEL', 'gpt-6.1-sol'),
                reasoning_effort=os.getenv('CONFIA_SEMANTIC_REASONING_EFFORT', 'medium'),
                enabled=os.getenv('CONFIA_SEMANTIC_LLM_ENABLED') == '1')


class SemanticProvider:
    """No client is constructed until explicit configuration enables paid inference."""
    def __call__(self, request):
        if os.getenv('CONFIA_SEMANTIC_LLM_ENABLED') != '1' or not os.getenv('OPENAI_API_KEY'):
            raise RuntimeError('SEMANTIC_PROVIDER_NOT_CONFIGURED')
        from openai import OpenAI
        with OpenAI(base_url='https://api.openai.com/v1', timeout=60, max_retries=0) as client:
            response = client.responses.create(model=os.getenv('CONFIA_SEMANTIC_MODEL', 'gpt-6.1-sol'),
                **({'reasoning':{'effort':os.getenv('CONFIA_SEMANTIC_REASONING_EFFORT','medium')}} if os.getenv('CONFIA_SEMANTIC_REASONING_EFFORT','medium') else {}),
                store=False, max_output_tokens=4000,
                input=[dict(role='system', content=PROMPT), dict(role='user', content=json.dumps(request, ensure_ascii=False))],
                text={'format':dict(type='json_schema',name='rubric_decision',strict=True,schema=SCHEMA)})
        self.metadata = dict(response_id=response.id, model=response.model, status=response.status,
            usage=response.usage.model_dump(mode='json') if response.usage else None)
        if response.status != 'completed':
            raise ValueError('incomplete_response')
        return json.loads(response.output_text)


def assess(request, provider=None):
    provider = provider or SemanticProvider()
    trace = obtain_review(provider, request)
    if not isinstance(trace.get('response',{}),dict):
        trace['invalid_response']=trace.pop('response')
    trace.update(policy=VERSION, verification_level='SEMANTIC_NOT_FORMAL',
                 created_at=datetime.now(timezone.utc).isoformat(),
                 provider=getattr(provider, 'metadata', {}))
    return trace
