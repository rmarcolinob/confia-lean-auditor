"""Dynamic evidence projected into the shared question audit/decision contract.

Readers acquire no exam/submission locks: D6 calls them under those locks.
Mathematical decisions remain exclusively in DY3–DY5 persisted artifacts.
"""
from confia_lean_auditor.submission_audits.schemas import AuditRun
from confia_lean_auditor.submission_audits.router import service
from confia_lean_auditor.submissions.integrity import canonical_sha256
from .reconciliation_service import ReconciliationService, sealed_read


def associated(case, run):
    if not run or run.status!='COMPLETED': return None, None
    raw=AuditRun.model_validate(run.model_dump(exclude={'stale'}))
    s=ReconciliationService(service())
    reviews=[]
    for path in s.reviews.root.glob('drev_*.json'):
        _,r=s.reviews.load_record(path)
        if r.audit_run_id==run.audit_run_id: reviews.append(s.reviews.read(path,case,raw))
    latest=max(reviews,key=lambda r:r.completed_at) if reviews else None
    if not latest: return None,None
    candidates=[]
    for path in s.root.glob('drec_*.json'):
        record=sealed_read(s.root,path)
        if record.get('grader_audit_run_id')==run.audit_run_id and record.get('independent_review_id')==latest.review_id:
            candidates.append(s.read(path,case,raw))
    rec=max(candidates,key=lambda r:r.completed_at).model_dump(mode='json') if candidates else None
    return latest.model_dump(mode='json'),rec


def current_reconciliation(case, run):
    return associated(case,run)[1] if run and not getattr(run,'stale',False) else None


def project(result,run,case):
    review,rec=associated(case,run)
    from .grading_context import case_context
    _,_,rubric,_=case_context(case)
    rubric_by_id={c.criterion_id:c for c in rubric.criteria}
    reasons=list(rec['review_reasons']) if rec else ['Conclua a revisão independente e a reconciliação antes da homologação.']
    if getattr(run,'stale',False): reasons.append('Leitura alterada: esta análise pertence a uma versão anterior.')
    decisions={c['criterion_id']:c for c in rec['criteria']} if rec else {}
    items=[]
    for d in result.decisions:
        r=decisions.get(d.criterion_id)
        points=float(r['reconciled_points']) if r else float(d.suggested_points)
        pending=(r['status'] in {'REVIEW_REQUIRED','TECHNICAL_ERROR'}) if r else bool(d.semantic_trace and d.semantic_trace.get('decision')=='review' or d.dependency_trace and d.dependency_trace['status'] in {'unknown','violated'})
        technical=(r['technical_uncertainty']) if r else bool(d.semantic_trace and d.semantic_trace.get('error_type'))
        if pending:
            points=None
        needs=r['review_required'] if r else d.review_required
        supported=bool(points) or (d.max_points==0 and d.sufficiency=='COMPLETE')
        status='indeterminate' if needs else 'supported' if supported else 'refuted'
        items.append(dict(rubric_item_id=d.criterion_id,label=d.description,max_points=float(d.max_points),suggested_points=points,
            status=status,display_status=status,status_label='Falha técnica' if technical else 'Revisar' if pending else ('Avaliação semântica' if d.semantic_trace else 'Revisar') if needs else 'Sustentado' if supported else 'Não sustentado',
            review_required=needs,reason=r['reason'] if r else d.explanation,evidence_ids=d.claim_ids,checker_ids=[],children=[],
            grader_points=float(d.suggested_points),reviewer_points=r['reviewer_points'] if r else None,
            automation=r['automation'] if r else 'REVIEW_ONLY',
            dependencies=list(rubric_by_id[d.criterion_id].dependencies),
            teacher_guidance=rubric_by_id[d.criterion_id].teacher_guidance,
            rubric_notes=rubric_by_id[d.criterion_id].notes,grader_explanation=d.explanation,
            grader_semantic_trace=d.semantic_trace,
            **({'credit_levels':[v.model_dump(mode='json') for v in rubric_by_id[d.criterion_id].credit_levels]} if rubric_by_id[d.criterion_id].credit_levels else {}),
            **({'dependency_rules':[v.model_dump(mode='json') for v in rubric_by_id[d.criterion_id].dependency_rules], 'dependency_assessment':d.dependency_trace} if d.dependency_trace else {})))
    evidence=[dict(evidence_id=c.claim_id,text=c.text,kind='text',claim_type=c.claim_type,
        source_span=dict(start=c.start,end=c.end,scope='transcription',sha256=run.source_hash),exam_page_id=None,page_number=None,
        region=None,grounding_status=c.fidelity) for c in result.analysis.claims]
    checks=[dict(checker_id=c.claim_id,checker_type=c.verifier,status={'VERIFIED':'verified','REFUTED':'refuted','ERROR':'technical_error'}.get(c.verification_status,'indeterminate'),
        status_label=c.verification_detail,evidence_ids=[c.claim_id],trace_reference=f'audit-run:{run.audit_run_id}') for c in result.analysis.claims]
    return dict(engine_mode='DYNAMIC',rubric_items=items,evidences=evidence,checker_summary=checks,
        technical_uncertainty=bool(rec and rec['technical_uncertainty']) or any(c['status']=='technical_error' for c in checks) or any(d.semantic_trace and d.semantic_trace.get('error_type') for d in result.decisions),
        suggested_score=(float(rec['reconciled_suggested_score']) if rec['reconciled_suggested_score'] is not None else None) if rec else result.score,grader_suggested_score=result.score,
        review_required=bool(reasons),review_reasons=reasons,suggestion_ready=bool(rec) and rec['reconciled_suggested_score'] is not None and not getattr(run,'stale',False),
        reconciliation_id=rec['reconciliation_id'] if rec else None,reconciliation=rec,
        independent_review=review,policy_profile=rec['policy_profile'] if rec else None,
        workflow_actions=[] if getattr(run,'stale',False) else ([dict(label='Reconciliar sugestão',route=['dynamic','attempts',case.case_id,'audits',run.audit_run_id,'reconciliations'],body=dict(independent_review_id=review['review_id']))] if review and not rec else []) + [dict(label='Solicitar revisão independente',route=['dynamic','attempts',case.case_id,'audits',run.audit_run_id,'independent-reviews'])])


def decision_reference(audit,body,case,run):
    if audit.get('engine_mode')!='DYNAMIC':
        if body.reconciliation_id or body.adjudication: raise ValueError('reconciliation is unavailable for this engine')
        return {}
    # Integrity binds the persisted artifact, never its public/redacted projection.
    rec=current_reconciliation(case,run)
    if (not audit.get('suggestion_ready') and not body.adjudication) or not rec or body.reconciliation_id!=rec['reconciliation_id']:
        from confia_lean_auditor.tme.exam_store import ExamConflict
        raise ExamConflict('select the current reconciled suggestion')
    return dict(reconciliation_id=rec['reconciliation_id'],reconciliation_sha256=canonical_sha256(rec),
        grader_suggested_points=rec['grader_score_snapshot'],independent_review_id=rec['independent_review_id'])
