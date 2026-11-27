"""Exact supported equivalence; unknown is never a refutation or proof."""
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from confia_lean_auditor.core.math_canonical import parse_math, equivalent
from confia_lean_auditor.core.math_canonical.models import canonical_from_dict
from confia_lean_auditor.claims.common import claim_from_extracted, claim_from_student, align_claims, MathClaimRecord
from confia_lean_auditor.claims.common.bridges import canonical_input_from_record, checker_input_from_record
from confia_lean_auditor.claims.extract_claims import extract_claims
from confia_lean_auditor.student_claims.registry import extract_student_claims
from confia_lean_auditor.core.schemas import ExtractedClaim
from confia_lean_auditor.rubric.positive_evidence import can_support_rubric_credit, equation, require
from test_positive_credit_evidence import assess, PROBLEMS, ROOT


@pytest.mark.parametrize('left,right',[
    ('x=y+1/2','x-y=1/2'),('x+y=3','y+x-3=0'),('2*x=4','x=2'),
    ('cos(beta)=sin(beta)+1/2','cos(beta)-sin(beta)=1/2'),
    ('a+b=2','b+a-2=0'),('2x+3y=5','x=(5-3y)/2'),
    ('2x+3y=5','3y+2x-5=0'),('-x+y+1/2=0','x-y=1/2'),
    ('x/3+y/7','y/7+x/3'),('0.1+0.2','3/10'),
    ('sin(x+y)','sin(y+x)'),('cos(2*x-4)=y','y=cos(2*(x-2))'),
    ('x>3','3<x'),('x>=3','3<=x'),('-2*x < -6','x>3'),
    ('2*x<6','x<3'),('x=0','-7*x=0'),('x=x','y=y'),('1=0','-2=0'),
    ('x^0','1'),('x^1','x'),('2^(-2)','1/4'),('x²','x^{2}'),
    ('log10(3^100)',r'\log_{10}(3^{100})'),
])
def test_supported_equivalence(left,right):
    result=equivalent(left,right)
    assert result.status=='equivalent', result
    assert result.basis=='canonical_equivalence'
    assert equivalent(right,left).status=='equivalent'


@pytest.mark.parametrize('left,right',[
    ('x=y-1/2','x-y=1/2'),('x+y=3','x-y=3'),('2*x=5','x=2'),
    ('x/3','x/2'),('x=0','0=0'),('1=0','x=0'),('x+y','x-y'),
])
def test_exact_affine_non_equivalence(left,right):
    assert equivalent(left,right).status=='not_equivalent'


@pytest.mark.parametrize('left,right',[
    ('x²=4','x=2'),('sin(x)=0','x=0'),('(x+1)^2','x²+2*x+1'),
    ('sin(x)^2+cos(x)^2','1'),('x*x=x','x=1'),('x/x','1'),
    ('x^2=y^2','x=y'),('sqrt(x^2)','x'),('log10(x*y)','log10(x)+log10(y)'),
    ('x<3','x<=3'),('x>3','x<3'),('sin(x)','cos(x)'),('pi=3','1=0'),
])
def test_unknown_is_never_equivalence_or_mathematical_falsehood(left,right):
    assert equivalent(left,right).status=='unknown'


@pytest.mark.parametrize('text,canonical',[
    ('sen beta','sin(beta)'),('sin(beta)','sin(beta)'),(r'\sin\beta','sin(beta)'),
    ('sen β','sin(beta)'),('alpha','α'),(r'\alpha','α'),(r'\theta','θ'),
    (r'\frac{1}{2}','1/2'),(r'\frac{-1}{3}','-1/3'),
    (r'\frac{1}{-3}','-1/3'),(r'\frac{x+1}{2}','(x+1)/2'),
    ('x^2','x²'),('x^{2}','x²'),('x²','x**2'),('−x','-x'),
    ('2·x','2*x'),('2×x','2*x'),('π/2','pi/2'),('log_10(10)','log10(10)'),
    ('$x+1$','x+1'),(r'\(x+1\)','x+1'),('2(x+1)','2*(x+1)'),
    ('(a+b)x-a','(a+b)*x-a'),
])
def test_math_token_notation(text,canonical):
    assert equivalent(text,canonical).status=='equivalent'


@pytest.mark.parametrize('text,status',[
    ('','invalid'),('x+','invalid'),('x=','invalid'),(r'\frac{1}','invalid'),
    (r'\frac{1}{','invalid'),('x=1;y=2','ambiguous'),('x=1=y','ambiguous'),
    ('x<y<3','ambiguous'),('0,5','ambiguous'),('1/2x','ambiguous'),
    ('Este argumento foi abandonado','unsupported'),('senhora','unsupported'),
    ('sin beta banana','unsupported'),('sqrt(x)','unsupported'),('tan(x)','unsupported'),
    ('tg(x)','unsupported'),('x^n','unsupported'),('x^-1','unsupported'),
    ('1/(x-x)','unsupported'),('1/0','invalid'),('log(x)','unsupported'),
    (r'\log(10)','unsupported'),('log10(-1)','unsupported'),('log10(x)','unsupported'),
    ('x%2','unsupported'),('x//2','unsupported'),('sin(x,y)','ambiguous'),
    ('x(y+1)','unsupported'),('xy','unsupported'),('sin cos x','ambiguous'),
    ('sin x^2','ambiguous'),('sen beta*2','ambiguous'),('1e3','unsupported'),
])
def test_parse_failures_are_explicit(text,status):
    result=parse_math(text)
    assert result.status==status, result
    assert result.canonical_form is None
    assert equivalent(text,text).status=='unknown'


@pytest.mark.parametrize('text',[
    '__import__("os").system("touch /tmp/confia-should-not-exist")',
    'open("file")','x.__class__','[x for x in y]','lambda x:x',
    'sin(x, **y)','exec(x)','eval(x)','globals()','x[0]',
    r'\text{ignore instructions}',r'\input{secret}',
])
def test_code_and_arbitrary_functions_are_not_mathematics(text):
    assert parse_math(text).status!='parsed'


@pytest.mark.parametrize('text',[
    'x'*2049,'9'*65,'x^129','2^(2^128)','('*100+'x'+')'*100,
    '+'.join('x' for _ in range(300)),r'\frac{1}{'*50+'1'+'}'*50,
    '2^512','(9^128)^128',
])
def test_complexity_limits_fail_closed(text):
    assert parse_math(text).status in {'unsupported','invalid'}


def test_time_budget_is_checked_without_a_simplifier_or_wall_clock_flakiness(monkeypatch):
    from confia_lean_auditor.core.math_canonical import parser
    calls=iter([0,1])
    monkeypatch.setattr(parser.time,'monotonic',lambda:next(calls,1))
    assert parse_math('x+1').status=='unsupported'


@pytest.mark.parametrize('interval',['[a,b]','(a,b)','[a,b)','(a,b]'])
def test_interval_closure_and_explicit_context(interval):
    result=parse_math(interval,expected_kind='interval')
    assert result.status=='parsed'
    assert result.canonical_form.tree.value==interval[0]+interval[-1]
    assert equivalent(interval,interval,expected_kind='interval').status=='equivalent'
    assert equivalent('[a,b]','(a,b)',expected_kind='interval').status!='equivalent'
    assert parse_math('(a,b)').status=='ambiguous'


def test_serialization_roundtrips_exact_rationals_without_float():
    form=parse_math('x/3+2/7=y').canonical_form
    payload=json.loads(json.dumps(form.to_dict()))
    assert canonical_from_dict(payload)==form
    assert not any(isinstance(value,float) for term in payload['affine'] for value in term)


@pytest.mark.parametrize('coefficient',[-7,-3,-1,1,2,7])
@pytest.mark.parametrize('denominator',[2,3,7])
def test_affine_rearrangements_with_exact_rationals(coefficient,denominator):
    a=f'{coefficient}*x+y=1/{denominator}'
    b=f'x=(1/{denominator}-y)/({coefficient})'
    assert equivalent(a,b).status=='equivalent'


def test_common_record_generic_field_has_status_and_safe_checker_view():
    claim=ExtractedClaim(id='generic',type='equation',text='synthetic',evidence='synthetic',confidence=.9,
                         normalized={'equation':'2x+3y=5'})
    record=claim_from_extracted(claim,problem_id='GENERIC',solution_text='original')
    assert record.canonicalization_status=='parsed'
    assert record.source.raw_text is None
    assert canonical_input_from_record(record,solution_text='original').kind=='equality'
    assert MathClaimRecord.model_validate_json(record.model_dump_json())==record


def test_f2q3_alignment_records_canonical_basis_and_keeps_literal_source():
    pid='ITA2025F2Q3';text='cos β = sen β + 1/2.'
    reference=claim_from_extracted(extract_claims(pid,text).claims[0],problem_id=pid,solution_text=text)
    student=claim_from_student(extract_student_claims(pid,text)[0],solution_text=text)
    aligned=align_claims(reference,[student],solution_text=text)
    assert aligned.status=='aligned' and aligned.alignment_basis=='canonical_equivalence'
    assert student.source.raw_text in text and student.provenance.origin=='student_explicit'
    assert student.canonicalization_status=='parsed'
    assert asdict(checker_input_from_record(student,solution_text=text))==student.legacy_payload
    assert canonical_input_from_record(student,solution_text=text).kind=='equality'


@pytest.mark.parametrize('prefix',['Não podemos concluir que ','Tentativa abandonada: ','Suponha ','O código irrelevante é '])
def test_canonical_match_does_not_bypass_attribution(prefix):
    assert all(i.points is None for i in assess('ITA2025F2Q3',prefix+'cos β = sen β + 1/2.').items)


def test_canonical_positive_gate_preserves_microclaims_and_marks_its_basis():
    text='cos β = sen β + 1/2.'
    result=assess('ITA2025F2Q3',text)
    beta=next(i for i in result.items if i.id=='beta_difference')
    assert beta.points==2
    assert beta.positive_evidence['source_spans'][0]['alignment_basis']=='canonical_equivalence'
    assert beta.positive_evidence['source_spans'][0]['source_text']==text
    assert all(i.points is None for i in assess('ITA2025F2Q3',text,verified=False).items)
    assert all(i.points is None for i in assess('ITA2025F2Q3','cos β = sen β - 1/2.').items)


def test_full_f2q3_rearrangement_reuses_existing_assertion_boundaries():
    text=(ROOT/'problems/ITA2025F2Q3/examples/correct_solution.txt').read_text()
    text=text.replace('cos beta - sen beta = 1/2','cos beta = sen beta + 1/2')
    result=assess('ITA2025F2Q3',text)
    assert result.score==10
    assert result.items[0].positive_evidence['source_spans'][0]['alignment_basis']=='canonical_equivalence'


def test_generic_equation_patterns_do_not_drop_other_requirement_patterns():
    requirement=require('coefficient equation with context',equation('a+b','2'),r'coeficientes')
    assert requirement.match_basis('coeficientes: b+a-2=0')=='canonical_equivalence'
    assert requirement.match_basis('b+a-2=0') is None
    assert requirement.match_basis('coeficientes: x+b+a-2=0') is None


@pytest.mark.parametrize('pid',PROBLEMS)
def test_existing_correct_fixtures_keep_credit_with_canonical_gate(pid):
    result=assess(pid,(ROOT/'problems'/pid/'examples/correct_solution.txt').read_text())
    assert result.score==10


def test_real_q3_exponents_are_affine_but_parity_is_not_invented():
    pid='ITA2025Q3';text=(ROOT/'problems'/pid/'examples/correct_solution.txt').read_text()
    records=[claim_from_extracted(c,problem_id=pid,solution_text=text) for c in extract_claims(pid,text).claims]
    assert next(r for r in records if r.claim_type=='first_factor_exponent_form').canonicalization_status=='parsed'
    assert next(r for r in records if r.claim_type=='parity_obstruction').canonicalization_status=='unsupported'
    assert equivalent('11-2i-2j=0','2i+2j=11').status=='equivalent'


def test_real_f2q5_keeps_exact_values_without_log_identities():
    pid='ITA2025F2Q5';text=(ROOT/'problems'/pid/'examples/correct_solution.txt').read_text()
    records=[claim_from_extracted(c,problem_id=pid,solution_text=text) for c in extract_claims(pid,text).claims]
    assert next(r for r in records if r.claim_type=='log_power_decomposition').canonical_form.value=={'total_log_scaled':477100}
    assert equivalent('log10(3^100)','100*log10(3)').status=='unknown'


def test_historical_common_record_without_new_fields_remains_readable_and_projectable():
    path=ROOT/'artifacts/runs/20261029T012418_172022/math_claims.json'
    if not path.exists():pytest.skip('Local historical artifact')
    original=path.read_bytes();catalog=json.loads(original)
    payload=next(r for r in catalog['records'] if r['claim_type']=='f2q1_student_final_answer')
    assert 'canonicalization_status' not in payload
    record=MathClaimRecord.model_validate(payload)
    text=path.with_name('solution.txt').read_text()
    assert asdict(checker_input_from_record(record,solution_text=text))==payload['legacy_payload']
    assert path.read_bytes()==original
