"""Source-admitted membership evidence; the finite query has no score authority."""
import re
from confia_lean_auditor.student_claims.semantic import sha
from confia_lean_auditor.experimental.tme_p3_checker_first.components import finite_certificate
from confia_lean_auditor.tme.p3_machine import load_machine
from confia_lean_auditor.tme.registry import ROOT
from .mapper import ORDINALS

OBLIGATION='b.same_compartment'
SUBJECT='repeticao_branca'


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
    """Only source-certified inclusion atoms enter the unchanged finite query."""
    from .semantic_contracts import SAFE_FIDELITY, SAFE_BINDING
    rejected={(m['evidence_id'],m['obligation_id']):m['reason'] for m in mapping if not m['accepted']}
    results=[];machine=None
    for e in evidence:
        r=e.metadata.get('representation_receipt',{})
        atom=r.get('proposition') or {}
        bindings=e.metadata.get('binding_receipts',[])
        if (atom.get('kind')!='member' or atom.get('property')!=SUBJECT
                or r.get('representation_fidelity') not in SAFE_FIDELITY
                or not any(b['obligation_id']==OBLIGATION and b['binding_status'] in SAFE_BINDING for b in bindings)):
            continue
        if document.text[e.source_start:e.source_end]!=e.source_span:continue
        if machine is None:machine=load_machine(ROOT/'examples/pautas/tme2_problem3.machine.v1.json')
        for compartment in atom['members']:
            check=membership_result(compartment,machine)
            tokens=[str(compartment)]+[k for k,v in ORDINALS.items() if v==str(compartment)]
            literal=re.search(r'\b(?:'+'|'.join(tokens)+r')\b',e.source_span,re.I)
            token=literal[0] if literal else None
            token_start=e.source_start+literal.start() if literal else e.source_start
            results.append(dict(guard_id='p3-membership-guard:'+sha([e.evidence_id,atom])[:24],
                evidence_id=e.evidence_id,evidence_ids=[e.evidence_id],obligation_id=OBLIGATION,
                item_id=e.item_id,subject=SUBJECT,source_span=e.source_span,
                source_start=e.source_start,source_end=e.source_end,source_sha256=r['source_sha256'],
                atomic_claim=dict(kind='membership_claim',compartment=compartment,
                                  relation='same_compartment_second_white',literal_token=token,
                                  literal_start=token_start,literal_end=token_start+len(token or ''),
                                  representation_receipt_ref=r['receipt_id']),
                original_normalized_claim=e.normalized_claim,
                positive_mapping_rejection=rejected.get((e.evidence_id,OBLIGATION),'membership_is_not_positive_set'),
                route='DETERMINISTIC',guard_only=True,award_eligible=False,
                formal_status='FORMAL_NOT_ATTEMPTED',formal_attempted=False,
                sufficiency_decision=dict(sufficient=False,basis='guard_cannot_award'),**check))
    return results
