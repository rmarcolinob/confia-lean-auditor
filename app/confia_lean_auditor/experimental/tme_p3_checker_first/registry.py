"""Coverage of the opt-in P3 substrate, not the historical TME_CURRENT route."""
from confia_lean_auditor.rubric.pauta.tme2_p3 import TME2_P3_OBLIGATIONS

STRENGTHENED = frozenset({'b.ordered_pairs', 'b.different_favorable', 'b.second_white_probability'})
COMPOSITE = STRENGTHENED | {'b.alternative_complete', 'c.strategy_case_1', 'c.strategy_case_2',
                          'c.conditional_success_1', 'c.conditional_success_2', 'c.total_win_probability'}
FORMAL_CAPABLE = frozenset({'a.first_white_probability', 'b.second_white_probability',
                          'c.conditional_success_1', 'c.conditional_success_2', 'c.total_win_probability'})


def coverage_rows():
    return [dict(obligation_id=oid, rubric_item=oid[0],
                 coverage='COMPOSITE_STRONG' if oid in COMPOSITE else 'DETERMINISTIC_STRONG',
                 primary_checker='StrongP3Checks' if oid in STRENGTHENED else 'tme2_p3._' + oid[0],
                 formal_arithmetic_available=oid in FORMAL_CAPABLE,
                 result_only_route=oid in {'a.first_white_probability', 'b.second_white_probability'},
                 semantic_allowed=False) for oid in TME2_P3_OBLIGATIONS]
