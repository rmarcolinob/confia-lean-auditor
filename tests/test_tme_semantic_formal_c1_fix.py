"""Targeted bridge regressions: frozen interpretation JSON, never a live pilot."""
import json
from pathlib import Path

import pytest

from test_tme_semantic_formal_c1 import claim, run, provider
from confia_lean_auditor.experimental.tme_semantic_formal.engine import evaluate
from confia_lean_auditor.experimental.tme_semantic_formal.obligation_mapper import SourceDocument
from confia_lean_auditor.experimental.tme_semantic_formal.obligation_registry import REGISTRY
from confia_lean_auditor.experimental.tme_semantic_formal.verification import formal_execution, verification_status
from confia_lean_auditor.tme.obligation_experiment import primary_audit
from scripts.evaluation.run_tme_semantic_formal_c1 import summarize

FIXTURES = Path(__file__).parent/'fixtures/tme_semantic_formal_c1'
SOURCES = {c['case_id']: c for c in json.loads((FIXTURES/'pilot_sources.json').read_text())}
CLAIMS = {c['case_id']: c['evidence'] for c in json.loads((FIXTURES/'fix_replay_claims.json').read_text())}


def replay(case, *, use_lean=False):
    c = SOURCES[case]
    return evaluate(case, c['problem_id'], c['solution_text'], use_lean=use_lean,
                    extraction_provider=provider(CLAIMS[case]))


@pytest.mark.parametrize('case', ['b_complete', 'b_equivalent_algebra', 'p1_complete_regression'])
def test_written_adjacent_chain_recovers_b_without_inferred_endpoints(case):
    r = replay(case)
    b = next(i for i in r['rubric_items'] if i['item_id'] == 'b')
    assert b['points_awarded'] == '5'
    segments = [p for p in r['projection'] if p['derivation'] == 'written_adjacent_equality']
    assert len(segments) == 2 and [p['segment_index'] for p in segments] == [0, 1]
    assert len({p['evidence_id'] for p in segments}) == 1
    parent = next(e for e in r['extracted_evidence'] if e['evidence_id'] == segments[0]['evidence_id'])
    assert parent['normalized_claim'].count('=') == 2
    for p in segments:
        assert p['segment_count'] == 2 and p['attributable'] and p['canonicalized']
        assert r['source_text'][p['original_source_start']:p['original_source_end']] == p['derived_source_span']
        assert p['parent_source_span'] == parent['source_span']
        assert p['derived_expression'].count('=') == 1
    left, middle, right = parent['normalized_claim'].split('=')
    assert [p['derived_expression'] for p in segments] == [left+'='+middle, middle+'='+right]
    assert all(v['status'] == 'DETERMINISTIC_VERIFIED' for v in r['verification_results']
               if v['obligation_id'].startswith('b.'))
    assert sum(c['points'] for c in r['credits'] if c['rubric_item'] == 'b') == 5
    assert all(a['verification_result'] for a in r['awards'] if a['eligible'])
    assert {a['obligation_id'] for a in r['awards']} == set(REGISTRY) and len(REGISTRY) == 21


@pytest.mark.parametrize('normalized', [None, '(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c)'])
def test_incorrect_written_chain_cannot_be_repaired_by_extractor(normalized):
    span = '(100a+10b+c)-(100c+10b+a)=98a-98c=97(a-c)'
    text = '(b)\n'+span
    r = run(text, [claim(text, span, ['b.subtraction', 'b.middle_cancellation', 'b.factorization'],
                         normalized=normalized)])
    assert r['score'] == 0
    assert not any(a['eligible'] for a in r['awards']
                   if a['obligation_id'] in {'b.middle_cancellation', 'b.factorization'})
    if normalized is None:
        assert len(r['projection']) == 2
        assert all(p['derived_expression'] in span for p in r['projection'])
    else:
        assert all(not p['attributable'] for p in r['projection'])


def test_a_complete_formal_suggestion_preserves_deterministic_facts():
    r = replay('a_complete')
    for oid in ['a.identifies_137', 'a.constructs_subtraction']:
        m = next(m for m in r['obligation_mapping'] if m['obligation_id'] == oid)
        assert m['accepted'] and m['suggested_route'] == 'FORMAL'
        assert m['effective_route'] == 'DETERMINISTIC' and m['route_override_reason'] == 'obligation_registry'
        v = next(v for v in r['verification_results'] if v['obligation_id'] == oid)
        assert v['status'] == 'DETERMINISTIC_VERIFIED' and v['source_claim_ids']
    assert not any(v['status'] == 'CONTEXT_REJECTED' for v in r['verification_results'])
    assert r['score'] == 1  # formal result deliberately not executed in this unit test


def test_inverse_role_recovery_preserves_suggestion_trace_and_requires_checker():
    r = replay('a_only_inverse')
    m, = r['obligation_mapping']
    assert m['suggested_obligation_candidates'] == ['a.result_594']
    assert m['obligation_id'] == 'a.identifies_137'
    assert m['mapping_override_reason'] == 'standalone_item_a_inverse_role'
    v, = r['verification_results']
    assert v['status'] == 'DETERMINISTIC_VERIFIED' and v['source_claim_ids']
    assert r['score'] == 1 and not r['formal_awards']


@pytest.mark.parametrize('text,span,normalized', [
    ('(a)\n1137', '1137', '1137'),
    ('(a)\n594', '594', '594'),
    ('(a)\n731-594=137', '731-594=137', '731-594=137'),
    ('(a)\nResultado: 137', 'Resultado: 137', '137'),
    ('(a)\nSuponha que 137', 'Suponha que 137', '137'),
    ('(a)\n137\nTentativa abandonada.', '137', '137'),
    ('(b)\n137', '137', '137'),
])
def test_literal_occurrence_or_another_mathematical_role_does_not_recover_inverse(text, span, normalized):
    r = run(text, [claim(text, span, ['a.result_594'], normalized=normalized)])
    assert not any(m['mapping_override_reason'] for m in r['obligation_mapping'])
    assert not next(a for a in r['awards'] if a['obligation_id'] == 'a.identifies_137')['eligible']
    assert r['score'] == 0


@pytest.mark.parametrize('case', ['a_only_result', 'a_wrong_setup', 'd_later_error', 'd_only_difference_then_error'])
def test_previous_unproved_without_lean_is_not_attempted(case, monkeypatch):
    from confia_lean_auditor.lean import student_claim_checker
    monkeypatch.setattr(student_claim_checker, 'check_one_student_claim',
                        lambda *a, **k: pytest.fail('This representation must not call Lean'))
    r = replay(case, use_lean=True)
    formal = [v for v in r['verification_results'] if v['route'] == 'FORMAL']
    assert len(formal) == 1 and formal[0]['status'] == 'FORMAL_NOT_ATTEMPTED'
    assert not formal[0]['formal_attempted'] and not formal[0]['mathematical_refutation']
    assert not r['technical_uncertainty'] and type(r['score']) is float
    metrics = summarize([r])
    assert metrics['formal_not_attempted'] == 1
    assert metrics['formal_attempts'] == metrics['formal_unproved'] == 0


def test_unproved_requires_execution_evidence_not_just_formal_route():
    for check in [None, {}, {'lean_statement': 'p', 'lean_file': None, 'status': 'unverified'}]:
        assert not formal_execution(check)
        assert verification_status('FORMAL', 'unverified', formal_attempted=formal_execution(check)) == 'FORMAL_NOT_ATTEMPTED'
    assert verification_status('FORMAL', 'unverified', formal_attempted=True) == 'FORMAL_UNPROVED'
    assert verification_status('FORMAL', 'technical_error', formal_attempted=False) == 'FORMAL_ERROR'
    assert formal_execution(dict(lean_statement='p', lean_file='p.lean',
                                 status='technical_error', failure_category='PROCESS_ERROR')) is None


@pytest.mark.parametrize('changes', [{'hypothetical': True}, {'abandoned': True},
                                    {'attributed_to_student': False}, {'scope': 'side_calculation'}])
def test_recovered_inverse_role_does_not_bypass_context(changes):
    text = '(a)\n137'
    r = run(text, [claim(text, '137', ['a.result_594'], **changes)])
    assert r['score'] == 0 and not r['obligation_mapping'][0]['accepted']


@pytest.mark.parametrize('case', list(SOURCES))
def test_current_wrapper_preserves_existing_assessment_for_each_known_source(case):
    c = SOURCES[case]
    bridge, baseline = primary_audit(c['problem_id'], SourceDocument.parse(c['solution_text']).items,
                                    solution_id=case, use_lean=False)
    r = evaluate(case, c['problem_id'], c['solution_text'], mode='tme_current', use_lean=False,
                 extraction_provider=lambda *a: pytest.fail('Current requested LLM'))
    assert r['current_assessment'] == baseline.model_dump(mode='json')
    assert r['current_bridge'] == bridge.model_dump(mode='json')
    assert type(r['score']) is float and 0 <= r['score'] <= 20


def test_numeric_score_without_extractor_credit_for_all_known_p1_sources():
    for case in SOURCES.values():
        r = run(case['solution_text'], [])
        assert r['score'] == 0.0 and not r['credits']
        assert len(r['awards']) == 21 and not any(a['eligible'] for a in r['awards'])
