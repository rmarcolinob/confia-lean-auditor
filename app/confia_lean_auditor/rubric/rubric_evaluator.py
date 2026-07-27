from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from confia_lean_auditor.core.paths import get_problem_dir
from confia_lean_auditor.core.problem_assets import RubricConfig, load_rubric_config
from confia_lean_auditor.core.schemas import (
    ClaimExtraction,
    MicroclaimResult,
    RubricAssessment,
    RubricItemResult,
)


def evaluate_rubric(
    repo_root: Path,
    problem_id: str,
    claim_extraction: ClaimExtraction,
    microclaims: Optional[List[MicroclaimResult]] = None,
    rubric_config: Optional[RubricConfig] = None,
) -> RubricAssessment:
    if rubric_config is None:
        problem_dir = get_problem_dir(repo_root, problem_id)
        rubric_config = load_rubric_config(problem_dir)

    claims_by_type = {}
    for claim in claim_extraction.claims:
        claims_by_type.setdefault(claim.type, claim)

    verified_microclaim_ids = set()
    if microclaims is not None:
        verified_microclaim_ids = {
            mc.id
            for mc in microclaims
            if mc.textual_evidence and mc.lean_status == "verified_by_lean"
        }

    items: List[RubricItemResult] = []
    score = 0.0

    for item in rubric_config.items:
        claim_type = item.claim_type
        claim = claims_by_type.get(claim_type)

        required_microclaim_ids = item.required_microclaim_ids

        has_claim = claim is not None

        if required_microclaim_ids:
            has_required_microclaims = all(
                mc_id in verified_microclaim_ids for mc_id in required_microclaim_ids
            )
        else:
            has_required_microclaims = True

        detected = has_claim and has_required_microclaims

        points = float(item.points) if detected else 0.0
        score += points

        evidence = None
        claim_id = None

        if claim is not None:
            evidence = claim.evidence
            claim_id = claim.id

        items.append(
            RubricItemResult(
                id=item.id,
                description=item.description,
                detected=detected,
                points=points,
                max_points=float(item.points),
                evidence=evidence,
                claim_id=claim_id,
            )
        )

    return RubricAssessment(
        score=score,
        max_score=float(rubric_config.max_score),
        items=items,
    )
