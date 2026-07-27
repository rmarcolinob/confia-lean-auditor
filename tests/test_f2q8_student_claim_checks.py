from confia_lean_auditor.student_claims.extract_f2q8_student_claims import (
    extract_f2q8_student_claims,
)
from confia_lean_auditor.lean.student_claim_checker import check_student_claims


def _checks_by_type(solution: str, run_id: str):
    claims = extract_f2q8_student_claims(solution)
    checks = check_student_claims(claims, run_id=run_id)
    return {check.claim_type: check for check in checks}


def test_f2q8_correct_final_answer_and_pair_reduction():
    solution = """
    Aplicando diferenças sucessivas de colunas, obtemos det(A_k)=(-1)^(k-1)k.
    Logo a soma é 1-2+3-4+...+2025.
    Agrupando os pares, temos 2025 - 1012 = 1013.
    Portanto, a resposta é 1013.
    """

    by_type = _checks_by_type(solution, "pytest_f2q8_correct_final_pair_reduction")

    assert by_type["f2q8_student_final_answer"].status == "verified"
    assert by_type["f2q8_student_pair_reduction"].status == "verified"

    # Em contexto de soma alternada, esta igualdade deve ser tratada como
    # redução contextual, não como igualdade aritmética genérica.
    assert "arithmetic_equality" not in by_type


def test_f2q8_wrong_final_answer_and_pair_reduction():
    solution = """
    Aplicando diferenças sucessivas de colunas, obtemos det(A_k)=(-1)^(k-1)k.
    Logo a soma é 1-2+3-4+...+2025.
    Agrupando os pares, temos 2025 - 1012 = 1014.
    Portanto, a resposta é 1014.
    """

    by_type = _checks_by_type(solution, "pytest_f2q8_wrong_final_pair_reduction")

    assert by_type["f2q8_student_final_answer"].status == "failed"
    assert by_type["f2q8_student_pair_reduction"].status == "failed"

    assert "arithmetic_equality" not in by_type


def test_f2q8_generic_arithmetic_equality_still_works():
    solution = """
    O aluno faz uma conta auxiliar: 2025 - 1012 = 1013.
    """

    by_type = _checks_by_type(solution, "pytest_f2q8_generic_arithmetic")

    assert by_type["arithmetic_equality"].status == "verified"


def test_f2q8_generic_wrong_arithmetic_equality_still_fails():
    solution = """
    O aluno faz uma conta auxiliar: 2025 - 1012 = 1014.
    """

    by_type = _checks_by_type(solution, "pytest_f2q8_generic_wrong_arithmetic")

    assert by_type["arithmetic_equality"].status == "failed"


def test_f2q8_wrong_formula_is_rejected():
    solution = """
    Aplicando diferenças sucessivas de colunas, obtemos det(A_k)=(-1)^k k.
    Portanto, a resposta é 1014.
    """

    by_type = _checks_by_type(solution, "pytest_f2q8_wrong_det_formula")

    assert by_type["f2q8_student_det_formula"].status == "failed"


def test_f2q8_correct_formula_is_verified():
    solution = """
    Aplicando diferenças sucessivas de colunas, obtemos det(A_k)=(-1)^(k-1)k.
    Portanto, a resposta é 1013.
    """

    by_type = _checks_by_type(solution, "pytest_f2q8_correct_det_formula")

    assert by_type["f2q8_student_det_formula"].status == "verified"


def test_f2q8_correct_pair_count_but_wrong_rhs():
    solution = """
    A soma alternada tem 1012 pares.
    Agrupando os pares, temos 2025 - 1012 = 999.
    Portanto, a resposta é 999.
    """

    by_type = _checks_by_type(solution, "pytest_f2q8_pair_count_correct_rhs_wrong")

    assert by_type["f2q8_student_pair_count"].status == "verified"
    assert by_type["f2q8_student_pair_reduction"].status == "failed"
    assert by_type["f2q8_student_final_answer"].status == "failed"


def test_f2q8_wrong_pair_count_true_local_subtraction():
    solution = """
    Existem 1013 pares.
    Agrupando os pares, temos 2025 - 1013 = 1012.
    Portanto, a resposta é 1012.
    """

    by_type = _checks_by_type(solution, "pytest_f2q8_wrong_pair_count_true_subtraction")

    assert by_type["f2q8_student_pair_count"].status == "failed"
    assert by_type["f2q8_student_pair_reduction"].status == "failed"
    assert by_type["f2q8_student_final_answer"].status == "failed"


def test_f2q8_does_not_extract_fake_final_answer_from_alternating_sum_start():
    solution = """
    Logo a soma é 1-2+3-4+...+2025.
    """

    claims = extract_f2q8_student_claims(solution)

    assert all(
        claim.claim_type != "f2q8_student_final_answer"
        for claim in claims
    )
