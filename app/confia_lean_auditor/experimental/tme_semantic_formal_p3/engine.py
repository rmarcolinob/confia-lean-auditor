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
from .mapper import SourceDocument
from .verification import POSITIVE
from .verification import formal_state
from .unified import run_unified

ROOT=Path(__file__).resolve().parents[4]


def configuration_hashes(extractor,config):
    local={p.name:sha(p.read_text()) for p in Path(__file__).parent.glob('*.py')}
    app=ROOT/'app/confia_lean_auditor'
    frozen={str(p.relative_to(app)):sha(p.read_text()) for folder in ('student_claims','claims','lean','rubric/pauta','core/math_canonical','tme','experimental/tme_p3_checker_first','experimental/tme_semantic_formal') for p in (app/folder).rglob('*.py')}
    runner=ROOT/'scripts/evaluation/run_tme_semantic_formal_p3.py'
    return dict(experiment=sha(local),source_files=local,frozen_code=sha(frozen),registry=sha(registry_rows()),
        pauta=sha(config.model_dump(mode='json')),extractor=sha(extractor.configuration()),
        runner=sha(runner.read_text()),lean_toolchain=sha((ROOT/'lean-toolchain').read_text()),lake_manifest=sha((ROOT/'lake-manifest.json').read_text()),machine=sha((ROOT/'examples/pautas/tme2_problem3.machine.v1.json').read_text()))


def award(case_id,evidence,mapping,results,conflicts,policy):
    if not policy.snapshot.valid():raise ValueError('stale_discourse_snapshot')
    eligible={(m['evidence_id'],m['obligation_id'],m['effective_route']) for m in mapping if m['accepted'] and m['context_valid']}
    accepted_ids={i for i,_,_ in eligible}
    by_id={e.evidence_id:e for e in evidence}
    blocked={c['obligation_id'] for c in conflicts if any(c['obligation_id'] in d['target_obligation_ids'] for d in policy.applied(c.get('policy_decisions',[])))}
    observations=[];awards=[]
    for oid,spec in REGISTRY.items():
        rows=[r for r in results if r['obligation_id']==oid]
        automatic=[policy.automation.decide(r,blocked=oid in blocked) for r in rows]
        authorized={a['checker_ref'] for a in automatic if a['automation_eligibility']=='AUTO_AWARD'}
        positives=[r for r in rows if r.get('verification_id') in authorized
            and r['status'] in POSITIVE and r['route'] in spec.allowed_routes
            and r['sufficiency_decision']['sufficient'] and r.get('verification_id')
            and r.get('original_fact') and r['evidence_ids']
            and any((i,oid,r['route']) in eligible for i in r['primary_evidence_ids'])
            and not r.get('guard_only',False)
            and all(i in accepted_ids and i in by_id and policy.snapshot.get(i)
                    and policy.snapshot.get(i).positive_credit_eligible
                    and by_id[i].metadata.get('ledger_revision')==policy.snapshot.ledger_revision
                    and by_id[i].metadata.get('source_sha256')==policy.snapshot.source_sha256 for i in r['evidence_ids'])]
        negative=oid in blocked
        chosen=next(iter(sorted(positives,key=lambda r:r['verification_id'])),None) if oid not in blocked else None
        technical=any(r['technical_uncertainty'] for r in rows)
        status='supported' if chosen else 'indeterminate' if oid in blocked else 'refuted' if negative else 'technical_error' if technical else 'indeterminate'
        refs=sorted({i for r in rows for i in r['evidence_ids']} | {i for c in conflicts if c['obligation_id']==oid for d in policy.applied(c.get('policy_decisions',[])) for i in d['evidence_ids']})
        effective_route=chosen['route'] if chosen else rows[0]['route'] if rows else spec.route
        origin='student_lean' if effective_route=='FORMAL' else 'deterministic'
        reason='verified_and_sufficient' if chosen else 'blocked_conflict' if oid in blocked else 'no_sufficient_checker_result'
        observations.append(ObligationEvidence(obligation_id=oid,status=status,origin=origin,verification_source=origin,
            attributable_to_student=bool(chosen or negative),evidence_refs=tuple(refs),source_claim_ids=tuple(chosen['source_claim_ids']) if chosen else (),
            grounding_status='grounded' if refs else 'unavailable',metadata=dict(reason=reason,version=VERSION,conflict=oid in blocked)))
        awards.append(dict(obligation_id=oid,rubric_item=spec.rubric_item,eligible=chosen is not None,
            evidence_ids=chosen['evidence_ids'] if chosen else [],verification_route=chosen['route'] if chosen else None,
            verification_status=chosen['status'] if chosen else None,verification_result=chosen,
            sufficiency_decision=chosen['sufficiency_decision'] if chosen else None,award_decision=reason,technical_uncertainty=technical,
            automation_eligibility='AUTO_AWARD' if chosen else 'AUTO_VETO' if oid in blocked else 'REVIEW_ONLY',
            automation_decisions=automatic,
            obligation_support_bundle=dict(obligation_id=oid,source_sha256=policy.snapshot.source_sha256,
                ledger_revision=policy.snapshot.ledger_revision,positive_witnesses=sorted(authorized),
                review_refs=[a['decision_id'] for a in automatic if a['automation_eligibility']=='REVIEW_ONLY'],
                veto_refs=[d['decision_id'] for c in conflicts if c['obligation_id']==oid for d in policy.applied(c.get('policy_decisions',[]))]),
            decision_receipt=dict(ledger_revision=policy.snapshot.ledger_revision,source_sha256=policy.snapshot.source_sha256,
                positive_witness=chosen.get('verification_id') if chosen else None,
                veto_decisions=[d['decision_id'] for c in conflicts if c['obligation_id']==oid for d in policy.applied(c.get('policy_decisions',[]))],
                absence_reason=None if chosen or oid in blocked else 'no_current_sufficient_checker_witness')))
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
    if mode=='tme_current':
        bridge,assessment=primary_audit(PROBLEM_ID,document.items,solution_id=case_id,use_lean=use_lean)
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
        fallback=meta['status']!='completed'
        if fallback:
            output.update(effective_mode='TME_SEMANTIC_FORMAL_NATIVE_FALLBACK',fallback=True,
                fallback_used=True,fallback_reason=meta.get('reason','extractor_unavailable'))
        views,mapping,bridge,results,projection,policy,conflicts,trace=run_unified(
            document,units,config,case_id,use_lean=use_lean,fallback=fallback)
        observations,awards=award(case_id,views,mapping,results,conflicts,policy)
        output.update(trace)
        output['automation_decisions']=[d for a in awards for d in a['automation_decisions']]+[v['automation_decision'] for v in trace['veto_decisions']]
        assessment=PautaEngine().evaluate(config,observations)
        credits=credited_rules(assessment,awards)
        if sum(c['points'] for c in credits)!=float(assessment.known_points):raise ValueError('credit_trace_does_not_close')
        blocked={c['obligation_id'] for c in conflicts if not c['resolved']}
        output.update(extracted_evidence=[u.model_dump(mode='json') for u in units],obligation_mapping=mapping,
            verification_results=results,awards=awards,credits=credits,conflicts=conflicts,projection=projection,
            rejected_evidence=[r for r in results if r['status'] not in POSITIVE or not r['sufficiency_decision']['sufficient'] or r['obligation_id'] in blocked],
            mathematical_bridge=bridge.model_dump(mode='json'),evidence=observations.model_dump(mode='json'),
            pauta_assessment=assessment.model_dump(mode='json'),rubric_items=[i.model_dump(mode='json') for i in assessment.items])
        output.update(ScoreClosurePolicy().close(assessment,technical_uncertainty=any(r.get('technical_uncertainty',False) for r in results+trace['native_guard_results']+trace['conflict_guard_results']),
            review_recommended=bool(conflicts) or bool(output['rejected_evidence']) or any(d.state=='AMBIGUOUS' for d in policy.snapshot.decisions)))
    output['latency']=time.monotonic()-start
    return output
