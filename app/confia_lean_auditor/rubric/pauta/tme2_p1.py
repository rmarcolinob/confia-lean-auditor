"""Explicit DIGITAL pilot orchestration, outside the pure PautaEngine."""
from confia_lean_auditor.student_claims.tme2_p1_digital import collect_tme2_p1_digital
from confia_lean_auditor.lean.student_claim_checkers.tme2_p1 import verify_tme2_p1_digital
from .bridge import bridge_tme2_p1
from .engine import PautaEngine


def audit_tme2_p1_digital(config, items, solution_id, *, use_lean=True, run_id=None):
    digital = collect_tme2_p1_digital(items)
    facts = verify_tme2_p1_digital(digital, solution_id, use_lean=use_lean, run_id=run_id)
    bridge = bridge_tme2_p1(config, facts)
    return bridge, PautaEngine().evaluate(config, bridge.evidence)
