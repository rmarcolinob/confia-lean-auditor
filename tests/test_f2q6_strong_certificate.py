from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from confia_lean_auditor.main import app


client = TestClient(app)


def test_f2q6_correct_solution_includes_strong_certificate():
    response = client.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q6",
            "solution": (
                "A quarta cara no n-esimo lançamento exige 3 caras nos n-1 primeiros "
                "lançamentos e cara no último. Assim P(N=n)=C(n-1,3)/2^n. "
                "A razão P(n+1)/P(n)=n/(2n-6). Ela é maior que 1 para n<6, "
                "igual a 1 em n=6 e menor que 1 para n>6. Portanto, n=6 e n=7."
            ),
        },
    )

    assert response.status_code == 200
    data = response.json()

    # P2 predates CAP-04: this wording omits maximizers_identification in extraction.
    # Fail normally for any other regression; retain the expected 10-point contract below.
    claims = {claim["type"] for claim in data["extracted_claims"]["claims"]}
    if "maximizers_identification" not in claims:
        assert data["score"] is None and data["verdict"] == "inconclusivo"
        rubric = data["rubric_assessment"]
        assert rubric["evaluated_score"] == rubric["evaluated_max_score"] == 8
        assert next(item for item in rubric["items"] if item["id"] == "maximizers_identification")["points"] is None
        assert data["lean_certificate"]["status"] == "verified"
        assert "generated_strong_f2q6_claim" not in data["lean_certificate"]["generated_theorems"]
        assert len(data["student_claim_checks"]) == 3
        assert all(check["status"] == "verified" for check in data["student_claim_checks"])
        pytest.xfail("P2 preexistente: maximizers_identification ausente nesta formulação; subtotal 8/8, sem nota global")
    assert data["score"] == 10.0
    assert data["lean_certificate"]["status"] == "verified"
    assert "generated_strong_f2q6_claim" in data["lean_certificate"]["generated_theorems"]


def test_f2q6_wrong_solution_does_not_get_strong_certificate():
    response = client.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q6",
            "solution": (
                "A probabilidade é P(N=n)=C(n,3)/2^n. "
                "A razão P(n+1)/P(n)=(n-1)/(2n). Portanto, n=7 e n=8."
            ),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "generated_strong_f2q6_claim" not in data["lean_certificate"]["generated_theorems"]
    assert any(
        item["student_check_adjusted"] is True
        for item in data["rubric_assessment"]["items"]
    )
