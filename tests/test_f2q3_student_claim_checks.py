from __future__ import annotations

from confia_lean_auditor.lean.student_claim_checkers.ita2025f2q3 import (
    check_f2q3_student_claims,
)
from confia_lean_auditor.student_claims.extract_f2q3_student_claims import (
    extract_f2q3_student_claims,
)


def _checks_by_type(solution: str):
    claims = extract_f2q3_student_claims(solution)
    checks = check_f2q3_student_claims(
        claims,
        run_id="pytest_f2q3_student_claim_checks",
    )
    by_type = {}
    for check in checks:
        by_type.setdefault(check.claim_type, []).append(check)
    return by_type


def test_f2q3_correct_solution_claims_are_verified():
    solution = (
        "Das equações, obtemos cos beta - sin beta = 1/2. "
        "Logo sin beta = -(sqrt(7)+1)/4, cos beta = (1-sqrt(7))/4, "
        "sin alpha = -sqrt(7)/4 e cos alpha = -3/4. "
        "Assim, sin(alpha+beta)=sin alpha cos beta + cos alpha sin beta = "
        "(5+sqrt(7))/8. Portanto, resposta = (5+sqrt(7))/8."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q3_student_beta_difference"][0].status == "verified"
    assert all(
        check.status == "verified"
        for check in by_type["f2q3_student_candidate_value"]
    )
    assert by_type["f2q3_student_final_sin_sum"][0].status == "verified"
    assert by_type["f2q3_student_final_answer"][0].status == "verified"


def test_f2q3_wrong_beta_difference_is_rejected():
    solution = (
        "Das equações, obtemos cos beta - sin beta = -1/2. "
        "Portanto, resposta = (5+sqrt(7))/8."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q3_student_beta_difference"][0].status == "failed"
    assert by_type["f2q3_student_final_answer"][0].status == "verified"


def test_f2q3_wrong_candidate_signs_are_rejected():
    solution = (
        "Temos sin beta = (sqrt(7)+1)/4, cos beta = (sqrt(7)-1)/4, "
        "sin alpha = sqrt(7)/4 e cos alpha = 3/4. "
        "Portanto, resposta = (5+sqrt(7))/8."
    )

    by_type = _checks_by_type(solution)

    assert all(
        check.status == "failed"
        for check in by_type["f2q3_student_candidate_value"]
    )
    assert by_type["f2q3_student_final_answer"][0].status == "verified"


def test_f2q3_wrong_final_sin_sum_is_rejected():
    solution = (
        "Com a fórmula de adição, sin(alpha+beta)=1/2. "
        "Portanto, resposta = 1/2."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q3_student_final_sin_sum"][0].status == "failed"
    assert by_type["f2q3_student_final_answer"][0].status == "failed"


def test_f2q3_correct_final_answer_alone_is_verified():
    solution = "Portanto, resposta = (5+sqrt(7))/8."

    by_type = _checks_by_type(solution)

    assert by_type["f2q3_student_final_answer"][0].status == "verified"
