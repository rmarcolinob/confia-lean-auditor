# TME_MODEL_ABLATION_DEV25_LIVE_01

Data: 2026-11-02. **MODEL_ABLATION_GO**.

Sol mostrou ganho material e consistente de especificidade, preservando cobertura útil: nos 18 pares válidos, falsos créditos 36→0, vínculos incorretos 9→0, falsas atribuições 81→0 e apoios legítimos 235→259. Nas 25 tentativas, apoios legítimos 266→334 e pipelines válidos 20→22. Há um vínculo incorreto confirmado do Sol em P5_02 e 14 apoios ambíguos; o GO é experimental e não afirma ausência universal de erros. O ganho sustenta-se sem usar notas sintéticas como ground truth.

**HOLDOUT processadas: 0/100.** Não houve mudança de notas persistidas nem commit. A execução terminou nas 25 DEV; a decisão não abre HOLDOUT nem ativa o modelo no produto.

## Preflight e execução congelada

A = `gpt-4o-mini-2024-07-18`; B = `gpt-6.1-sol`.

- Branch: `feat/tme-dual-input`.
- SHA completo: `ea3ae12b0c62f7f266a1cd91da795e32dc43f326`.
- Working tree limpa antes das inferências.
- SHA do smoke: `1284a06a745ddd59901c507ffe8bbe37e4266c4e`; entre os SHAs mudou apenas o relatório do smoke.
- Os 233 arquivos protegidos de código/prompt/schema/regras/pautas/referências permaneceram idênticos ao smoke; nenhuma adaptação durante a execução.
- Lista DEV congelada com 25 IDs únicos, cinco por problema; allowlist SHA256 `d6ae59f0a2d766f9c7541b2d8341fb6aa56ee8c1fdf55200131c842087d1d140` e pacote de fontes `a3432c6aa1fff0f68018e609989a26b23b7b6f5d8e86e5c586801f2445d0fe79`.
- Nova execução dos 25 casos nos dois braços; nenhum output do smoke ou de um braço foi usado como input do outro.
- Ordem determinística: casos ordenados por ID, A→B em cada caso; duas etapas no mesmo modelo por braço.
- A manteve temperature=0. B manteve reasoning.effort=medium, sem temperature/top_p/top_logprobs ou substituto de sampling. Ambos com store=false, max_output_tokens=16000, timeout de 180 s e max_retries=0.
- Autorização explícita do usuário ampliou a DEV apesar do smoke inconclusivo; não foi tratada como aprovação prévia de modelo.

> Os parâmetros de geração não são literalmente idênticos porque os modelos possuem contratos de API diferentes. Cada braço utiliza a configuração válida previamente especificada, mantendo constantes todas as camadas semânticas e matemáticas do experimento.

Solução, problem_id, referência, obligations, evidence units, prompts, contrato/schema e geradores, context gates, sufficiency rules, canonicalização, checkers, Lean, EvidenceReconciler, HybridEvidencePolicy, PautaEngine e scoring ficaram congelados. Os schemas da etapa 1 são iguais entre braços. Na etapa 2, os enums/IDs concretos dependem dos candidatos novos de cada braço: o contrato e gerador são idênticos, mas os requests derivados não são necessariamente byte a byte iguais. Essa limitação constava no preflight congelado; não houve edição de schemas.

Execução em cópia byte a byte sob `artifacts/evaluations/tme_model_ablation_dev25_live_01/execution/`, com cache Lean existente e provas novas dentro desse diretório. Não foram modificados código do produto, submissões, transcrições, avaliações oficiais ou AuditRuns existentes. Nenhum leitor de HOLDOUT foi usado.

## Protocolo de revisão

Oito artefatos de anotações/revisões anteriores foram copiados e tiveram hashes congelados antes das inferências. Julgamentos manuais explícitos anteriores foram preservados, com prioridade da revisão mais recente do smoke. Achados de vínculo específico só são aplicáveis quando a evidência deficiente reaparece; não condenam outra seleção correta.

A revisão de fonte dos 730 pares solução–obrigação foi registrada durante a execução, antes de consultar qualquer output matemático novo, e seu hash foi travado. Rótulos diagnósticos de “aparentemente satisfeita” são preservados separadamente e não são automaticamente verdade matemática. Ambiguidades de equivalência/forma são registradas como incerteza sem sobrescrever a anotação original.

Os novos trechos/julgamentos foram avaliados em pacotes `solution + obligation + evidence`, com A/B e resultado final de reconciliação ocultos. Vereditos foram registrados antes de abrir o mapa de identidades. A identidade pode ser inferida por estilo ou por falhas operacionais acompanhadas; o revisor também conhece o smoke anterior. Portanto, é revisão local do Codex com mascaramento parcial, **não estudo humano independente/cego**. Notas sintéticas só foram lidas após a revisão matemática.

Contagem de falso crédito: obrigação sem requisito escrito/válido que terminou apoiada; inclui vias alternativas sem necessariamente aumentar pontos. Vínculo incorreto: conteúdo legítimo existente na solução sem suporte nos trechos selecionados/autorizados; uma auditoria primária independente válida pode preservar apoio correto. Falsa atribuição: conteúdo inventado/alterado em output validado, mesmo se bloqueado depois; respostas brutas inválidas são excluídas. São métricas sobrepostas, não parcelas somáveis. Apoios ambíguos são separados dos legítimos e dos falsos confirmados: os erros confirmados são limites inferiores.

“Créditos legítimos perdidos” compara com o outro braço: apoio confirmado no outro, ausente ou seguramente incorreto neste. Um apoio apenas ambíguo não é automaticamente contado como perda. No conjunto completo, perdas incluem falhas de confiabilidade; a tabela pareada separa a qualidade dos pipelines integralmente válidos.

## Comparação principal: 25 tentativas por modelo

Foram executados os 25 casos em cada braço. Na tabela, “DEV concluídas” conta os casos em que todas as etapas necessárias produziram outputs válidos; skips locais sem candidatos são permitidos, mas falhas anteriores não contam como conclusão válida.

| Métrica | Mini | Sol | Δ B−A |
|---|---:|---:|---:|
| DEV concluídas | 20 | 22 | +2 |
| Etapa 1 válida | 22 | 25 | +3 |
| Etapa 2 válida | 19 | 21 | +2 |
| Invalid responses | 5 | 2 | -3 |
| Erros API/transporte | 0 | 1 | +1 |
| Etapas puladas | 4 | 1 | -3 |
| Obrigações apoiadas | 329 | 349 | +20 |
| Apoios legítimos confirmados | 266 | 334 | +68 |
| Apoios ambíguos | 14 | 14 | +0 |
| Falsos créditos confirmados | 39 | 0 | -39 |
| Vínculos incorretos finais | 10 | 1 | -9 |
| Falsas atribuições confirmadas | 95 | 0 | -95 |
| Créditos legítimos perdidos vs outro braço | 103 | 36 | -67 |
| FORMAL_VERIFIED | 7 | 15 | +8 |
| DETERMINISTIC_VERIFIED | 30 | 45 | +15 |
| SEMANTIC_SUPPORTED | 292 | 288 | -4 |
| REFUTED | 2 | 5 | +3 |
| CONFLICT | 1 | 3 | +2 |
| INDETERMINATE | 184 | 315 | +131 |
| TECHNICAL_ERROR | 215 | 61 | -154 |
| needs_review: casos | 16 | 25 | +9 |

Erros presentes em B e ausentes em A, nos 25 casos: falsos créditos 0; vínculos incorretos 1; falsas atribuições 0. No subconjunto pareado válido: 0, 0 e 0, respectivamente. Fora do subconjunto pareado, uma ausência pode decorrer de falha, portanto não comprova regressão semântica.

Obrigações com fonte positiva na revisão fixada: 452. Sem apoio legítimo confirmado nesse conjunto: mini 186, Sol 118. Isso inclui perdas compartilhadas e ambiguidades; não equivale à perda relativa ao outro braço.

Há 730 obrigações no escopo e 409 aparentemente satisfeitas no diagnóstico congelado. Cobertura desse conjunto histórico: mini 255/409; Sol 304/409. Esse índice não substitui revisão de especificidade, pois pode incluir apoios inseguros. Primeiros julgamentos satisfeitos: mini 525, Sol 468.

## Comparação com denominador pareado

18 casos possuem pipelines válidos nos dois braços. Casos: TME2026P1_06, TME2026P1_13, TME2026P1_15, TME2026P1_17, TME2026P2_01, TME2026P2_08, TME2026P2_15, TME2026P2_18, TME2026P3_02, TME2026P3_03, TME2026P3_07, TME2026P3_13, TME2026P3_22, TME2026P4_13, TME2026P4_16, TME2026P4_21, TME2026P4_23, TME2026P5_22.

| Métrica | Mini | Sol | Δ B−A |
|---|---:|---:|---:|
| DEV concluídas | 18 | 18 | +0 |
| Etapa 1 válida | 18 | 18 | +0 |
| Etapa 2 válida | 17 | 17 | +0 |
| Invalid responses | 0 | 0 | +0 |
| Erros API/transporte | 0 | 0 | +0 |
| Etapas puladas | 1 | 1 | +0 |
| Obrigações apoiadas | 291 | 265 | -26 |
| Apoios legítimos confirmados | 235 | 259 | +24 |
| Apoios ambíguos | 11 | 6 | -5 |
| Falsos créditos confirmados | 36 | 0 | -36 |
| Vínculos incorretos finais | 9 | 0 | -9 |
| Falsas atribuições confirmadas | 81 | 0 | -81 |
| Créditos legítimos perdidos vs outro braço | 34 | 11 | -23 |
| FORMAL_VERIFIED | 7 | 11 | +4 |
| DETERMINISTIC_VERIFIED | 23 | 32 | +9 |
| SEMANTIC_SUPPORTED | 261 | 221 | -40 |
| REFUTED | 0 | 3 | +3 |
| CONFLICT | 0 | 2 | +2 |
| INDETERMINATE | 132 | 155 | +23 |
| TECHNICAL_ERROR | 0 | 0 | +0 |
| needs_review: casos | 9 | 18 | +9 |

As falhas não foram imputadas como julgamentos matemáticos negativos nem escondidas no denominador. `needs_review` é o estado do PautaEngine shadow, separado desta revisão manual.

## Resultados por problema

| Problema | Válidas A/B | Apoios legítimos A/B | Falsos créditos A/B | Vínculos incorretos A/B | Falsas atribuições A/B | Apoios ambíguos A/B |
|---|---:|---:|---:|---:|---:|---:|
| TME2026P1 | 5/4 | 78/63 | 6/0 | 3/0 | 9/0 | 7/3 |
| TME2026P2 | 4/4 | 74/76 | 10/0 | 6/0 | 22/0 | 1/0 |
| TME2026P3 | 5/5 | 34/32 | 4/0 | 0/0 | 8/0 | 0/0 |
| TME2026P4 | 5/4 | 63/68 | 8/0 | 1/0 | 27/0 | 5/1 |
| TME2026P5 | 1/5 | 17/95 | 11/0 | 0/1 | 29/0 | 1/10 |


Os detalhes por tier, validade, incerteza e subconjunto pareado de P1–P5 estão em `metrics_by_problem.json`.

## Divergências

- Nos 18 pares válidos, Sol preservou 224 dos 235 apoios legítimos do Mini (95,3%), perdeu 11 e recuperou 34; um apoio adicional veio de uma situação ambígua no Mini, totalizando 259. A classificação única pode priorizar a correção de outro erro, por isso as classes de divergência não substituem as contagens independentes.
- P1 e P2: Sol evita completar condições, realizações de tabuleiro e contagens ausentes; exemplos incluem não trocar 192 por 384 e não inventar realizações para centros 1, 5, 9. P1 tem 63→60 apoios legítimos nos quatro pares válidos; P2 tem 73→75.
- P3: falsos créditos 4→0, com apoios legítimos 34→32. P3_13 perde cobertura nos dois braços: todas as candidatas ficam bloqueadas pelo contexto local, embora a fonte tenha raciocínio válido. Em P3_07, um argumento corrigido é bloqueado como não assertivo; isso permanece registrado como perda do Sol.
- P4: nos quatro pares válidos, apoios legítimos 51→68 e falsos créditos 5→0. Sol não inventa o segundo caso/raiz em P4_16 nem aceita a exclusão algébrica inválida de 12 em P4_19. Porém, a exclusão válida por hipótese em P4_13 é bloqueada como nonasserted_context; a resposta de gate de P4_19 também é estruturalmente inválida.
- P5: Mini só tem um dos cinco pipelines inteiramente válido, Sol tem cinco. Em P5_22, Mini apoia 11 requisitos sem suporte suficiente; Sol não mantém esses falsos créditos. O gate do Sol também rejeita o produto final correto de P5_22 por causa do argumento errado, gerando conflito e uma perda de apoio legítimo.
- Único vínculo incorreto final confirmado do Sol: P5_02/c.four_product seleciona a igualdade de produtos em (d), por meio de E016 com item_hint contaminado pela referência textual a (c). A igualdade existe em (c), mas em E014 não selecionado. Não há invenção matemática nesse caso, mas há erro de proveniência; não foi corrigido ou escondido. Mini teve gate inválido nesse caso, de modo que a classificação do par é MANUAL_REVIEW_UNCERTAIN, e o erro de B permanece em campo independente.
- Confiabilidade: Mini tem 5 INVALID_RESPONSE, três na etapa 1 e dois no gate; Sol tem 2 INVALID_RESPONSE no gate e 1 timeout. Nenhuma chamada foi repetida. A escolha não supõe confiabilidade perfeita.
- Incerteza preservada: 14 apoios ambíguos em cada braço. Se todos os 14 apoios ambíguos de Sol fossem indevidos, haveria 14 falsos créditos potenciais, ainda abaixo dos 39 confirmados do Mini; isso é apenas análise de sensibilidade, não relabelagem. Seis apoios de Sol têm conflito com rótulo diagnóstico negativo, explicitado sem alterar a fonte: inversão expandida de P1_15, duas comparações em P5_18, duas em P5_24 e a soma 3+1=4 em P5_24.
- MAE sintético não decide o resultado: no subconjunto pareado, Mini 3,39 e Sol 3,94. Sol atribui notas menores em vários casos, mas reduz fortemente apoios inseguros e conserva cobertura matemática útil.

| Classe | Quantidade |
|---|---:|
| BOTH_CORRECT | 214 |
| B_FIXED_FALSE_ATTRIBUTION | 40 |
| B_FIXED_FALSE_CREDIT | 36 |
| B_FIXED_WRONG_LINK | 9 |
| B_IMPROVED_UNCERTAINTY | 13 |
| B_LOST_LEGITIMATE_CREDIT | 11 |
| B_RECOVERED_LEGITIMATE_CREDIT | 28 |
| MANUAL_REVIEW_UNCERTAIN | 336 |

Cada divergência relevante tem uma classificação única em `disagreements.json`. O comparador considera julgamento, evidence IDs/extrações, suficiência, vínculo, decisão/tier, conflito e falsas atribuições revisadas; diferenças só de redação não são tratadas como ganho. Casos com pipeline inválido ou ambiguidade relevante usam MANUAL_REVIEW_UNCERTAIN, sem transformar erro estrutural em vitória semântica. Campos independentes preservam eventuais erros simultâneos que uma categoria única não consegue expressar.

## Validade estrutural e falhas

| Caso | Braço | Etapa | Classe | Motivo |
|---|---|---|---|---|
| TME2026P2_10 | A | sufficiency | INVALID_RESPONSE | positive_changed_selected_evidence |
| TME2026P5_02 | A | sufficiency | INVALID_RESPONSE | 1 validation error for SufficiencyDecision   Value error, unsupported_sufficiency [type=value_error, input_value={'obligation_id': 'a.prod...ivamente desenvolvido.'}, input_type=dict]     For further information visit https://errors.pydantic.dev/2.13/v/value_error |
| TME2026P5_09 | A | semantic | INVALID_RESPONSE | missing_duplicate_or_foreign_obligations |
| TME2026P5_18 | A | semantic | INVALID_RESPONSE | missing_duplicate_or_foreign_obligations |
| TME2026P5_24 | A | semantic | INVALID_RESPONSE | 1 validation error for JudgmentResponse judgments.3   Value error, extraction_without_selected_source [type=value_error, input_value={'obligation_id': 'a.stru...009', 'E010', 'E011']}]}, input_type=dict]     For further information visit https://errors.pydantic.dev/2.13/v/value_error |
| TME2026P1_12 | B | sufficiency | INVALID_RESPONSE | positive_changed_selected_evidence |
| TME2026P2_10 | B | sufficiency | API_ERROR | APITimeoutError |
| TME2026P4_19 | B | sufficiency | INVALID_RESPONSE | positive_changed_selected_evidence |

Todas as falhas foram mantidas, sem retries seletivos, reparo silencioso ou repetição. INVALID_RESPONSE inclui violação do contrato local de obrigações/evidence IDs, mesmo quando a API retorna JSON e status completed. SKIPPED não é uma resposta inválida: pode ocorrer porque a etapa anterior falhou ou não há candidatos. A mesma política congelada foi aplicada aos dois modelos. A proveniência e os detalhes estão em `validity.json`; as respostas brutas foram preservadas.

## Custos

| Custo/execução | Mini | Sol |
|---|---:|---:|
| Chamadas | 46 | 49 |
| Input tokens | 423236 | 380397 |
| Output tokens | 101663 | 144654 |
| Reasoning tokens (já no output) | 0 | 11795 |
| Cached input | 0 | 29573 |
| Cache writes | 0 | 350680 |
| Latência acumulada API/validação (s) | 1029.680 | 1611.821 |
| Tempo acumulado de pipeline com auditoria (s) | 1204.845 | 1902.268 |
| USD estimado | 0.124483 | 2.326485 |
| Tentativas sem usage informado | 0 | 1 |
| Retries | 0 | 0 |

Total: **95 chamadas de inferência tentadas**, subtotal de uso conhecido em USD estimado **2.450968**. Sem retries e sem consultas adicionais de disponibilidade neste run. Estimativa pelas tarifas publicadas de [GPT-4o mini](https://developers.openai.com/api/docs/models/gpt-4o-mini) e [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol): mini input 0.15/output 0.60 USD por milhão; Sol input 2/cache-write 2.50/cache-hit 0.10/output 10. Cache writes substituem input comum para esses tokens, e reasoning já integra output. Uma chamada de Sol terminou em timeout sem usage informado e não está precificada nesse subtotal. Não é fatura; uso não informado e ajustes comerciais não são inferidos como gratuitos. Latências são acumuladas; as medições por chamada estão em `costs.json`.

## Comparação contra rótulo sintético, não acurácia humana

| Escopo/modelo | n | MAE | Bias | Exact | ±1 | ±2 |
|---|---:|---:|---:|---:|---:|---:|
| all_available/A | 20 | 3.2000 | -1.5000 | 6/20 | 8/20 | 12/20 |
| all_available/B | 22 | 3.8636 | -3.7727 | 4/22 | 5/22 | 10/22 |
| paired_valid/A | 18 | 3.3889 | -1.5000 | 5/18 | 7/18 | 11/18 |
| paired_valid/B | 18 | 3.9444 | -3.9444 | 4/18 | 4/18 | 8/18 |


| Caso | Mini | Sol | Rótulo sintético | Erro absoluto Mini/Sol |
|---|---:|---:|---:|---:|
| TME2026P1_06 | 20.0 | 18.0 | 18 | 2.0/0.0 |
| TME2026P1_12 | 16.0 | indisponível | 19 | 3.0/indisponível |
| TME2026P1_13 | 20.0 | 17.0 | 17 | 3.0/0.0 |
| TME2026P1_15 | 18.0 | 17.0 | 20 | 2.0/3.0 |
| TME2026P1_17 | 20.0 | 15.0 | 20 | 0.0/5.0 |
| TME2026P2_01 | 20.0 | 13.0 | 16 | 4.0/3.0 |
| TME2026P2_08 | 20.0 | 17.0 | 19 | 1.0/2.0 |
| TME2026P2_10 | indisponível | indisponível | 20 | indisponível/indisponível |
| TME2026P2_15 | 20.0 | 16.0 | 16 | 4.0/0.0 |
| TME2026P2_18 | 20.0 | 19.0 | 19 | 1.0/0.0 |
| TME2026P3_02 | 20.0 | 17.0 | 20 | 0.0/3.0 |
| TME2026P3_03 | 4.0 | 4.0 | 7 | 3.0/3.0 |
| TME2026P3_07 | 20.0 | 16.0 | 18 | 2.0/2.0 |
| TME2026P3_13 | 0.0 | 0.0 | 20 | 20.0/20.0 |
| TME2026P3_22 | 20.0 | 14.0 | 20 | 0.0/6.0 |
| TME2026P4_13 | 20.0 | 18.0 | 20 | 0.0/2.0 |
| TME2026P4_16 | 12.0 | 10.0 | 14 | 2.0/4.0 |
| TME2026P4_19 | 18.0 | indisponível | 18 | 0.0/indisponível |
| TME2026P4_21 | 6.0 | 4.0 | 6 | 0.0/2.0 |
| TME2026P4_23 | 12.0 | 12.0 | 20 | 8.0/8.0 |
| TME2026P5_02 | indisponível | 11.0 | 17 | indisponível/6.0 |
| TME2026P5_09 | indisponível | 11.0 | 10 | indisponível/1.0 |
| TME2026P5_18 | indisponível | 10.0 | 15 | indisponível/5.0 |
| TME2026P5_22 | 9.0 | 10.0 | 18 | 9.0/8.0 |
| TME2026P5_24 | indisponível | 7.0 | 9 | indisponível/2.0 |


Score ausente permanece ausente; não foi imputado zero. A decisão principal usa especificidade, vínculos, atribuição, confiabilidade e cobertura útil, sem exigir mais pontos para o Sol e sem decidir por MAE.

## Decisão

**MODEL_ABLATION_GO**. Sol mostrou ganho material e consistente de especificidade, preservando cobertura útil: nos 18 pares válidos, falsos créditos 36→0, vínculos incorretos 9→0, falsas atribuições 81→0 e apoios legítimos 235→259. Nas 25 tentativas, apoios legítimos 266→334 e pipelines válidos 20→22. Há um vínculo incorreto confirmado do Sol em P5_02 e 14 apoios ambíguos; o GO é experimental e não afirma ausência universal de erros. O ganho sustenta-se sem usar notas sintéticas como ground truth.

Limitações: 25 DEV sintéticas, uma execução por caso/modelo, revisão local parcialmente mascarada e apoios ambíguos explicitados. O resultado não estima acurácia humana nem comprova desempenho fora desta DEV. Nenhuma abertura de HOLDOUT foi feita ou inferida da decisão.

Os artefatos requeridos estão em `artifacts/evaluations/tme_model_ablation_dev25_live_01/`: preflight, 25 fontes, JSONL brutos, validade, 730 comparações, divergências, revisão, métricas globais/P1–P5, diagnóstico sintético, custos e decisão, com snapshots/hash das anotações, pacotes mascarados e verificação final. Scripts de consolidação local não fazem chamadas nem alteram o runner.

**HOLDOUT processadas: 0/100. Sem commit. Notas persistidas não modificadas.**
