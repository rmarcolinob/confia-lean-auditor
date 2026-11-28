# Fase 4 — fluxo institucional e Gestão (27/11/2026)

Base: `923bf3acbd9994af9662bcdff6b18eac1b6d4df9`. Branch: `codex/stabilize-platform-pre10dez`. Diagnóstico histórico: [PR #6](https://github.com/rmarcolinob/confia-lean-auditor/pull/6), preservado. Nenhuma alteração estética, regra matemática, permissão ou contrato público.

**APROVADO COM LIMITAÇÕES na validação local.** O percurso institucional digitado foi executado com serviços, autenticação e persistência reais, dados sintéticos e providers desligados. A decisão final foi uma adjudicação humana explícita, não uma nota produzida por um LLM simulado. A disponibilidade e a qualidade do corretor semântico real continuam pendentes de autorização e execução posterior.

## Defeitos e correções

1. A Gestão consultava somente `teacher_decisions`. Confirmações TME/DYNAMIC, armazenadas em `tme.human_decisions` e divulgadas pelo vínculo da finalização escolar, não eram contadas. Dois testes novos falharam na base: três questões confirmadas eram contadas como zero. A projeção de leitura `management/question_decisions.py::decision_state` usa `human_decisions.project`, `finalization.lifecycle` e a divulgação atual; não cria decisões, não recalcula notas nem reescreve registros. A filtragem institucional ocorre antes dessa leitura. O caminho legado continua funcionando; cada submissão é contada uma vez.
2. `static/app.js` carregava `/problems` antes de conhecer o perfil. Gestão recebia 403 e erro de console, corretamente recusada pela API. Agora o catálogo inicia depois de `/auth/me` para Professor/Aluno e não inicia para Gestão. O modo local sem autenticação conserva o carregamento anterior. Não se concedeu permissão adicional à Gestão.
3. A leitura existente da divulgação foi extraída, sem mudança de regra, para `dynamic/school_service.py::current_release`. Somente uma divulgação íntegra, vinculada ao ID e hash da finalização atual, conta como publicada. Reabertura revoga essa contagem. Integridade inválida deixa os indicadores indisponíveis (`null`), em vez de publicar zero enganoso.

`override_count` conta alteração numérica em relação à sugestão conhecida. Uma adjudicação necessária por ausência de sugestão não é contabilizada como alteração numérica. `decisions_finalized_count` conta confirmações por questão, não número de provas. Provas locais sem vínculo institucional não são incluídas artificialmente nas estatísticas escolares. Registros TME avulsos sem `exam_submission_id` conservam o caminho legado.

## Percurso real local, sem inferência paga

[Evidência HTTP](evidence/platform/institutional-flow.json) e [retomada em processos novos](evidence/platform/resume.json).

- Professor cadastrou uma equação inédita e rubrica manual com desenvolvimento (6) e resultado (4). Tentativa antes da aprovação: 409. Rubrica aprovada, atividade ativada, versão publicada para a turma.
- Aluno enviou texto; o Grader determinístico reconheceu passos, mas a reconciliação permaneceu tecnicamente pendente sem Reviewer semântico disponível. O workspace não apresentou subtotal como nota final.
- Professor adjudicou os dois critérios, com justificativas, confirmou 10/10 e finalizou. **Esse valor é entrada humana sintética do teste**, não gold independente nem evidência de inferência automática correta.
- Resultado oculto antes da divulgação explícita. Aluno não pode divulgar (403). Depois da divulgação, consultou 10/10 e a devolutiva docente.
- Outro estudante: 404; professor de outra escola: 403; aluno no workspace docente: 403; anônimo: 401; gestor em outra escola: 403. Artefatos anteriores preservados byte a byte; repetição idempotente não criou outra tentativa.
- Gestão: uma submissão, uma decisão confirmada, um resultado divulgado. Antes da correção, o mesmo tipo de fluxo registrava zero decisões e zero divulgações.
- Dois processos Python independentes retomaram uma auditoria digitada. Retry devolveu o mesmo registro; nova leitura criou nova revisão/auditoria e invalidou a anterior, sem modificar seus bytes. A nova resolução incorreta ficou pendente; não se converteu falha/insuficiência em zero.

## Navegador

Aplicação ASGI separada, `127.0.0.1:8876`, contas exclusivamente sintéticas e diretórios temporários ignorados pelo Git. Login por Enter levou diretamente a Professor, Aluno e Gestão. Menu de início funcionou nos três; teclado Enter testado também no menu, retorno e atividades. Recarregar a Gestão preservou a sessão. Marca do Aluno/Gestão permaneceu texto, sem navegação. A interface aprovada do Professor não foi redesenhada.

Foram abertos a atividade DYNAMIC, os originais textuais, a análise por critério, a decisão humana separada, a consulta do aluno e os indicadores. Console da Gestão sem erros. As regressões JavaScript verificam explicitamente zero chamadas de catálogo na Gestão e uma chamada após autenticação nos demais perfis.

| Registro visual sintético | Observação |
|---|---|
| [Workspace docente](evidence/platform/teacher-decision.jpg) | Sugestão não determinada e nota humana fundamentada são mostradas separadamente |
| [Resultado divulgado ao aluno](evidence/platform/student-release.jpg) | Nota e feedback somente depois da autorização docente |
| [Gestão](evidence/platform/management-current.jpg) | Confirmação e divulgação agora contadas |
| [Estudo autônomo](evidence/platform/study-provider-unavailable.jpg) | Enunciado preservado, leitura confirmada e preparação indisponível; nenhuma nota |

TutorIA abriu normalmente e identificou conteúdos, feedback ilustrativo, trilhas, progresso e recomendações demonstrativas. Isso não prova tutoria adaptativa real. No estudo autônomo, o aluno registrou um problema de função afim e confirmou a leitura; preparação sem provider terminou em falha explícita, sem critérios fictícios ou pontuação. A mensagem genérica de ambiguidade junto da falha técnica é uma limitação de apresentação, não evidência de ambiguidade matemática nesse enunciado.

## Regressões e reprodução

Python validado do projeto (3.9.6), Node 24.15.0. Executar na raiz deste worktree com `PYTHONPATH=app:tests`:

```sh
python -m pytest -q tests/test_management_dynamic_decisions.py tests/test_core_institutional.py tests/test_dynamic_school.py tests/test_teacher_decisions.py
python -m pytest -q tests/test_core_auth.py tests/test_tutoria_demo.py tests/test_tutoria_chat_demo.py tests/test_dynamic_self_study.py tests/test_dynamic_self_study_feedback_policy.py tests/test_tme_finalization.py
node --test tests/js/*.cjs
git diff --check
```

Primeira bateria: **73 aprovados**, 217,99 s. Segunda bateria (autenticação, TutorIA, estudo autônomo, feedback e finalização): **67 aprovados**, 108,00 s. Total dirigido Python: **140 aprovados**. JavaScript completo: **631 aprovados**. Testes novos cobrem confirmações/divulgações, reabertura, integridade, escopo institucional e decisões TME com alteração numérica; o provider das fixtures de integração é explicitamente simulado. O percurso HTTP descrito acima é distinto: provider desligado e adjudicação humana explícita.

## Limitações e impacto

- Sem teste de carga; a agregação lê históricos e verificações de integridade e pode ficar custosa com muitos registros. Não foi criado cache de resultados possivelmente obsoletos.
- `completed_audits`/`inconclusive_audits` continuam refletindo o AuditRun do Grader, não a reconciliação posterior. Não devem ser interpretados como taxas de acerto ou de notas escolares concluídas. Não se mudou silenciosamente esse contrato.
- A home do Professor conserva indicadores de seu fluxo original; as atividades DYNAMIC estão na área DYNAMIC. Não se criou uma nova agregação global docente nesta correção.
- Sem OCR, chamadas pagas, dados reais de estudantes ou avaliação humana independente. Captura e transcrição existentes foram preservadas; aperfeiçoamento de OCR permanece com Luis.
- A validação funcional offline não autoriza correção escolar autônoma. Os 21 casos históricos ainda sem validação independente permanecem pendentes. Main, políticas, rubricas, PautaEngine, checkers, Lean e tag científica preservados; nenhuma integração automática.
