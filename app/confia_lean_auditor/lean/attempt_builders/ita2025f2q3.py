from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from confia_lean_auditor.core.schemas import ClaimExtraction, FormalStepResult


COMMON_HEADER_F2Q3 = r'''
import ConfiaLeanAuditor.Problems.ITA2025F2Q3.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025F2Q3

open ConfIA.LeanAuditor.ITA2025F2Q3

noncomputable section
'''


BETA_DIFFERENCE = r'''
theorem generated_beta_difference : BetaDifferenceClaim := by
  exact beta_difference_claim
'''


EQUATIONS = r'''
theorem generated_equations : FirstEquationClaim ∧ SecondEquationClaim := by
  exact ⟨first_equation_claim, second_equation_claim⟩
'''


UNIT_CIRCLE = r'''
theorem generated_unit_circle : CandidateUnitCircleClaim := by
  exact candidate_unit_circle_claim
'''


FINAL_SIN_SUM = r'''
theorem generated_final_sin_sum : FinalSinSumClaim := by
  exact final_sin_sum_claim
'''


FINAL_ANSWER = r'''
theorem generated_final_answer : FinalAnswerClaim := by
  exact final_answer_claim
'''


STRONG_F2Q3_CLAIM = r'''
theorem generated_strong_f2q3_claim : StrongF2Q3Claim := by
  exact strong_f2q3_claim
'''


COMMON_FOOTER_F2Q3 = r'''
end

end ConfIA.LeanAuditor.Generated.ITA2025F2Q3
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


def build_attempt_ita2025f2q3(
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    types = claim_types(claim_extraction)
    verified_steps = verified_step_types(formal_step_results)

    parts: List[str] = [COMMON_HEADER_F2Q3]
    generated_theorems: List[str] = []

    if "beta_difference" in types and "f2q3_beta_difference" in verified_steps:
        parts.append(BETA_DIFFERENCE)
        generated_theorems.append("generated_beta_difference")

    if "candidate_values" in types and "f2q3_equations" in verified_steps:
        parts.append(EQUATIONS)
        generated_theorems.append("generated_equations")

    if "candidate_values" in types and "f2q3_unit_circle" in verified_steps:
        parts.append(UNIT_CIRCLE)
        generated_theorems.append("generated_unit_circle")

    if "final_sin_sum" in types and "f2q3_final_sin_sum" in verified_steps:
        parts.append(FINAL_SIN_SUM)
        generated_theorems.append("generated_final_sin_sum")

    if "final_answer" in types and "f2q3_final_answer" in verified_steps:
        parts.append(FINAL_ANSWER)
        generated_theorems.append("generated_final_answer")

    if (
        "generated_beta_difference" in generated_theorems
        and "generated_equations" in generated_theorems
        and "generated_unit_circle" in generated_theorems
        and "generated_final_sin_sum" in generated_theorems
        and "generated_final_answer" in generated_theorems
    ):
        parts.append(STRONG_F2Q3_CLAIM)
        generated_theorems.append("generated_strong_f2q3_claim")

    parts.append(COMMON_FOOTER_F2Q3)

    attempt_path = artifact_dir / "Attempt.lean"
    attempt_path.write_text("\n".join(parts), encoding="utf-8")

    return {
        "attempt_path": attempt_path,
        "generated_theorems": generated_theorems,
    }
