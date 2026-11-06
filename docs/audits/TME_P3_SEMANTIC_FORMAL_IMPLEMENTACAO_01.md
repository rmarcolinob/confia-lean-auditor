# TME Semantic Formal P3 — Implementação 01

Data: 2026-11-05. Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3`. Branch: `experiment/tme-semantic-formal-p3`. Base encontrada nesta tarefa, com worktree inicialmente limpo: **`6617447f6bbfab37d9c16fc33ea7e898a5141578`**. Esta base já contém o checker-first concluído; não foi usado o SHA anterior dos relatórios como se ainda fosse o HEAD.

**READY_FOR_P3_SEMANTIC_FORMAL_DEV.** Camada experimental implementada, com **419 testes distintos aprovados**, incluindo as 274 regressões checker-first. Os oito casos DEV e o runner estão preparados. **O piloto não foi executado, em nenhum dos dois modos; nenhuma chamada real ao SemanticExtractor/API foi feita.** A prontidão é para iniciar o DEV posteriormente, não evidência de qualidade do modelo em prosa inédita.

## 1. Arquitetura e autoridade

```text
solução original, separada por itens
→ SemanticExtractorP3: interpretação estruturada
→ EvidenceUnit: envelope literal, IDs e offsets calculados localmente
→ ObligationMapper: item, subject, tipo, representação, contexto e registry
→ projeção rastreável em MathClaimRecord
→ StrongP3Checks e demais produtores congelados de P3
→ resultados e componentes de verificação independentes
→ reconciliação + sufficiency/award gate
→ PautaEngine congelado
→ ScoreClosurePolicy: score sempre numérico para a auditoria aceita
```

O pacote paralelo é [tme_semantic_formal_p3](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3). Não foi registrado como substituto do TME_CURRENT. O modelo não recebe score baseline, resultados de checker, pontos ou alvos de nota. Recebe enunciado, fonte, vocabulário, descrição das obrigações e schemas de representação. Não pode enviar campos de decisão ou pontos: o schema é fechado.

| Componente novo | Responsabilidade |
| --- | --- |
| evidence.py | Schema de extração; binding exato à fonte; IDs/offsets locais; deduplicação sem usar confidence para crédito |
| extractor.py | Prompt P3, structured output e transporte; sem retries; indisponibilidade explícita |
| registry.py | 13 obrigações derivadas de coverage_rows do checker-first; subjects/tipos compatíveis e rotas fortes |
| mapper.py | Contexto local, propriedade do item, sujeito e fidelidade da representação; não verifica verdade matemática |
| verification.py | Projeção, execução dos checkers congelados, recibos e isolamento de exceção por obrigação |
| engine.py | Guard negativo, conflitos, award, pauta, fallback e fechamento numérico |
| __init__.py | Versão `tme-semantic-formal-p3.v1` |

Reutilizam-se o collector digital P3, `StrongP3Checks`, `_a/_b/_c`, o checker racional Lean, a máquina, FactResultsBuilder, bridge e PautaEngine. O adaptador de projeção substitui somente o suplemento de interpretação dentro de um scope local. O guard executa checker-first sobre a fonte com `use_lean=False` e sem LLM; **serve apenas de veto**, nunca completa evidência positiva omitida pelo extractor.

## 2. Extração, fonte e contexto

Configuração padrão: **gpt-6.1-sol / medium**, timeout **180 s**, `max_retries=0`, `max_output_tokens=16000`, **store=False**, compatível com P2. Falha de transporte, resposta incompleta e erro de schema/binding retornam indisponibilidade; não há tentativa escondida com outro modelo. Testes do transporte usaram cliente simulado, inclusive timeout, sem rede.

EvidenceUnit preserva `source_evidence_ids`, `source_span`, `item_id`, `asserted_content`, `normalized_claim`, `subject`, `claim_type`, `assertion_status`, `polarity`, `scope`, `hypothetical`, `abandoned`, `attributed_to_student`, `obligation_candidates`, `route_candidate`, `confidence`, offsets, modelo e hash da fonte. O payload canônico fica também registrado no evento de projeção. `asserted_content` deve estar literalmente no span. O envelope deve ser exatamente o intervalo entre as unidades de fonte indicadas; o modelo não escolhe offsets arbitrários.

`confidence` é diagnóstica e não muda ID, routing, verificação ou score. `route_candidate=SEMANTIC` pode ser recebido como sugestão não confiável, mas é substituído pelo registry: **não existe rota efetiva de crédito SEMANTIC**. A lista de obrigações não aceita IDs inventados.

O mapper exige atribuição positiva ao aluno e item correspondente. Negação, hipótese não adotada, abandono, citação e atribuição não adotada a terceiros produzem `CONTEXT_REJECTED`. Um cabeçalho de contexto restritivo vale no seu parágrafo até uma retomada explícita; ele não veta automaticamente toda a solução. Há teste de hipótese inválida seguida de resposta independente válida, preservando os 2 pontos dessa resposta. Condição matemática de caso, como “Após sair branca do compartimento 1”, não é automaticamente tratada como hipótese exploratória.

Notação tipada precisa manter o payload literal do mesmo subject. Na prosa, a normalização é limitada a âncoras locais, números por extenso, ordinais, cores e representação escrita. Quantidades de brancas/cores devem estar ligadas ao número escrito. Não é permitido extrair 2 de “doze”, usar a quantidade de pretas como a de brancas, transportar número de outra oração ou cortar o lado errado de uma igualdade. Conjuntos precisam ter membros explícitos; não são completados a partir da máquina. Caso/compartimento precisa estar indicado na fonte.

Essas verificações são conservadoras: prosa ambígua, múltiplas orações concorrentes ou representação fora da gramática ficam sem crédito automático. Não se afirma cobertura universal de linguagem, imagens ou árvores visuais.

## 3. Matriz de 13 obrigações e rotas

Referência congelada: [Checker Coverage 02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_CHECKER_COVERAGE_02.md). A classificação primária permanece 4 DETERMINISTIC_STRONG + 9 COMPOSITE_STRONG. FORMAL é rota da igualdade escrita apropriada, não uma substituição da verificação do estado.

| obligation_id | Subjects | Rota efetiva | Condição de suficiência preservada |
| --- | --- | --- | --- |
| a.bottom_white_count | inferiores_brancas | DETERMINISTIC | Contagem explícita das brancas inferiores, confrontada com a máquina |
| a.first_white_probability | primeira_branca | DETERMINISTIC para valor; FORMAL para igualdade escrita | Valor isolado permitido; igualdade formal só recebe selo formal se Lean a provar |
| b.ordered_pairs | pares_ordenados | COMPOSITE | Certificado dos pares + aritmética + relação de duas escolhas escrita |
| b.different_favorable | favoraveis_distintos | COMPOSITE | Enumeração dos distintos favoráveis + relação dos fatores + aritmética |
| b.same_compartment | repeticao_branca | DETERMINISTIC | Conjunto explícito comparado à diagonal branca do modelo |
| b.second_white_probability | segunda_branca, arvore_total | COMPOSITE | Resultado separado de argumento; desenvolvimento exige partição/árvore validada; aritmética pode executar Lean |
| b.alternative_complete | arvore_total, ramo_1..ramo_6 | COMPOSITE | Seis ramos corretos + soma ponderada completa; método alternativo, não pontos adicionais |
| c.continue_compartments | continuar | DETERMINISTIC | Conjunto explícito de continuação |
| c.strategy_case_1 | estrategia_1, contagem_1 | COMPOSITE | Cor, contagem e ótimo derivados do estado após o caso 1 |
| c.strategy_case_2 | estrategia_2, contagem_2 | COMPOSITE | Cor, contagem e ótimo derivados do estado após o caso 2 |
| c.conditional_success_1 | condicional_1 | COMPOSITE | Estratégia verificada do caso 1 + probabilidade; Lean em igualdade elegível |
| c.conditional_success_2 | condicional_2 | COMPOSITE | Estratégia verificada do caso 2 + probabilidade; Lean em igualdade elegível |
| c.total_win_probability | total | COMPOSITE | Continuação, estratégias, condicionais e desenvolvimento global; Lean em igualdade elegível |

Dependências de um fato composto permanecem vinculadas às EvidenceUnits que produziram os registros de contexto. Não se exige que o modelo adivinhe todas as dependências como candidatos de cada claim: cada evidência precisa de seu mapeamento válido e o checker congelado constrói a conjunção. O fato principal precisa de candidato compatível com a obrigação e de recibo validado. Nenhum ponto nasce só da presença de uma EvidenceUnit.

O total de 11 casos favoráveis não cria uma 14ª obrigação: aparece como parte da partição verificada da probabilidade. A máquina versionada continua sendo a autoridade para os 36 eventos, 10 distintos favoráveis, único repetido favorável e probabilidades/ótimos. Nenhuma dessas constantes foi introduzida como premissa fornecida pelo extractor.

## 4. Resultado, justificativa e pauta

Pauta preservada: 4+8+8, teto 20. Não houve alteração de pesos, all_of, max_of ou dependências.

- **(a):** `1/3` isolado, inequivocamente vinculado ao item, recebe 2 por checker determinístico, com FORMAL_NOT_ATTEMPTED. Não concede a contagem das duas brancas. A conta `2/6=1/3` pode seguir FORMAL; Lean não foi imposto ao valor isolado.
- **(b):** `11/36` isolado conserva somente os 2 pontos operacionais da conclusão. O composto registra `result_credit_only=true` e `argument_satisfied=false`. 36 ou 10 isolados não ganham as parcelas argumentativas. Desenvolvimento falso não migra automaticamente para a rota de valor. O máximo entre contagem e árvore permanece 8.
- **(c):** `1/6` isolado não cria estratégia, condicionais nem desenvolvimento global. Cor e contagem precisam estar vinculadas ao caso. As duas condicionais compartilham uma única parcela de 1 ponto, com as dependências existentes; não se inventou meio ponto por conditional.

O modo sem Lean usado em unitários não simula FORMAL_VERIFIED: uma igualdade de a roteada a FORMAL permanece FORMAL_NOT_ATTEMPTED e não recebe aquele award. Isso não afeta a rota determinística autorizada para um valor isolado. Nas rotas compostas, a aritmética determinística admitida pelo contrato checker-first continua válida quando Lean não é solicitado.

## 5. Conflitos, estados e fechamento numérico

Evidências positiva e negativa são preservadas. Conflitos materiais não têm precedência por ordem, confiança ou preferência do modelo. São reconciliados pela bridge e pelo gate da camada nova, com `CONFLICTING_EVIDENCE`, `resolved=false` e bloqueio local do award. O guard impede omitir uma contradição reconhecível pelo parser/checker congelado; ele não fornece créditos positivos.

Testes incluem `11/36` e `12/36`, repetição {6} e {5}, estratégias incompatíveis no mesmo estado, duas ordens de apresentação e omissão deliberada de evidência negativa tipada. Em todos esses cenários, uma contagem válida independente no item a conserva seus 2 pontos. Hipótese rejeitada não é promovida a refutação matemática nem apaga outro span válido.

Estados observáveis:

| Família | Estados / alcance |
| --- | --- |
| FORMAL | FORMAL_VERIFIED, FORMAL_REFUTED, FORMAL_UNPROVED, FORMAL_ERROR, FORMAL_NOT_ATTEMPTED |
| DETERMINISTIC | DETERMINISTIC_VERIFIED, DETERMINISTIC_FAILED; INCOMPLETE e ERROR quando apropriado |
| COMPOSITE | COMPOSITE_VERIFIED, COMPOSITE_FAILED, COMPOSITE_INCOMPLETE; COMPOSITE_ERROR para falha técnica |
| Contexto | CONTEXT_REJECTED; interpretação contraditória preservada como CONFLICTING_EVIDENCE |

Um erro antes de iniciar Lean tem FORMAL_NOT_ATTEMPTED mais estado técnico; não é FORMAL_UNPROVED. Falha após execução é distinguida por recibo. Prova da igualdade não atesta a estrutura probabilística: `(9+2)/36=11/36` foi formalmente provada nos testes, mas o composto rejeitou a partição e reteve crédito.

Exceções nos métodos `observe`/`numerical` são contidas na obrigação que falhou; o adaptador descarta eventual resultado parcial dessa chamada e emite technical_error. `ScoreClosurePolicy` mantém score numérico e registra `technical_uncertainty`/`review_recommended`, preservando créditos independentes. Esse tratamento não muda a matemática dos checkers congelados.

Falha do extractor/API/schema/binding usa **TME_CURRENT_FALLBACK**, com `fallback=true`, `fallback_used=true`, motivo e modo efetivo explícitos. O baseline recebe a fonte original. Resultado vazio válido do extractor não é falha de API e não ganha evidência positiva do guard. O modo `tme_current` não chama extractor.

## 6. Testes e regressões executados

| Seleção | Resultado final |
| --- | --- |
| test_tme_semantic_formal_p3.py | **132 PASS** |
| test_tme_semantic_formal_p3_lean.py | **13 PASS** |
| test_tme2_p3_pauta_bridge + test_pauta_engine + test_tme_p3_checker_first + test_tme_p3_checker_first_lean | **268 PASS** |
| Seleção TME2026P3 em semantic_claims, tme_hybrid_grader, scope_boundary | **6 PASS**, 132 deselected |
| Total distinto | **419 PASS**, zero falha residual, zero error, zero skip |

As regressões somam os mesmos **274** testes da entrega checker-first. Incluem os 25 casos históricos; testes adicionais comparam os dumps completos do baseline antes/depois e executam o modo current nesses 25 casos, mantendo todas as expectativas. Não foi feito um novo piloto ou replay DEV. O replay histórico de 25/25 da entrega anterior não foi contado como nova execução independente nesta etapa.

A primeira rodada da nova suíte encontrou duas falhas de chamada na árvore alternativa: metadata `method` colidia com um parâmetro do adaptador de isolamento. A assinatura do adaptador novo foi corrigida; os checkers e expectativas históricos ficaram intactos. A suíte final passou. Testes adicionais fecharam o vínculo de quantidades na prosa para impedir que um número correto de outra oração reparasse um claim falso.

Os testes unitários cobrem todos os 13 IDs, três rotas, negativos matemáticos, contexto hostil, abandono, atribuição, item/subject errados, span adulterado, route override, confidence sem efeito, parcial permitido, método ausente, conflitos, fallback, exceção local, source-only DEV e manifest. O teste de runner usa uma entrada temporária `unit-only` e avaliação simulada; não executa as oito fontes DEV.

## 7. Lean real

Versão confirmada: **Lean 4.28.0**, commit `7e01a1bf5c70fc6167d49c345d3bf80596e9a79b`, arm64-apple-darwin24.6.0. Mathlib: **`8f9d9cff6bd728b17a24e163c9402775d9e6a365`**. Reutilizada a infraestrutura existente, sem alteração de toolchain/manifest.

As provas usam o checker racional congelado, `import Mathlib`, ℚ e `norm_num`. A extração foi fornecida por providers source-only de teste; o compilador, arquivos Lean e resultados formais foram reais. Os cinco IDs com aritmética Lean foram exercitados através da projeção: a.first_white_probability, b.second_white_probability, as duas condicionais de c e c.total_win_probability.

| Status, por ocorrência de fato/componente | Nova suíte de integração | Regressão checker-first Lean |
| --- | --- | --- |
| FORMAL_VERIFIED | 14 | 5 |
| FORMAL_REFUTED | 4 | 3 |
| FORMAL_UNPROVED | 1, induzido com `skip` | 0 |
| FORMAL_ERROR | 1, identificador inexistente induzido | 0 |
| FORMAL_NOT_ATTEMPTED | 19 | 7 |

Ocorrências não equivalem a proposições distintas: fixtures de contexto completo verificam várias igualdades e reaparecem em testes diferentes. Dos 13 testes novos, 12 executam o compilador; um injeta exceção anterior à execução para conferir isolamento técnico. O FORMAL_UNPROVED e o FORMAL_ERROR são controles deliberados com Lean real, não falhas residuais da suíte ou infraestrutura. A refutação exige negação provada, não mera falha da tentativa positiva.

Uma rechecagem focal da versão final do mapper usa três testes já incluídos nos 13, cobrindo as cinco obrigações formais através de a, b e c completo. Ela não aumenta o total distinto de 419. Recibos dessa rechecagem ficam separados das contagens principais acima.

## 8. DEV preparado e congelado antes de execução

Arquivos: [dev_sources.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/dev_sources.json) e [dev_ids.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/fixtures/tme_semantic_formal_p3/dev_ids.json).

| case_id | Família |
| --- | --- |
| p3_dev_initial_count | Contagem inicial e probabilidade de a |
| p3_dev_isolated_answer | 1/3 isolado |
| p3_dev_sample_space | Espaço amostral e duas escolhas |
| p3_dev_favorable_partition | Contagem dos distintos, repetição e total |
| p3_dev_complete_strategy | Estratégias ótimas e probabilidade global |
| p3_dev_probability_error | Erro de contagem/probabilidade |
| p3_dev_hypothesis_context | Hipótese não adotada e resposta independente |
| p3_dev_partial_conflict | Crédito independente e conflitos em b |

Cada fonte contém somente `case_id`, `problem_id`, `solution_text`. Não há expected_score, gold, respostas externas ou anotações de verdade entregues ao extractor. As fontes foram criadas antes dos testes e não foram editadas em função de resultados. Os testes apenas validaram seu schema/IDs; não as avaliaram.

SHA-256 dos bytes, preservados desde a criação:

```text
dev_sources.json d12a77cd87f0e5197db7e3cdafaedf78a130dd7dc3b1b59fa5d029a702e375cc
dev_ids.json     a7ab3a65f60e1284b119c8974a47e3eea0c037f58c96963bff8c7372ebcaab0a
```

## 9. Runner e comandos exatos do piloto — NÃO executados

[run_tme_semantic_formal_p3.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/scripts/evaluation/run_tme_semantic_formal_p3.py) possui modos `tme_current` e `tme_semantic_formal`, destinos separados e recusa sobrescrever uma pasta de saída existente. InputCase é fechado; caminhos gold/holdout e campos rotulados são recusados. O manifest contém SHA, hashes de conteúdo/bytes dos datasets, modelo/effort, modo, configuração, hashes da implementação/checkers/pauta/máquina/toolchain, timestamp, limpeza e status Git; ao terminar acrescenta fallback, motivos por caso, modos efetivos e timestamp final. Uma execução interrompida conserva `state=started` e fallback desconhecido, sem declarar conclusão.

Para uma futura execução autorizada:

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app:$PWD" CONFIA_TME_SEMANTIC_ENABLED=0
P3_PYTHON=/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python

"$P3_PYTHON" -m scripts.evaluation.run_tme_semantic_formal_p3 \
  --mode tme_current \
  --dataset tests/fixtures/tme_semantic_formal_p3/dev_sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_p3/dev_ids.json \
  --output-dir artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_current \
  --model gpt-6.1-sol --reasoning-effort medium

"$P3_PYTHON" -m scripts.evaluation.run_tme_semantic_formal_p3 \
  --mode tme_semantic_formal \
  --dataset tests/fixtures/tme_semantic_formal_p3/dev_sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_p3/dev_ids.json \
  --output-dir artifacts/evaluations/tme_p3_semantic_formal_dev_01/tme_semantic_formal \
  --model gpt-6.1-sol --reasoning-effort medium
```

O flag legado CONFIA_TME_SEMANTIC_ENABLED=0 desabilita suplementos antigos; o extractor experimental só é chamado explicitamente no modo semantic. O segundo comando fará chamadas reais quando futuramente executado com credenciais/configuração disponíveis. Nenhum dos dois comandos acima foi executado nesta tarefa.

## 10. Comandos de validação efetivamente executados

No mesmo worktree e com o ambiente Python descrito acima:

```bash
"$P3_PYTHON" -m pytest tests/test_tme_semantic_formal_p3.py -q -p no:cacheprovider \
  --basetemp=/private/tmp/p3-semantic-01/unit-final2 \
  --junitxml=/private/tmp/p3-semantic-01/unit-final2.xml
"$P3_PYTHON" -m pytest tests/test_tme_semantic_formal_p3_lean.py -q -s -p no:cacheprovider \
  --basetemp=/private/tmp/p3-semantic-01/lean --junitxml=/private/tmp/p3-semantic-01/lean.xml
"$P3_PYTHON" -m pytest tests/test_tme2_p3_pauta_bridge.py tests/test_pauta_engine.py \
  tests/test_tme_p3_checker_first.py tests/test_tme_p3_checker_first_lean.py -q -p no:cacheprovider \
  --basetemp=/private/tmp/p3-semantic-01/regression --junitxml=/private/tmp/p3-semantic-01/regression.xml
"$P3_PYTHON" -m pytest tests/test_semantic_claims.py tests/test_tme_hybrid_grader.py tests/test_scope_boundary.py \
  -k TME2026P3 -q -p no:cacheprovider --basetemp=/private/tmp/p3-semantic-01/related \
  --junitxml=/private/tmp/p3-semantic-01/related.xml
"$P3_PYTHON" -m pytest tests/test_tme_semantic_formal_p3_lean.py \
  -k 'each_five and not conditional_success' -q -p no:cacheprovider \
  --basetemp=/private/tmp/p3-semantic-01/lean-final --junitxml=/private/tmp/p3-semantic-01/lean-final.xml
lake env lean --version
git -C .lake/packages/mathlib rev-parse HEAD
git diff --check
git status --short
git rev-parse HEAD
git branch --show-current
```

Logs e JUnit, comandos integrais com redirecionamentos, receipts formais, hashes, resumo de testes e checagem de preservação: [artefatos locais](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_formal_implementacao_01). Os arquivos Lean executados permanecem em `artifacts/student_claim_checks` com caminhos nos recibos. Nenhum theorem de produção foi adicionado.

## 11. Preservação, limites e Git

**798 arquivos preexistentes monitorados permaneceram byte a byte idênticos.** A comparação excluiu caminhos de gold/holdout, que não foram lidos. Preservados TME_CURRENT, pauta, PautaEngine, checker-first P3, máquina, prompts anteriores, datasets históricos, P1/P2, toolchain e manifest. As duas fixtures DEV mantiveram os hashes da criação. Não houve stage ou commit.

Arquivos novos: sete módulos no pacote P3, runner, dois testes, duas fixtures DEV e este relatório. Artefatos de execução são locais/ignorados. Estado final:

```text
?? app/confia_lean_auditor/experimental/tme_semantic_formal_p3/
?? docs/audits/TME_P3_SEMANTIC_FORMAL_IMPLEMENTACAO_01.md
?? scripts/evaluation/run_tme_semantic_formal_p3.py
?? tests/fixtures/tme_semantic_formal_p3/
?? tests/test_tme_semantic_formal_p3.py
?? tests/test_tme_semantic_formal_p3_lean.py

HEAD: 6617447f6bbfab37d9c16fc33ea7e898a5141578
branch: experiment/tme-semantic-formal-p3
```

Limites preservados dos checkers congelados: formatos aceitos de árvore e total de c continuam restritos; o classificador antigo de b.alternative_complete ainda pode marcar shape ausente como refuted não formal. O adaptador não reescreveu esses contratos. O guard detecta contradições dentro da representação que ele reconhece; não se afirma detecção universal de contradições em prosa omitidas pelo modelo. A camada semântica conserva rejeição conservadora quando não consegue vincular a representação.

O critério desta entrega é infraestrutura e contratos testados sem piloto real. A qualidade da interpretação por gpt-6.1-sol nos oito casos preparados continua não medida. A próxima etapa é executar o DEV autorizado, sem alterar casos a partir dos resultados.

**READY_FOR_P3_SEMANTIC_FORMAL_DEV**
