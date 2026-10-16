# Áreas do aluno: TutorIA e Exames

O shell usa a sessão (`/auth/me`) para mostrar o nome do aluno e a matrícula ativa (`/institutional/me/context`) para mostrar escola e turma. A navegação principal do aluno é Início, TutorIA, Exames e Minhas submissões.

O workspace compartilha um único iframe `/capture`. O estado central `TUTOR` usa o modo de captura `practice`; `EXAM` usa `submission`. No TutorIA, a escrita pode ser reconhecida por `/submissions/recognition-preview` sobre uma cópia congelada **somente em memória**. A prévia é transitória; ao pedir feedback, o aluno envia o texto reconhecido ao mecanismo de prática `/audit`. Esse fluxo não cria Submission, RecognitionRun oficial, TranscriptionRevision ou AuditRun institucional. Uma nova tentativa cria outro rascunho local.

Em Exames, o aluno escolhe uma atividade explicitamente disponível para sua turma. O mesmo caderno usa o pipeline existente: preparar versão, reconhecer para conferir, enviar Submission e iniciar reconhecimento oficial. Minhas submissões consulta `/submissions` da própria sessão; tentativas de TutorIA não entram nessa lista.

## Disponibilidade temporária de exames

Até existir uma entidade Assessment, `GET /institutional/me/exams` lê o arquivo opcional `exams.json` no diretório configurado por `CONFIA_INSTITUTIONAL_DIR` (por padrão, `runtime/institutional`). Sem esse arquivo, a lista é vazia. Um exemplo de atividade é:

```json
[
  {
    "exam_id": "atividade-2026-01",
    "title": "Atividade de matemática",
    "school_id": "ceti-centro",
    "classroom_id": "turma-3a",
    "academic_year": 2026,
    "problem_ids": ["ITA2025Q1"],
    "active": true
  }
]
```

O servidor filtra pelo `Enrollment` ativo do estudante e pelo catálogo de questões. O arquivo é a fronteira de integração futura com Assessment, sem endpoint público de publicação nesta fase. O endpoint atual de Submission ainda não grava `exam_id`; a associação formal entre envio e Assessment deve ser adicionada quando esse contrato existir.
