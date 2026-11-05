"""Exact finite P2 mathematics and bounded, explicit argument certificates.

A model certificate proves mathematics of the problem, never that a student
presented an argument. The separate relation checker requires written structure.
"""
from __future__ import annotations

import ast
from functools import lru_cache
import hashlib
from itertools import permutations, product
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictStr, ValidationError
from confia_lean_auditor.core.math_canonical.combinatorial import FACTORIAL, factorial_form
from confia_lean_auditor.core.math_canonical.rational import rational_value


class IntegralInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    subject: Literal['S']
    terms: tuple[StrictStr, ...]


def component(name, status, reason, *, false=False, route='DETERMINISTIC', **details):
    return dict(name=name, route=route, status=status, reason=reason,
                mathematical_refutation=false, **details)


def check_integrality(payload):
    """S is a sum of three integers, not an enum accepted on sight.

left/center/right denote the three integer digits of a P2 line (1..9).
Concrete terms permit exact negative controls and future bound numeric inputs.
Unsupported terms are unknown, never false; malformed envelopes are errors.
"""
    try:
        value = IntegralInput.model_validate(payload)
    except ValidationError:
        return component('integrality', 'DETERMINISTIC_ERROR', 'invalid_payload')
    if len(value.terms) != 3:
        return component('integrality', 'DETERMINISTIC_NOT_ATTEMPTED', 'three_terms_required')
    if any(not t or len(t) > 128 for t in value.terms):
        return component('integrality', 'DETERMINISTIC_NOT_ATTEMPTED', 'unsupported_term')
    numbers = []
    symbolic = []
    for term in value.terms:
        if term in {'left', 'center', 'right'}:
            symbolic.append(term)
        else:
            v = rational_value(term)
            if v is None:
                return component('integrality', 'DETERMINISTIC_NOT_ATTEMPTED', 'unsupported_term')
            numbers.append(v)
    # An integral symbolic contribution cannot change a fractional remainder.
    integral = sum(numbers).denominator == 1
    in_domain = all(v.denominator == 1 and 1 <= v <= 9 for v in numbers)
    valid = integral and in_domain
    return component('integrality', 'DETERMINISTIC_VERIFIED' if valid else 'DETERMINISTIC_FAILED',
        'integer_sum_closure' if valid else 'nonintegral_sum' if not integral else 'non_digit_term',
        false=not valid, proposition='S = left + center + right; each term is an integer digit; S is integral',
        input_terms=list(value.terms), symbolic_integer_digits=symbolic,
        concrete_subtotal=str(sum(numbers)), sum_is_integral=integral, concrete_terms_in_digit_domain=in_domain,
        domain_origin='P2 problem definition, not a student-derived claim')


@lru_cache(maxsize=1)
def _finite_certificate_json():
    """Exhaustive domain (8! states) independent of the 4!*2^4 generator."""
    digits = tuple(range(1, 10))
    cases = [(x, (sum(digits) + 3*x)//4) for x in digits if (sum(digits)+3*x) % 4 == 0]
    center, common = max(cases, key=lambda p: p[1])
    outer = tuple(x for x in digits if x != center)
    pairs = tuple((x, common-center-x) for x in outer if x < common-center-x and common-center-x in outer)
    if len(pairs) != 4 or sorted(x for p in pairs for x in p) != list(outer):
        raise ValueError('invalid_pair_partition')
    distributions = tuple(permutations(range(len(pairs))))
    orientations = tuple(product((0, 1), repeat=len(pairs)))
    encoded = {}
    for order in distributions:
        for flips in orientations:
            ordered = [pairs[i][::(-1 if flip else 1)] for i, flip in zip(order, flips)]
            state = tuple(p[0] for p in ordered) + tuple(p[1] for p in ordered)
            if state in encoded:
                raise ValueError('encoding_not_injective')
            encoded[state] = (order, flips)
    independent = {state for state in permutations(outer)
                   if all(state[i] + center + state[i+4] == common for i in range(4))}
    if set(encoded) != independent:
        raise ValueError('encoding_not_surjective')
    # An independently reconstructed inverse, not lookup in the generator.
    for state, expected in encoded.items():
        order, flips = [], []
        for i in range(4):
            observed = (state[i], state[i+4]); unordered = tuple(sorted(observed))
            order.append(pairs.index(unordered)); flips.append(int(observed != unordered))
        if (tuple(order), tuple(flips)) != expected:
            raise ValueError('inverse_mismatch')
    return json.dumps(dict(center=center, common_sum=common, pairs=pairs,
        distributions=len(distributions), orientations=len(orientations), total=len(independent),
        distinct_lines=4, choices_per_pair=2, exhaustive_candidate_states=40320,
        injective=True, surjective=True, inverse_verified=True,
        model_origin='P2 fixed labelled lines and digits; not student evidence',
        states_sha256=hashlib.sha256(json.dumps(sorted(independent)).encode()).hexdigest()), sort_keys=True)


def finite_certificate():
    # Returning fresh data prevents callers from poisoning the cached certificate.
    return json.loads(_finite_certificate_json())


def _tree(text):
    return ast.parse(FACTORIAL.sub(lambda m: 'factorial('+m[1]+')', text.strip()).replace('^', '**'), mode='eval').body


def _factors(node):
    """Written counting stages, retaining operations rather than just the value."""
    if isinstance(node, ast.Constant) and type(node.value) is int and 1 <= node.value <= 24:
        return [node.value] if node.value != 1 else []
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'factorial'
            and len(node.args) == 1 and isinstance(node.args[0], ast.Constant)
            and type(node.args[0].value) is int and 0 <= node.args[0].value <= 4):
        return list(range(2, node.args[0].value+1))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        a, b = _factors(node.left), _factors(node.right)
        return None if a is None or b is None else a+b
    if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow)
            and isinstance(node.right, ast.Constant) and type(node.right.value) is int
            and 1 <= node.right.value <= 4):
        base = _factors(node.left)
        return None if base is None else base*node.right.value
    return None


def _distribution(node):
    return _factors(node) is not None and sorted(_factors(node)) == [2, 3, 4]


def _orientation(node):
    return _factors(node) == [2, 2, 2, 2]


def argument_relation(key, expression):
    """Closed typed notation only. No inference from prose or matching numbers.

For the direct method, explicit 24*16 is an existing rubric method: the model
independently certifies both components. No prior credit for other steps is needed.
"""
    form = factorial_form(expression)
    if form is None:
        return component('relation', 'DETERMINISTIC_NOT_ATTEMPTED', 'unsupported_representation')
    nodes = [_tree(s) for s in form['original_parts']]
    if key == 'pair_permutations':
        supported = any(_distribution(n) for n in nodes)
    elif key == 'pair_orientations':
        supported = any(_orientation(n) for n in nodes)
    elif key == 'counting_product':
        n = nodes[0]
        supported = False
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult):
            def stage(node, which):
                return ((_distribution(node) if which == 24 else _orientation(node)) or
                        isinstance(node, ast.Constant) and type(node.value) is int and node.value == which)
            supported = ((stage(n.left, 24) and stage(n.right, 16)) or
                         (stage(n.right, 24) and stage(n.left, 16)))
    else:
        raise ValueError('unknown_combinatorial_obligation')
    return component('relation', 'DETERMINISTIC_VERIFIED' if supported else 'DETERMINISTIC_FAILED',
        'explicit_counting_stages' if supported else 'argument_not_established',
        # Failure to recognize a sufficient argument is NOT mathematical falsity.
        false=False, expression=expression, typed_subject=key,
        proof_scope='written structure linked to independently enumerated P2 counting objects')


def combine(components, *, semantic_decision=None, required=('arithmetic', 'counting_components', 'relation')):
    """No semantic authority is enabled for these four mathematically decidable IDs.

The optional decision is adversarial/compatibility input, never an override.
A future dedicated semantic route requires a new explicit contract, not this hook.
"""
    rows = tuple(components)
    if any(r['mathematical_refutation'] or r['status'] == 'FORMAL_REFUTED' for r in rows):
        state, reason = 'refuted', 'mathematical_refutation_has_precedence'
    elif any(r['status'] in {'FORMAL_ERROR', 'DETERMINISTIC_ERROR'} for r in rows):
        state, reason = 'technical_error', 'checker_error'
    elif (len({r['name'] for r in rows}) == len(rows) and set(required) <= {r['name'] for r in rows}
          and all(r['status'] in {'FORMAL_VERIFIED', 'DETERMINISTIC_VERIFIED'} for r in rows)):
        state, reason = 'verified', 'all_required_components_verified'
    else:
        state, reason = 'unverified', 'missing_or_insufficient_component'
    return dict(state=state, reason=reason, semantic_authority=False,
                semantic_input_ignored=semantic_decision is not None)
