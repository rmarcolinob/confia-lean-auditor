"""Immutable publication and historical verification, without recollection."""
from pathlib import Path

from confia_lean_auditor.submissions.store import SubmissionStore
from .canonical import canonical_bytes, sha256
from .schemas import (
    AuditReproducibilityManifest, DEPENDENCIES_FILENAME, MANIFEST_FILENAME,
    ReproducibilityManifestRecord, ReproducibilityMetadata,
)


class ReproducibilityIntegrityError(ValueError):
    pass


def atomic_write(path, data):
    # Reuse existing fsync + hard-link publication, with no replacement.
    SubmissionStore._write_atomic_new(path, data)


def publish(snapshot, artifact_dir):
    if snapshot is None:
        return ReproducibilityMetadata(status="unavailable", error_code="METADATA_COLLECTION_FAILED")
    try:
        artifact_dir = Path(artifact_dir)
        if not artifact_dir.is_absolute() or any(p.is_symlink() for p in [artifact_dir, *artifact_dir.parents]):
            raise ValueError("unsafe metadata directory")
        raw = canonical_bytes(snapshot.manifest)
        record = ReproducibilityManifestRecord(manifest=snapshot.manifest,
            manifest_sha256=sha256(raw), size_bytes=len(raw))
        atomic_write(artifact_dir / DEPENDENCIES_FILENAME, snapshot.dependencies)
        atomic_write(artifact_dir / MANIFEST_FILENAME, raw)
        result = ReproducibilityMetadata(status="recorded", record=record)
        verify(result, artifact_dir)
        return result
    except Exception:
        return ReproducibilityMetadata(status="unavailable", error_code="METADATA_PUBLICATION_FAILED")


def _read_controlled(root, filename):
    root = Path(root)
    path = root / filename
    if not root.is_absolute() or any(p.is_symlink() for p in [path, *path.parents]):
        raise ReproducibilityIntegrityError("reproducibility integrity mismatch")
    return path.read_bytes()


def verify(metadata, artifact_dir):
    if metadata is None or metadata.status != "recorded":
        return metadata or ReproducibilityMetadata(status="legacy_unversioned")
    try:
        record = metadata.record
        raw = _read_controlled(artifact_dir, record.filename)
        manifest = AuditReproducibilityManifest.model_validate_json(raw)
        if (len(raw) != record.size_bytes or sha256(canonical_bytes(manifest)) != record.manifest_sha256
                or manifest != record.manifest):
            raise ValueError("manifest mismatch")
        python = manifest.python_environment
        dependencies = _read_controlled(artifact_dir, python.dependency_manifest_filename)
        if (sha256(dependencies) != python.dependency_manifest_sha256
                or len(dependencies) != python.dependency_manifest_size_bytes
                or len(dependencies.splitlines()) != python.dependency_count):
            raise ValueError("dependencies mismatch")
        return metadata
    except (OSError, ValueError, TypeError):
        raise ReproducibilityIntegrityError("reproducibility integrity mismatch") from None
