"""Small input port over the shared accepted TranscriptionVersion, independent of capture.

Provenance and source regions remain in AuditSource; they are never math evidence.
No normalization or recognition is performed here.
"""
from confia_lean_auditor.submission_audits.errors import AuditConflict

class InputRequiresReview(AuditConflict):
    code = "INPUT_REQUIRES_REVIEW"
    message = "Revise a entrada: texto ausente, incompleto ou com incerteza de captura. Nenhuma nota foi produzida."


def require_usable(source, case):
    if not case.problem_id or source.problem_id != case.problem_id or source.submission_id != case.submission_id:
        raise InputRequiresReview()
    revision=source.provenance.revision
    if (not source.solution_text.strip() or source.warnings
            or any(i.requires_review for i in revision.input_issues)
            or any(s.kind == 'unknown' or not (s.text or s.latex or '').strip() for s in revision.segments)):
        raise InputRequiresReview()
    return source
