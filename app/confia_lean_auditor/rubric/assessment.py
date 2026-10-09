"""Only decided criteria enter the subtotal; pending criteria have no grade."""
from confia_lean_auditor.core.schemas import RubricAssessment


def refresh_assessment(rubric: RubricAssessment) -> RubricAssessment:
    evaluated = [item for item in rubric.items if item.points is not None]
    rubric.evaluated_score = sum(item.points for item in evaluated)
    rubric.evaluated_max_score = sum(item.max_points for item in evaluated)
    complete = len(evaluated) == len(rubric.items)
    rubric.assessment_status = "complete" if complete else "partial" if evaluated else "indeterminate"
    rubric.score = rubric.evaluated_score if complete else None
    return rubric
