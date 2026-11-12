"""DY3: network-free evidence gates and the real shared submission/AuditRun path."""

from copy import deepcopy
from types import SimpleNamespace
from decimal import Decimal
from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient
from confia_lean_auditor.main import app
from confia_lean_auditor.dynamic.models import (
    Actor,
    CreateProblem,
    SaveRubric,
    ApproveRubric,
    PreparationRequest,
    CreateStatement,
)
from confia_lean_auditor.dynamic.store import dynamic_store, DynamicConflict
from confia_lean_auditor.dynamic.preparation import PreparationService
from confia_lean_auditor.dynamic.grading_context import resolve
from confia_lean_auditor.dynamic.grader import (
    DynamicSolutionGrader,
    extract,
    problem_equation,
)
from confia_lean_auditor.submissions.schemas import TranscriptionSegment
from test_dynamic_dy2 import ControlledProvider, proposal

ACTOR = Actor(actor_id="technical-demo:dynamic", kind="TECHNICAL_DEMO")
QUESTION = "Resolva no conjunto dos reais: 2y² - 14y + 24 = 0."
FACTOR = "y²-7y+12=0; (y-3)(y-4)=0; S={3,4}; 2*3^2-14*3+24=0; 2*4^2-14*4+24=0"
FORMULA = "Delta=(-14)^2-4*2*24=4; y=(14+sqrt(4))/4=4; y=(14-sqrt(4))/4=3; S={3,4}; 2*3^2-14*3+24=0; 2*4^2-14*4+24=0"
CRITERIA = [
    dict(
        criterion_id="method",
        title="Método",
        description="Justificar a resolução por transformações equivalentes.",
        max_points="4",
        order=1,
    ),
    dict(
        criterion_id="roots",
        title="Raízes",
        description="Obter todas as raízes reais. Crédito parcial proporcional às raízes corretas.",
        max_points="3",
        order=2,
    ),
    dict(
        criterion_id="check",
        title="Verificação",
        description="Verificar as raízes por substituição. Crédito parcial proporcional às raízes corretas.",
        max_points="3",
        order=3,
    ),
]


@pytest.fixture
def setup(tmp_path, monkeypatch):
    for key, folder in [
        ("CONFIA_DYNAMIC_DIR", "dynamic"),
        ("CONFIA_TME_CASES_DIR", "cases"),
        ("CONFIA_SUBMISSIONS_DIR", "submissions"),
        ("CONFIA_SUBMISSION_AUDITS_DIR", "audits"),
        ("CONFIA_TME_EXAMS_DIR", "exams"),
    ]:
        monkeypatch.setenv(key, str(tmp_path / folder))
    monkeypatch.setenv("CONFIA_AUTH_ENABLED", "0")
    monkeypatch.setenv("CONFIA_TME_DEMO_NO_AUTH", "1")
    monkeypatch.setenv("CONFIA_DYNAMIC_DEMO_ENABLED", "1")
    monkeypatch.setenv("CONFIA_ENV", "test")
    from confia_lean_auditor.tme.home_summary import rebuild_index

    rebuild_index()
    return tmp_path, TestClient(app)


def prepared(question=QUESTION, criteria=None, review=False):
    store = dynamic_store()
    d = store.create(
        CreateProblem(statement=question, max_score="10", correction_mode="DYNAMIC"),
        ACTOR,
    )
    p = proposal()
    p["warnings"] = (
        [dict(code="REVIEW", message="Confira a interpretação.", requires_review=True)]
        if review
        else []
    )
    # Controlled preparation is deliberately independent of grader claims.
    # Both the statement and its sealed version, never these candidate answers, are grader input authority.
    d = PreparationService(store, ControlledProvider(preparation=p)).start(
        d["problem"]["problem_id"],
        PreparationRequest(expected_revision=d["revision"]),
        ACTOR,
    )
    d = store.save_rubric(
        d["problem"]["problem_id"],
        SaveRubric(
            expected_revision=d["revision"],
            statement_version=1,
            max_score="10",
            criteria=criteria or CRITERIA,
        ),
        ACTOR,
    )
    d = store.approve(
        d["problem"]["problem_id"],
        d["rubrics"][-1]["rubric_id"],
        ApproveRubric(expected_revision=d["revision"], acknowledge_warnings=True),
        ACTOR,
    )
    return d


def grade(root, d, text, checker=None):
    context, statement, rubric, prep = resolve(d["problem"]["problem_id"], ACTOR, True)
    segment = TranscriptionSegment(
        segment_id="s", page_index=0, order=0, kind="text", text=text
    )
    source = SimpleNamespace(
        solution_text=text,
        source_hash="a" * 64,
        transcription_id="tr_" + "a" * 32,
        revision_number=1,
        problem_id=d["problem"]["problem_id"],
        provenance=SimpleNamespace(revision=SimpleNamespace(segments=[segment])),
    )
    return DynamicSolutionGrader(checker).grade(
        source, statement, rubric, prep, context, root / "result"
    )


@pytest.mark.parametrize(
    "solution,expected",
    [(FACTOR, 10), (FORMULA, 10), ("y²-7y+12=0; y=3", 1.5), ("y=9", 0), ("S={3,4}", 3)],
)
def test_vertical_slice(setup, solution, expected):
    root, _ = setup
    d = prepared()
    r = grade(root, d, solution)
    assert r.score == expected
    assert r.suggested_score == r.score
    assert sum(x.suggested_points for x in r.decisions) == Decimal(str(expected))
    for c in r.analysis.claims:
        assert solution[c.start : c.end] == c.text
    assert all(x.suggested_points <= x.max_points for x in r.decisions)
    assert r.analysis.provenance["llm_used"] is False


@pytest.mark.parametrize(
    "solution",
    [
        "talvez S={3,4}",
        "Se y=3, então y=4",
        "S={3,4}; S={3,5}",
        "y=3; y=9",
        "S={3,4}; não tenho certeza",
    ],
)
def test_ambiguous_conflicting_or_hypothetical_is_review(setup, solution):
    root, _ = setup
    r = grade(root, prepared(), solution)
    assert r.review_required
    assert r.decisions[1].automation == "REVIEW_ONLY"
    assert r.decisions[1].suggested_points == 0


def test_retracted_error_does_not_veto_adopted_roots(setup):
    root, _ = setup
    r = grade(root, prepared(), "Descarto: y=9; S={3,4}")
    assert r.analysis.claims[0].adoption == "ABANDONED"
    assert r.decisions[1].suggested_points == 3


def test_unknown_rubric_condition_never_silently_dropped(setup):
    root, _ = setup
    c = deepcopy(CRITERIA)
    c[1]["description"] = "Obter todas as raízes reais e justificar geometricamente."
    r = grade(root, prepared(criteria=c), FACTOR)
    assert r.decisions[1].automation == "REVIEW_ONLY"


def test_argument_requirement_not_inferred_from_final_answer(setup):
    root, _ = setup
    r = grade(root, prepared(), "S={3,4}")
    assert r.decisions[0].suggested_points == 0 and r.decisions[0].review_required
    assert r.decisions[1].suggested_points == 3


def test_independent_credit_and_follow_through_do_not_double_veto(setup):
    root, _ = setup
    c = deepcopy(CRITERIA)
    c[2]["dependencies"] = ["method"]
    r = grade(root, prepared(criteria=c), "(y-8)(y-9)=0; S={3,4}; 2*3^2-14*3+24=0")
    assert r.decisions[0].automation == "AUTO_VETO"
    assert r.decisions[1].suggested_points == 3
    assert r.decisions[2].automation == "REVIEW_ONLY"


@pytest.mark.parametrize("error", [RuntimeError, ValueError, ZeroDivisionError])
def test_checker_error_is_not_false_and_unrelated_identity_is_not_credit(setup, error):
    root, _ = setup

    def fail(c):
        raise error("controlled checker failure")

    r = grade(root, prepared(), FACTOR, fail)
    assert all(c.verification_status == "ERROR" for c in r.analysis.claims)
    assert r.score == 0 and all(d.automation == "REVIEW_ONLY" for d in r.decisions)


def test_unrelated_arithmetic_does_not_satisfy_rubric(setup):
    root, _ = setup
    r = grade(root, prepared(), "2+2=4; 0=0")
    assert r.score == 0 and r.review_required


def test_second_problem_linear_without_id_specific_tuning(setup):
    root, _ = setup
    r = grade(
        root,
        prepared("Resolva nos reais: 3z + 6 = 0."),
        "3z=-6; z=-2; S={-2}; 3*(-2)+6=0",
    )
    assert r.score == 10


def test_preparation_review_requires_explicit_policy(setup):
    _, client = setup
    d = prepared(review=True)
    url = f"/dynamic/problems/{d['problem']['problem_id']}/attempts"
    assert (
        client.post(
            url, json=dict(external_candidate_ref="S1", solution=FACTOR)
        ).status_code
        == 409
    )
    assert (
        client.post(
            url,
            json=dict(
                external_candidate_ref="S1",
                solution=FACTOR,
                allow_preparation_review=True,
            ),
        ).status_code
        == 201
    )


def attempt(client, d, text=FACTOR):
    response = client.post(
        f"/dynamic/problems/{d['problem']['problem_id']}/attempts",
        json=dict(
            external_candidate_ref="S1", solution=text, allow_preparation_review=True
        ),
    )
    assert response.status_code == 201, response.text
    case = response.json()
    base = f"/tme/cases/{case['case_id']}"
    tr = client.get(base + "/transcriptions").json()[0]["transcription"][
        "transcription_id"
    ]
    accepted = client.post(
        base + f"/transcriptions/{tr}/accept",
        json=dict(revision_number=1, reviewer_identity_verified=False),
    )
    assert accepted.status_code == 200, accepted.text
    request = dict(
        transcription_id=tr,
        revision_number=1,
        acceptance_id=accepted.json()["acceptance"]["acceptance_id"],
    )
    return case, base, request


def test_shared_attempt_original_transcription_audit_replay_queue_and_integrity(setup):
    root, client = setup
    d = prepared()
    case, base, request = attempt(client, d)
    assert client.get(base + "/original-text").json()["text"] == FACTOR
    response = client.post(base + "/audits", json=request)
    assert response.status_code == 200, response.text
    run = response.json()
    assert run["status"] == "COMPLETED", run
    assert run["result"]["score"] == 10 and run["result"]["engine_mode"] == "DYNAMIC"
    assert run["source"]["dynamic_context"]["rubric_version"] == 1
    assert (
        client.post(base + "/audits", json=request).json()["audit_run_id"]
        == run["audit_run_id"]
    )
    assert client.get("/tme/cases?view=queue").status_code == 200
    assert {e["event_type"] for e in run["result"]["events"]} >= {
        "dynamic_grading_started",
        "student_claim_extracted",
        "rubric_binding_created",
        "dynamic_checker_completed",
        "dynamic_rubric_decision",
        "dynamic_grading_completed",
    }
    stored = json.loads((root / "audits" / f"{run['audit_run_id']}.json").read_text())
    Path(stored["artifact_dir"], "solution.txt").write_text("tampered")
    assert client.get(base + "/audits").status_code == 409


def test_changed_statement_or_preparation_blocks_old_attempt_without_rewriting_history(
    setup,
):
    root, client = setup
    d = prepared()
    case, base, request = attempt(client, d)
    first = client.post(base + "/audits", json=request).json()
    assert first["status"] == "COMPLETED"
    old = (root / "audits" / f"{first['audit_run_id']}.json").read_bytes()
    dynamic_store().statement(
        d["problem"]["problem_id"],
        CreateStatement(
            expected_revision=d["revision"],
            statement="Resolva nos reais: y-7=0.",
            max_score="10",
        ),
        ACTOR,
    )
    assert client.post(base + "/audits", json=request).status_code == 409
    assert (root / "audits" / f"{first['audit_run_id']}.json").read_bytes() == old
    assert client.get(base + "/audits").json()[0]["stale"]


def test_draft_rubric_and_missing_preparation_cannot_create_attempt(setup):
    _, client = setup
    s = dynamic_store()
    d = s.create(
        CreateProblem(statement=QUESTION, max_score="10", correction_mode="DYNAMIC"),
        ACTOR,
    )
    assert (
        client.post(
            f"/dynamic/problems/{d['problem']['problem_id']}/attempts",
            json=dict(external_candidate_ref="S1", solution=FACTOR),
        ).status_code
        == 409
    )


def test_other_owner_cannot_attach_dynamic_problem(setup):
    _, client = setup
    s = dynamic_store()
    d = s.create(
        CreateProblem(statement=QUESTION, max_score="10", correction_mode="DYNAMIC"),
        Actor(actor_id="another", kind="TEACHER"),
    )
    assert (
        client.post(
            f"/dynamic/problems/{d['problem']['problem_id']}/attempts",
            json=dict(external_candidate_ref="S1", solution=FACTOR),
        ).status_code
        == 404
    )


@pytest.mark.parametrize(
    "solution,expected",
    [("S={3}", 1.5), ("S={3,9}", 1.5), ("(y²-7y+12)=0; S={3,4}", 0)],
)
def test_partial_set_components_and_parentheses_are_not_factorization(
    setup, solution, expected
):
    root, _ = setup
    c = deepcopy(CRITERIA)
    if solution.startswith("("):
        c[0]["description"] = "Justificar a fatoração."
    r = grade(root, prepared(criteria=c), solution)
    decision = r.decisions[0] if solution.startswith("(") else r.decisions[1]
    assert decision.suggested_points == Decimal(str(expected))
    if not solution.startswith("("):
        assert r.analysis.claims[0].verification_status == "REFUTED"


@pytest.mark.parametrize("change", ["preparation", "rubric_draft", "rubric_approval"])
def test_new_preparation_or_rubric_cannot_rebind_an_old_attempt(setup, change):
    root, client = setup
    d = prepared()
    case, base, request = attempt(client, d)
    first = client.post(base + "/audits", json=request).json()
    assert first["status"] == "COMPLETED"
    assert first["engine_mode"] == "DYNAMIC"
    old = (root / "audits" / f"{first['audit_run_id']}.json").read_bytes()
    store = dynamic_store()
    pid = d["problem"]["problem_id"]
    if change == "preparation":
        PreparationService(store, ControlledProvider()).start(
            pid,
            PreparationRequest(
                expected_revision=d["revision"], reason="Revisar preparação"
            ),
            ACTOR,
        )
    else:
        d = store.save_rubric(
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
        if change == "rubric_approval":
            store.approve(
                pid,
                d["rubrics"][-1]["rubric_id"],
                ApproveRubric(
                    expected_revision=d["revision"], acknowledge_warnings=True
                ),
                ACTOR,
            )
    assert client.post(base + "/audits", json=request).status_code == 409
    assert (root / "audits" / f"{first['audit_run_id']}.json").read_bytes() == old
    assert client.get(base + "/audits").json()[0]["stale"]


def test_no_specialized_fallback_and_human_confirmation(setup, monkeypatch):
    import confia_lean_auditor.submission_audits.router as service

    root, client = setup
    d = prepared()
    case, base, request = attempt(client, d)

    def forbidden(*a, **kw):
        raise AssertionError("Specialized auditor must not run")

    monkeypatch.setattr(service, "engine", forbidden)
    response = client.post(base + "/audits", json=request)
    assert response.status_code == 200 and response.json()["result"]["score"] == 10

    run = response.json()
    confirmed = client.post(
        base + "/decision",
        json=dict(
            audit_run_id=run["audit_run_id"],
            max_points=10,
            final_points=10,
            feedback="Conferido pelo avaliador.",
        ),
    )
    assert confirmed.status_code == 201, confirmed.text
    assert confirmed.json()["suggested_points"] == "10.00"
    assert client.get(base).json()["status"] == "DECIDED"
    from confia_lean_auditor.tme.home_summary import rebuild_index

    rebuild_index()
    assert client.get("/tme/cases?view=queue&source=TEXT").status_code == 200


@pytest.mark.parametrize(
    "question",
    [QUESTION + " Considere apenas y>3.", QUESTION + " Justifique geometricamente."],
)
def test_statement_extra_conditions_cannot_be_dropped(setup, question):
    root, _ = setup
    r = grade(root, prepared(question), FACTOR)
    assert r.score == 0 and r.review_required


def test_rubric_notes_are_not_silently_discarded(setup):
    root, _ = setup
    c = deepcopy(CRITERIA)
    c[1]["teacher_guidance"] = "Exigir demonstração geométrica."
    r = grade(root, prepared(criteria=c), "S={3,4}")
    assert (
        r.decisions[1].automation == "REVIEW_ONLY"
        and r.decisions[1].suggested_points == 0
    )


def test_demo_grading_needs_dynamic_authorization_and_nonblank_source(
    setup, monkeypatch
):
    root, client = setup
    d = prepared()
    url = f"/dynamic/problems/{d['problem']['problem_id']}/attempts"
    assert (
        client.post(
            url, json=dict(external_candidate_ref="S1", solution="   ")
        ).status_code
        == 422
    )
    monkeypatch.setenv("CONFIA_DYNAMIC_DEMO_ENABLED", "0")
    assert (
        client.post(
            url, json=dict(external_candidate_ref="S1", solution=FACTOR)
        ).status_code
        == 409
    )


def test_zero_weight_satisfied_criterion_is_not_a_mathematical_refutation(setup):
    root, _ = setup
    criteria = deepcopy(CRITERIA)
    criteria[0]["max_points"] = "0"
    criteria[1]["max_points"] = "4"
    criteria[2]["max_points"] = "6"
    result = grade(root, prepared(criteria=criteria), FACTOR)
    assert result.score == 10
    assert result.decisions[0].automation == "AUTO_AWARD"
    assert result.rubric_assessment["items"][0]["mathematical_status"] == "supported"
    assert (
        result.rubric_assessment["items"][0]["verification_status"]
        == "verified_in_scope"
    )
