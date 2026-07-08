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


def has_regex(pattern: str, text: str) -> bool:
    return re.search(pattern, text) is not None


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

    has_first_exponent = (
        has_regex(r"6\s*-\s*2\s*\*?\s*i", t)
        or ("expoente" in t and "(x+1/x)^6" in c)
        or ("termo geral" in t and "(x+1/x)^6" in c)
    )

    has_second_exponent = (
        has_regex(r"5\s*-\s*2\s*\*?\s*j", t)
        or ("expoente" in t and "(x-2/x)^5" in c)
        or ("termo geral" in t and "(x-2/x)^5" in c)
    )

    has_product_exponent = (
        has_regex(r"11\s*-\s*2\s*\*?\s*i\s*-\s*2\s*\*?\s*j", t)
        or "11-2i-2j" in c
        or "11-2*i-2*j" in c
    )

    has_exponent_balance = (
        has_product_exponent
        and (
            "=0" in c
            or "expoentezero" in c
            or "termoindependente" in c
            or "termo independente" in t
        )
    )

    has_parity_obstruction = (
        "impar" in t
        or "paridade" in t
        or "nunca pode ser zero" in t
        or "nunca e zero" in t
        or "nao pode ser zero" in t
        or "nao e zero" in t
        or "não pode ser zero" in solution.lower()
    )

    final_answer_zero = (
        "termoindependentee0" in c
        or "termoindependente=0" in c
        or "termoindependente:0" in c
        or "termo independente e 0" in t
        or "termo independente é 0" in solution.lower()
        or "resposta:0" in c
        or "respostae0" in c
        or "resposta é 0" in solution.lower()
    )

    return {
        "has_first_exponent": has_first_exponent,
        "has_second_exponent": has_second_exponent,
        "has_product_exponent": has_product_exponent,
        "has_exponent_balance": has_exponent_balance,
        "has_parity_obstruction": has_parity_obstruction,
        "final_answer_zero": final_answer_zero,
    }


def extract_q3_formal_steps(solution: str) -> List[FormalStep]:
    features = detect_features(solution)

    steps: List[FormalStep] = []

    if features["has_product_exponent"] and features["has_parity_obstruction"]:
        steps.append(
            FormalStep(
                id="q3_s1_no_zero_exponent",
                type="q3_no_zero_exponent",
                description="Verificação formal de que 11 - 2i - 2j nunca é zero.",
                evidence="A solução usa paridade para afirmar que 11 - 2i - 2j não pode ser zero.",
                lhs="11 - 2 * i - 2 * j",
                rhs="0",
                lean_method="omega",
                supports_claim_types=["exponent_balance", "parity_obstruction"],
                supports_rubric_items=["exponent_balance", "parity_obstruction"],
            )
        )

    return steps


def extract_claims_ita2025q3(solution: str) -> ClaimExtraction:
    features = detect_features(solution)

    claims: List[ExtractedClaim] = []
    formal_steps = extract_q3_formal_steps(solution)

    if features["has_first_exponent"]:
        claims.append(
            make_claim(
                claim_id="q3_c1",
                claim_type="first_factor_exponent_form",
                text="Os expoentes dos termos de (x + 1/x)^6 têm a forma 6 - 2i.",
                evidence="A solução identifica a forma 6 - 2i para os expoentes do primeiro fator.",
                confidence=0.9,
                normalized={"first_exponent": "6 - 2i"},
            )
        )

    if features["has_second_exponent"]:
        claims.append(
            make_claim(
                claim_id="q3_c2",
                claim_type="second_factor_exponent_form",
                text="Os expoentes dos termos de (x - 2/x)^5 têm a forma 5 - 2j.",
                evidence="A solução identifica a forma 5 - 2j para os expoentes do segundo fator.",
                confidence=0.9,
                normalized={"second_exponent": "5 - 2j"},
            )
        )

    if features["has_exponent_balance"]:
        claims.append(
            make_claim(
                claim_id="q3_c3",
                claim_type="exponent_balance",
                text="Para haver termo independente, seria necessário 11 - 2i - 2j = 0.",
                evidence="A solução monta a condição de expoente zero.",
                confidence=0.95,
                normalized={"exponent_condition": "11 - 2i - 2j = 0"},
            )
        )

    if features["has_parity_obstruction"]:
        claims.append(
            make_claim(
                claim_id="q3_c4",
                claim_type="parity_obstruction",
                text="Como 11 - 2i - 2j é ímpar, ele nunca pode ser zero.",
                evidence="A solução usa paridade para excluir expoente zero.",
                confidence=0.95,
                normalized={"obstruction": "odd exponent"},
            )
        )

    if features["final_answer_zero"]:
        claims.append(
            make_claim(
                claim_id="q3_c5",
                claim_type="final_answer_zero",
                text="O termo independente é 0.",
                evidence="A solução conclui que o termo independente é 0.",
                confidence=0.98,
                normalized={"answer": "0"},
            )
        )

    return ClaimExtraction(
        problem_id="ITA2025Q3",
        claims=claims,
        formal_steps=formal_steps,
    )
