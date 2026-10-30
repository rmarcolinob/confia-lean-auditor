# CONFIA-TME-WORKSPACE-01B — área útil desktop

## 1. Causa anterior

A regra `.correction-workspace { height: max(480px, calc(100dvh - 340px)) }` descontava uma altura fixa sem considerar os demais elementos. O shell era um bloco de altura automática; a decisão sticky sobrepunha o painel. O espaço restante era consumido por título e tabs em linhas distintas, status e metadata da transcrição no Original, toolbar de 62px e histórico fechado de 61px. Em 1440×900, `.solution-views` tinha apenas **282,5px** apesar do split de 560px.

## 2. Componentes e seletores

Mudanças restritas a `static/tme/correction-workspace.css`, `correction-workspace.js`, `tme.js` e referências de cache em `index.html`.

Principais seletores: body no workspace, `.workspace-shell`, main, `#app[data-view="workspace"]`, `.correction-workspace`, `.solution-topline`, `.solution-panel`, `.solution-views`, `.original-document`, `.transcript-document`, `.viewer-commands`, `.transcription-caption`, `.transcription-metadata`, `.analysis-column` e `.decision-bar`.

## 3. Nova estratégia vertical

Em ≥1100px, body/shell/main/app distribuem a viewport por flex. Header, contexto, enunciado e decisão têm altura intrínseca; o split recebe o restante com `flex: 1 1 0` e `min-height: 0`. A decisão participa do fluxo e tem separação de 8px do split. A mensagem redundante “Análise concluída” é omitida nesse layout quando não há mensagem específica ou ação pendente. Estados de erro/processamento e ações continuam disponíveis.

O enunciado KaTeX não foi alterado. Proporção padrão 60/40 e splitter existente preservados. Título/tabs dividem uma linha desktop; o histórico fechado ocupa 45px e, aberto, cresce até 35% do painel com scroll próprio.

## 4. Viewer

O painel é coluna flexível. Controles permanecem fixos e o viewer recebe o espaço variável. Toolbar: **48px**, mantendo zoom, página e rotação. No Original desktop, as duas linhas da transcrição são ocultadas. Na Transcrição/Comparar, o caption compacto apresenta, por exemplo, “Transcrição automática · Mathpix · revisão 1”; provenance completa continua no histórico. Mobile mantém as informações anteriores.

## 5. Ajuste à largura / à página

Default desktop: ajustar à largura. O cálculo preserva aspect ratio e considera rotação. Ajustar à página limita a imagem simultaneamente pela largura e altura reais do viewer. Selecionar um ajuste reaplica o enquadramento, retornando o zoom manual a 100%; ajustes manuais posteriores são preservados. Sem alteração dos bytes da imagem. A preferência fica em memória por caso, sem novo armazenamento persistente.

## 6. Expandir solução

Controle discreto no título, com nome acessível “Expandir solução”. Expande para toda a largura do split, escondendo análise e splitter somente no desktop. “Restaurar análise” repõe o painel e preserva seu estado recolhido/aberto. Sem fullscreen, nova rota ou reconstrução da imagem. Zoom, página, rotação e fit são preservados entre renderizações do caso.

## 7. Scroll e performance

Original/transcrição e análise têm rolagens independentes; cabeçalho da análise sticky no próprio painel. Na verificação, a análise rolou 565px enquanto manuscrito e página permaneceram em 0. Fit page rotacionado coube integralmente no viewer, sem scroll horizontal. Histórico aberto reduziu o viewer sem mover a decisão sobre ele.

Sequência de fit/expandir/restaurar/rotacionar não produziu novos registros HTTP no servidor. Testes confirmam reutilização dos mesmos elementos de imagem e nenhuma chamada de dados nessas ações.

## 8. Validação visual

| Viewport | Split | Viewer de solução | Área interna do original | Toolbar | Sobreposição da decisão |
| --- | ---: | ---: | ---: | ---: | --- |
| 1366×768 | 366,2px | 222,2px | 210,2px | 48px | Não |
| 1440×900 | 498,2px | 354,2px | 342,2px | 48px | Não |
| 1920×1080 | 678,2px | 534,2px | 522,2px | 48px | Não |

Em 1440×900, o viewer cresceu **25,4%** (282,5 → 354,2px). A imagem começa aproximadamente 146px mais acima. O aumento de 180px na altura do monitor passou integralmente ao viewer. As duas colunas têm a mesma altura e a decisão permanece dentro da viewport.

Também verificados 390×844, 393×852, 430×932 e 768×1024: fluxo vertical, controles desktop ocultos, sem overflow horizontal. O limite desktop 1100px com splitter a 45% manteve todos os controles utilizáveis. Testado em Chromium/IAB; sem certificação Safari iOS em aparelho físico.

Screenshots em `/private/tmp/confia-workspace01b/`: `before-1440x900.jpg`, `workspace-1366x768.jpg`, `workspace-1440x900.jpg`, `workspace-1920x1080.jpg`, `workspace-430x932.jpg`, além de expansão e fit rotacionado. Medidas em `responsive-checks.json`.

## 9. Testes

- `node --test tests/js/test_*.cjs`: **406 aprovados, 0 falhas, 0 ignorados**; seis testes novos em `test_tme_workspace_01b.cjs`.
- `.venv/bin/python -m pytest -q tests/test_tme_photo_errors.py tests/test_tme_pilot.py`: **35 aprovados, 0 falhas**.
- Sete larguras/alturas verificadas no navegador; assertions sobre overflow, altura igual dos painéis, decisão sem sobreposição, toolbar, crescimento e preservação mobile.

Arquivos adicionais: `tests/js/tme-dom.cjs` (viewport desktop simulado), `tests/js/test_tme_workspace_01b.cjs` e este relatório. Nenhum backend, OCR, transcrição, asset de problema, KaTeX, Auditor, claim, rubrica, Lean, score policy ou TeacherDecision alterado nesta tarefa. Conferência contra hashes do início da tarefa.

## 10. git diff --check

**Exit 0**, sem saída. Arquivos novos/alterados também verificados contra whitespace final.

## 11. git status --short

Saída integral em `/private/tmp/confia-workspace01b/git-status-short.txt`; lista específica desta tarefa em `changed-files.txt`. Alterações anteriores foram preservadas.

Sem staging, commit ou push.
