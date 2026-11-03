"""One pure award policy for EvidenceUnit; no extractor-specific scoring paths."""
from __future__ import annotations

import math
from confia_lean_auditor.core.schemas import RubricAssessment, RubricItemResult
from confia_lean_auditor.semantic.evidence_unit import EvidenceUnit
from confia_lean_auditor.semantic.semantic_claim_adapter import MAPPINGS, matching_check

AWARD_POLICY = "common_evidence_formal_award.v2"
EXPERIMENT_DESIGN = ("Both modes use EvidenceUnit, one adapter, the historical checkers and Lean, "
    "one obligation mapping, one FormalAwardGate and one score function. "
    "Only extraction/contextualization differs. Fallbacks are reported separately.")


def final_score(items):
    """Count each rubric item exactly once, bounded by its immutable rubric maximum."""
    if len({i.id for i in items}) != len(items):
        raise ValueError("Duplicate rubric item")
    if any(not math.isfinite(i.points) or not 0 <= i.points <= i.max_points for i in items):
        raise ValueError("Invalid item award")
    score = float(sum(i.points for i in items))
    if not 0 <= score <= 10:
        raise ValueError("Score outside [0,10]")
    return score


def formal_award_gate(problem_id, evidence: list[EvidenceUnit], checks, microclaims=(),
                      extraction=None, rubric_config=None):
    """Same predicates for every evidence unit. Labels are copied to audit only."""
    if any(type(e) is not EvidenceUnit for e in evidence):
        raise TypeError("FormalAwardGate requires EvidenceUnit")
    if rubric_config is None:
        raise ValueError("Frozen rubric configuration required")
    if len({e.evidence_id for e in evidence}) != len(evidence):
        raise ValueError("Duplicate evidence_id")
    if len({c.id for c in checks}) != len(checks):
        raise ValueError("Duplicate check id")
    mapping = MAPPINGS[problem_id]
    verified_mc = {m.id for m in microclaims if m.lean_status == "verified_by_lean"
                   and m.textual_evidence and m.formal_steps_verified and m.dependencies_verified}
    present = {c.type for c in extraction.claims} if extraction else set()
    items, decisions = [], []
    for config in rubric_config.items:
        evs = [ev for ev in evidence if config.id in mapping.get(ev.claim_type, [])]
        related = [c for c in checks if c.problem_id == problem_id
                   and config.id in mapping.get(c.claim_type, [])]
        failed = [c for c in related if c.status == "failed"]
        verified = [c for c in related if c.status == "verified"]
        records, eligible, context_excluded = [], [], []
        for ev in evs:
            bound = [c for c in related if matching_check(ev, c, problem_id)]
            status = bound[0].status if bound else "not_checked_or_mismatched"
            context_ok = ev.eligible_context()
            if status == "verified" and context_ok:
                eligible.append(ev.evidence_id)
            if not context_ok:
                context_excluded.append(ev.evidence_id)
            records.append(dict(ev.model_dump(mode="json"), lean_status=status,
                                context_eligible=context_ok))
        obligation = (config.claim_type in present
                      and all(mid in verified_mc for mid in config.required_microclaim_ids))
        if failed:
            rejection = "conflicting_failed"
        elif not evs:
            rejection = "no_evidence"
        elif not eligible:
            rejection = ("context_rejected" if any(r["lean_status"] == "verified" and not r["context_eligible"]
                                                   for r in records) else "claim_not_verified")
        elif not obligation:
            rejection = "formal_obligation_not_satisfied"
        else:
            rejection = None
        award = float(config.points) if rejection is None else 0.0
        used = eligible if rejection is None else []
        item = RubricItemResult(id=config.id, description=config.description,
            detected=award > 0, points=award, max_points=float(config.points),
            evidence="\n".join(r["source_span"] for r in records if r["evidence_id"] in used and r["source_span"]) or None,
            claim_id=used[0] if used else None)
        items.append(item)
        decisions.append({"rubric_item_id": config.id, "policy": AWARD_POLICY,
            "evidence": records, "used_evidence_ids": used,
            "claim_types": sorted({e.claim_type for e in evs}),
            "gate_decision": "award" if rejection is None else "reject",
            "award": award, "points": award, "max_points": float(config.points),
            "rejection_reason": rejection, "reason": rejection or "eligible_verified_obligation_satisfied",
            "conflicting_evidence": [{"evidence_id": c.id, "claim_type": c.claim_type,
                "lean_status": c.status, "normalized_payload": c.data} for c in failed],
            "verified_check_ids": [c.id for c in verified], "failed_check_ids": [c.id for c in failed],
            "eligible_evidence_ids": eligible, "excluded_evidence_ids": context_excluded,
            "required_microclaim_ids": list(config.required_microclaim_ids),
            "obligation_satisfied": obligation, "formal_obligation_satisfied": obligation})
    result = RubricAssessment(score=final_score(items), max_score=float(rubric_config.max_score), items=items)
    return result, decisions
