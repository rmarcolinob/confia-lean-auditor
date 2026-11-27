"""Written additive constructions using the existing bounded canonicalizer."""
import ast
from itertools import combinations
from . import equivalent
from .syntax import expression_syntax, syntax_text


def comparison(left, right):
    return {"equivalent": "verified", "not_equivalent": "refuted"}.get(equivalent(left, right).status, "unverified")


def sum_development(text, expected):
    """Match an explicitly written sum of perimeter contributions, not its total.

    Bounded partition of written additive terms uses the existing affine
    canonicalizer. It admits expansion such as 3x+18-3x without a general CAS.
    """
    def terms(node, sign=1):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            return terms(node.left, sign) + terms(node.right, sign * (-1 if isinstance(node.op, ast.Sub) else 1))
        return [f"({sign})*({syntax_text(node)})"] if node is not None else []
    observed = terms(expression_syntax(text))
    if not len(expected) <= len(observed) <= 8:
        return False
    def match(parts, goals):
        if len(goals) == 1:
            return comparison("+".join(parts), goals[0]) == "verified"
        for count in range(1, len(parts) - len(goals) + 2):
            for indices in combinations(range(len(parts)), count):
                if comparison("+".join(parts[i] for i in indices), goals[0]) == "verified" and match(
                        [p for i, p in enumerate(parts) if i not in indices], goals[1:]):
                    return True
        return False
    return match(observed, expected)

