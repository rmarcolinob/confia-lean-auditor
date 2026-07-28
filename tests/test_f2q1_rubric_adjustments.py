from __future__ import annotations

from confia_lean_auditor.core.schemas import RubricAssessment, RubricItemResult
from confia_lean_auditor.rubric.adjusters.ita2025f2q1 import (
    apply_f2q1_student_claim_adjustments,
)
from confia_lean_auditor.student_claims.schemas import StudentClaimCheck


def _base_rubric() -> RubricAssessment:
    return RubricAssessment(
        score=10.0,
        max_score=10.0,
        items=[
            RubricItemResult(
                id="power_reductions",
                description="Usa as reduções de potência.",
                detected=True,
                points=3.0,
                max_points=3.0,
                evidence="evidence",
                claim_id="c1",
            ),
            RubricItemResult(
                id="reduced_polynomial_form",
                description="Obtém o resto geral.",
                detected=True,
                points=3.0,
                max_points=3.0,
                evidence="evidence",
                claim_id="c2",
            ),
            RubricItemResult(
                id="coefficient_system",
                description="Monta o sistema.",
                detected=True,
                points=2.0,
                max_points=2.0,
                evidence="evidence",
                claim_id="c3",
            ),
            RubricItemResult(
                id="final_answer",
                description="Conclui a=-1 e b=3.",
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
        problem_id="ITA2025F2Q1",
        claim_type=claim_type,  # type: ignore[arg-type]
        raw_text=raw_text,
        normalized_text=raw_text,
        lean_statement="False",
        method="norm_num",
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
        problem_id="ITA2025F2Q1",
        claim_type=claim_type,  # type: ignore[arg-type]
        raw_text=raw_text,
        normalized_text=raw_text,
        lean_statement="True",
        method="norm_num",
        status="verified",
        compiled=True,
        lean_file=None,
        stdout="",
        stderr="",
        data={},
    )


def test_f2q1_failed_power_reduction_zeros_power_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q1_student_claim_adjustments(
        rubric,
        [_failed_check("f2q1_student_power_reduction", "x^14=1-x")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 7.0
    assert by_id["power_reductions"].points == 0.0
    assert by_id["power_reductions"].student_check_adjusted is True
    assert "x^14=1-x" in by_id["power_reductions"].adjustment_notes[0]

    assert by_id["reduced_polynomial_form"].points == 3.0
    assert by_id["coefficient_system"].points == 2.0
    assert by_id["final_answer"].points == 2.0


def test_f2q1_failed_reduced_form_zeros_reduced_form_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q1_student_claim_adjustments(
        rubric,
        [_failed_check("f2q1_student_reduced_form", "(a-b)x-a")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 7.0
    assert by_id["reduced_polynomial_form"].points == 0.0
    assert by_id["reduced_polynomial_form"].student_check_adjusted is True
    assert "(a-b)x-a" in by_id["reduced_polynomial_form"].adjustment_notes[0]


def test_f2q1_failed_coefficient_system_zeros_system_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q1_student_claim_adjustments(
        rubric,
        [_failed_check("f2q1_student_coefficient_system", "a+b=2; a=1")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.0
    assert by_id["coefficient_system"].points == 0.0
    assert by_id["coefficient_system"].student_check_adjusted is True
    assert "a+b=2; a=1" in by_id["coefficient_system"].adjustment_notes[0]


def test_f2q1_failed_final_answer_zeros_final_answer_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q1_student_claim_adjustments(
        rubric,
        [_failed_check("f2q1_student_final_answer", "a=1, b=1")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.0
    assert by_id["final_answer"].points == 0.0
    assert by_id["final_answer"].student_check_adjusted is True
    assert "a=1, b=1" in by_id["final_answer"].adjustment_notes[0]


def test_f2q1_verified_checks_do_not_change_score():
    rubric = _base_rubric()

    adjusted = apply_f2q1_student_claim_adjustments(
        rubric,
        [_verified_check("f2q1_student_final_answer", "a=-1, b=3")],
    )

    assert adjusted.score == 10.0
    assert all(item.student_check_adjusted is False for item in adjusted.items)
    assert all(item.adjustment_notes == [] for item in adjusted.items)
