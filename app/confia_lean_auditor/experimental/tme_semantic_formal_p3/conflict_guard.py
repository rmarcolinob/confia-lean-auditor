"""Partial membership evidence is veto-only, never a complete positive set.

The original mapper rejection remains visible. This bounded adapter recovers
an asserted member from its literal source, not from a model-supplied set or
truth judgment, and queries the frozen finite-machine certificate.
"""
import re
from confia_lean_auditor.student_claims.semantic import sha, normalized
from confia_lean_auditor.experimental.tme_p3_checker_first.components import finite_certificate
from confia_lean_auditor.tme.p3_machine import load_machine
from confia_lean_auditor.tme.registry import ROOT
from .mapper import local_context, ORDINALS

OBLIGATION = 'b.same_compartment'
SUBJECT = 'repeticao_branca'
REPRESENTATION_REJECTIONS = frozenset({
    'partial_membership_not_complete_set', 'unsupported_checker_payload', 'explicit_integer_set_required',
    'set_members_not_written', 'set_payload_omits_source_members',
    'subject_not_uniquely_bound_to_source_clause',
})
_ORDINAL = '|'.join(ORDINALS)
_MEMBER = re.compile(
    r'\b(?:o\s+)?(?:compartimento\s+(?P<index>\d+)|'
    r'(?P<ordinal>' + _ORDINAL + r')(?:\s+compartimento)?)\s+tamb[eé]m'
    r'(?P<property>\s+(?:libera|produz|fornece)\s+(?:(?:uma\s+)?bola\s+)?branca)?'
    r'\s*(?=[.;\n]|$)', re.I)


def _bound_context(document, evidence):
    owner = [key for key, (a, b) in document.ranges.items()
             if a <= evidence.source_start < evidence.source_end <= b]
    return (owner == ['b'] and evidence.item_id == 'b'
            and evidence.subject == SUBJECT
            and OBLIGATION in evidence.obligation_candidates
            and document.text[evidence.source_start:evidence.source_end] == evidence.source_span
            and evidence.metadata.get('source_sha256') == sha(document.text)
            and evidence.assertion_status == 'asserted' and evidence.polarity == 'positive'
            and evidence.attributed_to_student and not evidence.hypothetical and not evidence.abandoned
            and evidence.scope in {'main_argument', 'final_conclusion'}
            and local_context(document, evidence))


def _explicit_relation(span):
    text = normalized(span)
    return bool(re.search(r'\brepet\w*\b|\bmesmo compartimento\b', text)
                and re.search(r'\bbranc\w*\b', text))


def membership_result(compartment, machine):
    """An inclusion query, not equality with an invented complete set."""
    certificate = finite_certificate(machine)
    if type(compartment) is not int or not 1 <= compartment <= certificate['choice_count']:
        raise ValueError('invalid_compartment_index')
    event = next(e for e in certificate['events'] if e['pair'] == [compartment, compartment])
    verified = [compartment, compartment] in certificate['same_white']
    return dict(status='DETERMINISTIC_VERIFIED' if verified else 'DETERMINISTIC_FAILED',
                mathematical_refutation=not verified,
                checker='frozen_finite_certificate_same_white_membership',
                checker_receipt=dict(machine_source=certificate['machine_source'],
                    machine_sha256=certificate['machine_sha256'], event=event,
                    derived_same_white_pairs=certificate['same_white']))


def conflict_guards(document, evidence, mapping):
    """Recover only format-rejected members; never change positive mapping."""
    rejected = {m['evidence_id']: m['reason'] for m in mapping
                if m['obligation_id'] == OBLIGATION and not m['accepted']
                and m['reason'] in REPRESENTATION_REJECTIONS}
    bound = [e for e in evidence if _bound_context(document, e)]
    # Explicit same-family source supplies an elliptical relation, in either
    # order. It does not supply a member or a mathematical truth value.
    relation_written = any(_explicit_relation(e.source_span) for e in bound)
    results = []
    machine = None
    for e in bound:
        if e.evidence_id not in rejected:
            continue
        for match in _MEMBER.finditer(e.source_span):
            if not (_explicit_relation(e.source_span) or relation_written):
                continue
            token = match.group('index') or match.group('ordinal')
            compartment = int(token) if match.group('index') else int(ORDINALS[token.lower()])
            if machine is None:
                machine = load_machine(ROOT / 'examples/pautas/tme2_problem3.machine.v1.json')
            if not 1 <= compartment <= len(machine.stacks):
                continue  # Invalid index is not a refuted event in this model.
            check = membership_result(compartment, machine)
            start = e.source_start + (match.start('index') if match.group('index') else match.start('ordinal'))
            result = dict(
                guard_id='p3-membership-guard:' + sha([e.evidence_id, start, compartment])[:24],
                evidence_id=e.evidence_id, obligation_id=OBLIGATION, item_id=e.item_id, subject=e.subject,
                source_span=e.source_span, source_start=e.source_start, source_end=e.source_end,
                source_sha256=e.metadata['source_sha256'],
                assertion_status=e.assertion_status, polarity=e.polarity, scope=e.scope,
                hypothetical=e.hypothetical, abandoned=e.abandoned, attributed_to_student=e.attributed_to_student,
                atomic_claim=dict(kind='membership_claim', compartment=compartment,
                    relation='same_compartment_second_white', literal_token=token,
                    literal_start=start, literal_end=start + len(token)),
                original_normalized_claim=e.normalized_claim,
                abandonment_decision=e.metadata.get('abandonment_safety'),
                positive_mapping_rejection=rejected[e.evidence_id],
                route='DETERMINISTIC', guard_only=True, award_eligible=False,
                formal_status='FORMAL_NOT_ATTEMPTED', formal_attempted=False,
                sufficiency_decision=dict(sufficient=False, basis='guard_cannot_award'),
                **check)
            results.append(result)
    return results
