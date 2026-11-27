"""Opt-in syntax for complete digital integer/finite-collection statements.

No expected values, problem rules or scores. No prose interpretation or ellipsis
completion. Claims use the existing MathClaimRecord native channel.
"""
import ast
import hashlib
import re

from confia_lean_auditor.claims.common.schemas import (
    CanonicalForm, MathClaimRecord, Origin, Provenance, SourceBinding,
)
from confia_lean_auditor.core.math_canonical import parse_math
from confia_lean_auditor.student_claims.generic_math import contextual_role

VERSION = "digital-literal.v1"


def _integer(node):
    sign = 1
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        sign = -1 if isinstance(node.op, ast.USub) else 1
        node = node.operand
    if isinstance(node, ast.Constant) and type(node.value) is int and abs(node.value) <= 10**9:
        return sign * node.value
    raise ValueError("Not a bounded integer literal")


def literal_form(text):
    if len(text) > 2048:
        return None
    parts = re.split(r"∈|\\in\b", text)
    if len(parts) > 2:
        return None
    subject = parts[0].strip() if len(parts) == 2 else None
    literal = parts[-1].strip()
    try:
        node = ast.parse(literal, mode="eval").body
        if not isinstance(node, (ast.Set, ast.List, ast.Tuple)):
            if subject is not None:
                return None
            value = _integer(node)
            form = parse_math(literal).canonical_form
            if form is None:
                return None
            return "math_literal", CanonicalForm(family="mathematical", subject="unlabeled_value",
                value=form.to_dict(), method=VERSION, mathematical_form=form.to_dict())
        if not 1 <= len(node.elts) <= 128:
            return None
        elements = []
        for member in node.elts:
            if isinstance(member, ast.Tuple) and len(member.elts) == 2:
                elements.append([_integer(x) for x in member.elts])
            else:
                elements.append(_integer(member))
        if len({isinstance(x, list) for x in elements}) > 1:
            return None
        subject_form = None
        if subject is not None:
            # Ordered variable pair is explicit syntax, never inferred from prose.
            pair = ast.parse(subject, mode="eval").body if "," in subject else None
            if isinstance(pair, ast.Tuple) and len(pair.elts) == 2 and all(
                    isinstance(x, ast.Name) and re.fullmatch(r"[A-Za-z]", x.id) for x in pair.elts):
                subject_form = {"ordered_variables": [x.id for x in pair.elts]}
            else:
                parsed = parse_math(subject)
                if parsed.status != "parsed" or parsed.canonical_form.kind != "expression":
                    return None
                subject_form = parsed.canonical_form.to_dict()
        return "math_finite_collection", CanonicalForm(family="finite_collection",
            subject="membership" if subject is not None else "unlabeled_collection",
            value={"subject": subject_form, "elements": elements,
                   "container": "set" if isinstance(node, ast.Set) else "sequence"}, method=VERSION)
    except (ValueError, SyntaxError, TypeError, RecursionError):
        return None


def extract_digital_literals(problem_id, source, *, statement_text=""):
    if len(source) > 20000:
        return ()
    digest = hashlib.sha256(source.encode()).hexdigest()
    records = []
    for line in re.finditer(r"[^\n]+", source):
        raw = line[0].strip()
        a = line.start() + len(line[0]) - len(line[0].lstrip())
        b = a + len(raw)
        form = literal_form(raw)
        if form is None:
            continue
        role, attributable = contextual_role(source, a, b, statement_text)
        kind, canonical = form
        records.append(MathClaimRecord(record_id=f"native:{VERSION}:{a}:{b}", problem_id=problem_id,
            claim_type=kind, source=SourceBinding(grounding_status="grounded", raw_text=raw,
                source_start=a, source_end=b, source_sha256=digest, attributable=attributable),
            provenance=Provenance(origin=Origin.STUDENT_EXPLICIT if attributable else Origin.STUDENT_CANDIDATE,
                channel="native", extraction_method=VERSION), semantic_role=role,
            canonical_form=canonical, canonicalization_status="parsed",
            canonicalization_reason="Complete bounded literal syntax; no truth or score inferred"))
    return tuple(records)


def validate_literal_record(record, source, *, statement_text=""):
    return any(r == record.model_copy(update={"verification_results": (), "rubric_links": ()})
               for r in extract_digital_literals(record.problem_id, source, statement_text=statement_text))
