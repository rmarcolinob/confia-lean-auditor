# TME² P5 — pauta, maximalidade e carry-forward

## Estado inicial e escopo

P5 foi acrescentado sobre a árvore de trabalho existente no commit `f22b18e`,
branch `feat/tme-dual-input`. O trabalho de P4 estava sem commit e foi preservado.
`baseline.json` registra hashes de arquivos versionados e não versionados,
HEAD e status; `preexisting.diff` separa as alterações anteriores. As versões
iniciais dos arquivos compartilhados modificados nesta tarefa foram recuperadas
e conferidas pelos hashes antes de gerar o diff incremental.

O registry existente usa `TME2_P1_PILOT` para P1 (divergente do nome público
mencionado no pedido), além de `TME2026P3` e `TME2026P4`. Esses identificadores
foram preservados; `TME2026P5` é o quarto problema opt-in. Não houve migração
silenciosa de P1. O catálogo e o endpoint ITA não foram alterados.

Sem secondary, LLM, OCR, API externa, benchmark grande, staging, commit ou push.
P2 não foi implementado. Engine, modelos de pauta, ponte comum e política ITA
continuam os mesmos.

## Infraestrutura reutilizada

`texto por item → collect_digital_items/extract_named_math → MathClaimRecord
→ FactResultsBuilder/FactResult → bridge_facts/PautaEvidence → PautaEngine`.

Apenas o engine aplica pontos. O producer P5 verifica matemática e vínculos de
origem; não contém valores de pontuação. A pauta totaliza A=6, B=4, C=6, D=4.

Extensões compartilhadas, sem nova camada arquitetural:

- `named_math`: três tipos opt-in (`positive_multiset`, `partition_table`,
  `factored_product`). Os tipos anteriores mantiveram seus resultados.
- `integer_structures`: representações limitadas de listas e produtos. Reutiliza
  tokens, budgets e aritmética exata da infraestrutura canônica existente.
- `development`: a função já existente de reconhecimento de somas escritas foi
  extraída do checker P4 sem mudar o algoritmo. P4 mantém a importação pública
  compatível e P5 reutiliza a mesma função.
- `real_algebra`: o renderer e o ciclo de prova nativa de P4 agora também aceitam
  explicitamente o domínio `Z`. O padrão continua `R`, com as mesmas variáveis
  e saídas anteriores. A divisão é recusada no renderer inteiro para impedir
  mudança semântica por divisão truncada. Nenhum parser geral teve seus limites
  ampliados para aceitar expoentes enormes.
- Registry e runner de fixtures: novo despacho de P5 e suporte opcional a
  contexto de múltiplos itens, necessário ao carry-forward C→D.

O ciclo formal continua `evaluate_student_proof`: prova positiva, classificação
conservadora de falhas e, quando apropriado, compilação separada da negação.
Não foi modificado nesta tarefa. Não existe fallback de falha formal para
crédito determinístico no mesmo fato formal.

## Gramática DIGITAL e representações

O piloto usa asserções matemáticas tipadas por linha, como P3/P4. A gramática
completa está em `student_claims/tme2_p5_digital.py`. Prosa não reconhecida,
rótulos desconhecidos e construções fora dos limites continuam inconclusivos.
Não há inferência de intenção a partir de palavras-chave.

Exemplos de listas equivalentes, com ordem irrelevante:

```text
candidate: (2,3,3,3)
candidate: (3,3,2,3)
candidate: 2+3+3+3
candidate: {2:1,3:3}
```

A forma canônica é um mapa valor→multiplicidade, com inteiros positivos e chaves
normalizadas. Contagens duplicadas no mapa, zero, negativos, booleanos, código,
comentários e listas acima dos limites são recusados. Não são comparadas strings
de listas. Limites: até 128 entradas explícitas, 16 valores distintos na forma
compacta, valor/multiplicidade até 100.000, soma até 1.000.000 e orçamento de AST.

As listas grandes permanecem compactas:

```text
list_twos: {2:2,3:674}
list_four: {4:1,3:674}
```

O tipo de produto é diferente:

```text
max_product: 4*3^674
max_product: 12*3^673
max_product: 4*9^337
max_product: (2*3^337)^2
```

Todos têm a assinatura exata `{2:2, 3:674}` de expoentes primos. Os fatores
pequenos são fatorados e expoentes são combinados sem materializar `3^674`.
Exponentes são inteiros exatos limitados; variáveis, expoentes negativos ou
fracionários, bases não positivas e divisão não são aceitos nesse tipo.
Essa forma é uma representação limitada de produtos, não um CAS geral.

`list_twos: 4*3^674` não é uma lista reconhecida. O motor não transforma uma
potência em 674 elementos por adivinhação. A notação de multiplicidade dispensa
escrever centenas de números. Outras redações naturais de multiplicidade ainda
não têm interpretação automática neste piloto.

## A — maximalidade independente versus argumento do estudante

O módulo `p5_integer_break` enumera exatamente as 56 partições positivas não
ordenadas de 11, calcula seus produtos e encontra máximo 54. A única partição
maximizadora, ignorada a ordem, é `(2,3,3,3)`.

Isso verifica A1, mas **não gera A3**. O bundle registra separadamente
`engine_derived_maximum` e a ausência de argumento estudantil. O cálculo A2
exige uma igualdade de produto com os fatores da candidata, e não `54=54`.

A3 possui duas formas de evidência:

1. `enumeration`: tabela explícita das partições, junto de `enum_max: 54`.
   O checker compara conjuntos de multiconjuntos, exige cobertura completa e
   ausência de listas extrínsecas. Repetições/ordem não alteram a cobertura.
   Uma tabela contendo somente a candidata não é uma enumeração completa.
2. Certificado estrutural de substituições: o aluno apresenta preservação de
   soma e aumento de produto para remover 1 e entradas ≥5, divisão de 4,
   melhora dos três 2 e uma `normal_list` de soma 11. Esses fatos explicitamente
   fornecidos justificam a redução a 3s e no máximo dois 2.

Os dois caminhos completos dão 6/6. `máximo=54`, `enum_max:54`, uma lista ótima
ou conhecimento interno do máximo não preenchem a justificativa ausente.

## B — substituição de n por 3 e n−3

A preservação da soma exige construção escrita, como `3+(n-3)=n`; `n=n` não
substitui essa evidência. A comparação usa as contribuições antiga `n` e nova
`3(n-3)`, reconhecendo formas afins equivalentes.

Para o aumento de produto, `domain: n>=5` é uma asserção separada obrigatória.
Aceita-se a desigualdade direta ou a combinação explícita de diferença e
positividade. A hipótese não é inventada pelo checker quando ausente.
O domínio formal é ℤ; a pertinência ao problema de inteiros positivos e a
positividade de `n-3` decorrem de n≥5.

Uma desigualdade oposta grounded é refutável. Já um domínio não reconhecido ou
uma expressão que não representa a contribuição em análise fica inconclusiva.

## C — máximo para 2026 e métodos alternativos

O argumento determinístico é matemático, não uma regra de pontuação:

1. Uma lista com 1 pode ser melhorada fundindo-o com outro inteiro positivo.
2. Uma entrada n≥5 pode ser substituída por 3 e n−3, com soma igual e produto maior.
3. Um 4 pode ser substituído por dois 2 sem alterar soma ou produto.
4. Três 2 podem ser substituídos por dois 3: soma 6 e produto 8→9.
5. Logo, uma forma normal ótima contém 3s e no máximo dois 2. Os resíduos da
   soma módulo 3 determinam as multiplicidades. Para 2026 são dois 2 e 674 três.

A existência do máximo usa o conjunto finito de partições positivas da soma.
Não se enumeram partições de 2026. O teorema de substituições foi confrontado
com enumeração independente para todas as somas de 2 a 18 nos testes.

A pauta usa `max_of(official_replacement_path, general_integer_break_path)`:

- Oficial: redução sem 1/≥5; substituições locais com contagens 674/2;
  decomposição da soma e produto final. Crédito parcial permanece por etapa.
- Geral: certificado de substituições, regra explícita e exaustiva para os três
  resíduos de s=3q+r, identificação `2026=3*675+1` e aplicação ao produto.
  Não exige os campos oficiais `threes_count`, `twos_count` nem a decomposição
  literal `3*674+2+2`. As fórmulas da regra geral são verificadas canonicamente:
  r=0→(zero 2, q três), r=1→(dois 2, q−1 três), r=2→(um 2, q três).

A regra geral isolada ou a frase “usar 3 é melhor” não substitui sua justificativa.
Os dois caminhos completos dão 6/6, sem somar créditos entre métodos.
O resultado final isolado não fabrica C1/C2 ou a decomposição de C3.

Identidades verdadeiras sem a construção exigida não fornecem a prova: `4=4`,
`6=6`, `4=4*1` e comparações não estritas não substituem os passos locais.
Além disso, `2>1` não é promovida ao argumento universal `m+1>m`: são conferidos
os dois membros da relação, evitando que a normalização de verdades apague o
escopo da afirmação.

## D — formas ótimas, unicidade e quantidades

A forma normal tem exatamente um par de 2. É possível manter esse par ou fundi-lo
em um único 4; não há outro par a fundir. O modelo determinístico identifica
as duas formas ótimas. D1/D2 exigem as listas fornecidas pelo estudante.

D3 exige as duas formas, as igualdades de soma/produto e a conclusão explícita
`only_forms: merge_two_twos`. Essa conclusão isolada não pontua. O argumento
parte da forma normal ótima do problema; sua correção global permanece no
verificador determinístico, sem alegação de prova formal de unicidade.

D4 verifica as quantidades 676 e 675 e uma comparação estrita correta.
Identifica-se quando o aluno faz a aritmética escrita `674+2=676` e `674+1=675`,
permitindo submetê-la a Lean. Uma igualdade aritmética verdadeira com uma
quantidade absoluta errada não é promovida a prova da quantidade correta.

## Carry-forward C→D

Foi usada exclusivamente a estratégia existente, em um `max_of` para o ponto
D4. A referência anterior é `c.threes_count`, que deve estar **refutada**.

Entrada condicional explícita de exemplo:

```text
[c]
threes_count: 673
[d]
cf_adopt_threes: 673
cf_dependency: sizes_from_adopted_threes
cf_size_twos: 673+2=675
cf_size_four: 673+1=674
cf_different_sizes: 675>674
```

A adoção aponta ao `record_id` exato do erro anterior. Adoção, dependência e
coerência recebem o mesmo `ConditionalContext`, com a regra `d.sizes_cf` e a
mesma referência adotada. Essa referência precisa aparecer nas evidências do
resultado anterior e da adoção, como já exige o engine.

O exemplo recebe somente o ponto condicional D4. A contagem anterior continua
refutada; não se declaram corretas as quantidades absolutas ou as listas ótimas
com 673 três. A conferência da coerência exige soma escrita usando o valor
adotado, os incrementos 2/1, resultados corretos e comparação correta.

Há seis controles: válido; aritmética condicional errada; adoção ausente;
valor/referência incompatível; dependência ausente; resultado anterior não
refutado. Somente o válido aplica carry-forward. Um teste adicional modifica
apenas a referência do contexto no limite do engine e confirma a recusa.
Não existe heurística para inferir adoção de uma resposta anterior.

## Proposições realmente verificadas em Lean

As 18 verificações selecionadas reutilizam o ciclo formal nativo com números
inteiros e source binding estrito. Os certificados contêm exatamente as
proposições escritas ou sua quantificação contextual declarada:

- Produto `2*3*3*3=54`.
- `∀n:ℤ, 3+(n-3)=n`.
- `∀n:ℤ, n≥5 → 3*(n-3)>n`.
- `4=2+2` e `4=2*2`.
- `2+2+2=3+3` e `2*2*2<3*3`.
- `2026=3*674+2+2`.
- `674+2=676` e `674+1=675`.

Alguns lemas aparecem em mais de um item. As quatro refutações reais são:

- `∀n:ℤ, n≥5 → 3*(n-3)<n` (contraexemplo n=5).
- `2*2*2>3*3`.
- `2026=3*673+4`.
- `674+2=675`.

Cada refutação decorre de compilação da negação; uma falha de compilação não é
tratada como falsidade. Testes simulam falhas técnicas e objetivos não resolvidos,
confirmando `technical_error`/`unverified` e ausência de crédito formal.

**Não estão formalizados em Lean:** maximalidade global para 11 ou 2026,
completude das partições, teorema geral de integer break, exaustividade das duas
formas ótimas ou equivalência de produtos com expoente 674 como um teorema Lean.
Essas partes são determinísticas/canônicas e exigem os argumentos estudantis
especificados na pauta. Não se afirma que “P5 está formalizado em Lean”.

## Grounding e explicabilidade

Registros mantêm texto literal, offsets no documento DIGITAL composto, hash,
canonical form, origem e papel semântico. Contextos negados, provisórios,
rejeitados ou citados não produzem crédito positivo. Antes de verificar, o
checker reextrai os itens e recusa qualquer mutação de texto, roteamento ou
anotação canônica.

A prova nativa vincula assertion/payload e domínio inteiro; a ponte confere
fingerprints, links de verificação e igualdade com o resultado formal original.
A execução pelo projetor legado continua vedada a esses registros nativos.

O trace distingue:

- `student_asserted`: IDs de afirmações efetivamente fornecidas;
- `student_argument_refs`: passos fornecidos que sustentam uma conclusão;
- `engine_derived`: consequências verificadas desses passos, sem novo trecho
  ou MathClaimRecord falsamente atribuído ao estudante;
- `student_lean`: proposição compilada, domínio e contexto registrados;
- mecanismos determinístico/canônico: identificados como tais, inclusive para
  a maximalidade global e produtos fatorados.

O caminho auditável permanece:

`item → regra/caminho → obrigação → FactResult → MathClaimRecord/evidência
→ verification_source/certificado → pontos decididos pelo PautaEngine`.

## Limitações e riscos residuais

- A entrada DIGITAL é estruturada. Soluções em prosa ou com gramática diferente
  podem ficar inconclusivas mesmo sendo matematicamente corretas.
- A enumeração aceita uma tabela completa de partições; não há reconhecimento
  geral de tabelas pedagógicas abreviadas. O caminho estrutural é uma alternativa
  completa, evitando exigir exclusivamente uma tabela específica.
- A regra geral aceita um certificado explícito de substituições e resíduos,
  não qualquer prova abstrata de integer break. Argumentos diferentes precisam
  de um producer verificável antes de autorizar crédito.
- A maximalidade global apoia-se no argumento matemático determinístico descrito,
  não num teorema monolítico compilado. Os testes por enumeração de somas pequenas
  são regressão independente, não substituto de formalização global.
- O reconhecimento de hipóteses formais é limitado ao contrato explícito;
  hipóteses equivalentes que exigiriam raciocínio inteiro adicional podem não
  ser reconhecidas pela canonicalização real compartilhada.
- Carry-forward depende de uma única referência anterior inequívoca, adoção e
  dependência explicitamente fornecidas. Ambiguidades são recusadas.
- As comparações idênticas de P1/P3/P4 são dos 83 outputs controlados completos
  sem Lean, evitando diferenças de UUID e caminhos. Não representam acurácia
  geral em redações ou benchmarks externos.

## Validação final

- **52/52 casos**, **58/58 obrigações atômicas** exercitadas positivamente.
- **463 testes direcionados** passaram, incluindo **130 novos de P5**.
- **703 testes de regressão compartilhada/ITA** passaram, incluindo auditoria offline real de F2Q3.
- Total executado: **1166 passed**, zero falhas e zero xfail nessas suítes. Não é contagem da suíte inteira do repositório.
- Lean real: **18 verificações**, sendo **14 positivas e 4 refutações**; zero falhas técnicas ou provas inconclusivas.
- P1/P3/P4: **20/25/38 outputs completos**, respectivamente, **idênticos byte a byte** à linha de base. Nenhum snapshot esperado foi atualizado para acomodar diferenças.
- Carry-forward: **6/6 controles** passaram; somente o caso válido recebe o ponto condicional.
- Rechecagem do código final: todos os 52 pontos, status de obrigações e caminhos coincidem com o replay formal selecionado.
- Zero regressões observadas nas suítes e casos executados. Não houve correção de falhas conhecidas de UI/HMER/secondary.
- Todos os arquivos existentes fora das sete alterações compartilhadas deliberadas conservaram seus hashes, incluindo o trabalho anterior não commitado de P4.
- `git diff --check`: OK; índice vazio e HEAD preservado.

Comandos:

```sh
.venv/bin/python -m pytest -q tests/test_pauta_engine.py tests/test_tme2_p1_pauta_bridge.py tests/test_tme2_p3_pauta_bridge.py tests/test_tme2_p4_pauta_bridge.py tests/test_tme2_p5_pauta_bridge.py
.venv/bin/python -m pytest -q tests/test_claim_fidelity.py tests/test_math_canonical.py tests/test_common_math_claims.py tests/test_audit_math_canonicalization.py tests/test_math_canonical_pipeline.py tests/test_rubric_bridge.py tests/test_positive_credit_evidence.py tests/test_student_proof_semantics.py tests/test_score_policy.py tests/test_score_policy_api.py tests/test_generic_student_math.py tests/test_claim_alignment_obligations.py
.venv/bin/python scripts/evaluation/run_tme_pauta_cases.py --problem TME2026P5 --output artifacts/evaluations/tme2_p5_pauta_bridge/replay_lean --lean-cases a_complete,b_complete,b_false_inequality,c_complete,c_wrong_gain,c_wrong_decomposition,d_complete,d_wrong_arithmetic
```

A revisão adversarial acrescentou proteção para escopo de desigualdades gerais e permitiu reagrupamentos genuínos do produto, como `6*9=54`, sem aceitar `54=54` ou `54*1=54` como cálculo. Os 52 casos controlados e suas proposições Lean não mudaram; a última suíte e a rechecagem são do código final.

### Contagens de evidência

Cada ocorrência de fato conta uma vez por caso; não se trata de estimativa de acurácia geral.

| Mecanismo | Ocorrências |
|---|---:|
| deterministic | 80 |
| student_lean | 18 |
| canonical_equivalence | 170 |

| Resultado de fato | Ocorrências |
|---|---:|
| verified | 234 |
| unverified | 13 |
| refuted | 21 |

| Status de obrigação no item avaliado | Ocorrências |
|---|---:|
| supported | 233 |
| indeterminate | 532 |
| refuted | 16 |

Os fatos do contexto C nos testes de carry-forward integram a contagem de fatos, mas não a contagem de obrigações restrita ao item D avaliado.

### Casos controlados

| Caso | Item | Pontos | Resultado |
|---|---|---:|---|
| a_complete | a | 6 | PASS |
| a_list_only | a | 2 | PASS |
| a_product_only | a | 1 | PASS |
| a_bare_54 | a | 0 | PASS |
| a_no_argument | a | 3 | PASS |
| a_reordered | a | 6 | PASS |
| a_additive_list | a | 6 | PASS |
| a_enumeration | a | 3 | PASS |
| a_structural | a | 6 | PASS |
| a_rejected | a | 0 | PASS |
| a_wrong_list | a | 4 | PASS |
| a_engine_max_alone | a | 0 | PASS |
| a_incomplete_enum | a | 3 | PASS |
| a_false_product | a | 2 | PASS |
| b_complete | b | 4 | PASS |
| b_sum_only | b | 1 | PASS |
| b_comparison_only | b | 1 | PASS |
| b_inequality | b | 2 | PASS |
| b_false_inequality | b | 0 | PASS |
| b_missing_domain | b | 2 | PASS |
| b_wrong_sign | b | 2 | PASS |
| b_difference | b | 4 | PASS |
| b_tautology | b | 0 | PASS |
| c_complete | c | 6 | PASS |
| c_general | c | 6 | PASS |
| c_final_only | c | 0 | PASS |
| c_reduction | c | 2 | PASS |
| c_substitution_only | c | 0 | PASS |
| c_counts_only | c | 0 | PASS |
| c_wrong_count | c | 4 | PASS |
| c_wrong_exponent | c | 4 | PASS |
| c_equivalent_product | c | 6 | PASS |
| c_wrong_gain | c | 0 | PASS |
| c_wrong_decomposition | c | 0 | PASS |
| c_general_keyword | c | 0 | PASS |
| c_general_incomplete | c | 0 | PASS |
| d_complete | d | 4 | PASS |
| d_one_list | d | 1 | PASS |
| d_no_uniqueness | d | 3 | PASS |
| d_uniqueness | d | 3 | PASS |
| d_counts_only | d | 1 | PASS |
| d_wrong_arithmetic | d | 0 | PASS |
| d_wrong_counts | d | 3 | PASS |
| d_multiplicity_order | d | 4 | PASS |
| d_product_not_list | d | 0 | PASS |
| d_only_keyword | d | 0 | PASS |
| d_cf_valid | d | 1 | PASS |
| d_cf_bad_arithmetic | d | 0 | PASS |
| d_cf_missing_adoption | d | 0 | PASS |
| d_cf_wrong_binding | d | 0 | PASS |
| d_cf_missing_dependency | d | 0 | PASS |
| d_cf_no_prior_error | d | 0 | PASS |

### Carry-forward

| Caso | Aplicado | Pontos D | Resultado anterior |
|---|---|---:|---|
| d_cf_valid | True | 1 | refuted |
| d_cf_bad_arithmetic | False | 0 | refuted |
| d_cf_missing_adoption | False | 0 | refuted |
| d_cf_wrong_binding | False | 0 | refuted |
| d_cf_missing_dependency | False | 0 | refuted |
| d_cf_no_prior_error | False | 0 | supported |

### Arquivos incrementais de P5

Adicionados:

- `app/confia_lean_auditor/core/math_canonical/development.py`
- `app/confia_lean_auditor/core/math_canonical/integer_structures.py`
- `app/confia_lean_auditor/lean/student_claim_checkers/tme2_p5.py`
- `app/confia_lean_auditor/rubric/pauta/tme2_p5.py`
- `app/confia_lean_auditor/student_claims/tme2_p5_digital.py`
- `app/confia_lean_auditor/tme/p5_integer_break.py`
- `docs/audits/TME2_P5_PAUTA_BRIDGE.md`
- `examples/pautas/tme2_problem5.v1.json`
- `tests/fixtures/tme2_p5_digital/cases.json`
- `tests/test_tme2_p5_pauta_bridge.py`

Modificados sobre o estado já contendo P4:

- `app/confia_lean_auditor/lean/student_claim_checkers/real_algebra.py`
- `app/confia_lean_auditor/lean/student_claim_checkers/tme2_p4.py`
- `app/confia_lean_auditor/student_claims/named_math.py`
- `app/confia_lean_auditor/tme/registry.py`
- `scripts/evaluation/run_tme_pauta_cases.py`
- `tests/test_tme2_p3_pauta_bridge.py`
- `tests/test_tme2_p4_pauta_bridge.py`

As alterações nos testes existentes de P3/P4 apenas atualizam o conjunto do registry e trocam o ID não suportado P5 por P2. As asserções matemáticas anteriores não foram relaxadas. O checker P4 apenas importa a função comum extraída; seus outputs permaneceram idênticos.

### Artefatos

Diretório: `artifacts/evaluations/tme2_p5_pauta_bridge/`.

- `validation_summary.json`: estado final e hashes.
- `replay_lean/replay_summary.json` e 52 bundles: decisões, fontes, caminhos e certificados formais locais.
- `final_semantic_recheck.json`: verificação dos 52 casos no código final.
- `carry_forward_summary.json`: seis controles condicionais.
- `p1_p3_p4_regression.json`, `*_before.json`, `*_after.json`: comparação completa dos 83 casos anteriores.
- `targeted_tests.log`, `regression_tests.log`: resultados das suítes.
- `baseline.json`, `preexisting.diff`, `baseline_sources/`: estado anterior preservado.
- `implementation.diff`: somente as mudanças incrementais de P5, sem misturar a implementação prévia de P4.
- `git_diff_check.txt`, `git_status.txt`: estado Git final.

### Git final

O status geral ainda inclui o trabalho anterior de P4, que não foi revertido nem colocado em staging.

```text
 M app/confia_lean_auditor/lean/student_proof.py
 M app/confia_lean_auditor/student_claims/named_math.py
 M app/confia_lean_auditor/tme/registry.py
 M scripts/evaluation/run_tme_pauta_cases.py
 M tests/test_tme2_p3_pauta_bridge.py
?? app/confia_lean_auditor/core/math_canonical/development.py
?? app/confia_lean_auditor/core/math_canonical/integer_structures.py
?? app/confia_lean_auditor/lean/student_claim_checkers/real_algebra.py
?? app/confia_lean_auditor/lean/student_claim_checkers/tme2_p4.py
?? app/confia_lean_auditor/lean/student_claim_checkers/tme2_p5.py
?? app/confia_lean_auditor/rubric/pauta/tme2_p4.py
?? app/confia_lean_auditor/rubric/pauta/tme2_p5.py
?? app/confia_lean_auditor/student_claims/tme2_p4_digital.py
?? app/confia_lean_auditor/student_claims/tme2_p5_digital.py
?? app/confia_lean_auditor/tme/p4_geometry.py
?? app/confia_lean_auditor/tme/p5_integer_break.py
?? docs/audits/TME2_P4_PAUTA_BRIDGE.md
?? docs/audits/TME2_P5_PAUTA_BRIDGE.md
?? examples/pautas/tme2_problem4.v1.json
?? examples/pautas/tme2_problem5.v1.json
?? tests/fixtures/tme2_p4_digital/
?? tests/fixtures/tme2_p5_digital/
?? tests/test_tme2_p4_pauta_bridge.py
?? tests/test_tme2_p5_pauta_bridge.py
```

Sem staging, commit ou push.
