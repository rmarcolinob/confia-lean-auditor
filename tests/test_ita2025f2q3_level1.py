from pathlib import Path

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


CLIENT = TestClient(app)


def read_example(name: str) -> str:
    return Path(f"problems/ITA2025F2Q3/examples/{name}").read_text(encoding="utf-8")


def audit_solution(solution: str):
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q3",
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


def test_f2q3_correct_solution_scores_10_and_verifies_lean():
    data = audit_solution(read_example("correct_solution.txt"))

    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"

    formal_steps_by_type = {
        step["type"]: step
        for step in data["formal_steps"]
    }

    assert formal_steps_by_type["f2q3_beta_difference"]["status"] == "verified"
    assert formal_steps_by_type["f2q3_equations"]["status"] == "verified"
    assert formal_steps_by_type["f2q3_unit_circle"]["status"] == "verified"
    assert formal_steps_by_type["f2q3_final_sin_sum"]["status"] == "verified"
    assert formal_steps_by_type["f2q3_final_answer"]["status"] == "verified"

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "generated_beta_difference" in generated
    assert "generated_equations" in generated
    assert "generated_unit_circle" in generated
    assert "generated_final_sin_sum" in generated
    assert "generated_final_answer" in generated

    assert microclaim_by_id(data, "f2q3_beta_difference")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "f2q3_equations")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "f2q3_unit_circle")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "f2q3_final_sin_sum")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "f2q3_final_answer")["lean_status"] == "verified_by_lean"


def test_f2q3_answer_only_scores_final_points_only():
    data = audit_solution(read_example("answer_only.txt"))

    assert data["score"] == 2.0
    assert rubric_item_by_id(data, "final_answer")["points"] == 2.0
    assert rubric_item_by_id(data, "beta_difference")["points"] == 0.0
    assert rubric_item_by_id(data, "candidate_values")["points"] == 0.0
    assert rubric_item_by_id(data, "final_sin_sum")["points"] == 0.0


def test_f2q3_partial_beta_difference_scores_partial():
    data = audit_solution(read_example("partial_beta_difference.txt"))

    assert data["score"] == 2.0
    assert rubric_item_by_id(data, "beta_difference")["points"] == 2.0
    assert rubric_item_by_id(data, "candidate_values")["points"] == 0.0
    assert rubric_item_by_id(data, "final_sin_sum")["points"] == 0.0
    assert rubric_item_by_id(data, "final_answer")["points"] == 0.0


def test_f2q3_wrong_answer_scores_zero():
    data = audit_solution(read_example("wrong_answer.txt"))

    assert data["score"] == 0.0
    assert rubric_item_by_id(data, "final_answer")["points"] == 0.0
    assert rubric_item_by_id(data, "final_sin_sum")["points"] == 0.0
