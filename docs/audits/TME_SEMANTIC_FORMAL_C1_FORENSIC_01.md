# C1 — auditoria forense somente-leitura dos pilotos P1

Data: **2026-11-04** (America/Fortaleza). Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1`.

**Conclusão:** as cinco regressões são explicadas por três mecanismos verificáveis nos artefatos: rejeição de obrigações não formais por uma sugestão FORMAL compartilhada (3 pontos), vínculo incorreto do literal 137 a uma obrigação (1 ponto) e ausência de segmentação de cadeias de igualdades no adapter (9 pontos). Total: **13 pontos**, de 69 para 56 na soma dos 21 casos. Não há falha Lean, conflito ou erro técnico responsável por essas perdas. As causas são demonstradas antes das recomendações, ao final.

## 1. Escopo, procedência e método

Leitura dos 42 resultados de caso, dois summaries e dois manifests dos pilotos explicitamente indicados; inspeção estática dos módulos envolvidos. Nenhum código foi alterado ou executado para reavaliar alunos. Não houve novo piloto, teste, chamada LLM, chamada Lean, consulta a gold, leitura do holdout ou commit. A única gravação no repositório é este relatório. Scripts auxiliares de agregação e hashes ficam em `/private/tmp/confia-c1-forensic/`.

O Git estava limpo no início. HEAD atual e SHA registrado em todos os casos: **`6fe808fa693b7e0d662dd49c498e6b575dd9d47f`**. Esse é o código dos pilotos fornecidos, distinto do SHA-base histórico da implementação. Nenhuma mudança de HEAD foi feita nesta auditoria. Ambos os pilotos registram modelo `gpt-6.1-sol`, esforço `medium`; não o modelo sugerido no relatório de preparação.

Os 21 pares têm fontes e hashes de fonte idênticos e configurações idênticas entre modos, incluindo pauta, registry, extractor e código. Os hashes dos módulos experimentais, do código reutilizado e do runner foram conferidos contra os arquivos atuais. Assim, as referências de linha abaixo correspondem ao código que gerou os artefatos. Os resultados do baseline são comparador de comportamento, não gold ou julgamento externo.

- [pilot_current_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01); [summary.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01/summary.json); [run_manifest.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01/run_manifest.json).

- [pilot_semantic_formal_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01); [summary.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/summary.json); [run_manifest.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/run_manifest.json).

Métricas recompostas dos JSON por caso, sem reexecução:

| métrica | TME_CURRENT | TME_SEMANTIC_FORMAL |
|---|---|---|
| cases | 21 | 21 |
| numeric_scores | 21 | 21 |
| fallbacks | 0 | 0 |
| claims_extracted | 0 | 54 |
| formal_routes | 5 | 10 |
| deterministic_routes | 81 | 83 |
| semantic_routes | 0 | 0 |
| formal_verified | 4 | 4 |
| formal_refuted | 1 | 1 |
| formal_unproved | 0 | 5 |
| formal_error | 0 | 0 |
| deterministic_verified | 69 | 56 |
| deterministic_failed | 12 | 27 |
| context_rejected | 0 | 3 |
| conflicts | 0 | 0 |
| technical_uncertainty_cases | 0 | 0 |
| review_recommended_cases | 20 | 21 |
| mean_score | 3.2857142857142856 | 2.6666666666666665 |

**16 empates, 5 regressões, 0 melhoras.** As métricas de rota contam linhas de resultado, não subprocessos Lean nem claims únicos. Há 54 evidências extraídas, 93 linhas de resultado com rota efetiva e 3 rejeições de mapeamento. Os dois pilotos têm cinco resultados com checker Lean real: quatro verificados e um refutado.

## 2. As cinco regressões: cadeia completa e primeira divergência

As tabelas de evidência, payload e decisão se relacionam por `evidence_id` e `obligation_id`; juntas explicitam `source_span → normalized_claim → obligation → route → checker → status → sufficiency → award`. Não se atribuem pontos independentes a obrigações que compartilham uma regra `all_of`.

### a_complete: 3 → 0

Fontes: [pilot_current_01/a_complete.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01/a_complete.json); [pilot_semantic_formal_01/a_complete.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/a_complete.json).

```text
(a)
731-137=594
```

**Primeira divergência:** o extractor associa uma única sugestão `FORMAL` às quatro obrigações do claim. No mapper/router, `invented_formal_route` rejeita as três obrigações não formais. Classificação primária **ROUTER_ERROR**, com gatilho **FORMAL_OVERROUTING** na sugestão e acoplamento de uma rota por evidência a várias obrigações. O nome `CONTEXT_REJECTED` é enganoso aqui: não houve hipótese, negação ou abandono.

A ponte matemática C1 efetivamente contém fatos verificados para identificação, montagem e resultado. Contudo, `mathematical_verification` filtra os dois primeiros porque seus pares evidence/obligation não foram aceitos. Lean prova `731−137=594`; AwardGate aceita isoladamente `a.result_594`, mas a faixa `a.full` exige também identificação/montagem. Nem `a.identification` sobrevive. Os 3 pontos são perdidos conjuntamente em G1. Não é `FORMAL_UNPROVED`, falha Lean ou regra excessiva de suficiência.

#### Evidências e sugestões do extractor

| evidence_id | source_span literal | normalized_claim | claim_type | obligation mapping sugerido | suggested route | contexto declarado |
|---|---|---|---|---|---|---|
| `E002:claim:dd761853adfaa954a7b6` | `731-137=594` | `731-137=594` | `expression` | `["a.identifies_137","a.constructs_subtraction","a.result_594","a.arithmetic_error_only"]` | `FORMAL` | `{"assertion_status":"asserted","polarity":"positive","scope":"final_conclusion","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |

#### Payload e representação efetivamente entregues

A coluna “payload” transcreve os campos matemáticos efetivos de `SemanticClaimCandidate.normalized_payload`; o lote de entrada de `verify_tme2_p1_digital` contém o `MathClaimRecord` identificado na coluna seguinte. Os campos completos, incluindo árvores canônicas, estão em `mathematical_bridge.auditor.records` no JSON citado. `null` abaixo significa ausência real de forma canônica, não ausência de inspeção. Coordenadas do registro são relativas à fonte digital reenquadrada; o span original permanece na tabela acima.

| evidence_id | payload da projeção | registro no lote | representação canônica útil | resultado da projeção | entrada no checker de item |
|---|---|---|---|---|---|
| `E002:claim:dd761853adfaa954a7b6` | `{"subject":"expression","expression":"731-137=594","item_id":"a"}` | `semantic:311acc1e0151b94273f70c12` / `math_relation` | `{"expression":"731-137=594"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_a |

#### Comparação por obrigação e decisão de crédito

“Apoio” é o status da ponte; “elegível” é a decisão do AwardGate. Pontos pertencem a blocos/faixas da pauta: valores repetidos identificam o mesmo bloco e **não devem ser somados por obrigação**. G1…G8 são reconciliados na tabela de perdas adiante. Nenhum desses casos contém conflitos.

| rubric item | obligation_id | TME_CURRENT: apoio / award | C1: award / pontos | evidence_id | effective route | verification status | sufficiency status | context/mapping status | conflict status | award decision | reason / rejection reason | points perdidos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a | `a.identifies_137` | supported; a.full=3 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | `E002:claim:dd761853adfaa954a7b6` | nenhuma | CONTEXT_REJECTED | False / contexto | rejeitado: invented_formal_route / False | nenhum | `no_sufficient_verified_evidence` | invented_formal_route | G1: 3 pt conjuntos (não somar linhas) |
| a | `a.constructs_subtraction` | supported; a.full=3 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | `E002:claim:dd761853adfaa954a7b6` | nenhuma | CONTEXT_REJECTED | False / contexto | rejeitado: invented_formal_route / False | nenhum | `no_sufficient_verified_evidence` | invented_formal_route | G1: 3 pt conjuntos (não somar linhas) |
| a | `a.result_594` | supported; a.full=3 pt (bloco) | elegível; 0 pt; nenhum bloco pago | `E002:claim:dd761853adfaa954a7b6` | FORMAL | FORMAL_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | G1: 3 pt conjuntos (não somar linhas) |
| a | `a.arithmetic_error_only` | indeterminate; 0 pt; nenhum bloco pago | não elegível; 0 pt; nenhum bloco pago | `E002:claim:dd761853adfaa954a7b6` | nenhuma | CONTEXT_REJECTED | False / contexto | rejeitado: invented_formal_route / False | nenhum | `no_sufficient_verified_evidence` | invented_formal_route | 0 |

Itens sem fonte neste caso: b, c, d. Todas as suas obrigações têm 0 ponto nas duas linhas, sem candidato C1, sem rota/checker e sem perda incremental. A tabela concentra o item efetivamente respondido.

#### Evidência do baseline e fatos C1 que delimitam a causa

| obrigação | representação usada no baseline | status baseline |
|---|---|---|
| `a.identifies_137` | `{"record_id":"student:generic_math_4_15_relation","source_span":"731-137=594","payload":{"expression":"731-137=594"}}` | DETERMINISTIC_VERIFIED |
| `a.constructs_subtraction` | `{"record_id":"student:generic_math_4_15_relation","source_span":"731-137=594","payload":{"expression":"731-137=594"}}` | DETERMINISTIC_VERIFIED |
| `a.result_594` | `{"record_id":"student:generic_math_4_15_relation","source_span":"731-137=594","payload":{"expression":"731-137=594"}}`<br>`{"record_id":"student:tme2-arithmetic-66dd0eb9dcf88b45","source_span":"731-137=594","payload":{"left_expr":"731-137","right_expr":"594"}}` | FORMAL_VERIFIED |

Fatos preservados na ponte matemática C1, antes do filtro por candidato:

| fato realmente presente na ponte C1 | status | source_claim_ids |
|---|---|---|
| `a.inverted_number_137` | verified | `["semantic:311acc1e0151b94273f70c12"]` |
| `a.subtraction_731_137` | verified | `["semantic:311acc1e0151b94273f70c12"]` |
| `a.result_594` | verified | `["semantic:311acc1e0151b94273f70c12","student:tme2-arithmetic-3b00ecb6871d8a21"]` |

### a_only_inverse: 1 → 0

Fontes: [pilot_current_01/a_only_inverse.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01/a_only_inverse.json); [pilot_semantic_formal_01/a_only_inverse.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/a_only_inverse.json).

```text
(a)
137
```

**Primeira divergência:** `extractor.raw_output` associa o literal correto `137` apenas a `a.result_594`, omitindo `a.identifies_137`. Classificação primária **OBLIGATION_MAPPING_ERROR**, originada na sugestão do extractor e não recuperada pelo mapper; consequência **BASELINE_EVIDENCE_NOT_REPRESENTED** no conjunto autorizado. Não houve alteração do número.

A própria ponte matemática C1 contém `a.inverted_number_137=verified`, assim como o baseline. O filtro de candidatos elimina esse fato da saída de verificação porque a obrigação correta não foi sugerida. O router força FORMAL para `a.result_594`; nenhum fato dessa obrigação existe para `137`, e o adapter sintetiza `FORMAL_UNPROVED`. O ponto perdido é o da identificação, não um ponto antes concedido por Lean.

#### Evidências e sugestões do extractor

| evidence_id | source_span literal | normalized_claim | claim_type | obligation mapping sugerido | suggested route | contexto declarado |
|---|---|---|---|---|---|---|
| `E002:claim:9b82fb4a1ffd952c6aa2` | `137` | `137` | `expression` | `["a.result_594"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"final_conclusion","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |

#### Payload e representação efetivamente entregues

A coluna “payload” transcreve os campos matemáticos efetivos de `SemanticClaimCandidate.normalized_payload`; o lote de entrada de `verify_tme2_p1_digital` contém o `MathClaimRecord` identificado na coluna seguinte. Os campos completos, incluindo árvores canônicas, estão em `mathematical_bridge.auditor.records` no JSON citado. `null` abaixo significa ausência real de forma canônica, não ausência de inspeção. Coordenadas do registro são relativas à fonte digital reenquadrada; o span original permanece na tabela acima.

| evidence_id | payload da projeção | registro no lote | representação canônica útil | resultado da projeção | entrada no checker de item |
|---|---|---|---|---|---|
| `E002:claim:9b82fb4a1ffd952c6aa2` | `{"subject":"expression","expression":"137","item_id":"a"}` | `semantic:5b174a009e76379b0aae2c4b` / `math_literal` | `{"expression":"137"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_a |

#### Comparação por obrigação e decisão de crédito

“Apoio” é o status da ponte; “elegível” é a decisão do AwardGate. Pontos pertencem a blocos/faixas da pauta: valores repetidos identificam o mesmo bloco e **não devem ser somados por obrigação**. G1…G8 são reconciliados na tabela de perdas adiante. Nenhum desses casos contém conflitos.

| rubric item | obligation_id | TME_CURRENT: apoio / award | C1: award / pontos | evidence_id | effective route | verification status | sufficiency status | context/mapping status | conflict status | award decision | reason / rejection reason | points perdidos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a | `a.identifies_137` | supported; a.identification=1 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | — | nenhuma | sem resultado | não avaliada | sem candidato (não testado) | nenhum | `no_sufficient_verified_evidence` | ausência de candidato/resultado | G2: 1 pt |
| a | `a.constructs_subtraction` | indeterminate; 0 pt; nenhum bloco pago | não elegível; 0 pt; nenhum bloco pago | — | nenhuma | sem resultado | não avaliada | sem candidato (não testado) | nenhum | `no_sufficient_verified_evidence` | ausência de candidato/resultado | 0 |
| a | `a.result_594` | indeterminate; 0 pt; nenhum bloco pago | não elegível; 0 pt; nenhum bloco pago | `E002:claim:9b82fb4a1ffd952c6aa2` | FORMAL | FORMAL_UNPROVED | False / missing_checker_fact | aceito / True | nenhum | `no_sufficient_verified_evidence` | no_existing_fact_for_selected_claim | 0 |
| a | `a.arithmetic_error_only` | indeterminate; 0 pt; nenhum bloco pago | não elegível; 0 pt; nenhum bloco pago | — | nenhuma | sem resultado | não avaliada | sem candidato (não testado) | nenhum | `no_sufficient_verified_evidence` | ausência de candidato/resultado | 0 |

Itens sem fonte neste caso: b, c, d. Todas as suas obrigações têm 0 ponto nas duas linhas, sem candidato C1, sem rota/checker e sem perda incremental. A tabela concentra o item efetivamente respondido.

#### Evidência do baseline e fatos C1 que delimitam a causa

| obrigação | representação usada no baseline | status baseline |
|---|---|---|
| `a.identifies_137` | `{"record_id":"native:digital-literal.v1:4:7","source_span":"137","payload":{"kind":"expression","tree":{"kind":"rational","value":"137","args":[]},"affine":[["","137"]],"relation":null,"variables":[],"schema_version":"canonical-math-v1","domain":"real_total"}}` | DETERMINISTIC_VERIFIED |
| `a.result_594` | sem fato | sem resultado |

Fatos preservados na ponte matemática C1, antes do filtro por candidato:

| fato realmente presente na ponte C1 | status | source_claim_ids |
|---|---|---|
| `a.inverted_number_137` | verified | `["semantic:5b174a009e76379b0aae2c4b"]` |

### b_complete: 5 → 2

Fontes: [pilot_current_01/b_complete.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01/b_complete.json); [pilot_semantic_formal_01/b_complete.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/b_complete.json).

```text
(b)
r=100c+10b+a.
(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c).
```

**Primeira divergência:** o baseline segmenta a cadeia em igualdades adjacentes; o C1 mantém a cadeia inteira em um único `normalized_payload.expression`. O extractor conserva o significado e os passos escritos, mas `ClaimProjection` cria um único candidato, sem a segmentação realizada por `generic_math.candidate_spans`. Classificação primária **CHECKER_REPRESENTATION_MISMATCH**, localizada no **adapter**; não há evidência de erro algébrico na normalização.

`convert_candidate` produz `math_semantic_candidate`, `canonical_form=null`, `attributable=false`, `canonicalized=false`, `reason=unsupported_representation`, com grounding literal válido e `context_rejected=false`. O verificador recebe o registro no lote, mas o exclui antes de `_check_b`. Não há fato para subtração/cancelamento/fatoração. O C1 emite três `DETERMINISTIC_FAILED` sem refutação matemática, e AwardGate corretamente retém os blocos de 2+1 pontos. A representação do invertido continua valendo 2 pontos.

#### Evidências e sugestões do extractor

| evidence_id | source_span literal | normalized_claim | claim_type | obligation mapping sugerido | suggested route | contexto declarado |
|---|---|---|---|---|---|---|
| `E002:claim:a96eba8aae15f4fab3be` | `r=100c+10b+a.` | `r=100c+10b+a` | `expression` | `["b.reversed_number"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E003:claim:4d5362e65b3d6dd66ced` | `(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c).` | `(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c)` | `expression` | `["b.subtraction","b.middle_cancellation","b.factorization"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |

#### Payload e representação efetivamente entregues

A coluna “payload” transcreve os campos matemáticos efetivos de `SemanticClaimCandidate.normalized_payload`; o lote de entrada de `verify_tme2_p1_digital` contém o `MathClaimRecord` identificado na coluna seguinte. Os campos completos, incluindo árvores canônicas, estão em `mathematical_bridge.auditor.records` no JSON citado. `null` abaixo significa ausência real de forma canônica, não ausência de inspeção. Coordenadas do registro são relativas à fonte digital reenquadrada; o span original permanece na tabela acima.

| evidence_id | payload da projeção | registro no lote | representação canônica útil | resultado da projeção | entrada no checker de item |
|---|---|---|---|---|---|
| `E002:claim:a96eba8aae15f4fab3be` | `{"subject":"expression","expression":"r=100c+10b+a","item_id":"b"}` | `semantic:aca937aeea7d56181811ec4f` / `math_relation` | `{"expression":"r=100c+10b+a"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_b |
| `E003:claim:4d5362e65b3d6dd66ced` | `{"subject":"expression","expression":"(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c)","item_id":"b"}` | `semantic:a7d6020cadaf6eb0a98c13bd` / `math_semantic_candidate` | `null` | `{"grounding":"grounded","attributable":false,"canonicalized":false,"context_rejected":false,"reason":"unsupported_representation"}` | excluído antes de _check_b |

#### Comparação por obrigação e decisão de crédito

“Apoio” é o status da ponte; “elegível” é a decisão do AwardGate. Pontos pertencem a blocos/faixas da pauta: valores repetidos identificam o mesmo bloco e **não devem ser somados por obrigação**. G1…G8 são reconciliados na tabela de perdas adiante. Nenhum desses casos contém conflitos.

| rubric item | obligation_id | TME_CURRENT: apoio / award | C1: award / pontos | evidence_id | effective route | verification status | sufficiency status | context/mapping status | conflict status | award decision | reason / rejection reason | points perdidos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| b | `b.reversed_number` | supported; b.reverse=2 pt (bloco) | elegível; b.reverse=2 pt (bloco) | `E002:claim:a96eba8aae15f4fab3be` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| b | `b.subtraction` | supported; b.subtract_cancel=2 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | `E003:claim:4d5362e65b3d6dd66ced` | DETERMINISTIC | DETERMINISTIC_FAILED | False / missing_checker_fact | aceito / True | nenhum | `no_sufficient_verified_evidence` | no_existing_fact_for_selected_claim | G3: 2 pt conjuntos |
| b | `b.middle_cancellation` | supported; b.subtract_cancel=2 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | `E003:claim:4d5362e65b3d6dd66ced` | DETERMINISTIC | DETERMINISTIC_FAILED | False / missing_checker_fact | aceito / True | nenhum | `no_sufficient_verified_evidence` | no_existing_fact_for_selected_claim | G3: 2 pt conjuntos |
| b | `b.factorization` | supported; b.simplify=1 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | `E003:claim:4d5362e65b3d6dd66ced` | DETERMINISTIC | DETERMINISTIC_FAILED | False / missing_checker_fact | aceito / True | nenhum | `no_sufficient_verified_evidence` | no_existing_fact_for_selected_claim | G4: 1 pt |

Itens sem fonte neste caso: a, c, d. Todas as suas obrigações têm 0 ponto nas duas linhas, sem candidato C1, sem rota/checker e sem perda incremental. A tabela concentra o item efetivamente respondido.

#### Evidência do baseline e fatos C1 que delimitam a causa

| obrigação | representação usada no baseline | status baseline |
|---|---|---|
| `b.reversed_number` | `{"record_id":"student:generic_math_4_16_relation","source_span":"r=100c+10b+a","payload":{"expression":"r=100c+10b+a"}}` | DETERMINISTIC_VERIFIED |
| `b.subtraction` | `{"record_id":"student:generic_math_18_51_relation","source_span":"(100a+10b+c)-(100c+10b+a)=99a-99c","payload":{"expression":"(100a+10b+c)-(100c+10b+a)=99a-99c"}}` | DETERMINISTIC_VERIFIED |
| `b.middle_cancellation` | `{"record_id":"student:generic_math_18_51_relation","source_span":"(100a+10b+c)-(100c+10b+a)=99a-99c","payload":{"expression":"(100a+10b+c)-(100c+10b+a)=99a-99c"}}` | DETERMINISTIC_VERIFIED |
| `b.factorization` | `{"record_id":"student:generic_math_44_59_relation","source_span":"99a-99c=99(a-c)","payload":{"expression":"99a-99c=99(a-c)"}}` | DETERMINISTIC_VERIFIED |

### b_equivalent_algebra: 5 → 2

Fontes: [pilot_current_01/b_equivalent_algebra.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01/b_equivalent_algebra.json); [pilot_semantic_formal_01/b_equivalent_algebra.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/b_equivalent_algebra.json).

```text
(b)
r=a+10*b+100*c.
(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c=-99*(c-a).
```

**Primeira divergência:** o baseline segmenta a cadeia em igualdades adjacentes; o C1 mantém a cadeia inteira em um único `normalized_payload.expression`. O extractor conserva o significado e os passos escritos, mas `ClaimProjection` cria um único candidato, sem a segmentação realizada por `generic_math.candidate_spans`. Classificação primária **CHECKER_REPRESENTATION_MISMATCH**, localizada no **adapter**; não há evidência de erro algébrico na normalização.

`convert_candidate` produz `math_semantic_candidate`, `canonical_form=null`, `attributable=false`, `canonicalized=false`, `reason=unsupported_representation`, com grounding literal válido e `context_rejected=false`. O verificador recebe o registro no lote, mas o exclui antes de `_check_b`. Não há fato para subtração/cancelamento/fatoração. O C1 emite três `DETERMINISTIC_FAILED` sem refutação matemática, e AwardGate corretamente retém os blocos de 2+1 pontos. A representação do invertido continua valendo 2 pontos.

#### Evidências e sugestões do extractor

| evidence_id | source_span literal | normalized_claim | claim_type | obligation mapping sugerido | suggested route | contexto declarado |
|---|---|---|---|---|---|---|
| `E002:claim:8f98bfde372d0b39ebd2` | `r=a+10*b+100*c.` | `r=a+10*b+100*c` | `expression` | `["b.reversed_number"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E003:claim:6efc54fe41d5194184ba` | `(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c=-99*(c-a).` | `(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c=-99*(c-a)` | `expression` | `["b.subtraction","b.middle_cancellation","b.factorization"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |

#### Payload e representação efetivamente entregues

A coluna “payload” transcreve os campos matemáticos efetivos de `SemanticClaimCandidate.normalized_payload`; o lote de entrada de `verify_tme2_p1_digital` contém o `MathClaimRecord` identificado na coluna seguinte. Os campos completos, incluindo árvores canônicas, estão em `mathematical_bridge.auditor.records` no JSON citado. `null` abaixo significa ausência real de forma canônica, não ausência de inspeção. Coordenadas do registro são relativas à fonte digital reenquadrada; o span original permanece na tabela acima.

| evidence_id | payload da projeção | registro no lote | representação canônica útil | resultado da projeção | entrada no checker de item |
|---|---|---|---|---|---|
| `E002:claim:8f98bfde372d0b39ebd2` | `{"subject":"expression","expression":"r=a+10*b+100*c","item_id":"b"}` | `semantic:4b242e8f14f5b6971515452b` / `math_relation` | `{"expression":"r=a+10*b+100*c"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_b |
| `E003:claim:6efc54fe41d5194184ba` | `{"subject":"expression","expression":"(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c=-99*(c-a)","item_id":"b"}` | `semantic:3d38afd49e8cfc19dfa204f0` / `math_semantic_candidate` | `null` | `{"grounding":"grounded","attributable":false,"canonicalized":false,"context_rejected":false,"reason":"unsupported_representation"}` | excluído antes de _check_b |

#### Comparação por obrigação e decisão de crédito

“Apoio” é o status da ponte; “elegível” é a decisão do AwardGate. Pontos pertencem a blocos/faixas da pauta: valores repetidos identificam o mesmo bloco e **não devem ser somados por obrigação**. G1…G8 são reconciliados na tabela de perdas adiante. Nenhum desses casos contém conflitos.

| rubric item | obligation_id | TME_CURRENT: apoio / award | C1: award / pontos | evidence_id | effective route | verification status | sufficiency status | context/mapping status | conflict status | award decision | reason / rejection reason | points perdidos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| b | `b.reversed_number` | supported; b.reverse=2 pt (bloco) | elegível; b.reverse=2 pt (bloco) | `E002:claim:8f98bfde372d0b39ebd2` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| b | `b.subtraction` | supported; b.subtract_cancel=2 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | `E003:claim:6efc54fe41d5194184ba` | DETERMINISTIC | DETERMINISTIC_FAILED | False / missing_checker_fact | aceito / True | nenhum | `no_sufficient_verified_evidence` | no_existing_fact_for_selected_claim | G5: 2 pt conjuntos |
| b | `b.middle_cancellation` | supported; b.subtract_cancel=2 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | `E003:claim:6efc54fe41d5194184ba` | DETERMINISTIC | DETERMINISTIC_FAILED | False / missing_checker_fact | aceito / True | nenhum | `no_sufficient_verified_evidence` | no_existing_fact_for_selected_claim | G5: 2 pt conjuntos |
| b | `b.factorization` | supported; b.simplify=1 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | `E003:claim:6efc54fe41d5194184ba` | DETERMINISTIC | DETERMINISTIC_FAILED | False / missing_checker_fact | aceito / True | nenhum | `no_sufficient_verified_evidence` | no_existing_fact_for_selected_claim | G6: 1 pt |

Itens sem fonte neste caso: a, c, d. Todas as suas obrigações têm 0 ponto nas duas linhas, sem candidato C1, sem rota/checker e sem perda incremental. A tabela concentra o item efetivamente respondido.

#### Evidência do baseline e fatos C1 que delimitam a causa

| obrigação | representação usada no baseline | status baseline |
|---|---|---|
| `b.reversed_number` | `{"record_id":"student:generic_math_4_18_relation","source_span":"r=a+10*b+100*c","payload":{"expression":"r=a+10*b+100*c"}}` | DETERMINISTIC_VERIFIED |
| `b.subtraction` | `{"record_id":"student:generic_math_20_59_relation","source_span":"(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c","payload":{"expression":"(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c"}}` | DETERMINISTIC_VERIFIED |
| `b.middle_cancellation` | `{"record_id":"student:generic_math_20_59_relation","source_span":"(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c","payload":{"expression":"(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c"}}` | DETERMINISTIC_VERIFIED |
| `b.factorization` | `{"record_id":"student:generic_math_50_69_relation","source_span":"99*a-99*c=-99*(c-a)","payload":{"expression":"99*a-99*c=-99*(c-a)"}}` | DETERMINISTIC_VERIFIED |

### p1_complete_regression: 20 → 17

Fontes: [pilot_current_01/p1_complete_regression.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01/p1_complete_regression.json); [pilot_semantic_formal_01/p1_complete_regression.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/p1_complete_regression.json).

```text
(a)
731-137=594
(b)
r=100c+10b+a.
(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c).
(c)
D=99(a-c).
1<=c.
a<=9.
a>c.
(a-c) ∈ {1,2,3,4,5,6,7,8}
D ∈ {99,198,297,396,495,594,693,792}
(d)
99(a-c)=594.
a-c=6.
(a,c) ∈ {(7,1),(8,2),(9,3)}
b ∈ {0,1,2,3,4,5,6,7,8,9}
3*10=30.
```

**Primeira divergência:** o baseline segmenta a cadeia em igualdades adjacentes; o C1 mantém a cadeia inteira em um único `normalized_payload.expression`. O extractor conserva o significado e os passos escritos, mas `ClaimProjection` cria um único candidato, sem a segmentação realizada por `generic_math.candidate_spans`. Classificação primária **CHECKER_REPRESENTATION_MISMATCH**, localizada no **adapter**; não há evidência de erro algébrico na normalização.

`convert_candidate` produz `math_semantic_candidate`, `canonical_form=null`, `attributable=false`, `canonicalized=false`, `reason=unsupported_representation`, com grounding literal válido e `context_rejected=false`. O verificador recebe o registro no lote, mas o exclui antes de `_check_b`. Não há fato para subtração/cancelamento/fatoração. O C1 emite três `DETERMINISTIC_FAILED` sem refutação matemática, e AwardGate corretamente retém os blocos de 2+1 pontos. A representação do invertido continua valendo 2 pontos.

Neste caso composto, a, c e d conservam respectivamente 3, 6 e 6 pontos. As duas verificações Lean são `FORMAL_VERIFIED`. A perda inteira está em b; não há nenhum `FORMAL_UNPROVED` neste caso.

#### Evidências e sugestões do extractor

| evidence_id | source_span literal | normalized_claim | claim_type | obligation mapping sugerido | suggested route | contexto declarado |
|---|---|---|---|---|---|---|
| `E002:claim:d9017d3974f86c992ec2` | `731-137=594` | `731-137=594` | `expression` | `["a.identifies_137","a.constructs_subtraction","a.result_594","a.arithmetic_error_only"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"final_conclusion","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E004:claim:7c74ec09d879bbd9dbe4` | `r=100c+10b+a.` | `r=100c+10b+a` | `expression` | `["b.reversed_number"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E005:claim:fb2ebef929356718cdb6` | `(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c).` | `(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c)` | `expression` | `["b.subtraction","b.middle_cancellation","b.factorization"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E007:claim:19082c647895c86de8c0` | `D=99(a-c).` | `D=99(a-c)` | `expression` | `["c.uses_expression","c.pattern_recognized"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E008:claim:c2a4273c754d912db20b` | `1<=c.` | `1<=c` | `expression` | `["c.difference_domain"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E009:claim:79f4338fe51607b7aace` | `a<=9.` | `a<=9` | `expression` | `["c.difference_domain"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E010:claim:f14713be0350ad3e8909` | `a>c.` | `a>c` | `expression` | `["c.difference_domain"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E011:claim:769c5fb6d182a0f31453` | `(a-c) ∈ {1,2,3,4,5,6,7,8}` | `(a-c) ∈ {1,2,3,4,5,6,7,8}` | `collection` | `["c.difference_domain"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E012:claim:d0fa4b80c1895810f651` | `D ∈ {99,198,297,396,495,594,693,792}` | `D ∈ {99,198,297,396,495,594,693,792}` | `collection` | `["c.complete_list","c.no_extraneous_values","c.single_list_error","c.several_correct","c.pattern_recognized","c.some_correct"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"final_conclusion","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E014:claim:4ddfb4aef52a6c41e7f6` | `99(a-c)=594.` | `99(a-c)=594` | `expression` | `["d.equation"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E015:claim:ad573bea609411e5e193` | `a-c=6.` | `a-c=6` | `expression` | `["d.difference_six"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E016:claim:04e3a0b28ac7d4dc06df` | `(a,c) ∈ {(7,1),(8,2),(9,3)}` | `(a,c) ∈ {(7,1),(8,2),(9,3)}` | `collection` | `["d.digit_pairs"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E017:claim:f7fd7f251d7a905602a9` | `b ∈ {0,1,2,3,4,5,6,7,8,9}` | `b ∈ {0,1,2,3,4,5,6,7,8,9}` | `collection` | `["d.middle_choices"]` | `DETERMINISTIC` | `{"assertion_status":"asserted","polarity":"positive","scope":"main_argument","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |
| `E018:claim:b4342ef631173217586d` | `3*10=30.` | `3*10=30` | `expression` | `["d.total_thirty"]` | `FORMAL` | `{"assertion_status":"asserted","polarity":"positive","scope":"final_conclusion","hypothetical":false,"abandoned":false,"attributed_to_student":true}` |

#### Payload e representação efetivamente entregues

A coluna “payload” transcreve os campos matemáticos efetivos de `SemanticClaimCandidate.normalized_payload`; o lote de entrada de `verify_tme2_p1_digital` contém o `MathClaimRecord` identificado na coluna seguinte. Os campos completos, incluindo árvores canônicas, estão em `mathematical_bridge.auditor.records` no JSON citado. `null` abaixo significa ausência real de forma canônica, não ausência de inspeção. Coordenadas do registro são relativas à fonte digital reenquadrada; o span original permanece na tabela acima.

| evidence_id | payload da projeção | registro no lote | representação canônica útil | resultado da projeção | entrada no checker de item |
|---|---|---|---|---|---|
| `E002:claim:d9017d3974f86c992ec2` | `{"subject":"expression","expression":"731-137=594","item_id":"a"}` | `semantic:bf69a0da85fbeb1a6857d578` / `math_relation` | `{"expression":"731-137=594"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_a |
| `E004:claim:7c74ec09d879bbd9dbe4` | `{"subject":"expression","expression":"r=100c+10b+a","item_id":"b"}` | `semantic:6798592a5f423fcd808985c2` / `math_relation` | `{"expression":"r=100c+10b+a"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_b |
| `E005:claim:fb2ebef929356718cdb6` | `{"subject":"expression","expression":"(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c)","item_id":"b"}` | `semantic:5247f847993da005410c6c79` / `math_semantic_candidate` | `null` | `{"grounding":"grounded","attributable":false,"canonicalized":false,"context_rejected":false,"reason":"unsupported_representation"}` | excluído antes de _check_b |
| `E007:claim:19082c647895c86de8c0` | `{"subject":"expression","expression":"D=99(a-c)","item_id":"c"}` | `semantic:c57c5ae2fd5946f724c10f9e` / `math_relation` | `{"expression":"D=99(a-c)"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_c |
| `E008:claim:c2a4273c754d912db20b` | `{"subject":"expression","expression":"1<=c","item_id":"c"}` | `semantic:0c74daa121d64a01b75270e9` / `math_relation` | `{"expression":"1<=c"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_c |
| `E009:claim:79f4338fe51607b7aace` | `{"subject":"expression","expression":"a<=9","item_id":"c"}` | `semantic:d73aa22c3f1e18d294ff6b4b` / `math_relation` | `{"expression":"a<=9"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_c |
| `E010:claim:f14713be0350ad3e8909` | `{"subject":"expression","expression":"a>c","item_id":"c"}` | `semantic:a00f2a850addc21cc8f3f713` / `math_relation` | `{"expression":"a>c"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_c |
| `E011:claim:769c5fb6d182a0f31453` | `{"subject":"collection","expression":"(a-c) ∈ {1,2,3,4,5,6,7,8}","item_id":"c"}` | `semantic:1dd6454248be4d20990383fd` / `math_finite_collection` | `{"subject":{"kind":"expression","tree":{"kind":"difference","value":null,"args":[{"kind":"variable","value":"a","args":[]},{"kind":"variable","value":"c","args":[]}]},"affine":[["a","1"],["c","-1"]],"relation":null,"variables":["a","c"],"schema_version":"canonical-math-v1","domain":"real_total"},"elements":[1,2,3,4,5,6,7,8],"container":"set"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_c |
| `E012:claim:d0fa4b80c1895810f651` | `{"subject":"collection","expression":"D ∈ {99,198,297,396,495,594,693,792}","item_id":"c"}` | `semantic:86f7dcfe5ae73cc3468bbab3` / `math_finite_collection` | `{"subject":{"kind":"expression","tree":{"kind":"variable","value":"D","args":[]},"affine":null,"relation":null,"variables":["D"],"schema_version":"canonical-math-v1","domain":"real_total"},"elements":[99,198,297,396,495,594,693,792],"container":"set"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_c |
| `E014:claim:4ddfb4aef52a6c41e7f6` | `{"subject":"expression","expression":"99(a-c)=594","item_id":"d"}` | `semantic:d7032d0c5fc633030769e45f` / `math_relation` | `{"expression":"99(a-c)=594"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_d |
| `E015:claim:ad573bea609411e5e193` | `{"subject":"expression","expression":"a-c=6","item_id":"d"}` | `semantic:750585d2287e50848d3eaa4b` / `math_relation` | `{"expression":"a-c=6"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_d |
| `E016:claim:04e3a0b28ac7d4dc06df` | `{"subject":"collection","expression":"(a,c) ∈ {(7,1),(8,2),(9,3)}","item_id":"d"}` | `semantic:732a920eb25a720fa8287f6f` / `math_finite_collection` | `{"subject":{"ordered_variables":["a","c"]},"elements":[[7,1],[8,2],[9,3]],"container":"set"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_d |
| `E017:claim:f7fd7f251d7a905602a9` | `{"subject":"collection","expression":"b ∈ {0,1,2,3,4,5,6,7,8,9}","item_id":"d"}` | `semantic:77f978b3116877320568d4b4` / `math_finite_collection` | `{"subject":{"kind":"expression","tree":{"kind":"variable","value":"b","args":[]},"affine":[["b","1"]],"relation":null,"variables":["b"],"schema_version":"canonical-math-v1","domain":"real_total"},"elements":[0,1,2,3,4,5,6,7,8,9],"container":"set"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_d |
| `E018:claim:b4342ef631173217586d` | `{"subject":"expression","expression":"3*10=30","item_id":"d"}` | `semantic:9f082b946f356a0bcfa2db4b` / `math_relation` | `{"expression":"3*10=30"}` | `{"grounding":"grounded","attributable":true,"canonicalized":true,"context_rejected":false,"reason":"exact"}` | elegível para _check_d |

#### Comparação por obrigação e decisão de crédito

“Apoio” é o status da ponte; “elegível” é a decisão do AwardGate. Pontos pertencem a blocos/faixas da pauta: valores repetidos identificam o mesmo bloco e **não devem ser somados por obrigação**. G1…G8 são reconciliados na tabela de perdas adiante. Nenhum desses casos contém conflitos.

| rubric item | obligation_id | TME_CURRENT: apoio / award | C1: award / pontos | evidence_id | effective route | verification status | sufficiency status | context/mapping status | conflict status | award decision | reason / rejection reason | points perdidos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a | `a.identifies_137` | supported; a.full=3 pt (bloco) | elegível; a.full=3 pt (bloco) | `E002:claim:d9017d3974f86c992ec2` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| a | `a.constructs_subtraction` | supported; a.full=3 pt (bloco) | elegível; a.full=3 pt (bloco) | `E002:claim:d9017d3974f86c992ec2` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| a | `a.result_594` | supported; a.full=3 pt (bloco) | elegível; a.full=3 pt (bloco) | `E002:claim:d9017d3974f86c992ec2` | FORMAL | FORMAL_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| a | `a.arithmetic_error_only` | indeterminate; 0 pt; nenhum bloco pago | não elegível; 0 pt; nenhum bloco pago | `E002:claim:d9017d3974f86c992ec2` | DETERMINISTIC | DETERMINISTIC_FAILED | False / missing_checker_fact | aceito / True | nenhum | `no_sufficient_verified_evidence` | no_existing_fact_for_selected_claim | 0 |
| b | `b.reversed_number` | supported; b.reverse=2 pt (bloco) | elegível; b.reverse=2 pt (bloco) | `E004:claim:7c74ec09d879bbd9dbe4` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| b | `b.subtraction` | supported; b.subtract_cancel=2 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | `E005:claim:fb2ebef929356718cdb6` | DETERMINISTIC | DETERMINISTIC_FAILED | False / missing_checker_fact | aceito / True | nenhum | `no_sufficient_verified_evidence` | no_existing_fact_for_selected_claim | G7: 2 pt conjuntos |
| b | `b.middle_cancellation` | supported; b.subtract_cancel=2 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | `E005:claim:fb2ebef929356718cdb6` | DETERMINISTIC | DETERMINISTIC_FAILED | False / missing_checker_fact | aceito / True | nenhum | `no_sufficient_verified_evidence` | no_existing_fact_for_selected_claim | G7: 2 pt conjuntos |
| b | `b.factorization` | supported; b.simplify=1 pt (bloco) | não elegível; 0 pt; nenhum bloco pago | `E005:claim:fb2ebef929356718cdb6` | DETERMINISTIC | DETERMINISTIC_FAILED | False / missing_checker_fact | aceito / True | nenhum | `no_sufficient_verified_evidence` | no_existing_fact_for_selected_claim | G8: 1 pt |
| c | `c.uses_expression` | supported; c.expression=1 pt (bloco) | elegível; c.expression=1 pt (bloco) | `E007:claim:19082c647895c86de8c0` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| c | `c.difference_domain` | supported; c.domain=1 pt (bloco) | elegível; c.domain=1 pt (bloco) | `E008:claim:c2a4273c754d912db20b`<br>`E009:claim:79f4338fe51607b7aace`<br>`E010:claim:f14713be0350ad3e8909`<br>`E011:claim:769c5fb6d182a0f31453` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True; aceito / True; aceito / True; aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| c | `c.complete_list` | supported; c.list.full=4 pt (bloco) | elegível; c.list.full=4 pt (bloco) | `E012:claim:d0fa4b80c1895810f651` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| c | `c.no_extraneous_values` | supported; c.list.full=4 pt (bloco) | elegível; c.list.full=4 pt (bloco) | `E012:claim:d0fa4b80c1895810f651` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| c | `c.single_list_error` | refuted; 0 pt; nenhum bloco pago | não elegível; 0 pt; nenhum bloco pago | `E012:claim:d0fa4b80c1895810f651` | DETERMINISTIC | DETERMINISTIC_FAILED | False / existing_P1_fact_contract | aceito / True | nenhum | `no_sufficient_verified_evidence` | EXISTING_VERIFICATION_RESULT | 0 |
| c | `c.several_correct` | supported; 0 pt; nenhum bloco pago | elegível; 0 pt; nenhum bloco pago | `E012:claim:d0fa4b80c1895810f651` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| c | `c.pattern_recognized` | supported; 0 pt; nenhum bloco pago | elegível; 0 pt; nenhum bloco pago | `E012:claim:d0fa4b80c1895810f651`<br>`E007:claim:19082c647895c86de8c0` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True; aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| c | `c.some_correct` | supported; 0 pt; nenhum bloco pago | elegível; 0 pt; nenhum bloco pago | `E012:claim:d0fa4b80c1895810f651` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| d | `d.equation` | supported; d.solve=2 pt (bloco) | elegível; d.solve=2 pt (bloco) | `E014:claim:4ddfb4aef52a6c41e7f6` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| d | `d.difference_six` | supported; d.solve=2 pt (bloco) | elegível; d.solve=2 pt (bloco) | `E015:claim:ad573bea609411e5e193` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| d | `d.digit_pairs` | supported; d.pairs=2 pt (bloco) | elegível; d.pairs=2 pt (bloco) | `E016:claim:04e3a0b28ac7d4dc06df` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| d | `d.middle_choices` | supported; d.count=2 pt (bloco) | elegível; d.count=2 pt (bloco) | `E017:claim:f7fd7f251d7a905602a9` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |
| d | `d.total_thirty` | supported; d.count=2 pt (bloco) | elegível; d.count=2 pt (bloco) | `E018:claim:b4342ef631173217586d` | FORMAL | FORMAL_VERIFIED | True / existing_P1_fact_contract | aceito / True | nenhum | `eligible` | EXISTING_VERIFICATION_RESULT | 0 |

#### Evidência do baseline e fatos C1 que delimitam a causa

| obrigação | representação usada no baseline | status baseline |
|---|---|---|
| `b.reversed_number` | `{"record_id":"student:generic_math_22_34_relation","source_span":"r=100c+10b+a","payload":{"expression":"r=100c+10b+a"}}` | DETERMINISTIC_VERIFIED |
| `b.subtraction` | `{"record_id":"student:generic_math_36_69_relation","source_span":"(100a+10b+c)-(100c+10b+a)=99a-99c","payload":{"expression":"(100a+10b+c)-(100c+10b+a)=99a-99c"}}` | DETERMINISTIC_VERIFIED |
| `b.middle_cancellation` | `{"record_id":"student:generic_math_36_69_relation","source_span":"(100a+10b+c)-(100c+10b+a)=99a-99c","payload":{"expression":"(100a+10b+c)-(100c+10b+a)=99a-99c"}}` | DETERMINISTIC_VERIFIED |
| `b.factorization` | `{"record_id":"student:generic_math_62_77_relation","source_span":"99a-99c=99(a-c)","payload":{"expression":"99a-99c=99(a-c)"}}` | DETERMINISTIC_VERIFIED |

### Payloads Lean realmente executados nos casos regressivos

Além dos payloads de projeção acima, estes são os `StudentClaim.data` efetivamente entregues ao checker aritmético, conforme `verification_results[].checker_result`. São resultados já registrados, não novas execuções desta auditoria.

| caso | obrigação | payload aritmético | proposição Lean | resultado |
|---|---|---|---|---|
| a_complete | a.result_594 | `{"left_expr":"731-137","right_expr":"594"}` | `((731 : ℤ)-137) = ((594 : ℤ))` | `compiled=true`, `formal_status=verified`; stdout/stderr vazios |
| p1_complete_regression | a.result_594 | `{"left_expr":"731-137","right_expr":"594"}` | `((731 : ℤ)-137) = ((594 : ℤ))` | `compiled=true`, `formal_status=verified`; stdout/stderr vazios |
| p1_complete_regression | d.total_thirty | `{"left_expr":"3*10","right_expr":"30"}` | `((3 : ℤ)*10) = ((30 : ℤ))` | `compiled=true`, `formal_status=verified`; stdout/stderr vazios |

Em `a_only_inverse`, `b_complete` e `b_equivalent_algebra`, não houve payload Lean executado. Nas cadeias de b, o registro chegou ao verificador geral, mas foi excluído antes do checker do item; não se deve confundir essa exclusão com uma tentativa matemática malsucedida.

### Reconciliação dos 13 pontos perdidos (sem dupla contagem)

| grupo | caso | regra paga antes | Current → C1 | primeira divergência | categoria primária |
|---|---|---|---|---|---|
| G1 | a_complete | a.full; a.identification também inviabilizada | 3 → 0 | sugestão FORMAL compartilhada → router rejeita identificação/montagem | ROUTER_ERROR (gatilho FORMAL_OVERROUTING) |
| G2 | a_only_inverse | a.identification | 1 → 0 | extractor sugere a.result_594 para 137; fato de identificação filtrado | OBLIGATION_MAPPING_ERROR |
| G3 | b_complete | b.subtract_cancel | 2 → 0 | cadeia inteira não segmentada na projeção | CHECKER_REPRESENTATION_MISMATCH / adapter |
| G4 | b_complete | b.simplify | 1 → 0 | mesma cadeia | mesma causa de G3 |
| G5 | b_equivalent_algebra | b.subtract_cancel | 2 → 0 | cadeia inteira não segmentada | CHECKER_REPRESENTATION_MISMATCH / adapter |
| G6 | b_equivalent_algebra | b.simplify | 1 → 0 | mesma cadeia | mesma causa de G5 |
| G7 | p1_complete_regression | b.subtract_cancel | 2 → 0 | cadeia inteira não segmentada | CHECKER_REPRESENTATION_MISMATCH / adapter |
| G8 | p1_complete_regression | b.simplify | 1 → 0 | mesma cadeia | mesma causa de G7 |

A perda de 3 em a não equivale a 1 ponto por obrigação. O resultado formal permanece elegível, mas não paga uma faixa sozinho. Em b, subtração e cancelamento são testemunhos do mesmo bloco de 2 pontos; a fatoração paga 1 ponto separado. Nenhum defeito de dupla contagem ou do AwardGate é necessário para explicar as perdas.

### Encadeamento no código que demonstra os mecanismos

- [Router: rejeita sugestão FORMAL fora das duas obrigações, antes de selecionar a rota efetiva](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/experimental/tme_semantic_formal/claim_router.py:10).

- [Mapper: só percorre obligation_candidates; captura ValueError sem recuperar outras obrigações](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/experimental/tme_semantic_formal/obligation_mapper.py:48).

- [Adapter: um SemanticClaimCandidate por evidência; ignora a coleção deterministic fornecida](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/experimental/tme_semantic_formal/verification.py:52).

- [Filtro: um fato só aparece se seu par evidence/obligation estiver entre os candidatos aceitos](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/experimental/tme_semantic_formal/verification.py:89).

- [Ausência de fato gera resultado sintético UNPROVED/FAILED](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/experimental/tme_semantic_formal/verification.py:113).

- [Baseline: fragmenta explicitamente igualdades adjacentes de uma cadeia](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/student_claims/generic_math.py:166).

- [Conversão: parse único; forma ausente vira unsupported_representation e attributable=false](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/student_claims/semantic.py:349).

- [Checker: sides exige exatamente um sinal de igualdade](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/lean/student_claim_checkers/tme2_p1.py:40).

- [Checker: filtra registros não atribuíveis antes de _check_a…_check_d](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/lean/student_claim_checkers/tme2_p1.py:329).

- [AwardGate: exige resultado positivo, suficiência e vínculo aceito](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/experimental/tme_semantic_formal/award_gate.py:25).

A divergência observada não prova um erro interno do modelo nem permite inferir sua intenção. O que os artefatos demonstram é o JSON retornado e a transformação posterior. No caso de b, manter a cadeia inteira é fiel ao texto e compatível com a orientação “preserva a expressão inteira”; a granularidade do adapter é que não coincide com a representação aceita.

## 3. Os cinco FORMAL_UNPROVED

**Nenhum dos cinco contém uma proposição Lean efetivamente testada.** Quatro têm `no_existing_fact_for_selected_claim`; um tem `formal_checker_not_executed_for_this_representation`. Todos têm `technical_uncertainty=false`, `mathematical_refutation=false`, suficiência falsa e zero crédito na obrigação. Não há timeout, import ausente, erro Mathlib ou `unsolved goals` nesses cinco resultados. Não confundir os dez resultados de rota FORMAL com dez execuções Lean.

### a_only_inverse

| campo | constatação |
|---|---|
| obrigação / evidence_id | `a.result_594` / `E002:claim:9b82fb4a1ffd952c6aa2` |
| source_span | `137` |
| claim extraído | `137` |
| tipo / rota sugerida → efetiva | expression / DETERMINISTIC → FORMAL |
| payload no lote matemático | `{"record_id":"semantic:5b174a009e76379b0aae2c4b","claim_type":"math_literal","representation":{"expression":"137"}}` |
| payload StudentClaim/Lean | Nenhum: arithmetic não foi chamado para esta evidência. |
| proposição Lean efetivamente testada | Nenhuma; não existe certificado associado a este resultado. |
| motivo registrado | `no_existing_fact_for_selected_claim` |
| completude do claim | 137 é completo como identificação do invertido; incompleto/inadequado como prova de resultado 594. |
| pré-requisito | Não é falta de uma cadeia oficial: a obrigação selecionada está errada. |
| normalização alterou o significado? | Não; 137 permaneceu 137. |
| FORMAL apropriado? | Não para este vínculo. O literal pertence à identificação determinística. |
| classificação / efeito na nota | OBLIGATION_MAPPING_ERROR; 1 ponto perdido na identificação. |
| artefato | [pilot_semantic_formal_01/a_only_inverse.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/a_only_inverse.json) |

### a_only_result

| campo | constatação |
|---|---|
| obrigação / evidence_id | `a.result_594` / `E002:claim:f0694a43bf7a6caa4ff0` |
| source_span | `594` |
| claim extraído | `594` |
| tipo / rota sugerida → efetiva | expression / DETERMINISTIC → FORMAL |
| payload no lote matemático | `{"record_id":"semantic:220ed5e237cdb6c135927405","claim_type":"math_literal","representation":{"expression":"594"}}` |
| payload StudentClaim/Lean | Nenhum: arithmetic não foi chamado para esta evidência. |
| proposição Lean efetivamente testada | Nenhuma; não existe certificado associado a este resultado. |
| motivo registrado | `formal_checker_not_executed_for_this_representation` |
| completude do claim | 594 é apenas um número, sem igualdade escrita. |
| pré-requisito | Faltam montagem/identificação para a.full e uma igualdade para o checker formal; baseline também dá 0. |
| normalização alterou o significado? | Não. |
| FORMAL apropriado? | Não executável nesta representação, embora a obrigação esteja na whitelist formal. O baseline verifica o literal deterministicamente; C1 impede promoção desse fato a formal. |
| classificação / efeito na nota | CHECKER_REPRESENTATION_MISMATCH / cobertura formal mais restrita; 0 ponto incremental. |
| artefato | [pilot_semantic_formal_01/a_only_result.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/a_only_result.json) |

### a_wrong_setup

| campo | constatação |
|---|---|
| obrigação / evidence_id | `a.result_594` / `E002:claim:3797ace8f1c6c08936f0` |
| source_span | `731-173=584` |
| claim extraído | `731-173=584` |
| tipo / rota sugerida → efetiva | expression / DETERMINISTIC → FORMAL |
| payload no lote matemático | `{"record_id":"semantic:8e3c7e072f754735abcb7c6a","claim_type":"math_relation","representation":{"expression":"731-173=584"}}` |
| payload StudentClaim/Lean | Nenhum: arithmetic não foi chamado para esta evidência. |
| proposição Lean efetivamente testada | Nenhuma; não existe certificado associado a este resultado. |
| motivo registrado | `no_existing_fact_for_selected_claim` |
| completude do claim | A igualdade escrita é completa, mas a subtração usa 173, não 137. |
| pré-requisito | Falha a condição is_subtraction(731,137); _check_a continua antes de chamar arithmetic. |
| normalização alterou o significado? | Não; os operandos e o resultado foram preservados. |
| FORMAL apropriado? | Está na whitelist, mas não é uma instância elegível de a.result_594. Não houve teste da igualdade falsa. |
| classificação / efeito na nota | Mapeamento amplo / elegibilidade do checker; 0 ponto incremental. |
| artefato | [pilot_semantic_formal_01/a_wrong_setup.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/a_wrong_setup.json) |

### d_later_error

| campo | constatação |
|---|---|
| obrigação / evidence_id | `d.total_thirty` / `E006:claim:d2ae868581f141aac057` |
| source_span | `3*9=27.` |
| claim extraído | `3*9=27` |
| tipo / rota sugerida → efetiva | expression / FORMAL → FORMAL |
| payload no lote matemático | `{"record_id":"semantic:e99ba0734821941a477fe579","claim_type":"math_relation","representation":{"expression":"3*9=27"}}` |
| payload StudentClaim/Lean | Nenhum: arithmetic não foi chamado para esta evidência. |
| proposição Lean efetivamente testada | Nenhuma; não existe certificado associado a este resultado. |
| motivo registrado | `no_existing_fact_for_selected_claim` |
| completude do claim | 3*9=27 é igualdade aritmética completa e verdadeira, mas não sustenta a contagem de trinta. |
| pré-requisito | Pares escritos têm diferença 5; escolhas de b omitem 0. Ambos refutados. Além disso, o checker exige produto 3×10. |
| normalização alterou o significado? | Não; apenas pontuação final removida. |
| FORMAL apropriado? | Não para d.total_thirty. Provar 3×9=27 não provaria a obrigação nem corrigiria pré-requisitos. |
| classificação / efeito na nota | DEPENDENCY_ERROR no trabalho escrito + instância fora do contrato; 0 ponto incremental. |
| artefato | [pilot_semantic_formal_01/d_later_error.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/d_later_error.json) |

### d_only_difference_then_error

| campo | constatação |
|---|---|
| obrigação / evidence_id | `d.total_thirty` / `E004:claim:913738bf5cbfcafa9a6c` |
| source_span | `30` |
| claim extraído | `30` |
| tipo / rota sugerida → efetiva | expression / DETERMINISTIC → FORMAL |
| payload no lote matemático | `{"record_id":"semantic:df1cf834e41aedf96807fd29","claim_type":"math_literal","representation":{"expression":"30"}}` |
| payload StudentClaim/Lean | Nenhum: arithmetic não foi chamado para esta evidência. |
| proposição Lean efetivamente testada | Nenhuma; não existe certificado associado a este resultado. |
| motivo registrado | `no_existing_fact_for_selected_claim` |
| completude do claim | 30 é literal sem produto/igualdade. |
| pré-requisito | Pares incorretos; escolhas de b ausentes; produto escrito ausente. |
| normalização alterou o significado? | Não. |
| FORMAL apropriado? | Não executável para o literal; whitelist de obrigação não basta. |
| classificação / efeito na nota | Pré-requisitos e representação ausentes; 0 ponto incremental. |
| artefato | [pilot_semantic_formal_01/d_only_difference_then_error.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/d_only_difference_then_error.json) |

**Relação com as regressões:** `a_complete` não tem UNPROVED: seu resultado é FORMAL_VERIFIED. `b_complete` não tem rota formal. `p1_complete_regression` tem duas provas formais verificadas. Nenhum dos cinco UNPROVED explica essas três perdas. Apenas `a_only_inverse` pertence ao conjunto regressivo; o UNPROVED é consequência do vínculo errado, enquanto a perda vem da identificação válida filtrada.

## 4. Aumento de DETERMINISTIC_FAILED: 12 → 27

| obrigação | verified Current | verified C1 | failed Current | failed C1 | Δ failed |
|---|---|---|---|---|---|
| `a.identifies_137` | 4 | 2 | 0 | 1 | 1 |
| `a.constructs_subtraction` | 3 | 2 | 0 | 1 | 1 |
| `a.result_594` | 1 | 0 | 0 | 0 | 0 |
| `a.arithmetic_error_only` | 1 | 1 | 0 | 2 | 2 |
| `b.reversed_number` | 4 | 4 | 0 | 0 | 0 |
| `b.subtraction` | 4 | 1 | 0 | 3 | 3 |
| `b.middle_cancellation` | 4 | 1 | 0 | 3 | 3 |
| `b.factorization` | 3 | 0 | 0 | 5 | 5 |
| `c.uses_expression` | 4 | 4 | 0 | 0 | 0 |
| `c.difference_domain` | 2 | 2 | 0 | 0 | 0 |
| `c.complete_list` | 3 | 3 | 3 | 3 | 0 |
| `c.no_extraneous_values` | 5 | 5 | 1 | 1 | 0 |
| `c.single_list_error` | 2 | 2 | 4 | 4 | 0 |
| `c.several_correct` | 5 | 5 | 1 | 1 | 0 |
| `c.pattern_recognized` | 4 | 4 | 0 | 0 | 0 |
| `c.some_correct` | 6 | 6 | 0 | 0 | 0 |
| `d.equation` | 4 | 4 | 0 | 0 | 0 |
| `d.difference_six` | 5 | 5 | 0 | 0 | 0 |
| `d.digit_pairs` | 3 | 3 | 2 | 2 | 0 |
| `d.middle_choices` | 2 | 2 | 1 | 1 | 0 |

Os **15 failed adicionais** decompõem-se exatamente em: **9 perdas de fatos antes verificados** (3 obrigações × 3 cadeias de b) e **6 candidatos sem fato que o baseline simplesmente não emitia**. Os 12 failed já existentes permanecem: 9 em critérios de lista de c e 3 em pares/escolhas de d, todos com refutação matemática registrada. Uma lista correta refuta “exatamente um erro”, sem reduzir sua faixa completa; isso não é falha do pipeline.

| grupo | ocorrências adicionais | baseline | payload/expectativa | efeito |
|---|---|---|---|---|
| Cadeias de igualdades em b | 9 | Duas igualdades adjacentes, verificadas | LLM conserva cadeia inteira; adapter não a divide; parser/sides precisam de igualdade binária | 9 pontos perdidos; causa adapter |
| a_wrong_setup: identifies/constructs/arithmetic_error_only | 3 | Nenhum fato para montagem com 173 | 731-173=584; checker exige subtração de 137 e erro único com montagem correta | Nenhum ponto incremental; candidatos sem suporte |
| p1_complete_regression: arithmetic_error_only | 1 | Nenhum diagnóstico de erro no cálculo correto | 731-137=594; não satisfaz erro aritmético único | Nenhum ponto incremental |
| b_no_factorization: factorization | 1 | Nenhum fato de fatoração; 4 pontos preservados | Igualdade termina em 99a-99c; falta passo expandido → fatorado | Nenhum ponto incremental |
| b_only_expression: factorization | 1 | Nenhum fato de fatoração | 99(a-c) isolado; checker exige transformação escrita, não só resultado | Nenhum ponto incremental |

Os **13 verified a menos** também fecham: 9 de b; 2 de identificação/montagem em `a_complete`; 1 identificação em `a_only_inverse`; 1 literal `594` que o baseline tratava como determinístico e C1 relata como FORMAL_UNPROVED. Assim, rotas determinísticas variam por −13+15=+2 (81→83). A mudança de contagem não representa 15 novas refutações matemáticas.

### Todas as 27 linhas determinísticas malsucedidas

| caso | obrigação | baseline | reason C1 | refutação matemática? | payload expression |
|---|---|---|---|---|---|
| a_wrong_setup | `a.identifies_137` | sem linha | no_existing_fact_for_selected_claim | False | `731-173=584` |
| a_wrong_setup | `a.constructs_subtraction` | sem linha | no_existing_fact_for_selected_claim | False | `731-173=584` |
| a_wrong_setup | `a.arithmetic_error_only` | sem linha | no_existing_fact_for_selected_claim | False | `731-173=584` |
| b_complete | `b.subtraction` | DETERMINISTIC_VERIFIED | no_existing_fact_for_selected_claim | False | `(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c)` |
| b_complete | `b.middle_cancellation` | DETERMINISTIC_VERIFIED | no_existing_fact_for_selected_claim | False | `(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c)` |
| b_complete | `b.factorization` | DETERMINISTIC_VERIFIED | no_existing_fact_for_selected_claim | False | `(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c)` |
| b_equivalent_algebra | `b.subtraction` | DETERMINISTIC_VERIFIED | no_existing_fact_for_selected_claim | False | `(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c=-99*(c-a)` |
| b_equivalent_algebra | `b.middle_cancellation` | DETERMINISTIC_VERIFIED | no_existing_fact_for_selected_claim | False | `(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c=-99*(c-a)` |
| b_equivalent_algebra | `b.factorization` | DETERMINISTIC_VERIFIED | no_existing_fact_for_selected_claim | False | `(c+10*b+100*a)-(a+10*b+100*c)=99*a-99*c=-99*(c-a)` |
| b_no_factorization | `b.factorization` | sem linha | no_existing_fact_for_selected_claim | False | `(100a+10b+c)-(100c+10b+a)=99a-99c` |
| b_only_expression | `b.factorization` | sem linha | no_existing_fact_for_selected_claim | False | `99(a-c)` |
| c_complete | `c.single_list_error` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `D ∈ {99,198,297,396,495,594,693,792}` |
| c_few_results | `c.complete_list` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `{99}` |
| c_few_results | `c.single_list_error` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `{99}` |
| c_few_results | `c.several_correct` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `{99}` |
| c_one_extraneous | `c.no_extraneous_values` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `{99,198,297,396,495,594,693,792,891}` |
| c_one_omission | `c.complete_list` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `D ∈ {99,198,297,396,495,594,693}` |
| c_several_with_pattern | `c.complete_list` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `D ∈ {99,198,297,396}` |
| c_several_with_pattern | `c.single_list_error` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `D ∈ {99,198,297,396}` |
| d_later_error | `d.digit_pairs` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `(a,c) ∈ {(6,1),(7,2),(8,3)}` |
| d_later_error | `d.middle_choices` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `b ∈ {1,2,3,4,5,6,7,8,9}` |
| d_only_difference_then_error | `d.digit_pairs` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `(a,c) ∈ {(6,1),(7,2),(8,3)}` |
| p1_complete_regression | `c.single_list_error` | DETERMINISTIC_FAILED | EXISTING_VERIFICATION_RESULT | True | `D ∈ {99,198,297,396,495,594,693,792}` |
| p1_complete_regression | `a.arithmetic_error_only` | sem linha | no_existing_fact_for_selected_claim | False | `731-137=594` |
| p1_complete_regression | `b.subtraction` | DETERMINISTIC_VERIFIED | no_existing_fact_for_selected_claim | False | `(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c)` |
| p1_complete_regression | `b.middle_cancellation` | DETERMINISTIC_VERIFIED | no_existing_fact_for_selected_claim | False | `(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c)` |
| p1_complete_regression | `b.factorization` | DETERMINISTIC_VERIFIED | no_existing_fact_for_selected_claim | False | `(100a+10b+c)-(100c+10b+a)=99a-99c=99(a-c)` |

**Diagnóstico A–G:** **G — combinação**, dominada por **C — adapter** (9/13 pontos), seguida do contrato extractor/mapper/router (4/13). Na perda de a_complete, o roteamento rígido torna uma sugestão do modelo impeditiva; em a_only_inverse, o mapeamento de pertinência errado impede aproveitar um fato já verificado. **B — normalização semântica incorreta**, **E — erro matemático do checker** e **F — suficiência excessiva** não são demonstrados como causas destas cinco regressões. A falha de b ocorre antes do checker de item; a suficiência falsa apenas acompanha a ausência de fato.

## 5. SEMANTIC routes = 0

O zero é **correto como descrição da execução observada**, mas não valida a cobertura semântica do C1. As 54 evidências são **38 expression + 16 collection + 0 qualitative**. Em todos os 21 casos, `sufficiency.provider={status: skipped, api_calls: 0}`. Os textos com conteúdo matemático usam notação explícita; os dois textos de prosa sem matemática são “Não sei resolver.” e “Não sei.”, corretamente sem claims. Não há neste piloto um argumento matemático substantivo em prosa que demonstre coerção indevida para DETERMINISTIC.

Regra comum às 19 obrigações D/S: o tipo permitido `expression`/`collection` escolhe DETERMINISTIC; `qualitative` escolhe SEMANTIC, desde que não seja apenas notação matemática reconhecida rotulada como prosa e que o contexto seja válido. A sugestão SEMANTIC não muda uma `expression` para SEMANTIC. Sugestão FORMAL fora da whitelist é rejeitada, como visto em a_complete. A rota é escolhida **antes** de tentar converter/verificar a representação. Não existe fallback DETERMINISTIC→SEMANTIC após falha. O gate só agrupa mapeamentos cuja rota efetiva já era SEMANTIC.

| obrigação D/S | quando DETERMINISTIC | quando SEMANTIC é candidata | fallback D→S | linhas D observadas | linhas S |
|---|---|---|---|---|---|
| `a.identifies_137` | expression | qualitative: identificação literal do invertido em prosa; sujeito a gate e política local | não | 3 | 0 |
| `a.constructs_subtraction` | expression | qualitative: descrição explícita da subtração e de sua ordem; sujeito a gate e política local | não | 3 | 0 |
| `a.arithmetic_error_only` | expression | qualitative: diagnóstico textual de erro único, com evidência do item inteiro; sujeito a gate e política local | não | 3 | 0 |
| `b.reversed_number` | expression | qualitative: descrição inequívoca da representação invertida; sujeito a gate e política local | não | 4 | 0 |
| `b.subtraction` | expression | qualitative: diferença posicional explicitada em palavras; sujeito a gate e política local | não | 4 | 0 |
| `b.middle_cancellation` | expression | qualitative: cancelamento do termo central explicado; sujeito a gate e política local | não | 4 | 0 |
| `b.factorization` | expression | qualitative: passagem de expansão para fatoração explicitada; sujeito a gate e política local | não | 5 | 0 |
| `c.uses_expression` | expression | qualitative: uso da expressão descrito no argumento; sujeito a gate e política local | não | 4 | 0 |
| `c.difference_domain` | expression ou collection | qualitative: limites/domínio inteiro justificados em palavras; sujeito a gate e política local | não | 2 | 0 |
| `c.complete_list` | collection | qualitative: enumeração literal completa em prosa; sujeito a gate e política local | não | 6 | 0 |
| `c.no_extraneous_values` | collection | qualitative: enumeração literal que permite verificar ausência de extras; sujeito a gate e política local | não | 6 | 0 |
| `c.single_list_error` | collection | qualitative: lista/argumento literal que permite diagnóstico de um erro; sujeito a gate e política local | não | 6 | 0 |
| `c.several_correct` | collection | qualitative: dois valores distintos explicitamente escritos; sujeito a gate e política local | não | 6 | 0 |
| `c.pattern_recognized` | expression ou collection | qualitative: explicação que liga fórmula e lista; sujeito a gate e política local | não | 4 | 0 |
| `c.some_correct` | collection | qualitative: pelo menos um valor explicitamente escrito; sujeito a gate e política local | não | 6 | 0 |
| `d.equation` | expression | qualitative: equação relatada inequivocamente no argumento; sujeito a gate e política local | não | 4 | 0 |
| `d.difference_six` | expression | qualitative: diferença entre os dígitos explicitada; sujeito a gate e política local | não | 5 | 0 |
| `d.digit_pairs` | collection | qualitative: enumeração inequívoca dos pares; sujeito a gate e política local | não | 5 | 0 |
| `d.middle_choices` | expression ou collection | qualitative: enumeração/descrição explícita das escolhas centrais; sujeito a gate e política local | não | 3 | 0 |

O registry permite a rota; não promete que o gate concederá crédito a qualquer prosa. Nas obrigações de lista/contagem, uma alegação vaga de completude não substitui elementos escritos. Para as cadeias de b, o encaminhamento determinístico é apropriado: o baseline já as verifica após segmentação. Transformar automaticamente esse erro de adapter em um julgamento semântico esconderia a causa. Para prosa fiel que não possua representação suportada, a entrada SEMANTIC pode ser pertinente quando a política permitir; esses pilotos não exercitaram essa situação. Uma falha que represente refutação matemática, conflito ou contexto inválido não autoriza resgate semântico. A ausência de fallback é uma limitação explícita, não a causa primária demonstrada dos nove pontos de b.

## 6. Controles positivos: empates em c e d

Selecionados dois casos de c e dois de d. Todos têm contexto aceito, projeções atribuíveis/canônicas, nenhum conflito e nenhuma incerteza técnica. As falhas de critérios alternativos não invalidam os créditos independentes.

### c_complete: 6 = 6

[pilot_current_01/c_complete.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01/c_complete.json); [pilot_semantic_formal_01/c_complete.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/c_complete.json).

| obrigação | evidência → claim/payload | rota | status | suficiente | crédito efetivo |
|---|---|---|---|---|---|
| `c.uses_expression` | `E002:claim:e0d77e33eac7fc8bcb80`: `D=99(a-c).` → `D=99(a-c)` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | c.expression=1 pt (bloco) |
| `c.difference_domain` | `E003:claim:c450b199e47613557e8d`: `1<=c.` → `1<=c`<br>`E004:claim:715eed219adaa305e596`: `a<=9.` → `a<=9`<br>`E005:claim:03488b802f30e578ebb1`: `a>c.` → `a>c`<br>`E006:claim:4d6dbb031b526c82f33b`: `(a-c) ∈ {1,2,3,4,5,6,7,8}` → `(a-c) ∈ {1,2,3,4,5,6,7,8}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | c.domain=1 pt (bloco) |
| `c.complete_list` | `E007:claim:3ad35927740d10ff3466`: `D ∈ {99,198,297,396,495,594,693,792}` → `D ∈ {99,198,297,396,495,594,693,792}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | c.list.full=4 pt (bloco) |
| `c.no_extraneous_values` | `E007:claim:3ad35927740d10ff3466`: `D ∈ {99,198,297,396,495,594,693,792}` → `D ∈ {99,198,297,396,495,594,693,792}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | c.list.full=4 pt (bloco) |
| `c.single_list_error` | `E007:claim:3ad35927740d10ff3466`: `D ∈ {99,198,297,396,495,594,693,792}` → `D ∈ {99,198,297,396,495,594,693,792}` | DETERMINISTIC | DETERMINISTIC_FAILED | False | 0 pt; nenhum bloco pago |
| `c.several_correct` | `E007:claim:3ad35927740d10ff3466`: `D ∈ {99,198,297,396,495,594,693,792}` → `D ∈ {99,198,297,396,495,594,693,792}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | 0 pt; nenhum bloco pago |
| `c.some_correct` | `E007:claim:3ad35927740d10ff3466`: `D ∈ {99,198,297,396,495,594,693,792}` → `D ∈ {99,198,297,396,495,594,693,792}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | 0 pt; nenhum bloco pago |
| `c.pattern_recognized` | `E002:claim:e0d77e33eac7fc8bcb80`: `D=99(a-c).` → `D=99(a-c)`<br>`E007:claim:3ad35927740d10ff3466`: `D ∈ {99,198,297,396,495,594,693,792}` → `D ∈ {99,198,297,396,495,594,693,792}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | 0 pt; nenhum bloco pago |

Fluxo correto: fórmula (1), domínio a partir de três desigualdades e coleção (1), lista exata (4) = 6. `c.single_list_error` é refutado porque a lista não contém erro; não se acumula a faixa alternativa com os 4 pontos da lista completa.

### c_one_omission: 4 = 4

[pilot_current_01/c_one_omission.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01/c_one_omission.json); [pilot_semantic_formal_01/c_one_omission.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/c_one_omission.json).

| obrigação | evidência → claim/payload | rota | status | suficiente | crédito efetivo |
|---|---|---|---|---|---|
| `c.uses_expression` | `E002:claim:0596e21dcbcbe5611175`: `D=99(a-c).` → `D=99(a-c)` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | c.expression=1 pt (bloco) |
| `c.complete_list` | `E003:claim:2b5147b988dc38086322`: `D ∈ {99,198,297,396,495,594,693}` → `D ∈ {99,198,297,396,495,594,693}` | DETERMINISTIC | DETERMINISTIC_FAILED | False | 0 pt; nenhum bloco pago |
| `c.no_extraneous_values` | `E003:claim:2b5147b988dc38086322`: `D ∈ {99,198,297,396,495,594,693}` → `D ∈ {99,198,297,396,495,594,693}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | 0 pt; nenhum bloco pago |
| `c.single_list_error` | `E003:claim:2b5147b988dc38086322`: `D ∈ {99,198,297,396,495,594,693}` → `D ∈ {99,198,297,396,495,594,693}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | c.list.one_error=3 pt (bloco) |
| `c.several_correct` | `E003:claim:2b5147b988dc38086322`: `D ∈ {99,198,297,396,495,594,693}` → `D ∈ {99,198,297,396,495,594,693}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | 0 pt; nenhum bloco pago |
| `c.some_correct` | `E003:claim:2b5147b988dc38086322`: `D ∈ {99,198,297,396,495,594,693}` → `D ∈ {99,198,297,396,495,594,693}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | 0 pt; nenhum bloco pago |
| `c.pattern_recognized` | `E002:claim:0596e21dcbcbe5611175`: `D=99(a-c).` → `D=99(a-c)`<br>`E003:claim:2b5147b988dc38086322`: `D ∈ {99,198,297,396,495,594,693}` → `D ∈ {99,198,297,396,495,594,693}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | 0 pt; nenhum bloco pago |

Fluxo correto: fórmula (1) + exatamente uma omissão na lista (3) = 4. `c.complete_list` é refutado, enquanto a faixa `c.list.one_error` é satisfeita. Domínio não escrito não recebe crédito. A redução é igual à do baseline, não uma regressão C1.

### d_complete: 6 = 6

[pilot_current_01/d_complete.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01/d_complete.json); [pilot_semantic_formal_01/d_complete.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/d_complete.json).

| obrigação | evidência → claim/payload | rota | status | suficiente | crédito efetivo |
|---|---|---|---|---|---|
| `d.equation` | `E002:claim:ec19d2274d0e60ab77b9`: `99(a-c)=594.` → `99(a-c)=594` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | d.solve=2 pt (bloco) |
| `d.difference_six` | `E003:claim:1dddb387745499405e0b`: `a-c=6.` → `a-c=6` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | d.solve=2 pt (bloco) |
| `d.digit_pairs` | `E004:claim:6beeb5582745772c6675`: `(a,c) ∈ {(7,1),(8,2),(9,3)}` → `(a,c) ∈ {(7,1),(8,2),(9,3)}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | d.pairs=2 pt (bloco) |
| `d.middle_choices` | `E005:claim:d3d554ef3c11f2178fa1`: `b ∈ {0,1,2,3,4,5,6,7,8,9}` → `b ∈ {0,1,2,3,4,5,6,7,8,9}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | d.count=2 pt (bloco) |
| `d.total_thirty` | `E006:claim:e248a11e5e515ae6da4f`: `3*10=30.` → `3*10=30` | FORMAL | FORMAL_VERIFIED | True | d.count=2 pt (bloco) |

Fluxo correto: `d.solve` (equação + diferença, 2), pares (2), `d.count` (escolhas + total, 2) = 6. Payload Lean efetivo: `{"left_expr":"3*10","right_expr":"30"}`; proposição `((3 : ℤ)*10) = ((30 : ℤ))`; `compiled=true`, `formal_status=verified`, stdout/stderr vazios. Pré-requisitos vinculados: `["E004:claim:6beeb5582745772c6675","E005:claim:d3d554ef3c11f2178fa1"]`. Certificado já existente: [Lean](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/student_claim_checks/tme-semantic-formal-c1-a2267a5e79764be381ab268868d22ed1/student_claim_check_0.lean).

### d_no_count: 4 = 4

[pilot_current_01/d_no_count.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01/d_no_count.json); [pilot_semantic_formal_01/d_no_count.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01/d_no_count.json).

| obrigação | evidência → claim/payload | rota | status | suficiente | crédito efetivo |
|---|---|---|---|---|---|
| `d.equation` | `E002:claim:9604e96d076d4b9fa8a5`: `99(a-c)=594.` → `99(a-c)=594` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | d.solve=2 pt (bloco) |
| `d.difference_six` | `E003:claim:641963dc8df1aac85338`: `a-c=6.` → `a-c=6` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | d.solve=2 pt (bloco) |
| `d.digit_pairs` | `E004:claim:f0f5af8560dd04bf612e`: `(a,c) ∈ {(7,1),(8,2),(9,3)}` → `(a,c) ∈ {(7,1),(8,2),(9,3)}` | DETERMINISTIC | DETERMINISTIC_VERIFIED | True | d.pairs=2 pt (bloco) |

Fluxo correto: `d.solve` (2) + pares (2) = 4. O extractor não inventa escolhas de b nem produto; não há rota FORMAL sintetizada para obrigação não candidata. `d.count` permanece sem crédito. Controle de preservação de evidência parcial, sem exigir a solução inteira.

**Controle adicional isolando o adapter de b:** `b_no_factorization` mantém 4→4 porque seu payload termina em uma única igualdade `(...)-(...)=99a-99c`, aceito pelo mesmo parser/checker. A única diferença estrutural relevante frente à cadeia regressiva é o segundo “=”. Isso corrobora a causa de representação sem reexecutar nenhum caso.

## 7. REVIEW_RECOMMENDED: 20/21 → 21/21

A política efetiva é `review_recommended = argumento explícito OR technical_uncertainty OR assessment.needs_review`. O argumento explícito C1 vale true se houver conflito ou mapeamento rejeitado. `ScoreClosurePolicy.applied=false` em **42/42** resultados; nenhum score era None e nenhum erro técnico foi encontrado. Logo, o fechamento numérico não criou estas revisões.

O `PautaEngine` avalia a pauta inteira P1 mesmo quando o caso contém um único item. Os demais itens ficam sem evidência, com intervalo de pontuação aberto; `needs_review` é o OR dos itens. Isso explica a taxa alta nos dois modos, inclusive casos completos de um item.

| causa / indicador | Current | C1 | interpretação |
|---|---|---|---|
| assessment.needs_review | 20 | 21 | Todos os flags finais já estavam presentes no assessment |
| Ao menos um item ausente com needs_review | 20 | 20 | Herdado da pauta integral em fixtures de um único item |
| Ao menos um item presente com needs_review | 13 | 17 | Evidência parcial/indeterminada; +a_complete, b_complete, b_equivalent_algebra, p1_complete_regression |
| ScoreClosure aplicado (score original None) | 0 | 0 | Não causa revisões neste piloto |
| Erro técnico | 0 | 0 | Não causa revisões |
| Conflitos | 0 | 0 | Não causa revisões |
| Caso com mapeamento rejeitado explícito | 0 | 1 | a_complete; flag redundante com assessment.needs_review |
| Casos com FORMAL_UNPROVED | 0 | 5 | Afetam evidência/intervalos; não são um gatilho direto independente |
| Revisão exclusivamente nova no caso composto | 0 | 1 | p1_complete_regression: b passou a indeterminado por cadeia não segmentada |

As contagens de causas se sobrepõem; não devem ser somadas. Em `d_later_error`, o item d fica decidido apesar do FORMAL_UNPROVED, porque os pré-requisitos refutados já impedem os blocos restantes; a revisão global decorre dos itens a/b/c ausentes. Portanto UNPROVED não implica, isoladamente, revisão nem erro técnico.

| caso | review Current | itens causadores Current | review C1 | itens causadores C1 |
|---|---|---|---|---|
| a_complete | True | b (ausente), c (ausente), d (ausente) | True | a (presente), b (ausente), c (ausente), d (ausente) |
| a_no_evidence | True | a (presente), b (ausente), c (ausente), d (ausente) | True | a (presente), b (ausente), c (ausente), d (ausente) |
| a_only_inverse | True | a (presente), b (ausente), c (ausente), d (ausente) | True | a (presente), b (ausente), c (ausente), d (ausente) |
| a_only_result | True | a (presente), b (ausente), c (ausente), d (ausente) | True | a (presente), b (ausente), c (ausente), d (ausente) |
| a_single_arithmetic_error | True | b (ausente), c (ausente), d (ausente) | True | b (ausente), c (ausente), d (ausente) |
| a_wrong_setup | True | a (presente), b (ausente), c (ausente), d (ausente) | True | a (presente), b (ausente), c (ausente), d (ausente) |
| b_complete | True | a (ausente), c (ausente), d (ausente) | True | a (ausente), b (presente), c (ausente), d (ausente) |
| b_equivalent_algebra | True | a (ausente), c (ausente), d (ausente) | True | a (ausente), b (presente), c (ausente), d (ausente) |
| b_no_factorization | True | a (ausente), b (presente), c (ausente), d (ausente) | True | a (ausente), b (presente), c (ausente), d (ausente) |
| b_only_expression | True | a (ausente), b (presente), c (ausente), d (ausente) | True | a (ausente), b (presente), c (ausente), d (ausente) |
| c_complete | True | a (ausente), b (ausente), d (ausente) | True | a (ausente), b (ausente), d (ausente) |
| c_few_results | True | a (ausente), b (ausente), c (presente), d (ausente) | True | a (ausente), b (ausente), c (presente), d (ausente) |
| c_no_evidence | True | a (ausente), b (ausente), c (presente), d (ausente) | True | a (ausente), b (ausente), c (presente), d (ausente) |
| c_one_extraneous | True | a (ausente), b (ausente), c (presente), d (ausente) | True | a (ausente), b (ausente), c (presente), d (ausente) |
| c_one_omission | True | a (ausente), b (ausente), c (presente), d (ausente) | True | a (ausente), b (ausente), c (presente), d (ausente) |
| c_several_with_pattern | True | a (ausente), b (ausente), c (presente), d (ausente) | True | a (ausente), b (ausente), c (presente), d (ausente) |
| d_complete | True | a (ausente), b (ausente), c (ausente) | True | a (ausente), b (ausente), c (ausente) |
| d_later_error | True | a (ausente), b (ausente), c (ausente) | True | a (ausente), b (ausente), c (ausente) |
| d_no_count | True | a (ausente), b (ausente), c (ausente), d (presente) | True | a (ausente), b (ausente), c (ausente), d (presente) |
| d_only_difference_then_error | True | a (ausente), b (ausente), c (ausente), d (presente) | True | a (ausente), b (ausente), c (ausente), d (presente) |
| p1_complete_regression | False | nenhum | True | b (presente) |

Referências: [PautaEngine: agregação de needs_review](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/rubric/pauta/engine.py:57); [intervalo incerto determina revisão](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/rubric/pauta/engine.py:89); [ScoreClosurePolicy: OR de flags](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/experimental/tme_semantic_formal/score_closure.py:8); [engine C1: conflitos/mapeamentos rejeitados](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/app/confia_lean_auditor/experimental/tme_semantic_formal/engine.py:133).

## 8. Root causes

Ocorrência primária é um incidente por caso; “linhas” mede resultados/obrigações afetadas. Os pontos desta tabela são incrementais contra Current e não duplicam os grupos G1…G8.

| causa | número de ocorrências | obrigações afetadas | pontos afetados | gravidade |
|---|---|---|---|---|
| CHECKER_REPRESENTATION_MISMATCH — adapter não segmenta cadeia | 3 claims/casos; 9 resultados FAILED | b.subtraction, b.middle_cancellation, b.factorization | 9 perdidos (3×3) | Alta; bloqueante |
| ROUTER_ERROR — sugestão única FORMAL inviabiliza vínculos D | 1 caso; 3 rejeições, 2 sobre obrigações com suporte baseline | a.identifies_137, a.constructs_subtraction; rejeição extra a.arithmetic_error_only | 3 perdidos conjuntamente | Alta; bloqueante |
| OBLIGATION_MAPPING_ERROR — 137 associado ao resultado, fato válido filtrado | 1 caso; 1 obrigação correta omitida e 1 vínculo incorreto | a.identifies_137 / a.result_594 | 1 perdido | Alta; bloqueante |
| Candidatos amplos/ausência de fato contabilizada como FAILED | 6 resultados adicionais sem suporte; 4 casos | a.identifies_137, a.constructs_subtraction, a.arithmetic_error_only, b.factorization | 0 adicionais | Média; interpretação de métricas |
| FORMAL_UNPROVED antes de executar Lean | 5 resultados/casos; inclui o erro de mapping acima | a.result_594 (3), d.total_thirty (2) | 0 adicionais além do 1 já atribuído ao mapping | Média; cobertura/observabilidade |
| SEMANTIC não exercitado | 0 qualitative entre 54 evidências; 21 gates skipped | 19 obrigações D/S sem teste em prosa substantiva | 0 demonstrados | Lacuna de validação, não defeito comprovado |
| Review por pauta inteira e itens ausentes | 20 casos por modo; 1 revisão global nova por b no composto | itens ausentes; b no caso composto | 0 adicionais | Baixa para score; média para leitura da métrica |

Categorias não demonstradas como causas das perdas: NORMALIZATION_ERROR, SUFFICIENCY_TOO_STRICT, CONFLICT, AWARD_GATE_ERROR e DOUBLE_COUNT_PROTECTION_ERROR. Não houve contaminação entre itens, source_span inexistente, falha de API/fallback ou erro de infraestrutura nos artefatos auditados. A etiqueta CONTEXT_REJECTED em a_complete é consequência da classificação genérica da exceção de rota, não evidência de contexto indevido do aluno.

## 9. Recomendações (somente após a demonstração; não implementadas)

### Necessárias antes de novo piloto

1. **Restaurar compatibilidade de representação no adapter:** conservar cadeia e origem, mas produzir as igualdades adjacentes já escritas, com vínculos/offsets corretos, como o baseline faz. Não inventar igualdade de extremos nem passos ausentes. Cobrir as duas notações de b e o caso composto com regressões derivadas destes artefatos.
2. **Revisar o contrato de sugestão de rota por evidência:** uma evidência pode apoiar obrigações determinísticas e formais simultaneamente. A rota efetiva deve continuar restrita por obrigação; uma sugestão formal não deve apagar fatos determinísticos válidos de outra obrigação. Preservar a proibição de enviar obrigações não suportadas ao Lean.
3. **Validar pertinência por obrigação com conteúdo/fatos:** o literal 137 deve poder vincular-se à identificação quando o checker existente já a verifica. A lista proposta pelo LLM não deve ser o único mecanismo que decide quais fatos válidos são visíveis. Qualquer recuperação precisa manter origem, contexto e traço explícito; não substituir silenciosamente toda a linha C1 pelo baseline.
4. **Distinguir evidência não aplicável de prova tentada sem sucesso no diagnóstico:** manter FORMAL_UNPROVED distinto de refutação/erro, mas tornar legível se houve chamada Lean, qual precondição falhou e qual payload foi usado. Os cinco casos mostram por que a métrica atual, isolada, induz a diagnóstico incorreto.
5. Após correções autorizadas, validar primeiro regressões direcionadas de G1…G8 e preservação dos controles positivos; somente então executar novo piloto P1 comparável. Não há evidência para avançar a P2 agora.

### Desejáveis, não bloqueantes para corrigir as perdas demonstradas

- Acrescentar controles DEV de prosa matemática para exercer SEMANTIC e sua suficiência independente. O piloto atual não mede essa capacidade.
- Separar nas métricas `DETERMINISTIC_FAILED` por refutação real, ausência de fato, erro de representação e candidato não pertinente; distinguir rotas nominais de execuções Lean.
- Relatar motivos de review e separar revisão do item respondido da revisão global por itens ausentes, mantendo a política histórica até decisão explícita.
- Refinar sugestões amplas como arithmetic_error_only em cálculo correto e factorization sem passo fatorado; são ruído diagnóstico, não origem adicional de perda aqui.
- Documentar se haverá algum fallback D→S para prosa não representável. Não usá-lo como atalho para cadeias matemáticas suportadas, refutações ou conflito.

### Pontos que não devem ser modificados com base nesta auditoria

- Checkers matemáticos/Lean, pauta e valores de pontos: a evidência aponta para contratos anteriores ao checker, não para matemática ou faixas incorretas.
- Whitelist formal de apenas a.result_594 e d.total_thirty; não formalizar b para contornar a perda do adapter.
- Distinção entre VERIFIED, REFUTED, UNPROVED e ERROR; não promover literal 594/30 ou opinião semântica a prova formal.
- Pré-requisitos de d.total_thirty, controles de fonte/contexto, veto a conflitos e proteção de dupla contagem.
- Política de não usar gold, baseline como comparador e não como resposta oculta, holdout selado e isolamento de TME_CURRENT.
- Créditos parciais dos controles c/d e a regra de não inferir passos ausentes.

## 10. Veredito

**FIX_AND_RERUN_P1.** Os três mecanismos observados explicam integralmente os 13 pontos perdidos e são localizados nos contratos de roteamento/mapeamento/projeção. Os controles c/d e as provas Lean existentes funcionam. Não há fundamento nestes dados para redesenho arquitetural completo; tampouco há base para READY_FOR_P2. A rota semântica ainda não foi exercitada por prosa substantiva. Nenhuma recomendação foi aplicada nesta tarefa.

## 11. Integridade e estado final

HEAD: `6fe808fa693b7e0d662dd49c498e6b575dd9d47f`. Estado inicial limpo. Os 46 JSON dos dois pilotos e os 13 arquivos Python experimentais/runner foram protegidos por snapshot SHA-256 e permaneceram intactos. `git diff --exit-code` e `git diff --cached --exit-code` não apontam alterações em arquivos versionados. Nenhum novo piloto/artefato de avaliação foi criado; somente este relatório foi adicionado no worktree.

```text
?? docs/audits/TME_SEMANTIC_FORMAL_C1_FORENSIC_01.md
```

A auditoria reconstrói execuções já registradas; não mediu novamente a API, não gerou novos certificados e não testou contrafactuais de correção. As recomendações não constituem demonstração de recuperação até uma validação futura autorizada.
