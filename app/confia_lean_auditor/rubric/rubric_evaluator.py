from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from confia_lean_auditor.core.paths import get_problem_dir
from confia_lean_auditor.core.problem_assets import RubricConfig, load_rubric_config
from confia_lean_auditor.core.schemas import (
    ClaimExtraction,
    MicroclaimResult,
    RubricAssessment,
    RubricItemResult,
)


def evaluate_rubric(
    repo_root: Path,
    problem_id: str,
    claim_extraction: ClaimExtraction,
    microclaims: Optional[List[MicroclaimResult]] = None,
    rubric_config: Optional[RubricConfig] = None,
) -> RubricAssessment:
    if rubric_config is None:
        problem_dir = get_problem_dir(repo_root, problem_id)
        rubric_config = load_rubric_config(problem_dir)

    claims_by_type = {}
    for claim in claim_extraction.claims:
        claims_by_type.setdefault(claim.type, claim)

    verified_microclaim_ids = set()
    if microclaims is not None:
        verified_microclaim_ids = {
            mc.id
            for mc in microclaims
            if mc.textual_evidence and mc.lean_status == "verified_by_lean"
        }

    items: List[RubricItemResult] = []
    score = 0.0

    for item in rubric_config.items:
        claim_type = item.claim_type
        claim = claims_by_type.get(claim_type)

        required_microclaim_ids = item.required_microclaim_ids

        has_claim = claim is not None

        if required_microclaim_ids:
            has_required_microclaims = all(
                mc_id in verified_microclaim_ids for mc_id in required_microclaim_ids
            )
        else:
            has_required_microclaims = True

        detected = has_claim and has_required_microclaims

        points = float(item.points) if detected else 0.0
        score += points

        evidence = None
        claim_id = None

        if claim is not None:
            evidence = claim.evidence
            claim_id = claim.id

        items.append(
            RubricItemResult(
                id=item.id,
                description=item.description,
                detected=detected,
                points=points,
                max_points=float(item.points),
                evidence=evidence,
                claim_id=claim_id,
            )
        )

    return RubricAssessment(
        score=score,
        max_score=float(rubric_config.max_score),
        items=items,
    )


F2Q8_STUDENT_CHECK_TO_RUBRIC_ITEMS: Dict[str, List[str]] = {
    "f2q8_student_det_formula": ["determinant_formula"],
    "f2q8_student_final_answer": ["final_answer"],
    "f2q8_student_pair_reduction": ["final_answer"],
    "f2q8_student_alternating_sum_value": ["final_answer"],
    "f2q8_student_pair_count": ["final_answer"],
}


F2Q8_STUDENT_CHECK_REASON: Dict[str, str] = {
    "f2q8_student_det_formula": (
        "A fórmula do determinante escrita pelo aluno foi rejeitada "
        "pela verificação dinâmica em Lean."
    ),
    "f2q8_student_final_answer": (
        "A resposta final escrita pelo aluno não coincide com o valor "
        "canônico 1013 verificado em Lean."
    ),
    "f2q8_student_pair_reduction": (
        "A redução final por pares escrita pelo aluno foi rejeitada "
        "pela verificação dinâmica em Lean."
    ),
    "f2q8_student_alternating_sum_value": (
        "O valor atribuído pelo aluno à soma alternada foi rejeitado "
        "pela verificação dinâmica em Lean."
    ),
    "f2q8_student_pair_count": (
        "A contagem de pares escrita pelo aluno foi rejeitada "
        "pela verificação dinâmica em Lean."
    ),
}


def _field_value(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        value = obj.get(name)
    else:
        value = getattr(obj, name, None)

    if hasattr(value, "value"):
        return value.value

    return value


def apply_student_claim_adjustments(
    rubric: RubricAssessment,
    problem_id: str,
    student_claim_checks: List[Any],
) -> RubricAssessment:
    """Reduce rubric points when a concrete student claim is formally refuted.

    This function is intentionally conservative:
    - it only penalizes checks with status == "failed";
    - it does not penalize unsupported claims;
    - it does not penalize Lean/time-out errors automatically;
    - it does not add points.
    """
    if problem_id != "ITA2025F2Q8":
        return rubric

    failed_reasons_by_item: Dict[str, List[str]] = {}

    for check in student_claim_checks:
        status = _field_value(check, "status")
        if status != "failed":
            continue

        claim_type = _field_value(check, "claim_type")
        if claim_type not in F2Q8_STUDENT_CHECK_TO_RUBRIC_ITEMS:
            continue

        raw_text = _field_value(check, "raw_text") or ""
        base_reason = F2Q8_STUDENT_CHECK_REASON.get(
            claim_type,
            "Uma afirmação concreta do aluno foi rejeitada pela verificação dinâmica em Lean.",
        )

        if raw_text:
            reason = f"{base_reason} Trecho: {raw_text!r}."
        else:
            reason = base_reason

        for item_id in F2Q8_STUDENT_CHECK_TO_RUBRIC_ITEMS[claim_type]:
            failed_reasons_by_item.setdefault(item_id, []).append(reason)

    if not failed_reasons_by_item:
        return rubric

    for item in rubric.items:
        reasons = failed_reasons_by_item.get(item.id, [])
        if not reasons:
            continue

        # Mantemos detected=True se o texto foi detectado, mas zeramos os pontos
        # porque uma afirmação concreta associada foi formalmente refutada.
        item.points = 0.0
        item.student_check_adjusted = True

        for reason in reasons:
            if reason not in item.adjustment_notes:
                item.adjustment_notes.append(reason)

    rubric.score = sum(item.points for item in rubric.items)
    return rubric
