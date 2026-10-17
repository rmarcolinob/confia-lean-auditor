from __future__ import annotations

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


CLIENT = TestClient(app)

EXPECTED_PROBLEM_IDS = {
    "ITA2025Q1",
    "ITA2025Q3",
    "ITA2025Q4",
    "ITA2025Q5",
    "ITA2025Q8",
    "ITA2025F2Q1",
    "ITA2025F2Q3",
    "ITA2025F2Q5",
    "ITA2025F2Q6",
    "ITA2025F2Q8",
}

EXPECTED_EXAMPLE_KEYS = {
    "correct",
    "partial",
    "wrong",
    "adversarial",
}


def test_root_serves_mvp_html():
    response = CLIENT.get("/")

    assert response.status_code == 200
    html = response.text
    assert "ConfIA" in html
    assert "Confiabilidade e Explicabilidade em Matemática" in html
    assert '<main id="app-root"' in html
    assert 'id="auth-identity"' in html
    assert 'id="auth-logout"' in html
    for section in ("student-area", "student-exams", "student-workspace", "teacher-area",
                    "manuscript-inbox", "teacher-exams", "management-area", "management-overview"):
        assert f'id="{section}"' in html
    for link in ("#student/tutoria", "#student/exams", "#student/submissions",
                 "#teacher/submissions", "#management/overview"):
        assert f'href="{link}"' in html
    for element in ("problem-statement", "problem-title", "problem-statement-text"):
        assert f'id="{element}"' in html


def test_problems_endpoint_lists_10_mvp_questions_with_examples():
    response = CLIENT.get("/problems")

    assert response.status_code == 200
    problems = response.json()

    assert {problem["id"] for problem in problems} == EXPECTED_PROBLEM_IDS
    assert {problem["problem_id"] for problem in problems} == EXPECTED_PROBLEM_IDS
    assert len(problems) == 10

    for problem in problems:
        assert problem["problem_id"]
        assert problem["title"]
        assert problem["statement"]
        examples = problem["examples"]
        assert {example["key"] for example in examples} == EXPECTED_EXAMPLE_KEYS


def test_f2q1_catalog_includes_non_empty_statement():
    response = CLIENT.get("/problems")

    assert response.status_code == 200
    problems = response.json()
    f2q1 = next(problem for problem in problems if problem["problem_id"] == "ITA2025F2Q1")

    assert f2q1["statement"]


def test_problem_example_endpoint_returns_solution_text():
    response = CLIENT.get("/problems/ITA2025F2Q1/examples/correct")

    assert response.status_code == 200
    payload = response.json()

    assert payload["problem_id"] == "ITA2025F2Q1"
    assert payload["example_key"] == "correct"
    assert payload["solution"]
    assert "x^57" in payload["solution"]


def test_problem_example_endpoint_rejects_unknown_problem_or_example():
    unknown_problem = CLIENT.get("/problems/ITA2025F2Q999/examples/correct")
    unknown_example = CLIENT.get("/problems/ITA2025F2Q1/examples/../../secret")
    unsupported_example = CLIENT.get("/problems/ITA2025F2Q1/examples/debug")

    assert unknown_problem.status_code == 404
    assert unknown_example.status_code in {404, 422}
    assert unsupported_example.status_code == 404


def test_ui_can_load_example_and_audit_with_pedagogical_report(monkeypatch):
    from pathlib import Path
    import subprocess
    import confia_lean_auditor.main as main
    from confia_lean_auditor.core.schemas import AuditResponse
    root = Path(__file__).resolve().parents[1]
    def files():
        return {str(p): (p.stat().st_size, p.stat().st_mtime_ns)
                for name in ("artifacts", ".lake") for p in (root / name).rglob("*") if p.is_file()}
    before = files()
    calls = []
    def engine(request):
        calls.append(request)
        return AuditResponse(problem_id=request.problem_id, score=0, max_score=10, verdict="insuficiente",
            extracted_claims={"problem_id": request.problem_id, "claims": []}, formal_steps=[],
            rubric_assessment={"score": 0, "max_score": 10, "items": []},
            lean_certificate={"status": "unverified", "compiled": False, "exit_code": 0,
                              "uses_forbidden_token": False, "forbidden_tokens_found": []},
            microclaims=[], feedback="Resposta controlada",
            pedagogical_report={"summary": "Resumo controlado", "result": "Insuficiente", "score": 0,
                                "max_score": 10, "verdict": "insuficiente", "reliability": "limitada"})
    def forbidden(*args, **kwargs):
        raise AssertionError("static UI test must not execute subprocesses")
    monkeypatch.setattr(main, "execute_audit", engine)
    monkeypatch.setattr(subprocess, "run", forbidden)
    example_response = CLIENT.get("/problems/ITA2025F2Q1/examples/correct")
    assert example_response.status_code == 200

    solution = example_response.json()["solution"]
    audit_response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q1",
            "solution": solution,
        },
    )

    assert audit_response.status_code == 200, audit_response.text
    payload = audit_response.json()

    assert payload["problem_id"] == "ITA2025F2Q1"
    assert payload["pedagogical_report"] is not None
    assert payload["pedagogical_report"]["summary"]

    assert len(calls) == 1 and calls[0].solution == solution
    assert files() == before
