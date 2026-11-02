"""Opt-in global semantic assessment, selective audit, explicit reconciliation.

The reconciler never computes points. Semantic support is not a FactResult and
is never passed off as deterministic/Lean verification. Existing checkers keep
all their grounding, representation and carry-forward contracts.
"""
from dataclasses import dataclass
import json
import re

from confia_lean_auditor.student_claims import hybrid_semantic as sem
from confia_lean_auditor.student_claims import evidence_id_semantic as projection
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.student_claims.obligation_catalog import mathematical_obligations, internal_id
from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.rubric.pauta.models import ObligationEvidence, PautaEvidence
from confia_lean_auditor.rubric.pauta.engine import PautaEngine
from confia_lean_auditor.rubric.pauta.evidence_policy import HybridEvidencePolicy
from .obligation_experiment import primary_audit, verify_without_scoring

POLICY = HybridEvidencePolicy()
# Mathematical reuse allowed by the task/dependencies, not free item reassignment.
DEPENDENCIES = {
 'TME2_P1_PILOT': {'c': {'b'}, 'd': {'b','c'}},
 'TME2026P2': {'b': {'a'}, 'c': {'a','b'}},
 'TME2026P3': {'b': {'a'}, 'c': {'a','b'}},
 'TME2026P4': {'b': {'a'}, 'c': {'a','b'}},
 'TME2026P5': {'a': {'b','c'}, 'c': {'a','b'}, 'd': {'b','c'}},
}


def context_check(problem, text, judgment, units):
    selected = [units[i] for i in judgment.evidence_ids if i in units]
    result = dict(valid=False, reason='no_evidence', cross_item=False, source_items=[], target_item=judgment.obligation_id.split('.')[0])
    if not selected or len(selected) != len(judgment.evidence_ids):
        return result
    regions = sem.item_regions(text)
    hints = {item for u in selected for item in sem.unit_hints(u, regions)}
    target = result['target_item']; foreign = hints - {target}
    result.update(source_items=sorted(hints), cross_item=bool(foreign))
    allowed = DEPENDENCIES.get(problem, {}).get(target, set())
    if foreign and (not foreign <= allowed or target not in hints):
        return dict(result, reason='cross_item_without_target_or_dependency')
    # Look at complete relevant item regions, including unselected corrections.
    relevant = [r for r in regions if r['item'] in (hints or {target})]
    context = '\n'.join(text[r['start']:r['end']] for r in relevant) if relevant else text
    if judgment.assertion_mode != 'asserted':
        return dict(result, reason='nonasserted_context')
    key = judgment.obligation_id.split('.',1)[1]
    stub = type('Selection', (), {'mathematical_payload':type('Payload', (), {'subject':key})()})()
    restriction = projection.context_restriction(context, stub)
    if restriction:
        return dict(result, reason=restriction)
    normalized = legacy.normalized(context)
    if re.search(r'na pagina\s+\d|ignore.*instru|desconsidere.*instru|porque sim|sem justific|raciocinio (?:esta )?errado', normalized):
        return dict(result, reason='unsupported_or_instruction_context')
    selected_text = legacy.normalized('\n'.join(u.exact_text for u in selected))
    description = next(o['mathematical_requirement'] for o in sem.catalog(problem) if o['obligation_id']==judgment.obligation_id)
    proof_needed = (bool(re.search(r'justifica|desenvolve|calcula|metodo alternativo|argumento', legacy.normalized(description)))
        or key in {'structural_max','enumeration','general_complete','general_rule','no_ones','no_ge5','uniqueness','increase','comparison','sizes','total_win_probability','perimeter_apqr','shaded_sum','factorization','difference_domain','total_thirty'})
    if proof_needed:
        # Necessary, not sufficient: mathematical soundness is the global judge's
        # job, augmented by applicable audits. A number/method name alone is not proof.
        reasoning = re.search(r'porque|pois|como\b|logo|portanto|entao|assim|substit|retir|troc|junt|aument|dimin|cada|caso|ramo|pares|distribu|escolh|dobro|soma|produto|[=<>≤≥]|\d\s*[*×+−-]', selected_text)
        bare_method = bool(re.fullmatch(r'(?:\(?[a-d]\)?[).:]?\s*)?(?:e |apqr e |apqr: )?(?:um )?paralelogramo[.\s]*', selected_text))
        if not reasoning or bare_method or re.fullmatch(r'[\W\d]*', selected_text):
            return dict(result, reason='justification_missing')
    if key not in {'apqr','triangle_pbq','triangle_rqc'} and 'paralelogram' in selected_text and not re.search(r'\d|[=]|dobro|lados', selected_text):
        return dict(result, reason='method_name_without_consequences')
    return dict(result, valid=True, reason='declared_dependency_with_target' if foreign else 'same_item_or_global_unlabelled')


def selective_audit(problem, items, text, judgments, solution_id, primary, *, use_lean=True):
    targets = mathematical_obligations(problem)
    allowed = {t['obligation_id']:{r['subject']:r['kind'] for r in t['representations']} for t in targets}
    selections, skipped = [], []
    for j in judgments:
        for statement in j.extracted_mathematical_statements:
            if (allowed[j.obligation_id].get(statement.subject) != statement.representation_kind
                    or statement.representation_kind == 'qualitative' or len(statement.evidence_ids)>12):
                skipped.append(dict(obligation_id=j.obligation_id, reason='not_automatically_representable'))
                continue
            selections.append(projection.ObligationEvidenceSelection(obligation_id=j.obligation_id,
                evidence_present=True, evidence_ids=statement.evidence_ids,
                assertion_mode=j.assertion_mode if j.assertion_mode != 'mixed' else 'uncertain',
                mathematical_payload=projection.previous.MathematicalPayload(subject=statement.subject, expression=statement.expression),
                representation_kind=statement.representation_kind, reason_code='literal_evidence'))
    if not selections:
        return primary, dict(selections=[], events=[], skipped=skipped)
    session = projection.EvidenceProjectionSession(problem,text,targets,selections,dict(status='global_judgment_extractions',api_calls=0))
    with legacy.supplement_scope(session):
        bridge = verify_without_scoring(problem,items,solution_id,use_lean=use_lean)
    return bridge, dict(session.telemetry, skipped=skipped)


def tier_for(evidence):
    formal = evidence.verification_source in {'student_lean','reference_lean'} or evidence.origin == 'student_lean'
    if evidence.status == 'supported': return 'FORMAL_VERIFIED' if formal else 'DETERMINISTIC_VERIFIED'
    if evidence.status == 'refuted': return 'FORMAL_REFUTED' if formal else 'DETERMINISTIC_REFUTED'
    return 'TECHNICAL_ERROR' if evidence.status == 'technical_error' else 'INDETERMINATE'


def audit_trace(bridge, identifier, selected_texts):
    evidence = next((e for e in bridge.evidence.obligations if e.obligation_id==identifier),None)
    if evidence is None: return None
    facts = [f for f in bridge.auditor.facts if f.fact_id == evidence.metadata.get('fact_id') or set(f.source_claim_ids)&set(evidence.source_claim_ids)]
    record_ids = set(evidence.source_claim_ids) | {i for f in facts for i in f.source_claim_ids}
    records = [r for r in bridge.auditor.records if r.record_id in record_ids]
    same = any(legacy.normalized(r.source.raw_text) in legacy.normalized(t) or legacy.normalized(t) in legacy.normalized(r.source.raw_text)
               for r in records for t in selected_texts if t.strip() and r.source.raw_text.strip())
    return dict(evidence=evidence.model_dump(mode='json'), facts=[f.model_dump(mode='json') for f in facts],
                records=[r.model_dump(mode='json') for r in records], same_selected_claim=same)


class EvidenceReconciler:
    def reconcile(self, problem, text, judgments, primary, audited, *, provider_ok=True):
        problem = internal_id(problem)
        units = {u.evidence_id:u for u in evidence_units(text)}
        semantic = {j.obligation_id:j for j in judgments}
        old = {e.obligation_id:e for e in primary.evidence.obligations}
        new = {e.obligation_id:e for e in audited.evidence.obligations}
        result, trace = [], []
        for obligation in sem.config_for(problem).obligations:
            oid = obligation.id; j = semantic.get(oid)
            bindings = [units[i].model_dump(mode='json') for i in (j.evidence_ids if j else []) if i in units]
            selected_texts = [b['exact_text'] for b in bindings]
            context = context_check(problem,text,j,units) if j else dict(valid=False,reason='provider_unavailable')
            base, extra = old.get(oid), new.get(oid)
            # Settled existing mathematical evidence cannot be erased by a model.
            settled = lambda e: e is not None and e.status in {'supported','refuted'} and e.attributable_to_student
            chosen = base if settled(base) else extra
            conflict = False; reason = 'semantic_absent'; tier = 'INDETERMINATE'
            if settled(chosen):
                tier = tier_for(chosen); reason = 'audited_evidence_precedence'
                conflict = bool(j and ((chosen.status=='refuted' and j.semantic_judgment=='satisfied') or
                    (chosen.status=='supported' and j.semantic_judgment=='contradicted')))
                if settled(base) and settled(extra) and base.status != extra.status:
                    conflict = True
                e = chosen
                if conflict:
                    tier = 'CONFLICT'
                    e = e.model_copy(update={'metadata':dict(e.metadata, conflict=True, audit_tier=tier_for(chosen))})
            elif chosen is not None and chosen.status == 'technical_error':
                e = chosen; tier = 'TECHNICAL_ERROR'; reason = 'audit_technical_failure_not_refutation'
            elif j and j.semantic_judgment=='satisfied' and context['valid'] and not oid.split('.')[1].startswith('cf_'):
                tier = 'SEMANTIC_SUPPORTED'; reason = 'global_semantic_judgment_grounded_no_audit_contradiction'
                e = ObligationEvidence(obligation_id=oid,status='supported',origin='semantic',
                    evidence_refs=tuple(j.evidence_ids),attributable_to_student=True,
                    source_claim_ids=(f'hybrid:{oid}',),verification_source='semantic',grounding_status='grounded',
                    metadata=dict(reconciliation_policy=POLICY.version, evidence_tier=tier, confidence=j.confidence,
                                  context_valid=True, conflict=False, method_path=j.method_path))
            else:
                tier = ('TECHNICAL_ERROR' if not provider_ok else 'SEMANTIC_NOT_SUPPORTED'
                        if j and j.semantic_judgment in {'not_satisfied','contradicted'} else 'INDETERMINATE')
                reason = ('carry_forward_requires_existing_bound_audit' if '.cf_' in oid else context['reason'])
                e = ObligationEvidence(obligation_id=oid,status='technical_error' if not provider_ok else 'indeterminate',
                    origin='semantic',verification_source='semantic',evidence_refs=tuple(j.evidence_ids) if j else (),
                    metadata=dict(evidence_tier=tier, reason=reason))
            # Revalidate model_copy changes, including preserved conditional bindings.
            e = ObligationEvidence.model_validate(e.model_dump())
            result.append(e)
            review = e.status in {'indeterminate','technical_error'} or conflict or (tier=='SEMANTIC_SUPPORTED' and j.confidence!='high')
            primary_trace = audit_trace(primary,oid,selected_texts)
            selective_trace = audit_trace(audited,oid,selected_texts)
            trace.append(dict(obligation_id=oid, semantic_judgment=j.model_dump(mode='json') if j else None,
                evidence_ids=j.evidence_ids if j else [], evidence_bindings=bindings, context=context,
                primary_audit=primary_trace, selective_audit=selective_trace,
                conflict_scope=('same_selected_claim' if any(t and t['same_selected_claim'] for t in (primary_trace,selective_trace))
                                else 'obligation_level_disagreement') if conflict else None,
                evidence_tier=tier, audit_tier=tier_for(chosen) if chosen else None,
                conflict=conflict, decision=e.status, needs_review=review, reason=reason,
                reconciled_evidence=e.model_dump(mode='json')))
        return PautaEvidence(problem_id=problem,solution_id=primary.evidence.solution_id,obligations=tuple(result)), trace


@dataclass(frozen=True)
class HybridShadow:
    primary_bridge: object
    baseline_assessment: object
    audit_bridge: object
    reconciled_evidence: PautaEvidence
    potential_assessment: object
    audit_only_assessment: object
    reconciliation: list
    audit_telemetry: dict
    judgments: tuple
    provider: dict
    hybrid_shadow: bool = True

    @property
    def semantic_only_points(self):
        # Counterfactual through the SAME engine: includes dependency effects.
        return self.potential_assessment.known_points-self.audit_only_assessment.known_points


def run_hybrid_shadow(problem, items, text, *, solution_id, primary=None, provider=None, use_lean=True):
    problem = internal_id(problem)
    primary_bridge, baseline = primary or primary_audit(problem,items,solution_id=solution_id,use_lean=use_lean)
    judgments, metadata = (provider or sem.request_judgments)(problem,text)
    if metadata['status']=='completed':
        judgments = sem.validate_response(json.dumps({'judgments':[j.model_dump() for j in judgments]}),problem,text)
    elif judgments:
        raise ValueError('failed_provider_cannot_supply_judgments')
    audited, telemetry = selective_audit(problem,items,text,judgments,solution_id,primary_bridge,use_lean=use_lean)
    evidence, trace = EvidenceReconciler().reconcile(problem,text,judgments,primary_bridge,audited,provider_ok=metadata['status']=='completed')
    config = sem.config_for(problem)
    potential = PautaEngine().evaluate(config,evidence,evidence_policy=POLICY)
    audit_only = evidence.model_copy(update={'obligations':tuple(e for e in evidence.obligations if e.origin!='semantic')})
    audit_assessment = PautaEngine().evaluate(config,audit_only,evidence_policy=POLICY)
    return HybridShadow(primary_bridge,baseline,audited,evidence,potential,audit_assessment,trace,telemetry,tuple(judgments),metadata)


def activate_hybrid(shadow, *, gate_passed=False):
    if gate_passed is not True:
        raise ValueError('Active DEV requires passed frozen shadow gate')
    return PautaEngine().evaluate(sem.config_for(shadow.reconciled_evidence.problem_id),shadow.reconciled_evidence,evidence_policy=POLICY)
