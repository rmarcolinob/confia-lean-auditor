"""Self-study contracts. Numeric engine judgments never belong to public reports."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import Field, model_validator
from confia_lean_auditor.submissions.schemas import SubmissionModel, TranscriptionSegment, Sha256
from confia_lean_auditor.tme.exam_models import OriginalUpload
from .models import RubricContent

class SourceInput(SubmissionModel):
    text: str = Field(default='',max_length=20000)
    original_documents: list[OriginalUpload] = Field(default_factory=list,max_length=20)
    @model_validator(mode='after')
    def one_input(self):
        if bool(self.text.strip()) == bool(self.original_documents):
            raise ValueError('Envie texto ou originais, separadamente.')
        if any(d.media_type=='application/pdf' for d in self.original_documents) and len(self.original_documents)!=1:
            raise ValueError('Envie um PDF ou fotografias.')
        return self

class CreateStudy(SubmissionModel):
    source: SourceInput
    grade_year: int = Field(default=9,ge=6,le=12)
    execution_key: str = Field(min_length=1,max_length=100)

class NewStudyAttempt(SubmissionModel):
    source: SourceInput
    package_id: str
    execution_key: str = Field(min_length=1,max_length=100)

class StudyReading(SubmissionModel):
    based_on_revision_number: int = Field(ge=0)
    segments: list[TranscriptionSegment] = Field(min_length=1,max_length=300)

class ReadingSelection(SubmissionModel):
    revision_number: int = Field(ge=1)
    revision_sha256: Sha256
    confirmed: Literal[True]

class PackageSelection(SubmissionModel):
    package_id: str
    package_sha256: Sha256
    confirmed: Literal[True]

class HelpRequest(SubmissionModel):
    level: int = Field(ge=2,le=4)
    request_complete_solution: bool = False

class StudyPage(SubmissionModel):
    index: int = Field(ge=0)
    page_id: str
    derived_width: int = Field(gt=0)
    derived_height: int = Field(gt=0)
    original_index: int = Field(ge=0)
    original_page: int = Field(ge=1)

class StudySourceSnapshot(SubmissionModel):
    schema_version: Literal['self-study-source.v1'] = 'self-study-source.v1'
    context: Literal['SELF_STUDY'] = 'SELF_STUDY'
    snapshot_id: str
    problem_id: str
    study_id: str
    author_id: str
    purpose: Literal['STATEMENT','SOLUTION']
    original_text: str = Field(default='',max_length=20000)
    pages: list[StudyPage] = Field(default_factory=list,max_length=50)

class StudyStatement(SubmissionModel):
    context: Literal['SELF_STUDY'] = 'SELF_STUDY'
    problem_id: str
    version_number: int
    statement: str
    max_score: int = 3  # Only an internal normalization for the shared grader.

class StudyRubric(RubricContent):
    context: Literal['SELF_STUDY'] = 'SELF_STUDY'
    status: Literal['PROVISIONAL_FORMATIVE'] = 'PROVISIONAL_FORMATIVE'
    rubric_id: str
    version_number: int
    provenance: dict

class LearningFinding(SubmissionModel):
    criterion_id: str
    objective: str
    state: Literal['SUPPORTED','PARTIAL','MATHEMATICAL_ERROR','NEEDS_EXPLANATION','UNCERTAIN','TECHNICAL_ERROR']
    verification: Literal['EXACT_WITHIN_SCOPE','SEMANTIC_NOT_FORMAL','UNDETERMINED']
    evidence: list[dict]
    guidance: str
    mathematical_finding: Literal["VALID_ARGUMENT", "MATHEMATICAL_ERROR", "INCOMPLETE", "INSUFFICIENT_EVIDENCE", "UNCERTAIN"] = "UNCERTAIN"

class LearningReport(SubmissionModel):
    schema_version: Literal['self-study-report.v1'] = 'self-study-report.v1'
    context: Literal['SELF_STUDY'] = 'SELF_STUDY'
    status: Literal['FEEDBACK_AVAILABLE','REVIEW_PENDING','TECHNICAL_ERROR']
    rubric_status: Literal['PROVISIONAL_FORMATIVE'] = 'PROVISIONAL_FORMATIVE'
    findings: list[LearningFinding]
    uncertainties: list[str]
    comparison: list[dict]
    formal_verification_performed: Literal[False] = False
    policy_version: Literal['self-study-feedback.v1','self-study-feedback.v2'] = 'self-study-feedback.v2'

class HelpItem(SubmissionModel):
    criterion_id: str
    message: str = Field(min_length=1,max_length=3000)
    quotes: list[str] = Field(max_length=10)

class HelpProposal(SubmissionModel):
    items: list[HelpItem] = Field(min_length=1,max_length=20)
    limitations: list[str] = Field(max_length=10)


# Selection/rendering contract, not another mathematical evaluator. Historical
# HelpProposal stays readable, but free prose is never a public v2 instruction.
GuidanceTopic = Literal['EQUALITY','FACTORIZATION','PROPORTION','FUNCTION','GEOMETRY','CHECK_CONDITIONS','EXPLAIN_STEP']
StepRule = Literal['EQUALITY','FACTORIZATION','PROPORTION','FUNCTION','GEOMETRY','CHECK_CONDITIONS','EXPLAIN_STEP','SIMPLIFY','SUBSTITUTE','CONCLUDE']

class GuidedStep(SubmissionModel):
    rule: StepRule
    expression: str = Field(min_length=1,max_length=300)

class ControlledHelpItem(SubmissionModel):
    criterion_id: str
    topic: GuidanceTopic
    quotes: list[str] = Field(min_length=1,max_length=10)
    steps: list[GuidedStep] = Field(default_factory=list,max_length=12)

class ControlledHelpProposal(SubmissionModel):
    schema_version: Literal['self-study-help.v2'] = 'self-study-help.v2'
    items: list[ControlledHelpItem] = Field(min_length=1,max_length=8)
