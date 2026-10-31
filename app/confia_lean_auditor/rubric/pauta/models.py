"""Versioned, closed contracts for evidence -> rubric rules -> points.

Evidence is an upstream assertion, not raw student text or a proof to execute.
Decimal points keep caps and addition exact, including fractional rubrics.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, field_validator, model_validator

Identifier = Annotated[StrictStr, Field(min_length=1, pattern=r"^\S+$")]
Points = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]
EvidenceStatus = Literal["supported", "refuted", "indeterminate", "technical_error"]
EvidenceOrigin = Literal["deterministic", "student_lean", "reference_lean", "secondary", "semantic", "diagram"]
Strategy = Literal["additive", "banded", "max_of", "all_of", "any_of", "carry_forward"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ConditionalContext(Contract):
    """All three carry-forward facts must concern this SAME adopted result."""
    rule_id: Identifier
    prior_obligation_id: Identifier
    adopted_result_ref: Identifier


class ObligationEvidence(Contract):
    obligation_id: Identifier
    status: EvidenceStatus
    origin: EvidenceOrigin
    evidence_refs: tuple[Identifier, ...] = ()
    attributable_to_student: StrictBool = False
    conditional_on: Optional[ConditionalContext] = None

    @model_validator(mode="after")
    def validate_references(self):
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("Duplicate evidence references")
        if self.status in {"supported", "refuted"} and not self.evidence_refs:
            raise ValueError("A mathematical decision requires existing evidence references")
        if self.origin == "secondary" and self.status == "refuted":
            raise ValueError("A secondary denial is not a mathematical refutation")
        return self


class PautaEvidence(Contract):
    schema_version: Literal["pauta-evidence.v1"] = "pauta-evidence.v1"
    problem_id: Identifier
    solution_id: Identifier
    obligations: tuple[ObligationEvidence, ...] = ()

    @model_validator(mode="after")
    def unique_obligations(self):
        ids = [e.obligation_id for e in self.obligations]
        if len(ids) != len(set(ids)):
            raise ValueError("Resolve duplicate/conflicting evidence upstream")
        return self


class PautaObligation(Contract):
    id: Identifier
    description: str
    accepted_origins: tuple[EvidenceOrigin, ...] = ("deterministic", "student_lean")

    @model_validator(mode="after")
    def origins(self):
        if not self.accepted_origins or len(set(self.accepted_origins)) != len(self.accepted_origins):
            raise ValueError("Declare a nonempty, unique origin policy")
        if "reference_lean" in self.accepted_origins:
            raise ValueError("Reference proof alone cannot establish student achievement")
        return self


class CarryForwardContract(Contract):
    prior_obligation_id: Identifier
    adoption_obligation_id: Identifier
    dependency_obligation_id: Identifier
    coherence_obligation_id: Identifier

    def obligation_ids(self):
        return (self.prior_obligation_id, self.adoption_obligation_id,
                self.dependency_obligation_id, self.coherence_obligation_id)

    @model_validator(mode="after")
    def distinct_facts(self):
        if len(set(self.obligation_ids())) != 4:
            raise ValueError("Prior result, adoption, dependency and coherence must be distinct")
        return self


class PautaRule(Contract):
    id: Identifier
    description: str = ""
    scoring_strategy: Strategy
    max_points: Points
    obligation_ids: tuple[Identifier, ...] = ()
    children: tuple[PautaRule, ...] = ()
    carry_forward: Optional[CarryForwardContract] = None

    @field_validator("max_points", mode="before")
    @classmethod
    def numeric_points(cls, value):
        if isinstance(value, bool):
            raise ValueError("Boolean is not a point value")
        return value

    @model_validator(mode="after")
    def shape(self):
        strategy = self.scoring_strategy
        if len(set(self.obligation_ids)) != len(self.obligation_ids):
            raise ValueError("Duplicate obligations in rule")
        if strategy in {"all_of", "any_of"}:
            if not self.obligation_ids or self.children or self.carry_forward:
                raise ValueError("Predicates require obligations only; empty predicates cannot award")
        elif strategy == "carry_forward":
            if not self.carry_forward or self.children or self.obligation_ids:
                raise ValueError("carry_forward requires its explicit contract only")
        else:
            if not self.children or self.obligation_ids or self.carry_forward:
                raise ValueError("Combinators require child rules only")
            available = (sum(c.max_points for c in self.children) if strategy == "additive"
                         else max(c.max_points for c in self.children))
            if self.max_points > available:
                raise ValueError("Rule cap exceeds reachable child points")
            if strategy != "additive" and self.max_points != available:
                raise ValueError("Alternative/band cap must equal the highest child cap")
            if strategy == "banded" and any(c.scoring_strategy not in {"all_of", "any_of", "carry_forward"}
                                            for c in self.children):
                raise ValueError("Each band must be an integral predicate, not a partial subtotal")
        return self


class PautaItem(PautaRule):
    pass


class PautaConfig(Contract):
    schema_version: Literal["pauta.v1"] = "pauta.v1"
    problem_id: Identifier
    title: str
    max_score: Points
    # Withhold is an explicit scoring convention, never a mathematical refutation.
    unresolved_policy: Literal["defer", "withhold"] = "defer"
    obligations: tuple[PautaObligation, ...]
    items: tuple[PautaItem, ...]

    @field_validator("max_score", mode="before")
    @classmethod
    def numeric_score(cls, value):
        return PautaRule.numeric_points(value)

    @model_validator(mode="after")
    def references_and_totals(self):
        ids = [o.id for o in self.obligations]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("Obligation IDs must be nonempty and unique")
        if not self.items or sum(i.max_points for i in self.items) != self.max_score:
            raise ValueError("Item caps must sum exactly to max_score")
        seen = set()

        def visit(rule):
            if rule.id in seen:
                raise ValueError("Rule/item IDs must be globally unique")
            seen.add(rule.id)
            refs = rule.carry_forward.obligation_ids() if rule.carry_forward else rule.obligation_ids
            if not set(refs) <= set(ids):
                raise ValueError("Rule references an undeclared obligation")
            for child in rule.children:
                visit(child)

        for item in self.items:
            visit(item)
        return self


class ObligationDecision(Contract):
    obligation_id: Identifier
    input_status: Optional[EvidenceStatus] = None
    effective_status: EvidenceStatus
    origin: Optional[EvidenceOrigin] = None
    evidence_refs: tuple[Identifier, ...] = ()
    conditional_on: Optional[ConditionalContext] = None
    reason: str


class PautaDecision(Contract):
    item_id: Identifier
    scoring_strategy: Strategy
    max_points: Points
    points_awarded: Optional[Points]
    known_points: Points
    possible_points: Points
    status: Literal["decided", "indeterminate", "technical_error"]
    fully_satisfied: bool
    satisfied_obligations: tuple[str, ...]
    unsatisfied_obligations: tuple[str, ...]
    indeterminate_obligations: tuple[str, ...]
    technical_error_obligations: tuple[str, ...]
    selected_band: Optional[str] = None
    selected_method_path: Optional[str] = None
    carry_forward_applied: bool = False
    evidence_refs: tuple[str, ...]
    credit_evidence_refs: tuple[str, ...]
    needs_review: bool
    reason: str
    obligations: tuple[ObligationDecision, ...] = ()
    children: tuple[PautaDecision, ...] = ()

    @model_validator(mode="after")
    def bounded(self):
        if not self.known_points <= self.possible_points <= self.max_points:
            raise ValueError("Invalid scoring interval")
        if self.points_awarded is not None and self.points_awarded != self.known_points:
            raise ValueError("Only evidenced points may be awarded, never potential points")
        if (self.status == "decided") != (self.known_points == self.possible_points):
            raise ValueError("Decision status must preserve scoring uncertainty")
        if self.status == "decided" and self.points_awarded is None:
            raise ValueError("A decided score must expose its known points")
        if self.status == "technical_error" and self.points_awarded is not None:
            raise ValueError("An unresolved technical failure must remain pending")
        if self.known_points > 0 and not self.credit_evidence_refs:
            raise ValueError("Positive points require traceable credit evidence")
        if not set(self.credit_evidence_refs) <= set(self.evidence_refs):
            raise ValueError("Credit references must be among the observed references")
        return self


class PautaAssessment(Contract):
    schema_version: Literal["pauta-decision.v1"] = "pauta-decision.v1"
    pauta_version: Literal["pauta.v1"] = "pauta.v1"
    config_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    evidence_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    problem_id: Identifier
    solution_id: Identifier
    unresolved_policy: Literal["defer", "withhold"]
    max_score: Points
    score: Optional[Points]
    known_points: Points
    possible_points: Points
    needs_review: bool
    items: tuple[PautaDecision, ...]

    @model_validator(mode="after")
    def totals(self):
        if sum(i.max_points for i in self.items) != self.max_score:
            raise ValueError("Item caps do not match assessment cap")
        if not self.known_points <= self.possible_points <= self.max_score:
            raise ValueError("Invalid assessment interval")
        expected = None if any(i.points_awarded is None for i in self.items) else sum(i.points_awarded for i in self.items)
        if self.score != expected:
            raise ValueError("Score must preserve pending items and sum awarded points")
        if self.known_points != sum(i.known_points for i in self.items) or self.possible_points != sum(i.possible_points for i in self.items):
            raise ValueError("Assessment interval must sum item intervals")
        return self
