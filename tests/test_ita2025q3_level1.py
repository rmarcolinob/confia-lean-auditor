from pathlib import Path

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


CLIENT = TestClient(app)


def read_example(name: str) -> str:
    return Path(f"problems/ITA2025Q3/examples/{name}").read_text(encoding="utf-8")


def audit_solution(solution: str):
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025Q3",
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


def test_q3_correct_solution_scores_10_and_verifies_formal_step():
    data = audit_solution(read_example("correct_solution.txt"))

    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"

    formal_steps_by_type = {
        step["type"]: step
        for step in data["formal_steps"]
    }
    assert formal_steps_by_type["q3_no_zero_exponent"]["status"] == "verified"

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "first_factor_exponent_form" in generated
    assert "second_factor_exponent_form" in generated
    assert "no_constant_exponent" in generated
    assert "product_exponent_odd" in generated
    assert "final_answer_zero" in generated

    assert microclaim_by_id(data, "mc_first_factor_exponent")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_second_factor_exponent")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_exponent_balance")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_parity_obstruction")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_final_answer")["lean_status"] == "verified_by_lean"


def test_q3_answer_only_scores_one_point():
    data = audit_solution(read_example("answer_only.txt"))

    assert data["score"] == 1.0

    final_item = rubric_item_by_id(data, "final_answer")
    assert final_item["detected"] is True
    assert final_item["points"] == 1.0


def test_q3_wrong_coefficient_scores_zero():
    data = audit_solution(read_example("wrong_coefficient.txt"))

    assert data["score"] == 0.0

    final_item = rubric_item_by_id(data, "final_answer")
    assert final_item["detected"] is False
    assert final_item["points"] == 0.0


def test_q3_missing_parity_blocks_formal_chain():
    data = audit_solution(read_example("missing_parity.txt"))

    assert rubric_item_by_id(data, "first_factor_exponent")["points"] == 2.0
    assert rubric_item_by_id(data, "second_factor_exponent")["points"] == 2.0
    assert rubric_item_by_id(data, "exponent_balance")["points"] == 0.0
    assert rubric_item_by_id(data, "parity_obstruction")["points"] == 0.0
    assert rubric_item_by_id(data, "final_answer")["points"] == 1.0

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "no_constant_exponent" not in generated
    assert "product_exponent_odd" not in generated
    assert "final_answer_zero" not in generated
