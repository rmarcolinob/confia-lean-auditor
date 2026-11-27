"""Source-preserving substitution recognition, without evaluating away provenance.

Canonical math's evaluated tree is appropriate for truth checking, but a numeric
zero alone cannot establish which expression was evaluated. This bounded syntax
normal form keeps powers/products and only normalizes signs, commutative order,
and rational literals. Exact truth is still delegated to the existing checker.
"""
import ast
from fractions import Fraction
import re

VERSION = 'substitution-operation.r1'
NORMALIZATION_VERSION = 'source-structure.r1'


def syntax_key(text, variable=None, value=None):
    """A structural key, never executable code or equality-by-numeric-coincidence."""
    if len(text) > 4000:
        raise ValueError('source structure budget')
    source = text.replace('^', '**')
    tree = ast.parse(source, mode='eval')
    if sum(1 for _ in ast.walk(tree)) > 240:
        raise ValueError('source structure budget')

    def number(v):
        v = Fraction(v)
        if max(v.numerator.bit_length(), v.denominator.bit_length()) > 512:
            raise ValueError('rational budget')
        return ('number', str(v))

    def negate(k):
        if k[0] == 'number':
            return number(-Fraction(k[1]))
        if k[0] == 'negative':
            return k[1]
        if k[0] == 'sum':
            return total([negate(x) for x in k[1]])
        return ('negative', k)

    def total(items):
        flat = []
        for k in items:
            flat.extend(k[1] if k[0] == 'sum' else [k])
        return ('sum', tuple(sorted(flat, key=repr)))

    def product(items):
        flat = []
        negative = False
        pending = list(items)
        while pending:
            k = pending.pop()
            if k[0] == 'product':
                pending.extend(k[1])
            elif k[0] == 'negative':
                negative = not negative
                pending.append(k[1])
            elif k[0] == 'number' and Fraction(k[1]) < 0:
                negative = not negative
                flat.append(number(-Fraction(k[1])))
            else:
                flat.append(k)
        result = ('product', tuple(sorted(flat, key=repr)))
        return negate(result) if negative else result

    def convert(node, depth=0):
        if depth > 45:
            raise ValueError('source structure depth')
        sub = lambda n: convert(n, depth+1)
        if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
            return number(ast.get_source_segment(source, node))
        if isinstance(node, ast.Name) and variable and node.id == variable:
            return number(value) if value is not None else ('variable', variable)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            key = sub(node.operand)
            return negate(key) if isinstance(node.op, ast.USub) else key
        if isinstance(node, ast.BinOp):
            left, right = sub(node.left), sub(node.right)
            if isinstance(node.op, ast.Add):
                return total([left, right])
            if isinstance(node.op, ast.Sub):
                return total([left, negate(right)])
            if isinstance(node.op, ast.Mult):
                return product([left, right])
            if isinstance(node.op, ast.Div):
                if left[0] == right[0] == 'number':
                    return number(Fraction(left[1]) / Fraction(right[1]))
                return ('quotient', left, right)
            if isinstance(node.op, ast.Pow) and right[0] == 'number':
                exponent = Fraction(right[1])
                if exponent.denominator == 1 and 0 <= exponent <= 12:
                    return ('power', left, right)
        raise ValueError('unsupported source structure')

    return convert(tree.body)


def substitution_operation(text, equation, normalize, evaluate):
    """Recognize only grounded operations; no inferred complete-solution claim."""
    left, right, var, _, roots = equation
    # Prefix is an explicit value assignment, not a license to accept any true sum.
    prefix = re.fullmatch(
        r'\s*(?:Substituindo|Para|Com)\s+' + re.escape(var)
        + r'\s*=\s*([+−-]?\d+(?:\.\d+)?(?:/\d+)?)\s*[:,]\s*(.+)',
        text, re.IGNORECASE,
    )
    body = prefix[2] if prefix else text
    parts = normalize(body).split('=')
    if len(parts) != 2:
        return None
    if not prefix and re.search(r'[A-Za-z]', parts[0]):
        return None
    try:
        candidates = [evaluate(prefix[1])] if prefix else sorted(roots)
        for value in candidates:
            observed = syntax_key(parts[0], var if prefix else None, value)
            expected = syntax_key(normalize(left), var, value)
            if observed != expected:
                continue
            # Symbolic source after an explicit assignment remains the same operation.
            grounded = re.sub(r'\b' + re.escape(var) + r'\b', f'({value})', parts[0])
            actual, claimed = evaluate(grounded), evaluate(parts[1])
            matches = actual == claimed
            root_check = matches and value in roots and claimed == evaluate(right)
            return dict(
                schema_version=VERSION,
                normalization_version=NORMALIZATION_VERSION,
                original_expression=left,
                variable=var,
                substituted_value=str(value),
                source_expression=parts[0],
                source_result=parts[1],
                evaluated_expression=grounded,
                computed_result=str(actual),
                claimed_result=str(claimed),
                value_assignment_explicit=bool(prefix),
                match_basis='STRUCTURAL_OPERATION',
                evaluation_verified=matches,
                verifies_root=root_check,
                complete_solution_claimed=False,
            )
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, RecursionError):
        return None
    return None
