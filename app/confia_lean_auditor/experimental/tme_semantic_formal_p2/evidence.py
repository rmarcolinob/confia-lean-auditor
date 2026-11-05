"""Model interpretation is not a verdict. IDs, offsets and metadata are local."""
from typing import Literal
from pydantic import Field
from confia_lean_auditor.student_claims.semantic import StrictModel, sha
from confia_lean_auditor.student_claims.evidence_units import evidence_units
from confia_lean_auditor.student_claims.tme2_p2_digital import VOCABULARY
from .registry import REGISTRY

class ExtractedClaim(StrictModel):
    source_evidence_ids: list[str] = Field(min_length=1,max_length=12)
    source_span: str = Field(min_length=1,max_length=2048)
    normalized_claim: str = Field(min_length=1,max_length=2048)
    subject: str
    claim_type: Literal['math','relation','integer_pairs','integer_set','integer_mapping','enum','congruence','combinatorial_math','qualitative']
    assertion_status: Literal['asserted','hypothetical','negated','abandoned','quoted','unclear']
    polarity: Literal['positive','negative','unclear']
    scope: Literal['main_argument','final_conclusion','exploration','side_calculation','unknown']
    hypothetical: bool
    abandoned: bool
    attributed_to_student: bool
    obligation_candidates: list[str] = Field(min_length=1,max_length=23)
    route_candidate: Literal['FORMAL','DETERMINISTIC','COMPOSITE','SEMANTIC']

class ExtractionResponse(StrictModel):
    evidence: list[ExtractedClaim] = Field(max_length=160)

class EvidenceUnit(ExtractedClaim):
    evidence_id: str
    source_start: int
    source_end: int
    extractor_model: str
    metadata: dict


def bind_evidence(raw, text, model):
    parsed = ExtractionResponse.model_validate_json(raw)
    units = {u.evidence_id:u for u in evidence_units(text)}
    result = {}
    for c in parsed.evidence:
        if c.subject not in {*VOCABULARY,'unmapped'}: raise ValueError('unknown_subject')
        if not set(c.obligation_candidates) <= REGISTRY.keys() or len(set(c.obligation_candidates)) != len(c.obligation_candidates):
            raise ValueError('unknown_or_duplicate_obligation')
        if not set(c.source_evidence_ids) <= units.keys() or len(set(c.source_evidence_ids)) != len(c.source_evidence_ids):
            raise ValueError('unknown_or_duplicate_source_id')
        selected = sorted((units[i] for i in c.source_evidence_ids),key=lambda u:u.source_start)
        a,b = selected[0].source_start,selected[-1].source_end
        if text[a:b] != c.source_span: raise ValueError('source_span_not_exact_selected_envelope')
        eid = selected[0].evidence_id+':p2:'+sha(dict(source=sha(text),claim=c.model_dump()))[:20]
        result[eid] = EvidenceUnit(**c.model_dump(),evidence_id=eid,source_start=a,source_end=b,
            extractor_model=model,metadata=dict(source_sha256=sha(text),binding='exact_evidence_id_envelope'))
    return tuple(result.values())
