"""Source fidelity and pedagogical binding. No machine, answers, or score access."""
import re
from confia_lean_auditor.student_claims.semantic import sha, notation_view
from .registry import REGISTRY

VERSION = 'p3-semantic-contracts-v1'
FIDELITIES = ('EXACT','SUPPORTED_NORMALIZATION','PARTIAL','AMBIGUOUS','UNSUPPORTED')
BINDINGS = ('EXACT_BINDING','VALID_EQUIVALENT_BINDING','PARTIAL_BINDING','AMBIGUOUS_BINDING','INVALID_BINDING')
SAFE_FIDELITY = frozenset(FIDELITIES[:2])
SAFE_BINDING = frozenset(BINDINGS[:2])


def receipt(document, e):
    from .mapper import representation, source_view
    from .source_adapter import member_atom
    source_ok = (document.text[e.source_start:e.source_end] == e.source_span
                 and e.metadata.get('source_sha256') == sha(document.text))
    a,b = e.metadata.get('assertion_range',(e.source_start,e.source_end))
    assertion = document.text[a:b]
    atom = None; reason = 'source_binding_changed'; fidelity = 'UNSUPPORTED'
    try:
        if not source_ok or not e.source_start <= a < b <= e.source_end:
            raise ValueError(reason)
        if re.search(r'\b(?:nao|nunca|jamais)\b',source_view(e.source_span)):
            raise ValueError('negated_proposition_requires_explicit_representation')
        member = member_atom(e)
        if member:
            atom = member
            fidelity = 'EXACT'; reason = 'literal_membership_not_exhaustive_set'
        else:
            # The submitted expression must be present in the assertion, not
            # merely elsewhere in an expanded sentence/envelope.
            if notation_view(e.normalized_claim) not in notation_view(source_view(assertion)):
                if e.claim_type not in {'integer_set','enum'}:
                    raise ValueError('payload_not_in_assertion')
            parsed = representation(e, document)
            atom = dict(property=e.subject,kind=e.claim_type,
                        value=parsed.canonical_form.value)
            fidelity = ('EXACT' if e.normalized_claim in assertion else 'SUPPORTED_NORMALIZATION')
            reason = 'source_checked_payload'
    except ValueError as error:
        reason = str(error)
        if 'uniquely' in reason or 'mixed_' in reason: fidelity = 'AMBIGUOUS'
        elif 'truncated' in reason or 'omits' in reason or reason.startswith('partial_'): fidelity = 'PARTIAL'
    r = dict(version=VERSION,claim_id=e.evidence_id,source_sha256=sha(document.text),
        source_ranges=[[e.source_start,e.source_end]],assertion_range=[a,b],
        source_span=e.source_span,asserted_content=assertion,
        relation_support=e.metadata.get('membership_relation_support'),
        original_payload=e.metadata.get('original_payload',e.normalized_claim),
        normalized_payload=e.normalized_claim,proposition=atom,
        proposition_digest=sha(atom),representation_fidelity=fidelity,
        completeness_for_assertion=fidelity in SAFE_FIDELITY,
        covered_ranges=[[a,b]] if fidelity in SAFE_FIDELITY else [],
        uncovered_ranges=[] if fidelity in SAFE_FIDELITY else [[a,b]],
        normalization_steps=[] if fidelity=='EXACT' else [dict(rule=reason,source_range=[a,b])],
        reason=reason)
    r['receipt_id']='representation:'+sha(r)
    return r


def bindings(document, e, representation_receipt):
    """Suggestion selects candidates only; source validation supplies authority."""
    rows=[]; r=representation_receipt; atom=r['proposition'] or {}
    for oid in e.obligation_candidates:
        spec=REGISTRY.get(oid)
        item=bool(spec and e.item_id==spec.rubric_item and
                  document.ranges.get(e.item_id,(0,0))[0]<=e.source_start<e.source_end<=document.ranges.get(e.item_id,(0,0))[1])
        subject=bool(spec and atom.get('property') in spec.subjects)
        valid=item and subject and r['representation_fidelity'] in SAFE_FIDELITY
        status=('EXACT_BINDING' if valid else 'INVALID_BINDING' if not item or (atom and not subject)
                else 'AMBIGUOUS_BINDING' if r['representation_fidelity']=='AMBIGUOUS' else 'PARTIAL_BINDING')
        relation=('membership_counterevidence' if atom.get('kind')=='member' else
                  'complete_set' if atom.get('kind')=='integer_set' else 'written_result_or_premise')
        row=dict(version=VERSION,claim_id=e.evidence_id,obligation_id=oid,
            item_compatibility=item,subject_compatibility=subject,
            case_condition_compatibility=subject,semantic_relation=relation,
            representation_fidelity=r['representation_fidelity'],representation_receipt_ref=r['receipt_id'],
            binding_confidence_diagnostic=e.confidence,binding_status=status,
            source_sha256=r['source_sha256'],source_ranges=r['source_ranges'],
            diagnostics=[r['reason']],validator='source_representation_and_registry')
        # Confidence is diagnostic, never part of authority/revision identity.
        row['receipt_id']='binding:'+sha({k:v for k,v in row.items() if k!='binding_confidence_diagnostic'})
        rows.append(row)
    return rows


def checker_input(snapshot, result):
    """Close the input chain before any mathematical receipt gains authority."""
    ids=result.get('evidence_ids') or [result.get('evidence_id')]
    premises=[]
    for eid in ids:
        d=snapshot.get(eid)
        if not d: continue
        r=d.representation_receipt
        premises.append(dict(evidence_id=eid,proposition_digest=r.get('proposition_digest'),
            representation_receipt_ref=r.get('receipt_id'),
            binding_refs=[b['receipt_id'] for b in d.binding_receipts],
            segment_ref=d.segment.get('segment_id')))
    r=dict(version=VERSION,source_sha256=snapshot.source_sha256,ledger_revision=snapshot.ledger_revision,
           obligation_id=result['obligation_id'],premises=premises)
    r['input_digest']=sha(r)
    return r


def annotate_result(snapshot, result):
    result['checker_input_receipt']=checker_input(snapshot,result)
    return result
