# TME WORKSPACE-02 — Refinamento visual

22/10/2026 · branch `feat/tme-dual-input`.

## 1. Tokens reutilizados

Paleta, superfícies, bordas, raios, sombras, espaçamento e escala tipográfica de `tme-theme.css`, já usados pela Home. Mesma fonte de sistema. Transição de 160 ms consolidada em `--confia-motion-fast` e consumida também pela Home. Nenhuma cor nova, framework, dependência ou biblioteca de ícones adicionada.

## 2. Elementos refinados

Metadados com separadores discretos; pills compactas de 26 px; etapas com marcadores e conectores finos; enunciado compacto; títulos padronizados; tabs em controle segmentado; toolbar agrupada à direita no desktop; disclosures com chevrons consistentes; hover/pressed/focus e scrollbars discretas. Reutilizado o renderizador SVG da Home, com o mesmo traço de 1,7, nos comandos e estados da análise.

Removidas declarações desktop sobrescritas de padding, largura de label e overflow, além dos chevrons antigos substituídos. Regras responsivas que atendem outras rotas foram preservadas.

## 3. Barra de decisão

Primário azul à direita; “Usar sugestão” secundário; “Ajustar” ghost; observação em disclosure. Separação visual entre sugestão e pontuação. Input compacto de 16 px, label pequena, placeholder sem atribuir valor e foco azul. A barra desktop continua com 60 px e comportamento sticky no Original. A lógica de validação/finalização e os payloads não mudaram.

## 4. Critérios e análise

Resultado em superfície azul suave com tipografia de 26 px. Critérios em linhas, sem cards individuais; ícones com alternativa textual; descrição em cor muted. Faixa de evidência discreta; resumo formal em linha; detalhes técnicos fechados. O estado vazio de passos não deixa mais um bloco de detalhe vazio. Nenhuma conclusão, pontuação ou classificação foi recalculada.

## 5. Viewer

Mantidos grid 60/40, splitter, expansão, zoom, rotação e ajuste proporcional do WORKSPACE-01D. O fundo e a sombra da página foram refinados. Em 1440×900, a imagem mediu 801×1068 px; viewer com `clientHeight = scrollHeight = 1068`. Ao rolar a página 665 px, o scroll interno permaneceu zero. A página geral pode rolar para exibir o final da folha larga.

## 6. Mobile

Barra compacta “Sugestão / Ajustar / Finalizar”, navegação existente e input de pelo menos 16 px. Comandos de expansão desktop continuam ocultos. Inspecionados 390×844 e 430×932. O tablet conserva o comportamento anterior do viewer, inclusive sua rolagem interna quando necessária.

## 7. Desktop e consistência com a Home

Inspecionados 1366×768, 1440×900 e 1920×1080, além de tablet 768×1024. Nenhum overflow horizontal global nas seis medidas. Solução dominante; análise lateral; top nav e avatar compartilham os componentes da Home.

**“Esse workspace parece claramente parte do mesmo produto da Home?” Sim**, após comparação visual direta: mesma fonte, azul, superfícies, raios de 20 px, sombras e família de ícones, com densidade adequada à correção.

## 8. Acessibilidade

- Controles visíveis medidos (buttons, summaries, input e navegação) com dimensões de pelo menos 44 px nas seis viewports.
- Tabs: ArrowRight/Home confirmados no navegador; seleção, foco visível e roving tabindex preservados. Teste cobre também End.
- Disclosure de observação abriu/fechou com Enter; foco solid visível.
- Estados possuem texto/alternativa acessível além da cor. SVGs decorativos não duplicam nomes dos comandos.
- Contrastes calculados: muted/branco 5,01:1; azul escuro/azul claro 6,75:1; branco/azul primário 5,31:1; status warning/success/error sobre branco 6,34/5,88/6,62:1.
- Transições respeitam `prefers-reduced-motion`. Sem animação nova em skeletons.

Validação no navegador integrado no Mac com viewport redimensionada; não representa teste em aparelho iOS físico nem certificação completa de acessibilidade.

## 9. Screenshots e artifacts

Em `/private/tmp/confia-workspace02/`, fora do repositório:

- [Desktop 1440×900](/private/tmp/confia-workspace02/workspace-1440x900.jpg)
- [Mobile 430×932](/private/tmp/confia-workspace02/workspace-430x932.jpg)
- [390×844](/private/tmp/confia-workspace02/workspace-390x844.jpg)
- [768×1024](/private/tmp/confia-workspace02/workspace-768x1024.jpg)
- [1366×768](/private/tmp/confia-workspace02/workspace-1366x768.jpg)
- [1920×1080](/private/tmp/confia-workspace02/workspace-1920x1080.jpg)
- [Página completa](/private/tmp/confia-workspace02/workspace-full-page.jpg)
- [Critério expandido](/private/tmp/confia-workspace02/criterion-evidence.jpg)
- [Home usada na comparação](/private/tmp/confia-workspace02/home-reference-1280x720.jpg)
- [Geometria e controles](/private/tmp/confia-workspace02/geometry.json)

Os nomes indicam viewport CSS; capturas nativas podem excluir a barra de rolagem. A captura completa foi feita após rolar: a coluna sticky aparece na posição correspondente à rolagem.

## 10. Testes e performance

- `node --test tests/js/test_*.cjs`: **417 passaram; 0 falhas; 0 ignorados**.
- `.venv/bin/python -m pytest -q tests/test_tme_photo_errors.py tests/test_tme_pilot.py tests/test_tme_audit_view.py tests/test_capture_static.py`: **50 passaram**.
- Dois testes novos: ícones/nomes acessíveis/estados e tabs por teclado sem novas requisições. A suíte existente mantém cobertura de decisão, disclosures, zoom, páginas, rotação, fit e estados do relatório.
- Console final sem warnings/errors. Inspeção em caso real sem envio de decisão.
- Aumento de **7.821 bytes não comprimidos** nos assets alterados; sem novos requests de assets, dependências ou fontes. Logs de testes no diretório de artifacts.

## 11. Git diff --check e arquivos

`git diff --check`: sem erros. Whitespace dos arquivos novos também verificado.

Alterados nesta tarefa:

- `app/confia_lean_auditor/static/tme/tme-theme.css`
- `app/confia_lean_auditor/static/tme/home.css`
- `app/confia_lean_auditor/static/tme/home.js`
- `app/confia_lean_auditor/static/tme/correction-workspace.css`
- `app/confia_lean_auditor/static/tme/correction-workspace.js`
- `app/confia_lean_auditor/static/tme/workspace-report.js`
- `app/confia_lean_auditor/static/tme/tme.js`
- `app/confia_lean_auditor/static/tme/index.html`
- `tests/js/test_tme_workspace_02.cjs` (novo)
- Este relatório (novo).

Hashes comparados com o início da tarefa confirmam que as mudanças em arquivos existentes ficaram restritas aos oito assets acima. Backend, OCR, Mathpix, Auditor, claims, rubricas, Lean, dados e decisões não foram alterados nesta tarefa.

## 12. Git status --short

[Saída completa](/private/tmp/confia-workspace02/git-status-short.txt), incluindo alterações anteriores da branch. Sem staging, commit ou push.
