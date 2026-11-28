# Correção direta docente — demonstração de 10/12/2026

Branch local: `codex/teacher-direct-dec10`. Base exata do PR #11: `f16314e440ce43587843105cae6ee64f943c8de6`. Não houve push, merge, alteração da main, dos PRs #7–#10 ou de tags. Nenhuma chamada paga foi executada.

## Diagnóstico e serviços reutilizados

O PR #11 já tinha correção DYNAMIC avulsa por problema, rubricas versionadas com aprovação docente, armazenamento de transcrições, auditorias, Reviewer, Reconciliation e decisão humana. A interface principal, porém, encaminhava DYNAMIC para avaliações/listas e SPECIALIZED para o recebimento de provas inteiras. A entrada avulsa SPECIALIZED oferecia scan/caderno digital, sem texto. A aceitação técnica de transcrição avulsa podia ser criada automaticamente ao solicitar a auditoria.

A adaptação promove dois acessos: **Corrigir com SPECIALIZED** e **Corrigir com DYNAMIC**. O primeiro seleciona os problemas existentes no catálogo ITA/TME². O segundo abre diretamente o editor existente de problema/rubrica. Ambos recebem a solução que o professor já possui, sem avaliação publicada, turma, matrícula ou login de aluno.

Serviços preservados: catálogo; CaseStore; SubmissionStore; revisões/aceites imutáveis; AuditService e seu roteamento; auditor especializado; grounding; certificados Lean; Semantic B; rubricas/PautaEngine; preparação DYNAMIC; Grader; Reviewer; Reconciliation; adjudicação docente; relatórios e histórico. Não foi criado corretor paralelo nem alterada regra matemática, pauta, peso ou crédito.

## Alterações e contratos

- Novo `POST /tme/direct-solutions`: recebe problema, código pseudônimo, texto e original opcional. A autorização docente e a resolução da configuração DYNAMIC continuam no servidor.
- A fonte textual existente passa a atender também problemas SPECIALIZED do catálogo. O snapshot acrescenta campos opcionais `teacher_confirmation_required` e `original`; registros antigos continuam legíveis, com confirmação adicional desativada por padrão.
- Os originais são validados pelo decodificador de documentos existente, preservados em bytes e vinculados por SHA-256 ao snapshot. O acesso exige propriedade da correção; adulteração impede leitura/auditoria.
- A nova entrada requer aceite explícito da revisão atual antes da auditoria. O registro usa a nota de confirmação comum à interface e ao serviço; não altera o contrato `reviewer_identity_verified=False`, que não representa o login da sessão. O login permanece real e verificado pelo servidor.
- Revisar o texto cria nova versão; não reaproveita o aceite da versão anterior. Não há divulgação automática.
- O percurso DYNAMIC encadeia o Grader existente com Reviewer e Reconciliation e recupera o estado persistido. Falha no encadeamento preserva o Grader e informa a pendência, sem convertê-la em erro matemático.
- Entradas antigas de avaliação completa, scan e caderno digital permanecem em “Outras entradas existentes”. Módulos de Aluno e Gestão não foram ampliados.

Arquivos principais: `static/teacher-direct.js`, `static/teacher-presentation.js`, `static/dynamic.js`, `static/tme/tme.js`, HTMLs de entrada, `tme/direct_router.py`, `tme/router.py`, `tme/store.py`, `submissions/text_source.py`, `submissions/store.py`, `submission_audits/service.py`. Testes novos em `tests/test_teacher_direct.py` e `tests/js/test_teacher_direct.cjs`; testes de navegação anteriores foram adaptados aos novos acessos, preservando as verificações existentes. Sem conflitos de integração.

## Evidências de validação

Ambiente: Python 3.9.6 no venv existente; Node 24.15.0; Lean 4.28.0; checkout e armazenamento isolados. Cache formal copiado para este worktree e `lake build` concluído antes dos testes dependentes de Lean. Processos de teste recebem somente variáveis básicas de ambiente; credenciais externas são removidas e os três providers LLM permanecem desligados.

A nova integração autenticada usa um professor sem turma ou atribuição institucional. Não simula autenticação, Grader, Reviewer, Reconciliation, auditor especializado ou Lean. Os dados matemáticos são sintéticos; o caso SPECIALIZED usa a fixture completa de referência, não gold independente.

- SPECIALIZED: TME² P1, texto com itens identificados, aceite explícito, motor real, relatório **20/20**, duas verificações Lean compiladas (`731-137=594`, `3*10=30`), persistência e nova sessão. O escopo formal dessas duas checagens não equivale à formalização integral da solução.
- DYNAMIC: problema fora do catálogo, bloqueio sem rubrica aprovada, rubrica manual, aprovação explícita, texto, confirmação, Grader, Reviewer, Reconciliation e recuperação em nova sessão. Com provider desligado, sugestão e nota reconciliada indeterminadas, revisão necessária e nenhuma decisão humana automática. Uma adjudicação humana explícita por critério foi testada depois: 10/10, mantendo a sugestão automática indeterminada, as pendências e a reconciliação original. Não é uma avaliação semântica real nem um parecer simulado apresentado como real.
- Originais: PNG, JPG e PDF preservados; original inválido recusado; acesso por outro professor/aluno impedido; aceite técnico não autoriza a nova entrada; alteração de arquivo detectada.
- Python: **316 testes distintos aprovados**: 132 de entrada/auditoria/autenticação/DYNAMIC, 162 de auditoria TME/revisão/reconciliação/adjudicação/captura, 22 dos contextos DYNAMIC institucional e autoestudo. Os seis novos testes integrados foram repetidos após os ajustes, todos aprovados. As regressões herdadas incluem fixtures e providers simulados identificados nos próprios testes; isso não é inferência LLM real. A suíte completa de 3.755 testes do PR #11 não foi reexecutada nesta adaptação.
- JavaScript: **634 testes aprovados**, incluindo os controles de entrada, confirmação, ausência de publicação/auditoria automática, preservação de texto após erro e regressões das interfaces anteriores. São testes de componentes/DOM sintético, não validação visual.
- Lean: **build aprovado — 8.038 jobs**.

Os logs detalhados ficam em `artifacts/direct-validation/` (ignorados pelo Git). As primeiras verificações encontraram um nome de artefato incompatível com o contrato existente e pressupostos incorretos no novo teste (posição dos certificados e máximo de 20 pontos). A implementação passou a usar `original_1.bin`, e o teste foi corrigido para conferir os campos reais e a pauta de 20 pontos. O motor e a pauta não foram alterados.

### Limite da verificação visual

O host de automação retornou `The browser access host is unavailable`; o acesso nativo ao Chrome expirou. Portanto **não há aprovação visual, de navegação por teclado ou de console de navegador**. O preflight e a consulta HTTP ao servidor ativo em localhost foram executados com autenticação real e providers desligados. A revisão visual abaixo precisa ser realizada antes da apresentação.

## OCR e limites operacionais

PDF/JPG/PNG/WebP são anexos originais, não correções matemáticas automáticas. O backend existente valida o formato e prepara sua visualização; este percurso não chama OCR nem extrai matemática do arquivo. O professor digita e confirma a transcrição. A integração futura de captura/OCR do Luis e os contratos anteriores foram preservados.

DYNAMIC com provider desligado demonstra o percurso e a abstenção correta; não demonstra qualidade de julgamento semântico por LLM. Antes de habilitá-lo, é necessária autorização específica de modelo, custo e número de chamadas. Não há nova validação científica dos 16 temas nem do gold independente nesta mudança de interface. As limitações científicas registradas no PR #11 permanecem.

Texto ainda não enviado deve ser salvo pelo botão de entrada antes de recarregar. Depois do recebimento, original, transcrição, versões, confirmação e auditorias ficam no armazenamento local. Os dados do servidor de demonstração não devem ser publicados nem usados como dados institucionais reais.

## Iniciar e demonstrar

No worktree `/private/tmp/confia-teacher-direct-dec10`:

```sh
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python scripts/run_teacher_direct_demo.py --check
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python scripts/run_teacher_direct_demo.py
```

Abra `http://127.0.0.1:8888/`. O script informa o login `professor.direto` e uma senha local gerada, guardada somente no runtime ignorado. Preserva os dados entre reinícios. Remove credenciais herdadas, desabilita providers e escuta apenas em localhost.

1. Faça login. Confira as duas opções de correção e abra **Corrigir com SPECIALIZED**.
2. Selecione **TME² 2026 — Problema 1**. Use código `DEMO-SPECIALIZED-01`. Cole o conteúdo de [teacher-direct-tme-p1.txt](teacher-direct-tme-p1.txt), uma solução sintética completa. Opcionalmente anexe um original sintético.
3. Clique **Conferir transcrição**. Compare Original/Transcrição; marque a conferência e clique **Confirmar transcrição**. Antes disso, a análise deve estar desabilitada.
4. Execute **Analisar com ConfIA**. Mostre 20/20, itens da pauta, evidências e as duas verificações Lean efetivamente compiladas. Recarregue e retome o mesmo caso.
5. Volte a **Corrigir com DYNAMIC**. Crie o problema `Resolva nos reais: 2y² - 14y + 24 = 0. Justifique.` com máximo 10. Cadastre rubrica manual: método 4, raízes 3, verificação 3. Salve e aprove explicitamente; confira os avisos de preparação.
6. Use código `DEMO-DYNAMIC-01` e texto: `y²-7y+12=0; (y-3)(y-4)=0; S={3,4}; 2*3^2-14*3+24=0; 2*4^2-14*4+24=0`. Receba, confirme a transcrição e execute a análise.
7. Mostre Grader, Reviewer e Reconciliation. Explique a nota indeterminada e as pendências do provider desligado; não anuncie correção semântica real. Se demonstrar adjudicação, registre justificativa por critério e identifique a nota como **decisão humana**, nunca como resultado automático do motor.
8. Recarregue, consulte histórico/versões e confirme que nada foi divulgado ao aluno. Teste Tab/Shift+Tab, retorno à página inicial, abas Original/Transcrição/Comparar e console do navegador.

Comandos de regressão executados (Python com `PYTHONPATH=app:tests`, raiz apontando para este worktree e ambiente sem credenciais):

```sh
python -m pytest -q tests/test_teacher_direct.py tests/test_submissions.py tests/test_submission_audits.py tests/test_tme_pilot.py tests/test_dynamic_dy3.py tests/test_dynamic_teacher_simplified.py tests/test_core_auth.py
python -m pytest -q tests/test_tme_accepted_integration.py tests/test_dynamic_dy4.py tests/test_dynamic_dy5.py tests/test_dynamic_human_adjudication.py tests/test_tme_full_exam.py
python -m pytest -q tests/test_dynamic_school.py tests/test_dynamic_self_study.py
node --test tests/js/*.cjs
lake build
git diff --check
```

O percurso direto está implementado para os dois motores. A liberação para apresentação depende da revisão visual e, se a demonstração exigir julgamento semântico automático do DYNAMIC, de um smoke com LLM real especificamente autorizado.
