# Relatório Técnico — Benchmark Nível 1 da Suíte ITA 2025 F2

## Objetivo

Este relatório registra o estado estabilizado do benchmark de Nível 1 da suíte ITA 2025 — 2ª fase no ConfIA Auditor.

O Nível 1 avalia o pipeline:

- entrada da solução;
- carregamento dos assets da questão;
- extração de claims matemáticos;
- mapeamento para formal_steps associados à camada Lean.

Nesta etapa, o objetivo não é verificar diretamente a solução textual completa, mas validar se o sistema identifica corretamente os elementos matemáticos relevantes presentes na solução.

## Escopo

Foram avaliadas 500 soluções sintéticas controladas, distribuídas em 5 questões:

- ITA2025F2Q1
- ITA2025F2Q3
- ITA2025F2Q5
- ITA2025F2Q6
- ITA2025F2Q8

Cada questão possui 100 soluções nas categorias A, B, C, D, E e F: correta, erro de conta, erro de conceito, parcial, formato difícil e adversarial.

## Resultado por questão

| Questão | Claim Precision | Claim Recall | Claim F1 | Formal Step Precision | Formal Step Recall | Formal Step F1 | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| ITA2025F2Q1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | Fechada |
| ITA2025F2Q3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | Fechada |
| ITA2025F2Q5 | 1.000 | 0.929 | 0.963 | 1.000 | 0.946 | 0.972 | Forte, residual |
| ITA2025F2Q6 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | Fechada |
| ITA2025F2Q8 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | Fechada |

## Interpretação técnica

Quatro das cinco questões atingiram correspondência perfeita entre o gold sintético e a extração do sistema: F2Q1, F2Q3, F2Q6 e F2Q8.

A F2Q5 permaneceu com divergências residuais de recall, mas sem falsos positivos:

- claim_fp = 0
- formal_step_fp = 0

Isso indica comportamento conservador: o agente deixa de reconhecer alguns elementos esperados em certos textos, mas não inventa claims matemáticos inexistentes.

## Papel da camada Lean

Neste benchmark, a camada Lean não verifica diretamente a solução textual completa.

A função da camada Lean é verificar proposições formais associadas aos claims extraídos. A arquitetura correta é:

- LLM/extractor/rules: identifica claims e evidências textuais;
- Python/FastAPI: organiza pipeline, rubricas, benchmark e relatórios;
- Lean 4/Mathlib: verifica proposições formais associadas aos claims.

## Veredito

O benchmark de Nível 1 da suíte ITA 2025 F2 está estabilizado.

O sistema atingiu desempenho perfeito em 4 de 5 questões e desempenho conservador forte na questão restante.

Este estado pode ser usado como baseline técnico para apresentação, comparação futura e avanço para validação de Nível 2.

## Próximas etapas

1. Congelar este resultado como baseline.
2. Tratar F2Q5 em branch ou commit separado.
3. Rodar benchmark de Nível 2 com foco em score, rubrica e verificação Lean.
4. Gerar relatório institucional com gráficos e resumo executivo.
5. Comparar resultados em dados sintéticos, LLM-generated e humanos.
