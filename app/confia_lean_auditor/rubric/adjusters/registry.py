from __future__ import annotations

from typing import Any, Callable, Dict, List

from confia_lean_auditor.core.schemas import RubricAssessment
from confia_lean_auditor.rubric.adjusters.ita2025f2q8 import (
    apply_f2q8_student_claim_adjustments,
)
from confia_lean_auditor.rubric.adjusters.ita2025f2q1 import (
    apply_f2q1_student_claim_adjustments,
)
from confia_lean_auditor.rubric.adjusters.ita2025f2q5 import (
    apply_f2q5_student_claim_adjustments,
)
from confia_lean_auditor.rubric.adjusters.ita2025f2q3 import (
    apply_f2q3_student_claim_adjustments,
)


RubricAdjuster = Callable[[RubricAssessment, List[Any]], RubricAssessment]


ADJUSTERS: Dict[str, RubricAdjuster] = {
    "ITA2025F2Q3": apply_f2q3_student_claim_adjustments,
    "ITA2025F2Q5": apply_f2q5_student_claim_adjustments,
    "ITA2025F2Q8": apply_f2q8_student_claim_adjustments,
    "ITA2025F2Q1": apply_f2q1_student_claim_adjustments,
}


def apply_student_claim_adjustments(
    rubric: RubricAssessment,
    problem_id: str,
    student_claim_checks: List[Any],
) -> RubricAssessment:
    """Dispatch rubric adjustments by problem.

    Problems without a registered student-claim adjuster preserve the
    previous rubric behavior.
    """
    adjuster = ADJUSTERS.get(problem_id)
    if adjuster is None:
        return rubric

    return adjuster(rubric, student_claim_checks)
