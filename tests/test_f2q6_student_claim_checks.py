from __future__ import annotations

from confia_lean_auditor.lean.student_claim_checkers.ita2025f2q6 import (
    check_f2q6_student_claims,
)
from confia_lean_auditor.student_claims.extract_f2q6_student_claims import (
    extract_f2q6_student_claims,
)


def _checks_by_type(solution: str):
    claims = extract_f2q6_student_claims(solution)
    checks = check_f2q6_student_claims(
        claims,
        run_id="pytest_f2q6_student_claim_checks",
    )
    by_type = {}
    for check in checks:
        by_type.setdefault(check.claim_type, []).append(check)
    return by_type


def test_f2q6_correct_solution_claims_are_verified():
    solution = (
        "A quarta cara no n-esimo lançamento exige 3 caras nos n-1 primeiros "
        "lançamentos e cara no último. Assim P(N=n)=C(n-1,3)/2^n. "
        "A razão P(n+1)/P(n)=n/(2n-6). Ela é maior que 1 para n<6, "
        "igual a 1 em n=6 e menor que 1 para n>6. Portanto, n=6 e n=7."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q6_student_probability_formula"][0].status == "verified"
    assert by_type["f2q6_student_ratio_formula"][0].status == "verified"
    assert by_type["f2q6_student_final_answer"][0].status == "verified"


def test_f2q6_wrong_probability_formula_is_rejected():
    solution = (
        "A probabilidade é P(N=n)=C(n,3)/2^n. "
        "A razão P(n+1)/P(n)=n/(2n-6). Portanto, n=6 e n=7."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q6_student_probability_formula"][0].status == "failed"
    assert by_type["f2q6_student_ratio_formula"][0].status == "verified"
    assert by_type["f2q6_student_final_answer"][0].status == "verified"


def test_f2q6_wrong_ratio_formula_is_rejected():
    solution = (
        "Temos P(N=n)=C(n-1,3)/2^n. "
        "A razão P(n+1)/P(n)=(n-1)/(2n). Portanto, n=6 e n=7."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q6_student_probability_formula"][0].status == "verified"
    assert by_type["f2q6_student_ratio_formula"][0].status == "failed"
    assert by_type["f2q6_student_final_answer"][0].status == "verified"


def test_f2q6_wrong_final_answer_is_rejected():
    solution = (
        "Temos P(N=n)=C(n-1,3)/2^n. "
        "A razão P(n+1)/P(n)=n/(2n-6). Portanto, n=7 e n=8."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q6_student_probability_formula"][0].status == "verified"
    assert by_type["f2q6_student_ratio_formula"][0].status == "verified"
    assert by_type["f2q6_student_final_answer"][0].status == "failed"


def test_f2q6_single_maximizer_answer_is_rejected():
    solution = (
        "Temos P(N=n)=C(n-1,3)/2^n. "
        "A razão P(n+1)/P(n)=n/(2n-6). Portanto, n=6."
    )

    by_type = _checks_by_type(solution)

    assert by_type["f2q6_student_final_answer"][0].status == "failed"
