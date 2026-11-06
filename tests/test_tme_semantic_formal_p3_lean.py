"""Real Lean through semantic projection; only interpretation uses a test provider."""
import json
import pytest
from confia_lean_auditor.experimental.tme_semantic_formal_p3.engine import evaluate
from test_tme_semantic_formal_p3 import PROBLEM_ID,COMPLETE_C,typed_claims,provider,result,award

def real(text,tmp_path):
    r=evaluate('p3-semantic-real',PROBLEM_ID,text,extraction_provider=provider(typed_claims(text)),use_lean=True)
    (tmp_path/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    return r

@pytest.mark.parametrize('oid,text',[
 ('a.first_white_probability','a) primeira_branca: 2/6=1/3'),
 ('b.second_white_probability','b) segunda_branca: (10+1)/36=11/36'),
 ('c.conditional_success_1','c) '+COMPLETE_C),
 ('c.conditional_success_2','c) '+COMPLETE_C),
 ('c.total_win_probability','c) '+COMPLETE_C)])
def test_each_five_lean_capable_ids_proves_real_bound_equality(oid,text,tmp_path):
    r=real(text,tmp_path);v=result(r,oid)
    assert v['formal_status']=='FORMAL_VERIFIED' and v['formal_attempted']
    assert v['checker_result']['compiled'] and v['checker_result']['grounding']['source_text'] in text
    assert award(r,oid)['eligible'] and not r['fallback']

@pytest.mark.parametrize('oid,text',[
 ('a.first_white_probability','a) inferiores_brancas: 2\nprimeira_branca: 2/6=1/2'),
 ('b.second_white_probability','b) segunda_branca: (10+1)/36=1/2'),
 ('c.total_win_probability','c) '+COMPLETE_C.replace('+(1/6)*(1/2)=1/6','+(1/6)*(1/2)=1/3'))])
def test_real_refutation_not_overwritten(oid,text,tmp_path):
    r=real(text,tmp_path);v=result(r,oid)
    assert v['formal_status']=='FORMAL_REFUTED' and v['checker_result']['refutation_verified']
    assert v['mathematical_refutation'] and not award(r,oid)['eligible']
    if oid.startswith('a.'):assert r['score']==2
    if oid.startswith('c.'):assert r['score']==6

def test_true_lean_equality_with_false_partition_has_no_credit(tmp_path):
    r=real('b) segunda_branca: (9+2)/36=11/36',tmp_path);v=result(r,'b.second_white_probability')
    assert v['formal_status']=='FORMAL_VERIFIED' and v['checker_result']['compiled']
    assert v['status']=='COMPOSITE_FAILED' and r['score']==0

def test_conflicting_value_and_real_refutation_preserve_other_credit(tmp_path):
    r=real('a) inferiores_brancas: 2\nb) segunda_branca: 11/36\nsegunda_branca: (10+1)/36=1/2',tmp_path)
    assert r['score']==2 and r['conflicts']
    assert {v['formal_status'] for v in r['verification_results']}=={'FORMAL_NOT_ATTEMPTED','FORMAL_REFUTED'}

@pytest.mark.parametrize('tactic,formal,technical',[('skip','FORMAL_UNPROVED',False),
    ('exact p3_test_missing_identifier','FORMAL_ERROR',True)])
def test_real_failure_lifecycle_and_numeric_closure(monkeypatch,tmp_path,tactic,formal,technical):
    from confia_lean_auditor.lean.student_claim_checkers import rational_equality
    original=rational_equality.evaluate_student_proof
    def fault(**kw):
        kw['lean_code']=kw['lean_code'].replace('norm_num',tactic)
        kw['negation_code']=kw['negation_code'].replace('norm_num','skip')
        return original(**kw)
    monkeypatch.setattr(rational_equality,'evaluate_student_proof',fault)
    r=real('a) inferiores_brancas: 2\nprimeira_branca: 2/6=1/3',tmp_path);v=result(r,'a.first_white_probability')
    assert v['formal_status']==formal and v['formal_attempted'] and not v['mathematical_refutation']
    assert r['score']==2 and r['technical_uncertainty']==technical and not r['fallback']
    assert not v['checker_result']['compiled'] and not v['checker_result']['refutation_verified']

def test_checker_exception_is_local_not_extractor_fallback(monkeypatch,tmp_path):
    from confia_lean_auditor.lean.student_claim_checkers import tme2_p3
    def unavailable(*args,**kwargs):raise TimeoutError('injected checker transport failure')
    monkeypatch.setattr(tme2_p3,'check_rational_record',unavailable)
    r=real('a) inferiores_brancas: 2\nprimeira_branca: 2/6=1/3',tmp_path)
    assert r['score']==2 and r['technical_uncertainty'] and not r['fallback']
    v=result(r,'a.first_white_probability')
    assert v['formal_status']=='FORMAL_NOT_ATTEMPTED' and not v['formal_attempted']
    assert v['state']=='technical_error' and not v['mathematical_refutation']
