"""Immutable, offline ITA evaluation wrapper. Selection never imports the engine.

Prepare with --select-smoke; execute later with --run --selection-file PATH and
a DIFFERENT, new --output. No in-place resume, retries, gold or score comparison.
Per-case checkpoints and inflight records are retained even on interruption.
Only I/O/provider boundaries are adapted; mathematical callables stay unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack, contextmanager
import csv
from datetime import datetime, timezone
import hashlib
import http.client
import importlib
import io
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
PROBLEMS = ("ITA2025F2Q1", "ITA2025F2Q5", "ITA2025F2Q6")
DEFAULT_DATASET = Path("/Users/LinMarcolino/Library/CloudStorage/Dropbox/envio_v2.0/solucoes_v2.0.csv")
VERSION = "ita-lean-strong-local.v1"
UNSUPPORTED = "UNSUPPORTED_IN_THIS_RUNNER"
COUNTS = ("claims_extracted", "student_claims", "formal_verified_student",
          "formal_verified_reference", "deterministic_verified", "refuted_formal",
          "refuted_deterministic", "indeterminate", "technical_errors",
          "lean_attempts_student", "lean_attempts_reference", "lean_success_student",
          "lean_success_reference", "lean_failures")


class RunnerError(ValueError):
    pass


class LocalOnlyViolation(RuntimeError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(Path(path).read_bytes())


def write_new(path, value):
    """Exclusive creation; never replace an existing artifact."""
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def append(handle, value):
    handle.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
    handle.flush()
    os.fsync(handle.fileno())


def disable_external_configuration():
    # Never read, log, restore or pass the credential to a client/subprocess.
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ["CONFIA_ENABLE_LLM_FORMAL_STEPS"] = "0"
    os.environ["CONFIA_TME_SEMANTIC_ENABLED"] = "0"
    sys.dont_write_bytecode = True


def load_dataset(path):
    path = Path(path).resolve(strict=True)
    data = path.read_bytes()
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
    if reader.fieldnames != ["id", "qid", "texto"]:
        raise RunnerError("DATASET_SCHEMA: expected exactly id,qid,texto; gold columns forbidden")
    cases, seen = [], set()
    for row in reader:
        if set(row) != {"id", "qid", "texto"} or any(v is None for v in row.values()):
            raise RunnerError("DATASET_SCHEMA: malformed row")
        cid, qid = row["id"], row["qid"]
        if (not re.fullmatch(r"[A-Za-z0-9_-]+", cid) or cid in seen
                or not re.fullmatch(r"[A-Za-z0-9_-]+", qid)):
            raise RunnerError("DATASET_IDS: invalid or duplicate identifier")
        seen.add(cid)
        cases.append(dict(solution_id=cid, problem_id=qid, text=row["texto"],
                          source_sha256=sha(row["texto"].encode("utf-8"))))
    if not cases:
        raise RunnerError("EMPTY_DATASET")
    return cases, dict(path=str(path), sha256=sha(data))


def identity(case):
    return {k: case[k] for k in ("solution_id", "problem_id", "source_sha256")}


def dataset_manifest(cases, dataset):
    groups = defaultdict(list)
    for c in cases:
        groups[c["problem_id"], c["source_sha256"]].append(c["solution_id"])
    return dict(dataset, timestamp=now(), total_rows=len(cases),
                by_problem=dict(sorted(Counter(c["problem_id"] for c in cases).items())),
                cases=[dict(identity(c), eligibility="SUPPORTED" if c["problem_id"] in PROBLEMS else UNSUPPORTED)
                       for c in cases],
                duplicates_by_problem_text=[dict(problem_id=q, source_sha256=h, solution_ids=ids)
                    for (q, h), ids in sorted(groups.items()) if len(ids) > 1])


def select(cases, dataset, args):
    for qid in args.problem or []:
        if qid not in PROBLEMS:
            raise RunnerError(f"{UNSUPPORTED}: {qid}")
    if args.select_smoke and (args.problem or args.case_id or args.limit or args.selection_file):
        raise RunnerError("Smoke is exactly three IDs per allowed problem; filters cannot be combined")
    if args.selection_file:
        if args.problem or args.case_id or args.limit:
            raise RunnerError("Frozen selection cannot be combined with filters")
        saved = json.loads(args.selection_file.read_text(encoding="utf-8"))
        if saved.get("version") != VERSION or saved.get("dataset_sha256") != dataset["sha256"]:
            raise RunnerError("SELECTION_DATASET_MISMATCH")
        index = {c["solution_id"]: c for c in cases}
        chosen = []
        for c in saved.get("cases", []):
            if c.get("problem_id") not in PROBLEMS:
                raise RunnerError(UNSUPPORTED)
            original = index.get(c.get("solution_id"))
            if original is None or identity(original) != c:
                raise RunnerError("SELECTION_SOURCE_MISMATCH")
            chosen.append(original)
        policy = saved.get("selection_policy", "frozen_ids")
    else:
        chosen = sorted((c for c in cases if c["problem_id"] in PROBLEMS),
                        key=lambda c: (c["problem_id"], c["solution_id"]))
        if args.problem:
            chosen = [c for c in chosen if c["problem_id"] in args.problem]
        if args.case_id:
            index = {c["solution_id"]: c for c in cases}
            for cid in args.case_id:
                if cid not in index:
                    raise RunnerError("UNKNOWN_CASE_ID: " + cid)
                if index[cid]["problem_id"] not in PROBLEMS:
                    raise RunnerError(UNSUPPORTED + ": " + cid)
                if args.problem and index[cid]["problem_id"] not in args.problem:
                    raise RunnerError("CASE_PROBLEM_FILTER_MISMATCH")
            chosen = [c for c in chosen if c["solution_id"] in args.case_id]
        policy = "allowed_cases_sorted_by_problem_and_id"
        if args.select_smoke:
            smoke = []
            for qid in PROBLEMS:
                group = [c for c in chosen if c["problem_id"] == qid]
                if len(group) < 3:
                    raise RunnerError("SMOKE_REQUIRES_AT_LEAST_THREE_CASES_PER_PROBLEM")
                smoke.extend(group[i] for i in (0, len(group) // 2, len(group) - 1))
            chosen, policy = smoke, "first_upper_median_last_id_per_problem; no labels"
        elif args.limit:
            chosen = chosen[:args.limit]
    if not chosen or len({c["solution_id"] for c in chosen}) != len(chosen):
        raise RunnerError("EMPTY_OR_DUPLICATE_SELECTION")
    return chosen, dict(version=VERSION, dataset_sha256=dataset["sha256"],
                        selection_policy=policy, cases=[identity(c) for c in chosen])


def engine_hashes():
    files = set()
    for directory, suffix in (("app", ".py"), ("app", ".json"),
                              ("ConfiaLeanAuditor", ".lean"), ("problems", ".json")):
        files.update(p for p in (ROOT / directory).rglob("*" + suffix) if p.is_file())
    files.update(ROOT / name for name in ("pyproject.toml", "lean-toolchain", "lakefile.toml", "lake-manifest.json"))
    return {str(p.relative_to(ROOT)): file_sha(p) for p in sorted(files)}


def installed_tools():
    toolchain = (ROOT / "lean-toolchain").read_text().strip()
    if not re.fullmatch(r"leanprover/lean4:v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?", toolchain):
        raise RunnerError("UNSUPPORTED_LOCAL_TOOLCHAIN")
    directory = (Path(os.environ.get("ELAN_HOME", str(Path.home() / ".elan"))) / "toolchains" / toolchain.replace("/", "--").replace(":", "---") / "bin").resolve()
    tools = {name: directory / name for name in ("lean", "lake")}
    if any(not p.is_file() for p in tools.values()):
        raise RunnerError("LOCAL_TOOLCHAIN_MISSING: installation/download is forbidden")
    return tools


def local_lean_path():
    manifest = json.loads((ROOT / "lake-manifest.json").read_text())
    names = [p["name"] for p in manifest["packages"]]
    if any(not re.fullmatch(r"[A-Za-z0-9_-]+", n) for n in names):
        raise RunnerError("INVALID_LAKE_PACKAGE")
    paths = [ROOT / ".lake/build/lib/lean"] + [ROOT / ".lake/packages" / n / ".lake/build/lib/lean" for n in names]
    # Packages such as Cli can belong to Lake's tooling without a built Lean
    # library used by these proofs. Missing optional search paths are harmless;
    # imports still fail locally if an actual dependency is unavailable.
    if not paths[0].is_dir() or not (ROOT / ".lake/packages/mathlib/.lake/build/lib/lean/Mathlib.olean").is_file():
        raise RunnerError("LOCAL_LEAN_CACHE_MISSING: no download/build allowed")
    for qid in PROBLEMS:
        if not (paths[0] / "ConfiaLeanAuditor/Problems" / qid / "Statement.olean").is_file():
            raise RunnerError("LOCAL_PROBLEM_OLEAN_MISSING: " + qid)
    return os.pathsep.join(map(str, paths))


def snapshot():
    def command(argv):
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=10, check=True)
        return result.stdout.strip()
    tools = installed_tools()
    hashes = engine_hashes()
    lake = json.loads((ROOT / "lake-manifest.json").read_text())
    return dict(timestamp=now(), git_sha=command(["git", "rev-parse", "HEAD"]),
        git_branch=command(["git", "branch", "--show-current"]),
        git_status=command(["git", "--no-optional-locks", "status", "--porcelain"]),
        python=sys.version, python_executable=sys.executable,
        lean_version=command([str(tools["lean"]), "--version"]),
        lean_binary_sha256=file_sha(tools["lean"]), lake_manifest_sha256=hashes["lake-manifest.json"],
        mathlib_revision=next(p["rev"] for p in lake["packages"] if p["name"] == "mathlib"),
        runner_sha256=file_sha(__file__), engine_files_sha256=hashes,
        external_api_enabled=False, llm_formal_steps=False, secondary_remote_adjudication=False,
        credential_policy="OPENAI_API_KEY removed, never logged or forwarded",
        untracked_audit_note="docs/audits/TME_HOLDOUT_EVAL_01.md is documented by git_status and is not a blocker",
        process_policy="Installed Lean only; lake env lean translated to direct Lean with cached LEAN_PATH; no installer or network subprocess")


def protocol():
    return dict(version=VERSION, allowed_problems=PROBLEMS, external_api_enabled=False,
        gold_loaded=False, scoring_policy="unchanged engine SCORE-POLICY-02; remote boundary unavailable",
        pipeline_valid="Supported ID + valid engine response + consistent numeric decision or local abstention + no technical errors, forbidden external attempts or instrumentation gaps. Null is valid only for EMPTY_SOLUTION or explicitly local ADJUDICATOR_UNAVAILABLE, with needs_review=true.",
        numeric_score="score is a finite number; null is retained and counted separately",
        formal_verified_student="Source-attributed verified student checks with successful observed positive Lean process and matching proof hash",
        formal_verified_reference="Verified certificate/formal steps with matching observed successful Lean process; excludes derived microclaims",
        deterministic_verified="Supported rubric criteria explicitly tagged positive_evidence.verification_type=deterministic_check; not grounded_text or inferred from missing files",
        refuted_deterministic="Only student checks explicitly tagged verification_source=deterministic and status=refuted; never infer from absence of Lean",
        indeterminate="Rubric criteria with mathematical_status=indeterminate",
        lean_counts="Actual spawned processes, including negative proof attempts; process success is exit 0, distinct from attributed evidence. Version probes excluded.",
        technical_errors="Fatal/contract errors plus engine checks classified technical_error and invalid rubric configuration; local provider unavailability alone is not a technical failure",
        output_policy="New directory only. No overwrite or in-place resume. Reuse selection in a new output; per-case checkpoints/inflight records preserved for explicit recovery, never automatic retries.",
        mathematical_engine_changed=False, runtime_io="Byte-identical problem/config copies and dedicated student proof directory under new output")


class LocalGuard:
    """Process-scoped network/client deny and observed, offline Lean transport.

    This wraps subprocess execution, not proof generation or verification logic.
    All Python-launched child commands are denied except installed version probes
    and Lean on files inside this run. No lake/elan resolution can fetch packages.
    """
    def __init__(self, runtime, tools, lean_path):
        self.runtime, self.tools, self.lean_path = runtime, tools, lean_path
        self.events, self.violations = [], []
        self.authorized = None

    def deny(self, *args, **kwargs):
        self.violations.append("EXTERNAL_OR_UNAPPROVED_OPERATION_BLOCKED")
        raise LocalOnlyViolation(self.violations[-1])

    @contextmanager
    def active(self):
        disable_external_configuration()
        original_run, original_popen = subprocess.run, subprocess.Popen
        with ExitStack() as stack:
            for target in ("socket.create_connection", "socket.getaddrinfo", "socket.gethostbyname",
                           "socket.gethostbyname_ex", "socket.socket.connect", "socket.socket.connect_ex",
                           "socket.socket.sendto", "socket.socket.send", "socket.socket.sendall",
                           "socket.getnameinfo", "http.client.HTTPConnection.__init__", "os.system"):
                stack.enter_context(patch(target, self.deny))
            # Importing these libraries creates no clients. Block even explicitly
            # supplied credentials; key removal is not the sole protection.
            for module_name, classes in (("httpx", ("Client", "AsyncClient")),
                                         ("openai", ("OpenAI", "AsyncOpenAI", "AzureOpenAI", "AsyncAzureOpenAI"))):
                module = importlib.import_module(module_name)
                for name in classes:
                    stack.enter_context(patch.object(getattr(module, name), "__init__", self.deny))

            def popen(command, *args, **kwargs):
                if self.authorized is None or command != self.authorized[0] or args or kwargs.get("shell"):
                    return self.deny()
                event = self.authorized[1]
                proc = original_popen(command, **kwargs)
                if event is not None:
                    event["spawned"] = True
                return proc

            def run(command, *args, **kwargs):
                if args or not isinstance(command, (list, tuple)) or kwargs.get("shell") or kwargs.get("executable"):
                    return self.deny()
                argv = list(map(str, command)); event = None
                if argv[:3] == ["lake", "env", "lean"] and len(argv) == 4:
                    source = Path(argv[3]).resolve(strict=True)
                    if not source.is_relative_to(self.runtime) or source.suffix != ".lean":
                        return self.deny()
                    argv = [str(self.tools["lean"]), str(source)]
                    event = dict(started_at=now(), lean_file=str(source), source_sha256=file_sha(source),
                        scope="student" if "student_claim_checks" in source.parts else "reference",
                        proof_kind="negation" if source.stem.endswith("_refutation") else "positive",
                        spawned=False, exit_code=None, timeout=False)
                    self.events.append(event)
                elif argv not in ([str(p), "--version"] for p in self.tools.values()):
                    return self.deny()
                env = os.environ.copy()
                env.pop("OPENAI_API_KEY", None)
                env["LEAN_PATH"] = self.lean_path
                env["CONFIA_ENABLE_LLM_FORMAL_STEPS"] = "0"
                kwargs["env"] = env
                kwargs["cwd"] = self.runtime
                self.authorized = (argv, event)
                started = time.monotonic()
                try:
                    result = original_run(argv, **kwargs)
                    if event is not None:
                        event["exit_code"] = result.returncode
                    return result
                except subprocess.TimeoutExpired:
                    if event is not None:
                        event["timeout"] = True
                    raise
                finally:
                    self.authorized = None
                    if event is not None:
                        event.update(finished_at=now(), elapsed_seconds=time.monotonic() - started)

            stack.enter_context(patch("subprocess.Popen", popen))
            stack.enter_context(patch("subprocess.run", run))
            yield self


def prepare_runtime(output, state):
    runtime = output / "engine_workspace"
    runtime.mkdir()
    copies = ["pyproject.toml", "lean-toolchain", "lakefile.toml", "lake-manifest.json"]
    for qid in PROBLEMS:
        copies.extend(f"problems/{qid}/{name}" for name in ("problem.json", "rubric.json", "microclaims.json"))
        copies.append(f"ConfiaLeanAuditor/Problems/{qid}/Statement.lean")
    for relative in copies:
        destination = runtime / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as handle:
            handle.write((ROOT / relative).read_bytes())
        if file_sha(destination) != state["engine_files_sha256"][relative]:
            raise RunnerError("RUNTIME_INPUT_CHANGED")
    return runtime, copies


@contextmanager
def engine_session(runtime, state):
    """Same execute_audit, with isolated files and an unavailable local provider."""
    if str(ROOT / "app") not in sys.path:
        sys.path.insert(0, str(ROOT / "app"))
    guard = LocalGuard(runtime, installed_tools(), local_lean_path())
    with guard.active(), ExitStack() as stack:
        from confia_lean_auditor.rubric import secondary_adjudicator as secondary

        def unavailable(_payload):
            raise secondary.AdjudicationError("ADJUDICATOR_UNAVAILABLE", category="LOCAL_ONLY_REMOTE_DISABLED",
                diagnostics=dict(validation_status="not_attempted", error_code="ADJUDICATOR_UNAVAILABLE",
                    reason="LOCAL_ONLY_REMOTE_DISABLED", attempts=0, retry_count=0, external_api_enabled=False))

        stack.enter_context(patch.object(secondary, "adjudicate", unavailable))
        stack.enter_context(patch.dict(os.environ, {
            "CONFIA_LEAN_AUDITOR_ROOT": str(runtime), "CONFIA_ENABLE_LLM_FORMAL_STEPS": "0",
            "CONFIA_BUILD_COMMIT": state["git_sha"], "CONFIA_BUILD_DIRTY": str(bool(state["git_status"])).lower(),
        }))
        for module in ["confia_lean_auditor.lean.student_claim_checker"] + [
                "confia_lean_auditor.lean.student_claim_checkers." + q.lower() for q in PROBLEMS]:
            stack.enter_context(patch.object(importlib.import_module(module), "CHECK_DIR",
                                            runtime / "artifacts/student_claim_checks"))
        from confia_lean_auditor.main import execute_audit
        from confia_lean_auditor.core.schemas import AuditRequest

        def execute(case):
            if case["problem_id"] not in PROBLEMS:
                raise RunnerError(UNSUPPORTED)
            if "OPENAI_API_KEY" in os.environ or os.environ.get("CONFIA_ENABLE_LLM_FORMAL_STEPS") != "0":
                return guard.deny()
            # Exactly two engine inputs: never selection metadata or labels.
            return execute_audit(AuditRequest(problem_id=case["problem_id"], solution=case["text"]))

        if guard.violations:
            raise LocalOnlyViolation("BLOCKED_OPERATION_DURING_ENGINE_IMPORT")
        yield execute, guard


def measure(case, raw, events, *, error=None):
    row = dict(identity(case), **dict.fromkeys(COUNTS, 0), score=None, numeric_score=False,
               needs_review=True, pipeline_valid=False, unscorable_reason=None,
               instrumentation_gaps=[], error=error)
    spawned = [e for e in events if e["spawned"]]
    for scope in ("student", "reference"):
        group = [e for e in spawned if e["scope"] == scope]
        row["lean_attempts_" + scope] = len(group)
        row["lean_success_" + scope] = sum(e["exit_code"] == 0 for e in group)
    row["lean_failures"] = sum(e["exit_code"] != 0 for e in spawned)
    row["technical_errors"] = int(error is not None)
    if raw is None:
        return row
    from confia_lean_auditor.lean.verification import verification_state
    from confia_lean_auditor.student_claims.grounding import source_matches
    rubric = raw["rubric_assessment"]
    checks = raw["student_claim_checks"]
    references = [raw["lean_certificate"], *raw["formal_steps"]]
    used_events = set()

    def witness(check, scope, field="lean_file", kind="positive"):
        if scope == "student" and not source_matches(check, case["text"]):
            return False
        path = check.get(field)
        if not path or not Path(path).is_file():
            return False
        digest = file_sha(path)
        for index, event in enumerate(spawned):
            if (index not in used_events and event["scope"] == scope and event["proof_kind"] == kind
                    and event["exit_code"] == 0 and event["source_sha256"] == digest):
                used_events.add(index)
                return True
        return False

    for scope, group in (("student", checks), ("reference", references)):
        for check in group:
            technical = (check["status"] in {"technical_error", "error"} if scope == "student"
                         else verification_state(check) == "technical_error")
            if technical:
                row["technical_errors"] += 1
            if check["status"] == "verified" and check.get("compiled"):
                if witness(check, scope):
                    row["formal_verified_" + scope] += 1
                else:
                    row["instrumentation_gaps"].append(check.get("id", "certificate"))
            if scope == "student" and check["status"] == "refuted" and check.get("refutation_verified"):
                if witness(check, scope, "refutation_lean_file", "negation"):
                    row["refuted_formal"] += 1
                else:
                    row["instrumentation_gaps"].append(check.get("id", "refutation"))
            if check.get("verification_source") == "deterministic" and check["status"] == "refuted":
                row["refuted_deterministic"] += 1
    row.update(score=raw["score"], needs_review=raw["needs_review"],
        unscorable_reason=raw["unscorable_reason"], claims_extracted=len(raw["extracted_claims"]["claims"]),
        student_claims=len(raw["student_claims"]),
        indeterminate=sum(i["mathematical_status"] == "indeterminate" for i in rubric["items"]),
        deterministic_verified=sum(i["mathematical_status"] == "supported" and
            (i.get("positive_evidence") or {}).get("supported") is True and
            i["positive_evidence"].get("verification_type") == "deterministic_check" for i in rubric["items"]))
    numeric = isinstance(raw["score"], (int, float)) and not isinstance(raw["score"], bool) and math.isfinite(raw["score"])
    row["numeric_score"] = numeric
    secondary = rubric.get("secondary_adjudication") or {}
    local_abstention = (raw["score"] is None and raw["needs_review"] is True and
        (raw["unscorable_reason"] == "EMPTY_SOLUTION" or
         raw["unscorable_reason"] == "ADJUDICATOR_UNAVAILABLE" and secondary.get("reason") == "LOCAL_ONLY_REMOTE_DISABLED"))
    numeric_valid = (numeric and 0 <= raw["score"] <= raw["max_score"] and
                     raw["unscorable_reason"] is None and
                     all(i.get("points") is not None and i.get("suggested_points") == i["points"] for i in rubric["items"]) and
                     math.isclose(raw["score"], sum(i["points"] for i in rubric["items"])))
    contract_ok = (raw["problem_id"] == case["problem_id"] and rubric["score"] == raw["score"] and
        rubric.get("needs_review") == raw["needs_review"] and secondary.get("attempts", 0) == 0 and
        not any(i.get("scoring_basis") == "secondary_adjudication" for i in rubric["items"]))
    if not contract_ok or not (numeric_valid or local_abstention) or raw["unscorable_reason"] == "INVALID_RUBRIC":
        row["technical_errors"] += 1
        row["error"] = "INVALID_LOCAL_SCORE_CONTRACT"
    row["pipeline_valid"] = (case["problem_id"] in PROBLEMS and contract_ok and
        (numeric_valid or local_abstention) and not row["technical_errors"] and not row["instrumentation_gaps"])
    return row


def summarize(selected, rows):
    return dict(cases_selected=len(selected), cases_attempted=len(rows),
        supported=sum(c["problem_id"] in PROBLEMS for c in selected),
        pipeline_valid=sum(r["pipeline_valid"] for r in rows),
        numeric_scores=sum(r["numeric_score"] for r in rows),
        null_scores=sum(r["score"] is None for r in rows), needs_review=sum(bool(r["needs_review"]) for r in rows),
        technical_failures=sum(bool(r["technical_errors"] or r["instrumentation_gaps"]) for r in rows),
        **{k: sum(r[k] for r in rows) for k in COUNTS})


def verify_inputs(dataset, state, runtime=None, copies=()):
    def unchanged(path, digest):
        try:
            return file_sha(path) == digest
        except OSError:
            return False
    try:
        engine_unchanged = engine_hashes() == state["engine_files_sha256"]
    except OSError:
        engine_unchanged = False
    return dict(dataset_unchanged=unchanged(dataset["path"], dataset["sha256"]),
        engine_unchanged=engine_unchanged, runner_unchanged=unchanged(__file__, state["runner_sha256"]),
        runtime_inputs_unchanged=all(unchanged(runtime / p, state["engine_files_sha256"][p]) for p in copies))


def run(args):
    disable_external_configuration()
    output = args.output.resolve()
    if output.exists():
        raise RunnerError("OUTPUT_EXISTS: never overwrite; choose a new output directory")
    if args.limit is not None and args.limit <= 0:
        raise RunnerError("LIMIT_MUST_BE_POSITIVE")
    if output.is_relative_to(ROOT) and output.parent != ROOT / "artifacts/evaluations":
        raise RunnerError("OUTPUT_LOCATION: use a new direct child of artifacts/evaluations or a directory outside the repository")
    if output.is_relative_to(args.dataset.resolve().parent):
        raise RunnerError("OUTPUT_LOCATION: dataset directory is read-only")
    cases, dataset = load_dataset(args.dataset)
    selected, selection = select(cases, dataset, args)
    state = snapshot()
    if args.run:
        local_lean_path()  # Fail before creating output if cached prerequisites are absent.
    output.mkdir(parents=True, exist_ok=False)
    for name, value in (("protocol.json", protocol()), ("dataset_manifest.json", dataset_manifest(cases, dataset)),
                        ("environment_snapshot.json", state), ("selected_cases.json", selection)):
        write_new(output / name, value)
    for name in ("raw_results", "checkpoints", "inflight"):
        (output / name).mkdir()
    rows, fatal, copies, runtime = [], None, [], None
    with ExitStack() as stack:
        ledgers = {name: stack.enter_context((output / name).open("x", encoding="utf-8"))
                   for name in ("results.jsonl", "lean_events.jsonl", "errors.jsonl")}
        try:
            if args.run:
                runtime, copies = prepare_runtime(output, state)
                with engine_session(runtime, state) as (execute, guard):
                    for case in selected:
                        if not all(verify_inputs(dataset, state, runtime, copies).values()):
                            raise RunnerError("INPUT_INTEGRITY_CHANGED")
                        started_at, start = now(), time.monotonic()
                        write_new(output / "inflight" / (case["solution_id"] + ".json"),
                                  dict(identity(case), started_at=started_at))
                        event_start, violation_start = len(guard.events), len(guard.violations)
                        raw, error = None, None
                        try:
                            response = execute(case)
                            from confia_lean_auditor.core.schemas import AuditResponse
                            if not isinstance(response, AuditResponse):
                                raise RunnerError("INVALID_ENGINE_RESPONSE_TYPE")
                            raw = response.model_dump(mode="json")
                            write_new(output / "raw_results" / (case["solution_id"] + ".json"), raw)
                            if len(guard.violations) != violation_start:
                                raise LocalOnlyViolation("EXTERNAL_OR_UNAPPROVED_OPERATION_BLOCKED")
                        except Exception as exc:
                            # No exception body: it can contain solution text or credentials.
                            error = type(exc).__name__
                        events = guard.events[event_start:]
                        row = measure(case, raw, events, error=error)
                        row.update(started_at=started_at, finished_at=now(), elapsed_seconds=time.monotonic() - start)
                        raw_path = output / "raw_results" / (case["solution_id"] + ".json")
                        row["raw_result_sha256"] = file_sha(raw_path) if raw_path.exists() else None
                        for event in events:
                            append(ledgers["lean_events.jsonl"], dict(solution_id=case["solution_id"], **event))
                        write_new(output / "checkpoints" / (case["solution_id"] + ".json"), row)
                        append(ledgers["results.jsonl"], row)
                        rows.append(row)
                        if row["error"] or row["technical_errors"] or row["instrumentation_gaps"]:
                            append(ledgers["errors.jsonl"], dict(solution_id=case["solution_id"],
                                error=row["error"], technical_errors=row["technical_errors"], instrumentation_gaps=row["instrumentation_gaps"]))
                        if len(guard.violations) != violation_start:
                            raise LocalOnlyViolation("EXTERNAL_OR_UNAPPROVED_OPERATION_BLOCKED")
        except (Exception, KeyboardInterrupt) as exc:
            fatal = type(exc).__name__
            append(ledgers["errors.jsonl"], dict(fatal_error=fatal, timestamp=now()))
        finally:
            integrity = verify_inputs(dataset, state, runtime, copies)
            if not all(integrity.values()):
                fatal = "INPUT_INTEGRITY_CHANGED"
                append(ledgers["errors.jsonl"], dict(fatal_error=fatal, integrity=integrity))
            summary = summarize(selected, rows)
            summary.update(mode="run" if args.run else "selection_only", fatal_error=fatal, integrity=integrity,
                           status="FAILED" if fatal else "COMPLETE" if args.run else "SELECTED")
            write_new(output / "summary.json", summary)
            write_new(output / "summary_by_problem.json", {q: summarize(
                [c for c in selected if c["problem_id"] == q], [r for r in rows if r["problem_id"] == q]) for q in PROBLEMS})
    write_new(output / "artifact_manifest.json", dict(timestamp=now(), excludes_self=True,
        files={str(p.relative_to(output)): file_sha(p) for p in sorted(output.rglob("*")) if p.is_file()}))
    if fatal:
        raise RunnerError("RUN_FAILED: " + fatal + "; inspect the new output; no automatic retry")
    return summary


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--problem", action="append", help="Repeat to filter allowed problem IDs")
    p.add_argument("--case-id", action="append", help="Repeat to filter exact case IDs")
    p.add_argument("--limit", type=int)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--select-smoke", action="store_true")
    mode.add_argument("--run", action="store_true")
    p.add_argument("--selection-file", type=Path, help="Previously frozen selected_cases.json; output must be NEW")
    return p


def main():
    disable_external_configuration()
    p = parser()
    args = p.parse_args()
    if args.limit is not None and args.limit <= 0:
        p.error("--limit must be positive")
    try:
        result = run(args)
    except Exception as exc:
        # Only our fixed errors are printable; unknown exception strings may leak input.
        p.exit(1, (str(exc) if isinstance(exc, RunnerError) else type(exc).__name__) + "\n")
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
