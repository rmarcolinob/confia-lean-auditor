from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import importlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
from confia_lean_auditor.semantic.semantic_student_claim import (
    CONTRACTS, PROBLEMS, LLM_FIELDS, allowed_contracts, extraction_schema)
from confia_lean_auditor.semantic.semantic_extractor_v2 import (
    parse_response, build_prompt, extract_semantic_claims, SemanticExtractionError)
from confia_lean_auditor.semantic.semantic_claim_adapter import adapt_claim, evidence_bridge, MAPPINGS
from confia_lean_auditor.evaluation.formal_award_gate import formal_award_gate, AWARD_POLICY
from confia_lean_auditor.semantic.evidence_unit import from_semantic_claim
from confia_lean_auditor.evaluation.semantic_formal_b import (
    evaluate_case, evaluate_mode, run_checks, checker_paths)
from confia_lean_auditor.core.problem_assets import validate_problem_assets
from confia_lean_auditor.student_claims.schemas import StudentClaimCheck

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/evaluation'))
import run_ita_semantic_formal_b as runner
from compare_formal_vs_semantic_b import compare

PAYLOADS = {
    'f2q1_student_final_answer': {'a': -1, 'b': 3},
    'f2q1_student_power_reduction': {'exponent': 57, 'const': -1, 'coeff': 0},
    'f2q1_student_reduced_form': {'form_kind': 'correct'},
    'f2q1_student_coefficient_system': {'sum_lhs': 'candidateA + candidateB', 'sum_rhs': 2, 'a_equation_kind': 'neg_a', 'a_rhs': 1},
    'f2q5_student_log_power_decomposition': {'total_log_scaled': 477100, 'integer_part_scaled': 470000, 'mantissa_scaled': 7100},
    'f2q5_student_mantissa': {'mantissa_scaled': 7100},
    'f2q5_student_digit_log_bounds': {'log5_scaled': 6990, 'log6_scaled': 7781},
    'f2q5_student_between_bounds': {'left_scaled': 6990, 'middle_scaled': 7100, 'right_scaled': 7781},
    'f2q5_student_final_digit': {'digit': 5},
    'f2q6_student_probability_formula': {'formula_kind': 'correct'},
    'f2q6_student_ratio_formula': {'ratio_kind': 'correct'},
    'f2q6_student_final_answer': {'values': [6, 7]},
}


def pid(kind):
    return 'ITA2025' + kind.split('_')[0].upper()


def raw(kind='f2q5_student_final_digit', text='O primeiro algarismo é 5.', **changes):
    value = dict(source_span=text, claim_type=kind, normalized_payload=deepcopy(PAYLOADS[kind]),
        assertion_status='asserted', polarity='positive', scope='main_argument', hypothetical=False, abandoned=False)
    value.update(changes)
    return value


def evidence(kind='f2q5_student_final_digit', **changes):
    value = raw(kind, **changes)
    claim = parse_response({'claims': [value]}, pid(kind), value['source_span'], 'fake-model')[0]
    return from_semantic_claim(claim, pid(kind), value['source_span'])


def check(ev, status='verified'):
    return StudentClaimCheck(id=ev.evidence_id, problem_id=pid(ev.claim_type), claim_type=ev.claim_type,
        raw_text=ev.source_span, normalized_text='', lean_statement='test', method='norm_num',
        status=status, compiled=status == 'verified', lean_file=None, stdout='', stderr='', data=deepcopy(ev.normalized_payload))


def assets(problem_id):
    return validate_problem_assets(ROOT / 'problems' / problem_id, problem_id)


@pytest.mark.parametrize('kind', sorted(CONTRACTS))
def test_every_payload_accepted_by_unchanged_builder(kind):
    ev = evidence(kind)
    c = adapt_claim(ev, pid(kind), ev.source_span)
    q = kind.split('_')[0]
    module = importlib.import_module('confia_lean_auditor.lean.student_claim_checkers.ita2025' + q)
    build = getattr(module, '_lean_statement_and_method_for_' + q + '_claim')
    statement, method, error = build(c)
    assert statement and method and not error
    assert c.data == PAYLOADS[kind]
    assert set(allowed_contracts(pid(kind))) == set(MAPPINGS[pid(kind)])


@pytest.mark.parametrize('kind', sorted(CONTRACTS))
def test_payload_extra_fields_cannot_change_points(kind):
    value = raw(kind)
    value['normalized_payload']['points'] = 10
    with pytest.raises(ValueError):
        parse_response({'claims': [value]}, pid(kind), value['source_span'], 'fake')


@pytest.mark.parametrize('bad', [True, '5', 5.0, None])
def test_strict_integer(bad):
    with pytest.raises(ValueError):
        evidence(normalized_payload={'digit': bad})


@pytest.mark.parametrize('status', ['hypothetical', 'negated', 'abandoned', 'quoted_or_problem_text', 'unclear'])
def test_nonasserted_never_awarded(status):
    ev = evidence(assertion_status=status, hypothetical=status == 'hypothetical', abandoned=status == 'abandoned')
    cfg = assets('ITA2025F2Q5').rubric
    extraction = evidence_bridge(ROOT, 'ITA2025F2Q5', [ev], [check(ev)])
    result, decisions = formal_award_gate('ITA2025F2Q5', [ev], [check(ev)], extraction=extraction, rubric_config=cfg)
    assert result.score == 0
    assert decisions[-1]['reason'] == 'context_rejected'


@pytest.mark.parametrize('change', [{'polarity': 'negative'}, {'polarity': 'unclear'},
    {'scope': 'exploration'}, {'scope': 'side_calculation'}, {'hypothetical': True}, {'abandoned': True}])
def test_other_context_exclusions(change):
    assert not evidence(**change).eligible_context()


@pytest.mark.parametrize('span', ['', ' ', 'algarismo 5', 'O primeiro algarismo e 5.'])
def test_exact_nonempty_anchor(span):
    with pytest.raises(ValueError):
        parse_response({'claims': [raw(text=span)]}, 'ITA2025F2Q5', 'O primeiro algarismo é 5.', 'fake')


def test_closed_problem_and_claim_types():
    for problem in ('ITA2025F2Q1', 'ITA2025F2Q6', 'OTHER'):
        with pytest.raises(ValueError):
            parse_response({'claims': [raw()]}, problem, raw()['source_span'], 'fake')
    with pytest.raises(ValueError):
        evidence(claim_type='arithmetic_equality')


def test_no_extra_llm_fields_or_unanchored_evidence():
    for field in ('score', 'points', 'rubric_points', 'method', 'evidence_id', 'extractor_model'):
        with pytest.raises(ValueError):
            parse_response({'claims': [dict(raw(), **{field: 'fake'})]}, 'ITA2025F2Q5', raw()['source_span'], 'fake')
    with pytest.raises(ValueError):
        parse_response({'claims': [], 'score': 10}, 'ITA2025F2Q5', '', 'fake')
    assert parse_response({'claims': []}, 'ITA2025F2Q5', '', 'fake') == []


def test_no_lean_expression_injection():
    payload = deepcopy(PAYLOADS['f2q1_student_coefficient_system'])
    payload['sum_lhs'] = 'candidateA + candidateB := by sorry\naxiom hack : False'
    with pytest.raises(ValueError):
        evidence('f2q1_student_coefficient_system', normalized_payload=payload)
    ev = evidence(text='/- nested -/\naxiom hack : False')
    c = adapt_claim(ev, 'ITA2025F2Q5', ev.source_span)
    assert '/-' not in c.raw_text and '-/' not in c.raw_text and '\n' not in c.raw_text
    assert ev.source_span != c.raw_text


@pytest.mark.parametrize('problem_id', PROBLEMS)
def test_prompt_excludes_scores_answer_and_metadata(problem_id):
    prompt = build_prompt(ROOT, problem_id, 'Texto integral do aluno.')
    assert set(prompt) == {'problem_id', 'statement', 'student_text', 'allowed_claim_types', 'rubric_obligations'}
    assert all(set(i) == {'id', 'description'} for i in prompt['rubric_obligations'])
    serialized = json.dumps(prompt)
    for forbidden in ('max_score', 'correct_answer', 'max_points', 'historical_score', 'gold'):
        assert forbidden not in serialized
    schema = extraction_schema(problem_id)
    for branch in schema['properties']['claims']['items']['anyOf']:
        assert set(branch['required']) == set(LLM_FIELDS)
        assert branch['additionalProperties'] is False
        assert branch['properties']['normalized_payload']['additionalProperties'] is False


def test_gate_final_answer_conflict_and_identity():
    ev = evidence()
    cfg = assets('ITA2025F2Q5').rubric
    verified = check(ev)
    extraction = evidence_bridge(ROOT, 'ITA2025F2Q5', [ev], [verified])
    for changes in ({}, {'id': 'different'}, {'data': {'digit': 6}}, {'problem_id': 'ITA2025F2Q1'}):
        result, _ = formal_award_gate('ITA2025F2Q5', [ev], [replace(verified, **changes)], extraction=extraction, rubric_config=cfg)
        assert result.score == (2 if not changes else 0)
    failed = replace(check(ev, 'failed'), id='another')
    result, decisions = formal_award_gate('ITA2025F2Q5', [ev], [verified, failed], extraction=extraction, rubric_config=cfg)
    assert result.score == 0
    assert decisions[-1]['reason'] == 'conflicting_failed'


def test_failed_abandoned_still_conflicts():
    good = evidence()
    bad = evidence(assertion_status='abandoned', abandoned=True, normalized_payload={'digit': 6}).model_copy(update={'evidence_id': 'bad'})
    extraction = evidence_bridge(ROOT, 'ITA2025F2Q5', [good, bad], [check(good), check(bad, 'failed')])
    assert not extraction.claims


def test_partial_power_no_longer_receives_replay_promotion():
    ev = evidence('f2q1_student_power_reduction').model_copy(update={
        'extractor_mode': 'FORMAL_OFFLINE', 'context_policy': 'legacy_context_assumed'})
    cfg = assets('ITA2025F2Q1').rubric
    extraction = evidence_bridge(ROOT, 'ITA2025F2Q1', [ev], [check(ev)])
    result, decisions = formal_award_gate('ITA2025F2Q1', [ev], [check(ev)],
        extraction=extraction, rubric_config=cfg)
    assert result.score == 0
    assert decisions[0]['rejection_reason'] == 'formal_obligation_not_satisfied'


def test_semantic_needs_all_power_reductions_and_microclaims():
    ev = evidence('f2q1_student_power_reduction')
    extraction = evidence_bridge(ROOT, 'ITA2025F2Q1', [ev], [check(ev)])
    assert not extraction.claims
    values = [(57, -1, 0), (14, -1, 1), (7, 0, 1)]
    evs = [evidence('f2q1_student_power_reduction', normalized_payload=dict(exponent=e, const=c, coeff=k)).model_copy(update={'evidence_id': str(e)}) for e,c,k in values]
    checks = [check(e) for e in evs]
    extraction = evidence_bridge(ROOT, 'ITA2025F2Q1', evs, checks)
    assert [c.type for c in extraction.claims] == ['power_reductions']
    cfg = assets('ITA2025F2Q1').rubric
    result, decisions = formal_award_gate('ITA2025F2Q1', evs, checks, extraction=extraction, rubric_config=cfg)
    assert result.score == 0
    assert decisions[0]['reason'] == 'formal_obligation_not_satisfied'


def test_ratio_alone_does_not_create_maximizer_evidence():
    ev = evidence('f2q6_student_ratio_formula')
    extraction = evidence_bridge(ROOT, 'ITA2025F2Q6', [ev], [check(ev)])
    assert {c.type for c in extraction.claims} == {'ratio_comparison'}


def test_api_request_usage_reasoning_and_schema_failure():
    captured = {}
    def create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(status='completed', id='r1', model='fake',
            usage=SimpleNamespace(model_dump=lambda **kw: {'input_tokens': 10, 'output_tokens': 20}),
            output_text=json.dumps({'claims': [raw()]}))
    client = SimpleNamespace(responses=SimpleNamespace(create=create))
    claims, meta = extract_semantic_claims(ROOT, 'ITA2025F2Q5', raw()['source_span'], 'fake', 'low', client)
    assert claims and meta['token_usage']['input_tokens'] == 10
    assert captured['reasoning'] == {'effort': 'low'}
    assert captured['text']['format']['strict'] is True
    with pytest.raises(SemanticExtractionError) as exc:
        extract_semantic_claims(ROOT, 'ITA2025F2Q5', 'No matching evidence', 'fake', client=client)
    assert exc.value.metadata['api_status'] == 'schema_error'


@pytest.mark.parametrize('failure', ['api', 'schema', 'unexpected'])
def test_fallback_exact_numeric_offline_score(tmp_path, failure):
    def extractor(*args):
        if failure == 'unexpected':
            raise ValueError('bad output')
        raise SemanticExtractionError(failure + '_error', {'api_status': failure + '_error'})
    calls = []
    def evaluator(root, output, problem, text, mode, evidence):
        calls.append(mode)
        return {'score': 4.0, 'rubric_items': [], 'student_claim_checks': [], 'technical_errors': []}
    case = {'solution_id': 'synthetic', 'problem_id': 'ITA2025F2Q5', 'text': 'anything'}
    semantic = evaluate_case(ROOT, tmp_path, case, 'semantic_formal', 'fake', extractor=extractor, evaluator=evaluator)
    offline = evaluate_case(ROOT, tmp_path, case, 'formal_offline', 'fake', extractor=extractor, evaluator=evaluator)
    assert semantic['score'] == offline['score'] == 4.0
    assert semantic['fallback_used'] and semantic['fallback_reason']
    assert semantic['mode_effective'] == 'FORMAL_OFFLINE'
    assert calls == ['FORMAL_OFFLINE', 'FORMAL_OFFLINE']


def test_empty_success_does_not_fallback(tmp_path):
    row = evaluate_case(ROOT, tmp_path, {'solution_id': 'synthetic', 'problem_id': 'ITA2025F2Q5', 'text': ''},
        'semantic_formal', 'fake', extractor=lambda *args: ([], {'api_status': 'success'}),
        evaluator=lambda *args: {'score': 0.0})
    assert row['score'] == 0 and not row['fallback_used'] and row['mode_effective'] == 'SEMANTIC_FORMAL'


def test_technical_lean_exception_numeric_and_paths_restored(tmp_path, monkeypatch):
    module = importlib.import_module('confia_lean_auditor.evaluation.semantic_formal_b')
    def fail(*a, **k):
        raise FileNotFoundError('lake unavailable')
    monkeypatch.setattr(module, 'check_student_claims_for_problem', fail)
    monkeypatch.setattr(module, 'run_formal_chain', fail)
    specific = importlib.import_module('confia_lean_auditor.lean.student_claim_checkers.ita2025f2q5')
    old = specific.CHECK_DIR
    result = evaluate_mode(ROOT, tmp_path / 'run', 'ITA2025F2Q5', 'O primeiro algarismo é 5.', 'FORMAL_OFFLINE')
    assert result['score'] == 0.0 and result['lean_status'] == 'technical_error'
    assert result['technical_errors']
    assert specific.CHECK_DIR == old
    with pytest.raises(FileExistsError):
        evaluate_mode(ROOT, tmp_path / 'run', 'ITA2025F2Q5', '', 'FORMAL_OFFLINE')


def test_gold_access_denied_before_open_and_extra_dataset_columns(tmp_path, monkeypatch):
    forbidden = tmp_path / 'notas_referencia_v2.0.csv'
    original = Path.open
    def watched(path, *args, **kwargs):
        assert path != forbidden, 'Gold was opened'
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', watched)
    with pytest.raises(ValueError, match='Gold'):
        runner.load_dataset(forbidden)
    allowed = tmp_path / 'solutions.csv'
    allowed.write_text('id,qid,texto,score\na,ITA2025F2Q5,text,10\n')
    with pytest.raises(ValueError, match='schema'):
        runner.load_dataset(allowed)


def test_gold_guard_blocks_indirect_open_in_subprocess(tmp_path):
    script = f"""import sys
sys.path.insert(0, {str(ROOT / 'scripts/evaluation')!r})
from run_ita_semantic_formal_b import install_guards
install_guards(True)
try:
    open({str(tmp_path / 'notas_referencia_v2.0.csv')!r})
except PermissionError:
    print('blocked')
else:
    raise AssertionError('unblocked')
"""
    proc = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == 'blocked'


def test_frozen_pilot_uniform_unique_and_hashes():
    population = json.loads((runner.FIXTURES / 'population_b.json').read_text())['cases']
    ids = json.loads((runner.FIXTURES / 'pilot18_ids.json').read_text())
    assert ids == runner.uniform_pilot(population)
    assert len(ids) == len(set(ids)) == 18
    for p in PROBLEMS:
        assert sum(s.startswith(p + '_') for s in ids) == 6
    assert len(population) == 252


def test_select_cases_hash_validation_and_no_score_fields():
    case = dict(solution_id='x', problem_id='ITA2025F2Q5', text='text')
    pop = [dict(solution_id='x', problem_id='ITA2025F2Q5', source_sha256=runner.digest(b'text'))]
    assert runner.select_cases([case], pop) == [case]
    with pytest.raises(ValueError):
        runner.select_cases([dict(case, text='changed')], pop)
    with pytest.raises(ValueError):
        runner.select_cases([case], pop, ids=['x', 'x'])


def test_compare_paired_and_fallback_excluded():
    a = dict(solution_id='x', problem_id='ITA2025F2Q5', score=4.,
        source_sha256='hash', historical_base_sha='base', experimental_file_sha256={'x': 'hash'},
        lean_status='verified', rubric_items=[], award_policy=AWARD_POLICY)
    b = dict(a, fallback_used=True, mode_effective='FORMAL_OFFLINE')
    key = ('ITA2025F2Q5', 'x')
    result = compare({key: a}, {key: b})
    assert result['all_cases']['mean_delta'] == 0
    assert result['semantic_success_without_technical_errors']['cases'] == 0
    with pytest.raises(ValueError):
        compare({key: a}, {key: dict(b, score=5.)})
    with pytest.raises(ValueError):
        compare({key: a}, {})


@pytest.mark.parametrize('mode', ['formal_offline', 'semantic_formal'])
def test_unexpected_engine_error_still_numeric(tmp_path, mode):
    def evaluator(*args):
        raise OSError('synthetic failure')
    row = evaluate_case(ROOT, tmp_path, {'solution_id': 'synthetic', 'problem_id': 'ITA2025F2Q5', 'text': ''},
        mode, 'fake', extractor=lambda *a: ([], {'api_status':'success'}), evaluator=evaluator)
    assert row['score'] == 0.0 and row['lean_status'] == 'technical_error'
    assert row['technical_errors'] and len(row['formal_award_decisions']) == 5
    assert row['fallback_used'] == (mode == 'semantic_formal')


def test_timeout_bytes_are_serializable(tmp_path, monkeypatch):
    module = importlib.import_module('confia_lean_auditor.evaluation.semantic_formal_b')
    ev = evidence()
    timeout = replace(check(ev, 'error'), stdout=b'partial stdout', stderr='timeout after 90s')
    monkeypatch.setattr(module, 'check_student_claims_for_problem', lambda *a: [timeout])
    result = run_checks(ROOT, tmp_path, 'ITA2025F2Q5', [adapt_claim(ev, 'ITA2025F2Q5', ev.source_span)])
    assert result[0].stdout == 'partial stdout'


def test_all_closed_enum_variants_are_supported_by_historical_checker():
    from confia_lean_auditor.semantic.semantic_student_claim import validate_payload
    for kind, contract in CONTRACTS.items():
        for field, spec in contract['payload_schema']['properties'].items():
            for value in spec.get('enum', []):
                payload = deepcopy(PAYLOADS[kind])
                payload[field] = value
                validate_payload(kind, payload, pid(kind))
                ev = evidence(kind, normalized_payload=payload)
                q = kind.split('_')[0]
                module = importlib.import_module('confia_lean_auditor.lean.student_claim_checkers.ita2025' + q)
                statement, method, error = getattr(module, '_lean_statement_and_method_for_' + q + '_claim')(adapt_claim(ev,pid(kind),ev.source_span))
                assert statement and method and not error


def test_runner_cli_persists_both_modes_without_api_or_real_dataset(tmp_path, monkeypatch):
    module = importlib.import_module('confia_lean_auditor.evaluation.semantic_formal_b')
    fixture = tmp_path / 'fixtures'
    fixture.mkdir()
    (fixture / 'population_b.json').write_text(json.dumps({'cases':[{
        'solution_id':'synthetic', 'problem_id':'ITA2025F2Q5', 'source_sha256':runner.digest(b'text')}]}))
    dataset = tmp_path / 'solutions.csv'
    dataset.write_text('id,qid,texto\nsynthetic,ITA2025F2Q5,text\n')
    monkeypatch.setattr(runner,'FIXTURES',fixture)
    monkeypatch.setattr(runner,'install_guards',lambda offline: None)
    monkeypatch.setattr(runner,'provenance',lambda: {'code_sha':'test-sha', 'experimental_file_sha256':{'synthetic':'hash'}})
    monkeypatch.setattr(runner,'prepare_runtime',lambda output,cache: ROOT)
    def fake(root, output, case, mode, model, reasoning):
        return dict(solution_id=case['solution_id'],problem_id=case['problem_id'],
            mode_requested=mode.upper(),mode_effective=mode.upper(),score=2.0,
            rubric_items=[{'id':'final_digit','points':2}],extracted_evidence=[],
            student_claim_checks=[],formal_award_decisions=[],lean_status='verified',
            api_status='not_called' if mode=='formal_offline' else 'mock_success',
            fallback_used=False,latency_seconds=0.1,token_usage=None,cost=None,
            technical_errors=[],model_configuration={'model':model,'reasoning_effort':reasoning})
    monkeypatch.setattr(module,'evaluate_case',fake)
    for mode in ('formal_offline','semantic_formal'):
        output=tmp_path/mode
        assert runner.main(['--dataset',str(dataset),'--mode',mode,'--output-dir',str(output),'--model','fake'])==0
        result=json.loads((output/'results.jsonl').read_text())
        summary=json.loads((output/'summary.json').read_text())
        assert result['score']==2.0 and summary['numeric_scores']==1
        assert result['code_sha']=='test-sha' and result['source_sha256']==runner.digest(b'text')
        assert (output/'cases/0000/result.json').exists()
    with pytest.raises(FileExistsError):
        runner.main(['--dataset',str(dataset),'--mode','formal_offline','--output-dir',str(tmp_path/'formal_offline')])


def test_bridge_uses_historical_method_and_aggregates_shared_steps():
    evs = [evidence(k).model_copy(update={'evidence_id': k}) for k in PAYLOADS if k.startswith('f2q5')]
    extraction = evidence_bridge(ROOT,'ITA2025F2Q5',evs,[check(e) for e in evs])
    shared = {s.type:s for s in extraction.formal_steps}['f2q5_digit_bounds']
    assert set(shared.supports_rubric_items) == {'digit_log_bounds','mantissa_between_bounds','final_digit'}
    ratio = evidence('f2q6_student_ratio_formula')
    extraction = evidence_bridge(ROOT,'ITA2025F2Q6',[ratio],[check(ratio)])
    assert extraction.formal_steps[0].lean_method == 'omega'
    from confia_lean_auditor.lean.formal_step_evaluator import render_formal_step
    step = extraction.formal_steps[0]
    assert render_formal_step('ITA2025F2Q6',step) == render_formal_step('ITA2025F2Q6',step.model_copy(update={'lean_method':'norm_num'}))
