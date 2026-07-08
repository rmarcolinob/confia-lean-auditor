from pathlib import Path

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


CLIENT = TestClient(app)


def read_example(name: str) -> str:
    return Path(f"problems/ITA2025Q8/examples/{name}").read_text(encoding="utf-8")


def audit_solution(solution: str):
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025Q8",
            "solution": solution,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def rubric_item_by_id(data, item_id: str):
    for item in data["rubric_assessment"]["items"]:
        if item["id"] == item_id:
            return item
    raise AssertionError(f"Rubric item not found: {item_id}")


def microclaim_by_id(data, microclaim_id: str):
    for item in data["microclaims"]:
        if item["id"] == microclaim_id:
            return item
    raise AssertionError(f"Microclaim not found: {microclaim_id}")


def test_q8_correct_solution_scores_10_and_verifies_lean():
    data = audit_solution(read_example("correct_solution.txt"))

    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"

    formal_steps_by_type = {
        step["type"]: step
        for step in data["formal_steps"]
    }
    assert formal_steps_by_type["q8_numerator_factorization"]["status"] == "verified"
    assert formal_steps_by_type["q8_endpoint_sum"]["status"] == "verified"

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "numerator_factorization" in generated
    assert "endpoint_sum" in generated
    assert "candidate_length" in generated

    assert microclaim_by_id(data, "mc_numerator_factorization")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_endpoint_sum")["lean_status"] == "verified_by_lean"


def test_q8_answer_only_scores_interval_and_sum_only():
    data = audit_solution(read_example("answer_only.txt"))

    assert data["score"] == 3.5

    assert rubric_item_by_id(data, "numerator_factorization")["points"] == 0.0
    assert rubric_item_by_id(data, "denominator_condition")["points"] == 0.0
    assert rubric_item_by_id(data, "sign_analysis")["points"] == 0.0
    assert rubric_item_by_id(data, "longest_interval")["points"] == 2.0
    assert rubric_item_by_id(data, "endpoint_sum")["points"] == 1.5


def test_q8_missing_sign_analysis_loses_sign_points():
    data = audit_solution(read_example("missing_sign_analysis.txt"))

    assert rubric_item_by_id(data, "numerator_factorization")["points"] == 2.5
    assert rubric_item_by_id(data, "denominator_condition")["points"] == 2.0
    assert rubric_item_by_id(data, "sign_analysis")["points"] == 0.0
    assert rubric_item_by_id(data, "longest_interval")["points"] == 2.0
    assert rubric_item_by_id(data, "endpoint_sum")["points"] == 1.5

    assert data["score"] == 8.0


def test_q8_wrong_interval_scores_zero():
    data = audit_solution(read_example("wrong_interval.txt"))

    assert data["score"] == 0.0
    assert rubric_item_by_id(data, "longest_interval")["points"] == 0.0
    assert rubric_item_by_id(data, "endpoint_sum")["points"] == 0.0
