# TUTORIA-CHAT-DEMO-01 — Assistente contextual TutorIA

## Decisão final de produto

O Assistente é uma ferramenta transversal, acessada pelo botão **✦ TutorIA**, apenas
no ambiente TutorIA. Não há aba, card de módulo, página exclusiva nem ação de expansão.
O endereço antigo `#student/tutoria/chat` retorna à Visão geral do TutorIA; não renderiza
uma experiência de chat independente.

O botão aparece em Visão geral, Conteúdos, Banco de questões, Praticar, Feedback,
Trilhas, Meu progresso e Minhas atividades do TutorIA. Fica ausente em Início global,
Exames, Minhas submissões institucionais, Professor e Gestão. `EXAM` e `submission`
bloqueiam a abertura e o envio mesmo se a rota informada estiver inconsistente.
Enquanto a autenticação está pendente, o assistente permanece oculto.

## Painel e interação

O botão abre o drawer sem mudar a rota. O painel contém:

- TutorIA / Assistente de estudo;
- indicação discreta “Experiência demonstrativa”;
- contexto atual, com detalhes recolhíveis;
- histórico da conversa;
- Me dê uma pista, Explique de outro jeito, Como começo?, Meu raciocínio faz sentido?;
- campo “Digite sua dúvida...” e Enviar;
- Nova conversa e Recolher.

O aluno continua usando a página e o caderno. O drawer é não modal, sem backdrop,
sem avatar comercial e sem animações. Recolher ou Escape dentro do painel devolvem
foco ao botão sem deslocamento provocado por foco. Conversas e mensagens ainda não
enviadas permanecem em memória por contexto; fechar ou navegar não as apaga. Recarregar
encerra essa sessão. Nova conversa reinicia apenas o contexto atual.

Enter envia; Shift+Enter insere uma linha; composição de teclado é respeitada.
Mensagens vazias e acima de 2.000 caracteres são rejeitadas. O histórico usa
`role="log"` e `aria-live="polite"`. Texto/LaTeX usam o renderer compartilhado/KaTeX;
HTML informado permanece texto e erros matemáticos escritos são preservados.

## Contexto do frontend

| Tela | Contexto apresentado |
| --- | --- |
| Visão geral | Como posso ajudar nos seus estudos? |
| Conteúdo selecionado | Você está estudando: título real do material selecionado. |
| Banco com filtro de tema | Você está explorando questões de tema selecionado. |
| Banco sem filtro/metadado de tema | Você está explorando o banco de questões. |
| Questão em TUTOR | Você está trabalhando na questão código real do catálogo. |
| Feedback | Você está revisando uma tentativa. |

O banco não inventa um tema quando o catálogo não oferece esse dado. Alterar o filtro
atualiza o drawer aberto. Conteúdo usa o título e tema da biblioteca demonstrativa;
questão usa o catálogo existente; feedback usa a representação da tentativa selecionada,
ou o exemplo explicitamente ilustrativo quando não há tentativa real.

A seleção de contexto copia somente `kind`, `origin`, `theme`, `contentId`,
`contentTitle`, `problemId`, `problemTitle` e `attemptText`. Não copia identidade,
submissão, auditoria ou decisão docente. Respostas são sempre `DEMO`; mensagens
escritas pelo usuário e referências ao catálogo são identificadas separadamente.

## Caderno e responsividade

Desktop/tablet reservam espaço lateral para o botão e para o drawer, fora do conteúdo.
No celular, uma faixa inferior é reservada para o botão; o drawer ocupa 48% da altura
e a tela atual mantém 52%, com rolagens independentes. A paleta e as bordas/sombras
usam os tokens existentes do ConfIA.

O wrapper existe no HTML inicial. Abrir/fechar não recria nem move o iframe, não muda
seu `src`, não emite comandos de captura e não altera questão, strokes, snapshot,
Mathpix preview ou autosave. Atualizações de layout com o mesmo contexto não recriam
o campo de mensagem. O espaço de escrita continua disponível.

## Demo pedagógica e integração futura

As respostas são locais, predefinidas em `demo/tutoria-chat-demo.js`. Fazem perguntas,
dão pistas graduais e ajudam a organizar o raciocínio; não atribuem nota nem afirmam
correção automática. O adaptador `reply` permanece separado da apresentação.

Não há LLM, chamada externa, armazenamento de conversa, endpoint novo, Auditor ConfIA,
Lean ou criação de Submission/AuditRun/TeacherDecision. A conversa não altera métricas
demonstrativas ou evidências institucionais.

Uma integração futura, autorizada separadamente, poderá transformar o contexto em:

```text
current_context = { content_id, theme, problem_id, current_attempt }
POST /tutoria/chat
```

Esse backend não foi implementado. Autenticação/autorização, minimização de dados,
retenção e transporte deverão ser definidos nessa futura integração.

## Arquivos

- `static/tutoria-assistant.js` / `.css`: escopo, contexto, abertura e layout do drawer.
- `static/tutoria-chat.js` / `.css`: conversa, memória e renderer.
- `static/demo/tutoria-chat-demo.js`: respostas e quatro ações rápidas.
- `static/index.html`, `shell.js`, `tutoria.js`, `tutoria.css`, `demo/tutoria-demo-data.js`
  e `resolution-workspace.js`: integração e remoção da página/atalhos antigos.
- `tests/js/test_tutoria_assistant.cjs`, `test_tutoria_chat.cjs`, `test_tutoria_demo.cjs`
  e `tests/test_tutoria_chat_demo.py`: comportamento e contratos de apresentação.

## Validação da revisão final

- `node --test tests/js/*.cjs`: **337 testes aprovados**.
- Python focado: **29 testes aprovados** em `test_tutoria_demo.py`,
  `test_tutoria_chat_demo.py`, `test_ux_pro_01.py`, `test_ui_02_workspace.py`,
  `test_ui_p0_accessibility.py` e `test_ui_01_shell.py`.
- Cobertura de escopo das rotas/perfis, ausência da aba/card/página, abertura sem
  navegação, fechamento, mudança de contexto e filtros, isolamento das conversas,
  bloqueio de EXAM, preservação de iframe/questão/ink version/snapshot/preview/autosave
  e ausência de chamadas externas ou criação de Submission.
- Conferência visual com dados descartáveis em `127.0.0.1:8768`, desktop e tablet,
  incluindo traços no modo Mouse/teste. Caneta física não foi exercitada.
- Backend, captura, renderer matemático e implementação docente preservados por
  comparação SHA-256 com o início desta revisão.
- Sem staging, commit ou push; suíte Python integral não executada.
