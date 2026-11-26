"""POINTS REQUIRE EVIDENCE: controlled reference proofs are not source evidence."""
from dataclasses import asdict
from pathlib import Path
import json

import pytest

from confia_lean_auditor.claims.extract_claims import extract_claims
from confia_lean_auditor.core.problem_assets import validate_problem_assets
from confia_lean_auditor.core.schemas import AuditResponse, MicroclaimResult
from confia_lean_auditor.rubric.rubric_evaluator import evaluate_rubric
from confia_lean_auditor.student_claims.registry import extract_student_claims
from confia_lean_auditor.student_claims.schemas import StudentClaimCheck
from confia_lean_auditor.reports.report_builder import _build_rubric_evidence_items

ROOT = Path(__file__).resolve().parents[1]
PROBLEMS = sorted(p.name for p in (ROOT/'problems').iterdir() if (p/'rubric.json').exists())


def assess(pid, text, *, checks=(), verified=True, supply_source=True, extraction=None):
    assets = validate_problem_assets(ROOT/'problems'/pid, pid)
    if extraction is None:
        extraction = extract_claims(pid, text)
    # Explicitly controlled reference verification profile, not a Lean execution.
    microclaims = [MicroclaimResult(id=m.id, description=m.description, textual_evidence=True,
        claim_types=m.claim_types, depends_on_microclaim_ids=m.depends_on_microclaim_ids,
        lean_status='verified_by_lean', verification_scope='generated_reference')
        for m in assets.microclaims.microclaims] if verified else []
    return evaluate_rubric(ROOT, pid, extraction, microclaims, assets.rubric,
        solution_text=text if supply_source else None, student_claim_checks=checks,
        statement_text=assets.problem.statement)


@pytest.mark.parametrize('pid', PROBLEMS)
def test_correct_fixtures_keep_all_attributable_credit(pid):
    text=(ROOT/'problems'/pid/'examples/correct_solution.txt').read_text()
    rubric=assess(pid,text)
    assert rubric.score == rubric.max_score, [(i.id,i.positive_evidence) for i in rubric.items if i.points is None]
    for item in rubric.items:
        evidence=item.positive_evidence
        assert evidence['supported'] and evidence['source_spans']
        assert evidence['verification_type'] != 'reference_heuristic'
        for span in evidence['source_spans']:
            assert text[span['source_start']:span['source_end']] == span['source_text']
        assert item.claim_id and item.evidence


@pytest.mark.parametrize('pid,text',[
    ('ITA2025F2Q5','5 não é o algarismo final.'),
    ('ITA2025F2Q5','O primeiro algarismo de 3^100 não é 5.'),
    ('ITA2025F2Q1','Não podemos concluir que a=−1 e b=3.'),
    ('ITA2025F2Q3','A igualdade cos beta - sen beta = 1/2 seria falsa aqui.'),
    ('ITA2025Q1','Não concluo que a=15.'),
    ('ITA2025Q1','Suponha a=15.'),
    ('ITA2025Q1','Tentei a=15, mas essa tentativa foi abandonada.'),
    ('ITA2025Q1','O código irrelevante do exemplo é a=15.'),
    ('ITA2025Q1','a=15+1.'),
    ('ITA2025F2Q8','A página 1013 descreve diferenças de colunas e soma alternada.'),
    ('ITA2025Q8','Estudo de sinais. Pontos críticos. O número 13pi/6.'),
    ('ITA2025Q4','Prove que g não é injetora.'),
    ('ITA2025Q5','Prove que (a_n) também é uma PG.'),
    ('ITA2025Q4','Não podemos concluir que g não é injetora.'),
    ('ITA2025Q5','Se (a_n) é uma PG, algo acontece.'),
    ('ITA2025F2Q1','a=-1 e b=3. a=9 e b=8.'),
    ('ITA2025Q1','Não é verdade. Portanto a=15.'),
    ('ITA2025Q1','"Portanto a=15."'),
    ('ITA2025Q1',"'Portanto a=15.'"),
    ('ITA2025Q1','‘Portanto a=15.’'),
])
def test_adversarial_mentions_never_gain_credit_from_reference_proofs(pid,text):
    rubric=assess(pid,text)
    assert all(i.points is None and i.mathematical_status=='indeterminate' for i in rubric.items)
    assert rubric.evaluated_score == 0


@pytest.mark.parametrize('pid',PROBLEMS)
def test_copying_the_actual_problem_statement_does_not_earn_points(pid):
    statement=json.loads((ROOT/'problems'/pid/'problem.json').read_text())['statement']
    assert all(i.points is None for i in assess(pid,statement).items)


@pytest.mark.parametrize('pid,text,criterion',[
    ('ITA2025Q4','g não é injetora.','not_injective_conclusion'),
    ('ITA2025Q5','Portanto, (a_n) também é uma PG.','conclusion_pg'),
])
def test_rubric_permitted_textual_conclusions_do_not_require_lean(pid,text,criterion):
    rubric=assess(pid,text,verified=False)
    item=next(i for i in rubric.items if i.id==criterion)
    assert item.points==1 and item.positive_evidence['verification_type']=='grounded_text'
    assert all(i.points is None for i in rubric.items if i.id!=criterion)


def test_reference_heuristic_without_original_source_is_pending_not_zero():
    pid='ITA2025F2Q1'
    text=(ROOT/'problems'/pid/'examples/correct_solution.txt').read_text()
    assert all(i.points is None for i in assess(pid,text,supply_source=False).items)


def test_missing_required_microclaims_cannot_be_replaced_by_text():
    pid='ITA2025F2Q1'
    text=(ROOT/'problems'/pid/'examples/correct_solution.txt').read_text()
    result=assess(pid,text,verified=False)
    assert [(i.id,i.points) for i in result.items]==[
        ('power_reductions',None),('reduced_polynomial_form',None),('coefficient_system',None),('final_answer',2)]


def verified_check(pid,text,kind):
    claim=next(c for c in extract_student_claims(pid,text) if c.claim_type==kind)
    return StudentClaimCheck(id=claim.id,problem_id=pid,claim_type=kind,raw_text=claim.raw_text,
        normalized_text=claim.normalized_text,lean_statement='controlled proposition',method='norm_num',
        status='verified',compiled=True,lean_file='controlled.lean',stdout='',stderr='',
        data=claim.data,grounding=claim.grounding,formal_status='verified')


def test_grounded_formal_check_strengthens_only_its_own_criterion():
    pid='ITA2025F2Q1';text='Portanto a=-1 e b=3.'
    check=verified_check(pid,text,'f2q1_student_final_answer')
    rubric=assess(pid,text,checks=[asdict(check)])
    item=next(i for i in rubric.items if i.id=='final_answer')
    assert item.points==2 and item.positive_evidence['verification_type']=='formal_verification'
    assert item.positive_evidence['student_check_ids']==[check.id]
    assert all(i.points is None for i in rubric.items if i.id!='final_answer')
    # Wrong source digest must not promote a textual finding to formal evidence.
    check.grounding['source_sha256']='0'*64
    item=assess(pid,text,checks=[check]).items[-1]
    assert item.positive_evidence['verification_type']=='deterministic_check'


def test_report_uses_original_source_without_claiming_a_reference_proof_is_student_reasoning():
    rubric=assess('ITA2025Q4','Portanto, g não é injetora.',verified=False)
    item=next(i for i in _build_rubric_evidence_items(rubric,set()) if i.id=='not_injective_conclusion')
    assert item.evidence=='Portanto, g não é injetora.'
    assert 'trechos originais' in item.explanation and 'formalmente' not in item.explanation


def test_historical_response_roundtrip_keeps_hash_shape():
    path=ROOT/'artifacts/runs/20261027T145952_481754/audit.json'
    if not path.exists():
        pytest.skip('Historical smoke artifact is local')
    before=path.read_bytes(); data=json.loads(before)
    assert AuditResponse.model_validate(data).model_dump(mode='json')==data
    assert path.read_bytes()==before


@pytest.mark.parametrize('pid',PROBLEMS)
def test_multiline_quote_cannot_launder_an_entire_correct_solution(pid):
    text=(ROOT/'problems'/pid/'examples/correct_solution.txt').read_text()
    assert all(i.points is None for i in assess(pid,'“'+text+'”').items)


@pytest.mark.parametrize('text',[
    'a=15. Isso está errado.',
    'a=15. Essa resposta é falsa.',
    'a=15. Essa tentativa foi abandonada.',
    'Não sabemos a resposta. a=15.',
])
def test_sentence_splitting_preserves_paragraph_qualifiers(text):
    assert all(i.points is None for i in assess('ITA2025Q1',text).items)


@pytest.mark.parametrize('pid,text,kind',[
    ('ITA2025Q1','Não podemos concluir a=15.','final_answer'),
    ('ITA2025Q4','Os números 1/8 e 3/8 são positivos.','positive_witnesses'),
    ('ITA2025Q8','Estudo de sinais.','sign_analysis'),
    ('ITA2025F2Q8','A resposta é 1013. Essa tentativa foi abandonada.','final_answer'),
])
def test_real_legacy_detector_candidate_is_insufficient(pid,text,kind):
    assert kind in {c.type for c in extract_claims(pid,text).claims}
    rubric=assess(pid,text)
    item=next(i for i in rubric.items if i.positive_evidence['claim_id'] and
              next(c.type for c in extract_claims(pid,text).claims if c.id==i.claim_id)==kind)
    assert item.points is None and item.positive_evidence['supported'] is False


def test_rejected_equality_is_not_extracted_and_a_legacy_candidate_still_gets_no_credit():
    pid = 'ITA2025F2Q3'
    positive = 'cos beta - sen beta = 1/2.'
    source = positive + ' Essa igualdade é falsa.'
    assert 'beta_difference' not in {c.type for c in extract_claims(pid, source).claims}
    assert assess(pid, source).items[0].points is None
    # A historical/external candidate must still fail the independent credit gate.
    legacy = extract_claims(pid, positive)
    assert 'beta_difference' in {c.type for c in legacy.claims}
    item = assess(pid, source, extraction=legacy).items[0]
    assert item.claim_id and item.points is None
    assert item.positive_evidence['supported'] is False


@pytest.mark.parametrize('text',['A resposta é 1013?','A resposta é 1013. Esse resultado foi rejeitado.'])
def test_questions_and_rejected_results_are_not_asserted_conclusions(text):
    assert all(i.points is None for i in assess('ITA2025F2Q8',text).items)


def test_long_unrecognized_math_does_not_match_a_truncated_answer():
    assert all(i.points is None for i in assess('ITA2025Q1','a='+'sin'*900+'!').items)


@pytest.mark.parametrize('pid',PROBLEMS)
def test_correct_mathematical_content_survives_paragraph_reflow(pid):
    text=' '.join((ROOT/'problems'/pid/'examples/correct_solution.txt').read_text().split())
    rubric=assess(pid,text)
    assert rubric.score==rubric.max_score, [(i.id,i.positive_evidence['reason']) for i in rubric.items if i.points is None]


def test_reference_dependencies_cannot_launder_unattributed_witnesses():
    text=(ROOT/'problems/ITA2025Q4/examples/correct_solution.txt').read_text()
    text=text.replace('Escolha x1 = 1/8 e x2 = 3/8. Ambos são positivos.',
                      'Os números 1/8 e 3/8 são positivos.')
    rubric=assess('ITA2025Q4',text)
    assert all(i.points is None for i in rubric.items if i.id!='not_injective_conclusion')
    assert rubric.items[-1].points==1  # the existing rubric permits the conclusion alone
    assert any(not d['supported'] for d in rubric.items[1].positive_evidence['reference_dependencies'])


@pytest.mark.parametrize('pid,text,kind',[
    ('ITA2025Q1','- a^2 - 2a + 5 = 200.','area_equation'),
    ('ITA2025F2Q3','cos beta - sen beta = 1/2 x.','beta_difference'),
    ('ITA2025F2Q5','O primeiro algarismo de 3^100 é 5.5.','final_digit_five'),
    ('ITA2025F2Q8','A resposta é 1013.5.','final_answer'),
    ('ITA2025Q3','O termo independente é 0+1.','final_answer_zero'),
    ('ITA2025F2Q5','O primeiro algarismo de 3^100 é 5-1.','final_digit_five'),
    ('ITA2025F2Q8','A resposta é 1013-1.','final_answer'),
])
def test_incomplete_or_wrong_mathematical_representation_never_earns_points(pid,text,kind):
    rubric=assess(pid,text)
    assert all(i.points is None for i in rubric.items)


@pytest.mark.parametrize('pid,criterion,points',[
    ('ITA2025Q1','final_answer',1),('ITA2025Q3','final_answer',1),
    ('ITA2025Q4','not_injective_conclusion',1),('ITA2025Q5','conclusion_pg',1),
    ('ITA2025Q8','longest_interval',2),('ITA2025F2Q1','final_answer',2),
    ('ITA2025F2Q3','final_answer',2),('ITA2025F2Q5','final_digit',2),
    ('ITA2025F2Q6','final_answer',2),('ITA2025F2Q8','final_answer',1.5),
])
def test_existing_answer_only_fixtures_preserve_rubric_permitted_conclusions(pid,criterion,points):
    text=(ROOT/'problems'/pid/'examples/answer_only.txt').read_text()
    item=next(i for i in assess(pid,text).items if i.id==criterion)
    assert item.points==points,item.positive_evidence


def test_existing_latex_projection_is_reused_without_losing_original_spans():
    text=r'\[\cos\beta-\operatorname{sen}\beta=\frac{1}{2}\]'
    item=assess('ITA2025F2Q3',text).items[0]
    assert item.points==2,item.positive_evidence
    assert all(text[s['source_start']:s['source_end']]==s['source_text'] for s in item.positive_evidence['source_spans'])
    wrong=text.replace(r'=\frac',r'=-\frac')
    assert all(i.points is None for i in assess('ITA2025F2Q3',wrong).items)


def test_canonical_determinant_proof_cannot_replace_the_written_expansion():
    text=(ROOT/'problems/ITA2025Q1/examples/correct_solution.txt').read_text()
    text=text.replace('(a-1)4a - 2(a^2-5)', '(a-1)4a - 7(a^2-5)')
    item=next(i for i in assess('ITA2025Q1',text).items if i.id=='area_formula')
    assert item.points is None


def test_ratio_formula_without_analysis_does_not_claim_the_analysis_was_done():
    text='A razão P(n+1)/P(n)=n/(2n-6).'
    assert next(i for i in assess('ITA2025F2Q6',text).items if i.id=='ratio_comparison').points is None


def test_q8_partial_fixture_retains_content_actually_stated_without_sign_analysis():
    text=(ROOT/'problems/ITA2025Q8/examples/missing_sign_analysis.txt').read_text()
    rubric=assess('ITA2025Q8',text)
    assert [(i.id,i.points) for i in rubric.items]==[
        ('numerator_factorization',2.5),('denominator_condition',2),('sign_analysis',None),
        ('longest_interval',2),('endpoint_sum',1.5)]


def test_explicit_final_conclusion_can_follow_a_rejected_attempt_without_losing_later_qualifiers():
    from confia_lean_auditor.rubric.positive_evidence import can_support_rubric_credit
    text='Primeiro tentei a=3 e b=2, mas isso falha. Logo a=-1 e b=3.'
    # Test attribution independently: the unchanged legacy detector may omit a
    # candidate when multiple pairs occur. This gate does not create candidates.
    claim=extract_claims('ITA2025F2Q1','Portanto a=-1 e b=3.').claims[-1]
    assets=validate_problem_assets(ROOT/'problems/ITA2025F2Q1','ITA2025F2Q1')
    def gate(source):
        return can_support_rubric_credit(problem_id='ITA2025F2Q1',item=assets.rubric.items[-1],
            claim=claim,solution_text=source,statement_text=assets.problem.statement)
    assert gate(text)['supported']
    assert not gate(text+' Mas essa resposta está errada.')['supported']


def test_positive_gate_still_blocks_a_legacy_hmer_false_candidate():
    from test_hmer_audit_parity import LATEX
    wrong=LATEX.replace(r'=\frac{1}{2}\\',r'=-\frac{1}{2}\\')
    assert 'beta_difference' not in {c.type for c in extract_claims('ITA2025F2Q3',wrong).claims}
    assert assess('ITA2025F2Q3',wrong).items[0].points is None
    # Preserve the original gate regression even after fixing extraction.
    legacy = extract_claims('ITA2025F2Q3', LATEX)
    assert 'beta_difference' in {c.type for c in legacy.claims}
    item = assess('ITA2025F2Q3', wrong, extraction=legacy).items[0]
    assert item.claim_id and item.points is None
    assert item.positive_evidence['supported'] is False


@pytest.mark.parametrize('pid,tail,criterion',[
    ('ITA2025F2Q1','x^57=1.','power_reductions'),
    ('ITA2025F2Q3','sin beta = (sqrt(7)+1)/4.','candidate_values'),
    ('ITA2025F2Q6','A razão é n/(2n).','ratio_comparison'),
])
def test_ambiguous_component_blocks_composite_credit_and_reference_dependencies(pid,tail,criterion):
    text=(ROOT/'problems'/pid/'examples/correct_solution.txt').read_text()+'\n\n'+tail
    claims=extract_student_claims(pid,text)
    checks=[{**asdict(c),'status':'unverified','compiled':False} for c in claims]
    assert any(c.grounding['status']=='ambiguous' for c in claims)
    rubric=assess(pid,text,checks=checks)
    item=next(i for i in rubric.items if i.id==criterion)
    assert item.points is None and item.mathematical_status=='indeterminate'
    # F2Q1 already suppresses the reference candidate for conflicting powers;
    # other legacy detectors still propose a candidate and need this gate.
    if item.claim_id:
        assert 'ambiguous' in str(item.positive_evidence)
    assert any(i.points is None and any(not d['supported'] for d in
        i.positive_evidence.get('reference_dependencies',[])) for i in rubric.items)


def test_f2q3_existing_strong_certificate_variant_keeps_complete_credit():
    import ast
    tree=ast.parse((ROOT/'tests/test_f2q3_strong_certificate.py').read_text())
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and
                  n.name=='test_f2q3_correct_solution_includes_strong_certificate')
    text=next(n.value for n in ast.walk(function) if isinstance(n,ast.Constant)
              and isinstance(n.value,str) and n.value.startswith('Das equações'))
    assert assess('ITA2025F2Q3',text).score==10


def test_f2q3_explicit_answer_label_keeps_only_final_credit_with_real_engine():
    from fastapi.testclient import TestClient
    from confia_lean_auditor.main import app
    text='Portanto, resposta = (5+sqrt(7))/8.'
    # The answer still requires the asset's existing formal microclaim.
    assert assess('ITA2025F2Q3',text,verified=False).items[-1].points is None
    assert all(i.points is None for i in assess('ITA2025F2Q3','Não podemos concluir: '+text).items)
    response=TestClient(app).post('/audit',json={'problem_id':'ITA2025F2Q3','solution':text})
    assert response.status_code==200,response.text
    data=response.json();items=data['rubric_assessment']['items']
    assert [(i['id'],i['points']) for i in items]==[
        ('beta_difference',None),('candidate_values',None),('final_sin_sum',None),('final_answer',2)]
    evidence=items[-1]['positive_evidence']
    assert evidence['verification_type']=='formal_verification'
    assert all(text[s['source_start']:s['source_end']]==s['source_text'] for s in evidence['source_spans'])
    assert 'generated_strong_f2q3_claim' not in data['lean_certificate']['generated_theorems']
