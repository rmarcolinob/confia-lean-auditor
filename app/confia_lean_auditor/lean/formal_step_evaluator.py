from __future__ import annotations

from pathlib import Path
from typing import List

from confia_lean_auditor.core.schemas import (
    ClaimExtraction,
    FormalStep,
    FormalStepResult,
)
from confia_lean_auditor.lean.run_lean import run_lean_file
from confia_lean_auditor.lean.safe_formal_step import (
    FormalStepValidationError,
    validate_formal_step,
)


def lean_theorem_name(step_id: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in step_id)
    return "student_" + safe


def render_q1_formal_step(step: FormalStep) -> str:
    theorem_name = lean_theorem_name(step.id)

    return f'''
import ConfiaLeanAuditor.Problems.ITA2025Q1.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025Q1.Step

open ConfIA.LeanAuditor.ITA2025Q1

noncomputable section

theorem {theorem_name} (a : ℝ) :
    {step.lhs}
      = {step.rhs} := by
  {step.lean_method}

end

end ConfIA.LeanAuditor.Generated.ITA2025Q1.Step
'''


def render_q4_formal_step(step: FormalStep) -> str:
    theorem_name = lean_theorem_name(step.id)

    if step.type == "q4_distinct_g_inputs":
        relation = "≠"
    else:
        relation = "="

    return f'''
import ConfiaLeanAuditor.Problems.ITA2025Q4.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025Q4.Step

open ConfIA.LeanAuditor.ITA2025Q4

noncomputable section

theorem {theorem_name} :
    ({step.lhs} : ℝ)
      {relation} ({step.rhs} : ℝ) := by
  {step.lean_method}

end

end ConfIA.LeanAuditor.Generated.ITA2025Q4.Step
'''



def render_q3_formal_step(step: FormalStep) -> str:
    theorem_name = lean_theorem_name(step.id)

    return f"""
import ConfiaLeanAuditor.Problems.ITA2025Q3.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025Q3.Step

open ConfIA.LeanAuditor.ITA2025Q3

noncomputable section

theorem {theorem_name} (i j : ℤ) :
    {step.lhs}
      ≠ {step.rhs} := by
  {step.lean_method}

end

end ConfIA.LeanAuditor.Generated.ITA2025Q3.Step
"""



def render_q5_formal_step(step: FormalStep) -> str:
    theorem_name = lean_theorem_name(step.id)

    if step.type != "q5_geometric_factorization":
        raise NotImplementedError(f"Unsupported ITA2025Q5 formal step type: {step.type}")

    return f"""
import ConfiaLeanAuditor.Problems.ITA2025Q5.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025Q5.Step

open ConfIA.LeanAuditor.ITA2025Q5

noncomputable section

theorem {theorem_name} (c q : ℝ) (n : ℕ) :
    {step.lhs}
      = {step.rhs} := by
  rw [pow_succ]
  {step.lean_method}

end

end ConfIA.LeanAuditor.Generated.ITA2025Q5.Step
"""



def render_q8_formal_step(step: FormalStep) -> str:
    theorem_name = lean_theorem_name(step.id)

    if step.type == "q8_numerator_factorization":
        theorem_body = f"""
theorem {theorem_name} : NumeratorFactorizationClaim := by
  unfold NumeratorFactorizationClaim numerator factoredNumerator
  intro x
  rw [sin_two_mul]
  ring
"""

    elif step.type == "q8_endpoint_sum":
        theorem_body = f"""
theorem {theorem_name} : EndpointSumClaim := by
  unfold EndpointSumClaim CandidateA CandidateB
  ring
"""

    else:
        raise NotImplementedError(f"Unsupported ITA2025Q8 formal step type: {step.type}")

    return f"""
import ConfiaLeanAuditor.Problems.ITA2025Q8.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025Q8.Step

open Real
open ConfIA.LeanAuditor.ITA2025Q8

noncomputable section

{theorem_body}

end

end ConfIA.LeanAuditor.Generated.ITA2025Q8.Step
"""



def render_f2q5_formal_step(step: FormalStep) -> str:
    theorem_name = lean_theorem_name(step.id)

    if step.type == "f2q5_log_power_decomposition":
        theorem_body = f"""
theorem {theorem_name} : LogPowerDecompositionClaim := by
  unfold LogPowerDecompositionClaim totalLogScaled integerPartScaled mantissaScaled log3Scaled scale
  norm_num
"""

    elif step.type == "f2q5_digit_bounds":
        theorem_body = f"""
theorem {theorem_name} : DigitLogBoundsClaim ∧ MantissaBetweenBoundsClaim := by
  constructor
  · unfold DigitLogBoundsClaim log5Scaled log6Scaled log2Scaled log3Scaled scale
    norm_num
  · unfold MantissaBetweenBoundsClaim log5Scaled log6Scaled mantissaScaled log2Scaled log3Scaled scale
    norm_num
"""

    else:
        raise NotImplementedError(f"Unsupported ITA2025F2Q5 formal step type: {step.type}")

    return f"""
import ConfiaLeanAuditor.Problems.ITA2025F2Q5.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025F2Q5.Step

open ConfIA.LeanAuditor.ITA2025F2Q5

noncomputable section

{theorem_body}

end

end ConfIA.LeanAuditor.Generated.ITA2025F2Q5.Step
"""



def render_f2q1_formal_step(step: FormalStep) -> str:
    theorem_name = lean_theorem_name(step.id)

    if step.type == "f2q1_power_reductions":
        theorem_body = f"""
theorem {theorem_name} : PowerReductionsClaim := by
  unfold PowerReductionsClaim
  norm_num [powRem]
"""

    elif step.type == "f2q1_reduced_form":
        theorem_body = f"""
theorem {theorem_name} : ReducedPolynomialFormClaim := by
  unfold ReducedPolynomialFormClaim
  intro a b
  unfold remainderConst remainderXCoeff
  constructor
  · norm_num [powRem]
  · norm_num [powRem]
"""

    elif step.type == "f2q1_coefficient_solution":
        theorem_body = f"""
theorem {theorem_name} : CoefficientSystemSolutionClaim ∧ TargetRemainderClaim ∧ FinalAnswerClaim := by
  constructor
  · unfold CoefficientSystemSolutionClaim candidateA candidateB
    norm_num
  · constructor
    · unfold TargetRemainderClaim remainderXCoeff remainderConst candidateA candidateB
      norm_num [powRem]
    · unfold FinalAnswerClaim candidateA candidateB
      norm_num
"""

    else:
        raise NotImplementedError(f"Unsupported ITA2025F2Q1 formal step type: {step.type}")

    return f"""
import ConfiaLeanAuditor.Problems.ITA2025F2Q1.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025F2Q1.Step

open ConfIA.LeanAuditor.ITA2025F2Q1

noncomputable section

{theorem_body}

end

end ConfIA.LeanAuditor.Generated.ITA2025F2Q1.Step
"""



def render_f2q6_formal_step(step: FormalStep) -> str:
    theorem_name = lean_theorem_name(step.id)

    if step.type == "f2q6_probability_values":
        theorem_body = f"""
theorem {theorem_name} : ProbabilityValuesClaim := by
  unfold ProbabilityValuesClaim waysBeforeFourthHead denom
  norm_num
"""

    elif step.type == "f2q6_ratio_comparison":
        theorem_body = f"""
theorem {theorem_name} : RatioComparisonClaim := by
  unfold RatioComparisonClaim ratioNumer ratioDenom
  constructor
  · intro n hn hlt
    omega
  · constructor
    · norm_num
    · intro n hgt
      omega
"""

    else:
        raise NotImplementedError(f"Unsupported ITA2025F2Q6 formal step type: {step.type}")

    return f"""
import ConfiaLeanAuditor.Problems.ITA2025F2Q6.Statement

namespace ConfIA.LeanAuditor.Generated.ITA2025F2Q6.Step

open ConfIA.LeanAuditor.ITA2025F2Q6

noncomputable section

{theorem_body}

end

end ConfIA.LeanAuditor.Generated.ITA2025F2Q6.Step
"""


def render_formal_step(problem_id: str, step: FormalStep) -> str:
    if problem_id == "ITA2025Q1":
        return render_q1_formal_step(step)

    if problem_id == "ITA2025Q3":
        return render_q3_formal_step(step)

    if problem_id == "ITA2025Q4":
        return render_q4_formal_step(step)

    if problem_id == "ITA2025Q5":
        return render_q5_formal_step(step)

    if problem_id == "ITA2025Q8":
        return render_q8_formal_step(step)

    if problem_id == "ITA2025F2Q1":
        return render_f2q1_formal_step(step)

    if problem_id == "ITA2025F2Q6":
        return render_f2q6_formal_step(step)

    if problem_id == "ITA2025F2Q5":
        return render_f2q5_formal_step(step)

    raise NotImplementedError("Formal step rendering not implemented for problem: " + problem_id)


def evaluate_formal_steps(
    repo_root: Path,
    problem_id: str,
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
) -> List[FormalStepResult]:
    steps_dir = artifact_dir / "formal_steps"
    steps_dir.mkdir(parents=True, exist_ok=True)

    results: List[FormalStepResult] = []

    for step in claim_extraction.formal_steps:
        lean_file = steps_dir / (step.id + ".lean")

        try:
            validate_formal_step(step)
        except FormalStepValidationError as exc:
            rejected_file = steps_dir / (step.id + ".rejected.txt")
            rejected_file.write_text(
                "Rejected formal step.\n\n"
                + "Reason: " + str(exc) + "\n\n"
                + "lhs: " + step.lhs + "\n"
                + "rhs: " + step.rhs + "\n"
                + "lean_method: " + step.lean_method + "\n",
                encoding="utf-8",
            )

            results.append(
                FormalStepResult(
                    id=step.id,
                    type=step.type,
                    description=step.description,
                    evidence=step.evidence,
                    lhs=step.lhs,
                    rhs=step.rhs,
                    lean_method=step.lean_method,
                    supports_claim_types=step.supports_claim_types,
                    supports_rubric_items=step.supports_rubric_items,
                    lean_file=str(rejected_file),
                    status="invalid_formal_step",
                    compiled=False,
                    exit_code=-1,
                    stdout="",
                    stderr=str(exc),
                )
            )
            continue

        lean_source = render_formal_step(problem_id, step)
        lean_file.write_text(lean_source, encoding="utf-8")

        raw = run_lean_file(repo_root=repo_root, lean_file=lean_file)

        status = "verified" if raw["status"] == "verified" else raw["status"]

        results.append(
            FormalStepResult(
                id=step.id,
                type=step.type,
                description=step.description,
                evidence=step.evidence,
                lhs=step.lhs,
                rhs=step.rhs,
                lean_method=step.lean_method,
                supports_claim_types=step.supports_claim_types,
                supports_rubric_items=step.supports_rubric_items,
                lean_file=str(lean_file),
                status=status,
                compiled=raw["compiled"],
                exit_code=raw["exit_code"],
                stdout=raw.get("stdout", ""),
                stderr=raw.get("stderr", ""),
            )
        )

    return results
