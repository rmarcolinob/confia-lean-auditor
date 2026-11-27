"""DY3 evidence contracts. No model-supplied score or implicit approval."""

from typing import Literal, Optional
from decimal import Decimal
from pydantic import Field, model_validator, model_serializer
from .versions import GRADER_VERSION
from confia_lean_auditor.submissions.schemas import SubmissionModel, Sha256


class DynamicGradingContext(SubmissionModel):
    semantic_policy: Optional[Literal['dynamic-semantic.v1']] = None

    @model_serializer(mode='wrap')
    def preserve_context(self, handler):
        data=handler(self)
        if 'semantic_policy' not in self.model_fields_set: data.pop('semantic_policy',None)
        return data

    engine_mode: Literal["DYNAMIC"] = "DYNAMIC"
    problem_id: str
    package_id: str
    package_version: int
    package_sha256: Sha256
    statement_version: int
    statement_sha256: Sha256
    preparation_id: str
    preparation_version: int
    preparation_sha256: Sha256
    rubric_id: str
    rubric_version: int
    rubric_sha256: Sha256
    allow_preparation_review: bool = False
    grader_version: Literal["dynamic-grader.v1", "dynamic-grader.r1-substitution", "dynamic-grader.r1"] = GRADER_VERSION


class StudentClaim(SubmissionModel):
    schema_version: Literal["student-claim.v1", "student-claim.r1"] = "student-claim.v1"
    substitution: Optional[dict] = None
    claim_id: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str
    normalized: str
    claim_type: str
    subject: str
    dependencies: list[str] = Field(default_factory=list)
    polarity: Literal["POSITIVE", "NEGATIVE", "UNKNOWN"] = "POSITIVE"
    adoption: Literal["ADOPTED", "ABANDONED", "HYPOTHETICAL", "AMBIGUOUS"] = "ADOPTED"
    fidelity: Literal[
        "FAITHFUL", "SUPPORTED_NORMALIZATION", "PARTIAL", "AMBIGUOUS", "UNSUPPORTED"
    ]
    strategy_context: str = "UNKNOWN_STRATEGY"
    verification_status: Literal[
        "VERIFIED", "REFUTED", "INCOMPLETE", "NOT_ATTEMPTED", "ERROR", "REVIEW_ONLY"
    ]
    verification_detail: str
    verifier: str = "dynamic-exact-polynomial.v1"
    components: list[dict] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    verified_values: list[str] = Field(default_factory=list)


    @model_serializer(mode="wrap")
    def preserve_legacy_wire_shape(self, handler):
        # Historical audit/review receipts hash their serialized models. Merely
        # reading v1 evidence must not add new default keys to those receipts.
        result = handler(self)
        if self.schema_version == "student-claim.v1":
            result.pop("schema_version", None)
            if self.substitution is None:
                result.pop("substitution", None)
        return result


class RubricBinding(SubmissionModel):
    criterion_id: str
    claim_id: str
    binding_type: str
    evidence: str
    diagnostic_confidence: Literal["EXACT", "UNRESOLVED"]
    status: Literal["SUPPORTED", "REVIEW_ONLY"]


class DynamicRubricDecision(SubmissionModel):
    dependency_trace: Optional[dict] = None
    semantic_trace: Optional[dict] = None

    @model_serializer(mode='wrap')
    def preserve_decision(self, handler):
        data=handler(self)
        if 'semantic_trace' not in self.model_fields_set: data.pop('semantic_trace',None)
        if 'dependency_trace' not in self.model_fields_set: data.pop('dependency_trace',None)
        return data

    criterion_id: str
    description: str
    max_points: Decimal = Field(ge=0)
    suggested_points: Decimal = Field(ge=0)
    automation: Literal["AUTO_AWARD", "AUTO_VETO", "REVIEW_ONLY", "SEMANTIC_SUGGESTION"]
    sufficiency: Literal[
        "COMPLETE", "PARTIAL", "NOT_SATISFIED", "INSUFFICIENT", "CONFLICT"
    ]
    claim_ids: list[str]
    checker_results: list[dict]
    evidence: list[str]
    explanation: str
    review_required: bool
    warnings: list[str]

    @model_validator(mode="after")
    def bounded(self):
        if self.suggested_points > self.max_points or (
            self.automation == "REVIEW_ONLY" and self.suggested_points
        ):
            raise ValueError("unsafe rubric credit")
        return self


class DynamicStudentSolutionAnalysis(SubmissionModel):
    transcription_version: str
    source_sha256: Sha256
    segments: list[dict]
    claims: list[StudentClaim]
    strategy_status: Literal[
        "KNOWN_STRATEGY",
        "VALID_ALTERNATIVE_CANDIDATE",
        "UNKNOWN_STRATEGY",
        "MIXED_INCOMPLETE",
    ]
    strategy_candidate: str
    final_answer_candidates: list[str]
    warnings: list[str]
    provenance: dict


class DynamicAuditResult(SubmissionModel):
    engine_mode: Literal["DYNAMIC"] = "DYNAMIC"
    problem_id: str
    context: DynamicGradingContext
    score: Optional[float]
    suggested_score: Optional[float]
    max_score: float
    review_required: bool
    verdict: str
    uncertainty: list[str]
    reviewed_components: list[str]
    unreviewed_components: list[str]
    analysis: DynamicStudentSolutionAnalysis
    bindings: list[RubricBinding]
    decisions: list[DynamicRubricDecision]
    events: list[dict]
    rubric_assessment: dict
    feedback: str
    artifact_dir: str
    reproducibility: None = None

    @model_validator(mode="after")
    def coherent(self):
        total = sum((d.suggested_points for d in self.decisions), Decimal(0))
        maximum = sum((d.max_points for d in self.decisions), Decimal(0))
        if (
            (None if any(d.semantic_trace and d.semantic_trace.get("decision")=="review" for d in self.decisions) else float(total)) != self.score
            or self.score != self.suggested_score
            or float(maximum) != self.max_score
        ):
            raise ValueError("score must be the sum of bounded rubric decisions")
        if len({d.criterion_id for d in self.decisions}) != len(self.decisions):
            raise ValueError("duplicate criterion")
        return self
