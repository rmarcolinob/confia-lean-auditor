from __future__ import annotations

import re
import unicodedata
from typing import Dict, Optional

from confia_lean_auditor.core.schemas import (
    ClaimExtraction,
    ExtractedClaim,
)


def normalize(text: str) -> str:
    text = text.replace("²", "^2")
    text = text.replace("−", "-")
    text = text.replace("·", "*")
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def make_claim(
    claim_id: str,
    claim_type: str,
    text: str,
    evidence: str,
    confidence: float,
    normalized: Optional[Dict[str, str]] = None,
) -> ExtractedClaim:
    return ExtractedClaim(
        id=claim_id,
        type=claim_type,
        text=text,
        evidence=evidence,
        confidence=confidence,
        normalized=normalized or {},
    )


def extract_claims_ita2025q4(solution: str) -> ClaimExtraction:
    t = normalize(solution)
    c = compact(t)

    claims = []

    has_x1 = "1/8" in c or "(1/8)" in c
    has_x2 = "3/8" in c or "(3/8)" in c
    mentions_positive = (
        "positivo" in t
        or "positivos" in t
        or "x1>0" in c
        or "x2>0" in c
        or "x_1>0" in c
        or "x_2>0" in c
    )

    if has_x1 and has_x2 and mentions_positive:
        claims.append(
            make_claim(
                claim_id="q4_c1",
                claim_type="positive_witnesses",
                text="Escolhe x1 = 1/8 e x2 = 3/8 como testemunhas positivas.",
                evidence="A solução escolhe x1 = 1/8 e x2 = 3/8 e menciona que são positivos.",
                confidence=0.95,
                normalized={"x1": "1/8", "x2": "3/8"},
            )
        )

    has_same_value = "29/32" in c
    has_phi_expression = (
        "2x1^2-x1+1" in c
        or "2*x1^2-x1+1" in c
        or "2x_1^2-x_1+1" in c
        or "2(1/8)^2-1/8+1" in c
    ) and (
        "2x2^2-x2+1" in c
        or "2*x2^2-x2+1" in c
        or "2x_2^2-x_2+1" in c
        or "2(3/8)^2-3/8+1" in c
    )

    if has_x1 and has_x2 and (has_same_value or has_phi_expression):
        claims.append(
            make_claim(
                claim_id="q4_c2",
                claim_type="same_f_argument",
                text="As testemunhas produzem o mesmo argumento em f.",
                evidence="A solução verifica que 2(1/8)^2 - 1/8 + 1 e 2(3/8)^2 - 3/8 + 1 são iguais a 29/32.",
                confidence=0.95,
                normalized={"common_argument": "29/32"},
            )
        )

    has_distinct_squares = (
        ("1/64" in c and "9/64" in c)
        or "x1^2!=x2^2" in c
        or "x1^2≠x2^2" in c
        or "distintos" in t
        or "diferentes" in t
    )

    if has_x1 and has_x2 and has_distinct_squares:
        claims.append(
            make_claim(
                claim_id="q4_c3",
                claim_type="distinct_g_inputs",
                text="As entradas x1^2 e x2^2 de g são distintas.",
                evidence="A solução identifica x1^2 = 1/64 e x2^2 = 9/64, que são distintos.",
                confidence=0.95,
                normalized={"x1_squared": "1/64", "x2_squared": "9/64"},
            )
        )

    uses_functional_hypothesis = (
        "pela hipotese" in t
        or "hipotese funcional" in t
        or "g(x1^2)" in c
        or "g(x_1^2)" in c
        or "g((1/8)^2)" in c
    )

    concludes_equal_g = (
        "g(x1^2)=g(x2^2)" in c
        or "g(x_1^2)=g(x_2^2)" in c
        or "mesmo valor" in t
        or "valores iguais" in t
    )

    if uses_functional_hypothesis and concludes_equal_g:
        claims.append(
            make_claim(
                claim_id="q4_c4",
                claim_type="equal_g_values",
                text="Usa a hipótese funcional para concluir que g(x1^2) = g(x2^2).",
                evidence="A solução aplica g(x^2)=f(2x^2-x+1) aos dois valores escolhidos e conclui igualdade dos valores de g.",
                confidence=0.95,
                normalized={"equal_values": "g(x1^2) = g(x2^2)"},
            )
        )

    concludes_not_injective = (
        "g nao e injetora" in t
        or "g nao e injetiva" in t
        or "g não é injetora" in solution.lower()
        or "g não é injetiva" in solution.lower()
        or "nao injetora" in t
        or "nao injetiva" in t
    )

    if concludes_not_injective:
        claims.append(
            make_claim(
                claim_id="q4_c5",
                claim_type="not_injective_conclusion",
                text="Conclui corretamente que g não é injetora.",
                evidence="A solução conclui que g não é injetora.",
                confidence=0.98,
                normalized={"conclusion": "g_not_injective"},
            )
        )

    return ClaimExtraction(
        problem_id="ITA2025Q4",
        claims=claims,
        formal_steps=[],
    )
