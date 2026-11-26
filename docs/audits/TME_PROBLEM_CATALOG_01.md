# TME_PROBLEM_CATALOG_01

## Resultado e baseline

Catálogo oficial completo de TME2026P1–P5 disponibilizado no endpoint e no painel já existentes. Alteração restrita a conteúdo, leitura/validação de catálogo e apresentação. Baseline inicial limpo, branch `feat/tme-dual-input`, SHA `c8475ede0c4aa8a24559fbe742309c32c71489b7`. Data: 2026-11-01 (America/Fortaleza).

## Diagnóstico do carregamento anterior

- `tme.js:newCase` busca `GET /tme/problems` para preencher o seletor; `openCase` reutiliza esse endpoint para o workspace. `problem_id`, título e texto vêm dessa resposta.
- `tme/router.py:problems` já acrescentava os cinco IDs de `PUBLIC_PROBLEMS` ao catálogo ITA. Portanto, P2–P5 não estavam ausentes do registry matemático nem da lista de IDs; faltava conteúdo: todos os cinco recebiam o mesmo placeholder para consultar a prova.
- O máximo era obtido por `pauta_for(key).max_score` (20). O registry matemático permanece em `tme/registry.py`; P1 mantém o alias público TME2026P1 → TME2_P1_PILOT.
- `core/problem_catalog.py` carregava enunciados ITA de `problems/<id>/problem.json`. `static/problem-presentations/registry.json` fornece apresentações matemáticas curadas para os dez ITA; não contém textos TME.
- `correction-workspace.js:ProblemStatement` renderizava apenas a string, usando o renderer matemático existente, e mantinha o comportamento expandir/recolher. Não existia suporte de apresentação a figuras do enunciado nesse componente.
- `tme/store.py` já aceitava os cinco IDs. Nenhuma alteração no store, na identidade do caso ou na lógica de correção foi necessária.

## Fonte normativa e fidelidade

Fonte local lida integralmente nas páginas pertinentes, com extração textual e inspeção visual:
`/Users/LinMarcolino/Library/CloudStorage/Dropbox/Segunda Fase TME² - Gabarito com pauta.pdf`.

SHA256: `a2660f1c0761738a8b9232dc179feaea9538efb45102e1b2a9b991a3dd2ac384`.

| Problema | Páginas do PDF (1-based) | Itens | Máximo |
| --- | --- | --- | --- |
| P1 | 2 | a–d | 20 |
| P2 | 4–5 | a–c | 20 |
| P3 | 7–8 | a–c | 20 |
| P4 | 10 | a–c | 20 |
| P5 | 13–14 | a–d | 20 |

O documento intercala perguntas e respostas: somente as introduções, exemplos dados no enunciado, transições e perguntas foram transcritos. Foram excluídos resolução, tabelas de respostas, pontuações por item e pauta. A barra de abc e a notação matemática foram preservadas em delimitadores TeX reconhecidos pelo KaTeX já embarcado; as quebras de linha do PDF foram normalizadas. Preservados também o exemplo 804−408=396 de P1, a regra de distinção dos preenchimentos de P2, a atualização dos compartimentos de P3 e a passagem ao número 2026 antes do item (c) de P5. Nenhum texto foi reconstruído de fixtures/extractors.

O PDF completo não é servido pela aplicação: contém respostas. O carregamento em runtime e os testes não dependem da cópia local do PDF; sua proveniência está nos JSONs versionáveis.

## Figuras oficiais

PNG recortados diretamente de renderizações locais do PDF com Poppler, altura de página de 1600 px. Sem redesenho, geração por IA ou reconstrução a partir de regras do motor. Coordenadas de recorte `(left, top, right, bottom)` registradas em cada JSON, juntamente com página, dimensões e SHA256 do asset.

| Asset | Página | Recorte |
| --- | --- | --- |
| TME2026P2/circulos.png | 4 | 405, 178, 725, 495 |
| TME2026P2/item-a.png | 4 | 55, 711, 371, 1028 |
| TME2026P3/compartimentos.png | 7 | 440, 182, 690, 503 |
| TME2026P4/triangulo.png | 10 | 398, 220, 730, 531 |

Inspeção visual confirmou: círculos A–H e X completos; segunda figura com centro 5 e extremidades vazias; seis compartimentos e todas as bolas/cores; triângulo com A/B/C/P/Q/R, x e regiões sombreadas. Nenhum recorte contém solução. Textos alternativos descrevem o conteúdo visual sem solucionar os itens. A imagem é mantida junto ao trecho correspondente, inclusive a figura específica de P2(a), e redimensionada sem deformação em telas estreitas.

## Implementação e contrato

- Reutilizado `core/problem_catalog.py` e o padrão `problems/<id>/problem.json`; não criado endpoint paralelo ou segundo registro manual de problemas suportados.
- `list_tme_problem_catalog` lê arquivos de conteúdo usando modelos fechados. Blocos de texto e figura preservam a ordem da prova. O campo `statement` completo é derivado dos blocos, sem duplicação de texto no armazenamento.
- `GET /tme/problems` mantém os dez objetos ITA anteriores e substitui os cinco placeholders TME pelos conteúdos. O subconjunto TME é exatamente P1–P5. `GET /problems` continua exclusivamente com os dez ITA e seus exemplos.
- Registry público, registry do auditor e diretórios de conteúdo devem coincidir nas duas direções. Divergências interrompem o carregamento, em vez de ocultar um problema ou exibir conteúdo de outro ID.
- Validações adicionais: ID interno da pauta (incluindo alias P1), caminho da pauta derivado do registry, máximo igual à pauta, itens na mesma ordem, textos/títulos não vazios, referências de figuras únicas e usadas, arquivos locais existentes e com hash correto. Nenhuma lógica de crédito é duplicada no catálogo.
- O painel existente usa `ConfiaProblemMath.renderContent` para cada bloco textual, e cria imagens com APIs DOM. Não injeta HTML. Somente URLs de PNG no diretório local dos problemas TME são aceitas pelo componente.
- Mantidos seleção, navegação, recebimento da transcrição, expansão/recolhimento do enunciado e disposição do workspace. Acrescentadas apenas apresentação de parágrafos/figuras e atualização de versão de cache dos dois assets alterados.

## Validação

Resultados finais: **740 testes Python TME/pautas/assets aprovados + 5 testes de compatibilidade do catálogo ITA aprovados = 745 testes Python distintos; 174 testes JavaScript aprovados; zero falhas e zero regressões detectadas no escopo executado.** São 22 testes Python novos e 9 testes JavaScript novos. Os números não somam repetições da execução focada inicial.

Logs e resumo: `artifacts/evaluations/tme_problem_catalog_01/{pytest.log,ita_catalog.log,node.log,validation_summary.json}`. Conferência independente dos arquivos protegidos e figuras: `protected_paths_check.json` e `figure_checks.json`.

Testes novos:
- `tests/test_tme_problem_catalog.py`: 22 testes — catálogo exato, conteúdo e contexto, referência normativa, ausência de trechos de solução, APIs/casos e assets dos cinco problemas, preservação ITA, rejeição de registros ausentes/extras, IDs/pautas/itens incompatíveis, textos vazios e figuras inválidas.
- `tests/js/test_tme_problem_catalog.cjs`: 9 testes — cinco opções no seletor, cinco painéis completos com figuras e expandir/recolher, comportamento legado ITA, rejeição de imagem externa e parsing real das fórmulas pelo KaTeX local.

Comandos de regressão:
```sh
.venv/bin/python -m pytest -q tests/test_tme*.py tests/test_pauta*.py tests/test_problem_assets*.py tests/test_problem_router_coverage.py
node --test tests/js/test_tme*.cjs tests/js/test_problem_math.cjs
.venv/bin/python -m pytest -q tests/test_static_ui.py tests/test_capture_static.py -k 'problems_endpoint or f2q1_catalog or problem_example_endpoint or shared_curated_registry'
```

A suíte Python inclui os cinco problemas, PautaEngine e integração aceita. A comparação independente de 204 arquivos protegidos com os blobs do HEAD encontrou zero alterações (ver `protected_paths_check.json`). Não alterados PautaEngine, pautas P1–P5, FactResult, produtores, bridges, checkers, Lean, scoring, secondary, adaptador de auditoria aceita ou conteúdo ITA. Nenhum benchmark grande, OCR ou API externa foi executado.

## Limitações e observações

- A validação visual abrangeu o documento e todos os recortes, e a UI foi testada por DOM e KaTeX. Não foi concluída captura de tela de navegador real: o Chromium gerenciado não estava instalado e o Chrome local não iniciou no sandbox. Não foram instalados navegadores nem acessadas APIs externas para contornar essa limitação.
- A garantia de ausência de regressão se limita às verificações e testes registrados; não é uma nova estimativa de acurácia do corretor.
- O fingerprint amplo de `audit_context` inclui todos os módulos de `tme`, inclusive o router. Assim, a alteração de catalogação no router muda o identificador de versão em novas auditorias, sem mudar suas regras matemáticas ou modificar resultados históricos. O mecanismo de fingerprint permanece intocado.

## Arquivos adicionados/modificados

- `app/confia_lean_auditor/core/problem_catalog.py`
- `app/confia_lean_auditor/static/tme/correction-workspace.css`
- `app/confia_lean_auditor/static/tme/correction-workspace.js`
- `app/confia_lean_auditor/static/tme/index.html`
- `app/confia_lean_auditor/tme/router.py`
- `app/confia_lean_auditor/static/problem-assets/TME2026P2/circulos.png`
- `app/confia_lean_auditor/static/problem-assets/TME2026P2/item-a.png`
- `app/confia_lean_auditor/static/problem-assets/TME2026P3/compartimentos.png`
- `app/confia_lean_auditor/static/problem-assets/TME2026P4/triangulo.png`
- `problems/TME2026P1/problem.json`
- `problems/TME2026P2/problem.json`
- `problems/TME2026P3/problem.json`
- `problems/TME2026P4/problem.json`
- `problems/TME2026P5/problem.json`
- `tests/js/test_tme_problem_catalog.cjs`
- `tests/test_tme_problem_catalog.py`
- `docs/audits/TME_PROBLEM_CATALOG_01.md` (este relatório).

## Conferência final do Git

`git diff --check`: OK, sem erros de whitespace. Índice vazio (`git diff --cached --quiet`), nenhuma operação de staging, commit ou push. Apenas os 17 arquivos listados nesta tarefa adicionados/modificados.

`git status --short --untracked-files=all`:
```text
 M app/confia_lean_auditor/core/problem_catalog.py
 M app/confia_lean_auditor/static/tme/correction-workspace.css
 M app/confia_lean_auditor/static/tme/correction-workspace.js
 M app/confia_lean_auditor/static/tme/index.html
 M app/confia_lean_auditor/tme/router.py
?? app/confia_lean_auditor/static/problem-assets/TME2026P2/circulos.png
?? app/confia_lean_auditor/static/problem-assets/TME2026P2/item-a.png
?? app/confia_lean_auditor/static/problem-assets/TME2026P3/compartimentos.png
?? app/confia_lean_auditor/static/problem-assets/TME2026P4/triangulo.png
?? docs/audits/TME_PROBLEM_CATALOG_01.md
?? problems/TME2026P1/problem.json
?? problems/TME2026P2/problem.json
?? problems/TME2026P3/problem.json
?? problems/TME2026P4/problem.json
?? problems/TME2026P5/problem.json
?? tests/js/test_tme_problem_catalog.cjs
?? tests/test_tme_problem_catalog.py
```

Os artifacts de validação são locais e ignorados pelo Git; os cinco JSONs de conteúdo, quatro PNGs, testes e relatório estão em diretórios versionáveis. Nenhuma mudança em `.gitignore`.
