from pathlib import Path

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


CLIENT = TestClient(app)


def read_example(name: str) -> str:
    return Path(f"problems/ITA2025Q5/examples/{name}").read_text(encoding="utf-8")


def audit_solution(solution: str):
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025Q5",
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


def test_q5_correct_solution_scores_10_and_verifies_lean():
    data = audit_solution(read_example("correct_solution.txt"))

    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"

    formal_steps_by_type = {
        step["type"]: step
        for step in data["formal_steps"]
    }
    assert formal_steps_by_type["q5_geometric_factorization"]["status"] == "verified"

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "difference_relation" in generated
    assert "geometric_form_template" in generated
    assert "geometric_factorization" in generated
    assert "conclusion_pg" in generated

    assert microclaim_by_id(data, "mc_difference_relation")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_geometric_form")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_geometric_factorization")["lean_status"] == "verified_by_lean"
    assert microclaim_by_id(data, "mc_conclusion_pg")["lean_status"] == "verified_by_lean"


def test_q5_answer_only_scores_conclusion_point_only():
    data = audit_solution(read_example("answer_only.txt"))

    assert data["score"] == 1.0

    assert rubric_item_by_id(data, "difference_relation")["points"] == 0.0
    assert rubric_item_by_id(data, "geometric_form")["points"] == 0.0
    assert rubric_item_by_id(data, "geometric_factorization")["points"] == 0.0
    assert rubric_item_by_id(data, "conclusion_pg")["points"] == 1.0


def test_q5_missing_difference_blocks_factorization_dependency():
    data = audit_solution(read_example("missing_difference_relation.txt"))

    assert rubric_item_by_id(data, "difference_relation")["points"] == 0.0
    assert rubric_item_by_id(data, "geometric_form")["points"] == 2.0
    assert rubric_item_by_id(data, "geometric_factorization")["points"] == 0.0
    assert rubric_item_by_id(data, "conclusion_pg")["points"] == 1.0

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "difference_relation" not in generated
    assert "geometric_form_template" in generated
    assert "geometric_factorization" not in generated
    assert "conclusion_pg" not in generated


def test_q5_missing_factorization_blocks_formal_step():
    data = audit_solution(read_example("missing_factorization.txt"))

    assert rubric_item_by_id(data, "difference_relation")["points"] == 3.0
    assert rubric_item_by_id(data, "geometric_form")["points"] == 2.0
    assert rubric_item_by_id(data, "geometric_factorization")["points"] == 0.0
    assert rubric_item_by_id(data, "conclusion_pg")["points"] == 1.0

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "difference_relation" in generated
    assert "geometric_form_template" in generated
    assert "geometric_factorization" not in generated
    assert "conclusion_pg" not in generated


def test_q5_wrong_direction_scores_zero():
    data = audit_solution(read_example("wrong_direction.txt"))

    assert data["score"] == 0.0
    assert rubric_item_by_id(data, "conclusion_pg")["points"] == 0.0
