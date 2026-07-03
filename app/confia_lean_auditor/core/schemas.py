from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AuditRequest(BaseModel):
    problem_id: str
    solution: str


class FormalStep(BaseModel):
    id: str
    type: str
    description: str
    evidence: str
    lhs: str
    rhs: str
    lean_method: str = "ring"
    supports_claim_types: List[str] = Field(default_factory=list)
    supports_rubric_items: List[str] = Field(default_factory=list)


class FormalStepResult(BaseModel):
    id: str
    type: str
    description: str
    evidence: str
    lhs: str
    rhs: str
    lean_method: str
    supports_claim_types: List[str] = Field(default_factory=list)
    supports_rubric_items: List[str] = Field(default_factory=list)
    lean_file: str
    status: str
    compiled: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""


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
    formal_steps: List[FormalStep] = Field(default_factory=list)


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
    required_formal_step_types: List[str] = Field(default_factory=list)
    depends_on_microclaim_ids: List[str] = Field(default_factory=list)
    dependencies_verified: bool = True
    formal_steps_verified: bool = True
    textual_evidence: bool
    lean_status: str
    supports_rubric_items: List[str] = Field(default_factory=list)


class AuditResponse(BaseModel):
    problem_id: str
    score: float
    max_score: float
    verdict: str
    extracted_claims: ClaimExtraction
    formal_steps: List[FormalStepResult]
    rubric_assessment: RubricAssessment
    lean_certificate: LeanCertificate
    microclaims: List[MicroclaimResult]
    feedback: str
    artifact_dir: Optional[str] = None
