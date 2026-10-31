"""P3 notation and item routing; mathematical assertions remain common records."""
from .digital_items import collect_digital_items
from .digital_literals import extract_digital_literals
from .named_math import extract_named_math

PROBLEM_ID = "TME2026P3"
COLORS = {"branca": "white", "branco": "white", "white": "white",
          "preta": "black", "preto": "black", "black": "black",
          "cinza": "gray", "gray": "gray", "grey": "gray"}
VOCABULARY = {name: {"kind": "math"} for name in (
    "inferiores_brancas", "primeira_branca", "pares_ordenados", "favoraveis_distintos",
    "segunda_branca", "contagem_1", "contagem_2", "condicional_1", "condicional_2",
    "total", "arvore_total", *(f"ramo_{i}" for i in range(1, 7)))}
VOCABULARY.update({name: {"kind": "integer_set"} for name in ("repeticao_branca", "continuar")})
VOCABULARY.update({name: {"kind": "enum", "values": COLORS} for name in ("estrategia_1", "estrategia_2")})


def extract_p3_quantities(problem_id, source):
    return extract_named_math(problem_id, source, VOCABULARY)


def collect_tme2_p3_digital(items):
    return collect_digital_items(PROBLEM_ID, items, item_ids="abc",
        literal_extractors=(extract_digital_literals, extract_p3_quantities))
