from pathlib import Path

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app
from audit_contract import assert_score_contract, assert_incomplete


CLIENT = TestClient(app)


def read_example(name: str) -> str:
    return Path(f"problems/ITA2025F2Q5/examples/{name}").read_text(encoding="utf-8")


def audit_solution(solution: str):
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q5",
            "solution": solution,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert_score_contract(data)
    return data


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


def test_f2q5_correct_solution_scores_10_and_verifies_lean():
    data = audit_solution(read_example("correct_solution.txt"))

    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"

    formal_steps_by_type = {
        step["type"]: step
        for step in data["formal_steps"]
    }

    assert formal_steps_by_type["f2q5_log_power_decomposition"]["status"] == "verified"
    assert formal_steps_by_type["f2q5_digit_bounds"]["status"] == "verified"

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "log_power_decomposition" in generated
    assert "digit_log_bounds" in generated
    assert "mantissa_between_bounds" in generated
    assert "final_digit_five" in generated

    assert microclaim_by_id(data, "mc_log_power_decomposition")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_mantissa_identification")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_digit_log_bounds")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_mantissa_between_bounds")["lean_status"] == "verified_by_lean"


def test_f2q5_answer_only_scores_final_points_only():
    data = audit_solution(read_example("answer_only.txt"))

    assert_incomplete(data, 2, 2)
    assert rubric_item_by_id(data, "final_digit")["points"] == 2.0
    assert rubric_item_by_id(data, "log_power_decomposition")["points"] is None


def test_f2q5_missing_bounds_scores_partial():
    data = audit_solution(read_example("missing_bounds.txt"))

    assert rubric_item_by_id(data, "log_power_decomposition")["points"] == 2.0
    assert rubric_item_by_id(data, "mantissa_identification")["points"] == 2.0
    assert rubric_item_by_id(data, "digit_log_bounds")["points"] is None
    assert rubric_item_by_id(data, "mantissa_between_bounds")["points"] is None
    assert rubric_item_by_id(data, "final_digit")["points"] == 2.0
    assert_incomplete(data, 6, 6)

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "log_power_decomposition" in generated
    assert "digit_log_bounds" not in generated
    assert "mantissa_between_bounds" not in generated
    assert "final_digit_five" not in generated


def test_f2q5_wrong_digit_keeps_undecided_criteria_and_decided_subtotal():
    data = audit_solution(read_example("wrong_digit.txt"))

    assert_incomplete(data, 0, 2)
    assert rubric_item_by_id(data, "final_digit")["points"] == 0.0
