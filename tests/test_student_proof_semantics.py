"""Compiler failures are not refutations, across all student checkers/routes."""
from importlib import import_module
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

import confia_lean_auditor.main as main
import confia_lean_auditor.lean.formal_step_evaluator as formal
from confia_lean_auditor.core.schemas import RubricAssessment, RubricItemResult
from confia_lean_auditor.reports.report_builder import _build_check_evidence_items
from confia_lean_auditor.student_claims.schemas import StudentClaim
from test_submission_audits import source, accept, execute


CHECKERS = [
    ("confia_lean_auditor.lean.student_claim_checker", "check_one_student_claim", "ITA2025F2Q8", "arithmetic_equality", {"left_expr": "2+2", "right_expr": "5"}),
    *[(f"confia_lean_auditor.lean.student_claim_checkers.ita2025f2q{n}", f"check_one_f2q{n}_student_claim", f"ITA2025F2Q{n}", kind, data)
      for n, kind, data in [
          (1, "f2q1_student_final_answer", {"a": -1, "b": 3}),
          (3, "f2q3_student_final_answer", {"expr": "(5 + sqrt7) / 8"}),
          (5, "f2q5_student_final_digit", {"digit": 5}),
          (6, "f2q6_student_final_answer", {"values": [6, 7]}),
      ]],
]


@pytest.mark.parametrize("module_name,function,problem,kind,data", CHECKERS)
@pytest.mark.parametrize("diagnostic,expected", [
    ("error: unknown module prefix Mathlib", "technical_error"),
    ("object file 'Mathlib.olean' does not exist", "technical_error"),
    ("error: unknown identifier x", "technical_error"),
    ("error: unsolved goals", "unverified"),
    ("error: tactic 'norm_num' failed", "unverified"),
    ("error: failed to synthesize Decidable", "unverified"),
    ("error: type mismatch", "technical_error"),
    ("timeout", "technical_error"),
    ("process failure", "technical_error"),
])
def test_every_checker_keeps_compile_failures_inconclusive(tmp_path, monkeypatch,
        module_name, function, problem, kind, data, diagnostic, expected):
    module = import_module(module_name)
    monkeypatch.setattr(module, "CHECK_DIR", tmp_path)
    monkeypatch.setattr(module, "_run_lean_file", lambda *args, **kwargs: subprocess.CompletedProcess([], 1, diagnostic, ""))
    claim = StudentClaim("claim", problem, kind, "a=-1, b=3", "a=-1, b=3", "student", data)
    check = getattr(module, function)(claim, "run", 0)
    assert check.status == expected and not check.refutation_verified
    evidence = _build_check_evidence_items([claim], [check])[0]
    assert evidence.result != "incorreta"
    assert "formal" in evidence.explanation


def test_timeout_exception_is_technical(tmp_path, monkeypatch):
    module = import_module(CHECKERS[1][0])
    monkeypatch.setattr(module, "CHECK_DIR", tmp_path)
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("lean", 1)
    monkeypatch.setattr(module, "_run_lean_file", timeout)
    claim = StudentClaim("claim", "ITA2025F2Q1", "f2q1_student_final_answer", "a=-1, b=3", "", "student", {"a": -1, "b": 3})
    check = module.check_one_f2q1_student_claim(claim, "run", 0)
    assert check.status == "technical_error" and check.failure_category == "TIMEOUT"


@pytest.mark.parametrize("positive,negative,expected", [(0, 1, "verified"), (1, 0, "refuted"), (1, 1, "unverified")])
def test_only_compiled_negation_is_refutation(tmp_path, monkeypatch, positive, negative, expected):
    module = import_module(CHECKERS[0][0])
    monkeypatch.setattr(module, "CHECK_DIR", tmp_path)
    def runner(path, **kwargs):
        refutation = path.stem.endswith("_refutation")
        if refutation:
            assert "¬ ((" in path.read_text()
        code = negative if refutation else positive
        return subprocess.CompletedProcess([], code, "" if code == 0 else "error: unsolved goals", "")
    monkeypatch.setattr(module, "_run_lean_file", runner)
    claim = StudentClaim("claim", "ITA2025F2Q8", "arithmetic_equality", "2+2=5", "", "student", {"left_expr": "2+2", "right_expr": "5"})
    check = module.check_one_student_claim(claim, "run", 0)
    assert check.status == expected
    assert check.refutation_verified is (expected == "refuted")


@pytest.mark.parametrize("number", [1, 3, 5, 6, 8])
@pytest.mark.parametrize("status", ["unverified", "technical_error", "failed", "error", "refuted"])
def test_all_rubric_adjusters_require_refutation_evidence(number, status):
    module = import_module(f"confia_lean_auditor.rubric.adjusters.ita2025f2q{number}")
    mapping = getattr(module, f"F2Q{number}_STUDENT_CHECK_TO_RUBRIC_ITEMS")
    kind, items = next(iter(mapping.items()))
    rubric = RubricAssessment(score=10, max_score=10, items=[
        RubricItemResult(id=items[0], description="criterion", detected=True, points=10, max_points=10)])
    check = {"claim_type": kind, "status": status, "raw_text": "student statement"}
    adjusted = getattr(module, f"apply_f2q{number}_student_claim_adjustments")(rubric, [check])
    assert adjusted.score == 10 and adjusted.items[0].student_check_adjusted is False


@pytest.mark.parametrize("failure", ["unknown module prefix Mathlib", "unknown identifier x", "unsolved goals", "timeout"])
def test_textual_and_bridge_share_failure_semantics_without_score_penalty(tmp_path, monkeypatch, failure):
    module = import_module(CHECKERS[1][0])
    root = Path(__file__).resolve().parents[1]
    (tmp_path / "problems").symlink_to(root / "problems", target_is_directory=True)
    monkeypatch.setattr(main, "repo_root", lambda: tmp_path)
    monkeypatch.setenv("CONFIA_SUBMISSIONS_DIR", str(tmp_path / "submissions"))
    monkeypatch.setenv("CONFIA_SUBMISSION_AUDITS_DIR", str(tmp_path / "audits"))
    monkeypatch.setattr(module, "CHECK_DIR", tmp_path / "student-checks")
    verified = lambda *args, **kwargs: {
        "status": "verified", "compiled": True, "exit_code": 0,
        "uses_forbidden_token": False, "forbidden_tokens_found": []}
    monkeypatch.setattr(main, "run_lean_file", verified)
    monkeypatch.setattr(formal, "run_lean_file", verified)
    monkeypatch.setattr(module, "_run_lean_file", lambda *args, **kwargs: subprocess.CompletedProcess([], 0, "", ""))
    solution = (root / "problems/ITA2025F2Q1/examples/correct_solution.txt").read_text()
    client = TestClient(main.app)
    baseline = client.post("/audit", json={"problem_id": "ITA2025F2Q1", "solution": solution}).json()
    monkeypatch.setattr(module, "_run_lean_file", lambda *args, **kwargs: subprocess.CompletedProcess([], 1, failure, ""))
    textual = client.post("/audit", json={"problem_id": "ITA2025F2Q1", "solution": solution})
    assert textual.status_code == 200
    sid, rev = source(client, values=[{"segment_id": "exact", "page_index": 0, "order": 0, "kind": "mixed", "text": solution}])
    bridge = execute(client, sid, accept(client, sid, rev)).json()
    assert bridge["status"] == "COMPLETED"
    a, b = textual.json(), bridge["result"]
    def central(value):
        if isinstance(value, dict):
            return {k: central(v) for k, v in value.items() if k not in {"artifact_dir", "lean_file", "refutation_lean_file", "stdout", "stderr", "refutation_stdout", "refutation_stderr"}}
        if isinstance(value, list):
            return [central(v) for v in value]
        return value
    assert central(a) == central(b)
    assert a["score"] == baseline["score"] == 10
    assert all(item["status"] != "refuted" for item in a["student_claim_checks"])
    assert all(item["result"] != "incorreta" for item in a["pedagogical_report"]["evidence_items"] if item["title"] == "Afirmação do estudante")


def test_real_arithmetic_negation_and_verified_claim(tmp_path, monkeypatch):
    module = import_module(CHECKERS[0][0])
    monkeypatch.setattr(module, "CHECK_DIR", tmp_path)
    for value, expected in (("5", "refuted"), ("4", "verified")):
        claim = StudentClaim("claim", "ITA2025F2Q8", "arithmetic_equality", f"2+2={value}", "", "student", {"left_expr": "2+2", "right_expr": value})
        check = module.check_one_student_claim(claim, f"real-{value}", 0)
        assert check.status == expected, check
        if expected == "refuted":
            assert check.refutation_verified and Path(check.refutation_lean_file).is_file()
