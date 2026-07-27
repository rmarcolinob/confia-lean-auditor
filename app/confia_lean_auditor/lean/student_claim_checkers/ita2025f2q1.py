from __future__ import annotations

import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import List

from confia_lean_auditor.lean.student_claim_checker import CHECK_DIR, ROOT_DIR, _run_lean_file
from confia_lean_auditor.student_claims.schemas import StudentClaim, StudentClaimCheck


def _build_f2q1_lean_code(
    claim: StudentClaim,
    theorem_name: str,
    lean_statement: str,
    method: str,
) -> str:
    safe_raw = claim.raw_text.replace("-/", "-∕")

    return f'''import ConfiaLeanAuditor.Problems.ITA2025F2Q1.Statement

namespace ConfiaStudentClaimCheck.ITA2025F2Q1

open ConfIA.LeanAuditor.ITA2025F2Q1

/-- Afirmação extraída do aluno: {safe_raw} -/
theorem {theorem_name} :
    {lean_statement} := by
  {method}

end ConfiaStudentClaimCheck.ITA2025F2Q1
'''


def _reduced_form_statement(form_kind: str) -> str | None:
    if form_kind == "correct":
        return "∀ a b : ℤ, remainderConst a b = -a ∧ remainderXCoeff a b = a + b"

    if form_kind == "wrong_const_sign":
        return "∀ a b : ℤ, remainderConst a b = a ∧ remainderXCoeff a b = a + b"

    if form_kind == "wrong_coeff_minus":
        return "∀ a b : ℤ, remainderConst a b = -a ∧ remainderXCoeff a b = a - b"

    if form_kind == "wrong_coeff_swapped_minus":
        return "∀ a b : ℤ, remainderConst a b = -a ∧ remainderXCoeff a b = b - a"

    return None


def _lean_statement_and_method_for_f2q1_claim(claim: StudentClaim) -> tuple[str | None, str, str]:
    if claim.claim_type == "f2q1_student_final_answer":
        a_value = claim.data.get("a")
        b_value = claim.data.get("b")

        if not isinstance(a_value, int) or not isinstance(b_value, int):
            return None, claim.method, "missing a/b"

        statement = f"candidateA = ({a_value} : ℤ) ∧ candidateB = ({b_value} : ℤ)"
        return statement, "norm_num [candidateA, candidateB]", ""

    if claim.claim_type == "f2q1_student_power_reduction":
        exponent = claim.data.get("exponent")
        const = claim.data.get("const")
        coeff = claim.data.get("coeff")

        if not isinstance(exponent, int) or not isinstance(const, int) or not isinstance(coeff, int):
            return None, claim.method, "missing exponent/const/coeff"

        statement = f"powRem {exponent} = ({const}, {coeff})"
        return statement, "norm_num [powRem]", ""

    if claim.claim_type == "f2q1_student_reduced_form":
        form_kind = claim.data.get("form_kind")

        if not isinstance(form_kind, str):
            return None, claim.method, "missing form_kind"

        statement = _reduced_form_statement(form_kind)
        if statement is None:
            return None, claim.method, f"unsupported form_kind: {form_kind}"

        method = "intro a b\n  constructor <;> norm_num [remainderConst, remainderXCoeff, powRem]"
        return statement, method, ""

    if claim.claim_type == "f2q1_student_coefficient_system":
        sum_lhs = claim.data.get("sum_lhs")
        sum_rhs = claim.data.get("sum_rhs")
        a_equation_kind = claim.data.get("a_equation_kind")
        a_rhs = claim.data.get("a_rhs")

        if not isinstance(sum_lhs, str) or not isinstance(sum_rhs, int):
            return None, claim.method, "missing sum_lhs/sum_rhs"

        if not isinstance(a_equation_kind, str) or not isinstance(a_rhs, int):
            return None, claim.method, "missing a_equation_kind/a_rhs"

        if a_equation_kind == "neg_a":
            a_statement = f"-candidateA = ({a_rhs} : ℤ)"
        elif a_equation_kind == "a":
            a_statement = f"candidateA = ({a_rhs} : ℤ)"
        else:
            return None, claim.method, f"unsupported a_equation_kind: {a_equation_kind}"

        statement = f"{sum_lhs} = ({sum_rhs} : ℤ) ∧ {a_statement}"
        return statement, "norm_num [candidateA, candidateB]", ""

    return None, claim.method, f"unsupported claim_type for F2Q1: {claim.claim_type}"


def check_one_f2q1_student_claim(
    claim: StudentClaim,
    run_id: str,
    index: int,
    timeout_seconds: int = 90,
) -> StudentClaimCheck:
    out_dir = CHECK_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    theorem_name = f"student_claim_check_{index}"
    lean_statement, method, unsupported_reason = _lean_statement_and_method_for_f2q1_claim(claim)

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
    lean_code = _build_f2q1_lean_code(claim, theorem_name, lean_statement, method)
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


def check_f2q1_student_claims(
    claims: List[StudentClaim],
    run_id: str | None = None,
) -> List[StudentClaimCheck]:
    run_id = run_id or time.strftime("%Y%m%dT%H%M%S")
    return [
        check_one_f2q1_student_claim(claim, run_id=run_id, index=i)
        for i, claim in enumerate(claims)
    ]


def checks_to_dicts(checks: List[StudentClaimCheck]) -> List[dict]:
    return [asdict(check) for check in checks]
