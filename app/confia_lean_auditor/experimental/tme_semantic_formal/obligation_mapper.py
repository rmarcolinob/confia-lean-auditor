"""Literal source, item ownership, context and closed obligation compatibility."""
from dataclasses import dataclass
import re
from types import SimpleNamespace
from confia_lean_auditor.student_claims.sufficiency_context import item_regions, link_evidence, context_gate
from confia_lean_auditor.student_claims.sufficiency_requirements import requirements
from confia_lean_auditor.student_claims.generic_math import contextual_role
from confia_lean_auditor.student_claims.semantic import sha
from .claim_router import ClaimRouter
from .obligation_registry import PROBLEM_ID, REGISTRY


@dataclass(frozen=True)
class SourceDocument:
    text: str
    items: dict
    ranges: dict

    @classmethod
    def parse(cls, text):
        if not isinstance(text, str) or len(text) > 19000:
            raise ValueError('source_must_be_text_up_to_19000_characters')
        ranges = {}
        for region in item_regions(text):
            item = region['item_id']
            if item is None:
                continue
            if item in ranges:
                raise ValueError('repeated_item_heading_requires_explicit_revision')
            start = region['start']
            heading = re.match(r'(?:\([a-d]\)|[a-d]\))\s*', text[start:region['end']], re.I)
            if heading:
                start += heading.end()
            ranges[item] = (start, region['end'])
        return cls(text, {k: text[a:b] for k, (a, b) in ranges.items()}, ranges)


class ObligationMapper:
    @staticmethod
    def candidates(document, evidence):
        """Recover the existing standalone inverse-answer role, never a substring.

        Only an entire item-a literal answer can use this narrow correction.
        Equations, labelled results, prose, other items and values extracted from
        a larger expression retain their original candidates and checker gates.
        This selects an obligation; it does not verify or authorize any credit.
        """
        from confia_lean_auditor.student_claims.digital_literals import literal_form
        from confia_lean_auditor.lean.student_claim_checkers.tme2_p1 import eq
        raw = evidence.source_span.strip()
        literal = literal_form(raw)
        if (evidence.claim_type == 'expression' and literal and literal[0] == 'math_literal'
                and evidence.normalized_claim.strip() == raw
                and document.items.get('a', '').strip() == raw
                and 'a' in evidence.rubric_candidates
                and all(o.startswith('a.') for o in evidence.obligation_candidates)
                and eq(raw, '137')):
            return ('a.identifies_137',)
        return evidence.obligation_candidates

    def map(self, document, evidence):
        reqs = {r['obligation_id']: r for r in requirements(PROBLEM_ID)}
        mapped = []
        interpretations = {}
        for e in evidence:
            for oid in self.candidates(document, e):
                key = (e.source_start, e.source_end, e.normalized_claim, oid)
                interpretations.setdefault(key, set()).add((e.assertion_status, e.polarity,
                    e.scope, e.hypothetical, e.abandoned, e.attributed_to_student))
        for e in evidence:
            candidates = self.candidates(document, e)
            for oid in candidates:
                row = dict(evidence_id=e.evidence_id, obligation_id=oid, accepted=False,
                           effective_route=None, reason='', context_valid=False,
                           suggested_route=e.verification_route_candidate,
                           route_override_reason=None,
                           suggested_obligation_candidates=list(e.obligation_candidates),
                           mapping_override_reason='standalone_item_a_inverse_role'
                               if tuple(candidates) != tuple(e.obligation_candidates) else None)
                try:
                    if oid not in REGISTRY:
                        raise ValueError('unknown_obligation')
                    if len(interpretations[(e.source_start, e.source_end, e.normalized_claim, oid)]) > 1:
                        raise ValueError('conflicting_extractor_context')
                    if (document.text[e.source_start:e.source_end] != e.source_span
                            or e.extractor_metadata.get('source_sha256') != sha(document.text)):
                        raise ValueError('source_binding_changed')
                    if not (e.attributed_to_student and e.assertion_status == 'asserted'
                            and e.polarity == 'positive' and not e.hypothetical and not e.abandoned
                            and e.scope in {'main_argument', 'final_conclusion'}):
                        raise ValueError('nonasserted_or_unattributed_context')
                    if REGISTRY[oid].rubric_item not in e.rubric_candidates:
                        raise ValueError('rubric_candidate_mismatch')
                    route = ClaimRouter().route(e, oid)
                    if route != e.verification_route_candidate:
                        row['route_override_reason'] = 'obligation_registry'
                    # Even a hostile model cannot turn quoted/negative source into support.
                    _, attributable = contextual_role(document.text, e.source_start, e.source_end)
                    link = link_evidence(document.text, reqs[oid], e.source_evidence_ids)
                    context = context_gate(link, SimpleNamespace(assertion_mode='asserted', obligation_id=oid))
                    if not attributable or not context['valid'] or link['unassigned_item']:
                        raise ValueError('source_context_rejected')
                    owner = [k for k, (a, b) in document.ranges.items() if a <= e.source_start < e.source_end <= b]
                    if route != 'SEMANTIC' and owner != [REGISTRY[oid].rubric_item]:
                        raise ValueError('mathematical_projection_requires_same_item')
                    row.update(accepted=True, effective_route=route, context_valid=True,
                               reason='compatible_candidate_pending_verification', item_linkage=link)
                except ValueError as error:
                    row['reason'] = str(error)
                mapped.append(row)
        return mapped
