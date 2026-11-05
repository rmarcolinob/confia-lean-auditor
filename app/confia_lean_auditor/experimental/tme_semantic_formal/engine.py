"""Explicit P1 experiment and current-pipeline numeric wrapper. No global switch."""
from __future__ import annotations

from pathlib import Path
import subprocess
import time
from confia_lean_auditor.student_claims.semantic import sha
from confia_lean_auditor.student_claims.hybrid_semantic import config_for
from confia_lean_auditor.rubric.pauta.engine import PautaEngine
from confia_lean_auditor.rubric.pauta.evidence_policy import HybridEvidencePolicy
from confia_lean_auditor.tme.obligation_experiment import primary_audit
from . import VERSION
from .obligation_registry import PROBLEM_ID, REGISTRY, require_p1, registry_rows
from .obligation_mapper import SourceDocument, ObligationMapper
from .semantic_extractor import SemanticExtractorTME
from .verification import mathematical_verification, semantic_verification
from .verification import verification_status, complete_item_sufficiency
from .reconciliation import reconcile
from .award_gate import AwardGate, credited_rules
from .score_closure import ScoreClosurePolicy

ROOT = Path(__file__).resolve().parents[4]


def configuration_hashes(extractor, config):
    # SHA alone cannot identify an uncommitted experiment. Bind all experiment
    # sources, reused runtime sources and the exact rubric as separate hashes.
    local = {p.name: sha(p.read_text()) for p in Path(__file__).parent.glob('*.py')}
    app = ROOT / 'app/confia_lean_auditor'
    reused = {str(p.relative_to(app)): sha(p.read_text()) for folder in
              ('student_claims', 'claims', 'lean', 'rubric/pauta', 'core/math_canonical', 'tme')
              for p in (app/folder).rglob('*.py')}
    return dict(experiment=sha(local), reused_code=sha(reused),
                registry=sha(registry_rows()), pauta=sha(config.model_dump(mode='json')),
                extractor=sha(extractor.configuration()), source_files=local,
                runner=sha((ROOT/'scripts/evaluation/run_tme_semantic_formal_c1.py').read_text()),
                lean_toolchain=sha((ROOT/'lean-toolchain').read_text()),
                lake_manifest=sha((ROOT/'lake-manifest.json').read_text()))


def current_verification_results(bridge):
    from confia_lean_auditor.rubric.pauta.bridge import TME2_P1_OBLIGATIONS
    result = []
    for fact in bridge.auditor.facts:
        route = 'FORMAL' if fact.verification_source == 'student_lean' else 'DETERMINISTIC'
        result.append(dict(obligation_id=TME2_P1_OBLIGATIONS[fact.fact_id], evidence_ids=[],
            source_claim_ids=list(fact.source_claim_ids), route=route,
            status=verification_status(route, fact.verification.status),
            technical_uncertainty=fact.verification.status == 'technical_error',
            verification_ref=fact.verification.artifact_ref, checker_result=fact.student_check,
            provenance='TME_CURRENT_original_fact', original_fact=fact.model_dump(mode='json')))
    return result


def evaluate(case_id, problem_id, text, *, mode='tme_semantic_formal', model='gpt-4o-mini-2024-07-18',
             reasoning_effort='none', extraction_provider=None, sufficiency_provider=None, use_lean=True):
    require_p1(problem_id)
    if mode not in {'tme_current', 'tme_semantic_formal'}:
        raise ValueError('unknown_C1_runner_mode')
    started = time.monotonic()
    document = SourceDocument.parse(text)
    config = config_for(PROBLEM_ID)
    extractor = SemanticExtractorTME(model, reasoning_effort)
    requested = 'TME_CURRENT' if mode == 'tme_current' else 'TME_SEMANTIC_FORMAL'
    output = dict(case_id=case_id, problem_id=PROBLEM_ID, requested_mode=requested, effective_mode=requested,
        score=0.0, extracted_evidence=[], obligation_mapping=[], verification_results=[],
        formal_awards=[], deterministic_awards=[], semantic_awards=[], credits=[], rejected_evidence=[],
        conflicts=[], rubric_items=[], fallback_used=False, fallback_reason=None,
        model=model, reasoning_effort=reasoning_effort, use_lean=use_lean,
        token_usage={}, source_sha256=sha(text), version=VERSION,
        source_text=text, source_item_ranges=document.ranges,
        configuration_hashes=configuration_hashes(extractor, config),
        code_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
    evidence, extraction = (), dict(status='not_requested', api_calls=0)
    if mode != 'tme_current':
        evidence, extraction = extractor.extract(PROBLEM_ID, text, provider=extraction_provider)
        output['extractor'] = extraction
        output['token_usage']['extractor'] = extraction.get('usage')
    if mode == 'tme_current' or extraction['status'] != 'completed':
        # Exact existing local baseline; pin supplement off for reproducibility
        # and avoid a second call to the unavailable extractor during fallback.
        bridge, assessment = primary_audit(PROBLEM_ID, document.items, solution_id=case_id, use_lean=use_lean)
        if mode != 'tme_current':
            output.update(effective_mode='TME_CURRENT_FALLBACK', fallback_used=True,
                          fallback_reason=extraction.get('reason', 'extractor_unavailable'))
        output.update(ScoreClosurePolicy().close(assessment))
        output.update(current_bridge=bridge.model_dump(mode='json'),
                      current_assessment=assessment.model_dump(mode='json'),
                      verification_results=current_verification_results(bridge),
                      rubric_items=[i.model_dump(mode='json') for i in assessment.items])
    else:
        mapping = ObligationMapper().map(document, evidence)
        math_bridge, results, projection = mathematical_verification(document, evidence, mapping,
            config, case_id, use_lean=use_lean)
        # Read all locally detectable claims only as a contradiction veto.
        # Unselected positive evidence cannot grant credit in the experiment.
        guard, _ = primary_audit(PROBLEM_ID, document.items, solution_id=case_id, use_lean=False)
        complete_item_sufficiency(results, guard)
        semantic, sufficiency = semantic_verification(document, evidence, mapping, extractor,
                                                       provider=sufficiency_provider)
        results += semantic
        for m in mapping:
            if not m['accepted']:
                results.append(dict(obligation_id=m['obligation_id'], evidence_ids=[m['evidence_id']],
                    route=None, status='CONFLICTING_EVIDENCE' if m['reason'] == 'conflicting_extractor_context' else 'CONTEXT_REJECTED',
                    reason=m['reason'], technical_uncertainty=False,
                    mathematical_refutation=False, sufficiency_decision=dict(sufficient=False)))
        conflicts, inherited = reconcile(document, math_bridge, guard, results)
        observed, awards = AwardGate().evaluate(case_id, evidence, mapping, results, conflicts)
        assessment = PautaEngine().evaluate(config, observed, evidence_policy=HybridEvidencePolicy())
        credits = credited_rules(assessment, awards)
        if sum(c['points'] for c in credits) != float(assessment.known_points):
            raise ValueError('credit_trace_does_not_close_to_authorized_score')
        # Partition credits, do not repeat a mixed rule's points across routes.
        # Mixed credits retain their full routes/witnesses in the canonical trace.
        for credit in credits:
            category = ('semantic_awards' if 'SEMANTIC' in credit['routes'] else
                        'formal_awards' if 'FORMAL' in credit['routes'] else 'deterministic_awards')
            output[category].append(credit)
        output.update(extracted_evidence=[e.model_dump(mode='json') for e in evidence],
            obligation_mapping=mapping, verification_results=results, conflicts=conflicts,
            rejected_evidence=[r for r in results if r['status'] not in
                               {'FORMAL_VERIFIED', 'DETERMINISTIC_VERIFIED', 'SEMANTIC_SUPPORTED'}
                               or not r['sufficiency_decision']['sufficient']
                               or any(c['obligation_id'] == r['obligation_id'] and not c['resolved'] for c in conflicts)],
            awards=awards, credits=credits, rubric_items=[i.model_dump(mode='json') for i in assessment.items],
            pauta_assessment=assessment.model_dump(mode='json'), evidence=observed.model_dump(mode='json'),
            mathematical_bridge=math_bridge.model_dump(mode='json'), projection=projection,
            inherited_reconciliation=inherited, sufficiency=sufficiency)
        output['token_usage']['sufficiency'] = sufficiency['provider'].get('usage')
        output.update(ScoreClosurePolicy().close(assessment,
            technical_uncertainty=any(r.get('technical_uncertainty') for r in results),
            review_recommended=bool(conflicts) or any(not m['accepted'] for m in mapping)))
    output['latency'] = time.monotonic()-started
    return output
