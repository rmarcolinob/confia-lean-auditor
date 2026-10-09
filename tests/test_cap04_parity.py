"""Bridge contract, controlled semantics, real availability and witness integrity."""
from collections import Counter
from copy import deepcopy
from importlib import import_module
from pathlib import Path
import hashlib
import json
import subprocess
import time

from fastapi.testclient import TestClient
import pytest

import confia_lean_auditor.main as main
import confia_lean_auditor.lean.formal_step_evaluator as formal
from confia_lean_auditor.core.schemas import (
    AuditResponse, ClaimExtraction, FormalStepResult, LeanCertificate,
    RubricAssessment, RubricItemResult,
)
from confia_lean_auditor.lean.run_lean import run_lean_file
from confia_lean_auditor.lean.verification import verification_state
from confia_lean_auditor.submission_audits.artifacts import capture_manifest
from audit_contract import assert_score_contract
from test_cap04_global_semantics import central
from test_submission_audits import source, accept, execute, result
from test_submissions import payload


ROOT = Path(__file__).resolve().parents[1]
PROBLEM = "ITA2025F2Q1"
CORRECT_SHA256 = "121558291e4b28600f9a8431084411cb89a1d17a0fe83fe264ef390f982dbda1"
STATE_FIELDS = {"status", "compiled", "exit_code", "failure_category", "refutation_verified"}
DIAGNOSTIC_FIELDS = {"stdout", "stderr", "refutation_stdout", "refutation_stderr",
                     "lean_file", "refutation_lean_file"}


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def canonical_hash(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode("utf-8"))


@pytest.fixture
def parity_pipeline(tmp_path, monkeypatch):
    (tmp_path / "problems").symlink_to(ROOT / "problems", target_is_directory=True)
    monkeypatch.setenv("CONFIA_ENABLE_LLM_FORMAL_STEPS", "0")
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_SUBMISSION_AUDITS_DIR", str(tmp_path / "audits"))
    monkeypatch.setattr(main, "repo_root", lambda: tmp_path)
    # Isolate writes while retaining the actual project cwd and original limits.
    def lean(repo_root, lean_file, timeout_seconds=30):
        return run_lean_file(ROOT, lean_file, timeout_seconds)
    monkeypatch.setattr(main, "run_lean_file", lean)
    monkeypatch.setattr(formal, "run_lean_file", lean)
    for suffix in ("student_claim_checker", "student_claim_checkers.ita2025f2q1"):
        module = import_module("confia_lean_auditor.lean." + suffix)
        monkeypatch.setattr(module, "CHECK_DIR", tmp_path / "checks")
    return TestClient(main.app), monkeypatch


@pytest.fixture
def controlled_executor(parity_pipeline):
    _, monkeypatch = parity_pipeline
    state = {"mode": "VERIFIED", "calls": []}
    def runner(command, **kwargs):
        assert command[:3] == ["lake", "env", "lean"]
        file = Path(command[3])
        assert Path(kwargs["cwd"]) == ROOT
        if file.parent.name == "formal_steps" or file.name == "Attempt.lean":
            assert kwargs["timeout"] == 30
        else:
            assert 0 < kwargs["timeout"] <= 90
        state["calls"].append(str(file))
        mode = state["mode"]
        if mode == "TECHNICAL_ERROR" or (mode == "S1_TIMEOUT" and file.stem == "f2q1_s1_power_reductions"):
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        if mode == "PROCESS_ERROR":
            raise OSError("executor unavailable")
        if mode == "MISSING_MODULE":
            return subprocess.CompletedProcess(command, 1, "unknown module prefix Mathlib", "")
        if mode == "UNKNOWN_IDENTIFIER":
            return subprocess.CompletedProcess(command, 1, "unknown identifier x", "")
        if mode in {"VERIFIED", "S1_TIMEOUT"} or (mode == "REFUTED" and file.stem.endswith("_refutation")):
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 1, "unsolved goals", "")
    monkeypatch.setattr(subprocess, "run", runner)
    return state


def accepted_source(client, problem, solution):
    request_payload = payload()
    snapshot = json.loads(request_payload["snapshot_json"])
    snapshot["problem_id"] = problem
    request_payload["snapshot_json"] = json.dumps(snapshot)
    sid, revision = source(client, values=[dict(segment_id="exact", page_index=0,
        order=0, kind="mixed", text=solution)], request_payload=request_payload)
    return sid, accept(client, sid, revision)


def execute_pair(parity_pipeline, problem, solution, before_bridge=None):
    client, monkeypatch = parity_pipeline
    engine, runner = main.execute_audit, subprocess.run
    state = {"route": None, "entries": [], "results": {}, "subprocesses": []}
    def observed_engine(request):
        state["entries"].append((state["route"], engine, request.model_dump(), request.solution.encode("utf-8")))
        value = engine(request)
        state["results"][state["route"]] = value.model_dump(mode="json")
        return value
    def observed_runner(command, **kwargs):
        file = Path(command[3])
        entry = dict(route=state["route"], file=str(file), source_sha256=sha256(file.read_bytes()),
                     timeout_seconds=kwargs["timeout"], runtime_failure=False)
        started = time.perf_counter()
        try:
            value = runner(command, **kwargs)
            entry["exit_code"] = value.returncode
            diagnostic = ((value.stdout or "") + "\n" + (value.stderr or "")).lower()
            entry["runtime_failure"] = value.returncode != 0 and any(
                text in diagnostic for text in ("unknown module", "object file", "no such file"))
            return value
        except (subprocess.TimeoutExpired, OSError) as error:
            entry.update(runtime_failure=True, exit_code=124 if isinstance(error, subprocess.TimeoutExpired) else -1)
            raise
        finally:
            entry["duration_seconds"] = time.perf_counter() - started
            state["subprocesses"].append(entry)
    monkeypatch.setattr(main, "execute_audit", observed_engine)
    monkeypatch.setattr(subprocess, "run", observed_runner)
    sid, request = accepted_source(client, problem, solution)
    state["route"] = "textual"
    textual = client.post("/audit", json=dict(problem_id=problem, solution=solution))
    assert textual.status_code == 200, textual.text
    if before_bridge:
        before_bridge()
    state["route"] = "bridge"
    response = execute(client, sid, request)
    assert response.status_code == 200, response.text
    run = response.json()
    assert Counter(entry[0] for entry in state["entries"]) == {"textual": 1, "bridge": 1}
    for _, called_engine, arguments, raw in state["entries"]:
        assert called_engine is engine
        assert arguments == dict(problem_id=problem, solution=solution)
        assert raw == solution.encode("utf-8")
        assert sha256(raw) == sha256(solution.encode("utf-8"))
    assert textual.json() == state["results"]["textual"]
    assert run["result"] == state["results"]["bridge"]
    assert_bridge_integrity(client, run, problem, solution)
    return textual.json(), run["result"], state


def assert_bridge_integrity(client, run, problem, solution):
    assert run["status"] == "COMPLETED", run
    assert run["problem_id"] == run["source"]["problem_id"] == problem
    assert run["source"]["solution_text"] == solution
    assert run["source_hash"] == canonical_hash({k: v for k, v in run["source"].items() if k != "source_hash"})
    assert run["result_sha256"] == canonical_hash(run["result"])
    assert run["artifact_manifest_sha256"] == canonical_hash(run["required_artifacts"])
    assert [item.model_dump(mode="json") for item in capture_manifest(AuditResponse.model_validate(run["result"]))] == run["required_artifacts"]
    response = client.get(f'/submission-audits/{run["audit_run_id"]}')
    assert response.status_code == 200, response.text
    assert response.json() == run


def assert_execution_invariants(data, solution, *, pipeline=True):
    assert_score_contract(data)
    assert Path(data["artifact_dir"], "solution.txt").read_bytes() == solution.encode("utf-8")
    assert json.loads(Path(data["artifact_dir"], "audit.json").read_text()) == data
    assert capture_manifest(AuditResponse.model_validate(data))
    refuted = []
    for check in data["student_claim_checks"]:
        if check["status"] == "technical_error":
            assert not check["compiled"] and not check["refutation_verified"]
        if check["status"] == "refuted":
            assert check["refutation_verified"] is True
            witness = Path(check["refutation_lean_file"])
            assert f'¬ ({check["lean_statement"]})' in witness.read_text()
            refuted.append(check)
        if check["status"] == "verified":
            assert check["compiled"] is True
    for proof in [data["lean_certificate"], *data["formal_steps"]]:
        if proof["status"] == "verified":
            assert proof["compiled"] is True and proof["exit_code"] == 0
    if not refuted:
        assert data["verdict"] != "incorreto"
        assert all(item["points"] != 0 and item["mathematical_status"] != "refuted"
                   for item in data["rubric_assessment"]["items"])
    if not pipeline:
        return
    # A technical mismatch cannot excuse unrelated changes to derived decisions.
    # Reassess the observed proof profile without invoking Lean again.
    assets = main.validate_problem_assets(ROOT / "problems" / data["problem_id"], data["problem_id"])
    extraction = ClaimExtraction.model_validate(data["extracted_claims"])
    certificate = LeanCertificate.model_validate(data["lean_certificate"])
    steps = [FormalStepResult.model_validate(value) for value in data["formal_steps"]]
    microclaims = main.evaluate_microclaims(ROOT, data["problem_id"], extraction, certificate,
        certificate.generated_theorems, steps, assets.microclaims)
    assert [value.model_dump() for value in microclaims] == data["microclaims"]
    rubric = main.evaluate_rubric(ROOT, data["problem_id"], extraction, microclaims, assets.rubric)
    rubric = main.apply_student_claim_adjustments(rubric=rubric, problem_id=data["problem_id"],
                                                 student_claim_checks=data["student_claim_checks"])
    assert rubric.model_dump() == data["rubric_assessment"]
    report = main.build_pedagogical_report(score=rubric.score, max_score=rubric.max_score,
        verdict=main.verdict_from_score(rubric.score, rubric.max_score), rubric=rubric,
        student_claims=data["student_claims"], student_claim_checks=data["student_claim_checks"],
        microclaims=microclaims, artifact_dir=data["artifact_dir"], verification_status=verification_state(certificate))
    assert report.model_dump() == data["pedagogical_report"]
    assert data["verdict"] == report.verdict
    assert main.build_feedback(rubric, certificate, microclaims) == data["feedback"]


def obligations(data):
    values = [("certificate", {"id": "principal", **data["lean_certificate"]})]
    values += [("formal_step", value) for value in data["formal_steps"]]
    values += [("student_check", value) for value in data["student_claim_checks"]]
    indexed = {(kind, value["id"]): value for kind, value in values}
    assert len(indexed) == len(values), "duplicate formal obligation"
    return indexed


def coverage(data):
    return dict(obligations={f"{kind}:{identifier}": {key: value.get(key) for key in STATE_FIELDS}
                             for (kind, identifier), value in obligations(data).items()},
        generated_theorems=data["lean_certificate"]["generated_theorems"],
        microclaims=[{key: value[key] for key in ("id", "lean_status", "verification_status",
            "required_formal_step_types", "depends_on_microclaim_ids", "dependencies_verified",
            "formal_steps_verified")} for value in data["microclaims"]])


def compare_pair(textual, bridge, state, solution):
    if coverage(textual) == coverage(bridge):
        assert central(textual) == central(bridge), "equivalent coverage with different central semantics"
        return "COMPARABLE_EQUAL"
    assert textual["problem_id"] == bridge["problem_id"]
    assert textual["extracted_claims"] == bridge["extracted_claims"]
    assert textual["student_claims"] == bridge["student_claims"]
    left, right = obligations(textual), obligations(bridge)
    assert left.keys() == right.keys(), "different formal obligations"
    changed = []
    for key in left:
        before, after = left[key], right[key]
        ignored = STATE_FIELDS | DIAGNOSTIC_FIELDS | {"generated_theorems"}
        assert {k: v for k, v in before.items() if k not in ignored} == {k: v for k, v in after.items() if k not in ignored}
        if key[0] != "certificate":
            for field in ("lean_file",):
                if before.get(field) and after.get(field):
                    assert Path(before[field]).read_bytes() == Path(after[field]).read_bytes()
        if {k: before.get(k) for k in STATE_FIELDS} == {k: after.get(k) for k in STATE_FIELDS}:
            continue
        changed.append(key)
        actual_runtime_failure = False
        for route, value in (("textual", before), ("bridge", after)):
            if value.get("compiled") or value.get("refutation_verified"):
                continue
            paths = {value.get("lean_file"), value.get("refutation_lean_file")}
            actual_runtime_failure |= any(entry["route"] == route and entry["file"] in paths
                and entry["runtime_failure"] for entry in state["subprocesses"])
        assert actual_runtime_failure, f"non-runtime coverage difference: {key}"
    assert changed, "coverage changed without an observed runtime failure"
    if not any(kind == "formal_step" for kind, _ in changed):
        assert textual["lean_certificate"]["generated_theorems"] == bridge["lean_certificate"]["generated_theorems"]
        assert Path(textual["lean_certificate"]["lean_file"]).read_bytes() == Path(bridge["lean_certificate"]["lean_file"]).read_bytes()
    for data in (textual, bridge):
        assert_execution_invariants(data, solution)
    return "NOT_COMPARABLE_TECHNICAL_AVAILABILITY"


@pytest.mark.parametrize("score", [None, 4.0])
def test_bridge_contract_parity(parity_pipeline, score):
    _, monkeypatch = parity_pipeline
    solution = (ROOT / "problems" / PROBLEM / "examples/correct_solution.txt").read_text()
    assert len(solution.encode("utf-8")) == 487 and len(solution) == 482
    assert sha256(solution.encode("utf-8")) == CORRECT_SHA256
    response = result(PROBLEM)
    response.rubric_assessment = RubricAssessment(score=score, max_score=10,
        assessment_status="indeterminate" if score is None else "complete",
        evaluated_score=score or 0, evaluated_max_score=0 if score is None else 10,
        items=[RubricItemResult(id="contract", description="Contrato", detected=True,
            points=score, max_points=10, mathematical_status="indeterminate" if score is None else "supported")])
    response.lean_certificate.status = "lean_timeout" if score is None else "verified"
    response.lean_certificate.compiled = score is not None
    response.lean_certificate.exit_code = 124 if score is None else 0
    response.score, response.verdict = score, main.verdict_from_score(score, 10)
    response.pedagogical_report = main.build_pedagogical_report(score=score, max_score=10,
        verdict=response.verdict, rubric=response.rubric_assessment, student_claims=[],
        student_claim_checks=[], microclaims=[], artifact_dir=response.artifact_dir,
        verification_status=verification_state(response.lean_certificate))
    directory = Path(response.artifact_dir)
    (directory / "solution.txt").write_text(solution)
    (directory / "Attempt.lean").write_text("theorem contract_fixture : True := by trivial\n")
    (directory / "audit.json").write_text(response.model_dump_json())
    monkeypatch.setattr(main, "execute_audit", lambda request: response.model_copy(deep=True))
    def no_lean(*args, **kwargs):
        pytest.fail("contract parity must not execute Lean")
    monkeypatch.setattr(subprocess, "run", no_lean)
    textual, bridge, state = execute_pair(parity_pipeline, PROBLEM, solution)
    assert state["subprocesses"] == []
    assert textual == bridge == response.model_dump(mode="json")
    for data in (textual, bridge):
        assert_execution_invariants(data, solution, pipeline=False)


@pytest.mark.parametrize("mode", ["VERIFIED", "REFUTED", "UNVERIFIED", "TECHNICAL_ERROR", "MISSING_MODULE", "PROCESS_ERROR"])
def test_controlled_engine_semantic_parity(parity_pipeline, controlled_executor, mode):
    controlled_executor["mode"] = mode
    example = "wrong_answer.txt" if mode == "REFUTED" else "correct_solution.txt"
    solution = (ROOT / "problems" / PROBLEM / "examples" / example).read_text()
    textual, bridge, state = execute_pair(parity_pipeline, PROBLEM, solution)
    for data in (textual, bridge):
        assert_execution_invariants(data, solution)
        checks = data["student_claim_checks"]
        expected = mode.lower() if mode in {"VERIFIED", "REFUTED", "UNVERIFIED"} else "technical_error"
        assert checks and all(check["status"] == expected for check in checks)
        if mode == "VERIFIED":
            assert data["score"] == 10 and data["verdict"] == "correto"
        else:
            assert data["score"] is None and data["verdict"] == "inconclusivo"
    assert coverage(textual) == coverage(bridge)
    assert compare_pair(textual, bridge, state, solution) == "COMPARABLE_EQUAL"


@pytest.mark.parametrize("problem,example", [(PROBLEM, "correct_solution.txt"), ("ITA2025F2Q8", "wrong_answer.txt")])
def test_real_engine_smoke(parity_pipeline, problem, example, record_property):
    solution = (ROOT / "problems" / problem / "examples" / example).read_text()
    textual, bridge, state = execute_pair(parity_pipeline, problem, solution)
    for data in (textual, bridge):
        assert_execution_invariants(data, solution)
    classification = compare_pair(textual, bridge, state, solution)
    record_property("parity_classification", classification)
    record_property("textual_coverage", json.dumps(coverage(textual), sort_keys=True))
    record_property("bridge_coverage", json.dumps(coverage(bridge), sort_keys=True))
    record_property("lean_executions", json.dumps(state["subprocesses"]))
    if classification != "COMPARABLE_EQUAL":
        pytest.skip("ENG-LEAN-01: rodada NÃO COMPARÁVEL; invariantes individuais verificados, paridade não aprovada")


@pytest.mark.parametrize("kind", ["formal_step", "refutation", "certificate"])
@pytest.mark.parametrize("change", ["removed", "changed"])
def test_formal_witness_integrity_independent(parity_pipeline, controlled_executor, kind, change):
    client, monkeypatch = parity_pipeline
    controlled_executor["mode"] = "REFUTED" if kind == "refutation" else "VERIFIED"
    example = "wrong_answer.txt" if kind == "refutation" else "correct_solution.txt"
    solution = (ROOT / "problems" / PROBLEM / "examples" / example).read_text()
    engine, calls = main.execute_audit, []
    def counted(request):
        calls.append(request)
        return engine(request)
    monkeypatch.setattr(main, "execute_audit", counted)
    sid, request = accepted_source(client, PROBLEM, solution)
    response = execute(client, sid, request)
    assert response.status_code == 200, response.text
    run = response.json()
    assert_bridge_integrity(client, run, PROBLEM, solution)
    assert_execution_invariants(run["result"], solution)
    witness = Path(next(item["file"] for item in run["required_artifacts"] if item["artifact_type"] == kind))
    witness.unlink() if change == "removed" else witness.write_bytes(b"altered witness")
    assert client.get(f'/submission-audits/{run["audit_run_id"]}').status_code == 409
    assert client.get(f'/submissions/{sid}/audits').status_code == 409
    assert execute(client, sid, request).status_code == 409
    assert len(calls) == 1


def different_availability_pair(parity_pipeline, controlled_executor):
    solution = (ROOT / "problems" / PROBLEM / "examples/correct_solution.txt").read_text()
    textual, bridge, state = execute_pair(parity_pipeline, PROBLEM, solution,
        before_bridge=lambda: controlled_executor.update(mode="S1_TIMEOUT"))
    return textual, bridge, state, solution


def test_real_parity_guard_records_only_observed_runtime_difference(parity_pipeline, controlled_executor):
    textual, bridge, state, solution = different_availability_pair(parity_pipeline, controlled_executor)
    assert coverage(textual) != coverage(bridge) and central(textual) != central(bridge)
    assert compare_pair(textual, bridge, state, solution) == "NOT_COMPARABLE_TECHNICAL_AVAILABILITY"
    with pytest.raises(AssertionError, match="non-runtime coverage difference"):
        compare_pair(textual, bridge, {**state, "subprocesses": []}, solution)


def test_real_parity_guard_fails_semantic_difference_with_equivalent_coverage(parity_pipeline, controlled_executor):
    solution = (ROOT / "problems" / PROBLEM / "examples/correct_solution.txt").read_text()
    textual, bridge, state = execute_pair(parity_pipeline, PROBLEM, solution)
    altered = deepcopy(bridge)
    altered["feedback"] += " route-specific alteration"
    assert coverage(textual) == coverage(altered)
    with pytest.raises(AssertionError, match="equivalent coverage"):
        compare_pair(textual, altered, state, solution)


@pytest.mark.parametrize("mode", ["UNVERIFIED", "REFUTED", "UNKNOWN_IDENTIFIER"])
def test_real_parity_guard_does_not_skip_non_runtime_failures(parity_pipeline, controlled_executor, mode):
    solution = (ROOT / "problems" / PROBLEM / "examples/correct_solution.txt").read_text()
    textual, bridge, state = execute_pair(parity_pipeline, PROBLEM, solution,
        before_bridge=lambda: controlled_executor.update(mode=mode))
    with pytest.raises(AssertionError, match="non-runtime coverage difference"):
        compare_pair(textual, bridge, state, solution)


@pytest.mark.parametrize("field", ["feedback", "report", "rubric", "claim", "formal_step", "student_check"])
def test_real_parity_guard_does_not_hide_other_changes_during_timeout(parity_pipeline, controlled_executor, field):
    textual, bridge, state, solution = different_availability_pair(parity_pipeline, controlled_executor)
    altered = deepcopy(bridge)
    if field == "feedback":
        altered["feedback"] += " unsupported change"
    elif field == "report":
        altered["pedagogical_report"]["summary"] = "Invented mathematical conclusion"
    elif field == "rubric":
        altered["rubric_assessment"]["items"][0]["evidence"] = "invented evidence"
    elif field == "claim":
        altered["extracted_claims"]["claims"][0]["text"] = "changed input claim"
    else:
        value = altered["formal_steps"][1] if field == "formal_step" else altered["student_claim_checks"][0]
        value.update(status="unverified", compiled=False, exit_code=1)
    # Simulate an engine that exports its own wrong decision consistently;
    # rejection must not depend only on a mismatching audit.json.
    Path(altered["artifact_dir"], "audit.json").write_text(json.dumps(altered))
    with pytest.raises(AssertionError):
        compare_pair(textual, altered, state, solution)
