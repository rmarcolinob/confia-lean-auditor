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
    text = text.replace("·", "*")
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def compact_no_star(text: str) -> str:
    return compact(text).replace("*", "")


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


def leanize_polynomial_expr(expr: str) -> str:
    expr = expr.strip()
    expr = expr.strip(".;,")
    expr = expr.replace(" ", "")
    expr = expr.replace("²", "^2")
    expr = expr.replace("−", "-")

    expr = re.sub(r"(\d+)a", r"\1*a", expr)

    expr = expr.replace("^", " ^ ")
    expr = expr.replace("*", " * ")
    expr = expr.replace("+", " + ")
    expr = expr.replace("-", " - ")

    expr = re.sub(r"\s+", " ", expr).strip()

    if expr.startswith("- "):
        expr = "-" + expr[2:]

    return expr


def extract_q1_formal_steps(solution: str) -> List[FormalStep]:
    t = normalize(solution)
    steps: List[FormalStep] = []

    for raw_line in t.splitlines():
        line = compact(raw_line)

        if "=" not in line:
            continue

        if "(a-1)" not in line:
            continue

        if "a^2-5" not in line:
            continue

        rhs = line.split("=")[-1].strip().strip(".;,")

        if "a^2" not in rhs:
            continue

        if "10" not in rhs:
            continue

        rhs_lean = leanize_polynomial_expr(rhs)

        steps.append(
            FormalStep(
                id="q1_s1_determinant_expansion",
                type="determinant_expansion",
                description="Expansão algébrica do determinante usado no cálculo da área.",
                evidence=raw_line.strip(),
                lhs="(a - 1) * (4 * a) - 2 * (a ^ 2 - 5)",
                rhs=rhs_lean,
                lean_method="ring",
                supports_claim_types=["area_formula"],
                supports_rubric_items=["area_formula"],
            )
        )

        break

    return steps


def extract_claims_ita2025q1(solution: str) -> ClaimExtraction:
    t = normalize(solution)
    c = compact_no_star(t)

    claims: List[ExtractedClaim] = []
    formal_steps = extract_q1_formal_steps(solution)

    if not any(step.type == "determinant_expansion" for step in formal_steps):
        from confia_lean_auditor.llm.formal_step_extractor import (
            extract_formal_steps_with_llm,
        )

        formal_steps.extend(
            extract_formal_steps_with_llm("ITA2025Q1", solution)
        )


    has_z2 = ("z^2" in t or "z2" in t) and "a^2" in c
    has_real = "a^2-4" in c
    has_imag = "4a" in c

    if has_z2 and has_real and has_imag:
        claims.append(
            make_claim(
                claim_id="q1_c1",
                claim_type="z_squared_coordinates",
                text="z² = (a² - 4) + 4ai, logo z² corresponde ao ponto (a² - 4, 4a).",
                evidence="A solução apresenta z² = a² - 4 + 4ai e usa o ponto (a² - 4, 4a).",
                confidence=0.95,
                normalized={"z2_re": "a^2 - 4", "z2_im": "4a"},
            )
        )

    has_area_method = "area" in t or "det" in t or "determinante" in t
    has_area_formula = "a^2-2a+5" in c

    if has_area_method and has_area_formula:
        claims.append(
            make_claim(
                claim_id="q1_c2",
                claim_type="area_formula",
                text="A área do triângulo é a² - 2a + 5.",
                evidence="A solução calcula a área por determinante e obtém a² - 2a + 5.",
                confidence=0.95,
                normalized={"area": "a^2 - 2a + 5"},
            )
        )

    has_equation = (
        "a^2-2a+5=200" in c
        or "a^2-2a-195=0" in c
        or "(a-15)(a+13)=0" in c
    )

    if has_equation:
        claims.append(
            make_claim(
                claim_id="q1_c3",
                claim_type="area_equation",
                text="Da condição de área 200, obtém-se a equação a² - 2a + 5 = 200.",
                evidence="A solução monta equação equivalente, como a² - 2a + 5 = 200 ou (a - 15)(a + 13) = 0.",
                confidence=0.95,
                normalized={"equation": "a^2 - 2a + 5 = 200"},
            )
        )

    mentions_positive = "a > 0" in t or "a positivo" in t or "positivo" in t
    discards_negative = "-13" in t or "raiz negativa" in t or "descarta" in t

    if mentions_positive and discards_negative:
        claims.append(
            make_claim(
                claim_id="q1_c4",
                claim_type="positive_root_selection",
                text="Como a > 0, descarta-se a raiz negativa -13.",
                evidence="A solução menciona a positividade de a e descarta -13.",
                confidence=0.95,
                normalized={"discarded_root": "-13"},
            )
        )

    final_answer_patterns = [
        r"\ba\s*=\s*15\b",
        r"\ba\s+vale\s+15\b",
        r"\bresposta\s*:?\s*15\b",
        r"\bvalor\s+de\s+a\s+e\s+15\b",
    ]

    if any(re.search(pattern, t) for pattern in final_answer_patterns):
        claims.append(
            make_claim(
                claim_id="q1_c5",
                claim_type="final_answer",
                text="O valor correto é a = 15.",
                evidence="A solução conclui a = 15.",
                confidence=0.98,
                normalized={"answer": "15"},
            )
        )

    return ClaimExtraction(
        problem_id="ITA2025Q1",
        claims=claims,
        formal_steps=formal_steps,
    )


def extract_claims(problem_id: str, solution: str) -> ClaimExtraction:
    if problem_id == "ITA2025Q1":
        return extract_claims_ita2025q1(solution)

    return ClaimExtraction(problem_id=problem_id, claims=[], formal_steps=[])
