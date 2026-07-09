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


from confia_lean_auditor.claims.extractors.ita2025q5 import (
    extract_claims_ita2025q5,
)

from confia_lean_auditor.claims.extractors.ita2025q8 import (
    extract_claims_ita2025q8,
)

from confia_lean_auditor.claims.extractors.ita2025f2q5 import (
    extract_claims_ita2025f2q5,
)

from confia_lean_auditor.claims.extractors.ita2025f2q1 import (
    extract_claims_ita2025f2q1,
)

from confia_lean_auditor.claims.extractors.ita2025f2q6 import (
    extract_claims_ita2025f2q6,
)

def extract_claims(problem_id: str, solution: str) -> ClaimExtraction:
    if problem_id == "ITA2025Q1":
        return extract_claims_ita2025q1(solution)

    if problem_id == "ITA2025Q3":
        return extract_claims_ita2025q3(solution)

    if problem_id == "ITA2025Q4":
        return extract_claims_ita2025q4(solution)

    if problem_id == "ITA2025Q5":
        return extract_claims_ita2025q5(solution)

    if problem_id == "ITA2025Q8":
        return extract_claims_ita2025q8(solution)

    if problem_id == "ITA2025F2Q1":
        return extract_claims_ita2025f2q1(solution)

    if problem_id == "ITA2025F2Q6":
        return extract_claims_ita2025f2q6(solution)

    if problem_id == "ITA2025F2Q5":
        return extract_claims_ita2025f2q5(solution)




    return ClaimExtraction(problem_id=problem_id, claims=[], formal_steps=[])
