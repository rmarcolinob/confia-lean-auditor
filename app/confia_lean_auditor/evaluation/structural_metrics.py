"""Structural counters over persisted case results; no external inputs."""
import math


def case_metrics(row):
    checks = row.get("student_claim_checks", [])
    decisions = row.get("formal_award_decisions", [])
    score = row.get("score")
    return {
        "claims_extracted": len(row.get("extracted_evidence", [])),
        "claims_submitted_to_checker": len(checks),
        "claims_sent_to_lean": sum(bool(c.get("lean_file")) or c.get("status") in {"verified", "failed"} for c in checks),
        "verified": sum(c["status"] == "verified" for c in checks),
        "failed": sum(c["status"] == "failed" for c in checks),
        "rubric_items_with_evidence": sum(bool(d.get("evidence")) for d in decisions),
        "items_scored": sum(i["points"] > 0 for i in row.get("rubric_items", [])),
        "items_rejected_for_context": sum(d.get("rejection_reason") == "context_rejected" for d in decisions),
        "items_rejected_for_insufficiency": sum(d.get("rejection_reason") in {
            "no_evidence", "claim_not_verified", "formal_obligation_not_satisfied"} for d in decisions),
        "items_rejected_for_conflict": sum(d.get("rejection_reason") == "conflicting_failed" for d in decisions),
        "fallbacks": int(bool(row.get("fallback_used", False))),
        "numeric_scores": int(type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 10),
    }


def aggregate_metrics(rows):
    total = {key: 0 for key in case_metrics({})}
    for row in rows:
        for key, value in case_metrics(row).items():
            total[key] += value
    return total
