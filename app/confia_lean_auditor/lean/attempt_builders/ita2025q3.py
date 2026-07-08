from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from confia_lean_auditor.core.schemas import ClaimExtraction, FormalStepResult


COMMON_HEADER_Q3 = r'''
import ConfiaLeanAuditor.Problems.ITA2025Q3.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025Q3

open ConfIA.LeanAuditor.ITA2025Q3

noncomputable section
'''


FIRST_FACTOR_EXPONENT = r'''
theorem first_factor_exponent_form : FirstFactorExponentClaim := by
  unfold FirstFactorExponentClaim firstExponent
  intro i
  use 3 - i
  ring
'''


SECOND_FACTOR_EXPONENT = r'''
theorem second_factor_exponent_form : SecondFactorExponentClaim := by
  unfold SecondFactorExponentClaim secondExponent
  intro j
  use 2 - j
  ring
'''


NO_CONSTANT_EXPONENT = r'''
theorem no_constant_exponent : NoConstantExponentClaim := by
  unfold NoConstantExponentClaim productExponent firstExponent secondExponent
  intro i j h
  omega
'''


PRODUCT_EXPONENT_ODD = r'''
theorem product_exponent_odd : ProductExponentOddClaim := by
  unfold ProductExponentOddClaim productExponent firstExponent secondExponent
  intro i j
  use 5 - i - j
  ring
'''


FINAL_ANSWER_ZERO = r'''
theorem final_answer_zero : FinalAnswerZeroClaim := by
  unfold FinalAnswerZeroClaim
  exact no_constant_exponent
'''


COMMON_FOOTER_Q3 = r'''
end

end ConfIA.LeanAuditor.Generated.ITA2025Q3
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


def build_attempt_ita2025q3(
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    types = claim_types(claim_extraction)
    verified_steps = verified_step_types(formal_step_results)

    parts: List[str] = [COMMON_HEADER_Q3]
    generated_theorems: List[str] = []

    if "first_factor_exponent_form" in types:
        parts.append(FIRST_FACTOR_EXPONENT)
        generated_theorems.append("first_factor_exponent_form")

    if "second_factor_exponent_form" in types:
        parts.append(SECOND_FACTOR_EXPONENT)
        generated_theorems.append("second_factor_exponent_form")

    if "exponent_balance" in types and "q3_no_zero_exponent" in verified_steps:
        parts.append(NO_CONSTANT_EXPONENT)
        generated_theorems.append("no_constant_exponent")

    if "parity_obstruction" in types and "q3_no_zero_exponent" in verified_steps:
        parts.append(PRODUCT_EXPONENT_ODD)
        generated_theorems.append("product_exponent_odd")

    if (
        "final_answer_zero" in types
        and "parity_obstruction" in types
        and "q3_no_zero_exponent" in verified_steps
    ):
        parts.append(FINAL_ANSWER_ZERO)
        generated_theorems.append("final_answer_zero")

    parts.append(COMMON_FOOTER_Q3)

    attempt_path = artifact_dir / "Attempt.lean"
    attempt_path.write_text("\n".join(parts), encoding="utf-8")

    return {
        "attempt_path": attempt_path,
        "generated_theorems": generated_theorems,
    }
