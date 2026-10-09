"""A failed proof is inconclusive; only a compiled negation refutes a claim."""
from dataclasses import replace
from pathlib import Path
import re
import subprocess
import time

from confia_lean_auditor.lean.run_lean import classify, detect_forbidden_tokens
from confia_lean_auditor.student_claims.schemas import StudentClaimCheck


def failure_outcome(proc):
    message = ((proc.stdout or "") + "\n" + (proc.stderr or "")).lower()
    category = classify(proc.returncode, [], proc.stdout or "", proc.stderr or "")
    if "unknown module" in message or "object file" in message or "no such file" in message:
        return "technical_error", "MISSING_MODULE"
    if category == "lean_timeout" or proc.returncode == 124:
        return "technical_error", "TIMEOUT"
    if category == "lean_error_unknown_identifier":
        return "technical_error", "UNKNOWN_IDENTIFIER"
    if category == "lean_error_unsolved_goals":
        return "unverified", "UNSOLVED_GOALS"
    if category == "lean_error_synthesis_failed":
        return "unverified", "SYNTHESIS_ERROR"
    if "tactic" in message and ("failed" in message or "failure" in message):
        return "unverified", "TACTIC_FAILED"
    if "type mismatch" in message or "application type" in message or "elaborat" in message:
        return "technical_error", "ELABORATION_ERROR"
    return "technical_error", "PROCESS_ERROR"


def negation_method(claim, method):
    """Use the same trusted definitions; never derive falsity from diagnostics."""
    if claim.claim_type == "f2q1_student_reduced_form":
        return "intro h\n  have contra := h 1 1\n  norm_num [remainderConst, remainderXCoeff, powRem] at contra"
    if claim.problem_id == "ITA2025F2Q3":
        return ("intro h\n  norm_num [sinAlphaCandidate, cosAlphaCandidate, sinBetaCandidate, "
                "cosBetaCandidate] at h <;> nlinarith [sqrt7_sq, sqrt7_nonneg, one_lt_sqrt7]")
    definitions = re.search(r"norm_num\s*(\[[^\]]*\])", method)
    return "norm_num" + (" " + definitions.group(1) if definitions else "")


def evaluate_student_proof(*, claim, lean_file: Path, lean_statement, method,
                           lean_code, negation_code, runner, timeout_seconds):
    check = StudentClaimCheck(id=claim.id, problem_id=claim.problem_id,
        claim_type=claim.claim_type, raw_text=claim.raw_text, normalized_text=claim.normalized_text,
        lean_statement=lean_statement, method=method, status="unverified", compiled=False,
        lean_file=str(lean_file), stdout="", stderr="", data=claim.data)
    started = time.monotonic()
    try:
        lean_file.write_text(lean_code, encoding="utf-8")
        if detect_forbidden_tokens(lean_code):
            return replace(check, status="technical_error", failure_category="INVALID_PROOF")
        proc = runner(lean_file, timeout_seconds=timeout_seconds)
        check = replace(check, stdout=proc.stdout or "", stderr=proc.stderr or "")
        if proc.returncode == 0 and "declaration uses 'sorry'" not in (check.stdout + check.stderr).lower():
            return replace(check, status="verified", compiled=True)
        status, category = failure_outcome(proc)
        check = replace(check, status=status, failure_category=category)
        if status == "technical_error":
            return check
        # A separate theorem proves NOT the original proposition. Failed
        # compilation of either theorem is never negative mathematical evidence.
        negative = lean_file.with_name(lean_file.stem + "_refutation.lean")
        negative.write_text(negation_code, encoding="utf-8")
        check = replace(check, refutation_lean_file=str(negative))
        if detect_forbidden_tokens(negation_code):
            return replace(check, status="technical_error", failure_category="INVALID_PROOF")
        remaining = timeout_seconds - (time.monotonic() - started)
        if remaining <= 0:
            return replace(check, status="technical_error", failure_category="TIMEOUT")
        neg = runner(negative, timeout_seconds=remaining)
        check = replace(check, refutation_stdout=neg.stdout or "", refutation_stderr=neg.stderr or "")
        if neg.returncode == 0 and "declaration uses 'sorry'" not in (check.refutation_stdout + check.refutation_stderr).lower():
            return replace(check, status="refuted", refutation_verified=True, failure_category=None)
        status, category = failure_outcome(neg)
        return replace(check, status=status, failure_category=category)
    except subprocess.TimeoutExpired:
        return replace(check, status="technical_error", failure_category="TIMEOUT",
                       stderr="Formal verification timed out")
    except OSError:
        return replace(check, status="technical_error", failure_category="PROCESS_ERROR",
                       stderr="Formal verification unavailable")
