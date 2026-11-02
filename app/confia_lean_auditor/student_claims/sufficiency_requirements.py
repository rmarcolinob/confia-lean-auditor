"""Point-free evidence requirements, separate from immutable scoring pautas."""
from enum import Enum
from .hybrid_semantic import catalog
from .obligation_catalog import internal_id


class EvidenceRequirement(str, Enum):
    FINAL_ANSWER = 'FINAL_ANSWER'
    FACT = 'FACT'
    INTERMEDIATE_STEP = 'INTERMEDIATE_STEP'
    JUSTIFICATION = 'JUSTIFICATION'
    COMPLETE_METHOD = 'COMPLETE_METHOD'
    ENUMERATION = 'ENUMERATION'
    STRATEGY = 'STRATEGY'


# Classification by mathematical role, never by student/case ID or score.
ROLE_GROUPS = {
 'TME2_P1_PILOT': {
  'FINAL_ANSWER': 'a.result_594 d.total_thirty',
  'FACT': 'a.identifies_137 a.arithmetic_error_only',
  'INTERMEDIATE_STEP': 'a.constructs_subtraction b.reversed_number b.subtraction d.equation d.difference_six',
  'JUSTIFICATION': 'b.middle_cancellation b.factorization c.uses_expression c.difference_domain c.pattern_recognized d.middle_choices',
  'ENUMERATION': 'c.complete_list c.no_extraneous_values c.single_list_error c.several_correct c.some_correct d.digit_pairs',
 },
 'TME2026P2': {
  'FINAL_ANSWER': 'c.max_sum c.total',
  'FACT': 'a.pair_sum a.line_sum b.integral_sum b.admissible_center b.sum_at_five c.max_center',
  'INTERMEDIATE_STEP': 'b.balance_relation b.sum_formula',
  'JUSTIFICATION': 'b.modular_condition b.centers c.pair_permutations c.pair_orientations c.counting_product',
  'COMPLETE_METHOD': 'a.placement a.complete_configuration',
  'ENUMERATION': 'a.pairs b.center_sums b.realizable_1 b.realizable_5 b.realizable_9 c.pairs',
 },
 'TME2026P3': {
  'FINAL_ANSWER': 'a.first_white_probability b.second_white_probability',
  'FACT': 'a.bottom_white_count c.continue_compartments',
  'INTERMEDIATE_STEP': 'b.ordered_pairs c.conditional_success_1 c.conditional_success_2',
  'JUSTIFICATION': 'b.different_favorable b.same_compartment c.total_win_probability',
  'COMPLETE_METHOD': 'b.alternative_complete',
  'STRATEGY': 'c.strategy_case_1 c.strategy_case_2',
 },
 'TME2026P4': {
  'FINAL_ANSWER': 'c.x_candidates',
  'FACT': 'a.triangle_pbq a.triangle_rqc b.apqr c.perimeter_pbq c.perimeter_rqc c.perimeter_apqr',
  'INTERMEDIATE_STEP': 'a.pb a.bq a.pq a.qc a.qr a.rc a.perimeter_pbq a.perimeter_rqc b.ap b.qr b.pq b.ar c.h_plus_c c.pythagoras c.h c.c c.shaded_lengths c.case_3x c.case_other c.case_3x_root c.case_other_root',
  'JUSTIFICATION': 'a.shaded_sum c.exclude_12',
  'COMPLETE_METHOD': 'b.perimeter_apqr',
 },
}
P5_ROLES = {
 'FACT': 'one_domain domain threes_count twos_count residue0_twos residue0_threes residue1_twos residue1_threes residue2_twos residue2_threes cf_adoption cf_dependency',
 'FINAL_ANSWER': 'max_product size_twos size_four different_sizes',
 'INTERMEDIATE_STEP': 'product normal_list one_sum sum_preserved old_contribution new_contribution four_sum four_product twos_sum decomposition quotient',
 'JUSTIFICATION': 'one_gain increase comparison twos_gain no_ones no_ge5 general_rule uniqueness sizes cf_coherence',
 'COMPLETE_METHOD': 'structural_max general_complete',
 'ENUMERATION': 'candidate enumeration list_twos list_four',
}

# Only these obligations explicitly permit mathematical evidence from these
# earlier items. No problem-wide blanket cross-item permission.
CROSS_ITEM = {
 'TME2_P1_PILOT': {'c.uses_expression': ['b']},
 'TME2026P2': {'b.realizable_5': ['a'], 'c.pairs': ['b']},
 'TME2026P3': {},
 'TME2026P4': {'b.qr':['a'], 'b.pq':['a'], 'c.perimeter_pbq':['a'],
              'c.perimeter_rqc':['a'], 'c.perimeter_apqr':['b'], 'c.h_plus_c':['a']},
 'TME2026P5': {'c.no_ge5':['b'], 'c.domain':['b'], 'c.sum_preserved':['b'],
              'c.increase':['b'], 'd.four_sum':['c'], 'd.four_product':['c']},
}

REQUIREMENT_GUIDANCE = {
 'FINAL_ANSWER': 'Conclusão explícita correta, com unidade/objeto correto. Preserve erros e contradições escritos; não substitua a resposta pela esperada.',
 'FACT': 'Fato matemático realmente afirmado ou imediatamente implicado pelos trechos; não invente cálculos ou dados ausentes.',
 'INTERMEDIATE_STEP': 'Passo intermediário efetivamente desenvolvido. Ter a resposta final correta não demonstra que o passo ocorreu.',
 'JUSTIFICATION': 'Argumento que sustenta a conclusão, incluindo sua validade. Conclusão isolada, tautologia e raciocínio inválido não bastam.',
 'COMPLETE_METHOD': 'Todos os ingredientes matemáticos do método exigido, com suas consequências. Nome de método e resposta final sem desenvolvimento não bastam.',
 'ENUMERATION': 'Verifique os elementos e multiplicidades realmente presentes; diferencie lista completa, parcial e reticências. Não complete entradas ausentes.',
 'STRATEGY': 'A ação/decisão deve estar ligada ao caso e às consequências matemáticas exigidas; estratégia errada com probabilidade final correta não basta.',
}


def requirements(problem_id):
    problem = internal_id(problem_id)
    groups = ROLE_GROUPS.get(problem, P5_ROLES)
    lookup = {oid:kind for kind,ids in groups.items() for oid in ids.split()}
    result = []
    for o in catalog(problem):
        key = o['obligation_id'].split('.',1)[1] if problem=='TME2026P5' else o['obligation_id']
        kind = lookup[key]  # Missing declarations fail closed during preparation.
        result.append(dict(obligation_id=o['obligation_id'],item_id=o['item_id'],
            obligation_description=o['mathematical_requirement'],evidence_requirement=kind,
            sufficiency_requirement=REQUIREMENT_GUIDANCE[kind],
            authorized_source_items=CROSS_ITEM[problem].get(o['obligation_id'],[])))
    return tuple(result)
