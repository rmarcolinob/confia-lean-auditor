"""Source-bound projection into frozen P3 mathematics; no semantic credit."""
from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.student_claims.tme2_p3_digital import collect_tme2_p3_digital
from confia_lean_auditor.claims.common.schemas import SourceBinding,Provenance,Origin,SemanticRole
from confia_lean_auditor.experimental.tme_p3_checker_first.engine import StrongP3Checks
from confia_lean_auditor.lean.student_claim_checkers.tme2_p3 import _a,_b,_c,assertions_in_item
from confia_lean_auditor.tme.p3_machine import load_machine
from confia_lean_auditor.tme.registry import ROOT
from confia_lean_auditor.rubric.pauta.tme2_p3 import bridge_tme2_p3
from confia_lean_auditor.rubric.pauta.bridge import _validated_status
from .mapper import representation
from .registry import REGISTRY,PROBLEM_ID,route_for_expression
from . import VERSION

POSITIVE={'FORMAL_VERIFIED','DETERMINISTIC_VERIFIED','COMPOSITE_VERIFIED'}

def formal_state(check,state):
    attempted=bool(check and check.get('lean_file') and check.get('lean_statement'))
    if not attempted: return 'FORMAL_NOT_ATTEMPTED',False
    if state=='technical_error': return 'FORMAL_ERROR',True
    if check.get('compiled'): return 'FORMAL_VERIFIED',True
    if check.get('refutation_verified'): return 'FORMAL_REFUTED',True
    return 'FORMAL_UNPROVED',True

class ClaimProjection:
    def __init__(self,document,evidence,mapping):
        self.document=document
        selected={m['evidence_id'] for m in mapping if m['accepted']}
        self.evidence=[e for e in evidence if e.evidence_id in selected]
        from .semantic_contracts import receipt
        for e in self.evidence:
            if e.metadata.get('representation_receipt')!=receipt(document,e):
                raise ValueError('representation_changed_before_checker')
        self.bindings,self.events={},[]

    def __call__(self,problem,source,ranges,deterministic,*,observe=True):
        if problem!=PROBLEM_ID: raise ValueError('wrong_projection_problem')
        records,bindings,events={},{},[]
        for e in self.evidence:
            owner=e.item_id
            a=ranges[owner][0]+e.source_start-self.document.ranges[owner][0];b=a+len(e.source_span)
            if source[a:b]!=e.source_span: raise ValueError('projection_coordinate_changed')
            template=representation(e,self.document)
            rid='semantic-p3:'+legacy.sha(dict(source=legacy.sha(source),evidence=e.evidence_id))[:24]
            record=template.model_copy(update=dict(record_id=rid,rubric_links=(owner,),semantic_role=SemanticRole.INTERMEDIATE,
                source=SourceBinding(raw_text=e.source_span,source_start=a,source_end=b,source_sha256=legacy.sha(source),grounding_status='grounded',attributable=True),
                provenance=Provenance(origin=Origin.STUDENT_EXPLICIT,channel='native',extraction_method=VERSION)))
            records[rid]=record;bindings[rid]=[e.evidence_id]
            events.append(dict(evidence_id=e.evidence_id,record_id=rid,source_start=e.source_start,source_end=e.source_end,
                projected_start=a,projected_end=b,source_span=e.source_span,normalized_claim=e.normalized_claim,
                subject=e.subject,normalized_payload=template.canonical_form.model_dump(mode='json'),
                representation_receipt_ref=e.metadata['representation_receipt']['receipt_id'],
                proposition_digest=e.metadata['representation_receipt']['proposition_digest'],
                segment_ref=e.metadata['discourse_segment']['segment_id']))
        if observe: self.bindings,self.events=bindings,events
        return tuple(records.values()),None

class IsolatedChecks(StrongP3Checks):
    """Contain a checker exception to its obligation, preserving other facts."""
    def _call(self,callback,oid,records,/,*args,**kw):
        count=len(self.pending)
        try: return callback(oid,*args,**kw)
        except Exception as error:
            del self.pending[count:]
            self.add(oid,records,'technical_error',metadata=dict(checker_exception=type(error).__name__,
                decision=dict(status='COMPOSITE_ERROR',state='technical_error',reason='checker_exception')))

    def observe(self,oid,records,status,**kw):
        return self._call(super().observe,oid,records,records,status,**kw)

    def numerical(self,oid,record,expected,**kw):
        return self._call(super().numerical,oid,[record],record,expected,**kw)

def verify(document,evidence,mapping,config,case_id,*,use_lean):
    projection=ClaimProjection(document,evidence,mapping)
    machine=load_machine(ROOT/'examples/pautas/tme2_problem3.machine.v1.json')
    with legacy.supplement_scope(projection):
        digital=collect_tme2_p3_digital(document.items)
        if collect_tme2_p3_digital(document.items)!=digital: raise ValueError('projection_not_replayable')
        checks=IsolatedChecks(digital,case_id,machine,use_lean,'p3-semantic-formal')
        for item,checker in zip('abc',(_a,_b,_c)):
            checker(checks,assertions_in_item(digital,item))
        bundle=checks.finish()
    bridge=bridge_tme2_p3(config,bundle)
    records={r.record_id:r for r in bundle.records}
    candidates={(m['evidence_id'],m['obligation_id']) for m in mapping if m['accepted']}
    results=[]
    for fact in bundle.facts:
        oid=fact.fact_id;spec=REGISTRY[oid]
        primary_ids=list(dict.fromkeys(i for rid in fact.source_claim_ids for i in projection.bindings.get(rid,())))
        if not any((eid,oid) in candidates for eid in primary_ids): continue
        dependencies=fact.metadata.get('context_claim_ids',[])
        ids=list(dict.fromkeys(primary_ids+[i for rid in dependencies for i in projection.bindings.get(rid,())]))
        validated,reason=_validated_status(fact,[records[r] for r in fact.source_claim_ids],bundle.source_sha256)
        state=fact.verification.status; components=fact.metadata.get('components',[])
        arithmetic=next((c for c in components if c['name']=='arithmetic'),{})
        check=arithmetic.get('checker_result') or fact.student_check
        formal,attempted=formal_state(check,state)
        if arithmetic: formal,attempted=arithmetic['formal_status'],arithmetic['formal_attempted']
        expression=records[fact.source_claim_ids[0]].canonical_form.value.get('expression','')
        route=route_for_expression(oid,expression)
        if route=='FORMAL': status=formal
        elif route=='COMPOSITE':
            status={'supported':'COMPOSITE_VERIFIED','refuted':'COMPOSITE_FAILED','technical_error':'COMPOSITE_ERROR'}.get(validated,'COMPOSITE_INCOMPLETE')
        else: status={'supported':'DETERMINISTIC_VERIFIED','refuted':'DETERMINISTIC_FAILED','technical_error':'DETERMINISTIC_ERROR'}.get(validated,'DETERMINISTIC_INCOMPLETE')
        sufficient=status in POSITIVE and validated=='supported'
        results.append(dict(obligation_id=oid,evidence_ids=ids,primary_evidence_ids=primary_ids,
            source_claim_ids=list(fact.source_claim_ids),route=route,status=status,state=state,formal_status=formal,
            formal_attempted=attempted,reason=reason,mathematical_refutation=validated=='refuted',
            technical_uncertainty=state=='technical_error',checker_result=check,subchecks=components,
            checker_metadata=fact.metadata,verification_id=fact.verification.verification_id,
            verification_ref=fact.verification.artifact_ref,
            sufficiency_decision=dict(sufficient=sufficient,policy=spec.sufficiency_policy,basis='frozen_P3_checker_and_validated_binding'),
            original_fact=fact.model_dump(mode='json')))
    for m in mapping:
        if not m['accepted']: status='CONFLICTING_EVIDENCE' if m['reason']=='conflicting_extractor_interpretation' else 'CONTEXT_REJECTED'
        elif any(r['obligation_id']==m['obligation_id'] and m['evidence_id'] in r['evidence_ids'] for r in results): continue
        else: status={'FORMAL':'FORMAL_NOT_ATTEMPTED','COMPOSITE':'COMPOSITE_INCOMPLETE','DETERMINISTIC':'DETERMINISTIC_INCOMPLETE'}[m['effective_route']]
        results.append(dict(obligation_id=m['obligation_id'],evidence_ids=[m['evidence_id']],primary_evidence_ids=[m['evidence_id']],
            source_claim_ids=[],route=m['effective_route'],status=status,formal_status='FORMAL_NOT_ATTEMPTED',
            formal_attempted=False,technical_uncertainty=False,mathematical_refutation=False,
            reason=m['reason'] if not m['accepted'] else 'no_checker_fact',checker_result=None,subchecks=[],
            sufficiency_decision=dict(sufficient=False,basis='no_eligible_checker_result')))
    return bridge,results,projection.events
