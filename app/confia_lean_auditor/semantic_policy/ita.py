"""Minimal fallback for undecided ITA criteria, mutually exclusive with SCORE-POLICY-02."""
from .service import assess, VERSION
from confia_lean_auditor.rubric.assessment import refresh_assessment
from confia_lean_auditor.rubric.secondary_context import prepare_payload
from confia_lean_auditor.rubric.secondary_award_gate import _scope_issue
from confia_lean_auditor.student_claims.schemas import is_mathematically_refuted


def apply(*, rubric, solution, assets, microclaims, student_claim_checks, claim_context=None,
          technical_issue=False, claim_extraction=None, provider=None):
    refresh_assessment(rubric)
    rubric.scoring_policy = VERSION
    rubric.secondary_adjudication = {'policy': VERSION, 'criteria': {}}
    pending = [i for i in rubric.items if i.points is None]
    payload = prepare_payload(pending=pending, solution=solution, assets=assets,
        microclaims=microclaims, student_checks=student_claim_checks, claim_context=claim_context)
    rows = {r['id']:r for r in payload['pending_criteria']}
    for item in rubric.items:
        item.verified_points = item.points
        item.suggested_points = item.points
        item.scoring_basis = 'first_pass' if item.points is not None else 'unscorable'
        if item.points is not None:
            continue
        row = rows[item.id]
        claims = row.get('award_grounded_claims', [])
        checks = row.get('award_verification_results', [])
        candidates = []
        for c in claims:
            span = c.get('source_span') or {}; a,b = span.get('start'),span.get('end')
            if c.get('semantic_role') in {'assumption','quoted_statement','rejected_attempt'}:
                continue
            if isinstance(a,int) and isinstance(b,int) and solution[a:b] == c['text']:
                e = dict(source_start=a,source_end=b,source_text=c['text'])
                if not _scope_issue(e, solution, row): candidates.append(e)
        for c in checks:
            g = c.get('grounding') or {}
            a,b = g.get('source_start'),g.get('source_end')
            if isinstance(a,int) and isinstance(b,int) and 0 <= a < b <= len(solution):
                e = dict(source_start=a,source_end=b,source_text=solution[a:b])
                if not _scope_issue(e, solution, row): candidates.append(e)
        blocked = any(is_mathematically_refuted(c) or c.get('status') == 'failed' for c in checks)
        conflict = any(a.get('status') == 'conflicting' for c in claims for a in c.get('alignment',[]))
        if not candidates or blocked or conflict:
            rubric.secondary_adjudication['criteria'][item.id] = dict(decision='review',
                reason='conflicting_failed' if blocked or conflict else 'no_eligible_evidence')
            continue
        trace = assess(dict(problem_id=getattr(assets.problem,'id',''), solution=solution,
            statement=assets.problem.statement, criterion=next(c.model_dump(mode='json') for c in assets.rubric.items if c.id==item.id),
            rubric=assets.rubric.model_dump(mode='json'), evidence=candidates, checks=checks,
            microclaims=[m.model_dump(mode='json') for m in microclaims],
            reason='formal_obligation_not_satisfied' if any(c.get('status')=='verified' for c in checks) else 'claim_not_verified'),provider)
        rubric.secondary_adjudication['criteria'][item.id] = trace
        item.scoring_evidence = [q['text'] for q in trace.get('quotes',[])]
        item.scoring_rationale = trace.get('response',{}).get('justification')
        item.adjustment_notes.append('Avaliação semântica pela rubrica; sem certificação formal.')
        if trace['decision'] != 'review':
            item.suggested_points = item.max_points if trace['decision']=='met' else 0.0
            item.scoring_basis = 'semantic_fallback'
    values=[i.suggested_points for i in rubric.items]
    rubric.score = sum(values) if all(v is not None for v in values) else None
    rubric.needs_review = technical_issue or rubric.score is None or any(i.scoring_basis == "semantic_fallback" for i in rubric.items)
    rubric.coverage = rubric.evaluated_max_score / rubric.max_score if rubric.max_score else 0
    rubric.estimated_points = rubric.score-rubric.evaluated_score if rubric.score is not None else None
    semantic_failure = any(t.get('error_type') for t in rubric.secondary_adjudication['criteria'].values())
    rubric.unscorable_reason = ('SEMANTIC_PROVIDER_FAILURE' if semantic_failure else 'SEMANTIC_REVIEW_REQUIRED') if rubric.score is None else None
    return rubric
