# TME² P4 — ponte de evidências e pauta

## Escopo e estado inicial

Implementação opt-in de `TME2026P4` sobre o commit `f22b18e`, branch
`feat/tme-dual-input`, com árvore de trabalho inicialmente limpa. Não houve
staging, commit, push, chamadas de LLM, secondary, OCR ou benchmark grande.
O artefato `baseline.json` registra HEAD, status e hashes dos arquivos versionados.

Há uma divergência de nomenclatura no pedido: neste commit, o ID efetivamente
registrado de P1 é `TME2_P1_PILOT`, não `TME2026P1`. Foi preservado, sem migração
ou alteração de contrato. P3 continua `TME2026P3`; P4 é o terceiro problema no
registry matemático opt-in. Nenhum deles foi adicionado ao catálogo ITA.

## Arquitetura reutilizada

`texto DIGITAL por item → collect_digital_items → extract_named_math → MathClaimRecord
→ FactResultsBuilder/FactResult → bridge_facts → PautaEvidence → PautaEngine`.

O engine, seus modelos e a ponte comum não foram alterados. Os producers não
possuem pontos. A pauta JSON aplica toda a pontuação: A=4, B=6, C=10. O registry
apenas despacha o problema; não modifica `/audit`.

Foram estendidos somente dois componentes comuns de execução:

- `named_math`: tipos opt-in `relation`, `expression_set` e `set_equality`, com
  a gramática limitada e a canonicalização existentes. Nenhum vocabulário
  anterior foi alterado. Conjuntos têm no máximo 12 membros, sem aproximação.
- `evaluate_student_proof`: parâmetro opcional de validação de grounding para
  projeções nativas. O valor padrão continua `has_valid_grounding`; todos os
  consumidores ITA/P1/P3 mantêm o gate original. P4 fornece validação estrita
  por reextração, igualdade do payload completo, span e hash do documento.

O novo checker `real_algebra` reutiliza o ciclo de prova, classificação de
falha técnica e compilação separada da negação. Não adiciona um motor de
provas, um CAS ou uma camada de pontuação. Os registros formais são nativos:
`project_student_claim` continua recusando sua execução no checker inteiro legado.

## Contrato DIGITAL e grounding

O piloto aceita asserções tipadas completas por linha, como em P3. Exemplo:

```text
triangle_PBQ: equilateral
PB: x
BQ: x
PQ: x
perimeter_PBQ: 3*x
shaded_sum: 3*x+3*(6-x)=18
```

Nomes são normalizados sem distinguir maiúsculas e minúsculas. Os campos
aceitos estão em `student_claims/tme2_p4_digital.py`. Valores matemáticos passam
pelo parser comum. Isso permite `3(6-x)`/`18-3x`, frações equivalentes exatas e
ordem diferente dos membros de conjuntos, sem ignorar sinais.

Campos de relações:

- `exclude_12: (3*x)^2+(3*(6-x))^2=12^2` significa explicitamente **esta equação
  não possui solução real**. O rótulo tipado expressa a exclusão; não é uma
  hipótese que o motor promove a afirmação positiva.
- `h_plus_c: h+c=18` e `pythagoras: h^2=c^2+144` relacionam os dois perímetros
  sombreados, com `h` designando a hipotenusa e `c` o outro cateto.
- `case_3x` e `case_other` identificam as equações de Pitágoras nos dois casos;
  `case_3x_root` e `case_other_root` apresentam suas soluções respectivas.
- `shaded_lengths: {3*x,3*(6-x)}={5,13}` expressa a correspondência não ordenada.
- `x_candidates: {5/3,13/3}` expressa o conjunto de respostas, sem inventar sua
  derivação. Uma raiz isolada não equivale ao conjunto completo.

Palavras-chave isoladas, rótulos desconhecidos e prosa não suportada permanecem
sem evidência para a obrigação. Não há fallback semântico. Negações, citações,
hipóteses e tentativas rejeitadas passam pelo `contextual_role` já existente.
Um resultado corretamente mencionado mas explicitamente rejeitado no mesmo
contexto não recebe crédito. As fronteiras de parágrafo são preservadas.

Cada claim guarda `raw_text`, offsets no documento DIGITAL composto, SHA-256,
canonical form, origem e papel semântico. Antes de verificar, o producer
reconstrói a coleta a partir do texto e exige igualdade integral: mutações de
canonical form, roteamento ou texto são recusadas. A ponte confere fingerprints,
links de verificação, origem e atribuição.

## Geometria estruturada, sem alegação de formalização euclidiana

`P4Geometry` registra a fonte como o contrato fornecido no pedido: AB=6,
PB=x e P no segmento AB. Daí o domínio `0 ≤ x ≤ 6`. Não foi necessário
inventar hipóteses adicionais, nem baixar ou interpretar uma figura.

O modelo contém os comprimentos PB=BQ=PQ=AR=RA=x e AP=QC=QR=RC=6−x. Perímetros
são somas desses lados. As propriedades PBQ/RQC equiláteros e APQR paralelogramo
são confrontadas com o contrato geométrico fornecido. Não são inferidas de
respostas finais nem provadas por um modelo euclidiano em Lean.

Fatos desses tipos usam `verification_source=deterministic` e
`metadata.verification_kind=deterministic_geometry`, compatíveis com a ponte.
O campo `geometry_source` mantém a origem. A geometria não é reclassificada
como formal apenas porque uma identidade numérica/algebraica foi compilada.

Quando uma fórmula geométrica é comparada formalmente com a expressão derivada
dos lados, o escopo é **equivalência algébrica sob o contrato geométrico**.
Por exemplo, provar `∀x, 3x=x+x+x` não é provar que PBQ é equilátero.

## Álgebra e Lean

O renderer traduz somente ASTs reconhecidas: inteiros exatos em ℝ, variáveis
`x/h/c`, operações +, −, ×, divisão por constante não nula e potências pequenas.
Não insere texto do estudante diretamente como código Lean. Divisão variável,
funções não suportadas, expoentes grandes e código injetado são recusados.
Decimais podem ser comparados exatamente pelo canonicalizador; não há conversão
aproximada para raízes. Algumas sintaxes canônicas não têm renderer formal e
permanecem verificadas apenas pelo mecanismo canônico, explicitamente identificado.

Proposições selecionadas para prova local:

1. Perímetros escritos de PBQ/RQC são equivalentes às somas de seus lados.
2. `∀x:ℝ, 3*x+3*(6-x)=18` — identidade A, com os membros efetivamente escritos.
3. `∀x:ℝ, (6-x)+x+(6-x)+x=12` e a forma por paralelogramo
   `2*((6-x)+x)=12` — identidades B.
4. `∀x:ℝ, ¬((3*x)^2+(3*(6-x))^2=12^2)` — C2. A prova usa
   `sq_nonneg (x-3)`; o certificado determinístico correspondente é
   `18*(x-3)^2+162 ≥ 162 > 144`.
5. Sob `h+c=18` e `h²=c²+144`, obtém-se `h-c=8`, seguido de `h=13` ou `c=5`
   em provas separadas. A álgebra já determina os valores: não foi necessário
   adicionar positividade artificial. Esse contexto só é atribuído à derivação
   do estudante se as duas relações estiverem presentes e verificadas.
6. Sob a equação de cada caso, `x=13/3` ou `x=5/3`, respectivamente.
7. De `3*x=5 ∨ 3*x=13`, deduz-se o conjunto de raízes escrito pelo estudante.
   A premissa é uma consequência derivada pelo motor da igualdade de conjuntos
   explicitamente fornecida, registrada como `engine_derived_premise`, não como
   nova citação do aluno.

As identidades e a exclusão valem para todo real; as raízes estão no domínio
geométrico. Os certificados não precisam da restrição `0≤x≤6`. Os contraexemplos
usados na refutação de fórmulas de lados/perímetros também pertencem ao domínio.

Não foram formalizados em Lean: geometria euclidiana, identificação visual,
prosa livre, igualdade de conjuntos geométricos como estrutura de conjuntos,
completude narrativa de uma solução. A seleção/alinhamento dessas proposições
é determinístico e canônico. O passo formal da união de raízes é a implicação
algébrica declarada acima, não uma formalização de toda a geometria.

`student_asserted` referencia somente o registro literal. Expressões calculadas,
contextos e premissas do motor têm metadados separados. `formally verified` só
ocorre após compilação. Falha técnica produz `technical_error`; falta de prova
produz `unverified`. Somente uma negação compilada produz refutação formal.

## Pauta e métodos alternativos

- A1 exige reconhecimento de PBQ equilátero, lados e perímetro; A2 faz o mesmo
  para RQC. A3 exige desenvolvimento da soma, não apenas `18` ou `18=18`.
- B usa `max_of(official_metric_path, parallelogram_path)`. O caminho oficial
  é aditivo (2+2+2); o caminho alternativo exige paralelogramo e cálculo válido
  do perímetro, sem exigir os quatro campos de lados do caminho oficial. Ambos
  atingem 6/6, nunca 12/6. O cálculo aceita quatro parcelas, duas parcelas
  dobradas ou um fator 2 externo à soma dos lados adjacentes.
- C1 e C2 são comuns (2+2). Os 6 pontos restantes usam `max_of(h_c_path,
  cases_path)`, cada um aditivo. O segundo exige ambos os casos para representar
  uma análise completa, em qualquer ordem. Uma análise somente de `3x` não
  inventa a análise de `3(6-x)`.
- `h=13,c=5` isolados recebem apenas C4; não fabricam C3. Raízes isoladas não
  fabricam C5. Uma falha posterior preserva o crédito anterior independente.

A decomposição de somas inspeciona as operações escritas e usa equivalência
afím limitada para seus termos. Não aceita uma tautologia apenas por reduzir
ao mesmo total. O reconhecimento de Pitágoras compara separadamente os dois
catetos e a hipotenusa, inclusive permutações; uma equação impossível qualquer,
como `0=1`, não serve como exclusão de 12.

## Explicabilidade

O replay salva, para cada caso, a entrada, o bundle completo, a evidência da
ponte e a avaliação. A árvore de avaliação contém obrigações, status, pontos,
crédito autorizado, evidências e método escolhido. Assim é possível percorrer:

`item → folha da pauta → obrigação → FactResult → source_claim_ids → MathClaimRecord
→ verification_source/certificado → pontos da folha`.

Os 31 IDs atômicos estão no mapa explícito `TME2_P4_OBLIGATIONS` e na pauta.
Uma obrigação ausente permanece `indeterminate`, sem IDs inventados. Resultados
conflitantes para o mesmo fato também permanecem inconclusivos. Na origem formal,
a ponte exige igualdade de payload e de source binding, além do certificado.

## Limitações e riscos residuais

- Este é um piloto DIGITAL com gramática explícita, não cobertura geral de
  redações livres ou diagramas. Uma solução matematicamente válida fora da
  gramática pode ficar inconclusiva; isso é preferível a atribuição inventada.
- O contrato geométrico é fornecido pelo pedido, não validado visualmente ou
  axiomatizado. Alterar o problema exige revisar esse contrato e seus testes.
- Há reconhecimento limitado de forma quadrática (quadrados dos perímetros),
  sem CAS para polinômios arbitrariamente expandidos. Equivalência desconhecida
  não vira refutação.
- O modo `use_lean=False` não simula certificados. Usa somente os mecanismos
  determinístico/canônico identificados; os certificados reais estão no replay
  selecionado com Lean.
- A evidência formal permanece condicionada ao contexto documentado. Nenhuma
  prova produz por si só afirmações intermediárias ausentes do estudante.
- As comparações idênticas P1/P3 cobrem os 45 casos controlados e seus outputs
  completos sem Lean, para evitar diferenças de UUID e caminhos de execução.
  Não são uma alegação de acurácia universal ou de igualdade byte a byte entre
  execuções formais com identificadores de run distintos.

## Validação final

- Casos controlados: **38/38**; obrigações atômicas cobertas: **31/31**.
- Testes direcionados: **333 passed** (89 novos de P4; engine/P1/P3 preservados).
- Regressão compartilhada/ITA: **703 passed**, incluindo auditoria offline real F2Q3.
- Total das suítes executadas: **1036 passed**, zero falhas e zero xfail nessas suítes. Não é contagem da suíte inteira do repositório.
- Lean real selecionado: **29** verificações, **24 verified**, **5 refuted**, zero falhas técnicas/inconclusivas.
- P1: 20 outputs completos idênticos byte a byte; P3: 25 outputs completos idênticos byte a byte.
- 124 arquivos protegidos de ITA/engine/HMER/secondary/frontend mantiveram o hash da linha de base.
- Rechecagem determinística do código final: 38 resultados, status e caminhos iguais ao replay formal selecionado.
- Zero regressões observadas nas verificações executadas. Não foram alteradas nem incluídas correções de UI, HMER ou secondary.
- `git diff --check`: OK. HEAD preservado; índice sem alterações.

Comandos executados:

```sh
.venv/bin/python -m pytest -q tests/test_pauta_engine.py tests/test_tme2_p1_pauta_bridge.py tests/test_tme2_p3_pauta_bridge.py tests/test_tme2_p4_pauta_bridge.py
.venv/bin/python -m pytest -q tests/test_claim_fidelity.py tests/test_math_canonical.py tests/test_common_math_claims.py tests/test_audit_math_canonicalization.py tests/test_math_canonical_pipeline.py tests/test_rubric_bridge.py tests/test_positive_credit_evidence.py tests/test_student_proof_semantics.py tests/test_score_policy.py tests/test_score_policy_api.py tests/test_generic_student_math.py tests/test_claim_alignment_obligations.py
.venv/bin/python scripts/evaluation/run_tme_pauta_cases.py --problem TME2026P4 --output artifacts/evaluations/tme2_p4_pauta_bridge/replay_final --lean-cases a_complete,a_wrong_perimeter,a_wrong_sign,b_official,b_parallelogram,b_wrong_ap,c_complete,c_cases,c_local_error,c_wrong_roots
```

A primeira execução formal encontrou dois diagnósticos `linarith failed` tratados conservadoramente como erro técnico pelo classificador legado. Os templates novos de P4 foram ajustados para deixar objetivos não resolvidos quando uma candidata não é provada e permitir a compilação separada da negação. O classificador não foi alterado. A execução formal final revalidou os mesmos dez casos selecionados, incluindo os positivos. Os logs iniciais permanecem disponíveis para rastreabilidade.

A revisão adversarial também acrescentou o gate de variáveis não ligadas: `AP:y`, `h:h` e conjuntos de raízes simbólicos não resolvidos ficam inconclusivos, sem refutação ou crédito artificial. Esse gate não modifica as 38 soluções controladas nem as proposições formais já verificadas.

Contagem de fatos no replay final (inclui repetições entre casos):

| Mecanismo | Quantidade |
|---|---:|
| deterministic | 66 |
| student_lean | 29 |
| canonical_equivalence | 145 |

| Resultado de fato | Quantidade |
|---|---:|
| verified | 227 |
| refuted | 12 |
| unverified | 1 |

| Status de obrigação no item avaliado | Quantidade |
|---|---:|
| supported | 227 |
| indeterminate | 186 |
| refuted | 12 |

### Casos controlados

| Caso | Item | Pontos | Resultado |
|---|---|---:|---|
| a_complete | a | 4 | PASS |
| a_only_pbq | a | 1 | PASS |
| a_both_no_sum | a | 2 | PASS |
| a_bare_18 | a | 0 | PASS |
| a_equivalent | a | 4 | PASS |
| a_wrong_sign | a | 2 | PASS |
| a_wrong_perimeter | a | 3 | PASS |
| a_no_geometry | a | 2 | PASS |
| a_sum_tautology | a | 0 | PASS |
| b_official | b | 6 | PASS |
| b_parallelogram | b | 6 | PASS |
| b_bare_12 | b | 0 | PASS |
| b_partial | b | 2 | PASS |
| b_reordered | b | 6 | PASS |
| b_rejected | b | 0 | PASS |
| b_keyword_only | b | 0 | PASS |
| b_doubled | b | 6 | PASS |
| b_wrong_ap | b | 4 | PASS |
| b_both_paths | b | 6 | PASS |
| c_complete | c | 10 | PASS |
| c_cases | c | 10 | PASS |
| c_cases_reversed | c | 10 | PASS |
| c_only_c1 | c | 2 | PASS |
| c_c1_c2 | c | 4 | PASS |
| c_relations_no_resolution | c | 6 | PASS |
| c_only_values | c | 2 | PASS |
| c_only_roots | c | 0 | PASS |
| c_local_error | c | 8 | PASS |
| c_rejected_conclusion | c | 8 | PASS |
| c_one_root | c | 8 | PASS |
| c_wrong_roots | c | 8 | PASS |
| c_exact_rationals | c | 10 | PASS |
| c_rounded_roots | c | 8 | PASS |
| c_no_exclusion | c | 8 | PASS |
| c_unrelated_exclusion | c | 8 | PASS |
| c_incomplete_cases | c | 4 | PASS |
| c_x_two | c | 8 | PASS |
| c_bad_assignment | c | 8 | PASS |

### Certificados formais

As proposições exatas, valores negativos literais, contextos e caminhos dos certificados estão em `replay_final/replay_summary.json` e nos bundles por caso. As 5 refutações são as afirmações de perímetro `4x`, soma com sinal errado, `AP=x`, `h=12` e conjunto de raízes `{2,4}`. O controle de raiz isolada `{2}` também é refutado pelo checker canônico, sem fabricar uma prova de completude.

### Arquivos adicionados/modificados

- `app/confia_lean_auditor/lean/student_claim_checkers/real_algebra.py`
- `app/confia_lean_auditor/lean/student_claim_checkers/tme2_p4.py`
- `app/confia_lean_auditor/lean/student_proof.py`
- `app/confia_lean_auditor/rubric/pauta/tme2_p4.py`
- `app/confia_lean_auditor/student_claims/named_math.py`
- `app/confia_lean_auditor/student_claims/tme2_p4_digital.py`
- `app/confia_lean_auditor/tme/p4_geometry.py`
- `app/confia_lean_auditor/tme/registry.py`
- `docs/audits/TME2_P4_PAUTA_BRIDGE.md`
- `examples/pautas/tme2_problem4.v1.json`
- `scripts/evaluation/run_tme_pauta_cases.py`
- `tests/fixtures/tme2_p4_digital/cases.json`
- `tests/test_tme2_p3_pauta_bridge.py`
- `tests/test_tme2_p4_pauta_bridge.py`

A única alteração no teste existente de P3 atualiza o conjunto esperado do registry para incluir P4. Nenhuma asserção matemática de P3 foi removida ou relaxada.

### Artefatos

Diretório: `artifacts/evaluations/tme2_p4_pauta_bridge/`.

- `validation_summary.json`: consolidação final.
- `replay_final/replay_summary.json` e 38 bundles: replay com Lean selecionado.
- `final_semantic_recheck.json`: conferência final dos 38 casos.
- `p1_p3_regression.json`, `*_before.json`, `*_after.json`: comparação integral de P1/P3.
- `targeted_tests.log`, `regression_tests.log`: execução das suítes.
- `baseline.json`, `implementation.diff`, `git_diff_check.txt`, `git_status.txt`: escopo e estado Git.

### Git final

```text
 M app/confia_lean_auditor/lean/student_proof.py
 M app/confia_lean_auditor/student_claims/named_math.py
 M app/confia_lean_auditor/tme/registry.py
 M scripts/evaluation/run_tme_pauta_cases.py
 M tests/test_tme2_p3_pauta_bridge.py
?? app/confia_lean_auditor/lean/student_claim_checkers/real_algebra.py
?? app/confia_lean_auditor/lean/student_claim_checkers/tme2_p4.py
?? app/confia_lean_auditor/rubric/pauta/tme2_p4.py
?? app/confia_lean_auditor/student_claims/tme2_p4_digital.py
?? app/confia_lean_auditor/tme/p4_geometry.py
?? docs/audits/TME2_P4_PAUTA_BRIDGE.md
?? examples/pautas/tme2_problem4.v1.json
?? tests/fixtures/tme2_p4_digital/
?? tests/test_tme2_p4_pauta_bridge.py
```

Sem staging, commit ou push.
