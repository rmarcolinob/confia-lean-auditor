from __future__ import annotations

import re

from confia_lean_auditor.core.schemas import FormalStep


ALLOWED_LEAN_METHODS = {"ring", "norm_num", "omega"}

ALLOWED_EXPR_RE = re.compile(r"^[0-9A-Za-z_\s+\-*/^()]+$")


class FormalStepValidationError(ValueError):
    pass


def has_balanced_parentheses(expr: str) -> bool:
    depth = 0

    for ch in expr:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False

    return depth == 0


def validate_restricted_polynomial_expr(expr: str) -> None:
    if not expr:
        raise FormalStepValidationError("Empty Lean expression.")

    if "\n" in expr or "\r" in expr:
        raise FormalStepValidationError("Lean expression cannot contain line breaks.")

    if not ALLOWED_EXPR_RE.fullmatch(expr):
        raise FormalStepValidationError(
            "Lean expression contains forbidden characters. "
            "Allowed: integers, variable a, +, -, *, ^, parentheses and spaces."
        )

    identifiers = re.findall(r"[A-Za-z_]+", expr)
    for ident in identifiers:
        if ident not in {"a", "i", "j", "c", "q", "n"}:
            raise FormalStepValidationError(
                "Forbidden identifier in Lean expression: " + ident
            )

    if not has_balanced_parentheses(expr):
        raise FormalStepValidationError("Unbalanced parentheses in Lean expression.")


def validate_lean_method(method: str) -> None:
    if method not in ALLOWED_LEAN_METHODS:
        raise FormalStepValidationError(
            "Forbidden Lean method: " + method
        )


def validate_formal_step(step: FormalStep) -> None:
    validate_restricted_polynomial_expr(step.lhs)
    validate_restricted_polynomial_expr(step.rhs)
    validate_lean_method(step.lean_method)
