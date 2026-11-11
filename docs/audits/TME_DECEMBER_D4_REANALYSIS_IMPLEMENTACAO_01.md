# D4 — correção da leitura e reanálise por questão

## 1. SHA inicial e escopo

SHA inicial: `ac52c97e9ed9ca14a1a8c36c48faa1cbb7d508ec` (`Implement TME question audit workspace for December demo`). Branch `feat/tme-december-integration`, worktree `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-december-integration`, inicialmente limpo. Sessão de 10/11/2026, horário de Fortaleza.

Reutiliza D1–D3. Nenhuma alteração de Lean, checkers, PautaEngine, fixtures matemáticas, benchmarks, golds ou experimental P3. Sem ajuste humano da pontuação, confirmação, nota final ou fechamento global D5–D7. Sem `git add` ou commit.

## 2. Fluxo de reanálise

Corrigir leitura → salvar revisão imutável → versão corrente atualizada → auditorias anteriores stale → botão **Reanalisar questão** → aceite técnico da versão escolhida → `CorrectionEngine.audit_question` → novo AuditRun → nova sugestão e comparação.

Salvar, navegar, abrir histórico e consultar versões não executam auditoria. O mesmo editor/endpoint é usado ao entrar por Transcrição ou Comparar. Loading desabilita análise, edição e troca de questão durante o request. Um rascunho aberto bloqueia a execução.

## 3. Stale handling e estados

CURRENT/STALE continuam derivados da correspondência exata entre run e revisão corrente. Nenhum enum novo foi introduzido. COMPLETED/FAILED permanecem no AuditRun; RUNNING é estado da UI durante a chamada síncrona; REVIEW é o estado de produto quando há revisão ou falha.

Após a edição: “Leitura alterada — reanálise necessária”, sugestão **anterior** claramente rotulada, nenhuma sugestão corrente fabricada. O backend retorna `current_audit=null` se não houver run da leitura corrente. Um run FAILED corrente prevalece sobre scores de runs antigos e `analysis_state=FAILED` tem precedência sobre o aviso de reanálise.

## 4. Históricos imutáveis

AuditRuns e revisões existentes não são regravados. O histórico mostra versão, score ou pontuação ausente, status e conclusão. IDs completos, engine mode/version, timestamps e contrato ficam nos detalhes da análise. Proveniência antiga continua ligada ao resultado antigo.

O histórico de transcrição D2 foi preservado: versões anteriores podem ser expandidas para consulta, com origem, data e indicação corrente/preservada, sem operação de restauração/ativação. A validação compara hashes dos arquivos antes/depois e verifica que abrir histórico não muda a leitura ativa.

## 5. Versionamento, concorrência e idempotência

O adapter verifica a revisão corrente sob o lock existente da prova e confere novamente a versão no snapshot do workspace antes de chamar o serviço. O AuditService conserva o texto aceito exato e calcula stale novamente ao retornar. Se uma edição acontecer durante o cálculo, o run termina ligado à versão antiga e fica histórico; não é promovido para a versão nova.

A execution_key persiste no frontend quando a resposta HTTP é incerta. Replay com a mesma chave retorna o mesmo run; o lock de request serializa chamadas simultâneas equivalentes. Após FAILED terminal, **Tentar novamente** usa nova chave e conserva o run falho. Após sucesso, a política D3 de nova execução manual foi mantida e explicitamente rotulada **Executar nova análise**. Não há duplicação por navegação ou double-click; chamadas independentes com chaves diferentes são comandos distintos, não deduplicação distribuída entre navegadores.

## 6. CorrectionEngine

Reutilizado `CorrectionEngine.audit_question(case_id, AuditRequest, user)`. O caminho matemático permanece AuditService → accepted TME adapter → registry/checkers → bridge → PautaEngine. Sem cálculo de critérios/pontos no frontend e sem endpoint paralelo.

O adapter captura a análise mais recente de **outra versão de leitura** como referência da correção. Esse predecessor, score, máximo, versão e conclusão são congelados no evento persistido `question_reanalysis_requested`. Reconsultar o run não escolhe outro predecessor a partir de runs posteriores. Retry na mesma versão compara com a leitura anterior, enquanto a tentativa FAILED da versão corrente permanece no histórico.

Runs D3 existentes não são migrados nem reescritos. Seus eventos e payload persistidos são preservados; não se fabrica comparação retroativa se o snapshot de predecessor não foi registrado.

## 7. APIs e contrato

| Endpoint existente | Comportamento D4 |
|---|---|
| POST `/tme/cases/{case_id}/transcriptions/{id}/revisions` | Reutilizado, com based_on_revision_number e criação imutável. |
| POST `/tme/cases/{case_id}/audits` | Primeira análise, reanálise e retry pelo mesmo adapter/contrato. |
| GET `/tme/cases/{case_id}/audits` | Histórico normalizado, incluindo comparação quando registrada. |
| GET `/tme/question-attempts/{case_id}/workspace` | current_audit, previous_audit, audit_comparison, estados, versões, eventos e partial_suggestion. |

Contrato de run `question-audit.v1` recebe campo aditivo `comparison`. Contém previous/current audit IDs, previous/current transcription version IDs, previous/current score, previous_max_score, previous_completed_at, timestamp e score_changed. A ausência de score permanece null.

Autorização, demo sem login, ownership e integridade D3 continuam vigentes. O frontend não envia score nem predecessor confiável: o backend resolve ambos.

## 8. Frontend e layout preservado

Mesmos header, paleta, tipografia, componentes, tabs, divisor, navegação, cards, toolbar e painel ConfIA. Nenhum CSS alterado. Scripts recebem versão `december-d4` para cache.

O painel mostra a comparação em uma seção compacta expansível **Atualizado após correção da leitura**, com anterior/atual. Em falha: **Tentativa após correção da leitura**. Histórico técnico não é usado como título principal. Após cada operação, recarrega somente o workspace/dados pertinentes, sem reload da aplicação inteira. O resumo parcial é calculado pelo backend e atualizado também ao trocar de questão.

“Ver no original” continua usando a evidência do run exibido. Com página conhecida, navega à folha; nenhum highlight ou source span é inventado. O navegador confirmou a ação para a evidência do item (b) da nova leitura.

## 9. Eventos estruturados

Eventos D2 de `transcription_human_corrected` e `audit_marked_stale` são projeções determinísticas dos registros imutáveis. Agora incluem assessment_id, participante pseudônimo, submission_id da prova, question_attempt_id, transcription_version_id, timestamp, engine_version e previous_audit_run_id quando existente. Antes da primeira auditoria, engine_version/previous_audit_run_id são null, pois ainda não existe engine associado à correção.

Novos runs mantêm o digest e validação de eventos D3. Acrescentados:

- `question_reanalysis_requested`: predecessor de outra versão e snapshot da comparação;
- `audit_failed`: terminal FAILED, em vez de relatar sucesso de conclusão;
- `suggested_score_changed`: somente quando ambos os scores são numéricos, diferentes e o novo run concluiu; old_score/new_score reais.

`audit_started`, `audit_completed`, rubric/checker events e review_required são reutilizados. Eventos da reanálise incluem previous_audit_run_id. Score igual não gera mudança; null em falha não é zero. Eventos antigos persistidos não são reinterpretados ou reescritos.

Eventos de auditoria são publicados atomicamente com o resultado terminal, como em D3. O timestamp de início/pedido é o início do run, mas não há broker/journal de pedidos durável antes da conclusão. Eventos de leitura são derivados na consulta, sem escrita em GET. Não foi implementada estatística.

## 10. Sugestão anterior/atual e soma parcial

O score individual vem do resultado do motor. A comparação não ajusta nem recalcula pontos. Na demonstração: leitura v1 omitia item (b), 15/20; v2 recupera o trecho do original, 20/20. São dois AuditRuns diferentes e ambas as leituras continuam acessíveis.

`partial_suggestion` soma apenas a análise mais recente não stale, COMPLETED, com resultado numérico de cada questão. Não usa runs FAILED nem scores antigos como fallback. Inclui máximo total cadastrado, quantidade de questões com sugestão disponível, quantidade aguardando reanálise e flag complete. Sugestão numérica com REVIEW continua disponível e é contabilizada, sem ocultar a revisão individual.

Exemplo observado: Q1 15 + Q2 20 → parcial 35/100; editar Q1 → parcial 20/100, 1 aguardando reanálise; reanalisar → parcial 40/100, 2/5 questões. A interface identifica o total incompleto como **Sugestão ConfIA parcial**, nunca nota final. Zero numa soma vazia é acompanhado de 0/N questões e não é atribuído a um run falho.

## 11. Failure handling

Uma exceção controlada no transporte do engine produz AuditRun FAILED persistido, score null, revisão e mensagem **Não foi possível concluir a reanálise**. A versão nova permanece current. O score anterior só aparece como histórico/comparação. O botão **Tentar novamente** cria outro run após resultado terminal; falha de transporte HTTP incerta conserva a chave para replay.

No navegador, a injeção foi feita exclusivamente no launcher temporário `/tmp/confia-d4-serve.py`, por um marcador `/private/tmp/confia-d4-browser/fail-engine`; nenhum mecanismo de falha foi adicionado ao produto ou engine. O marcador foi removido antes do retry. O AuditRun FAILED foi preservado byte a byte após retry bem-sucedido. Diagnósticos privados não são expostos; detalhes preservam a categoria técnica do serviço existente.

## 12. Testes Python

Interpretador solicitado: `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`, com `PYTHONPATH=app`. Cinco novos testes em `tests/test_tme_reanalysis.py`, usando stores/APIs/motor estável reais e modo determinístico explícito nos sucessos:

1. mudança numérica, nova versão/run, histórico e eventos, pseudônimo/demo, Q1/Q2 isoladas e parcial sem stale;
2. score igual, replay idempotente e comparação estável após nova execução manual;
3. FAILED/null, retry, score real com review, histórico e parcial sem falha;
4. edição durante cálculo: resultado antigo preservado stale, rejeição da versão antiga e reanálise correta;
5. duas chamadas simultâneas com a mesma chave executam o engine apenas uma vez.

Recorte D4+D3+D2: **21 PASS**, 10,65 s. Regressão ampliada final: **831 PASS / 2 FAIL preexistentes / 1 SKIP**, 242,51 s. As contagens se sobrepõem e não devem ser somadas.

## 13. Testes JavaScript

Baseline D3 reproduzida: **502 PASS / 0 FAIL**, 1,64 s. Suíte final: **505 PASS / 0 FAIL**, 1,65 s.

Três testes novos cobrem stale banner, ação de reanálise, loading/double-click, sucesso, falha/retry com nova chave, comparação, status, navegação e isolamento Q1/Q2, total parcial, versões da leitura, histórico e componentes existentes. Fixtures JS representam contratos; não substituem a validação com engine real. Duas assertions D2/D3 passaram a ignorar maiúscula/minúscula no aviso solicitado, mantendo a verificação semântica.

A inspeção visual detectou uma mensagem “Aguardando análise” indevida junto de resultado concluído durante a implementação. Corrigida a condição e acrescentada assertion de ausência dessa mensagem após reanálise. A suíte completa foi repetida após o ajuste.

## 14. Regressões

Recorte ampliado em 24 arquivos cobre D1/D2/D3/D4, submissions/transcriptions, recognition/invariants, Mathpix strokes, TME/auth/home/photo, assessments, teacher decisions, core institucional, submission_audits, pauta e bridges, public audit boundary. Código Python ficou estável durante a execução para preservar o fingerprint de engine context.

Resultado final: **831 PASS / 2 FAIL / 1 SKIP**, 242,51 s. As duas falhas são exclusivamente as Lean preexistentes da seção 15. O skip existente em `tests/test_rubric_bridge.py:202` depende de artifact V2 local e tem regressão portátil equivalente no mesmo arquivo. `git diff --check` limpo. Nenhuma expectation matemática, fixture ou regra do motor foi alterada.

## 15. Falhas Lean preexistentes

Reproduzidas em exportação limpa do SHA inicial, `/private/tmp/confia-d4-baseline`: **2 FAIL em 2,50 s**:

- `test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved`: technical_error em vez de verified/refuted;
- `test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`: ausência de refuted.

São as falhas conhecidas de indisponibilidade de Mathlib documentadas em D1–D3. Nos artifacts da regressão final, a obtenção de `mathlib4` termina em `external command 'git' exited with code 128`, sem diagnóstico mais específico. Não foram corrigidas ou mascaradas. Demonstração e testes de sucesso configuram `CONFIA_TME_QUESTION_USE_LEAN=0` explicitamente; configuração registrada no run. O padrão do produto continua com Lean habilitado. Não há fallback automático.

## 16. Validação no navegador

Aplicação real em `127.0.0.1:8765/tme`, demo sem login, prova D4-REAL-ENGINE recebida pelas APIs D1, quatro páginas de PDF sintético. Q1 folhas 1/2; Q2 folhas 3/4. O PDF contém as soluções existentes de teste, sem alteração de fixture. O candidato de Q1 omite deliberadamente o item (b), presente no original, para simular correção de leitura com mudança real de sugestão.

Percurso executado pela UI:

- abrir Home/fila/prova/Q1, importar leitura e analisar: 15/20, REVIEW;
- abrir Q2, importar/analisar: 20/20; parcial 35/100;
- voltar Q1, corrigir em Comparar e salvar v2: stale, sugestão anterior 15, botão Reanalisar; parcial 20/100;
- navegar Q2 e voltar: Q2 continua pronta, Q1 continua stale;
- reanalisar Q1: 20/20, novo AuditRun/v2, comparação 15→20, parcial 40/100;
- consultar AuditRun antigo 15/20 e texto v1, sem ativá-los;
- editar espaçamento em Q1, salvar v3 e provocar falha controlada: FAILED/null, retry disponível;
- desativar injeção e tentar novamente: novo run v3, 20/20; FAILED continua no histórico;
- abrir original pela evidência nova do item (b); conferir Q2 ainda 20/20 e parcial 40/100.

Console sem erros/warnings. Comparação de hashes confirma originais, revisões e runs antigos intactos. Estado final Q1: quatro runs (v1 15, v2 20, v3 FAILED/null, retry v3 20); Q2: exatamente um run 20. Um único suggested_score_changed, 15→20. Servidor temporário encerrado após validação; marcador de falha removido.

## 17. Screenshots e evidências

Em `docs/audits/assets/tme-december-d4/`:

- [q1-before.jpg](assets/tme-december-d4/q1-before.jpg): Q1 15/20, leitura incompleta.
- [q1-stale.jpg](assets/tme-december-d4/q1-stale.jpg): v2, sugestão anterior e ação explícita.
- [q1-running.jpg](assets/tme-december-d4/q1-running.jpg): processamento e botão desabilitado.
- [q1-reanalyzed.jpg](assets/tme-december-d4/q1-reanalyzed.jpg): comparação real 15→20 no layout existente.
- [q1-history.jpg](assets/tme-december-d4/q1-history.jpg): análise v1 preservada.
- [transcription-history.jpg](assets/tme-december-d4/transcription-history.jpg): leitura v1 consultada sem ativação.
- [q1-failed.jpg](assets/tme-december-d4/q1-failed.jpg): falha sem pontuação e retry.
- [q1-retry.jpg](assets/tme-december-d4/q1-retry.jpg): novo resultado após retry.
- [new-evidence-original.jpg](assets/tme-december-d4/new-evidence-original.jpg): nova evidência e Original.
- [q2-independent.jpg](assets/tme-december-d4/q2-independent.jpg), [q2-while-q1-stale.jpg](assets/tme-december-d4/q2-while-q1-stale.jpg), [q2-after-reanalysis.jpg](assets/tme-december-d4/q2-after-reanalysis.jpg): Q2 preservada durante o fluxo.
- [persistence-check.json](assets/tme-december-d4/persistence-check.json): IDs, hashes, sequência de runs, comparação, eventos e parcial final.

- [test-results.txt](assets/tme-december-d4/test-results.txt): resumo final Python/JavaScript e diagnóstico Lean.
- [python-regression.txt](assets/tme-december-d4/python-regression.txt): saída integral da regressão ampliada.
- [lean-baseline.txt](assets/tme-december-d4/lean-baseline.txt): reprodução das duas falhas no SHA inicial.

## 18. Arquivos modificados

- `app/confia_lean_auditor/tme/correction_engine.py`: vínculo de predecessor, comparação e eventos D4, segunda verificação da versão corrente.
- `app/confia_lean_auditor/tme/question_review.py`: enriquecimento de eventos, estado FAILED, previous/current e soma parcial.
- `app/confia_lean_auditor/static/tme/tme.js`: ação de reanálise/retry, banner, comparação, histórico e parcial.
- `app/confia_lean_auditor/static/tme/workspace-report.js`: rótulo de histórico e timestamps nos detalhes.
- `app/confia_lean_auditor/static/tme/index.html`: versão de cache dos scripts.
- Novos `tests/test_tme_reanalysis.py` e `tests/js/test_question_reanalysis.cjs`.
- `tests/js/exam-fixture.cjs`, `tests/js/test_question_audit.cjs`, `tests/js/test_review_workspace.cjs`: contratos e assertions de compatibilidade.
- Este relatório e assets D4.

Nenhuma mudança no AuditService, schema persistido, autenticação, engine matemático ou CSS foi necessária nesta etapa.

## 19. Riscos e limites

- Serviço síncrono; não implementa recuperação de jobs após queda do processo. Eventos ficam duráveis com o resultado terminal.
- Lock/idempotência por execution_key; dois comandos intencionais com chaves diferentes podem gerar dois runs da mesma leitura, conforme política D3 explicitada no botão.
- A comparação usa o último run de outra versão conhecido no pedido, inclusive score null se aquele run falhou. Não busca uma nota antiga favorável nem inventa predecessor.
- A soma parcial considera sugestões numéricas com REVIEW; não equivale a aprovação nem fechamento da prova. Sem sugestões, mostra parcial 0 com 0/N analisadas.
- Consultas de workspace já verificam histórico e artifacts dos irmãos; o novo resumo aproveita esses dados. Muitos runs podem tornar essa consulta custosa; sem novo índice.
- Eventos de transcrição não possuem engine_version antes da primeira execução. Leitura é proveniência do produto, não resultado matemático.
- Mantidas limitações do engine estável quanto à entrada explicitamente dividida em itens e à proveniência visual limitada à página. Sem interpretação experimental nova.
- Mathlib indisponível impede validar os checks formais locais neste ambiente. Modo determinístico não representa prova formal completa.

## 20. Comandos e veredito

```sh
/usr/local/bin/node --test tests/js/test_*.cjs
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_reanalysis.py tests/test_tme_question_audit.py tests/test_tme_review_workspace.py
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_reanalysis.py tests/test_tme_question_audit.py tests/test_tme_review_workspace.py tests/test_tme_full_exam.py tests/test_submissions.py tests/test_transcriptions.py tests/test_recognition.py tests/test_recognition_invariants.py tests/test_mathpix_strokes.py tests/test_tme_pilot.py tests/test_tme_photo_errors.py tests/test_tme_home_summary.py tests/test_tme_demo_auth.py tests/test_assessments.py tests/test_teacher_decisions.py tests/test_core_auth.py tests/test_core_institutional.py tests/test_tme_accepted_integration.py tests/test_submission_audits.py tests/test_pauta_engine.py tests/test_tme2_p1_pauta_bridge.py tests/test_tme2_p2_pauta_bridge.py tests/test_rubric_bridge.py tests/test_public_audit_boundary.py
```

Reprodução do baseline Lean:

```sh
mkdir -p /private/tmp/confia-d4-baseline
git archive ac52c97e9ed9ca14a1a8c36c48faa1cbb7d508ec | tar -x -C /private/tmp/confia-d4-baseline
cd /private/tmp/confia-d4-baseline
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline
```

Reabrir demonstração com os dados temporários desta sessão:

```sh
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python /tmp/confia-d4-serve.py
```

O launcher lê `/tmp/confia-d4-environment.py`, configura development, auth habilitado e demo sem login, Lean explicitamente desligado e stores isolados sob `/private/tmp/confia-d4-browser`. Não contém credenciais. A falha só é ativada se o marcador temporário existir; ao término ele está ausente. Esse launcher é ferramenta local de validação, não parte do produto.

Verificação concluída: **831 PASS / 2 FAIL preexistentes / 1 SKIP** no Python ampliado; **21 PASS** no recorte focado; **505 PASS / 0 FAIL** no JavaScript completo. Navegador validou mudança 15→20, histórico imutável, Q2 isolada, falha com null e retry. HEAD inalterado, índice sem alterações, `git diff --check` limpo. Sem `git add` ou commit.

READY_FOR_DECEMBER_D5
