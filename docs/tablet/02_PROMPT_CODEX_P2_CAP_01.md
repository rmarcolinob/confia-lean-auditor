# Codex — P2-CAP-01: caderno experimental de captura manuscrita

Trabalhe no repositório ConfIA-Lean-Auditor aberto neste workspace.
Diretório histórico: ~/Documents/confia-lean-auditor. Confirme o diretório efetivo; não presuma que a árvore e os nomes históricos continuam iguais.

## Missão

Implemente agora um primeiro incremento pequeno e funcional de captura manuscrita em tablet para o Produto 2 — Avaliação Assistida.

Resultado esperado: uma página experimental permite selecionar uma questão já cadastrada, escrever com caneta, apagar/desfazer, salvar/recuperar o rascunho local e exportar um documento de traços e PNG por página.

Este incremento NÃO reconhece escrita, NÃO chama /audit, NÃO roda Lean, NÃO atribui nota e NÃO constitui entrega oficial ao professor. Não simule essas funções.

## 1. Inspeção curta antes do patch

Leia as instruções locais do projeto (inclusive AGENTS.md, quando existir). Execute git status --short, veja branch e últimos commits. Inspecione somente montagem de static/rotas, frontend atual, acesso ao catálogo, versão de Python/Pydantic e organização dos testes.

Há registro histórico de arquivos de interface modificados e benchmarks não rastreados. Preserve todo trabalho preexistente. Não faça reset, clean, stash, troca de branch, commit ou staging automático. Não reformate arquivos inteiros. Se houver conflito direto com edição já existente, informe o conflito e proponha uma alternativa isolada; não apague alterações.

Depois dessa inspeção, prossiga para a implementação. Não substitua esta tarefa por outra auditoria geral do projeto.

## 2. Escopo e arquivos

Prefira uma página isolada sob a montagem estática existente, com link discreto apenas onde puder ser adicionado sem conflito. Não redesenhe as áreas Aluno/Professor/Gestão.

Estrutura sugerida, adaptável ao que já existir:

app/confia_lean_auditor/capture/__init__.py
app/confia_lean_auditor/capture/schemas.py
app/confia_lean_auditor/static/capture/tablet.html
app/confia_lean_auditor/static/capture/tablet.css
app/confia_lean_auditor/static/capture/ink-model.js
app/confia_lean_auditor/static/capture/ink-canvas.js
app/confia_lean_auditor/static/capture/draft-store.js
app/confia_lean_auditor/static/capture/tablet.js
tests/test_capture_contracts.py
tests/test_capture_static.py
docs/CAPTURA_TABLET_P2_CAP_01.md

Use a versão de Pydantic e os padrões já presentes. Não atualize dependências por conveniência.

Não alterar: /audit, claims, formal steps, student claims/checkers, Lean, Mathlib, Lake, rubricas, score/verdict, assets matemáticos, benchmarks ou relatórios existentes.

main.py só pode receber uma alteração mínima de roteamento se a página não puder ser servida pela montagem estática atual. Nesse caso explique a necessidade e preserve o corpo de /audit.

## 3. Interface

Manter a identidade visual existente, sem inventar logos: azul institucional, fundo claro, controles legíveis, botões com rótulos e foco acessível.

Título: “ConfIA — Caderno de resolução”.
Aviso visível: “Ambiente experimental de captura. Não realiza correção automática.”

Reaproveitar o catálogo já existente por leitura. Não inventar endpoints nem enunciados. Se o catálogo não tiver uma rota reutilizável, empregar uma rota mínima de leitura ou um seletor gerado com os assets existentes, justificando a escolha. Não codificar enunciados duplicados dentro do JavaScript.

Um rascunho corresponde a uma questão. Trocar questão deve salvar o rascunho anterior e abrir/criar outro sem sobrescrevê-lo. Não tratar problem_id como identificador único de aluno/tentativa.

Disponibilizar caneta, borracha de traço inteiro, desfazer, refazer, navegação de páginas e uma grade discreta. Limite inicial de três páginas por rascunho, definido em configuração. Não implementar borracha parcial, reconhecimento de figuras ou editor matemático nesta etapa.

Botões finais: “Preparar versão para envio”, “Exportar traços” e “Exportar PNG da página”. Não usar “Solução enviada ao professor” sem backend de recebimento.

## 4. Contrato de captura v1

Separar modelo de dados, desenho e armazenamento. Usar JSON versionado e validável. Definir e documentar:

- schema_version;
- draft_id / local_snapshot_id;
- problem_id;
- input_mode = tablet_ink;
- origem experimental/local;
- páginas com page_id, índice, largura/altura lógicas e sistema de coordenadas;
- traços com stroke_id, page_id, pointer_type, largura/configuração visual e pontos;
- pontos com x, y, t_ms relativo ao início do traço e pressure_reported nullable;
- operações mínimas de adicionar/apagar/desfazer/refazer, com referências consistentes;
- configuração/versão do renderizador;
- estado ativo final reconstituível;
- horários do cliente identificados como tal.

NÃO incluir nota, veredito, confiança matemática, identidade autenticada inventada, autorização docente, receipt_id do servidor ou audit_ready=true.

Proibir campos extras; validar números finitos, coordenadas dentro da página, pressão em [0,1] quando fornecida, tempo não decrescente por traço, IDs únicos, referências existentes, limites de páginas/traços/pontos e tamanho de importação. Definir limites iniciais configuráveis e documentar que são limites do protótipo, não do fornecedor OCR.

Estado exibido, exportação e recuperação devem ser derivados da mesma representação de traços ativos. Elementos apagados/desfeitos não podem reaparecer no PNG. Registrar apenas o histórico necessário para consistência e revisão técnica; não coletar nome, matrícula ou dados biométricos adicionais.

## 5. Pointer Events e geometria

No modo caneta, aceitar desenho somente de pointerType=pen. Disponibilizar modo mouse explícito para teste em computador; não ativar desenho por toque automaticamente.

Usar pointer capture quando disponível; tratar pointerup, pointercancel e lostpointercapture de forma consistente, sem unir traços distintos. Se um traço for interrompido, preservar os pontos já recebidos como segmento interrompido e encerrar sua captura, sem inventar continuação.

Usar getCoalescedEvents quando disponível, com fallback e sem duplicar pontos. Não usar eventos preditos no documento persistido. Não depender exclusivamente de APIs ausentes em alguns navegadores/contextos; documentar detecção de capacidade.

Transformar coordenadas do evento em coordenadas lógicas da página. Tratar escala CSS e devicePixelRatio sem modificar os pontos salvos. Redimensionar/rotacionar deve redesenhar a partir do modelo, sem esticar nem perder a escrita.

touch-action deve ser limitado à área de desenho; preservar navegação/acessibilidade no restante da página. Não desabilitar zoom da página inteira. Não declarar “rejeição de palma resolvida”; isso depende de teste físico.

## 6. Renderização

Preservar pontos brutos reportados. Suavização não pode sobrescrever a fonte.

Se perfect-freehand já estiver disponível, reutilizar de forma isolada, com versão/opções registradas. Se estiver ausente, iniciar com um renderizador Canvas simples e substituível; não adicionar um framework/bundler nem um CDN sem versão para cumprir esse detalhe. Registre a ausência como decisão do primeiro incremento. Não inventar medição real de pressão: valor reportado e opção de renderização são informações distintas.

PNG: fundo branco, sem grade, sem interface e somente traços ativos. Dimensões e transformação devem ser documentadas. O usuário deve conseguir conferir a prévia que será exportada.

## 7. Salvamento, congelamento e exportação

Usar IndexedDB para rascunhos. Salvar depois de traço/operação concluída e manter checkpoints de traços longos quando viável. Exibir “Salvo neste dispositivo” apenas após sucesso. Tratar quota/falha, exibindo erro e oferecendo exportação; nunca limpar silenciosamente.

Na reabertura, apresentar escolha explícita de rascunho, sem carregar automaticamente dados de outra sessão. Este laboratório é para dados fictícios/testes autorizados e não implementa isolamento multiusuário. Documentar essa limitação.

“Preparar versão para envio” cria cópia local independente e não editável pela interface normal. Isso não autentica autoria e não substitui o futuro recibo do servidor. Exibir: “Versão preparada localmente; ainda não enviada.”

Para continuar escrevendo, criar nova versão de rascunho sem alterar a cópia anterior. JSON e PNG exportados devem se referir à mesma versão selecionada, não misturar snapshot com rascunho posterior.

Exportar JSON estruturado e PNG por página. Não tornar zip uma dependência obrigatória. Caso implemente importação de JSON para recuperação, validar integralmente e importar como cópia, sem sobrescrever IDs/revisões existentes.

## 8. Testes

Executar testes novos em diretórios temporários e testes leves relevantes já existentes. Não instalar navegadores, iniciar serviços externos, rodar benchmark de 500 casos ou executar Lean.

Testes de contrato: documento válido; campos extras; NaN/infinito; IDs duplicados; referência inválida; coordenadas/pressão fora do intervalo; tempos inconsistentes; limite excedido; round-trip sem alteração dos dados.

Testes de lógica de traços, usando a infraestrutura JavaScript já disponível: apagar/desfazer/refazer, isolamento de páginas, reconstituição do estado ativo, congelamento independente e mudança de questão sem sobrescrita. Se não houver infraestrutura, separar funções puras para teste e informar explicitamente o que não foi executado. Não alegar teste funcional de navegador a partir de asserts de HTML.

Teste de fronteira: a página nova não chama /audit, não aciona reconhecedor, não produz Lean, score ou veredito. Verifique importações e chamadas na superfície nova e, se houver ferramenta de navegador instalada, intercepte chamadas de rede durante o teste.

Testes manuais a documentar, sem marcar como executados sem dispositivo:
- iPad/Safari + Apple Pencil;
- tablet Android/Chrome + caneta suportada;
- palma antes/depois da caneta;
- rotação durante/após escrita;
- várias páginas;
- expoentes, frações e sinais pequenos;
- apagar, desfazer/refazer, recarregar e exportar;
- storage indisponível/quota;
- acesso em rede local sem presumir APIs exclusivas de contexto seguro.

## 9. Critérios de aceite

1. A página experimental abre sem alterar a auditoria existente.
2. Escrever e editar traços funciona no ambiente que foi efetivamente testado.
3. O documento exportado é aceito pelo schema.
4. Rascunhos podem ser recuperados sem perda silenciosa de operações concluídas.
5. PNG e versão ativa do documento correspondem.
6. Não existe falsa mensagem de entrega, transcrição, autenticação ou correção.
7. Limitações de teste físico, salvamento local e dispositivo compartilhado estão visíveis/documentadas.

## 10. Relato final

Mostre: arquivos alterados/criados; decisões e limites do schema; como abrir a página no computador/tablet; comando de inicialização conforme o projeto; resultados reais dos testes; pendências de hardware; git diff --stat e git status --short finais.

Para tablet, explique o endereço do computador na mesma rede autorizada, sem sugerir que 127.0.0.1 no tablet aponta para o computador. Não exponha o serviço em rede pública. Diferencie acesso em rede local de implantação autenticada.

Não declare integração com Mathpix, manuscrito transcrito, envio ao professor ou Lean neste patch. Termine com o próximo incremento recomendado: recebimento persistente de uma versão e revisão docente, podendo usar transcrição manual antes de OCR.
