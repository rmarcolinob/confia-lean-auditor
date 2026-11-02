"""Shared opt-in digital item framing, extraction and source routing."""
from dataclasses import dataclass
from typing import Mapping

from confia_lean_auditor.claims.common.adapters import claim_from_student, validate_projection
from confia_lean_auditor.claims.common.schemas import MathClaimRecord
from .registry import extract_student_claims_for_audit
from .digital_literals import extract_digital_literals

@dataclass(frozen=True)
class DigitalItemClaims:
    source_text: str
    records: tuple[MathClaimRecord, ...]
    item_ranges: dict[str, tuple[int, int]]


def collect_digital_items(problem_id, items: Mapping[str, str], *, item_ids="abcd",
                          literal_extractors=(extract_digital_literals,)) -> DigitalItemClaims:
    if not set(items) <= set(item_ids) or any(not isinstance(t, str) for t in items.values()):
        raise ValueError(f"Provide explicitly separated digital items {', '.join(item_ids[:-1])} and/or {item_ids[-1]}")
    source, ranges = "", {}
    for item_id in item_ids:
        if item_id in items:
            source += f"[{item_id}]\n"
            start = len(source)
            source += items[item_id]
            ranges[item_id] = (start, len(source))
            source += "\n\n"
    if len(source) > 20000:
        raise ValueError("Digital input exceeds the existing bounded extractor limit")
    literals = tuple(r for extractor in literal_extractors for r in extractor(problem_id, source))
    records = list(literals)
    for claim in extract_student_claims_for_audit(problem_id, source):
        record = claim_from_student(claim, solution_text=source)
        if any(r.source.source_start <= record.source.source_start and record.source.source_end <= r.source.source_end
               for r in literals if record.source.source_start is not None):
            continue
        validate_projection(record, solution_text=source)
        records.append(record)
    routed = []
    for record in records:
        if record.provenance.channel == "native" and not any(
                record == fresh for extractor in literal_extractors for fresh in extractor(problem_id, source)):
            raise ValueError("Literal source projection is inconsistent")
        a, b = record.source.source_start, record.source.source_end
        owners = [key for key, (start, end) in ranges.items()
                  if a is not None and start <= a < b <= end]
        if len(owners) == 1:
            routed.append(record.model_copy(update={"rubric_links": tuple(owners)}))
    from .semantic import supplement
    routed, _ = supplement(problem_id, source, ranges, routed)
    return DigitalItemClaims(source, tuple(sorted(routed, key=lambda r: (r.source.source_start if r.source.source_start is not None else len(source), r.record_id))), ranges)
