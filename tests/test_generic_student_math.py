"""Source fidelity and conservative integration for generic mathematical spans."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import json
import time

import pytest

from confia_lean_auditor.student_claims.generic_math import extract_generic_math, candidate_spans, source_is_valid
from confia_lean_auditor.student_claims.registry import extract_student_claims, extract_student_claims_for_audit
from confia_lean_auditor.claims.common.adapters import claim_from_student, claim_from_extracted, validate_projection
from confia_lean_auditor.claims.common.alignment import align_claims
from confia_lean_auditor.claims.common.rubric_bridge import RubricClaimContext
from confia_lean_auditor.core.schemas import ExtractedClaim
from confia_lean_auditor.core.math_canonical import parse_math

ROOT=Path(__file__).resolve().parents[1]


def records(text, problem='UNSEEN', statement=''):
    return [claim_from_student(c,solution_text=text,statement_text=statement)
            for c in extract_student_claims_for_audit(problem,text)]


@pytest.mark.parametrize('text', ['logo x=2','portanto, x = 2','obtemos x igual a 2',
    'x=2','x vale 2','x é igual a 2','x é 2','a resposta é 2'])
def test_explicit_assignment_spellings(text):
    result=records(text)
    assert len(result)==1
    r=result[0]
    assert r.source.grounding_status=='grounded' and r.source.attributable
    assert r.canonicalization_status=='parsed'
    assert r.provenance.extraction_method=='generic_math'
    assert r.source.raw_text==text[r.source.source_start:r.source.source_end]
    assert r.verification_results==()


@pytest.mark.parametrize('marker',['logo','portanto','assim','daí','concluímos','obtemos','resulta','segue que'])
def test_markers_only_classify_role(marker):
    r=records(marker+' x=2')[0]
    assert r.semantic_role=='conclusion' and not r.verification_results


@pytest.mark.parametrize('expression',['x+y=5','x>3','x≤3','x^3=-1','x⁶=1',
    'cos β = sen β + 1/2',r'\cos(\beta)=\sin(\beta)+\frac{1}{2}',
    '[π/2, 3π/2]','log10(5)=0.6990','2x+1'])
def test_supported_syntax_uses_the_existing_parser(expression):
    r=records(expression)[0]
    expected=parse_math(expression)
    assert expected.status=='parsed'
    assert r.canonicalization_status=='parsed'
    assert r.canonical_form.value==expected.canonical_form.to_dict()


@pytest.mark.parametrize('text',['g(a)=g(b)','a≠b','P(n)=C(n-1,3)*(1/2)^n',
    'log(5)=0,6990','x^(n+1)=x*x^n'])
def test_grounded_unsupported_syntax_is_not_verified(text):
    result=records(text)
    assert result
    assert any(r.source.grounding_status=='grounded' and r.canonicalization_status in {'unsupported','ambiguous'} for r in result)
    assert all(not r.verification_results for r in result)


@pytest.mark.parametrize('n',range(10))
@pytest.mark.parametrize('label',['o algarismo é','o primeiro algarismo é','o último algarismo é'])
def test_digit_detection_is_independent_of_problem_and_expected_number(label,n):
    text=f'{label} {n}.'
    r=records(text)[0]
    assert r.claim_type=='math_value'
    assert r.legacy_payload['data']['expression']==str(n)
    assert r.source.attributable


@pytest.mark.parametrize('text',['a=-1, b=3','b=3 e a=-1','a é menos um e b é três'])
def test_local_bindings_are_consistent(text):
    r=records(text)[0]
    assert r.claim_type=='math_bindings'
    assert r.canonical_form.value=={'a':-1,'b':3}
    assert r.source.grounding_status=='grounded'
    for unsupported in ['x é vinte e um','a resposta é dois mil','x vale dois terços','a resposta é dois,5']:
        assert records(unsupported)==[]


@pytest.mark.parametrize('separator',['. ', '; ', '\n', '\n\n'])
def test_bindings_never_cross_clauses(separator):
    result=records('a=-1'+separator+'b=3')
    assert len(result)==2 and all(r.claim_type!='math_bindings' for r in result)


@pytest.mark.parametrize('text,role',[
    ('Tentamos x=2, mas isso é impossível.','rejected_attempt'),
    ('Suponha x=2.','assumption'),
    ('Isso daria x=2, mas essa hipótese falha.','rejected_attempt'),
    ('O enunciado afirma x=2.','quoted_statement'),
    ('“Logo x=2.”','quoted_statement'),
    ('A resposta não é 5.','unknown'),
    ('Será que x=2?','unknown'),
    ('O código irrelevante é x=2.','unknown'),
])
def test_adversarial_context_never_promotes_a_conclusion(text,role):
    result=records(text)
    assert result
    assert all(not r.source.attributable for r in result)
    assert all(r.semantic_role==role for r in result)


@pytest.mark.parametrize('text',['Tenho 5 lápis.','não sei fazer','x=2+','x=','a resposta é 2+',
    'Há quinze alunos nesta sala.'])
def test_no_assertion_or_incomplete_expression_is_not_a_claim(text):
    assert records(text)==[]


def test_unknown_suffix_is_never_truncated_to_correct_numeric_answer():
    result=records('x=2evil')
    assert all(r.legacy_payload['data'].get('expression')!='x=2' for r in result)
    assert not any(r.canonicalization_status=='parsed' for r in result)


def test_negated_value_preserves_negation_without_positive_canonical_form():
    r=records('a resposta não é 5')[0]
    assert r.legacy_payload['data']['negated'] is True
    assert r.canonical_form is None and not r.source.attributable
    from confia_lean_auditor.claims.common.canonical import mathematical_value
    first=records('o primeiro algarismo é 5')[0]
    last=records('o último algarismo é 5')[0]
    assert first.canonical_form.subject!=last.canonical_form.subject
    assert mathematical_value(first.canonical_form) is None
    assert mathematical_value(last.canonical_form) is None


def test_prompt_quotation_cannot_become_student_achievement():
    assert not records('x=2',statement='Sabendo que x=2, determine y.')[0].source.attributable


def test_function_property_and_sequence_are_typed_but_not_formalized():
    for text in ['g não é injetiva','g não injetora','a sequência é uma PG']:
        r=records(text)[0]
        assert r.claim_type=='math_property' and r.canonical_form is None
        assert r.source.grounding_status=='grounded'
        assert not r.verification_results


def test_adjacent_chain_equations_do_not_infer_endpoint_equality():
    result=records('x=2+1=3')
    assert [r.legacy_payload['data']['expression'] for r in result]==['x=2+1','2+1=3']
    assert all(r.source.raw_text in 'x=2+1=3' for r in result)


def test_specific_duplicate_preserves_id_data_and_both_origins():
    text='Logo a=-1 e b=3.'
    old=extract_student_claims('ITA2025F2Q1',text)
    combined=extract_student_claims_for_audit('ITA2025F2Q1',text)
    final=next(c for c in combined if c.claim_type=='f2q1_student_final_answer')
    assert final.id==old[-1].id and final.data==old[-1].data
    assert 'generic_math' in final.grounding['extraction_origins']
    assert not any(c.claim_type=='math_bindings' for c in combined)
    for pid,text in [('ITA2025F2Q5','O primeiro algarismo é 5.'),('ITA2025F2Q1','x^57=-1.')]:
        original=extract_student_claims(pid,text)
        combined=extract_student_claims_for_audit(pid,text)
        assert len(combined)==len(original)
        assert any('generic_math' in c.grounding.get('extraction_origins',[]) for c in combined)


def test_competing_assignments_remain_ambiguous_not_silently_selected():
    result=records('x=2. x=3.')
    assert len(result)==2
    assert all(r.source.grounding_status=='ambiguous' and not r.source.attributable for r in result)


@pytest.mark.parametrize('tamper',['data','span','source','role','canonical'])
def test_serialized_annotations_cannot_forge_grounding(tamper):
    text='logo x=2';r=records(text)[0]
    if tamper in {'data','span'}:
        payload=deepcopy(r.legacy_payload)
        if tamper=='data':payload['data']['expression']='x=3'
        else:payload['grounding']['source_start']=0
        assert not source_is_valid(payload,text)
    else:
        forged=(r.model_copy(update={'semantic_role':'assumption'}) if tamper=='role' else
                r.model_copy(update={'canonical_form':None}) if tamper=='canonical' else
                r.model_copy(update={'source':r.source.model_copy(update={'attributable':False})}))
        with pytest.raises(ValueError):validate_projection(forged,solution_text=text)


def test_existing_alignment_runs_without_new_matching_rules():
    text='x=2'
    reference=claim_from_extracted(ExtractedClaim(id='expected',type='math_relation',text='expected',
        evidence='reference',confidence=1,normalized={'expression':'x=2'}),problem_id='UNSEEN',solution_text=text)
    aligned=align_claims(reference,records(text),solution_text=text)
    assert aligned.status=='aligned' and aligned.alignment_basis
    assert not records(text)[0].verification_results


def test_no_assets_checkers_or_llm_needed_and_detection_is_bounded(monkeypatch):
    import confia_lean_auditor.core.problem_assets as assets
    monkeypatch.setattr(assets,'validate_problem_assets',lambda *a,**k:pytest.fail('assets accessed'))
    start=time.monotonic()
    assert len(extract_generic_math('ANY','x=2\n'*1000))<=256
    assert extract_generic_math('ANY','x'*20001)==[]
    assert time.monotonic()-start<5


def test_priority_saved_texts_without_reauditing_or_rewriting_artifacts():
    base=ROOT/'artifacts/evaluations/ita1000_v1_2/smoke_v2_20261029T040221Z/cases'
    if not base.exists():pytest.skip('Local replay artifacts; portable cases above cover the syntax')
    for ds,digit in [('ITA2025F2Q5_S003_L04','5'),('ITA2025F2Q5_S024_L04','1')]:
        path=base/ds/'solution.txt';before=path.read_bytes();text=before.decode()
        matches=[r for r in records(text,ds.split('_')[0]) if r.legacy_payload['data'].get('concept')=='leading_digit'
                 or r.canonical_form and r.canonical_form.subject=='leading_digit']
        assert len(matches)==1
        data=matches[0].legacy_payload['data']
        assert data.get('expression',str(data.get('digit')))==digit
        assert matches[0].source.grounding_status=='grounded'
        assert (matches[0].provenance.extraction_method=='generic_math' or
                'generic_math' in matches[0].legacy_payload['grounding'].get('extraction_origins',[]))
        assert path.read_bytes()==before
    assert records((base/'ITA2025Q4_S002_L04/solution.txt').read_text())==[]
    pair=records((base/'ITA2025F2Q1_S003_L02/solution.txt').read_text())[0]
    assert pair.canonical_form.value=={'a':-1,'b':3}
