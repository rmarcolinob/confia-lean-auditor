"""Safe cross-pipeline projections; labels alone never establish alignment."""
from dataclasses import dataclass
import re

from confia_lean_auditor.core.math_canonical import parse_math, compare_canonical
from confia_lean_auditor.core.math_canonical.models import canonical_from_dict, EquivalenceResult
from .canonical import mathematical_value
from .expected import exact_integer, DIGIT_OBLIGATIONS, quantity_subject

REUSABLE_TYPES = {
    'bindings': {'math_bindings','math_relation','math_value'},
    'leading_digit': {'math_value'},
    'mathematical_relation': {'math_relation'},
    'mathematical_expression': {'math_expression'},
}


@dataclass(frozen=True)
class Comparable:
    kind: str
    value: object


def compare(left,right):
    if left.kind!=right.kind:return EquivalenceResult('unknown','Different semantic domains')
    if left.kind=='canonical':return compare_canonical(left.value,right.value)
    return EquivalenceResult('equivalent' if left.value==right.value else 'not_equivalent',
                             'Exact typed structured values','structured_equivalence')


def _canonical(form):
    data=mathematical_value(form)
    return canonical_from_dict(data) if data else None


def _anchor(node):
    if node.kind=='relation' and node.value=='=':
        a,b=node.args
        if a.kind=='variable' and b.kind=='rational':return ('binding',a.value)
        if b.kind=='variable' and a.kind=='rational':return ('binding',b.value)
    if node.kind=='rational':return ('rational','*')
    if node.kind=='power':return ('power',_anchor(node.args[0]),node.args[1])
    return (node.kind,node.value,tuple(_anchor(a) for a in node.args))


def _same_declared_subject(student_data, expected_subject):
    text=student_data.get('subject_text')
    if not text:return True
    text=re.sub(r'^(?:de|do)\s+(?:resultado\s+de\s+)?','',text.strip(),flags=re.I)
    parsed=parse_math(text)
    if parsed.status!='parsed' or expected_subject is None:return False
    return compare_canonical(parsed.canonical_form,canonical_from_dict(expected_subject)).status=='equivalent'


def project_pair(reference,student,*,statement_text='',strict=False):
    """Return comparable complete payloads or None for unrelated semantics.

    A canonical equivalent full proposition can match across syntax. A merely
    different proposition is competing only when its structural subject agrees.
    No textual similarity or partial expression is used as mathematical proof.
    """
    ref=reference.canonical_form;form=student.canonical_form
    if ref is None or form is None:return None
    data=(student.legacy_payload or {}).get('data',{})
    if ref.family=='integer_bindings' and reference.claim_type in {'final_answer','coefficient_assignment','coefficient_solution'}:
        expected=ref.value
        values=(form.value if form.family=='integer_bindings' else data.get('bindings') if student.claim_type=='math_bindings' else None)
        if values is not None:
            if set(values)!=set(expected):return None
            if len(expected)>1:return Comparable('bindings',expected),Comparable('bindings',values)
            symbol=next(iter(expected));actual=parse_math(f'{symbol}={values[symbol]}').canonical_form
        elif len(expected)==1 and student.claim_type=='math_relation':
            actual=_canonical(form)
            if actual is None or actual.kind!='equality' or set(actual.variables)!=set(expected):return None
            # A polynomial intermediate equation is not a competing final
            # assignment merely because it mentions the same variable.
            if actual.affine is None:return None
        elif len(expected)==1 and student.claim_type=='math_value' and data.get('concept') in {'answer','value'}:
            if student.semantic_role!='conclusion' or data.get('negated'):return None
            value=exact_integer(data.get('expression'));symbol=next(iter(expected))
            if value is None:return None
            subject=data.get('subject_text')
            if subject and re.sub(r'^(?:de|do)\s+','',subject.strip())!=symbol:return None
            actual=parse_math(f'{symbol}={value}').canonical_form
        else:return None
        expected_form=parse_math(f'{next(iter(expected))}={next(iter(expected.values()))}').canonical_form
        if actual is None or expected_form is None:return None
        return Comparable('canonical',expected_form),Comparable('canonical',actual)
    if reference.claim_type in DIGIT_OBLIGATIONS and ref.subject=='leading_digit':
        if strict and form.family=='integer_binding' and form.subject=='leading_digit':
            return Comparable('leading_digit',ref.value),Comparable('leading_digit',form.value)
        if student.claim_type!='math_value' or data.get('concept')!='leading_digit' or data.get('negated'):return None
        subject=quantity_subject(statement_text)
        if not _same_declared_subject(data,subject):return None
        digit=exact_integer(data.get('expression'))
        if digit is None or not 0<=digit<=9:return None
        return Comparable('leading_digit',ref.value),Comparable('leading_digit',{'d':digit})
    expected,actual=_canonical(ref),_canonical(form)
    if expected is None or actual is None:return None
    category='mathematical_relation' if expected.kind in {'equality','inequality'} else 'mathematical_expression'
    if (not strict and student.claim_type not in REUSABLE_TYPES[category]) or actual.kind!=expected.kind:return None
    # A bare scalar in a historical reference does not express a whole verbal
    # obligation (root selection, equal function values, parity, etc.).
    if expected.kind=='expression' and not expected.variables:return None
    comparison=compare_canonical(expected,actual)
    if comparison.status!='equivalent' and _anchor(expected.tree)!=_anchor(actual.tree):return None
    return Comparable('canonical',expected),Comparable('canonical',actual)
