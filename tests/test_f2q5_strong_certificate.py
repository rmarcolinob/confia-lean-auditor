from __future__ import annotations

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


client = TestClient(app)


def test_f2q5_correct_solution_includes_strong_certificate():
    response = client.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q5",
            "solution": (
                "Temos log10(3^100)=100log10(3)=100*0,4771=47,7100. "
                "A mantissa é 0,7100. Além disso, log10(5)=0,6990 e "
                "log10(6)=0,7781, logo 0,6990<0,7100<0,7781. "
                "Portanto, o primeiro algarismo é 5."
            ),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"
    assert (
        "generated_strong_f2q5_claim"
        in data["lean_certificate"]["generated_theorems"]
    )


def test_f2q5_missing_bounds_does_not_include_strong_certificate():
    response = client.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q5",
            "solution": (
                "Temos log10(3^100)=100log10(3)=100*0,4771=47,7100. "
                "A mantissa é 0,7100. Portanto, o primeiro algarismo é 5."
            ),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert (
        "generated_strong_f2q5_claim"
        not in data["lean_certificate"]["generated_theorems"]
    )


def test_f2q5_wrong_final_digit_does_not_include_strong_certificate():
    response = client.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q5",
            "solution": (
                "Temos log10(3^100)=100log10(3)=100*0,4771=47,7100. "
                "A mantissa é 0,7100. Além disso, log10(5)=0,6990 e "
                "log10(6)=0,7781, logo 0,6990<0,7100<0,7781. "
                "Portanto, o primeiro algarismo é 6."
            ),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert (
        "generated_strong_f2q5_claim"
        not in data["lean_certificate"]["generated_theorems"]
    )
    assert any(
        item["student_check_adjusted"] is True
        for item in data["rubric_assessment"]["items"]
    )
