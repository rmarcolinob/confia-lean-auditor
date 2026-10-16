# P2-ASSMT-01 — Exames institucionais

O Assessment é persistido em `runtime/assessments/` (ou `CONFIA_ASSESSMENTS_DIR`) em documentos JSON validados pelo Pydantic 2. A escrita usa lock de processo, arquivo temporário, `fsync` e substituição atômica. O modelo separa Assessment, AssessmentItem e Submission. Cada item referencia apenas um `problem_id` do catálogo atual.

## Contrato e integridade

`POST /assessments` cria DRAFT para uma turma com TeacherAssignment ativo. `POST /assessments/{id}/items` adiciona questões do catálogo. `PATCH` e `DELETE` permitem ajustes apenas no rascunho. `POST /assessments/{id}/publish` valida o vínculo, a turma, as questões e os pontos, calcula `definition_sha256` canônico e congela a definição. `POST /assessments/{id}/close` encerra o exame. `GET /assessments` e `GET /assessments/{id}` são filtrados por TeacherAssignment ou Enrollment. `GET /assessments/{id}/progress` mostra os alunos e as Submissions por item ao professor.

Para o aluno, DRAFT é invisível. A disponibilidade é derivada de `opens_at` e `closes_at` em UTC: AGENDADO, DISPONÍVEL ou ENCERRADO. Envio fora da janela é bloqueado. O endpoint `POST /assessments/{id}/items/{item_id}/submissions` deriva Assessment, item, problema, escola, turma e aluno da sessão e do store institucional. O corpo contém somente a versão congelada e seus PNGs, conforme o contrato existente de Submission. O registro guarda `assessment_id`, `assessment_item_id` e o hash da definição. A trava de Submission impede mais de uma entrega oficial por aluno e item; repetir a mesma versão devolve o recibo original. Submissions legadas permanecem legíveis e sem vínculo retroativo.

O workspace EXAM reutiliza o caderno `/capture`, a prévia Mathpix transitória, o envio oficial e o reconhecimento oficial `NEEDS_REVIEW`. O professor abre uma entrega na tela já existente de manuscrito, transcrição, aceite e Análise ConfIA. TutorIA continua em `practice` e não cria Assessment nem Submission institucional.

## Seed de demonstração

Execute `python scripts/create_demo_assessments.py` após criar usuários e dados institucionais demo. O script confirma a existência dos quatro problemas no catálogo antes de gravar, encontra `professor.demo`, CETI Centro, 2ª série A e o TeacherAssignment ativo e publica:

| Avaliação | Questões | Pontos |
| --- | --- | --- |
| Avaliação 1 | ITA2025F2Q1, ITA2025F2Q3 | 5 + 5 |
| Avaliação 2 | ITA2025F2Q5, ITA2025F2Q8 | 5 + 5 |

Os IDs são estáveis para a turma e ano. A primeira execução abre cinco minutos antes e encerra sete dias depois. Execuções posteriores preservam as datas. Se encontrar exatamente os dois registros demo publicados com os títulos antigos, o seed troca somente o título e recalcula o hash da definição do Assessment; os hashes históricos das Submissions permanecem intactos. Outros registros ou divergências no seed causam erro. ITA2025F2Q6 ficou fora por dívida técnica conhecida em `maximizers_identification`, não por indisponibilidade do problema.

O manifesto opcional `runtime/institutional/exams.json` e `GET /institutional/me/exams` pertencem à etapa anterior e não alimentam mais a UI de Exames.

## Limites desta etapa

Pontos dos itens são institucionais e não viram nota oficial. Não há reenvio, edição de exame publicado, TeacherDecision, boletim, cron ou armazenamento PostgreSQL.
