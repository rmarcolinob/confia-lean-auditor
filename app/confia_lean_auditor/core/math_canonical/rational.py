"""Exact closed rationals and their written arithmetic, using existing grammar."""
import ast
from fractions import Fraction

from .parser import parse_math
from .syntax import expression_syntax, syntax_text


def rational_value(text):
    parsed = parse_math(text)
    if (parsed.status == "parsed" and parsed.canonical_form.kind == "expression"
            and parsed.canonical_form.tree.kind == "rational"):
        return Fraction(parsed.canonical_form.tree.value)
    return None


def closed_equality(text):
    parts = tuple(p.strip() for p in text.split("="))
    if len(parts) != 2 or any(rational_value(p) is None for p in parts):
        return None
    return parts


def lean_rational_expression(text):
    """Render only bounded exact arithmetic; every literal is explicitly ℚ.

    Repeating decimals, variables, functions and zero denominators fail closed.
    No raw source is injected into Lean code.
    """
    if rational_value(text) is None:
        return None

    def render(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return f"({node.value} : ℚ)"
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return f"(-{render(node.operand)})" if isinstance(node.op, ast.USub) else render(node.operand)
        operators = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}
        if isinstance(node, ast.BinOp) and type(node.op) in operators:
            return f"({render(node.left)} {operators[type(node.op)]} {render(node.right)})"
        raise ValueError("Unsupported rational syntax")

    try:
        return render(expression_syntax(text))
    except (ValueError, TypeError, RecursionError):
        return None


def weighted_sum_matches(text, weights, conditionals):
    """Check written branch contributions, not merely their numerical sum.

    Supports a sum of products, or one common factor times a sum. Explicit
    branch identity/context is validated separately by the problem checker.
    """
    def terms(node):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return terms(node.left) + terms(node.right)
        return [node]

    root = expression_syntax(text)
    if root is None:
        return False
    expected = sorted(zip(weights, conditionals))
    observed = []
    for node in terms(root):
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Mult):
            break
        pair = (rational_value(syntax_text(node.left)), rational_value(syntax_text(node.right)))
        if None in pair:
            break
        # Problem contracts here use one common branch weight. Multiplication
        # is commutative but a bare sum of already evaluated results is not a tree.
        if pair[0] != weights[0] and pair[1] == weights[0]:
            pair = pair[::-1]
        observed.append(pair)
    else:
        if sorted(observed) == expected:
            return True
    if isinstance(root, ast.BinOp) and isinstance(root.op, ast.Mult) and len(set(weights)) == 1:
        for factor, total in ((root.left, root.right), (root.right, root.left)):
            values = [rational_value(syntax_text(t)) for t in terms(total)]
            if (rational_value(syntax_text(factor)) == weights[0] and None not in values
                    and sorted(values) == sorted(conditionals)):
                return True
    return False
