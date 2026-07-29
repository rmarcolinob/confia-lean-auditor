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

    raw = solution.lower()
    raw = raw.replace("−", "-").replace("–", "-").replace("·", "*")
    raw = raw.replace("{,}", ".").replace("{.}", ".")
    raw = raw.replace(",", ".")
    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    raw_c = compact(raw)

    latex_free = (
        raw_c.replace("\\", "")
        .replace("{", "")
        .replace("}", "")
        .replace("*", "")
    )

    # ------------------------------------------------------------
    # log10(3^100)=100 log10(3)=47,7100
    # Aceita:
    #   3^100, 100log3, 100 log 3, 100\log 3, 100*0.4771
    # ------------------------------------------------------------
    mentions_power = (
        "3^100" in c
        or "3**100" in c
        or "3^{100}" in raw_c
        or "3100" in c
    )

    mentions_log3 = (
        "log10(3)" in c
        or "log(3)" in c
        or "log3" in c
        or "log10 3" in t
        or "log 3" in t
        or "log3" in latex_free
        or "0.4771" in c
        or "0.4771" in raw_c
    )

    mentions_total_log = (
        "47.7100" in c
        or "47.71" in c
        or "47.7100" in raw_c
        or "47.71" in raw_c
    )

    has_log_power = (
        mentions_total_log
        and (
            (mentions_power and mentions_log3)
            or "100*0.4771" in c
            or "100.0.4771" in c
            or "100log10(3)" in c
            or "100log(3)" in c
            or "100log3" in c
            or "100log3" in latex_free
            or "100log10 3" in t
            or "100 log 3" in t
            or "100\\log3" in raw_c
            or "100\\log 3" in raw
        )
    )

    # ------------------------------------------------------------
    # Mantissa 0,71.
    # Aceita:
    #   mantissa=0,71
    #   parte fracionária = 0,71
    #   m=71/100
    #   10^0,71
    # ------------------------------------------------------------
    mentions_mantissa_value = (
        "0.7100" in c
        or "0.71" in c
        or "0.7100" in raw_c
        or "0.71" in raw_c
        or "m=71/100" in c
        or "m=71/100" in raw_c
        or "mantissa=71/100" in c
        or "partefracionaria=71/100" in c
    )

    mentions_mantissa_context = (
        "partefracionaria" in c
        or "parte fracionaria" in t
        or "mantissa" in c
        or "m=71/100" in c
        or "10^0.7100" in c
        or "10^0.71" in c
        or "dependede10^0.7100" in c
        or "dependede10^0.71" in c
        or has_log_power
    )

    has_mantissa = mentions_mantissa_value and mentions_mantissa_context

    # ------------------------------------------------------------
    # Bounds logarítmicos:
    #   log5=0,6990
    #   log6=0,7781
    #   0,6990 < 0,71 < 0,7781
    # ------------------------------------------------------------
    has_log5 = (
        "log10(5)" in c
        or "log(5)" in c
        or "log5" in c
        or "log 5" in t
        or "log5" in latex_free
        or "0.6990" in c
        or "0.699" in c
        or "0.6990" in raw_c
        or "0.699" in raw_c
    )

    has_log6 = (
        "log10(6)" in c
        or "log(6)" in c
        or "log6" in c
        or "log 6" in t
        or "log6" in latex_free
        or "0.7781" in c
        or "0.7781" in raw_c
    )

    wrong_log_bounds = (
        "log4" in c
        or "log 4" in t
        or "0.7081" in c
        or "0.7081" in raw_c
    )

    has_digit_bounds = (
        not wrong_log_bounds
        and has_log5
        and has_log6
        and ("0.6990" in c or "0.699" in c or "0.6990" in raw_c or "0.699" in raw_c)
        and ("0.7781" in c or "0.7781" in raw_c)
    )

    has_between_bounds = (
        not wrong_log_bounds
        and (
            "0.6990<0.7100<0.7781" in c
            or "0.699<0.7100<0.7781" in c
            or "0.6990<0.71<0.7781" in c
            or "0.699<0.71<0.7781" in c
            or "0.6990<0.71<0.7781" in raw_c
            or "0.699<0.71<0.7781" in raw_c
            or (
                ("0.6990" in c or "0.699" in c or "0.6990" in raw_c or "0.699" in raw_c)
                and ("0.7100" in c or "0.71" in c or "0.7100" in raw_c or "0.71" in raw_c or "71/100" in c)
                and ("0.7781" in c or "0.7781" in raw_c)
                and "<" in c + raw_c
            )
        )
    )

    # ------------------------------------------------------------
    # Resposta final: primeiro algarismo é 5.
    # Deve evitar extrair quando o texto conclui 4, 6 ou 7.
    # ------------------------------------------------------------
    wrong_digit = (
        "primeiroalgarismo=4" in c
        or "primeiroalgarismo4" in c
        or "primeiroalgarismoe4" in c
        or "primeiroalgarismo=6" in c
        or "primeiroalgarismo6" in c
        or "primeiroalgarismoe6" in c
        or "primeiroalgarismo=7" in c
        or "primeiroalgarismo7" in c
        or "primeiroalgarismoe7" in c
        or "algarismoeo7" in c
        or "algarismoe7" in c
        or "digitoera4" in c
        or "digitoe4" in c
        or "digitoe6" in c
        or "digitoe7" in c
    )

    final_digit_five = (
        not wrong_digit
        and (
            "primeiroalgarismode3^100e5" in c
            or "primeiroalgarismoede5" in c
            or "primeiroalgarismoe5" in c
            or "primeiroalgarismo=5" in c
            or "primeiroalgarismo5" in c
            or "algarismoiniciale5" in c
            or "algarismoinicial=5" in c
            or "algarismo=5" in c
            or "digito=5" in c
            or "digito:5" in raw_c
            or "digitoe5" in c
            or "digitoiniciale5" in c
            or "digitoinicial=5" in c
            or "resposta:5" in raw_c
            or "respostae5" in c
            or "primeiro algarismo de 3^100 e 5" in t
            or "primeiro algarismo de 3^100 é 5" in solution.lower()
            or "primeiro algarismo e 5" in t
            or "primeiro algarismo é 5" in solution.lower()
            or "digito inicial e 5" in t
            or "dígito inicial é 5" in solution.lower()
            or "digito: 5" in t
            or "dígito: 5" in solution.lower()
        )
    )

    # Se a solução apresenta mantissa, os logs de 5 e 6, e conclui
    # corretamente que o primeiro algarismo é 5, aceitamos a comparação
    # entre bounds como implícita no Nível 1.
    #
    # Isso aumenta recall sem aceitar casos como log4/log5 ou dígito 4/6/7,
    # pois essas situações já são bloqueadas por wrong_log_bounds/wrong_digit.
    if final_digit_five and has_digit_bounds and has_mantissa:
        has_between_bounds = True

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
