from __future__ import annotations

from confia_lean_auditor.lean.student_claim_checkers.ita2025f2q5 import (
    check_f2q5_student_claims,
)
from confia_lean_auditor.student_claims.extract_f2q5_student_claims import (
    extract_f2q5_student_claims,
)


def _checks_by_type(solution: str):
    claims = extract_f2q5_student_claims(solution)
    checks = check_f2q5_student_claims(
        claims,
        run_id="pytest_f2q5_student_claim_checks",
    )
    by_type = {}
    for check in checks:
        by_type.setdefault(check.claim_type, []).append(check)
    return by_type


def test_f2q5_correct_solution_claims_are_verified():
    solution = (
        "Temos log10(3^100)=100log10(3)=100*0,4771=47,7100. "
        "A mantissa é 0,7100. Além disso, log10(5)=0,6990 e "
        "log10(6)=0,7781, logo 0,6990<0,7100<0,7781. "
        "Portanto, o primeiro algarismo é 5."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q5_student_log_power_decomposition"][0].status == "verified"
    assert by_type["f2q5_student_mantissa"][0].status == "verified"
    assert by_type["f2q5_student_digit_log_bounds"][0].status == "verified"
    assert by_type["f2q5_student_between_bounds"][0].status == "verified"
    assert by_type["f2q5_student_final_digit"][0].status == "verified"


def test_f2q5_wrong_log_power_decomposition_is_rejected():
    solution = (
        "Temos log10(3^100)=100*0,4771=47,7000. "
        "A mantissa é 0,7000. log10(5)=0,6990 e log10(6)=0,7781. "
        "Portanto, o primeiro algarismo é 5."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q5_student_log_power_decomposition"][0].status == "failed"
    assert by_type["f2q5_student_mantissa"][0].status == "failed"
    assert by_type["f2q5_student_digit_log_bounds"][0].status == "verified"
    assert by_type["f2q5_student_final_digit"][0].status == "verified"


def test_f2q5_wrong_digit_log_bounds_are_rejected():
    solution = (
        "Temos log10(3^100)=47,7100. A mantissa é 0,7100. "
        "Além disso, log10(5)=0,6900 e log10(6)=0,7781. "
        "Portanto, o primeiro algarismo é 5."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q5_student_digit_log_bounds"][0].status == "failed"


def test_f2q5_wrong_between_bounds_are_rejected():
    solution = (
        "Temos log10(3^100)=47,7100. A mantissa é 0,7100. "
        "log10(5)=0,6990 e log10(6)=0,7781, mas escrevo "
        "0,7100<0,6990<0,7781. Portanto, o primeiro algarismo é 5."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q5_student_between_bounds"][0].status == "failed"


def test_f2q5_wrong_final_digit_is_rejected():
    solution = (
        "Temos log10(3^100)=47,7100. A mantissa é 0,7100. "
        "log10(5)=0,6990 e log10(6)=0,7781, logo 0,6990<0,7100<0,7781. "
        "Portanto, o primeiro algarismo é 6."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q5_student_final_digit"][0].status == "failed"
