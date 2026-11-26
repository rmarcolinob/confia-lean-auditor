"""P2 text collection and explicit mixed text/structured-diagram input envelope."""
from .digital_items import collect_digital_items
from .named_math import extract_named_math
from confia_lean_auditor.tme.p2_diagram import DiagramSubmission

PROBLEM_ID='TME2026P2'
VOCABULARY={k:{'kind':'math'} for k in ('pair_sum','line_sum','sum_formula','admissible_center','sum_at_five','max_center','max_sum')}
VOCABULARY.update({k:{'kind':'integer_pairs'} for k in ('pairs','center_sums','realizable_1','realizable_5','realizable_9')})
VOCABULARY['centers']={'kind':'integer_set'}
VOCABULARY['placement']={'kind':'integer_mapping'}
VOCABULARY['balance_relation']={'kind':'relation'}
VOCABULARY['modular_condition']={'kind':'congruence'}
VOCABULARY['integral_sum']={'kind':'enum','values':{'integer':'integer','inteiro':'integer','z':'integer'}}
VOCABULARY.update({k:{'kind':'combinatorial_math'} for k in ('pair_permutations','pair_orientations','total','counting_product')})


def extract_p2_quantities(problem_id,source):
    return extract_named_math(problem_id,source,VOCABULARY,
        introductions={'Os pares são':'pairs','Os pares sao':'pairs'})


def collect_tme2_p2_text(items):
    return collect_digital_items(PROBLEM_ID,items,item_ids='abc',literal_extractors=(extract_p2_quantities,))


def split_p2_input(solution):
    if not isinstance(solution,dict) or not set(solution)<=set('abc'):
        raise ValueError('P2 accepts explicitly separated a/b/c items')
    texts={};diagrams={}
    for item,value in solution.items():
        if isinstance(value,str):texts[item]=value;continue
        if not isinstance(value,dict) or not set(value)<= {'text','diagrams'}:
            raise ValueError('Use item text or {text, diagrams}; no image recognition is implicit')
        text=value.get('text','');entries=value.get('diagrams',[])
        if not isinstance(text,str) or not isinstance(entries,list) or len(entries)>8:
            raise ValueError('Invalid text/structured diagram envelope')
        texts[item]=text
        diagrams[item]=tuple(DiagramSubmission.model_validate(e) for e in entries)
    return texts,diagrams
