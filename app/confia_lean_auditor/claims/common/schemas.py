"""Versioned, provenance-preserving records; alignment is not verification."""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional, Union
import hashlib
import json

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, model_validator


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


class StructuredSourceBinding(RecordModel):
    """Opt-in diagram provenance. No fabricated transcription or text offsets.

    source_sha256 binds the textual part of the same audit envelope (possibly
    empty); payload_sha256 separately binds the original structured diagram.
    Neither digest claims to be a hash of an image that was not read.
    """
    kind: Literal['diagram_structured']
    source_ref: StrictStr = Field(min_length=1, max_length=500)
    image_ref: Optional[StrictStr] = Field(default=None, min_length=1, max_length=1000)
    page_index: Optional[int] = Field(default=None, ge=0)
    regions: dict[str, tuple[float, float, float, float]] = Field(default_factory=dict)
    confidence: Optional[float] = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    position_confidence: dict[str, float] = Field(default_factory=dict)
    confirmed: StrictBool
    origin: Literal['student', 'reference', 'unknown']
    payload: dict[str, Any]
    payload_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    source_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    grounding_status: Literal['grounded', 'ambiguous', 'unresolved', 'unavailable']
    attributable: StrictBool = False
    raw_text: None = None
    source_start: None = None
    source_end: None = None

    @model_validator(mode='after')
    def bound_structure(self):
        from math import isfinite
        digest = hashlib.sha256(json.dumps(self.payload, sort_keys=True, separators=(',', ':'),
                                           ensure_ascii=False, allow_nan=False).encode()).hexdigest()
        if digest != self.payload_sha256:
            raise ValueError('Structured payload digest mismatch')
        if self.attributable and (not self.confirmed or self.origin != 'student' or self.grounding_status != 'grounded'):
            raise ValueError('Structured attribution requires confirmed student evidence')
        if any(not isfinite(v) or not 0 <= v <= 1 for v in self.position_confidence.values()):
            raise ValueError('Invalid position confidence')
        if any(any(not isfinite(v) or v < 0 for v in box) or box[2] == 0 or box[3] == 0
               for box in self.regions.values()):
            raise ValueError('Invalid diagram region')
        return self


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
    source: Union[SourceBinding, StructuredSourceBinding]
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

    @model_validator(mode='after')
    def structured_record_is_not_a_text_projection(self):
        if isinstance(self.source, StructuredSourceBinding):
            if (self.claim_type != 'diagram_state' or self.provenance.channel != 'native'
                    or self.provenance.extraction_method != 'diagram_structured.v1'
                    or self.legacy_payload is not None or self.canonical_form is None
                    or self.canonical_form.family != 'diagram_state'
                    or self.canonical_form.value != self.source.payload):
                raise ValueError('Structured evidence must retain its original diagram payload and native type')
        return self


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
