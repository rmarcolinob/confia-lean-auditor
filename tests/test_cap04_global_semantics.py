"""P1: unavailable verification never becomes a mathematical zero or verdict."""
from importlib import import_module
from pathlib import Path
import json
import subprocess

from fastapi.testclient import TestClient
import pytest

import confia_lean_auditor.main as main
import confia_lean_auditor.lean.formal_step_evaluator as formal
from confia_lean_auditor.core.schemas import FormalStepResult, RubricAssessment
from confia_lean_auditor.core.problem_assets import RubricConfig
from confia_lean_auditor.core.schemas import ClaimExtraction
from confia_lean_auditor.rubric.rubric_evaluator import evaluate_rubric
from confia_lean_auditor.lean.verification import verification_state
from confia_lean_auditor.reports.report_builder import build_pedagogical_report
from test_submission_audits import source, accept, execute, result, setup
from test_submissions import payload


ROOT = Path(__file__).resolve().parents[1]
FAILURES = [
    ("lean_timeout", "timeout", "technical_error"),
    ("lean_error", "unknown module prefix Mathlib", "technical_error"),
    ("lean_error_unknown_identifier", "unknown identifier x", "technical_error"),
    ("lean_error_unsolved_goals", "unsolved goals", "partial"),
]


def central(value):
    if isinstance(value, dict):
        return {key: central(item) for key, item in value.items() if key not in {
            "artifact_dir", "lean_file", "refutation_lean_file", "stdout", "stderr",
            "refutation_stdout", "refutation_stderr"}}
    if isinstance(value, list):
        return [central(item) for item in value]
    return value


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    (tmp_path / "problems").symlink_to(ROOT / "problems", target_is_directory=True)
    monkeypatch.setattr(main, "repo_root", lambda: tmp_path)
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_SUBMISSION_AUDITS_DIR", str(tmp_path / "audits"))
    return TestClient(main.app), tmp_path, monkeypatch


def compiler(pipeline, number, status, diagnostic, *, independent_steps=False):
    client, tmp_path, monkeypatch = pipeline
    module = import_module("confia_lean_auditor.lean." + (
        "student_claim_checker" if number == 8 else f"student_claim_checkers.ita2025f2q{number}"))
    monkeypatch.setattr(module, "CHECK_DIR", tmp_path / "checks")
    raw = dict(status=status, compiled=False, exit_code=1, uses_forbidden_token=False,
               forbidden_tokens_found=[], stdout=diagnostic, stderr="")
    monkeypatch.setattr(main, "run_lean_file", lambda *args, **kwargs: dict(raw))
    monkeypatch.setattr(formal, "run_lean_file", lambda *args, **kwargs: dict(raw) if not independent_steps else {
        **raw, "status": "verified", "compiled": True, "exit_code": 0, "stdout": ""})
    monkeypatch.setattr(module, "_run_lean_file", lambda *args, **kwargs:
                        subprocess.CompletedProcess([], 1, diagnostic, ""))
    return client


@pytest.mark.parametrize("number", [1, 3, 5, 6, 8])
@pytest.mark.parametrize("status,diagnostic,availability", FAILURES)
def test_correct_f2_with_all_verification_unavailable_is_inconclusive_on_both_routes(
        pipeline, number, status, diagnostic, availability):
    client = compiler(pipeline, number, status, diagnostic)
    problem = f"ITA2025F2Q{number}"
    solution = (ROOT / "problems" / problem / "examples/correct_solution.txt").read_text()
    textual = client.post("/audit", json={"problem_id": problem, "solution": solution})
    assert textual.status_code == 200, textual.text
    data = textual.json()
    assert data["score"] is None and data["verdict"] == "inconclusivo"
    rubric = data["rubric_assessment"]
    assert rubric["assessment_status"] in {"partial", "indeterminate"}
    assert any(item["points"] is None for item in rubric["items"])
    assert not any(item["points"] == 0 or item["student_check_adjusted"] for item in rubric["items"])
    assert all(item["mathematical_status"] != "refuted" for item in rubric["items"])
    report = data["pedagogical_report"]
    assert report["verification_status"] == availability
    assert "indisponível" in report["summary"] if availability == "technical_error" else "não foi concluída" in report["summary"]
    assert "conferidas" not in report["summary"]
    request_payload = payload()
    snapshot = json.loads(request_payload["snapshot_json"])
    snapshot["problem_id"] = problem
    request_payload["snapshot_json"] = json.dumps(snapshot)
    sid, rev = source(client, values=[dict(segment_id="exact", page_index=0, order=0,
        kind="mixed", text=solution)], request_payload=request_payload)
    run = execute(client, sid, accept(client, sid, rev)).json()
    assert run["status"] == "COMPLETED", run
    assert central(data) == central(run["result"])
    assert run["required_artifacts"] and run["artifact_manifest_sha256"]


def test_independent_verified_steps_remain_evidence_when_principal_attempt_is_unavailable(pipeline):
    client = compiler(pipeline, 3, "lean_error_unknown_identifier", "unknown identifier x", independent_steps=True)
    solution = (ROOT / "problems/ITA2025F2Q3/examples/correct_solution.txt").read_text()
    data = client.post("/audit", json={"problem_id": "ITA2025F2Q3", "solution": solution}).json()
    assert data["score"] == 10
    assert all(item["mathematical_status"] == "supported" for item in data["rubric_assessment"]["items"])
    assert "Parte das evidências" in data["pedagogical_report"]["summary"]
    assert "indisponível" in data["pedagogical_report"]["summary"]


@pytest.mark.parametrize("exception", [subprocess.TimeoutExpired("lean", 30, output=b"partial diagnostic"), OSError("missing process")])
def test_actual_global_compiler_wrapper_preserves_unavailable_semantics(pipeline, exception):
    client, tmp_path, monkeypatch = pipeline
    module = import_module("confia_lean_auditor.lean.student_claim_checkers.ita2025f2q3")
    monkeypatch.setattr(module, "CHECK_DIR", tmp_path / "checks")
    def unavailable(*args, **kwargs):
        raise exception
    monkeypatch.setattr(subprocess, "run", unavailable)
    solution = (ROOT / "problems/ITA2025F2Q3/examples/correct_solution.txt").read_text()
    response = client.post("/audit", json={"problem_id": "ITA2025F2Q3", "solution": solution})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["score"] is None and data["verdict"] == "inconclusivo"
    assert data["pedagogical_report"]["verification_status"] == "technical_error"


def test_missing_required_microclaim_is_pending_not_zero(tmp_path):
    rubric = evaluate_rubric(tmp_path, "test", ClaimExtraction(problem_id="test", claims=[
        dict(id="claim", type="answer", text="x=1", evidence="x=1")]), microclaims=[],
        rubric_config=RubricConfig(problem_id="test", max_score=10, items=[
            dict(id="answer", description="Resposta", claim_type="answer", points=10,
                 required_microclaim_ids=["missing"])]))
    assert rubric.score is None and rubric.items[0].points is None
    assert rubric.evaluated_max_score == 0 and rubric.items[0].mathematical_status == "indeterminate"


@pytest.mark.parametrize("status,expected", [("lean_error_unsolved_goals", "partial"),
    ("lean_error_synthesis_failed", "partial"), ("lean_timeout", "technical_error"),
    ("lean_error_unknown_identifier", "technical_error")])
def test_global_status_remains_meaningful_without_diagnostic_output(status, expected):
    assert verification_state(dict(status=status, compiled=False, exit_code=1)) == expected


@pytest.mark.parametrize("statuses", [["unverified"], ["technical_error"], ["verified", "technical_error"]])
def test_high_score_cannot_supply_missing_evidence_in_summary(statuses):
    checks = [dict(id=str(i), status=status, raw_text="x=1", compiled=status == "verified")
              for i, status in enumerate(statuses)]
    report = build_pedagogical_report(score=10, max_score=10, verdict="correto",
        rubric=RubricAssessment(score=10, max_score=10, items=[]), student_claims=[],
        student_claim_checks=checks, microclaims=[], artifact_dir=None)
    assert report.verdict == "inconclusivo" and report.score is None
    if "verified" not in statuses:
        assert "conferid" not in report.summary and "verificada" not in report.summary
        assert not any(item.result == "conferida" for item in report.evidence_items)
    else:
        assert "Parte das evidências pôde ser verificada" in report.summary
    if "technical_error" in statuses:
        assert "indisponível" in report.summary
    assert "solução correta" not in report.summary and "solução incorreta" not in report.summary


def step(path, status="verified"):
    return FormalStepResult(id="step", type="formal", description="Passo", evidence="x=x",
        lhs="x", rhs="x", lean_method="rfl", lean_file=str(path), status=status,
        compiled=status == "verified", exit_code=0 if status == "verified" else 1)


@pytest.mark.parametrize("change", ["removed", "changed_same_size", "changed_size", "symlink"])
def test_verified_formal_step_witness_changes_block_read_and_retry(setup, monkeypatch, change):
    client, _ = setup
    def engine(request):
        data = result(request.problem_id)
        witness = Path(data.artifact_dir) / "formal_steps/step.lean"
        witness.parent.mkdir()
        witness.write_text("theorem x : True := by trivial")
        data.formal_steps = [step(witness)]
        return data
    monkeypatch.setattr(main, "execute_audit", engine)
    sid, rev = source(client)
    request = accept(client, sid, rev)
    run = execute(client, sid, request).json()
    assert run["status"] == "COMPLETED"
    reference = next(item for item in run["required_artifacts"] if item["artifact_type"] == "formal_step")
    witness = Path(reference["file"])
    original = witness.read_bytes()
    if change == "removed":
        witness.unlink()
    elif change == "changed_same_size":
        witness.write_bytes(b"X" + original[1:])
    elif change == "changed_size":
        witness.write_bytes(original + b"\n-- changed")
    else:
        target = witness.with_suffix(".copy")
        target.write_bytes(original)
        witness.unlink()
        witness.symlink_to(target)
    assert client.get(f'/submission-audits/{run["audit_run_id"]}').status_code == 409
    assert client.get(f'/submissions/{sid}/audits').status_code == 409
    assert execute(client, sid, request).status_code == 409


@pytest.mark.parametrize("status", ["verified", "unverified", "textual", "lean_timeout"])
def test_only_verified_formal_steps_require_witness_at_publication(setup, monkeypatch, status):
    client, _ = setup
    def engine(request):
        data = result(request.problem_id)
        data.formal_steps = [step(Path(data.artifact_dir) / "missing.lean", status)]
        return data
    monkeypatch.setattr(main, "execute_audit", engine)
    sid, rev = source(client)
    run = execute(client, sid, accept(client, sid, rev)).json()
    assert run["status"] == ("FAILED" if status == "verified" else "COMPLETED")
    if run["status"] == "COMPLETED":
        assert not any(item["artifact_type"] == "formal_step" for item in run["required_artifacts"])


@pytest.mark.parametrize("outside", [False, True])
def test_verified_witness_cannot_escape_run_directory(setup, monkeypatch, tmp_path, outside):
    client, _ = setup
    def engine(request):
        data = result(request.problem_id)
        witness = tmp_path / "outside.lean"
        witness.write_text("theorem x : True := by trivial")
        if not outside:
            link = Path(data.artifact_dir) / "linked"
            link.symlink_to(tmp_path, target_is_directory=True)
            witness = link / "outside.lean"
        data.formal_steps = [step(witness)]
        return data
    monkeypatch.setattr(main, "execute_audit", engine)
    sid, rev = source(client)
    assert execute(client, sid, accept(client, sid, rev)).json()["status"] == "FAILED"


@pytest.mark.parametrize("kind", ["student_proof", "refutation", "certificate", "export"])
@pytest.mark.parametrize("change", ["removed", "changed"])
def test_all_required_artifact_kinds_remain_integrity_bound(setup, monkeypatch, kind, change):
    client, _ = setup
    def engine(request):
        data = result(request.problem_id)
        if kind in {"student_proof", "refutation"}:
            witness = Path(data.artifact_dir) / "student.lean"
            witness.write_text("theorem x : True := by trivial")
            data.student_claim_checks = [dict(id="claim", status="verified" if kind == "student_proof" else "refuted",
                compiled=kind == "student_proof", lean_file=str(witness), refutation_lean_file=str(witness),
                refutation_verified=kind == "refutation")]
        return data
    monkeypatch.setattr(main, "execute_audit", engine)
    sid, rev = source(client)
    request = accept(client, sid, rev)
    run = execute(client, sid, request).json()
    assert run["status"] == "COMPLETED"
    artifact = next(item for item in run["required_artifacts"] if item["artifact_type"] == kind)
    witness = Path(artifact["file"])
    witness.unlink() if change == "removed" else witness.write_bytes(b"modified")
    assert client.get(f'/submission-audits/{run["audit_run_id"]}').status_code == 409


@pytest.mark.parametrize("verified", [False, True])
def test_refutation_cannot_publish_without_its_witness(setup, monkeypatch, verified):
    client, _ = setup
    def engine(request):
        data = result(request.problem_id)
        data.student_claim_checks = [dict(id="claim", status="refuted", refutation_verified=verified,
            refutation_lean_file=str(Path(data.artifact_dir) / "missing-negation.lean"))]
        return data
    monkeypatch.setattr(main, "execute_audit", engine)
    sid, rev = source(client)
    run = execute(client, sid, accept(client, sid, rev)).json()
    assert run["status"] == "FAILED" and run["result"] is None
