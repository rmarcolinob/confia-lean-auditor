# TME_FIGURES_01 — figuras oficiais no caderno TME

## Causa raiz confirmada

Baseline inicial limpo: `feat/tme-dual-input`, commit `b71d789ef7734d444a2e0255ae68bf79c0321d3f`.

Reprodução no navegador real em `http://127.0.0.1:8000/tme`, abrindo um caso digital existente de P2. O iframe do caderno exibia todas as perguntas, mas nenhuma imagem. O painel de correção e o caderno são consumidores diferentes: `static/tme/correction-workspace.js` já processava `statement_blocks` e `figures`; `static/capture/tablet.js:renderProblem` apenas atribuía `problem.statement` a `textContent` e renderizava a matemática dessa string. Os testes de DOM anteriores cobriam o painel de correção, não esse consumidor.

Não havia erro de caminho, ausência de arquivo ou 404. As quatro URLs já retornavam HTTP 200 com MIME `image/png`. A primeira correção de renderização também revelou que o limite anterior do painel de texto (`min(25vh, 200px)`) era menor que as figuras completas.

## Filesystem e URLs públicas

Montagem real: `main.py` usa `app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')`. `STATIC_DIR` aponta para `app/confia_lean_auditor/static`.

| Arquivo sob STATIC_DIR | URL pública (antes e depois) |
| --- | --- |
| `problem-assets/TME2026P2/circulos.png` | `/static/problem-assets/TME2026P2/circulos.png` |
| `problem-assets/TME2026P2/item-a.png` | `/static/problem-assets/TME2026P2/item-a.png` |
| `problem-assets/TME2026P3/compartimentos.png` | `/static/problem-assets/TME2026P3/compartimentos.png` |
| `problem-assets/TME2026P4/triangulo.png` | `/static/problem-assets/TME2026P4/triangulo.png` |

Os caminhos não precisaram ser corrigidos ou movidos. Os assets versionados são recortes oficiais contendo somente as figuras; não foram alterados. O catálogo continua usando `figures[].src` e `statement_blocks[].figure_id`. Nenhum catálogo ou endpoint adicional foi criado. Nenhum caminho `/Users/...`, `file://` ou diretório Python é enviado como URL de imagem.

## Correção restrita à apresentação

- O caderno usa os blocos ordenados já declarados no catálogo para TME2026P1–P5 quando existem figuras. Os parágrafos passam pelo renderer matemático existente e as imagens entram na posição correspondente ao enunciado.
- As URLs são atribuídas diretamente a `img.src`, aceitando apenas PNGs públicos do diretório do próprio problema. Preservados `alt`, dimensões e proporção. Rejeitados caminhos locais, URLs externas e referências a figuras de outro problema.
- P1/P5 não criam imagens vazias e continuam no caminho textual anterior. ITA mantém o renderer anterior, inclusive quando metadados extras forem fornecidos.
- O painel com figuras recebe uma marca de apresentação; somente esse painel TME aumenta o limite rolável para `min(65vh, 520px)`. As imagens usam largura automática, máximo de 100% da largura do painel e altura máxima proporcional ao viewport. Não há recorte do arquivo nem deformação; o texto longo e a segunda figura de P2 continuam acessíveis pela rolagem existente.
- Versões de cache atualizadas para `tme-figures-01` no HTML do caderno, evitando reutilização dos antigos JS/CSS.

## Arquivos modificados

- `app/confia_lean_auditor/static/capture/tablet.js`
- `app/confia_lean_auditor/static/capture/tablet.css`
- `app/confia_lean_auditor/static/capture/tablet.html`
- `tests/js/capture-dom.cjs` — suporte do harness ao renderer de conteúdo e identificação das tags DOM.
- `tests/js/test_tme_notebook_figures.cjs` — novo, nove testes.
- `tests/test_tme_problem_catalog.py` — dois cenários adicionais HTTP/HTTPS.
- `docs/audits/TME_FIGURES_01.md` — este relatório.

## Testes e evidências

```sh
.venv/bin/python -m pytest -q tests/test_tme_problem_catalog.py tests/test_tme_pilot.py tests/test_tme_navigation.py tests/test_capture_static.py
node --test tests/js/test_tme*.cjs tests/js/test_capture*.cjs tests/js/test_problem_math.cjs
```

Resultado final: **59 Python e 195 JavaScript aprovados; zero falhas**. Inclui os testes existentes de catálogo e UI TME, persistência do caderno, renderização matemática e compatibilidade ITA. Os novos testes exercitam o caderno real por DOM para todos os cinco IDs, ordenação dos blocos, figuras/alt/dimensões, expansão/recolhimento, ausência de imagens em P1/P5, caminhos inválidos e URLs de outra origem/problema.

Cada um dos quatro assets foi testado diretamente com FastAPI/TestClient em ambas as origens:
- `http://127.0.0.1:8000`;
- `https://figure-control.trycloudflare.com` (origem simulada pelo transporte ASGI, sem tráfego externo).

Todos retornaram `200 image/png`, com hash igual ao catálogo. Como os `src` começam com `/static/`, o navegador conserva esquema e host, inclusive HTTPS de um quick tunnel. Não há localhost hardcoded nem mixed content. Não foi aberto nem testado um túnel Cloudflare real: a confirmação HTTPS é de comportamento de mesma origem via ASGI.

Verificação adicional no navegador real local: as duas imagens de P2 carregaram (`complete=true`, dimensões naturais presentes), com erro de proporção zero, cabendo na largura e na altura rolável do painel nos viewports desktop 1280×900 e tablet 768×1024. A figura completa foi inspecionada visualmente no tablet. O viewport temporário foi restaurado. Não houve escrita de solução, envio, OCR ou auditoria do caso. P3/P4 foram verificados pelos testes de assets e de DOM; não foram criados casos operacionais para teste.

Evidência visual: `artifacts/evaluations/tme_figures_01/tablet_p2.png`.
Resumo e logs: `artifacts/evaluations/tme_figures_01/{validation_summary.json,pytest.log,node.log}`.

## Escopo e Git

Enunciados, catálogo, assets originais, pautas, PautaEngine, FactResult, audit_tme, producers, bridges, checkers, Lean, scoring, reconhecimento e código TME de auditoria permanecem inalterados, verificados por diff contra HEAD. Nenhum benchmark grande nem API externa foi executado.

`git diff --check`: OK. Sem staging, commit ou push.
