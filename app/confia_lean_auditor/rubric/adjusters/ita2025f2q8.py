from __future__ import annotations

from confia_lean_auditor.student_claims.schemas import is_mathematically_refuted

from typing import Any, Dict, List

from confia_lean_auditor.core.schemas import RubricAssessment
from confia_lean_auditor.rubric.assessment import refresh_assessment


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


def apply_f2q8_student_claim_adjustments(
    rubric: RubricAssessment,
    student_claim_checks: List[Any],
) -> RubricAssessment:
    """Apply F2Q8 rubric reductions based on dynamic Lean checks.

    Policy:
    - only a formally evidenced "refuted" check reduces points;
    - "unsupported" does not reduce points;
    - "technical_error", "unverified" and legacy "failed"/"error" never reduce points;
    - this adjuster never adds points.
    """
    failed_reasons_by_item: Dict[str, List[str]] = {}

    for check in student_claim_checks:
        if not is_mathematically_refuted(check):
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

        item.points = 0.0
        item.mathematical_status = "refuted"
        item.verification_status = "available"
        item.assessment_note = "Refutação matemática formal disponível para este critério."
        item.student_check_adjusted = True

        for reason in reasons:
            if reason not in item.adjustment_notes:
                item.adjustment_notes.append(reason)

    return refresh_assessment(rubric)
