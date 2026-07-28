from __future__ import annotations

from typing import List

from confia_lean_auditor.student_claims.schemas import StudentClaim, StudentClaimCheck
from confia_lean_auditor.lean.student_claim_checker import (
    check_student_claims as check_f2q8_student_claims_legacy,
)
from confia_lean_auditor.lean.student_claim_checkers.ita2025f2q1 import (
    check_f2q1_student_claims,
)
from confia_lean_auditor.lean.student_claim_checkers.ita2025f2q5 import (
    check_f2q5_student_claims,
)


try:
    from confia_lean_auditor.lean.student_claim_checkers.ita2025f2q6 import (
        check_f2q6_student_claims,
    )
except ModuleNotFoundError:
    check_f2q6_student_claims = None  # type: ignore[assignment]


def check_student_claims_for_problem(
    problem_id: str,
    student_claims: List[StudentClaim],
    run_id: str,
) -> List[StudentClaimCheck]:
    """Dispatch dynamic Lean checks for concrete student claims."""
    if not student_claims:
        return []

    if problem_id == "ITA2025F2Q8":
        return check_f2q8_student_claims_legacy(
            student_claims,
            run_id=run_id,
        )

    if problem_id == "ITA2025F2Q1":
        return check_f2q1_student_claims(
            student_claims,
            run_id=run_id,
        )

    if problem_id == "ITA2025F2Q5":
        return check_f2q5_student_claims(
            student_claims,
            run_id=run_id,
        )

    if problem_id == "ITA2025F2Q6" and check_f2q6_student_claims is not None:
        return check_f2q6_student_claims(
            student_claims,
            run_id=run_id,
        )

    return []
