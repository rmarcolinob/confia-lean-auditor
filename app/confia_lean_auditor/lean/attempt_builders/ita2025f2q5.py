from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from confia_lean_auditor.core.schemas import ClaimExtraction, FormalStepResult


COMMON_HEADER_F2Q5 = r'''
import ConfiaLeanAuditor.Problems.ITA2025F2Q5.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025F2Q5

open ConfIA.LeanAuditor.ITA2025F2Q5

noncomputable section
'''


LOG_POWER_DECOMPOSITION = r'''
theorem log_power_decomposition : LogPowerDecompositionClaim := by
  unfold LogPowerDecompositionClaim totalLogScaled integerPartScaled mantissaScaled log3Scaled scale
  norm_num
'''


DIGIT_LOG_BOUNDS = r'''
theorem digit_log_bounds : DigitLogBoundsClaim := by
  unfold DigitLogBoundsClaim log5Scaled log6Scaled log2Scaled log3Scaled scale
  norm_num
'''


MANTISSA_BETWEEN_BOUNDS = r'''
theorem mantissa_between_bounds : MantissaBetweenBoundsClaim := by
  unfold MantissaBetweenBoundsClaim log5Scaled log6Scaled mantissaScaled log2Scaled log3Scaled scale
  norm_num
'''


FINAL_DIGIT_FIVE = r'''
theorem final_digit_five : FinalDigitFiveClaim := by
  unfold FinalDigitFiveClaim
  exact ⟨digit_log_bounds, mantissa_between_bounds⟩
'''


COMMON_FOOTER_F2Q5 = r'''
end

end ConfIA.LeanAuditor.Generated.ITA2025F2Q5
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


def build_attempt_ita2025f2q5(
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    types = claim_types(claim_extraction)
    verified_steps = verified_step_types(formal_step_results)

    parts: List[str] = [COMMON_HEADER_F2Q5]
    generated_theorems: List[str] = []

    if (
        "log_power_decomposition" in types
        and "f2q5_log_power_decomposition" in verified_steps
    ):
        parts.append(LOG_POWER_DECOMPOSITION)
        generated_theorems.append("log_power_decomposition")

    if (
        "digit_log_bounds" in types
        and "f2q5_digit_bounds" in verified_steps
    ):
        parts.append(DIGIT_LOG_BOUNDS)
        generated_theorems.append("digit_log_bounds")

    if (
        "mantissa_between_bounds" in types
        and "f2q5_digit_bounds" in verified_steps
        and "mantissa_identification" in types
        and "log_power_decomposition" in generated_theorems
        and "digit_log_bounds" in generated_theorems
    ):
        parts.append(MANTISSA_BETWEEN_BOUNDS)
        generated_theorems.append("mantissa_between_bounds")

    if (
        "final_digit_five" in types
        and "digit_log_bounds" in generated_theorems
        and "mantissa_between_bounds" in generated_theorems
    ):
        parts.append(FINAL_DIGIT_FIVE)
        generated_theorems.append("final_digit_five")

    parts.append(COMMON_FOOTER_F2Q5)

    attempt_path = artifact_dir / "Attempt.lean"
    attempt_path.write_text("\n".join(parts), encoding="utf-8")

    return {
        "attempt_path": attempt_path,
        "generated_theorems": generated_theorems,
    }
