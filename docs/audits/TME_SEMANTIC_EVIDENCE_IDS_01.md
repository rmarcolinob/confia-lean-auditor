# TME_SEMANTIC_EVIDENCE_IDS_01

Data: 2026-11-02 (America/Fortaleza).

**Decisão: NO_GO. ACTIVE DEV não executado. HOLDOUT processadas: 0/100.**

A seleção por IDs eliminou as falhas de offsets produzidos pelo modelo e aumentou a validade de respostas de 13/25 para 25/25. Entretanto, o ganho não chegou à verificação matemática: foram produzidos quatro FactResults novos, sendo três verified e um unverified, contra seis verified no live anterior. O gate congelado exigia aumento acima de seis; a execução parou no shadow, sem modificar código ou prompt após os resultados.

## Implementação e congelamento

Base: `699b7421308ec3c6f9c5abaabdae8e1cff75dfb4`, branch `feat/tme-dual-input`. O código novo não foi commitado. Foram adicionados cinco arquivos de código/testes; nenhum arquivo preexistente de implementação foi alterado. O caminho padrão da aplicação continua intacto.

- `evidence_units.py`: `SemanticEvidenceUnit` com evidence_id, exact_text, source_start, source_end, unit_kind e context_ids.
- `evidence_id_semantic.py`: schema `ObligationEvidenceSelection`, provider, resolução de IDs e projeção com gates existentes.
- `evidence_id_experiment.py`: rota shadow separada, reutilizando verificação/bridge e preservando o baseline.
- `evaluate_tme_evidence_ids.py`: preparação, congelamento, live e ativação sujeita a gate.
- `test_evidence_id_semantic.py`: 53 testes novos.

O freeze foi registrado em `2026-11-02T14:40:36.678937+00:00`; a primeira resposta persistida é posterior, em `2026-11-02T14:41:16.412250+00:00`. Hash do manifesto congelado: `394a1c81cb14fe0ad45a85cfc72ccf84b1883737f61bc63d6dc0aad190154563`. O manifesto inclui hashes de código, testes, prompt, schema, catálogo, unidades, payloads, schemas por DEV, cache primário e referências anteriores. Todos foram conferidos no encerramento. Nenhum commit foi criado.

Foram usados exclusivamente os mesmos 25 IDs DEV já congelados, registrados em `preflight.json`. Modelo configurado `gpt-4o-mini`, snapshot reportado `gpt-4o-mini-2024-07-18`, temperatura 0, `store=false`, timeout 180 segundos, saída máxima 16.000 tokens e **zero retries**. Foram feitas exatamente 25 chamadas externas. A API key foi registrada somente como booleano. Nenhum secret foi impresso. Nenhum texto ou resultado individual HOLDOUT foi aberto.

## Unidades, contexto e múltiplas evidências

As 25 soluções produziram **335 unidades determinísticas**, com IDs E001, E002, … estáveis para o mesmo texto. A unidade usa uma linha física completa; rótulos de item no início da linha são separados. Os tipos distinguem sentença, cláusula/rótulo, bloco matemático, item de lista e parágrafo curto. Não há divisão por vírgula ou recorte que isole `x=5` de “Tentei … mas está errado”. A construção preserva todos os caracteres não brancos, Unicode e offsets originais; não normaliza nem trunca a fonte.

`context_ids` liga linhas do mesmo parágrafo. O modelo recebe IDs, textos exatos, tipos e links de contexto, além de enunciado e obrigações sem pontos. Os offsets ficam exclusivamente no engine. O output não permite source_start, source_end, source_text, supported, refuted, points, score, award ou deny.

Para múltiplos IDs, o engine guarda **todos os trechos e seus spans**. A projeção para o record legado usa o intervalo original do primeiro ao último trecho, incluindo texto intermediário. Esse intervalo não é uma concatenação fabricada. O payload precisa também passar pela validação de representação usando somente os trechos selecionados: contexto intermediário não pode fornecer matemática que o modelo deixou de selecionar.

IDs inválidos, duplicados, ausência incoerente ou pares obrigação/tipo/assunto inválidos continuam rejeitando a resposta inteira. Um ID válido só prova que o trecho existe naquela solução. Não prova pertinência à obrigação, atribuição positiva, correção matemática ou direito a crédito.

Os gates existentes continuam obrigatórios. Uma restrição adicional conservadora examina o item aceito para impedir seleção parcial em torno de negação explícita, hipótese, tentativa rejeitada, correção posterior, citação e conflitos cobertos. Ela pode rejeitar um item ambíguo inteiro. A resolução de autocorreções não foi delegada ao modelo. Checkers e reextração revalidam a projeção, e os tipos/semântica de FactResult não mudaram.

## Structured Outputs e as 12 rejeições anteriores

O live anterior guardou apenas nove `ValueError` e três `ValidationError`, descartando corpo bruto e detalhes. Não é possível reconstruir a causa exata de cada uma das 12 respostas. A inspeção do código revelou dois contratos que o schema anterior não expressava completamente: compatibilidade por obrigação entre subject/representation_kind e coerência de presença/spans. São causas possíveis documentadas, não diagnósticos inventados por caso.

O novo schema usa `anyOf` aninhado para os pares permitidos por alvo e para separar presença/ausência. Todos os campos são obrigatórios, objetos proíbem propriedades extras e IDs usam enum compartilhado. Foram conferidos os limites de tamanho: máximo de 1.117 propriedades e 640 entradas de enum entre os 25 schemas. Essa estrutura segue a [documentação oficial de Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs). O modelo preservou compatibilidade real em 25/25 respostas.

Não se relaxou o contrato para aceitar JSON arbitrário, nem se recuperaram candidatos de respostas inválidas. O provider novo conserva saída bruta, response_id, uso e erros locais detalhados. Ainda assim, uma string aceita pelo schema pode conter prosa ou uma expressão não suportada pelo parser: essa é uma falha posterior, sem autoridade matemática.

## Comparação global antes/depois

| Medida | Live com spans LLM | Live com evidence IDs |
| --- | ---: | ---: |
| Chamadas externas | 25 | 25 |
| Respostas válidas | 13/25 (52%) | 25/25 (100%) |
| Respostas inválidas | 12 | 0 |
| Retries | 0 | 0 |
| Total de candidatos/seleções | 262 | 704 |
| Evidência presente | 166 | 235 |
| Ausência explícita | 96 | 469 |
| Vínculo literal exato / seleção vinculada por ID | 21 | 235 |
| Grounded na projeção legada | 9 | 49 |
| Atribuíveis após todos os gates | 6 | 8 |
| Canonicalizados | 16 | 22 |
| Flag context_rejected | 10 | 55 |
| FactResults semânticos novos | 6 | 4 |
| Verified novos | 6 | 3 |
| Refuted novos | 0 | 0 |
| Unverified novos | 0 | 1 |
| Technical error nos novos fatos | 0 | 0 |

**704 seleções não significam 704 evidências positivas:** 469 são respostas explícitas de ausência. Nenhum alvo foi omitido nesta rodada. As 235 seleções positivas usaram 332 ocorrências de IDs, todas válidas. A validade de ID foi 100%; o grounding legado foi 49 porque ainda aplica fronteiras de item e restrições de representação. O rótulo grounded, mesmo nesse estágio, não é suficiente para atribuição: apenas oito seleções foram atribuíveis.

A flag context_rejected inclui restrições de representação do código legado; não representa 55 exemplos de negação. As razões e a guarda adicional estão discriminadas em `post_grounding_diagnosis.json`. Houve quatro ocorrências da guarda conservadora adicional, sem alteração das regras antigas.

## Funil das 366 obrigações aparentemente satisfeitas antes perdidas

A tabela conta obrigações distintas, com denominador fixo de 366. A contagem global anterior de 21 spans exatos inclui uma obrigação fora desse subconjunto; neste funil, o número anterior é 20.

| Estágio | Antes | Agora |
| --- | ---: | ---: |
| Recebeu evidência candidata | 124 (33.88%) | 176 (48.09%) |
| Vínculo literal exato / por ID | 20 (5.46%) | 176 (48.09%) |
| Grounded na projeção existente | 9 (2.46%) | 39 (10.66%) |
| FactResult produzido | 6 (1.64%) | 4 (1.09%) |
| Verified | 6 (1.64%) | 3 (0.82%) |
| Potencialmente supported | 6 (1.64%) | 3 (0.82%) |

A perda de proveniência por offsets deixou de ocorrer. Entretanto, **176 seleções ligadas a trechos reais chegaram a 39 grounded na projeção e a apenas três verified**. A recuperação final foi **0,82%**, menor que os **1,64%** anteriores.

Esta não é uma ablação causal pura: schema, prompt, segmentação e guarda conservadora mudaram juntos, e o modelo gerou seleções diferentes. Não se pode afirmar que uma fração exata dos 115 misses que antes caíram de 124 para nove teria sido recuperada apenas pela troca de offsets. O resultado observável é: o vínculo determinístico funcionou, mas não bastou para aumentar fatos verificados.

| Problema | Misses | Com seleção | Vínculo por ID | Grounded projetado | FactResults | Verified |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TME2026P1 | 48 | 25 | 25 | 19 | 1 | 1 |
| TME2026P2 | 84 | 24 | 24 | 6 | 0 | 0 |
| TME2026P3 | 46 | 34 | 34 | 1 | 1 | 1 |
| TME2026P4 | 96 | 81 | 81 | 7 | 0 | 0 |
| TME2026P5 | 92 | 12 | 12 | 6 | 2 | 1 |

Os percentuais por problema e todos os denominadores estão em `summary_by_problem.json`.

## Onde o vínculo por ID ainda não chega à verificação

Entre as 235 seleções positivas, as razões finais são:

| Razão | Seleções |
| --- | ---: |
| unsupported_representation | 74 |
| input_mapping_miss | 66 |
| item_binding_miss | 60 |
| evidence_envelope_too_long | 13 |
| representation_miss | 11 |
| exact | 5 |
| deduplicated | 3 |
| context_gate | 3 |

As 66 ocorrências de input_mapping_miss estão nas quatro DEV cujo texto já não tinha item aceito mapeado. IDs não autorizam inventar esse roteamento. As 60 violações de fronteira de item incluem unidades físicas largas e seleções de rótulos fora da região aceita. Em P4_16, os itens `(b)` e `(c)` aparecem na mesma linha que `(a)`; 22 seleções ficam fora dos limites exigidos pelo adaptador. A segmentação desta versão preservou esse contexto, mas não criou unidades alinhadas aos itens internos da linha.

As 13 seleções de P3_13 usam um intervalo maior que 2.048 caracteres, limite existente na projeção. O texto foi preservado e o candidato bloqueado, sem truncamento.

Os payloads também continuam sendo um gargalo. Entre os 74 casos unsupported_representation, há strings com frases/rótulos em lugares onde a ontologia espera expressão, enum ou coleção. Exemplo: `APQR é paralelogramo.` pode estar associado a um ID verdadeiro, mas não equivale ao valor canônico esperado no campo enum. Isso não foi corrigido silenciosamente.

Um contraste observado é P5_18 versus P5_24: o primeiro retornou `P = 3*3*3*2 = 54`, que permaneceu unverified; o segundo retornou `3 * 3 * 3 * 2 = 54`, verificado por Lean. Não se retirou `P =` depois de observar os resultados. As perdas foram mantidas.

Esses achados delimitam a versão entregue. Qualquer ajuste futuro de segmentação, alinhamento a itens ou formato de expressão seria outro experimento congelado, não uma continuação com tratamento especial de DEV desta rodada.

## Supported: nomes e invariantes

| Métrica | Valor e significado |
| --- | --- |
| baseline_supported | **24**, caminho determinístico + Unicode congelado |
| semantic_verified_candidates | **3**, seleções ligadas a novos FactResults verified |
| semantic_potential_supported_new | **3**, novas obrigações supported frente ao baseline24 |
| combined_potential_supported | **27 = 24 + 3** |
| previous_obligation_shadow_supported | **30 = 24 + 6**, live anterior com offsets |
| historical_generic_supported | **43**, outro experimento, com o extrator semântico genérico |

A comparação antiga “43 → 30” misturava duas arquiteturas; não era uma redução do mesmo baseline pela simples presença do suplemento. Nesta rodada, **27 ≥ 24**, e a inclusão dos IDs supported do primário foi verificada em cada uma das 25 DEV. A proteção que rejeitaria a trilha semântica inteira se ela apagasse supported primário não precisou ser acionada.

| Problema | Primário | Shadow anterior | Shadow IDs |
| --- | ---: | ---: | ---: |
| TME2026P1 | 20 | 20 | 21 |
| TME2026P2 | 0 | 0 | 0 |
| TME2026P3 | 4 | 5 | 5 |
| TME2026P4 | 0 | 0 | 0 |
| TME2026P5 | 0 | 5 | 1 |

A cobertura entre as 409 aparentemente satisfeitas foi de 30/409 (7,33%) no shadow anterior para 27/409 (6,60%) neste. Indeterminate passou de 698 para 701. O primário isolado permanece em 24/409 (5,87%) e 704 indeterminate. O histórico genérico permanece como referência separada: 43/409 (10,51%).

## Segurança, revisão e testes

**137 testes passaram, zero falhas: 53 novos e 84 anteriores.** Foram exercitados IDs inexistentes/duplicados, campos proibidos, presença/ausência, Unicode, fontes repetidas, seleção múltipla, texto intermediário não selecionado, fronteiras de item, limite de tamanho, deduplicação, baseline monotônico, isolamento shadow e revalidação pelos checkers.

Os controles incluem negação, hipótese, tentativa abandonada, rejeição em parágrafo posterior, citação em outra linha, conflito não selecionado, resposta correta incidental e método errado com valor final correto. Fixtures positivos e negativos passaram por Lean real. Também foi conferido o caso em que o modelo omite o método errado e devolve apenas `12`: não foi produzido fato de perímetro nem crédito no fixture.

A revisão manual abrangeu todas as **oito seleções atribuíveis**. Três são confirmações deduplicadas de registros determinísticos; uma não produziu FactResult; quatro produziram FactResult, sendo três verified e um unverified. As fórmulas, contagens e pares selecionados correspondem explicitamente aos trechos. Não foi identificada falsa atribuição nos candidatos aceitos. Os trechos e a cadeia de evidência estão em `attribution_review.json` e `semantic_fact_provenance.json`.

Os quatro fatos novos foram:

| DEV | Fato | Verificação |
| --- | --- | --- |
| P1_13 | d.equation | verified — equivalência canônica |
| P3_22 | a.bottom_white_count | verified — checker determinístico |
| P5_18 | a.product | unverified — preservado sem crédito |
| P5_24 | a.product | verified — Lean |

A equação correta de P1_13 não valida a contagem posterior incorreta de valores de b; nenhum fato novo foi criado para essa contagem. O rótulo de uma obrigação não substituiu a decisão matemática do checker. Nenhuma evidência semântica chegou ao PautaEngine em shadow; nenhuma nota foi alterada.

A regressão ampla anterior foi reutilizada após conferir hashes dos arquivos preexistentes: 1.288 core passed e 263 ITA passed, com um xfail preexistente. Ela não foi apresentada como nova execução. Os testes da trilha nova e todos os controles semânticos foram efetivamente reexecutados. Os logs iniciais anteriores ao freeze também foram preservados; uma expectativa de fixture sobre pontuação intermediária foi ajustada para respeitar o parser legado, sem alterar esse parser.

## Gate e decisão final

Política registrada antes do live:

| Critério | Exigido | Observado | Resultado |
| --- | ---: | ---: | --- |
| Respostas válidas | ≥20/25 | 25/25 | Passou |
| Seleções positivas com IDs reais | 100% | 235/235 | Passou |
| Novos fatos verified | ≥7, acima dos seis anteriores | 3 | Falhou |
| Novos supported | ≥7 | 3 | Falhou |
| Falsa atribuição conhecida no escopo revisado | 0 | 0 | Passou |
| Falhas nos controles de contexto | 0 | 0 | Passou |
| Supported primário perdido | 0 | 0 | Passou |
| Technical error nos checkers | 0 | 0 | Passou |

**NO_GO. ACTIVE DEV não executado.** Os scores shadow permaneceram exatamente iguais ao primário; `needs_review=25/25` e `score_null=0/25`. Não há resultado de scoring ativo ou novas métricas sintéticas ativas, e nenhuma nota sintética foi usada como entrada ou critério do modelo. Zero falso crédito conhecido é uma conclusão limitada aos controles e evidências revisadas, não uma garantia geral.

**HOLDOUT processadas: 0/100.** Não houve reexecução seletiva, retry, alteração de código/prompt após o live, alteração de pauta/bridge/checker/Lean, mudança de UI/OCR ou commit.

## Artefatos e reprodução

- [preflight.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/preflight.json)
- [experiment_freeze.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/experiment_freeze.json)
- [promotion_policy.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/promotion_policy.json)
- [schema_preflight.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/schema_preflight.json)
- [structured_output_review.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/structured_output_review.json)
- [api_calls_summary.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/api_calls_summary.json)
- [shadow_candidates.jsonl](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/shadow_candidates.jsonl)
- [shadow_summary.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/shadow_summary.json)
- [funnel_before_after.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/funnel_before_after.json)
- [summary_by_problem.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/summary_by_problem.json)
- [metrics_definitions.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/metrics_definitions.json)
- [post_grounding_diagnosis.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/post_grounding_diagnosis.json)
- [false_credit_controls.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/false_credit_controls.json)
- [attribution_review.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/attribution_review.json)
- [semantic_fact_provenance.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/semantic_fact_provenance.json)
- [dev_before_after.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/dev_before_after.json)
- [GO_NO_GO.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/GO_NO_GO.json)
- [regression_validation.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/regression_validation.json)
- [integrity.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/integrity.json)
- [implementation.diff](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_evidence_ids_01/implementation.diff)

As unidades completas ficam em `evidence_units/`; o input sem offsets, em `prepared_payloads/`; schemas efetivamente enviados, em `schemas/`; saídas brutas/metadata, em `responses/`; bundles verificáveis, em `shadow/`. Os resumos originais do runner estão preservados em `runner_outputs/`. Não existe `active_dev_results.jsonl`, pois o gate falhou.

Reprodução dos controles, sem chamadas de modelo:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_evidence_id_semantic.py tests/test_obligation_semantic.py tests/test_semantic_claims.py
```

O runner tem modos `prepare`, `shadow` e `activate`, mas bloqueia reexecução live com respostas já existentes e alteração do freeze. `activate` exige gate aprovado, inexistente nesta rodada. Não há modo HOLDOUT. Não se deve apagar artefatos para repetir este experimento.
