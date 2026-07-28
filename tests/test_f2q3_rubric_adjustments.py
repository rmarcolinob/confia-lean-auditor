from __future__ import annotations

from confia_lean_auditor.core.schemas import RubricAssessment, RubricItemResult
from confia_lean_auditor.rubric.adjusters.ita2025f2q3 import (
    apply_f2q3_student_claim_adjustments,
)
from confia_lean_auditor.student_claims.schemas import StudentClaimCheck


def _base_rubric() -> RubricAssessment:
    return RubricAssessment(
        score=10.0,
        max_score=10.0,
        items=[
            RubricItemResult(
                id="beta_difference",
                description="Obtém cos(beta)-sen(beta)=1/2.",
                detected=True,
                points=2.0,
                max_points=2.0,
                evidence="evidence",
                claim_id="c1",
            ),
            RubricItemResult(
                id="candidate_values",
                description="Determina corretamente os valores candidatos.",
                detected=True,
                points=3.0,
                max_points=3.0,
                evidence="evidence",
                claim_id="c2",
            ),
            RubricItemResult(
                id="final_sin_sum",
                description="Calcula sen(alpha+beta).",
                detected=True,
                points=3.0,
                max_points=3.0,
                evidence="evidence",
                claim_id="c3",
            ),
            RubricItemResult(
                id="final_answer",
                description="Apresenta a resposta final correta.",
                detected=True,
                points=2.0,
                max_points=2.0,
                evidence="evidence",
                claim_id="c4",
            ),
        ],
    )


def _failed_check(claim_type: str, raw_text: str) -> StudentClaimCheck:
    return StudentClaimCheck(
        id="student_claim_0",
        problem_id="ITA2025F2Q3",
        claim_type=claim_type,  # type: ignore[arg-type]
        raw_text=raw_text,
        normalized_text=raw_text,
        lean_statement="False",
        method="ring_nf",
        status="failed",
        compiled=False,
        lean_file=None,
        stdout="",
        stderr="",
        data={},
    )


def _verified_check(claim_type: str, raw_text: str) -> StudentClaimCheck:
    return StudentClaimCheck(
        id="student_claim_0",
        problem_id="ITA2025F2Q3",
        claim_type=claim_type,  # type: ignore[arg-type]
        raw_text=raw_text,
        normalized_text=raw_text,
        lean_statement="True",
        method="ring_nf",
        status="verified",
        compiled=True,
        lean_file=None,
        stdout="",
        stderr="",
        data={},
    )


def test_f2q3_failed_beta_difference_zeros_beta_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q3_student_claim_adjustments(
        rubric,
        [_failed_check("f2q3_student_beta_difference", "cos beta - sin beta = -1/2")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.0
    assert by_id["beta_difference"].points == 0.0
    assert by_id["beta_difference"].student_check_adjusted is True
    assert "-1/2" in by_id["beta_difference"].adjustment_notes[0]

    assert by_id["candidate_values"].points == 3.0
    assert by_id["final_sin_sum"].points == 3.0
    assert by_id["final_answer"].points == 2.0


def test_f2q3_failed_candidate_value_zeros_candidate_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q3_student_claim_adjustments(
        rubric,
        [_failed_check("f2q3_student_candidate_value", "cos alpha = 3/4")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 7.0
    assert by_id["candidate_values"].points == 0.0
    assert by_id["candidate_values"].student_check_adjusted is True
    assert "3/4" in by_id["candidate_values"].adjustment_notes[0]


def test_f2q3_multiple_failed_candidate_values_zero_candidate_item_once():
    rubric = _base_rubric()

    adjusted = apply_f2q3_student_claim_adjustments(
        rubric,
        [
            _failed_check("f2q3_student_candidate_value", "sin beta = (sqrt(7)+1)/4"),
            _failed_check("f2q3_student_candidate_value", "cos beta = (sqrt(7)-1)/4"),
        ],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 7.0
    assert by_id["candidate_values"].points == 0.0
    assert by_id["candidate_values"].student_check_adjusted is True
    assert len(by_id["candidate_values"].adjustment_notes) == 2


def test_f2q3_failed_final_sin_sum_zeros_final_sin_sum_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q3_student_claim_adjustments(
        rubric,
        [_failed_check("f2q3_student_final_sin_sum", "sin(alpha+beta)=1/2")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 7.0
    assert by_id["final_sin_sum"].points == 0.0
    assert by_id["final_sin_sum"].student_check_adjusted is True
    assert "1/2" in by_id["final_sin_sum"].adjustment_notes[0]


def test_f2q3_failed_final_answer_zeros_final_answer_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q3_student_claim_adjustments(
        rubric,
        [_failed_check("f2q3_student_final_answer", "resposta = 1/2")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.0
    assert by_id["final_answer"].points == 0.0
    assert by_id["final_answer"].student_check_adjusted is True
    assert "1/2" in by_id["final_answer"].adjustment_notes[0]


def test_f2q3_verified_checks_do_not_change_score():
    rubric = _base_rubric()

    adjusted = apply_f2q3_student_claim_adjustments(
        rubric,
        [_verified_check("f2q3_student_final_answer", "resposta = (5+sqrt(7))/8")],
    )

    assert adjusted.score == 10.0
    assert all(item.student_check_adjusted is False for item in adjusted.items)
    assert all(item.adjustment_notes == [] for item in adjusted.items)
