"""P5 orchestration with an explicit fact map; the engine alone assigns points."""
from confia_lean_auditor.lean.student_claim_checkers.tme2_p5 import verify_tme2_p5_digital
from confia_lean_auditor.student_claims.tme2_p5_digital import PROBLEM_ID, collect_tme2_p5_digital
from .bridge import bridge_facts
from .engine import PautaEngine

TME2_P5_OBLIGATIONS = {name: name for name in (
    'a.candidate',
    'a.product',
    'a.enumeration',
    'a.structural_max',
    'a.normal_list',
    'a.one_domain',
    'a.one_sum',
    'a.one_gain',
    'a.domain',
    'a.sum_preserved',
    'a.increase',
    'a.four_sum',
    'a.four_product',
    'a.twos_sum',
    'a.twos_gain',
    'b.domain',
    'b.sum_preserved',
    'b.increase',
    'b.old_contribution',
    'b.new_contribution',
    'b.comparison',
    'c.one_domain',
    'c.one_sum',
    'c.one_gain',
    'c.domain',
    'c.sum_preserved',
    'c.increase',
    'c.four_sum',
    'c.four_product',
    'c.twos_sum',
    'c.twos_gain',
    'c.no_ones',
    'c.no_ge5',
    'c.threes_count',
    'c.twos_count',
    'c.decomposition',
    'c.max_product',
    'c.general_rule',
    'c.quotient',
    'c.general_complete',
    'c.residue0_twos',
    'c.residue0_threes',
    'c.residue1_twos',
    'c.residue1_threes',
    'c.residue2_twos',
    'c.residue2_threes',
    'd.list_twos',
    'd.list_four',
    'd.four_sum',
    'd.four_product',
    'd.uniqueness',
    'd.size_twos',
    'd.size_four',
    'd.different_sizes',
    'd.sizes',
    'd.cf_adoption',
    'd.cf_dependency',
    'd.cf_coherence',
)}


def bridge_tme2_p5(config,bundle):
    return bridge_facts(config,bundle,problem_id=PROBLEM_ID,
        obligation_map=TME2_P5_OBLIGATIONS,mapping_version="tme2-p5-obligations.v1")


def audit_tme2_p5_digital(config,items,solution_id,*,use_lean=True,run_id=None):
    digital=collect_tme2_p5_digital(items)
    bundle=verify_tme2_p5_digital(digital,solution_id,use_lean=use_lean,run_id=run_id)
    bridge=bridge_tme2_p5(config,bundle)
    return bridge,PautaEngine().evaluate(config,bridge.evidence)
