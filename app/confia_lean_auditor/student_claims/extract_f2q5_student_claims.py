from __future__ import annotations

import re
import unicodedata
from typing import List

from confia_lean_auditor.student_claims.schemas import StudentClaim


def normalize(text: str) -> str:
    text = text.replace("²", "^2")
    text = text.replace("³", "^3")
    text = text.replace("¹⁰⁰", "^100")
    text = text.replace("−", "-")
    text = text.replace("–", "-")
    text = text.replace("·", "*")
    text = text.replace(",", ".")
    text = text.replace("≤", "<=")
    text = text.replace("≥", ">=")
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _context(original: str, raw: str, radius: int = 90) -> str:
    idx = original.lower().find(raw.lower())
    if idx < 0:
        return original[: 2 * radius]
    start = max(0, idx - radius)
    end = min(len(original), idx + len(raw) + radius)
    return original[start:end]


def _scaled_decimal(value: str) -> int:
    value = value.strip().replace(",", ".")
    if "." not in value:
        return int(value) * 10000
    whole, frac = value.split(".", 1)
    frac = (frac + "0000")[:4]
    return int(whole) * 10000 + int(frac)


def _make_claim(
    idx: int,
    claim_type: str,
    raw_text: str,
    normalized_text: str,
    context: str,
    data: dict,
    method: str = "norm_num",
    confidence: float = 0.86,
) -> StudentClaim:
    return StudentClaim(
        id=f"student_claim_{idx}",
        problem_id="ITA2025F2Q5",
        claim_type=claim_type,  # type: ignore[arg-type]
        raw_text=raw_text,
        normalized_text=normalized_text,
        context=context,
        data=data,
        method=method,
        confidence=confidence,
    )


def _extract_log_power_decomposition(solution: str, claims: List[StudentClaim]) -> None:
    t = normalize(solution)
    c = compact(t)

    # Captura valores como 47.7100, 47.71, 47.7000.
    match = re.search(r"47\.(?:\d{2,4})", c)
    if not match:
        return

    total_text = match.group(0)
    total_scaled = _scaled_decimal(total_text)

    mantissa_scaled = total_scaled - 47 * 10000

    claims.append(
        _make_claim(
            idx=len(claims),
            claim_type="f2q5_student_log_power_decomposition",
            raw_text=f"log total = {total_text}",
            normalized_text=f"totalLogScaled = {total_scaled}; mantissaScaled = {mantissa_scaled}",
            context=_context(solution, total_text),
            data={
                "total_log_scaled": total_scaled,
                "integer_part_scaled": 47 * 10000,
                "mantissa_scaled": mantissa_scaled,
            },
            method="norm_num [totalLogScaled, integerPartScaled, mantissaScaled, log3Scaled, scale]",
            confidence=0.86,
        )
    )


def _extract_mantissa(solution: str, claims: List[StudentClaim]) -> None:
    c = compact(normalize(solution))

    value_text: str | None = None
    for candidate in ["0.7100", "0.71", "0.7000", "0.72"]:
        if candidate in c:
            value_text = candidate
            break

    if value_text is None:
        return

    value_scaled = _scaled_decimal(value_text)

    claims.append(
        _make_claim(
            idx=len(claims),
            claim_type="f2q5_student_mantissa",
            raw_text=f"mantissa = {value_text}",
            normalized_text=f"mantissaScaled = {value_scaled}",
            context=_context(solution, value_text),
            data={"mantissa_scaled": value_scaled},
            method="norm_num [mantissaScaled]",
            confidence=0.86,
        )
    )


def _extract_digit_log_bounds(solution: str, claims: List[StudentClaim]) -> None:
    c = compact(normalize(solution))

    log5_text: str | None = None
    log6_text: str | None = None

    # Ordem importa: padrões mais específicos antes dos truncados.
    for candidate in ["0.6990", "0.699", "0.6900"]:
        if candidate in c:
            log5_text = candidate
            break

    for candidate in ["0.7781", "0.778"]:
        if candidate in c:
            log6_text = candidate
            break

    if log5_text is None or log6_text is None:
        return

    log5_scaled = _scaled_decimal(log5_text)
    log6_scaled = _scaled_decimal(log6_text)

    claims.append(
        _make_claim(
            idx=len(claims),
            claim_type="f2q5_student_digit_log_bounds",
            raw_text=f"log5={log5_text}; log6={log6_text}",
            normalized_text=f"log5Scaled = {log5_scaled}; log6Scaled = {log6_scaled}",
            context=solution[:220],
            data={"log5_scaled": log5_scaled, "log6_scaled": log6_scaled},
            method="norm_num [log5Scaled, log6Scaled, log2Scaled, log3Scaled, scale]",
            confidence=0.86,
        )
    )


def _extract_between_bounds(solution: str, claims: List[StudentClaim]) -> None:
    c = compact(normalize(solution))

    # Padrão principal: 0.6990 < 0.7100 < 0.7781.
    match = re.search(
        r"(?P<left>0\.\d{2,4})<(?P<middle>0\.\d{2,4})<(?P<right>0\.\d{2,4})",
        c,
    )

    if not match:
        return

    left_text = match.group("left")
    middle_text = match.group("middle")
    right_text = match.group("right")

    left_scaled = _scaled_decimal(left_text)
    middle_scaled = _scaled_decimal(middle_text)
    right_scaled = _scaled_decimal(right_text)

    raw = f"{left_text}<{middle_text}<{right_text}"

    claims.append(
        _make_claim(
            idx=len(claims),
            claim_type="f2q5_student_between_bounds",
            raw_text=raw,
            normalized_text=(
                f"between: {left_scaled} < {middle_scaled} < {right_scaled}"
            ),
            context=_context(solution, raw),
            data={
                "left_scaled": left_scaled,
                "middle_scaled": middle_scaled,
                "right_scaled": right_scaled,
            },
            method="norm_num [log5Scaled, log6Scaled, mantissaScaled]",
            confidence=0.86,
        )
    )


def _extract_final_digit(solution: str, claims: List[StudentClaim]) -> None:
    t = normalize(solution)

    tail = t
    for cue in ["portanto", "logo", "resposta", "conclu", "primeiro algarismo"]:
        idx = t.rfind(cue)
        if idx >= 0:
            tail = t[idx:]
            break

    digit: int | None = None

    patterns = [
        r"primeiro\s+algarismo\s+(?:e|é|=)\s*([0-9])",
        r"algarismo\s+inicial\s+(?:e|é|=)\s*([0-9])",
        r"resposta\s+(?:e|é|=)\s*([0-9])",
        r"portanto.*?([0-9])",
    ]

    for pattern in patterns:
        match = re.search(pattern, tail)
        if match:
            digit = int(match.group(1))
            break

    if digit is None:
        return

    claims.append(
        _make_claim(
            idx=len(claims),
            claim_type="f2q5_student_final_digit",
            raw_text=f"primeiro algarismo = {digit}",
            normalized_text=f"final_digit = {digit}",
            context=tail[:220],
            data={"digit": digit},
            method="norm_num",
            confidence=0.88,
        )
    )


def extract_f2q5_student_claims(solution: str) -> List[StudentClaim]:
    claims: List[StudentClaim] = []

    _extract_log_power_decomposition(solution, claims)
    _extract_mantissa(solution, claims)
    _extract_digit_log_bounds(solution, claims)
    _extract_between_bounds(solution, claims)
    _extract_final_digit(solution, claims)

    return claims
