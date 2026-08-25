from __future__ import annotations

from typing import Any, Dict, List, Optional

from confia_lean_auditor.core.schemas import (
    LeanCertificate,
    MicroclaimResult,
    PedagogicalEvidenceItem,
    PedagogicalReport,
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


def _field_value(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _normalize_space(text: str) -> str:
    return " ".join(text.strip().split())


def _confidence_label(confidence: Optional[float]) -> str:
    if confidence is None:
        return "não avaliada"
    if confidence >= 0.85:
        return "confiabilidade alta"
    if confidence >= 0.65:
        return "confiabilidade média"
    return "confiabilidade baixa"


def _overall_reliability(items: List[PedagogicalEvidenceItem]) -> str:
    reliabilities = {item.reliability for item in items}

    if "confiabilidade baixa" in reliabilities:
        return "confiabilidade baixa"
    if "confiabilidade alta" in reliabilities:
        return "confiabilidade alta"
    if "confiabilidade média" in reliabilities:
        return "confiabilidade média"
    return "não avaliada"


def _pedagogical_note(text: str) -> str:
    replacements = {
        "pela verificação dinâmica em Lean": "pela checagem automática",
        "pela verificação dinâmica": "pela checagem automática",
        "verificados em Lean": "esperados",
        "verificado em Lean": "esperado",
        "Lean": "checagem automática",
    }
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    return _normalize_space(result)


def _summary_for_verdict(verdict: str, score: float, max_score: float) -> str:
    if verdict == "correto":
        return (
            f"A solução correta recebeu {score:g} de {max_score:g} pontos. "
            "As principais evidências reconhecidas foram conferidas automaticamente "
            "por checagem automática."
        )
    if verdict == "parcialmente_correto":
        return (
            f"A solução está parcialmente correta e recebeu {score:g} de {max_score:g} pontos. "
            "Há boas evidências em parte do raciocínio, mas ainda faltam etapas ou justificativas."
        )
    if score > 0:
        return (
            f"A solução recebeu {score:g} de {max_score:g} pontos. "
            "Foram encontradas poucas evidências suficientes para sustentar a resposta."
        )
    return (
        f"A solução foi classificada como incorreta e recebeu {score:g} de {max_score:g} pontos. "
        "As evidências encontradas não sustentam a resposta final."
    )


def _claim_confidence_by_id(student_claims: List[Any]) -> Dict[str, Optional[float]]:
    result: Dict[str, Optional[float]] = {}
    for claim in student_claims:
        claim_id = _field_value(claim, "id")
        confidence = _field_value(claim, "confidence")
        if isinstance(claim_id, str):
            result[claim_id] = confidence if isinstance(confidence, (int, float)) else None
    return result


def _build_check_evidence_items(
    student_claims: List[Any],
    student_claim_checks: List[Any],
) -> List[PedagogicalEvidenceItem]:
    confidence_by_id = _claim_confidence_by_id(student_claims)
    items: List[PedagogicalEvidenceItem] = []

    for index, check in enumerate(student_claim_checks):
        status = _field_value(check, "status")
        if status not in {"verified", "failed", "unsupported", "error"}:
            continue

        raw_text = _field_value(check, "raw_text")
        evidence = _normalize_space(str(raw_text)) if raw_text else None
        check_id = _field_value(check, "id")
        confidence = confidence_by_id.get(check_id)

        if status == "verified":
            result = "conferida"
            explanation = (
                "Esta afirmação foi reconhecida no texto e conferida automaticamente."
            )
            reliability = _confidence_label(confidence)
        elif status == "failed":
            result = "incorreta"
            explanation = (
                "Esta afirmação foi reconhecida no texto, mas a checagem automática indicou "
                "que ela não está correta."
            )
            reliability = _confidence_label(confidence)
        elif evidence:
            result = "não conclusiva"
            explanation = (
                "Esta afirmação foi reconhecida no texto, mas não houve cobertura suficiente "
                "para decidir automaticamente."
            )
            reliability = "confiabilidade baixa"
        else:
            result = "não avaliada"
            explanation = "Não houve evidência textual suficiente para avaliar esta afirmação."
            reliability = "não avaliada"

        items.append(
            PedagogicalEvidenceItem(
                id=str(check_id or f"student_check_{index}"),
                title="Afirmação do estudante",
                result=result,
                evidence=evidence,
                reliability=reliability,
                explanation=explanation,
            )
        )

    return items


def _build_rubric_evidence_items(
    rubric: RubricAssessment,
    checked_evidence_texts: set[str],
) -> List[PedagogicalEvidenceItem]:
    items: List[PedagogicalEvidenceItem] = []

    for item in rubric.items:
        evidence = _normalize_space(item.evidence) if item.evidence else None
        if evidence and evidence in checked_evidence_texts:
            continue

        if item.points > 0 and evidence:
            result = "pontuada"
            reliability = "confiabilidade média"
            explanation = (
                "Este ponto da rubrica tem trecho textual correspondente, mas não foi uma "
                "afirmação concreta checada separadamente."
            )
        elif item.points > 0:
            result = "pontuada"
            reliability = "confiabilidade baixa"
            explanation = "Este ponto foi reconhecido, mas a evidencia textual e limitada."
        elif evidence:
            result = "não pontuada"
            reliability = "confiabilidade baixa"
            explanation = (
                "Há um trecho relacionado a este ponto, mas ele não foi suficiente para "
                "receber a pontuação."
            )
        else:
            continue

        items.append(
            PedagogicalEvidenceItem(
                id=item.id,
                title=item.description,
                result=result,
                evidence=evidence,
                reliability=reliability,
                explanation=explanation,
            )
        )

    return items


def build_pedagogical_report(
    *,
    score: float,
    max_score: float,
    verdict: str,
    rubric: RubricAssessment,
    student_claims: List[Any],
    student_claim_checks: List[Any],
    microclaims: List[MicroclaimResult],
    artifact_dir: Optional[str],
) -> PedagogicalReport:
    check_items = _build_check_evidence_items(student_claims, student_claim_checks)
    checked_evidence_texts = {
        item.evidence for item in check_items if item.evidence
    }
    rubric_items = _build_rubric_evidence_items(rubric, checked_evidence_texts)
    evidence_items = check_items + rubric_items

    attention_points: List[str] = []
    for item in rubric.items:
        for note in item.adjustment_notes:
            cleaned = _pedagogical_note(note)
            if cleaned and cleaned not in attention_points:
                attention_points.append(cleaned)

    verified_internal = [
        mc.description
        for mc in microclaims
        if mc.textual_evidence and mc.lean_status == "verified_by_lean"
    ]
    if verified_internal and verdict == "correto":
        attention_points.append(
            "As etapas centrais reconhecidas também passaram por verificação formal interna."
        )

    return PedagogicalReport(
        summary=_summary_for_verdict(verdict, score, max_score),
        result=verdict,
        score=score,
        max_score=max_score,
        verdict=verdict,
        reliability=_overall_reliability(evidence_items),
        evidence_items=evidence_items,
        attention_points=attention_points,
        technical_record_available=bool(artifact_dir),
    )
