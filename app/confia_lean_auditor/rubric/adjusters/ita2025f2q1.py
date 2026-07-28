from __future__ import annotations

from typing import Any, Dict, List

from confia_lean_auditor.core.schemas import RubricAssessment


F2Q1_STUDENT_CHECK_TO_RUBRIC_ITEMS: Dict[str, List[str]] = {
    "f2q1_student_power_reduction": ["power_reductions"],
    "f2q1_student_reduced_form": ["reduced_polynomial_form"],
    "f2q1_student_coefficient_system": ["coefficient_system"],
    "f2q1_student_final_answer": ["final_answer"],
}


F2Q1_STUDENT_CHECK_REASON: Dict[str, str] = {
    "f2q1_student_power_reduction": (
        "Uma redução de potência escrita pelo aluno foi rejeitada "
        "pela verificação dinâmica em Lean."
    ),
    "f2q1_student_reduced_form": (
        "A forma reduzida do polinômio escrita pelo aluno foi rejeitada "
        "pela verificação dinâmica em Lean."
    ),
    "f2q1_student_coefficient_system": (
        "O sistema de coeficientes escrito pelo aluno foi rejeitado "
        "pela verificação dinâmica em Lean."
    ),
    "f2q1_student_final_answer": (
        "A resposta final escrita pelo aluno não coincide com "
        "a=-1 e b=3, valores canônicos verificados em Lean."
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


def apply_f2q1_student_claim_adjustments(
    rubric: RubricAssessment,
    student_claim_checks: List[Any],
) -> RubricAssessment:
    """Apply F2Q1 rubric reductions based on dynamic Lean checks.

    Policy:
    - only status == "failed" reduces points;
    - "unsupported" does not reduce points;
    - "error" does not reduce points automatically;
    - this adjuster never adds points.
    """
    failed_reasons_by_item: Dict[str, List[str]] = {}

    for check in student_claim_checks:
        status = _field_value(check, "status")
        if status != "failed":
            continue

        claim_type = _field_value(check, "claim_type")
        if claim_type not in F2Q1_STUDENT_CHECK_TO_RUBRIC_ITEMS:
            continue

        raw_text = _field_value(check, "raw_text") or ""
        base_reason = F2Q1_STUDENT_CHECK_REASON.get(
            claim_type,
            "Uma afirmação concreta do aluno foi rejeitada pela verificação dinâmica em Lean.",
        )

        if raw_text:
            reason = f"{base_reason} Trecho: {raw_text!r}."
        else:
            reason = base_reason

        for item_id in F2Q1_STUDENT_CHECK_TO_RUBRIC_ITEMS[claim_type]:
            failed_reasons_by_item.setdefault(item_id, []).append(reason)

    if not failed_reasons_by_item:
        return rubric

    for item in rubric.items:
        reasons = failed_reasons_by_item.get(item.id, [])
        if not reasons:
            continue

        item.points = 0.0
        item.student_check_adjusted = True

        for reason in reasons:
            if reason not in item.adjustment_notes:
                item.adjustment_notes.append(reason)

    rubric.score = sum(item.points for item in rubric.items)
    return rubric
