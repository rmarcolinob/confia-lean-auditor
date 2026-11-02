#!/usr/bin/env python3
"""Contemporary, shadow-only A/B orchestration over the frozen 25 DEV.

Dry-run never constructs a client. LIVE requires an explicit flag and a clean
checkout; parameter/account compatibility must be checked in a later LIVE task.
The sufficiency payload/schema depend on each arm's fresh first-stage response.
"""
from __future__ import annotations

import argparse
from functools import partial
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'app'))
from confia_lean_auditor.student_claims import hybrid_semantic as semantic
from confia_lean_auditor.student_claims import semantic_sufficiency as sufficiency
from confia_lean_auditor.student_claims import evidence_units as units_module
from confia_lean_auditor.student_claims.obligation_catalog import internal_id
from confia_lean_auditor.tme.hybrid_grader import selective_audit
from confia_lean_auditor.tme.obligation_experiment import primary_audit
from confia_lean_auditor.tme.sufficiency_experiment import run_sufficiency_shadow

DEV_IDS = ROOT / 'artifacts/evaluations/tme_semantic_understanding_01/dev_ids.json'
DEV_SOURCES = ROOT / 'artifacts/evaluations/tme_semantic_diag_01/cases_analysis.json'
DEV_IDS_SHA256 = 'd6ae59f0a2d766f9c7541b2d8341fb6aa56ee8c1fdf55200131c842087d1d140'
DEV_SOURCES_SHA256 = 'a3432c6aa1fff0f68018e609989a26b23b7b6f5d8e86e5c586801f2445d0fe79'
SMOKE_IDS = ('TME2026P1_06', 'TME2026P2_01', 'TME2026P3_02',
             'TME2026P4_13', 'TME2026P5_09')


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode()).hexdigest()


def validate_model(model):
    # Syntax only: no model lookup, key access or provider-specific assumptions.
    if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}', model):
        raise ValueError('Invalid model ID syntax')
    return model


def select_cases(split, case_ids=None):
    if split not in {'smoke', 'dev'}:
        raise ValueError('Only smoke or dev is allowed')
    if file_hash(DEV_IDS) != DEV_IDS_SHA256:
        raise ValueError('Frozen DEV allowlist changed')
    allowed = json.loads(DEV_IDS.read_text())
    if len(allowed) != 25 or len(set(allowed)) != 25:
        raise ValueError('Expected exactly 25 frozen DEV IDs')
    selected = list(case_ids) if case_ids is not None else list(SMOKE_IDS if split == 'smoke' else sorted(allowed))
    # Check the WHOLE selection before loading texts or invoking any provider.
    if not selected or len(set(selected)) != len(selected) or set(selected) - set(allowed):
        raise ValueError('Selection must contain unique frozen DEV IDs only')
    if split == 'dev' and set(selected) != set(allowed):
        raise ValueError('DEV split must contain all 25 frozen cases')
    if split == 'smoke' and len(selected) != 5:
        raise ValueError('Smoke requires exactly five DEV cases')
    if file_hash(DEV_SOURCES) != DEV_SOURCES_SHA256:
        raise ValueError('Frozen DEV sources changed')
    spec = importlib.util.spec_from_file_location('ablation_dev_sources',
        Path(__file__).with_name('evaluate_tme_obligation_aware.py'))
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    sources = {c['solution_id']: c for c in loader.sources()}
    cases = [sources[sid] for sid in selected]
    if split == 'smoke' and len({c['problem_id'] for c in cases}) != 5:
        raise ValueError('Smoke requires one DEV case per problem')
    return cases


def git_state():
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
    return dict(sha=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'),
                status_short=git('status', '--short'))


def protected_hashes():
    paths = {*ROOT.glob('app/**/*.py'), *ROOT.glob('scripts/evaluation/*.py'),
             *ROOT.glob('examples/pautas/tme2*.json'),
             *ROOT.glob('problems/TME2026P[1-5]/problem.json'),
             *ROOT.glob('app/confia_lean_auditor/tme/references/*.json')}
    return {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(paths)}


def build_plan(model_a, model_b, split, case_ids=None):
    models = {'a': validate_model(model_a), 'b': validate_model(model_b)}
    cases = select_cases(split, case_ids)
    state = git_state()
    protected = protected_hashes()
    prepared = {}
    for c in cases:
        p, text = c['problem_id'], c['solution_text']
        prepared[c['solution_id']] = dict(problem_id=p, source_sha256=c['source_sha256'],
            payload=semantic.wire_payload(p, text), schema=semantic.response_schema(p, text))
    schema_hashes = {sid: object_hash(v['schema']) for sid, v in prepared.items()}
    payload_hashes = {sid: object_hash(v['payload']) for sid, v in prepared.items()}
    contract = dict(decision=sufficiency.SufficiencyDecision.model_json_schema(),
        generator_sha256=hashlib.sha256(inspect.getsource(sufficiency.response_schema).encode()).hexdigest())
    arms = {}
    for arm, model in models.items():
        sc, gc = semantic.configuration(model=model), sufficiency.configuration(model=model)
        arms[arm] = dict(model=model, git_sha=state['sha'], semantic_configuration=sc,
            semantic_configuration_sha256=object_hash(sc), sufficiency_configuration=gc,
            sufficiency_configuration_sha256=object_hash(gc),
            prompt_hashes={'semantic': sc['prompt_sha256'], 'sufficiency': gc['prompt_sha256']},
            semantic_schema_hashes=dict(schema_hashes), semantic_payload_hashes=dict(payload_hashes),
            sufficiency_schema_contract_sha256=object_hash(contract),
            sufficiency_instantiated_schema_hashes=None,
            evidence_unit_configuration_hash=file_hash(units_module.__file__),
            protected_code_hash=object_hash(protected))
    count = 2 * len(cases)
    plan = dict(version='tme-model-ablation.v1', git=state, split=split, shadow=True,
        case_ids=[c['solution_id'] for c in cases], cases=len(cases), arms=arms,
        order=[dict(solution_id=c['solution_id'], arm=a) for c in cases for a in models],
        stages_per_arm=2, first_stage_calls_planned=count,
        sufficiency_calls_planned={'minimum': 0, 'maximum': count},
        total_calls_planned={'minimum': count, 'maximum': 2 * count}, api_calls_made=0,
        holdout_processed=0, holdout_total=100, contemporary_first_stage=True,
        historical_judgments_reused=False, historical_audits_reused=False,
        dev_ids_sha256=DEV_IDS_SHA256, dev_sources_sha256=DEV_SOURCES_SHA256,
        protected_files=protected,
        schemas_equal_between_arms=True, prompts_equal_between_arms=True,
        schema_equality_scope='Identical first-stage schemas and sufficiency contract/generator. '
            'Instantiated sufficiency schemas depend on fresh selected candidates/IDs; no fictitious candidates in dry-run.',
        sufficiency_payload_status='WAITING_FOR_FRESH_FIRST_STAGE',
        parameter_compatibility='Not checked against API; later LIVE preflight. No model-specific overrides.',
        reasoning_override=None)
    return plan, prepared, cases


def _run_arm(case, model, *, judgment_provider=None, sufficiency_provider=None, use_lean=True):
    """Internal: case must come from select_cases; never accepts caller source text."""
    problem, text, sid = case['problem_id'], case['solution_text'], case['solution_id']
    started = time.monotonic()
    judge = partial(judgment_provider or semantic.request_judgments, model=model)
    gate_provider = partial(sufficiency_provider or sufficiency.request_sufficiency, model=model)
    tick = time.monotonic()
    judgments, first_meta = judge(problem, text)
    first_seconds = time.monotonic() - tick
    if first_meta['status'] == 'completed':
        judgments = semantic.validate_response(json.dumps({'judgments': [j.model_dump() for j in judgments]}), problem, text)
    elif judgments:
        raise ValueError('failed_provider_cannot_supply_judgments')
    gate = sufficiency.SemanticSufficiencyGate()
    payload, _, _ = gate.prepare(problem, text, judgments)
    tick = time.monotonic()
    decisions, gate_meta = gate.evaluate(payload, provider=gate_provider)
    gate_seconds = time.monotonic() - tick
    if gate_meta['status'] == 'completed':
        decisions = sufficiency.validate_response(json.dumps({'decisions': {
            d.obligation_id: d.model_dump() for d in decisions}}), payload)
    elif decisions:
        raise ValueError('failed_gate_cannot_supply_decisions')
    # Both model stages are fresh. Audit the actual extractions of THIS arm.
    primary, baseline = primary_audit(internal_id(problem), case['items'], solution_id=sid, use_lean=use_lean)
    audited, telemetry = selective_audit(internal_id(problem), case['items'], text,
        judgments, sid, primary, use_lean=use_lean)

    def current_gate_result(expected):
        if expected != payload:
            raise ValueError('Sufficiency payload changed inside the same arm')
        return decisions, gate_meta

    # Existing reconciliation/scoring implementation, with only the just-created
    # gate result injected. This does not make a second gate request.
    shadow = run_sufficiency_shadow(problem, text, judgments, primary, audited,
        provider=current_gate_result, first_provider_ok=first_meta['status'] == 'completed')
    return dict(solution_id=sid, problem_id=problem, requested_model=model, shadow=True,
        source_sha256=case['source_sha256'], judgments=[j.model_dump(mode='json') for j in judgments],
        first_provider=first_meta, sufficiency_provider=gate_meta,
        sufficiency_payload=payload, sufficiency_schema_sha256=object_hash(sufficiency.response_schema(payload)),
        sufficiency_decisions=[d.model_dump(mode='json') for d in shadow.decisions],
        item_linkage=shadow.linkage, reconciliation=shadow.reconciliation,
        primary_bridge=primary.model_dump(mode='json'), audit_bridge=audited.model_dump(mode='json'),
        audit_telemetry=telemetry, baseline_assessment=baseline.model_dump(mode='json'),
        evidence=shadow.evidence.model_dump(mode='json'),
        potential_assessment=shadow.potential_assessment.model_dump(mode='json'),
        audit_only_assessment=shadow.audit_only_assessment.model_dump(mode='json'),
        semantic_only_points=float(shadow.semantic_only_points),
        latency_seconds=dict(semantic=first_seconds, sufficiency=gate_seconds, total=time.monotonic() - started),
        api_calls=first_meta.get('api_calls', 0) + gate_meta.get('api_calls', 0))


def execute_plan(plan, *, judgment_provider=None, sufficiency_provider=None, use_lean=True, on_result=None):
    """Revalidate the entire plan before any provider; useful for offline injection."""
    current, _, cases = build_plan(plan['arms']['a']['model'], plan['arms']['b']['model'],
        plan['split'], plan['case_ids'])
    if current != plan:
        raise ValueError('Plan/code/configuration changed; prepare a new plan')
    results = {'a': [], 'b': []}
    for case in cases:
        for arm in ('a', 'b'):
            row = _run_arm(case, plan['arms'][arm]['model'], judgment_provider=judgment_provider,
                sufficiency_provider=sufficiency_provider, use_lean=use_lean)
            results[arm].append(row)
            if on_result:
                on_result(arm, row)
    return results


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-a', required=True)
    parser.add_argument('--model-b', required=True)
    parser.add_argument('--split', choices=['smoke', 'dev'], required=True)
    parser.add_argument('--case-id', action='append', dest='case_ids')
    parser.add_argument('--shadow', action='store_true', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--live', action='store_true')
    parser.add_argument('--output', type=Path, required=True, help='New directory; existing outputs are never overwritten')
    args = parser.parse_args(argv)
    try:
        plan, prepared, _ = build_plan(args.model_a, args.model_b, args.split, args.case_ids)
        if args.live and plan['git']['status_short']:
            raise ValueError('LIVE requires a clean frozen Git checkout')
        args.output.mkdir(parents=True, exist_ok=False)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    write_json(args.output / 'preflight.json', plan)
    for sid, data in prepared.items():
        write_json(args.output / 'prepared_payloads' / f'{sid}.json', data)
    # Do not count our requested output artifacts as source changes. Writing
    # inside a tracked source directory is still detected by protected hashes.
    if args.dry_run:
        status = dict(status='DRY_RUN', cases=plan['cases'], arms=2, stages_per_arm=2,
            calls_planned=plan['total_calls_planned'], api_calls_made=0, holdout_processed=0,
            prompts_equal=True, schemas_equal=True, schema_equality_scope=plan['schema_equality_scope'])
    else:
        def persist(arm, row):
            with (args.output / f'{args.split}_model_{arm}.jsonl').open('a') as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
        results = execute_plan(plan, on_result=persist)
        status = dict(status='SHADOW_COMPLETED', api_calls_made=sum(r['api_calls'] for rs in results.values() for r in rs),
            holdout_processed=0, model_quality_assessed=False, manual_review_required=True)
    write_json(args.output / 'execution_status.json', status)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
