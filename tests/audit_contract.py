"""Consumer assertions for a final score versus an unscaled decided subtotal."""
import pytest


def assert_score_contract(data):
    rubric = data["rubric_assessment"]
    items = rubric["items"]
    decided = [item for item in items if item["points"] is not None]
    pending = [item for item in items if item["points"] is None]
    subtotal = sum(item["points"] for item in decided)
    decided_max = sum(item["max_points"] for item in decided)
    assert rubric["evaluated_score"] == pytest.approx(subtotal)
    assert rubric["evaluated_max_score"] == pytest.approx(decided_max)
    assert data["max_score"] == rubric["max_score"]
    for item in decided:
        assert 0 <= item["points"] <= item["max_points"]
        assert item["mathematical_status"] in {"supported", "refuted"}
    for item in pending:
        assert item["mathematical_status"] == "indeterminate"
    if pending:
        assert data["score"] is None and rubric["score"] is None
        assert data["verdict"] == "inconclusivo"
        assert rubric["assessment_status"] in {"partial", "indeterminate"}
    else:
        assert isinstance(data["score"], (int, float))
        assert 0 <= data["score"] <= data["max_score"]
        assert data["score"] == rubric["score"] == pytest.approx(subtotal)
        assert rubric["assessment_status"] == "complete"
    report = data["pedagogical_report"]
    assert report["score"] == data["score"]
    assert report["verdict"] == data["verdict"]
    assert report["evaluated_score"] == pytest.approx(subtotal)
    assert report["evaluated_max_score"] == pytest.approx(decided_max)


def assert_incomplete(data, subtotal, decided_max):
    assert_score_contract(data)
    assert data["score"] is None
    assert data["verdict"] == "inconclusivo"
    assert any(item["points"] is None for item in data["rubric_assessment"]["items"])
    assert data["rubric_assessment"]["evaluated_score"] == pytest.approx(subtotal)
    assert data["rubric_assessment"]["evaluated_max_score"] == pytest.approx(decided_max)
