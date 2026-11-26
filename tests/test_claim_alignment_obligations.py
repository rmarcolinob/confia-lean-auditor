"""Cross-pipeline content alignment without expected-answer fabrication."""
from pathlib import Path
import pytest

from confia_lean_auditor.claims.common.adapters import claim_from_extracted, claim_from_student
from confia_lean_auditor.claims.common.alignment import align_claims, align_obligations
from confia_lean_auditor.claims.common.rubric_bridge import RubricClaimContext
from confia_lean_auditor.claims.common.schemas import Origin
from confia_lean_auditor.claims.extract_claims import extract_claims
from confia_lean_auditor.core.problem_assets import validate_problem_assets
from confia_lean_auditor.core.schemas import ExtractedClaim
from confia_lean_auditor.core.math_canonical.models import EquivalenceResult
from confia_lean_auditor.student_claims.registry import extract_student_claims_for_audit
from confia_lean_auditor.rubric.rubric_evaluator import evaluate_rubric

ROOT=Path(__file__).resolve().parents[1]


def reference(text, expression='x=2', kind='historical_equation', identifier='ref', criterion='criterion'):
    return claim_from_extracted(ExtractedClaim(id=identifier,type=kind,text='reference',
        evidence='heuristic reference, not a student quote',confidence=.5,
        normalized={'equation':expression}),problem_id='ANY',solution_text=text,rubric_links=(criterion,))


def students(text):
    return [claim_from_student(c,solution_text=text) for c in extract_student_claims_for_audit('ANY',text)]


def context(pid,text,*,answer=None,checks=()):
    assets=validate_problem_assets(ROOT/'problems'/pid,pid)
    extraction=extract_claims(pid,text)
    prepared=RubricClaimContext(problem_id=pid,solution_text=text,extraction=extraction,
        students=extract_student_claims_for_audit(pid,text),checks=checks,rubric_config=assets.rubric,
        statement_text=assets.problem.statement,correct_answer=assets.problem.correct_answer if answer is None else answer)
    return assets,extraction,prepared


@pytest.mark.parametrize('text',['x=2','2=x','2x=4','x+1=3','x = 2.'])
def test_same_proposition_historical_type_and_different_syntax(text):
    r=reference(text)
    result=align_claims(r,students(text),solution_text=text)
    assert result.status=='aligned' and result.alignment_basis=='canonical_equivalence'
    assert r.provenance.origin==Origin.REFERENCE_EXPECTED and not r.source.attributable


@pytest.mark.parametrize('text',['a=-1,b=3','b=3 e a=-1','a é menos um e b é três'])
@pytest.mark.parametrize('kind',['final_answer','coefficient_solution','coefficient_assignment'])
def test_reordered_bindings_use_structured_semantics(text,kind):
    r=claim_from_extracted(ExtractedClaim(id='expected',type=kind,text='reference',evidence='reference',
        confidence=1,normalized={'b':'3','a':'-1'}),problem_id='ANY',solution_text=text)
    result=align_claims(r,students(text),solution_text=text)
    assert result.status=='aligned' and result.alignment_basis=='structured_equivalence'


@pytest.mark.parametrize('text,expected,status',[
    ('x=3','x=2','conflicting'),('x+1=4','x+1=3','conflicting'),
    ('x^2=4','x=2','unmatched'),('y=2','x=2','unmatched'),
    ('x=2. x=3.','x=2','ambiguous'),('Suponha x=2.','x=2','unmatched'),
    ('"x=2"','x=2','unmatched')])
def test_false_matches_and_context_are_not_promoted(text,expected,status):
    assert align_claims(reference(text,expected),students(text),solution_text=text).status==status


def test_wrong_bindings_are_explicit_conflict_not_a_match():
    text='a=3,b=2'
    r=claim_from_extracted(ExtractedClaim(id='same-id',type='coefficient_solution',text='reference',
        evidence='reference',confidence=1,normalized={'a':'-1','b':'3'}),problem_id='ANY',solution_text=text)
    result=align_claims(r,students(text),solution_text=text)
    assert result.status=='conflicting' and result.alignment_basis=='structured_equivalence'


def test_unknown_equivalence_does_not_become_equivalent(monkeypatch):
    import confia_lean_auditor.claims.common.compatibility as module
    monkeypatch.setattr(module,'compare_canonical',lambda *args:EquivalenceResult('unknown','controlled unknown'))
    assert align_claims(reference('x=2'),students('x=2'),solution_text='x=2').status=='unmatched'


@pytest.mark.parametrize('same_criterion',[False,True])
def test_multiple_expected_obligations_are_not_selected_by_position(same_criterion):
    text='x=2'
    refs=[reference(text,identifier='one',criterion='one'),
          reference(text,'2x=4',identifier='two',criterion='one' if same_criterion else 'two')]
    forward=align_obligations(refs,students(text),solution_text=text)
    reverse=align_obligations(list(reversed(refs)),students(text),solution_text=text)
    expected='aligned' if same_criterion else 'ambiguous'
    assert all(r.status==expected for r in (*forward,*reverse))


def test_missing_expected_math_stays_unmatched():
    text='x=2'
    r=reference(text,'identifica corretamente o passo final')
    assert r.canonical_form is None
    assert align_claims(r,students(text),solution_text=text).status=='unmatched'


@pytest.mark.parametrize('text', ['a=-1,b=3','b=3 e a=-1','Logo a vale -1 e b vale 3.'])
def test_f2q1_expected_binding_aligns_naturally(text):
    _,_,c=context('ITA2025F2Q1',text)
    expected=c.expected['final_answer'];result=c.alignment(expected)
    assert result.status=='aligned' and result.alignment_basis
    assert expected.expected_obligation.criterion_id=='final_answer'
    assert expected.expected_obligation.expected_payload=={'a':'-1','b':'3'}


@pytest.mark.parametrize('text,status',[
    ('O primeiro algarismo de 3^100, da esquerda para a direita, é 5.','aligned'),
    ('O primeiro algarismo é 5.','aligned'),
    ('O primeiro algarismo é 4.','conflicting'),
    ('O último algarismo é 5.','unmatched'),
    ('O primeiro algarismo de 2^100 é 5.','unmatched'),
    ('5 não é o algarismo.','unmatched'),
    ('O primeiro algarismo não é 5.','unmatched')])
def test_digit_quantity_semantics_and_source_context(text,status):
    _,_,c=context('ITA2025F2Q5',text)
    r=c.alignment(c.expected['final_digit'])
    assert r.status==status
    if status=='aligned':assert r.alignment_basis in {'structured_values','structured_equivalence'}


def test_f2q5_bridge_checks_expected_value_and_retains_all_microclaims():
    text='O primeiro algarismo de 3^100, da esquerda para a direita, é 5.'
    assets,extraction,c=context('ITA2025F2Q5',text)
    result=evaluate_rubric(ROOT,'ITA2025F2Q5',extraction,[],assets.rubric,solution_text=text,
        statement_text=assets.problem.statement,claim_context=c)
    final=result.items[-1]
    assert final.points==2 and final.positive_evidence['student_bridge']['verification_basis']=='deterministic_expected_value'
    assert all(i.points is None for i in result.items[:-1])
    from confia_lean_auditor.rubric.positive_evidence import can_support_rubric_credit
    required=assets.rubric.items[-1].model_copy(update={'required_microclaim_ids':['missing']})
    assert not can_support_rubric_credit(problem_id='ITA2025F2Q5',item=required,claim=None,
        solution_text=text,statement_text=assets.problem.statement,claim_context=c)['supported']


def test_f2q3_canonical_regression():
    _,_,c=context('ITA2025F2Q3','Assim, cos beta = sen beta + 1/2.')
    result=c.alignment(c.expected['beta_difference'])
    assert result.status=='aligned' and result.alignment_basis=='canonical_equivalence'


def test_q4_no_student_content_remains_unmatched():
    _,_,c=context('ITA2025Q4','não sei fazer')
    assert c.students==()
    assert not any(c.alignment(r).status=='aligned' for r in (*c.references,*c.expected_records))


def test_vague_expected_answer_is_not_inferred_from_student():
    _,_,c=context('ITA2025F2Q5','O primeiro algarismo é 5.',answer='identifica corretamente o resultado')
    assert 'final_digit' not in c.expected


def test_expected_variant_metadata_preserves_microclaims_and_original_ids():
    assets,_,c=context('ITA2025Q1','a^2-2a+5=200. Logo a=15.')
    variants=c.expected_by_criterion['equation']
    assert len(variants)==3
    required=next(i.required_microclaim_ids for i in assets.rubric.items if i.id=='equation')
    assert all(r.expected_obligation.required_microclaim_ids==tuple(required) for r in variants)
    assert all(r.provenance.origin==Origin.REFERENCE_EXPECTED and not r.source.attributable for r in variants)


def test_intermediate_polynomial_is_not_a_competing_final_assignment():
    _,_,c=context('ITA2025Q1','a^2-2a-195=0. Logo a=15.')
    result=c.alignment(c.expected['final_answer'])
    assert result.status=='aligned'
    assert len(result.preferred_attribution_ids)==1


def test_linear_wrong_final_assignment_is_still_a_conflict():
    _,_,c=context('ITA2025Q1','Logo 2a=28.')
    assert c.alignment(c.expected['final_answer']).status=='conflicting'
