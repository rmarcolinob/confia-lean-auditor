"""Literal accepted-item context for the minimal fallback, never mathematical facts."""
import hashlib
from types import SimpleNamespace

from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.student_claims.sufficiency_requirements import requirements


def accepted_contexts(bridge, solution, items):
    if items is None:
        return {}
    texts = {k: v if isinstance(v, str) else v.get('text', '') for k, v in items.items()}
    # Same explicit item framing used by collect_digital_items. Bind the supplied
    # mapping to the auditor's input, without running extraction/checkers again.
    framed = ''.join(f'[{k}]\n{texts[k]}\n\n' for k in 'abcd' if k in texts)
    if hashlib.sha256(framed.encode()).hexdigest() != bridge.auditor.source_sha256:
        raise ValueError('TME_ITEM_CONTEXT_SOURCE_MISMATCH')
    contexts = {}
    for item, text in texts.items():
        bindings = []
        units = [SimpleNamespace(exact_text=text)] if text.strip() and text in solution else evidence_units(text)
        for unit in units:
            literal = unit.exact_text
            start = 0
            occurrences = []
            while (start := solution.find(literal, start)) >= 0:
                occurrences.append(dict(start=start, end=start+len(literal)))
                start += 1
            if not occurrences:
                raise ValueError('TME_ITEM_CONTEXT_NOT_LITERAL')
            bindings.append(dict(item_id=item, source_text=literal, occurrences=occurrences,
                evidence_id='accepted:' + item + ':' + hashlib.sha256(literal.encode()).hexdigest()))
        if bindings:
            contexts[item] = dict(text=text, bindings=bindings)
    return contexts


def obligation_contexts(config, contexts, obligation_id):
    requirement = next(r for r in requirements(config.problem_id) if r['obligation_id'] == obligation_id)
    target = requirement['item_id']
    if target not in contexts:
        return requirement, []  # Never fill an absent item from another answer.
    allowed = [target, *requirement['authorized_source_items']]
    selected = []
    for item in allowed:
        context = contexts.get(item)
        if not context:
            continue
        # This is full source context for a reviewer, not an extracted positive
        # assertion. Preserve hypotheses, quotations and rejected attempts so the
        # reviewer can judge their role; an extractor's assertion gate would
        # incorrectly hide valid conditional/contradiction proofs here.
        selected.extend(context['bindings'])
    return requirement, selected


def quotes_in_context(trace, contexts):
    """Global literal validation alone cannot authorize evidence from another item."""
    return all(any(q['text'] in c['source_text'] for c in contexts) for q in trace.get('quotes', []))
