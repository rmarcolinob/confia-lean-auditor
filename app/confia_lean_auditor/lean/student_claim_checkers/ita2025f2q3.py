from __future__ import annotations

import subprocess
import time
from dataclasses import asdict
from typing import List

from confia_lean_auditor.lean.student_claim_checker import CHECK_DIR, _run_lean_file
from confia_lean_auditor.student_claims.schemas import StudentClaim, StudentClaimCheck


ALLOWED_LHS = {
    "sinBetaCandidate",
    "cosBetaCandidate",
    "sinAlphaCandidate",
    "cosAlphaCandidate",
}

ALLOWED_EXPRS = {
    "1 / 2",
    "-1 / 2",
    "- (sqrt7 + 1) / 4",
    "- (1 + sqrt7) / 4",
    "(-1 - sqrt7) / 4",
    "(sqrt7 + 1) / 4",
    "(1 - sqrt7) / 4",
    "- (sqrt7 - 1) / 4",
    "(sqrt7 - 1) / 4",
    "- sqrt7 / 4",
    "sqrt7 / 4",
    "-3 / 4",
    "3 / 4",
    "(5 + sqrt7) / 8",
    "(sqrt7 + 5) / 8",
    "(5 - sqrt7) / 8",
}


def _build_f2q3_lean_code(
    claim: StudentClaim,
    theorem_name: str,
    lean_statement: str,
    method: str,
) -> str:
    safe_raw = claim.raw_text.replace("-/", "-∕")

    return f'''import ConfiaLeanAuditor.Problems.ITA2025F2Q3.Statement

namespace ConfiaStudentClaimCheck.ITA2025F2Q3

open ConfIA.LeanAuditor.ITA2025F2Q3

/-- Afirmação extraída do aluno: {safe_raw} -/
theorem {theorem_name} :
    {lean_statement} := by
  {method}

end ConfiaStudentClaimCheck.ITA2025F2Q3
'''


def _lean_statement_and_method_for_f2q3_claim(
    claim: StudentClaim,
) -> tuple[str | None, str, str]:
    if claim.claim_type == "f2q3_student_beta_difference":
        expr = claim.data.get("value_expr")
        if expr not in ALLOWED_EXPRS:
            return None, claim.method, "unsupported beta difference expression"

        statement = f"cosBetaCandidate - sinBetaCandidate = ({expr} : ℝ)"
        method = "unfold cosBetaCandidate sinBetaCandidate sqrt7; ring"
        return statement, method, ""

    if claim.claim_type == "f2q3_student_candidate_value":
        lhs = claim.data.get("lean_lhs")
        expr = claim.data.get("expr")

        if lhs not in ALLOWED_LHS:
            return None, claim.method, "unsupported lhs"
        if expr not in ALLOWED_EXPRS:
            return None, claim.method, "unsupported expression"

        statement = f"{lhs} = ({expr} : ℝ)"

        if lhs == "sinBetaCandidate":
            method = "unfold sinBetaCandidate; ring"
        elif lhs == "cosBetaCandidate":
            method = "unfold cosBetaCandidate; ring"
        elif lhs == "sinAlphaCandidate":
            method = "unfold sinAlphaCandidate; ring"
        elif lhs == "cosAlphaCandidate":
            method = "unfold cosAlphaCandidate; norm_num"
        else:
            return None, claim.method, "unsupported lhs"

        return statement, method, ""

    if claim.claim_type == "f2q3_student_final_sin_sum":
        expr = claim.data.get("expr")
        if expr not in ALLOWED_EXPRS:
            return None, claim.method, "unsupported final expression"

        statement = (
            "sinAlphaCandidate * cosBetaCandidate + "
            f"cosAlphaCandidate * sinBetaCandidate = ({expr} : ℝ)"
        )
        method = (
            "unfold sinAlphaCandidate cosAlphaCandidate sinBetaCandidate "
            "cosBetaCandidate; ring_nf; rw [sqrt7_sq]; ring"
        )
        return statement, method, ""

    if claim.claim_type == "f2q3_student_final_answer":
        expr = claim.data.get("expr")
        if expr not in ALLOWED_EXPRS:
            return None, claim.method, "unsupported final answer expression"

        statement = f"(5 + sqrt7) / 8 = ({expr} : ℝ)"
        method = "ring_nf"
        return statement, method, ""

    return None, claim.method, f"unsupported claim_type for F2Q3: {claim.claim_type}"


def check_one_f2q3_student_claim(
    claim: StudentClaim,
    run_id: str,
    index: int,
    timeout_seconds: int = 90,
) -> StudentClaimCheck:
    out_dir = CHECK_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    theorem_name = f"student_claim_check_{index}"
    lean_statement, method, unsupported_reason = _lean_statement_and_method_for_f2q3_claim(claim)

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
    lean_code = _build_f2q3_lean_code(claim, theorem_name, lean_statement, method)
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


def check_f2q3_student_claims(
    claims: List[StudentClaim],
    run_id: str | None = None,
) -> List[StudentClaimCheck]:
    run_id = run_id or time.strftime("%Y%m%dT%H%M%S")
    return [
        check_one_f2q3_student_claim(claim, run_id=run_id, index=i)
        for i, claim in enumerate(claims)
    ]


def checks_to_dicts(checks: List[StudentClaimCheck]) -> List[dict]:
    return [asdict(check) for check in checks]
