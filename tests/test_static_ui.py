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
    assert "ConfIA" in response.text
    assert "app-root" in response.text


def test_problems_endpoint_lists_10_mvp_questions_with_examples():
    response = CLIENT.get("/problems")

    assert response.status_code == 200
    problems = response.json()

    assert {problem["id"] for problem in problems} == EXPECTED_PROBLEM_IDS

    for problem in problems:
        assert problem["title"]
        examples = problem["examples"]
        assert {example["key"] for example in examples} == EXPECTED_EXAMPLE_KEYS


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


def test_ui_can_load_example_and_audit_with_pedagogical_report():
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
