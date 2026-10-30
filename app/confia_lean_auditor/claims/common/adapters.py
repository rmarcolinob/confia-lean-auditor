"""The only legacy-to-common conversions. No synthetic text becomes a quote."""
from copy import deepcopy
from dataclasses import asdict, is_dataclass
import hashlib

from confia_lean_auditor.core.schemas import ExtractedClaim
from confia_lean_auditor.student_claims.schemas import StudentClaim
from confia_lean_auditor.student_claims.grounding import source_matches, normalized, FINAL
from confia_lean_auditor.rubric.positive_evidence import (
    Rule, attributable, quoted_ranges, source_contexts, UNATTRIBUTABLE,
)
from .canonical import canonical_details_from_legacy, legacy_canonical_from_legacy
from .schemas import MathClaimRecord, Origin, Provenance, SemanticRole, SourceBinding


def payload_copy(value):
    if hasattr(value, 'model_dump'):
        value = value.model_dump(mode='json')
    elif is_dataclass(value):
        value = asdict(value)
    return deepcopy(dict(value))


def source_digest(solution_text):
    return hashlib.sha256(solution_text.encode()).hexdigest() if solution_text is not None else None


def record_id(channel, legacy_id):
    return f'{channel}:{legacy_id}'


def claim_from_extracted(claim, *, problem_id, solution_text=None, rubric_links=()):
    payload = payload_copy(claim)
    validated = ExtractedClaim.model_validate(payload)
    form, status, reason = canonical_details_from_legacy(problem_id, 'extracted', payload)
    return MathClaimRecord(
        record_id=record_id('extracted', validated.id), problem_id=problem_id, claim_type=validated.type,
        provenance=Provenance(origin=Origin.REFERENCE_EXPECTED, channel='extracted', legacy_id=validated.id),
        source=SourceBinding(grounding_status='unavailable', source_sha256=source_digest(solution_text)),
        canonical_form=form, canonicalization_status=status, canonicalization_reason=reason,
        legacy_payload=payload, rubric_links=tuple(rubric_links))


def _source_role(binding, solution_text, statement_text, claim_type):
    start, end = binding['source_start'], binding['source_end']
    if any(start < b and end > a for a, b in quoted_ranges(solution_text)):
        return SemanticRole.QUOTED_STATEMENT, False
    # Reuse the P0's paragraph scope: a sentence cannot lose a preceding
    # hypothesis/negation wrapper merely because the old grounder split it.
    contexts = [text for a, b, text in source_contexts(solution_text) if a <= start and b >= end]
    allowed = [text for text in contexts if attributable(text, Rule(()), statement_text)]
    if not allowed:
        tokens = [m[0] for text in contexts for m in UNATTRIBUTABLE.finditer(normalized(text))]
        if any(t.startswith(('tentativa', 'tentei', 'abandon', 'descart', 'rejeit')) for t in tokens):
            return SemanticRole.REJECTED_ATTEMPT, False
        if any(t.startswith(('suponh', 'hipotese')) or t in {'se', 'talvez'} for t in tokens):
            return SemanticRole.ASSUMPTION, False
        if any(t in {'enunciado', 'citacao', 'citado', 'prove', 'mostre'} for t in tokens):
            return SemanticRole.QUOTED_STATEMENT, False
        return SemanticRole.UNKNOWN, False
    if FINAL.search(normalized(binding['source_text'])) or 'final_answer' in claim_type:
        return SemanticRole.CONCLUSION, True
    return SemanticRole.UNKNOWN, True


def claim_from_student(claim, *, solution_text=None, statement_text='', rubric_links=()):
    payload = payload_copy(claim)
    grounding = payload.get('grounding') or {}
    status = grounding.get('status', 'unavailable')
    status = status if status in {'grounded', 'ambiguous', 'unresolved', 'unavailable'} else 'unresolved'
    matched = solution_text is not None and source_matches(payload, solution_text)
    role, attributed = SemanticRole.UNKNOWN, False
    if matched:
        role, attributed = _source_role(grounding, solution_text, statement_text, payload['claim_type'])
    elif status == 'grounded':
        status = 'unresolved'
    if payload['claim_type'].startswith('math_'):
        from confia_lean_auditor.student_claims.generic_math import source_is_valid, contextual_role
        matched = solution_text is not None and source_is_valid(payload, solution_text)
        status = 'grounded' if matched else 'unresolved'
        role, attributed = (contextual_role(solution_text, grounding['source_start'], grounding['source_end'], statement_text)
                            if matched else (SemanticRole.UNKNOWN, False))
    if matched and grounding.get('interpretation_status') == 'ambiguous':
        status, attributed = 'ambiguous', False
    source = SourceBinding(
        grounding_status=status, source_sha256=source_digest(solution_text),
        raw_text=grounding['source_text'] if matched else None,
        source_start=grounding['source_start'] if matched else None,
        source_end=grounding['source_end'] if matched else None, attributable=attributed)
    form, canonical_status, reason = canonical_details_from_legacy(payload['problem_id'], 'student', payload)
    return MathClaimRecord(
        record_id=record_id('student', payload['id']), problem_id=payload['problem_id'], claim_type=payload['claim_type'],
        provenance=Provenance(origin=Origin.STUDENT_EXPLICIT if attributed else Origin.STUDENT_CANDIDATE,
                              channel='student', legacy_id=payload['id'], extraction_method=grounding.get('extraction_method')),
        source=source, canonical_form=form, canonicalization_status=canonical_status, canonicalization_reason=reason,
        semantic_role=role, legacy_payload=payload, rubric_links=tuple(rubric_links))


def validate_projection(record, *, solution_text, statement_text=''):
    """Serialized annotations cannot override the original payload or gates."""
    if record.provenance.channel not in {'extracted', 'student'} or record.legacy_payload is None:
        raise ValueError('No legacy execution projection is defined for this native record')
    if record.provenance.channel == 'extracted':
        expected = claim_from_extracted(record.legacy_payload, problem_id=record.problem_id, solution_text=solution_text)
    else:
        expected = claim_from_student(record.legacy_payload, solution_text=solution_text, statement_text=statement_text)
    if record.canonicalization_status is None and record.canonicalization_reason is None:
        # Historical annotations are rebuilt, never granted new authority.
        expected = expected.model_copy(update={
            'canonical_form': legacy_canonical_from_legacy(record.problem_id, record.provenance.channel, record.legacy_payload),
            'canonicalization_status': None, 'canonicalization_reason': None})
    # Links are observations added later, not inputs to a mathematical decision.
    for field in ('schema_version', 'record_id', 'problem_id', 'claim_type', 'provenance',
                  'source', 'canonical_form', 'canonicalization_status', 'canonicalization_reason', 'semantic_role', 'legacy_payload'):
        if getattr(record, field) != getattr(expected, field):
            raise ValueError(f'Inconsistent common claim projection: {field}')
    return expected


def project_extracted_claim(record, *, solution_text):
    validate_projection(record, solution_text=solution_text)
    if record.provenance.channel != 'extracted' or record.provenance.origin != Origin.REFERENCE_EXPECTED:
        raise ValueError('Only a reference candidate can project to ExtractedClaim')
    return ExtractedClaim.model_validate(deepcopy(record.legacy_payload))


def project_student_claim(record, *, solution_text, statement_text=''):
    validate_projection(record, solution_text=solution_text, statement_text=statement_text)
    if record.provenance.channel != 'student' or not record.source.attributable:
        raise ValueError('A source-attributable student record is required for a checker input')
    return StudentClaim(**deepcopy(record.legacy_payload))
