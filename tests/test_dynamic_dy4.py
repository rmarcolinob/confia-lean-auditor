"""DY4 controlled providers: blindness, adversarial opinions and immutable association."""

import json
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
import pytest
from test_dynamic_dy3 import (
    setup,
    prepared,
    grade,
    attempt,
    ACTOR,
    FACTOR,
    FORMULA,
    CRITERIA,
    QUESTION,
)
from confia_lean_auditor.dynamic.grading_context import resolve
from confia_lean_auditor.dynamic.reviewer import IndependentDynamicReviewer, blind_input
from confia_lean_auditor.dynamic.review_comparison import compare_review
from confia_lean_auditor.dynamic.review_models import BlindReviewProposal
from confia_lean_auditor.dynamic.review_service import DynamicReviewService
from confia_lean_auditor.dynamic.preparation_models import GenerationProvenance
from confia_lean_auditor.dynamic.provider import ProviderFailure
from confia_lean_auditor.submissions.integrity import canonical_sha256
from confia_lean_auditor.submission_audits.router import service
from confia_lean_auditor.dynamic.models import (
    CreateStatement,
    PreparationRequest,
    SaveRubric,
    ApproveRubric,
)
from confia_lean_auditor.dynamic.store import dynamic_store
from confia_lean_auditor.dynamic.preparation import PreparationService
from test_dynamic_dy2 import ControlledProvider as PreparationProvider


class ReviewerProvider:
    def __init__(
        self,
        points=("4", "3", "3"),
        refs=None,
        statuses=("COMPLETE",) * 3,
        extra=None,
        alternative=False,
        failure=False,
        callback=None,
    ):
        self.points = points
        self.refs = refs or [
            ["review_claim_1", "review_claim_2"],
            ["review_claim_3"],
            ["review_claim_4", "review_claim_5"],
        ]
        self.statuses = statuses
        self.extra = extra or []
        self.alternative = alternative
        self.failure = failure
        self.calls = []
        self.callback = callback

    def generate(self, payload, response_type):
        self.calls.append(deepcopy(payload))
        if self.callback:
            self.callback()
        if self.failure:
            raise ProviderFailure("CONTROLLED_FAILURE")
        raw = dict(
            detected_strategy=(
                "Fórmula quadrática" if self.alternative else "Álgebra exata"
            ),
            alternative_strategy=self.alternative,
            additional_claims=self.extra,
            criterion_reviews=[
                dict(
                    criterion_id=c["criterion_id"],
                    assessment=status,
                    proposed_points=points,
                    claim_ids=refs,
                    explanation="Obrigação confrontada com os trechos e verificações independentes.",
                    uncertainty=[],
                )
                for c, points, refs, status in zip(
                    payload["approved_rubric"]["criteria"],
                    self.points,
                    self.refs,
                    self.statuses,
                )
            ],
            warnings=[],
        )
        text = json.dumps(raw)
        meta = GenerationProvenance(
            provider="controlled-dy4",
            requested_model="independent-fixture",
            returned_model="independent-fixture-v1",
            reasoning_effort=None,
            prompt_version="dynamic-dy4-blind.v1",
            schema_version=response_type.__name__ + ".v1",
            input_sha256=canonical_sha256(payload),
            output_sha256=canonical_sha256(text),
            response_id=None,
            created_at=datetime.now(timezone.utc),
            code_sha=None,
            max_output_tokens=10000,
            raw_output=text,
        )
        return response_type.model_validate(raw), meta


def independent(root, d, text, provider):
    g = grade(root, d, text)
    ctx, statement, rubric, prep = resolve(d["problem"]["problem_id"], ACTOR, True)
    source = SimpleNamespace(
        solution_text=text,
        source_hash=g.analysis.source_sha256,
        transcription_id="tr_x",
        revision_number=1,
    )
    payload, equation, claims = blind_input(source, statement, rubric, prep, ctx)
    phase = IndependentDynamicReviewer(provider).analyze(
        payload, equation, claims, rubric
    )
    return g, phase, rubric


def altered(g, criterion, points, **updates):
    from confia_lean_auditor.dynamic.grading_models import DynamicAuditResult

    raw = g.model_dump(mode="json")
    d = next(x for x in raw["decisions"] if x["criterion_id"] == criterion)
    d.update(
        suggested_points=str(points),
        automation="AUTO_AWARD" if points else "AUTO_VETO",
        review_required=False,
        **updates,
    )
    raw["score"] = raw["suggested_score"] = float(
        sum(Decimal(x["suggested_points"]) for x in raw["decisions"])
    )
    return DynamicAuditResult.model_validate(raw)


def test_full_agreement_and_phase_a_has_no_grader_judgments(setup):
    root, _ = setup
    p = ReviewerProvider()
    g, phase, rubric = independent(root, prepared(), FACTOR, p)
    comparison = compare_review(g, phase, rubric, FACTOR)
    assert comparison.exact_agreement and comparison.agreement_count == 3
    forbidden = {
        "suggested_score",
        "score",
        "decisions",
        "bindings",
        "sufficiency",
        "suggested_points",
        "grader_points",
        "audit_run_id",
    }

    def inspect(x):
        if isinstance(x, dict):
            assert not forbidden.intersection(x)
            for v in x.values():
                inspect(v)
        elif isinstance(x, list):
            for v in x:
                inspect(v)

    inspect(p.calls[0])
    assert phase.provenance.input_sha256 == canonical_sha256(p.calls[0])
    assert phase.provenance.requested_model == "independent-fixture"


def test_alternative_formula_agrees_without_penalty(setup):
    root, _ = setup
    p = ReviewerProvider(
        refs=[
            ["review_claim_2", "review_claim_3"],
            ["review_claim_4"],
            ["review_claim_5", "review_claim_6"],
        ],
        alternative=True,
    )
    g, phase, rubric = independent(root, prepared(), FORMULA, p)
    assert compare_review(g, phase, rubric, FORMULA).exact_agreement


def test_partial_credit_is_reviewed_without_promoting_to_full(setup):
    root, _ = setup
    text = "y²-7y+12=0; y=3"
    p = ReviewerProvider(
        points=("0", "1.5", "0"),
        refs=[["review_claim_1"], ["review_claim_2"], []],
        statuses=("INSUFFICIENT", "PARTIAL", "INSUFFICIENT"),
    )
    g, phase, rubric = independent(root, prepared(), text, p)
    assert phase.criterion_reviews[1].proposed_points == Decimal("1.5")
    assert compare_review(g, phase, rubric, text).conflicting_criteria == []


def test_incorrect_has_no_false_missed_credit(setup):
    root, _ = setup
    p = ReviewerProvider(
        points=("0", "0", "0"),
        refs=[[], ["review_claim_1"], []],
        statuses=("INSUFFICIENT", "NOT_SATISFIED", "INSUFFICIENT"),
    )
    g, phase, rubric = independent(root, prepared(), "y=9", p)
    assert not any(
        "MISSED_CREDIT_SUSPECTED" in c.disagreement_types
        for c in compare_review(g, phase, rubric, "y=9").criteria
    )


@pytest.mark.parametrize(
    "text", ["talvez S={3,4}", "S={3,4}; não tenho certeza", "S={3,4}; S={3,5}"]
)
def test_ambiguous_or_conflicting_cannot_receive_reviewer_credit(setup, text):
    root, _ = setup
    p = ReviewerProvider(
        points=("0", "3", "0"),
        refs=[[], ["review_claim_1"], []],
        statuses=("INSUFFICIENT", "COMPLETE", "INSUFFICIENT"),
    )
    _, phase, _ = independent(root, prepared(), text, p)
    assert phase.review_required and phase.criterion_reviews[1].proposed_points is None


def test_adversarial_false_credit_final_answer_cannot_supply_argument(setup):
    root, _ = setup
    text = "S={3,4}"
    p = ReviewerProvider(
        points=("0", "3", "0"),
        refs=[[], ["review_claim_1"], []],
        statuses=("INSUFFICIENT", "COMPLETE", "INSUFFICIENT"),
    )
    g, phase, rubric = independent(root, prepared(), text, p)
    bad = altered(g, "method", 4, sufficiency="COMPLETE", claim_ids=["claim_1"])
    c = compare_review(bad, phase, rubric, text).criteria[0]
    assert {"FALSE_CREDIT_SUSPECTED", "BINDING_DISAGREEMENT"} <= set(
        c.disagreement_types
    )
    assert c.review_required


def test_adversarial_missed_alternative_credit(setup):
    root, _ = setup
    p = ReviewerProvider(
        refs=[
            ["review_claim_2", "review_claim_3"],
            ["review_claim_4"],
            ["review_claim_5", "review_claim_6"],
        ],
        alternative=True,
    )
    g, phase, rubric = independent(root, prepared(), FORMULA, p)
    bad = altered(g, "method", 0, sufficiency="NOT_SATISFIED")
    c = compare_review(bad, phase, rubric, FORMULA).criteria[0]
    assert {"MISSED_CREDIT_SUSPECTED", "STRATEGY_DISAGREEMENT"} <= set(
        c.disagreement_types
    )


def test_binding_disagreement_even_when_points_agree(setup):
    root, _ = setup
    g, phase, rubric = independent(root, prepared(), FACTOR, ReviewerProvider())
    bad = altered(g, "method", 4, claim_ids=["claim_3"])
    c = compare_review(bad, phase, rubric, FACTOR).criteria[0]
    assert c.difference == 0 and "BINDING_DISAGREEMENT" in c.disagreement_types
    assert not compare_review(bad, phase, rubric, FACTOR).exact_agreement


def test_adversarial_mathematical_conflict_and_wrong_representation(setup):
    root, _ = setup
    text = "y=9"
    p = ReviewerProvider(
        points=("0", "0", "0"),
        refs=[[], ["review_claim_1"], []],
        statuses=("INSUFFICIENT", "NOT_SATISFIED", "INSUFFICIENT"),
    )
    g, phase, rubric = independent(root, prepared(), text, p)
    bad = altered(g, "roots", 3, sufficiency="COMPLETE")
    bad.analysis.claims[0].normalized = "y=3"
    bad.analysis.claims[0].verification_status = "VERIFIED"
    c = compare_review(bad, phase, rubric, text).criteria[1]
    assert {
        "MATHEMATICAL_DISAGREEMENT",
        "BINDING_DISAGREEMENT",
        "FALSE_CREDIT_SUSPECTED",
    } <= set(c.disagreement_types)


def test_additional_omitted_claim_is_grounded_and_not_grader_decomposition(setup):
    root, _ = setup
    text = "Logo, S={3,4}"
    p = ReviewerProvider(
        points=("0", "3", "0"),
        refs=[[], ["extra_roots"], []],
        statuses=("INSUFFICIENT", "COMPLETE", "INSUFFICIENT"),
        extra=[dict(claim_id="extra_roots", start=6, end=len(text), quote="S={3,4}")],
    )
    g, phase, rubric = independent(root, prepared(), text, p)
    assert g.score == 0 and phase.additional_claims[0].text == "S={3,4}"
    assert (
        "MISSED_CREDIT_SUSPECTED"
        in compare_review(g, phase, rubric, text).criteria[1].disagreement_types
    )


@pytest.mark.parametrize("prefix", ["Se ", "Não é verdade que ", "Descarto: "])
def test_additional_claim_cannot_crop_away_discourse(setup, prefix):
    root, _ = setup
    text = prefix + "S={3,4}"
    p = ReviewerProvider(
        points=("0", "3", "0"),
        refs=[[], ["extra_roots"], []],
        statuses=("INSUFFICIENT", "COMPLETE", "INSUFFICIENT"),
        extra=[
            dict(
                claim_id="extra_roots",
                start=len(prefix),
                end=len(text),
                quote="S={3,4}",
            )
        ],
    )
    _, phase, _ = independent(root, prepared(), text, p)
    assert phase.rejected_claims and phase.criterion_reviews[1].proposed_points is None


def test_ungrounded_provider_points_do_not_become_reviewer_credit(setup):
    root, _ = setup
    p = ReviewerProvider(
        points=("4", "3", "0"),
        refs=[[], ["review_claim_1"], []],
        statuses=("COMPLETE", "COMPLETE", "INSUFFICIENT"),
    )
    _, phase, _ = independent(root, prepared(), "S={3,4}", p)
    assert phase.criterion_reviews[0].provider_proposed_points == 4
    assert phase.criterion_reviews[0].proposed_points is None


def test_follow_through_is_not_invented_and_independent_roots_survive(setup):
    root, _ = setup
    c = deepcopy(CRITERIA)
    c[2]["dependencies"] = ["method"]
    text = "(y-8)(y-9)=0; S={3,4}; 2*3^2-14*3+24=0"
    p = ReviewerProvider(
        points=("0", "3", "1.5"),
        refs=[["review_claim_1"], ["review_claim_2"], ["review_claim_3"]],
        statuses=("NOT_SATISFIED", "COMPLETE", "PARTIAL"),
    )
    _, phase, _ = independent(root, prepared(criteria=c), text, p)
    assert (
        phase.criterion_reviews[1].proposed_points == 3
        and phase.criterion_reviews[2].proposed_points is None
    )


def test_second_domain_linear(setup):
    root, _ = setup
    text = "3z=-6; z=-2; S={-2}; 3*(-2)+6=0"
    p = ReviewerProvider(
        refs=[
            ["review_claim_1"],
            ["review_claim_2", "review_claim_3"],
            ["review_claim_4"],
        ]
    )
    g, phase, rubric = independent(
        root, prepared("Resolva nos reais: 3z + 6 = 0."), text, p
    )
    assert compare_review(g, phase, rubric, text).exact_agreement


def audited(setup):
    root, client = setup
    d = prepared()
    case, base, req = attempt(client, d)
    r = client.post(base + "/audits", json=req)
    assert r.status_code == 200, r.text
    return root, client, d, case, r.json()


def test_associated_persistence_replay_hashes_events_and_audit_unchanged(
    setup, monkeypatch
):
    root, client, d, case, run = audited(setup)
    p = ReviewerProvider()
    import confia_lean_auditor.dynamic.router as router

    monkeypatch.setattr(
        router, "independent_review_service", lambda: DynamicReviewService(service(), p)
    )
    url = f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}/independent-reviews"
    original = (root / "audits" / f"{run['audit_run_id']}.json").read_bytes()
    r = client.post(url, json={"execution_key": "first"})
    assert r.status_code == 201, r.text
    view = r.json()
    review = view["review"]
    assert review["status"] == "COMPLETED" and review["comparison"]["exact_agreement"]
    assert (
        view["reconciliation"] is None
        and client.post(url, json={"execution_key": "first"}).json() == view
    )
    assert len(p.calls) == 1 and client.get(url).json() == [view]
    assert (root / "audits" / f"{run['audit_run_id']}.json").read_bytes() == original
    assert client.get(f"/tme/cases/{case['case_id']}/decision").json() is None
    assert {e["event_type"] for e in review["events"]} >= {
        "independent_review_started",
        "independent_review_completed",
        "grader_reviewer_agreement",
    }
    path = root / "audits" / "independent_reviews" / f"{review['review_id']}.json"
    raw = json.loads(path.read_text())
    raw["record"]["phase_a"]["detected_strategy"] = "tampered"
    path.write_text(json.dumps(raw))
    assert client.get(url).status_code == 409


@pytest.mark.parametrize("change", ["statement", "preparation", "rubric"])
def test_version_change_rejects_new_review_and_preserves_history(setup, change):
    root, client, d, case, run = audited(setup)
    store = dynamic_store()
    s = DynamicReviewService(service(), ReviewerProvider())
    from confia_lean_auditor.tme.store import case_store

    c = case_store().read(case["case_id"])
    view = s.execute(c, run["audit_run_id"], "first")
    pid = d["problem"]["problem_id"]
    if change == "statement":
        store.statement(
            pid,
            CreateStatement(
                expected_revision=d["revision"],
                statement="Resolva nos reais: y-7=0.",
                max_score="10",
            ),
            ACTOR,
        )
    elif change == "preparation":
        PreparationService(store, PreparationProvider()).start(
            pid,
            PreparationRequest(
                expected_revision=d["revision"], reason="Nova preparação"
            ),
            ACTOR,
        )
    else:
        store.save_rubric(
            pid,
            SaveRubric(
                expected_revision=d["revision"],
                statement_version=1,
                max_score="10",
                criteria=CRITERIA,
            ),
            ACTOR,
            base_id=d["rubrics"][-1]["rubric_id"],
        )
    with pytest.raises(ValueError):
        s.execute(c, run["audit_run_id"], "second")
    assert s.list(c, run["audit_run_id"])[0]["stale"]


def test_change_during_provider_call_cannot_publish(setup):
    root, client, d, case, run = audited(setup)
    from confia_lean_auditor.tme.store import case_store

    def change():
        dynamic_store().statement(
            d["problem"]["problem_id"],
            CreateStatement(
                expected_revision=d["revision"],
                statement="Resolva nos reais: y-7=0.",
                max_score="10",
            ),
            ACTOR,
        )

    s = DynamicReviewService(service(), ReviewerProvider(callback=change))
    with pytest.raises(ValueError):
        s.execute(case_store().read(case["case_id"]), run["audit_run_id"], "racing")
    assert not list((root / "audits" / "independent_reviews").glob("drev_*.json"))


def test_provider_failure_is_persisted_inconclusive_without_score_change(setup):
    root, client, d, case, run = audited(setup)
    from confia_lean_auditor.tme.store import case_store

    view = DynamicReviewService(service(), ReviewerProvider(failure=True)).execute(
        case_store().read(case["case_id"]), run["audit_run_id"], "failure"
    )
    assert view["review"]["status"] == "FAILED" and view["review_required"]
    assert (
        view["review"]["comparison"] is None
        and service().get(run["audit_run_id"]).result.score == 10
    )


def test_auxiliary_arithmetic_and_conclusion_do_not_replace_development(setup):
    root, _ = setup
    p = ReviewerProvider(
        refs=[
            ["review_claim_1", "review_claim_2", "review_claim_3", "review_claim_4"],
            ["review_claim_4"],
            ["review_claim_5", "review_claim_6"],
        ],
        alternative=True,
    )
    g, phase, rubric = independent(root, prepared(), FORMULA, p)
    assert compare_review(g, phase, rubric, FORMULA).exact_agreement


def test_provider_out_of_range_and_bad_provenance_are_rejected(setup):
    root, _ = setup
    d = prepared()
    with pytest.raises(ProviderFailure):
        independent(root, d, FACTOR, ReviewerProvider(points=("999", "3", "3")))


def test_specialized_cannot_route_to_dynamic_reviewer(setup):
    root, client = setup
    r = client.post(
        "/tme/cases",
        json={
            "problem_id": "ITA2025F2Q1",
            "source_mode": "IMAGE_SCAN",
            "external_candidate_ref": "S1",
        },
    )
    assert r.status_code == 201, r.text
    s = DynamicReviewService(service(), ReviewerProvider())
    from confia_lean_auditor.tme.store import case_store

    fake = SimpleNamespace(
        source=SimpleNamespace(dynamic_context=None),
        submission_id=None,
        status="COMPLETED",
    )
    s.audits._read = lambda _: fake
    with pytest.raises(ValueError):
        s.audit_for(case_store().read(r.json()["case_id"]), "aud_x")


def test_review_endpoint_requires_owner_and_explicit_dynamic_demo(setup, monkeypatch):
    root, client, d, case, run = audited(setup)
    url = f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}/independent-reviews"
    monkeypatch.setenv("CONFIA_DYNAMIC_DEMO_ENABLED", "0")
    assert client.post(url, json={"execution_key": "first"}).status_code == 409
    monkeypatch.setenv("CONFIA_TME_DEMO_NO_AUTH", "0")
    assert client.get(url).status_code == 401


def test_transcription_revision_makes_independent_review_stale(setup):
    root, client, d, case, run = audited(setup)
    from confia_lean_auditor.tme.store import case_store

    c = case_store().read(case["case_id"])
    s = DynamicReviewService(service(), ReviewerProvider())
    s.execute(c, run["audit_run_id"], "first")
    response = client.post(
        f"/tme/cases/{case['case_id']}/transcriptions/{run['transcription_id']}/revisions",
        json=dict(
            reviewer_reference="test",
            based_on_revision_number=1,
            segments=[
                dict(
                    segment_id="text:0", page_index=0, order=0, kind="text", text="y=9"
                )
            ],
        ),
    )
    assert response.status_code == 201, response.text
    assert s.list(c, run["audit_run_id"])[0]["stale"]
    with pytest.raises(ValueError):
        s.execute(c, run["audit_run_id"], "new")


def test_extra_pedagogical_deduction_cannot_penalize_valid_alternative(setup):
    root, _ = setup
    p = ReviewerProvider(
        points=("2", "3", "3"),
        refs=[
            ["review_claim_2", "review_claim_3"],
            ["review_claim_4"],
            ["review_claim_5", "review_claim_6"],
        ],
        alternative=True,
    )
    g, phase, rubric = independent(root, prepared(), FORMULA, p)
    assert phase.criterion_reviews[0].provider_proposed_points == 2
    assert phase.criterion_reviews[0].proposed_points is None
    row = compare_review(g, phase, rubric, FORMULA).criteria[0]
    assert (
        row.difference is None
        and "FALSE_CREDIT_SUSPECTED" not in row.disagreement_types
    )
    assert row.review_required and g.score == 10


def test_false_provider_provenance_cannot_be_persisted_as_complete(setup):
    root, client, d, case, run = audited(setup)
    from confia_lean_auditor.tme.store import case_store

    class Untrusted(ReviewerProvider):
        def generate(self, *args):
            proposal, meta = super().generate(*args)
            return proposal, meta.model_copy(update={"input_sha256": "a" * 64})

    result = DynamicReviewService(service(), Untrusted()).execute(
        case_store().read(case["case_id"]), run["audit_run_id"], "untrusted"
    )
    assert result["review"]["status"] == "FAILED"
    assert result["review"]["error_code"] == "REVIEWER_PROVENANCE_MISMATCH"


def test_other_owner_is_denied_before_provider_call(setup):
    root, client, d, case, run = audited(setup)
    from confia_lean_auditor.main import app
    from confia_lean_auditor.tme.auth import require_tme_evaluator, TMEEvaluator

    app.dependency_overrides[require_tme_evaluator] = lambda: TMEEvaluator(
        "another-teacher"
    )
    try:
        url = f"/dynamic/attempts/{case['case_id']}/audits/{run['audit_run_id']}/independent-reviews"
        assert client.get(url).status_code == 403
        assert client.post(url, json={"execution_key": "denied"}).status_code == 403
    finally:
        app.dependency_overrides.pop(require_tme_evaluator, None)


@pytest.mark.parametrize(
    "mode,event",
    [
        ("over", "possible_false_credit_detected"),
        ("under", "possible_missed_credit_detected"),
    ],
)
def test_adversarial_grader_test_double_events_preserve_original_audit(
    setup, monkeypatch, mode, event
):
    from confia_lean_auditor.dynamic.grader import DynamicSolutionGrader
    from confia_lean_auditor.tme.store import case_store
    from pathlib import Path

    original_grade = DynamicSolutionGrader.grade

    def faulty(self, *args, **kwargs):
        result = original_grade(self, *args, **kwargs)
        result = altered(
            result,
            "method",
            4 if mode == "over" else 0,
            sufficiency="COMPLETE" if mode == "over" else "NOT_SATISFIED",
            claim_ids=["claim_1"],
        )
        Path(result.artifact_dir, "audit.json").write_text(
            result.model_dump_json(indent=2)
        )
        return result

    monkeypatch.setattr(DynamicSolutionGrader, "grade", faulty)
    root, client = setup
    d = prepared()
    text = "S={3,4}" if mode == "over" else FACTOR
    case, base, req = attempt(client, d, text)
    run = client.post(base + "/audits", json=req).json()
    assert run["status"] == "COMPLETED"
    provider = (
        ReviewerProvider(
            points=("0", "3", "0"),
            refs=[[], ["review_claim_1"], []],
            statuses=("INSUFFICIENT", "COMPLETE", "INSUFFICIENT"),
        )
        if mode == "over"
        else ReviewerProvider()
    )
    raw = (root / "audits" / f"{run['audit_run_id']}.json").read_bytes()
    review = DynamicReviewService(service(), provider).execute(
        case_store().read(case["case_id"]), run["audit_run_id"], "adversarial"
    )["review"]
    assert event in {e["event_type"] for e in review["events"]}
    assert (root / "audits" / f"{run['audit_run_id']}.json").read_bytes() == raw
    assert review["comparison"]["review_required"]
