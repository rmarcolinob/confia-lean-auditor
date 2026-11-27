# Inventário de publicação — 25/11/2026

Inventário anterior à criação das branches de colaboração: 48 branches locais, 16 registros de worktree (15 presentes e um cadastro obsoleto). `main` local/remota em `8fde840d95fa4df0553b915d7b60301c9892aa65`. Remoto confirmado por Git e API: `https://github.com/rmarcolinob/confia-lean-auditor.git`, público, padrão `main`, usuário autenticado proprietário com permissão de push/admin. A visibilidade foi mantida conforme orientação do mantenedor. Não foram alteradas permissões nem enviados convites.

O remoto tinha 34 branches; `luis_ocr` estava presente remotamente, sem referência de acompanhamento local. Seu desenvolvimento não foi integrado nem declarado revisado. As demais pontas remotas conferiam com o inventário local. Somente `codex/dec10-functional-integration` (19 commits) e `feat/dynamic-correction` (9 commits) continham commits ainda não alcançados pelos remotos locais; os nove últimos são ancestrais da integração. A publicação não reescreve esse histórico.

## Worktrees originais

Caminhos abreviados pelo nome da pasta, evitando depender do diretório pessoal do mantenedor. Contagens são de entradas Git, não linhas de código. Nenhum destes worktrees foi limpo, restaurado ou usado para novos commits.

| Pasta | Branch / HEAD | Modificados rastreados | Não rastreados |
| --- | --- | ---: | ---: |
| `confia-lean-auditor` | `feat/tme-dual-input` | 0 | 4009 |
| `confia-r1-attribution-baseline-5aa7344` | `detached 5aa7344` | ausente | cadastro obsoleto |
| `confia-lean-auditor-dynamic` | `feat/dynamic-correction` | 2 | 107 |
| `confia-lean-auditor-leanstrong-aug` | `detached 8f50835` | 0 | 1 |
| `confia-lean-auditor-research-archive` | `archive/research-artifacts-2026-11` | 0 | 0 |
| `confia-lean-auditor-semantic-formal-b` | `experiment/semantic-formal-b` | 0 | 0 |
| `confia-lean-auditor-semantic-formal-b-f2-complete` | `experiment/semantic-formal-b-f2-complete` | 7 | 287 |
| `confia-lean-auditor-semantic-formal-b-f2-policy-ab-01` | `experiment/semantic-formal-b-f2-policy-ab-01` | 7 | 294 |
| `confia-lean-auditor-specialized-math-assessment-c1` | `experiment/specialized-math-assessment-c1` | 7 | 39 |
| `confia-lean-auditor-specialized-semantic-c2` | `experiment/specialized-semantic-providers-c2` | 7 | 92 |
| `confia-lean-auditor-tme-december-integration` | `feat/tme-december-integration` | 0 | 0 |
| `confia-lean-auditor-tme-semantic-formal-c1` | `experiment/tme-semantic-formal-c1` | 0 | 0 |
| `confia-lean-auditor-tme-semantic-formal-p2` | `experiment/tme-semantic-formal-p2` | 0 | 0 |
| `confia-lean-auditor-tme-semantic-formal-p3` | `experiment/tme-semantic-formal-p3` | 0 | 0 |
| `confia-dec10-integration` | `codex/dec10-functional-integration` | 0 | 0 |
| `tme-semantic-understanding-01` | `codex/tme-semantic-understanding-01` | 5 | 6 |

O cadastro obsoleto em `/private/tmp` não foi removido. No principal, 4009 arquivos não rastreados incluem benchmarks ITA, experimentos Semantic B, relatórios, scripts, testes e 30 arquivos do vídeo. Esses experimentos brutos não foram misturados à candidata. O vídeo é preservado separadamente, mantendo os arquivos originais. Os demais materiais locais requerem seleção e revisão de publicação próprias; não se declara sua transferência ao remoto concluída.

Os worktrees Semantic Formal B/F2/policy, Specialized C1/C2, Leanstrong e semantic-understanding contêm trabalho experimental pendente. Não foi alterado seu núcleo matemático nem publicado automaticamente conteúdo experimental sem revisão de proveniência. As branches históricas já remotas não capturam essas diferenças locais. Inventários completos dos caminhos e hashes de preservação ficam no diretório local ignorado `artifacts/collaboration-publication-20261125/` do repositório principal.

## DYNAMIC preservado

Os **109 arquivos** do worktree `confia-lean-auditor-dynamic` (2 modificados + 107 novos) já estão preservados byte a byte no commit `74a6960`. Não há uma segunda implementação R1 perdida a importar. A integração posterior `77a5b7c` acrescenta avaliação semântica e fluxo compartilhado. `feat/dynamic-correction` conserva o marco histórico `5aa7344`; a nova `codex/dynamic-development` parte da integração atual e recebe documentação explícita de pendências. Não confundir a mensagem histórica de conclusão de integração com validação geral do DYNAMIC.

## Interface encontrada

| Commit | Mudança |
| --- | --- |
| `a5d2461` | Identidade compartilhada e navegação de modalidades; shell, CSS, workspace e testes |
| `1545955` | Professor monta componentes reais do TME²; `teacher-presentation.js/.css`, home, navegação e DYNAMIC |
| `8c17274` | Entrada, Aluno e Gestão no mesmo padrão; `platform-presentation.js/.css`, login, shell e management |
| `6739a66`, `afa82c3` | Ajustes posteriores de estados de correção incompleta/erro e integração; commits também têm backend |

As mudanças de aplicação estão commitadas na ancestralidade da RC1. Não foi encontrado diff não registrado do frontend da plataforma nos worktrees examinados. As branches antigas `feat/ui-01-shell-design-system`, `feat/ui-02-student-resolution-workspace`, `feat/ui-03-teacher-workflow` e `feat/ui-p0-professionalization` não contêm commits inéditos em relação ao remoto. O projeto Remotion `video-institucional/` é audiovisual separado, não uma substituição do frontend.

## Organização

- `codex/dec10-functional-integration` e tag RC1: referências congeladas, exatamente no snapshot existente.
- `feat/dynamic-correction`: marco histórico DY1–DY7, sem acrescentar novos commits a esse worktree.
- `codex/collaboration-handoff`: documentação e recibo pós-congelamento, derivada da RC1.
- `codex/dynamic-development`: base integrada e plano DYNAMIC; nenhuma mudança matemática nesta organização.
- `codex/interface-review`: base integrada e escopo de revisão visual; nenhuma reconstrução de frontend.
- `codex/interface-video`: fontes do vídeo anteriormente não rastreadas; sem renderizações, áudios gerados, caches ou dependências vendorizadas.

Branches derivadas compartilham a história anterior; esta separação organiza próximos commits, sem cherry-picks parciais de dependências acopladas. A `main` aguarda PRs e revisão. O status efetivo de publicação é conferido no relatório final, não inferido apenas pela existência local de uma branch.

## Branches locais no inventário inicial

| Branch | Commit | Commits ainda não alcançados pelos remotos locais |
| --- | --- | ---: |
| `add-f2q8-student-claim-checks` | `00dce19b5252` | 0 |
| `add-ita2025f2q1` | `7ed6f1126dcf` | 0 |
| `add-ita2025f2q5` | `ee86f3a7395d` | 0 |
| `add-ita2025f2q6` | `de7e069eed74` | 0 |
| `add-ita2025f2q8-strong` | `d9820a830e96` | 0 |
| `add-ita2025q3` | `33e5a5ef99aa` | 0 |
| `add-ita2025q5` | `21a0b8e5ec9c` | 0 |
| `add-ita2025q8` | `b08a6c3e0311` | 0 |
| `archive/leanstrong-aug` | `8f50835f9391` | 0 |
| `archive/research-artifacts-2026-11` | `18538f667c47` | 0 |
| `benchmark-f2-strong-suite` | `9fc5465c7b2b` | 0 |
| `codex/dec10-functional-integration` | `c03403fe5b83` | 19 |
| `codex/tme-semantic-understanding-01` | `30260b398dd8` | 0 |
| `experiment/semantic-formal-b` | `47ed3c031abe` | 0 |
| `experiment/semantic-formal-b-f2-complete` | `47ed3c031abe` | 0 |
| `experiment/semantic-formal-b-f2-policy-ab-01` | `47ed3c031abe` | 0 |
| `experiment/specialized-math-assessment-c1` | `47ed3c031abe` | 0 |
| `experiment/specialized-semantic-providers-c2` | `47ed3c031abe` | 0 |
| `experiment/tme-semantic-formal-c1` | `34732d445ff1` | 0 |
| `experiment/tme-semantic-formal-p2` | `1165dbf62f85` | 0 |
| `experiment/tme-semantic-formal-p3` | `f9794167403f` | 0 |
| `feat/core-auth-rbac` | `04a2011e92f5` | 0 |
| `feat/core-institutional-hierarchy` | `110967b173b1` | 0 |
| `feat/dynamic-correction` | `5aa7344e5904` | 9 |
| `feat/gov-01-audit-reproducibility` | `8f3c1220f2f6` | 0 |
| `feat/p2-assessments` | `33fa7474bc1a` | 0 |
| `feat/p2-cap-01-tablet` | `5166cadd18e8` | 0 |
| `feat/p2-cap-02-submissions` | `44fbcd57b496` | 0 |
| `feat/p2-cap-03-transcription` | `60d895ca456f` | 0 |
| `feat/p2-cap-03b-recognition` | `e3a885f50aa9` | 0 |
| `feat/p2-cap-04-audit-bridge` | `d73fbf9d137d` | 0 |
| `feat/p2-hmer-mathpix-strokes` | `25c1c7bba6d5` | 0 |
| `feat/p2-teacher-decisions` | `8fde840d95fa` | 0 |
| `feat/tme-december-integration` | `cb1df6e381fd` | 0 |
| `feat/tme-dual-input` | `1b3daea41ba4` | 0 |
| `feat/ui-01-shell-design-system` | `e65835293325` | 0 |
| `feat/ui-02-student-resolution-workspace` | `52d7817e7c20` | 0 |
| `feat/ui-03-teacher-workflow` | `fb20bc0fc519` | 0 |
| `feat/ui-p0-professionalization` | `7c634a7192df` | 0 |
| `fix/ci-assessment-contracts` | `f270e3ddb9f6` | 0 |
| `harden-v5-1` | `a52163f55a62` | 0 |
| `harden-v5-2` | `ee86f3a7395d` | 0 |
| `main` | `8fde840d95fa` | 0 |
| `modularize-problem-modules` | `c103a4fdfe93` | 0 |
| `standardize-student-claim-pattern` | `c847464ef6c0` | 0 |
| `strengthen-ita2025f2q3` | `1c8204bff4eb` | 0 |
| `strengthen-ita2025f2q5` | `9f4b13ee865a` | 0 |
| `strengthen-ita2025f2q6` | `f6d38cdd5bf9` | 0 |
