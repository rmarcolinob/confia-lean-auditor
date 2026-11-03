"""Opt-in real Lean integration on synthetic examples, never dataset/pilot cases.

CONFIA_B_LEAN_RUNTIME must point to a fresh isolated clone with pinned .lake.
All generated files are under pytest's explicit --basetemp directory.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import pytest
from confia_lean_auditor.semantic.semantic_extractor_v2 import parse_response, SemanticExtractionError
from confia_lean_auditor.evaluation.semantic_formal_b import evaluate_mode, evaluate_case
from test_semantic_formal_b import PAYLOADS, raw

RUNTIME = os.environ.get('CONFIA_B_LEAN_RUNTIME')
pytestmark = pytest.mark.skipif(not RUNTIME, reason='Opt-in isolated Lean runtime required')

TEXTS = {
 'ITA2025F2Q1': 'x^57=-1; x^14=x-1; x^7=x. Resto: (a+b)x-a. Comparando com 2x+1: a+b=2 e -a=1. Portanto a=-1 e b=3.',
 'ITA2025F2Q5': 'log10(3^100)=100log10(3)=47,7100=47+0,7100. A mantissa é 0,7100. log5=0,6990; log6=0,7781. 0,6990<0,7100<0,7781. Portanto o primeiro algarismo é 5.',
 'ITA2025F2Q6': 'P(n)=C(n-1,3)/2^n. A razão P(n+1)/P(n)=n/(2n-6). Cresce até 6, empata em 6 e 7 e decresce depois. Portanto n=6 e n=7.'}
SPANS = {
 'f2q1_student_power_reduction': 'x^57=-1',
 'f2q1_student_reduced_form': '(a+b)x-a',
 'f2q1_student_coefficient_system': 'a+b=2 e -a=1',
 'f2q1_student_final_answer': 'a=-1 e b=3',
 'f2q5_student_log_power_decomposition': 'log10(3^100)=100log10(3)=47,7100=47+0,7100',
 'f2q5_student_mantissa': 'A mantissa é 0,7100',
 'f2q5_student_digit_log_bounds': 'log5=0,6990; log6=0,7781',
 'f2q5_student_between_bounds': '0,6990<0,7100<0,7781',
 'f2q5_student_final_digit': 'o primeiro algarismo é 5',
 'f2q6_student_probability_formula': 'P(n)=C(n-1,3)/2^n',
 'f2q6_student_ratio_formula': 'A razão P(n+1)/P(n)=n/(2n-6)',
 'f2q6_student_final_answer': 'Portanto n=6 e n=7',
}


@pytest.mark.parametrize('problem_id', sorted(TEXTS))
def test_real_lean_same_historical_core_both_modes(problem_id, tmp_path):
    prefix = problem_id.replace('ITA2025', '').lower()
    claims = [raw(k, text=SPANS[k]) for k in PAYLOADS if k.startswith(prefix)]
    if problem_id == 'ITA2025F2Q1':
        claims.extend([raw('f2q1_student_power_reduction', text='x^14=x-1', normalized_payload={'exponent':14,'const':-1,'coeff':1}),
                       raw('f2q1_student_power_reduction', text='x^7=x', normalized_payload={'exponent':7,'const':0,'coeff':1})])
    evs = parse_response({'claims':claims}, problem_id, TEXTS[problem_id], 'mock-no-api')
    semantic = evaluate_mode(Path(RUNTIME), tmp_path / 'semantic', problem_id, TEXTS[problem_id], 'SEMANTIC_FORMAL', evs)
    offline = evaluate_mode(Path(RUNTIME), tmp_path / 'offline', problem_id, TEXTS[problem_id], 'FORMAL_OFFLINE')
    (tmp_path / 'results.json').write_text(json.dumps({'semantic':semantic,'offline':offline},indent=2))
    assert semantic['lean_status'] == offline['lean_status'] == 'verified'
    assert semantic['score'] == offline['score'] == 10.0
    assert semantic['award_policy'] == offline['award_policy'] == 'common_evidence_formal_award.v2'
    assert all(e['context_policy']=='legacy_context_assumed' for e in offline['extracted_evidence'])
    assert all('context_policy' in e for e in semantic['extracted_evidence'])
    assert [i['max_points'] for i in semantic['rubric_items']] == [i['max_points'] for i in offline['rubric_items']]
    assert all(c['status']=='verified' for c in semantic['student_claim_checks'])
    assert all(d['formal_obligation_satisfied'] for d in semantic['formal_award_decisions'])
    for mode in (semantic, offline):
        for c in mode['student_claim_checks']:
            assert str(tmp_path) in c['lean_file']


def test_real_failed_claim_and_api_fallback(tmp_path):
    problem_id='ITA2025F2Q5'
    text='O primeiro algarismo é 6.'
    evs=parse_response({'claims':[raw(text=text, normalized_payload={'digit':6})]},problem_id,text,'mock-no-api')
    result=evaluate_mode(Path(RUNTIME),tmp_path/'failed',problem_id,text,'SEMANTIC_FORMAL',evs)
    assert result['score']==0.0
    assert result['student_claim_checks'][0]['status']=='failed'
    assert result['formal_award_decisions'][-1]['reason']=='conflicting_failed'
    case={'solution_id':'synthetic-final-only','problem_id':problem_id,'text':'O primeiro algarismo é 5.'}
    offline=evaluate_case(Path(RUNTIME),tmp_path/'offline-case',case,'formal_offline','mock-no-api')
    def fail(*args):
        raise SemanticExtractionError('api_error:synthetic',{'api_status':'api_error'})
    fallback=evaluate_case(Path(RUNTIME),tmp_path/'fallback-case',case,'semantic_formal','mock-no-api',extractor=fail)
    assert fallback['score']==offline['score']==2.0
    assert fallback['fallback_used'] and fallback['mode_effective']=='FORMAL_OFFLINE'
    (tmp_path/'fallback.json').write_text(json.dumps({'offline':offline,'fallback':fallback},indent=2))


def test_real_single_power_insufficient_for_both_modes(tmp_path):
    text='x^57=-1'
    problem='ITA2025F2Q1'
    claims=parse_response({'claims':[raw('f2q1_student_power_reduction',text=text)]},problem,text,'mock-no-api')
    a=evaluate_mode(Path(RUNTIME),tmp_path/'offline',problem,text,'FORMAL_OFFLINE')
    b=evaluate_mode(Path(RUNTIME),tmp_path/'semantic',problem,text,'SEMANTIC_FORMAL',claims)
    assert a['score']==b['score']==0.0
    assert a['student_claim_checks'][0]['status']==b['student_claim_checks'][0]['status']=='verified'
    assert a['formal_award_decisions'][0]['rejection_reason']==b['formal_award_decisions'][0]['rejection_reason']=='formal_obligation_not_satisfied'
    (tmp_path/'partial_power.json').write_text(json.dumps({'offline':a,'semantic':b},indent=2))


def test_real_context_is_only_reason_for_different_award(tmp_path):
    text='Se o primeiro algarismo é 5, ainda precisamos demonstrar.'
    problem='ITA2025F2Q5'
    claims=parse_response({'claims':[raw(text=text,assertion_status='hypothetical',hypothetical=True,scope='exploration')]},problem,text,'mock-no-api')
    a=evaluate_mode(Path(RUNTIME),tmp_path/'offline',problem,text,'FORMAL_OFFLINE')
    b=evaluate_mode(Path(RUNTIME),tmp_path/'semantic',problem,text,'SEMANTIC_FORMAL',claims)
    assert a['student_claim_checks'][0]['status']==b['student_claim_checks'][0]['status']=='verified'
    assert a['student_claim_checks'][0]['lean_statement']==b['student_claim_checks'][0]['lean_statement']
    assert a['score']==2.0 and b['score']==0.0
    assert a['extracted_evidence'][0]['context_policy']=='legacy_context_assumed'
    assert b['formal_award_decisions'][-1]['rejection_reason']=='context_rejected'
    (tmp_path/'context.json').write_text(json.dumps({'offline':a,'semantic':b},indent=2))
