# D5 — Decisão humana por questão

## 1. SHA inicial e escopo

Worktree: `~/Documents/confia-lean-auditor-tme-december-integration`. Branch: `feat/tme-december-integration`. SHA inicial: `0a48c6c410bfdc3a397055d1cd05902113b363bc`. Árvore inicialmente limpa. Implementação de D5 sobre D1–D4, sem `git add` e sem commit.

D5 acrescenta homologação por questão. Não implementa fechamento global, envio da nota da prova, estatística, certificação, Dynamic ou P4/P5. Não altera motor matemático, PautaEngine, Lean/checkers, experimental, benchmarks ou CSS.

## 2. Modelo HumanDecision e auditoria dos equivalentes

O domínio já possuía `tme.models.EvaluatorDecision`: snapshot da pontuação, avaliador, data e hashes de auditoria, mas com arquivo único e encerramento `DECIDED`. Também possui `teacher_decisions.TeacherDecision`, cujo fluxo institucional DRAFT/FINALIZED/RELEASED depende de escola/turma e não oferece histórico append-only por questão do modo TME.

D5 reutiliza `EvaluatorDecision` como base de `HumanDecision` e `teacher_decisions.models.Points` para validação numérica. Amplia o modelo com ID próprio, question_attempt, assessment, participante pseudônimo, submissão da prova, versão exata da transcrição, AuditRun, modo/versão do motor, snapshot de review, delta, tipo e `supersedes_decision_id`. O revisor usa a identidade autenticada ou `tme-demo-evaluator`, sem nome civil de participante.

`HumanRubricDecision[]` prepara o contrato futuro; fica vazio nesta entrega. Ajuste implementado é da nota total. A dependência é do contrato normalizado CorrectionEngine/AuditRun, sem condicional P1/P2/P3. O motor atual informa `TME_CURRENT`; os campos de modo/versão não são enumerados apenas para esse motor.

## 3. Snapshots

Cada decisão guarda `suggested_points`, `final_points`, `max_points`, `adjustment_delta`, motivo, avaliador, instante, AuditRun, versão da leitura e hashes de fonte/resultado. `suggested_points` representa o snapshot de `suggested_score`; `final_points`, a nota final humana da questão. A interpretação histórica não depende de recalcular o motor.

Também persiste `review_required_snapshot` e `review_reasons_snapshot`. ConfIA 15, humano 18 e delta +3 permanecem distintos. Nenhum AuditRun é sobrescrito pela homologação.

## 4. Aceitar sugestão

`ACCEPT_SUGGESTION` exige auditoria atual, COMPLETED, pontuação disponível e versão correspondente à leitura corrente. Nota humana recebe a sugestão e delta zero. Aceitação não transforma ausência de score em zero. É necessário reabrir antes de trocar uma confirmação corrente.

## 5. Ajustar nota

`ADJUST_SCORE` recebe nota final decimal entre zero e o máximo da questão, com até duas casas, e calcula `final − suggested`. Rejeita NaN, infinito, vazio, negativos, acima do máximo e precisão excedente. Limites e razão são validados no backend; o formulário também orienta e valida antes do envio. Delta positivo e negativo são cobertos.

## 6. Motivos

Diferença não zero exige texto livre não vazio após remover espaços nas extremidades; limite de 2.000 caracteres. Aceitação ou ajuste numericamente igual pode omitir motivo. Não foi criada taxonomia artificial de categorias.

## 7. Confirmação

O workspace projeta `CONFIRMED` somente quando a decisão corresponde à leitura e à auditoria correntes e não houve reabertura/invalidação. Navegação mostra check e nota final; painel separa ConfIA, final e ajuste, além dos detalhes da decisão.

O estado operacional da QuestionAttempt é a projeção `workspace.state`/`question_states`, não uma flag mutável gravada no CorrectionCase legado. Isso impede que `DECIDED` bloqueie a correção de leitura ou permaneça válido após mudança da fonte. O fluxo legado continua disponível para casos fora da prova completa.

## 8. Reabertura

`Reabrir questão` acrescenta registro próprio à cadeia. A decisão anterior permanece íntegra e passa a histórica; estado volta a READY/REVIEW conforme a análise corrente. Nova homologação gera novo ID, com referência à decisão anterior. Reabrir não altera sugestão nem análise.

## 9. Invalidação e concorrência

Nova versão de leitura invalida a confirmação corrente, mantém a antiga no histórico e exige reanálise. Novo AuditRun exige nova homologação, inclusive quando a nota se mantém igual. Auditoria FAILED, stale ou sem score bloqueia tanto aceitar quanto ajustar; D5 não permite homologação manual sobre falha.

O POST explicita AuditRun, TranscriptionVersion e última decisão conhecida. Conflitos retornam HTTP 409. Chave de execução permite repetição idempotente do mesmo pedido; reutilizá-la com outro conteúdo conflita. Repetir uma confirmação histórica devolve seu recibo sem restaurar sua validade corrente.

A ordem dos locks é questão → prova → submissions. Auditorias de produto compartilham o lock da questão. A publicação final da decisão/reabertura usa o lock exclusivo do SubmissionStore e revalida a leitura mais recente e o AuditRun mais recente. Isso também cobre os endpoints genéricos, que não usam o lock da questão. O lock não envolve a execução matemática: edição durante auditoria continua preservando um resultado stale, como em D4.

## 10. Histórico e dados para certificação

Registros novos ficam em `tme_cases/<case>/human_decisions/000001.json`, etc. Escrita atômica sem sobrescrita, sequência, hash anterior e digest do registro permitem detectar corrupção. GET apenas projeta estado; não grava invalidações. Decisões, reaberturas, leituras e auditorias duráveis permitem reconstruir V1 → A1 → H1 e V2 → A2 → H2.

Cada decisão histórica expõe `certification`: nota humana, sugestão ConfIA, erro absoluto, erro assinado, ajuste, review e versão da auditoria/motor. Convenção: **erro assinado = ConfIA − humano**, **ajuste = humano − ConfIA**. Portanto 15/18 gera erro −3 e ajuste +3. Nota humana é referência registrada, não declaração automática de gold validado. Métricas agregadas ficam para D7.

## 11. APIs

| Operação | Endpoint |
| --- | --- |
| Aceitar ou ajustar | `POST /tme/cases/{case_id}/decision` |
| Decisão humana corrente ou null | `GET /tme/cases/{case_id}/decision` |
| Histórico, eventos e última decisão | `GET /tme/cases/{case_id}/decisions` |
| Reabrir | `POST /tme/cases/{case_id}/reopen` |
| Estado, análises, versões, decisões e totais | `GET /tme/question-attempts/{case_id}/workspace` |

O endpoint existente de decisão aceita o contrato D5 em provas completas, preservando o contrato legado nos casos antigos. Não foram criados endpoints separados redundantes de aceitar/ajustar. Propriedade e autenticação continuam obrigatórias fora do modo demo explícito; respostas usam no-store.

## 12. UI

Ações foram inseridas no painel direito após o resumo ConfIA. Mantidos header, paleta, tipografia, abas, Original/Transcrição/Comparar, pauta, alertas, botões e espaçamentos existentes. Nenhum CSS foi modificado. Cache versions dos scripts passam a `december-d5`.

Painel confirmado mostra sugestão, final, delta ou “Sugestão aceita”, motivo, revisor/data e detalhes técnicos expansíveis. Histórico humano é acessível na área de histórico. `review_required` aparece como alerta e não impede decisão consciente. RUNNING e edição em andamento impedem publicação; duplo clique é protegido; conflito atualiza o workspace e pede revisão da versão corrente. Falha de transporte conserva a chave do pedido para repetição segura.

## 13. Totais

Sugestão parcial permanece a soma das auditorias correntes válidas. Total confirmado soma apenas decisões humanas correntes; seu denominador soma os máximos das questões confirmadas. Também informa máximo da prova, quantidade confirmada e restante. Não se chama nota final da prova.

Exemplo observado: Q1 aceita 20 e Q2 ajustada de 15 para 18 → ConfIA parcial 35/100; confirmado 38/40, 2/5 questões. Invalidar Q2 retira seus 18 do total corrente, preservando o histórico.

## 14. Eventos

Disponíveis: `suggestion_accepted`, `score_adjusted`, `adjustment_reason_recorded`, `question_confirmed`, `question_reopened`, `human_decision_superseded`, `confirmation_invalidated_by_transcription_change`, `confirmation_invalidated_by_new_audit`.

Cada evento contém assessment, participante pseudônimo, submissão, questão, versão da leitura, AuditRun, HumanDecision, timestamp, modo/versão do motor, sugestão, final e delta. Eventos são projeções determinísticas dos registros duráveis, não mensagens já entregues a um broker externo. IDs de invalidação usam a primeira versão/análise posterior para estabilidade.

## 15. Testes Python D5

**44 PASS em 22,08 s** no conjunto focado D2–D5; 23 casos da nova suíte D5 (incluindo parametrizações).

A nova suíte cobre snapshot, aceitar, ajuste, razão, limites, precisão, deltas, status, reabertura, nova decisão, histórico, invalidação por leitura/análise, review, failed, stale, concorrência, isolamento, totais, eventos, pseudônimo, autenticação, corrupção, duplo envio e revisor diferente. Inclui quatro combinações de concorrência: leitura/auditoria genérica publicadas entre snapshot e append durante confirmar/reabrir.

Durante desenvolvimento, corrigido parsing de timestamp `Z` no runtime Python do projeto. Nenhum teste anterior foi enfraquecido.

## 16. Testes JavaScript

Baseline D4 executado: **505 PASS / 0 FAIL**. Suíte completa D5: **510 PASS / 0 FAIL**, zero skip/cancel (1,55 s). Cinco testes novos exercitam aceitação, controle de ajuste, validações, review, diferença/final, histórico/reabertura, navegação/totais, invalidação/reanálise, concorrência e failed. Fixture JS ampliada somente para simular as respostas humanas; navegador usou backend e motor reais.

## 17. Regressões

**854 PASS, 2 FAIL preexistentes, 1 SKIP em 247,89 s** no recorte de 25 arquivos. Inclui D1–D5, assessments, submissions, transcriptions, recognition, TME, decisões institucionais, autenticação, submission_audits, Pauta e bridges estáveis. Nenhuma falha nova. Log completo: [python-regression.txt](assets/tme-december-d5/python-regression.txt).

As duas falhas Lean foram reproduzidas separadamente em exportação limpa do SHA inicial, sem alterações D5 (**2 failed em 2,43 s**):

- `test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved`;
- `test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`.

Diagnóstico persistido: tentativa de clone de Mathlib, seguida de `external command 'git' exited with code 128`. Dependência indisponível impede os certificados/refutações esperados. Evidências: [reprodução limpa](assets/tme-december-d5/lean-baseline.txt) e [stderr do artefato](assets/tme-december-d5/lean-diagnostic.txt). Não corrigido nesta branch. O skip do recorte é o teste que depende de artefato local V2; existe cobertura portátil correspondente.

Uma execução intermediária da regressão foi interrompida após 446 passes para reforçar a publicação concorrente; ela não é o resultado final. Fonte Python ficou estável durante cada execução final, preservando o fingerprint de auditoria.

## 18. Validação no navegador

Execução real em servidor local, com modo demo explícito e `CONFIA_TME_QUESTION_USE_LEAN=0`, respeitando a indisponibilidade local de Mathlib. Motor estável real, sem mock de nota. PDF sintético de quatro páginas; captura inicial de Q2 omite o item a que existe no original, permitindo correção real de leitura e reanálise. Fixtures matemáticas do repositório não foram alteradas.

- **A:** importar/analisar Q1 → 20/20 → aceitar → Confirmada 20/20.
- **B:** importar/analisar Q2 → 15/20 com review → tentativa de ajustar sem motivo bloqueada → 18 com “Crédito parcial após conferência da estratégia no original.” → ConfIA 15 / Final 18 / +3.
- **Reabertura adicional:** reabrir Q1 → decisão histórica → aceitar novamente → novo ID, Q2 intacta.
- **C:** editar leitura de Q2 → confirmação removida do corrente, 18 histórico → reanalisar → nova sugestão 20, ainda sem confirmação → aceitar → nova decisão 20, antiga 15/18 preservada.
- **D:** editar Q1 → Q1 exige reanálise; Q2 continua confirmada 20 e Q3 pendente. Dados de Q2 não se alteram.

Estado final da demonstração é intencionalmente Q1 stale/não confirmada e Q2 confirmada 20; total confirmado 20/20, 1/5. Console sem mensagens de erro na inspeção. Servidor encerrado após a validação.

Verificação de persistência compara SHA-256 do original, leituras, auditorias e primeiras decisões antes/depois, além do isolamento integral de Q2 ao editar Q1. As oito classes de evento foram observadas. Prova local em `persistence-check.json`. A mesma checagem de hashes e estado foi repetida e aprovada após o hardening final de concorrência, sem regravar os artefatos da demonstração.

## 19. Screenshots e evidências

Pasta: [assets/tme-december-d5](assets/tme-december-d5/).

| Evidência | Arquivo |
| --- | --- |
| Q1 aceita | [q1-accepted.jpg](assets/tme-december-d5/q1-accepted.jpg) |
| Q2 ajustada | [q2-adjusted.jpg](assets/tme-december-d5/q2-adjusted.jpg) |
| ConfIA 15, final 18, +3 e motivo | [q2-decision-details.jpg](assets/tme-december-d5/q2-decision-details.jpg) |
| Q1 reaberta | [q1-reopened.jpg](assets/tme-december-d5/q1-reopened.jpg) |
| Q2 invalidada após edição | [q2-confirmation-invalidated.jpg](assets/tme-december-d5/q2-confirmation-invalidated.jpg) |
| Decisão anterior preservada | [q2-human-history.jpg](assets/tme-december-d5/q2-human-history.jpg) |
| Nova análise sem confirmação automática | [q2-new-audit-unconfirmed.jpg](assets/tme-december-d5/q2-new-audit-unconfirmed.jpg) |
| Q2 preservada após editar Q1 | [q2-isolated-after-q1-edit.jpg](assets/tme-december-d5/q2-isolated-after-q1-edit.jpg) |
| Hashes, estados, decisões e eventos | [persistence-check.json](assets/tme-december-d5/persistence-check.json) |
| Testes e reprodução Lean | [test-results.txt](assets/tme-december-d5/test-results.txt) |

## 20. Arquivos modificados

- `app/confia_lean_auditor/tme/human_decisions.py`: modelo, ledger, regras, concorrência e projeção humana.
- `app/confia_lean_auditor/tme/correction_engine.py`: lock compartilhado da operação por questão.
- `app/confia_lean_auditor/tme/question_review.py`: decisões, estados, totais, eventos e histórico no workspace.
- `app/confia_lean_auditor/tme/router.py`: reaproveitamento GET/POST de decisão.
- `app/confia_lean_auditor/tme/exam_router.py`: histórico e reabertura.
- `app/confia_lean_auditor/static/tme/tme.js`: ações, detalhes, histórico e totais humanos.
- `app/confia_lean_auditor/static/tme/correction-workspace.js`: navegação confirmada e nota final.
- `app/confia_lean_auditor/static/tme/workspace-report.js`: encaixe do painel humano.
- `app/confia_lean_auditor/static/tme/index.html`: cache dos scripts.
- `tests/test_tme_human_confirmation.py`: regressão de domínio/API/concorrência.
- `tests/js/test_human_confirmation.cjs` e `tests/js/exam-fixture.cjs`: cobertura da UI.
- Este relatório e `docs/audits/assets/tme-december-d5/`: evidências.

## 21. Riscos e limites

- Estado corrente é projetado: consumidores devem usar o workspace/API de decisão corrente, não interpretar o status imutável CONFIRMED de uma decisão histórica como validade atual.
- Ledger e locks são locais ao armazenamento em filesystem já usado pelo projeto. D5 não cria transação distribuída, fila de eventos ou mecanismo de retenção externa. A publicação serializa escrita humana contra escrita de leitura/auditoria; leituras concorrentes podem refletir instantes diferentes, e o POST revalida.
- Hashes detectam inconsistência interna; não são assinatura digital nem impedem administrador de reescrever toda a cadeia.
- A varredura de auditorias segue a arquitetura local existente; indexação/escala e fechamento global ficam fora de D5.
- Ajuste por critério está preparado no modelo, mas não editável. Review requer julgamento do professor; confirmação humana não prova correção matemática.
- Evidências visuais validam o fluxo atual em demo. Mathlib segue indisponível para os dois testes Lean locais; as demais verificações discriminam essa limitação.

## 22. Comandos e veredito

Comandos executados no worktree (Python solicitado pelo usuário):

```sh
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_human_confirmation.py tests/test_tme_reanalysis.py tests/test_tme_question_audit.py tests/test_tme_review_workspace.py
/usr/local/bin/node --test tests/js/*.cjs
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_human_confirmation.py tests/test_tme_reanalysis.py tests/test_tme_question_audit.py tests/test_tme_review_workspace.py tests/test_tme_full_exam.py tests/test_submissions.py tests/test_transcriptions.py tests/test_recognition.py tests/test_recognition_invariants.py tests/test_mathpix_strokes.py tests/test_tme_pilot.py tests/test_tme_photo_errors.py tests/test_tme_home_summary.py tests/test_tme_demo_auth.py tests/test_assessments.py tests/test_teacher_decisions.py tests/test_core_auth.py tests/test_core_institutional.py tests/test_tme_accepted_integration.py tests/test_submission_audits.py tests/test_pauta_engine.py tests/test_tme2_p1_pauta_bridge.py tests/test_tme2_p2_pauta_bridge.py tests/test_rubric_bridge.py tests/test_public_audit_boundary.py
```

Reprodução das falhas no SHA inicial: exportação `git archive 0a48c6c410bfdc3a397055d1cd05902113b363bc` em `/private/tmp/confia-d5-baseline`, seguida do mesmo Python com `PYTHONPATH=app -m pytest -q tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline` dentro dessa exportação. Não altera checkout nem index.

Verificações finais: `git diff --check`, `git diff --cached --stat`, `git rev-parse HEAD`, `git status --short`. Nenhum staging ou commit realizado.

READY_FOR_DECEMBER_D6
