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
from confia_lean_auditor.rubric.assessment import refresh_assessment


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

    microclaims_by_id = {mc.id: mc for mc in microclaims or []}
    verified_microclaim_ids = set()
    if microclaims is not None:
        verified_microclaim_ids = {
            mc.id
            for mc in microclaims
            if mc.textual_evidence and mc.lean_status in {"verified_by_lean", "verified_by_formal_steps"}
            and mc.dependencies_verified
        }

    items: List[RubricItemResult] = []

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

        # Neither an absent proof nor an absent extracted claim refutes the
        # student's mathematics. Keep undecidable criteria out of the score.
        points = float(item.points) if detected else None
        required = [microclaims_by_id.get(mc_id) for mc_id in required_microclaim_ids]
        availability = "available" if detected else (
            "technical_error" if any(mc and mc.verification_status == "technical_error" for mc in required)
            else "partial")

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
                mathematical_status="supported" if detected else "indeterminate",
                verification_status=availability,
                assessment_note=None if detected else (
                    "Verificação formal indisponível nesta execução." if availability == "technical_error"
                    else "Evidência insuficiente para decidir este critério nesta execução."),
            )
        )

    return refresh_assessment(RubricAssessment(
        score=None,
        max_score=float(rubric_config.max_score),
        items=items,
    ))
