from __future__ import annotations

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


client = TestClient(app)


def test_f2q1_correct_solution_includes_strong_certificate():
    response = client.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q1",
            "solution": (
                "Como x^3=-1 e x^6=1, temos x^57=-1, x^14=x-1 e x^7=x. "
                "Logo o resto é (a+b)x-a. Comparando com 2x+1, obtemos "
                "a+b=2 e -a=1. Portanto, a=-1 e b=3."
            ),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"
    assert "generated_strong_f2q1_claim" in data["lean_certificate"]["generated_theorems"]


def test_f2q1_wrong_solution_does_not_get_strong_certificate():
    response = client.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q1",
            "solution": (
                "Como x^6=1, temos x^57=-1, x^14=1-x e x^7=x. "
                "Logo o resto é (a-b)x-a. Comparando com 2x+1, obtemos "
                "a+b=2 e a=1. Portanto, a=1 e b=1."
            ),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["score"] == 0.0
    assert "generated_strong_f2q1_claim" not in data["lean_certificate"]["generated_theorems"]
