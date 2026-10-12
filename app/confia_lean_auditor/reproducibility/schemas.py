from __future__ import annotations

from datetime import datetime
from pathlib import PurePosixPath
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .canonical import canonical_bytes, sha256

SCHEMA_VERSION = "1.0"
MANIFEST_FILENAME = "reproducibility_manifest.json"
DEPENDENCIES_FILENAME = "python_dependencies.txt"
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Source = Literal["environment", "git", "package", "project", "command", "lake-manifest", "unavailable"]


class MetadataModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class IdentifiedValue(MetadataModel):
    value: Optional[str] = None
    metadata_source: Source = "unavailable"
    reason: Optional[Literal["not_available", "invalid_value", "not_versioned", "command_failed"]] = "not_available"

    @model_validator(mode="after")
    def coherent(self):
        if self.value is not None and not self.value.strip():
            raise ValueError("identified value must not be blank")
        if (self.value is None) != (self.metadata_source == "unavailable"):
            raise ValueError("inconsistent metadata source")
        if (self.value is None) != (self.reason is not None):
            raise ValueError("inconsistent availability reason")
        return self


class CodeIdentity(MetadataModel):
    git_commit: IdentifiedValue
    worktree_dirty: Optional[bool]
    worktree_dirty_source: Source
    build_id: IdentifiedValue
    dirty_fingerprint_sha256: Optional[Digest] = None


class ApplicationIdentity(MetadataModel):
    project_version: IdentifiedValue
    api_version: str
    audit_bridge_version: IdentifiedValue
    conversion_version: str
    capture_schema_version: str
    reproducibility_schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION


class AssetFingerprint(MetadataModel):
    logical_name: str
    relative_path: str
    sha256: Optional[Digest] = None
    size_bytes: Optional[int] = Field(default=None, ge=0)
    required: bool
    status: Literal["available", "unavailable"]
    reason: Optional[Literal["missing_or_unreadable", "unsafe_path"]] = None

    @field_validator("relative_path")
    @classmethod
    def controlled_path(cls, value):
        path = PurePosixPath(value)
        if (not value or path.is_absolute() or ".." in path.parts or "\\" in value
                or ":" in value or str(path) != value):
            raise ValueError("asset path must be controlled and relative")
        return value

    @model_validator(mode="after")
    def coherent(self):
        if self.status == "available":
            if self.sha256 is None or self.size_bytes is None or self.reason is not None:
                raise ValueError("available asset requires a fingerprint")
        elif self.sha256 is not None or self.size_bytes is not None or self.reason is None:
            raise ValueError("unavailable asset cannot claim a fingerprint")
        return self


class PythonEnvironment(MetadataModel):
    version: str
    implementation: str
    major: int
    minor: int
    micro: int
    operating_system: str
    release: str
    machine: str
    dependency_manifest_filename: Literal[DEPENDENCIES_FILENAME] = DEPENDENCIES_FILENAME
    dependency_manifest_sha256: Digest
    dependency_manifest_size_bytes: int = Field(ge=0)
    dependency_count: int = Field(ge=0)


class LeanDependency(MetadataModel):
    name: str
    revision: IdentifiedValue


class FormalEnvironment(MetadataModel):
    lean_version: IdentifiedValue
    lake_version: IdentifiedValue
    toolchain: IdentifiedValue
    mathlib_revision: IdentifiedValue
    dependencies: list[LeanDependency]


class ExecutionConfiguration(MetadataModel):
    llm_formal_steps_enabled: bool
    llm_model: IdentifiedValue


class AuditReproducibilityManifest(MetadataModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    manifest_id: Annotated[str, Field(pattern=r"^rep_[0-9a-f]{32}$")]
    generated_at: datetime
    problem_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]+$")]
    code_identity: CodeIdentity
    application_identity: ApplicationIdentity
    problem_assets: list[AssetFingerprint]
    configuration_assets: list[AssetFingerprint]
    execution_configuration: ExecutionConfiguration
    python_environment: PythonEnvironment
    formal_environment: FormalEnvironment
    limitations: list[str]

    @field_validator("generated_at")
    @classmethod
    def aware_timestamp(cls, value):
        if value.tzinfo is None:
            raise ValueError("timestamp requires a timezone")
        return value


class ReproducibilityManifestRecord(MetadataModel):
    manifest: AuditReproducibilityManifest
    manifest_sha256: Digest
    filename: Literal[MANIFEST_FILENAME] = MANIFEST_FILENAME
    size_bytes: int = Field(ge=0)

    @model_validator(mode="after")
    def valid_digest(self):
        raw = canonical_bytes(self.manifest)
        if self.manifest_sha256 != sha256(raw) or self.size_bytes != len(raw):
            raise ValueError("reproducibility integrity mismatch")
        return self


class ReproducibilityMetadata(MetadataModel):
    status: Literal["recorded", "unavailable", "legacy_unversioned"]
    record: Optional[ReproducibilityManifestRecord] = None
    error_code: Optional[Literal["METADATA_COLLECTION_FAILED", "METADATA_PUBLICATION_FAILED",
                                 "METADATA_INTEGRITY_FAILED", "AUDIT_NOT_COMPLETED"]] = None

    @model_validator(mode="after")
    def coherent(self):
        if self.status == "recorded":
            if self.record is None or self.error_code is not None:
                raise ValueError("recorded metadata requires a record")
        elif self.record is not None or ((self.status == "unavailable") != (self.error_code is not None)):
            raise ValueError("inconsistent metadata status")
        return self
