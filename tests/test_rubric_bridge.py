"""Student evidence must cross alignment, grounding and the existing P0 gate."""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import json

import pytest

from confia_lean_auditor.claims.common.rubric_bridge import RubricClaimContext
from confia_lean_auditor.claims.common.catalog import build_claim_catalog
from confia_lean_auditor.claims.extract_claims import extract_claims
from confia_lean_auditor.core.problem_assets import validate_problem_assets
from confia_lean_auditor.core.schemas import AuditResponse, MicroclaimResult
from confia_lean_auditor.rubric.rubric_evaluator import evaluate_rubric
from confia_lean_auditor.rubric.positive_evidence import can_support_rubric_credit
from confia_lean_auditor.rubric.adjusters.registry import apply_student_claim_adjustments
from confia_lean_auditor.student_claims.registry import extract_student_claims
from test_positive_credit_evidence import verified_check

ROOT = Path(__file__).resolve().parents[1]
PID = 'ITA2025F2Q1'
TEXT = 'Logo a vale -1 e b vale 3.'


def setup_case(pid=PID, text=TEXT, *, checks=(), students=None, rubric_config=None):
    assets = validate_problem_assets(ROOT/'problems'/pid, pid)
    extraction = extract_claims(pid, text)
    students = extract_student_claims(pid, text) if students is None else students
    config = rubric_config or assets.rubric
    context = RubricClaimContext(problem_id=pid, solution_text=text, extraction=extraction,
        students=students, checks=checks, rubric_config=config,
        statement_text=assets.problem.statement, correct_answer=assets.problem.correct_answer)
    return assets, extraction, students, context


def assess_setup(setup, *, microclaims=()):
    assets, extraction, students, context = setup
    return evaluate_rubric(ROOT, context.problem_id, extraction, list(microclaims), assets.rubric,
        solution_text=context.solution_text, student_claim_checks=context.checks,
        statement_text=context.statement_text, claim_context=context)


@pytest.mark.parametrize('text', [TEXT, 'a vale -1 e b vale 3', 'Resposta: a=-1 e b=3.'])
def test_grounded_aligned_lean_verified_supports_atomic_criterion(text):
    check = asdict(verified_check(PID, text, 'f2q1_student_final_answer'))
    setup = setup_case(text=text, checks=[check])
    result = assess_setup(setup)
    final = result.items[-1]
    assert final.points == 2 and final.mathematical_status == 'supported'
    evidence = final.positive_evidence['student_bridge']
    assert evidence['verification_basis'] == 'formal_lean_verified'
    assert evidence['alignment_basis'] == 'structured_values'
    assert evidence['student_check_ids'] == [check['id']]
    assert all(i.points is None for i in result.items[:-1])
    assert final.claim_id is None if 'vale' in text else final.claim_id is not None
    for span in evidence['source_spans']:
        assert text[span['source_start']:span['source_end']] == span['source_text']
    assert evidence['expected_claim_id'] != evidence['student_claim_ids'][0]


def test_canonical_alignment_and_deterministic_verification_without_student_lean():
    pid = 'ITA2025F2Q3'
    text = 'Assim, cos beta = sen beta + 1/2.'
    setup = setup_case(pid, text)
    assets = setup[0]
    micro = [MicroclaimResult(id=m.id, description=m.description, textual_evidence=True,
        claim_types=m.claim_types, depends_on_microclaim_ids=m.depends_on_microclaim_ids,
        lean_status='verified_by_lean') for m in assets.microclaims.microclaims]
    item = assess_setup(setup, microclaims=micro).items[0]
    assert item.id == 'beta_difference' and item.points == 2
    evidence = item.positive_evidence['student_bridge']
    assert evidence['alignment_basis'] == 'canonical_equivalence'
    assert evidence['verification_basis'] == 'deterministic_expected_relation'
    assert evidence['student_check_ids'] == []
    # Reference microclaims remain necessary even for the aligned student.
    assert assess_setup(setup).items[0].points is None


@pytest.mark.parametrize('required,dependencies', [(['missing'], []),
    ([], [{'supported': False, 'microclaim_id': 'unattributed'}])])
def test_complete_student_proof_cannot_replace_other_obligations(required, dependencies):
    check = asdict(verified_check(PID, TEXT, 'f2q1_student_final_answer'))
    assets, _, _, context = setup_case(checks=[check])
    item = assets.rubric.items[-1].model_copy(update={'required_microclaim_ids': required})
    e = can_support_rubric_credit(problem_id=PID, item=item, claim=None, solution_text=TEXT,
        statement_text=assets.problem.statement, claim_context=context,
        reference_dependencies=dependencies)
    assert not e['supported'] and not e['student_bridge']['supported']


def test_reference_lean_only_without_student_grounding_cannot_use_bridge():
    assets, extraction, _, context = setup_case(students=[])
    assert not extraction.claims  # no reference regex for this conclusion wording
    result = assess_setup((assets, extraction, [], context), microclaims=[
        MicroclaimResult(id=m.id, description=m.description, textual_evidence=True,
            claim_types=m.claim_types, lean_status='verified_by_lean')
        for m in assets.microclaims.microclaims])
    assert all(i.points is None for i in result.items)


@pytest.mark.parametrize('variant', ['unresolved', 'ambiguous', 'wrong_value', 'duplicate', 'quoted'])
def test_unmatched_ambiguous_conflicting_or_unattributable_student_never_gains_credit(variant):
    text = TEXT
    students = extract_student_claims(PID, text)
    if variant in {'unresolved', 'ambiguous'}:
        students = [replace(students[0], grounding={'status': variant})]
    elif variant == 'wrong_value':
        text = 'Logo a vale 3 e b vale 2.'
        students = extract_student_claims(PID, text)
    elif variant == 'duplicate':
        students = students * 2
    else:
        text = '“' + text + '”'
        students = extract_student_claims(PID, text)
    setup = setup_case(text=text, students=students)
    assert assess_setup(setup).items[-1].points is None


def test_grounded_positive_and_refuted_claims_preserve_conflict_and_negative_precedence():
    import hashlib
    fragments = ['Assim, cos beta - sen beta = 1/2.', 'Assim, cos beta - sen beta = -1/2.']
    text = '\n\n'.join(fragments)
    pid = 'ITA2025F2Q3'
    # Replay/import can contain independently bound contradictory assertions.
    # Preserve each literal span and full-source digest; no grounder is mocked.
    students = []
    for index, fragment in enumerate(fragments):
        c = next(c for c in extract_student_claims(pid, fragment)
                 if c.claim_type == 'f2q3_student_beta_difference')
        offset = text.index(fragment)
        c = replace(c, id='independent_' + str(index), grounding={**c.grounding,
            'source_start': c.grounding['source_start'] + offset,
            'source_end': c.grounding['source_end'] + offset,
            'source_sha256': hashlib.sha256(text.encode()).hexdigest()})
        students.append(c)
    checks = []
    for index, c in enumerate(students):
        check = asdict(verified_check(pid, fragments[index], c.claim_type))
        check.update(id=c.id, data=c.data, grounding=c.grounding, raw_text=c.raw_text,
                     status='verified' if index == 0 else 'refuted',
                     formal_status='verified' if index == 0 else 'refuted',
                     refutation_verified=index == 1, refutation_lean_file='controlled_negation.lean')
        checks.append(check)
    setup = setup_case(pid, text, checks=checks, students=students)
    result = assess_setup(setup)
    assert result.items[0].points is None and result.items[0].positive_evidence['conflict']
    result = apply_student_claim_adjustments(rubric=result, problem_id=pid, student_claim_checks=checks)
    assert result.items[0].points == 0 and result.items[0].mathematical_status == 'refuted'
    assert result.items[0].positive_evidence['conflict']


@pytest.mark.parametrize('field,value', [('id', 'other'), ('problem_id', 'ITA2025F2Q3'),
    ('claim_type', 'f2q1_student_coefficient_system'), ('data', {'a': 3, 'b': 2}),
    ('compiled', False), ('verification_scope', 'generated_reference')])
def test_wrong_check_never_becomes_student_formal_evidence(field, value):
    check = asdict(verified_check(PID, TEXT, 'f2q1_student_final_answer'))
    check[field] = value
    result = assess_setup(setup_case(checks=[check]))
    evidence = result.items[-1].positive_evidence['student_bridge']
    # The independent exact-answer verifier is still legitimate, but this check
    # must never be credited as Lean verification for that student record.
    assert evidence['verification_basis'] == 'deterministic_expected_value'
    assert evidence['student_check_ids'] == []


def test_verified_final_answer_cannot_be_linked_to_the_wrong_criterion():
    assets, _, _, context = setup_case(checks=[asdict(verified_check(PID, TEXT, 'f2q1_student_final_answer'))])
    wrong = assets.rubric.items[0].model_copy(update={'claim_type': 'final_answer'})
    evidence = can_support_rubric_credit(problem_id=PID, item=wrong, claim=None, solution_text=TEXT,
        statement_text=assets.problem.statement, claim_context=context)
    assert not evidence['supported']


def test_expected_answer_is_not_inferred_from_description_or_student_value():
    assets, extraction, students, _ = setup_case()
    context = RubricClaimContext(problem_id=PID, solution_text=TEXT, extraction=extraction,
        students=students, checks=(), rubric_config=assets.rubric,
        statement_text=assets.problem.statement, correct_answer='An unspecified pair')
    assert context.expected == {}


def test_catalog_reuses_runtime_alignment_and_keeps_ids_and_provenances():
    setup = setup_case(checks=[asdict(verified_check(PID, TEXT, 'f2q1_student_final_answer'))])
    assets, extraction, students, context = setup
    rubric = assess_setup(setup)
    expected = context.expected['final_answer']
    alignment = context.alignment(expected)
    catalog = build_claim_catalog(problem_id=PID, solution_text=TEXT, extraction=extraction,
        students=students, checks=context.checks, rubric_config=assets.rubric, rubric=rubric,
        statement_text=assets.problem.statement, claim_context=context)
    assert context.alignment(expected) is alignment
    assert expected in catalog.records and not expected.source.attributable
    trace = next(t for t in catalog.criterion_traces if t.criterion_id == 'final_answer')
    assert trace.reference_record_id == expected.record_id
    assert trace.student_record_ids == ('student:' + students[0].id,)


def test_saved_f2q1_v2_proof_replay_recovers_only_the_final_criterion():
    source = ROOT/'artifacts/evaluations/ita1000_v1_2/smoke_v2_20261029T040221Z'
    path = source/'results/ITA2025F2Q1_S001_L04.json'
    if not path.exists():
        pytest.skip('Local V2 artifact; equivalent portable regression is tested above')
    before = path.read_bytes()
    d = AuditResponse.model_validate_json(before)
    text = (source/'cases/ITA2025F2Q1_S001_L04/solution.txt').read_text()
    setup = setup_case(text=text, checks=d.student_claim_checks)
    result = assess_setup(setup, microclaims=d.microclaims)
    assert result.items[-1].points == 2
    assert all(i.points is None for i in result.items[:-1])
    assert result.items[-1].positive_evidence['student_bridge']['verification_basis'] == 'formal_lean_verified'
    assert path.read_bytes() == before
