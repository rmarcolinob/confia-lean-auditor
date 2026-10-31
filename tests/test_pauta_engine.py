"""Offline structured-evidence contracts; no extractor, provider or Lean required."""
from copy import deepcopy
from decimal import Decimal
from itertools import product
from pathlib import Path

import pytest
from pydantic import ValidationError

from confia_lean_auditor.rubric.pauta import (
    ConditionalContext, ObligationEvidence, PautaConfig, PautaEngine, PautaEvidence,
    load_pauta,
)

PILOT = Path(__file__).resolve().parents[1] / "examples/pautas/tme2_problem1.v1.json"


def atom(identifier, points, *obligations, strategy="all_of"):
    return dict(id=identifier, max_points=points, scoring_strategy=strategy,
                obligation_ids=obligations)


def config(rule, *, policy="defer", obligations=("x", "y")):
    return PautaConfig.model_validate(dict(problem_id="test", title="Test rubric",
        max_score=rule["max_points"], unresolved_policy=policy,
        obligations=[dict(id=i, description=i) for i in obligations], items=[rule]))


def evidence(identifier, status="supported", **kwargs):
    return ObligationEvidence(obligation_id=identifier, status=status,
        **(dict(origin="deterministic", attributable_to_student=True,
                evidence_refs=("source:" + identifier,)) | kwargs))


def evaluate(cfg, *records):
    return PautaEngine().evaluate(cfg, PautaEvidence(problem_id=cfg.problem_id,
        solution_id="synthetic-test", obligations=records))


@pytest.fixture
def pilot():
    return load_pauta(PILOT)


@pytest.mark.parametrize("ids,points,band", [
    (("a.identifies_137", "a.constructs_subtraction", "a.result_594"), 3, "a.full"),
    (("a.identifies_137", "a.constructs_subtraction", "a.arithmetic_error_only"), 2, "a.arithmetic_only"),
    (("a.identifies_137",), 1, "a.identification"),
    (("a.result_594",), 0, None),
    ((), 0, None),
    # A missing result does not establish that the ONLY error was arithmetic.
    (("a.identifies_137", "a.constructs_subtraction"), 1, "a.identification"),
])
def test_item_a_requires_construction_and_an_explicit_arithmetic_error_contract(pilot, ids, points, band):
    item = evaluate(pilot, *(evidence(i) for i in ids)).items[0]
    assert item.points_awarded == points and item.selected_band == band
    if points == 0:
        assert item.indeterminate_obligations and not item.unsatisfied_obligations
        assert item.needs_review


@pytest.mark.parametrize("ids,points,band", [
    (("c.complete_list", "c.no_extraneous_values"), 4, "c.list.full"),
    (("c.single_list_error",), 3, "c.list.one_error"),
    (("c.several_correct", "c.pattern_recognized"), 2, "c.list.pattern"),
    (("c.some_correct",), 1, "c.list.some"),
    ((), 0, None),
    (("c.several_correct",), 0, None),
    (("c.complete_list",), 0, None),
])
def test_item_c_selects_one_integrally_satisfied_list_band(pilot, ids, points, band):
    item = evaluate(pilot, *(evidence(i) for i in ids)).items[2]
    portion = item.children[2]
    assert portion.points_awarded == item.points_awarded == points
    assert portion.selected_band == band


def test_all_bands_never_accumulate_and_full_problem_is_twenty(pilot):
    result = evaluate(pilot, *(evidence(o.id) for o in pilot.obligations))
    assert [i.points_awarded for i in result.items] == [3, 5, 6, 6]
    assert result.score == result.known_points == result.possible_points == 20
    assert result.items[0].selected_band == "a.full"
    assert result.items[2].children[2].points_awarded == 4  # never 4+3+2+1
    assert result.items[2].children[2].selected_band == "c.list.full"


def test_full_pilot_needs_no_error_claims_or_lower_band_evidence(pilot):
    irrelevant = {"a.arithmetic_error_only", "c.single_list_error", "c.several_correct",
                  "c.pattern_recognized", "c.some_correct"}
    result = evaluate(pilot, *(evidence(o.id) for o in pilot.obligations if o.id not in irrelevant))
    assert result.score == result.known_points == result.possible_points == 20
    assert not result.needs_review
    assert [i.points_awarded for i in result.items] == [3, 5, 6, 6]


def test_bare_expression_cannot_supply_item_b_justification(pilot):
    result = evaluate(pilot, evidence("c.uses_expression"))
    assert result.items[1].points_awarded == 0
    assert result.items[2].points_awarded == 1
    # Even an upstream verified factorization supplies only its declared point.
    assert evaluate(pilot, evidence("b.factorization")).items[1].points_awarded == 1


def test_b_subtraction_requires_cancellation_and_d_requires_counting_argument(pilot):
    result = evaluate(pilot, evidence("b.subtraction"), evidence("d.total_thirty"))
    assert result.items[1].points_awarded == result.items[3].points_awarded == 0
    result = evaluate(pilot, evidence("b.subtraction"), evidence("b.middle_cancellation"),
                      evidence("d.middle_choices"), evidence("d.total_thirty"))
    assert result.items[1].points_awarded == result.items[3].points_awarded == 2


@pytest.mark.parametrize("supported", [("x",), ("y",), ("x", "y")])
def test_alternative_methods_each_get_full_credit_once(supported):
    cfg = config(dict(id="item", scoring_strategy="max_of", max_points=3,
        children=[atom("official", 3, "x"), atom("alternative", 3, "y")]))
    item = evaluate(cfg, *(evidence(i) for i in supported)).items[0]
    assert item.points_awarded == 3
    assert item.selected_method_path == ("official" if "x" in supported else "alternative")
    assert item.status == "decided" and not item.needs_review
    assert item.credit_evidence_refs == ("source:" + supported[0],)


def test_max_of_chooses_partial_method_without_summing_paths():
    cfg = config(dict(id="item", scoring_strategy="max_of", max_points=4, children=[
        dict(id="official", scoring_strategy="additive", max_points=4,
             children=[atom("step1", 2, "x"), atom("step2", 2, "y")]),
        atom("alternative", 4, "z")]), policy="withhold", obligations=("x", "y", "z"))
    item = evaluate(cfg, evidence("x"), evidence("z", "refuted")).items[0]
    assert item.points_awarded == 2 and item.selected_method_path == "official"
    assert item.possible_points == 4 and item.needs_review


@pytest.mark.parametrize("strategy,states", product(("all_of", "any_of"),
    product(("supported", "refuted", "indeterminate", "technical_error"), repeat=2)))
def test_four_status_predicates_do_not_conflate_unknown_with_refutation(strategy, states):
    cfg = config(atom("item", 2, "x", "y", strategy=strategy))
    item = evaluate(cfg, *(evidence(i, s) for i, s in zip(("x", "y"), states))).items[0]
    if (strategy == "all_of" and states == ("supported", "supported")) or (strategy == "any_of" and "supported" in states):
        assert item.points_awarded == 2 and item.status == "decided"
    elif (strategy == "all_of" and "refuted" in states) or states == ("refuted", "refuted"):
        assert item.points_awarded == 0 and item.status == "decided"
    else:
        assert item.points_awarded is None and item.known_points == 0 and item.possible_points == 2
        assert item.status == ("technical_error" if "technical_error" in states else "indeterminate")
    assert item.unsatisfied_obligations == tuple(i for i, s in zip(("x", "y"), states) if s == "refuted")
    assert item.technical_error_obligations == tuple(i for i, s in zip(("x", "y"), states) if s == "technical_error")


def test_unknown_default_defers_but_explicit_withhold_is_not_refutation():
    cfg = config(atom("item", 2, "x"))
    result = evaluate(cfg)
    assert result.score is None and result.known_points == 0 and result.possible_points == 2
    cfg = config(atom("item", 2, "x"), policy="withhold")
    result = evaluate(cfg)
    assert result.score == 0 and result.needs_review
    assert result.items[0].status == "indeterminate"
    assert result.items[0].indeterminate_obligations == ("x",)
    assert result.items[0].unsatisfied_obligations == ()
    assert result.items[0].evidence_refs == result.items[0].credit_evidence_refs == ()


def test_withhold_does_not_turn_technical_failure_into_zero():
    cfg = config(atom("item", 2, "x"), policy="withhold")
    result = evaluate(cfg, evidence("x", "technical_error"))
    assert result.score is None and result.items[0].status == "technical_error"
    assert not result.items[0].unsatisfied_obligations


def test_banded_preserves_lower_credit_and_uncertainty_of_higher_band():
    rule = dict(id="item", scoring_strategy="banded", max_points=3,
                children=[atom("high", 3, "x", "y"), atom("low", 1, "x")])
    result = evaluate(config(rule), evidence("x"))
    assert result.score is None and result.known_points == 1 and result.possible_points == 3
    assert result.items[0].selected_band == "low"
    assert evaluate(config(rule, policy="withhold"), evidence("x")).score == 1
    assert evaluate(config(rule, policy="withhold"), evidence("x"), evidence("y", "technical_error")).score is None


def test_additive_cap_and_decimal_points_are_exact():
    cfg = config(dict(id="item", scoring_strategy="additive", max_points="0.3",
        children=[atom("one", "0.1", "x"), atom("two", "0.2", "y")]))
    result = evaluate(cfg, evidence("x"), evidence("y"))
    assert result.score == Decimal("0.3")
    cfg = config(dict(id="item", scoring_strategy="additive", max_points=3,
        children=[atom("one", 2, "x"), atom("two", 2, "y")]))
    assert evaluate(cfg, evidence("x"), evidence("y")).score == 3


@pytest.mark.parametrize("origin", ["reference_lean", "semantic", "secondary", "diagram"])
def test_unapproved_origins_cannot_fabricate_primary_credit(origin):
    result = evaluate(config(atom("item", 2, "x")), evidence("x", origin=origin))
    assert result.score is None and result.items[0].known_points == 0
    assert result.items[0].obligations[0].origin == origin
    assert result.items[0].obligations[0].input_status == "supported"
    assert result.items[0].obligations[0].reason == "ORIGIN_NOT_ACCEPTED"


@pytest.mark.parametrize("origin", ["secondary", "semantic", "diagram"])
def test_explicitly_accepted_nonprimary_origin_preserves_review_and_provenance(origin):
    data = config(atom("item", 2, "x")).model_dump()
    data["obligations"][0]["accepted_origins"] = [origin]
    result = evaluate(PautaConfig.model_validate(data), evidence("x", origin=origin))
    assert result.score == 2 and result.needs_review
    assert result.items[0].evidence_refs == ("source:x",)
    assert result.items[0].obligations[0].origin == origin


@pytest.mark.parametrize("status", ["supported", "refuted"])
def test_unattributed_assertion_is_neither_credit_nor_student_refutation(status):
    result = evaluate(config(atom("item", 2, "x")), evidence("x", status, attributable_to_student=False))
    assert result.score is None
    assert result.items[0].obligations[0].reason == "NOT_ATTRIBUTABLE_TO_STUDENT"
    assert not result.items[0].unsatisfied_obligations


def test_immutable_reproducible_round_trip(pilot):
    payload = PautaEvidence(problem_id=pilot.problem_id, solution_id="s", obligations=(evidence("a.identifies_137"),))
    before = (pilot.model_dump_json(), payload.model_dump_json())
    engine = PautaEngine()
    first = engine.evaluate(pilot, payload)
    second = engine.evaluate(PautaConfig.model_validate_json(before[0]), PautaEvidence.model_validate_json(before[1]))
    assert first.model_dump_json() == second.model_dump_json()
    assert len(first.config_sha256) == len(first.evidence_sha256) == 64
    assert before == (pilot.model_dump_json(), payload.model_dump_json())
    assert type(first).model_validate_json(first.model_dump_json()) == first
    with pytest.raises(ValidationError):
        pilot.max_score = 100


@pytest.mark.parametrize("value", [-1, True, "NaN", "Infinity", float("inf")])
def test_invalid_points_rejected(value):
    with pytest.raises(ValidationError):
        config(atom("item", value, "x"))


@pytest.mark.parametrize("mutation", [
    lambda d: d.update(schema_version="pauta.v2"),
    lambda d: d.update(typo=True),
    lambda d: d.update(max_score=99),
    lambda d: d["items"][0].update(obligation_ids=[]),
    lambda d: d["items"][0].update(obligation_ids=["missing"]),
    lambda d: d["items"][0].update(obligation_ids=["x", "x"]),
    lambda d: d["items"][0].update(scoring_strategy="guess"),
    lambda d: d["obligations"][0].update(accepted_origins=["reference_lean"]),
])
def test_closed_schema_rejects_invalid_rule_contracts(mutation):
    data = deepcopy(config(atom("item", 2, "x")).model_dump())
    mutation(data)
    with pytest.raises(ValidationError):
        PautaConfig.model_validate(data)


def test_duplicate_rule_ids_and_partial_bands_are_rejected():
    rule = dict(id="item", scoring_strategy="additive", max_points=4,
                children=[atom("same", 2, "x"), atom("same", 2, "y")])
    with pytest.raises(ValidationError, match="globally unique"):
        config(rule)
    rule = dict(id="item", scoring_strategy="banded", max_points=4, children=[
        dict(id="partial", scoring_strategy="additive", max_points=4,
             children=[atom("x", 2, "x"), atom("y", 2, "y")])])
    with pytest.raises(ValidationError, match="integral predicate"):
        config(rule)


def test_evidence_ids_and_problem_scope_are_validated():
    cfg = config(atom("item", 2, "x"))
    with pytest.raises(ValidationError, match="references"):
        evidence("x", evidence_refs=())
    with pytest.raises(ValidationError, match="duplicate/conflicting"):
        evaluate(cfg, evidence("x"), evidence("x", "refuted"))
    with pytest.raises(ValueError, match="undeclared"):
        evaluate(cfg, evidence("unknown"))
    with pytest.raises(ValueError, match="different problem"):
        PautaEngine().evaluate(cfg, PautaEvidence(problem_id="other", solution_id="s"))
    with pytest.raises(ValueError):
        evaluate(cfg.model_copy(update={"max_score": Decimal(-10)}), evidence("x"))


def test_duplicate_json_keys_are_rejected(tmp_path):
    path = tmp_path / "pauta.json"
    path.write_text('{"max_score":20,"max_score":200}')
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        load_pauta(path)


def carry_config():
    data = config(atom("previous", 1, "prior"), policy="withhold",
                  obligations=("prior", "absolute", "adoption", "dependency", "coherence")).model_dump()
    data["max_score"] = 3
    data["items"] = [data["items"][0], dict(id="later", scoring_strategy="max_of", max_points=2,
        children=[atom("normal", 2, "absolute"), dict(id="cf", scoring_strategy="carry_forward", max_points=2,
            carry_forward=dict(prior_obligation_id="prior", adoption_obligation_id="adoption",
                dependency_obligation_id="dependency", coherence_obligation_id="coherence"))])]
    return PautaConfig.model_validate(data)


def carry_records(coherence="supported"):
    context = ConditionalContext(rule_id="cf", prior_obligation_id="prior", adopted_result_ref="result:wrong")
    return [evidence("prior", "refuted", evidence_refs=("result:wrong", "check:prior")),
            evidence("absolute", "refuted"),
            evidence("adoption", conditional_on=context, evidence_refs=("result:wrong", "check:adoption")),
            evidence("dependency", conditional_on=context),
            evidence("coherence", coherence, conditional_on=context)]


def test_carry_forward_preserves_prior_error_without_second_penalty():
    result = evaluate(carry_config(), *carry_records())
    assert [i.points_awarded for i in result.items] == [0, 2]
    assert result.score == 2
    later = result.items[1]
    assert later.selected_method_path == "cf" and later.carry_forward_applied
    assert "prior" in later.unsatisfied_obligations
    assert "result:wrong" in later.credit_evidence_refs


def test_carry_forward_does_not_forgive_incorrect_conditional_work():
    result = evaluate(carry_config(), *carry_records("refuted"))
    assert result.score == 0 and not result.items[1].carry_forward_applied
    assert "coherence" in result.items[1].unsatisfied_obligations


@pytest.mark.parametrize("missing", ["adoption", "dependency", "coherence"])
def test_each_carry_forward_fact_is_mandatory(missing):
    result = evaluate(carry_config(), *(e for e in carry_records() if e.obligation_id != missing))
    assert result.score == 0 and result.needs_review
    assert not result.items[1].carry_forward_applied


@pytest.mark.parametrize("change", [dict(rule_id="other"), dict(prior_obligation_id="other"),
                                   dict(adopted_result_ref="different-result")])
def test_carry_forward_cannot_join_unrelated_evidence(change):
    records = carry_records()
    records[-1] = records[-1].model_copy(update={"conditional_on": records[-1].conditional_on.model_copy(update=change)})
    result = evaluate(carry_config(), *records)
    assert result.score == 0 and not result.items[1].carry_forward_applied


def test_carry_forward_needs_the_actual_adopted_record_and_a_known_prior_error():
    records = carry_records()
    records[0] = evidence("prior", "refuted", evidence_refs=("unrelated-result",))
    assert evaluate(carry_config(), *records).score == 0
    records = carry_records()
    records[0] = evidence("prior", "indeterminate", evidence_refs=("result:wrong",))
    assert evaluate(carry_config(), *records).score == 0


def test_conditional_coherence_cannot_be_reused_as_unconditional_achievement():
    cfg = config(atom("item", 2, "coherence"), obligations=("coherence",))
    result = evaluate(cfg, carry_records()[-1])
    assert result.score is None and not result.items[0].credit_evidence_refs
    assert result.items[0].obligations[0].reason == "CONDITIONAL_EVIDENCE_NOT_UNCONDITIONAL"


def test_technical_failure_in_carry_forward_remains_pending():
    result = evaluate(carry_config(), *carry_records("technical_error"))
    assert result.score is None and result.items[1].status == "technical_error"
    assert "coherence" not in result.items[1].unsatisfied_obligations


def test_zero_point_band_still_requires_evidence_to_be_satisfied():
    cfg = config(dict(id="item", scoring_strategy="banded", max_points=2,
        children=[atom("high", 2, "x"), atom("explicit_zero", 0, "y")]), policy="withhold")
    item = evaluate(cfg).items[0]
    assert item.selected_band is None and not item.children[1].fully_satisfied
    item = evaluate(cfg, evidence("y")).items[0]
    assert item.selected_band == "explicit_zero" and item.points_awarded == 0


def test_decision_fingerprints_bind_exact_config_and_evidence():
    cfg = config(atom("item", 2, "x"))
    first = evaluate(cfg, evidence("x"))
    second = evaluate(cfg, evidence("x", evidence_refs=("different-record",)))
    third = evaluate(config(atom("item", 2, "x"), policy="withhold"), evidence("x"))
    assert first.score == second.score == third.score == 2
    assert first.config_sha256 == second.config_sha256 != third.config_sha256
    assert first.evidence_sha256 != second.evidence_sha256


def test_attribution_is_a_strict_boolean_not_truthy_text():
    with pytest.raises(ValidationError):
        evidence("x", attributable_to_student="true")


def test_secondary_denial_cannot_be_labeled_mathematical_refutation():
    with pytest.raises(ValidationError, match="not a mathematical refutation"):
        evidence("x", "refuted", origin="secondary")


def test_output_contract_cannot_promote_potential_points_or_fabricate_references():
    item = evaluate(config(atom("item", 2, "x"))).items[0]
    with pytest.raises(ValidationError, match="potential points"):
        type(item).model_validate(item.model_dump() | {"points_awarded": 2})
    item = evaluate(config(atom("item", 2, "x")), evidence("x")).items[0]
    with pytest.raises(ValidationError, match="traceable"):
        type(item).model_validate(item.model_dump() | {"credit_evidence_refs": ()})
    with pytest.raises(ValidationError, match="observed references"):
        type(item).model_validate(item.model_dump() | {"credit_evidence_refs": ("invented",)})


def test_noncritical_technical_failure_does_not_block_a_proven_alternative():
    cfg = config(dict(id="item", scoring_strategy="max_of", max_points=2,
        children=[atom("official", 2, "x"), atom("alternative", 2, "y")]))
    item = evaluate(cfg, evidence("x", "technical_error"), evidence("y")).items[0]
    assert item.points_awarded == 2 and item.selected_method_path == "alternative"
    assert item.technical_error_obligations == ("x",) and not item.unsatisfied_obligations
    assert item.needs_review
