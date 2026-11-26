"""Rubric-grounded fallback outside exact coverage, with blind review and abstention."""
from datetime import datetime, timezone
from copy import deepcopy
from decimal import Decimal
from confia_lean_auditor.semantic_policy.service import digest, DYNAMIC_VERSION
from .grading_models import StudentClaim, DynamicAuditResult, RubricBinding
from .review_models import IndependentPhase, BlindReviewProposal, CriterionProposal, CriterionReview
from .preparation_models import GenerationProvenance
from .reconciliation_models import CriterionReconciliation
from .semantic_provenance import assess_with_provenance, summarize, evaluation_record


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
        trace=assess_with_provenance(request_for(source.solution_text,statement,rubric,criterion,
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
    affected=[d for d in decisions if d.semantic_trace]
    traces=[d.semantic_trace for d in affected]
    evaluations=[evaluation_record(d.criterion_id,d.semantic_trace,d.claim_ids) for d in affected]
    provenance=deepcopy(result.analysis.provenance)
    provenance.update(summarize(traces))
    provenance.update(semantic_policy=DYNAMIC_VERSION, semantic_evaluation_attempted=True,
        semantic_evaluations=evaluations,
        deterministic_pass=dict(provenance=deepcopy(result.analysis.provenance),
            decisions=[d.model_dump(mode='json') for d in result.decisions],
            reviewed_components=list(result.reviewed_components),
            unreviewed_components=list(result.unreviewed_components),
            uncertainty=list(result.uncertainty),
            event_ids=[e['event_id'] for e in result.events]),
        selected_capabilities=[*result.analysis.provenance['selected_capabilities'],'SEMANTIC_RESIDUAL'],
        selection_reason='Verificações locais preservadas na passagem determinística; pendências encaminhadas à avaliação semântica. Consulte os recibos por critério para execução, abstenções e falhas. Lean não executado.')
    analysis=result.analysis.model_copy(update={'claims':claims,'provenance':provenance})
    bindings=list(result.bindings)
    events=deepcopy(result.events)
    for d, receipt in zip(affected,evaluations):
        bindings.extend(RubricBinding(criterion_id=d.criterion_id,claim_id=cid,
            binding_type='SEMANTIC_EVIDENCE',evidence=text,diagnostic_confidence='UNRESOLVED',
            status='REVIEW_ONLY') for cid,text in zip(d.claim_ids,d.evidence))
        events.append(dict(event_type='dynamic_semantic_rubric_decision',
            **receipt, suggested_points=None if d.semantic_trace['decision']=='review' else str(d.suggested_points),
            max_points=str(d.max_points),sufficiency=d.sufficiency,review_required=d.review_required,
            semantic_trace_sha256=digest(d.semantic_trace)))
    reviewed=[d.criterion_id for d in decisions if
        (d.semantic_trace['decision'] in {'met','not_met'} if d.semantic_trace else not d.review_required)]
    unreviewed=[d.criterion_id for d in decisions if d.criterion_id not in reviewed]
    events.append(dict(event_type='dynamic_semantic_grading_completed',stage='grader',
        score=score,reviewed_components=reviewed,unreviewed_components=unreviewed,
        technical_uncertainty=technical))
    for i,event in enumerate(events[len(result.events):],len(result.events)):
        event.update(event_id=digest(dict(source=source.source_hash,index=i,event=event)),
            transcription_version=result.analysis.transcription_version,package_id=result.context.package_id,
            preparation_id=result.context.preparation_id,rubric_id=result.context.rubric_id,
            created_at=datetime.now(timezone.utc).isoformat())
    updated=result.model_copy(update=dict(decisions=decisions,analysis=analysis,score=score,suggested_score=score,
        bindings=bindings,events=events,reviewed_components=reviewed,unreviewed_components=unreviewed,
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
        trace=assess_with_provenance(request_for(payload['solution'],statement,rubric,criterion,
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
    summary=summarize(traces.values())
    provenance=GenerationProvenance(provider=summary['provider'] or 'unknown; see_semantic_reviews',
        requested_model=summary['requested_model'] or 'unknown; see_semantic_reviews',
        returned_model=summary['model'] or 'unknown; see_semantic_reviews',reasoning_effort=summary['reasoning_effort'],prompt_version=DYNAMIC_VERSION+':review',
        schema_version='met-not_met-review.v1',input_sha256=digest(payload),output_sha256=digest(traces),
        response_id=None,created_at=now,code_sha=None,max_output_tokens=4000,raw_output=__import__('json').dumps(traces,ensure_ascii=False))
    return IndependentPhase(criterion_reviews=reviews,claims=claims,additional_claims=[],rejected_claims=[],
        detected_strategy='rubric_grounded',alternative_strategy=False,warnings=[],review_required=any(r.review_required for r in reviews),
        proposal=proposal,provenance=provenance,input_sha256=digest(payload),completed_at=now,semantic_reviews=traces)


def reconcile(grader,review,rubric):
    traces=review.phase_a.semantic_reviews if review.phase_a else {}
    traces=traces or {}
    independent=review.phase_a.criterion_reviews if review.phase_a else []
    criteria={c.criterion_id:c for c in rubric.criteria}
    ids=[r.criterion_id for r in independent]
    aligned=set(ids)==set(criteria)=={d.criterion_id for d in grader.decisions} and len(ids)==len(set(ids))
    rows=[]
    for d in grader.decisions:
        t=traces.get(d.criterion_id,{})
        g=d.semantic_trace
        r=next((r for r in independent if r.criterion_id==d.criterion_id),None)
        criterion=criteria.get(d.criterion_id)
        rpoints=r.proposed_points if r else None
        technical=review.status=='FAILED' or bool(t.get('error_type')) or bool(g and g.get('error_type'))
        # Exact partial credit is a conclusive level of its own, not an implicit "met".
        exact_conclusive=not g and not d.review_required and (
            d.automation=='AUTO_AWARD' and (
                d.sufficiency=='COMPLETE' and d.suggested_points==d.max_points or
                d.sufficiency=='PARTIAL' and 0<d.suggested_points<d.max_points) or
            d.automation=='AUTO_VETO' and d.sufficiency=='NOT_SATISFIED' and d.suggested_points==0)
        def semantic_level(trace,points,sufficiency):
            return (trace.get('decision')=='met' and points==d.max_points and sufficiency=='COMPLETE' or
                    trace.get('decision')=='not_met' and points==0 and sufficiency=='NOT_SATISFIED')
        conclusive=exact_conclusive or bool(g and semantic_level(g,d.suggested_points,d.sufficiency))
        reviewer_conclusive=bool(r and not r.review_required and r.assessment==r.sufficiency and
            semantic_level(t,rpoints,r.sufficiency))
        agrees=bool(not technical and aligned and criterion and r and
            criterion.max_points==d.max_points==r.max_points and conclusive and reviewer_conclusive and
            d.suggested_points==rpoints and d.sufficiency==r.sufficiency)
        if technical:
            reason='Falha técnica; pontos do Grader preservados, reconciliação pendente.'
        elif agrees:
            reason=('Concordância semântica de pontuação e atendimento pela rubrica; confirmar com o professor.' if g else
                    'Mesma pontuação e nível de atendimento; verificação exata preservada.')
        elif conclusive and reviewer_conclusive and d.suggested_points!=rpoints:
            reason=f'Divergência numérica: Grader {d.suggested_points}/{d.max_points} ({d.sufficiency}); Reviewer {rpoints}/{d.max_points} ({r.sufficiency}). Pontos do Grader preservados; reconciliação pendente.'
        else:
            reason='Abstenção, critérios incompatíveis ou divergência de atendimento/evidência; pontos do Grader preservados, reconciliação pendente.'
        rows.append(CriterionReconciliation(criterion_id=d.criterion_id,max_points=d.max_points,
            grader_points=d.suggested_points,reviewer_points=rpoints,grader_evidence=d.evidence,
            reviewer_evidence=[q['text'] for q in t.get('quotes',[])],mathematical_verification=[],
            fidelity_binding_state='SEMANTIC_NOT_FORMAL' if g else 'EXACT',sufficiency=d.sufficiency,
            status='TECHNICAL_ERROR' if technical else 'AGREEMENT_UNVERIFIED' if agrees and g else 'AGREEMENT_SUPPORTED' if agrees else 'REVIEW_REQUIRED',
            reconciled_points=d.suggested_points,automation='REVIEW_ONLY' if g or not agrees else 'AUTO_ACCEPT',
            reason=reason,
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
