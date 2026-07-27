from __future__ import annotations

import re
import unicodedata

from confia_lean_auditor.student_claims.schemas import StudentClaim


ARITH_ALLOWED_RE = re.compile(r"^[0-9+\-*() ]+$")

ARITH_EQUALITY_RE = re.compile(
    r"(?P<left>-?[0-9][0-9\s+\-*()]{0,80})\s*=\s*(?P<right>-?[0-9][0-9\s+\-*()]{0,80})"
)

EXPLICIT_FINAL_RE = re.compile(
    r"(?P<raw>"
    r"(?:resposta|resultado|valor\s+pedido|valor\s+final|valor)"
    r"\s*(?:é|e|eh|=|:|vale|igual\s+a)?\s*"
    r"(?P<value>-?[0-9]{1,8})"
    r")",
    re.IGNORECASE,
)

SUM_EQUALS_FINAL_RE = re.compile(
    r"(?P<raw>"
    r"(?:soma|somatorio|somatório)"
    r"[^.\n=]{0,80}"
    r"=\s*(?P<value>-?[0-9]{1,8})"
    r")",
    re.IGNORECASE,
)

DET_FORMULA_RE = re.compile(
    r"(?P<raw>"
    r"det\s*\(?\s*a\s*[_{]?\s*k\s*[)}]?"
    r"\s*(?:=|é|e|eh|vale)\s*"
    r"(?P<formula>[^.\n;]{0,100})"
    r")",
    re.IGNORECASE,
)

ALT_SUM_VALUE_RE = re.compile(
    r"(?P<raw>"
    r"1\s*-\s*2\s*\+\s*3\s*-\s*4\s*\+\s*(?:\.\.\.|…)\s*\+?\s*2025"
    r"\s*=\s*(?P<value>-?[0-9]{1,8})"
    r")",
    re.IGNORECASE,
)

PAIR_COUNT_RE = re.compile(
    r"(?P<raw>(?P<count>[0-9]{1,8})\s+pares?)",
    re.IGNORECASE,
)

PAIR_REDUCTION_RE = re.compile(
    r"(?P<raw>"
    r"2025\s*-\s*(?P<count>[0-9]{1,8})"
    r"(?:\s*=\s*(?P<value>-?[0-9]{1,8}))?"
    r")",
    re.IGNORECASE,
)

def _normalize_text(text: str) -> str:
    return (
        text.replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("…", "...")
    )


def _strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def _compact_formula(text: str) -> str:
    text = _strip_accents(_normalize_text(text.lower()))
    text = text.replace(" ", "")
    text = text.replace("*", "")
    text = text.replace("·", "")
    text = text.replace("{", "(").replace("}", ")")
    return text


def _context(text: str, start: int, end: int, radius: int = 90) -> str:
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    return text[a:b].strip()


def _clean_arith_expr(expr: str) -> str | None:
    expr = _normalize_text(expr)
    expr = re.sub(r"\s+", " ", expr.strip())

    if not expr:
        return None

    if len(expr) > 100:
        return None

    if not ARITH_ALLOWED_RE.match(expr):
        return None

    return expr


def _make_claim(
    idx: int,
    claim_type,
    raw_text: str,
    normalized_text: str,
    context: str,
    data: dict,
    method: str = "norm_num",
    confidence: float = 0.85,
) -> StudentClaim:
    return StudentClaim(
        id=f"student_claim_{idx}",
        problem_id="ITA2025F2Q8",
        claim_type=claim_type,
        raw_text=raw_text,
        normalized_text=normalized_text,
        context=context,
        data=data,
        method=method,
        confidence=confidence,
    )


def _extract_final_answer_claims(solution: str, start_index: int = 0) -> list[StudentClaim]:
    text = _normalize_text(solution)
    candidates: list[tuple[int, int, str, str]] = []

    for pattern in [EXPLICIT_FINAL_RE, SUM_EQUALS_FINAL_RE]:
        for match in pattern.finditer(text):
            value = match.group("value")
            raw = match.group("raw").strip()
            candidates.append((match.start(), match.end(), raw, value))

    by_value: dict[int, tuple[int, int, str, str]] = {}
    for start, end, raw, value_text in candidates:
        value = int(value_text)
        by_value[value] = (start, end, raw, value_text)

    claims: list[StudentClaim] = []
    idx = start_index

    for value, (start, end, raw, value_text) in sorted(by_value.items(), key=lambda x: x[1][0]):
        claims.append(
            _make_claim(
                idx=idx,
                claim_type="f2q8_student_final_answer",
                raw_text=raw,
                normalized_text=f"final_answer = {value_text}",
                context=_context(solution, start, end),
                data={"student_value": value},
                method="norm_num",
                confidence=0.88,
            )
        )
        idx += 1

    return claims


def _classify_det_formula(formula_text: str) -> str | None:
    f = _compact_formula(formula_text)

    if "(-1)^(k-1)(k+1)" in f or "(-1)^(k-1)k+1" in f:
        return "minus_one_pow_k_minus_1_times_k_plus_1"

    if "(-1)^kk" in f or "(-1)^(k)k" in f:
        return "minus_one_pow_k_times_k"

    if "(-1)^(k-1)k" in f:
        return "minus_one_pow_k_minus_1_times_k"

    if f.startswith("k") or f == "k":
        return "positive_k"

    if f.startswith("-k") or f == "-k":
        return "negative_k"

    return None


def _extract_det_formula_claims(solution: str, start_index: int = 0) -> list[StudentClaim]:
    text = _normalize_text(solution)
    claims: list[StudentClaim] = []
    idx = start_index

    for match in DET_FORMULA_RE.finditer(text):
        formula_text = match.group("formula").strip()
        formula_kind = _classify_det_formula(formula_text)

        if formula_kind is None:
            continue

        raw = match.group("raw").strip()

        claims.append(
            _make_claim(
                idx=idx,
                claim_type="f2q8_student_det_formula",
                raw_text=raw,
                normalized_text=f"det_formula_kind = {formula_kind}",
                context=_context(solution, match.start(), match.end()),
                data={
                    "formula_text": formula_text,
                    "formula_kind": formula_kind,
                },
                method="norm_num",
                confidence=0.86,
            )
        )
        idx += 1

        # Para a primeira versão, basta uma fórmula de determinante por solução.
        break

    return claims


def _extract_alternating_sum_value_claims(solution: str, start_index: int = 0) -> list[StudentClaim]:
    text = _normalize_text(solution)
    claims: list[StudentClaim] = []
    idx = start_index

    for match in ALT_SUM_VALUE_RE.finditer(text):
        value = int(match.group("value"))
        raw = match.group("raw").strip()

        claims.append(
            _make_claim(
                idx=idx,
                claim_type="f2q8_student_alternating_sum_value",
                raw_text=raw,
                normalized_text=f"alternating_sum_value = {value}",
                context=_context(solution, match.start(), match.end()),
                data={"student_value": value},
                method="norm_num",
                confidence=0.87,
            )
        )
        idx += 1

    return claims


def _extract_pair_count_claims(solution: str, start_index: int = 0) -> list[StudentClaim]:
    text = _normalize_text(solution)
    claims: list[StudentClaim] = []
    idx = start_index

    for match in PAIR_COUNT_RE.finditer(text):
        count = int(match.group("count"))
        raw = match.group("raw").strip()

        claims.append(
            _make_claim(
                idx=idx,
                claim_type="f2q8_student_pair_count",
                raw_text=raw,
                normalized_text=f"pair_count = {count}",
                context=_context(solution, match.start(), match.end()),
                data={"pair_count": count},
                method="norm_num",
                confidence=0.84,
            )
        )
        idx += 1

    return claims


def _extract_pair_reduction_claims(solution: str, start_index: int = 0) -> list[StudentClaim]:
    text = _normalize_text(solution)
    claims: list[StudentClaim] = []
    idx = start_index

    for match in PAIR_REDUCTION_RE.finditer(text):
        count = int(match.group("count"))
        value_text = match.group("value")
        stated_value = int(value_text) if value_text is not None else None
        raw = match.group("raw").strip()

        ctx = _context(solution, match.start(), match.end())
        ctx_lower = _strip_accents(ctx.lower())

        # Evita capturar qualquer 2025 - n fora do contexto da soma alternada.
        if not any(token in ctx_lower for token in ["par", "agrup", "soma", "alternad"]):
            continue

        data = {"subtracted_pair_count": count}
        if stated_value is not None:
            data["stated_value"] = stated_value

        normalized = f"pair_reduction = 2025 - {count}"
        if stated_value is not None:
            normalized += f" = {stated_value}"

        claims.append(
            _make_claim(
                idx=idx,
                claim_type="f2q8_student_pair_reduction",
                raw_text=raw,
                normalized_text=normalized,
                context=ctx,
                data=data,
                method="norm_num",
                confidence=0.86,
            )
        )
        idx += 1

    return claims

def _extract_arithmetic_equalities(solution: str, start_index: int = 0) -> list[StudentClaim]:
    text = _normalize_text(solution)
    claims: list[StudentClaim] = []
    idx = start_index

    for match in ARITH_EQUALITY_RE.finditer(text):
        prefix = text[max(0, match.start() - 6):match.start()]
        if "..." in prefix:
            continue

        left = _clean_arith_expr(match.group("left"))
        right = _clean_arith_expr(match.group("right"))

        if left is None or right is None:
            continue

        raw = match.group(0).strip()
        ctx = _context(solution, match.start(), match.end())
        ctx_lower = _strip_accents(ctx.lower())

        # Se a igualdade é uma redução contextual da soma alternada,
        # ela já é tratada por f2q8_student_pair_reduction.
        # Não queremos também gerar arithmetic_equality genérico,
        # pois a subtração isolada pode ser verdadeira mesmo quando
        # a etapa matemática da F2Q8 está errada.
        compact_left = re.sub(r"\s+", "", left)
        if (
            compact_left.startswith("2025-")
            and any(token in ctx_lower for token in ["par", "agrup", "soma", "alternad"])
        ):
            continue

        claims.append(
            _make_claim(
                idx=idx,
                claim_type="arithmetic_equality",
                raw_text=raw,
                normalized_text=f"{left} = {right}",
                context=ctx,
                data={
                    "left_expr": left,
                    "right_expr": right,
                },
                method="norm_num",
                confidence=0.85,
            )
        )
        idx += 1

    return claims

def extract_f2q8_student_claims(solution: str) -> list[StudentClaim]:
    claims: list[StudentClaim] = []

    for extractor in [
        _extract_final_answer_claims,
        _extract_det_formula_claims,
        _extract_alternating_sum_value_claims,
        _extract_pair_count_claims,
        _extract_pair_reduction_claims,
        _extract_arithmetic_equalities,
    ]:
        new_claims = extractor(solution, start_index=len(claims))
        claims.extend(new_claims)

    return claims
