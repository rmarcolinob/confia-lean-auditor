"""Real Lean total proofs/refutations and conflicts with explicit value evidence."""
import json
import pytest
from confia_lean_auditor.experimental.tme_semantic_formal_p2.engine import evaluate
from confia_lean_auditor.experimental.tme_semantic_formal_p2.registry import PROBLEM_ID
from test_tme_semantic_formal_p2 import claim,provider


def execute(expressions,tmp_path):
    text='c) '+'\n'.join('total: '+e for e in expressions)
    claims=[claim(text,'c.total',expression=e) for e in expressions]
    r=evaluate('partial-real',PROBLEM_ID,text,extraction_provider=provider(claims),use_lean=True)
    (tmp_path/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    return r


@pytest.mark.parametrize('expression,expected,score',[
 ('24*16=384','FORMAL_VERIFIED',1),('24*16=364','FORMAL_REFUTED',0)])
def test_real_total_equality(expression,expected,score,tmp_path):
    r=execute([expression],tmp_path);v=r['verification_results'][0]
    assert v['route']=='FORMAL' and v['status']==v['formal_status']==expected and v['formal_attempted'] is True
    assert v['checker_result']['compiled'] if score else v['checker_result']['refutation_verified']
    assert r['score']==score and isinstance(r['score'],float)
    assert not r['fallback_used']


def test_value_and_true_equality_do_not_duplicate_credit(tmp_path):
    r=execute(['384','24*16=384'],tmp_path)
    assert {v['status'] for v in r['verification_results']}=={'DETERMINISTIC_VERIFIED','FORMAL_VERIFIED'}
    assert not r['conflicts'] and r['score']==1
    assert [(c['rule_id'],c['points']) for c in r['credits']]==[('c.conclusion',1.0)]


@pytest.mark.parametrize('expressions',[
 ['384','24*16=364'],['24*16=364','384'],['385','24*16=384']])
def test_value_and_contradictory_equality_are_reconciled(expressions,tmp_path):
    r=execute(expressions,tmp_path)
    assert r['conflicts'] and r['conflicts'][0]['status']=='CONFLICTING_EVIDENCE'
    assert not r['conflicts'][0]['resolved'] and r['review_recommended']
    assert r['score']==0 and not next(a for a in r['awards'] if a['obligation_id']=='c.total')['eligible']
    if '384' in expressions:
        v=next(v for v in r['verification_results'] if v['status']=='FORMAL_REFUTED')
        assert v['checker_result']['refutation_verified'] and v['mathematical_refutation']
