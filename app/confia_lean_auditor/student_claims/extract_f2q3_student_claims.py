from __future__ import annotations

import re
import unicodedata
from typing import List

from confia_lean_auditor.student_claims.schemas import StudentClaim


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


def _context(original: str, raw: str, radius: int = 90) -> str:
    idx = original.lower().find(raw.lower())
    if idx < 0:
        return original[: 2 * radius]
    start = max(0, idx - radius)
    end = min(len(original), idx + len(raw) + radius)
    return original[start:end]


def _make_claim(
    idx: int,
    claim_type: str,
    raw_text: str,
    normalized_text: str,
    context: str,
    data: dict,
    method: str = "ring_nf",
    confidence: float = 0.86,
) -> StudentClaim:
    return StudentClaim(
        id=f"student_claim_{idx}",
        problem_id="ITA2025F2Q3",
        claim_type=claim_type,  # type: ignore[arg-type]
        raw_text=raw_text,
        normalized_text=normalized_text,
        context=context,
        data=data,
        method=method,
        confidence=confidence,
    )


def _extract_beta_difference(solution: str, claims: List[StudentClaim]) -> None:
    t = normalize(solution)
    c = compact(t)

    candidates = [
        ("cosbeta-sinbeta=1/2", "1 / 2", "cos beta - sin beta = 1/2"),
        ("cos(beta)-sin(beta)=1/2", "1 / 2", "cos(beta)-sin(beta)=1/2"),
        ("cosbeta-sinbeta=-1/2", "-1 / 2", "cos beta - sin beta = -1/2"),
        ("cos(beta)-sin(beta)=-1/2", "-1 / 2", "cos(beta)-sin(beta)=-1/2"),
        ("sinbeta-cosbeta=1/2", "1 / 2", "sin beta - cos beta = 1/2"),
    ]

    for needle, value_expr, raw in candidates:
        if needle in c:
            claims.append(
                _make_claim(
                    idx=len(claims),
                    claim_type="f2q3_student_beta_difference",
                    raw_text=raw,
                    normalized_text=f"cosBetaCandidate - sinBetaCandidate = {value_expr}",
                    context=_context(solution, raw),
                    data={"value_expr": value_expr},
                    method="ring",
                    confidence=0.86,
                )
            )
            return


def _extract_candidate_values(solution: str, claims: List[StudentClaim]) -> None:
    c = compact(normalize(solution))

    patterns = [
        (
            "sin_beta",
            "sinBetaCandidate",
            [
                ("sinbeta=-(sqrt(7)+1)/4", "- (sqrt7 + 1) / 4", "sin beta = -(sqrt(7)+1)/4"),
                ("sinbeta=-(1+sqrt(7))/4", "- (1 + sqrt7) / 4", "sin beta = -(1+sqrt(7))/4"),
                ("sinbeta=(-1-sqrt(7))/4", "(-1 - sqrt7) / 4", "sin beta = (-1-sqrt(7))/4"),
                ("sinbeta=(sqrt(7)+1)/4", "(sqrt7 + 1) / 4", "sin beta = (sqrt(7)+1)/4"),
            ],
        ),
        (
            "cos_beta",
            "cosBetaCandidate",
            [
                ("cosbeta=(1-sqrt(7))/4", "(1 - sqrt7) / 4", "cos beta = (1-sqrt(7))/4"),
                ("cosbeta=-(sqrt(7)-1)/4", "- (sqrt7 - 1) / 4", "cos beta = -(sqrt(7)-1)/4"),
                ("cosbeta=(sqrt(7)-1)/4", "(sqrt7 - 1) / 4", "cos beta = (sqrt(7)-1)/4"),
            ],
        ),
        (
            "sin_alpha",
            "sinAlphaCandidate",
            [
                ("sinalpha=-sqrt(7)/4", "- sqrt7 / 4", "sin alpha = -sqrt(7)/4"),
                ("sinalpha=-(sqrt(7))/4", "- sqrt7 / 4", "sin alpha = -(sqrt(7))/4"),
                ("sinalpha=sqrt(7)/4", "sqrt7 / 4", "sin alpha = sqrt(7)/4"),
            ],
        ),
        (
            "cos_alpha",
            "cosAlphaCandidate",
            [
                ("cosalpha=-3/4", "-3 / 4", "cos alpha = -3/4"),
                ("cosalpha=3/4", "3 / 4", "cos alpha = 3/4"),
            ],
        ),
    ]

    for value_name, lean_lhs, options in patterns:
        for needle, expr, raw in options:
            if needle in c:
                claims.append(
                    _make_claim(
                        idx=len(claims),
                        claim_type="f2q3_student_candidate_value",
                        raw_text=raw,
                        normalized_text=f"{lean_lhs} = {expr}",
                        context=_context(solution, raw),
                        data={
                            "value_name": value_name,
                            "lean_lhs": lean_lhs,
                            "expr": expr,
                        },
                        method="ring_nf; rw [sqrt7_sq]; ring",
                        confidence=0.86,
                    )
                )
                break


def _extract_final_sin_sum(solution: str, claims: List[StudentClaim]) -> None:
    t = normalize(solution)
    c = compact(t)

    if "sin(alpha+beta)" not in c and "sen(alpha+beta)" not in c:
        return

    options = [
        ("(5+sqrt(7))/8", "(5 + sqrt7) / 8", "sin(alpha+beta) = (5+sqrt(7))/8"),
        ("(sqrt(7)+5)/8", "(sqrt7 + 5) / 8", "sin(alpha+beta) = (sqrt(7)+5)/8"),
        ("(5-sqrt(7))/8", "(5 - sqrt7) / 8", "sin(alpha+beta) = (5-sqrt(7))/8"),
        ("1/2", "1 / 2", "sin(alpha+beta) = 1/2"),
    ]

    for needle, expr, raw in options:
        if needle in c:
            claims.append(
                _make_claim(
                    idx=len(claims),
                    claim_type="f2q3_student_final_sin_sum",
                    raw_text=raw,
                    normalized_text=f"FinalSinSumClaim value = {expr}",
                    context=_context(solution, raw),
                    data={"expr": expr},
                    method="ring_nf; rw [sqrt7_sq]; ring",
                    confidence=0.88,
                )
            )
            return


def _extract_final_answer(solution: str, claims: List[StudentClaim]) -> None:
    t = normalize(solution)
    c = compact(t)

    tail = t
    for cue in ["portanto", "logo", "resposta", "conclu", "assim"]:
        idx = t.rfind(cue)
        if idx >= 0:
            tail = t[idx:]
            break

    tail_c = compact(tail)

    options = [
        ("(5+sqrt(7))/8", "(5 + sqrt7) / 8", "resposta = (5+sqrt(7))/8"),
        ("(sqrt(7)+5)/8", "(sqrt7 + 5) / 8", "resposta = (sqrt(7)+5)/8"),
        ("(5-sqrt(7))/8", "(5 - sqrt7) / 8", "resposta = (5-sqrt(7))/8"),
        ("1/2", "1 / 2", "resposta = 1/2"),
    ]

    for needle, expr, raw in options:
        if needle in tail_c or (needle in c and "resposta" in c):
            claims.append(
                _make_claim(
                    idx=len(claims),
                    claim_type="f2q3_student_final_answer",
                    raw_text=raw,
                    normalized_text=f"FinalAnswerClaim value = {expr}",
                    context=tail[:220],
                    data={"expr": expr},
                    method="ring_nf; rw [sqrt7_sq]; ring",
                    confidence=0.9,
                )
            )
            return


def extract_f2q3_student_claims(solution: str) -> List[StudentClaim]:
    claims: List[StudentClaim] = []

    _extract_beta_difference(solution, claims)
    _extract_candidate_values(solution, claims)
    _extract_final_sin_sum(solution, claims)
    _extract_final_answer(solution, claims)

    return claims
