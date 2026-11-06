"""Source-local validation of model abandonment, exclusively for safety views.

Original EvidenceUnits and positive mappings are never promoted. A recovered
view may be checked for contradictions; even a verified result cannot award.
"""
import re
from confia_lean_auditor.student_claims.semantic import normalized, sha
from .mapper import local_context, representation, source_view, _anchor


def source_bound(document, e):
    owner = [k for k, (a, b) in document.ranges.items()
             if a <= e.source_start < e.source_end <= b]
    return (owner == [e.item_id]
            and document.text[e.source_start:e.source_end] == e.source_span
            and e.metadata.get('source_sha256') == sha(document.text))


def _literal_payload(document, e):
    # Same source validation as positive claims; no mathematical truth inferred.
    try:
        value = representation(e, document).canonical_form.value
        if e.claim_type == 'integer_set':
            return ('written_members', tuple(sorted(str(x) for x in value['value'])))
        return (e.claim_type, value.get('expression', value.get('value')))
    except ValueError:
        # Partial repeat-membership prose need not pretend to be a full set.
        if e.subject == 'repeticao_branca' and _anchor(e, document):
            raw = source_view(e.source_span)
            members = re.findall(r'\b(?:o\s+)?([1-6])\s+(?:tambem|libera|funciona)\b', raw)
            if len(members) == 1:
                return ('written_members', (members[0],))
    return None


def abandonment_support(document, e, evidence):
    """Return a textual receipt, not a mathematical verdict or last-wins rule."""
    raw = normalized(e.source_span)
    own = re.search(r'\b(?:tentativa\s+(?:explicitamente\s+)?(?:abandonada|descartada)|'
                    r'(?:afirmacao|resposta)\s+(?:abandonada|descartada)|isso\s+esta\s+errado)\b', raw)
    if own:
        return True, 'explicit_abandonment_in_span', e.source_span
    # Only immediately following, unambiguous deictic rejection targets this
    # assertion. An unrelated later correction cannot silently revoke it.
    tail = document.text[e.source_end:document.ranges[e.item_id][1]]
    rejection = re.match(r'^[\s.;]*(isso\s+esta\s+errado\b|'
        r'corrigindo\s+(?:(?:a\s+)?minha|a)\s+afirmacao\s+anterior\b|'
        r'desconsidere\s+(?:a\s+(?:minha\s+)?afirmacao\s+anterior|o\s+que\s+acabei\s+de\s+afirmar)\b|'
        r'nao,\s*o\s+correto\s+e\b)', normalized(tail))
    if rejection:
        return True, 'immediate_explicit_retraction', tail[:rejection.end()]
    for correction in evidence:
        if correction.source_start < e.source_end or correction.evidence_id == e.evidence_id:
            continue
        gap = document.text[e.source_end:correction.source_start]
        if gap.strip(' \t\r\n.;') or '\n\n' in gap:
            continue
        if (not source_bound(document, correction) or correction.item_id != e.item_id
                or correction.subject != e.subject
                or not set(e.obligation_candidates) & set(correction.obligation_candidates)
                or correction.assertion_status != 'asserted' or correction.abandoned
                or correction.hypothetical or not correction.attributed_to_student
                or correction.polarity != 'positive'
                or correction.scope not in {'main_argument', 'final_conclusion'}
                or not local_context(document, correction)):
            continue
        if not re.match(r'^\s*(?:na verdade|corrigindo)\b', normalized(correction.source_span)):
            continue
        before = _literal_payload(document, e)
        after = _literal_payload(document, correction)
        if before is not None and after is not None and before != after:
            return True, 'adjacent_same_subject_correction', correction.source_span
    return False, 'no_unambiguous_local_retraction', None


def conflict_visibility(document, evidence):
    """Recover unsupported abandonment for safety only; audit every such flag."""
    views = []; decisions = []
    for e in evidence:
        model_abandoned = e.abandoned or e.assertion_status == 'abandoned'
        if not model_abandoned:
            views.append(e)
            continue
        supported, reason, reference = False, 'invalid_source_binding', None
        if source_bound(document, e):
            supported, reason, reference = abandonment_support(document, e, evidence)
        other_context_ok = (source_bound(document, e)
            and e.assertion_status in {'asserted', 'abandoned'} and e.polarity == 'positive'
            and e.attributed_to_student and not e.hypothetical
            and local_context(document, e))
        visible = other_context_ok and not supported
        decision = dict(evidence_id=e.evidence_id, source_span=e.source_span,
            source_start=e.source_start, source_end=e.source_end,
            source_sha256=e.metadata.get('source_sha256'), item_id=e.item_id, subject=e.subject,
            model_abandoned=e.abandoned, model_assertion_status=e.assertion_status, model_scope=e.scope,
            abandonment_textually_supported=supported, abandonment_reason=reason,
            retraction_source_span=reference, other_context_valid=other_context_ok,
            effective_conflict_visibility=visible, positive_credit_eligible=False)
        decisions.append(decision)
        if visible:
            views.append(e.model_copy(update=dict(assertion_status='asserted', abandoned=False, scope='main_argument',
                metadata=dict(e.metadata, abandonment_safety=decision))))
        else:
            views.append(e)
    return views, decisions


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
            abandonment_decisions=[by_id[i].metadata['abandonment_safety'] for i in sorted(involved)]))
    return guards
