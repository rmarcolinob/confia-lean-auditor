"""Non-destructive adapters into August StudentClaim and ClaimExtraction."""
from __future__ import annotations

import json
from confia_lean_auditor.student_claims.schemas import StudentClaim
from confia_lean_auditor.core.schemas import ClaimExtraction, ExtractedClaim, FormalStep
from confia_lean_auditor.rubric.adjusters.ita2025f2q1 import F2Q1_STUDENT_CHECK_TO_RUBRIC_ITEMS
from confia_lean_auditor.rubric.adjusters.ita2025f2q5 import F2Q5_STUDENT_CHECK_TO_RUBRIC_ITEMS
from confia_lean_auditor.rubric.adjusters.ita2025f2q6 import F2Q6_STUDENT_CHECK_TO_RUBRIC_ITEMS
from .semantic_student_claim import validate_payload
from .evidence_unit import EvidenceUnit

MAPPINGS = {"ITA2025F2Q1": F2Q1_STUDENT_CHECK_TO_RUBRIC_ITEMS,
            "ITA2025F2Q5": F2Q5_STUDENT_CHECK_TO_RUBRIC_ITEMS,
            "ITA2025F2Q6": F2Q6_STUDENT_CHECK_TO_RUBRIC_ITEMS}


def adapt_claim(claim: EvidenceUnit, problem_id, solution):
    if type(claim) is not EvidenceUnit:
        raise TypeError("Common adapter requires EvidenceUnit")
    claim.validate_source(problem_id, solution)
    payload = validate_payload(claim.claim_type, claim.normalized_payload, problem_id)
    # The old builder places raw_text in a Lean block comment. Neutralize nesting
    # and newline/control tricks; retain the untouched source_span in evidence.
    safe_comment = json.dumps(claim.source_span or "[source_span unavailable]", ensure_ascii=True).replace("/-", "/∕").replace("-/", "-∕")
    return StudentClaim(id=claim.evidence_id, problem_id=problem_id,
        claim_type=claim.claim_type, raw_text=safe_comment,
        normalized_text=json.dumps(payload, sort_keys=True), context=claim.source_span or "",
        data=payload, method="norm_num", confidence=1.0)


def matching_check(evidence, check, problem_id):
    return (check.id == evidence.evidence_id and check.problem_id == problem_id
            and check.claim_type == evidence.claim_type
            and check.data == evidence.normalized_payload)


def evidence_bridge(repo_root, problem_id, evidence: list[EvidenceUnit], checks):
    """Common obligation mapping; missing source spans have no scoring effect."""
    if any(type(e) is not EvidenceUnit for e in evidence):
        raise TypeError("Common bridge requires EvidenceUnit")
    if len({c.evidence_id for c in evidence}) != len(evidence):
        raise ValueError("Duplicate evidence_id")
    if len({c.id for c in checks}) != len(checks):
        raise ValueError("Duplicate check id")
    mapping = MAPPINGS[problem_id]
    by_item = {}
    for ev in evidence:
        if not ev.eligible_context():
            continue
        if not any(matching_check(ev, c, problem_id) and c.status == "verified" for c in checks):
            continue
        for item in mapping.get(ev.claim_type, []):
            by_item.setdefault(item, []).append(ev)
    # A failed claim conflicts even if the extractor labels it abandoned.
    for check in checks:
        if check.status == "failed":
            for item in mapping.get(check.claim_type, []):
                by_item.pop(item, None)
    if problem_id == "ITA2025F2Q1":
        exponents = {e.normalized_payload["exponent"] for e in by_item.get("power_reductions", [])}
        if not {57, 14, 7}.issubset(exponents):
            by_item.pop("power_reductions", None)
    if problem_id == "ITA2025F2Q6" and "final_answer" not in by_item:
        by_item.pop("maximizers_identification", None)
    rubric = json.loads((repo_root / "problems" / problem_id / "rubric.json").read_text())
    micros = json.loads((repo_root / "problems" / problem_id / "microclaims.json").read_text())
    claims, steps = [], {}
    for item in rubric["items"]:
        evs = by_item.get(item["id"], [])
        if not evs:
            continue
        span = "\n".join(e.source_span or f"[evidence_id={e.evidence_id}; source_span unavailable]" for e in evs)
        claims.append(ExtractedClaim(id=evs[0].evidence_id, type=item["claim_type"],
            text=item["description"], evidence=span, confidence=1.0, normalized={}))
        for micro in micros["microclaims"]:
            if item["id"] not in micro["supports_rubric_items"]:
                continue
            for kind in micro["required_formal_step_types"]:
                # Existing renderers own statements/methods, never the LLM.
                if kind in steps:
                    step = steps[kind]
                    step.supports_claim_types = sorted(set(step.supports_claim_types + micro["claim_types"]))
                    step.supports_rubric_items = sorted(set(step.supports_rubric_items + micro["supports_rubric_items"]))
                    if span not in step.evidence:
                        step.evidence += "\n" + span
                else:
                    method = {"f2q1_reduced_form": "ring", "f2q6_ratio_comparison": "omega"}.get(kind, "norm_num")
                    steps[kind] = FormalStep(id=kind, type=kind, description=micro["description"],
                        evidence=span, lhs="0", rhs="0", lean_method=method,
                        supports_claim_types=micro["claim_types"],
                        supports_rubric_items=micro["supports_rubric_items"])
    return ClaimExtraction(problem_id=problem_id, claims=claims, formal_steps=list(steps.values()))
