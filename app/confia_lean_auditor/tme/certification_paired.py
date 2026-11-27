"""Paired research adapter over actual persisted outputs; never invokes either engine.

The same shared HumanGold reference is applied to both arms. Problem eligibility,
identical textual input, maxima and explicit criterion alignment are mandatory.
"""
from decimal import Decimal
from typing import Literal
from pydantic import Field
from confia_lean_auditor.submissions.schemas import SubmissionModel
from confia_lean_auditor.submissions.integrity import canonical_sha256
from confia_lean_auditor.submission_audits.router import service
from confia_lean_auditor.core.paths import get_repo_root
from confia_lean_auditor.core.problem_catalog import list_tme_problem_catalog
from confia_lean_auditor.dynamic.grading_context import case_context
from .question_review import owned_case
from .exam_store import exam_store
from .correction_engine import project_audit
from .certification_metrics import ratio
from .certification_experiment_metrics import criterion_metrics
from . import certification_runs as runs


class Pair(SubmissionModel):
    dynamic_question_attempt_id: str
    specialized_question_attempt_id: str
    specialized_audit_run_id: str
    # Keys Dynamic criterion IDs, values Specialized IDs. Omit for total-only A.
    criterion_alignment: dict[str,str] = Field(default_factory=dict)
    alignment_justification: str = Field(min_length=20,max_length=2000)


class PairedRequest(SubmissionModel):
    dynamic_run_id: str = Field(pattern=r'^run_[0-9a-f]{64}$')
    experiment: Literal['END_TO_END','COMMON_RUBRIC']
    pairs: list[Pair] = Field(min_length=1,max_length=10000)
    preparation_difference_note: str = Field(min_length=20,max_length=4000)


def paired_metrics(pairs):
    valid=[p for p in pairs if not p['exclusions']]
    dynamic=specialized=tie=0;deltas=[];false=[];missed=[]
    for p in valid:
        g=Decimal(p['gold_score']);a=abs(Decimal(p['dynamic_score'])-g);b=abs(Decimal(p['specialized_score'])-g)
        dynamic+=a<b;specialized+=b<a;tie+=a==b;deltas.append(a-b)
        if p.get('criterion_difference'):
            false.append(p['criterion_difference']['false_credit_difference']);missed.append(p['criterion_difference']['missed_credit_difference'])
    return dict(N=len(valid),dynamic_better=dynamic,specialized_better=specialized,tie=tie,
        mean_absolute_error_delta_dynamic_minus_specialized=ratio(sum(deltas),len(deltas)),
        N_criterion_aligned=len(false),false_credit_count_difference=sum(false) if false else None,missed_credit_count_difference=sum(missed) if missed else None,
        dynamic_review_rate=ratio(sum(p['dynamic_review_required'] for p in valid),len(valid)),specialized_review_rate=ratio(sum(p['specialized_review_required'] for p in valid),len(valid)),
        exclusions=[dict(index=i,reasons=p['exclusions']) for i,p in enumerate(pairs) if p['exclusions']],
        interpretation='Paired descriptive comparison only; no superiority or causal claim')


def compare(aid,body,user):
    run=runs.read(aid,body.dynamic_run_id,user);out=[];seen=set()
    for pair in body.pairs:
        if pair.dynamic_question_attempt_id in seen:raise ValueError('duplicate comparison pair')
        seen.add(pair.dynamic_question_attempt_id)
        row=next((r for r in run['records'] if r['question_attempt_id']==pair.dynamic_question_attempt_id),None)
        if not row:raise ValueError('Dynamic case absent from run')
        dc=owned_case(pair.dynamic_question_attempt_id,user);sc=owned_case(pair.specialized_question_attempt_id,user)
        if sc.dynamic_context or not dc.dynamic_context:raise ValueError('comparison requires separate legitimate engines')
        raw=service().get(pair.specialized_audit_run_id)
        if raw.submission_id!=sc.submission_id or not raw.question_context:raise ValueError('Specialized audit binding mismatch')
        detail=exam_store().detail(sc.exam_submission_id,user)
        audit=project_audit(raw.model_copy(update={'stale':False}),sc,detail)
        draw=service().get(row['audit_run_id'])
        _,statement,rubric,prep=case_context(dc)
        catalog=next((p for p in list_tme_problem_catalog(get_repo_root()) if p['problem_id']==sc.problem_id),None)
        errors=list(row['dynamic_evaluation']['exclusions']);dg=row['dynamic_evaluation']['stages']['G2']
        if not catalog:errors.append('UNSUPPORTED_BENCHMARK_CONDITION')
        elif ' '.join(catalog['statement'].split())!=' '.join(statement.statement.split()):errors.append('STATEMENT_MISMATCH')
        if raw.source.solution_text!=draw.source.solution_text:errors.append('TRANSCRIPTION_MISMATCH')
        if Decimal(str(audit['max_score']))!=Decimal(row['max_score']):errors.append('MAXIMUM_MISMATCH')
        if audit['technical_uncertainty'] or dg['technical_failures']:errors.append('TECHNICAL_FAILURE')
        if audit['suggested_score'] is None or dg['score'] is None:errors.append('UNAVAILABLE_STAGE')
        difference=None;special={i['rubric_item_id']:i for i in audit['rubric_items']}
        dynamic={c.criterion_id:c for c in rubric.criteria}
        mapping=pair.criterion_alignment
        aligned=bool(mapping) and set(mapping)==set(dynamic) and len(set(mapping.values()))==len(mapping) and set(mapping.values())==set(special)
        if aligned:aligned=all(Decimal(str(special[v]['max_points']))==dynamic[k].max_points for k,v in mapping.items())
        if mapping and not aligned:errors.append('RUBRIC_MISMATCH')
        # B is accepted only for literally identical obligations and point maxima.
        if body.experiment=='COMMON_RUBRIC' and (not aligned or any(dynamic[k].description!=special[v].get('label') for k,v in mapping.items())):
            errors.append('COMMON_RUBRIC_NOT_ESTABLISHED')
        if aligned:
            pseudo={**row,'dynamic_evaluation':{'stages':{'S':{'criteria':[dict(criterion_id=k,points=special[v]['suggested_points'],max_points=special[v]['max_points']) for k,v in mapping.items()]}}}}
            dm=criterion_metrics([row],'G2');sm=criterion_metrics([pseudo],'S')
            difference=dict(false_credit_difference=dm['false_credit_count']-sm['false_credit_count'],missed_credit_difference=dm['missed_credit_count']-sm['missed_credit_count'])
        out.append(dict(dynamic_question_attempt_id=dc.case_id,specialized_question_attempt_id=sc.case_id,exclusions=sorted(set(errors)),
            gold_record_id=row['gold_record_id'],gold_sha256=row['gold_sha256'],gold_score=row['human_gold_score'],
            dynamic_score=dg['score'],specialized_score=str(audit['suggested_score']) if audit['suggested_score'] is not None else None,
            dynamic_review_required=dg['review_required'],specialized_review_required=audit['review_required'],criterion_difference=difference,
            identical_text_sha256=canonical_sha256(raw.source.solution_text),specialized_artifact_sha256=canonical_sha256(raw.model_dump(mode='json')),
            specialized=dict(audit_run_id=raw.audit_run_id,engine_version=audit['engine_version'],engine_config=audit['engine_config'],checker_coverage=audit['checker_summary'],rubric=audit['rubric_items']),
            dynamic=dict(context=row['dynamic_evaluation']['context'],provenance=row['dynamic_evaluation']['provenance']),
            alignment=pair.model_dump(mode='json')))
    value=dict(schema_version='certification-paired.v1',assessment_id=aid,experiment=body.experiment,request=body.model_dump(mode='json'),
        dynamic_run_id=body.dynamic_run_id,evaluation_mode='SHADOW_EVALUATION',official_correction_affected=False,created_at=runs.now(),pairs=out,metrics=paired_metrics(out))
    identity='comparison_'+canonical_sha256([aid,body.model_dump(mode='json')]);value['id']=identity
    with exam_store()._locked():
        target=runs.path(aid,identity)
        if target.exists():return runs.read(aid,identity,user)
        return runs.save(aid,identity,value)
