"""P3 orchestration: common ledger → state → producers → central authority."""
from confia_lean_auditor.student_claims.semantic import sha
from .source_adapter import native_units,member_atom,exact_members
from .discourse import DiscourseStateResolver
from .mapper import ObligationMapper
from .verification import verify
from .conflict_guard import conflict_guards
from .veto_policy import VetoEligibilityPolicy,candidate,reconcile


def structural_candidates(document,units,snapshot):
    """Source-checked exact-set/member incompatibility; never positive support."""
    results=[]
    for e in units:
        atom=member_atom(e)
        if not atom:continue
        for other in units:
            members=exact_members(other)
            if other.item_id!=e.item_id or other.subject!=atom['property'] or members is None:continue
            if set(atom['members'])<=set(members):continue
            # The checker validates a relation between two written propositions,
            # not a reference answer. State eligibility is decided downstream.
            results.append(dict(guard_id='structural:'+sha([e.evidence_id,other.evidence_id,atom,members]),
                evidence_id=e.evidence_id,evidence_ids=[e.evidence_id,other.evidence_id],
                obligation_id=atom['obligation_id'],status='STRUCTURAL_INCOMPATIBILITY_VERIFIED',
                mathematical_refutation=True,contradiction_type='written_exact_set_excludes_written_member',
                checker='source_exact_set_membership_relation',checker_receipt=dict(partial=atom,exact_set=members,
                    source_sha256=sha(document.text),source_ranges=[[e.source_start,e.source_end],[other.source_start,other.source_end]]),
                guard_only=True,award_eligible=False,sufficiency_decision=dict(sufficient=False,basis='guard_cannot_award')))
    return results


def run_unified(document,units,config,case_id,*,use_lean,fallback=False):
    inventory=[]
    native=native_units(document,inventory)
    snapshot,views,ledger,adaptations=DiscourseStateResolver().resolve(document,tuple(units)+native)
    semantic_ids={u.evidence_id for u in units}
    positives=tuple(v for v in views if (v.evidence_id in semantic_ids or fallback))
    mapping=ObligationMapper().map(document,positives)
    bridge,results,projection=verify(document,positives,mapping,config,case_id,use_lean=use_lean)
    # The second deterministic producer sees the same resolved state before
    # composition. It cannot reintroduce withdrawn native records.
    native_mapping=ObligationMapper().map(document,views)
    native_bridge,native_results,native_projection=verify(document,views,native_mapping,config,case_id+'-native-guard',use_lean=False)
    active_views=[v for v in views if snapshot.get(v.evidence_id).positive_credit_eligible]
    active_mapping=ObligationMapper().map(document,active_views)
    atomic=[]
    try:
        atomic=conflict_guards(document,active_views,active_mapping)
    except Exception as error:
        # A failed producer is technical uncertainty, never a refutation.
        for v in active_views:
            if v.subject!='repeticao_branca':continue
            atomic.append(dict(guard_id='atomic-error:'+sha(v.evidence_id),evidence_id=v.evidence_id,
                obligation_id='b.same_compartment',status='DETERMINISTIC_ERROR',
                mathematical_refutation=False,technical_uncertainty=True,guard_only=True,award_eligible=False,
                checker_receipt=dict(error_type=type(error).__name__),
                sufficiency_decision=dict(sufficient=False,basis='guard_cannot_award')))
    structural=structural_candidates(document,views,snapshot)
    policy=VetoEligibilityPolicy(snapshot)
    decisions=[]
    for producer,rows in [('positive_checker',results),('native_checker',native_results),('atomic_guard',atomic),('structural_guard',structural)]:
        for row in rows:
            if row.get('original_fact') or row.get('guard_id'):
                decisions.append(policy.decide(candidate(row,producer)))
    conflicts=reconcile(policy,decisions)
    # Compatibility trace: it no longer drives decisions or revives a record.
    abandonment=[];regular=[]
    for u in units:
        if not(u.abandoned or u.assertion_status=='abandoned'):continue
        d=snapshot.get(u.evidence_id)
        abandonment.append(dict(evidence_id=u.evidence_id,source_span=u.source_span,
            abandonment_textually_supported=d.state in {'SUPERSEDED','NON_ADOPTED'},
            abandonment_reason=d.reason,retraction_source_span=d.supporting_spans,
            effective_conflict_visibility=d.state=='ACTIVE',positive_credit_eligible=d.positive_credit_eligible,
            discourse_decision=d.as_dict()))
        for r in native_results:
            if u.evidence_id in r['evidence_ids'] and r.get('original_fact'):
                regular.append(dict(evidence_id=u.evidence_id,evidence_ids=r['evidence_ids'],obligation_id=r['obligation_id'],
                    status=r['status'],mathematical_refutation=r['mathematical_refutation'],checker_result=r,
                    guard_only=True,award_eligible=False,sufficiency_decision=dict(sufficient=False,basis='guard_cannot_award')))
    trace=dict(native_source_inventory=inventory,discourse_ledger=ledger,discourse_decisions=[d.as_dict() for d in snapshot.decisions],
        ledger_revision=snapshot.ledger_revision,source_adaptations=adaptations,veto_decisions=decisions,
        conflict_guard_results=atomic,structural_guard_results=structural,abandonment_decisions=abandonment,
        abandonment_guard_results=regular,native_guard_results=native_results,native_projection=native_projection,
        native_mathematical_bridge=native_bridge.model_dump(mode='json'))
    return positives,mapping,bridge,results,projection,policy,conflicts,trace
