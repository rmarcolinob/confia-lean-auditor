"""Replayable projection into the frozen P2 checkers, with exact provenance."""
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.student_claims.tme2_p2_digital import collect_tme2_p2_text
from confia_lean_auditor.claims.common.schemas import SourceBinding,Provenance,Origin
from confia_lean_auditor.student_claims.generic_math import contextual_role
from confia_lean_auditor.experimental.tme_p2_checker_first.engine import StrongP2Checks,arithmetic_status
from confia_lean_auditor.rubric.pauta.tme2_p2 import bridge_tme2_p2
from confia_lean_auditor.rubric.pauta.bridge import _validated_status
from .mapper import representation
from .registry import REGISTRY,PROBLEM_ID,route_for_expression
from . import VERSION

POSITIVE={'FORMAL_VERIFIED','DETERMINISTIC_VERIFIED','COMPOSITE_VERIFIED'}

class ClaimProjection:
    def __init__(self,document,evidence,mapping):
        self.document=document
        selected={m['evidence_id'] for m in mapping if m['accepted']}
        self.evidence=[e for e in evidence if e.evidence_id in selected]
        self.bindings,self.events={},[]

    def __call__(self,problem,source,ranges,deterministic,*,observe=True):
        if problem!=PROBLEM_ID: raise ValueError('wrong_projection_problem')
        records,bindings,events={},{},[]
        for e in self.evidence:
            owner=next(k for k,(a,b) in self.document.ranges.items() if a<=e.source_start<e.source_end<=b)
            a=ranges[owner][0]+e.source_start-self.document.ranges[owner][0];b=a+len(e.source_span)
            if source[a:b]!=e.source_span: raise ValueError('projection_coordinate_changed')
            template=representation(e);role,attributed=contextual_role(source,a,b)
            rid='semantic-p2:'+legacy.sha(dict(source=legacy.sha(source),evidence=e.evidence_id))[:24]
            record=template.model_copy(update=dict(record_id=rid,rubric_links=(owner,),semantic_role=role,
                source=SourceBinding(raw_text=e.source_span,source_start=a,source_end=b,source_sha256=legacy.sha(source),grounding_status='grounded',attributable=attributed),
                provenance=Provenance(origin=Origin.STUDENT_EXPLICIT if attributed else Origin.STUDENT_CANDIDATE,channel='native',extraction_method=VERSION)))
            records[rid]=record;bindings[rid]=[e.evidence_id]
            events.append(dict(evidence_id=e.evidence_id,record_id=rid,source_start=e.source_start,source_end=e.source_end,
                projected_start=a,projected_end=b,source_span=e.source_span,normalized_claim=e.normalized_claim,subject=e.subject))
        if observe:self.bindings,self.events=bindings,events
        return tuple(records.values()),None


def verify(document,evidence,mapping,config,case_id,*,use_lean):
    projection=ClaimProjection(document,evidence,mapping)
    with legacy.supplement_scope(projection):
        digital=collect_tme2_p2_text(document.items)
        if collect_tme2_p2_text(document.items)!=digital: raise ValueError('projection_not_replayable')
        checks=StrongP2Checks(digital,case_id,use_lean,'p2-semantic-formal')
        checks.a();checks.b();checks.c()
        bundle=checks.finish()
    bridge=bridge_tme2_p2(config,bundle)
    records={r.record_id:r for r in bundle.records}
    candidates={(m['evidence_id'],m['obligation_id']) for m in mapping if m['accepted']}
    results=[]
    for fact in bundle.facts:
        oid=fact.fact_id;spec=REGISTRY[oid]
        ids=list(dict.fromkeys(i for rid in fact.source_claim_ids for i in projection.bindings.get(rid,())))
        if not any((eid,oid) in candidates for eid in ids): continue
        validated,reason=_validated_status(fact,[records[r] for r in fact.source_claim_ids],bundle.source_sha256)
        state=fact.verification.status;components=fact.metadata.get('components',[])
        attempted=False;check=fact.student_check
        expression=records[fact.source_claim_ids[0]].canonical_form.value.get('expression','')
        route=route_for_expression(oid,expression)
        if route=='FORMAL':
            status,attempted=arithmetic_status(state,check)
            if not check: status='FORMAL_NOT_ATTEMPTED'
            if validated not in {'supported','refuted','technical_error'}:
                status='FORMAL_UNPROVED' if attempted else 'FORMAL_NOT_ATTEMPTED'
        elif route=='COMPOSITE':
            status={'supported':'COMPOSITE_VERIFIED','refuted':'COMPOSITE_FAILED'}.get(validated,'COMPOSITE_INCOMPLETE')
            arithmetic=next((c for c in components if c['name']=='arithmetic'),{})
            attempted=arithmetic.get('formal_attempted',False);check=arithmetic.get('checker_result')
        else:
            status='DETERMINISTIC_VERIFIED' if validated=='supported' else 'DETERMINISTIC_FAILED'
        sufficient=status in POSITIVE and validated=='supported'
        results.append(dict(obligation_id=oid,evidence_ids=ids,source_claim_ids=list(fact.source_claim_ids),
            route=route,status=status,formal_attempted=attempted,reason=reason,
            mathematical_refutation=validated=='refuted',technical_uncertainty=state=='technical_error',
            checker_result=check,subchecks=components,checker_metadata=fact.metadata,
            verification_id=fact.verification.verification_id,verification_ref=fact.verification.artifact_ref,
            sufficiency_decision=dict(sufficient=sufficient,policy=spec.sufficiency_policy,basis='frozen_P2_checker_and_validated_binding'),
            original_fact=fact.model_dump(mode='json')))
        if oid=='c.total':
            results[-1].update(formal_status=status if route=='FORMAL' else 'FORMAL_NOT_ATTEMPTED',
                verification_kind='written_total_value' if route=='DETERMINISTIC' else 'written_total_equality')
    for m in mapping:
        if not m['accepted']:
            status='CONFLICTING_EVIDENCE' if m['reason']=='conflicting_extractor_interpretation' else 'CONTEXT_REJECTED'
        elif any(r['obligation_id']==m['obligation_id'] and m['evidence_id'] in r['evidence_ids'] for r in results):continue
        else: status={'FORMAL':'FORMAL_NOT_ATTEMPTED','COMPOSITE':'COMPOSITE_INCOMPLETE','DETERMINISTIC':'DETERMINISTIC_FAILED'}[m['effective_route']]
        results.append(dict(obligation_id=m['obligation_id'],evidence_ids=[m['evidence_id']],source_claim_ids=[],
            route=m['effective_route'],status=status,reason=m['reason'] if not m['accepted'] else 'no_checker_fact',
            formal_attempted=False,technical_uncertainty=False,mathematical_refutation=False,checker_result=None,subchecks=[],
            sufficiency_decision=dict(sufficient=False,basis='no_eligible_checker_result')))
    return bridge,results,projection.events
