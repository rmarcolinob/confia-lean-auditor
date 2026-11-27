"""Opt-in native real-algebra projections using the existing proof lifecycle.

The caller supplies a trusted, source-derived proposition, never student Lean
code. Re-extraction and the full projection payload are checked before running.
Geometry is not formalized by this module.
"""
import ast
import hashlib
from dataclasses import asdict

from confia_lean_auditor.claims.common.schemas import Provenance
from confia_lean_auditor.core.math_canonical.syntax import expression_syntax
from confia_lean_auditor.core.math_canonical.rational import rational_value
from confia_lean_auditor.lean.student_claim_checker import CHECK_DIR, _run_lean_file
from confia_lean_auditor.lean.student_proof import evaluate_student_proof
from confia_lean_auditor.student_claims.schemas import StudentClaim
from confia_lean_auditor.student_claims.grounding import _digest, _payload


def lean_real_expression(text, *, number_domain="R", variables=("x", "h", "c")):
    """Bounded grammar: exact numbers, x/h/c, + - * /constant and small powers."""
    if number_domain not in {"R", "Z"}:
        raise ValueError("Unsupported formal number domain")
    domain = "ℝ" if number_domain == "R" else "ℤ"
    allowed = set(variables) & {"x", "h", "c", "n", "m", "q", "S"}
    def render(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return f"({node.value} : {domain})"
        if isinstance(node, ast.Name) and node.id in allowed:
            return node.id
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return f"(-{render(node.operand)})" if isinstance(node.op, ast.USub) else render(node.operand)
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Pow) and isinstance(node.right, ast.Constant) and type(node.right.value) is int and 0 <= node.right.value <= 4:
                return f"({render(node.left)} ^ {node.right.value})"
            operators = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}
            if type(node.op) in operators:
                if isinstance(node.op, ast.Div) and (number_domain == "Z" or rational_value(ast.unparse(node.right)) in {None, 0}):
                    raise ValueError("Only nonzero constant denominators")
                return f"({render(node.left)} {operators[type(node.op)]} {render(node.right)})"
        raise ValueError("Unsupported real expression")
    try:
        return render(expression_syntax(text))
    except (TypeError, ValueError, RecursionError):
        return None


def check_real_record(record, digital, *, collect, statement, proof, refutation,
                      context, run_id, index, timeout_seconds=90, number_domain="R"):
    """Bind the exact native assertion AND explicit contextual assumptions.

    Native records have no legacy execution projection. The StudentClaim here
    is only the existing lifecycle carrier; this validator is never used by ITA.
    """
    if number_domain not in {"R", "Z"}:
        raise ValueError("Unsupported formal number domain")
    original = record
    items = {k: digital.source_text[a:b] for k, (a, b) in digital.item_ranges.items()}
    fresh = collect(items)
    if fresh != digital or record not in fresh.records or not record.source.attributable:
        return None
    identifier = "real-" + hashlib.sha256((record.record_id + statement).encode()).hexdigest()[:20]
    data = {"native_assertion": record.canonical_form.model_dump(mode="json"),
            "number_domain": number_domain, "formal_statement": statement, "context": context}
    claim = StudentClaim(id=identifier, problem_id=record.problem_id, claim_type="math_relation",
        raw_text=record.source.raw_text, normalized_text=record.source.raw_text,
        context=record.source.raw_text, data=data)
    claim.grounding = dict(status="grounded", validator="native-real-projection.v1",
        extraction_method="native-real-projection.v1", source_text=record.source.raw_text,
        source_start=record.source.source_start, source_end=record.source.source_end,
        source_sha256=record.source.source_sha256, payload_sha256=_digest(_payload(claim)))
    frozen = asdict(claim)

    def valid(candidate):
        return (asdict(candidate) == frozen and record == original and record in fresh.records
                and digital.source_text[record.source.source_start:record.source.source_end] == record.source.raw_text
                and hashlib.sha256(digital.source_text.encode()).hexdigest() == record.source.source_sha256)

    projected = record.model_copy(update={"record_id": "native:" + identifier, "claim_type": "math_relation",
        "provenance": Provenance(origin=record.provenance.origin, channel="native", legacy_id=identifier,
            extraction_method="native-real-projection.v1"), "legacy_payload": frozen})
    directory = CHECK_DIR / run_id
    directory.mkdir(parents=True, exist_ok=True)
    name = f"real_check_{index}"
    code = f"import Mathlib\n\ntheorem {name} : {statement} := by\n  {proof}\n"
    negative = f"import Mathlib\n\ntheorem {name}_refutation : ¬ ({statement}) := by\n  {refutation}\n"
    check = evaluate_student_proof(claim=claim, lean_file=directory / (name + ".lean"),
        lean_statement=statement, method=proof, lean_code=code, negation_code=negative,
        runner=_run_lean_file, timeout_seconds=timeout_seconds, grounding_validator=valid)
    return projected, check
