from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from confia_lean_auditor.core.schemas import ClaimExtraction, FormalStepResult


COMMON_HEADER_Q8 = r'''
import ConfiaLeanAuditor.Problems.ITA2025Q8.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025Q8

open Real
open ConfIA.LeanAuditor.ITA2025Q8

noncomputable section
'''


NUMERATOR_FACTORIZATION = r'''
theorem numerator_factorization : NumeratorFactorizationClaim := by
  unfold NumeratorFactorizationClaim numerator factoredNumerator
  intro x
  rw [sin_two_mul]
  ring
'''


ENDPOINT_SUM = r'''
theorem endpoint_sum : EndpointSumClaim := by
  unfold EndpointSumClaim CandidateA CandidateB
  ring
'''


CANDIDATE_LENGTH = r'''
theorem candidate_length : CandidateLengthClaim := by
  unfold CandidateLengthClaim CandidateA CandidateB
  ring
'''


COMMON_FOOTER_Q8 = r'''
end

end ConfIA.LeanAuditor.Generated.ITA2025Q8
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


def build_attempt_ita2025q8(
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    types = claim_types(claim_extraction)
    verified_steps = verified_step_types(formal_step_results)

    parts: List[str] = [COMMON_HEADER_Q8]
    generated_theorems: List[str] = []

    if (
        "numerator_factorization" in types
        and "q8_numerator_factorization" in verified_steps
    ):
        parts.append(NUMERATOR_FACTORIZATION)
        generated_theorems.append("numerator_factorization")

    if (
        "endpoint_sum" in types
        and "q8_endpoint_sum" in verified_steps
    ):
        parts.append(ENDPOINT_SUM)
        parts.append(CANDIDATE_LENGTH)
        generated_theorems.append("endpoint_sum")
        generated_theorems.append("candidate_length")

    parts.append(COMMON_FOOTER_Q8)

    attempt_path = artifact_dir / "Attempt.lean"
    attempt_path.write_text("\n".join(parts), encoding="utf-8")

    return {
        "attempt_path": attempt_path,
        "generated_theorems": generated_theorems,
    }
