"""All 21 P1 obligations. No point values or inferred formal capabilities."""
from dataclasses import asdict, dataclass
from types import MappingProxyType

PROBLEM_ID = 'TME2_P1_PILOT'
PUBLIC_ID = 'TME2026P1'
FORMAL_OBLIGATIONS = frozenset({'a.result_594', 'd.total_thirty'})


@dataclass(frozen=True)
class ObligationSpec:
    obligation_id: str
    rubric_item: str
    allowed_claim_types: tuple
    allowed_routes: tuple
    checker: str
    sufficiency_policy: str
    award_type: str
    logical_dependencies: tuple = ()
    pedagogical_dependencies: tuple = ()
    credit_dependencies: tuple = ()


# These dependencies describe the existing checker and rubric, not a new official
# solution chain. Independent obligations keep independent eligibility.
_ROWS = (
 ('a.identifies_137', ('expression',), 'literal_inverse', (), ()),
 ('a.constructs_subtraction', ('expression',), 'written_subtraction', (), ()),
 ('a.result_594', ('expression',), 'written_integer_equality', (), ('a.identifies_137', 'a.constructs_subtraction')),
 ('a.arithmetic_error_only', ('expression',), 'single_written_arithmetic_error', (), ('a.identifies_137', 'a.constructs_subtraction')),
 ('b.reversed_number', ('expression',), 'explicit_reverse_representation', (), ()),
 ('b.subtraction', ('expression',), 'written_positional_subtraction', (), ('b.middle_cancellation',)),
 ('b.middle_cancellation', ('expression',), 'written_cancellation', (), ('b.subtraction',)),
 ('b.factorization', ('expression',), 'written_expansion_to_factorization', (), ()),
 ('c.uses_expression', ('expression',), 'explicit_difference_expression', (), ()),
 ('c.difference_domain', ('expression', 'collection'), 'bounds_and_explicit_digit_domain', (), ()),
 ('c.complete_list', ('collection',), 'enumerated_no_omissions', (), ('c.no_extraneous_values',)),
 ('c.no_extraneous_values', ('collection',), 'enumerated_no_extras', (), ('c.complete_list',)),
 ('c.single_list_error', ('collection',), 'exactly_one_list_error', (), ()),
 ('c.several_correct', ('collection',), 'two_distinct_correct_values', (), ('c.pattern_recognized',)),
 ('c.pattern_recognized', ('expression', 'collection'), 'formula_linked_to_list', (), ('c.several_correct',)),
 ('c.some_correct', ('collection',), 'one_correct_value', (), ()),
 ('d.equation', ('expression',), 'written_equation', (), ('d.difference_six',)),
 ('d.difference_six', ('expression',), 'written_digit_difference', (), ('d.equation',)),
 ('d.digit_pairs', ('collection',), 'exact_ordered_digit_pairs', (), ()),
 ('d.middle_choices', ('expression', 'collection'), 'explicit_middle_choices', (), ('d.total_thirty',)),
 ('d.total_thirty', ('expression',), 'written_counting_product', ('d.digit_pairs', 'd.middle_choices'), ('d.middle_choices',)),
)


def _spec(row):
    oid, kinds, policy, logical, credit = row
    formal = oid in FORMAL_OBLIGATIONS
    return ObligationSpec(oid, oid.split('.')[0], kinds if formal else (*kinds, 'qualitative'),
        ('FORMAL',) if formal else ('DETERMINISTIC', 'SEMANTIC'),
        'lean.student_claim_checkers.tme2_p1:' + ('_check_' + oid[0]),
        policy + ('; existing_checker' if formal else '; existing_checker_or_semantic_sufficiency'),
        'formal' if formal else 'deterministic_or_semantic', logical, (), credit)


REGISTRY = MappingProxyType({r[0]: _spec(r) for r in _ROWS})


def registry_rows():
    return [asdict(s) for s in REGISTRY.values()]


def require_p1(problem):
    if problem not in {PROBLEM_ID, PUBLIC_ID}:
        raise ValueError('C1_supports_only_P1')
    return PROBLEM_ID
