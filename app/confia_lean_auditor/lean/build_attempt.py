from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from confia_lean_auditor.core.schemas import ClaimExtraction, FormalStepResult
from confia_lean_auditor.lean.attempt_builders.ita2025q1 import (
    build_attempt_ita2025q1,
)


def build_attempt(
    repo_root: Path,
    problem_id: str,
    claim_extraction: ClaimExtraction,
    artifact_dir: Path,
    formal_step_results: Optional[List[FormalStepResult]] = None,
) -> Dict[str, Any]:
    if problem_id == "ITA2025Q1":
        return build_attempt_ita2025q1(
            claim_extraction=claim_extraction,
            artifact_dir=artifact_dir,
            formal_step_results=formal_step_results,
        )

    raise NotImplementedError("Attempt builder not implemented for problem: " + problem_id)
