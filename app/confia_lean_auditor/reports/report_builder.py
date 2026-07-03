from __future__ import annotations

from typing import List

from confia_lean_auditor.core.schemas import (
    LeanCertificate,
    MicroclaimResult,
    RubricAssessment,
)


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
    detected = [item.description for item in rubric.items if item.detected]
    missing = [item.description for item in rubric.items if not item.detected]

    verified_microclaims = [
        mc.description
        for mc in microclaims
        if mc.lean_status == "verified_by_lean" and mc.textual_evidence
    ]

    parts = []

    if detected:
        parts.append(
            "A solução apresentou evidências para: "
            + "; ".join(detected)
            + "."
        )

    if missing:
        parts.append(
            "Não foram detectadas evidências suficientes para: "
            + "; ".join(missing)
            + "."
        )

    if verified_microclaims:
        parts.append(
            "Microclaims com evidência textual e certificado Lean: "
            + "; ".join(verified_microclaims)
            + "."
        )

    if lean_certificate.status != "verified":
        parts.append(
            "A checagem Lean não gerou certificado válido. Status: "
            + lean_certificate.status
            + "."
        )

    return " ".join(parts)
