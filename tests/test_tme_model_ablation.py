"""Offline transport/orchestration tests. Never evaluates an external model."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from confia_lean_auditor.student_claims import hybrid_semantic as semantic
from confia_lean_auditor.student_claims import semantic_sufficiency as sufficiency
from test_tme_hybrid_grader import judgment, provider as judgments_for

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ablation', ROOT / 'scripts/evaluation/evaluate_tme_model_ablation.py')
ablation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ablation)


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    import socket
    import openai
    attempts = []
    def forbidden(*args, **kwargs):
        attempts.append(True)
        raise AssertionError('External calls forbidden in preparation tests')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    monkeypatch.setattr(openai, 'OpenAI', forbidden)
    yield
    # Provider wrappers catch Exceptions; detect even a swallowed attempt.
    assert not attempts, 'A client/network attempt was made during offline preparation'


@pytest.fixture
def plan():
    if not ablation.DEV_IDS.exists() or not ablation.DEV_SOURCES.exists():
        pytest.skip('Frozen local DEV pack unavailable; never replace with another dataset')
    return ablation.build_plan('MODEL_A', 'MODEL_B', 'smoke')[0]


@pytest.mark.parametrize('module,version,prompt_hash', [
    (semantic, 'tme-hybrid-grader.v1', '590349b9a1ea613ed8e930cb275e019cc4e6fa287b6d5c2a5b9eb79cd7aa7d6e'),
    (sufficiency, 'semantic-sufficiency.v1', 'b7cb54d3f32afa16f3f8e112f0c8a07df5d7defd2d140f45b6b72285bcc5173c'),
])
def test_default_configuration_is_exactly_legacy(module, version, prompt_hash):
    expected = dict(version=version, model='gpt-4o-mini-2024-07-18', temperature=0,
        store=False, timeout=180, max_retries=0, max_output_tokens=16000, prompt_sha256=prompt_hash)
    assert module.configuration() == expected == module.configuration(model=None)
    assert module.configuration(model='MODEL_X') == dict(expected, model='MODEL_X')
    assert module.configuration() == expected  # No shared mutation.


@pytest.mark.parametrize('stage', ['semantic', 'sufficiency'])
def test_override_changes_only_model_in_actual_sdk_request(monkeypatch, stage):
    import openai
    calls, client_configs = [], []
    text = 'APQR é um paralelogramo.'
    js, _ = judgments_for('TME2026P4', text, {'b.apqr': judgment('b.apqr')})
    payload, _, _ = sufficiency.SemanticSufficiencyGate().prepare('TME2026P4', text, js)
    class Client:
        def __init__(self, **kwargs):
            client_configs.append(kwargs)
            self.responses = self
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def create(self, **kwargs):
            calls.append(kwargs)
            if stage == 'semantic':
                data = {'judgments': [j.model_dump() for j in js]}
            else:
                data = {'decisions': {o['obligation_id']: dict(obligation_id=o['obligation_id'],
                    sufficiency='sufficient', evidence_ids=[e['evidence_id'] for e in o['selected_evidence']],
                    reason_code='adequate_evidence', concise_rationale='Offline fixture.') for o in payload['obligations']}}
            return SimpleNamespace(status='completed', model=kwargs['model'], id='offline',
                output_text=json.dumps(data), usage=None)
    monkeypatch.setattr(openai, 'OpenAI', Client)
    for options in [{}, {'model': 'MODEL_A'}, {'model': 'MODEL_B'}]:
        _, meta = (semantic.request_judgments('TME2026P4', text, **options) if stage == 'semantic'
                   else sufficiency.request_sufficiency(payload, **options))
        assert meta['status'] == 'completed'
    assert [c['model'] for c in calls] == ['gpt-4o-mini-2024-07-18', 'MODEL_A', 'MODEL_B']
    assert all({k: v for k, v in c.items() if k != 'model'} ==
               {k: v for k, v in calls[0].items() if k != 'model'} for c in calls)
    assert all(c == client_configs[0] for c in client_configs)
    assert 'reasoning' not in calls[0] and calls[0]['store'] is False


def test_plan_has_identical_payloads_contracts_and_only_model_difference(plan):
    a, b = deepcopy(plan['arms']['a']), deepcopy(plan['arms']['b'])
    assert a.pop('model') != b.pop('model')
    for kind in ['semantic', 'sufficiency']:
        assert a[kind + '_configuration'].pop('model') != b[kind + '_configuration'].pop('model')
        assert a.pop(kind + '_configuration_sha256') != b.pop(kind + '_configuration_sha256')
        assert a['model_transport_configuration'][kind]['request'].pop('model') != b['model_transport_configuration'][kind]['request'].pop('model')
    assert a.pop('model_transport_sha256') != b.pop('model_transport_sha256')
    assert a == b
    assert plan['cases'] == 5 and plan['stages_per_arm'] == 2
    assert plan['first_stage_calls_planned'] == 10
    assert plan['total_calls_planned'] == {'minimum': 10, 'maximum': 20}
    assert plan['arms']['a']['sufficiency_instantiated_schema_hashes'] is None


@pytest.mark.parametrize('model', ['', ' model', 'model\n', 'model with spaces', '../not-a-model', None])
def test_malformed_model_rejected_before_provider(model):
    with pytest.raises(ValueError, match='syntax'):
        ablation.validate_model(model)


@pytest.mark.parametrize('selection', [
    ['TME2026P1_01', *ablation.SMOKE_IDS[1:]],  # Valid-looking ID outside frozen DEV.
    [*ablation.SMOKE_IDS[:4], 'HOLDOUT_NOT_READ'],
    [*ablation.SMOKE_IDS[:4], ablation.SMOKE_IDS[0]],
])
def test_entire_selection_rejected_before_any_provider(plan, selection):
    plan['case_ids'] = selection
    calls = []
    def spy(*args, **kwargs): calls.append((args, kwargs)); pytest.fail('Provider invoked')
    with pytest.raises(ValueError, match='DEV IDs'):
        ablation.execute_plan(plan, judgment_provider=spy, sufficiency_provider=spy)
    assert calls == []


def test_modified_dev_manifest_is_rejected_before_sources(plan, tmp_path, monkeypatch):
    path = tmp_path / 'ids.json'
    path.write_text(json.dumps([*ablation.SMOKE_IDS, 'HOLDOUT_NOT_READ']))
    monkeypatch.setattr(ablation, 'DEV_IDS', path)
    with pytest.raises(ValueError, match='allowlist changed'):
        ablation.select_cases('smoke')


def test_dry_run_cli_has_no_key_client_or_network(plan, tmp_path, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    out = tmp_path / 'dry'
    assert ablation.main(['--model-a', 'MODEL_A', '--model-b', 'MODEL_B', '--split', 'smoke',
                          '--shadow', '--dry-run', '--output', str(out)]) == 0
    data = json.loads((out / 'preflight.json').read_text())
    assert data['api_calls_made'] == 0 and data['holdout_processed'] == 0
    assert len(list((out / 'prepared_payloads').glob('*.json'))) == 5
    assert not list(out.glob('*model_*.jsonl'))
    assert data['historical_judgments_reused'] is False


def test_dev_plan_loads_exactly_25_frozen_cases_without_providers(plan):
    full, _, cases = ablation.build_plan('MODEL_A', 'MODEL_B', 'dev')
    assert len(cases) == 25 and full['total_calls_planned'] == {'minimum': 50, 'maximum': 100}
    assert full['api_calls_made'] == 0


def test_fresh_both_stages_same_model_and_independent_arms(plan):
    events = []
    expected_targets = {}
    def first(problem, text, *, model):
        events.append(('semantic', model))
        # Deliberately distinct first-stage choices: B must never reuse A's.
        oid = semantic.catalog(problem)[0 if model == 'MODEL_A' else 1]['obligation_id']
        units = ablation.units_module.evidence_units(text)
        ids = [u.evidence_id for u in units]
        js, meta = judgments_for(problem, text, {oid: judgment(oid, ids)})
        payload, _, _ = sufficiency.SemanticSufficiencyGate().prepare(problem, text, js)
        expected_targets[model] = [o['obligation_id'] for o in payload['obligations']]
        return js, dict(meta, model=model)
    def second(payload, *, model):
        events.append(('sufficiency', model))
        assert [o['obligation_id'] for o in payload['obligations']] == expected_targets[model]
        decisions = tuple(sufficiency.SufficiencyDecision(obligation_id=o['obligation_id'],
            sufficiency='insufficient', evidence_ids=[e['evidence_id'] for e in o['selected_evidence']],
            reason_code='missing_step', concise_rationale='Offline fixture.') for o in payload['obligations'])
        return decisions, dict(status='completed', api_calls=0, model=model)
    results = ablation.execute_plan(plan, judgment_provider=first, sufficiency_provider=second, use_lean=False)
    assert [model for stage, model in events if stage == 'semantic'] == ['MODEL_A', 'MODEL_B'] * 5
    assert {model for stage, model in events if stage == 'sufficiency'} == {'MODEL_A', 'MODEL_B'}
    for arm, model in [('a', 'MODEL_A'), ('b', 'MODEL_B')]:
        assert len(results[arm]) == 5
        for row in results[arm]:
            assert row['first_provider']['model'] == model and row['api_calls'] == 0
            assert row['sufficiency_provider']['status'] in {'completed', 'skipped'}
            if row['sufficiency_provider']['status'] == 'completed':
                assert row['sufficiency_provider']['model'] == model
            assert row['primary_bridge'] and row['audit_bridge'] and row['reconciliation']


def test_no_positive_candidates_skips_gate_and_preserves_audit(plan):
    case = ablation.select_cases('smoke')[3]
    def first(p, t, *, model): return judgments_for(p, t, {})
    def forbidden(*args, **kwargs): pytest.fail('No gate call without candidates')
    result = ablation._run_arm(case, 'MODEL_A', judgment_provider=first,
        sufficiency_provider=forbidden, use_lean=False)
    assert result['sufficiency_provider'] == {'status': 'skipped', 'api_calls': 0}
    assert result['api_calls'] == 0


def test_failed_first_provider_never_reuses_old_judgments(plan):
    case = ablation.select_cases('smoke')[3]
    def failed(*args, **kwargs): return (), dict(status='unavailable', api_calls=0)
    def forbidden(*args, **kwargs): pytest.fail('Unexpected gate call')
    result = ablation._run_arm(case, 'MODEL_A', judgment_provider=failed,
        sufficiency_provider=forbidden, use_lean=False)
    assert result['judgments'] == [] and result['sufficiency_decisions'] == []
    assert any(t['decision'] == 'technical_error' for t in result['reconciliation'])


def test_changed_config_plan_is_rejected_before_provider(plan):
    plan['arms']['b']['sufficiency_configuration']['temperature'] = 1
    with pytest.raises(ValueError, match='changed'):
        ablation.execute_plan(plan)


def test_live_cli_requires_clean_checkout_and_never_overwrites(plan, tmp_path, monkeypatch):
    monkeypatch.setattr(ablation, 'git_state', lambda: dict(sha='frozen', branch='test', status_short=' M source.py'))
    with pytest.raises(SystemExit):
        ablation.main(['--model-a', 'MODEL_A', '--model-b', 'MODEL_B', '--split', 'smoke',
                      '--shadow', '--live', '--output', str(tmp_path / 'live')])
    assert not (tmp_path / 'live').exists()
