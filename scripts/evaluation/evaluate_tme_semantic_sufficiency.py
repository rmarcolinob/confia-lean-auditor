#!/usr/bin/env python3
"""Independent gate over the 25 frozen Hybrid01 DEV sources/candidates. No HOLDOUT loader."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'app'))
spec=importlib.util.spec_from_file_location('hybrid_runner',Path(__file__).with_name('evaluate_tme_hybrid_grader.py'))
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
from confia_lean_auditor.student_claims import semantic_sufficiency as sem
from confia_lean_auditor.student_claims.hybrid_semantic import SemanticObligationJudgment,config_for
from confia_lean_auditor.student_claims.sufficiency_context import annotated_units
from confia_lean_auditor.student_claims.sufficiency_requirements import requirements
from confia_lean_auditor.tme.sufficiency_experiment import run_sufficiency_shadow
from confia_lean_auditor.rubric.pauta.models import PautaEvidence
from confia_lean_auditor.rubric.pauta.engine import PautaEngine
from confia_lean_auditor.tme.hybrid_grader import POLICY as ENGINE_POLICY
OUT=ROOT/'artifacts/evaluations/tme_semantic_sufficiency_01';PRIOR=old.OUT
read=old.read;sha=old.old.sha
POLICY=dict(minimum_coverage=0.5,minimum_improved_problems=4,known_false_credit_eliminated=15,known_wrong_links_eliminated=6,
    new_known_false_attribution=0,negative_context_failures=0,mathematical_regressions=0,
    model='gpt-4o-mini-2024-07-18',holdout='NEVER_READ',first_evaluator='reuse_frozen_Hybrid01',
    active='only on all gates plus reviewed precision; same code/prompt/model/parameters')

def write(name,v):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def rows(name,rs):
    (OUT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs))

def cases():return old.old.sources()

def prior(c):return read(PRIOR/f"shadow/{c['solution_id']}.json")

def candidates(r):return tuple(SemanticObligationJudgment.model_validate(j) for j in r['judgments'])

def freeze():
    paths={*ROOT.glob('app/confia_lean_auditor/**/*.py'),*ROOT.glob('tests/test*.py'),*ROOT.glob('examples/pautas/tme2*.json'),
        *ROOT.glob('problems/TME2026P[1-5]/problem.json'),Path(__file__),ROOT/'tests/fixtures/tme_semantic_sufficiency_dev.json'}
    value=dict(configuration=sem.configuration(),policy=POLICY,
      source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},
      previous_results={p.name:sha(p) for p in sorted((PRIOR/'shadow').glob('*.json'))},
      dev_ids_sha256=sha(old.old.PRIOR/'dev_ids.json'),diagnosis_sha256=sha(old.old.DIAG/'cases_analysis.json'),
      prepared_hashes={str(p.relative_to(OUT)):sha(p) for folder in ['prepared_payloads','schemas','evidence_units','requirements'] for p in sorted((OUT/folder).glob('*.json'))})
    p=OUT/'experiment_freeze.json'
    if p.exists():assert read(p)==value,'Frozen code/input/config changed'
    else:write('experiment_freeze.json',value)
    return value

def prepare():
    assert not (OUT/'experiment_freeze.json').exists()
    cs=cases();gate=sem.SemanticSufficiencyGate();requested=local_count=0;candidate_rows=[];link_rows=[]
    for c in cs:
        sid=c['solution_id'];r=prior(c);js=candidates(r)
        payload,local,links=gate.prepare(c['problem_id'],c['solution_text'],js)
        write(f'prepared_payloads/{sid}.json',payload);write(f'schemas/{sid}.json',sem.response_schema(payload))
        write(f'evidence_units/{sid}.json',annotated_units(c['solution_text']))
        write(f'requirements/{c["problem_id"]}.json',requirements(c['problem_id']))
        requested+=bool(payload['obligations']);local_count+=len(local)
        candidate_rows.extend(dict(solution_id=sid,problem_id=c['problem_id'],first_evaluator_reused=True,**j.model_dump(mode='json')) for j in js)
        link_rows.extend(dict(solution_id=sid,problem_id=c['problem_id'],**l) for l in links)
    rows('semantic_candidates.jsonl',candidate_rows);rows('item_linkage.jsonl',link_rows)
    write('promotion_policy.json',POLICY)
    write('preflight.json',dict(dev_cases=25,first_evaluator_api_calls=0,gate_api_calls_planned=requested,
        valid_first_responses=21,invalid_first_responses=4,semantic_satisfied=471,local_preflight_rejections=local_count,
        model=sem.configuration()['model'],store=False,retries=0,endpoint='https://api.openai.com/v1',holdout_processed=0))
    freeze();print(json.dumps(read(OUT/'preflight.json'),ensure_ascii=False,indent=2))

def shadow():
    freeze();assert not list((OUT/'responses').glob('*.json')),'No repeat live calls'
    def request(c):
        sid=c['solution_id'];payload=read(OUT/f'prepared_payloads/{sid}.json')
        ds,meta=sem.SemanticSufficiencyGate().evaluate(payload)
        write(f'responses/{sid}.json',dict(solution_id=sid,source_sha256=c['source_sha256'],payload_sha256=sha(OUT/f'prepared_payloads/{sid}.json'),
              decisions=[d.model_dump(mode='json') for d in ds],provider=meta))
        print('SUFFICIENCY',sid,meta['status'],len(ds),meta.get('reason',''),flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for f in as_completed([pool.submit(request,c) for c in cases()]):f.result()
    replay()

def replay():
    freeze();rs=[]
    for c in cases():
        sid=c['solution_id'];r=prior(c);raw=read(OUT/f'responses/{sid}.json')
        assert raw['source_sha256']==c['source_sha256'] and raw['payload_sha256']==sha(OUT/f'prepared_payloads/{sid}.json')
        def provider(payload):
            assert payload==read(OUT/f'prepared_payloads/{sid}.json')
            return tuple(sem.SufficiencyDecision.model_validate(d) for d in raw['decisions']),raw['provider']
        primary=old.old.PautaBridgeResult.model_validate(r['primary_bridge'])
        audited=old.old.PautaBridgeResult.model_validate(r['audit_bridge'])
        result=run_sufficiency_shadow(c['problem_id'],c['solution_text'],candidates(r),primary,audited,provider=provider,
            first_provider_ok=r['provider']['status']=='completed')
        row=dict(solution_id=sid,problem_id=c['problem_id'],source_sha256=c['source_sha256'],hybrid_shadow=True,
            previous_potential_assessment=r['potential_assessment'],baseline_assessment=r['baseline_assessment'],
            evidence=result.evidence.model_dump(mode='json'),reconciliation=result.reconciliation,
            sufficiency_decisions=[d.model_dump(mode='json') for d in result.decisions],item_linkage=result.linkage,
            potential_assessment=result.potential_assessment.model_dump(mode='json'),audit_only_assessment=result.audit_only_assessment.model_dump(mode='json'),
            semantic_only_points=float(result.semantic_only_points),provider=result.provider,
            audit_reused_from='tme_hybrid_grader_01',first_provider_status=r['provider']['status'])
        write(f'shadow/{sid}.json',row);rs.append(row)
        print('SHADOW',sid,row['potential_assessment']['score'],flush=True)
    summarize(rs);freeze()

def summarize(rs):
    cs=cases();apparent={(c['solution_id'],o['obligation_id']) for c in cs for o in c['obligations'] if o['apparently_satisfied']=='sim'}
    trace=[dict(solution_id=r['solution_id'],problem_id=r['problem_id'],**t) for r in rs for t in r['reconciliation']]
    positive={(t['solution_id'],t['obligation_id']) for t in trace if t['decision']=='supported'}
    old_positive={(c['solution_id'],t['obligation_id']) for c in cs for t in prior(c)['reconciliation'] if t['decision']=='supported'}
    math_before={(c['solution_id'],t['obligation_id'],t['decision']) for c in cs for t in prior(c)['reconciliation']
                 if t['reconciled_evidence']['origin']!='semantic' and t['decision'] in {'supported','refuted'}}
    math_after={(t['solution_id'],t['obligation_id'],t['decision']) for t in trace if t['reconciled_evidence']['origin']!='semantic' and t['decision'] in {'supported','refuted'}}
    historical={r['solution_id']:r for r in read(old.old.PRIOR/'dev_after_results.json')}
    histpos={(sid,e['obligation_id']) for sid,r in historical.items() for e in r['bridge']['evidence']['obligations'] if e['status']=='supported'}
    byproblem={}
    for p in sorted({c['problem_id'] for c in cs}):
        ids={c['solution_id'] for c in cs if c['problem_id']==p};sub=lambda s:{k for k in s if k[0] in ids}
        byproblem[p]=dict(apparent=len(sub(apparent)),old_hybrid_among_409=len(sub(old_positive&apparent)),
            new_among_409=len(sub(positive&apparent)),historical_among_409=len(sub(histpos&apparent)),
            new_supported=len(sub(positive)),tiers=dict(Counter(t['evidence_tier'] for t in trace if t['problem_id']==p)))
    ds=[dict(solution_id=r['solution_id'],**d) for r in rs for d in r['sufficiency_decisions']]
    required=read(ROOT/'tests/fixtures/tme_semantic_sufficiency_dev.json');lookup={(t['solution_id'],t['obligation_id']):t for t in trace}
    checks=[dict(solution_id=c['solution_id'],obligation_id=c['obligation_id'],error_class=c['error_class'],kind=c['historical_kind'],
        eliminated=lookup[(c['solution_id'],c['obligation_id'])]['decision']!='supported',
        result=lookup[(c['solution_id'],c['obligation_id'])]) for c in required]
    counts={kind:dict(total=sum(c['kind']==kind for c in checks),eliminated=sum(c['kind']==kind and c['eliminated'] for c in checks)) for kind in ['FALSE_CREDIT','FALSE_ATTRIBUTION']}
    for v in counts.values():v['remaining_rate']=(v['total']-v['eliminated'])/v['total']
    write('false_credit_regressions.json',dict(known_dev_controls=counts,cases=checks,
        rate_scope='Rates on the 15 known false-credit obligations and 6 known wrong-link obligations, not an overall precision estimate.'))
    summary=dict(cases=25,semantic_candidates=471,valid_first_judgments=543,first_evaluator_api_calls=0,
        gate_api_calls=sum(r['provider'].get('api_calls',0) for r in rs),gate_provider_statuses=dict(Counter(r['provider']['status'] for r in rs)),
        sufficiency_states=dict(Counter(d['sufficiency'] for d in ds)),sufficiency_reasons=dict(Counter(d['reason_code'] for d in ds)),
        evidence_tiers=dict(Counter(t['evidence_tier'] for t in trace)),reconciled_states=dict(Counter(t['decision'] for t in trace)),
        old_hybrid_coverage=268/409,new_coverage=len(positive&apparent)/409,denominator=409,
        old_hybrid_among_409=268,new_among_409=len(positive&apparent),total_supported=len(positive),
        supported_outside_apparent=len(positive-apparent),new_supported_vs_hybrid=sorted(positive-old_positive),
        improved_problems_vs_historical=sum(v['new_among_409']>v['historical_among_409'] for v in byproblem.values()),
        mathematical_evidence_lost=sorted(math_before-math_after),needs_review=sum(r['potential_assessment']['needs_review'] for r in rs),
        semantic_only_potential_points=sum(r['semantic_only_points'] for r in rs),
        audit_only_known_points=sum(float(r['audit_only_assessment']['known_points']) for r in rs),
        potential_known_points=sum(float(r['potential_assessment']['known_points']) for r in rs),
        known_dev_controls=counts,holdout_processed=0,existing_cases_modified=0)
    write('coverage_before_after.json',summary);write('summary_by_problem.json',byproblem)
    rows('sufficiency_decisions.jsonl',ds);rows('reconciliation.jsonl',trace)
    rows('shadow_results.jsonl',[{k:v for k,v in r.items() if k not in {'reconciliation','sufficiency_decisions','item_linkage','provider'}} for r in rs])
    rows('active_dev_results.jsonl',[])
    labels={r['solution_id']:r['synthetic_expected_score'] for r in read(old.old.PRIOR/'dev_before_after.json')}
    comparisons=[dict(solution_id=r['solution_id'],baseline_score=r['baseline_assessment']['score'],previous_shadow_score=r['previous_potential_assessment']['score'],
        potential_score=r['potential_assessment']['score'],synthetic_expected_score=labels[r['solution_id']],active_score=None) for r in rs]
    paired=[r for r in comparisons if r['potential_score'] is not None and r['previous_shadow_score'] is not None]
    write('before_after.json',dict(cases=comparisons,paired_n=len(paired),new_shadow=old.metrics(paired,'potential_score'),
        previous_shadow=old.metrics(paired,'previous_shadow_score'),baseline=old.metrics(paired,'baseline_score'),active_status='NOT_RUN'))
    write('GO_NO_GO.json',dict(decision='PENDING_REVIEW',active_status='NOT_RUN',holdout_processed=0))
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)

def gate():
    freeze();summary=read(OUT/'coverage_before_after.json');review=read(OUT/'manual_review.json');tests=read(OUT/'regression_summary.json')
    known=all(v['eliminated']==v['total'] for v in summary['known_dev_controls'].values())
    checks=dict(known_failures_eliminated=known,coverage=summary['new_coverage']>=POLICY['minimum_coverage'],
        problems=summary['improved_problems_vs_historical']>=4,math_preserved=not summary['mathematical_evidence_lost'],
        regressions=tests['passed'],review=review['passed'] and review['new_known_false_attribution']==0)
    passed=all(checks.values())
    write('GO_NO_GO.json',dict(decision='GO_FOR_HOLDOUT' if passed else 'NO_GO_FOR_HOLDOUT',checks=checks,shadow_gate_passed=passed,
        active_status='READY' if passed else 'NOT_RUN',holdout_processed=0,findings=review['findings']))
    print(json.dumps(read(OUT/'GO_NO_GO.json'),ensure_ascii=False,indent=2))

def activate():
    freeze();decision=read(OUT/'GO_NO_GO.json');assert decision['shadow_gate_passed']
    active=[]
    for c in cases():
        r=read(OUT/f"shadow/{c['solution_id']}.json");ev=PautaEvidence.model_validate(r['evidence'])
        assessment=PautaEngine().evaluate(config_for(c['problem_id']),ev,evidence_policy=ENGINE_POLICY)
        assert assessment.model_dump(mode='json')==r['potential_assessment']
        active.append(dict(solution_id=c['solution_id'],assessment=assessment.model_dump(mode='json'),isolated_dev=True))
    rows('active_dev_results.jsonl',active);decision['active_status']='COMPLETED';write('GO_NO_GO.json',decision);freeze()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','shadow','replay','gate','activate']);globals()[p.parse_args().mode]()
