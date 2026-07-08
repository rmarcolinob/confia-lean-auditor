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

    has_difference_relation = (
        (
            "b_{n+1}-b_n" in c
            or "b_{n+1}-bn" in c
            or "b(n+1)-b(n)" in c
            or "bn+1-bn" in c
            or "b_{n+1}" in c and "b_n" in c and "s_n-s_{n-1}" in c
            or "s_n-s_{n-1}" in c
            or "sn-s{n-1}" in c
            or "sn-sn-1" in c
        )
        and (
            "a_n" in c
            or "an" in c
        )
    )

    has_geometric_form = (
        "b_n=cq^n" in c
        or "b_n=c*q^n" in c
        or "bn=cq^n" in c
        or "bn=c*q^n" in c
        or ("pg" in t and "q^n" in c and "c" in c)
        or ("progressao geometrica" in t and "q^n" in c)
    )

    has_factorization = (
        "c(q-1)q^n" in c
        or "c*(q-1)*q^n" in c
        or "c*(q-1)q^n" in c
        or "c(q-1)*q^n" in c
    )

    has_conclusion_pg = (
        "a_n tambem e uma pg" in t
        or "a_n tambem e pg" in t
        or "an tambem e uma pg" in t
        or "an tambem e pg" in t
        or "a_n e uma pg" in t
        or "a_n e pg" in t
        or "an e uma pg" in t
        or "an e pg" in t
        or "a_n tambem e uma progressao geometrica" in t
        or "a_n e uma progressao geometrica" in t
        or "sequencia (a_n) tambem e uma pg" in t
        or "(a_n) tambem e uma pg" in t
    )

    wrong_direction = (
        "se a_n e uma pg" in t
        or "se an e uma pg" in t
    ) and (
        "b_n tambem e uma pg" in t
        or "bn tambem e uma pg" in t
    )

    if wrong_direction:
        has_conclusion_pg = False

    return {
        "has_difference_relation": has_difference_relation,
        "has_geometric_form": has_geometric_form,
        "has_factorization": has_factorization,
        "has_conclusion_pg": has_conclusion_pg,
    }


def extract_q5_formal_steps(solution: str) -> List[FormalStep]:
    features = detect_features(solution)

    steps: List[FormalStep] = []

    if features["has_factorization"]:
        steps.append(
            FormalStep(
                id="q5_s1_geometric_factorization",
                type="q5_geometric_factorization",
                description="Verificação formal de c q^{n+1} - c q^n = c(q - 1)q^n.",
                evidence="A solução fatoriza c q^{n+1} - c q^n como c(q - 1)q^n.",
                lhs="c * q ^ (n + 1) - c * q ^ n",
                rhs="c * (q - 1) * q ^ n",
                lean_method="ring",
                supports_claim_types=["geometric_factorization"],
                supports_rubric_items=["geometric_factorization"],
            )
        )

    return steps


def extract_claims_ita2025q5(solution: str) -> ClaimExtraction:
    features = detect_features(solution)

    claims: List[ExtractedClaim] = []
    formal_steps = extract_q5_formal_steps(solution)

    if features["has_difference_relation"]:
        claims.append(
            make_claim(
                claim_id="q5_c1",
                claim_type="difference_relation",
                text="Da relação entre S_n e b_n, obtém-se a_n = b_{n+1} - b_n.",
                evidence="A solução deduz a diferença a_n = S_n - S_{n-1} = b_{n+1} - b_n.",
                confidence=0.9,
                normalized={"difference": "a_n = b_{n+1} - b_n"},
            )
        )

    if features["has_geometric_form"]:
        claims.append(
            make_claim(
                claim_id="q5_c2",
                claim_type="geometric_form",
                text="Como (b_n) é PG, escreve-se b_n = c q^n.",
                evidence="A solução representa a PG por b_n = c q^n.",
                confidence=0.9,
                normalized={"b_n": "c q^n"},
            )
        )

    if features["has_factorization"]:
        claims.append(
            make_claim(
                claim_id="q5_c3",
                claim_type="geometric_factorization",
                text="A solução obtém c q^{n+1} - c q^n = c(q - 1)q^n.",
                evidence="A solução apresenta a fatoração geométrica central.",
                confidence=0.95,
                normalized={"factorization": "c q^{n+1} - c q^n = c(q - 1)q^n"},
            )
        )

    if features["has_conclusion_pg"]:
        claims.append(
            make_claim(
                claim_id="q5_c4",
                claim_type="conclusion_pg",
                text="A sequência (a_n) também é uma PG.",
                evidence="A solução conclui que (a_n) é progressão geométrica.",
                confidence=0.95,
                normalized={"conclusion": "a_n is PG"},
            )
        )

    return ClaimExtraction(
        problem_id="ITA2025Q5",
        claims=claims,
        formal_steps=formal_steps,
    )
