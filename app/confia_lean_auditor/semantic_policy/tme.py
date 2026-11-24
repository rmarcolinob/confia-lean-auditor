"""Semantic B opinions on unsettled obligations; PautaEngine remains the only scorer."""
from .service import assess, VERSION, specialized_policy
from confia_lean_auditor.rubric.pauta.engine import PautaEngine


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


def apply(config, bridge, solution, statement, *, provider=None):
    originals={r.record_id:r for r in bridge.auditor.records}
    definitions={o.id:o for o in config.obligations}
    obligations=[]
    for e in bridge.evidence.obligations:
        candidates=[originals[k] for k in e.source_claim_ids if k in originals]
        eligible=(e.status not in {'supported','refuted'} and e.attributable_to_student
            and e.grounding_status=='grounded' and candidates
            and all(r.semantic_role.value not in {'assumption','quoted_statement','rejected_attempt'} for r in candidates)
            and not any(v.get('effective_status')=='refuted' for v in e.metadata.get('verifications',[]))
            and not e.metadata.get('reason','').startswith('CONFLICTING'))
        if eligible:
            trace=assess(dict(solution=solution,statement=statement,
                criterion=definitions[e.obligation_id].model_dump(mode='json'),
                rubric=config.model_dump(mode='json'), evidence=[r.model_dump(mode='json') for r in candidates],
                checks=e.model_dump(mode='json'), reason='formal_obligation_not_satisfied'),provider)
            status={'met':'supported','not_met':'refuted','review':'technical_error' if trace.get('error_type') else 'indeterminate'}[trace['decision']]
            e=e.model_copy(update=dict(status=status,origin='semantic',verification_source='semantic',
                metadata={**e.metadata,'semantic_fallback':trace,'verification_level':'SEMANTIC_NOT_FORMAL'}))
        obligations.append(e)
    evidence=bridge.evidence.model_copy(update={'obligations':tuple(obligations)})
    updated=bridge.model_copy(update={'evidence':evidence})
    return updated,PautaEngine().evaluate(config,evidence,evidence_policy=MinimalEvidencePolicy())
