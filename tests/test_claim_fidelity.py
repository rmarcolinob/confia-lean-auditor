"""P0: source correspondence is required independently of proposition truth."""
from dataclasses import asdict, replace
from importlib import import_module
import json
from pathlib import Path
import subprocess

import pytest

from confia_lean_auditor.student_claims.grounding import (
    select_bindings, ground_student_claims, has_valid_grounding, source_matches,
)
from confia_lean_auditor.student_claims.registry import extract_student_claims
from confia_lean_auditor.student_claims.schemas import StudentClaim, StudentClaimCheck, is_mathematically_refuted
from confia_lean_auditor.lean.student_proof import reconcile_attribution
from confia_lean_auditor.lean.student_claim_checkers.registry import check_student_claims_for_problem
from confia_lean_auditor.core.schemas import AuditResponse, RubricAssessment, RubricItemResult
from confia_lean_auditor.rubric.adjusters.registry import apply_student_claim_adjustments
from confia_lean_auditor.reports.report_builder import _build_check_evidence_items

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('source,expected', [
    ('Portanto a=-1 e b=3.', {'a':-1,'b':3}),
    ('b=18, a=-27.', {'a':-27,'b':18}),
    ('Na questão 42, temos a=9 e b=-8.', {'a':9,'b':-8}),
    ('Primeiro tentei a=3 e b=2, mas isso falha. Logo a=-1 e b=3.', {'a':-1,'b':3}),
    ('a=10 e b=11. Portanto a=20 e b=21.', {'a':20,'b':21}),
    ('a=-1, b=2-a=3. Portanto a vale -1 e b vale 3.', {'a':-1,'b':3}),
    ('Portanto a=−27 e b=18.', {'a':-27,'b':18}),
])
def test_local_bindings(source,expected):
    result,status,_=select_bindings(source,('a','b'))
    assert status=='grounded' and result[3]==expected
    assert source[result[0]:result[1]]==result[2]
    claim=next(c for c in extract_student_claims('ITA2025F2Q1',source) if c.claim_type.endswith('final_answer'))
    assert claim.data==expected and source_matches(claim,source)


@pytest.mark.parametrize('source',[
    'a=3 e b=2. a=-1 e b=3.',
    'a=3 e b=2 ou a=-1 e b=3.',
    'Logo a=1 e b=2. Portanto a=3 e b=4.',
])
def test_conflicting_candidates_never_choose_a_pair(source):
    claim=extract_student_claims('ITA2025F2Q1',source)[-1]
    assert claim.data=={} and claim.grounding['status']=='ambiguous'


@pytest.mark.parametrize('source',[
    'a=3. b=2.', 'a=2-1 e b=5+1.', 'b=2-a=3.',
    'Não é a=7 e b=8.', 'Se a=7 e b=8, temos algo.',
    'Tentei a=7 e b=8.', 'a+b=2 e a=1.',
    'a=1/2 e b=3.', 'a=1.5 e b=3.', 'a=1e3 e b=2.',
])
def test_incomplete_hypothetical_and_truncated_bindings_are_not_grounded(source):
    result,status,_=select_bindings(source,('a','b'))
    assert result is None and status=='unresolved'


def final_claim(source='Portanto a=-1 e b=3.'):
    return next(c for c in extract_student_claims('ITA2025F2Q1',source) if c.claim_type.endswith('final_answer'))


def test_missing_span_and_inconsistent_structure_block_lean(tmp_path,monkeypatch):
    module=import_module('confia_lean_auditor.lean.student_claim_checkers.ita2025f2q1')
    monkeypatch.setattr(module,'CHECK_DIR',tmp_path)
    def forbidden(*args,**kwargs): raise AssertionError('ungrounded claim reached Lean')
    monkeypatch.setattr(module,'_run_lean_file',forbidden)
    original=final_claim()
    for claim in (replace(original,grounding=None),replace(original,data={'a':3,'b':2}),
                  replace(original,grounding={**original.grounding,'source_text':'a=99 e b=100.'}),
                  replace(original,grounding={**original.grounding,'source_start':-1})):
        check=module.check_one_f2q1_student_claim(claim,'blocked',0)
        assert check.status=='unverified' and check.failure_category=='CLAIM_NOT_GROUNDED'
        assert check.lean_file is None and not check.refutation_verified
    assert not list(tmp_path.rglob('*.lean'))


def test_gate_validates_against_actual_audit_source(tmp_path,monkeypatch):
    module=import_module('confia_lean_auditor.lean.student_claim_checkers.ita2025f2q1')
    monkeypatch.setattr(module,'CHECK_DIR',tmp_path)
    monkeypatch.setattr(module,'_run_lean_file',lambda *a,**k: pytest.fail('wrong source reached Lean'))
    check=check_student_claims_for_problem('ITA2025F2Q1',[final_claim()],'blocked',solution='Portanto a=3 e b=2.')[0]
    assert check.status=='unverified'


def test_non_ab_binding_uses_same_parser():
    result,status,_=select_bindings('Logo y=12 e z=-34.',('y','z'))
    assert status=='grounded' and result[3]=={'y':12,'z':-34}


def test_historical_refutation_preserved_but_not_attributed():
    check=StudentClaimCheck('old','ITA2025F2Q1','f2q1_student_final_answer','a=3,b=2','','a=3 ∧ b=2','norm_num','refuted',False,'/old/positive.lean','','',data={'a':3,'b':2},refutation_verified=True,refutation_lean_file='/old/negative.lean')
    safe=reconcile_attribution(check)
    assert safe.status=='unverified' and safe.formal_status=='refuted'
    assert safe.refutation_verified and safe.refutation_lean_file==check.refutation_lean_file
    assert not is_mathematically_refuted(safe)
    assert _build_check_evidence_items([], [check])[0].result!='incorreta'


@pytest.mark.parametrize('n',[1,3,5,6,8])
def test_every_adjuster_rejects_ungrounded_refutation(n):
    module=import_module(f'confia_lean_auditor.rubric.adjusters.ita2025f2q{n}')
    mapping=getattr(module,f'F2Q{n}_STUDENT_CHECK_TO_RUBRIC_ITEMS')
    for kind,ids in mapping.items():
        rubric=RubricAssessment(score=10,max_score=10,items=[RubricItemResult(id=i,description=i,detected=False,points=None,max_points=2,mathematical_status='indeterminate') for i in ids])
        check={'claim_type':kind,'status':'refuted','refutation_verified':True,'refutation_lean_file':'/old/neg.lean'}
        result=apply_student_claim_adjustments(f'ITA2025F2Q{n}',rubric,[check])
        assert all(i.points is None and not i.student_check_adjusted for i in result.items)


def test_smoke_mismatch_offline_without_rewriting_artifacts(tmp_path,monkeypatch):
    smoke=ROOT/'artifacts/evaluations/ita1000_v1_2/smoke_20261027_stage2'
    paths=list(smoke.rglob('*ITA2025F2Q1_S001_L04*'))
    if not paths:
        pytest.skip('Original smoke artifact is local; the portable source fixture is tested separately')
    # The original run is identified from the recorded result, not regenerated.
    audit=ROOT/'artifacts/runs/20261027T145952_481754/audit.json'
    before=audit.read_bytes(); historical=json.loads(before)
    solution=(audit.parent/'solution.txt').read_text()
    claims=extract_student_claims('ITA2025F2Q1',solution)
    claim=next(c for c in claims if c.claim_type.endswith('final_answer'))
    assert claim.data=={'a':-1,'b':3} and source_matches(claim,solution)
    module=import_module('confia_lean_auditor.lean.student_claim_checkers.ita2025f2q1')
    monkeypatch.setattr(module,'CHECK_DIR',tmp_path)
    seen=[]
    def runner(path,**kwargs):
        seen.append(path.read_text())
        return subprocess.CompletedProcess([],0,'','')
    monkeypatch.setattr(module,'_run_lean_file',runner)
    check=module.check_one_f2q1_student_claim(claim,'offline',0)
    assert check.status=='verified' and len(seen)==1
    assert '(-1 : ℤ)' in check.lean_statement and '(3 : ℤ)' in check.lean_statement
    old=next(c for c in historical['student_claim_checks'] if c['claim_type'].endswith('final_answer'))
    assert old['data']=={'a':3,'b':2} and not is_mathematically_refuted(old)
    # Reading a historical response retains its exact field shape.
    parsed=AuditResponse.model_validate(historical).model_dump(mode='json')
    assert 'verification_scope' not in parsed['lean_certificate']
    assert audit.read_bytes()==before


@pytest.mark.parametrize('source', [
    'Não concluo que a=7 e b=8.',
    'Não aceito a resposta a=7 e b=8.',
    'A resposta a=7 e b=8 está errada.',
    'Talvez a=7 e b=8.',
])
def test_conclusion_cues_do_not_discard_negation(source):
    assert not any(has_valid_grounding(c) for c in extract_student_claims('ITA2025F2Q1',source))


@pytest.mark.parametrize('problem,source', [
    ('ITA2025F2Q8', 'det(A_k)=k+1.'),
    ('ITA2025F2Q6', 'A razão é n/(2n-6)(n+1).'),
    ('ITA2025F2Q1', 'x^14=1-x+7.'),
    ('ITA2025F2Q5', 'log10(3^100)=47.7000+1.'),
])
def test_truncated_formula_is_not_grounded(problem,source):
    claims=extract_student_claims(problem,source)
    assert claims, 'fixture must exercise an existing detector'
    assert not any(has_valid_grounding(c) for c in claims)


def test_unattributed_proof_remains_manifest_required(tmp_path):
    from confia_lean_auditor.submission_audits.artifacts import required_references
    from types import SimpleNamespace
    result=SimpleNamespace(artifact_dir=str(tmp_path), reproducibility=None, lean_certificate=None, formal_steps=[],
        student_claim_checks=[{'id':'old','status':'unverified','formal_status':'refuted',
                               'refutation_verified':True,'refutation_lean_file':str(tmp_path/'negative.lean')}])
    # required_references also requires a certificate; use the existing fixture
    # contract rather than relaxing witness validation.
    from confia_lean_auditor.core.schemas import LeanCertificate
    result.lean_certificate=LeanCertificate(status='unverified',compiled=False,exit_code=1,
        uses_forbidden_token=False,forbidden_tokens_found=[])
    _,refs=required_references(result)
    assert ('refutation','old',str(tmp_path/'negative.lean')) in refs


def test_portable_original_source_fixture():
    source=(ROOT/'tests/fixtures/f2q1_claim_fidelity.txt').read_text()
    claim=final_claim(source)
    assert claim.data=={'a':-1,'b':3} and source_matches(claim,source)
    assert claim.data!={'a':3,'b':2}


def test_log_value_cannot_be_borrowed_from_another_equation_in_same_clause():
    source='log10(3^100)=5 e k=47.7100.'
    claims=extract_student_claims('ITA2025F2Q5',source)
    assert claims and all(not has_valid_grounding(c) for c in claims)


@pytest.mark.parametrize('field,value',[('source_sha256',1),('source_start',False),('source_end',1.5),('extraction_method',[]),('source_text',None)])
def test_malformed_provenance_is_rejected_without_exception(field,value):
    claim=final_claim()
    claim.grounding={**claim.grounding,field:value}
    assert not has_valid_grounding(claim)
