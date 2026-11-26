"""P4 attributed mathematical facts. Geometry, algebra and proof scope stay separate.

No points, semantic fallback, new CAS, or guessed intermediate student claims.
"""
import ast
import re
import uuid
from dataclasses import asdict
from itertools import permutations

from confia_lean_auditor.claims.common.fact_results import FactResultsBuilder
from confia_lean_auditor.core.math_canonical import equivalent, parse_math
from confia_lean_auditor.core.math_canonical.development import sum_development
from confia_lean_auditor.core.math_canonical.rational import rational_value
from confia_lean_auditor.core.math_canonical.syntax import expression_syntax, syntax_text
from confia_lean_auditor.student_claims.tme2_p4_digital import PROBLEM_ID, collect_tme2_p4_digital
from confia_lean_auditor.tme.p4_geometry import P4Geometry
from .real_algebra import lean_real_expression, check_real_record

VERSION = "tme2-p4-check.v1"


def expression(record):
    return record.canonical_form.value["expression"]


def comparison(left, right):
    return {"equivalent": "verified", "not_equivalent": "refuted"}.get(equivalent(left, right).status, "unverified")


def in_x_scope(text):
    """Unbound symbols are missing context, not false geometric formulas."""
    forms = [parse_math(p) for p in text.split("=")]
    return all(p.status == "parsed" and set(p.canonical_form.variables) <= {"x"} for p in forms)


def together(states):
    if "technical_error" in states:
        return "technical_error"
    if "refuted" in states:
        return "refuted"
    return "verified" if states and all(s == "verified" for s in states) else "unverified"


def same_set(observed, expected):
    # Sets ignore order and duplicates; equivalence uses exact canonical math.
    unique = []
    for value in observed:
        if not any(comparison(value, old) == "verified" for old in unique):
            unique.append(value)
    if len(unique) != len(expected):
        return "refuted" if all(rational_value(v) is not None for v in [*unique, *expected]) else "unverified"
    outcomes = [together([comparison(a, b) for a, b in zip(unique, order)]) for order in permutations(expected)]
    return "verified" if "verified" in outcomes else "unverified" if "unverified" in outcomes else "refuted"


def square_equation(text, hypotenuse, cathetus1, cathetus2):
    """Recognize the two squared legs and squared hypotenuse individually."""
    parts = text.split("=")
    if len(parts) != 2:
        return False
    def square(node, base):
        if node is None:
            return False
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow) and isinstance(node.right, ast.Constant) and node.right.value == 2:
            return comparison(syntax_text(node.left), base) == "verified"
        value = rational_value(syntax_text(node))
        expected = rational_value(base)
        return value is not None and expected is not None and value == expected * expected
    for left, right in (parts, parts[::-1]):
        a, b = expression_syntax(left), expression_syntax(right)
        if square(a, hypotenuse) and isinstance(b, ast.BinOp) and isinstance(b.op, ast.Add):
            if any(square(p, cathetus1) and square(q, cathetus2) for p, q in ((b.left, b.right), (b.right, b.left))):
                return True
    return False


def lean_equality(text):
    parts = text.split("=")
    if len(parts) != 2:
        return None
    parts = [lean_real_expression(p) for p in parts]
    return " = ".join(parts) if all(parts) else None


class P4Checks(FactResultsBuilder):
    def __init__(self, digital, solution_id, use_lean, run_id):
        super().__init__(digital, solution_id, problem_id=PROBLEM_ID, checker_version=VERSION)
        if run_id is not None and not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", run_id):
            raise ValueError("Unsafe run ID")
        self.run_id = (run_id or "tme2-p4") + "-" + uuid.uuid4().hex
        self.use_lean = use_lean
        self.geometry = P4Geometry()

    def select(self, item, key):
        return [r for r in self.digital.records if r.rubric_links == (item,) and r.source.attributable
                and r.source.grounding_status == "grounded" and r.canonical_form
                and r.canonical_form.family == "named_quantity" and r.canonical_form.subject == key]

    def supported(self, *facts):
        return all((states := [p["verification"].status for p in self.pending if p["fact_id"] == fact])
                   and all(s == "verified" for s in states) for fact in facts)

    def context(self, facts):
        return {"student_assumption_fact_ids": list(facts), "source_claim_ids": list(dict.fromkeys(
            i for p in self.pending if p["fact_id"] in facts for i in p["source_claim_ids"])),
            "domain": self.geometry.domain, "geometry_source": self.geometry.source}

    def observe(self, fact, record, status, *, mechanism="canonical_equivalence", formal=None, **metadata):
        refs = [record]
        check = None
        if self.use_lean and formal:
            statement, proof, refutation, context = formal
            outcome = check_real_record(record, self.digital, collect=collect_tme2_p4_digital,
                statement=statement, proof=proof, refutation=refutation, context=context,
                run_id=self.run_id, index=len(self.pending))
            if outcome:
                projected, checked = outcome
                self.records[projected.record_id] = projected
                refs.append(projected)
                check = asdict(checked)
                status, mechanism = checked.status, "student_lean"
                metadata.update(formal_statement=statement, formal_context=context)
        self.add(fact, refs, status, mechanism=mechanism, check=check,
            metadata={"student_asserted": record.record_id, "geometry_source": self.geometry.source,
                      "domain": self.geometry.domain, **metadata})

    def value(self, item, key, expected, *, fact=None, geometry=False, formal=False):
        for r in self.select(item, key):
            parts = expression(r).split("=")
            status = together([comparison(p, expected) for p in parts]) if in_x_scope(expression(r)) else "unverified"
            certificate = None
            # Only closed/affine expressions in x are universal identities here.
            rendered = [lean_real_expression(p) for p in parts]
            target = lean_real_expression(expected)
            if formal and all(rendered) and target and in_x_scope(expression(r)):
                statement = "∀ x : ℝ, " + " ∧ ".join(f"({p} = {target})" for p in rendered)
                certificate = (statement, "intro x\n  constructor <;> ring" if len(parts) == 2 else "intro x\n  repeat' constructor\n  all_goals ring",
                    "push_neg\n  first | (refine ⟨1, ?_⟩; norm_num) | (refine ⟨2, ?_⟩; norm_num)",
                    {"engine_derived_expected_expression": expected, "geometry_source": self.geometry.source,
                     "scope": "algebraic equivalence under structured geometry; no Euclidean proof"})
            self.observe(fact or f"{item}.{key}", r, status, formal=certificate,
                mechanism="deterministic" if geometry else "canonical_equivalence",
                verification_kind="deterministic_geometry" if geometry else "algebra",
                engine_derived_expected_expression=expected)

    def enum(self, item, key, expected):
        for r in self.select(item, key):
            self.observe(f"{item}.{key}", r, r.canonical_form.value["value"] == expected,
                         mechanism="deterministic", verification_kind="deterministic_geometry")

    def development(self, item, key, expected, contributions):
        for r in self.select(item, key):
            parts = expression(r).split("=")
            if not in_x_scope(expression(r)):
                self.observe(f"{item}.{key}", r, "unverified", scope="Unbound variables")
                continue
            status = together([comparison(p, expected) for p in parts])
            developed = any(sum_development(parts[0], group) for group in contributions)
            # An isolated number/tautology never supplies a perimeter construction.
            if not developed and status == "verified":
                continue
            eq = lean_equality(expression(r))
            if not developed and len(parts) == 1:
                continue
            formal = None
            if eq and len(parts) == 2:
                formal = (f"∀ x : ℝ, {eq}", "intro x\n  ring",
                    "push_neg\n  first | (refine ⟨1, ?_⟩; norm_num) | (refine ⟨2, ?_⟩; norm_num)",
                    {"scope": "exact written perimeter identity", "geometry_source": self.geometry.source})
            # A valid equality at the wrong total is NOT a proof of this obligation.
            if status != "verified" and eq and comparison(parts[-1], expected) != "verified":
                formal = None
            self.observe(f"{item}.{key}", r, status, formal=formal, written_development=developed)

    def a(self):
        for triangle in ("pbq", "rqc"):
            self.enum("a", "triangle_" + triangle, "equilateral")
        for s in ("pb", "bq", "pq", "qc", "qr", "rc"):
            self.value("a", s, self.geometry.lengths[s.upper()], geometry=True)
        for polygon in ("PBQ", "RQC"):
            self.value("a", "perimeter_" + polygon.lower(), self.geometry.perimeter(polygon), formal=True)
        self.development("a", "shaded_sum", "18", [("3*x", "3*(6-x)")])

    def b(self):
        for s in ("ap", "qr", "pq", "ar", "ra"):
            self.value("b", s, self.geometry.lengths[s.upper()], fact="b.ar" if s == "ra" else None,
                       geometry=True, formal=s == "ap")
        self.enum("b", "apqr", "parallelogram")
        # Both the four-side metric sum and the two doubled adjacent sides.
        self.development("b", "perimeter_apqr", "12", [("6-x", "x", "6-x", "x"), ("2*(6-x)", "2*x")])
        # Factored parallelogram perimeter 2*((6-x)+x) preserves its construction.
        for r in self.select("b", "perimeter_apqr"):
            parts = expression(r).split("=")
            node = expression_syntax(parts[0])
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
                for factor, inner in ((node.left, node.right), (node.right, node.left)):
                    if rational_value(syntax_text(factor)) == 2 and sum_development(syntax_text(inner), ("6-x", "x")):
                        status = together([comparison(p, "12") for p in parts])
                        eq = lean_equality(expression(r))
                        formal = (f"∀ x : ℝ, {eq}", "intro x\n  ring", "push_neg\n  refine ⟨1, ?_⟩\n  norm_num", {"scope": "written parallelogram perimeter identity"}) if eq and status == "verified" else None
                        self.observe("b.perimeter_apqr", r, status, formal=formal, written_development=True)

    def c(self):
        for polygon in ("PBQ", "RQC", "APQR"):
            self.value("c", "perimeter_" + polygon.lower(), self.geometry.perimeter(polygon))
        for r in self.select("c", "exclude_12"):
            valid = square_equation(expression(r), "12", "3*x", "3*(6-x)")
            if not valid:
                self.observe("c.exclude_12", r, "unverified", scope="Unrecognized exclusion equation")
                continue
            eq = lean_equality(expression(r))
            formal = (f"∀ x : ℝ, ¬ ({eq})", "intro x heq\n  nlinarith [sq_nonneg (x - 3)]",
                      "push_neg\n  refine ⟨3, ?_⟩\n  norm_num", {"scope": "no real root of the exact written equation; no domain restriction"}) if eq else None
            # Deterministic algebra: minimum squared-leg sum is 162 > 144.
            self.observe("c.exclude_12", r, "verified", formal=formal,
                         engine_derived_certificate="18*(x-3)^2+162 >= 162 > 144")
        for r in self.select("c", "h_plus_c"):
            self.observe("c.h_plus_c", r, comparison(expression(r), "h+c=18"))
        for r in self.select("c", "pythagoras"):
            self.observe("c.pythagoras", r, "verified" if square_equation(expression(r), "h", "c", "12") else "unverified")
        context_facts = ("c.h_plus_c", "c.pythagoras")
        for name, expected in (("h", "13"), ("c", "5")):
            for r in self.select("c", name):
                text = expression(r)
                status = comparison(text, expected) if rational_value(text) is not None else "unverified"
                value = lean_real_expression(text) if rational_value(text) is not None else None
                formal = None
                if self.supported(*context_facts) and value:
                    statement = f"∀ h c : ℝ, h+c=18 → h^2=c^2+144 → {name}={value}"
                    # A wrong candidate must leave an unsolved goal, allowing
                    # the lifecycle to try its independently compiled negation.
                    proof = "intro h c hs hp\n  have hd : h-c=8 := by nlinarith [sq_nonneg (h+c-18)]\n  try linarith"
                    formal = (statement, proof,
                        "push_neg\n  refine ⟨13, 5, ?_, ?_, ?_⟩ <;> norm_num", self.context(context_facts))
                self.observe("c." + name, r, status, formal=formal,
                    scope="Named hypotenuse/cathetus value; no missing student derivation inferred")
        for r in self.select("c", "shaded_lengths"):
            sets = r.canonical_form.value["sets"]
            states = [together([same_set(sets[0]["expressions"], a), same_set(sets[1]["expressions"], b)])
                for a, b in ((["3*x", "3*(6-x)"], ["5", "13"]), (["5", "13"], ["3*x", "3*(6-x)"]))]
            self.observe("c.shaded_lengths", r, "verified" if "verified" in states else "unverified" if "unverified" in states else "refuted")
        for label, hypo, other, root in (("case_3x", "3*x", "3*(6-x)", "13/3"), ("case_other", "3*(6-x)", "3*x", "5/3")):
            for r in self.select("c", label):
                self.observe("c." + label, r, "verified" if square_equation(expression(r), hypo, other, "12") else "unverified")
            for r in self.select("c", label + "_root"):
                value = lean_real_expression(expression(r)) if rational_value(expression(r)) is not None else None
                formal = None
                if self.supported("c." + label) and value:
                    eq = f"({lean_real_expression(hypo)})^2=({lean_real_expression(other)})^2+144"
                    statement = f"∀ x : ℝ, {eq} → x={value}"
                    proof = "intro x hx\n  try nlinarith"
                    refutation = f"push_neg\n  refine ⟨({lean_real_expression(root)}), ?_, ?_⟩ <;> norm_num"
                    formal = (statement, proof, refutation, self.context(("c." + label,)))
                status = comparison(expression(r), root) if rational_value(expression(r)) is not None else "unverified"
                self.observe("c." + label + "_root", r, status, formal=formal)
        for r in self.select("c", "x_candidates"):
            values = r.canonical_form.value["sets"][0]["expressions"]
            status = same_set(values, ["5/3", "13/3"]) if all(rational_value(v) is not None for v in values) else "unverified"
            formal = None
            if self.supported("c.shaded_lengths") and len(values) == 2 and all(rational_value(v) is not None for v in values):
                targets = [lean_real_expression(v) for v in values]
                if all(targets):
                    statement = f"∀ x : ℝ, (3*x=5 ∨ 3*x=13) → (x={targets[0]} ∨ x={targets[1]})"
                    proof = "intro x hx\n  rcases hx with hx | hx\n  all_goals first | (left; linarith) | (right; linarith) | skip"
                    refutation = "push_neg\n  first | (refine ⟨(5/3:ℝ), ?_, ?_⟩ <;> norm_num) | (refine ⟨(13/3:ℝ), ?_, ?_⟩ <;> norm_num)"
                    formal = (statement, proof, refutation, {**self.context(("c.shaded_lengths",)),
                        "engine_derived_premise": "3*x=5 or 3*x=13 from the student's explicit unordered length equality"})
            self.observe("c.x_candidates", r, status, formal=formal)


def verify_tme2_p4_digital(digital, solution_id, *, use_lean=True, run_id=None):
    items = {k: digital.source_text[a:b] for k, (a, b) in digital.item_ranges.items()}
    if collect_tme2_p4_digital(items) != digital:
        raise ValueError("Digital source/claim projection changed")
    checks = P4Checks(digital, solution_id, use_lean, run_id)
    checks.a()
    checks.b()
    checks.c()
    return checks.finish()
