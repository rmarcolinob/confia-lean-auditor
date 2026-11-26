# D6 — Fechamento global da correção

## 1. SHA inicial

Worktree: `~/Documents/confia-lean-auditor-tme-december-integration`. Branch: `feat/tme-december-integration`. SHA inicial: `df6e20ebf51c89649ee24793c030949e3c27da60`, com D5 commitado e árvore limpa. Não foi executado `git add` nem criado commit nesta etapa.

## 2. FinalCorrection e domínio existente

Auditados `EvaluatorDecision`/`HumanDecision` do TME, `teacher_decisions.TeacherDecision`, `CorrectionStatus` institucional e `ExamSubmission`. As decisões existentes fecham uma questão/submissão individual; nenhuma agrega decisões de uma prova com histórico de reabertura. O status RECEIVED do ExamSubmission descreve o recebimento imutável, e o CorrectionStatus institucional descreve o fluxo individual até publicação de resultado.

D6 reutiliza HumanDecision, Points/Decimal, integridade SHA-256, escrita atômica e locks dos stores. Introduz `FinalCorrection` para o agregado que faltava: avaliação, submissão, participante pseudônimo, total sugerido congelado, total humano, ajuste, máximo, contagens, avaliador, timestamp, versão, referência anterior, digest do resumo e snapshots por questão. Não duplica o fluxo institucional de liberação de resultados.

`ClosureStatus` distingue IN_PROGRESS, READY_TO_FINALIZE, FINALIZED e REOPENED no resumo. `ExamDetail.correction_status` e a listagem expõem FINALIZED/REOPENED; prontidão detalhada pertence ao resumo. O manifesto de captura conserva RECEIVED e seus bytes originais.

## 3. Snapshot da prova

Cada `ConfirmedQuestion` preserva QuestionAttempt, ordem, problema, TranscriptionVersion, AuditRun, HumanDecision ID, sugestão, final, delta, máximo, review e modo/versão do motor. Inclui a HumanDecision completa, com motivo, revisor, data e hashes da fonte/resultado.

Validadores conferem vínculos, limites, contagens, escopo, totais e consistência entre a linha e a decisão incorporada. O fechamento continua interpretável após reabertura ou alteração de uma questão, sem recalcular matemática.

## 4. Readiness

O backend valida o conjunto exato de itens da avaliação, ordem e limites. A definição e a fonte congelada precisam continuar íntegras. Cada questão deve ter leitura atual, análise corrente COMPLETED com pontuação e decisão humana corrente correspondente.

O resumo identifica a questão e a razão: leitura pendente, análise pendente, análise anterior desatualizada, falha técnica, ausência de pontuação ou falta de homologação. Decisão invalidada não conta como confirmação. Inconsistência estrutural, fonte corrompida ou conjunto de questões divergente falha de forma fechada; não é tratado como prova completa.

Todas as questões configuradas na avaliação são obrigatórias: o modelo atual não possui flag de item opcional. D6 não introduz exceções para P4/P5 nem finalização parcial. É possível usar uma avaliação legitimamente configurada com Q1–Q3, como na demonstração.

## 5. Summary

`GET .../correction` reúne prontidão, razões de bloqueio, tabela, totais, snapshot digest, estado, fechamento corrente, histórico, eventos e linhas para consulta futura de gold.

Tabela: Questão | ConfIA | Final | Ajuste | Status. Questões com decisão corrente sobre review aparecem como **Confirmada após revisão**. Pendências oferecem atalho para a questão. O resumo usa dados calculados pelo backend; o frontend apenas formata números e textos.

## 6. Totais

`suggested_total` soma apenas análises atuais COMPLETED com score. Ausência de qualquer sugestão é null; soma parcial aparece explicitamente incompleta. Zero produzido por análise válida continua zero.

`final_total` soma apenas HumanDecisions correntes válidas. Antes da completude, é rotulado Confirmado parcial. `total_adjustment` só é calculado quando sugestão e confirmação estão completas. Na FinalCorrection: `final_total = Σ final_score`, `suggested_total_snapshot = Σ suggested_score` e `total_adjustment = final_total − suggested_total_snapshot`.

Política herdada de D5: ausência técnica de sugestão bloqueia homologação e, consequentemente, fechamento. Não há nota manual sobre FAILED/null e não há conversão silenciosa em zero.

## 7. Ajustes e revisão

O snapshot e a tabela mostram delta por questão, total e quantidade de questões ajustadas. A contagem review inclui questões com alerta do ConfIA, mesmo quando o humano as confirmou. `unconfirmed_review_question_count` distingue as que ainda estão em revisão; `pending_question_count` inclui todas as não confirmadas.

Demonstração v1: Q1 20→20, Q2 15→18 (+3), Q3 20→19 (−1). ConfIA 55/60, final 57/60, ajuste +2; duas questões ajustadas e uma confirmada com review.

## 8. Finalizar

O resumo mostra `Finalizar correção`, habilitado somente quando apto. Essa ação apresenta uma confirmação explícita com quantidade de questões e total. `Confirmar finalização` envia a identidade do snapshot apresentado e uma chave idempotente.

O backend revalida, grava um registro atômico de fechamento e projeta FINALIZED. As gravações de leitura, aceite, reconhecimento, auditoria, decisão, reabertura individual e associação passam a exigir reabertura global explícita. O bloqueio existe no backend, além dos controles desabilitados na UI.

## 9. Concorrência e idempotência

O digest esperado cobre definição da avaliação, associação, linhas/IDs/decisões correntes e ciclo de fechamento. Nova HumanDecision, transcrição, auditoria ou reabertura torna o resumo anterior incompatível e retorna 409. Uma nova confirmação nunca fecha um snapshot diferente daquele apresentado.

Finalize/reopen adquirem locks na ordem prova → submissions exclusivo. As decisões D5 já seguram o lock da prova; os caminhos genéricos de transcrição/auditoria usam o mesmo lock de submissions e verificam o ledger global sem adquirir o lock da prova novamente. Auditoria verifica antes da execução e na publicação: se começou antes do fechamento, não consegue publicar depois dele.

Mesmo pedido/chave retorna a FinalCorrection original. Outra carga com a mesma chave conflita. Uma prova já finalizada recebe conflito coerente em novo pedido. Replay histórico não restaura um fechamento reaberto. Falhas de transporte conservam a chave no frontend; duplo envio é bloqueado visualmente e serializado no servidor.

## 10. Reabrir

`Reabrir correção` requer confirmação explícita e o ID do fechamento corrente. Acrescenta registro de reabertura; não altera a FinalCorrection anterior nem as decisões das questões. O status passa a REOPENED. Se nenhuma questão for alterada, a prova continua apta para nova versão; se houver mudança, as regras D4/D5 exigem reanálise/homologação conforme o caso.

Novo fechamento incrementa `version` e referencia `previous_final_correction_id`.

## 11. Histórico

Ledger append-only em `tme_exams/<exam_id>/finalizations/000001.json`, etc. Cada registro tem sequência, hash anterior, digest, ator, chave/hash do pedido e eventos. Fechamento, reabertura e tentativa bloqueada são operações distintas. Não há ponteiro mutável separado capaz de divergir do histórico.

A UI oferece `Histórico de fechamento`, com versões, data, avaliador, totais e tabela congelada por questão. GET não cria eventos ou versões. A verificação local confirmou que o primeiro fechamento e os artefatos anteriores permaneceram byte a byte idênticos após a versão 2.

## 12. APIs

| Operação | Endpoint |
| --- | --- |
| Prontidão, resumo, fechamento corrente, histórico, eventos, gold rows | `GET /tme/exam-submissions/{exam_id}/correction` |
| Finalizar o snapshot esperado | `POST /tme/exam-submissions/{exam_id}/correction/finalize` |
| Reabrir o fechamento corrente | `POST /tme/exam-submissions/{exam_id}/correction/reopen` |

Não foram criados GETs redundantes para cada parte do mesmo agregado. Autorização existente do avaliador e no-store preservados. O detail/list de provas inclui estado operacional e metadados do fechamento quando aplicável.

## 13. UI e preservação visual

Resumo e visualização final foram acrescentados ao `full-exam.js`, dentro do shell existente. Reutilizados Page, cards, tabela, botões e alertas. Nenhum CSS foi alterado; header, paleta, tipografia, navegação e painéis das questões permanecem.

Ações de prova completa agora usam o agrupamento existente `.actions`: uma regra antiga ocultava botões diretos de `.workspace-actions` em tela estreita, pois o fluxo avulso tinha um rodapé alternativo. A tabela de fechamento usa um contêiner com rolagem horizontal, sem a classe da fila que esconde tabelas em mobile. Essas correções foram motivadas pela validação real no navegador.

Home e fila reutilizam a seção Provas recebidas, exibindo Finalizada, total final, ajustes e data. Os indicadores históricos de casos avulsos da Home mantêm sua semântica; a prova completa aparece identificada na seção própria. Não foi criado frontend novo nem PDF.

## 14. Eventos

Registrados de forma durável junto à operação: `finalization_requested`, `finalization_blocked`, `correction_finalized`, `correction_reopened` e `final_correction_superseded`.

O evento de fechamento inclui avaliação, participante pseudônimo, submissão, ID do fechamento, timestamp, quantidade de questões, sugestão, total humano, delta, contagens de ajuste/review, modos/versões de motor e HumanDecision IDs. Pedido bloqueado inclui motivo e questões impeditivas. A reabertura inclui ator e fechamento reaberto.

Um GET de resumo ou botão desabilitado não gera evento de tentativa no servidor. `finalization_requested/blocked` são registrados quando chega um POST de finalização, inclusive com snapshot obsoleto. Não há entrega para broker externo nesta etapa.

## 15. Dados para gold humano

`gold_rows` do fechamento corrente fornece participant_code, assessment, submission, fechamento/versão, questão/problema, sugestão ConfIA, final humano, ajuste, AuditRun, TranscriptionVersion, HumanDecision, review e modo/versão do motor. Snapshots históricos conservam os mesmos campos para consultas de versões anteriores.

Nenhuma estatística, acurácia ou integração com gold externo foi implementada. Nota humana registrada não é automaticamente um gold validado. FinalCorrection/ConfirmedQuestion operam sobre o contrato de auditoria e decisão; não importam motor experimental nem condicionam comportamento a P1/P2/P3. Um teste valida modo/versão arbitrários no contrato, sem simular a existência de Dynamic.

## 16. Testes Python

Nove testes D6 com stores reais e motor estável cobrem: readiness, pending, stale, FAILED, decisão invalidada, sugestão/final/delta, contagens, review, snapshots, finalização, duplo envio, concorrência, status/listagem, bloqueios de mutação, reabertura, segunda versão, integridade/histórico, pseudônimo, eventos, gold rows e contrato agnóstico.

Incluída concorrência em que uma auditoria genérica começa antes da finalização e tenta publicar depois: publicação rejeitada, fechamento preservado. Rotas de produto e métodos de armazenamento compartilhados pelos endpoints genéricos são exercitados.

Conjunto focado D1–D6: **67 PASS em 42,63 s**. Após o ajuste de ordem de validação: transcriptions + D6, **88 PASS em 26,94 s**. Depois da correção final de ordem de validação em auditorias, submission_audits + D6: **39 PASS e 1 falha Lean preexistente em 24,06 s**. Resultado amplo final na seção 18.

## 17. Testes JavaScript

Baseline D5 conferido: **510 PASS / 0 FAIL**. Resultado final D6: **515 PASS / 0 FAIL**, zero skip/cancel, em aproximadamente 1,58 s. Comando usa `tests/js/test_*.cjs`; incluir todos os `*.cjs` também faz o Node contar módulos auxiliares como testes vazios.

Cinco testes novos cobrem resumo/tabela, totais, ajustes/review, botão desabilitado, atalho de pendência, confirmação explícita, finalizada/bloqueios, reabertura/histórico, concorrência e apresentação na Home. A fixture JS representa contratos de UI; a validação de navegador usa API e motor reais.

## 18. Regressões

**863 PASS, 2 FAIL preexistentes, 1 SKIP em 272,36 s**, em 26 arquivos. Recorte inclui D1–D6, assessments, submissions/transcriptions, recognition, TME, decisões, autenticação, submission_audits, Pauta e bridges estáveis. Nenhuma falha nova. [Log completo da regressão final](assets/tme-december-d6/python-regression.txt).

Falhas Lean reproduzidas em exportação limpa do SHA inicial: **2 FAIL em 2,32 s**:

- `test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved`;
- `test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`.

Evidências: [reprodução limpa](assets/tme-december-d6/lean-baseline.txt) e [diagnóstico do artefato](assets/tme-december-d6/lean-diagnostic.txt). Mathlib indisponível localmente: tentativa de clone termina com `external command 'git' exited with code 128`. Não corrigido nesta branch. O skip preexistente depende de artefato local V2 e possui equivalente portátil.

Durante desenvolvimento, três regressões de transcrição apontaram HTTP 422 em vez de 409 para metadados corrompidos. A proteção nova estava sendo chamada antes da validação de integridade. A ordem foi corrigida, preservando o contrato anterior; nenhum teste foi enfraquecido. A execução intermediária foi interrompida para essa correção e não é contabilizada como resultado final. Uma execução seguinte encontrou duas diferenças na mensagem de erro de auditorias com fonte corrompida; a checagem de fechamento foi movida para depois da validação da fonte, preservando também esse contrato. Ambas as correções foram verificadas antes da regressão final.

## 19. Validação no navegador

Servidor local com modo demo explícito e `CONFIA_TME_QUESTION_USE_LEAN=0`; motor estável real e originais sintéticos. Avaliação configurada legitimamente com três questões, PDF de cinco páginas, captura de Q2 sem o item a para produzir sugestão 15. Não alterados fixtures matemáticos, Pauta ou checkers.

- **A — normal:** todas confirmadas, resumo revisado, confirmação explícita, versão 1 criada com 57/60. Home mostrou Finalizada, 57, dois ajustes e data.
- **B — bloqueio:** Q1/Q2 confirmadas, Q3 sem leitura/confirmação. Resumo mostrou pendência de Q3, total incompleto e Finalizar desabilitado. Atalho abriu Q3; após análise e homologação foi possível finalizar.
- **C — ajustes:** Q1 20→20, Q2 15→18 (+3), Q3 20→19 (−1). Backend/UI: ConfIA 55, humano 57, total +2.
- **D — reabertura:** controles de leitura/análise desabilitados enquanto finalizada; reabertura global explícita preservou decisões. Q1 reaberta e ajustada de 20 para 19 com motivo; nova homologação; versão 2 fechada com ConfIA 55, humano 56 e delta +1. Histórico exibiu a versão 1 com 57 intactos.

Console sem erros/warnings na inspeção. Sem alteração artificial de viewport. Em tela estreita, validados botões, tabela, rolagem, links e navegação por teclado. Capturas e persistência em assets. Servidor local encerrado ao término da validação.

## 20. Screenshots e evidências

Pasta [assets/tme-december-d6](assets/tme-december-d6/):

| Evidência | Arquivo |
| --- | --- |
| Resumo com Q3 pendente | [pending-q3.jpg](assets/tme-december-d6/pending-q3.jpg) |
| Finalizar desabilitado e atalho | [finalization-blocked.jpg](assets/tme-december-d6/finalization-blocked.jpg) |
| Resumo 55 × 57, +3/−1 | [ready-summary.jpg](assets/tme-december-d6/ready-summary.jpg) |
| Primeiro fechamento | [finalized-v1.jpg](assets/tme-december-d6/finalized-v1.jpg) |
| Home Finalizada | [home-finalized.jpg](assets/tme-december-d6/home-finalized.jpg) |
| Reabertura com decisões preservadas | [reopened.jpg](assets/tme-december-d6/reopened.jpg) |
| Segundo fechamento 56/60 | [finalized-v2.jpg](assets/tme-december-d6/finalized-v2.jpg) |
| Histórico da versão 1 | [closure-history-v1.jpg](assets/tme-december-d6/closure-history-v1.jpg) |
| Hashes e dados persistidos | [persistence-check.json](assets/tme-december-d6/persistence-check.json) |
| Console | [browser-console.json](assets/tme-december-d6/browser-console.json) |
| Testes | [test-results.txt](assets/tme-december-d6/test-results.txt) |

Persistência: onze arquivos (original, revisões, auditorias, decisões e primeiro fechamento) conservaram SHA-256. Q2/Q3 são idênticas entre os dois snapshots. Q1 tem novo HumanDecision ID. As consultas finais preservam duas versões, vínculo anterior, eventos e três gold rows.

## 21. Arquivos modificados

- `tme/finalization.py`: contratos, snapshot, readiness, totais, ledger, concorrência, eventos, consulta gold e proteção de edição.
- `tme/exam_models.py`, `tme/exam_store.py`, `tme/exam_router.py`: estado operacional, listagem/detail e três operações de fechamento.
- `tme/human_decisions.py`, `tme/question_review.py`, `tme/correction_engine.py`: bloqueio das mutações de produto após fechamento; flag de finalizada no workspace.
- `submissions/store.py`, `submission_audits/service.py`: verificações de ciclo de vida nos caminhos compartilhados/genéricos, inclusive publicação de auditoria. Nenhuma alteração na matemática.
- `static/tme/full-exam.js`, `static/tme/tme.js`, `static/tme/index.html`: resumo/relatório final, confirmação, histórico, Home/fila, bloqueios e cache de scripts.
- `tests/test_tme_finalization.py`, `tests/js/test_finalization.cjs`, `tests/js/exam-fixture.cjs`: testes e contratos simulados de UI.
- Este relatório e `docs/audits/assets/tme-december-d6/`.

Caminhos de código acima são relativos a `app/confia_lean_auditor/`; os caminhos de testes/docs são relativos à raiz. Nenhuma modificação de CSS, motor matemático, PautaEngine, Lean/checkers, experimental, benchmarks ou implementação de P4/P5.

## 22. Riscos e limites

- O fechamento é local ao filesystem e aos locks existentes, sem banco distribuído, assinatura digital ou broker. SHA-256 detecta inconsistência interna; não autentica autoria contra administrador do armazenamento.
- O resumo revalida artefatos e percorre auditorias; escalabilidade/indexação ficam fora desta etapa. A publicação prioriza snapshot consistente sob lock.
- READY_TO_FINALIZE é propriedade do resumo; o manifesto RECEIVED é imutável. Consumidores de produto devem usar `correction_status`/summary em vez de interpretar recebimento como estado da correção.
- Ajustes são por nota total da questão; não se acrescentou edição por critério. Não há envio externo, publicação institucional de resultado, novo PDF ou gold estatístico.
- D6 não certifica correção matemática nem resolve a indisponibilidade local de Mathlib. Review confirmado continua visível e registrado.

## 23. Comandos e veredito

Executados com o Python solicitado:

```sh
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_finalization.py tests/test_tme_human_confirmation.py tests/test_tme_reanalysis.py tests/test_tme_question_audit.py tests/test_tme_review_workspace.py tests/test_tme_full_exam.py
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_transcriptions.py tests/test_tme_finalization.py
/usr/local/bin/node --test tests/js/test_*.cjs
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_finalization.py tests/test_tme_human_confirmation.py tests/test_tme_reanalysis.py tests/test_tme_question_audit.py tests/test_tme_review_workspace.py tests/test_tme_full_exam.py tests/test_submissions.py tests/test_transcriptions.py tests/test_recognition.py tests/test_recognition_invariants.py tests/test_mathpix_strokes.py tests/test_tme_pilot.py tests/test_tme_photo_errors.py tests/test_tme_home_summary.py tests/test_tme_demo_auth.py tests/test_assessments.py tests/test_teacher_decisions.py tests/test_core_auth.py tests/test_core_institutional.py tests/test_tme_accepted_integration.py tests/test_submission_audits.py tests/test_pauta_engine.py tests/test_tme2_p1_pauta_bridge.py tests/test_tme2_p2_pauta_bridge.py tests/test_rubric_bridge.py tests/test_public_audit_boundary.py
```

Reprodução limpa: `git archive df6e20ebf51c89649ee24793c030949e3c27da60` extraído em `/private/tmp/confia-d6-baseline`; no diretório exportado, mesmo Python com `PYTHONPATH=app -m pytest -q tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`.

Verificações finais: `git diff --check`, `git diff --cached --stat`, `git rev-parse HEAD`, `git status --short`. Sem staging ou commit.

READY_FOR_DECEMBER_D7
