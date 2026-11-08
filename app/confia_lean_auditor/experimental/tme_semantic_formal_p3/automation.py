"""Common admission boundary; only the central veto policy can authorize veto."""
from copy import deepcopy
from confia_lean_auditor.student_claims.semantic import sha
from .semantic_contracts import SAFE_FIDELITY, SAFE_BINDING, checker_input
from .registry import REGISTRY,registry_rows

VERSION='p3-automation-v1'
POSITIVE={'FORMAL_VERIFIED','DETERMINISTIC_VERIFIED','COMPOSITE_VERIFIED'}
NEGATIVE={'FORMAL_REFUTED','DETERMINISTIC_FAILED','COMPOSITE_FAILED','STRUCTURAL_INCOMPATIBILITY_VERIFIED'}

class AutomationEligibilityPolicy:
    def __init__(self,snapshot):
        if not snapshot.valid():raise ValueError('stale_semantic_snapshot')
        self.snapshot=snapshot
        self._issued={}

    def admission(self,ids,oid,*,positive=False,primary_ids=None):
        reasons=[]; chains=[]
        primary=set(primary_ids or ids)
        for eid in ids:
            d=self.snapshot.get(eid)
            if not d: reasons.append('missing_claim');continue
            r=d.representation_receipt; bs=d.binding_receipts
            applicable=[b for b in bs if b['obligation_id']==oid] if eid in primary else bs
            if not d.binding_valid:reasons.append('invalid_source_binding')
            if d.state!='ACTIVE':reasons.append('discourse_'+d.state.lower())
            if r.get('representation_fidelity') not in SAFE_FIDELITY:reasons.append('insufficient_fidelity')
            if not any(b['binding_status'] in SAFE_BINDING for b in applicable):reasons.append('invalid_or_ambiguous_binding')
            if positive and (r.get('proposition') or {}).get('kind')=='member':reasons.append('membership_is_not_positive_set')
            chains.append(dict(evidence_id=eid,segment=d.segment,discourse=d.as_dict(),
                               representation=r,bindings=applicable))
        if not ids:reasons.append('no_premises')
        return dict(admitted=not reasons,reasons=sorted(set(reasons)),chains=chains)

    def decide(self,result,*,veto_receipt=None,veto_authenticator=None,blocked=False,positive=True):
        ids=result.get('evidence_ids') or [result.get('evidence_id')]
        ids=[i for i in ids if i]
        admission=self.admission(ids,result['obligation_id'],positive=positive,
                                 primary_ids=result.get('primary_evidence_ids'))
        reasons=list(admission['reasons']); action='REVIEW_ONLY'
        if result.get('checker_input_receipt')!=checker_input(self.snapshot,result):reasons.append('checker_input_not_bound')
        if not(result.get('verification_id') or result.get('guard_id')):reasons.append('no_checker_receipt')
        if positive:
            spec=REGISTRY.get(result['obligation_id'])
            if not spec or result.get('route') not in spec.allowed_routes:reasons.append('route_not_authorized')
            if not result.get('original_fact'):reasons.append('no_positive_checker_fact')
            if result.get('status') not in POSITIVE:reasons.append('checker_not_verified')
            if not result.get('sufficiency_decision',{}).get('sufficient'):reasons.append('insufficient')
            if result.get('guard_only'):reasons.append('guard_cannot_award')
            if blocked:reasons.append('central_veto_applied')
            if not reasons:action='AUTO_AWARD'
        else:
            if result.get('status') not in NEGATIVE or result.get('mathematical_refutation') is not True:reasons.append('checker_not_refutation')
            # Only called with an authentic decision by the owning veto policy.
            if not veto_receipt or not veto_authenticator or not veto_authenticator(veto_receipt) or not veto_receipt.get('hard_veto_eligible'):reasons.append('central_veto_not_authorized')
            if not reasons:action='AUTO_VETO'
        decision=dict(version=VERSION,registry_revision=sha(registry_rows()),
            checker_context=result.get('checker_metadata') or result.get('checker_receipt'),obligation_id=result['obligation_id'],evidence_ids=ids,
            automation_eligibility=action,authority_for_positive_credit=action=='AUTO_AWARD',
            authority_for_hard_veto=action=='AUTO_VETO',authority_for_review_only=action=='REVIEW_ONLY',
            reasons=sorted(set(reasons)),source_sha256=self.snapshot.source_sha256,
            ledger_revision=self.snapshot.ledger_revision,provenance=admission['chains'],
            checker_ref=result.get('verification_id') or result.get('guard_id'),
            checker_input_receipt=result.get('checker_input_receipt'),
            checker_status=result.get('status'),sufficiency=result.get('sufficiency_decision'),
            veto_policy_ref=veto_receipt.get('decision_id') if veto_receipt else None)
        decision['decision_id']='automation:'+sha(decision)
        self._issued[decision['decision_id']]=deepcopy(decision)
        return decision
