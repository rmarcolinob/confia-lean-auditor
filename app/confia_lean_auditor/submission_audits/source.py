"""Lossless stored-string conversion, with explicit unanalysed diagram markers."""
import hashlib
import json

from .schemas import AuditProvenance, AuditSource, ConversionWarning


def canonical_hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                     allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def convert_segments(segments):
    chunks, warnings = [], []
    for segment in sorted(segments, key=lambda item: (item.page_index, item.order)):
        content = "\n".join(value for value in (segment.text, segment.latex) if value is not None)
        if segment.kind == "diagram":
            content = f"[Diagrama não analisado: {segment.segment_id}; página {segment.page_index + 1}]"
            code, message = "DIAGRAM_NOT_ANALYZED", "Diagrama preservado na revisão e no manuscrito; não analisado pelo auditor textual."
        elif segment.kind == "unknown":
            content = f"[Segmento não identificado: {segment.segment_id}]" + ("\n" + content if content else "")
            code, message = "UNKNOWN_SEGMENT", "Segmento não identificado; somente o conteúdo armazenado foi encaminhado."
        elif not content:
            content = f"[Segmento sem conteúdo: {segment.segment_id}]"
            code, message = "EMPTY_SEGMENT", "Segmento sem conteúdo textual ou matemático armazenado."
        else:
            code = None
        chunks.append(content)
        if code:
            warnings.append(ConversionWarning(segment_id=segment.segment_id, page_index=segment.page_index,
                                              code=code, message=message))
    return "\n".join(chunks), warnings


def source_digest(source):
    return canonical_hash(source.model_dump(mode="json", exclude={"source_hash"}))


def build_source(submission, revision, acceptance, receipt):
    solution, warnings = convert_segments(revision.segments)
    source = AuditSource(
        submission_id=submission.submission_id, problem_id=submission.problem_id,
        transcription_id=revision.transcription_id, revision_number=revision.revision_number,
        acceptance_id=acceptance.acceptance_id, accepted_at=acceptance.accepted_at,
        source_hash="0" * 64, solution_text=solution, warnings=warnings,
        provenance=AuditProvenance(original_artifacts=[submission.snapshot, *submission.page_images],
                                   revision=revision, acceptance=acceptance, acceptance_receipt=receipt),
    )
    return source.model_copy(update={"source_hash": source_digest(source)})
