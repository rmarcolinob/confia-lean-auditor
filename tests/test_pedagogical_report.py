from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from confia_lean_auditor.main import app


CLIENT = TestClient(app)


def read_f2q1_example(name: str) -> str:
    return Path(f"problems/ITA2025F2Q1/examples/{name}").read_text(encoding="utf-8")


def audit_f2q1(solution: str) -> dict:
    response = CLIENT.post(
        "/audit",
        json={
            "problem_id": "ITA2025F2Q1",
            "solution": solution,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def report_text(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False).lower()


def compact(text: str) -> str:
    return "".join(text.lower().split())


def test_f2q1_correct_solution_has_pedagogical_report():
    data = audit_f2q1(read_f2q1_example("correct_solution.txt"))

    assert isinstance(data["feedback"], str)
    assert data["feedback"]

    report = data["pedagogical_report"]
    text = report_text(report)

    assert "solução" in text
    assert "correta" in text
    assert "evidências" in text
    assert report["evidence_items"]
    assert any(item.get("evidence") for item in report["evidence_items"])
    assert "confiabilidade alta" in text
    assert "checagem automática" in text


def test_f2q1_wrong_solution_reports_incorrect_student_statements():
    solution = (
        "Como x^6=1, temos x^57=-1, x^14=1-x e x^7=x. "
        "Logo o resto é (a-b)x-a. Comparando com 2x+1, obtemos "
        "a+b=2 e a=1. Portanto, a=1 e b=1."
    )

    data = audit_f2q1(solution)
    report = data["pedagogical_report"]
    text = report_text(report)
    dense = compact(text)

    assert "incorreta" in text
    assert "checagem automática" in text
    assert "x^14=1-x" in dense
    assert "(a-b)x-a" in dense
    assert "a=1" in dense
    assert "b=1" in dense


def test_pedagogical_report_hides_technical_details():
    data = audit_f2q1(read_f2q1_example("correct_solution.txt"))
    text = report_text(data["pedagogical_report"])

    forbidden_terms = [
        "lean_statement",
        "stdout",
        "stderr",
        "compiled",
        "formal_steps",
        "microclaims",
        "attempt.lean",
    ]

    for term in forbidden_terms:
        assert term not in text

    assert "artifact_dir" not in data["pedagogical_report"]
    assert data["pedagogical_report"]["technical_record_available"] is True
    assert data["artifact_dir"] is None


def test_legacy_feedback_still_exists_with_pedagogical_report():
    data = audit_f2q1(read_f2q1_example("correct_solution.txt"))

    assert isinstance(data["feedback"], str)
    assert data["feedback"]
    assert data["pedagogical_report"] is not None
