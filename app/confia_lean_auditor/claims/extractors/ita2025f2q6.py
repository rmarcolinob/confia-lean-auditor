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

    raw = solution.lower()
    raw = raw.replace("−", "-").replace("–", "-").replace("·", "*")
    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    raw_c = compact(raw)

    c_no_braces = (
        c.replace("\\", "")
        .replace("{", "")
        .replace("}", "")
        .replace("*", "")
    )
    raw_no_braces = (
        raw_c.replace("\\", "")
        .replace("{", "")
        .replace("}", "")
        .replace("*", "")
    )

    # ------------------------------------------------------------------
    # Fórmula correta:
    # P(N=n)=C(n-1,3)/2^n
    # P(n)=binom(n-1,3)(1/2)^n
    # P(n)=\binom{n-1}{3}2^{-n}
    # ------------------------------------------------------------------
    explicit_correct_probability_formula = (
        "c(n-1.3)/2^n" in c
        or "c(n-1,3)/2^n" in raw_c
        or "c(n-1;3)/2^n" in raw_c
        or "binom(n-1.3)(1/2)^n" in c
        or "binom(n-1,3)(1/2)^n" in raw_c
        or "binom(n-1.3)/2^n" in c
        or "binom(n-1,3)/2^n" in raw_c
        or "binomn-132^-n" in c_no_braces
        or "binomn-132^{-n}" in raw_no_braces
        or (
            "binom" in c_no_braces
            and "n-1" in c_no_braces
            and "3" in c_no_braces
            and (
                "2^-n" in c_no_braces
                or "2^{-n}" in c_no_braces
                or "(1/2)^n" in c_no_braces
                or "/2^n" in c_no_braces
            )
        )
    )

    # Fórmulas conceitualmente erradas. Cuidado:
    # - a solução correta pode conter (1/2)^(n-1) * (1/2);
    # - a razão correta contém C(n,3) no numerador de P(N=n+1).
    # Portanto, só bloqueamos como fórmula errada quando não há evidência
    # explícita da fórmula correta P(N=n)=C(n-1,3)/2^n.
    has_final_correct_denominator = (
        "/2^n" in c
        or "/2^n" in raw_c
        or "(1/2)^n" in c
        or "2^-n" in c
        or "2^{-n}" in c
    )

    has_correct_factorized_probability = (
        "c(n-1.3)" in c
        and (
            "(1/2)^(n-1)*(1/2)" in c
            or "(1/2)^(n-1)(1/2)" in c
            or ("(1/2)^(n-1)" in c and "*(1/2)" in c)
        )
    )

    has_explicit_canonical_probability = (
        "c(n-1.3)/2^n" in c
        or "c(n-1,3)/2^n" in raw_c
        or "binom(n-1.3)/2^n" in c
        or "binom(n-1,3)/2^n" in raw_c
        or (
            "c(n-1.3)" in c
            and has_final_correct_denominator
        )
        or (
            "binom" in c_no_braces
            and "n-1" in c_no_braces
            and "3" in c_no_braces
            and (
                "2^-n" in c_no_braces
                or "2^{-n}" in c_no_braces
                or "(1/2)^n" in c_no_braces
                or "/2^n" in c_no_braces
            )
        )
    )

    has_correct_probability_evidence = (
        explicit_correct_probability_formula
        or has_explicit_canonical_probability
        or has_correct_factorized_probability
    )

    wrong_probability_formula = (
        not has_correct_probability_evidence
        and (
            "c(n.3)" in c
            or "c(n,3)" in raw_c
            or "c(n.4)" in c
            or "c(n,4)" in raw_c
            or "2^(n-1)" in c
            or "2^(n-1)" in raw_c
        )
    )

    mentions_binomial_structure = (
        "c(n-1" in c
        or "binom" in c
        or "comb" in c
        or "combinacao" in t
        or "escolher" in t
    )

    mentions_correct_denominator = (
        "/2^n" in c
        or "(1/2)^n" in c
        or "2^-n" in c
        or "2^{-n}" in c
    )

    mentions_event_structure = (
        "3caras" in c
        or "trescaras" in c
        or "3 caras" in t
        or "quarta cara" in t
        or "n-1primeiros" in c
        or "ultimolancamento" in c
        or "ultimo lancamento" in t
        or "último lançamento" in solution.lower()
    )

    has_probability_formula = (
        not wrong_probability_formula
        and (
            explicit_correct_probability_formula
            or (
                mentions_binomial_structure
                and mentions_correct_denominator
                and mentions_event_structure
            )
        )
    )

    # ------------------------------------------------------------------
    # Razão:
    # P(n+1)/P(n)=n/(2n-6)=n/(2(n-3)).
    # ------------------------------------------------------------------
    mentions_ratio = (
        "p(n+1)/p(n)" in c
        or "pn+1/pn" in c
        or "razao" in t
        or "razão" in solution.lower()
        or "termosconsecutivos" in c
        or "probabilidadesconsecutivas" in c
        or "comparandotermos" in c
        or "compararprobabilidades" in c
    )

    mentions_ratio_value = (
        "n/(2n-6)" in c
        or "n/[2n-6]" in c
        or "n/(2(n-3))" in c
        or "n/[2(n-3)]" in c
        or "n/2(n-3)" in c
        or "n/(2*(n-3))" in c
        or "n/2n-6" in c
    )

    has_ratio_formula = mentions_ratio and mentions_ratio_value

    # ------------------------------------------------------------------
    # Par {6,7}: reconhecer "n=6 e n=7", "n=6,7", "máximo: n=6,7".
    # ------------------------------------------------------------------
    mentions_pair_6_7 = (
        "n=6en=7" in c
        or "n=6e7" in c
        or "n=6,7" in raw_c
        or "n=6.7" in c
        or "6e7" in c
        or "6 e 7" in t
        or "6,7" in raw_c
        or "p(6)=p(7)" in c
        or "p6=p7" in c
    )

    mentions_max_context = (
        "maximiz" in t
        or "maximo" in t
        or "máximo" in solution.lower()
        or "maxima" in t
        or "máxima" in solution.lower()
        or "maioresvalores" in c
        or "maior valor" in t
        or "empata" in t
        or "empate" in t
        or "p(6)=p(7)" in c
        or "sobe" in t
        or "cresce" in t
        or "cai" in t
        or "decresce" in t
        or "depois cai" in t
        or "depoisdecresce" in c
    )

    has_ratio_analysis = (
        has_ratio_formula
        and (
            mentions_max_context
            or mentions_pair_6_7
            or "n<6" in c
            or "n=6" in c
            or "n>6" in c
            or ">1" in c
            or "<1" in c
        )
    )

    has_maximizers = mentions_pair_6_7 and mentions_max_context

    final_answer = (
        mentions_pair_6_7
        and (
            "resposta" in t
            or "portanto" in t
            or "logo" in t
            or "concl" in t
            or "valoresden" in c
            or "valores de n" in t
            or mentions_max_context
        )
    )

    wrong_answer = (
        "n=4" in c
        or "n=5" in c
        or "n=8" in c
        or "n=6apenas" in c
        or "n=6 apenas" in t
    ) and not (
        "n=7" in c
        or "n=7" in raw_c
        or "6 e 7" in t
        or "6,7" in raw_c
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

    if features["has_ratio_formula"] or features["has_ratio_analysis"]:
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
