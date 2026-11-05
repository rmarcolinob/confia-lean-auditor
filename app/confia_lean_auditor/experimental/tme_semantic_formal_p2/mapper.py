"""Deterministic attribution, item, subject, representation and route validation."""
import re
from types import SimpleNamespace
from confia_lean_auditor.experimental.tme_semantic_formal.obligation_mapper import SourceDocument as P1Document
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.student_claims.named_math import extract_named_math
from confia_lean_auditor.student_claims.tme2_p2_digital import VOCABULARY
from confia_lean_auditor.student_claims.generic_math import contextual_role
from confia_lean_auditor.student_claims.sufficiency_context import link_evidence,context_gate
from confia_lean_auditor.student_claims.sufficiency_requirements import requirements
from .registry import PROBLEM_ID,REGISTRY,route_for_expression

class SourceDocument:
    @staticmethod
    def parse(text):
        document=P1Document.parse(text)
        if not set(document.items)<={'a','b','c'}: raise ValueError('P2_only_items_abc')
        return document

# These are source-role anchors, never expected numeric answers.
ANCHORS={
    'balance_relation':r'\bS\b.*\bx\b|\bx\b.*\bS\b',
    'integral_sum':r'\bS\b|\bsoma\b',
    'modular_condition':r'\bx\b',
    'centers':r'centr|centros|\bx\b',
    'admissible_center':r'centr|\bx\b',
    'center_sums':r'centr.*som|som.*centr',
    'realizable_1':r'centr\w*\s*(?:=|e|é)?\s*1\b',
    'realizable_5':r'centr\w*\s*(?:=|e|é)?\s*5\b',
    'realizable_9':r'centr\w*\s*(?:=|e|é)?\s*9\b',
}


def representation(e):
    """Reuse canonicalizers; never change their mathematics or complete a claim."""
    if e.subject not in VOCABULARY: raise ValueError('no_checker_for_qualitative_representation')
    if e.claim_type != VOCABULARY[e.subject]['kind']: raise ValueError('claim_type_subject_mismatch')
    if '\n' in e.normalized_claim: raise ValueError('multiline_payload_not_supported')
    parsed=extract_named_math(PROBLEM_ID,e.subject+': '+e.normalized_claim,VOCABULARY)
    if len(parsed)!=1: raise ValueError('unsupported_checker_payload')
    native=extract_named_math(PROBLEM_ID,e.source_span,VOCABULARY)
    if native:
        if not any(r.canonical_form.subject==e.subject and (
                legacy.notation_view(r.canonical_form.value['expression'])==legacy.notation_view(e.normalized_claim)
                or e.claim_type=='enum' and r.canonical_form.value.get('value')==parsed[0].canonical_form.value.get('value')) for r in native):
            raise ValueError('typed_source_payload_changed')
        return parsed[0]
    if e.subject=='placement': raise ValueError('positions_require_explicit_typed_mapping')
    candidate=legacy.SemanticClaimCandidate(candidate_id=e.evidence_id,claim_kind='named_relation',
        source_text=e.source_span,source_start=e.source_start,source_end=e.source_end,
        normalized_payload=legacy.NormalizedPayload(subject=e.subject,expression=e.normalized_claim,item_id='unknown'),assertion_mode='asserted')
    anchor=legacy.subject_binding(PROBLEM_ID,candidate)
    if not anchor and e.subject in ANCHORS:
        anchor=bool(re.search(ANCHORS[e.subject],e.source_span,re.I))
    if not anchor: raise ValueError('subject_not_bound_to_source')
    if not legacy.numeric_tokens(e.normalized_claim)<=legacy.numeric_tokens(e.source_span): raise ValueError('invented_numeric_payload')
    if not legacy.written_representation(PROBLEM_ID,candidate): raise ValueError('representation_not_written')
    if re.search(r'\b(?:pagina|exercicio|questao|ano|telefone|matricula|idade)\s*(?:numero|:)?\s*\d+',legacy.normalized(e.source_span)):
        raise ValueError('incidental_number_context')
    # A matching substring may still omit a wrong result or operator. Preserve
    # complete written arithmetic; do not normalize 4!=20 down to 4! or to 20.
    if e.claim_type in {'math','relation','combinatorial_math'}:
        raw=legacy.notation_view(e.source_span);expr=legacy.notation_view(e.normalized_claim)
        matches=list(re.finditer(re.escape(expr),raw))
        def whole(m):
            before=raw[:m.start()].rstrip('(');after=raw[m.end():].lstrip(')')
            left=before[-1:] if before else '';right=after[:1]
            left_ok=not left or left not in '=+-*/^!0123456789'
            if e.subject=='sum_formula' and left=='=' and re.search(r's=$',before,re.I): left_ok=True
            return left_ok and (not right or right not in '=+-*/^!0123456789')
        if matches and not any(whole(m) for m in matches): raise ValueError('truncated_written_arithmetic')
    return parsed[0]


class ObligationMapper:
    def map(self,document,evidence):
        reqs={r['obligation_id']:r for r in requirements(PROBLEM_ID)}
        contexts={}
        for e in evidence:
            for oid in e.obligation_candidates:
                contexts.setdefault((e.source_start,e.source_end,oid),set()).add((e.normalized_claim,e.subject,e.claim_type,e.assertion_status,e.polarity,e.scope,e.hypothetical,e.abandoned,e.attributed_to_student))
        rows=[]
        for e in evidence:
            for oid in e.obligation_candidates:
                spec=REGISTRY.get(oid)
                row=dict(evidence_id=e.evidence_id,obligation_id=oid,accepted=False,reason=None,
                    suggested_route=e.route_candidate,effective_route=spec.route if spec else None,
                    route_override_reason='obligation_registry' if spec and e.route_candidate!=spec.route else None,
                    context_valid=False)
                try:
                    if not spec: raise ValueError('unknown_obligation')
                    if document.text[e.source_start:e.source_end]!=e.source_span or e.metadata.get('source_sha256')!=legacy.sha(document.text):
                        raise ValueError('source_binding_changed')
                    if len(contexts[(e.source_start,e.source_end,oid)])>1: raise ValueError('conflicting_extractor_interpretation')
                    if not (e.assertion_status=='asserted' and e.polarity=='positive' and e.attributed_to_student
                            and not e.hypothetical and not e.abandoned and e.scope in {'main_argument','final_conclusion'}):
                        raise ValueError('nonasserted_or_unattributed_context')
                    owner=[k for k,(a,b) in document.ranges.items() if a<=e.source_start<e.source_end<=b]
                    if owner!=[spec.rubric_item]: raise ValueError('same_item_required')
                    link=link_evidence(document.text,reqs[oid],e.source_evidence_ids)
                    _,attributable=contextual_role(document.text,e.source_start,e.source_end)
                    gate=context_gate(link,SimpleNamespace(assertion_mode='asserted',obligation_id=oid))
                    if not attributable or not gate['valid'] or link['unassigned_item']: raise ValueError('source_context_rejected')
                    if e.subject not in spec.subjects or e.claim_type not in spec.claim_types: raise ValueError('obligation_subject_type_mismatch')
                    representation(e)
                    route=route_for_expression(oid,e.normalized_claim)
                    row.update(accepted=True,context_valid=True,reason='compatible_pending_checker',item_linkage=link,
                        effective_route=route,route_override_reason='obligation_registry' if e.route_candidate!=route else None)
                except ValueError as error: row['reason']=str(error)
                rows.append(row)
        return rows
