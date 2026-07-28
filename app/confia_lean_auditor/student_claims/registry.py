from __future__ import annotations

from typing import List

from confia_lean_auditor.student_claims.schemas import StudentClaim
from confia_lean_auditor.student_claims.extract_f2q8_student_claims import (
    extract_f2q8_student_claims,
)
from confia_lean_auditor.student_claims.extract_f2q1_student_claims import (
    extract_f2q1_student_claims,
)
from confia_lean_auditor.student_claims.extract_f2q5_student_claims import (
    extract_f2q5_student_claims,
)
from confia_lean_auditor.student_claims.extract_f2q3_student_claims import (
    extract_f2q3_student_claims,
)


def extract_student_claims(problem_id: str, solution: str) -> List[StudentClaim]:
    """Dispatch student-claim extraction by problem.

    This is the public entry point used by /audit.

    Each problem may register a specific extractor. Problems without a
    dynamic student-claim extractor return an empty list, preserving the
    old behavior.
    """
    if problem_id == "ITA2025F2Q8":
        return extract_f2q8_student_claims(solution)

    if problem_id == "ITA2025F2Q1":
        return extract_f2q1_student_claims(solution)

    if problem_id == "ITA2025F2Q5":
        return extract_f2q5_student_claims(solution)

    if problem_id == "ITA2025F2Q3":
        return extract_f2q3_student_claims(solution)

    return []
