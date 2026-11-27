"""Exact Decimal comparisons with explicit denominators; no causal inference."""
from collections import defaultdict
from decimal import Decimal


def ratio(n,d):
    return str(Decimal(n)/Decimal(d)) if d else None


def comparisons(rows, prediction, reference):
    pairs=[(Decimal(str(r[prediction])),Decimal(str(r[reference]))) for r in rows
           if r.get(prediction) is not None and r.get(reference) is not None]
    errors=[a-b for a,b in pairs];n=len(pairs)
    return dict(N=n,exact_score_agreement=ratio(sum(e==0 for e in errors),n),
        MAE=ratio(sum(abs(e) for e in errors),n),bias=ratio(sum(errors),n),
        within_1=ratio(sum(abs(e)<=1 for e in errors),n),within_2=ratio(sum(abs(e)<=2 for e in errors),n),
        under_score_count=sum(e<0 for e in errors),over_score_count=sum(e>0 for e in errors),
        zero_when_gold_positive=sum(a==0 and b>0 for a,b in pairs),positive_when_gold_zero=sum(a>0 and b==0 for a,b in pairs))


def rubric_metrics(rows):
    tp=fp=fn=n=0
    for row in rows:
        predicted={r['rubric_item_id']:r for r in row['rubric_decisions']}
        for gold in row.get('rubric_gold',[]):
            item=predicted.get(gold['rubric_item_id'])
            if not item or item['suggested_points'] is None or Decimal(str(item['max_points']))!=Decimal(gold['max_points']):continue
            a=Decimal(str(item['suggested_points']))>0;b=Decimal(gold['gold_points'])>0
            n+=1;tp+=a and b;fp+=a and not b;fn+=not a and b
    return dict(N_rubric_pairs=n,precision=ratio(tp,tp+fp),recall=ratio(tp,tp+fn),
        true_positive_awards=tp,false_positive_awards=fp,missed_awards=fn,
        definition='Positive award presence (>0), top-level rubric pairs explicitly supplied in gold.',
        obligation_precision=None,obligation_recall=None,obligation_unavailable_reason='No independent obligation-level gold labels.')


def score_metrics(rows):
    return dict(confia_vs_gold=comparisons(rows,'suggested_score','human_gold_score'),
        confia_vs_human_decision=comparisons(rows,'suggested_score','human_decision_score'),
        human_decision_vs_gold=comparisons(rows,'human_decision_score','human_gold_score'),rubric_awards=rubric_metrics(rows))


def metrics(rows,audit_history,question_history):
    grouped=defaultdict(list)
    for row in rows:grouped[row['engine_mode'] or 'UNANALYZED'].append(row)
    confirmed=[r for r in rows if r['adjustment'] is not None]
    deltas=[Decimal(r['adjustment']) for r in confirmed]
    reads=[q for q in question_history if q['transcription_version_count']]
    corrected=[q for q in reads if q['human_corrected']]
    histories=defaultdict(list)
    for audit in audit_history:histories[(audit['question_attempt_id'],audit['engine_mode'])].append(audit)
    changes=[];reanalyzed=set()
    for (qid,mode),runs in histories.items():
        runs.sort(key=lambda r:(r['created_at'],r['audit_run_id']))
        if len(runs)>1:reanalyzed.add(qid)
        for previous,current in zip(runs,runs[1:]):
            if (current['transcription_version_id']!=previous['transcription_version_id'] and current['human_corrected_reading']
                    and current['suggested_score'] is not None and previous['suggested_score'] is not None):
                changes.append(Decimal(current['suggested_score'])-Decimal(previous['suggested_score']))
    completed=[a for a in audit_history if a['status']=='COMPLETED']
    return dict(**score_metrics(rows),by_engine_mode={m:score_metrics(rs) for m,rs in grouped.items()},
        stages=dict(transcription=dict(N_questions_with_reading=len(reads),human_corrected_questions=len(corrected),
            correction_rate=ratio(len(corrected),len(reads))),
            audit=dict(N_runs=len(audit_history),completed=len(completed),failures=sum(a['status']=='FAILED' for a in audit_history),
                success_rate=ratio(len(completed),len(audit_history)),review_rate=ratio(sum(a['review_required'] for a in completed),len(completed)),
                technical_uncertainty_rate=ratio(sum(a['technical_uncertainty'] for a in audit_history),len(audit_history))),
            human_adjustment=dict(N_decisions=len(deltas),adjusted_count=sum(d!=0 for d in deltas),
                adjustment_rate=ratio(sum(d!=0 for d in deltas),len(deltas)),mean_absolute_adjustment=ratio(sum(abs(d) for d in deltas),len(deltas)),
                upward_count=sum(d>0 for d in deltas),downward_count=sum(d<0 for d in deltas)),
            reanalysis=dict(reanalyzed_questions=len(reanalyzed),N_reading_change_pairs=len(changes),
                mean_score_change_after_reading_correction=ratio(sum(changes),len(changes)),
                mean_absolute_score_change=ratio(sum(abs(d) for d in changes),len(changes)))),
        interpretation='Descriptive paired comparisons only; no causal effect or statistical certification claim.')
