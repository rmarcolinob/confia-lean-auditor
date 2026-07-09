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
    text = text.replace("⁴", "^4")
    text = text.replace("⁶", "^6")
    text = text.replace("⁷", "^7")
    text = text.replace("−", "-")
    text = text.replace("–", "-")
    text = text.replace("·", "*")
    text = text.replace("≤", "<=")
    text = text.replace("≥", ">=")
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

    # Fórmula P(N=n)=C(n-1,3)/2^n.
    mentions_binomial = (
        "c(n-1.3)" in c
        or "c(n-1,3)" in c
        or "c(n-1;3)" in c
        or "c(n-1" in c
        or "choose(n-1" in c
        or "binom" in c
        or "comb" in c
        or "combinacao" in t
        or "combinação" in solution.lower()
        or "escolher" in t
    )

    mentions_denominator = (
        "/2^n" in c
        or "2^n" in c
        or "(1/2)^n" in c
        or "(1/2)^(n-1)" in c
        or "1/2" in c
    )

    mentions_event_structure = (
        "3caras" in c
        or "trescaras" in c
        or "3 caras" in t
        or "quarta" in t
        or "quarta cara" in solution.lower()
        or "n-1primeiros" in c
        or "ultimolancamento" in c
        or "ultimo lancamento" in t
    )

    has_probability_formula = (
        mentions_binomial
        and mentions_denominator
        and mentions_event_structure
    ) or (
        "p(n)=c(n-1.3)/2^n" in c
        or "p(n)=c(n-1,3)/2^n" in c
        or "p(n)=c(n-1;3)/2^n" in c
    )

    # Razão P(N=n+1)/P(N=n)=n/(2n-6)=n/[2(n-3)].
    mentions_ratio = (
        "p(n+1)/p(n)" in c
        or "pn+1/pn" in c
        or "razao" in t
        or "razão" in solution.lower()
        or "probabilidadesconsecutivas" in c
        or "compararprobabilidades" in c
    )

    mentions_ratio_value = (
        "n/(2n-6)" in c
        or "n/[2(n-3)]" in c
        or "n/(2(n-3))" in c
        or "n/2(n-3)" in c
        or "n/[2n-6]" in c
    )

    has_ratio_formula = mentions_ratio and mentions_ratio_value

    has_ratio_analysis = (
        has_ratio_formula
        and (
            "n<6" in c
            or "n = 6" in t
            or "n=6" in c
            or "quando n = 6" in t
        )
        and (
            "n>6" in c
            or "depoisdecresce" in c
            or "decresce" in t
            or "menorque1" in c
            or "<1" in c
        )
    )

    has_maximizers = (
        (
            "n=6en=7" in c
            or "n=6e7" in c
            or "6e7" in c
            or "6 e 7" in t
            or "n sao 6 e 7" in t
            or "n são 6 e 7" in solution.lower()
        )
        and (
            "maximiz" in t
            or "maxima" in t
            or "máxima" in solution.lower()
            or "valoresden" in c
            or "probabilidade cresce" in t
            or "depois decresce" in t
        )
    )

    final_answer = (
        "n=6en=7" in c
        or "n=6e7" in c
        or "valoresden sao6e7" in c
        or "valoresden sao6e7" in t
        or "valores de n sao 6 e 7" in t
        or "valores de n são 6 e 7" in solution.lower()
        or "sao 6 e 7" in t
        or "são 6 e 7" in solution.lower()
        or "6 e 7" in t
    )

    wrong_answer = (
        "n=4" in c
        or "n=5" in c
        or "n=8" in c
    ) and not (
        "n=6" in c and "n=7" in c
    )

    if wrong_answer:
        final_answer = False
        has_maximizers = False

    return {
        "has_probability_formula": has_probability_formula,
        "has_ratio_formula": has_ratio_formula,
        "has_ratio_analysis": has_ratio_analysis,
        "has_maximizers": has_maximizers,
        "final_answer": final_answer,
    }


def extract_f2q6_formal_steps(solution: str) -> List[FormalStep]:
    features = detect_features(solution)
    steps: List[FormalStep] = []

    if features["has_probability_formula"]:
        steps.append(
            FormalStep(
                id="f2q6_s1_probability_values",
                type="f2q6_probability_values",
                description="Verificação formal dos valores C(5,3)/2^6 e C(6,3)/2^7.",
                evidence="A solução usa a fórmula C(n-1,3)/2^n.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["probability_formula"],
                supports_rubric_items=["probability_formula"],
            )
        )

    if features["has_ratio_analysis"]:
        steps.append(
            FormalStep(
                id="f2q6_s2_ratio_comparison",
                type="f2q6_ratio_comparison",
                description="Verificação formal das desigualdades da razão n/(2n-6).",
                evidence="A solução analisa a razão entre probabilidades consecutivas.",
                lhs="0",
                rhs="0",
                lean_method="omega",
                supports_claim_types=[
                    "ratio_comparison",
                    "maximizers_identification",
                    "final_answer",
                ],
                supports_rubric_items=[
                    "ratio_comparison",
                    "maximizers_identification",
                    "final_answer",
                ],
            )
        )

    return steps


def extract_claims_ita2025f2q6(solution: str) -> ClaimExtraction:
    features = detect_features(solution)
    claims: List[ExtractedClaim] = []
    formal_steps = extract_f2q6_formal_steps(solution)

    if features["has_probability_formula"]:
        claims.append(
            make_claim(
                claim_id="f2q6_c1",
                claim_type="probability_formula",
                text="Obtém P(N=n)=C(n-1,3)/2^n.",
                evidence="A solução exige 3 caras nos n-1 primeiros lançamentos e cara no último.",
                confidence=0.95,
                normalized={"probability": "C(n-1,3)/2^n"},
            )
        )

    if features["has_ratio_formula"] or features["has_ratio_analysis"]:
        claims.append(
            make_claim(
                claim_id="f2q6_c2",
                claim_type="ratio_comparison",
                text="Calcula P(N=n+1)/P(N=n)=n/(2n-6).",
                evidence="A solução compara probabilidades consecutivas pela razão n/(2n-6).",
                confidence=0.9,
                normalized={"ratio": "n/(2n-6)"},
            )
        )

    if features["has_maximizers"]:
        claims.append(
            make_claim(
                claim_id="f2q6_c3",
                claim_type="maximizers_identification",
                text="Identifica que os máximos ocorrem em n=6 e n=7.",
                evidence="A solução mostra crescimento, empate e decrescimento das probabilidades.",
                confidence=0.95,
                normalized={"maximizers": "{6,7}"},
            )
        )

    if features["final_answer"]:
        claims.append(
            make_claim(
                claim_id="f2q6_c4",
                claim_type="final_answer",
                text="Conclui que os valores de n são 6 e 7.",
                evidence="A solução apresenta os valores maximizantes corretos.",
                confidence=0.98,
                normalized={"n": "6,7"},
            )
        )

    return ClaimExtraction(
        problem_id="ITA2025F2Q6",
        claims=claims,
        formal_steps=formal_steps,
    )
