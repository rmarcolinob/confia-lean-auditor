# P2 — Semantic Robustness DEV 01

Data: 2026-11-05. Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2`. SHA congelado: **`4fcc943521a1af566bed68e285462025f86b6b51`**.

**Veredito pré-registrado: P2_SEMANTIC_ADVANTAGE_CONFIRMED.** O resultado se limita a 48 casos sintéticos DEV, uma execução por modo e ao contrato operacional congelado; não mede generalização no holdout.

Exact score: **34/48 → 43/48**; MAE: **0,9583 → 0,1875**; recall: **61,11% → 83,33%**; precision: **76,74% → 100%**. Semantic Formal teve 11 vitórias, zero derrotas e 37 empates por erro absoluto. Houve um fallback semântico, nove obrigações legítimas perdidas e nenhuma obrigação positiva indevida no modo semântico.

## 1. Congelamento e protocolo

Estado inicial limpo. Os 48 textos/IDs e expectativas foram congelados antes de iniciar qualquer avaliação. Nenhum código, prompt, extractor, mapper, registry, checker, pauta, contrato de evidência ou política de score foi alterado. Nenhum gold externo/holdout foi acessado, nenhum P3 executado e nenhum commit foi feito.

Cada fonte contém somente `case_id`, `problem_id` e `solution_text`. O runner existente lê apenas `sources.json` e `ids.json`; expectativas e recibos não entram no payload do modelo. Ambos os modos usam `gpt-6.1-sol`, `medium`, `CONFIA_TME_SEMANTIC_ENABLED=0` e Lean habilitado. Current conserva seu caminho sem chamadas LLM. Cada caso foi executado uma vez por modo, sem retries de benchmark nem tuning.

As expectativas foram obtidas por referências matemáticas tipadas, previamente especificadas na construção, verificadas pelo `audit_p2_checker_first(use_lean=False)` e pontuadas pelo PautaEngine existente. Não houve LLM corretor. A referência não depende do sucesso da extração do texto variante. Os recibos contêm as referências, resultados dos checkers e todas as decisões de pauta. A construção usa verificação exata local, não afirma ter executado Lean; as provas reais são as da execução de benchmark.

As expectativas são operacionais: incluem dependências de justificação e limitações das representações admitidas, não somente verdade matemática. Contextos não adotados são removidos da referência por construção, antes da execução. Em campos tipados, o subject é preservado: `total: 24*16` vale apenas o ponto final, sem promoção a `counting_product`.

| arquivo | SHA-256 dos bytes |
| --- | --- |
| [expectations.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/tests/fixtures/tme_semantic_formal_p2/semantic_robustness_01/expectations.json) | ecf1fd6e728f7545f57258d20e654bcf42bb6bd3f176cae2a0f4868d4bce92fc |
| [sources.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/tests/fixtures/tme_semantic_formal_p2/semantic_robustness_01/sources.json) | 4128d9ba4e721f31c290770043e5e5a905bb28b522cfa565324e9759a3347c6e |
| [ids.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/tests/fixtures/tme_semantic_formal_p2/semantic_robustness_01/ids.json) | c7854dc49b1cba9c849ac41423439334a656152b9dc0363097be157bfe25e368 |
| [construction_receipts.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/tests/fixtures/tme_semantic_formal_p2/semantic_robustness_01/construction_receipts.json) | fe422baf6078c0093b9bdd04b9e6bf0bb166c5723fd86cdef9a1c664062df4ac |
| [manifest.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/tests/fixtures/tme_semantic_formal_p2/semantic_robustness_01/manifest.json) | 4fd345e6833985ee100459c32c6206950ca9318735900ff91b1a453527b34026 |

O manifesto contém hashes dos outros quatro arquivos; seu próprio hash é registrado acima, evitando uma autorreferência impossível. Hashes de serialização canônica do runner são distintos dos hashes dos bytes. Snapshot de 783 arquivos preexistentes verificado novamente ao final; todos preservados.

## 2. Distribuição e cobertura

| família | conteúdo | casos |
| --- | --- | --- |
| A | Paráfrase linguística | 8 |
| B | Representação matemática equivalente / fronteiras de representação | 8 |
| C | Justificação combinatória | 8 |
| D | Crédito parcial | 8 |
| E | Contexto negativo | 8 |
| F | Conflito, irrelevância e falso crédito | 8 |

As referências positivas cobrem as **23 obrigações**. Isso não implica cobertura exaustiva de cada representação/contexto de cada obrigação. Os oito casos C distinguem números isolados, rótulos, argumento verbal, aritmética tautológica, justificativa completa, aritmética falsa, estrutura combinatória inadequada e conclusão correta com justificativas insuficientes.

**Fronteiras preservadas:** B01 (`4*S-3*x=45`) é matematicamente equivalente ao balanço, mas o comparador congelado retorna `unverified`; o recibo pré-execução calculou zero. A descrição original de equivalência da construção é matemática, não prova de aceitação pelo checker. A04 e C03 têm expectativa operacional zero porque a estrutura verbal pura não é uma representação aceita por `argument_relation`; C03 é argumento matematicamente pertinente. Esses casos não demonstram que argumentos verbais são inválidos. Não se alteraram casos/expectativas depois da execução para transformar esses limites em ganhos.

## 3. Métricas e denominadores

- Exact score: igualdade com expected_score_by_construction; MAE em pontos; bias = score menos expected; within 1 é inclusivo.
- Obrigações: IDs com award elegível, inclusive fatos auxiliares sem parcela própria. Precision/recall são micro sobre pares caso–obrigação. FP/FN não são inferidos apenas da nota.
- False credit: excesso de pontos e, separadamente, suporte indevido a obrigações. Uma nota igual à esperada pode esconder FP e FN.
- Context rejection accuracy: ausência de suporte elegível ao ID do trecho negativo pré-registrado; todos esses alvos não têm outra evidência positiva adotada no caso. Omissão segura conta como supressão; rejeição explícita é contabilizada separadamente.
- Conflict handling accuracy: conflito esperado explicitamente marcado não resolvido e ID sem crédito. Bloqueio sem flag é informado à parte.
- Mathematical refutation preservation: um resultado negativo de checker preservado para cada alvo pré-registrado, inclusive refutação em subcheck. Ausência/insuficiência não contam como refutação.
- Status contam registros, não subprocessos únicos. Subchecks e diagnóstico formal são separados do status principal para evitar dupla contagem.
- Denominador zero: n/a. Falha operacional de extração é separada do flag nativo technical_uncertainty.

O critério congelado exige MAE menor, exact não inferior, excesso não maior, precisão de obrigações não inferior e acurácia de contexto/conflito não inferior para vantagem; com MAE empatado, noninferior only. Caso contrário, regression. Trata-se de uma regra descritiva, não de teste de significância.

## 4. Resultados globais

| métrica | Current | Semantic Formal |
| --- | --- | --- |
| Casos / scores numéricos | 48 | 48 |
| Exact (n) | 34 | 43 |
| Exact (proporção) | 0.7083 | 0.8958 |
| MAE | 0.9583 | 0.1875 |
| Bias | -0.1250 | -0.1875 |
| Within 1 (n) | 35 | 44 |
| Casos subpontuados | 9 | 5 |
| Casos sobrepontuados | 5 | 0 |
| Pontos faltantes | 26.0 | 9.0 |
| Pontos excedentes | 20.0 | 0.0 |
| TP obrigações | 33 | 45 |
| FP obrigações | 10 | 0 |
| FN obrigações | 21 | 9 |
| Precision | 0.7674 | 1.0 |
| Recall | 0.6111 | 0.8333 |
| Casos com FP | 5 | 0 |
| Alvos contextuais | 13 | 13 |
| Alvos suprimidos | 13 | 13 |
| Context accuracy | 1.0 | 1.0 |
| Rejeições contextuais explícitas | 0 | 9 |
| Alvos de conflito | 2 | 2 |
| Conflitos tratados explicitamente | 2 | 2 |
| Conflict accuracy | 1.0 | 1.0 |
| Alvos conflitantes sem crédito | 2 | 2 |
| Alvos de refutação | 6 | 6 |
| Refutações preservadas | 5 | 5 |
| Refutation preservation | 0.8333 | 0.8333 |
| Fallbacks | 0 | 1 |
| Falhas do extractor | 0 | 1 |
| Flag técnico nativo | 0 | 0 |
| FORMAL_ERROR principal/subcheck | 0 | 0 |
| Chamadas API | 0 | 48 |
| Latência média por caso (s) | 3.4626 | 11.1107 |

## 5. Resultados por família

### Família A

| métrica | Current | Semantic Formal |
| --- | --- | --- |
| Exact (n) | 1 | 4 |
| MAE | 2.3750 | 0.8750 |
| Bias | -2.3750 | -0.8750 |
| Within 1 (n) | 2 | 5 |
| Casos subpontuados | 7 | 4 |
| Casos sobrepontuados | 0 | 0 |
| Pontos faltantes | 19.0 | 7.0 |
| Pontos excedentes | 0.0 | 0.0 |
| TP obrigações | 0 | 9 |
| FP obrigações | 0 | 0 |
| FN obrigações | 17 | 8 |
| Precision | n/a | 1.0 |
| Recall | 0.0 | 0.5294 |
| Casos com FP | 0 | 0 |
| Alvos contextuais | 0 | 0 |
| Alvos suprimidos | 0 | 0 |
| Context accuracy | n/a | n/a |
| Rejeições contextuais explícitas | 0 | 0 |
| Alvos de conflito | 0 | 0 |
| Conflitos tratados explicitamente | 0 | 0 |
| Conflict accuracy | n/a | n/a |
| Alvos conflitantes sem crédito | 0 | 0 |
| Alvos de refutação | 0 | 0 |
| Refutações preservadas | 0 | 0 |
| Refutation preservation | n/a | n/a |
| Fallbacks | 0 | 1 |
| Falhas do extractor | 0 | 1 |
| Flag técnico nativo | 0 | 0 |
| FORMAL_ERROR principal/subcheck | 0 | 0 |

### Família B

| métrica | Current | Semantic Formal |
| --- | --- | --- |
| Exact (n) | 8 | 8 |
| MAE | 0.0 | 0.0 |
| Bias | 0.0 | 0.0 |
| Within 1 (n) | 8 | 8 |
| Casos subpontuados | 0 | 0 |
| Casos sobrepontuados | 0 | 0 |
| Pontos faltantes | 0.0 | 0.0 |
| Pontos excedentes | 0.0 | 0.0 |
| TP obrigações | 15 | 15 |
| FP obrigações | 0 | 0 |
| FN obrigações | 0 | 0 |
| Precision | 1.0 | 1.0 |
| Recall | 1.0 | 1.0 |
| Casos com FP | 0 | 0 |
| Alvos contextuais | 0 | 0 |
| Alvos suprimidos | 0 | 0 |
| Context accuracy | n/a | n/a |
| Rejeições contextuais explícitas | 0 | 0 |
| Alvos de conflito | 0 | 0 |
| Conflitos tratados explicitamente | 0 | 0 |
| Conflict accuracy | n/a | n/a |
| Alvos conflitantes sem crédito | 0 | 0 |
| Alvos de refutação | 0 | 0 |
| Refutações preservadas | 0 | 0 |
| Refutation preservation | n/a | n/a |
| Fallbacks | 0 | 0 |
| Falhas do extractor | 0 | 0 |
| Flag técnico nativo | 0 | 0 |
| FORMAL_ERROR principal/subcheck | 0 | 0 |

### Família C

| métrica | Current | Semantic Formal |
| --- | --- | --- |
| Exact (n) | 3 | 8 |
| MAE | 2.6250 | 0.0 |
| Bias | 1.3750 | 0.0 |
| Within 1 (n) | 3 | 8 |
| Casos subpontuados | 1 | 0 |
| Casos sobrepontuados | 4 | 0 |
| Pontos faltantes | 5.0 | 0.0 |
| Pontos excedentes | 16.0 | 0.0 |
| TP obrigações | 1 | 4 |
| FP obrigações | 8 | 0 |
| FN obrigações | 3 | 0 |
| Precision | 0.1111 | 1.0 |
| Recall | 0.2500 | 1.0 |
| Casos com FP | 4 | 0 |
| Alvos contextuais | 0 | 0 |
| Alvos suprimidos | 0 | 0 |
| Context accuracy | n/a | n/a |
| Rejeições contextuais explícitas | 0 | 0 |
| Alvos de conflito | 0 | 0 |
| Conflitos tratados explicitamente | 0 | 0 |
| Conflict accuracy | n/a | n/a |
| Alvos conflitantes sem crédito | 0 | 0 |
| Alvos de refutação | 2 | 2 |
| Refutações preservadas | 2 | 2 |
| Refutation preservation | 1.0 | 1.0 |
| Fallbacks | 0 | 0 |
| Falhas do extractor | 0 | 0 |
| Flag técnico nativo | 0 | 0 |
| FORMAL_ERROR principal/subcheck | 0 | 0 |

### Família D

| métrica | Current | Semantic Formal |
| --- | --- | --- |
| Exact (n) | 8 | 8 |
| MAE | 0.0 | 0.0 |
| Bias | 0.0 | 0.0 |
| Within 1 (n) | 8 | 8 |
| Casos subpontuados | 0 | 0 |
| Casos sobrepontuados | 0 | 0 |
| Pontos faltantes | 0.0 | 0.0 |
| Pontos excedentes | 0.0 | 0.0 |
| TP obrigações | 15 | 15 |
| FP obrigações | 0 | 0 |
| FN obrigações | 0 | 0 |
| Precision | 1.0 | 1.0 |
| Recall | 1.0 | 1.0 |
| Casos com FP | 0 | 0 |
| Alvos contextuais | 0 | 0 |
| Alvos suprimidos | 0 | 0 |
| Context accuracy | n/a | n/a |
| Rejeições contextuais explícitas | 0 | 0 |
| Alvos de conflito | 0 | 0 |
| Conflitos tratados explicitamente | 0 | 0 |
| Conflict accuracy | n/a | n/a |
| Alvos conflitantes sem crédito | 0 | 0 |
| Alvos de refutação | 0 | 0 |
| Refutações preservadas | 0 | 0 |
| Refutation preservation | n/a | n/a |
| Fallbacks | 0 | 0 |
| Falhas do extractor | 0 | 0 |
| Flag técnico nativo | 0 | 0 |
| FORMAL_ERROR principal/subcheck | 0 | 0 |

### Família E

| métrica | Current | Semantic Formal |
| --- | --- | --- |
| Exact (n) | 7 | 7 |
| MAE | 0.2500 | 0.2500 |
| Bias | -0.2500 | -0.2500 |
| Within 1 (n) | 7 | 7 |
| Casos subpontuados | 1 | 1 |
| Casos sobrepontuados | 0 | 0 |
| Pontos faltantes | 2.0 | 2.0 |
| Pontos excedentes | 0.0 | 0.0 |
| TP obrigações | 0 | 0 |
| FP obrigações | 0 | 0 |
| FN obrigações | 1 | 1 |
| Precision | n/a | n/a |
| Recall | 0.0 | 0.0 |
| Casos com FP | 0 | 0 |
| Alvos contextuais | 8 | 8 |
| Alvos suprimidos | 8 | 8 |
| Context accuracy | 1.0 | 1.0 |
| Rejeições contextuais explícitas | 0 | 8 |
| Alvos de conflito | 0 | 0 |
| Conflitos tratados explicitamente | 0 | 0 |
| Conflict accuracy | n/a | n/a |
| Alvos conflitantes sem crédito | 0 | 0 |
| Alvos de refutação | 1 | 1 |
| Refutações preservadas | 0 | 0 |
| Refutation preservation | 0.0 | 0.0 |
| Fallbacks | 0 | 0 |
| Falhas do extractor | 0 | 0 |
| Flag técnico nativo | 0 | 0 |
| FORMAL_ERROR principal/subcheck | 0 | 0 |

### Família F

| métrica | Current | Semantic Formal |
| --- | --- | --- |
| Exact (n) | 7 | 8 |
| MAE | 0.5000 | 0.0 |
| Bias | 0.5000 | 0.0 |
| Within 1 (n) | 7 | 8 |
| Casos subpontuados | 0 | 0 |
| Casos sobrepontuados | 1 | 0 |
| Pontos faltantes | 0.0 | 0.0 |
| Pontos excedentes | 4.0 | 0.0 |
| TP obrigações | 2 | 2 |
| FP obrigações | 2 | 0 |
| FN obrigações | 0 | 0 |
| Precision | 0.5000 | 1.0 |
| Recall | 1.0 | 1.0 |
| Casos com FP | 1 | 0 |
| Alvos contextuais | 5 | 5 |
| Alvos suprimidos | 5 | 5 |
| Context accuracy | 1.0 | 1.0 |
| Rejeições contextuais explícitas | 0 | 1 |
| Alvos de conflito | 2 | 2 |
| Conflitos tratados explicitamente | 2 | 2 |
| Conflict accuracy | 1.0 | 1.0 |
| Alvos conflitantes sem crédito | 2 | 2 |
| Alvos de refutação | 3 | 3 |
| Refutações preservadas | 3 | 3 |
| Refutation preservation | 1.0 | 1.0 |
| Fallbacks | 0 | 0 |
| Falhas do extractor | 0 | 0 |
| Flag técnico nativo | 0 | 0 |
| FORMAL_ERROR principal/subcheck | 0 | 0 |

## 6. Checkers e epistemologia

Lean real: 12 recibos de prova compilada e quatro de refutação no Current; 15 de prova compilada (seis principais e nove componentes) e quatro de refutação no Semantic Formal. Foram conferidos 20 e 23 arquivos Lean únicos, respectivamente; hashes e caminhos estão em analysis/execution_receipt.json. Esses números não incluem a construção determinística das expectativas.

| status principal | Current | Semantic Formal |
| --- | --- | --- |
| FORMAL_VERIFIED | 12 | 6 |
| FORMAL_REFUTED | 4 | 2 |
| FORMAL_UNPROVED | 0 | 0 |
| FORMAL_NOT_ATTEMPTED | 0 | 2 |
| FORMAL_ERROR | 0 | 0 |
| DETERMINISTIC_VERIFIED | 33 | 34 |
| DETERMINISTIC_FAILED | 4 | 2 |
| COMPOSITE_VERIFIED | 0 | 7 |
| COMPOSITE_INCOMPLETE | 0 | 12 |
| COMPOSITE_FAILED | 0 | 2 |

Demais status principais: Current `{}`; Semantic Formal `{"CONTEXT_REJECTED": 25, "CONFLICTING_EVIDENCE": 8}`.

Subchecks são recibos componentes, não nova pontuação.

| status dos subchecks | Current | Semantic Formal |
| --- | --- | --- |
| DETERMINISTIC_FAILED | 0 | 12 |
| DETERMINISTIC_VERIFIED | 0 | 41 |
| FORMAL_REFUTED | 0 | 2 |
| FORMAL_VERIFIED | 0 | 9 |

Diagnósticos formais adicionais de c.total: Current `{}`; Semantic Formal `{"FORMAL_NOT_ATTEMPTED": 9, "FORMAL_REFUTED": 2}`. Um total DETERMINISTIC_VERIFIED pode ter FORMAL_NOT_ATTEMPTED como diagnóstico sem perder o ponto. Ausência de prova não é refutação.

Contagens por família de todos os status principais:

| família | modo | FORMAL_VERIFIED | FORMAL_REFUTED | FORMAL_UNPROVED | FORMAL_NOT_ATTEMPTED | FORMAL_ERROR | DETERMINISTIC_VERIFIED | DETERMINISTIC_FAILED | COMPOSITE_VERIFIED | COMPOSITE_INCOMPLETE | COMPOSITE_FAILED |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | current | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| A | semantic_formal | 1 | 0 | 0 | 1 | 0 | 8 | 0 | 0 | 1 | 0 |
| B | current | 3 | 0 | 0 | 0 | 0 | 12 | 1 | 0 | 0 | 0 |
| B | semantic_formal | 2 | 0 | 0 | 0 | 0 | 12 | 1 | 1 | 0 | 0 |
| C | current | 4 | 2 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 |
| C | semantic_formal | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 2 | 8 | 2 |
| D | current | 3 | 0 | 0 | 0 | 0 | 12 | 1 | 0 | 0 | 0 |
| D | semantic_formal | 3 | 0 | 0 | 1 | 0 | 10 | 0 | 2 | 0 | 0 |
| E | current | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E | semantic_formal | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| F | current | 2 | 2 | 0 | 0 | 0 | 4 | 2 | 0 | 0 | 0 |
| F | semantic_formal | 0 | 2 | 0 | 0 | 0 | 2 | 1 | 2 | 3 | 0 |

## 7. Comparação pareada

Vencedor por menor erro absoluto de nota: **{"Semantic": 11, "Current": 0, "Empate": 37}**. Empate de nota não implica equivalência de suporte ou segurança.

| caso | expected | Current | Semantic | erro C | erro S | winner |
| --- | --- | --- | --- | --- | --- | --- |
| p2_rob_A01_balanco | 2.0 | 0.0 | 0.0 | 2.0 | 2.0 | Empate |
| p2_rob_A02_integralidade | 4.0 | 0.0 | 2.0 | 4.0 | 2.0 | Semantic |
| p2_rob_A03_maximo_pares | 3.0 | 0.0 | 3.0 | 3.0 | 0.0 | Semantic |
| p2_rob_A04_distribuicoes_verbais | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_A05_orientacoes | 2.0 | 0.0 | 0.0 | 2.0 | 2.0 | Empate |
| p2_rob_A06_conclusao | 1.0 | 0.0 | 1.0 | 1.0 | 0.0 | Semantic |
| p2_rob_A07_pares_cinco | 3.0 | 0.0 | 3.0 | 3.0 | 0.0 | Semantic |
| p2_rob_A08_formula_somas | 4.0 | 0.0 | 3.0 | 4.0 | 1.0 | Semantic |
| p2_rob_B01_balanco_equivalente | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_B02_formula_equivalente | 3.0 | 3.0 | 3.0 | 0.0 | 0.0 | Empate |
| p2_rob_B03_centros_reordenados | 2.0 | 2.0 | 2.0 | 0.0 | 0.0 | Empate |
| p2_rob_B04_pares_reordenados | 2.0 | 2.0 | 2.0 | 0.0 | 0.0 | Empate |
| p2_rob_B05_produto_comutado | 5.0 | 5.0 | 5.0 | 0.0 | 0.0 | Empate |
| p2_rob_B06_total_fatorial | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | Empate |
| p2_rob_B07_colocacao | 5.0 | 5.0 | 5.0 | 0.0 | 0.0 | Empate |
| p2_rob_B08_realizacoes | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | Empate |
| p2_rob_C01_numeros | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_C02_rotulos | 0.0 | 4.0 | 0.0 | 4.0 | 0.0 | Semantic |
| p2_rob_C03_relacao_verbal | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_C04_aritmetica_tautologica | 0.0 | 4.0 | 0.0 | 4.0 | 0.0 | Semantic |
| p2_rob_C05_justificacao_completa | 5.0 | 0.0 | 5.0 | 5.0 | 0.0 | Semantic |
| p2_rob_C06_aritmetica_falsa | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_C07_relacao_inadequada | 0.0 | 4.0 | 0.0 | 4.0 | 0.0 | Semantic |
| p2_rob_C08_conclusao_insuficiente | 1.0 | 5.0 | 1.0 | 4.0 | 0.0 | Semantic |
| p2_rob_D01_so_balanco | 2.0 | 2.0 | 2.0 | 0.0 | 0.0 | Empate |
| p2_rob_D02_so_integralidade | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_D03_centros_sem_base | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_D04_so_pares | 2.0 | 2.0 | 2.0 | 0.0 | 0.0 | Empate |
| p2_rob_D05_total_expressao | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | Empate |
| p2_rob_D06_etapas_sem_total | 4.0 | 4.0 | 4.0 | 0.0 | 0.0 | Empate |
| p2_rob_D07_total_literal | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | Empate |
| p2_rob_D08_subconjunto_misto | 3.0 | 3.0 | 3.0 | 0.0 | 0.0 | Empate |
| p2_rob_E01_hipotese | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_E02_negacao | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_E03_abandonado | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_E04_citacao | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_E05_enunciado | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_E06_tentativa | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_E07_abandono_e_conclusao | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_E08_misto_contexto | 2.0 | 0.0 | 0.0 | 2.0 | 2.0 | Empate |
| p2_rob_F01_verdade_irrelevante | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_F02_igualdade_contraditoria | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_F03_valores_incompativeis | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_F04_item_errado | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_F05_numeros_sem_relacao | 0.0 | 4.0 | 0.0 | 4.0 | 0.0 | Semantic |
| p2_rob_F06_conclusao_errada | 4.0 | 4.0 | 4.0 | 0.0 | 0.0 | Empate |
| p2_rob_F07_retracao | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |
| p2_rob_F08_numeros_incidentais | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | Empate |

## 8. False credits e missed credits

### current

| caso | excesso pts | falta pts | obrigações FP | obrigações FN |
| --- | --- | --- | --- | --- |
| p2_rob_A01_balanco | 0 | 2.0 | — | b.balance_relation |
| p2_rob_A02_integralidade | 0 | 4.0 | — | b.balance_relation, b.centers, b.integral_sum |
| p2_rob_A03_maximo_pares | 0 | 3.0 | — | c.max_center, c.max_sum, c.pairs |
| p2_rob_A05_orientacoes | 0 | 2.0 | — | c.pair_orientations |
| p2_rob_A06_conclusao | 0 | 1.0 | — | c.total |
| p2_rob_A07_pares_cinco | 0 | 3.0 | — | a.line_sum, a.pair_sum, a.pairs |
| p2_rob_A08_formula_somas | 0 | 4.0 | — | b.admissible_center, b.balance_relation, b.center_sums, b.sum_at_five, b.sum_formula |
| p2_rob_C02_rotulos | 4.0 | 0 | c.pair_orientations, c.pair_permutations | — |
| p2_rob_C04_aritmetica_tautologica | 4.0 | 0 | c.pair_orientations, c.pair_permutations | — |
| p2_rob_C05_justificacao_completa | 0 | 5.0 | — | c.pair_orientations, c.pair_permutations, c.total |
| p2_rob_C07_relacao_inadequada | 4.0 | 0 | c.pair_orientations, c.pair_permutations | — |
| p2_rob_C08_conclusao_insuficiente | 4.0 | 0 | c.pair_orientations, c.pair_permutations | — |
| p2_rob_E08_misto_contexto | 0 | 2.0 | — | c.pairs |
| p2_rob_F05_numeros_sem_relacao | 4.0 | 0 | c.pair_orientations, c.pair_permutations | — |

### semantic_formal

| caso | excesso pts | falta pts | obrigações FP | obrigações FN |
| --- | --- | --- | --- | --- |
| p2_rob_A01_balanco | 0 | 2.0 | — | b.balance_relation |
| p2_rob_A02_integralidade | 0 | 2.0 | — | b.centers, b.integral_sum |
| p2_rob_A05_orientacoes | 0 | 2.0 | — | c.pair_orientations |
| p2_rob_A07_pares_cinco | 0.0 | -0.0 | — | a.pair_sum |
| p2_rob_A08_formula_somas | 0 | 1.0 | — | b.admissible_center, b.sum_at_five, b.sum_formula |
| p2_rob_E08_misto_contexto | 0 | 2.0 | — | c.pairs |

## 9. COMPOSITE_STRONG

Os três checkers continuam exigindo arithmetic, counting_components e relation. O certificado finito prova o modelo do problema; não prova que o aluno escreveu uma justificativa. Um resultado verdadeiro isolado pode ficar COMPOSITE_INCOMPLETE; falha de relation com mathematical_refutation=false não refuta o número.

| caso | expected | Current | Semantic | resultados compostos S |
| --- | --- | --- | --- | --- |
| p2_rob_A04_distribuicoes_verbais | 0.0 | 0.0 | 0.0 | c.pair_permutations: COMPOSITE_INCOMPLETE [arithmetic=DETERMINISTIC_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established] |
| p2_rob_A05_orientacoes | 2.0 | 0.0 | 0.0 | c.pair_orientations: CONFLICTING_EVIDENCE []; c.pair_orientations: CONFLICTING_EVIDENCE [] |
| p2_rob_B05_produto_comutado | 5.0 | 5.0 | 5.0 | c.counting_product: COMPOSITE_VERIFIED [arithmetic=FORMAL_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_VERIFIED/explicit_counting_stages] |
| p2_rob_B06_total_fatorial | 1.0 | 1.0 | 1.0 | c.counting_product: CONTEXT_REJECTED [] |
| p2_rob_C01_numeros | 0.0 | 0.0 | 0.0 | c.counting_product: CONTEXT_REJECTED [] |
| p2_rob_C02_rotulos | 0.0 | 4.0 | 0.0 | c.pair_permutations: COMPOSITE_INCOMPLETE [arithmetic=DETERMINISTIC_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established]; c.pair_orientations: COMPOSITE_INCOMPLETE [arithmetic=DETERMINISTIC_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established] |
| p2_rob_C03_relacao_verbal | 0.0 | 0.0 | 0.0 | c.pair_permutations: CONTEXT_REJECTED []; c.pair_orientations: CONTEXT_REJECTED [] |
| p2_rob_C04_aritmetica_tautologica | 0.0 | 4.0 | 0.0 | c.pair_permutations: COMPOSITE_INCOMPLETE [arithmetic=FORMAL_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established]; c.pair_orientations: COMPOSITE_INCOMPLETE [arithmetic=FORMAL_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established] |
| p2_rob_C05_justificacao_completa | 5.0 | 0.0 | 5.0 | c.pair_permutations: COMPOSITE_VERIFIED [arithmetic=FORMAL_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_VERIFIED/explicit_counting_stages]; c.pair_orientations: COMPOSITE_VERIFIED [arithmetic=FORMAL_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_VERIFIED/explicit_counting_stages] |
| p2_rob_C06_aritmetica_falsa | 0.0 | 0.0 | 0.0 | c.pair_permutations: COMPOSITE_FAILED [arithmetic=FORMAL_REFUTED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_VERIFIED/explicit_counting_stages]; c.pair_orientations: COMPOSITE_FAILED [arithmetic=FORMAL_REFUTED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_VERIFIED/explicit_counting_stages] |
| p2_rob_C07_relacao_inadequada | 0.0 | 4.0 | 0.0 | c.pair_permutations: COMPOSITE_INCOMPLETE [arithmetic=FORMAL_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established]; c.pair_orientations: COMPOSITE_INCOMPLETE [arithmetic=FORMAL_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established] |
| p2_rob_C08_conclusao_insuficiente | 1.0 | 5.0 | 1.0 | c.pair_permutations: COMPOSITE_INCOMPLETE [arithmetic=DETERMINISTIC_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established]; c.pair_orientations: COMPOSITE_INCOMPLETE [arithmetic=DETERMINISTIC_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established] |
| p2_rob_D05_total_expressao | 1.0 | 1.0 | 1.0 | c.counting_product: CONTEXT_REJECTED [] |
| p2_rob_D06_etapas_sem_total | 4.0 | 4.0 | 4.0 | c.pair_permutations: COMPOSITE_VERIFIED [arithmetic=DETERMINISTIC_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_VERIFIED/explicit_counting_stages]; c.pair_orientations: COMPOSITE_VERIFIED [arithmetic=DETERMINISTIC_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_VERIFIED/explicit_counting_stages] |
| p2_rob_E03_abandonado | 0.0 | 0.0 | 0.0 | c.pair_permutations: CONTEXT_REJECTED [] |
| p2_rob_E06_tentativa | 0.0 | 0.0 | 0.0 | c.counting_product: CONTEXT_REJECTED [] |
| p2_rob_F01_verdade_irrelevante | 0.0 | 0.0 | 0.0 | c.counting_product: CONFLICTING_EVIDENCE []; c.counting_product: CONFLICTING_EVIDENCE [] |
| p2_rob_F02_igualdade_contraditoria | 0.0 | 0.0 | 0.0 | c.counting_product: CONTEXT_REJECTED [] |
| p2_rob_F05_numeros_sem_relacao | 0.0 | 4.0 | 0.0 | c.pair_permutations: COMPOSITE_INCOMPLETE [arithmetic=DETERMINISTIC_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established]; c.pair_orientations: COMPOSITE_INCOMPLETE [arithmetic=DETERMINISTIC_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established]; c.counting_product: COMPOSITE_INCOMPLETE [arithmetic=DETERMINISTIC_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_FAILED/argument_not_established] |
| p2_rob_F06_conclusao_errada | 4.0 | 4.0 | 4.0 | c.pair_permutations: COMPOSITE_VERIFIED [arithmetic=FORMAL_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_VERIFIED/explicit_counting_stages]; c.pair_orientations: COMPOSITE_VERIFIED [arithmetic=FORMAL_VERIFIED/existing_exact_written_arithmetic, counting_components=DETERMINISTIC_VERIFIED/exhaustive_finite_model_and_inverse, relation=DETERMINISTIC_VERIFIED/explicit_counting_stages]; c.counting_product: CONTEXT_REJECTED [] |

## 10. Contextos, conflitos, refutações e fallbacks

### context

| caso | Current | Semantic Formal |
| --- | --- | --- |
| p2_rob_E01_hipotese | [{"obligation_id": "c.total", "source_span": "Se eu supusesse total: 384, ainda seria apenas uma hipótese, não minha resposta.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "c.total", "source_span": "Se eu supusesse total: 384, ainda seria apenas uma hipótese, não minha resposta.", "safe": true, "explicit_rejection": true, "eligible_support_tied_to_span": false, "omission_or_other_suppression": false}] |
| p2_rob_E02_negacao | [{"obligation_id": "c.total", "source_span": "Não afirmo que total: 384. Não adoto esse resultado.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "c.total", "source_span": "Não afirmo que total: 384. Não adoto esse resultado.", "safe": true, "explicit_rejection": true, "eligible_support_tied_to_span": false, "omission_or_other_suppression": false}] |
| p2_rob_E03_abandonado | [{"obligation_id": "c.pair_permutations", "source_span": "Tentativa abandonada: pair_permutations: 4!=24. Descarto essa solução.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "c.pair_permutations", "source_span": "Tentativa abandonada: pair_permutations: 4!=24. Descarto essa solução.", "safe": true, "explicit_rejection": true, "eligible_support_tied_to_span": false, "omission_or_other_suppression": false}] |
| p2_rob_E04_citacao | [{"obligation_id": "b.balance_relation", "source_span": "Um colega escreveu \"balance_relation: 4*S=45+3*x\". Estou apenas citando, não adotando o argumento.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "b.balance_relation", "source_span": "Um colega escreveu \"balance_relation: 4*S=45+3*x\". Estou apenas citando, não adotando o argumento.", "safe": true, "explicit_rejection": true, "eligible_support_tied_to_span": false, "omission_or_other_suppression": false}] |
| p2_rob_E05_enunciado | [{"obligation_id": "c.max_sum", "source_span": "Transcrição do enunciado, não minha solução: max_sum: 18.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "c.max_sum", "source_span": "Transcrição do enunciado, não minha solução: max_sum: 18.", "safe": true, "explicit_rejection": true, "eligible_support_tied_to_span": false, "omission_or_other_suppression": false}] |
| p2_rob_E06_tentativa | [{"obligation_id": "c.counting_product", "source_span": "Rascunho não adotado: counting_product: 24*16=384. Ainda não tenho solução.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "c.counting_product", "source_span": "Rascunho não adotado: counting_product: 24*16=384. Ainda não tenho solução.", "safe": true, "explicit_rejection": true, "eligible_support_tied_to_span": false, "omission_or_other_suppression": false}] |
| p2_rob_E07_abandono_e_conclusao | [{"obligation_id": "c.total", "source_span": "Tentativa abandonada: total: 384.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "c.total", "source_span": "Tentativa abandonada: total: 384.", "safe": true, "explicit_rejection": true, "eligible_support_tied_to_span": false, "omission_or_other_suppression": false}] |
| p2_rob_E08_misto_contexto | [{"obligation_id": "c.total", "source_span": "Hipótese descartada: total: 384.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "c.total", "source_span": "Hipótese descartada: total: 384.", "safe": true, "explicit_rejection": true, "eligible_support_tied_to_span": false, "omission_or_other_suppression": false}] |
| p2_rob_F01_verdade_irrelevante | [{"obligation_id": "c.total", "source_span": "A conta 12*32=384 está correta, mas é um exemplo alheio e não representa a contagem dos preenchimentos.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "c.total", "source_span": "A conta 12*32=384 está correta, mas é um exemplo alheio e não representa a contagem dos preenchimentos.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] |
| p2_rob_F04_item_errado | [{"obligation_id": "c.total", "source_span": "total: 384", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}, {"obligation_id": "c.pair_permutations", "source_span": "pair_permutations: 4!=24", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "c.total", "source_span": "total: 384", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}, {"obligation_id": "c.pair_permutations", "source_span": "pair_permutations: 4!=24", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] |
| p2_rob_F07_retracao | [{"obligation_id": "c.total", "source_span": "total: 384.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "c.total", "source_span": "total: 384.", "safe": true, "explicit_rejection": true, "eligible_support_tied_to_span": false, "omission_or_other_suppression": false}] |
| p2_rob_F08_numeros_incidentais | [{"obligation_id": "c.total", "source_span": "Consultei a página 24, o exercício 16 e a ficha de matrícula 384. Ainda não resolvi a contagem.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] | [{"obligation_id": "c.total", "source_span": "Consultei a página 24, o exercício 16 e a ficha de matrícula 384. Ainda não resolvi a contagem.", "safe": true, "explicit_rejection": false, "eligible_support_tied_to_span": false, "omission_or_other_suppression": true}] |

### conflicts

| caso | Current | Semantic Formal |
| --- | --- | --- |
| p2_rob_F02_igualdade_contraditoria | [{"obligation_id": "c.total", "flagged": true, "credit_blocked": true, "correct": true}] | [{"obligation_id": "c.total", "flagged": true, "credit_blocked": true, "correct": true}] |
| p2_rob_F03_valores_incompativeis | [{"obligation_id": "c.total", "flagged": true, "credit_blocked": true, "correct": true}] | [{"obligation_id": "c.total", "flagged": true, "credit_blocked": true, "correct": true}] |

### refutations

| caso | Current | Semantic Formal |
| --- | --- | --- |
| p2_rob_C06_aritmetica_falsa | [{"obligation_id": "c.pair_permutations", "preserved": true}, {"obligation_id": "c.pair_orientations", "preserved": true}] | [{"obligation_id": "c.pair_permutations", "preserved": true}, {"obligation_id": "c.pair_orientations", "preserved": true}] |
| p2_rob_E07_abandono_e_conclusao | [{"obligation_id": "c.total", "preserved": false}] | [{"obligation_id": "c.total", "preserved": false}] |
| p2_rob_F02_igualdade_contraditoria | [{"obligation_id": "c.total", "preserved": true}] | [{"obligation_id": "c.total", "preserved": true}] |
| p2_rob_F03_valores_incompativeis | [{"obligation_id": "c.total", "preserved": true}] | [{"obligation_id": "c.total", "preserved": true}] |
| p2_rob_F06_conclusao_errada | [{"obligation_id": "c.total", "preserved": true}] | [{"obligation_id": "c.total", "preserved": true}] |

Fallbacks: listados abaixo.

| modo | caso | motivo |
| --- | --- | --- |
| semantic_formal | p2_rob_A01_balanco | ValueError:extractor_incomplete_or_refused |

A01 registrou output_tokens=16000, igual ao limite configurado, e extractor_incomplete_or_refused. Isso é evidência compatível com truncamento, mas o wrapper não preserva incomplete_details/status original suficiente para afirmar a causa exata. Não houve reexecução. Falha do extractor pode acionar fallback mesmo com technical_uncertainty=false.

### Achados que permanecem sem correção

- **A01:** indisponibilidade do extractor; fallback não recuperou o balanço.
- **A02:** integralidade extraída como integer foi rejeitada por representation_not_written; sem essa premissa, centers ficou FORMAL_NOT_ATTEMPTED. Não é refutação dos centros.
- **A05:** duas interpretações do mesmo envelope (qualitativa e fórmula escrita) acionaram conflicting_extractor_interpretation, bloqueando as orientações corretas.
- **A07:** conflito de interpretação suprimiu a.pair_sum, mas a.line_sum preservou o ponto da regra any_of; a nota correta oculta uma obrigação perdida.
- **A08:** fórmula rejeitada por subject_not_bound_to_source; S(5)=15 é payload não suportado; x=1 não passou a guarda de representação de admissible_center.
- **E08:** o modelo extraiu os pares como afirmados, mas a guarda local retornou source_context_rejected; a hipótese descartada anterior coexistia com uma enumeração efetivamente adotada. A causalidade observável é o veto local, não uma omissão do modelo.
- **E07:** ambos os modos deixaram sem crédito a conclusão errada 385, mas também não produziram a refutação matemática esperada. Por isso a preservação de refutação foi 5/6, e não 100%.
- Há quatro conflitos semânticos além dos dois alvos matemáticos pré-registrados: A05, A07, F01 e F07. Eles vêm de interpretações do extractor; F01/F07 não têm crédito esperado, mas A05/A07 perdem suporte legítimo. A acurácia 2/2 de conflitos esperados não mede esses conflitos adicionais.
- CONTEXT_REJECTED é um rótulo nativo também usado para rejeições de payload. Seus 25 registros não equivalem a 25 contextos negativos corretamente reconhecidos.

## 11. Análise causal de todas as divergências

Divergência inclui nota, conjunto de obrigações elegíveis, conflitos, status principais, fallback ou flag técnico. Classificações podem coexistir. SEMANTIC_RESCUE exige TP recuperado; COMPOSITE_RELATION_GAIN exige obrigação composta legítima recuperada, não mera inflação. CURRENT_BETTER usa menor erro absoluto. A classificação é uma síntese dos traces, não uma atribuição experimental isolada do efeito de cada componente.

Os JSON completos contêm source_span → claim → obligation → effective_route → checker → status → sufficiency → award, além de subchecks, mapping, proposição Lean e regras pagas. Nenhuma folha é somada duas vezes por aparecer em duas linhas.

### p2_rob_A01_balanco — EXTRACTION_MISS

Expected 2.0; Current 0.0; Semantic 0.0. Relação de balanço escrita em prosa e notação implícita de multiplicação.

```text
b) Somando as quatro linhas, contamos o centro x quatro vezes e os outros números uma vez. Assim, para a soma comum S, escrevo 4S = 45 + 3x.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_A01_balanco.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_A01_balanco.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

### p2_rob_A02_integralidade — SEMANTIC_RESCUE, PAYLOAD_MISMATCH

Expected 4.0; Current 0.0; Semantic 2.0. Balanço e integralidade justificam o conjunto de centros; não foi isolada a fórmula.

```text
b) A soma S precisa ser inteira porque soma três inteiros. O balanço é 4*S=45+3*x. Portanto os centros possíveis são {1,5,9}.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_A02_integralidade.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_A02_integralidade.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A soma S precisa ser inteira porque soma três inteiros. O balanço é 4*S=45+3*x. Portanto os centros possíveis são {1,5,9}. | 4*S=45+3*x | b.balance_relation | DETERMINISTIC | P2Checks.b | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| A soma S precisa ser inteira porque soma três inteiros. O balanço é 4*S=45+3*x. Portanto os centros possíveis são {1,5,9}. | {1,5,9} | b.centers | FORMAL | P2Checks.b | FORMAL_NOT_ATTEMPTED / EXISTING_VERIFICATION_RESULT | False | False |
| A soma S precisa ser inteira porque soma três inteiros. O balanço é 4*S=45+3*x. Portanto os centros possíveis são {1,5,9}. | integer | b.integral_sum | DETERMINISTIC | check_integrality (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / representation_not_written | False | False |

Regras efetivamente pagas: `[{"rule_id": "b.relation", "points": 2.0}]`.

### p2_rob_A03_maximo_pares — SEMANTIC_RESCUE

Expected 3.0; Current 0.0; Semantic 3.0. Máximo conjunto e enumeração dos pares, sem contagem.

```text
c) A maior soma comum é 18 e ocorre com o centro 9. Os pares das extremidades são {(1,8),(2,7),(3,6),(4,5)}.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_A03_maximo_pares.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_A03_maximo_pares.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A maior soma comum é 18 e ocorre com o centro 9. Os pares das extremidades são {(1,8),(2,7),(3,6),(4,5)}. | 9 | c.max_center | DETERMINISTIC | P2Checks.c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| A maior soma comum é 18 e ocorre com o centro 9. Os pares das extremidades são {(1,8),(2,7),(3,6),(4,5)}. | 18 | c.max_sum | DETERMINISTIC | P2Checks.c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| A maior soma comum é 18 e ocorre com o centro 9. Os pares das extremidades são {(1,8),(2,7),(3,6),(4,5)}. | {(1,8),(2,7),(3,6),(4,5)} | c.pairs | DETERMINISTIC | P2Checks.c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.maximum", "points": 1.0}, {"rule_id": "c.max_pairs", "points": 2.0}]`.

### p2_rob_A04_distribuicoes_verbais — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Rótulo e resultado não contêm estrutura combinatória admitida pelo checker congelado.

```text
c) Os quatro pares podem ser distribuídos pelas quatro retas de 24 formas.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_A04_distribuicoes_verbais.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_A04_distribuicoes_verbais.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Os quatro pares podem ser distribuídos pelas quatro retas de 24 formas. | 24 | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_A05_orientacoes — COMPOSITE_RELATION_MISS

Expected 2.0; Current 0.0; Semantic 0.0. Produto de quatro escolhas binárias realmente escrito.

```text
c) Cada um dos quatro pares admite duas posições independentes. Para as orientações, multiplico 2*2*2*2=16.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_A05_orientacoes.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_A05_orientacoes.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Cada um dos quatro pares admite duas posições independentes. Para as orientações, multiplico 2*2*2*2=16. | Cada um dos quatro pares admite duas posições independentes. | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONFLICTING_EVIDENCE / conflicting_extractor_interpretation | False | False |
| Cada um dos quatro pares admite duas posições independentes. Para as orientações, multiplico 2*2*2*2=16. | 2*2*2*2=16 | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONFLICTING_EVIDENCE / conflicting_extractor_interpretation | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_A06_conclusao — SEMANTIC_RESCUE

Expected 1.0; Current 0.0; Semantic 1.0. Total explícito, sem igualdade e sem crédito de método.

```text
c) Concluo que o total de preenchimentos é 384.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_A06_conclusao.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_A06_conclusao.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Concluo que o total de preenchimentos é 384. | 384 | c.total | DETERMINISTIC | P2Checks.c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.conclusion", "points": 1.0}]`.

### p2_rob_A07_pares_cinco — SEMANTIC_RESCUE

Expected 3.0; Current 0.0; Semantic 3.0. Regra e quatro pares, sem posições completas.

```text
a) Com o centro 5, cada par oposto soma 10 e cada linha soma 15. Os pares são {(1,9),(2,8),(3,7),(4,6)}.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_A07_pares_cinco.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_A07_pares_cinco.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Com o centro 5, cada par oposto soma 10 e cada linha soma 15. Os pares são {(1,9),(2,8),(3,7),(4,6)}. | 15 | a.line_sum | DETERMINISTIC | P2Checks.a | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| Com o centro 5, cada par oposto soma 10 e cada linha soma 15. Os pares são {(1,9),(2,8),(3,7),(4,6)}. | {(1,9),(2,8),(3,7),(4,6)} | a.pairs | DETERMINISTIC | P2Checks.a | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| Com o centro 5, cada par oposto soma 10 e cada linha soma 15. Os pares são {(1,9),(2,8),(3,7),(4,6)}. | 10 | a.pair_sum | DETERMINISTIC | P2Checks.a (não executado: mapping rejeitado/sem fato) | CONFLICTING_EVIDENCE / conflicting_extractor_interpretation | False | False |
| Com o centro 5, cada par oposto soma 10 e cada linha soma 15. Os pares são {(1,9),(2,8),(3,7),(4,6)}. | {(1,9),(2,8),(3,7),(4,6)} | a.pair_sum | DETERMINISTIC | P2Checks.a (não executado: mapping rejeitado/sem fato) | CONFLICTING_EVIDENCE / conflicting_extractor_interpretation | False | False |

Regras efetivamente pagas: `[{"rule_id": "a.rule", "points": 1.0}, {"rule_id": "a.four_pairs", "points": 2.0}]`.

### p2_rob_A08_formula_somas — SEMANTIC_RESCUE, PAYLOAD_MISMATCH

Expected 4.0; Current 0.0; Semantic 3.0. Cobre fórmula, três implicações e fatos auxiliares sem inventar realizabilidade.

```text
b) O balanço entre a soma S e o centro x é 4*S=45+3*x. Isolando a soma, S=(45+3*x)/4. As correspondências centro-soma são {(1,12),(5,15),(9,18)}. Para o centro 5 a soma é 15; o centro 1 é admissível.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_A08_formula_somas.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_A08_formula_somas.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| O balanço entre a soma S e o centro x é 4*S=45+3*x. Isolando a soma, S=(45+3*x)/4. As correspondências centro-soma são {(1,12),(5,15),(9,18)}. Para o centro 5 a soma é 15; o centro 1 é admissível. | 4*S=45+3*x | b.balance_relation | DETERMINISTIC | P2Checks.b | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| O balanço entre a soma S e o centro x é 4*S=45+3*x. Isolando a soma, S=(45+3*x)/4. As correspondências centro-soma são {(1,12),(5,15),(9,18)}. Para o centro 5 a soma é 15; o centro 1 é admissível. | {(1,12),(5,15),(9,18)} | b.center_sums | FORMAL | P2Checks.b | FORMAL_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| O balanço entre a soma S e o centro x é 4*S=45+3*x. Isolando a soma, S=(45+3*x)/4. As correspondências centro-soma são {(1,12),(5,15),(9,18)}. Para o centro 5 a soma é 15; o centro 1 é admissível. | S=(45+3*x)/4 | b.sum_formula | FORMAL | P2Checks.b (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / subject_not_bound_to_source | False | False |
| O balanço entre a soma S e o centro x é 4*S=45+3*x. Isolando a soma, S=(45+3*x)/4. As correspondências centro-soma são {(1,12),(5,15),(9,18)}. Para o centro 5 a soma é 15; o centro 1 é admissível. | S(5)=15 | b.sum_at_five | FORMAL | P2Checks.b (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / unsupported_checker_payload | False | False |
| O balanço entre a soma S e o centro x é 4*S=45+3*x. Isolando a soma, S=(45+3*x)/4. As correspondências centro-soma são {(1,12),(5,15),(9,18)}. Para o centro 5 a soma é 15; o centro 1 é admissível. | x=1 | b.admissible_center | FORMAL | P2Checks.b (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / representation_not_written | False | False |

Regras efetivamente pagas: `[{"rule_id": "b.relation", "points": 2.0}, {"rule_id": "b.sums", "points": 1.0}]`.

### p2_rob_B05_produto_comutado — OTHER

Expected 5.0; Current 5.0; Semantic 5.0. Método direto com fatores comutados; campo tipado é counting_product, não total.

```text
c) counting_product: 16*24=384
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_B05_produto_comutado.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| counting_product: 16*24=384 | 16*24=384 | c.counting_product | FORMAL | P2Checks.c / tme2-p2-check.v1 | FORMAL_VERIFIED / None | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.direct_product_path", "points": 5.0}]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_B05_produto_comutado.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| counting_product: 16*24=384 | 16*24=384 | c.counting_product | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.direct_product_path", "points": 5.0}]`.

### p2_rob_B06_total_fatorial — OTHER

Expected 1.0; Current 1.0; Semantic 1.0. Expressão fechada escrita no campo total: rota de valor, sem promover o subject a método direto.

```text
c) total: 4!*2^4
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_B06_total_fatorial.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| total: 4!*2^4 | 4!*2^4 | c.total | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.conclusion", "points": 1.0}]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_B06_total_fatorial.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| total: 4!*2^4 | 4!*2^4 | c.total | DETERMINISTIC | P2Checks.c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| total: 4!*2^4 | 4!*2^4 | c.counting_product | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / typed_source_payload_changed | False | False |

Regras efetivamente pagas: `[{"rule_id": "c.conclusion", "points": 1.0}]`.

### p2_rob_C01_numeros — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Números sem objeto ou relação não satisfazem nenhuma obrigação.

```text
c) 24. 16.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_C01_numeros.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_C01_numeros.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 24. 16. | 24 · 16 | c.counting_product | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / unsupported_checker_payload | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_C02_rotulos — BASELINE_OVER_CREDIT

Expected 0.0; Current 4.0; Semantic 0.0. Resultados e rótulos não bastam aos dois compostos.

```text
c) pair_permutations: 24
pair_orientations: 16
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_C02_rotulos.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 24 | 24 | c.pair_permutations | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | True | True |
| pair_orientations: 16 | 16 | c.pair_orientations | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.distributions", "points": 2.0}, {"rule_id": "c.orientations", "points": 2.0}]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_C02_rotulos.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 24 | 24 | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |
| pair_orientations: 16 | 16 | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_C03_relacao_verbal — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Argumento verbal matematicamente pertinente, mas sem representação simbólica admitida; expectativa operacional do contrato congelado, não juízo de invalidade pedagógica.

```text
c) Distribuo um par em cada reta: há quatro escolhas para a primeira, três para a segunda, duas para a terceira e uma para a última, dando 24 distribuições. Cada par pode inverter suas duas pontas independentemente, resultando em 16 orientações.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_C03_relacao_verbal.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_C03_relacao_verbal.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Distribuo um par em cada reta: há quatro escolhas para a primeira, três para a segunda, duas para a terceira e uma para a última, dando 24 distribuições. Cada par pode inverter suas duas pontas independentemente, resultando em 16 orientações. | Distribuo um par em cada reta: há quatro escolhas para a primeira, três para a segunda, duas para a terceira e uma para a última, dando 24 distribuições. | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / unsupported_checker_payload | False | False |
| Distribuo um par em cada reta: há quatro escolhas para a primeira, três para a segunda, duas para a terceira e uma para a última, dando 24 distribuições. Cada par pode inverter suas duas pontas independentemente, resultando em 16 orientações. | Cada par pode inverter suas duas pontas independentemente, resultando em 16 orientações. | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / unsupported_checker_payload | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_C04_aritmetica_tautologica — BASELINE_OVER_CREDIT

Expected 0.0; Current 4.0; Semantic 0.0. Igualdades verdadeiras sem estrutura das escolhas não estabelecem relation.

```text
c) pair_permutations: 24=24
pair_orientations: 16=16
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_C04_aritmetica_tautologica.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 24=24 | 24=24 | c.pair_permutations | FORMAL | P2Checks.counting / tme2-p2-check.v1 | FORMAL_VERIFIED / None | True | True |
| pair_orientations: 16=16 | 16=16 | c.pair_orientations | FORMAL | P2Checks.counting / tme2-p2-check.v1 | FORMAL_VERIFIED / None | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.distributions", "points": 2.0}, {"rule_id": "c.orientations", "points": 2.0}]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_C04_aritmetica_tautologica.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 24=24 | 24=24 | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |
| pair_orientations: 16=16 | 16=16 | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_C05_justificacao_completa — SEMANTIC_RESCUE, COMPOSITE_RELATION_GAIN

Expected 5.0; Current 0.0; Semantic 5.0. Estrutura multiplicativa das duas etapas e conclusão explícita: 2+2+1.

```text
c) Distribuo os quatro pares por 4*3*2*1=24 maneiras. As orientações independentes dos quatro pares dão 2*2*2*2=16. O total de preenchimentos é 384.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_C05_justificacao_completa.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_C05_justificacao_completa.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Distribuo os quatro pares por 4*3*2*1=24 maneiras. As orientações independentes dos quatro pares dão 2*2*2*2=16. O total de preenchimentos é 384. | 4*3*2*1=24 | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| Distribuo os quatro pares por 4*3*2*1=24 maneiras. As orientações independentes dos quatro pares dão 2*2*2*2=16. O total de preenchimentos é 384. | 2*2*2*2=16 | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| Distribuo os quatro pares por 4*3*2*1=24 maneiras. As orientações independentes dos quatro pares dão 2*2*2*2=16. O total de preenchimentos é 384. | 384 | c.total | DETERMINISTIC | P2Checks.c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.distributions", "points": 2.0}, {"rule_id": "c.orientations", "points": 2.0}, {"rule_id": "c.conclusion", "points": 1.0}]`.

### p2_rob_C06_aritmetica_falsa — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Resultados aritméticos falsos não recebem reparação semântica.

```text
c) pair_permutations: 4!=25
pair_orientations: 2^4=15
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_C06_aritmetica_falsa.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 4!=25 | 4!=25 | c.pair_permutations | FORMAL | P2Checks.counting / tme2-p2-check.v1 | FORMAL_REFUTED / None | False | False |
| pair_orientations: 2^4=15 | 2^4=15 | c.pair_orientations | FORMAL | P2Checks.counting / tme2-p2-check.v1 | FORMAL_REFUTED / None | False | False |

Regras efetivamente pagas: `[]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_C06_aritmetica_falsa.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 4!=25 | 4!=25 | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_FAILED / EXISTING_VERIFICATION_RESULT | False | False |
| pair_orientations: 2^4=15 | 2^4=15 | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_FAILED / EXISTING_VERIFICATION_RESULT | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_C07_relacao_inadequada — BASELINE_OVER_CREDIT

Expected 0.0; Current 4.0; Semantic 0.0. Aritmética verdadeira com estrutura errada para os objetos combinatórios; insuficiência, não refutação aritmética.

```text
c) pair_permutations: 2^3*3=24
pair_orientations: 4+12=16
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_C07_relacao_inadequada.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 2^3*3=24 | 2^3*3=24 | c.pair_permutations | FORMAL | P2Checks.counting / tme2-p2-check.v1 | FORMAL_VERIFIED / None | True | True |
| pair_orientations: 4+12=16 | 4+12=16 | c.pair_orientations | FORMAL | P2Checks.counting / tme2-p2-check.v1 | FORMAL_VERIFIED / None | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.distributions", "points": 2.0}, {"rule_id": "c.orientations", "points": 2.0}]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_C07_relacao_inadequada.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 2^3*3=24 | 2^3*3=24 | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |
| pair_orientations: 4+12=16 | 4+12=16 | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_C08_conclusao_insuficiente — BASELINE_OVER_CREDIT

Expected 1.0; Current 5.0; Semantic 1.0. Somente o ponto de conclusão permitido pelo contrato revisado.

```text
c) pair_permutations: 24
pair_orientations: 16
total: 384
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_C08_conclusao_insuficiente.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 24 | 24 | c.pair_permutations | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | True | True |
| pair_orientations: 16 | 16 | c.pair_orientations | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | True | True |
| total: 384 | 384 | c.total | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.distributions", "points": 2.0}, {"rule_id": "c.orientations", "points": 2.0}, {"rule_id": "c.conclusion", "points": 1.0}]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_C08_conclusao_insuficiente.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 24 | 24 | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |
| pair_orientations: 16 | 16 | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |
| total: 384 | 384 | c.total | DETERMINISTIC | P2Checks.c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.conclusion", "points": 1.0}]`.

### p2_rob_D03_centros_sem_base — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Centros sem integralidade/balanço ou condição modular permanecem injustificados; sem realizabilidade.

```text
b) centers: {1,5,9}
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_D03_centros_sem_base.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| centers: {1,5,9} | {1,5,9} | b.centers | DETERMINISTIC | P2Checks.b / tme2-p2-check.v1 | DETERMINISTIC_FAILED / None | False | False |

Regras efetivamente pagas: `[]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_D03_centros_sem_base.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| centers: {1,5,9} | {1,5,9} | b.centers | FORMAL | P2Checks.b | FORMAL_NOT_ATTEMPTED / EXISTING_VERIFICATION_RESULT | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_D05_total_expressao — OTHER

Expected 1.0; Current 1.0; Semantic 1.0. Total como expressão fechada no seu campo: somente conclusão de 1 ponto.

```text
c) total: 24*16
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_D05_total_expressao.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| total: 24*16 | 24*16 | c.total | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.conclusion", "points": 1.0}]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_D05_total_expressao.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| total: 24*16 | 24*16 | c.total | DETERMINISTIC | P2Checks.c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| total: 24*16 | 24*16 | c.counting_product | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / typed_source_payload_changed | False | False |

Regras efetivamente pagas: `[{"rule_id": "c.conclusion", "points": 1.0}]`.

### p2_rob_D06_etapas_sem_total — OTHER

Expected 4.0; Current 4.0; Semantic 4.0. Estruturas escritas com valor exatamente verificável, sem conclusão final: 4 pontos.

```text
c) pair_permutations: 4!
pair_orientations: 2^4
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_D06_etapas_sem_total.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 4! | 4! | c.pair_permutations | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | True | True |
| pair_orientations: 2^4 | 2^4 | c.pair_orientations | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.distributions", "points": 2.0}, {"rule_id": "c.orientations", "points": 2.0}]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_D06_etapas_sem_total.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 4! | 4! | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| pair_orientations: 2^4 | 2^4 | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |

Regras efetivamente pagas: `[{"rule_id": "c.distributions", "points": 2.0}, {"rule_id": "c.orientations", "points": 2.0}]`.

### p2_rob_E01_hipotese — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Afirmação correta em contexto não adotado: não atribuir crédito.

```text
c) Se eu supusesse total: 384, ainda seria apenas uma hipótese, não minha resposta.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_E01_hipotese.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_E01_hipotese.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Se eu supusesse total: 384, ainda seria apenas uma hipótese, não minha resposta. | total: 384 | c.total | FORMAL | P2Checks.c (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / nonasserted_or_unattributed_context | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_E02_negacao — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Afirmação correta em contexto não adotado: não atribuir crédito.

```text
c) Não afirmo que total: 384. Não adoto esse resultado.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_E02_negacao.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_E02_negacao.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Não afirmo que total: 384. Não adoto esse resultado. | total = 384 | c.total | FORMAL | P2Checks.c (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / nonasserted_or_unattributed_context | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_E03_abandonado — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Afirmação correta em contexto não adotado: não atribuir crédito.

```text
c) Tentativa abandonada: pair_permutations: 4!=24. Descarto essa solução.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_E03_abandonado.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_E03_abandonado.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Tentativa abandonada: pair_permutations: 4!=24. Descarto essa solução. | 4!=24 | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / nonasserted_or_unattributed_context | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_E04_citacao — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Afirmação correta em contexto não adotado: não atribuir crédito.

```text
b) Um colega escreveu "balance_relation: 4*S=45+3*x". Estou apenas citando, não adotando o argumento.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_E04_citacao.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_E04_citacao.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Um colega escreveu "balance_relation: 4*S=45+3*x". Estou apenas citando, não adotando o argumento. | 4*S=45+3*x | b.balance_relation | DETERMINISTIC | P2Checks.b (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / nonasserted_or_unattributed_context | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_E05_enunciado — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Afirmação correta em contexto não adotado: não atribuir crédito.

```text
c) Transcrição do enunciado, não minha solução: max_sum: 18.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_E05_enunciado.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_E05_enunciado.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c) Transcrição do enunciado, não minha solução: max_sum: 18. | 18 | c.max_sum | DETERMINISTIC | P2Checks.c (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / nonasserted_or_unattributed_context | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_E06_tentativa — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Afirmação correta em contexto não adotado: não atribuir crédito.

```text
c) Rascunho não adotado: counting_product: 24*16=384. Ainda não tenho solução.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_E06_tentativa.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_E06_tentativa.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rascunho não adotado: counting_product: 24*16=384. Ainda não tenho solução. | 24*16=384 | c.counting_product | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / nonasserted_or_unattributed_context | False | False |
| Rascunho não adotado: counting_product: 24*16=384. Ainda não tenho solução. | Ainda não tenho solução. | c.total | FORMAL | P2Checks.c (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / nonasserted_or_unattributed_context | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_E07_abandono_e_conclusao — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Mesmo objeto tem valor correto abandonado e conclusão diferente errada; não selecionar 384.

```text
c) Tentativa abandonada: total: 384.
Minha conclusão final é total: 385.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_E07_abandono_e_conclusao.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_E07_abandono_e_conclusao.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Tentativa abandonada: total: 384. | 384 | c.total | FORMAL | P2Checks.c (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / nonasserted_or_unattributed_context | False | False |
| Minha conclusão final é total: 385. | 385 | c.total | FORMAL | P2Checks.c (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / source_context_rejected | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_E08_misto_contexto — OTHER

Expected 2.0; Current 0.0; Semantic 0.0. Rejeitar hipótese e preservar enumeração adotada.

```text
c) Hipótese descartada: total: 384.
Como solução efetiva, os pares das extremidades são {(1,8),(2,7),(3,6),(4,5)}.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_E08_misto_contexto.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_E08_misto_contexto.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Hipótese descartada: total: 384. | 384 | c.total | FORMAL | P2Checks.c (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / nonasserted_or_unattributed_context | False | False |
| Como solução efetiva, os pares das extremidades são {(1,8),(2,7),(3,6),(4,5)}. | {(1,8),(2,7),(3,6),(4,5)} | c.pairs | DETERMINISTIC | P2Checks.c (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / source_context_rejected | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_F01_verdade_irrelevante — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Igualdade verdadeira explicitamente irrelevante; não é total nem método direto.

```text
c) A conta 12*32=384 está correta, mas é um exemplo alheio e não representa a contagem dos preenchimentos.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_F01_verdade_irrelevante.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_F01_verdade_irrelevante.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A conta 12*32=384 está correta, mas é um exemplo alheio e não representa a contagem dos preenchimentos. | A conta 12*32=384 está correta | c.counting_product | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONFLICTING_EVIDENCE / conflicting_extractor_interpretation | False | False |
| A conta 12*32=384 está correta, mas é um exemplo alheio e não representa a contagem dos preenchimentos. | é um exemplo alheio e não representa a contagem dos preenchimentos. | c.counting_product | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONFLICTING_EVIDENCE / conflicting_extractor_interpretation | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_F02_igualdade_contraditoria — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Valor correto e igualdade falsa exigem conflito não resolvido e zero.

```text
c) total: 384
total: 24*16=364
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_F02_igualdade_contraditoria.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| total: 384 | 384 | c.total | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | False | False |
| total: 24*16=364 | 24*16=364 | c.total | FORMAL | P2Checks.counting / tme2-p2-check.v1 | FORMAL_REFUTED / None | False | False |

Regras efetivamente pagas: `[]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_F02_igualdade_contraditoria.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| total: 384 | 384 | c.total | DETERMINISTIC | P2Checks.c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | False |
| total: 24*16=364 | 24*16=364 | c.total | FORMAL | P2Checks.c | FORMAL_REFUTED / EXISTING_VERIFICATION_RESULT | False | False |
| total: 24*16=364 | 24*16=364 | c.counting_product | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / typed_source_payload_changed | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_F03_valores_incompativeis — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Dois valores incompatíveis da mesma conclusão: bloquear crédito.

```text
c) total: 384
total: 385
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_F03_valores_incompativeis.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| total: 384 | 384 | c.total | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | False | False |
| total: 385 | 385 | c.total | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_FAILED / None | False | False |

Regras efetivamente pagas: `[]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_F03_valores_incompativeis.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| total: 384 | 384 | c.total | DETERMINISTIC | P2Checks.c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT | True | False |
| total: 385 | 385 | c.total | DETERMINISTIC | P2Checks.c | DETERMINISTIC_FAILED / EXISTING_VERIFICATION_RESULT | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_F04_item_errado — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Contagem de c escrita somente no item a; não transportar entre itens.

```text
a) total: 384
pair_permutations: 4!=24
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_F04_item_errado.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_F04_item_errado.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a) total: 384 | 384 | a.pair_sum | DETERMINISTIC | P2Checks.a (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / same_item_required | False | False |
| pair_permutations: 4!=24 | 4!=24 | a.pair_sum | DETERMINISTIC | P2Checks.a (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / obligation_subject_type_mismatch | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_F05_numeros_sem_relacao — BASELINE_OVER_CREDIT

Expected 0.0; Current 4.0; Semantic 0.0. Três números rotulados sem estrutura; inclusive produto direto não é um valor final total tipado.

```text
c) pair_permutations: 24
pair_orientations: 16
counting_product: 384
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_F05_numeros_sem_relacao.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 24 | 24 | c.pair_permutations | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | True | True |
| pair_orientations: 16 | 16 | c.pair_orientations | DETERMINISTIC | P2Checks.counting / tme2-p2-check.v1 | DETERMINISTIC_VERIFIED / None | True | True |
| counting_product: 384 | 384 | c.counting_product | DETERMINISTIC | P2Checks.c / tme2-p2-check.v1 | DETERMINISTIC_FAILED / None | False | False |

Regras efetivamente pagas: `[{"rule_id": "c.distributions", "points": 2.0}, {"rule_id": "c.orientations", "points": 2.0}]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_F05_numeros_sem_relacao.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 24 | 24 | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |
| pair_orientations: 16 | 16 | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |
| counting_product: 384 | 384 | c.counting_product | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_INCOMPLETE / EXISTING_VERIFICATION_RESULT | False | False |

Regras efetivamente pagas: `[]`.

### p2_rob_F06_conclusao_errada — OTHER

Expected 4.0; Current 4.0; Semantic 4.0. Duas etapas corretas valem 4; conclusão falsa não recebe o quinto ponto.

```text
c) pair_permutations: 4!=24
pair_orientations: 2^4=16
total: 24*16=385
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_F06_conclusao_errada.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 4!=24 | 4!=24 | c.pair_permutations | FORMAL | P2Checks.counting / tme2-p2-check.v1 | FORMAL_VERIFIED / None | True | True |
| pair_orientations: 2^4=16 | 2^4=16 | c.pair_orientations | FORMAL | P2Checks.counting / tme2-p2-check.v1 | FORMAL_VERIFIED / None | True | True |
| total: 24*16=385 | 24*16=385 | c.total | FORMAL | P2Checks.counting / tme2-p2-check.v1 | FORMAL_REFUTED / None | False | False |

Regras efetivamente pagas: `[{"rule_id": "c.distributions", "points": 2.0}, {"rule_id": "c.orientations", "points": 2.0}]`.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_F06_conclusao_errada.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_permutations: 4!=24 | 4!=24 | c.pair_permutations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| pair_orientations: 2^4=16 | 2^4=16 | c.pair_orientations | COMPOSITE | P2CompositeCountingChecker | COMPOSITE_VERIFIED / EXISTING_VERIFICATION_RESULT | True | True |
| total: 24*16=385 | 24*16=385 | c.total | FORMAL | P2Checks.c | FORMAL_REFUTED / EXISTING_VERIFICATION_RESULT | False | False |
| total: 24*16=385 | 24*16=385 | c.counting_product | COMPOSITE | P2CompositeCountingChecker (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / typed_source_payload_changed | False | False |

Regras efetivamente pagas: `[{"rule_id": "c.distributions", "points": 2.0}, {"rule_id": "c.orientations", "points": 2.0}]`.

### p2_rob_F07_retracao — OTHER

Expected 0.0; Current 0.0; Semantic 0.0. Retratação explícita posterior invalida a adoção do claim; não usar primeira frase isolada.

```text
c) total: 384.
Retiro explicitamente minha afirmação anterior: não aceito que o total seja 384. Não apresento outra conclusão.
```

**current** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/current/p2_rob_F07_retracao.json).

Nenhum fato verificável produzido. O artefato preserva os registros locais e a extração bruta disponível; ausência não é refutação.

**semantic_formal** — [artefato completo](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal/p2_rob_F07_retracao.json).

| source_span | claim | obligation | rota | checker | status / motivo | suficiência | award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| total: 384. | total = 384 | c.total | FORMAL | P2Checks.c (não executado: mapping rejeitado/sem fato) | CONTEXT_REJECTED / nonasserted_or_unattributed_context | False | False |
| Retiro explicitamente minha afirmação anterior: não aceito que o total seja 384. Não apresento outra conclusão. | não aceito que o total seja 384 | c.total | FORMAL | P2Checks.c (não executado: mapping rejeitado/sem fato) | CONFLICTING_EVIDENCE / conflicting_extractor_interpretation | False | False |
| Retiro explicitamente minha afirmação anterior: não aceito que o total seja 384. Não apresento outra conclusão. | Não apresento outra conclusão. | c.total | FORMAL | P2Checks.c (não executado: mapping rejeitado/sem fato) | CONFLICTING_EVIDENCE / conflicting_extractor_interpretation | False | False |

Regras efetivamente pagas: `[]`.

## 12. Limitações e veredito

O benchmark é sintético e pequeno, com exemplos deliberadamente tipados ao lado de prosa. Uma única execução não estima variância do extractor. Os alvos de conflito são apenas dois; os denominadores de segurança são pequenos. O contrato operacional restringe a referência de crédito: B01 e C03 evidenciam limites reais, mas sua expectativa zero não mede recall de todo raciocínio matematicamente válido. Não se deve usar os resultados para afirmar compreensão semântica geral.

As referências de construção são especificadas por desenho e verificadas deterministicamente; não são rótulos externos independentes nem solução de um segundo LLM. Uma interpretação discutível do desenho permanece auditável nos recibos. Não se mudaram expectativas para favorecer o modo semântico após observar resultados.

Condições do veredito: `{"mae_noninferior": true, "exact_noninferior": true, "excess_noninferior": true, "precision_noninferior": true, "context_noninferior": true, "conflict_noninferior": true}`. **P2_SEMANTIC_ADVANTAGE_CONFIRMED**. Defeitos observados ficam documentados; nenhuma correção foi aplicada nesta tarefa.

## 13. Reprodutibilidade e Git

Comandos executados uma vez cada, com stdout/stderr combinados preservados em logs:

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0 \
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python \
  scripts/evaluation/run_tme_semantic_formal_p2.py \
  --mode tme_current \
  --dataset tests/fixtures/tme_semantic_formal_p2/semantic_robustness_01/sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_p2/semantic_robustness_01/ids.json \
  --output-dir artifacts/evaluations/tme_p2_semantic_robustness_01/current \
  --model gpt-6.1-sol --reasoning-effort medium \
  > /private/tmp/p2-robustness-01/current.log 2>&1

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0 \
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python \
  scripts/evaluation/run_tme_semantic_formal_p2.py \
  --mode tme_semantic_formal \
  --dataset tests/fixtures/tme_semantic_formal_p2/semantic_robustness_01/sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_p2/semantic_robustness_01/ids.json \
  --output-dir artifacts/evaluations/tme_p2_semantic_robustness_01/semantic_formal \
  --model gpt-6.1-sol --reasoning-effort medium \
  > /private/tmp/p2-robustness-01/semantic_formal.log 2>&1

```

Artefatos: [/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01). Métricas e traces: [metrics.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/analysis/metrics.json), [causal_traces.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/artifacts/evaluations/tme_p2_semantic_robustness_01/analysis/causal_traces.json). Scripts auxiliares de construção/agregação estão nos artefatos ignorados e em `/private/tmp/p2-robustness-01/`; não fazem parte do pipeline.

HEAD permanece `4fcc943521a1af566bed68e285462025f86b6b51`. Índice sem alterações. Estado final esperado, conferido após salvar:

```text
?? docs/audits/TME_P2_SEMANTIC_ROBUSTNESS_01.md
?? tests/fixtures/tme_semantic_formal_p2/semantic_robustness_01/
```
