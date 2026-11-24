"""Rubric-grounded fallback outside exact coverage, with blind review and abstention."""
from datetime import datetime, timezone
from decimal import Decimal
from confia_lean_auditor.semantic_policy.service import assess, digest, DYNAMIC_VERSION
from .grading_models import StudentClaim, DynamicAuditResult
from .review_models import IndependentPhase, BlindReviewProposal, CriterionProposal, CriterionReview
from .preparation_models import GenerationProvenance
from .reconciliation_models import CriterionReconciliation


def enabled(context):
    return getattr(context,'semantic_policy',None)==DYNAMIC_VERSION


def request_for(solution, statement, rubric, criterion, checks, stage):
    return dict(solution=solution, statement=statement.model_dump(mode='json'),
        rubric=rubric.model_dump(mode='json'),criterion=criterion.model_dump(mode='json'),
        checks=checks,stage=stage,verification_level='SEMANTIC_NOT_FORMAL')


def claims_for(trace, prefix):
    result=[]
    for i,q in enumerate(trace.get('quotes',[])):
        span=q['occurrences'][0]
        result.append(StudentClaim(claim_id=f'{prefix}_{i}', start=span['start'],end=span['end'],
            text=q['text'],normalized=q['text'],claim_type='SEMANTIC_EVIDENCE',subject='approved_rubric',
            fidelity='FAITHFUL',verification_status='REVIEW_ONLY',
            verification_detail='Trecho literal; avaliação semântica, sem prova formal.',verifier=DYNAMIC_VERSION))
    return result


def augment(result, source, statement, rubric, provider=None):
    if not any(d.review_required for d in result.decisions):
        return result
    criteria={c.criterion_id:c for c in rubric.criteria}
    decisions=[]; claims=list(result.analysis.claims)
    for decision in result.decisions:
        if not decision.review_required:
            decisions.append(decision);continue
        criterion=criteria[decision.criterion_id]
        trace=assess(request_for(source.solution_text,statement,rubric,criterion,
            decision.checker_results,'grader'),provider)
        # Exact contradictory evidence is never overwritten by an LLM opinion.
        if decision.sufficiency=='CONFLICT' or any(c.get('status')=='REFUTED' for c in decision.checker_results):
            trace.update(decision='review',gate_reason='EXACT_CONFLICT_REQUIRES_REVIEW')
        additions=claims_for(trace,'sem_'+str(len(decisions)));claims.extend(additions)
        state=trace['decision'];points=criterion.max_points if state=='met' else Decimal(0)
        decisions.append(decision.model_copy(update=dict(suggested_points=points,
            automation='SEMANTIC_SUGGESTION' if state!='review' else 'REVIEW_ONLY',
            sufficiency={'met':'COMPLETE','not_met':'NOT_SATISFIED','review':'INSUFFICIENT'}[state],
            evidence=[q['text'] for q in trace.get('quotes',[])],
            claim_ids=[c.claim_id for c in additions],semantic_trace=trace,
            explanation=trace.get('response',{}).get('justification','Avaliação indisponível; revisão necessária.'),
            review_required=True,warnings=['Avaliação semântica; sem certificação formal.'])))
    pending=any(d.semantic_trace and d.semantic_trace['decision']=='review' for d in decisions)
    score=None if pending else float(sum(d.suggested_points for d in decisions))
    technical=any(d.semantic_trace and d.semantic_trace.get('error_type') for d in decisions)
    analysis=result.analysis.model_copy(update={'claims':claims})
    updated=result.model_copy(update=dict(decisions=decisions,analysis=analysis,score=score,suggested_score=score,
        review_required=any(d.review_required for d in decisions),verdict='falha_tecnica' if technical else 'inconclusivo' if pending else 'sugestao_semantica',
        feedback='Sugestão pela rubrica aprovada. Conclua Reviewer e reconciliação; avaliação semântica não é certificação formal.',
        rubric_assessment={'assessment_status':'partial' if pending else 'complete',
            'items':[dict(id=d.criterion_id,description=d.description,points=None if d.semantic_trace and d.semantic_trace['decision']=='review' else float(d.suggested_points),
                max_points=float(d.max_points),verification_status='technical_error' if d.semantic_trace and d.semantic_trace.get('error_type') else 'review_only' if d.semantic_trace and d.semantic_trace['decision']=='review' else 'semantic' if d.semantic_trace else 'verified_in_scope',verification_level='SEMANTIC_NOT_FORMAL' if d.semantic_trace else 'EXACT',
                evidence=d.evidence,assessment_note=d.explanation) for d in decisions]}))
    return DynamicAuditResult.model_validate(updated.model_dump())


def review_phase(payload, rubric, provider=None):
    from types import SimpleNamespace
    statement=SimpleNamespace(model_dump=lambda **_:payload['statement'])
    traces={};reviews=[];claims=[];proposals=[]
    for criterion in rubric.criteria:
        trace=assess(request_for(payload['solution'],statement,rubric,criterion,
            payload['mathematical_evidence'],'independent_reviewer'),provider)
        traces[criterion.criterion_id]=trace
        additions=claims_for(trace,'review_sem_'+str(len(reviews)));claims.extend(additions)
        state=trace['decision'];points=criterion.max_points if state=='met' else Decimal(0) if state=='not_met' else None
        suff={'met':'COMPLETE','not_met':'NOT_SATISFIED','review':'INSUFFICIENT'}[state]
        explanation=trace.get('response',{}).get('justification','Revisão indisponível.')
        proposals.append(CriterionProposal(criterion_id=criterion.criterion_id,assessment=suff,
            proposed_points=str(points) if points is not None else None,claim_ids=[c.claim_id for c in additions],
            explanation=explanation,uncertainty=[] if points is not None else ['Abstenção semântica.']))
        reviews.append(CriterionReview(criterion_id=criterion.criterion_id,max_points=criterion.max_points,
            proposed_points=points,provider_proposed_points=None,assessment=suff,sufficiency=suff,
            claim_ids=[c.claim_id for c in additions],evidence=[c.text for c in additions],checker_references=[],
            explanation=explanation,uncertainty=[] if points is not None else ['Abstenção semântica.'],review_required=points is None))
    proposal=BlindReviewProposal(detected_strategy='rubric_grounded',alternative_strategy=False,
        additional_claims=[],criterion_reviews=proposals,warnings=[])
    now=datetime.now(timezone.utc)
    provenance=GenerationProvenance(provider='semantic_policy',requested_model='see_semantic_reviews',
        returned_model='see_semantic_reviews',reasoning_effort=None,prompt_version=DYNAMIC_VERSION+':review',
        schema_version='met-not_met-review.v1',input_sha256=digest(payload),output_sha256=digest(traces),
        response_id=None,created_at=now,code_sha=None,max_output_tokens=4000,raw_output=__import__('json').dumps(traces,ensure_ascii=False))
    return IndependentPhase(criterion_reviews=reviews,claims=claims,additional_claims=[],rejected_claims=[],
        detected_strategy='rubric_grounded',alternative_strategy=False,warnings=[],review_required=any(r.review_required for r in reviews),
        proposal=proposal,provenance=provenance,input_sha256=digest(payload),completed_at=now,semantic_reviews=traces)


def reconcile(grader,review):
    traces=review.phase_a.semantic_reviews if review.phase_a else {}
    rows=[]
    for d in grader.decisions:
        t=traces.get(d.criterion_id,{})
        g=d.semantic_trace
        # Exact first-pass decisions remain final mathematical evidence.
        expected=('met' if d.automation=='AUTO_AWARD' else 'not_met') if not g else g['decision']
        agrees=expected in {'met','not_met'} and t.get('decision')==expected
        technical=review.status=='FAILED' or bool(t.get('error_type')) or bool(g and g.get('error_type'))
        rpoints=d.max_points if t.get('decision')=='met' else Decimal(0) if t.get('decision')=='not_met' else None
        rows.append(CriterionReconciliation(criterion_id=d.criterion_id,max_points=d.max_points,
            grader_points=d.suggested_points,reviewer_points=rpoints,grader_evidence=d.evidence,
            reviewer_evidence=[q['text'] for q in t.get('quotes',[])],mathematical_verification=[],
            fidelity_binding_state='SEMANTIC_NOT_FORMAL' if g else 'EXACT',sufficiency=d.sufficiency,
            status='TECHNICAL_ERROR' if technical else 'AGREEMENT_UNVERIFIED' if agrees and g else 'AGREEMENT_SUPPORTED' if agrees else 'REVIEW_REQUIRED',
            reconciled_points=d.suggested_points,automation='REVIEW_ONLY' if g or not agrees else 'AUTO_ACCEPT',
            reason='Concordância semântica pela rubrica; confirmar com o professor.' if agrees and g else 'Verificação exata preservada.' if agrees else 'Divergência, abstenção ou falha técnica; nota pendente.',
            review_required=bool(g) or not agrees,technical_uncertainty=technical))
    return rows


class TeacherPreparationProvider:
    """Local context receipt for teacher-supplied rubrics; invents no reference solution."""
    def generate(self, operation, payload, response_type):
        from .preparation_models import PreparationProposal
        statement=payload['statement']['statement']
        proposal=PreparationProposal(mathematical_domain='teacher_supplied',normalized_problem=statement,
            data=(),assumptions=(),objects=(),target='Aplicar a rubrica aprovada pelo professor.',
            expects_unique_result=False,candidate_reference_solutions=(),alternative_strategies=(),
            warnings=(),uncertainties=())
        meta=GenerationProvenance(provider='local_teacher_context',requested_model='not_applicable',
            returned_model='not_applicable',reasoning_effort=None,prompt_version='teacher-context.v1',
            schema_version='PreparationProposal.v1',input_sha256=digest(payload),output_sha256=digest(proposal.model_dump(mode='json')),
            response_id=None,created_at=datetime.now(timezone.utc),code_sha=None,max_output_tokens=0,
            raw_output=proposal.model_dump_json())
        return proposal,meta
