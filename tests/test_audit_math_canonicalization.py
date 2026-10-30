import pytest

from confia_lean_auditor.core.audit_math_projection import (
    canonicalize_equality, has_equivalent_equality, project_audit_math,
)
from confia_lean_auditor.claims.extractors.ita2025f2q3 import extract_claims_ita2025f2q3
from confia_lean_auditor.student_claims.extract_f2q3_student_claims import extract_f2q3_student_claims

TARGET = 'cos(beta)-sin(beta)=1/2'


@pytest.mark.parametrize('source', [
    'cos β - sin β = 1/2',
    'cos β = sin β + 1/2',
    'cos β - 1/2 = sin β',
    'sin β + 1/2 = cos β',
    'cos beta = sen beta + 1/2',
    r'\cos\beta = \sen\beta + \frac{1}{2}',
    '2*(cos(beta)-sin(beta))=1',
    'cos(beta)-sin(beta)=2/4',
])
def test_f2q3_equivalent_equalities(source):
    original = source
    assert canonicalize_equality(source) == canonicalize_equality(TARGET)
    extraction = extract_claims_ita2025f2q3(source)
    claim = next(c for c in extraction.claims if c.type == 'beta_difference')
    assert claim.normalized == {'beta_difference': '1/2'}
    student = extract_f2q3_student_claims(source)[0]
    assert student.data['value_expr'] == '1 / 2'
    assert student.context == original
    assert source == original


@pytest.mark.parametrize('source', [
    'cos β = sin β - 1/2',
    'cos β + sin β = 1/2',
    'cos β - sin β = 1/20',
    'cos β - sin β = 1/2 + 1',
    'cos β - sin α = 1/2',
    '(cos(beta)-sin(beta))**2=1/4',
    '(cos(beta)-sin(beta))/(cos(beta)-sin(beta))=1',
    'cos(beta)-sin(beta)=1/0',
    'cos(beta)-sin(beta)=1/2*x',
    'cos(beta)-sin(beta)=1/2 < 2',
])
def test_f2q3_does_not_credit_inequivalent_or_unsupported(source):
    assert not has_equivalent_equality(source, TARGET)
    assert not any(c.type == 'beta_difference' for c in extract_claims_ita2025f2q3(source).claims)


def test_negative_difference_keeps_sign_for_formal_check():
    for source in ['cos β = sin β - 1/2', 'sin β - cos β = 1/2']:
        claim = extract_f2q3_student_claims(source)[0]
        assert claim.data['value_expr'] == '-1 / 2'


@pytest.mark.parametrize(('left', 'right'), [
    ('x= y+3/7', '7*x-7*y=3'),
    ('2*(x+y)-x=4', 'y*2+x-4=0'),
    ('cos(alpha+beta)=x', 'x=cos(beta+alpha)'),
])
def test_generic_exact_affine_canonicalization(left, right):
    assert canonicalize_equality(left) is not None
    assert canonicalize_equality(left) == canonicalize_equality(right)


def test_complete_clause_and_prose():
    assert has_equivalent_equality('Subtraindo as equações, obtemos cos beta = sen beta + 1/2.', TARGET)
    assert not has_equivalent_equality('x + cos beta - sin beta = 1/2', TARGET)
    assert canonicalize_equality('__import__("os").system("echo bad")=0') is None


@pytest.mark.parametrize('equation', [TARGET, 'x-y=3/7'])
@pytest.mark.parametrize('wrapper', [
    'Não é verdade, portanto {equation}.',
    'Suponha provisoriamente:\n{equation}.',
    'Se isso fosse válido, teríamos:\n{equation}.',
    '{equation}. Essa afirmação é falsa.',
    'Tentei:\n{equation}. Essa tentativa foi rejeitada.',
    '"Uma citação. {equation}."',
    r'\text{Não é verdade:}\[{equation}\]',
])
def test_qualifiers_are_not_erased_by_projection_or_clause_splitting(equation, wrapper):
    source = wrapper.replace('{equation}', equation)
    assert not has_equivalent_equality(source, equation)


@pytest.mark.parametrize('source,target', [
    ('Portanto x-y=3/7.', 'x-y=3/7'),
    (r'\[\frac{3*x-y}{7}=-\frac{5}{11}\]', '11*(3*x-y)=-35'),
    (r'\[x-y=-\frac{3}{7}\]', 'x-y=-3/7'),
])
def test_asserted_general_relations_preserve_signs_and_fractions(source, target):
    assert has_equivalent_equality(source, target)
    lhs, rhs = target.split('=')
    assert not has_equivalent_equality(source, f'{lhs}=-({rhs})')


@pytest.mark.parametrize('source', [
    '1/4+x-y=3/4; x-y=-1/2',
    'x-y=-1/2; 1/4+x-y=3/4',
    '1/4+x-y=3/4; -1/2=x-y',
])
def test_explicit_value_is_not_overwritten_by_an_intermediate_rearrangement(source):
    assert not has_equivalent_equality(source, 'x-y=1/2')
    assert has_equivalent_equality(source, 'x-y=-1/2')


@pytest.mark.parametrize('source', ['x-y=1/2; x-y=-1/2', 'x-y=-1/2; x-y=1/2'])
def test_conflicting_explicit_values_do_not_choose_the_expected_answer(source):
    assert not has_equivalent_equality(source, 'x-y=1/2')
    assert not has_equivalent_equality(source, 'x-y=-1/2')


def test_nested_general_fraction_projection_preserves_operand_grouping():
    assert project_audit_math(r'\frac{a+b}{\frac{c-d}{e}}') == '(a+b)/((c-d)/e)'
