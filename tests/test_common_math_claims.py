"""Common records preserve P0 authority; alignment never supplies proof credit."""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
import json

import pytest

from confia_lean_auditor.claims.common import (
    MathClaimRecord, MathClaimCatalog, Origin, SemanticRole,
    claim_from_extracted, claim_from_student, align_claims,
)
from confia_lean_auditor.claims.common.adapters import project_extracted_claim
from confia_lean_auditor.claims.common.bridges import (
    checker_input_from_record, positive_credit_from_record, record_is_mathematically_refuted,
)
from confia_lean_auditor.claims.common.catalog import build_claim_catalog
from confia_lean_auditor.claims.extract_claims import extract_claims
from confia_lean_auditor.core.schemas import ExtractedClaim, AuditResponse, FormalStepResult
from confia_lean_auditor.core.problem_assets import validate_problem_assets
from confia_lean_auditor.student_claims.registry import extract_student_claims
from confia_lean_auditor.rubric.positive_evidence import can_support_rubric_credit
from test_positive_credit_evidence import assess, verified_check, PROBLEMS

ROOT = Path(__file__).resolve().parents[1]


def pair(text='Portanto a=-1 e b=3.', expected=None):
    pid='ITA2025F2Q1'
    reference=extract_claims(pid,'Portanto a=-1 e b=3.').claims[-1]
    if expected is not None:
        reference=reference.model_copy(update={'normalized':expected})
    student=next(c for c in extract_student_claims(pid,text) if c.claim_type=='f2q1_student_final_answer')
    return claim_from_extracted(reference,problem_id=pid,solution_text=text), claim_from_student(student,solution_text=text)


def test_equal_pairs_align_but_keep_separate_origins_and_ids():
    text='Portanto a=-1 e b=3.';r,s=pair(text)
    result=align_claims(r,[s],solution_text=text)
    assert result.status=='aligned' and result.preferred_attribution_ids==(s.record_id,)
    assert r.provenance.origin==Origin.REFERENCE_EXPECTED
    assert s.provenance.origin==Origin.STUDENT_EXPLICIT
    assert r.record_id!=s.record_id and r.source.raw_text is None
    assert s.source.raw_text==text and s.semantic_role==SemanticRole.CONCLUSION
    assert r.verification_results==s.verification_results==()  # matching is not verification


def test_conflicting_grounded_pair_is_preferred_for_attribution_not_overwritten():
    text='Portanto a=3 e b=2.';r,s=pair(text)
    result=align_claims(r,[s],solution_text=text)
    assert result.status=='conflicting' and result.preferred_attribution_ids==(s.record_id,)
    assert s.canonical_form.value=={'a':3,'b':2}
    assert r.canonical_form.value=={'a':-1,'b':3}


@pytest.mark.parametrize('text',['Portanto b=3 e a=-1.','Portanto a = −1 e b = 3.'])
def test_supported_binding_notation_aligns_without_string_similarity(text):
    r,s=pair(text)
    assert align_claims(r,[s],solution_text=text).status=='aligned'


@pytest.mark.parametrize('text',[
    'cos beta - sen beta = 1/2.',
    'sen beta - cos beta = -1/2.',
    '2*cos(beta)-2*sin(beta)=1.',
])
def test_existing_affine_canonicalization_aligns_supported_equalities(text):
    pid='ITA2025F2Q3'
    reference=extract_claims(pid,'cos beta - sen beta = 1/2.').claims[0]
    student=next(c for c in extract_student_claims(pid,text) if c.claim_type=='f2q3_student_beta_difference')
    r=claim_from_extracted(reference,problem_id=pid,solution_text=text)
    s=claim_from_student(student,solution_text=text)
    assert align_claims(r,[s],solution_text=text).status=='aligned'
    assert s.canonical_form.method=='canonicalize_equality'


@pytest.mark.parametrize('text',[
    'Não podemos concluir que a=-1 e b=3.',
    'Tentei a=-1 e b=3, mas a tentativa foi abandonada.',
    'Suponha a=-1 e b=3.',
    'O código irrelevante é a=-1 e b=3.',
    'Não é verdade. Portanto a=-1 e b=3.',
    '"Portanto a=-1 e b=3."',
    "'Portanto a=-1 e b=3.'",
])
def test_qualified_or_irrelevant_content_is_never_confirmed_by_alignment(text):
    if extract_student_claims('ITA2025F2Q1',text):
        r,s=pair(text)
    else:
        # P0 already suppresses some candidates. The common layer must neither
        # fabricate them nor trust an ungrounded candidate supplied by a caller.
        seed='Portanto a=-1 e b=3.'
        r=claim_from_extracted(extract_claims('ITA2025F2Q1',seed).claims[-1],
            problem_id='ITA2025F2Q1',solution_text=text)
        assert align_claims(r,[],solution_text=text).status=='unmatched'
        candidate=replace(extract_student_claims('ITA2025F2Q1',seed)[0],grounding=None)
        s=claim_from_student(candidate,solution_text=text)
    result=align_claims(r,[s],solution_text=text)
    assert result.status!='aligned' and result.preferred_attribution_ids==()
    assert not s.source.attributable
    with pytest.raises(ValueError):checker_input_from_record(s,solution_text=text)


def test_quotation_role_is_distinct_from_verified_text_correspondence():
    text='"Portanto a=-1 e b=3."';_,s=pair(text)
    assert s.semantic_role==SemanticRole.QUOTED_STATEMENT
    assert s.provenance.origin==Origin.STUDENT_CANDIDATE


def test_both_without_grounding_do_not_align_even_when_values_agree():
    text='Portanto a=-1 e b=3.';r,s=pair(text)
    payload=deepcopy(s.legacy_payload);payload['grounding']=None
    s=claim_from_student(payload,solution_text=text)
    assert r.canonical_form==s.canonical_form
    assert align_claims(r,[s],solution_text=text).status=='unmatched'


def test_ambiguous_grounding_and_duplicate_identity_are_explicit():
    text='a=-1 e b=3. a=3 e b=2.';r,s=pair(text)
    assert s.source.grounding_status=='ambiguous'
    assert align_claims(r,[s],solution_text=text).status=='ambiguous'
    text='Portanto a=-1 e b=3.';r,s=pair(text)
    assert align_claims(r,[s,s],solution_text=text).status=='ambiguous'


def test_absent_canonical_form_is_not_fabricated_and_legacy_payload_is_lossless():
    text='Portanto a=-1 e b=3.';r,s=pair(text,expected={})
    assert r.canonical_form is None
    assert align_claims(r,[s],solution_text=text).status=='unmatched'
    assert r.legacy_payload['normalized']=={}


@pytest.mark.parametrize('field,value',[
    ('claim_type','other'),('record_id','forged'),('problem_id','OTHER'),
    ('semantic_role',SemanticRole.ASSUMPTION),
])
def test_modified_common_annotations_cannot_change_checker_input(field,value):
    text='Portanto a=-1 e b=3.';r,s=pair(text)
    altered=s.model_copy(update={field:value})
    assert align_claims(r,[altered],solution_text=text).status in {'ambiguous','unmatched'}
    with pytest.raises(ValueError):checker_input_from_record(altered,solution_text=text)


def test_canonical_or_source_tampering_cannot_create_alignment():
    text='Portanto a=-1 e b=3.';r,s=pair(text)
    s.canonical_form.value['a']=99
    assert align_claims(r,[s],solution_text=text).status=='ambiguous'
    with pytest.raises(ValueError):checker_input_from_record(s,solution_text=text)
    _,s=pair(text)
    assert align_claims(r,[s],solution_text=text+' Outro texto.').status=='ambiguous'
    with pytest.raises(ValueError):checker_input_from_record(s,solution_text=text+' Outro texto.')


@pytest.mark.parametrize('pid',PROBLEMS)
def test_all_current_claims_roundtrip_without_losing_legacy_information(pid):
    text=(ROOT/'problems'/pid/'examples/correct_solution.txt').read_text()
    for claim in extract_claims(pid,text).claims:
        before=claim.model_dump(mode='json')
        record=claim_from_extracted(claim,problem_id=pid,solution_text=text)
        restored=MathClaimRecord.model_validate_json(record.model_dump_json())
        assert restored==record and record.legacy_payload==before
        assert project_extracted_claim(restored,solution_text=text).model_dump(mode='json')==before
        assert claim.model_dump(mode='json')==before
        with pytest.raises(ValueError):checker_input_from_record(restored,solution_text=text)
    for claim in extract_student_claims(pid,text):
        before=asdict(claim)
        record=claim_from_student(claim,solution_text=text)
        restored=MathClaimRecord.model_validate_json(record.model_dump_json())
        assert restored==record and record.legacy_payload==before and asdict(claim)==before
        if record.source.attributable:
            assert asdict(checker_input_from_record(restored,solution_text=text))==before
            assert text[record.source.source_start:record.source.source_end]==record.source.raw_text
        else:
            with pytest.raises(ValueError):checker_input_from_record(restored,solution_text=text)


@pytest.mark.parametrize('pid',PROBLEMS)
def test_common_positive_bridge_keeps_existing_gate_results_exactly(pid):
    text=(ROOT/'problems'/pid/'examples/correct_solution.txt').read_text()
    assets=validate_problem_assets(ROOT/'problems'/pid,pid)
    claims={c.type:c for c in extract_claims(pid,text).claims}
    for item in assets.rubric.items:
        claim=claims.get(item.claim_type)
        record=claim_from_extracted(claim,problem_id=pid,solution_text=text) if claim else None
        args=dict(problem_id=pid,item=item,solution_text=text,statement_text=assets.problem.statement,
                  verified_microclaim_ids=item.required_microclaim_ids)
        assert positive_credit_from_record(record=record,**args)==can_support_rubric_credit(claim=claim,**args)
    # No changes to scores or verdict inputs in the supported fixtures.
    rubric=assess(pid,text)
    assert rubric.score==rubric.max_score==10


def test_positive_bridge_does_not_accept_a_student_in_place_of_reference():
    text='Portanto a=-1 e b=3.';_,student=pair(text)
    with pytest.raises(ValueError):
        positive_credit_from_record(record=student,solution_text=text,problem_id='ITA2025F2Q1',
            item=SimpleNamespace(id='final_answer',required_microclaim_ids=[]))


def test_negative_bridge_reuses_grounding_and_formal_refutation_gate():
    text='Portanto a=3 e b=2.';reference,student=pair(text)
    check=asdict(verified_check('ITA2025F2Q1',text,'f2q1_student_final_answer'))
    check.update(status='refuted',compiled=False,formal_status='refuted',
                 refutation_verified=True,refutation_lean_file='controlled_refutation.lean')
    assert record_is_mathematically_refuted(student,check,solution_text=text)
    assert not record_is_mathematically_refuted(reference,check,solution_text=text)
    assert not record_is_mathematically_refuted(student,{**check,'refutation_verified':False},solution_text=text)
    assert not record_is_mathematically_refuted(student,{**check,'data':{'a':-1,'b':3}},solution_text=text)
    assert not record_is_mathematically_refuted(student,check,solution_text=text+'x')


@pytest.mark.parametrize('pid',['ITA2025Q1','ITA2025Q3','ITA2025Q4','ITA2025F2Q1','ITA2025F2Q3','ITA2025F2Q5'])
def test_catalog_links_rubric_and_verification_without_creating_student_claims(pid):
    text=(ROOT/'problems'/pid/'examples/correct_solution.txt').read_text()
    assets=validate_problem_assets(ROOT/'problems'/pid,pid);extraction=extract_claims(pid,text)
    students=extract_student_claims(pid,text);rubric=assess(pid,text)
    step=FormalStepResult(id='reference_proof',type='controlled',description='Reference',evidence='synthetic',
        lhs='1',rhs='1',lean_method='rfl',supports_claim_types=[extraction.claims[0].type],
        lean_file='controlled.lean',status='verified',compiled=True,exit_code=0,
        verification_scope='generated_reference')
    catalog=build_claim_catalog(problem_id=pid,solution_text=text,extraction=extraction,students=students,
        checks=[],rubric_config=assets.rubric,rubric=rubric,formal_steps=[step],statement_text=assets.problem.statement)
    assert MathClaimCatalog.model_validate_json(catalog.model_dump_json())==catalog
    assert len(catalog.records)==len(extraction.claims)+len(students)
    assert len(catalog.criterion_traces)==len(assets.rubric.items)
    references=[r for r in catalog.records if r.provenance.channel=='extracted']
    assert references[0].verification_results[0].origin==Origin.GENERATED_REFERENCE
    assert references[0].verification_results[0].attributed_to_student is False
    assert all(r.provenance.origin==Origin.REFERENCE_EXPECTED for r in references)
    for item,trace in zip(rubric.items,catalog.criterion_traces):
        assert trace.criterion_id==item.id and trace.reference_record_id
        assert trace.evidence_ref.endswith('/positive_evidence')
    if pid in {'ITA2025Q1','ITA2025Q3','ITA2025Q4'}:
        assert not students and all(a.status=='unmatched' for a in catalog.alignments)


def test_generated_reference_never_overwrites_student_source():
    text='Portanto a=3 e b=2.';r,s=pair(text)
    r2=r.model_copy(update={'provenance':r.provenance.model_copy(update={'origin':Origin.STUDENT_EXPLICIT})})
    assert align_claims(r2,[s],solution_text=text).status=='ambiguous'
    assert s.legacy_payload['data']=={'a':3,'b':2}


def test_legacy_public_response_shape_has_no_common_layer_fields():
    path=ROOT/'artifacts/runs/20261027T145952_481754/audit.json'
    if not path.exists():pytest.skip('Local historical artifact')
    original=path.read_bytes();payload=json.loads(original)
    assert AuditResponse.model_validate(payload).model_dump(mode='json')==payload
    assert path.read_bytes()==original
    assert 'math_claims' not in AuditResponse.model_fields


def test_checker_projection_preserves_the_existing_lean_proposition():
    from confia_lean_auditor.lean.student_claim_checkers.ita2025f2q1 import _lean_statement_and_method_for_f2q1_claim
    text='Portanto a=-1 e b=3.'
    original=extract_student_claims('ITA2025F2Q1',text)[0]
    record=claim_from_student(original,solution_text=text)
    projected=checker_input_from_record(record,solution_text=text)
    assert _lean_statement_and_method_for_f2q1_claim(projected)==_lean_statement_and_method_for_f2q1_claim(original)


@pytest.mark.parametrize('text,role',[
    ('Suponha uma hipótese. a=-1 e b=3.',SemanticRole.ASSUMPTION),
    ('Tentativa abandonada. a=-1 e b=3.',SemanticRole.REJECTED_ATTEMPT),
])
def test_common_roles_keep_parent_scope_of_a_locally_grounded_sentence(text,role):
    r,s=pair(text)
    assert s.source.grounding_status=='grounded'
    assert s.semantic_role==role and not s.source.attributable
    assert align_claims(r,[s],solution_text=text).status=='unmatched'


def test_reference_and_student_canonical_absence_do_not_disable_legacy_storage():
    pid='ITA2025F2Q3';text='cos beta = (1-sqrt(7))/4.'
    student=next(c for c in extract_student_claims(pid,text) if c.claim_type=='f2q3_student_candidate_value')
    record=claim_from_student(student,solution_text=text)
    assert record.canonical_form is None
    assert record.legacy_payload['data']['expr']==student.data['expr']
    assert asdict(checker_input_from_record(record,solution_text=text))==asdict(student)


def test_alignment_never_crosses_problem_boundaries():
    text='Portanto a=-1 e b=3.';r,s=pair(text)
    other=replace(extract_student_claims('ITA2025F2Q1',text)[0],problem_id='OTHER')
    foreign=claim_from_student(other,solution_text=text)
    assert align_claims(r,[foreign],solution_text=text).status=='unmatched'


def test_native_common_record_does_not_require_a_legacy_model_or_gain_a_checker():
    from confia_lean_auditor.claims.common.schemas import Provenance, SourceBinding
    record=MathClaimRecord(record_id='native:1',problem_id='FUTURE',claim_type='new_mathematical_claim',
        provenance=Provenance(origin=Origin.STUDENT_DERIVED,channel='native'),
        source=SourceBinding(grounding_status='unavailable'),semantic_role=SemanticRole.INTERMEDIATE)
    assert record.legacy_payload is None and record.canonical_form is None
    assert MathClaimRecord.model_validate_json(record.model_dump_json())==record
    with pytest.raises(ValueError):checker_input_from_record(record,solution_text='')


@pytest.mark.parametrize('payload',[
    {'grounding_status':'grounded','attributable':True},
    {'grounding_status':'unresolved','raw_text':'a','source_start':0},
    {'grounding_status':'grounded','raw_text':'a','source_start':0,'source_end':2},
    {'grounding_status':'grounded','raw_text':'a','source_start':0,'source_end':1,'attributable':True,'source_sha256':'bad'},
])
def test_common_source_shape_cannot_claim_incomplete_or_invalid_spans(payload):
    from confia_lean_auditor.claims.common.schemas import SourceBinding
    with pytest.raises(ValueError):SourceBinding(**payload)
