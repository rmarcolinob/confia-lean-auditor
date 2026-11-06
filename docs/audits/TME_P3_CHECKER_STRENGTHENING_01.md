# TME P3 — Checker Strengthening 01

Data: 2026-11-05. Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3`. Branch: `experiment/tme-semantic-formal-p3`. HEAD preservado: `1165dbf62f854d6d40c0cc5f2bb6fcb02ca381e9`.

**Veredito: CHECKER_COVERAGE_COMPLETE.** Foram fortalecidos exclusivamente `b.ordered_pairs`, `b.different_favorable` e `b.second_white_probability`, em módulo experimental de uso explícito. A matriz final contém 13/13 obrigações com checker forte no contrato digital tipado: 4 DETERMINISTIC_STRONG, 9 COMPOSITE_STRONG, 0 CHECKER_GAP. Não foi implementado SemanticExtractor P3 nem alterado o TME_CURRENT.

## 1. Origem e reconstrução dos três gaps

Fonte: [diagnóstico preservado](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_CHECKER_FIRST_DIAGNOSTICO_01.md), especialmente seções 5 e 9. A lista de gaps implementados é exatamente G1–G3; não foram promovidas as demais limitações de representação a novos gaps desta tarefa.

| Rubric rule → obrigação | Evidence/fact e produtor anterior | Verificação anterior | Insuficiência |
| --- | --- | --- | --- |
| b.space, all_of, 2 → b.ordered_pairs | `pares_ordenados` → MathClaimRecord → `_b` → `P3Checks.observe` → FactResult de mesmo ID | `value_status` contra cardinalidade de `machine.ordered_pairs()`; metadado uniform_ordered_pairs=True | 36 ou 36=36 já era verified. O motor conhecia o espaço, mas a resposta não precisava escrever a relação de duas escolhas. |
| b.different, all_of, 2 → b.different_favorable | `favoraveis_distintos` → `_b` → `P3Checks.observe` | Valor contra o tamanho do subconjunto de `second_white_pairs()` com i≠j | 10 ou 10=10 já era verified. A enumeração do sistema não demonstra que o aluno apresentou a contagem 2×5. |
| b.conclusion, all_of, 2 → b.second_white_probability | `segunda_branca`, `arvore_total` ou matemática isolada → `_b` → `P3Checks.numerical` | Equivalência racional contra número de favoráveis/36; Lean para igualdade elegível | Valor final e argumento não eram distinguidos. Total verdadeiro em árvore incompleta ou falsa podia manter os 2 pontos da conclusão. |

Referências de implementação: [produtores antigos](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/lean/student_claim_checkers/tme2_p3.py:127), [aritmética antiga](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/lean/student_claim_checkers/tme2_p3.py:90) e [pauta operacional](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/examples/pautas/tme2_problem3.v1.json).

Esses produtores já verificavam valores verdadeiros. O problema era a suficiência para método/argumento e, em G3, a falta de separação explícita do crédito de resultado. Não havia necessidade de reconstruir a máquina por LLM ou criar novos pesos.

## 2. Implementação e fronteira do baseline

Novo entry point: [audit_p3_checker_first](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_p3_checker_first/engine.py:136). Não foi registrado no registry de produção. `StrongP3Checks` herda o produtor existente e especializa somente `observe` para os dois counts e `numerical` para a segunda probabilidade. `_a`, `_b`, `_c`, o collector, os verificadores Lean, FactResultsBuilder, bridge e PautaEngine são reutilizados sem edição.

O fluxo usa `supplement_scope(deterministic_only)` e não chama LLM. Reconstrói a extração com o collector existente, conserva os registros de fonte e fingerprints e submete os fatos à bridge existente. O composto mantém os componentes e o recibo aritmético original em metadata; a origem do fato composto é determinística, não uma afirmação de prova formal de toda a máquina. `ScoreClosurePolicy` existente mantém score numérico e sinalização de revisão/incerteza técnica.

Os outros dez IDs preservam seus produtores e critérios. Testes com as 25 fixtures comparam o baseline antes e depois da chamada experimental, incluindo dumps completos, e comparam os estados das dez obrigações não fortalecidas. Isso não afirma identidade byte a byte entre baseline e nova auditoria: os novos compostos têm fontes/recibos adicionais. A igualdade integral verificada é baseline antes/depois.

## 3. Modelo finito e certificado independente

Asset preservado: `examples/pautas/tme2_problem3.machine.v1.json`. Pilhas inferior→superior:

| Índice | Pilha |
| --- | --- |
| 1 | branca, preta, branca, cinza, preta |
| 2 | branca, cinza, preta |
| 3 | cinza, preta |
| 4 | preta, preta |
| 5 | cinza, preta |
| 6 | preta, branca, cinza, preta |

[finite_certificate](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_p3_checker_first/components.py:19) recebe `P3Machine` confiável e, para cada (i,j), copia as pilhas, retira a bola inferior de i, registra o estado, retira a inferior de j do estado atualizado e registra a segunda cor e o estado final. Não usa números extraídos do aluno para construir o certificado. A regra uniforme em cada acionamento é premissa do enunciado; a medida exata é 1/6×1/6=1/36.

Campos observáveis: origem e hash das pilhas; 36 eventos; primeira/segunda cor; estados após ambas as retiradas; probabilidade por evento; massa total; pares distintos e repetidos; favoráveis; agrupamento dos distintos pelo segundo compartimento; condicionais por primeira escolha; contagens e probabilidade final.

| Derivação do certificado | Resultado |
| --- | --- |
| Espaço de pares | 36, cada um com peso 1/36; massa total 1 |
| Pares com i≠j / diagonal | 30 / 6 |
| Segunda branca e i≠j | (1,2), (2,1), (3,1), (3,2), (4,1), (4,2), (5,1), (5,2), (6,1), (6,2) |
| Agrupamento dos favoráveis distintos | j=1 e j=2; cinco primeiras escolhas em cada grupo |
| Segunda branca e i=j | Somente (6,6) |
| União favorável disjunta | 10+1=11 eventos |
| Probabilidade da segunda branca | 11/36 |
| Condicionais dadas primeiras escolhas 1..6 | 1/6, 1/6, 1/3, 1/3, 1/3, 1/2 |

Os números 10, 1 e 11 são saídas da enumeração. Controles sintéticos alteram apenas máquinas em memória: retirar a branca da segunda posição do sexto elimina o favorável diagonal e muda a probabilidade para 5/18; retirar uma branca inicial muda os favoráveis distintos para 5 e o fator esperado para 1×5. O asset oficial e as fixtures não foram alterados.

`check_event_set(kind,pairs,machine)` também deriva seu próprio certificado: rejeita subconjunto errado mesmo com cardinalidade correta, duplicatas, casos trocados e certificado fabricado pelo chamador. Payload/índice inválido é ERROR, não refutação do conteúdo matemático. Essa função é um checker matemático de baixo nível, sem scoring ou atribuição automática; a notação textual existente ainda não extrai listas de pares. Não foi acrescentado extractor disfarçado.

## 4. Componentes e suficiência dos três compostos

| Obrigação | Componentes exigidos | Exemplos aceitos / não suficientes |
| --- | --- | --- |
| b.ordered_pairs | Valor/igualdade exata + certificado finito + relação escrita de duas escolhas de seis | `6*6=36`, `6^2=36`, `36=6*6` e produto sem igualdade; 36, 36=36 e 12*3=36 ficam INCOMPLETE |
| b.different_favorable | Valor/igualdade exata + certificado finito + relação escrita entre brancas iniciais e primeiras escolhas distintas | `2*5=10`, `5*2=10`, `2*(6-1)=10`; 10, 10=10 e 4+6=10 ficam INCOMPLETE |
| b.second_white_probability, desenvolvimento | Aritmética preservada + certificado + consistência de contexto + partição escrita ou seis ramos e pesos | `(10+1)/36=11/36`, `10/36+1/36=11/36`; partição (9+2) é falsa apesar do total correto; desenvolvimento não reconhecido não cai na rota de valor |
| b.second_white_probability, resultado | Aritmética/valor exato + certificado + consistência + contrato explícito de b.conclusion | `11/36`, equivalente `22/72` ou igualdade só entre valores. Somente 2 pontos; `result_credit_only=true`, `argument_satisfied=false` |

A validação de relação é limitada e tipada: a quantidade vincula o objeto e a árvore sintática identifica os fatores/partição. Não se infere uma explicação em prosa a partir de qualquer conta igual a 36 ou 10. Uniformidade vem da regra confiável do problema, não do número apresentado pelo estudante.

### Por que preservar 11/36 isolado

O diagnóstico registrou divergência entre a formulação pedagógica de reunir casos e o contrato operacional. O JSON descreve a conclusão e usa all_of somente de `b.second_white_probability`; `b_answer_only` tem expectativa histórica de 2. A solicitação atual autoriza manter parcela isolada prevista na pauta **ou contrato operacional**. A solução preserva esses 2 pontos em rota separada, sem dizer que um valor demonstra o método e sem criar parcela adicional. G1/G2 continuam exigindo argumento; valor correto não preenche as demais etapas.

Uma afirmação desenvolvida que falha na estrutura não pode se reclassificar automaticamente como resposta isolada. `arvore_total` sempre vai à rota de árvore; faltam ramos → INCOMPLETE; ramo falso → FAILED. `(12-1)/36=11/36` permanece INCOMPLETE por representação não reconhecida, e não refuted. Uma igualdade realmente provada só estabelece a aritmética escrita.

## 5. Conflitos, falsidade e erros

| Situação | Resultado observável | Crédito |
| --- | --- | --- |
| Todos os componentes aplicáveis verificados | COMPOSITE_VERIFIED / verified | Pode ser aceito pela bridge e pauta |
| Valor/partição/ramos matematicamente falsos | COMPOSITE_FAILED / refuted | Retido para essa obrigação |
| Relação ausente ou representação não suportada | COMPOSITE_INCOMPLETE / unverified | Retido; não é refutação |
| Falha de geração/consistência do certificado | COMPOSITE_ERROR / technical_error | Retido com incerteza técnica |
| Contagem/repetição explicitamente falsa junto de total correto | source_consistency=CONFLICTING_EVIDENCE; conclusão INCOMPLETE e revisão | Não ignora o contexto falso |
| Evidências verdadeira e falsa do mesmo ID, em qualquer ordem | Conflito reconciliado pela bridge; evidência indeterminate | Não escolhe apenas a positiva |

O componente de consistência funciona somente como veto. Contagens corretas anteriores não preenchem uma relação ausente no total. A rota de valor não exige que os outros créditos estejam presentes, mas não pode ignorar suas contradições explícitas. O max_of histórico entre métodos completos de b continua valendo: não foi introduzida política global de zerar o item inteiro por qualquer erro local.

## 6. Testes novos e resultados negativos

[test_tme_p3_checker_first.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_checker_first.py): 90 testes, incluindo equivalências admitidas, números errados, caso trocado, relação não escrita, tautologias, subconjuntos errados/duplicados, índices inválidos, partição falsa com total verdadeiro, atribuição ao item errado, hipótese/negação/tentativa descartada, conflitos nas duas ordens, mutações controladas da máquina, falha técnica, 25 comparações de baseline e cobertura positiva dos 13 IDs.

[test_tme_p3_checker_first_lean.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_checker_first_lean.py): 8 integrações reais, sem mock de Lean. Cobrem igualdade verdadeira, refutação demonstrada, aritmética verdadeira com partição falsa, conflito entre valor verdadeiro e igualdade falsa em ambas as ordens, dois métodos completos históricos e ausência de dupla pontuação.

| Sondagem local, sem novo dataset | TME_CURRENT | Rota fortalecida | Motivo |
| --- | --- | --- | --- |
| Somente 36, 10, {6}, 11/36 rotulados | 8 | 4 | Só exclusividade da repetição e resultado final satisfazem seus contratos |
| 36=36 e 10=10 rotulados | 4 | 0 | Tautologia não estabelece contagem |
| 11/36 isolado | 2 | 2 | Resultado separado de justificativa |
| (9+2)/36=11/36 | 2 | 0 | Partição falsa, mesmo com igualdade verdadeira |
| favoraveis_distintos:12 + segunda_branca:11/36 | 2 | 0 | Conflito de contexto não descartado |

## 7. Lean real e estados epistêmicos

Verificado nesta execução:

```text
Lean (version 4.28.0, arm64-apple-darwin24.6.0,
commit 7e01a1bf5c70fc6167d49c345d3bf80596e9a79b, Release)
Mathlib revision: 8f9d9cff6bd728b17a24e163c9402775d9e6a365
```

Foi reutilizada a infraestrutura já preparada. A prova continua usando `import Mathlib`, domínio ℚ e `norm_num` no checker racional existente. Não foi adicionada formalização Lean da máquina nem alteração dos checkers Lean de produção.

| Status formal | Replay TME_CURRENT | Novos testes Lean |
| --- | --- | --- |
| FORMAL_VERIFIED | 12 | 5 |
| FORMAL_REFUTED | 2 | 3 |
| FORMAL_UNPROVED | 0 | 0 |
| FORMAL_ERROR | 0 | 0 |
| FORMAL_NOT_ATTEMPTED | 52 | 7 |

Unidade desta tabela: fatos emitidos nos casos executados (e componentes aritméticos dos fatos novos). NOT_ATTEMPTED inclui fatos determinísticos, não apenas probabilidades isoladas; não conta obrigações ausentes. Foram 14 checks Lean no replay e 8 nos novos testes. A soma de ocorrências não representa 22 proposições distintas. Receipts completos com caminhos `.lean`, stdout/stderr, proposição e resultado estão em `formal_receipts.json`.

Prova decisiva: `(((9 : ℚ)+(2 : ℚ))/(36 : ℚ))=((11 : ℚ)/(36 : ℚ))` compilou, mas o composto foi FAILED pela partição errada. Para `(10+1)/36=1/2`, a tentativa positiva não provou a igualdade e a negação compilou; `refutation_verified=true`. Refutação foi estabelecida por prova negativa, não inferida da falha da tentativa positiva. Nos casos verificados, `compiled=true` e stdout/stderr vazios. A ausência de igualdade em resultado puro produz NOT_ATTEMPTED, mantendo crédito determinístico quando autorizado.

Os cinco IDs com capacidade Lean histórica continuam disponíveis: a.first_white_probability, b.second_white_probability, c.conditional_success_1, c.conditional_success_2 e c.total_win_probability. Os novos count checkers são determinísticos: o domínio finito e a aritmética exata bastam; usar Lean apenas para 36=36 não fecharia o gap de argumento.

## 8. Regressões

| Seleção executada | Resultado |
| --- | --- |
| test_tme2_p3_pauta_bridge.py, 70 + test_pauta_engine.py, 100 + novos unitários, 90 | 260 PASS |
| Seleção TME2026P3 em semantic_claims, tme_hybrid_grader, scope_boundary | 6 PASS, 132 deselected |
| Novas integrações Lean reais | 8 PASS |
| Total pytest distinto | **274 PASS**, incluindo os **176 anteriores**; zero falha residual |
| Replay existente TME2026P3 | **25/25**, 13 IDs exercitados, 14 checks Lean locais |
| Rechecagem focal após corrigir nome de função no metadado do novo registry | 1 PASS, 89 deselected; já incluído nos 90, não somado novamente |

As expectativas históricas não foram editadas. A auditoria fortalecida dos mesmos 25 textos mantém 22 notas e altera somente as três seguintes; o replay do TME_CURRENT mantém 25/25:

| Fixture | Current | Fortalecido | Razão |
| --- | --- | --- | --- |
| b_wrong_favorable | 2 | 0 | O crédito restante antigo vinha de 36 isolado; a nova relação amostral não foi estabelecida |
| b_incomplete_tree | 2 | 0 | Total de árvore sem todos os ramos não migra para resultado isolado |
| b_wrong_branch | 2 | 0 | Total correto não neutraliza ramo falso |

`b_official`, `b_tree` e `b_both_methods` continuam 8; `b_missing_same` continua 6; `b_answer_only` continua 2. Os casos a/c mantêm todas as notas. O replay novo é diagnóstico da rota experimental, não alteração dos alvos históricos ou novo benchmark/gold. Os 25 casos já integram a suíte parametrizada; não são 25 novos textos independentes.

## 9. Comandos e artefatos

Comandos executados no worktree P3 (stdout/stderr combinados nos logs; strings integrais com redirecionamentos em `commands.json`):

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0
P3_PYTHON=/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python

"$P3_PYTHON" -m pytest tests/test_tme2_p3_pauta_bridge.py tests/test_pauta_engine.py \
  tests/test_tme_p3_checker_first.py -q -p no:cacheprovider \
  --basetemp=/private/tmp/p3-strengthening-01/regression \
  --junitxml=/private/tmp/p3-strengthening-01/regression.xml
"$P3_PYTHON" -m pytest tests/test_semantic_claims.py tests/test_tme_hybrid_grader.py \
  tests/test_scope_boundary.py -k TME2026P3 -q -p no:cacheprovider \
  --basetemp=/private/tmp/p3-strengthening-01/related \
  --junitxml=/private/tmp/p3-strengthening-01/related.xml
"$P3_PYTHON" -m pytest tests/test_tme_p3_checker_first_lean.py -q -s -p no:cacheprovider \
  --basetemp=/private/tmp/p3-strengthening-01/lean \
  --junitxml=/private/tmp/p3-strengthening-01/lean.xml
"$P3_PYTHON" -m scripts.evaluation.run_tme_pauta_cases --problem TME2026P3 \
  --output artifacts/evaluations/tme_p3_checker_strengthening_01/current_replay \
  --lean-cases a_complete,a_wrong_probability,b_official,b_tree,c_complete,c_wrong_total,c_conditional_equivalent,c_wrong_second,c_arithmetic_without_strategy,a_answer_only,b_answer_only,c_answer_only
"$P3_PYTHON" -m pytest tests/test_tme_p3_checker_first.py -k all_13_obligations \
  -q -p no:cacheprovider --basetemp=/private/tmp/p3-strengthening-01/registry-check
"$P3_PYTHON" /private/tmp/p3-strengthening-01/consolidate.py
lake env lean --version
git -C .lake/packages/mathlib rev-parse HEAD
git diff --check
git status --short
git rev-parse HEAD
git branch --show-current
```

Artefatos ignorados pelo Git: [tme_p3_checker_strengthening_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_checker_strengthening_01), incluindo logs/JUnit, comandos, recibos Lean, before_hashes, preservation.json, finite_certificate.json, coverage.json, sondagens e replays pareados. Os arquivos Lean efetivamente executados ficam em `artifacts/student_claim_checks`, nos caminhos registrados pelos receipts. O script de consolidação foi preservado como artefato de auditoria, não novo script de produção.

## 10. Arquivos e preservação

Foram criados somente:

- `app/confia_lean_auditor/experimental/tme_p3_checker_first/{__init__,components,engine,registry}.py`;
- `tests/test_tme_p3_checker_first.py` e `tests/test_tme_p3_checker_first_lean.py`;
- os relatórios `TME_P3_CHECKER_COVERAGE_02.md` e este documento;
- artefatos locais ignorados de execução/auditoria.

**790 arquivos preexistentes monitorados conservaram seus hashes**, incluindo o diagnóstico anterior, código, prompts, pauta, máquina, fixtures, datasets monitorados, toolchain e manifest. Caminhos de gold/holdout foram excluídos do conjunto monitorado e não lidos. Nenhuma expectativa histórica foi ajustada. Não houve acesso a gold/holdout, provider externo, piloto Semantic Formal, P4/P5, stage ou commit.

Estado final esperado/verificado após gravar estes relatórios:

```text
?? app/confia_lean_auditor/experimental/tme_p3_checker_first/
?? docs/audits/TME_P3_CHECKER_COVERAGE_02.md
?? docs/audits/TME_P3_CHECKER_FIRST_DIAGNOSTICO_01.md
?? docs/audits/TME_P3_CHECKER_STRENGTHENING_01.md
?? tests/test_tme_p3_checker_first.py
?? tests/test_tme_p3_checker_first_lean.py
HEAD: 1165dbf62f854d6d40c0cc5f2bb6fcb02ca381e9
branch: experiment/tme-semantic-formal-p3
```

`TME_P3_CHECKER_FIRST_DIAGNOSTICO_01.md` já estava untracked no início e foi preservado. Nenhum arquivo rastreado foi modificado.

## 11. Limites e veredito

A matriz completa está em [TME_P3_CHECKER_COVERAGE_02.md](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_CHECKER_COVERAGE_02.md). O alcance é o contrato digital existente, com relações matemáticas limitadas e verificáveis. Expressões não reconhecidas não recebem crédito automático. Árvores visuais, prosa livre e schema de estados escritos pelo aluno não foram implementados.

Os limites G4–G7 do diagnóstico permanecem: o antigo b.alternative_complete ainda usa refuted não formal em algumas ausências de shape; o total de c mantém seu desenvolvimento restrito; as rotas semânticas legadas não participam desta entrada. Não se declara saneamento geral de todos os estados do pipeline antigo. A cobertura forte usa o mesmo domínio tipado da matriz original e fecha os três gaps autorizados, sem tornar o LLM autoridade matemática.

**CHECKER_COVERAGE_COMPLETE — 13/13, CHECKER_GAP=0 na rota P3_CHECKER_FIRST.** Encerrado o fortalecimento; Semantic Formal/Extractor P3 não iniciado.
