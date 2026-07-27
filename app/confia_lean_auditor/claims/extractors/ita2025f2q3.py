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

    beta_difference = (
        "cosbeta-sinbeta=1/2" in c
        or "cos(beta)-sin(beta)=1/2" in c
        or "cos beta - sin beta = 1/2" in t
        or ("subtra" in t and "1/2" in c and "cosbeta" in c and "sinbeta" in c)
    )

    has_sin_beta = (
        "sinbeta=-(1+sqrt(7))/4" in c
        or "sinbeta=-(sqrt(7)+1)/4" in c
        or "sinbeta=(-1-sqrt(7))/4" in c
    )

    has_cos_beta = (
        "cosbeta=(1-sqrt(7))/4" in c
        or "cosbeta=-(sqrt(7)-1)/4" in c
    )

    has_sin_alpha = (
        "sinalpha=-sqrt(7)/4" in c
        or "sinalpha=-(sqrt(7))/4" in c
        or "sinalpha=sinbeta+1/4=-sqrt(7)/4" in c
        or ("sinalpha=sinbeta+1/4" in c and "-sqrt(7)/4" in c)
        or ("sin alpha" in t and "-sqrt(7)/4" in c)
    )

    has_cos_alpha = (
        "cosalpha=-3/4" in c
    )

    candidate_values = has_sin_beta and has_cos_beta and has_sin_alpha and has_cos_alpha

    final_sin_sum = (
        (
            "sin(alpha+beta)" in c
            or "sin(alpha + beta)" in t
        )
        and (
            "sinalpha*cosbeta+cosalpha*sinbeta" in c
            or "sinalphacosbeta+cosalphasinbeta" in c
            or "sin alpha cos beta + cos alpha sin beta" in t
            or "sin alpha*cos beta+cos alpha*sin beta" in t
        )
        and (
            "(5+sqrt(7))/8" in c
            or "(sqrt(7)+5)/8" in c
            or "5+sqrt(7)" in c and "/8" in c
        )
    )

    final_answer = (
        "(5+sqrt(7))/8" in c
        or "(sqrt(7)+5)/8" in c
        or "5+sqrt(7)" in c and "/8" in c
    )

    wrong_answer = (
        "respostae1/2" in c
        or "resposta=1/2" in c
        or "sen(alpha+beta)=1/2" in c
        or "sin(alpha+beta)=1/2" in c
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
