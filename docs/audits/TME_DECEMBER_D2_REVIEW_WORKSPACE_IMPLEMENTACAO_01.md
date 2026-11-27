# D2 — workspace de revisão por questão

## 1. Base e escopo

SHA inicial: `c2ebda83ccfaf5816adf7014fc835d53117c2154`; branch `feat/tme-december-integration`; worktree `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-december-integration`. Data: 10/11/2026. Worktree inicialmente limpo. HEAD preservado; sem `git add` e sem commit.

D2 conecta as QuestionAttempts de D1 ao workspace real do `/tme`, com Original, Transcrição, Comparar e revisão imutável. Não implementa D3–D7. Nenhum arquivo do motor matemático, Lean, checkers, Semantic Formal experimental, P1/P2/P3, pautas, benchmarks ou fixtures matemáticas foi alterado.

## 2. Arqueologia e modelos reutilizados

A inspeção de modelos, persistência, endpoints e componentes precedeu a implementação da interface.

| Domínio/componente encontrado | Decisão |
|---|---|
| Assessment, ExamSubmission, ExamPage, QuestionAttemptPage D1 | REUSED; originais e associação M:N preservados |
| CorrectionCase = QuestionAttempt | EXTENDED por projeção de workspace; nenhum segundo sistema de notas |
| SubmissionRecord/SubmissionStore | EXTENDED com fonte congelada `exam_pages`; captura legada continua limitada a três páginas |
| TranscriptionRecord + TranscriptionRevision | REUSED; histórico append-only, predecessor, autor e versão corrente pela última revisão |
| TranscriptionAcceptance + receipt | REUSED; revisão da leitura não significa aprovação matemática |
| RecognitionService/MathpixImageProvider | REUSED; adaptação de entrada/limite das páginas, sem novo OCR |
| AuditRun/AuditSource | REUSED; já registram transcription_id, revision_number, acceptance e hashes; stale já derivado |
| capture_pages/transcription_candidate | EXTENDED por importação explícita, sem reconhecimento ao abrir a questão |
| renderCorrection, CorrectionHeader, QuestionNavigator, ProblemStatement | REUSED; mesmo workspace, abas, comparador, editor, painel ConfIA e controles |
| Persistência JSON/locks/fsync | REUSED; projeções não constituem outro banco de transcrições |

## 3. Contratos novos e vínculo com D1

`QuestionSourceSnapshot` (`exam-question-source.v1`) e `QuestionSourcePage` congelam somente as páginas associadas à questão no primeiro registro de leitura. Incluem question_attempt_id, exam_submission_id, problem_id, mapping_version, exam_page_id, referência completa à ExamPage, referências/hash dos assets original e preview e dimensões. Índices locais são contíguos; até 50 páginas, conforme D1.

A Submission técnica por questão usa os stores existentes e ID determinístico a partir da QuestionAttempt. Copia os previews PNG para entrada do reconhecimento existente; **os originais continuam no ExamSubmission e são referenciados, não substituídos**. Repetições não publicam outra fonte. A associação da questão fica congelada após vincular a fonte; editar outra questão não invalida o snapshot anterior por mera mudança da versão global do mapeamento.

`CreateQuestionTranscription` permite `manual` com segmentos ou `capture` sem segmentos enviados pelo cliente. A importação lê os candidatos já persistidos pelo D1. `CaptureImportProvenance` guarda produtor, versão, ExamSubmission e páginas de origem. Não foi criada uma entidade TranscriptionVersion concorrente.

## 4. Versionamento e corrente

A versão conceitual é a revisão existente. A API projeta:

| Campo conceitual | Fonte |
|---|---|
| version_id | `transcription_id:revision_number` |
| question_attempt_id | CorrectionCase vinculada à Submission |
| version_number | revision_number |
| predecessor_version_id | mesmo transcription_id e número anterior |
| text | segmentos ordenados por página e ordem |
| origin | human, automatic, capture ou digital_ink |
| created_at / created_by | timestamp e reviewer_reference persistidos |
| metadata/confidence | histórico original e segmentos; proveniência de reconhecimento/importação |
| current | última revisão da cadeia corrente; exatamente uma |

Salvar uma edição cria nova revisão; a primeira e todas as anteriores permanecem consultáveis. Concorrência usa `based_on_revision_number`; uma edição baseada em revisão antiga recebe 409. Duplo envio inicial recebe 409. Na UI, salvar sem alteração não cria revisão adicional. O backend mantém a semântica legada de revisões explícitas.

A origem da cadeia automática continua preservada na proveniência mesmo após uma revisão humana. A apresentação distingue a revisão humana. O serializer omite o novo campo opcional em registros legados que não o continham, preservando a forma usada pelos hashes históricos.

## 5. APIs

| Método e rota | Comportamento |
|---|---|
| GET `/tme/question-attempts/{case_id}/workspace` | Novo: páginas associadas, histórico, versões, corrente, estados, auditorias reais e eventos derivados; sem escrita |
| POST `/tme/cases/{case_id}/transcriptions` | Novo: primeira leitura manual ou importação explícita de candidato; exige expected_mapping_version |
| POST `/tme/cases/{case_id}/transcriptions/{transcription_id}/revisions` | Reutilizado: revisão humana, autor autenticado/demo e controle de concorrência |
| POST `/tme/cases/{case_id}/recognize` | Reutilizado: congela as páginas e chama RecognitionService/MathpixImageProvider existentes |
| GET `/tme/cases/{case_id}/transcriptions` | Histórico legado reutilizado |
| GET `/tme/exam-submissions/{id}/assets/{asset_id}` | D1 reutilizado: original/preview com integridade e autorização |

Respostas de workspace/transcrição usam `Cache-Control: no-store`. Abertura não importa, reconhece ou audita. Após existir leitura, reconhecimento inicial adicional é recusado para não substituir uma correção humana. A UI não solicita auditoria matemática, aceitação ou decisão nesta etapa. Autorização e isolamento de proprietário foram testados; demo continua restrito às rotas TME existentes.

## 6. Workspace e identidade visual

`full-exam.js` abre a QuestionAttempt por callback no **mesmo `renderCorrection`** usado pelo fluxo anterior. A página provisória D1 por questão foi substituída pela integração ao componente real; não existe dashboard paralelo. A navegação superior usa todas as questões reais da avaliação, na ordem do catálogo da prova, sem restringir a família do problema.

Não houve alteração de CSS, paleta, tipografia ou framework. `index.html` mudou apenas versões dos scripts para atualização de cache. Mantidos header, cards, enunciado, tabs, divisor ajustável, zoom, rotação, ajuste, expansão da solução, painel lateral/drawer e histórico existentes. Contexto da avaliação e pontuação **máxima** vêm do cadastro; não representam nota atribuída.

## 7. Original e evidência

Imagens usam diretamente o asset original D1. PDF usa a representação integral de cada página gerada em D1, sem crop, com links para o PDF original e fragmento de página em “Originais e histórico”. A distinção é informada nesse painel. Zoom/pan/rotação/ajuste reaproveitam os controles atuais e preservam proporção.

Exibe página local e número da folha na prova. Navegar Q1→Q2 reutiliza a mesma ExamPage/asset quando compartilhada. A proveniência dos segmentos projeta `exam_page_id` e `page_number`; o segmento original conserva `source_region`, spans e confidence quando disponíveis. Edição de uma página que altera seu conteúdo cria texto de página inteira; não conserva artificialmente regiões/spans antigos. Sem região, a página integral é a referência de evidência.

## 8. Transcrição e entradas

A aba mostra versão/origem e renderiza o texto pelo renderer existente. “Originais e histórico” permite consultar texto das versões anteriores e a corrente.

Entradas convergem para TranscriptionRecord/Revision:

- Pipeline atual: mesma rota e provedor de reconhecimento, agora com fontes `exam_pages`.
- Capture package: “Importar leitura da captura” registra origem capture/automática, confidence e proveniência. Um candidato explicitamente atribuído a outra questão não é importado.
- Texto digitado: “Digitar transcrição” cria a primeira revisão manual, por página associada.
- Edição humana: “Corrigir leitura” cria a revisão seguinte.

O caminho de escrita digital legado continua usando seus snapshots/strokes e o pipeline existente, sem mudanças no editor. A projeção de origem reconhece `digital_ink` quando houver proveniência strokes; D2 não cria um editor de caneta nem transforma imagens em strokes. O reconhecimento de imagem foi testado com o adaptador real e transporte HTTP simulado; não houve chamada paga/externa ao Mathpix na validação manual.

Metadados por página fornecidos pelo capture package permanecem no ExamSubmission imutável de D1; a revisão referencia esse documento e conserva confidence nos segmentos. Não há integração direta entre Luis/Rian e a UI.

## 9. Comparar e responsividade

Desktop: original e transcrição simultâneos, lado a lado, dentro do painel existente; análise ConfIA à direita. Versão/origem aparece também em Comparar. Tela menor (613 × 900): usa a adaptação responsiva existente, com conteúdo em sequência vertical, navegação inferior e painel ConfIA preservados. Não foi introduzido breakpoint novo.

## 10. Edição humana e navegação

Corrigir leitura abre o texto corrente como base. Salvar cria revisão; cancelar descarta o rascunho e recarrega a corrente do servidor. Falhas/conflitos preservam o rascunho para não perder trabalho. Controles de gravação respeitam estado ocupado.

O rascunho fica no cache da questão durante a sessão, com aviso explícito; Q1→Q2→Q1 preserva campos e revisão-base. A página selecionada também permanece entre trocas na sessão. Fechar/recarregar com rascunho aciona o aviso de saída; rascunhos não são persistidos no servidor/localStorage. Um reload sem rascunho recupera a revisão salva e inicia o visualizador na primeira página. Navegar ou cancelar não duplica versões.

## 11. Stale, reanálise, auditoria e estados

O vínculo já existente `AuditRun.transcription_id + revision_number` é a identidade da versão; AuditSource também preserva revisão, aceitação e hashes. Não se reescreve um AuditRun para marcá-lo antigo: o serviço existente deriva `stale` ao comparar com a leitura corrente. O workspace expõe `audit_stale`, `reanalysis_required` e `analysis_state`.

Correção humana sem auditoria nova produz `REANALYSIS_REQUIRED`. Sem qualquer auditoria, `audit_stale` permanece falso: não se inventa um audit. Com audit antigo, ele permanece no histórico e passa a stale. Havendo uma análise corrente concluída, a necessidade de reanálise é atendida; necessidade de revisão humana do resultado continua refletida por `needs_review`.

| Estado projetado | Regra D2 |
|---|---|
| PENDING | Sem leitura |
| REVIEW | Leitura sem análise corrente concluída ou resultado com needs_review |
| READY | Análise corrente concluída, com resultado sem needs_review |
| CONFIRMED | CorrectionCase já DECIDED; D2 não cria essa decisão |

A mesma função deriva estado da questão aberta e das demais questões na navegação. Não há score fabricado. Painel vazio: “Aguardando análise. Nenhuma pontuação foi calculada para esta leitura.” Resultados reais existentes continuam pelo renderer atual, com aviso de stale quando aplicável. Não há novo Semantic Formal, reanálise, ajuste de nota ou finalização no workspace D2.

## 12. Eventos e rastreabilidade

Eventos estruturados são **projeções determinísticas dos registros imutáveis**, e não um novo journal persistido ou fila de mensagens:

- transcription_created: revisão inicial;
- transcription_human_corrected: revisão humana posterior;
- transcription_activated: cada revisão publicada;
- audit_marked_stale: audit anterior e primeira versão posterior que o substituiu.

IDs estáveis incluem transcription_id, revision_number, question_attempt_id e, quando aplicável, audit_run_id. Os três eventos de transcrição levam timestamp/autor da revisão. O evento stale mantém o mesmo ID após novas correções. GET repetido não grava eventos. D4/Levi/Mykael podem consumir a relação; uma futura entrega assíncrona de eventos exigirá mecanismo próprio, fora de D2.

## 13. Testes Python

Python utilizado: `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`, com `PYTHONPATH=app`. Nenhuma dependência nova nesta etapa.

| Execução | Resultado |
|---|---|
| Verificação inicial D1 + submissions | 44 PASS |
| Regressão ampliada de 18 arquivos | 457 PASS, 2 FAIL, 216,23 s |
| Recorte final: workspace + D1 + transcriptions + recognition_invariants + home_summary | 170 PASS, 12,12 s |
| Arquivo D2 final após acrescentar regra needs_review | **8 PASS**, 1,39 s |
| Duas falhas Lean no SHA inicial exportado | 2 FAIL, 2,42 s; mesmas assertions |

Há sobreposição entre execuções; não somar os totais. A regressão ampliada ocorreu antes das últimas ampliações dos testes D2. O recorte final cobre as alterações de integração; após a última correção de projeção de status, o arquivo D2 completo foi executado novamente.

Oito casos D2 (incluindo parametrização PDF/imagem) cobrem primeira leitura, importação, revisão v2/v3, corrente única, predecessor/autor, bytes imutáveis, demo/auth/proprietário, ausência de notas, página fora do escopo, isolamento Q1/Q2, origem PDF/imagem, reconhecimento real do adaptador com quatro páginas e HTTP mock, bloqueio de reprocessamento, congelamento/independência do mapeamento, candidato de outra questão, adulteração de fonte e estados com needs_review.

O teste stale cria um AuditRun real pelo serviço existente com falha do motor deliberadamente simulada, preserva seus bytes, modifica a leitura e verifica stale sem nova execução matemática. Os demais testes existentes de auditoria/aceitação foram mantidos na regressão ampliada.

## 14. Testes JavaScript

Antes de D2: **493 PASS / 0 FAIL**. Final: **498 PASS / 0 FAIL**, 1,28 s, executando toda `tests/js/test_*.cjs`.

Cinco testes novos usam os módulos de produção e cobrem abas/painéis/divisor existentes, ausência de score/decisão fake, multipáginas, Q1→Q2→Q1, asset compartilhado, importação, edição/save/versionamento, histórico, reanálise, rascunho, cancelamento, save sem alteração, digitação inicial e conflito de revisão com preservação do rascunho. A fixture de prova foi extraída para reutilização, mantendo as assertions D1. Os testes de backend usam stores reais; a fixture JS simula apenas as respostas HTTP.

## 15. Regressões e Lean preexistente

Duas falhas da regressão ampliada:

1. `test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved`: technical_error em vez de verified/refuted.
2. `test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`: ausência de refuted.

Reproduzidas em `/tmp/confia-d2-baseline`, exportado integralmente de `c2ebda83ccfaf5816adf7014fc835d53117c2154` via git archive. Artefatos registram `mathlib: cloning https://github.com/leanprover-community/mathlib4` e `external command 'git' exited with code 128`. Mesma indisponibilidade de Mathlib documentada em D1. Não são contadas como regressão D2; não foram relaxadas assertions, alterados checkers nem modificado o motor para obter verde.

Na validação JS intermediária, um teste legado detectou mudança indevida na visibilidade do caption em Comparar; a implementação foi corrigida para limitar a extensão às provas completas. A versão final mantém os 493 testes anteriores passando. O aviso de rascunho também foi limitado ao novo fluxo para não alterar o comportamento do editor legado.

## 16. Validação manual no navegador

Servidor local real em `127.0.0.1:8765`, dados isolados em `/tmp/confia-d2-browser`, modo development/demo sem login. Duas provas sem dados pessoais foram recebidas pelas APIs reais D1: D2-PDF (PDF com quatro páginas) e D2-IMAGENS (quatro imagens). Q1 associada às folhas 1 e 2; Q2 à folha 2. Candidate de captura de demonstração explicitamente identificado como tal, sem nota simulada.

Percurso realizado:

1. `/tme` em demo, abrir a prova PDF da fila e Q1.
2. Conferir Original, Transcrição e Comparar.
3. Importar candidato e observar versão 1 automática/capture.
4. Corrigir leitura e salvar: versão 2 humana e sinalização de reanálise.
5. Q2 mostra folha 2 e nenhuma leitura; voltar Q1 preserva v2.
6. Navegar às duas páginas; abrir histórico e conferir texto intacto de v1.
7. Recarregar e consultar Transcrição: v2 persistida.
8. Criar rascunho, Q1→Q2→Q1, conferir texto não salvo e cancelar; volta v2 sem duplicação.
9. Comparar em 613 × 900; restaurar viewport ao terminar.
10. Abrir D2-IMAGENS e Q1: imagem servida por `assets/original_0001`, sem substituição pelo preview.

Console consultado sem erros/warnings capturados. Após o navegador, os cinco documentos originais (um PDF e quatro imagens) foram conferidos contra seus hashes de manifesto. No store da prova PDF há exatamente v1 e v2, com os textos esperado e corrigido. A verificação automatizada também compara bytes antes/depois da edição; evidência manual complementar em `persistence-check.json`.

## 17. Arquivos modificados

Produção:

- `app/confia_lean_auditor/recognition/{mathpix_image.py,schemas.py,service.py}`: aceitar fontes/páginas da prova pelo reconhecimento existente.
- `app/confia_lean_auditor/submissions/{schemas.py,store.py}`: fonte congelada e proveniência capture, reutilizando persistência/versionamento.
- `app/confia_lean_auditor/tme/{question_review.py,review_models.py}` (novos): orquestração/projeção e contratos de fonte/importação.
- `app/confia_lean_auditor/tme/{exam_router.py,router.py,store.py}`: APIs e binding da fonte.
- `app/confia_lean_auditor/tme/home_summary.py`: não inserir fontes de prova completa nos índices legados por caso.
- `app/confia_lean_auditor/static/tme/{tme.js,full-exam.js,correction-workspace.js,index.html}`: integrar QuestionAttempt ao workspace existente.

Testes/documentação:

- `tests/test_tme_review_workspace.py` (novo).
- `tests/js/test_review_workspace.cjs` e `tests/js/exam-fixture.cjs` (novos).
- `tests/js/test_full_exam.cjs` (fixture compartilhada; assertions preservadas).
- Este relatório e `docs/audits/assets/tme-december-d2/`.

## 18. Riscos e limites

- Store local e locks de arquivo seguem o protótipo existente. O primeiro reconhecimento mantém o lock do store de provas durante a chamada ao provedor para serializar fonte/importação/mapeamento; isso limita concorrência e deve ser tratado antes de escalar o serviço.
- Limite de 50 páginas aceita D1, mas reconhecimento mantém prazos/limites do provedor atual; não se promete sucesso de OCR de uma prova longa inteira.
- Mapeamento da questão congela ao criar fonte. Corrigir associação depois desse ponto demanda fluxo explícito futuro; não se reatribui uma leitura existente silenciosamente.
- Rascunho existe apenas na sessão; o aviso de saída depende do navegador. A leitura salva e o histórico persistem no servidor.
- Candidato sem question_hint em folha compartilhada só é importado por ação explícita; exige conferência humana. Com hint de outra questão é recusado.
- Região/spans não são recalculados automaticamente após edição; página inteira conserva a origem correta.
- Eventos são derivados, sem journal de entrega. Certificação estatística continua fora do escopo.
- Comparação visual usou os componentes reais preservados, sem alterar CSS. Não constitui comparação pixel a pixel de frames do vídeo institucional.
- Mathlib precisa estar disponível para os dois testes Lean reais; essa limitação preexistente permanece.

## 19. Comandos de reprodução

A partir do worktree:

```sh
/usr/local/bin/node --test tests/js/test_*.cjs
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_review_workspace.py tests/test_tme_full_exam.py tests/test_transcriptions.py tests/test_recognition_invariants.py tests/test_tme_home_summary.py
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_review_workspace.py tests/test_tme_full_exam.py tests/test_submissions.py tests/test_transcriptions.py tests/test_recognition.py tests/test_recognition_invariants.py tests/test_recognition_preview.py tests/test_mathpix_strokes.py tests/test_tme_pilot.py tests/test_tme_photo_errors.py tests/test_tme_home_summary.py tests/test_tme_demo_auth.py tests/test_assessments.py tests/test_teacher_decisions.py tests/test_core_auth.py tests/test_core_institutional.py tests/test_tme_accepted_integration.py tests/test_submission_audits.py
```

Servidor da sessão, com as variáveis isoladas registradas em `/tmp/confia-d2-environment.py`:

```sh
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -c "exec(open('/tmp/confia-d2-environment.py').read()); import uvicorn; uvicorn.run('confia_lean_auditor.main:app', host='127.0.0.1', port=8765)"
```

Esse arquivo define CONFIA_ENV=development, CONFIA_AUTH_ENABLED=1, CONFIA_TME_DEMO_NO_AUTH=1 e os diretórios AUTH, INSTITUTIONAL, ASSESSMENTS, ASSESSMENT_PARTICIPANTS, TME_EXAMS, TME_CASES, SUBMISSIONS e SUBMISSION_AUDITS sob `/tmp/confia-d2-browser`. Arquivos de `/tmp` são evidência temporária local, não requisito novo da aplicação. Servidor de validação encerrado ao finalizar o trabalho.

Reprodução das duas falhas sem mudanças D2:

```sh
mkdir -p /tmp/confia-d2-baseline
git archive c2ebda83ccfaf5816adf7014fc835d53117c2154 | tar -x -C /tmp/confia-d2-baseline
cd /tmp/confia-d2-baseline
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline
```

## 20. Evidências e veredito

Arquivos em `docs/audits/assets/tme-december-d2/`:

| Evidência | Conteúdo |
|---|---|
| [compare-v1.jpg](assets/tme-december-d2/compare-v1.jpg) | Captura importada, Comparar e painel aguardando análise |
| [compare-v2.jpg](assets/tme-december-d2/compare-v2.jpg) | Versão humana salva e reanálise necessária |
| [history-preserved.jpg](assets/tme-december-d2/history-preserved.jpg) | Texto anterior consultável e links dos originais |
| [compare-mobile.jpg](assets/tme-december-d2/compare-mobile.jpg) | Layout responsivo existente com v2 |
| [original-images.jpg](assets/tme-december-d2/original-images.jpg) | Prova de múltiplas imagens, original real |
| [persistence-check.json](assets/tme-december-d2/persistence-check.json) | Hashes dos cinco originais e duas revisões da demonstração |
| [test-results.txt](assets/tme-december-d2/test-results.txt) | Resumos das execuções |
| [lean-baseline.txt](assets/tme-december-d2/lean-baseline.txt) | Duas falhas reproduzidas no SHA inicial |

`git diff --check` sem erros. Nenhuma alteração staged e nenhum commit. D2 concluído com a ressalva explícita da infraestrutura Lean preexistente; integração, versionamento e navegação cobertos pelas verificações acima.

READY_FOR_DECEMBER_D3
