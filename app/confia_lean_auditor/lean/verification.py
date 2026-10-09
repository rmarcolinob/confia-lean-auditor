"""Verification availability is independent from mathematical truth."""
from types import SimpleNamespace

from confia_lean_auditor.lean.student_proof import failure_outcome


def verification_state(result) -> str:
    def field(name, default=None):
        return result.get(name, default) if isinstance(result, dict) else getattr(result, name, default)
    status = field("status")
    if status == "verified":
        return "available"
    if status in {"unverified", "failed", "unsupported", "invalid_formal_step", "invalid_forbidden_token",
                  "invalid_uses_sorry", "lean_error_unsolved_goals", "lean_error_synthesis_failed"}:
        return "partial"
    if status in {"technical_error", "error", "lean_timeout", "lean_error_unknown_identifier"}:
        return "technical_error"
    outcome, _ = failure_outcome(SimpleNamespace(returncode=field("exit_code", 1),
        stdout=field("stdout", ""), stderr=field("stderr", "") or str(status or "")))
    return "partial" if outcome == "unverified" else "technical_error"
