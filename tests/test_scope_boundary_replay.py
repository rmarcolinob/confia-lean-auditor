"""Frozen DEV responses only; no inference or audit recomputation."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('scope_replay', ROOT / 'scripts/evaluation/replay_tme_scope_boundary.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    import socket
    def forbidden(*args, **kwargs):
        pytest.fail('Offline replay attempted network access')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)


@pytest.fixture(scope='module')
def frozen():
    path = replay.SOURCE / 'model_b.jsonl'
    if not path.exists():
        pytest.skip('Frozen DEV outputs unavailable; never substitute another split')
    rows = {r['solution_id']: r for r in map(json.loads, path.read_text().splitlines())}
    def get(sid):
        packet = json.loads((replay.SOURCE / 'blind_packets' / (sid + '.json')).read_text())
        return rows[sid], packet['source_text']
    return get


def test_p5_02_removes_scope_credit_without_erasing_legitimate_d_proofs(frozen):
    row, text = frozen('TME2026P5_02')
    original = deepcopy(row)
    after = replay.replay_row(row, text)
    traces = {r['obligation_id']: r for r in after['reconciliation']}
    assert traces['c.four_product']['decision'] == 'indeterminate'
    assert traces['c.four_product']['reason'] == 'invalid_item_linkage'
    assert all(traces[o]['decision'] == 'supported' for o in ['d.four_sum', 'd.four_product'])
    assert after['potential_assessment']['score'] == '9'
    assert row['potential_assessment']['score'] == '11'
    c = next(i for i in after['potential_assessment']['items'] if i['item_id'] == 'c')
    counts = next(i for path in c['children'] for i in path['children'] if i['item_id'] == 'c.normal_counts')
    assert counts['points_awarded'] == '0' and counts['needs_review']
    assert row == original and after['api_calls'] == 0
    # Correct origin alone cannot manufacture a missing remote judgment.
    assert traces['d.list_twos']['decision'] == 'indeterminate'
    assert after['decision_provenance']['d.list_twos'] == 'missing_cached_gate'


@pytest.mark.parametrize('sid', ['TME2026P1_12', 'TME2026P4_19', 'TME2026P2_10'])
def test_original_contract_failures_and_timeout_remain_closed(frozen, sid):
    row, text = frozen(sid)
    after = replay.replay_row(row, text)
    assert after['original_provider_status'] == 'unavailable'
    assert after['potential_assessment'] == row['potential_assessment']
    assert after['potential_assessment']['score'] is None
    assert after['potential_assessment']['needs_review']
    assert not any(t['evidence_tier'] == 'SEMANTIC_SUPPORTED' for t in after['reconciliation'])
    assert after['api_calls'] == 0


def test_cached_positive_cannot_survive_removal_or_movement_of_its_source_span():
    def link(start, text):
        return dict(context=dict(valid=True), linkage=dict(valid=True, bindings=[dict(
            evidence_id='E001', authorized_slices=[dict(source_start=start, source_end=start+len(text), exact_text=text)])]))
    old = link(5, '2*2=4')
    assert replay.authorized_basis_preserved(old, link(0, 'texto2*2=4 fim'))
    assert not replay.authorized_basis_preserved(old, link(6, '2*2=4'))
    assert not replay.authorized_basis_preserved(old, link(5, '2*2=5'))
    assert not replay.authorized_basis_preserved(old, link(5, '2*2='))
    invalid = link(5, '2*2=4'); invalid['context']['valid'] = False
    assert not replay.authorized_basis_preserved(old, invalid)
