# D3 — auditoria real no workspace por questão

## 1. Base e escopo

SHA inicial: `d23ebf5f11b1ccf02fbe4a09bbf125ef0bc323df`. Branch `feat/tme-december-integration`; worktree `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-december-integration`, inicialmente limpo. Data: 10/11/2026. Sem `git add`, sem commit e sem mudança de HEAD.

D3 conecta QuestionAttempt e revisão corrente à auditoria matemática estável, com sugestão, pauta, evidências, revisão, histórico e eventos. Não altera regras matemáticas, checkers, Lean, PautaEngine, benchmarks, golds ou fixtures matemáticas. Não integra Semantic Formal experimental, hybrid shadow, ajuste de nota, confirmação, fechamento global ou estatística. As questões já suportadas pelo registry permanecem suportadas; não foi desenvolvido motor novo para P4/P5.

## 2. Arqueologia do motor, anterior à implementação

| Componente inspecionado | Caminho real e decisão |
|---|---|
| `main.py:/audit → execute_audit` | Caminho geral/ITA: valida assets, extrai claims, executa checks de passos/microclaims/student claims, avalia rubric/adjusters/scoring policy, publica artifacts e AuditResponse. Não é o despacho TME escolhido. |
| `submission_audits.service.AuditService` | Valida revisão aceita, receipt e hashes; calcula identidade, serializa execução por run, persiste resultado/manifesto e deriva stale. REUSED. |
| `tme.accepted_audit` | `split_accepted_items` reconhece metadados tme_item_id ou cabeçalhos isolados; não infere itens pelo conteúdo. `audit_accepted_tme_transcription` chama o registry e preserva solução, revisão, mapeamento e certificados. REUSED sem alteração. |
| `tme.registry.audit_tme` | Despacha coletores/checkers estáveis por questão. P1 chama collect/verify/bridge/PautaEngine; as demais rotas já existentes seguem seus adapters atuais. REUSED. |
| `rubric.pauta.bridge` | Valida ligação exata claim/fact/verificação, atribuição ao estudante, conflitos, origem e status; mapeia fatos às obrigações. REUSED sem alteração. |
| `PautaEngine.evaluate` | Consome evidência já verificada e regras da pauta; calcula PautaDecision/PautaAssessment. REUSED sem alteração. |
| MathClaimRecord/FactResult/VerificationLink | Texto e offsets do envelope do motor, claim/fact IDs, checker type/status e referências. REUSED. |
| `tme.hybrid_grader.run_hybrid_shadow` | Caminho opt-in/shadow e ativação condicionada. Não está no dispatch do AuditService usado aqui; não foi ativado. |
| `workspace-report.js` | Cards/classes de sugestão, critério, evidência e detalhes existentes. Reutilizados por renderer de contrato de produto. |

Fluxo implementado: revisão corrente persistida → aceite técnico existente → AuditService → adapter TME estável → extração/checks → bridge → PautaEngine → TMEAuditResult imutável → projeção de produto. Não há HTTP interno para `/audit` nem segundo cálculo de pontos.

## 3. CorrectionEngine

Novo `tme/correction_engine.py`: `CorrectionEngine.audit_question(case_id, AuditRequest, user)` resolve assessment, participante pseudônimo, prova, fonte da questão e revisão. Valida proprietário, fonte congelada, corrente e execution_key. O texto é obtido da revisão aceita, nunca confiado a um segundo campo enviado pelo frontend.

O contrato `schema_version=question-audit.v1` contém IDs, `engine_mode`, `engine_version`, configuração, versão da leitura, sugestão/máximo, critérios, evidências, checks, motivos, warnings, incerteza técnica, referência de trace e timestamps. IDs distinguem `submission_id` da prova e `source_submission_id` da fonte técnica por questão. O frontend de prova completa recebe essa projeção, sem bridge, pauta bruta, classes Lean ou caminhos locais de artifacts.

Modo efetivo: `TME_CURRENT`. A versão vem do fingerprint persistido do engine context existente, não da versão atual do código no momento da consulta. A estrutura admite futura implementação de outros modos por outro adapter; SEMANTIC_FORMAL/AUTO não estão ativos em D3. Configuração `CONFIA_TME_QUESTION_USE_LEAN=0` seleciona explicitamente o modo determinístico existente; por padrão Lean permanece habilitado. Nenhuma falha desliga Lean automaticamente.

## 4. AuditRun reutilizado

O AuditRun existente continua sendo a entidade persistida. Foram acrescentados campos opcionais `question_context`, `completed_at`, `question_events` e `question_events_sha256`. Contexto contém assessment_id, participant_id, exam_submission_id, question_attempt_id, engine_mode, adapter_version e máximo cadastrado. Não contém nome, CPF, email ou outro identificador civil.

O serializer mantém a forma anterior de registros legados quando os novos campos não existiam. O serviço recebe contexto/callback de eventos opcional; chamadas legadas mantêm comportamento e contratos anteriores. Nenhum resultado anterior é sobrescrito.

Cada ação explícita ganha um UUID em `execution_key`; nova ação gera novo run. Retry de resultado HTTP incerto conserva a mesma chave para deduplicar pela identidade/lock existentes. Duplo clique é bloqueado na UI e a repetição da mesma requisição é idempotente no serviço.

## 5. Vínculo com a TranscriptionVersion

A identidade já existente `transcription_id:revision_number` é exposta como `transcription_version_id`. AuditSource preserva revisão exata, aceite, receipt, solution_text, hashes e contexto do motor. Não há cópia editável independente da transcrição no contrato do produto.

O endpoint só inicia análise para a revisão corrente da questão; transcrição de outra questão, versão antiga, fonte inválida, questão confirmada ou ausência de chave são recusadas. O aceite técnico reutilizado não declara conferência humana nem nota final; a nota da aceitação continua explicitando a vinculação automática a pedido do avaliador.

## 6. Stale e histórico

A análise corrente é a mais recente **não stale**, inclusive se falhou. Uma falha recente não é ocultada por uma análise bem-sucedida anterior. Runs anteriores permanecem em “Histórico de análises”.

Após edição, `current_audit=null` se todos os runs são de versões antigas; a UI mostra reanálise necessária e ausência de sugestão para a leitura atual. A sugestão antiga só aparece no histórico, identificada como anterior e com sua versão/run ID. Navegar, recarregar, abrir histórico ou salvar leitura não executa o motor. Não há ciclo automático de correção/aceite/reauditoria D4; o comando de análise continua sendo explícito.

## 7. RubricDecision

PautaDecision/PautaAssessment são reutilizados, sem entidade de pontuação paralela. O backend projeta ID, rótulo, máximo, pontos sugeridos, status bruto/legível, revisão, motivo, intervalo de pontos e referências a evidências/checks.

A seleção de bandas/métodos já feita pelo motor é respeitada. A UI mostra a árvore escolhida, sem recalcular critérios nem pontos. Evidências/checkers de cada critério vêm das obrigações desse caminho; alternativas descartadas não são misturadas à fundamentação do critério. O resultado bruto completo segue preservado no AuditRun. Se a pauta não possui descrição, o backend usa rótulos neutros “Item (a)”/“Etapa 1”, mantendo o ID técnico nos detalhes.

## 8. Evidência e “Ver no original”

Texto/claim/fact e offsets são os registros reais do motor. `source_span.scope=engine_input` informa que os offsets pertencem ao texto enquadrado pelo motor, não a caracteres da transcrição original nem a pixels da folha.

Para página, usa-se proveniência estruturada explícita ou o mapeamento existente de item→segmento→página, somente quando o item pertence inequivocamente a uma única página. A ação abre Original e seleciona a folha correta. A UI informa “Página do item; sem destaque de trecho específico”. Um item distribuído por várias páginas não recebe link inventado.

Não há busca por similaridade textual, crop fabricado ou conversão de coordenadas locais de diagrama em região da página. O contrato reserva `region`, atualmente nulo; não se desenha highlight sem geometria comprovada. Os originais continuam os assets D1 e os hashes são preservados.

## 9. Checker statuses e Lean

O backend preserva checker ID, fact ID, tipo, status bruto e trace; projeta linguagem legível: Verificado, Não verificado, Revisar e Erro técnico. A UI não interpreta enums internos de P1/P2/P3 para decidir pontos.

Quando um check Lean registra status verified, compilação e certificado, o texto é “Verificação formal deste passo concluída”. Não se afirma prova formal completa da solução. Configuração sem Lean é identificada nos detalhes; checker results e certificados do modo formal permanecem nos contratos/artifacts existentes.

## 10. Sugestão e falhas numéricas

“**Sugestão ConfIA: X / Y**” vem diretamente do AuditRun/PautaAssessment. Não é gravada como nota final. Falha técnica sem resultado retorna `suggested_score=null`; a UI mostra “Pontuação não determinada” e revisão. O máximo permanece disponível pelo contexto da avaliação.

A pauta estável tem política `withhold` em cenários como texto sem item reconhecido: pode retornar zero real e warnings. D3 preserva esse zero do motor e o acompanha de revisão/motivos; não o confunde com uma conversão de falha para zero. Divergência entre máximo do motor e máximo cadastrado é motivo de revisão, sem reescalar silenciosamente o resultado.

## 11. Review e estados de análise

Uma função comum deriva motivos de revisão para painel e navegação: stale, FAILED, score ausente, needs_review da pauta, falhas técnicas dos checks, warnings de omissão/interpretação de entrada e divergência de máximo. Warnings incidentais da projeção pública não são promovidos a bloqueios.

Estados persistidos do serviço continuam COMPLETED/FAILED. O contrato de apresentação distingue COMPLETED_WITH_REVIEW; RUNNING aparece durante o request síncrono na UI, com controles ocupados. PENDING corresponde à ausência de análise. Não foi introduzido worker/fila assíncrona.

Questão sem leitura: PENDING; leitura sem análise ou com revisão: REVIEW; última análise corrente concluída sem motivos: READY; DECIDED preexistente: CONFIRMED. D3 não cria confirmação humana.

## 12. APIs

| Rota existente | Integração D3 |
|---|---|
| POST `/tme/cases/{case_id}/audits` | Para prova completa, chama CorrectionEngine com AuditRequest existente; execution_key obrigatório. Para caso legado, mantém operação anterior. |
| GET `/tme/cases/{case_id}/audits` | Histórico normalizado da questão completa; legado mantém contrato anterior. |
| GET `/tme/question-attempts/{case_id}/workspace` | Acrescenta current_audit, histórico normalizado e eventos; estados uniformes. |
| POST `.../transcriptions/{id}/accept` | Reutilizado para receipt técnico da revisão escolhida. |

Cache-Control no-store e autorização de avaliador/proprietário mantidos. Nenhum endpoint duplicado de OCR, pauta ou `/audit`. O comando não recebe score, evidências ou decisões do frontend. Erros de domínio são tratados sem expor diagnóstico privado.

## 13. UI e preservação visual

Mesmo `renderCorrection`, Original/Transcrição/Comparar, header, navegação de questões, painel ConfIA, cards, divisor, botões e classes de D2. Nenhuma alteração de CSS, paleta, tipografia ou framework. `index.html` só atualiza versões dos scripts.

Novo renderer `renderQuestion` em workspace-report consome exclusivamente o contrato do produto. Usa a estrutura dos cards existentes, score sugerido, alertas, evidência, link ao original e detalhes expansíveis. Não contém regras específicas por questão. O renderer legado continua disponível para casos anteriores.

“Analisar com ConfIA”/“Executar nova análise” têm loading e bloqueio de duplo envio; edição aberta impede analisar rascunho. O botão permanece disponível após reload. Nova execução na mesma revisão conserva histórico. Q1/Q2 recuperam seus próprios estados sem reexecutar. Não foi acrescentado resumo/soma global opcional: isso não é necessário para D3 e nenhuma soma parcial é apresentada como nota final.

## 14. Eventos persistidos

Os novos runs guardam no próprio registro `question_events`, com digest canônico e validação de vínculo ao run, questão e versão. Tipos: audit_started, audit_completed, rubric_item_decided, checker_result_recorded e review_required. IDs estáveis; cada evento inclui assessment_id, participant_id pseudônimo, submission_id da prova, question_attempt_id, transcription_version_id, audit_run_id, timestamp e engine_version. Quando aplicável, inclui critério/checker, status e pontos.

Eventos são publicados atomicamente com o resultado terminal. audit_started leva o instante de início real, porém não é uma notificação persistida/distribuída em tempo real antes da conclusão; não há journal externo, worker ou broker. Runs antigos sem esses campos recebem projeção compatível, sem migração ou sobrescrita, e não se inventa completed_at ausente.

Após stale, eventos de conclusão persistidos não mudam; a alteração de leitura continua representada pelos eventos D2. Um teste altera evento no disco e comprova rejeição por integridade. Não há análise estatística em D3.

## 15. Testes Python

Interpretador: `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`, `PYTHONPATH=app`. Sem dependência nova.

Oito testes D3 usam stores/APIs reais e, nos cenários de sucesso, o motor estável com `use_lean=False` explicitamente configurado. Cobrem paridade com PautaEngine/registry, 20/20 real em Q1, Q2 independente, versão exata, critérios/checks/evidência, eventos persistidos, timestamps, pseudônimo, demo/proprietário, deduplicação, nova execução, histórico, stale, captura, warning/withhold, falha técnica nula, falha recente sem fallback para score antigo, integridade dos eventos e item em múltiplas páginas sem mapeamento visual inventado.

Execução focada final: **17 PASS**, 11,11 s (8 D3 + 8 D2 + teste full-5 de compatibilidade). Regressão ampliada final: **826 PASS / 2 FAIL / 1 SKIP**, 233,89 s, em 23 arquivos. As duas falhas são exclusivamente as Lean preexistentes descritas na seção 18. O skip existente em `tests/test_rubric_bridge.py:202` depende de artifact V2 local; a regressão portátil equivalente é testada no mesmo arquivo. As contagens das execuções focada e ampliada se sobrepõem e não devem ser somadas.

## 16. Testes JavaScript

Baseline D2 reproduzida: **498 PASS / 0 FAIL**. Suíte final: **502 PASS / 0 FAIL**, 1,43 s. Quatro testes novos verificam botão/loading/double-submit, score, critérios/evidência, status legível, ligação ao original, Q1/Q2, nova análise/histórico, stale sem execução automática, edição bloqueando análise, warning/falha sem zero, ausência de link sem página e retry da mesma execution_key.

A fixture JS de prova foi estendida para aceitar respostas de auditoria declaradas pelo teste; não é usada no navegador real. O harness disponibiliza Web Crypto para UUIDs. Um stub do teste D2 passou a incluir score, campo presente no modelo real; suas assertions de estado foram preservadas.

## 17. Regressões e ajustes encontrados

Primeira regressão ampliada: 823 PASS, 3 FAIL, 1 SKIP, 230,79 s. Duas falhas eram as Lean conhecidas. A terceira foi `test_five_problems_accepted_engine_persistence_api[full-5]`, com SourceIntegrityError enquanto os arquivos do adapter estavam sendo editados durante a execução. O fingerprint do engine context inclui esses arquivos e é revalidado antes da publicação; alterar código durante o run invalida a fonte/contexto. O teste passou novamente com o código estável. A suíte ampliada foi repetida integralmente sem editar Python durante a execução: **826 PASS / 2 FAIL / 1 SKIP**. O full-5 passou também nessa execução completa; restaram somente as duas falhas Lean preexistentes. Dois testes D3 adicionais de captura/proveniência explicam o aumento do total de 827 para 829 casos entre as execuções.

A validação visual encontrou/corrigiu a estrutura do summary dos cards para usar as classes existentes e o ocultamento indevido do botão após reload. A revisão de evidência limitou as referências apresentadas ao caminho selecionado pela pauta. Nenhuma expectation matemática foi enfraquecida.

## 18. Lean preexistente

As duas falhas foram reproduzidas numa exportação limpa do SHA inicial em `/tmp/confia-d3-baseline` (2 FAIL, 2,47 s):

- `test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved` — technical_error em vez de verified/refuted.
- `test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline` — ausência de refuted.

Mathlib indisponível, conforme D1/D2. O diagnóstico dos artifacts da execução final registra `mathlib: cloning https://github.com/leanprover-community/mathlib4` seguido de `external command 'git' exited with code 128`; o stderr não informa uma causa mais específica. Essas falhas não são regressões D3 e não foram corrigidas ou mascaradas no motor. O modo determinístico da demonstração é configuração explícita e fica registrado em engine_config; não é fallback automático oculto.

## 19. Validação no navegador

Servidor real `/tme` em demo sem login, dados isolados em `/private/tmp/confia-d3-browser`. Prova recebida pelas APIs D1, código pseudônimo D3-REAL-ENGINE, quatro páginas de PDF contendo o mesmo texto dos candidatos de transcrição. Conteúdo sintético identificado nas folhas, originado das soluções de teste já existentes, sem alterar fixtures ou fabricar resultado de auditoria. Q1 usa folhas 1/2; Q2 usa 3/4.

Percurso observado: Home→fila→prova→Q1 Original→Transcrição→importar leitura→Analisar→loading→Sugestão/pauta/evidência→Comparar→Ver no original (folha 2)→Q2→importar/analisar→Q1 com run preservado→corrigir leitura→versão 2→reanálise necessária→histórico da versão 1.

Q1 retornou 20/20 (itens 3/3, 5/5, 6/6, 6/6); Q2 retornou 20/20 (5/5, 7/7, 8/8), ambos pelo engine estável. Depois de editar Q1, não há análise corrente nem nova execução; a nota anterior aparece exclusivamente no histórico. Q2 permanece com seu próprio AuditRun.

O primeiro run de Q1 falhou porque `/tmp` no macOS é um symlink e a proteção de artifacts recusa esse caminho. A UI mostrou score ausente e revisão. A configuração foi corrigida para o caminho real `/private/tmp`, sem mudar a proteção nem o engine; o run de falha permaneceu no histórico.

Após o percurso, os hashes dos três AuditRuns foram comparados com os registrados antes da edição: todos idênticos. Original PDF também confere com o manifesto. Console consultado sem erros/warnings. Não foi acionada reanálise após corrigir a leitura.

## 20. Screenshots e evidências

Em `docs/audits/assets/tme-december-d3/`:

- [q1-audit.jpg](assets/tme-december-d3/q1-audit.jpg): Q1 com sugestão real, pauta e Comparar.
- [q1-evidence-original.jpg](assets/tme-december-d3/q1-evidence-original.jpg): evidência navegando à folha 2.
- [q2-audit.jpg](assets/tme-december-d3/q2-audit.jpg): análise própria de Q2.
- [q1-stale.jpg](assets/tme-december-d3/q1-stale.jpg): versão humana 2, reanálise necessária e nenhuma sugestão corrente.
- [q1-history.jpg](assets/tme-december-d3/q1-history.jpg): 20/20 anterior identificado como histórico, com run ID.
- [technical-failure.jpg](assets/tme-december-d3/technical-failure.jpg): falha real de configuração sem nota fictícia.
- [persistence-check.json](assets/tme-december-d3/persistence-check.json): IDs, hashes e estado final da demonstração.

- [test-results.txt](assets/tme-december-d3/test-results.txt): resumo das execuções finais Python/JS e diagnóstico Lean.
- [python-regression.txt](assets/tme-december-d3/python-regression.txt): saída integral da regressão Python final.
- [lean-baseline.txt](assets/tme-december-d3/lean-baseline.txt): reprodução das duas falhas no SHA inicial.

## 21. Arquivos modificados

Produção:

- Novo `app/confia_lean_auditor/tme/correction_engine.py`: adapter estável e projeção de produto.
- `app/confia_lean_auditor/submission_audits/schemas.py`: contexto, conclusão e eventos opcionais, com preservação legada.
- `app/confia_lean_auditor/submission_audits/service.py`: publicação do contexto/eventos no AuditRun existente.
- `app/confia_lean_auditor/tme/{router.py,exam_router.py,question_review.py}`: roteamento, erros e estados/histórico.
- `app/confia_lean_auditor/static/tme/{tme.js,workspace-report.js,index.html}`: ação/painel no layout existente.

Testes/documentação:

- Novos `tests/test_tme_question_audit.py`, `tests/js/test_question_audit.cjs`.
- `tests/test_tme_review_workspace.py`, `tests/js/{exam-fixture.cjs,tme-dom.cjs}`: extensão dos stubs, preservando testes anteriores.
- Este relatório e `docs/audits/assets/tme-december-d3/`.

## 22. Limites e riscos

- Engine estável exige itens explicitamente identificados; Q2 usa a representação textual já suportada. D3 não promete interpretar qualquer redação manuscrita/natural nem acrescenta heurística matemática.
- Pauta com descrições ausentes recebe rótulo neutro, sem inventar justificativa. Detalhes conservam reason/IDs/status reais.
- Referências visuais de texto podem chegar apenas à página do item; spans continuam no escopo do motor e não são destaques na imagem. Geometria de diagrama não é promovida a coordenada da folha.
- Serviço continua síncrono. Loading é estado da UI; eventos ficam duráveis com o run terminal. Crash abrupto antes da publicação não tem recuperação de job implementada nesta etapa.
- Consulta de histórico valida manifests/artifacts do serviço existente e pode ficar custosa com muitos runs; não foi criado índice paralelo.
- Não editar código durante uma execução: o fingerprint e a revalidação de engine context detectam mudança. Diretórios de artifacts precisam ter caminhos reais, sem symlinks.
- Mathlib precisa estar disponível para validar Lean neste ambiente. A demonstração determinística não certifica formalmente toda a solução.
- Nenhum fechamento global, ajuste humano, confirmação, automatismo de reanálise ou integração experimental foi incluído.

## 23. Comandos e resultado final

A partir do worktree:

```sh
/usr/local/bin/node --test tests/js/test_*.cjs
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_question_audit.py tests/test_tme_review_workspace.py
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_question_audit.py tests/test_tme_review_workspace.py tests/test_tme_full_exam.py tests/test_submissions.py tests/test_transcriptions.py tests/test_recognition.py tests/test_recognition_invariants.py tests/test_mathpix_strokes.py tests/test_tme_pilot.py tests/test_tme_photo_errors.py tests/test_tme_home_summary.py tests/test_tme_demo_auth.py tests/test_assessments.py tests/test_teacher_decisions.py tests/test_core_auth.py tests/test_core_institutional.py tests/test_tme_accepted_integration.py tests/test_submission_audits.py tests/test_pauta_engine.py tests/test_tme2_p1_pauta_bridge.py tests/test_tme2_p2_pauta_bridge.py tests/test_rubric_bridge.py tests/test_public_audit_boundary.py
```

Servidor da demonstração, com env e dados temporários desta sessão:

```sh
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -c "exec(open('/tmp/confia-d3-environment.py').read()); import uvicorn; uvicorn.run('confia_lean_auditor.main:app', host='127.0.0.1', port=8765)"
```

O env define development, auth habilitado, demo TME sem login, `CONFIA_TME_QUESTION_USE_LEAN=0` e diretórios AUTH/INSTITUTIONAL/ASSESSMENTS/ASSESSMENT_PARTICIPANTS/TME_EXAMS/TME_CASES/SUBMISSIONS/SUBMISSION_AUDITS sob `/private/tmp/confia-d3-browser`. Não contém credenciais. Fora dessa configuração de demonstração, Lean fica habilitado por padrão.

Baseline Lean:

```sh
mkdir -p /tmp/confia-d3-baseline
git archive d23ebf5f11b1ccf02fbe4a09bbf125ef0bc323df | tar -x -C /tmp/confia-d3-baseline
cd /tmp/confia-d3-baseline
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline
```

Verificação concluída: Python ampliado **826 PASS / 2 FAIL preexistentes / 1 SKIP**, Python focado **17 PASS**, JavaScript **502 PASS / 0 FAIL**. Fluxo real Q1/Q2, evidência no Original, preservação dos runs e stale após edição confirmados no navegador. Servidor temporário encerrado após a validação. `git diff --check` limpo; índice sem alterações; HEAD permanece no SHA inicial. Nenhum `git add` ou commit executado.

READY_FOR_DECEMBER_D4
