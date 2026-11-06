"""Compatibility views; discourse authority lives only in the central resolver."""
from confia_lean_auditor.student_claims.semantic import sha
from .discourse import DiscourseStateResolver


def source_bound(document,e):
    return (document.text[e.source_start:e.source_end]==e.source_span
            and e.metadata.get('source_sha256')==sha(document.text)
            and any(k==e.item_id and a<=e.source_start<e.source_end<=b for k,(a,b) in document.ranges.items()))


def conflict_visibility(document,evidence):
    snapshot,views,_,_=DiscourseStateResolver().resolve(document,evidence)
    decisions=[]
    for e in evidence:
        if not(e.abandoned or e.assertion_status=='abandoned'):continue
        d=snapshot.get(e.evidence_id)
        decisions.append(dict(evidence_id=e.evidence_id,abandonment_textually_supported=d.state in {'SUPERSEDED','NON_ADOPTED'},
            abandonment_reason=d.reason,retraction_source_span=d.supporting_spans,
            effective_conflict_visibility=d.binding_valid and d.state=='ACTIVE',positive_credit_eligible=d.positive_credit_eligible,
            discourse_decision=d.as_dict()))
    return views,decisions


def regular_safety_checks(document, views, mapping, config, case_id, recovered):
    """Use unchanged checkers on a safety-only projection; never emit awards."""
    if not recovered:
        return []
    from .verification import verify
    _, results, _ = verify(document, views, mapping, config, case_id + '-abandonment-guard', use_lean=False)
    by_id = {e.evidence_id: e for e in views}
    guards = []
    for r in results:
        involved = set(r['evidence_ids']) & recovered
        if not involved or not r.get('original_fact'):
            continue
        guards.append(dict(evidence_id=sorted(involved)[0], evidence_ids=r['evidence_ids'],
            obligation_id=r['obligation_id'], status=r['status'],
            mathematical_refutation=r['mathematical_refutation'],
            checker_result=r, guard_only=True, award_eligible=False,
            sufficiency_decision=dict(sufficient=False, basis='guard_cannot_award'),
            abandonment_decisions=[by_id[i].metadata['discourse_decision'] for i in sorted(involved)]))
    return guards
