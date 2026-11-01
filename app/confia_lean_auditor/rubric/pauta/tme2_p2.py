"""P2 mixed evidence orchestration; all scoring remains in the existing engine."""
from confia_lean_auditor.lean.student_claim_checkers.tme2_p2 import verify_tme2_p2
from confia_lean_auditor.student_claims.tme2_p2_digital import PROBLEM_ID,split_p2_input,collect_tme2_p2_text
from .bridge import bridge_facts
from .engine import PautaEngine

TME2_P2_OBLIGATIONS={name:name for name in (
    'a.pair_sum',
    'a.line_sum',
    'a.pairs',
    'a.placement',
    'a.complete_configuration',
    'b.balance_relation',
    'b.sum_formula',
    'b.integral_sum',
    'b.modular_condition',
    'b.centers',
    'b.admissible_center',
    'b.center_sums',
    'b.sum_at_five',
    'b.realizable_1',
    'b.realizable_5',
    'b.realizable_9',
    'c.max_center',
    'c.max_sum',
    'c.pairs',
    'c.pair_permutations',
    'c.pair_orientations',
    'c.total',
    'c.counting_product',
)}


DIAGRAM_FACTS=frozenset(('a.complete_configuration','a.placement','a.pairs','a.pair_sum',
    'b.realizable_1','b.realizable_5','b.realizable_9','c.max_center','c.max_sum','c.pairs'))


def bridge_tme2_p2(config,bundle):
    return bridge_facts(config,bundle,problem_id=PROBLEM_ID,
        obligation_map=TME2_P2_OBLIGATIONS,mapping_version="tme2-p2-obligations.v1",
        structured_fact_ids=DIAGRAM_FACTS)


def audit_tme2_p2(config,solution,solution_id,*,use_lean=True,run_id=None):
    texts,diagrams=split_p2_input(solution)
    digital=collect_tme2_p2_text(texts)
    bundle=verify_tme2_p2(digital,diagrams,solution_id,use_lean=use_lean,run_id=run_id)
    bridge=bridge_tme2_p2(config,bundle)
    return bridge,PautaEngine().evaluate(config,bridge.evidence)
