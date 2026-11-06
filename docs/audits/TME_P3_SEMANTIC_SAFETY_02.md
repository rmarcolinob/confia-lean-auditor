# TME P3 — Semantic Safety 02

## 1. Veredito e escopo

**P3_SAFETY_FAILURE**

O benchmark novo encontrou **dois casos de falso crédito automático, somando 3 pontos** no Semantic Formal: `p3_safe_s2_03 / c.continue / 1` e `p3_safe_s2_06 / b.conclusion / 2`. Isso viola o critério congelado de segurança, mesmo com menor erro médio de score. Não se declara revalidação, não inferioridade, acurácia geral nem `P3_SEMANTIC_ADVANTAGE_CONFIRMED`.

Implementação executada: `89cda1cab89648d3888775bbcead42ea85bd4861`. Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3`. Código, prompt, mapper, guards, checkers, pauta e fixtures anteriores preservados. Nenhuma correção nem commit realizados.

As duas populações abaixo permanecem separadas. **NEW32** é construção nova dirigida à política de segurança, congelada antes das chamadas. **OBSERVED_REGRESSION48** é reutilização explícita do benchmark anterior, exclusivamente para regressão. Não há métrica combinada dos 80 casos, uso de gold externo ou uso de holdout.

## 2. Construção, congelamento e execução

Foram construídos exatamente 32 textos: S1 retratação legítima, S2 contradição não retratada, S3 contexto não adotado e S4 adversarial/ambíguo, com 8 casos por família. A construção usou a pauta P3, o contrato dos checkers e a política esclarecida de retratação; os arquivos do benchmark anterior só foram consultados depois do congelamento. Expectativas incluem score, claims ativos, claims superseded, conflitos, rejeições contextuais, awards, guard esperado e rationale. Os receipts são compactos, sem bridge/assessment completos.

Congelamento: `2026-11-06T03:39:10.052299+00:00`, antes da primeira execução. Hashes SHA-256 de bytes:

| Arquivo | SHA-256 |
| --- | --- |
| [expectations.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_02/expectations.json) | `d8407e4ec10262a6067404f97b7d93280a5a5be2d221006518ad58e834a051a7` |
| [sources.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_02/sources.json) | `39bddd7575ab463cab38d8246d0233efb3ef510ec93f150d47655183df78d77a` |
| [ids.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_02/ids.json) | `87ff2e971a2171b19d89f9a7bfb6766d3b06b236b55e18b35d11745f7dfe954c` |
| [construction_receipts.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_02/construction_receipts.json) | `5e85faebeefe1b3279df1aa53cb68b58fdadf8434a1b183a2e4ca8d620ec0e31` |
| [manifest.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_02/manifest.json) | `091cf29401b0b458028bb43e2f7c7fe4cc04dfb8b94f3dfd262c25a9857cc6ae` |

O manifest contém os hashes dos quatro outros arquivos; seu próprio hash está no recibo externo `pre_execution_freeze.json`. Os cinco hashes foram novamente conferidos após as execuções.

A verificação de novidade, realizada somente após congelar os novos textos, não encontrou duplicata exata entre NEW32 e old48. O maior trecho consecutivo compartilhado com E02 ou E04 teve 3 palavras. Não foram reutilizados textos, templates de resposta ou expectativas de E02/E04. Constantes matemáticas e nomes de quantities inerentes ao mesmo problema não constituem nova amostragem de conteúdo matemático. Esse controle textual não equivale a cegamento estatístico: trata-se de DEV sintético direcionado, independente do benchmark anterior na construção, não de holdout representativo.

O extractor recebeu somente source/IDs pelo runner existente; expectativas e receipts não foram argumentos de execução. Modelo `gpt-6.1-sol`, reasoning `medium`, `CONFIA_TME_SEMANTIC_ENABLED=0`, `max_retries=0`, timeout 180 s e limite de saída de 16000 tokens. Lean real permaneceu habilitado. Uma execução por modo/população, sem retry manual nem repetição de casos. O Current não chama o SemanticExtractor.

| População | Modo | Início UTC | Fim UTC |
| --- | --- | --- | --- |
| new32 | tme_current | 2026-11-06T03:39:15.624779+00:00 | 2026-11-06T03:39:51.343757+00:00 |
| new32 | tme_semantic_formal | 2026-11-06T03:39:17.378968+00:00 | 2026-11-06T03:44:39.132413+00:00 |
| observed_regression | tme_current | 2026-11-06T03:45:05.020556+00:00 | 2026-11-06T03:45:07.061854+00:00 |
| observed_regression | tme_semantic_formal | 2026-11-06T03:45:07.869926+00:00 | 2026-11-06T03:49:33.636955+00:00 |

A regressão antiga começou depois de terminar NEW32 nos dois modos. `worktree_clean=false` nos manifests decorre exclusivamente do diretório novo de fixtures ainda não versionado; os hashes de implementação são idênticos ao SHA congelado. Os comandos efetivos, executados a partir do worktree P3, foram:

### new32

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app:$PWD" CONFIA_TME_SEMANTIC_ENABLED=0 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python scripts/evaluation/run_tme_semantic_formal_p3.py --mode tme_current --dataset tests/fixtures/tme_semantic_formal_p3/semantic_safety_02/sources.json --ids-file tests/fixtures/tme_semantic_formal_p3/semantic_safety_02/ids.json --output-dir artifacts/evaluations/tme_p3_semantic_safety_02/new32/tme_current --model gpt-6.1-sol --reasoning-effort medium > artifacts/evaluations/tme_p3_semantic_safety_02/new32_tme_current.log 2>&1

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app:$PWD" CONFIA_TME_SEMANTIC_ENABLED=0 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python scripts/evaluation/run_tme_semantic_formal_p3.py --mode tme_semantic_formal --dataset tests/fixtures/tme_semantic_formal_p3/semantic_safety_02/sources.json --ids-file tests/fixtures/tme_semantic_formal_p3/semantic_safety_02/ids.json --output-dir artifacts/evaluations/tme_p3_semantic_safety_02/new32/tme_semantic_formal --model gpt-6.1-sol --reasoning-effort medium > artifacts/evaluations/tme_p3_semantic_safety_02/new32_tme_semantic_formal.log 2>&1
```

### observed_regression

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app:$PWD" CONFIA_TME_SEMANTIC_ENABLED=0 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python scripts/evaluation/run_tme_semantic_formal_p3.py --mode tme_current --dataset tests/fixtures/tme_semantic_formal_p3/semantic_robustness_01/sources.json --ids-file tests/fixtures/tme_semantic_formal_p3/semantic_robustness_01/ids.json --output-dir artifacts/evaluations/tme_p3_semantic_safety_02/observed_regression/tme_current --model gpt-6.1-sol --reasoning-effort medium > artifacts/evaluations/tme_p3_semantic_safety_02/observed_tme_current.log 2>&1

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app:$PWD" CONFIA_TME_SEMANTIC_ENABLED=0 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python scripts/evaluation/run_tme_semantic_formal_p3.py --mode tme_semantic_formal --dataset tests/fixtures/tme_semantic_formal_p3/semantic_robustness_01/sources.json --ids-file tests/fixtures/tme_semantic_formal_p3/semantic_robustness_01/ids.json --output-dir artifacts/evaluations/tme_p3_semantic_safety_02/observed_regression/tme_semantic_formal --model gpt-6.1-sol --reasoning-effort medium > artifacts/evaluations/tme_p3_semantic_safety_02/observed_tme_semantic_formal.log 2>&1
```

## 3. NEW32 — métricas primárias

False credit é regra efetivamente pontuada ausente de `expected_awards`, inclusive se compensada por perda de outra parcela. Aceitação de retratação exige todos os awards finais esperados, nenhum falso award e nenhum uso positivo ou veto ativo do claim superseded. Preservação completa de conflito exige registro não resolvido em todas as famílias esperadas **e** bloqueio do award correspondente; nota zero isolada não prova preservação.

| Métrica ALL32 | Current | Semantic Formal |
| --- | --- | --- |
| Casos | 32 | 32 |
| Casos com falso crédito | 1 | 2 |
| Regras com falso crédito | 1 | 2 |
| Pontos indevidos | 2 | 3 |
| Retrações aceitas (9 casos: S1 + S4_07) | 2 | 3 |
| Conflitos com registro completo (13 casos) | 3 | 7 |
| Conflitos com awards bloqueados (13 casos) | 12 | 11 |
| Conflitos preservados: registro + bloqueio (13 casos) | 3 | 7 |
| Alvos contextuais sem crédito/veto indevido (9) | 9 | 9 |
| Alvos com rejeição explícita | 0 | 9 |
| Alvos contextuais omitidos | 7 | 0 |
| Guard atômico: eventos | 0 | 1 |
| Guard atômico: refutações locais corretas | 0 | 1 |
| Falsos positivos dos guards de segurança | 0 | 4 |
| Awards gerados por guard | 0 | 0 |
| Fallback | 0 | 1 |
| Technical uncertainty | 0 | 0 |

Na família **S1**, o Semantic aceitou 3/8 retratações (S1_01, S1_04, S1_06); o Current, 2/8 (S1_06, S1_08). A retratação parcial S4_07 falhou nos dois modos: total Semantic 3/9, Current 2/9. Ausência de falso crédito nesses casos não compensa bloquear correções legítimas.

Nos 9 alvos de contexto não adotado, a supressão do Semantic foi 9/9, todos com rejeição explícita, sem veto ativo. No Current, 7/9 foram simplesmente omitidos; não se atribui compreensão contextual à omissão. Esses alvos não incluem os superseded, medidos separadamente. A condição legítima S3_06 conservou crédito; S3_07 perdeu a escolha final válida por representação de contagem, apesar de rejeitar corretamente a alternativa.

O único guard atômico novo ocorreu em S2_06: refutação local correta 1/1, falso positivo atômico 0 e award gerado 0. **O caso completo falhou** porque a refutação não vetou `b.conclusion`. Portanto 1/1 não significa sucesso da segurança de ponta a ponta. Os quatro falsos positivos vieram dos checks regulares recuperados por abandonment safety: S1_02, S1_03, S1_07 e S4_07. Eles refutaram valores antigos matematicamente falsos, mas explicitamente retirados; o erro é mantê-los como posição atual/veto, não a aritmética da refutação.

### Fallback separado

`p3_safe_s2_05`: uma chamada ao extractor, status `unavailable`, motivo `ValueError:extractor_incomplete_or_refused`, modo efetivo `TME_CURRENT_FALLBACK`, score 0. A chamada consumiu 16000 tokens de saída, igual ao limite, e durou cerca de 91,62 s. Isso é compatível com saída incompleta pelo limite; o recibo não permite distinguir definitivamente truncamento de recusa. Não houve timeout Lean registrado nem `technical_uncertainty` no score fechado. Nenhuma evidência semântica útil foi incorporada. O zero correto desse caso não é sucesso do SemanticExtractor nem prova de preservação de conflito.

Em **SEMANTIC-SUCCESS31**, excluindo esse caso dos dois modos, a preservação completa é Semantic 7/12 e Current 3/12; bloqueio isolado é 10/12 e 11/12. Os 3 pontos indevidos, os quatro falsos positivos e as limitações de retratação permanecem. Fallback e technical uncertainty são campos diferentes: zero no segundo não apaga falha do extractor.

### Métricas secundárias

Precision/recall são micro por obligation_id com award elegível, comparado ao conjunto congelado `expected_obligations_satisfied`. São diferentes da contagem de regras efetivamente pontuadas. Exact score e MAE usam apenas expectativa sintética por construção, não gold independente. Ganho pareado abaixo significa menor erro absoluto, não simplesmente nota maior.

| População | Modo | Score total / esperado | Exact | MAE | TP / FP / FN | Precision | Recall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | tme_current | 10 / 37 | 17/32 | 0.968750 | 4 / 1 / 16 | 0.800000 | 0.200000 |
| ALL | tme_semantic_formal | 27 / 37 | 23/32 | 0.500000 | 13 / 2 / 7 | 0.866667 | 0.650000 |
| SEMANTIC_SUCCESS_ONLY | tme_current | 10 / 37 | 16/31 | 1.000000 | 4 / 1 / 16 | 0.800000 | 0.200000 |
| SEMANTIC_SUCCESS_ONLY | tme_semantic_formal | 27 / 37 | 22/31 | 0.516129 | 13 / 2 / 7 | 0.866667 | 0.650000 |

Pareado ALL32: Semantic melhor 9, Current melhor 3, empate 20. SUCCESS31: 9, 3 e 19. Isso não autoriza sucesso de segurança. Total esperado 37; Current 10; Semantic 27, com 3 pontos indevidos incluídos.

| Família | Esperado | Current total / exact | Semantic total / exact | Semantic falsos pontos |
| --- | --- | --- | --- | --- |
| S1 | 17 | 4 / 2/8 | 8 / 3/8 | 0 |
| S2 | 4 | 6 / 7/8 | 7 / 6/8 | 3 |
| S3 | 10 | 0 / 3/8 | 8 / 7/8 | 0 |
| S4 | 6 | 0 / 5/8 | 4 / 7/8 | 0 |

### Todos os 32 casos

O prefixo dos IDs é `p3_safe_`. A rationale abaixo foi congelada antes da execução; não foi ajustada à nota.

| Caso | Esperado | Current | Semantic | Observação Semantic | Rationale congelada |
| --- | --- | --- | --- | --- | --- |
| p3_safe_s1_01 | 4 | 0 | 4 | score conforme | Correção adjacente da mesma probabilidade, com marcador explícito; contagem independente. 2+2=4. |
| p3_safe_s1_02 | 2 | 0 | 0 | guard FP; crédito legítimo perdido | Retratação deítica inequívoca da linha anterior; a nova potência representa duas escolhas uniformes. |
| p3_safe_s1_03 | 2 | 0 | 0 | guard FP; crédito legítimo perdido | Pensando melhor acompanhado de retirada explícita da cor/contagem; estratégia corrigida do caso 2 vale 2, sem inferir condicionais. |
| p3_safe_s1_04 | 2 | 0 | 2 | score conforme | Rejeição inequívoca da contagem anterior e nova contagem explícita; nenhuma probabilidade declarada. |
| p3_safe_s1_05 | 2 | 0 | 0 | crédito legítimo perdido | O correto é mais substituição explícita; valor final de b concede somente b.conclusion=2. |
| p3_safe_s1_06 | 2 | 2 | 2 | score conforme | Risco acompanhado de explicação literal de anulação, sem depender só de Markdown; a resposta final isolada é autorizada. |
| p3_safe_s1_07 | 1 | 0 | 0 | guard FP; crédito legítimo perdido | Substituição explicitamente vinculada ao conjunto, sem inventar estratégias; c.continue=1. |
| p3_safe_s1_08 | 2 | 2 | 0 | crédito legítimo perdido | Autocorreção em notação com anulado/válido e confirmação da única linha mantida. Igualdade de a verificada, sem inferir a.count. |
| p3_safe_s2_01 | 2 | 4 | 2 | score conforme | Contagens 2 e 3 adotadas conflitam; a.count bloqueado. Probabilidade de a é parcela independente e continua valendo 2. |
| p3_safe_s2_02 | 0 | 0 | 0 | score conforme | Valor falso antes do correto, ambos explicitamente adotados; ausência de retratação impede crédito de a.probability. |
| p3_safe_s2_03 | 0 | 0 | 1 | FALSE_CREDIT: c.continue=1 | Lista exaustiva de continuação e inclusão de outro estado são incompatíveis. A propriedade é continuação em c, não repetição de b; não transplantar o guard b. |
| p3_safe_s2_04 | 0 | 0 | 0 | score conforme | A conta verdadeira não apaga a afirmação 1/4 da mesma probabilidade; b.conclusion bloqueado. |
| p3_safe_s2_05 | 0 | 0 | 0 | FALLBACK | Estratégias incompatíveis no mesmo estado; a estratégia verdadeira não pode ganhar a mesma parcela diante da outra adotada. |
| p3_safe_s2_06 | 2 | 2 | 4 | FALSE_CREDIT: b.conclusion=2 | A relação dos diferentes é correta e independente. A afirmação falsa de repetição deve vetar b.conclusion por source_consistency; total correto não saneia contexto de contagem falso. |
| p3_safe_s2_07 | 0 | 0 | 0 | score conforme | Uma igualdade aritmética é falsa. A prova da outra não autoriza ignorar refutação da mesma obrigação. |
| p3_safe_s2_08 | 0 | 0 | 0 | score conforme | Exaustividade {2,4} e inclusão de 1 são incompatíveis e ambas falsas no modelo. Nenhum número correto da diagonal é fornecido. Exigir retenção da incompatibilidade, não apenas zero por ausência de positivo. |
| p3_safe_s3_01 | 0 | 0 | 0 | score conforme | Uma relação verdadeira explicitamente hipotética não constitui evidência adotada. |
| p3_safe_s3_02 | 2 | 0 | 2 | score conforme | Tentativa descartada não pontua c. Afirmação adotada de outro item permanece independente. |
| p3_safe_s3_03 | 0 | 0 | 0 | score conforme | Atribuição exclusiva a terceiro, sem adoção; nenhum crédito por valor verdadeiro citado. |
| p3_safe_s3_04 | 0 | 0 | 0 | score conforme | Conteúdo atribuído ao enunciado não preenche a obrigação do aluno. |
| p3_safe_s3_05 | 2 | 0 | 2 | score conforme | Pergunta não adotada não é contradição ativa; a contagem afirmada permite apenas a.count. |
| p3_safe_s3_06 | 2 | 0 | 2 | score conforme | Condição matemática de ramo adotada não é hipótese exploratória. Estratégia vale 2; só uma condicional não completa a parcela conjunta. |
| p3_safe_s3_07 | 2 | 0 | 0 | crédito legítimo perdido | Alternativa explicitamente negada não é decisão concorrente; somente a estratégia adotada é pontuável. |
| p3_safe_s3_08 | 2 | 0 | 2 | score conforme | Erro citado para refutação não vira afirmação ativa; relação de pares ordenados é evidência independente válida. |
| p3_safe_s4_01 | 2 | 0 | 2 | score conforme | Na verdade trata da probabilidade e não revoga a contagem. As duas contagens continuam adotadas; a.probability é independente. |
| p3_safe_s4_02 | 0 | 0 | 0 | score conforme | Marcador distante e alvo não identificado: não há autorização para apagar a primeira resposta. Conservar conflito e zero na obrigação. |
| p3_safe_s4_03 | 0 | 0 | 0 | score conforme | Correção em outro item não revoga a nem ganha crédito de a; em b não é a probabilidade da segunda branca. |
| p3_safe_s4_04 | 2 | 0 | 2 | score conforme | Número 3 de uma estratégia não se confunde com contagem inicial. c.strategy_case_1=2; as duas contagens de a conflitam. |
| p3_safe_s4_05 | 0 | 0 | 0 | score conforme | Várias afirmações atuais incompatíveis; número correto entre elas não autoriza b.conclusion. |
| p3_safe_s4_06 | 0 | 0 | 0 | score conforme | Valor correto está negado, valor adotado é falso; não promover o primeiro a resposta do aluno. |
| p3_safe_s4_07 | 2 | 0 | 0 | guard FP; crédito legítimo perdido | Retratação tem alvo inequívoco apesar da linha interveniente: só contagem. Aceitar a.count=2, refutar a probabilidade 5/6 mantida. |
| p3_safe_s4_08 | 0 | 0 | 0 | score conforme | Pronome sem referente não autoriza apagar seletivamente os valores falsos. Ambas as obrigações conflitam; score zero. |

## 4. NEW32 — cadeias causais dos falsos créditos

### S2_03 — 1 ponto indevido em c.continue

Fonte ativa 1: `Registro os estados em que decido continuar: continuar: {1,2}.` → claim `{1,2}`, subject `continuar` → `c.continue_compartments` → DETERMINISTIC → checker `tme2-p3-check.v1` → `DETERMINISTIC_VERIFIED` → sufficiency true → award elegível → regra `c.continue`, 1 ponto.

Fonte ativa 2: `Também mantenho o jogo em curso se a primeira branca for atribuída ao compartimento 4; essa inclusão integra minha resposta.` → o extractor manteve a frase como asserted/atribuída/não hipotética, mas com subject `unmapped` → mapping `obligation_subject_type_mismatch` → `CONTEXT_REJECTED` → nenhum checker negativo, nenhum guard, nenhum conflito. Assim a afirmação incompatível adotada desapareceu do caminho de veto.

A pauta concede 1 ponto pelo conjunto correto de continuação; a política congelada exige bloquear essa mesma parcela quando permanece adotada a inclusão incompatível de 4. O ponto não veio diretamente do LLM: houve checker do conjunto correto. O falso crédito resulta da perda da contradição antes da reconciliação. O status `CONTEXT_REJECTED` aqui designa rejeição de mapeamento, não evidência de que a fonte era contexto não adotado. Current: 0.

### S2_06 — 2 pontos indevidos em b.conclusion

Fonte independente `favoraveis_distintos: 2*5=10` → `b.different_favorable` → COMPOSITE → arithmetic + finite_machine + written_relation todos `DETERMINISTIC_VERIFIED` → `COMPOSITE_VERIFIED`, sufficient → `b.different`, 2 pontos legítimos.

Fonte negativa: `Na minha enumeração, ao repetir o compartimento, o terceiro também fornece uma bola branca.` → subject `repeticao_branca`, normalizado `{3}`, asserted → mapping rejeitado `set_payload_omits_source_members`, `CONTEXT_REJECTED`. O atomic guard recuperou o token literal `terceiro` → membership do compartimento 3 → modelo finito → `DETERMINISTIC_FAILED`, refutação verdadeira → conflito não resolvido em `b.same_compartment`. Guard `award_eligible=false`.

Fonte da conclusão: `Apesar dessa inclusão, mantenho a probabilidade da segunda branca em 11/36.` → `b.second_white_probability` → COMPOSITE → arithmetic e finite_machine verificados; `source_consistency=DETERMINISTIC_VERIFIED/no_negative_context`; result_credit_contract verificado → `COMPOSITE_VERIFIED`, sufficient → `b.conclusion`, 2 pontos indevidos. Score Semantic 4, esperado 2, Current 2.

O próprio contrato existente de `source_consistency` prevê veto por fatos refutados/erro técnico em `b.ordered_pairs`, `b.different_favorable` ou `b.same_compartment`. A projeção positiva descartou a frase problemática antes desse componente. O engine executa a verificação positiva antes dos guards e reconcilia guards apenas na mesma obligation_id. A refutação recuperada posteriormente ficou local a `b.same_compartment` e não refez o veto de `b.second_white_probability`. O valor isolado 11/36 é verdadeiro e admite crédito por resultado quando não há contexto negativo; aqui o aluno mantém explicitamente a enumeração falsa que deveria acionar o veto já contratado. A classificação não acrescenta exigência de demonstração à pauta.

Os dois casos possuem checker positivo e sufficiency: **NO CHECKER → NO CREDIT não basta se as evidências contraditórias escapam do veto aplicável**. Não houve award produzido pelo guard, nem promoção direta de um resultado `COMPOSITE_FAILED`; houve crédito positivo incompatível com a segurança contextual exigida.

## 5. NEW32 — perdas legítimas e limites da retratação

| Caso | Perda | Causa observada |
| --- | --- | --- |
| S1_02 | 2 | O span antigo inclui “Corrigindo a minha afirmação anterior”. O validador procura esse marcador depois do span; o novo span começa sobreposto. Retração vira `no_unambiguous_local_retraction`, e o check regular recupera 30 como veto contra 36. |
| S1_03 | 2 | “Pensando melhor, retiro essa escolha de cor e sua contagem” não é reconhecido como vínculo de abandono; a estratégia preta antiga veta a cinza corrigida, apesar de o checker positivo verificar a nova. |
| S1_05 | 2 | Span antigo engloba também a correção; abandono não reconhecido. A linha final recebe `subject_not_uniquely_bound_to_source_clause`. Nenhum resultado suficiente. |
| S1_07 | 1 | Substituição explícita de {2,3} por {1,2} não reconhecida; check regular do conjunto retirado cria conflito e bloqueia a linha final verificada. |
| S1_08 | 2 | Duas interpretações de probabilidade no mesmo span “[anulado] ⇒ [válido]” geram `conflicting_extractor_interpretation`; a linha final independente chega a `FORMAL_VERIFIED`, mas o conflito a bloqueia. |
| S3_07 | 2 | Escolha final preta aceita; contagem normalizada como `preta: 3 vezes` recebe `unsupported_checker_payload`, deixando `COMPOSITE_INCOMPLETE`. Alternativa cinza corretamente rejeitada. |
| S4_07 | 2 | Correção explicitamente limitada à contagem é separada por uma probabilidade não corrigida. Regra de adjacência não reconhece o alvo; contagem 5 retirada vira veto contra 2. A probabilidade 5/6 é corretamente refutada. |

São 13 pontos legítimos perdidos pelo Semantic, distribuídos em sete obrigações. Os 3 pontos indevidos explicam o saldo 27−37=−10. No Current, o único falso crédito novo é S2_01: `a.count=2` apesar das contagens 2 e 3 simultaneamente adotadas; a parcela independente `a.probability=2` é legítima. Não se assume que o Current seja referência correta.

As causas são diagnósticos de integração, representação e escopo da política textual; nenhum código foi corrigido nesta tarefa. Referências do SHA congelado: `tme_semantic_formal_p3/abandonment.py:36` (vínculo local), `mapper.py:132` (interpretações do mesmo span), `engine.py:35` (reconciliação por obligation_id), `engine.py:130` (verificação antes dos guards), `conflict_guard.py:64` (guard especializado em repetição), `tme_p3_checker_first/engine.py:81` (source_consistency). Os arquivos ficam sob `app/confia_lean_auditor/experimental/`.

## 6. OBSERVED_REGRESSION48 — exclusivamente regressão observada

O dataset `semantic_robustness_01` e seus resultados históricos foram preservados. Não é avaliação independente pós-fix. A única revisão de expectativa autorizada e anterior às chamadas foi E02: 2→4 pontos, incluindo `b.same`, pela política explícita de autocorreção. Isso foi aplicado em um sidecar de análise; a fixture histórica não foi editada. E04 continua esperado 2. Nenhuma outra expectativa foi revista.

| Métrica ALL48 | Current | Semantic |
| --- | --- | --- |
| Total esperado | 79 | 79 |
| Total observado | 14 | 61 |
| Exact / 48 | 23 | 39 |
| MAE | 1.4375 | 0.375 |
| Obligation TP | 5 | 37 |
| Obligation FP | 2 | 0 |
| Obligation FN | 41 | 9 |
| Obligation precision | 0.714286 | 1 |
| Obligation recall | 0.108696 | 0.804348 |
| Casos de falso crédito | 2 | 0 |
| Pontos indevidos | 4 | 0 |
| Guard atômico: eventos | 0 | 2 |
| Guard atômico: refutações | 0 | 2 |
| Awards gerados por guard | 0 | 0 |
| Fallback | 0 | 0 |
| Technical uncertainty | 0 | 0 |

Regressões de casos historicamente exatos: **2** de **41**. Casos com nova regra indevidamente pontuada em relação à execução histórica, sob a política esclarecida: **0**. Exact histórico usa a expectativa histórica; qualidade atual usa a política esclarecida. Os resultados são de uma realização do extractor: uma diferença não demonstra causalidade exclusiva do patch.

| Caso | Semantic histórico | Semantic atual | Esperado atual | Regrediu de exact histórico? | Nova regra indevida |
| --- | --- | --- | --- | --- | --- |
| p3_rob_a08 | 8 | 6 | 8 | sim | — |
| p3_rob_e02 | 4 | 2 | 4 | não | — |
| p3_rob_e04 | 2 | 2 | 2 | não | — |
| p3_rob_e08 | 2 | 0 | 2 | sim | — |

Sob a política esclarecida aplicada simetricamente às duas realizações, a execução histórica tinha 42 scores exatos e o replay tem 39: **três perdas**, A08, E08 e E02. A coluna “exact histórico” acima conserva a definição original (41), por isso E02 não aparece como regressão nessa coluna; isso não o torna aprovado. O zero histórico de F08 usou fallback e só conta para comparação do pipeline, não como sucesso histórico do extractor.

**A08: 8→6.** Perdeu `c.total_win_probability`, 2 pontos. A expressão original `(2/6)*(1/2)=1/6` estava escrita. O extractor normalizou como `1/6, com (2/6)*(1/2)=1/6`, rejeitado por `unsupported_checker_payload`; `CONTEXT_REJECTED`, sem checker suficiente nem award de `c.total`. Continuação, duas estratégias e condicionais permaneceram verificadas. A perda é de representação, sem conflito matemático.

**E08: 2→0.** A fala falsa atribuída a Beatriz foi corretamente rejeitada. A resposta própria “somente o sexto libera branca” foi normalizada como frase, não conjunto/membership executável: `unsupported_checker_payload`, sem resultado suficiente para `b.same_compartment`. Não houve guard nem conflito; a perda foi do payload da posição própria, não contaminação contextual pela citação.

**E02 não passou no replay real**: esperado 4, observado 2; apenas `a.count`. O extractor marcou o claim antigo abandoned, porém seu source_span compreendeu tanto a afirmação antiga quanto a frase iniciada por “Na verdade”. O validador retornou `no_unambiguous_local_retraction`, recuperou visibilidade negativa e o guard refutou o membership antigo. `b.same_compartment` permaneceu em conflito. O controle anterior com 4 pontos não garantiu robustez à delimitação real de spans. Mantém-se esperado 4, sem ajustar a expectativa nem rerodar.

Os dois guards atômicos do replay refutaram matematicamente o quinto compartimento. Em E04, isso é o veto correto; em E02, é **um falso positivo operacional do guard**, pois a afirmação foi legitimamente substituída. Assim, neste replay, há 1/2 veto atômico apropriado e 1/2 indevido, com zero awards gerados. O campo automatizado `guard_false_positives=0` da agregação antiga não mede esse alvo: o schema histórico não possui annotations de superseded. Ele não pode ser interpretado como ausência de falso positivo; a classificação manual acima deriva da política E02 registrada antes da execução e do trace.

**E04 passou no requisito de segurança**: observado 2, apenas `a.count`; conflito `b.same_compartment` preservado pelo guard atômico, sem abandono registrado. Os dois resultados devem ser relatados separadamente: a correção preserva esse conflito, mas ainda perde uma autocorreção legítima.

Fallback Semantic no replay: nenhum. A subset SEMANTIC-SUCCESS possui 48 casos. Os indicadores de retratação/contexto do schema novo não são extrapolados aos receipts antigos; avaliam-se E02/E04 pelos traces reais.

| Caso antigo | Esperado sob política atual | Current atual | Semantic atual | Semantic histórico | Nota |
| --- | --- | --- | --- | --- | --- |
| p3_rob_a01 | 2 | 0 | 0 | 0 |  |
| p3_rob_a02 | 2 | 0 | 0 | 0 |  |
| p3_rob_a03 | 2 | 0 | 0 | 0 |  |
| p3_rob_a04 | 2 | 0 | 2 | 2 |  |
| p3_rob_a05 | 2 | 0 | 2 | 2 |  |
| p3_rob_a06 | 2 | 0 | 0 | 0 |  |
| p3_rob_a07 | 2 | 0 | 0 | 0 |  |
| p3_rob_a08 | 8 | 0 | 6 | 8 |  |
| p3_rob_b01 | 2 | 0 | 2 | 2 |  |
| p3_rob_b02 | 2 | 2 | 2 | 2 |  |
| p3_rob_b03 | 2 | 0 | 2 | 2 |  |
| p3_rob_b04 | 2 | 2 | 2 | 2 |  |
| p3_rob_b05 | 2 | 2 | 2 | 2 |  |
| p3_rob_b06 | 2 | 0 | 2 | 2 |  |
| p3_rob_b07 | 2 | 0 | 2 | 2 |  |
| p3_rob_b08 | 8 | 0 | 8 | 8 |  |
| p3_rob_c01 | 2 | 2 | 2 | 2 |  |
| p3_rob_c02 | 2 | 0 | 2 | 2 |  |
| p3_rob_c03 | 0 | 0 | 0 | 0 |  |
| p3_rob_c04 | 2 | 2 | 0 | 0 |  |
| p3_rob_c05 | 0 | 0 | 0 | 0 |  |
| p3_rob_c06 | 2 | 0 | 2 | 2 |  |
| p3_rob_c07 | 5 | 0 | 5 | 5 |  |
| p3_rob_c08 | 0 | 0 | 0 | 0 |  |
| p3_rob_d01 | 0 | 0 | 0 | 0 |  |
| p3_rob_d02 | 0 | 0 | 0 | 0 |  |
| p3_rob_d03 | 2 | 0 | 2 | 2 |  |
| p3_rob_d04 | 0 | 0 | 0 | 0 |  |
| p3_rob_d05 | 0 | 0 | 0 | 0 |  |
| p3_rob_d06 | 0 | 0 | 0 | 0 |  |
| p3_rob_d07 | 4 | 0 | 4 | 4 |  |
| p3_rob_d08 | 2 | 0 | 2 | 2 |  |
| p3_rob_e01 | 2 | 0 | 2 | 2 |  |
| p3_rob_e02 | 4 | 0 | 2 | 4 |  |
| p3_rob_e03 | 2 | 2 | 2 | 2 |  |
| p3_rob_e04 | 2 | 0 | 2 | 2 |  |
| p3_rob_e05 | 0 | 0 | 0 | 0 |  |
| p3_rob_e06 | 0 | 0 | 0 | 0 |  |
| p3_rob_e07 | 2 | 0 | 2 | 2 |  |
| p3_rob_e08 | 2 | 0 | 0 | 2 |  |
| p3_rob_f01 | 0 | 0 | 0 | 0 |  |
| p3_rob_f02 | 0 | 0 | 0 | 0 |  |
| p3_rob_f03 | 0 | 2 | 0 | 0 |  |
| p3_rob_f04 | 0 | 0 | 0 | 0 |  |
| p3_rob_f05 | 0 | 0 | 0 | 0 |  |
| p3_rob_f06 | 0 | 0 | 0 | 0 |  |
| p3_rob_f07 | 0 | 0 | 0 | 0 |  |
| p3_rob_f08 | 0 | 0 | 0 | 0 |  |

## 7. Status e rastreabilidade

Status principais de verification_results, separados dos componentes internos e dos guards:

| População | Modo | Status observados |
| --- | --- | --- |
| NEW32 | tme_current | DETERMINISTIC_FAILED=10, DETERMINISTIC_VERIFIED=9, FORMAL_VERIFIED=2, FORMAL_REFUTED=1 |
| NEW32 | tme_semantic_formal | DETERMINISTIC_VERIFIED=16, CONTEXT_REJECTED=37, COMPOSITE_VERIFIED=10, FORMAL_VERIFIED=2, CONFLICTING_EVIDENCE=2, DETERMINISTIC_FAILED=11, COMPOSITE_FAILED=3, FORMAL_REFUTED=1, COMPOSITE_INCOMPLETE=1 |
| OBSERVED_REGRESSION48 | tme_current | DETERMINISTIC_VERIFIED=8, DETERMINISTIC_FAILED=3 |
| OBSERVED_REGRESSION48 | tme_semantic_formal | CONTEXT_REJECTED=27, COMPOSITE_VERIFIED=23, DETERMINISTIC_VERIFIED=20, FORMAL_VERIFIED=1, COMPOSITE_FAILED=9, COMPOSITE_INCOMPLETE=6, DETERMINISTIC_FAILED=4 |

Os formal_status internos não são confundidos com o status composto. Por exemplo, um COMPOSITE pode conter prova Lean de aritmética e ainda falhar na relação. FORMAL_NOT_ATTEMPTED não é refutação; fallback não é FORMAL_ERROR. Nos novos casos, FORMAL_VERIFIED/FORMAL_REFUTED foram preservados nos recibos, e nenhum FORMAL_ERROR ou technical uncertainty foi contabilizado.

Artefatos para auditoria, sem novas chamadas de modelo:

- [pre_execution_freeze.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/pre_execution_freeze.json)
- [novelty_check.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/novelty_check.json)
- [commands.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/commands.json)
- [preservation_before.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/preservation_before.json)
- [old_artifact_hashes.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/old_artifact_hashes.json)
- [metrics.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/new32/metrics.json)
- [case_analysis.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/new32/case_analysis.json)
- [observed_policy_expectations.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/observed_policy_expectations.json)
- [metrics.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/observed_regression/metrics.json)
- [case_analysis.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/observed_regression/case_analysis.json)
- [transitions.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/observed_regression/transitions.json)

Os JSONs por caso em `new32/{modo}/{case_id}.json` e `observed_regression/{modo}/{case_id}.json` preservam fonte, resposta do extractor quando disponível, claims/spans, routes, checkers/componentes, statuses, sufficiency, guards, conflitos, awards e créditos. `case_analysis.json` é uma agregação de leitura desses recibos. O script de agregação foi corrigido para tolerar canonical_form nulo do baseline, sem tocar nas execuções ou expectativas. Os diretórios de artefatos são ignorados pelo Git: preservação local não equivale a publicação/versionamento desses traces.

## 8. Preservação e conclusão

Foram reconferidos os cinco hashes congelados, os arquivos rastreados previamente inventariados e os hashes dos artefatos históricos. `git diff` permanece vazio. As únicas novidades versionáveis são as cinco fixtures novas e este relatório; scripts de construção/agregação e resultados estão em artefatos ignorados. SHA permanece `89cda1cab89648d3888775bbcead42ea85bd4861`. Não houve stage nem commit.

NEW32 agora é **DEV observado**, assim como old48; ambos não podem ser apresentados como futura avaliação independente. A segurança não foi revalidada: dois falsos créditos materiais, aceitação incompleta de retratação e E02 perdido no replay impedem promoção do status geral. Nenhuma correção foi implementada.

**P3_SAFETY_FAILURE**

## Apêndice — fontes novas completas e expectativas congeladas

Os textos abaixo reproduzem `sources.json` sem edição após a execução. As expectativas completas, inclusive offsets dos alvos, estão em `expectations.json`.

### p3_safe_s1_01

```text
a) Minha estimativa para a primeira bola branca é 2/3.
Na verdade, a chance da primeira bola branca é 1/3.
Na base encontro exatamente 2 bolas brancas.
```

Esperado: 4. Awards: `a.count=2`, `a.probability=2`. Conflitos esperados: nenhum.

### p3_safe_s1_02

```text
b) Minha primeira linha de contagem foi:
pares_ordenados: 6*5=30
Corrigindo a minha afirmação anterior:
pares_ordenados: 6^2=36
```

Esperado: 2. Awards: `b.space=2`. Conflitos esperados: nenhum.

### p3_safe_s1_03

```text
c) No estado após branca do compartimento 2, escolho preta e conto 3 posições dessa cor.
Pensando melhor, retiro essa escolha de cor e sua contagem.
Para o compartimento 2, após a branca, escolho cinza, que aparece 3 vezes.
```

Esperado: 2. Awards: `c.second_strategy=2`. Conflitos esperados: nenhum.

### p3_safe_s1_04

```text
a) Contei 4 bolas brancas inferiores.
Isto estava errado: eu incluí bolas que não estão na base.
Após a revisão, identifico 2 bolas brancas inferiores.
```

Esperado: 2. Awards: `a.count=2`. Conflitos esperados: nenhum.

### p3_safe_s1_05

```text
b) Deixo inicialmente segunda_branca: 1/6
O correto é segunda_branca: 11/36
A linha correta substitui integralmente minha primeira estimativa; ela é a única resposta que mantenho.
```

Esperado: 2. Awards: `b.conclusion=2`. Conflitos esperados: nenhum.

### p3_safe_s1_06

```text
a) Registro de cálculo:
~~primeira_branca: 5/6~~
O risco acima anula aquela resposta. Abaixo está a resposta que entrego:
primeira_branca: 1/3
```

Esperado: 2. Awards: `a.probability=2`. Conflitos esperados: nenhum.

### p3_safe_s1_07

```text
c) No registro inicial escrevi
continuar: {2,3}
Substituo integralmente esse conjunto pelo seguinte, que é o único adotado:
continuar: {1,2}
```

Esperado: 1. Awards: `c.continue=1`. Conflitos esperados: nenhum.

### p3_safe_s1_08

```text
a) Para a primeira branca, reescrevo a linha de cálculo:
(3/6=1/2) [anulado] ⇒ (2/6=1/3) [válido].
Única linha que mantenho:
primeira_branca: 2/6=1/3
```

Esperado: 2. Awards: `a.probability=2`. Conflitos esperados: nenhum.

### p3_safe_s2_01

```text
a) Na minha resposta mantenho as três linhas abaixo, sem cancelar nenhuma:
inferiores_brancas: 2
Também sustento que há 3 bolas brancas inferiores.
primeira_branca: 1/3
```

Esperado: 2. Awards: `a.probability=2`. Conflitos esperados: a.bottom_white_count.

### p3_safe_s2_02

```text
a) A chance da primeira bola branca é 1/6.
Mais adiante registro também: A chance da primeira bola branca é 1/3.
São duas conclusões que mantenho simultaneamente, não uma correção.
```

Esperado: 0. Awards: nenhum. Conflitos esperados: a.first_white_probability.

### p3_safe_s2_03

```text
c) Registro os estados em que decido continuar: continuar: {1,2}.
Também mantenho o jogo em curso se a primeira branca for atribuída ao compartimento 4; essa inclusão integra minha resposta.
```

Esperado: 0. Awards: nenhum. Conflitos esperados: c.continue_compartments.

### p3_safe_s2_04

```text
b) Uso ao mesmo tempo as duas expressões abaixo como probabilidade da segunda branca:
segunda_branca: (10+1)/36=11/36
segunda_branca: 1/4
Nenhuma das duas foi descartada.
```

Esperado: 0. Awards: nenhum. Conflitos esperados: b.second_white_probability.

### p3_safe_s2_05

```text
c) Minha política mantém ambas as escolhas a seguir:
Para a branca que veio do compartimento 2, adoto cinza, que aparece 3 vezes.
Para esse mesmo caso 2, adoto igualmente preta, que aparece 3 vezes.
As duas escolhas ficam como decisões atuais.
```

Esperado: 0. Awards: nenhum. Conflitos esperados: c.strategy_case_2.

### p3_safe_s2_06

```text
b) Separei os eventos de compartimentos diferentes na linha
favoraveis_distintos: 2*5=10
Na minha enumeração, ao repetir o compartimento, o terceiro também fornece uma bola branca.
Apesar dessa inclusão, mantenho a probabilidade da segunda branca em 11/36.
```

Esperado: 2. Awards: `b.different=2`. Conflitos esperados: b.second_white_probability.

### p3_safe_s2_07

```text
a) Minha folha apresenta duas igualdades que afirmo serem válidas para a mesma primeira branca:
primeira_branca: 2/6=1/3
primeira_branca: 2/6=2/3
```

Esperado: 0. Awards: nenhum. Conflitos esperados: a.first_white_probability.

### p3_safe_s2_08

```text
b) Para duas retiradas do mesmo local, proponho a lista
repeticao_branca: {2,4}
Declaro essa lista exaustiva.
Na repetição do mesmo compartimento, o primeiro também produz branca; mantenho expressamente as duas alegações.
```

Esperado: 0. Awards: nenhum. Conflitos esperados: b.same_compartment.

### p3_safe_s3_01

```text
b) Hipótese exploratória que não adoto na resposta:
pares_ordenados: 6^2=36
Esta linha é apenas a hipótese sob exame; não apresento uma conclusão.
```

Esperado: 0. Awards: nenhum. Conflitos esperados: nenhum.

### p3_safe_s3_02

```text
c) Tentativa explicitamente descartada:
No caso 1, após branca, preta aparece 3 vezes e seria minha escolha.

a) Resposta que mantenho: Na base do dispositivo identifico 2 bolas brancas inferiores.
```

Esperado: 2. Awards: `a.count=2`. Conflitos esperados: nenhum.

### p3_safe_s3_03

```text
a) Rafael afirmou: a probabilidade da primeira bola branca é 1/3.
Estou apenas transcrevendo a fala dele; não a adoto como minha resposta.
```

Esperado: 0. Awards: nenhum. Conflitos esperados: nenhum.

### p3_safe_s3_04

```text
c) Transcrição identificada como enunciado, não como solução:
continuar: {1,2}
Não apresento aqui uma estratégia própria.
```

Esperado: 0. Awards: nenhum. Conflitos esperados: nenhum.

### p3_safe_s3_05

```text
a) Seria a probabilidade da primeira branca igual a 1/2? Essa é uma pergunta retórica, não uma resposta afirmada.
Minha afirmação é que existem 2 bolas brancas inferiores.
```

Esperado: 2. Awards: `a.count=2`. Conflitos esperados: nenhum.

### p3_safe_s3_06

```text
c) Condicionado à retirada de branca do compartimento 1, escolho preta, que aparece 3 vezes.
Nesse caso 1, a probabilidade condicional de sucesso é 3/6=1/2.
```

Esperado: 2. Awards: `c.first_strategy=2`. Conflitos esperados: nenhum.

### p3_safe_s3_07

```text
c) Comparo uma alternativa com minha escolha final.
Não escolho cinza no caso 1, embora essa alternativa tenha 2 posições.
Minha decisão para a branca do compartimento 1 é preta, que aparece 3 vezes.
```

Esperado: 2. Awards: `c.first_strategy=2`. Conflitos esperados: nenhum.

### p3_safe_s3_08

```text
b) A frase "a probabilidade da segunda branca é 12/36" é um erro que estou refutando, e não minha resposta.
Para minha contagem dos pares ordenados uso 6*6=36.
```

Esperado: 2. Awards: `b.space=2`. Conflitos esperados: nenhum.

### p3_safe_s4_01

```text
a) Mantenho a contagem
inferiores_brancas: 4
Na verdade, a probabilidade da primeira branca é 1/3.
Além disso, mantenho a outra contagem
inferiores_brancas: 2
```

Esperado: 2. Awards: `a.probability=2`. Conflitos esperados: a.bottom_white_count.

### p3_safe_s4_02

```text
a) Registro como resposta
primeira_branca: 1/2

Depois desenhei a disposição das filas.
Anotei a ordem das tentativas.
Separei uma folha para os cálculos.

Corrigindo um cálculo que não identifico aqui, registro também
primeira_branca: 1/3
Não indico qual anotação anterior foi retirada.
```

Esperado: 0. Awards: nenhum. Conflitos esperados: a.first_white_probability.

### p3_safe_s4_03

```text
a) Minha resposta neste item permanece
primeira_branca: 1/2

b) Na verdade, a probabilidade da primeira branca é 1/3. A frase está escrita apenas neste item.
```

Esperado: 0. Awards: nenhum. Conflitos esperados: nenhum.

### p3_safe_s4_04

```text
c) No caso 1 após branca, escolho preta, que aparece 3 vezes.

a) Na verdade, existem 3 bolas brancas inferiores.
Também mantenho inferiores_brancas: 2
```

Esperado: 2. Awards: `c.first_strategy=2`. Conflitos esperados: a.bottom_white_count.

### p3_safe_s4_05

```text
b) Estas são três respostas concorrentes que mantenho, sem escolher uma ou apagar as outras:
segunda_branca: 11/36
segunda_branca: 7/18
segunda_branca: 1/2
```

Esperado: 0. Awards: nenhum. Conflitos esperados: b.second_white_probability.

### p3_safe_s4_06

```text
a) Não aceito a proposição de que a probabilidade da primeira branca é 1/3.
Minha afirmação atual é primeira_branca: 1/2
```

Esperado: 0. Awards: nenhum. Conflitos esperados: nenhum.

### p3_safe_s4_07

```text
a) Meu registro inicial contém duas quantidades:
inferiores_brancas: 5
primeira_branca: 5/6
Corrigindo apenas a contagem das bolas inferiores, substituo aquela contagem por
inferiores_brancas: 2
A probabilidade 5/6 permanece sendo minha resposta.
```

Esperado: 2. Awards: `a.count=2`. Conflitos esperados: nenhum.

### p3_safe_s4_08

```text
a) Uma ficha contém
inferiores_brancas: 2
primeira_branca: 1/3
Outra ficha, também adotada, contém
inferiores_brancas: 4
primeira_branca: 2/3
Digo que "isso" deve ser corrigido, sem identificar a ficha ou a quantidade. Ambas as fichas ainda constam como minhas respostas.
```

Esperado: 0. Awards: nenhum. Conflitos esperados: a.bottom_white_count, a.first_white_probability.
