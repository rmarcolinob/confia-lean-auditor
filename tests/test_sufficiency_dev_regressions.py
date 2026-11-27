"""Known DEV failures. Assertions use the actual frozen shadow, never a mock judge.

Run after the live gate. Before that the live-dependent checks are explicitly
skipped; fixture/protocol tests still run. No HOLDOUT data or API calls here.
"""
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/'tests/fixtures/tme_semantic_sufficiency_dev.json').read_text())
OUT=ROOT/'artifacts/evaluations/tme_semantic_sufficiency_01'


def test_frozen_known_failures_have_exact_classified_scope():
    assert len(CASES)==21
    assert sum(c['historical_kind']=='FALSE_CREDIT' for c in CASES)==15
    assert sum(c['historical_kind']=='FALSE_ATTRIBUTION' for c in CASES)==6
    assert all(c['source'] and c['error_class'] and not c['expected_reconciled_support'] for c in CASES)


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['solution_id']+':'+c['obligation_id'])
def test_known_dev_failure_is_eliminated_in_actual_shadow(case):
    path=OUT/'shadow'/f"{case['solution_id']}.json"
    if not path.exists():pytest.skip('Actual independent gate shadow has not run yet')
    row=json.loads(path.read_text())
    decision=next(t for t in row['reconciliation'] if t['obligation_id']==case['obligation_id'])
    assert decision['decision']!='supported', (case['error_class'],decision['sufficiency'],decision['reason'])
