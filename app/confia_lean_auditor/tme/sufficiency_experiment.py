"""DEV-only sufficiency route; unchanged auditor, reconciler precedence and scorer.

Existing frozen audit results are reusable mathematical evidence. No semantic
judgment bypasses sufficiency merely because projection failed to build a fact.
"""
from dataclasses import dataclass
from confia_lean_auditor.student_claims.semantic_sufficiency import SemanticSufficiencyGate,SufficiencyDecision,VERSION
from confia_lean_auditor.student_claims.sufficiency_requirements import requirements
from confia_lean_auditor.student_claims.hybrid_semantic import config_for
from confia_lean_auditor.student_claims.semantic import sha
from confia_lean_auditor.rubric.pauta.models import ObligationEvidence,PautaEvidence
from confia_lean_auditor.rubric.pauta.engine import PautaEngine
from .hybrid_grader import EvidenceReconciler,POLICY


@dataclass(frozen=True)
class SufficiencyShadow:
    evidence:PautaEvidence
    reconciliation:list
    decisions:tuple
    linkage:list
    potential_assessment:object
    audit_only_assessment:object
    provider:dict

    @property
    def semantic_only_points(self):
        return self.potential_assessment.known_points-self.audit_only_assessment.known_points


def reconcile_sufficiency(problem,text,judgments,primary,audited,decisions,links,*,first_provider_ok=True):
    # With no semantic input, the old reconciler supplies only its established
    # formal/deterministic precedence. Its old item parser cannot promote here.
    base,base_trace=EvidenceReconciler().reconcile(problem,text,(),primary,audited)
    js={j.obligation_id:j for j in judgments};ds={d.obligation_id:d for d in decisions}
    ls={l['obligation_id']:l for l in links};reqs={r['obligation_id']:r for r in requirements(problem)}
    evidence=[];trace=[]
    for audit,t in zip(base.obligations,base_trace):
        oid=audit.obligation_id;j=js.get(oid);d=ds.get(oid);link=ls.get(oid)
        conflict=False;reason='no_positive_candidate';tier=t['evidence_tier'];e=audit
        if audit.status in {'supported','refuted'}:
            # Neither sufficiency nor model confidence can erase a settled audit.
            conflict=bool((audit.status=='refuted' and j and j.semantic_judgment=='satisfied') or
                          (audit.status=='supported' and d and d.sufficiency=='contradictory'))
            if conflict:
                tier='CONFLICT';e=audit.model_copy(update={'metadata':dict(audit.metadata,conflict=True,audit_tier=t['evidence_tier'])})
            reason='existing_mathematical_evidence_precedence'
        elif audit.status=='technical_error':reason='audit_technical_failure'
        elif not first_provider_ok:
            tier='TECHNICAL_ERROR';reason='first_evaluator_invalid'
            e=ObligationEvidence(obligation_id=oid,status='technical_error',origin='semantic',verification_source='semantic')
        elif j and j.semantic_judgment=='satisfied':
            valid_link=bool(link and link['linkage']['valid'] and link['context']['valid'])
            if d and d.sufficiency=='sufficient' and valid_link and '.cf_' not in oid:
                tier='SEMANTIC_SUPPORTED';reason='independent_sufficiency_and_context_passed'
                # Unknown item boundaries cannot silently carry high confidence.
                confidence='medium' if link['linkage']['unassigned_item'] else j.confidence
                e=ObligationEvidence(obligation_id=oid,status='supported',origin='semantic',verification_source='semantic',
                    evidence_refs=tuple(d.evidence_ids),attributable_to_student=True,grounding_status='grounded',
                    source_claim_ids=(f'sufficiency:{oid}',),metadata=dict(reconciliation_policy=POLICY.version,
                        evidence_tier=tier,confidence=confidence,evaluator_confidence=j.confidence,
                        context_valid=True,conflict=False,sufficiency_version=VERSION,
                        sufficiency_decision=d.model_dump(mode='json'),evidence_requirement=reqs[oid]['evidence_requirement'],
                        item_linkage=link['linkage'],source_sha256=sha(text)))
            else:
                technical=d is None or d.reason_code=='provider_error'
                conflict=bool(d and d.sufficiency=='contradictory')
                tier='TECHNICAL_ERROR' if technical else 'CONFLICT' if conflict else 'SEMANTIC_NOT_SUPPORTED' if d and d.sufficiency=='insufficient' else 'INDETERMINATE'
                reason='carry_forward_requires_existing_bound_audit' if '.cf_' in oid else d.reason_code if d else 'missing_gate_decision'
                e=ObligationEvidence(obligation_id=oid,status='technical_error' if technical else 'indeterminate',
                    origin='semantic',verification_source='semantic',evidence_refs=tuple(j.evidence_ids),
                    metadata=dict(evidence_tier=tier,conflict=conflict,reason=reason))
        else:
            tier='SEMANTIC_NOT_SUPPORTED' if j and j.semantic_judgment in {'not_satisfied','contradicted'} else 'INDETERMINATE'
            e=ObligationEvidence(obligation_id=oid,status='indeterminate',origin='semantic',verification_source='semantic',
                evidence_refs=tuple(j.evidence_ids) if j else (),metadata=dict(evidence_tier=tier,reason=reason))
        e=ObligationEvidence.model_validate(e.model_dump());evidence.append(e)
        trace.append(dict(obligation_id=oid,evidence_requirement=reqs[oid]['evidence_requirement'],
            semantic_judgment=j.model_dump(mode='json') if j else None,
            sufficiency=d.model_dump(mode='json') if d else None,item_linkage=link,
            primary_audit=t['primary_audit'],selective_audit=t['selective_audit'],
            evidence_tier=tier,decision=e.status,conflict=conflict,reason=reason,
            reconciled_evidence=e.model_dump(mode='json')))
    return PautaEvidence(problem_id=base.problem_id,solution_id=base.solution_id,obligations=tuple(evidence)),trace


def run_sufficiency_shadow(problem,text,judgments,primary,audited,*,provider=None,first_provider_ok=True):
    gate=SemanticSufficiencyGate();payload,local,links=gate.prepare(problem,text,judgments)
    remote,meta=gate.evaluate(payload,provider=provider)
    if meta['status']=='completed':
        from confia_lean_auditor.student_claims.semantic_sufficiency import validate_response
        import json
        remote=validate_response(json.dumps({'decisions':{d.obligation_id:d.model_dump() for d in remote}}),payload)
    elif remote:raise ValueError('failed_gate_cannot_supply_decisions')
    if payload['obligations'] and meta['status']!='completed':
        remote=tuple(SufficiencyDecision(obligation_id=o['obligation_id'],sufficiency='uncertain',evidence_ids=[],
            reason_code='provider_error',concise_rationale='Sufficiency provider unavailable or invalid; not a mathematical refutation.') for o in payload['obligations'])
    decisions=tuple(local)+tuple(remote)
    evidence,trace=reconcile_sufficiency(problem,text,judgments,primary,audited,decisions,links,first_provider_ok=first_provider_ok)
    config=config_for(problem);potential=PautaEngine().evaluate(config,evidence,evidence_policy=POLICY)
    audited_only=evidence.model_copy(update={'obligations':tuple(e for e in evidence.obligations if e.origin!='semantic')})
    audit_assessment=PautaEngine().evaluate(config,audited_only,evidence_policy=POLICY)
    return SufficiencyShadow(evidence,trace,decisions,links,potential,audit_assessment,meta)
