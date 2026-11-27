# P0-SECONDARY-FALSE-CREDIT-04

## Resultado — tarefa incompleta por aceitação live
Validação live: **failed**, 8 casos, 0 falsos créditos remanescentes nos três critérios-alvo; 2/3 controles positivos e 2/2 controles de deny preservados. 0 respostas inválidas. Não houve batch de 18/502/1000. Este resultado não demonstra ausência universal de erro semântico nem autoriza 502.

## Fonte e diagnóstico antes da alteração
Fonte preservada integralmente: `/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/ita1000_v1_2/smoke_v4_20261029T210908Z`. Os três casos foram obtidos de semantic_review.json e conferidos contra os resultados e catálogos originais. Os 18 hashes históricos de request foram reconstruídos offline antes das alterações; isso foi leitura/reconstrução, sem auditoria externa ou novo benchmark.
Os três testes de regressão falharam na versão anterior; cinco controles passaram (red_tests.log). As cópias dos módulos anteriores estão em snapshot/. O diagnóstico completo está em false_credit_diagnosis.json, com pauta, microclaims, candidatos, IDs escolhidos, spans, claims relacionados, prompt, resposta estruturada, rationale e pontos.

| Caso | Critério | V4 pontos | Requisitos de referência | Primeira decisão errada |
| --- | --- | --- | --- | --- |
| ITA2025F2Q1_S002_L04 | reduced_polynomial_form | 3.0/3.0 | no_textual_evidence | AWARD sem satisfação matemática do critério |
| ITA2025Q1_S014_L04 | coordinates | 2.0/2.0 | verified_by_lean | AWARD sem satisfação matemática do critério |
| ITA2025Q3_S002_L01 | parity_obstruction | 3.0/3.0 | formal_steps_not_verified | AWARD sem satisfação matemática do critério |

### ITA2025F2Q1_S002_L04 / reduced_polynomial_form
O critério exige resto geral (a+b)x−a. O trecho selecionado usa x²=−x−1 e obtém (−a+b)x+(2−a), diferente. Recebe 3 pontos mesmo sem apresentar o resto exigido. É falha semântica de adjudicação, não quebra do vínculo à fonte.
Causa primária: CRITERION_MISINTERPRETATION. Causas adicionais: EVIDENCE_NOT_SUFFICIENT, MISSING_REQUIRED_MICROCLAIM, RATIONALE_OVERREACH.
IDs escolhidos: E2_1. Rationale original: A evidência citada satisfaz o critério da pauta: «Obtém o resto geral p(x) ≡ (a+b)x - a.».
Obrigação: Obtém o resto geral p(x) ≡ (a+b)x - a.
Evidência selecionada original:

> p(x) = x⁵⁷ + a x¹⁴ + b x⁷ +1
> resto da divisão por x² -x +1 é 2x +1 → p(x) ≡ 2x +1 mod x² -x +1
> x² = -x -1
> x³ = x * x² = x(-x -1) = -x² -x = -(-x -1) -x = x +1 -x =1
> x⁵⁷ = (x³)^19 =1^19=1
> x⁷ = x^(6+1) = (x³)^2 *x =1 *x =x
> x¹⁴ = (x³)^4 *x² =1 * (-x -1) = -x -1
> substitui:1 +a(-x -1) +b x +1 = (-a +b)x + (2 -a)
> igualar coeficientes:
> -a +b =2
> 2 -a =1 → a=1, então b=3
> (1,3)

### ITA2025Q1_S014_L04 / coordinates
O secondary concede 2 pontos por coordenadas corretas, mas o trecho selecionado usa z²=(a²+4,4a), onde deveria ser (a²−4,4a). A atribuição literal é correta; a avaliação matemática positiva é incorreta.
Causa primária: CRITERION_MISINTERPRETATION. Causas adicionais: EVIDENCE_NOT_SUFFICIENT, RATIONALE_OVERREACH.
IDs escolhidos: E1_2. Rationale original: A evidência citada satisfaz o critério da pauta: «Representa corretamente os pontos 1, z e z² em coordenadas reais.».
Obrigação: Representa corretamente os pontos 1, z e z² em coordenadas reais.
Evidência selecionada original:

> Assim, no plano de Argand-Gauss, os três pontos são:
> 1 = (1, 0)
> z = (a, 2)
> z² = (a² + 4, 4a)

### ITA2025Q3_S002_L01 / parity_obstruction
O critério exige 11−2i−2j ímpar. O texto selecionado escreve (6−2i)+(5−2j)=10−2(i+j) e diz que é ímpar. Para i=j=0, a soma é 11 e o lado escrito é 10, que é par. O award de 3 pontos aceita a justificativa errada; concluir corretamente zero não corrige esse passo.
Causa primária: CRITERION_MISINTERPRETATION. Causas adicionais: EVIDENCE_NOT_SUFFICIENT, MISSING_REQUIRED_MICROCLAIM, RATIONALE_OVERREACH.
IDs escolhidos: E4_1, E4_2. Rationale original: A evidência citada satisfaz o critério da pauta: «Observa que 11 - 2i - 2j é sempre ímpar, logo nunca é zero.».
Obrigação: Observa que 11 - 2i - 2j é sempre ímpar, logo nunca é zero.
Evidência selecionada original:

> Ímpar nunca é 0, então não existe termo com x⁰ na expansão, e o coeficiente de x⁰ é 0.

> No produto o expoente de x é (6−2i)+(5−2j) = 10 − 2(i+j), que é ímpar pra qualquer i, j inteiros.

### Fluxo reconstruído e causa raiz
A pauta gerou um critério indeterminado (points=None). O catálogo recuperou spans reais; o modelo selecionou IDs existentes e retornou award/max_points/SATISFIES_CRITERION. A primeira decisão matematicamente incorreta foi essa classificação semântica do modelo. O validador local verificava estrutura, enum, pontos, IDs, literalidade e rationale autorizado, mas não exigia os pré-requisitos de AWARD. A score policy então somava a proposta aceita. Não houve erro na resolução dos IDs ou na soma.
Grounding prova “o aluno escreveu isto”; não prova “isto satisfaz a pauta”. Em Q1, a referência Lean estava verificada, mas a evidência selecionada tinha o sinal errado. Em Q3 e F2Q1, também faltavam microclaims obrigatórios satisfeitos. A rationale fechada podia afirmar satisfação sem que isso fosse verdade; limitar o vocabulário não valida a matemática.

## Gate implementado
Novo módulo: app/confia_lean_auditor/rubric/secondary_award_gate.py; função can_secondary_award. Integração: secondary_adjudicator.enforce_award_eligibility e validate_decisions, depois da validação estrutural/IDs e antes de aceitar pontos. secondary_context.prepare_payload expõe localmente os requisitos da pauta e os resultados de verificação existentes.
- IDs continuam sendo o único contrato de evidência da API. Não se voltou a evidência textual livre.
- Microclaims explicitamente exigidos precisam satisfazer a política existente (locally_verified e dependencies_are_verified); flags são calculadas localmente, sem executar ou modificar Lean.
- Relações matemáticas completas já codificadas na pauta são conferidas no texto selecionado, inclusive equivalências no domínio canônico existente. Grupos expressam requisitos cumulativos e alternativas explicitamente declaradas. Não há IDs de soluções nem valores especiais dos três erros no gate.
- Refutações matemáticas com grounding válido e conflitos de alinhamento já conhecidos bloqueiam AWARD. Erro técnico não é refutação. O contexto de segurança local não é truncado pelo orçamento de recuperação de candidatos.
- O gate examina contexto original para citações, hipóteses, negações e tentativas abandonadas; recortar apenas a equação não apaga o prefixo/sufixo. Negações matemáticas já autorizadas pela regra são preservadas.
- Critérios que explicitamente pedem apenas conclusão continuam aceitando afirmação direta avaliada semanticamente pelo modelo, sem obrigar sintaxe algébrica. Ausência de microclaim não é regra global de zero.
- O gate não chama can_support_rubric_credit, não exige um ExtractedClaim detectado ou alinhamento positivo para todos os créditos e não refaz toda a avaliação semântica. Elegibilidade é condição necessária, não prova de satisfação.
- Uma proposta válida mas inelegível torna-se DENY/0 com INCOMPLETE_FOR_CRITERION ou CONTRADICTS_CRITERION já existentes. A proposta original, razões e versão do gate ficam no trace. Não há retry por veto determinístico nem classificação de resposta inválida por esse veto.
- O contrato moderno também passa pelo gate quando validate_decisions é chamado novamente pela score policy. O leitor de registros textuais históricos permanece compatível; a API ativa continua rejeitando essa forma de resposta.

## Prompt e expected answer
O live utilizou secondary-award-safety-v1. Após o único controle positivo falhar, a revisão final foi versionada para secondary-award-safety-v2, validada somente offline. Ele proíbe usar resultado isolado como substituto de derivação/microclaim, reforça requisitos obrigatórios, sinais/igualdades e contexto de hipótese/negação, preservando conclusões answer-only. O schema continua secondary-evidence-ids-v1; não foi necessário acrescentar reason codes.
Na inspeção, problem.correct_answer não era enviado. Havia expected_bindings duplicando valores já disponíveis na descrição/contrato; prepare_payload deixou de gerar essa duplicação. As relações necessárias para interpretar a pauta e o enunciado foram mantidos. O caminho de leitura de payloads históricos permanece compatível. As oito requisições live foram verificadas para ausência de expected_bindings, fonte completa, IDs internos e contexto local de segurança.

## Preservação da semântica primária
Nenhuma alteração em score_policy, ExtractedClaims, StudentClaims, alignment, canonicalização, Lean, rubric bridge, assets/rubricas ou UI. O deny do secondary mantém mathematical_status=indeterminate e points=None; só suggested_points passa a zero. Coverage, evaluated_score e evaluated_max_score continuam medindo a primeira passagem. Nas oito execuções, os resultados primários, extrações e alignments foram comparados com V4 e permaneceram iguais.

## Controles e live limitado
Os controles foram escolhidos antes do live, em live_selection.json. Positivos: conclusão a=-1,b=3 em palavras; comparação dos limites da mantissa de F2Q5; conclusão dos maximizadores 6 e 7 em F2Q6. Denies: resposta “não sei fazer” em Q4 e cálculo logarítmico incorreto em F2Q5_S024_L04. Os controles avaliam esses critérios específicos, não a correção integral de cada solução.

| Caso | Grupo | Critério | Decisão final | Pontos | Modelo propôs | Veto local | Aceitação |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ITA2025Q1_S014_L04 | false_award | coordinates | deny | 0.0 | award | MISSING_DECLARED_RELATION | True |
| ITA2025Q3_S002_L01 | false_award | parity_obstruction | deny | 0.0 | deny | nenhum | True |
| ITA2025F2Q1_S002_L04 | false_award | reduced_polynomial_form | deny | 0.0 | deny | nenhum | True |
| ITA2025F2Q1_S003_L02 | positive | final_answer | deny | 0.0 | deny | nenhum | False |
| ITA2025F2Q5_S003_L04 | positive | mantissa_between_bounds | award | 2.0 | award | nenhum | True |
| ITA2025F2Q6_S006_L04 | positive | final_answer | award | 2.0 | award | nenhum | True |
| ITA2025Q4_S002_L04 | deny | positive_witnesses | deny | 0.0 | deny | nenhum | True |
| ITA2025F2Q5_S024_L04 | deny | log_power_decomposition | deny | 0.0 | deny | nenhum | True |

8 tentativas de API; 0 respostas inválidas. Resultados persistidos a cada caso. HTTP redigido sem cabeçalhos/credenciais em http/; auditorias completas em results/ e cases/. O motor foi congelado durante as oito execuções. Nenhuma nona execução ou tentativa de melhorar o resultado por reexecução.

### Controle positivo que falhou e ajuste após o live
ITA2025F2Q1_S003_L02 recebeu DENY/INSUFFICIENT_EVIDENCE do modelo para a resposta correta em palavras. O gate não foi solicitado para esse deny e não foi sua causa. O contrato da pauta exige apenas concluir a=-1,b=3, sem microclaim obrigatório. O modelo recusou uma resposta legítima, portanto a aceitação live da tarefa NÃO foi atingida.
A requisição carregava conclusion_only=false, um flag primário cuja semântica original se refere à atribuição de conclusões copiadas, não à exigência de justificativa. Essa ambiguidade pode ter contribuído para a recusa, mas uma execução não prova causalidade. Após terminar os oito casos, prepare_payload passou a produzir answer_only a partir da descrição real da pauta e o wire deixou de expor o flag legado quando existe essa classificação explícita. O prompt v2 também distingue requisitos de cada critério e aceita valores por extenso. Não há upgrade local de DENY para AWARD.
A versão v2 passou por testes offline, incluindo um replay do DENY real que permanece DENY. Esses testes não provam que uma nova chamada live concederia os pontos. A versão exata usada nos oito casos está em live_engine_snapshot/; a versão final inclui o ajuste posterior. Nenhuma nona execução foi feita. Falta autorização para uma nova validação live do controle positivo antes de considerar esta tarefa completa.

## Testes offline
Antes do live: 329 passed, 0 failed, 45 testes novos. Versão final: 332 passed, 0 failed; 48 testes novos no total. Os três testes dos falsos créditos falham antes e passam depois. A suíte relacionada inclui score policy/API, contrato secundário, evidência por IDs, bridge e crédito positivo. Não foi executada a suíte inteira do repositório; falhas históricas HMER/UI/tablet/xfail F2Q6 não foram corrigidas nem contadas como regressões desta tarefa.
Os testes cobrem alvo correto sem derivação exigida; conclusão answer-only; hipótese; negação; tentativa abandonada; requisito ausente; equivalência matemática representável; refutação grounded; conflito/stale binding; erro técnico; preservação de coverage/status; metadata e ausência de retry por veto. Sockets externos são bloqueados e as chaves reais removidas nos testes offline.
Na primeira rodada pós-live, houve uma asserção nova sensível à quebra de linha do prompt (corrigida no teste) e uma falha canonical_form no caminho primário Q8 sem alteração nesta tarefa. A falha Q8 não se reproduziu na checagem focada (6 passed) nem na rodada final completa relacionada (332 passed). A causa não foi estabelecida; canonicalização não foi modificada. Logs dessa rodada foram preservados em post_live_initial_tests.log.

## Limitações e recomendação
O gate é uma barreira determinística para requisitos objetivos, não um provador semântico universal. Fora das relações e contextos representáveis, o modelo ainda pode errar. Frases fora do vocabulário de escopo podem escapar; contexto amplo e equivalência não representável podem causar falso negativo. As regras existentes e microclaims de referência não cobrem todos os métodos corretos.
Exigir os microclaims declarados pode reduzir créditos legítimos anteriormente concedidos quando a primeira passagem não representava a solução; esse custo não foi ocultado nem compensado inflando coverage. Não foram inventadas dispensas de microclaims ou alternativas novas. Uma equivalência representável satisfaz a relação declarada, mas não dispensa outros requisitos explícitos.
No live, apenas dois dos três controles positivos passaram; os dois denies foram preservados. Isso não mede recall geral ou taxa universal de falso crédito. Não se declara maturidade matemática. Recomenda-se revisar o efeito na variedade de métodos antes de nova escala; nenhum batch de 18/502/1000 foi executado nesta tarefa.

## Arquivos e integridade
Arquivos de implementação: app/confia_lean_auditor/rubric/secondary_award_gate.py (novo), secondary_adjudicator.py e secondary_context.py (incremental). Testes: tests/test_secondary_false_credit.py e oito fixtures em tests/fixtures/secondary_false_credit_04/. Este relatório e os artifacts são novos.
git diff --check: OK. HEAD e índice Git inalterados, nenhum staging/commit/push. 362 arquivos de V4 e 1029 arquivos históricos adicionais conferidos por hash. Mudanças preexistentes preservadas; status completo em git_status_after.txt.
Artifacts: `/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/ita1000_v1_2/p0_secondary_false_credit_04`. false_credit_diagnosis.json; implementation.diff; offline_validation.json; live_validation.json; preservation_validation.json. O diff é incremental contra os snapshots anteriores a esta tarefa, não contra HEAD, para não misturar alterações das tarefas anteriores.

## Final live revalidation

P0-SECONDARY-FALSE-CREDIT-04B — 2026-10-29 21:37:48 UTC. **COMPLETE**: os mesmos oito controles foram reexecutados com o código final atual, sem alterações no motor.

Falsos AWARDs: 0/3; controles positivos: 3/3; controles DENY: 2/2; respostas inválidas: 0; retries: 0. Prompt secondary-award-safety-v2. O controle positivo em palavras de F2Q1 foi preservado nesta execução.

Primeira passagem, claims, alignments e coverage preservados; git diff --check OK; nenhum staging, commit ou push. Resultado limitado aos controles já classificados, sem extrapolação para acurácia geral e sem execução de 18/502/1000.

Evidências: `/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/ita1000_v1_2/p0_secondary_false_credit_04b/live_revalidation.json` e `/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/ita1000_v1_2/p0_secondary_false_credit_04b/validation_summary.json`.
