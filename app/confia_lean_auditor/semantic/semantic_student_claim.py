"""Closed August payload contracts. No model-controlled points or Lean code."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal
from pydantic import Field
from .evidence_unit import EvidenceUnit

PROBLEMS = ("ITA2025F2Q1", "ITA2025F2Q5", "ITA2025F2Q6")


def integer():
    return {"type": "integer"}


def enum(*values):
    return {"type": "string", "enum": list(values)}


def contract(description, **fields):
    return {"description": description, "payload_schema": {
        "type": "object", "additionalProperties": False,
        "properties": fields, "required": list(fields)}}


CONTRACTS = {
    "f2q1_student_final_answer": contract("Valores finais de a e b escritos pelo aluno.", a=integer(), b=integer()),
    "f2q1_student_power_reduction": contract("Resto const + coeff*x de x^exponent módulo x²-x+1; apenas expoentes 57,14,7.", exponent={"type": "integer", "enum": [57, 14, 7]}, const=integer(), coeff=integer()),
    "f2q1_student_reduced_form": contract("Forma do resto: correct=(a+b)x-a; wrong_const_sign=(a+b)x+a; wrong_coeff_minus=(a-b)x-a; wrong_coeff_swapped_minus=(b-a)x-a. Rótulos históricos, sem julgamento.", form_kind=enum("correct", "wrong_const_sign", "wrong_coeff_minus", "wrong_coeff_swapped_minus")),
    "f2q1_student_coefficient_system": contract("Sistema escrito. candidateA representa a; candidateB representa b; neg_a representa -a. Não gerar expressão livre.", sum_lhs=enum("candidateA + candidateB", "candidateB + candidateA"), sum_rhs=integer(), a_equation_kind=enum("a", "neg_a"), a_rhs=integer()),
    "f2q5_student_log_power_decomposition": contract("Decomposição do log de 3^100; todos os valores multiplicados por 10000, inclusive parte inteira. Extrair apenas decomposição presente, sem completar passos.", total_log_scaled=integer(), integer_part_scaled=integer(), mantissa_scaled=integer()),
    "f2q5_student_mantissa": contract("Parte fracionária indicada pelo aluno, multiplicada por 10000.", mantissa_scaled=integer()),
    "f2q5_student_digit_log_bounds": contract("Valores atribuídos a log10(5) e log10(6), multiplicados por 10000.", log5_scaled=integer(), log6_scaled=integer()),
    "f2q5_student_between_bounds": contract("Cadeia estrita left < middle < right escrita pelo aluno; valores multiplicados por 10000.", left_scaled=integer(), middle_scaled=integer(), right_scaled=integer()),
    "f2q5_student_final_digit": contract("Primeiro algarismo de 3^100 indicado pelo aluno.", digit=integer()),
    "f2q6_student_probability_formula": contract("Forma textual: correct=C(n-1,3)/2^n; wrong_choose_n_3=C(n,3)/2^n; correct_numerator_wrong_denominator_n_minus_1=C(n-1,3)/2^(n-1). Identificar forma, não julgar correção.", formula_kind=enum("correct", "wrong_choose_n_3", "correct_numerator_wrong_denominator_n_minus_1")),
    "f2q6_student_ratio_formula": contract("Razão P(n+1)/P(n): correct=n/(2n-6); wrong_n_minus_1_over_2n=(n-1)/(2n); wrong_n_minus_1_over_2n_minus_6=(n-1)/(2n-6); wrong_n_over_2n=n/(2n); wrong_n_over_2n_minus_8=n/(2n-8). Identificar forma textual.", ratio_kind=enum("correct", "wrong_n_minus_1_over_2n", "wrong_n_minus_1_over_2n_minus_6", "wrong_n_over_2n", "wrong_n_over_2n_minus_8")),
    "f2q6_student_final_answer": contract("Lista dos valores de n apresentados como resposta; preservar valores errados, sem completar a lista.", values={"type": "array", "items": integer()}),
}


def allowed_contracts(problem_id):
    if problem_id not in PROBLEMS:
        raise ValueError("Unsupported problem_id")
    prefix = problem_id.replace("ITA2025", "").lower() + "_student_"
    return {k: deepcopy(v) for k, v in CONTRACTS.items() if k.startswith(prefix)}


def validate_payload(claim_type, payload, problem_id):
    contracts = allowed_contracts(problem_id)
    if claim_type not in contracts:
        raise ValueError("claim_type outside closed problem contract")
    props = contracts[claim_type]["payload_schema"]["properties"]
    if not isinstance(payload, dict) or set(payload) != set(props):
        raise ValueError("Payload fields do not match historical checker contract")
    for key, spec in props.items():
        value = payload[key]
        valid = ((spec["type"] == "integer" and type(value) is int)
                 or (spec["type"] == "string" and type(value) is str)
                 or (spec["type"] == "array" and type(value) is list
                     and all(type(v) is int for v in value)))
        if not valid or ("enum" in spec and value not in spec["enum"]):
            raise ValueError("Invalid payload field: " + key)
    return deepcopy(payload)


class SemanticStudentClaim(EvidenceUnit):
    """Strict LLM boundary. Downstream consumers receive plain EvidenceUnit."""
    source_span: str = Field(min_length=1)
    context_policy: Literal["explicit_semantic_context"] = "explicit_semantic_context"
    extractor_mode: Literal["SEMANTIC_FORMAL"] = "SEMANTIC_FORMAL"
    extractor_model: str


LLM_FIELDS = ("source_span", "claim_type", "normalized_payload", "assertion_status",
              "polarity", "scope", "hypothetical", "abandoned")


def extraction_schema(problem_id):
    common = SemanticStudentClaim.model_json_schema()["properties"]
    variants = []
    for kind, spec in allowed_contracts(problem_id).items():
        props = {k: deepcopy(common[k]) for k in LLM_FIELDS}
        props["claim_type"] = enum(kind)
        props["normalized_payload"] = spec["payload_schema"]
        variants.append({"type": "object", "additionalProperties": False,
                         "properties": props, "required": list(LLM_FIELDS)})
    return {"type": "object", "additionalProperties": False,
            "properties": {"claims": {"type": "array", "items": {"anyOf": variants}}},
            "required": ["claims"]}
