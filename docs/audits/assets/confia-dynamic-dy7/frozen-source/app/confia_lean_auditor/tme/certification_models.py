"""Additive D7 contracts: explicit research labels, never operational truth."""
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from pydantic import Field, model_validator
from confia_lean_auditor.submissions.schemas import SubmissionModel, Sha256
from confia_lean_auditor.teacher_decisions.models import Points


class GoldBinding(SubmissionModel):
    question_attempt_id: str = Field(pattern=r'^case_[0-9a-f]{32}$')
    transcription_version_id: str = Field(pattern=r'^tr_[0-9a-f]{32}:[1-9][0-9]*$')
    statement_version: int = Field(ge=1)
    statement_sha256: Sha256
    rubric_id: str
    rubric_version: int = Field(ge=1)
    rubric_sha256: Sha256


class RaterScore(SubmissionModel):
    rater_id: str = Field(min_length=1,max_length=80,pattern=r'^[A-Za-z0-9_.:-]+$')
    score: Points
    criterion_points: dict[str, Points] = Field(default_factory=dict)
    blind: bool
    independent: bool
    evaluated_at: datetime


class GoldEvaluation(SubmissionModel):
    evaluator_id: str = Field(min_length=1,max_length=80,pattern=r'^[A-Za-z0-9_.:-]+$')
    evaluated_at: datetime
    blind: bool
    blindness_note: str = Field(min_length=1,max_length=500)
    reference_kind: Literal['HUMAN','SYNTHETIC_FIXTURE']
    adjudication_status: Literal['SINGLE_RATER','ADJUDICATED','UNRESOLVED']
    ratings: list[RaterScore] = Field(default_factory=list,max_length=20)
    adjudication_reason: Optional[str] = Field(default=None,max_length=1000)
    requires_review: Optional[bool] = None
    review_reason: Optional[str] = Field(default=None,max_length=500)

    @model_validator(mode='after')
    def coherent(self):
        if len({r.rater_id for r in self.ratings})!=len(self.ratings):raise ValueError('duplicate rater')
        if self.adjudication_status=='ADJUDICATED' and (len(self.ratings)<2 or not self.adjudication_reason):
            raise ValueError('adjudication requires ratings and a reason')
        if self.requires_review is not None and not self.review_reason:raise ValueError('review label requires rationale')
        return self


class DatasetCase(SubmissionModel):
    question_attempt_id: str = Field(pattern=r'^case_[0-9a-f]{32}$')
    split: Literal['DEV','VALIDATION','HOLDOUT']
    group_id: str = Field(min_length=1,max_length=100,pattern=r'^[A-Za-z0-9_.:-]+$')
    source_kind: Literal['SYNTHETIC','CURATED','REAL_STUDENT']
    domain: str = Field(min_length=1,max_length=80)
    difficulty: str = Field(default='UNSPECIFIED',max_length=80)
    difficulty_basis: Literal['HUMAN','ESTIMATED','UNSPECIFIED'] = 'UNSPECIFIED'
    solution_type: str = Field(min_length=1,max_length=80)


class ExperimentalGates(SubmissionModel):
    label: str = Field(min_length=1,max_length=100)
    profile: Literal['FORMATIVE_LIST','SCHOOL_EXAM']
    split: Literal['VALIDATION','HOLDOUT'] = 'HOLDOUT'
    source_kind: Literal['SYNTHETIC','CURATED','REAL_STUDENT']
    min_n: int = Field(ge=1)
    max_mae: Optional[Points] = None
    max_false_credit_rate: Optional[Decimal] = Field(default=None,ge=0,le=1)
    min_review_precision: Optional[Decimal] = Field(default=None,ge=0,le=1)
    max_technical_failure_rate: Optional[Decimal] = Field(default=None,ge=0,le=1)
    max_automation_risk: Optional[Decimal] = Field(default=None,ge=0,le=1)


class FreezeDataset(SubmissionModel):
    dataset_version: str = Field(min_length=1,max_length=80,pattern=r'^[A-Za-z0-9_.:-]+$')
    gold_version: int = Field(ge=1)
    cases: list[DatasetCase] = Field(min_length=1,max_length=10000)
    protocol: str = Field(min_length=20,max_length=4000)
    protocol_sha256: Sha256
    material_error_points: Points = Decimal('1')
    gates: Optional[ExperimentalGates] = None

    @model_validator(mode='after')
    def unique(self):
        if len({c.question_attempt_id for c in self.cases})!=len(self.cases):raise ValueError('duplicate case')
        groups={}
        for c in self.cases:
            if c.group_id in groups and groups[c.group_id]!=c.split:raise ValueError('group crosses dataset splits')
            groups[c.group_id]=c.split
        return self


class CreateCertificationRun(SubmissionModel):
    dataset_id: str = Field(pattern=r'^dataset_[0-9a-f]{64}$')
    bootstrap_seed: int = Field(default=20261112,ge=0,le=2**32-1)
