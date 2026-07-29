from __future__ import annotations

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


client = TestClient(app)


def test_f2q3_correct_solution_includes_strong_certificate():
    response = client.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q3",
            "solution": (
                "Das equações, obtemos cos beta - sin beta = 1/2. "
                "Logo sin beta = -(sqrt(7)+1)/4, cos beta = (1-sqrt(7))/4, "
                "sin alpha = -sqrt(7)/4 e cos alpha = -3/4. "
                "Esses valores satisfazem sen^2+cos^2=1. "
                "Assim, sin(alpha+beta)=sin alpha cos beta + cos alpha sin beta = "
                "(5+sqrt(7))/8. Portanto, resposta = (5+sqrt(7))/8."
            ),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"
    assert (
        "generated_strong_f2q3_claim"
        in data["lean_certificate"]["generated_theorems"]
    )


def test_f2q3_final_answer_alone_does_not_include_strong_certificate():
    response = client.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q3",
            "solution": "Portanto, resposta = (5+sqrt(7))/8.",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert (
        "generated_strong_f2q3_claim"
        not in data["lean_certificate"]["generated_theorems"]
    )


def test_f2q3_wrong_solution_does_not_include_strong_certificate():
    response = client.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q3",
            "solution": (
                "Das equações, obtemos cos beta - sin beta = -1/2. "
                "Temos sin beta = (sqrt(7)+1)/4, cos beta = (sqrt(7)-1)/4, "
                "sin alpha = sqrt(7)/4 e cos alpha = 3/4. "
                "Assim, sin(alpha+beta)=1/2. Portanto, resposta = 1/2."
            ),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert (
        "generated_strong_f2q3_claim"
        not in data["lean_certificate"]["generated_theorems"]
    )
    assert any(
        item["student_check_adjusted"] is True
        for item in data["rubric_assessment"]["items"]
    )
