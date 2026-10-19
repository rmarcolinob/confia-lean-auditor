# TUTORIA-DEMO-01 — Visão ampliada do TutorIA

## Objetivo

Apresentar o TutorIA como ambiente de aprendizagem matemática para a rede pública:
conteúdos, questões, prática, feedback, trilhas e acompanhamento. A entrada
`#student/tutoria` é uma home com seis módulos; não abre uma questão automaticamente.
O contexto do aluno, da escola e da turma é preservado.

A navegação principal do aluno mantém Início, TutorIA, Exames e Minhas submissões.
Dentro do TutorIA, a navegação secundária oferece Visão geral, Conteúdos, Banco de
questões, Minhas atividades e Meu progresso.

A extensão conversacional está descrita em [TUTORIA_CHAT_DEMO_01.md](TUTORIA_CHAT_DEMO_01.md).
Feedback pedagógico apresenta a revisão estruturada da tentativa; Assistente TutorIA
oferece uma conversa demonstrativa em drawer pelo botão flutuante, somente dentro
do TutorIA. Não possui aba, card ou página exclusiva.

## Módulos e origem dos dados

`REAL`, `DEMO` e `FUTURE` são classificações internas. A interface usa indicações
como “Visão demonstrativa”, “Dados ilustrativos” e “Em desenvolvimento”.

| Rota após `#student/` | Entrega | Situação |
| --- | --- | --- |
| `tutoria` | Seis módulos, conteúdo em destaque, recomendações e atividades recentes | Composição de recursos reais e exemplos identificados |
| `tutoria/content` | Cinco temas, treze materiais navegáveis e exemplos com KaTeX | DEMO |
| `tutoria/questions` | Catálogo existente, busca, enunciados e ação Resolver | REAL |
| `tutoria/practice` | Mesmo caderno, escrita, reconhecimento, prévia e solução digitada | REAL; as orientações de feedback são DEMO |
| `tutoria/feedback` | Representação da tentativa e orientações de revisão | Tentativa REAL da sessão ou exemplo DEMO; feedback sempre DEMO nesta fase |
| `tutoria/trails` | Quatro percursos com etapas e percentuais ilustrativos | DEMO |
| `tutoria/progress` | Temas, atividades, questões, evolução e próximos focos | Métricas DEMO; atividades reais da sessão são identificadas separadamente |
| `tutoria/attempts` | Tentativas desta sessão; exemplos na ausência de tentativas | REAL em memória; histórico persistente FUTURE |

### Conteúdos e destaque

A biblioteca contém Álgebra, Funções, Geometria, Trigonometria e Estatística e
Probabilidade. O destaque “Funções do 1º grau” apresenta objetivos, nível e tempo
estimado ilustrativo. Cada material abre uma explicação curta e um exemplo.
“Praticar questões” leva ao catálogo real; não promete questões daquele conteúdo
quando o catálogo ainda não informa essa relação.

### Catálogo real

O banco reutiliza a única carga de `/problems` feita pelo aplicativo e disponibilizada
pelo workspace. Não há segunda base de questões. A busca considera código, título e
enunciado, ignorando acentos. A ação Resolver seleciona o `problem_id` correspondente
e abre o mesmo iframe `/capture` em modo `practice`.

Tema, dificuldade, série e origem só filtram valores efetivamente presentes nos
metadados. Filtros sem dados ficam desabilitados, com “Em desenvolvimento”. Não se
deduz dificuldade, série ou origem pelo título. O carregamento, o catálogo vazio,
a busca sem resultados e a falha de carregamento têm estados próprios.

### Prática e feedback

O caminho de escrita continua usando o caderno existente, S Pen, Mathpix transitório,
prévia e renderer matemático compartilhado. A geometria da captura e os arquivos de
`static/capture/` não foram modificados nesta tarefa. A prática digitada também usa
o caminho de feedback pedagógico.

O endpoint legado `/audit` executa auditoria formal. Ele **não é chamado pelo modo
TUTOR** nesta demonstração. Como não há um serviço independente de feedback pedagógico,
`ConfIATutoria.requestFeedback()` fornece orientações demonstrativas locais, sem
transporte HTTP e sem fallback para o auditor. O fluxo docente de auditoria permanece
existente. Os atalhos autenticados antigos `resolve` e `feedback` direcionam às novas
rotas de prática e feedback do TutorIA.

As orientações não afirmam que a solução do aluno está certa ou errada. Para uma
tentativa real, mostram “O que você já fez”, “Pontos para revisar” e “Próximo passo”,
acompanhados de “Feedback demonstrativo” e “sem análise automática desta tentativa”.
Um exemplo independente, claramente ilustrativo, apresenta a visão de feedback
quando ainda não há tentativa na sessão.

A representação da solução conserva o conteúdo recebido, inclusive erros matemáticos.
Texto e matemática usam o renderer compartilhado/KaTeX, sem editar o HTML gerado e
sem corrigir números, sinais ou etapas. Uma versão modificada depois do pedido de
feedback é identificada como diferente da tentativa registrada.

## Separação TutorIA × Exames

- TutorIA: conteúdo, prática e revisão; nenhum `Assessment`, `Submission` oficial,
  `AuditRun` institucional ou `TeacherDecision` é criado pela ação de feedback.
- Exames: avaliação, entrega oficial, professor, Auditor ConfIA, Lean seletivo e
  decisão docente continuam no fluxo existente.
- A interface normal do TutorIA não apresenta Lean, claims, verificação Mathlib,
  status formal, pontuação institucional ou relatório técnico do auditor.
- Ao sair do TutorIA, a mensagem global de feedback é limpa. Exames não herda a
  apresentação de feedback de estudo.
- A troca de Exames para prática limpa o vínculo com avaliação/item e configura o
  caderno em `practice`. As tentativas do TutorIA não aparecem em Minhas submissões.
- Não houve alteração de autorização nem de modelos/backend nesta tarefa.

## Governança dos dados demonstrativos

`static/demo/tutoria-demo-data.js` concentra conteúdos, exemplos, trilhas,
recomendações, `activities_demo`, `feedback_demo` e `progress_demo`. O módulo de
apresentação não contém cliente de persistência, integração com Gestão ou chamadas
de auditoria. Nenhum valor ilustrativo é gravado em stores institucionais.

As tentativas feitas pelo usuário são registradas apenas em memória nesta página,
com `origin: "REAL"`, problema, texto, data e sequência. O feedback tem origem
separada (`feedbackOrigin: "DEMO"`). A home mostra as três tentativas mais recentes;
a área de atividades mostra até vinte. Recarregar a página encerra esse histórico.
Os rascunhos locais já existentes do caderno seguem seu mecanismo anterior.

Quando há tentativas da sessão, elas substituem os exemplos na lista de atividades.
Elas não alteram os números de `progress_demo`. Os percentuais e contagens
ilustrativos não constituem evidência de aprendizagem nem são enviados à Gestão.

## Identidade visual e responsividade

`tutoria.css` usa somente tokens existentes: azul, navy, branco, fundos claros e
acentos institucionais. Não introduz paleta, framework ou biblioteca externa.
Os módulos usam três colunas em desktop, duas até 1100 px e uma até 620 px.
A navegação secundária se ajusta em linhas e fica fora da área de escrita ativa,
preservando o espaço do caderno. Links, botões, campos e indicadores mantêm semântica
nativa, foco visível e rótulos acessíveis.

## Arquitetura futura

Estes conceitos estão documentados como próximos passos, sem novos modelos ou tabelas:

| Conceito | Responsabilidade futura |
| --- | --- |
| `Content` | Conteúdos curriculares revisados e versionados |
| `LearningResource` | Materiais e recursos associados aos conteúdos |
| `PracticeAttempt` | Tentativas persistentes de prática, separadas de Submission |
| `PedagogicalFeedback` | Orientações reais, com origem e versão da tentativa |
| `LearningPath` | Percursos e critérios de avanço |
| `StudentSkillState` | Evidências reais e rastreáveis por habilidade |
| `Recommendation` | Sugestões baseadas em evidências, com justificativa |

O próximo serviço pedagógico deverá substituir o adaptador demonstrativo sem usar
`/audit` como atalho. Histórico, metadados do catálogo e recomendações reais estão
classificados como `FUTURE`. A evolução deverá distinguir progresso real e demo,
definir retenção/autorização próprias e somente então considerar métricas reais de
aprendizagem. Não foram implementados agentes, proficiência, analytics, API SEDUC,
banco novo ou motor de recomendação.

## Arquivos desta entrega

- Novos: `static/demo/tutoria-demo-data.js`, `static/tutoria.js`, `static/tutoria.css`.
- Integração: `static/index.html`, `static/shell.js`, `static/app.js` e
  `static/resolution-workspace.js`.
- Testes: `tests/js/test_tutoria_demo.cjs`, `tests/test_tutoria_demo.py`; ajustes nos
  testes de shell, separação TutorIA/Exames, workspace e acessibilidade e no harness JS.
- Documentação: este arquivo.

Os caminhos `static/` acima são relativos a `app/confia_lean_auditor/`.
As alterações anteriores de P2-DEC-01 e UX-PRO-01 foram preservadas.

## Validação da entrega inicial TUTORIA-DEMO-01

- `node --test tests/js/*.cjs`: **318 testes aprovados**. Inclui dez testes novos de
  home, módulos, conteúdo, catálogo real, filtros, estados vazios/erro, rotas, prática
  manuscrita/digitada, feedback, isolamento institucional e retorno de Exames.
- Python focado: **42 testes aprovados** em `test_static_ui.py`, `test_ui_01_shell.py`,
  `test_ui_02_workspace.py`, `test_ui_p0_accessibility.py`, `test_ux_pro_01.py`,
  `test_tutoria_demo.py` e `test_capture_static.py`. Não foi executada a suíte integral.
- Navegador com dados descartáveis em `127.0.0.1:8768`: início do aluno, home, conteúdo
  em destaque, catálogo de dez questões, busca, abertura do caderno, feedback de uma
  tentativa digitada, atividades, trilhas, progresso e retorno a Exames.
- Desktop 1280 px, tablet 768 px e celular 390 px: distribuição dos cards conferida;
  sem rolagem horizontal da página nos tamanhos medidos.
- A tentativa de teste contendo `2+2=5` permaneceu inalterada na representação.
  Exames continuou com suas avaliações e zero entregas da prática.
- Comparação SHA-256 com o estado inicial desta tarefa: backend, arquivos da captura,
  renderer compartilhado, paleta e implementações docentes preservados.
- `git diff --check`: sem erros. Branch `feat/p2-teacher-decisions`; sem staging,
  commit ou push. O working tree inclui também as alterações anteriores.

Limites da verificação: S Pen físico e uma chamada real ao serviço externo Mathpix
não foram exercitados nesta rodada. A preservação da integração foi verificada pelos
testes existentes e pela ausência de alterações nos arquivos de captura. O feedback
continua demonstrativo e o histórico de tentativas continua restrito à sessão.
