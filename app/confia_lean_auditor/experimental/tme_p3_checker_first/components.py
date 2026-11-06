"""Independent finite machine certificates and bounded written relations."""
import ast
import hashlib
import json
from fractions import Fraction
from itertools import product

from confia_lean_auditor.tme.p3_machine import P3Machine

from confia_lean_auditor.core.math_canonical.rational import rational_value
from confia_lean_auditor.core.math_canonical.syntax import expression_syntax, syntax_text


def component(name, status, reason, *, false=False, **data):
    return dict(name=name, status=status, reason=reason,
                mathematical_refutation=false, **data)


def finite_certificate(machine):
    """Derive every count from fresh two-pop simulations, not learner claims."""
    if not isinstance(machine, P3Machine):
        raise ValueError('trusted_machine_required')
    n = len(machine.stacks)
    events = []
    for i, j in product(range(1, n + 1), repeat=2):
        stacks = [list(stack) for stack in machine.stacks]
        first = stacks[i - 1].pop(0)
        after_first = [list(stack) for stack in stacks]
        second = stacks[j - 1].pop(0)
        events.append(dict(pair=[i, j], first_color=first, second_color=second,
                           stacks_after_first=after_first, stacks_after_second=stacks,
                           probability=str(Fraction(1, n) * Fraction(1, n))))
    all_pairs = [e['pair'] for e in events]
    different = [e['pair'] for e in events if e['pair'][0] != e['pair'][1]]
    repeated = [e['pair'] for e in events if e['pair'][0] == e['pair'][1]]
    favorable = [e['pair'] for e in events if e['second_color'] == 'white']
    different_white = [p for p in favorable if p[0] != p[1]]
    same_white = [p for p in favorable if p[0] == p[1]]
    initially_white = [i for i, s in enumerate(machine.stacks, 1) if s[0] == 'white']
    grouped = {str(j): [p for p in different_white if p[1] == j] for j in initially_white}
    if (sum(Fraction(e['probability']) for e in events) != 1
            or len(different_white) + len(same_white) != len(favorable)
            or any(len(grouped[str(j)]) != n - 1 for j in initially_white)):
        raise ValueError('inconsistent_finite_certificate')
    return dict(machine_source=machine.source_reference,
                machine_sha256=hashlib.sha256(json.dumps(machine.stacks).encode()).hexdigest(),
                selection_rule='uniform_compartment_at_each_draw_as_given_in_problem',
                choice_count=n, event_probability=str(Fraction(1, n * n)),
                total_mass='1', events=events, ordered_pairs=all_pairs,
                different_pairs=different, repeated_pairs=repeated,
                different_white=different_white, same_white=same_white,
                favorable_pairs=favorable, initially_white=initially_white,
                different_by_second_compartment=grouped,
                branch_probabilities=[str(Fraction(sum(e['second_color'] == 'white'
                    for e in events if e['pair'][0] == i), n)) for i in range(1, n + 1)],
                counts=dict(sample=len(all_pairs), different=len(different_white),
                            same=len(same_white), favorable=len(favorable)),
                second_white_probability=str(Fraction(len(favorable), len(all_pairs))),
                premise_origin='versioned_problem_machine_and_selection_rule_not_student_conclusion')


def check_event_set(kind, pairs, machine):
    """Low-level typed set checker, no scoring or automatic source attribution.

    The caller must bind a written enumeration before it could be used for credit.
    Current textual adapter uses the existing scalar notation, not this API.
    """
    try:
        certificate = finite_certificate(machine)
    except (ValueError, TypeError, KeyError, IndexError) as error:
        return component('event_set', 'DETERMINISTIC_ERROR', type(error).__name__)
    allowed = {'sample': 'ordered_pairs', 'different': 'different_white',
               'same': 'same_white', 'favorable': 'favorable_pairs'}
    if kind not in allowed or not isinstance(pairs, (list, tuple)):
        return component('event_set', 'DETERMINISTIC_ERROR', 'invalid_set_payload')
    n = certificate['choice_count']
    if any(not isinstance(p, (list, tuple)) or len(p) != 2 or
           any(type(i) is not int or not 1 <= i <= n for i in p) for p in pairs):
        return component('event_set', 'DETERMINISTIC_ERROR', 'invalid_event_index')
    actual = [tuple(p) for p in pairs]
    expected = {tuple(p) for p in certificate[allowed[kind]]}
    valid = len(actual) == len(set(actual)) and set(actual) == expected
    return component('event_set', 'DETERMINISTIC_VERIFIED' if valid else 'DETERMINISTIC_FAILED',
                     'exact_event_set' if valid else 'wrong_event_subset', false=not valid,
                     expected_pairs=sorted(expected), asserted_pairs=actual)


def _value(node):
    return rational_value(syntax_text(node))


def _product(node, factors):
    return (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult)
            and sorted((_value(node.left), _value(node.right)), key=str) == sorted(factors, key=str))


def count_relation(kind, expression, certificate):
    nodes = [expression_syntax(p) for p in expression.split('=')]
    if any(n is None for n in nodes):
        return component('written_relation', 'DETERMINISTIC_INCOMPLETE', 'unsupported_representation')
    n = certificate['choice_count']
    if kind == 'sample':
        valid = any(_product(x, [Fraction(n), Fraction(n)]) or
                    isinstance(x, ast.BinOp) and isinstance(x.op, ast.Pow)
                    and _value(x.left) == n and _value(x.right) == 2 for x in nodes)
        reason = 'two_uniform_choices_written'
    elif kind == 'different':
        factors = [Fraction(len(certificate['initially_white'])), Fraction(n - 1)]
        valid = any(_product(x, factors) for x in nodes)
        reason = 'white_second_choice_and_distinct_first_choices_written'
    else:
        return component('written_relation', 'DETERMINISTIC_ERROR', 'unknown_count_kind')
    return component('written_relation', 'DETERMINISTIC_VERIFIED' if valid else 'DETERMINISTIC_INCOMPLETE',
                     reason if valid else 'counting_relation_not_established',
                     expression=expression, typed_count_kind=kind,
                     uniformity_premise='problem_rule_verified_by_finite_measure')


def _simple_value(node):
    if isinstance(node, ast.Constant):
        return type(node.value) in (int, float)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _simple_value(node.operand)
    return (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
            and _simple_value(node.left) and _simple_value(node.right))


def probability_route(expression, *, tree=False):
    if tree:
        return 'conditional_tree'
    nodes = [expression_syntax(p) for p in expression.split('=')]
    return 'result_value' if all(n is not None and _simple_value(n) for n in nodes) else 'counting_development'


def probability_relation(expression, certificate):
    """Recognized partition with wrong summands is false, unknown form incomplete."""
    d, s, size = (certificate['counts'][k] for k in ('different', 'same', 'sample'))
    recognized = []
    for part in expression.split('='):
        node = expression_syntax(part)
        if node is None:
            continue
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            numerator = node.left
            if isinstance(numerator, ast.BinOp) and isinstance(numerator.op, ast.Add):
                recognized.append(_value(node.right) == size and
                    sorted([_value(numerator.left), _value(numerator.right)], key=str) == sorted([Fraction(d), Fraction(s)], key=str))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            terms = (node.left, node.right)
            if all(isinstance(t, ast.BinOp) and isinstance(t.op, ast.Div) for t in terms):
                recognized.append(all(_value(t.right) == size for t in terms) and
                    sorted([_value(t.left) for t in terms], key=str) == sorted([Fraction(d), Fraction(s)], key=str))
    if not recognized:
        return component('written_relation', 'DETERMINISTIC_INCOMPLETE', 'probability_partition_not_established')
    valid = all(recognized)
    return component('written_relation', 'DETERMINISTIC_VERIFIED' if valid else 'DETERMINISTIC_FAILED',
                     'disjoint_favorable_partition_written' if valid else 'false_written_partition',
                     false=not valid, expected_partition=dict(different=d, same=s, sample=size))


def combine(rows):
    if any(r['mathematical_refutation'] for r in rows):
        return dict(state='refuted', status='COMPOSITE_FAILED', reason='mathematical_refutation')
    if any(r['status'] in {'DETERMINISTIC_ERROR', 'FORMAL_ERROR'} for r in rows):
        return dict(state='technical_error', status='COMPOSITE_ERROR', reason='checker_error')
    if any(r['status'] == 'CONFLICTING_EVIDENCE' for r in rows):
        return dict(state='unverified', status='COMPOSITE_INCOMPLETE', reason='conflicting_source_evidence')
    if rows and all(r['status'] in {'DETERMINISTIC_VERIFIED', 'FORMAL_VERIFIED'} for r in rows):
        return dict(state='verified', status='COMPOSITE_VERIFIED', reason='all_required_components_verified')
    return dict(state='unverified', status='COMPOSITE_INCOMPLETE', reason='missing_or_unsupported_evidence')
