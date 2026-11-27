"""Small opt-in mathematical registry; separate from ITA and HTTP /audit."""
from pathlib import Path
from types import MappingProxyType
from uuid import uuid4

from confia_lean_auditor.rubric.pauta import load_pauta

ROOT = Path(__file__).resolve().parents[3]
TME_PROBLEMS = MappingProxyType({
    "TME2_P1_PILOT": "tme2_problem1.v1.json",
    "TME2026P3": "tme2_problem3.v1.json",
    "TME2026P4": "tme2_problem4.v1.json",
    "TME2026P5": "tme2_problem5.v1.json",
    "TME2026P2": "tme2_problem2.v1.json",
})


def audit_tme(problem_id, solution, *, solution_id=None, use_lean=True, run_id=None):
    """solution is a mapping of explicit DIGITAL items, as in the P1 pilot."""
    # Public P1 spelling is an alias; preserve existing mathematical IDs/hashes.
    if problem_id == "TME2026P1":
        problem_id = "TME2_P1_PILOT"
    if problem_id not in TME_PROBLEMS:
        raise ValueError("Unsupported opt-in TME problem")
    if not isinstance(solution, dict):
        raise ValueError("Use an explicit item-to-text mapping, e.g. {'a': '1/3'}")
    config = load_pauta(ROOT / "examples/pautas" / TME_PROBLEMS[problem_id])
    solution_id = solution_id or "tme-" + uuid4().hex
    if problem_id == "TME2026P2":
        from confia_lean_auditor.rubric.pauta.tme2_p2 import audit_tme2_p2
        return audit_tme2_p2(config, solution, solution_id, use_lean=use_lean, run_id=run_id)
    if problem_id == "TME2_P1_PILOT":
        from confia_lean_auditor.rubric.pauta.tme2_p1 import audit_tme2_p1_digital
        return audit_tme2_p1_digital(config, solution, solution_id, use_lean=use_lean, run_id=run_id)
    if problem_id == "TME2026P4":
        from confia_lean_auditor.rubric.pauta.tme2_p4 import audit_tme2_p4_digital
        return audit_tme2_p4_digital(config, solution, solution_id, use_lean=use_lean, run_id=run_id)
    if problem_id == "TME2026P5":
        from confia_lean_auditor.rubric.pauta.tme2_p5 import audit_tme2_p5_digital
        return audit_tme2_p5_digital(config, solution, solution_id, use_lean=use_lean, run_id=run_id)
    from confia_lean_auditor.rubric.pauta.tme2_p3 import audit_tme2_p3_digital
    from .p3_machine import load_machine
    machine = load_machine(ROOT / "examples/pautas/tme2_problem3.machine.v1.json")
    return audit_tme2_p3_digital(config, solution, solution_id, machine, use_lean=use_lean, run_id=run_id)
