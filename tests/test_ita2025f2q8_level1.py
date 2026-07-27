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


def test_f2q8_correct_solution_scores_10_and_verifies_lean():
    data = audit_solution(read_example("correct_solution.txt"))

    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"

    formal_steps_by_type = {
        step["type"]: step
        for step in data["formal_steps"]
    }

    assert formal_steps_by_type["f2q8_bridge"]["status"] == "verified"
    assert formal_steps_by_type["f2q8_coldiff_det_one"]["status"] == "verified"
    assert formal_steps_by_type["f2q8_determinant_formula"]["status"] == "verified"
    assert formal_steps_by_type["f2q8_final_sum"]["status"] == "verified"

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "generated_bridge_generic" in generated
    assert "generated_coldiff_det_one" in generated
    assert "generated_determinant_formula" in generated
    assert "generated_final_answer" in generated
    assert "generated_strong_claim" in generated

    assert microclaim_by_id(data, "f2q8_column_difference")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "f2q8_det_formula")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "f2q8_final_sum")["lean_status"] == "verified_by_lean"


def test_f2q8_answer_only_scores_final_points_only():
    data = audit_solution(read_example("answer_only.txt"))

    assert data["score"] == 1.5
    assert rubric_item_by_id(data, "final_answer")["points"] == 1.5
    assert rubric_item_by_id(data, "matrix_transformation")["points"] == 0.0
    assert rubric_item_by_id(data, "determinant_formula")["points"] == 0.0
    assert rubric_item_by_id(data, "alternating_sum")["points"] == 0.0


def test_f2q8_missing_determinant_formula_scores_partial():
    data = audit_solution(read_example("missing_determinant_formula.txt"))

    assert rubric_item_by_id(data, "matrix_transformation")["points"] == 0.0
    assert rubric_item_by_id(data, "determinant_formula")["points"] == 0.0
    assert rubric_item_by_id(data, "alternating_sum")["points"] == 2.0
    assert rubric_item_by_id(data, "final_answer")["points"] == 1.5
    assert data["score"] == 3.5

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "generated_determinant_formula" not in generated
    assert "generated_final_answer" in generated


def test_f2q8_wrong_answer_scores_zero():
    data = audit_solution(read_example("wrong_answer.txt"))

    assert data["score"] == 0.0
    assert rubric_item_by_id(data, "final_answer")["points"] == 0.0
    assert rubric_item_by_id(data, "determinant_formula")["points"] == 0.0
