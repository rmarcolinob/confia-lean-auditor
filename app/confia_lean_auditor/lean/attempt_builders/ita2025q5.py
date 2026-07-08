from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from confia_lean_auditor.core.schemas import ClaimExtraction, FormalStepResult


COMMON_HEADER_Q5 = r'''
import ConfiaLeanAuditor.Problems.ITA2025Q5.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025Q5

open ConfIA.LeanAuditor.ITA2025Q5

noncomputable section
'''


DIFFERENCE_RELATION = r'''
theorem difference_relation : DifferenceRelationClaim := by
  unfold DifferenceRelationClaim
  intro b n
  ring
'''


GEOMETRIC_FORM_TEMPLATE = r'''
theorem geometric_form_template : GeometricFormTemplateClaim := by
  unfold GeometricFormTemplateClaim bGeom
  intro c q n
  rfl
'''


GEOMETRIC_FACTORIZATION = r'''
theorem geometric_factorization : GeometricFactorizationClaim := by
  unfold GeometricFactorizationClaim aFromGeom bGeom
  intro c q n
  rw [pow_succ]
  ring
'''


CONCLUSION_PG = r'''
theorem conclusion_pg : ConclusionPGClaim := by
  unfold ConclusionPGClaim
  intro c q
  use c * (q - 1)
  intro n
  calc
    aFromGeom c q n = c * (q - 1) * q ^ n := geometric_factorization c q n
    _ = (c * (q - 1)) * q ^ n := by ring
'''


COMMON_FOOTER_Q5 = r'''
end

end ConfIA.LeanAuditor.Generated.ITA2025Q5
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


def build_attempt_ita2025q5(
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    types = claim_types(claim_extraction)
    verified_steps = verified_step_types(formal_step_results)

    parts: List[str] = [COMMON_HEADER_Q5]
    generated_theorems: List[str] = []

    if "difference_relation" in types:
        parts.append(DIFFERENCE_RELATION)
        generated_theorems.append("difference_relation")

    if "geometric_form" in types:
        parts.append(GEOMETRIC_FORM_TEMPLATE)
        generated_theorems.append("geometric_form_template")

    if (
        "geometric_factorization" in types
        and "q5_geometric_factorization" in verified_steps
        and "difference_relation" in generated_theorems
        and "geometric_form_template" in generated_theorems
    ):
        parts.append(GEOMETRIC_FACTORIZATION)
        generated_theorems.append("geometric_factorization")

    if (
        "conclusion_pg" in types
        and "geometric_factorization" in generated_theorems
    ):
        parts.append(CONCLUSION_PG)
        generated_theorems.append("conclusion_pg")

    parts.append(COMMON_FOOTER_Q5)

    attempt_path = artifact_dir / "Attempt.lean"
    attempt_path.write_text("\n".join(parts), encoding="utf-8")

    return {
        "attempt_path": attempt_path,
        "generated_theorems": generated_theorems,
    }
