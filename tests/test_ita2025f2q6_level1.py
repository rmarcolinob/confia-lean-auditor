from pathlib import Path

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


CLIENT = TestClient(app)


def read_example(name: str) -> str:
    return Path(f"problems/ITA2025F2Q6/examples/{name}").read_text(encoding="utf-8")


def audit_solution(solution: str):
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q6",
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


def test_f2q6_correct_solution_scores_10_and_verifies_lean():
    data = audit_solution(read_example("correct_solution.txt"))

    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"

    formal_steps_by_type = {
        step["type"]: step
        for step in data["formal_steps"]
    }

    assert formal_steps_by_type["f2q6_probability_values"]["status"] == "verified"
    assert formal_steps_by_type["f2q6_ratio_comparison"]["status"] == "verified"

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "probability_values" in generated
    assert "ratio_comparison" in generated
    assert "candidate_maximizers" in generated
    assert "final_answer" in generated

    assert microclaim_by_id(data, "mc_probability_formula")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_ratio_comparison")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_maximizers_identification")["lean_status"] == "verified_by_lean"


def test_f2q6_answer_only_scores_final_points_only():
    data = audit_solution(read_example("answer_only.txt"))

    assert data["score"] == 2.0
    assert rubric_item_by_id(data, "final_answer")["points"] == 2.0
    assert rubric_item_by_id(data, "probability_formula")["points"] == 0.0
    assert rubric_item_by_id(data, "ratio_comparison")["points"] == 0.0


def test_f2q6_missing_ratio_scores_partial():
    data = audit_solution(read_example("missing_ratio.txt"))

    assert rubric_item_by_id(data, "probability_formula")["points"] == 3.0
    assert rubric_item_by_id(data, "ratio_comparison")["points"] == 0.0
    assert rubric_item_by_id(data, "maximizers_identification")["points"] == 0.0
    assert rubric_item_by_id(data, "final_answer")["points"] == 2.0
    assert data["score"] == 5.0

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "probability_values" in generated
    assert "ratio_comparison" not in generated
    assert "candidate_maximizers" not in generated


def test_f2q6_wrong_answer_scores_zero():
    data = audit_solution(read_example("wrong_answer.txt"))

    assert data["score"] == 0.0
    assert rubric_item_by_id(data, "final_answer")["points"] == 0.0
