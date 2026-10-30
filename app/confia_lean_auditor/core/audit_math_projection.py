"""LaTeX projection and conservative algebra for audit extractors.

The stored transcription and audit source remain byte-for-byte unchanged.
Unknown commands remain visible instead of being guessed or evaluated.
"""

import ast
import re
from fractions import Fraction


_SIMPLE_COMMANDS = {
    "alpha": "alpha", "beta": "beta", "gamma": "gamma",
    "sin": "sin", "cos": "cos", "sen": "sen",
    "cdot": "*", "times": "*", "quad": " ", "qquad": " ",
    "left": "", "right": "", "displaystyle": "",
}


def _braced(text: str, start: int):
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "{":
        return None
    depth = 1
    for index in range(start + 1, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:index], index + 1
    return None


def _operand(value: str) -> str:
    value = value.strip()
    return value if re.fullmatch(r"[+-]?[A-Za-z0-9_.]+(?:\([A-Za-z0-9_.]+\))?", value) else f"({value})"


def project_audit_math(text: str) -> str:
    """Translate common Mathpix syntax without changing values or signs."""
    text = re.sub(r"\\(?:begin|end)\s*\{(?:array|aligned|align|gathered|matrix)\}(?:\s*\{[^{}]*\})?", "", text)
    text = text.replace(r"\(", " ").replace(r"\)", " ").replace(r"\[", "\n").replace(r"\]", "\n")
    text = text.replace(r"\\", "\n")
    output = []
    index = 0
    while index < len(text):
        if text[index] != "\\":
            output.append(text[index])
            index += 1
            continue
        match = re.match(r"\\([A-Za-z]+)", text[index:])
        if not match:
            output.append(text[index])
            index += 1
            continue
        command = match.group(1)
        end = index + len(match.group(0))
        if command in {"operatorname", "mathrm", "text", "frac", "sqrt"}:
            first = _braced(text, end)
            if first:
                value, end = first
                value = project_audit_math(value)
                if command == "frac":
                    second = _braced(text, end)
                    if second:
                        denominator, end = second
                        output.append(f"{_operand(value)}/{_operand(project_audit_math(denominator))}")
                        index = end
                        continue
                elif command == "sqrt":
                    output.append(f"sqrt({value.strip()})")
                    index = end
                    continue
                else:
                    output.append(value)
                    index = end
                    continue
        if command in _SIMPLE_COMMANDS:
            output.append(_SIMPLE_COMMANDS[command])
        else:
            output.append(match.group(0))
        index += len(match.group(0))
    return "".join(output)


# Deliberately restricted algebra: affine expressions over symbolic atoms, with
# exact rational constants. No eval, floating point, or cancellation of variable
# denominators (which could change the domain of an equality).
def _math_expression(text: str) -> str:
    text = project_audit_math(text).lower()
    for source, target in {"α": "alpha", "β": "beta", "γ": "gamma", "−": "-", "–": "-", "·": "*", "×": "*"}.items():
        text = text.replace(source, target)
    text = re.sub(r"\b(?:sen|seno)\b", "sin", text)
    text = re.sub(r"\b(sin|sen|cos)\s*(alpha|beta|gamma)\b", r"\1(\2)", text)
    return re.sub(r"\bsen(?=\()", "sin", text.strip()).replace("{", "(").replace("}", ")")


def _add(left, right, scale=Fraction(1)):
    result = dict(left)
    for atom, coefficient in right.items():
        result[atom] = result.get(atom, Fraction(0)) + scale * coefficient
    return {atom: coefficient for atom, coefficient in result.items() if coefficient}


def _scale(expression, factor):
    return {atom: value * factor for atom, value in expression.items() if value * factor}


def _affine(node, budget=None):
    result = _affine_value(node, budget)
    if budget is not None:
        budget.tick()
        for coefficient in result.values():
            budget.rational(coefficient)
    return result


def _affine_value(node, budget=None):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return {"": Fraction(node.value)} if node.value else {}
    if isinstance(node, ast.Name) and re.fullmatch(r"[a-z]+", node.id):
        return {node.id: Fraction(1)}
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"sin", "cos"} and len(node.args) == 1 and not node.keywords:
        argument = tuple(sorted(_affine(node.args[0], budget).items()))
        return {f"{node.func.id}{argument!r}": Fraction(1)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _scale(_affine(node.operand, budget), -1 if isinstance(node.op, ast.USub) else 1)
    if isinstance(node, ast.BinOp):
        left, right = _affine(node.left, budget), _affine(node.right, budget)
        if isinstance(node.op, (ast.Add, ast.Sub)):
            return _add(left, right, -1 if isinstance(node.op, ast.Sub) else 1)
        if isinstance(node.op, ast.Mult):
            if not set(left) - {""}:
                return _scale(right, left.get("", 0))
            if not set(right) - {""}:
                return _scale(left, right.get("", 0))
        if isinstance(node.op, ast.Div) and set(right) == {""}:
            return _scale(left, 1 / right[""])
    raise ValueError("Unsupported algebraic expression")


def canonicalize_equality(text: str):
    """Return a deterministic LHS-RHS zero form, or None if unsupported.

    Nonzero rational scaling is removed, including reversal of the sides.
    Trigonometric functions are symbolic atoms; no trig identities are assumed.
    """
    # Compatibility projection; the generic parser owns bounded AST validation.
    from confia_lean_auditor.core.math_canonical import parse_math
    if not isinstance(text, str) or len(text) > 2048:
        return None
    parsed = parse_math(_math_expression(text))
    form = parsed.canonical_form
    if parsed.status != "parsed" or form.kind != "equality" or form.affine is None:
        return None
    return tuple((atom, Fraction(coefficient)) for atom, coefficient in form.affine)


def strip_audit_equation_prefix(clause):
    """Existing assertion introducers; this is not an attribution decision."""
    return re.sub(r"^.*\b(?:obtemos|temos|logo|assim|portanto)\s*,?\s+", "", clause, flags=re.I)


def iter_audit_equalities(text: str):
    """Read complete equation clauses, preserving original source as evidence.

    Prose before an equation is accepted only as a prefix to the clause. Never
    search for a matching substring inside an expression or truncate its RHS.
    """
    projected = project_audit_math(text)
    for clause in re.split(r"[\n;:,]|(?<!\d)\.|\.(?!\d)", projected):
        clause = clause.strip().strip("$").strip()
        if "=" not in clause:
            continue
        # Existing audit prose commonly introduces equations with 'obtemos'.
        clause = strip_audit_equation_prefix(clause)
        if canonicalize_equality(clause) is not None:
            yield clause


def has_equivalent_equality(text: str, target: str) -> bool:
    canonical = canonicalize_equality(target)
    return canonical is not None and any(canonicalize_equality(clause) == canonical for clause in iter_audit_equalities(text))
