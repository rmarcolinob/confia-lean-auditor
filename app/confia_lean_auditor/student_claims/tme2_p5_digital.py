"""P5 typed DIGITAL grammar. Lists, products and arguments are distinct types."""
from .digital_items import collect_digital_items
from .named_math import extract_named_math

PROBLEM_ID='TME2026P5'
VOCABULARY={k:{'kind':'math'} for k in (
    'product','enum_max','old_contribution','new_contribution','threes_count','twos_count',
    'residue0_twos','residue0_threes','residue1_twos','residue1_threes','residue2_twos','residue2_threes',
    'size_twos','size_four','cf_adopt_threes','cf_size_twos','cf_size_four')}
VOCABULARY.update({k:{'kind':'relation'} for k in (
    'sum_preserved','domain','increase','difference','positive_difference',
    'one_domain','one_sum','one_gain','four_sum','four_product','twos_sum','twos_gain',
    'decomposition','quotient','different_sizes','cf_different_sizes')})
VOCABULARY.update({k:{'kind':'positive_multiset'} for k in ('candidate','normal_list','list_twos','list_four')})
VOCABULARY['enumeration']={'kind':'partition_table'}
VOCABULARY['max_product']={'kind':'factored_product'}
VOCABULARY['only_forms']={'kind':'enum','values':{'merge_two_twos':'merge_two_twos'}}
VOCABULARY['cf_dependency']={'kind':'enum','values':{'sizes_from_adopted_threes':'sizes_from_adopted_threes'}}


def extract_p5_quantities(problem_id, source):
    return extract_named_math(problem_id,source,VOCABULARY)


def collect_tme2_p5_digital(items):
    return collect_digital_items(PROBLEM_ID,items,item_ids='abcd',literal_extractors=(extract_p5_quantities,))
