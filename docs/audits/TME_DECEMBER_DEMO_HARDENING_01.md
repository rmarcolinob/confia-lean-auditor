# TME — hardening e ensaio de dezembro 01

**Resultado: DECEMBER_DEMO_RELEASE_CANDIDATE_READY**

Ensaio realizado em 11/11/2026, no worktree `confia-lean-auditor-tme-december-integration`, branch `feat/tme-december-integration`. A aplicação D1–D7 permaneceu no SHA `ed370faa715c6f4d879f1d023139c1cd47b166a0`. Nenhum código de aplicação, motor, pauta, expectativa preexistente ou layout foi alterado. Não houve commit, tag, push ou release externa.

## Entrega operacional

- `scripts/demo_december.sh` / `.py`: startup local com preflight, storage isolado, assessment sintético idempotente e flags explícitas. Recusa produção, cache ausente/divergente e porta ocupada; não baixa dependências nem faz build.
- `examples/demo_december/`: PDF de quatro páginas, quatro transcrições controladas, gold externo sintético e PDF propositalmente inválido. Não contém PII.
- [Runbook](../DEMO_DECEMBER_RUNBOOK.md) e [checklist imprimível, uma página](../DEMO_DECEMBER_CHECKLIST.pdf).
- Cinco testes novos de operação; evidências em [assets/tme-december-hardening](assets/tme-december-hardening/).

Comando único, a partir do worktree:

```sh
scripts/demo_december.sh start
```

URL: `http://127.0.0.1:8765/tme`. O servidor do ensaio foi encerrado com segurança ao terminar; os dados permanecem em `runtime/demo_december` (ignorado pelo Git).

## Ambiente e segurança

| Item | Verificação |
|---|---|
| Python/venv | `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`, Python 3.9.6; override `CONFIA_DEMO_PYTHON` |
| Imports/assets | FastAPI, Uvicorn, Pydantic, PDFium, Pillow e arquivos TME locais disponíveis; PDF e imagens carregados no navegador |
| PYTHONPATH | Shell fixa caminho absoluto de `app`; independe do diretório inicial do terminal |
| Flags | `CONFIA_AUTH_ENABLED=1`, `CONFIA_TME_DEMO_NO_AUTH=1`, `CONFIA_TME_CERTIFICATION_ENABLED=1`, `CONFIA_TME_QUESTION_USE_LEAN=1` |
| Rede | Bind somente `127.0.0.1:8765`; não exposto externamente |
| Storage | Diretórios locais explícitos para auth, institutional, assessments, participants, exams, cases, submissions e audits; criação do diretório raiz com modo 0700 |
| Credenciais | Nenhuma no percurso manual ensaiado; OCR/API externos não são dependência deste roteiro |
| Produção | Launcher rejeita `CONFIA_ENV=production` antes de criar storage. Lifespan da aplicação também rejeita demo em produção, inclusive caixa alta; suíte existente passou |
| Certificação | Flag de certificação sozinha não remove autenticação: leitura, importação e exports retornaram 401 no teste novo |

O lançamento não configura um banco remoto. Não foram copiadas credenciais. O assessment é criado apenas quando ausente; uma definição existente divergente provoca recusa, sem sobrescrita. `check` verifica ambiente sem criar o assessment.

## Mathlib e Lean preparados

Comandos executados:

```sh
lake env lean --version
git -C .lake/packages/mathlib rev-parse HEAD
lake build ConfiaLeanAuditor
scripts/demo_december.sh check
```

Lean **4.28.0**, commit `7e01a1bf5c70fc6167d49c345d3bf80596e9a79b`; Mathlib **`8f9d9cff6bd728b17a24e163c9402775d9e6a365`**. Os nove repositórios em `.lake/packages` correspondem ao manifest. Foi clonado por APFS o cache já compilado do repositório principal para este worktree, sem symlink e sem mudar versões. O diretório `.lake` continua ignorado pelo Git.

Após disponibilizar Mathlib, o primeiro teste focal ainda revelou ausência dos módulos locais `ConfiaLeanAuditor`. `lake build ConfiaLeanAuditor` resolveu esse preparo local (8038 jobs concluídos). A repetição dos dois testes formais passou: **2 passed em 89,21 s**. Não houve modificação do motor ou de expectativas. O preflight importa tanto Mathlib quanto ConfiaLeanAuditor e verifica `2 + 2 = 4` por `norm_num`.

Logs: [falha intermediária](assets/tme-december-hardening/lean-before-local-build.txt), [build](assets/tme-december-hardening/lean-build.txt), [testes preparados](assets/tme-december-hardening/lean-prepared.txt), [preflight](assets/tme-december-hardening/startup-preflight.txt). Preparação com rede/cache/build deve ocorrer 24h antes; nenhum download/build pertence à apresentação.

## Cenário reproduzível e resultados reais

Assessment **Dezembro - ensaio controlado Q1-Q3**, ID `asmt_dec20260000000000000000000000001`; participante **DEZ-ENSAIO-001**. Cada questão vale 20. Prova criada: `exam_6ac1e052b4d10b3cf1bca485de7cf0c2`.

| Questão | Entrada controlada | Resultado efetivamente calculado |
|---|---|---|
| Q1 / TME2026P1 | Original correto em duas páginas; leitura inicial troca 594 por 584; revisão restaura 594 | ConfIA 19 → 20; somente Q1 reanalisada |
| Q2 / TME2026P2 | Solução parcial: itens b/c, sem a | ConfIA 15; humano ajustou para 18 com motivo |
| Q3 / TME2026P3 | Erro matemático explícito `2/6=1/2` | ConfIA 18; erro refutado; humano aceitou |

Os textos exercitam fixtures matemáticas existentes, mas os quatro AuditRuns foram executados pelo motor real com Lean. Nenhuma resposta de auditoria foi substituída por mock no ensaio do navegador. O gold `[20,18,18]` é uma referência sintética independente importada, identificada como `synthetic-rehearsal / v1`; não é resultado oficial nem evidência de validade estatística.

## Ensaio no navegador — 33 passos

| Passos solicitados | Observação e evidência |
|---|---|
| 1–4: /tme sem login, nova correção, assessment, pseudônimo | Home e formulário operacionais; nenhuma credencial solicitada |
| 5–7: PDF multipágina, páginas e associação | Quatro páginas; Q1=1–2, Q2=3, Q3=4; reload preservou associações |
| 8–11: Q1, Original, Transcrição, Comparar | Três modos conferidos; [Original](assets/tme-december-hardening/03-original-desktop.jpg), [Comparar](assets/tme-december-hardening/04-compare-desktop.jpg) |
| 12–13: analisar Q1, sugestão/pauta/evidências | 19/20; erro na leitura refutado e evidências por página; [resultado](assets/tme-december-hardening/06-q1-audit.jpg) |
| 14: analisar Q2 | 15/20; revisão requerida pela solução parcial |
| 15–18: corrigir Q1, stale, reanálise isolada, antes/depois | Versão 2 da leitura; 19 anterior excluído do total atual; Q2 permaneceu no mesmo AuditRun; [stale](assets/tme-december-hardening/08-q1-stale.jpg), [19 → 20](assets/tme-december-hardening/09-reanalysis-comparison.jpg) |
| 19–22: aceitar, ajustar, justificar, confirmar todas | Q1 aceita; Q2 ajustada para 18 com motivo; Q3 analisada e aceita; todas confirmadas |
| 23–24: finalizar e resumo ConfIA × humano | v1: ConfIA 53/60, humano 56/60; [snapshot](assets/tme-december-hardening/12-finalized-v1.jpg) |
| 25–28: reabrir, alterar, finalizar nova versão, histórico | Q1 reaberta e ajustada para 19; v2 humano 55/60; v1 56/60 preservada; [histórico](assets/tme-december-hardening/13-finalized-v2-history.jpg) |
| 29: habilitar certificação | Flag habilitada no startup; acesso pelo resumo; aviso SHADOW e ausência inicial de gold conferidos |
| 30–31: importar gold e mostrar métricas | Importação v1 com três registros; [métricas](assets/tme-december-hardening/15-certification-metrics.jpg) |
| 32–33: exportar CSV e JSON | Downloads pelos controles reais do navegador; três registros em ambos; [CSV](assets/tme-december-hardening/certification.csv), [JSON](assets/tme-december-hardening/certification.json) |

Métricas observadas: ConfIA × gold N=3, MAE=1, bias=−1, concordância exata 66,7%; humano × gold MAE=0,333; ConfIA × humano MAE=1,333. JSON inclui quatro auditorias, dois fechamentos e histórico de gold. A revisão requerida de 25% usa quatro runs; não confundir com porcentagem de questões atuais. Precisão/recall por rubrica permanecem indisponíveis sem rótulos independentes, como esperado.

## Tempos, erros e comportamento inesperado

Tempos do motor calculados de `created_at`/`completed_at`, em [audit-timings.json](assets/tme-december-hardening/audit-timings.json):

| Operação | Duração |
|---|---:|
| Q1 inicial | 98,87 s |
| Q2 parcial | 48,04 s |
| Q1 reanálise | 14,43 s |
| Q3 erro matemático | 40,56 s |

O ensaio do navegador durou cerca de **10 min 37 s**, incluindo negativos, duas versões, exports e reinício. Recebimento do PDF: 0,497 s; primeira finalização: 0,387 s; download JSON: 5,225 s. Tempos de observação entre ferramentas, incluindo gold (≤7,635 s) e v2 (≤8,282 s), são limites superiores, não benchmarks do servidor. A primeira análise concorreu com preparação/testes; não executar esses processos durante a reunião. Reservar até dois minutos por análise, sem prometer SLA a partir desta amostra.

Houve três reloads deliberados: após associação, durante stale e após reinício. Uma aba foi fechada/reaberta após decisão humana; outra foi usada para conflito. Nenhum reload foi necessário para destravar a aplicação. Um timeout de espera e falhas de clique em controle fora da área visível ocorreram na automação; interação por teclado prosseguiu. Não foram falhas do motor. O console da aba final não apresentou erros ou warnings capturados; isso não substitui o registro dos HTTP 422/409 esperados nas abas anteriores.

**Bug operacional encontrado e corrigido:** a sondagem de porta do novo launcher recusou o primeiro reinício limpo por TIME_WAIT, mesmo sem listener ativo (`lsof` sem resultado). Foi adicionado `SO_REUSEADDR` à sondagem; a instância seguinte iniciou e recuperou a sessão. Uma porta com listener ativo continua impedida pelo bind: teste real em loopback retornou errno 48 e o rebind imediato após conexão/shutdown passou ([log](assets/tme-december-hardening/socket-restart-validation.txt)). [Antes](assets/tme-december-hardening/restart-before-fix.txt) / [depois](assets/tme-december-hardening/restart-after-fix.txt). Nenhuma alteração em backend de produto foi necessária.

## Falhas controladas

| Caso | Validação |
|---|---|
| PDF inválido | Navegador: 422 e orientação de PDF íntegro/sem senha; campos preservados; [captura](assets/tme-december-hardening/01-invalid-pdf.jpg) |
| Página ausente | Questão sem associação mostra instrução explícita e não oferece análise; [captura](assets/tme-december-hardening/02-missing-page.jpg); invariantes de associação cobertas em Python |
| Transcrição vazia | Navegador: “Informe a leitura de pelo menos uma página.”; não publica leitura vazia |
| Engine failure | Testes Python com exceção controlada persistem falha sem score fictício; JS valida mensagem, ausência de fallback numérico e retry. Não se interrompeu o motor real do cenário para fabricar uma falha |
| Stale audit | Navegador e reload: leitura antiga identificada, score anterior preservado historicamente e retirado do atual; confirmação stale rejeitada em Python |
| Confirmação concorrente | Duas abas: decisão antiga recebeu 409 e orientação para revisar dados; 18 preservado, sem duplicação; [captura](assets/tme-december-hardening/10-decision-conflict.jpg). Concorrência simultânea adicional com ThreadPoolExecutor passou |
| Gold inválido | 99/20 rejeitado com orientação de formato/códigos/limites; sem versão ativa até importação válida; [captura](assets/tme-december-hardening/14-invalid-gold.jpg) |
| Finalizar incompleta | Botão desabilitado com pendências explícitas; [captura](assets/tme-december-hardening/07-incomplete.jpg); POST forçado recusado nos testes de finalização |

A cobertura de engine failure é automatizada na fronteira backend e no renderizador JS; não é uma simulação visual manual no navegador. OCR remoto, indisponibilidade real de provedor externo e rede pública não foram exercitados. O percurso manual e o plano B dispensam essa dependência.

## Persistência e responsividade

Reloads preservaram prova, quatro páginas, associações, transcrições e estado stale. Fechar/reabrir workspace recuperou Q1=19 e histórico humano. Após shutdown seguro/restart, foram comparados SHA-256 de 92 arquivos: **91 registros/assets idênticos**, zero adicionados/removidos; apenas `tme_cases/.home-summary.json`, cache derivado, mudou. Conferidos prova, imagens originais/preview, revisões/acceptances, quatro AuditRuns, HumanDecisions, duas FinalCorrections e gold. [Manifesto de persistência](assets/tme-december-hardening/persistence.json).

No navegador, após restart: [v2 e totais](assets/tme-december-hardening/17-restored-finalization.jpg), [gold e métricas](assets/tme-december-hardening/18-restored-certification.jpg). A URL recupera a questão; resumo/certificação são reabertos pelos botões. Rascunhos ainda não salvos não são prometidos como persistentes.

Desktop **1366×900** e janela **800×900**: original/comparação e certificação legíveis, controles utilizáveis, sem overflow horizontal do documento (`scrollWidth=innerWidth=800`). [Comparação menor](assets/tme-december-hardening/05-small-window-800.jpg), [certificação menor](assets/tme-december-hardening/16-certification-small.jpg). Nenhum bug claro de layout encontrado; nenhum redesign/CSS alterado. Override de viewport restaurado.

## Testes executados

| Grupo | Resultado |
|---|---|
| D1–D7 + demo auth + operações | 109 testes distintos aprovados: primeira execução 108; após adicionar o teste de auth/certificação, operações 5/5 reaprovadas |
| Regressões relevantes | 782 passed, 1 skipped, 2 deselected, 229,52 s; os dois deselected são os formais executados separadamente |
| Lean focal preparado | 2 passed, 89,21 s |
| JavaScript | 519 passed, 0 failed |
| Total Python distinto | **893 passed, 1 skipped**, nenhuma falha remanescente |

O skip preexistente é `test_rubric_bridge.py`, artefato V2 local opcional, com regressão portátil equivalente; nenhuma expectativa foi ajustada para obter verde. Logs [Python focado](assets/tme-december-hardening/python-focused.txt), [operações](assets/tme-december-hardening/python-operations.txt), [regressões](assets/tme-december-hardening/python-regression.txt), [JS](assets/tme-december-hardening/javascript.txt).

Comandos reproduzíveis (venv acima; sempre `PYTHONPATH=app`):

```sh
PYTHONPATH=app ../confia-lean-auditor/.venv/bin/python -m pytest -q \
  tests/test_tme_full_exam.py tests/test_tme_review_workspace.py \
  tests/test_tme_question_audit.py tests/test_tme_reanalysis.py \
  tests/test_tme_human_confirmation.py tests/test_tme_finalization.py \
  tests/test_tme_certification.py tests/test_tme_demo_auth.py \
  tests/test_demo_december_operations.py

PYTHONPATH=app ../confia-lean-auditor/.venv/bin/python -m pytest -q \
  tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved \
  tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline

/usr/local/bin/node --test tests/js/test_*.cjs
```

Regressões: `test_submissions`, `test_transcriptions`, `test_recognition`, `test_recognition_invariants`, `test_mathpix_strokes`, `test_tme_pilot`, `test_tme_photo_errors`, `test_tme_home_summary`, `test_assessments`, `test_teacher_decisions`, `test_core_auth`, `test_core_institutional`, `test_tme_accepted_integration`, `test_submission_audits`, `test_pauta_engine`, `test_tme2_p1_pauta_bridge`, `test_tme2_p2_pauta_bridge`, `test_rubric_bridge`, `test_public_audit_boundary` (arquivos `.py` em `tests/`), excluindo os dois testes formais acima nessa execução.

## Freeze proposto

**DECEMBER_DEMO_RELEASE_CANDIDATE_01 — SHA da aplicação: `ed370faa715c6f4d879f1d023139c1cd47b166a0`.** O código da aplicação testado corresponde integralmente a esse commit. As adições operacionais deste hardening estão sem commit e, portanto, não pertencem a esse SHA. O manifesto `operational-files.sha256` identifica os arquivos entregues; um SHA único que inclua scripts, cenário, checklist e relatório só existirá após commit manual do usuário. Não há tag criada nem alegação de pacote integral já commitado.

Pronto para demonstração local com o ambiente preparado e o roteiro manual. Repetir o preflight 24h/1h antes, manter o mesmo storage para recuperação e não executar builds/suítes durante a reunião. Plano B explícito: transcrição manual; `--without-lean` somente anunciado como ausência de nova verificação formal. Nenhuma estatística deste ensaio é certificação de desempenho real.

**DECEMBER_DEMO_RELEASE_CANDIDATE_READY**
