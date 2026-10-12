"""GOV-01 evidence, privacy, immutable history and shared-engine contracts."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

import confia_lean_auditor.main as main
from confia_lean_auditor.reproducibility import collector, service
from confia_lean_auditor.reproducibility.canonical import canonical_bytes, sha256
from confia_lean_auditor.reproducibility.schemas import (
    AssetFingerprint, AuditReproducibilityManifest, DEPENDENCIES_FILENAME,
    MANIFEST_FILENAME, ReproducibilityManifestRecord,
)
from confia_lean_auditor.submission_audits import router as audits
from confia_lean_auditor.submissions.integrity import model_sha256
from test_submission_audits import persisted_run, setup, source, accept, execute, result
from test_submissions import payload

ROOT = Path(__file__).resolve().parents[1]
PROBLEM = "ITA2025Q1"
COMMIT = "a" * 40
ENV = {"CONFIA_BUILD_COMMIT": COMMIT, "CONFIA_BUILD_DIRTY": "false", "CONFIA_BUILD_ID": "pilot-01"}


def dist(name, version):
    return SimpleNamespace(metadata={"Name": name}, version=version)


@pytest.fixture
def project(tmp_path):
    for relative in (f"problems/{PROBLEM}", f"ConfiaLeanAuditor/Problems/{PROBLEM}"):
        shutil.copytree(ROOT / relative, tmp_path / relative)
    for name in ("pyproject.toml", "lean-toolchain", "lakefile.toml", "lake-manifest.json"):
        shutil.copyfile(ROOT / name, tmp_path / name)
    return tmp_path


@pytest.fixture
def snapshot(project, monkeypatch):
    monkeypatch.setattr(collector, "installed_formal_version", lambda root, toolchain, tool, env:
                        collector.identified("4.28.0" if tool == "lean" else "5.0.0", "command"))
    return collector.collect(project, PROBLEM, environ=ENV, distributions=[dist("Test_package", "1.2.3")])


def test_schema_valid_extra_forbidden_and_hash(snapshot):
    manifest = snapshot.manifest
    raw = canonical_bytes(manifest)
    assert AuditReproducibilityManifest.model_validate_json(raw) == manifest
    record = ReproducibilityManifestRecord(manifest=manifest, manifest_sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
    assert record.manifest_sha256 == sha256(raw)
    assert "manifest_sha256" not in json.loads(raw)
    for path in ((), ("code_identity",), ("python_environment",), ("application_identity",)):
        data = manifest.model_dump(mode="json")
        target = data
        for key in path:
            target = target[key]
        target["unexpected"] = "forbidden"
        with pytest.raises(ValidationError):
            AuditReproducibilityManifest.model_validate(data)
    with pytest.raises(ValidationError):
        ReproducibilityManifestRecord(manifest=manifest, manifest_sha256="0" * 64, size_bytes=len(raw))


def test_canonical_json_and_explicit_utc_datetime():
    utc = datetime(2026, 10, 12, 12, tzinfo=timezone.utc)
    local = utc.astimezone(timezone(timedelta(hours=-3)))
    assert canonical_bytes({"b": "ação", "a": utc}) == canonical_bytes({"a": local, "b": "ação"})
    assert b'2026-10-12T12:00:00.000000Z' in canonical_bytes(utc)
    with pytest.raises(ValueError):
        canonical_bytes(datetime(2026, 10, 12))
    with pytest.raises(ValueError):
        canonical_bytes(float("nan"))


@pytest.mark.parametrize("dirty,expected", [("true", True), ("false", False), ("1", True), ("0", False)])
def test_environment_code_identity(project, monkeypatch, dirty, expected):
    monkeypatch.setattr(collector, "command_output", lambda *args: pytest.fail("build evidence should not call Git"))
    identity = collector.collect_code(project, {**ENV, "CONFIA_BUILD_DIRTY": dirty})
    assert identity.git_commit.value == COMMIT and identity.git_commit.metadata_source == "environment"
    assert identity.worktree_dirty is expected and identity.worktree_dirty_source == "environment"
    assert identity.build_id.value == "pilot-01" and identity.build_id.metadata_source == "environment"


@pytest.mark.parametrize("key,bad", [("CONFIA_BUILD_COMMIT", "short"), ("CONFIA_BUILD_DIRTY", "yes"),
    ("CONFIA_BUILD_ID", "/Users/private/token"), ("CONFIA_BUILD_ID", "secret\nAuthorization: token")])
def test_invalid_build_values_never_leak(project, key, bad):
    identity = collector.collect_code(project, {**ENV, key: bad})
    assert bad not in identity.model_dump_json()
    if key == "CONFIA_BUILD_DIRTY":
        assert identity.worktree_dirty is None


@pytest.mark.parametrize("dirty", [False, True])
def test_git_fallback_clean_dirty(project, monkeypatch, dirty):
    (project / ".git").mkdir()
    calls = []
    def output(command, root):
        assert root == project
        calls.append(command)
        return COMMIT if command[1] == "rev-parse" else " M app/example.py" if dirty else ""
    monkeypatch.setattr(collector, "command_output", output)
    identity = collector.collect_code(project, {})
    assert identity.git_commit.value == COMMIT
    assert identity.git_commit.metadata_source == "git"
    assert identity.worktree_dirty is dirty
    assert len(calls) == 2


def test_git_unavailable_no_parent_repo_or_diagnostic(project, monkeypatch):
    assert collector.collect_code(project, {}).git_commit.value is None
    (project / ".git").mkdir()
    monkeypatch.setattr(collector, "command_output", lambda *args: None)
    code = collector.collect_code(project, {})
    assert code.git_commit.metadata_source == "unavailable" and code.worktree_dirty is None


def test_application_versions_from_existing_sources(snapshot):
    from confia_lean_auditor.submission_audits.schemas import AuditProvenance
    from confia_lean_auditor.capture.schemas import SCHEMA_VERSION
    app = snapshot.manifest.application_identity
    assert app.project_version.value == "0.1.0" and app.project_version.metadata_source == "project"
    assert app.api_version == main.app.version == TestClient(main.app).get("/health").json()["version"]
    assert app.audit_bridge_version.value is None and app.audit_bridge_version.reason == "not_versioned"
    assert app.conversion_version == AuditProvenance.model_fields["conversion_version"].default
    assert app.capture_schema_version == SCHEMA_VERSION


def test_asset_hash_size_required_and_controlled(snapshot, project):
    for asset in snapshot.manifest.problem_assets + snapshot.manifest.configuration_assets:
        data = (project / asset.relative_path).read_bytes()
        assert asset.sha256 == sha256(data) and asset.size_bytes == len(data)
        assert asset.required and asset.status == "available"
        assert not Path(asset.relative_path).is_absolute()
    assert {asset.logical_name for asset in snapshot.manifest.problem_assets} == {
        "problem.json", "rubric.json", "microclaims.json", "formal_statement"}
    (project / "problems" / PROBLEM / "rubric.json").unlink()
    missing = collector.asset(project, f"problems/{PROBLEM}/rubric.json", "rubric.json")
    assert missing.required and missing.status == "unavailable" and missing.sha256 is None


@pytest.mark.parametrize("path", ["/etc/passwd", "../private", "a/../b", "a\\b", "C:/private", "./file"])
def test_unsafe_relative_paths_rejected(path):
    with pytest.raises(ValidationError):
        AssetFingerprint(logical_name="test", relative_path=path, required=True,
                         status="unavailable", reason="unsafe_path")


def test_symlink_asset_not_fingerprinted(project, tmp_path):
    (project / "linked").symlink_to(project / "pyproject.toml")
    asset = collector.asset(project, "linked", "linked")
    assert asset.status == "unavailable" and asset.reason == "unsafe_path"


def test_dependencies_deterministic_hash_and_changes(snapshot):
    dependencies = [dist("Z_Pkg", "1.0"), dist("a.pkg", "2.0"), dist("Z-Pkg", "1.0")]
    raw, count = collector.dependency_manifest(dependencies)
    assert raw == b"a-pkg==2.0\nz-pkg==1.0\n" and count == 2
    assert (raw, count) == collector.dependency_manifest(reversed(dependencies))
    assert sha256(raw) != sha256(collector.dependency_manifest([dist("a.pkg", "2.1")])[0])
    python = snapshot.manifest.python_environment
    assert python.dependency_manifest_sha256 == sha256(snapshot.dependencies)
    assert python.dependency_manifest_size_bytes == len(snapshot.dependencies)
    assert python.dependency_count == 1


def test_python_platform_without_personal_identifiers(snapshot):
    import platform
    import sys
    python = snapshot.manifest.python_environment
    assert python.version == sys.version and python.implementation == platform.python_implementation()
    assert (python.major, python.minor, python.micro) == sys.version_info[:3]
    assert python.operating_system == platform.system()
    assert python.release == platform.release() and python.machine == platform.machine()
    assert not {"hostname", "username", "home", "sys_path", "environment"} & python.model_dump().keys()


def test_formal_sources_and_versions(snapshot, project):
    formal = snapshot.manifest.formal_environment
    assert formal.lean_version.value == "4.28.0" and formal.lake_version.value == "5.0.0"
    manifest = json.loads((project / "lake-manifest.json").read_bytes())
    assert formal.mathlib_revision.value == next(p["rev"] for p in manifest["packages"] if p["name"] == "mathlib")
    assert formal.mathlib_revision.metadata_source == "lake-manifest"
    assert formal.toolchain.value == (project / "lean-toolchain").read_text().strip()
    assert {a.logical_name for a in snapshot.manifest.configuration_assets} >= {"lean-toolchain", "lake-manifest.json"}


@pytest.mark.parametrize("tool,output,expected", [("lean", "Lean (version 4.28.0, commit abc, Release)", "4.28.0"),
    ("lake", "Lake version 5.0.0-src+abcdef (Lean version 4.28.0)", "5.0.0-src+abcdef"),
    ("lean", "failure /Users/private/secret", None)])
def test_formal_commands_use_installed_binaries_only(project, monkeypatch, tool, output, expected):
    elan = project / "installed-elan"
    binary = elan / "toolchains/leanprover--lean4---v4.28.0/bin" / tool
    binary.parent.mkdir(parents=True)
    binary.write_text("test")
    monkeypatch.setattr(collector.shutil, "which", lambda *a, **k: str(elan / "bin" / tool))
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        assert kwargs["timeout"] == 3 and kwargs["cwd"] == project
        assert command == [str(binary), "--version"]
        return SimpleNamespace(returncode=0, stdout=output)
    monkeypatch.setattr(collector.subprocess, "run", run)
    identity = collector.installed_formal_version(project,
        collector.identified("leanprover/lean4:v4.28.0", "project"), tool, {"ELAN_HOME": str(elan)})
    assert identity.value == expected and len(calls) == 1
    assert "/Users/" not in identity.model_dump_json()


def test_missing_formal_toolchain_never_installs(project, monkeypatch):
    monkeypatch.setattr(collector.subprocess, "run", lambda *a, **k: pytest.fail("no elan shim allowed"))
    value = collector.installed_formal_version(project,
        collector.identified("leanprover/lean4:v4.28.0", "project"), "lean", {"ELAN_HOME": str(project / "absent")})
    assert value.value is None


def test_no_cache_mix_history_or_frozen_dirty(project, snapshot, monkeypatch):
    def collect(root, env=ENV):
        return collector.collect(root, PROBLEM, environ=env, distributions=[]).manifest
    first, second = collect(project), collect(project)
    variable = {"manifest_id", "generated_at"}
    assert first.model_dump(exclude=variable) == second.model_dump(exclude=variable)
    assert first.manifest_id != second.manifest_id
    original = canonical_bytes(first)
    asset = project / "problems" / PROBLEM / "rubric.json"
    asset.write_text(asset.read_text() + "\n")
    third = collect(project)
    assert first.problem_assets[1].sha256 != third.problem_assets[1].sha256
    other = project / "other-root"
    other.mkdir()
    assert collect(other).problem_assets[0].status == "unavailable"
    assert collect(project, {**ENV, "CONFIA_BUILD_COMMIT": "b" * 40}).code_identity != first.code_identity
    dirty = collect(project, {**ENV, "CONFIA_BUILD_DIRTY": "true"})
    assert dirty.code_identity.worktree_dirty and any("dirty" in item for item in dirty.limitations)
    assert canonical_bytes(first) == original


@pytest.mark.parametrize("filename", [MANIFEST_FILENAME, DEPENDENCIES_FILENAME])
@pytest.mark.parametrize("change", ["modify", "remove", "symlink"])
def test_historical_integrity(snapshot, project, filename, change):
    destination = project / "artifacts"
    record = service.publish(snapshot, destination)
    assert record.status == "recorded"
    assert service.verify(record, destination) == record
    target = destination / filename
    if change == "modify":
        if filename == MANIFEST_FILENAME:
            data = json.loads(target.read_bytes())
            data["code_identity"]["build_id"]["value"] = "changed-build"
            target.write_text(json.dumps(data))
        else:
            target.write_bytes(b"altered==1.0\n")
    else:
        target.unlink()
        if change == "symlink":
            target.symlink_to(project / "pyproject.toml")
    with pytest.raises(service.ReproducibilityIntegrityError):
        service.verify(record, destination)


def test_atomic_no_replacement_and_publication_failure(snapshot, project, monkeypatch):
    destination = project / "artifacts"
    destination.mkdir()
    target = destination / MANIFEST_FILENAME
    target.write_bytes(b"existing")
    failure = service.publish(snapshot, destination)
    assert failure.status == "unavailable" and failure.error_code == "METADATA_PUBLICATION_FAILED"
    assert target.read_bytes() == b"existing"
    assert not list(destination.glob("*.pending"))


@pytest.fixture
def pipeline(project, monkeypatch):
    monkeypatch.setattr(main, "repo_root", lambda: project)
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(project / "submissions"))
    monkeypatch.setenv("CONFIA_SUBMISSION_AUDITS_DIR", str(project / "audits"))
    monkeypatch.setenv("CONFIA_ENABLE_LLM_FORMAL_STEPS", "0")
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(collector, "installed_formal_version", lambda *args: collector.identified("4.28.0", "command"))
    # Keep the actual extractor, builder, rubric and report. Only the compiler
    # and student proof service are controlled; no Lean builds/dependency fetch.
    monkeypatch.setattr(main, "check_student_claims_for_problem", lambda **kwargs: [])
    monkeypatch.setattr(main, "run_lean_file", lambda *args: dict(status="lean_timeout", compiled=False,
        exit_code=124, uses_forbidden_token=False, forbidden_tokens_found=[], stdout="", stderr=""))
    return TestClient(main.app)


def pair(client):
    body = payload()
    snapshot = json.loads(body["snapshot_json"])
    snapshot["problem_id"] = PROBLEM
    body["snapshot_json"] = json.dumps(snapshot)
    sid, revision = source(client, request_payload=body)
    request = accept(client, sid, revision)
    run = execute(client, sid, request).json()
    return sid, request, run


def test_shared_engine_snapshot_once_and_no_mathematical_change(pipeline, monkeypatch, project):
    calls = []
    original = main.capture_reproducibility
    def capture(root, problem):
        calls.append(problem)
        return original(root, problem)
    monkeypatch.setattr(main, "capture_reproducibility", capture)
    request = dict(problem_id=PROBLEM, solution="x=1")
    response = pipeline.post("/audit", json=request)
    assert response.status_code == 200
    data = response.json()
    assert data["reproducibility"]["status"] == "recorded" and calls == [PROBLEM]
    from confia_lean_auditor.core.public_audit import public_projection
    internal = json.loads(next((project / "artifacts/runs").glob("*/audit.json")).read_bytes())
    assert public_projection(internal, internal["artifact_dir"]) == data
    monkeypatch.setattr(main, "capture_reproducibility", lambda *args: None)
    baseline = pipeline.post("/audit", json=request).json()
    from test_cap04_global_semantics import central
    assert central({k: v for k, v in data.items() if k != "reproducibility"}) == central(
        {k: v for k, v in baseline.items() if k != "reproducibility"})
    assert baseline["reproducibility"]["status"] == "unavailable"


def test_bridge_endpoint_binding_and_immutable_history(pipeline, project):
    sid, request, run = pair(pipeline)
    assert run["status"] == "COMPLETED" and run["reproducibility_status"] == "recorded"
    record = run["result"]["reproducibility"]["record"]
    assert run["reproducibility_manifest_sha256"] == record["manifest_sha256"]
    assert run["reproducibility_manifest_filename"] == MANIFEST_FILENAME
    assert len([a for a in run["required_artifacts"] if a["artifact_type"] == "reproducibility"]) == 2
    endpoint = f'/submission-audits/{run["audit_run_id"]}/reproducibility'
    first = pipeline.get(endpoint)
    assert first.status_code == 200 and first.json() == run["result"]["reproducibility"]
    assert first.headers["Cache-Control"] == "no-store"
    assert str(project) not in first.text and "/Users/" not in first.text
    (project / "problems" / PROBLEM / "rubric.json").write_text("changed after the run")
    assert pipeline.get(endpoint).json() == first.json()
    assert execute(pipeline, sid, request).json() == run
    assert pipeline.get("/submission-audits/not-an-id/reproducibility").status_code == 404


@pytest.mark.parametrize("filename", [MANIFEST_FILENAME, DEPENDENCIES_FILENAME])
def test_bridge_tamper_blocks_get_list_endpoint_and_retry(pipeline, filename):
    sid, request, run = pair(pipeline)
    Path(persisted_run(run)["artifact_dir"], filename).write_bytes(b"tampered")
    for url in (f'/submission-audits/{run["audit_run_id"]}', f'/submissions/{sid}/audits',
                f'/submission-audits/{run["audit_run_id"]}/reproducibility'):
        assert pipeline.get(url).status_code == 409
    assert execute(pipeline, sid, request).status_code == 409


def test_actual_legacy_serialization_without_retrohash(setup):
    client, _ = setup
    sid, request, run = pair(client)
    path = audits.service()._path(run["audit_run_id"])
    stored = json.loads(path.read_bytes())
    assert "reproducibility" not in stored["result"]
    # Produce the exact pre-GOV-01 run shape, keeping its historical digests.
    for key in list(stored):
        if key.startswith("reproducibility_"):
            del stored[key]
    path.write_text(json.dumps(stored))
    before = path.read_bytes()
    loaded = client.get(f'/submission-audits/{run["audit_run_id"]}').json()
    assert loaded["reproducibility_status"] == "legacy_unversioned"
    assert loaded["result_sha256"] == stored["result_sha256"]
    assert client.get(f'/submission-audits/{run["audit_run_id"]}/reproducibility').json()["status"] == "legacy_unversioned"
    assert client.get(f'/submissions/{sid}/audits').status_code == 200
    assert execute(client, sid, request).json()["reproducibility_status"] == "legacy_unversioned"
    assert path.read_bytes() == before
    assert not Path(persisted_run(run)["artifact_dir"], MANIFEST_FILENAME).exists()


def test_collection_and_publication_failures_preserve_math(pipeline, monkeypatch):
    def broken(*args, **kwargs):
        raise OSError("secret diagnostics /Users/private/token")
    monkeypatch.setattr(collector, "collect", broken)
    sid, request, run = pair(pipeline)
    assert run["status"] == "COMPLETED" and run["reproducibility_status"] == "unavailable"
    assert run["result"]["reproducibility"]["error_code"] == "METADATA_COLLECTION_FAILED"
    assert "secret diagnostics" not in json.dumps(run)


def test_publication_failure_keeps_completed_result_without_false_record(pipeline, monkeypatch):
    original = service.atomic_write
    def fail_manifest(path, data):
        if path.name == MANIFEST_FILENAME:
            raise OSError("fake-private-token")
        return original(path, data)
    monkeypatch.setattr(service, "atomic_write", fail_manifest)
    sid, request, run = pair(pipeline)
    assert run["status"] == "COMPLETED" and run["result"] is not None
    assert run["reproducibility_status"] == "unavailable"
    assert run["reproducibility_manifest_sha256"] is None
    assert run["result"]["reproducibility"]["error_code"] == "METADATA_PUBLICATION_FAILED"
    assert pipeline.get(f'/submission-audits/{run["audit_run_id"]}').status_code == 200


@pytest.mark.parametrize("filename", [MANIFEST_FILENAME, DEPENDENCIES_FILENAME])
def test_tamper_before_bridge_publication_is_governance_failure(pipeline, monkeypatch, filename):
    engine = main.execute_audit
    def changed(request):
        response = engine(request)
        Path(response.artifact_dir, filename).unlink()
        return response
    monkeypatch.setattr(main, "execute_audit", changed)
    _, _, run = pair(pipeline)
    assert run["status"] == "FAILED" and run["error_code"] == "METADATA_INTEGRITY_FAILED"
    assert run["reproducibility_status"] == "unavailable"
    assert run["result"] is None
    metadata = pipeline.get(f'/submission-audits/{run["audit_run_id"]}/reproducibility').json()
    assert metadata["status"] == "unavailable" and metadata["error_code"] == "METADATA_INTEGRITY_FAILED"


def test_current_engine_failure_is_not_mislabelled_as_legacy(pipeline, monkeypatch):
    def failed(*args):
        raise RuntimeError("engine unavailable")
    monkeypatch.setattr(main, "execute_audit", failed)
    _, _, run = pair(pipeline)
    assert run["status"] == "FAILED" and run["reproducibility_status"] == "unavailable"
    metadata = pipeline.get(f'/submission-audits/{run["audit_run_id"]}/reproducibility').json()
    assert metadata["error_code"] == "AUDIT_NOT_COMPLETED"


def test_collection_before_pipeline_and_once_per_run(pipeline, monkeypatch, project):
    calls = {"dependencies": 0, "versions": []}
    dependencies = collector.dependency_manifest
    def counted_dependencies(*args):
        calls["dependencies"] += 1
        return dependencies(*args)
    def version(root, toolchain, tool, env):
        calls["versions"].append(tool)
        return collector.identified("4.28.0", "command")
    monkeypatch.setattr(collector, "dependency_manifest", counted_dependencies)
    monkeypatch.setattr(collector, "installed_formal_version", version)
    extract = main.extract_claims
    path = project / "problems" / PROBLEM / "problem.json"
    original = sha256(path.read_bytes())
    def changed_during_pipeline(*args):
        assert calls == {"dependencies": 1, "versions": ["lean", "lake"]}
        path.write_text(path.read_text() + "\n")
        return extract(*args)
    monkeypatch.setattr(main, "extract_claims", changed_during_pipeline)
    response = pipeline.post("/audit", json=dict(problem_id=PROBLEM, solution="x=1\nx=2\nx=3")).json()
    manifest = response["reproducibility"]["record"]["manifest"]
    assert manifest["problem_assets"][0]["sha256"] == original
    assert sha256(path.read_bytes()) != original
    assert calls == {"dependencies": 1, "versions": ["lean", "lake"]}


def test_formal_version_change_affects_deterministic_identity(project, monkeypatch):
    monkeypatch.setattr(collector, "installed_formal_version", lambda *args: collector.identified("4.28.0", "command"))
    first = collector.collect(project, PROBLEM, environ=ENV, distributions=[]).manifest
    monkeypatch.setattr(collector, "installed_formal_version", lambda *args: collector.identified("4.29.0", "command"))
    second = collector.collect(project, PROBLEM, environ=ENV, distributions=[]).manifest
    assert first.formal_environment != second.formal_environment


def test_timeouts_are_sanitized(project, monkeypatch):
    import subprocess
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("private-command", 3, output="secret-value")
    monkeypatch.setattr(collector.subprocess, "run", timeout)
    assert collector.command_output(["git", "rev-parse", "HEAD"], project) is None


def test_required_asset_missing_keeps_existing_validation(pipeline, project):
    (project / "problems" / PROBLEM / "rubric.json").unlink()
    response = pipeline.post("/audit", json=dict(problem_id=PROBLEM, solution="x=1"))
    assert response.status_code == 400


def test_environment_secrets_absent_from_all_outputs(pipeline, project, monkeypatch, caplog, capsys):
    secrets = {key: f"fake-sensitive-{key}-private-value" for key in
               ("OPENAI_API_KEY", "AWS_SECRET_ACCESS_KEY", "PASSWORD", "COOKIE", "AUTHORIZATION", "UNLISTED_TOKEN")}
    for key, value in secrets.items():
        monkeypatch.setenv(key, value)
    sid, request, run = pair(pipeline)
    textual = pipeline.post("/audit", json=dict(problem_id=PROBLEM, solution="x=1"))
    endpoint = pipeline.get(f'/submission-audits/{run["audit_run_id"]}/reproducibility')
    captured = capsys.readouterr()
    outputs = json.dumps(run) + textual.text + endpoint.text + caplog.text + captured.out + captured.err
    for path in project.rglob("*"):
        if path.is_file():
            outputs += path.read_bytes().decode("utf-8", errors="replace")
    assert all(value not in outputs for value in secrets.values())


def test_ui_disclosure_language_and_safe_technical_paths():
    source = (ROOT / "app/confia_lean_auditor/static/app.js").read_text()
    for label in ("Ambiente da análise", "Metadados da execução registrados.",
                  "Metadados de reprodutibilidade não registrados nesta execução.",
                  "Detalhes técnicos", "não é assinatura digital"):
        assert label in source
    assert "Execução garantidamente reproduzível" not in source
    assert "targetPanel.appendChild(renderEnvironment(data))" in source
    assert "JSON.stringify(data, publicTechnicalValue, 2)" in source
