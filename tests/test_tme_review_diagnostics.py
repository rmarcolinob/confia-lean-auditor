"""Projection regressions: synthetic rules and explicitly identified archives.

No real audit/provider execution. Local P2–P5 runs are read-only optional inputs;
the portable P1 archive and synthetic contracts always run in CI.
"""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from confia_lean_auditor import main
from confia_lean_auditor.rubric.pauta import PautaEngine, PautaEvidence
from confia_lean_auditor.semantic_policy.tme import MinimalEvidencePolicy
from confia_lean_auditor.submission_audits import router
from confia_lean_auditor.submission_audits.schemas import AuditRun, QuestionAuditContext
from confia_lean_auditor.tme.review_diagnostics import diagnose_run, project_pauta
from test_pauta_engine import atom, config, evaluate, evidence
from test_tme_archived_quote_scope import FIXTURE, archived, replay

ROOT = Path(__file__).resolve().parents[1]
RUNS = (
    "aud_1eb247481575591afe015612b9bcab6b98943d338347f5ce36da598eabaa019e",
    "aud_6f7e8d0a116941fe22164444b60ecbd0c71e1e227c4a6c244528fafc5eed1808",
    "aud_b78d47c5651567e96939a38cd3ac76b1ead85eb9e5cde1a308360ae687067ee6",
    "aud_00e84780b3c5556e82c092d34fbc66f8af67da2b398b1860da19b88366433bb2",
    "aud_e840502ea785c0ff3469e187a2f2d53831f8a9eba6f281ac9805103b0d230c93",
)


def combine(strategy, cap, *children):
    return dict(id="item", max_points=cap, scoring_strategy=strategy, children=children)


def project(cfg, *records):
    a = PautaEngine().evaluate(cfg, PautaEvidence(problem_id=cfg.problem_id,
        solution_id="SYNTHETIC_DIAGNOSTIC_CONTROL", obligations=records),
        evidence_policy=MinimalEvidencePolicy())
    before = a.model_dump_json()
    d = project_pauta(cfg, a, semantic_policy="semantic-b-minimal.v1")
    assert a.model_dump_json() == before
    return a, d


def ids(rows):
    return {o["obligation_id"] for o in rows}


def run_view(result, **kwargs):
    # Synthetic envelope only; mathematical content is the unmodified P1 archive.
    return SimpleNamespace(result=result, status="COMPLETED", audit_run_id=RUNS[0],
                           problem_id="TME2026P1", result_sha256="a" * 64,
                           source_hash="b" * 64, **kwargs)


@pytest.mark.parametrize("strategy", ["max_of", "banded"])
def test_full_score_with_dispensable_alternative(strategy):
    cfg = config(combine(strategy, 10, atom("official", 10, "x"), atom("other", 10, "y")))
    a, d = project(cfg, evidence("x"))
    assert a.score == 10 and a.needs_review  # Legacy flag intentionally preserved.
    assert d["score_state"] == "determined" and d["final_score"] == "10"
    assert d["mathematical_pending"]["state"] == "absent"
    assert ids(d["dispensable_alternatives"]) == {"y"}
    assert d["human_review"]["required"] is None


def test_partial_score_is_determined_by_refutation_not_missing_evidence():
    cfg = config(combine("additive", 10, atom("first", 4, "x"), atom("second", 6, "y")))
    a, d = project(cfg, evidence("x"), evidence("y", "refuted"))
    assert a.score == 4 and not a.needs_review
    assert d["final_score"] == "4" and d["score_state"] == "determined"
    assert d["nonblocking_pending"] == []
    assert d["mathematical_pending"]["state"] == "absent"
    assert d["human_review"]["state"] == "unknown"  # false legacy flag is not permission.


@pytest.mark.parametrize("status", ["indeterminate", "technical_error"])
def test_unselected_alternative_may_still_determine_credit(status):
    cfg = config(combine("max_of", 10, atom("selected", 4, "x"), atom("other", 10, "y")))
    a, d = project(cfg, evidence("x"), evidence("y", status))
    assert a.items[0].selected_method_path == "selected"
    assert d["score_state"] == "undetermined" and d["final_score"] is None
    assert (d["known_points"], d["possible_points"]) == ("4", "10")
    assert d["mathematical_pending"]["obligation_ids"] == ["y"]
    assert d["dispensable_alternatives"] == []
    assert bool(d["technical_errors"]) == (status == "technical_error")


@pytest.mark.parametrize("decision,status,score", [("met", "supported", "10"), ("not_met", "refuted", "0"),
                                                  ("review", "indeterminate", None), ("review", "technical_error", None)])
def test_semantic_review_is_distinct_from_mathematical_uncertainty(decision, status, score):
    cfg = config(atom("item", 10, "x"))
    e = evidence("x", status, origin="semantic", verification_source="semantic", grounding_status="grounded",
                 metadata={"semantic_fallback": {"policy": "semantic-b-minimal.v1", "decision": decision}})
    a, d = project(cfg, e)
    assert a.needs_review and d["final_score"] == score
    assert d["score_state"] == ("determined" if score is not None else "undetermined")
    assert d["mathematical_pending"]["state"] == ("absent" if score is not None else "present")
    assert d["semantic_evidence_review"]["state"] == "present"
    assert d["semantic_evidence_review"]["occurrences"][0]["decision_conclusive"] == (score is not None)
    assert d["human_review"]["required"] is None


def test_explicit_exam_requirement_is_not_a_claim_about_human_confirmation():
    old = archived()[0]
    context = QuestionAuditContext(assessment_id="synthetic-assessment", participant_id="synthetic-participant",
        exam_submission_id="synthetic-exam", question_attempt_id="synthetic-case", max_score=20)
    d = diagnose_run(run_view(old, question_context=context))
    assert d["human_review"]["required"] is True
    assert d["human_review"]["scope"] == "current_exam_finalization"
    assert d["human_review"]["confirmation_state"] == "unknown"
    assert d["human_review"]["rule_id"] == "tme.finalization.current_human_decision"
    assert diagnose_run(run_view(old))["human_review"]["required"] is None


@pytest.mark.parametrize("prior,blocking", [("supported", False), ("refuted", True), ("indeterminate", True)])
def test_carry_forward_requires_a_proven_prior_error(prior, blocking):
    cfg = config(dict(id="cf", max_points=2, scoring_strategy="carry_forward", carry_forward=dict(
        prior_obligation_id="prior", adoption_obligation_id="adoption",
        dependency_obligation_id="dependency", coherence_obligation_id="coherence")),
        obligations=("prior", "adoption", "dependency", "coherence"))
    a, d = project(cfg, evidence("prior", prior))
    assert (d["score_state"] == "undetermined") == blocking
    if blocking:
        assert d["final_score"] is None and d["mathematical_pending"]["state"] == "present"
    else:
        assert a.score == 0 and d["final_score"] == "0"
        assert {o["reason"] for o in d["nonblocking_pending"]} == {"CARRY_FORWARD_INAPPLICABLE_PRIOR_SUPPORTED"}
        assert ids(d["nonblocking_pending"]) == {"adoption", "dependency", "coherence"}


@pytest.mark.parametrize("status", ["indeterminate", "technical_error"])
def test_withhold_never_turns_an_open_interval_into_a_final_zero(status):
    cfg = config(atom("item", 10, "x"), policy="withhold")
    a, d = project(cfg, evidence("x", status))
    assert a.score == (None if status == "technical_error" else 0)
    assert d["score_state"] == "undetermined" and d["final_score"] is None
    assert d["mathematical_pending"]["obligation_ids"] == ["x"]


def test_disjunction_conjunction_and_additive_caps_do_not_hide_technical_errors():
    any_cfg = config(atom("item", 10, "x", "y", strategy="any_of"))
    _, d = project(any_cfg, evidence("x"), evidence("y", "technical_error"))
    assert d["final_score"] == "10" and ids(d["dispensable_alternatives"]) == {"y"}
    assert d["technical_errors"][0]["affects_score"] is False
    all_cfg = config(atom("item", 10, "x", "y"))
    _, d = project(all_cfg, evidence("x", "refuted"), evidence("y", "technical_error"))
    assert d["final_score"] == "0" and d["dispensable_alternatives"] == []
    assert d["nonblocking_pending"][0]["reason"] == "REFUTED_CONJUNCTION"
    cap_cfg = config(combine("additive", 10, atom("first", 10, "x"), atom("second", 6, "y")))
    _, d = project(cap_cfg, evidence("x"), evidence("y", "technical_error"))
    assert d["final_score"] == "10"
    assert d["nonblocking_pending"][0]["reason"] == "ADDITIVE_CAP_REACHED"


def test_same_obligation_can_be_nonblocking_and_relevant_in_different_paths():
    cfg = config(combine("additive", 20, atom("either", 10, "x", "y", strategy="any_of"),
                         atom("required", 10, "y")))
    _, d = project(cfg, evidence("x"))
    assert d["mathematical_pending"]["obligation_ids"] == ["y"]
    assert ids(d["dispensable_alternatives"]) == {"y"}
    assert d["mathematical_pending"]["occurrences"][0]["rule_path"] == ["item", "required"]


def test_unknown_data_is_not_a_favorable_diagnosis():
    cfg = config(atom("item", 10, "x"))
    a = evaluate(cfg, evidence("x"))
    assert project_pauta(cfg, a, semantic_policy="future-policy")["score_state"] == "unknown"
    changed = cfg.model_copy(update={"title": "Different pauta"})
    assert project_pauta(changed, a)["score_state"] == "unknown"
    broken = a.model_copy(update={"items": (a.items[0].model_copy(update={"obligations": ()}),)})
    assert project_pauta(cfg, broken)["score_state"] == "unknown"
    failed = run_view(None)
    failed.status = "FAILED"
    d = diagnose_run(failed)
    assert d["score_state"] == "unknown" and d["final_score"] is None
    assert d["reason"] == "AUDIT_NOT_COMPLETED"


def test_portable_p1_original_and_real_archived_replay_remain_distinct(monkeypatch):
    files = {p: p.read_bytes() for p in FIXTURE.iterdir() if p.is_file()}
    old, updated, assessment, provider = replay()
    assert len(provider.calls) == 13
    current = old.model_copy(update={"bridge": updated, "assessment": assessment})
    def forbidden(*args, **kwargs):
        pytest.fail("The projection must not invoke scoring or a provider")
    monkeypatch.setattr(PautaEngine, "evaluate", forbidden)
    original_json, replay_json = old.model_dump_json(), current.model_dump_json()
    historical = diagnose_run(run_view(old))
    repaired = diagnose_run(run_view(current))
    assert historical["legacy"]["score"] is None
    assert historical["mathematical_pending"]["obligation_ids"] == ["d.middle_choices"]
    assert {o["obligation_id"]: o["affects_score"] for o in historical["technical_errors"]} == {
        "c.no_extraneous_values": False, "d.middle_choices": True}
    assert repaired["final_score"] == "17" and repaired["score_state"] == "determined"
    assert repaired["legacy"] == dict(status="COMPLETED", score=17.0, needs_review=True, verdict="inconclusivo")
    assert repaired["semantic_evidence_review"]["state"] == "present"
    assert len(repaired["semantic_evidence_review"]["occurrences"]) == 13
    assert repaired["technical_errors"] == [] and repaired["human_review"]["required"] is None
    assert old.model_dump_json() == original_json and current.model_dump_json() == replay_json
    assert all(p.read_bytes() == data for p, data in files.items())


def test_p1_resume_keeps_nonblocking_historical_technical_error():
    old, bridge, a, provider = replay(resume=True)
    d = diagnose_run(run_view(old.model_copy(update={"bridge": bridge, "assessment": a})))
    assert provider.calls == ["d.middle_choices"] and d["final_score"] == "17"
    assert [(o["obligation_id"], o["affects_score"]) for o in d["technical_errors"]] == [
        ("c.no_extraneous_values", False)]


@pytest.mark.parametrize("number,run_id,nonblocking", zip(range(1, 6), RUNS, [4, 2, 1, 5, 5]))
def test_local_p1_to_p5_records_and_artifacts_are_unchanged(number, run_id, nonblocking):
    path = ROOT / "runtime/pilot-dec10/submission_audits" / f"{run_id}.json"
    if not path.is_file():
        pytest.skip("Local pilot audit unavailable; portable P1 and synthetic regressions still run")
    original = path.read_bytes()
    run = AuditRun.model_validate_json(original)  # Existing validators, not an audit execution.
    before = run.model_dump_json()
    artifacts = {}
    for entry in run.required_artifacts:
        p = Path(entry.file)
        data = p.read_bytes()
        assert len(data) == entry.byte_size and hashlib.sha256(data).hexdigest() == entry.sha256
        artifacts[p] = data
    d = diagnose_run(run)
    assert d["legacy"]["score"] == (None if number == 1 else 20.0)
    assert d["legacy"]["needs_review"] and d["legacy"]["verdict"] == "inconclusivo"
    assert d["score_state"] == ("undetermined" if number == 1 else "determined")
    assert len(ids(d["nonblocking_pending"])) == nonblocking
    assert d["human_review"]["required"] is None
    if number != 1:
        assert d["final_score"] == "20" and d["mathematical_pending"]["state"] == "absent"
        assert d["semantic_evidence_review"]["state"] == "absent"
        assert d["technical_errors"] == []
    assert run.model_dump_json() == before and path.read_bytes() == original
    assert all(p.read_bytes() == data for p, data in artifacts.items())


def test_read_endpoint_is_additive_sanitized_and_never_executes_audit(monkeypatch):
    saved = archived()[0]
    before = saved.model_dump_json()
    view = run_view(saved, stale=True)
    calls = []
    def get(identifier):
        calls.append(identifier)
        if identifier != RUNS[0]:
            raise FileNotFoundError()
        return view
    monkeypatch.setattr(router, "service", lambda: SimpleNamespace(get=get))
    monkeypatch.setattr(main, "execute_audit", lambda _: pytest.fail("Read-only endpoint"))
    client = TestClient(main.app)
    response = client.get(f"/submission-audits/{RUNS[0]}/diagnostics")
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    d = response.json()
    assert d["stale"] is True and d["source_result_sha256"] == "a" * 64
    assert d["mathematical_pending"]["obligation_ids"] == ["d.middle_choices"]
    assert "artifact_dir" not in d and "/Users/" not in response.text
    assert client.get("/submission-audits/missing/diagnostics").status_code == 404
    assert calls == [RUNS[0], "missing"] and saved.model_dump_json() == before
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "1")
    assert client.get(f"/submission-audits/{RUNS[0]}/diagnostics").status_code == 401
    assert calls == [RUNS[0], "missing"]
