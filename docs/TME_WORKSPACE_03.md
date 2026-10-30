# TME WORKSPACE-03 — Ergonomia final

22/10/2026 · `feat/tme-dual-input`.

## 1. Header mobile e redução até o manuscrito

Medições antes/depois no mesmo caso real (`prova2`, ITA2025F2Q3), mesma imagem e mesma viewport:

| Viewport CSS | Header antes → depois | Primeiro pixel do manuscrito antes → depois | Redução |
| --- | --- | --- | --- |
| 430×932 | 196,5 → 128,5 px | 561,9 → 395,1 px | **29,7%** |
| 390×844 | 196,5 → 128,5 px | 607,2 → 395,1 px | **34,9%** |
| 1440×900 | 90,5 → 90,5 px | 368,8 → 368,8 px | Desktop preservado |

Header móvel 68 px mais baixo (34,6%). Metadados essenciais em linha compacta. A contagem textual de questões continua no desktop; no mobile, as questões conhecidas continuam acessíveis no navegador de questões. Etapas compactas, sem mudança da etapa atual.

Helper exclusivamente visual `displayExamName`: `prova2` → `Prova 2`; `prova00231` → `Prova 00231`. O identificador persistido não é alterado.

## 2. Indicador de questão

Quando existe uma única questão conhecida, o indicador e as etapas compartilham a mesma linha no mobile. Q3 usa superfície azul clara e área de toque de **44×44 px**; não ocupa mais uma linha inteira isolada. Para múltiplas questões, continua existindo navegação horizontal somente pelas questões conhecidas.

## 3. Original sem metadata de transcrição

`Transcrição disponível` e o caption de transcrição ficam ocultos na aba Original em todos os breakpoints. Também não aparecem em Comparar. O estado é aplicado com `hidden`, incluindo a árvore acessível.

No mobile, o título redundante “Página 1” acima da imagem foi removido visualmente; a toolbar continua indicando a página. Toolbar medida em **49 px**, com controles de pelo menos 44 px e indicação de zoom/página em uma linha. Fit-width móvel preservado.

## 4. Aba Transcrição e enunciado

Somente a aba Transcrição mostra o caption compacto, por exemplo `Transcrição automática · Mathpix · revisão 1`. Provider completo e versão permanecem no histórico/detalhes. Texto transcrito não foi modificado.

O enunciado móvel recolhido usa aproximadamente três linhas, movendo o limite antes de uma fórmula que atravessaria o corte. Expandir mostra o mesmo conteúdo completo; não há nova renderização nem alteração da matemática. Desktop mantém o tamanho anterior.

## 5. Página única no desktop

Mantida a estratégia do WORKSPACE-01D: largura efetiva × razão natural determina a altura da superfície; o quadro cresce para acomodar a página inteira. Nenhum novo fit que reduza a escala.

Em 1440×900, a imagem permaneceu **801×1068 px** antes e depois. Viewer com `clientHeight = scrollHeight = 1068`, sem rolagem vertical interna. Grid 60/40 e análise lateral preservados. Zoom, rotação, páginas e aba Comparar mantêm os controles existentes.

“Inteira” significa integralmente contida no quadro. A folha larga pode ultrapassar a altura da janela e ser percorrida pela rolagem geral, conforme permitido na solicitação.

## 6. Barras inferiores e final da folha

A altura real da barra de decisão é observada pelo `ResizeObserver` existente e alimenta `--decision-clearance`. No Original desktop, o conteúdo reserva padding-bottom equivalente (60 px no caso verificado). Alterações de altura, inclusive quebra de linha, atualizam a reserva.

Ao final da rolagem desktop: imagem termina em **711,8 px**, barra começa em **831,8 px**; viewer mantém scrollTop zero. A folha termina inteiramente acima da barra.

No mobile, o padding inferior considera altura medida da action bar, bottom nav, safe area e margem. A action bar de 65 px termina exatamente onde começa a navegação de 74 px. O final da folha ficou acessível acima da action bar após rolar a página; navegação e identidade preservadas.

## 7. Screenshots e inspeção

Comparação com o estado anterior WORKSPACE-02, capturado antes da implementação. Inspeção no navegador integrado no Mac; dimensões indicam viewport CSS, e a captura nativa pode excluir a barra de rolagem. Não houve teste em iPhone físico.

- [430×932 — depois](/private/tmp/confia-workspace03/workspace-430x932.jpg)
- [430×932 — antes](/private/tmp/confia-workspace03/before-430x932.jpg)
- [390×844 — depois](/private/tmp/confia-workspace03/workspace-390x844.jpg)
- [390×844 — antes](/private/tmp/confia-workspace03/before-390x844.jpg)
- [1440×900](/private/tmp/confia-workspace03/workspace-1440x900.jpg)
- [Desktop — página completa](/private/tmp/confia-workspace03/workspace-full-page.jpg)
- [Desktop — fim da folha](/private/tmp/confia-workspace03/desktop-end-of-sheet.jpg)
- [Mobile — fim da folha](/private/tmp/confia-workspace03/mobile-end-of-sheet.jpg)
- [Transcrição](/private/tmp/confia-workspace03/transcription-390x844.jpg)
- [Geometria antes/depois](/private/tmp/confia-workspace03/geometry.json)

Sem overflow horizontal global nas três dimensões. Verificados troca de abas, expansão/recolhimento do enunciado, proporção da imagem, barras e rolagem. Console sem warnings/errors. Nenhuma decisão enviada.

## 8. Testes e arquivos

- `node --test tests/js/test_*.cjs`: **421 passaram, 0 falhas, 0 ignorados**.
- `.venv/bin/python -m pytest -q tests/test_tme_photo_errors.py tests/test_tme_pilot.py tests/test_tme_audit_view.py tests/test_capture_static.py`: **50 passaram**.
- Quatro testes novos: helper visual, metadata por aba com navegação/fit-width, limite compacto antes de fórmula e reserva dinâmica das barras.
- Testes anteriores mantêm cobertura da largura/proporção desktop, rotação, zoom, teclado e múltiplas páginas. Duas expectativas antigas foram atualizadas para o nome visual e caption compacto.

Arquivos desta tarefa:

- `app/confia_lean_auditor/static/tme/correction-workspace.js`
- `app/confia_lean_auditor/static/tme/correction-workspace.css`
- `app/confia_lean_auditor/static/tme/tme.js`
- `app/confia_lean_auditor/static/tme/index.html`
- `tests/js/test_correction_workspace.cjs`
- `tests/js/test_tme_workspace_01b.cjs`
- `tests/js/test_tme_workspace_03.cjs` (novo)
- Este relatório (novo).

Hashes comparados com o início da tarefa: alterações em arquivos existentes limitadas aos seis listados. Backend, OCR, Auditor, claims, rubricas, Lean, score policy, dados e decisões não foram alterados.

## 9. Git diff --check

Sem erros. Whitespace dos arquivos novos também verificado.

## 10. Git status --short

[Saída completa](/private/tmp/confia-workspace03/git-status-short.txt), incluindo mudanças preexistentes. Sem staging, commit ou push.
