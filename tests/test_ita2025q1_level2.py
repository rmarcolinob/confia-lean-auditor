from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


REPO_ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)


def read_example(name: str) -> str:
    return (REPO_ROOT / "problems" / "ITA2025Q1" / "examples" / name).read_text(
        encoding="utf-8"
    )


def audit_solution(solution: str):
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025Q1",
            "solution": solution,
        },
    )
    assert response.status_code == 200
    return response.json()


def microclaim_by_id(data, microclaim_id: str):
    return {
        microclaim["id"]: microclaim
        for microclaim in data["microclaims"]
    }[microclaim_id]


def rubric_item_by_id(data, item_id: str):
    return {
        item["id"]: item
        for item in data["rubric_assessment"]["items"]
    }[item_id]


def test_q1_correct_solution_scores_10_and_verifies_formal_step():
    data = audit_solution(read_example("correct_solution.txt"))

    assert data["score"] == 10.0
    assert data["verdict"] == "correto"

    assert len(data["formal_steps"]) == 1
    assert data["formal_steps"][0]["type"] == "determinant_expansion"
    assert data["formal_steps"][0]["status"] == "verified"

    assert "triangleArea_formula" in data["lean_certificate"]["generated_theorems"]

    area_mc = microclaim_by_id(data, "mc_area_formula")
    assert area_mc["lean_status"] == "verified_by_lean"
    assert area_mc["formal_steps_verified"] is True


def test_q1_wrong_determinant_step_blocks_area_and_dependencies():
    data = audit_solution(read_example("wrong_determinant_step.txt"))

    assert data["score"] == 3.0
    assert data["verdict"] == "insuficiente"

    assert len(data["formal_steps"]) == 1
    assert data["formal_steps"][0]["type"] == "determinant_expansion"
    assert data["formal_steps"][0]["status"] != "verified"

    area_item = rubric_item_by_id(data, "area_formula")
    assert area_item["detected"] is False
    assert area_item["points"] == 0.0

    equation_item = rubric_item_by_id(data, "equation")
    assert equation_item["detected"] is False
    assert equation_item["points"] == 0.0

    positive_root_item = rubric_item_by_id(data, "positive_root")
    assert positive_root_item["detected"] is False
    assert positive_root_item["points"] == 0.0

    area_mc = microclaim_by_id(data, "mc_area_formula")
    assert area_mc["lean_status"] == "formal_steps_not_verified"
    assert area_mc["formal_steps_verified"] is False

    unique_mc = microclaim_by_id(data, "mc_unique_positive_solution")
    assert unique_mc["lean_status"] == "dependency_not_verified"
    assert unique_mc["dependencies_verified"] is False


def test_q1_answer_only_scores_1():
    data = audit_solution(read_example("answer_only.txt"))

    assert data["score"] == 1.0
    assert data["verdict"] == "insuficiente"

    assert data["formal_steps"] == []

    answer_mc = microclaim_by_id(data, "mc_answer_check")
    assert answer_mc["lean_status"] == "verified_by_lean"


def test_q1_injection_attempt_is_rejected_before_lean_generation():
    data = audit_solution(read_example("injection_attempt.txt"))

    assert len(data["formal_steps"]) == 1
    step = data["formal_steps"][0]

    assert step["status"] == "invalid_formal_step"
    assert step["compiled"] is False
    assert "forbidden" in step["stderr"].lower() or "contains" in step["stderr"].lower()

    area_mc = microclaim_by_id(data, "mc_area_formula")
    assert area_mc["lean_status"] == "formal_steps_not_verified"


def test_malicious_problem_id_is_rejected():
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "../../etc",
            "solution": "teste",
        },
    )

    assert response.status_code == 400
