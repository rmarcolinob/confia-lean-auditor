from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


OUT = Path(__file__).resolve().parent / "gold_500.csv"


DIST = {
    "A": 30,
    "B": 24,
    "C": 12,
    "D": 16,
    "E": 10,
    "F": 8,
}


ROWS: List[Dict[str, str]] = []


def join(items: List[str]) -> str:
    return "|".join(items)


def add(
    problem_id: str,
    case_id: str,
    category: str,
    solution: str,
    expected_claims: List[str],
    expected_formal_steps: List[str],
    expected_score_min: float,
    expected_score_max: float,
    notes: str = "",
) -> None:
    ROWS.append(
        {
            "id": case_id,
            "problem_id": problem_id,
            "category": category,
            "solution": solution,
            "expected_claims": join(expected_claims),
            "expected_formal_steps": join(expected_formal_steps),
            "expected_score_min": str(expected_score_min),
            "expected_score_max": str(expected_score_max),
            "notes": notes,
        }
    )


def repeat(problem_id: str, category: str, templates: List[Dict[str, object]]) -> None:
    total = DIST[category]
    for i in range(total):
        t = templates[i % len(templates)]
        add(
            problem_id=problem_id,
            case_id=f"{problem_id.replace('ITA2025', '')}-{category}{i+1:02d}",
            category=category,
            solution=str(t["solution"]),
            expected_claims=list(t.get("claims", [])),
            expected_formal_steps=list(t.get("steps", [])),
            expected_score_min=float(t.get("score_min", 0)),
            expected_score_max=float(t.get("score_max", 10)),
            notes=str(t.get("notes", "")),
        )


# ---------------------------------------------------------------------
# F2Q1
# ---------------------------------------------------------------------

F2Q1_FULL_CLAIMS = [
    "power_reductions",
    "reduced_polynomial_form",
    "coefficient_system",
    "final_answer",
]
F2Q1_FULL_STEPS = [
    "f2q1_power_reductions",
    "f2q1_reduced_form",
    "f2q1_coefficient_solution",
]

repeat(
    "ITA2025F2Q1",
    "A",
    [
        {
            "solution": "No resto módulo x^2-x+1, temos x^2=x-1 e daí x^3=-1. Assim x^57=-1, x^14=x-1 e x^7=x. O resto fica -1+a(x-1)+bx+1=(a+b)x-a. Comparando com 2x+1: -a=1 e a+b=2. Logo a=-1 e b=3.",
            "claims": F2Q1_FULL_CLAIMS,
            "steps": F2Q1_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
        {
            "solution": "Usando x^2≡x−1 mod x^2−x+1, segue x^3≡−1. Portanto x^57≡−1, x^14≡x−1 e x^7≡x. Então o resto é (a+b)x−a. Igualando a 2x+1, temos -a=1 e a+b=2. Logo a=-1 e b=3.",
            "claims": F2Q1_FULL_CLAIMS,
            "steps": F2Q1_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
    ],
)

repeat(
    "ITA2025F2Q1",
    "B",
    [
        {
            "solution": "Vou usar x^3=1 no quociente. Então x^57=1, x^14=x^2=x-1 e x^7=x. O resto fica 1+a(x-1)+bx+1. Igualando com 2x+1, chego em a=1 e b=1.",
            "claims": ["power_reductions", "reduced_polynomial_form", "coefficient_system", "final_answer"],
            "steps": F2Q1_FULL_STEPS,
            "score_min": 0,
            "score_max": 4,
            "notes": "erro clássico: usa x^3=1 em vez de x^3=-1",
        },
        {
            "solution": "Reduzi as potências e achei que x^14=1-x. Assim o resto ficou (b-a)x+a. Comparando com 2x+1, concluí a=1 e b=3.",
            "claims": ["power_reductions", "reduced_polynomial_form", "coefficient_system", "final_answer"],
            "steps": F2Q1_FULL_STEPS,
            "score_min": 0,
            "score_max": 5,
        },
    ],
)

repeat(
    "ITA2025F2Q1",
    "C",
    [
        {
            "solution": "Como x^2=x-1, substituo isso como se valesse para todo número real. Depois escolho x=1 e concluo que a e b podem ser quaisquer reais.",
            "claims": ["power_reductions"],
            "steps": ["f2q1_power_reductions"],
            "score_min": 0,
            "score_max": 3,
            "notes": "erro conceitual: trata congruência modular como identidade real global",
        },
        {
            "solution": "O divisor tem grau 2, então o resto sempre é 2x+1 independentemente de a e b. Logo qualquer par serve.",
            "claims": [],
            "steps": [],
            "score_min": 0,
            "score_max": 2,
        },
    ],
)

repeat(
    "ITA2025F2Q1",
    "D",
    [
        {
            "solution": "Consegui reduzir x^57=-1, x^14=x-1 e x^7=x, mas não deu tempo de montar o sistema.",
            "claims": ["power_reductions"],
            "steps": ["f2q1_power_reductions"],
            "score_min": 3,
            "score_max": 5,
        },
        {
            "solution": "O resto fica (a+b)x-a. Falta só comparar com 2x+1.",
            "claims": ["reduced_polynomial_form"],
            "steps": ["f2q1_reduced_form"],
            "score_min": 3,
            "score_max": 6,
        },
    ],
)

repeat(
    "ITA2025F2Q1",
    "E",
    [
        {
            "solution": "x2=x-1;x3=-1;x57=-1;x14=x-1;x7=x;resto=(a+b)x-a=2x+1=>a=-1,b=3",
            "claims": F2Q1_FULL_CLAIMS,
            "steps": F2Q1_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
        {
            "solution": r"\mod (x^2-x+1): x^3=-1, x^{57}=-1, x^{14}=x-1, x^7=x. R=(a+b)x-a. Portanto a=-1 e b=3.",
            "claims": F2Q1_FULL_CLAIMS,
            "steps": F2Q1_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
    ],
)

repeat(
    "ITA2025F2Q1",
    "F",
    [
        {
            "solution": "a=-1 b=3 resto potência x matemática.",
            "claims": [],
            "steps": [],
            "score_min": 0,
            "score_max": 2,
        },
        {
            "solution": "Não sei resolver, mas acho que é a=-1 e b=3.",
            "claims": ["final_answer"],
            "steps": [],
            "score_min": 0,
            "score_max": 2,
        },
    ],
)


# ---------------------------------------------------------------------
# F2Q3
# ---------------------------------------------------------------------

F2Q3_FULL_CLAIMS = [
    "beta_difference",
    "candidate_values",
    "final_sin_sum",
    "final_answer",
]
F2Q3_FULL_STEPS = [
    "f2q3_beta_difference",
    "f2q3_equations",
    "f2q3_unit_circle",
    "f2q3_final_sin_sum",
    "f2q3_final_answer",
]

repeat(
    "ITA2025F2Q3",
    "A",
    [
        {
            "solution": "Das equações, subtraindo a primeira da segunda, obtenho cosβ−senβ=1/2. Com β no intervalo, escolho senβ=−(sqrt(7)+1)/4 e cosβ=(1−sqrt(7))/4. Então senα=−sqrt(7)/4 e cosα=−3/4. Logo sen(α+β)=senα cosβ+cosα senβ=(5+sqrt(7))/8.",
            "claims": F2Q3_FULL_CLAIMS,
            "steps": F2Q3_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
        {
            "solution": "Temos cos beta - sen beta = 1/2. Resolvendo com sen² beta + cos² beta = 1 e usando o sinal do intervalo, vem sen beta = -(sqrt(7)+1)/4 e cos beta = (1-sqrt(7))/4. Da primeira equação sen alpha = -sqrt(7)/4 e então cos alpha = -3/4. Portanto sen(alpha+beta)=(5+sqrt(7))/8.",
            "claims": F2Q3_FULL_CLAIMS,
            "steps": F2Q3_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
    ],
)

repeat(
    "ITA2025F2Q3",
    "B",
    [
        {
            "solution": "Achei cosβ−senβ=-1/2. Então usei senβ=(sqrt(7)+1)/4, cosβ=(sqrt(7)-1)/4, senα=sqrt(7)/4 e cosα=3/4. Assim sen(α+β)=1/2.",
            "claims": F2Q3_FULL_CLAIMS,
            "steps": F2Q3_FULL_STEPS,
            "score_min": 0,
            "score_max": 4,
        },
        {
            "solution": "A conta dá cos beta - sen beta = 1/2, mas escolhi os sinais positivos. Usei sen beta=(sqrt(7)+1)/4 e cos beta=(sqrt(7)-1)/4. No fim obtive sen(alpha+beta)=1/2.",
            "claims": ["beta_difference", "candidate_values", "final_sin_sum", "final_answer"],
            "steps": F2Q3_FULL_STEPS,
            "score_min": 0,
            "score_max": 5,
        },
    ],
)

repeat(
    "ITA2025F2Q3",
    "C",
    [
        {
            "solution": "Como alpha e beta estão entre pi/2 e 3pi/2, assumi que todos os senos e cossenos são negativos. Daí tomei sen alpha = sen beta = -1 e concluí que sen(alpha+beta)=0.",
            "claims": [],
            "steps": [],
            "score_min": 0,
            "score_max": 3,
        },
        {
            "solution": "Usei sen(alpha+beta)=sen alpha + sen beta, sem o termo dos cossenos. Assim a resposta fica -sqrt(7)/4-(sqrt(7)+1)/4.",
            "claims": ["candidate_values"],
            "steps": ["f2q3_equations"],
            "score_min": 0,
            "score_max": 4,
        },
    ],
)

repeat(
    "ITA2025F2Q3",
    "D",
    [
        {
            "solution": "Subtraindo as equações, obtenho cosβ−senβ=1/2. Parei aqui.",
            "claims": ["beta_difference"],
            "steps": ["f2q3_beta_difference"],
            "score_min": 2,
            "score_max": 4,
        },
        {
            "solution": "Encontrei sen beta = -(sqrt(7)+1)/4 e cos beta = (1-sqrt(7))/4, mas não terminei sen(alpha+beta).",
            "claims": ["candidate_values"],
            "steps": ["f2q3_equations", "f2q3_unit_circle"],
            "score_min": 3,
            "score_max": 6,
        },
    ],
)

repeat(
    "ITA2025F2Q3",
    "E",
    [
        {
            "solution": "cosβ-senβ=1/2; senβ=-(√7+1)/4; cosβ=(1-√7)/4; senα=-√7/4; cosα=-3/4; sen(α+β)=(5+√7)/8.",
            "claims": F2Q3_FULL_CLAIMS,
            "steps": F2Q3_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
        {
            "solution": r"\cos\beta-\sin\beta=1/2,\ \sin\beta=-(\sqrt7+1)/4,\ \cos\beta=(1-\sqrt7)/4,\ \sin(\alpha+\beta)=(5+\sqrt7)/8.",
            "claims": F2Q3_FULL_CLAIMS,
            "steps": F2Q3_FULL_STEPS,
            "score_min": 8,
            "score_max": 10,
        },
    ],
)

repeat(
    "ITA2025F2Q3",
    "F",
    [
        {
            "solution": "sqrt(7) seno cosseno beta alpha resposta.",
            "claims": [],
            "steps": [],
            "score_min": 0,
            "score_max": 2,
        },
        {
            "solution": "Resposta final: (5+sqrt(7))/8, sem fazer as contas.",
            "claims": ["final_answer"],
            "steps": ["f2q3_final_answer"],
            "score_min": 0,
            "score_max": 3,
        },
    ],
)


# ---------------------------------------------------------------------
# F2Q5
# ---------------------------------------------------------------------

F2Q5_FULL_CLAIMS = [
    "log_power_decomposition",
    "mantissa_identification",
    "digit_log_bounds",
    "mantissa_between_bounds",
    "final_digit_five",
]
F2Q5_FULL_STEPS = [
    "f2q5_log_power_decomposition",
    "f2q5_digit_bounds",
]

repeat(
    "ITA2025F2Q5",
    "A",
    [
        {
            "solution": "Temos log(3^100)=100 log 3=47,71. A mantissa é 0,71 = 71/100. Como log 5 = 1-log2 = 0,6990 e log 6 = log2+log3 = 0,7781, temos 0,6990 < 0,71 < 0,7781. Logo o primeiro algarismo de 3^100 é 5.",
            "claims": F2Q5_FULL_CLAIMS,
            "steps": F2Q5_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
        {
            "solution": "Calculando, 100·0,4771=47,71. Então só importa a parte decimal 0,71. Ela está entre log10 5=0,6990 e log10 6=0,7781. Portanto o dígito inicial é 5.",
            "claims": F2Q5_FULL_CLAIMS,
            "steps": F2Q5_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
    ],
)

repeat(
    "ITA2025F2Q5",
    "B",
    [
        {
            "solution": "100 log3 = 47,71. Mas calculei log6 = 0,7081. Como 0,71 fica acima disso, concluí que o primeiro algarismo é 6.",
            "claims": F2Q5_FULL_CLAIMS,
            "steps": F2Q5_FULL_STEPS,
            "score_min": 0,
            "score_max": 5,
        },
        {
            "solution": "A mantissa é 0,71, mas comparei com log4 e log5 e achei que o primeiro dígito era 4.",
            "claims": ["mantissa_identification", "digit_log_bounds", "mantissa_between_bounds", "final_digit"],
            "steps": ["f2q5_digit_bounds"],
            "score_min": 0,
            "score_max": 5,
        },
    ],
)

repeat(
    "ITA2025F2Q5",
    "C",
    [
        {
            "solution": "Como 100 log3 = 47,71, achei que o primeiro algarismo é o 7, pois aparece depois da vírgula.",
            "claims": ["log_power_decomposition", "mantissa_identification", "final_digit"],
            "steps": ["f2q5_log_power_decomposition"],
            "score_min": 0,
            "score_max": 4,
        },
        {
            "solution": "Usei a parte inteira 47 para decidir o primeiro algarismo e concluí que seria 4.",
            "claims": ["log_power_decomposition", "final_digit"],
            "steps": ["f2q5_log_power_decomposition"],
            "score_min": 0,
            "score_max": 3,
        },
    ],
)

repeat(
    "ITA2025F2Q5",
    "D",
    [
        {
            "solution": "Calculei 100 log3 = 47,71, então a mantissa é 0,71. Não terminei a comparação.",
            "claims": ["log_power_decomposition", "mantissa_identification"],
            "steps": ["f2q5_log_power_decomposition"],
            "score_min": 3,
            "score_max": 6,
        },
        {
            "solution": "Sei que precisa comparar a mantissa com log5 e log6, mas não lembro os valores.",
            "claims": ["digit_log_bounds"],
            "steps": [],
            "score_min": 1,
            "score_max": 4,
        },
    ],
)

repeat(
    "ITA2025F2Q5",
    "E",
    [
        {
            "solution": "100log3=47,71;mantissa=0,71=71/100;log5=0,6990;log6=0,7781;algarismo=5",
            "claims": F2Q5_FULL_CLAIMS,
            "steps": F2Q5_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
        {
            "solution": r"100\log 3=47{,}71,\ m=71/100,\ \log5=0{,}6990<0{,}71<0{,}7781=\log6. Dígito: 5.",
            "claims": F2Q5_FULL_CLAIMS,
            "steps": F2Q5_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
    ],
)

repeat(
    "ITA2025F2Q5",
    "F",
    [
        {
            "solution": "log 0,71 5 6 47,71 primeiro.",
            "claims": [],
            "steps": [],
            "score_min": 0,
            "score_max": 2,
        },
        {
            "solution": "A resposta é 5.",
            "claims": ["final_digit_five"],
            "steps": [],
            "score_min": 0,
            "score_max": 2,
        },
    ],
)


# ---------------------------------------------------------------------
# F2Q6
# ---------------------------------------------------------------------

F2Q6_FULL_CLAIMS = [
    "probability_formula",
    "ratio_comparison",
    "maximizers_identification",
    "final_answer",
]
F2Q6_FULL_STEPS = [
    "f2q6_probability_values",
    "f2q6_ratio_comparison",
]

repeat(
    "ITA2025F2Q6",
    "A",
    [
        {
            "solution": "Para a quarta cara sair no lançamento n, nos n-1 primeiros deve haver exatamente 3 caras e o último deve ser cara. Logo P(N=n)=C(n-1,3)/2^n. A razão P(n+1)/P(n)=n/(2n-6). Ela é maior que 1 antes de 6, igual em n=6 e menor depois. Portanto os máximos ocorrem em n=6 e n=7.",
            "claims": F2Q6_FULL_CLAIMS,
            "steps": F2Q6_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
        {
            "solution": "P(n)=binom(n-1,3)(1/2)^n. Comparando termos consecutivos, P(n+1)/P(n)=n/(2(n-3)). O empate ocorre em n=6, então P(6)=P(7) e esses são os maiores valores.",
            "claims": F2Q6_FULL_CLAIMS,
            "steps": F2Q6_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
    ],
)

repeat(
    "ITA2025F2Q6",
    "B",
    [
        {
            "solution": "Usei P(N=n)=C(n,3)/2^n. A razão fica favorável até n=5 e depois cai, então respondi n=5 e n=6.",
            "claims": F2Q6_FULL_CLAIMS,
            "steps": F2Q6_FULL_STEPS,
            "score_min": 0,
            "score_max": 5,
        },
        {
            "solution": "A fórmula é C(n-1,3)/2^(n-1), pois só olho os primeiros lançamentos. Daí o máximo fica em n=6 apenas.",
            "claims": ["probability_formula", "final_answer"],
            "steps": ["f2q6_probability_values"],
            "score_min": 0,
            "score_max": 5,
        },
    ],
)

repeat(
    "ITA2025F2Q6",
    "C",
    [
        {
            "solution": "Como a moeda é justa, qualquer n tem a mesma chance de ser a quarta cara. Então todos os n maximizam.",
            "claims": [],
            "steps": [],
            "score_min": 0,
            "score_max": 2,
        },
        {
            "solution": "Basta ter quatro caras em n lançamentos, então usei C(n,4)/2^n e procurei o máximo.",
            "claims": ["probability_formula"],
            "steps": [],
            "score_min": 0,
            "score_max": 4,
        },
    ],
)

repeat(
    "ITA2025F2Q6",
    "D",
    [
        {
            "solution": "A probabilidade é P(N=n)=C(n-1,3)/2^n, mas não consegui maximizar.",
            "claims": ["probability_formula"],
            "steps": ["f2q6_probability_values"],
            "score_min": 3,
            "score_max": 5,
        },
        {
            "solution": "A razão entre termos consecutivos é n/(2n-6), mas parei antes de concluir os valores.",
            "claims": ["ratio_comparison"],
            "steps": ["f2q6_ratio_comparison"],
            "score_min": 3,
            "score_max": 6,
        },
    ],
)

repeat(
    "ITA2025F2Q6",
    "E",
    [
        {
            "solution": "P(n)=C(n-1,3)/2^n;P(n+1)/P(n)=n/(2n-6);sobe até 6, empata 6 e 7, cai depois; resposta n=6 e n=7.",
            "claims": F2Q6_FULL_CLAIMS,
            "steps": F2Q6_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
        {
            "solution": r"P(N=n)=\binom{n-1}{3}2^{-n}. Razão = n/(2(n-3)). Máximo: n=6,7.",
            "claims": F2Q6_FULL_CLAIMS,
            "steps": F2Q6_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
    ],
)

repeat(
    "ITA2025F2Q6",
    "F",
    [
        {
            "solution": "moeda cara quarta n 6 7 razão probabilidade.",
            "claims": [],
            "steps": [],
            "score_min": 0,
            "score_max": 2,
        },
        {
            "solution": "Resposta: n=6 e n=7.",
            "claims": ["final_answer"],
            "steps": [],
            "score_min": 0,
            "score_max": 2,
        },
    ],
)


# ---------------------------------------------------------------------
# F2Q8
# ---------------------------------------------------------------------

F2Q8_FULL_CLAIMS = [
    "matrix_transformation",
    "determinant_formula",
    "alternating_sum",
    "final_answer",
]
F2Q8_FULL_STEPS = [
    "f2q8_bridge",
    "f2q8_coldiff_det_one",
    "f2q8_determinant_formula",
    "f2q8_final_sum",
]

repeat(
    "ITA2025F2Q8",
    "A",
    [
        {
            "solution": "Aplicando diferenças sucessivas de colunas em A_k=(max{i,j}), obtemos uma matriz transformada. A matriz de diferenças tem determinante 1, então o determinante é preservado. Da forma obtida segue det(A_k)=(-1)^(k-1)k. Logo a soma é 1-2+3-4+...+2025=1013.",
            "claims": F2Q8_FULL_CLAIMS,
            "steps": F2Q8_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
    ],
)

repeat(
    "ITA2025F2Q8",
    "B",
    [
        {
            "solution": "Faço diferenças de colunas, mas concluo que det(A_k)=(-1)^k k. Assim a soma fica -1+2-3+...-2025=-1013.",
            "claims": ["matrix_transformation"],
            "steps": ["f2q8_bridge", "f2q8_coldiff_det_one"],
            "score_min": 0,
            "score_max": 5,
        },
        {
            "solution": "A transformação por colunas está certa e dá det(A_k)=(-1)^(k-1)k. Só que agrupei os pares e achei 2025-1013=1012.",
            "claims": ["matrix_transformation", "determinant_formula", "alternating_sum"],
            "steps": ["f2q8_bridge", "f2q8_coldiff_det_one", "f2q8_determinant_formula", "f2q8_final_sum"],
            "score_min": 4,
            "score_max": 8,
        },
    ],
)

repeat(
    "ITA2025F2Q8",
    "C",
    [
        {
            "solution": "Como A_k é simétrica, seu determinante deve ser a soma dos elementos da diagonal. Então concluo que o valor é 1013.",
            "claims": ["final_answer"],
            "steps": ["f2q8_final_sum"],
            "score_min": 0,
            "score_max": 3,
        },
        {
            "solution": "Como max(i,j) sempre cresce, o determinante é positivo para todo k. Portanto basta somar k.",
            "claims": [],
            "steps": [],
            "score_min": 0,
            "score_max": 2,
        },
    ],
)

repeat(
    "ITA2025F2Q8",
    "D",
    [
        {
            "solution": "A matriz pode ser simplificada por diferenças sucessivas de colunas.",
            "claims": ["matrix_transformation"],
            "steps": ["f2q8_bridge"],
            "score_min": 2,
            "score_max": 4,
        },
        {
            "solution": "Cheguei na fórmula det(A_k)=(-1)^(k-1)k, mas não consegui terminar a soma.",
            "claims": ["determinant_formula"],
            "steps": ["f2q8_determinant_formula"],
            "score_min": 4,
            "score_max": 6,
        },
    ],
)

repeat(
    "ITA2025F2Q8",
    "E",
    [
        {
            "solution": "Cj<-Cj-Cj-1;det matriz auxiliar=1;det(Ak)=(-1)^(k-1)k;soma=1-2+3-4+...+2025=1013",
            "claims": F2Q8_FULL_CLAIMS,
            "steps": F2Q8_FULL_STEPS,
            "score_min": 9,
            "score_max": 10,
        },
    ],
)

repeat(
    "ITA2025F2Q8",
    "F",
    [
        {
            "solution": "matriz diferença determinante soma 1013 fórmula k coluna.",
            "claims": [],
            "steps": [],
            "score_min": 0,
            "score_max": 2,
        },
        {
            "solution": "Hoje eu comi arroz, feijão e 1013 bananas. Não sei resolver matriz.",
            "claims": [],
            "steps": [],
            "score_min": 0,
            "score_max": 1,
        },
    ],
)



F2Q5_CLAIM_ORDER = [
    "log_power_decomposition",
    "mantissa_identification",
    "digit_log_bounds",
    "mantissa_between_bounds",
    "final_digit_five",
]

F2Q5_STEP_ORDER = [
    "f2q5_log_power_decomposition",
    "f2q5_digit_bounds",
]


def _split_pipe(value: str) -> set[str]:
    value = (value or "").strip()
    if not value:
        return set()
    return {x.strip() for x in value.split("|") if x.strip()}


def _join_ordered(items: set[str], order: list[str]) -> str:
    ordered = [x for x in order if x in items]
    rest = sorted(x for x in items if x not in order)
    return "|".join(ordered + rest)


def _has_correct_f2q5_final_answer(text: str) -> bool:
    t = text.lower()

    correct_patterns = [
        "primeiro algarismo de 3^100 é 5",
        "primeiro algarismo é 5",
        "primeiro digito é 5",
        "primeiro dígito é 5",
        "dígito inicial é 5",
        "digito inicial é 5",
        "algarismo=5",
        "dígito: 5",
        "digito: 5",
        "dígito inicial: 5",
        "digito inicial: 5",
        "resposta é 5",
        "resposta: 5",
    ]

    wrong_patterns = [
        "algarismo é o 7",
        "algarismo é 7",
        "dígito era 4",
        "digito era 4",
        "primeiro dígito era 4",
        "primeiro digito era 4",
        "primeiro algarismo é 6",
        "primeiro algarismo seria 6",
        "concluí que o primeiro algarismo é 6",
        "conclui que o primeiro algarismo é 6",
    ]

    if any(p in t for p in wrong_patterns):
        return False

    return any(p in t for p in correct_patterns)


def normalize_level1_gold_rows() -> None:
    """Corrige inconsistências do gold sintético antes de escrever o CSV.

    Regra central:
    - final_digit é nome antigo e não deve aparecer.
    - final_digit_five só deve aparecer se a solução conclui corretamente algarismo 5.
    - comparações erradas com log4/log5 ou log6=0,7081 não devem acionar
      digit_log_bounds nem mantissa_between_bounds no Nível 1.
    """
    for row in ROWS:
        if row.get("problem_id") != "ITA2025F2Q5":
            continue

        solution = row.get("solution", "")
        t = solution.lower()

        claims = _split_pipe(row.get("expected_claims", ""))
        steps = _split_pipe(row.get("expected_formal_steps", ""))

        # Nome antigo: nunca deve aparecer no gold novo.
        claims.discard("final_digit")

        # Se a conclusão final é 4, 6 ou 7, não é o claim canônico correto.
        if not _has_correct_f2q5_final_answer(solution):
            claims.discard("final_digit_five")

        # Comparações erradas não devem contar como bounds corretos.
        wrong_bounds = (
            "log4" in t
            or "log 4" in t
            or "0,7081" in t
            or "0.7081" in t
            or "comparei com log4" in t
            or "comparei com log 4" in t
        )

        if wrong_bounds:
            claims.discard("digit_log_bounds")
            claims.discard("mantissa_between_bounds")
            steps.discard("f2q5_digit_bounds")

        # Erro conceitual com parte inteira não identifica corretamente mantissa/bounds.
        if "parte inteira" in t:
            claims.discard("mantissa_identification")
            claims.discard("digit_log_bounds")
            claims.discard("mantissa_between_bounds")
            claims.discard("final_digit_five")
            steps.discard("f2q5_digit_bounds")

        row["expected_claims"] = _join_ordered(claims, F2Q5_CLAIM_ORDER)
        row["expected_formal_steps"] = _join_ordered(steps, F2Q5_STEP_ORDER)



F2Q6_CLAIM_ORDER = [
    "probability_formula",
    "ratio_comparison",
    "maximizers_identification",
    "final_answer",
]

F2Q6_STEP_ORDER = [
    "f2q6_probability_values",
    "f2q6_ratio_comparison",
]


def normalize_level1_gold_rows_f2q6() -> None:
    """Corrige inconsistências do gold sintético da F2Q6.

    Regra:
    - C(n,3), C(n,4) e denominador 2^(n-1) não são a fórmula canônica correta.
    - respostas n=5,6 ou apenas n=6 não são a resposta final canônica {6,7}.
    - claims errados do aluno devem ser tratados no Nível 2, não como claims canônicos do Nível 1.
    """
    for row in ROWS:
        if row.get("problem_id") != "ITA2025F2Q6":
            continue

        solution = row.get("solution", "")
        t = solution.lower()
        c = (
            t.replace(" ", "")
            .replace("−", "-")
            .replace("–", "-")
            .replace(",", ".")
        )

        claims = _split_pipe(row.get("expected_claims", ""))
        steps = _split_pipe(row.get("expected_formal_steps", ""))

        wrong_probability_formula = (
            "c(n.3)" in c
            or "c(n,3)" in t.replace(" ", "")
            or "c(n.4)" in c
            or "c(n,4)" in t.replace(" ", "")
            or "2^(n-1)" in c
            or "2^(n−1)" in t.replace(" ", "")
            or "2^(n–1)" in t.replace(" ", "")
            or "c(n-1.3)/2^(n-1)" in c
        )

        wrong_final_answer = (
            "n=5" in c
            or "n=4" in c
            or "n=8" in c
            or "n=6 apenas" in t
            or "em n=6 apenas" in t
            or "maximo fica em n=6 apenas" in t
            or "máximo fica em n=6 apenas" in t
        ) and not ("n=7" in c or "6 e 7" in t or "6,7" in t)

        if wrong_probability_formula:
            claims.discard("probability_formula")
            steps.discard("f2q6_probability_values")

        if wrong_final_answer:
            claims.discard("maximizers_identification")
            claims.discard("final_answer")
            steps.discard("f2q6_ratio_comparison")

        # Se o texto usa fórmula errada e conclui máximo errado, não manter razão canônica.
        if wrong_probability_formula and wrong_final_answer:
            claims.discard("ratio_comparison")
            claims.discard("maximizers_identification")
            claims.discard("final_answer")
            steps.discard("f2q6_ratio_comparison")

        row["expected_claims"] = _join_ordered(claims, F2Q6_CLAIM_ORDER)
        row["expected_formal_steps"] = _join_ordered(steps, F2Q6_STEP_ORDER)



F2Q3_CLAIM_ORDER = [
    "beta_difference",
    "candidate_values",
    "final_sin_sum",
    "final_answer",
]

F2Q3_STEP_ORDER = [
    "f2q3_beta_difference",
    "f2q3_equations",
    "f2q3_unit_circle",
    "f2q3_final_sin_sum",
    "f2q3_final_answer",
]


def _norm_f2q3_text(solution: str) -> tuple[str, str]:
    t = solution.lower()
    t = t.replace("α", "alpha").replace("β", "beta")
    t = t.replace("sen", "sin").replace("seno", "sin")
    t = t.replace("√", "sqrt")
    t = t.replace("−", "-").replace("–", "-")
    t = t.replace(",", ".")
    c = "".join(t.split())
    return t, c


def normalize_level1_gold_rows_f2q3() -> None:
    """Corrige inconsistências do gold sintético da F2Q3.

    Claims canônicos do Nível 1 devem representar passos corretos:
    - beta_difference: cosβ - sinβ = 1/2.
    - candidate_values: sinais/valores corretos de sin/cos de alpha e beta.
    - final_sin_sum/final_answer: valor correto (5+sqrt(7))/8.

    Soluções com ramo errado, sinais errados ou resposta 1/2 não devem
    carregar esses claims como esperados. Esses erros pertencem ao Nível 2.
    """
    for row in ROWS:
        if row.get("problem_id") != "ITA2025F2Q3":
            continue

        solution = row.get("solution", "")
        t, c = _norm_f2q3_text(solution)

        claims = _split_pipe(row.get("expected_claims", ""))
        steps = _split_pipe(row.get("expected_formal_steps", ""))

        wrong_beta_difference = (
            "cosbeta-sinbeta=-1/2" in c
            or "cos(beta)-sin(beta)=-1/2" in c
            or "cosβ-senβ=-1/2" in solution.lower()
        )

        wrong_candidate_values = (
            "sinbeta=(sqrt(7)+1)/4" in c
            or "sinbeta=(sqrt7+1)/4" in c
            or "cosbeta=(sqrt(7)-1)/4" in c
            or "cosbeta=(sqrt7-1)/4" in c
            or "sinalpha=sqrt(7)/4" in c
            or "sinalpha=sqrt7/4" in c
            or "cosalpha=3/4" in c
            or "sinal errado" in t
            or "ramo errado" in t
            or "outro sinal" in t
        )

        wrong_final_answer = (
            "sin(alpha+beta)=1/2" in c
            or "sin(alpha+beta)=-1/2" in c
            or "resposta=1/2" in c
            or "respostae1/2" in c
            or "assim sin(alpha+beta)=1/2" in c
        )

        if wrong_beta_difference:
            claims.discard("beta_difference")
            steps.discard("f2q3_beta_difference")

        if wrong_candidate_values:
            claims.discard("candidate_values")
            steps.discard("f2q3_equations")
            steps.discard("f2q3_unit_circle")

        if wrong_final_answer:
            claims.discard("final_sin_sum")
            claims.discard("final_answer")
            steps.discard("f2q3_final_sin_sum")
            steps.discard("f2q3_final_answer")

        # Categoria B da F2Q3 é erro de conta/sinal; se ainda sobrou claim
        # forte incorreto, removemos de forma conservadora.
        if row.get("category") == "B":
            if wrong_beta_difference or wrong_candidate_values or wrong_final_answer:
                claims.discard("candidate_values")
                claims.discard("final_sin_sum")
                claims.discard("final_answer")
                steps.discard("f2q3_equations")
                steps.discard("f2q3_unit_circle")
                steps.discard("f2q3_final_sin_sum")
                steps.discard("f2q3_final_answer")

        # O claim candidate_values, como definido no extractor, exige os quatro
        # valores candidatos corretos: sin beta, cos beta, sin alpha e cos alpha.
        # Textos que apresentam apenas valores de beta, ou apenas sin alpha/sin beta,
        # não devem esperar candidate_values no Nível 1.
        c_plain = (
            c.replace("\\", "")
             .replace("{", "")
             .replace("}", "")
             .replace("*", "")
        )

        has_sin_beta_correct = (
            "sinbeta=-(sqrt(7)+1)/4" in c_plain
            or "sinbeta=-(sqrt7+1)/4" in c_plain
            or "sinbeta=(-1-sqrt(7))/4" in c_plain
            or "sinbeta=(-1-sqrt7)/4" in c_plain
        )

        has_cos_beta_correct = (
            "cosbeta=(1-sqrt(7))/4" in c_plain
            or "cosbeta=(1-sqrt7)/4" in c_plain
            or "cosbeta=-(sqrt(7)-1)/4" in c_plain
            or "cosbeta=-(sqrt7-1)/4" in c_plain
        )

        has_sin_alpha_correct = (
            "sinalpha=-sqrt(7)/4" in c_plain
            or "sinalpha=-sqrt7/4" in c_plain
            or "sinalpha=-(sqrt(7))/4" in c_plain
            or "sinalpha=-(sqrt7)/4" in c_plain
        )

        has_cos_alpha_correct = (
            "cosalpha=-3/4" in c_plain
        )

        has_full_candidate_values = (
            has_sin_beta_correct
            and has_cos_beta_correct
            and has_sin_alpha_correct
            and has_cos_alpha_correct
        )

        if "candidate_values" in claims and not has_full_candidate_values:
            claims.discard("candidate_values")
            steps.discard("f2q3_equations")
            steps.discard("f2q3_unit_circle")

        row["expected_claims"] = _join_ordered(claims, F2Q3_CLAIM_ORDER)
        row["expected_formal_steps"] = _join_ordered(steps, F2Q3_STEP_ORDER)



F2Q1_CLAIM_ORDER = [
    "power_reductions",
    "reduced_polynomial_form",
    "coefficient_system",
    "final_answer",
]

F2Q1_STEP_ORDER = [
    "f2q1_power_reductions",
    "f2q1_reduced_form",
    "f2q1_coefficient_solution",
]


def _norm_f2q1_text(solution: str) -> tuple[str, str]:
    t = solution.lower()
    t = t.replace("²", "^2").replace("³", "^3")
    t = t.replace("⁶", "^6").replace("⁷", "^7")
    t = t.replace("¹⁴", "^14").replace("⁵⁷", "^57")
    t = t.replace("−", "-").replace("–", "-")
    t = t.replace("≡", "=").replace(",", ".")
    c = "".join(t.split())
    return t, c


def normalize_level1_gold_rows_f2q1() -> None:
    """Corrige inconsistências do gold sintético da F2Q1.

    Claims canônicos:
    - power_reductions exige x^57=-1, x^14=x-1 e x^7=x.
    - reduced_polynomial_form exige resto (a+b)x-a.
    - coefficient_system exige a+b=2 e -a=1.
    - final_answer exige a=-1, b=3 em contexto matemático válido.
    """
    for row in ROWS:
        if row.get("problem_id") != "ITA2025F2Q1":
            continue

        solution = row.get("solution", "")
        t, c = _norm_f2q1_text(solution)

        claims = _split_pipe(row.get("expected_claims", ""))
        steps = _split_pipe(row.get("expected_formal_steps", ""))

        wrong_reductions = (
            "x^3=1" in c
            or "x3=1" in c
            or "x^57=1" in c
            or "x57=1" in c
            or "x^14=1-x" in c
            or "x14=1-x" in c
            or "x^7=-x" in c
            or "x7=-x" in c
        )

        wrong_final = (
            "a=1" in c and "b=1" in c
        ) or (
            "a=3" in c and "b=-1" in c
        )

        if wrong_reductions:
            claims.discard("power_reductions")
            claims.discard("reduced_polynomial_form")
            claims.discard("coefficient_system")
            claims.discard("final_answer")
            steps.discard("f2q1_power_reductions")
            steps.discard("f2q1_reduced_form")
            steps.discard("f2q1_coefficient_solution")

        # Erro conceitual: usar x^2=x-1 como identidade real global não
        # constitui redução correta das potências módulo x^2-x+1.
        if (
            "como x^2=x-1" in t
            and ("todo numero real" in t or "todo número real" in t or "todonumeroreal" in c)
        ):
            claims.discard("power_reductions")
            steps.discard("f2q1_power_reductions")

        # Caso que apresenta apenas o resto reduzido e a resposta final,
        # sem comparação explícita com 2x+1 e sem sistema a+b=2, -a=1.
        # Isso não deve contar como coefficient_system no Nível 1.
        lacks_coefficient_comparison = (
            "coefficient_system" in claims
            and "2x+1" not in c
            and "a+b=2" not in c
            and "b+a=2" not in c
            and "-a=1" not in c
            and "compar" not in t
            and "igualando" not in t
            and "coeficient" not in t
        )

        if lacks_coefficient_comparison:
            claims.discard("coefficient_system")
            steps.discard("f2q1_coefficient_solution")

        if wrong_final:
            claims.discard("coefficient_system")
            claims.discard("final_answer")
            steps.discard("f2q1_coefficient_solution")

        row["expected_claims"] = _join_ordered(claims, F2Q1_CLAIM_ORDER)
        row["expected_formal_steps"] = _join_ordered(steps, F2Q1_STEP_ORDER)


def main() -> None:
    normalize_level1_gold_rows()
    normalize_level1_gold_rows_f2q6()
    normalize_level1_gold_rows_f2q3()
    normalize_level1_gold_rows_f2q1()

    OUT.parent.mkdir(parents=True, exist_ok=True)

    expected_n = 500
    if len(ROWS) != expected_n:
        raise RuntimeError(f"Esperava {expected_n} linhas, mas gerei {len(ROWS)}")

    fieldnames = [
        "id",
        "problem_id",
        "category",
        "solution",
        "expected_claims",
        "expected_formal_steps",
        "expected_score_min",
        "expected_score_max",
        "notes",
    ]

    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ROWS)

    print(f"Wrote {len(ROWS)} rows to {OUT}")


if __name__ == "__main__":
    main()
