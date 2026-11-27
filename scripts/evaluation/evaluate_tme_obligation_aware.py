#!/usr/bin/env python3
"""Frozen 25-DEV obligation experiment. No dataset/HOLDOUT reader exists here.

Shadow runs first and stops for safety review. --activate requires a separately
recorded passed shadow gate, unchanged source/config and clean regression review.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))
from confia_lean_auditor.student_claims import obligation_semantic as sem
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.student_claims.obligation_catalog import mathematical_obligations,internal_id
from confia_lean_auditor.tme.obligation_experiment import primary_audit,unresolved_targets,run_shadow
from confia_lean_auditor.rubric.pauta.bridge import PautaBridgeResult
from confia_lean_auditor.rubric.pauta.models import PautaAssessment

OUT=ROOT/'artifacts/evaluations/tme_obligation_aware_01'
PRIOR=ROOT/'artifacts/evaluations/tme_semantic_understanding_01'
DIAG=ROOT/'artifacts/evaluations/tme_semantic_diag_01'


def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows_write(path,rows):path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))


def source_hashes():
    files=[*ROOT.glob('app/confia_lean_auditor/**/*.py'),*ROOT.glob('examples/pautas/tme2*.json'),
           ROOT/'scripts/evaluation/evaluate_tme_obligation_aware.py',ROOT/'tests/test_obligation_semantic.py']
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}


def freeze():
    current=dict(configuration=sem.configuration(),source_hashes=source_hashes(),
                 promotion_policy_sha256=sha(OUT/'promotion_policy.json'),
                 dev_ids_sha256=sha(PRIOR/'dev_ids.json'),diagnosis_sha256=sha(DIAG/'cases_analysis.json'))
    path=OUT/'experiment_freeze.json'
    if path.exists():assert read(path)==current,'Code/prompt/config changed after freeze'
    else:write(path,current)
    return current


def sources():
    ids=read(PRIOR/'dev_ids.json');cases=read(DIAG/'cases_analysis.json')['cases']
    assert len(ids)==25 and set(ids)=={c['solution_id'] for c in cases}
    assert sum(r['apparently_satisfied']=='sim' for c in cases for r in c['obligations'])==409
    assert sum(r['confirmed_miss'] for c in cases for r in c['obligations'])==366
    for c in cases:
        assert c['source_sha256']==hashlib.sha256(c['solution_text'].encode()).hexdigest()
        assert c['mapped_source_sha256']==hashlib.sha256(c['mapped_text'].encode()).hexdigest()
        c['items']={k:c['mapped_text'][a:b] for k,(a,b) in c['mapped_item_ranges'].items()}
    return cases


def evidence_map(bridge):return {e['obligation_id']:e for e in bridge['evidence']['obligations']}


def aggregate(cases,results,prior):
    diag={(c['solution_id'],r['obligation_id']):r for c in cases for r in c['obligations']}
    satisfied={k for k,r in diag.items() if r['apparently_satisfied']=='sim'}
    misses={k for k,r in diag.items() if r['confirmed_miss']}
    all_events=[dict(solution_id=r['solution_id'],**e) for r in results for e in r['telemetry']['events']]
    all_candidates=[c for r in results for c in r['telemetry']['candidates']]
    before_supported={(sid,e['obligation_id']) for sid,r in prior.items() for e in r['bridge']['evidence']['obligations'] if e['status']=='supported'}
    primary_supported={(r['solution_id'],e['obligation_id']) for r in results for e in r['primary_bridge']['evidence']['obligations'] if e['status']=='supported'}
    potential_supported={(r['solution_id'],e['obligation_id']) for r in results for e in r['potential_bridge']['evidence']['obligations'] if e['status']=='supported'}
    facts=[dict(solution_id=r['solution_id'],**f) for r in results for f in r['potential_bridge']['auditor']['facts']]
    semfacts=[f for f in facts if any(s.startswith('semantic:') for s in f['source_claim_ids'])]
    keys_by_stage={'candidate':set(),'literal_grounded':set(),'grounded':set(),'canonicalized':set(),'attributable':set(),'FactResult':set(),'verified':set(),'potentially_mappable':set()}
    for r in results:
        sid=r['solution_id'];bridge=r['potential_bridge'];fs={f['fact_id']:f for f in bridge['auditor']['facts']};ev=evidence_map(bridge)
        for e in r['telemetry']['events']:
            key=(sid,e['obligation_id'])
            if e['evidence_present']:keys_by_stage['candidate'].add(key)
            for name in ('literal_grounded','canonicalized','attributable'):
                if e[name]:keys_by_stage[name].add(key)
            if e['grounding']=='grounded':keys_by_stage['grounded'].add(key)
            f=fs.get(ev[e['obligation_id']]['metadata']['fact_id'])
            if f and {e.get('record_id'),e.get('retained_record_id')}.intersection(f['source_claim_ids']):
                keys_by_stage['FactResult'].add(key)
                if f['verification']['status']=='verified':keys_by_stage['verified'].add(key)
                if ev[e['obligation_id']]['status']=='supported':keys_by_stage['potentially_mappable'].add(key)
    states=Counter(e['status'] for r in results for e in r['potential_bridge']['evidence']['obligations'])
    positive=set(potential_supported&satisfied)
    summary=dict(semantic_shadow=True,cases=len(cases),targets_requested=sum(len(r['telemetry']['target_obligation_ids']) for r in results),
        provider_statuses=dict(Counter(r['telemetry']['provider']['status'] for r in results)),
        candidates=len(all_candidates),evidence_present=sum(c['evidence_present'] for c in all_candidates),
        explicit_no_evidence=sum(not c['evidence_present'] for c in all_candidates),
        literal_grounded=sum(e['literal_grounded'] for e in all_events),grounded=sum(e['grounding']=='grounded' for e in all_events),
        context_rejected=sum(e['context_rejected'] for e in all_events),canonicalized=sum(e['canonicalized'] for e in all_events),
        unresolved=sum(e['evidence_present'] and not e['attributable'] for e in all_events),
        attributable=sum(e['attributable'] for e in all_events),event_reasons=dict(Counter(e['reason'] for e in all_events)),
        semantic_fact_results=len(semfacts),semantic_fact_outcomes=dict(Counter(f['verification']['status'] for f in semfacts)),
        all_fact_outcomes=dict(Counter(f['verification']['status'] for f in facts)),
        potential_decisions=dict(states),primary_supported=len(primary_supported),prior_generic_supported=len(before_supported),
        potential_supported=len(potential_supported),new_verified_vs_deterministic=len(potential_supported-primary_supported),
        recovered_prior_misses=len(potential_supported&misses),lost_prior_supported=sorted([list(k) for k in before_supported-potential_supported]),
        primary_metric={'denominator':409,'prior_generic_verified':len(before_supported&satisfied),'deterministic_verified':len(primary_supported&satisfied),
                        'shadow_verified':len(positive),'prior_generic_ratio':len(before_supported&satisfied)/409,'shadow_ratio':len(positive)/409},
        misses_366={k:len(v&misses) for k,v in keys_by_stage.items()},
        apparent_409={k:len(v&satisfied) for k,v in keys_by_stage.items()},
        shadow_scores_equal_primary=all(r['assessment']==r['primary_assessment'] for r in results),
        new_facts_sent_to_engine=0,
        notes=['All potential decisions come from the unchanged bridge; no shadow engine evaluation.',
               'Reference43/409 is the prior generic experiment; the live primary is deterministic+Unicode.',
               'Strict spans are checked in full solution_text then translated exactly to unchanged accepted item boundaries.'])
    byproblem={}
    for problem in sorted({c['problem_id'] for c in cases}):
        ids={c['solution_id'] for c in cases if c['problem_id']==problem};cohort={k for k in satisfied if k[0] in ids};ms={k for k in misses if k[0] in ids}
        byproblem[problem]=dict(apparently_satisfied=len(cohort),prior_verified=len(before_supported&cohort),primary_verified=len(primary_supported&cohort),
            shadow_verified=len(potential_supported&cohort),prior_ratio=len(before_supported&cohort)/len(cohort),shadow_ratio=len(potential_supported&cohort)/len(cohort),
            recovered_prior_misses=len(potential_supported&ms),misses={k:len(v&ms) for k,v in keys_by_stage.items()})
    return summary,byproblem


def shadow_run(*,prepare_only=False):
    OUT.mkdir(parents=True,exist_ok=True);frozen=freeze();cases=sources()
    prior={r['solution_id']:r for r in read(PRIOR/'dev_after_results.json')}
    pdir=OUT/'primary';pdir.mkdir(exist_ok=True);rdir=OUT/'responses';rdir.mkdir(exist_ok=True);sdir=OUT/'shadow';sdir.mkdir(exist_ok=True)
    primaries={}
    for c in cases:
        sid=c['solution_id'];path=pdir/(sid+'.json')
        if path.exists():
            raw=read(path);bridge=PautaBridgeResult.model_validate(raw['bridge']);assessment=PautaAssessment.model_validate(raw['assessment'])
        else:
            bridge,assessment=primary_audit(c['problem_id'],c['items'],solution_id=prior[sid]['assessment']['solution_id'],use_lean=True)
            write(path,dict(bridge=bridge.model_dump(mode='json'),assessment=assessment.model_dump(mode='json')))
        assert bridge.auditor.source_sha256==c['mapped_source_sha256']
        primaries[sid]=(bridge,assessment)
        print('PRIMARY',sid,str(assessment.score),flush=True)
    payload_dir=OUT/'prepared_payloads';payload_dir.mkdir(exist_ok=True)
    for c in cases:
        problem=internal_id(c['problem_id'])
        targets=unresolved_targets(problem,primaries[c['solution_id']][0])
        write(payload_dir/(c['solution_id']+'.json'),sem.wire_payload(problem,c['solution_text'],targets))
    if prepare_only:
        print('PREPARED_ONLY: 25 exact DEV payloads; no provider requests.',flush=True)
        return
    config=json.dumps(frozen['configuration'],sort_keys=True)
    def extract(c):
        sid=c['solution_id'];path=rdir/(sid+'.json');problem=internal_id(c['problem_id'])
        targets=unresolved_targets(problem,primaries[sid][0]);target_json=json.dumps(targets,ensure_ascii=False,sort_keys=True)
        identity=dict(problem_id=problem,source_sha256=c['source_sha256'],targets_sha256=legacy.sha(target_json),configuration_sha256=legacy.sha(config))
        if path.exists():
            raw=read(path);assert raw['identity']==identity
        else:
            candidates,meta=sem.request_candidates(problem,c['solution_text'],target_json,config)
            raw=dict(identity=identity,candidates=[x.model_dump() for x in candidates],provider=meta)
            write(path,raw)
        print('EXTRACT',sid,len(raw['candidates']),raw['provider']['status'],flush=True)
        return sid,raw
    cached={}
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs=[pool.submit(extract,c) for c in cases]
        for job in as_completed(jobs):sid,raw=job.result();cached[sid]=raw
    results=[]
    for c in cases:
        sid=c['solution_id'];raw=cached[sid];path=sdir/(sid+'.json')
        def replay(problem,source,targets,configuration):
            assert legacy.sha(configuration)==raw['identity']['configuration_sha256'] and legacy.sha(source)==raw['identity']['source_sha256']
            assert legacy.sha(targets)==raw['identity']['targets_sha256']
            return tuple(sem.ObligationEvidenceCandidate.model_validate(x) for x in raw['candidates']),raw['provider']
        if path.exists():result=read(path)
        else:
            shadow=run_shadow(c['problem_id'],c['items'],c['solution_text'],solution_id=prior[sid]['assessment']['solution_id'],
                provider=replay,primary=primaries[sid],use_lean=True)
            result=dict(solution_id=sid,problem_id=c['problem_id'],semantic_shadow=True,
                primary_bridge=shadow.primary_bridge.model_dump(mode='json'),primary_assessment=shadow.assessment.model_dump(mode='json'),
                assessment=shadow.assessment.model_dump(mode='json'),potential_bridge=shadow.potential_bridge.model_dump(mode='json'),telemetry=shadow.telemetry)
            write(path,result)
        results.append(result)
        print('SHADOW',sid,len(result['potential_bridge']['auditor']['facts']),flush=True)
        rows_write(OUT/'shadow_candidates.jsonl',[dict(solution_id=r['solution_id'],**r['telemetry']) for r in results])
    summary,byproblem=aggregate(cases,results,prior)
    write(OUT/'shadow_summary.json',summary);write(OUT/'summary_by_problem.json',byproblem)
    write(OUT/'funnel_before_after.json',dict(reference='409 apparent obligations from frozen diagnosis; no labels',
        primary_metric=summary['primary_metric'],misses_366=summary['misses_366'],apparent_409=summary['apparent_409'],active_status='NOT_RUN'))
    comparisons=[]
    for r in results:
        sid=r['solution_id'];comparisons.append(dict(solution_id=sid,problem_id=r['problem_id'],
            prior_generic_score=prior[sid]['score'],deterministic_primary_score=float(r['assessment']['score']) if r['assessment']['score'] is not None else None,
            shadow_published_score=float(r['assessment']['score']) if r['assessment']['score'] is not None else None,
            active_score=None,active_status='NOT_RUN',prior_supported=[e['obligation_id'] for e in prior[sid]['bridge']['evidence']['obligations'] if e['status']=='supported'],
            shadow_potential_supported=[e['obligation_id'] for e in r['potential_bridge']['evidence']['obligations'] if e['status']=='supported']))
    write(OUT/'dev_before_after.json',comparisons)
    (OUT/'dev_active_results.jsonl').write_text('')
    policy=read(OUT/'promotion_policy.json')['shadow_gate']
    material=summary['primary_metric']['shadow_verified']>=policy['minimum_verified_apparently_satisfied'] and summary['new_verified_vs_deterministic']>=policy['minimum_new_verified_vs_deterministic']
    write(OUT/'GO_NO_GO.json',dict(decision='PENDING_SAFETY_REVIEW' if material else 'NO_GO',
        shadow_gate_materiality_passed=material,shadow_gate_passed=False,active_status='NOT_RUN',holdout_status='NOT_RUN_PROHIBITED',
        reasons=[] if material else ['SHADOW_MATERIALITY_BELOW_FROZEN_THRESHOLD'],code_frozen=True,
        safety_review='PENDING',regression_review='PENDING'))
    assert freeze()==frozen
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)


def activate():
    # The full audited shadow bundles are replayed, without new interpretation.
    freeze();decision=read(OUT/'GO_NO_GO.json')
    assert decision['shadow_gate_passed'] is True and decision['safety_review']=='PASSED' and decision['regression_review']=='PASSED'
    from confia_lean_auditor.rubric.pauta.engine import PautaEngine
    from confia_lean_auditor.rubric.pauta import load_pauta
    from confia_lean_auditor.tme.registry import TME_PROBLEMS
    cases=sources();active=[]
    for c in cases:
        raw=read(OUT/'shadow'/(c['solution_id']+'.json'));bridge=PautaBridgeResult.model_validate(raw['potential_bridge'])
        config=load_pauta(ROOT/'examples/pautas'/TME_PROBLEMS[internal_id(c['problem_id'])])
        assessment=PautaEngine().evaluate(config,bridge.evidence)
        active.append(dict(solution_id=c['solution_id'],problem_id=c['problem_id'],score=float(assessment.score) if assessment.score is not None else None,
                           bridge=bridge.model_dump(mode='json'),assessment=assessment.model_dump(mode='json')))
    rows_write(OUT/'dev_active_results.jsonl',active)
    # DEV labels only, already separated from HOLDOUT, loaded strictly after scoring.
    labels={r['solution_id']:r['synthetic_expected_score'] for r in read(PRIOR/'dev_before_after.json')}
    assert set(labels)=={c['solution_id'] for c in cases}
    def metrics(rows):
        errors=[r['score']-labels[r['solution_id']] for r in rows if r['score'] is not None]
        states=Counter(e['status'] for r in rows for e in r['bridge']['evidence']['obligations']);n=len(errors)
        return dict(supported=states['supported'],indeterminate=states['indeterminate'],primary_coverage=(states['supported']+states['refuted'])/sum(states.values()),
            score_null=sum(r['score'] is None for r in rows),needs_review=sum(r['assessment']['needs_review'] for r in rows),
            synthetic_mae=sum(map(abs,errors))/n if n else None,synthetic_bias=sum(errors)/n if n else None,
            exact_synthetic_agreement=sum(e==0 for e in errors)/n if n else None,within_1=sum(abs(e)<=1 for e in errors)/n if n else None,within_2=sum(abs(e)<=2 for e in errors)/n if n else None)
    before=read(PRIOR/'dev_after_results.json');comparisons=read(OUT/'dev_before_after.json')
    for row,result in zip(comparisons,active):
        assert row['solution_id']==result['solution_id']
        row.update(active_score=result['score'],active_status='COMPLETED',synthetic_expected_score=labels[result['solution_id']])
    write(OUT/'dev_before_after.json',dict(cases=comparisons,before=metrics(before),after=metrics(active)))
    funnel=read(OUT/'funnel_before_after.json');funnel.update(active_status='COMPLETED',active_metrics=metrics(active));write(OUT/'funnel_before_after.json',funnel)
    bp=read(OUT/'summary_by_problem.json')
    for problem,item in bp.items():
        item['active_metrics']=metrics([r for r in active if r['problem_id']==problem])
    write(OUT/'summary_by_problem.json',bp)
    policy=read(OUT/'promotion_policy.json')['dev_go'];summary=read(OUT/'shadow_summary.json')
    gains=sum(r['shadow_verified']>r['prior_verified'] for r in bp.values())
    passed=summary['primary_metric']['shadow_verified']>=policy['minimum_verified_apparently_satisfied'] and metrics(active)['indeterminate']<=policy['maximum_indeterminate'] and gains>=policy['minimum_problems_gaining_vs_prior_generic']
    decision.update(decision='GO' if passed else 'NO_GO',active_status='COMPLETED',holdout_status='NOT_RUN_PROHIBITED',problems_gaining=gains)
    write(OUT/'GO_NO_GO.json',decision)
    assert freeze()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--activate',action='store_true')
    modes.add_argument('--prepare-only',action='store_true',help='Local primary checks and exact wire payloads; never calls a provider')
    args=parser.parse_args()
    activate() if args.activate else shadow_run(prepare_only=args.prepare_only)
