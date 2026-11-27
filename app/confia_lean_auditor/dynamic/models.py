"""DY1 immutable content; approval/current state is projected from lifecycle records."""
from datetime import datetime, timezone
from typing import Annotated, Literal, Optional

from pydantic import ConfigDict, Field, StringConstraints, field_validator, model_validator, model_serializer
from confia_lean_auditor.submissions.schemas import SubmissionModel, Sha256
from confia_lean_auditor.submissions.integrity import model_sha256 as _model_sha256
from .preparation_models import (PreparationRecord, PreparationReference, CriterionEvidence, GenerationProvenance, SemanticReview, Warning)

def model_sha256(model):
    # Preserve DY1 hashes when optional DY2 fields were absent in stored bytes.
    return _model_sha256(model, exclude_unset=True)
from confia_lean_auditor.teacher_decisions.models import Points
from confia_lean_auditor.core.correction_mode import CorrectionMode

ProblemId = Annotated[str, StringConstraints(pattern=r"^dyn_[0-9a-f]{32}$")]
PackageId = Annotated[str, StringConstraints(pattern=r"^dpkg_[0-9a-f]{32}$")]
RubricId = Annotated[str, StringConstraints(pattern=r"^drub_[0-9a-f]{32}$")]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)]
CriterionId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,80}$")]
RubricStatus = Literal["DRAFT_AI", "DRAFT_TEACHER", "TEACHER_EDITED", "APPROVED", "SUPERSEDED"]


class Immutable(SubmissionModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, frozen=True)

    @field_validator("created_at", "approved_at", "timestamp", check_fields=False)
    @classmethod
    def utc(cls, value):
        if value.tzinfo is None:
            raise ValueError("timezone required")
        return value.astimezone(timezone.utc)


class Actor(Immutable):
    actor_id: str = Field(min_length=1, max_length=100)
    kind: Literal["TEACHER", "TECHNICAL_DEMO"]
    tenant_id: Optional[str] = None


class AssessmentReference(Immutable):
    assessment_id: str = Field(pattern=r"^asmt_[0-9a-f]{32}$")
    assessment_definition_sha256: Optional[Sha256] = None
    # Context only in DY1; adding an assessment item is a later integration.


class Provenance(Immutable):
    origin: Literal["TEACHER", "TECHNICAL_DEMO", "AI"]
    schema_version: Literal["dynamic-provenance.v1"] = "dynamic-provenance.v1"
    model_provenance: Optional[dict] = None


class CreditLevel(Immutable):
    level_id: CriterionId
    points: Points = Field(gt=0)
    description: Text


class DependencyRule(Immutable):
    criterion_id: CriterionId
    kind: Literal['MATHEMATICAL', 'PROCEDURAL', 'CARRY_FORWARD']
    condition: Text
    minimum_points: Optional[Points] = Field(default=None, gt=0)

    @model_validator(mode='after')
    def threshold_only_for_mathematics(self):
        if self.minimum_points is not None and self.kind != 'MATHEMATICAL':
            raise ValueError('only mathematical dependencies have score thresholds')
        return self


class RubricCriterion(Immutable):
    credit_levels: tuple[CreditLevel, ...] = Field(default=(), max_length=20)
    dependency_rules: tuple[DependencyRule, ...] = Field(default=(), max_length=100)

    @model_serializer(mode='wrap')
    def preserve_historical_shape(self, handler):
        data = handler(self)
        for key in ('credit_levels', 'dependency_rules'):
            if key not in self.model_fields_set: data.pop(key, None)
        return data

    @model_validator(mode='after')
    def authorized_levels_and_rules(self):
        if len({v.level_id for v in self.credit_levels}) != len(self.credit_levels):
            raise ValueError('duplicate credit level')
        if any(v.points >= self.max_points for v in self.credit_levels):
            raise ValueError('partial levels must be strictly below criterion maximum')
        ids = [v.criterion_id for v in self.dependency_rules]
        if len(set(ids)) != len(ids) or not set(ids) <= set(self.dependencies):
            raise ValueError('dependency rules must name distinct declared dependencies')
        return self

    criterion_id: CriterionId
    title: str = Field(min_length=1, max_length=160)
    description: Text
    max_points: Points
    order: int = Field(ge=1, le=100)
    dependencies: tuple[CriterionId, ...] = ()
    notes: str = Field(default="", max_length=2000)
    teacher_guidance: str = Field(default="", max_length=2000)
    evidence: Optional[CriterionEvidence] = None
    # Deliberately no checker/claim_type requirement. Future bindings are a
    # versioned addition, not opaque, executable instructions in teacher text.

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        if not value.strip():
            raise ValueError("criterion title required")
        return value.strip()


class RubricContent(Immutable):
    max_score: Points = Field(gt=0)
    criteria: tuple[RubricCriterion, ...] = Field(default=(), max_length=100)

    @model_validator(mode="after")
    def coherent(self):
        ids = [c.criterion_id for c in self.criteria]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate criterion ID")
        if [c.order for c in self.criteria] != list(range(1, len(ids) + 1)):
            raise ValueError("criterion order must be contiguous")
        if self.criteria and sum(c.max_points for c in self.criteria) != self.max_score:
            raise ValueError("criterion points must sum to max_score")
        graph = {c.criterion_id: c.dependencies for c in self.criteria}
        for key, deps in graph.items():
            if len(deps) != len(set(deps)) or not set(deps) <= set(ids):
                raise ValueError("invalid criterion dependencies")
        by_id = {c.criterion_id:c for c in self.criteria}
        for c in self.criteria:
            for rule in c.dependency_rules:
                if rule.minimum_points is not None and rule.minimum_points > by_id[rule.criterion_id].max_points:
                    raise ValueError('dependency threshold exceeds prerequisite maximum')
        done, visiting = set(), set()
        def visit(key):
            if key in visiting:
                raise ValueError("cyclic criterion dependencies")
            if key in done:
                return
            visiting.add(key)
            for dep in graph[key]:
                visit(dep)
            visiting.remove(key)
            done.add(key)
        for key in graph:
            visit(key)
        return self


class DynamicProblem(Immutable):
    problem_id: ProblemId
    correction_mode: Literal[CorrectionMode.DYNAMIC] = CorrectionMode.DYNAMIC
    created_at: datetime
    created_by: Actor
    assessment_reference: Optional[AssessmentReference] = None


class StatementVersion(Immutable):
    problem_id: ProblemId
    version_number: int = Field(ge=1)
    title: str = Field(default="", max_length=160)
    statement: Text
    max_score: Points = Field(gt=0)
    created_at: datetime
    created_by: Actor
    provenance: Provenance


class RubricVersion(RubricContent):
    rubric_id: RubricId
    problem_id: ProblemId
    statement_version: int = Field(ge=1)
    statement_sha256: Sha256
    version_number: int = Field(ge=1)
    draft_status: Literal["DRAFT_AI", "DRAFT_TEACHER", "TEACHER_EDITED"]
    preparation_reference: Optional[PreparationReference] = None
    generation: Optional["RubricGeneration"] = None
    supersedes_id: Optional[RubricId] = None
    created_at: datetime
    created_by: Actor
    provenance: Provenance


class RubricGeneration(Immutable):
    preparation: PreparationReference
    generation: GenerationProvenance
    semantic_review: SemanticReview
    review_provenance: GenerationProvenance
    warnings: tuple[Warning, ...]
    previous_rubric_id: Optional[RubricId] = None
    reason: Optional[str] = None


class FuturePreparation(Immutable):
    """Reserved extension boundary. DY1 rejects nonempty preparation payloads."""
    normalized_interpretation: None = None
    assumptions_domain: None = None
    candidate_reference_solutions: None = None
    alternative_strategies: None = None
    verifier_plan: None = None
    warnings: tuple[str, ...] = ()
    model_provenance: None = None


class DynamicProblemPackage(Immutable):
    package_id: PackageId
    problem_id: ProblemId  # Stable question reference, even before an assessment exists.
    assessment_reference: Optional[AssessmentReference] = None
    package_version: int = Field(ge=1)
    statement_version: int = Field(ge=1)
    statement_sha256: Sha256
    rubric_id: Optional[RubricId] = None
    rubric_version: Optional[int] = Field(default=None, ge=1)
    rubric_sha256: Optional[Sha256] = None
    preparation_status: Literal["NOT_PREPARED", "READY_FOR_REVIEW", "REVIEW_REQUIRED"] = "NOT_PREPARED"
    preparation_reference: Optional[PreparationReference] = None
    preparation: FuturePreparation = Field(default_factory=FuturePreparation)
    created_at: datetime
    created_by: Actor
    provenance: Provenance

    @model_validator(mode="after")
    def rubric_binding(self):
        refs = (self.rubric_id, self.rubric_version, self.rubric_sha256)
        if any(x is not None for x in refs) != all(x is not None for x in refs):
            raise ValueError("incomplete rubric binding")
        return self


class Approval(Immutable):
    package_id: PackageId
    rubric_id: RubricId
    approved_at: datetime
    approved_by: Actor
    package_sha256: Sha256
    rubric_sha256: Sha256
    acknowledged_warnings: bool = False


class DynamicEvent(Immutable):
    event_id: str
    event_type: Literal["dynamic_problem_created", "problem_statement_version_created",
        "rubric_draft_created", "rubric_edited", "rubric_approved", "rubric_superseded",
        "dynamic_problem_package_activated", "preparation_pending", "preparation_running",
        "preparation_completed", "preparation_failed", "preparation_superseded", "rubric_suggestion_failed"]
    problem_id: ProblemId
    timestamp: datetime
    actor: Actor
    statement_version: int
    package_id: PackageId
    package_version: int
    rubric_id: Optional[RubricId] = None
    rubric_version: Optional[int] = None
    reason: Optional[str] = None
    preparation_id: Optional[str] = None
    generation_provenance: Optional[GenerationProvenance] = None


class DynamicDocument(Immutable):
    schema_version: Literal["dynamic-document.v1"] = "dynamic-document.v1"
    revision: int = Field(ge=1)
    problem: DynamicProblem
    statements: tuple[StatementVersion, ...]
    rubrics: tuple[RubricVersion, ...] = ()
    packages: tuple[DynamicProblemPackage, ...]
    approvals: tuple[Approval, ...] = ()
    events: tuple[DynamicEvent, ...]
    current_package_id: Optional[PackageId] = None
    preparations: tuple[PreparationRecord, ...] = ()

    @model_validator(mode="after")
    def bindings(self):
        pid = self.problem.problem_id
        if not self.statements or not self.packages:
            raise ValueError("statement and package required")
        for rows, field in ((self.statements, "version_number"), (self.rubrics, "version_number"),
                            (self.packages, "package_version")):
            if [getattr(x, field) for x in rows] != list(range(1, len(rows) + 1)):
                raise ValueError("non-contiguous versions")
            if any(x.problem_id != pid for x in rows):
                raise ValueError("cross-problem record")
        rubrics = {x.rubric_id: x for x in self.rubrics}
        packages = {x.package_id: x for x in self.packages}
        if len(rubrics) != len(self.rubrics) or len(packages) != len(self.packages):
            raise ValueError("duplicate IDs")
        previous = set()
        for r in self.rubrics:
            if r.statement_version > len(self.statements):
                raise ValueError("unknown statement")
            s = self.statements[r.statement_version - 1]
            if r.statement_sha256 != model_sha256(s) or r.max_score != s.max_score:
                raise ValueError("rubric statement mismatch")
            if r.supersedes_id and r.supersedes_id not in previous:
                raise ValueError("invalid rubric predecessor")
            previous.add(r.rubric_id)
        for p in self.packages:
            if p.statement_version > len(self.statements) or p.assessment_reference != self.problem.assessment_reference:
                raise ValueError("package scope mismatch")
            if p.statement_sha256 != model_sha256(self.statements[p.statement_version - 1]):
                raise ValueError("package statement mismatch")
            if p.rubric_id:
                r = rubrics.get(p.rubric_id)
                if not r or (r.statement_version, r.version_number, model_sha256(r)) != (p.statement_version, p.rubric_version, p.rubric_sha256):
                    raise ValueError("package rubric mismatch")
        approved = set()
        for a in self.approvals:
            p = packages.get(a.package_id)
            if not p or p.package_id in approved or p.rubric_id != a.rubric_id or not rubrics[a.rubric_id].criteria:
                raise ValueError("invalid approval")
            if (a.package_sha256, a.rubric_sha256) != (model_sha256(p), p.rubric_sha256):
                raise ValueError("approval digest mismatch")
            if a.approved_at < p.created_at or a.approved_by != self.problem.created_by:
                raise ValueError("invalid approval actor/time")
            approved.add(p.package_id)
        if self.current_package_id:
            p = packages.get(self.current_package_id)
            if not p or p.package_id not in approved or p.statement_version != len(self.statements):
                raise ValueError("current package must be approved for current statement")
        if len({e.event_id for e in self.events}) != len(self.events):
            raise ValueError("duplicate events")
        for e in self.events:
            p = packages.get(e.package_id)
            if not p or e.problem_id != pid or e.actor != self.problem.created_by or (
                    e.statement_version, e.package_version, e.rubric_id, e.rubric_version) != (
                    p.statement_version, p.package_version, p.rubric_id, p.rubric_version):
                raise ValueError("invalid event binding")
        prep_by_id = {}
        version = 0
        for preparation in self.preparations:
            source = packages.get(preparation.source_package_id)
            if not source or preparation.problem_id != pid or preparation.statement_version != source.statement_version or preparation.statement_sha256 != source.statement_sha256 or preparation.requested_by != self.problem.created_by.actor_id:
                raise ValueError('invalid preparation binding')
            old = prep_by_id.get(preparation.preparation_id)
            if old is None:
                version += 1
                if preparation.status != 'PENDING' or preparation.preparation_version != version:
                    raise ValueError('preparation must begin pending with contiguous version')
            else:
                allowed = {'PENDING': {'RUNNING', 'FAILED'}, 'RUNNING': {'READY_FOR_REVIEW', 'REVIEW_REQUIRED', 'FAILED'}}
                if preparation.status not in allowed.get(old.status, set()):
                    raise ValueError('invalid preparation transition')
                for key in ('preparation_version', 'statement_version', 'statement_sha256', 'source_package_id', 'created_at', 'requested_by', 'reason'):
                    if getattr(old, key) != getattr(preparation, key): raise ValueError('preparation identity changed')
            prep_by_id[preparation.preparation_id] = preparation
        def validate_preparation(reference, statement_version):
            if reference is None: return
            prep = prep_by_id.get(reference.preparation_id)
            if not prep or prep.status not in {'READY_FOR_REVIEW', 'REVIEW_REQUIRED'} or (prep.preparation_version, model_sha256(prep), prep.statement_version) != (reference.preparation_version, reference.preparation_sha256, statement_version):
                raise ValueError('invalid preparation reference')
        for e in self.events:
            if e.preparation_id and e.preparation_id not in prep_by_id:
                raise ValueError('event refers to unknown preparation')
        for r in self.rubrics:
            validate_preparation(r.preparation_reference, r.statement_version)
            if r.generation and r.generation.preparation != r.preparation_reference:
                raise ValueError('rubric generation binding mismatch')
        for p in self.packages:
            validate_preparation(p.preparation_reference, p.statement_version)
            if p.rubric_id and rubrics[p.rubric_id].preparation_reference != p.preparation_reference:
                raise ValueError('package preparation/rubric mismatch')
            if p.preparation_reference and p.preparation_status != prep_by_id[p.preparation_reference.preparation_id].status:
                raise ValueError('package preparation status mismatch')
        return self


class CreateProblem(SubmissionModel):
    title: str = Field(default="", max_length=160)
    statement: Text
    max_score: Points = Field(gt=0)
    correction_mode: Literal[CorrectionMode.DYNAMIC]  # Explicit opt-in, never inferred.
    assessment_id: Optional[str] = Field(default=None, pattern=r"^asmt_[0-9a-f]{32}$")


class ExpectedRevision(SubmissionModel):
    expected_revision: int = Field(ge=1)


class CreateStatement(ExpectedRevision):
    title: str = Field(default="", max_length=160)
    statement: Text
    max_score: Points = Field(gt=0)


class SaveRubric(ExpectedRevision, RubricContent):
    statement_version: int = Field(ge=1)
    replace_with_teacher: bool = False


class PreparationRequest(ExpectedRevision):
    reason: Optional[str] = Field(default=None, max_length=1000)


class SuggestionRequest(PreparationRequest):
    preparation_id: str = Field(pattern=r'^dprep_[0-9a-f]{32}$')


class ApproveRubric(ExpectedRevision):
    acknowledge_warnings: bool = False


class SuggestedRubric(RubricContent):
    warnings: tuple[Warning, ...]


RubricVersion.model_rebuild()
