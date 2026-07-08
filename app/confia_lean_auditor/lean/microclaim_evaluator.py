from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from confia_lean_auditor.core.paths import get_problem_dir
from confia_lean_auditor.core.problem_assets import (
    MicroclaimsConfig,
    load_microclaims_config,
)
from confia_lean_auditor.core.schemas import (
    ClaimExtraction,
    FormalStepResult,
    LeanCertificate,
    MicroclaimResult,
)


def locally_verified(result: MicroclaimResult) -> bool:
    return (
        result.textual_evidence
        and result.formal_steps_verified
        and result.lean_status == "verified_by_lean"
    )


def dependencies_are_verified(
    depends_on_microclaim_ids: List[str],
    results_by_id: Dict[str, MicroclaimResult],
) -> bool:
    for dep_id in depends_on_microclaim_ids:
        dep = results_by_id.get(dep_id)
        if dep is None:
            return False
        if not locally_verified(dep):
            return False

    return True


def evaluate_microclaims(
    repo_root: Path,
    problem_id: str,
    claim_extraction: ClaimExtraction,
    lean_certificate: LeanCertificate,
    generated_theorems: List[str],
    formal_step_results: List[FormalStepResult],
    microclaims_config: Optional[MicroclaimsConfig] = None,
) -> List[MicroclaimResult]:
    if microclaims_config is None:
        problem_dir = get_problem_dir(repo_root, problem_id)
        microclaims_config = load_microclaims_config(problem_dir)

    present_claim_types = set(claim.type for claim in claim_extraction.claims)
    generated = set(generated_theorems)
    verified_step_types = {
        step.type for step in formal_step_results if step.status == "verified"
    }

    first_pass: List[MicroclaimResult] = []

    for item in microclaims_config.microclaims:
        theorem = item.theorem
        claim_types = item.claim_types
        required_formal_step_types = item.required_formal_step_types
        depends_on_microclaim_ids = item.depends_on_microclaim_ids

        textual_evidence = (
            all(claim_type in present_claim_types for claim_type in claim_types)
            if claim_types
            else False
        )

        theorem_generated = theorem in generated if theorem else False

        formal_steps_verified = all(
            step_type in verified_step_types
            for step_type in required_formal_step_types
        )

        if not textual_evidence:
            lean_status = "no_textual_evidence"
        elif not formal_steps_verified:
            lean_status = "formal_steps_not_verified"
        elif not theorem_generated:
            lean_status = "not_generated"
        elif lean_certificate.status == "verified":
            lean_status = "verified_by_lean"
        else:
            lean_status = "not_verified_" + lean_certificate.status

        first_pass.append(
            MicroclaimResult(
                id=item.id,
                description=item.description,
                theorem=theorem,
                claim_types=claim_types,
                required_formal_step_types=required_formal_step_types,
                depends_on_microclaim_ids=depends_on_microclaim_ids,
                dependencies_verified=False,
                formal_steps_verified=formal_steps_verified,
                textual_evidence=textual_evidence,
                lean_status=lean_status,
                supports_rubric_items=item.supports_rubric_items,
            )
        )

    results_by_id = {mc.id: mc for mc in first_pass}
    final_results: List[MicroclaimResult] = []

    for mc in first_pass:
        dependencies_verified = dependencies_are_verified(
            mc.depends_on_microclaim_ids,
            results_by_id,
        )

        lean_status = mc.lean_status
        if mc.textual_evidence and mc.lean_status == "verified_by_lean" and not dependencies_verified:
            lean_status = "dependency_not_verified"

        final_results.append(
            MicroclaimResult(
                id=mc.id,
                description=mc.description,
                theorem=mc.theorem,
                claim_types=mc.claim_types,
                required_formal_step_types=mc.required_formal_step_types,
                depends_on_microclaim_ids=mc.depends_on_microclaim_ids,
                dependencies_verified=dependencies_verified,
                formal_steps_verified=mc.formal_steps_verified,
                textual_evidence=mc.textual_evidence,
                lean_status=lean_status,
                supports_rubric_items=mc.supports_rubric_items,
            )
        )

    return final_results
