# TME P3 — Semantic Formal DEV02 — Validação 01

## 1. Escopo e procedência

Validação exclusivamente por leitura dos artefatos já existentes em `artifacts/evaluations/tme_p3_semantic_formal_dev_02`: 16 resultados individuais, dois manifests e dois summaries. Nenhum modo, extractor, teste ou compilador Lean foi reexecutado nesta tarefa. Nenhum código, fixture, prompt, checker ou pauta foi alterado; somente este relatório foi criado. Não houve uso de gold/holdout nem commit.

**SHA exato da implementação executada: `dc12446418efe8db1b92694f4b220bf682cb21c6`**, commit `Fix P3 conflict preservation before reconciliation`. Os dois manifests registram esse SHA, `worktree_clean=true`, `git_status=""` e `state=completed`; o HEAD local confere. Não se confunde esse SHA com o de DEV01 (`e4dc1e94b0e8e22a16489fcdcc3eb14e1abfd4ab`) nem com o HEAD inicial da tarefa anterior de correção.

Execução registrada em UTC: Current, 2026-11-06 02:37:44–02:37:45; Semantic, 02:37:53–02:39:20. Em America/Fortaleza, corresponde a 2026-11-05, 23:37–23:39. Esta tarefa não realizou uma segunda execução. Os artefatos permitem conferir a execução arquivada; a informação de que houve uma única execução DEV02 foi fornecida pelo usuário.

Fontes principais:

- [Manifest Current](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_02/tme_current/run_manifest.json) e [summary Current](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_02/tme_current/summary.json).
- [Manifest Semantic](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_02/tme_semantic_formal/run_manifest.json) e [summary Semantic](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_02/tme_semantic_formal/summary.json).

## 2. Fixtures e integridade

SHA-256 dos bytes, recalculado por leitura e coincidente com `input_hashes.dataset_bytes/ids_bytes` dos dois manifests e com os relatórios DEV01 e pré-DEV02:

| Fixture | SHA-256 |
| --- | --- |
| `tests/fixtures/tme_semantic_formal_p3/dev_sources.json` | `d12a77cd87f0e5197db7e3cdafaedf78a130dd7dc3b1b59fa5d029a702e375cc` |
| `tests/fixtures/tme_semantic_formal_p3/dev_ids.json` | `a7ab3a65f60e1284b119c8974a47e3eea0c037f58c96963bff8c7372ebcaab0a` |

A ordem dos oito IDs foi conferida. O `source_text` de cada um dos 16 resultados coincide integralmente com a fonte congelada correspondente. Também foram recalculados os hashes dos oito arquivos do pacote Semantic Formal P3 e do conjunto `frozen_code`, sem importar/executar o pipeline: coincidem com ambos os manifests.

- `configuration_hashes.experiment`: `2be7e9ecf8cf2c3ff096a198e5325e0a94185b535a1d388d91ad536aa7907033`.
- `configuration_hashes.frozen_code`: `98156af5f695db102257b255cb98ffdf9644d58613bc34dcf776b7cb35e7b77e`.

## 3. Scores caso a caso

Valores lidos dos JSON individuais e conferidos contra os summaries. Fallback e technical uncertainty são false em cada caso de ambos os modos.

| case_id | Current | Semantic DEV02 | Delta | Parcelas concedidas no Semantic |
| --- | ---: | ---: | ---: | --- |
| p3_dev_initial_count | 0 | 4 | +4 | a.count=2; a.probability=2 |
| p3_dev_isolated_answer | 2 | 2 | 0 | a.probability=2 |
| p3_dev_sample_space | 0 | 2 | +2 | b.space=2 |
| p3_dev_favorable_partition | 0 | 8 | +8 | b.space=2; b.different=2; b.same=2; b.conclusion=2 |
| p3_dev_complete_strategy | 0 | 8 | +8 | c.continue=1; c.first_strategy=2; c.second_strategy=2; c.conditionals=1; c.total=2 |
| p3_dev_probability_error | 0 | 2 | +2 | b.same=2 |
| p3_dev_hypothesis_context | 0 | 2 | +2 | a.probability=2 |
| p3_dev_partial_conflict | 0 | 2 | +2 | a.count=2 |
| **Total** | **2** | **30** | **+28** | |

Vetores confirmados, na ordem de `dev_ids.json`:

```text
TME_CURRENT         = [0, 2, 0, 0, 0, 0, 0, 0]
TME_SEMANTIC_FORMAL = [4, 2, 2, 8, 8, 2, 2, 2]
```

Comparação pareada: **Semantic melhor = 7; Current melhor = 0; empate = 1**. “Melhor” nesta contagem significa score maior; a legitimidade das parcelas é vinculada à perícia anterior, não inferida do aumento de nota.

## 4. Previsão pré-DEV02 e desaparecimento do falso crédito

O [relatório do fix, seção 7](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_CONFLICT_PRESERVATION_FIX_01.md) registrou antes de DEV02 o controle com a resposta de extração observada: `partial_conflict=2`, somente `a.count`, `b.same=0` e conflitos preservados. Essa previsão não foi ajustada após ler DEV02.

| Condição prevista | Evidência DEV02 | Resultado |
| --- | --- | --- |
| b.same não recebe os 2 pontos indevidos | Award de b.same_compartment: eligible=false, award_decision=blocked_conflict | Confirmada |
| Conflito de repetição observável | CONFLICTING_EVIDENCE, resolved=false, envolvendo os spans do sexto e do quinto | Confirmada |
| Crédito independente de a.count preservado | DETERMINISTIC_VERIFIED, sufficiency=true, eligible=true, credits a.count=2 | Confirmada |
| Score total 2, emergente das obrigações | score=2.0; única parcela em credits é a.count | Confirmada |

No [resultado de partial_conflict](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_02/tme_semantic_formal/p3_dev_partial_conflict.json), a cadeia efetivamente registrada é:

| Fonte / evidência | Obrigação e resultado | Destino |
| --- | --- | --- |
| “Há duas bolas brancas embaixo.”; E002:p3:7680cddee0359e14aa0f; valor 2 | a.bottom_white_count; checker tme2-p3-check.v1 deriva white_count=2; DETERMINISTIC_VERIFIED; suficiente | a.count=2 |
| “somente o sexto libera branca”; E004:p3:dc62180683f1cbf26a3a; {6} | b.same_compartment; DETERMINISTIC_VERIFIED | Positivo preservado, mas award bloqueado pelo conflito |
| “o quinto também libera branca”; E005:p3:856496825099c4e46c5d; {5} | b.same_compartment; DETERMINISTIC_FAILED; mathematical_refutation=true; checker deriva same_compartment_favorable=[6] | Refutação chega à reconciliação; CONFLICTING_EVIDENCE; nenhum crédito |
| “11/36” e “12/36” | b.second_white_probability; COMPOSITE_INCOMPLETE e COMPOSITE_FAILED | Conflito não resolvido; award blocked_conflict; zero em b.conclusion |

**Distinção de mecanismo:** no DEV02 o extractor produziu `{5}`, formato aceito pelo caminho de verificação existente. Por isso `conflict_guard_results=[]` e `atomic_guard_results=[]`. A contradição foi refutada pelo checker determinístico e reconciliada pelo caminho regular. Não é correto afirmar que o novo guard atômico disparou nesta execução.

O guard introduzido pelo fix cobre a representação em prosa rejeitada no DEV01; sua atuação nessa representação foi demonstrada pelo controle pré-DEV02 e pelos testes documentados no relatório do fix. DEV02 confirma a saída prevista e a preservação da contradição nesta extração, mas não isola causalmente o efeito do novo guard, pois a representação extraída mudou.

O falso crédito material anteriormente identificado em `p3_dev_partial_conflict / b.same / 2 pontos` **desapareceu**. Os 2 pontos de a.count permaneceram: pertencem a outra obrigação/item, são verificados pela contagem das bolas brancas inferiores e não dependem da exclusividade de repetição em b.

## 5. Fallback, incerteza técnica e statuses

**Zero fallback**: todos os oito resultados Semantic têm `fallback=false`, modo efetivo `TME_SEMANTIC_FORMAL`; manifest sem fallback_cases. **Zero technical uncertainty**: todos têm `technical_uncertainty=false`; summary registra zero casos. Current também tem zero em ambos os indicadores.

Em particular, isolated_answer agora foi processado pelo Semantic, com a.first_white_probability DETERMINISTIC_VERIFIED e a.probability=2. No DEV01 era fallback por InternalServerError. Não houve alteração de retry/fallback nesta tarefa; o empate em 2 não acrescenta pontos ao delta.

Contagem recalculada sobre `verification_results[].status` dos oito resultados, sem duplicar subchecks, awards ou recibos embutidos; coincide exatamente com o summary:

| Status | Quantidade |
| --- | ---: |
| DETERMINISTIC_VERIFIED | 8 |
| FORMAL_VERIFIED | 1 |
| COMPOSITE_VERIFIED | 9 |
| CONTEXT_REJECTED | 2 |
| COMPOSITE_FAILED | 3 |
| DETERMINISTIC_FAILED | 1 |
| COMPOSITE_INCOMPLETE | 1 |
| **Total de resultados de verificação** | **25** |

São contagens de resultados, não de casos, pontos ou todas as chamadas Lean internas. O FORMAL_VERIFIED de nível principal está em initial_count/a.first_white_probability: o recibo arquivado registra `compiled=true`, `2/6=1/3`, stdout/stderr vazios. Nenhum Lean foi executado novamente nesta validação.

CONTEXT_REJECTED aparece em sample_space e hypothesis_context; COMPOSITE_FAILED aparece duas vezes em probability_error e uma em partial_conflict; DETERMINISTIC_FAILED e COMPOSITE_INCOMPLETE aparecem em partial_conflict. Falha/incompletude de evidência matemática não foi confundida com incerteza técnica. Current registra um DETERMINISTIC_VERIFIED no seu summary.

## 6. Relação dos +28 com o forense DEV01

O [forense DEV01, seções 6–8](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_SEMANTIC_FORMAL_DEV01_FORENSIC.md) já classificava **15 parcelas, somando 28 pontos, como resgates legítimos** sobre o Current, além de uma parcela falsa de 2 pontos. As parcelas concedidas no DEV02 são as mesmas parcelas legítimas discriminadas na tabela de scores:

```text
initial_count       +4
sample_space        +2
favorable_partition +8
complete_strategy   +8
probability_error   +2
hypothesis_context  +2
partial_conflict    +2 (somente a.count)
                    --
                    +28
```

O DEV01 totalizava 32 no Semantic contra 2 no Current: delta +30, composto por +28 legítimos e +2 falsos. O DEV02 totaliza 30 contra 2: **delta +28**, com retirada da parcela falsa e manutenção das parcelas anteriormente julgadas legítimas. Isolated_answer conserva seus 2 pontos já concedidos pelo Current; não é resgate adicional.

Essa correspondência foi conferida por rule_id/pontos, não apenas pela soma. Não houve reclassificação retrospectiva da parcela falsa como legítima, criação de nova regra ou alteração de expectativa. As rotas/status de algumas evidências podem variar entre extrações; a igualdade dos créditos legítimos não implica identidade das respostas do extractor.

## 7. Limites da conclusão e estado do repositório

O resultado sustenta a validação do comportamento observado **nestes oito casos DEV**, incluindo o desaparecimento do falso crédito conhecido e a preservação do crédito independente. Não constitui estimativa de acurácia geral, avaliação contra gold, evidência de desempenho em holdout ou prova de ausência universal de falso crédito.

**Os oito casos são DEV observado. Já foram inspecionados, usados em diagnóstico e no desenvolvimento da correção; não podem ser tratados futuramente como avaliação independente**, mesmo sob novo nome ou nova execução. As métricas aqui são scores, comparação pareada e correspondência com o julgamento prévio da pauta.

A conferência usou leitura de JSON, comparação de fontes, hashes e inspeção de relatórios/código; não importou nem chamou o pipeline. Os 20 JSON DEV02 foram preservados. SHA inicial/final: `dc12446418efe8db1b92694f4b220bf682cb21c6`. Worktree inicialmente limpo; única inclusão desta tarefa:

```text
?? docs/audits/TME_P3_SEMANTIC_FORMAL_DEV02_VALIDACAO_01.md
```

Sem stage ou commit. Todos os números solicitados foram confirmados pelos artefatos.

**P3_DEV_SEMANTIC_BEHAVIOR_VALIDATED**
