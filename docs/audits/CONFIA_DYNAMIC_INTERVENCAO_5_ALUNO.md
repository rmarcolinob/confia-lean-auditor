# ConfIA DYNAMIC — Intervenção 5: atividades escolares do aluno

26/11/2026. Implementação experimental na branch `codex/dynamic-development`, worktree `artifacts/worktrees/confia-dynamic-development`. A nova integração estudantil permanece sem commit e sem push, para revisão. Não foi criado outro corretor.

## Resultado

O professor pode publicar uma atividade DYNAMIC preparada para uma turma institucional. O aluno autenticado acessa os enunciados autorizados, registra soluções textuais ou originais fotográficos/PDF, associa páginas, revisa transcrições, confirma explicitamente a leitura e envia ao núcleo DYNAMIC existente. O professor revisa/adjudica, finaliza e autoriza separadamente a divulgação. O aluno consulta apenas suas tentativas e os resultados liberados.

A demonstração utilizou três questões sintéticas do 9º ano, com OCR e pareceres semânticos simulados. A pontuação sugerida foi 2 + 1,5 + 0 = 3,5/6; a nota só apareceu ao aluno após confirmação e divulgação docente. Esse resultado verifica integração e regras da rubrica de teste, não qualidade matemática de um modelo real.

## Etapa 0: ocorrência HTTP 409 e publicação docente

A ocorrência original em `test_complete_summary_snapshots_totals_review_gold_and_finalized_list` não foi reproduzida sob a configuração correta da suíte. O cenário passou 20 vezes consecutivas e a regressão anterior à intervenção estudantil passou com 587 testes Python e 80 testes JavaScript dirigidos. Não foram observados conflitos de versões, corrupção ou concorrência que estabelecessem um bloqueio funcional reproduzível.

Uma sonda executada inicialmente sem o `conftest` reproduziu HTTP 409 com a política padrão `semantic-b-minimal.v1`: a fixture incompleta de P2 tinha subtotal 15 e total indeterminado; a confirmação humana corretamente rejeitou uma auditoria não pontuável. Esse resultado demonstra sensibilidade à configuração, mas **não prova a causa da ocorrência original**. Os artefatos daquela ocorrência não estavam disponíveis para estabelecer sua causa exata. O teste não foi relaxado e nenhuma correção matemática foi feita para eliminar o 409.

Os 13 arquivos da intervenção manuscrita docente foram inventariados e examinados quanto a dados sensíveis, registrados e publicados exclusivamente na branch DYNAMIC:

- Commit: `57517f337cc0531f0c7069556050aa95350d811a`.
- Mensagem: `feat(dynamic): integrate handwritten activity review with explicit reading confirmation`.
- Remoto original: `github.com/rmarcolinob/confia-lean-auditor`.
- HEAD local e referência remota coincidiram após a publicação.

Nenhuma alteração estudantil deste relatório está nesse commit. A main não foi integrada. A tag anotada `SPECIALIZED-TME2-RC1` continua com objeto `0c64e318a26e21f71fe3097c66ee17a5206dd8a3`, apontando para `c03403fe5b83d9db9df172882bd69af3dfa2d027`.

## Contratos e regras da integração

### Publicação e acesso

`SchoolPolicy` (`dynamic-classroom-policy.v1`) acrescenta política institucional opcional, com etapa escolar, modos de entrada, número máximo de tentativas, feedback e exigência de divulgação docente. Datas de abertura/encerramento fazem parte da definição publicada. Atividades somativas não aceitam divulgação orientadora automática.

A publicação cria outro Assessment institucional, copiando os vínculos aprovados e seus hashes; não troca o escopo do registro docente histórico. Enunciados e rubricas permanecem fixados por versão. Alterar posteriormente um problema não substitui o conteúdo publicado. O gateway exige sessão real, papel apropriado, vínculo docente à turma e matrícula estudantil; não atribui privilégios docentes ao estudante. Atividades agendadas não disponibilizam os enunciados pelo novo endpoint.

O aluno recebe uma projeção por lista permitida. Contextos internos de rubricas, preparações, referências, eventos docentes e pareceres brutos ficam fora dessa projeção. O acesso às tentativas e aos originais verifica o autor, inclusive entre colegas da mesma turma. As rotas genéricas de escrita não permitem contornar a política do gateway em submissões escolares vinculadas.

### Autoria e estados

`SchoolAttemptBinding` (`dynamic-school-attempt.v1`) registra aluno, professor, número da tentativa, hash da política e serviço `dynamic-school-audit.v1`. O participante é um usuário registrado. Os casos internos continuam sob responsabilidade docente, mas os originais registram o aluno como autor.

A confirmação manuscrita registra `reviewer_role=STUDENT` ou `TEACHER`, separadamente da aceitação técnica. A interface docente identifica uma leitura conferida pelo aluno sem atribuir-lhe conferência docente. O serviço interno aceita tecnicamente a revisão selecionada com identidade humana não verificada; esse passo não substitui a confirmação explícita de leitura.

`school_submission.json` preserva o instante de envio, o autor, a definição e as revisões selecionadas. Depois do envio, a tentativa fica imutável para o aluno. Antes disso, uma edição cria revisão nova e exige confirmação do texto corrente. A interface conserva rascunhos ainda não salvos e bloqueia envio, nova associação ou reconhecimento que os descartaria silenciosamente.

Estados projetados distinguem rascunho, avaliação pendente, erro técnico, revisão pendente, espera pelo professor e confirmação docente. Ausência de resultado divulgado é apresentada como retenção/pendência, nunca como zero. Uma repetição com a mesma chave reutiliza a tentativa e os serviços idempotentes; não cria uma nova nota.

### Correção e divulgação

A execução passa pelo `CorrectionEngine`/AuditService, Grader DYNAMIC, `DynamicReviewService` e `ReconciliationService` já existentes, com a rubrica aprovada. Crédito parcial e dependências não foram reimplementados. Adjudicação, decisões humanas e `FinalCorrection` também são reutilizados.

A divulgação escreve um registro versionado e selado vinculado ao ID e hash da finalização corrente. O endpoint não recebe uma nota livre: publica a nota da finalização. Uma finalização reaberta ou substituída deixa de corresponder ao registro divulgado. Pontuação e comentário pedagógico possuem controles separados; `WITHHOLD` bloqueia explicações. Sugestão automática não é nota escolar oficial.

As orientações formativas automáticas são mensagens conservadoras sobre passos aproveitáveis e necessidade de justificar/revisar. Não publicam texto bruto de LLM nem soluções completas. Explicações específicas podem ser redigidas pelo professor e liberadas; geração automática de feedback detalhado adequado à etapa escolar ainda exige validação adicional.

### Captura e compatibilidade

Texto, fotografias e PDF usam a infraestrutura existente. Os originais conservam hashes e tamanhos; corrupção impede leitura. Uma questão pode ocupar várias páginas e a mesma página pode ser associada a questões diferentes. Cada transcrição seleciona somente os trechos pertinentes, com confirmação explícita do escopo. Não há segmentação automática confiável presumida.

Os campos novos são opcionais e omitidos quando ausentes, preservando a serialização histórica. Não há migração de AuditRuns ou fixtures. Na finalização compartilhada, o identificador do participante passa a aceitar o usuário registrado quando não há código externo; soma e decisões permanecem iguais. As rotas TME existentes continuam disponíveis. PautaEngine, Semantic B, verificadores, teoremas Lean e rubricas históricas não foram modificados.

## Arquivos da intervenção estudantil

Caminhos relativos a este worktree, agrupados por responsabilidade:

| Responsabilidade | Arquivos |
|---|---|
| Novos contratos, autorização e orquestração escolar | `app/confia_lean_auditor/dynamic/school_contracts.py`, `school_scope.py`, `school_service.py`, `school_router.py` |
| Publicação institucional e projeção sem informações restritas | `app/confia_lean_auditor/assessments/models.py`, `router.py`, `store.py`; `app/confia_lean_auditor/dynamic/assessment_service.py` |
| Registro das rotas e proteção das escritas genéricas | `app/confia_lean_auditor/main.py`; `app/confia_lean_auditor/auth/dependencies.py` |
| Interface do aluno e publicação/divulgação docente | novo `app/confia_lean_auditor/static/dynamic-student.js`; `dynamic-assessment.js`, `resolution-workspace.js`, `index.html`, `tme/tme.js` no mesmo diretório estático |
| Proveniência escolar das auditorias | `app/confia_lean_auditor/submission_audits/schemas.py`, `service.py` |
| Autoria dos originais, confirmação da leitura e limites de entrada | `app/confia_lean_auditor/submissions/reading_confirmation.py`, `store.py`, `text_source.py`, `body_limit.py` |
| Reutilização da captura e participantes registrados | `app/confia_lean_auditor/tme/exam_models.py`, `exam_store.py`, `question_review.py`, `router.py`, `store.py`, `finalization.py` |
| Regressões | novo `tests/test_dynamic_school.py`; novo `tests/js/test_dynamic_student.cjs`; `tests/js/test_dynamic_ui_convergence.cjs`, `tests/js/test_student_tutor_exams.cjs` |
| Relatório | `docs/audits/CONFIA_DYNAMIC_INTERVENCAO_5_ALUNO.md` |

## Navegador

Foi utilizado servidor local isolado em `http://127.0.0.1:8766`, com contas e dados sintéticos temporários e providers simulados. Nenhuma credencial de produção ou serviço pago foi utilizado. O servidor de demonstração é temporário, não o ambiente institucional.

Percursos demonstrados:

1. Professor: abrir DYNAMIC, selecionar atividade preparada, publicar para escola/turma com política e consentimento explícito.
2. Aluno: `/#student/exams`, abrir atividade, registrar três respostas textuais, enviar, consultar estados e histórico sem nota antecipada.
3. Professor: consultar evidências no workspace compartilhado, confirmar questões, finalizar e divulgar nota/comentário.
4. Aluno: visualizar o resultado liberado e o comentário do professor.
5. Nova tentativa fotográfica: três páginas, Q1 nas páginas 1–2, Q2 também na página 2, Q3 na página 3; reconhecimento simulado, correção do texto por questão, confirmação como aluno e envio. A tentativa anterior permanece no histórico.
6. Navegação e ativação de controles nativos por teclado, incluindo Enter em acesso à atividade, formulários e envio. Não foi realizada auditoria completa de acessibilidade.

A verificação visual detectou e corrigiu um filtro legado que ocultava atividades DYNAMIC quando não pertenciam ao catálogo de questões preparadas. O caderno/TutorIA existente não foi reconstruído.

Capturas locais (não publicadas): `/private/tmp/confia-i5-student-result.jpg` e `/private/tmp/confia-i5-student-photos.jpg`.

## Testes e evidências de validação

Resultados de execuções distintas; os números abaixo não devem ser somados como testes únicos:

| Execução | Resultado |
|---|---|
| Base docente antes da intervenção estudantil | 587 Python e 80 JavaScript dirigidos aprovados |
| Sonda do fechamento TME com a configuração da suíte | 20 repetições aprovadas |
| Regressão ampliada final DYNAMIC, captura, finalização, auditorias, autenticação e instituições | **572 aprovados, 2 skips, 1 deselecionado**, 288,87 s |
| Suíte estudantil final após os últimos reforços | **8 aprovados**, 53,70 s |
| Teste Lean real isolado deselecionado da execução ampliada | **1 aprovado**, 92,22 s |
| JavaScript completo (`node --test tests/js/*.cjs`) | **610 aprovados**, sem skips/falhas |
| `git diff --check` | Aprovado |

Os dois skips são os testes dependentes de `Frozen local DEV pack`, indisponível neste worktree, em `test_tme_model_compat.py`. O teste executado isoladamente foi `test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`.

Na primeira regressão ampliada ocorreram duas falhas: a verificação Lean real e `test_new_audit_same_reading_invalidates_and_rejects_old_audit`. A primeira tinha evidência persistida de tentativa de obter Mathlib (`git` com saída 128) por falta das dependências locais no worktree. Foram conferidos os HEADs dos nove pacotes contra `lake-manifest.json` e reutilizados os caches locais ignorados pelo Git. Os fontes Lean correspondentes foram comparados antes da reutilização dos objetos compilados. Lean 4.28.0 passou no teste real isolado; não foram alterados fontes, toolchain ou manifesto. O teste de confirmação humana passou isoladamente e na regressão ampliada final; a causa da ocorrência transitória não foi estabelecida e não deve ser atribuída a Lean sem evidência.

Os testes escolares cobrem publicação sem mutação da origem, pinning, autenticação e isolamento inclusive na mesma turma, enunciado agendado, prazo/quota/idempotência, fonte não enviada que não conta como submissão, texto, fotografias e páginas compartilhadas, OCR simulado, revisão e confirmação com autoria estudantil, integridade dos originais, créditos integral/parcial/zero, discordância, abstenção, falha técnica, adjudicação, homologação e retenção/divulgação. Os testes JavaScript cobrem também leituras não salvas e a listagem de atividades fora do catálogo preparado.

Comandos principais, a partir do worktree DYNAMIC (o interpretador validado é o `.venv` do repositório principal):

```sh
export PYTHONPATH=app
export PYTHONDONTWRITEBYTECODE=1
export CONFIA_SEMANTIC_LLM_ENABLED=0
export CONFIA_DYNAMIC_LLM_ENABLED=0
unset OPENAI_API_KEY
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/test_dynamic_school.py
node --test tests/js/*.cjs
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/test_dynamic*.py tests/test_tme_full_exam.py tests/test_tme_question_audit.py tests/test_tme_finalization.py tests/test_tme_human_confirmation.py tests/test_tme_reanalysis.py tests/test_tme_review_workspace.py tests/test_tme_model_compat.py tests/test_tme_home_summary.py tests/test_tme_demo_auth.py tests/test_submission_audits.py tests/test_assessments.py tests/test_core_auth.py tests/test_core_institutional.py -k 'not test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline'
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline
git diff --check
```

Logs e capturas foram copiados para `artifacts/qa/dynamic-intervention5/`, ignorado pelo Git. Nenhuma auditoria paga ou dado real identificável de aluno foi utilizado. A varredura dos arquivos alterados não identificou credenciais reais; as credenciais dos providers nos testes são valores simulados.

## Limitações e próximos passos

- O percurso institucional está funcional nos cenários controlados, mas não constitui validação científica de correção de soluções independentes.
- OCR real, interpretação de manuscritos, LLM real, custo, latência e estabilidade sob carga não foram avaliados. A existência de um parecer de LLM não implica certificação Lean.
- O caderno digital anterior permanece disponível; seus traços ainda não são vinculados diretamente a esta nova tentativa institucional. A política desta intervenção oferece TEXT, IMAGES e PDF.
- PDFs usam o recebimento/renderização existentes, cobertos pelas regressões compartilhadas; a demonstração estudantil no navegador utilizou texto e PNGs, não um PDF real.
- Cada tentativa abrange todas as questões obrigatórias. A reserva de uma tentativa ocorre ao criá-la, inclusive antes do envio; não há cancelamento que recupere a quota. A interface informa essa regra.
- Operações são síncronas. Falhas técnicas não geram zero; a repetição idempotente não garante uma nova chamada ao provider. Revisão/retomada docente usa o workspace existente. Não foi criado worker ou novo sistema de filas.
- Associação e delimitação textual de respostas continuam exigindo conferência humana. Não há garantia automática de fidelidade de uma transcrição ao manuscrito.
- A qualidade pedagógica das orientações automáticas é limitada. Explicações matemáticas contextualizadas devem ser revistas antes de ampliar a divulgação automática.
- A causa da ocorrência HTTP 409 original continua não demonstrada; os testes corretos e repetidos não evidenciaram bloqueio reproduzível. Preservar logs e artefatos completos se reaparecer.

A próxima intervenção mínima é um contexto próprio de estudo autônomo do estudante, com rubrica gerada explicitamente provisória/formativa, isolamento por autor e ausência de nota escolar oficial. Deve reutilizar os mesmos serviços DYNAMIC, captura, proveniência e histórico, acrescentando uma política de feedback progressivo. Não deve simular privilégios docentes, reutilizar rubricas restritas ou criar outro motor. Essa extensão não foi implementada aqui.

## Consolidação autorizada na Intervenção 6

Na revisão de 26/11/2026, antes de iniciar o estudo autônomo, os 32 arquivos desta intervenção passaram pela conferência de escopo e varredura de padrões de credenciais. A validação dirigida repetiu 51 testes Python aprovados, dois skips e 610 testes JavaScript aprovados, além de `git diff --check`. Não houve bloqueio funcional reproduzível.

Os dois casos omitidos são `test_real_smoke_dry_run_separates_semantic_hashes_from_transport` e `test_transport_builder_does_not_weaken_holdout_guard`, em `tests/test_tme_model_compat.py`: dependem do pacote DEV local congelado, não versionado neste worktree. São skips, não deseleções. Cobrem o plano offline de comparação de transporte entre modelos e o impedimento de incluir IDs fora do conjunto DEV. Os testes de contrato de transporte sem esse pacote passaram. O teste Lean deselecionado na execução ampliada anterior foi distinto e passou isoladamente, conforme registrado acima.

O usuário autorizou o registro e a publicação desta integração institucional na etapa 0 da Intervenção 6. As alterações posteriores de estudo autônomo permanecem fora desse registro. Nenhum dado de aluno, log local, imagem ou bundle experimental é incluído no commit.
