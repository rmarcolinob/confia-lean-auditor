"""Offline replay of S071: recorded Lean/GPT outcomes, unchanged real rubric.

The missing remainder opinion is explicitly simulated, not a recorded GPT call.
Only external outcomes are substituted; extraction, grounding, rubric, policy,
aggregation, report and publication execute through the production pipeline.
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from test_score_policy_api import isolated_engine
from confia_lean_auditor.core.schemas import AuditRequest, AuditResponse
from confia_lean_auditor.student_claims.schemas import StudentClaimCheck
from confia_lean_auditor.semantic_policy import ita, service
from tests.audit_contract import assert_score_contract

FIXTURE = Path(__file__).parent / 'fixtures/ita_s071_real_run'
SOURCE = (FIXTURE / 'solution.txt').read_text()
RECORDED = json.loads((FIXTURE / 'audit.json').read_text())
REMAINDER_QUOTE = 'Assim p(x) ≡ 1 + a(x − 1) + bx + 1 = ax + a + bx + 2 = (a + b)x + (a + 2).'
REMAINDER_OPINION = dict(decision='not_met', quotes=[REMAINDER_QUOTE],
    justification='Replay offline simulado: o resto geral escrito (a+b)x+(a+2) '
    'não é (a+b)x-a. A redução x⁵⁷≡1 e a expansão a(x−1)=ax+a estão incorretas; '
    'os erros não se cancelam como identidade em a e b.')


@pytest.fixture
def replay(isolated_engine, monkeypatch):
    import confia_lean_auditor.main as main
    from confia_lean_auditor.rubric import secondary_adjudicator
    saved = AuditResponse.model_validate(RECORDED)
    monkeypatch.setenv('CONFIA_SPECIALIZED_POLICY', service.VERSION)
    monkeypatch.setattr(main, 'evaluate_formal_steps', lambda **_: copy.deepcopy(saved.formal_steps))
    raw = saved.lean_certificate.model_dump(exclude={'verification_scope'})
    monkeypatch.setattr(main, 'run_lean_file', lambda *a, **k: copy.deepcopy(raw))
    # Microclaim evaluation is real: its inputs retain the observed exit 124.
    checks = copy.deepcopy(saved.student_claim_checks)
    for check in checks:
        if check.get('lean_file'):
            check['lean_file'] = str(FIXTURE / 'student_claim_checks' / Path(check['lean_file']).name)
    monkeypatch.setattr(main, 'check_student_claims_for_problem',
        lambda **_: [StudentClaimCheck(**c) for c in copy.deepcopy(checks)])
    monkeypatch.setattr(secondary_adjudicator, 'adjudicate',
        lambda *_: pytest.fail('Legacy adjudication must not run'))
    calls = []

    def execute(remainder=REMAINDER_OPINION):
        def provider(self, request):
            cid = request['criterion']['id']
            calls.append(request)
            assert request['solution'] == SOURCE
            assert cid != 'final_answer', 'A decided criterion must not be adjudicated again'
            if cid == 'reduced_polynomial_form':
                if isinstance(remainder, Exception):
                    raise remainder
                return copy.deepcopy(remainder)
            return copy.deepcopy(RECORDED['rubric_assessment']['secondary_adjudication']['criteria'][cid]['response'])
        monkeypatch.setattr(service.SemanticProvider, '__call__', provider)
        return main.execute_audit(AuditRequest(problem_id='ITA2025F2Q1', solution=SOURCE)), calls
    return execute


def test_original_failure_and_fixture_integrity():
    for name, expected in json.loads((FIXTURE / 'source_manifest.json').read_text())['files'].items():
        assert hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() == expected
    rubric = RECORDED['rubric_assessment']
    assert RECORDED['score'] is None
    assert [i['suggested_points'] for i in rubric['items']] == [0, None, 0, 2]
    assert [i['points'] for i in rubric['items']] == [None, None, None, 2]
    assert rubric['secondary_adjudication']['criteria']['reduced_polynomial_form'] == {
        'decision': 'review', 'reason': 'no_eligible_evidence'}


def test_real_replay_decides_zero_preserves_final_answer_and_timeout(replay):
    result, calls = replay()
    assert [r['criterion']['id'] for r in calls] == ['power_reductions', 'reduced_polynomial_form', 'coefficient_system']
    assert [i.points for i in result.rubric_assessment.items] == [0, 0, 0, 2]
    assert result.score == 2
    assert_score_contract(result.model_dump(mode='json'))
    rubric = result.rubric_assessment
    assert rubric.assessment_status == 'complete' and rubric.evaluated_max_score == 10
    assert rubric.coverage == .2 and rubric.estimated_points == 0 and rubric.needs_review
    assert rubric.unscorable_reason is None
    for item in rubric.items[:3]:
        assert item.mathematical_status == 'refuted'
        assert item.verified_points is None and item.scoring_basis == 'semantic_fallback'
        assert rubric.secondary_adjudication['criteria'][item.id]['formal_certification'] is False
    assert result.formal_steps[0].status == 'lean_timeout' and result.formal_steps[0].exit_code == 124
    assert rubric.items[2].verification_status == 'technical_error'
    final = rubric.items[-1]
    assert final.scoring_basis == 'first_pass' and final.verified_points == 2
    assert final.positive_evidence['reference_dependencies'] == []
    for span in final.positive_evidence['source_spans']:
        assert SOURCE[span['source_start']:span['source_end']] == span['source_text']
        assert 'a = −1 e b = 3' in span['source_text']
        assert span['student_claim_id'].startswith('student:')
    remainder = calls[1]
    assert any(REMAINDER_QUOTE in e['source_text'] for e in remainder['evidence'])
    assert remainder['checks'] == []  # No fabricated checker/structured claim.
    persisted = AuditResponse.model_validate_json((Path(result.artifact_dir)/'audit.json').read_text())
    assert persisted.score == result.score
    catalog = json.loads((Path(result.artifact_dir)/'math_claims.json').read_text())
    assert [c['scoring_basis'] for c in catalog['criterion_traces']] == ['semantic_fallback']*3 + ['first_pass']


@pytest.mark.parametrize('opinion, points, score', [
    (dict(decision='met', justification='Controle simulado de crédito, não parecer sobre S071.', quotes=[REMAINDER_QUOTE]), 3, 5),
    (dict(decision='review', justification='Ambiguidade material no controle simulado.', quotes=[REMAINDER_QUOTE]), None, None),
    (TimeoutError('offline provider failure'), None, None),
    (dict(decision='not_met', justification='Resposta inválida.', quotes=['Trecho que não está na solução.']), None, None),
])
def test_external_outcome_variants_keep_real_pending_states(replay, opinion, points, score):
    result, calls = replay(opinion)
    assert len(calls) == 3
    assert [i.points for i in result.rubric_assessment.items] == [0, points, 0, 2]
    assert result.score == score
    assert_score_contract(result.model_dump(mode='json'))
    assert result.rubric_assessment.items[1].verified_points is None
    assert result.coverage == .2
    if points is None:
        assert result.rubric_assessment.items[1].mathematical_status == 'indeterminate'
        assert result.unscorable_reason and result.needs_review


def test_mathematical_expected_outcome_comes_from_original_rubric():
    # Independent exact polynomial arithmetic modulo x²-x+1, not the extractor.
    def power(n):
        c, d = 1, 0
        for _ in range(n):
            c, d = -d, c+d
        return c, d
    assert power(57) == (-1, 0) and power(14) == (-1, 1) and power(7) == (0, 1)
    # General coefficients: constant=-a; x coefficient=a+b.
    a, b = -1, 3
    remainder = tuple(power(57)[k] + a*power(14)[k] + b*power(7)[k] + (1 if k == 0 else 0) for k in (0, 1))
    assert remainder == (1, 2)
    # The student's constant a+2 is not the identity -a (e.g. a=0).
    assert 0+2 != -0
    # Original criterion independently asks for the correct final pair.
    root = Path(__file__).resolve().parents[1]
    rubric = json.loads((root/'problems/ITA2025F2Q1/rubric.json').read_text())
    assert rubric['items'] == RECORDED['rubric_assessment']['secondary_adjudication']['criteria']['power_reductions']['request']['rubric']['items']
    assert rubric['items'][-1]['description'] == 'Conclui corretamente a=-1 e b=3.'


def test_reapplying_decided_semantic_result_does_not_readjudicate(replay, monkeypatch):
    result, _ = replay()
    before = result.rubric_assessment.model_dump(mode='json')
    from confia_lean_auditor.core.problem_assets import validate_problem_assets
    assets = validate_problem_assets(Path(__file__).resolve().parents[1]/'problems/ITA2025F2Q1', 'ITA2025F2Q1')
    monkeypatch.setattr(ita, 'prepare_payload', lambda **_: {'pending_criteria': []})
    again = ita.apply(rubric=result.rubric_assessment, solution=SOURCE, assets=assets,
        microclaims=[], student_claim_checks=[], provider=lambda _: pytest.fail('double adjudication'))
    assert again.model_dump(mode='json') == before


def test_reference_answer_cannot_award_unwritten_student_conclusion():
    from confia_lean_auditor.claims.common.rubric_bridge import RubricClaimContext
    from confia_lean_auditor.core.problem_assets import validate_problem_assets
    from confia_lean_auditor.rubric.rubric_evaluator import evaluate_rubric
    from confia_lean_auditor.student_claims.registry import extract_student_claims
    root = Path(__file__).resolve().parents[1]
    assets = validate_problem_assets(root/'problems/ITA2025F2Q1', 'ITA2025F2Q1')
    source = SOURCE[:SOURCE.index('O resto tem grau')]
    saved = AuditResponse.model_validate(RECORDED)
    context = RubricClaimContext(problem_id=assets.problem.id, solution_text=source,
        extraction=saved.extracted_claims, students=extract_student_claims(assets.problem.id, source),
        checks=saved.student_claim_checks, rubric_config=assets.rubric,
        statement_text=assets.problem.statement, correct_answer=assets.problem.correct_answer)
    result = evaluate_rubric(root, assets.problem.id, saved.extracted_claims, saved.microclaims,
        assets.rubric, solution_text=source, student_claim_checks=saved.student_claim_checks,
        statement_text=assets.problem.statement, claim_context=context)
    assert result.items[-1].points is None


@pytest.mark.parametrize('source, kind, literal', [
    ('Resto não representado.', 'local_context', False),
    ('Texto sem vínculo com o critério.', 'bounded_context', True),
    ('Supondo que o resto seja x+1.', 'local_context', True),
    ('Tentativa errada: o resto é x+1.', 'local_context', True),
    ('"O resto é x+1."', 'local_context', True),
])
def test_unusable_retrieved_context_stays_pending(monkeypatch, source, kind, literal):
    from types import SimpleNamespace
    from confia_lean_auditor.core.schemas import RubricAssessment, RubricItemResult
    item = RubricItemResult(id='remainder', description='Obtém o resto.',
        detected=False, points=None, max_points=3, mathematical_status='indeterminate')
    candidate = dict(source_start=0, source_end=len(source), source_kind=kind,
        source_text=source if literal else 'Outro texto.', grounding_status='grounded')
    row = dict(id=item.id, candidate_evidence=[candidate])
    monkeypatch.setattr(ita, 'prepare_payload', lambda **_: {'pending_criteria':[row]})
    result = ita.apply(rubric=RubricAssessment(score=None, max_score=3, items=[item]),
        solution=source, assets=SimpleNamespace(), microclaims=[], student_claim_checks=[],
        provider=lambda _: pytest.fail('Unusable context must not call the provider'))
    assert result.score is None and item.points is None
    assert item.mathematical_status == 'indeterminate'
