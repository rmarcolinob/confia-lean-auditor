# TME P3 — Semantic Safety 02: auditoria forense

## 0. Resultado e método

**MULTIPLE_ROOT_CAUSES.** Os dois falsos créditos não foram causados por abandono inferido: em ambos, os claims relevantes são asserted, atribuídos ao aluno e `abandoned=false`. Um perdeu a contradição na fronteira de representação; o outro produziu a refutação, mas não a propagou à conclusão sujeita ao veto. Os quatro falsos positivos de guard e E02 têm outra causa demonstrável: suporte textual de retratação dependente da geometria dos envelopes, de marcadores restritos e de adjacência rígida. A08/E08 acrescentam variação de payload incompatível com o mapper. O fallback é uma falha de conclusão da extração, sem evidência suficiente para atribuir sua causa de transporte exata.

Auditoria de 06/11/2026, somente leitura dos recibos, fontes, pauta, código e teste controlado já gravados. Nenhum modo, checker, teste ou API foi reexecutado. Nenhuma expectativa foi revista. O único arquivo novo no worktree é este relatório.

HEAD da auditoria: `1b864705017939a6fbf9087888cce3d606cf0de5` (`Record P3 independent semantic safety 02 failure`). Implementação que gerou a avaliação: `89cda1cab89648d3888775bbcead42ea85bd4861`. O diff entre esses SHAs contém apenas o relatório anterior e os cinco arquivos de fixtures safety_02; não contém código. O worktree estava limpo ao iniciar.

As classificações distinguem observação do trace, explicação pelo fluxo de código e recomendação futura. Não se afirma que mudar apenas uma condição resolveria todos os casos: nenhum contrafactual foi executado.

Fontes principais: [avaliação safety_02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_SEMANTIC_SAFETY_02.md), [fix anterior](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_ABANDONMENT_SAFETY_FIX_01.md), [pauta P3](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/examples/pautas/tme2_problem3.v1.json), [expectativas congeladas](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/semantic_safety_02/expectations.json).

## 1. Dois falsos créditos: cadeia completa

Nos dois casos, houve checker positivo real e sufficiency=true; os pontos não nasceram diretamente da confiança do LLM. O erro está em conceder a parcela após perder ou limitar indevidamente a evidência negativa relevante. Não é correto dizer que o checker provou a afirmação falsa descartada.

### 1.1 p3_safe_s2_03 — c.continue, 1 ponto

Recibo: [p3_safe_s2_03.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s2_03.json).

Fonte integral:

```text
c) Registro os estados em que decido continuar: continuar: {1,2}.
Também mantenho o jogo em curso se a primeira branca for atribuída ao compartimento 4; essa inclusão integra minha resposta.
```

EvidenceUnits originais (offsets `[start,end)` do recibo, sem normalizar a fonte):

**`E002:p3:b7ba51086f6692348d57`** — source_evidence_ids `["E002"]`, offsets `[3,65)`.

```text
Registro os estados em que decido continuar: continuar: {1,2}.
```

Asserted content: `continuar: {1,2}`. Payload: `{1,2}`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| c / continuar / integer_set | asserted / positive | false / false | main_argument / true | ["c.continue_compartments"] / DETERMINISTIC |

**`E003:p3:ede981b2d83490c6b1d1`** — source_evidence_ids `["E003"]`, offsets `[66,190)`.

```text
Também mantenho o jogo em curso se a primeira branca for atribuída ao compartimento 4; essa inclusão integra minha resposta.
```

Asserted content: `Também mantenho o jogo em curso se a primeira branca for atribuída ao compartimento 4; essa inclusão integra minha resposta.`. Payload: `Também mantenho o jogo em curso se a primeira branca for atribuída ao compartimento 4; essa inclusão integra minha resposta.`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| c / unmapped / qualitative | asserted / positive | false / false | main_argument / true | ["c.continue_compartments"] / SEMANTIC |

| EvidenceUnit | Obrigação | accepted / context_valid | Motivo | Rota efetiva |
| --- | --- | --- | --- | --- |
| E002:p3:b7ba51086f6692348d57 | c.continue_compartments | true / true | compatible_pending_checker | DETERMINISTIC |
| E003:p3:ede981b2d83490c6b1d1 | c.continue_compartments | false / false | obligation_subject_type_mismatch | DETERMINISTIC |

| Obrigação / evidence_ids | Checker / verification_id | Status / formal_status | Sufficiency | Componentes |
| --- | --- | --- | --- | --- |
| c.continue_compartments / ["E002:p3:b7ba51086f6692348d57"] | tme2-p3-check.v1 / tme2-p3-check.v1:284b9a7fe20ba457a88a | DETERMINISTIC_VERIFIED / FORMAL_NOT_ATTEMPTED | {"sufficient": true, "policy": "frozen_checker_first_with_result_method_separation", "basis": "frozen_P3_checker_and_validated_binding"} | sem componentes separados |
| c.continue_compartments / ["E003:p3:ede981b2d83490c6b1d1"] | não executado / — | CONTEXT_REJECTED / FORMAL_NOT_ATTEMPTED | {"sufficient": false, "basis": "no_eligible_checker_result"} | sem componentes separados |

**Abandono/retratação:** `abandonment_decisions=[]`; nenhum claim traz abandono. Não há marcador de correção, retirada ou substituição. “Também” acrescenta uma inclusão adotada, e “essa inclusão integra minha resposta” reforça a adoção. O “se” é condição do estado do jogo, não hipótese exploratória descartada; o próprio modelo registrou hypothetical=false.

**Checker:** `tme2-p3-check.v1` compara o conjunto executável {1,2} com `engine_derived.continue_compartments=[1,2]`. Essa checagem está correta para a primeira afirmação. A segunda EvidenceUnit não produz fato matemático: `obligation_subject_type_mismatch` deixa mathematical_refutation=false e sufficient=false. `CONTEXT_REJECTED` aqui é o rótulo técnico de uma rejeição de representação, não comprovação de contexto não adotado.

**Guard → reconciliation:** `conflict_guard_results=[]`, `abandonment_guard_results=[]`, `conflicts=[]`. O guard atômico existente é exclusivo de `b.same_compartment/repeticao_branca`; não examina continuação em c. A recuperação regular de abandono só opera quando há abandonos recuperados, inexistentes aqui. A reconciliação recebe um positivo e uma rejeição sem refutação, não um conflito ativo.

**Sufficiency → award → pauta:** o positivo tem sufficient=true, basis=`frozen_P3_checker_and_validated_binding`. Sem conflito/refutação na obrigação, `award()` seleciona o positivo com `verified_and_sufficient`. A pauta usa `c.continue`, all_of de `c.continue_compartments`, valor 1. Score atual 1; esperado congelado 0.

| Obrigação | Award elegível | Decisão | Pontos da regra |
| --- | --- | --- | --- |
| c.continue_compartments | true | verified_and_sufficient | c.continue=1.0 |

**Respostas causais:**

- Afirmação falsa não creditada diretamente: inclusão do compartimento 4. A parcela indevida é a identificação completa da continuação, concedida pelo subconjunto correto enquanto a inclusão incompatível segue adotada.
- Checker não bloqueou porque só recebeu o conjunto {1,2}; a frase negativa não teve representação executável.
- Não houve mapping para obrigação errada: ambas apontam a `c.continue_compartments`. Houve subject/type inadequados (`unmapped/qualitative`) e ausência de recuperação de segurança para essa relação.
- Evidência contraditória foi preservada no JSON, mas descartada da checagem e do veto. Não houve autocorreção interpretada incorretamente.
- Classificação: **MAPPING_MISS / SAFETY_COVERAGE_GAP**, com contribuição da representação do extractor e do desenho mapper→projection→reconciliation. O award gate aplica seu contrato local, mas não exige resolução da afirmação ativa não representada na mesma família. Não é erro de aritmética, de pauta, de abandono ou de prova Lean.

### 1.2 p3_safe_s2_06 — b.conclusion, 2 pontos

Recibo: [p3_safe_s2_06.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s2_06.json).

Fonte integral:

```text
b) Separei os eventos de compartimentos diferentes na linha
favoraveis_distintos: 2*5=10
Na minha enumeração, ao repetir o compartimento, o terceiro também fornece uma bola branca.
Apesar dessa inclusão, mantenho a probabilidade da segunda branca em 11/36.
```

EvidenceUnits originais (offsets `[start,end)` do recibo, sem normalizar a fonte):

**`E002:p3:e448cbc2597a9d1f8b84`** — source_evidence_ids `["E002", "E003"]`, offsets `[3,88)`.

```text
Separei os eventos de compartimentos diferentes na linha
favoraveis_distintos: 2*5=10
```

Asserted content: `favoraveis_distintos: 2*5=10`. Payload: `2*5=10`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| b / favoraveis_distintos / math | asserted / positive | false / false | main_argument / true | ["b.different_favorable"] / COMPOSITE |

**`E004:p3:25f6a0931855798ee442`** — source_evidence_ids `["E004"]`, offsets `[89,180)`.

```text
Na minha enumeração, ao repetir o compartimento, o terceiro também fornece uma bola branca.
```

Asserted content: `ao repetir o compartimento, o terceiro também fornece uma bola branca.`. Payload: `{3}`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| b / repeticao_branca / integer_set | asserted / positive | false / false | main_argument / true | ["b.same_compartment"] / DETERMINISTIC |

**`E005:p3:ab0286677c12b6e3c637`** — source_evidence_ids `["E005"]`, offsets `[181,256)`.

```text
Apesar dessa inclusão, mantenho a probabilidade da segunda branca em 11/36.
```

Asserted content: `Apesar dessa inclusão, mantenho a probabilidade da segunda branca em 11/36.`. Payload: `11/36`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| b / segunda_branca / math | asserted / positive | false / false | final_conclusion / true | ["b.second_white_probability"] / COMPOSITE |

| EvidenceUnit | Obrigação | accepted / context_valid | Motivo | Rota efetiva |
| --- | --- | --- | --- | --- |
| E002:p3:e448cbc2597a9d1f8b84 | b.different_favorable | true / true | compatible_pending_checker | COMPOSITE |
| E004:p3:25f6a0931855798ee442 | b.same_compartment | false / false | set_payload_omits_source_members | DETERMINISTIC |
| E005:p3:ab0286677c12b6e3c637 | b.second_white_probability | true / true | compatible_pending_checker | COMPOSITE |

| Obrigação / evidence_ids | Checker / verification_id | Status / formal_status | Sufficiency | Componentes |
| --- | --- | --- | --- | --- |
| b.different_favorable / ["E002:p3:e448cbc2597a9d1f8b84"] | p3-checker-first.v1 / tme2-p3-check.v1:67a17cb3c6db0c2bd446 | COMPOSITE_VERIFIED / FORMAL_NOT_ATTEMPTED | {"sufficient": true, "policy": "frozen_checker_first_with_result_method_separation", "basis": "frozen_P3_checker_and_validated_binding"} | arithmetic: DETERMINISTIC_VERIFIED (existing_exact_arithmetic); finite_machine: DETERMINISTIC_VERIFIED (two_actual_withdrawals_and_uniform_measure); written_relation: DETERMINISTIC_VERIFIED (white_second_choice_and_distinct_first_choices_written) |
| b.second_white_probability / ["E005:p3:ab0286677c12b6e3c637"] | p3-checker-first.v1 / tme2-p3-check.v1:5c0014a65c0fcc384324 | COMPOSITE_VERIFIED / FORMAL_NOT_ATTEMPTED | {"sufficient": true, "policy": "frozen_checker_first_with_result_method_separation", "basis": "frozen_P3_checker_and_validated_binding"} | arithmetic: DETERMINISTIC_VERIFIED (existing_exact_arithmetic); finite_machine: DETERMINISTIC_VERIFIED (two_actual_withdrawals_and_uniform_measure); source_consistency: DETERMINISTIC_VERIFIED (no_negative_context); result_credit_contract: DETERMINISTIC_VERIFIED (b_conclusion_explicit_result_route_no_method_credit) |
| b.same_compartment / ["E004:p3:25f6a0931855798ee442"] | não executado / — | CONTEXT_REJECTED / FORMAL_NOT_ATTEMPTED | {"sufficient": false, "basis": "no_eligible_checker_result"} | sem componentes separados |

**Abandono/retratação:** os três claims são asserted/positive, atribuídos ao aluno, hypothetical=false e abandoned=false. `abandonment_decisions=[]`. “Apesar dessa inclusão, mantenho” conserva a afirmação, não a revoga. Não existe tentativa superseded.

**Checker positivo:** `p3-checker-first.v1`. Para `b.different_favorable`, arithmetic, finite_machine e written_relation verificam 2*5=10; `argument_satisfied=true`. Esses 2 pontos são legítimos e independentes. Para `b.second_white_probability`, arithmetic e finite_machine validam 11/36; `result_credit_contract` autoriza somente resultado, não demonstração (`argument_satisfied=false`, `result_credit_only=true`). O componente decisivo é `source_consistency=DETERMINISTIC_VERIFIED`, reason=`no_negative_context`, negative_fact_ids=[].

**Por que a frase negativa saiu da projeção:** `representation()` tenta uma igualdade de conjunto completo para payload {3}. `source_view` converte “terceiro” em 3 e o artigo “uma” em 1; a lista de números da frase não coincide com [3], ocasionando `set_payload_omits_source_members`. O problema é de representação de membership parcial e papel do numeral, não de obrigação errada. O guard consegue recuperar o pertencimento literal sem fabricar um conjunto completo.

**Guard:** `p3-membership-guard:863a2c6f17e18fb7984537c0`, EvidenceUnit `E004:p3:25f6a0931855798ee442`. Extrai `terceiro` em `[140,148)`, compartment=3, relation=`same_compartment_second_white`. Checker `frozen_finite_certificate_same_white_membership`: evento [3,3], primeira cor gray, segunda black; pares diagonais favoráveis derivados [[6,6]]. Resultado `DETERMINISTIC_FAILED`, mathematical_refutation=true. Guard-only=true, award_eligible=false, formal_status=`FORMAL_NOT_ATTEMPTED`, sufficient=false/basis=`guard_cannot_award`.

**Reconciliation:** cria conflito não resolvido apenas em `b.same_compartment`, reason=`conflicting_source_or_checker_evidence`, e bloqueia seu award. `b.second_white_probability` continua sem conflito. O checker positivo foi executado antes desse guard; `source_consistency` só viu os fatos negativos presentes em sua projeção. O reconciliador filtra guards por igualdade de obligation_id, sem aplicar o veto já contratado às conclusões dependentes.

**Sufficiency → award → pauta:** b.conclusion permanece sufficient=true e `verified_and_sufficient`. A pauta atribui `b.different=2` e `b.conclusion=2`, total 4; esperado congelado 2. A especificação prévia de S2_06 registrava explicitamente `negative_context_must_reach_conclusion`.

| Obrigação | Award elegível | Decisão | Pontos da regra |
| --- | --- | --- | --- |
| b.different_favorable | true | verified_and_sufficient | b.different=2.0 |
| b.same_compartment | false | blocked_conflict | 0 |
| b.second_white_probability | true | verified_and_sufficient | b.conclusion=2.0 |

**Respostas causais:**

- A falsa afirmação “o terceiro também fornece branca” não recebeu award; foi realmente refutada. O crédito indevido é a conclusão 11/36 sustentada pelo registro que mantém o contexto de contagem falso. O valor 11/36, isoladamente, não é falso.
- Não se acrescenta uma exigência pedagógica: a pauta b.conclusion é all_of apenas de `b.second_white_probability`, **não** de `b.same_compartment`. É o checker existente `source_consistency` que já prevê veto por evidência negativa em ordered_pairs/different_favorable/same_compartment. Exigir prova completa ou resultado positivo dessas três obrigações seria uma alteração diferente e não recomendada.
- Não houve mapping para obrigação errada. A rejeição de formato foi recuperada pelo guard, mas sua autoridade negativa permaneceu confinada à obrigação de origem.
- Não houve descarte definitivo da contradição nem erro de autocorreção. Houve **perda da dependência negativa** entre o resultado do guard e a conclusão.
- Classificação: **RECONCILIATION_DEPENDENCY_GAP / NEGATIVE_CONTEXT_NOT_PROPAGATED**, com gatilho de representação no mapper. Checker aritmético/modelo finito corretos; guard local correto; integração do source_consistency e award gate incompleta para esse caminho.

Referências das duas cadeias: [tme_semantic_formal_p3/mapper.py:117](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:117); [tme_semantic_formal_p3/verification.py:25](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py:25); [tme_semantic_formal_p3/conflict_guard.py:14](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py:14); [tme_p3_checker_first/engine.py:81](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_p3_checker_first/engine.py:81); [tme_semantic_formal_p3/engine.py:35](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:35); [tme_semantic_formal_p3/engine.py:60](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:60); [tme_semantic_formal_p3/engine.py:130](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:130).

## 2. Quatro falsos positivos dos guards

São quatro **eventos de guard regular de abandonment safety**, não quatro eventos do guard atômico de repetição. Todos possuem `guard_only=true`, `award_eligible=false`, sufficient=false e nenhuma geração de pontos. Todos bloqueiam uma posição final positiva já verificada. Há 7 pontos legítimos perdidos nesses quatro casos; isso é um subconjunto das perdas do benchmark.

Nos quatro, a inferência de abandono feita pelo modelo está sustentada pela fonte segundo a política esclarecida; o validador determinístico é que retorna `no_unambiguous_local_retraction`. Os checks matemáticos da posição antiga não são falsos positivos matemáticos. O falso positivo é discursivo: usá-la como posição ainda adotada contra a correção final.

### p3_safe_s1_02

Recibo: [p3_safe_s1_02.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s1_02.json).

Fonte integral:

```text
b) Minha primeira linha de contagem foi:
pares_ordenados: 6*5=30
Corrigindo a minha afirmação anterior:
pares_ordenados: 6^2=36
```

EvidenceUnits originais (offsets `[start,end)` do recibo, sem normalizar a fonte):

**`E002:p3:cda95ee0686359802bcd`** — source_evidence_ids `["E002", "E003", "E004"]`, offsets `[3,103)`.

```text
Minha primeira linha de contagem foi:
pares_ordenados: 6*5=30
Corrigindo a minha afirmação anterior:
```

Asserted content: `pares_ordenados: 6*5=30`. Payload: `6*5=30`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| b / pares_ordenados / math | abandoned / positive | false / true | main_argument / true | ["b.ordered_pairs"] / COMPOSITE |

**`E004:p3:45dbad8af58f3f0a124d`** — source_evidence_ids `["E004", "E005"]`, offsets `[65,127)`.

```text
Corrigindo a minha afirmação anterior:
pares_ordenados: 6^2=36
```

Asserted content: `pares_ordenados: 6^2=36`. Payload: `6^2=36`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| b / pares_ordenados / math | asserted / positive | false / false | main_argument / true | ["b.ordered_pairs"] / COMPOSITE |

| Claim retomado | Suporte textual reconhecido | Contexto restante válido | Visível para conflito | Razão |
| --- | --- | --- | --- | --- |
| E002:p3:cda95ee0686359802bcd | false | true | true | no_unambiguous_local_retraction |

O envelope antigo `[3,103)` contém o próprio marcador “Corrigindo a minha afirmação anterior”; o novo `[65,127)` o sobrepõe. A regra de marcador dentro do span não inclui essa forma; a regra de tail começa depois de 103, já após o marcador; a comparação adjacente rejeita a nova evidência porque 65<103. Mesmo item b, subject pares_ordenados e obligation b.ordered_pairs; correção local e incompatível, sem troca de assunto.

O guard regular usa `p3-checker-first.v1`: arithmetic=`DETERMINISTIC_FAILED`, finite_machine=`DETERMINISTIC_VERIFIED`, written_relation=`DETERMINISTIC_INCOMPLETE/counting_relation_not_established`, composto=`COMPOSITE_FAILED`. O rótulo arithmetic compara a quantidade esperada 36, não refuta a igualdade verdadeira 6*5=30: `value_status` exige que os lados representem o valor esperado. A correção 6^2=36 passa todos os componentes. O veto da contagem antiga bloqueia b.space.

| Guard / checker | Evidências usadas | Resultado | Conflito / award | Impacto |
| --- | --- | --- | --- | --- |
| p3-checker-first.v1 | ["E002:p3:cda95ee0686359802bcd"] | COMPOSITE_FAILED; mathematical_refutation=true | b.ordered_pairs não resolvido; blocked_conflict | b.space: 2→0; score esperado 2, observado 0 |

Classificação: **SPAN_BOUNDARY_RETRACTION_MISS**; categoria principal ABANDONMENT_POLICY, consequência GUARD_FALSE_POSITIVE. Não é hipótese/citação nem posição matemática atual. A retirada deve afetar o claim anterior, mantendo o novo elegível somente após checker.

### p3_safe_s1_03

Recibo: [p3_safe_s1_03.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s1_03.json).

Fonte integral:

```text
c) No estado após branca do compartimento 2, escolho preta e conto 3 posições dessa cor.
Pensando melhor, retiro essa escolha de cor e sua contagem.
Para o compartimento 2, após a branca, escolho cinza, que aparece 3 vezes.
```

EvidenceUnits originais (offsets `[start,end)` do recibo, sem normalizar a fonte):

**`E002:p3:d2f90804e539d10eba77`** — source_evidence_ids `["E002", "E003"]`, offsets `[3,148)`.

```text
No estado após branca do compartimento 2, escolho preta e conto 3 posições dessa cor.
Pensando melhor, retiro essa escolha de cor e sua contagem.
```

Asserted content: `escolho preta`. Payload: `black`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| c / estrategia_2 / enum | abandoned / positive | false / true | main_argument / true | ["c.strategy_case_2"] / COMPOSITE |

**`E002:p3:7d02c3b6e0cb547f8c54`** — source_evidence_ids `["E002", "E003"]`, offsets `[3,148)`.

```text
No estado após branca do compartimento 2, escolho preta e conto 3 posições dessa cor.
Pensando melhor, retiro essa escolha de cor e sua contagem.
```

Asserted content: `conto 3 posições dessa cor.`. Payload: `3`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| c / contagem_2 / math | abandoned / positive | false / true | main_argument / true | ["c.strategy_case_2"] / COMPOSITE |

**`E004:p3:7db6457d2f50136143e4`** — source_evidence_ids `["E004"]`, offsets `[149,223)`.

```text
Para o compartimento 2, após a branca, escolho cinza, que aparece 3 vezes.
```

Asserted content: `escolho cinza`. Payload: `gray`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| c / estrategia_2 / enum | asserted / positive | false / false | final_conclusion / true | ["c.strategy_case_2"] / COMPOSITE |

**`E004:p3:d68eeff32c15bc60bb59`** — source_evidence_ids `["E004"]`, offsets `[149,223)`.

```text
Para o compartimento 2, após a branca, escolho cinza, que aparece 3 vezes.
```

Asserted content: `cinza, que aparece 3 vezes.`. Payload: `3`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| c / contagem_2 / math | asserted / positive | false / false | final_conclusion / true | ["c.strategy_case_2"] / COMPOSITE |

| Claim retomado | Suporte textual reconhecido | Contexto restante válido | Visível para conflito | Razão |
| --- | --- | --- | --- | --- |
| E002:p3:d2f90804e539d10eba77 | false | true | true | no_unambiguous_local_retraction |
| E002:p3:7d02c3b6e0cb547f8c54 | false | true | true | no_unambiguous_local_retraction |

“Pensando melhor, retiro essa escolha de cor e sua contagem” é retirada explícita, não hipótese nem citação. Ambos os claims antigos (cor black e contagem 3) têm span `[3,148)` incluindo a retirada; os finais gray/3 ficam em `[149,223)`. O novo span começa por “Para”, não pelo conjunto restrito de marcadores aceitos; o marcador interior de retirada tampouco é reconhecido. Mesmo caso 2, item c e obrigação; a escolha de cor é incompatível, embora o número 3 permaneça igual.

O guard `tme2-p3-check.v1` refuta a estratégia antiga: após branca do 2, counts={white:1,gray:3,black:2}, optimal_colors=[gray]. O recibo do guard combina a cor antiga `E002:p3:d2f90804e539d10eba77` com a contagem **final** `E004:p3:d68eeff32c15bc60bb59`; não registra um check completo do par antigo como unidade isolada. A checagem compõe evidências do mesmo subject de caso sem uma versão discursiva. O erro material já está na reativação da cor antiga; a mistura evidencia por que a futura composição deve respeitar a correção. A estratégia final gray/3 tem COMPOSITE_VERIFIED e sufficient=true, mas perde c.second_strategy.

| Guard / checker | Evidências usadas | Resultado | Conflito / award | Impacto |
| --- | --- | --- | --- | --- |
| tme2-p3-check.v1 | ["E002:p3:d2f90804e539d10eba77", "E004:p3:d68eeff32c15bc60bb59"] | COMPOSITE_FAILED; mathematical_refutation=true | c.strategy_case_2 não resolvido; blocked_conflict | c.second_strategy: 2→0; score esperado 2, observado 0 |

Classificação: **EXPLICIT_RETRACTION_MARKER_AND_SCOPE_MISS**; categoria principal ABANDONMENT_POLICY, consequência GUARD_FALSE_POSITIVE. Não é hipótese/citação nem posição matemática atual. A retirada deve afetar o claim anterior, mantendo o novo elegível somente após checker.

### p3_safe_s1_07

Recibo: [p3_safe_s1_07.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s1_07.json).

Fonte integral:

```text
c) No registro inicial escrevi
continuar: {2,3}
Substituo integralmente esse conjunto pelo seguinte, que é o único adotado:
continuar: {1,2}
```

EvidenceUnits originais (offsets `[start,end)` do recibo, sem normalizar a fonte):

**`E002:p3:c845853005a1f0c2e394`** — source_evidence_ids `["E002", "E003", "E004"]`, offsets `[3,123)`.

```text
No registro inicial escrevi
continuar: {2,3}
Substituo integralmente esse conjunto pelo seguinte, que é o único adotado:
```

Asserted content: `continuar: {2,3}`. Payload: `{2,3}`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| c / continuar / integer_set | abandoned / positive | false / true | exploration / true | ["c.continue_compartments"] / DETERMINISTIC |

**`E004:p3:ce7cffa66f89c1456ce7`** — source_evidence_ids `["E004", "E005"]`, offsets `[48,140)`.

```text
Substituo integralmente esse conjunto pelo seguinte, que é o único adotado:
continuar: {1,2}
```

Asserted content: `continuar: {1,2}`. Payload: `{1,2}`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| c / continuar / integer_set | asserted / positive | false / false | final_conclusion / true | ["c.continue_compartments"] / DETERMINISTIC |

| Claim retomado | Suporte textual reconhecido | Contexto restante válido | Visível para conflito | Razão |
| --- | --- | --- | --- | --- |
| E002:p3:c845853005a1f0c2e394 | false | true | true | no_unambiguous_local_retraction |

“Substituo integralmente esse conjunto pelo seguinte, que é o único adotado” estabelece substituição inequívoca. O antigo {2,3}, span `[3,123)`, scope exploration, contém o marcador. O novo {1,2}, span `[48,140)`, scope final_conclusion, sobrepõe o anterior. A política não reconhece a substituição no span e rejeita a comparação adjacente por sobreposição. Não há outro item, subject ou obrigação.

O scope exploration original não impede recuperação: quando abandoned não é sustentado, `conflict_visibility` cria cópia asserted/not abandoned/main_argument se os outros filtros forem válidos. O checker `tme2-p3-check.v1` refuta {2,3} contra o conjunto derivado [1,2], criando veto permanente. O conjunto final já estava DETERMINISTIC_VERIFIED. O estado real é tentativa explicitamente substituída; não basta tratar exploration como falsa atribuição, nem ignorar a substituição porque o envelope é largo.

| Guard / checker | Evidências usadas | Resultado | Conflito / award | Impacto |
| --- | --- | --- | --- | --- |
| tme2-p3-check.v1 | ["E002:p3:c845853005a1f0c2e394"] | DETERMINISTIC_FAILED; mathematical_refutation=true | c.continue_compartments não resolvido; blocked_conflict | c.continue: 1→0; score esperado 1, observado 0 |

Classificação: **EXPLICIT_REPLACEMENT_WITH_OVERLAPPING_ENVELOPES**; categoria principal ABANDONMENT_POLICY, consequência GUARD_FALSE_POSITIVE. Não é hipótese/citação nem posição matemática atual. A retirada deve afetar o claim anterior, mantendo o novo elegível somente após checker.

### p3_safe_s4_07

Recibo: [p3_safe_s4_07.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s4_07.json).

Fonte integral:

```text
a) Meu registro inicial contém duas quantidades:
inferiores_brancas: 5
primeira_branca: 5/6
Corrigindo apenas a contagem das bolas inferiores, substituo aquela contagem por
inferiores_brancas: 2
A probabilidade 5/6 permanece sendo minha resposta.
```

EvidenceUnits originais (offsets `[start,end)` do recibo, sem normalizar a fonte):

**`E003:p3:13b002527f6ee653e3f2`** — source_evidence_ids `["E003"]`, offsets `[49,70)`.

```text
inferiores_brancas: 5
```

Asserted content: `inferiores_brancas: 5`. Payload: `5`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| a / inferiores_brancas / math | abandoned / positive | false / true | main_argument / true | ["a.bottom_white_count"] / DETERMINISTIC |

**`E004:p3:ea550b0947d4dca94bd0`** — source_evidence_ids `["E004"]`, offsets `[71,91)`.

```text
primeira_branca: 5/6
```

Asserted content: `primeira_branca: 5/6`. Payload: `5/6`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| a / primeira_branca / math | asserted / positive | false / false | main_argument / true | ["a.first_white_probability"] / DETERMINISTIC |

**`E005:p3:15a5516133c2a6591d23`** — source_evidence_ids `["E005", "E006"]`, offsets `[92,194)`.

```text
Corrigindo apenas a contagem das bolas inferiores, substituo aquela contagem por
inferiores_brancas: 2
```

Asserted content: `inferiores_brancas: 2`. Payload: `2`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| a / inferiores_brancas / math | asserted / positive | false / false | main_argument / true | ["a.bottom_white_count"] / DETERMINISTIC |

**`E007:p3:07fc9a20f2dd6655d7ff`** — source_evidence_ids `["E007"]`, offsets `[195,246)`.

```text
A probabilidade 5/6 permanece sendo minha resposta.
```

Asserted content: `A probabilidade 5/6 permanece sendo minha resposta.`. Payload: `5/6`.

| item / subject / tipo | assertion_status / polarity | hypothetical / model_abandoned | scope / atribuído ao aluno | obligation_candidates / rota sugerida |
| --- | --- | --- | --- | --- |
| a / primeira_branca / math | asserted / positive | false / false | final_conclusion / true | ["a.first_white_probability"] / DETERMINISTIC |

| Claim retomado | Suporte textual reconhecido | Contexto restante válido | Visível para conflito | Razão |
| --- | --- | --- | --- | --- |
| E003:p3:13b002527f6ee653e3f2 | false | true | true | no_unambiguous_local_retraction |

A fonte contém duas quantidades e corrige **apenas** a contagem. `inferiores_brancas:5` está em `[49,70)`; `primeira_branca:5/6` ocupa `[71,91)`; a correção da contagem começa em 92. O gap não é vazio: a probabilidade interposta impede a regra de adjacência. A regra imediata de tail também encontra a probabilidade, não o marcador. O mesmo subject/obrigação da contagem e seu alvo textual explícito não chegam a superar essa barreira.

É autocorreção parcial local, não retratação da probabilidade nem ambiguidade sobre o alvo. A contagem 2 é verificada; 5/6 continua asserted e é corretamente DETERMINISTIC_FAILED. O guard adicional refuta a contagem retirada 5 contra white_count=2, bloqueando a.count. Essa perda é independente da probabilidade falsa: a pauta a é aditiva e a.count não depende de a.probability.

| Guard / checker | Evidências usadas | Resultado | Conflito / award | Impacto |
| --- | --- | --- | --- | --- |
| tme2-p3-check.v1 | ["E003:p3:13b002527f6ee653e3f2"] | DETERMINISTIC_FAILED; mathematical_refutation=true | a.bottom_white_count não resolvido; blocked_conflict | a.count: 2→0; score esperado 2, observado 0 |

Classificação: **SUBJECT_SPECIFIC_RETRACTION_BLOCKED_BY_ADJACENCY**; categoria principal ABANDONMENT_POLICY, consequência GUARD_FALSE_POSITIVE. Não é hipótese/citação nem posição matemática atual. A retirada deve afetar o claim anterior, mantendo o novo elegível somente após checker.

Referências: [tme_semantic_formal_p3/abandonment.py:36](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/abandonment.py:36) (suporte textual), [tme_semantic_formal_p3/abandonment.py:76](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/abandonment.py:76) (cópia para segurança), [tme_semantic_formal_p3/abandonment.py:108](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/abandonment.py:108) (checks regulares), [composição da estratégia](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/lean/student_claim_checkers/tme2_p3.py:169).

### 2.5 Segundo caminho de veto: guard_bridge determinístico

Os quatro eventos acima estão em `abandonment_guard_results`. A reconciliação também recebe um **guard_bridge** separado, produzido por `audit_p3_checker_first(document.items, use_lean=False)` diretamente da fonte original, antes de aplicar as decisões de abandono. Os recibos de conflito conservam essa visão em `guard_evidence`/`guard_source_records`:

| Caso | guard_evidence da mesma obrigação | Registros nativos considerados |
| --- | --- | --- |
| S1_02 | indeterminate / CONFLICTING_FACT_RESULTS; um refuted e um supported | pares_ordenados: 6*5=30; pares_ordenados: 6^2=36 |
| S1_03 | indeterminate / NO_EXISTING_FACT | nenhum |
| S1_07 | indeterminate / CONFLICTING_FACT_RESULTS; um refuted e um supported | continuar: {2,3}; continuar: {1,2} |
| S4_07 | indeterminate / CONFLICTING_FACT_RESULTS; um refuted e um supported | inferiores_brancas: 5; inferiores_brancas: 2 |
| E02 replay | indeterminate / NO_EXISTING_FACT | nenhum |

Nos três casos com `CONFLICTING_FACT_RESULTS`, os registros nativos têm semantic_role=intermediate. O guard_bridge não recebe a exclusão da posição superseded. O checker-first transforma esse motivo em conflito; `reconcile()` também bloqueia quando a obrigação está em `guard_conflicts`. **Há, portanto, dois caminhos suficientes de veto nesses três casos:** guard regular de abandono e conflito determinístico da fonte. Esta conclusão decorre dos recibos e das condições alternativas no código; não foi feito rerun removendo guards.

Os quatro eventos continuam sendo quatro, e a perda continua somando 7 pontos: o segundo canal não acrescenta novas parcelas. Ele impede atribuir toda a perda exclusivamente ao novo validador de abandono e mostra que corrigir apenas seu reconhecimento textual não basta. Classificação adicional para S1_02/S1_07/S4_07: **DISCOURSE_STATE_NOT_SHARED_WITH_SOURCE_GUARD**. S1_03 e E02 não têm esse segundo veto registrado.

Referências: [engine.py:130](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:130), [reconcile:35](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:35), [checker-first:163](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_p3_checker_first/engine.py:163).

## 3. False credit × guard false positive: teste da hipótese comum

**A hipótese de uma única política binária como causa raiz suficiente é rejeitada.** Existe uma fragilidade arquitetural comum de representar rejeição/visibilidade por flags e status genéricos, mas os caminhos executados são diferentes. Não é demonstrável corrigir os dois falsos créditos apenas ampliando a regra de abandono.

| Dimensão | S2_03, falso crédito | S2_06, falso crédito | Quatro guard FPs / E02 |
| --- | --- | --- | --- |
| model_abandoned | false em ambos os claims | false nos três | true nos claims retirados |
| Análise textual de abandono | não executada | não executada | executada, suporte=false indevido |
| Marcador | “Também”, adoção | “Apesar… mantenho”, adoção | correção/retirada/substituição explícita |
| Proximidade / envelopes | não explica o erro | não explica o erro | sobreposição/interior em S1_02/S1_07/E02; marcador interior em S1_03; sujeito interposto em S4_07 |
| Subject / obligation | obligation correta, subject unmapped | ambos corretos; duas obrigações relacionadas | mesmo subject/família entre anterior e final; S4_07 distingue contagem e probabilidade |
| Ordem textual | soma incompatível após lista | guard é executado depois do check positivo | uso de start/end exige final não sobreposto e gap vazio |
| Correção incompatível | não há correção | não há correção | sim para a propriedade substituída; não necessariamente muda todo número |
| Scope/parágrafo | main_argument, adotado | main_argument e final_conclusion, adotados | predominante mesmo parágrafo; exploration em S1_07 é reativado pela cópia |
| Adoção final | ambas mantidas | enumeração falsa mantida | somente correção deve valer, salvo probabilidade explicitamente mantida em S4_07 |
| Destino negativo | sem checker nem veto | refutação presente, dependência de veto perdida | posição retirada convertida em veto |

Três mecanismos de segurança precisam ser distinguidos:

1. **Visibilidade não é executabilidade.** Uma fonte adotada não deixa de ser relevante porque o payload é qualitative/unmapped ou não cabe no parser de conjunto. É correto negar crédito à representação inválida; não é correto concluir que ela é não adotada ou irrelevante para conflito.
2. **Visibilidade local não fecha dependências.** S2_06 demonstra que preservar/refutar o membership é insuficiente se `source_consistency` da conclusão usa uma visão anterior e incompleta. Não se resolve esse caso apenas mantendo mais claims ativos.
3. **Vínculo de retratação não é adjacência de envelopes.** Spans amplos são válidos pelo contrato de binding, mas fazem marcadores e correções cair dentro do envelope anterior. O validador trata isso como falta de suporte e reativa conteúdo corretamente abandonado pelo modelo.

Os flags do modelo ainda não podem ser autoridade final. O fato de o modelo acertar o abandono nesses exemplos não autoriza aceitar todos os `abandoned=true`. A separação deve preservar casos sem suporte textual e distinguir ambiguidade de adoção comprovada.

## 4. E02: controle com 4 versus execução real com 2

São três evidências distintas: chamada histórica pré-fix (4), controle pós-fix usando resposta gravada/zero API (4), replay real pós-fix (2). Não se confunde o controle com nova extração.

Controle lido: [result.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_abandonment_safety_fix_01/focal_receipts/test_recorded_e02_e04_without_0/result.json). Teste que o produziu: [test_recorded_e02_e04_without_api](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_abandonment_safety.py:144). Histórico: [p3_rob_e02.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_e02.json).

Recibo: [p3_rob_e02.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/observed_regression/tme_semantic_formal/p3_rob_e02.json).

Fonte integral:

```text
a) Há duas bolas brancas embaixo.
b) Ao repetir o mesmo compartimento, o quinto também libera branca.
Na verdade, ao repetir o mesmo compartimento, somente o sexto libera branca.
```

| Aspecto | Controle pós-fix gravado | Replay real pós-fix |
| --- | --- | --- |
| API calls | 0, extraction_provider com RECORDED | 1, gpt-6.1-sol/medium |
| Claim antigo: source IDs | [E004] | [E004,E005] |
| Span antigo | `[37,101)`, só frase do quinto | `[37,178)`, frase do quinto **e** correção |
| Payload antigo | “Ao repetir o mesmo compartimento, o 5 também libera branca.” | “Ao repetir o mesmo compartimento, o compartimento 5 também libera branca.” |
| asserted_content antigo | apenas frase do quinto | apenas frase do quinto |
| Flags antigos | abandoned / positive; abandoned=true; hypothetical=false | iguais |
| Claim final | `[102,178)`, {6}, asserted, final_conclusion | idêntico, inclusive evidence_id |
| Abandono textual reconhecido | true / adjacent_same_subject_correction | false / no_unambiguous_local_retraction |
| Visibilidade antiga | false | true na cópia de segurança |
| Guard | nenhum | membership do quinto refutado |
| b.same | 2 | 0, blocked_conflict |
| a.count independente | 2 | 2 |
| Score | 4 | 2 |

O código da configuração registrado no controle é idêntico, nos hashes compartilhados, ao da execução sob 89cda1c; o `code_sha` do controle é f335760… porque ele foi salvo antes do commit, com o fix no worktree. Não se usa apenas esse SHA antigo para atribuir o comportamento à versão pré-fix. Fonte e hash da fonte são iguais nos três recibos. O controle usa use_lean=false e o replay use_lean=true; as obrigações a.count/b.same deste controle são determinísticas, e essa diferença não explica o veto observado.

**O extractor mudou a representação?** Sim: ampliou source_evidence_ids/source_span do claim antigo e variou a frase normalizada. O raw_output já contém o envelope ampliado; não foi inventado pelo binder. Este apenas confirma correspondência literal ao envelope selecionado. A EvidenceUnit final `{6}` é a mesma do controle.

**Autocorreção identificada?** Pelo LLM, sim: claim antigo abandoned=true/abandoned, final asserted. Pela validação textual efetiva, não. A fonte contém vínculo local inequívoco conforme política previamente esclarecida. Não é abandono sem suporte, embora assim tenha sido classificado pelo validador.

**Ponto exato:** no replay, `correction.source_start=102 < old.source_end=178`, de modo que `abandonment_support` descarta a comparação por sobreposição. O tail do claim antigo está vazio; o reconhecimento de marcador interior não contempla “Na verdade”. No controle, 102≥101, gap apenas newline, mesmo item/subject/obligation e payloads escritos incompatíveis permitem `adjacent_same_subject_correction`.

**Claims ativos e superseded:** semanticamente o quinto está superseded e o sexto ativo. No crédito positivo, o quinto continua rejeitado; no caminho de segurança, sua cópia é reativada como asserted/not abandoned/main_argument. O sexto é verificado (`DETERMINISTIC_VERIFIED`, sufficient=true), mas perde b.same pelo conflito. Portanto o flag de abandono não foi apagado do recibo original; houve duas visões incompatíveis da evidência.

**Guard e pontos:** guard do token `quinto`, offsets `[73,79)`, checker `frozen_finite_certificate_same_white_membership`, `DETERMINISTIC_FAILED`, award_eligible=false. O quinto realmente não produz branca; esse resultado não deveria vetar o sexto após retratação. Reconciliador cria conflito em b.same_compartment, award=`blocked_conflict`. A contagem inicial de duas brancas permanece verificada e pontua a.count=2.

Classificação: **EXTRACTION_VARIANCE (envelope) + ABANDONMENT_POLICY → GUARD_FALSE_POSITIVE**. A mudança de envelope expõe uma política que não é invariante à segmentação válida da mesma retratação. A expectativa continua 4; o histórico expected=2 não foi editado, e o sidecar de política anterior ao replay preserva a revisão autorizada.

Referências: [tme_semantic_formal_p3/evidence.py:37](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/evidence.py:37) e [tme_semantic_formal_p3/abandonment.py:36](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/abandonment.py:36).

## 5. A08 e E08: comparação das representações

Fonte literal, payload de entrada, schema do extractor e configuração do extractor são iguais entre a realização histórica e o replay em cada caso. Mapper, evidence binding, verification, checkers e pauta também têm hashes iguais; as alterações de source_files entre versões são engine/abandonment/conflict_guard. Esses dois casos não produziram abandonment_decisions nem guards. A divergência de payload na resposta está comprovada, mas uma única amostra não estima sua frequência.

### 5.1 A08 — EXTRACTION_VARIANCE → MAPPING_MISS

Recibo: [p3_rob_a08.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/observed_regression/tme_semantic_formal/p3_rob_a08.json).

Fonte integral:

```text
c) A probabilidade total de vitória é um sexto, com (2/6)*(1/2)=1/6.
Após sair branca do compartimento 2, escolho cinza, que aparece três vezes.
No caso 2, a probabilidade condicional de sucesso é 3/6=1/2.
O jogo continua somente nos compartimentos 1 e 2.
Após sair branca do compartimento 1, escolho preta, que aparece três vezes.
No caso 1, a probabilidade condicional de sucesso é 3/6=1/2.
```

- Histórico: 8; replay: 6; expected: 8. Parcela perdida: `c.total=2`, obrigação `c.total_win_probability`.
- Span nos dois: `A probabilidade total de vitória é um sexto, com (2/6)*(1/2)=1/6.`
- Histórico: payload `(2/6)*(1/2)=1/6`, EvidenceUnit `E002:p3:ffeb84fbc28c74f67dce`.
- Replay: payload `1/6, com (2/6)*(1/2)=1/6`, EvidenceUnit `E002:p3:eb35b237530d2a890df9`.
- Contexto: total do item c, math/asserted/positive, final_conclusion, atribuído ao aluno, hypothetical=false, abandoned=false. Não há correção nem citação.
- Histórico: mapping COMPOSITE aceito, checker `tme2-p3-check.v1`, `COMPOSITE_VERIFIED`, aritmética `FORMAL_VERIFIED`, sufficient=true; apoiado nas estratégias, condicionais e continuação escritas.
- Replay: `extract_named_math` não aceita o payload contendo prosa; `unsupported_checker_payload` → `CONTEXT_REJECTED`, effective_route COMPOSITE, `FORMAL_NOT_ATTEMPTED`, sufficient=false; **o checker do total não é executado**. Nenhum conflito ou guard. Award `no_sufficient_checker_result`.
- Permanecem `c.continue=1`, `c.first_strategy=2`, `c.second_strategy=2`, `c.conditionals=1`, total 6. A regra c.total exige total + demais obrigações de c, todas as demais satisfeitas; a perda se localiza no total.

Não é falha Lean, refutação, mudança de sufficiency matemática ou supressão de contexto. É variação de normalização que não cumpre o contrato de payload, corretamente recusada para crédito mas sem recuperação conservadora de representação. Não se propõe aceitar texto misto arbitrário ou inferir uma conta ausente: a conta já está na fonte.

### 5.2 E08 — EXTRACTION_VARIANCE → MAPPING_MISS

Recibo: [p3_rob_e08.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/observed_regression/tme_semantic_formal/p3_rob_e08.json).

Fonte integral:

```text
b) Beatriz disse que, ao repetir o mesmo compartimento, o quinto também libera branca.

Minha resposta: ao repetir o mesmo compartimento, somente o sexto libera branca.
```

- Histórico: 2; replay: 0; expected: 2. Parcela perdida: `b.same=2`, obrigação `b.same_compartment`.
- Span da posição própria nos dois: `Minha resposta: ao repetir o mesmo compartimento, somente o sexto libera branca.`
- Histórico: payload `{6}`, EvidenceUnit `E003:p3:f83e8f50ffefab201704`; mapping DETERMINISTIC aceito; checker `tme2-p3-check.v1`, `DETERMINISTIC_VERIFIED`, sufficient=true.
- Replay: payload `Ao repetir o mesmo compartimento, somente o compartimento 6 libera branca.`, EvidenceUnit `E003:p3:04cfeef77873b1de15d7`; subject repeticao_branca, tipo integer_set, asserted/positive, final_conclusion, atribuído ao aluno, hypothetical=false, abandoned=false.
- Mapper rejeita `unsupported_checker_payload`; a rota efetiva é DETERMINISTIC, mas nenhum checker desse claim é executado. `CONTEXT_REJECTED`, `FORMAL_NOT_ATTEMPTED`, sufficient=false; award=`no_sufficient_checker_result`.
- A citação de Beatriz permanece quoted/não adotada e é rejeitada por `nonasserted_or_unattributed_context`. Não há guard atômico, check regular recuperado, abandonment_decision ou conflito. O guard não usa a citação como veto.

Não é CONTEXT_SUPPRESSION da resposta própria: o reset “Minha resposta” e a atribuição própria foram preservados. A perda nasce do payload inteiro em prosa sob um contrato integer_set, não de contaminação pela fala de terceiro.

Históricos comparados: [A08 anterior](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_a08.json) e [E08 anterior](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_e08.json). Ponto comum da rejeição: [tme_semantic_formal_p3/mapper.py:69](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:69).

## 6. Fallback dos 32 novos

Caso **p3_safe_s2_05**, fonte:

Recibo: [p3_safe_s2_05.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_02/new32/tme_semantic_formal/p3_safe_s2_05.json).

Fonte integral:

```text
c) Minha política mantém ambas as escolhas a seguir:
Para a branca que veio do compartimento 2, adoto cinza, que aparece 3 vezes.
Para esse mesmo caso 2, adoto igualmente preta, que aparece 3 vezes.
As duas escolhas ficam como decisões atuais.
```

| Campo | Recibo |
| --- | --- |
| Erro | ValueError:extractor_incomplete_or_refused |
| Estágio | resposta da API com status diferente de completed; antes de salvar raw_output e antes de bind_evidence |
| Chamadas da execução original | 1 |
| Extractor final | unavailable |
| Modo efetivo | TME_CURRENT_FALLBACK |
| Score | 0, numérico |
| Technical uncertainty do score | false |
| EvidenceUnits semânticas úteis | nenhuma incorporada |
| Saída / limite | 16000 tokens / 16000 |
| Latência | 91,623449709 s |
| Retry | max_retries=0; nenhuma repetição nesta auditoria |

O código lança o motivo genérico quando response.status não é completed. O recibo não guarda o status original específico/incomplete_details nem raw_output; portanto não permite afirmar definitivamente recusa ou limite. Consumo igual ao teto é evidência compatível com truncamento, não prova conclusiva da causa. Não é erro de checker, Lean, mapper ou pauta. Classificação: **FALLBACK / EXTRACTION_COMPLETION_FAILURE**.

O score 0 satisfaz a expectativa de construção, mas não demonstra conflito preservado pelo SemanticExtractor. Este caso fica excluído de inferências sobre qualidade semântica: ALL32 versus SEMANTIC-SUCCESS31. A falha de extração continua contada operacionalmente, mesmo com technical_uncertainty=false. Nenhum retry ou ajuste de política foi feito.

Referências: [tme_semantic_formal_p3/extractor.py:68](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/extractor.py:68) e [tme_semantic_formal_p3/engine.py:106](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:106).

## 7. Matriz conceitual de estado discursivo

Esta matriz é recomendação de contrato, não campos já implementados nem nova pauta. A verdade matemática continua separada de adoção discursiva, representabilidade e score. Conflict visibility significa ser considerado para checagem/revisão; não significa refutação automática.

| Estado observado/pretendido | Crédito positivo? | Conflict detection? | Regra e exemplo |
| --- | --- | --- | --- |
| Claim adotado (ACTIVE) | Sim, se fonte/representação/checker/sufficiency forem válidos e não houver veto aplicável | Sim | O conjunto {1,2} de S2_03 é verificável, mas não pode esconder a outra inclusão adotada |
| Claim falso adotado (ACTIVE + refutado) | Não | Sim, pela refutação independente | Membership do terceiro em S2_06; preservar dependência de veto contratada |
| Hipótese não adotada (NON_ADOPTED) | Não | Não como posição do aluno | A condição de caso legítima não deve ser confundida com hipótese exploratória |
| Terceiro não adotado (NON_ADOPTED) | Não | Não como posição do aluno | Citação de Beatriz em E08 |
| Tentativa explicitamente retratada (SUPERSEDED) | Não para o claim antigo | Não contra a correção final; manter histórico | S1_02/S1_03/S1_07: guardar a refutação histórica sem torná-la veto atual |
| Abandonment apenas inferido pelo LLM | Não para esse claim marcado abandonado | Sim, conservadoramente, se fonte própria vinculada; ou review se adoção não resolvida | Flag não é autoridade suficiente para apagar contradição; não equivale a ACTIVE comprovado |
| Autocorreção local inequívoca | Anterior SUPERSEDED; final só pode pontuar após checker | Anterior não deve gerar conflito permanente | E02; aceitar vínculo sustentado mesmo com envelopes sobrepostos |
| Ambíguo (AMBIGUOUS) | Sem crédito positivo automático na parcela afetada | Preservar evidência e aplicar review/withhold local; não declarar refutação sem checker | Não usar último texto, confiança LLM ou resposta numericamente correta como desempate |
| Adotado, mas representação não executável | Não pelo claim não executável; também não presumir segurança de positivo concorrente | Sim como pendência de segurança, sem inventar falsidade/conjunto | S2_03; ACTIVE é independente de checker_payload_valid |

A linha adicional de representação é necessária pelos artefatos: a rejeição `CONTEXT_REJECTED` abrange tanto não adoção quanto erro de payload. Esta última condição não é estado discursivo. `SUPERSEDED` deve referenciar alvo, marcador, correção e escopo; um enum desacompanhado de recibo apenas transferiria a confiança cega do flag abandoned para outro campo.

## 8. Recomendação arquitetural mínima, sem patch

**Separar explicitamente positive_credit_eligibility, conflict_visibility e discourse_state é apropriado, mas insuficiente sozinho.** O código já separa parcialmente os dois primeiros na cópia de segurança; falta uma decisão discursiva auditável consistente entre canais, cobertura para rejeições de representação e fechamento das dependências negativas.

1. **Estado por claim e relação de substituição vinculada à fonte.** Registrar ACTIVE/SUPERSEDED/NON_ADOPTED/AMBIGUOUS a partir da evidência textual, com alvo da retratação, subject/item/caso, correção e ranges. Distinguir envelope de proveniência da cláusula assertiva e do marcador. Sobreposição de envelopes não invalida por si só um vínculo; proximidade e ordem são evidência, não prova única. A correção pode ser explicitamente limitada a um subject mesmo com outro interposto. Não aceitar “na verdade” sem relação, nem depender de a nova conclusão ser matematicamente verdadeira para reconhecer retirada da antiga.
2. **Representação e discurso como eixos independentes.** Manter rejeição positiva de payload inválido, mas não converter active/unmapped em non-adopted. Uma afirmação ativa ligada à mesma propriedade deve permanecer como pendência de segurança. Se houver representação atômica tipada, extraída literalmente e conferível, enviá-la ao checker apropriado; se não houver, reter a incerteza da parcela afetada para revisão, sem fabricar set completo nem resultado matemático. Um adaptador geral de membership deve distinguir números que indexam compartimentos de números/artigos que quantificam bolas. Normalização de payloads deve preservar operações/valores escritos e evitar depender de prosa incidental no campo executável.
3. **Uma visão discursiva consistente para composição e reconciliação.** Checks positivos só podem compor claims atuais compatíveis; checks de segurança devem indicar se a refutação é histórica, atual ou de atribuição ambígua. A mesma decisão deve governar também o consumo do guard_bridge determinístico da fonte: excluir um claim da cópia de abandono não pode deixá-lo vetando pela leitura nativa. Essa conciliação pertence à camada experimental e exige vínculo de fonte auditável; não implica alterar o TME_CURRENT nem ignorar negativos com base no flag do LLM. O resultado de um guard continua incapaz de pontuar. Refutações atuais devem alcançar somente dependências negativas já previstas pelo contrato, inclusive source_consistency, antes da decisão final de sufficiency/award. A origem — projeção regular ou guard — não deve alterar a aplicabilidade de um veto. Não bloquear todo item nem adicionar dependência positiva de b.same à pauta de b.conclusion.

| Problema | Separar três eixos basta? | Complemento mínimo necessário |
| --- | --- | --- |
| S2_03 falso crédito | Não | Preservação de pendência ativa não representada e checagem atômica/withhold local |
| S2_06 falso crédito | Não | Propagar refutação atual pelas dependências negativas existentes antes do award |
| Quatro guard FPs | Não apenas nomear estados; sim com vínculo textual correto | Resolver supersedes na cláusula, não só nas bordas do envelope, e usar o mesmo estado na cópia de segurança e no consumo do guard_bridge nativo |
| E02 autocorreção legítima | Mesma condição acima | Invariância a segmentações válidas da mesma correção |
| Abandono inferido | Separação ajuda | Sem suporte, não conceder autoridade para suprimir o caminho de segurança; review quando adoção ambígua |
| A08/E08 | Não | Contrato de payload/normalização vinculada à fonte; não há problema de abandono nesses dois |
| Fallback | Não | Questão separada de conclusão/transporte; nenhuma mudança de retry recomendada por estes dados isolados |

Essa é uma correção de contratos de evidência e fluxo negativo, preservando checkers, pesos, resultado versus justificativa e PautaEngine. Não há um patch de uma única regex demonstrado como suficiente. Futuros testes gerais devem variar envelope/segmentação, marcador sem alvo, alvo explícito com outro subject interposto, retratação parcial, ordem de frases, citação, membership parcial e dependência negativa; os resultados esperados devem derivar desses contratos antes de novas chamadas. Proibidos hardcode de case_id, exceções E02/A08/E08 e mudança de expected para acomodar score. Nenhuma dessas recomendações foi implementada.

Preservar distinções epistêmicas: ausência de representação/prova não é FORMAL_REFUTED; rejeição de fonte não é erro matemático; FORMAL_UNPROVED/NOT_ATTEMPTED/ERROR permanecem distintos. Estado discursivo não substitui status de checker. Resultado isolado correto só recebe o crédito que a pauta já permite, sujeito aos vetos existentes.

## 9. Status dos datasets e limites de inferência

- `semantic_robustness_01`: observado/regressão; E02 tem política esclarecida de 4 no sidecar anterior ao replay. A fixture histórica não foi alterada.
- `semantic_safety_02`: avaliação independente em relação à construção do benchmark anterior que revelou falha; **agora observado para tuning/regressão**, sem poder ser reutilizado como teste independente da futura correção.
- Qualquer correção futura deve ser congelada e avaliada posteriormente em um **novo conjunto independente `semantic_safety_03`**, sem reutilização trivial nem expectativa ajustada após notas. Esse novo conjunto não foi criado nesta auditoria.

Não há estimativa de acurácia geral, nova chamada ou inferência de desempenho do extractor baseada no fallback. Resultados de uma realização mostram mecanismos de falha, não frequência populacional. As recomendações são sustentadas pelos traces e pelo fluxo estático; eficácia de um fix permanece por testar.

## 10. Integridade e veredito forense

Conferidos 357 arquivos preexistentes dos artefatos safety_02, robustness_01, controle do fix e das duas fixtures: hashes preservados. Nenhum artefato, fixture, expectation, prompt, código ou checker foi modificado. Não houve API, execução de modo, teste, Lean, tuning, holdout ou commit nesta tarefa. Análise auxiliar temporária apenas fora do repositório; único novo arquivo versionável: este relatório.

HEAD permanece `1b864705017939a6fbf9087888cce3d606cf0de5`; git diff de arquivos rastreados e índice vazio. Estado final:

```text
?? docs/audits/TME_P3_SEMANTIC_SAFETY_02_FORENSIC.md
```

Há uma fragilidade conceitual compartilhada — estado discursivo/representação/visibilidade insuficientemente distinguidos —, mas os mecanismos observados não se reduzem a uma única decisão binária. Foram demonstrados: perda de segurança por representação, falta de propagação de veto, falhas do vínculo de retratação, estado discursivo não compartilhado entre os canais de segurança e variação de payload; fallback permanece uma falha separada com causa específica não conclusiva.

**MULTIPLE_ROOT_CAUSES**
