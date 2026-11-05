"""Explicit P1 structural runner. Source-only JSON; never imports a gold dataset."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Literal

from pydantic import Field
from confia_lean_auditor.student_claims.semantic import StrictModel, sha
from confia_lean_auditor.experimental.tme_semantic_formal.engine import evaluate
from confia_lean_auditor.experimental.tme_semantic_formal.obligation_mapper import SourceDocument


class InputCase(StrictModel):
    case_id: str = Field(min_length=1, max_length=120, pattern=r'^[A-Za-z0-9_-]+$')
    problem_id: Literal['TME2026P1', 'TME2_P1_PILOT']
    solution_text: str = Field(max_length=19000)


def safe_input(path):
    resolved = Path(path).resolve()
    if 'tme_holdout_eval_01' in str(path).lower() or 'tme_holdout_eval_01' in str(resolved).lower():
        raise ValueError('sealed_holdout_forbidden')
    return resolved


def load_inputs(dataset, ids_file):
    # Check both paths before opening either. Input schema intentionally cannot
    # carry scores, annotations, gold, historical judgments or other metadata.
    dataset, ids_file = safe_input(dataset), safe_input(ids_file)
    raw = json.loads(dataset.read_text())
    if not isinstance(raw, list):
        raise ValueError('dataset_must_be_source_only_case_list')
    cases = [InputCase.model_validate(row) for row in raw]
    lookup = {c.case_id: c for c in cases}
    if len(lookup) != len(cases):
        raise ValueError('duplicate_dataset_case_id')
    if set(lookup) & {'summary', 'run_manifest'}:
        raise ValueError('case_id_reserved_for_runner_artifacts')
    ids = json.loads(ids_file.read_text())
    if (not isinstance(ids, list) or not ids or any(type(i) is not str for i in ids)
            or len(set(ids)) != len(ids) or not set(ids) <= lookup.keys()):
        raise ValueError('ids_must_be_unique_existing_case_ids')
    for identifier in ids:
        SourceDocument.parse(lookup[identifier].solution_text)
    return [lookup[i] for i in ids], dict(dataset=sha(raw), ids=sha(ids))


def summarize(rows):
    counts = Counter(r['status'].lower() for row in rows for r in row['verification_results'])
    routes = Counter(r['route'].lower() for row in rows for r in row['verification_results'] if r['route'])
    result = dict(cases=len(rows), numeric_scores=sum(type(r['score']) in {int, float} for r in rows),
        fallbacks=sum(r['fallback_used'] for r in rows),
        claims_extracted=sum(len(r['extracted_evidence']) for r in rows),
        obligations_with_evidence=sum(len({m['obligation_id'] for m in r['obligation_mapping'] if m['accepted']}) for r in rows),
        conflicts=sum(len(r['conflicts']) for r in rows),
        items_scored=sum(i['known_points'] is not None and float(i['known_points']) > 0 for r in rows for i in r['rubric_items']),
        technical_uncertainty_cases=sum(r['technical_uncertainty'] for r in rows),
        review_recommended_cases=sum(r['review_recommended'] for r in rows),
        mean_score=sum(r['score'] for r in rows)/len(rows) if rows else 0.0)
    for name in ('formal_verified', 'formal_refuted', 'formal_unproved', 'formal_not_attempted', 'formal_error',
                 'deterministic_verified', 'deterministic_failed', 'semantic_supported',
                 'semantic_insufficient', 'context_rejected'):
        result[name] = counts[name]
    for route in ('formal', 'deterministic', 'semantic'):
        result[route + '_routes'] = routes[route]
    result['formal_attempts'] = sum(bool(r.get('formal_attempted')) for row in rows for r in row['verification_results'])
    result['formal_execution_unknown'] = sum(r.get('status') == 'FORMAL_ERROR' and r.get('formal_attempted') is None
                                             for row in rows for r in row['verification_results'])
    result['metric_definitions'] = dict(routes='verification result rows, including composite obligation checks',
        formal_attempts='result rows with execution confirmed by the existing Lean checker contract',
        formal_execution_unknown='technical errors whose existing checker result cannot establish subprocess execution',
        formal_not_attempted='formal candidate without a Lean execution; never a mathematical refutation',
        items_scored='top-level rubric items with positive authorized points',
        obligations_with_evidence='unique obligations with context-compatible mapped candidates per case',
        baseline='baseline/fallback verification rows come from original facts; C1 extraction/mapping metrics are zero')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', required=True, choices=['tme_current', 'tme_semantic_formal'])
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--ids-file', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--model', default='gpt-4o-mini-2024-07-18')
    parser.add_argument('--reasoning-effort', default='none', choices=['none', 'minimal', 'low', 'medium', 'high', 'xhigh'])
    args = parser.parse_args(argv)
    cases, hashes = load_inputs(args.dataset, args.ids_file)
    output = args.output_dir.resolve()
    if 'tme_holdout_eval_01' in str(output).lower():
        raise ValueError('sealed_holdout_forbidden')
    output.mkdir(parents=True, exist_ok=False)
    (output/'run_manifest.json').write_text(json.dumps(dict(mode=args.mode, model=args.model,
        reasoning_effort=args.reasoning_effort, ids=[c.case_id for c in cases], input_hashes=hashes), indent=2)+'\n')
    rows = []
    for case in cases:
        row = evaluate(case.case_id, case.problem_id, case.solution_text, mode=args.mode,
                       model=args.model, reasoning_effort=args.reasoning_effort)
        row['configuration_hashes'].update(hashes)
        (output/(case.case_id + '.json')).write_text(json.dumps(row, ensure_ascii=False, indent=2)+'\n')
        rows.append(row)
    summary = summarize(rows)
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
