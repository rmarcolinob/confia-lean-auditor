# P1-STUDENT-CLAIM-COVERAGE-01

## Estado recuperado após as interrupções

A inspeção por hashes, timestamps e conteúdo encontrou somente `before.json`, `baseline_sources.tar.gz`, `diagnosis_before.json` e `diagnosis_before.md`. Nenhum arquivo de código/testes havia sido alterado em relação ao snapshot; não havia camada genérica, replay, logs de testes ou diff. A classificação inicial foi recuperada, não refeita. `interruption_inspection.json` registra essa inspeção. O snapshot inclui as mudanças anteriores de fidelity, modelo comum, canonicalização, bridge e TME; elas não pertencem ao diff desta tarefa.

Nenhum arquivo foi revertido. Não houve reset/restore/clean, staging, commit ou push. A continuação implementou apenas extração genérica, projeção/integração, testes, replay offline e documentação.

## Diagnóstico antes de editar

Os **26 registros são obrigações de referência em 11 soluções**, não 26 soluções. A inspeção classificou **26 em A (conteúdo matemático relacionado explícito, antes sem representação student correspondente)** e **zero em B (conteúdo realmente ausente)**. A categoria A inclui afirmações incorretas, qualificadas, verbais e fora do domínio canônico. Ela não significa que o aluno tenha demonstrado o critério inteiro ou escrito a resposta esperada.

| Solução | Obrigação | Trecho literal relacionado | Resultado de representação |
|---|---|---|---|
| ITA2025Q1_S016_L01 | positive_root_selection | `a=15 ou a=-13` | created_parsed |
| ITA2025Q1_S016_L01 | final_answer | `Então o valor de a é quinze` | created_parsed |
| ITA2025Q1_S001_L04 | z_squared_coordinates | `z² = (a² - 4, 4a)` | created_ambiguous |
| ITA2025Q1_S001_L04 | area_formula | `S = (1/2)` | created_parsed |
| ITA2025Q1_S001_L04 | area_equation | `a² - 2a + 5 = 200` | created_parsed |
| ITA2025Q1_S001_L04 | positive_root_selection | `Então a = 15` | created_parsed |
| ITA2025Q1_S001_L04 | final_answer | `O valor pedido é 15` | created_parsed |
| ITA2025Q1_S014_L04 | z_squared_coordinates | `z² = (a² + 4, 4a)` | created_ambiguous |
| ITA2025Q3_S004_L01 | parity_obstruction | `F ímpar` | created_unsupported |
| ITA2025Q3_S002_L01 | first_factor_exponent_form | `C(6,i) x^(6-2i)` | created_ambiguous |
| ITA2025Q3_S002_L01 | second_factor_exponent_form | `C(5,j) (−2)^j x^(5-2j)` | created_ambiguous |
| ITA2025Q3_S002_L01 | parity_obstruction | `que é ímpar` | still_absent |
| ITA2025Q3_S001_L04 | first_factor_exponent_form | `C(6,i) x^{6-2i}` | created_unsupported |
| ITA2025Q3_S001_L04 | second_factor_exponent_form | `C(5,j)(-2)^j x^{5-2j}` | created_unsupported |
| ITA2025Q3_S001_L04 | parity_obstruction | `nao ha i+j que torne zero` | created_parsed |
| ITA2025Q4_S003_L04 | positive_witnesses | `x₁ = 1/4 + 1/8 = 3/8 e x₂ = 1/4 − 1/8 = 1/8` | created_parsed |
| ITA2025Q4_S003_L04 | same_f_argument | `h(3/8) = 2·(9/64)` | created_parsed |
| ITA2025Q4_S003_L04 | distinct_g_inputs | `valores distintos entre si` | still_absent |
| ITA2025Q4_S003_L04 | equal_g_values | `g(9/64) = f(h(3/8)) = f(29/32) = f(h(1/8)) = g(1/64)` | created_unsupported |
| ITA2025Q4_S003_L04 | not_injective_conclusion | `g não é injetora` | created_unsupported |
| ITA2025Q4_S002_L02 | same_f_argument | `2*(1/8)² -1/8 +1 = 2*(3/8)² -3/8 +1 = 29/32` | created_parsed |
| ITA2025Q4_S002_L02 | distinct_g_inputs | `1/64≠9/64` | created_unsupported |
| ITA2025Q4_S002_L02 | not_injective_conclusion | `g não injetora` | created_unsupported |
| ITA2025F2Q6_S006_L04 | final_answer | `máxima ocorre em n=6 e n=7` | created_parsed |
| ITA2025F2Q6_S001_L04 | probability_formula | `P(n) = C(n-1, 3) * (1/2)^n` | created_ambiguous |
| ITA2025F2Q6_S017_L04 | probability_formula | `P(n)=C(n,4)*(1/2)^n` | created_ambiguous |

Os JSONs de diagnóstico preservam offsets, classificação, estruturas e observações por registro. O diagnóstico anterior precedeu qualquer edição no motor.

## Arquitetura

`student_claims/generic_math.py` é a camada transversal. `candidate_spans` localiza spans originais; `math_runs` delimita sequências lexicais sem interpretar álgebra; `parse_math` continua sendo o único parser matemático. `extract_generic_math` cria StudentClaims com IDs estáveis derivados de posição/tipo, payload literal, hash da fonte, offsets e método `generic_math`. `source_is_valid` revalida o payload contra o span original. `contextual_role` combina os contextos e gates P0 com classificação conservadora de papel. `merge_candidates` deduplica ou preserva interpretações concorrentes.

```text
texto original
 → spans matemáticos limitados
 → parser existente / payload tipado
 → StudentClaim com vínculo literal
 → extractors específicos preservados
 → deduplicação conservadora
 → MathClaimRecord / catálogo / alignment existente
```

`extract_student_claims_for_audit` executa a camada genérica antes dos extractors específicos. O entrypoint legado `extract_student_claims` mantém seu contrato para consumidores existentes. O motor usa o entrypoint completo. Os adapters publicam os novos registros em `student_claims.json` e `math_claims.json`, inclusive status de canonicalização e semantic_role.

Tipos reutilizáveis: `math_relation`, `math_expression`, `math_interval`, `math_value`, `math_bindings` e `math_property`. Não foram criados tipos por questão. Detecção não recebe rubrica, resposta esperada ou assets e não utiliza problem_id para interpretar matemática; o ID apenas identifica a origem do registro.

## Domínio e sintaxe

- Igualdades, desigualdades simples, atribuições, potências inteiras e relações com funções reconhecidas usam o parser existente.
- Unicode/LaTeX são entregues ao parser existente; a detecção reutiliza sua whitelist de nomes e aliases.
- Pares de inteiros locais usam `local_integer_bindings`. Ordem dos símbolos não altera os valores; cláusulas separadas não são fundidas. Um pequeno vocabulário explícito de inteiros por extenso permite preservar “menos um” e “três”, sem buscar números no gabarito.
- Cadeias de igualdade produzem apenas as igualdades adjacentes literalmente presentes; não se inferem igualdades entre extremos.
- Conclusões de valor, resposta, resto e algarismo são tipadas. “Primeiro”, “último” e algarismo sem qualificador permanecem conceitos distintos. O valor não é fixado em 5.
- Propriedades limitadas de função, paridade e PG podem ser registradas sem formalização. Funções arbitrárias, binomiais, divisões simbólicas e logs fora da sintaxe atual ficam unsupported/ambiguous.
- Uma expressão incompleta não é truncada para produzir uma afirmação aparentemente válida.

O parser, suas regras de equivalência, limites, whitelist, semântica de logs e cálculo algébrico não foram modificados. Não há segundo parser, eval, execução de conteúdo, LLM ou Lean na detecção. Limites adicionais: fonte de 20.000 caracteres, fragmento de 2.048, até 256 candidatos e até 16 relações para decompor uma cadeia. Fontes acima do limite da camada genérica não são truncadas; os extractors legados mantêm seu comportamento.

Conclusões de valor usam a família `explicit_semantic_value`: conceito e sujeito explícito são mantidos junto ao valor parseado. Assim, primeiro algarismo 5, último algarismo 5 e resposta 5 não se tornam intercambiáveis apenas porque contêm o mesmo número. Essa tradução de novos payloads não muda as regras do parser ou do alignment.

Medição local (`performance.json`), cinco repetições por texto do replay: mediana entre casos 2.96 ms; maior amostra 62.32 ms. Entrada-limite de 20.000 caracteres: 2.72 s, com saída limitada a 256 candidatos. A medição ocorreu com regressões Lean concorrentes, portanto não é benchmark isolado de hardware.

A gramática limitada de números por extenso exige o término completo do literal: “vinte e um”, “dois mil”, “dois terços” e grafias híbridas como “dois,5” não são truncadas para 20 ou 2. Essas expressões ficam fora do domínio verbal inicial.

## Grounding, contexto e conflitos

Cada candidato preserva raw_text, source_text, source_start/source_end em caracteres Unicode, source_sha256 e payload_sha256. A projeção não confia em annotations serializadas: revalida a interpretação literal e reconstrói canonicalização e papel. Um span pode estar grounded como citação/hipótese e ainda não ser atribuível como afirmação utilizável para crédito.

Marcadores “logo”, “portanto”, “assim”, “daí”, “concluímos”, “obtemos”, “resulta” e “segue que” só classificam conclusion. Negação, pergunta retórica, citação, enunciado, irrelevância, hipótese e tentativa rejeitada não viram conclusão atribuível. Os filtros P0 permanecem ativos; “tentamos”, “isso daria”, “impossível” e incerteza explícita recebem tratamento adicional conservador. “A resposta não é 5” mantém negated=true, não recebe forma positiva canônica nem crédito. Propriedades negativas como não injetividade são preservadas como payload tipado, sem flexibilizar os gates para formalizá-las.

A deduplicação exige fonte sobreposta, atribuição válida e equivalência canônica, valores estruturados iguais ou o validador P0 de correspondência completa do payload. Preserva ID e dados do claim específico e registra `extraction_origins` e `generic_source_ids` no grounding. Representações sem comparação segura permanecem separadas. Bindings atribuíveis concorrentes recebem `interpretation_status=ambiguous`, permanecem visíveis e não são selecionados silenciosamente. Hipóteses/citações não contaminam bindings atribuíveis.

## Bridge, alignment, Lean e score

As regras de alignment não foram alteradas. A ponte existente recebe o catálogo ampliado e mantém seus contratos semânticos, microclaims e verificações. Os novos tipos genéricos não são renomeados com base na resposta esperada para fazê-los coincidir com tipos de rubrica. Não há caminho paralelo de crédito.

Claims específicos deduplicados continuam nos checkers existentes. Os seis tipos genéricos ainda não possuem contratos próprios de checker; o despacho do motor os exclui da chamada Lean. Isso evita gerar provas artificiais ou confundir “detectado” com “verified”. Nenhum módulo Lean, gate P0, adjuster, rubric asset, score policy, adjudicador ou UI foi alterado.

## Replay offline dos 26

Foram reprocessados apenas textos salvos das 11 soluções do diagnóstico e dos quatro casos prioritários. Não foi executado execute_audit no replay, pipeline externo, Lean, score policy ou adjudicador. Resultados e catálogos foram gravados em uma pasta nova; os artifacts históricos não foram sobrescritos.

| Resultado exclusivo por obrigação | Quantidade |
|---|---:|
| created_parsed | 11 |
| created_ambiguous | 6 |
| created_unsupported | 7 |
| still_absent | 2 |

**24 de 26** trechos relacionados passaram a ter representação student; **13** têm ao menos uma representação atribuível segundo os gates. `created_ambiguous` inclui ambiguidade do parse ou da interpretação; `created_unsupported` preserva o literal sem forma canônica. Os grupos são exclusivos e somam 26.

A métrica usa sobreposição com o trecho diagnosticado antes da mudança. Ela mede representação do conteúdo relacionado, não comprovação do critério completo. Permanecem ausentes a afirmação verbal de paridade de Q3_S002_L01 e a distinção verbal dos quadrados de Q4_S003_L04: têm sujeitos implícitos/referências discursivas fora do escopo. Não foram fabricadas relações a partir da pauta.

**Alignments das 26 obrigações: 26 unmatched → 26 unmatched (0 aligned → 0 aligned).** A representação genérica aumentou, mas a infraestrutura atual exige tipos semânticos correspondentes. O replay documenta esse limite em vez de afrouxar matching. Não se apresenta esse resultado como nova execução dos 37 alignments nem como ganho de score/cobertura primária.

## Casos prioritários

- **ITA2025F2Q5_S003_L04:** a conclusão literal do primeiro algarismo 5 agora gera `math_value`, concept=leading_digit, com grounding e canonicalização do valor. Não foi hardcodado problema, solution_id ou valor; testes variam os dígitos de 0 a 9. Não há nova verificação Lean ou crédito automático para esse tipo genérico.
- **ITA2025Q4_S002_L04:** “não sei fazer” continua com zero claims.
- **ITA2025F2Q1_S003_L02:** “a é menos um e b é três” passa a bindings a=-1,b=3. A incerteza “acho” mantém a atribuição conservadora; não se converte em conclusão comprovada.
- **ITA2025F2Q5_S024_L04:** o texto incorreto permanece incorreto: o algarismo afirmado é 1. A camada genérica registra expressões adicionais e deduplica o algarismo com o claim específico existente, preservando as duas origens. “Zero claims” neste conjunto se referia a ExtractedClaims, não necessariamente a zero StudentClaims.

## Validação e regressões

Os runners removem credenciais OpenAI/Mathpix, desabilitam extração LLM opcional e bloqueiam conexões IP. Logs completos ficam na pasta desta tarefa. Os 97 testes unitários novos e a integração de artifacts cobrem variantes de texto, Unicode/LaTeX, tipos, negativas, hipóteses, citações, perguntas, números irrelevantes, entrada incompleta, tampering, deduplicação, ambiguidades, limites, casos salvos e ausência de crédito/Lean artificial.

Durante a ampliação da deduplicação, dois testes novos precisaram corrigir expectativas: x^6=1 não tinha extractor legado (trocado por x^57=-1 para testar deduplicação real); o caso de algarismo 1 corretamente conserva o claim específico, e o teste agora exige valor, grounding e as duas origens em vez de exigir uma cópia genérica. Nenhum gate foi afrouxado. As versões finais passaram em `new_tests_complete.log` (98 testes) e `verbal_boundary_recheck.log` (97 unitários, após o último bloqueio de prefixos). Reruns focados validam os ajustes finais de fronteira e representação, sem somar novamente os mesmos casos à suíte.

As 88 comparações legadas são integralmente iguais ao snapshot. Outras 88 com a ponte ativa mantêm pontos, status e subtotais, sem mudanças silenciosas. A API de extração legada foi mantida e o teste de pipeline verifica que um novo claim grounded não ganha pontos apenas por ser detectado.

<!-- FINAL_VALIDATION_START -->
Resultado final: **1531 casos únicos — 1527 passed, 3 falhas preexistentes e 1 xfailed esperado**. Nenhuma regressão nova.

| Grupo | Passed | Failed | Xfailed |
|---|---:|---:|---:|
| broad | 1302 | 3 | 0 |
| proof_pipeline | 149 | 0 | 1 |
| reference_pipeline | 75 | 0 | 0 |
| immutability | 1 | 0 | 0 |

Falhas conhecidas: HMER (`test_projection_preserves_falsehoods_signs_and_general_fractions`), UI vocabulary (`test_central_product_vocabulary_is_preserved_without_contract_renames`) e tablet sticky (`test_parent_statement_is_compact_and_sticky_through_notebook_and_submission`). O xfail F2Q6 permanece esperado; não foi corrigido.

Os 98 testes novos passaram. Reruns focados não são contados duas vezes. O teste de imutabilidade rodou isolado, com stdout em /tmp e sem outros escritores de artifacts.

Preservação: 321 arquivos históricos Smoke V2 idênticos por SHA-256; 3078 arquivos preexistentes idênticos e somente os cinco arquivos previstos alterados. `git diff --check`: OK. HEAD e índice idênticos ao snapshot. Nenhum arquivo staged.

O estado completo do Git, incluindo alterações de tarefas anteriores, está em `git_status_short.txt`. Contagens: {' M': 55, '??': 40}.
<!-- FINAL_VALIDATION_END -->

## Limitações e próximo limite técnico

A detecção agora é transversal, mas não substitui a interpretação semântica da solução inteira. Regras para sujeitos implícitos, seleção de alternativas, referência anafórica, números por extenso gerais, propriedades funcionais formais e expressões fora do parser permanecem limitadas. Decimal com vírgula conserva o tratamento conservador do parser atual. Tipos genéricos não têm checker universal. Uma próxima tarefa pode adicionar traduções semânticas explícitas e verificáveis para contratos de critérios, sem inferir valores da pauta; essa expansão não foi feita aqui.

## Arquivos e entrega

Arquivos preexistentes alterados nesta tarefa:

- `app/confia_lean_auditor/student_claims/registry.py` — entrypoint genérico antes da extração específica;
- `app/confia_lean_auditor/student_claims/schemas.py` — seis tipos reutilizáveis;
- `app/confia_lean_auditor/claims/common/adapters.py` — projeção com revalidação da fonte e contexto;
- `app/confia_lean_auditor/claims/common/canonical.py` — tradução de bindings locais e retenção explícita de negação;
- `app/confia_lean_auditor/main.py` — integração do entrypoint e preservação do despacho Lean.

Novos: `student_claims/generic_math.py`, `tests/test_generic_student_math.py`, `tests/test_generic_student_math_pipeline.py` e este relatório. Scripts, snapshots, diagnóstico, catálogos, replay e logs estão em `artifacts/evaluations/ita1000_v1_2/p1_student_claim_coverage_01/`.

[Diff incremental](../../artifacts/evaluations/ita1000_v1_2/p1_student_claim_coverage_01/implementation.diff) compara com o snapshot inicial desta tarefa, incluindo o estado sujo anterior, e não com o HEAD antigo. [Validação](../../artifacts/evaluations/ita1000_v1_2/p1_student_claim_coverage_01/validation_summary.json), [replay](../../artifacts/evaluations/ita1000_v1_2/p1_student_claim_coverage_01/replay_summary.json) e [Git status completo](../../artifacts/evaluations/ita1000_v1_2/p1_student_claim_coverage_01/git_status_short.txt) são os registros finais.
