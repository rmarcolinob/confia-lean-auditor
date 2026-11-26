"""Versioned DY2 evidence contracts. Provider proposals never supply check results."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import ConfigDict, Field, model_validator
from confia_lean_auditor.submissions.schemas import SubmissionModel, Sha256


class Evidence(SubmissionModel):
    model_config = ConfigDict(extra='forbid', frozen=True, allow_inf_nan=False)


class Warning(Evidence):
    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=3000)
    requires_review: bool


class Assumption(Evidence):
    text: str
    source: Literal['EXPLICIT', 'INFERRED']


class MathematicalObject(Evidence):
    name: str
    domain: str
    constraints: tuple[str, ...]


Capability = Literal['EXACT_ARITHMETIC', 'SYMBOLIC_ALGEBRA', 'NUMERICAL',
    'FINITE_ENUMERATION', 'DETERMINISTIC', 'LEAN_CANDIDATE', 'SEMANTIC_RESIDUAL', 'REVIEW_ONLY']


class CheckSpec(Evidence):
    kind: Literal['EQUALITY', 'ROOT_SET', 'NONE']
    left: str = Field(max_length=2048)
    right: str = Field(max_length=2048)
    variable: str = Field(max_length=20)
    values: tuple[str, ...] = Field(max_length=20)


class ReferenceClaim(Evidence):
    claim_id: str = Field(pattern=r'^[A-Za-z0-9_-]{1,80}$')
    text: str = Field(min_length=1, max_length=3000)
    normalized_form: str
    claim_type: str
    dependencies: tuple[str, ...]
    mathematical_objects: tuple[str, ...]
    proposed_verifier: Capability
    verifier_reason: str
    formalizability_candidate: bool
    check: CheckSpec


class FinalResult(Evidence):
    kind: Literal['ROOT_SET', 'EXPRESSION', 'TEXT', 'NO_SOLUTION', 'NON_UNIQUE', 'UNKNOWN']
    text: str
    values: tuple[str, ...]
    supporting_claim_ids: tuple[str, ...]


class CandidateSolution(Evidence):
    solution_id: str
    strategy_id: str
    strategy_label: str
    claims: tuple[ReferenceClaim, ...] = Field(max_length=40)
    final_result: FinalResult
    uncertainties: tuple[str, ...]


class AlternativeStrategy(Evidence):
    strategy_id: str
    description: str
    expected_key_claim_ids: tuple[str, ...]


class PreparationProposal(Evidence):
    mathematical_domain: str
    normalized_problem: str
    data: tuple[str, ...]
    assumptions: tuple[Assumption, ...]
    objects: tuple[MathematicalObject, ...]
    target: str
    expects_unique_result: bool
    candidate_reference_solutions: tuple[CandidateSolution, ...] = Field(max_length=5)
    alternative_strategies: tuple[AlternativeStrategy, ...] = Field(max_length=10)
    warnings: tuple[Warning, ...] = Field(max_length=40)
    uncertainties: tuple[str, ...] = Field(max_length=40)

    @model_validator(mode='after')
    def references(self):
        strategies = [s.strategy_id for s in self.alternative_strategies]
        solutions = [s.solution_id for s in self.candidate_reference_solutions]
        claims = [c.claim_id for s in self.candidate_reference_solutions for c in s.claims]
        if any(len(x) != len(set(x)) for x in (strategies, solutions, claims)):
            raise ValueError('duplicate preparation IDs')
        for s in self.candidate_reference_solutions:
            if s.strategy_id not in strategies:
                raise ValueError('missing strategy')
            prior = set()
            for c in s.claims:
                if not set(c.dependencies) <= prior:
                    raise ValueError('claims must depend on prior local claims')
                prior.add(c.claim_id)
            if not set(s.final_result.supporting_claim_ids) <= prior:
                raise ValueError('unknown final result claim')
        if any(not set(s.expected_key_claim_ids) <= set(claims) for s in self.alternative_strategies):
            raise ValueError('unknown strategy claim')
        return self


class GenerationProvenance(Evidence):
    provider: str
    requested_model: str
    returned_model: str
    reasoning_effort: Optional[str]
    prompt_version: str
    schema_version: str
    input_sha256: Sha256
    output_sha256: Sha256
    response_id: Optional[str]
    created_at: datetime
    code_sha: Optional[str]
    code_content_sha256: Optional[Sha256] = None
    max_output_tokens: int
    raw_output: str = Field(max_length=200000)


class CheckResult(Evidence):
    claim_id: str
    capability: Capability
    reason: str
    available: bool
    requires_additional_input: bool
    status: Literal['VERIFIED_WITHIN_SCOPE', 'CONTRADICTED', 'UNVERIFIED']
    detail: str
    scope: str
    verifier_version: str
    formal_status: Literal['FORMAL_NOT_ATTEMPTED'] = 'FORMAL_NOT_ATTEMPTED'


class CandidateCheck(Evidence):
    solution_id: str
    status: Literal['VERIFIED_WITHIN_SCOPE', 'PARTIALLY_VERIFIED', 'CONTRADICTED', 'UNRESOLVED']
    final_result_verified: bool


class StrategyCheck(Evidence):
    strategy_id: str
    status: Literal['VERIFIED_WITHIN_SCOPE', 'PARTIALLY_VERIFIED', 'CONTRADICTED', 'UNRESOLVED']
    limitation: str = 'Somente claims declarados; legitimidade pedagógica e interpretação requerem revisão.'


class PreparationAnalysis(Evidence):
    verifier_plan: tuple[CheckResult, ...]
    candidate_checks: tuple[CandidateCheck, ...]
    strategy_checks: tuple[StrategyCheck, ...] = ()
    warnings: tuple[Warning, ...]
    trust_state: Literal['CHECKED_WITHIN_SCOPE', 'HUMAN_REVIEW_REQUIRED', 'UNAVAILABLE']
    automatic_correction_allowed: Literal[False] = False


class PreparationRecord(Evidence):
    preparation_id: str = Field(pattern=r'^dprep_[0-9a-f]{32}$')
    preparation_version: int = Field(ge=1)
    problem_id: str
    source_package_id: str
    statement_version: int = Field(ge=1)
    statement_sha256: Sha256
    status: Literal['PENDING', 'RUNNING', 'READY_FOR_REVIEW', 'REVIEW_REQUIRED', 'FAILED']
    created_at: datetime
    completed_at: Optional[datetime] = None
    requested_by: str
    reason: Optional[str] = None
    proposal: Optional[PreparationProposal] = None
    analysis: Optional[PreparationAnalysis] = None
    provenance: Optional[GenerationProvenance] = None
    failure_code: Optional[str] = None

    @model_validator(mode='after')
    def terminal(self):
        if self.status in {'READY_FOR_REVIEW', 'REVIEW_REQUIRED'}:
            if not all((self.completed_at, self.proposal, self.analysis, self.provenance)):
                raise ValueError('completed preparation requires evidence')
            expected = 'READY_FOR_REVIEW' if self.analysis.trust_state == 'CHECKED_WITHIN_SCOPE' else 'REVIEW_REQUIRED'
            if self.status != expected:
                raise ValueError('preparation trust/status mismatch')
        elif self.status == 'FAILED':
            if not self.failure_code or not self.completed_at:
                raise ValueError('failure requires code and completion time')
        elif any((self.proposal, self.analysis, self.completed_at, self.failure_code)):
            raise ValueError('in-flight preparation cannot contain a result')
        return self


class PreparationReference(Evidence):
    preparation_id: str
    preparation_version: int = Field(ge=1)
    preparation_sha256: Sha256


class CriterionEvidence(Evidence):
    mathematical_objective: str
    related_reference_claims: tuple[str, ...]
    accepted_alternative_strategies: tuple[str, ...]
    verifier_hints: tuple[Capability, ...]
    warnings: tuple[str, ...]


class SemanticReview(Evidence):
    warnings: tuple[Warning, ...] = Field(max_length=40)
    overlap_detected: bool
    vague_criteria: bool
    impossible_dependency: bool
    absent_information_required: bool
    unjustified_single_strategy: bool
    rationale: str
