from __future__ import annotations

from confia_lean_auditor.core.schemas import ClaimExtraction
from confia_lean_auditor.claims.extractors.ita2025q1 import (
    extract_claims_ita2025q1,
)


def extract_claims(problem_id: str, solution: str) -> ClaimExtraction:
    if problem_id == "ITA2025Q1":
        return extract_claims_ita2025q1(solution)

    return ClaimExtraction(problem_id=problem_id, claims=[], formal_steps=[])
