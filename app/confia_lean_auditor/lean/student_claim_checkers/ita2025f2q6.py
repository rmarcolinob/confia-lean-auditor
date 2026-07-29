from __future__ import annotations

import subprocess
import time
from dataclasses import asdict
from typing import List

from confia_lean_auditor.lean.student_claim_checker import CHECK_DIR, _run_lean_file
from confia_lean_auditor.student_claims.schemas import StudentClaim, StudentClaimCheck


def _build_f2q6_lean_code(
    claim: StudentClaim,
    theorem_name: str,
    lean_statement: str,
    method: str,
) -> str:
    safe_raw = claim.raw_text.replace("-/", "-∕")

    return f'''import ConfiaLeanAuditor.Problems.ITA2025F2Q6.Statement

namespace ConfiaStudentClaimCheck.ITA2025F2Q6

open ConfIA.LeanAuditor.ITA2025F2Q6

/-- Afirmação extraída do aluno: {safe_raw} -/
theorem {theorem_name} :
    {lean_statement} := by
  {method}

end ConfiaStudentClaimCheck.ITA2025F2Q6
'''


def _probability_formula_values(formula_kind: str, n: int) -> tuple[int, int] | None:
    """Return the numerator/denominator values asserted by the student's formula.

    We check the formula at n=6 and n=7, the two canonical maximizers.

    Correct formula:
      C(n-1,3) / 2^n

    Supported wrong variants:
      C(n,3) / 2^n
      C(n-1,3) / 2^(n-1)
    """
    if formula_kind == "correct":
        if n == 6:
            return 10, 64
        if n == 7:
            return 20, 128

    if formula_kind == "wrong_choose_n_3":
        if n == 6:
            return 20, 64
        if n == 7:
            return 35, 128

    if formula_kind == "correct_numerator_wrong_denominator_n_minus_1":
        if n == 6:
            return 10, 32
        if n == 7:
            return 20, 64

    return None


def _probability_formula_statement(formula_kind: str) -> str | None:
    # Canonical values from C(n-1,3)/2^n:
    # n=6: 10/64
    # n=7: 20/128
    expected = {
        6: (10, 64),
        7: (20, 128),
    }

    checks: list[str] = []

    for n, (expected_num, expected_den) in expected.items():
        student_values = _probability_formula_values(formula_kind, n)
        if student_values is None:
            return None

        student_num, student_den = student_values

        checks.append(
            f"({student_num} : ℤ) * ({expected_den} : ℤ) = "
            f"({expected_num} : ℤ) * ({student_den} : ℤ)"
        )

    return " ∧ ".join(checks)


def _ratio_components(ratio_kind: str, n: int) -> tuple[str, str] | None:
    z = f"({n} : ℤ)"

    if ratio_kind == "correct":
        return z, f"(2 : ℤ) * {z} - 6"

    if ratio_kind == "wrong_n_minus_1_over_2n":
        return f"{z} - 1", f"(2 : ℤ) * {z}"

    if ratio_kind == "wrong_n_minus_1_over_2n_minus_6":
        return f"{z} - 1", f"(2 : ℤ) * {z} - 6"

    if ratio_kind == "wrong_n_over_2n":
        return z, f"(2 : ℤ) * {z}"

    if ratio_kind == "wrong_n_over_2n_minus_8":
        return z, f"(2 : ℤ) * {z} - 8"

    return None


def _ratio_formula_statement(ratio_kind: str) -> str | None:
    checks: list[str] = []

    for n in range(4, 10):
        components = _ratio_components(ratio_kind, n)
        if components is None:
            return None

        student_num, student_den = components
        expected_num = f"({n} : ℤ)"
        expected_den = f"(2 : ℤ) * ({n} : ℤ) - 6"

        checks.append(
            f"({student_num}) * ({expected_den}) = "
            f"({expected_num}) * ({student_den})"
        )

    return " ∧ ".join(checks)


def _final_answer_statement(values: list[int]) -> str:
    unique_values = sorted(set(values))
    length = len(unique_values)

    first = unique_values[0] if length >= 1 else -1
    second = unique_values[1] if length >= 2 else first

    return (
        f"candidateN1 = ({first} : ℕ) ∧ "
        f"candidateN2 = ({second} : ℕ) ∧ "
        f"({length} : ℕ) = (2 : ℕ)"
    )


def _lean_statement_and_method_for_f2q6_claim(
    claim: StudentClaim,
) -> tuple[str | None, str, str]:
    if claim.claim_type == "f2q6_student_probability_formula":
        formula_kind = claim.data.get("formula_kind")

        if not isinstance(formula_kind, str):
            return None, claim.method, "missing formula_kind"

        statement = _probability_formula_statement(formula_kind)
        if statement is None:
            return None, claim.method, f"unsupported formula_kind: {formula_kind}"

        return statement, "norm_num", ""

    if claim.claim_type == "f2q6_student_ratio_formula":
        ratio_kind = claim.data.get("ratio_kind")

        if not isinstance(ratio_kind, str):
            return None, claim.method, "missing ratio_kind"

        statement = _ratio_formula_statement(ratio_kind)
        if statement is None:
            return None, claim.method, f"unsupported ratio_kind: {ratio_kind}"

        return statement, "norm_num", ""

    if claim.claim_type == "f2q6_student_final_answer":
        values = claim.data.get("values")

        if not isinstance(values, list) or not all(isinstance(v, int) for v in values):
            return None, claim.method, "missing values"

        return _final_answer_statement(values), "norm_num [candidateN1, candidateN2]", ""

    return None, claim.method, f"unsupported claim_type for F2Q6: {claim.claim_type}"


def check_one_f2q6_student_claim(
    claim: StudentClaim,
    run_id: str,
    index: int,
    timeout_seconds: int = 90,
) -> StudentClaimCheck:
    out_dir = CHECK_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    theorem_name = f"student_claim_check_{index}"
    lean_statement, method, unsupported_reason = _lean_statement_and_method_for_f2q6_claim(claim)

    if lean_statement is None:
        return StudentClaimCheck(
            id=claim.id,
            problem_id=claim.problem_id,
            claim_type=claim.claim_type,
            raw_text=claim.raw_text,
            normalized_text=claim.normalized_text,
            lean_statement="",
            method=method,
            status="unsupported",
            compiled=False,
            lean_file=None,
            stdout="",
            stderr=unsupported_reason,
            data=claim.data,
        )

    lean_file = out_dir / f"{theorem_name}.lean"
    lean_code = _build_f2q6_lean_code(claim, theorem_name, lean_statement, method)
    lean_file.write_text(lean_code, encoding="utf-8")

    try:
        proc = _run_lean_file(lean_file, timeout_seconds=timeout_seconds)
        compiled = proc.returncode == 0

        return StudentClaimCheck(
            id=claim.id,
            problem_id=claim.problem_id,
            claim_type=claim.claim_type,
            raw_text=claim.raw_text,
            normalized_text=claim.normalized_text,
            lean_statement=lean_statement,
            method=method,
            status="verified" if compiled else "failed",
            compiled=compiled,
            lean_file=str(lean_file),
            stdout=proc.stdout,
            stderr=proc.stderr,
            data=claim.data,
        )

    except subprocess.TimeoutExpired as exc:
        return StudentClaimCheck(
            id=claim.id,
            problem_id=claim.problem_id,
            claim_type=claim.claim_type,
            raw_text=claim.raw_text,
            normalized_text=claim.normalized_text,
            lean_statement=lean_statement,
            method=method,
            status="error",
            compiled=False,
            lean_file=str(lean_file),
            stdout=exc.stdout or "",
            stderr=f"timeout after {timeout_seconds}s",
            data=claim.data,
        )


def check_f2q6_student_claims(
    claims: List[StudentClaim],
    run_id: str | None = None,
) -> List[StudentClaimCheck]:
    run_id = run_id or time.strftime("%Y%m%dT%H%M%S")
    return [
        check_one_f2q6_student_claim(claim, run_id=run_id, index=i)
        for i, claim in enumerate(claims)
    ]


def checks_to_dicts(checks: List[StudentClaimCheck]) -> List[dict]:
    return [asdict(check) for check in checks]
