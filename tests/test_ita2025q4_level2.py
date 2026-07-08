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


def claim_types(data):
    return {claim["type"] for claim in data["extracted_claims"]["claims"]}


def test_q4_wrong_target_does_not_get_not_injective_conclusion():
    data = audit_solution(read_example("wrong_target.txt"))

    assert "not_injective_conclusion" not in claim_types(data)

    conclusion = rubric_item_by_id(data, "not_injective_conclusion")
    assert conclusion["detected"] is False
    assert conclusion["points"] == 0.0

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "g_not_injective" not in generated


def test_q4_missing_distinct_inputs_blocks_final_dependency():
    data = audit_solution(read_example("missing_distinct_inputs.txt"))

    assert "not_injective_conclusion" in claim_types(data)
    assert "distinct_g_inputs" not in claim_types(data)

    distinct_mc = microclaim_by_id(data, "mc_distinct_g_inputs")
    assert distinct_mc["textual_evidence"] is False
    assert distinct_mc["lean_status"] == "no_textual_evidence"

    equal_mc = microclaim_by_id(data, "mc_equal_g_values")
    assert equal_mc["dependencies_verified"] is False

    final_mc = microclaim_by_id(data, "mc_not_injective")
    assert final_mc["dependencies_verified"] is False

    conclusion = rubric_item_by_id(data, "not_injective_conclusion")
    assert conclusion["detected"] is True
    assert conclusion["points"] == 1.0

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "g_not_injective" not in generated


def test_q4_wrong_witnesses_do_not_verify_same_argument():
    data = audit_solution(read_example("wrong_witnesses.txt"))

    same_argument = rubric_item_by_id(data, "same_f_argument")
    assert same_argument["detected"] is False
    assert same_argument["points"] == 0.0

    equal_values = rubric_item_by_id(data, "equal_g_values")
    assert equal_values["detected"] is False
    assert equal_values["points"] == 0.0

    generated = set(data["lean_certificate"]["generated_theorems"])
    assert "same_f_argument" not in generated
    assert "equal_g_values" not in generated
    assert "g_not_injective" not in generated
