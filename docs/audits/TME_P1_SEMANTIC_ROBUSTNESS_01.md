# P1 — robustez semântica DEV controlada, experimento 01

Data: **2026-11-05** (America/Fortaleza). Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1`.

**Veredito pelo critério pré-registrado: P1_SEMANTIC_ADVANTAGE_CONFIRMED.** Resultado limitado a estes 36 casos sintéticos DEV e a uma execução por modo; não constitui estimativa de desempenho no holdout ou em uma população de respostas.

## 1. Estado inicial, execução e preservação

Antes da construção foram executados `git status --short` (saída vazia: worktree limpo) e `git rev-parse HEAD`: **`377427a93a44208e430f9a014b0b062320054083`**. Esse SHA foi usado nos dois modos. Nenhum arquivo de código do pipeline foi alterado, nenhum prompt/checker/pauta/registry/AwardGate foi ajustado e nenhum commit foi feito.

Os dois runners existentes foram executados com `gpt-6.1-sol`, reasoning `medium`, Lean habilitado e os mesmos 36 IDs/fontes. TME_CURRENT conserva seu caminho determinístico existente; a configuração de modelo não força uma chamada LLM nesse modo. TME_SEMANTIC_FORMAL usa seu extractor e, quando aplicável, o checker semântico secundário existente. Não houve gold externo, holdout ou expansão para P2.

Diretórios de resultados, sem sobrescrever os pilotos anteriores:

- [semantic_robustness_current_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_current_01).

- [semantic_robustness_formal_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_formal_01).

- [semantic_robustness_analysis_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_analysis_01).


Comandos de avaliação executados (com streams capturados nos logs temporários):

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1
export PYTHONPATH="$PWD/app"
export PYTHONDONTWRITEBYTECODE=1
export CONFIA_TME_SEMANTIC_ENABLED=0
ROBUSTNESS_PYTHON=/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python

"$ROBUSTNESS_PYTHON" -m scripts.evaluation.run_tme_semantic_formal_c1 \
  --mode tme_current \
  --dataset tests/fixtures/tme_semantic_formal_c1/semantic_robustness_01/sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_c1/semantic_robustness_01/ids.json \
  --output-dir artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_current_01 \
  --model gpt-6.1-sol --reasoning-effort medium

"$ROBUSTNESS_PYTHON" -m scripts.evaluation.run_tme_semantic_formal_c1 \
  --mode tme_semantic_formal \
  --dataset tests/fixtures/tme_semantic_formal_c1/semantic_robustness_01/sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_c1/semantic_robustness_01/ids.json \
  --output-dir artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_formal_01 \
  --model gpt-6.1-sol --reasoning-effort medium
```

A rede/API foi usada somente na execução autorizada. Ambos os processos terminaram com exit code 0; seus 36 resultados têm nota numérica. Os stdout/stderr combinados contêm os sumários, sem traceback. Cópias permanentes dos streams estão em semantic_robustness_analysis_01/current_runner_stdout.log e formal_runner_stdout.log. Scripts auxiliares de construção/agregação ficaram em `/private/tmp/confia-p1-robustness-01/`; não foram incorporados ao pipeline.

## 2. Dataset, expectativas e congelamento

As entradas do runner têm exclusivamente `{case_id, problem_id, solution_text}`. As expectativas, famílias, referências canônicas e motivos pedagógicos ficam em arquivos separados, que o runner não lê e que o LLM não recebe. A nota esperada é calculada pelo **PautaEngine existente** a partir de fatos dos **checkers existentes**, incluindo Lean real nas referências que o exigem; não foi atribuída por um LLM corretor.

A construção usa as soluções P1 conhecidas como referências matemáticas. Variações de linguagem/ordem recebem os mesmos fatos da referência quando preservam seu significado. Nos casos E, a referência contém apenas o conteúdo explicitamente adotado; nos F, apenas o conteúdo pertinente. O complemento dos 21 IDs registra expected_obligations_not_satisfied; “não satisfeita” engloba ausência e refutação, sem confundir esses estados no resultado do checker.

Houve uma conferência de construção **antes de executar qualquer um dos 36 casos**: em D02, o coletor do baseline omitia a expressão isolada `731-137`. Sua expectativa foi então calculada passando esse payload escrito ao checker existente via projeção canônica, obtendo identificação e montagem, com 1 ponto pela pauta. Assim a limitação de extração do baseline não virou a definição da expectativa. Os 36 textos e IDs não mudaram. O manifesto final registra construction_revision=2; depois desse congelamento final, nenhum caso, expectativa ou código mudou, inclusive após observar os resultados.

| arquivo congelado | SHA-256 dos bytes |
|---|---|
| [sources.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/tests/fixtures/tme_semantic_formal_c1/semantic_robustness_01/sources.json) | `9002b4adab0d4a9c7c1b90e5fea1dcb78e0e3aea572cabd2239b8c2b8b970b36` |
| [ids.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/tests/fixtures/tme_semantic_formal_c1/semantic_robustness_01/ids.json) | `9bb6e827a66ad74d4d39bd592411821401977b17c8de59e3b493b81f322009d9` |
| [expectations.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/tests/fixtures/tme_semantic_formal_c1/semantic_robustness_01/expectations.json) | `e60c4ad3b245f1f86f940003823f630c11f456f2b9e0a7b3e5167decbc1de33e` |
| [construction_receipts.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/tests/fixtures/tme_semantic_formal_c1/semantic_robustness_01/construction_receipts.json) | `b5fdaf2ad7df39d996b588310820e24d1cdb8b0efe8a7c4d3e7546f7b093b201` |
| [manifest.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/tests/fixtures/tme_semantic_formal_c1/semantic_robustness_01/manifest.json) | `bc9bf8e3e13c38babaca40355f20313c926eef8b0a7c90781f0cc741f471dd11` |


Os hashes de configuração e das fontes registrados pelos runners também são conferidos. Os hashes acima são dos bytes dos arquivos; os input_hashes do runner usam sua serialização JSON canônica e, por isso, não são confundidos com hashes de arquivo.

| família | descrição | casos |
|---|---|---|
| A | Paráfrase linguística | 6 |
| B | Representação matemática equivalente | 6 |
| C | Ordem dos passos/itens | 6 |
| D | Crédito parcial | 6 |
| E | Contexto negativo | 6 |
| F | Evidência irrelevante | 6 |


São 36 casos, incluindo um caso composto de quatro itens. A igualdade invertida de B05 é do item d, cujo checker admite ambos os lados; não se presumiu que inverter sintaticamente qualquer igualdade de a preserva o contrato. As descrições pedagógicas individuais e referências canônicas estão em expectations.json, com as contas de pauta auditáveis em construction_receipts.json.

## 3. Métricas: definições pré-registradas

- **Exact score:** igualdade numérica com expected_score_by_construction; **MAE:** média do erro absoluto em pontos.
- **Obrigações detectadas:** conjunto de IDs com effective_status=supported no assessment da pauta; considera critérios satisfeitos mesmo quando pertencem a uma faixa alternativa não escolhida. Contagens micro agregam pares caso/obrigação, não IDs únicos globais.
- **Recall:** TP/(TP+FN); **precision:** TP/(TP+FP). Denominador zero é n/a.
- **False credit:** pontos excedentes `max(score−expected,0)` e, separadamente, obrigações positivas indevidas. Nota correta pode coexistir com falso suporte a critério não pago.
- **Missed legitimate credit:** pontos faltantes `max(expected−score,0)` e obrigações esperadas não detectadas. Pontos de blocos all_of não são duplicados por obrigação.
- **Context rejection accuracy:** seis trechos negativos de E; sucesso significa nenhum suporte efetivo ligado ao trecho rejeitado. Não extrair um claim não adotado conta como supressão segura. Rejeição explícita e ausência de extração são distinguidas na análise; a métrica não exige um rótulo CONTEXT_REJECTED.
- Rotas/status contam resultados de verificação, não necessariamente subprocessos Lean. FORMAL_NOT_ATTEMPTED continua separado de FORMAL_UNPROVED, erro e refutação.

Critério de veredito congelado antes da execução: vantagem exige MAE estritamente menor, exact score não inferior, soma de pontos excedentes não maior e supressão contextual não inferior. Com MAE apenas não maior e as demais condições, noninferior only. Caso contrário, semantic regression. Esse critério não é um teste de significância estatística.

## 4. Resultado global

| métrica | TME_CURRENT | TME_SEMANTIC_FORMAL |
|---|---|---|
| Casos | 36 | 36 |
| Exact score (n) | 29 | 30 |
| Exact score (%) | 80.56% | 83.33% |
| MAE (pontos) | 0.5278 | 0.3611 |
| Obrigações esperadas | 95 | 95 |
| Obrigações detectadas | 75 | 83 |
| TP | 75 | 83 |
| FP de obrigação | 0 | 0 |
| FN de obrigação | 20 | 12 |
| Obligation recall | 78.95% | 87.37% |
| Obligation precision | 100.00% | 100.00% |
| Casos com pontos excedentes | 0 | 0 |
| Pontos excedentes | 0.0000 | 0.0000 |
| Casos com obrigação FP | 0 | 0 |
| Casos com pontos faltantes | 7 | 6 |
| Pontos faltantes | 19.0000 | 13.0000 |
| Contextos negativos suprimidos | 6 | 6 |
| Context rejection accuracy | 100.00% | 100.00% |
| Claims LLM validados e consumidos | 0 | 74 |
| Fallbacks | 0 | 3 |
| Casos com technical_uncertainty (flag nativo) | 0 | 0 |
| Resultados FORMAL_ERROR | 0 | 0 |
| Review recommended | 35 | 35 |
| Latência média por caso (s) | 2.0912 | 10.3471 |
| FORMAL_VERIFIED | 8 | 8 |
| FORMAL_REFUTED | 1 | 1 |
| FORMAL_UNPROVED | 0 | 0 |
| FORMAL_NOT_ATTEMPTED | 0 | 4 |
| FORMAL_ERROR | 0 | 0 |
| DETERMINISTIC_VERIFIED | 67 | 74 |
| DETERMINISTIC_FAILED | 11 | 26 |
| SEMANTIC_SUPPORTED | 0 | 1 |
| SEMANTIC_INSUFFICIENT | 0 | 0 |
| CONTEXT_REJECTED | 0 | 10 |
| Falhas operacionais de extração | 0 | 3 |
| Tentativas Lean confirmadas | 9 | 9 |


“Claims LLM validados e consumidos = 0” no Current não significa ausência de registros matemáticos locais: é a métrica estrutural do runner para extracted_evidence. Os fatos determinísticos/formais do baseline aparecem nas contagens de verificação e no assessment. Os 74 claims do C1 são os aceitos em extracted_evidence; saídas inválidas/incompletas dos três fallbacks ficam fora dessa contagem. As três falhas operacionais são discriminadas na seção 9 e não estão incluídas no flag nativo technical_uncertainty.

## 5. Resultados por família A–F

| família | modo | exact | MAE | detectadas/esperadas | recall | precision | excesso pts | falta pts | context accuracy | fallbacks | flag técnico nativo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | Current | 1/6 | 2.8333 | 2/19 | 10.53% | 100.00% | 0.0 | 17.0 | n/a | 0 | 0 |
| A | Semantic Formal | 1/6 | 2.0000 | 8/19 | 42.11% | 100.00% | 0.0 | 12.0 | n/a | 0 | 0 |
| B | Current | 6/6 | 0.0000 | 14/14 | 100.00% | 100.00% | 0.0 | 0.0 | n/a | 0 | 0 |
| B | Semantic Formal | 6/6 | 0.0000 | 14/14 | 100.00% | 100.00% | 0.0 | 0.0 | n/a | 0 | 0 |
| C | Current | 6/6 | 0.0000 | 44/44 | 100.00% | 100.00% | 0.0 | 0.0 | n/a | 0 | 0 |
| C | Semantic Formal | 6/6 | 0.0000 | 44/44 | 100.00% | 100.00% | 0.0 | 0.0 | n/a | 0 | 0 |
| D | Current | 5/6 | 0.1667 | 9/11 | 81.82% | 100.00% | 0.0 | 1.0 | n/a | 0 | 0 |
| D | Semantic Formal | 6/6 | 0.0000 | 11/11 | 100.00% | 100.00% | 0.0 | 0.0 | n/a | 0 | 0 |
| E | Current | 5/6 | 0.1667 | 0/1 | 0.00% | n/a | 0.0 | 1.0 | 100.00% | 0 | 0 |
| E | Semantic Formal | 5/6 | 0.1667 | 0/1 | 0.00% | n/a | 0.0 | 1.0 | 100.00% | 2 | 0 |
| F | Current | 6/6 | 0.0000 | 6/6 | 100.00% | 100.00% | 0.0 | 0.0 | n/a | 0 | 0 |
| F | Semantic Formal | 6/6 | 0.0000 | 6/6 | 100.00% | 100.00% | 0.0 | 0.0 | n/a | 1 | 0 |


| família | modo | claims LLM | F_VERIFIED | F_REFUTED | F_NOT_ATTEMPTED | D_VERIFIED | D_FAILED | S_SUPPORTED |
|---|---|---|---|---|---|---|---|---|
| A | Current | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| A | Semantic Formal | 10 | 0 | 0 | 4 | 7 | 10 | 1 |
| B | Current | 0 | 2 | 0 | 0 | 12 | 0 | 0 |
| B | Semantic Formal | 10 | 2 | 0 | 0 | 12 | 1 | 0 |
| C | Current | 0 | 4 | 0 | 0 | 40 | 3 | 0 |
| C | Semantic Formal | 33 | 4 | 0 | 0 | 40 | 5 | 0 |
| D | Current | 0 | 0 | 1 | 0 | 9 | 3 | 0 |
| D | Semantic Formal | 7 | 0 | 1 | 0 | 11 | 3 | 0 |
| E | Current | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E | Semantic Formal | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| F | Current | 0 | 2 | 0 | 0 | 4 | 5 | 0 |
| F | Semantic Formal | 9 | 2 | 0 | 0 | 4 | 7 | 0 |


Falhas de extração por família no C1: A=0, B=0, C=0, D=0, E=2 e F=1; Current=0 em todas. FORMAL_ERROR=0, FORMAL_UNPROVED=0 e SEMANTIC_INSUFFICIENT=0 em todas as famílias e modos. CONTEXT_REJECTED no C1: E=8 e F=2; zero nas demais e no Current.

## 6. Os 36 resultados e expectativas

| caso | família | expected por construção | Current | Semantic Formal | classificação da diferença |
|---|---|---|---|---|---|
| A01_menos | A | 3.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| A02_subtraindo | A | 3.0000 | 0.0000 | 1.0000 | SEMANTIC_RESCUE, MISSED_CREDIT |
| A03_resultado_por_extenso | A | 3.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| A04_invertido_em_prosa | A | 2.0000 | 2.0000 | 0.0000 | CURRENT_BETTER, MISSED_CREDIT |
| A05_lista_em_prosa | A | 5.0000 | 1.0000 | 5.0000 | NORMALIZATION_GAIN |
| A06_contagem_em_prosa | A | 4.0000 | 0.0000 | 2.0000 | NORMALIZATION_GAIN, MISSED_CREDIT |
| B01_sinais_espacos | B | 3.0000 | 3.0000 | 3.0000 | empate de nota e obrigações/contexto |
| B02_posicional_reordenada | B | 2.0000 | 2.0000 | 2.0000 | empate de nota e obrigações/contexto |
| B03_algebra_equivalente | B | 5.0000 | 5.0000 | 5.0000 | empate de nota e obrigações/contexto |
| B04_formula_sinal | B | 1.0000 | 1.0000 | 1.0000 | empate de nota e obrigações/contexto |
| B05_equacoes_simetrizadas | B | 2.0000 | 2.0000 | 2.0000 | empate de nota e obrigações/contexto |
| B06_produto_comutado | B | 4.0000 | 4.0000 | 4.0000 | empate de nota e obrigações/contexto |
| C01_b_passos_reordenados | C | 5.0000 | 5.0000 | 5.0000 | empate de nota e obrigações/contexto |
| C02_c_lista_primeiro | C | 6.0000 | 6.0000 | 6.0000 | empate de nota e obrigações/contexto |
| C03_d_produto_primeiro | C | 6.0000 | 6.0000 | 6.0000 | empate de nota e obrigações/contexto |
| C04_itens_d_b_a_c | C | 20.0000 | 20.0000 | 20.0000 | empate de nota e obrigações/contexto |
| C05_c_parcial_lista_primeiro | C | 4.0000 | 4.0000 | 4.0000 | empate de nota e obrigações/contexto |
| C06_d_contagem_reordenada | C | 4.0000 | 4.0000 | 4.0000 | empate de nota e obrigações/contexto |
| D01_identificacao | D | 1.0000 | 1.0000 | 1.0000 | empate de nota e obrigações/contexto |
| D02_montagem_sem_resultado | D | 1.0000 | 0.0000 | 1.0000 | NORMALIZATION_GAIN |
| D03_erro_aritmetico | D | 2.0000 | 2.0000 | 2.0000 | empate de nota e obrigações/contexto |
| D04_somente_invertido | D | 2.0000 | 2.0000 | 2.0000 | empate de nota e obrigações/contexto |
| D05_um_valor | D | 1.0000 | 1.0000 | 1.0000 | empate de nota e obrigações/contexto |
| D06_equacao_e_diferenca | D | 2.0000 | 2.0000 | 2.0000 | empate de nota e obrigações/contexto |
| E01_hipotese | E | 0.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| E02_negacao | E | 0.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| E03_abandono | E | 0.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| E04_citacao | E | 0.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| E05_rejeicao_explicita | E | 0.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| E06_misto_adotado_descartado | E | 1.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| F01_soma_verdadeira | F | 0.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| F02_identidade_alheia | F | 0.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| F03_quadrados | F | 0.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| F04_diferenca_numerica | F | 0.0000 | 0.0000 | 0.0000 | empate de nota e obrigações/contexto |
| F05_conta_correta_com_ruido | F | 3.0000 | 3.0000 | 3.0000 | empate de nota e obrigações/contexto |
| F06_contagem_com_ruido | F | 4.0000 | 4.0000 | 4.0000 | empate de nota e obrigações/contexto |


Classificações podem coexistir: uma normalização pode recuperar parte do crédito e ainda deixar MISSED_CREDIT. SEMANTIC_RESCUE exige suporte semântico efetivo; NORMALIZATION_GAIN identifica recuperação pelo caminho matemático. CURRENT_BETTER indica menor erro de nota do baseline. Diferenças de obrigações/contexto com nota igual recebem OTHER e os alertas aplicáveis. Não se chama toda diferença de ganho semântico.

## 7. Análise causal das diferenças

As cadeias abaixo são extraídas dos artefatos completos; `paid_rules` conserva os blocos pagos e evita repartir artificialmente seus pontos entre testemunhos. O trace JSON inclui payload de checker, mapping, projeção, suficiência e referências. A coluna checker identifica o contrato de destino; quando há no_existing_fact_for_selected_claim, ele não produziu fato para aquele claim. FORMAL_NOT_ATTEMPTED significa que o subprocesso Lean não foi chamado para essa obrigação. Um bloco repetido em duas linhas de testemunhos é pago apenas uma vez. Casos com mesma nota mas diferente suporte/contexto também são incluídos.

### A02_subtraindo — SEMANTIC_RESCUE, MISSED_CREDIT

Expectativa 3.0000; Current 0.0000; Semantic Formal 1.0000. Identificação e conta completas, com a ordem dos operandos explicitada por de.

```text
(a)
O número invertido é 137. Subtraindo 137 de 731, obtenho 594.
```

**Current** — [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_current_01/A02_subtraindo.json)

Nenhum resultado de verificação vinculado; nenhuma evidência positiva atravessou o caminho deste modo.

Esperadas não detectadas: `["a.constructs_subtraction","a.identifies_137","a.result_594"]`. Positivas indevidas: `[]`.

**Semantic Formal** — [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_formal_01/A02_subtraindo.json)

| source_span | claim | obrigação | rota efetiva | checker | verificação / motivo | suficiência | award | pontos em bloco |
|---|---|---|---|---|---|---|---|---|
| `O número invertido é 137. Subtraindo 137 de 731, obtenho 594.` | `731 - 137 = 594` | `a.constructs_subtraction` | DETERMINISTIC | _check_a | DETERMINISTIC_FAILED / no_existing_fact_for_selected_claim; projeção: representation_miss | False | sem suporte | 0 (sem bloco pago) |
| `O número invertido é 137. Subtraindo 137 de 731, obtenho 594.` | `731 - 137 = 594` | `a.result_594` | FORMAL | _check_a → student Lean checker | FORMAL_NOT_ATTEMPTED / no_existing_fact_for_selected_claim; projeção: representation_miss | False | sem suporte | 0 (sem bloco pago) |
| `O número invertido é 137. Subtraindo 137 de 731, obtenho 594.` | `731 - 137 = 594` | `a.arithmetic_error_only` | DETERMINISTIC | _check_a | DETERMINISTIC_FAILED / no_existing_fact_for_selected_claim; projeção: representation_miss | False | sem suporte | 0 (sem bloco pago) |
| `O número invertido é 137. Subtraindo 137 de 731, obtenho 594.` | `O número invertido é 137.` | `a.identifies_137` | SEMANTIC | SemanticSufficiencyGate | SEMANTIC_SUPPORTED / adequate_evidence | True | suporte | a.identification=1.0000 |


Esperadas não detectadas: `["a.constructs_subtraction","a.result_594"]`. Positivas indevidas: `[]`.

A interpretação causal detalhada e as limitações de atribuição são discutidas na seção de achados abaixo.

### A04_invertido_em_prosa — CURRENT_BETTER, MISSED_CREDIT

Expectativa 2.0000; Current 2.0000; Semantic Formal 0.0000. A representação posicional do invertido está explícita; nenhuma subtração/fatoração é alegada.

```text
(b)
O número invertido é 100c+10b+a.
```

**Current** — [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_current_01/A04_invertido_em_prosa.json)

| source_span | claim | obrigação | rota efetiva | checker | verificação / motivo | suficiência | award | pontos em bloco |
|---|---|---|---|---|---|---|---|---|
| `100c+10b+a` | `100c+10b+a` | `b.reversed_number` | DETERMINISTIC | _check_b | DETERMINISTIC_VERIFIED / fato do checker existente | decisão nativa da ponte | suporte | b.reverse=2.0000 |


Esperadas não detectadas: `[]`. Positivas indevidas: `[]`.

**Semantic Formal** — [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_formal_01/A04_invertido_em_prosa.json)

| source_span | claim | obrigação | rota efetiva | checker | verificação / motivo | suficiência | award | pontos em bloco |
|---|---|---|---|---|---|---|---|---|
| `O número invertido é 100c+10b+a.` | `O número invertido é 100c+10b+a.` | `b.reversed_number` | DETERMINISTIC | _check_b | DETERMINISTIC_FAILED / no_existing_fact_for_selected_claim; projeção: unsupported_representation | False | sem suporte | 0 (sem bloco pago) |


Esperadas não detectadas: `["b.reversed_number"]`. Positivas indevidas: `[]`.

A interpretação causal detalhada e as limitações de atribuição são discutidas na seção de achados abaixo.

### A05_lista_em_prosa — NORMALIZATION_GAIN

Expectativa 5.0000; Current 1.0000; Semantic Formal 5.0000. Fórmula e enumeração completa; domínio dos dígitos não é demonstrado e não recebe crédito.

```text
(c)
A diferença é dada por D=99(a-c). Os valores são D ∈ {99,198,297,396,495,594,693,792}.
```

**Current** — [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_current_01/A05_lista_em_prosa.json)

| source_span | claim | obrigação | rota efetiva | checker | verificação / motivo | suficiência | award | pontos em bloco |
|---|---|---|---|---|---|---|---|---|
| `D=99(a-c)` | `D=99(a-c)` | `c.uses_expression` | DETERMINISTIC | _check_c | DETERMINISTIC_VERIFIED / fato do checker existente | decisão nativa da ponte | suporte | c.expression=1.0000 |


Esperadas não detectadas: `["c.complete_list","c.no_extraneous_values","c.pattern_recognized","c.several_correct","c.some_correct"]`. Positivas indevidas: `[]`.

**Semantic Formal** — [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_formal_01/A05_lista_em_prosa.json)

| source_span | claim | obrigação | rota efetiva | checker | verificação / motivo | suficiência | award | pontos em bloco |
|---|---|---|---|---|---|---|---|---|
| `A diferença é dada por D=99(a-c). Os valores são D ∈ {99,198,297,396,495,594,693,792}.` | `D=99(a-c)` | `c.uses_expression` | DETERMINISTIC | _check_c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT; projeção: exact | True | suporte | c.expression=1.0000 |
| `A diferença é dada por D=99(a-c). Os valores são D ∈ {99,198,297,396,495,594,693,792}.` | `D ∈ {99,198,297,396,495,594,693,792}` | `c.complete_list` | DETERMINISTIC | _check_c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT; projeção: exact | True | suporte | c.list.full=4.0000 |
| `A diferença é dada por D=99(a-c). Os valores são D ∈ {99,198,297,396,495,594,693,792}.` | `D ∈ {99,198,297,396,495,594,693,792}` | `c.no_extraneous_values` | DETERMINISTIC | _check_c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT; projeção: exact | True | suporte | c.list.full=4.0000 |
| `A diferença é dada por D=99(a-c). Os valores são D ∈ {99,198,297,396,495,594,693,792}.` | `D ∈ {99,198,297,396,495,594,693,792}` | `c.single_list_error` | DETERMINISTIC | _check_c | DETERMINISTIC_FAILED / EXISTING_VERIFICATION_RESULT; projeção: exact | False | sem suporte | 0 (sem bloco pago) |
| `A diferença é dada por D=99(a-c). Os valores são D ∈ {99,198,297,396,495,594,693,792}.` | `D ∈ {99,198,297,396,495,594,693,792}` | `c.several_correct` | DETERMINISTIC | _check_c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT; projeção: exact | True | suporte | 0 (sem bloco pago) |
| `A diferença é dada por D=99(a-c). Os valores são D ∈ {99,198,297,396,495,594,693,792}.` | `D ∈ {99,198,297,396,495,594,693,792}` | `c.some_correct` | DETERMINISTIC | _check_c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT; projeção: exact | True | suporte | 0 (sem bloco pago) |
| `A diferença é dada por D=99(a-c). Os valores são D ∈ {99,198,297,396,495,594,693,792}.`; `A diferença é dada por D=99(a-c). Os valores são D ∈ {99,198,297,396,495,594,693,792}.` | `D ∈ {99,198,297,396,495,594,693,792}`; `D=99(a-c)` | `c.pattern_recognized` | DETERMINISTIC | _check_c | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT; projeção: exact | True | suporte | 0 (sem bloco pago) |


Esperadas não detectadas: `[]`. Positivas indevidas: `[]`.

A interpretação causal detalhada e as limitações de atribuição são discutidas na seção de achados abaixo.

### A06_contagem_em_prosa — NORMALIZATION_GAIN, MISSED_CREDIT

Expectativa 4.0000; Current 0.0000; Semantic Formal 2.0000. Contagem explícita de pares e escolhas; não exige equação e solução de a-c antes de contar.

```text
(d)
Há os pares (a,c) ∈ {(7,1),(8,2),(9,3)}. Para a dezena, b ∈ {0,1,2,3,4,5,6,7,8,9}. Portanto 3*10=30.
```

**Current** — [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_current_01/A06_contagem_em_prosa.json)

Nenhum resultado de verificação vinculado; nenhuma evidência positiva atravessou o caminho deste modo.

Esperadas não detectadas: `["d.digit_pairs","d.middle_choices","d.total_thirty"]`. Positivas indevidas: `[]`.

**Semantic Formal** — [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_formal_01/A06_contagem_em_prosa.json)

| source_span | claim | obrigação | rota efetiva | checker | verificação / motivo | suficiência | award | pontos em bloco |
|---|---|---|---|---|---|---|---|---|
| `Há os pares (a,c) ∈ {(7,1),(8,2),(9,3)}. Para a dezena, b ∈ {0,1,2,3,4,5,6,7,8,9}. Portanto 3*10=30.` | `(a,c) ∈ {(7,1),(8,2),(9,3)}` | `d.digit_pairs` | DETERMINISTIC | _check_d | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT; projeção: exact | True | suporte | d.pairs=2.0000 |
| `Há os pares (a,c) ∈ {(7,1),(8,2),(9,3)}. Para a dezena, b ∈ {0,1,2,3,4,5,6,7,8,9}. Portanto 3*10=30.` | `Para a dezena, b ∈ {0,1,2,3,4,5,6,7,8,9}` | `d.middle_choices` | DETERMINISTIC | _check_d | DETERMINISTIC_FAILED / no_existing_fact_for_selected_claim; projeção: unsupported_representation | False | sem suporte | 0 (sem bloco pago) |
| `Há os pares (a,c) ∈ {(7,1),(8,2),(9,3)}. Para a dezena, b ∈ {0,1,2,3,4,5,6,7,8,9}. Portanto 3*10=30.` | `3*10=30` | `d.total_thirty` | FORMAL | _check_d → student Lean checker | FORMAL_NOT_ATTEMPTED / no_existing_fact_for_selected_claim; projeção: exact | False | sem suporte | 0 (sem bloco pago) |


Esperadas não detectadas: `["d.middle_choices","d.total_thirty"]`. Positivas indevidas: `[]`.

A interpretação causal detalhada e as limitações de atribuição são discutidas na seção de achados abaixo.

### D02_montagem_sem_resultado — NORMALIZATION_GAIN

Expectativa 1.0000; Current 0.0000; Semantic Formal 1.0000. Montagem permite identificação, mas não há resultado nem diagnóstico de erro aritmético para faixa superior.

```text
(a)
731-137
```

**Current** — [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_current_01/D02_montagem_sem_resultado.json)

Nenhum resultado de verificação vinculado; nenhuma evidência positiva atravessou o caminho deste modo.

Esperadas não detectadas: `["a.constructs_subtraction","a.identifies_137"]`. Positivas indevidas: `[]`.

**Semantic Formal** — [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_formal_01/D02_montagem_sem_resultado.json)

| source_span | claim | obrigação | rota efetiva | checker | verificação / motivo | suficiência | award | pontos em bloco |
|---|---|---|---|---|---|---|---|---|
| `731-137` | `731-137` | `a.identifies_137` | DETERMINISTIC | _check_a | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT; projeção: exact | True | suporte | a.identification=1.0000 |
| `731-137` | `731-137` | `a.constructs_subtraction` | DETERMINISTIC | _check_a | DETERMINISTIC_VERIFIED / EXISTING_VERIFICATION_RESULT; projeção: exact | True | suporte | 0 (sem bloco pago) |


Esperadas não detectadas: `[]`. Positivas indevidas: `[]`.

A interpretação causal detalhada e as limitações de atribuição são discutidas na seção de achados abaixo.

## 8. False credits, missed credits e contexto

Nenhum ponto excedente ou obrigação positiva indevida nos dois modos.

| modo | caso | pontos faltantes | obrigações FN | score | expected |
|---|---|---|---|---|---|
| Current | A01_menos | 3.0 | `["a.constructs_subtraction","a.identifies_137","a.result_594"]` | 0.0 | 3.0 |
| Current | A02_subtraindo | 3.0 | `["a.constructs_subtraction","a.identifies_137","a.result_594"]` | 0.0 | 3.0 |
| Current | A03_resultado_por_extenso | 3.0 | `["a.constructs_subtraction","a.identifies_137","a.result_594"]` | 0.0 | 3.0 |
| Current | A05_lista_em_prosa | 4.0 | `["c.complete_list","c.no_extraneous_values","c.pattern_recognized","c.several_correct","c.some_correct"]` | 1.0 | 5.0 |
| Current | A06_contagem_em_prosa | 4.0 | `["d.digit_pairs","d.middle_choices","d.total_thirty"]` | 0.0 | 4.0 |
| Current | D02_montagem_sem_resultado | 1.0 | `["a.constructs_subtraction","a.identifies_137"]` | 0.0 | 1.0 |
| Current | E06_misto_adotado_descartado | 1.0 | `["a.identifies_137"]` | 0.0 | 1.0 |
| Semantic Formal | A01_menos | 3.0 | `["a.constructs_subtraction","a.identifies_137","a.result_594"]` | 0.0 | 3.0 |
| Semantic Formal | A02_subtraindo | 2.0 | `["a.constructs_subtraction","a.result_594"]` | 1.0 | 3.0 |
| Semantic Formal | A03_resultado_por_extenso | 3.0 | `["a.constructs_subtraction","a.identifies_137","a.result_594"]` | 0.0 | 3.0 |
| Semantic Formal | A04_invertido_em_prosa | 2.0 | `["b.reversed_number"]` | 0.0 | 2.0 |
| Semantic Formal | A06_contagem_em_prosa | 2.0 | `["d.middle_choices","d.total_thirty"]` | 2.0 | 4.0 |
| Semantic Formal | E06_misto_adotado_descartado | 1.0 | `["a.identifies_137"]` | 0.0 | 1.0 |


| modo | caso E | trecho esperado rejeitado | supressão segura | suporte efetivo ligado ao trecho |
|---|---|---|---|---|
| Current | E01_hipotese | `Suponha que 731-137=594. Não adoto esta hipótese como minha solução.` | sim | `[]` |
| Current | E02_negacao | `Não é verdade que 731-137=594.` | sim | `[]` |
| Current | E03_abandono | `Tentativa abandonada: r=100c+10b+a.` | sim | `[]` |
| Current | E04_citacao | `Cito apenas uma tentativa de outra pessoa: "D=99(a-c)." Não a adoto como solução.` | sim | `[]` |
| Current | E05_rejeicao_explicita | `Rejeito a afirmação 99(a-c)=594; não a uso na minha solução.` | sim | `[]` |
| Current | E06_misto_adotado_descartado | `Apenas a conta a seguir foi abandonada: 731-137=594.` | sim | `[]` |
| Semantic Formal | E01_hipotese | `Suponha que 731-137=594. Não adoto esta hipótese como minha solução.` | sim | `[]` |
| Semantic Formal | E02_negacao | `Não é verdade que 731-137=594.` | sim | `[]` |
| Semantic Formal | E03_abandono | `Tentativa abandonada: r=100c+10b+a.` | sim | `[]` |
| Semantic Formal | E04_citacao | `Cito apenas uma tentativa de outra pessoa: "D=99(a-c)." Não a adoto como solução.` | sim | `[]` |
| Semantic Formal | E05_rejeicao_explicita | `Rejeito a afirmação 99(a-c)=594; não a uso na minha solução.` | sim | `[]` |
| Semantic Formal | E06_misto_adotado_descartado | `Apenas a conta a seguir foi abandonada: 731-137=594.` | sim | `[]` |


## 9. Achados causais e limites

Há **quatro melhorias de nota e uma regressão**, com empate de nota e obrigações nos outros 31 casos. A recuperação bruta é de 8 pontos e a perda localizada é de 2, reduzindo os pontos faltantes de 19 para 13. Entre os ganhos, **1 ponto** vem do checker semântico secundário e **7 pontos** vêm de extração/projeção para checkers matemáticos existentes. Não há novo ponto concedido por Lean nas diferenças; ambos os modos têm 9 tentativas formais confirmadas, 8 FORMAL_VERIFIED e 1 FORMAL_REFUTED.

- **A02 — SEMANTIC_RESCUE + MISSED_CREDIT (0 → 1; esperado 3).** O baseline não produz fato. O extractor conserva o argumento literal `O número invertido é 137.` como qualitative; a rota SEMANTIC e o SemanticSufficiencyGate retornam adequate_evidence para a.identifies_137. AwardGate autoriza a obrigação e a pauta paga a.identification=1. A conta também é extraída como `731 - 137 = 594`, mas a projeção recebe representation_miss, sem fato de montagem nem resultado. A rota formal fica FORMAL_NOT_ATTEMPTED; os dois pontos restantes não são concedidos. A extração da conta, por si só, não constituiu prova.
- **A04 — CURRENT_BETTER + MISSED_CREDIT (2 → 0; esperado 2).** O baseline isola `100c+10b+a`, o _check_b reconhece a representação invertida e paga b.reverse=2. O C1 conserva a frase inteira `O número invertido é 100c+10b+a.` como expression. A fonte está grounded, mas a forma matemática é unsupported_representation e attributable=false. Não há fato para b.reversed_number, o resultado é DETERMINISTIC_FAILED e nenhum bloco é pago. A falha está na granularidade/representação extraída e na projeção; o JSON foi aceito, portanto não há fallback automático para recuperar o crédito que o baseline concederia. Trata-se de regressão local real, preservada no resultado.
- **A05 — NORMALIZATION_GAIN (1 → 5; esperado 5).** O baseline verifica somente D=99(a-c). O C1 separa fórmula e coleção, preservando o sujeito D e os oito valores explícitos; ambas as projeções são exact. O _check_c verifica a fórmula, completude e ausência de extras; AwardGate autoriza e PautaEngine paga c.expression=1 e c.list.full=4. Os fatos some_correct, several_correct e pattern_recognized também ficam supported, sem somar novamente os pontos das faixas inferiores. Não há suporte semântico secundário neste ganho e não se concede domínio dos dígitos ausente.
- **A06 — NORMALIZATION_GAIN + MISSED_CREDIT (0 → 2; esperado 4).** O C1 extrai os pares corretamente e o _check_d paga d.pairs=2. Contudo, o claim das escolhas mantém o prefixo `Para a dezena,` e a coleção recebe unsupported_representation. A igualdade `3*10=30` está projetada como exact, mas _check_d somente chama a verificação aritmética de contagem quando existem pares **e** escolhas reconhecidos. Sem o segundo pré-requisito, d.total_thirty fica FORMAL_NOT_ATTEMPTED e d.counting não paga seus 2 pontos. Não é refutação do produto nem falha de infraestrutura Lean.
- **D02 — NORMALIZATION_GAIN (0 → 1; esperado 1).** O coletor do baseline omite `731-137` isolado. O C1 o extrai sem inventar resultado, a projeção é exact e _check_a suporta identificação e montagem. A pauta escolhe a.identification=1, sem autorizar a.result_594 ou a faixa de erro aritmético. A expectativa deste caso foi conferida no contrato dos checkers antes de executar o benchmark, conforme seção 2.

**Falhas comuns que o empate não revela.** A01 e A03 ficam em 0 nos dois modos, contra 3 esperados em cada um. No C1, o extractor chega à igualdade correta, mas representation_gate não aceita sua relação com a forma verbal da fonte; A03 também transforma o resultado por extenso em um token numérico ausente do texto. O bloqueio ocorre antes do Lean. Em E06, ambos perdem 1 ponto da identificação explicitamente adotada. No C1, o extractor reformula `O número invertido que adoto é 137.` para `O número invertido adotado é 137.`; bind_evidence exige que um qualitative seja substring literal do source_span, rejeita o lote inteiro e retorna ao baseline. Esses casos demonstram que interpretar o significado não basta para atravessar as validações de representação e atribuição existentes.

**Contexto e irrelevância.** Os seis trechos negativos de E não produzem crédito nos dois modos: context rejection accuracy=6/6. No C1 há rejeição explícita em E01, E02, E03 e E05 (8 linhas de verificação); E04 e E06 terminam em fallback e ausência de suporte. Portanto, não há evidência comparativa de CONTEXT_SUPPRESSION superior ao baseline. E06 ainda evidencia perda do trecho positivo adotado, apesar de a supressão negativa estar correta. Os outros 2 eventos CONTEXT_REJECTED do C1 pertencem a F05/F06, onde o extractor marca evidência irrelevante como não atribuída; são contados como eventos do pipeline, não como os seis alvos contextuais de E. Nos F, os modos preservam todo o crédito pertinente e não dão pontos às afirmações alheias; a identidade F02 e a diferença F04 são negadas por ausência de fato pertinente, não declaradas matematicamente falsas.

**Confiabilidade operacional e classificação dos três fallbacks.** O indicador nativo technical_uncertainty e FORMAL_ERROR permanece 0/36 nos dois modos. Isso não equivale a ausência de falhas operacionais: há **3/36 falhas de extração** no C1, todas seguidas de TME_CURRENT_FALLBACK, e nenhuma no Current. Não foram reexecutadas para substituir respostas.

| caso | causa observada | classificação | consequência |
|---|---|---|---|
| E04_citacao | ValueError:qualitative_claim_must_preserve_literal_argument; o modelo reformula uma descrição contextual em vez de preservar o argumento literal | violação do contrato de extração/validação | lote descartado; baseline retorna 0, esperado 0 |
| E06_misto_adotado_descartado | mesmo ValueError no argumento positivo reformulado | violação do contrato de extração/validação | lote descartado; baseline retorna 0, esperado 1 |
| F01_soma_verdadeira | ValueError:extractor_incomplete_or_refused; 16.000 output_tokens, iguais ao limite configurado | resposta do modelo não concluída; provável limite de saída | baseline retorna 0, esperado 0; latência do extractor ≈99,68 s |

Em F01, atingir exatamente o teto de saída é evidência compatível com truncamento, mas o wrapper não preserva response.status original nem incomplete_details no artefato final; não é possível afirmar a razão terminal exata ou uma recusa. Não há evidência de timeout, import/module path, unknown identifier, cache ou problema de Mathlib. Os detalhes estão em [operational_reliability.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_analysis_01/operational_reliability.json).

**Limites da conclusão.** O veredito favorece o C1 neste DEV pelo critério congelado, mas a família A ainda acerta só **1/6** notas exatas em ambos os modos: seu MAE melhora de 2,8333 para 2,0000 e seu recall de obrigações de 10,53% para 42,11%, sem robustez ampla às paráfrases. B, C e F já eram perfeitas no baseline desta amostra; D melhora de 5/6 para 6/6 e E permanece em 5/6. Há apenas um conjunto pequeno construído a partir de contratos conhecidos e uma execução por modo; variação estocástica, custo e generalização não foram avaliados. O critério de vantagem mede fidelidade de nota e supressão indevida, não confiabilidade da extração; por isso os três fallbacks e a regressão A04 acompanham explicitamente o veredito. Nenhum desses defeitos foi corrigido durante a avaliação.


## 10. Veredito e integridade final

**P1_SEMANTIC_ADVANTAGE_CONFIRMED**, segundo o critério congelado. O experimento terminou sem tuning. Defeitos observados ficam documentados; nenhuma correção ou expansão foi iniciada.

Dataset, expectativas, manifesto e 234 arquivos protegidos de runtime/pilotos anteriores foram conferidos por SHA-256. Os resultados dos dois modos usam o mesmo SHA, pauta, registry, checker, prompt e AwardGate. Os artefatos de análise registram os hashes de cada saída. Nenhum arquivo versionado anterior foi modificado; somente dataset DEV e este relatório foram adicionados ao worktree, além dos artefatos de avaliação ignorados pelo Git.

Estado final do Git; `git rev-parse HEAD` permaneceu `377427a93a44208e430f9a014b0b062320054083`:

```text
?? docs/audits/TME_P1_SEMANTIC_ROBUSTNESS_01.md
?? tests/fixtures/tme_semantic_formal_c1/semantic_robustness_01/
```

Artefatos analíticos: [métricas globais/por família](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_analysis_01/metrics.json); [métricas por caso](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_analysis_01/per_case_metrics.json); [cadeias causais completas](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_analysis_01/causal_comparisons.json); [integridade](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/semantic_robustness_analysis_01/integrity.json).

## Apêndice — conteúdo e motivo pedagógico dos 36 casos

### A01_menos (A)

```text
(a)
731 menos 137 é igual a 594.
```

Expectativa calculada: 3.0000; referência `a_complete`. Verbaliza a mesma subtração, com ambos os operandos, ordem e resultado explícitos.

Obrigações esperadas: `["a.constructs_subtraction","a.identifies_137","a.result_594"]`. Rejeições esperadas: `[]`.

### A02_subtraindo (A)

```text
(a)
O número invertido é 137. Subtraindo 137 de 731, obtenho 594.
```

Expectativa calculada: 3.0000; referência `a_complete`. Identificação e conta completas, com a ordem dos operandos explicitada por de.

Obrigações esperadas: `["a.constructs_subtraction","a.identifies_137","a.result_594"]`. Rejeições esperadas: `[]`.

### A03_resultado_por_extenso (A)

```text
(a)
731 menos 137 é quinhentos e noventa e quatro.
```

Expectativa calculada: 3.0000; referência `a_complete`. Somente o resultado passa a ser escrito por extenso; não acrescenta nem retira passo.

Obrigações esperadas: `["a.constructs_subtraction","a.identifies_137","a.result_594"]`. Rejeições esperadas: `[]`.

### A04_invertido_em_prosa (A)

```text
(b)
O número invertido é 100c+10b+a.
```

Expectativa calculada: 2.0000; referência `b_reverse`. A representação posicional do invertido está explícita; nenhuma subtração/fatoração é alegada.

Obrigações esperadas: `["b.reversed_number"]`. Rejeições esperadas: `[]`.

### A05_lista_em_prosa (A)

```text
(c)
A diferença é dada por D=99(a-c). Os valores são D ∈ {99,198,297,396,495,594,693,792}.
```

Expectativa calculada: 5.0000; referência `c_formula_list`. Fórmula e enumeração completa; domínio dos dígitos não é demonstrado e não recebe crédito.

Obrigações esperadas: `["c.complete_list","c.no_extraneous_values","c.pattern_recognized","c.several_correct","c.some_correct","c.uses_expression"]`. Rejeições esperadas: `[]`.

### A06_contagem_em_prosa (A)

```text
(d)
Há os pares (a,c) ∈ {(7,1),(8,2),(9,3)}. Para a dezena, b ∈ {0,1,2,3,4,5,6,7,8,9}. Portanto 3*10=30.
```

Expectativa calculada: 4.0000; referência `d_count`. Contagem explícita de pares e escolhas; não exige equação e solução de a-c antes de contar.

Obrigações esperadas: `["d.digit_pairs","d.middle_choices","d.total_thirty"]`. Rejeições esperadas: `[]`.

### B01_sinais_espacos (B)

```text
(a)
731 − 137 = 594
```

Expectativa calculada: 3.0000; referência `a_complete`. Mesma subtração em ordem, com sinal Unicode e espaços; nenhuma troca de lados.

Obrigações esperadas: `["a.constructs_subtraction","a.identifies_137","a.result_594"]`. Rejeições esperadas: `[]`.

### B02_posicional_reordenada (B)

```text
(b)
R=a+10*b+100*c.
```

Expectativa calculada: 2.0000; referência `b_reverse`. Comutatividade da soma na representação invertida com símbolo novo inequívoco.

Obrigações esperadas: `["b.reversed_number"]`. Rejeições esperadas: `[]`.

### B03_algebra_equivalente (B)

```text
(b)
r=a+10*b+100*c.
(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c=-99*(c-a).
```

Expectativa calculada: 5.0000; referência `b_complete`. Mesma expansão, cancelamento e fatoração em notação equivalente já conhecida na regressão.

Obrigações esperadas: `["b.factorization","b.middle_cancellation","b.reversed_number","b.subtraction"]`. Rejeições esperadas: `[]`.

### B04_formula_sinal (B)

```text
(c)
D=-99(c-a).
```

Expectativa calculada: 1.0000; referência `c_formula`. Expressão equivalente por duas trocas de sinal; apenas a fórmula, sem lista ou domínio.

Obrigações esperadas: `["c.uses_expression"]`. Rejeições esperadas: `[]`.

### B05_equacoes_simetrizadas (B)

```text
(d)
594=99(a-c).
6=a-c.
```

Expectativa calculada: 2.0000; referência `d_solve`. O contrato de _check_d examina ambos os lados; inverter a igualdade preserva estas duas obrigações. Não se generaliza essa propriedade ao item a.

Obrigações esperadas: `["d.difference_six","d.equation"]`. Rejeições esperadas: `[]`.

### B06_produto_comutado (B)

```text
(d)
(a,c) ∈ {(7,1),(8,2),(9,3)}
b ∈ {0,1,2,3,4,5,6,7,8,9}
10*3=30.
```

Expectativa calculada: 4.0000; referência `d_count`. Produto com fatores comutados, explicitamente aceito pelo checker; mesmos pré-requisitos.

Obrigações esperadas: `["d.digit_pairs","d.middle_choices","d.total_thirty"]`. Rejeições esperadas: `[]`.

### C01_b_passos_reordenados (C)

```text
(b)
99a-99c=99(a-c).
r=100c+10b+a.
(100a+10b+c)-(100c+10b+a)=99a-99c.
```

Expectativa calculada: 5.0000; referência `b_complete`. Reordena afirmações completas de uma mesma demonstração; a fatoração continua escrita com expansão, não inferida.

Obrigações esperadas: `["b.factorization","b.middle_cancellation","b.reversed_number","b.subtraction"]`. Rejeições esperadas: `[]`.

### C02_c_lista_primeiro (C)

```text
(c)
D ∈ {99,198,297,396,495,594,693,792}
a>c.
D=99(a-c).
(a-c) ∈ {1,2,3,4,5,6,7,8}
a<=9.
1<=c.
```

Expectativa calculada: 6.0000; referência `c_complete`. Lista, fórmula e restrições são as mesmas do caso completo, em ordem diferente.

Obrigações esperadas: `["c.complete_list","c.difference_domain","c.no_extraneous_values","c.pattern_recognized","c.several_correct","c.some_correct","c.uses_expression"]`. Rejeições esperadas: `[]`.

### C03_d_produto_primeiro (C)

```text
(d)
3*10=30.
b ∈ {0,1,2,3,4,5,6,7,8,9}
(a,c) ∈ {(7,1),(8,2),(9,3)}
a-c=6.
99(a-c)=594.
```

Expectativa calculada: 6.0000; referência `d_complete`. Produto e premissas explícitas pertencem ao mesmo item; não há dependência pedagógica de ordem textual.

Obrigações esperadas: `["d.difference_six","d.digit_pairs","d.equation","d.middle_choices","d.total_thirty"]`. Rejeições esperadas: `[]`.

### C04_itens_d_b_a_c (C)

```text
(d)
99(a-c)=594.
a-c=6.
(a,c) ∈ {(7,1),(8,2),(9,3)}
b ∈ {0,1,2,3,4,5,6,7,8,9}
3*10=30.
(b)
r=100c+10b+a.
(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c).
(a)
731-137=594
(c)
D=99(a-c).
1<=c.
a<=9.
a>c.
(a-c) ∈ {1,2,3,4,5,6,7,8}
D ∈ {99,198,297,396,495,594,693,792}
```

Expectativa calculada: 20.0000; referência `p1_complete_regression`. Mantém os quatro itens completos e suas fronteiras explícitas, mudando apenas a ordem dos itens.

Obrigações esperadas: `["a.constructs_subtraction","a.identifies_137","a.result_594","b.factorization","b.middle_cancellation","b.reversed_number","b.subtraction","c.complete_list","c.difference_domain","c.no_extraneous_values","c.pattern_recognized","c.several_correct","c.some_correct","c.uses_expression","d.difference_six","d.digit_pairs","d.equation","d.middle_choices","d.total_thirty"]`. Rejeições esperadas: `[]`.

### C05_c_parcial_lista_primeiro (C)

```text
(c)
D ∈ {99,198,297,396,495,594,693}
D=99(a-c).
```

Expectativa calculada: 4.0000; referência `c_one_omission`. A lista com uma omissão precede a fórmula; continua sem domínio, preservando crédito parcial.

Obrigações esperadas: `["c.no_extraneous_values","c.pattern_recognized","c.several_correct","c.single_list_error","c.some_correct","c.uses_expression"]`. Rejeições esperadas: `[]`.

### C06_d_contagem_reordenada (C)

```text
(d)
b ∈ {0,1,2,3,4,5,6,7,8,9}
3*10=30.
(a,c) ∈ {(7,1),(8,2),(9,3)}
```

Expectativa calculada: 4.0000; referência `d_count`. Somente o subconjunto de contagem, com ordem alterada e premissas explícitas.

Obrigações esperadas: `["d.digit_pairs","d.middle_choices","d.total_thirty"]`. Rejeições esperadas: `[]`.

### D01_identificacao (D)

```text
(a)
137
```

Expectativa calculada: 1.0000; referência `a_only_inverse`. Somente identifica o invertido; não inventar montagem nem resultado.

Obrigações esperadas: `["a.identifies_137"]`. Rejeições esperadas: `[]`.

### D02_montagem_sem_resultado (D)

```text
(a)
731-137
```

Expectativa calculada: 1.0000; referência `a_setup`. Montagem permite identificação, mas não há resultado nem diagnóstico de erro aritmético para faixa superior.

Obrigações esperadas: `["a.constructs_subtraction","a.identifies_137"]`. Rejeições esperadas: `[]`.

### D03_erro_aritmetico (D)

```text
(a)
731-137=584
```

Expectativa calculada: 2.0000; referência `a_single_arithmetic_error`. Montagem correta com um único resultado aritmético falso; faixa específica da pauta, não resultado verdadeiro.

Obrigações esperadas: `["a.arithmetic_error_only","a.constructs_subtraction","a.identifies_137"]`. Rejeições esperadas: `[{"source_span":"731-137=584","rejection_kind":"mathematical_refutation","reason":"Não autoriza a.result_594; a montagem e o diagnóstico de erro único continuam válidos.","source_start":4,"source_end":15}]`.

### D04_somente_invertido (D)

```text
(b)
r=100c+10b+a.
```

Expectativa calculada: 2.0000; referência `b_reverse`. Apenas representação invertida, independente da subtração e fatoração.

Obrigações esperadas: `["b.reversed_number"]`. Rejeições esperadas: `[]`.

### D05_um_valor (D)

```text
(c)
{99}
```

Expectativa calculada: 1.0000; referência `c_few_results`. Apenas um valor correto; não presume fórmula, completude ou domínio.

Obrigações esperadas: `["c.no_extraneous_values","c.some_correct"]`. Rejeições esperadas: `[]`.

### D06_equacao_e_diferenca (D)

```text
(d)
99(a-c)=594.
a-c=6.
```

Expectativa calculada: 2.0000; referência `d_solve`. Somente bloco solve; não presume pares, escolhas ou contagem.

Obrigações esperadas: `["d.difference_six","d.equation"]`. Rejeições esperadas: `[]`.

### E01_hipotese (E)

```text
(a)
Suponha que 731-137=594. Não adoto esta hipótese como minha solução.
```

Expectativa calculada: 0.0000; referência `empty`. Conteúdo correto é explicitamente hipotético e não adotado.

Obrigações esperadas: `[]`. Rejeições esperadas: `[{"source_span":"Suponha que 731-137=594. Não adoto esta hipótese como minha solução.","rejection_kind":"context","reason":"Hipótese não adotada não sustenta obrigações.","source_start":4,"source_end":72}]`.

### E02_negacao (E)

```text
(a)
Não é verdade que 731-137=594.
```

Expectativa calculada: 0.0000; referência `empty`. A igualdade correta aparece negada; não pode ser atribuída como afirmação positiva.

Obrigações esperadas: `[]`. Rejeições esperadas: `[{"source_span":"Não é verdade que 731-137=594.","rejection_kind":"context","reason":"Asserção negada, não suporte positivo.","source_start":4,"source_end":34}]`.

### E03_abandono (E)

```text
(b)
Tentativa abandonada: r=100c+10b+a.
```

Expectativa calculada: 0.0000; referência `empty`. A representação correta foi abandonada, sem uma versão adotada.

Obrigações esperadas: `[]`. Rejeições esperadas: `[{"source_span":"Tentativa abandonada: r=100c+10b+a.","rejection_kind":"context","reason":"Tentativa explicitamente abandonada.","source_start":4,"source_end":39}]`.

### E04_citacao (E)

```text
(c)
Cito apenas uma tentativa de outra pessoa: "D=99(a-c)." Não a adoto como solução.
```

Expectativa calculada: 0.0000; referência `empty`. Citação de tentativa de terceiro, sem adoção pelo aluno.

Obrigações esperadas: `[]`. Rejeições esperadas: `[{"source_span":"Cito apenas uma tentativa de outra pessoa: \"D=99(a-c).\" Não a adoto como solução.","rejection_kind":"context","reason":"Citação não atribuível como solução adotada.","source_start":4,"source_end":85}]`.

### E05_rejeicao_explicita (E)

```text
(d)
Rejeito a afirmação 99(a-c)=594; não a uso na minha solução.
```

Expectativa calculada: 0.0000; referência `empty`. O próprio aluno rejeita a equação; verdade matemática isolada não autoriza crédito.

Obrigações esperadas: `[]`. Rejeições esperadas: `[{"source_span":"Rejeito a afirmação 99(a-c)=594; não a uso na minha solução.","rejection_kind":"context","reason":"Afirmação rejeitada pelo aluno.","source_start":4,"source_end":64}]`.

### E06_misto_adotado_descartado (E)

```text
(a)
O número invertido que adoto é 137.
Apenas a conta a seguir foi abandonada: 731-137=594.
```

Expectativa calculada: 1.0000; referência `a_only_inverse`. Identificação explicitamente adotada permanece; somente a conta posterior está abandonada.

Obrigações esperadas: `["a.identifies_137"]`. Rejeições esperadas: `[{"source_span":"Apenas a conta a seguir foi abandonada: 731-137=594.","rejection_kind":"context","reason":"Descartar a conta não apaga a identificação anterior adotada.","source_start":40,"source_end":92}]`.

### F01_soma_verdadeira (F)

```text
(a)
2+2=4
```

Expectativa calculada: 0.0000; referência `empty`. Soma verdadeira sem identificação, montagem ou resultado exigidos.

Obrigações esperadas: `[]`. Rejeições esperadas: `[{"source_span":"2+2=4","rejection_kind":"irrelevant","reason":"Soma verdadeira sem identificação, montagem ou resultado exigidos.","source_start":4,"source_end":9}]`.

### F02_identidade_alheia (F)

```text
(b)
(x+y)^2=x^2+2*x*y+y^2
```

Expectativa calculada: 0.0000; referência `empty`. Identidade verdadeira alheia à representação/fatoração da pauta.

Obrigações esperadas: `[]`. Rejeições esperadas: `[{"source_span":"(x+y)^2=x^2+2*x*y+y^2","rejection_kind":"irrelevant","reason":"Identidade verdadeira alheia à representação/fatoração da pauta.","source_start":4,"source_end":25}]`.

### F03_quadrados (F)

```text
(c)
{1,4,9,16}
```

Expectativa calculada: 0.0000; referência `empty`. Coleção de quadrados sem valores corretos da lista requerida.

Obrigações esperadas: `[]`. Rejeições esperadas: `[{"source_span":"{1,4,9,16}","rejection_kind":"irrelevant","reason":"Coleção de quadrados sem valores corretos da lista requerida.","source_start":4,"source_end":14}]`.

### F04_diferenca_numerica (F)

```text
(d)
7-1=6
```

Expectativa calculada: 0.0000; referência `empty`. Diferença numérica verdadeira, sem vincular a-c ou enumerar os pares exigidos.

Obrigações esperadas: `[]`. Rejeições esperadas: `[{"source_span":"7-1=6","rejection_kind":"irrelevant","reason":"Diferença numérica verdadeira, sem vincular a-c ou enumerar os pares exigidos.","source_start":4,"source_end":9}]`.

### F05_conta_correta_com_ruido (F)

```text
(a)
731-137=594.
5*5=25.
```

Expectativa calculada: 3.0000; referência `a_complete`. Conta requerida permanece completa; produto verdadeiro adicional não satisfaz obrigação nem soma pontos.

Obrigações esperadas: `["a.constructs_subtraction","a.identifies_137","a.result_594"]`. Rejeições esperadas: `[{"source_span":"5*5=25.","rejection_kind":"irrelevant","reason":"Produto alheio às obrigações de a.","source_start":17,"source_end":24}]`.

### F06_contagem_com_ruido (F)

```text
(d)
(a,c) ∈ {(7,1),(8,2),(9,3)}
2+2=4.
b ∈ {0,1,2,3,4,5,6,7,8,9}
3*10=30.
```

Expectativa calculada: 4.0000; referência `d_count`. Pares e contagem permanecem explícitos; soma intermediária irrelevante não autoriza solve ou pontos extras.

Obrigações esperadas: `["d.digit_pairs","d.middle_choices","d.total_thirty"]`. Rejeições esperadas: `[{"source_span":"2+2=4.","rejection_kind":"irrelevant","reason":"Soma alheia às obrigações de d.","source_start":32,"source_end":38}]`.
