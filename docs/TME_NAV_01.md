# TME NAV-01 — Navegação moderna unificada

23/10/2026 · `feat/tme-dual-input`.

## 1. Mapa encontrado antes da mudança

Mapeamento realizado antes de editar código; [registro inicial](/private/tmp/confia-nav01/navigation-before.md).

| Ação | Destino anterior | URL / comportamento |
| --- | --- | --- |
| Início | `home()` | `/tme` |
| Fila / Ver fila / Ver fila completa | `cases(false)` | `/tme`; lista antiga |
| Nova / Nova correção | `newCase()` | `/tme`; formulário no shell antigo |
| Resultados | `cases(true)` | `/tme`; somente finalizadas, lista antiga |
| Progresso: Ver todas | `cases(false)` | Mesma fila antiga |
| Card de prova | `cases(false)` | Sem filtro da prova clicada |
| Abrir caso | `openCase(id)` | `/tme?case_id=...`; workspace moderno |
| Voltar do workspace | `navigate("cases")` | Origem perdida |

As mudanças usavam `replaceState`; não havia restauração por `popstate`, view na URL ou histórico entre as telas.

## 2. Por que o legado aparecia

Os seletores que ocultavam `.top` e `.sidebar` e exibiam o header moderno só cobriam `home` e `workspace`. As outras views reutilizavam a estrutura administrativa. A fila também buscava todos os casos e hidratava cada um com transcrições, auditorias, decisão, submission e reconhecimento, sem paginação.

## 3. Nova navegação e shell

O documento TME usa `data-tme-shell="modern"`, que isola o shell moderno em todas as views. O HTML e CSS legados foram preservados; nenhum outro módulo foi removido ou migrado.

| URL | View |
| --- | --- |
| `/tme` | Home |
| `/tme?view=queue` | Fila |
| `/tme?view=new` | Nova correção |
| `/tme?view=results` | Resultados |
| `/tme?view=exams` | Progresso por prova |
| `/tme?view=queue&exam=...` | Questões conhecidas de uma prova |
| `/tme?case_id=...` | Workspace ou entrada existente do caso |

Mantido o identificador interno `cases`; `view=cases` também é aceito. Filtros e página ficam na query. URLs inválidas de view caem na Home moderna. O menu contém os mesmos quatro itens; Progresso ativa Resultados, e Workspace ativa Fila.

## 4. Fila

- Lista desktop em colunas; cards no mobile, sem tabela comprimida.
- Linha inteira é um botão nativo, operável por clique, toque, Enter e Espaço.
- Busca, questão, status, origem e atualização discreta por ícone.
- **50 casos por página**, com anterior/próxima; API aceita no máximo 100.
- Mesmos `StatusPill` e CTA da Home. “Corrigir próxima” consome a prioridade do mesmo `/tme/home-summary`, sem algoritmo alternativo.
- Sugestão numérica, inclusive zero, é exibida quando existe. Valor indeterminado não vira zero; ausência de projeção da sugestão aparece como “Não disponível”.
- “Ver fila completa” limpa filtros anteriores. Voltar do workspace preserva filtros e página de origem.

## 5. Nova correção e entradas

Formulário com código da prova, questão do catálogo existente e cards Foto / scan e Escrever no tablet. Seleção exposta por `aria-pressed`, validação nativa e bloqueio de envio duplicado.

A criação continua em `POST /tme/cases`; em seguida abre o mesmo fluxo do caso. Foto reaproveita seleção/câmera, três páginas, preview, confirmação, remoção, reordenação, rotação e preservação dos originais. Escrita digital continua no capture existente, sem mudanças em strokes, pointer events, pressão, undo/redo, autosave, snapshots, PNG ou JSON. Apenas o painel externo recebe os tokens modernos.

O retorno do capture continua usando a mensagem validada existente e abre o workspace. Ao ajustar páginas e criar outro caso, a URL passa a apontar para o novo caso. Nenhum caso real ou decisão foi criado durante a inspeção visual; criação/submissão foram exercitadas pelos testes com fixtures e mocks.

## 6. Resultados

Reutiliza `OverviewMetrics`/`MetricCard` da Home e a mesma função de classificação operacional. Exibe todo o período de forma explícita, correções finalizadas por questão e distribuição atual. Os botões de questão/status abrem a fila filtrada.

São indicadores operacionais reais. Não há métricas inventadas de produtividade, tempo médio ou desempenho matemático do participante; não foi adicionada biblioteca de gráficos.

## 7. Progresso por prova

Cards com finalizadas/total conhecido, estados das questões, barra e atualização. O total não pressupõe cinco questões. A regra de escolher o caso mais recente por prova/questão é compartilhada com a Home. Abrir a prova mostra suas questões conhecidas no mesmo componente moderno de fila; cada uma abre seu workspace.

## 8. Deep links

`case_id` mantém prioridade sobre `view` e abre diretamente o workspace atual. Views e filtros funcionam ao recarregar a página. A ausência de ambos abre a Home. Deep link sem origem usa Fila como retorno.

## 9. Histórico

Navegação utiliza `pushState` e restauração por `popstate`. A origem do workspace fica no estado do histórico, incluindo filtros. Voltar/avançar foi testado no navegador real e nos testes JS. Repetição de navegação ainda pendente compartilha o trabalho; não adiciona entrada duplicada nem outra busca da mesma página. Respostas de uma view anterior não substituem a atual.

## 10. Desktop

**1440×900 e 1920×1080 aprovados** nas seis telas. Header da Home compartilhado, com logo, submarca, quatro itens, avatar, altura e largura máxima consistentes. O header desktop do Workspace foi alinhado ao mesmo max-width; a largura aprovada do manuscrito foi preservada. Resultados e Progresso aproveitam duas colunas; Fila tem lista densa.

## 11. Tablet

**768×1024 e 1024×768 aprovados** nas seis telas. Layout e dimensionamento do workspace/capture existentes preservados. Novas telas usam os mesmos tokens e navegação superior do tablet. O caderno existente foi aberto e inspecionado, sem desenhar ou enviar dados.

## 12. Mobile e acessibilidade

**430×932 aprovado** nas seis telas. Bottom nav com quatro itens e estado ativo. Fila em cards, formulário em coluna, progresso em cards e Resultados com métricas horizontais e seções empilhadas.

Sem overflow horizontal nas 30 combinações de view/viewport. Controles novos têm altura mínima de 44 px; inputs/selects usam 16 px. Headings, labels, foco visível, status textuais, paginação nomeada e skeleton com status acessível. Busca sem resultado e avatar foram verificados no navegador; erros por domínio e retries cobertos pelos testes. Não houve teste em tablet/iPhone físico.

## 13. Dados, performance e testes

O endpoint **existente** `GET /tme/cases` ganhou projeções opcionais `view=queue|exams|results`, filtros e paginação. Sem `view`, a resposta original permanece compatível. Todas as projeções usam `require_tme_evaluator`, filtram pelo avaliador e respondem com `Cache-Control: no-store`.

A pequena extensão de backend foi necessária: `/home-summary` só disponibilizava três casos e duas provas, enquanto `/cases` não tinha paginação ou status operacional. Não foi criado endpoint duplicado. O índice descartável existente passa a guardar apenas os escalares de sugestão já calculados; sem alterar auditoria, nota, decisão ou seus artefatos. Sua reconstrução ocorre no startup, como antes.

Listagens não carregam manuscritos, transcrições, AuditRuns completos, reconhecimento ou Lean. A fila monta uma página de metadados e consulta a prioridade da Home uma vez; Resultados/Progresso fazem uma consulta de metadados. O servidor ainda lê o índice operacional inteiro para filtrar/agrupar: foi validado com **25 mil casos**, respostas limitadas e nenhuma consulta aos serviços de artefatos. Isso não equivale a um teste de carga concorrente de produção.

- **449 testes JS passaram**, zero falhas/ignorados: `node --test tests/js/test_*.cjs`.
- **87 testes Python passaram**: `tests/test_tme_navigation.py`, `test_tme_home_summary.py`, `test_tme_demo_auth.py`, `test_tme_photo_errors.py`, `test_tme_pilot.py`, `test_tme_audit_view.py`, `test_capture_static.py`.
- **24 testes JS novos**: rotas, criação dos dois modos, workspace/retorno, deep links, histórico, paginação, requisições, erro e vazio.
- **5 testes Python novos**: paginação/filtros, isolamento, valores zero/nulos, métricas consistentes, questões conhecidas, compatibilidade, 25 mil casos, validação e indisponibilidade.
- Testes anteriores de captura, transcrição, auditoria, decisão e workspace continuaram passando. Expectativas antigas de fila foram atualizadas para a nova navegação.
- Console sem warnings/errors na sessão visual final.

[Log JS](/private/tmp/confia-nav01/js-tests.log) · [Log Python](/private/tmp/confia-nav01/python-tests.log) · [Medições](/private/tmp/confia-nav01/geometry.json) · [Verificações visuais](/private/tmp/confia-nav01/visual-checks.txt).

Arquivos alterados nesta tarefa:

- Frontend existente: `static/tme/index.html`, `home.js`, `tme.js`.
- Frontend novo: `static/tme/secondary-views.js`, `secondary-views.css`.
- Projeção/rota existentes: `tme/home_summary.py`, `tme/router.py`.
- Testes existentes: `tests/js/tme-dom.cjs`, `test_correction_workspace.cjs`, `test_tme_home.cjs`, `test_tme_pilot_ui.cjs`, `test_tme_workspace_01.cjs`.
- Testes novos: `tests/js/test_tme_navigation.cjs`, `tests/test_tme_navigation.py`.
- Este relatório.

Os caminhos frontend/backend acima são relativos a `app/confia_lean_auditor/`. Comparação de hashes com o início confirma esse escopo. Auditor, execute_audit, extractors, claims, rubricas, score policy, Lean, Mathlib, OCR/Mathpix, modelos RecognitionRun/AuditRun/TeacherDecision e GOV-01 não foram alterados nesta tarefa.

## 14. Screenshots

Artefatos locais, sem inclusão automática no Git. Dimensões indicam viewport CSS; a captura nativa pode excluir a barra de rolagem.

| Tela | 430×932 | 768×1024 | 1024×768 | 1440×900 | 1920×1080 |
| --- | --- | --- | --- | --- | --- |
| Home | [ver](/private/tmp/confia-nav01/home-430x932.jpg) | [ver](/private/tmp/confia-nav01/home-768x1024.jpg) | [ver](/private/tmp/confia-nav01/home-1024x768.jpg) | [ver](/private/tmp/confia-nav01/home-1440x900.jpg) | [ver](/private/tmp/confia-nav01/home-1920x1080.jpg) |
| Fila | [ver](/private/tmp/confia-nav01/queue-430x932.jpg) | [ver](/private/tmp/confia-nav01/queue-768x1024.jpg) | [ver](/private/tmp/confia-nav01/queue-1024x768.jpg) | [ver](/private/tmp/confia-nav01/queue-1440x900.jpg) | [ver](/private/tmp/confia-nav01/queue-1920x1080.jpg) |
| Nova | [ver](/private/tmp/confia-nav01/new-430x932.jpg) | [ver](/private/tmp/confia-nav01/new-768x1024.jpg) | [ver](/private/tmp/confia-nav01/new-1024x768.jpg) | [ver](/private/tmp/confia-nav01/new-1440x900.jpg) | [ver](/private/tmp/confia-nav01/new-1920x1080.jpg) |
| Resultados | [ver](/private/tmp/confia-nav01/results-430x932.jpg) | [ver](/private/tmp/confia-nav01/results-768x1024.jpg) | [ver](/private/tmp/confia-nav01/results-1024x768.jpg) | [ver](/private/tmp/confia-nav01/results-1440x900.jpg) | [ver](/private/tmp/confia-nav01/results-1920x1080.jpg) |
| Progresso | [ver](/private/tmp/confia-nav01/exams-430x932.jpg) | [ver](/private/tmp/confia-nav01/exams-768x1024.jpg) | [ver](/private/tmp/confia-nav01/exams-1024x768.jpg) | [ver](/private/tmp/confia-nav01/exams-1440x900.jpg) | [ver](/private/tmp/confia-nav01/exams-1920x1080.jpg) |
| Workspace | [ver](/private/tmp/confia-nav01/workspace-430x932.jpg) | [ver](/private/tmp/confia-nav01/workspace-768x1024.jpg) | [ver](/private/tmp/confia-nav01/workspace-1024x768.jpg) | [ver](/private/tmp/confia-nav01/workspace-1440x900.jpg) | [ver](/private/tmp/confia-nav01/workspace-1920x1080.jpg) |

[Fila vazia](/private/tmp/confia-nav01/queue-empty-430x932.jpg) · [Questões da prova](/private/tmp/confia-nav01/exam-detail-1920x1080.jpg) · [Entrada foto desktop](/private/tmp/confia-nav01/photo-entry-1440x900.jpg) · [Entrada foto mobile](/private/tmp/confia-nav01/photo-entry-430x932.jpg) · [Capture existente no tablet](/private/tmp/confia-nav01/ink-entry-768x1024.jpg).

## 15. Git diff --check

Sem erros; whitespace dos arquivos novos também verificado.

## 16. Git status --short

[Saída completa](/private/tmp/confia-nav01/git-status-short.txt), incluindo as mudanças preexistentes na branch. Sem staging, commit ou push.

**Critério final:** existe algum retorno visual ao shell administrativo ao navegar pelas funções TME? **Não**, nos fluxos e resoluções verificados.
