#!/usr/bin/env python3
"""Frozen DEV-only evidence-ID experiment. No HOLDOUT reader or execution mode.

Prepare -> freeze -> shadow -> explicit reviewed gate -> optional active DEV.
The existing obligation runner supplies DEV inputs, aggregation and activation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'app'))
spec = importlib.util.spec_from_file_location('obligation_runner', Path(__file__).with_name('evaluate_tme_obligation_aware.py'))
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
from confia_lean_auditor.student_claims import evidence_id_semantic as sem
from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.tme.evidence_id_experiment import run_shadow

OUT = ROOT/'artifacts/evaluations/tme_semantic_evidence_ids_01'
LIVE = ROOT/'artifacts/evaluations/tme_obligation_aware_live_01'
POLICY = dict(minimum_valid_responses=20, minimum_id_grounding_rate=1.0,
              minimum_new_verified_facts=7, minimum_new_supported=7,
              known_false_attribution=0, known_false_credit=0, context_control_failures=0,
              checker_technical_errors=0, baseline_regression_blocked=0,
              rationale='Validity at least 80% versus 52%; at most 5 invalid versus 12. More than the previous 6 new verified facts and supportable obligations. All valid positive selections must bind real IDs; safety and baseline preservation required.',
              holdout='NEVER_READ_OR_RUN', retries=0)
read = old.read
sha = old.sha


def write(name, value):
    old.write(OUT/name, value)


def source_hashes():
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted({
        *ROOT.glob('app/confia_lean_auditor/**/*.py'), *ROOT.glob('examples/pautas/tme2*.json'),
        Path(__file__), Path(__file__).with_name('evaluate_tme_obligation_aware.py'),
        *ROOT.glob('tests/test*semantic*.py'), ROOT/'tests/test_evidence_id_semantic.py',
    })}


def freeze():
    current = dict(configuration=sem.configuration(), source_hashes=source_hashes(), policy=POLICY,
                   dev_ids_sha256=sha(old.PRIOR/'dev_ids.json'), diagnosis_sha256=sha(old.DIAG/'cases_analysis.json'),
                   historical_generic_sha256=sha(old.PRIOR/'dev_after_results.json'),
                   previous_live_sha256=sha(LIVE/'shadow_summary.json'),
                   primary_cache_sha256={p.name: sha(p) for p in sorted((LIVE/'primary').glob('*.json'))},
                   prepared_sha256={p.name: sha(p) for p in sorted((OUT/'prepared_payloads').glob('*.json'))},
                   units_sha256={p.name: sha(p) for p in sorted((OUT/'evidence_units').glob('*.json'))},
                   request_schema_sha256={p.name: sha(p) for p in sorted((OUT/'schemas').glob('*.json'))})
    path = OUT/'experiment_freeze.json'
    if path.exists():
        assert read(path) == current, 'Code/prompt/schema/config/input changed after freeze'
    else:
        write('experiment_freeze.json', current)
    return current


def primaries():
    return {p.stem: (old.PautaBridgeResult.model_validate(read(p)['bridge']),
                    old.PautaAssessment.model_validate(read(p)['assessment']))
            for p in (LIVE/'primary').glob('*.json')}


def prepare():
    OUT.mkdir(exist_ok=True)
    assert not (OUT/'experiment_freeze.json').exists(), 'Already frozen'
    cases = old.sources()
    primary = primaries()
    assert set(primary) == {c['solution_id'] for c in cases}
    for directory in ('prepared_payloads', 'evidence_units', 'schemas', 'responses', 'shadow'):
        (OUT/directory).mkdir(exist_ok=True)
    for c in cases:
        sid = c['solution_id'];problem = old.internal_id(c['problem_id'])
        targets = old.unresolved_targets(problem, primary[sid][0]);units = evidence_units(c['solution_text'])
        write(f'prepared_payloads/{sid}.json', sem.wire_payload(problem, c['solution_text'], targets))
        write(f'evidence_units/{sid}.json', [u.model_dump(mode='json') for u in units])
        write(f'schemas/{sid}.json', sem.response_schema(targets, units))
    preflight = dict(sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        branch=subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
        working_tree=subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
        api_key_available=bool(os.environ.get('OPENAI_API_KEY')), model=sem.configuration()['model'],
        api_destination=os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
        dev_ids=[c['solution_id'] for c in cases], holdout_processed=0, holdout_texts_read=0,
        primary_cache='tme_obligation_aware_live_01/primary',
        primary_cache_sha256={p.name: sha(p) for p in (LIVE/'primary').glob('*.json')})
    # Do not accidentally persist credentials embedded in a custom endpoint.
    from urllib.parse import urlsplit
    endpoint = urlsplit(preflight['api_destination'])
    assert not endpoint.username and not endpoint.password and not endpoint.query
    write('preflight.json', preflight)
    write('promotion_policy.json', POLICY)
    frozen = freeze()
    print('PREPARED_AND_FROZEN', len(cases), 'DEV', frozen['configuration']['model'], flush=True)


def shadow():
    frozen = freeze();cases = old.sources();primary = primaries()
    assert not list((OUT/'responses').glob('*.json')), 'Do not rerun live cases'
    assert read(OUT/'preflight.json')['api_key_available']
    def request(c):
        sid = c['solution_id'];problem = old.internal_id(c['problem_id'])
        targets = old.unresolved_targets(problem, primary[sid][0])
        selections, metadata = sem.request_selections(problem, c['solution_text'], json.dumps(targets, ensure_ascii=False, sort_keys=True), json.dumps(frozen['configuration'], sort_keys=True))
        raw = dict(solution_id=sid, problem_id=c['problem_id'], selections=[s.model_dump() for s in selections], provider=metadata,
                   source_sha256=c['source_sha256'], targets_sha256=old.legacy.sha(targets))
        write(f'responses/{sid}.json', raw)
        print('EXTRACT', sid, metadata['status'], metadata.get('reason', ''), len(selections), flush=True)
        return sid, raw
    cached = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = [pool.submit(request, c) for c in cases]
        for job in as_completed(jobs):
            sid, raw = job.result();cached[sid] = raw
    results = []
    for c in cases:
        sid = c['solution_id'];raw = cached[sid]
        def replay(problem, source, targets, config):
            assert old.legacy.sha(source) == raw['source_sha256']
            assert old.legacy.sha(json.loads(targets)) == raw['targets_sha256']
            assert json.loads(config) == frozen['configuration']
            return tuple(sem.ObligationEvidenceSelection.model_validate(s) for s in raw['selections']), raw['provider']
        result = run_shadow(c['problem_id'], c['items'], c['solution_text'], solution_id=primary[sid][1].solution_id,
                            provider=replay, primary=primary[sid], use_lean=True)
        row = dict(solution_id=sid, problem_id=c['problem_id'], primary_bridge=result.primary_bridge.model_dump(mode='json'),
            primary_assessment=result.assessment.model_dump(mode='json'), assessment=result.assessment.model_dump(mode='json'),
            potential_bridge=result.potential_bridge.model_dump(mode='json'), telemetry=result.telemetry, semantic_shadow=True)
        write(f'shadow/{sid}.json', row);results.append(row)
        old.rows_write(OUT/'shadow_candidates.jsonl', [dict(solution_id=r['solution_id'], **r['telemetry']) for r in results])
        print('SHADOW', sid, result.telemetry['combined_potential_supported'], flush=True)
    summarize(results, cases)
    assert freeze() == frozen


def summarize(results, cases):
    prior = {r['solution_id']: r for r in read(old.PRIOR/'dev_after_results.json')}
    # Adapter for common measurement code only. No candidate/source reconstruction.
    adapted = [{**r, 'telemetry': {**r['telemetry'], 'candidates': r['telemetry']['selections']}} for r in results]
    summary, byproblem = old.aggregate(cases, adapted, prior)
    events = [dict(solution_id=r['solution_id'], **e) for r in results for e in r['telemetry']['events']]
    present = [e for e in events if e['evidence_present']]
    providers = [r['telemetry']['provider'] for r in results]
    semantic_facts = [f for r in results for f in r['potential_bridge']['auditor']['facts'] if any(s.startswith('semantic:') for s in f['source_claim_ids'])]
    verified_records = {(r['solution_id'], sid) for r in results for f in r['potential_bridge']['auditor']['facts']
                        if f['verification']['status']=='verified' for sid in f['source_claim_ids'] if sid.startswith('semantic:')}
    id_grounded = {(e['solution_id'], e['obligation_id']) for e in present if e['id_grounded']}
    misses = {(c['solution_id'], o['obligation_id']) for c in cases for o in c['obligations'] if o['confirmed_miss']}
    verified_candidates = {(e['solution_id'], e['candidate_id']) for e in present
                           if (e['solution_id'], e.get('retained_record_id', e.get('record_id'))) in verified_records}
    summary.update(baseline_supported=summary['primary_supported'], baseline_semantics='deterministic_plus_unicode',
        historical_generic_supported=summary['prior_generic_supported'], previous_obligation_shadow_supported=30,
        semantic_verified_candidates=len(verified_candidates),
        semantic_potential_supported_new=summary['new_verified_vs_deterministic'],
        combined_potential_supported=summary['potential_supported'],
        deterministically_grounded_selections=sum(e['id_grounded'] for e in present),
        valid_evidence_ids=sum(len(e['evidence_ids']) for e in present),
        selected_id_grounding_rate=sum(e['id_grounded'] for e in present)/len(present) if present else 0,
        baseline_regression_blocked=[r['solution_id'] for r in results if r['telemetry']['baseline_regression_blocked']],
        api_calls=sum(p.get('api_calls', 0) for p in providers), retries=sum(p.get('retries', 0) for p in providers),
        valid_responses=sum(p['status']=='completed' for p in providers),
        invalid_responses=sum(p['status']!='completed' for p in providers),
        semantic_verification_sources=dict(Counter(f['verification_source'] for f in semantic_facts)))
    summary['misses_366']['id_grounded'] = len(id_grounded & misses)
    for problem, data in byproblem.items():
        ids = {c['solution_id'] for c in cases if c['problem_id']==problem}
        data['misses']['id_grounded'] = len({k for k in id_grounded & misses if k[0] in ids})
        data.update(baseline_supported=sum(r['telemetry']['baseline_supported'] for r in results if r['problem_id']==problem),
                    combined_potential_supported=sum(r['telemetry']['combined_potential_supported'] for r in results if r['problem_id']==problem))
    write('shadow_summary.json', summary);write('summary_by_problem.json', byproblem)
    old_summary = read(LIVE/'shadow_summary.json')
    write('funnel_before_after.json', dict(before=old_summary, after=summary,
        note='ID grounding is provenance; compare separately with legacy projected grounding after representation/context gates. Historical generic 43 is not the deterministic baseline24.'))
    write('api_calls_summary.json', dict(calls=summary['api_calls'], retries=summary['retries'], valid=summary['valid_responses'], invalid=summary['invalid_responses'],
        reasons=dict(Counter(p.get('reason','completed') for p in providers)), models=sorted({p['model'] for p in providers}),
        raw_responses_and_validation_errors_preserved=True, holdout_processed=0))
    comparisons = [dict(solution_id=r['solution_id'], problem_id=r['problem_id'], prior_generic_score=prior[r['solution_id']]['score'],
                       deterministic_primary_score=float(r['assessment']['score']) if r['assessment']['score'] is not None else None,
                       shadow_published_score=float(r['assessment']['score']) if r['assessment']['score'] is not None else None,
                       active_status='NOT_RUN', active_score=None) for r in results]
    write('dev_before_after.json', comparisons)
    passing = (summary['valid_responses']>=POLICY['minimum_valid_responses']
        and summary['selected_id_grounding_rate']>=POLICY['minimum_id_grounding_rate']
        and summary['semantic_fact_outcomes'].get('verified',0)>=POLICY['minimum_new_verified_facts']
        and summary['semantic_potential_supported_new']>=POLICY['minimum_new_supported']
        and not summary['baseline_regression_blocked'] and not summary['all_fact_outcomes'].get('technical_error',0))
    write('GO_NO_GO.json', dict(decision='PENDING_SAFETY_REVIEW' if passing else 'NO_GO', materiality_passed=passing,
        shadow_gate_passed=False, safety_review='PENDING', regression_review='PENDING', active_status='NOT_RUN', holdout_processed=0))
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


def activate():
    freeze();decision=read(OUT/'GO_NO_GO.json')
    assert decision['materiality_passed'] and decision['shadow_gate_passed']
    assert decision['safety_review']=='PASSED' and decision['regression_review']=='PASSED'
    # Reuse the same existing engine activation, without interpreting again.
    from confia_lean_auditor.rubric.pauta.engine import PautaEngine
    from confia_lean_auditor.rubric.pauta import load_pauta
    from confia_lean_auditor.tme.registry import TME_PROBLEMS
    active=[]
    for c in old.sources():
        raw=read(OUT/'shadow'/(c['solution_id']+'.json'))
        bridge=old.PautaBridgeResult.model_validate(raw['potential_bridge'])
        assessment=PautaEngine().evaluate(load_pauta(ROOT/'examples/pautas'/TME_PROBLEMS[old.internal_id(c['problem_id'])]),bridge.evidence)
        active.append(dict(solution_id=c['solution_id'],problem_id=c['problem_id'],bridge=bridge.model_dump(mode='json'),
            assessment=assessment.model_dump(mode='json'),score=float(assessment.score) if assessment.score is not None else None))
    old.rows_write(OUT/'active_dev_results.jsonl',active)
    decision.update(decision='GO',active_status='COMPLETED',holdout_processed=0)
    write('GO_NO_GO.json',decision);freeze()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','shadow','activate'])
    args=parser.parse_args()
    {'prepare':prepare,'shadow':shadow,'activate':activate}[args.mode]()
