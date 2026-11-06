"""Observed recorded regressions; never an independent benchmark or API call."""
import json
from pathlib import Path
import pytest
from confia_lean_auditor.experimental.tme_semantic_formal_p3.engine import evaluate

ROOT=Path(__file__).resolve().parents[1]
# Pre-implementation architectural counterfactuals (§8), not fitted labels.
PRIORITY={'p3_safe_s2_03':0,'p3_safe_s2_06':2,'p3_safe_s1_02':2,'p3_safe_s1_03':2,
          'p3_safe_s1_07':1,'p3_safe_s4_07':2,'p3_rob_e02':4,'p3_rob_e04':2,
          'p3_rob_a08':8,'p3_rob_e08':2}

@pytest.mark.parametrize('case_id,expected',PRIORITY.items())
def test_recorded_priority_replay_without_model(case_id,expected,tmp_path,monkeypatch):
    import openai
    def forbidden(*args,**kwargs):raise AssertionError('real extractor API forbidden in recorded regression')
    monkeypatch.setattr(openai,'OpenAI',forbidden)
    base=ROOT/'artifacts/evaluations/tme_p3_semantic_safety_02'
    paths=list(base.glob('*/tme_semantic_formal/'+case_id+'.json'))
    if not paths:pytest.skip('local historical artifact unavailable; cannot fabricate recorded response')
    original=json.loads(paths[0].read_text())
    def recorded(*args):return original['extractor']['raw_output'],dict(status='completed',api_calls=0,model='recorded')
    r=evaluate('recorded-'+case_id,'TME2026P3',original['source_text'],extraction_provider=recorded,use_lean=False)
    (tmp_path/'replay.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    assert r['score']==expected and not r['fallback'] and r['extractor']['api_calls']==0
    assert not r['technical_uncertainty']
    assert not any(d['hard_veto_eligible'] and set(d['discourse_states'])!={'ACTIVE'} for d in r['veto_decisions'])
    assert all(a['verification_result'].get('guard_only') is not True for a in r['awards'] if a['eligible'])
    if case_id in {'p3_safe_s1_02','p3_safe_s1_07','p3_safe_s4_07'}:
        assert any(e['original']['extractor_model']=='native' and e['decision']['resolved_discourse_state']=='SUPERSEDED' for e in r['discourse_ledger'])
    if case_id=='p3_safe_s2_06':
        assert {a['obligation_id'] for a in r['awards'] if a['eligible']}=={'b.different_favorable'}
        assert any(['b.same_compartment','b.second_white_probability'] in d['dependency_paths'] for d in r['veto_decisions'])
