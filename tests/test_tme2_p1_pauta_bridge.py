"""Offline source -> claims -> checks -> bridge -> points, plus trust boundary."""
import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

from confia_lean_auditor.claims.common.schemas import Origin
from confia_lean_auditor.core.math_canonical.syntax import expression_syntax
from confia_lean_auditor.lean.student_claim_checkers.tme2_p1 import verify_tme2_p1_digital
from confia_lean_auditor.rubric.pauta import PautaEngine, ObligationEvidence, load_pauta
from confia_lean_auditor.rubric.pauta.bridge import (
    bridge_tme2_p1, record_fingerprint, TME2_P1_OBLIGATIONS,
)
from confia_lean_auditor.rubric.pauta.tme2_p1 import audit_tme2_p1_digital
from confia_lean_auditor.student_claims.digital_literals import literal_form
from confia_lean_auditor.student_claims.tme2_p1_digital import collect_tme2_p1_digital

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests/fixtures/tme2_p1_digital/cases.json").read_text())


@pytest.fixture
def pilot():
    return load_pauta(ROOT / "examples/pautas/tme2_problem1.v1.json")


def run(pilot, item, text):
    return audit_tme2_p1_digital(pilot, {item: text}, "offline-test", use_lean=False)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_digital_cases(pilot, case):
    bridge, result = run(pilot, case["item"], case["text"])
    item = result.items["abcd".index(case["item"])]
    assert item.points_awarded == case["points"]
    if "band" in case:
        selection = item.children[2] if case["item"] == "c" else item
        assert selection.selected_band == case["band"]
        if "band_points" in case:
            assert selection.points_awarded == case["band_points"]
    by_id = {r.record_id: r for r in bridge.auditor.records}
    for evidence in bridge.evidence.obligations:
        if evidence.status == "supported":
            assert evidence.source_claim_ids and evidence.evidence_refs
            assert evidence.grounding_status == "grounded"
            for identifier in evidence.source_claim_ids:
                record = by_id[identifier]
                assert record.source.attributable and record.canonical_form
                assert record.verification_results
    # Trace fields survive into the engine's obligation decisions.
    dumped = result.model_dump(mode="json")
    assert "source_claim_ids" in json.dumps(dumped)


@pytest.mark.parametrize("text", [
    "Não é verdade que 731-137=594.", "Suponha que 731-137=594.",
    'O enunciado diz: "731-137=594".', "Tentativa descartada: 731-137=594.",
])
def test_nonasserted_math_never_becomes_credit(pilot, text):
    bridge, result = run(pilot, "a", text)
    assert result.items[0].points_awarded == 0
    assert not any(e.status == "supported" for e in bridge.evidence.obligations)


@pytest.mark.parametrize("text", ["584", "731-173=584", "731-(100+37)=584",
    "731-137=584.\n2+2=5.", "731-137=584. Outra justificativa não analisada."])
def test_wrong_answer_is_not_automatically_one_arithmetic_error(pilot, text):
    bridge, _ = run(pilot, "a", text)
    assert bridge.evidence.obligations[3].status == "indeterminate"


@pytest.mark.parametrize("text", ["0=0", "99(a-c)=99(a-c)", "(100a+10b+c)-(100c+10b+a)=0",
    "99(a-c)+0=99(a-c)", "99a-99c=1*(99a-99c)"])
def test_true_tautology_or_false_algebra_does_not_prove_factorization(pilot, text):
    bridge, _ = run(pilot, "b", text)
    evidence = {e.obligation_id: e for e in bridge.evidence.obligations}
    assert evidence["b.factorization"].status != "supported"
    assert evidence["b.middle_cancellation"].status != "supported"


@pytest.mark.parametrize("text", ["{99,...,792}", "{99, x}", "{(7,1),2}", "b ∈ {True,1}",
    "{x for x in range(9)}", "{__import__('os').getcwd()}", "{99999999999999}"])
def test_literal_grammar_fails_closed(text):
    assert literal_form(text) is None


def test_syntax_retains_operations_and_signed_general_fractions():
    node = expression_syntax("731-137")
    assert isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub)
    node = expression_syntax("-3/7")
    assert isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
    assert isinstance(node.left, ast.UnaryOp) and isinstance(node.left.op, ast.USub)


@pytest.mark.parametrize("text,points", [
    ("(a-c) ∈ {1,2,3,4,5,6,7,8}", 0),
    ("{99,99,99}", 1),
    ("D=99(a-c).\nX ∈ {99,198,297,396,495,594,693,792}", 1),
])
def test_collection_subjects_and_duplicates_are_not_invented(pilot, text, points):
    _, result = run(pilot, "c", text)
    assert result.items[2].points_awarded == points


def test_routing_is_explicit_and_no_cross_item_credit(pilot):
    bridge, result = run(pilot, "b", "731-137=594")
    assert result.score == 0
    assert all(e.status == "indeterminate" for e in bridge.evidence.obligations)
    with pytest.raises(ValueError):
        collect_tme2_p1_digital({"e": "137"})


def test_source_and_routing_mutations_fail_before_checks():
    digital = collect_tme2_p1_digital({"a": "137"})
    with pytest.raises(ValueError):
        verify_tme2_p1_digital(replace(digital, source_text=digital.source_text.replace("137", "138")), "x", use_lean=False)
    record = digital.records[0].model_copy(update={"rubric_links": ("b",)})
    with pytest.raises(ValueError):
        verify_tme2_p1_digital(replace(digital, records=(record,)), "x", use_lean=False)


def changed_bundle(bundle, record, *, refresh=False):
    records = tuple(record if r.record_id == record.record_id else r for r in bundle.records)
    facts = tuple(f.model_copy(update={"record_fingerprints": {
        i: record_fingerprint(next(r for r in records if r.record_id == i))
        for i in f.source_claim_ids}}) if refresh else f for f in bundle.facts)
    return bundle.model_copy(update={"records": records, "facts": facts})


@pytest.mark.parametrize("mutation", ["fingerprint", "reference", "unattributed", "missing_link"])
def test_bridge_rejects_untrusted_or_changed_records(pilot, mutation):
    bridge, _ = run(pilot, "a", "137")
    record = bridge.auditor.records[0]
    if mutation == "fingerprint":
        record = record.model_copy(update={"canonicalization_reason": "changed after checking"})
    elif mutation == "reference":
        record = record.model_copy(update={"provenance": record.provenance.model_copy(update={"origin": Origin.GENERATED_REFERENCE})})
    elif mutation == "unattributed":
        record = record.model_copy(update={"source": record.source.model_copy(update={"attributable": False})})
    else:
        record = record.model_copy(update={"verification_results": ()})
    result = bridge_tme2_p1(pilot, changed_bundle(bridge.auditor, record, refresh=mutation != "fingerprint"))
    assert result.evidence.obligations[0].status == "indeterminate"


def with_fact_status(bundle, status, mechanism="deterministic"):
    fact = bundle.facts[0]
    link = fact.verification.model_copy(update={"status": status})
    records = tuple(r.model_copy(update={"verification_results": (link,)}) for r in bundle.records)
    fact = fact.model_copy(update={"verification": link, "verification_source": mechanism,
        "record_fingerprints": {r.record_id: record_fingerprint(r) for r in records}})
    return bundle.model_copy(update={"facts": (fact,), "records": records})


@pytest.mark.parametrize("status,expected", [("technical_error", "technical_error"),
    ("unverified", "indeterminate"), ("failed", "indeterminate"), ("refuted", "refuted")])
def test_bridge_preserves_status_meaning(pilot, status, expected):
    bridge, _ = run(pilot, "a", "137")
    result = bridge_tme2_p1(pilot, with_fact_status(bridge.auditor, status))
    assert result.evidence.obligations[0].status == expected
    if status == "technical_error":
        assert PautaEngine().evaluate(pilot, result.evidence).items[0].points_awarded is None


@pytest.mark.parametrize("mechanism", ["student_lean", "reference_lean", "secondary", "semantic"])
def test_bridge_never_labels_unproven_result_as_student_lean_or_secondary_credit(pilot, mechanism):
    bridge, _ = run(pilot, "a", "137")
    result = bridge_tme2_p1(pilot, with_fact_status(bridge.auditor, "verified", mechanism))
    assert result.evidence.obligations[0].status == "indeterminate"


def test_bridge_rejects_unmapped_facts_and_other_problems(pilot):
    bridge, _ = run(pilot, "a", "137")
    fact = bridge.auditor.facts[0].model_copy(update={"fact_id": "invented.fact"})
    with pytest.raises(ValueError):
        bridge_tme2_p1(pilot, bridge.auditor.model_copy(update={"facts": (fact,)}))
    with pytest.raises(ValueError):
        bridge_tme2_p1(pilot.model_copy(update={"problem_id": "TME2_P2"}), bridge.auditor)


def test_every_pilot_obligation_has_an_observed_supported_case(pilot):
    covered = set()
    for case in CASES:
        bridge, _ = run(pilot, case["item"], case["text"])
        covered.update(e.obligation_id for e in bridge.evidence.obligations if e.status == "supported")
    assert covered == set(TME2_P1_OBLIGATIONS.values())


def test_legacy_evidence_serialization_is_unchanged():
    evidence = ObligationEvidence(obligation_id="x", status="supported", origin="deterministic",
        evidence_refs=("x",), attributable_to_student=True)
    assert not ({"metadata", "source_claim_ids", "grounding_status", "verification_source"}
                & evidence.model_dump(mode="json").keys())


def test_full_problem_keeps_items_separate_and_reaches_twenty(pilot):
    texts = {c["item"]: c["text"] for c in CASES if c["id"] in
             {"a_complete", "b_complete", "c_complete", "d_complete"}}
    bridge, result = audit_tme2_p1_digital(pilot, texts, "whole-problem", use_lean=False)
    assert result.score == 20 and not result.needs_review
    for record in bridge.auditor.records:
        assert len(record.rubric_links) == 1


def test_contradictory_results_stay_indeterminate(pilot):
    bridge, result = run(pilot, "a", "731-137=594.\n731-137=584.")
    assert bridge.evidence.obligations[2].status == "indeterminate"
    assert bridge.evidence.obligations[2].metadata["reason"] == "CONFLICTING_FACT_RESULTS"
    assert result.items[0].points_awarded == 1


@pytest.mark.parametrize("text", ["731-137=x", "731-137=sin(1)"])
def test_unknown_result_is_not_a_refutation(pilot, text):
    bridge, _ = run(pilot, "a", text)
    assert bridge.evidence.obligations[2].status == "indeterminate"


@pytest.mark.parametrize("status", ["verified", "refuted", "technical_error"])
def test_formal_result_identity_and_status_are_preserved(pilot, monkeypatch, status):
    # A checker-result contract unit test. Real local Lean execution is recorded
    # separately by scripts/evaluation/run_tme2_p1_pauta_pilot.py --with-lean.
    from confia_lean_auditor.student_claims.schemas import StudentClaimCheck
    from confia_lean_auditor.lean import student_claim_checker

    def fake_checker(claim, run_id, index):
        return StudentClaimCheck(id=claim.id, problem_id=claim.problem_id,
            claim_type=claim.claim_type, raw_text=claim.raw_text, normalized_text=claim.normalized_text,
            lean_statement="mock contract fixture", method="norm_num", status=status,
            compiled=status == "verified", lean_file="mock-proof.lean", stdout="", stderr="",
            data=claim.data, grounding=claim.grounding, formal_status=status,
            refutation_verified=status == "refuted", refutation_lean_file="mock-negation.lean" if status == "refuted" else None)

    monkeypatch.setattr(student_claim_checker, "check_one_student_claim", fake_checker)
    bridge, _ = audit_tme2_p1_digital(pilot, {"a": "731-137=594" if status == "verified" else "731-137=584"}, "formal-contract")
    result = bridge.evidence.obligations[2]
    assert result.status == {"verified": "supported", "refuted": "refuted", "technical_error": "technical_error"}[status]
    assert result.verification_source == "student_lean"
    assert len(result.source_claim_ids) == 2  # canonical view and exact legacy checker input
    formal_fact = next(f for f in bridge.auditor.facts if f.student_check)
    # Altering only the returned checker payload invalidates its attribution.
    corrupted = formal_fact.model_copy(update={"student_check": {**formal_fact.student_check, "data": {"left_expr": "1", "right_expr": "1"}}})
    bundle = bridge.auditor.model_copy(update={"facts": tuple(corrupted if f == formal_fact else f for f in bridge.auditor.facts)})
    assert bridge_tme2_p1(pilot, bundle).evidence.obligations[2].status == "indeterminate"


def test_fraction_is_not_projected_to_integer_lean_checker(pilot, monkeypatch):
    from confia_lean_auditor.lean import student_claim_checker

    def forbidden(*args, **kwargs):
        pytest.fail("A rational expression must not be cast to integer division")

    monkeypatch.setattr(student_claim_checker, "check_one_student_claim", forbidden)
    bridge, result = audit_tme2_p1_digital(pilot, {"a": "731-137=1188/2"}, "fraction")
    assert result.items[0].points_awarded == 3
    assert bridge.evidence.obligations[2].verification_source == "canonical_equivalence"


@pytest.mark.parametrize("item,text", [
    ("b", "a=100c+10b+a"), ("b", "r=100c+10b+a.\nr=0."),
    ("c", "a=99(a-c)"), ("c", "D=99(a-c).\nD=0."),
])
def test_existing_digit_symbols_and_conflicting_definitions_are_not_fresh_notation(pilot, item, text):
    _, result = run(pilot, item, text)
    assert result.items["abcd".index(item)].points_awarded == 0
