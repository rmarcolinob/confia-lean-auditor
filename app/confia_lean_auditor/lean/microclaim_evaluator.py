from __future__ import annotations

import json
from pathlib import Path
from typing import List

from confia_lean_auditor.core.paths import get_problem_dir
from confia_lean_auditor.core.schemas import (
    ClaimExtraction,
    LeanCertificate,
    MicroclaimResult,
)


def evaluate_microclaims(
    repo_root: Path,
    problem_id: str,
    claim_extraction: ClaimExtraction,
    lean_certificate: LeanCertificate,
    generated_theorems: List[str],
) -> List[MicroclaimResult]:
    problem_dir = get_problem_dir(repo_root, problem_id)
    path = problem_dir / "microclaims.json"

    if not path.exists():
        raise FileNotFoundError("Microclaim contract not found: " + str(path))

    data = json.loads(path.read_text(encoding="utf-8"))
    present_claim_types = set(claim.type for claim in claim_extraction.claims)
    generated = set(generated_theorems)

    results = []

    for item in data["microclaims"]:
        theorem = item.get("theorem")
        claim_types = item.get("claim_types", [])

        textual_evidence = (
            all(claim_type in present_claim_types for claim_type in claim_types)
            if claim_types
            else False
        )

        theorem_generated = theorem in generated if theorem else False

        if not textual_evidence:
            lean_status = "no_textual_evidence"
        elif not theorem_generated:
            lean_status = "not_generated"
        elif lean_certificate.status == "verified":
            lean_status = "verified_by_lean"
        else:
            lean_status = "not_verified_" + lean_certificate.status

        results.append(
            MicroclaimResult(
                id=item["id"],
                description=item["description"],
                theorem=theorem,
                claim_types=claim_types,
                textual_evidence=textual_evidence,
                lean_status=lean_status,
                supports_rubric_items=item.get("supports_rubric_items", []),
            )
        )

    return results
