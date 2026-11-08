# P3 — regressão congelada Multi-Layer 01

**Veredito: `P3_MULTI_LAYER_REGRESSION_FAILED`.**

Execução em 08/11/2026. Classificação de todos os dados: **OBSERVED REGRESSION ONLY**. Foram reprocessados 184 registros históricos (128 case_ids distintos), sem API, com Lean real, sobre o SHA limpo `8fc68fa49cb833f45b854e7e3cced747efa9dcbb`. Não houve alteração de implementação, prompt, fixtures, expectations, matemática ou pauta.

A05 ficou em 0; os cinco falsos vetos prioritários e os quatro falsos positivos antigos dos guards estão corrigidos. Não foi encontrado falso crédito conforme os contratos observados e a política de E02 já autorizada. Entretanto, há **três falsos vetos aplicados**: Safety02/S1_05 e Safety03/C06/E05. S1_05 e E05 bloqueiam diretamente witnesses corretos, verificados e suficientes, de 2 pontos cada. C06 tem um veto indevido adicional à falha de representação positiva; não atribuímos seus 2 pontos perdidos exclusivamente ao veto.

Os 184 scores reproduzem o replay registrado durante a implementação. Isso não basta para prontidão: nos três casos, a autoridade negativa é nova em relação aos traces anteriores ao Multi-Layer, embora a nota 0 já existisse. O critério “zero novo falso veto material” falha. Os checks de integridade dos receipts passam porque os estados discursivos incorretos já chegam como `ACTIVE` à política. **Não executar Safety04 com base nesta regressão.**

## 1. Congelamento e execução

Congelamento: `2026-11-08T15:12:08.546537+00:00`; replay: `2026-11-08T15:12:12.109247+00:00` até `2026-11-08T15:16:48.346713+00:00`. Foram conferidos antes/depois **1331 arquivos**, incluindo arquivos rastreados e insumos históricos. Zero mudança nos hashes congelados. O protocolo foi escrito antes do replay: SHA-256 `0da12da99d7516db742aba5d222612646d8803d2ebc95f8f8a727ad5e23ae797`.

Artefatos novos e separados dos anteriores: [diretório da execução](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01). Evidências: [freeze.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/freeze.json), [protocol.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/protocol.json), [preservation.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/preservation.json), [run/summary.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/summary.json), [run/run_manifest.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/run_manifest.json), [analysis/metrics.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/metrics.json), [analysis/causal_regressions.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/causal_regressions.json), [invariants.xml](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/invariants.xml), [replay.log](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/replay.log), [artifact_manifest.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/artifact_manifest.json). O script de apuração `analyze.py` arquivado nesse diretório usa somente a biblioteca padrão, lê os traces e a pauta congelada, e não importa nem executa o pipeline.

Comandos exatos executados no worktree P3:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python scripts/evaluation/replay_tme_p3_multilayer.py --output /private/tmp/p3-frozen-regression/run > /private/tmp/p3-frozen-regression/replay.log 2>&1

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_tme_p3_multilayer.py tests/test_tme_p3_discourse_state.py tests/test_tme_p3_veto_policy.py tests/test_tme_p3_unified_reconciliation.py tests/test_tme_p3_unified_lean.py --basetemp=/private/tmp/p3-frozen-regression/pytest --junitxml=/private/tmp/p3-frozen-regression/invariants.xml --tb=short > /private/tmp/p3-frozen-regression/invariants.log 2>&1
```

Ambos encerraram com exit code 0. Suíte selecionada: **194 passed in 33.73s**, sem falha/skip. Os 1.178 testes mencionados no relatório de implementação são evidência anterior, não uma nova execução de 1.178 nesta tarefa. `openai.OpenAI` ficou bloqueado pelo runner; o provider devolveu somente o raw_output histórico. **Zero chamadas API; nenhum extractor rerodado.** Os modos Current não foram reexecutados; “histórico” no apêndice significa Semantic da respectiva rodada original.

Os dados não representam 184 amostras independentes: DEV01 e DEV02 reutilizam os oito textos; Safety02 inclui seus 32 textos e uma rodada registrada dos 48 textos de Robustness01. As duas versões de output do extractor foram preservadas e reprocessadas separadamente.

Hashes SHA-256 principais (manifesto completo em `freeze.json`):

| Fixture | SHA-256 |
| --- | --- |
| dev_ids.json | `a7ab3a65f60e1284b119c8974a47e3eea0c037f58c96963bff8c7372ebcaab0a` |
| dev_sources.json | `d12a77cd87f0e5197db7e3cdafaedf78a130dd7dc3b1b59fa5d029a702e375cc` |
| semantic_robustness_01/expectations.json | `8d52cabe84a7d4ddbf96f46599dd48df7fc5c4428045f9060086dd49364ec84d` |
| semantic_robustness_01/sources.json | `56d15fc1c217b0c112f8538a5585c2f7f2db2e88a9b1f1713bae0f29227d753b` |
| semantic_safety_02/expectations.json | `d8407e4ec10262a6067404f97b7d93280a5a5be2d221006518ad58e834a051a7` |
| semantic_safety_02/sources.json | `39bddd7575ab463cab38d8246d0233efb3ef510ec93f150d47655183df78d77a` |
| semantic_safety_03/expectations.json | `d79bdde532db58f394d952df818ec1fc349af97a951416e5c9be7d3ebbdb51e2` |
| semantic_safety_03/sources.json | `79fce6d0062b6cd5cd237dfb5838779a3f89603079233230af34a746954d836d` |

## 2. Contratos e definição das métricas

Nenhuma expectation foi ajustada após observar o resultado. Exact = igualdade do score com o contrato, dividido pelo número de registros rotulados; MAE = média de |score − esperado|. Precision/recall são micro por obligation_id elegível: TP/(TP+FP) e TP/(TP+FN), não por número de claims nem por decisão candidata. Crédito indevido conta parcelas efetivamente pontuadas sem suporte no contrato; missed points usa a pauta congelada com `all_of` e `max_of`, sem duplicar dependências. Veto falso é receipt negativo **aplicado** a obrigação legítima segundo fonte e contrato; rejeição/ausência de witness sozinha não é hard veto.

DEV não tem arquivo expectations: os alvos 4/2/2/8/8/2/2/2 derivam dos julgamentos já registrados no forense DEV01 e validação DEV02, copiados no protocolo antes desta execução. Portanto, exact/MAE de DEV são concordância com esse contrato forense observado, não uma previsão pré-piloto nem gold. Para os demais conjuntos, usam-se os arquivos expectations congelados.

**E02:** a fixture histórica ainda prevê 2 e apenas `a.bottom_white_count`; a autorização anterior do usuário aceita a autocorreção “Na verdade…” e prevê também `b.same_compartment`, total 4. Apresentam-se separadamente métricas literais e métricas da política autorizada. Esta distinção foi fixada antes do replay; nenhuma fixture mudou.

## 3. Scores e métricas por conjunto

ALL inclui fallback nativo. Precision/recall e false credits desta primeira tabela usam a política de E02 autorizada. Os scores individuais estão no apêndice B e os numeradores completos em `analysis/metrics.json`.

| Conjunto | N | Score/esperado | Exact | MAE | Precision | Recall | Falso crédito (pts) | Falsos vetos (casos) | Missed casos/pts | Fallback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEV01 | 8 | 30/30 | 8/8 | 0.000000 | 17/17 | 17/17 | 0 | 0 | 0 / 0 | 1 |
| DEV02 | 8 | 30/30 | 8/8 | 0.000000 | 17/17 | 17/17 | 0 | 0 | 0 / 0 | 0 |
| Robustness01 | 48 | 71/79 | 44/48 | 0.166667 | 42/42 | 42/46 | 0 | 0 | 4 / 8 | 1 |
| Safety02/new32 | 32 | 33/37 | 30/32 | 0.125000 | 18/18 | 18/20 | 0 | 1 | 2 / 4 | 1 |
| Safety02/observed48 | 48 | 71/79 | 44/48 | 0.166667 | 42/42 | 42/46 | 0 | 0 | 4 / 8 | 0 |
| Safety03 | 40 | 49/71 | 30/40 | 0.550000 | 27/27 | 27/39 | 0 | 2 | 10 / 22 | 3 |

Safety02 completo (80 registros): score **104/116**, exact **74/80**, MAE **0,15**, precision **60/60**, recall **60/66**, zero falso crédito, 1 caso com falso veto, 12 pontos perdidos e 1 fallback. Os 48 registros observados não são um novo benchmark.

Comparação literal com a fixture antiga de E02, sem correção de política: Robustness01 e Safety02/observed48 têm cada um **score 71/77, exact 43/48, MAE 0,208333, precision 41/42 e recall 41/45**. O único FP por obrigação de cada rodada é E02/b.same, 2 pontos; é uma divergência documental conhecida e autorizada, não um falso crédito matemático novo. Safety02 completo literal: score104/114, exact73/80, MAE0,175.

Somente **RECORDED_SUCCESS**, excluindo outputs gravados indisponíveis:

| Conjunto | N | Score/esperado | Exact | MAE | Precision | Recall | Missed pts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEV01 | 7 | 28/28 | 7/7 | 0.000000 | 16/16 | 16/16 | 0 |
| DEV02 | 8 | 30/30 | 8/8 | 0.000000 | 17/17 | 17/17 | 0 |
| Robustness01 | 47 | 71/79 | 43/47 | 0.170213 | 42/42 | 42/46 | 8 |
| Safety02/new32 | 31 | 33/37 | 29/31 | 0.129032 | 18/18 | 18/20 | 4 |
| Safety02/observed48 | 48 | 71/79 | 44/48 | 0.166667 | 42/42 | 42/46 | 8 |
| Safety03 | 37 | 49/68 | 29/37 | 0.513514 | 27/27 | 27/37 | 19 |

No agregado de **registros**, sem interpretação de independência: score284/326, exact164/184, MAE0,228261, precision163/163, recall163/185; 42 pontos perdidos em20 registros. Há6 fallbacks e178 replays com raw_output aproveitável. O agregado duplica os conjuntos observados acima e não mede acurácia geral.

## 4. Fallbacks e incerteza técnica

| Conjunto | Case_id | Score | Esperado | Modo efetivo |
| --- | --- | --- | --- | --- |
| DEV01 | p3_dev_isolated_answer | 2 | 2 | TME_SEMANTIC_FORMAL_NATIVE_FALLBACK |
| Robustness01 | p3_rob_f08 | 0 | 0 | TME_SEMANTIC_FORMAL_NATIVE_FALLBACK |
| Safety02/new32 | p3_safe_s2_05 | 0 | 0 | TME_SEMANTIC_FORMAL_NATIVE_FALLBACK |
| Safety03 | p3_s03_c03 | 0 | 1 | TME_SEMANTIC_FORMAL_NATIVE_FALLBACK |
| Safety03 | p3_s03_d01 | 0 | 0 | TME_SEMANTIC_FORMAL_NATIVE_FALLBACK |
| Safety03 | p3_s03_d06 | 0 | 2 | TME_SEMANTIC_FORMAL_NATIVE_FALLBACK |

Nos seis registros: `ValueError:recorded_extraction_unavailable`, status do provider `unavailable`, sem chamada útil ao SemanticExtractor nesta execução. O runner encontrou ausência ou insucesso do output gravado e seguiu o fallback nativo unificado. Esses seis casos não sustentam desempenho do SemanticExtractor. Safety02/observed48 possui output disponível para Robustness/F08, ao contrário da rodada original Robustness01.

**Technical uncertainty = 0 em todos os conjuntos**, inclusive fallback. Isso não transforma indisponibilidade de replay em sucesso semântico; são eixos distintos. C03 e D06 de Safety03 perdem1 e2 pontos respectivamente no fallback, sem hard veto registrado.

## 5. Estados observados e autoridade

Contagens por evidence_id/receipt; aliases semântico/nativo podem duplicar uma afirmação textual. Decisões candidatas são distintas de ações finais por obrigação. Um candidato negativo REVIEW_ONLY de um checker VERIFIED pode coexistir com um candidato positivo AUTO_AWARD do mesmo checker; isso não é award produzido por REVIEW_ONLY.

### Discourse states

| Conjunto | ACTIVE | SUPERSEDED | NON_ADOPTED | AMBIGUOUS |
| --- | --- | --- | --- | --- |
| DEV01 | 25 | 0 | 1 | 1 |
| DEV02 | 26 | 0 | 1 | 1 |
| Robustness01 | 97 | 1 | 8 | 1 |
| Safety02/new32 | 86 | 10 | 12 | 7 |
| Safety02/observed48 | 97 | 1 | 8 | 2 |
| Safety03 | 72 | 7 | 6 | 11 |

### Representation fidelity

| Conjunto | EXACT | SUPPORTED_NORMALIZATION | PARTIAL | AMBIGUOUS | UNSUPPORTED |
| --- | --- | --- | --- | --- | --- |
| DEV01 | 15 | 10 | 0 | 0 | 2 |
| DEV02 | 16 | 10 | 0 | 0 | 2 |
| Robustness01 | 55 | 43 | 0 | 5 | 4 |
| Safety02/new32 | 94 | 3 | 0 | 3 | 15 |
| Safety02/observed48 | 55 | 43 | 0 | 5 | 5 |
| Safety03 | 56 | 6 | 0 | 3 | 31 |

### Binding status

| Conjunto | EXACT_BINDING | VALID_EQUIVALENT_BINDING | PARTIAL_BINDING | AMBIGUOUS_BINDING | INVALID_BINDING |
| --- | --- | --- | --- | --- | --- |
| DEV01 | 25 | 0 | 2 | 0 | 0 |
| DEV02 | 26 | 0 | 2 | 0 | 0 |
| Robustness01 | 97 | 0 | 4 | 5 | 1 |
| Safety02/new32 | 96 | 0 | 16 | 3 | 2 |
| Safety02/observed48 | 97 | 0 | 9 | 5 | 1 |
| Safety03 | 62 | 0 | 33 | 3 | 0 |

### Automation eligibility — decisões candidatas

| Conjunto | AUTO_AWARD | AUTO_VETO | REVIEW_ONLY |
| --- | --- | --- | --- |
| DEV01 | 17 | 6 | 48 |
| DEV02 | 17 | 6 | 49 |
| Robustness01 | 42 | 32 | 160 |
| Safety02/new32 | 18 | 46 | 142 |
| Safety02/observed48 | 42 | 32 | 165 |
| Safety03 | 27 | 20 | 144 |

### Automation eligibility — decisão final por obrigação

| Conjunto | AUTO_AWARD | AUTO_VETO | REVIEW_ONLY |
| --- | --- | --- | --- |
| DEV01 | 17 | 4 | 83 |
| DEV02 | 17 | 4 | 83 |
| Robustness01 | 42 | 25 | 557 |
| Safety02/new32 | 18 | 20 | 378 |
| Safety02/observed48 | 42 | 25 | 557 |
| Safety03 | 27 | 11 | 482 |

### Status de verificação

| Conjunto | Status e contagens |
| --- | --- |
| DEV01 | COMPOSITE_FAILED=3; COMPOSITE_VERIFIED=10; CONTEXT_REJECTED=3; DETERMINISTIC_VERIFIED=8; FORMAL_VERIFIED=1 |
| DEV02 | COMPOSITE_FAILED=3; COMPOSITE_VERIFIED=10; CONTEXT_REJECTED=3; DETERMINISTIC_VERIFIED=8; FORMAL_VERIFIED=1 |
| Robustness01 | COMPOSITE_FAILED=9; COMPOSITE_INCOMPLETE=6; COMPOSITE_VERIFIED=26; CONTEXT_REJECTED=20; DETERMINISTIC_FAILED=2; DETERMINISTIC_VERIFIED=21; FORMAL_VERIFIED=1 |
| Safety02/new32 | COMPOSITE_FAILED=4; COMPOSITE_INCOMPLETE=1; COMPOSITE_VERIFIED=11; CONTEXT_REJECTED=36; DETERMINISTIC_FAILED=11; DETERMINISTIC_VERIFIED=17; FORMAL_REFUTED=1; FORMAL_VERIFIED=2 |
| Safety02/observed48 | COMPOSITE_FAILED=9; COMPOSITE_INCOMPLETE=6; COMPOSITE_VERIFIED=26; CONTEXT_REJECTED=25; DETERMINISTIC_FAILED=2; DETERMINISTIC_VERIFIED=21; FORMAL_VERIFIED=1 |
| Safety03 | COMPOSITE_FAILED=3; COMPOSITE_INCOMPLETE=9; COMPOSITE_VERIFIED=13; CONTEXT_REJECTED=45; DETERMINISTIC_FAILED=6; DETERMINISTIC_VERIFIED=20; FORMAL_VERIFIED=1 |

405 resultados de verificação:95 DETERMINISTIC_VERIFIED,96 COMPOSITE_VERIFIED,132 CONTEXT_REJECTED,7 FORMAL_VERIFIED,31 COMPOSITE_FAILED,22 COMPOSITE_INCOMPLETE,21 DETERMINISTIC_FAILED e1 FORMAL_REFUTED. O campo formal_status, inclusive componentes de compostos, registra35 FORMAL_VERIFIED,1 FORMAL_REFUTED e369 FORMAL_NOT_ATTEMPTED. Não foram observados FORMAL_ERROR ou FORMAL_UNPROVED; ausência de tentativa e incompletude não foram tratadas como refutação.

Houve **36 resultados com formal_attempted=true**, dos quais35 verificados e1 refutado, incluindo aritmética dentro dos checkers compostos. Isso não significa36 subprocessos únicos: uma execução pode ser referenciada em mais de um resultado. O replay usou `use_lean=True`; arquivos Lean e hashes foram preservados. Em Safety03/B02, `((2 : ℚ)/(6 : ℚ)) = ((1 : ℚ)/(3 : ℚ))`, método norm_num, compiled=true, stdout/stderr vazios, sem categoria de falha. A suíte executou também B02 real e os dois testes `test_real_lean_after_validated_retraction` (igualdade verdadeira e refutação).

## 6. Casos obrigatórios — julgamento causal

| Caso | Esperado autorizado | Obtido | Parcelas concedidas |
| --- | --- | --- | --- |
| p3_s03_a05 | 0 | 0 | nenhuma |
| p3_s03_b02 | 2 | 2 | a.probability=2 |
| p3_s03_b04 | 1 | 1 | c.continue=1 |
| p3_s03_b05 | 2 | 2 | b.conclusion=2 |
| p3_s03_b08 | 2 | 2 | a.count=2 |
| p3_s03_e01 | 4 | 4 | a.count=2, a.probability=2 |
| p3_rob_e02 | 4 | 4 | a.count=2, b.same=2 |
| p3_rob_e04 | 2 | 2 | a.count=2 |
| p3_rob_a08 | 8 | 8 | c.continue=1, c.first_strategy=2, c.second_strategy=2, c.conditionals=1, c.total=2 |
| p3_rob_e08 | 2 | 2 | b.same=2 |
| p3_safe_s2_03 | 0 | 0 | nenhuma |
| p3_safe_s2_06 | 2 | 2 | b.different=2 |
| p3_safe_s1_02 | 2 | 2 | b.space=2 |
| p3_safe_s1_03 | 2 | 2 | c.second_strategy=2 |
| p3_safe_s1_07 | 1 | 1 | c.continue=1 |
| p3_safe_s4_07 | 2 | 2 | a.count=2 |

**p3_s03_a05:** A lista fechada {6} foi verificada, mas a inclusão adicional do3 continua ACTIVE. A representação negativa é o átomo member(3), EXACT; não um conjunto exaustivo inventado. O finite checker consulta a segunda cor ao repetir3, refuta branca, e a política central veta b.same e sua dependência b.conclusion. Score0; nenhum falso crédito. A rejeição positiva do átomo não o converte em REVIEW com autoridade: o AUTO_VETO tem checker e receipt negativos próprios.

**p3_s03_b02:** 1/2 está SUPERSEDED. A igualdade escrita2/6=1/3 está ACTIVE/EXACT, foi compilada/provada por Lean e recebe a.probability=2. Nenhum veto herdado da estimativa retirada.

**p3_s03_b04:** {1,4} está SUPERSEDED; {1,2} ACTIVE/EXACT é verificado deterministicamente e recebe c.continue=1. Nenhum veto da primeira lista.

**p3_s03_b05:** 7/36 está SUPERSEDED e sua representação antiga é AMBIGUOUS; não ganha autoridade negativa.11/36 está ACTIVE/EXACT e passa a rota result_value do composto, recebendo b.conclusion=2. “Conferir a partição” não recebe crédito de método nem substitui relação escrita.

**p3_s03_b08:** quatro está SUPERSEDED; “duas” é normalização suportada para2 na quantidade escrita. Checker determinístico recebe a.count=2; a correção não usa a verdade matemática para reclassificar o discurso.

**p3_s03_e01:** 7/12 de colega está NON_ADOPTED.1/3 e2 próprios permanecem ACTIVE, exact e ligados a obrigações distintas: a.probability=2 e a.count=2. A correção do falso veto recupera2; a contagem independente recupera outros2. São4 pontos, não4 pontos atribuíveis ao veto anterior.

**p3_rob_e02:** O quinto é SUPERSEDED por correção adjacente validada; {6} é ACTIVE e verificado. a.count=2+b.same=2. A antiga expectativa2 é mostrada nas métricas literais; a política autorizada exige4.

**p3_rob_e04:** A lista exclusiva{6} e a inclusão do quinto permanecem ACTIVE. O payload legado pode mostrar{5,6}, mas a proposição realmente checada é member(5), com relação explícita ao span anterior. Refutação finita e incompatibilidade estrutural vetam b.same/b.conclusion. a.count=2 permanece independente.

**p3_rob_a08:** Estão escritos continuação{1,2}, preta com3 saídas no caso1, cinza com3 no caso2, condicionais3/6=1/2 e total(2/6)*(1/2)=1/6. O modelo finito valida cores, contagens e optimality; condicionais e total exigem esses suportes. A ordem textual invertida não impede o vínculo. Award:1+2+2+1+2=8. Nenhuma justificação é fabricada a partir de números isolados.

**p3_rob_e08:** A inclusão do quinto atribuída a Beatriz está NON_ADOPTED; a resposta própria exclusiva{6} está ACTIVE. b.same=2, sem veto. A recuperação de representação conserva o veto contextual local.

**p3_safe_s2_03:** continuar{1,2} passa como valor, mas a inclusão escrita/adotada do4 contradiz a exclusividade. Guard estrutural e política central bloqueiam c.continue e c.total;0p. O guard não gera witness positivo.

**p3_safe_s2_06:** 2*5=10, com relação de compartimentos distintos, sustenta b.different=2. O terceiro na repetição é member(3) refutado; bloqueia b.same e b.conclusion.11/36 verificado como valor não ignora a dependência negativa. O crédito distinto permanece local e independente.

**p3_safe_s1_02:** 6*5=30 retirado está SUPERSEDED, incluindo aliases nativos.6^2=36 permanece ACTIVE; composto confirma espaço amostral e duas escolhas uniformes escritas. b.space=2. Nenhum veto do guard antigo.

**p3_safe_s1_03:** Aposta preta/contagem antiga do caso2 estão SUPERSEDED. A estratégia cinza+3 revisada passa o modelo finito, c.second_strategy=2. Uma representação antiga insuficiente não recebe autoridade negativa.

**p3_safe_s1_07:** continuar{2,3} está SUPERSEDED. O conjunto{1,2} revisado está ACTIVE, verificado, c.continue=1. Nenhum veto antigo.

**p3_safe_s4_07:** A correção é só da contagem:5 SUPERSEDED,2 ACTIVE, a.count=2.5/6 permanece ACTIVE e falso; a.probability recebe veto legítimo, sem contaminar a.count. O outro span ambíguo sobre5/6 fica REVIEW_ONLY e não é a fonte do veto.

Os cinco casos Safety03 recuperam seus9 pontos de falso veto anterior (2+1+2+2+2); E01 ainda mantém os2 de contagem independente. Os quatro falsos positivos antigos dos guards mantêm7 pontos (2+2+1+2). O apêndice A apresenta as cadeias completas resumidas por claim; os receipts íntegros são arquivados por registro.

## 7. Regressões causais que impedem prontidão

### Safety02/S1_05 — veto material sobre correção explícita

A fonte declara1/6 como estimativa inicial,11/36 como correto e, depois, “A linha correta substitui integralmente minha primeira estimativa; ela é a única resposta que mantenho.” O resolver mantém ambas ACTIVE.1/6 é EXACT/EXACT_BINDING e COMPOSITE_FAILED; produz AUTO_VETO aplicado a b.second_white_probability.11/36 é EXACT, COMPOSITE_VERIFIED, sufficient=true, mas sua decisão positiva fica REVIEW_ONLY **somente por central_veto_applied**. Resultado0 em vez dos2 previstos. Classificação: FALSE_VETO material; falha de discurso/retração, não de aritmética nem de integridade do receipt.

No trace unificado anterior, score0 sem conflitos ou veto aplicado; havia perda de representação/suporte. O Multi-Layer recupera a verificação positiva e, simultaneamente, introduz autoridade negativa indevida. Portanto, Δscore=0 oculta a regressão causal.

### Safety03/E05 — citação não adotada e afirmação corrigida tratadas como ativas

“Cito sem adotar a fala de Célia: «inferiores_brancas:6»” deve ser NON_ADOPTED; a contagem própria1 é explicitamente corrigida para2 e deve ser SUPERSEDED. Os três claims ficam ACTIVE, com fidelity EXACT/binding EXACT. Os checkers refutam6 e1 corretamente, mas ambos recebem AUTO_VETO indevido sobre a.count.2 está DETERMINISTIC_VERIFIED/sufficient=true e é bloqueado exclusivamente por central_veto_applied. Resultado0/2. Classificação: FALSE_VETO material de discurso/adoção e retraction. Não é possível usar a exatidão numérica do checker como validação de autoria/adoção.

No trace original de Safety03, as representações eram rejeitadas, sem conflito aplicado; o score já era0. O novo mecanismo negativo introduziu veto material sobre um witness agora verificado.

### Safety03/C06 — exemplo de erro explicitamente não assumido

A fonte apresenta6 como erro explicado e diz “Não assumo essa contagem”, antes de declarar2. O primeiro claim fica ACTIVE/EXACT/EXACT_BINDING e gera DETERMINISTIC_FAILED→AUTO_VETO sobre a.count; deveria ser NON_ADOPTED. A afirmação correta2 é adicionalmente UNSUPPORTED/PARTIAL_BINDING por white_count_not_bound_to_written_quantity e fica CONTEXT_REJECTED/REVIEW_ONLY. Resultado0/2. Há FALSE_VETO aplicado e MISSED_CREDIT, mas remover apenas o veto não garantiria os2 pontos nesta execução. Não se soma a perda duas vezes.

Os três já aparecem no replay salvo durante a implementação, que esta execução reproduziu. São novos em relação às autoridades negativas dos respectivos traces **anteriores à implementação**, não novos em relação a uma segunda execução dos mesmos bytes. O relatório anterior verificara ausência de perda de award; esta auditoria amplia a verificação para a causa das notas0. Evidências comparativas e hashes: `analysis/causal_regressions.json`.

## 8. Créditos perdidos e limites remanescentes

| Conjunto | Caso | Score/esperado | Missed obrigações | Pontos perdidos | Causa |
| --- | --- | --- | --- | --- | --- |
| Robustness01 | p3_rob_a01 | 0/2 | a.bottom_white_count | 2 | contagem em prosa: white_count_not_bound_to_written_quantity; sem veto |
| Robustness01 | p3_rob_a02 | 0/2 | a.first_white_probability | 2 | “uma em três” não admitido: payload_not_in_assertion; sem veto |
| Robustness01 | p3_rob_a06 | 0/2 | c.strategy_case_1 | 2 | subject_not_uniquely_bound_to_source_clause; AMBIGUOUS_BINDING no caso1 |
| Robustness01 | p3_rob_a07 | 0/2 | c.strategy_case_2 | 2 | subject_not_uniquely_bound_to_source_clause; AMBIGUOUS_BINDING no caso2 |
| Safety02/new32 | p3_safe_s1_05 | 0/2 | b.second_white_probability | 2 | falso veto material; seção7 |
| Safety02/new32 | p3_safe_s3_07 | 0/2 | c.strategy_case_1 | 2 | cor positiva exata, contagem “preta:3 vezes” sem representação admitida; COMPOSITE_INCOMPLETE, sem veto |
| Safety02/observed48 | p3_rob_a01 | 0/2 | a.bottom_white_count | 2 | contagem em prosa: white_count_not_bound_to_written_quantity; sem veto |
| Safety02/observed48 | p3_rob_a02 | 0/2 | a.first_white_probability | 2 | “uma em três” não admitido: payload_not_in_assertion; sem veto |
| Safety02/observed48 | p3_rob_a06 | 0/2 | c.strategy_case_1 | 2 | subject_not_uniquely_bound_to_source_clause; AMBIGUOUS_BINDING no caso1 |
| Safety02/observed48 | p3_rob_a07 | 0/2 | c.strategy_case_2 | 2 | subject_not_uniquely_bound_to_source_clause; AMBIGUOUS_BINDING no caso2 |
| Safety03 | p3_s03_a06 | 0/2 | c.strategy_case_1 | 2 | contagem “Nesse cenário…” UNSUPPORTED/AMBIGUOUS; cor sozinha não completa estratégia |
| Safety03 | p3_s03_b06 | 0/2 | c.strategy_case_1 | 2 | contagem_1 não vinculada à cor; antigo cinza ainda ACTIVE, porém sem refutação/hard veto; composto incompleto |
| Safety03 | p3_s03_c01 | 0/2 | a.bottom_white_count | 2 | a própria afirmação “Fora dessa hipótese…” foi NON_ADOPTED indevidamente; rejeição de contexto, sem hard veto |
| Safety03 | p3_s03_c03 | 0/1 | c.continue_compartments | 1 | output histórico indisponível; fallback sem witness |
| Safety03 | p3_s03_c06 | 0/2 | a.bottom_white_count | 2 | falso veto + representação positiva insuficiente; seção7 |
| Safety03 | p3_s03_d06 | 0/2 | a.bottom_white_count | 2 | output histórico indisponível; fallback sem witness |
| Safety03 | p3_s03_d08 | 0/2 | c.strategy_case_2 | 2 | contagem de cinzas não vinculada; estratégia incompleta; nenhuma propagação negativa das alternativas abertas |
| Safety03 | p3_s03_e03 | 2/4 | a.bottom_white_count | 2 | contagem revisada2 continua UNSUPPORTED; probabilidade independente1/3 preserva2p |
| Safety03 | p3_s03_e05 | 0/2 | a.bottom_white_count | 2 | falso veto material; seção7 |
| Safety03 | p3_s03_e08 | 3/8 | c.conditional_success_2, c.strategy_case_2, c.total_win_probability | 5 | contagem_2 após correção não vinculada à cor; perde estratégia2, conditional2,total; continuam1+2p de continue e estratégia1 |

As demais perdas não são reclassificadas artificialmente como falsos vetos. C01, por exemplo, tem erro semântico de escopo; sua ação mecânica é rejeição local, sem AUTO_VETO. E08 de Safety03 não é o E08 de Robustness: no primeiro faltam5 pontos; no segundo os2 esperados foram preservados. Não houve tuning ou alteração de expectativas para ocultar essas lacunas.

## 9. Invariantes Multi-Layer em execução

Foram inspecionadas1.013 decisões candidatas,305 ações automáticas (163 AUTO_AWARD/142 AUTO_VETO),2.392 decisões finais por obrigação e151 parcelas pontuadas. Todos os481 source_spans dos RepresentationReceipts batem literalmente com os offsets na fonte. A contagem de AUTO_VETO final é89 obrigações; múltiplos receipts podem atuar sobre a mesma obrigação e suas dependências.

| Invariante | Evidência executada | Resultado/limite |
| --- | --- | --- |
| Nenhum AUTO_AWARD com fidelity insuficiente | 265 premissas de163 ações, fidelity EXACT/SUPPORTED_NORMALIZATION | PASS nos receipts; não prova adequação universal do normalizador |
| Nenhum AUTO_VETO com fidelity insuficiente | 176 premissas de142 ações, mesmas condições | PASS nos receipts; estados ACTIVE incorretos causam os falsos vetos da seção7 |
| Nenhum AUTO_AWARD/AUTO_VETO com binding ambíguo | 441 premissas com binding admitido; referências ao receipt original conferidas | PASS |
| VERIFIED/REFUTED não aumentam fidelity | 1.390 cópias de provenance iguais aos receipts do snapshot; matriz de4 estados×5 fidelities×5 bindings com ambos resultados | PASS; test_F1_F6_admission_cross_product_cannot_be_elevated_by_math |
| REVIEW_ONLY não gera award nem hard veto | 708 candidatas sem autoridade positiva/negativa;163 awards com witness AUTO_AWARD;226 aplicações de veto autenticadas | PASS por decisão; não confundir candidatos positivos/negativos distintos |
| REVIEW_ONLY preserva créditos independentes | test_F8_F9_F19_F23_review_has_no_negative_edges_or_global_gate; E04/E08,S4_07,E01,E03 | PASS mecânico nos testes; não é garantia semântica universal: C01 perde a afirmação independente por escopo NON_ADOPTED incorreto, e D08/E03/E08 por representação insuficiente |
| Guard nunca gera award | 163 witnesses possuem original_fact, checker positivo e guard_only falso; nenhum witness de guard | PASS;0 guard-generated awards |
| Nenhum bypass da AutomationEligibilityPolicy | 163 awards ligados à decisão emitida;226 aplicações negativas ligadas a AUTO_VETO e política central; mutation/authentication tests | PASS nos caminhos exercitados |
| Provenance completo para cada ação automática | 305 source hashes/ledger revisions/checker refs/input digests;441 proposition digests e vínculos de segmentos;1.013 decision digests | PASS; receipts íntegros no arquivo por caso |
| Sem falso veto material sobre fonte não adotada/retirada | Auditoria de fonte e contratos, não somente enums do trace | FAIL: S1_05 e E05; C06 adiciona veto indevido concorrente com representação perdida |

Zero violações **mecânicas** na auditoria de receipts (`invariant_checks`/`invariant_violations` em metrics.json). Isso não equivale a zero erro semântico: a política autentica fielmente um snapshot cujo estado discursivo pode estar errado. Não há bypass nesses três falsos vetos; há admissão de premissas com adoção incorretamente validada.

## 10. FALSE AUTOMATIC CREDIT AUDIT

| Pergunta | Resultado |
| --- | --- |
| Novo falso crédito conforme fontes/contratos observados | 0 casos/0 pontos; E02 fica explicitamente separado da fixture histórica |
| Parcela pontuada sem checker | 0;151 parcelas exigem obrigações elegíveis,163 witnesses verificados/suficientes |
| Crédito apenas por interpretação do LLM | 0 encontrado nos registros; toda ação positiva passou pelo checker e política |
| Guard gerou award | 0 |
| COMPOSITE_FAILED ou refutação gerou a mesma parcela | 0 encontrado; conflito negativo aplicado bloqueia a parcela e dependências previstas |
| CONTEXT_REJECTED/REVIEW_ONLY gerou award | 0 por decisão/witness; evidência independente pode sustentar outra decisão |
| Insuficiência promovida a refutação | 0 encontrado; COMPOSITE_INCOMPLETE/FORMAL_NOT_ATTEMPTED não autorizam hard veto |
| Novos falsos vetos materiais | 2 diretamente bloqueando witnesses suficientes;1 falso veto adicional com representação positiva insuficiente |

Zero falso crédito é uma conclusão circunscrita a estes contratos observados e à auditoria causal realizada, não uma estimativa de precisão fora da amostra. As fontes não foram enviadas a serviço externo, gold externo e holdout não foram acessados.

## 11. Critério de saída e preservação

| Critério para prontidão | Resultado |
| --- | --- |
| Zero novo falso crédito | PASS dentro dos contratos observados, ressalva documental E02 |
| Zero novo falso veto material | FAIL: Safety02/S1_05 e Safety03/E05; C06 também indevido |
| A05 corrigido | PASS,0p e negativa checada |
| Cinco falsos vetos prioritários corrigidos | PASS,B02/B04/B05/B08/E01 |
| Zero guard-generated awards / awards sem checker / bypass | PASS nos184 registros e testes selecionados |
| Invariantes críticos | Integridade/autenticação PASS; adequação discursiva negativa FAIL nos casos apontados |

HEAD inicial e final: `8fc68fa49cb833f45b854e7e3cced747efa9dcbb`. Antes de criar este relatório: `git status --short` vazio; 1331 arquivos congelados sem alteração. Ao entregar, a única novidade não ignorada deve ser `?? docs/audits/TME_P3_MULTI_LAYER_REGRESSION_01.md`; os artefatos novos ficam no diretório de avaliações ignorado pelo Git. Nenhum commit foi criado. Nenhuma correção foi implementada. Safety04 não foi executado.

**`P3_MULTI_LAYER_REGRESSION_FAILED`**. O resultado não permite `READY_FOR_P3_SAFETY_04`. Não se reivindica revalidação de segurança geral, acurácia contra gold ou desempenho de holdout. Todos estes textos e outputs continuam DEV observado e não podem ser usados futuramente como avaliação independente.

## Apêndice A — cadeias dos casos obrigatórios e de todos os casos com perda

Cada linha resume `source_span → segment/assertion_range → representation → fidelity/discourse → binding → automation → checker → veto/reconciliation → award`. IDs longos são abreviados na tabela; o JSON.gz apontado contém os IDs completos, premises, componentes de checkers, witnesses, sufficiency, hashes e dependências. As fontes originais são reproduzidas integralmente. Aliases com cadeias idênticas são agrupados por span/representação/estado. Cada execução repetida também possui seu próprio audit.json.gz, sem deduplicação dos artefatos.

### p3_rob_a01 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_a01.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_a01.audit.json.gz)

```text
a) Duas das seis bolas inferiores são brancas.
```

contagem em prosa: white_count_not_bound_to_written_quantity; sem veto.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Duas das seis bolas inferiores são brancas. [[3, 46]] | segment:40d1c04e56adc2fa… assertion=[3, 46] | 2; UNSUPPORTED; white_count_not_bound_to_written_quantity | ACTIVE; literal_own_assertion | a.bottom_white_count: PARTIAL_BINDING | a.bottom_white_count: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_rob_a02 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_a02.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_a02.audit.json.gz)

```text
a) A chance de a primeira bola ser branca é uma em três.
```

“uma em três” não admitido: payload_not_in_assertion; sem veto.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A chance de a primeira bola ser branca é uma em três. [[3, 56]] | segment:b5090495e317c3c9… assertion=[3, 56] | 1/3; UNSUPPORTED; payload_not_in_assertion | ACTIVE; literal_own_assertion | a.first_white_probability: PARTIAL_BINDING | a.first_white_probability: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_rob_a06 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_a06.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_a06.audit.json.gz)

```text
c) Depois da branca no primeiro compartimento, preta é a melhor escolha; no caso 1 a preta aparece três vezes.
```

subject_not_uniquely_bound_to_source_clause; AMBIGUOUS_BINDING no caso1.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Depois da branca no primeiro compartimento, preta é a melhor escolha; no caso 1 a preta aparece três vezes. [[3, 110]] | segment:0e03cad9825b3cb4… assertion=[73, 110] | 3; AMBIGUOUS; subject_not_uniquely_bound_to_source_clause | ACTIVE; literal_own_assertion | c.strategy_case_1: AMBIGUOUS_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Depois da branca no primeiro compartimento, preta é a melhor escolha; no caso 1 a preta aparece três vezes. [[3, 110]] | segment:3870aa2ce790f014… assertion=[3, 71] | black; AMBIGUOUS; subject_not_uniquely_bound_to_source_clause | ACTIVE; literal_own_assertion | c.strategy_case_1: AMBIGUOUS_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_rob_a07 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_a07.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_a07.audit.json.gz)

```text
c) No segundo compartimento, após a branca, cinza maximiza a chance; no caso 2 a cinza aparece três vezes.
```

subject_not_uniquely_bound_to_source_clause; AMBIGUOUS_BINDING no caso2.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| No segundo compartimento, após a branca, cinza maximiza a chance; no caso 2 a cinza aparece três vezes. [[3, 106]] | segment:1db45e529cea2994… assertion=[69, 106] | 3; AMBIGUOUS; subject_not_uniquely_bound_to_source_clause | ACTIVE; literal_own_assertion | c.strategy_case_2: AMBIGUOUS_BINDING | c.strategy_case_2: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| No segundo compartimento, após a branca, cinza maximiza a chance; no caso 2 a cinza aparece três vezes. [[3, 106]] | segment:d0ce1d524423f26d… assertion=[3, 67] | cinza; AMBIGUOUS; subject_not_uniquely_bound_to_source_clause | ACTIVE; literal_own_assertion | c.strategy_case_2: AMBIGUOUS_BINDING | c.strategy_case_2: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_rob_a08 — 8 / 8

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_a08.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_a08.audit.json.gz)

```text
c) A probabilidade total de vitória é um sexto, com (2/6)*(1/2)=1/6.
Após sair branca do compartimento 2, escolho cinza, que aparece três vezes.
No caso 2, a probabilidade condicional de sucesso é 3/6=1/2.
O jogo continua somente nos compartimentos 1 e 2.
Após sair branca do compartimento 1, escolho preta, que aparece três vezes.
No caso 1, a probabilidade condicional de sucesso é 3/6=1/2.
```

Estão escritos continuação{1,2}, preta com3 saídas no caso1, cinza com3 no caso2, condicionais3/6=1/2 e total(2/6)*(1/2)=1/6. O modelo finito valida cores, contagens e optimality; condicionais e total exigem esses suportes. A ordem textual invertida não impede o vínculo. Award:1+2+2+1+2=8. Nenhuma justificação é fabricada a partir de números isolados.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A probabilidade total de vitória é um sexto, com (2/6)*(1/2)=1/6. [[3, 68]] | segment:1a7e7e66710d5a06… assertion=[3, 68] | (2/6)*(1/2)=1/6; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.total_win_probability: EXACT_BINDING | c.total_win_probability: AUTO_AWARD; c.total_win_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:6705fac2b0209b65dd48: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:a5ed7c5d3575a9eb30cb: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.total=2 |
| Após sair branca do compartimento 2, escolho cinza, que aparece três vezes. [[69, 144]] | segment:1042079f9c8f6277… assertion=[69, 144] | 3; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_2: EXACT_BINDING | c.conditional_success_2: AUTO_AWARD; c.conditional_success_2: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.strategy_case_2: AUTO_AWARD; c.strategy_case_2: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.total_win_probability: AUTO_AWARD; c.total_win_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:237a20cf273b52d3aeec: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:5bbfeda579458b29ed68: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:6705fac2b0209b65dd48: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:a5ed7c5d3575a9eb30cb: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:f0c7ac02a23e5e3e80b3: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:fc8c86fe1de1ab23ad6e: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.second_strategy=2, c.conditionals=1, c.total=2 |
| Após sair branca do compartimento 2, escolho cinza, que aparece três vezes. [[69, 144]] | segment:e0705de8d1a05a7d… assertion=[69, 119] | cinza; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_2: EXACT_BINDING | c.conditional_success_2: AUTO_AWARD; c.conditional_success_2: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.strategy_case_2: AUTO_AWARD; c.strategy_case_2: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.total_win_probability: AUTO_AWARD; c.total_win_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:237a20cf273b52d3aeec: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:5bbfeda579458b29ed68: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:6705fac2b0209b65dd48: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:a5ed7c5d3575a9eb30cb: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:f0c7ac02a23e5e3e80b3: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:fc8c86fe1de1ab23ad6e: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.second_strategy=2, c.conditionals=1, c.total=2 |
| No caso 2, a probabilidade condicional de sucesso é 3/6=1/2. [[145, 205]] | segment:906c6106f19ae598… assertion=[145, 205] | 3/6=1/2; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.conditional_success_2: EXACT_BINDING | c.conditional_success_2: AUTO_AWARD; c.conditional_success_2: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.total_win_probability: AUTO_AWARD; c.total_win_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:237a20cf273b52d3aeec: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:6705fac2b0209b65dd48: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:a5ed7c5d3575a9eb30cb: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:fc8c86fe1de1ab23ad6e: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.conditionals=1, c.total=2 |
| O jogo continua somente nos compartimentos 1 e 2. [[206, 255]] | segment:f2c8597e6e1e8381… assertion=[206, 255] | {1, 2}; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | c.continue_compartments: EXACT_BINDING | c.continue_compartments: AUTO_AWARD; c.continue_compartments: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.total_win_probability: AUTO_AWARD; c.total_win_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:5d40c4a45b2609bf6402: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:6705fac2b0209b65dd48: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:a5ed7c5d3575a9eb30cb: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:f78ec2be96d8fe364a00: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.continue=1, c.total=2 |
| Após sair branca do compartimento 1, escolho preta, que aparece três vezes. [[256, 331]] | segment:a1d5a6bb24e96d9e… assertion=[256, 331] | 3; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_1: EXACT_BINDING | c.conditional_success_1: AUTO_AWARD; c.conditional_success_1: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.strategy_case_1: AUTO_AWARD; c.strategy_case_1: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.total_win_probability: AUTO_AWARD; c.total_win_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:6705fac2b0209b65dd48: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:91080845485cc951f181: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:a5ed7c5d3575a9eb30cb: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:a942dfd3f8e65a164331: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:abaa85b5c3df146963ec: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:b66dfd5455a72195c435: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.first_strategy=2, c.conditionals=1, c.total=2 |
| Após sair branca do compartimento 1, escolho preta, que aparece três vezes. [[256, 331]] | segment:237630f0066fa00b… assertion=[256, 306] | preta; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_1: EXACT_BINDING | c.conditional_success_1: AUTO_AWARD; c.conditional_success_1: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.strategy_case_1: AUTO_AWARD; c.strategy_case_1: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.total_win_probability: AUTO_AWARD; c.total_win_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:6705fac2b0209b65dd48: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:91080845485cc951f181: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:a5ed7c5d3575a9eb30cb: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:a942dfd3f8e65a164331: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:abaa85b5c3df146963ec: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:b66dfd5455a72195c435: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.first_strategy=2, c.conditionals=1, c.total=2 |
| No caso 1, a probabilidade condicional de sucesso é 3/6=1/2. [[332, 392]] | segment:7c6c456428501b24… assertion=[332, 392] | 3/6=1/2; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.conditional_success_1: EXACT_BINDING | c.conditional_success_1: AUTO_AWARD; c.conditional_success_1: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.total_win_probability: AUTO_AWARD; c.total_win_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:6705fac2b0209b65dd48: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:91080845485cc951f181: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:a5ed7c5d3575a9eb30cb: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:b66dfd5455a72195c435: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.conditionals=1, c.total=2 |

Parcelas finais do caso: c.continue=1, c.first_strategy=2, c.second_strategy=2, c.conditionals=1, c.total=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_rob_e02 — 4 / 4

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_e02.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_e02.audit.json.gz)

```text
a) Há duas bolas brancas embaixo.
b) Ao repetir o mesmo compartimento, o quinto também libera branca.
Na verdade, ao repetir o mesmo compartimento, somente o sexto libera branca.
```

O quinto é SUPERSEDED por correção adjacente validada; {6} é ACTIVE e verificado. a.count=2+b.same=2. A antiga expectativa2 é mostrada nas métricas literais; a política autorizada exige4.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Há duas bolas brancas embaixo. [[3, 33]] | segment:bbd0a4bf41836020… assertion=[3, 33] | 2; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: AUTO_AWARD; a.bottom_white_count: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:43c5b7d82cec86a979d7: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:e5e6bfb39ffc3ed09afd: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: a.count=2 |
| Ao repetir o mesmo compartimento, o quinto também libera branca. [[37, 101]] | segment:116f363a69440dab… assertion=[37, 101] | member([5]); EXACT; literal_membership_not_exhaustive_set | SUPERSEDED; validated_local_replacement | b.same_compartment: EXACT_BINDING | b.same_compartment: REVIEW_ONLY [central_veto_not_authorized,discourse_superseded]; b.same_compartment: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,membership_is_not_positive_set,no_checker_receipt,no_positive_checker_fact] | structural:6c4f4ab8612d99007825fb7a2f01439426b3eabe29f3ae730713b8565ef73fe8: STRUCTURAL_INCOMPATIBILITY_VERIFIED; suff=False | sem hard veto; parcelas da obrigação no caso: b.same=2 |
| Na verdade, ao repetir o mesmo compartimento, somente o sexto libera branca. [[102, 178]] | segment:533a34d7ab4a58c0… assertion=[102, 178] | {6}; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | b.same_compartment: EXACT_BINDING | b.same_compartment: AUTO_AWARD; b.same_compartment: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; b.same_compartment: REVIEW_ONLY [central_veto_not_authorized,discourse_superseded] | structural:6c4f4ab8612d99007825fb7a2f01439426b3eabe29f3ae730713b8565ef73fe8: STRUCTURAL_INCOMPATIBILITY_VERIFIED; suff=False; tme2-p3-check.v1:7d500737a39e9c68d993: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:99dcb90796eed5858290: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: b.same=2 |

Parcelas finais do caso: a.count=2, b.same=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_rob_e04 — 2 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_e04.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_e04.audit.json.gz)

```text
a) Há duas bolas brancas embaixo.
b) Ao repetir o mesmo compartimento, somente o sexto libera branca.
O quinto também.
```

A lista exclusiva{6} e a inclusão do quinto permanecem ACTIVE. O payload legado pode mostrar{5,6}, mas a proposição realmente checada é member(5), com relação explícita ao span anterior. Refutação finita e incompatibilidade estrutural vetam b.same/b.conclusion. a.count=2 permanece independente.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Há duas bolas brancas embaixo. [[3, 33]] | segment:89383bec6b008e2c… assertion=[3, 33] | 2; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: AUTO_AWARD; a.bottom_white_count: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:3ad265df6a5cd3dddbe8: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:95f38479bb8380a968f8: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: a.count=2 |
| Ao repetir o mesmo compartimento, somente o sexto libera branca. [[37, 101]] | segment:720193426c819677… assertion=[37, 101] | {6}; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | b.same_compartment: EXACT_BINDING | b.same_compartment: AUTO_VETO; b.same_compartment: REVIEW_ONLY [central_veto_applied]; b.same_compartment: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | structural:8609c5995fb1a06d7f8b81e3af8613582cc0ec70e0236f73f5cc9bf3f2c5b34c: STRUCTURAL_INCOMPATIBILITY_VERIFIED; suff=False; tme2-p3-check.v1:06f6ca5611a9f1413f7b: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:f98440fa999f823d73ee: DETERMINISTIC_VERIFIED; suff=True | b.same_compartment → b.same_compartment,b.second_white_probability (STRUCTURAL_INCOMPATIBILITY_VERIFIED); parcelas da obrigação no caso: nenhuma |
| O quinto também. [[102, 118]] | segment:a7602f948334becb… assertion=[102, 118] | member([5]); EXACT; literal_membership_not_exhaustive_set | ACTIVE; literal_own_assertion | b.same_compartment: EXACT_BINDING | b.same_compartment: AUTO_VETO; b.same_compartment: REVIEW_ONLY [central_veto_applied,checker_not_verified,insufficient,membership_is_not_positive_set,no_checker_receipt,no_positive_checker_fact] | p3-membership-guard:55056ad60830f9861c622eb6: DETERMINISTIC_FAILED; suff=False; structural:8609c5995fb1a06d7f8b81e3af8613582cc0ec70e0236f73f5cc9bf3f2c5b34c: STRUCTURAL_INCOMPATIBILITY_VERIFIED; suff=False | b.same_compartment → b.same_compartment,b.second_white_probability (DETERMINISTIC_FAILED); b.same_compartment → b.same_compartment,b.second_white_probability (STRUCTURAL_INCOMPATIBILITY_VERIFIED); parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: a.count=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_rob_e08 — 2 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_e08.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_e08.audit.json.gz)

```text
b) Beatriz disse que, ao repetir o mesmo compartimento, o quinto também libera branca.

Minha resposta: ao repetir o mesmo compartimento, somente o sexto libera branca.
```

A inclusão do quinto atribuída a Beatriz está NON_ADOPTED; a resposta própria exclusiva{6} está ACTIVE. b.same=2, sem veto. A recuperação de representação conserva o veto contextual local.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Beatriz disse que, ao repetir o mesmo compartimento, o quinto também libera branca. [[3, 86]] | segment:5e2ee3c18a3c9d11… assertion=[3, 86] | member([5]); EXACT; literal_membership_not_exhaustive_set | NON_ADOPTED; written_third_party_or_quotation | b.same_compartment: EXACT_BINDING | b.same_compartment: REVIEW_ONLY [central_veto_not_authorized,discourse_non_adopted]; b.same_compartment: REVIEW_ONLY [checker_not_verified,discourse_non_adopted,insufficient,membership_is_not_positive_set,no_checker_receipt,no_positive_checker_fact] | structural:87fc5d0c1043f67489094849b2c9235bbf928c15b0659357ba11cffc101477ff: STRUCTURAL_INCOMPATIBILITY_VERIFIED; suff=False | sem hard veto; parcelas da obrigação no caso: b.same=2 |
| Minha resposta: ao repetir o mesmo compartimento, somente o sexto libera branca. [[88, 168]] | segment:28ef6e5824362c89… assertion=[104, 168] | {6}; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | b.same_compartment: EXACT_BINDING | b.same_compartment: AUTO_AWARD; b.same_compartment: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; b.same_compartment: REVIEW_ONLY [central_veto_not_authorized,discourse_non_adopted] | structural:87fc5d0c1043f67489094849b2c9235bbf928c15b0659357ba11cffc101477ff: STRUCTURAL_INCOMPATIBILITY_VERIFIED; suff=False; tme2-p3-check.v1:826365cc5dc628473dac: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:a0ea0bd869180372d34b: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: b.same=2 |

Parcelas finais do caso: b.same=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_safe_s1_02 — 2 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s1_02.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s1_02.audit.json.gz)

```text
b) Minha primeira linha de contagem foi:
pares_ordenados: 6*5=30
Corrigindo a minha afirmação anterior:
pares_ordenados: 6^2=36
```

6*5=30 retirado está SUPERSEDED, incluindo aliases nativos.6^2=36 permanece ACTIVE; composto confirma espaço amostral e duas escolhas uniformes escritas. b.space=2. Nenhum veto do guard antigo.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pares_ordenados: 6*5=30 [[41, 64]] | segment:9ef03349ea2e130a… assertion=[41, 64] | 6*5=30; EXACT; source_checked_payload | SUPERSEDED; validated_local_replacement | b.ordered_pairs: EXACT_BINDING | b.ordered_pairs: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: b.space=2 |
| pares_ordenados: 6^2=36 [[104, 127]] | segment:2ba3d7008b52a5bf… assertion=[104, 127] | 6^2=36; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | b.ordered_pairs: EXACT_BINDING | b.ordered_pairs: AUTO_AWARD; b.ordered_pairs: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:60cbd461a7add5ede62e: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:ad1b0f87d39b4d0d5f9e: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:ffb96113dfc28bf761bb: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: b.space=2 |

Parcelas finais do caso: b.space=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_safe_s1_03 — 2 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s1_03.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s1_03.audit.json.gz)

```text
c) No estado após branca do compartimento 2, escolho preta e conto 3 posições dessa cor.
Pensando melhor, retiro essa escolha de cor e sua contagem.
Para o compartimento 2, após a branca, escolho cinza, que aparece 3 vezes.
```

Aposta preta/contagem antiga do caso2 estão SUPERSEDED. A estratégia cinza+3 revisada passa o modelo finito, c.second_strategy=2. Uma representação antiga insuficiente não recebe autoridade negativa.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| No estado após branca do compartimento 2, escolho preta e conto 3 posições dessa cor. [[3, 88]] | segment:3be29f2c54b86c33… assertion=[61, 88] | 3; UNSUPPORTED; color_count_not_bound_to_written_quantity | SUPERSEDED; validated_local_replacement | c.strategy_case_2: PARTIAL_BINDING | c.strategy_case_2: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: c.second_strategy=2 |
| No estado após branca do compartimento 2, escolho preta e conto 3 posições dessa cor. [[3, 88]] | segment:92cd21475ed9fe54… assertion=[45, 58] | black; SUPPORTED_NORMALIZATION; source_checked_payload | SUPERSEDED; validated_local_replacement | c.strategy_case_2: EXACT_BINDING | c.strategy_case_2: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: c.second_strategy=2 |
| Para o compartimento 2, após a branca, escolho cinza, que aparece 3 vezes. [[149, 223]] | segment:c80104f8b7b75fed… assertion=[188, 201] | gray; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_2: EXACT_BINDING | c.strategy_case_2: AUTO_AWARD; c.strategy_case_2: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:4a27ba433c25c6e844c6: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:edb6ae0611e4108a1273: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.second_strategy=2 |
| Para o compartimento 2, após a branca, escolho cinza, que aparece 3 vezes. [[149, 223]] | segment:51aaf5735882d484… assertion=[196, 223] | 3; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_2: EXACT_BINDING | c.strategy_case_2: AUTO_AWARD; c.strategy_case_2: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:4a27ba433c25c6e844c6: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:edb6ae0611e4108a1273: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.second_strategy=2 |

Parcelas finais do caso: c.second_strategy=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_safe_s1_05 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s1_05.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s1_05.audit.json.gz)

```text
b) Deixo inicialmente segunda_branca: 1/6
O correto é segunda_branca: 11/36
A linha correta substitui integralmente minha primeira estimativa; ela é a única resposta que mantenho.
```

falso veto material; seção7.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Deixo inicialmente segunda_branca: 1/6 [[3, 41]] | segment:6977f3b2b78f599e… assertion=[22, 41] | 1/6; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | b.second_white_probability: EXACT_BINDING | b.second_white_probability: AUTO_VETO; b.second_white_probability: REVIEW_ONLY [central_veto_applied,checker_not_verified,insufficient] | tme2-p3-check.v1:7b1abec88f379027c22f: COMPOSITE_FAILED; suff=False; tme2-p3-check.v1:c98be1311b836398630c: COMPOSITE_FAILED; suff=False | b.second_white_probability → b.second_white_probability (COMPOSITE_FAILED); parcelas da obrigação no caso: nenhuma |
| O correto é segunda_branca: 11/36 [[42, 75]] | segment:f8d2863f5a228acd… assertion=[54, 75] | 11/36; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | b.second_white_probability: EXACT_BINDING | b.second_white_probability: REVIEW_ONLY [central_veto_applied]; b.second_white_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:699394887a62c99f8d70: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:7abfd64d3eee448872c8: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_safe_s1_07 — 1 / 1

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s1_07.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s1_07.audit.json.gz)

```text
c) No registro inicial escrevi
continuar: {2,3}
Substituo integralmente esse conjunto pelo seguinte, que é o único adotado:
continuar: {1,2}
```

continuar{2,3} está SUPERSEDED. O conjunto{1,2} revisado está ACTIVE, verificado, c.continue=1. Nenhum veto antigo.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| continuar: {2,3} [[31, 47]] | segment:1a55eee1e7107cef… assertion=[31, 47] | {2,3}; EXACT; source_checked_payload | SUPERSEDED; validated_local_replacement | c.continue_compartments: EXACT_BINDING | c.continue_compartments: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: c.continue=1 |
| continuar: {1,2} [[124, 140]] | segment:df8554b99a093bdd… assertion=[124, 140] | {1,2}; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.continue_compartments: EXACT_BINDING | c.continue_compartments: AUTO_AWARD; c.continue_compartments: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:35bf7d3edfa7656dd42f: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:6687a33649b9e8c80ebc: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:718fa15408fa2ab9ee6a: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.continue=1 |

Parcelas finais do caso: c.continue=1. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_safe_s2_03 — 0 / 0

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s2_03.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s2_03.audit.json.gz)

```text
c) Registro os estados em que decido continuar: continuar: {1,2}.
Também mantenho o jogo em curso se a primeira branca for atribuída ao compartimento 4; essa inclusão integra minha resposta.
```

continuar{1,2} passa como valor, mas a inclusão escrita/adotada do4 contradiz a exclusividade. Guard estrutural e política central bloqueiam c.continue e c.total;0p. O guard não gera witness positivo.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Registro os estados em que decido continuar: continuar: {1,2}. [[3, 65]] | segment:1f8f4ee194ee9e71… assertion=[48, 64] | {1,2}; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.continue_compartments: EXACT_BINDING | c.continue_compartments: AUTO_VETO; c.continue_compartments: REVIEW_ONLY [central_veto_applied]; c.continue_compartments: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | structural:c115db902620d0ccf45ad17099c09fe53aa6682ecca3614027dc601221562688: STRUCTURAL_INCOMPATIBILITY_VERIFIED; suff=False; tme2-p3-check.v1:00155e32bcbae8a8f8b9: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:249d3ef1e0eb8575fae5: DETERMINISTIC_VERIFIED; suff=True | c.continue_compartments → c.continue_compartments,c.total_win_probability (STRUCTURAL_INCOMPATIBILITY_VERIFIED); parcelas da obrigação no caso: nenhuma |
| Também mantenho o jogo em curso se a primeira branca for atribuída ao compartimento 4; essa inclusão integra minha resposta. [[66, 190]] | segment:b924de0606ff2213… assertion=[66, 190] | member([4]); EXACT; literal_membership_not_exhaustive_set | ACTIVE; literal_own_assertion | c.continue_compartments: EXACT_BINDING | c.continue_compartments: AUTO_VETO; c.continue_compartments: REVIEW_ONLY [central_veto_applied,checker_not_verified,insufficient,membership_is_not_positive_set,no_checker_receipt,no_positive_checker_fact] | structural:c115db902620d0ccf45ad17099c09fe53aa6682ecca3614027dc601221562688: STRUCTURAL_INCOMPATIBILITY_VERIFIED; suff=False | c.continue_compartments → c.continue_compartments,c.total_win_probability (STRUCTURAL_INCOMPATIBILITY_VERIFIED); parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_safe_s2_06 — 2 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s2_06.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s2_06.audit.json.gz)

```text
b) Separei os eventos de compartimentos diferentes na linha
favoraveis_distintos: 2*5=10
Na minha enumeração, ao repetir o compartimento, o terceiro também fornece uma bola branca.
Apesar dessa inclusão, mantenho a probabilidade da segunda branca em 11/36.
```

2*5=10, com relação de compartimentos distintos, sustenta b.different=2. O terceiro na repetição é member(3) refutado; bloqueia b.same e b.conclusion.11/36 verificado como valor não ignora a dependência negativa. O crédito distinto permanece local e independente.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| favoraveis_distintos: 2*5=10 [[60, 88]] | segment:f29f9975f667d965… assertion=[60, 88] | 2*5=10; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | b.different_favorable: EXACT_BINDING | b.different_favorable: AUTO_AWARD; b.different_favorable: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:6c1eeb477782bc6d86e8: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:c2f219af21d3dadbbdc6: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:f0634724d347114d341c: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: b.different=2 |
| Na minha enumeração, ao repetir o compartimento, o terceiro também fornece uma bola branca. [[89, 180]] | segment:cc4099a5dee13c0d… assertion=[110, 180] | member([3]); EXACT; literal_membership_not_exhaustive_set | ACTIVE; literal_own_assertion | b.same_compartment: EXACT_BINDING | b.same_compartment: AUTO_VETO; b.same_compartment: REVIEW_ONLY [central_veto_applied,checker_not_verified,insufficient,membership_is_not_positive_set,no_checker_receipt,no_positive_checker_fact] | p3-membership-guard:b198b68f9f3ec01d6a89b35b: DETERMINISTIC_FAILED; suff=False | b.same_compartment → b.same_compartment,b.second_white_probability (DETERMINISTIC_FAILED); parcelas da obrigação no caso: nenhuma |
| Apesar dessa inclusão, mantenho a probabilidade da segunda branca em 11/36. [[181, 256]] | segment:9747a89899af90eb… assertion=[181, 256] | 11/36; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | b.second_white_probability: EXACT_BINDING | b.second_white_probability: REVIEW_ONLY [central_veto_applied]; b.second_white_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:5cfc551f81c0a7fee15e: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:e81258ce292faa040d83: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: b.different=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_safe_s3_07 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s3_07.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s3_07.audit.json.gz)

```text
c) Comparo uma alternativa com minha escolha final.
Não escolho cinza no caso 1, embora essa alternativa tenha 2 posições.
Minha decisão para a branca do compartimento 1 é preta, que aparece 3 vezes.
```

cor positiva exata, contagem “preta:3 vezes” sem representação admitida; COMPOSITE_INCOMPLETE, sem veto.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Comparo uma alternativa com minha escolha final. [[3, 51]] | segment:6e1855bc5d033e12… assertion=[3, 51] | Comparo uma alternativa com minha escolha final.; UNSUPPORTED; no_checker_representation | AMBIGUOUS; adoption_not_source_validated | c.strategy_case_1: PARTIAL_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,discourse_ambiguous,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Não escolho cinza no caso 1, embora essa alternativa tenha 2 posições. [[52, 122]] | segment:c32cbf888b7817e0… assertion=[52, 122] | cinza: 2 posições; UNSUPPORTED; negated_proposition_requires_explicit_representation | ACTIVE; literal_own_assertion | c.strategy_case_1: PARTIAL_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Não escolho cinza no caso 1, embora essa alternativa tenha 2 posições. [[52, 122]] | segment:e54cb7a39834bed3… assertion=[52, 79] | cinza; UNSUPPORTED; negated_proposition_requires_explicit_representation | ACTIVE; literal_own_assertion | c.strategy_case_1: PARTIAL_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Minha decisão para a branca do compartimento 1 é preta, que aparece 3 vezes. [[123, 199]] | segment:5f4a558a7a7ba91a… assertion=[123, 199] | preta: 3 vezes; UNSUPPORTED; payload_not_in_assertion | ACTIVE; literal_own_assertion | c.strategy_case_1: PARTIAL_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Minha decisão para a branca do compartimento 1 é preta, que aparece 3 vezes. [[123, 199]] | segment:ccd38d421a31c7b9… assertion=[123, 177] | preta; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_1: EXACT_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_safe_s4_07 — 2 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s4_07.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s4_07.audit.json.gz)

```text
a) Meu registro inicial contém duas quantidades:
inferiores_brancas: 5
primeira_branca: 5/6
Corrigindo apenas a contagem das bolas inferiores, substituo aquela contagem por
inferiores_brancas: 2
A probabilidade 5/6 permanece sendo minha resposta.
```

A correção é só da contagem:5 SUPERSEDED,2 ACTIVE, a.count=2.5/6 permanece ACTIVE e falso; a.probability recebe veto legítimo, sem contaminar a.count. O outro span ambíguo sobre5/6 fica REVIEW_ONLY e não é a fonte do veto.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| inferiores_brancas: 5 [[49, 70]] | segment:12e0a618d6681a06… assertion=[49, 70] | 5; EXACT; source_checked_payload | SUPERSEDED; validated_local_replacement | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: a.count=2 |
| primeira_branca: 5/6 [[71, 91]] | segment:6ffc5534016cbc6e… assertion=[71, 91] | 5/6; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | a.first_white_probability: EXACT_BINDING | a.first_white_probability: AUTO_VETO; a.first_white_probability: REVIEW_ONLY [central_veto_applied,checker_not_verified,insufficient] | tme2-p3-check.v1:14be8dea438d9419d3b3: DETERMINISTIC_FAILED; suff=False; tme2-p3-check.v1:7e33e2f0a43a4b3ddf5c: DETERMINISTIC_FAILED; suff=False; tme2-p3-check.v1:c4a3a59fb77ab296bc69: DETERMINISTIC_FAILED; suff=False | a.first_white_probability → a.first_white_probability (DETERMINISTIC_FAILED); parcelas da obrigação no caso: nenhuma |
| inferiores_brancas: 2 [[173, 194]] | segment:a6bb2568187d36a4… assertion=[173, 194] | 2; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: AUTO_AWARD; a.bottom_white_count: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:19ad40bcc6e9a09b24b0: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:56c86a44932afadcddf0: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:fd791c5b8b674ca283a4: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: a.count=2 |
| A probabilidade 5/6 permanece sendo minha resposta. [[195, 246]] | segment:cda139a50411792a… assertion=[195, 246] | 5/6; AMBIGUOUS; subject_not_uniquely_bound_to_source_clause | ACTIVE; written_own_assertion_unrepresented | a.first_white_probability: AMBIGUOUS_BINDING | a.first_white_probability: REVIEW_ONLY [central_veto_applied,checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: a.count=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_a05 — 0 / 0

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_a05.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_a05.audit.json.gz)

```text
b) Minha lista fechada de compartimentos que dão branca ao repetir é {6}. Acrescento uma afirmação que também considero válida: repetir o compartimento 3 dá branca.
```

A lista fechada {6} foi verificada, mas a inclusão adicional do3 continua ACTIVE. A representação negativa é o átomo member(3), EXACT; não um conjunto exaustivo inventado. O finite checker consulta a segunda cor ao repetir3, refuta branca, e a política central veta b.same e sua dependência b.conclusion. Score0; nenhum falso crédito. A rejeição positiva do átomo não o converte em REVIEW com autoridade: o AUTO_VETO tem checker e receipt negativos próprios.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minha lista fechada de compartimentos que dão branca ao repetir é {6}. [[3, 73]] | segment:a284063266a6f7e3… assertion=[3, 73] | {6}; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | b.same_compartment: EXACT_BINDING | b.same_compartment: AUTO_VETO; b.same_compartment: REVIEW_ONLY [central_veto_applied]; b.same_compartment: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | structural:2f707075538a03303d9847a75e7a83c247fce6b91dd3a530b7c07c53fdae3388: STRUCTURAL_INCOMPATIBILITY_VERIFIED; suff=False; tme2-p3-check.v1:ab4110b7fd51a0f58ac4: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:d54e7372af07b2ce710c: DETERMINISTIC_VERIFIED; suff=True | b.same_compartment → b.same_compartment,b.second_white_probability (STRUCTURAL_INCOMPATIBILITY_VERIFIED); parcelas da obrigação no caso: nenhuma |
| Acrescento uma afirmação que também considero válida: repetir o compartimento 3 dá branca. [[74, 164]] | segment:aa6cf222d79d7c9c… assertion=[74, 164] | member([3]); EXACT; literal_membership_not_exhaustive_set | ACTIVE; literal_own_assertion | b.same_compartment: EXACT_BINDING | b.same_compartment: AUTO_VETO; b.same_compartment: REVIEW_ONLY [central_veto_applied,checker_not_verified,insufficient,membership_is_not_positive_set,no_checker_receipt,no_positive_checker_fact] | p3-membership-guard:2ce93056d869b64680495295: DETERMINISTIC_FAILED; suff=False; structural:2f707075538a03303d9847a75e7a83c247fce6b91dd3a530b7c07c53fdae3388: STRUCTURAL_INCOMPATIBILITY_VERIFIED; suff=False | b.same_compartment → b.same_compartment,b.second_white_probability (DETERMINISTIC_FAILED); b.same_compartment → b.same_compartment,b.second_white_probability (STRUCTURAL_INCOMPATIBILITY_VERIFIED); parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_a06 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_a06.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_a06.audit.json.gz)

```text
c) No cenário em que a primeira branca veio do compartimento 1, aposto na preta para a segunda retirada. Nesse cenário, conto 3 saídas pretas entre as seis.
```

contagem “Nesse cenário…” UNSUPPORTED/AMBIGUOUS; cor sozinha não completa estratégia.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nesse cenário, conto 3 saídas pretas entre as seis. [[105, 156]] | segment:b37ea1e61f6938f3… assertion=[105, 156] | 3 saídas pretas entre as 6; UNSUPPORTED; unsupported_checker_payload | AMBIGUOUS; adoption_not_source_validated | c.strategy_case_1: PARTIAL_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,discourse_ambiguous,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| No cenário em que a primeira branca veio do compartimento 1, aposto na preta para a segunda retirada. [[3, 104]] | segment:1d143df05e1e0f35… assertion=[3, 104] | black; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_1: EXACT_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_b02 — 2 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b02.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b02.audit.json.gz)

```text
a) Minha chance de branca na primeira retirada era 1/2. Refaço a conta e substituo essa chance por primeira_branca: 2/6=1/3.
```

1/2 está SUPERSEDED. A igualdade escrita2/6=1/3 está ACTIVE/EXACT, foi compilada/provada por Lean e recebe a.probability=2. Nenhum veto herdado da estimativa retirada.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minha chance de branca na primeira retirada era 1/2. [[3, 55]] | segment:90be764e607507e9… assertion=[3, 55] | 1/2; EXACT; source_checked_payload | SUPERSEDED; validated_local_replacement | a.first_white_probability: EXACT_BINDING | a.first_white_probability: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: a.probability=2 |
| Refaço a conta e substituo essa chance por primeira_branca: 2/6=1/3. [[56, 124]] | segment:804c94686afc8a13… assertion=[56, 124] | 2/6=1/3; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | a.first_white_probability: EXACT_BINDING | a.first_white_probability: AUTO_AWARD; a.first_white_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:0fb48555172862415715: FORMAL_VERIFIED; suff=True; tme2-p3-check.v1:b897d4c0fedf251cc9cd: FORMAL_NOT_ATTEMPTED; suff=False | sem hard veto; parcelas da obrigação no caso: a.probability=2 |

Parcelas finais do caso: a.probability=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_b04 — 1 / 1

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b04.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b04.audit.json.gz)

```text
c) A indicação para continuar era o conjunto {1,4}. Retifico os compartimentos de continuação: continuar: {1,2}. Esta é a indicação definitiva.
```

{1,4} está SUPERSEDED; {1,2} ACTIVE/EXACT é verificado deterministicamente e recebe c.continue=1. Nenhum veto da primeira lista.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A indicação para continuar era o conjunto {1,4}. [[3, 51]] | segment:fe2b3c529ce0b204… assertion=[3, 51] | {1,4}; EXACT; source_checked_payload | SUPERSEDED; validated_local_replacement | c.continue_compartments: EXACT_BINDING | c.continue_compartments: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: c.continue=1 |
| Retifico os compartimentos de continuação: continuar: {1,2}. Esta é a indicação definitiva. [[52, 143]] | segment:d558532931909fdf… assertion=[52, 143] | {1,2}; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.continue_compartments: EXACT_BINDING | c.continue_compartments: AUTO_AWARD; c.continue_compartments: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:491638ca54ab57336dcc: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:506ff643539bc16f8705: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.continue=1 |

Parcelas finais do caso: c.continue=1. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_b05 — 2 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b05.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b05.audit.json.gz)

```text
b) A probabilidade da segunda branca ficou anotada como 7/36. Depois de conferir a partição, invalido esse valor e assino o resultado da segunda branca: 11/36.
```

7/36 está SUPERSEDED e sua representação antiga é AMBIGUOUS; não ganha autoridade negativa.11/36 está ACTIVE/EXACT e passa a rota result_value do composto, recebendo b.conclusion=2. “Conferir a partição” não recebe crédito de método nem substitui relação escrita.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A probabilidade da segunda branca ficou anotada como 7/36. Depois de conferir a partição, invalido esse valor e assino o resultado da segunda branca: 11/36. [[3, 159]] | segment:7eb43d9e541bf0c6… assertion=[3, 112] | 7/36; AMBIGUOUS; subject_not_uniquely_bound_to_source_clause | SUPERSEDED; validated_local_replacement | b.second_white_probability: AMBIGUOUS_BINDING | b.second_white_probability: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: b.conclusion=2 |
| Depois de conferir a partição, invalido esse valor e assino o resultado da segunda branca: 11/36. [[62, 159]] | segment:b015002518371d0f… assertion=[115, 159] | 11/36; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | b.second_white_probability: EXACT_BINDING | b.second_white_probability: AUTO_AWARD; b.second_white_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:2c0a0129ef364c32d398: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:7b9e8cbe7a7dc2017320: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: b.conclusion=2 |

Parcelas finais do caso: b.conclusion=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_b06 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b06.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b06.audit.json.gz)

```text
c) Para a branca inicial do compartimento 1, minha aposta era cinza. Troco a aposta desse caso 1: estrategia_1: preta. No mesmo estado conto contagem_1: 3.
```

contagem_1 não vinculada à cor; antigo cinza ainda ACTIVE, porém sem refutação/hard veto; composto incompleto.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| No mesmo estado conto contagem_1: 3. [[119, 155]] | segment:c620ea4ec80e3941… assertion=[119, 155] | 3; UNSUPPORTED; color_count_not_bound_to_written_quantity | ACTIVE; literal_own_assertion | c.strategy_case_1: PARTIAL_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Troco a aposta desse caso 1: estrategia_1: preta. [[69, 118]] | segment:0b8ff699a80ca742… assertion=[69, 118] | black; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_1: EXACT_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Para a branca inicial do compartimento 1, minha aposta era cinza. [[3, 68]] | segment:fde72e47131261e9… assertion=[3, 68] | gray; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_1: EXACT_BINDING | c.strategy_case_1: REVIEW_ONLY [checker_not_verified,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_b08 — 2 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b08.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b08.audit.json.gz)

```text
a) Eu havia dito quatro brancas na base. Volto a essa contagem e retiro o quatro: minha resposta para as bolas brancas inferiores é duas.
```

quatro está SUPERSEDED; “duas” é normalização suportada para2 na quantidade escrita. Checker determinístico recebe a.count=2; a correção não usa a verdade matemática para reclassificar o discurso.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Volto a essa contagem e retiro o quatro: minha resposta para as bolas brancas inferiores é duas. [[41, 137]] | segment:ee79159e1536bf82… assertion=[82, 137] | 2; SUPPORTED_NORMALIZATION; source_checked_payload | ACTIVE; literal_own_assertion | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: AUTO_AWARD; a.bottom_white_count: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:67b7db801908f67abbba: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:b55e19949c03fa8bd06f: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: a.count=2 |
| Eu havia dito quatro brancas na base. [[3, 40]] | segment:1c16c9df5d04eaf3… assertion=[3, 40] | 4; SUPPORTED_NORMALIZATION; source_checked_payload | SUPERSEDED; validated_local_replacement | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: a.count=2 |

Parcelas finais do caso: a.count=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_c01 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_c01.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_c01.audit.json.gz)

```text
a) Exploro uma hipótese que não assumo na resposta: a chance de primeira branca seria 3/4. Fora dessa hipótese, afirmo que a base contém 2 bolas brancas.
```

a própria afirmação “Fora dessa hipótese…” foi NON_ADOPTED indevidamente; rejeição de contexto, sem hard veto.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Exploro uma hipótese que não assumo na resposta: a chance de primeira branca seria 3/4. [[3, 90]] | segment:83e3af79c5af7bea… assertion=[3, 90] | 3/4; UNSUPPORTED; negated_proposition_requires_explicit_representation | NON_ADOPTED; written_unadopted_scope | a.first_white_probability: PARTIAL_BINDING | a.first_white_probability: REVIEW_ONLY [checker_not_verified,discourse_non_adopted,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Fora dessa hipótese, afirmo que a base contém 2 bolas brancas. [[91, 153]] | segment:9fdc7f1047456ebb… assertion=[91, 153] | 2; EXACT; source_checked_payload | NON_ADOPTED; written_unadopted_scope | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: REVIEW_ONLY [checker_not_verified,discourse_non_adopted,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_c03 — 0 / 1

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_c03.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_c03.audit.json.gz)

```text
c) Copio apenas um dado da figura do enunciado, não uma etapa da minha solução: a primeira bola de baixo do compartimento 1 é branca. Minha decisão para quando o jogo continua é continuar: {1,2}.
```

output histórico indisponível; fallback sem witness.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

Sem ledger semântico utilizável: raw_output histórico indisponível; a cadeia encerra no fallback nativo sem witness. Não inventar segmento ou claim para cobrir a ausência.

### p3_s03_c06 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_c06.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_c06.audit.json.gz)

```text
a) O erro que estou explicando é escrever inferiores_brancas: 6, pois isso trataria todas as cores como brancas. Não assumo essa contagem. Minha contagem efetiva é inferiores_brancas: 2.
```

falso veto + representação positiva insuficiente; seção7.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| O erro que estou explicando é escrever inferiores_brancas: 6, pois isso trataria todas as cores como brancas. [[3, 112]] | segment:5600c6a10112c3dd… assertion=[42, 63] | 6; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: AUTO_VETO; a.bottom_white_count: REVIEW_ONLY [central_veto_applied,checker_not_verified,insufficient] | tme2-p3-check.v1:31f3060585277a4d5815: DETERMINISTIC_FAILED; suff=False; tme2-p3-check.v1:44950c6947d866007833: DETERMINISTIC_FAILED; suff=False | a.bottom_white_count → a.bottom_white_count (DETERMINISTIC_FAILED); parcelas da obrigação no caso: nenhuma |
| Minha contagem efetiva é inferiores_brancas: 2. [[139, 186]] | segment:838e496a024fb00b… assertion=[139, 186] | 2; UNSUPPORTED; white_count_not_bound_to_written_quantity | ACTIVE; literal_own_assertion | a.bottom_white_count: PARTIAL_BINDING | a.bottom_white_count: REVIEW_ONLY [central_veto_applied,checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_d06 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_d06.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_d06.audit.json.gz)

```text
a) A linha da primeira probabilidade foi cortada: «primeira_branca: 1/». Não completei o denominador. Em outra linha completa deixo inferiores_brancas: 2.
```

output histórico indisponível; fallback sem witness.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

Sem ledger semântico utilizável: raw_output histórico indisponível; a cadeia encerra no fallback nativo sem witness. Não inventar segmento ou claim para cobrir a ausência.

### p3_s03_d08 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_d08.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_d08.audit.json.gz)

```text
c) Para continuar tenho duas opções ainda abertas, continuar: {1,2} ou continuar: {2,6}; não assinalei nenhuma. Independentemente dessa escolha, depois da branca do compartimento 2 minha aposta é cinza e conto 3 saídas cinzas nesse estado.
```

contagem de cinzas não vinculada; estratégia incompleta; nenhuma propagação negativa das alternativas abertas.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Para continuar tenho duas opções ainda abertas, continuar: {1,2} ou continuar: {2,6}; não assinalei nenhuma. [[3, 111]] | segment:01354ea5b9ef7bb3… assertion=[71, 87] | {2,6}; UNSUPPORTED; negated_proposition_requires_explicit_representation | ACTIVE; literal_own_assertion | c.continue_compartments: PARTIAL_BINDING | c.continue_compartments: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Para continuar tenho duas opções ainda abertas, continuar: {1,2} ou continuar: {2,6}; não assinalei nenhuma. [[3, 111]] | segment:618391249ebf23d8… assertion=[89, 110] | não assinalei nenhuma; UNSUPPORTED; negated_proposition_requires_explicit_representation | AMBIGUOUS; adoption_not_source_validated | c.continue_compartments: PARTIAL_BINDING | c.continue_compartments: REVIEW_ONLY [checker_not_verified,discourse_ambiguous,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Para continuar tenho duas opções ainda abertas, continuar: {1,2} ou continuar: {2,6}; não assinalei nenhuma. [[3, 111]] | segment:fd1e0dda666aadbd… assertion=[51, 67] | {1,2}; UNSUPPORTED; negated_proposition_requires_explicit_representation | ACTIVE; literal_own_assertion | c.continue_compartments: PARTIAL_BINDING | c.continue_compartments: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Independentemente dessa escolha, depois da branca do compartimento 2 minha aposta é cinza e conto 3 saídas cinzas nesse estado. [[112, 239]] | segment:e4bbe527a01221f3… assertion=[112, 201] | cinza; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_2: EXACT_BINDING | c.strategy_case_2: REVIEW_ONLY [checker_not_verified,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Independentemente dessa escolha, depois da branca do compartimento 2 minha aposta é cinza e conto 3 saídas cinzas nesse estado. [[112, 239]] | segment:4a1910fff79b74ea… assertion=[204, 238] | 3; UNSUPPORTED; color_count_not_bound_to_written_quantity | ACTIVE; literal_own_assertion | c.strategy_case_2: PARTIAL_BINDING | c.strategy_case_2: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_e01 — 4 / 4

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_e01.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_e01.audit.json.gz)

```text
a) A nota de uma colega dizia primeira_branca: 7/12; transcrevo sem concordar. Na minha resolução, primeira_branca: 1/3 e inferiores_brancas: 2.
```

7/12 de colega está NON_ADOPTED.1/3 e2 próprios permanecem ACTIVE, exact e ligados a obrigações distintas: a.probability=2 e a.count=2. A correção do falso veto recupera2; a contagem independente recupera outros2. São4 pontos, não4 pontos atribuíveis ao veto anterior.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A nota de uma colega dizia primeira_branca: 7/12; transcrevo sem concordar. [[3, 78]] | segment:bbdb7b41b460a41f… assertion=[30, 51] | 7/12; EXACT; source_checked_payload | NON_ADOPTED; written_third_party_without_adoption | a.first_white_probability: EXACT_BINDING | a.first_white_probability: REVIEW_ONLY [checker_not_verified,discourse_non_adopted,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: a.probability=2 |
| Na minha resolução, primeira_branca: 1/3 e inferiores_brancas: 2. [[79, 144]] | segment:0ccd357464a46934… assertion=[99, 119] | 1/3; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | a.first_white_probability: EXACT_BINDING | a.first_white_probability: AUTO_AWARD; a.first_white_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:884c1c7e0a4307d42eff: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:cc387af7361a08f0765d: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: a.probability=2 |
| Na minha resolução, primeira_branca: 1/3 e inferiores_brancas: 2. [[79, 144]] | segment:683aa4c8995cf8b6… assertion=[122, 143] | 2; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: AUTO_AWARD; a.bottom_white_count: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:7a68352c66e0d8a0bb6d: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:ebf97e9561a7579ad574: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: a.count=2 |

Parcelas finais do caso: a.count=2, a.probability=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_e03 — 2 / 4

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_e03.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_e03.audit.json.gz)

```text
a) Inicialmente contei inferiores_brancas: 3. Retiro essa contagem inicial e passo a adotar inferiores_brancas: 2. Além disso, minha probabilidade da primeira branca é 1/3.
```

contagem revisada2 continua UNSUPPORTED; probabilidade independente1/3 preserva2p.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Inicialmente contei inferiores_brancas: 3. [[3, 45]] | segment:d98824085a22fdd8… assertion=[3, 45] | 3; UNSUPPORTED; white_count_not_bound_to_written_quantity | SUPERSEDED; validated_local_replacement | a.bottom_white_count: PARTIAL_BINDING | a.bottom_white_count: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Além disso, minha probabilidade da primeira branca é 1/3. [[115, 172]] | segment:4d2081bd53014d16… assertion=[127, 172] | 1/3; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | a.first_white_probability: EXACT_BINDING | a.first_white_probability: AUTO_AWARD; a.first_white_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:2e3b86ce66e0577cf0db: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:9afe14717fa62f47e8cc: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: a.probability=2 |
| Retiro essa contagem inicial e passo a adotar inferiores_brancas: 2. [[46, 114]] | segment:e338e3910e9b6ed9… assertion=[46, 114] | 2; UNSUPPORTED; white_count_not_bound_to_written_quantity | ACTIVE; literal_own_assertion | a.bottom_white_count: PARTIAL_BINDING | a.bottom_white_count: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: a.probability=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_e05 — 0 / 2

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_e05.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_e05.audit.json.gz)

```text
a) Cito sem adotar a fala de Célia: «inferiores_brancas: 6». Quanto à minha própria resposta, registrei inferiores_brancas: 1; corrijo minha própria contagem para inferiores_brancas: 2.
```

falso veto material; seção7.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Cito sem adotar a fala de Célia: «inferiores_brancas: 6». [[3, 60]] | segment:8a36beaf96d41afc… assertion=[37, 58] | 6; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: AUTO_VETO; a.bottom_white_count: REVIEW_ONLY [central_veto_applied,checker_not_verified,insufficient] | tme2-p3-check.v1:78153ec95b8f09bb273c: DETERMINISTIC_FAILED; suff=False; tme2-p3-check.v1:8e44ff67640ed9017df4: DETERMINISTIC_FAILED; suff=False | a.bottom_white_count → a.bottom_white_count (DETERMINISTIC_FAILED); parcelas da obrigação no caso: nenhuma |
| Quanto à minha própria resposta, registrei inferiores_brancas: 1; corrijo minha própria contagem para inferiores_brancas: 2. [[61, 185]] | segment:7df20a2b1c066921… assertion=[163, 184] | 2; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: REVIEW_ONLY [central_veto_applied]; a.bottom_white_count: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:07c7560a240149c35af7: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:3ee825486d7bf9605630: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Quanto à minha própria resposta, registrei inferiores_brancas: 1; corrijo minha própria contagem para inferiores_brancas: 2. [[61, 185]] | segment:ea6a27daa99d1cb6… assertion=[104, 125] | 1; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | a.bottom_white_count: EXACT_BINDING | a.bottom_white_count: AUTO_VETO; a.bottom_white_count: REVIEW_ONLY [central_veto_applied,checker_not_verified,insufficient] | tme2-p3-check.v1:8e56aec570cf352e78bd: DETERMINISTIC_FAILED; suff=False; tme2-p3-check.v1:f9db5ca075dcb3f7a754: DETERMINISTIC_FAILED; suff=False | a.bottom_white_count → a.bottom_white_count (DETERMINISTIC_FAILED); parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: nenhuma. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

### p3_s03_e08 — 3 / 8

[Trace integral](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/run/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_e08.json.gz) · [Auditoria por claim](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_frozen_regression_01/analysis/cases/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_e08.audit.json.gz)

```text
c) Minha antiga aposta após branca do compartimento 2 era preta; retiro essa escolha e a substituo por estrategia_2: cinza. Para essa escolha revisada, contagem_2: 3.
No caso da branca do compartimento 1, estrategia_1: preta e contagem_1: 3.
O jogo prossegue com continuar: {1,2}.
Para as apostas finais, condicional_1: 3/6=1/2 e condicional_2: 3/6=1/2.
Pondero os dois caminhos no total: (1/6)*(1/2)+(1/6)*(1/2)=1/6.
```

contagem_2 após correção não vinculada à cor; perde estratégia2, conditional2,total; continuam1+2p de continue e estratégia1.

| Source span/range | Segment | Representação/fidelity | Discourse | Binding | Automation | Checker/sufficiency | Reconciliação/award |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minha antiga aposta após branca do compartimento 2 era preta; retiro essa escolha e a substituo por estrategia_2: cinza. [[3, 123]] | segment:e628bf012d304b5f… assertion=[87, 122] | cinza; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_2: EXACT_BINDING | c.strategy_case_2: REVIEW_ONLY [checker_not_verified,insufficient,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Minha antiga aposta após branca do compartimento 2 era preta; retiro essa escolha e a substituo por estrategia_2: cinza. [[3, 123]] | segment:7cdf5f7e47af242c… assertion=[3, 84] | preta; AMBIGUOUS; subject_not_uniquely_bound_to_source_clause | SUPERSEDED; validated_local_replacement | c.strategy_case_2: AMBIGUOUS_BINDING | c.strategy_case_2: REVIEW_ONLY [checker_not_verified,discourse_superseded,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Para essa escolha revisada, contagem_2: 3. [[124, 166]] | segment:6269c838cca95f6e… assertion=[124, 166] | 3; UNSUPPORTED; color_count_not_bound_to_written_quantity | ACTIVE; literal_own_assertion | c.strategy_case_2: PARTIAL_BINDING | c.strategy_case_2: REVIEW_ONLY [checker_not_verified,insufficient,insufficient_fidelity,invalid_or_ambiguous_binding,no_checker_receipt,no_positive_checker_fact] | nenhum checker matemático admitido | sem hard veto; parcelas da obrigação no caso: nenhuma |
| No caso da branca do compartimento 1, estrategia_1: preta e contagem_1: 3. [[167, 241]] | segment:2dd23b03bef45bd2… assertion=[227, 240] | 3; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_1: EXACT_BINDING | c.conditional_success_1: AUTO_AWARD; c.conditional_success_1: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.strategy_case_1: AUTO_AWARD; c.strategy_case_1: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:04028f46efaa51854cd2: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:677bb6fb324f7835fd99: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:91e8cfa4bb8708aaafd5: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:c1a4faef8b5ae197396a: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.first_strategy=2 |
| No caso da branca do compartimento 1, estrategia_1: preta e contagem_1: 3. [[167, 241]] | segment:353493d7ed2f1b29… assertion=[205, 224] | preta; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.strategy_case_1: EXACT_BINDING | c.conditional_success_1: AUTO_AWARD; c.conditional_success_1: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.strategy_case_1: AUTO_AWARD; c.strategy_case_1: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:04028f46efaa51854cd2: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:677bb6fb324f7835fd99: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:91e8cfa4bb8708aaafd5: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:c1a4faef8b5ae197396a: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.first_strategy=2 |
| O jogo prossegue com continuar: {1,2}. [[242, 280]] | segment:ca58e05cc1a48e8d… assertion=[242, 280] | {1,2}; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.continue_compartments: EXACT_BINDING | c.continue_compartments: AUTO_AWARD; c.continue_compartments: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:047d1f84f10338083301: DETERMINISTIC_VERIFIED; suff=True; tme2-p3-check.v1:6e448fac933a2c0fca84: DETERMINISTIC_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: c.continue=1 |
| Para as apostas finais, condicional_1: 3/6=1/2 e condicional_2: 3/6=1/2. [[281, 353]] | segment:0adac93967b520d5… assertion=[330, 352] | 3/6=1/2; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.conditional_success_2: EXACT_BINDING | c.conditional_success_2: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.conditional_success_2: REVIEW_ONLY [checker_not_verified,insufficient] | tme2-p3-check.v1:9e143758003abb16e7f1: COMPOSITE_INCOMPLETE; suff=False; tme2-p3-check.v1:ddef49981d81bfbf397c: COMPOSITE_INCOMPLETE; suff=False | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Para as apostas finais, condicional_1: 3/6=1/2 e condicional_2: 3/6=1/2. [[281, 353]] | segment:6ba348b028c8569f… assertion=[305, 327] | 3/6=1/2; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.conditional_success_1: EXACT_BINDING | c.conditional_success_1: AUTO_AWARD; c.conditional_success_1: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation] | tme2-p3-check.v1:04028f46efaa51854cd2: COMPOSITE_VERIFIED; suff=True; tme2-p3-check.v1:91e8cfa4bb8708aaafd5: COMPOSITE_VERIFIED; suff=True | sem hard veto; parcelas da obrigação no caso: nenhuma |
| Pondero os dois caminhos no total: (1/6)*(1/2)+(1/6)*(1/2)=1/6. [[354, 417]] | segment:4fb12f25f6b4775f… assertion=[354, 417] | (1/6)*(1/2)+(1/6)*(1/2)=1/6; EXACT; source_checked_payload | ACTIVE; literal_own_assertion | c.total_win_probability: EXACT_BINDING | c.total_win_probability: REVIEW_ONLY [central_veto_not_authorized,checker_not_refutation]; c.total_win_probability: REVIEW_ONLY [checker_not_verified,insufficient] | tme2-p3-check.v1:150d17efba9d8af1b094: COMPOSITE_INCOMPLETE; suff=False; tme2-p3-check.v1:b7f22ade1aca88b2815c: COMPOSITE_INCOMPLETE; suff=False | sem hard veto; parcelas da obrigação no caso: nenhuma |

Parcelas finais do caso: c.continue=1, c.first_strategy=2. As parcelas indicadas por obrigação na tabela não significam que todos os aliases dessa obrigação produziram o witness; a seleção exata está no decision_receipt.

## Apêndice B — todos os scores, por registro

### DEV01

| Case_id | Semantic histórico | Replay atual | Expectation literal | Contrato autorizado | Fallback | Missed pts | Falso veto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| p3_dev_complete_strategy | 8 | 8 | 8 | 8 | não | 0 | — |
| p3_dev_favorable_partition | 8 | 8 | 8 | 8 | não | 0 | — |
| p3_dev_hypothesis_context | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_dev_initial_count | 4 | 4 | 4 | 4 | não | 0 | — |
| p3_dev_isolated_answer | 2 | 2 | 2 | 2 | sim | 0 | — |
| p3_dev_partial_conflict | 4 | 2 | 2 | 2 | não | 0 | — |
| p3_dev_probability_error | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_dev_sample_space | 2 | 2 | 2 | 2 | não | 0 | — |

### DEV02

| Case_id | Semantic histórico | Replay atual | Expectation literal | Contrato autorizado | Fallback | Missed pts | Falso veto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| p3_dev_complete_strategy | 8 | 8 | 8 | 8 | não | 0 | — |
| p3_dev_favorable_partition | 8 | 8 | 8 | 8 | não | 0 | — |
| p3_dev_hypothesis_context | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_dev_initial_count | 4 | 4 | 4 | 4 | não | 0 | — |
| p3_dev_isolated_answer | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_dev_partial_conflict | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_dev_probability_error | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_dev_sample_space | 2 | 2 | 2 | 2 | não | 0 | — |

### Robustness01

| Case_id | Semantic histórico | Replay atual | Expectation literal | Contrato autorizado | Fallback | Missed pts | Falso veto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| p3_rob_a01 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_rob_a02 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_rob_a03 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_a04 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_a05 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_a06 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_rob_a07 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_rob_a08 | 8 | 8 | 8 | 8 | não | 0 | — |
| p3_rob_b01 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b02 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b03 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b04 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b05 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b06 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b07 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b08 | 8 | 8 | 8 | 8 | não | 0 | — |
| p3_rob_c01 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_c02 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_c03 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_c04 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_c05 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_c06 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_c07 | 5 | 5 | 5 | 5 | não | 0 | — |
| p3_rob_c08 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d01 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d02 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d03 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_d04 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d05 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d06 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d07 | 4 | 4 | 4 | 4 | não | 0 | — |
| p3_rob_d08 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_e01 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_e02 | 4 | 4 | 2 | 4 | não | 0 | — |
| p3_rob_e03 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_e04 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_e05 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_e06 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_e07 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_e08 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_f01 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f02 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f03 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f04 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f05 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f06 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f07 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f08 | 0 | 0 | 0 | 0 | sim | 0 | — |

### Safety02/new32

| Case_id | Semantic histórico | Replay atual | Expectation literal | Contrato autorizado | Fallback | Missed pts | Falso veto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| p3_safe_s1_01 | 4 | 4 | 4 | 4 | não | 0 | — |
| p3_safe_s1_02 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s1_03 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s1_04 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s1_05 | 0 | 0 | 2 | 2 | não | 2 | b.second_white_probability |
| p3_safe_s1_06 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s1_07 | 0 | 1 | 1 | 1 | não | 0 | — |
| p3_safe_s1_08 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s2_01 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s2_02 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s2_03 | 1 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s2_04 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s2_05 | 0 | 0 | 0 | 0 | sim | 0 | — |
| p3_safe_s2_06 | 4 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s2_07 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s2_08 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s3_01 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s3_02 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s3_03 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s3_04 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s3_05 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s3_06 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s3_07 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_safe_s3_08 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s4_01 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s4_02 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s4_03 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s4_04 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s4_05 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s4_06 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_safe_s4_07 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_safe_s4_08 | 0 | 0 | 0 | 0 | não | 0 | — |

### Safety02/observed48

| Case_id | Semantic histórico | Replay atual | Expectation literal | Contrato autorizado | Fallback | Missed pts | Falso veto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| p3_rob_a01 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_rob_a02 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_rob_a03 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_a04 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_a05 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_a06 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_rob_a07 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_rob_a08 | 6 | 8 | 8 | 8 | não | 0 | — |
| p3_rob_b01 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b02 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b03 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b04 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b05 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b06 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b07 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_b08 | 8 | 8 | 8 | 8 | não | 0 | — |
| p3_rob_c01 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_c02 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_c03 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_c04 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_c05 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_c06 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_c07 | 5 | 5 | 5 | 5 | não | 0 | — |
| p3_rob_c08 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d01 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d02 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d03 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_d04 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d05 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d06 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_d07 | 4 | 4 | 4 | 4 | não | 0 | — |
| p3_rob_d08 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_e01 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_e02 | 2 | 4 | 2 | 4 | não | 0 | — |
| p3_rob_e03 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_e04 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_e05 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_e06 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_e07 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_e08 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_rob_f01 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f02 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f03 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f04 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f05 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f06 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f07 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_rob_f08 | 0 | 0 | 0 | 0 | não | 0 | — |

### Safety03

| Case_id | Semantic histórico | Replay atual | Expectation literal | Contrato autorizado | Fallback | Missed pts | Falso veto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| p3_s03_a01 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_a02 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_s03_a03 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_s03_a04 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_a05 | 2 | 0 | 0 | 0 | não | 0 | — |
| p3_s03_a06 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_s03_a07 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_s03_a08 | 4 | 4 | 4 | 4 | não | 0 | — |
| p3_s03_b01 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_b02 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_b03 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_b04 | 0 | 1 | 1 | 1 | não | 0 | — |
| p3_s03_b05 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_b06 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_s03_b07 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_b08 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_c01 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_s03_c02 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_c03 | 0 | 0 | 1 | 1 | sim | 1 | — |
| p3_s03_c04 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_c05 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_c06 | 0 | 0 | 2 | 2 | não | 2 | a.bottom_white_count |
| p3_s03_c07 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_c08 | 1 | 1 | 1 | 1 | não | 0 | — |
| p3_s03_d01 | 0 | 0 | 0 | 0 | sim | 0 | — |
| p3_s03_d02 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_d03 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_s03_d04 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_s03_d05 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_s03_d06 | 0 | 0 | 2 | 2 | sim | 2 | — |
| p3_s03_d07 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_s03_d08 | 0 | 0 | 2 | 2 | não | 2 | — |
| p3_s03_e01 | 0 | 4 | 4 | 4 | não | 0 | — |
| p3_s03_e02 | 0 | 0 | 0 | 0 | não | 0 | — |
| p3_s03_e03 | 2 | 2 | 4 | 4 | não | 2 | — |
| p3_s03_e04 | 0 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_e05 | 0 | 0 | 2 | 2 | não | 2 | a.bottom_white_count |
| p3_s03_e06 | 4 | 4 | 4 | 4 | não | 0 | — |
| p3_s03_e07 | 2 | 2 | 2 | 2 | não | 0 | — |
| p3_s03_e08 | 1 | 3 | 8 | 8 | não | 5 | — |

A comparação com o replay salvo durante a implementação é distinta da coluna histórico acima: **184/184 scores e conjuntos de obrigações elegíveis idênticos**. Não se usou essa igualdade como substituto da auditoria causal.
