from __future__ import annotations

from confia_lean_auditor.core.schemas import ClaimExtraction
from confia_lean_auditor.claims.extractors.ita2025q1 import (
    extract_claims_ita2025q1,
)
from confia_lean_auditor.claims.extractors.ita2025q3 import (
    extract_claims_ita2025q3,
)
from confia_lean_auditor.claims.extractors.ita2025q4 import (
    extract_claims_ita2025q4,
)


def extract_claims(problem_id: str, solution: str) -> ClaimExtraction:
    if problem_id == "ITA2025Q1":
        return extract_claims_ita2025q1(solution)

    if problem_id == "ITA2025Q3":
        return extract_claims_ita2025q3(solution)

    if problem_id == "ITA2025Q4":
        return extract_claims_ita2025q4(solution)

    return ClaimExtraction(problem_id=problem_id, claims=[], formal_steps=[])
