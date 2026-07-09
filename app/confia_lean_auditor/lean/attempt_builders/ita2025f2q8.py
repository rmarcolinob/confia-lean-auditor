from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from confia_lean_auditor.core.schemas import ClaimExtraction, FormalStepResult


COMMON_HEADER_F2Q8 = r'''
import ConfiaLeanAuditor.Problems.ITA2025F2Q8.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025F2Q8

open ConfIA.LeanAuditor.ITA2025F2Q8

noncomputable section
'''


BRIDGE_GENERIC = r'''
theorem generated_bridge_generic :
    ∀ n : ℕ,
      maxMatrix (n + 1) * colDiffMatrix (n + 1) =
        transformedShape (n + 1) := by
  intro n
  exact bridge_generic n
'''


COLDIFF_DET_ONE = r'''
theorem generated_coldiff_det_one :
    ∀ k : ℕ, Matrix.det (colDiffMatrix k) = 1 := by
  intro k
  exact det_colDiffMatrix_eq_one k
'''


DETERMINANT_FORMULA = r'''
theorem generated_determinant_formula : determinantFormulaClaim := by
  exact determinant_formula_claim
'''


FINAL_ANSWER = r'''
theorem generated_final_answer : finalAnswerClaim := by
  exact final_answer_claim
'''


STRONG_CLAIM = r'''
theorem generated_strong_claim : strongF2Q8Claim := by
  exact strong_f2q8_claim
'''


COMMON_FOOTER_F2Q8 = r'''
end

end ConfIA.LeanAuditor.Generated.ITA2025F2Q8
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


def build_attempt_ita2025f2q8(
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    types = claim_types(claim_extraction)
    verified_steps = verified_step_types(formal_step_results)

    parts: List[str] = [COMMON_HEADER_F2Q8]
    generated_theorems: List[str] = []

    if (
        "matrix_transformation" in types
        and "f2q8_bridge" in verified_steps
    ):
        parts.append(BRIDGE_GENERIC)
        generated_theorems.append("generated_bridge_generic")

    if (
        "matrix_transformation" in types
        and "f2q8_coldiff_det_one" in verified_steps
    ):
        parts.append(COLDIFF_DET_ONE)
        generated_theorems.append("generated_coldiff_det_one")

    if (
        "determinant_formula" in types
        and "f2q8_determinant_formula" in verified_steps
    ):
        parts.append(DETERMINANT_FORMULA)
        generated_theorems.append("generated_determinant_formula")

    if (
        "final_answer" in types
        and "f2q8_final_sum" in verified_steps
    ):
        parts.append(FINAL_ANSWER)
        generated_theorems.append("generated_final_answer")

    if (
        "generated_determinant_formula" in generated_theorems
        and "generated_final_answer" in generated_theorems
    ):
        parts.append(STRONG_CLAIM)
        generated_theorems.append("generated_strong_claim")

    parts.append(COMMON_FOOTER_F2Q8)

    attempt_path = artifact_dir / "Attempt.lean"
    attempt_path.write_text("\n".join(parts), encoding="utf-8")

    return {
        "attempt_path": attempt_path,
        "generated_theorems": generated_theorems,
    }
