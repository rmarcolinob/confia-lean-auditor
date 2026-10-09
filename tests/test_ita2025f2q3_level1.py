from pathlib import Path

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app
from audit_contract import assert_score_contract, assert_incomplete


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

    assert_incomplete(data, 2, 2)
    assert rubric_item_by_id(data, "final_answer")["points"] == 2.0
    assert rubric_item_by_id(data, "beta_difference")["points"] is None
    assert rubric_item_by_id(data, "candidate_values")["points"] is None
    assert rubric_item_by_id(data, "final_sin_sum")["points"] is None


def test_f2q3_partial_beta_difference_scores_partial():
    data = audit_solution(read_example("partial_beta_difference.txt"))

    assert_incomplete(data, 2, 4)
    assert rubric_item_by_id(data, "beta_difference")["points"] == 2.0
    assert rubric_item_by_id(data, "candidate_values")["points"] is None
    assert rubric_item_by_id(data, "final_sin_sum")["points"] is None
    # The existing checker also decides the extracted final-answer claim by refutation.
    # Its zero belongs to the decided capacity; missing criteria remain pending.
    final = rubric_item_by_id(data, "final_answer")
    assert final["points"] == 0.0
    assert final["mathematical_status"] == "refuted"
    check = next(check for check in data["student_claim_checks"]
                 if check["claim_type"] == "f2q3_student_final_answer")
    assert check["status"] == "refuted" and check["refutation_verified"] is True
    assert check["refutation_lean_file"]


def test_f2q3_wrong_answer_keeps_undecided_criteria_and_decided_subtotal():
    data = audit_solution(read_example("wrong_answer.txt"))

    assert_incomplete(data, 0, 5)
    assert rubric_item_by_id(data, "final_answer")["points"] == 0.0
    assert rubric_item_by_id(data, "final_sin_sum")["points"] == 0.0
