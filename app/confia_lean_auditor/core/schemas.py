from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AuditRequest(BaseModel):
    problem_id: str
    solution: str


class ExtractedClaim(BaseModel):
    id: str
    type: str
    text: str
    evidence: str
    confidence: float = 0.0
    normalized: Dict[str, str] = Field(default_factory=dict)


class ClaimExtraction(BaseModel):
    problem_id: str
    claims: List[ExtractedClaim]


class RubricItemResult(BaseModel):
    id: str
    description: str
    detected: bool
    points: float
    max_points: float
    evidence: Optional[str] = None
    claim_id: Optional[str] = None


class RubricAssessment(BaseModel):
    score: float
    max_score: float
    items: List[RubricItemResult]


class LeanCertificate(BaseModel):
    status: str
    compiled: bool
    exit_code: int
    uses_forbidden_token: bool
    forbidden_tokens_found: List[str]
    stdout: str = ""
    stderr: str = ""
    lean_file: Optional[str] = None
    generated_theorems: List[str] = Field(default_factory=list)


class MicroclaimResult(BaseModel):
    id: str
    description: str
    theorem: Optional[str] = None
    claim_types: List[str] = Field(default_factory=list)
    textual_evidence: bool
    lean_status: str
    supports_rubric_items: List[str] = Field(default_factory=list)


class AuditResponse(BaseModel):
    problem_id: str
    score: float
    max_score: float
    verdict: str
    extracted_claims: ClaimExtraction
    rubric_assessment: RubricAssessment
    lean_certificate: LeanCertificate
    microclaims: List[MicroclaimResult]
    feedback: str
    artifact_dir: Optional[str] = None
