"""Methodology configuration, independent of historical engine implementation IDs.

Existing assessments have no such configuration and remain Specialized. This
contract does not change dispatch, persisted assessment shapes or TME_CURRENT.
"""
from enum import Enum
from typing import Optional
from pydantic import model_validator
from confia_lean_auditor.submissions.schemas import SubmissionModel, Sha256


class CorrectionMode(str, Enum):
    SPECIALIZED = "SPECIALIZED"
    DYNAMIC = "DYNAMIC"


class PackageReference(SubmissionModel):
    problem_id: str
    package_id: str
    package_version: int
    statement_version: int
    statement_sha256: Sha256
    rubric_id: str
    rubric_version: int
    rubric_sha256: Sha256
    package_sha256: Sha256

    @model_validator(mode="after")
    def versions(self):
        if min(self.package_version, self.statement_version, self.rubric_version) < 1:
            raise ValueError("explicit positive versions required")
        return self


class CorrectionConfiguration(SubmissionModel):
    mode: CorrectionMode = CorrectionMode.SPECIALIZED
    package: Optional[PackageReference] = None

    @model_validator(mode="after")
    def explicit_dynamic(self):
        if (self.mode == CorrectionMode.DYNAMIC) != (self.package is not None):
            raise ValueError("Dynamic requires an exact approved package reference")
        return self


class DynamicAuditProvenance(SubmissionModel):
    """Future AuditRun input, never a result or an executable engine in DY1."""
    configuration: CorrectionConfiguration
    engine_version: str

    @model_validator(mode="after")
    def dynamic_only(self):
        if self.configuration.mode != CorrectionMode.DYNAMIC or not self.engine_version.strip():
            raise ValueError("Dynamic provenance requires its engine version")
        return self


def configured_mode(configuration=None):
    return CorrectionConfiguration.model_validate({} if configuration is None else configuration).mode
