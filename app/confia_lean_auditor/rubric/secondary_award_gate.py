"""Objective secondary-award prerequisites; never proves or scores a claim.

The model still judges semantic sufficiency. This gate vetoes known violations
of the rubric contract, without borrowing the primary gate's extraction rules.
"""
import re
from .secondary_candidates import candidate_binding
from .positive_evidence import canonical, equation, Requirement, quoted_ranges
from confia_lean_auditor.student_claims.grounding import source_matches
from confia_lean_auditor.student_claims.schemas import is_mathematically_refuted

VERSION = "secondary-award-gate-v1"
VERIFIED = {"verified_by_lean", "verified_by_formal_steps"}


def answer_only(criterion):
    # Read the declared criterion, not its ID or the presence of an expected value.
    return bool(criterion.get('conclusion_only') or
                re.match(r'^conclui\b', canonical(criterion.get('description', ''))))


def _scope_issue(candidate, source, criterion):
    """Inspect enclosing source, so selecting an equation cannot erase its wrapper.

    Deliberately bounded discourse checks, not a general semantic parser. Known
    mathematical negations declared by the rubric are exempted, not all negation.
    """
    a, b = candidate['source_start'], candidate['source_end']
    if any(a < end and b > start for start, end in quoted_ranges(source)):
        return 'QUOTED_CONTEXT'
    # Paragraph scope retains multiline hypotheses and abandoned attempts.
    left = source.rfind('\n\n', 0, a) + 2
    left = max(0, left if left > 1 else 0)
    right = source.find('\n\n', b)
    context = source[left:right if right >= 0 else len(source)]
    # A genuinely new conclusion after an explicitly abandoned attempt may stand
    # on its own. Never discard a rejection following the selected span.
    prefix = source[left:a]
    transitions = list(re.finditer(r'(?<=[.!?])\s*(?:Logo|Portanto|Concluo)\b', prefix))
    if transitions and re.search(r'\b(?:abandon\w*|rejeit\w*)\b', canonical(prefix[:transitions[-1].start()])):
        context = source[left+transitions[-1].start():right if right >= 0 else len(source)]
    text = canonical(context)
    for pattern in criterion.get('allowed_mathematical_negations', []):
        text = re.sub(pattern, ' ', text)
    if re.search(r'\b(?:abandon\w*|rejeit\w*|descart\w*|tentativa\s+(?:errada|falha)|tentei)\b', text):
        return 'REJECTED_ATTEMPT'
    if (re.search(r'\b(?:suponh\w*|supondo|hipotetic\w*|assumindo|por\s+hipotese)\b', text)
            or re.search(r'(?:^|[.!?\n])\s*se\b', text)):
        return 'HYPOTHETICAL_CONTEXT'
    if re.search(r'\b(?:nao\s+(?:e|afirmo|concluo|vale|satisfaz|obtem|resulta)|e\s+falso|falso\s+que)\b', text):
        return 'NEGATED_CONTEXT'
    # Direct negation of the selected assertion (including a prefix outside it).
    if re.search(r'\b(?:nao|nunca)\s*[:(]?\s*$', canonical(source[max(left,a-40):a])):
        return 'NEGATED_CONTEXT'
    if re.match(r'\s*(?:nao|nunca)\b', canonical(candidate['source_text'])):
        cleaned = canonical(candidate['source_text'])
        for pattern in criterion.get('allowed_mathematical_negations', []):
            cleaned = re.sub(pattern, ' ', cleaned)
        if re.match(r'\s*(?:nao|nunca)\b', cleaned):
            return 'NEGATED_CONTEXT'
    if re.search(r'\b(?:enunciado\s+(?:diz|pede)|prove\s+que|mostre\s+que)\b', canonical(candidate['source_text'])):
        return 'COPIED_PROBLEM_STATEMENT'
    return None


def can_secondary_award(criterion, selected_evidence, *, source, statement=''):
    """Eligibility is necessary, never sufficient for an award.

    No problem/solution IDs, target-value shortcuts, new microclaims or alternative
    methods are introduced. Relation alternatives come from the existing rules.
    """
    reasons = []
    if not selected_evidence or any(not candidate_binding(e, source) for e in selected_evidence):
        reasons.append('INVALID_SOURCE_BINDING')
    for mc in criterion.get('required_microclaims', []):
        # New engine payloads carry the existing dependency-policy result. Legacy
        # replay payloads retain the old explicit verified status, never a guess.
        if mc.get('satisfied', mc.get('status') in VERIFIED) is not True:
            reasons.append('MISSING_REQUIRED_MICROCLAIM')
    for check in criterion.get('award_verification_results', criterion.get('candidate_student_checks', [])):
        if source_matches(check, source) and is_mathematically_refuted(check):
            reasons.append('KNOWN_MATHEMATICAL_CONTRADICTION')
    for claim in criterion.get('award_grounded_claims', criterion.get('grounded_claims', [])):
        span = claim.get('source_span') or {}; a, b = span.get('start'), span.get('end')
        if type(a) is int and type(b) is int and 0 <= a < b <= len(source) and source[a:b] == claim.get('text'):
            if any(x.get('status') == 'conflicting' for x in claim.get('alignment', [])):
                reasons.append('KNOWN_CLAIM_CONFLICT')
    safe = [e for e in selected_evidence if candidate_binding(e, source)]
    for e in safe:
        issue = _scope_issue(e, source, criterion)
        if issue:
            reasons.append(issue)
        # A copied problem is not an achievement. An explicit conclusion-only
        # rubric may legitimately ask the student simply to state that result.
        compact = re.sub(r'\s+', '', canonical(e['source_text'])).strip('.;:')
        prompt = re.sub(r'\s+', '', canonical(statement))
        if compact and compact in prompt and not answer_only(criterion):
            reasons.append('COPIED_PROBLEM_STATEMENT')
    for requirement in ([] if answer_only(criterion) else criterion.get('coded_requirements', [])):
        # Each group is one required relation, with explicitly declared equivalent
        # alternatives. Prose/derivation requirements remain the model's job.
        for alternatives in requirement.get('relation_alternatives', []):
            matches = False
            for relation in alternatives:
                if relation.count('=') != 1:
                    continue
                lhs, rhs = relation.split('=')
                check = Requirement(requirement['description'], (equation(lhs, rhs),))
                if any(check.matches(e['source_text']) for e in safe):
                    matches = True
            if not matches:
                reasons.append('MISSING_DECLARED_RELATION')
    reasons = list(dict.fromkeys(reasons))
    return {'version': VERSION, 'eligible': not reasons, 'reasons': reasons,
            'scope': 'objective_prerequisites_only_not_mathematical_proof'}
