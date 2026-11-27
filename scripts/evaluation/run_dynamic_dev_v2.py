"""Offline paired component experiment. Never reads or executes HOLDOUT_V1 cases."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from datetime import datetime, timezone
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[2]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(rows, stage):
    eligible = [r for r in rows if r['eligibility'] != 'BENCHMARK_ADJUDICATION_REQUIRED']
    valid = [r for r in eligible if r[stage]['points'] is not None]
    tp = sum(r[stage]['points'] is not None and r[stage]['points'] > 0 and r['gold_points'] > 0 for r in eligible)
    fp = sum(r[stage]['points'] is not None and r[stage]['points'] > 0 and r['gold_points'] == 0 for r in eligible)
    positives = sum(r['gold_points'] > 0 for r in eligible)
    auto = [r for r in eligible if not r[stage]['review_required']]
    unsafe = [r for r in auto if r[stage]['points'] != r['gold_points']]
    ratio = lambda a,b: a / b if b else None
    return dict(N=len(eligible),N_defined=len(valid),abstentions=len(eligible)-len(valid),
        precision=ratio(tp,tp+fp),recall=ratio(tp,positives),
        false_credit_count=sum(r[stage]['points']>r['gold_points'] for r in valid),
        false_credit_rate=ratio(sum(r[stage]['points']>r['gold_points'] for r in valid),len(eligible)),
        missed_credit_count=sum(r[stage]['points']<r['gold_points'] for r in valid),
        missed_credit_rate=ratio(sum(r[stage]['points']<r['gold_points'] for r in valid),len(eligible)),
        point_MAE=ratio(sum(abs(r[stage]['points']-r['gold_points']) for r in valid),len(valid)),
        over_credit_points=sum(max(r[stage]['points']-r['gold_points'],0) for r in valid),
        under_credit_points=sum(max(r['gold_points']-r[stage]['points'],0) for r in valid),
        gold_points=sum(r['gold_points'] for r in eligible),points=sum(r[stage]['points'] for r in valid) if len(valid)==len(eligible) else None,
        review_rate=ratio(sum(r[stage]['review_required'] for r in eligible),len(eligible)),
        automation_count=len(auto),automation_coverage=ratio(len(auto),len(eligible)),
        unsafe_automation_count=len(unsafe),unsafe_automation_rate=ratio(len(unsafe),len(auto)),
        material_unsafe_count=sum(abs(r[stage]['points']-r['gold_points'])>=1 for r in unsafe))


def compare(before, after):
    old={(r['profile'],r['case_id']):r for r in before['rows']}
    result={}
    for profile in ['FORMATIVE_LIST','SCHOOL_EXAM']:
        result[profile]={}
        for stage in ['G0','G2']:
            pairs=[(old[(r['profile'],r['case_id'])],r) for r in after['rows'] if r['profile']==profile and r['eligibility']=='PRIMARY']
            diffs=[(abs(a[stage]['points']-a['gold_points']),abs(b[stage]['points']-b['gold_points'])) for a,b in pairs]
            result[profile][stage]=dict(N=len(pairs),better=sum(y<x for x,y in diffs),worse=sum(y>x for x,y in diffs),tie=sum(y==x for x,y in diffs),
                recovered_under_credit_points=sum(max(a['gold_points']-a[stage]['points'],0)-max(b['gold_points']-b[stage]['points'],0) for a,b in pairs),
                new_false_credits=sum(a[stage]['points']<=a['gold_points'] and b[stage]['points']>b['gold_points'] for a,b in pairs),
                review_to_automatic=sum(a[stage]['review_required'] and not b[stage]['review_required'] for a,b in pairs),
                automatic_to_review=sum(not a[stage]['review_required'] and b[stage]['review_required'] for a,b in pairs))
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--implementation',choices=['baseline','current'],required=True)
    parser.add_argument('--label',required=True)
    parser.add_argument('--family',choices=['substitution','method','all'],default='all')
    args=parser.parse_args()
    if not args.label.replace('-','').replace('_','').isalnum():raise ValueError('invalid label')
    impl=ROOT/'artifacts/dynamic_r1/baseline_source' if args.implementation=='baseline' else ROOT
    sys.path.insert(0,str(impl/'app'))
    os.environ['CONFIA_LEAN_AUDITOR_ROOT']=str(impl)
    from confia_lean_auditor.dynamic.grader import DynamicSolutionGrader,criterion_policy
    from confia_lean_auditor.dynamic.grading_models import DynamicGradingContext
    from confia_lean_auditor.dynamic.models import RubricContent
    from confia_lean_auditor.dynamic.reviewer import blind_input,IndependentDynamicReviewer
    from confia_lean_auditor.dynamic.review_comparison import compare_review
    from confia_lean_auditor.dynamic.reconciliation import reconcile_criteria
    from confia_lean_auditor.dynamic.preparation_models import GenerationProvenance
    from confia_lean_auditor.submissions.schemas import TranscriptionSegment
    from confia_lean_auditor.submissions.integrity import canonical_sha256
    class Carrier(SimpleNamespace):
        def model_dump(self,**kw):
            def dump(x):
                if hasattr(x,'model_dump'):return x.model_dump(**kw)
                if isinstance(x,list):return [dump(y) for y in x]
                return x
            return {k:dump(v) for k,v in vars(self).items()}
    class ScopedMaxFixture:
        """Fixed before baseline; same implementation at all stages; never gets gold/G0."""
        def generate(self,payload,schema):
            rubric=RubricContent.model_validate(payload['approved_rubric'])
            types={'substitution':{'SUBSTITUTION'},'roots':{'ROOT','ROOTS','FORMULA'},'method':{'TRANSFORMATION','FORMULA','ROOT','ROOTS'},'factorization':{'TRANSFORMATION','ROOT','ROOTS'},'transformation':{'TRANSFORMATION'}}
            proposals=[]
            for c in rubric.criteria:
                policy,_=criterion_policy(c)
                refs=[x['claim_id'] for x in payload['mathematical_evidence'] if x['claim_type'] in types.get(policy,set()) and x['adoption']=='ADOPTED']
                proposals.append(dict(criterion_id=c.criterion_id,assessment='COMPLETE',proposed_points=str(c.max_points),claim_ids=refs,explanation='Fixed scoped-max DEV fixture; no access to gold or G0.',uncertainty=[]))
            raw=dict(detected_strategy='rubric-scoped evidence',alternative_strategy=False,additional_claims=[],criterion_reviews=proposals,warnings=[])
            text=json.dumps(raw,ensure_ascii=False)
            return schema.model_validate(raw),GenerationProvenance(response_id=None,code_sha=None,provider='synthetic-dev-v2',requested_model='not-an-LLM',returned_model='rubric-scoped-max.v1',reasoning_effort=None,prompt_version='dev-v2-scoped-max.v1',schema_version=schema.__name__+'.v1',input_sha256=canonical_sha256(payload),output_sha256=canonical_sha256(text),created_at=datetime.now(timezone.utc),max_output_tokens=10000,raw_output=text)
    data=ROOT/'benchmarks/dynamic/dev_v2/cases.json';protocol=ROOT/'benchmarks/dynamic/dev_v2/protocol.json'
    prereg=json.loads(protocol.read_text());assert digest(data)==prereg['dataset_sha256']
    spec=json.loads(data.read_text());selected=[c for c in spec['cases'] if args.family=='all' or c['family']==args.family]
    runtime=ROOT/'artifacts/dynamic_r1/runs'/args.label
    runtime.mkdir(parents=True,exist_ok=False)
    output=ROOT/'docs/audits/assets/confia-dynamic-r1-dev-v2'/f'{args.label}.json'
    assert not output.exists(),'Immutable run label already used'
    source_hashes={str(p.relative_to(impl)):digest(p) for p in sorted((impl/'app').rglob('*.py'))}
    rows=[]
    for c in selected:
        assert hashlib.sha256(c['solution'].encode()).hexdigest()==c['source_sha256']
        token=hashlib.sha256(c['case_id'].encode()).hexdigest()[:32]
        context=DynamicGradingContext(problem_id='dyn_'+token,package_id='dpkg_'+token,package_version=1,package_sha256='a'*64,statement_version=1,statement_sha256=canonical_sha256(c['statement']),preparation_id='dprep_'+token,preparation_version=1,preparation_sha256='b'*64,rubric_id='drub_'+token,rubric_version=1,rubric_sha256=canonical_sha256(c['criterion']))
        statement=Carrier(statement=c['statement'],version_number=1)
        rubric=RubricContent(max_score=c['max_points'],criteria=[c['criterion']])
        preparation=Carrier(status='READY_FOR_REVIEW',proposal=Carrier(candidate_reference_solutions=[],alternative_strategies=[]),analysis=Carrier(verifier_plan=[]))
        source=Carrier(solution_text=c['solution'],source_hash=c['source_sha256'],transcription_id='tr_'+token,revision_number=1,problem_id=context.problem_id,provenance=Carrier(revision=Carrier(segments=[TranscriptionSegment(segment_id='text:0',page_index=0,order=0,kind='text',text=c['solution'])])))
        grader=DynamicSolutionGrader().grade(source,statement,rubric,preparation,context,runtime/c['case_id'])
        payload,equation,claims=blind_input(source,statement,rubric,preparation,context)
        phase=IndependentDynamicReviewer(ScopedMaxFixture()).analyze(payload,equation,claims,rubric)
        comparison=compare_review(grader,phase,rubric,c['solution'])
        review=Carrier(status='COMPLETED',phase_a=phase,comparison=comparison)
        for profile in spec['profiles']:
            reconciled=reconcile_criteria(grader,review,statement,rubric,c['solution'],profile)
            gd=grader.decisions[0];rv=phase.criterion_reviews[0];rc=reconciled[0]
            rows.append(dict(case_id=c['case_id'],pair_id=c['pair_id'],family=c['family'],variant=c['variant'],eligibility=c['eligibility'],profile=profile,gold_points=float(c['gold_points']),source_text=c['solution'],statement=c['statement'],source_sha256=c['source_sha256'],transcription_version=c['transcription_version'],rubric=c['criterion'],
                G0=dict(points=float(gd.suggested_points),review_required=gd.review_required,decision=gd.model_dump(mode='json')),
                G1=dict(points=None if rv.proposed_points is None else float(rv.proposed_points),raw_points=None if rv.provider_proposed_points is None else float(rv.provider_proposed_points),review_required=rv.review_required,phase=phase.model_dump(mode='json')),
                G2=dict(points=float(rc.reconciled_points),review_required=rc.review_required,decision=rc.model_dump(mode='json')),
                claims=[x.model_dump(mode='json') for x in grader.analysis.claims],bindings=[x.model_dump(mode='json') for x in grader.bindings],provenance=grader.analysis.provenance,context=context.model_dump(mode='json'),comparison=comparison.model_dump(mode='json')))
    groups={}
    for profile in spec['profiles']:
        groups[profile]={}
        for group in ['PRIMARY','COVERAGE_BOUNDARY','ALL_UNAMBIGUOUS','substitution','method']:
            selection=[r for r in rows if r['profile']==profile and (r['eligibility']==group or (group=='ALL_UNAMBIGUOUS' and r['eligibility']!='BENCHMARK_ADJUDICATION_REQUIRED') or r['family']==group)]
            groups[profile][group]={stage:metrics(selection,stage) for stage in ['G0','G1','G2']}
    result=dict(schema_version='dynamic-dev-v2-run.v1',label=args.label,implementation=args.implementation,created_at=datetime.now(timezone.utc).isoformat(),dataset_sha256=digest(data),protocol_sha256=digest(protocol),harness_sha256=digest(Path(__file__)),source_hashes=source_hashes,family=args.family,rows=rows,metrics=groups,holdout_executed=False,real_provider_calls=0)
    baseline=output.parent/'baseline.json'
    if baseline.exists():result['paired_vs_baseline']=compare(json.loads(baseline.read_text()),result)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'label':args.label,'cases':len(selected),'primary_G0':groups['FORMATIVE_LIST']['PRIMARY']['G0'],'primary_G2':groups['FORMATIVE_LIST']['PRIMARY']['G2']},indent=2))

if __name__=='__main__':main()
