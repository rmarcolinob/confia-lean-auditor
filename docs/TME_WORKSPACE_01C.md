# CONFIA-TME-WORKSPACE-01C — página inteira por padrão

## 1. Causa

O cálculo de ajuste à página já existia, mas o selector e o layout começavam em `width`. A imagem era ampliada até a largura do painel, ultrapassando sua altura. O zoom manual também não possuía um estado explícito separado do ajuste automático.

## 2. Fit-page

`layoutOriginal` em `static/tme/correction-workspace.js` limita a escala pelas duas dimensões, equivalente a `min(larguraDisponível/larguraNatural, alturaDisponível/alturaNatural)`. A rotação troca as dimensões efetivas. São reservados 4px de respiro; aspect ratio e bytes do original são preservados.

A superfície é centralizada horizontalmente e recebe respiro vertical calculado quando sobra altura. O desktop deixa de reservar uma faixa de scrollbar vazia. O overflow permanece automático: não existe rolagem quando a imagem cabe, mas o zoom manual pode torná-la necessária. Não há recorte nem `overflow:hidden` usado para esconder parte da folha.

## 3. Default por breakpoint e estados

- **≥1100px:** `page` — Ajustar à página.
- **Mobile/tablet:** `width` e dimensionamento anterior, preservando a leitura móvel.
- O default acompanha o breakpoint enquanto o avaliador não escolheu explicitamente um modo.
- Zoom +/− entra em **custom**, exibido como “Zoom manual” no menu. A base do enquadramento é preservada durante o zoom manual, em vez de aplicar continuamente um ajuste automático.
- Selecionar Ajustar à página ou Ajustar à largura retorna a 100% do respectivo enquadramento e zera o deslocamento da rolagem.
- A troca de página preserva o modo escolhido e recalcula o enquadramento pelas dimensões daquela imagem.

## 4. Rotação

No desktop, cada rotação retorna ao fit-page, recalcula as dimensões efetivas e desfaz zoom/deslocamento que poderiam cortar a folha. As quatro orientações são cobertas por teste. No mobile, a rotação mantém o comportamento anterior.

## 5. Página inteira no desktop/Mac

**Sim, no navegador testado.** Na resolução 1728×1117, o original real retrato de 3024×4032 ficou inteiro, centralizado e sem scroll do manuscrito. A leitura detalhada continua disponível por Ajustar à largura ou zoom manual.

| Viewport | Modo inicial | Imagem renderizada | Scroll vertical do original |
| --- | --- | --- | --- |
| 1366×768 | Página | 154,5×206px | 0px |
| 1440×900 | Página | 253,5×338px | 0px |
| 1728×1117 | Página | 416,25×555px | 0px |
| 1920×1080 | Página | 388,5×518px | 0px |
| 430×932 | Largura | 338×450,7px | Fluxo móvel preservado |

Todas as imagens desktop ficaram dentro dos quatro limites do viewer, com `scrollHeight == clientHeight` e `scrollWidth == clientWidth`. Não houve overflow horizontal da página. Validação em IAB/Chromium no ambiente macOS; Safari não foi certificado.

## 6. Testes

- `node --test tests/js/test_*.cjs`: **412 aprovados, 0 falhas, 0 ignorados**.
- `.venv/bin/python -m pytest -q tests/test_tme_photo_errors.py tests/test_tme_pilot.py`: **35 aprovados, 0 falhas**.
- Seis testes novos em `tests/js/test_tme_workspace_01c.cjs`: defaults, limite por largura/altura e centralização, zoom custom, retorno ao fit, quatro rotações, múltiplas páginas e mudança de breakpoint.
- Testes anteriores do WORKSPACE-01B ajustados ao novo requisito de default e rotação; preservação de estado continua coberta.

## 7. Inspeção visual e escopo

Capturas nas cinco resoluções acima e rotação em 1440×900, em `/private/tmp/confia-workspace01c/`. A alternância para largura produziu rolagem como esperado; o retorno a página eliminou-a. Dados observados em `fit-checks.json` e `interaction-checks.json`.

Arquivos alterados nesta tarefa:

- `app/confia_lean_auditor/static/tme/correction-workspace.js`
- `app/confia_lean_auditor/static/tme/tme.js`
- `app/confia_lean_auditor/static/tme/correction-workspace.css`
- `app/confia_lean_auditor/static/tme/index.html`
- `tests/js/test_tme_workspace_01b.cjs`
- `tests/js/test_tme_workspace_01c.cjs`
- `docs/TME_WORKSPACE_01C.md`

Sem alteração de backend, Auditor, OCR, conteúdo da transcrição, regra de decisão, enunciado ou KaTeX. Hashes comparados ao início desta tarefa.

## 8. git diff --check

**Exit 0**, sem saída. Arquivos novos/alterados também verificados contra whitespace final.

## 9. git status --short

Saída integral em `/private/tmp/confia-workspace01c/git-status-short.txt`. Alterações de tarefas anteriores preservadas. Sem staging, commit ou push.
