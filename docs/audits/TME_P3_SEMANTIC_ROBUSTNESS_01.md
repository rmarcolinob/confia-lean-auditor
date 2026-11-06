# TME P3 — Semantic Robustness DEV 01

**P3_SEMANTIC_REGRESSION — regressão de segurança localizada, apesar da vantagem agregada de recuperação.** O Semantic reduz o MAE e resgata mais obrigações, mas concede novo crédito material indevido em E02, onde o Current não o concede. O falso crédito decorre da interpretação de abandono pelo LLM, antes da máquina e da reconciliação. O critério pré-execução do manifest veta confirmação de vantagem quando surge falso crédito material adicional ao Current em um caso. Não se está afirmando piora agregada de score: essa melhora é quantificada abaixo.

## 1. Implementação, escopo e execução

SHA congelado e final: **`f335760e9424fb122f24afab6b459f784491aa32`**. Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3`. Os manifests dos dois modos confirmam o mesmo SHA. A única sujeira registrada no início das execuções era o novo diretório de fixtures desta tarefa; não havia alteração do código congelado. O relatório DEV02 já estava commitado no HEAD inicial.

Exatamente 48 textos sintéticos, seis famílias A–F com oito casos cada, executados uma vez por modo. Current: 2026-11-06 02:50:21–02:50:23 UTC. Semantic: 02:50:24–02:56:41 UTC (05/11, 23:50–23:56 em Fortaleza). Model `gpt-6.1-sol`, reasoning_effort `medium`, `CONFIA_TME_SEMANTIC_ENABLED=0`, timeout=180, max_retries=0, max_output_tokens=16000, store=false. Total registrado: 48 chamadas ao extractor no Semantic, zero no Current. Nenhuma repetição de caso ou ajuste de retry.

Não foram alterados implementação, prompt, mapper, registry, guard, checkers, pauta, score closure, máquina nem DEV01/DEV02. Não houve acesso a holdout/gold externo, tuning após resultados, P4 ou commit. Os scripts de construção/agregação e controles estão em artifacts, sem mudanças no código do pipeline.

[Manifest Current](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/tme_current/run_manifest.json) · [Manifest Semantic](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/tme_semantic_formal/run_manifest.json) · [Métricas completas](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/metrics.json).

## 2. Congelamento e expectativas por construção

Congelamento anterior às duas execuções: `2026-11-06T02:50:17.876612+00:00`. Os hashes abaixo foram registrados antes e reconferidos depois. O manifest não inclui seu próprio hash por circularidade; esse hash está no recibo externo pré-execução.

| Arquivo | SHA-256 |
| --- | --- |
| expectations.json | 8d52cabe84a7d4ddbf96f46599dd48df7fc5c4428045f9060086dd49364ec84d |
| sources.json | 56d15fc1c217b0c112f8538a5585c2f7f2db2e88a9b1f1713bae0f29227d753b |
| ids.json | 0e2f78d96c3492340e714e8217d5601f43fb9c92c865b900b7ccae38da0f01c8 |
| construction_receipts.json | a11e2841a14ad08c4b3ca502c632aad25d1c4756d8e74ab6d4595e06d9465068 |
| manifest.json | c5181b9df558961956e407c4e75f1c2cf81a91015bf4fa384532540d58f6a5fa |


[Fixture sources](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_robustness_01/sources.json) · [Expectativas](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_robustness_01/expectations.json) · [Receipts de construção](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_robustness_01/construction_receipts.json) · [Manifest do dataset](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_robustness_01/manifest.json) · [Freeze anterior à execução](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/pre_execution_freeze.json).

Somente sources.json e ids.json são entradas do runner. A schema aceita apenas case_id, problem_id e solution_text; expectativas, receipts e manifest não foram entregues ao extractor. Cada expectativa explicita score, obrigações satisfeitas e não satisfeitas, contextos, conflitos, rotas, parcelas e rationale. Os receipts têm 37.087 bytes, sem dumps de bridge/assessment. Resultados integrais permanecem em artifacts.

As expectativas vêm da pauta e do contrato checker-first: a aceita 1/3 isolado (2); b.space exige 6*6 ou 6², b.different exige 2*5; b.conclusion aceita 11/36 isolado como valor (2), mas uma partição escrita falsa não pode ser reparada pelo número final. Em c, cor e contagem pertencem ao mesmo estado; c.conditionals exige as duas estratégias e ambas as condicionais; c.total exige contexto completo e desenvolvimento autorizado. 1/6 isolado rende zero. A lista completa de referências consta dos receipts; _a/_b/_c são as funções do módulo tme2_p3, executadas por P3Checks.

Expected_obligations_satisfied significa obrigação elegível após contexto, consistência e suficiência; não apenas um fragmento matematicamente verdadeiro. Há 45 pares caso/obrigação legítimos, 41 parcelas de pauta e 77 pontos esperados. Esta é referência sintética por construção, não gold externo nem julgamento derivado da nota observada. A contagem foi congelada antes da primeira execução.

## 3. Distribuição e resultados por família

| Família | Cobertura | N | Exato Current / Semantic | MAE Current / Semantic | Falsos pontos Current / Semantic |
| --- | --- | --- | --- | --- | --- |
| A | Paráfrase/normalização nos três itens | 8 | 0/8 ; 3/8 | 2.750 ; 1.250 | 0 ; 0 |
| B | Representações matemáticas equivalentes | 8 | 3/8 ; 8/8 | 2.000 ; 0.000 | 0 ; 0 |
| C | Crédito parcial/suficiência | 8 | 5/8 ; 7/8 | 1.125 ; 0.250 | 0 ; 0 |
| D | Contexto/hipótese/abandono | 8 | 5/8 ; 8/8 | 1.000 ; 0.000 | 0 ; 0 |
| E | Conflito e guard atômico | 8 | 3/8 ; 7/8 | 1.250 ; 0.250 | 2 ; 2 |
| F | Erro matemático/adversarial | 8 | 7/8 ; 8/8 | 0.250 ; 0.000 | 2 ; 0 |


F inclui F08 em fallback na tabela ALL48; na avaliação do extractor, F tem apenas 7 casos concluídos (7/7 exatos). Não atribuir o oitavo acerto ao SemanticExtractor.

## 4. Métricas de score

Erro = score observado − esperado; MAE = média do módulo; bias = média assinada. Exact exige igualdade exata; within 1 exige módulo ≤1. Under/over são contagens de casos.

| Métrica | Current ALL48 | Semantic ALL48 | Current SUCCESS47 | Semantic SUCCESS47 |
| --- | --- | --- | --- | --- |
| N | 48 | 48 | 47 | 47 |
| Total esperado | 77 | 77 | 77 | 77 |
| Total observado | 14 | 67 | 14 | 67 |
| Exact score (n) | 23 | 41 | 22 | 40 |
| MAE | 1.3958 | 0.2917 | 1.4255 | 0.2979 |
| Bias | -1.3125 | -0.2083 | -1.3404 | -0.2128 |
| Within 1 (n) | 23 | 41 | 22 | 40 |
| Under-score (n) | 24 | 6 | 24 | 6 |
| Over-score (n) | 1 | 1 | 1 | 1 |


Exact: Current 23/48=47,92%; Semantic 41/48=85,42%. SUCCESS47: 22/47=46,81% versus 40/47=85,11%. Within 1 coincide com exact porque não ocorreu erro de módulo 1. Total observado maior não basta para julgar correção; E03 demonstra compensação entre crédito faltante e indevido.

## 5. Obrigações, false credits e missed credits

Predição = conjunto único de obligation_ids com award eligible=true, após reconciliação. TP=predição∩esperado; FP=predição−esperado; FN=esperado−predição. Precision=TP/(TP+FP), recall=TP/(TP+FN). CONTEXT_REJECTED/VERIFIED isolados não são awards. Uma condicional individual elegível pode ser TP sem gerar a parcela all_of conjunta.

| Métrica | Current | Semantic |
| --- | --- | --- |
| TP obligations | 5 | 39 |
| FP obligations | 2 | 1 |
| Missed legitimate obligations (FN) | 40 | 6 |
| Precision | 0.7143 | 0.9750 |
| Recall | 0.1111 | 0.8667 |
| False automatic credit: parcelas | 2 | 1 |
| False automatic credit: pontos | 4 | 2 |
| Missed credit: parcelas | 36 | 6 |
| Missed credit: pontos | 67 | 12 |


Essas contagens de obrigações/parcelas coincidem em ALL48 e SUCCESS47, pois F08 tem expectativa zero e nenhum award. Precision: 71,43%→97,50%; recall: 11,11%→86,67%. Há ganho agregado, mas precision não é 100%.

| Modo/caso | Parcela indevida | Pontos | Causa |
| --- | --- | --- | --- |
| Current/E03 | b.same | 2 | Lê {6} tipado, perde prosa contraditória do quinto. Score total 2 coincide com esperado, mas falta a.count e sobra b.same. |
| Current/F03 | b.different | 2 | 1*10=10 avaliado como valor 10 pelo baseline; não valida relação 2*5 requerida no contrato fortalecido. |
| Semantic/E02 | b.same | 2 | Primeiro claim contraditório marcado abandoned=true; não chega à máquina nem ao guard. |


O Semantic tem menos falso crédito total (2 versus 4 pontos), mas introduz um falso crédito em um caso que o Current não premiava. A falha local de segurança é material e não é apagada pelo ganho médio. Não é um award direto do claim falso: a exclusividade do sexto é premiada porque o claim incompatível foi descartado antes da reconciliação.

| Missed Semantic | Obrigação | Pontos perdidos | Causa |
| --- | --- | --- | --- |
| A01 | a.bottom_white_count | 2 | white_count_not_bound_to_written_quantity: duas das seis ... brancas não casa com o vínculo local. |
| A02 | a.first_white_probability | 2 | representation_not_written_or_truncated: uma em três → 1/3 não é aceito no texto normalizado. |
| A03 | b.ordered_pairs | 2 | unsupported_checker_payload: extractor normalizou a frase inteira em vez do payload 6*6=36. |
| A06 | c.strategy_case_1 | 2 | subject_not_uniquely_bound_to_source_clause: duas cláusulas do mesmo estado no mesmo span. |
| A07 | c.strategy_case_2 | 2 | Mesmo problema de duas cláusulas para cor/contagem do caso 2. |
| C04 | b.second_white_probability | 2 | same_item_required: envelope inclui b), embora item_id=b esteja correto. |


Current perde 36 parcelas/67 pontos legítimos, sobretudo por ausência de claims tipados a partir da prosa. A discriminação de todos os FN por caso está na tabela pareada e no anexo causal. As cinco perdas de A não foram reclassificadas como zero esperado após os resultados.

## 6. Comparação pareada completa

Winner é quem tem menor erro absoluto contra a expectativa congelada. Semantic melhor=19, Current melhor=1, empate=28 (ALL48). Em SUCCESS47: 19, 1, 27. E02 empata em erro absoluto (2) apesar de falhas diferentes: Current perde crédito legítimo; Semantic concede crédito indevido.

| case_id | Current | Semantic | Expected | Erro absoluto C | Erro absoluto S | Winner |
| --- | --- | --- | --- | --- | --- | --- |
| p3_rob_a01 | 0 | 0 | 2 | 2 | 2 | tie |
| p3_rob_a02 | 0 | 0 | 2 | 2 | 2 | tie |
| p3_rob_a03 | 0 | 0 | 2 | 2 | 2 | tie |
| p3_rob_a04 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_a05 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_a06 | 0 | 0 | 2 | 2 | 2 | tie |
| p3_rob_a07 | 0 | 0 | 2 | 2 | 2 | tie |
| p3_rob_a08 | 0 | 8 | 8 | 8 | 0 | Semantic |
| p3_rob_b01 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_b02 | 2 | 2 | 2 | 0 | 0 | tie |
| p3_rob_b03 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_b04 | 2 | 2 | 2 | 0 | 0 | tie |
| p3_rob_b05 | 2 | 2 | 2 | 0 | 0 | tie |
| p3_rob_b06 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_b07 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_b08 | 0 | 8 | 8 | 8 | 0 | Semantic |
| p3_rob_c01 | 2 | 2 | 2 | 0 | 0 | tie |
| p3_rob_c02 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_c03 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_c04 | 2 | 0 | 2 | 0 | 2 | Current |
| p3_rob_c05 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_c06 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_c07 | 0 | 5 | 5 | 5 | 0 | Semantic |
| p3_rob_c08 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_d01 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_d02 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_d03 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_d04 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_d05 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_d06 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_d07 | 0 | 4 | 4 | 4 | 0 | Semantic |
| p3_rob_d08 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_e01 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_e02 | 0 | 4 | 2 | 2 | 2 | tie |
| p3_rob_e03 | 2 | 2 | 2 | 0 | 0 | tie |
| p3_rob_e04 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_e05 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_e06 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_e07 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_e08 | 0 | 2 | 2 | 2 | 0 | Semantic |
| p3_rob_f01 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_f02 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_f03 | 2 | 0 | 0 | 2 | 0 | Semantic |
| p3_rob_f04 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_f05 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_f06 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_f07 | 0 | 0 | 0 | 0 | 0 | tie |
| p3_rob_f08 | 0 | 0 | 0 | 0 | 0 | tie (fallback) |


## 7. Conflitos e ordem textual

Seis casos com conflitos materiais predefinidos (E01–E06). Detectar exige evento CONFLICTING_EVIDENCE não resolvido na família esperada; suprimir exige ausência de award dessa família. Zero pontos por não extrair nada não é detecção de conflito.

| Métrica | Current | Semantic |
| --- | --- | --- |
| Conflitos detectados | 1/6 | 5/6 |
| Famílias conflitantes sem award | 5/6 | 5/6 |
| Conjunto de conflitos correto por caso | 43/48 | 47/48 |
| Refutações esperadas preservadas | 2/13 | 12/13 |


Accuracy estrita de detecção nos positivos: 16,67% versus 83,33%; supressão=83,33% em ambos, em casos diferentes. O acerto do conjunto de conflitos (incluindo casos negativos) é 89,58% versus 97,92%, mas não substitui a taxa nos seis desafios. A única refutação esperada ausente do Semantic é E02. F03 é insuficiência relacional e não foi contado como refutação obrigatória.

**E02, cadeia da falha:** “o quinto também” → normalized_claim em prosa, assertion_status=abandoned, abandoned=true → b.same_compartment → mapper nonasserted_or_unattributed_context → CONTEXT_REJECTED → sem checker matemático/sem guard → positivo {6} DETERMINISTIC_VERIFIED/sufficiency=true → b.same=2. a.count=2 permanece; total=4 contra esperado=2. O texto “Na verdade” não foi registrado na expectativa como abandono explícito, seguindo o contrato/teste congelado de ordem inversa. Não se alterou essa política para acomodar a interpretação do modelo.

Na direção direta E01, o falso {5} chega ao checker regular, gera DETERMINISTIC_FAILED e bloqueia b.same. E03 também usa o caminho regular. E05 preserva 11/36 versus 12/36; E06 bloqueia estratégias preta/cinza incompatíveis no mesmo estado. E07/E08 não devem criar conflito material: são abandono explícito e terceiro não adotado.

## 8. Atomic guard: esperado versus observado

| Caso | Caminho esperado antes do run | Observado | Resultado |
| --- | --- | --- | --- |
| E01 | Regular se conjunto; guard se prosa incompatível | Regular; guard=0 | Conflito preservado |
| E02 | Regular se conjunto; guard se prosa incompatível | Nenhum: abandoned=true | Falha de contexto anterior ao guard; falso crédito |
| E03 | Regular se conjunto; guard se prosa incompatível | Regular; guard=0 | Conflito preservado |
| E04 | Guard atômico para elipse parcial | Guard=1, DETERMINISTIC_FAILED | Conflito preservado; a.count=2 |
| E05/E06 | Checker regular | Regular | Conflitos preservados |
| E07/E08 | Nenhum por contexto rejeitado | Nenhum; CONTEXT_REJECTED | Crédito válido preservado |


Em E04, o LLM forneceu {5,6} sobre o envelope de dois spans: “somente o sexto” e “O quinto também.”. O mapper rejeitou set_members_not_written. O novo caminho não usou esse conjunto para conceder pontos: derivou o átomo membership_claim(compartment=5, relation=same_compartment_second_white) do token literal quinto, offsets [104,110), consultou o modelo e obteve DETERMINISTIC_FAILED. Guard_only=true, award_eligible=false, sufficiency=false. Há exatamente um evento de guard no run real, e ele não gerou crédito.

O desafio atomic-only E04 foi observado (1/1). Nos quatro casos E01–E04, preservação da contradição=3/4; não se pode transformar os casos resolvidos pelo checker regular em “sucesso do guard”. O guard respeitou os flags de contexto em E02, mas esses flags estavam errados em relação à referência congelada.

Controles adicionais pré-declarados no manifest, usando somente os mesmos textos E01–E04/E07–E08: 12 avaliações sem API (payload de conjunto versus payload em prosa), todas PASS. Foram observados 5 acionamentos esperados de guard e 7 ausências esperadas; bloqueios/contexto e score=2 conferiram nos 12. Esses controles mantêm os claims como asserted para testar inclusive veto contextual independente no texto. Não são novos casos do dataset, não são amostras de saída do LLM, e não entram em ALL48/SUCCESS47. O helper foi preparado antes de observar os resultados reais da família E.

[Resumo dos controles](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/controlled_guards/summary.json) · [Script dos controles](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/controlled_guards.py).

## 9. Contexto, hipóteses e localidade

Há nove spans inválidos pré-anotados: D01–D07 e E07–E08. Segurança contextual = não usar o span inválido para award/veto matemático; no Semantic também se confere ausência de mapping aceito. Semantic: 9/9 rejeições explícitas CONTEXT_REJECTED, sem contaminação indevida; Current: 9/9 sem crédito por esses spans, sendo 3 com rejeição de origem, 5 omitidos e 1 registro sem crédito. Não atribuir ao baseline nove decisões explícitas de contexto.

A supressão dos inválidos é 100% nesse denominador, não “acurácia contextual geral”. E02 evidencia falso abandono de uma afirmação material, fora dos nove spans que deveriam ser rejeitados. D03 preserva a correção explicitamente delimitada; D07 preserva a.count+a.probability=4 após parágrafo hipotético; D08 preserva a condição legítima de caso (estratégia e condicional elegíveis, 2 pontos de estratégia). As duas ordens de E01/E02 não tiveram comportamento equivalente.

## 10. Status de checkers e autoridade matemática

Duas contagens não intercambiáveis: status principal de verification_results e formal_status dos mesmos registros. COMPOSITE_VERIFIED pode conter aritmética FORMAL_VERIFIED; não somar essas colunas como chamadas distintas. O guard e os eventos de reconciliação são contados à parte.

| Status | Principal Current | Principal Semantic | Ciclo formal Current | Ciclo formal Semantic |
| --- | --- | --- | --- | --- |
| FORMAL_VERIFIED | 0 | 1 | 0 | 10 |
| FORMAL_REFUTED | 0 | 0 | 0 | 0 |
| FORMAL_UNPROVED | 0 | 0 | 0 | 0 |
| FORMAL_NOT_ATTEMPTED | 0 | 0 | 11 | 75 |
| FORMAL_ERROR | 0 | 0 | 0 | 0 |
| DETERMINISTIC_VERIFIED | 8 | 21 | — | — |
| DETERMINISTIC_FAILED | 3 | 4 | — | — |
| COMPOSITE_VERIFIED | 0 | 24 | — | — |
| COMPOSITE_INCOMPLETE | 0 | 6 | — | — |
| COMPOSITE_FAILED | 0 | 9 | — | — |
| CONTEXT_REJECTED | 0 | 20 | — | — |
| CONFLICTING_EVIDENCE | 0 | 0 | — | — |


Reconciliação: CONFLICTING_EVIDENCE=1 Current e 5 Semantic, fora da tabela principal (zero nessa chave em verification_results). Guard: um DETERMINISTIC_FAILED adicional, fora dos quatro principais. Há 11 resultados principais no Current e 85 no Semantic. CONTEXT_REJECTED=20 inclui também rejeições de formato; não são vinte hipóteses inválidas.

As dez ocorrências de FORMAL_VERIFIED no ciclo formal têm recibos de igualdade racional compilada; podem compartilhar a mesma igualdade em mais de uma obrigação. FORMAL_REFUTED/UNPROVED/ERROR=0 não significa que os erros matemáticos ficaram sem refutação: a matemática de estados/partições foi tratada deterministicamente. Exemplo F05: (9+2)/36=11/36 é igualdade verdadeira, mas partição falsa; COMPOSITE_FAILED veta crédito. F03: 1*10=10 é aritmética verdadeira, porém relação de contagem insuficiente; COMPOSITE_INCOMPLETE, zero no Semantic.

## 11. Fallbacks e erros técnicos

**Um fallback: p3_rob_f08.** A chamada retornou estado não completed, e o extractor registrou ValueError:extractor_incomplete_or_refused. Não há raw_output útil nem EvidenceUnits vinculadas. Uso registrado: 16.000 output tokens (limite configurado), 2.873 input tokens; latência ~96,66 s. Atingir o limite é evidência compatível com incompletude, mas o recibo não preserva incomplete_details; não se afirma uma causa mais específica nem se inventa recusa de segurança.

Modo efetivo TME_CURRENT_FALLBACK; score=0, esperado=0. Esse acerto pertence ao baseline. ALL48 inclui o fallback operacional; SUCCESS47 o exclui dos dois lados pareados. Nenhuma conclusão positiva ou negativa sobre a qualidade da interpretação do extractor usa F08. A família adversarial tem 7 sucessos de extração, não 8.

technical_uncertainty=0 em ambos os modos; erros formais/determinísticos de checker=0. Houve **1 falha operacional de extração**, separada desses indicadores, com fallback. Não chamar a execução de “zero falhas técnicas” sem essa distinção. Não houve mudança de timeout, retries ou reexecução.

## 12. Análise causal e rastreabilidade

[Anexo causal completo dos 48 casos](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/causal_chains.md) reconstrói fonte integral, claim/subject/contexto, obligation, effective_route, checker/subcomponentes, status/formal_status, sufficiency, elegibilidade, conflitos e parcelas finais para os dois modos. [Análise estruturada](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/case_analysis.json) e [Classificações](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/classifications.json) permitem conferir os mesmos dados sem dumps redundantes de certificados.

Síntese das divergências relevantes (a cadeia integral está no anexo):

| Caso | Classificação | Efeito |
| --- | --- | --- |
| p3_rob_a01 | BASELINE_UNDER_CREDIT, PAYLOAD_MISMATCH | C=0; S=0; esperado=2 |
| p3_rob_a02 | BASELINE_UNDER_CREDIT, PAYLOAD_MISMATCH | C=0; S=0; esperado=2 |
| p3_rob_a03 | BASELINE_UNDER_CREDIT, PAYLOAD_MISMATCH | C=0; S=0; esperado=2 |
| p3_rob_a04 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, NORMALIZATION_GAIN | C=0; S=2; esperado=2 |
| p3_rob_a05 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, NORMALIZATION_GAIN | C=0; S=2; esperado=2 |
| p3_rob_a06 | BASELINE_UNDER_CREDIT, PAYLOAD_MISMATCH | C=0; S=0; esperado=2 |
| p3_rob_a07 | BASELINE_UNDER_CREDIT, PAYLOAD_MISMATCH | C=0; S=0; esperado=2 |
| p3_rob_a08 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, NORMALIZATION_GAIN | C=0; S=8; esperado=8 |
| p3_rob_b01 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN | C=0; S=2; esperado=2 |
| p3_rob_b03 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, NORMALIZATION_GAIN | C=0; S=2; esperado=2 |
| p3_rob_b06 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN | C=0; S=2; esperado=2 |
| p3_rob_b07 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN | C=0; S=2; esperado=2 |
| p3_rob_b08 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN | C=0; S=8; esperado=8 |
| p3_rob_c02 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN | C=0; S=2; esperado=2 |
| p3_rob_c04 | PAYLOAD_MISMATCH, CURRENT_BETTER | C=2; S=0; esperado=2 |
| p3_rob_c06 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN | C=0; S=2; esperado=2 |
| p3_rob_c07 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN | C=0; S=5; esperado=5 |
| p3_rob_d03 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN, CONTEXT_SUPPRESSION | C=0; S=2; esperado=2 |
| p3_rob_d07 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN, CONTEXT_SUPPRESSION | C=0; S=4; esperado=4 |
| p3_rob_d08 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN | C=0; S=2; esperado=2 |
| p3_rob_e01 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN, CONFLICT_SUPPRESSION | C=0; S=2; esperado=2 |
| p3_rob_e02 | SEMANTIC_FALSE_CREDIT, BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN | C=0; S=4; esperado=2 |
| p3_rob_e03 | BASELINE_OVER_CREDIT, BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN, CONFLICT_SUPPRESSION | C=2; S=2; esperado=2 |
| p3_rob_e04 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN, CONFLICT_SUPPRESSION, ATOMIC_GUARD_SUCCESS | C=0; S=2; esperado=2 |
| p3_rob_e07 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN, CONTEXT_SUPPRESSION | C=0; S=2; esperado=2 |
| p3_rob_e08 | BASELINE_UNDER_CREDIT, SEMANTIC_RESCUE, STRUCTURE_GAIN, CONTEXT_SUPPRESSION | C=0; S=2; esperado=2 |
| p3_rob_f03 | BASELINE_OVER_CREDIT | C=2; S=0; esperado=0 |
| p3_rob_f08 | FALLBACK | C=0; S=0; esperado=0 |


SEMANTIC_RESCUE denota obrigação legítima adicional efetivamente premiada, não uma expressão identificada sem checker. NORMALIZATION_GAIN/STRUCTURE_GAIN são etiquetas de evidência observável, não estimativa de efeito causal aleatorizado. E03/F03 são BASELINE_OVER_CREDIT; E02 SEMANTIC_FALSE_CREDIT; C04 CURRENT_BETTER por limite do span; F08 FALLBACK. OTHER inclui os controles concordantes sem resgate/falha e as insuficiências corretamente não premiadas.

## 13. Limitações e conclusão

São 48 casos sintéticos dirigidos, com expectativas internas por construção e forte concentração nos contratos conhecidos. Não há gold externo, amostragem probabilística, holdout ou inferência de acurácia geral. B02/C01 repetem intencionalmente 1/3 isolado; algumas expressões já eram conhecidas em DEV. Esta bateria tem 12 das 13 famílias de obrigação como alvo; não exercita o método alternativo completo de seis ramos (b.alternative_complete), mantido como negativo nas expectativas.

As expectativas não foram alteradas. Os oito casos de cada família permanecem DEV observado após esta execução e não podem ser promovidos a avaliação independente. A bateria demonstra ganhos agregados e também limites lexicais, de envelope e de interpretação contextual. Nenhuma correção foi implementada nesta tarefa.

Resposta à pergunta: com checkers congelados, o Semantic recuperou muito mais obrigações legítimas (39 versus 5 TP), com menor falso crédito agregado (2 versus 4 pontos), porém não garantiu preservação de contradição na ordem inversa. O guard funcionou em E04 e nos controles, mas não pode recuperar uma afirmação que chega marcada indevidamente como abandonada. O critério de segurança por caso impede declarar vantagem confirmada sem registrar essa regressão material.

Git: SHA permanece f335760e9424fb122f24afab6b459f784491aa32; arquivos preexistentes monitorados preservados, fixtures DEV01/DEV02 idênticas. Novidades rastreáveis esperadas: o diretório semantic_robustness_01 com cinco JSON e este relatório. Artifacts contém execução, métricas, cadeias e scripts; sem stage/commit.

**P3_SEMANTIC_REGRESSION**
