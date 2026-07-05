from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from confia_lean_auditor.core.schemas import FormalStep


SEMANTIC_EXTRACTION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "q1_data": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "determinant_computation": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "present": {"type": "boolean"},
                        "method": {"type": "string"},
                        "evidence": {"type": "string"},
                        "chain": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "final_determinant": {"type": "string"},
                    },
                    "required": [
                        "present",
                        "method",
                        "evidence",
                        "chain",
                        "final_determinant",
                    ],
                }
            },
            "required": ["determinant_computation"],
        }
    },
    "required": ["q1_data"],
}


def llm_enabled() -> bool:
    return os.environ.get("CONFIA_ENABLE_LLM_FORMAL_STEPS") == "1"


def build_q1_semantic_prompt(solution: str) -> str:
    return f"""
Você é um extrator semântico de dados matemáticos para o projeto ConfIA Lean Auditor.

PROBLEMA:
Na questão ITA2025Q1, o aluno calcula a área de um triângulo no plano de Argand-Gauss.
Um dos passos importantes é o cálculo do determinante D.

FUNÇÃO DO LLM:
- Extraia apenas o que está explicitamente escrito na solução.
- Não corrija a solução.
- Não complete passos ausentes.
- Não decida se a solução está correta.
- Não atribua pontuação.
- Não gere código Lean.
- Não transforme uma solução incompleta em completa.

TAREFA:
Preencha q1_data.determinant_computation.

REGRAS:
1. Se a solução contém cálculo explícito do determinante, use present = true.
2. Se não contém cálculo explícito do determinante, use present = false.
3. O campo chain deve conter as igualdades do determinante exatamente como aparecem, ou o mais próximo possível.
4. É permitido usar D no campo chain, pois esta é uma extração semântica.
5. O campo final_determinant deve conter o resultado final que o aluno escreveu para D.
6. Não invente final_determinant se o aluno não escreveu.
7. Se o aluno escreveu uma conta errada, extraia a conta errada exatamente como escrita.
8. Não use essa etapa para corrigir erro do aluno.

EXEMPLO:
Se a solução contém:
D = [2 + 0 + 4a^2] - [2a^2 - 8 + 4a]
D = 4a^2 + 2 - 2a^2 + 8 - 4a
D = 2a^2 - 4a + 10

A saída deve conter:
chain = [
  "D = [2 + 0 + 4a^2] - [2a^2 - 8 + 4a]",
  "D = 4a^2 + 2 - 2a^2 + 8 - 4a",
  "D = 2a^2 - 4a + 10"
]
final_determinant = "2a^2 - 4a + 10"

SOLUÇÃO DO ALUNO:
{solution}
""".strip()


def normalize_algebraic_expr(expr: str) -> str:
    expr = expr.strip()
    expr = expr.strip(".;,")
    expr = expr.replace("$", "")
    expr = expr.replace("²", "^2")
    expr = expr.replace("−", "-")
    expr = expr.replace("·", "*")
    expr = expr.replace("×", "*")
    expr = expr.replace("[", "(").replace("]", ")")

    # Remove nomes semânticos antes da igualdade: D = ..., det = ...
    if "=" in expr:
        expr = expr.split("=")[-1].strip()

    # Remove barras verticais se vierem por engano.
    expr = expr.replace("|", "")

    # Multiplicação implícita simples.
    expr = re.sub(r"(\d+)\s*a", r"\1 * a", expr)
    expr = re.sub(r"(\d+)\s*\(", r"\1 * (", expr)
    expr = re.sub(r"\)\s*a", r") * a", expr)
    expr = re.sub(r"a\s*\(", r"a * (", expr)

    # Espaçamento de operadores.
    for op in ["^", "*", "+", "-", "/", "(", ")"]:
        expr = expr.replace(op, f" {op} ")

    expr = re.sub(r"\s+", " ", expr).strip()

    if expr.startswith("- "):
        expr = "-" + expr[2:]

    return expr


def looks_like_valid_candidate(expr: str) -> bool:
    if not expr:
        return False

    if "=" in expr:
        expr = expr.split("=")[-1]

    # Precisa ter variável a e alguma operação algébrica.
    return "a" in expr and any(op in expr for op in ["+", "-", "^", "*"])


def choose_chain_lhs(chain: List[str]) -> Optional[str]:
    candidates = []

    for line in chain:
        if looks_like_valid_candidate(line):
            candidates.append(line)

    if not candidates:
        return None

    # Preferimos a primeira expressão desenvolvida do determinante.
    return candidates[0]


def choose_chain_rhs(chain: List[str], final_determinant: str) -> Optional[str]:
    if looks_like_valid_candidate(final_determinant):
        return final_determinant

    candidates = [
        line for line in chain
        if looks_like_valid_candidate(line)
    ]

    if not candidates:
        return None

    # Em geral, a última linha é o resultado final do determinante.
    return candidates[-1]


def semantic_to_formal_steps(data: Dict[str, Any]) -> List[FormalStep]:
    det = (
        data.get("q1_data", {})
        .get("determinant_computation", {})
    )

    if not det.get("present", False):
        return []

    chain = det.get("chain", [])
    final_determinant = det.get("final_determinant", "")

    if not isinstance(chain, list):
        return []

    lhs_raw = choose_chain_lhs(chain)
    rhs_raw = choose_chain_rhs(chain, final_determinant)

    if lhs_raw is None or rhs_raw is None:
        return []

    lhs = normalize_algebraic_expr(lhs_raw)
    rhs = normalize_algebraic_expr(rhs_raw)

    if lhs == rhs:
        return []

    evidence = det.get("evidence", "")
    if not evidence:
        evidence = " | ".join(str(x) for x in chain)

    return [
        FormalStep(
            id="q1_llm_s1_determinant_expansion",
            type="determinant_expansion",
            description="Expansão algébrica do determinante extraída semanticamente por LLM.",
            evidence=evidence,
            lhs=lhs,
            rhs=rhs,
            lean_method="ring",
            supports_claim_types=["area_formula"],
            supports_rubric_items=["area_formula"],
        )
    ]


def extract_q1_semantic_data_with_llm(solution: str) -> Dict[str, Any]:
    if not llm_enabled():
        return {}

    try:
        from openai import OpenAI
    except ImportError:
        return {}

    model = os.environ.get("CONFIA_LLM_MODEL", "gpt-4o-mini")
    client = OpenAI()

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "Você é um extrator semântico. "
                    "Você não corrige, não pontua, não completa raciocínios e não gera código Lean. "
                    "Você apenas extrai dados explícitos da solução do aluno em JSON estruturado."
                ),
            },
            {
                "role": "user",
                "content": build_q1_semantic_prompt(solution),
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "confia_q1_semantic_extraction",
                "strict": True,
                "schema": SEMANTIC_EXTRACTION_SCHEMA,
            }
        },
    )

    try:
        return json.loads(response.output_text)
    except Exception:
        return {}


def extract_q1_formal_steps_with_llm(solution: str) -> List[FormalStep]:
    data = extract_q1_semantic_data_with_llm(solution)
    if not data:
        return []

    return semantic_to_formal_steps(data)


def extract_formal_steps_with_llm(problem_id: str, solution: str) -> List[FormalStep]:
    if problem_id == "ITA2025Q1":
        return extract_q1_formal_steps_with_llm(solution)

    return []
