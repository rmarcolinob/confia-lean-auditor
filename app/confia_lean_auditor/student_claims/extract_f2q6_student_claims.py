from __future__ import annotations

import re
import unicodedata
from typing import List

from confia_lean_auditor.student_claims.schemas import StudentClaim


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
    method: str = "norm_num",
    confidence: float = 0.86,
) -> StudentClaim:
    return StudentClaim(
        id=f"student_claim_{idx}",
        problem_id="ITA2025F2Q6",
        claim_type=claim_type,  # type: ignore[arg-type]
        raw_text=raw_text,
        normalized_text=normalized_text,
        context=context,
        data=data,
        method=method,
        confidence=confidence,
    )


def _extract_probability_formula(solution: str, claims: List[StudentClaim]) -> None:
    c = compact(normalize(solution))

    formula_kind: str | None = None
    raw = ""

    correct_patterns = [
        "p(n)=c(n-1.3)/2^n",
        "p(n)=c(n-1;3)/2^n",
        "c(n-1.3)/2^n",
        "c(n-1;3)/2^n",
        "binom(n-1.3)/2^n",
        "choose(n-1.3)/2^n",
    ]

    wrong_n_patterns = [
        "p(n)=c(n.3)/2^n",
        "p(n)=c(n;3)/2^n",
        "c(n.3)/2^n",
        "c(n;3)/2^n",
    ]

    wrong_denom_patterns = [
        "c(n-1.3)/2^(n-1)",
        "c(n-1;3)/2^(n-1)",
        "p(n)=c(n-1.3)/2^(n-1)",
        "p(n)=c(n-1;3)/2^(n-1)",
    ]

    for pat in wrong_denom_patterns:
        if pat in c:
            formula_kind = "correct_numerator_wrong_denominator_n_minus_1"
            raw = pat
            break

    if formula_kind is None:
        for pat in wrong_n_patterns:
            if pat in c:
                formula_kind = "wrong_choose_n_3"
                raw = pat
                break

    if formula_kind is None:
        for pat in correct_patterns:
            if pat in c:
                formula_kind = "correct"
                raw = pat
                break

    if formula_kind is None:
        return

    claims.append(
        _make_claim(
            idx=len(claims),
            claim_type="f2q6_student_probability_formula",
            raw_text=raw,
            normalized_text=f"probability_formula_kind = {formula_kind}",
            context=_context(solution, "P(N=n)") if "P(N=n)" in solution else solution[:220],
            data={"formula_kind": formula_kind, "formula_text": raw},
            method="norm_num",
            confidence=0.86,
        )
    )


def _extract_ratio_formula(solution: str, claims: List[StudentClaim]) -> None:
    c = compact(normalize(solution))

    ratio_kind: str | None = None
    raw = ""

    wrong_patterns = [
        ("wrong_n_minus_1_over_2n", ["(n-1)/(2n)", "(n-1)/2n"]),
        ("wrong_n_minus_1_over_2n_minus_6", ["(n-1)/(2n-6)"]),
        ("wrong_n_over_2n", ["n/(2n)"]),
        ("wrong_n_over_2n_minus_8", ["n/(2n-8)"]),
    ]

    for kind, patterns in wrong_patterns:
        for pat in patterns:
            if pat in c:
                ratio_kind = kind
                raw = pat
                break
        if ratio_kind is not None:
            break

    correct_patterns = [
        "n/(2n-6)",
        "n/[2n-6]",
        "n/(2(n-3))",
        "n/[2(n-3)]",
    ]

    if ratio_kind is None:
        for pat in correct_patterns:
            if pat in c:
                ratio_kind = "correct"
                raw = pat
                break

    if ratio_kind is None:
        return

    claims.append(
        _make_claim(
            idx=len(claims),
            claim_type="f2q6_student_ratio_formula",
            raw_text=raw,
            normalized_text=f"ratio_formula_kind = {ratio_kind}",
            context=_context(solution, raw),
            data={"ratio_kind": ratio_kind, "ratio_text": raw},
            method="norm_num",
            confidence=0.86,
        )
    )


def _extract_final_answer(solution: str, claims: List[StudentClaim]) -> None:
    t = normalize(solution)

    tail = t
    for cue in ["portanto", "logo", "resposta", "conclu", "valores"]:
        idx = t.rfind(cue)
        if idx >= 0:
            tail = t[idx:]
            break

    values: list[int] = []

    for match in re.finditer(r"n\s*=\s*(\d+)", tail):
        values.append(int(match.group(1)))

    if not values:
        if "6 e 7" in tail or "6e7" in compact(tail):
            values = [6, 7]
        elif "6" in tail and "7" in tail:
            values = [6, 7]

    if not values:
        return

    unique_values = sorted(set(values))
    raw = "n=" + ",".join(str(v) for v in unique_values)

    claims.append(
        _make_claim(
            idx=len(claims),
            claim_type="f2q6_student_final_answer",
            raw_text=raw,
            normalized_text=f"final_answer_values = {unique_values}",
            context=tail[:220],
            data={"values": unique_values},
            method="norm_num [candidateN1, candidateN2]",
            confidence=0.88,
        )
    )


def extract_f2q6_student_claims(solution: str) -> List[StudentClaim]:
    claims: List[StudentClaim] = []

    _extract_probability_formula(solution, claims)
    _extract_ratio_formula(solution, claims)
    _extract_final_answer(solution, claims)

    return claims
