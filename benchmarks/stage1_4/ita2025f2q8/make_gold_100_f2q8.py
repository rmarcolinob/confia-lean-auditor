from __future__ import annotations

import csv
from pathlib import Path


OUT = Path(__file__).resolve().parent / "gold_100.csv"


FULL_CLAIMS = "matrix_transformation|determinant_formula|alternating_sum|final_answer"
FULL_STEPS = "f2q8_bridge|f2q8_coldiff_det_one|f2q8_determinant_formula|f2q8_final_sum"

MATRIX_CLAIMS = "matrix_transformation"
MATRIX_STEPS = "f2q8_bridge|f2q8_coldiff_det_one"

DET_CLAIMS = "determinant_formula"
DET_STEPS = "f2q8_determinant_formula"

SUM_CLAIMS = "alternating_sum|final_answer"
SUM_STEPS = "f2q8_final_sum"

FINAL_CLAIMS = "final_answer"
FINAL_STEPS = "f2q8_final_sum"


rows = []


def add(row_id: str, category: str, solution: str, claims: str, steps: str) -> None:
    rows.append(
        {
            "id": row_id,
            "problem_id": "ITA2025F2Q8",
            "category": category,
            "solution": solution,
            "expected_claims": claims,
            "expected_formal_steps": steps,
        }
    )


# A — 30 corretas
correct_templates = [
    "Aplicando diferenças sucessivas de colunas em A_k=(max{{i,j}}), obtemos uma matriz transformada. A matriz de diferenças tem determinante 1, então o determinante é preservado. Da forma obtida segue det(A_k)=(-1)^(k-1)k. Logo a soma é 1-2+3-4+...+2025=1013.",
    "Faço C_j <- C_j-C_(j-1), para j>=2. Essa transformação corresponde a multiplicar por uma matriz triangular de determinante 1. Calculando a matriz resultante, vem det(A_k)=(-1)^(k-1)k. Portanto a soma alternada até 2025 vale 1013.",
    "A ideia é subtrair colunas consecutivas. Como a matriz que realiza essa operação tem determinante igual a 1, o determinante de A_k não muda. Depois da transformação, obtém-se det(A_k)=(-1)^(k-1)k. Assim, 1-2+3-4+...+2025=1013.",
    "Mantendo a primeira coluna e trocando cada coluna seguinte pela diferença com a anterior, a matriz fica simples. A operação é feita por uma matriz de determinante 1. O cálculo dá det(A_k)=(-1)^(k-1) k; então a soma dos determinantes é 1013.",
    "Pelas diferenças sucessivas de colunas, reduzo A_k a uma forma triangular por blocos. A matriz auxiliar tem determinante 1, logo det(A_k)=(-1)^(k-1)k. Somando de k=1 até 2025: 1-2+3-4+...+2025=1013.",
    "Uso a transformação C2-C1, C3-C2, etc. Ela preserva o determinante porque equivale a uma matriz triangular com diagonal unitária. Na matriz final aparece a fórmula det(A_k)=(-1)^(k-1)k. A soma pedida é 1013.",
    "Depois das diferenças de colunas, a matriz obtida permite expansão direta. Como a matriz das diferenças tem det igual a 1, resulta det(A_k)=(-1)^(k-1)k. Assim a soma alternada termina em +2025 e vale 1013.",
    "Considero a matriz de diferenças de colunas. Multiplicar A_k por ela transforma a matriz original sem alterar o determinante, pois seu determinante é 1. Daí det(A_k)=(-1)^(k-1)k e a soma final é 1013.",
    "A_k pode ser simplificada por diferenças sucessivas nas colunas. Essa passagem tem determinante auxiliar 1. O determinante geral fica (-1)^(k-1)k. Portanto, a soma 1-2+3-4+...+2025 é igual a 1013.",
    "Subtraindo cada coluna da anterior, a matriz de max(i,j) fica em uma forma cujo determinante é (-1)^(k-1)k. A transformação usada tem determinante 1. Logo a soma dos determinantes até 2025 é 1013.",
]

for i in range(30):
    add(f"F2Q8-A{i+1:02d}", "A", correct_templates[i % len(correct_templates)], FULL_CLAIMS, FULL_STEPS)


# B — 24 erros de conta
wrong_templates = [
    (
        "Faço diferenças de colunas, mas concluo que det(A_k)=(-1)^k k. Assim a soma fica -1+2-3+...-2025=-1013.",
        MATRIX_CLAIMS,
        MATRIX_STEPS,
    ),
    (
        "Uso diferenças sucessivas de colunas. Achei que a matriz de diferenças teria determinante -1, então fiquei com det(A_k)=(-1)^k k e resposta -1013.",
        MATRIX_CLAIMS,
        MATRIX_STEPS,
    ),
    (
        "A matriz parece dar det(A_k)=k para todo k. Então a soma seria 1+2+...+2025.",
        "",
        "",
    ),
    (
        "Depois de transformar as colunas, eu obtenho det(A_k)=(-1)^(k-1)(k+1). Logo a soma alternada fica 1-3+4-5+... e não 1013.",
        MATRIX_CLAIMS,
        MATRIX_STEPS,
    ),
    (
        "Faço C_j-C_(j-1), mas na soma final calculei 1-2+3-4+...+2025 como 1012.",
        "matrix_transformation|determinant_formula|alternating_sum",
        "f2q8_bridge|f2q8_coldiff_det_one|f2q8_determinant_formula|f2q8_final_sum",
    ),
    (
        "A transformação por colunas está certa e dá det(A_k)=(-1)^(k-1)k. Só que agrupei os pares e achei 2025-1013=1012.",
        "matrix_transformation|determinant_formula|alternating_sum",
        "f2q8_bridge|f2q8_coldiff_det_one|f2q8_determinant_formula|f2q8_final_sum",
    ),
]

for i in range(24):
    sol, claims, steps = wrong_templates[i % len(wrong_templates)]
    add(f"F2Q8-B{i+1:02d}", "B", sol, claims, steps)


# C — 12 erros de conceito
concept_templates = [
    (
        "Como A_k é simétrica, seu determinante deve ser a soma dos elementos da diagonal. Então concluo que o valor é 1013.",
        FINAL_CLAIMS,
        FINAL_STEPS,
    ),
    (
        "Como max(i,j) sempre cresce, o determinante é positivo para todo k. Portanto basta somar k e obter a resposta.",
        "",
        "",
    ),
    (
        "A matriz tem linhas parecidas, então o determinante é sempre zero. Logo a soma também seria zero.",
        "",
        "",
    ),
    (
        "Por ser uma matriz com entradas inteiras, assumi que det(A_k)=k^2. Então a soma é a soma dos quadrados.",
        "",
        "",
    ),
    (
        "A matriz é simétrica, logo diagonalizável, então diretamente det(A_k)=(-1)^(k-1)k, sem precisar transformar colunas.",
        DET_CLAIMS,
        DET_STEPS,
    ),
    (
        "Troco linhas por colunas livremente e digo que isso não altera nada. Daí afirmo que o determinante é 1013.",
        FINAL_CLAIMS,
        FINAL_STEPS,
    ),
]

for i in range(12):
    sol, claims, steps = concept_templates[i % len(concept_templates)]
    add(f"F2Q8-C{i+1:02d}", "C", sol, claims, steps)


# D — 16 parciais
partial_templates = [
    (
        "A matriz pode ser simplificada por diferenças sucessivas de colunas.",
        MATRIX_CLAIMS,
        "f2q8_bridge",
    ),
    (
        "A matriz de diferenças de colunas tem determinante 1, então essa operação preserva o determinante.",
        MATRIX_CLAIMS,
        MATRIX_STEPS,
    ),
    (
        "Cheguei na fórmula det(A_k)=(-1)^(k-1)k, mas não consegui terminar a soma.",
        DET_CLAIMS,
        DET_STEPS,
    ),
    (
        "A soma fica 1-2+3-4+...+2025.",
        "alternating_sum",
        "f2q8_final_sum",
    ),
    (
        "A resposta final é 1013.",
        FINAL_CLAIMS,
        FINAL_STEPS,
    ),
    (
        "Depois da transformação, parece que o determinante alterna sinal e tem módulo k.",
        DET_CLAIMS,
        DET_STEPS,
    ),
    (
        "Não deu tempo de escrever tudo: usei diferenças de colunas e depois somei uma sequência alternada até 2025.",
        "matrix_transformation|alternating_sum",
        "f2q8_bridge|f2q8_coldiff_det_one|f2q8_final_sum",
    ),
    (
        "Se det(A_k)=(-1)^(k-1)k, então o final sai 1013.",
        "determinant_formula|final_answer",
        "f2q8_determinant_formula|f2q8_final_sum",
    ),
]

for i in range(16):
    sol, claims, steps = partial_templates[i % len(partial_templates)]
    add(f"F2Q8-D{i+1:02d}", "D", sol, claims, steps)


# E — 10 formatos difíceis
format_templates = [
    (
        "Cj<-Cj-Cj-1;det matriz auxiliar=1;det(Ak)=(-1)^(k-1)k;soma=1-2+3-4+...+2025=1013",
        FULL_CLAIMS,
        FULL_STEPS,
    ),
    (
        "Faço coluna j menos coluna j menos um. A auxiliar tem determinante um. O determinante de A índice k é menos um elevado a k menos um vezes k. A soma dá mil e treze.",
        FULL_CLAIMS,
        FULL_STEPS,
    ),
    (
        "C_j\\leftarrow C_j-C_{j-1}. \\det(B)=1. \\det(A_k)=(-1)^{k-1}k. \\sum_{k=1}^{2025}\\det(A_k)=1013.",
        FULL_CLAIMS,
        FULL_STEPS,
    ),
    (
        "diferenças   de   colunas     det=1      det(A_k)=(-1)^(k-1)k       1-2+3-4+...+2025=1013",
        FULL_CLAIMS,
        FULL_STEPS,
    ),
    (
        "Primeiro pensei que era -1013, mas corrigi: com det(A_k)=(-1)^(k-1)k, a soma alternada termina em +2025 e vale 1013.",
        "determinant_formula|alternating_sum|final_answer",
        "f2q8_determinant_formula|f2q8_final_sum",
    ),
]

for i in range(10):
    sol, claims, steps = format_templates[i % len(format_templates)]
    add(f"F2Q8-E{i+1:02d}", "E", sol, claims, steps)


# F — 8 adversariais
adv_templates = [
    (
        "Hoje eu comi arroz, feijão e 1013 bananas. Não sei resolver matriz.",
        "",
        "",
    ),
    (
        "Resposta: 1013. Confia.",
        FINAL_CLAIMS,
        FINAL_STEPS,
    ),
    (
        "det(A_k)=(-1)^(k-1)k. 1013. Sem demonstração.",
        "determinant_formula|final_answer",
        "f2q8_determinant_formula|f2q8_final_sum",
    ),
    (
        "O Flamengo ganhou de 1-2+3-4+2025 e o placar final foi 1013.",
        "",
        "",
    ),
    (
        "Não sei.",
        "",
        "",
    ),
    (
        "?",
        "",
        "",
    ),
    (
        "Para funções f e g, tomo x1=1/8 e x2=3/8, logo g não é injetora.",
        "",
        "",
    ),
    (
        "matriz diferença determinante soma 1013 fórmula k coluna.",
        "",
        "",
    ),
]

for i in range(8):
    sol, claims, steps = adv_templates[i]
    add(f"F2Q8-F{i+1:02d}", "F", sol, claims, steps)


assert len(rows) == 100, len(rows)

with OUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "id",
            "problem_id",
            "category",
            "solution",
            "expected_claims",
            "expected_formal_steps",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {OUT}")
