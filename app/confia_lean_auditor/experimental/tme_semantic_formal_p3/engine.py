"""P3 interpretation → frozen verification → existing numeric scoring policy."""
from pathlib import Path
import subprocess
import time
from confia_lean_auditor.student_claims.semantic import sha
from confia_lean_auditor.student_claims.hybrid_semantic import config_for
from confia_lean_auditor.tme.obligation_experiment import primary_audit
from confia_lean_auditor.rubric.pauta.models import ObligationEvidence,PautaEvidence
from confia_lean_auditor.rubric.pauta.engine import PautaEngine
from confia_lean_auditor.experimental.tme_semantic_formal.score_closure import ScoreClosurePolicy
from confia_lean_auditor.experimental.tme_semantic_formal.award_gate import credited_rules
from . import VERSION
from .registry import PROBLEM_ID,REGISTRY,require_p3,registry_rows
from .extractor import SemanticExtractorP3
from .mapper import SourceDocument,ObligationMapper
from .verification import verify,POSITIVE
from .verification import formal_state
from confia_lean_auditor.experimental.tme_p3_checker_first.engine import audit_p3_checker_first

ROOT=Path(__file__).resolve().parents[4]


def configuration_hashes(extractor,config):
    local={p.name:sha(p.read_text()) for p in Path(__file__).parent.glob('*.py')}
    app=ROOT/'app/confia_lean_auditor'
    frozen={str(p.relative_to(app)):sha(p.read_text()) for folder in ('student_claims','claims','lean','rubric/pauta','core/math_canonical','tme','experimental/tme_p3_checker_first','experimental/tme_semantic_formal') for p in (app/folder).rglob('*.py')}
    runner=ROOT/'scripts/evaluation/run_tme_semantic_formal_p3.py'
    return dict(experiment=sha(local),source_files=local,frozen_code=sha(frozen),registry=sha(registry_rows()),
        pauta=sha(config.model_dump(mode='json')),extractor=sha(extractor.configuration()),
        runner=sha(runner.read_text()),lean_toolchain=sha((ROOT/'lean-toolchain').read_text()),lake_manifest=sha((ROOT/'lake-manifest.json').read_text()),machine=sha((ROOT/'examples/pautas/tme2_problem3.machine.v1.json').read_text()))


def reconcile(results,math_bridge,guard_bridge):
    """Guard evidence is veto-only; omitted positive source cannot award points."""
    current={o['obligation_id']:o for o in guard_bridge['bridge']['evidence']['obligations']}
    guard_conflicts={c['obligation_id'] for c in guard_bridge['conflicts']}
    math={o.obligation_id:o for o in math_bridge.evidence.obligations}
    conflicts=[]
    for oid in REGISTRY:
        rows=[r for r in results if r['obligation_id']==oid]
        positive=any(r['status'] in POSITIVE for r in rows)
        negative=any(r['mathematical_refutation'] for r in rows)
        contradictory=lambda o:o.metadata.get('reason') in {'CONFLICTING_FACT_RESULTS','CONFLICTING_CONDITIONAL_CONTEXTS'}
        if (positive and negative or any(r['status']=='CONFLICTING_EVIDENCE' for r in rows)
                or any(r.get('checker_metadata',{}).get('decision',{}).get('reason')=='conflicting_source_evidence' for r in rows)
                or contradictory(math[oid]) or oid in guard_conflicts or positive and current[oid]['status']=='refuted'):
            conflicts.append(dict(obligation_id=oid,status='CONFLICTING_EVIDENCE',resolved=False,
                resolution_rule=None,reason='conflicting_source_or_checker_evidence',
                evidence_ids=list(dict.fromkeys(i for r in rows for i in r['evidence_ids'])),
                selected_evidence=math[oid].model_dump(mode='json'),guard_evidence=current[oid],
                guard_source_records=[r for r in guard_bridge['bridge']['auditor']['records'] if r['record_id'] in current[oid]['source_claim_ids']]))
    return conflicts


def award(case_id,evidence,mapping,results,conflicts):
    eligible={(m['evidence_id'],m['obligation_id'],m['effective_route']) for m in mapping if m['accepted'] and m['context_valid']}
    accepted_ids={i for i,_,_ in eligible}
    by_id={e.evidence_id:e for e in evidence};blocked={c['obligation_id'] for c in conflicts if not c['resolved']}
    observations=[];awards=[]
    for oid,spec in REGISTRY.items():
        rows=[r for r in results if r['obligation_id']==oid]
        positives=[r for r in rows if r['status'] in POSITIVE and r['route'] in spec.allowed_routes
            and r['sufficiency_decision']['sufficient'] and r.get('verification_id')
            and r.get('original_fact') and r['evidence_ids']
            and any((i,oid,r['route']) in eligible for i in r['primary_evidence_ids'])
            and all(i in accepted_ids and i in by_id and by_id[i].assertion_status=='asserted'
                    and by_id[i].polarity=='positive' and by_id[i].attributed_to_student
                    and not by_id[i].hypothetical and not by_id[i].abandoned for i in r['evidence_ids'])]
        negative=any(r['mathematical_refutation'] for r in rows)
        chosen=next(iter(positives),None) if oid not in blocked and not negative else None
        technical=any(r['technical_uncertainty'] for r in rows)
        status='supported' if chosen else 'indeterminate' if oid in blocked else 'refuted' if negative else 'technical_error' if technical else 'indeterminate'
        refs=list(dict.fromkeys(i for r in rows for i in r['evidence_ids']))
        effective_route=chosen['route'] if chosen else rows[0]['route'] if rows else spec.route
        origin='student_lean' if effective_route=='FORMAL' else 'deterministic'
        reason='verified_and_sufficient' if chosen else 'blocked_conflict' if oid in blocked else 'no_sufficient_checker_result'
        observations.append(ObligationEvidence(obligation_id=oid,status=status,origin=origin,verification_source=origin,
            attributable_to_student=bool(chosen or negative),evidence_refs=tuple(refs),source_claim_ids=tuple(chosen['source_claim_ids']) if chosen else (),
            grounding_status='grounded' if refs else 'unavailable',metadata=dict(reason=reason,version=VERSION,conflict=oid in blocked)))
        awards.append(dict(obligation_id=oid,rubric_item=spec.rubric_item,eligible=chosen is not None,
            evidence_ids=chosen['evidence_ids'] if chosen else [],verification_route=chosen['route'] if chosen else None,
            verification_status=chosen['status'] if chosen else None,verification_result=chosen,
            sufficiency_decision=chosen['sufficiency_decision'] if chosen else None,award_decision=reason,technical_uncertainty=technical))
    return PautaEvidence(problem_id=PROBLEM_ID,solution_id=case_id,obligations=tuple(observations)),awards


def evaluate(case_id,problem_id,text,*,mode='tme_semantic_formal',model='gpt-6.1-sol',reasoning_effort='medium',extraction_provider=None,use_lean=True):
    require_p3(problem_id)
    if mode not in {'tme_current','tme_semantic_formal'}:raise ValueError('unknown_P3_mode')
    start=time.monotonic();document=SourceDocument.parse(text);config=config_for(PROBLEM_ID)
    extractor=SemanticExtractorP3(model,reasoning_effort)
    requested='TME_CURRENT' if mode=='tme_current' else 'TME_SEMANTIC_FORMAL'
    output=dict(case_id=case_id,problem_id=PROBLEM_ID,version=VERSION,requested_mode=requested,effective_mode=requested,
        fallback=False,fallback_used=False,fallback_reason=None,model=model,reasoning_effort=reasoning_effort,use_lean=use_lean,
        code_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        configuration_hashes=configuration_hashes(extractor,config),source_text=text,source_sha256=sha(text),source_item_ranges=document.ranges,
        extracted_evidence=[],obligation_mapping=[],verification_results=[],awards=[],credits=[],rejected_evidence=[],conflicts=[],projection=[])
    units=();meta=dict(status='not_requested',api_calls=0)
    if mode!='tme_current':units,meta=extractor.extract(PROBLEM_ID,text,provider=extraction_provider)
    output['extractor']=meta
    if mode=='tme_current' or meta['status']!='completed':
        bridge,assessment=primary_audit(PROBLEM_ID,document.items,solution_id=case_id,use_lean=use_lean)
        if mode!='tme_current':output.update(effective_mode='TME_CURRENT_FALLBACK',fallback=True,fallback_used=True,fallback_reason=meta.get('reason','extractor_unavailable'))
        output.update(ScoreClosurePolicy().close(assessment))
        current_results=[]
        for fact in bridge.auditor.facts:
            status,attempted=formal_state(fact.student_check,fact.verification.status)
            current_results.append(dict(obligation_id=fact.fact_id,route='FORMAL' if fact.student_check else 'DETERMINISTIC',
                status=status if fact.student_check else {'verified':'DETERMINISTIC_VERIFIED','refuted':'DETERMINISTIC_FAILED','technical_error':'DETERMINISTIC_ERROR'}.get(fact.verification.status,'DETERMINISTIC_INCOMPLETE'),formal_status=status,state=fact.verification.status,formal_attempted=attempted,
                checker_result=fact.student_check,subchecks=fact.metadata.get('components',[]),
                original_fact=fact.model_dump(mode='json')))
        current_awards=[dict(obligation_id=e.obligation_id,rubric_item=e.obligation_id[0],eligible=e.status=='supported',
            verification_route='FORMAL' if e.verification_source=='student_lean' else 'DETERMINISTIC',
            evidence_refs=list(e.evidence_refs),original_evidence=e.model_dump(mode='json')) for e in bridge.evidence.obligations]
        credits=credited_rules(assessment,current_awards)
        if sum(c['points'] for c in credits)!=float(assessment.known_points):raise ValueError('baseline_credit_trace_does_not_close')
        current_conflicts=[dict(obligation_id=e.obligation_id,status='CONFLICTING_EVIDENCE',resolved=False,
            resolution_rule=None,reason=e.metadata['reason'],original_evidence=e.model_dump(mode='json'))
            for e in bridge.evidence.obligations if e.metadata.get('reason') in {'CONFLICTING_FACT_RESULTS','CONFLICTING_CONDITIONAL_CONTEXTS'}]
        blocked={c['obligation_id'] for c in current_conflicts}
        output.update(current_bridge=bridge.model_dump(mode='json'),current_assessment=assessment.model_dump(mode='json'),
            verification_results=current_results,awards=current_awards,credits=credits,conflicts=current_conflicts,
            rejected_evidence=[r for r in current_results if r['state']!='verified' or r['obligation_id'] in blocked],
            rubric_items=[i.model_dump(mode='json') for i in assessment.items])
    else:
        mapping=ObligationMapper().map(document,units)
        bridge,results,projection=verify(document,units,mapping,config,case_id,use_lean=use_lean)
        guard=audit_p3_checker_first(document.items,solution_id=case_id,use_lean=False)
        conflicts=reconcile(results,bridge,guard)
        observations,awards=award(case_id,units,mapping,results,conflicts)
        assessment=PautaEngine().evaluate(config,observations)
        credits=credited_rules(assessment,awards)
        if sum(c['points'] for c in credits)!=float(assessment.known_points):raise ValueError('credit_trace_does_not_close')
        blocked={c['obligation_id'] for c in conflicts if not c['resolved']}
        output.update(extracted_evidence=[u.model_dump(mode='json') for u in units],obligation_mapping=mapping,
            verification_results=results,awards=awards,credits=credits,conflicts=conflicts,projection=projection,
            rejected_evidence=[r for r in results if r['status'] not in POSITIVE or not r['sufficiency_decision']['sufficient'] or r['obligation_id'] in blocked],
            mathematical_bridge=bridge.model_dump(mode='json'),evidence=observations.model_dump(mode='json'),
            pauta_assessment=assessment.model_dump(mode='json'),rubric_items=[i.model_dump(mode='json') for i in assessment.items])
        output.update(ScoreClosurePolicy().close(assessment,technical_uncertainty=any(r['technical_uncertainty'] for r in results),
            review_recommended=bool(conflicts) or bool(output['rejected_evidence'])))
    output['latency']=time.monotonic()-start
    return output
