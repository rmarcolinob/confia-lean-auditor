"""Rubric obligations, not a candidate solution's preferred route.

The closed language distinguishes a complete solution with a shown transformation,
a factorization identity, and a single equivalent transformation. Partial method
credit is only supported by an explicit fixed-weight clause in the approved text.
"""
from fractions import Fraction
from .substitution import syntax_key
from .verification import polynomial

VERSION = 'method-sufficiency.r1'
PARTIAL_METHOD_SUFFIX = ' credito parcial de 50% por transformacao equivalente sem conclusao'


def is_restatement(expression, original, variable):
    def without_identities(key):
        if key[0] in {'product', 'sum'}:
            neutral = ('number', '1' if key[0] == 'product' else '0')
            items = [without_identities(x) for x in key[1]]
            items = [x for x in items if x != neutral]
            if not items:
                return neutral
            if len(items) == 1:
                return items[0]
            return (key[0], tuple(items))
        if key[0] in {'power', 'quotient'} and key[2] == ('number', '1'):
            return without_identities(key[1])
        return key

    try:
        sides = expression.split('=')
        original_sides = original.split('=')
        return len(sides) == len(original_sides) == 2 and all(
            without_identities(syntax_key(a, variable)) == without_identities(syntax_key(b, variable))
            for a, b in zip(sides, original_sides)
        )
    except (ValueError, SyntaxError, ZeroDivisionError, RecursionError):
        return False


def is_factorization(expression, variable):
    """Recognize nonconstant linear factors through bounded parsed structure."""
    def expression_of(key):
        if key[0] in {'number', 'variable'}:
            return '(' + key[1] + ')'
        if key[0] == 'negative':
            return '-(' + expression_of(key[1]) + ')'
        if key[0] in {'sum', 'product'}:
            operator = '+' if key[0] == 'sum' else '*'
            return '(' + operator.join(expression_of(k) for k in key[1]) + ')'
        if key[0] in {'power', 'quotient'}:
            operator = '^' if key[0] == 'power' else '/'
            return '(' + expression_of(key[1]) + operator + expression_of(key[2]) + ')'
        raise ValueError('not a polynomial factor')

    def degree(key):
        # Syntactic variable occurrences can cancel (w-w+1 is constant).
        # Use the existing exact polynomial capability, not a syntactic count.
        text = expression_of(key)
        if len(text) > 8000:
            raise ValueError('factor structure budget')
        return max(polynomial(text, variable), default=0)

    def factored(key):
        if key[0] == 'negative':
            return factored(key[1])
        if key[0] == 'quotient' and degree(key[2]) == 0:
            return factored(key[1])
        if key[0] == 'power':
            return degree(key[1]) == 1 and Fraction(key[2][1]) == 2
        return key[0] == 'product' and sum(degree(k) == 1 for k in key[1]) >= 2

    try:
        return any(factored(syntax_key(side, variable)) for side in expression.split('='))
    except (ValueError, SyntaxError, ZeroDivisionError, RecursionError):
        return False


def method_coverage(policy, partial, evidence, answers, roots):
    """Return fraction and status; never infer a method from a final answer."""
    if any(c.verification_status == 'REFUTED' for c in evidence):
        return Fraction(0), 'NOT_SATISFIED'
    good = [c for c in evidence if c.verification_status == 'VERIFIED']
    if not good:
        return Fraction(0), 'INSUFFICIENT'
    if policy in {'transformation', 'factorization'}:
        # The caller binds only transformations, and factorization requires its tag.
        return Fraction(1), 'COMPLETE'
    formula_values = {Fraction(v) for c in good if c.claim_type == 'FORMULA' for v in c.verified_values}
    root_values = {Fraction(v) for c in answers if c.verification_status == 'VERIFIED' for v in c.verified_values}
    wrong_answer = any(c.verification_status == 'REFUTED' for c in answers)
    transformations = [c for c in good if c.claim_type == 'TRANSFORMATION']
    if not wrong_answer and (formula_values == roots or transformations and root_values == roots):
        return Fraction(1), 'COMPLETE'
    if partial and transformations and not answers:
        return Fraction(1, 2), 'PARTIAL'
    return Fraction(0), 'INSUFFICIENT'
