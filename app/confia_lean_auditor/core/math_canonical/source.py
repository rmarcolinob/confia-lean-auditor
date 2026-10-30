"""Conservative clause boundaries; source attribution remains owned by P0."""
import re
from confia_lean_auditor.core.audit_math_projection import strip_audit_equation_prefix
from .parser import parse_math


def mathematical_clauses(text):
    if len(text)>4000:
        return
    for clause in re.split(r'[\n;:]|(?<!\d)\.|\.(?!\d)',text):
        clause=clause.strip()
        clause=strip_audit_equation_prefix(clause)
        # No substring search in an expression, and no truncation of its RHS.
        parsed=parse_math(clause)
        if parsed.status=='parsed':
            yield clause,parsed.canonical_form
