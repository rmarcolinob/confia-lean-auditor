from __future__ import annotations

from typing import List

from confia_lean_auditor.core.schemas import (
    LeanCertificate,
    MicroclaimResult,
    RubricAssessment,
)


def clean_sentence(text: str) -> str:
    text = text.strip()
    while text.endswith("."):
        text = text[:-1].strip()
    return text


def verdict_from_score(score: float, max_score: float) -> str:
    ratio = score / max_score if max_score else 0.0

    if ratio >= 0.9:
        return "correto"
    if ratio >= 0.5:
        return "parcialmente_correto"
    if ratio > 0:
        return "insuficiente"
    return "incorreto"


def build_feedback(
    rubric: RubricAssessment,
    lean_certificate: LeanCertificate,
    microclaims: List[MicroclaimResult],
) -> str:
    parts: List[str] = []

    credited_items = [
        item.description
        for item in rubric.items
        if item.points > 0
    ]

    adjusted_items = [
        item
        for item in rubric.items
        if getattr(item, "student_check_adjusted", False)
    ]

    missing_items = [
        item.description
        for item in rubric.items
        if item.points == 0 and not getattr(item, "student_check_adjusted", False)
    ]

    if credited_items:
        parts.append(
            "A solução apresentou evidências suficientes para: "
            + "; ".join(credited_items)
            + "."
        )

    if missing_items:
        parts.append(
            "Não foram detectadas evidências suficientes para: "
            + "; ".join(missing_items)
            + "."
        )

    dynamic_notes: List[str] = []
    for item in adjusted_items:
        for note in getattr(item, "adjustment_notes", []) or []:
            if note not in dynamic_notes:
                dynamic_notes.append(note)

    if dynamic_notes:
        parts.append(
            "A verificação dinâmica em Lean refutou afirmações concretas da solução: "
            + " ".join(dynamic_notes)
        )

    if lean_certificate.status != "verified":
        parts.append(
            "A verificação Lean canônica não foi concluída com sucesso. "
            "Status: "
            + lean_certificate.status
            + "."
        )

    verified_microclaims = [
        mc.description
        for mc in microclaims
        if mc.textual_evidence and mc.lean_status == "verified_by_lean"
    ]

    if verified_microclaims:
        parts.append(
            "Microclaims com evidência textual e certificado Lean: "
            + "; ".join(verified_microclaims)
            + "."
        )

    if not parts:
        return "Não foram encontradas evidências suficientes para avaliar a solução."

    return " ".join(parts)
