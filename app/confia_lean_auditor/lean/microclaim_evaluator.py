from __future__ import annotations

import json
from pathlib import Path
from typing import List

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
) -> List[MicroclaimResult]:
    path = repo_root / "problems" / problem_id / "microclaims.json"

    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    present_claim_types = set(claim.type for claim in claim_extraction.claims)

    results = []

    for item in data["microclaims"]:
        claim_types = item.get("claim_types", [])
        textual_evidence = any(claim_type in present_claim_types for claim_type in claim_types)

        if lean_certificate.status == "verified":
            lean_status = "verified_by_lean"
        else:
            lean_status = "not_verified_" + lean_certificate.status

        results.append(
            MicroclaimResult(
                id=item["id"],
                description=item["description"],
                theorem=item.get("theorem"),
                claim_types=claim_types,
                textual_evidence=textual_evidence,
                lean_status=lean_status,
                supports_rubric_items=item.get("supports_rubric_items", []),
            )
        )

    return results
