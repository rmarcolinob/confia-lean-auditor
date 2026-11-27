"""Literal RHS attribution; semantic opinions are simulated, Lean is separate."""
from pathlib import Path
import pytest

from confia_lean_auditor.student_claims.extract_f2q1_student_claims import extract_f2q1_student_claims
from confia_lean_auditor.student_claims.grounding import representation_matches
from confia_lean_auditor.claims.common.adapters import claim_from_student

FORMS = [('correct', '(a+b)x-a'), ('wrong_const_sign', '(a+b)x+a'),
         ('wrong_coeff_minus', '(a-b)x-a'), ('wrong_coeff_swapped_minus', '(b-a)x-a')]


@pytest.mark.parametrize('kind,formula', FORMS)
@pytest.mark.parametrize('prefix', ['p(x) = ', 'Assim p(x) ≡ -1+a(x-1)+bx+1 = '])
def test_complete_rhs_is_grounded_independently_of_its_truth(kind, formula, prefix):
    source = prefix + formula + '.'
    claim = next(c for c in extract_f2q1_student_claims(source) if c.claim_type == 'f2q1_student_reduced_form')
    assert claim.data['form_kind'] == kind
    record = claim_from_student(claim, solution_text=source)
    assert record.source.attributable and record.source.grounding_status == 'grounded'
    assert source[record.source.source_start:record.source.source_end] == record.source.raw_text
    assert not record.verification_results  # Grounding is not mathematical verification.


@pytest.mark.parametrize('source', [
    'p(x) = (a+b)x-a+1.', 'p(x) = 2*(a+b)x-a.',
    'p(x) <= (a+b)x-a.', 'p(x) >= (a+b)x-a.', 'p(x) != (a+b)x-a.',
    'p(x) = (a+b)x-a/2.', 'p(x) = (a+b)x-ab.',
])
def test_subexpressions_and_inequalities_are_not_the_asserted_remainder(source):
    assert not representation_matches('f2q1_student_reduced_form',
        {'form_kind':'correct', 'formula_text':'(a+b)x-a'}, source)


@pytest.mark.parametrize('source', [
    'Suponha que p(x) = (a+b)x-a.', 'Talvez p(x) = (a+b)x-a.',
    'Tentativa errada: p(x) = (a+b)x-a.', 'Não é verdade que p(x) = (a+b)x-a.',
    'O enunciado diz: p(x) = (a+b)x-a.', '"p(x) = (a+b)x-a."',
])
def test_rhs_does_not_bypass_attribution_gates(source):
    records = [claim_from_student(c, solution_text=source) for c in extract_f2q1_student_claims(source)]
    assert records and not any(r.source.attributable for r in records)


def test_real_context_routes_chain_to_minimal_fallback_without_awarding_points():
    from confia_lean_auditor.main import validate_problem_assets
    from confia_lean_auditor.claims.common.rubric_bridge import RubricClaimContext
    from confia_lean_auditor.claims.extractors.ita2025f2q1 import extract_claims_ita2025f2q1
    from confia_lean_auditor.core.schemas import RubricAssessment, RubricItemResult
    from confia_lean_auditor.semantic_policy.ita import apply
    root = Path(__file__).resolve().parents[1]
    assets = validate_problem_assets(root/'problems/ITA2025F2Q1', 'ITA2025F2Q1')
    source = 'Assim p(x) ≡ -1+a(x-1)+bx+1 = (a+b)x-a.'
    context = RubricClaimContext(problem_id=assets.problem.id, solution_text=source,
        extraction=extract_claims_ita2025f2q1(source), students=extract_f2q1_student_claims(source),
        checks=[], rubric_config=assets.rubric, statement_text=assets.problem.statement,
        correct_answer=assets.problem.correct_answer)
    criterion = next(c for c in assets.rubric.items if c.id == 'reduced_polynomial_form')
    item = RubricItemResult(id=criterion.id, description=criterion.description,
                           detected=False, points=None, max_points=criterion.points)
    calls = []
    def simulated(request):
        calls.append(request)
        return dict(decision='review', quotes=[source], justification='Provider simulado: teste de encaminhamento, sem julgamento matemático.')
    result = apply(rubric=RubricAssessment(score=None, max_score=criterion.points, items=[item]),
        solution=source, assets=assets, microclaims=[], student_claim_checks=[],
        claim_context=context, provider=simulated)
    assert len(calls) == 1
    assert calls[0]['criterion']['id'] == criterion.id
    assert any(e['source_text'] == source for e in calls[0]['evidence'])
    assert result.score is None and result.items[0].points is None


@pytest.mark.parametrize('kind,formula,status', [
    ('correct', '(a+b)x-a', 'verified'),
    ('wrong_coeff_minus', '(a-b)x-a', 'refuted'),
])
def test_existing_lean_checker_verifies_the_written_rhs(kind, formula, status):
    from uuid import uuid4
    from confia_lean_auditor.lean.student_claim_checkers.ita2025f2q1 import check_f2q1_student_claims
    source = f'Assim p(x) ≡ -1+a(x-1)+bx+1 = {formula}.'
    claims = extract_f2q1_student_claims(source)
    checks = check_f2q1_student_claims(claims, run_id='pytest_rhs_' + uuid4().hex)
    check = next(c for c in checks if c.claim_type == 'f2q1_student_reduced_form')
    assert check.data['form_kind'] == kind
    assert check.grounding['source_text'] == source
    assert check.status == status
    if status == 'verified':
        assert check.compiled and check.formal_status == 'verified'
    else:
        assert check.refutation_verified
