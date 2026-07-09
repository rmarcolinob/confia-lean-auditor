from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from confia_lean_auditor.core.schemas import ClaimExtraction, FormalStepResult


COMMON_HEADER_F2Q1 = r'''
import ConfiaLeanAuditor.Problems.ITA2025F2Q1.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025F2Q1

open ConfIA.LeanAuditor.ITA2025F2Q1

noncomputable section
'''


POWER_REDUCTIONS = r'''
theorem power_reductions : PowerReductionsClaim := by
  unfold PowerReductionsClaim
  norm_num [powRem]
'''


REDUCED_POLYNOMIAL_FORM = r'''
theorem reduced_polynomial_form : ReducedPolynomialFormClaim := by
  unfold ReducedPolynomialFormClaim
  intro a b
  unfold remainderConst remainderXCoeff
  constructor
  · norm_num [powRem]
  · norm_num [powRem]
'''


COEFFICIENT_SYSTEM_SOLUTION = r'''
theorem coefficient_system_solution : CoefficientSystemSolutionClaim := by
  unfold CoefficientSystemSolutionClaim candidateA candidateB
  norm_num

theorem target_remainder : TargetRemainderClaim := by
  unfold TargetRemainderClaim remainderXCoeff remainderConst candidateA candidateB
  norm_num [powRem]
'''


FINAL_ANSWER = r'''
theorem final_answer : FinalAnswerClaim := by
  unfold FinalAnswerClaim candidateA candidateB
  norm_num
'''


COMMON_FOOTER_F2Q1 = r'''
end

end ConfIA.LeanAuditor.Generated.ITA2025F2Q1
'''


def claim_types(claim_extraction: ClaimExtraction) -> Set[str]:
    return {claim.type for claim in claim_extraction.claims}


def verified_step_types(
    formal_step_results: Optional[List[FormalStepResult]],
) -> Set[str]:
    if formal_step_results is None:
        return set()

    return {
        step.type
        for step in formal_step_results
        if step.status == "verified"
    }


def build_attempt_ita2025f2q1(
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    types = claim_types(claim_extraction)
    verified_steps = verified_step_types(formal_step_results)

    parts: List[str] = [COMMON_HEADER_F2Q1]
    generated_theorems: List[str] = []

    if (
        "power_reductions" in types
        and "f2q1_power_reductions" in verified_steps
    ):
        parts.append(POWER_REDUCTIONS)
        generated_theorems.append("power_reductions")

    if (
        "reduced_polynomial_form" in types
        and "f2q1_reduced_form" in verified_steps
        and "power_reductions" in generated_theorems
    ):
        parts.append(REDUCED_POLYNOMIAL_FORM)
        generated_theorems.append("reduced_polynomial_form")

    if (
        "coefficient_system" in types
        and "f2q1_coefficient_solution" in verified_steps
        and "reduced_polynomial_form" in generated_theorems
    ):
        parts.append(COEFFICIENT_SYSTEM_SOLUTION)
        generated_theorems.append("coefficient_system_solution")
        generated_theorems.append("target_remainder")

    if (
        "final_answer" in types
        and "coefficient_system_solution" in generated_theorems
    ):
        parts.append(FINAL_ANSWER)
        generated_theorems.append("final_answer")

    parts.append(COMMON_FOOTER_F2Q1)

    attempt_path = artifact_dir / "Attempt.lean"
    attempt_path.write_text("\n".join(parts), encoding="utf-8")

    return {
        "attempt_path": attempt_path,
        "generated_theorems": generated_theorems,
    }
