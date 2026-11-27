"""Evidence-ID shadow route reusing the existing experimental verification path."""
import json

from confia_lean_auditor.student_claims import semantic as legacy
from confia_lean_auditor.student_claims import evidence_id_semantic as semantic
from confia_lean_auditor.student_claims.obligation_catalog import internal_id
from .obligation_experiment import primary_audit, unresolved_targets, verify_without_scoring, ShadowAudit


def run_shadow(problem_id, items, full_text, *, solution_id, use_lean=True, provider=None, primary=None):
    problem_id = internal_id(problem_id)
    primary_bridge, assessment = primary or primary_audit(problem_id, items, solution_id=solution_id, use_lean=use_lean)
    targets = unresolved_targets(problem_id, primary_bridge)
    config = semantic.configuration()
    request = provider or semantic.request_selections
    if targets:
        selections, metadata = request(problem_id, full_text, json.dumps(targets, ensure_ascii=False, sort_keys=True), json.dumps(config, sort_keys=True))
    else:
        selections, metadata = (), dict(status='skipped', api_calls=0)
    session = semantic.EvidenceProjectionSession(problem_id, full_text, targets, selections, metadata)
    with legacy.supplement_scope(session):
        potential = verify_without_scoring(problem_id, items, solution_id, use_lean=use_lean)
    baseline_supported = {e.obligation_id for e in primary_bridge.evidence.obligations if e.status == 'supported'}
    combined_supported = {e.obligation_id for e in potential.evidence.obligations if e.status == 'supported'}
    lost = sorted(baseline_supported - combined_supported)
    # Reject the whole supplementation if it would erase primary evidence.
    # No merging/relabeling of facts or changes to bridge/scoring semantics.
    if lost:
        potential = primary_bridge
        combined_supported = baseline_supported
    session.telemetry.update(baseline_supported=len(baseline_supported),
        semantic_potential_supported_new=len(combined_supported - baseline_supported),
        combined_potential_supported=len(combined_supported), baseline_regression_blocked=lost)
    return ShadowAudit(problem_id, primary_bridge, assessment, potential, session.telemetry, config)
