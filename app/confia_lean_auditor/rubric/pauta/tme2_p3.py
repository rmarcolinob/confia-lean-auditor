"""P3 orchestration and explicit fact map; the scoring engine stays pure."""
from confia_lean_auditor.lean.student_claim_checkers.tme2_p3 import verify_tme2_p3_digital
from confia_lean_auditor.student_claims.tme2_p3_digital import PROBLEM_ID, collect_tme2_p3_digital
from .bridge import bridge_facts
from .engine import PautaEngine

TME2_P3_OBLIGATIONS = {name: name for name in (
    "a.bottom_white_count", "a.first_white_probability", "b.ordered_pairs",
    "b.different_favorable", "b.same_compartment", "b.second_white_probability",
    "b.alternative_complete", "c.continue_compartments", "c.strategy_case_1",
    "c.strategy_case_2", "c.conditional_success_1", "c.conditional_success_2",
    "c.total_win_probability")}


def bridge_tme2_p3(config, bundle):
    return bridge_facts(config, bundle, problem_id=PROBLEM_ID,
        obligation_map=TME2_P3_OBLIGATIONS, mapping_version="tme2-p3-obligations.v1")


def audit_tme2_p3_digital(config, items, solution_id, machine, *, use_lean=True, run_id=None):
    digital = collect_tme2_p3_digital(items)
    bundle = verify_tme2_p3_digital(digital, solution_id, machine, use_lean=use_lean, run_id=run_id)
    bridge = bridge_tme2_p3(config, bundle)
    return bridge, PautaEngine().evaluate(config, bridge.evidence)
