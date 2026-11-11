"""Structural runner tests. No real execute_audit, grading, Lean or provider call."""
from contextlib import contextmanager
from copy import deepcopy
import csv
import http.client
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/evaluation/run_ita_lean_strong_local.py"
spec = importlib.util.spec_from_file_location("ita_local_runner", PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.fixture
def dataset(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    path = folder / "solucoes.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "qid", "texto"])
        for q in reversed(runner.PROBLEMS):
            for i in reversed(range(7)):
                writer.writerow([f"{q}_S{i:03}_L01", q, f"Texto estrutural {i}\ncom vírgula, ç."])
        writer.writerow(["OTHER_001", "ITA2025Q2", "Excluída"])
    (folder / "notas_referencia_v2.0.csv").write_text("MUST_NOT_BE_READ")
    return path


def args(dataset, output, *flags):
    return runner.parser().parse_args(["--dataset", str(dataset), "--output", str(output), *flags])


@pytest.fixture
def state(monkeypatch):
    value = dict(git_sha="a" * 40, git_status="?? docs/audits/TME_HOLDOUT_EVAL_01.md",
        engine_files_sha256=runner.engine_hashes(), runner_sha256=runner.file_sha(PATH),
        external_api_enabled=False, llm_formal_steps=False, secondary_remote_adjudication=False)
    monkeypatch.setattr(runner, "snapshot", lambda: deepcopy(value))
    monkeypatch.setattr(runner, "local_lean_path", lambda: "/existing/local/cache")
    return value


def raw_response():
    # Valid schema, explicitly synthetic response; no mathematical engine run.
    from confia_lean_auditor.core.schemas import AuditResponse
    item = dict(id="pending", description="structural fixture", detected=False, points=None,
                max_points=10, mathematical_status="indeterminate", verification_status="partial",
                verified_points=None, suggested_points=None, scoring_basis="unscorable")
    local = dict(score=None, max_score=10, needs_review=True, scoring_policy="SCORE-POLICY-02",
                 unscorable_reason="ADJUDICATOR_UNAVAILABLE", evaluated_score=0, evaluated_max_score=0)
    return AuditResponse(problem_id=runner.PROBLEMS[0], verdict="indeterminado", feedback="fixture",
        extracted_claims=dict(problem_id=runner.PROBLEMS[0], claims=[]), formal_steps=[], microclaims=[],
        lean_certificate=dict(status="unverified", compiled=False, exit_code=1,
            uses_forbidden_token=False, forbidden_tokens_found=[], lean_file=None),
        rubric_assessment=dict(items=[item], assessment_status="indeterminate",
            secondary_adjudication=dict(reason="LOCAL_ONLY_REMOTE_DISABLED", attempts=0), **local), **local)


@pytest.fixture
def fake_session(monkeypatch):
    calls = []

    @contextmanager
    def session(runtime, state):
        guard = SimpleNamespace(events=[], violations=[])

        def execute(case):
            calls.append(runner.identity(case))
            response = raw_response()
            response.problem_id = case["problem_id"]
            response.extracted_claims.problem_id = case["problem_id"]
            return response

        yield execute, guard

    monkeypatch.setattr(runner, "engine_session", session)
    return calls


def test_csv_manifest_and_no_gold_read(dataset, monkeypatch):
    original = Path.open

    def opened(path, *a, **kw):
        assert "notas_referencia" not in str(path)
        return original(path, *a, **kw)

    monkeypatch.setattr(Path, "open", opened)
    cases, source = runner.load_dataset(dataset)
    manifest = runner.dataset_manifest(cases, source)
    assert len(cases) == manifest["total_rows"] == 22
    assert source["sha256"] == runner.file_sha(dataset)
    assert all("text" not in c and len(c["source_sha256"]) == 64 for c in manifest["cases"])
    assert sum(c["eligibility"] == runner.UNSUPPORTED for c in manifest["cases"]) == 1
    assert "\n" in cases[0]["text"]


def test_gold_columns_and_duplicate_ids_rejected(dataset):
    dataset.write_text("id,qid,texto,gold_score\nx,ITA2025F2Q1,t,10\n")
    with pytest.raises(runner.RunnerError, match="gold columns forbidden"):
        runner.load_dataset(dataset)
    dataset.write_text("id,qid,texto\nx,ITA2025F2Q1,t\nx,ITA2025F2Q1,u\n")
    with pytest.raises(runner.RunnerError, match="duplicate"):
        runner.load_dataset(dataset)


def test_duplicates_are_per_problem_and_text(dataset):
    cases, source = runner.load_dataset(dataset)
    duplicate = dict(cases[0], solution_id="extra")
    result = runner.dataset_manifest([*cases, duplicate], source)
    assert len(result["duplicates_by_problem_text"]) == 1
    assert result["duplicates_by_problem_text"][0]["solution_ids"] == [cases[0]["solution_id"], "extra"]


def test_smoke_determinism_and_filters(dataset, tmp_path):
    cases, source = runner.load_dataset(dataset)
    config = args(dataset, tmp_path / "out", "--select-smoke")
    chosen, frozen = runner.select(cases, source, config)
    assert len(chosen) == 9
    assert runner.select(list(reversed(cases)), source, config)[1] == frozen
    for q in runner.PROBLEMS:
        assert [c["solution_id"] for c in chosen if c["problem_id"] == q] == [f"{q}_S{i:03}_L01" for i in (0, 3, 6)]
    filtered, _ = runner.select(cases, source, args(dataset, tmp_path / "out", "--run", "--problem", runner.PROBLEMS[1], "--limit", "2"))
    assert len(filtered) == 2 and {c["problem_id"] for c in filtered} == {runner.PROBLEMS[1]}


@pytest.mark.parametrize("flags", [("--problem", "ITA2025Q2"), ("--case-id", "OTHER_001")])
def test_unsupported_explicit_filters_rejected(dataset, tmp_path, flags):
    cases, source = runner.load_dataset(dataset)
    with pytest.raises(runner.RunnerError, match=runner.UNSUPPORTED):
        runner.select(cases, source, args(dataset, tmp_path / "out", "--run", *flags))


def test_selection_only_does_not_import_or_call_engine(dataset, tmp_path, state, monkeypatch):
    monkeypatch.setattr(runner, "engine_session", Mock(side_effect=AssertionError("engine must not load")))
    monkeypatch.setenv("OPENAI_API_KEY", "UNUSED_TEST_SENTINEL")
    monkeypatch.setenv("CONFIA_ENABLE_LLM_FORMAL_STEPS", "1")
    output = tmp_path / "selection"
    result = runner.run(args(dataset, output, "--select-smoke"))
    assert result["cases_selected"] == 9 and result["cases_attempted"] == 0
    assert "OPENAI_API_KEY" not in os.environ
    assert os.environ["CONFIA_ENABLE_LLM_FORMAL_STEPS"] == "0"
    assert not (output / "engine_workspace").exists()
    manifest = json.loads((output / "artifact_manifest.json").read_text())
    assert all(runner.file_sha(output / name) == digest for name, digest in manifest["files"].items())
    assert "score_comparison.json" not in manifest["files"]
    assert all("UNUSED_TEST_SENTINEL" not in p.read_text() for p in output.glob("*.json"))


def test_existing_output_never_touched(dataset, tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "history.json"
    sentinel.write_bytes(b"historical bytes")
    with pytest.raises(runner.RunnerError, match="OUTPUT_EXISTS"):
        runner.run(args(dataset, output, "--select-smoke"))
    assert list(output.iterdir()) == [sentinel] and sentinel.read_bytes() == b"historical bytes"


def test_frozen_selection_run_with_only_mocked_audits(dataset, tmp_path, state, fake_session):
    selection_dir, output = tmp_path / "selection", tmp_path / "run"
    runner.run(args(dataset, selection_dir, "--select-smoke"))
    before = runner.file_sha(dataset)
    result = runner.run(args(dataset, output, "--run", "--selection-file", str(selection_dir / "selected_cases.json")))
    assert len(fake_session) == result["cases_attempted"] == result["pipeline_valid"] == 9
    assert result["numeric_scores"] == result["lean_attempts_reference"] == result["lean_attempts_student"] == 0
    assert result["null_scores"] == result["needs_review"] == 9
    assert result["technical_failures"] == 0 and runner.file_sha(dataset) == before
    assert all(result["integrity"].values())
    assert len(list((output / "checkpoints").glob("*.json"))) == 9
    assert len(list((output / "inflight").glob("*.json"))) == 9
    raw = json.loads(next((output / "raw_results").glob("*.json")).read_text())
    assert raw["score"] is None and raw["rubric_assessment"]["items"][0]["points"] is None
    assert (output / "lean_events.jsonl").read_text() == ""
    assert (output / "errors.jsonl").read_text() == ""


@pytest.mark.parametrize("mutation", ["dataset", "hash", "unsupported", "duplicate"])
def test_tampered_selection_rejected(dataset, tmp_path, mutation):
    cases, source = runner.load_dataset(dataset)
    _, selection = runner.select(cases, source, args(dataset, tmp_path / "out", "--select-smoke"))
    if mutation == "dataset": selection["dataset_sha256"] = "0" * 64
    if mutation == "hash": selection["cases"][0]["source_sha256"] = "0" * 64
    if mutation == "unsupported": selection["cases"][0]["problem_id"] = "ITA2025Q2"
    if mutation == "duplicate": selection["cases"].append(selection["cases"][0])
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(selection))
    with pytest.raises(runner.RunnerError):
        runner.select(cases, source, args(dataset, tmp_path / "out", "--run", "--selection-file", str(path)))


def guard(tmp_path):
    return runner.LocalGuard(tmp_path, {"lean": Path("/installed/lean"), "lake": Path("/installed/lake")}, "/cached")


def test_network_clients_and_unapproved_processes_blocked(tmp_path, monkeypatch):
    import httpx
    import openai
    launch = Mock(side_effect=AssertionError("No OS process may start"))
    monkeypatch.setattr(subprocess, "Popen", launch)
    instance = guard(tmp_path)
    with instance.active():
        operations = [lambda: openai.OpenAI(api_key="EXPLICIT_UNUSED"), lambda: openai.AsyncOpenAI(api_key="EXPLICIT_UNUSED"),
                      lambda: httpx.Client(), lambda: httpx.AsyncClient(),
                      lambda: http.client.HTTPSConnection("example.invalid"),
                      lambda: socket.getaddrinfo("example.invalid", 443),
                      lambda: subprocess.run(["curl", "https://example.invalid"]),
                      lambda: subprocess.run(["lake", "update"]),
                      lambda: subprocess.Popen(["curl", "https://example.invalid"])]
        for operation in operations:
            with pytest.raises(runner.LocalOnlyViolation): operation()
    launch.assert_not_called()
    assert len(instance.violations) == len(operations)


def test_lean_transport_events_and_clean_subprocess_env(tmp_path, monkeypatch):
    # Simulates process lifecycle only. Never invokes Lean or another executable.
    source = tmp_path / "student_claim_checks" / "claim_refutation.lean"
    source.parent.mkdir()
    source.write_text("-- synthetic process fixture")
    seen = []

    class Process:
        def __init__(self, command, **kwargs):
            seen.append((command, kwargs))
            self.args, self.returncode = command, 0
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def communicate(self, *args, **kwargs): return ("", "")
        def poll(self): return self.returncode
        def wait(self): return self.returncode

    monkeypatch.setattr(subprocess, "Popen", Process)
    monkeypatch.setenv("OPENAI_API_KEY", "UNUSED_SENTINEL")
    instance = guard(tmp_path)
    with instance.active():
        subprocess.run(["lake", "env", "lean", str(source)], capture_output=True, text=True)
    assert seen[0][0] == ["/installed/lean", str(source)]
    assert "OPENAI_API_KEY" not in seen[0][1]["env"]
    assert seen[0][1]["env"]["LEAN_PATH"] == "/cached"
    assert len(instance.events) == 1
    event = instance.events[0]
    assert event["spawned"] and event["exit_code"] == 0 and event["proof_kind"] == "negation"
    assert event["scope"] == "student" and event["source_sha256"] == runner.file_sha(source)


def test_real_session_replaces_only_provider_and_io_boundaries(tmp_path, state, monkeypatch):
    import confia_lean_auditor.main as engine
    from confia_lean_auditor.rubric import secondary_adjudicator as secondary
    from confia_lean_auditor.lean.student_claim_checkers import ita2025f2q1 as checker
    old_directory = checker.CHECK_DIR
    remote = Mock(side_effect=AssertionError("Remote provider must not be invoked"))
    monkeypatch.setattr(secondary, "adjudicate", remote)
    response = raw_response()
    fake_engine = Mock(return_value=response)
    monkeypatch.setattr(engine, "execute_audit", fake_engine)
    runtime, _ = runner.prepare_runtime(tmp_path, state)
    case = dict(solution_id="fixture", problem_id=runner.PROBLEMS[0], text="synthetic", source_sha256="a" * 64)
    with runner.engine_session(runtime, state) as (execute, _):
        with pytest.raises(secondary.AdjudicationError) as exc:
            secondary.adjudicate({"pending": "fixture"})
        assert exc.value.code == "ADJUDICATOR_UNAVAILABLE"
        assert exc.value.diagnostics["attempts"] == 0
        assert execute(case) is response
        assert engine.repo_root() == runtime
        assert checker.CHECK_DIR.is_relative_to(runtime)
        with pytest.raises(runner.RunnerError, match=runner.UNSUPPORTED):
            execute(dict(case, problem_id="ITA2025Q1"))
    assert set(fake_engine.call_args.args[0].model_dump()) == {"problem_id", "solution"}
    assert checker.CHECK_DIR == old_directory
    remote.assert_not_called()


def test_measure_preserves_null_distinguishes_fatal_and_missing_events(tmp_path):
    raw = raw_response().model_dump(mode="json")
    case = dict(solution_id="fixture", problem_id=runner.PROBLEMS[0], text="fixture", source_sha256="a" * 64)
    row = runner.measure(case, raw, [])
    assert row["pipeline_valid"] and row["score"] is None and not row["numeric_score"]
    assert not runner.measure(case, raw, [], error="Exception")["pipeline_valid"]
    raw["lean_certificate"].update(status="verified", compiled=True, exit_code=0)
    row = runner.measure(case, raw, [])
    assert row["lean_attempts_reference"] == row["formal_verified_reference"] == 0
    assert row["instrumentation_gaps"] and not row["pipeline_valid"]
    raw["lean_certificate"].update(status="lean_timeout", compiled=False, exit_code=124)
    assert runner.measure(case, raw, [])["technical_errors"] == 1


def test_reference_events_not_microclaims_or_deterministic_inference(tmp_path):
    raw = raw_response().model_dump(mode="json")
    source = tmp_path / "reference.lean"
    source.write_text("-- reference fixture")
    raw["lean_certificate"].update(status="verified", compiled=True, exit_code=0, lean_file=str(source))
    raw["microclaims"] = [{"lean_status": "verified_by_lean"}] * 50
    event = dict(spawned=True, scope="reference", exit_code=0, source_sha256=runner.file_sha(source), proof_kind="positive")
    case = dict(solution_id="fixture", problem_id=runner.PROBLEMS[0], text="fixture", source_sha256="a" * 64)
    before = deepcopy(raw)
    row = runner.measure(case, raw, [event])
    assert raw == before
    assert row["formal_verified_reference"] == row["lean_attempts_reference"] == row["lean_success_reference"] == 1
    assert row["deterministic_verified"] == 0


def test_integrity_change_is_recorded_and_stops(dataset, tmp_path, state, monkeypatch):
    @contextmanager
    def session(*args):
        def execute(case):
            dataset.write_text("changed")
            return raw_response()
        yield execute, SimpleNamespace(events=[], violations=[])
    monkeypatch.setattr(runner, "engine_session", session)
    output = tmp_path / "out"
    with pytest.raises(runner.RunnerError, match="INPUT_INTEGRITY_CHANGED"):
        runner.run(args(dataset, output, "--run", "--limit", "1"))
    summary = json.loads((output / "summary.json").read_text())
    assert not summary["integrity"]["dataset_unchanged"] and summary["status"] == "FAILED"
    assert (output / "artifact_manifest.json").is_file()


@pytest.mark.parametrize("status", ["verified", "refuted", "unverified"])
def test_student_formal_counts_require_real_events_and_grounding(tmp_path, status):
    from dataclasses import asdict
    from confia_lean_auditor.student_claims.extract_f2q5_student_claims import extract_f2q5_student_claims
    text = "O primeiro algarismo é 6."
    claim = asdict(extract_f2q5_student_claims(text)[-1])
    positive, negative = tmp_path / "student.lean", tmp_path / "student_refutation.lean"
    positive.write_text("-- positive fixture")
    negative.write_text("-- negative fixture")
    check = dict(claim, status=status, compiled=status == "verified", lean_file=str(positive),
                 refutation_verified=status == "refuted", refutation_lean_file=str(negative))
    raw = raw_response().model_dump(mode="json")
    raw["problem_id"] = runner.PROBLEMS[1]
    raw["student_claim_checks"] = [check]
    raw["student_claims"] = [claim]
    case = dict(solution_id="fixture", problem_id=runner.PROBLEMS[1], text=text, source_sha256=runner.sha(text.encode()))
    events = [dict(spawned=True, scope="student", exit_code=0 if status == "verified" else 1,
                   source_sha256=runner.file_sha(positive), proof_kind="positive")]
    if status != "verified":
        events.append(dict(spawned=True, scope="student", exit_code=0 if status == "refuted" else 1,
                           source_sha256=runner.file_sha(negative), proof_kind="negation"))
    row = runner.measure(case, raw, events)
    assert row["formal_verified_student"] == int(status == "verified")
    assert row["refuted_formal"] == int(status == "refuted")
    assert row["technical_errors"] == 0 and row["pipeline_valid"]
    assert row["lean_attempts_student"] == len(events)
    assert row["lean_failures"] == sum(e["exit_code"] != 0 for e in events)
    if status != "unverified":
        check["grounding"]["source_sha256"] = "0" * 64
        bad = runner.measure(case, raw, events)
        assert not bad["pipeline_valid"] and bad["instrumentation_gaps"]
        assert bad["formal_verified_student"] == bad["refuted_formal"] == 0


def test_numeric_zero_is_not_null_and_deterministic_is_explicit():
    raw = raw_response().model_dump(mode="json")
    for obj in (raw, raw["rubric_assessment"]):
        obj.update(score=0, needs_review=False, unscorable_reason=None)
    item = raw["rubric_assessment"]["items"][0]
    item.update(points=0, suggested_points=0, mathematical_status="refuted", scoring_basis="first_pass")
    case = dict(solution_id="fixture", problem_id=runner.PROBLEMS[0], text="fixture", source_sha256="a" * 64)
    row = runner.measure(case, raw, [])
    assert row["pipeline_valid"] and row["numeric_score"] and row["score"] == 0
    assert row["refuted_deterministic"] == 0  # A criterion zero does not identify its proof mechanism.
    item.update(mathematical_status="supported", positive_evidence=dict(supported=True, verification_type="deterministic_check"))
    assert runner.measure(case, raw, [])["deterministic_verified"] == 1
    item["positive_evidence"]["verification_type"] = "grounded_text"
    assert runner.measure(case, raw, [])["deterministic_verified"] == 0


@pytest.mark.parametrize("mutation", ["remote", "bad_total", "wrong_problem", "wrong_null_reason"])
def test_invalid_scoring_contract_is_not_valid(mutation):
    raw = raw_response().model_dump(mode="json")
    case = dict(solution_id="fixture", problem_id=runner.PROBLEMS[0], text="fixture", source_sha256="a" * 64)
    if mutation == "remote": raw["rubric_assessment"]["secondary_adjudication"]["attempts"] = 1
    if mutation == "bad_total": raw["score"] = 10
    if mutation == "wrong_problem": raw["problem_id"] = "ITA2025Q1"
    if mutation == "wrong_null_reason": raw["unscorable_reason"] = "ADJUDICATOR_TIMEOUT"
    assert not runner.measure(case, raw, [])["pipeline_valid"]


def test_swallowed_guard_violation_still_aborts_batch(dataset, tmp_path, state, monkeypatch):
    calls = []

    @contextmanager
    def session(*args):
        guard = SimpleNamespace(events=[], violations=[])
        def execute(case):
            calls.append(case["solution_id"])
            guard.violations.append("BLOCKED_TEST_OPERATION")
            return raw_response()
        yield execute, guard

    monkeypatch.setattr(runner, "engine_session", session)
    output = tmp_path / "out"
    with pytest.raises(runner.RunnerError, match="LocalOnlyViolation"):
        runner.run(args(dataset, output, "--run"))
    assert len(calls) == 1
    result = json.loads((output / "checkpoints" / (calls[0] + ".json")).read_text())
    assert not result["pipeline_valid"]
    assert json.loads((output / "summary.json").read_text())["status"] == "FAILED"


def test_missing_inputs_fail_integrity_without_losing_report(dataset, state):
    _, source = runner.load_dataset(dataset)
    dataset.unlink()
    assert runner.verify_inputs(source, state)["dataset_unchanged"] is False


def test_local_cache_requires_proof_dependencies_not_unused_lake_tooling(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    (tmp_path / "lake-manifest.json").write_text(json.dumps({"packages": [{"name": "mathlib"}, {"name": "Cli"}]}))
    mathlib = tmp_path / ".lake/packages/mathlib/.lake/build/lib/lean/Mathlib.olean"
    mathlib.parent.mkdir(parents=True)
    mathlib.write_bytes(b"structural fixture only; never executed")
    for q in runner.PROBLEMS:
        p = tmp_path / ".lake/build/lib/lean/ConfiaLeanAuditor/Problems" / q / "Statement.olean"
        p.parent.mkdir(parents=True)
        p.write_bytes(b"structural fixture only; never executed")
    assert str(mathlib.parent) in runner.local_lean_path()
    mathlib.unlink()
    with pytest.raises(runner.RunnerError, match="LOCAL_LEAN_CACHE_MISSING"):
        runner.local_lean_path()
