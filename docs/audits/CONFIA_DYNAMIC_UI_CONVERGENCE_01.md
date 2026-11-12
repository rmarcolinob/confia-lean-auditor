# ConfIA Dynamic — convergência da interface 01

Data: 11/11/2026 (America/Fortaleza). Validação técnica encerrada em 12/11/2026 UTC.

Worktree exclusivo: `/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic`.
Branch: `feat/dynamic-correction`. HEAD mantido: `c2985d211ccbe29e9ce45ca1ec25b62e5fcec32a`.
Base solicitada `cb1df6e381fd0214092f33afe554ce506da68c78` confirmada como ancestral.
Nenhum outro worktree consultado, alterado ou utilizado como dependência. Sem `git add` e sem commit.

## 1. Causa da divergência

DY1/DY2 expunham a preparação por `#teacher/dynamic`, dentro do shell genérico de perfis. A lógica de edição dependia de um elemento `#teacher-dynamic` presente desde o carregamento da página. Isso criou uma entrada visual separada da experiência de correção assistida D1–D7.

A fonte de verdade passa a ser a interface existente em `/tme`. A preparação é uma etapa de criação dentro dessa interface. Não foi criada outra home, outro dashboard ou outro workspace.

## 2. Shell antigo afetado

Removidas cirurgicamente de `static/index.html` as quatro integrações exclusivas do Dynamic: stylesheet, link na sidebar, seção de montagem e script.

Em `static/shell.js`, removidos a entrada de título Dynamic, o controle de visibilidade/montagem do painel e as condições exclusivas desse modo. Não houve checkout integral. Após as edições, ambos os arquivos coincidem byte a byte com a base `cb1df6e…`.

Gestão, Aluno, Professor e módulos históricos permanecem no shell genérico. Nenhum deles participa do novo fluxo de preparação.

## 3. Componentes `/tme` reutilizados

- `static/tme/index.html`: header ConfIA, navegação principal, `#app`, shell moderno e carregamento de assets.
- `tme.js`: roteamento, histórico do navegador, estado ocupado, renderização e entrada Nova.
- `secondary-views.js`: `ConfiaTmeViews.Page`; estilos existentes `tme-panel`, `tme-button`, `home-status` e tokens `tme-theme.css`.
- `full-exam.js`: criação e recebimento de avaliação preparada; caminho de questão avulsa permanece disponível.
- `home.js`, `home.css`, `correction-workspace.js`, `correction-workspace.css`, `workspace-report.js` e `full-exam.js`: preservados sem alterações nesta tarefa.

A [comparação SHA-256](assets/confia-dynamic-ui-convergence/preservation-sha256.json) comprova preservação de 16 arquivos: os oito módulos Python Dynamic, seus dois arquivos de testes Python e os seis arquivos compartilhados citados acima.

## 4. Mudanças realizadas

`Nova` e os atalhos `Nova correção` agora abrem duas opções:

- **Avaliação preparada** — Para TME, olimpíadas, vestibulares e avaliações previamente configuradas.
- **Nova atividade ou prova** — Crie questões inéditas e prepare rubricas com o ConfIA.

`static/dynamic.js` foi adaptado para uma instância montada pelo fluxo Nova, recebendo o container, o callback de seleção e o estado ocupado do shell. Foram mantidos os endpoints, payloads de edição/aprovação e as invariantes de revisão existentes.

O conteúdo usa cards para Questão, Preparação, Rubrica e Histórico, com navegação contextual horizontal. “Retomar preparação” permite reabrir questões persistidas. “Nova questão” retorna ao formulário sem remover versões armazenadas.

Leituras atrasadas são invalidadas ao sair da preparação, abrir outra questão ou restaurar o workspace. Durante mutações, a navegação respeita o estado ocupado já utilizado pela plataforma. Os novos assets receberam versão `unified-01`.

## 5. Specialized preservado

Selecionar Avaliação preparada chama o `fullExam.newCorrection()` existente. A alternativa de questão avulsa chama o `newSingleCase()` existente. Captura, associação de páginas, transcrição, auditoria, decisão humana, prova completa e certificação não foram reimplementadas.

Os testes existentes de criação passaram a selecionar Avaliação preparada antes de executar suas verificações anteriores. Assertions sobre IDs, arquivos originais, páginas, pontuação, idempotência, transcrição e workspace foram mantidas. Não houve alteração de expectativas matemáticas ou de certificação para obter aprovação dos testes.

No navegador, a seleção de **TME² — 2ª Fase 2026** abriu o formulário existente de recebimento de prova, com pseudônimo, PDF/imagens e acesso à questão avulsa.

## 6. Dynamic integrado e backend preservado

O fluxo dentro de `/tme` utiliza os contratos existentes para:

1. criar questão com `correction_mode: DYNAMIC` explícito;
2. criar novas versões do enunciado;
3. preparar/regenerar com ConfIA;
4. inspecionar soluções candidatas, métodos alternativos, verificações, avisos e proveniência;
5. gerar/regenerar sugestão de rubrica ou fornecer rubrica docente;
6. editar como nova versão;
7. aprovar explicitamente, reconhecendo os avisos quando exigido;
8. consultar histórico e configuração aprovada.

Nenhum arquivo Python Dynamic foi modificado nesta convergência. As alterações DY2 que já estavam pendentes antes da tarefa foram preservadas, assim como os testes Python. O [status inicial](assets/confia-dynamic-ui-convergence/initial-git-status.txt) diferencia essas alterações preexistentes.

O modo é persistido pelos contratos DY1/DY2. O parâmetro de URL apenas escolhe a entrada visual; não substitui autorização nem define o motor de uma auditoria existente.

## 7. Visual e home

Home, cards e conteúdo existente permanecem iguais. A folha Dynamic está restrita ao container de preparação e às duas escolhas de criação, reutilizando cores, fontes, espaçamentos, bordas, botões e estados do tema ConfIA.

O navegador confirmou header ConfIA, Início/Fila/Nova/Resultados e ausência de Gestão e sidebar antiga visíveis. O aviso de identidade técnica permanece na demonstração local, sem exigir troca de perfil.

Não foi criado `dynamic-workspace.html`. Original / Transcrição / Comparar e o painel ConfIA continuam sendo a infraestrutura compartilhada a receber o grader futuro.

## 8. Rotas

| Rota | Destino |
|---|---|
| `/tme` | Home existente |
| `/tme?view=new` | Escolha do tipo de criação |
| `/tme?view=new&mode=specialized` | Criação de avaliação preparada |
| `/tme?view=new&mode=dynamic` | Formulário e retomada de preparação |
| `/tme?view=new&mode=dynamic&problem_id=…` | Questão persistida e suas versões |
| `/tme?view=queue` | Fila existente |
| `/tme?view=results` | Resultados existentes |

URLs existentes de caso, prova completa e questão da prova continuam funcionando. Voltar/avançar e recarregar uma preparação restauram o documento persistido. `/tme` não foi renomeado; generalizar seu nome é dívida futura.

## 9. Status técnico → apresentação

| Valor interno preservado | Apresentação |
|---|---|
| DRAFT_AI | Sugestão da IA |
| DRAFT_TEACHER | Rascunho do professor |
| TEACHER_EDITED | Revisada pelo professor |
| APPROVED | Aprovada |
| SUPERSEDED | Versão anterior |
| PENDING / RUNNING | Aguardando preparação / Preparando |
| READY_FOR_REVIEW | Pronta para revisão |
| REVIEW_REQUIRED | Revisão necessária |
| FAILED | Preparação não concluída |
| VERIFIED_WITHIN_SCOPE | Verificada no escopo disponível |
| PARTIALLY_VERIFIED | Verificação parcial |
| CONTRADICTED | Inconsistência identificada |
| UNRESOLVED / UNVERIFIED | Verificação pendente / Não verificada |
| FORMAL_NOT_ATTEMPTED | Verificação formal não executada |
| CHECKED_WITHIN_SCOPE | Verificações limitadas concluídas |
| HUMAN_REVIEW_REQUIRED | Revisão docente necessária |
| UNAVAILABLE | Verificação indisponível |

Capacidades de verificação também têm nomes legíveis. Referências de soluções e critérios nos avisos usam seus títulos quando disponíveis. O texto original dos avisos, códigos e proveniência permanece em detalhes expansíveis. O navegador confirmou ausência dos enums técnicos principais no texto visível com esses detalhes fechados.

Aprovar a rubrica não converte a preparação em verificada e não remove avisos. Não há indicação de certeza formal quando ela não existe.

## 10. Testes

| Escopo | Resultado | Evidência |
|---|---|---|
| Backend DY1/DY2 | **68 passed** | [python-dynamic.txt](assets/confia-dynamic-ui-convergence/python-dynamic.txt) |
| JavaScript completo | **538 passed** | [js-regression.txt](assets/confia-dynamic-ui-convergence/js-regression.txt) |
| Python compartilhado/TME/D1–D7/certificação | **505 passed, 2 failed** | [python-platform.txt](assets/confia-dynamic-ui-convergence/python-platform.txt) |
| Preservação de backend e componentes compartilhados | **16 hashes idênticos** | [preservation-sha256.json](assets/confia-dynamic-ui-convergence/preservation-sha256.json) |
| Sintaxe e whitespace | `node --check` e `git diff --check` sem erros | Verificação local |

Os 538 testes JS incluem os 11 testes DY1/DY2 atualizados para montagem no shell e nomenclatura em português, além de oito testes novos em `tests/js/test_dynamic_ui_convergence.cjs`.

A nova cobertura verifica ambas as entradas, ausência da integração antiga, criação explícita DYNAMIC, preparação, sugestão, edição, aprovação condicionada aos avisos, histórico, retorno à home/fila/resultados, deep links, retomada, estado ocupado, erro de leitura e invalidação de respostas atrasadas, inclusive ao restaurar workspace.

Comandos principais, executados na raiz deste worktree:

```sh
node --test --test-reporter=tap tests/js/test_*.cjs
PYTHONPATH=app .venv/bin/python -m pytest tests/test_dynamic_dy1.py tests/test_dynamic_dy2.py -q
PYTHONPATH=app .venv/bin/python -m pytest tests/test_assessments.py tests/test_submissions.py tests/test_transcriptions.py tests/test_teacher_decisions.py tests/test_submission_audits.py tests/test_submissions_ui.py tests/test_reproducibility.py tests/test_tme_pilot.py tests/test_tme_photo_errors.py tests/test_tme_demo_auth.py tests/test_tme_home_summary.py tests/test_tme_navigation.py tests/test_tme_problem_catalog.py tests/test_tme_accepted_integration.py tests/test_tme_audit_view.py tests/test_tme_full_exam.py tests/test_tme_question_audit.py tests/test_tme_review_workspace.py tests/test_tme_human_confirmation.py tests/test_tme_reanalysis.py tests/test_tme_certification.py tests/test_tme_finalization.py tests/test_tme_synthetic_demo.py -q
```

## 11. Regressões e falhas conhecidas

As duas falhas Python são as mesmas já documentadas no relatório DY2:

- `test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`;
- `test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved`.

Os artefatos da execução atual registram tentativa de checkout Mathlib na revisão `8f9d9cff6bd728b17a24e163c9402775d9e6a365`, seguida de `external command 'git' exited with code 1`. Isso produz `technical_error` em vez dos certificados esperados. [Evidência atual](assets/confia-dynamic-ui-convergence/formal-failure-evidence.json).

O diagnóstico coincide com a evidência anterior DY2, que já reproduzia as falhas sem o Dynamic. Não foram alteradas expectativas, dependências Lean ou arquivos de outro worktree. Esta entrega não declara a suíte Python inteiramente verde e não resolve a instalação Mathlib.

## 12. Validação no navegador

Servidor local em `127.0.0.1:8768`, auth de demonstração explicitamente habilitada apenas em desenvolvimento. Runtime exclusivo deste teste em `runtime/ui-convergence/{dynamic,cases,exams}`. Provider real OpenAI, modelo `gpt-4.1`; nenhuma chave incluída nas evidências.

**Cenário Specialized:** home → Nova → Avaliação preparada → seleção TME² → formulário de recebimento existente.

**Cenário Dynamic:** mesma home → Nova → Nova atividade ou prova → título/enunciado/10 pontos → criar → preparar → inspecionar solução candidata e métodos alternativos/avisos → sugerir rubrica → editar descrição do primeiro critério → salvar V2 → reconhecer avisos → aprovar.

**Cenário navegação:** preparação → Início → Fila → Resultados → Nova → retomar preparação aprovada. Todas as rotas ficaram sob `/tme`; nenhuma troca de perfil ou navegação para Gestão.

Persistência confirmada pela API: documento revisão 7, enunciado V1, preparação V1 em REVIEW_REQUIRED, rubrica V1 DRAFT_AI e V2 APPROVED, configuração aprovada V4, reconhecimento de avisos registrado e `correction_available=false`. A consulta `/current` devolve a preparação exata do pacote aprovado. [Resumo verificável](assets/confia-dynamic-ui-convergence/browser-validation.json).

## 13. Screenshots

1. [Home preservada](assets/confia-dynamic-ui-convergence/01-home.jpg).
2. [Duas entradas de Nova](assets/confia-dynamic-ui-convergence/02-nova.jpg).
3. [Avaliação preparada existente](assets/confia-dynamic-ui-convergence/03-avaliacao-preparada.jpg).
4. [Criação de questão](assets/confia-dynamic-ui-convergence/04-criacao.jpg).
5. [Solução de referência candidata](assets/confia-dynamic-ui-convergence/05-preparacao.jpg).
6. [Rubrica com edição docente persistida](assets/confia-dynamic-ui-convergence/06-rubrica-editada.jpg).
7. [Aprovação, histórico e convergência futura](assets/confia-dynamic-ui-convergence/07-aprovacao-historico.jpg).
8. [Fila no mesmo shell](assets/confia-dynamic-ui-convergence/08-fila.jpg).
9. [Resultados no mesmo shell](assets/confia-dynamic-ui-convergence/09-resultados.jpg).
10. [Preparação retomada no ConfIA](assets/confia-dynamic-ui-convergence/10-preparacao-unificada.jpg).

## 14. Limitações explícitas

O usuário autorizou preservar o backend e adiar tipo persistido (lista/atividade/prova) e agrupamento de várias questões. A tela explica que, nesta etapa, prepara uma questão por vez, com título, enunciado e pontos. Não há seletor que simule persistência inexistente.

A prova real mostrou uma limitação da geração DY2: a IA emitiu um aviso de domínio inferido embora “soluções reais” estivesse explícito no enunciado. A UI preservou esse aviso como evidência. A edição docente explicitou o domínio e separou justificativa de execução para reduzir a sobreposição sugerida. A aprovação de demonstração não apaga o aviso nem transforma a referência em prova formal.

Ainda não existe correção Dynamic de respostas, associação de múltiplas questões Dynamic a uma avaliação nem registros Dynamic de QuestionAttempt/AuditRun. Não foram implementados grader, reviewer, reconciliation ou nova UI de aluno.

A validação de navegador usou demonstração local e uma questão matemática de teste; não constitui homologação multiusuário em produção. As duas integrações Lean reais permanecem bloqueadas pela dependência externa descrita acima.

## 15. Recomendação para DY3

A convergência de produto/UI está concluída. DY3 pode partir da preparação e aprovação existentes, reutilizando o mesmo shell e workspace D1–D7. A integração futura deve conservar a ligação de versões e proveniência ao percorrer:

`Dynamic Problem → Question/Assessment → QuestionAttempt → TranscriptionVersion → AuditRun → HumanDecision → FinalCorrection`.

O workspace deve consumir resultados de auditoria e revisão humana sem exigir outra plataforma ou duplicação visual. A generalização de `/tme`, a entidade de atividade e o agrupamento de questões continuam decisões futuras explícitas. O bloqueio Mathlib deve ser tratado separadamente antes de declarar homologação formal completa.

Esta tarefa encerra a etapa de UI pré-DY3; DY3 não foi iniciado.

**READY_FOR_DYNAMIC_DY3_UNIFIED_UI**
