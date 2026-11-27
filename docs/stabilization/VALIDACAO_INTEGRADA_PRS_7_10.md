# ConfIA — validação integrada dos PRs #7, #8, #9 e #10

Data: 27/11/2026 (America/Fortaleza). Evidência produzida nesta execução, separada dos relatórios individuais dos PRs.

**APROVADO COM LIMITAÇÕES na integração técnica offline. Merge à main condicionado ao CI do conjunto e à verificação visual pendente; sem validação semântica independente.**

## Integração e preservação

Branch isolada: `codex/validate-integrated-pr7-10`.
Worktree: `/private/tmp/confia-integrated-pr7-10`.
Base remota confirmada: `923bf3acbd9994af9662bcdff6b18eac1b6d4df9`.

| PR | Commit solicitado e verificado no GitHub | Commit local com cherry-pick -x |
|---|---|---|
| #7 | `5f37f4db5397253b83e9c48266b7805f59ca6ea7` | `2c4f213cd78b7e4afcd32f19a9445d73ad13bc84` |
| #8 | `3a1cf5f00f36a1f8768a1b4314cf6b4471706a3a` | `5db3a98de1f3e7e19b9fc0c6125606111f53776d` |
| #9 | `61bae9dc273b71a116f04ffc90b0d9afcf097465` | `9395b1162fe7785c3caa8126b27d94c6525f96ec` |
| #10 | `ff7a098bc9ab9a5d71d55d6aaab90291afa7386c` | `13822365e7cc9848fd828b5f2718f3dc4151c57e` |

Aplicação na ordem solicitada, sem conflitos, sem alterações adicionais de produção. Todos os commits originais têm a base indicada como pai. A main local estava em `97c84bb432dd751878d532adeab35bb4e57a24dc`; foi preservada, usando a main remota atual para a nova branch. O checkout inicial continua destacado em `923bf3a`. As quatro branches originais, a main e a tag `SPECIALIZED-TME2-RC1` foram preservadas. Tag anotada `0c64e318a26e21f71fe3097c66ee17a5206dd8a3`, alvo `c03403fe5b83d9db9df172882bd69af3dfa2d027`.

Os PRs continuavam abertos, não integrados e nos mesmos heads na consulta inicial e na reconferência. Nenhum push, merge remoto ou chamada paga foi realizado.

## GitHub e falha histórica

As execuções de pull_request dos quatro PRs estavam aprovadas em Python e Lean. A consulta restrita a pull_request não mostrava a falha do PR #10; foi necessário consultar também o evento push.

- [Push Python do PR #10, run 46038834453](https://github.com/rmarcolinob/confia-lean-auditor/actions/runs/46038834453): **1 falha, 3711 aprovados, 52 skips, 1 xfail**, 3510,83 s; job `140641042965`. Falha exatamente em `test_five_problems_accepted_engine_persistence_api[full-4]`, `AUDITOR_FAILED`. JavaScript não executou nesse job por causa da falha anterior.
- [Pull request Python do mesmo head, run 46038908451](https://github.com/rmarcolinob/confia-lean-auditor/actions/runs/46038908451): aprovado na primeira tentativa. Não foi um retry do push.
- [Lean CI do pull request, run 46038908413](https://github.com/rmarcolinob/confia-lean-auditor/actions/runs/46038908413): aprovado. O workflow Lean também executa Python.

Não houve alteração inesperada de commits. A coexistência de aprovação e falha é compatível com intermitência, não uma prova de resolução anterior.

## Ambiente e método

macOS 27.2.1 arm64; Python 3.9.6 do ambiente existente do projeto, Node 24.15.0, Lean 4.28.0, Lake 5.0.0-src+7e01a1b. Dependências registradas em `artifacts/integrated-validation/environment.log`. O Python CI histórico usa 3.11.18/Linux: não se declara equivalência integral entre ambientes.

`PYTHONPATH` aponta explicitamente para `app:tests` deste worktree, com `CONFIA_LEAN_AUDITOR_ROOT` também isolado. `import-provenance.log` confirma a origem dos módulos; o editable instalado no venv pertence a outro checkout e não foi reinstalado/modificado. Ambiente dos subprocessos construído por lista permitida; credenciais e variáveis de providers herdadas foram excluídas. Os três flags LLM foram definidos como `0`. Fixtures podem substituir transportes por mocks explicitamente identificados; não houve acesso a providers pagos.

A fixture global preserva as políticas legadas nos testes históricos; as suítes das políticas atuais optam explicitamente por v1. Testes institucionais reativam autenticação. O percurso adicional de plataforma foi executado com autenticação ligada e `dynamic-semantic.v1`, sem provider semântico simulado.

Cache `.lake` copiado por clone de arquivos, sem symlink para build mutável de outro worktree. Cópia concluída antes de `lake build`; build concluído antes da suíte Python. Mathlib conferida em `8f9d9cff6bd728b17a24e163c9402775d9e6a365`. Nenhum `lake update`; manifests formais intactos. É build com cache pré-provisionado, não reconstrução fria de toda Mathlib.

## Resultados desta validação

| Verificação | Resultado desta versão combinada |
|---|---|
| Python completo: `python -m pytest -q -rs tests` | **3755 aprovados, 52 skips, 1 xfail; 0 falhas, 0 erros** (3808 coletados) |
| JavaScript: `node --test tests/js/*.cjs` | **631 aprovados**, 0 falhas/skips, 1,89 s |
| Lean: `lake build` após provisionamento completo | **Aprovado**, 8038 jobs, 9,24 s com cache |
| P4, repetições e controles | 30/30 isolados + 5/5 sob pausas aprovados; controle antigo 5/5 falhas esperadas; também aprovado na suíte completa |
| Fluxo textual autenticado e retomada em processos novos | **Aprovados**, com adjudicação humana sintética e providers desligados |
| Plano smoke `--text-only` | **PLAN_ONLY**, 0 chamadas, OCR limitado a 0 |
| `git diff --check 923bf3a` e comparação de fontes com `1382236` | Sem erro de whitespace; nenhuma alteração adicional em app, testes, scripts de produção ou formalizações |
| Navegador/teclado real | **Pendente por indisponibilidade da ferramenta**, não substituído por mocks |

O pytest registrou **5439,41 s (1h30min39s)** e dois avisos de exportação JUnit: `record_property` incompatível com `xunit2` em dois testes CAP04 existentes. Não são falhas do motor; nenhum teste foi alterado para suprimir os avisos. Tempos e códigos de cada subprocesso estão nos metadados. A execução Python permaneceu aberta por 12809.12 s de relógio de parede durante a longa sessão, que incluiu a indisponibilidade da automação do navegador; não usar esse número como benchmark de desempenho da aplicação.

Os [skips e o xfail](evidence/integrated-validation/skips.md) estão discriminados por motivo e arquivo. [Resultados por arquivo](evidence/integrated-validation/python-results.json), [log Python completo](evidence/integrated-validation/python-full.log) e [log JavaScript](evidence/integrated-validation/javascript.log) permitem conferir os totais. Nenhum skip/xfail foi adicionado nesta sessão.

Recortes incluídos no total (não somar novamente):

| Recorte | Aprovados |
|---|---|
| DYNAMIC: todos test_dynamic*.py | 577 |
| Matriz dos 16 temas | 112 |
| Estabilidade P3/P4 | 7 |
| RHS F2Q1, incluindo Lean real | 24 |
| F2Q6: política semântica atual | 4 |
| Gestão: decisões e divulgação atuais | 5 |
| Orçamento e bloqueio de OCR no smoke | 13 |


Comandos e evidência detalhada ficam em `artifacts/integrated-validation/`, incluindo logs brutos, metadados JSON por execução, XML JUnit e scripts de reprodução. Os logs copiados para a documentação tiveram apenas espaços finais removidos para atender `git diff --check`; os originais brutos permanecem em artifacts. Um resumo preservado está em [evidence/integrated-validation](evidence/integrated-validation/), com [instruções e snapshot de reprodução](evidence/integrated-validation/reproduction/README.md). Não há retry automático nem conversão de falha em sucesso. A suíte completa conserva testes de captura/recognition já existentes com mocks; nenhum OCR real foi executado ou desenvolvido.

## P4: comparação controlada e limites da conclusão

O teste original usa Lean desligado (`tme_use_lean=False`), texto sintético aceito, motor matemático/extratores reais e persistência real em diretórios temporários. A disponibilidade do cache Lean não explica essa ocorrência específica.

| Condição | Resultado |
|---|---|
| Teste original inalterado, 30 subprocessos, `PYTHONHASHSEED=1..30`, sem pausa injetada | **30/30 aprovados**, 149,44 s acumulados |
| Primeiro ensaio: pausa única na primeira canonização da segunda extração, orçamento original em memória | 5/5 aprovados; provocação insuficiente, preservada nos logs |
| Mesmo primeiro ensaio, versão combinada | 5/5 aprovados |
| Controle refinado: pausa real de 100 ms na primeira canonização de cada reextração, Budget original em memória, seeds 1..5 | **5/5 falharam com AUDITOR_FAILED** |
| Mesmo controle refinado com Budget do PR #7, seeds 1..5 | **5/5 aprovados**, 80,35 s acumulados |

Os controles executam o mesmo nodeid e as mesmas asserções de nota 20, integridade, consulta e persistência. A substituição do Budget antigo ocorre apenas no processo diagnóstico, carregando sua implementação diretamente da base Git; código de produção em disco, testes, critérios e notas esperadas não foram alterados. No primeiro ensaio, a pausa não necessariamente afetava a evidência cuja igualdade estava sendo comparada; o controle refinado cobre as reextrações seguintes. As aprovações do ensaio inicial não foram omitidas.

O controle antigo registra `stage=engine type=ValueError location=student_claims/digital_items.py:44`, onde está a proteção `Literal source projection is inconsistent`. O orçamento de 50 ms de relógio de parede pode expirar quando o processo é desescalonado; a reextração da mesma fonte passa então a divergir da primeira projeção. O PR #7 mede CPU da própria thread e preserva esse limite, limites estruturais e a proteção de integridade.

**O mecanismo foi reproduzido e corrigido na versão combinada; a falha espontânea não reapareceu nas 30 repetições. Isso não demonstra eliminação universal da intermitência nem prova retrospectivamente a causa do run histórico**, que descartava a exceção interna. Custos reais de CPU acima do orçamento, outras exceções de pipeline e diferenças de ambiente permanecem possíveis; os novos diagnósticos permitem distingui-los. Não se recomenda ampliar timeout, remover validação de origem, alterar pontuação ou repetir CI até aparecer verde.

## SPECIALIZED

**Funcional nos cenários offline verificados, com verificações Lean reais de escopo delimitado; semântica real continua não validada.**

A suíte cobre ITA/TME², extração/grounding, fidelidade e atribuição, evidência positiva, bloqueio de crédito indevido, Semantic B/fallback mínimo, rubricas/PautaEngine, pontuação e contratos de persistência. Inclui certificados/checkers Lean reais e regressões de RHS F2Q1: atribuir a expressão escrita não concede verdade; o checker existente verifica a forma correta e refuta a incorreta.

As provas Lean certificam as proposições formalizadas, não toda a solução em linguagem natural. Casos semânticos usam respostas simuladas ou replay arquivado, sem nova inferência real. A limitação legada de F2Q6 permanece como xfail; o roteamento semântico atual é testado, mas com provider desligado ou simulado. Não houve alteração de checker, formalização, pauta, política matemática ou peso de critério.

## DYNAMIC

**Fluxos e contratos offline aprovados; qualidade matemática dos pareceres LLM não foi medida.**

A suíte cobre Grader, Reviewer independente, Reconciliation, crédito parcial autorizado, dependências, recusa de crédito sem evidência, divergências e adjudicação humana. A matriz de 16 temas contém **96 integrações com pareceres simulados e 16 com provider desabilitado**; ela valida contratos e fluxo, não a acurácia matemática de um LLM.

Temas: conjuntos, intervalos, porcentagem, razão, proporção, função afim, quadrática, modular, exponencial, logarítmica, equação, inequação, juros simples, juros compostos, geometria plana e trigonometria. Os rótulos do corpus são sintéticos, não gold independente. O DYNAMIC não executa Lean; suas verificações exatas têm escopo limitado. Concordância de dois agentes semânticos não é prova formal.

O helper `dynamic_rc1_smoke.py --text-only` retornou **PLAN_ONLY, api_calls=0, OCR=0, máximo 21 chamadas, teto US$ 6**. Isso apenas prepara um futuro smoke; não autoriza execução nem valida tarifas/modelos atuais.

## Plataforma e retomada

**Percurso autenticado por API aprovado; percurso visual desta combinação permanece pendente.**

O script `platform_flow.py` usa APIs ASGI reais via TestClient, contas/instituições sintéticas e diretório dedicado. Providers desligados, sem substituir pareceres semânticos no percurso adicional:

1. Professor cadastra avaliação e questão inédita; ativação sem rubrica aprovada retorna 409.
2. Rubrica manual aprovada com desenvolvimento 6 e resultado 4; atividade publicada para turma.
3. Aluno envia solução digitada; retry mantém o mesmo ID. Grader/Reviewer/Reconciliation executam, mantendo a nota inconclusiva por indisponibilidade semântica.
4. Professor adjudica os dois critérios com justificativa explícita, confirma 10/10 e finaliza. **10/10 é uma decisão humana sintética introduzida pelo teste**, não acerto automático medido.
5. Resultado oculto até divulgação explícita. Aluno não pode divulgar (403); após divulgação docente, vê nota e feedback.
6. Gestão: 1 submissão, 1 confirmação, 0 divulgações antes; 1 divulgação depois. Os indicadores de AuditRun continuam refletindo o Grader, incluindo 1 inconclusivo, e não foram reinterpretados como acurácia ou reconciliação concluída.
7. Anônimo 401, outro aluno 404, professor de outra escola 403, aluno no workspace docente 403 e gestor fora de escola 403.
8. Outros processos Python retomam os mesmos registros; retry da submissão devolve a mesma tentativa, auditoria tem o mesmo ID e bytes/hash preservados; resultado divulgado e indicadores mantidos.

O primeiro ensaio de retomada falhou porque o harness apontava `SUBMISSION_AUDITS` para `submission_audits`, enquanto a fixture inicial usava `audits`. O ajuste mínimo foi alinhar esse diretório no harness, sem mudar produção ou dados. O log da falha inicial foi mantido. O primeiro bind HTTP também foi bloqueado pelo sandbox; um servidor local autorizado iniciou normalmente e foi encerrado depois.

**Validação visual/teclado não concluída nesta sessão:** o host de acesso ao navegador estava indisponível; a alternativa nativa Chrome terminou por timeout. Os 631 testes JavaScript e as APIs não substituem esse percurso. Capturas dos PRs são evidência anterior, não foram apresentadas como novas capturas da versão combinada.

## Pendências e recomendação

**Recomendo integrar os quatro PRs como estabilização técnica, nesta ordem e com os quatro commits juntos, após revisão humana, CI da versão combinada e conclusão do percurso visual/teclado pendente. Não recomendo merge imediato enquanto esses dois checks operacionais não estiverem concluídos.** Não foi encontrada regressão bloqueante nos testes locais executados; não foi necessária correção adicional de produção.

A falha P4 tem um mecanismo demonstrado e corrigido pelo PR #7, com recorrência controlada no Budget antigo e ausência de recorrência nas execuções combinadas registradas. A ausência de exceção histórica impede atribuição causal definitiva. Manter diagnósticos e investigar qualquer nova ocorrência, sem esconder falhas com retries.

As pendências científicas abaixo impedem declarar o corretor semanticamente validado, mas são distintas da integração dessas correções técnicas. O CI remoto do conjunto não foi iniciado porque não houve push autorizado.

Pendências científicas: 21 casos históricos sem validação independente; gold humano cego; acurácia por critério; alternativas válidas, erros sutis e dependências; inferência real, custo e latência ainda não medidos. Providers indisponíveis mantêm critérios pendentes e exigem decisão docente explícita. Não há autorização para correção escolar autônoma.

Pendências operacionais: repetir percurso visual e teclado em navegador disponível; validar CI do commit combinado em Linux/Python 3.11 antes de merge; observabilidade das futuras falhas P3/P4; dimensionamento dos indicadores de Gestão, que leem históricos. Os skips por artefatos locais ausentes e o xfail legado permanecem explícitos. OCR/reconhecimento manuscrito/captura avançada seguem fora de escopo, sob responsabilidade de Luis.

## Arquivos integrados

36 arquivos dos quatro commits, 1148 inserções e 40 remoções; a contagem inclui quatro imagens de evidência histórica. Nenhum conflito resolvido manualmente. Este relatório e seus novos registros de evidência são a documentação adicional desta sessão; nenhum ajuste de produção foi necessário para a integração.

- `app/confia_lean_auditor/core/math_canonical/parser.py`
- `app/confia_lean_auditor/dynamic/school_service.py`
- `app/confia_lean_auditor/management/question_decisions.py`
- `app/confia_lean_auditor/management/router.py`
- `app/confia_lean_auditor/static/app.js`
- `app/confia_lean_auditor/static/shell.js`
- `app/confia_lean_auditor/student_claims/grounding.py`
- `app/confia_lean_auditor/submission_audits/service.py`
- `docs/stabilization/FASE1_ESTABILIZACAO_TECNICA.md`
- `docs/stabilization/FASE2_SPECIALIZED.md`
- `docs/stabilization/FASE3_DYNAMIC.md`
- `docs/stabilization/FASE4_PLATAFORMA.md`
- `docs/stabilization/RESULTADO_ESTABILIZACAO.md`
- `docs/stabilization/SMOKE_TEXTUAL_POSTERIOR.md`
- `docs/stabilization/evidence/dynamic/SHA256SUMS`
- `docs/stabilization/evidence/dynamic/offline-results.json`
- `docs/stabilization/evidence/dynamic/text-smoke-samples.json`
- `docs/stabilization/evidence/f2q6-current-policy.json`
- `docs/stabilization/evidence/platform/SHA256SUMS`
- `docs/stabilization/evidence/platform/institutional-flow.json`
- `docs/stabilization/evidence/platform/management-current.jpg`
- `docs/stabilization/evidence/platform/resume.json`
- `docs/stabilization/evidence/platform/student-release.jpg`
- `docs/stabilization/evidence/platform/study-provider-unavailable.jpg`
- `docs/stabilization/evidence/platform/teacher-decision.jpg`
- `scripts/evaluation/dynamic_rc1_smoke.py`
- `tests/fixtures/dynamic_highschool_topics.json`
- `tests/js/test_ui_01_shell.cjs`
- `tests/test_digital_extraction_stability.py`
- `tests/test_dynamic_highschool_topics.py`
- `tests/test_f2q6_current_semantic_routing.py`
- `tests/test_ita_equality_chain_grounding.py`
- `tests/test_management_dynamic_decisions.py`
- `tests/test_math_canonical.py`
- `tests/test_rc1_smoke_budget.py`
- `tests/test_submission_audits.py`
