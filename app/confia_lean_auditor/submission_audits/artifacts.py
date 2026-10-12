"""One mandatory-artifact inventory, captured once and checked on every read."""
import hashlib
from pathlib import Path

from .schemas import RequiredArtifact
from confia_lean_auditor.reproducibility.service import verify


def required_references(result):
    root = Path(result.artifact_dir or "")
    if not result.artifact_dir or not root.is_absolute() or not root.is_dir():
        raise ValueError("invalid audit artifact directory")
    references = [("export", name, str(root / name)) for name in (
        "audit.json", "solution.txt", "claims.json", "student_claims.json", "student_claim_checks.json")]
    metadata = verify(result.reproducibility, root)
    if metadata.status == "recorded":
        record = metadata.record
        for name in (record.filename, record.manifest.python_environment.dependency_manifest_filename):
            references.append(("reproducibility", name, str(root / name)))
    references.append(("certificate", "principal", result.lean_certificate.lean_file))
    for step in result.formal_steps:
        if step.status == "verified":
            if not step.compiled or step.exit_code != 0:
                raise ValueError("inconsistent formal step verification")
            references.append(("formal_step", step.id, step.lean_file))
    for check in result.student_claim_checks:
        if check.get("status") == "verified":
            if check.get("compiled") is not True:
                raise ValueError("inconsistent student verification")
            references.append(("student_proof", check["id"], check.get("lean_file")))
        elif check.get("status") == "refuted":
            if check.get("refutation_verified") is not True:
                raise ValueError("missing refutation evidence")
            references.append(("refutation", check["id"], check.get("refutation_lean_file")))
    return root, references


def controlled_file(root, value):
    if not value:
        raise ValueError("missing required artifact")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts or ".." in root.parts:
        raise ValueError("invalid artifact path")
    path.relative_to(root)
    # Reject links in the file and every ancestor, including the run directory.
    if any(parent.is_symlink() for parent in [path, *path.parents]):
        raise ValueError("symbolic artifact path")
    if not path.is_file():
        raise ValueError("missing required artifact")
    return path


def capture_manifest(result):
    root, references = required_references(result)
    manifest = []
    for kind, relation, value in references:
        path = controlled_file(root, value)
        data = path.read_bytes()
        manifest.append(RequiredArtifact(artifact_type=kind, relation_id=relation,
            file=str(path), sha256=hashlib.sha256(data).hexdigest(), byte_size=len(data)))
    return manifest


def validate_manifest(result, manifest):
    root, references = required_references(result)
    expected = set(references)
    actual = {(item.artifact_type, item.relation_id, item.file) for item in manifest}
    if expected != actual or len(actual) != len(manifest):
        raise ValueError("incomplete required artifact manifest")
    for item in manifest:
        data = controlled_file(root, item.file).read_bytes()
        if len(data) != item.byte_size or hashlib.sha256(data).hexdigest() != item.sha256:
            raise ValueError("changed required artifact")
