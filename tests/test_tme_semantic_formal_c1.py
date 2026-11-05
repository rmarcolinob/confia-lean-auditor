"""C1 boundaries and scoring contracts; injected interpreters never grant proof."""
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from confia_lean_auditor.experimental.tme_semantic_formal.evidence_unit import bind_evidence
from confia_lean_auditor.experimental.tme_semantic_formal.obligation_registry import REGISTRY, FORMAL_OBLIGATIONS
from confia_lean_auditor.experimental.tme_semantic_formal.obligation_mapper import SourceDocument, ObligationMapper
from confia_lean_auditor.experimental.tme_semantic_formal.claim_router import ClaimRouter
from confia_lean_auditor.experimental.tme_semantic_formal.semantic_extractor import SemanticExtractorTME, transport
from confia_lean_auditor.experimental.tme_semantic_formal.engine import evaluate
from confia_lean_auditor.experimental.tme_semantic_formal.score_closure import ScoreClosurePolicy
from confia_lean_auditor.experimental.tme_semantic_formal.reconciliation import resolve_conflict
from confia_lean_auditor.experimental.tme_semantic_formal.verification import verification_status
from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.student_claims.semantic_sufficiency import SufficiencyDecision
from confia_lean_auditor.student_claims.hybrid_semantic import config_for
from confia_lean_auditor.rubric.pauta.engine import PautaEngine
from confia_lean_auditor.rubric.pauta.models import ObligationEvidence, PautaEvidence
from confia_lean_auditor.tme.obligation_experiment import primary_audit
from scripts.evaluation.run_tme_semantic_formal_c1 import load_inputs, summarize, main

ROOT = Path(__file__).resolve().parents[1]
BASE = '1b3daea41ba4ce31c0cfd35dd07907da3d03669f'


def claim(text, span, obligations, *, normalized=None, kind='expression', **changes):
    units = [u for u in evidence_units(text) if u.exact_text == span]
    assert len(units) == 1
    value = dict(source_evidence_ids=[units[0].evidence_id], source_span=span,
        normalized_claim=normalized or span, claim_type=kind, assertion_status='asserted',
        polarity='positive', scope='main_argument', hypothetical=False, abandoned=False,
        attributed_to_student=True, rubric_candidates=list(dict.fromkeys(o[0] for o in obligations)),
        obligation_candidates=obligations, verification_route_candidate='DETERMINISTIC')
    value.update(changes)
    return value


def provider(claims):
    return lambda *args: (json.dumps(dict(evidence=claims), ensure_ascii=False),
                          dict(status='completed', model='offline-contract', api_calls=0))


def run(text, claims, *, use_lean=False, **kwargs):
    return evaluate('contract', 'TME2026P1', text, extraction_provider=provider(claims), use_lean=use_lean, **kwargs)


def fake_checker(monkeypatch, status):
    """Proof-result contract only. The separate real-Lean test has no patches."""
    from confia_lean_auditor.lean import student_claim_checker
    from confia_lean_auditor.student_claims.schemas import StudentClaimCheck
    def check(c, run_id, index):
        return StudentClaimCheck(id=c.id, problem_id=c.problem_id, claim_type=c.claim_type,
            raw_text=c.raw_text, normalized_text=c.normalized_text, lean_statement='contract mock',
            method='norm_num', status=status, compiled=status == 'verified', lean_file='contract-proof.lean',
            stdout='', stderr='', data=c.data, grounding=c.grounding,
            formal_status=status if status in {'verified', 'refuted'} else None,
            refutation_verified=status == 'refuted', refutation_lean_file='contract-negation.lean' if status == 'refuted' else None)
    monkeypatch.setattr(student_claim_checker, 'check_one_student_claim', check)


def gate(state='sufficient'):
    def call(payload):
        return tuple(SufficiencyDecision(obligation_id=o['obligation_id'], sufficiency=state,
            evidence_ids=[e['evidence_id'] for e in o['selected_evidence']],
            reason_code={'sufficient': 'adequate_evidence', 'insufficient': 'missing_step',
                         'contradictory': 'contradictory_mathematics'}[state], concise_rationale='Offline contract.')
            for o in payload['obligations']), dict(status='completed', api_calls=0)
    return call


def test_literal_span_and_local_identity_unicode():
    text = '(a)\n731−137=594'
    c = claim(text, '731−137=594', ['a.result_594'])
    e, = bind_evidence(json.dumps({'evidence': [c]}), text, 'fixture')
    assert text[e.source_start:e.source_end] == e.source_span
    assert e.evidence_id.startswith('E002:claim:')
    c['source_span'] = '731−137=584'
    with pytest.raises(ValueError, match='source_span'):
        bind_evidence(json.dumps({'evidence': [c]}), text, 'fixture')


@pytest.mark.parametrize('field', ['score', 'points', 'award', 'formal_status', 'verification_status', 'source_start', 'extractor_metadata'])
def test_llm_cannot_supply_authority_or_local_coordinates(field):
    text = '(a)\n137'; c = claim(text, '137', ['a.identifies_137']); c[field] = 20
    with pytest.raises(ValidationError):
        bind_evidence(json.dumps({'evidence': [c]}), text, 'fixture')


def test_foreign_obligation_and_source_id_are_rejected():
    text = '(a)\n137'; c = claim(text, '137', ['a.invented'])
    with pytest.raises(ValueError, match='obligation'):
        bind_evidence(json.dumps({'evidence': [c]}), text, 'fixture')
    c = claim(text, '137', ['a.identifies_137']); c['source_evidence_ids'] = ['E999']
    with pytest.raises(ValueError, match='source_evidence_id'):
        bind_evidence(json.dumps({'evidence': [c]}), text, 'fixture')


def test_extractor_payload_is_allowlisted_without_grading_or_official_solution():
    ex = SemanticExtractorTME(); p = ex.payload('TME2026P1', '(a)\n137')
    assert len(p['obligations']) == 21
    assert set(p) == {'problem_id', 'statement', 'full_student_solution', 'supported_claim_types',
                      'obligations', 'verifier_payload_schemas', 'evidence_units'}
    wire = json.dumps(p)
    for forbidden in ('max_points', 'max_score', 'official_reference', 'expected_points', 'gold', 'current_assessment'):
        assert forbidden not in wire
    assert ex.schema('(a)\n137')['additionalProperties'] is False


@pytest.mark.parametrize('oid', list(REGISTRY))
def test_all_21_routes_closed_and_only_two_formal(oid):
    spec = REGISTRY[oid]
    assert spec.checker and spec.sufficiency_policy and spec.rubric_item == oid[0]
    assert ('FORMAL' in spec.allowed_routes) == (oid in FORMAL_OBLIGATIONS)
    text = f'({oid[0]})\n137'
    c = claim(text, '137', [oid], kind=spec.allowed_claim_types[0], verification_route_candidate='FORMAL')
    e, = bind_evidence(json.dumps({'evidence': [c]}), text, 'fixture')
    if oid in FORMAL_OBLIGATIONS:
        assert ClaimRouter().route(e, oid) == 'FORMAL'
    else:
        assert ClaimRouter().route(e, oid) == 'DETERMINISTIC'


def test_suggestion_cannot_downgrade_formal_or_claim_unrelated_obligation():
    text = '(a)\n731-137=594'
    c = claim(text, '731-137=594', ['a.result_594'], verification_route_candidate='SEMANTIC')
    r = run(text, [c])
    assert r['verification_results'][0]['status'] == 'FORMAL_NOT_ATTEMPTED'
    assert r['verification_results'][0]['route'] == 'FORMAL'
    text = '(b)\n99(a-c)'
    r = run(text, [claim(text, '99(a-c)', ['b.factorization'])])
    assert r['score'] == 0  # a correct expression is not a written factorization


@pytest.mark.parametrize('changes', [
    {'hypothetical': True}, {'assertion_status': 'hypothetical'},
    {'assertion_status': 'negated'}, {'polarity': 'negative'},
    {'abandoned': True}, {'assertion_status': 'abandoned'},
    {'attributed_to_student': False}, {'assertion_status': 'quoted'},
    {'scope': 'exploration'}, {'scope': 'side_calculation'}, {'scope': 'unknown'}])
def test_context_never_scores(changes):
    text = '(a)\n137'
    r = run(text, [claim(text, '137', ['a.identifies_137'], **changes)])
    assert r['score'] == 0
    assert r['verification_results'][0]['status'] == 'CONTEXT_REJECTED'


@pytest.mark.parametrize('prefix', ['Suponha que ', 'Não é verdade que ', 'Tentativa descartada: ', 'João disse que '])
def test_hostile_asserted_context_fails_independent_gate(prefix):
    span = prefix + '731-137=594'; text = '(a)\n' + span
    r = run(text, [claim(text, span, ['a.identifies_137'], normalized='731-137=594')])
    assert r['score'] == 0


@pytest.mark.parametrize('status,expected,score', [('verified', 'FORMAL_VERIFIED', 3),
    ('refuted', 'FORMAL_REFUTED', 1), ('unverified', 'FORMAL_UNPROVED', 1),
    ('technical_error', 'FORMAL_ERROR', 1)])
def test_formal_credit_and_epistemic_states(monkeypatch, status, expected, score):
    fake_checker(monkeypatch, status)
    span = '731-137=584' if status == 'refuted' else '731-137=594'
    text = '(a)\n' + span
    r = run(text, [claim(text, span, ['a.identifies_137', 'a.constructs_subtraction', 'a.result_594'])], use_lean=True)
    formal = next(x for x in r['verification_results'] if x['obligation_id'] == 'a.result_594')
    assert formal['status'] == expected and r['score'] == score
    assert formal['mathematical_refutation'] == (status == 'refuted')
    assert r['technical_uncertainty'] == (status == 'technical_error')
    if status == 'verified':
        assert r['formal_awards'][0]['points'] == 3 and r['credits'][0]['rule_id'] == 'a.full'


def test_score_closure_preserves_other_credit_without_mutating_original():
    cfg = config_for('TME2026P1')
    ev = PautaEvidence(problem_id=cfg.problem_id, solution_id='closure', obligations=(
        ObligationEvidence(obligation_id='a.result_594', status='technical_error', origin='student_lean'),
        ObligationEvidence(obligation_id='b.reversed_number', status='supported', origin='deterministic',
                           attributable_to_student=True, evidence_refs=('r',))))
    assessment = PautaEngine().evaluate(cfg, ev)
    snapshot = assessment.model_dump_json()
    closed = ScoreClosurePolicy().close(assessment)
    assert assessment.score is None and closed['score'] == 2
    assert closed['technical_uncertainty'] and closed['review_recommended']
    assert assessment.model_dump_json() == snapshot


def test_semantic_support_is_distinct_and_independent_obligation_can_score():
    text = '(b)\nAo inverter, centenas e unidades trocam de posição e a dezena permanece.'
    c = claim(text, text.split('\n')[1], ['b.reversed_number'], kind='qualitative')
    r = run(text, [c], sufficiency_provider=gate())
    assert r['score'] == 2 and r['semantic_awards'] and not r['formal_awards']
    assert {v['status'] for v in r['verification_results']} == {'SEMANTIC_SUPPORTED'}
    assert not r['sufficiency']['payload'].get('official_reference')
    assert all(not x['eligible'] for x in r['awards'] if x['obligation_id'] != 'b.reversed_number')


def test_sufficiency_failure_does_not_erase_independent_local_credit():
    text = '(a)\n137\n(b)\nAo inverter, centenas e unidades trocam de posição.'
    cs = [claim(text, '137', ['a.identifies_137']),
          claim(text, text.splitlines()[-1], ['b.reversed_number'], kind='qualitative')]
    r = run(text, cs, sufficiency_provider=lambda p: ((), {'status': 'unavailable', 'reason': 'timeout'}))
    assert r['score'] == 1 and r['technical_uncertainty'] and r['review_recommended']
    assert not r['fallback_used']  # extractor succeeded; uncertainty is local


def test_unselected_conflicting_claim_blocks_automatic_award(monkeypatch):
    fake_checker(monkeypatch, 'verified')
    text = '(a)\n731-137=594\n731-137=584'
    r = run(text, [claim(text, '731-137=594', ['a.identifies_137', 'a.constructs_subtraction', 'a.result_594'])], use_lean=True)
    assert r['score'] == 1
    conflict = next(c for c in r['conflicts'] if c['obligation_id'] == 'a.result_594')
    assert conflict['status'] == 'CONFLICTING_EVIDENCE' and not conflict['resolved']
    assert conflict['resolution_rule'] is None and conflict['guard_source_records']
    assert 'E003' in conflict['conflicting_evidence_ids']
    assert any(b['source_span'] == '731-137=584' for b in conflict['guard_source_bindings'])
    assert not next(a for a in r['awards'] if a['obligation_id'] == 'a.result_594')['eligible']


def test_contradictory_semantics_is_explicit_blocking_conflict():
    text = '(b)\nAo inverter, centenas e unidades trocam de posição.'
    r = run(text, [claim(text, text.splitlines()[-1], ['b.reversed_number'], kind='qualitative')],
            sufficiency_provider=gate('contradictory'))
    assert r['score'] == 0 and r['conflicts'] and not r['semantic_awards']


def test_resolution_requires_explicit_rule_and_same_binding():
    rows = [dict(evidence_ids=['a'], route='FORMAL', status='FORMAL_VERIFIED', claim_binding_sha256='same'),
            dict(evidence_ids=['b'], route='SEMANTIC', status='SEMANTIC_INSUFFICIENT', claim_binding_sha256='same')]
    assert not resolve_conflict(rows)['resolved']
    with pytest.raises(ValueError):
        resolve_conflict(rows, rule='prefer_larger_score')
    result = resolve_conflict(rows, rule='same_bound_claim_formal_over_semantic')
    assert result['resolved'] and result['winning_evidence'] == ['a'] and result['rejected_evidence'] == ['b']
    rows[1]['claim_binding_sha256'] = 'different'
    with pytest.raises(ValueError):
        resolve_conflict(rows, rule='same_bound_claim_formal_over_semantic')


def test_duplicate_claims_cannot_duplicate_points(monkeypatch):
    fake_checker(monkeypatch, 'verified')
    text = '(a)\n731-137=594'
    c = claim(text, '731-137=594', ['a.identifies_137', 'a.constructs_subtraction', 'a.result_594'])
    r = run(text, [c, c, c], use_lean=True)
    assert r['score'] == 3
    assert len(r['extracted_evidence']) == 1
    assert len(r['credits']) == 1 and sum(x['points'] for x in r['credits']) == 3


@pytest.mark.parametrize('failure', ['api', 'schema'])
def test_extractor_failure_uses_current_with_numeric_closure(failure):
    def failed(*args):
        if failure == 'api':
            raise TimeoutError('offline')
        return '{"points":20}', dict(status='completed')
    r = evaluate('fallback', 'TME2026P1', '(a)\n137', extraction_provider=failed, use_lean=False)
    assert r['score'] == 1 and r['requested_mode'] == 'TME_SEMANTIC_FORMAL'
    assert r['effective_mode'] == 'TME_CURRENT_FALLBACK' and r['fallback_used'] and r['fallback_reason']
    assert not r['extracted_evidence']


def test_fallback_technical_error_preserves_valid_credits(monkeypatch):
    fake_checker(monkeypatch, 'technical_error')
    r = evaluate('fallback', 'TME2026P1', '(a)\n731-137=594',
                 extraction_provider=lambda *a: (None, {'status': 'unavailable'}))
    assert r['current_assessment']['score'] is None
    assert r['score'] == 1 and r['technical_uncertainty'] and r['fallback_used']


def test_current_wrapper_equals_existing_baseline():
    text = '(a)\n137'
    _, baseline = primary_audit('TME2026P1', SourceDocument.parse(text).items, solution_id='current', use_lean=False)
    r = evaluate('current', 'TME2026P1', text, mode='tme_current', use_lean=False,
                 extraction_provider=lambda *a: pytest.fail('current mode requested LLM'))
    assert r['current_assessment'] == baseline.model_dump(mode='json')
    assert r['score'] == float(baseline.score) and not r['fallback_used']


def test_no_unselected_positive_credit_or_cross_item_projection():
    text = '(a)\n137'
    assert run(text, [])['score'] == 0
    r = run(text, [claim(text, '137', ['b.reversed_number'])])
    assert r['score'] == 0 and not r['obligation_mapping'][0]['accepted']


def test_pipeline_files_and_auditor_version_inputs_are_unchanged():
    folders = ['tme', 'claims', 'student_claims', 'lean', 'core/math_canonical', 'rubric/pauta', 'submission_audits']
    paths = ['app/confia_lean_auditor/' + p for p in folders] + ['examples/pautas', 'lean-toolchain', 'lake-manifest.json']
    subprocess.run(['git', 'diff', '--exit-code', BASE, '--', *paths], cwd=ROOT, check=True, capture_output=True)
    tracked = set(subprocess.check_output(['git', 'ls-files', *paths], cwd=ROOT, text=True).splitlines())
    assert all(str(p.relative_to(ROOT)) in tracked for folder in folders
               for p in (ROOT/'app/confia_lean_auditor'/folder).rglob('*.py'))


def test_runner_source_only_ids_and_holdout_block_before_read(tmp_path):
    data, ids = tmp_path/'source.json', tmp_path/'ids.json'
    data.write_text(json.dumps([dict(case_id='known', problem_id='TME2026P1', solution_text='(a)\n137')]))
    ids.write_text('["known"]')
    cases, hashes = load_inputs(data, ids)
    assert len(cases) == 1 and hashes['dataset']
    with pytest.raises(ValueError, match='sealed_holdout'):
        load_inputs(tmp_path/'tme_holdout_eval_01'/'never_opened.json', ids)
    rows = json.loads(data.read_text()); rows[0]['gold'] = 20; data.write_text(json.dumps(rows))
    with pytest.raises(ValidationError):
        load_inputs(data, ids)


def test_runner_persists_structural_metrics_without_running_pilot(tmp_path, monkeypatch):
    from scripts.evaluation import run_tme_semantic_formal_c1 as runner
    text = '(a)\n137'; row = run(text, [claim(text, '137', ['a.identifies_137'])])
    data, ids = tmp_path/'source.json', tmp_path/'ids.json'
    data.write_text(json.dumps([dict(case_id='contract', problem_id='TME2026P1', solution_text=text)]))
    ids.write_text('["contract"]')
    monkeypatch.setattr(runner, 'evaluate', lambda *a, **k: deepcopy(row))
    assert main(['--mode', 'tme_semantic_formal', '--dataset', str(data), '--ids-file', str(ids),
                 '--output-dir', str(tmp_path/'out'), '--model', 'configurable', '--reasoning-effort', 'high']) == 0
    result = json.loads((tmp_path/'out/summary.json').read_text())
    assert result['cases'] == result['numeric_scores'] == result['deterministic_verified'] == 1
    assert result['mean_score'] == 1
    assert (tmp_path/'out/contract.json').is_file()


def test_model_and_effort_are_explicit_without_model_substitution():
    for model in ['gpt-6.1-sol', 'caller-chosen-model']:
        r = transport({'temperature': 0, 'store': False}, model, 'high')
        assert r['model'] == model and r['reasoning'] == {'effort': 'high'} and 'temperature' not in r


def test_score_range_and_missing_evidence():
    for text in ['', '(a)\nNada concluído.', '(a)\n137']:
        r = run(text, [])
        assert type(r['score']) is float and 0 <= r['score'] <= 20
    with pytest.raises(ValueError, match='only_P1'):
        evaluate('invalid', 'TME2026P2', '')


def test_local_verification_meanings_do_not_collapse():
    assert verification_status('FORMAL', 'unverified', formal_attempted=True) == 'FORMAL_UNPROVED'
    assert verification_status('FORMAL', 'unverified') == 'FORMAL_NOT_ATTEMPTED'
    assert verification_status('FORMAL', 'technical_error') == 'FORMAL_ERROR'
    assert verification_status('DETERMINISTIC', 'refuted') == 'DETERMINISTIC_FAILED'


def test_extractor_live_transport_contract_with_offline_client(monkeypatch):
    from types import SimpleNamespace
    import openai
    text = '(a)\n137'
    raw = json.dumps({'evidence': [claim(text, '137', ['a.identifies_137'])]})
    calls = []
    class Client:
        def __init__(self, **kwargs):
            assert kwargs == {'timeout': 180, 'max_retries': 0}
            self.responses = self
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(status='completed', model='chosen-model', id='fixture', output_text=raw,
                usage=SimpleNamespace(model_dump=lambda **kw: dict(input_tokens=10, output_tokens=20, total_tokens=30)))
    monkeypatch.setattr(openai, 'OpenAI', Client)
    es, meta = SemanticExtractorTME('chosen-model', 'high').extract('TME2026P1', text)
    assert len(es) == 1 and meta['status'] == 'completed' and meta['usage']['total_tokens'] == 30
    assert calls[0]['store'] is False and calls[0]['reasoning'] == {'effort': 'high'}
    assert calls[0]['text']['format']['strict'] is True
    assert set(json.loads(calls[0]['input'][1]['content'])) == set(SemanticExtractorTME().payload('TME2026P1', text))


def test_unknown_source_item_is_conservative_and_literal_qualitative_is_required():
    text = '137'
    r = run(text, [claim(text, '137', ['a.identifies_137'])])
    assert r['score'] == 0 and r['review_recommended']
    text = '(b)\nSem desenvolvimento.'
    c = claim(text, 'Sem desenvolvimento.', ['b.reversed_number'], kind='qualitative', normalized='invented argument')
    with pytest.raises(ValueError, match='literal_argument'):
        bind_evidence(json.dumps({'evidence': [c]}), text, 'fixture')


def test_prepared_pilot_is_source_only_and_not_executed():
    folder = ROOT/'tests/fixtures/tme_semantic_formal_c1'
    cases, _ = load_inputs(folder/'pilot_sources.json', folder/'pilot_ids.json')
    manifest = json.loads((folder/'pilot_manifest.json').read_text())
    assert len(cases) == 21 and all(c.problem_id == 'TME2026P1' for c in cases)
    assert manifest['executed'] is False and manifest['prepared_only'] is True
    assert all(set(c.model_dump()) == {'case_id', 'problem_id', 'solution_text'} for c in cases)


def test_qualitative_tag_cannot_bypass_existing_mathematical_checker():
    text = '(d)\na-c=7'
    r = run(text, [claim(text, 'a-c=7', ['d.difference_six'], kind='qualitative')],
            sufficiency_provider=lambda p: pytest.fail('incorrect route reached semantic gate'))
    assert r['score'] == 0
    assert r['obligation_mapping'][0]['reason'] == 'supported_math_cannot_bypass_checker_as_qualitative'


def test_conflicting_extractor_context_does_not_select_favorable_interpretation():
    text = '(a)\n137'
    c = claim(text, '137', ['a.identifies_137'])
    r = run(text, [c, dict(c, abandoned=True)])
    assert r['score'] == 0 and r['conflicts']
    assert len(r['conflicts'][0]['conflicting_evidence_ids']) >= 2


def test_award_gate_cannot_accept_an_unexplained_resolved_flag():
    from confia_lean_auditor.experimental.tme_semantic_formal.award_gate import AwardGate
    text = '(a)\n137'; c = claim(text, '137', ['a.identifies_137'])
    r = run(text, [c]); es = bind_evidence(json.dumps({'evidence': [c]}), text, 'fixture')
    with pytest.raises(ValueError, match='requires_explicit_rule'):
        AwardGate().evaluate('contract', es, r['obligation_mapping'], r['verification_results'],
                             [{'obligation_id': 'a.identifies_137', 'resolved': True}])


def test_selected_subclaim_cannot_certify_only_one_error_in_whole_item():
    span = '731-137=584; 2+2=5'
    text = '(a)\n' + span
    c = claim(text, span, ['a.identifies_137', 'a.constructs_subtraction', 'a.arithmetic_error_only'],
              normalized='731-137=584')
    r = run(text, [c])
    assert r['score'] == 1
    award = next(a for a in r['awards'] if a['obligation_id'] == 'a.arithmetic_error_only')
    assert not award['eligible']
    result = next(v for v in r['verification_results'] if v['obligation_id'] == 'a.arithmetic_error_only')
    assert not result['sufficiency_decision']['sufficient']


def test_selected_correct_definition_cannot_hide_conflicting_definition():
    text = '(b)\nR=100c+10b+a\nR=100a+10b+c'
    r = run(text, [claim(text, 'R=100c+10b+a', ['b.reversed_number'])])
    assert r['score'] == 0
    assert r['conflicts'][0]['detection_reason'] == 'conflicting_written_symbol_definitions'
    assert 'E003' in r['conflicts'][0]['conflicting_evidence_ids']
