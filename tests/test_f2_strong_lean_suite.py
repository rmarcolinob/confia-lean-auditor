from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


CLIENT = TestClient(app)

F2_PROBLEMS = [
    "ITA2025F2Q1",
    "ITA2025F2Q3",
    "ITA2025F2Q5",
    "ITA2025F2Q6",
    "ITA2025F2Q8",
]

WRONG_EXAMPLES = {
    "ITA2025F2Q1": "wrong_answer.txt",
    "ITA2025F2Q3": "wrong_answer.txt",
    "ITA2025F2Q5": "wrong_digit.txt",
    "ITA2025F2Q6": "wrong_answer.txt",
    "ITA2025F2Q8": "wrong_answer.txt",
}


def read_example(problem_id: str, name: str) -> str:
    return Path(f"problems/{problem_id}/examples/{name}").read_text(encoding="utf-8")


def audit_solution(problem_id: str, solution: str) -> dict:
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": problem_id,
            "solution": solution,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("problem_id", F2_PROBLEMS)
def test_f2_correct_solution_has_full_operational_strong_lean_contract(problem_id: str):
    data = audit_solution(problem_id, read_example(problem_id, "correct_solution.txt"))

    assert data["score"] == data["max_score"]
    assert data["verdict"] == "correto"
    assert data["lean_certificate"]["status"] == "verified"
    assert data["pedagogical_report"] is not None
    assert data["artifact_dir"]
    assert isinstance(data["formal_steps"], list)
    assert isinstance(data["student_claims"], list)
    assert isinstance(data["student_claim_checks"], list)


@pytest.mark.parametrize("problem_id", F2_PROBLEMS)
def test_f2_wrong_answer_stays_below_full_score(problem_id: str):
    data = audit_solution(problem_id, read_example(problem_id, WRONG_EXAMPLES[problem_id]))

    assert data["score"] < data["max_score"]
    assert data["pedagogical_report"] is not None

    if data["student_claim_checks"]:
        statuses = {check["status"] for check in data["student_claim_checks"]}
        assert statuses & {"failed", "rejected"}
