from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from confia_lean_auditor.core.schemas import ClaimExtraction, FormalStepResult


COMMON_HEADER_Q4 = r'''
import ConfiaLeanAuditor.Problems.ITA2025Q4.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025Q4

open ConfIA.LeanAuditor.ITA2025Q4

noncomputable section
'''


POSITIVE_WITNESSES = r'''
theorem positive_witnesses : PositiveWitnessesClaim := by
  unfold PositiveWitnessesClaim witnessX1 witnessX2
  constructor <;> norm_num
'''


SAME_F_ARGUMENT = r'''
theorem same_f_argument : SameArgumentWitnessClaim := by
  unfold SameArgumentWitnessClaim phi witnessX1 witnessX2
  norm_num
'''


DISTINCT_G_INPUTS = r'''
theorem distinct_g_inputs : DistinctGInputsClaim := by
  unfold DistinctGInputsClaim witnessX1 witnessX2
  norm_num
'''


EQUAL_G_VALUES = r'''
theorem equal_g_values : EqualGValuesClaim := by
  unfold EqualGValuesClaim FunctionalHypothesis
  intro f g h
  have hpos1 : 0 < witnessX1 := by
    unfold witnessX1
    norm_num
  have hpos2 : 0 < witnessX2 := by
    unfold witnessX2
    norm_num
  have h1 := h witnessX1 hpos1
  have h2 := h witnessX2 hpos2
  have harg : phi witnessX1 = phi witnessX2 := by
    unfold phi witnessX1 witnessX2
    norm_num
  calc
    g (witnessX1 ^ 2) = f (phi witnessX1) := h1
    _ = f (phi witnessX2) := by rw [harg]
    _ = g (witnessX2 ^ 2) := h2.symm
'''


G_NOT_INJECTIVE = r'''
theorem g_not_injective : GNotInjectiveClaim := by
  unfold GNotInjectiveClaim
  intro f g h hg
  have heq : g (witnessX1 ^ 2) = g (witnessX2 ^ 2) := by
    exact equal_g_values f g h
  have hneq : witnessX1 ^ 2 ≠ witnessX2 ^ 2 := by
    unfold witnessX1 witnessX2
    norm_num
  exact hneq (hg heq)
'''


COMMON_FOOTER_Q4 = r'''
end

end ConfIA.LeanAuditor.Generated.ITA2025Q4
'''


def claim_types(claim_extraction: ClaimExtraction) -> Set[str]:
    return set(claim.type for claim in claim_extraction.claims)


def verified_step_types(formal_step_results: Optional[List[FormalStepResult]]) -> Set[str]:
    if formal_step_results is None:
        return set()

    return {
        step.type for step in formal_step_results if step.status == "verified"
    }


def build_attempt_ita2025q4(
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    types = claim_types(claim_extraction)
    verified_steps = verified_step_types(formal_step_results)

    parts: List[str] = [COMMON_HEADER_Q4]
    generated_theorems: List[str] = []

    if "positive_witnesses" in types:
        parts.append(POSITIVE_WITNESSES)
        generated_theorems.append("positive_witnesses")

    if "same_f_argument" in types and "q4_same_f_argument" in verified_steps:
        parts.append(SAME_F_ARGUMENT)
        generated_theorems.append("same_f_argument")

    if "distinct_g_inputs" in types and "q4_distinct_g_inputs" in verified_steps:
        parts.append(DISTINCT_G_INPUTS)
        generated_theorems.append("distinct_g_inputs")

    if (
        "positive_witnesses" in types
        and "same_f_argument" in types
        and "distinct_g_inputs" in types
        and "equal_g_values" in types
        and "q4_same_f_argument" in verified_steps
        and "q4_distinct_g_inputs" in verified_steps
    ):
        parts.append(EQUAL_G_VALUES)
        generated_theorems.append("equal_g_values")

    if (
        "equal_g_values" in types
        and "distinct_g_inputs" in types
        and "not_injective_conclusion" in types
        and "q4_same_f_argument" in verified_steps
        and "q4_distinct_g_inputs" in verified_steps
    ):
        parts.append(G_NOT_INJECTIVE)
        generated_theorems.append("g_not_injective")

    parts.append(COMMON_FOOTER_Q4)

    attempt_path = artifact_dir / "Attempt.lean"
    attempt_path.write_text("\n".join(parts), encoding="utf-8")

    return {
        "attempt_path": attempt_path,
        "generated_theorems": generated_theorems,
    }
