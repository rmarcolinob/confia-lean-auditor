"""Actual P2 projection→Lean runs; no mocked compiler, results or stdout."""
import json
import pytest
from confia_lean_auditor.experimental.tme_semantic_formal_p2.engine import evaluate
from confia_lean_auditor.experimental.tme_semantic_formal_p2.registry import REGISTRY,PROBLEM_ID
from test_tme_semantic_formal_p2 import sample,provider


def real(oid,tmp_path,value=None):
    text,claims=sample(oid,value)
    r=evaluate('semantic-real',PROBLEM_ID,text,extraction_provider=provider(claims),use_lean=True)
    (tmp_path/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    return r,next(v for v in r['verification_results'] if v['obligation_id']==oid)


@pytest.mark.parametrize('oid',[o for o,s in REGISTRY.items() if s.route=='FORMAL'])
def test_all_six_formal_routes_compile_the_bound_claim(oid,tmp_path):
    r,v=real(oid,tmp_path)
    assert v['status']=='FORMAL_VERIFIED' and v['formal_attempted'] is True,v
    assert v['checker_result']['compiled'] and not r['fallback_used']
    assert next(a for a in r['awards'] if a['obligation_id']==oid)['eligible']
    assert v['checker_result']['grounding']['source_text'] in r['source_text']
    print(oid,v['status'])


@pytest.mark.parametrize('oid,bad',[
 ('c.pair_permutations','4!=20'),('c.pair_orientations','2^4=8'),('c.counting_product','24*16=364')])
@pytest.mark.parametrize('correct',[True,False])
def test_three_composites_real_arithmetic_and_refutation(oid,bad,correct,tmp_path):
    r,v=real(oid,tmp_path,None if correct else bad)
    arithmetic=next(c for c in v['subchecks'] if c['name']=='arithmetic')
    assert arithmetic['formal_attempted'] is True
    assert arithmetic['status']==('FORMAL_VERIFIED' if correct else 'FORMAL_REFUTED')
    assert arithmetic['checker_result']['compiled'] if correct else arithmetic['checker_result']['refutation_verified']
    assert v['status']==('COMPOSITE_VERIFIED' if correct else 'COMPOSITE_FAILED')
    assert next(a for a in r['awards'] if a['obligation_id']==oid)['eligible'] is correct
    assert not r['technical_uncertainty']
    print(oid,v['status'],arithmetic['status'])


@pytest.mark.parametrize('oid,value',[('b.admissible_center','2'),('b.sum_at_five','14')])
def test_false_formal_claim_is_refuted_not_unknown(oid,value,tmp_path):
    r,v=real(oid,tmp_path,value)
    assert v['status']=='FORMAL_REFUTED' and v['checker_result']['refutation_verified']
    assert not next(a for a in r['awards'] if a['obligation_id']==oid)['eligible']


def test_unrendered_formal_claim_is_not_attempted_and_not_credited(tmp_path):
    r,v=real('c.total',tmp_path,'384')
    assert v['status']=='FORMAL_NOT_ATTEMPTED' and v['formal_attempted'] is False
    assert not v['mathematical_refutation'] and r['score']==0


@pytest.mark.parametrize('proof,status,category',[
 ('skip','FORMAL_UNPROVED','UNSOLVED_GOALS'),
 ('exact p2_semantic_test_missing_identifier','FORMAL_ERROR','UNKNOWN_IDENTIFIER')])
def test_real_failure_diagnostics_survive_projection(monkeypatch,tmp_path,proof,status,category):
    # Fault injection changes only test tactics. The frozen lifecycle runs real
    # Lean for proof/refutation; no simulated execution or checker result.
    from confia_lean_auditor.lean.student_claim_checkers import tme2_p2
    original=tme2_p2.check_real_record
    def with_test_tactic(*args,**kwargs):
        return original(*args,**dict(kwargs,proof=proof,refutation='skip'))
    monkeypatch.setattr(tme2_p2,'check_real_record',with_test_tactic)
    r,v=real('b.sum_at_five',tmp_path)
    assert v['status']==status and v['formal_attempted'] is True
    assert v['checker_result']['failure_category']==category
    assert not v['checker_result']['compiled'] and not v['checker_result']['refutation_verified']
    assert r['technical_uncertainty'] is (status=='FORMAL_ERROR')
    assert r['score']==0
