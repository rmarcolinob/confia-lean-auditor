"""DY5 authority/policy fixtures. No API dependency."""

from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace
import pytest
from test_dynamic_dy3 import setup, prepared, FACTOR, FORMULA, CRITERIA
from test_dynamic_dy4 import ReviewerProvider, independent, altered, audited
from confia_lean_auditor.dynamic.reconciliation import reconcile_criteria
from confia_lean_auditor.dynamic.review_comparison import compare_review
from confia_lean_auditor.dynamic.grading_context import resolve
from test_dynamic_dy3 import ACTOR


def reconciled(
    root,
    text=FACTOR,
    provider=None,
    profile="FORMATIVE_LIST",
    change=None,
    criteria=None,
    question=None,
):
    d = prepared(**({"question": question} if question else {}), criteria=criteria)
    g, phase, rubric = independent(root, d, text, provider or ReviewerProvider())
    if change:
        g = change(g)
    review = SimpleNamespace(
        phase_a=phase,
        comparison=compare_review(g, phase, rubric, text),
        status="COMPLETED",
    )
    statement = resolve(d["problem"]["problem_id"], ACTOR, True)[1]
    return reconcile_criteria(g, review, statement, rubric, text, profile)


@pytest.mark.parametrize("profile", ["FORMATIVE_LIST", "SCHOOL_EXAM"])
def test_correct_agreement_is_supported(setup, profile):
    rows = reconciled(setup[0], profile=profile)
    assert {r.automation for r in rows} == {"AUTO_ACCEPT"}
    assert {r.status for r in rows} == {"AGREEMENT_SUPPORTED"}
    assert sum(r.reconciled_points for r in rows) == 10


@pytest.mark.parametrize(
    "profile,action,points",
    [("FORMATIVE_LIST", "AUTO_ADJUST_UP", 4), ("SCHOOL_EXAM", "REVIEW_ONLY", 0)],
)
def test_verified_missed_credit_is_profile_dependent(setup, profile, action, points):
    p = ReviewerProvider(
        refs=[
            ["review_claim_2", "review_claim_3"],
            ["review_claim_4"],
            ["review_claim_5", "review_claim_6"],
        ],
        alternative=True,
    )
    rows = reconciled(
        setup[0],
        FORMULA,
        p,
        profile,
        lambda g: altered(g, "method", 0, sufficiency="NOT_SATISFIED"),
    )
    assert rows[0].automation == action and rows[0].reconciled_points == points
    assert rows[0].status == "GRADER_MISSED_CREDIT_CONFIRMED"
    assert rows[0].recovered_credit == points
    assert rows[1].automation == "AUTO_ACCEPT" and rows[2].automation == "AUTO_ACCEPT"


@pytest.mark.parametrize(
    "profile,action,points",
    [("FORMATIVE_LIST", "AUTO_ADJUST_DOWN", 0), ("SCHOOL_EXAM", "REVIEW_ONLY", 3)],
)
def test_refuted_claim_false_credit_is_profile_dependent(
    setup, profile, action, points
):
    p = ReviewerProvider(
        points=("0", "0", "0"),
        refs=[[], ["review_claim_1"], []],
        statuses=("INSUFFICIENT", "NOT_SATISFIED", "INSUFFICIENT"),
    )
    rows = reconciled(
        setup[0],
        "y=9",
        p,
        profile,
        lambda g: altered(g, "roots", 3, sufficiency="COMPLETE"),
    )
    assert rows[1].automation == action and rows[1].reconciled_points == points
    assert rows[1].status == "GRADER_FALSE_CREDIT_CONFIRMED"
    assert rows[1].points_removed == 3 - points


def test_both_agree_wrong_cannot_override_checker(setup, monkeypatch):
    import confia_lean_auditor.dynamic.reconciliation as module

    original = module.independent_limit

    def authoritative(c, *args):
        if c.criterion_id == "roots":
            return Decimal(0), "NOT_SATISFIED", []
        return original(c, *args)

    monkeypatch.setattr(module, "independent_limit", authoritative)
    rows = reconciled(setup[0])
    assert rows[1].automation == "REVIEW_ONLY" and rows[1].reconciled_points == 3
    assert rows[1].review_required


def test_final_answer_truth_does_not_supply_argument(setup):
    p = ReviewerProvider(
        points=("4", "3", "0"),
        refs=[[], ["review_claim_1"], []],
        statuses=("COMPLETE", "COMPLETE", "INSUFFICIENT"),
    )
    rows = reconciled(
        setup[0],
        "S={3,4}",
        p,
        change=lambda g: altered(
            g, "method", 4, sufficiency="COMPLETE", claim_ids=["claim_1"]
        ),
    )
    assert (
        rows[0].status == "SUFFICIENCY_DISAGREEMENT"
        and rows[0].automation == "REVIEW_ONLY"
    )
    assert rows[0].reconciled_points == 4 and rows[1].automation == "AUTO_ACCEPT"


@pytest.mark.parametrize("status", ["ERROR", "NOT_ATTEMPTED", "REVIEW_ONLY"])
def test_unavailable_checker_is_not_refutation(setup, monkeypatch, status):
    import confia_lean_auditor.dynamic.reconciliation as module

    original = module.evidence_inventory

    def unavailable(*args):
        eq, claims, warnings = original(*args)
        for claim in claims:
            claim.verification_status = status
        return eq, claims, warnings

    monkeypatch.setattr(module, "evidence_inventory", unavailable)
    rows = reconciled(setup[0])
    assert {r.automation for r in rows} == {"REVIEW_ONLY"}
    assert sum(r.reconciled_points for r in rows) == 10
    if status == "ERROR":
        assert all(
            r.technical_uncertainty and r.status == "TECHNICAL_ERROR" for r in rows
        )


@pytest.mark.parametrize("text", ["talvez S={3,4}", "S={3,4}; S={3,5}"])
def test_discourse_conflict_stays_review_only(setup, text):
    p = ReviewerProvider(
        points=("0", "3", "0"),
        refs=[[], ["review_claim_1"], []],
        statuses=("INSUFFICIENT", "COMPLETE", "INSUFFICIENT"),
    )
    rows = reconciled(setup[0], text, p)
    assert (
        rows[1].automation == "REVIEW_ONLY"
        and rows[1].status == "MATHEMATICAL_CONFLICT"
    )


def test_follow_through_is_not_invented_independent_credit_survives(setup):
    c = deepcopy(CRITERIA)
    c[2]["dependencies"] = ["method"]
    p = ReviewerProvider(
        points=("0", "3", "1.5"),
        refs=[["review_claim_1"], ["review_claim_2"], ["review_claim_3"]],
        statuses=("NOT_SATISFIED", "COMPLETE", "PARTIAL"),
    )
    rows = reconciled(setup[0], "(y-8)(y-9)=0; S={3,4}; 2*3^2-14*3+24=0", p, criteria=c)
    assert rows[1].automation == "AUTO_ACCEPT" and rows[1].reconciled_points == 3
    assert rows[2].automation == "REVIEW_ONLY"


def test_second_domain_linear(setup):
    p = ReviewerProvider(
        refs=[
            ["review_claim_1"],
            ["review_claim_2", "review_claim_3"],
            ["review_claim_4"],
        ]
    )
    rows = reconciled(
        setup[0],
        "3z=-6; z=-2; S={-2}; 3*(-2)+6=0",
        p,
        question="Resolva nos reais: 3z+6=0.",
    )
    assert {r.automation for r in rows} == {"AUTO_ACCEPT"}


def test_unknown_rubric_obligation_cannot_auto_adjust(setup):
    c = deepcopy(CRITERIA)
    c[0]["description"] = "Apresente uma explicação conceitual completa."
    rows = reconciled(setup[0], criteria=c)
    assert rows[0].automation == "REVIEW_ONLY"


def test_failed_review_preserves_numeric_grade(setup):
    root, _ = setup
    d = prepared()
    g, phase, rubric = independent(root, d, FACTOR, ReviewerProvider())
    rows = reconcile_criteria(
        g,
        SimpleNamespace(phase_a=None, comparison=None, status="FAILED"),
        resolve(d["problem"]["problem_id"], ACTOR, True)[1],
        rubric,
        FACTOR,
        "FORMATIVE_LIST",
    )
    assert sum(r.reconciled_points for r in rows) == 10
    assert all(r.automation == "REVIEW_ONLY" and r.technical_uncertainty for r in rows)


@pytest.fixture(autouse=True)
def isolate_assessments(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIA_ASSESSMENTS_DIR", str(tmp_path / "assessments"))


def chain(
    setup,
    monkeypatch,
    profile="FORMATIVE_LIST",
    text=FACTOR,
    provider=None,
    change=None,
):
    from pathlib import Path
    from test_dynamic_dy3 import attempt
    from confia_lean_auditor.dynamic.grader import DynamicSolutionGrader
    from confia_lean_auditor.dynamic.review_service import DynamicReviewService
    from confia_lean_auditor.submission_audits.router import service
    import confia_lean_auditor.dynamic.router as router

    if change:
        original = DynamicSolutionGrader.grade

        def controlled(self, *args, **kwargs):
            result = change(original(self, *args, **kwargs))
            Path(result.artifact_dir, "audit.json").write_text(
                result.model_dump_json(indent=2)
            )
            return result

        monkeypatch.setattr(DynamicSolutionGrader, "grade", controlled)
    root, client = setup
    d = prepared()
    case, base, request = attempt(client, d, text)
    response = client.post(base + "/audits", json=request)
    assert response.status_code == 200, response.text
    run = response.json()
    prefix = f"/dynamic/attempts/{case['case_id']}"
    url = prefix + f"/audits/{run['audit_run_id']}"
    monkeypatch.setattr(
        router,
        "independent_review_service",
        lambda: DynamicReviewService(service(), provider or ReviewerProvider()),
    )
    response = client.post(
        url + "/independent-reviews", json={"execution_key": "review"}
    )
    assert response.status_code == 201, response.text
    review = response.json()["review"]
    response = client.post(prefix + "/policy", json={"policy_profile": profile})
    assert response.status_code == 201, response.text
    response = client.post(
        url + "/reconciliations", json={"independent_review_id": review["review_id"]}
    )
    assert response.status_code == 201, response.text
    return (
        root,
        client,
        case,
        base,
        url,
        run,
        review,
        response.json()["reconciliation"],
        request,
    )


def test_integrated_immutable_chain_policy_provenance_and_replay(setup, monkeypatch):
    import json
    from confia_lean_auditor.submissions.integrity import canonical_sha256

    root, client, case, base, url, run, review, r, request = chain(setup, monkeypatch)
    auditpath = root / "audits" / f"{run['audit_run_id']}.json"
    reviewpath = root / "audits/independent_reviews" / f"{review['review_id']}.json"
    before = (auditpath.read_bytes(), reviewpath.read_bytes())
    assert r["reconciled_suggested_score"] == "10" and not r["review_required"]
    assert r["provenance"]["source_sha256"] == run["source_hash"]
    assert (
        r["policy_profile"] == "FORMATIVE_LIST"
        and r["policy_version"] == "dynamic-safe-automation.v1"
    )
    assert (
        client.post(
            url + "/reconciliations",
            json={"independent_review_id": review["review_id"]},
        ).json()["reconciliation"]
        == r
    )
    assert client.get(url + "/reconciliations").json() == [
        {"reconciliation": r, "stale": False}
    ]
    assessment = json.loads(
        (root / "assessments" / f"{r['assessment_id']}.json").read_text()
    )
    assert assessment["assessment"]["dynamic_policy_profile"] == "FORMATIVE_LIST"
    assert (auditpath.read_bytes(), reviewpath.read_bytes()) == before
    assert {e["event_type"] for e in r["events"]} == {
        "dynamic_reconciliation_started",
        "criterion_auto_accepted",
        "dynamic_reconciliation_completed",
    }
    assert (
        client.post(
            f"/dynamic/attempts/{case['case_id']}/policy",
            json={"policy_profile": "SCHOOL_EXAM"},
        ).status_code
        == 409
    )
    path = root / "audits/reconciliations" / f"{r['reconciliation_id']}.json"
    raw = json.loads(path.read_text())
    raw["data"]["reconciled_suggested_score"] = "9"
    path.write_text(json.dumps(raw))
    assert client.get(url + "/reconciliations").status_code == 409


@pytest.mark.parametrize(
    "profile,score", [("FORMATIVE_LIST", "10"), ("SCHOOL_EXAM", "6")]
)
def test_integrated_recovered_credit_and_human_suggestion(
    setup, monkeypatch, profile, score
):
    import json

    root, client, case, base, url, run, review, r, request = chain(
        setup,
        monkeypatch,
        profile=profile,
        change=lambda g: altered(g, "method", 0, sufficiency="NOT_SATISFIED"),
    )
    assert (
        r["grader_score_snapshot"] == "6.0" and r["reconciled_suggested_score"] == score
    )
    assert (
        client.post(
            base + "/decision",
            json={
                "audit_run_id": run["audit_run_id"],
                "max_points": 10,
                "final_points": 10,
            },
        ).status_code
        == 409
    )
    body = {
        "audit_run_id": run["audit_run_id"],
        "reconciliation_id": r["reconciliation_id"],
        "max_points": 10,
        "final_points": float(score),
    }
    response = client.post(base + "/decision", json=body)
    assert response.status_code == 201, response.text
    d = response.json()
    assert (
        Decimal(d["suggested_points"]) == Decimal(score)
        and Decimal(d["grader_suggested_points"]) == 6
    )
    assert (
        d["reconciliation_id"] == r["reconciliation_id"]
        and d["independent_review_id"] == review["review_id"]
    )
    assert d["transcription_version_id"] == r["transcription_version_id"]
    assert client.post(base + "/decision", json=body).json() == d
    assert client.get(base + "/decision").json() == d
    # Replaying the same independent review must not invalidate a confirmation
    # or replace the projected reconciled score with the original grader score.
    replay = client.post(url + "/independent-reviews", json={"execution_key": "review"})
    assert (
        replay.status_code == 201
        and replay.json()["review"]["review_id"] == review["review_id"]
    )
    queued = client.get("/tme/cases?view=queue").json()["items"][0]
    assert (
        queued["suggested_score"] == float(score)
        and queued["operational_status"] == "finalized"
    )
    from confia_lean_auditor.tme.home_summary import rebuild_index

    rebuild_index()
    queued = client.get("/tme/cases?view=queue").json()["items"][0]
    assert (
        queued["suggested_score"] == float(score)
        and queued["operational_status"] == "finalized"
    )

    assert client.get(f"/dynamic/attempts/{case['case_id']}/human-decisions").json()[0][
        "current"
    ]
    assert (
        json.loads((root / "audits" / f"{run['audit_run_id']}.json").read_text())[
            "result"
        ]["score"]
        == 6
    )


def test_adjustment_needs_reason_and_preserves_reconciled_snapshot(setup, monkeypatch):
    _, client, case, base, url, run, review, r, _ = chain(setup, monkeypatch)
    body = {
        "audit_run_id": run["audit_run_id"],
        "reconciliation_id": r["reconciliation_id"],
        "max_points": 10,
        "final_points": 8,
    }
    assert client.post(base + "/decision", json=body).status_code == 422
    body["override_reason"] = "Avaliador identificou lacuna na explicação."
    response = client.post(base + "/decision", json=body)
    assert response.status_code == 201, response.text
    assert (
        Decimal(response.json()["suggested_points"]) == 10
        and Decimal(response.json()["final_points"]) == 8
    )


@pytest.mark.parametrize("change", ["transcription", "audit", "review"])
def test_current_chain_and_human_confirmation_invalidate(setup, monkeypatch, change):
    _, client, case, base, url, run, review, r, request = chain(setup, monkeypatch)
    body = {
        "audit_run_id": run["audit_run_id"],
        "reconciliation_id": r["reconciliation_id"],
        "max_points": 10,
        "final_points": 10,
    }
    assert client.post(base + "/decision", json=body).status_code == 201
    if change == "transcription":
        response = client.post(
            base + f"/transcriptions/{run['transcription_id']}/revisions",
            json={
                "reviewer_reference": "test",
                "based_on_revision_number": 1,
                "segments": [
                    {
                        "segment_id": "text:0",
                        "page_index": 0,
                        "order": 0,
                        "kind": "text",
                        "text": "y=9",
                    }
                ],
            },
        )
    elif change == "audit":
        response = client.post(
            base + "/audits", json={**request, "execution_key": "another"}
        )
    else:
        response = client.post(
            url + "/independent-reviews", json={"execution_key": "new-review"}
        )
    assert response.status_code in (200, 201), response.text
    assert client.get(url + "/reconciliations").json()[0]["stale"]
    assert client.get(base + "/decision").json() is None
    assert (
        client.get("/tme/cases?view=queue").json()["items"][0]["operational_status"]
        != "finalized"
    )
    history = client.get(f"/dynamic/attempts/{case['case_id']}/human-decisions").json()
    assert len(history) == 1 and not history[0]["current"]
    assert client.post(base + "/decision", json=body).status_code == 409
    assert (
        client.post(
            url + "/reconciliations",
            json={"independent_review_id": review["review_id"]},
        ).status_code
        == 409
    )


def test_failed_reviewer_can_only_preserve_score_with_technical_review(
    setup, monkeypatch
):
    _, _, _, _, _, _, _, r, _ = chain(
        setup, monkeypatch, provider=ReviewerProvider(failure=True)
    )
    assert (
        r["technical_uncertainty"]
        and r["review_required"]
        and r["reconciled_suggested_score"] == "10"
    )
    assert all(c["automation"] == "REVIEW_ONLY" for c in r["criteria"])


def test_reconciliation_owner_and_specialized_guards(setup, monkeypatch):
    from confia_lean_auditor.main import app
    from confia_lean_auditor.tme.auth import require_tme_evaluator, TMEEvaluator

    _, client, case, base, url, run, review, r, _ = chain(setup, monkeypatch)
    app.dependency_overrides[require_tme_evaluator] = lambda: TMEEvaluator(
        "other-owner"
    )
    try:
        assert client.get(url + "/reconciliations").status_code == 403
        assert (
            client.post(
                url + "/reconciliations",
                json={"independent_review_id": review["review_id"]},
            ).status_code
            == 403
        )
    finally:
        app.dependency_overrides.pop(require_tme_evaluator, None)
    special = client.post(
        "/tme/cases",
        json={
            "problem_id": "ITA2025F2Q1",
            "external_candidate_ref": "S1",
            "source_mode": "IMAGE_SCAN",
        },
    ).json()
    assert (
        client.post(
            f"/dynamic/attempts/{special['case_id']}/policy",
            json={"policy_profile": "FORMATIVE_LIST"},
        ).status_code
        == 409
    )


def test_checker_resolves_binding_but_only_with_independent_sufficiency(setup):
    rows = reconciled(
        setup[0],
        change=lambda g: altered(
            g, "method", 4, sufficiency="COMPLETE", claim_ids=["claim_3"]
        ),
    )
    assert rows[0].status == "CHECKER_RESOLVED" and rows[0].automation == "AUTO_ACCEPT"
    exam = reconciled(
        setup[0] / "exam",
        profile="SCHOOL_EXAM",
        change=lambda g: altered(
            g, "method", 4, sufficiency="COMPLETE", claim_ids=["claim_3"]
        ),
    )
    assert exam[0].automation == "REVIEW_ONLY"


def test_actual_refuted_source_overrides_fabricated_consensus(setup):
    root, _ = setup
    d = prepared()
    p = ReviewerProvider(
        points=("0", "0", "0"),
        refs=[[], ["review_claim_1"], []],
        statuses=("INSUFFICIENT", "NOT_SATISFIED", "INSUFFICIENT"),
    )
    g, phase, rubric = independent(root, d, "y=9", p)
    g = altered(g, "roots", 3, sufficiency="COMPLETE")
    opinions = list(phase.criterion_reviews)
    opinions[1] = opinions[1].model_copy(
        update={
            "proposed_points": Decimal(3),
            "provider_proposed_points": Decimal(3),
            "sufficiency": "COMPLETE",
            "review_required": False,
            "uncertainty": [],
        }
    )
    phase = phase.model_copy(update={"criterion_reviews": opinions})
    review = SimpleNamespace(
        phase_a=phase,
        comparison=compare_review(g, phase, rubric, "y=9"),
        status="COMPLETED",
    )
    rows = reconcile_criteria(
        g,
        review,
        resolve(d["problem"]["problem_id"], ACTOR, True)[1],
        rubric,
        "y=9",
        "FORMATIVE_LIST",
    )
    assert (
        rows[1].status == "MATHEMATICAL_CONFLICT"
        and rows[1].automation == "REVIEW_ONLY"
    )
    assert (
        rows[1].reconciled_points == 3
        and rows[1].mathematical_verification[0].verification_status == "REFUTED"
    )


def test_additional_faithful_claim_can_recover_missed_credit(setup):
    text = "Logo, S={3,4}"
    p = ReviewerProvider(
        points=("0", "3", "0"),
        refs=[[], ["extra_roots"], []],
        statuses=("INSUFFICIENT", "COMPLETE", "INSUFFICIENT"),
        extra=[dict(claim_id="extra_roots", start=6, end=len(text), quote="S={3,4}")],
    )
    rows = reconciled(setup[0], text, p)
    assert rows[1].automation == "AUTO_ADJUST_UP" and rows[1].recovered_credit == 3


def test_no_adjustment_on_unverified_alternative(setup):
    p = ReviewerProvider(
        points=("2", "3", "3"),
        refs=[
            ["review_claim_2", "review_claim_3"],
            ["review_claim_4"],
            ["review_claim_5", "review_claim_6"],
        ],
        alternative=True,
    )
    rows = reconciled(setup[0], FORMULA, p)
    assert rows[0].automation == "REVIEW_ONLY" and rows[0].reconciled_points == 4
    assert rows[0].status == "SUFFICIENCY_DISAGREEMENT"


def test_unknown_policy_and_out_of_bounds_contract_rejected(setup):
    from confia_lean_auditor.dynamic.reconciliation import SafeAutomationPolicy
    from confia_lean_auditor.dynamic.reconciliation_models import (
        CriterionReconciliation,
    )

    with pytest.raises(ValueError):
        SafeAutomationPolicy("guess-from-title")
    row = reconciled(setup[0])[0].model_dump()
    row["reconciled_points"] = 5
    with pytest.raises(ValueError):
        CriterionReconciliation.model_validate(row)
    row.update(
        reconciled_points=3,
        points_removed=1,
        automation="REVIEW_ONLY",
        review_required=True,
    )
    with pytest.raises(ValueError):
        CriterionReconciliation.model_validate(row)


def test_new_activity_profile_is_explicit_and_published(setup):
    root, client = setup
    d = prepared()
    response = client.post(
        f"/dynamic/problems/{d['problem']['problem_id']}/attempts",
        json=dict(
            external_candidate_ref="LISTA-1",
            solution=FACTOR,
            allow_preparation_review=True,
            policy_profile="SCHOOL_EXAM",
        ),
    )
    assert response.status_code == 201, response.text
    case = response.json()
    view = client.get(f"/dynamic/attempts/{case['case_id']}/policy").json()
    assert (
        view["policy_profile"] == "SCHOOL_EXAM"
    )  # The name LISTA never selects the policy.
    assert (root / "assessments" / f"{view['assessment_id']}.json").is_file()


@pytest.mark.parametrize("change", ["statement", "rubric", "preparation"])
def test_context_version_invalidates_reconciliation_and_confirmation(
    setup, monkeypatch, change
):
    from confia_lean_auditor.dynamic.store import dynamic_store
    from confia_lean_auditor.dynamic.models import (
        CreateStatement,
        SaveRubric,
        PreparationRequest,
    )
    from confia_lean_auditor.dynamic.preparation import PreparationService
    from test_dynamic_dy2 import ControlledProvider

    _, client, case, base, url, run, review, r, _ = chain(setup, monkeypatch)
    body = dict(
        audit_run_id=run["audit_run_id"],
        reconciliation_id=r["reconciliation_id"],
        max_points=10,
        final_points=10,
    )
    assert client.post(base + "/decision", json=body).status_code == 201
    store = dynamic_store()
    d = store.get(case["problem_id"], ACTOR)
    rev = d["revision"]
    if change == "statement":
        store.statement(
            case["problem_id"],
            CreateStatement(
                expected_revision=rev,
                statement="Resolva nos reais: y-3=0.",
                max_score="10",
            ),
            ACTOR,
        )
    elif change == "rubric":
        store.save_rubric(
            case["problem_id"],
            SaveRubric(
                expected_revision=rev,
                statement_version=1,
                max_score="10",
                criteria=CRITERIA,
            ),
            ACTOR,
            base_id=d["rubrics"][-1]["rubric_id"],
        )
    else:
        PreparationService(store, ControlledProvider()).start(
            case["problem_id"],
            PreparationRequest(expected_revision=rev, reason="Nova preparação"),
            ACTOR,
        )
    assert client.get(url + "/reconciliations").json()[0]["stale"]
    assert client.get(base + "/decision").json() is None
    assert client.post(base + "/decision", json=body).status_code == 409


def test_no_published_profile_no_reconciliation(setup, monkeypatch):
    from confia_lean_auditor.dynamic.reconciliation_service import ReconciliationService
    from confia_lean_auditor.tme.store import case_store
    from confia_lean_auditor.submission_audits.router import service
    from confia_lean_auditor.dynamic.review_service import DynamicReviewService

    root, client, d, case, run = audited(setup)
    c = case_store().read(case["case_id"])
    review = DynamicReviewService(service(), ReviewerProvider()).execute(
        c, run["audit_run_id"], "r"
    )["review"]
    with pytest.raises(ValueError, match="Configure explicitamente"):
        ReconciliationService(service()).execute(
            c, run["audit_run_id"], review["review_id"]
        )


def test_inflight_transcription_edit_cannot_publish_reconciliation(setup, monkeypatch):
    import confia_lean_auditor.dynamic.reconciliation_service as module
    from confia_lean_auditor.dynamic.review_service import DynamicReviewService
    from confia_lean_auditor.submission_audits.router import service
    from confia_lean_auditor.tme.store import case_store

    root, client, d, case, run = audited(setup)
    c = case_store().read(case["case_id"])
    review = DynamicReviewService(service(), ReviewerProvider()).execute(
        c, run["audit_run_id"], "r"
    )["review"]
    module.configure_activity(c, "FORMATIVE_LIST")
    original = module.reconcile_criteria

    def edit(*args):
        rows = original(*args)
        response = client.post(
            f"/tme/cases/{case['case_id']}/transcriptions/{run['transcription_id']}/revisions",
            json={
                "reviewer_reference": "test",
                "based_on_revision_number": 1,
                "segments": [
                    {
                        "segment_id": "text:0",
                        "page_index": 0,
                        "order": 0,
                        "kind": "text",
                        "text": "y=9",
                    }
                ],
            },
        )
        assert response.status_code == 201
        return rows

    monkeypatch.setattr(module, "reconcile_criteria", edit)
    with pytest.raises(ValueError):
        module.ReconciliationService(service()).execute(
            c, run["audit_run_id"], review["review_id"]
        )
    assert not list((root / "audits/reconciliations").glob("drec_*.json"))


@pytest.mark.parametrize(
    "kind,points,refs,uncertainty,expected",
    [
        ([], "3", ["review_claim_3"], ["Fonte ainda ambígua"], "AGREEMENT_UNVERIFIED"),
        (
            ["STRATEGY_DISAGREEMENT"],
            "2",
            ["review_claim_3"],
            ["Estratégia não resolvida"],
            "STRATEGY_DISAGREEMENT",
        ),
        ([], None, [], ["Sem vínculo de evidência"], "INSUFFICIENT_EVIDENCE"),
        ([], "2", ["review_claim_3"], ["Cobertura em revisão"], "REVIEW_REQUIRED"),
    ],
)
def test_unresolved_interpretations_preserve_points_and_independent_criteria(
    setup, kind, points, refs, uncertainty, expected
):
    d = prepared()
    g, phase, rubric = independent(setup[0], d, FACTOR, ReviewerProvider())
    opinions = list(phase.criterion_reviews)
    opinions[1] = opinions[1].model_copy(
        update={
            "proposed_points": Decimal(points) if points is not None else None,
            "claim_ids": refs,
            "uncertainty": uncertainty,
            "review_required": True,
        }
    )
    phase = phase.model_copy(update={"criterion_reviews": opinions})
    comparison = compare_review(g, phase, rubric, FACTOR)
    comparisons = list(comparison.criteria)
    comparisons[1] = comparisons[1].model_copy(update={"disagreement_types": kind})
    review = SimpleNamespace(
        phase_a=phase,
        comparison=comparison.model_copy(update={"criteria": comparisons}),
        status="COMPLETED",
    )
    rows = reconcile_criteria(
        g,
        review,
        resolve(d["problem"]["problem_id"], ACTOR, True)[1],
        rubric,
        FACTOR,
        "FORMATIVE_LIST",
    )
    assert rows[1].status == expected
    assert rows[1].automation == "REVIEW_ONLY" and rows[1].reconciled_points == 3
    assert rows[0].automation == rows[2].automation == "AUTO_ACCEPT"


def test_rebuilt_queue_preserves_confirmation_after_new_audit(setup, monkeypatch):
    from confia_lean_auditor.tme.home_summary import rebuild_index

    _, client, case, base, url, run, review, r, request = chain(setup, monkeypatch)
    newer = client.post(
        base + "/audits", json={**request, "execution_key": "newer"}
    ).json()
    url = f"/dynamic/attempts/{case['case_id']}/audits/{newer['audit_run_id']}"
    review = client.post(
        url + "/independent-reviews", json={"execution_key": "newer"}
    ).json()["review"]
    r = client.post(
        url + "/reconciliations", json={"independent_review_id": review["review_id"]}
    ).json()["reconciliation"]
    response = client.post(
        base + "/decision",
        json=dict(
            audit_run_id=newer["audit_run_id"],
            reconciliation_id=r["reconciliation_id"],
            max_points=10,
            final_points=10,
        ),
    )
    assert response.status_code == 201, response.text
    rebuild_index()
    queued = client.get("/tme/cases?view=queue").json()["items"][0]
    assert (
        queued["operational_status"] == "finalized" and queued["suggested_score"] == 10
    )
