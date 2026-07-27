from __future__ import annotations

import re
import unicodedata
from typing import List

from confia_lean_auditor.student_claims.schemas import StudentClaim


PAIR_BY_EXPR: dict[str, tuple[int, int]] = {
    "-1": (-1, 0),
    "1": (1, 0),
    "x": (0, 1),
    "-x": (0, -1),
    "x-1": (-1, 1),
    "-1+x": (-1, 1),
    "1-x": (1, -1),
}


def normalize(text: str) -> str:
    text = text.replace("²", "^2")
    text = text.replace("³", "^3")
    text = text.replace("⁶", "^6")
    text = text.replace("⁷", "^7")
    text = text.replace("¹⁴", "^14")
    text = text.replace("⁵⁷", "^57")
    text = text.replace("−", "-")
    text = text.replace("–", "-")
    text = text.replace("·", "*")
    text = text.replace("≡", "=")
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
        problem_id="ITA2025F2Q1",
        claim_type=claim_type,  # type: ignore[arg-type]
        raw_text=raw_text,
        normalized_text=normalized_text,
        context=context,
        data=data,
        method=method,
        confidence=confidence,
    )


def _extract_final_answer(solution: str, claims: List[StudentClaim]) -> None:
    t = normalize(solution)

    # Não queremos capturar o "b=2" dentro de "a+b=2".
    # Por isso excluímos letras precedidas por "+", "-", ou caractere de palavra.
    a_matches = list(re.finditer(r"(?<![-+\w])a\s*=\s*(-?\d+)", t))
    b_matches = list(re.finditer(r"(?<![-+\w])b\s*=\s*(-?\d+)", t))

    if not a_matches or not b_matches:
        return

    # Em soluções textuais, a resposta final costuma aparecer no final.
    # Usamos a última ocorrência compatível.
    a_match = a_matches[-1]
    b_match = b_matches[-1]

    a_value = int(a_match.group(1))
    b_value = int(b_match.group(1))

    raw = f"a={a_value}, b={b_value}"

    start = min(a_match.start(), b_match.start())
    end = max(a_match.end(), b_match.end())
    context_start = max(0, start - 90)
    context_end = min(len(solution), end + 90)

    claims.append(
        _make_claim(
            idx=len(claims),
            claim_type="f2q1_student_final_answer",
            raw_text=raw,
            normalized_text=f"final_answer: a={a_value}, b={b_value}",
            context=solution[context_start:context_end],
            data={"a": a_value, "b": b_value},
            confidence=0.9,
        )
    )


def _rhs_after_power(c: str, exp: int) -> str | None:
    # Casos em cadeia comuns: x^57=x^3=-1, x^14=x^2=x-1.
    chain_patterns = {
        57: [("x^57=x^3=-1", "-1"), ("x57=x3=-1", "-1")],
        14: [("x^14=x^2=x-1", "x-1"), ("x14=x2=x-1", "x-1")],
        7: [("x^7=x", "x"), ("x7=x", "x")],
    }

    for pattern, rhs in chain_patterns.get(exp, []):
        if pattern in c:
            return rhs

    prefixes = [f"x^{exp}=", f"x{exp}="]
    choices = sorted(PAIR_BY_EXPR.keys(), key=len, reverse=True)

    for prefix in prefixes:
        pos = c.find(prefix)
        if pos < 0:
            continue

        after = c[pos + len(prefix) : pos + len(prefix) + 8]
        for choice in choices:
            if after.startswith(choice):
                return choice

    return None


def _extract_power_reductions(solution: str, claims: List[StudentClaim]) -> None:
    c = compact(normalize(solution))

    for exp in [57, 14, 7]:
        rhs = _rhs_after_power(c, exp)
        if rhs is None:
            continue

        const, coeff = PAIR_BY_EXPR[rhs]
        raw = f"x^{exp}={rhs}"

        claims.append(
            _make_claim(
                idx=len(claims),
                claim_type="f2q1_student_power_reduction",
                raw_text=raw,
                normalized_text=f"powRem {exp} = ({const}, {coeff})",
                context=_context(solution, f"x^{exp}"),
                data={"exponent": exp, "rhs": rhs, "const": const, "coeff": coeff},
                method="norm_num [powRem]",
                confidence=0.86,
            )
        )


def _extract_reduced_form(solution: str, claims: List[StudentClaim]) -> None:
    c = compact(normalize(solution))

    patterns = [
        ("correct", ["(a+b)x-a", "(a+b)*x-a"]),
        ("wrong_const_sign", ["(a+b)x+a", "(a+b)*x+a"]),
        ("wrong_coeff_minus", ["(a-b)x-a", "(a-b)*x-a"]),
        ("wrong_coeff_swapped_minus", ["(b-a)x-a", "(b-a)*x-a"]),
    ]

    for form_kind, candidates in patterns:
        for candidate in candidates:
            if candidate in c:
                claims.append(
                    _make_claim(
                        idx=len(claims),
                        claim_type="f2q1_student_reduced_form",
                        raw_text=candidate,
                        normalized_text=f"reduced_form_kind = {form_kind}",
                        context=_context(solution, candidate),
                        data={"form_kind": form_kind, "formula_text": candidate},
                        method="intro a b\n  constructor <;> norm_num [remainderConst, remainderXCoeff, powRem]",
                        confidence=0.86,
                    )
                )
                return


def _extract_coefficient_system(solution: str, claims: List[StudentClaim]) -> None:
    c = compact(normalize(solution))

    sum_rhs: int | None = None
    sum_lhs = "candidateA + candidateB"

    if "a+b=2" in c:
        sum_rhs = 2
        sum_lhs = "candidateA + candidateB"
    elif "b+a=2" in c:
        sum_rhs = 2
        sum_lhs = "candidateB + candidateA"
    elif "a+b=1" in c:
        sum_rhs = 1
        sum_lhs = "candidateA + candidateB"
    elif "b+a=1" in c:
        sum_rhs = 1
        sum_lhs = "candidateB + candidateA"

    if sum_rhs is None:
        return

    a_equation_kind: str | None = None
    a_rhs: int | None = None

    if "-a=1" in c:
        a_equation_kind = "neg_a"
        a_rhs = 1
    elif "-a=-1" in c:
        a_equation_kind = "neg_a"
        a_rhs = -1
    elif "a=-1" in c:
        a_equation_kind = "a"
        a_rhs = -1
    elif "a=1" in c:
        a_equation_kind = "a"
        a_rhs = 1

    if a_equation_kind is None or a_rhs is None:
        return

    raw = f"{sum_lhs} = {sum_rhs}; {a_equation_kind} = {a_rhs}"

    claims.append(
        _make_claim(
            idx=len(claims),
            claim_type="f2q1_student_coefficient_system",
            raw_text=raw,
            normalized_text=f"coefficient_system: sum_rhs={sum_rhs}, {a_equation_kind}_rhs={a_rhs}",
            context=solution[:220],
            data={
                "sum_lhs": sum_lhs,
                "sum_rhs": sum_rhs,
                "a_equation_kind": a_equation_kind,
                "a_rhs": a_rhs,
            },
            method="norm_num [candidateA, candidateB]",
            confidence=0.86,
        )
    )


def extract_f2q1_student_claims(solution: str) -> List[StudentClaim]:
    claims: List[StudentClaim] = []

    _extract_power_reductions(solution, claims)
    _extract_reduced_form(solution, claims)
    _extract_coefficient_system(solution, claims)
    _extract_final_answer(solution, claims)

    return claims
