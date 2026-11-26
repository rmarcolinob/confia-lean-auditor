"""Versioned classroom policy and actor binding; no grading rules."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class SchoolPolicy(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    schema_version: Literal['dynamic-classroom-policy.v1'] = 'dynamic-classroom-policy.v1'
    grade_year: int = Field(default=9, ge=6, le=12)
    max_attempts: int = Field(default=1, ge=1, le=10)
    allowed_inputs: list[Literal['TEXT','IMAGES','PDF']] = Field(default_factory=lambda:['TEXT','IMAGES','PDF'], min_length=1, max_length=3)
    feedback: Literal['WITHHOLD','GUIDANCE','TEACHER_RELEASE'] = 'TEACHER_RELEASE'
    reveal_complete_solution: Literal[False] = False
    official_grade: Literal['TEACHER_RELEASE'] = 'TEACHER_RELEASE'

    @model_validator(mode='after')
    def unique_inputs(self):
        if len(set(self.allowed_inputs)) != len(self.allowed_inputs):
            raise ValueError('duplicate input modes')
        return self

class SchoolAttemptBinding(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    schema_version: Literal['dynamic-school-attempt.v1'] = 'dynamic-school-attempt.v1'
    student_user_id: str = Field(min_length=1,max_length=80)
    teacher_user_id: str = Field(min_length=1,max_length=80)
    attempt_number: int = Field(ge=1,le=10)
    policy_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    evaluation_service: Literal['dynamic-school-audit.v1'] = 'dynamic-school-audit.v1'
