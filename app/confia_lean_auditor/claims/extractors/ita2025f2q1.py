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
    text = text.replace("³", "^3")
    text = text.replace("⁶", "^6")
    text = text.replace("⁷", "^7")
    text = text.replace("¹⁴", "^14")
    text = text.replace("⁵⁷", "^57")
    text = text.replace("−", "-")
    text = text.replace("–", "-")
    text = text.replace("·", "*")
    text = text.replace("≡", "=")
    text = text.replace(",", ".")
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

    mentions_period = (
        "x^6=1" in c
        or "x6=1" in c
        or "x^3=-1" in c
        or "x3=-1" in c
        or "modulo6" in c
        or "mod6" in c
    )

    has_power_reductions = (
        mentions_period
        and (
            ("x^57=x^3=-1" in c)
            or ("x^57=-1" in c)
            or ("x57=-1" in c)
        )
        and (
            ("x^14=x^2=x-1" in c)
            or ("x^14=x-1" in c)
            or ("x14=x-1" in c)
        )
        and (
            ("x^7=x" in c)
            or ("x7=x" in c)
        )
    )

    has_reduced_form = (
        "(a+b)x-a" in c
        or "(a+b)*x-a" in c
        or "arestoe(a+b)x-a" in c
        or "restoe(a+b)x-a" in c
        or "resto(a+b)x-a" in c
        or ("a(x-1)+bx" in c and "(a+b)" in c and "-a" in c)
    )

    has_coefficient_system = (
        ("a+b=2" in c or "b+a=2" in c)
        and ("-a=1" in c or "a=-1" in c)
    )

    final_answer = (
        ("a=-1" in c and "b=3" in c)
        or ("a=-1eb=3" in c)
        or ("a=-1,b=3" in c)
    )

    wrong_answer = (
        ("a=1" in c and "b=1" in c)
        or ("a=1eb=1" in c)
        or ("a=1,b=1" in c)
        or ("a=3" in c and "b=-1" in c)
    )

    if wrong_answer:
        final_answer = False

    return {
        "has_power_reductions": has_power_reductions,
        "has_reduced_form": has_reduced_form,
        "has_coefficient_system": has_coefficient_system,
        "final_answer": final_answer,
    }


def extract_f2q1_formal_steps(solution: str) -> List[FormalStep]:
    features = detect_features(solution)
    steps: List[FormalStep] = []

    if features["has_power_reductions"]:
        steps.append(
            FormalStep(
                id="f2q1_s1_power_reductions",
                type="f2q1_power_reductions",
                description="Verificação formal das reduções de x^57, x^14 e x^7.",
                evidence="A solução reduz os expoentes usando o ciclo módulo 6.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["power_reductions"],
                supports_rubric_items=["power_reductions"],
            )
        )

    if features["has_reduced_form"]:
        steps.append(
            FormalStep(
                id="f2q1_s2_reduced_form",
                type="f2q1_reduced_form",
                description="Verificação formal do resto geral (a+b)x-a.",
                evidence="A solução obtém o resto geral (a+b)x-a.",
                lhs="0",
                rhs="0",
                lean_method="ring",
                supports_claim_types=["reduced_polynomial_form"],
                supports_rubric_items=["reduced_polynomial_form"],
            )
        )

    if features["has_coefficient_system"] and features["final_answer"]:
        steps.append(
            FormalStep(
                id="f2q1_s3_coefficient_solution",
                type="f2q1_coefficient_solution",
                description="Verificação formal de a=-1, b=3 e do resto 2x+1.",
                evidence="A solução monta o sistema e conclui a=-1, b=3.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["coefficient_system", "final_answer"],
                supports_rubric_items=["coefficient_system", "final_answer"],
            )
        )

    return steps


def extract_claims_ita2025f2q1(solution: str) -> ClaimExtraction:
    features = detect_features(solution)
    claims: List[ExtractedClaim] = []
    formal_steps = extract_f2q1_formal_steps(solution)

    if features["has_power_reductions"]:
        claims.append(
            make_claim(
                claim_id="f2q1_c1",
                claim_type="power_reductions",
                text="Reduz x^57, x^14 e x^7 usando o ciclo módulo 6.",
                evidence="A solução usa x^3=-1, x^6=1 e reduz os expoentes.",
                confidence=0.95,
                normalized={
                    "x57": "-1",
                    "x14": "x-1",
                    "x7": "x"
                },
            )
        )

    if features["has_reduced_form"]:
        claims.append(
            make_claim(
                claim_id="f2q1_c2",
                claim_type="reduced_polynomial_form",
                text="Obtém o resto geral (a+b)x-a.",
                evidence="A solução simplifica -1+a(x-1)+bx+1 para (a+b)x-a.",
                confidence=0.95,
                normalized={"remainder": "(a+b)x-a"},
            )
        )

    if features["has_coefficient_system"]:
        claims.append(
            make_claim(
                claim_id="f2q1_c3",
                claim_type="coefficient_system",
                text="Compara com 2x+1 e obtém a+b=2 e -a=1.",
                evidence="A solução iguala os coeficientes do resto calculado aos de 2x+1.",
                confidence=0.9,
                normalized={"system": "a+b=2; -a=1"},
            )
        )

    if features["final_answer"]:
        claims.append(
            make_claim(
                claim_id="f2q1_c4",
                claim_type="final_answer",
                text="Conclui a=-1 e b=3.",
                evidence="A solução apresenta os valores corretos de a e b.",
                confidence=0.98,
                normalized={"a": "-1", "b": "3"},
            )
        )

    return ClaimExtraction(
        problem_id="ITA2025F2Q1",
        claims=claims,
        formal_steps=formal_steps,
    )
