from __future__ import annotations

from confia_lean_auditor.lean.student_claim_checkers.ita2025f2q1 import (
    check_f2q1_student_claims,
)
from confia_lean_auditor.student_claims.extract_f2q1_student_claims import (
    extract_f2q1_student_claims,
)


def _checks_by_type(solution: str):
    claims = extract_f2q1_student_claims(solution)
    checks = check_f2q1_student_claims(
        claims,
        run_id="pytest_f2q1_student_claim_checks",
    )
    by_type = {}
    for check in checks:
        by_type.setdefault(check.claim_type, []).append(check)
    return by_type


def test_f2q1_correct_solution_claims_are_verified():
    solution = (
        "Como x^3=-1 e x^6=1, temos x^57=-1, x^14=x-1 e x^7=x. "
        "Logo o resto é (a+b)x-a. Comparando com 2x+1, obtemos "
        "a+b=2 e -a=1. Portanto, a=-1 e b=3."
    )

    by_type = _checks_by_type(solution)

    assert len(by_type["f2q1_student_power_reduction"]) == 3
    assert all(c.status == "verified" for c in by_type["f2q1_student_power_reduction"])
    assert by_type["f2q1_student_reduced_form"][0].status == "verified"
    assert by_type["f2q1_student_coefficient_system"][0].status == "verified"
    assert by_type["f2q1_student_final_answer"][0].status == "verified"


def test_f2q1_wrong_final_answer_is_rejected():
    solution = (
        "Como x^3=-1 e x^6=1, temos x^57=-1, x^14=x-1 e x^7=x. "
        "Logo o resto é (a+b)x-a. Comparando com 2x+1, obtemos "
        "a+b=2 e -a=1. Portanto, a=1 e b=1."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q1_student_final_answer"][0].status == "failed"


def test_f2q1_wrong_power_reduction_is_rejected():
    solution = (
        "Como x^6=1, temos x^57=-1, x^14=1-x e x^7=x. "
        "Logo o resto é (a+b)x-a. Portanto, a=-1 e b=3."
    )

    by_type = _checks_by_type(solution)

    power_checks = by_type["f2q1_student_power_reduction"]
    assert any(c.raw_text == "x^14=1-x" and c.status == "failed" for c in power_checks)


def test_f2q1_wrong_reduced_form_is_rejected():
    solution = (
        "Como x^3=-1 e x^6=1, temos x^57=-1, x^14=x-1 e x^7=x. "
        "Logo o resto é (a-b)x-a. Portanto, a=-1 e b=3."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q1_student_reduced_form"][0].status == "failed"


def test_f2q1_wrong_coefficient_system_is_rejected():
    solution = (
        "Como x^3=-1 e x^6=1, temos x^57=-1, x^14=x-1 e x^7=x. "
        "Logo o resto é (a+b)x-a. Comparando com 2x+1, obtemos "
        "a+b=2 e a=1. Portanto, a=1 e b=1."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q1_student_coefficient_system"][0].status == "failed"
    assert by_type["f2q1_student_final_answer"][0].status == "failed"
