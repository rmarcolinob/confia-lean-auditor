# TME P3 — Regressão observada da arquitetura unificada 01

**OBSERVED REGRESSION ONLY — READY_FOR_P3_SAFETY_03.** Nenhum novo falso crédito material, nenhum award de guard e nenhum hard veto fora da política central foi encontrado nos 79 replays disponíveis. Os dois falsos créditos conhecidos de Safety 02 e os quatro falsos positivos conhecidos dos guards desapareceram. Há perdas de representação e lacunas de rotulagem discursiva remanescentes, detalhadas abaixo. Esta execução **não** revalida segurança de forma independente.

## Congelamento, execução e denominadores

SHA confirmado antes e depois: `a6ab3d2c173ee801e1bc5a27d155215c054e007d`. Worktree inicialmente limpo. Os 399 arquivos protegidos inventariados, as fixtures/expectations e as gravações utilizadas permaneceram iguais. Nenhum código, prompt, pauta, peso, checker, política ou fixture foi alterado. Sem commit e sem Safety 03.

Modo: **RECORDED_REPLAY**, `use_lean=True`. Zero chamadas e zero tentativas bloqueadas de API; nenhum retry do extractor. As expectativas foram lidas apenas na análise, separadamente da execução. Respostas gravadas foram vinculadas de novo à fonte e submetidas à implementação congelada. Lean realmente executou quando exigido: 14 tentativas formais, 13 FORMAL_VERIFIED e 1 FORMAL_REFUTED; sem technical uncertainty.

Seleção definida antes da execução:

- Robustness: 48 gravações mais recentes em `tme_p3_semantic_safety_02/observed_regression/tme_semantic_formal`, anteriores à unificação. Essa rodada contém as perdas A08/E08 solicitadas para auditoria. São as mesmas 48 fontes, conferidas por hash.
- Safety: 32 artefatos originais em `tme_p3_semantic_safety_02/new32/tme_semantic_formal`; 31 possuem raw_output completo. S2_05 não possui e ficou REPLAY_UNAVAILABLE.
- Scores da primeira execução de robustness também permanecem visíveis em coluna separada. Não são misturados à comparação causal, porque suas interpretações diferem em alguns casos.

Logo, **48/48 robustness + 31/32 safety = 79/80 replays**. Não se atribuiu zero, acerto ou erro do extractor ao caso indisponível. A execução foi sequencial, sem competição por artefatos Lean.

Execução: 2026-11-06T17:30:21.064690-03:00 a 2026-11-06T17:32:40.135475-03:00 (America/Fortaleza).

### Hashes de congelamento

SHA-256 dos bytes; todos conferidos com os manifests históricos antes da execução e novamente ao final:

| Conjunto | Arquivo | SHA-256 |
| --- | --- | --- |
| semantic_robustness_01 | sources.json | `56d15fc1c217b0c112f8538a5585c2f7f2db2e88a9b1f1713bae0f29227d753b` |
| semantic_robustness_01 | ids.json | `0e2f78d96c3492340e714e8217d5601f43fb9c92c865b900b7ccae38da0f01c8` |
| semantic_robustness_01 | expectations.json | `8d52cabe84a7d4ddbf96f46599dd48df7fc5c4428045f9060086dd49364ec84d` |
| semantic_robustness_01 | construction_receipts.json | `a11e2841a14ad08c4b3ca502c632aad25d1c4756d8e74ab6d4595e06d9465068` |
| semantic_safety_02 | sources.json | `39bddd7575ab463cab38d8246d0233efb3ef510ec93f150d47655183df78d77a` |
| semantic_safety_02 | ids.json | `87ff2e971a2171b19d89f9a7bfb6766d3b06b236b55e18b35d11745f7dfe954c` |
| semantic_safety_02 | expectations.json | `d8407e4ec10262a6067404f97b7d93280a5a5be2d221006518ad58e834a051a7` |
| semantic_safety_02 | construction_receipts.json | `5e85faebeefe1b3279df1aa53cb68b58fdadf8434a1b183a2e4ca8d620ec0e31` |

[Manifest de execução e seleção por caso](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/run_manifest.json); [inventário de preservação](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/preservation_before.json); [métricas completas](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/metrics.json); [análise dos 80 casos, obrigações antigas/unificadas, awards e classificações](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/case_analysis.json).

### Definições

Exact é concordância de score com a expectation indicada; não é acurácia contra gold independente. MAE = média de |score−expected|; bias = média de score−expected. Precision/recall de obrigações são microagregadas sobre obligation_ids com award eligible, sem tratar falta de checker como refutação.

Falso crédito é uma parcela **efetivamente pontuada** sem autorização na expectation/pauta aplicável; não apenas over-score. Missed credit é parcela prevista não pontuada. False veto é obrigação legitimamente pontuável bloqueada por conflito/decisão negativa; rejeição representacional e ausência de witness são registradas como perdas, não automaticamente como false veto. Guard FP exige autoridade negativa indevida, não a mera existência de resultado histórico guard_only. Context authority error significa uso positivo ou veto de evidência contextual que deveria ser excluída; não equivale a acerto de todas as etiquetas discursivas.

Um conflito registrado sem positivo elegível também aparece no trace atual. Portanto o aumento de contagem de conflitos não implica aumento de falsos vetos. Aliases semânticos/nativos e produtores diferentes não duplicam a parcela pontuada.

## A. robustness_01 — observed regression

### Comparação primária com a expectation congelada (48 pares)

| Métrica | Antes, mesmas respostas | Unificado |
| --- | ---: | ---: |
| Casos no denominador | 48 | 48 |
| Soma dos scores | 61 | 71 |
| Exact score | 40/48 (83.33%) | 43/48 (89.58%) |
| MAE | 0.3333 | 0.2083 |
| Bias (score − expected) | -0.3333 | -0.1250 |
| Over-score: casos / pontos | 0 / 0 | 1 / 2 |
| Under-score: casos / pontos | 8 / 16 | 4 / 8 |
| Obligation precision | 37/37 = 100.00% | 41/42 = 97.62% |
| Obligation recall | 37/45 = 82.22% | 41/45 = 91.11% |
| FP / missed obligations | 0 / 8 | 1 / 4 |
| Parcelas extras contra expectation: casos / pontos | 0 / 0 | 1 / 2 |
| Missed credit: parcelas / pontos | 8 / 16 | 4 / 8 |
| False vetoes: casos / obrigações | 0 / 0 | 0 / 0 |
| Guard false positives: casos / eventos | 0 / 0 | 0 / 0 |
| Conflitos registrados: casos / obrigações | 6 / 6 | 12 / 25 |
| Conflitos esperados preservados | 6/6 | 5/6 |
| Context authority errors / alvos | 0/9 | 0/9 |
| Fallback / technical uncertainty no denominador | 0 / 0 | 0 / 0 |

Os 2 pontos extras e a única obrigação FP dessa comparação bruta são **exclusivamente E02**: a fixture histórica ainda espera 2, mas a política de autocorreção autorizada antes desta regressão permite 4. Não é um novo falso crédito material. A fixture foi mantida intacta.

### Política E02 previamente autorizada, mostrada em paralelo

Expected total: 79, em vez de 77. Antes → depois: score total **61 → 71**; exact **39/48 → 44/48 (91,67%)**; MAE/bias **0,3750/−0,3750 → 0,1667/−0,1667**. Precision **37/37 → 42/42 (100%)**; recall **37/46 → 42/46 (91,30%)**. Falsos créditos materiais: **0 → 0**; false vetoes: **1 → 0** (E02); missed: **9 → 4 obrigações**, **18 → 8 pontos**. Os cinco conflitos não retratados previstos por essa política permanecem preservados: 5/5.

As perdas restantes são A01, A02, A06 e A07, 2 pontos cada, todas já presentes. Nenhuma nova regressão de score sob a política autorizada. A rodada original de robustness, distinta das gravações pareadas, somou 67, exact 41/48 contra a fixture e teve um fallback (F08); esses números não medem o efeito isolado desta arquitetura.

### Tabela dos 48 casos

¹ `original_score` é a primeira rodada histórica. `old_score pareado` é a última execução pré-unificação sobre exatamente o raw_output reusado. ² Issues são julgadas pela política autorizada; E02 mantém também o desvio contra a fixture visível. `OTHER` inclui recuperação de representação e perda preexistente, pois a taxonomia solicitada não contém `FIXED_REPRESENTATION`.

| case_id | expected congelado | original_score¹ | old_score pareado | unified_score | old_issue² | unified_issue² | classification |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| [p3_rob_a01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_a01.json) | 2 | 0 | 0 | 0 | missed a.count | missed a.count | `OTHER` |
| [p3_rob_a02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_a02.json) | 2 | 0 | 0 | 0 | missed a.probability | missed a.probability | `OTHER` |
| [p3_rob_a03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_a03.json) | 2 | 0 | 0 | 2 | missed b.space | sem erro de crédito observado | `OTHER` |
| [p3_rob_a04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_a04.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_a05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_a05.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_a06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_a06.json) | 2 | 0 | 0 | 0 | missed c.first_strategy | missed c.first_strategy | `OTHER` |
| [p3_rob_a07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_a07.json) | 2 | 0 | 0 | 0 | missed c.second_strategy | missed c.second_strategy | `OTHER` |
| [p3_rob_a08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_a08.json) | 8 | 8 | 6 | 8 | missed c.total | sem erro de crédito observado | `OTHER` |
| [p3_rob_b01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_b01.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_b02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_b02.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_b03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_b03.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_b04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_b04.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_b05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_b05.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_b06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_b06.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_b07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_b07.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_b08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_b08.json) | 8 | 8 | 8 | 8 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_c01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_c01.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_c02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_c02.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_c03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_c03.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_c04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_c04.json) | 2 | 0 | 0 | 2 | missed b.conclusion | sem erro de crédito observado | `OTHER` |
| [p3_rob_c05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_c05.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_c06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_c06.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_c07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_c07.json) | 5 | 5 | 5 | 5 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_c08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_c08.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_d01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_d01.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_d02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_d02.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_d03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_d03.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_d04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_d04.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_d05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_d05.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_d06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_d06.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_d07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_d07.json) | 4 | 4 | 4 | 4 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_d08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_d08.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_e01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e01.json) | 2 | 2 | 2 | 2 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_rob_e02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e02.json) | 2 | 4 | 2 | 4 | autocorreção vetada; −2 pela política autorizada | 4 correto pela política; +2 contra fixture histórica | `EXPECTATION_POLICY_MISMATCH` |
| [p3_rob_e03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e03.json) | 2 | 2 | 2 | 2 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_rob_e04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e04.json) | 2 | 2 | 2 | 2 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_rob_e05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e05.json) | 0 | 0 | 0 | 0 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_rob_e06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e06.json) | 0 | 0 | 0 | 0 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_rob_e07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e07.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_e08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e08.json) | 2 | 2 | 0 | 2 | missed b.same | sem erro de crédito observado | `OTHER` |
| [p3_rob_f01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_f01.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_f02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_f02.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_f03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_f03.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_f04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_f04.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_f05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_f05.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_f06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_f06.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_f07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_f07.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_rob_f08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_f08.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |

## B. safety_02 — observed regression

### Comparação pareada (31 casos com resposta gravada)

| Métrica | Antes, mesmas respostas | Unificado |
| --- | ---: | ---: |
| Casos no denominador | 31 | 31 |
| Soma dos scores | 27 | 33 |
| Exact score | 22/31 (70.97%) | 29/31 (93.55%) |
| MAE | 0.5161 | 0.1290 |
| Bias (score − expected) | -0.3226 | -0.1290 |
| Over-score: casos / pontos | 2 / 3 | 0 / 0 |
| Under-score: casos / pontos | 7 / 13 | 2 / 4 |
| Obligation precision | 13/15 = 86.67% | 18/18 = 100.00% |
| Obligation recall | 13/20 = 65.00% | 18/20 = 90.00% |
| FP / missed obligations | 2 / 7 | 0 / 2 |
| Parcelas extras contra expectation: casos / pontos | 2 / 3 | 0 / 0 |
| Missed credit: parcelas / pontos | 7 / 13 | 2 / 4 |
| False vetoes: casos / obrigações | 5 / 5 | 0 / 0 |
| Guard false positives: casos / eventos | 4 / 4 | 0 / 0 |
| Conflitos registrados: casos / obrigações | 13 / 14 | 15 / 19 |
| Conflitos esperados preservados | 7/12 | 12/12 |
| Context authority errors / alvos | 0/9 | 0/9 |
| Fallback / technical uncertainty no denominador | 0 / 0 | 0 / 0 |

Os resultados antigos ALL32 foram: score total 27, exact 23/32, MAE 0,5000, bias −0,3125, incluindo o fallback S2_05=0. O comparativo válido para o replay usa **22/31 → 29/31**. Não calculamos um “unified ALL32” imputando score ao indisponível.

### Segurança

- Falsos créditos conhecidos: **2 casos / 3 pontos → 0 / 0**. S2_03 passa de 1 para 0; S2_06 de 4 para 2.
- False vetoes de qualquer origem: **5 → 0**. Os quatro guard FPs conhecidos são S1_02, S1_03, S1_07 e S4_07 (7 pontos); todos resolvidos. S1_08 era um quinto veto, causado pela antiga agregação de interpretações concorrentes, sem guard negativo: também desapareceu, recuperando 2 pontos.
- Guard-generated awards: **0 → 0**. Nenhum resultado guard_only foi eleito como witness.
- Conflitos não retratados esperados nos casos disponíveis: **7/12 → 12/12**. O 13º alvo está em S2_05, indisponível, e não é contado como sucesso.
- Aceitação operacional de retratação (parcelas finais corretas e ausência de uso da posição retirada): **3/9 → 8/9**, contando S4_07 além dos oito S1. Somente em S1: **3/8 → 7/8**.
- Reconhecimento explícito de todos os alvos retirados como SUPERSEDED: **6/9**. Não confundir 8/9 de efeito correto com 8/9 de rotulagem correta.
- Context authority errors: **0/9** alvos. Não houve crédito ou veto de NON_ADOPTED, SUPERSEDED ou AMBIGUOUS.

Persistem S1_05 e S3_07, ambos 0 em vez de 2, perdas representacionais já existentes; nenhum hard veto central nesses casos. Sem nova perda material. S1_05 não reconhece a revisão retrospectiva e mantém os dois claims como ACTIVE, mas ambos ficam sem representação executável. S1_06 mantém a linha riscada como ACTIVE, também sem checker/crédito/veto, enquanto a resposta final pontua corretamente. S1_08 mantém as duas expressões anotadas como AMBIGUOUS e prova a igualdade final independente. São limitações reais do resolver, não “sucesso completo” de entendimento discursivo.

### Tabela dos 32 casos

| case_id | expected congelado | original_score¹ | old_score pareado | unified_score | old_issue² | unified_issue² | classification |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| [p3_safe_s1_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s1_01.json) | 4 | 4 | 4 | 4 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s1_02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s1_02.json) | 2 | 0 | 0 | 2 | falso veto b.ordered_pairs | sem erro de crédito observado | `FIXED_FALSE_VETO` |
| [p3_safe_s1_03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s1_03.json) | 2 | 0 | 0 | 2 | falso veto c.strategy_case_2 | sem erro de crédito observado | `FIXED_FALSE_VETO` |
| [p3_safe_s1_04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s1_04.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s1_05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s1_05.json) | 2 | 0 | 0 | 0 | missed b.conclusion | missed b.conclusion | `OTHER` |
| [p3_safe_s1_06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s1_06.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s1_07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s1_07.json) | 1 | 0 | 0 | 1 | falso veto c.continue_compartments | sem erro de crédito observado | `FIXED_FALSE_VETO` |
| [p3_safe_s1_08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s1_08.json) | 2 | 0 | 0 | 2 | falso veto a.first_white_probability | sem erro de crédito observado | `FIXED_FALSE_VETO` |
| [p3_safe_s2_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s2_01.json) | 2 | 2 | 2 | 2 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_safe_s2_02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s2_02.json) | 0 | 0 | 0 | 0 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_safe_s2_03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s2_03.json) | 0 | 1 | 1 | 0 | falso crédito c.continue | conflito preservado | `FIXED_FALSE_CREDIT` |
| [p3_safe_s2_04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s2_04.json) | 0 | 0 | 0 | 0 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_safe_s2_05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s2_05.json) | 0 | 0 | 0 | — | fallback histórico | REPLAY_UNAVAILABLE; sem raw_output | `REPLAY_UNAVAILABLE` |
| [p3_safe_s2_06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s2_06.json) | 2 | 4 | 4 | 2 | falso crédito b.conclusion | conflito preservado | `FIXED_FALSE_CREDIT` |
| [p3_safe_s2_07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s2_07.json) | 0 | 0 | 0 | 0 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_safe_s2_08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s2_08.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_safe_s3_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s3_01.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s3_02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s3_02.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s3_03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s3_03.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s3_04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s3_04.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s3_05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s3_05.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s3_06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s3_06.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s3_07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s3_07.json) | 2 | 0 | 0 | 0 | missed c.first_strategy | missed c.first_strategy | `OTHER` |
| [p3_safe_s3_08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s3_08.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s4_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s4_01.json) | 2 | 2 | 2 | 2 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_safe_s4_02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s4_02.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_safe_s4_03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s4_03.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s4_04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s4_04.json) | 2 | 2 | 2 | 2 | sem erro de crédito observado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_safe_s4_05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s4_05.json) | 0 | 0 | 0 | 0 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |
| [p3_safe_s4_06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s4_06.json) | 0 | 0 | 0 | 0 | sem erro de crédito observado | sem erro de crédito observado | `PRESERVED_CORRECT` |
| [p3_safe_s4_07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s4_07.json) | 2 | 0 | 0 | 2 | falso veto a.bottom_white_count | sem erro de crédito observado | `FIXED_FALSE_VETO` |
| [p3_safe_s4_08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_safety_02/p3_safe_s4_08.json) | 0 | 0 | 0 | 0 | conflito preservado | conflito preservado | `PRESERVED_CONFLICT` |

## Invariantes nos casos observados

Nenhuma violação **de autoridade/pontuação** dos dez invariantes críticos foi registrada. Isso não afirma que todos os rótulos de discurso estejam corretos. Cada caso disponível possui um arquivo `.audit.json` com violations, operational_order e a cadeia de cada veto.

| Invariante | Evidência observada |
| --- | --- |
| I1 Guard nunca gera award | 60 awards elegíveis / 55 parcelas pontuadas inspecionadas; zero witness guard_only ou award_eligible de guard |
| I2 NON_ADOPTED sem hard veto | 19 entradas, incluindo aliases, sem participação em veto ou crédito |
| I3 model_abandoned não basta | Todo hard veto exigiu fonte, estado validado, checker_ref e contradição; nenhum veto foi fundado só no flag. O subcaso de hard veto recuperado de flag abandoned não teve exposição positiva nesta amostra |
| I4 SUPERSEDED não bloqueia correção | 11 entradas SUPERSEDED, zero autoridade atual; aliases nativos retirados também excluídos |
| I5 AMBIGUOUS sem crédito | 11 entradas AMBIGUOUS; zero suporte a award |
| I6 AMBIGUOUS sem hard veto | Zero veto por ambiguidade; S1_08 recebe os 2 pontos da igualdade final independente |
| I7 ACTIVE refutado pode bloquear | 73 decisões elegíveis, todas com premissas ACTIVE e checker de refutação/incompatibilidade; nenhum target premiado apesar de receipt aplicado |
| I8 Conflito local | Targets dentro do contrato de dependências; S2_06 preserva b.different, S4_07 preserva a.count, E04 preserva a.count |
| I9 Provenance e política | Todos os bloqueios de award têm receipt válido; nenhum bypass ou receipt sem fonte/checker/revisão |
| I10 Ordem operacional | 79/79: resolver refeito com ledger em ordem inversa; candidatos/resultados/mappings invertidos; mesmos snapshot, decision_ids, elegibilidade e score |

A checagem de ordem reutiliza os receipts matemáticos reais desta execução. Não reordena a fonte nem muda a direção temporal das correções, não chama o extractor e não modifica os resultados dos checkers. A ausência de exposição de um ramo não é convertida em evidência de sucesso nesse ramo.

Estados totais, incluindo aliases: ACTIVE=182, SUPERSEDED=11, NON_ADOPTED=19, AMBIGUOUS=11. Os 79 resultados registram 13 FORMAL_VERIFIED e 1 FORMAL_REFUTED; nenhum FORMAL_ERROR. A prova formal não foi inferida do número correto: consta compiled/refutation_verified nos receipts Lean.

## Todos os caminhos de veto e segundo produtor determinístico

Revisão estática do fluxo congelado e inspeção dinâmica concordam: produtores emitem resultados; `VetoEligibilityPolicy.decide` emite autoridade; `reconcile` aceita receipts da instância/revisão; `award` confere receipt e target. O antigo atalho `any(mathematical_refutation)` não autoriza bloqueio. O branch Current segue legado, porém não foi executado aqui nem usado como fallback.

| Produtor | Vetos robustness | Vetos safety | Total |
| --- | ---: | ---: | ---: |
| positive_checker | 11 | 15 | 26 |
| native_checker (segundo determinístico) | 14 | 24 | 38 |
| atomic_guard | 3 | 1 | 4 |
| structural_guard | 4 | 1 | 5 |
| Total de receipts elegíveis | 32 | 41 | 73 |

Esses receipts dão 110 ligações receipt→target (64+46), pois há dependências e produtores sobrepostos. A pontuação não é duplicada. Há 267 candidatos/receipts de política no total, incluindo positivos e não aplicáveis. Todos os vetos observados têm registro completo:

```text
producer → evidence + source range → discourse_state → checker_result
         → VetoEligibilityPolicy receipt → reconciliation target → award effect
```

Os arquivos `*.audit.json`, campo `veto_chains`, contêm **cada** ligação com o resultado original do checker, receipt completo, estado, IDs e efeito. Não há amostragem nessa inspeção. Rejeição de representação, ausência de witness, erro técnico e all_of da pauta não são classificados como hard veto contra outro positivo.

Nos casos S1_02/S1_07/S4_07, os aliases nativos antigos ficam SUPERSEDED no mesmo snapshot dos semânticos; nenhuma refutação nativa residual derrota a correção. A fonte nativa não foi removida: produziu 38 receipts negativos válidos em outros casos e continua detectando negativos representáveis omitidos pelo extractor. Safety regular aparece como trace de compatibilidade de resultados dessa projeção, sem autoridade paralela.

## Casos prioritários: provenance e decisão

### E02 — EXPECTATION_POLICY_MISMATCH

Fonte antiga: `Ao repetir o mesmo compartimento, o quinto também libera branca.` em [37,101). Evidence `E004:p3:a76bc78cc9c88601e531` fica SUPERSEDED, com `superseded_by=[E005:p3:859cc279dbdb68b8e6aa]`. O envelope original antigo abrangia também a correção; a cláusula, não o envelope, define a ordem.

Fonte corretiva: `Na verdade, ao repetir o mesmo compartimento, somente o sexto libera branca.` em [102,178). O marcador literal `Na verdade` está em [102,112); relação `incompatible_local_correction`, propriedade `(b,repeticao_branca)`. A correção fica ACTIVE; `{6}` → b.same_compartment → DETERMINISTIC → `tme2-p3-check.v1:78b1e4faa5515d4ab39a` → DETERMINISTIC_VERIFIED → sufficient=true → b.same=2. Com a.count=2, score=4. Nenhum veto incorreto permaneceu.

A primeira execução histórica tinha score 4; a gravação pareada pré-unificação, 2; este replay, 4. Contra a fixture imutável, expected=2 e erro=+2. Contra a política explicitamente autorizada antes da regressão, expected=4 e erro=0. Ambos permanecem visíveis; não se reescreveu expectativa nem se legitimou o resultado após observar a nota.

### E04 — contradição não retratada

`Somente o sexto` e `O quinto também` permanecem ACTIVE, sem superseded_by. O claim exclusivo `{6}` tem checker positivo, mas a inclusão do quinto é mantida como membership parcial. Evidence negativa: `E004:p3:49699553e8a33bd3e27b`.

O guard atômico consulta o evento (5,5) do certificado finito e retorna DETERMINISTIC_FAILED; a incompatibilidade estrutural com o conjunto exclusivo também é validada. Ambos passam pela política. Receipts `veto:9857005940671f4814e4416db67a730f7f47130c7ae6df7ae99381de70cac985` e `veto:e10c1334f8235cdea4ca3d639c985043b62e1f88a00fde4702eab7ea6c926bb0` bloqueiam b.same e o destino contratual b.second_white_probability. b.same não pontua; a.count permanece em 2. Score 2→2; conflito preservado, sem “última afirmação vence”.

### A08 — perda representacional eliminada

Source [3,68): `A probabilidade total de vitória é um sexto, com (2/6)*(1/2)=1/6.` Evidence `E002:p3:eb35b237530d2a890df9`, ACTIVE. O payload gravado `1/6, com (2/6)*(1/2)=1/6` era não executável. `unique_literal_payload` seleciona a igualdade **inteira escrita** `(2/6)*(1/2)=1/6`, sem fabricar derivação ou remover lado falso.

c.total_win_probability → COMPOSITE → `tme2-p3-check.v1:d68e808f9699fbc54ec6` → COMPOSITE_VERIFIED, FORMAL_VERIFIED real, sufficient=true. O receipt referencia também as sete evidências de continuação, estratégias/contagens e condicionais. c.total recupera 2; total do item=8 (1+2+2+1+2). Original histórico 8, gravação pareada 6, unificado 8. Nenhum veto. Não há variabilidade nova do extractor nessa transição.

### E08 — perda representacional eliminada com contexto local

A citação de Beatriz (`E002:p3:ef304d42a79d4bab3aeb`) fica NON_ADOPTED e não fornece crédito nem veto. A resposta própria em [88,168), `E003:p3:04cfeef77873b1de15d7`, fica ACTIVE. O adapter converte apenas a exclusividade literalmente escrita em `{6}`.

b.same_compartment → DETERMINISTIC → `tme2-p3-check.v1:acd62752b25ca7bcb23c` → DETERMINISTIC_VERIFIED → sufficient=true → b.same=2. Original histórico 2, gravação pareada 0, unificado 2. O veto contextual permanece local à citação; não contamina o span adotado.

[p3_rob_e02 trace completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e02.json) · [auditoria](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e02.audit.json)

[p3_rob_e04 trace completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e04.json) · [auditoria](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e04.audit.json)

[p3_rob_a08 trace completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_a08.json) · [auditoria](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_a08.audit.json)

[p3_rob_e08 trace completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e08.json) · [auditoria](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_unified_regression_01/semantic_robustness_01/p3_rob_e08.audit.json)

## FALSE AUTOMATIC CREDIT AUDIT

- Robustness: **0 pontos falsos materiais** pela política vigente; **2 pontos extras contra a fixture histórica**, exclusivamente o mismatch fundamentado de E02.
- Safety: **0 pontos falsos** restantes; S2_03 perdeu o 1 indevido e S2_06 perdeu os 2 indevidos, mantendo b.different=2.
- Novo falso crédito: **nenhum**. Não houve compensação oculta entre parcela falsa e parcela perdida: a comparação inclui rule_ids e obrigações, não só score total.
- NON_ADOPTED/SUPERSEDED/AMBIGUOUS usados em award: **zero**. Guard produzindo award: **zero**. Witness selecionado sem resultado verificável: **zero**.
- Claim falso rotulado ACTIVE sem checker/veto: **sim, há lacuna de representação/rotulagem** em S1_05 (1/6 retirado retrospectivamente) e S1_06 (5/6 riscado). Não foram premiados nem vetaram a correção. São afirmações retiradas na fonte, não evidência de falso claim atualmente adotado recebendo crédito. Não foi identificado falso claim adotado e verificado cuja refutação fosse ignorada.

Não se afirma cobertura universal dos falsos claims. As entradas ACTIVE sem checker executável ficam listadas em cada `.audit.json`; esse diagnóstico também contém claims corretos não normalizados, claims em item incompatível e estratégias incompletas. Ausência de checker não foi contada como prova de verdade ou falsidade.

## FALSE-VETO AUDIT

False vetoes materiais restantes: **0** em ambos os conjuntos disponíveis. Os quatro guard FPs conhecidos de Safety 02 desapareceram e seus 7 pontos legítimos foram recuperados. O veto adicional de S1_08 também desapareceu. Nenhum novo false veto, nenhum SUPERSEDED/NON_ADOPTED/AMBIGUOUS com hard veto e nenhum bloqueio de parcela independente fora do contrato foram observados.

As seis parcelas ainda perdidas (A01/A02/A06/A07, S1_05/S3_07) não têm veto central contra positivo suficiente. Causas: associação de número à quantidade não reconhecida; fração verbal não normalizada; subject ligado a múltiplas cláusulas; payload de contagem ainda em prosa. S1_05 também mantém relação retrospectiva de retirada não reconhecida. Essas perdas já existiam; não foram corrigidas nesta tarefa.

## Replay indisponível, histórico e limites

S2_05: fallback original `extractor_incomplete_or_refused`, sem raw_output completo para bind. Novo status REPLAY_UNAVAILABLE; score unificado ausente. Não houve chamada substituta, nem contagem como acerto/erro semântico. Robustness tem 48 gravações utilizáveis na rodada mais recente; o fallback F08 da primeira rodada aparece apenas no histórico, pois existe gravação posterior bem-sucedida da mesma fonte.

Os conjuntos já eram observados; expectativas por construção e a política E02 não são gold externo independente. Nenhuma métrica aqui é estimativa de generalização. Não houve mudança de texto, payload gravado, prompt ou política para melhorar o resultado. As lacunas de estados e representação descritas não foram reparadas. O próximo conjunto, se autorizado, deverá ser novo e congelado antes de executar; Safety 03 não foi criado.

As seis perdas preexistentes e as rotulagens limitadas não violaram os critérios de autoridade/pontuação exigidos para prontidão nesta regressão. Isso permite o próximo teste independente; não autoriza tratar o resolver como semanticamente completo.

## Reprodutibilidade, artefatos e integridade final

Comandos executados, com os drivers de regressão/análise em diretório temporário (nenhum código existente alterado):

```bash
cd ~/Documents/confia-lean-auditor-tme-semantic-formal-p3
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app:. CONFIA_TME_SEMANTIC_ENABLED=0   /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python   /private/tmp/p3-unified-regression-01/run.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app:. CONFIA_TME_SEMANTIC_ENABLED=0   /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python   /private/tmp/p3-unified-regression-01/analyze.py
git status --short
git rev-parse HEAD
```

Manifest inclui plano dos 80 casos, caminhos/hash das gravações, hashes de fixtures, SHA, estado inicial limpo, config replay/Lean e preservação final. `case_analysis.json` registra obligations antigas/unificadas, FP/FN, créditos, contexto e classificações. Cada JSON de caso preserva fonte completa, claims/spans, mapping, checker results, estados, vetos e awards. Cada `.audit.json` registra todos os vetos e a checagem de ordem. Logs: `/private/tmp/p3-unified-regression-01/run.log` e `analysis.log`.

Os artefatos de avaliação e de prova são novos outputs ignorados pelo Git; o único arquivo novo visível em `git status --short` é este relatório. Nenhum arquivo rastreado foi alterado. HEAD permanece `a6ab3d2c173ee801e1bc5a27d155215c054e007d`; sem stage/commit.

**READY_FOR_P3_SAFETY_03**
