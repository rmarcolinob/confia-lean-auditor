"""Transport-only compatibility checks: local SDK doubles, never inference."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from confia_lean_auditor.student_claims import hybrid_semantic as semantic
from confia_lean_auditor.student_claims import semantic_sufficiency as sufficiency
from confia_lean_auditor.student_claims import model_transport as transport
from test_tme_hybrid_grader import judgment, provider as judgments_for
from test_tme_model_ablation import ablation, forbid_network

MINI = 'gpt-4o-mini-2024-07-18'
SOL = 'gpt-6.1-sol'


def test_sol_removes_incompatible_parameters_without_mutating_source():
    request = dict(model=SOL, temperature=0, top_p=1, top_logprobs=3, logprobs=True,
        include=['message.output_text.logprobs', 'reasoning.encrypted_content'],
        input=[{'role': 'user', 'content': 'fixed'}], text={'format': {'type': 'json_schema'}},
        store=False, max_output_tokens=16000)
    before = deepcopy(request)
    built = transport.build_request(request)
    assert not {'temperature', 'top_p', 'top_logprobs', 'logprobs'} & built.keys()
    assert built['reasoning'] == {'effort': 'medium'}
    assert built['include'] == ['reasoning.encrypted_content']
    assert built['input'] == request['input'] and built['text'] == request['text']
    assert request == before


@pytest.mark.parametrize('module', [semantic, sufficiency])
def test_mini_transport_is_exactly_legacy_and_configuration_is_opt_in(module):
    legacy = module.configuration()
    assert transport.build_request(legacy) == legacy
    assert legacy['model'] == MINI and legacy['temperature'] == 0 and 'reasoning' not in legacy
    # The existing component configuration is not globally rewritten for Sol.
    raw_sol = module.configuration(model=SOL)
    effective = transport.build_request(raw_sol)
    assert raw_sol['temperature'] == 0 and 'reasoning' not in raw_sol
    assert 'temperature' not in effective and effective['reasoning'] == {'effort': 'medium'}
    assert module.configuration() == legacy


def install_client(monkeypatch, calls):
    import openai
    class Client:
        def __init__(self, **kwargs):
            assert kwargs == dict(base_url='https://api.openai.com/v1', timeout=180, max_retries=0)
            self.responses = self
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def create(self, **kwargs):
            calls.append(kwargs)
            payload = json.loads(kwargs['input'][1]['content'])
            if kwargs['text']['format']['name'] == 'semantic_rubric_judgments':
                js, _ = judgments_for(payload['problem_id'], payload['full_student_solution'],
                    {'b.apqr': judgment('b.apqr', ('E002',))})
                data = {'judgments': [j.model_dump() for j in js]}
            else:
                data = {'decisions': {o['obligation_id']: dict(obligation_id=o['obligation_id'],
                    sufficiency='sufficient', evidence_ids=[e['evidence_id'] for e in o['selected_evidence']],
                    reason_code='adequate_evidence', concise_rationale='Local test fixture.') for o in payload['obligations']}}
            return SimpleNamespace(status='completed', model=kwargs['model'], id='offline',
                output_text=json.dumps(data), usage=None)
    monkeypatch.setattr(openai, 'OpenAI', Client)


@pytest.mark.parametrize('stage', ['semantic', 'sufficiency'])
def test_sdk_receives_valid_transport_and_identical_prompt_schema(monkeypatch, stage):
    calls = []
    install_client(monkeypatch, calls)
    text = '(b) APQR é um paralelogramo.'
    js, _ = judgments_for('TME2026P4', text, {'b.apqr': judgment('b.apqr', ('E002',))})
    payload, _, _ = sufficiency.SemanticSufficiencyGate().prepare('TME2026P4', text, js)
    for model in [MINI, SOL]:
        options = dict(model=model, request_builder=transport.build_request)
        _, meta = (semantic.request_judgments('TME2026P4', text, **options) if stage == 'semantic'
                   else sufficiency.request_sufficiency(payload, **options))
        assert meta['status'] == 'completed' and meta['model'] == model
    a, b = calls
    assert a['model'] == MINI and a['temperature'] == 0 and 'reasoning' not in a
    assert b['model'] == SOL and b['reasoning'] == {'effort': 'medium'}
    assert not {'temperature', 'top_p', 'top_logprobs', 'logprobs'} & b.keys()
    strip_transport = lambda v: {k: x for k, x in v.items() if k not in {'model', 'temperature', 'reasoning'}}
    assert strip_transport(a) == strip_transport(b)
    assert a['input'] == b['input'] and a['text'] == b['text']


def test_runner_default_providers_apply_compatibility_to_both_stages(monkeypatch):
    # Synthetic local input; no DEV inference or historical judgments.
    case = dict(solution_id='offline-test', problem_id='TME2026P4',
        solution_text='(b) APQR é um paralelogramo.', items={}, source_sha256='offline')
    calls = []
    install_client(monkeypatch, calls)
    for model in [MINI, SOL]:
        row = ablation._run_arm(case, model, use_lean=False)
        assert row['first_provider']['status'] == row['sufficiency_provider']['status'] == 'completed'
        assert row['model_transport_configuration']['semantic']['request']['model'] == model
        assert row['model_transport_configuration']['sufficiency']['request']['model'] == model
    assert [c['model'] for c in calls] == [MINI, MINI, SOL, SOL]
    for i in [0, 1]:
        assert calls[i]['temperature'] == 0 and 'reasoning' not in calls[i]
    for i in [2, 3]:
        assert calls[i]['reasoning'] == {'effort': 'medium'} and 'temperature' not in calls[i]
    assert calls[0]['input'] == calls[2]['input'] and calls[0]['text'] == calls[2]['text']
    assert calls[1]['input'] == calls[3]['input'] and calls[1]['text'] == calls[3]['text']


def test_real_smoke_dry_run_separates_semantic_hashes_from_transport(tmp_path, monkeypatch):
    if not ablation.DEV_IDS.exists() or not ablation.DEV_SOURCES.exists():
        pytest.skip('Frozen local DEV pack unavailable')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    out = tmp_path / 'dry'
    ablation.main(['--model-a', MINI, '--model-b', SOL, '--split', 'smoke', '--shadow',
                  '--dry-run', '--output', str(out)])
    plan = json.loads((out / 'preflight.json').read_text())
    a, b = plan['arms']['a'], plan['arms']['b']
    for key in ['prompt_hashes', 'semantic_schema_hashes', 'semantic_payload_hashes',
                'semantic_layer_hashes', 'sufficiency_schema_contract_sha256',
                'evidence_unit_configuration_hash', 'protected_code_hash']:
        assert a[key] == b[key]
    assert a['model_transport_sha256'] != b['model_transport_sha256']
    for stage in ['semantic', 'sufficiency']:
        ar = a['model_transport_configuration'][stage]['request']
        br = b['model_transport_configuration'][stage]['request']
        assert ar == dict(model=MINI, store=False, max_output_tokens=16000, temperature=0)
        assert br == dict(model=SOL, store=False, max_output_tokens=16000, reasoning={'effort': 'medium'})
    status = json.loads((out / 'execution_status.json').read_text())
    assert status['cases'] == 5 and status['api_calls_made'] == status['holdout_processed'] == 0
    assert status['generation_parameter_note'] == transport.PARAMETER_NOTE


def test_transport_builder_does_not_weaken_holdout_guard():
    if not ablation.DEV_IDS.exists():
        pytest.skip('Frozen local DEV pack unavailable')
    with pytest.raises(ValueError, match='DEV IDs'):
        ablation.build_plan(MINI, SOL, 'smoke', [*ablation.SMOKE_IDS[:4], 'HOLDOUT_NOT_READ'])
