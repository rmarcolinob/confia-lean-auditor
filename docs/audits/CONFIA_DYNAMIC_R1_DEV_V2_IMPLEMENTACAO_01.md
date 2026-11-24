# ConfIA Dynamic — R1 / DYNAMIC_DEV_V2 — Implementação 01

**Veredito: R1_DEV_V2_IMPROVEMENT_CONFIRMED.** No DEV_V2 primário, G0 e G2 passaram de 18 para 1 missed-credit criterion, sem falso crédito novo: 17 melhorias, 0 pioras e 55 empates por perfil. São resultados de desenvolvimento sintético, não evidência independente de generalização.

## 1. Frozen forensic SHA

Forense: `5aa7344e5904305a414688741f83aafc7d610200`; implementação DY7 da baseline: `e0975898bb2449c05595c5b75236a9690c51b8b1`. Branch `feat/dynamic-correction`, worktree exclusivo `~/Documents/confia-lean-auditor-dynamic`. Nenhum git add ou commit foi feito nesta etapa.

A baseline foi executada a partir de uma cópia de `app/` extraída do commit DY7, dentro de `artifacts/dynamic_r1/baseline_source`. Não depende de worktrees de dezembro ou P3. O run guarda os hashes dos fontes efetivamente importados; o SHA do Git obtido pelo runtime pode refletir o repositório pai, por isso a identidade do código baseline é o commit de extração mais o manifesto de arquivos, não esse metadado isolado.

O [diagnóstico pré-implementação](assets/confia-dynamic-r1-dev-v2/preimplementation.md), o dataset e o protocolo foram escritos antes da alteração de `app/`. A primeira execução do harness encontrou dois campos obrigatórios de proveniência ausentes na fixture; foram preenchidos antes da baseline concluída. Os dados e gold não foram alterados.

Versões finais: grader `dynamic-grader.r1`, claim `student-claim.r1`, extractor `source-grammar.r1`, normalização `source-structure.r1`, operação `substitution-operation.r1`, política de linguagem `exact-rubric-language.r1`, sufficiency `method-sufficiency.r1`. O checker continua `dynamic-exact-polynomial.v1`; reviewer e reconciliation/policy não foram alterados. O estágio intermediário teve grader `dynamic-grader.r1-substitution`.

## 2. Root causes

| Camada | Comportamento DY7 | Ponto de mudança |
| --- | --- | --- |
| CLAIM_EXTRACTION | Comparação textual por `shape` perde vínculo de avaliações numericamente corretas com a expressão original | `substitution_operation` compara estrutura preservada e associa variável, valor, expressão e resultado |
| SUFFICIENCY | Método depende da tag de fatoração ou fórmula completa; transformações equivalentes verificadas com conclusão completa podem receber zero | `method_coverage` verifica a obrigação da rubrica e a evidência apresentada |
| Reconhecimento de fatoração, contribuinte upstream | Regex não lida com parênteses internos | `is_factorization` examina fatores lineares em árvore limitada |
| Contrato histórico | Novos campos poderiam modificar hashes ao reler evidências v1 | Serializer preserva exatamente o formato legado; 80 resultados baseline DEV_V2 relidos com mesmo hash |

A tensão entre gold e rubrica nos dois method antigos não foi usada para decidir concessão de crédito com uma conclusão incorreta. Esses registros continuam históricos e pendentes de adjudicação. A regra de método completo ainda exige conclusão completa verificada, salvo rubrica com outra obrigação expressamente suportada.

## 3. DEV_V2 design

[Casos e gold congelados](../../benchmarks/dynamic/dev_v2/cases.json) e [protocolo pré-registrado](../../benchmarks/dynamic/dev_v2/protocol.json). ID `DYNAMIC_DEV_V2`, versão `2.0.0`, papel `DEVELOPMENT_NOT_HOLDOUT`.

| Estrato | Tentativas / critérios | Tratamento |
| --- | --- | --- |
| Substituição | 40: 20 positivos + 20 negativos próximos | Primário |
| Método | 32: 16 positivos + 16 negativos próximos | Primário |
| Fronteiras: função e sistema | 4: 2 positivos + 2 negativos próximos | Separado e incluído no total inequívoco |
| Tensão de método × gold | 4 casos novos | BENCHMARK_ADJUDICATION_REQUIRED, fora de métricas numéricas |
| Total | 80 | 72 primários; 76 inequívocos |

Cada tentativa tem um critério alvo de **4 pontos máximos**, inclusive positivos parciais de 2 pontos. Há seis enunciados suportados de equações reais, mais dois enunciados de fronteira. As expressões numéricas são avaliadas no contexto das equações; funções isoladas e sistemas não ganharam suporte neste R1. Não se apresenta esta amostra como cobertura geral de funções ou sistemas. O [manifesto versionado](../../benchmarks/dynamic/dev_v2/manifest.json) liga aliases de transcrição, fonte, rubrica, gold, implementação e cada run.

Variam sinais, raízes negativas, frações, decimal exato, parênteses, ordem comutativa, prefixos explícitos, substituição implícita, avaliações repetidas, conclusão subsequente, fórmula alternativa, retração e aritmética irrelevante. Os pares de método incluem fatoração, divisão por constante, transposição, quadrado completo, simplificação, fórmula, sequência, ausência de método, transformação parcial, técnica específica e resultado correto com desenvolvimento errado.

Baseline e R1 usam a mesma fixture `rubric-scoped-max.v1`: cita claims por tipo/obrigação e propõe o máximo, sem acesso ao gold ou G0. É fixture de exercício dos gates, não reviewer inteligente nem LLM. O harness é uma avaliação dos componentes com contexto/rubrica/transcrição sintéticos congelados; não simula aprovação pedagógica humana nem uma turma real. A proteção de RubricVersion aprovada em produção continua nos serviços de resolução de contexto, cobertos pela regressão.

Os dois perfis repetem os mesmos exemplos: 160 registros físicos, **80 tentativas lógicas**, não N=160 independente. Os 36 pares primários também compartilham problemas; não há inferência estatística de generalização.

## 4. Anti-leakage policy

HOLDOUT_V1 não foi executado pós-fix, copiado para o DEV ou usado como critério de sucesso. Nenhum arquivo de seus casos, rubricas, gold, expectativas, outputs ou forense foi alterado. A proteção por hashes inclui esses arquivos e o código de reviewer/reconciliation.

O protocolo antecede os resultados e fixa: precisão/recall binários de crédito, false/missed credit versus pontos gold, point MAE, sobre/subcrédito, review rate, automação, unsafe automation, pares e exclusões. Gate final: reduzir ao menos 25% dos missed credits primários em G0 e G2, sem aumento de falso crédito ou sobrecrédito e sem nova automação insegura material. Limiar material: **1 ponto na escala /4**. Esse critério de experimento não altera threshold de produção.

`null` em G1 não é nota zero: disponibilidade e abstenção são publicadas. Recall binário considera ausência de crédito validado como FN quando gold>0; MAE de G1 usa somente notas definidas e nunca é apresentado sem denominador.

## 5. Substitution fix

Mudanças em `dynamic/substitution.py`, `grader.extract` e no contrato de StudentClaim. O fluxo agora é:

`source span exato → SUBSTITUTION + operação vinculada → avaliação exata existente → verified_values → binding ao critério`.

A operação registra expressão original, variável, valor, expressão e resultado escritos, expressão avaliada, resultado calculado, se a atribuição de valor foi explícita e a versão da normalização. Conserva `complete_solution_claimed=false`: verificar uma raiz não afirma que o aluno forneceu todas as soluções.

O normalizador estrutural usa AST limitada, sem executar código. Normaliza sinais, comutatividade e literais racionais; preserva produtos e potências, em vez de reduzir toda expressão numérica a zero. Isso impede que `0=0` ou uma conta irrelevante verdadeira adquiram vínculo com o problema. Avaliação de verdade continua no checker exato existente. Um valor que não é raiz pode ter avaliação aritmética verdadeira sem receber crédito de verificação de raiz. Uma avaliação falsa é REFUTED; uma falha do checker é ERROR, não refutação.

Prefixos suportados incluem `Para`, `Com` e `Substituindo` com atribuição explícita. A atribuição não libera qualquer cálculo numérico: a estrutura ainda deve corresponder à expressão original. Não há condição por problem ID, case ID, coeficientes ou texto do HOLDOUT.

**Gate intermediário:** em 40 critérios, missed credit 10→0, subcrédito 30→0 pontos, falso crédito 0→0. Pares: 10 melhores, 0 piores, 30 empates. Os 20 negativos ficaram protegidos. Antes de avançar para método, 163 testes de substituição e DY3–DY5 passaram. [Registro do gate](assets/confia-dynamic-r1-dev-v2/substitution-gate.json).

## 6. Method sufficiency fix

A linguagem executável permanece fechada; notas, obrigações extras ou redações não suportadas não são descartadas por keyword match.

| Obrigação reconhecida | Evidência exigida por R1 |
| --- | --- |
| Justificar resolução por transformações equivalentes | Transformação não cosmética, verificada e pertinente, mais conclusão completa verificada; ou fórmulas verificadas cobrindo todas as raízes. Sem passo refutado |
| Justificar fatoração | Fatoração estruturalmente identificada e verificada; não acrescenta exigência de conjunto final de raízes a uma rubrica que só pede fatoração |
| Simplificar por uma transformação equivalente | Uma transformação pertinente verificada; resposta final sozinha não serve |
| Método com cláusula explícita de 50% por transformação sem conclusão | Metade dos pontos somente quando há transformação válida e nenhuma conclusão apresentada; não promove evidência parcial a full credit |
| Técnica específica fora da linguagem, como a redação DEV que exige fórmula | REVIEW_ONLY; não substituir silenciosamente por “qualquer método” |

A cláusula parcial de 50% é texto explícito do novo critério, não desconto arbitrário global. Uma cláusula diferente, como 75%, fica não suportada. Multiplicação por 1, mera mudança de parênteses ou reordenação cosmética da equação original não criam método. Uma transformação refutada bloqueia crédito de método mesmo com resposta final correta. Candidate solutions não são consultadas para pontuar. Uma revisão adicional reforçou o grau real dos fatores usando o checker polinomial existente: uma variável que se cancela não pode simular um fator não constante. Os controles adicionais de fatoração e de combinações de cláusulas parciais passaram; o run definitivo `r1-final-03` inclui essa proteção e manteve todas as métricas do dataset congelado.

**Gate de método:** 32 critérios, missed credit 8→1, subcrédito 30→4 pontos, falso crédito 0→0. Recuperados 26 pontos. A regressão inicial detectou que quantizar crédito integral mudava `10` para `10.00`; a implementação foi corrigida para preservar o contrato, sem mudar expectativa de teste. Depois passaram 90 testes focais. [Gate de método](assets/confia-dynamic-r1-dev-v2/method-gate.json).

Reviewer e reconciliation mantêm suas implementações. Eles recebem claims melhores pela extração compartilhada; alguns critérios concedidos pelo novo grader continuam em revisão porque o limite independente do reviewer ainda é mais estreito. Não foram alterados para compensar G0 nem para aumentar coverage.

## 7. Rubric/gold adjudication policy

O [registro de adjudicação](../../benchmarks/dynamic/dev_v2/adjudication.json) separa referências históricas dos quatro novos casos ambíguos. Estado: `BENCHMARK_ADJUDICATION_REQUIRED`, sem adjudicação automática, sem modificação do gold ou rubrica.

Os quatro casos foram excluídos prospectivamente das métricas que exigem interpretação inequívoca; seus golds originais e traces permanecem no JSON. Todos continuam em revisão. A regra não exclui casos apenas porque o motor falhou: o positivo de fórmula específica permanece no denominador primário, e os positivos de função/sistema entram no total inequívoco de 76.

Ação futura: dois avaliadores humanos devem explicitar se método recebe crédito independente de conclusão incorreta e, se necessário, aprovar nova versão de rubrica/gold com razão e referência ao histórico. Nenhuma mensagem externa ou mudança de estado docente foi feita.

## 8. Baseline

Aplicação DY7 congelada, executada **somente no DEV_V2**, com mesmo texto, gold, rubrica, fixture e perfis de R1. [Output baseline](assets/confia-dynamic-r1-dev-v2/baseline.json).

| Estágio | N definido / 72 | Precisão | Recall | FC / MC | Point MAE /4 | Sobre / subcrédito | Revisão | Automação interna / final |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G0 | 72/72 | 100.00% | 50.00% | 0 / 18 | 0.8333 | 0.0 / 60.0 | 63.89% | 26/72 |
| G1 | 11/72 | 100.00% | 30.56% | 0 / 0 | 0.0000 | 0.0 / 0.0 | 84.72% | 11/72 |
| G2 | 72/72 | 100.00% | 50.00% | 0 / 18 | 0.8333 | 0.0 / 60.0 | 84.72% | 11/72 |

G1 tem MAE 0 apenas nos 11 critérios definidos e abstém-se nos demais 61; isso não representa correção perfeita. Gold primário total: 118 pontos, score G0/G2: 58. Precisão de crédito positiva é 1, mas recall é 0,5 e faltam 60 pontos legítimos.

## 9. R1 metrics

[Output final R1](assets/confia-dynamic-r1-dev-v2/r1-final-03.json); ambos os perfis têm os resultados abaixo.

| Estágio | N definido / 72 | Precisão | Recall | FC / MC | Point MAE /4 | Sobre / subcrédito | Revisão | Automação interna / final |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G0 | 72/72 | 100.00% | 97.22% | 0 / 1 | 0.0556 | 0.0 / 4.0 | 37.50% | 45/72 |
| G1 | 20/72 | 100.00% | 55.56% | 0 / 0 | 0.0000 | 0.0 / 0.0 | 72.22% | 20/72 |
| G2 | 72/72 | 100.00% | 97.22% | 0 / 1 | 0.0556 | 0.0 / 4.0 | 72.22% | 20/72 |

Gold primário 118; G0/G2 114; sobrecrédito 0; subcrédito 4. Recall de critérios positivos 35/36=97,22%; point MAE 0,0556 na escala /4. Missed-credit rate 1/72=1,39%, contra 25% na baseline. Redução de contagem de missed credit: 94,44%. Não confundir recall binário com recuperação de todos os pontos: ambas as métricas são publicadas.

Incluindo os quatro casos de fronteira (76 inequívocos):

| Versão / perfil | N | Precisão | Recall | FC / MC | MAE /4 | Subcrédito | Review rate | Automação G2 | Unsafe G2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DY7 / ambos | 76 | 100.00% | 47.37% | 0 / 20 | 0.8947 | 68.0 | 85.53% | 11/76 (14.47%) | 0/11 |
| R1 / ambos | 76 | 100.00% | 92.11% | 0 / 3 | 0.1579 | 12.0 | 73.68% | 20/76 (26.32%) | 0/20 |

Há três MC nesse denominador: fórmula específica, função e sistema. A melhora no DEV primário não é usada para ocultar esses limites.

## 10. Paired comparison

| Perfil / unidade | N | Melhor | Pior | Empate | Pontos recuperados | Novos FC |
| --- | --- | --- | --- | --- | --- | --- |
| FORMATIVE_LIST / primário G0=G2 | 72 | 17 | 0 | 55 | 56.0 | 0 |
| SCHOOL_EXAM / primário G0=G2 | 72 | 17 | 0 | 55 | 56.0 | 0 |
| FORMATIVE_LIST / todos inequívocos G0=G2 | 76 | 17 | 0 | 59 | 56 | 0 |
| SCHOOL_EXAM / todos inequívocos G0=G2 | 76 | 17 | 0 | 59 | 56 | 0 |

G0 e G2 são numericamente iguais nos exemplos desta avaliação. Foram recuperados **56 pontos**: 30 por substituição e 26 por método. Não houve novos falsos créditos. No primário, G2 teve nove transições revisão→automação e nenhuma no sentido contrário; G0 teve 20→automação e uma→revisão. Essas contagens não equivalem a mudanças de nota: a revisão pode mudar mantendo pontos iguais.

[Comparação por critério/caso](assets/confia-dynamic-r1-dev-v2/paired.csv) contém baseline/R1, deltas, gold, elegibilidade e revisão. [Resumo legível por máquina](assets/confia-dynamic-r1-dev-v2/summary.json) conserva denominadores e veredito.

Traces completos incluem texto, fonte/versão, claims e operações, bindings, checker status, sufficiency, G0, proposta bruta/validada G1, comparação e G2. Exemplos novos:

| Caso | Fonte nova | Gold | G0 baseline | G0 R1 | G1 R1 | G2 R1 | Sufficiency G0 | G2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| substitution-signed-positive | 3*(5)^2+(-36)*(5)+105=0 | 2.0 | 0.0 | 2.0 | null | 2.0 | PARTIAL | REVIEW_ONLY |
| substitution-context-no-license-negative | Para w=-3: 12-12=0 | 0.0 | 0.0 | 0.0 | null | 0.0 | INSUFFICIENT | REVIEW_ONLY |
| method-division-positive | t^2-12*t+35=0; S={5,7} | 4.0 | 0.0 | 4.0 | null | 4.0 | COMPLETE | REVIEW_ONLY |
| method-factor-only-positive | (r-9)*(r+9)=0 | 4.0 | 0.0 | 4.0 | null | 4.0 | COMPLETE | REVIEW_ONLY |
| method-partial-explicit-positive | t^2-12*t+35=0 | 2.0 | 0.0 | 2.0 | null | 2.0 | PARTIAL | REVIEW_ONLY |
| method-answer-only-negative | S={5,8} | 0.0 | 0.0 | 0.0 | null | 0.0 | INSUFFICIENT | REVIEW_ONLY |
| method-specific-formula-positive | k=(13+sqrt(9))/2=8; k=(13-sqrt(9))/2=5; S={5,8} | 4.0 | 0.0 | 0.0 | null | 0.0 | INSUFFICIENT | REVIEW_ONLY |

## 11. False credits

Primário: 0/72 na baseline e 0/72 em R1, G0 e G2, com zero over-credit points. Total inequívoco: 0/76 em ambos. Os 36 negativos primários e os dois negativos de fronteira não ganharam crédito indevido.

Controles específicos incluem sinal incorreto, número que coincide com um resultado verdadeiro sem associação à expressão, valor explicitamente diferente do usado na conta, potência de número negativo sem os parênteses necessários, transformação não equivalente, resposta final sem método, método errado com resposta correta, fatoração exigida mas fórmula fornecida e exigência de fórmula não suportada. Nenhum threshold global de REVIEW_ONLY foi reduzido.

Zero falso crédito em DEV sintético é uma observação local, não garantia de precisão geral. Os mesmos casos foram observados durante desenvolvimento e são marcados como DEV.

## 12. Missed credits

O MC primário restante é `method-specific-formula-positive` (4 pontos): a fonte contém fórmula válida, mas a redação específica do critério não pertence à linguagem executável; o sistema não infere uma obrigação mais fraca. O controle negativo de fatoração sob esse critério também permanece zero/revisão.

`boundary-function-positive` e `boundary-system-positive` somam mais 8 pontos ausentes no total inequívoco. Não são excluídos retrospectivamente; a fronteira foi declarada no protocolo inicial e o relatório apresenta ambos os denominadores. Outras equivalências algébricas arbitrárias de contas já avaliadas podem continuar sem associação de fonte; R1 não tenta reconstruir passos que o aluno não escreveu.

## 13. Automation

G2 primário: 11/72=15,28% → 20/72=27,78%; review rate: 84,72% → 72,22%. No total inequívoco: 11/76=14,47% → 20/76=26,32%. FORMATIVE_LIST e SCHOOL_EXAM não diferiram neste conjunto; isso não significa que suas políticas sejam equivalentes em geral.

Não se usa a autorização interna de G0 como automação final. G1 definido aumentou de 11 para 20, mas ainda tem 52 abstenções primárias. A fixture de máxima proposta não fornece pontuação parcial e não é evidência sobre desempenho de LLM reviewer. O ganho de automação decorre de evidência que passou nos gates existentes, não de relaxamento de política.

## 14. Unsafe automation

G2 primário: baseline 0/11 e R1 0/20 automatizados com erro versus gold; nenhum erro material novo. Total inequívoco: os mesmos denominadores automáticos. Os quatro casos de adjudicação ficaram em revisão e não foram automatizados.

O protocolo considera qualquer divergência de score insegura e reporta separadamente divergência material ≥1 ponto /4. Precisão e recall, sobrecrédito, subcrédito, review rate, coverage e risco foram congelados antes dos outputs; a queda de MAE, sozinha, não determina o veredito. Não foram calculados intervalos de generalização a partir destes poucos problemas sintéticos correlacionados.

## 15. Regression

| Execução | Resultado |
| --- | --- |
| Dynamic final (DY1–DY7 + R1) | **306 passed**, incluindo 92 testes R1 |
| JavaScript completo | **564 passed**, 0 failed |
| Python completo | **3009 passed, 47 skipped, 105 failed** (3161 coletados) |
| Repetição DY7 de dois testes Specialized | As mesmas duas falhas reproduzidas |
| Repetição DY7 de schema de captura e dois testes de UI | As mesmas três falhas reproduzidas |

**A regressão global não está verde.** Das 105 falhas, 102 estão em testes de integração formal/Lean e efeitos dependentes de verificação indisponível. Artefatos desta execução registram `mathlib: checking out revision 8f9d9cff6bd728b17a24e163c9402775d9e6a365` seguido de `external command git exited with code 1`; respostas podem terminar com `technical_error`, `lean_error`, pontuação indefinida ou `ADJUDICATOR_UNAVAILABLE`. Não se transformou essa indisponibilidade em erro matemático nem se alterou Mathlib.

As quatro falhas formais já documentadas no DY7 estão preservadas separadamente:

1. `tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`
2. `tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved`
3. `tests/test_tme_hybrid_grader.py::test_wrong_reasoning_correct_final_is_refuted_by_real_lean`
4. `tests/test_tme_hybrid_grader.py::test_real_formal_verified_is_preserved_and_not_semantic`

A suíte completa encontrou outras 98 falhas da família formal; duas foram reproduzidas individualmente na baseline DY7. As demais têm classificação de integração formal consistente com o ambiente observado, **não uma reprodução individual completa contra baseline**. A validação formal ampla permanece pendente.

As três falhas não Lean foram todas reproduzidas no código DY7: divergência entre schema gerado e fixture de reconhecimento manuscrito; expectativa antiga da expressão “Verificação formal com Lean” no frontend; expectativa de ausência de `position: sticky` no CSS de captura. Esses arquivos e suas expectativas não foram alterados por R1.

A suíte ampla começou antes do últimos reforços locais da classificação de fatores e da linguagem fechada de crédito parcial; após esse reforço, todos os 306 testes Dynamic foram reexecutados na versão final e o benchmark foi novamente congelado como `r1-final-03`, com métricas idênticas. Os testes existentes não foram editados. [Classificação e lista integral de falhas](assets/confia-dynamic-r1-dev-v2/regression-classification.json) e [evidência ambiental](assets/confia-dynamic-r1-dev-v2/environment-evidence.json) mantêm essa distinção auditável.

A suíte completa abrange DY1–DY7, D1–D7, Specialized, TME, certification e contratos compartilhados. Testes determinísticos não usam rede; nenhum provider real foi chamado. Os testes anteriores não foram modificados. Os novos testes são de comportamento e segurança, incluindo source spans, racional/decimal exato, múltiplas avaliações, ausência de conclusão implícita, checker ERROR, requisitos específicos, crédito parcial explícito e preservação de recibos antigos.

O schema aceita ler versões antigas. A execução com contexto de grader histórico não pode ser silenciosamente reidentificada como R1: requer novo contexto atual. No benchmark, `dev-v2:case:1` é a referência lógica do dataset, não um ID de banco: o manifesto a mapeia para `tr_<hash>:1`, usada pelo motor, com o mesmo hash da fonte. A serialização v1 preserva os campos antigos para não invalidar hashes de AuditRun/review; a verificação direta de 80 resultados DY7 produzidos no novo DEV_V2 confirmou hashes canônicos idênticos.

Logs: [Python](assets/confia-dynamic-r1-dev-v2/regression-python.log), [JavaScript](assets/confia-dynamic-r1-dev-v2/regression-js.log), [testes intermediários](assets/confia-dynamic-r1-dev-v2/substitution-tests.log). [Verificação de integridade](assets/confia-dynamic-r1-dev-v2/integrity.json) vincula fontes finais, dataset, outputs e arquivos históricos protegidos.

## 16. Limitations

- Gold sintético de um autor, predeclarado, não avaliação humana independente. Pares e perfis repetem problemas; resultados são de desenvolvimento.
- Benchmark principal avalia componentes com um critério alvo por tentativa; a regressão cobre contratos e fluxos existentes, mas isso não constitui estudo real multiquestão com professores.
- Gramática matemática continua restrita a equações reais univariadas de grau 1/2 com raízes racionais e às operações exatas suportadas. Funções/sistemas do estrato de fronteira continuam em revisão.
- Linguagem de rubrica fechada; a redação específica de fórmula ainda perde crédito. Novas cláusulas não são interpretadas por aproximação.
- O recognizer estrutural não demonstra cobertura de toda notação equivalente nem transforma qualquer conta verdadeira em substituição. Captura/OCR permaneceu fora do escopo.
- Reviewer fixture não foi melhorado para compensar o grader; casos sem proposta validada continuam em revisão, incluindo parte dos créditos recuperados por G0.
- Falhas formais ambientais não foram reparadas nem confundidas com refutação matemática.

## 17. Recommendation

**R1_DEV_V2_IMPROVEMENT_CONFIRMED** no DEV_V2, conforme gates prospectivos e limites acima. Os arquivos de implementação, testes, casos, protocolo e artefatos estão disponíveis para revisão; não houve git add/commit.

Próxima etapa: construir e congelar **HOLDOUT_V2 novo, independente e ainda não observado**, com curadoria e adjudicação humana, depois de congelar a versão avaliada. Não reusar HOLDOUT_V1 como validação independente. Nenhum caso completo de HOLDOUT_V2 foi criado nesta tarefa.

Reprodução offline: recriar `artifacts/dynamic_r1/baseline_source/app` a partir de `git archive e097589 app`, se ausente; executar `scripts/evaluation/run_dynamic_dev_v2.py --implementation baseline --label NOVO_ROTULO` ou `--implementation current --label NOVO_ROTULO` com o Python de `.venv`. O runner exige hash do dataset igual ao protocolo e recusa reutilizar diretório/rótulo de run. Os outputs existentes são preservados; os resultados oficiais deste relatório são os rótulos `baseline` e `r1-final-03`, não uma reexecução futura. O manifesto registra seus hashes e versões.
