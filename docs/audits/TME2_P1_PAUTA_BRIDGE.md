# Ponte de evidências — TME² Problema 1

## Inspeção inicial

Baseline: `629549f` (`feat/tme-dual-input`), working tree limpo.

`MathClaimRecord` já contém `record_id`, `problem_id`, `provenance`, `source`
(`SourceBinding`: texto literal, offsets, hash, grounding e atribuição),
`canonical_form`, papel semântico, payload legado e `VerificationLink`.
`StudentClaim` e `StudentClaimCheck` preservam payload, grounding e resultados
de prova/refutação. `RubricClaimContext` combina projeções, alinhamentos e gates
atuais; alinhamento e prova de referência não bastam para crédito do aluno.

A canonicalização existente oferece AST limitada e comparação afim exata.
Ela não interpreta prosa, listas finitas nem pares ordenados. A extração
genérica preserva spans e negação/contexto, mas não extrai `137` isolado.
O dispatcher de checkers conhece apenas questões ITA. O checker aritmético
existente aceita `arithmetic_equality` e pode ser reutilizado explicitamente
sem criar teoremas/estratégias novos para o piloto.

A ponte fica fora do PautaEngine e recebe resultados de verificação e
referências a `MathClaimRecord`, sem representação concorrente de claim. A
pauta-piloto e os pesos continuam responsáveis pela pontuação.

## Arquitetura implementada

Fluxo opt-in, restrito a `TME2_P1_PILOT`:

1. `collect_tme2_p1_digital({"a": texto, ...})` enquadra itens explicitamente
   identificados. Os offsets referem-se ao documento digital composto, com
   marcadores `[a]` a `[d]`; o conteúdo original de cada item não é reescrito.
2. A extração genérica existente produz `StudentClaim` e os adapters produzem
   `MathClaimRecord`. O produtor opt-in `digital_literals.py`, na mesma camada,
   acrescenta somente sintaxe completa de inteiros e coleções finitas de
   inteiros/pares. Usa o canal `native` já existente de `MathClaimRecord`.
   Não há reconhecimento de prosa, reticências, diagramas ou nova representação
   concorrente de claim. Fragmentos internos de uma coleção reconhecida não
   são contados novamente como claims independentes.
3. `verify_tme2_p1_digital`, na camada de student claim checkers, revalida a
   projeção/grounding antes de verificar fatos. Reutiliza a comparação afim
   exata de `math_canonical`. `expression_syntax` expõe as operações escritas
   usando o lexer e os limites existentes: o valor canônico de `731-137` é 594,
   mas é necessário conservar a subtração escrita para comprovar a montagem.
4. Igualdades aritméticas de inteiros, com `+`, `-` e `*`, são projetadas para
   `StudentClaim(arithmetic_equality)` e o checker Lean **já existente**.
   Cada chamada tem diretório exclusivo para não sobrescrever provas de outro
   caso. Frações não são convertidas em divisão inteira; seguem a comparação
   canônica conservadora. Não foram criados novos teoremas ou táticas Lean.
5. `bridge_tme2_p1` recebe somente `AuditorFactBundle`: registros originais e
   `FactResult` já verificados. Faz o mapa explícito de 21 fatos para IDs da
   pauta, valida referências/proveniência e produz `PautaEvidence`. Não recebe
   texto cru, interpreta matemática, executa extractor, Lean ou secondary.
6. `PautaEngine` recebe essa evidência estruturada e aplica a configuração
   existente. A única mudança nele é transportar os novos campos de
   rastreabilidade para as decisões. Regras, pesos e scoring ITA não mudaram.

`audit_tme2_p1_digital` é apenas a composição explícita dessas etapas. Não é
chamado pelo dispatcher ITA nem pelo `execute_audit` global.

### Contratos e rastreabilidade

- `FactResult` é um resultado de verificação, não um claim: contém ID do fato,
  IDs dos `MathClaimRecord`, fingerprints dos registros verificados,
  `VerificationLink`, mecanismo, eventual payload original de
  `StudentClaimCheck`, `conditional_on` e metadata.
- `AuditorFactBundle` conserva todos os registros, inclusive candidatos sem
  atribuição, hash do documento e resultados. Rejeita IDs duplicados,
  referências inexistentes e registros de outro problema.
- `PautaEvidence`/`ObligationEvidence` e suas decisões passam a conservar
  `source_claim_ids`, `verification_source`, `grounding_status` e `metadata`,
  além de `obligation_id`, status, referências e contexto condicional.
- Os campos adicionais são omitidos quando ausentes em payloads v1 antigos,
  preservando sua forma serializada e a entrada dos hashes legados.
- O resultado da ponte inclui o bundle original: raw span, offsets, hash,
  canonical form, semantic role e links de verificação permanecem disponíveis.
  Referências determinísticas `check:<hash>` identificam o resultado dentro do
  próprio bundle; referências Lean apontam para os arquivos de prova originais.
  Quando há mecanismos diferentes para uma obrigação, a origem agregada é
  determinística e cada mecanismo individual permanece na metadata.
- No caminho Lean ficam ambos os registros: a visão matemática canônica
  original e a projeção exata para o checker legado. A ponte exige mesmo
  `SourceBinding`, correspondência de ID/tipo/payload/grounding e sucesso real
  de prova ou de prova da negação no resultado upstream. Nenhum status Lean
  é inferido de uma equivalência canônica.
- Um resultado precisa aparecer também nos `verification_results` dos
  registros de origem. Alterar um registro depois da verificação invalida seu
  fingerprint. Esses hashes detectam alteração acidental; não são assinatura
  criptográfica nem tornam um cliente arbitrário uma fonte confiável de provas.

Os estados mantêm significados distintos: suporte, refutação, indeterminação e
erro técnico. Falta de claim produz `indeterminate`, sem evidência inventada;
erro técnico permanece `technical_error`. Resultados conflitantes ficam
indeterminados. Origem de referência, hipótese, tentativa rejeitada, citação,
fonte sem atribuição e mecanismos semantic/secondary não autorizam crédito.
O campo condicional é preservado e contextos conflitantes são rejeitados;
nenhuma relação de carry-forward é inferida neste piloto.

## Fatos por item

### a — montagem e aritmética

`a.inverted_number_137 → a.identifies_137`,
`a.subtraction_731_137 → a.constructs_subtraction`,
`a.result_594 → a.result_594`,
`a.single_arithmetic_error → a.arithmetic_error_only`.

A identificação literal de 137 é distinta do resultado literal 594. A montagem
exige uma subtração escrita com os operandos corretos, na ordem correta.
O diagnóstico de erro único exige exatamente uma operação binária, um resultado
inteiro literal incorreto, uma única afirmação matemática e ausência de prosa ou
outras afirmações fora desse span. Registra operandos, resultado calculado,
resultado escrito e contagens. Uma resposta final errada, montagem errada ou
erro posterior não satisfaz esse diagnóstico automaticamente.

### b — desenvolvimento algébrico

Os quatro IDs `b.*` são mapeados diretamente. A representação do invertido pode
ser uma expressão explícita ou definição não contraditória de um novo símbolo.
Reatribuir `a`, `b` ou `c` não é tratado como definir o invertido.
Subtração exige os dois números posicionais e sua ordem. Cancelamento exige
igualdade escrita válida a partir dessa subtração, com eliminação de `b`.
Fatoração exige passagem escrita de uma expansão para um produto equivalente
com o fator 99 extraído. Repetir uma fórmula já fatorada com `+0` ou multiplicar
a expansão por 1 não demonstra essa passagem.

São comparados os lados e a estrutura de operações, **não** a forma afim da
igualdade inteira: identidades verdadeiras diferentes podem reduzir a `0=0`,
o que não comprova o desenvolvimento solicitado. Reordenação de termos e
`-99(c-a)` são aceitos por equivalência exata. `99(a-c)` isolado não demonstra
nenhuma dessas passagens.

### c — domínio e coleção finita

Os oito IDs `c.*` são diretos. O produtor conserva a coleção observada, valores
esperados, omissões, valores extras, duplicatas e quantidade de valores corretos.
O esperado é enumerado como `{99*k | k=1,...,8}` a partir dos dígitos do problema.
A justificativa de domínio desta versão exige as condições escritas
`1<=c`, `a<=9`, `a>c` e a coleção explícita de `a-c`; usa a premissa do problema
de que os símbolos são algarismos inteiros. A lista sozinha não inventa essas
condições nem o uso da fórmula.

`complete_list` significa ausência de omissões; `no_extraneous_values`, ausência
de extras. A faixa completa exige ambos na pauta. `single_list_error` significa
exatamente uma omissão **ou** um extra. `some_correct` significa pelo menos um
valor correto; `several_correct`, pelo menos dois valores distintos corretos.
Esta definição operacional de “vários” é explícita e pode exigir decisão
editorial futura. `pattern_recognized` exige também a fórmula escrita e sua
ligação à lista; a quantidade de números, sozinha, não inventa um padrão.
Duplicatas não aumentam a quantidade de resultados distintos.

Listas com variável precisam de vínculo à variável definida pela fórmula;
coleção sem rótulo é aceita como lista de resultados somente no item c.
O produtor não contém os pesos 4/3/2/1: fornece predicados e estatísticas, e a
pauta seleciona uma única faixa.

### d — equação, pares e contagem

Os cinco IDs `d.*` são diretos. A equação com 594 e a diferença 6 são passos
escritos separados: não se inventa um deles a partir do outro. A comparação
canônica confirma correspondência com as obrigações sob o contexto do problema,
não um teorema universal sobre quaisquer valores reais de `a,c`.

Os pares são enumerados no domínio `1<=a,c<=9` com diferença 6 e comparados à
coleção ordenada por `(a,c)`. As escolhas de `b` exigem a coleção explícita de
0 a 9. O total exige os pares, as escolhas e a multiplicação escrita de suas
cardinalidades. `30` isolado não comprova contagem. A igualdade de contagem pode
ser formalmente verificada pelo checker aritmético existente; as referências
dos claims das cardinalidades são mantidas na metadata.

## Replay digital controlado

Fixture versionada: `tests/fixtures/tme2_p1_digital/cases.json`.
Execução final: `artifacts/evaluations/tme2_p1_pauta_bridge_20261031_validated/`.
Cada JSON por caso contém a entrada, bundle, PautaEvidence, decisões, faixas,
obrigações satisfeitas/refutadas/indeterminadas e referências de crédito.
`validation_summary.json` reúne os resultados. Não é estimativa de acurácia de
um dataset nem execução dos Problemas 2–5.

| Caso | Pontos do item | Faixa da lista, quando aplicável |
|---|---:|---:|
| a: completo | 3/3 | — |
| a: erro único `731-137=584` | 2/3 | — |
| a: somente 137 | 1/3 | — |
| a: somente 594 | 0/3 | — |
| a: sem evidência | 0/3 | — |
| a: montagem errada | 0/3 | — |
| b: demonstração completa | 5/5 | — |
| b: invertido, subtração e cancelamento, sem fatoração | 4/5 | — |
| b: somente `99(a-c)` | 0/5 | — |
| b: forma algébrica equivalente | 5/5 | — |
| c: fórmula, domínio justificado e lista completa | 6/6 | 4 |
| c: fórmula e uma omissão | 4/6 | 3 |
| c: lista com um extra | 3/6 | 3 |
| c: vários resultados com padrão | 3/6 | 2 |
| c: poucos resultados | 1/6 | 1 |
| c: sem evidência | 0/6 | 0 |
| d: completo | 6/6 | — |
| d: equação, diferença e pares, sem contagem | 4/6 | — |
| d: equação e diferença corretas, erro posterior | 2/6 | — |
| d: somente diferença 6, pares errados e 30 isolado | 0/6 | — |

Resultado: **20/20** casos com pontuação/faixa esperadas e **21/21** obrigações
com pelo menos um suporte observado no conjunto. O teste composto dos quatro
itens completos obtém 20/20 sem revisão pendente. Casos incompletos preservam
o intervalo e `needs_review` segundo a política `withhold` já existente.

Três verificações Lean reais no replay final: prova de `731-137=594`, prova da
negação de `731-137=584`, prova de `3*10=30`. Assim, duas obrigações distintas
(`a.result_594`, `d.total_thirty`) têm cobertura formal real. As demais usam
checagem determinística de sintaxe/domínio/coleções ou equivalência afim exata.
As provas e saídas originais estão referenciadas nos JSONs; mocks dos testes
unitários de contrato não são contabilizados como cobertura formal real.

Reprodução (somente local, sem API):

```sh
.venv/bin/python -m scripts.evaluation.run_tme2_p1_pauta_pilot \
  --output artifacts/evaluations/tme2_p1_pauta_bridge_nova_execucao --with-lean
```

O diretório de saída deve ser novo. Sem `--with-lean`, o runner registra
explicitamente `deterministic_only`, sem afirmar que houve prova formal.

## Limitações e riscos residuais

- Cobertura de 21 obrigações é cobertura desta linguagem digital controlada,
  não compreensão geral de respostas naturais. Prosa equivalente, listas com
  reticências, contagens verbais e justificativas alternativas ainda podem
  permanecer indeterminadas. Não há chamada semântica/secondary de fallback.
- A camada de sintaxe é deliberadamente opt-in. Não altera a interpretação
  genérica dos datasets ITA nem promete suporte HMER.
- O diagnóstico de erro aritmético único é restrito à afirmação completa
  analisável; não tenta certificar todas as possíveis justificativas em prosa.
- Identidades são verificadas apenas no domínio suportado pelo canonicalizador
  existente. Comparação desconhecida não é refutação. Não há novo CAS.
- A detecção de contradições não é um solucionador lógico geral. Resultados
  conflitantes para o mesmo fato e definições contraditórias observadas são
  conservadores, mas textos arbitrários podem demandar interpretação futura.
- O bundle é contrato interno de resultados confiáveis. Receber JSON forjado
  com hashes e flags coerentes não substitui executar verificadores confiáveis.
- A nota é sugestão ConfIA; não escreve nem substitui decisão do avaliador.
  A pauta e a escolha editorial das faixas continuam independentes da ponte.

## Arquivos alterados

Modificados: `rubric/pauta/models.py` (campos de trace compatíveis) e
`rubric/pauta/engine.py` (propagação desses campos), sob
`app/confia_lean_auditor/`.

Novos, sob a mesma raiz: `core/math_canonical/syntax.py`,
`student_claims/digital_literals.py`, `student_claims/tme2_p1_digital.py`,
`lean/student_claim_checkers/tme2_p1.py`, `rubric/pauta/bridge.py` e
`rubric/pauta/tme2_p1.py`.

Também novos: `tests/test_tme2_p1_pauta_bridge.py`,
`tests/fixtures/tme2_p1_digital/cases.json`,
`scripts/evaluation/run_tme2_p1_pauta_pilot.py` e este relatório.

Nenhuma alteração na pauta JSON, catálogo ITA, scoring ITA, secondary, HMER,
UI, registry global ou `execute_audit`. Sem staging, commit ou push.

## Validação

PautaEngine + bridge + extração genérica + alignment: **315 passed**.
Inclui 74 testes novos da bridge, 100 existentes do PautaEngine e 141 testes
existentes das camadas de extração/alignment. Os novos testes cobrem os 20 casos,
atribuição, negação, hipótese, citação, rejeição, tautologia, coleções adversariais,
fração geral, fonte alterada, conflito, isolamento entre itens, origem de
referência, mecanismos não habilitados e vinculação exata do resultado formal.

Comando:

```sh
.venv/bin/python -m pytest -q tests/test_pauta_engine.py \
  tests/test_tme2_p1_pauta_bridge.py tests/test_generic_student_math.py \
  tests/test_generic_student_math_pipeline.py tests/test_claim_alignment_obligations.py
```

A suíte legada de grounding/canonicalização/MathClaimRecord/rubric bridge/
scoring/checkers ITA terminou com **595 passed em 1221,21 s (20:21)**. Inclui
integrações reais locais, provas e refutações dos checkers F2Q1/F2Q3/F2Q5/F2Q6/F2Q8.
As duas seleções não se sobrepõem: **910 testes distintos passaram**, incluindo
74 novos, sem falhas ou xfails nas seleções executadas. Os 20 casos do replay
são registrados separadamente, sem inflar esse total de testes pytest.

Comando da suíte legada relevante (sem rede; os testes desabilitam a chave de API
e as integrações formais usam Lean local):

```sh
.venv/bin/python -m pytest -q \
  tests/test_claim_fidelity.py tests/test_math_canonical.py \
  tests/test_common_math_claims.py tests/test_common_claim_pipeline.py \
  tests/test_audit_math_canonicalization.py tests/test_math_canonical_pipeline.py \
  tests/test_rubric_bridge.py tests/test_rubric_bridge_pipeline.py \
  tests/test_positive_credit_evidence.py tests/test_student_proof_semantics.py \
  tests/test_score_policy.py tests/test_score_policy_api.py \
  tests/test_f2q1_student_claim_checks.py tests/test_f2q3_student_claim_checks.py \
  tests/test_f2q5_student_claim_checks.py tests/test_f2q6_student_claim_checks.py \
  tests/test_f2q8_student_claim_checks.py
```

O escopo de validação não inclui a suíte completa de UI/HMER. Nenhum teste
existente foi editado, enfraquecido ou removido.

Regressões observadas: nenhuma nas seleções executadas. A confirmação de
compatibilidade ITA combina esses testes com ausência de alterações em seus
extractors, checkers, configuração, rubricas e política de pontuação.

## Estado final do repositório

`git diff --check`: **OK**. Verificação adicional de whitespace dos arquivos
novos: **OK**. Index sem alterações; HEAD permanece `629549f` e branch
`feat/tme-dual-input`. Não houve staging, commit ou push.

`git status --short` ao concluir (o diretório de artifacts continua ignorado):

```text
 M app/confia_lean_auditor/rubric/pauta/engine.py
 M app/confia_lean_auditor/rubric/pauta/models.py
?? app/confia_lean_auditor/core/math_canonical/syntax.py
?? app/confia_lean_auditor/lean/student_claim_checkers/tme2_p1.py
?? app/confia_lean_auditor/rubric/pauta/bridge.py
?? app/confia_lean_auditor/rubric/pauta/tme2_p1.py
?? app/confia_lean_auditor/student_claims/digital_literals.py
?? app/confia_lean_auditor/student_claims/tme2_p1_digital.py
?? docs/audits/TME2_P1_PAUTA_BRIDGE.md
?? scripts/evaluation/run_tme2_p1_pauta_pilot.py
?? tests/fixtures/tme2_p1_digital/
?? tests/test_tme2_p1_pauta_bridge.py
```

O resumo JSON final conserva hashes da implementação validada, identificação
do commit-base, resultados do replay e resultados das duas seleções de testes.
