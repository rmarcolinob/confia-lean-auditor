from __future__ import annotations

import re
import subprocess
import time
from dataclasses import asdict
from pathlib import Path

from confia_lean_auditor.student_claims.schemas import StudentClaim, StudentClaimCheck


ROOT_DIR = Path(__file__).resolve().parents[3]
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
CHECK_DIR = ARTIFACTS_DIR / "student_claim_checks"

F2Q8_EXPECTED_FINAL_ANSWER = 1013


def _run_lean_file(lean_file: Path, timeout_seconds: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["lake", "env", "lean", str(lean_file)],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )


def _lean_int_expr(expr: str) -> str:
    expr = expr.strip()

    def repl(match: re.Match[str]) -> str:
        return f"({match.group(0)} : ℤ)"

    return re.sub(r"-?\d+", repl, expr, count=1)


def _expected_det_value(k: int) -> int:
    return k if k % 2 == 1 else -k


def _student_det_expr(formula_kind: str, k: int) -> str | None:
    if formula_kind == "minus_one_pow_k_minus_1_times_k":
        return f"((-1 : ℤ) ^ ({k} - 1) * ({k} : ℤ))"

    if formula_kind == "minus_one_pow_k_times_k":
        return f"((-1 : ℤ) ^ {k} * ({k} : ℤ))"

    if formula_kind == "minus_one_pow_k_minus_1_times_k_plus_1":
        return f"((-1 : ℤ) ^ ({k} - 1) * (({k} : ℤ) + 1))"

    if formula_kind == "positive_k":
        return f"({k} : ℤ)"

    if formula_kind == "negative_k":
        return f"-({k} : ℤ)"

    return None


def _det_formula_check_statement(formula_kind: str) -> str | None:
    checks: list[str] = []

    for k in range(1, 9):
        student_expr = _student_det_expr(formula_kind, k)
        if student_expr is None:
            return None

        expected = _expected_det_value(k)
        checks.append(f"{student_expr} = ({expected} : ℤ)")

    return " ∧ ".join(checks)


def _lean_statement_for_claim(claim: StudentClaim) -> tuple[str | None, str]:
    if claim.claim_type == "arithmetic_equality":
        left = claim.data.get("left_expr")
        right = claim.data.get("right_expr")

        if not isinstance(left, str) or not isinstance(right, str):
            return None, "missing left_expr/right_expr"

        return f"({_lean_int_expr(left)}) = ({_lean_int_expr(right)})", ""

    if claim.claim_type == "f2q8_student_final_answer":
        value = claim.data.get("student_value")

        if not isinstance(value, int):
            return None, "missing student_value"

        return f"({F2Q8_EXPECTED_FINAL_ANSWER} : ℤ) = ({value} : ℤ)", ""

    if claim.claim_type == "f2q8_student_alternating_sum_value":
        value = claim.data.get("student_value")

        if not isinstance(value, int):
            return None, "missing student_value"

        return f"({F2Q8_EXPECTED_FINAL_ANSWER} : ℤ) = ({value} : ℤ)", ""

    if claim.claim_type == "f2q8_student_pair_count":
        count = claim.data.get("pair_count")

        if not isinstance(count, int):
            return None, "missing pair_count"

        # Em 2025 termos, há 1012 pares e um termo restante:
        # 2 * 1012 + 1 = 2025.
        return f"(2 : ℤ) * ({count} : ℤ) + 1 = (2025 : ℤ)", ""

    if claim.claim_type == "f2q8_student_pair_reduction":
        count = claim.data.get("subtracted_pair_count")
        stated_value = claim.data.get("stated_value")

        if not isinstance(count, int):
            return None, "missing subtracted_pair_count"

        checks = [
            # A redução contextual correta da F2Q8 deve usar 1012 pares:
            # 2025 - 1012 = 1013.
            f"(2025 : ℤ) - ({count} : ℤ) = ({F2Q8_EXPECTED_FINAL_ANSWER} : ℤ)"
        ]

        if isinstance(stated_value, int):
            # Verifica também o resultado que o aluno escreveu depois do sinal de igualdade.
            checks.append(f"(2025 : ℤ) - ({count} : ℤ) = ({stated_value} : ℤ)")
            checks.append(f"({stated_value} : ℤ) = ({F2Q8_EXPECTED_FINAL_ANSWER} : ℤ)")

        return " ∧ ".join(checks), ""

    if claim.claim_type == "f2q8_student_det_formula":
        formula_kind = claim.data.get("formula_kind")

        if not isinstance(formula_kind, str):
            return None, "missing formula_kind"

        statement = _det_formula_check_statement(formula_kind)
        if statement is None:
            return None, f"unsupported formula_kind: {formula_kind}"

        return statement, ""

    return None, f"unsupported claim_type: {claim.claim_type}"

def _build_lean_code(claim: StudentClaim, theorem_name: str, lean_statement: str) -> str:
    lines: list[str] = []
    lines.append("import Mathlib")
    lines.append("")
    lines.append("namespace ConfiaStudentClaimCheck")
    lines.append("")
    lines.append(f"/-- Afirmação extraída do aluno: {claim.raw_text} -/")
    lines.append(f"theorem {theorem_name} :")
    lines.append(f"    {lean_statement} := by")
    lines.append(f"  {claim.method}")
    lines.append("")
    lines.append("end ConfiaStudentClaimCheck")
    lines.append("")

    return "\n".join(lines)


def check_one_student_claim(
    claim: StudentClaim,
    run_id: str,
    index: int,
    timeout_seconds: int = 90,
) -> StudentClaimCheck:
    out_dir = CHECK_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    theorem_name = f"student_claim_check_{index}"
    lean_statement, unsupported_reason = _lean_statement_for_claim(claim)

    if lean_statement is None:
        return StudentClaimCheck(
            id=claim.id,
            problem_id=claim.problem_id,
            claim_type=claim.claim_type,
            raw_text=claim.raw_text,
            normalized_text=claim.normalized_text,
            lean_statement="",
            method=claim.method,
            status="unsupported",
            compiled=False,
            lean_file=None,
            stdout="",
            stderr=unsupported_reason,
            data=claim.data,
        )

    lean_file = out_dir / f"{theorem_name}.lean"
    lean_code = _build_lean_code(claim, theorem_name, lean_statement)
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
            method=claim.method,
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
            method=claim.method,
            status="error",
            compiled=False,
            lean_file=str(lean_file),
            stdout=exc.stdout or "",
            stderr=f"timeout after {timeout_seconds}s",
            data=claim.data,
        )


def check_student_claims(
    claims: list[StudentClaim],
    run_id: str | None = None,
) -> list[StudentClaimCheck]:
    run_id = run_id or time.strftime("%Y%m%dT%H%M%S")
    return [
        check_one_student_claim(claim, run_id=run_id, index=i)
        for i, claim in enumerate(claims)
    ]


def checks_to_dicts(checks: list[StudentClaimCheck]) -> list[dict]:
    return [asdict(check) for check in checks]
