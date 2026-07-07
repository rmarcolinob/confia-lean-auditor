from pathlib import Path

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


CLIENT = TestClient(app)


def read_example(name: str) -> str:
    return Path(f"problems/ITA2025Q4/examples/{name}").read_text(encoding="utf-8")


def audit_solution(solution: str):
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025Q4",
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


def test_q4_correct_solution_scores_10_and_verifies_lean():
    data = audit_solution(read_example("correct_solution.txt"))

    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "positive_witnesses" in generated
    assert "same_f_argument" in generated
    assert "distinct_g_inputs" in generated
    assert "equal_g_values" in generated
    assert "g_not_injective" in generated

    assert microclaim_by_id(data, "mc_positive_witnesses")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_same_f_argument")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_distinct_g_inputs")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_equal_g_values")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_not_injective")["lean_status"] == "verified_by_lean"


def test_q4_answer_only_scores_conclusion_point_only():
    data = audit_solution(read_example("answer_only.txt"))

    assert data["score"] == 1.0

    conclusion = rubric_item_by_id(data, "not_injective_conclusion")
    assert conclusion["detected"] is True
    assert conclusion["points"] == 1.0

    assert rubric_item_by_id(data, "positive_witnesses")["points"] == 0.0
    assert rubric_item_by_id(data, "same_f_argument")["points"] == 0.0
    assert rubric_item_by_id(data, "distinct_g_inputs")["points"] == 0.0
    assert rubric_item_by_id(data, "equal_g_values")["points"] == 0.0
