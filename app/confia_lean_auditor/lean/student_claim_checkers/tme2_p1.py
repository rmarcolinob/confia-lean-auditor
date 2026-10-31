"""Opt-in P1 checks over existing grounded digital claims, never point rules.

Exact affine comparison is supplied by math_canonical. Finite integer domains
are enumerated from the problem's nonzero decimal digit premises. This module
does not infer prose, omitted algebra, ellipses, or a student's intended answer.
"""
import ast
import hashlib
import json
import re
import uuid
from dataclasses import asdict

from confia_lean_auditor.claims.common.fact_results import FactResultsBuilder
from confia_lean_auditor.claims.common.adapters import claim_from_student, validate_projection
from confia_lean_auditor.claims.common.schemas import Origin, SemanticRole, VerificationLink
from confia_lean_auditor.core.math_canonical import equivalent, compare_canonical, parse_math
from confia_lean_auditor.core.math_canonical.models import canonical_from_dict
from confia_lean_auditor.core.math_canonical.syntax import expression_syntax, syntax_text
from confia_lean_auditor.rubric.pauta.bridge import AuditorFactBundle, FactResult, record_fingerprint
from confia_lean_auditor.student_claims.digital_literals import validate_literal_record
from confia_lean_auditor.student_claims.grounding import VERSION, _digest, _payload, source_matches
from confia_lean_auditor.student_claims.schemas import StudentClaim
from confia_lean_auditor.student_claims.tme2_p1_digital import PROBLEM_ID

VERSION_CHECK = "tme2-p1-digital-check.v1"
FORWARD, REVERSE, DIFFERENCE = "100a+10b+c", "100c+10b+a", "99(a-c)"


def eq(left, right):
    return equivalent(left, right).status == "equivalent"


def expression(record):
    return (record.legacy_payload or {}).get("data", {}).get("expression", record.source.raw_text)


def sides(record):
    text = expression(record)
    parsed = parse_math(text)
    if parsed.status == "parsed" and parsed.canonical_form.kind == "equality" and text.count("=") == 1:
        return tuple(t.strip() for t in text.split("="))
    return None


def is_subtraction(text, left, right):
    node = expression_syntax(text)
    return (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub)
            and eq(syntax_text(node.left), left) and eq(syntax_text(node.right), right))


def integer_syntax(text):
    node = expression_syntax(text)
    return node is not None and all(isinstance(n, (ast.Expression, ast.Constant, ast.UnaryOp,
        ast.BinOp, ast.UAdd, ast.USub, ast.Add, ast.Sub, ast.Mult))
        and (not isinstance(n, ast.Constant) or type(n.value) is int) for n in ast.walk(node))


def literal_integer(text):
    node = expression_syntax(text)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        node = node.operand
    return isinstance(node, ast.Constant) and type(node.value) is int


def collection(record):
    form = record.canonical_form
    return form.value if form and form.family == "finite_collection" else None


def subject_is(value, text):
    subject = value["subject"]
    return bool(subject and "ordered_variables" not in subject and compare_canonical(
        canonical_from_dict(subject), parse_math(text).canonical_form).status == "equivalent")


def fact_status(value):
    return "verified" if value else "refuted"


def constant_result_status(text, expected):
    parsed = parse_math(text)
    if parsed.status != "parsed" or parsed.canonical_form.variables:
        return "unverified"
    comparison = equivalent(text, expected).status
    return {"equivalent": "verified", "not_equivalent": "refuted"}.get(comparison, "unverified")


class _Checks(FactResultsBuilder):
    def __init__(self, digital, solution_id, use_lean, run_id):
        super().__init__(digital, solution_id, problem_id=PROBLEM_ID, checker_version=VERSION_CHECK)
        self.use_lean, self.run_id = use_lean, run_id
        self.formal = {}

    def arithmetic(self, record):
        """Project exactly the written integer equality to the EXISTING checker."""
        if not self.use_lean:
            return None
        if record.record_id in self.formal:
            return self.formal[record.record_id]
        pair = sides(record)
        if not pair or not all(integer_syntax(x) for x in pair):
            return None
        from confia_lean_auditor.lean.student_claim_checker import check_one_student_claim
        claim = StudentClaim(id="tme2-arithmetic-" + hashlib.sha256(record.record_id.encode()).hexdigest()[:16],
            problem_id=PROBLEM_ID, claim_type="arithmetic_equality", raw_text=record.source.raw_text,
            normalized_text=record.source.raw_text, context=record.source.raw_text,
            data={"left_expr": pair[0], "right_expr": pair[1]})
        claim.grounding = dict(status="grounded", validator=VERSION, extraction_method=VERSION_CHECK,
            source_text=record.source.raw_text, source_start=record.source.source_start,
            source_end=record.source.source_end, source_sha256=record.source.source_sha256,
            payload_sha256=_digest(_payload(claim)))
        if not source_matches(claim, self.digital.source_text):
            return None  # Unsupported projection is not a mathematical failure.
        projected = claim_from_student(claim, solution_text=self.digital.source_text,
                                       rubric_links=record.rubric_links)
        result = asdict(check_one_student_claim(claim, self.run_id, len(self.formal)))
        self.records[projected.record_id] = projected
        self.formal[record.record_id] = (projected, result)
        return projected, result



def _check_a(checks, records):
    for record in records:
        pair = sides(record)
        text = pair[0] if pair else expression(record)
        if record.claim_type == "math_literal":
            if eq(text, "137"):
                checks.add("a.inverted_number_137", [record], True)
            elif eq(text, "594"):
                checks.add("a.result_594", [record], True)
        if not is_subtraction(text, "731", "137"):
            continue
        checks.add("a.inverted_number_137", [record], True)
        checks.add("a.subtraction_731_137", [record], True)
        if not pair:
            continue
        result_status = constant_result_status(pair[1], "594")
        correct = result_status == "verified"
        formal = checks.arithmetic(record)
        checks.add("a.result_594", [record, formal[0]] if formal else [record],
            formal[1]["status"] if formal else result_status,
            mechanism="student_lean" if formal else "canonical_equivalence",
            check=formal[1] if formal else None)
        # Exact single binary subtraction + literal result, with no other
        # assertions in the item. A wrong final number alone is insufficient.
        node = expression_syntax(pair[0])
        count = sum(isinstance(n, ast.BinOp) for n in ast.walk(node))
        start, end = checks.digital.item_ranges["a"]
        outside = (checks.digital.source_text[start:record.source.source_start]
                   + checks.digital.source_text[record.source.source_end:end])
        complete_assertion = not outside.strip(" \t\r\n.")
        if not correct and literal_integer(pair[1]) and count == 1 and len(records) == 1 and complete_assertion:
            checks.add("a.single_arithmetic_error", [record], True, metadata={
                "diagnosis": "one_written_subtraction_with_correct_operands_and_wrong_literal_result",
                "operands": [731, 137], "computed_result": 594, "written_result": pair[1],
                "operation_count": count, "item_claim_count": len(records)})


def _representations(records, target):
    """An expression or an unambiguous assignment to a fresh notation symbol.

    Digit symbols already have a meaning in the problem; `a = reverse` is not
    a definition of the reversed number. Conflicting definitions are unresolved.
    """
    matches = []
    for record in records:
        pair = sides(record)
        if pair is None:
            if eq(expression(record), target):
                matches.append(record)
            continue
        symbol = expression_syntax(pair[0])
        if not isinstance(symbol, ast.Name) or symbol.id in {"a", "b", "c"} or not eq(pair[1], target):
            continue
        definitions = [sides(other)[1] for other in records if sides(other)
                       and eq(sides(other)[0], symbol.id)]
        if all(eq(value, target) for value in definitions):
            matches.append(record)
    return matches


def _check_b(checks, records):
    for record in _representations(records, REVERSE):
        checks.add("b.reversed_number", [record], True, mechanism="canonical_equivalence")
    for record in records:
        pair = sides(record)
        parts = pair or (expression(record),)
        for part in parts:
            if is_subtraction(part, FORWARD, REVERSE):
                checks.add("b.subtraction", [record], True, mechanism="canonical_equivalence")
                if pair and eq(*pair) and not any(isinstance(n, ast.Name) and n.id == "b"
                        for n in ast.walk(expression_syntax(pair[1]))):
                    checks.add("b.middle_cancellation", [record], True, mechanism="canonical_equivalence")
                break
        if pair:
            left, right = map(expression_syntax, pair)
            # A written expansion -> factorization, not a repeated tautology.
            expanded = isinstance(left, ast.BinOp) and isinstance(left.op, (ast.Add, ast.Sub))
            if expanded:
                expanded = not any(isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult)
                    and any(isinstance(operand, ast.BinOp) and isinstance(operand.op, (ast.Add, ast.Sub))
                            for operand in (n.left, n.right)) for n in ast.walk(left))
            factored = False
            if isinstance(right, ast.BinOp) and isinstance(right.op, ast.Mult):
                factors = (syntax_text(right.left), syntax_text(right.right))
                factored = any((eq(scalar, "99") and eq(difference, "a-c")) or
                    (eq(scalar, "-99") and eq(difference, "c-a"))
                    for scalar, difference in (factors, factors[::-1]))
            if expanded and factored and eq(pair[0], DIFFERENCE) and eq(*pair):
                checks.add("b.factorization", [record], True, mechanism="canonical_equivalence")


def _formula(records):
    return _representations(records, DIFFERENCE)


def _check_c(checks, records):
    formulas = _formula(records)
    for r in formulas:
        checks.add("c.uses_expression", [r], True, mechanism="canonical_equivalence")
    bounds = []
    for bound in ("1<=c", "a<=9", "a>c"):
        matches = [r for r in records if eq(expression(r), bound)]
        if matches:
            bounds.append(matches[0])
    variables = [sides(r)[0] for r in formulas if sides(r)]
    expected = {99 * n for n in range(1, 9)}
    for record in records:
        value = collection(record)
        if not value or any(isinstance(x, list) for x in value["elements"]):
            continue
        observed = set(value["elements"])
        if subject_is(value, "a-c"):
            if len(bounds) == 3:
                checks.add("c.difference_domain", [*bounds, record], observed == set(range(1, 9)),
                    metadata={"integer_digit_premises": "1<=c<a<=9", "enumerated_domain": list(range(1, 9))})
            continue
        if value["subject"] is not None and not any(subject_is(value, var) for var in variables):
            continue
        missing, extra, correct = expected - observed, observed - expected, expected & observed
        meta = dict(expected=sorted(expected), observed=sorted(observed), missing=sorted(missing),
            extraneous=sorted(extra), correct_count=len(correct),
            duplicates=len(value["elements"]) - len(observed))
        for name, condition in (("complete_list", not missing), ("no_extraneous_values", not extra),
                ("single_list_error", len(missing) + len(extra) == 1),
                ("several_correct", len(correct) >= 2), ("some_correct", bool(correct))):
            checks.add("c." + name, [record], condition, metadata=meta)
        if formulas and correct:
            checks.add("c.pattern_recognized", [record, formulas[0]], True,
                mechanism="canonical_equivalence", metadata={**meta, "pattern": DIFFERENCE})


def _check_d(checks, records):
    pairs, choices = [], []
    for record in records:
        pair = sides(record)
        if pair:
            for lhs, rhs in (pair, pair[::-1]):
                if eq(lhs, DIFFERENCE) and eq(rhs, "594"):
                    checks.add("d.equation", [record], True, mechanism="canonical_equivalence")
                    break
            for lhs, rhs in (pair, pair[::-1]):
                if eq(lhs, "a-c"):
                    checks.add("d.difference_six", [record], constant_result_status(rhs, "6"), mechanism="canonical_equivalence")
                    break
        value = collection(record)
        if not value:
            continue
        if value["subject"] == {"ordered_variables": ["a", "c"]} and all(isinstance(x, list) for x in value["elements"]):
            observed = {tuple(x) for x in value["elements"]}
            expected = {(a, c) for a in range(1, 10) for c in range(1, 10) if a-c == 6}
            checks.add("d.digit_pairs", [record], observed == expected,
                metadata={"expected_pairs": sorted(expected), "observed_pairs": sorted(observed)})
            if observed == expected:
                pairs.append(record)
        if subject_is(value, "b") and all(type(x) is int for x in value["elements"]):
            correct = set(value["elements"]) == set(range(10))
            checks.add("d.middle_choices", [record], correct, metadata={"cardinality": len(set(value["elements"]))})
            if correct:
                choices.append(record)
    if pairs and choices:
        for record in records:
            pair = sides(record)
            node = expression_syntax(pair[0]) if pair else None
            if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult)):
                continue
            factors = (syntax_text(node.left), syntax_text(node.right))
            if not ((eq(factors[0], "3") and eq(factors[1], "10")) or
                    (eq(factors[0], "10") and eq(factors[1], "3"))):
                continue
            formal = checks.arithmetic(record)
            # Counting prerequisites have separate obligations; retain refs in
            # metadata so the formal result binds only to the written equality.
            checks.add("d.total_thirty", [record, formal[0]] if formal else [record],
                formal[1]["status"] if formal else constant_result_status(pair[1], "30"),
                mechanism="student_lean" if formal else "canonical_equivalence",
                check=formal[1] if formal else None,
                metadata={"counting_claim_ids": [pairs[0].record_id, choices[0].record_id]})


def verify_tme2_p1_digital(digital, solution_id, *, use_lean=True, run_id=None):
    """Validate source projections before any fact; no registry/default changes."""
    if run_id is not None and not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", run_id):
        raise ValueError("Unsafe Lean run identifier")
    # Every call retains its own proof artifacts, including repeated solution IDs.
    run_id = (run_id or "tme2-p1-pilot") + "-" + uuid.uuid4().hex
    checks = _Checks(digital, solution_id, use_lean, run_id)
    valid = []
    for record in digital.records:
        if record.problem_id != PROBLEM_ID:
            raise ValueError("Foreign problem record")
        if record.provenance.channel == "native":
            if not validate_literal_record(record, digital.source_text):
                raise ValueError("Inconsistent native source projection")
        else:
            validate_projection(record, solution_text=digital.source_text)
        a, b = record.source.source_start, record.source.source_end
        owners = tuple(k for k, (start, end) in digital.item_ranges.items()
                       if a is not None and start <= a < b <= end)
        if owners != record.rubric_links:
            raise ValueError("Digital item routing changed after extraction")
        if (record.source.attributable and record.source.grounding_status == "grounded"
                and record.semantic_role not in {SemanticRole.ASSUMPTION,
                    SemanticRole.QUOTED_STATEMENT, SemanticRole.REJECTED_ATTEMPT}):
            valid.append(record)
    for item, checker in zip("abcd", (_check_a, _check_b, _check_c, _check_d)):
        checker(checks, [r for r in valid if r.rubric_links == (item,)])
    return checks.finish()
