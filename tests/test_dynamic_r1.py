"""New DEV_V2 contracts and adversarial structural/fidelity controls, offline."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from decimal import Decimal
import pytest
from confia_lean_auditor.dynamic.grader import DynamicSolutionGrader, extract, problem_equation
from confia_lean_auditor.dynamic.grading_models import DynamicGradingContext
from confia_lean_auditor.dynamic.models import RubricContent
from confia_lean_auditor.submissions.schemas import TranscriptionSegment
from confia_lean_auditor.dynamic.substitution import syntax_key

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT/'benchmarks/dynamic/dev_v2/cases.json').read_text())

class Carrier(SimpleNamespace):
    def model_dump(self, **kw):
        def dump(x):
            if hasattr(x, 'model_dump'):
                return x.model_dump(**kw)
            if isinstance(x, list):
                return [dump(v) for v in x]
            return x
        return {k:dump(v) for k,v in vars(self).items()}


def grade_case(tmp_path, case, checker=None, context=None):
    context = context or DynamicGradingContext(problem_id='dyn_r1',package_id='dpkg_r1',package_version=1,package_sha256='a'*64,statement_version=1,statement_sha256='b'*64,preparation_id='dprep_r1',preparation_version=1,preparation_sha256='c'*64,rubric_id='drub_r1',rubric_version=1,rubric_sha256='d'*64)
    statement=Carrier(statement=case['statement'],version_number=1)
    rubric=RubricContent(max_score=case['max_points'],criteria=[case['criterion']])
    prep=Carrier(status='READY_FOR_REVIEW',proposal=Carrier(candidate_reference_solutions=[],alternative_strategies=[]),analysis=Carrier(verifier_plan=[]))
    text=case['solution']
    source=Carrier(solution_text=text,source_hash=hashlib.sha256(text.encode()).hexdigest(),transcription_id='tr_r1',revision_number=1,problem_id=context.problem_id,provenance=Carrier(revision=Carrier(segments=[TranscriptionSegment(segment_id='s',page_index=0,order=0,kind='text',text=text)])))
    return DynamicSolutionGrader(checker).grade(source,statement,rubric,prep,context,tmp_path/'result')


@pytest.mark.parametrize('case',[c for c in SPEC['cases'] if c['family']=='substitution'],ids=lambda c:c['case_id'])
def test_new_substitution_family_and_negative_pairs(tmp_path,case):
    result=grade_case(tmp_path,case)
    assert result.score==float(case['gold_points'])
    for claim in result.analysis.claims:
        assert case['solution'][claim.start:claim.end]==claim.text
        if claim.claim_type=='SUBSTITUTION':
            assert claim.substitution['match_basis']=='STRUCTURAL_OPERATION'
            assert claim.substitution['complete_solution_claimed'] is False
            assert claim.substitution['variable'] in case['statement']


@pytest.mark.parametrize('source',['0=0','12-12=0','Para w=-3: 12-12=0','Para w=-3: 4*(-2)+8=0','Com w=-2: 4*(-3)+12=0'])
def test_numeric_coincidence_is_not_source_binding(source):
    claims,_=extract(source,problem_equation('Resolva em R: 4*w+12=0.'))
    assert not any(c.claim_type=='SUBSTITUTION' for c in claims)


def test_structural_normalization_does_not_erase_power_sign_or_operations():
    assert syntax_key('(-9)^2') != syntax_key('-9^2')
    assert syntax_key('4*(-3)+12') != syntax_key('0')
    assert syntax_key('2*(18/4)-9')==syntax_key('2*4.5-9')
    assert syntax_key('3*5^2+(-36)*5+105')==syntax_key('105+3*5^2-5*36')
    for text in ['f(5)','a.b','[5]', '__import__("os")', '9^100000', '1/0']:
        with pytest.raises((ValueError,ZeroDivisionError)):
            syntax_key(text)


def test_false_evaluation_is_refuted_without_root_credit():
    claims,_=extract('Para w=-3: 4*w+12=1',problem_equation('Resolva em R: 4*w+12=0.'))
    c=claims[0]
    assert c.claim_type=='SUBSTITUTION' and c.verification_status=='REFUTED'
    assert not c.verified_values


def test_true_nonroot_evaluation_does_not_verify_root():
    claims,_=extract('Com w=-2: 4*w+12=4',problem_equation('Resolva em R: 4*w+12=0.'))
    c=claims[0]
    assert c.verification_status=='VERIFIED' and c.substitution['computed_result']=='4'
    assert not c.substitution['verifies_root'] and not c.verified_values


def test_large_precision_decimal_not_rounded_into_valid_substitution():
    claims,_=extract('2*4.500000000000000000000000000001-9=0',problem_equation('Resolva em R: 2*v-9=0.'))
    assert not any(c.claim_type=='SUBSTITUTION' and c.verification_status=='VERIFIED' for c in claims)


def test_checker_failure_is_technical_not_refutation(tmp_path):
    case=next(c for c in SPEC['cases'] if c['case_id']=='substitution-explicit-positive')
    def broken(claim):raise RuntimeError('controlled')
    result=grade_case(tmp_path,case,broken)
    assert result.score==0 and result.review_required
    assert result.analysis.claims[0].verification_status=='ERROR'


def test_historical_context_is_readable_but_cannot_silently_execute_new_engine(tmp_path):
    case=SPEC['cases'][0]
    result=grade_case(tmp_path,case)
    old=result.context.model_copy(update={'grader_version':'dynamic-grader.v1'})
    assert DynamicGradingContext.model_validate(old.model_dump()).grader_version=='dynamic-grader.v1'
    with pytest.raises(ValueError,match='Historical grader'):
        grade_case(tmp_path,case,context=old)


@pytest.mark.parametrize('case',[c for c in SPEC['cases'] if c['family']=='method'],ids=lambda c:c['case_id'])
def test_method_obligations_and_adjacent_controls(tmp_path,case):
    result=grade_case(tmp_path,case)
    if case['case_id']=='method-specific-formula-positive':
        # This approved wording remains outside the closed executable language;
        # it is a declared missed credit, never silently relaxed to any method.
        assert result.score==0 and result.review_required
    else:
        assert result.score==float(case['gold_points'])
    for claim in result.analysis.claims:
        assert case['solution'][claim.start:claim.end]==claim.text


def test_old_claim_wire_hashes_are_preserved():
    from confia_lean_auditor.dynamic.grading_models import StudentClaim
    from confia_lean_auditor.submissions.integrity import canonical_sha256
    baseline=json.loads((ROOT/'docs/audits/assets/confia-dynamic-r1-dev-v2/baseline.json').read_text())
    for row in baseline['rows']:
        for claim in row['claims']:
            assert StudentClaim.model_validate(claim).model_dump(mode='json')==claim
            assert canonical_sha256(StudentClaim.model_validate(claim).model_dump(mode='json'))==canonical_sha256(claim)


def test_ambiguous_gold_is_predeclared_and_never_relabelled():
    pending=[c for c in SPEC['cases'] if c['eligibility']=='BENCHMARK_ADJUDICATION_REQUIRED']
    assert len(pending)==4 and all(c['gold_points']=='4' for c in pending)
    protocol=json.loads((ROOT/'benchmarks/dynamic/dev_v2/protocol.json').read_text())
    assert hashlib.sha256((ROOT/'benchmarks/dynamic/dev_v2/cases.json').read_bytes()).hexdigest()==protocol['dataset_sha256']


@pytest.mark.parametrize('cosmetic', ['(k^2-13*k+40)=0', '40+k^2-13*k=0', '1*(k^2-13*k+40)=0'])
def test_parentheses_or_order_alone_do_not_create_a_method(tmp_path, cosmetic):
    case=next(c for c in SPEC['cases'] if c['case_id']=='method-restatement-negative').copy()
    case['solution']=cosmetic+'; S={5,8}'
    result=grade_case(tmp_path,case)
    assert result.score==0 and result.analysis.claims[0].claim_type=='RESTATEMENT'


def test_unknown_partial_credit_clause_stays_review_only(tmp_path):
    case=next(c for c in SPEC['cases'] if c['case_id']=='method-partial-explicit-positive').copy()
    case['criterion']={**case['criterion'],'description':case['criterion']['description'].replace('50%','75%')}
    result=grade_case(tmp_path,case)
    assert result.score==0 and result.review_required


@pytest.mark.parametrize('padded', ['(w-w+1)*(4*w+12)=0', '(w-w+1)*(4*w+12)/1=0'])
def test_cancelled_variable_is_not_a_nonconstant_factor(tmp_path,padded):
    case=next(c for c in SPEC['cases'] if c['case_id']=='method-factor-only-positive').copy()
    case['statement']='Resolva nos reais: 4*w+12=0.'
    case['solution']=padded
    result=grade_case(tmp_path,case)
    assert result.score==0
    assert not any(c.strategy_context=='factorization' for c in result.analysis.claims)


def test_combining_partial_clauses_cannot_drop_an_extra_rubric_obligation(tmp_path):
    case=next(c for c in SPEC['cases'] if c['case_id']=='method-partial-explicit-positive').copy()
    case['criterion']={**case['criterion'],'description':
        'Justificar a resolução por transformações equivalentes. '
        'Crédito parcial proporcional às raízes corretas. '
        'Crédito parcial de 50% por transformação equivalente sem conclusão.'}
    result=grade_case(tmp_path,case)
    assert result.score==0 and result.review_required
