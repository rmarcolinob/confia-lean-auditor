# TME P3 Semantic Formal DEV01 — Auditoria forense

Data local: 2026-11-05 (America/Fortaleza). Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3`. SHA confirmado: **`e4dc1e94b0e8e22a16489fcdcc3eb14e1abfd4ab`**. Branch: `experiment/tme-semantic-formal-p3`. Estado inicial limpo.

**Veredito: P3_DEV_REQUIRES_FIX.** Há um falso crédito automático material de **2 pontos em b.same, no caso p3_dev_partial_conflict**. O checker verificou corretamente a afirmação isolada `{6}`, mas a camada de representação descartou a afirmação contraditória “o quinto também” sem encaminhá-la como conflito. A reconciliação concedeu a parcela de exclusividade sobre uma resposta que contém duas afirmações incompatíveis.

Dos 4 pontos desse caso, **somente a.count (2) é claramente independente do conflito**. Não é possível confirmar a premissa de que os quatro seriam independentes. O erro não está no valor matemático derivado da máquina; está na autorização de crédito com contradição explícita não reconciliada.

O fallback foi **p3_dev_isolated_answer**. Seus 2 pontos são do TME_CURRENT e ficam excluídos das alegações de desempenho do SemanticExtractor. Nos outros sete casos, foram identificadas 15 parcelas resgatadas legitimamente, somando 28 pontos, e uma parcela indevida de 2 pontos. Não foi calculada acurácia contra gold.

## 1. Escopo, integridade e método

Esta auditoria lê os artefatos existentes, a fonte dos oito casos, a pauta, o código e os arquivos Lean já gerados. **Não executou extractor, API, runner, checker, Lean, testes ou replay.** Não alterou código, fixtures, prompt, expectativas ou relatórios anteriores. A única saída no repositório é este documento. Não acessou gold externo ou holdout.

Fontes primárias:

- [Fontes DEV congeladas](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/dev_sources.json).
- [Artefatos TME_CURRENT](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_current).
- [Artefatos TME_SEMANTIC_FORMAL](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_semantic_formal).
- [Pauta operacional](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/examples/pautas/tme2_problem3.v1.json), [máquina](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/examples/pautas/tme2_problem3.machine.v1.json) e [contrato checker-first](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_CHECKER_COVERAGE_02.md).
- [Política de conflitos documentada antes do DEV](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_SEMANTIC_FORMAL_IMPLEMENTACAO_01.md:84).

Os dois manifests registram o SHA acima e worktree limpo. O Current ocorreu em 05/11/2026, 22:20:05; o Semantic em 22:20:14–22:22:01, hora de Fortaleza. Os timestamps UTC nos JSON são 06/11/2026, 01:20–01:22; não são uma divergência de data.

Conferidos: hashes dos sete módulos experimentais contra ambos os manifests; hashes dos bytes de dataset/IDs; igualdade entre cada source_text dos 16 resultados e sua fixture; igualdade literal de todos os 26 source spans com seus offsets na fonte. Os cinco arquivos Lean citados existem, têm as proposições registradas e seus recibos indicam compiled=true. Não foram recompilados.

```text
dev_sources.json SHA-256: d12a77cd87f0e5197db7e3cdafaedf78a130dd7dc3b1b59fa5d029a702e375cc
dev_ids.json SHA-256:     a7ab3a65f60e1284b119c8974a47e3eea0c037f58c96963bff8c7372ebcaab0a
```

O julgamento de parcelas abaixo parte do que está escrito e dos requisitos congelados, não da nota retornada. Os números de parcelas legítimas são conclusões desta auditoria, não novos alvos salvos nas fixtures. O artefato preserva as notas originais, inclusive a nota 4 do caso com falso crédito.

## 2. Pauta e critério de julgamento

| Regra | Pontos | Obrigação / dependência congelada |
| --- | --- | --- |
| a.count | 2 | a.bottom_white_count |
| a.probability | 2 | a.first_white_probability; valor isolado autorizado |
| b.space | 2 | b.ordered_pairs; relação de duas escolhas escrita no contrato fortalecido |
| b.different | 2 | b.different_favorable; relação de contagem escrita |
| b.same | 2 | b.same_compartment; exclusividade da repetição do sexto |
| b.conclusion | 2 | b.second_white_probability; resultado pode usar rota própria, sem demonstrar método |
| b.alternative | 8 alternativos | b.alternative_complete; árvore completa, max_of com a soma de b.counting |
| c.continue | 1 | c.continue_compartments |
| c.first_strategy | 2 | c.strategy_case_1; cor ótima e contagem no caso 1 |
| c.second_strategy | 2 | c.strategy_case_2; cor ótima e contagem no caso 2 |
| c.conditionals | 1 conjunto | all_of das duas conditional_success e duas strategy_case |
| c.total | 2 | all_of do total, continuação, duas estratégias e duas condicionais |

Não se dividiu c.conditionals em duas parcelas. Nenhum método alternativo foi inventado para estes casos. O max_of de b não foi somado ao caminho de contagem. A política congelada bloqueia award automático de obrigação materialmente contraditória sem precedência explícita; a ordem textual não define precedência.

LEGITIMATE_CREDIT significa parcela concedida sustentada pela fonte, checker e política. FALSE_CREDIT inclui crédito sem reconciliação necessária, mesmo se o fragmento escolhido for verdadeiro. QUESTIONABLE_CREDIT seria suporte insuficiente para conclusão firme; não foi necessário deixar nenhuma parcela concedida nessa categoria. MISSED_CREDIT indica parcela claramente satisfeita e perdida. PAUTA_AMBIGUOUS seria usado se o contrato congelado não resolvesse o requisito; não há caso decisivo ambíguo nesta amostra. Em particular, não se está criando agora a regra de veto de conflito.

## 3. Fallback: p3_dev_isolated_answer

- Motivo gravado: `InternalServerError`.
- Estágio: chamada à API em `client.responses.create`, antes de obter output útil, binding, mapeamento e checker semântico-experimental.
- `api_calls=1`, `status=unavailable`, latência registrada 0,444808042 s; configuração `max_retries=0`.
- Sem `raw_output`, `response_id` ou `usage` no recibo; `extracted_evidence=[]`, mapping/projection vazios.
- Modo efetivo: `TME_CURRENT_FALLBACK`; `fallback=true`, `fallback_used=true`.
- Score devolvido: **2**, por a.probability com verificação determinística do baseline; FORMAL_NOT_ATTEMPTED.
- Houve tentativa de chamada, **não houve extração útil observável antes da falha**. Não se infere dos logs se algum cálculo interno do servidor aconteceu. O artefato não guarda corpo HTTP nem causa interna, portanto não permite diagnóstico mais fino do servidor.

Essa nota valida o comportamento de fallback e a preservação do parcial de a; não demonstra que o SemanticExtractor interpretou corretamente `1/3`. O caso está fora de SEMANTIC-SUCCESS7.

## 4. Reconstrução individual dos oito casos

Notação: offsets `[início,fim)` são índices Unicode da fonte original; os prefixos E002 etc. são locais a cada caso. Cada EvidenceUnit é identificada integralmente nas tabelas. A tabela de verificação explicita a cadeia **span → claim → obrigação → rota → checker → status → sufficiency → award**. “Suficiente” refere-se à decisão registrada do sistema; a classificação forense das parcelas é apresentada separadamente e pode discordar dela.

### 4.1. p3_dev_initial_count

Current **0**; Semantic solicitado **4**; fallback **false**; modo efetivo **TME_SEMANTIC_FORMAL**.

Fonte original completa:

```text
a) Há duas bolas brancas embaixo. A probabilidade da primeira branca é 2/6=1/3.
```

Artefatos: [Current](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_current/p3_dev_initial_count.json) · [Semantic](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_semantic_formal/p3_dev_initial_count.json).

| Span | Offsets | Texto literal |
| --- | --- | --- |
| S1 | [3,79) | Há duas bolas brancas embaixo. A probabilidade da primeira branca é 2/6=1/3. |

| EvidenceUnit | Fonte | Subject / tipo | Claim normalizado | Contexto | Rota sugerida |
| --- | --- | --- | --- | --- | --- |
| E002:p3:47c304b74e85c088544f | S1 | inferiores_brancas / math | 2 | asserted; positive; main_argument; H=False; A=False; aluno=True | DETERMINISTIC |
| E002:p3:af8824085a07f87e10c2 | S1 | primeira_branca / math | 2/6=1/3 | asserted; positive; final_conclusion; H=False; A=False; aluno=True | DETERMINISTIC |

| EvidenceUnit | Obrigação | Rota efetiva | Mapeamento |
| --- | --- | --- | --- |
| E002:p3:47c304b74e85c088544f | a.bottom_white_count | DETERMINISTIC | aceito: compatible_pending_checker |
| E002:p3:af8824085a07f87e10c2 | a.first_white_probability | FORMAL | aceito: compatible_pending_checker |

| Resultado / obrigação | EvidenceUnits → claim | Rota | Checker | Estado epistêmico | Sufficiency registrada | Usado no award | Motivo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1: a.bottom_white_count | E002:p3:47c304b74e85c088544f | DETERMINISTIC | P3Checks/_a + contagem nas pilhas | DETERMINISTIC_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V2: a.first_white_probability | E002:p3:af8824085a07f87e10c2 | FORMAL | P3Checks.numerical/_a + racional exato/Lean quando executado | FORMAL_VERIFIED; FORMAL_VERIFIED | True | sim | EXISTING_VERIFICATION_RESULT |

Componentes lógicos/metadados de V1 (subchecks=[] no recibo): engine_derived={"initial_bottom_colors": ["white", "white", "gray", "black", "gray", "black"], "white_count": 2}.

Recibo Lean de V2: `compiled=True`, stdout='', stderr=''; proposição `((2 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (3 : ℚ))`; [arquivo executado](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/student_claim_checks/p3-semantic-formal-aa1e8f14b66948668f59ed321fd6c15a/rational_check_0.lean).

Conflitos/reconciliação registrados: nenhum.

| Parcela concedida | Pontos | Obrigações na regra | Classificação forense |
| --- | --- | --- | --- |
| a.count | 2.0 | a.bottom_white_count | LEGITIMATE_CREDIT |
| a.probability | 2.0 | a.first_white_probability | LEGITIMATE_CREDIT |

Fechamento registrado: soma das parcelas = **4**, score final = **4**. Demais parcelas: zero. Nenhuma pontuação foi alterada pela auditoria.

**Julgamento pela fonte:** “duas bolas brancas embaixo” satisfaz a.count; a igualdade 2/6=1/3 expressa a probabilidade da primeira branca e satisfaz a.probability. São duas parcelas independentes claramente presentes: 2+2. O checker deriva duas brancas das pilhas e o recibo Lean prova a igualdade em ℚ. Nenhum outro ponto é justificado ou concedido.

**Current:** extraiu somente a igualdade genérica, sem quantity=primeira_branca, e não criou a contagem verbal. A igualdade está dentro de uma linha em prosa, portanto não atende standalone_math. `facts=[]`, score 0. Causas: EXTRACTION_MISS na contagem; STRUCTURE_MISS na vinculação da probabilidade; efeito BASELINE_UNDER_CREDIT. Duas parcelas/4 pontos legítimos perdidos pelo Current; zero pelo Semantic.

Registros Current preservados (para localizar a perda antes da pontuação):

| Texto capturado | Subject | Role | Atribuível |
| --- | --- | --- | --- |
| 2/6=1/3 | expression | intermediate | True |

Fatos Current: nenhum.

### 4.2. p3_dev_isolated_answer

Current **2**; Semantic solicitado **2**; fallback **true**; modo efetivo **TME_CURRENT_FALLBACK**.

Fonte original completa:

```text
a) 1/3
```

Artefatos: [Current](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_current/p3_dev_isolated_answer.json) · [Semantic](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_semantic_formal/p3_dev_isolated_answer.json).

Sem claims extraídos pelo SemanticExtractor; a cadeia abaixo é exclusivamente do baseline de fallback. Span literal `1/3`, na fonte original `[3,6)`, registro genérico do baseline → a.first_white_probability → DETERMINISTIC → P3Checks.numerical → verified → evidência supported → a.probability=2.

| Resultado / obrigação | EvidenceUnits → claim | Rota | Checker | Estado epistêmico | Sufficiency registrada | Usado no award | Motivo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1: a.first_white_probability | registro baseline | DETERMINISTIC | P3Checks.numerical/_a + racional exato/Lean quando executado | DETERMINISTIC_VERIFIED; FORMAL_NOT_ATTEMPTED | supported na bridge baseline | sim |  |

Conflitos/reconciliação registrados: nenhum.

| Parcela concedida | Pontos | Obrigações na regra | Classificação forense |
| --- | --- | --- | --- |
| a.probability | 2.0 | a.first_white_probability | LEGITIMATE_CREDIT |

Fechamento registrado: soma das parcelas = **2**, score final = **2**. Demais parcelas: zero. Nenhuma pontuação foi alterada pela auditoria.

**Julgamento pela fonte:** o item a contém exatamente 1/3. A autorização explícita de resposta isolada dá a.probability=2; não há afirmação de duas bolas brancas para a.count. O baseline reconhece a expressão inteira como standalone_math e calcula a razão correta. Current=2 e fallback=2, ambos legítimos. Não há resgate semântico ou MISSED_CREDIT. O extractor não produziu EvidenceUnits neste caso.

Registros Current preservados (para localizar a perda antes da pontuação):

| Texto capturado | Subject | Role | Atribuível |
| --- | --- | --- | --- |
| 1/3 | expression | intermediate | True |

Fatos Current: a.first_white_probability=verified.

### 4.3. p3_dev_sample_space

Current **0**; Semantic solicitado **2**; fallback **false**; modo efetivo **TME_SEMANTIC_FORMAL**.

Fonte original completa:

```text
b) As duas escolhas de compartimento são uniformes. O espaço amostral de pares ordenados tem 6*6=36 possibilidades.
```

Artefatos: [Current](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_current/p3_dev_sample_space.json) · [Semantic](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_semantic_formal/p3_dev_sample_space.json).

| Span | Offsets | Texto literal |
| --- | --- | --- |
| S1 | [3,115) | As duas escolhas de compartimento são uniformes. O espaço amostral de pares ordenados tem 6*6=36 possibilidades. |

| EvidenceUnit | Fonte | Subject / tipo | Claim normalizado | Contexto | Rota sugerida |
| --- | --- | --- | --- | --- | --- |
| E002:p3:880e53f1c99471ea4a3e | S1 | unmapped / qualitative | As duas escolhas de compartimento são uniformes. | asserted; positive; main_argument; H=False; A=False; aluno=True | SEMANTIC |
| E002:p3:a306b065c3ae26aef7a0 | S1 | pares_ordenados / math | 6*6=36 | asserted; positive; main_argument; H=False; A=False; aluno=True | COMPOSITE |

| EvidenceUnit | Obrigação | Rota efetiva | Mapeamento |
| --- | --- | --- | --- |
| E002:p3:880e53f1c99471ea4a3e | b.ordered_pairs | COMPOSITE | rejeitado: obligation_subject_type_mismatch |
| E002:p3:a306b065c3ae26aef7a0 | b.ordered_pairs | COMPOSITE | aceito: compatible_pending_checker |

| Resultado / obrigação | EvidenceUnits → claim | Rota | Checker | Estado epistêmico | Sufficiency registrada | Usado no award | Motivo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1: b.ordered_pairs | E002:p3:a306b065c3ae26aef7a0 | COMPOSITE | StrongP3Checks.observe + finite_certificate + count_relation(sample) | COMPOSITE_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V2: b.ordered_pairs | E002:p3:880e53f1c99471ea4a3e | COMPOSITE | não executado para este claim | CONTEXT_REJECTED; FORMAL_NOT_ATTEMPTED | False | não | obligation_subject_type_mismatch |

Componentes de V1 (b.ordered_pairs):

| Componente | Status | Razão |
| --- | --- | --- |
| arithmetic | DETERMINISTIC_VERIFIED | existing_exact_arithmetic |
| finite_machine | DETERMINISTIC_VERIFIED | two_actual_withdrawals_and_uniform_measure |
| written_relation | DETERMINISTIC_VERIFIED | two_uniform_choices_written |

Conflitos/reconciliação registrados: nenhum.

| Parcela concedida | Pontos | Obrigações na regra | Classificação forense |
| --- | --- | --- | --- |
| b.space | 2.0 | b.ordered_pairs | LEGITIMATE_CREDIT |

Fechamento registrado: soma das parcelas = **2**, score final = **2**. Demais parcelas: zero. Nenhuma pontuação foi alterada pela auditoria.

**Julgamento pela fonte:** há duas escolhas explicitamente uniformes e a relação 6*6=36 atribuída ao espaço amostral de pares ordenados. b.space=2 é legítimo; nenhuma contagem de favoráveis foi escrita. O composto valida aritmética, enumeração finita e relação de duas escolhas. A afirmação qualitativa de uniformidade foi preservada como unmapped e rejeitada por incompatibilidade subject/type. Ela não recebe award; o claim matemático independente escrito recebe a parcela. A uniformidade usada matematicamente é premissa do enunciado, conforme o checker-first.

**Current:** guardou 6*6=36 como matemática genérica, sem subject pares_ordenados; não produziu fato. STRUCTURE_MISS → BASELINE_UNDER_CREDIT, 1 parcela/2 pontos perdidos. Não é falha aritmética nem um crédito semântico baseado apenas na palavra “uniformes”.

Registros Current preservados (para localizar a perda antes da pontuação):

| Texto capturado | Subject | Role | Atribuível |
| --- | --- | --- | --- |
| 6*6=36 | expression | intermediate | True |

Fatos Current: nenhum.

### 4.4. p3_dev_favorable_partition

Current **0**; Semantic solicitado **8**; fallback **false**; modo efetivo **TME_SEMANTIC_FORMAL**.

Fonte original completa:

```text
b) Para os pares ordenados, 6*6=36.
Os casos favoráveis com compartimentos diferentes são 2*5=10.
Ao repetir o mesmo compartimento, somente o sexto libera branca.
A probabilidade da segunda branca é (10+1)/36=11/36.
```

Artefatos: [Current](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_current/p3_dev_favorable_partition.json) · [Semantic](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_semantic_formal/p3_dev_favorable_partition.json).

| Span | Offsets | Texto literal |
| --- | --- | --- |
| S1 | [3,35) | Para os pares ordenados, 6*6=36. |
| S2 | [36,97) | Os casos favoráveis com compartimentos diferentes são 2*5=10. |
| S3 | [98,162) | Ao repetir o mesmo compartimento, somente o sexto libera branca. |
| S4 | [163,215) | A probabilidade da segunda branca é (10+1)/36=11/36. |

| EvidenceUnit | Fonte | Subject / tipo | Claim normalizado | Contexto | Rota sugerida |
| --- | --- | --- | --- | --- | --- |
| E002:p3:a02d9d240ef5f924e9d1 | S1 | pares_ordenados / math | 6*6=36 | asserted; positive; main_argument; H=False; A=False; aluno=True | COMPOSITE |
| E003:p3:4508e11155b1e55714ec | S2 | favoraveis_distintos / math | 2*5=10 | asserted; positive; main_argument; H=False; A=False; aluno=True | COMPOSITE |
| E004:p3:aff78edc757df0ffe850 | S3 | repeticao_branca / integer_set | {6} | asserted; positive; main_argument; H=False; A=False; aluno=True | DETERMINISTIC |
| E005:p3:4d512cb1b671a5f7f270 | S4 | segunda_branca / math | (10+1)/36=11/36 | asserted; positive; final_conclusion; H=False; A=False; aluno=True | COMPOSITE |

| EvidenceUnit | Obrigação | Rota efetiva | Mapeamento |
| --- | --- | --- | --- |
| E002:p3:a02d9d240ef5f924e9d1 | b.ordered_pairs | COMPOSITE | aceito: compatible_pending_checker |
| E003:p3:4508e11155b1e55714ec | b.different_favorable | COMPOSITE | aceito: compatible_pending_checker |
| E004:p3:aff78edc757df0ffe850 | b.same_compartment | DETERMINISTIC | aceito: compatible_pending_checker |
| E005:p3:4d512cb1b671a5f7f270 | b.second_white_probability | COMPOSITE | aceito: compatible_pending_checker |

| Resultado / obrigação | EvidenceUnits → claim | Rota | Checker | Estado epistêmico | Sufficiency registrada | Usado no award | Motivo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1: b.ordered_pairs | E002:p3:a02d9d240ef5f924e9d1 | COMPOSITE | StrongP3Checks.observe + finite_certificate + count_relation(sample) | COMPOSITE_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V2: b.different_favorable | E003:p3:4508e11155b1e55714ec | COMPOSITE | StrongP3Checks.observe + finite_certificate + count_relation(different) | COMPOSITE_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V3: b.same_compartment | E004:p3:aff78edc757df0ffe850 | DETERMINISTIC | P3Checks/_b + igualdade do conjunto com diagonal branca | DETERMINISTIC_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V4: b.second_white_probability | E005:p3:4d512cb1b671a5f7f270 | COMPOSITE | StrongP3Checks.numerical + certificado + relação/contrato de valor | COMPOSITE_VERIFIED; FORMAL_VERIFIED | True | sim | EXISTING_VERIFICATION_RESULT |

Componentes de V1 (b.ordered_pairs):

| Componente | Status | Razão |
| --- | --- | --- |
| arithmetic | DETERMINISTIC_VERIFIED | existing_exact_arithmetic |
| finite_machine | DETERMINISTIC_VERIFIED | two_actual_withdrawals_and_uniform_measure |
| written_relation | DETERMINISTIC_VERIFIED | two_uniform_choices_written |

Componentes de V2 (b.different_favorable):

| Componente | Status | Razão |
| --- | --- | --- |
| arithmetic | DETERMINISTIC_VERIFIED | existing_exact_arithmetic |
| finite_machine | DETERMINISTIC_VERIFIED | two_actual_withdrawals_and_uniform_measure |
| written_relation | DETERMINISTIC_VERIFIED | white_second_choice_and_distinct_first_choices_written |

Componentes lógicos/metadados de V3 (subchecks=[] no recibo): engine_derived={"same_compartment_favorable": [6]}.

Componentes de V4 (b.second_white_probability):

| Componente | Status | Razão |
| --- | --- | --- |
| arithmetic | FORMAL_VERIFIED | existing_exact_arithmetic |
| finite_machine | DETERMINISTIC_VERIFIED | two_actual_withdrawals_and_uniform_measure |
| source_consistency | DETERMINISTIC_VERIFIED | no_negative_context |
| written_relation | DETERMINISTIC_VERIFIED | disjoint_favorable_partition_written |

Recibo Lean de V4: `compiled=True`, stdout='', stderr=''; proposição `(((10 : ℚ) + (1 : ℚ)) / (36 : ℚ)) = ((11 : ℚ) / (36 : ℚ))`; [arquivo executado](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/student_claim_checks/p3-semantic-formal-04f1652b11dc4287a8c20d74ea86c04f/rational_check_0.lean).

Conflitos/reconciliação registrados: nenhum.

| Parcela concedida | Pontos | Obrigações na regra | Classificação forense |
| --- | --- | --- | --- |
| b.space | 2.0 | b.ordered_pairs | LEGITIMATE_CREDIT |
| b.different | 2.0 | b.different_favorable | LEGITIMATE_CREDIT |
| b.same | 2.0 | b.same_compartment | LEGITIMATE_CREDIT |
| b.conclusion | 2.0 | b.second_white_probability | LEGITIMATE_CREDIT |

Fechamento registrado: soma das parcelas = **8**, score final = **8**. Demais parcelas: zero. Nenhuma pontuação foi alterada pela auditoria.

**Julgamento pela fonte:** as quatro parcelas de contagem foram escritas: pares ordenados 6*6; favoráveis distintos 2*5; repetição exclusivamente do sexto; reunião (10+1)/36=11/36. Logo b.space+b.different+b.same+b.conclusion = 2+2+2+2. Não há necessidade de inventar um argumento a partir de 36, 10 ou 11/36 isolados: os produtos e a partição estão literalmente na fonte, associados aos objetos corretos.

O certificado finito nos subchecks enumera 36 eventos com peso 1/36; diferentes favoráveis são 10, repetidos favoráveis somente (6,6), total 11. A relação 2×5 é verificada como dois segundos compartimentos brancos, com cinco primeiras escolhas diferentes para cada um. `argument_satisfied=true` nas três parcelas compostas; `result_credit_only=false`. O total tem FORMAL_VERIFIED na aritmética e relação determinística verificada. Não se declarou prova Lean da máquina inteira. Os 8 pontos são LEGITIMATE_CREDIT, sem árvore alternativa adicional.

**Current:** extraiu 6*6=36, 2*5=10 e (10+1)/36=11/36 como expressões genéricas, mas não ligou nenhuma aos subjects; também não produziu o conjunto da repetição verbal. STRUCTURE_MISS e EXTRACTION_MISS → BASELINE_UNDER_CREDIT, 4 parcelas/8 pontos perdidos.

Registros Current preservados (para localizar a perda antes da pontuação):

| Texto capturado | Subject | Role | Atribuível |
| --- | --- | --- | --- |
| 6*6=36 | expression | intermediate | True |
| 2*5=10 | expression | intermediate | True |
| (10+1)/36=11/36 | expression | intermediate | True |

Fatos Current: nenhum.

### 4.5. p3_dev_complete_strategy

Current **0**; Semantic solicitado **8**; fallback **false**; modo efetivo **TME_SEMANTIC_FORMAL**.

Fonte original completa:

```text
c) O jogo continua somente nos compartimentos 1 e 2.
Após sair branca do compartimento 1, escolho preta, que aparece três vezes.
No caso 1, a probabilidade condicional de sucesso é 3/6=1/2.
Após sair branca do compartimento 2, escolho cinza, que aparece três vezes.
No caso 2, a probabilidade condicional de sucesso é 3/6=1/2.
A probabilidade total de vitória é (1/6)*(1/2)+(1/6)*(1/2)=1/6.
```

Artefatos: [Current](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_current/p3_dev_complete_strategy.json) · [Semantic](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_semantic_formal/p3_dev_complete_strategy.json).

| Span | Offsets | Texto literal |
| --- | --- | --- |
| S1 | [3,52) | O jogo continua somente nos compartimentos 1 e 2. |
| S2 | [53,128) | Após sair branca do compartimento 1, escolho preta, que aparece três vezes. |
| S3 | [129,189) | No caso 1, a probabilidade condicional de sucesso é 3/6=1/2. |
| S4 | [190,265) | Após sair branca do compartimento 2, escolho cinza, que aparece três vezes. |
| S5 | [266,326) | No caso 2, a probabilidade condicional de sucesso é 3/6=1/2. |
| S6 | [327,390) | A probabilidade total de vitória é (1/6)*(1/2)+(1/6)*(1/2)=1/6. |

| EvidenceUnit | Fonte | Subject / tipo | Claim normalizado | Contexto | Rota sugerida |
| --- | --- | --- | --- | --- | --- |
| E002:p3:7dae7c931e16f8ce02a3 | S1 | continuar / integer_set | {1, 2} | asserted; positive; main_argument; H=False; A=False; aluno=True | DETERMINISTIC |
| E003:p3:13180e76b79b6f023a2e | S2 | estrategia_1 / enum | black | asserted; positive; main_argument; H=False; A=False; aluno=True | COMPOSITE |
| E003:p3:0c12ea20cfef9b5caaa5 | S2 | contagem_1 / math | 3 | asserted; positive; main_argument; H=False; A=False; aluno=True | COMPOSITE |
| E004:p3:6f7eb28996a160803f02 | S3 | condicional_1 / math | 3/6=1/2 | asserted; positive; main_argument; H=False; A=False; aluno=True | COMPOSITE |
| E005:p3:c90b925b67c8ee650975 | S4 | estrategia_2 / enum | gray | asserted; positive; main_argument; H=False; A=False; aluno=True | COMPOSITE |
| E005:p3:a64c5deba10197059d3c | S4 | contagem_2 / math | 3 | asserted; positive; main_argument; H=False; A=False; aluno=True | COMPOSITE |
| E006:p3:602d2f10c87780eabd1c | S5 | condicional_2 / math | 3/6=1/2 | asserted; positive; main_argument; H=False; A=False; aluno=True | COMPOSITE |
| E007:p3:befa1949babc0f52203b | S6 | total / math | (1/6)*(1/2)+(1/6)*(1/2)=1/6 | asserted; positive; final_conclusion; H=False; A=False; aluno=True | COMPOSITE |

| EvidenceUnit | Obrigação | Rota efetiva | Mapeamento |
| --- | --- | --- | --- |
| E002:p3:7dae7c931e16f8ce02a3 | c.continue_compartments | DETERMINISTIC | aceito: compatible_pending_checker |
| E003:p3:13180e76b79b6f023a2e | c.strategy_case_1 | COMPOSITE | aceito: compatible_pending_checker |
| E003:p3:0c12ea20cfef9b5caaa5 | c.strategy_case_1 | COMPOSITE | aceito: compatible_pending_checker |
| E004:p3:6f7eb28996a160803f02 | c.conditional_success_1 | COMPOSITE | aceito: compatible_pending_checker |
| E005:p3:c90b925b67c8ee650975 | c.strategy_case_2 | COMPOSITE | aceito: compatible_pending_checker |
| E005:p3:a64c5deba10197059d3c | c.strategy_case_2 | COMPOSITE | aceito: compatible_pending_checker |
| E006:p3:602d2f10c87780eabd1c | c.conditional_success_2 | COMPOSITE | aceito: compatible_pending_checker |
| E007:p3:befa1949babc0f52203b | c.total_win_probability | COMPOSITE | aceito: compatible_pending_checker |

| Resultado / obrigação | EvidenceUnits → claim | Rota | Checker | Estado epistêmico | Sufficiency registrada | Usado no award | Motivo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1: c.continue_compartments | E002:p3:7dae7c931e16f8ce02a3 | DETERMINISTIC | P3Checks/_c + conjunto de continuação | DETERMINISTIC_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V2: c.strategy_case_1 | E003:p3:13180e76b79b6f023a2e, E003:p3:0c12ea20cfef9b5caaa5 | COMPOSITE | P3Checks/_c + after_first/counts/best_choices(1) | COMPOSITE_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V3: c.conditional_success_1 | E004:p3:6f7eb28996a160803f02, E003:p3:13180e76b79b6f023a2e, E003:p3:0c12ea20cfef9b5caaa5 | COMPOSITE | P3Checks/_c + estratégia 1 + numerical | COMPOSITE_VERIFIED; FORMAL_VERIFIED | True | sim | EXISTING_VERIFICATION_RESULT |
| V4: c.strategy_case_2 | E005:p3:c90b925b67c8ee650975, E005:p3:a64c5deba10197059d3c | COMPOSITE | P3Checks/_c + after_first/counts/best_choices(2) | COMPOSITE_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V5: c.conditional_success_2 | E006:p3:602d2f10c87780eabd1c, E005:p3:c90b925b67c8ee650975, E005:p3:a64c5deba10197059d3c | COMPOSITE | P3Checks/_c + estratégia 2 + numerical | COMPOSITE_VERIFIED; FORMAL_VERIFIED | True | sim | EXISTING_VERIFICATION_RESULT |
| V6: c.total_win_probability | E007:p3:befa1949babc0f52203b, E002:p3:7dae7c931e16f8ce02a3, E003:p3:13180e76b79b6f023a2e, E003:p3:0c12ea20cfef9b5caaa5, E004:p3:6f7eb28996a160803f02, E005:p3:c90b925b67c8ee650975, E005:p3:a64c5deba10197059d3c, E006:p3:602d2f10c87780eabd1c | COMPOSITE | P3Checks/_c + contexto + weighted_sum + numerical | COMPOSITE_VERIFIED; FORMAL_VERIFIED | True | sim | EXISTING_VERIFICATION_RESULT |

Componentes lógicos/metadados de V1 (subchecks=[] no recibo): engine_derived={"continue_compartments": [1, 2]}.

Componentes lógicos/metadados de V2 (subchecks=[] no recibo): engine_derived={"bottom_colors_after_first": ["black", "white", "gray", "black", "gray", "black"], "counts": {"black": 3, "white": 1, "gray": 2}, "optimal_colors": ["black"]}; student_color="black".

Componentes lógicos/metadados de V3 (subchecks=[] no recibo): context_gate="deterministically verified strategy; arithmetic certificate has numeric scope".

Recibo Lean de V3: `compiled=True`, stdout='', stderr=''; proposição `((3 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (2 : ℚ))`; [arquivo executado](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/student_claim_checks/p3-semantic-formal-6c0742e72bf74d95bea659a1077541d5/rational_check_0.lean).

Componentes lógicos/metadados de V4 (subchecks=[] no recibo): engine_derived={"bottom_colors_after_first": ["white", "gray", "gray", "black", "gray", "black"], "counts": {"white": 1, "gray": 3, "black": 2}, "optimal_colors": ["gray"]}; student_color="gray".

Componentes lógicos/metadados de V5 (subchecks=[] no recibo): context_gate="deterministically verified strategy; arithmetic certificate has numeric scope".

Recibo Lean de V5: `compiled=True`, stdout='', stderr=''; proposição `((3 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (2 : ℚ))`; [arquivo executado](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/student_claim_checks/p3-semantic-formal-6c0742e72bf74d95bea659a1077541d5/rational_check_1.lean).

Componentes lógicos/metadados de V6 (subchecks=[] no recibo): engine_derived={"uniform_first_draw_weights": ["1/6", "1/6"]}; context_gate="verified continuation, strategies and conditional probabilities"; written_development="two_branch_sum".

Recibo Lean de V6: `compiled=True`, stdout='', stderr=''; proposição `((((1 : ℚ) / (6 : ℚ)) * ((1 : ℚ) / (2 : ℚ))) + (((1 : ℚ) / (6 : ℚ)) * ((1 : ℚ) / (2 : ℚ)))) = ((1 : ℚ) / (6 : ℚ))`; [arquivo executado](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/student_claim_checks/p3-semantic-formal-6c0742e72bf74d95bea659a1077541d5/rational_check_2.lean).

Conflitos/reconciliação registrados: nenhum.

| Parcela concedida | Pontos | Obrigações na regra | Classificação forense |
| --- | --- | --- | --- |
| c.continue | 1.0 | c.continue_compartments | LEGITIMATE_CREDIT |
| c.first_strategy | 2.0 | c.strategy_case_1 | LEGITIMATE_CREDIT |
| c.second_strategy | 2.0 | c.strategy_case_2 | LEGITIMATE_CREDIT |
| c.conditionals | 1.0 | c.conditional_success_1, c.conditional_success_2, c.strategy_case_1, c.strategy_case_2 | LEGITIMATE_CREDIT |
| c.total | 2.0 | c.total_win_probability, c.continue_compartments, c.strategy_case_1, c.strategy_case_2, c.conditional_success_1, c.conditional_success_2 | LEGITIMATE_CREDIT |

Fechamento registrado: soma das parcelas = **8**, score final = **8**. Demais parcelas: zero. Nenhuma pontuação foi alterada pela auditoria.

**Julgamento pela fonte:** há continuação nos compartimentos 1 e 2, escolha de preta com três ocorrências após o caso 1, escolha de cinza com três após o caso 2, ambas as condicionais 3/6=1/2 e a soma global desde a primeira escolha. As parcelas são 1+2+2+1+2=8. A identificação de cor e contagem está escrita; não foi completada pelo modelo.

Recibos `engine_derived` confirmam:

| Caso | Cores inferiores após primeira retirada | Contagens | Máximo / escolha escrita |
| --- | --- | --- | --- |
| 1 | preta, branca, cinza, preta, cinza, preta | preta=3, branca=1, cinza=2 | máximo=3; preta é única ótima |
| 2 | branca, cinza, cinza, preta, cinza, preta | branca=1, cinza=3, preta=2 | máximo=3; cinza é única ótima |

`P3Machine.best_choices` calcula max(counts) e os argmax das cores, não consulta a resposta do LLM. As duas condicionais possuem contexto de estratégia validado e provas Lean de 3/6=1/2. O total tem `written_development=two_branch_sum`, pesos 1/6 e contexto com continuação, duas estratégias e duas condicionais. O recibo Lean comprova a igualdade global escrita. Esses checkers antigos de c não emitem uma lista de subchecks separada: seus componentes estão nos metadados/context_claim_ids e no código congelado; não se inventou um recibo de componente ausente.

**Current:** guardou as três igualdades genéricas, sem vínculos condicional_1, condicional_2 ou total; não normalizou continuação e cores/contagens como quantidades tipadas. As igualdades estão em linhas com prosa, não são standalone. STRUCTURE_MISS + EXTRACTION_MISS, com perda de normalização de conjunto/enum por extenso, resultam em BASELINE_UNDER_CREDIT: 5 parcelas/8 pontos. Todos os 8 concedidos pelo Semantic são legítimos.

Registros Current preservados (para localizar a perda antes da pontuação):

| Texto capturado | Subject | Role | Atribuível |
| --- | --- | --- | --- |
| 3/6=1/2 | expression | intermediate | True |
| 3/6=1/2 | expression | intermediate | True |
| (1/6)*(1/2)+(1/6)*(1/2)=1/6 | expression | intermediate | True |

Fatos Current: nenhum.

### 4.6. p3_dev_probability_error

Current **0**; Semantic solicitado **2**; fallback **false**; modo efetivo **TME_SEMANTIC_FORMAL**.

Fonte original completa:

```text
b) Os casos favoráveis com compartimentos diferentes são 2*6=12.
Ao repetir o mesmo compartimento, somente o sexto libera branca.
A probabilidade da segunda branca é (12+1)/36=13/36.
```

Artefatos: [Current](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_current/p3_dev_probability_error.json) · [Semantic](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_semantic_formal/p3_dev_probability_error.json).

| Span | Offsets | Texto literal |
| --- | --- | --- |
| S1 | [3,64) | Os casos favoráveis com compartimentos diferentes são 2*6=12. |
| S2 | [65,129) | Ao repetir o mesmo compartimento, somente o sexto libera branca. |
| S3 | [130,182) | A probabilidade da segunda branca é (12+1)/36=13/36. |

| EvidenceUnit | Fonte | Subject / tipo | Claim normalizado | Contexto | Rota sugerida |
| --- | --- | --- | --- | --- | --- |
| E002:p3:2b335106a1fd90fb45d1 | S1 | favoraveis_distintos / math | 2*6=12 | asserted; positive; main_argument; H=False; A=False; aluno=True | COMPOSITE |
| E003:p3:4344f3047ac5396c33ac | S2 | repeticao_branca / integer_set | {6} | asserted; positive; main_argument; H=False; A=False; aluno=True | DETERMINISTIC |
| E004:p3:59251faf1db588a85df9 | S3 | segunda_branca / math | (12+1)/36=13/36 | asserted; positive; final_conclusion; H=False; A=False; aluno=True | COMPOSITE |

| EvidenceUnit | Obrigação | Rota efetiva | Mapeamento |
| --- | --- | --- | --- |
| E002:p3:2b335106a1fd90fb45d1 | b.different_favorable | COMPOSITE | aceito: compatible_pending_checker |
| E003:p3:4344f3047ac5396c33ac | b.same_compartment | DETERMINISTIC | aceito: compatible_pending_checker |
| E004:p3:59251faf1db588a85df9 | b.second_white_probability | COMPOSITE | aceito: compatible_pending_checker |

| Resultado / obrigação | EvidenceUnits → claim | Rota | Checker | Estado epistêmico | Sufficiency registrada | Usado no award | Motivo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1: b.different_favorable | E002:p3:2b335106a1fd90fb45d1 | COMPOSITE | StrongP3Checks.observe + finite_certificate + count_relation(different) | COMPOSITE_FAILED; FORMAL_NOT_ATTEMPTED | False | não | EXISTING_VERIFICATION_RESULT |
| V2: b.same_compartment | E003:p3:4344f3047ac5396c33ac | DETERMINISTIC | P3Checks/_b + igualdade do conjunto com diagonal branca | DETERMINISTIC_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V3: b.second_white_probability | E004:p3:59251faf1db588a85df9, E002:p3:2b335106a1fd90fb45d1 | COMPOSITE | StrongP3Checks.numerical + certificado + relação/contrato de valor | COMPOSITE_FAILED; FORMAL_NOT_ATTEMPTED | False | não | EXISTING_VERIFICATION_RESULT |

Componentes de V1 (b.different_favorable):

| Componente | Status | Razão |
| --- | --- | --- |
| arithmetic | DETERMINISTIC_FAILED | existing_exact_arithmetic |
| finite_machine | DETERMINISTIC_VERIFIED | two_actual_withdrawals_and_uniform_measure |
| written_relation | DETERMINISTIC_INCOMPLETE | counting_relation_not_established |

Componentes lógicos/metadados de V2 (subchecks=[] no recibo): engine_derived={"same_compartment_favorable": [6]}.

Componentes de V3 (b.second_white_probability):

| Componente | Status | Razão |
| --- | --- | --- |
| arithmetic | DETERMINISTIC_FAILED | existing_exact_arithmetic |
| finite_machine | DETERMINISTIC_VERIFIED | two_actual_withdrawals_and_uniform_measure |
| source_consistency | CONFLICTING_EVIDENCE | explicit_counting_context_conflict |
| written_relation | DETERMINISTIC_FAILED | false_written_partition |

Conflitos/reconciliação registrados: nenhum.

| Parcela concedida | Pontos | Obrigações na regra | Classificação forense |
| --- | --- | --- | --- |
| b.same | 2.0 | b.same_compartment | LEGITIMATE_CREDIT |

Fechamento registrado: soma das parcelas = **2**, score final = **2**. Demais parcelas: zero. Nenhuma pontuação foi alterada pela auditoria.

**Por que 2 pontos:** a única parcela concedida foi **b.same**, apoiada no span “somente o sexto libera branca”, `{6}` → DETERMINISTIC_VERIFIED → sufficiency=true → award=true → 2. Essa parcela é independente de b.different e b.conclusion na pauta. A enumeração da diagonal confirma (6,6), mesmo que o estudante tenha errado o outro subconjunto.

`2*6=12` é uma igualdade aritmética verdadeira, mas uma contagem falsa do evento com compartimentos diferentes: o esperado derivado da máquina é 10. O componente chamado arithmetic compara todos os valores ao valor-alvo; DETERMINISTIC_FAILED aqui não significa que a identidade 2×6=12 é falsa. O composto de b.different é FAILED, sem suficiência/award.

`(12+1)/36=13/36` também é uma igualdade aritmética verdadeira, mas não é a probabilidade correta da segunda branca; o evento tem 11 favoráveis. b.second_white_probability tem falha de valor, partição falsa e source_consistency=CONFLICTING_EVIDENCE. O agregador prioriza a refutação e registra COMPOSITE_FAILED, não conflito separado no array global. A conclusão não recebe crédito. Não houve Lean/refutação formal nessa fonte: FORMAL_NOT_ATTEMPTED.

Os dois COMPOSITE_FAILED ficam em verification_results/rejected_evidence e seus awards são inelegíveis. Nenhum claim falso foi premiado. **LEGITIMATE_CREDIT: b.same=2.**

**Current:** retém somente as duas contas genéricas, sem fatos; não extrai a exclusividade verbal da repetição. EXTRACTION_MISS → BASELINE_UNDER_CREDIT de 1 parcela/2 pontos. Não se contabilizam as afirmações falsas como evidência legítima perdida.

Registros Current preservados (para localizar a perda antes da pontuação):

| Texto capturado | Subject | Role | Atribuível |
| --- | --- | --- | --- |
| 2*6=12 | expression | intermediate | True |
| (12+1)/36=13/36 | expression | intermediate | True |

Fatos Current: nenhum.

### 4.7. p3_dev_hypothesis_context

Current **0**; Semantic solicitado **2**; fallback **false**; modo efetivo **TME_SEMANTIC_FORMAL**.

Fonte original completa:

```text
a) Hipótese não adotada: a probabilidade da primeira branca seria 1/2.

Minha resposta: a probabilidade da primeira branca é 1/3.
```

Artefatos: [Current](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_current/p3_dev_hypothesis_context.json) · [Semantic](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_semantic_formal/p3_dev_hypothesis_context.json).

| Span | Offsets | Texto literal |
| --- | --- | --- |
| S1 | [3,70) | Hipótese não adotada: a probabilidade da primeira branca seria 1/2. |
| S2 | [72,129) | Minha resposta: a probabilidade da primeira branca é 1/3. |

| EvidenceUnit | Fonte | Subject / tipo | Claim normalizado | Contexto | Rota sugerida |
| --- | --- | --- | --- | --- | --- |
| E002:p3:4e4e97c3e33577363f1c | S1 | primeira_branca / math | 1/2 | abandoned; positive; exploration; H=True; A=True; aluno=True | DETERMINISTIC |
| E003:p3:917c76fe263d7410c759 | S2 | primeira_branca / math | 1/3 | asserted; positive; final_conclusion; H=False; A=False; aluno=True | DETERMINISTIC |

| EvidenceUnit | Obrigação | Rota efetiva | Mapeamento |
| --- | --- | --- | --- |
| E002:p3:4e4e97c3e33577363f1c | a.first_white_probability | DETERMINISTIC | rejeitado: nonasserted_or_unattributed_context |
| E003:p3:917c76fe263d7410c759 | a.first_white_probability | DETERMINISTIC | aceito: compatible_pending_checker |

| Resultado / obrigação | EvidenceUnits → claim | Rota | Checker | Estado epistêmico | Sufficiency registrada | Usado no award | Motivo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1: a.first_white_probability | E003:p3:917c76fe263d7410c759 | DETERMINISTIC | P3Checks.numerical/_a + racional exato/Lean quando executado | DETERMINISTIC_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V2: a.first_white_probability | E002:p3:4e4e97c3e33577363f1c | DETERMINISTIC | não executado para este claim | CONTEXT_REJECTED; FORMAL_NOT_ATTEMPTED | False | não | nonasserted_or_unattributed_context |

Conflitos/reconciliação registrados: nenhum.

| Parcela concedida | Pontos | Obrigações na regra | Classificação forense |
| --- | --- | --- | --- |
| a.probability | 2.0 | a.first_white_probability | LEGITIMATE_CREDIT |

Fechamento registrado: soma das parcelas = **2**, score final = **2**. Demais parcelas: zero. Nenhuma pontuação foi alterada pela auditoria.

**Julgamento pela fonte:** a primeira frase declara hipótese não adotada e usa “seria 1/2”. Não vale como resposta nem como refutação da resposta final. A segunda frase, em outro parágrafo, declara “Minha resposta” e atribui 1/3 à primeira branca: a.probability=2, sem contagem adicional.

Somente E002 ficou CONTEXT_REJECTED por `nonasserted_or_unattributed_context`: assertion_status=abandoned, hypothetical=true, abandoned=true, scope=exploration. E003 é asserted/positive/final_conclusion, sem esses vetos; passou pelo checker determinístico exato e produziu os 2 pontos. Não houve conflito matemático, prova Lean ou contaminação do segundo span pelo veto do primeiro. Os outros dois CONTEXT_REJECTED do resumo ALL8 pertencem a outros casos e não a esta hipótese.

**Current:** já marcou 1/2 como assumption, attributable=false; preservou 1/3 como conclusion, attributable=true. Também criou o registro genérico “resposta: a”, sem valor probabilístico útil. O 1/3 final continuou sem quantity=primeira_branca e sem forma standalone. Portanto a perda foi STRUCTURE_MISS, com efeito BASELINE_UNDER_CREDIT de 1 parcela/2 pontos, **não CONTEXT_MISS**. O contexto válido não foi apagado no baseline; faltou vincular a probabilidade à obrigação.

Registros Current preservados (para localizar a perda antes da pontuação):

| Texto capturado | Subject | Role | Atribuível |
| --- | --- | --- | --- |
| 1/2 | expression | assumption | False |
| resposta: a | answer: | conclusion | True |
| 1/3 | expression | conclusion | True |

Fatos Current: nenhum.

### 4.8. p3_dev_partial_conflict

Current **0**; Semantic solicitado **4**; fallback **false**; modo efetivo **TME_SEMANTIC_FORMAL**.

Fonte original completa:

```text
a) Há duas bolas brancas embaixo.
b) Ao repetir o mesmo compartimento, somente o sexto libera branca.
Ao repetir o mesmo compartimento, o quinto também libera branca.
A probabilidade da segunda branca é 11/36.
A probabilidade da segunda branca é 12/36.
```

Artefatos: [Current](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_current/p3_dev_partial_conflict.json) · [Semantic](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_semantic_formal/p3_dev_partial_conflict.json).

| Span | Offsets | Texto literal |
| --- | --- | --- |
| S1 | [3,33) | Há duas bolas brancas embaixo. |
| S2 | [37,101) | Ao repetir o mesmo compartimento, somente o sexto libera branca. |
| S3 | [102,166) | Ao repetir o mesmo compartimento, o quinto também libera branca. |
| S4 | [167,209) | A probabilidade da segunda branca é 11/36. |
| S5 | [210,252) | A probabilidade da segunda branca é 12/36. |

| EvidenceUnit | Fonte | Subject / tipo | Claim normalizado | Contexto | Rota sugerida |
| --- | --- | --- | --- | --- | --- |
| E002:p3:7680cddee0359e14aa0f | S1 | inferiores_brancas / math | 2 | asserted; positive; main_argument; H=False; A=False; aluno=True | DETERMINISTIC |
| E004:p3:dc62180683f1cbf26a3a | S2 | repeticao_branca / integer_set | {6} | asserted; positive; main_argument; H=False; A=False; aluno=True | DETERMINISTIC |
| E005:p3:7a9383b541b4e859a01f | S3 | repeticao_branca / integer_set | O compartimento 5 também libera branca ao repetir o mesmo compartimento. | asserted; positive; main_argument; H=False; A=False; aluno=True | DETERMINISTIC |
| E006:p3:046c024353a8120290fd | S4 | segunda_branca / math | 11/36 | asserted; positive; final_conclusion; H=False; A=False; aluno=True | COMPOSITE |
| E007:p3:eaf57ea943afa39f385b | S5 | segunda_branca / math | 12/36 | asserted; positive; final_conclusion; H=False; A=False; aluno=True | COMPOSITE |

| EvidenceUnit | Obrigação | Rota efetiva | Mapeamento |
| --- | --- | --- | --- |
| E002:p3:7680cddee0359e14aa0f | a.bottom_white_count | DETERMINISTIC | aceito: compatible_pending_checker |
| E004:p3:dc62180683f1cbf26a3a | b.same_compartment | DETERMINISTIC | aceito: compatible_pending_checker |
| E005:p3:7a9383b541b4e859a01f | b.same_compartment | DETERMINISTIC | rejeitado: unsupported_checker_payload |
| E006:p3:046c024353a8120290fd | b.second_white_probability | COMPOSITE | aceito: compatible_pending_checker |
| E007:p3:eaf57ea943afa39f385b | b.second_white_probability | COMPOSITE | aceito: compatible_pending_checker |

| Resultado / obrigação | EvidenceUnits → claim | Rota | Checker | Estado epistêmico | Sufficiency registrada | Usado no award | Motivo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1: a.bottom_white_count | E002:p3:7680cddee0359e14aa0f | DETERMINISTIC | P3Checks/_a + contagem nas pilhas | DETERMINISTIC_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V2: b.same_compartment | E004:p3:dc62180683f1cbf26a3a | DETERMINISTIC | P3Checks/_b + igualdade do conjunto com diagonal branca | DETERMINISTIC_VERIFIED; FORMAL_NOT_ATTEMPTED | True | sim | EXISTING_VERIFICATION_RESULT |
| V3: b.second_white_probability | E006:p3:046c024353a8120290fd | COMPOSITE | StrongP3Checks.numerical + certificado + relação/contrato de valor | COMPOSITE_VERIFIED; FORMAL_NOT_ATTEMPTED | True | não | EXISTING_VERIFICATION_RESULT |
| V4: b.second_white_probability | E007:p3:eaf57ea943afa39f385b | COMPOSITE | StrongP3Checks.numerical + certificado + relação/contrato de valor | COMPOSITE_FAILED; FORMAL_NOT_ATTEMPTED | False | não | EXISTING_VERIFICATION_RESULT |
| V5: b.same_compartment | E005:p3:7a9383b541b4e859a01f | DETERMINISTIC | não executado para este claim | CONTEXT_REJECTED; FORMAL_NOT_ATTEMPTED | False | não | unsupported_checker_payload |

Componentes lógicos/metadados de V1 (subchecks=[] no recibo): engine_derived={"initial_bottom_colors": ["white", "white", "gray", "black", "gray", "black"], "white_count": 2}.

Componentes lógicos/metadados de V2 (subchecks=[] no recibo): engine_derived={"same_compartment_favorable": [6]}.

Componentes de V3 (b.second_white_probability):

| Componente | Status | Razão |
| --- | --- | --- |
| arithmetic | DETERMINISTIC_VERIFIED | existing_exact_arithmetic |
| finite_machine | DETERMINISTIC_VERIFIED | two_actual_withdrawals_and_uniform_measure |
| source_consistency | DETERMINISTIC_VERIFIED | no_negative_context |
| result_credit_contract | DETERMINISTIC_VERIFIED | b_conclusion_explicit_result_route_no_method_credit |

Componentes de V4 (b.second_white_probability):

| Componente | Status | Razão |
| --- | --- | --- |
| arithmetic | DETERMINISTIC_FAILED | existing_exact_arithmetic |
| finite_machine | DETERMINISTIC_VERIFIED | two_actual_withdrawals_and_uniform_measure |
| source_consistency | DETERMINISTIC_VERIFIED | no_negative_context |
| result_credit_contract | DETERMINISTIC_VERIFIED | b_conclusion_explicit_result_route_no_method_credit |

Conflitos/reconciliação registrados: b.second_white_probability → conflicting_source_or_checker_evidence; resolved=False.

| Parcela concedida | Pontos | Obrigações na regra | Classificação forense |
| --- | --- | --- | --- |
| a.count | 2.0 | a.bottom_white_count | LEGITIMATE_CREDIT |
| b.same | 2.0 | b.same_compartment | FALSE_CREDIT |

Fechamento registrado: soma das parcelas = **4**, score final = **4**. Demais parcelas: zero. Nenhuma pontuação foi alterada pela auditoria.

**Julgamento independente pela fonte:** a.count é claramente satisfeita pela contagem das duas brancas e vale 2. Em b há duas contradições materiais: exclusividade do sexto versus inclusão do quinto; 11/36 versus 12/36. Não há abandono, correção explícita ou regra de precedência que resolva qualquer delas. Pelo contrato de conflito congelado, b.same e b.conclusion devem ficar sem award automático. Os 4 pontos retornados não são integralmente legítimos.

**Conflito detectado:** E006 e E007 viraram claims matemáticos verificáveis da mesma obrigação b.second_white_probability. O primeiro recebeu COMPOSITE_VERIFIED/sufficiency=true; o segundo COMPOSITE_FAILED/sufficiency=false. O reconciliador registra `conflicting_source_or_checker_evidence`, sem resolução, e o award de b.conclusion é `blocked_conflict`. O positivo não foi escolhido silenciosamente nessa obrigação.

**Conflito perdido:** E004 “somente o sexto” virou `{6}`, passou no checker de conjunto e recebeu b.same=2. E005 “o quinto também” foi extraído — não omitido — com subject repeticao_branca, claim_type integer_set, mas normalized_claim em prosa: “O compartimento 5 também libera branca ao repetir o mesmo compartimento.” O schema aceitou a string; a representação exigida pelo checker não. O mapper devolveu `unsupported_checker_payload`, o verificador atribuiu CONTEXT_REJECTED e mathematical_refutation=false, e nenhum registro foi projetado ao checker para essa evidência.

Esse CONTEXT_REJECTED não descreve o contexto real da fonte: E005 está asserted, positive, attributed_to_student=true, hypothetical=false, abandoned=false, scope=main_argument. Sua confidence=0,98 não causa o bloqueio nem fornece precedência à confidence=1 da afirmação do sexto. O erro é de representação e conservação do conflito, não hipótese descartada. A máquina congelada contém no quinto uma pilha cinza, preta; na repetição sai preta, de modo que a afirmação sobre o quinto é falsa.

Como o reconciliador bloqueia negativos matemáticos, CONFLICTING_EVIDENCE e conflitos já detectados, mas não esse payload rejeitado, b.same permanece elegível. O guard determinístico também não extrai a relação verbal do quinto; não há veto alternativo. A anotação b.second/source_consistency “no_negative_context” decorre dessa ausência de fato negativo e não prova inexistência de contradição na fonte.

**Quatro pontos realmente concedidos:** a.count=2, LEGITIMATE_CREDIT; b.same=2, **FALSE_CREDIT por conflito material não reconciliado**. Só os dois de a são independentes. O claim falso do quinto não recebeu award diretamente; a falha é premiar a exclusividade incompatível enquanto a outra afirmação permanece na resposta. Não há justificativa para reclassificar os 2 indevidos como crédito parcial, nem ambiguidade de pauta que os autorize.

**Ordem textual:** o DEV gravado contém apenas esta ordem; não foi reexecutado nem invertido. Pelo código congelado, reconcile usa conjuntos/predicados any, não “última afirmação vence”. O par de probabilidades foi bloqueado apesar de a verdadeira vir antes. O par de compartimentos falhou porque só um lado chegou ao checker; não há evidência de uma regra temporal que tenha resolvido o conflito. Não se afirma validação experimental de todas as permutações pelo DEV01.

**Current:** só extraiu 11/36 e 12/36 genéricos, nenhum fato; perdeu a contagem verbal de a e os claims de repetição. EXTRACTION_MISS/STRUCTURE_MISS → BASELINE_UNDER_CREDIT **apenas de a.count=2**. O zero em b não deve ser chamado de subcrédito: era a retenção automática adequada ao conflito, embora tenha ocorrido por ausência de extração, e não por reconciliação bem-sucedida.

Registros Current preservados (para localizar a perda antes da pontuação):

| Texto capturado | Subject | Role | Atribuível |
| --- | --- | --- | --- |
| 11/36 | expression | intermediate | True |
| 12/36 | expression | intermediate | True |

Fatos Current: nenhum.

## 5. Causa do falso crédito e fronteira de representação

A cadeia causal é verificável por leitura do código congelado:

1. [mapper.py, representação](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:69): a frase normalizada do quinto não forma o payload integer_set; gera `unsupported_checker_payload`.
2. [verification.py, projeção](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py:28): somente mapeamentos accepted entram em MathClaimRecord e nos checkers.
3. [verification.py, rejeições](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py:108): quase toda rejeição de mapper recebe CONTEXT_REJECTED, inclusive representação inválida de afirmação efetivamente adotada; mathematical_refutation=false.
4. [engine.py, reconcile](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:33): não há veto para essa rejeição de representação. O guard também não reconhece o claim verbal do quinto. Só b.second_white_probability aparece em conflicts.
5. [engine.py, award](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:54): o resultado positivo de b.same é selecionado porque não há negative matemático nem blocked para esse ID.

O conteúdo sobre o quinto permaneceu no JSON, mas foi removido do circuito de verificação/conflito antes do award. A falha não é “o LLM deu pontos” nem “o checker calculou errado”; é a aceitação automática de evidência positiva enquanto uma afirmação material incompatível foi tratada como se sua rejeição de formato eliminasse o conflito. Não é lícito converter automaticamente “o quinto também” em `{5}` nesta auditoria: isso trocaria uma afirmação de inclusão por uma de exclusividade. O que a fonte permite concluir sem nova extração é a incompatibilidade com “somente o sexto”.

Não foram implementadas correções nem rodados contrafactuais. O diagnóstico aponta a necessidade de preservar o efeito de conflitos materiais na fronteira de representação; a escolha de implementação fica para outra tarefa.

## 6. FALSE AUTOMATIC CREDIT AUDIT

| Pergunta | Resultado forense |
| --- | --- |
| Houve ponto concedido sem checker? | Não: todos os awards escolhidos têm fato/recibo de checker ou bridge baseline no fallback. |
| Houve ponto baseado apenas na interpretação do LLM? | Não diretamente. Houve falha de cobertura do conflito após uma normalização inadequada do LLM: o positivo foi checado, a afirmação conflitante não. |
| Claim falso recebeu award? | Nenhum resultado matemático refutado foi selecionado. A afirmação falsa do quinto não ganhou pontos. Porém b.same ganhou 2 sobre uma resposta contraditória: isso é FALSE_CREDIT material de reconciliação. |
| COMPOSITE_FAILED gerou indevidamente a mesma parcela? | Não. Os dois FAILED de probability_error não foram premiados; o FAILED da probabilidade em partial_conflict bloqueou inclusive o positivo da mesma obrigação. |
| CONTEXT_REJECTED recebeu crédito? | Nenhum desses registros foi usado no award. Mas a rejeição de E005 em partial_conflict deixou de vetar a parcela conflitante, causando o falso crédito indireto. |
| Refutação formal/determinística foi ignorada? | Nenhuma refutação efetivamente produzida foi sobrescrita. Não houve FORMAL_REFUTED no DEV. As três refutações determinísticas/compostas tiveram seus awards retidos. A falsidade do quinto não chegou a ser verificada, por rejeição de payload. |
| Contexto funcionou localmente? | Sim para hipótese não adotada versus resposta independente. Não integralmente para afirmação adotada mas mal representada, indevidamente enquadrada como CONTEXT_REJECTED sem veto de conflito. |
| Falso crédito material encontrado | Uma parcela, b.same, 2 pontos, em p3_dev_partial_conflict. |
| Parcela legítima perdida pelo Semantic concluído | Nenhuma claramente identificada nesta amostra. Isso não reabilita a parcela indevida. |

O resumo `CONTEXT_REJECTED=3` agrega coisas diferentes: (1) uniformidade qualitativa sem subject/tipo suportado; (2) hipótese abandonada; (3) afirmação adotada sobre o quinto com payload inválido. Somente (2) é rejeição contextual legítima no sentido estrito. O contador sozinho não prova proteção contextual.

O resumo `FORMAL_VERIFIED=1` conta somente o status externo dos resultados. Há **cinco igualdades Lean verificadas nos recibos**, incluindo aritmética dentro dos compostos: a inicial (1), total de b (1), duas condicionais e total de c (3). Todos esses recibos têm compiled=true e stdout/stderr vazios; zero FORMAL_REFUTED, FORMAL_UNPROVED e FORMAL_ERROR. Os outros 20 resultados registram FORMAL_NOT_ATTEMPTED. Nenhum desses números foi obtido por recompilação nesta auditoria.

## 7. Current: classificação das divergências

O parser Current é determinístico. `quantity(record)` aceita somente canonical_form.family=named_quantity, e standalone_math exige que o registro ocupe toda a linha. Por isso capturar uma igualdade dentro de prosa não equivale a extrair uma obrigação P3. Nos sete casos divergentes, `current_bridge.auditor.facts=[]`; a perda antecede a pontuação. Não se atribuiu automaticamente toda diferença positiva a mérito semântico.

| Caso | Causa principal | Efeito e MISSED_CREDIT legítimo do Current |
| --- | --- | --- |
| initial_count | EXTRACTION_MISS da contagem; STRUCTURE_MISS da probabilidade | BASELINE_UNDER_CREDIT: a.count+a.probability, 4 |
| isolated_answer | Sem divergência; expressão standalone reconhecida | Nenhum; Semantic é fallback, não resgate |
| sample_space | STRUCTURE_MISS: conta capturada sem subject de espaço amostral | BASELINE_UNDER_CREDIT: b.space, 2 |
| favorable_partition | STRUCTURE_MISS das contas e EXTRACTION_MISS da repetição verbal | BASELINE_UNDER_CREDIT: quatro parcelas de b.counting, 8 |
| complete_strategy | EXTRACTION_MISS das relações de estado/cor/contagem; STRUCTURE_MISS das três igualdades; representação natural não normalizada | BASELINE_UNDER_CREDIT: cinco parcelas de c, 8 |
| probability_error | EXTRACTION_MISS da repetição correta; demais contas são falsas para o problema | BASELINE_UNDER_CREDIT: somente b.same, 2 |
| hypothesis_context | STRUCTURE_MISS da probabilidade final; a hipótese foi marcada corretamente como não atribuível | BASELINE_UNDER_CREDIT: a.probability, 2; não CONTEXT_MISS |
| partial_conflict | EXTRACTION_MISS da contagem de a; STRUCTURE_MISS de b | BASELINE_UNDER_CREDIT: somente a.count, 2; zero de b não é subcrédito legítimo |

NORMALIZATION_MISS descreve a ausência de representação tipada de conjuntos/cores/números verbais em c, como parte da perda de extração, não uma equivalência matemática calculada incorretamente. Não se encontrou BASELINE_OVER_CREDIT nesses oito casos. As 15 parcelas legítimas perdidas pelo Current somam 28 pontos; o excedente restante da diferença de 30 pontos é o falso crédito de 2 no Semantic.

## 8. ALL8 versus SEMANTIC-SUCCESS7

SEMANTIC-SUCCESS7 significa apenas extração concluída (`status=completed`, sem fallback), **não sete decisões de nota integralmente corretas**. Exclui p3_dev_isolated_answer. A ordem das listas segue dev_ids.json, removendo apenas esse caso na segunda coluna.

| Medida observacional | ALL8 | SEMANTIC-SUCCESS7 |
| --- | --- | --- |
| Casos | 8 | 7 |
| Scores Current | [0,2,0,0,0,0,0,0] | [0,0,0,0,0,0,0] |
| Scores da execução solicitada Semantic | [4,2,2,8,8,2,2,4] | [4,2,8,8,2,2,4] |
| Soma observada Current / Semantic | 2 / 32 | 0 / 30 |
| Casos com diferença positiva | 7 | 7 |
| Fallbacks | 1 | 0 |
| Parcelas resgatadas julgadas LEGITIMATE_CREDIT | 15, somando 28 pontos | 15, somando 28 pontos |
| Total de parcelas concedidas legítimas, incluindo baseline de fallback | 16, somando 30 pontos | 15, somando 28 pontos |
| FALSE_CREDIT | 1 parcela, 2 pontos, 1 caso | 1 parcela, 2 pontos, 1 caso |
| QUESTIONABLE_CREDIT pendente | 0 | 0 |
| MISSED_CREDIT identificado no Current | 15 parcelas / 28 pontos | 15 parcelas / 28 pontos |
| MISSED_CREDIT identificado no Semantic concluído | 0; fallback não avalia o extractor | 0 |
| Technical uncertainty registrada | 0 | 0 |

Há 17 regras pontuadas em ALL8 e 18 obligation awards: as duas condicionais de c são dois awards que sustentam uma única regra de 1 ponto. As métricas acima contam **parcelas/regras por caso**, não confundem awards com pontos nem contam duas vezes c.conditionals.

ALL8: DETERMINISTIC_VERIFIED=8, FORMAL_VERIFIED=1, COMPOSITE_VERIFIED=10, COMPOSITE_FAILED=3, CONTEXT_REJECTED=3. SEMANTIC-SUCCESS7: DETERMINISTIC_VERIFIED=7; demais contadores iguais. A diferença é o verified determinístico do fallback.

Foram sete chamadas concluídas com evidências e uma tentativa de API sem saída útil. Não se calculou acurácia, taxa de acerto contra gold, ganho percentual de qualidade ou generalização. O conjunto é sintético DEV e não há gold independente. b.alternative_complete não foi exercitado positivamente por estes oito casos; o piloto não demonstra por si cobertura semântica de todas as 13 obrigações.

## 9. Veredito e estado final

**P3_DEV_REQUIRES_FIX.** As diferenças positivas de initial_count, sample_space, favorable_partition, complete_strategy, probability_error e hypothesis_context são sustentadas pela fonte/pauta/checkers. O caso partial_conflict recupera legitimamente a.count, mas concede indevidamente b.same após perder a contradição de representação. O fallback está separado e não conta como êxito do extractor.

Não se concede P3_DEV_SEMANTIC_BEHAVIOR_VALIDATED porque há falso crédito material e a reconciliação não preservou integralmente um conflito explícito. Também não é apenas inconclusivo: os artefatos mostram a fonte, a rejeição de payload, a ausência de conflito nesse ID e a parcela concedida. Não foi implementada correção.

Conferência de preservação: 836 caminhos preexistentes monitorados (arquivos rastreados fora de gold/holdout, JSON do DEV01 e cinco fontes Lean referenciadas) mantidos idênticos. SHA permaneceu `e4dc1e94b0e8e22a16489fcdcc3eb14e1abfd4ab`; sem stage/commit. Única mudança esperada no Git, conferida ao final:

```text
?? docs/audits/TME_P3_SEMANTIC_FORMAL_DEV01_FORENSIC.md
```

**P3_DEV_REQUIRES_FIX**

