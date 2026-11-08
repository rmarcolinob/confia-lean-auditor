# TME P3 — Semantic Safety 03: auditoria forense

**MULTI_LAYER_ROOT_CAUSE. Recomendação: MULTI_LAYER_FIX_REQUIRED.** Não foi encontrado checker matemático errado nos seis casos examinados. O falso crédito A05 resulta de uma contradição ativa preservada no texto, mas sem representação executável e reclassificada como AMBIGUOUS; o outro claim, verdadeiro, recebe crédito isoladamente. Os cinco falsos vetos resultam de matemática corretamente refutada sobre conteúdo retirado ou de terceiro, promovido indevidamente a posição ACTIVE. Há ainda erros específicos de segmentação temporal e de reconhecimento de quantidade.

A hipótese de uma única projeção de “claim errado sobre obrigação verdadeira” **não explica A05**: seu witness positivo corresponde exatamente a uma afirmação escrita e à obrigação correta. O defeito comum é conceder autoridade sem assegurar a integridade do contexto discursivo da obrigação; os mecanismos de falha são diferentes.

## 1. Escopo, base e método somente leitura

Avaliação inspecionada: SHA `6fb07d4d15626e27b7c759a4e32f9cb3b415d2ea`. HEAD desta auditoria: `8c85ea67f2ba07b68e433e0dbf6ddf0668390958`, commit que registra Safety03; worktree inicialmente limpo. A implementação, os cinco arquivos congelados e os artefatos originais conferem com os hashes já registrados. A análise leu JSON, código e pauta; não chamou API, extractor, mapper, resolver, checkers, Lean ou modos de avaliação novamente. As explicações de fluxo são inferências estáticas ancoradas nos ranges/receipts gravados, não novos resultados experimentais.

O escopo causal é A05, B02, B04, B05, B08 e E01. Os três fallbacks são examinados separadamente. Este documento é o único novo arquivo no repositório. Nenhum relatório anterior, artifact, fixture, expectation, prompt, pauta ou código foi reescrito; sem commit. Não foi criado Safety04 nem implementado P4.

Safety03 passa a **OBSERVED FAILURE / REGRESSION DATASET**. O veredito histórico P3_SAFETY_FAILURE é mantido.

Fontes de referência: [relatório da avaliação](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_SEMANTIC_SAFETY_03.md); [expectativas congeladas](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_03/expectations.json); [hashes do congelamento](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/freeze_receipt.json); [integridade da avaliação](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/final_integrity.json). Todos os offsets abaixo são intervalos [início,fim) em codepoints da fonte original; não são offsets UTF-16 de editor. IDs completos permitem localizar cada cadeia no JSON correspondente.

## 2. A05 — reconstrução integral dos 2 pontos

```text
b) Minha lista fechada de compartimentos que dão branca ao repetir é {6}. Acrescento uma afirmação que também considero válida: repetir o compartimento 3 dá branca.
```

[p3_s03_a05: artefato original](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_a05.json).

### 2.1 Source → EvidenceUnit → payload → estado

As duas EvidenceUnits vêm de `E002`, envelope literal [3,164). Seus conteúdos são distintos, completos e localizáveis. `source_sha256` = `db8aa4d74053445f7a37a73b08b4571fea1841bbe294c98d481af99a2eda7ff5`.

**`E002:p3:1a9b2549534ea20bd788`**

- Asserted content: `Minha lista fechada de compartimentos que dão branca ao repetir é {6}.`
- Clause/assertion range: `[3, 73]` / `[3, 73]`.
- Tipo/subject: `integer_set` / `repeticao_branca`; obligation_candidates: `['b.same_compartment']`.
- Payload original e adaptado: `{6}` → `{6}`; adaptation=`identity`, changed=false.
- Modelo: assertion_status=asserted, polarity=positive, scope=main_argument, abandoned=false, hypothetical=false, attributed_to_student=true; route_candidate=DETERMINISTIC, confidence=1.0.
- Resolver: `ACTIVE`, reason=`literal_own_assertion`, binding_valid=true, property_key=`['b', 'repeticao_branca']`, positive_credit_eligibility=true, conflict_visible=true.

**`E002:p3:962f452cebaf26ae3f12`**

- Asserted content: `Acrescento uma afirmação que também considero válida: repetir o compartimento 3 dá branca.`
- Clause/assertion range: `[74, 164]` / `[74, 164]`.
- Tipo/subject: `qualitative` / `unmapped`; obligation_candidates: `['b.same_compartment']`.
- Payload original e adaptado: `repetir o compartimento 3 dá branca.` → `repetir o compartimento 3 dá branca.`; adaptation=`identity`, changed=false.
- Modelo: assertion_status=asserted, polarity=positive, scope=main_argument, abandoned=false, hypothetical=false, attributed_to_student=true; route_candidate=SEMANTIC, confidence=0.92.
- Resolver: `AMBIGUOUS`, reason=`unresolved_property_binding`, binding_valid=true, property_key=`['b', 'unmapped']`, positive_credit_eligibility=false, conflict_visible=true.

O estado da primeira evidência está correto. A segunda é inequivocamente adotada (“também considero válida”), portanto deveria conservar adoção ACTIVE, mesmo sendo não representável. `unresolved_property_binding` é incerteza de representação; aqui foi transformada em incerteza de adoção. O texto negativo não sumiu da extração nem do ledger: desapareceu **da verificação matemática e da reconciliação com autoridade**.

### 2.2 Mapping → checker → componentes → sufficiency

| Evidência | Mapping/rota efetiva | Verificação real | Componentes | Sufficiency |
| --- | --- | --- | --- | --- |
| `E002:p3:1a9b2549534ea20bd788` | accepted=true; `compatible_pending_checker`; `DETERMINISTIC` | `DETERMINISTIC_VERIFIED`; `tme2-p3-check.v1:2c145837f30d65f13a1d` | `[]` | `{'sufficient': True, 'policy': 'frozen_checker_first_with_result_method_separation', 'basis': 'frozen_P3_checker_and_validated_binding'}` |
| `E002:p3:962f452cebaf26ae3f12` | accepted=false; `discourse_ambiguous`; `DETERMINISTIC` | `CONTEXT_REJECTED`; `None` | `[]` | `{'sufficient': False, 'basis': 'no_eligible_checker_result'}` |

O primeiro checker é `tme2-p3-check.v1`, regra `_b`: compara o conjunto escrito `{6}` com `same_compartment_favorable=[6]`. A comparação é correta e não usa Lean: FORMAL_NOT_ATTEMPTED; `subchecks=[]`, sem componentes compostos inventados. O enunciado “lista fechada ... {6}” é realmente exaustivo, portanto o payload não ampliou uma inclusão parcial para conjunto completo.

O segundo registro recebe CONTEXT_REJECTED; isso é um recibo de rejeição de mapping, **não execução de checker nem refutação matemática**. Não há verification_id, original_fact ou componente matemático para a inclusão do 3. A route_candidate SEMANTIC sugerida pelo modelo não tem autoridade e não cria checker semântico; a rota efetiva continua a da obrigação, DETERMINISTIC.

O produtor `native_checker` também verifica o primeiro claim e rejeita o segundo; não recupera um negativo adicional. Atomic/structural guards produzem zero resultados. `member_atom` exige, em b, subject `repeticao_branca` e a gramática estreita de índice seguido por “também”; o texto “repetir o compartimento 3 dá branca” não a satisfaz, além de vir como `unmapped`. Apenas substituir `unmapped` por `{3}` seria incorreto: converteria inclusão em exclusividade.

### 2.3 Policy → reconciliation → award → pauta

- `veto:fbab0216c0d6afdce23ed43df594bf08bf9bd1685a60fbdcb165456c2b8a460a` — producer=positive_checker, checker_ref=`tme2-p3-check.v1:2c145837f30d65f13a1d`, status=DETERMINISTIC_VERIFIED; mathematical_contradiction=false, hard_veto_eligible=false, reason=`checker_not_refutation`, reconciliation_status=NOT_APPLICABLE.
- `veto:2c7980ea25fe6ff5201248abccbc7b34c58cbceeddc2bc926925f9331a990625` — producer=native_checker, checker_ref=`tme2-p3-check.v1:cda578d38bf2cb1adaec`, status=DETERMINISTIC_VERIFIED; mathematical_contradiction=false, hard_veto_eligible=false, reason=`checker_not_refutation`, reconciliation_status=NOT_APPLICABLE.

Não há candidato de veto da inclusão falsa, pois a orquestração só emite candidatos com original_fact ou guard_id. `conflicts=[]`. O award de `b.same_compartment` seleciona `tme2-p3-check.v1:2c145837f30d65f13a1d`; decision=`verified_and_sufficient`, eligible=true, sufficient=true. Receipt ligado à ledger_revision `620d674688ac3c44fb860368433ff8428b1bbf8aea78a47b2576c9ce877ee022`.

A pauta aplica `b.same`, all_of de `b.same_compartment`, **2 pontos**; b.counting é a soma das quatro parcelas e o item b usa max_of com b.alternative. Nenhuma outra parcela foi concedida. O mecanismo executou a regra existente; o problema é o suporte incompleto/contraditório entregue à regra, não soma errada ou mudança de peso. `review_recommended=true` já estava presente, mas não bloqueou o award.

### 2.4 Perguntas causais de A05

| Pergunta | Conclusão sustentada pelos artefatos |
| --- | --- |
| Qual obrigação/qual escrita? | b.same_compartment / “Minha lista fechada ... {6}”, via b.same=2 |
| A escrita pertence à obrigação? | Sim: repetição no mesmo compartimento, item b; não houve troca de item ou propriedade no witness pago |
| Payload incorretamente normalizado? | Não: `{6}` foi preservado; a inclusão negativa permanece em prosa, sem fabricação numérica |
| Binding incorreto? | Binding literal do positivo é íntegro. Falta ligação executável da inclusão do 3 à mesma propriedade; não há deslocamento de bytes no negativo |
| Estado incorreto? | Sim: inclusão ativamente adotada → AMBIGUOUS por falha de propriedade; não é ambiguidade discursiva real |
| Checker provou outra proposição verdadeira? | Não no witness pago: verificou exatamente o conjunto escrito. Não verificou a consistência do conjunto com a outra afirmação adotada |
| Resultado virou justificativa inexistente? | Não: b.same admite o conjunto exaustivo; não é claim de produto/argumento que exigisse componentes ausentes |
| Negativo omitido? | Não da fonte/extração; sim da trilha executável de refutação/conflito |
| Expectation errada? | Não há evidência disso: repetir 3 libera preta, a lista exaustiva exclui 3, e o aluno sustenta ambas sem retirar uma |

Classificação primária: **DISCOURSE_STATE_ERROR**; contribuição de **SUBJECT_ERROR** no sentido de propriedade não representada (`unmapped`, com obligation hint correto) e **OTHER — cobertura negativa e suficiência de contexto para autoridade**. Não se demonstra EXTRACTION_ERROR de omissão literal: o prompt permite `qualitative/unmapped` para representação sem contrato. Não há evidência de SOURCE_BINDING_ERROR de offsets, PAYLOAD_NORMALIZATION_ERROR, CHECKER_SCOPE_ERROR matemático, RUBRIC_POLICY_ERROR ou EXPECTATION_ERROR no witness positivo. RECONCILIATION_ERROR não é um bypass: a reconciliação não recebeu negativo verificável. O sentido amplo de SUFFICIENCY_ERROR é a lacuna de integridade contextual; não uma justificativa inventada pelo checker local.

Referências de implementação: [contrato qualitative/unmapped](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/extractor.py:39); [member_atom](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/source_adapter.py:39); [adoção condicionada à propriedade](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/discourse.py:122); [candidatos apenas de facts/guards](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/unified.py:64); [admissão de award](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:33).

## 3. Cinco falsos vetos — mapa de perdas

| Caso | Obrigação / regra | Pontos previstos afetados | Positivo final verificado e suficiente já existe? | Causa principal |
| --- | --- | ---: | --- | --- |
| B02 | a.first_white_probability / a.probability | 2 | Sim, Lean real | Segmentação após fração apaga ordem temporal |
| B04 | c.continue_compartments / c.continue | 1 | Sim, determinístico | Retifico não reconhecido como revisão |
| B05 | b.second_white_probability / b.conclusion | 2 | Sim, composto de resultado | Ranges sobrepostos e ato de invalidação não reconhecido |
| B08 | a.bottom_white_count / a.count | 2 | Não: resultado final rejeitado por representação | Gramática de quantidade impede reconhecer valor final/revisão |
| E01 | a.first_white_probability / a.probability | 2 | Sim, determinístico | Citação sem adesão convertida em assertiva própria |
| Total | 5 obrigações em 5 casos | 9 | 7 pontos com witness pronto; 2 com causa concorrente | — |

**9 pontos afetados não equivalem a 9 recuperáveis apenas removendo receipts.** B08 também não tem witness suficiente. E01 perde ainda 2 de a.count por representação; esses 2 **não** pertencem aos 9 de falso veto. Em B04, c.total é bloqueada pela dependência contratada, mas não há solução de total no texto: não acrescenta pontos perdidos.

Nos cinco casos, os dois produtores `positive_checker` e `native_checker` refutam a mesma proposição antiga/citada. São dois receipts, não duas penalidades. `native_checker` verifica as views já resolvidas, inclusive as unidades semânticas; nos seis casos o ledger não contém unidade com extractor_model=native. Os dois negativos usam os mesmos IDs E002:p3, portanto sua concordância não constitui validação independente de adoção ou autoria. Todos chegam a hard_veto_eligible=true, `active_checked_contradiction`, status APPLIED e conflito `central_policy_active_contradiction`. Não há bypass. A mathematical contradiction é verdadeira para o conteúdo numérico/conjunto recebido; o erro é sua autoridade atual.

### 3.1. B02

```text
a) Minha chance de branca na primeira retirada era 1/2. Refaço a conta e substituo essa chance por primeira_branca: 2/6=1/3.
```

[p3_s03_b02: artefato original](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b02.json).

| EvidenceUnit | Asserted content / payload | Ranges assertion → source | Modelo → resolver | Mapping / checker / sufficiency |
| --- | --- | --- | --- | --- |
| `E002:p3:2dec75da6b1471ac7edc` / `primeira_branca` | Minha chance de branca na primeira retirada era 1/2.<br>payload=`1/2` | `[3, 55]` → `[3, 55]` | abandoned; abandoned=true; attributed=true; polarity=positive → ACTIVE/literal_own_assertion | a.first_white_probability: compatible_pending_checker; DETERMINISTIC_FAILED (tme2-p3-check.v1:b6df3bca1884daea3400); sufficient=False |
| `E002:p3:742b61b2c46c52fc2821` / `primeira_branca` | Refaço a conta e substituo essa chance por primeira_branca: 2/6=1/3.<br>payload=`2/6=1/3` | `[56, 124]` → `[3, 124]` | asserted; abandoned=false; attributed=true; polarity=positive → ACTIVE/literal_own_assertion | a.first_white_probability: compatible_pending_checker; FORMAL_VERIFIED (tme2-p3-check.v1:de9c051e4e42add61152); sufficient=True |

Todas as decisões acima têm binding_valid=true, positive_credit_eligibility=true e conflict_visible=true no snapshot gravado. Isso descreve a autoridade **atribuída pela implementação**, não a autoridade devida à fonte. Nenhuma possui superseded_by ou supporting_spans de correção. Os payloads originais e adaptados são iguais.

| Produtor / evidence | Checker ref | Policy receipt | Targets / resultado |
| --- | --- | --- | --- |
| positive_checker / `E002:p3:2dec75da6b1471ac7edc` | `tme2-p3-check.v1:b6df3bca1884daea3400` | `veto:9765844819b0d90c926bda33fbcd34241a3268d951d1d1df6aed47c29f4b6de3` | `['a.first_white_probability']`; DETERMINISTIC_FAILED; hard=true; APPLIED |
| native_checker / `E002:p3:2dec75da6b1471ac7edc` | `tme2-p3-check.v1:632bd1437a5321219692` | `veto:d150e26bc06652497009661e9bb8f8c3a5b325f64ced14448c46b437c005978d` | `['a.first_white_probability']`; DETERMINISTIC_FAILED; hard=true; APPLIED |

**Causa precisa.** O modelo identifica corretamente a primeira chance como abandoned=true e a nova como final_conclusion. O assert antigo termina em `1/2.`. A regex de `clause_view`, `(?<!\d)[.!?](?!\d)`, ignora ponto precedido por dígito, inclusive ponto final depois de uma fração. Para a correção, assertion_range=[56,124), mas source_range=[3,124); para a antiga, [3,55). Logo, ambos os source_range começam em 3. O resolver seleciona predecessores exigindo início estritamente menor; a antiga não pode ser predecessora da nova. O marcador “substituo” não é o primeiro bloqueador: a etapa de seleção temporal falha antes. A afirmação final está corretamente escrita e matematicamente vinculada; o erro é o range usado para ordenar o discurso.

O checker antigo refuta 1/2 frente a 1/3 corretamente. O final **já foi provado em Lean**: `((2 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (3 : ℚ))`, método norm_num, compiled=true, stdout e stderr vazios. Isso prova a igualdade escrita; não prova que a posição antiga permanece adotada. O falso veto derrota um witness formal verdadeiro por um estado discursivo errado.

Classificação: **SOURCE_BINDING_ERROR (segmentação/contexto temporal, não bytes inválidos) + DISCOURSE_STATE_ERROR**. O crédito final é independente da posição retirada; pertence à mesma obrigação. Não há evidência de contaminação de outra obrigação neste caso.

Awards efetivamente bloqueados: `a.first_white_probability`. Todos os scores finais do caso são 0; `review_recommended=true`. O receipt do award cita os IDs de veto acima, mesma ledger_revision/source_sha256 do caso.

### 3.2. B04

```text
c) A indicação para continuar era o conjunto {1,4}. Retifico os compartimentos de continuação: continuar: {1,2}. Esta é a indicação definitiva.
```

[p3_s03_b04: artefato original](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b04.json).

| EvidenceUnit | Asserted content / payload | Ranges assertion → source | Modelo → resolver | Mapping / checker / sufficiency |
| --- | --- | --- | --- | --- |
| `E002:p3:ac1a8367f778d7220752` / `continuar` | A indicação para continuar era o conjunto {1,4}.<br>payload=`{1,4}` | `[3, 51]` → `[3, 51]` | abandoned; abandoned=true; attributed=true; polarity=positive → ACTIVE/literal_own_assertion | c.continue_compartments: compatible_pending_checker; DETERMINISTIC_FAILED (tme2-p3-check.v1:8402d984e7fff4228490); sufficient=False |
| `E002:p3:e87ee35ca4dcdaff47e4` / `continuar` | Retifico os compartimentos de continuação: continuar: {1,2}. Esta é a indicação definitiva.<br>payload=`{1,2}` | `[52, 143]` → `[52, 143]` | asserted; abandoned=false; attributed=true; polarity=positive → ACTIVE/literal_own_assertion | c.continue_compartments: compatible_pending_checker; DETERMINISTIC_VERIFIED (tme2-p3-check.v1:4c9cebfb06758f1f0a29); sufficient=True |

Todas as decisões acima têm binding_valid=true, positive_credit_eligibility=true e conflict_visible=true no snapshot gravado. Isso descreve a autoridade **atribuída pela implementação**, não a autoridade devida à fonte. Nenhuma possui superseded_by ou supporting_spans de correção. Os payloads originais e adaptados são iguais.

| Produtor / evidence | Checker ref | Policy receipt | Targets / resultado |
| --- | --- | --- | --- |
| positive_checker / `E002:p3:ac1a8367f778d7220752` | `tme2-p3-check.v1:8402d984e7fff4228490` | `veto:ef00282b95ef2cf42bb1416d39fe79a804ac90c45bd93a4c7d9ff4a3aa746f8f` | `['c.continue_compartments', 'c.total_win_probability']`; DETERMINISTIC_FAILED; hard=true; APPLIED |
| native_checker / `E002:p3:ac1a8367f778d7220752` | `tme2-p3-check.v1:7f3bc813c68ada156725` | `veto:a21aaca0b4ce88495d8ce187581779880b464f7e81428bfc2dcd3815e9aa5cf2` | `['c.continue_compartments', 'c.total_win_probability']`; DETERMINISTIC_FAILED; hard=true; APPLIED |

**Causa precisa.** Os ranges antigo [3,51) e final [52,143) preservam a ordem; ambos os payloads são representáveis. O modelo marcou o antigo abandoned=true. O resolver reconhece um conjunto limitado de atos como `corrigindo`, `substitu...` e `retiro`; `Retifico` não está no padrão e não há “na verdade”. A nova posição não supersede a antiga. `_context` devolve `literal_own_assertion`, a projeção reescreve abandoned para false, e a refutação de `{1,4}` torna-se negativa atual.

O checker compara `{1,4}` e `{1,2}` com o conjunto real de continuação `{1,2}`. As duas decisões matemáticas são corretas. O negativo antigo não deveria ter autoridade; a identificação final já é suficiente para c.continue=1. A propagação adicional a c.total segue dependência existente, não veto global; não há pontos de total escritos a recuperar.

Classificação: **DISCOURSE_STATE_ERROR**, reconhecimento de substituição incompleto. O crédito final não depende de validar a antiga posição; não se trata de outra obrigação independente indevidamente bloqueada.

Awards efetivamente bloqueados: `c.continue_compartments`, `c.total_win_probability`. Todos os scores finais do caso são 0; `review_recommended=true`. O receipt do award cita os IDs de veto acima, mesma ledger_revision/source_sha256 do caso.

### 3.3. B05

```text
b) A probabilidade da segunda branca ficou anotada como 7/36. Depois de conferir a partição, invalido esse valor e assino o resultado da segunda branca: 11/36.
```

[p3_s03_b05: artefato original](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b05.json).

| EvidenceUnit | Asserted content / payload | Ranges assertion → source | Modelo → resolver | Mapping / checker / sufficiency |
| --- | --- | --- | --- | --- |
| `E002:p3:66d44d0858d5c726aad2` / `segunda_branca` | A probabilidade da segunda branca ficou anotada como 7/36. Depois de conferir a partição, invalido esse valor<br>payload=`7/36` | `[3, 112]` → `[3, 159]` | abandoned; abandoned=true; attributed=true; polarity=negative → ACTIVE/literal_own_assertion | b.second_white_probability: compatible_pending_checker; COMPOSITE_FAILED (tme2-p3-check.v1:0dec0524e80ca03e78f4); sufficient=False |
| `E002:p3:de0da5d175797bf82ae2` / `segunda_branca` | assino o resultado da segunda branca: 11/36.<br>payload=`11/36` | `[115, 159]` → `[3, 159]` | asserted; abandoned=false; attributed=true; polarity=positive → ACTIVE/literal_own_assertion | b.second_white_probability: compatible_pending_checker; COMPOSITE_VERIFIED (tme2-p3-check.v1:10d96dfcbfffdc8a1ef4); sufficient=True |

Todas as decisões acima têm binding_valid=true, positive_credit_eligibility=true e conflict_visible=true no snapshot gravado. Isso descreve a autoridade **atribuída pela implementação**, não a autoridade devida à fonte. Nenhuma possui superseded_by ou supporting_spans de correção. Os payloads originais e adaptados são iguais.

| Produtor / evidence | Checker ref | Policy receipt | Targets / resultado |
| --- | --- | --- | --- |
| positive_checker / `E002:p3:66d44d0858d5c726aad2` | `tme2-p3-check.v1:0dec0524e80ca03e78f4` | `veto:48090837708e14b1baa7f6b8cd2aeea94344493fa0fad76ce9ef51980be50ae2` | `['b.second_white_probability']`; COMPOSITE_FAILED; hard=true; APPLIED |
| native_checker / `E002:p3:66d44d0858d5c726aad2` | `tme2-p3-check.v1:318fec70222080fcc4db` | `veto:107123bf6ec6a9dcfce5db6dce1ff43620c07920604e4cbcc5f00d6401450ff4` | `['b.second_white_probability']`; COMPOSITE_FAILED; hard=true; APPLIED |

**Causa precisa.** O antigo asserted_content inclui a invalidação “Depois de conferir a partição, invalido esse valor”; o modelo sinaliza abandoned=true e polarity=negative. O novo asserted_content é a conclusão `11/36`. Ambos acabam com source_range=[3,159), embora assertion_ranges sejam [3,112) e [115,159). O ponto após `7/36.` não corta a cláusula pela mesma regex que falha em B02, e o asserted_content antigo já cobre mais de uma oração. O critério de predecessor por source_range impede a relação antes de analisar o marcador. Adicionalmente, “invalido” não integra os atos explícitos implementados; resolver a segmentação sozinho não demonstra que este caso ficaria correto.

Os payloads 7/36 e 11/36 são preservados, não há conta falsa inventada. O composto refuta o primeiro resultado e valida o segundo contra a máquina finita. A rota preserva result_credit_only/argument_satisfied=false; não cria uma justificativa de partição que não foi escrita. Ambos mantêm source_consistency=VERIFIED porque esse componente examina as etapas de contagem/mesmo compartimento, não adjudica a retratação entre dois valores finais.

Classificação: **SOURCE_BINDING_ERROR (contexto temporal) + DISCOURSE_STATE_ERROR**. O award final b.conclusion=2 tem witness pronto e não depende da probabilidade antiga retirada.

Awards efetivamente bloqueados: `b.second_white_probability`. Todos os scores finais do caso são 0; `review_recommended=true`. O receipt do award cita os IDs de veto acima, mesma ledger_revision/source_sha256 do caso.

### 3.4. B08

```text
a) Eu havia dito quatro brancas na base. Volto a essa contagem e retiro o quatro: minha resposta para as bolas brancas inferiores é duas.
```

[p3_s03_b08: artefato original](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_b08.json).

| EvidenceUnit | Asserted content / payload | Ranges assertion → source | Modelo → resolver | Mapping / checker / sufficiency |
| --- | --- | --- | --- | --- |
| `E002:p3:1052cb22fa9f25042410` / `inferiores_brancas` | minha resposta para as bolas brancas inferiores é duas.<br>payload=`2` | `[82, 137]` → `[41, 137]` | asserted; abandoned=false; attributed=true; polarity=positive → ACTIVE/literal_own_assertion | a.bottom_white_count: white_count_not_bound_to_written_quantity; CONTEXT_REJECTED (None); sufficient=False |
| `E002:p3:be65a0d394ff5bb4c99b` / `inferiores_brancas` | Eu havia dito quatro brancas na base.<br>payload=`4` | `[3, 40]` → `[3, 40]` | abandoned; abandoned=true; attributed=true; polarity=positive → ACTIVE/literal_own_assertion | a.bottom_white_count: compatible_pending_checker; DETERMINISTIC_FAILED (tme2-p3-check.v1:026ebd9cd7419b6ba98f); sufficient=False |

Todas as decisões acima têm binding_valid=true, positive_credit_eligibility=true e conflict_visible=true no snapshot gravado. Isso descreve a autoridade **atribuída pela implementação**, não a autoridade devida à fonte. Nenhuma possui superseded_by ou supporting_spans de correção. Os payloads originais e adaptados são iguais.

| Produtor / evidence | Checker ref | Policy receipt | Targets / resultado |
| --- | --- | --- | --- |
| positive_checker / `E002:p3:be65a0d394ff5bb4c99b` | `tme2-p3-check.v1:026ebd9cd7419b6ba98f` | `veto:4d9aa1a08403076a7a3d7ec8bce0ba4b477c018db1361f40ca675754018e2751` | `['a.bottom_white_count']`; DETERMINISTIC_FAILED; hard=true; APPLIED |
| native_checker / `E002:p3:be65a0d394ff5bb4c99b` | `tme2-p3-check.v1:439e9dc4a1d310cc9f70` | `veto:525d08a105f831f2cb5452c56a65e9df059ffaa81f6f0c6dfd454764fd6554fd` | `['a.bottom_white_count']`; DETERMINISTIC_FAILED; hard=true; APPLIED |

**Causa precisa.** O modelo preserva “quatro”→4 e “duas”→2, marcando 4 abandoned=true; não há erro aritmético de normalização. Os ranges são distintos e ordenados. Porém, `representation` exige o número **antes** de “bolas brancas” para inferiores_brancas. A frase “as bolas brancas inferiores é duas” não satisfaz essa gramática: `white_count_not_bound_to_written_quantity`. A adaptação é identity; o payload 2 já parseável não é reparado. `literal_property` fica sem propriedade executável para a nova quantidade, e o resolver abandona a análise desse possível substituto em `if new.state != ACTIVE or not np: continue`. O estado ainda pode ser ACTIVE pela âncora textual, mas a relação de revisão não é construída. A regra que deveria reconhecer a correção depende indevidamente da representabilidade positiva do resultado final.

O 4 antigo é representável e corretamente refutado contra a contagem 2. A própria fonte contém a correção, mas não existe checker executado para o novo 2. Retirar o falso veto sozinho não basta para gerar a.count=2: falta corrigir a vinculação da quantidade à frase, sem alterar o valor escrito.

Classificação: **SOURCE_BINDING_ERROR (quantidade expressa em ordem não reconhecida) + DISCOURSE_STATE_ERROR**; não PAYLOAD_NORMALIZATION_ERROR. Os 2 pontos legítimos são afetados por dois bloqueadores concorrentes. Não há outra parcela no texto.

Awards efetivamente bloqueados: `a.bottom_white_count`. Todos os scores finais do caso são 0; `review_recommended=true`. O receipt do award cita os IDs de veto acima, mesma ledger_revision/source_sha256 do caso.

### 3.5. E01

```text
a) A nota de uma colega dizia primeira_branca: 7/12; transcrevo sem concordar. Na minha resolução, primeira_branca: 1/3 e inferiores_brancas: 2.
```

[p3_s03_e01: artefato original](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_e01.json).

| EvidenceUnit | Asserted content / payload | Ranges assertion → source | Modelo → resolver | Mapping / checker / sufficiency |
| --- | --- | --- | --- | --- |
| `E002:p3:401b0ababc914bbc5da3` / `primeira_branca` | primeira_branca: 7/12<br>payload=`7/12` | `[30, 51]` → `[3, 78]` | quoted; abandoned=false; attributed=false; polarity=positive → ACTIVE/literal_own_assertion | a.first_white_probability: compatible_pending_checker; DETERMINISTIC_FAILED (tme2-p3-check.v1:d7e0c6b0feae66f95179); sufficient=False |
| `E002:p3:4ea4f320a77ab9f72a47` / `primeira_branca` | primeira_branca: 1/3<br>payload=`1/3` | `[99, 119]` → `[79, 144]` | asserted; abandoned=false; attributed=true; polarity=positive → ACTIVE/literal_own_assertion | a.first_white_probability: compatible_pending_checker; DETERMINISTIC_VERIFIED (tme2-p3-check.v1:c4a9544d6ec54c5b342a); sufficient=True |
| `E002:p3:6e1960acfc31eac33a2b` / `inferiores_brancas` | inferiores_brancas: 2<br>payload=`2` | `[122, 143]` → `[79, 144]` | asserted; abandoned=false; attributed=true; polarity=positive → ACTIVE/literal_own_assertion | a.bottom_white_count: white_count_not_bound_to_written_quantity; CONTEXT_REJECTED (None); sufficient=False |

Todas as decisões acima têm binding_valid=true, positive_credit_eligibility=true e conflict_visible=true no snapshot gravado. Isso descreve a autoridade **atribuída pela implementação**, não a autoridade devida à fonte. Nenhuma possui superseded_by ou supporting_spans de correção. Os payloads originais e adaptados são iguais.

| Produtor / evidence | Checker ref | Policy receipt | Targets / resultado |
| --- | --- | --- | --- |
| positive_checker / `E002:p3:401b0ababc914bbc5da3` | `tme2-p3-check.v1:d7e0c6b0feae66f95179` | `veto:2db8fd4702032f875131ab65ee620931f0b6915b6117ad12e609ff132fcdb6bf` | `['a.first_white_probability']`; DETERMINISTIC_FAILED; hard=true; APPLIED |
| native_checker / `E002:p3:401b0ababc914bbc5da3` | `tme2-p3-check.v1:60e63b90577dcc2bd913` | `veto:00687d50225ff6b96811dd611360beedcda92e9e43089424dd37a51d4b29eed1` | `['a.first_white_probability']`; DETERMINISTIC_FAILED; hard=true; APPLIED |

**Causa precisa.** O modelo sinaliza quoted, attributed_to_student=false, scope=unknown no 7/12. A cláusula adaptada conserva “nota de uma colega dizia” e “transcrevo sem concordar”. `_context` cobre `disse`, `afirmou`, certas outras fórmulas e aspas, mas não esse padrão de atribuição/negação de adesão. O default é `ACTIVE/literal_own_assertion`; o payload tem âncora matemática válida. A projeção então reescreve attributed_to_student=true, assertion_status=asserted e scope=main_argument. O mapper confia na decisão discursiva e não reaplica local_context quando ela existe. Assim uma citação sem adoção ganha autoridade negativa própria.

O conteúdo 7/12 é de fato falso para a primeira branca; a conta recebida pelo checker não está corrompida. O que mudou é “uma colega disse X e não concordo” → “o aluno adota X”. A resposta própria 1/3 tem DETERMINISTIC_VERIFIED/sufficient=true e fica bloqueada. A contagem própria 2 é independente, mas perde os outros 2 pontos por `white_count_not_bound_to_written_quantity`, não por esse veto.

Classificação: **DISCOURSE_STATE_ERROR (atribuição/adoção)**. Não há evidência de erro do extractor em atribuição, de obrigação errada ou de valor normalizado errado.

Awards efetivamente bloqueados: `a.first_white_probability`. Todos os scores finais do caso são 0; `review_recommended=true`. O receipt do award cita os IDs de veto acima, mesma ledger_revision/source_sha256 do caso.

## 4. Checker correctness × representation correctness

A máquina versionada tem duas saídas inferiores brancas (1 e 2); na repetição, a segunda branca aparece apenas no 6. Na repetição do 3 a segunda cor é preta. A probabilidade da primeira branca é 1/3; a da segunda é 11/36. As comparações abaixo são leitura dos certificados e aritmética exata, sem reexecutar checker.

| Caso | Proposição recebida | Resultado do checker | Correto para essa proposição? | Fidelidade à posição atual do aluno |
| --- | --- | --- | --- | --- |
| A05 | conjunto repetição={6} | DETERMINISTIC_VERIFIED | Sim | É uma afirmação real, mas não representa a solução inteira contraditória; inclusão do 3 não foi verificada |
| B02 | primeira prob.=1/2; igualdade 2/6=1/3 | FAILED; FORMAL_VERIFIED | Sim em ambos | 1/2 era histórico, não premissa atual |
| B04 | continuação={1,4}; continuação={1,2} | FAILED; VERIFIED | Sim em ambos | {1,4} já havia sido substituído |
| B05 | segunda prob.=7/36; segunda prob.=11/36 | COMPOSITE_FAILED; COMPOSITE_VERIFIED | Sim em ambos | O primeiro resultado foi invalidado pelo próprio texto |
| B08 | contagem branca=4 | DETERMINISTIC_FAILED | Sim | O 4 foi retirado; o novo 2 não chegou ao checker |
| E01 | primeira prob.=7/12; própria=1/3 | FAILED; VERIFIED | Sim em ambos | 7/12 era de terceiro explicitamente não adotado |

Não há perda de dígito, troca de fração, remoção de lado de igualdade ou transformação de número errado em número correto nesses witnesses. A perda é de **ato discursivo, relação entre afirmações ou cobertura de proposição**. O termo “checker correto sobre representação errada” se aplica aos cinco vetos se representação incluir adoção/tempo/atribuição; seria enganoso se implicasse payload numérico errado.

B05 é o único desses casos com componentes compostos. Para 7/36: arithmetic=DETERMINISTIC_FAILED; finite_machine=DETERMINISTIC_VERIFIED; source_consistency=DETERMINISTIC_VERIFIED/no_negative_context; result_credit_contract=DETERMINISTIC_VERIFIED, argument_satisfied=false. Para 11/36, todos esses componentes são VERIFIED, com argument_satisfied=false preservado. Finite_machine verifica a máquina/medida, não declara 7/36 verdadeiro; a refutação vem da comparação do resultado. Nos demais casos subchecks=[]; seus checkers diretos não devem receber componentes fictícios no relato.

Fontes: [máquina](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/examples/pautas/tme2_problem3.machine.v1.json); [pauta](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/examples/pautas/tme2_problem3.v1.json); [_a/_b/_c](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/lean/student_claim_checkers/tme2_p3.py:116); [validação de fatos e suficiência](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py:87).

## 5. Fallbacks: três casos fora da qualidade semântica

| Caso | Erro gravado | Estágio | Modo efetivo | Score | Uso da API |
| --- | --- | --- | --- | ---: | --- |
| [p3_s03_c03: artefato original](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_c03.json) | `ValueError:extractor_incomplete_or_refused` | Extractor: resposta não completed, antes de bind_evidence | `TME_SEMANTIC_FORMAL_NATIVE_FALLBACK` | 0 | api_calls=1, output_tokens=16000 |
| [p3_s03_d01: artefato original](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_d01.json) | `ValueError:extractor_incomplete_or_refused` | Extractor: resposta não completed, antes de bind_evidence | `TME_SEMANTIC_FORMAL_NATIVE_FALLBACK` | 0 | api_calls=1, output_tokens=16000 |
| [p3_s03_d06: artefato original](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_d06.json) | `ValueError:extractor_incomplete_or_refused` | Extractor: resposta não completed, antes de bind_evidence | `TME_SEMANTIC_FORMAL_NATIVE_FALLBACK` | 0 | api_calls=1, output_tokens=16000 |

Nos três, extracted_evidence=[] e não há interpretação útil vinculada; a rodada passa para o fallback nativo unificado. O erro agregado é `ValueError:extractor_incomplete_or_refused`; os 16.000 tokens de saída em cada resposta coincidem com o limite configurado. Isso é compatível com esgotamento do limite, mas os artefatos não preservam incomplete_details para distinguir conclusivamente esse motivo de outros estados não completed. Não atribuir automaticamente a recusa de segurança nem a erro de matemática. Status final do metadata é unavailable; não se presume que esse seja o status bruto retornado pela API.

ALL40 inclui os três; SEMANTIC_SUCCESS_ONLY tem 37. Nenhum fallback é prova de acerto/erro da interpretação semântica. Retries/max_output_tokens/configuração não foram alterados. Nesta auditoria não houve chamada API nem tentativa de recuperação.

## 6. Análise dos quatro estados nos seis casos

| Caso/evidência | Sinal do modelo | Evidência textual decisiva | Estado devido → gravado | Consequência |
| --- | --- | --- | --- | --- |
| A05 / inclusão do 3 | asserted, positive, attributed=true; qualitative/unmapped | “também considero válida” | ACTIVE → AMBIGUOUS | Não há checker/refutação; o conjunto positivo isolado recebe 2 |
| B02 / 1/2 | abandoned=true | “substituo essa chance ... 2/6=1/3” | SUPERSEDED → ACTIVE | Refutação do passado veta o final provado |
| B04 / {1,4} | abandoned=true | “Retifico ... {1,2} ... definitiva” | SUPERSEDED → ACTIVE | Refutação do passado veta a continuação correta |
| B05 / 7/36 | abandoned=true, polarity=negative | “invalido esse valor e assino ... 11/36” | SUPERSEDED → ACTIVE | Resultado final correto fica bloqueado |
| B08 / 4 | abandoned=true | “retiro o quatro ... é duas” | SUPERSEDED → ACTIVE | Veto mais rejeição da representação final |
| E01 / 7/12 | quoted, attributed=false | “colega dizia ... transcrevo sem concordar” | NON_ADOPTED → ACTIVE | Refutação de terceiro veta resposta própria |

As posições finais próprias permanecem ACTIVE nos cinco vetos; o problema não é retirar sua adoção, mas a autoridade residual atribuída ao conteúdo anterior/alheio. Em A05 não há ambiguidade discursiva real; a única AMBIGUOUS emitida é um substituto indevido para incapacidade de representar a propriedade. Não há exemplos normativamente AMBIGUOUS entre os seis problemas examinados; D02/D03 ficam fora deste recorte e não servem para inferência adicional aqui.

Não basta aceitar cegamente os flags do modelo: esses flags acertaram a retirada/citação nos cinco vetos, mas não são certificados. A política normativa que exige validação textual é adequada. O problema está na validação local incompleta, no default ACTIVE e na posterior reescrita dos flags para a projeção, apesar de relações/sinais não resolvidos. Em B02/B05 o resolver também recebe contexto temporal já distorcido pelo adaptador; em B08 depende de um input representacional ausente. Em E01 o wrapper correto está presente e é ignorado pelo reconhecedor. Em A05 o input já perdeu a propriedade tipada, mas preservou o conteúdo e a adoção; o resolver acrescenta a confusão entre representação e discurso.

## 7. Mapping/binding, suficiência e reconciliação

É necessário separar três validações:

1. **Binding literal:** hash, envelope, asserted_content e offsets conferem. Nos seis casos não há evidência de texto fabricado ou bytes de outro aluno.
2. **Binding de proposição/contexto:** subject, quantificador (inclusão/exclusividade), quantidade e cláusula temporal. Há deficiência negativa em A05, segmentos sobrepostos em B02/B05 e gramática estreita de quantidade em B08/E01(a.count).
3. **Adoção e autoridade:** um predicado verdadeiro/falso escrito pode ser hipótese, citação ou histórico. Essa informação foi perdida nos vetos; um hash de fonte correto não a recupera.

Os obligation_candidates relevantes são corretos, inclusive a inclusão do 3 em A05 aponta b.same_compartment. Não foi encontrada troca de obligation_id como causa dos 2 pontos ou dos cinco vetos. A sugestão do modelo, contudo, não é vínculo suficiente para refutação/award nem para instaurar veto apenas por estar presente.

A sufficiency implementada exige resultado positivo e status validado supported; `award` confere receipt, fontes e decisão de adoção. O filtro não mede se todas as afirmações materiais relacionadas à obrigação foram resolvidas. A05 passa com um witness suficiente localmente enquanto existe um claim relacionado, explicitamente adotado, sem interpretação executável. Isso não é uma nova justificativa inventada: é uma lacuna de fechamento contextual para automação. Nos cinco vetos a sufficiency dos finais B02/B04/B05/E01 já é verdadeira; o bloqueio acontece depois. Em B08 ela é falsa por falta de representação.

`VetoEligibilityPolicy` exige ACTIVE, binding válido, checker_ref, refutação reconhecida e scope compatível; `reconcile` só aceita receipts autênticos. Esses requisitos foram cumpridos **segundo os estados errados recebidos**, por isso os vetos não são bypasses. Reescrever a reconciliação para ignorar refutações ou aceitar o último número não corrige a causa e introduziria risco de falso crédito.

Referências: [clause_view](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/source_adapter.py:11); [literal_property](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/source_adapter.py:104); [representation](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:69); [ObligationMapper](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:129); [_context](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/discourse.py:56); [ordem/revisão](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/discourse.py:141); [projeção de autoridade](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/discourse.py:220); [decide](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/veto_policy.py:35); [reconcile](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/veto_policy.py:73).

## 8. Causa comum ou classes independentes?

**Há uma deficiência comum de integridade semântica antes da autoridade, com classes causais distintas.**

- A05: perda de cobertura negativa/subject e confusão entre “não representável” e AMBIGUOUS. O checker positivo aplica-se a um claim verdadeiro e corretamente mapeado. Rejeita-se a hipótese de que o falso 3 tenha sido projetado como o verdadeiro 6.
- B02/B05: contexto/segmentação faz perder direção temporal; B05 também tem ato de revisão não reconhecido.
- B04: revisão linguisticamente explícita fora do reconhecedor, com spans e payloads adequados.
- B08: vinculação de quantidade falha e impede construir a relação de revisão, além de impedir crédito positivo posterior.
- E01: atribuição de terceiro e recusa de adesão não reconhecidas; a proposição numérica é fiel, a autoria/adopção corrente não.

O padrão “checker correto aplicado a claim semanticamente mal representado” é **confirmado para os vetos no nível de contexto/adoção**, mas não como erro de todos os payloads e tampouco como explicação suficiente de A05. Uma única mudança de mapper, um checker mais fraco ou uma regex de “correção” não cobre todos os mecanismos. O relatório anterior permanece intacto; esta auditoria aprofunda a explicação de B02/B05: a colisão dos ranges precede a análise do marcador, portanto “marcador não reconhecido” sozinho era incompleto.

## 9. Positive credit versus hard veto: camada mínima

Os dois erros passam por autoridade tipada e versionada, mas o certificado da matemática não valida o significado discursivo usado para atribuir autoridade. Sim, um binding/contexto impreciso ainda pode ganhar autoridade após um checker; no falso crédito isso ocorre **por excluir contexto negativo relevante**, não por provar a falsidade.

A menor fronteira lógica adicional fica entre representação/resolução de discurso e emissão/consumo dos witnesses e receipts: um contrato verificável de integridade semântica por obrigação. Ele precisa distinguir adoção, representabilidade matemática, associação à obrigação e resolução das relações de revisão/contradição. Corrigir somente `VetoEligibilityPolicy` não recupera os campos de fonte perdidos; corrigir somente a matemática tampouco valida autoria. A solução pode envolver poucos módulos, mas tem obrigações em mais de uma camada.

Sinais do modelo podem propor a relação; regras/source receipts precisam validar alvo, direção, exclusividade e contexto. Quando isso não é decidível, manter review e não transformar ausência de representação em verdade, falsidade ou adoção. O relato da limitação não autoriza atribuir score a interpretação de LLM.

## 10. Safe automation boundary: avaliação, sem implementar

**Os artefatos sustentam avaliar uma fronteira explícita `AUTO_GRADE_SAFE` / `REVIEW_REQUIRED`, mas ela não substitui as correções de representação/discurso.** Nos seis casos já havia `review_recommended=true`. Logo, apenas adicionar/renomear um flag não teria efeito: A05 continuaria com 2 pontos se a fronteira não governasse a emissão do award.

O score deve permanecer numérico, soma das parcelas automaticamente autorizadas. REVIEW_REQUIRED é estado de decisão/certeza, não FORMAL_REFUTED, não `score=None` e não um hard veto disfarçado. A ausência de checker impede o próprio claim de ganhar crédito; evidência realmente ambígua continua sem autorização para refutar um positivo independente.

| Caso/classe | Benefício plausível, condicionado à validação de escopo | Limite / efeito que não se pode prometer |
| --- | --- | --- |
| A05 | Uma inclusão explicitamente adotada e materialmente relacionada ao conjunto, ainda não verificada, impede certificar a obrigação inteira como AUTO_GRADE_SAFE; reter só b.same evitaria os 2 indevidos | Não basta o LLM sugerir b.same ou dizer AMBIGUOUS para bloquear qualquer positivo; requer vínculo de propriedade/scope validado. Um guard matemático legítimo de membership também resolveria este negativo representável futuramente |
| B02/B04/B05/E01 | Não autorizar hard veto de posição histórica/citada não confirmada como atual; há witness final positivo suficiente no trace | Para conceder os 7 pontos é necessário validar a adoção final e a retirada/não adoção. Marcar toda a obrigação review e reter tudo mantém under-credit |
| B08 | Suspender autoridade do 4 quando a retirada não está resolvida evita veto ilegítimo | Continua faltando witness do 2; boundary sozinha não recupera os 2 pontos |
| Parcela independente | Preservar autoridade e pontos fora da propriedade/dependências afetadas | E01(a.count) já tem outra falha de representação; não se deve atribuí-la ao veto de probabilidade nem prometer sua recuperação por boundary |

Existe uma tensão normativa que precisa ser explícita: a arquitetura atual diz que AMBIGUOUS não pode retirar award ACTIVE independente. Uma regra genérica “qualquer AMBIGUOUS na obrigação ⇒ zero” violaria esse contrato e recriaria falsos vetos. Em A05, a adoção não é ambígua; a incapacidade de representar uma contradição material não deveria ter sido registrada como dúvida de adoção. Qualquer retenção por obrigação incompleta deve ser definida, auditada e validada como mudança de política de automação, com rastreio de pontos retidos; não apenas renomeada como review para ocultar um veto.

Portanto, a boundary pode reduzir simultaneamente **autoridade positiva e negativa indevidas**, com escopo local bem validado. Não há evidência experimental de que uma boundary isolada eliminaria os cinco under-scores. Os efeitos da tabela são contrafactuais lógicos a partir dos receipts, não resultados de um rerun.

## 11. Recomendação arquitetural

**MULTI_LAYER_FIX_REQUIRED.** Prioridade proposta, sem implementação:

1. Separar ranges de envelope, cláusula e assertiva para relações temporais; preservar sentença final depois de número/fração sem confundir com decimal. Uma correção pode compartilhar envelope com a posição retirada sem compartilhar o mesmo ato discursivo.
2. Reconhecer propriedade e papel discursivo sem exigir previamente que o payload positivo seja executável. ACTIVE não significa “o parser entendeu”; UNREPRESENTABLE não significa AMBIGUOUS. Preservar inclusão parcial sem transformá-la em conjunto exaustivo.
3. Validar relações de substituição e não adoção com alvo/escopo explícitos; manter sinais originais e receipts, evitando default ACTIVE quando a fonte traz retirada/citação ainda não resolvida. Não transformar flags do modelo em autoridade direta.
4. Corrigir vínculos representacionais de quantidade mantendo a posição escrita (inclusive número após predicado); não completar solução ou reinterpretar valores para casar com a máquina.
5. Definir e testar uma fronteira local de automação comum às autoridades positiva e negativa, com score numérico, review rastreável e conservação de créditos independentes. Formalizar o efeito de pendências materiais na obrigação, sem contrariar silenciosamente a política de ambiguidade.

Não se recomenda trocar pesos/pauta, enfraquecer checkers compostos, ignorar negativos, escolher sempre a última expressão ou retunar o prompt com estes seis textos. Também não se recomenda apenas FIX_SUFFICIENCY_POLICY: isso não corrige autoria/tempo nem a representação ausente de B08.

## 12. Plano de validação futuro — Safety04, não criado

Safety03 fica OBSERVED FAILURE / REGRESSION DATASET. Pode gerar regressões explícitas do defeito, nunca evidência independente de sucesso do próximo fix. Qualquer implementação futura requer nova autorização e SHA congelado; este documento não a executa.

Antes de uma nova avaliação independente:

- Validar contratos/metamorfismos locais para término de frase após inteiro/fração versus decimal, overlap de envelopes com assertion_ranges distintos, revisão sem depender de correção matemática, quantity binding em ordens variadas e referência de terceiro sem adesão.
- Exigir preservação de inclusão/exclusividade, polaridade e property identity; ausência de representação e ausência de validação de adoção devem permanecer distinguíveis.
- Testar concessão/veto por todos os produtores no mesmo snapshot; afirmar ausência de autoridade sem checker/receipt, sem bypass e sem perda de créditos independentes. Medir também pontos retidos indevidamente pela boundary, não apenas falsos vetos nomeados como tal.
- Usar Safety03 apenas como regressão observada, com expectativas intactas, reportando separadamente reparos, perdas e limitações de construção já documentadas.

Para **Safety04 inédito**: redigir novas fontes sem textos/paráfrases triviais dos conjuntos observados; revisar estados/expectativas antes de qualquer execução, com atenção a ambiguidades reais e dependências entre cor/contagem; congelar fontes, IDs, expectativas, receipts e SHA por hash; só depois executar uma vez por modo com configuração/retry predefinidos. Separar ALL e semantic-success; auditar proveniência de todo erro de autoridade. Critério primário continua zero falso crédito material, nenhuma autoridade sem validação, ausência de padrão material de falso veto e retratações/independência funcionando. Score médio melhor não compensa falha de segurança. Nenhum caso Safety04 foi escrito nesta tarefa.

## 13. Integridade e conclusão

A correção matemática dos checkers examinados é sustentada pelos valores e receipts gravados; a correção da autoridade é refutada pelas fontes. O conhecimento matemático necessário já estava disponível, mas segmentação, representação e adoção não foram preservadas até a decisão automática. A centralização de veto funcionou como implementada; não garantiu a validade semântica do input.

Conferência de integridade: 982 arquivos existentes inventariados, zero bytes alterados. Git HEAD `8c85ea67f2ba07b68e433e0dbf6ddf0668390958` preservado. O único arquivo novo é `docs/audits/TME_P3_SEMANTIC_SAFETY_03_FORENSIC.md`; sem stage/commit. Os artefatos de avaliação continuam originais, inclusive o receipt Lean histórico de B02; não houve reexecução.

**MULTI_LAYER_ROOT_CAUSE**
