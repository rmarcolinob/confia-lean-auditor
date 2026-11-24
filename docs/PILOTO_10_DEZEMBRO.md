# Piloto integrado de 10/12/2026

Implementação em `codex/dec10-functional-integration`, derivada de
`feat/dynamic-correction` (`5aa7344`). O commit `74a6960` preserva todos os
109 arquivos locais do trabalho R1, incluindo experimentos e resultados.
Os worktrees originais não foram usados como destino das alterações.

## Iniciar localmente

Na raiz do worktree de integração, com as dependências Python instaladas:

```sh
python scripts/pilot_dec10.py --port 8010
```

Neste computador, o interpretador já disponível é
`/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`.
O launcher importa o código do próprio worktree, mesmo usando esse interpretador.
O armazenamento padrão é `runtime/pilot-dec10`, isolado dos outros ambientes.
Use `--data-dir CAMINHO` para outra base. O servidor é uma demonstração local,
sem autenticação, restrita a `127.0.0.1`; não é um comando de implantação pública.

- `/` e `/#platform/home`: entrada geral, com os três módulos e identificação
  explícita da demonstração local ou da sessão institucional.
- `/#teacher/home`: área do Professor, com SPECIALIZED, DYNAMIC, fila,
  resultados e os acessos institucionais existentes.
- `/tme?view=new`: seleção SPECIALIZED / DYNAMIC, com retorno à área do Professor.
- `/#student/home` e `/#management/home`: áreas preservadas do Aluno e da Gestão.
  A seleção de perfis é demonstrativa quando a autenticação está desativada;
  em sessão autenticada, o perfil continua definido pelo servidor.
- As atividades institucionais exigem sessão e vínculos de escola/turma.
  O piloto local apresenta essa limitação na interface, sem remover o 401.
- SPECIALIZED: selecionar avaliação preparada, receber a solução, revisar/aceitar
  a transcrição e executar a auditoria. TME² conserva a pauta e a escala de 20.
- DYNAMIC: criar atividade/prova, adicionar o enunciado, abrir “Revisar Q…”,
  fornecer e salvar critérios, aprovar a rubrica e voltar à avaliação para ativá-la.
  A rubrica docente recebe um registro local de contexto automaticamente;
  não exige uma solução de referência gerada, microclaims, checker ou arquivo Lean.
- Receber as soluções na avaliação ativa; aceitar a transcrição, executar a
  auditoria, solicitar revisão independente e reconciliar. Confirmar a sugestão
  na interface compartilhada antes do fechamento e da disponibilização do feedback.

## Apresentação docente baseada no TME²

A página `/#teacher/home` monta o próprio `ConfiaTmeHome.TmeHome`, com seis
atalhos docentes. Cabeçalho, ícones, CTA, cards, métricas, fila, progresso,
carregamento e erro reutilizam `tme/home.js` e `tme/home.css`. O resumo usa o
GET já existente `/tme/home-summary`; falha de carregamento não vira contagem zero.
A folha de estilos do TME é ativada pelo adaptador do Professor. A entrada,
o Aluno e a Gestão reutilizam a mesma folha por um adaptador separado, descrito
abaixo, preservando a geometria do caderno e do assistente.

A barra lateral anterior fica oculta no Professor. Recursos complementares
permanecem no menu do cabeçalho; os seletores de escola/turma continuam nas
telas institucionais. SPECIALIZED e DYNAMIC abrem no workspace existente,
com o mesmo cabeçalho, sem a faixa adicional de links. Os formulários de avaliação
DYNAMIC reutilizam `tme-new-form`, sem alteração dos seus eventos ou contratos.
A marca ConfIA retorna ao início do Professor. No celular a navegação usa a
barra inferior já existente do TME².

Validação visual local: comparação de `/tme` e `/#teacher/home`, desktop,
tablet (768 px), celular (390 px), entradas SPECIALIZED/DYNAMIC, menu,
atividades institucionais, TutorIA/caderno e entrada da Gestão. A consulta de
dados institucionais completos requer uma sessão autenticada; a demonstração
não substitui essa validação. Os testes cobrem os perfis autenticados.
As capturas estão em `artifacts/integration-checks/teacher-visual-v2/`.

Regressão desta alteração: 573 testes JavaScript aprovados e 57 casos Python
relevantes aprovados (autenticação, isolamento institucional, avaliações,
integração SPECIALIZED/DYNAMIC e acessibilidade). As duas verificações antigas
que proibiam a palavra “Professor” no HTML foram atualizadas para admitir o
link de retorno e continuar proibindo seleção de perfil/login na tela demo.
Nenhuma chamada paga foi realizada.

## Unidade visual da entrada, Aluno e Gestão

A apresentação aprovada do Professor (`1545955`) permanece como referência.
`platform-presentation.js` reutiliza os componentes reais `QuickActions`,
`HeroIllustration`, ícones e classes do TME². `platform-presentation.css`
adapta os três novos contextos com os tokens existentes; seus seletores não
atingem o Professor. O Professor e `/tme` receberam apenas o link de retorno
à entrada geral. Seus componentes, apresentação e lógica não foram reconstruídos.

A entrada tem três cartões de acesso. Em sessão institucional, somente o
cartão do perfil autorizado fica habilitado; no login, os cartões levam o foco
ao formulário existente. A escolha nunca atribui um perfil. Login, logout,
restrições de rota, contratos e regras do servidor continuam os existentes.

O Aluno conserva os nós de identificação e vínculo institucional, o TutorIA,
atividades, submissões e todo o workspace de resolução. Durante a escrita, a
navegação do módulo fica oculta e o cabeçalho compacto; o caderno e a reserva
de espaço para o assistente mantêm seus próprios controles de dimensão.
A Gestão mostra o painel existente também no início, com os mesmos indicadores,
consultas, tabelas e detalhamento de escola/turma. Sem sessão autorizada, mostra
a indisponibilidade em vez de deixar uma mensagem permanente de carregamento.

Validação visual em 24/11/2026, desktop (1280 px) e celular (390 px): entrada,
Professor preservado, Aluno, Gestão, navegação e retorno ao início. Também foram
verificados os links diretos, TutorIA, seleção de questão, enunciado recolhível,
adição de página no caderno e preservação da página em andamento após sair e
voltar ao módulo. No desktop, o TutorIA lateral não sobrepôs a área de escrita.

Para conferir os indicadores e permissões com dados reais do servidor, foi
usada uma instância autenticada temporária em `127.0.0.1:8011`, com base isolada
de teste (uma escola, uma turma, um aluno e um professor). As capturas da Gestão
mostram esses registros de teste e contagens calculadas pelo backend existente;
nenhum indicador foi inventado no frontend nem inserido no piloto. Foram
verificados o detalhamento institucional, o bloqueio de outro perfil e o logout.
Essa instância foi encerrada após a inspeção. O piloto em `8010` continua sem
sessão institucional: o acesso aos dados protegidos depende de autenticação.

Regressão: **582 testes JavaScript aprovados e 65 casos Python relevantes
aprovados**. Na primeira execução Python, dois testes falharam: o texto estático
completo da marca no login foi restaurado e a verificação de vocabulário passou
a incluir os arquivos onde o relatório já era renderizado. A reexecução dos dois
arquivos afetados aprovou seus 14 casos; os outros 51 já haviam passado.
Não houve alteração de correção, rubricas, pontuação, persistência ou autenticação,
nem chamadas pagas ou execução de inferência na validação visual.

Capturas e logs locais: `artifacts/integration-checks/platform-visual-v3/`.
As imagens principais são `inicio-desktop.jpg`, `professor-desktop.jpg`,
`aluno-desktop.jpg` e `gestao-desktop.jpg`. Há também a Gestão completa, versões
móveis e capturas do caderno com TutorIA.

Arquivos desta etapa (relativos à raiz do worktree):

- `app/confia_lean_auditor/static/platform-presentation.js` e `.css` (novos);
- `app/confia_lean_auditor/static/index.html`, `login.html` e `auth.css`;
- `app/confia_lean_auditor/static/shell.js` e `management.js`;
- `app/confia_lean_auditor/static/tme/home.js` (exportação de componentes
  existentes) e `tme/index.html` (retorno à entrada);
- `tests/js/test_platform_presentation.cjs` (novo),
  `tests/js/test_ui_01_shell.cjs` e `tests/test_ui_01_shell.py`;
- `docs/PILOTO_10_DEZEMBRO.md`.

## Providers e estados

O launcher não habilita inferência paga. Sem provider, os critérios que precisam
de avaliação semântica ficam pendentes com falha técnica registrada; o sistema
não inventa uma nota. Os testes usam providers simulados, nunca um modelo falso
injetado no servidor do piloto.

Após autorização explícita para chamadas reais, o provider semântico usa
`OPENAI_API_KEY` e `CONFIA_SEMANTIC_LLM_ENABLED=1`. O modelo padrão é
`gpt-6.1-sol`, esforço `medium`, como no experimento de referência; ajustes ficam
em `CONFIA_SEMANTIC_MODEL` e `CONFIA_SEMANTIC_REASONING_EFFORT`.
Cada chamada tem timeout de 60 segundos, sem retry automático, e limite de 4.000
tokens de saída. A disponibilidade do identificador do modelo deve ser conferida
na conta usada para o piloto. Não houve chamada paga nesta integração.

As sugestões automáticas de preparação/rubrica usam o provider DYNAMIC já
existente: exigem separadamente `CONFIA_DYNAMIC_LLM_ENABLED=1` e a chave,
com `CONFIA_DYNAMIC_MODEL` e `CONFIA_DYNAMIC_REASONING_EFFORT` opcionais.
O professor pode usar a entrada manual sem habilitar essa geração.

O fallback retorna apenas `met`, `not_met` ou `review`, justificativa e citações
literais. O código aplica os pontos da rubrica. O Grader mantém as decisões exatas
e usa fallback nas pendências. O Reviewer recebe enunciado, rubrica, solução e
evidência matemática, sem a decisão do Grader. A reconciliação preserva a
distinção entre concordância semântica, verificação exata e certificação formal.

`not_met` conclusivo pode produzir zero. Abstenção, divergência ou falha técnica
deixam o total pendente (`null`) e bloqueiam a confirmação dessa sugestão.
Uma sugestão semântica concordante ainda exige confirmação docente.
Requests, respostas, hashes, citações, versão da política e metadados do provider
ficam nos artefatos existentes de auditoria/revisão/reconciliação.

O custo semântico é limitado a uma chamada por critério elegível no SPECIALIZED;
no DYNAMIC há uma por critério pendente no Grader e uma por critério no Reviewer.
São chamadas sequenciais: a latência aumenta com o número de critérios. Repetir
a mesma execução persistida não chama o provider novamente. Uma nova revisão
explícita pode gerar novas chamadas. Não foi feito benchmark de custo/latência.

## Reversão

Parar o servidor e iniciar com a mesma base:

```sh
python scripts/pilot_dec10.py --port 8010 --legacy
```

Equivale a `CONFIA_SPECIALIZED_POLICY=legacy` e `CONFIA_DYNAMIC_POLICY=legacy`.
As novas configurações usam a política anterior. Auditorias, revisões e avaliações
DYNAMIC já publicadas mantêm a política fixada nos respectivos registros;
não são reinterpretadas ou apagadas. Para corrigir com outra política, criar uma
nova configuração/tentativa/publicação, preservando as anteriores.

## Verificação local

```sh
PYTHONPATH=app python -m pytest tests/test_dec10_integration.py tests/test_dec10_specialized.py -q
node --test tests/js/test_*.cjs
```

Os testes funcionais cobrem ITA sem dupla adjudicação, TME² com PautaEngine,
questão inédita fora do parser de equações, rubrica docente, Grader, Reviewer
cego, reconciliação, submissão/transcrição, persistência, confirmação/fechamento,
abstenção, falha técnica, zero e leitura do histórico após reversão.
São testes de integração e contratos, não validação da acurácia matemática GPT.

Lean requer o toolchain de `lean-toolchain` e o cache `.lake` correspondente.
O cache local foi copiado com clone de arquivos para este worktree, sem substituir
checkers ou alterar o ambiente original. Não se deve interpretar erro de instalação
Lean como refutação matemática.

A validação matemática extensa com gold humano e a avaliação dos providers reais
continuam pendentes. A aprovação operacional do piloto deve considerar essas
limitações, além dos resultados dos testes locais.
