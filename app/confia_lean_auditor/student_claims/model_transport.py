"""Opt-in transport compatibility for the frozen model ablation, not grading.

No client, prompt, schema or response interpretation lives here. Legacy callers
do not use this builder unless they explicitly inject it into a request.
"""
from copy import deepcopy

VERSION = 'tme-model-transport.v1'
SOL_MODEL = 'gpt-6.1-sol'
PARAMETER_NOTE = (
    'Os parâmetros de geração não são literalmente idênticos porque os modelos possuem '
    'contratos de API diferentes. Cada braço utiliza a configuração válida previamente '
    'especificada, mantendo constantes todas as camadas semânticas e matemáticas do experimento.'
)


def build_request(request):
    """Copy existing kwargs; only Sol's explicitly specified contract differs.

    Unlisted models retain their original parameters; no availability or
    compatibility claim is made for them. No effort search or sampling fallback.
    Also accepts configuration metadata so preflight uses the same policy.
    """
    result = deepcopy(request)
    if result['model'] == SOL_MODEL:
        for key in ('temperature', 'top_p', 'top_logprobs', 'logprobs'):
            result.pop(key, None)
        if 'include' in result:
            result['include'] = [item for item in result['include']
                                 if item != 'message.output_text.logprobs']
        result['reasoning'] = {'effort': 'medium'}
    return result


def transport_configuration(configuration):
    """Only model/transport settings, separately hashable from semantic inputs."""
    effective = build_request(configuration)
    return dict(policy=VERSION, endpoint='https://api.openai.com/v1',
        client=dict(timeout=effective['timeout'], max_retries=effective['max_retries']),
        request={key: effective[key] for key in
                 ('model', 'store', 'max_output_tokens', 'temperature', 'reasoning') if key in effective})
