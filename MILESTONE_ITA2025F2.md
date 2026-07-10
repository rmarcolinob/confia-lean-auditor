# ConfIA-auditor — Marco técnico ITA 2025 2ª fase

## Estado atual

O ConfIA-auditor está em estágio de protótipo técnico avançado, com integração entre:

- FastAPI/Python para orquestração do pipeline;
- extratores de claims matemáticos;
- rubricas por problema;
- microclaims rastreáveis;
- formal steps;
- Lean 4/Mathlib como camada de verificação formal;
- testes automatizados de API e verificação Lean.

## Questões integradas

| Questão | Tema | Status |
|---|---|---|
| ITA2025F2Q1 | Polinômios / resto | Lean-backed |
| ITA2025F2Q3 | Trigonometria | Formalização algébrica parcial forte |
| ITA2025F2Q5 | Logaritmos / primeiro algarismo | Lean-backed |
| ITA2025F2Q6 | Probabilidade | Lean-backed |
| ITA2025F2Q8 | Determinantes | Formalização forte em Lean |

## Validação recente

- 20 testes automatizados passaram.
- `lake build` passou com sucesso.
- F2Q3 integrada ao pipeline.
- F2Q8 integrada com formalização forte.
- `Scratch/` ignorado para testes locais.

## Papel do Lean

O Lean não corrige a solução inteira em linguagem natural.

O Lean verifica proposições matemáticas formalizadas, associadas a claims extraídos da solução. A pontuação final resulta da combinação entre:

1. evidência textual;
2. claims extraídos;
3. rubrica;
4. microclaims;
5. formal steps;
6. certificados Lean.

## Exemplo forte: ITA2025F2Q8

Na F2Q8, o sistema formaliza a matriz `A_k = max(i,j)` e prova uma fórmula geral para o determinante:

`det(A_k)=(-1)^(k-1)k`.

A soma final até 2025 é verificada como `1013`.

Status: formalização forte em Lean.

## Exemplo parcial honesto: ITA2025F2Q3

Na F2Q3, Lean verifica:

- os valores candidatos para senos e cossenos;
- as duas equações do enunciado;
- a identidade `sen²+cos²=1`;
- o cálculo final de `sen(α+β)`.

Ainda não está formalizada em Lean a dedução completa dos sinais a partir dos intervalos trigonométricos.

Status: formalização algébrica parcial forte.

## Conclusão

O ConfIA-auditor já funciona como um sistema híbrido de auditoria matemática, com rastreabilidade entre solução textual, claims, rubrica e verificação formal. O próximo avanço é ampliar o número de questões, fortalecer formalizações parciais e melhorar a explicabilidade dos relatórios para professores e avaliadores.
