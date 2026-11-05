"""Prepared DEV P2 runner. Explicit invocation only; source-only input schema."""
import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Literal
from pydantic import Field
from confia_lean_auditor.student_claims.semantic import StrictModel,sha
from confia_lean_auditor.experimental.tme_semantic_formal_p2.engine import evaluate
from confia_lean_auditor.experimental.tme_semantic_formal_p2.mapper import SourceDocument

class InputCase(StrictModel):
    case_id: str = Field(min_length=1,max_length=120,pattern=r'^[A-Za-z0-9_-]+$')
    problem_id: Literal['TME2026P2']
    solution_text: str = Field(max_length=19000)

def safe_path(path):
    resolved=Path(path).resolve()
    if any(x in str(path).lower() or x in str(resolved).lower() for x in ('holdout','gold')):
        raise ValueError('sealed_or_labelled_input_forbidden')
    return resolved

def load_inputs(dataset,ids_file):
    dataset,ids_file=safe_path(dataset),safe_path(ids_file)
    raw=json.loads(dataset.read_text());ids=json.loads(ids_file.read_text())
    if not isinstance(raw,list):raise ValueError('source_only_case_list_required')
    cases=[InputCase.model_validate(c) for c in raw];lookup={c.case_id:c for c in cases}
    if len(lookup)!=len(cases) or set(lookup)&{'summary','run_manifest'}:raise ValueError('duplicate_or_reserved_case_id')
    if not isinstance(ids,list) or not ids or any(type(i)!=str for i in ids) or len(set(ids))!=len(ids) or not set(ids)<=lookup.keys():raise ValueError('invalid_case_ids')
    for i in ids:SourceDocument.parse(lookup[i].solution_text)
    return [lookup[i] for i in ids],dict(dataset=sha(raw),ids=sha(ids))

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['tme_current','tme_semantic_formal'],required=True)
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--ids-file',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--model',default='gpt-6.1-sol')
    parser.add_argument('--reasoning-effort',default='medium',choices=['none','minimal','low','medium','high','xhigh'])
    args=parser.parse_args(argv)
    output=safe_path(args.output_dir);cases,hashes=load_inputs(args.dataset,args.ids_file)
    output.mkdir(parents=True,exist_ok=False)
    (output/'run_manifest.json').write_text(json.dumps(dict(mode=args.mode,model=args.model,reasoning_effort=args.reasoning_effort,
        input_hashes=hashes,ids=[c.case_id for c in cases]),indent=2)+'\n')
    rows=[]
    for case in cases:
        result=evaluate(case.case_id,case.problem_id,case.solution_text,mode=args.mode,model=args.model,reasoning_effort=args.reasoning_effort,use_lean=True)
        result['configuration_hashes'].update(hashes)
        (output/(case.case_id+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        rows.append(result)
    summary=dict(cases=len(rows),scores=[r['score'] for r in rows],fallbacks=sum(r['fallback_used'] for r in rows),
        technical_uncertainty_cases=sum(r['technical_uncertainty'] for r in rows),
        statuses=dict(Counter(v.get('status',v.get('state')) for r in rows for v in r['verification_results'])))
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False))
    return 0

if __name__=='__main__':raise SystemExit(main())
