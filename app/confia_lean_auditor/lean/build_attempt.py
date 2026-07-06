from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from confia_lean_auditor.core.schemas import ClaimExtraction, FormalStepResult


COMMON_HEADER_Q1 = r'''
import ConfiaLeanAuditor.Problems.ITA2025Q1.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025Q1

open ConfIA.LeanAuditor.ITA2025Q1

noncomputable section

private theorem triangleArea_formula_helper (a : ℝ) :
    triangleArea a = a ^ 2 - 2 * a + 5 := by
  unfold triangleArea signedDoubleArea
  have hdet :
      (a - 1) * (4 * a) - 2 * ((a ^ 2 - 4) - 1)
        = 2 * (a ^ 2 - 2 * a + 5) := by
    ring
  rw [hdet]
  have hnonneg : 0 ≤ 2 * (a ^ 2 - 2 * a + 5) := by
    have hrewrite : a ^ 2 - 2 * a + 5 = (a - 1) ^ 2 + 4 := by
      ring
    have hsq : 0 ≤ (a - 1) ^ 2 := sq_nonneg (a - 1)
    nlinarith
  rw [abs_of_nonneg hnonneg]
  ring
'''


Z_SQUARED_COORDINATES = r'''
theorem z_squared_coordinates : ZSquaredCoordinatesClaim := by
  unfold ZSquaredCoordinatesClaim
  intro a
  constructor <;> ring
'''


TRIANGLE_AREA_FORMULA = r'''
theorem triangleArea_formula : TriangleAreaFormulaClaim := by
  unfold TriangleAreaFormulaClaim
  intro a
  exact triangleArea_formula_helper a
'''


ANSWER_UNIQUE = r'''
theorem answer_unique : AnswerUniqueClaim := by
  unfold AnswerUniqueClaim
  intro a ha harea
  rw [triangleArea_formula_helper] at harea
  have hquad : (a - 15) * (a + 13) = 0 := by
    nlinarith
  have hcases := mul_eq_zero.mp hquad
  cases hcases with
  | inl h =>
      nlinarith
  | inr h =>
      have hneg : a = -13 := by
        nlinarith
      nlinarith
'''


ANSWER_CHECK = r'''
theorem answer_check : AnswerCheckClaim := by
  unfold AnswerCheckClaim
  rw [triangleArea_formula_helper]
  norm_num
'''


COMMON_FOOTER_Q1 = r'''
end

end ConfIA.LeanAuditor.Generated.ITA2025Q1
'''


def claim_types(claim_extraction: ClaimExtraction) -> Set[str]:
    return set(claim.type for claim in claim_extraction.claims)


def verified_step_types(formal_step_results: Optional[List[FormalStepResult]]) -> Set[str]:
    if formal_step_results is None:
        return set()

    return {
        step.type for step in formal_step_results if step.status == "verified"
    }


def build_attempt_ita2025q1(
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    types = claim_types(claim_extraction)
    verified_steps = verified_step_types(formal_step_results)

    parts: List[str] = [COMMON_HEADER_Q1]
    generated_theorems: List[str] = []

    if "z_squared_coordinates" in types:
        parts.append(Z_SQUARED_COORDINATES)
        generated_theorems.append("z_squared_coordinates")

    if "area_formula" in types and "determinant_expansion" in verified_steps:
        parts.append(TRIANGLE_AREA_FORMULA)
        generated_theorems.append("triangleArea_formula")

    if (
        "determinant_expansion" in verified_steps
        and "area_equation" in types
        and "positive_root_selection" in types
    ):
        parts.append(ANSWER_UNIQUE)
        generated_theorems.append("answer_unique")

    if "final_answer" in types:
        parts.append(ANSWER_CHECK)
        generated_theorems.append("answer_check")

    parts.append(COMMON_FOOTER_Q1)

    attempt_path = artifact_dir / "Attempt.lean"
    attempt_path.write_text("\n".join(parts), encoding="utf-8")

    return {
        "attempt_path": attempt_path,
        "generated_theorems": generated_theorems,
    }


def build_attempt(
    repo_root: Path,
    problem_id: str,
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    if problem_id == "ITA2025Q1":
        return build_attempt_ita2025q1(
            claim_extraction=claim_extraction,
            artifact_dir=artifact_dir,
            formal_step_results=formal_step_results,
        )

    raise NotImplementedError("Attempt builder not implemented for problem: " + problem_id)
