from __future__ import annotations

from pathlib import Path
from typing import List

from confia_lean_auditor.core.schemas import (
    ClaimExtraction,
    FormalStep,
    FormalStepResult,
)
from confia_lean_auditor.lean.run_lean import run_lean_file


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


def render_formal_step(problem_id: str, step: FormalStep) -> str:
    if problem_id == "ITA2025Q1":
        return render_q1_formal_step(step)

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
        lean_source = render_formal_step(problem_id, step)
        lean_file = steps_dir / (step.id + ".lean")
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
