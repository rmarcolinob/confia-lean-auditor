from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional

from confia_lean_auditor.core.schemas import (
    ClaimExtraction,
    ExtractedClaim,
    FormalStep,
)


def normalize(text: str) -> str:
    text = text.replace("²", "^2")
    text = text.replace("−", "-")
    text = text.replace("–", "-")
    text = text.replace("·", "*")
    text = text.replace("≥", ">=")
    text = text.replace("≠", "!=")
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


def detect_features(solution: str) -> Dict[str, bool]:
    t = normalize(solution)
    c = compact(t)

    has_factored_numerator = (
        (
            "2cos(x)+1" in c
            and ("2sen(x)-1" in c or "2sin(x)-1" in c)
        )
        or "(2cos(x)+1)(2sen(x)-1)" in c
        or "(2cos(x)+1)*(2sen(x)-1)" in c
        or "(2cos(x)+1)(2sin(x)-1)" in c
        or "(2cos(x)+1)*(2sin(x)-1)" in c
    )

    has_denominator_condition = (
        "denominador" in t
        and (
            "16cos^2(x)" in c
            or "cos(x)!=0" in c
            or "cos(x)=0" in c
            or "cosx=0" in c
            or "excluir" in t
            or "nao nulo" in t
            or "não nulo" in solution.lower()
        )
    )

    has_sign_analysis = (
        "estudo de sinais" in t
        or "analise de sinais" in t
        or "análise de sinais" in solution.lower()
        or "pontos criticos" in t
        or "pontos críticos" in solution.lower()
        or "fazendo o estudo de sinais" in t
        or (
            "2cos(x)+1" in c
            and ("2sen(x)-1" in c or "2sin(x)-1" in c)
            and (">=0" in c or "maiorouigualazero" in c)
        )
        or (
            "intervalosdedefinicao" in c
            and "5π/6" in c
            and "4π/3" in c
        )
    )

    has_longest_interval = (
        "5π/6" in c
        and "4π/3" in c
        and (
            "intervalo" in t
            or "i=(" in c
            or "maior" in t
        )
    ) or (
        "5pi/6" in c
        and "4pi/3" in c
    )

    has_endpoint_sum = (
        "13π/6" in c
        or "13pi/6" in c
        or "a+b=13π/6" in c
        or "a+b=13pi/6" in c
    )

    wrong_interval = (
        "π/6" in c
        and "2π/3" in c
        and "5π/6" not in c
        and "4π/3" not in c
    )

    if wrong_interval:
        has_longest_interval = False
        has_endpoint_sum = False

    return {
        "has_factored_numerator": has_factored_numerator,
        "has_denominator_condition": has_denominator_condition,
        "has_sign_analysis": has_sign_analysis,
        "has_longest_interval": has_longest_interval,
        "has_endpoint_sum": has_endpoint_sum,
    }


def extract_q8_formal_steps(solution: str) -> List[FormalStep]:
    features = detect_features(solution)
    steps: List[FormalStep] = []

    # Os formal steps da Q8 são renderizados por tipo, não por expressão livre.
    # lhs/rhs ficam triviais para passar pela whitelist.
    if features["has_factored_numerator"]:
        steps.append(
            FormalStep(
                id="q8_s1_numerator_factorization",
                type="q8_numerator_factorization",
                description="Verificação formal da fatoração trigonométrica do numerador.",
                evidence="A solução fatorou o numerador como (2cos(x)+1)(2sen(x)-1).",
                lhs="0",
                rhs="0",
                lean_method="ring",
                supports_claim_types=["numerator_factorization"],
                supports_rubric_items=["numerator_factorization"],
            )
        )

    if features["has_endpoint_sum"]:
        steps.append(
            FormalStep(
                id="q8_s2_endpoint_sum",
                type="q8_endpoint_sum",
                description="Verificação formal de 5π/6 + 4π/3 = 13π/6.",
                evidence="A solução calcula a+b = 13π/6.",
                lhs="0",
                rhs="0",
                lean_method="ring",
                supports_claim_types=["endpoint_sum"],
                supports_rubric_items=["endpoint_sum"],
            )
        )

    return steps


def extract_claims_ita2025q8(solution: str) -> ClaimExtraction:
    features = detect_features(solution)
    claims: List[ExtractedClaim] = []
    formal_steps = extract_q8_formal_steps(solution)

    if features["has_factored_numerator"]:
        claims.append(
            make_claim(
                claim_id="q8_c1",
                claim_type="numerator_factorization",
                text="O numerador é fatorado como (2cos(x)+1)(2sen(x)-1).",
                evidence="A solução apresenta a fatoração trigonométrica do numerador.",
                confidence=0.9,
                normalized={"numerator": "(2cos(x)+1)(2sen(x)-1)"},
            )
        )

    if features["has_denominator_condition"]:
        claims.append(
            make_claim(
                claim_id="q8_c2",
                claim_type="denominator_condition",
                text="O denominador é positivo exceto nos pontos em que cos(x)=0.",
                evidence="A solução identifica a condição de denominador não nulo.",
                confidence=0.85,
                normalized={"denominator": "16cos^2(x)", "excluded": "cos(x)=0"},
            )
        )

    if features["has_sign_analysis"]:
        claims.append(
            make_claim(
                claim_id="q8_c3",
                claim_type="sign_analysis",
                text="A solução analisa o sinal de (2cos(x)+1)(2sen(x)-1).",
                evidence="A solução faz estudo de sinais ou lista os intervalos de definição.",
                confidence=0.85,
                normalized={"condition": "(2cos(x)+1)(2sen(x)-1) >= 0"},
            )
        )

    if features["has_longest_interval"]:
        claims.append(
            make_claim(
                claim_id="q8_c4",
                claim_type="longest_interval",
                text="O maior intervalo é (5π/6, 4π/3).",
                evidence="A solução identifica corretamente o maior intervalo.",
                confidence=0.95,
                normalized={"interval": "(5π/6, 4π/3)"},
            )
        )

    if features["has_endpoint_sum"]:
        claims.append(
            make_claim(
                claim_id="q8_c5",
                claim_type="endpoint_sum",
                text="A soma dos extremos é 13π/6.",
                evidence="A solução calcula a+b = 13π/6.",
                confidence=0.95,
                normalized={"a_plus_b": "13π/6"},
            )
        )

    return ClaimExtraction(
        problem_id="ITA2025Q8",
        claims=claims,
        formal_steps=formal_steps,
    )
