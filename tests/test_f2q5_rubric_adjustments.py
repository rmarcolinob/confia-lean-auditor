from __future__ import annotations

from confia_lean_auditor.core.schemas import RubricAssessment, RubricItemResult
from confia_lean_auditor.rubric.adjusters.ita2025f2q5 import (
    apply_f2q5_student_claim_adjustments,
)
from confia_lean_auditor.student_claims.schemas import StudentClaimCheck


def _base_rubric() -> RubricAssessment:
    return RubricAssessment(
        score=10.0,
        max_score=10.0,
        items=[
            RubricItemResult(
                id="log_power_decomposition",
                description="Calcula log10(3^100)=47,7100.",
                detected=True,
                points=2.0,
                max_points=2.0,
                evidence="evidence",
                claim_id="c1",
            ),
            RubricItemResult(
                id="mantissa_identification",
                description="Identifica a mantissa 0,7100.",
                detected=True,
                points=2.0,
                max_points=2.0,
                evidence="evidence",
                claim_id="c2",
            ),
            RubricItemResult(
                id="digit_log_bounds",
                description="Calcula log10(5) e log10(6).",
                detected=True,
                points=2.0,
                max_points=2.0,
                evidence="evidence",
                claim_id="c3",
            ),
            RubricItemResult(
                id="mantissa_between_bounds",
                description="Compara 0,6990 < 0,7100 < 0,7781.",
                detected=True,
                points=2.0,
                max_points=2.0,
                evidence="evidence",
                claim_id="c4",
            ),
            RubricItemResult(
                id="final_digit",
                description="Conclui primeiro algarismo 5.",
                detected=True,
                points=2.0,
                max_points=2.0,
                evidence="evidence",
                claim_id="c5",
            ),
        ],
    )


def _failed_check(claim_type: str, raw_text: str) -> StudentClaimCheck:
    return StudentClaimCheck(
        id="student_claim_0",
        problem_id="ITA2025F2Q5",
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
        problem_id="ITA2025F2Q5",
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


def test_f2q5_failed_log_power_decomposition_zeros_log_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q5_student_claim_adjustments(
        rubric,
        [_failed_check("f2q5_student_log_power_decomposition", "log total = 47.7000")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.0
    assert by_id["log_power_decomposition"].points == 0.0
    assert by_id["log_power_decomposition"].student_check_adjusted is True
    assert "47.7000" in by_id["log_power_decomposition"].adjustment_notes[0]

    assert by_id["mantissa_identification"].points == 2.0
    assert by_id["digit_log_bounds"].points == 2.0
    assert by_id["mantissa_between_bounds"].points == 2.0
    assert by_id["final_digit"].points == 2.0


def test_f2q5_failed_mantissa_zeros_mantissa_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q5_student_claim_adjustments(
        rubric,
        [_failed_check("f2q5_student_mantissa", "mantissa = 0.7000")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.0
    assert by_id["mantissa_identification"].points == 0.0
    assert by_id["mantissa_identification"].student_check_adjusted is True
    assert "0.7000" in by_id["mantissa_identification"].adjustment_notes[0]


def test_f2q5_failed_digit_log_bounds_zeros_bounds_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q5_student_claim_adjustments(
        rubric,
        [_failed_check("f2q5_student_digit_log_bounds", "log5=0.6900; log6=0.7781")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.0
    assert by_id["digit_log_bounds"].points == 0.0
    assert by_id["digit_log_bounds"].student_check_adjusted is True
    assert "0.6900" in by_id["digit_log_bounds"].adjustment_notes[0]


def test_f2q5_failed_between_bounds_zeros_comparison_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q5_student_claim_adjustments(
        rubric,
        [_failed_check("f2q5_student_between_bounds", "0.7100<0.6990<0.7781")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.0
    assert by_id["mantissa_between_bounds"].points == 0.0
    assert by_id["mantissa_between_bounds"].student_check_adjusted is True
    assert "0.7100<0.6990<0.7781" in by_id["mantissa_between_bounds"].adjustment_notes[0]


def test_f2q5_failed_final_digit_zeros_final_digit_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q5_student_claim_adjustments(
        rubric,
        [_failed_check("f2q5_student_final_digit", "primeiro algarismo = 6")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.0
    assert by_id["final_digit"].points == 0.0
    assert by_id["final_digit"].student_check_adjusted is True
    assert "6" in by_id["final_digit"].adjustment_notes[0]


def test_f2q5_verified_checks_do_not_change_score():
    rubric = _base_rubric()

    adjusted = apply_f2q5_student_claim_adjustments(
        rubric,
        [_verified_check("f2q5_student_final_digit", "primeiro algarismo = 5")],
    )

    assert adjusted.score == 10.0
    assert all(item.student_check_adjusted is False for item in adjusted.items)
    assert all(item.adjustment_notes == [] for item in adjusted.items)
