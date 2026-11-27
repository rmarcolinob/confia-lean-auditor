"""P4 opt-in typed assertions; no interpretation of unsupported prose."""
from .digital_items import collect_digital_items
from .named_math import extract_named_math

PROBLEM_ID = "TME2026P4"
VOCABULARY = {name: {"kind": "math"} for name in (
    "pb", "bq", "pq", "qc", "qr", "rc", "ap", "ar", "ra",
    "perimeter_pbq", "perimeter_rqc", "shaded_sum", "perimeter_apqr",
    "h", "c", "case_3x_root", "case_other_root")}
VOCABULARY.update({name: {"kind": "relation"} for name in (
    "exclude_12", "h_plus_c", "pythagoras", "case_3x", "case_other")})
VOCABULARY.update({name: {"kind": "enum", "values": {
    "equilateral": "equilateral", "equilatero": "equilateral",
    "scalene": "scalene", "escaleno": "scalene"}}
    for name in ("triangle_pbq", "triangle_rqc")})
VOCABULARY["apqr"] = {"kind": "enum", "values": {
    "parallelogram": "parallelogram", "paralelogramo": "parallelogram", "trapezoid": "trapezoid"}}
VOCABULARY["x_candidates"] = {"kind": "expression_set"}
VOCABULARY["shaded_lengths"] = {"kind": "set_equality"}


def extract_p4_quantities(problem_id, source):
    return extract_named_math(problem_id, source, VOCABULARY)


def collect_tme2_p4_digital(items):
    return collect_digital_items(PROBLEM_ID, items, item_ids="abc", literal_extractors=(extract_p4_quantities,))
