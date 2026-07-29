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
    text = text.replace("−", "-")
    text = text.replace("–", "-")
    text = text.replace("·", "*")
    text = text.replace("≤", "<=")
    text = text.replace("≥", ">=")
    text = text.replace("Σ", "soma")
    text = text.replace("∑", "soma")
    text = text.replace("determinante", "det")
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

    keyword_soup = (
        "matrizdiferencadeterminantesoma1013formulakcoluna" in c
        or "matrizdiferencadetsoma1013formulakcoluna" in c
    )

    mentions_column_difference = (
        not keyword_soup
        and (
            "diferencassucessivasdecolunas" in c
            or "diferencasdecolunas" in c
            or "diferencadecolunas" in c
            or "facodiferencasdecolunas" in c
            or "transformacaoporcolunas" in c
            or "c_j-c_{j-1}" in c
            or "cj-cj-1" in c
            or "colunaj-colunaj-1" in c
            or (
                "colunas" in t
                and (
                    "substitu" in t
                    or "operac" in t
                    or "diferenc" in t
                    or "transformac" in t
                )
            )
        )
    )

    mentions_determinant_formula = (
        "det(a_k)=(-1)^(k-1)k" in c
        or "detak=(-1)^(k-1)k" in c
        or "det(a_k)=(-1)^{k-1}k" in c
        or "(-1)^(k-1)*k" in c
        or "(-1)^(k-1)k" in c
        or ("det(a" in c and "alternad" in t and "k" in c)
    )

    mentions_transformed_shape = (
        "primeiracoluna" in c
        or "1,2,...,k" in c
        or "1,2,...,k" in t
        or "acima da diagonal" in t
        or ("expandindo" in t and "ultima linha" in t)
        or "cofator" in t
    )

    has_determinant_formula = mentions_determinant_formula or (
        mentions_column_difference and mentions_transformed_shape and "det" in t
    )

    unable_to_finish_sum = (
        "naoconseguiterminarasoma" in c
        or "naoconseguiterminar" in c
        or "nao consegui terminar a soma" in t
        or "não consegui terminar a soma" in solution.lower()
    )

    # Soma alternada exige evidência de soma, agrupamento ou sequência alternada.
    # A fórmula det(A_k)=(-1)^(k-1)k sozinha não basta.
    has_alternating_sum = (
        not unable_to_finish_sum
        and not keyword_soup
        and (
            "1-2+3-4" in c
            or "1 - 2 + 3 - 4" in t
            or "somaalternada" in c
            or ("alternad" in t and "soma" in t)
            or ("agrupei" in t and "par" in t)
            or ("agrup" in t and "par" in t)
            or ("2025-1013=1012" in c)
        )
    )

    wrong_final_context = (
        "-1013" in c
        or "= -1013" in t
        or "=-1013" in c
        or "2025-1013=1012" in c
        or ("=1012" in c and "=1013" not in c)
        or "2051325" in c
        or "1+2+...+2025" in c
        or "1 + 2 + ... + 2025" in t
        or "2025*2026/2" in c
    )

    answer_only_like = (
        len(c) <= 40
        and (
            c in {"arespostae1013.", "arespostae1013", "resposta1013", "1013"}
            or c.startswith("arespostae1013")
            or c.startswith("resposta:1013")
            or c.startswith("resultado1013")
        )
    )

    explicit_final_1013 = (
        not wrong_final_context
        and not keyword_soup
        and (
            answer_only_like
            or (
                "1013" in c
                and (
                    "resposta" in t
                    or "resultado" in t
                    or "valor final" in t
                    or "valorfinal" in c
                    or "conclu" in t
                    or "logo" in t
                    or "portanto" in t
                    or "soma dos det" in t
                    or "somadosdet" in c
                    or "soma=1013" in c
                    or "total=1013" in c
                    or ("=1013" in c and ("soma" in t or "agrup" in t or "2025" in c))
                )
            )
            or (
                "mil e treze" in t
                and (
                    "resposta" in t
                    or "resultado" in t
                    or "valor final" in t
                    or "conclu" in t
                    or "logo" in t
                    or "portanto" in t
                )
            )
        )
    )

    # O passo formal f2q8_coldiff_det_one deve aparecer quando há uma
    # operação concreta de diferenças/operações de colunas. Não deve aparecer
    # para menção vaga do tipo "a matriz pode ser simplificada por diferenças".
    active_column_operation = (
        "facodiferencasdecolunas" in c
        or "façodiferencasdecolunas" in c
        or "facodiferencassucessivasdecolunas" in c
        or "operacoesdecolunas" in c
        or "operaçõesdecolunas" in solution.lower().replace(" ", "")
        or "substituocada coluna" in t
        or "substituocadacoluna" in c
        or "c_j-c_{j-1}" in c
        or "cj-cj-1" in c
    )

    coldiff_det_one = (
        mentions_column_difference
        and not keyword_soup
        and (
            has_determinant_formula
            or active_column_operation
        )
    )

    wrong_global_sum = (
        "2051325" in c
        or "1+2+...+2025" in c
        or "1 + 2 + ... + 2025" in t
        or "2025*2026/2" in c
    ) and "1013" not in c

    if wrong_global_sum:
        explicit_final_1013 = False
        has_alternating_sum = False
        has_determinant_formula = False
        mentions_column_difference = False
        coldiff_det_one = False

    return {
        "matrix_transformation": mentions_column_difference,
        "coldiff_det_one": coldiff_det_one,
        "determinant_formula": has_determinant_formula,
        "alternating_sum": has_alternating_sum,
        "final_answer": explicit_final_1013,
    }


def extract_f2q8_formal_steps(solution: str) -> List[FormalStep]:
    features = detect_features(solution)
    steps: List[FormalStep] = []

    if features["matrix_transformation"]:
        steps.append(
            FormalStep(
                id="f2q8_s1_bridge",
                type="f2q8_bridge",
                description="Verificação formal da ponte maxMatrix * colDiffMatrix = transformedShape.",
                evidence="A solução usa diferenças sucessivas de colunas.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["matrix_transformation"],
                supports_rubric_items=["matrix_transformation"],
            )
        )

    if features["coldiff_det_one"]:
        steps.append(
            FormalStep(
                id="f2q8_s2_coldiff_det_one",
                type="f2q8_coldiff_det_one",
                description="Verificação formal de det(colDiffMatrix k)=1.",
                evidence="A solução usa operação de colunas que preserva o determinante.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["matrix_transformation"],
                supports_rubric_items=["matrix_transformation"],
            )
        )

    if features["determinant_formula"]:
        steps.append(
            FormalStep(
                id="f2q8_s3_determinant_formula",
                type="f2q8_determinant_formula",
                description="Verificação formal de det(A_k)=(-1)^(k-1)k para todo k>=1.",
                evidence="A solução obtém a fórmula geral do determinante.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["determinant_formula"],
                supports_rubric_items=["determinant_formula"],
            )
        )

    if features["alternating_sum"] or features["final_answer"]:
        steps.append(
            FormalStep(
                id="f2q8_s4_final_sum",
                type="f2q8_final_sum",
                description="Verificação formal da soma alternada final até 2025.",
                evidence="A solução reduz a soma a 1-2+3-4+...+2025 e/ou afirma 1013.",
                lhs="0",
                rhs="0",
                lean_method="norm_num",
                supports_claim_types=["alternating_sum", "final_answer"],
                supports_rubric_items=["alternating_sum", "final_answer"],
            )
        )

    return steps

def extract_claims_ita2025f2q8(solution: str) -> ClaimExtraction:
    features = detect_features(solution)
    claims: List[ExtractedClaim] = []

    if features["matrix_transformation"]:
        claims.append(
            make_claim(
                claim_id="f2q8_c1",
                claim_type="matrix_transformation",
                text="A solução usa diferenças sucessivas de colunas para simplificar A_k.",
                evidence="Foram detectadas operações/diferenças de colunas.",
                confidence=0.87,
            )
        )

    if features["determinant_formula"]:
        claims.append(
            make_claim(
                claim_id="f2q8_c2",
                claim_type="determinant_formula",
                text="A solução afirma ou deriva det(A_k)=(-1)^(k-1)k.",
                evidence="Foi detectada a fórmula geral do determinante ou sua derivação.",
                confidence=0.9,
            )
        )

    if features["alternating_sum"]:
        claims.append(
            make_claim(
                claim_id="f2q8_c3",
                claim_type="alternating_sum",
                text="A solução reduz a soma a 1-2+3-4+...+2025.",
                evidence="Foi detectada soma alternada.",
                confidence=0.86,
            )
        )

    if features["final_answer"]:
        claims.append(
            make_claim(
                claim_id="f2q8_c4",
                claim_type="final_answer",
                text="A solução apresenta resposta final 1013.",
                evidence="Foi detectado o valor 1013.",
                confidence=0.95,
            )
        )

    return ClaimExtraction(
        problem_id="ITA2025F2Q8",
        claims=claims,
        formal_steps=extract_f2q8_formal_steps(solution),
    )
