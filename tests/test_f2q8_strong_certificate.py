from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


CLIENT = TestClient(app)


def read_example(name: str) -> str:
    return Path(f"problems/ITA2025F2Q8/examples/{name}").read_text(encoding="utf-8")


def audit_solution(solution: str):
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q8",
            "solution": solution,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_f2q8_correct_solution_includes_strong_certificate():
    data = audit_solution(read_example("correct_solution.txt"))

    assert data["score"] == data["max_score"]
    assert data["lean_certificate"]["status"] == "verified"

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "generated_strong_f2q8_claim" in generated
    assert "generated_strong_claim" in generated


def test_f2q8_wrong_answer_does_not_include_complete_strong_certificate():
    data = audit_solution(read_example("wrong_answer.txt"))

    generated = set(data["lean_certificate"]["generated_theorems"])

    assert data["score"] is None
    assert data["verdict"] == "inconclusivo"
    assert "generated_strong_f2q8_claim" not in generated
    assert "generated_strong_claim" not in generated
