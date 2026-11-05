"""Closed interpretation contract. Source coordinates and identity are local."""
from __future__ import annotations

from typing import Literal
from pydantic import Field
from confia_lean_auditor.student_claims.semantic import StrictModel, sha
from confia_lean_auditor.student_claims.evidence_units import evidence_units

Route = Literal['FORMAL', 'DETERMINISTIC', 'SEMANTIC']
ClaimType = Literal['expression', 'collection', 'qualitative']
VerificationStatus = Literal[
    'FORMAL_VERIFIED', 'FORMAL_REFUTED', 'FORMAL_UNPROVED', 'FORMAL_ERROR',
    'DETERMINISTIC_VERIFIED', 'DETERMINISTIC_FAILED', 'SEMANTIC_SUPPORTED',
    'SEMANTIC_INSUFFICIENT', 'CONTEXT_REJECTED', 'CONFLICTING_EVIDENCE']


class ExtractedClaim(StrictModel):
    source_evidence_ids: list[str] = Field(min_length=1, max_length=12)
    source_span: str = Field(min_length=1, max_length=2048)
    normalized_claim: str = Field(min_length=1, max_length=2048)
    claim_type: ClaimType
    assertion_status: Literal['asserted', 'hypothetical', 'negated', 'abandoned', 'quoted', 'unclear']
    polarity: Literal['positive', 'negative', 'unclear']
    scope: Literal['main_argument', 'final_conclusion', 'exploration', 'side_calculation', 'unknown']
    hypothetical: bool
    abandoned: bool
    attributed_to_student: bool
    rubric_candidates: list[Literal['a', 'b', 'c', 'd']] = Field(max_length=4)
    obligation_candidates: list[str] = Field(min_length=1, max_length=21)
    verification_route_candidate: Route


class ExtractionResponse(StrictModel):
    evidence: list[ExtractedClaim] = Field(max_length=160)


class TMEEvidenceUnit(ExtractedClaim):
    evidence_id: str
    source_start: int = Field(ge=0)
    source_end: int = Field(ge=0)
    extractor_model: str
    extractor_metadata: dict


def bind_evidence(raw: str, text: str, model: str) -> tuple[TMEEvidenceUnit, ...]:
    from .obligation_registry import REGISTRY
    response = ExtractionResponse.model_validate_json(raw)
    units = {u.evidence_id: u for u in evidence_units(text)}
    result = []
    for claim in response.evidence:
        if (len(set(claim.source_evidence_ids)) != len(claim.source_evidence_ids)
                or not set(claim.source_evidence_ids) <= units.keys()):
            raise ValueError('unknown_or_duplicate_source_evidence_id')
        if (not set(claim.obligation_candidates) <= REGISTRY.keys()
                or len(set(claim.obligation_candidates)) != len(claim.obligation_candidates)):
            raise ValueError('unknown_or_duplicate_obligation')
        selected = sorted((units[i] for i in claim.source_evidence_ids), key=lambda u: u.source_start)
        a, b = selected[0].source_start, selected[-1].source_end
        if text[a:b] != claim.source_span:
            raise ValueError('source_span_not_exact_selected_envelope')
        if claim.claim_type == 'qualitative' and claim.normalized_claim not in claim.source_span:
            raise ValueError('qualitative_claim_must_preserve_literal_argument')
        # Multiple claims may share a physical unit; the suffix is system-owned.
        # Context/mapping differences remain separate, for conservative reconciliation.
        identity = sha(dict(source=sha(text), claim=claim.model_dump()))[:20]
        result.append(TMEEvidenceUnit(**claim.model_dump(),
            evidence_id=selected[0].evidence_id + ':claim:' + identity,
            source_start=a, source_end=b, extractor_model=model,
            extractor_metadata=dict(source_sha256=sha(text), binding='exact_evidence_id_envelope')))
    return tuple({e.evidence_id: e for e in result}.values())
