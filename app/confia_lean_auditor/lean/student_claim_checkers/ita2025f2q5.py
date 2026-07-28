from __future__ import annotations

import subprocess
import time
from dataclasses import asdict
from typing import List

from confia_lean_auditor.lean.student_claim_checker import CHECK_DIR, _run_lean_file
from confia_lean_auditor.student_claims.schemas import StudentClaim, StudentClaimCheck


def _build_f2q5_lean_code(
    claim: StudentClaim,
    theorem_name: str,
    lean_statement: str,
    method: str,
) -> str:
    safe_raw = claim.raw_text.replace("-/", "-∕")

    return f'''import ConfiaLeanAuditor.Problems.ITA2025F2Q5.Statement

namespace ConfiaStudentClaimCheck.ITA2025F2Q5

open ConfIA.LeanAuditor.ITA2025F2Q5

/-- Afirmação extraída do aluno: {safe_raw} -/
theorem {theorem_name} :
    {lean_statement} := by
  {method}

end ConfiaStudentClaimCheck.ITA2025F2Q5
'''


def _lean_statement_and_method_for_f2q5_claim(
    claim: StudentClaim,
) -> tuple[str | None, str, str]:
    if claim.claim_type == "f2q5_student_log_power_decomposition":
        total = claim.data.get("total_log_scaled")
        integer_part = claim.data.get("integer_part_scaled")
        mantissa = claim.data.get("mantissa_scaled")

        if not all(isinstance(v, int) for v in [total, integer_part, mantissa]):
            return None, claim.method, "missing total/integer_part/mantissa"

        statement = (
            f"totalLogScaled = ({total} : ℤ) ∧ "
            f"integerPartScaled = ({integer_part} : ℤ) ∧ "
            f"mantissaScaled = ({mantissa} : ℤ) ∧ "
            f"({total} : ℤ) = ({integer_part} : ℤ) + ({mantissa} : ℤ)"
        )

        method = "norm_num [totalLogScaled, integerPartScaled, mantissaScaled, log3Scaled, scale]"
        return statement, method, ""

    if claim.claim_type == "f2q5_student_mantissa":
        mantissa = claim.data.get("mantissa_scaled")

        if not isinstance(mantissa, int):
            return None, claim.method, "missing mantissa_scaled"

        statement = f"mantissaScaled = ({mantissa} : ℤ)"
        return statement, "norm_num [mantissaScaled]", ""

    if claim.claim_type == "f2q5_student_digit_log_bounds":
        log5 = claim.data.get("log5_scaled")
        log6 = claim.data.get("log6_scaled")

        if not isinstance(log5, int) or not isinstance(log6, int):
            return None, claim.method, "missing log5_scaled/log6_scaled"

        statement = (
            f"log5Scaled = ({log5} : ℤ) ∧ "
            f"log6Scaled = ({log6} : ℤ)"
        )

        method = "norm_num [log5Scaled, log6Scaled, log2Scaled, log3Scaled, scale]"
        return statement, method, ""

    if claim.claim_type == "f2q5_student_between_bounds":
        left = claim.data.get("left_scaled")
        middle = claim.data.get("middle_scaled")
        right = claim.data.get("right_scaled")

        if not all(isinstance(v, int) for v in [left, middle, right]):
            return None, claim.method, "missing left/middle/right"

        statement = (
            f"log5Scaled = ({left} : ℤ) ∧ "
            f"mantissaScaled = ({middle} : ℤ) ∧ "
            f"log6Scaled = ({right} : ℤ) ∧ "
            f"({left} : ℤ) < ({middle} : ℤ) ∧ "
            f"({middle} : ℤ) < ({right} : ℤ)"
        )

        method = "norm_num [log5Scaled, log6Scaled, mantissaScaled, log2Scaled, log3Scaled, scale]"
        return statement, method, ""

    if claim.claim_type == "f2q5_student_final_digit":
        digit = claim.data.get("digit")

        if not isinstance(digit, int):
            return None, claim.method, "missing digit"

        statement = f"(5 : ℤ) = ({digit} : ℤ)"
        return statement, "norm_num", ""

    return None, claim.method, f"unsupported claim_type for F2Q5: {claim.claim_type}"


def check_one_f2q5_student_claim(
    claim: StudentClaim,
    run_id: str,
    index: int,
    timeout_seconds: int = 90,
) -> StudentClaimCheck:
    out_dir = CHECK_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    theorem_name = f"student_claim_check_{index}"
    lean_statement, method, unsupported_reason = _lean_statement_and_method_for_f2q5_claim(claim)

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
    lean_code = _build_f2q5_lean_code(claim, theorem_name, lean_statement, method)
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


def check_f2q5_student_claims(
    claims: List[StudentClaim],
    run_id: str | None = None,
) -> List[StudentClaimCheck]:
    run_id = run_id or time.strftime("%Y%m%dT%H%M%S")
    return [
        check_one_f2q5_student_claim(claim, run_id=run_id, index=i)
        for i, claim in enumerate(claims)
    ]


def checks_to_dicts(checks: List[StudentClaimCheck]) -> List[dict]:
    return [asdict(check) for check in checks]
