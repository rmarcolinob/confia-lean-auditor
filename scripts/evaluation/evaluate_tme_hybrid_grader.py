#!/usr/bin/env python3
"""25 frozen DEV only. No HOLDOUT loader, production writes, or automatic retry."""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))
spec=importlib.util.spec_from_file_location('old_runner',Path(__file__).with_name('evaluate_tme_obligation_aware.py'))
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
from confia_lean_auditor.student_claims import hybrid_semantic as sem
from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.tme.hybrid_grader import run_hybrid_shadow, POLICY as EVIDENCE_POLICY
from confia_lean_auditor.rubric.pauta.engine import PautaEngine
from confia_lean_auditor.rubric.pauta.models import PautaEvidence

OUT=ROOT/'artifacts/evaluations/tme_hybrid_grader_01'
LIVE=ROOT/'artifacts/evaluations/tme_obligation_aware_live_01'
POLICY=dict(minimum_valid_responses=25, minimum_reconciled_among_409=205,
    minimum_problems_improved=4, known_false_credit=0, known_false_attribution=0,
    control_failures=0, mathematical_regressions=0,
    rationale='At least half of the 409 manually apparent obligations, versus historical 43; improvement in at least four problems, zero known safety failures, reviewed plausible sample and passing regressions.',
    active='same cached judgments, same frozen code; only isolated DEV artifacts', holdout='NEVER_READ_OR_RUN')
read=old.read

def write(name,value):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);old.write(p,value)

def rows(name,values):old.rows_write(OUT/name,values)

def hashes():
    paths={*ROOT.glob('app/confia_lean_auditor/**/*.py'),*ROOT.glob('examples/pautas/tme2*.json'),
       *ROOT.glob('problems/TME2026P[1-5]/problem.json'),*ROOT.glob('app/confia_lean_auditor/tme/references/*.json'),
       *ROOT.glob('tests/test*.py'),Path(__file__),Path(__file__).with_name('evaluate_tme_obligation_aware.py')}
    return {str(p.relative_to(ROOT)):old.sha(p) for p in sorted(paths)}

def freeze():
    value=dict(configuration=sem.configuration(),policy=POLICY,source_hashes=hashes(),
      dev_ids_sha256=old.sha(old.PRIOR/'dev_ids.json'),diagnosis_sha256=old.sha(old.DIAG/'cases_analysis.json'),
      primary_sha256={p.name:old.sha(p) for p in sorted((LIVE/'primary').glob('*.json'))},
      inputs_sha256={str(p.relative_to(OUT)):old.sha(p) for folder in ('prepared_payloads','schemas','evidence_units') for p in sorted((OUT/folder).glob('*.json'))})
    path=OUT/'experiment_freeze.json'
    if path.exists():assert read(path)==value,'Frozen source/input/config changed'
    else:write('experiment_freeze.json',value)
    return value

def primaries():
    return {p.stem:(old.PautaBridgeResult.model_validate(read(p)['bridge']),old.PautaAssessment.model_validate(read(p)['assessment']))
        for p in (LIVE/'primary').glob('*.json')}

def prepare():
    assert not (OUT/'experiment_freeze.json').exists()
    cases=old.sources();primary=primaries()
    assert set(primary)=={c['solution_id'] for c in cases}
    for c in cases:
        sid=c['solution_id'];text=c['solution_text'];p=c['problem_id']
        write(f'prepared_payloads/{sid}.json',sem.wire_payload(p,text))
        write(f'schemas/{sid}.json',sem.response_schema(p,text))
        write(f'evidence_units/{sid}.json',[u.model_dump(mode='json') for u in evidence_units(text)])
    write('promotion_policy.json',POLICY);freeze()
    print('PREPARED_FROZEN_25_DEV',sem.configuration()['model'],flush=True)

def shadow():
    freeze();cases=old.sources();primary=primaries()
    assert not list((OUT/'responses').glob('*.json')),'No repeated live calls'
    def request(c):
        js,meta=sem.request_judgments(c['problem_id'],c['solution_text'])
        raw=dict(solution_id=c['solution_id'],problem_id=c['problem_id'],source_sha256=c['source_sha256'],
            judgments=[j.model_dump(mode='json') for j in js],provider=meta)
        write(f"responses/{c['solution_id']}.json",raw)
        print('GLOBAL_JUDGE',c['solution_id'],meta['status'],meta.get('reason',''),len(js),flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs=[pool.submit(request,c) for c in cases]
        for job in as_completed(jobs):job.result()
    replay()

def replay():
    freeze();cases=old.sources();primary=primaries();results=[]
    for c in cases:
        sid=c['solution_id'];raw=read(OUT/f'responses/{sid}.json')
        assert raw['source_sha256']==c['source_sha256']
        def provider(p,t):
            assert old.legacy.sha(t)==raw['source_sha256']
            return tuple(sem.SemanticObligationJudgment.model_validate(j) for j in raw['judgments']),raw['provider']
        cached=OUT/f'shadow/{sid}.json'
        if cached.exists():
            results.append(read(cached));continue
        r=run_hybrid_shadow(c['problem_id'],c['items'],c['solution_text'],solution_id=primary[sid][1].solution_id,
            primary=primary[sid],provider=provider,use_lean=True)
        row=dict(solution_id=sid,problem_id=c['problem_id'],hybrid_shadow=True,source_sha256=c['source_sha256'],
            baseline_assessment=r.baseline_assessment.model_dump(mode='json'),
            primary_bridge=r.primary_bridge.model_dump(mode='json'),audit_bridge=r.audit_bridge.model_dump(mode='json'),
            reconciled_evidence=r.reconciled_evidence.model_dump(mode='json'),
            potential_assessment=r.potential_assessment.model_dump(mode='json'),
            audit_only_assessment=r.audit_only_assessment.model_dump(mode='json'),
            semantic_only_points=float(r.semantic_only_points),reconciliation=r.reconciliation,
            audit_telemetry=r.audit_telemetry,provider=r.provider,judgments=[j.model_dump(mode='json') for j in r.judgments])
        write(f'shadow/{sid}.json',row);results.append(row)
        print('SHADOW',sid,'potential',row['potential_assessment']['score'],'semantic_marginal',row['semantic_only_points'],flush=True)
    summarize(results,cases);freeze()

def summarize(results,cases):
    apparent={(c['solution_id'],o['obligation_id']) for c in cases for o in c['obligations'] if o['apparently_satisfied']=='sim'}
    previous={r['solution_id']:r for r in read(old.PRIOR/'dev_after_results.json')}
    historical={(sid,e['obligation_id']) for sid,r in previous.items() for e in r['bridge']['evidence']['obligations'] if e['status']=='supported'}
    trace=[dict(solution_id=r['solution_id'],problem_id=r['problem_id'],**t) for r in results for t in r['reconciliation']]
    positives={(t['solution_id'],t['obligation_id']) for t in trace if t['decision']=='supported'}
    primary={(r['solution_id'],e['obligation_id']) for r in results for e in r['primary_bridge']['evidence']['obligations'] if e['status']=='supported'}
    tiers=dict(Counter(t['evidence_tier'] for t in trace));states=dict(Counter(t['decision'] for t in trace))
    summaries={}
    for p in sorted({c['problem_id'] for c in cases}):
        ids={c['solution_id'] for c in cases if c['problem_id']==p}
        subset=lambda s:{k for k in s if k[0] in ids}
        summaries[p]=dict(apparently_satisfied=len(subset(apparent)),primary_supported=len(subset(primary)),
            historical_supported=len(subset(historical)),reconciled_supported=len(subset(positives)),
            reconciled_among_apparent=len(subset(positives&apparent)),historical_among_apparent=len(subset(historical&apparent)),
            evidence_tiers=dict(Counter(t['evidence_tier'] for t in trace if t['problem_id']==p)),
            semantic_only_points=sum(r['semantic_only_points'] for r in results if r['problem_id']==p))
    improved=sum(d['reconciled_among_apparent']>d['historical_among_apparent'] for d in summaries.values())
    valid=sum(r['provider']['status']=='completed' for r in results)
    summary=dict(hybrid_shadow=True,cases=len(results),api_calls=sum(r['provider']['api_calls'] for r in results),
        valid_responses=valid,invalid_responses=len(results)-valid,retries=0,
        semantically_satisfied=sum(j['semantic_judgment']=='satisfied' for r in results for j in r['judgments']),
        evidence_tiers=tiers,reconciled_states=states,primary_supported=len(primary),historical_supported=len(historical),
        reconciled_supported=len(positives),reconciled_supported_among_409=len(positives&apparent),
        coverage=len(positives&apparent)/409,primary_among_409=len(primary&apparent),historical_among_409=len(historical&apparent),
        supported_outside_apparent=len(positives-apparent),improved_problems=improved,
        baseline_support_lost=sorted(primary-positives),semantic_only_obligations=tiers.get('SEMANTIC_SUPPORTED',0),
        semantic_only_potential_points=sum(r['semantic_only_points'] for r in results),
        potential_known_points=sum(float(r['potential_assessment']['known_points']) for r in results),
        audit_only_known_points=sum(float(r['audit_only_assessment']['known_points']) for r in results),
        needs_review=sum(r['potential_assessment']['needs_review'] for r in results),
        holdout_texts_read=0,holdout_processed=0,existing_cases_modified=0,
        semantic_points_definition='Marginal known_points(full reconciled evidence) minus known_points(audit-only) through unchanged arithmetic engine; dependencies and max_of included, not additive attribution to individual facts.')
    summary['audit_only_point_share']=summary['audit_only_known_points']/summary['potential_known_points'] if summary['potential_known_points'] else 0
    rows('semantic_judgments.jsonl',[dict(solution_id=r['solution_id'],problem_id=r['problem_id'],**j) for r in results for j in r['judgments']])
    rows('reconciliation.jsonl',trace)
    rows('shadow_results.jsonl',[{k:v for k,v in r.items() if k not in {'primary_bridge','audit_bridge','reconciliation','judgments','audit_telemetry','provider'}} for r in results])
    write('shadow_summary.json',summary);write('summary_by_problem.json',summaries)
    write('evidence_tier_summary.json',dict(obligations=tiers,semantic_only_points=summary['semantic_only_potential_points'],
        audit_only_points=summary['audit_only_known_points'],audit_only_point_share=summary['audit_only_point_share'],definition=summary['semantic_points_definition']))
    # Synthetic labels are first consulted here AFTER interpretation/audit, never sent to model.
    labels={r['solution_id']:r['synthetic_expected_score'] for r in read(old.PRIOR/'dev_before_after.json')}
    comparisons=[dict(solution_id=r['solution_id'],problem_id=r['problem_id'],baseline_score=r['baseline_assessment']['score'],
        historical_generic_score=previous[r['solution_id']]['score'],potential_score=r['potential_assessment']['score'],
        hybrid_score=None,synthetic_expected_score=labels[r['solution_id']],semantic_only_points=r['semantic_only_points'],active_status='NOT_RUN') for r in results]
    write('before_after.json',dict(cases=comparisons,auxiliary_metrics=metrics(comparisons,'potential_score'),active_status='NOT_RUN'))
    rows('active_dev_results.jsonl',[])
    material=(valid>=POLICY['minimum_valid_responses'] and len(positives&apparent)>=POLICY['minimum_reconciled_among_409'] and improved>=4)
    write('GO_NO_GO.json',dict(decision='PENDING_REVIEW',materiality_passed=material,shadow_gate_passed=False,
        active_status='NOT_RUN',safety_review='PENDING',regression_review='PENDING',holdout_processed=0))
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)

def metrics(rows,field):
    pairs=[(float(r[field]),float(r['synthetic_expected_score'])) for r in rows if r[field] is not None]
    n=len(pairs)
    return dict(numeric_cases=n,exact=sum(a==b for a,b in pairs),within1=sum(abs(a-b)<=1 for a,b in pairs),
        within2=sum(abs(a-b)<=2 for a,b in pairs),MAE=sum(abs(a-b) for a,b in pairs)/n if n else None,
        bias=sum(a-b for a,b in pairs)/n if n else None)

def gate():
    freeze();summary=read(OUT/'shadow_summary.json');decision=read(OUT/'GO_NO_GO.json')
    review=read(OUT/'manual_review.json');reg=read(OUT/'regression_summary.json');controls=read(OUT/'false_credit_controls.json')
    safe=(review['passed'] and review['known_false_credit']==0 and review['known_false_attribution']==0 and controls['passed'])
    regok=reg['passed'] and not summary['baseline_support_lost']
    passed=decision['materiality_passed'] and safe and regok
    decision.update(decision='GO_FOR_HOLDOUT' if passed else 'NO_GO_FOR_HOLDOUT',shadow_gate_passed=passed,
        safety_review='PASSED' if safe else 'FAILED',regression_review='PASSED' if regok else 'FAILED',
        active_status='READY' if passed else 'NOT_RUN',reasons=review.get('findings',[]),
        holdout_authorization='Separate future authorization required even on GO')
    write('GO_NO_GO.json',decision);print(json.dumps(decision,ensure_ascii=False,indent=2))

def activate():
    freeze();decision=read(OUT/'GO_NO_GO.json')
    assert decision['shadow_gate_passed'] and decision['decision']=='GO_FOR_HOLDOUT'
    result=[]
    for c in old.sources():
        r=read(OUT/f"shadow/{c['solution_id']}.json")
        ev=PautaEvidence.model_validate(r['reconciled_evidence'])
        assessment=PautaEngine().evaluate(sem.config_for(c['problem_id']),ev,evidence_policy=EVIDENCE_POLICY)
        assert assessment.model_dump(mode='json')==r['potential_assessment']
        result.append(dict(solution_id=c['solution_id'],problem_id=c['problem_id'],assessment=assessment.model_dump(mode='json'),
            semantic_only_points=r['semantic_only_points'],isolated_experimental_dev=True))
    rows('active_dev_results.jsonl',result)
    before=read(OUT/'before_after.json');active={r['solution_id']:r for r in result}
    for row in before['cases']:
        row.update(hybrid_score=active[row['solution_id']]['assessment']['score'],active_status='COMPLETED')
    before.update(active_status='COMPLETED',auxiliary_metrics=metrics(before['cases'],'hybrid_score'))
    write('before_after.json',before);decision['active_status']='COMPLETED';write('GO_NO_GO.json',decision);freeze()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','shadow','replay','gate','activate'])
    globals()[parser.parse_args().mode]()
