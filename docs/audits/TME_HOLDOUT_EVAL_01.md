# TME_HOLDOUT_EVAL_01

**Decisão: HOLDOUT_FAIL.** A configuração não demonstrou generalização suficiente nesta primeira execução: foram **71/100 pipelines válidos**, com **13/20 em P4 e 1/20 em P5**, abaixo dos limites operacionais congelados (80/100 e 14/20 por problema). O esgotamento de créditos da API causou 24 falhas; houve ainda um timeout, uma falha de conexão e três rejeições de contrato. Isso impede uma conclusão de generalização de P5. Nos resultados disponíveis, a revisão identificou subcrédito sistemático por filtros de contexto excessivos e questões residuais que exigem adjudicação humana.

## Congelamento e execução

- Branch: `feat/tme-dual-input`. SHA: `1b3daea41ba4ce31c0cfd35dd07907da3d03669f`.
- `git status --short` vazio antes da abertura; SHA contém `SCOPE_FIX_GO`.
- Modelo exclusivo: `gpt-6.1-sol`; `reasoning.effort=medium`; `store=false`; `max_output_tokens=16000`; timeout 180 s; `max_retries=0`; sem temperature/top_p/top_logprobs.
- Exatamente 100 IDs congelados, 20 por problema, disjuntos das 25 DEV. Uma tentativa por etapa/caso, concorrência 1. As 163 chamadas foram apenas para essas HOLDOUT: 100 da etapa semântica e 63 do gate.
- Pipeline congelado, inclusive checkers/canonicalização/Lean seletivo, reconciliador, policy e PautaEngine. Execução em cópia byte a byte dos 368 arquivos protegidos, com artefatos de execução isolados; nenhuma nota persistida foi alterada. Somente orquestração pré-abertura e arquivos de análise/relatório foram acrescentados ao diretório de avaliação; código do sistema não foi alterado.
- Inputs: revisões aceitas 000001, pela mesma projeção de segmentos validada nas 25 DEV antes da abertura. Após a execução, as 100 fontes coincidiram com o dataset ao normalizar whitespace (38 também literalmente); hashes e revisões estão em `source_manifest.json`. Não houve substituição posterior de inputs.
- Abertura: `2026-11-02T22:06:06.538540+00:00`. Execução: `2026-11-02T22:06:14.743022+00:00` a `2026-11-02T23:47:38.377515+00:00`. Primeiro carregamento dos rótulos: `2026-11-02T23:47:59.227926+00:00`, depois de todas as 100 execuções.
- Integridade final: 368/368 hashes idênticos no repositório e na cópia executada, driver/protocolo inalterados, diff de arquivos rastreados vazio, todos os IDs/obrigações esperados presentes, nenhum rótulo sintético nos payloads. `final_integrity.json` passou. Não foi feito commit.

| Contrato protegido | SHA-256 |
|---|---|
| Prompt SemanticRubricEvaluator | `590349b9a1ea613ed8e930cb275e019cc4e6fa287b6d5c2a5b9eb79cd7aa7d6e` |
| Prompt SemanticSufficiencyGate | `b7cb54d3f32afa16f3f8e112f0c8a07df5d7defd2d140f45b6b72285bcc5173c` |
| Contratos Structured Output | `5e7188c57aefb6d35eaa57adde05ba0cb8cc60e429c28f85045b06daa0b5fd06` |
| Conjunto de arquivos protegidos | `f5110df0d5db453af8d0f9287a1c71dc2140ea15afd121b0c1a09f91296cf4c8` |
| Protocolo de análise/decisão | `770f116fef23ce98f110174a22c2bd130c2a9ad5d5190ef55ac0d6ec0acb4597` |

Os contratos e geradores de schema foram congelados antes da leitura. Schemas concretos dependem dos evidence IDs e, no gate, da resposta da etapa 1; seus hashes foram registrados ao instanciá-los em `prepared_payloads/` e `gate_payloads/`. Todos os hashes/configurações por componente constam de `preflight.json`.

## Métricas principais

| Métrica | P1 | P2 | P3 | P4 | P5 | Total |
|---|---:|---:|---:|---:|---:|---:|
| Casos | 20 | 20 | 20 | 20 | 20 | 100 |
| Pipelines válidos | 20 | 17 | 20 | 13 | 1 | 71 |
| Etapa 1 válida | 20 | 19 | 20 | 16 | 2 | 77 |
| Etapa 2 válida | 18 | 15 | 13 | 10 | 1 | 57 |
| Etapa 2 skipped | 2 | 3 | 7 | 7 | 18 | 37 |
| INVALID_RESPONSE | 0 | 1 | 0 | 2 | 0 | 3 |
| Erros API | 0 | 2 | 0 | 5 | 19 | 26 |
| Score válido | 20 | 17 | 20 | 13 | 1 | 71 |
| Score null | 0 | 3 | 0 | 7 | 19 | 29 |
| Needs review | 17 | 20 | 19 | 20 | 20 | 96 |
| FORMAL_VERIFIED | 7 | 6 | 4 | 8 | 0 | 25 |
| DETERMINISTIC_VERIFIED | 54 | 19 | 5 | 6 | 3 | 87 |
| SEMANTIC_SUPPORTED | 227 | 208 | 78 | 174 | 18 | 705 |
| REFUTED | 4 | 2 | 1 | 0 | 0 | 7 |
| INDETERMINATE | 128 | 162 | 172 | 239 | 81 | 782 |
| TECHNICAL_ERROR | 0 | 62 | 0 | 193 | 1058 | 1313 |
| CONFLICT (flag sobreposta) | 4 | 6 | 0 | 0 | 0 | 10 |
| Obrigações apoiadas | 288 | 234 | 87 | 188 | 21 | 818 |
| Obrigações totais | 420 | 460 | 260 | 620 | 1160 | 2920 |
| Cobertura | 68.57% | 50.87% | 33.46% | 30.32% | 1.81% | 28.01% |
| MAE sintético | 1.15 | 4.76 | 8.10 | 4.00 | 5.00 | 4.55 |

Cobertura principal = obrigações apoiadas / todas as 2.920 obrigações, incluindo caminhos alternativos/condicionais; não é acurácia nem completude de uma solução. Há 818 suportes: 25 formais + 87 determinísticos + 705 semânticos + **1 suporte com tier CONFLICT**. A flag CONFLICT aparece em 10 obrigações e não é uma categoria disjunta a somar aos demais status. `obligation_metrics.json` fornece cobertura e distribuição por cada obrigação, com denominador 20. Cobertura decidida (supported + refuted): 28,25%. Como diagnóstico separado, os 71 pipelines válidos têm 814/1.532 obrigações apoiadas (53,13%); outros quatro suportes nativos sobreviveram em pipelines com score null. O denominador principal e os critérios de decisão não foram alterados.

Etapa 2 skipped: 37 casos, dos quais 23 tinham falha da etapa 1 e 14 tinham etapa 1 válida sem gate externo necessário. Skipped não equivale a uma resposta válida da API; esses 14 podem formar pipeline válido. Os 29 pipelines inválidos tiveram score null e needs_review; nenhum recebeu suporte SEMANTIC_SUPPORTED. Evidência matemática independente pôde permanecer, como a soma formal em P4_22, sem converter a falha em nota numérica. Os 96 needs_review refletem a política congelada, não só falhas técnicas.

## Falhas técnicas e política segura

- **24 erros HTTP 429**, todos com `provider_error.code=credit_balance_exhausted`, `type=insufficient_quota`, exceção `RateLimitError`: 5 em P4 e 19 em P5. Trata-se de saldo esgotado, não de uma conclusão sobre incorreção matemática das soluções. Os erros completos estão preservados em `model_outputs.jsonl`/`provider_events.jsonl` e consolidados em `api_error_details.json`.
- **P2_04:** APITimeoutError na etapa 1 (~180,26 s); sem resposta/usage disponível.
- **P2_16:** APIConnectionError no gate; sem resposta/usage disponível. Não houve retry para determinar transitoriedade.
- **P2_14, P4_03 e P4_05:** gate respondeu JSON completo, mas alterou IDs em decisão positiva: `positive_changed_selected_evidence`. Rejeição integral conforme o contrato, não erro do parser nem truncamento. Nenhuma resposta disponível foi marcada incomplete; nenhum limite de tokens foi atingido nas respostas disponíveis.

| Caso | Obrigação | IDs esperados | IDs recebidos |
|---|---|---|---|
| P2_14 | c.max_center / c.max_sum | E014,E015,E019,E021 | E021 |
| P4_03 | b.ap | E002,E004 | E004 |
| P4_05 | a.qr / a.rc | E001,E002 | E001 |

Respostas, schemas, token usage e motivos de rejeição estão em `validity.json` e `failure_details.json`; `api_error_details.json` refina as classificações UNKNOWN deste último com os códigos de quota preservados. Não houve retry seletivo, alteração de timeout, relaxamento de schema, outro modelo ou chamada de diagnóstico externa.

## Diagnóstico sintético auxiliar

**comparação contra rótulo sintético, não acurácia humana**

Somente as 71 notas numéricas entram nos cálculos; 29 null são excluídas, nunca convertidas em zero. MAE **4.5493**, bias **-4.3239**; exact **27/71**, erro ≤1 **29/71**, erro ≤2 **37/71**. P5 tem apenas uma nota numérica: suas métricas não permitem estimar generalização. A seleção por disponibilidade também limita a comparação global.

| Diagnóstico sintético | P1 | P2 | P3 | P4 | P5 | Total |
|---|---:|---:|---:|---:|---:|---:|
| Notas comparadas | 20 | 17 | 20 | 13 | 1 | 71 |
| Bias | -0.95 | -4.76 | -7.50 | -4.00 | -5.00 | -4.32 |
| Exact | 80.00% | 17.65% | 20.00% | 30.77% | 0.00% | 38.03% |
| Erro ≤1 | 80.00% | 29.41% | 20.00% | 30.77% | 0.00% | 40.85% |
| Erro ≤2 | 90.00% | 41.18% | 30.00% | 46.15% | 0.00% | 52.11% |

Distribuição do erro (ConfIA − rótulo): `{"-20.0": 3, "-19.0": 1, "-18.0": 2, "-17.0": 1, "-14.0": 2, "-10.0": 2, "-9.0": 1, "-8.0": 5, "-6.0": 4, "-5.0": 4, "-4.0": 4, "-3.0": 4, "-2.0": 6, "-1.0": 2, "0.0": 27, "2.0": 2, "4.0": 1}`. Valores individuais e métricas por problema estão em `synthetic_score_metrics.json`. Diferença contra rótulo não foi usada, isoladamente, para declarar falso crédito ou correção matemática.

## Revisão local e rastreabilidade

A amostra determinística contém **26 casos**: maior/menor erro, primeiro null/needs_review, maior fração semântica e maior quantidade de evidências formais/determinísticas por problema, desempate por ID, mais flags de rastreabilidade. Distribuição: P1 5, P2 7, P3 5, P4 4, P5 5. Foram revisados adicionalmente 59 casos, total **85 revisões locais**, todas antes do carregamento dos rótulos. Foram lidos solução, obrigações, IDs/textos, sufficiency, vínculos e resultado da pauta. `manual_review_sample.json` contém a amostra, notas suplementares e addenda; o pacote mascarado não inclui notas sintéticas nem motivos de seleção.

Treze notas iniciais não têm timestamp individual; a anterioridade de todo o arquivo de notas ao primeiro carregamento dos rótulos foi conferida pelo horário de sua última gravação e pela sequência registrada de execução, conforme `manual_review_sample.json`.

Essa revisão foi realizada por Codex a partir das fontes e requisitos, sem novas chamadas ao modelo avaliador. **Não é uma adjudicação humana independente**, nem um estudo de acurácia humana.

- **Origem:** 1.398 evidence units, 2.246 bindings de unidades selecionadas e 207 bindings de fatos nativos verificados localmente; nenhuma divergência mecânica de origem/texto/offset nem ID de outro estudante detectada.
- **Referências internas:** 16 ocorrências inspecionadas; 15 preservam o contexto e uma, “Em (c)” em P4_10, é cabeçalho real. Nenhuma mudança falsa de seção confirmada nessas ocorrências. O detector deixa 36 soluções totalmente sem seção atribuída; isso é limitação de escopo, não prova automática de erro. Em P5_12/P5_23, `Item (a)` etc. não são reconhecidos e o contexto permanece None; ambos falharam na API, portanto o linkage resultante não pôde ser avaliado.
- **Crédito indevido/itens vizinhos:** nenhum caso confirmado após as addenda da revisão. Há questões não resolvidas em textos sem escopo atribuído, incluindo provas usadas em partes adjacentes em P2_13/P2_23; não se pode afirmar rastreabilidade perfeita. Falhas de API não contam como evidência de segurança do julgamento.
- **P2_19:** o aluno usa centro 5/máximo 15 e chega a 384 por 24×16. O gate contradiz `c.counting_product`, mas prova aritmética independente prevalece e o reconciliador marca supported/CONFLICT. A pauta separa 3 pontos de máximo/pares de 5 pontos de técnica de contagem; não concedeu os 3 pontos errados. A revisão inicial de excesso de escopo foi refinada após ler essa separação: os 5 pontos podem ser crédito parcial intencional, não se confirmou falso crédito. A prova Lean de 24×16 não prova maximalidade; é necessária adjudicação humana. Addendum preservado, sem mudar resultado.
- **P3_19:** a razão isolada 2/6 foi aceita como identificação de duas brancas entre seis. É interpretação plausível, mas sua suficiência para os pontos de contagem requer adjudicação humana; não foi declarada errada apenas por concisão.
- **Carry-forward:** zero `conditional_on` e zero `carry_forward_applied`. Não houve aplicação indevida observada, mas o conjunto executado não exercitou positivamente essa funcionalidade.

## Limitações matemáticas observadas

1. **Veto lexical excessivo recorrente.** “Segundo compartimento” (P3_01/P3_04/P3_06/P3_14/P3_16/P3_23/P3_24/P3_25) e “Segundo caso” (P4_04/P4_08) podem disparar a regra de atribuição `segundo + palavra`. Em P3_16 e P3_24, soluções matematicamente completas receberam 0; em P4_04/P4_08 o item c completo recebeu 0. Esse achado vem da leitura da prova, não do rótulo sintético.
2. **Contexto global/revisões posteriores.** Cabeçalhos não reconhecidos, expressões de dúvida/rejeição ou “Hipótese” em análise legítima de casos podem bloquear itens anteriores corretos: P2_05/P2_17, P3_10/P3_18 e P4_14. Não é um novo crédito falso, mas perda material de utilidade.
3. **Fronteiras compactas e seleção excessiva.** Em P1_16/P3_18, marcadores concatenados não abrem item; em P3_08/P3_15, IDs de outro item selecionados em excesso bloqueiam `c.continue_compartments`. Recusas são conservadoras, com perda de crédito válido.
4. **Suficiência mais exigente que a etapa.** Em P2, por vezes exige realizabilidade para centros integrais embora a pauta tenha etapa separada. Em P4_02/P4_10/P4_17, uma exclusão correta de 12 por contradição é tratada como não afirmada. Foram observadas diferenças de rigor entre provas parciais semelhantes. Nada foi corrigido nesta avaliação.

## Custos e latência

- Chamadas: **163**, modelo único; **0 retries**. Usage disponível em 137 chamadas; ausente em 26 falhas de API.
- Input: **1.084.694** tokens, sendo 14.129 cached e 1.070.154 cache-write; output: **342.925**; reasoning: **23.570**, já incluído em output.
- Estimativa do usage conhecido: **US$ 6.106870**. Tarifas históricas congeladas do DEV: input US$ 2/M, cached US$ 0,10/M, cache-write US$ 2,50/M, output US$ 10/M. Sem consulta externa de preço; não representa fatura confirmada. Usage ausente é desconhecido, não declarado gratuito.
- Latência somada dos providers: **3658.84s**; mediana **19.67s**; máximo **180.26s**. Soma dos pipelines: **4011.87s**. Tempo civil início/fim: **6083.63s** (101,39 min). As medidas usam relógios distintos; não se atribui a diferença a uma causa não instrumentada.

## Decisão e encerramento

**HOLDOUT_FAIL**, pelos critérios registrados em `analysis_protocol.json` antes da abertura: 71 < 80 globalmente; P4: 13 < 14; P5: 1 < 14. Não foi necessário redefinir critério com base nos rótulos. Não houve violação confirmada de origem de estudante ou crédito semântico derivado de provider inválido; isso não elimina as limitações de cobertura, os casos não avaliáveis e os conflitos pendentes.

Manter shadow e revisão humana obrigatória. Esta execução não autoriza congelamento para uso autônomo nem promoção. A avaliação fica formalmente encerrada; não foram ajustados/reexecutados casos, criadas fixtures de desenvolvimento a partir da HOLDOUT ou alteradas notas persistidas. Uma eventual avaliação futura exigirá desenho e autorização próprios; não foi iniciada nesta tarefa.

Artefatos em `artifacts/evaluations/tme_holdout_eval_01/`, com manifesto SHA-256 e proteção local de escrita no fechamento. Essa proteção é um selo local verificável, não armazenamento WORM externo. Outputs requeridos: `preflight.json`, `holdout_manifest.json`, `model_outputs.jsonl`, `validity.json`, `obligation_metrics.json`, `metrics_by_problem.json`, `synthetic_score_metrics.json`, `manual_review_sample.json`, `traceability_findings.json`, `costs.json`, `decision.json`.

**HOLDOUT processadas: 100/100** (100 tentativas únicas; 71 pipelines válidos).

**Nenhuma alteração do sistema foi realizada após a abertura da HOLDOUT.**
