"""Observed P3 replay, recorded providers only. This is not an independent eval."""
import argparse
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

from confia_lean_auditor.experimental.tme_semantic_formal_p3.engine import evaluate

ROOT=Path(__file__).resolve().parents[2]
GROUPS=('tme_p3_semantic_formal_dev_01','tme_p3_semantic_formal_dev_02',
        'tme_p3_semantic_robustness_01','tme_p3_semantic_safety_02','tme_p3_semantic_safety_03')

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--groups',nargs='+',choices=GROUPS,default=GROUPS)
    args=parser.parse_args()
    output=args.output.resolve()
    if output.exists():raise ValueError('output_must_be_new_preserve_previous_runs')
    historical=ROOT/'artifacts/evaluations'
    if any(output.is_relative_to((historical/g).resolve()) for g in GROUPS):
        raise ValueError('cannot_write_observed_inputs')
    inputs=[]
    for group in args.groups:
        for path in sorted((historical/group).rglob('tme_semantic_formal/*.json')):
            old=json.loads(path.read_text())
            if 'source_text' in old:inputs.append((group,path,old))
    if not inputs:raise ValueError('no_recorded_inputs')
    frozen={str(p.relative_to(ROOT)):digest(p) for _,p,_ in inputs}
    output.mkdir(parents=True)
    implementation={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'app/confia_lean_auditor/experimental/tme_semantic_formal_p3').glob('*.py')}
    started=datetime.now(timezone.utc).isoformat()
    (output/'run_manifest.json').write_text(json.dumps(dict(state='started',started=started,implementation=implementation,input_hashes=frozen,api_allowed=False),indent=2)+'\n')
    rows=[]
    with patch('openai.OpenAI',side_effect=AssertionError('API_FORBIDDEN_RECORDED_REPLAY')):
        for group,path,old in inputs:
            raw=old.get('extractor',{}).get('raw_output')
            recorded_status=old.get('extractor',{}).get('status')
            def recorded(*unused):
                if recorded_status!='completed' or raw is None:
                    raise ValueError('recorded_extraction_unavailable')
                return raw,dict(status='completed',api_calls=0,model='recorded')
            r=evaluate('multilayer-'+old['case_id'],'TME2026P3',old['source_text'],
                       extraction_provider=recorded,use_lean=True)
            assert r['extractor']['api_calls']==0
            relative=path.relative_to(historical)
            target=output/'cases'/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
            row=dict(group=group,input=str(path.relative_to(ROOT)),input_sha256=frozen[str(path.relative_to(ROOT))],
                case_id=old['case_id'],previous_score=old['score'],score=r['score'],
                delta=r['score']-old['score'],fallback=r['fallback'],previous_fallback=old['fallback'],
                technical_uncertainty=r['technical_uncertainty'],api_calls=r['extractor']['api_calls'],
                credits=[dict(rule_id=c['rule_id'],points=c['points']) for c in r['credits']],
                previous_credits=[dict(rule_id=c['rule_id'],points=c['points']) for c in old.get('credits',[])],
                statuses=dict(Counter(v['status'] for v in r['verification_results'])),
                automation=dict(Counter(d['automation_eligibility'] for d in r['automation_decisions'])),
                artifact=str(target.relative_to(output)))
            rows.append(row)
            print(old['case_id'],old['score'],'->',r['score'],'fallback',r['fallback'],flush=True)
    assert all(digest(ROOT/p)==h for p,h in frozen.items())
    assert all(digest(ROOT/p)==h for p,h in implementation.items())
    totals={g:dict(cases=sum(x['group']==g for x in rows),
                   previous=sum(x['previous_score'] for x in rows if x['group']==g),
                   current=sum(x['score'] for x in rows if x['group']==g),
                   fallbacks=sum(x['fallback'] for x in rows if x['group']==g),
                   technical=sum(x['technical_uncertainty'] for x in rows if x['group']==g)) for g in args.groups}
    summary=dict(classification='OBSERVED_REGRESSION_NOT_INDEPENDENT',
        base_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        use_lean=True,api_calls=0,implementation=implementation,started=started,finished=datetime.now(timezone.utc).isoformat(),groups=totals,rows=rows,input_hashes=frozen)
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    (output/'run_manifest.json').write_text(json.dumps(dict(state='completed',started=started,finished=summary['finished'],implementation=implementation,input_hashes=frozen,api_calls=0,api_allowed=False),indent=2)+'\n')
    print(json.dumps(totals,indent=2),flush=True)

if __name__=='__main__':main()
