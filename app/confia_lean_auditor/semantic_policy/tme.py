"""Semantic B opinions on unsettled obligations; PautaEngine remains the only scorer."""
from .service import assess, VERSION, specialized_policy
from confia_lean_auditor.rubric.pauta.engine import PautaEngine
from .tme_context import accepted_contexts, obligation_contexts, quotes_in_context


class MinimalEvidencePolicy:
    def accepts(self, e):
        t=e.metadata.get('semantic_fallback',{})
        return (e.origin=='semantic' and e.verification_source=='semantic'
            and e.attributable_to_student and e.grounding_status=='grounded'
            and t.get('policy')==VERSION and t.get('decision') in {'met','not_met'}
            and bool(e.evidence_refs) and not t.get('error_type'))

    def needs_review(self, decision):
        return decision.origin == 'semantic' or decision.effective_status not in {'supported','refuted'}


def policy_for(name):
    if name==VERSION: return MinimalEvidencePolicy()
    if name not in (None,'legacy'): raise ValueError('Unknown saved TME policy')
    return None


def apply(config, bridge, solution, statement, *, provider=None, item_sources=None):
    originals={r.record_id:r for r in bridge.auditor.records}
    definitions={o.id:o for o in config.obligations}
    contexts = accepted_contexts(bridge, solution, item_sources)
    obligations=list(bridge.evidence.obligations)
    for index, e in enumerate(obligations):
        current = bridge.evidence.model_copy(update={'obligations':tuple(obligations)})
        assessment = PautaEngine().evaluate(config, current, evidence_policy=MinimalEvidencePolicy())
        pending = {oid for item in assessment.items if item.status != 'decided'
                   for oid in (*item.indeterminate_obligations, *item.technical_error_obligations)}
        if e.obligation_id not in pending:
            continue  # Including unused alternative paths in an already decided item.
        candidates=[originals[k] for k in e.source_claim_ids if k in originals]
        record_eligible=(e.attributable_to_student
            and e.grounding_status=='grounded' and candidates
            and all(r.semantic_role.value not in {'assumption','quoted_statement','rejected_attempt'} for r in candidates))
        requirement, local = obligation_contexts(config, contexts, e.obligation_id)
        eligible=(e.status not in {'supported','refuted'} and (record_eligible or local)
            and not any(v.get('effective_status')=='refuted' for v in e.metadata.get('verifications',[]))
            and not e.metadata.get('reason','').startswith('CONFLICTING'))
        if item_sources is not None and not local:
            eligible = False  # Preserve item scope even if an extracted fragment lost its wrapper.
        if eligible:
            trace=assess(dict(solution=solution,statement=statement,
                criterion=definitions[e.obligation_id].model_dump(mode='json'),
                evidence_requirement=requirement,
                rubric=config.model_dump(mode='json'), evidence=[r.model_dump(mode='json') for r in candidates],
                accepted_item_evidence=local,
                checks=e.model_dump(mode='json'), reason='formal_obligation_not_satisfied'),provider)
            if local and trace['decision'] != 'review' and not quotes_in_context(trace, local):
                trace.update(decision='review', error_type='QuoteOutsideAuthorizedItem', error_stage='semantic_fallback')
            status={'met':'supported','not_met':'refuted','review':'technical_error' if trace.get('error_type') else 'indeterminate'}[trace['decision']]
            e=e.model_copy(update=dict(status=status,origin='semantic',verification_source='semantic',
                attributable_to_student=True, grounding_status='grounded',
                evidence_refs=tuple(dict.fromkeys((*e.evidence_refs, *(c['evidence_id'] for c in local)))),
                metadata={**e.metadata,'semantic_fallback':trace,'verification_level':'SEMANTIC_NOT_FORMAL'}))
        obligations[index] = e
    evidence=bridge.evidence.model_copy(update={'obligations':tuple(obligations)})
    updated=bridge.model_copy(update={'evidence':evidence})
    return updated,PautaEngine().evaluate(config,evidence,evidence_policy=MinimalEvidencePolicy())
