"""Versioned, provenance-preserving records; alignment is not verification."""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, model_validator


class Origin(str, Enum):
    STUDENT_EXPLICIT = 'student_explicit'
    STUDENT_DERIVED = 'student_derived'
    STUDENT_CANDIDATE = 'student_candidate'
    REFERENCE_EXPECTED = 'reference_expected'
    GENERATED_REFERENCE = 'generated_reference'
    SECONDARY_ADJUDICATION = 'secondary_adjudication'


class SemanticRole(str, Enum):
    ASSUMPTION = 'assumption'
    INTERMEDIATE = 'intermediate'
    CONCLUSION = 'conclusion'
    REJECTED_ATTEMPT = 'rejected_attempt'
    QUOTED_STATEMENT = 'quoted_statement'
    UNKNOWN = 'unknown'


class RecordModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class SourceBinding(RecordModel):
    grounding_status: Literal['grounded', 'ambiguous', 'unresolved', 'unavailable']
    raw_text: Optional[str] = None
    source_start: Optional[int] = None
    source_end: Optional[int] = None
    source_sha256: Optional[str] = None
    attributable: bool = False

    @model_validator(mode='after')
    def coherent_span(self):
        present = (self.raw_text is not None, self.source_start is not None, self.source_end is not None)
        if any(present) and not all(present):
            raise ValueError('A literal span requires text, start and end together')
        if all(present) and (self.source_start < 0 or self.source_end - self.source_start != len(self.raw_text)):
            raise ValueError('Invalid original-text offsets')
        if self.attributable and (self.grounding_status != 'grounded' or not all(present)
                                  or not self.source_sha256 or len(self.source_sha256) != 64
                                  or any(c not in '0123456789abcdef' for c in self.source_sha256)):
            raise ValueError('Attribution requires grounded source text and its digest')
        return self


class CanonicalForm(RecordModel):
    family: str
    subject: str
    variables: tuple[str, ...] = ()
    value: Any
    method: str
    mathematical_form: Optional[dict[str, Any]] = None


class Provenance(RecordModel):
    origin: Origin
    channel: Literal['extracted', 'student', 'native']
    legacy_id: Optional[str] = None
    extraction_method: Optional[str] = None


class VerificationLink(RecordModel):
    verification_id: str
    mechanism: Literal['student_check', 'formal_step', 'microclaim', 'positive_evidence_gate']
    origin: Origin
    status: str
    attributed_to_student: bool = False
    artifact_ref: str


class ExpectedObligation(RecordModel):
    criterion_id: str
    claim_id: str
    claim_type: str
    expected_payload: dict[str, Any]
    required_microclaim_ids: tuple[str, ...] = ()
    representation_source: str
    quantity_subject: Optional[dict[str, Any]] = None


class MathClaimRecord(RecordModel):
    schema_version: Literal['math-claim-v1'] = 'math-claim-v1'
    record_id: str
    problem_id: str
    claim_type: str
    provenance: Provenance
    source: SourceBinding
    canonical_form: Optional[CanonicalForm] = None
    canonicalization_status: Optional[Literal['parsed', 'unsupported', 'ambiguous', 'invalid']] = None
    canonicalization_reason: Optional[str] = None
    semantic_role: SemanticRole = SemanticRole.UNKNOWN
    # The single lossless compatibility payload retains fields unavailable in
    # the common vocabulary (including synthetic text and original grounding).
    legacy_payload: Optional[dict[str, Any]] = None
    verification_results: tuple[VerificationLink, ...] = ()
    rubric_links: tuple[str, ...] = ()
    # Describes the reference contract; never grants verification authority.
    expected_obligation: Optional[ExpectedObligation] = None


class ClaimAlignment(RecordModel):
    reference_record_id: str
    student_record_ids: tuple[str, ...] = ()
    status: Literal['aligned', 'conflicting', 'ambiguous', 'unmatched']
    preferred_attribution_ids: tuple[str, ...] = ()
    reason: str
    alignment_basis: Optional[str] = None


class CriterionTrace(RecordModel):
    criterion_id: str
    reference_record_id: Optional[str] = None
    student_record_ids: tuple[str, ...] = ()
    required_microclaim_ids: tuple[str, ...] = ()
    scoring_basis: Optional[str] = None
    decision_ref: str
    evidence_ref: str


class MathClaimCatalog(RecordModel):
    schema_version: Literal['math-claim-catalog-v1'] = 'math-claim-catalog-v1'
    problem_id: str
    source_sha256: str
    records: tuple[MathClaimRecord, ...]
    alignments: tuple[ClaimAlignment, ...]
    criterion_traces: tuple[CriterionTrace, ...]
