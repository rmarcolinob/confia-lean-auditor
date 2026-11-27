"""Source attribution for rubric credit, independent of reference theorem validity.

This is a bounded statement recognizer, not a new symbolic engine. Existing
reference detectors propose a criterion; its mathematical content must also be
present in attributable source contexts. No source means no first-pass credit.
"""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import re
from types import SimpleNamespace

from confia_lean_auditor.student_claims.grounding import normalized, source_matches

VERSION = "positive-source-v1"


class MathematicalPattern(str):
    """A full mathematical relation/fragment, with surrounding operator checks."""

    equations = ()


def canonical(text):
    if "\\" in text:
        from confia_lean_auditor.core.audit_math_projection import project_audit_math
        text = project_audit_math(text)
    text = normalized(text).replace("π", "pi").replace("≠", "!=").replace("≥", ">=").replace("≤", "<=")
    text = text.replace("_", "").replace("…", "...")
    text = re.sub(r"\^\{([^{}]+)\}", r"^(\1)", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"(?<![a-z])sen(?=\s*(?:\(|alpha|beta|x))", "sin", text)
    text = re.sub(r"(?<![a-z])(sin|cos)\s*\(\s*(alpha|beta|x)\s*\)", r"\1\2", text)
    text = re.sub(r"\b(sin|cos)\s+(alpha|beta|x)\b", r"\1\2", text)
    return text


def math_pattern(expression):
    """Whitespace is immaterial; signs, operators and argument roles are not."""
    return r"\s*".join(re.escape(c) for c in re.sub(r"\s+", "", canonical(expression)))


def fragment(expression):
    return MathematicalPattern(r"(?<![\w+*/^\-])" + math_pattern(expression) + math_end())


def math_end():
    return (r"(?!\w)(?!\s*(?:[+*/^=<>\-]|[.,]\d))"
            r"(?![ \t]*(?:[abcfghijknpqsxz]\b|(?:sqrt|sin|cos)\s*\())")


def equation(lhs, rhs):
    # A chain may contain only the bounded mathematical token vocabulary below.
    # In particular an unrelated prose clause cannot connect two equalities.
    functions = r"sqrt|sin|cos|alpha|beta|log|binom|choose|det"
    token = (r"(?:sqrt|sin|cos|alpha|beta|log10|log(?!10)|binom|choose|det|(?!(?:"
             + functions + r"))[abcfghijknpqsxz]|[0-9\s()\[\]{},.+*/^\-])")
    pattern = MathematicalPattern(r"(?<![\w+*/^\-])" + math_pattern(lhs) + r"\s*=\s*(?:" + token + r"+=\s*)*"
            + math_pattern(rhs) + math_end())
    pattern.equations = (lhs + '=' + rhs,)
    return pattern


@dataclass(frozen=True)
class Requirement:
    label: str
    patterns: tuple[str, ...]

    def matches(self, text):
        return self.match_basis(text) is not None

    def match_basis(self, text):
        legacy_text = canonical(text)
        def matches_pattern(pattern):
            for match in re.finditer(pattern, legacy_text):
                prefix = legacy_text[:match.start()].rstrip()
                if isinstance(pattern, MathematicalPattern) and prefix and prefix[-1] in "+-*/^":
                    continue
                return True
            return False
        used_canonical = False
        for pattern in self.patterns:
            if matches_pattern(pattern):
                continue
            targets = getattr(pattern, 'equations', ())
            if not targets:
                return None
            from confia_lean_auditor.core.math_canonical import equivalent
            from confia_lean_auditor.core.math_canonical.source import mathematical_clauses
            if not any(equivalent(clause, target).status == 'equivalent'
                       for clause, _ in mathematical_clauses(text) for target in targets):
                return None
            used_canonical = True
        return 'canonical_equivalence' if used_canonical else 'existing_pattern'


@dataclass(frozen=True)
class Rule:
    requirements: tuple[Requirement, ...]
    allowed_negations: tuple[str, ...] = ()
    # Only atomic, criterion-complete checks may upgrade the evidence category.
    formal_types: tuple[str, ...] = ()
    binding: tuple[tuple[str, int], ...] = ()
    conclusion_only: bool = False


def require(label, *patterns):
    return Requirement(label, patterns)


UNATTRIBUTABLE = re.compile(
    r"\b(?:nao|nunca|jamais|fals\w*|errad\w*|falh\w*|talvez|suponh\w*|"
    r"tentei|tentativa|provisori\w*|abandon\w*|descart\w*|rejeit\w*|incorret\w*|enunciado|"
    r"prove|provar|mostre|demonstrar|pergunta|citacao|citado|hipotese|se|"
    r"exemplo|rotulo|senha|codigo|irrelevante)\b"
)


def quoted_ranges(source):
    opening = {'"': '"', '“': '”', '«': '»', "'": "'", '‘': '’'}
    start = None
    closing = None
    for index, char in enumerate(source):
        if start is None and char in opening:
            # An apostrophe after a mathematical identifier is a prime, not an
            # opening quotation mark. Curly quotation marks are unambiguous.
            if char == "'" and index and (source[index-1].isalnum() or source[index-1] in ")]"):
                continue
            start, closing = index, opening[char]
        elif start is not None and char == closing:
            yield start, index + 1
            start = closing = None
    if start is not None:
        yield start, len(source)


def has_scoped_qualifier(text):
    """Only known mathematical negations allow splitting a qualified paragraph."""
    text = canonical(text)
    mathematical_negations = (
        r"g\s+nao\s+e\s+injet(?:ora|iva)",
        r"(?:nunca|nao)\s+(?:pode\s+)?ser\s+zero", r"nao\s+e\s+zero",
        r"nao\s+ha\s+termo\s+independente\s+nao\s+nulo",
        r"nao\s+esta\s+definido\s+quando\s*" + math_pattern("cos(x)=0"),
        r"nao\s+nulo", r"nao\s+alteram\s+o\s+determinante",
        r"descart\w*\s+(?:a\s+raiz\s+negativa\s+)?-\s*13\b",
        r"pela\s+hipotese\s+funcional",
    )
    for pattern in mathematical_negations:
        text = re.sub(pattern, " ", text)
    return bool(UNATTRIBUTABLE.search(text))


def source_contexts(source):
    """Paragraphs retain multiline algebra; sentences retain original offsets.

    Explicit quotation/provisional wrappers scope over their entire paragraph,
    so splitting cannot discard the qualifier and launder a following equation.
    """
    for match in re.finditer(r"\S(?:.*?\S)?(?=\n\s*\n|\s*\Z)", source, re.S):
        if len(match[0]) <= 4000:
            yield match.start(), match.end(), match[0]
            if has_scoped_qualifier(match[0]):
                # An explicitly rejected attempt may be followed by a new
                # conclusion. Keep the entire suffix, including any later
                # rejection, so sentence splitting cannot erase its scope.
                for conclusion in re.finditer(r"(?<=[.!?])\s*(?:Logo|Portanto|Assim|Concluo)\b", match[0], re.I):
                    prefix = canonical(match[0][:conclusion.start()])
                    if (re.search(r"\b(?:tentei|tentativa)\b", prefix)
                            and re.search(r"\b(?:falh\w*|errad\w*|abandon\w*|descart\w*)\b", prefix)):
                        start = match.start() + conclusion.start()
                        while source[start].isspace():
                            start += 1
                        yield start,match.end(),source[start:match.end()]
                continue
            start = match.start()
            for end in [match.start()+m.end() for m in re.finditer(r"(?<!\.)[.!?](?!\.)(?=\s|$)", match[0])] + [match.end()]:
                while start < end and source[start].isspace():
                    start += 1
                if start < end and (start,end) != (match.start(),match.end()):
                    yield start,end,source[start:end]
                start = end


def attributable(text, rule, statement):
    t = canonical(text)
    if any(mark in t for mark in ('"', '“', '”', '«', '»', '?')) or re.search(r"(?m)^\s*>", t):
        return False
    for phrase in rule.allowed_negations:
        t = re.sub(phrase, " ", t)
    if UNATTRIBUTABLE.search(t):
        return False
    # Bare prompt material is not an achievement. Rubric-permitted conclusions
    # remain accepted when asserted in the student's own context, without commands.
    compact = re.sub(r"\s+", "", canonical(text)).strip(".;:")
    prompt = re.sub(r"\s+", "", canonical(statement))
    if compact and compact in prompt and not rule.conclusion_only:
        return False
    return True


def _value(obj, name, default=None):
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)


@lru_cache(maxsize=1)
def rules():
    from confia_lean_auditor.rubric.positive_rules import RULES
    return RULES


@lru_cache(maxsize=32)
def related_check_types(problem_id, criterion_id):
    """Reuse the existing check-to-criterion contract, including composites."""
    from importlib import import_module
    suffix = problem_id.removeprefix("ITA2025")
    if suffix not in {"F2Q1", "F2Q3", "F2Q5", "F2Q6", "F2Q8"}:
        return ()
    module = import_module("confia_lean_auditor.rubric.adjusters.ita2025" + suffix.lower())
    mapping = getattr(module, suffix + "_STUDENT_CHECK_TO_RUBRIC_ITEMS")
    return tuple(kind for kind, criteria in mapping.items() if criterion_id in criteria)


def reference_dependency_evidence(*, problem_id, required_ids, microclaims_by_id,
                                  claims_by_type, solution_text, student_checks, statement_text):
    """Attribute the claim premises of the EXISTING microclaim dependency graph.

    A canonical proof whose premises are merely heuristic must not launder those
    premises into downstream credit. No dependency is added to the asset graph.
    """
    records = []
    visited = set()
    def visit(identifier):
        if identifier in visited:
            return
        visited.add(identifier)
        mc = microclaims_by_id.get(identifier)
        if mc is None:
            records.append({"microclaim_id": identifier, "supported": False,
                            "reason": "Required reference result missing"})
            return
        for kind in mc.claim_types:
            evidence = can_support_rubric_credit(problem_id=problem_id,
                item=SimpleNamespace(id=kind, required_microclaim_ids=[]),
                claim=claims_by_type.get(kind), solution_text=solution_text,
                student_checks=student_checks, statement_text=statement_text)
            records.append({"microclaim_id": identifier, **evidence})
        for dependency in mc.depends_on_microclaim_ids:
            visit(dependency)
    for identifier in required_ids:
        visit(identifier)
    return records


def can_support_rubric_credit(*, problem_id, item, claim, solution_text,
                             verified_microclaim_ids=(), student_checks=(), statement_text="",
                             reference_dependencies=(), claim_context=None):
    result = {"version": VERSION, "supported": False, "verification_type": "reference_heuristic",
              "claim_id": claim.id if claim else None, "criterion_id": item.id,
              "required_microclaim_ids": list(item.required_microclaim_ids), "source_spans": []}
    def pending(reason):
        return {**result, "reason": reason}
    if (claim_context is not None and solution_text
            and claim_context.problem_id == problem_id
            and claim_context.solution_text == solution_text
            and claim_context.statement_text == statement_text):
        bridge = claim_context.evidence(item)
        if bridge and bridge.get('conflict'):
            return {**pending(bridge['reason']), 'student_bridge': bridge,
                    'needs_review': True, 'conflict': True}
        if bridge and bridge['supported']:
            # A complete student check cannot replace other asset obligations
            # or launder unattributed premises of a reference proof.
            if not set(item.required_microclaim_ids) <= set(verified_microclaim_ids):
                return {**pending('Required microclaims are not verified; student bridge cannot replace them'),
                        'student_bridge': {**bridge, 'supported': False}}
            if any(not dependency['supported'] for dependency in reference_dependencies):
                return {**pending('A claim premise of the required reference proof lacks attributable evidence'),
                        'student_bridge': {**bridge, 'supported': False},
                        'reference_dependencies': list(reference_dependencies)}
            return {**result, 'supported': True, 'student_bridge': bridge,
                    'verification_type': ('formal_verification' if bridge['verification_basis'] == 'formal_lean_verified'
                                          else 'deterministic_check'),
                    'source_sha256': hashlib.sha256(solution_text.encode()).hexdigest(),
                    'source_spans': bridge['source_spans'], 'student_check_ids': bridge['student_check_ids'],
                    'reference_dependencies': list(reference_dependencies),
                    'reference_verification_scope': 'generated_reference',
                    'reason': 'Student bridge verified the obligation; required microclaims and attribution retained'}
    if claim is None:
        return pending("No reference candidate for this rubric criterion")
    if not solution_text:
        return pending("Original solution required for positive attribution")
    result["source_sha256"] = hashlib.sha256(solution_text.encode()).hexdigest()
    rule = rules().get((problem_id, claim.type))
    if rule is None:
        return pending("No source correspondence validator for this claim type")
    if not set(item.required_microclaim_ids) <= set(verified_microclaim_ids):
        return pending("Required microclaims are not verified; source alone cannot replace them")
    result["reference_dependencies"] = list(reference_dependencies)
    if any(not dependency["supported"] for dependency in reference_dependencies):
        return pending("A claim premise of the required reference proof lacks attributable evidence")
    quotes = list(quoted_ranges(solution_text))
    contexts = [(a,b,t) for a,b,t in source_contexts(solution_text)
                if not any(a < end and b > start for start,end in quotes)
                and attributable(t, rule, statement_text)]
    spans = []
    for requirement in rule.requirements:
        candidates = [(a,b,t,requirement.match_basis(t)) for a,b,t in contexts]
        candidates = [c for c in candidates if c[3] is not None]
        if not candidates:
            return pending("Missing attributable mathematical content: " + requirement.label)
        a,b,text,match_basis = candidates[-1]
        span = {"requirement": requirement.label, "source_start": a, "source_end": b, "source_text": text}
        if match_basis == 'canonical_equivalence':
            span['alignment_basis'] = match_basis
        spans.append(span)
    basis = "grounded_text"
    if rule.binding:
        from confia_lean_auditor.student_claims.grounding import select_bindings
        # Resolve conflicts against the whole answer, not just the matching span.
        binding_text = re.sub(r"\b(?:o\s+)?valor\s+de\s+([a-z])\s+e\s+([+-]?\d+)",
                              r"\1=\2", normalized(solution_text))
        selected,status,_ = select_bindings(binding_text, tuple(k for k,_ in rule.binding))
        if status != "grounded" or selected[3] != dict(rule.binding):
            return pending("Missing or conflicting local bindings for the proposed conclusion")
        basis = "deterministic_check"
    # Composite criteria must also respect ambiguous/refuted components. Only
    # the separate criterion-complete allowlist below can promote formal credit.
    relevant_types = set(related_check_types(problem_id, item.id)) | set(rule.formal_types)
    related = [check for check in student_checks
               if _value(check, "problem_id") == problem_id and _value(check, "claim_type") in relevant_types]
    if any((_value(c,"grounding") or {}).get("status") == "ambiguous" for c in related):
        return pending("Student claim interpretation is ambiguous")
    from confia_lean_auditor.student_claims.schemas import is_mathematically_refuted
    if any(is_mathematically_refuted(c) and source_matches(c, solution_text) for c in related):
        return pending("Grounded mathematical refutation takes precedence over reference detection")
    verified = [c for c in related if _value(c,"status") == "verified" and _value(c,"compiled")
                and source_matches(c, solution_text)]
    if rule.formal_types and set(rule.formal_types) <= {_value(c,"claim_type") for c in verified}:
        basis = "formal_verification"
    return {**result, "supported": True, "verification_type": basis, "source_spans": spans,
            "student_check_ids": [_value(c,"id") for c in verified],
            "reference_verification_scope": "generated_reference",
            "reason": "Criterion-specific mathematical statements are attributable to original source; required microclaims retained"}
