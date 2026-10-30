from __future__ import annotations

from typing import Dict, List, Optional, Any, Literal, ClassVar

from pydantic import BaseModel, Field, model_serializer

from confia_lean_auditor.reproducibility.schemas import ReproducibilityMetadata


class AuditRequest(BaseModel):
    problem_id: str
    solution: str


class ReferenceVerificationModel(BaseModel):
    """Scope is additive; historical documents retain their serialized shape."""
    verification_scope: Optional[Literal["generated_reference"]] = None

    @model_serializer(mode="wrap")
    def preserve_reference_shape(self, handler):
        data = handler(self)
        if "verification_scope" not in self.model_fields_set:
            data.pop("verification_scope", None)
        return data


class FormalStep(ReferenceVerificationModel):
    id: str
    type: str
    description: str
    evidence: str
    lhs: str
    rhs: str
    lean_method: str = "ring"
    supports_claim_types: List[str] = Field(default_factory=list)
    supports_rubric_items: List[str] = Field(default_factory=list)


class FormalStepResult(ReferenceVerificationModel):
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


class ExtractedClaim(ReferenceVerificationModel):
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


class ScoringCompatibleModel(BaseModel):
    """New scoring fields must not retroactively change persisted result hashes."""
    scoring_fields: ClassVar[set[str]] = set()

    @model_serializer(mode="wrap")
    def preserve_scoring_shape(self, handler):
        data = handler(self)
        for name in self.scoring_fields - self.model_fields_set:
            data.pop(name, None)
        return data


class RubricItemResult(ScoringCompatibleModel):
    scoring_fields = {"verified_points", "suggested_points", "scoring_basis",
                      "scoring_evidence", "scoring_rationale", "positive_evidence"}
    id: str
    description: str
    detected: bool
    points: Optional[float]
    max_points: float
    evidence: Optional[str] = None
    claim_id: Optional[str] = None
    student_check_adjusted: bool = False
    adjustment_notes: List[str] = Field(default_factory=list)
    mathematical_status: Optional[Literal["supported", "refuted", "indeterminate"]] = None
    verification_status: Literal["available", "partial", "technical_error"] = "available"
    assessment_note: Optional[str] = None
    verified_points: Optional[float] = None
    suggested_points: Optional[float] = None
    scoring_basis: Optional[Literal["first_pass", "secondary_adjudication", "unscorable"]] = None
    scoring_evidence: List[str] = Field(default_factory=list)
    scoring_rationale: Optional[str] = None
    positive_evidence: Optional[Dict[str, Any]] = None


class RubricAssessment(ScoringCompatibleModel):
    scoring_fields = {"scoring_policy", "coverage", "estimated_points", "needs_review",
                      "unscorable_reason", "secondary_adjudication"}
    score: Optional[float]
    max_score: float
    items: List[RubricItemResult]
    assessment_status: Literal["complete", "partial", "indeterminate"] = "complete"
    evaluated_score: float = 0.0
    evaluated_max_score: float = 0.0
    scoring_policy: Optional[Literal["SCORE-POLICY-02"]] = None
    coverage: Optional[float] = None
    estimated_points: Optional[float] = None
    needs_review: Optional[bool] = None
    unscorable_reason: Optional[str] = None
    secondary_adjudication: Optional[Dict[str, Any]] = None


class LeanCertificate(ReferenceVerificationModel):
    status: str
    compiled: bool
    exit_code: int
    uses_forbidden_token: bool
    forbidden_tokens_found: List[str]
    stdout: str = ""
    stderr: str = ""
    lean_file: Optional[str] = None
    generated_theorems: List[str] = Field(default_factory=list)


class MicroclaimResult(ReferenceVerificationModel):
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
    verification_status: Literal["available", "partial", "technical_error"] = "available"


class PedagogicalEvidenceItem(BaseModel):
    id: str
    title: str
    result: str
    evidence: Optional[str] = None
    reliability: str
    explanation: str


class PedagogicalReport(ScoringCompatibleModel):
    scoring_fields = {"scoring_policy", "coverage", "estimated_points", "needs_review", "unscorable_reason"}
    summary: str
    result: str
    score: Optional[float]
    max_score: float
    verdict: str
    reliability: str
    evidence_items: List[PedagogicalEvidenceItem] = Field(default_factory=list)
    attention_points: List[str] = Field(default_factory=list)
    technical_record_available: bool = False
    verification_status: Literal["available", "partial", "technical_error"] = "available"
    assessment_status: Literal["complete", "partial", "indeterminate"] = "complete"
    evaluated_score: float = 0.0
    evaluated_max_score: float = 0.0
    scoring_policy: Optional[Literal["SCORE-POLICY-02"]] = None
    coverage: Optional[float] = None
    estimated_points: Optional[float] = None
    needs_review: Optional[bool] = None
    unscorable_reason: Optional[str] = None


class AuditResponse(ScoringCompatibleModel):
    scoring_fields = {"scoring_policy", "evaluated_score", "evaluated_max_score", "coverage",
                      "estimated_points", "needs_review", "unscorable_reason"}
    problem_id: str
    score: Optional[float]
    max_score: float
    verdict: str
    extracted_claims: ClaimExtraction
    formal_steps: List[FormalStepResult]
    rubric_assessment: RubricAssessment
    lean_certificate: LeanCertificate
    microclaims: List[MicroclaimResult]

    student_claims: List[Dict[str, Any]] = Field(default_factory=list)
    student_claim_checks: List[Dict[str, Any]] = Field(default_factory=list)
    feedback: str
    pedagogical_report: Optional[PedagogicalReport] = None
    artifact_dir: Optional[str] = None
    reproducibility: Optional[ReproducibilityMetadata] = None
    scoring_policy: Optional[Literal["SCORE-POLICY-02"]] = None
    evaluated_score: Optional[float] = None
    evaluated_max_score: Optional[float] = None
    coverage: Optional[float] = None
    estimated_points: Optional[float] = None
    needs_review: Optional[bool] = None
    unscorable_reason: Optional[str] = None

    @model_serializer(mode="wrap")
    def preserve_legacy_digest(self, handler):
        data = handler(self)
        # Old audit.json/result hashes cover the original shape. Never add a
        # default field to their hashed representation or retroactively rehash.
        if self.reproducibility is None:
            data.pop("reproducibility", None)
        for name in self.scoring_fields - self.model_fields_set:
            data.pop(name, None)
        return data
