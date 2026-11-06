"""Real Lean integration; no compiler/proof mocks in this module."""
import json
from pathlib import Path
import pytest
from confia_lean_auditor.experimental.tme_p3_checker_first.engine import audit_p3_checker_first

ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/'tests/fixtures/tme2_p3_digital/cases.json').read_text())


def run(text,tmp_path):
    r=audit_p3_checker_first({'b':text},use_lean=True)
    (tmp_path/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    return r


def arith(v):
    return next(c for c in v['metadata']['components'] if c['name']=='arithmetic')


@pytest.mark.parametrize('expression,formal,status,score',[
 ('(10+1)/36=11/36','FORMAL_VERIFIED','COMPOSITE_VERIFIED',2),
 ('(10+1)/36=1/2','FORMAL_REFUTED','COMPOSITE_FAILED',0),
 ('(9+2)/36=11/36','FORMAL_VERIFIED','COMPOSITE_FAILED',0)])
def test_real_arithmetic_does_not_replace_model_relation(expression,formal,status,score,tmp_path):
    r=run('segunda_branca: '+expression,tmp_path);v=r['checks'][0];a=arith(v)
    assert a['status']==formal and a['formal_attempted']
    assert a['checker_result']['compiled'] if formal=='FORMAL_VERIFIED' else a['checker_result']['refutation_verified']
    assert v['status']==status and r['score']==score


@pytest.mark.parametrize('reverse',[False,True])
def test_real_refutation_and_value_conflict(reverse,tmp_path):
    rows=['segunda_branca: 11/36','segunda_branca: (10+1)/36=1/2']
    r=run('\n'.join(rows[::-1] if reverse else rows),tmp_path)
    assert r['conflicts'] and r['score']==0 and r['review_recommended']
    assert {arith(v)['formal_status'] for v in r['checks']}=={'FORMAL_NOT_ATTEMPTED','FORMAL_REFUTED'}


@pytest.mark.parametrize('case_id',['b_official','b_tree'])
def test_real_legacy_complete_methods_still_score_eight(case_id,tmp_path):
    c=next(c for c in CASES if c['id']==case_id);r=run(c['text'],tmp_path)
    v=next(v for v in r['checks'] if v['obligation_id']=='b.second_white_probability')
    assert arith(v)['status']=='FORMAL_VERIFIED' and r['score']==8


def test_real_correct_value_and_equality_do_not_duplicate_credit(tmp_path):
    r=run('segunda_branca: 11/36\nsegunda_branca: (10+1)/36=11/36',tmp_path)
    assert r['score']==2 and not r['conflicts']
    assert {arith(v)['status'] for v in r['checks']}=={'DETERMINISTIC_VERIFIED','FORMAL_VERIFIED'}
