# Identidade visual e escopo editorial

Análise realizada em 04/11/2026 (America/Fortaleza), antes da implementação. Commit de referência e hashes em `asset-manifest.json`.

## Referências examinadas

- `app/confia_lean_auditor/static/design-system.css`: azul `#1b66d2`, azul forte `#123b73`, fundo `#f4f7fb`, superfície branca, texto `#17233c`, bordas `#d5dfed`; semântica de sucesso, atenção, erro e informação.
- `static/styles.css` e `static/index.html`: monograma textual C/IA em quadrado azul, nome ConfIA em fonte de sistema, faixa institucional azul/amarelo/vermelho/verde na proporção 7:2:2:3. A marca é implementada em HTML/CSS; não foi encontrado arquivo de logotipo independente.
- `static/capture/tablet.html`, `tablet.css` e `identity.css`: caderno digital, enunciado, ferramentas de escrita, versão para envio e conferência da leitura. Reinterpretados para câmera 16:9 com geometria própria; nenhum código do caderno foi alterado.
- `static/index.html`, `submissions/teacher.js`, `teacher.css`, `audit-view.js`: revisão da transcrição, análise, decisão humana, estados formais separados de análise matemática. Não verificado não significa falso.
- `static/tme/index.html`, `tme-theme.css`, `home.css`, `home.js`: piloto TME, marca tipográfica, superfícies claras, ícones lineares, geometria de documento, cores semânticas. SVG decorativo original copiado para consulta em `public/assets/tme-hero.svg`.
- `management/router.py` e seção de gestão de `static/index.html`: indicadores agregados por escopo institucional implementados.

## Decisões

A animação usa a paleta compartilhada, o mesmo monograma e a mesma família de sistema; mantém os quatro acentos da faixa institucional. O azul específico do piloto (`#0867D9`) foi documentado, mas o filme usa prioritariamente o azul comum do sistema. Fórmulas compostas usam Times/Georgia do sistema; escrita simulada usa traços SVG originais para mostrar movimento de caneta. Estes traços são ilustrações de input, não uma identidade alternativa.

Movimento contínuo e programático: câmera em perspectiva sobre o caderno, traços de caneta, transformação em partículas de dados, progressão do fluxo de análise, reintrodução do denominador e conexões orbitais entre as áreas. Espaço seguro para legenda; aviso de demonstração sempre visível. Não usamos imagens geradas nem logomarcas inventadas.

## Marcas institucionais ausentes

Busca nos arquivos do repositório não encontrou logomarcas oficiais UFPI, FAPEPI ou SIA. O usuário informou que não as tem disponíveis no momento. O encerramento apresenta **nomes institucionais**, e não fac-símiles de logos. Para inserir arquivos oficiais depois, preencher `institutionAssets` em `src/Film.tsx` com caminhos relativos a `public/`. O registro tipográfico ConfIA reproduz o frontend. A versão renderizada é utilizável para revisão, com essa limitação de identidade explicitamente documentada.

## Maturidade mostrada no filme

| Dimensão | Evidência | Tratamento no vídeo |
|---|---|---|
| Aluno: caderno e envio | `static/capture/tablet.html`, `static/index.html` | Implementado no projeto |
| Professor: revisão e decisão | `static/submissions/teacher.js`, `teacher_decisions/`, `docs/TME_PILOT_01.md` | Implementado; decisão humana |
| Gestão: agregados | `management/router.py` | Implementado; sem números fictícios apresentados como reais |
| Feedback TutorIA | `docs/TUTORIA_DEMO_01.md`, `static/tutoria.js`, `tutoria-chat.js` | Demonstrativo |
| Histórico permanente de prática | `static/tutoria.js`, `docs/TUTORIA_DEMO_01.md` | Em desenvolvimento |

“Implementado” descreve código presente, não certificação de produção, escala ou validação de impacto. A soma dos naturais é um exemplo controlado, não uma execução do backend. Nenhum endpoint, LLM, OCR ou processo Lean é acionado pela animação. O trecho Lean representa uma proposição que poderia ser formalizada, com os imports apropriados (como Mathlib); sua presença não atesta compilação ou prova executada. A multiplicação 20 × 21 = 420 é verdadeira: o erro está na equivalência com a expressão anterior que tinha divisão por 2.
