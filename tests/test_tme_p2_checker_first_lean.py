"""Actual Lean/Mathlib executions. No provider or process mocks; no LLM."""
import json
from pathlib import Path
from uuid import uuid4

import pytest

from confia_lean_auditor.experimental.tme_p2_checker_first.engine import audit_p2_checker_first, arithmetic_status
from confia_lean_auditor.lean.student_claim_checkers.real_algebra import check_real_record
from confia_lean_auditor.student_claims.tme2_p2_digital import collect_tme2_p2_text
from confia_lean_auditor.student_claims.semantic import supplement_scope
from confia_lean_auditor.tme.obligation_experiment import deterministic_only


@pytest.mark.parametrize('key,good,bad,points',[
    ('pair_permutations','4!=24','4!=20',2),
    ('pair_orientations','2^4=16','2^4=8',2),
    ('counting_product','24*16=384','24*16=364',5),
])
@pytest.mark.parametrize('correct',[True,False])
def test_real_composite_arithmetic_and_refutation(key,good,bad,points,correct,tmp_path):
    source=key+': '+(good if correct else bad)
    r=audit_p2_checker_first({'c':source},use_lean=True,solution_id='real-'+uuid4().hex)
    c=next(c for c in r['checks'] if c['obligation_id']=='c.'+key)
    a=next(a for a in c['metadata']['components'] if a['name']=='arithmetic')
    assert a['formal_attempted'] is True and a['route']=='FORMAL'
    assert a['status']==('FORMAL_VERIFIED' if correct else 'FORMAL_REFUTED')
    proof=a['checker_result']
    assert proof['compiled'] if correct else proof['refutation_verified']
    file=Path(proof['lean_file'] if correct else proof['refutation_lean_file'])
    assert file.is_file() and ('¬ (' in file.read_text()) is (not correct)
    assert r['score']==(points if correct else 0) and not r['technical_uncertainty']
    assert c['metadata']['relation_supported']
    assert c['state']==('verified' if correct else 'refuted')
    (tmp_path/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    print(json.dumps(dict(source=source,component=a,score=r['score']),ensure_ascii=False))


def test_no_equality_is_formal_not_attempted_not_refuted(tmp_path):
    r=audit_p2_checker_first({'c':'pair_permutations: 4!'},use_lean=True)
    c=next(c for c in r['checks'] if c['obligation_id']=='c.pair_permutations')
    a=next(a for a in c['metadata']['components'] if a['name']=='arithmetic')
    assert a['formal_status']=='FORMAL_NOT_ATTEMPTED' and a['formal_attempted'] is False
    assert a['status']=='DETERMINISTIC_VERIFIED' and r['score']==2
    (tmp_path/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))


@pytest.mark.parametrize('proof,expected',[
    ('skip','FORMAL_UNPROVED'),
    ('exact p2_intentionally_missing_identifier','FORMAL_ERROR'),
])
def test_real_lean_inconclusive_and_technical_diagnostics(proof,expected,tmp_path):
    # Exercise the unchanged lifecycle with an actual generated P2 arithmetic
    # proposition and intentionally inadequate/invalid tactic. Not fake stdout.
    with supplement_scope(deterministic_only):
        digital=collect_tme2_p2_text({'c':'pair_permutations: 4!=24'})
        record=next(r for r in digital.records if r.canonical_form and r.canonical_form.subject=='pair_permutations')
        _,check=check_real_record(record,digital,collect=collect_tme2_p2_text,
            statement='((Nat.factorial 4 : ℕ) : ℤ) = (24 : ℤ)',proof=proof,refutation='skip',
            context={'scope':'test actual failure semantics of written factorial equality'},
            run_id='p2-epistemic-'+uuid4().hex,index=0,number_domain='Z')
    from dataclasses import asdict
    payload=asdict(check)
    status,attempted=arithmetic_status(check.status,payload)
    assert status==expected and attempted is True
    assert not check.compiled and not check.refutation_verified
    assert check.failure_category==('UNSOLVED_GOALS' if expected=='FORMAL_UNPROVED' else 'UNKNOWN_IDENTIFIER')
    (tmp_path/'proof-result.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    print(json.dumps(dict(status=status,checker=payload),ensure_ascii=False))
