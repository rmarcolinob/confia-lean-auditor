# TME WORKSPACE-01D — Original largo e inteiro no quadro

Validação em 22/10/2026, branch `feat/tme-dual-input`.

## 1. Arquivos alterados nesta tarefa

- `app/confia_lean_auditor/static/tme/correction-workspace.css`: altura automática do Original desktop, análise sticky e compactação vertical.
- `app/confia_lean_auditor/static/tme/correction-workspace.js`: escala pela largura disponível no Original desktop, preservando proporção e rotação.
- `app/confia_lean_auditor/static/tme/tme.js`: modo de layout por aba e recálculo ao trocar de aba.
- `app/confia_lean_auditor/static/tme/index.html`: versão dos assets `workspace01d`.
- `tests/js/test_tme_workspace_01b.cjs`: manter os testes de fit com altura limitada no contexto Comparar.
- `tests/js/test_tme_workspace_01c.cjs`: atualizar expectativas para Original largo e preservar testes de fit limitado.
- `tests/js/test_tme_workspace_01d.cjs`: três testes novos de largura/altura, redimensionamento/rotação e troca de abas sem novas requisições.
- Este relatório.

O workspace já continha alterações anteriores. Comparação por hashes com o início desta tarefa confirmou alterações somente nos seis arquivos existentes listados acima; os outros dois são novos. Backend, OCR, Auditor e lógica de decisão não foram alterados nesta tarefa.

## 2. Ampliação da altura útil

Em desktop (a partir de 1100 px), o Original usa a largura útil do painel. A superfície recebe a altura proporcional da imagem, e o viewer cresce automaticamente para contê-la. A altura da janela não reduz mais a folha no Original. Comparar mantém o fit com altura limitada, e Transcrição mantém seu layout anterior.

Contexto, enunciado e barra de decisão foram compactados. Em 1440×900, o início da folha passou de aproximadamente 405 para 365 px; a barra de decisão tem 60 px. O enunciado continua renderizado em LaTeX, com botão para expansão.

## 3. Grid

Preservado em 60/40, com prioridade para a solução, divisor redimensionável e opção de expansão. A análise acompanha a rolagem geral com `sticky` e conserva sua rolagem própria.

## 4. Folha larga e inteira

Caso real inspecionado: `prova2`, ITA2025F2Q3, imagem retrato 3024×4032.

| Viewport CSS | Imagem no Original | Altura interna / scrollHeight | Resultado |
| --- | --- | --- | --- |
| 1280×800 | 705×940 px | 940 / 940 px | Sem scroll vertical interno |
| 1440×900 | 801×1068 px | 1068 / 1068 px | Sem scroll vertical interno |
| 1728×1117 | 906×1208 px | 1208 / 1208 px | Sem scroll vertical interno |
| 1920×1080 | 906×1208 px | 1208 / 1208 px | Sem scroll vertical interno |

As medidas podem variar alguns pixels quando a captura omite a barra de rolagem do navegador: em 1440, a captura também registrou 810×1080 px. O max-width existente limita o crescimento em telas maiores.

**A folha inteira está contida no quadro, sem corte. Ela pode ultrapassar a altura da janela: nesse caso, rola-se a página geral, conforme permitido no item 11 da solicitação.** Não se afirma que uma folha larga de 1068 px de altura apareça simultaneamente dentro de uma janela de 900 px.

Ao rolar sobre a folha em 1440×900, `window.scrollY` chegou a 661 px enquanto `original.scrollTop` permaneceu zero. O final da imagem ficou acima da barra de decisão. Zoom manual continua podendo exigir deslocamento horizontal; a altura acompanha a imagem ampliada.

## 5. Testes

- `node --test tests/js/test_*.cjs`: **415 passaram, 0 falharam, 0 ignorados**.
- `.venv/bin/python -m pytest -q tests/test_tme_photo_errors.py tests/test_tme_pilot.py`: **35 passaram**.
- Subconjunto 01B/01C/01D: **15 passaram** (incluído no total JS).
- A execução inicial com `tests/js/*.cjs` também passou: 420 entradas, incluindo cinco arquivos auxiliares. O total de testes reportado acima exclui esses auxiliares.

Logs em `/private/tmp/confia-workspace01d/`.

## 6. Inspeção visual e interação

Aprovado no navegador integrado no Mac, nas cinco dimensões acima/abaixo: 1280×800, 1440×900, 1728×1117, 1920×1080 e 430×932. Mobile conserva seu comportamento anterior, barra de ações e navegação inferior. Sem overflow horizontal da página nas medidas verificadas.

Verificados no navegador: Original → Comparar → Transcrição → Original, zoom, quatro rotações, expansão/restauração da análise e rolagem até o final da folha. Barra de decisão visível no desktop; nenhuma decisão foi enviada. Console sem warnings/errors na inspeção final. Testes cobrem também múltiplas páginas e persistência dos controles.

Artifacts locais, não adicionados ao Git:

- [1440×900 — topo](/private/tmp/confia-workspace01d/original-1440x900.jpg)
- [1440 — página completa](/private/tmp/confia-workspace01d/original-1440-full-page.jpg)
- [1440 — fim da folha](/private/tmp/confia-workspace01d/original-1440-bottom.jpg)
- [1728×1117](/private/tmp/confia-workspace01d/original-1728x1117.jpg)
- [1920×1080](/private/tmp/confia-workspace01d/original-1920x1080.jpg)
- [1280×800](/private/tmp/confia-workspace01d/original-1280x800.jpg)
- [430×932](/private/tmp/confia-workspace01d/original-430x932.jpg)
- [Geometria](/private/tmp/confia-workspace01d/geometry.json)
- [Rolagem geral](/private/tmp/confia-workspace01d/scroll-check.json)

As dimensões nomeiam a viewport CSS configurada. Algumas capturas nativas excluem a barra de rolagem. A captura de página completa foi feita ao final da rolagem; por isso a análise sticky aparece mais abaixo nela.

## 7. Git diff --check

`git diff --check`: sem erros. Verificação adicional de whitespace nos arquivos novos/alterados desta tarefa: sem erros.

## 8. Git status --short

Saída completa salva em [git-status-short.txt](/private/tmp/confia-workspace01d/git-status-short.txt), incluindo alterações preexistentes. Nenhum staging, commit ou push realizado.
