# P1-CLAIM-ALIGNMENT-02

## Resultado e escopo

Replay offline das mesmas **26 obrigações históricas**, em 11 soluções: **26 unmatched → 2 aligned, 0 conflicting, 0 ambiguous, 24 unmatched**. Isso não equivale a 26 soluções nem a um novo smoke. Foram incluídas cinco soluções prioritárias adicionais; nenhum batch de auditoria foi executado.

A conclusão genérica do primeiro algarismo em ITA2025F2Q5_S003_L04 passou a alinhar e apoiar `final_digit` (2 pontos) na avaliação primária. F2Q1_S001_L04 preserva o alinhamento que a ponte anterior já produzia, com prova Lean de estudante reutilizada. A política de score, o secondary adjudicator, a UI, os checkers, os contratos Lean e os gates P0 não foram editados.

## Estado encontrado e delimitação incremental

A tarefa anterior de cobertura estava concluída e possuía relatório, replay, diff incremental e validação. Nenhum trecho dessa implementação foi reiniciado ou revertido. O snapshot desta tarefa (`before.json` e `baseline_sources.tar.gz`) foi feito antes das alterações: inclui as modificações não commitadas das tarefas anteriores. O diagnóstico (`diagnosis_before.json` e `.md`) precedeu qualquer edição do motor.

O Git já estava sujo por trabalhos P0, MathClaimRecord, canonicalization, rubric bridge, cobertura e TME UI. O `implementation.diff` desta pasta compara apenas os arquivos desta tarefa contra o snapshot inicial, e não contra HEAD. SHA-256, HEAD e índice são verificados pelo finalizador. O estado Git completo é preservado em `git_status_short.txt`; ele não representa uma lista de alterações exclusivas desta tarefa.

## Diagnóstico anterior à edição

Todos os 26 casos tinham reference/expected histórico e claim_type. Em 24 havia representação do trecho no lado estudante; dois trechos verbais permaneciam sem claim. O expected possuía canonicalização parsed em 12, unsupported em 11 e ambiguous em 3. O caminho histórico por tipo bloqueava os 26 antes de uma comparação canônica entre os pares potenciais. A mera existência de um record parsed não assegurava que ele representasse a obrigação completa.

O arquivo `diagnosis_before.json` registra por par: existência, tipos, compatibilidade anterior, canonicalização de ambos, dados estruturados, grounding, semantic_role, execução efetiva da equivalência e uma sondagem canônica separada. A sondagem diagnóstica não é confundida com equivalência executada pelo motor anterior. Nenhum dos 26 carecia totalmente de reference histórico; alguns careciam de um expected matemático completo.

| Categoria primária | Quantidade |
|---|---:|
| grounding_or_context_blocks | 11 |
| expected_canonical_unavailable | 6 |
| incompatible_historical_type | 5 |
| student_parser_limitation | 2 |
| semantic_verbal_unsupported | 2 |

## Arquitetura implementada

1. `schemas.ExpectedObligation` acrescenta metadados explícitos: criterion_id, claim_id, claim_type, expected_payload, required_microclaim_ids, representation_source e quantity_subject. O MathClaimRecord mantém canonical_form, provenance `reference_expected` e identidade histórica. Metadados descritivos não concedem autoridade de prova.
2. `expected.explicit_obligations` constrói projeções somente a partir de respostas estruturadas e contratos já declarados nas regras positivas. Bindings exigem confirmação pelo correct_answer; primeiro algarismo exige inteiro de 0 a 9; equações vêm de requisitos explicitamente matemáticos. Todas as alternativas declaradas participam. Descrições vagas e critérios compostos não viram matemática inventada.
3. `canonical.legacy_canonical_from_legacy` normaliza final_answer/coefficient_assignment/coefficient_solution com bindings completos. Para resposta escalar histórica, o símbolo vem do contrato declarado e o valor vem do payload real; não se troca um valor errado pela resposta esperada.
4. `compatibility.project_pair` faz projeções semânticas reutilizáveis para bindings, relações/expressões matemáticas e primeiro algarismo. Usa a API canônica existente e igualdade estruturada tipada. Uma igualdade inteira só é candidata quando representa a mesma proposição ou um sujeito estrutural concorrente. Uma expressão escalar isolada não prova seleção de raiz, igualdade de funções ou paridade.
5. `alignment.align_claims` mantém validação da projeção, fonte atribuível, grounding e ambiguidade. Acrescenta os tipos genéricos compatíveis ao caminho legado. Divergência matemática produz conflicting; interpretações concorrentes produzem ambiguous; unknown permanece unmatched. Não há similaridade livre de strings ou substring como prova.
6. `alignment.align_obligations` resolve a ambiguidade entre obrigações antes de a rubrica consumir qualquer resultado. Um claim alinhável a critérios distintos fica ambiguous, sem escolha silenciosa pela ordem. Variantes explícitas do mesmo critério são alternativas documentadas, não obrigações concorrentes.
7. `RubricClaimContext` mantém cache dos resultados e fornece ao gate apenas evidência aligned. Reutiliza verificação Lean de estudante com identidade, dados e fonte compatíveis; na ausência dessa prova, aplica somente os verificadores determinísticos já existentes de expected value/relation. Refutações e requisitos de microclaims permanecem soberanos.
8. `catalog.build_claim_catalog` publica todos os expected variants, canonical forms, alignment status/basis e verification links. CriterionTrace inclui os IDs dos claims genéricos efetivamente consumidos pela ponte, além dos vínculos históricos por tipo.

Não foram introduzidas condições por dataset_id, solution_id ou novos `if problem_id ==` na compatibilidade. As regras preexistentes por problema continuam sendo a fonte dos contratos matemáticos explícitos.

## Replay das 26 obrigações

`replay_offline.py` executa o app do snapshot em diretório temporário para o antes e o app atual para o depois. Reutiliza texto, extração de referência, microclaims e resultados de checks históricos. Não chama execute_audit, Lean, adjudicadores ou provedores. A avaliação primária da rubrica é repetida com a mesma evidência salva; score final adjudicado e feedback não são regenerados.

Cada diretório `replay/{before,after}/{dataset_id}` contém student_claims, math_claims, rubric e uma cópia byte a byte do audit histórico. Links das novas decisões apontam para `rubric.json`; links de provas históricas continuam em `audit.json`. Os arquivos originais do Smoke V2 não são reescritos.

| Solução | Reference | Antes | Depois | Basis / limitação restante |
|---|---|---|---|---|
| ITA2025Q1_S016_L01 | positive_root_selection | unmatched | unmatched | other: grounding/context blocks |
| ITA2025Q1_S016_L01 | final_answer | unmatched | unmatched | other: grounding/context blocks |
| ITA2025Q1_S001_L04 | z_squared_coordinates | unmatched | unmatched | expected outside canonical domain |
| ITA2025Q1_S001_L04 | area_formula | unmatched | unmatched | student claim without complete structured expected obligation |
| ITA2025Q1_S001_L04 | area_equation | unmatched | aligned | canonical_equivalence |
| ITA2025Q1_S001_L04 | positive_root_selection | unmatched | unmatched | student claim without complete structured expected obligation |
| ITA2025Q1_S001_L04 | final_answer | unmatched | aligned | canonical_equivalence |
| ITA2025Q1_S014_L04 | z_squared_coordinates | unmatched | unmatched | expected outside canonical domain |
| ITA2025Q3_S004_L01 | parity_obstruction | unmatched | unmatched | expected outside canonical domain |
| ITA2025Q3_S002_L01 | first_factor_exponent_form | unmatched | unmatched | parser limitation |
| ITA2025Q3_S002_L01 | second_factor_exponent_form | unmatched | unmatched | parser limitation |
| ITA2025Q3_S002_L01 | parity_obstruction | unmatched | unmatched | semantic verbal unsupported |
| ITA2025Q3_S001_L04 | first_factor_exponent_form | unmatched | unmatched | other: grounding/context blocks |
| ITA2025Q3_S001_L04 | second_factor_exponent_form | unmatched | unmatched | other: grounding/context blocks |
| ITA2025Q3_S001_L04 | parity_obstruction | unmatched | unmatched | other: grounding/context blocks |
| ITA2025Q4_S003_L04 | positive_witnesses | unmatched | unmatched | expected outside canonical domain |
| ITA2025Q4_S003_L04 | same_f_argument | unmatched | unmatched | student claim without complete structured expected obligation |
| ITA2025Q4_S003_L04 | distinct_g_inputs | unmatched | unmatched | semantic verbal unsupported |
| ITA2025Q4_S003_L04 | equal_g_values | unmatched | unmatched | expected outside canonical domain |
| ITA2025Q4_S003_L04 | not_injective_conclusion | unmatched | unmatched | other: grounding/context blocks |
| ITA2025Q4_S002_L02 | same_f_argument | unmatched | unmatched | other: grounding/context blocks |
| ITA2025Q4_S002_L02 | distinct_g_inputs | unmatched | unmatched | other: grounding/context blocks |
| ITA2025Q4_S002_L02 | not_injective_conclusion | unmatched | unmatched | other: grounding/context blocks |
| ITA2025F2Q6_S006_L04 | final_answer | unmatched | unmatched | other: grounding/context blocks |
| ITA2025F2Q6_S001_L04 | probability_formula | unmatched | unmatched | expected outside canonical domain |
| ITA2025F2Q6_S017_L04 | probability_formula | unmatched | unmatched | other: grounding/context blocks |

As duas novas correspondências são a equação de área e a resposta final a=15 de ITA2025Q1_S001_L04. A equação é comparada como igualdade completa; a resposta escalar histórica é projetada com o símbolo a do contrato. Ambas usam canonical_equivalence. A pontuação primária desses critérios já era apoiada pela evidência anterior, portanto o novo alignment melhora a conexão observável sem elevar seus pontos.

### Motivos dos 24 unmatched restantes

| Categoria | Quantidade |
|---|---:|
| other: grounding/context blocks | 11 |
| expected outside canonical domain | 6 |
| student claim without complete structured expected obligation | 3 |
| parser limitation | 2 |
| semantic verbal unsupported | 2 |

Os 11 casos classificados como other preservam o bloqueio de grounding/contexto: a existência de texto literal ou canonical form não o torna afirmação atribuível. Os seis expected fora do domínio canônico incluem coordenadas complexas, paridade, testemunhas/igualdade funcional e a fórmula probabilística de F2Q6. Os dois limites de parser são as formas exponenciais da solução Q3_S002_L01.

Os três casos sem expected completo são: area_formula (o payload escalar/expressão não representa sozinho o requisito composto de determinante); positive_root_selection (o número -13 isolado não expressa a seleção/descarte da raiz); same_f_argument (29/32 não expressa sozinho a igualdade de argumentos de f). Não se infere a obrigação inteira de um fragmento numérico. Os dois trechos verbais continuam sendo “que é ímpar” e “valores distintos entre si”; não foi adicionado parser verbal.

## Casos prioritários e efeito na rubrica

Os cinco casos prioritários adicionais não entram no denominador das 26 obrigações. Em particular, o novo alinhamento de final_digit em F2Q5 é reportado separadamente dos dois aligned dessa seleção fixa.

| Solução | StudentClaims | Critério final | Pontos | Alignment | Verification basis |
|---|---:|---|---:|---|---|
| ITA2025F2Q1_S001_L04 | 24 | final_answer | 2.0 | aligned | formal_lean_verified |
| ITA2025F2Q5_S003_L04 | 28 | final_digit | 2.0 | aligned | deterministic_expected_value |
| ITA2025Q4_S002_L04 | 0 | — | — | — | — |
| ITA2025F2Q1_S003_L02 | 1 | final_answer | None | — | — |
| ITA2025F2Q5_S024_L04 | 16 | final_digit | None | conflicting | — |

F2Q1_S001_L04: os bindings a=-1,b=3 alinham naturalmente com a obrigação explícita; o resultado formal salvo do estudante é aproveitado, sem uma nova execução Lean no replay. O critério final permanece com 2 pontos antes e depois. A melhoria não é apresentada como se esse apoio, já entregue pela ponte anterior, fosse novo.

F2Q5_S003_L04: a nova extração genérica prévia já continha o primeiro algarismo 5 com grounding. Agora o conceito leading_digit, o valor inteiro e o sujeito matemático compatível fecham a ligação com a obrigação. O critério final muda de indeterminate/None para supported/2 na rubrica primária, com deterministic_expected_value; isso não é uma prova Lean fabricada. É a única mudança de decisão primária nas soluções reprocessadas.

F2Q3: cos beta = sen beta + 1/2 permanece equivalente a cos beta - sen beta = 1/2 pela API canônica. O teste focado cobre o alinhamento, a comparação isolada do snapshot preserva os resultados da variante, e os testes de pipeline existentes verificam a integração.

Casos anteriormente chamados “zero claims”: Q4_S002_L04 continua com zero StudentClaims; F2Q1_S003_L02 conserva um registro genérico sem apoio para a resposta final; F2Q5_S024_L04 conserva 16 registros e o algarismo 4 é conflicting, sem crédito final. A quantidade de claims não é confundida com verificação ou pontuação.

A verificação de integridade (`verify_replay.py`) validou 32 catálogos antes/depois, 478 JSON pointers e a existência/SHA-256 da prova Lean reutilizada. Todos os aligned possuem fonte grounded e atribuível. O resultado está em `replay_integrity.json`; nenhuma prova foi reexecutada nessa verificação.

## Falsos positivos, testes e regressões

Foram adicionados 43 testes em `tests/test_claim_alignment_obligations.py`: sintaxe equivalente, ordem de bindings, tipos históricos, valores incorretos, not_equivalent, unknown controlado, candidatos múltiplos, referências heurísticas, ausência de expected matemático e casos prioritários. Entre os adversariais: a=-1,b=3 versus a=3,b=2; x²=4 versus x=2; negação do algarismo; último versus primeiro algarismo; quantidade 2^100 versus 3^100; citação e hipótese; equações intermediárias versus atribuição final.

O teste de pipeline genérico preexistente foi atualizado para exigir a nova evidência determinística de final_digit=2, todos os demais critérios sem crédito, nenhum check Lean genérico fabricado e o vínculo correto no CriterionTrace. Ele não é contado como teste novo.

Na primeira comparação de paridade, equações polinomiais intermediárias com a mesma variável foram equivocadamente tratadas como respostas finais concorrentes em três fixtures. A projeção de atribuição final foi restringida ao domínio afim comparável; dois testes de regressão foram acrescentados, preservando o conflito de uma resposta linear errada. O resultado final compara 88 rubricas legadas com igualdade integral e 88 avaliações com a ponte ativa sem mudança de decisão. Mudanças de metadados/evidência são registradas separadamente em baseline_parity.json.

A rodada focada final passou com 501 testes. A suíte ampla é dividida em grupos disjuntos; reruns focados não são somados de novo. O runner remove credenciais de provedores, desativa formalização LLM e bloqueia conexões IP externas. As três falhas conhecidas HMER/UI vocabulary/tablet sticky e o xfail F2Q6 são preservados, não corrigidos.

<!-- FINAL_VALIDATION_START -->
Resultado final: **1574 casos únicos — 1570 passed, 3 falhas preexistentes e 1 xfailed esperado**. Nenhuma regressão nova.

| Grupo | Passed | Failed | Xfailed |
|---|---:|---:|---:|
| broad | 1345 | 3 | 0 |
| proof_pipeline | 149 | 0 | 1 |
| reference_pipeline | 75 | 0 | 0 |
| immutability | 1 | 0 | 0 |

Falhas conhecidas: HMER (`test_projection_preserves_falsehoods_signs_and_general_fractions`), UI vocabulary (`test_central_product_vocabulary_is_preserved_without_contract_renames`) e tablet sticky (`test_parent_statement_is_compact_and_sticky_through_notebook_and_submission`). O xfail F2Q6 permanece esperado; não foi corrigido.

Os 43 testes novos passaram. O teste de pipeline existente atualizado também passou. Reruns focados não são contados duas vezes. O teste de imutabilidade rodou isolado, com stdout em /tmp e sem outros escritores de artifacts.

Preservação: 321 arquivos históricos Smoke V2 idênticos por SHA-256; 3081 arquivos preexistentes idênticos e somente os seis arquivos previstos alterados. `git diff --check`: OK. HEAD e índice idênticos ao snapshot. Nenhum arquivo staged.

O estado completo do Git, incluindo alterações de tarefas anteriores, está em `git_status_short.txt`. Contagens: {' M': 55, '??': 41}.
<!-- FINAL_VALIDATION_END -->

## Desempenho e limitações

O replay de 16 textos salvo nesta execução levou 1.620s antes e 1.664s depois, incluindo construção de contexto, avaliação primária e serialização. São medições locais de uma rodada, não um benchmark estatístico. O alinhamento é calculado uma vez por contexto e reutilizado pelos consumidores; nenhum Lean ou serviço foi chamado para medir isso.

O domínio canônico permanece deliberadamente limitado. Igualdades não lineares intermediárias não se tornam respostas finais por compartilhar variável. Um payload numérico parcial não comprova uma obrigação verbal composta. Grounding não é ampliado por esse trabalho. A comparação canônica unknown não é convertida em equivalent. O score global final do smoke não foi recalculado, e os resultados de prova reutilizados não representam uma nova certificação Lean.

## Arquivos exclusivos desta tarefa

Modificados incrementalmente: `claims/common/{alignment,canonical,catalog,rubric_bridge,schemas}.py` e `tests/test_generic_student_math_pipeline.py`. Novos: `claims/common/{expected,compatibility}.py`, `tests/test_claim_alignment_obligations.py` e este relatório. Os caminhos dos módulos são relativos a `app/confia_lean_auditor/`.

Artifacts finais e ferramentas de reprodução estão em `artifacts/evaluations/ita1000_v1_2/p1_claim_alignment_02/`: snapshot, diagnóstico, replay antes/depois, summaries, logs, comparação com baseline, validação Git e diff incremental. `incremental_stat.json` enumera os arquivos e linhas acrescentadas/removidas. `git_checks.json` registra o resultado literal dos comandos Git somente de leitura.

Nenhum staging, commit, push, reset, restore ou clean foi executado.
