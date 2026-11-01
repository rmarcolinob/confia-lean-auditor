"""P4 explicit mapping and orchestration; all points belong to PautaEngine."""
from confia_lean_auditor.lean.student_claim_checkers.tme2_p4 import verify_tme2_p4_digital
from confia_lean_auditor.student_claims.tme2_p4_digital import PROBLEM_ID, collect_tme2_p4_digital
from .bridge import bridge_facts
from .engine import PautaEngine

TME2_P4_OBLIGATIONS = {name: name for name in (
    'a.triangle_pbq',
    'a.pb',
    'a.bq',
    'a.pq',
    'a.perimeter_pbq',
    'a.triangle_rqc',
    'a.qc',
    'a.qr',
    'a.rc',
    'a.perimeter_rqc',
    'a.shaded_sum',
    'b.ap',
    'b.qr',
    'b.pq',
    'b.ar',
    'b.apqr',
    'b.perimeter_apqr',
    'c.perimeter_pbq',
    'c.perimeter_rqc',
    'c.perimeter_apqr',
    'c.exclude_12',
    'c.h_plus_c',
    'c.pythagoras',
    'c.h',
    'c.c',
    'c.shaded_lengths',
    'c.x_candidates',
    'c.case_3x',
    'c.case_other',
    'c.case_3x_root',
    'c.case_other_root',
)}


def bridge_tme2_p4(config, bundle):
    return bridge_facts(config, bundle, problem_id=PROBLEM_ID,
        obligation_map=TME2_P4_OBLIGATIONS, mapping_version="tme2-p4-obligations.v1")


def audit_tme2_p4_digital(config, items, solution_id, *, use_lean=True, run_id=None):
    digital = collect_tme2_p4_digital(items)
    bundle = verify_tme2_p4_digital(digital, solution_id, use_lean=use_lean, run_id=run_id)
    bridge = bridge_tme2_p4(config, bundle)
    return bridge, PautaEngine().evaluate(config, bridge.evidence)
