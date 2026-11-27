"""P3 mathematical/state contracts, DIGITAL E2E and separation from ITA/P1."""
import hashlib
import json
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from confia_lean_auditor.core.math_canonical.rational import (
    rational_value, lean_rational_expression, weighted_sum_matches,
)
from confia_lean_auditor.lean.student_claim_checkers.tme2_p3 import verify_tme2_p3_digital
from confia_lean_auditor.rubric.pauta import load_pauta
from confia_lean_auditor.rubric.pauta.bridge import record_fingerprint
from confia_lean_auditor.rubric.pauta.tme2_p3 import bridge_tme2_p3, TME2_P3_OBLIGATIONS
from confia_lean_auditor.student_claims.tme2_p3_digital import collect_tme2_p3_digital
from confia_lean_auditor.tme.p3_machine import P3Machine, load_machine
from confia_lean_auditor.tme.registry import audit_tme, TME_PROBLEMS

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests/fixtures/tme2_p3_digital/cases.json").read_text())


@pytest.fixture
def machine():
    return load_machine(ROOT / "examples/pautas/tme2_problem3.machine.v1.json")


def run(item, text, **kwargs):
    return audit_tme("TME2026P3", {item: text}, solution_id="p3-test", use_lean=False, **kwargs)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_controlled_digital_cases(case):
    bridge, result = run(case["item"], case["text"])
    item = result.items["abc".index(case["item"])]
    assert item.points_awarded == case["points"]
    if "selected_path" in case:
        assert item.selected_method_path == case["selected_path"]
    records = {r.record_id: r for r in bridge.auditor.records}
    for fact in bridge.auditor.facts:
        for identifier in fact.source_claim_ids:
            record = records[identifier]
            assert record.source.attributable and record.source.raw_text
            assert record.canonical_form and record.source.grounding_status == "grounded"
            assert fact.record_fingerprints[identifier] == record_fingerprint(record)
            assert fact.verification in record.verification_results
        assert "machine_sha256" in fact.metadata
    if item.points_awarded:
        assert item.credit_evidence_refs


def test_full_problem_and_alternative_reach_twenty():
    inputs = {"a": next(c["text"] for c in CASES if c["id"] == "a_complete"),
              "b": next(c["text"] for c in CASES if c["id"] == "b_tree"),
              "c": next(c["text"] for c in CASES if c["id"] == "c_complete")}
    _, result = audit_tme("TME2026P3", inputs, use_lean=False)
    assert result.score == 20 and not result.needs_review
    assert result.items[1].selected_method_path == "b.alternative"


def test_machine_uses_user_confirmed_bottom_first_stacks(machine):
    assert machine.stacks == (("white", "black", "white", "gray", "black"),
        ("white", "gray", "black"), ("gray", "black"), ("black", "black"),
        ("gray", "black"), ("black", "white", "gray", "black"))
    assert machine.bottom_colors == ("white", "white", "gray", "black", "gray", "black")
    assert machine.after_first(1) == ("black", "white", "gray", "black", "gray", "black")
    assert machine.after_first(2) == ("white", "gray", "gray", "black", "gray", "black")
    assert machine.after_first(6) == ("white", "white", "gray", "black", "gray", "white")
    assert machine.bottom_colors.count("white") == 2  # original is immutable
    assert machine.counts_after_first(1)["black"] == 3
    assert machine.counts_after_first(2)["gray"] == 3
    assert machine.best_choices(1) == (frozenset({"black"}), 3)
    assert machine.best_choices(2) == (frozenset({"gray"}), 3)


def test_finite_enumeration_not_expected_number_lookup(machine):
    assert len(machine.ordered_pairs()) == 36
    assert machine.second_white_pairs() == frozenset({(1, 2), (2, 1), (3, 1), (3, 2),
        (4, 1), (4, 2), (5, 1), (5, 2), (6, 1), (6, 2), (6, 6)})
    assert machine.continue_compartments() == {1, 2}
    assert machine.second_white_branches() == tuple(map(Fraction, ["1/6", "1/6", "1/3", "1/3", "1/3", "1/2"]))
    assert machine.win_probability() == Fraction(1, 6)
    # Changing a state changes its computed events, not just a label or answer.
    altered = replace(machine, stacks=machine.stacks[:-1] + (("black", "black"),))
    assert (6, 6) not in altered.second_white_pairs()
    assert len(altered.second_white_pairs()) == 10


@pytest.mark.parametrize("index", [0, 7, -1, True, 1.0])
def test_machine_rejects_invalid_compartments(machine, index):
    with pytest.raises(ValueError):
        machine.after_first(index)


def test_machine_requires_known_colors_and_source():
    with pytest.raises(ValueError):
        P3Machine((("white", "unknown"),) * 6, "fixture")
    with pytest.raises(ValueError):
        P3Machine((("white", "black"),) * 6, "")


@pytest.mark.parametrize("text,expected", [("2/6", "1/3"), ("(10+1)/36", "11/36"),
    ("3/6", "1/2"), ("0.5", "1/2"), ("-3/7", "-3/7"), ("0.333", "333/1000")])
def test_exact_rationals(text, expected):
    assert rational_value(text) == Fraction(expected)


@pytest.mark.parametrize("text", ["0.333...", "0.333…", "1/0", "x/3", "__import__('os')", "sin(1)"])
def test_unsupported_or_unsafe_math_is_not_guessed(text):
    assert lean_rational_expression(text) is None


def test_rational_renderer_does_not_use_integer_division_or_approximation():
    assert lean_rational_expression("2/6") == "((2 : ℚ) / (6 : ℚ))"
    assert "ℤ" not in lean_rational_expression("(1/6)(1/2)+(1/6)(1/2)")
    assert rational_value("0.333") != Fraction(1, 3)
    assert lean_rational_expression("+2/6") == lean_rational_expression("2/6")


@pytest.mark.parametrize("text", ["1/6", "1/6=1/6", "0=0", "(1/6)*(1/2)"])
def test_arithmetic_value_alone_is_not_a_two_branch_development(text):
    assert not weighted_sum_matches(text, [Fraction(1, 6)] * 2, [Fraction(1, 2)] * 2)


@pytest.mark.parametrize("prefix", ["Não é verdade:\n", "Suponha:\n", "Tentativa descartada:\n"])
def test_contextual_grounding_does_not_promote_hypotheses_or_rejections(prefix):
    bridge, result = run("a", prefix + "inferiores_brancas: 2\nprimeira_branca: 2/6=1/3")
    assert result.items[0].points_awarded == 0
    assert not any(e.status == "supported" for e in bridge.evidence.obligations)


@pytest.mark.parametrize("item,text", [("a", "outra_quantidade: 1/3"),
    ("b", "outra_quantidade: 11/36"), ("c", "total: 1/6=1/6"),
    ("b", "resto: 11/36"), ("a", "resto: 1/3")])
def test_unknown_labels_or_tautologies_do_not_fill_missing_context(item, text):
    _, result = run(item, text)
    assert result.items["abc".index(item)].points_awarded == 0


def test_existing_answer_concept_remains_supported_without_erasing_quantity_subjects():
    _, result = run("b", "Resposta: 11/36")
    assert result.items[1].points_awarded == 2


def test_conditional_weights_are_not_the_unconditional_game_probability():
    case = next(c for c in CASES if c["id"] == "c_complete")
    text = case["text"].replace("(1/6)(1/2)+(1/6)(1/2)=1/6", "(1/2)(1/2)+(1/2)(1/2)=1/2")
    _, result = run("c", text)
    assert result.items[2].points_awarded == 6


def test_correct_final_value_cannot_hide_a_false_written_equality():
    bridge, result = run("a", "inferiores_brancas: 2\nprimeira_branca: 1/2=1/3")
    assert result.items[0].points_awarded == 2
    assert bridge.evidence.obligations[1].status == "refuted"


def test_bare_answer_never_synthesizes_counting_facts():
    bridge, result = run("b", "11/36")
    states = {e.obligation_id: e.status for e in bridge.evidence.obligations}
    assert states["b.ordered_pairs"] == states["b.different_favorable"] == states["b.same_compartment"] == "indeterminate"
    assert result.items[1].points_awarded == 2


def test_all_obligations_exercised_and_no_secondary_calls():
    covered, origins = set(), set()
    for case in CASES:
        bridge, _ = run(case["item"], case["text"])
        covered.update(e.obligation_id for e in bridge.evidence.obligations if e.status == "supported")
        origins.update(f.verification_source for f in bridge.auditor.facts)
    assert covered == set(TME2_P3_OBLIGATIONS)
    assert origins == {"deterministic", "canonical_equivalence"}


def test_annotation_or_routing_changes_are_rejected(machine):
    digital = collect_tme2_p3_digital({"a": "inferiores_brancas: 2"})
    with pytest.raises(ValueError):
        verify_tme2_p3_digital(replace(digital, source_text=digital.source_text.replace("2", "3")), "x", machine, use_lean=False)
    record = digital.records[0]
    corrupted = record.model_copy(update={"rubric_links": ("b",)})
    with pytest.raises(ValueError):
        verify_tme2_p3_digital(replace(digital, records=(corrupted,)), "x", machine, use_lean=False)


def test_true_arithmetic_does_not_formally_verify_a_missing_strategy(monkeypatch):
    import confia_lean_auditor.lean.student_claim_checkers.tme2_p3 as module

    def forbidden(*args, **kwargs):
        pytest.fail("No formal credit without the mathematical probability context")

    monkeypatch.setattr(module, "check_rational_record", forbidden)
    case = next(c for c in CASES if c["id"] == "c_arithmetic_without_strategy")
    bridge, result = audit_tme("TME2026P3", {"c": case["text"]}, use_lean=True)
    assert result.items[2].points_awarded == 0
    assert all(f.verification.status == "unverified" for f in bridge.auditor.facts)


@pytest.mark.parametrize("status", ["verified", "refuted", "technical_error"])
def test_rational_formal_result_contract_and_tamper_rejection(monkeypatch, status):
    import confia_lean_auditor.lean.student_claim_checkers.rational_equality as module
    from confia_lean_auditor.student_claims.schemas import StudentClaimCheck

    def fake_proof(**kwargs):
        claim = kwargs["claim"]
        assert "ℚ" in kwargs["lean_statement"] and "ℤ" not in kwargs["lean_statement"]
        return StudentClaimCheck(id=claim.id, problem_id=claim.problem_id, claim_type=claim.claim_type,
            raw_text=claim.raw_text, normalized_text=claim.normalized_text, lean_statement=kwargs["lean_statement"],
            method="norm_num", status=status, compiled=status == "verified", lean_file="mock.lean",
            stdout="", stderr="", data=claim.data, grounding=claim.grounding, formal_status=status,
            refutation_verified=status == "refuted", refutation_lean_file="mock-negative.lean" if status == "refuted" else None)

    monkeypatch.setattr(module, "evaluate_student_proof", fake_proof)
    text = "primeira_branca: 2/6=1/3" if status == "verified" else "primeira_branca: 2/6=1/2"
    bridge, result = audit_tme("TME2026P3", {"a": text}, use_lean=True)
    fact = next(f for f in bridge.auditor.facts if f.student_check)
    assert fact.student_check["data"]["number_domain"] == "Q"
    assert fact.verification_source == "student_lean"
    from confia_lean_auditor.claims.common.adapters import project_student_claim
    native = next(r for r in bridge.auditor.records if r.record_id.startswith("native:rational:"))
    with pytest.raises(ValueError, match="native"):
        project_student_claim(native, solution_text=collect_tme2_p3_digital({"a": text}).source_text)
    assert bridge.evidence.obligations[1].status == {"verified": "supported", "refuted": "refuted", "technical_error": "technical_error"}[status]
    if status == "technical_error":
        assert result.items[0].points_awarded is None
    tampered = fact.model_copy(update={"student_check": {**fact.student_check,
        "data": {**fact.student_check["data"], "number_domain": "Z"}}})
    bundle = bridge.auditor.model_copy(update={"facts": (tampered,)})
    cfg = load_pauta(ROOT / "examples/pautas/tme2_problem3.v1.json")
    assert bridge_tme2_p3(cfg, bundle).evidence.obligations[1].status == "indeterminate"


def test_registry_is_opt_in_and_preserves_p1():
    from confia_lean_auditor.core.problem_catalog import CATALOG
    from confia_lean_auditor.rubric.pauta.tme2_p1 import audit_tme2_p1_digital
    assert set(TME_PROBLEMS) == {"TME2_P1_PILOT", "TME2026P3", "TME2026P4", "TME2026P5", "TME2026P2"}
    assert "TME2026P3" not in CATALOG
    cfg = load_pauta(ROOT / "examples/pautas/tme2_problem1.v1.json")
    expected = audit_tme2_p1_digital(cfg, {"a": "731-137=584"}, "same", use_lean=False)
    actual = audit_tme("TME2_P1_PILOT", {"a": "731-137=584"}, solution_id="same", use_lean=False)
    assert [r.model_dump(mode="json") for r in actual] == [r.model_dump(mode="json") for r in expected]
    with pytest.raises(ValueError):
        audit_tme("TME2026P6", {"a": "1/3"})
    with pytest.raises(ValueError):
        audit_tme("TME2026P3", "1/3")
