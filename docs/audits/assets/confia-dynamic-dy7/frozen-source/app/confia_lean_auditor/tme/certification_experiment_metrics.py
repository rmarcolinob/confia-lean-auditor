"""DY7 descriptive metrics. Explicit denominators, no institutional thresholds."""
from collections import Counter, defaultdict
from decimal import Decimal
import random
from .certification_metrics import comparisons, ratio

D=lambda value:Decimal(str(value))


def score_metrics(rows,stage):
    selected=[]
    for row in rows:
        e=row['dynamic_evaluation'];s=e['stages'][stage]
        if not e['exclusions'] and not s['technical_failures'] and s['score'] is not None and row.get('human_gold_score') is not None:
            selected.append(row)
    values=[dict(pred=r['dynamic_evaluation']['stages'][stage]['score'],gold=r['human_gold_score']) for r in selected]
    out=comparisons(values,'pred','gold')
    errors=[D(v['pred'])-D(v['gold']) for v in values]
    out.update(RMSE=str((sum(e*e for e in errors)/len(errors)).sqrt()) if errors else None,
        normalized_absolute_error=ratio(sum(abs(e)/D(r['max_score']) for e,r in zip(errors,selected)),len(errors)))
    return out,selected


def criterion_metrics(rows,stage):
    pairs=[]
    missing=0
    for r in rows:
        predictions={c['criterion_id']:c for c in r['dynamic_evaluation']['stages'][stage]['criteria']}
        for gold in r.get('rubric_gold',[]):
            if gold.get('adjudication_status')=='UNRESOLVED':missing+=1;continue
            p=predictions.get(gold['rubric_item_id'])
            if not p or p['points'] is None or D(p['max_points'])!=D(gold['max_points']):missing+=1;continue
            error=D(p['points'])-D(gold['gold_points'])
            pairs.append(dict(question_attempt_id=r['question_attempt_id'],criterion_id=gold['rubric_item_id'],error=str(error),
                over_credit_points=str(max(error,0)),under_credit_points=str(max(-error,0)),
                normalized_severity=str(abs(error)/D(gold['max_points'])) if D(gold['max_points']) else '0'))
    errors=[D(p['error']) for p in pairs];n=len(errors)
    return dict(N=n,missing_pairs=missing,exact_agreement=ratio(sum(e==0 for e in errors),n),point_MAE=ratio(sum(abs(e) for e in errors),n),
        false_credit_count=sum(e>0 for e in errors),false_credit_rate=ratio(sum(e>0 for e in errors),n),
        missed_credit_count=sum(e<0 for e in errors),missed_credit_rate=ratio(sum(e<0 for e in errors),n),
        over_credit_points=str(sum(max(e,0) for e in errors)),under_credit_points=str(sum(max(-e,0) for e in errors)),pairs=pairs)


def erroneous(row,stage,threshold):
    s=row['dynamic_evaluation']['stages'][stage]
    if s['score'] is None or row.get('human_gold_score') is None:return None
    if abs(D(s['score'])-D(row['human_gold_score']))>threshold:return True
    criteria=criterion_metrics([row],stage)['pairs']
    return any(abs(D(c['error']))>threshold for c in criteria)


def stage_summary(rows,stage,threshold):
    scores,valid=score_metrics(rows,stage)
    available=[r for r in rows if r['dynamic_evaluation']['stages'][stage]['score'] is not None]
    automatic=[r for r in available if not r['dynamic_evaluation']['stages'][stage]['review_required'] and not r['dynamic_evaluation']['stages'][stage]['technical_failures']]
    completed=[r for r in rows if r['dynamic_evaluation']['stages'][stage]['status']=='COMPLETED']
    reviewed=[r for r in completed if r['dynamic_evaluation']['stages'][stage]['review_required']]
    auto_valid=[r for r in valid if r in automatic];review_valid=[r for r in valid if r in reviewed]
    labelled=[r for r in valid if (r['dynamic_evaluation'].get('gold_evaluation') or {}).get('requires_review') is not None]
    escalated=[r for r in labelled if r in reviewed]
    correct=sum(r['dynamic_evaluation']['gold_evaluation']['requires_review'] for r in escalated)
    unsafe=sum(bool(erroneous(r,stage,threshold)) for r in auto_valid)
    need_review=[r for r in labelled if r['dynamic_evaluation']['gold_evaluation']['requires_review']]
    criterion_eligible=[r for r in rows if not r['dynamic_evaluation']['exclusions'] and not r['dynamic_evaluation']['stages'][stage]['technical_failures']]
    return dict(score=scores,criterion=criterion_metrics(criterion_eligible,stage),N_attempted=len(rows),N_available=len(available),N_completed=len(completed),
        N_automated=len(automatic),automation_coverage=ratio(len(automatic),len(rows)),review_rate=ratio(len(reviewed),len(completed)),
        N_gold_review_labels=len(labelled),N_escalated_with_label=len(escalated),correct_escalation=correct,unnecessary_escalation=len(escalated)-correct,
        missed_escalation=sum(r not in reviewed for r in need_review),review_precision=ratio(correct,len(escalated)),
        N_automated_with_gold=len(auto_valid),unsafe_automation_count=unsafe,unsafe_automation_rate=ratio(unsafe,len(auto_valid)),
        automated_score=score_metrics(auto_valid,stage)[0],reviewed_score=score_metrics(review_valid,stage)[0],
        technical_failures=dict(Counter(f for r in rows for f in r['dynamic_evaluation']['stages'][stage]['technical_failures'])))


def transition(rows,first,second):
    a,valid_a=score_metrics(rows,first);b,valid_b=score_metrics(rows,second)
    paired=[r for r in valid_a if r in valid_b]
    corrected=introduced=removed=recovered=agree_wrong=0
    points_removed=points_recovered=Decimal(0)
    detected=false_alarm=missed=alternative=0
    for r in paired:
        e=r['dynamic_evaluation'];x=D(e['stages'][first]['score']);y=D(e['stages'][second]['score']);gold=D(r['human_gold_score'])
        pa={p['criterion_id']:D(p['error']) for p in criterion_metrics([r],first)['pairs']}
        pb={p['criterion_id']:D(p['error']) for p in criterion_metrics([r],second)['pairs']}
        wrong_a=x!=gold or any(pa.values());wrong_b=y!=gold or any(pb.values())
        same=x==y and pa==pb
        corrected+=wrong_a and not wrong_b;introduced+=not wrong_a and wrong_b;agree_wrong+=same and wrong_a
        signal=not same or e['stages'][second]['review_required']
        detected+=wrong_a and signal;false_alarm+=not wrong_a and signal;missed+=wrong_a and not signal
        alternative+=bool(e['stages'][second].get('alternative_strategy')) and abs(y-gold)<abs(x-gold)
        for k in pa.keys() & pb.keys():
            removed+=pa[k]>0 and pb[k]<=0;recovered+=pa[k]<0 and pb[k]>=0
            points_removed+=max(max(pa[k],0)-max(pb[k],0),0)
            points_recovered+=max(max(-pa[k],0)-max(-pb[k],0),0)
    return dict(N_paired=len(paired),errors_corrected=corrected,errors_introduced=introduced,false_credit_criteria_removed=removed,
        missed_credit_criteria_recovered=recovered,over_credit_points_removed=str(points_removed),under_credit_points_recovered=str(points_recovered),
        agree_but_gold_disagrees=agree_wrong,grader_errors_detected=detected,reviewer_false_alarms=false_alarm,grader_errors_missed=missed,
        alternative_strategies_improved=alternative)


def bootstrap_mae(rows,stage,seed):
    _,valid=score_metrics(rows,stage);groups=defaultdict(list)
    for r in valid:groups[r.get('dataset_case',{}).get('group_id',r['participant_id'])].append(abs(D(r['dynamic_evaluation']['stages'][stage]['score'])-D(r['human_gold_score'])))
    n=len(groups)
    if n<20:return dict(N_groups=n,interval=None,status='PILOT_SMALL_SAMPLE',method='No interval below 20 independent groups')
    values=list(groups.values());rng=random.Random(seed);means=[]
    for _ in range(1000):
        sample=[error for _ in range(n) for error in rng.choice(values)];means.append(float(sum(sample)/len(sample)))
    means.sort()
    return dict(N_groups=n,interval=[means[24],means[974]],status='DESCRIPTIVE_INTERVAL',method='95% cluster percentile bootstrap, group_id, 1000 draws',seed=seed)


def summarize(rows,threshold=Decimal('1'),seed=20261112):
    stages={s:stage_summary(rows,s,threshold) for s in ('G0','G1','G2','G3')}
    human=[];useful=[];ratings=[]
    for r in rows:
        e=r['dynamic_evaluation'];g2=e['stages']['G2']['score'];g3=e['stages']['G3']['score']
        if g2 is not None and g3 is not None:
            human.append(D(g3)-D(g2))
            if not e['exclusions'] and e['stages']['G2']['review_required'] and r.get('human_gold_score') is not None:
                useful.append(abs(D(g3)-D(r['human_gold_score']))<abs(D(g2)-D(r['human_gold_score'])))
        rs=(e.get('gold_evaluation') or {}).get('ratings',[])
        for i,a in enumerate(rs):
            for b in rs[i+1:]:
                if a['independent'] and b['independent']:ratings.append(abs(D(a['score'])-D(b['score'])))
    technical=sum(any(s['technical_failures'] for s in r['dynamic_evaluation']['stages'].values()) for r in rows)
    credit_history=[]
    for r in rows:
        if r['dynamic_evaluation']['exclusions']:continue
        values={name:{p['criterion_id']:p for p in criterion_metrics([r],name)['pairs']} for name in ('G0','G1','G2') if not r['dynamic_evaluation']['stages'][name]['technical_failures']}
        for criterion in {k for stage in values.values() for k in stage}:
            errors={name:stage[criterion]['error'] for name,stage in values.items() if criterion in stage}
            over=[name for name,e in errors.items() if D(e)>0]
            credit_history.append(dict(question_attempt_id=r['question_attempt_id'],criterion_id=criterion,errors=errors,
                first_observed_false_credit_stage=over[0] if over else None))
    return dict(N=len(rows),stages=stages,credit_history=credit_history,exclusions=dict(Counter(x for r in rows for x in r['dynamic_evaluation']['exclusions'])),
        technical_failure_cases=technical,technical_failure_rate=ratio(technical,len(rows)),
        reviewer_value=transition(rows,'G0','G1'),reconciliation_value=transition(rows,'G0','G2'),
        human_override=dict(N=len(human),rate=ratio(sum(d!=0 for d in human),len(human)),mean_delta=ratio(sum(human),len(human)),
            upward=sum(d>0 for d in human),downward=sum(d<0 for d in human),N_reviewed_with_decision_and_gold=len(useful),review_usefulness=ratio(sum(useful),len(useful))),
        inter_rater=dict(N_pairs=len(ratings),exact_agreement=ratio(sum(d==0 for d in ratings),len(ratings)),MAE=ratio(sum(ratings),len(ratings)),method='Descriptive independent-rater pair score differences; no kappa or ICC claim'),
        uncertainty=bootstrap_mae(rows,'G2',seed),material_error_definition=f'Absolute total OR criterion point error > {threshold}',
        feedback_eligible_count=sum(r['dynamic_evaluation']['feedback_eligible'] for r in rows),feedback_coverage=ratio(sum(r['dynamic_evaluation']['feedback_eligible'] for r in rows),len(rows)))


def report(rows,threshold=Decimal('1'),seed=20261112):
    rows=[r for r in rows if r.get('dynamic_evaluation')]
    groups=defaultdict(list)
    for r in rows:
        m=r.get('dataset_case',{})
        key=(r['dynamic_evaluation']['policy_profile'],m.get('split','UNREGISTERED'),m.get('source_kind','UNREGISTERED'))
        groups[key].append(r)
    strata=[]
    for key,rs in sorted(groups.items()):
        item=dict(zip(('profile','split','source_kind'),key));item['metrics']=summarize(rs,threshold,seed)
        item['by_domain']={v:summarize([r for r in rs if r.get('dataset_case',{}).get('domain','UNSPECIFIED')==v],threshold,seed) for v in sorted({r.get('dataset_case',{}).get('domain','UNSPECIFIED') for r in rs})}
        item['by_solution_type']={v:summarize([r for r in rs if r.get('dataset_case',{}).get('solution_type','UNSPECIFIED')==v],threshold,seed) for v in sorted({r.get('dataset_case',{}).get('solution_type','UNSPECIFIED') for r in rs})}
        for dimension in ('difficulty','difficulty_basis'):
            item['by_'+dimension]={v:summarize([r for r in rs if r.get('dataset_case',{}).get(dimension,'UNSPECIFIED')==v],threshold,seed) for v in sorted({r.get('dataset_case',{}).get(dimension,'UNSPECIFIED') for r in rs})}
        def checker_group(r):
            checks=r['dynamic_evaluation'].get('checkers',[])
            if any(c['result']=='ERROR' for c in checks):return 'CHECKER_ERROR'
            if any(c['result']=='REFUTED' for c in checks):return 'CHECKER_REFUTED'
            if any(c['result']=='VERIFIED' for c in checks):return 'CHECKER_VERIFIED'
            return 'UNAVAILABLE_OR_REVIEW_ONLY'
        item['by_checker']={v:summarize([r for r in rs if checker_group(r)==v],threshold,seed) for v in sorted({checker_group(r) for r in rs})}
        strata.append(item)
    return dict(schema_version='dynamic-metrics.v1',N=len(rows),strata=strata,
        interpretation='Descriptive SHADOW evaluation. Synthetic, curated and real responses are never pooled; no statistical superiority or production certification.')
