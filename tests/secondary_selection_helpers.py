"""Explicit model-side ID selections for tests of the current API contract."""
from confia_lean_auditor.rubric import secondary_adjudicator as secondary
from confia_lean_auditor.rubric.secondary_candidates import with_candidates

def selection(payload, kind='award', reason=None):
    p=with_candidates(payload,secondary.redact) if 'solution_text' in payload else payload
    reason=reason or ('SATISFIES_CRITERION' if kind=='award' else 'INSUFFICIENT_EVIDENCE')
    return {c['id']:{'decision':kind,'suggested_points':c['max_points'] if kind=='award' else 0,
        'evidence_ids':[e['evidence_id'] for e in c.get('candidate_evidence',[])[:1]] if reason!='INSUFFICIENT_EVIDENCE' else [],
        'reason_code':reason,'rationale':secondary.selection_rationales(c,reason)[0]} for c in p['pending_criteria']}
