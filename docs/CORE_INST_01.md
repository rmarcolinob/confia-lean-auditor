# CORE-INST-01 — hierarquia institucional do ConfIA

## Modelo e persistência

O AuthUser identifica a pessoa e seu papel. O módulo `institutional` define onde ela atua: `Network → School → Classroom`, com `TeacherAssignment` e `Enrollment` ativos por ano letivo. `ManagerAssignment` associa gestores à escola ou à rede. Esses contratos usam Pydantic 2 com `extra="forbid"` e validam as referências entre escola, turma e ano. A UI recebe contexto pela API; nenhum vínculo institucional é inferido de seletores do navegador.

`InstitutionalStore` mantém coleções JSON locais em `runtime/institutional/`: `networks.json`, `schools.json`, `classrooms.json`, `teacher_assignments.json`, `enrollments.json` e `manager_assignments.json`. O diretório é ignorado pelo Git. Há lock local e substituição atômica por arquivo com modo `0600`. O seed preserva registros existentes e só acrescenta identidades ausentes. Este store é a fronteira a substituir por um repositório PostgreSQL no futuro; os routers e a UI não leem os arquivos diretamente. Uma instalação com múltiplas instâncias precisa de banco compartilhado e transações para atualizar várias coleções em conjunto.

## Demo

Na raiz do repositório:

```sh
.venv/bin/python scripts/create_demo_users.py
.venv/bin/python scripts/create_demo_institutional_data.py
```

O primeiro script cria contas locais `aluno.demo`, `professor.demo`, `gestao.demo` e `rede.demo`, solicitando senha sem eco. Contas existentes não são alteradas. O segundo cria a Rede Estadual Demo, CETI Centro (1ª e 2ª séries A) e CETI Norte (3ª série A), no ano corrente. Vincula aluno à 2ª série A do Centro, professor às duas turmas do Centro, gestor escolar ao Centro e, quando a conta `rede.demo` existe, gestor de rede à rede. Rodar o seed novamente não duplica vínculos. Não há senhas nem dados institucionais demo embutidos no frontend.

## Endpoints e autorização

| Leitura | Escopo |
| --- | --- |
| `GET /institutional/me/context`, `/institutional/me/schools` | Contexto da sessão: matrícula própria, turmas atribuídas, escola gerida ou rede gerida |
| `GET /institutional/schools/{school_id}/classrooms` | Apenas turmas autorizadas na escola |
| `GET /institutional/classrooms/{classroom_id}/students` | TEACHER com atribuição ativa na turma; nomes públicos dos alunos matriculados |
| `GET /submissions?school_id=…&classroom_id=…` | TEACHER: somente turma atribuída; filtros fora do escopo retornam 403 |
| `GET /management/network/overview` | NETWORK_MANAGER da rede |
| `GET /management/schools`, `/management/schools/{school_id}/overview`, `/management/schools/{school_id}/classrooms`, `/management/classrooms/{classroom_id}/overview` | SCHOOL_MANAGER da própria escola ou NETWORK_MANAGER da rede |

Sem sessão, os endpoints protegidos retornam 401. Papel inadequado ou objeto fora do vínculo retorna 403. ADMIN fica fora desta UI. O professor precisa de `TeacherAssignment` ativo para abrir Submission, transcrição, aceite e Audit Bridge; compartilhar `tenant_id` não basta. O aluno só lê suas Submissions e não passa escola ou turma no POST. O servidor deriva `network_id`, `school_id`, `classroom_id` e `submitted_by_user_id` da sessão e de uma única `Enrollment` ativa do ano corrente. Matrícula ausente ou ambígua impede um novo envio. O snapshot, o reconhecimento oficial e o aceite mantêm seus contratos anteriores.

Submissions anteriores não são migradas nem reatribuídas. Seus campos institucionais ausentes permanecem `null`. A leitura docente de registros legados só é possível na configuração local de desenvolvimento `CONFIA_AUTH_LEGACY_READ=1`; a opção é ignorada em produção. O aluno não recebe acesso a esses registros por essa opção.

## Fluxos de tela

O shell usa `/auth/me` para mostrar apenas o módulo do papel autenticado. O aluno vê, sem seletor, a escola e a turma de sua matrícula. O professor escolhe escola, turma e vê o ano corrente. Uma escola ou uma turma única é selecionada automaticamente. A troca de escola apaga a turma, a fila e o detalhe anteriores antes de consultar o servidor; a troca de turma também apaga a fila e o detalhe. Respostas antigas de consultas são ignoradas. As áreas Alunos, Soluções recebidas, Transcrições e Análises mantêm o corretor existente: manuscrito original ao lado da transcrição, aceite de fidelidade e só depois Análise ConfIA.

No caderno embedded, o documento pai exibe o enunciado sticky e logo abaixo a toolbar sticky de caneta, mouse de teste, escrita, borracha, desfazer/refazer e páginas. `ResizeObserver` atualiza a variável CSS do deslocamento quando o enunciado muda de altura. O iframe `/capture` continua proprietário dos traços, do modo, do histórico e das páginas. A toolbar pai envia comandos pela ponte `postMessage` já existente, validada por origem, documento, questão e modo. A toolbar própria continua no `/capture` standalone. Prévia Mathpix, envio, reconhecimento oficial e revisão `NEEDS_REVIEW` não mudam.

Gestão de rede começa nos indicadores da rede e navega por escola e turma. Gestão escolar começa em sua escola. As telas mostram apenas agregados. Não há manuscrito nem transcrição individual nesses endpoints.

## Métricas e privacidade

As métricas contam escolas e turmas ativas do ano corrente, usuários distintos em matrículas e atribuições ativas, Submissions com escopo institucional persistido, revisões de transcrição, RecognitionRuns e AuditRuns existentes. `recognition_success_count` conta runs `NEEDS_REVIEW`; `recognition_failure_count` conta `FAILED`. `completed_audits` conta `COMPLETED`; `inconclusive_audits` conta análises concluídas sem score sugerido. Coleção disponível e vazia retorna `0`; falha de leitura do store correspondente retorna `null` nas contagens opcionais. Nenhum número ilustrativo é apresentado como indicador real.

O score do Audit é apenas `confia_suggested_score`, uma sugestão do ConfIA. `teacher_final_score` não é produzido nesta fase; não existe nota oficial da gestão. As respostas agregadas expõem metadados institucionais, ano e contagens. Não incluem PNG, snapshot, `solution_text`, `transcription_text`, segmentos, nomes individuais nem detalhes do AuditRun.

## Evolução

Uma migração para PostgreSQL deve preservar os IDs, validar unicidade e chaves estrangeiras, oferecer transações para vínculos e leituras consistentes, e manter a autorização por objeto no backend. A futura integração com cadastro SEDUC poderá importar redes, escolas, turmas e matrículas para esse store/repositório, com reconciliação explícita de IDs e desativações. CORE-INST-01 não integra SEDUC, diário, boletim, TeacherDecision, OAuth ou gov.br.
