from __future__ import annotations

from confia_lean_auditor.core.schemas import RubricAssessment, RubricItemResult
from confia_lean_auditor.rubric.adjusters.ita2025f2q6 import (
    apply_f2q6_student_claim_adjustments,
)
from confia_lean_auditor.student_claims.schemas import StudentClaimCheck


def _base_rubric() -> RubricAssessment:
    return RubricAssessment(
        score=10.0,
        max_score=10.0,
        items=[
            RubricItemResult(
                id="probability_formula",
                description="Obtém a fórmula de probabilidade.",
                detected=True,
                points=3.0,
                max_points=3.0,
                evidence="evidence",
                claim_id="c1",
            ),
            RubricItemResult(
                id="ratio_comparison",
                description="Calcula a razão entre probabilidades consecutivas.",
                detected=True,
                points=3.0,
                max_points=3.0,
                evidence="evidence",
                claim_id="c2",
            ),
            RubricItemResult(
                id="maximizers_identification",
                description="Identifica crescimento, empate e decrescimento.",
                detected=True,
                points=2.0,
                max_points=2.0,
                evidence="evidence",
                claim_id="c3",
            ),
            RubricItemResult(
                id="final_answer",
                description="Conclui n=6 e n=7.",
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
        problem_id="ITA2025F2Q6",
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
        problem_id="ITA2025F2Q6",
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


def test_f2q6_failed_probability_formula_zeros_probability_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q6_student_claim_adjustments(
        rubric,
        [_failed_check("f2q6_student_probability_formula", "C(n,3)/2^n")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 7.0
    assert by_id["probability_formula"].points == 0.0
    assert by_id["probability_formula"].student_check_adjusted is True
    assert "C(n,3)/2^n" in by_id["probability_formula"].adjustment_notes[0]

    assert by_id["ratio_comparison"].points == 3.0
    assert by_id["maximizers_identification"].points == 2.0
    assert by_id["final_answer"].points == 2.0


def test_f2q6_failed_ratio_formula_zeros_ratio_and_maximizer_items():
    rubric = _base_rubric()

    adjusted = apply_f2q6_student_claim_adjustments(
        rubric,
        [_failed_check("f2q6_student_ratio_formula", "(n-1)/(2n)")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 5.0
    assert by_id["ratio_comparison"].points == 0.0
    assert by_id["maximizers_identification"].points == 0.0
    assert by_id["ratio_comparison"].student_check_adjusted is True
    assert by_id["maximizers_identification"].student_check_adjusted is True
    assert "(n-1)/(2n)" in by_id["ratio_comparison"].adjustment_notes[0]
    assert "(n-1)/(2n)" in by_id["maximizers_identification"].adjustment_notes[0]

    assert by_id["probability_formula"].points == 3.0
    assert by_id["final_answer"].points == 2.0


def test_f2q6_failed_final_answer_zeros_final_answer_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q6_student_claim_adjustments(
        rubric,
        [_failed_check("f2q6_student_final_answer", "n=7,8")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.0
    assert by_id["final_answer"].points == 0.0
    assert by_id["final_answer"].student_check_adjusted is True
    assert "n=7,8" in by_id["final_answer"].adjustment_notes[0]

    assert by_id["probability_formula"].points == 3.0
    assert by_id["ratio_comparison"].points == 3.0
    assert by_id["maximizers_identification"].points == 2.0


def test_f2q6_verified_checks_do_not_change_score():
    rubric = _base_rubric()

    adjusted = apply_f2q6_student_claim_adjustments(
        rubric,
        [_verified_check("f2q6_student_final_answer", "n=6,7")],
    )

    assert adjusted.score == 10.0
    assert all(item.student_check_adjusted is False for item in adjusted.items)
    assert all(item.adjustment_notes == [] for item in adjusted.items)
