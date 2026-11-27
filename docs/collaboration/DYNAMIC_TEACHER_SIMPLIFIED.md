# DYNAMIC docente simplificado

Implementação de 27/11/2026, preparada em `codex/dynamic-teacher-simplified` a partir da `main` `97c84bb432dd751878d532adeab35bb4e57a24dc`. Destinada a revisão por PR; integração técnica não equivale à validação científica para correção escolar autônoma.

## Percurso do professor

Abra **Professor → DYNAMIC** (`/tme?view=new&mode=dynamic`). As três ações usam os serviços persistentes existentes:

1. **Cadastrar avaliação:** título, prova/lista, orientações, questões e pontos. Cada questão abre o editor existente de rubrica, incluindo níveis parciais e dependências. A sugestão por IA encadeia a preparação e a sugestão; não aprova os critérios. É possível editar ou substituir a sugestão. A aprovação explícita continua obrigatória, incluindo ciência dos avisos. A avaliação só é ativada quando o backend atesta todas as questões prontas.
2. **Enviar provas respondidas:** selecione uma avaliação aprovada, informe um código pseudônimo e envie um PDF ou fotografias de **um participante por vez**. Associe manualmente as páginas: uma resposta pode ocupar várias páginas e uma página pode pertencer a várias questões. Confira e, se necessário, recorte o texto transcrito para conter somente a resposta da questão. A leitura automática e a vinculação técnica não substituem a confirmação explícita do professor. Ambiguidade não resolvida bloqueia a análise.
3. **Consultar correções:** provas realmente recebidas, situação, originais, transcrições, critérios, justificativas e evidências. A análise inicia o Grader e encadeia a revisão independente e a reconciliação. A retomada reutiliza registros atuais e a chave idempotente da revisão; não homologa nem divulga resultados. Discordâncias e falhas continuam pendentes. A confirmação/adjudicação e o fechamento usam os controles e contratos docentes existentes.

**Auditoria e evidências** reúne os pareceres e detalhes técnicos. A publicação institucional e a liberação de resultados continuam explícitas e separadas, sob **Publicação e próximas versões**. Atividades já institucionais continuam recebendo respostas pelo módulo do aluno, com as políticas existentes.

## Alterações e contratos

| Arquivos | Responsabilidade |
| --- | --- |
| `static/dynamic-assessment.js`, `static/dynamic.css` | Três ações, retomada de avaliações, disponibilidade e lista real de provas; preservação do formulário quando um salvamento falha. |
| `static/dynamic.js` | Opção de apresentação simplificada do editor existente; preparação antes da sugestão, sem aprovação implícita. |
| `static/dynamic-correction.js` | Encadeamento de APIs de Reviewer/Reconciliation com retomada idempotente; nenhuma decisão matemática. |
| `static/tme/{tme.js,full-exam.js,workspace-report.js,index.html}` | Navegação, associação à avaliação, relatório e carregamento dos componentes. |
| `dynamic/router.py` | Novo GET autenticado `/dynamic/capabilities`, somente presença de configuração, sem sondar providers ou retornar segredos; `no-store`. |
| `tests/test_dynamic_teacher_simplified.py`, `tests/js/test_dynamic_teacher_simplified.cjs`, `tests/js/test_dynamic_dy2.cjs` | Autorização, fluxo real com mocks, indisponibilidade, aprovação, encadeamento e retomada, preservação de entrada após erro. |
| `scripts/testing/teacher_simple_preview.py` | Ambiente de aceitação isolado: sessões, armazenamento e pipeline reais; imagens, OCR e pareceres sintéticos. |

Os caminhos na tabela são relativos a `app/confia_lean_auditor/`, exceto testes e scripts. Não há mudança de schema persistido, PautaEngine, Grader, Reviewer, Reconciliation, política semântica, checker, rubrica preparada, Lean ou autenticação. O editor legado e os links diretos continuam disponíveis. A tag `SPECIALIZED-TME2-RC1` permanece no objeto anotado `0c64e318a26e21f71fe3097c66ee17a5206dd8a3`, apontando para `c03403fe5b83d9db9df172882bd69af3dfa2d027`.

## Executar no Mac

Em um clone de desenvolvimento próprio, sem alterações locais pendentes:

```sh
git fetch origin
git switch --track origin/codex/dynamic-teacher-simplified
python3 -m venv .venv
.venv/bin/python -m pip install -e . -c docs/audits/assets/dynamic-rc1/python-constraints.txt
```

Para contas e armazenamento locais normais, siga [DYNAMIC com sessão autenticada](README.md#dynamic-com-sessão-autenticada). O acesso do professor é `/tme?view=new&mode=dynamic`. Configurar providers reais é uma etapa operacional separada, com orçamento e autorização próprios. Sem inferência configurada, cadastro, rubricas manuais, originais e transcrição manual continuam disponíveis; critérios sem decisão suficiente permanecem pendentes.

Para **reproduzir somente o teste sintético**:

```sh
PYTHONPATH=app .venv/bin/python scripts/testing/teacher_simple_preview.py --port 8771
```

Abra `http://127.0.0.1:8771/`. Contas sintéticas: `teacher.a`, `student.a`, `manager.a`; senha pública de fixture: `example-secret-for-tests`. Essas contas existem apenas no armazenamento temporário criado pelo script, nunca devem ser usadas em implantação. O caminho das imagens/PDF sintéticos é impresso ao iniciar. O script remove as credenciais de provider herdadas, substitui os providers por mocks identificados, bloqueia transporte HTTP externo e escuta somente em loopback. Não reutiliza dados institucionais. `Ctrl+C` encerra o servidor; cada inicialização cria um armazenamento temporário novo. Exige as dependências de testes já usadas no repositório.

## Validação realizada

- **700 testes Python aprovados**: DYNAMIC completo selecionado, autenticação, institucional, captura, submissões, workspace TME e interface. Python 3.9.6 do ambiente previamente validado do projeto; `PYTHONPATH=app` garante o código deste worktree.
- **631 testes JavaScript aprovados**, Node 24.15.0, incluindo os novos testes e todos os testes JS existentes.
- **1 teste Lean real aprovado**, isolado: `test_real_local_lean_status_certificates_preserved`. Usou toolchain/cache local já provisionado; não houve reconstrução integral da Mathlib nem alegação de prova Lean no percurso semântico DYNAMIC.
- `git diff --check` aprovado.

Comandos executados, na raiz da branch, substituindo `python` pelo interpretador do ambiente:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app CONFIA_ENABLE_LLM_FORMAL_STEPS=0 \
CONFIA_DYNAMIC_LLM_ENABLED=0 CONFIA_SEMANTIC_LLM_ENABLED=0 python -m pytest -q \
  tests/test_dynamic*.py tests/test_core_auth.py tests/test_core_institutional.py \
  tests/test_tme_full_exam.py tests/test_tme_question_audit.py tests/test_tme_review_workspace.py \
  tests/test_tme_reanalysis.py tests/test_tme_human_confirmation.py tests/test_tme_pilot.py \
  tests/test_recognition*.py tests/test_submissions*.py tests/test_ui*.py
node --test tests/js/*.cjs
PYTHONPATH=app CONFIA_ENABLE_LLM_FORMAL_STEPS=0 CONFIA_DYNAMIC_LLM_ENABLED=0 \
CONFIA_SEMANTIC_LLM_ENABLED=0 python -m pytest -q \
  tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved
git diff --check
```

No navegador, com autenticação real e providers simulados identificados: cadastro de duas questões (frações e equações), rubricas manuais e nível parcial aprovado, duas imagens, primeira página compartilhada, revisão por página, bloqueio de ambiguidade, confirmação explícita, pipeline completo, divergência 1/2 versus 2/2, adjudicação de 1/2, confirmação de 2/2 da outra questão e fechamento humano de 3/4. O subtotal automático permaneceu incompleto, sem ser promovido à nota final. O valor humano decorreu da rubrica sintética e da intervenção, não de regra adicionada ao corretor.

Também foram conferidos: preservação após reload, lista real de recebimentos, teclado (Tab/Enter/Space), largura de 390 px sem overflow horizontal, rejeição de seleção de arquivo não permitido, catálogo SPECIALIZED/entrada digital, atividades e estudo autônomo do aluno, TutorIA e indicadores persistidos da Gestão. Os testes Python existentes cobrem PDF multipágina, integridade, isolamento e invalidação por mudanças da leitura. A geração de sugestão IA foi testada com respostas controladas em JavaScript; no navegador estava indisponível e a rubrica foi manual.

Capturas reais do ambiente sintético:

- [Desktop](../images/dynamic-teacher-simplified/desktop.jpg)
- [Mobile](../images/dynamic-teacher-simplified/mobile.jpg)
- [Páginas e associações](../images/dynamic-teacher-simplified/paginas.jpg)
- [Divergência e adjudicação necessária](../images/dynamic-teacher-simplified/divergencia.jpg)
- [Fechamento humano, separado da sugestão automática](../images/dynamic-teacher-simplified/resumo.jpg)
- [Gestão preservada](../images/dynamic-teacher-simplified/gestao.jpg)

## OCR e limites

Inspecionada `origin/luis_ocr` em `0e446851ae595721ccb5e720400b834db3060c46`, sem merge. `recognition/glm_ocr.py` contém cliente local Ollama/GLM com limites; `uploads/images.py` e `answer_extraction.py` têm utilidades potencialmente aproveitáveis. Uma integração futura deve adaptar reconhecimento ao registry e preservar originais, revisões e confirmação. O endpoint `/uploads/audits`, que reconhece e chama diretamente a auditoria de OCR não conferido, **não foi incorporado**. Não há alegação de integração operacional com GLM nesta entrega.

Limites explícitos:

- Um participante por envio; sem lote com identificação automática. PDF até 50 páginas ou até 50 imagens; limites existentes de 20 MiB por arquivo e 40 MiB no conjunto.
- Identificação e separação textual por questão são manuais e dependem da conferência docente. Não há segmentação visual automática confiável sendo anunciada.
- O indicador de configuração não garante serviço remoto disponível. Falhas podem ocorrer depois de começar; registros anteriores são preservados e a interface permite retomar/revisar.
- Mocks validam integração, não qualidade de OCR, correção matemática independente, custo ou latência de providers reais. Nenhuma chamada paga foi realizada.
- O catálogo `/problems` é restrito a aluno/professor. A Gestão exibe os indicadores autorizados, mas o shell legado ainda tenta carregar esse catálogo e registra um erro de console para esse perfil. Comportamento preexistente, sem ampliar permissões nesta alteração.
- Algumas áreas do TutorIA já são demonstrativas e permanecem identificadas dessa forma. Não foram reconstruídas nem convertidas em funcionalidades de produção.
- Testes e screenshots não modificam auditorias históricas. Não há nova tag científica. O merge deste PR depende de revisão, aprovação posterior e CI satisfatório.
