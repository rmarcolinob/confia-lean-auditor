from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from confia_lean_auditor.core.schemas import ClaimExtraction, FormalStepResult


COMMON_HEADER_F2Q6 = r'''
import ConfiaLeanAuditor.Problems.ITA2025F2Q6.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025F2Q6

open ConfIA.LeanAuditor.ITA2025F2Q6

noncomputable section
'''


PROBABILITY_VALUES = r'''
theorem probability_values : ProbabilityValuesClaim := by
  unfold ProbabilityValuesClaim waysBeforeFourthHead denom
  norm_num
'''


RATIO_COMPARISON = r'''
theorem ratio_comparison : RatioComparisonClaim := by
  unfold RatioComparisonClaim ratioNumer ratioDenom
  constructor
  · intro n hn hlt
    omega
  · constructor
    · norm_num
    · intro n hgt
      omega
'''


CANDIDATE_MAXIMIZERS = r'''
theorem candidate_maximizers : CandidateMaximizersClaim := by
  unfold CandidateMaximizersClaim candidateN1 candidateN2
  norm_num
'''


FINAL_ANSWER = r'''
theorem final_answer : FinalAnswerClaim := by
  unfold FinalAnswerClaim
  exact candidate_maximizers
'''


COMMON_FOOTER_F2Q6 = r'''
end

end ConfIA.LeanAuditor.Generated.ITA2025F2Q6
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


def build_attempt_ita2025f2q6(
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    types = claim_types(claim_extraction)
    verified_steps = verified_step_types(formal_step_results)

    parts: List[str] = [COMMON_HEADER_F2Q6]
    generated_theorems: List[str] = []

    if (
        "probability_formula" in types
        and "f2q6_probability_values" in verified_steps
    ):
        parts.append(PROBABILITY_VALUES)
        generated_theorems.append("probability_values")

    if (
        "ratio_comparison" in types
        and "f2q6_ratio_comparison" in verified_steps
        and "probability_values" in generated_theorems
    ):
        parts.append(RATIO_COMPARISON)
        generated_theorems.append("ratio_comparison")

    if (
        "maximizers_identification" in types
        and "ratio_comparison" in generated_theorems
    ):
        parts.append(CANDIDATE_MAXIMIZERS)
        generated_theorems.append("candidate_maximizers")

    if (
        "final_answer" in types
        and "candidate_maximizers" in generated_theorems
    ):
        parts.append(FINAL_ANSWER)
        generated_theorems.append("final_answer")

    parts.append(COMMON_FOOTER_F2Q6)

    attempt_path = artifact_dir / "Attempt.lean"
    attempt_path.write_text("\n".join(parts), encoding="utf-8")

    return {
        "attempt_path": attempt_path,
        "generated_theorems": generated_theorems,
    }
