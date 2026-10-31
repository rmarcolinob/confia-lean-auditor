"""P3 facts from grounded assertions and a sourced six-compartment state.

No points, LLM, image interpretation, or guessed intermediate assertions.
Conditional/global arithmetic facts require strategy context in the pauta.
"""
import ast
import hashlib
import json
import re
import uuid
from dataclasses import asdict
from fractions import Fraction
from itertools import product

from confia_lean_auditor.claims.common.fact_results import FactResultsBuilder
from confia_lean_auditor.core.math_canonical.rational import rational_value, weighted_sum_matches
from confia_lean_auditor.core.math_canonical.syntax import expression_syntax, syntax_text
from confia_lean_auditor.student_claims.tme2_p3_digital import PROBLEM_ID, collect_tme2_p3_digital
from .rational_equality import check_rational_record

VERSION = "tme2-p3-check.v1"


def quantity(record):
    form = record.canonical_form
    return form.subject if form and form.family == "named_quantity" else None


def written_expression(record):
    if quantity(record):
        return record.canonical_form.value["expression"]
    return (record.legacy_payload or {}).get("data", {}).get("expression", record.source.raw_text)


def value_status(record, expected):
    """Every written equality must hold; matching only the last answer is unsafe."""
    parts = written_expression(record).split("=")
    values = [rational_value(p.strip()) for p in parts]
    if not values or None in values:
        return "unverified"
    return "verified" if all(v == expected for v in values) else "refuted"


def by_quantity(records, key):
    return [r for r in records if quantity(r) == key]


def asserted_set(record):
    value = record.canonical_form.value
    return frozenset(value["value"]) if value.get("value_kind") == "integer_set" else None


def assertions_in_item(digital, item):
    return [r for r in digital.records if r.rubric_links == (item,) and r.source.attributable
            and r.source.grounding_status == "grounded"]


def standalone_math(record, source):
    """An isolated mathematical assertion, not a fragment under an unknown label."""
    if quantity(record) is not None:
        return False
    if (record.claim_type == "math_value"
            and (record.legacy_payload or {}).get("data", {}).get("concept") != "answer"):
        return False
    start, end = record.source.source_start, record.source.source_end
    if start is None:
        return False
    line_start = source.rfind("\n", 0, start) + 1
    line_end = source.find("\n", end)
    line_end = len(source) if line_end == -1 else line_end
    return source[line_start:line_end].strip() == record.source.raw_text


class P3Checks(FactResultsBuilder):
    def __init__(self, digital, solution_id, machine, use_lean, run_id):
        super().__init__(digital, solution_id, problem_id=PROBLEM_ID, checker_version=VERSION)
        self.machine, self.use_lean = machine, use_lean
        self.state_metadata = {"machine_source": machine.source_reference,
            "machine_sha256": hashlib.sha256(json.dumps(machine.stacks).encode()).hexdigest()}
        if run_id is not None and not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", run_id):
            raise ValueError("Unsafe run ID")
        self.run_id = (run_id or "tme2-p3") + "-" + uuid.uuid4().hex
        self.formal = {}

    def observe(self, fact_id, records, status, **metadata):
        self.add(fact_id, records, status, metadata={
            "student_asserted": [r.record_id for r in records],
            **self.state_metadata, **metadata})

    def numerical(self, fact_id, record, expected, **metadata):
        status = value_status(record, expected)
        expression = written_expression(record)
        formal = None
        # A true arithmetic equality with the WRONG value does not formally
        # refute this expected answer. Keep it a canonical mismatch instead.
        parts = expression.split("=")
        eligible = len(parts) == 2 and rational_value(parts[0]) == expected
        if self.use_lean and eligible:
            if record.record_id not in self.formal:
                self.formal[record.record_id] = check_rational_record(record, expression,
                    self.digital.source_text, run_id=self.run_id, index=len(self.formal))
            formal = self.formal[record.record_id]
        if formal:
            projected, check = formal
            self.records[projected.record_id] = projected
            self.add(fact_id, [record, projected], check.status, mechanism="student_lean",
                check=asdict(check), metadata={"expected_rational": str(expected),
                    "student_asserted": record.record_id,
                    "formal_scope": "written_rational_equality_only", **self.state_metadata, **metadata})
        else:
            self.add(fact_id, [record], status, mechanism="canonical_equivalence",
                metadata={"expected_rational": str(expected), "student_asserted": record.record_id,
                          **self.state_metadata, **metadata})


def _a(checks, records):
    white = checks.machine.bottom_colors.count("white")
    for r in by_quantity(records, "inferiores_brancas"):
        checks.observe("a.bottom_white_count", [r], value_status(r, Fraction(white)),
            engine_derived={"initial_bottom_colors": checks.machine.bottom_colors, "white_count": white})
    for r in records:
        if quantity(r) == "primeira_branca" or standalone_math(r, checks.digital.source_text):
            checks.numerical("a.first_white_probability", r, Fraction(white, 6),
                meaning="first-draw probability; isolated answer explicitly allowed")


def _b(checks, records):
    pairs = checks.machine.second_white_pairs()
    sample_size = len(checks.machine.ordered_pairs())
    different = sorted((i, j) for i, j in pairs if i != j)
    same = frozenset(i for i, j in pairs if i == j)
    for key, fact, expected in (("pares_ordenados", "b.ordered_pairs", sample_size),
                               ("favoraveis_distintos", "b.different_favorable", len(different))):
        for r in by_quantity(records, key):
            checks.observe(fact, [r], value_status(r, Fraction(expected)),
                engine_derived={"sample_space_size": sample_size, "uniform_ordered_pairs": True,
                                "different_favorable_pairs": different})
    for r in by_quantity(records, "repeticao_branca"):
        checks.observe("b.same_compartment", [r], asserted_set(r) == same,
            engine_derived={"same_compartment_favorable": sorted(same)})
    for r in records:
        if quantity(r) in {"segunda_branca", "arvore_total"} or standalone_math(r, checks.digital.source_text):
            checks.numerical("b.second_white_probability", r, Fraction(len(pairs), sample_size))

    branches = checks.machine.second_white_branches()
    candidates = [by_quantity(records, f"ramo_{i}") for i in range(1, 7)]
    totals = by_quantity(records, "arvore_total")
    # All six conditional branch statements must exist. A correct total or
    # the word 'tree' alone is never a complete alternative proof.
    if all(candidates) and totals:
        selected = [r for group in candidates for r in group]
        statuses = [value_status(r, probability) for group, probability in zip(candidates, branches) for r in group]
        for total in totals:
            expression = written_expression(total)
            parts = expression.split("=")
            shape = len(parts) == 2 and weighted_sum_matches(parts[0], [Fraction(1, 6)] * 6, branches)
            status = value_status(total, Fraction(len(pairs), sample_size))
            if "unverified" in statuses or status == "unverified":
                result = "unverified"
            else:
                result = all(s == "verified" for s in statuses) and status == "verified" and shape
            checks.observe("b.alternative_complete", [*selected, total], result,
                engine_derived={"uniform_branch_weights": ["1/6"] * 6,
                    "conditional_branch_probabilities": [str(p) for p in branches]},
                student_asserted_branch_ids=[r.record_id for r in selected],
                method="complete_conditional_decomposition", written_weighted_sum=shape)


def _c(checks, records):
    machine = checks.machine
    continuation = by_quantity(records, "continuar")
    continue_valid = bool(continuation) and all(asserted_set(r) == machine.continue_compartments() for r in continuation)
    for r in continuation:
        checks.observe("c.continue_compartments", [r], asserted_set(r) == machine.continue_compartments(),
            engine_derived={"continue_compartments": sorted(machine.continue_compartments())})
    probabilities, strategy_valid, conditional_valid = [], [], []
    context_ids = [r.record_id for r in continuation]
    for compartment in (1, 2):
        best, maximum = machine.best_choices(compartment)
        probabilities.append(Fraction(maximum, 6))
        combinations = list(product(by_quantity(records, f"estrategia_{compartment}"),
                                    by_quantity(records, f"contagem_{compartment}")))
        states = []
        for strategy, count in combinations:
            color = strategy.canonical_form.value.get("value")
            number_status = value_status(count, Fraction(maximum))
            status = "unverified" if number_status == "unverified" else color in best and number_status == "verified"
            states.append(status is True)
            context_ids.extend((strategy.record_id, count.record_id))
            checks.observe(f"c.strategy_case_{compartment}", [strategy, count], status,
                engine_derived={"bottom_colors_after_first": machine.after_first(compartment),
                    "counts": dict(machine.counts_after_first(compartment)), "optimal_colors": sorted(best)},
                student_color=color)
        strategy_valid.append(bool(states) and all(states))
        conditionals = by_quantity(records, f"condicional_{compartment}")
        conditional_valid.append(bool(conditionals) and strategy_valid[-1] and
            all(value_status(r, Fraction(maximum, 6)) == "verified" for r in conditionals))
        for r in conditionals:
            context_ids.append(r.record_id)
            if strategy_valid[-1]:
                checks.numerical(f"c.conditional_success_{compartment}", r, Fraction(maximum, 6),
                    context_claim_ids=[x.record_id for pair in combinations for x in pair],
                    context_gate="deterministically verified strategy; arithmetic certificate has numeric scope")
            else:
                checks.observe(f"c.conditional_success_{compartment}", [r], "unverified",
                    reason="STRATEGY_CONTEXT_NOT_VERIFIED")
    for r in records:
        if quantity(r) != "total" and not standalone_math(r, checks.digital.source_text):
            continue
        expression = written_expression(r)
        parts = expression.split("=")
        if len(parts) != 2:
            continue
        shape = weighted_sum_matches(parts[0], [Fraction(1, 6)] * 2, probabilities)
        node = expression_syntax(parts[0])
        combined = False
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) and len(set(probabilities)) == 1:
            factors = (rational_value(syntax_text(node.left)), rational_value(syntax_text(node.right)))
            expected = (Fraction(len(machine.continue_compartments()), 6), probabilities[0])
            combined = factors == expected or factors[::-1] == expected
        shape = shape or combined
        if shape:
            if continue_valid and all(strategy_valid) and all(conditional_valid):
                checks.numerical("c.total_win_probability", r, machine.win_probability(),
                    written_development="combined_conditional" if combined else "two_branch_sum",
                    context_claim_ids=list(dict.fromkeys(context_ids)),
                    engine_derived={"uniform_first_draw_weights": ["1/6", "1/6"]},
                    context_gate="verified continuation, strategies and conditional probabilities")
            else:
                checks.observe("c.total_win_probability", [r], "unverified", reason="GAME_CONTEXT_NOT_VERIFIED")


def verify_tme2_p3_digital(digital, solution_id, machine, *, use_lean=True, run_id=None):
    # Rebuild from the exact source frames, not from mutable canonical annotations.
    items = {k: digital.source_text[a:b] for k, (a, b) in digital.item_ranges.items()}
    rebuilt = collect_tme2_p3_digital(items)
    if rebuilt.source_text != digital.source_text or rebuilt.item_ranges != digital.item_ranges:
        raise ValueError("Digital source/routing changed")
    original = tuple(r.model_copy(update={"verification_results": ()}) for r in digital.records)
    if original != rebuilt.records:
        raise ValueError("P3 source, canonical form or attribution changed after extraction")
    checks = P3Checks(digital, solution_id, machine, use_lean, run_id)
    for item, checker in zip("abc", (_a, _b, _c)):
        checker(checks, assertions_in_item(digital, item))
    return checks.finish()
