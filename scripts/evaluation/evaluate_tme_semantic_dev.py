#!/usr/bin/env python3
"""DEV-only evaluation through the existing accepted-input adapter and audit_tme.

No holdout reader or automatic promotion. Labels are joined only after audits.
Run from a clean-isolated source checkout with --data-root pointing at the frozen
synthetic demo. --replay reuses responses for adapter development, without calls.
"""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(SOURCE/'app'))
from confia_lean_auditor.student_claims import semantic as sem
from confia_lean_auditor.tme.accepted_audit import split_accepted_items
from confia_lean_auditor.submission_audits.schemas import AuditSource
from confia_lean_auditor.tme.registry import audit_tme


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def metrics(result,observations=()):
    audit=result['bridge']['auditor'];evidence=result['bridge']['evidence']['obligations']
    semantic_ids={r['record_id'] for r in audit['records'] if r['provenance']['extraction_method']==sem.VERSION}
    semantic_facts=[f for f in audit['facts'] if semantic_ids.intersection(f['source_claim_ids'])]
    states=Counter(e['status'] for e in evidence)
    events=[e for obs in observations for e in obs['events']]
    return dict(score=result['score'],needs_review=result['assessment']['needs_review'],
        obligations=len(evidence),supported=states['supported'],indeterminate=states['indeterminate'],
        decided_obligations=states['supported']+states['refuted'],technical_errors=states['technical_error'],
        primary_coverage=(states['supported']+states['refuted'])/len(evidence) if evidence else 0,
        candidates=sum(len(o['candidates']) for o in observations),grounded=sum(e['grounding']=='grounded' for e in events),
        rejected_by_context_gate=sum(e.get('context_rejected',e['reason']=='context_gate') for e in events),
        canonicalized=sum(e['canonicalized'] for e in events),
        unresolved=sum(not e['attributable'] for e in events),
        semantic_records=len(semantic_ids),converted_to_fact_result=len(semantic_facts),
        verified=sum(f['verification']['status']=='verified' for f in semantic_facts),
        refuted=sum(f['verification']['status']=='refuted' for f in semantic_facts),
        semantic_supported=sum(e['status']=='supported' and bool(semantic_ids.intersection(e['source_claim_ids'])) for e in evidence),
        deterministic_fact_results=len(audit['facts'])-len(semantic_facts),
        semantic_fact_ids=[f['fact_id'] for f in semantic_facts],
        unavailable_interpretations=sum(o['provider'].get('status')!='completed' for o in observations))


def summarize(rows,key):
    ms=[r[key] for r in rows];numeric=[(r[key]['score'],r['synthetic_expected_score']) for r in rows if r[key]['score'] is not None]
    errors=[a-b for a,b in numeric];den=len(errors)
    count_keys=('obligations','supported','indeterminate','decided_obligations','technical_errors','candidates','grounded','rejected_by_context_gate','canonicalized','unresolved',
        'semantic_records','converted_to_fact_result','verified','refuted','semantic_supported','deterministic_fact_results','unavailable_interpretations')
    result={k:sum(m[k] for m in ms) for k in count_keys}
    result.update(cases=len(rows),numeric_scores=den,null_scores=len(rows)-den,needs_review=sum(m['needs_review'] for m in ms),
        synthetic_mae=sum(abs(e) for e in errors)/den if den else None,bias=sum(errors)/den if den else None,
        exact_match=sum(e==0 for e in errors)/den if den else None,within_1=sum(abs(e)<=1 for e in errors)/den if den else None,
        within_2=sum(abs(e)<=2 for e in errors)/den if den else None)
    result['primary_coverage']=result['decided_obligations']/result['obligations']
    result['semantic_coverage']=result['semantic_supported']/result['obligations']
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',type=Path)
    args=parser.parse_args();root=args.data_root;out=args.output;out.mkdir(parents=True,exist_ok=True)
    frozen=root/'artifacts/evaluations/tme_semantic_understanding_01'
    ids=set(json.loads((frozen/'dev_ids.json').read_text()))
    assert len(ids)==25
    baseline={r['solution_id']:r for r in json.loads((frozen/'dev_baseline_results.json').read_text())}
    prior=[json.loads(line) for line in (root/'artifacts/evaluations/tme_synthetic_demo_20261102_000041/audit_results.jsonl').read_text().splitlines()]
    sources=[]
    for row in prior:
        if row['solution_id'] not in ids:continue  # Filter BEFORE opening any source.
        raw=json.loads((root/'runtime/submission_audits'/(row['audit_run_id']+'.json')).read_text())
        source=AuditSource.model_validate(raw['source']);items,warnings,_=split_accepted_items(source)
        problem='TME2_P1_PILOT' if row['problem_id']=='TME2026P1' else row['problem_id']
        framed=''.join('['+k+']\n'+items[k]+'\n\n' for k in 'abcd' if k in items)
        sources.append((row,source,items,warnings,problem,framed,raw['result']['assessment']['solution_id']))
    assert {s[0]['solution_id'] for s in sources}==ids
    config=json.dumps(sem.configuration(),sort_keys=True)
    if args.replay:
        responses=json.loads(args.replay.read_text())
        assert responses['configuration']==json.loads(config),'Replay requires the same prompt/model/parameters'
        cached=responses['responses']
    else:
        def extract(entry):
            row,source,items,warnings,problem,framed,_=entry
            if not framed.strip():return row['solution_id'],dict(candidates=[],provider={'status':'skipped_empty_input'},problem_id=problem,source_sha256=sem.sha(framed))
            cs,provider=sem.request_candidates(problem,sem.statement_for(problem),framed,config)
            print('EXTRACT',row['solution_id'],len(cs),provider.get('status'),flush=True)
            return row['solution_id'],dict(candidates=[c.model_dump() for c in cs],provider=provider,problem_id=problem,source_sha256=sem.sha(framed))
        with ThreadPoolExecutor(max_workers=3) as pool:cached=dict(pool.map(extract,sources))
        write(out/'dev_provider_responses.json',dict(configuration=json.loads(config),responses=cached))
    lookup={(r['problem_id'],r['source_sha256']):r for r in cached.values()}
    def replay(problem,statement,source,configuration):
        assert configuration==config
        r=lookup[(problem,sem.sha(source))]
        return tuple(sem.SemanticClaimCandidate.model_validate(c) for c in r['candidates']),r['provider']
    sem.request_candidates=replay
    comparisons=[];full=[];logs=[]
    for row,source,items,warnings,problem,framed,solution in sources:
        identifier=row['solution_id'];runs={}
        for phase in ('normalization_only','after'):
            os.environ['CONFIA_TME_SEMANTIC_ENABLED']='1' if phase=='after' else '0';sem.reset_observations()
            bridge,audit=audit_tme(source.problem_id,items,solution_id=solution,use_lean=True)
            result=dict(solution_id=identifier,problem_id=source.problem_id,score=float(audit.score) if audit.score is not None else None,
                assessment=audit.model_dump(mode='json'),bridge=bridge.model_dump(mode='json'),input_warnings=warnings)
            obs=sem.observations();runs[phase]=metrics(result,obs)
            if phase=='after':
                full.append(result)
                logs.extend(dict(solution_id=identifier,**o) for o in obs)
        before=metrics(baseline[identifier])
        old={e['obligation_id'] for e in baseline[identifier]['bridge']['evidence']['obligations'] if e['status']=='supported'}
        new={e['obligation_id'] for e in result['bridge']['evidence']['obligations'] if e['status']=='supported'}
        comparisons.append(dict(solution_id=identifier,problem_id=source.problem_id,before=before,**runs,
            obligations_newly_supported=sorted(new-old),obligations_lost=sorted(old-new),input_warnings=warnings,
            mapped_item_ids=list(items),empty_mapped_input=not bool(framed.strip())))
        write(out/'dev_after_results.json',full)
        (out/'semantic_candidates.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in logs))
        print('AUDIT',identifier,before['score'],runs['normalization_only']['score'],runs['after']['score'],flush=True)
    # Synthetic labels are analysis-only and enter after all interpretations/audits.
    labels={r['solution_id']:r['synthetic_expected_score'] for line in (root/'datasets/solucoes_tme2026/solucoes_tme2026.jsonl').read_text().splitlines()
            if (r:=json.loads(line))['solution_id'] in ids}
    for r in comparisons:r['synthetic_expected_score']=labels[r['solution_id']]
    write(out/'dev_before_after.json',comparisons)
    summary={phase:summarize(comparisons,phase) for phase in ('before','normalization_only','after')}
    summary['by_problem']={p:{phase:summarize([r for r in comparisons if r['problem_id']==p],phase) for phase in ('before','normalization_only','after')}
                           for p in sorted({r['problem_id'] for r in comparisons})}
    summary['metric_definitions']={'primary_coverage':'(supported + refuted obligations) / all obligations; excludes technical_error, includes alternative-path obligations',
        'semantic_coverage':'supported obligations linked to at least one semantic record / all obligations',
        'verified_refuted':'FactResults linked to semantic records, not LLM judgments',
        'unresolved':'semantic candidates not attributable after all gates',
        'score_metrics_denominator':'numeric scores only, separately for each phase; paired comparison also available in dev_before_after'}
    write(out/'dev_summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('by_problem','metric_definitions')},indent=2))

if __name__=='__main__':main()
