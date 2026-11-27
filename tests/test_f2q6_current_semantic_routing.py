"""The current policy may review an explicit argument omitted by the legacy extractor.
No synthetic decision in this file is a real GPT opinion or a Lean certificate.
"""
from pathlib import Path
import pytest
from confia_lean_auditor.claims.extractors.ita2025f2q6 import extract_claims_ita2025f2q6
from confia_lean_auditor.claims.common.rubric_bridge import RubricClaimContext
from confia_lean_auditor.core.schemas import RubricAssessment, RubricItemResult
from confia_lean_auditor.main import validate_problem_assets, extract_student_claims
from confia_lean_auditor.semantic_policy.ita import apply

SOURCE = ('A quarta cara no n-esimo lançamento exige 3 caras nos n-1 primeiros '
          'lançamentos e cara no último. Assim P(N=n)=C(n-1,3)/2^n. '
          'A razão P(n+1)/P(n)=n/(2n-6). Ela é maior que 1 para n<6, '
          'igual a 1 em n=6 e menor que 1 para n>6. Portanto, n=6 e n=7.')


@pytest.mark.parametrize('decision', ['met','not_met','review','error'])
def test_explicit_maximum_argument_is_eligible_without_expanding_reference_proofs(decision):
    root = Path(__file__).resolve().parents[1]
    assets = validate_problem_assets(root/'problems/ITA2025F2Q6', 'ITA2025F2Q6')
    extraction = extract_claims_ita2025f2q6(SOURCE)
    assert 'maximizers_identification' not in {c.type for c in extraction.claims}
    context = RubricClaimContext(problem_id=assets.problem.id, solution_text=SOURCE,
        extraction=extraction, students=extract_student_claims(assets.problem.id,SOURCE),
        checks=[], rubric_config=assets.rubric, statement_text=assets.problem.statement,
        correct_answer=assets.problem.correct_answer)
    criterion = next(c for c in assets.rubric.items if c.id == 'maximizers_identification')
    item = RubricItemResult(id=criterion.id, description=criterion.description,
        detected=False, points=None, max_points=criterion.points)
    calls=[]
    def provider(request):
        calls.append(request)
        if decision == 'error':raise TimeoutError('synthetic provider unavailable')
        return dict(decision=decision, quotes=[SOURCE],
                    justification='SIMULAÇÃO de decisão para verificar encaminhamento e aplicação da pauta.')
    result = apply(rubric=RubricAssessment(score=None, max_score=criterion.points, items=[item]),
        solution=SOURCE, assets=assets, microclaims=[], student_claim_checks=[], claim_context=context, provider=provider)
    assert len(calls) == 1 and calls[0]['solution'] == SOURCE
    assert calls[0]['criterion'] == criterion.model_dump(mode='json')
    assert 'n<6' in calls[0]['solution'] and 'n>6' in calls[0]['solution']
    assert calls[0]['evidence']
    assert all(SOURCE[e['source_start']:e['source_end']] == e['source_text'] for e in calls[0]['evidence'])
    expected = criterion.points if decision == 'met' else 0 if decision == 'not_met' else None
    assert result.items[0].points == expected
    assert result.secondary_adjudication['criteria'][criterion.id]['formal_certification'] is False
