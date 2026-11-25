# Interface — base preservada para revisão

Esta branch contém a interface integrada da RC1, com documentação de colaboração. Nenhum componente visual foi refeito nesta organização. A interface aprovada do Professor/TME² continua sendo a referência.

| Origem | Conteúdo preservado |
| --- | --- |
| `a5d2461` | Primeira harmonização de shell, navegação, estilos e acesso às modalidades |
| `1545955` | Professor usa `ConfiaTmeHome.TmeHome` e componentes TME reais; `teacher-presentation.js/.css` |
| `8c17274` | Entrada, Aluno e Gestão harmonizados; `platform-presentation.js/.css`, login, shell e management |
| `6739a66`, `afa82c3` | Estados posteriores de correção incompleta/falha; preservar com a integração backend correspondente |

Arquivos centrais: `app/confia_lean_auditor/static/tme/home.js`, `home.css`, `teacher-presentation.js`, `platform-presentation.js`, seus CSS, `shell.js`, `index.html`, `management.js`, `resolution-workspace.js` e os módulos existentes de caderno/TutorIA. A raiz `static/tme/` é a referência do padrão TME²; os adaptadores de Professor e plataforma ficam diretamente em `static/`.

Não foi encontrado frontend da aplicação modificado e ainda não registrado nos worktrees inventariados. As branches UI antigas têm commits já alcançáveis no remoto. As fontes de `video-institucional/` são outro produto, preservadas em `codex/interface-video` e não adicionadas a esta branch.

## Revisão futura

- Abrir `/`, `/#teacher/home`, `/#student/home`, `/#management/home` e `/tme` no piloto local.
- Conferir desktop/mobile, foco/teclado, estados vazios/erro/carregamento e retorno à entrada.
- Preservar o espaço de escrita, ferramentas, contexto por questão, autosave e submissões do caderno; preservar TutorIA e históricos.
- Preservar dashboards/indicadores reais, filtros e permissões. Não preencher indisponibilidade com números fictícios.
- Manter distinção entre demonstração local e sessão institucional; selecionar módulo não concede um papel no servidor.
- Propor mudanças em PRs pequenos; não cherry-pickar isoladamente commits que misturam estados de UI e integração de correção.

Validação desta organização: 45 testes JS de navegação, apresentação, login e workspace aprovados; testes Python dirigidos de autorização e integração também aprovados. Não houve novo ensaio visual no navegador nem nova validação de captura manuscrita nesta tarefa de publicação. As capturas e relatos anteriores continuam disponíveis em `docs/audits/`.
