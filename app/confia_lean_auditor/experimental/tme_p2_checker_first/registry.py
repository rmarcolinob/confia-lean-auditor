"""Coverage declaration for the opt-in P2 path; the legacy registry is untouched."""
from confia_lean_auditor.rubric.pauta.tme2_p2 import TME2_P2_OBLIGATIONS

FORMAL = frozenset({'b.sum_formula', 'b.centers', 'b.admissible_center', 'b.center_sums', 'b.sum_at_five', 'c.total'})
COMPOSITE = frozenset({'c.pair_permutations', 'c.pair_orientations', 'c.counting_product'})


def coverage_rows():
    rows = []
    for oid in TME2_P2_OBLIGATIONS:
        category = 'COMPOSITE_STRONG' if oid in COMPOSITE else 'FORMAL_STRONG' if oid in FORMAL else 'DETERMINISTIC_STRONG'
        checker = ('P2CompositeCountingChecker' if oid in COMPOSITE else 'check_integrality' if oid == 'b.integral_sum'
                   else 'P2Checks.'+oid[0])
        rows.append(dict(obligation_id=oid, rubric_item=oid[0], coverage=category,
                         primary_checker=checker, semantic_allowed=False))
    return rows
