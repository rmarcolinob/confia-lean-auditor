"""The only authority for a negative producer to defeat an independent award."""
from copy import deepcopy
from confia_lean_auditor.student_claims.semantic import sha
from .registry import REGISTRY

VERSION='p3-veto-v2'
DEPENDENCIES={
 'b.ordered_pairs':('b.second_white_probability',),
 'b.different_favorable':('b.second_white_probability',),
 'b.same_compartment':('b.second_white_probability',),
 'c.strategy_case_1':('c.conditional_success_1','c.total_win_probability'),
 'c.strategy_case_2':('c.conditional_success_2','c.total_win_probability'),
 'c.continue_compartments':('c.total_win_probability',),
 'c.conditional_success_1':('c.total_win_probability',),
 'c.conditional_success_2':('c.total_win_probability',),
}
FAILED={'FORMAL_REFUTED','DETERMINISTIC_FAILED','COMPOSITE_FAILED','STRUCTURAL_INCOMPATIBILITY_VERIFIED'}


def candidate(result,producer):
    ids=result.get('evidence_ids') or [result.get('evidence_id')]
    return dict(evidence_ids=[i for i in ids if i],primary_evidence_ids=result.get('primary_evidence_ids') or [i for i in ids if i],obligation_id=result['obligation_id'],
        checker_status=result['status'],checker_ref=result.get('verification_id') or result.get('guard_id'),
        mathematical_contradiction=result.get('mathematical_refutation',False),
        contradiction_type=result.get('contradiction_type','mathematical_refutation'),
        provenance=dict(producer=producer,guard_only=result.get('guard_only',False)),checker_result=result)


class VetoEligibilityPolicy:
    def __init__(self,snapshot):
        if not snapshot.valid():raise ValueError('invalid_discourse_snapshot')
        self.snapshot=snapshot
        self._issued={}
        from .automation import AutomationEligibilityPolicy
        self.automation=AutomationEligibilityPolicy(snapshot)

    def decide(self,c):
        states=[self.snapshot.get(i) for i in c['evidence_ids']]
        bound=bool(states) and all(d and d.binding_valid for d in states)
        active=bound and all(d.state=='ACTIVE' for d in states)
        targets=[c['obligation_id'],*DEPENDENCIES.get(c['obligation_id'],())]
        status=c['checker_status']
        validated=(bool(c.get('checker_ref')) and c.get('mathematical_contradiction') is True and status in FAILED)
        spec=REGISTRY.get(c['obligation_id'])
        primary=[self.snapshot.get(i) for i in c.get('primary_evidence_ids',c['evidence_ids'])]
        compatible=bool(bound and spec and all(d.property_key[0]==spec.rubric_item for d in states)
            and any(d and d.property_key[1] in spec.subjects for d in primary))
        admission=self.automation.admission(c['evidence_ids'],c['obligation_id'],primary_ids=c.get('primary_evidence_ids'))
        from .semantic_contracts import checker_input
        input_valid=(c['checker_result'].get('checker_input_receipt')==checker_input(self.snapshot,c['checker_result'])
            and c['checker_status']==c['checker_result'].get('status')
            and c['mathematical_contradiction']==c['checker_result'].get('mathematical_refutation',False))
        eligible=bool(active and validated and compatible and admission['admitted'] and input_valid)
        reason=('invalid_binding' if not bound else 'historical_or_nonadopted' if any(d.state in {'SUPERSEDED','NON_ADOPTED'} for d in states)
                else 'ambiguous_review_only' if not active else 'checker_not_refutation' if not validated
                else 'incompatible_scope' if not compatible else 'semantic_admission_failed' if not admission['admitted'] else 'checker_input_not_bound' if not input_valid else 'active_checked_contradiction')
        decision=dict(policy_version=VERSION,ledger_revision=self.snapshot.ledger_revision,
            source_sha256=self.snapshot.source_sha256,evidence_ids=c['evidence_ids'],
            canonical_ids=sorted({d.canonical_id for d in states if d}),obligation_id=c['obligation_id'],
            target_obligation_ids=targets if eligible else [],discourse_states=[d.state if d else None for d in states],
            discourse_decision_refs=[d.as_dict() for d in states if d],source_ranges=[d.source_range for d in states if d],
            checker_status=status,checker_ref=c.get('checker_ref'),checker_result=c['checker_result'],
            mathematical_contradiction=c.get('mathematical_contradiction'),contradiction_type=c['contradiction_type'],
            provenance=dict(c['provenance'],source_sha256=self.snapshot.source_sha256),
            conflict_visible=any(d and d.conflict_visible for d in states),hard_veto_eligible=eligible,veto_reason=reason,
            dependency_paths=[[c['obligation_id'],t] for t in targets if t!=c['obligation_id']] if eligible else [],
            invariant='I7/I8/I9/I16' if eligible else 'I2/I4/I6/I15/I17',
            reconciliation_status='APPLIED' if eligible else 'REJECTED_BINDING' if not bound else 'REVIEW_ONLY' if reason=='ambiguous_review_only' else 'AUDIT_ONLY' if not active else 'NOT_APPLICABLE')
        decision['decision_id']='veto:'+sha(decision)
        self._issued[decision['decision_id']]=deepcopy(decision)
        automatic=self.automation.decide(c['checker_result'],positive=False,veto_receipt=decision,veto_authenticator=self.authentic)
        decision['automation_decision']=automatic
        self._issued[decision['decision_id']]=deepcopy(decision)
        return decision

    def authentic(self,d):
        return self.snapshot.valid() and self._issued.get(d.get('decision_id'))==d and d.get('ledger_revision')==self.snapshot.ledger_revision

    def applied(self,decisions):
        return [d for d in decisions if self.authentic(d) and d['hard_veto_eligible'] and d.get('automation_decision',{}).get('automation_eligibility')=='AUTO_VETO']


def reconcile(policy,decisions):
    """No raw flags, aggregated conflicts, ordering or confidence has authority."""
    grouped={}
    for d in policy.applied(decisions):
        for oid in d['target_obligation_ids']:
            grouped.setdefault(oid,{})[d['decision_id']]=d
    return [dict(obligation_id=oid,status='CONFLICTING_EVIDENCE',resolved=False,
                 reason='central_policy_active_contradiction',resolution_rule=VERSION,
                 evidence_ids=sorted({i for d in rows.values() for i in d['evidence_ids']}),
                 policy_decisions=[rows[k] for k in sorted(rows)]) for oid,rows in sorted(grouped.items())]
