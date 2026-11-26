"""Read-only DY7 projection. Uses D7 HumanGold, D4/D5 artifacts and D6 decisions."""
from confia_lean_auditor.dynamic.product_adapter import associated
from confia_lean_auditor.dynamic.grading_context import case_context
from confia_lean_auditor.submissions.integrity import canonical_sha256


def provenance(value):
    if not value:return None
    data=value.model_dump(mode='json') if hasattr(value,'model_dump') else value
    # No raw prompt, student text, local paths or provider response body in exports.
    return {k:v for k,v in data.items() if k not in {'raw_output','response_id'}}


def stage(score=None,criteria=None,review=True,status='UNAVAILABLE',technical=None,**extra):
    return dict(score=str(score) if score is not None else None,criteria=criteria or [],review_required=review,
                status=status,technical_failures=technical or [],**extra)


def project(case,run,human,gold,current,profile,feedback_policy='WITHHOLD'):
    context,statement,rubric,prep=case_context(case)
    result=run.result if run else None
    review,rec=associated(case,run) if result else (None,None)
    claims=result.analysis.claims if result else []
    checkers=[dict(claim_id=c.claim_id,proposition=c.normalized,result=c.verification_status,verifier=c.verifier,
                  evidence_kind=('SYMBOLIC' if c.claim_type in {'TRANSFORMATION','FORMULA'} else 'DETERMINISTIC') if c.verification_status in {'VERIFIED','REFUTED','ERROR'} and c.verifier=='dynamic-exact-polynomial.v1' else 'SEMANTIC_OR_REVIEW_ONLY',
                  lean_executed=False) for c in claims]
    technical=['CHECKER_FAILURE'] if any(c.verification_status=='ERROR' for c in claims) else []
    if run and run.status=='FAILED':technical.append('INVALID_DATA' if run.error_code=='INPUT_REQUIRES_REVIEW' else 'GRADER_FAILURE')
    g0=stage(result.score if result else None,
        [dict(criterion_id=d.criterion_id,points=str(d.suggested_points),max_points=str(d.max_points)) for d in result.decisions] if result else [],
        result.review_required if result else True,run.status if run else 'UNAVAILABLE',technical,
        error_code=run.error_code if run else None,artifact_id=run.audit_run_id if run else None,artifact_sha256=canonical_sha256(run.model_dump(exclude={'stale'},mode='json')) if run else None)
    phase=review.get('phase_a') if review else None
    criteria=[dict(criterion_id=c['criterion_id'],points=c['proposed_points'],max_points=c['max_points']) for c in phase['criterion_reviews']] if phase else []
    from decimal import Decimal
    total=sum(Decimal(c['points']) for c in criteria) if criteria and all(c['points'] is not None for c in criteria) else None
    rt=['PROVIDER_FAILURE'] if review and review['status']=='FAILED' else []
    if phase and any(c['verification_status']=='ERROR' for c in phase['claims']+phase['additional_claims']):rt.append('CHECKER_FAILURE')
    g1=stage(total,criteria,review['review_required'] if review else True,review['status'] if review else 'UNAVAILABLE',rt,
        error_code=review['error_code'] if review else None,artifact_id=review['review_id'] if review else None,artifact_sha256=canonical_sha256(review) if review else None,
        alternative_strategy=phase['alternative_strategy'] if phase else None)
    g2=stage(rec['reconciled_suggested_score'] if rec else None,
        [dict(criterion_id=c['criterion_id'],points=c['reconciled_points'],max_points=c['max_points'],automation=c['automation']) for c in rec['criteria']] if rec else [],
        rec['review_required'] if rec else True,'COMPLETED' if rec else 'UNAVAILABLE',
        list(set(technical+rt+(['RECONCILIATION_TECHNICAL_UNCERTAINTY'] if rec and rec['technical_uncertainty'] else []))),
        artifact_id=rec['reconciliation_id'] if rec else None,artifact_sha256=canonical_sha256(rec) if rec else None)
    g3=stage(human['final_points'] if human else None,status='COMPLETED' if human else 'UNAVAILABLE',artifact_id=human['human_decision_id'] if human else None,
             adjustment_reason_recorded=bool(human and human.get('override_reason')))
    if human and human.get('adjudication'):
        a=human['adjudication']
        g3.update(origin='HUMAN_ADJUDICATION', formal_certification=False,
            adjudication_version=a['schema_version'],rubric_sha256=a['rubric_sha256'],
            criteria=[dict(criterion_id=c['criterion_id'],points=c['final_points'],
                justification_recorded=bool(c['justification'])) for c in a['criteria']])
    exclusions=[]
    binding=gold.get('binding') if gold else None
    if not gold:exclusions.append('MISSING_GOLD')
    elif not binding:exclusions.append('MISSING_VERSION_BINDING')
    else:
        if binding['question_attempt_id']!=case.case_id:exclusions.append('INVALID_SUBMISSION')
        version=f'{run.transcription_id}:{run.revision_number}' if run else current
        if binding['transcription_version_id']!=version:exclusions.append('TRANSCRIPTION_MISMATCH')
        if any(binding[k]!=getattr(context,k) for k in ('rubric_id','rubric_version','rubric_sha256')):exclusions.append('RUBRIC_MISMATCH')
        if any(binding[k]!=getattr(context,k) for k in ('statement_version','statement_sha256')):exclusions.append('STATEMENT_MISMATCH')
        if gold.get('evaluation',{}).get('adjudication_status')=='UNRESOLVED':exclusions.append('UNRESOLVED_GOLD')
    return dict(schema_version='dynamic-evaluation.v1',policy_profile=profile,context=context.model_dump(mode='json'),
        stages=dict(G0=g0,G1=g1,G2=g2,G3=g3),exclusions=exclusions,gold_evaluation=gold.get('evaluation') if gold else None,
        gold_binding=binding,checkers=checkers,provenance=dict(preparation=provenance(prep.provenance),
            grader=result.analysis.provenance if result else None,reviewer=provenance(phase['provenance']) if phase else None,
            reviewer_version=review['reviewer_version'] if review else None,policy_version=rec['policy_version'] if rec else None,
            reconciliation=rec['provenance'] if rec else None),
        feedback_eligible=bool(human and rec and feedback_policy=='AFTER_CONFIRMATION'))
