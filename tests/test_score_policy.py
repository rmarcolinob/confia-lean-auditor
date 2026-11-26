"""Suggestion scoring must not invent mathematical verification or human grades."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from confia_lean_auditor.core.schemas import AuditResponse, ClaimExtraction, RubricAssessment, RubricItemResult
from confia_lean_auditor.core.problem_assets import validate_problem_assets
from confia_lean_auditor.rubric.scoring_policy import apply_scoring_policy
from confia_lean_auditor.rubric import secondary_adjudicator as secondary
from confia_lean_auditor.reports.report_builder import build_pedagogical_report, verdict_from_score

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "artifacts/evaluations/ita1000_v1_2/smoke_20261027_stage2/results"


def inputs(statuses, technical=False):
    items = [RubricItemResult(id=f"c{i}", description=f"Official criterion {i}",
        detected=status == "supported", points=2.0 if status == "supported" else 0.0 if status == "refuted" else None,
        max_points=2.0, mathematical_status=status, verification_status="technical_error" if technical else "available")
        for i, status in enumerate(statuses)]
    assets = SimpleNamespace(problem=SimpleNamespace(model_dump=lambda **_: {"statement": "Explain the given equality"}),
        rubric=SimpleNamespace(items=items, model_dump=lambda **_: {"items": [i.model_dump() for i in items]}))
    return dict(rubric=RubricAssessment(score=None, max_score=2*len(items), items=items),
        solution="Uma igualdade e sua justificativa.", assets=assets,
        claim_extraction=ClaimExtraction(problem_id="test", claims=[]), microclaims=[], student_claim_checks=[],
        technical_issue=technical)


def fake_provider(monkeypatch, credit=True):
    calls = []
    def provider(payload):
        calls.append(copy.deepcopy(payload))
        return {c["id"]: {"suggested_points": c["max_points"] if credit else 0.0,
                "evidence": [payload["solution_text"][:800]], "decision": "award" if credit else "deny",
                "rationale": secondary.rationale_options(c)["award" if credit else "deny"][0]}
            for c in payload["pending_criteria"]}, {"provider": "unit-test"}
    monkeypatch.setattr(secondary, "adjudicate", provider)
    return calls


@pytest.mark.parametrize("statuses,credit,score,coverage,estimated,review", [
    (["supported", "supported"], True, 4, 1, 0, False),
    (["supported", "indeterminate"], True, 4, .5, 2, True),
    (["indeterminate", "indeterminate"], True, 4, 0, 4, True),
    (["supported", "indeterminate"], False, 2, .5, 0, True),
    (["indeterminate", "indeterminate"], False, 0, 0, 0, True),
    (["refuted", "supported"], True, 2, 1, 0, False),
    (["refuted", "refuted"], True, 0, 1, 0, False),
    (["refuted", "indeterminate"], True, 2, .5, 2, True),
])
def test_scoring_contract(monkeypatch, statuses, credit, score, coverage, estimated, review):
    calls = fake_provider(monkeypatch, credit)
    data = inputs(statuses)
    originals = [(i.points, i.mathematical_status, i.verification_status) for i in data["rubric"].items]
    result = apply_scoring_policy(**data)
    assert result.score == score
    assert result.coverage == coverage
    assert result.estimated_points == estimated
    assert result.needs_review is review
    assert [(i.points, i.mathematical_status, i.verification_status) for i in result.items] == originals
    assert result.evaluated_score == sum(i.points for i in result.items if i.points is not None)
    assert sum(i.suggested_points for i in result.items) == score
    for i in result.items:
        assert i.verified_points == i.points
        assert i.suggested_points in {0, i.max_points}
        if i.points is None:
            assert i.scoring_basis == "secondary_adjudication" and i.scoring_evidence and i.scoring_rationale
        if i.mathematical_status == "refuted":
            assert i.suggested_points == 0
    assert bool(calls) is ("indeterminate" in statuses)
    trace=secondary.artifact_trace(result)
    for item,entry in zip(result.items,trace["criteria"]):
        assert entry["validation_status"] == ("accepted" if item.scoring_basis=="secondary_adjudication" else "not_requested")
        if item.scoring_basis=="secondary_adjudication":
            assert entry["rationale"]==item.scoring_rationale and entry["evidence"]==item.scoring_evidence
    if calls:
        assert all(c["id"] not in {i.id for i in result.items if i.points is not None}
                   for c in calls[0]["pending_criteria"])


def test_technical_failure_still_scores_and_requests_review(monkeypatch):
    fake_provider(monkeypatch)
    r = apply_scoring_policy(**inputs(["supported", "indeterminate"], technical=True))
    assert r.score == 4 and r.needs_review and r.coverage == .5
    assert all(i.verification_status == "technical_error" for i in r.items)


@pytest.mark.parametrize("solution,reason", [("", "EMPTY_SOLUTION"), (" \n\t", "EMPTY_SOLUTION")])
def test_empty_input_is_explicitly_unscorable(monkeypatch, solution, reason):
    calls = fake_provider(monkeypatch)
    data = inputs(["indeterminate"]); data["solution"] = solution
    r = apply_scoring_policy(**data)
    assert r.score is None and r.unscorable_reason == reason and not calls


def test_provider_unavailable_does_not_invent_zero():
    r = apply_scoring_policy(**inputs(["supported", "indeterminate"]))
    assert r.score is None and r.evaluated_score == 2
    assert r.unscorable_reason == "ADJUDICATOR_UNAVAILABLE" and r.needs_review
    assert r.items[1].suggested_points is None


def test_invalid_rubric_is_unscorable():
    r = apply_scoring_policy(**inputs([]))
    assert r.score is None and r.unscorable_reason == "INVALID_RUBRIC"


@pytest.mark.parametrize("change,error", [
    ({"suggested_points": 1}, "ADJUDICATOR_INVALID_POINTS"),
    ({"suggested_points": True}, "ADJUDICATOR_INVALID_POINTS"),
    ({"suggested_points": float('nan')}, "ADJUDICATOR_INVALID_POINTS"),
    ({"evidence": ["invented quote"]}, "ADJUDICATOR_INVALID_EVIDENCE"),
    ({"evidence": []}, "ADJUDICATOR_INVALID_EVIDENCE"),
    ({"rationale": " "}, "ADJUDICATOR_MISSING_RATIONALE"),
])
def test_untrusted_adjudication_rejected_atomically(monkeypatch, change, error):
    def invalid(payload):
        criterion=payload["pending_criteria"][0]
        return {"c1": dict(suggested_points=2, evidence=[payload["solution_text"]], decision="award",
                           rationale=secondary.rationale_options(criterion)["award"][0]) | change}, {}
    monkeypatch.setattr(secondary, "adjudicate", invalid)
    r = apply_scoring_policy(**inputs(["supported", "indeterminate"]))
    assert r.score is None and r.unscorable_reason == error
    assert r.items[0].suggested_points == 2 and r.items[1].suggested_points is None


def test_cannot_overwrite_refuted_or_add_criterion(monkeypatch):
    monkeypatch.setattr(secondary, "adjudicate", lambda p: ({"c0": {"suggested_points": 2}, "c1": {}}, {}))
    r = apply_scoring_policy(**inputs(["refuted", "indeterminate"]))
    assert r.score is None and r.unscorable_reason == "ADJUDICATOR_INVALID_CRITERIA"
    assert r.items[0].suggested_points == 0 and r.items[0].mathematical_status == "refuted"


@pytest.mark.parametrize("credit,expected", [(True, "correto"), (False, "incorreto")])
def test_report_keeps_numeric_suggestion_without_verification(monkeypatch, credit, expected):
    fake_provider(monkeypatch, credit)
    r = apply_scoring_policy(**inputs(["indeterminate", "indeterminate"]))
    report = build_pedagogical_report(score=r.score, max_score=r.max_score,
        verdict=verdict_from_score(r.score, r.max_score), rubric=r, student_claims=[], student_claim_checks=[],
        microclaims=[], artifact_dir=None)
    assert report.score == r.score and report.verdict == expected
    assert report.needs_review and report.coverage == 0
    assert "Sugestão ConfIA" in report.summary and "decisão oficial" in report.summary
    assert all(i.result == "pontuação sugerida" for i in report.evidence_items)


def test_f2q5_original_text_regression(monkeypatch):
    path = BASELINE / "ITA2025F2Q5_S003_L04.json"
    if not path.exists():
        pytest.skip("Local synthetic corpus fixture unavailable")
    raw = json.loads(path.read_text()); result = AuditResponse.model_validate(raw)
    assets = validate_problem_assets(ROOT / "problems/ITA2025F2Q5", "ITA2025F2Q5")
    text = (ROOT / "dataset_1000_v1.2/respostas/ITA2025F2Q5_S003_L04.txt").read_text()
    calls = fake_provider(monkeypatch)
    r = apply_scoring_policy(rubric=result.rubric_assessment, solution=text, assets=assets,
        claim_extraction=result.extracted_claims, microclaims=result.microclaims,
        student_claim_checks=result.student_claim_checks)
    assert r.score == 10 and r.evaluated_score == 8 and r.coverage == .8 and r.estimated_points == 2
    assert calls[0]["solution_text"] == text
    assert [c["id"] for c in calls[0]["pending_criteria"]] == ["final_digit"]
    assert r.items[-1].points is None and r.items[-1].mathematical_status == "indeterminate"


def test_legacy_result_roundtrip_does_not_change_digest():
    path = ROOT / "tests/fixtures/rich_audit_response.json"
    raw = json.loads(path.read_text())
    # Normalize the old schema once, then require additive fields to stay absent.
    loaded = AuditResponse.model_validate(raw)
    serialized = loaded.model_dump(mode="json")
    assert "scoring_policy" not in serialized and "coverage" not in serialized
    assert "coverage" not in serialized["rubric_assessment"]
    assert all("suggested_points" not in i for i in serialized["rubric_assessment"]["items"])
    if BASELINE.exists():
        for path in BASELINE.glob("*.json"):
            old = json.loads(path.read_text())
            assert AuditResponse.model_validate(old).model_dump(mode="json") == old
