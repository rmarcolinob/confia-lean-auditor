"""Split the printed statement from the student's answer in a full-page transcription."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

MATCH_THRESHOLD = 0.75
MAX_WINDOW_LINES = 30


@dataclass(frozen=True)
class RemovedBlock:
    kind: str  # "before_statement" | "statement"
    page_index: int
    text: str


@dataclass(frozen=True)
class PageAnswer:
    page_index: int
    answer_text: str


@dataclass
class AnswerExtraction:
    answer_text: str
    pages: list[PageAnswer]
    removed: list[RemovedBlock] = field(default_factory=list)
    statement_found: bool = False
    statement_match: float | None = None
    warnings: list[str] = field(default_factory=list)


def match_key(text: str) -> str:
    """Comparable form: no accents, case, LaTeX/Markdown markup or whitespace."""
    text = re.sub(r"\\(?:frac|dfrac|sqrt|mathrm|text|mathbb|left|right|cdot|times)", " ", text)
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", text)


def _lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def _best_window(statement_key: str, pages: list[list[str]]):
    """(score, page, first line, last line) of the most similar run of consecutive lines."""
    best = (0.0, None, None, None)
    for p, lines in enumerate(pages):
        keys = [match_key(line) for line in lines]
        for i in range(len(lines)):
            window = ""
            for j in range(i, min(i + MAX_WINDOW_LINES, len(lines))):
                window += keys[j]
                if len(window) > 2 * len(statement_key) + 40:
                    break
                matcher = SequenceMatcher(None, statement_key, window, autojunk=False)
                if matcher.real_quick_ratio() <= best[0] or matcher.quick_ratio() <= best[0]:
                    continue
                score = matcher.ratio()
                if score > best[0]:
                    best = (score, p, i, j)
    return best


def extract_answer(page_texts: list[str], statement: str, threshold: float = MATCH_THRESHOLD) -> AnswerExtraction:
    pages = [_lines(text) for text in page_texts]
    statement_key = match_key(statement)
    score, page, first, last = _best_window(statement_key, pages) if statement_key else (0.0, None, None, None)

    if page is None or score < threshold:
        # Never guess a cut: return everything and ask for review.
        answers = [PageAnswer(i, "\n".join(lines)) for i, lines in enumerate(pages)]
        return AnswerExtraction(
            answer_text="\n\n".join(a.answer_text for a in answers if a.answer_text),
            pages=answers, statement_found=False, statement_match=round(score, 3) if score else None,
            warnings=["STATEMENT_NOT_FOUND: o enunciado não foi localizado; a resposta pode conter "
                      "texto impresso e precisa de conferência."],
        )

    removed, answers = [], []
    for i, lines in enumerate(pages):
        if i < page:
            if lines:
                removed.append(RemovedBlock("before_statement", i, "\n".join(lines)))
            answers.append(PageAnswer(i, ""))
        elif i == page:
            if first:
                removed.append(RemovedBlock("before_statement", i, "\n".join(lines[:first])))
            removed.append(RemovedBlock("statement", i, "\n".join(lines[first:last + 1])))
            answers.append(PageAnswer(i, "\n".join(lines[last + 1:])))
        else:
            answers.append(PageAnswer(i, "\n".join(lines)))

    warnings = []
    answer_text = "\n\n".join(a.answer_text for a in answers if a.answer_text)
    if not answer_text:
        warnings.append("EMPTY_ANSWER: nenhum texto depois do enunciado.")
    if any(b.kind == "before_statement" and re.search(r"\d\s*[=+\-]", b.text) for b in removed):
        warnings.append("CONTENT_BEFORE_STATEMENT: há contas antes do enunciado (anotação de margem?); "
                        "confira o texto removido.")
    return AnswerExtraction(answer_text=answer_text, pages=answers, removed=removed,
                            statement_found=True, statement_match=round(score, 3), warnings=warnings)
