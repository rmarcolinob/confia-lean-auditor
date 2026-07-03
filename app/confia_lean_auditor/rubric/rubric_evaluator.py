from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from confia_lean_auditor.core.schemas import (
    ClaimExtraction,
    ExtractedClaim,
    RubricAssessment,
    RubricItemResult,
)


def find_claim(claims: ClaimExtraction, claim_type: str) -> Optional[ExtractedClaim]:
    for claim in claims.claims:
        if claim.type == claim_type:
            return claim
    return None


def evaluate_rubric(
    repo_root: Path,
    problem_id: str,
    claim_extraction: ClaimExtraction,
) -> RubricAssessment:
    rubric_path = repo_root / "problems" / problem_id / "rubric.json"

    if not rubric_path.exists():
        raise FileNotFoundError("Rubric not found: " + str(rubric_path))

    rubric = json.loads(rubric_path.read_text(encoding="utf-8"))

    results = []
    total = 0.0

    for item in rubric["items"]:
        claim_type = item["claim_type"]
        claim = find_claim(claim_extraction, claim_type)

        detected = claim is not None
        points = float(item["points"]) if detected else 0.0
        total += points

        results.append(
            RubricItemResult(
                id=item["id"],
                description=item["description"],
                detected=detected,
                points=points,
                max_points=float(item["points"]),
                evidence=claim.evidence if claim else None,
                claim_id=claim.id if claim else None,
            )
        )

    return RubricAssessment(
        score=total,
        max_score=float(rubric["max_score"]),
        items=results,
    )
