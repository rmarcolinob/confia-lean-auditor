# P2-CAP-01 — caderno experimental de captura manuscrita

## Escopo

Este incremento acrescenta uma superfície local de engenharia para preservar escrita manuscrita. A página lê as questões do catálogo existente em `GET /problems`, mas não chama `/audit`, não reconhece escrita, não executa Lean, não produz nota e não envia dados ao professor.

O rascunho e as cópias congeladas ficam no IndexedDB do navegador. A mensagem “Salvo neste dispositivo” significa apenas que a escrita foi persistida localmente. A preparação exibe, de forma separada: “Versão preparada localmente; ainda não enviada.”

## Como iniciar

No diretório do repositório, com o ambiente virtual existente:

```bash
.venv/bin/uvicorn confia_lean_auditor.main:app --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000/capture` no computador.

Para um teste em tablet na mesma rede local autorizada, inicie explicitamente na interface de rede:

```bash
.venv/bin/uvicorn confia_lean_auditor.main:app --host 0.0.0.0 --port 8000
```

Descubra o endereço IPv4 local do computador e, no tablet conectado à mesma rede, abra `http://IP-LOCAL-DO-COMPUTADOR:8000/capture`. `127.0.0.1` no tablet aponta para o próprio tablet, não para o computador. Autorize a porta somente no firewall/rede local de teste; este protótipo não tem autenticação, TLS nem controles para exposição em rede pública.

## Contrato de captura v1

O modelo Python está em `app/confia_lean_auditor/capture/schemas.py`. O documento contém:

- `schema_version = "1.0"`, `document_kind`, `draft_id` e `local_snapshot_id`;
- `problem_id`, `input_mode = "tablet_ink"` e `origin = "experimental_local"`;
- até três páginas com dimensão lógica fixa inicial de 1200 × 1600 e origem no canto superior esquerdo;
- traços associados a uma página, tipo de ponteiro, estilo e pontos brutos;
- pontos em coordenadas lógicas com tempo relativo e pressão reportada anulável;
- operações `add`, `erase`, `undo` e `redo`, com referências reconstituíveis;
- lista final de traços ativos, conferida contra o histórico;
- versão e opções relevantes do renderizador;
- horários informados pelo cliente, sem tratá-los como horário confiável de servidor.

Campos extras são proibidos. O schema verifica números finitos, limites da página, pressão entre 0 e 1, tempos não decrescentes, IDs únicos, referências existentes, coerência do estado ativo e limites de cardinalidade. A função `validate_capture_json` recusa entrada acima de 10 MiB antes de decodificá-la.

Limites configurados para o protótipo: três páginas, 2.000 traços, 20.000 pontos por traço, 200.000 pontos totais, 10.000 operações e 10 MiB por documento importado. Estes são limites internos do P2-CAP-01, não limites de um fornecedor de OCR.

O contrato não inclui identidade de estudante/professor, recibo de servidor, autorização, confiança matemática, status de auditoria, nota ou veredito.

## Captura e renderização

A página usa Pointer Events. No modo padrão, apenas `pointerType=pen` desenha. Mouse só desenha após a ativação explícita de “Mouse (teste)”; toque não é convertido em tinta. A área do canvas usa `touch-action: none`, sem bloquear o zoom e a navegação da página inteira.

Quando disponível, `getCoalescedEvents()` preserva amostras intermediárias e elimina amostras duplicadas. Eventos preditos não são usados. `pointercancel` e `lostpointercapture` encerram o segmento como interrompido, conservando os pontos já recebidos. Redimensionamento e rotação redesenham a página a partir do modelo em coordenadas lógicas; `devicePixelRatio` altera apenas o buffer de renderização.

O primeiro incremento usa `confia_canvas_polyline` 1.0.0, um renderizador Canvas simples e substituível. Não foi adicionada a dependência `perfect-freehand`. A pressão reportada é armazenada, mas não modifica a largura e não é apresentada como medição calibrada.

A grade existe apenas na área de escrita. A prévia e o PNG usam fundo branco e somente os traços ativos da versão aberta. Apagamentos e operações desfeitas não reaparecem na imagem.

## Armazenamento e versões

Cada rascunho tem ID próprio; `problem_id` não identifica estudante ou tentativa. Trocar de questão enfileira o salvamento do rascunho anterior e cria outro rascunho separado. Depois de recarregar a página, nenhuma versão é restaurada automaticamente: a pessoa escolhe explicitamente uma versão salva para a questão.

“Preparar versão para envio” cria e salva uma cópia independente `local_snapshot`, abre-a em modo somente leitura e não altera o rascunho de origem. “Continuar em nova versão” clona a cópia para um novo `draft_id`. JSON e PNG são sempre produzidos a partir da mesma versão atualmente aberta; o nome do arquivo inclui o mesmo identificador local.

Falhas ou indisponibilidade do IndexedDB são exibidas. A interface continua oferecendo exportação manual e não apaga a única cópia em memória. Não há importação de JSON neste incremento.

## Refinamento de viewport e enunciados — 01/10/2026

A inspeção encontrou seletores com fonte computada de 14,08 px e largura mínima
intrínseca que podia expandir a coluna da página. No navegador local, uma viewport
de 390 px tinha 558 px de conteúdo para 375 px úteis. Em 1024 × 768 e 1180 × 820,
o layout anterior não apresentava overflow, a escala era 1 e não havia transform
no canvas. A fonte pequena é uma hipótese para o zoom ao focar controles no
dispositivo; o evento de zoom do tablet não foi reproduzido no navegador desktop.

Os controles agora usam 1rem (16 px na configuração padrão), com largura limitada
ao contêiner e `min-width: 0`. A coluna principal usa `minmax(0, 1fr)`. A viewport
mantém `width=device-width, initial-scale=1`, sem restringir zoom voluntário, sem
escala CSS e sem ocultar overflow da página inteira. A captura e a transformação
entre coordenadas CSS e lógicas do canvas permanecem intactas.

KaTeX 0.18.9 e auto-render são servidos de `static/capture/vendor/katex-0.18.9/`,
com fontes e licença MIT locais. A integridade do pacote oficial foi conferida.
O renderizador recebe texto inserido por `textContent` e reconhece `$...$`,
`$$...$$`, `\(...\)` e `\[...\]`. A renderização roda ao carregar e trocar questão,
somente no enunciado. Usa `trust: false`, limites de expansão/tamanho e fallback
legível para LaTeX inválido ou indisponibilidade do renderizador. Expressões muito
largas têm rolagem própria. O catálogo e os problem assets continuam como texto;
o fallback conservador para álgebra legada é descrito abaixo.

Verificação local executada: larguras 390, 600, 768, 1024, 1180, 1366 e 1440 px
sem overflow horizontal, incluindo recolher/expandir. Em catálogo fictício separado,
foram conferidos os quatro delimitadores, mistura de texto/matemática, erro de
LaTeX seguido de fórmula válida, texto semelhante a HTML e fórmula display larga.
Também foi conferida escrita com mouse após recolhimento, salvamento automático e
rolagem com sticky. Estes testes não comprovam comportamento físico de caneta
nem zoom de Safari/Chrome no tablet.

Os dados de teste estão em `tests/fixtures/capture_math_catalog.json`, sem alterar
o catálogo real. Testes automatizados pertinentes:

```bash
.venv/bin/pytest -q tests/test_capture_static.py tests/test_capture_contracts.py
node --test tests/js/*.cjs
```

Para validação física, verificar abertura em escala natural, foco nos seletores,
rotação, recolher/expandir, fórmulas largas, pinch zoom voluntário e alinhamento da
caneta antes/depois da rolagem. Não redefinir programaticamente o zoom escolhido.

## Fallback de matemática legada — 01/10/2026

Os dez `problem.json` atuais armazenam strings sem delimitadores matemáticos.
`core/problem_catalog.py` entrega `statement` sem transformação em `/problems`.
Exemplos reais:

- ITA2025F2Q1: `p(x)=x^57+a x^14+b x^7+1`, divisor `x^2-x+1` e resto `2x+1`;
- ITA2025Q3: `(x + 1/x)^6 (x - 2/x)^5`;
- ITA2025Q5: `S_n = ∑_{k=1}^n a_k = b_{n+1} - b_1`.

São texto puro com notação matemática parcial, não HTML nem LaTeX uniformemente
marcado. Nenhum asset, rota ou contrato de problemas foi modificado.

Na ausência de apresentação curada, `problem-math.js` mantém duas camadas exclusivas: havendo delimitadores, usa
auto-render normalmente, sem reinterpretar os trechos de texto ao redor. Sem
delimitadores, procura apenas expressões curtas de inteiros e variáveis `a,b,x,y,z`,
coeficientes (`2x`, `ax`, `a x`), potências inteiras, `+`, `-`, `=`, um nível de
parênteses e atribuições simples `p(x)=…`, `f(x)=…`, `g(x)=…`. Exige potência
explícita ou variável + número + adição/igualdade, evitando letras isoladas,
palavras e rótulos hifenizados. Expoentes são normalizados apenas na apresentação:
`x^57+ax^14` vira `x^{57}+ax^{14}` para KaTeX.

O fallback limita candidatos a 160 caracteres, números/expoentes a seis dígitos
e produtos a duas variáveis. Não interpreta frações com `/`, decimais, índices,
somatórios, trigonometria, gregas, comandos TeX ou fórmulas arbitrárias. Havendo
marcação parcial (`\\`, `_`, chaves), código com crases ou texto semelhante a HTML,
não aplica heurística ao enunciado. Fragmentos próximos de operadores não
suportados ou expressões incompletas ficam intactos. Frações e somatórios precisam
de apresentação curada ou de delimitadores e LaTeX explícitos para renderização completa.

Texto normal é criado com nós de texto; os spans matemáticos usam KaTeX com
`trust: false`. O DOM só é substituído depois de todas as expressões reconhecidas
renderizarem; em exceção, o texto original inteiro é mantido com aviso legível.
Carregamento/troca executam a apresentação; recolher/expandir apenas oculta/exibe
o mesmo DOM. Os testes cobrem o polinômio real, expoentes, texto comum,
delimitadores, candidatos inseguros e falha do renderizador.

Validação deste patch: 56 testes JavaScript e 24 testes Python de captura passaram.
No navegador local, F2Q1 mostrou três fórmulas com os expoentes corretos, inclusive
depois de recolher/expandir e trocar de questão; F2Q5 renderizou `3^{100}` e Q3
preservou integralmente a expressão com frações não suportadas. Larguras de 390,
1024 e 1366 px permaneceram sem overflow horizontal; nenhum erro de console.
Validação física no tablet permanece pendente.

## P2-UI-01 — apresentação matemática curada

O registro compartilhável fica em
`app/confia_lean_auditor/static/problem-presentations/registry.json`, fora dos
problem assets e da pasta de captura. É JSON declarativo, sem código por questão:
cada entrada contém `problem_id`, `source_statement` exato, `display_version` e
`segments` de tipos `text`/`math`. Conteúdo matemático é LaTeX sem delimitadores.
As dez entradas foram curadas manualmente; não foram alterados `problem.json`,
`ProblemConfig`, `/problems`, `/audit`, claims, Lean, rubricas ou benchmarks.

Cobertura: ITA2025Q1, ITA2025Q3, ITA2025Q4, ITA2025Q5, ITA2025Q8,
ITA2025F2Q1, ITA2025F2Q3, ITA2025F2Q5, ITA2025F2Q6 e ITA2025F2Q8.
Inclui potências, frações, índices, somatórios, raiz, conjuntos, funções reais,
gregas, logaritmos e trigonometria. `sen` foi mantido com `\\operatorname{sen}`;
os decimais mantêm vírgula e a prosa não foi reescrita.

Ordem de resolução na apresentação de `/capture`:

1. Entrada curada para o ID, somente com igualdade estrita de `source_statement`.
2. LaTeX explicitamente delimitado, se não houver entrada curada para o ID.
3. Fallback algébrico legado restrito, sem ampliar sua gramática.
4. Texto original.

Uma entrada conhecida com fonte divergente interrompe a resolução: a página
mostra literalmente o texto recebido, sem aplicar as camadas 2/3. Duplicidade,
estrutura inválida, KaTeX ausente ou erro de LaTeX também preservam o original
inteiro, com aviso legível. O renderizador constrói um fragmento e só o publica
quando todos os segmentos renderizam. Texto usa nós de texto, matemática usa
KaTeX local com `trust: false`, limites e macros novas por chamada.

`tablet.js` carrega o registro estático em paralelo com `/problems` e passa o ID
e o registro a `ConfiaProblemMath.render`. Uma falha no carregamento do registro
não desabilita captura ou salvamento: permanecem disponíveis as camadas já
existentes. Troca de questão renderiza novamente; recolher/expandir conserva o
mesmo DOM. A interface principal e a área do professor não foram refatoradas;
podem consumir futuramente esse mesmo JSON e a API de apresentação.

Para editar a curadoria, revisar manualmente a correspondência matemática e a
prosa, copiar a fonte exata e incrementar `display_version` quando a apresentação
mudar. Nunca acrescentar campos ao problem asset para transportar esta camada.
Testes verificam igualdade com os assets e com `/problems`, cobertura dos dez IDs,
renderização real no KaTeX local, mismatch, segurança, erros e integração da UI.

Validação do P2-UI-01: 86 testes JavaScript e 29 testes Python passaram (captura,
contratos e três testes de UI/catálogo selecionados). Não foram executados `/audit`
nem benchmarks. Os dez enunciados renderizaram no navegador local em 1024 × 768,
sem erros; Q1, Q3, Q5, Q8 e F2Q3 também foram inspecionados visualmente. Q5 manteve
as fórmulas após recolher/expandir nas larguras 390, 1024 e 1366 px, sem overflow
horizontal da página. Um respiro de 6 px vertical/3 px horizontal no contêiner
inline evita cortes de tipografia e barras espúrias, mantendo rolagem para
fórmulas largas. CSS e scripts de apresentação têm referências `?v=p2-ui-01`
para não reutilizar assets anteriores em cache. A validação física continua pendente.

## Verificação manual necessária

Use `docs/tablet/03_TESTE_MANUAL_TABLET.md` como registro. Permanecem pendentes testes físicos em:

- iPad/Safari com Apple Pencil;
- tablet Android/Chrome com caneta suportada;
- palma antes e durante a escrita;
- rotação durante e depois do traço;
- frações, expoentes, sinais pequenos, páginas e operações de edição;
- recuperação após recarga, quota/armazenamento indisponível e acesso pela rede local.

Não se deve concluir compatibilidade geral, rejeição de palma ou segurança para avaliação escolar sem esses ensaios e sem a camada futura de autenticação/recebimento.
