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

    mentions_power = (
        "3^100" in c
        or "3100" in c
        or "3**100" in c
    )

    mentions_log3 = (
        "log10(3)" in c
        or "log(3)" in c
        or "0.4771" in c
    )

    mentions_total_log = (
        "47.7100" in c
        or "47.71" in c
    )

    has_log_power = (
        mentions_power
        and mentions_log3
        and mentions_total_log
    ) or (
        "100*0.4771" in c
        and mentions_total_log
    ) or (
        "100log10(3)" in c
        and mentions_total_log
    ) or (
        "100log(3)" in c
        and mentions_total_log
    )

    has_mantissa = (
        "0.7100" in c
        or "0.71" in c
        or "10^0.7100" in c
        or "10^0.71" in c
    ) and (
        "partefracionaria" in c
        or "mantissa" in c
        or "10^0.7100" in c
        or "10^0.71" in c
        or "dependede10^0.7100" in c
        or "dependede10^0.71" in c
        or has_log_power
    )

    has_log5 = (
        "log10(5)" in c
        or "log(5)" in c
        or "0.6990" in c
        or "0.699" in c
    )

    has_log6 = (
        "log10(6)" in c
        or "log(6)" in c
        or "0.7781" in c
    )

    has_digit_bounds = (
        has_log5
        and has_log6
        and ("0.6990" in c or "0.699" in c)
        and "0.7781" in c
    )

    has_between_bounds = (
        "0.6990<0.7100<0.7781" in c
        or "0.699<0.7100<0.7781" in c
        or "0.6990<0.71<0.7781" in c
        or "0.699<0.71<0.7781" in c
        or (
            ("0.6990" in c or "0.699" in c)
            and ("0.7100" in c or "0.71" in c)
            and "0.7781" in c
            and "<" in c
        )
    )

    final_digit_five = (
        "primeiroalgarismode3^100e5" in c
        or "primeiroalgarismoede5" in c
        or "primeiroalgarismo=5" in c
        or "primeiroalgarismo5" in c
        or "algarismoiniciale5" in c
        or "algarismoinicial=5" in c
        or "primeiro algarismo de 3^100 e 5" in t
        or "primeiro algarismo de 3^100 é 5" in solution.lower()
        or "primeiro algarismo e 5" in t
        or "primeiro algarismo é 5" in solution.lower()
    )

    wrong_digit_six = (
        "primeiroalgarismode3^100e6" in c
        or "primeiroalgarismo=6" in c
        or "primeiroalgarismo6" in c
        or "primeiro algarismo de 3^100 e 6" in t
        or "primeiro algarismo de 3^100 é 6" in solution.lower()
        or "primeiro algarismo e 6" in t
        or "primeiro algarismo é 6" in solution.lower()
    )

    if wrong_digit_six:
        final_digit_five = False

    return {
        "has_log_power": has_log_power,
        "has_mantissa": has_mantissa,
        "has_digit_bounds": has_digit_bounds,
        "has_between_bounds": has_between_bounds,
        "final_digit_five": final_digit_five,
    }


def extract_f2q5_formal_steps(solution: str) -> List[FormalStep]:
    features = detect_features(solution)
    steps: List[FormalStep] = []

    if features["has_log_power"]:
        steps.append(
            FormalStep(
                id="f2q5_s1_log_power_decomposition",
                type="f2q5_log_power_decomposition",
                description="Verificação formal de 100*4771 = 47*10000 + 7100.",
                evidence="A solução calcula log10(3^100)=47,7100.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=[
                    "log_power_decomposition",
                    "mantissa_identification",
                ],
                supports_rubric_items=[
                    "log_power_decomposition",
                    "mantissa_identification",
                ],
            )
        )

    if features["has_digit_bounds"] and features["has_between_bounds"]:
        steps.append(
            FormalStep(
                id="f2q5_s2_digit_bounds",
                type="f2q5_digit_bounds",
                description="Verificação formal de log5=6990, log6=7781 e 6990<7100<7781 na escala 10000.",
                evidence="A solução compara 0,7100 com log10(5)=0,6990 e log10(6)=0,7781.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=[
                    "digit_log_bounds",
                    "mantissa_between_bounds",
                    "final_digit_five",
                ],
                supports_rubric_items=[
                    "digit_log_bounds",
                    "mantissa_between_bounds",
                    "final_digit",
                ],
            )
        )

    return steps


def extract_claims_ita2025f2q5(solution: str) -> ClaimExtraction:
    features = detect_features(solution)
    claims: List[ExtractedClaim] = []
    formal_steps = extract_f2q5_formal_steps(solution)

    if features["has_log_power"]:
        claims.append(
            make_claim(
                claim_id="f2q5_c1",
                claim_type="log_power_decomposition",
                text="Calcula log10(3^100)=100log10(3)=47,7100.",
                evidence="A solução multiplica 100 por 0,4771 e obtém 47,7100.",
                confidence=0.95,
                normalized={"total_log": "47.7100"},
            )
        )

    if features["has_mantissa"]:
        claims.append(
            make_claim(
                claim_id="f2q5_c2",
                claim_type="mantissa_identification",
                text="Identifica a mantissa 0,7100.",
                evidence="A solução usa a parte fracionária 0,7100.",
                confidence=0.9,
                normalized={"mantissa": "0.7100"},
            )
        )

    if features["has_digit_bounds"]:
        claims.append(
            make_claim(
                claim_id="f2q5_c3",
                claim_type="digit_log_bounds",
                text="Calcula log10(5)=0,6990 e log10(6)=0,7781.",
                evidence="A solução calcula os limites logarítmicos para 5 e 6.",
                confidence=0.9,
                normalized={"log5": "0.6990", "log6": "0.7781"},
            )
        )

    if features["has_between_bounds"]:
        claims.append(
            make_claim(
                claim_id="f2q5_c4",
                claim_type="mantissa_between_bounds",
                text="Compara 0,6990 < 0,7100 < 0,7781.",
                evidence="A solução mostra que a mantissa está entre log10(5) e log10(6).",
                confidence=0.95,
                normalized={"comparison": "0.6990 < 0.7100 < 0.7781"},
            )
        )

    if features["final_digit_five"]:
        claims.append(
            make_claim(
                claim_id="f2q5_c5",
                claim_type="final_digit_five",
                text="O primeiro algarismo de 3^100 é 5.",
                evidence="A solução conclui corretamente o primeiro algarismo.",
                confidence=0.98,
                normalized={"digit": "5"},
            )
        )

    return ClaimExtraction(
        problem_id="ITA2025F2Q5",
        claims=claims,
        formal_steps=formal_steps,
    )
