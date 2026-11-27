# TME MAC-01 — Original amplo sem rolagem interna

23/10/2026 · branch `feat/tme-dual-input`.

## 1. Diagnóstico e limite da reprodução

No checkout recebido, o cálculo de altura intrínseca do WORKSPACE-01D já estava ativo: nas quatro resoluções desktop, `scrollHeight` e `clientHeight` eram iguais. Portanto, **não foi reproduzido corte vertical efetivo no caso real utilizado nesta rodada**. Não há evidência suficiente para atribuir a ocorrência relatada a cache ou a outro estado do viewer.

Foi identificada e removida a configuração residual que mantinha o Original como contêiner de rolagem: `overflow:auto`, inclusive em escala normal. A captura anterior foi preservada antes de qualquer edição.

## 2. Regra responsável e correção

Em `correction-workspace.css`, dentro de `@media (min-width: 1100px)`, a regra `.original-document[data-layout="full-page"]` mantinha `height:auto; max-height:none; overflow:auto`. O ajuste acrescenta `overflow:visible` em ambos os eixos quando `data-scroll-mode="document"`. Usar somente `overflow-y:visible` com `overflow-x:auto` faria o eixo vertical voltar a `auto` no estilo computado.

Em `layoutOriginal`, o estado `document` é aplicado somente ao Original desktop, em zoom até 100%, cuja largura efetiva cabe no quadro. Zoom manual ampliado, comparação e breakpoints menores mantêm `viewer`. Somente a página ativa determina esse estado; páginas ocultas não o sobrescrevem. As versões dos dois assets alterados foram atualizadas no HTML.

## 3. Estratégia de altura

Preservado o cálculo existente: largura disponível menos a margem técnica de 4 px; altura igual à largura renderizada multiplicada por `naturalHeight / naturalWidth`. A superfície contém as dimensões transformadas da imagem e o viewer cresce com o conteúdo, sem altura máxima desktop. Não foi introduzido ajuste pela altura da janela nem novo botão.

A folha está inteira no quadro, podendo ultrapassar a viewport. Nesse caso, o avaliador percorre a página geral. A divisão horizontal continua em 60/40. Enunciado, header, toolbar e análise mantêm o layout anterior; “Originais e histórico” permanece recolhido.

## 4. Largura antes/depois

Mesma imagem real de 3024×4032 px, mesmo caso e mesma divisão de colunas. Medidas em pixels CSS:

| Viewport | Largura antes | Largura depois | Altura depois | Overflow vertical depois |
| --- | ---: | ---: | ---: | --- |
| 1366×768 | 757 | 757 | 1009,33 | visible |
| 1440×900 | 801 | 801 | 1068 | visible |
| 1728×1117 | 906 | 906 | 1208 | visible |
| 1920×1080 | 906 | 906 | 1208 | visible |

Nenhuma redução da imagem. Coordenadas e dimensões da imagem também permaneceram idênticas ao baseline.

## 5. Página única e barra de decisão

Nas quatro resoluções: imagem contida integralmente no viewer, `scrollHeight = clientHeight`, `scrollTop = 0`, `overflow-x/y:visible`, sem overflow horizontal global. Rolar sobre o manuscrito moveu o documento geral.

No fim da rolagem, o manuscrito terminou 120 px acima do início da barra de decisão. Em 1440×900: final da imagem em 711,81 px; barra em 831,81 px; scroll da página em 725 px; scroll do viewer em zero. Reserva inferior existente preservada.

## 6. Múltiplas páginas

Teste automatizado com duas imagens de proporções diferentes: anterior/próxima mantêm uma única página visível, usam as dimensões próprias de cada imagem e não geram novas requisições. Página oculta não altera a política de overflow da página atual. Não foi criado ou alterado um caso real para testar duas páginas no navegador.

## 7. Rotação, zoom e expansão

No navegador em 1440×900: 90°/270° produziram 801×600,75 px; 0°/180° produziram 801×1068 px. Em todos os ângulos, a folha permaneceu contida e sem rolagem interna normal.

Zoom 125% manteve a ampliação e o contêiner de navegação manual; voltar a “Ajustar à página” restaurou 801×1068 px e `overflow:visible`. Expandir solução produziu 1359×1812 px, sem corte; restaurar análise voltou a 801×1068 px. Testes automatizados também cobrem troca de abas, fit-width e navegação.

## 8. Desktop

Inspeção visual e geométrica realizada no navegador integrado no Mac: **1366×768, 1440×900, 1728×1117 e 1920×1080 aprovados**. A resolução 1728×1117 foi simulada como viewport; não se assume que seja a resolução física do monitor do usuário. Console sem warnings/errors na sessão inspecionada.

## 9. Regressão tablet

**768×1024 e 1024×768 preservados**. Comparação automatizada de todos os campos das medições antes/depois resultou em igualdade: imagem, viewer, limites de altura, overflow, header, enunciado, barra e largura da página. O scroll interno aprovado do tablet continua presente. Nenhuma regra CSS abaixo de 1100 px foi alterada.

## 10. Regressão mobile

**430×932 preservado**, com todas as medições antes/depois iguais. Imagem em 342×456 px, início em y=395,125 px. Toolbar, bottom nav e barra de ação mantidas. Teste por viewport no Mac; não houve teste em aparelho físico.

## 11. Screenshots e testes

Capturas não versionadas, em `/private/tmp/confia-mac01`. As capturas nativas podem excluir a largura da barra de rolagem; nomes indicam viewport CSS.

| Viewport | Antes | Depois | Fim da folha |
| --- | --- | --- | --- |
| 1366×768 | [antes](/private/tmp/confia-mac01/before-1366x768.jpg) | [depois](/private/tmp/confia-mac01/after-1366x768.jpg) | [fim](/private/tmp/confia-mac01/bottom-1366x768.jpg) |
| 1440×900 | [antes](/private/tmp/confia-mac01/before-1440x900.jpg) | [depois](/private/tmp/confia-mac01/after-1440x900.jpg) | [fim](/private/tmp/confia-mac01/bottom-1440x900.jpg) |
| 1728×1117 | [antes](/private/tmp/confia-mac01/before-1728x1117.jpg) | [depois](/private/tmp/confia-mac01/after-1728x1117.jpg) | [fim](/private/tmp/confia-mac01/bottom-1728x1117.jpg) |
| 1920×1080 | [antes](/private/tmp/confia-mac01/before-1920x1080.jpg) | [depois](/private/tmp/confia-mac01/after-1920x1080.jpg) | [fim](/private/tmp/confia-mac01/bottom-1920x1080.jpg) |
| 768×1024 | [antes](/private/tmp/confia-mac01/before-768x1024.jpg) | [depois](/private/tmp/confia-mac01/after-768x1024.jpg) | — |
| 1024×768 | [antes](/private/tmp/confia-mac01/before-1024x768.jpg) | [depois](/private/tmp/confia-mac01/after-1024x768.jpg) | — |
| 430×932 | [antes](/private/tmp/confia-mac01/before-430x932.jpg) | [depois](/private/tmp/confia-mac01/after-430x932.jpg) | — |

[Página completa](/private/tmp/confia-mac01/fullpage-1440x900.png): captura feita ao final da rolagem, portanto os elementos sticky aparecem na posição correspondente a esse estado. Para avaliar a composição inicial, usar as capturas de viewport acima.

Evidências: [geometria antes](/private/tmp/confia-mac01/geometry-before.json), [geometria depois](/private/tmp/confia-mac01/geometry-after.json), [interações e fim da folha](/private/tmp/confia-mac01/interactions.json).

- `node --test tests/js/test_*.cjs`: **425 passaram, 0 falhas, 0 ignorados**, incluindo quatro novos testes MAC-01. [Log](/private/tmp/confia-mac01/js-tests.log).
- `.venv/bin/python -m pytest -q tests/test_tme_photo_errors.py tests/test_tme_pilot.py tests/test_tme_audit_view.py tests/test_capture_static.py`: **50 passaram**. [Log](/private/tmp/confia-mac01/python-tests.log).
- Verificações das medições: sete viewports; nas quatro desktop, largura preservada, imagem contida, overflow visible e ausência de scroll interno; nas três restantes, igualdade completa com baseline.

Arquivos desta tarefa:

- `app/confia_lean_auditor/static/tme/correction-workspace.js`
- `app/confia_lean_auditor/static/tme/correction-workspace.css`
- `app/confia_lean_auditor/static/tme/index.html`
- `tests/js/test_tme_mac_01.cjs` (novo)
- `docs/TME_MAC_01.md` (novo)

Hashes comparados com o início da tarefa para confirmar o escopo. Backend, modelos, OCR, Auditor, Lean, claims, rubricas e score policy não foram modificados nesta rodada. Nenhuma decisão enviada.

## 12. Git diff --check

**Sem erros**. Whitespace dos arquivos novos também verificado.

## 13. Git status --short

[Saída completa](/private/tmp/confia-mac01/git-status-short.txt), incluindo as alterações preexistentes na branch. Nenhum staging, commit ou push realizado.
