# TME_MODEL_ABLATION_SMOKE_LIVE_01

Data: 2026-11-02. Decisão: **SMOKE_INCONCLUSIVE**.

O mini produziu uma resposta inválida em P5 (54 das 58 obrigações); o runner rejeitou a resposta inteira e pulou o sufficiency gate. Foram feitas **19 inferências**, sem retries: mini 9, Sol 10. Há quatro pares válidos para comparação. O Sol reduziu falsos créditos confirmados de 6 para 0 nesses pares, mas o apoio legítimo caiu de 74 para 72. Não há aprovação para avançar com base neste smoke incompleto.

**HOLDOUT processadas: 0/100. DEV completa 25 NÃO foi executada.** Não houve commit.

## Preflight, constantes e execução

- Branch: `feat/tme-dual-input`.
- SHA completo: `1284a06a745ddd59901c507ffe8bbe37e4266c4e`.
- `git status --short` vazio antes das inferências e novamente antes da criação deste relatório.
- O SHA contém `docs/audits/TME_MODEL_COMPAT_01.md` e a compatibilidade congelada.
- Disponibilidade: duas consultas de metadados, ambas HTTP 200, sem envio de textos; ver `model_availability.json`.
- Casos DEV exatos: `TME2026P1_06`, `TME2026P2_01`, `TME2026P3_02`, `TME2026P4_13`, `TME2026P5_09`.
- Ordem efetiva: P1 A→B, P2 A→B, P3 A→B, P4 A→B, P5 A→B. Etapa 2 de P5/A pulada. Detalhes em `execution_order.json`.
- Nenhum output de um braço alimentou o outro; etapas contemporâneas, sem reutilização de inferências/auditorias históricas.
- A: `gpt-4o-mini-2024-07-18`, `temperature=0`, sem configuração específica de reasoning.
- B: `gpt-6.1-sol`, `reasoning.effort=medium`, sem `temperature`, `top_p`, `top_logprobs` ou sampling substituto.
- Ambos: Responses API, `store=false`, `max_output_tokens=16000`, timeout 180 s, retries 0. O mesmo modelo foi usado nas duas etapas de cada braço.

> Os parâmetros de geração não são literalmente idênticos porque os modelos possuem contratos de API diferentes. Cada braço utiliza a configuração válida previamente especificada, mantendo constantes todas as camadas semânticas e matemáticas do experimento.

Os 233 hashes protegidos do código original e da cópia de execução permaneceram idênticos aos registrados no preflight. Soluções, problem IDs, referências, obligations, evidence units, prompts, regras de suficiência, reconciliação, pauta, checkers, canonicalização, PautaEngine e Lean ficaram congelados. Lean 4.28.0 foi usado com o ambiente existente.

| Hash | A | B |
|---|---|---|
| Prompt semantic | `590349b9a1ea613ed8e930cb275e019cc4e6fa287b6d5c2a5b9eb79cd7aa7d6e` | idêntico |
| Prompt sufficiency | `b7cb54d3f32afa16f3f8e112f0c8a07df5d7defd2d140f45b6b72285bcc5173c` | idêntico |
| Contrato/generator de schema sufficiency | `c0357dc85eccf98cb9c2cad8a848ec561c40096520cac28d3a0775f8e41e2aae` | idêntico |
| Transporte/modelo | `a0ae5acf748dac968314a06a2c36bb47d1387508cb4a4fb1757faefe1e9afcf4` | `b3887b01fa7802c924593036930c0a5617aa4de8e9328164154d2694ea564470` |

Os hashes individuais dos schemas da etapa 1, obligations, evidence units e pautas estão em `preflight.json`. **A igualdade de schema da etapa 2 é do contrato e gerador congelados.** Os schemas concretos do gate têm enums/IDs dependentes dos candidatos da etapa 1 e, portanto, seus hashes efetivos diferem entre braços; isso já constava no PREP/COMPAT e no preflight. Os payloads do gate também variam conforme a seleção de cada modelo. Não se afirma identidade byte a byte desses requests derivados. Ver `postflight.json` e os payloads/respostas brutos.

Para conter inclusive os arquivos de prova, a execução usou uma cópia byte a byte sob `artifacts/evaluations/tme_model_ablation_smoke_live_01/execution/`. Apenas o cache de dependências/build do Lean foi referenciado. As novas provas ficaram em `execution/artifacts/student_claim_checks/`. Não foram modificados código do produto, notas persistidas, submissões, transcrições ou AuditRuns existentes. Nenhum arquivo HOLDOUT foi carregado/copied para a execução.

## Métricas observadas

A tabela abaixo cobre o escopo dos cinco casos. **Os denominadores válidos são diferentes: 88 obrigações no mini e 146 no Sol.** Os 58 erros técnicos do mini não são 58 julgamentos matemáticos negativos. Os 87 apoios totais do Sol incluem 15 em P5, onde não há par mini válido.

| Métrica | Mini | Sol | Diferença B−A |
|---|---:|---:|---:|
| Casos tentados | 5 | 5 | +0 |
| Casos concluídos válidos | 4 | 5 | +1 |
| Etapa 1 válida | 4 | 5 | +1 |
| Etapa 2 válida | 4 | 5 | +1 |
| Obrigações no escopo | 146 | 146 | +0 |
| Obrigações com etapa 1 válida | 88 | 146 | +58 |
| Aparentemente satisfeitas: julgamento LIVE | 86 | 92 | +6 |
| Obrigações apoiadas | 84 | 87 | +3 |
| FORMAL_VERIFIED | 3 | 3 | +0 |
| DETERMINISTIC_VERIFIED | 6 | 6 | +0 |
| SEMANTIC_SUPPORTED | 75 | 78 | +3 |
| REFUTED | 0 | 1 | +1 |
| INDETERMINATE | 4 | 58 | +54 |
| TECHNICAL_ERROR | 58 | 0 | -58 |
| CONFLICT | 0 | 0 | +0 |
| Falsos créditos confirmados | 6 | 0 | -6 |
| Novos falsos créditos vs mini | 0 | 0 | +0 |
| Vínculos incorretos com crédito final | 2 | 0 | -2 |
| Falsas atribuições em outputs válidos | 10 | 0 | -10 |
| Créditos legítimos recuperados vs mini | 0 | 1 | +1 |
| Créditos legítimos perdidos vs mini | 0 | 3 | +3 |
| needs_review: casos | 3 | 5 | +2 |

“Concluído” exige ambas as etapas válidas; os dez pipelines terminaram operacionalmente. `needs_review` é o estado shadow do PautaEngine e não se confunde com a revisão manual desta avaliação. Os campos recuperados/perdidos usam o mini como referência, com zero na coluna de referência. As contagens de erro se sobrepõem e não devem ser somadas.

A comparação de qualidade usa somente os quatro pares completos:

| Métrica: somente P1–P4 | Mini | Sol | Diferença B−A |
|---|---:|---:|---:|
| Obrigações avaliadas | 88 | 88 | +0 |
| Obrigações apoiadas | 84 | 72 | -12 |
| Apoios legítimos confirmados | 74 | 72 | -2 |
| Apoios ambíguos | 2 | 0 | -2 |
| FORMAL_VERIFIED | 3 | 3 | +0 |
| DETERMINISTIC_VERIFIED | 6 | 6 | +0 |
| SEMANTIC_SUPPORTED | 75 | 63 | -12 |
| REFUTED | 0 | 1 | +1 |
| INDETERMINATE | 4 | 15 | +11 |
| Falsos créditos | 6 | 0 | -6 |
| Vínculos incorretos | 2 | 0 | -2 |
| Falsas atribuições | 10 | 0 | -10 |

O conjunto diagnóstico congelado marca 88 obrigações aparentemente satisfeitas nestes cinco casos, das quais 73 pertencem aos quatro pares válidos. A cobertura sobre esse denominador histórico foi mini 73/88 e Sol 83/88 no escopo todo; nos pares válidos, mini 73/73 e Sol 71/73. Esse rótulo é diagnóstico, não verdade matemática: pode incluir apoios inseguros. As 409 obrigações aparentemente satisfeitas da DEV completa estão fora do escopo deste smoke.

## Revisão matemática e divergências

Revisão local realizada pelo Codex sobre o texto integral, a pauta/referência congelada, evidence IDs, trechos autorizados, gate e auditoria. Não é revisão humana independente nem cega aos outputs. As decisões matemáticas foram registradas antes da leitura das notas sintéticas; uma atualização posterior somente enriqueceu referências às evidence units. Todas as 146 obrigações foram revisadas, incluindo os apoios de ambos os braços. A resposta bruta inválida de P5/A não foi promovida a julgamento válido.

Falso crédito significa **obrigação apoiada sem o requisito escrito/justificado**, mesmo quando pertence a uma via alternativa que não acrescenta pontos à nota. Vínculo incorreto significa apoio final sem suporte suficiente nos trechos autorizados, mesmo que o conteúdo exista em outro item. Falsa atribuição conta afirmação/extracão incorreta em output validado, incluindo erros que o gate bloqueou depois; exclui a resposta inválida de P5. Os IDs citados continuam pertencendo ao estudante: os erros foram de interpretação/atribuição de conteúdo, não de inexistência dos trechos.

| Caso/obrigação | Constatação no texto e resultado | Classificação |
|---|---|---|
| P1 `a.arithmetic_error_only` | 731−137=594 está correto; mini inventou a condição de erro aritmético. Sol rejeitou. Não implica ponto extra na via escolhida. | B_FIXED_FALSE_CREDIT |
| P1 `d.total_thirty` | Estudante escreve 3·10=20 e conclui 20; mini atribuiu 30, Sol preservou a contradição. | B_FIXED_FALSE_CREDIT |
| P1 `c.pattern_recognized` | Padrão legítimo no item c. Sol acrescentou E007 do item b a E010; o gate rejeitou o vínculo extra e retirou o apoio. | B_LOST_LEGITIMATE_CREDIT |
| P2 `b.realizable_1` | Não há pares/configuração para centro 1 em nenhum item. Mini inventou pares; Sol reconheceu a ausência. | B_FIXED_FALSE_CREDIT |
| P2 `b.realizable_5` | Pares estão em a/E002, cujo uso é autorizado. Mini citou só b/E004; Sol citou a e b e preservou o crédito corretamente. | B_FIXED_WRONG_LINK |
| P2 `b.realizable_9` | Pares estão em c/E006, fora da autorização para esta obrigação de b. Mini apoiou somente E004; Sol selecionou E006 e foi bloqueado. | B_FIXED_WRONG_LINK |
| P2 `c.pair_orientations` | Texto diz 2^4=8, não 16. Mini inventou 16; Sol detectou a contradição, confirmada por FORMAL_REFUTED. | B_FIXED_FALSE_CREDIT |
| P2 `c.total`, `c.counting_product` | Texto conclui 192 e 24×8. Ambos retiveram crédito; Sol representou corretamente a contradição que o primeiro julgamento mini ocultou. | B_IMPROVED_UNCERTAINTY (cada obrigação) |
| P2 `c.max_center` | Centro 9 está explícito em c. Sol juntou E004 de b e E006 de c; gate rejeitou a ligação extra. | B_LOST_LEGITIMATE_CREDIT |
| P3 `c.continue_compartments` | Dois ramos legítimos em c. Sol adicionou E002 de a; gate rejeitou, embora os trechos de c já descrevam os ramos. | B_LOST_LEGITIMATE_CREDIT |
| P4 `c.case_3x`, `c.case_other` | Solução usa h+c=18 e h²=c²+144, sem escrever Pitágoras separado para cada hipotenusa. Mini inventou esses passos; Sol não os creditou. Método geral completo mantém nota 20 em ambos. | B_FIXED_FALSE_CREDIT (cada obrigação) |
| P4 `c.case_3x_root`, `c.case_other_root` | As duas raízes estão no método geral. É ambíguo atribuí-las também às vias específicas não desenvolvidas. Dois apoios mini excluídos dos falsos créditos confirmados. | MANUAL_REVIEW_UNCERTAIN (cada obrigação) |
| P5: 58 obrigações | Mini inválido; Sol válido, 15 apoios, sem falso crédito confirmado. Não transformar a falta de resposta válida em ganho semântico do Sol. | MANUAL_REVIEW_UNCERTAIN (cada obrigação) |

Há **86 divergências** pelo critério registrado: decisão, tier, conflito, julgamento, evidence IDs, suficiência ou validade do vínculo. Variações apenas de redação, nomes de method_path e representação equivalente de extrações não constituem nova divergência de decisão; os outputs completos foram preservados. Cada divergência recebe exatamente uma categoria: 6 correções de falso crédito; 2 correções de vínculo; 3 perdas legítimas; 2 melhorias de incerteza; 13 BOTH_CORRECT; 60 MANUAL_REVIEW_UNCERTAIN (58 técnicas + 2 matemáticas). O ganho legítimo em `b.realizable_5` é contado na métrica de recuperação, mas sua classificação única permanece B_FIXED_WRONG_LINK.

A seleção do Sol produziu cinco rejeições `invalid_item_linkage`. Três causaram perdas legítimas; uma bloqueou o vínculo indevido de `b.realizable_9`; em `c.max_sum`, a evidência determinística válida preservou o crédito apesar da rejeição semântica. Essa precedência foi conferida nos registros. Os trechos selecionados são do aluno e as hipóteses/condições/carry-forward estão registradas por obrigação em `manual_review.json`; nenhuma hipótese ausente foi adicionada para conceder crédito. Em P5, não foi inferido carry-forward apenas por compatibilidade numérica.

## Diagnóstico sintético auxiliar

As notas abaixo não são acurácia humana nem ground truth matemático. A nota ausente do mini não foi imputada como zero.

| Caso | Mini | Sol | synthetic_expected_score | Erro absoluto Mini | Erro absoluto Sol |
|---|---:|---:|---:|---:|---:|
| TME2026P1_06 | 20.0 | 18.0 | 18 | 2.0 | 0.0 |
| TME2026P2_01 | 19.0 | 15.0 | 16 | 3.0 | 1.0 |
| TME2026P3_02 | 20.0 | 17.0 | 20 | 0.0 | 3.0 |
| TME2026P4_13 | 20.0 | 20.0 | 20 | 0.0 | 0.0 |
| TME2026P5_09 | indisponível | 9.0 | 10 | indisponível | 1.0 |

| Escopo auxiliar | Mini | Sol |
|---|---:|---:|
| Casos com nota disponível | 4 | 5 |
| Exact | 2/4 | 2/5 |
| ±1 | 2/4 | 4/5 |
| ±2 | 3/4 | 4/5 |
| MAE | 1.25 | 1.00 |
| Bias (score−rótulo) | +1.25 | −1.00 |
| Exact nos quatro pares | 2/4 | 2/4 |
| ±1 nos quatro pares | 2/4 | 3/4 |
| ±2 nos quatro pares | 3/4 | 3/4 |
| MAE nos quatro pares | 1.25 | 1.00 |
| Bias nos quatro pares | +1.25 | −1.00 |

## Custos e falhas

| Execução/custo | Mini | Sol |
|---|---:|---:|
| Chamadas de inferência | 9 | 10 |
| Input tokens | 87468 | 85479 |
| Output tokens | 19591 | 28925 |
| Reasoning tokens (incluídos no output) | 0 | 2085 |
| Cached input tokens | 0 | 0 |
| Cache-write tokens | 0 | 85449 |
| Latência acumulada das etapas semânticas (s) | 181.380 | 304.129 |
| Tempo acumulado de pipeline com auditoria (s) | 243.885 | 372.481 |
| Custo estimado USD | 0.024875 | 0.502933 |
| Erros de validação | 1 | 0 |
| Retries | 0 | 0 |

As duas consultas de disponibilidade são separadas das 19 inferências. Latências somadas por braço, sem paralelismo entre pipelines. Valores estimados pelas tarifas publicadas de [GPT-4o mini](https://developers.openai.com/api/docs/models/gpt-4o-mini) e [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol), consultadas em 2026-11-02: mini USD 0.15/M input e 0.60/M output; Sol USD 2/M input, 2.50/M cache write, 0.10/M cache hit e 10/M output. Cache writes expostos pelo Sol substituem a tarifa input comum para esses tokens; reasoning já integra output. Estimativa total USD **0.527807**, não uma fatura; descontos/ajustes comerciais não foram inferidos.

A única falha de validação ocorreu em P5/A: `missing_duplicate_or_foreign_obligations`. Faltaram `d.cf_adoption`, `d.cf_coherence`, `d.cf_dependency`, `d.sizes`; foram recebidas 54/58 obrigações, sem duplicadas ou estrangeiras. O provedor retornou status completed, mas o validador local rejeitou o conjunto. Nenhuma repetição/correção automática foi feita. O gate de P5/A não chamou a API. Ver `invalid_response_diagnostic.json`.

## Decisão e preservação

**SMOKE_INCONCLUSIVE**: execução pareada incompleta e cobertura legítima menor nos quatro pares válidos. Há evidência local favorável à especificidade do Sol, sem novos falsos créditos confirmados, mas isso não substitui cinco pares válidos nem cumpre manutenção de cobertura útil. O limiar absoluto de 50% registrado antes da execução é apenas um piso; não substitui a exigência comparativa do usuário. Não houve regressão observada de controles: a resposta inválida foi bloqueada, vínculos extras foram barrados e as verificações determinísticas/formais mantiveram sua precedência.

Não houve alteração/reexecução do pipeline, otimização de reasoning, tuning de prompt/schema, inferência adicional ou commit. A verificação final conferiu hashes, proveniência das citações, IDs/modelos por etapa, 19 chamadas, zero retries, igualdade das constantes e integridade dos JSONs. Não foi necessária uma nova bateria de regressão de código porque nenhum código congelado mudou.

Artefatos em `artifacts/evaluations/tme_model_ablation_smoke_live_01/`: `preflight.json`, `cases.json`, `model_a.jsonl`, `model_b.jsonl`, `obligation_comparison.json`, `disagreements.json`, `manual_review.json`, `metrics.json`, `costs.json`, `decision.json`, além dos payloads, ordem, diagnósticos, metadados, hashes e provas. Os scripts locais de consolidação apenas agregam esses resultados; não são o runner experimental e não realizam chamadas.

**HOLDOUT processadas: 0/100. DEV completa 25 NÃO foi executada.**
