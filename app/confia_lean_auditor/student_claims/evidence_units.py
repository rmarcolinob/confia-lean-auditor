"""Stable, exact source units. No mathematical inference or model offsets."""
from __future__ import annotations

import re
from typing import Literal

from .semantic import StrictModel


class SemanticEvidenceUnit(StrictModel):
    evidence_id: str
    exact_text: str
    source_start: int
    source_end: int
    unit_kind: Literal['sentence', 'clause', 'math_block', 'list_item', 'short_paragraph']
    context_ids: tuple[str, ...]


def evidence_units(source: str) -> tuple[SemanticEvidenceUnit, ...]:
    """Keep whole physical lines (including all sentence qualifiers).

    Paragraph links preserve neighboring lines. Item labels are separate units,
    allowing the existing accepted-item mapper to retain its exact boundaries.
    No unit is truncated to satisfy a downstream size limit.
    """
    spans = []
    offset = 0
    paragraph = 0
    for line in source.splitlines(keepends=True):
        if not line.strip():
            paragraph += 1
            offset += len(line)
            continue
        start = offset + len(line) - len(line.lstrip())
        end = offset + len(line.rstrip())
        heading = re.match(r'\(?[a-d]\)[ \t]*', source[start:end])
        if heading:
            paragraph += 1
            label_end = start + len(heading.group().rstrip())
            spans.append((start, label_end, paragraph, 'clause'))
            start += heading.end()
        if start < end:
            text = source[start:end]
            kind = ('list_item' if re.match(r'(?:\d+[.)]|[-•])\s', text)
                    else 'math_block' if re.search(r'[=<>≤≥]|\d\s*[*×·+]', text)
                    else 'short_paragraph' if len(text) > 180
                    else 'sentence')
            spans.append((start, end, paragraph, kind))
        offset += len(line)
    groups = {}
    for i, (_, _, group, _) in enumerate(spans):
        groups.setdefault(group, []).append(f'E{i+1:03d}')
    return tuple(SemanticEvidenceUnit(
        evidence_id=f'E{i+1:03d}', exact_text=source[a:b], source_start=a,
        source_end=b, unit_kind=kind, context_ids=tuple(groups[group]),
    ) for i, (a, b, group, kind) in enumerate(spans))
