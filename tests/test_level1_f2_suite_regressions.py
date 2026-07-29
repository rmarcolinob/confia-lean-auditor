from confia_lean_auditor.claims.extract_claims import extract_claims


def types(problem_id: str, solution: str):
    result = extract_claims(problem_id, solution)
    return {c.type for c in result.claims}, {s.type for s in result.formal_steps}


def test_f2q6_binom_power_notation():
    sol = r"P(N=n)=\binom{n-1}{3}2^{-n}. Razão = n/(2(n-3)). Máximo: n=6,7."
    claims, steps = types("ITA2025F2Q6", sol)

    assert "probability_formula" in claims
    assert "ratio_comparison" in claims
    assert "maximizers_identification" in claims
    assert "final_answer" in claims
    assert "f2q6_probability_values" in steps
    assert "f2q6_ratio_comparison" in steps


def test_f2q6_one_half_power_notation():
    sol = "P(n)=binom(n-1,3)(1/2)^n. Comparando termos, P(n+1)/P(n)=n/(2(n-3)). O máximo ocorre em n=6 e n=7."
    claims, steps = types("ITA2025F2Q6", sol)

    assert "probability_formula" in claims
    assert "ratio_comparison" in claims
    assert "maximizers_identification" in claims
    assert "final_answer" in claims
    assert "f2q6_probability_values" in steps
    assert "f2q6_ratio_comparison" in steps


def test_f2q5_compact_correct_solution():
    sol = "100log3=47,71;mantissa=0,71=71/100;log5=0,6990;log6=0,7781;algarismo=5"
    claims, steps = types("ITA2025F2Q5", sol)

    assert "log_power_decomposition" in claims
    assert "mantissa_identification" in claims
    assert "digit_log_bounds" in claims
    assert "mantissa_between_bounds" in claims
    assert "final_digit_five" in claims
    assert "f2q5_log_power_decomposition" in steps
    assert "f2q5_digit_bounds" in steps


def test_f2q5_latex_decimal_comma_solution():
    sol = r"100\log 3=47{,}71,\ m=71/100,\ \log5=0{,}6990<0{,}71<0{,}7781=\log6. Dígito: 5."
    claims, steps = types("ITA2025F2Q5", sol)

    assert "log_power_decomposition" in claims
    assert "mantissa_identification" in claims
    assert "digit_log_bounds" in claims
    assert "mantissa_between_bounds" in claims
    assert "final_digit_five" in claims
    assert "f2q5_log_power_decomposition" in steps
    assert "f2q5_digit_bounds" in steps


def test_f2q3_compact_unicode_solution():
    sol = "cosβ-senβ=1/2; senβ=-(√7+1)/4; cosβ=(1-√7)/4; senα=-√7/4; cosα=-3/4; sen(α+β)=(5+√7)/8."
    claims, steps = types("ITA2025F2Q3", sol)

    assert "beta_difference" in claims
    assert "candidate_values" in claims
    assert "final_sin_sum" in claims
    assert "final_answer" in claims
    assert "f2q3_beta_difference" in steps
    assert "f2q3_equations" in steps
    assert "f2q3_final_sin_sum" in steps
    assert "f2q3_final_answer" in steps


def test_f2q1_explicit_system_from_comparison():
    sol = "x^57=-1, x^14=x-1 e x^7=x. O resto é (a+b)x-a. Comparando com 2x+1, temos -a=1 e a+b=2. Logo a=-1 e b=3."
    claims, steps = types("ITA2025F2Q1", sol)

    assert "power_reductions" in claims
    assert "reduced_polynomial_form" in claims
    assert "coefficient_system" in claims
    assert "final_answer" in claims
    assert "f2q1_power_reductions" in steps
    assert "f2q1_reduced_form" in steps
    assert "f2q1_coefficient_solution" in steps


def test_f2q8_does_not_accept_banana_1013_as_final_answer():
    sol = "Hoje eu comi arroz, feijão e 1013 bananas. Não sei resolver matriz."
    claims, steps = types("ITA2025F2Q8", sol)

    assert "final_answer" not in claims
    assert "alternating_sum" not in claims
    assert "f2q8_final_sum" not in steps
