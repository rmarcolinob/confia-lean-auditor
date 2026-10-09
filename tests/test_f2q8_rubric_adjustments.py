from __future__ import annotations

from fastapi.testclient import TestClient

from confia_lean_auditor.core.schemas import RubricAssessment, RubricItemResult
from confia_lean_auditor.main import app
from confia_lean_auditor.rubric.adjusters.ita2025f2q8 import (
    apply_f2q8_student_claim_adjustments,
)
from confia_lean_auditor.student_claims.schemas import StudentClaimCheck


CLIENT = TestClient(app)


def _base_rubric() -> RubricAssessment:
    return RubricAssessment(
        score=10.0,
        max_score=10.0,
        items=[
            RubricItemResult(
                id="matrix_transformation",
                description="Usa diferenças sucessivas de colunas.",
                detected=True,
                points=3.0,
                max_points=3.0,
                evidence="evidence",
                claim_id="c1",
            ),
            RubricItemResult(
                id="determinant_formula",
                description="Obtém det(A_k)=(-1)^(k-1)k.",
                detected=True,
                points=3.5,
                max_points=3.5,
                evidence="evidence",
                claim_id="c2",
            ),
            RubricItemResult(
                id="alternating_sum",
                description="Reduz à soma alternada.",
                detected=True,
                points=2.0,
                max_points=2.0,
                evidence="evidence",
                claim_id="c3",
            ),
            RubricItemResult(
                id="final_answer",
                description="Conclui 1013.",
                detected=True,
                points=1.5,
                max_points=1.5,
                evidence="evidence",
                claim_id="c4",
            ),
        ],
    )


def _refuted_check(claim_type: str, raw_text: str) -> StudentClaimCheck:
    return StudentClaimCheck(
        id="student_claim_0",
        problem_id="ITA2025F2Q8",
        claim_type=claim_type,  # type: ignore[arg-type]
        raw_text=raw_text,
        normalized_text=raw_text,
        lean_statement="False",
        method="norm_num",
        status="refuted",
        refutation_verified=True,
        refutation_lean_file="/test/formal_negation.lean",
        compiled=False,
        lean_file=None,
        stdout="",
        stderr="",
        data={},
    )


def _verified_check(claim_type: str, raw_text: str) -> StudentClaimCheck:
    return StudentClaimCheck(
        id="student_claim_0",
        problem_id="ITA2025F2Q8",
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


def test_f2q8_failed_final_answer_zeros_final_answer_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q8_student_claim_adjustments(
        rubric,
        [_refuted_check("f2q8_student_final_answer", "resposta = 1014")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.5
    assert by_id["final_answer"].points == 0.0
    assert by_id["final_answer"].student_check_adjusted is True
    assert "1014" in by_id["final_answer"].adjustment_notes[0]

    assert by_id["matrix_transformation"].points == 3.0
    assert by_id["determinant_formula"].points == 3.5
    assert by_id["alternating_sum"].points == 2.0


def test_f2q8_failed_det_formula_zeros_determinant_item_only():
    rubric = _base_rubric()

    adjusted = apply_f2q8_student_claim_adjustments(
        rubric,
        [_refuted_check("f2q8_student_det_formula", "det(A_k)=(-1)^k k")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 6.5
    assert by_id["determinant_formula"].points == 0.0
    assert by_id["determinant_formula"].student_check_adjusted is True
    assert "(-1)^k k" in by_id["determinant_formula"].adjustment_notes[0]

    assert by_id["matrix_transformation"].points == 3.0
    assert by_id["alternating_sum"].points == 2.0
    assert by_id["final_answer"].points == 1.5


def test_f2q8_failed_pair_reduction_zeros_final_answer_item():
    rubric = _base_rubric()

    adjusted = apply_f2q8_student_claim_adjustments(
        rubric,
        [_refuted_check("f2q8_student_pair_reduction", "2025 - 1012 = 1014")],
    )

    by_id = {item.id: item for item in adjusted.items}

    assert adjusted.score == 8.5
    assert by_id["final_answer"].points == 0.0
    assert by_id["final_answer"].student_check_adjusted is True
    assert "1014" in by_id["final_answer"].adjustment_notes[0]


def test_f2q8_verified_checks_do_not_change_score():
    rubric = _base_rubric()

    adjusted = apply_f2q8_student_claim_adjustments(
        rubric,
        [_verified_check("f2q8_student_final_answer", "resposta = 1013")],
    )

    assert adjusted.score == 10.0
    assert all(item.student_check_adjusted is False for item in adjusted.items)
    assert all(item.adjustment_notes == [] for item in adjusted.items)


def test_f2q8_adversarial_solution_does_not_receive_max_score():
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q8",
            "solution": "Hoje eu comi arroz, feijao e 1013 bananas. Nao sei resolver matriz.",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["score"] is None
    assert data["verdict"] == "inconclusivo"
    assert data["rubric_assessment"]["assessment_status"] == "indeterminate"
    assert all(item["points"] is None for item in data["rubric_assessment"]["items"])
    assert data["pedagogical_report"] is not None
