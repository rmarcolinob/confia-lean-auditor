# CONFIA-TME-WORKSPACE-01A — enunciado matemático

## Origem e representação

1. **Endpoint:** `GET /tme/problems`, protegido pela autorização TME existente.
2. **Campo:** `statement`. `tme/router.py::problems` chama `core/problem_catalog.py::list_problem_catalog`; `_problem_metadata` lê `problems/{problem_id}/problem.json`. Não é uma cópia de banco. O catálogo expõe `id`, `problem_id`, `title`, `statement`, `phase` e exemplos; não há `statement_latex` nesse contrato.
3. **Representação estruturada já existente:** `app/confia_lean_auditor/static/problem-presentations/registry.json`. Cada registro contém `problem_id`, `source_statement`, `display_version` e `segments` de texto/matemática. O mesmo registro já é usado pelo workspace de resolução e pelo caderno digital. Ele tem prioridade quando seu texto fonte coincide exatamente com `statement`; divergência mantém o texto recebido, sem interpretar silenciosamente uma versão desatualizada.

## Helper e KaTeX

4. Reutilizado `ConfiaProblemMath` de `static/capture/problem-math.js`, com a entrada genérica `renderContent(element, source, presentation)`. Ela mantém a renderização segura existente e oferece fallback sem mensagem técnica nem tooltip vermelho. A API anterior `render` permanece disponível e seus testes anteriores continuam passando.
5. KaTeX **0.18.9 local**, CSS já carregado e `contrib/auto-render.min.js` local. Sem CDN, nova biblioteca ou `innerHTML` de conteúdo arbitrário. Texto entra por `textContent`/text nodes; matemática usa `katex.render` com `trust:false`, limites de expansão/tamanho e MathML acessível. Conteúdo delimitado aceita inline/display; segmentos estruturados podem optar por `display:true`. O registro é buscado uma vez e reutilizado; falha de carregamento não bloqueia a correção.

## ITA2025F2Q3

6. A comparação confirmou que `source_statement` do registro é idêntico ao `statement` de `problems/ITA2025F2Q3/problem.json`. São seis segmentos matemáticos: α, β, intervalo com π/2 e 3π/2, as duas igualdades com 1/4 e 3/4, e a expressão final. O registro usa `\operatorname{sen}` e `\cos`: essa convenção foi preservada. Não houve troca global de palavras nem reconstrução da matemática a partir do prompt. Os dois assets permanecem byte a byte inalterados.

## Compacto, expandido e responsividade

7. O mesmo subtree renderizado é mantido ao expandir/recolher. O compacto usa altura limitada e fade, sem line-clamp/ellipsis. A medição desloca o limite para antes de uma fórmula que cruzaria o corte. ResizeObserver recalcula no resize; a expansão preserva a renderização. Fórmulas largas têm rolagem própria, sem reduzir a fonte; display tem margens compactas.

Validação visual em Chromium/IAB: **390×844, 430×932, 1440×900**, com capturas recolhidas e expandidas. Em cada largura: seis expressões KaTeX, zero erros KaTeX, largura da página ≤ viewport. Gregas, frações, intervalo e sen confirmados visualmente; nenhum LaTeX bruto visível. Anotações TeX não visuais do MathML são preservadas para acessibilidade. Safari iOS não foi testado em dispositivo físico.

## Testes

8. `node --test tests/js/test_*.cjs`: **400 aprovados, 0 falhas, 0 ignorados**, incluindo oito testes novos.

   `.venv/bin/python -m pytest -q tests/test_capture_static.py tests/test_tme_photo_errors.py tests/test_tme_pilot.py`: **47 aprovados, 0 falhas**.

Cobertura: texto literal/HTML, inline/display, frações, gregas, intervalo, trigonometria, soma, conteúdo misto, fallback, origem canônica F2Q3, registro ausente/cache, expansão sem rerender e corte compacto antes de fração. Matriz de overflow verificada no navegador e registrada em JSON.

## Arquivos alterados nesta tarefa

9. Produção:

- `app/confia_lean_auditor/static/capture/problem-math.js`
- `app/confia_lean_auditor/static/tme/correction-workspace.js`
- `app/confia_lean_auditor/static/tme/correction-workspace.css`
- `app/confia_lean_auditor/static/tme/tme.js`
- `app/confia_lean_auditor/static/tme/index.html`

Testes/documentação:

- `tests/js/test_problem_math.cjs`
- `tests/js/test_tme_workspace_01.cjs`
- `tests/js/tme-dom.cjs`
- `docs/TME_WORKSPACE_01A.md`

A lista foi conferida contra hashes registrados no início desta tarefa. Nenhum arquivo Python, problema canônico, registro matemático, Auditor, rubrica, OCR, claim ou Lean foi alterado nesta tarefa.

## Git e evidências

10. `git diff --check`: **exit 0, sem saída**. Arquivos novos/alterados também verificados quanto a whitespace final.
11. `git status --short`: saída integral em `/private/tmp/confia-workspace01a/git-status-short.txt`. O checkout mantém as alterações anteriores; não houve staging, commit ou push.

Evidências locais (não versionadas): `/private/tmp/confia-workspace01a/`, com logs JS/Python, `responsive-checks.json`, `changed-files.txt` e seis screenshots `statement-{largura}x{altura}-{compact|expanded}.jpg`.

## Demais áreas, para refinamento posterior

- **Critérios:** usam `ConfiaRecognitionView.renderMathText`, mas descrições em texto puro como `cos(beta)-sen(beta)=1/2` continuam literais; confirmado no caso real.
- **Claims e evidências:** usam o renderer existente para trechos explicitamente delimitados; matemática recebida como texto puro permanece literal. Não recebem a curadoria do enunciado.
- **Transcrição:** delimitadores e segmentos explicitamente matemáticos são renderizados pelo helper existente; segmentos comuns sem delimitação permanecem texto. Nenhuma transcrição ou revisão foi alterada.
- **Feedback/justificativa:** campos de entrada continuam textuais. Não houve migração em massa dos demais campos.
