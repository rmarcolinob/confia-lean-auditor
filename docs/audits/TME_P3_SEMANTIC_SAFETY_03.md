# TME P3 — Semantic Safety 03

**P3_SAFETY_FAILURE.** Esta avaliação independente em relação ao SHA congelado encontrou **1 caso, 1 obrigação e 2 pontos de falso crédito automático**, além de 5 casos de falso hard veto. O ganho de score sobre Current não compensa a falha de segurança. **Não promover P3 para P3_SEMANTIC_ADVANTAGE_CONFIRMED.**

## 1. SHA, execução e preservação

Implementação congelada: `6fb07d4d15626e27b7c759a4e32f9cb3b415d2ea`. Esse commit registra a regressão observada; seu pai `a6ab3d2c173ee801e1bc5a27d155215c054e007d` contém a implementação unificada. Os manifests dos dois modos confirmam o mesmo HEAD e worktree limpo. Nenhum código, prompt, mapper, resolver, policy, checker, pauta ou expectativa foi alterado durante/após a execução. Sem commit e sem P4.

O dataset foi criado e congelado em `/private/tmp/p3-safety03/frozen/`. Os dois runners leram **somente sources.json e ids.json** dali. Depois de ambos concluírem, os cinco arquivos foram copiados byte a byte para o destino solicitado. Isso preservou worktree limpo na largada dos dois modos sem exigir commit. A cópia final e a preservação da implementação foram verificadas por hash.

Configuração: `gpt-6.1-sol`, effort `medium`, `CONFIA_TME_SEMANTIC_ENABLED=0`, `use_lean=True`, timeout 180 s, max_retries=0. Uma execução por modo, nenhuma nova tentativa após resultados. Current não chamou extractor/API. A autorização explícita de envio à API foi obtida depois que a revisão automática não reconheceu a autorização no anexo; o comando rejeitado não iniciou execução.

Congelamento: `2026-11-06T20:46:12.555523+00:00`. [Recibo externo de congelamento](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/freeze_receipt.json); [integridade final](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/final_integrity.json).

- `tme_current`: 2026-11-06T20:47:05.245839+00:00 → 2026-11-06T20:47:07.028374+00:00; state=completed; clean=True; [manifest](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_current/run_manifest.json).
- `tme_semantic_formal`: 2026-11-06T20:47:22.107208+00:00 → 2026-11-06T20:56:52.839060+00:00; state=completed; clean=True; [manifest](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/run_manifest.json).

## 2. Hashes SHA-256

| Arquivo | SHA-256 dos bytes congelados e entregues |
| --- | --- |
| [construction_receipts.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_03/construction_receipts.json) | `96331e54a1d6907c546e7cc5c40b64e41eaf7144ec4bc12f83a5ee130daa55af` |
| [expectations.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_03/expectations.json) | `d79bdde532db58f394d952df818ec1fc349af97a951416e5c9be7d3ebbdb51e2` |
| [ids.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_03/ids.json) | `46b8b660f49e7a999a7e85e2f1a337bf5364f70fd72ee435ed4a86c1d1795fd5` |
| [manifest.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_03/manifest.json) | `8ad97b39d2ff957b32904891ed1f0e2605294dabb76496dc0ec80263f30f04eb` |
| [sources.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_03/sources.json) | `79fce6d0062b6cd5cd237dfb5838779a3f89603079233230af34a746954d836d` |

O hash do manifest fica no recibo externo para evitar autorreferência circular. O próprio manifest contém os hashes dos outros quatro arquivos. Receipts de construção contêm apenas rationale, resumo de estados, score, obrigações e hashes; não contêm bridge, assessment ou dumps de execução.

## 3. Construção independente e revisão prévia

Os 40 textos foram escritos do zero nesta tarefa a partir da máquina, pauta e contrato normativo. Os resultados dos modos não foram usados para escolher textos ou expectativas. A auditoria de construção não executou extractor, mapper, resolver ou pipeline de correção: enumerou independentemente os 36 eventos da máquina, verificou 11 segundas brancas (10 em índices distintos, 1 no repetido 6), contagens/cores e aritmética racional exata. O PautaEngine confirmou a composição das parcelas **a partir das obrigações declaradas na construção**, sem ler texto ou produzir evidência.

Foram validados IDs, spans exatos, direção/subject das relações de revisão, pertença dos IDs ao registry de 13 obrigações, exclusão entre obrigações satisfeitas e vetos esperados, dependências de estratégias/total e fechamento da soma dos awards. Essa checagem confirmou a composição dos scores e os valores canônicos; não prova automaticamente a interpretação discursiva em linguagem livre nem substitui a leitura de relações cor–contagem (limite detalhado em §15). Nenhum campo de expectativa, estado esperado, rationale ou receipt foi fornecido ao extractor.

Depois da redação, uma triagem comparou os textos novos com os 80 anteriores apenas para detectar reutilização: zero cópias exatas; maior Jaccard de sequências de sete palavras = 0.047619. Essa medida é evidência auxiliar de novidade textual, não prova automática contra toda paráfrase. Os objetos matemáticos e o vocabulário contratual se repetem porque pertencem à mesma questão; os cenários discursivos foram escritos novamente. E02/E04/S2_05/A08/E08 não foram usados como moldes.

Independência aqui significa conjunto novo congelado antes de avaliar a implementação fixa. Não significa anotação cega por avaliadores externos: o autor conhece os fracassos históricos e os requisitos de risco. Não há gold externo nem holdout utilizado. Após esta única execução, Safety03 passa a ser **DEV observado**, sem validade como futura avaliação independente de um fix.

## 4. Famílias e resultados por caso

A: ACTIVE, 8; B: autocorreção/SUPERSEDED, 8; C: NON_ADOPTED, 8; D: AMBIGUOUS, 8; E: cross-state, 8. Foram congeladas 98 anotações: 54 ACTIVE, 13 SUPERSEDED, 12 NON_ADOPTED e 19 AMBIGUOUS. Score total esperado: 71. O conjunto inclui posição final falsa que substitui correta, contradição ativa, estratégia revisada, ambiguidades com crédito independente e uma solução completa de c.

`FC` = falso crédito; `FV` = falso veto; `MISS` = parcela legítima perdida. Mais de uma classificação pode coexistir no mesmo caso, inclusive score exato com witness indevido. O link de cada caso leva à auditoria completa; as fontes integrais estão em sources.json.

| case_id | expected | Current | Semantic | fallback | erro/observação |
| --- | ---: | ---: | ---: | --- | --- |
| [p3_s03_a01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a01.json) | 2 | 0 | 2 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_a02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a02.json) | 0 | 0 | 0 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_a03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a03.json) | 0 | 0 | 0 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_a04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a04.json) | 2 | 0 | 2 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_a05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a05.json) | 0 | 0 | 2 | não | FC: b.same |
| [p3_s03_a06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a06.json) | 2 | 0 | 0 | não | MISS: c.first_strategy |
| [p3_s03_a07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a07.json) | 0 | 0 | 0 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_a08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a08.json) | 4 | 0 | 4 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_b01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b01.json) | 2 | 0 | 2 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_b02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b02.json) | 2 | 0 | 0 | não | FV: a.first_white_probability; MISS: a.probability |
| [p3_s03_b03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b03.json) | 2 | 0 | 2 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_b04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b04.json) | 1 | 0 | 0 | não | FV: c.continue_compartments; MISS: c.continue |
| [p3_s03_b05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b05.json) | 2 | 0 | 0 | não | FV: b.second_white_probability; MISS: b.conclusion |
| [p3_s03_b06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b06.json) | 2 | 0 | 0 | não | MISS: c.first_strategy |
| [p3_s03_b07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b07.json) | 2 | 0 | 2 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_b08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b08.json) | 2 | 0 | 0 | não | FV: a.bottom_white_count; MISS: a.count |
| [p3_s03_c01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c01.json) | 2 | 0 | 0 | não | MISS: a.count |
| [p3_s03_c02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c02.json) | 2 | 0 | 2 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_c03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c03.json) | 1 | 0 | 0 | sim | MISS: c.continue |
| [p3_s03_c04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c04.json) | 2 | 0 | 2 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_c05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c05.json) | 2 | 0 | 2 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_c06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c06.json) | 2 | 0 | 0 | não | MISS: a.count |
| [p3_s03_c07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c07.json) | 2 | 0 | 2 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_c08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c08.json) | 1 | 0 | 1 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_d01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d01.json) | 0 | 0 | 0 | sim | score conforme expectation; estados auditados separadamente |
| [p3_s03_d02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d02.json) | 2 | 0 | 0 | não | MISS: a.count |
| [p3_s03_d03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d03.json) | 0 | 0 | 0 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_d04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d04.json) | 0 | 0 | 0 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_d05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d05.json) | 0 | 0 | 0 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_d06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d06.json) | 2 | 0 | 0 | sim | MISS: a.count |
| [p3_s03_d07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d07.json) | 0 | 0 | 0 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_d08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d08.json) | 2 | 0 | 0 | não | MISS: c.second_strategy |
| [p3_s03_e01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e01.json) | 4 | 0 | 0 | não | FV: a.first_white_probability; MISS: a.count,a.probability |
| [p3_s03_e02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e02.json) | 0 | 0 | 0 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_e03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e03.json) | 4 | 0 | 2 | não | MISS: a.count |
| [p3_s03_e04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e04.json) | 2 | 0 | 0 | não | MISS: a.count |
| [p3_s03_e05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e05.json) | 2 | 0 | 0 | não | MISS: a.count |
| [p3_s03_e06](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e06.json) | 4 | 0 | 4 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_e07](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e07.json) | 2 | 0 | 2 | não | score conforme expectation; estados auditados separadamente |
| [p3_s03_e08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e08.json) | 8 | 0 | 1 | não | MISS: c.first_strategy,c.second_strategy,c.conditionals,c.total |

## 5. Métricas primárias de segurança

Parcelas falsas são contadas por rule_id realmente pontuado não autorizado pelas expectativas congeladas, **ou por witness selecionado de claim anotado como não ativo**. Não se deduz segurança do score agregado e não se compensa falso crédito com perda em outra parcela. Pontos de uma regra all_of contam uma vez. Obrigações FP de elegibilidade e obrigações de parcelas pagas são métricas distintas.

False hard veto conta obrigação legítima bloqueada por receipt aplicado, com os pontos das parcelas perdidas que dela dependem; rejeição de representação sem receipt não é false veto. Pode haver simultaneamente perda representacional e veto; nesse caso o veto é indevido, mas removê-lo sozinho pode não recuperar a parcela.

| Métrica | ALL40 Semantic | SEMANTIC_SUCCESS_ONLY |
| --- | ---: | ---: |
| Casos | 40 | 37 |
| Falso crédito: casos | 1 | 1 |
| Falso crédito: obrigações em parcelas pagas | 1 | 1 |
| Falso crédito: pontos | 2.0 | 2.0 |
| Falso veto: casos | 5 | 5 |
| Falso veto: obrigações | 5 | 5 |
| Falso veto: pontos bloqueados | 9.0 | 9.0 |

## 6. Discourse-state accuracy e retratações

Unidade: claim anotado com span literal, subject/obrigação e estado esperado, não cada alias nativo/semântico. Corretude exige que todos os aliases alinhados concordem com o estado esperado; ausência de alinhamento é falha de cobertura, não acerto por abstenção. Esse contador inclui asserted_content com mais de uma localização possível, e não equivale sempre a omissão do extractor. `unmapped` pode ser alinhado por span/obrigação para registrar erro de representação em vez de inventar omissão. Sem fuzzy matching de números. Nas alternativas de subject D05, cada alvo contratual permanece separado. A coluna ALL40 é cobertura operacional; a acurácia da camada semântica é lida somente em SEMANTIC_SUCCESS_ONLY. Claims de fallback não são convertidos em erros do extractor.

| Estado esperado | ALL40: corretos/alvos | SUCCESS_ONLY: corretos/alvos | Sem alinhamento SUCCESS | Mistos SUCCESS | Uso em award SUCCESS | Hard veto SUCCESS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ACTIVE | 48/54 | 48/52 (92.31%) | 0 | 0 | 18 | 3 |
| SUPERSEDED | 0/13 | 0/13 (0.00%) | 2 | 0 | 0 | 4 |
| NON_ADOPTED | 4/12 | 4/11 (36.36%) | 0 | 0 | 0 | 2 |
| AMBIGUOUS | 4/19 | 4/16 (25.00%) | 0 | 0 | 0 | 2 |

Casos com correção: **12**; resultado operacional final integralmente aceito, sem uso da posição retirada: **4**. Claims retirados não reconhecidos como SUPERSEDED: **13 de 13**. False superseding observado: **0** alvos que não deveriam estar SUPERSEDED. O caso E02 exige retirar uma posição correta mesmo que a nova seja falsa; ver sua auditoria de I14.

Conflitos não retratados previstos: **1/2 casos preservados integralmente**. As restrições de AMBIGUOUS e retirada não podem ser avaliadas apenas pelos rótulos que o próprio resolver emitiu: os testes end-to-end usam também as anotações prévias da fonte.

Nenhum dos 12 casos teve todos os vínculos de retirada reconhecidos como SUPERSEDED. Os quatro resultados operacionais compatíveis são B01, B03, B07 e E02: nos três primeiros a posição antiga ficou sem autoridade executável; no último a nova posição falsa foi refutada. Esses quatro scores não demonstram reconhecimento correto de retratação.

## 7. False automatic credit: casos e proveniência

### p3_s03_a05

Fonte integral:

```text
b) Minha lista fechada de compartimentos que dão branca ao repetir é {6}. Acrescento uma afirmação que também considero válida: repetir o compartimento 3 dá branca.
```

Expected=0; Semantic=2. Parcelas indevidas: `b.same` (2 pontos; rule_not_authorized_by_frozen_expectation).

- `p3_s03_a05:C1` [9,72): “lista fechada de compartimentos que dão branca ao repetir é {6}” → IDs `E002:p3:1a9b2549534ea20bd788` → esperado ACTIVE, resolvido ACTIVE → mapping b.same_compartment: compatible_pending_checker → recibos de verificação DETERMINISTIC_VERIFIED → policy NOT_APPLICABLE.
- `p3_s03_a05:C2` [128,163): “repetir o compartimento 3 dá branca” → IDs `E002:p3:962f452cebaf26ae3f12` → esperado ACTIVE, resolvido AMBIGUOUS → mapping b.same_compartment: discourse_ambiguous → recibos de verificação CONTEXT_REJECTED → policy nenhum receipt.

[Cadeia completa, com checker, sufficiency, receipts, reconciliação e award](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a05.json); [resultado integral original](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_a05.json).


Em A05, o modelo finito da máquina mostra que a segunda bola do compartimento 3 é preta; a inclusão escrita é falsa. Não houve award direto para essa inclusão: o falso crédito é a parcela `b.same` mantida apesar da contradição ativa sobre a mesma obrigação. O conjunto `{6}` teve DETERMINISTIC_VERIFIED e sufficient=true; a inclusão ficou CONTEXT_REJECTED, sem execução de checker matemático nem receipt de veto, e a reconciliação não bloqueou b.same.

## 8. False hard veto: casos e proveniência

- **p3_s03_b02** — bloqueadas: `a.first_white_probability`. “chance de branca na primeira retirada era 1/2” [9,54) deveria ser SUPERSEDED, ficou ACTIVE; native_checker: DETERMINISTIC_FAILED / positive_checker: DETERMINISTIC_FAILED. [Trace por claim e por veto](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b02.json).
- **p3_s03_b04** — bloqueadas: `c.continue_compartments`. “indicação para continuar era o conjunto {1,4}” [5,50) deveria ser SUPERSEDED, ficou ACTIVE; native_checker: DETERMINISTIC_FAILED / positive_checker: DETERMINISTIC_FAILED. [Trace por claim e por veto](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b04.json).
- **p3_s03_b05** — bloqueadas: `b.second_white_probability`. “probabilidade da segunda branca ficou anotada como 7/36” [5,60) deveria ser SUPERSEDED, ficou ACTIVE; native_checker: COMPOSITE_FAILED / positive_checker: COMPOSITE_FAILED. [Trace por claim e por veto](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b05.json).
- **p3_s03_b08** — bloqueadas: `a.bottom_white_count`. “quatro brancas na base” [17,39) deveria ser SUPERSEDED, ficou ACTIVE; native_checker: DETERMINISTIC_FAILED / positive_checker: DETERMINISTIC_FAILED. [Trace por claim e por veto](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b08.json).
- **p3_s03_e01** — bloqueadas: `a.first_white_probability`. “nota de uma colega dizia primeira_branca: 7/12” [5,51) deveria ser NON_ADOPTED, ficou ACTIVE; native_checker: DETERMINISTIC_FAILED / positive_checker: DETERMINISTIC_FAILED. [Trace por claim e por veto](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e01.json).

## 9. Os vinte invariantes

As oportunidades são operações/alvos realmente exercitados, não uma porcentagem comum entre invariantes. I2/I4/I5/I6/I14/I20 incluem o estado normativo da fonte para não mascarar erro do resolver como “policy obedecida”. I9/I12/I19 verificam autenticação/autoridade interna. Ausência de exposição é registrada como NOT_EXERCISED, nunca como teste aprovado.

A auditoria de ordem, envelope, flags, idempotência e receipts reutiliza os claims e resultados congelados da única rodada. Executa apenas resolver/policy/reconcile/award sobre esses receipts; não chama modelo, Lean ou qualquer um dos dois modos de avaliação novamente. Não reordena semanticamente a fonte. I11 cobre expansão de envelopes com asserted_content único; I19 testa rejeição de revisão adulterada; I12 testa rejeição de candidatos sem receipt emitido. I15 cobre ranges, propriedade e conservação sintática de igualdades; não prova equivalência semântica universal de prosa. I7 exige refutação efetivamente verificada: A05/A07 são lacunas de cobertura negativa, registradas separadamente em `negative_coverage_gaps`, e não violações formais desse condicional por ausência de checker. I8 verifica a propagação somente pelas dependências contratadas; falso veto no próprio subject é contado em segurança/I2/I4, não confundido com propagação global. Os três fallbacks não produziram evidências nativas pontuáveis, limitando a exposição de I18 ao caminho vazio.

| invariant | opportunities | violations | casos com violação |
| --- | ---: | ---: | --- |
| I1 | 22 | 0 | — |
| I2 | 12 | 2 | p3_s03_c07, p3_s03_e01 |
| I3 | 62 | 0 | — |
| I4 | 13 | 4 | p3_s03_b02, p3_s03_b04, p3_s03_b05, p3_s03_b08 |
| I5 | 19 | 0 | — |
| I6 | 19 | 2 | p3_s03_d02, p3_s03_d03 |
| I7 | 22 | 0 | — |
| I8 | 22 | 0 | — |
| I9 | 40 | 0 | — |
| I10 | 40 | 0 | — |
| I11 | 5 | 0 | — |
| I12 | 53 | 0 | — |
| I13 | 40 | 0 | — |
| I14 | 1 | 1 | p3_s03_e02 |
| I15 | 105 | 0 | — |
| I16 | 288 | 0 | — |
| I17 | 1 | 0 | — |
| I18 | 3 | 0 | — |
| I19 | 90 | 0 | — |
| I20 | 18 | 0 | — |

### Violações críticas por caso

- **p3_s03_b02**: I4: posição retirada permaneceu com autoridade. “chance de branca na primeira retirada era 1/2” → ACTIVE. [evidências e decisões](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b02.json).
- **p3_s03_b04**: I4: posição retirada permaneceu com autoridade. “indicação para continuar era o conjunto {1,4}” → ACTIVE. [evidências e decisões](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b04.json).
- **p3_s03_b05**: I4: posição retirada permaneceu com autoridade. “probabilidade da segunda branca ficou anotada como 7/36” → ACTIVE. [evidências e decisões](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b05.json).
- **p3_s03_b08**: I4: posição retirada permaneceu com autoridade. “quatro brancas na base” → ACTIVE. [evidências e decisões](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b08.json).
- **p3_s03_c07**: I2: conteúdo não adotado ganhou autoridade negativa. “segunda branca teria probabilidade 1” → ACTIVE. [evidências e decisões](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c07.json).
- **p3_s03_d02**: I6: ambiguidade virou hard veto. “Nuno escreveu 1/2” → ACTIVE. [evidências e decisões](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d02.json).
- **p3_s03_d03**: I6: ambiguidade virou hard veto. “primeira_branca: 1/2” → ACTIVE. [evidências e decisões](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d03.json).
- **p3_s03_e01**: I2: conteúdo não adotado ganhou autoridade negativa. “nota de uma colega dizia primeira_branca: 7/12” → ACTIVE. [evidências e decisões](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e01.json).
- **p3_s03_e02**: I14: posição anterior correta não foi retirada conforme a revisão. “Eu adotava segunda_branca: 11/36” → ACTIVE. [evidências e decisões](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e02.json).

A descrição literal de I1–I20 está em [arquitetura congelada, seção 7](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_UNIFIED_DISCOURSE_VETO_ARCHITECTURE_01.md). Os detalhes de cada oportunidade que falhou constam em `audits/<case_id>.json`, campo `invariants`; não se conclui ausência de falha de segurança a partir de zero bypass interno.

## 10. Authority audit e produtores

Guard-generated awards: **0**. Awards sem checker/verification_id/original_fact: **0**. Violações de política paralela/autenticidade em I12: **0**. Todos os vetos aplicados têm cadeia source → decisão discursiva → checker → policy receipt → reconciliation → efeito no award, preservada em `veto_chains`.

| Produtor de hard veto | Receipts aplicáveis |
| --- | ---: |
| positive_checker | 11 |
| native_checker | 11 |

Há 16 receipts de autoridade negativa indevida em 8 casos quando confrontados com os estados prévios da fonte. Desses casos, 5 bloqueiam parcelas legitimamente pontuáveis (9 pontos); C07/D02/D03 exercem veto indevido sobre obrigações que já não tinham crédito esperado, sem perda adicional de parcela. Assim, 5 false vetoes com impacto em award não significam apenas 5 falhas de autoridade. Dos 19 alvos AMBIGUOUS, 16 tiveram alinhamento único e visibilidade no trace; 14 ficaram visíveis sem autoridade. Os três restantes pertencem a fallbacks. [Contagens e receipts por caso](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/authority_visibility_audit.json).

O segundo produtor determinístico continua passando pela política central. Quando ele e o positivo refutam uma posição retirada mal rotulada ACTIVE, ambos podem fornecer receipts autênticos e ainda assim produzir **falso veto end-to-end**. Autenticidade de receipt não demonstra que a adoção discursiva esteja correta. Igualmente, um checker pode provar um número de um claim não adotado; isso não autoriza crédito desse claim.

## 11. Fallback e execução formal

ALL40 inclui 3 fallback(s); SEMANTIC_SUCCESS_ONLY inclui 37 casos. Fallback não mede qualidade do extractor. Technical uncertainty: 0 em ALL40 e 0 no subconjunto sem fallback.

- `p3_s03_c03`: `ValueError:extractor_incomplete_or_refused`; efetivo `TME_SEMANTIC_FORMAL_NATIVE_FALLBACK`; score=0; API calls=1; nenhuma nova tentativa. [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_c03.json).
- `p3_s03_d01`: `ValueError:extractor_incomplete_or_refused`; efetivo `TME_SEMANTIC_FORMAL_NATIVE_FALLBACK`; score=0; API calls=1; nenhuma nova tentativa. [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_d01.json).
- `p3_s03_d06`: `ValueError:extractor_incomplete_or_refused`; efetivo `TME_SEMANTIC_FORMAL_NATIVE_FALLBACK`; score=0; API calls=1; nenhuma nova tentativa. [artefato](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_d06.json).

Tentativas formais reais por status: `{'FORMAL_VERIFIED': 1}`. Status de verificações: `{'DETERMINISTIC_VERIFIED': 15, 'DETERMINISTIC_FAILED': 7, 'CONTEXT_REJECTED': 55, 'COMPOSITE_VERIFIED': 9, 'COMPOSITE_INCOMPLETE': 7, 'FORMAL_VERIFIED': 1, 'COMPOSITE_FAILED': 4}`. FORMAL_NOT_ATTEMPTED e ausência de witness não foram convertidos em refutação. API calls declaradas pelo extractor: 40; respostas completas: 37.

## 12. Métricas secundárias de score e obrigações

Exact é concordância com a expectativa construída; não acurácia populacional. Precision/recall são microagregadas por obrigação elegível. Precision com denominador zero é indefinida. Os números abaixo não substituem a auditoria de segurança.

| Métrica | Current ALL40 | Semantic ALL40 | Semantic success only |
| --- | ---: | ---: | ---: |
| N | 40 | 40 | 37 |
| Total | 0.0 | 34.0 | 34.0 |
| Expected total | 71.0 | 71.0 | 68.0 |
| Exact (casos) | 10 | 22 | 21 |
| MAE | 1.7750 | 1.0250 | 1.0270 |
| Bias | -1.7750 | -0.9250 | -0.9189 |
| Over-score casos | 0 | 1 | 1 |
| Over-score pontos | 0.0 | 2.0 | 2.0 |
| Under-score casos | 30 | 17 | 15 |
| Under-score pontos | 71.0 | 39.0 | 36.0 |
| Obligation TP | 0 | 17 | 17 |
| Obligation FP | 0 | 1 | 1 |
| Obligation FN | 39 | 22 | 20 |
| Obligation precision | indefinida | 0.9444 | 0.9444 |
| Obligation recall | 0.0 | 0.4359 | 0.4595 |

[Métricas completas incluindo Current no subconjunto semantic-success](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/metrics.json); [comparação por caso e obrigações](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/case_analysis.json).

## 13. Comparação pareada

Score maior: Semantic **16**, Current **0**, empate **24**. Esses números significam maior nota, não maior correção. Menor erro absoluto contra a expectativa congelada: Semantic **15**, Current **1**, empate **24**. Total Current=0; Semantic=34; delta=+34.

Current recebeu zero nos 40 casos. Os artefatos preservados mostram ausência de facts/awards positivos nessa rodada de prosa e rótulos inseridos em frases; isso é limitação de extração/normalização do comparador, não justificativa para aceitar crédito Semantic. Os casos não foram reescritos para elevar o baseline nem para melhorar Semantic depois de observados.

## 14. Análise causal das divergências

- **p3_s03_a03**: 1 divergência(s) de estado/alinhamento; rejeições: discourse_ambiguous (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a03.json).
- **p3_s03_a05**: 1 divergência(s) de estado/alinhamento; rejeições: discourse_ambiguous (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a05.json).
- **p3_s03_a06**: 1 divergência(s) de estado/alinhamento; rejeições: discourse_ambiguous (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a06.json).
- **p3_s03_b01**: 1 divergência(s) de estado/alinhamento; rejeições: white_count_not_bound_to_written_quantity (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b01.json).
- **p3_s03_b02**: 1 divergência(s) de estado/alinhamento; bloqueio por receipt: a.first_white_probability; nenhuma rejeição de mapping nos alvos alinhados; verificar estados, omissões e sufficiency no trace. [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b02.json).
- **p3_s03_b03**: 1 divergência(s) de estado/alinhamento; rejeições: subject_not_uniquely_bound_to_source_clause (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b03.json).
- **p3_s03_b04**: 1 divergência(s) de estado/alinhamento; bloqueio por receipt: c.continue_compartments; nenhuma rejeição de mapping nos alvos alinhados; verificar estados, omissões e sufficiency no trace. [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b04.json).
- **p3_s03_b05**: 1 divergência(s) de estado/alinhamento; bloqueio por receipt: b.second_white_probability; nenhuma rejeição de mapping nos alvos alinhados; verificar estados, omissões e sufficiency no trace. [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b05.json).
- **p3_s03_b06**: 1 divergência(s) de estado/alinhamento; rejeições: subject_not_uniquely_bound_to_source_clause (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b06.json).
- **p3_s03_b07**: 2 divergência(s) de estado/alinhamento; nenhuma rejeição de mapping nos alvos alinhados; verificar estados, omissões e sufficiency no trace. [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b07.json).
- **p3_s03_b08**: 1 divergência(s) de estado/alinhamento; bloqueio por receipt: a.bottom_white_count; rejeições: white_count_not_bound_to_written_quantity (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b08.json).
- **p3_s03_c01**: 1 divergência(s) de estado/alinhamento; rejeições: discourse_non_adopted (2). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c01.json).
- **p3_s03_c02**: 1 divergência(s) de estado/alinhamento; rejeições: nonasserted_or_unattributed_context (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c02.json).
- **p3_s03_c03**: fallback; 2 divergência(s) de estado/alinhamento; nenhuma rejeição de mapping nos alvos alinhados; verificar estados, omissões e sufficiency no trace. [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c03.json).
- **p3_s03_c04**: 1 divergência(s) de estado/alinhamento; rejeições: subject_not_uniquely_bound_to_source_clause (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c04.json).
- **p3_s03_c05**: 1 divergência(s) de estado/alinhamento; rejeições: subject_not_uniquely_bound_to_source_clause (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c05.json).
- **p3_s03_c06**: 1 divergência(s) de estado/alinhamento; rejeições: white_count_not_bound_to_written_quantity (2). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c06.json).
- **p3_s03_c07**: 1 divergência(s) de estado/alinhamento; nenhuma rejeição de mapping nos alvos alinhados; verificar estados, omissões e sufficiency no trace. [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_c07.json).
- **p3_s03_d01**: fallback; 2 divergência(s) de estado/alinhamento; nenhuma rejeição de mapping nos alvos alinhados; verificar estados, omissões e sufficiency no trace. [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d01.json).
- **p3_s03_d02**: 2 divergência(s) de estado/alinhamento; rejeições: white_count_not_bound_to_written_quantity (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d02.json).
- **p3_s03_d03**: 2 divergência(s) de estado/alinhamento; nenhuma rejeição de mapping nos alvos alinhados; verificar estados, omissões e sufficiency no trace. [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d03.json).
- **p3_s03_d04**: 2 divergência(s) de estado/alinhamento; rejeições: subject_not_uniquely_bound_to_source_clause (2). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d04.json).
- **p3_s03_d06**: fallback; 2 divergência(s) de estado/alinhamento; nenhuma rejeição de mapping nos alvos alinhados; verificar estados, omissões e sufficiency no trace. [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d06.json).
- **p3_s03_d07**: 2 divergência(s) de estado/alinhamento; rejeições: unsupported_checker_payload (2). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d07.json).
- **p3_s03_d08**: 2 divergência(s) de estado/alinhamento; rejeições: set_payload_omits_source_members (2), color_count_not_bound_to_written_quantity (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_d08.json).
- **p3_s03_e01**: 1 divergência(s) de estado/alinhamento; bloqueio por receipt: a.first_white_probability; rejeições: white_count_not_bound_to_written_quantity (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e01.json).
- **p3_s03_e02**: 1 divergência(s) de estado/alinhamento; rejeições: subject_not_uniquely_bound_to_source_clause (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e02.json).
- **p3_s03_e03**: 1 divergência(s) de estado/alinhamento; rejeições: white_count_not_bound_to_written_quantity (2). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e03.json).
- **p3_s03_e04**: 2 divergência(s) de estado/alinhamento; rejeições: white_count_not_bound_to_written_quantity (1), subject_not_uniquely_bound_to_source_clause (2). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e04.json).
- **p3_s03_e05**: 2 divergência(s) de estado/alinhamento; rejeições: white_count_not_bound_to_written_quantity (1), subject_not_uniquely_bound_to_source_clause (2). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e05.json).
- **p3_s03_e08**: 1 divergência(s) de estado/alinhamento; rejeições: color_not_written (1), subject_not_uniquely_bound_to_source_clause (4), color_count_not_bound_to_written_quantity (1). [proveniência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e08.json).

B07 emitiu a expressão antiga `1/6`, mas asserted_content ocorre duas vezes no envelope: o resolver a marcou AMBIGUOUS por `ambiguous_assertion_location`. Os dois alvos antigos ficaram sem alinhamento único na métrica; não houve omissão literal dessa expressão.

A05 exemplifica perda de negativo ativo por classificação `unmapped`/AMBIGUOUS; B02/B04/B05 exemplificam marcador de revisão não reconhecido, com valor antigo ainda refutável; C01 exemplifica a palavra “hipótese” no próprio encerramento de hipótese contaminando a assertiva independente. Essas são causas distintas. Nenhuma foi corrigida nesta tarefa. Claims omitidos, payload incompleto ou falta de componente não foram rotulados como refutação formal.

## 15. Limitações

- Uma rodada por fonte, sem estimativa de variabilidade entre chamadas. Resultados são locais ao modelo, SHA e configuração registrados.
- O campo auxiliar `mathematically_correct` verifica valor canônico por subject, não toda a relação cor–contagem. Em A07, `contagem_2=3` coincide com o número canônico, mas a fonte o atribui à preta (que ocorre duas vezes): o rationale e a obrigação composta congelados corretamente exigem zero crédito. Esse limite do auditor prévio é preservado, sem corrigir os arquivos após congelamento.
- Expectativas por construção não são consenso humano externo. D02 declara referência pronominal não resolvida, mas os nomes podem sugerir uma leitura por gênero; isso é uma limitação de naturalidade/ambiguidade do caso. A expectativa permaneceu intacta e não foi reclassificada após resultados. O falso crédito inequívoco de A05 independe dessa limitação.
- Anotações de D05 cobrem dois possíveis subjects no mesmo trecho; a métrica conta alvos contratuais, não palavras distintas. C03 contém dado do enunciado sem obrigação pontuável, que pode ser omitido; sua omissão aparece como cobertura de estado ausente, nunca como falso crédito.
- Auditoria determinística prévia verifica matemática e coerência de contratos, não implementa um segundo entendimento semântico geral. A revisão não ajustou expectativas aos limites reais de regex ou payload do sistema avaliado.
- Falta de representação e omissão impedem algumas refutações; zero awards sem checker não assegura sozinho zero falso crédito contextual.
- Nenhuma métrica é de holdout externo, e estes 40 textos não poderão ser usados como validação independente de correções futuras.

## 16. Veredito

**P3_SAFETY_FAILURE.** Há falso crédito material, suficiente por si só para reprovar o critério de segurança. As falhas de retratação, ambiguidade e localidade reforçam o diagnóstico. O fluxo central de receipts pode funcionar internamente e ainda receber estados discursivos incorretos; o contrato de segurança exige as duas camadas.

## 17. Status geral do P3 e próximos passos

Não promover para `P3_SEMANTIC_ADVANTAGE_CONFIRMED`. DEV02, robustness observado e a regressão unificada continuam sendo evidências históricas de resgate/correção nos respectivos conjuntos. Safety02 conserva seus fracassos documentados; Safety03 demonstra que eliminá-los em replay observado não bastou para estabelecer generalização discursiva. Nada desses registros foi apagado ou reescrito.

Recomendação diagnóstica: revisar em tarefa futura a preservação de negativos ativos não representáveis, o reconhecimento de retirada/substituição e o escopo de não adoção/ambiguidade; exigir nova avaliação inédita após qualquer mudança. Este relatório não implementa fix, não altera expectativas e não autoriza usar Safety03 como teste independente pós-fix.

Comandos efetivamente executados uma vez por modo:

```bash
cd ~/Documents/confia-lean-auditor-tme-semantic-formal-p3
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app:. CONFIA_TME_SEMANTIC_ENABLED=0 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python scripts/evaluation/run_tme_semantic_formal_p3.py --mode tme_current --dataset /private/tmp/p3-safety03/frozen/sources.json --ids-file /private/tmp/p3-safety03/frozen/ids.json --output-dir artifacts/evaluations/tme_p3_semantic_safety_03/tme_current --model gpt-6.1-sol --reasoning-effort medium
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app:. CONFIA_TME_SEMANTIC_ENABLED=0 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python scripts/evaluation/run_tme_semantic_formal_p3.py --mode tme_semantic_formal --dataset /private/tmp/p3-safety03/frozen/sources.json --ids-file /private/tmp/p3-safety03/frozen/ids.json --output-dir artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal --model gpt-6.1-sol --reasoning-effort medium
```

Integridade: 269 arquivos existentes conferidos, 0 alterados. HEAD final `6fb07d4d15626e27b7c759a4e32f9cb3b415d2ea`. Novos arquivos versionáveis: cinco JSON do Safety03 e este relatório; nenhum stage/commit. Artefatos completos em [artifacts/evaluations/tme_p3_semantic_safety_03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/metrics.json).

**P3_SAFETY_FAILURE**
