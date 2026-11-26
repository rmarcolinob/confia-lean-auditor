"""Three-valued comparison: unsupported algebra never becomes a false claim."""
from .models import EquivalenceResult
from .parser import parse_math, _variable


def compare_canonical(left,right):
    if left.domain!=right.domain or left.schema_version!=right.schema_version:
        return EquivalenceResult('unknown','Different canonical domains or versions')
    if left.kind!=right.kind:
        return EquivalenceResult('unknown','Different mathematical structures')
    if left.tree==right.tree:
        return EquivalenceResult('equivalent','Identical validated syntax','canonical_equivalence')
    if left.affine is not None and right.affine is not None:
        if left.affine==right.affine and left.relation==right.relation:
            return EquivalenceResult('equivalent','Exact affine forms agree','canonical_equivalence')
        # Distinct affine expressions/hyperplanes over independent real variables
        # are distinguishable. Functions and pi are not independent variables.
        atoms={k for form in (left,right) for k,_ in form.affine}
        independent=all(not k or _variable(k) and k!='pi' for k in atoms)
        if independent and left.kind in {'expression','equality'}:
            return EquivalenceResult('not_equivalent','Distinct exact affine forms over real variables','exact_affine_difference')
    return EquivalenceResult('unknown','No supported proof of equivalence or non-equivalence')


def equivalent(left_text,right_text, *, expected_kind=None):
    left,right=parse_math(left_text, expected_kind=expected_kind),parse_math(right_text, expected_kind=expected_kind)
    if left.status!='parsed' or right.status!='parsed':
        return EquivalenceResult('unknown',f'Parse outcomes: {left.status}, {right.status}')
    return compare_canonical(left.canonical_form,right.canonical_form)
