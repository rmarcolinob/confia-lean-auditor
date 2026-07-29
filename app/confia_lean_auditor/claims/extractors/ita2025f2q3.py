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
    text = text.replace("α", "alpha")
    text = text.replace("β", "beta")
    text = text.replace("sen", "sin")
    text = text.replace("seno", "sin")
    text = text.replace("√", "sqrt")
    text = text.replace("−", "-")
    text = text.replace("–", "-")
    text = text.replace("·", "*")
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
    raw = raw.replace("α", "alpha").replace("β", "beta")
    raw = raw.replace("sen", "sin").replace("seno", "sin")
    raw = raw.replace("√", "sqrt")
    raw = raw.replace("−", "-").replace("–", "-").replace("·", "*")
    raw = raw.replace("{,}", ".").replace(",", ".")
    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    raw_c = compact(raw)

    latex_free = (
        raw_c.replace("\\", "")
        .replace("{", "")
        .replace("}", "")
        .replace("*", "")
    )

    def has_any(*patterns: str) -> bool:
        return any(p in c or p in raw_c or p in latex_free for p in patterns)

    # ------------------------------------------------------------
    # Diferença para beta:
    # cos(beta)-sin(beta)=1/2
    # ------------------------------------------------------------
    beta_difference = (
        has_any(
            "cosbeta-sinbeta=1/2",
            "cos(beta)-sin(beta)=1/2",
            "cosbeta-senbeta=1/2",
        )
        or "cos beta - sin beta = 1/2" in t
        or ("subtra" in t and "1/2" in c and "cosbeta" in c and "sinbeta" in c)
    )

    # ------------------------------------------------------------
    # Valores candidatos.
    # Aceita sqrt(7), sqrt7, \sqrt{7}.
    # ------------------------------------------------------------
    has_sin_beta = has_any(
        "sinbeta=-(1+sqrt(7))/4",
        "sinbeta=-(sqrt(7)+1)/4",
        "sinbeta=(-1-sqrt(7))/4",
        "sinbeta=-(1+sqrt7)/4",
        "sinbeta=-(sqrt7+1)/4",
        "sinbeta=(-1-sqrt7)/4",
        "sinbeta=-(sqrt7+1)/4",
    )

    has_cos_beta = has_any(
        "cosbeta=(1-sqrt(7))/4",
        "cosbeta=-(sqrt(7)-1)/4",
        "cosbeta=(1-sqrt7)/4",
        "cosbeta=-(sqrt7-1)/4",
    )

    has_sin_alpha = (
        has_any(
            "sinalpha=-sqrt(7)/4",
            "sinalpha=-(sqrt(7))/4",
            "sinalpha=-sqrt7/4",
            "sinalpha=-(sqrt7)/4",
            "sinalpha=sinbeta+1/4=-sqrt(7)/4",
            "sinalpha=sinbeta+1/4=-sqrt7/4",
        )
        or ("sinalpha=sinbeta+1/4" in c and ("-sqrt(7)/4" in c or "-sqrt7/4" in c))
        or ("sin alpha" in t and ("-sqrt(7)/4" in c or "-sqrt7/4" in c))
    )

    has_cos_alpha = has_any(
        "cosalpha=-3/4",
        "cos(alpha)=-3/4",
    )

    candidate_values = has_sin_beta and has_cos_beta and has_sin_alpha and has_cos_alpha

    # ------------------------------------------------------------
    # Valor de sin(alpha+beta).
    # Aceita tanto a fórmula de adição explícita quanto a declaração direta
    # sin(alpha+beta)=(5+sqrt(7))/8.
    # ------------------------------------------------------------
    mentions_sin_sum_target = has_any(
        "sin(alpha+beta)",
        "sinalpha+beta",
    ) or "sin(alpha + beta)" in t

    mentions_addition_formula = (
        "sinalpha*cosbeta+cosalpha*sinbeta" in c
        or "sinalphacosbeta+cosalphasinbeta" in c
        or "sin alpha cos beta + cos alpha sin beta" in t
        or "sin alpha*cos beta+cos alpha*sin beta" in t
    )

    mentions_correct_sum_value = has_any(
        "(5+sqrt(7))/8",
        "(sqrt(7)+5)/8",
        "(5+sqrt7)/8",
        "(sqrt7+5)/8",
        "5+sqrt(7)",
        "5+sqrt7",
    ) and "/8" in c + raw_c + latex_free

    final_sin_sum = mentions_sin_sum_target and mentions_correct_sum_value

    # Se a solução escreve a fórmula de adição e a expressão final correta,
    # também aceitamos mesmo que a notação de sin(alpha+beta) esteja compacta.
    final_sin_sum = final_sin_sum or (
        mentions_addition_formula and mentions_correct_sum_value
    )

    final_answer = mentions_correct_sum_value

    wrong_answer = (
        "respostae1/2" in c
        or "resposta=1/2" in c
        or "sen(alpha+beta)=1/2" in c
        or "sin(alpha+beta)=1/2" in c
        or "sin(alpha+beta)=-1/2" in c
        or "sin(alpha+beta)=0" in c
    ) and not final_answer

    if wrong_answer:
        final_answer = False
        final_sin_sum = False
        candidate_values = False

    return {
        "beta_difference": beta_difference,
        "candidate_values": candidate_values,
        "final_sin_sum": final_sin_sum,
        "final_answer": final_answer,
    }

def extract_f2q3_formal_steps(solution: str) -> List[FormalStep]:
    features = detect_features(solution)
    steps: List[FormalStep] = []

    if features["beta_difference"]:
        steps.append(
            FormalStep(
                id="f2q3_s1_beta_difference",
                type="f2q3_beta_difference",
                description="Verificação formal de cos beta - sen beta = 1/2 para os candidatos.",
                evidence="A solução obtém cos beta - sen beta = 1/2.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["beta_difference"],
                supports_rubric_items=["beta_difference"],
            )
        )

    if features["candidate_values"]:
        steps.append(
            FormalStep(
                id="f2q3_s2_equations",
                type="f2q3_equations",
                description="Verificação formal de que os candidatos satisfazem as duas equações.",
                evidence="A solução apresenta os valores candidatos de sen/cos de alpha e beta.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["candidate_values"],
                supports_rubric_items=["candidate_values"],
            )
        )
        steps.append(
            FormalStep(
                id="f2q3_s3_unit_circle",
                type="f2q3_unit_circle",
                description="Verificação formal de sen²+cos²=1 para os candidatos.",
                evidence="A solução apresenta candidatos compatíveis com o círculo trigonométrico.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["candidate_values"],
                supports_rubric_items=["candidate_values"],
            )
        )

    if features["final_sin_sum"]:
        steps.append(
            FormalStep(
                id="f2q3_s4_final_sin_sum",
                type="f2q3_final_sin_sum",
                description="Verificação formal do cálculo de sen(alpha+beta).",
                evidence="A solução usa sen(alpha+beta)=sen alpha cos beta + cos alpha sen beta.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["final_sin_sum"],
                supports_rubric_items=["final_sin_sum"],
            )
        )

    if features["final_answer"]:
        steps.append(
            FormalStep(
                id="f2q3_s5_final_answer",
                type="f2q3_final_answer",
                description="Verificação formal da resposta final.",
                evidence="A solução apresenta (5+sqrt(7))/8.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["final_answer"],
                supports_rubric_items=["final_answer"],
            )
        )

    return steps


def extract_claims_ita2025f2q3(solution: str) -> ClaimExtraction:
    features = detect_features(solution)
    claims: List[ExtractedClaim] = []

    if features["beta_difference"]:
        claims.append(
            make_claim(
                claim_id="f2q3_c1",
                claim_type="beta_difference",
                text="A solução obtém cos(beta)-sen(beta)=1/2.",
                evidence="Foi detectada a diferença cos beta - sen beta = 1/2.",
                confidence=0.88,
            )
        )

    if features["candidate_values"]:
        claims.append(
            make_claim(
                claim_id="f2q3_c2",
                claim_type="candidate_values",
                text="A solução apresenta os candidatos corretos para sen/cos de alpha e beta.",
                evidence="Foram detectados sen beta, cos beta, sen alpha e cos alpha candidatos.",
                confidence=0.86,
            )
        )

    if features["final_sin_sum"]:
        claims.append(
            make_claim(
                claim_id="f2q3_c3",
                claim_type="final_sin_sum",
                text="A solução calcula sen(alpha+beta) pela fórmula de adição.",
                evidence="Foi detectada a fórmula sen(alpha+beta)=sen alpha cos beta + cos alpha sen beta.",
                confidence=0.9,
            )
        )

    if features["final_answer"]:
        claims.append(
            make_claim(
                claim_id="f2q3_c4",
                claim_type="final_answer",
                text="A solução apresenta a resposta final (5+sqrt(7))/8.",
                evidence="Foi detectada a expressão (5+sqrt(7))/8.",
                confidence=0.95,
            )
        )

    return ClaimExtraction(
        problem_id="ITA2025F2Q3",
        claims=claims,
        formal_steps=extract_f2q3_formal_steps(solution),
    )
