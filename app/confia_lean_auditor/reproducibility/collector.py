"""One fresh snapshot per engine invocation; never collected per claim.

No process cache: edits, dependency changes and different worktrees are visible
on the next run. Commands never return their diagnostics to a public record.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from uuid import uuid4

from confia_lean_auditor.core.paths import validate_problem_id
from confia_lean_auditor.versions import API_VERSION
from .canonical import sha256
from .schemas import (
    ApplicationIdentity, AssetFingerprint, AuditReproducibilityManifest,
    CodeIdentity, ExecutionConfiguration, FormalEnvironment, IdentifiedValue,
    LeanDependency, PythonEnvironment,
)

COMMIT_PATTERN = r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})"
VERSION_PATTERN = r"[0-9][A-Za-z0-9.!+_-]{0,99}"
TOOLCHAIN_PATTERN = r"leanprover/lean4:v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?"


def identified(value, source):
    return IdentifiedValue(value=value, metadata_source=source, reason=None)


def validated(value, pattern, source):
    if value is not None and re.fullmatch(pattern, value):
        return identified(value, source)
    return IdentifiedValue(reason="invalid_value" if value is not None else "not_available")


def command_output(command, root):
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                timeout=3, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None


def collect_code(root, environ):
    commit = validated(environ.get("CONFIA_BUILD_COMMIT"), COMMIT_PATTERN, "environment")
    raw_dirty = environ.get("CONFIA_BUILD_DIRTY")
    dirty = {"true": True, "false": False, "1": True, "0": False}.get(raw_dirty)
    dirty_source = "environment" if dirty is not None else "unavailable"
    # Git is a development fallback. Never infer identity from a parent repo.
    if (root / ".git").exists():
        if commit.value is None and "CONFIA_BUILD_COMMIT" not in environ:
            commit = validated(command_output(["git", "rev-parse", "HEAD"], root), COMMIT_PATTERN, "git")
        if raw_dirty is None:
            status = command_output(["git", "--no-optional-locks", "status", "--porcelain", "--untracked-files=normal"], root)
            if status is not None:
                dirty, dirty_source = bool(status), "git"
    if commit.value:
        commit.value = commit.value.lower()
    return CodeIdentity(git_commit=commit, worktree_dirty=dirty,
        worktree_dirty_source=dirty_source,
        build_id=validated(environ.get("CONFIA_BUILD_ID"), r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", "environment"))


def asset(root, relative_path, logical_name, required=True):
    value = AssetFingerprint(logical_name=logical_name, relative_path=relative_path,
                             required=required, status="unavailable", reason="missing_or_unreadable")
    path = root / relative_path
    try:
        path.resolve().relative_to(root.resolve())
        if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
            return value.model_copy(update={"reason": "unsafe_path"})
        data = path.read_bytes()
    except ValueError:
        return value.model_copy(update={"reason": "unsafe_path"})
    except OSError:
        return value
    return value.model_copy(update={"status": "available", "reason": None,
                                    "sha256": sha256(data), "size_bytes": len(data)})


def dependency_manifest(distributions=None):
    """Names/versions only; no direct_url, install locations or package metadata."""
    distributions = metadata.distributions() if distributions is None else distributions
    entries = set()
    for distribution in distributions:
        name, version = distribution.metadata.get("Name"), distribution.version
        if (not name or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name)
                or not version or not re.fullmatch(VERSION_PATTERN, version)):
            raise ValueError("invalid dependency identity")
        name = re.sub(r"[-_.]+", "-", name).lower()
        entries.add((name, version))
    return "".join(f"{name}=={version}\n" for name, version in sorted(entries)).encode("utf-8"), len(entries)


def application_identity(root):
    # Import lazily: the bridge itself depends on the engine response schema.
    from confia_lean_auditor.capture.schemas import SCHEMA_VERSION
    from confia_lean_auditor.submission_audits.schemas import AuditProvenance
    version = IdentifiedValue()
    try:
        # Python 3.9 is supported. Read only the literal project version, without
        # adding a TOML parser dependency or confusing it with tool versions.
        project = (root / "pyproject.toml").read_text(encoding="utf-8")
        section = re.search(r"(?ms)^\[project\]\s*$(.*?)(?=^\[|\Z)", project)
        match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', section[1]) if section else None
        if match:
            version = validated(match[1], VERSION_PATTERN, "project")
    except (OSError, UnicodeError):
        pass
    if version.value is None:
        try:
            version = validated(metadata.version("confia-lean-auditor"), VERSION_PATTERN, "package")
        except metadata.PackageNotFoundError:
            pass
    return ApplicationIdentity(project_version=version, api_version=API_VERSION,
        audit_bridge_version=IdentifiedValue(reason="not_versioned"),
        conversion_version=AuditProvenance.model_fields["conversion_version"].default,
        capture_schema_version=SCHEMA_VERSION)


def installed_formal_version(root, toolchain, tool, environ):
    """Call installed binaries directly: never run an elan installation shim."""
    if not toolchain.value:
        return IdentifiedValue()
    elan_root = Path(environ.get("ELAN_HOME", str(Path.home() / ".elan")))
    binary = elan_root / "toolchains" / toolchain.value.replace("/", "--").replace(":", "---") / "bin" / tool
    selected = shutil.which(tool, path=environ.get("PATH", os.environ.get("PATH", "")))
    # Only infer shim selection when no higher-priority override exists. A
    # custom PATH or elan override must not be labelled as the declared toolchain.
    if not selected or Path(selected) not in (elan_root / "bin" / tool, binary):
        return IdentifiedValue()
    if environ.get("ELAN_TOOLCHAIN"):
        return IdentifiedValue()
    try:
        settings = (elan_root / "settings.toml").read_text()
        overrides = re.search(r"(?ms)^\[overrides\]\s*$(.*?)(?=^\[|\Z)", settings)
        if overrides and any(line.strip() and not line.lstrip().startswith("#") for line in overrides[1].splitlines()):
            return IdentifiedValue()
    except FileNotFoundError:
        pass
    except (OSError, UnicodeError):
        return IdentifiedValue()
    if not binary.is_file():
        return IdentifiedValue()
    output = command_output([str(binary), "--version"], root)
    # Keep only version tokens, never diagnostics, paths or host build strings.
    pattern = r"Lean \(version ([0-9][A-Za-z0-9.+_-]*)" if tool == "lean" else r"Lake version ([0-9][A-Za-z0-9.+_-]*)"
    match = re.match(pattern, output or "")
    return identified(match[1], "command") if match else IdentifiedValue(reason="command_failed")


def formal_environment(root, environ, configurations):
    available = {item.relative_path for item in configurations if item.status == "available"}
    toolchain = IdentifiedValue()
    dependencies = []
    if "lean-toolchain" in available:
        toolchain = validated((root / "lean-toolchain").read_text().strip(), TOOLCHAIN_PATTERN, "project")
    if "lake-manifest.json" in available:
        try:
            packages = json.loads((root / "lake-manifest.json").read_bytes()).get("packages", [])
            for package in packages:
                name = package.get("name", "")
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,79}", name):
                    dependencies.append(LeanDependency(name=name,
                        revision=validated(package.get("rev"), COMMIT_PATTERN, "lake-manifest")))
        except (ValueError, TypeError, AttributeError):
            dependencies = []
    mathlib = next((item.revision for item in dependencies if item.name == "mathlib"), IdentifiedValue())
    return FormalEnvironment(toolchain=toolchain, mathlib_revision=mathlib,
        dependencies=sorted(dependencies, key=lambda item: item.name),
        lean_version=installed_formal_version(root, toolchain, "lean", environ),
        lake_version=installed_formal_version(root, toolchain, "lake", environ))


@dataclass
class ExecutionSnapshot:
    manifest: AuditReproducibilityManifest
    dependencies: bytes


def collect(root, problem_id, *, environ=None, distributions=None):
    root = Path(root).resolve()
    validate_problem_id(problem_id)
    environ = os.environ if environ is None else environ
    generated_at = datetime.now(timezone.utc)
    code = collect_code(root, environ)
    assets = [asset(root, f"problems/{problem_id}/{name}", name) for name in
              ("problem.json", "rubric.json", "microclaims.json")]
    assets.append(asset(root, f"ConfiaLeanAuditor/Problems/{problem_id}/Statement.lean", "formal_statement"))
    configurations = [asset(root, name, name) for name in
                      ("pyproject.toml", "lean-toolchain", "lakefile.toml", "lake-manifest.json")]
    dependencies, count = dependency_manifest(distributions)
    python = PythonEnvironment(version=sys.version, implementation=platform.python_implementation(),
        major=sys.version_info.major, minor=sys.version_info.minor, micro=sys.version_info.micro,
        operating_system=platform.system(), release=platform.release(), machine=platform.machine(),
        dependency_manifest_sha256=sha256(dependencies), dependency_manifest_size_bytes=len(dependencies),
        dependency_count=count)
    formal = formal_environment(root, environ, configurations)
    limitations = ["Metadados de reprodutibilidade registrados; reprodução bit a bit não é garantida.",
        "SHA-256 fornece integridade técnica interna; não é assinatura digital nem prova de autoria.",
        "Versões e revisões declaradas não atestam os binários ou o conteúdo instalado de dependências.",
        "O toolchain registra a configuração do projeto; overrides ou PATH não reconhecidos deixam versões indisponíveis.",
        "Captura pontual antes do pipeline; alterações concorrentes do ambiente não são impedidas."]
    if code.worktree_dirty:
        limitations.append("Worktree dirty: o commit não identifica todo o código executado; fingerprint não coletado.")
    if code.worktree_dirty is None or code.git_commit.value is None:
        limitations.append("Identidade do código incompleta.")
    if any(item.status != "available" for item in assets + configurations):
        limitations.append("Há assets indisponíveis; consulte o status de cada arquivo.")
    if any(item.value is None for item in (formal.lean_version, formal.lake_version, formal.mathlib_revision)):
        limitations.append("Identificação do ambiente formal incompleta.")
    enabled = environ.get("CONFIA_ENABLE_LLM_FORMAL_STEPS") == "1"
    # The default belongs to the real extractor; prompts/templates live in code.
    from confia_lean_auditor.llm.formal_step_extractor import DEFAULT_LLM_MODEL
    model = validated(environ.get("CONFIA_LLM_MODEL", DEFAULT_LLM_MODEL),
                      r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}",
                      "environment" if "CONFIA_LLM_MODEL" in environ else "project") if enabled else IdentifiedValue()
    if enabled:
        limitations.append("Extração por serviço LLM habilitada; resposta externa não tem reprodução garantida.")
    return ExecutionSnapshot(AuditReproducibilityManifest(manifest_id="rep_" + uuid4().hex,
        generated_at=generated_at, problem_id=problem_id, code_identity=code,
        application_identity=application_identity(root), problem_assets=assets,
        configuration_assets=configurations, python_environment=python, formal_environment=formal,
        execution_configuration=ExecutionConfiguration(llm_formal_steps_enabled=enabled, llm_model=model),
        limitations=limitations), dependencies)


def capture(root, problem_id):
    """Noncritical governance failure must not become a mathematical failure."""
    try:
        return collect(root, problem_id)
    except Exception:
        # Never persist/log an exception that may contain environment values.
        return None
