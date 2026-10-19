# P2-DEC-01 — Decisão do professor

## Autoridade e escopo

`AuditRun` registra a análise e a pontuação **sugeridas pelo ConfIA**.
`TeacherDecision` registra a decisão humana sobre uma Submission institucional.
O score do Auditor nunca se torna uma pontuação final automaticamente. O professor
informa a pontuação, finaliza a decisão e, em uma ação separada, libera o resultado.

A implementação consome os contratos existentes de Submission, Assessment,
AssessmentItem e AuditRun. Não modifica execução da auditoria, extração de claims,
rubrica, política de score, Lean, manifests GOV-01, Mathpix, RecognitionRun,
TranscriptionRevision ou o significado de ACCEPTED (fidelidade da transcrição).
TutorIA mantém seu fluxo de prática; a projeção restrita descrita aqui é o resultado
da correção institucional de Exames.

## Contratos e provenance

Os modelos Pydantic 2 usam `extra="forbid"` e rejeitam números não finitos.
`TeacherDecision` contém os IDs da decisão, Submission, Assessment, AssessmentItem,
problema e professor responsável; o hash da definição publicada; o máximo do item;
os campos docentes; o ciclo de vida; timestamps UTC; versão para concorrência;
hash final e `schema_version="1.0"`.

Quando há análise selecionada, preserva também `audit_run_id`, `audit_source_sha256`,
`audit_result_sha256`, `confia_score_raw`, `confia_max_score_raw` e
`confia_suggested_points`. Não copia manuscrito, claims ou relatório técnico para a
decisão. Estudante, turma e escola continuam derivados da Submission, sem identidades
duplicadas na decisão.

O backend resolve todos os vínculos a partir da Submission persistida, da sessão e
da definição publicada do Assessment. Ele confere item, problema, escola, rede,
turma, máximo e hash da definição. O navegador pode enviar apenas a seleção de um
AuditRun e campos editáveis docentes; não pode fornecer os valores de provenance.

`teacher_user_id` identifica o último professor que salvou o rascunho e, ao
finalizar, o professor que assumiu a decisão. Um professor com atribuição ativa na
mesma turma pode continuar o único rascunho existente. A liberação preserva o autor
da finalização; este MVP não mantém um histórico separado de editores do rascunho
ou da identidade de quem liberou a decisão.

## Ciclo de vida e concorrência

| Estado | Edição | Visibilidade ao aluno | Ação seguinte |
| --- | --- | --- | --- |
| `DRAFT` | Campos docentes e seleção da análise | Nenhum resultado | Salvar ou finalizar |
| `FINALIZED` | Conteúdo congelado | Nenhum resultado | Liberar |
| `RELEASED` | Conteúdo congelado | Projeção reduzida | Nenhuma edição |

Há no máximo uma decisão por Submission nesta versão, inclusive após liberação.
O ID determinístico `dec_<UUID da Submission>` e o lock do store impedem duplicação
em retries e duplo clique. Um novo POST retorna a existente, sem atualizar a seleção
da análise ou qualquer outro campo.

PATCH e finalize recebem `expected_version`. Um rascunho alterado por outra aba
gera HTTP 409. Finalize repetido após finalização retorna a decisão existente;
release repetido preserva timestamps, versão e conteúdo. PATCH após finalização
e release antes da finalização retornam 409. A interface bloqueia navegação durante
uma operação ou enquanto houver alterações não salvas, oferecendo salvar, descartar
e recarregar a versão persistida.

## Pontuação, análise selecionada e override

A escala do Auditor é independente dos pontos do item:

```text
confia_suggested_points = AssessmentItem.points × AuditRun.result.score / AuditRun.result.max_score
Exemplo: item 5 pontos; ConfIA 8/10 → sugestão 4,00/5,0
```

O backend usa `Decimal(str(valor))` para os valores provenientes dos contratos
existentes com float. A sugestão usa duas casas decimais e `ROUND_HALF_UP`.
Pontuações finais aceitam até duas casas, entre zero e o máximo obtido do servidor.
Excesso de precisão é rejeitado, sem arredondar silenciosamente a entrada docente.
Decimais são serializados como strings JSON; a interface formata em português e
aceita vírgula ou ponto na entrada manual.

AssessmentItems antigos podem ter mais de duas casas decimais. Seu máximo exato é
preservado; se o arredondamento da sugestão exceder esse máximo, a sugestão fica
limitada ao maior centésimo que não o excede. Não há alteração do AssessmentItem.

Sem análise, score null, escala não positiva, score fora da escala, execução FAILED,
avaliação indeterminada ou `technical_error` nos critérios, microclaims ou relatório,
a sugestão é null. Os valores brutos disponíveis permanecem no snapshot. O professor
pode informar a pontuação final sem justificar override quando a sugestão é null.

A seleção é explícita: “Iniciar decisão com análise aberta” ou “Iniciar decisão
manual”. O painel identifica a análise aberta e mantém o ID e a escala original
em um disclosure. “Usar sugestão” apenas copia a sugestão para o campo de pontuação.
Não salva, finaliza ou libera.

O backend valida o AuditRun selecionado com o serviço existente, inclusive integridade
e freshness. Um run stale não pode criar uma decisão nem substituir o snapshot.
Ao finalizar, o backend verifica novamente a análise e compara o snapshot persistido.
Se ela ficou stale ou indisponível, o professor pode vincular uma análise atual ou
escolher explicitamente “Decidir sem sugestão ConfIA”. Nenhum run mais recente é
selecionado automaticamente. Entre vários runs atuais, qualquer um pode ser escolhido
explicitamente; seu ID exato fica preservado.

Se a pontuação final divergir da sugestão normalizada, `override_reason` não vazio é
obrigatório antes da finalização. O rascunho pode ser salvo sem justificativa. A
comparação é decimal. `teacher_feedback` é pedagógico e publicável;
`teacher_internal_note` e `override_reason` são internos.

## API

Todas as respostas de sucesso usam `Cache-Control: no-store`. As mutações mantêm
sessão e proteção de mesma origem do aplicativo.

| Método e rota | Contrato |
| --- | --- |
| POST `/submissions/{submission_id}/teacher-decision` | `{}` para manual ou `{ "audit_run_id": "aud_…" }`; 201 na criação, 200 se já existe |
| GET `/submissions/{submission_id}/teacher-decision` | Decisão completa e `audit_state` derivado; `null` se não existe |
| PATCH `/teacher-decisions/{decision_id}` | `expected_version` e campos explicitamente enviados: pontuação, feedback, nota interna, justificativa, seleção de análise |
| POST `/teacher-decisions/{decision_id}/finalize` | `{ "expected_version": 1 }`; congela e calcula hash |
| POST `/teacher-decisions/{decision_id}/release` | Sem corpo; libera a decisão já finalizada |
| GET `/student/assessments/{assessment_id}/items/{item_id}/result` | Resultado próprio liberado ou `null` |

Exemplo de PATCH:

```json
{
  "expected_version": 1,
  "teacher_final_points": "4.00",
  "teacher_feedback": "Boa solução. Justifique também a última etapa.",
  "teacher_internal_note": "Observação reservada ao professor."
}
```

`audit_run_id: null` no PATCH remove explicitamente a sugestão e sua provenance do
rascunho. Omitir esse campo preserva a seleção anterior. Campos desconhecidos e
pontuações inválidas retornam 422; conflitos de estado, versão e integridade
retornam 409; falta de vínculo docente retorna 403.

## Autorização e privacidade

Somente `TEACHER` autenticado com TeacherAssignment ativo para escola, turma e ano
da avaliação acessa ou altera decisões completas. O mesmo tenant, `classroom_ids`
do usuário ou uma permissão de leitura de legado não substituem a atribuição.
Os vínculos são reavaliados em cada operação. Alunos e gestores recebem 403 nas
rotas docentes. Decisões institucionais não operam no modo sem autenticação.

O endpoint do aluno deriva a matrícula ativa, verifica a avaliação da turma e filtra
Submissions pelo `submitted_by_user_id` da sessão. Outro aluno da mesma turma recebe
`null` para uma questão que ainda não tenha seu próprio resultado. Avaliações de
outra turma ficam ocultas. Nenhum ID de aluno é aceito como parâmetro de seleção.

A projeção `StudentResult` permite exatamente:

```json
{
  "assessment_id": "asmt_…",
  "item_id": "ait_…",
  "problem_id": "ITA2025F2Q1",
  "status": "corrected",
  "final_points": "4.00",
  "max_points": "5.0",
  "teacher_feedback": "Boa solução…",
  "released_at": "2026-10-18T12:00:00Z"
}
```

Não contém sugestão, score bruto, audit_run_id, claims, evidências, Lean, justificativa
de override, nota interna ou hash da decisão. A mesma projeção compõe
`released_results` nas respostas existentes de Assessment para o aluno. Esse campo
fica vazio para o professor. As rotas docentes de análise continuam inacessíveis ao
aluno. Conteúdo textual é renderizado com textContent, sem interpretar HTML.

## Interfaces e governança

O painel “Decisão do professor” aparece abaixo da Análise ConfIA, com sugestão
normalizada, pontuação manual, feedback, nota interna e justificativa condicional.
Após finalizar só resta a ação de liberação; depois de liberar não há controles
editáveis. A fila de soluções mostra o estado persistido da decisão.

O progresso do Assessment fornece `correction_statuses` tipado por item:
`SUBMITTED`, `TRANSCRIPTION_REVIEW`, `ANALYSIS_AVAILABLE`, `DECISION_DRAFT`,
`DECISION_FINALIZED` e `RESULT_RELEASED`. Esses estados aparecem em Exames e
Alunos da turma. ACCEPTED sozinho não significa análise disponível.

No aluno, o status de entrega continua derivado da existência de Submission
(“Não enviada”/“Enviada”). O status de correção mostra espera até a liberação e
“Corrigida” após RELEASED. Só então aparecem “Pontuação” e “Feedback do professor”.
O progresso de entregas e o contador de questões corrigidas são apresentados
separadamente. Não existe seção Feedback ConfIA no resultado do exame.

Os endpoints de gestão acrescentam somente contadores dentro do escopo institucional:

- `decisions_finalized_count`: decisões FINALIZED ou RELEASED;
- `decisions_released_count`: decisões RELEASED;
- `override_count`: decisões finalizadas, incluindo liberadas, com pontuação divergente.

Rascunhos não contam como overrides. Não há texto de feedback, nota interna,
justificativa ou manuscrito nos agregados. Dados indisponíveis/inválidos não são
convertidos em contadores fictícios. A seleção de análise, score normalizado,
pontuação final e justificativa ficam disponíveis para futuras métricas de
confiabilidade, sem dashboard avançado nem treinamento automático.

## Persistência e integridade

O diretório padrão é `runtime/teacher_decisions/`, ignorado pelo Git. Pode ser
alterado por `CONFIA_TEACHER_DECISIONS_DIR`. Diretório 0700, arquivos 0600, flock
exclusivo entre processos, arquivo temporário no mesmo diretório, fsync e replace
atômico protegem as transações locais. Leituras validam schema, ID, vínculo com a
Submission e hash final. Arquivos e raiz simbólicos são rejeitados.

`decision_sha256` usa a serialização JSON canônica já adotada pelo projeto
(UTF-8, chaves ordenadas, separadores compactos). Ele inclui todos os dados finais,
inclusive nota interna, professor, snapshot de análise, máximo, pontuação, feedback,
justificativa, timestamps de criação/finalização e versão do schema. Exclui apenas
hash próprio, status, updated_at, released_at e versão de concorrência.

A liberação muda somente status, released_at, updated_at e versão de concorrência.
O store verifica essa restrição além do serviço. Uma análise que fique stale após
a finalização não altera a decisão humana histórica nem impede sua liberação.
O hash detecta divergências de conteúdo; não é assinatura digital nem proteção
contra um administrador com acesso de escrita aos arquivos e capacidade de recalculá-lo.

## Testes e demonstração

Executar na raiz do repositório:

```sh
CONFIA_ENABLE_LLM_FORMAL_STEPS=0 .venv/bin/python -m pytest -q
node --test tests/js/*.cjs
lake build
git diff --check
git status --short
```

`tests/test_teacher_decisions.py` cobre autorização, binding, normalização 8/10→4/5,
ausência de score, falha técnica, limites/precisão, override, congelamento, idempotência,
concorrência, adulteração, stale, múltiplas análises, privacidade, agregados e legado.
`tests/js/test_teacher_decisions.cjs` exercita eventos e transporte do painel,
proteção de alterações não salvas, manual, sugestão, override, salvar/finalizar/liberar
e o resultado restrito do aluno. Os testes de UI existentes foram atualizados para
os estados e a separação entrega/correção.

O teste `test_demo_end_to_end_submission_acceptance_analysis_finalization_release`
usa aluno.demo e professor.demo, CETI Centro, 2ª série A, Avaliação 1/Q1: entrega real
pelo endpoint, transcrição e aceite persistidos, AuditRun 8/10, decisão 4/5,
feedback, finalização, liberação e consulta pelo aluno. O motor de auditoria usa
um fixture determinístico nesse cenário, sem chamar Mathpix ou gerar uma nova
avaliação matemática externa. A suíte de regressão do Auditor/Lean permanece separada.

O mesmo percurso foi conferido no navegador com servidor e dados temporários: o
aluno não via pontuação após FINALIZED, passou a ver 4,0/5,0 e feedback docente
após RELEASED, e a nota interna permaneceu ausente. Não houve erros no console
nessa verificação. Nenhum dado demo do runtime habitual foi alterado.

Validação local em 18/10/2026:

- Python focado (`test_teacher_decisions.py`, `test_assessments.py` e
  `test_ui_03_teacher_workflow.py`): **67 aprovados**.
- JavaScript (`node --test tests/js/*.cjs`): **278 aprovados**. Após o ajuste final
  do rótulo acessível da fila, os **10 testes de decisões** passaram novamente.
- `lake build`: aprovado.
- `git diff --check`: sem erros.
- A execução adicional da suíte Python integral foi interrompida nos cenários
  matemáticos antigos após **153 aprovados e 1 skipped**, sem falhas até esse ponto.
  Esse resultado parcial não certifica aprovação da suíte integral nem da CI.

Para demonstração manual com os usuários demo existentes, abrir a Avaliação 1 como
aluno e enviar Q1; abrir o envio da turma como professor, conferir a transcrição,
abrir/executar Análise ConfIA, iniciar a decisão com a análise aberta, usar sugestão
ou informar pontuação, escrever feedback, finalizar e liberar. Reabrir Exames como
aluno: Q1 mostra Corrigida, pontuação e feedback docente. Antes da liberação, esses
dados não aparecem.

## Limitações e evolução

Submissions sem Assessment continuam legíveis e não recebem decisão institucional
nem reatribuição histórica. Não há edição de decisão final, amendment, recurso do
aluno, segunda correção, nova rubrica manual, diário, boletim ou integração SEDUC.
Uma correção futura deverá criar revisão/superseding decision explícita, mantendo
a decisão original e a rastreabilidade de publicação.

O store usa filesystem POSIX local e lock global, adequado ao MVP em um host.
Consultas de progresso/agregados percorrem os registros; para volume maior, o adapter
PostgreSQL deverá manter UNIQUE(submission_id), transações, locks por linha,
controle de versão, validação de hash e projeções com a mesma autorização.
Uma transação distribuída entre decisões, vínculos institucionais, transcrições e
auditorias não faz parte do MVP: esses vínculos são conferidos durante a operação.
Histórico de edições de rascunho e registro separado do ator da liberação também
ficam para a evolução da governança.

## Arquivos desta entrega

Novos:

- `app/confia_lean_auditor/teacher_decisions/__init__.py`
- `app/confia_lean_auditor/teacher_decisions/models.py`
- `app/confia_lean_auditor/teacher_decisions/store.py`
- `app/confia_lean_auditor/teacher_decisions/service.py`
- `app/confia_lean_auditor/teacher_decisions/router.py`
- `app/confia_lean_auditor/static/submissions/decisions.js`
- `tests/test_teacher_decisions.py`
- `tests/js/test_teacher_decisions.cjs`
- `docs/P2_DEC_01.md`

Integrações e ajustes:

- `.gitignore`
- `app/confia_lean_auditor/main.py`
- `app/confia_lean_auditor/assessments/models.py`
- `app/confia_lean_auditor/assessments/router.py`
- `app/confia_lean_auditor/management/router.py`
- `app/confia_lean_auditor/static/index.html`
- `app/confia_lean_auditor/static/assessments.js`
- `app/confia_lean_auditor/static/management.js`
- `app/confia_lean_auditor/static/resolution-workspace.js`
- `app/confia_lean_auditor/static/submissions/teacher.js`
- `app/confia_lean_auditor/static/submissions/teacher.css`
- `tests/conftest.py`
- `tests/test_ui_03_teacher_workflow.py`
- `tests/js/ui-dom.cjs`
- `tests/js/teacher-dom.cjs`
- `tests/js/test_assessments_ui.cjs`
- `tests/js/test_core_institutional_management.cjs`
- `tests/js/test_student_tutor_exams.cjs`
- `tests/js/test_submission_audits.cjs`
- `tests/js/test_ui_01_shell.cjs`
- `tests/js/test_ui_03_teacher_workflow.cjs`
