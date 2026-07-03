# Auditoria descritiva do repositório

## 1. Visão geral do projeto

O projeto se identifica como `confia-lean-auditor`, versão Python `0.1.0`, com domínio descrito como corretor matemático com rubrica e certificados Lean em `pyproject.toml:6`, `pyproject.toml:7` e `pyproject.toml:8`. O pacote Python exige `>=3.9` e declara `fastapi`, `uvicorn`, `pydantic>=2` e `pytest` em `pyproject.toml:9`, `pyproject.toml:11`, `pyproject.toml:12`, `pyproject.toml:13` e `pyproject.toml:14`. O runtime Lean é `leanprover/lean4:v4.28.0` em `lean-toolchain:1`; Lake declara `confia_lean_auditor`, alvo padrão `ConfiaLeanAuditor`, mathlib `v4.28.0` e biblioteca `ConfiaLeanAuditor` em `lakefile.toml:1`, `lakefile.toml:4`, `lakefile.toml:13`, `lakefile.toml:15` e `lakefile.toml:18`.

Terreno detectado: monolito pequeno em camadas, com API FastAPI, heurísticas textuais, contratos JSON em `problems/`, geração de arquivos Lean em `artifacts/`, subprocess `lake env lean` e CI Lean via GitHub Actions. A árvore local contém `.lake/` ignorado por `.gitignore:1` e `.venv/` versionado parcialmente pelo Git; `git ls-files .venv | wc -l` indicou 1870 arquivos rastreados de ambiente, enquanto `pyproject.toml` já declara as dependências de runtime em `pyproject.toml:10`. Esta auditoria aprofunda os 87 arquivos de primeira parte visíveis fora de `.venv/` e `.lake/`; a presença de `.venv/` versionado é tratada como achado transversal, não como código próprio.

Inventário cru operacional: 87 arquivos fora de `.git`, `.lake` e `.venv`, incluindo `.github/`, `.gitignore`, manifestos, código Python, Lean, problemas, exemplos, egg-info, artefatos de execução e este relatório. A árvore completa local também contém caches e dependências materializadas; `.lake` é explicitamente ignorado em `.gitignore:1`, mas `.venv/pyvenv.cfg` existe e fixa Python `3.9.6` em `.venv/pyvenv.cfg:3`.

Módulos em uma linha: `main.py` expõe `/health` e `/audit` em `app/confia_lean_auditor/main.py:27` e `app/confia_lean_auditor/main.py:36`; `schemas.py` define os contratos Pydantic em `app/confia_lean_auditor/core/schemas.py:8`, `app/confia_lean_auditor/core/schemas.py:13`, `app/confia_lean_auditor/core/schemas.py:100`; `paths.py` resolve raiz e `problem_id` em `app/confia_lean_auditor/core/paths.py:15` e `app/confia_lean_auditor/core/paths.py:34`; `extract_claims.py` extrai claims e passos formais para `ITA2025Q1` em `app/confia_lean_auditor/claims/extract_claims.py:72` e `app/confia_lean_auditor/claims/extract_claims.py:117`; `formal_step_evaluator.py` gera Lean por passo em `app/confia_lean_auditor/lean/formal_step_evaluator.py:19`; `build_attempt.py` gera `Attempt.lean` em `app/confia_lean_auditor/lean/build_attempt.py:127`; `run_lean.py` chama `lake env lean` em `app/confia_lean_auditor/lean/run_lean.py:69`; `microclaim_evaluator.py` lê `microclaims.json` em `app/confia_lean_auditor/lean/microclaim_evaluator.py:47`; `rubric_evaluator.py` lê `rubric.json` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:23`; `report_builder.py` monta feedback em `app/confia_lean_auditor/reports/report_builder.py:31`; `ConfiaLeanAuditor.lean` importa módulos Lean em `ConfiaLeanAuditor.lean:1` e `ConfiaLeanAuditor.lean:2`; `ConfiaLeanAuditor/Basic.lean` mantém scaffold `hello` em `ConfiaLeanAuditor/Basic.lean:1`.

## 2. Diagrama de arquitetura textual

```
Cliente HTTP
  -> FastAPI app
     -> GET /health
     -> POST /audit: AuditRequest(problem_id, solution)
        -> get_repo_root()
        -> get_problem_dir(root, problem_id)
        -> artifacts/runs/{run_id}/
        -> extract_claims(problem_id, solution)
        -> evaluate_formal_steps(...): formal_steps/*.lean -> lake env lean
        -> build_attempt(...): Attempt.lean
        -> run_lean_file(...): lake env lean Attempt.lean
        -> evaluate_microclaims(...): problems/{problem_id}/microclaims.json
        -> evaluate_rubric(...): problems/{problem_id}/rubric.json
        -> verdict_from_score + build_feedback
        -> AuditResponse
        -> audit.json, solution.txt, claims.json

CLI Python
  -> python app/confia_lean_auditor/lean/run_lean.py --problem-id X --repo-root .
     -> problems/{problem_id}/certificate/Statement.lean
     -> lake env lean
     -> JSON em stdout

Lake / Lean
  -> lakefile.toml defaultTargets ["ConfiaLeanAuditor"]
     -> ConfiaLeanAuditor.lean
        -> ConfiaLeanAuditor.Basic
        -> ConfiaLeanAuditor.Problems.ITA2025Q1.Statement

GitHub Actions
  -> lean_action_ci.yml: checkout -> lean-action -> docgen-action
  -> create-release.yml: lean-release-tag em mudança de lean-toolchain
  -> update.yml: mathlib-update-action manual
```

O fluxo HTTP cria `artifact_dir` em `app/confia_lean_auditor/main.py:48`, `app/confia_lean_auditor/main.py:49` e `app/confia_lean_auditor/main.py:50`, grava `audit.json`, `solution.txt` e `claims.json` em `app/confia_lean_auditor/main.py:123`, `app/confia_lean_auditor/main.py:128` e `app/confia_lean_auditor/main.py:129`, e retorna `AuditResponse` em `app/confia_lean_auditor/main.py:109` e `app/confia_lean_auditor/main.py:134`. O fluxo CLI monta `certificate/Statement.lean` em `app/confia_lean_auditor/lean/run_lean.py:115`, verifica existência em `app/confia_lean_auditor/lean/run_lean.py:117` e imprime JSON em `app/confia_lean_auditor/lean/run_lean.py:138`.

## 3. Grafo de dependências

### Python: imports estáticos

- `app/confia_lean_auditor/main.py` importa FastAPI em `app/confia_lean_auditor/main.py:7`, extrator em `app/confia_lean_auditor/main.py:9`, paths em `app/confia_lean_auditor/main.py:10`, schemas em `app/confia_lean_auditor/main.py:11`, build Lean em `app/confia_lean_auditor/main.py:12`, avaliação formal em `app/confia_lean_auditor/main.py:13`, microclaims em `app/confia_lean_auditor/main.py:14`, runner Lean em `app/confia_lean_auditor/main.py:15`, report em `app/confia_lean_auditor/main.py:16` e rubrica em `app/confia_lean_auditor/main.py:17`.
- `claims/extract_claims.py` importa `re`, `unicodedata` e tipos em `app/confia_lean_auditor/claims/extract_claims.py:3`, `app/confia_lean_auditor/claims/extract_claims.py:4` e `app/confia_lean_auditor/claims/extract_claims.py:5`, e importa `ClaimExtraction`, `ExtractedClaim` e `FormalStep` de schemas em `app/confia_lean_auditor/claims/extract_claims.py:7`.
- `core/paths.py` importa `os`, `re` e `Path` em `app/confia_lean_auditor/core/paths.py:3`, `app/confia_lean_auditor/core/paths.py:4` e `app/confia_lean_auditor/core/paths.py:5`.
- `core/schemas.py` importa `BaseModel` e `Field` de Pydantic em `app/confia_lean_auditor/core/schemas.py:5`.
- `lean/build_attempt.py` importa `ClaimExtraction` e `FormalStepResult` em `app/confia_lean_auditor/lean/build_attempt.py:6`.
- `lean/formal_step_evaluator.py` importa schemas em `app/confia_lean_auditor/lean/formal_step_evaluator.py:6` e `run_lean_file` em `app/confia_lean_auditor/lean/formal_step_evaluator.py:11`.
- `lean/microclaim_evaluator.py` importa `get_problem_dir` em `app/confia_lean_auditor/lean/microclaim_evaluator.py:7` e schemas em `app/confia_lean_auditor/lean/microclaim_evaluator.py:8`.
- `lean/run_lean.py` importa `subprocess` em `app/confia_lean_auditor/lean/run_lean.py:6` e `get_problem_dir` em `app/confia_lean_auditor/lean/run_lean.py:10`.
- `reports/report_builder.py` importa schemas em `app/confia_lean_auditor/reports/report_builder.py:5`.
- `rubric/rubric_evaluator.py` importa `get_problem_dir` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:7` e schemas em `app/confia_lean_auditor/rubric/rubric_evaluator.py:8`.

### Python: imports inversos

- `core/schemas.py` é consumido por extrator, build, formal step, microclaim, report, rubric e main em `app/confia_lean_auditor/claims/extract_claims.py:7`, `app/confia_lean_auditor/lean/build_attempt.py:6`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:6`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:8`, `app/confia_lean_auditor/reports/report_builder.py:5`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:8` e `app/confia_lean_auditor/main.py:11`.
- `core/paths.py` é consumido por main, microclaims, rubrica e runner Lean em `app/confia_lean_auditor/main.py:10`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:7`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:7` e `app/confia_lean_auditor/lean/run_lean.py:10`.
- `claims/extract_claims.py`, `lean/build_attempt.py`, `lean/formal_step_evaluator.py`, `lean/microclaim_evaluator.py`, `lean/run_lean.py`, `reports/report_builder.py` e `rubric/rubric_evaluator.py` entram no fluxo HTTP via `main.py` em `app/confia_lean_auditor/main.py:9`, `app/confia_lean_auditor/main.py:12`, `app/confia_lean_auditor/main.py:13`, `app/confia_lean_auditor/main.py:14`, `app/confia_lean_auditor/main.py:15`, `app/confia_lean_auditor/main.py:16` e `app/confia_lean_auditor/main.py:17`.
- Os `__init__.py` de pacote têm zero linhas na contagem operacional; eles existem para marcação de pacote, sem exportações próprias, e aparecem como pacote raiz em `app/confia_lean_auditor.egg-info/top_level.txt:1`.

### Lean: imports estáticos e inversos

- `ConfiaLeanAuditor.lean` importa `ConfiaLeanAuditor.Basic` e `ConfiaLeanAuditor.Problems.ITA2025Q1.Statement` em `ConfiaLeanAuditor.lean:1` e `ConfiaLeanAuditor.lean:2`.
- `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean` importa `Mathlib` em `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:1` e define o namespace do problema em `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:3`.
- `problems/ITA2025Q1/certificate/Statement.lean` importa o statement do pacote em `problems/ITA2025Q1/certificate/Statement.lean:1`; `run_lean.py` procura exatamente este arquivo para o modo CLI em `app/confia_lean_auditor/lean/run_lean.py:115`.
- `build_attempt.py` e `formal_step_evaluator.py` produzem strings Lean que importam `ConfiaLeanAuditor.Problems.ITA2025Q1.Statement` em `app/confia_lean_auditor/lean/build_attempt.py:10` e `app/confia_lean_auditor/lean/formal_step_evaluator.py:23`.

### Acoplamento dinâmico

- `CONFIA_LEAN_AUDITOR_ROOT` altera a raiz em runtime em `app/confia_lean_auditor/core/paths.py:16`, `app/confia_lean_auditor/core/paths.py:17` e `app/confia_lean_auditor/core/paths.py:18`.
- `problem_id` vira caminho de filesystem em `app/confia_lean_auditor/core/paths.py:34`, `app/confia_lean_auditor/core/paths.py:37` e `app/confia_lean_auditor/core/paths.py:38`; a regex restringe caracteres em `app/confia_lean_auditor/core/paths.py:8` e `app/confia_lean_auditor/core/paths.py:26`.
- `rubric_evaluator.py` e `microclaim_evaluator.py` carregam JSON por nome fixo em `app/confia_lean_auditor/rubric/rubric_evaluator.py:23`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:28`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:47` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:52`.
- `build_attempt.py` escreve `Attempt.lean` em `app/confia_lean_auditor/lean/build_attempt.py:127` e `app/confia_lean_auditor/lean/build_attempt.py:128`; `formal_step_evaluator.py` cria `formal_steps` e escreve um arquivo por passo em `app/confia_lean_auditor/lean/formal_step_evaluator.py:55`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:62` e `app/confia_lean_auditor/lean/formal_step_evaluator.py:63`.
- `run_lean.py` executa `lake env lean` via subprocess com timeout em `app/confia_lean_auditor/lean/run_lean.py:69`, `app/confia_lean_auditor/lean/run_lean.py:72` e `app/confia_lean_auditor/lean/run_lean.py:78`.
- CI consome ações externas em `.github/workflows/lean_action_ci.yml:19`, `.github/workflows/lean_action_ci.yml:20`, `.github/workflows/lean_action_ci.yml:21`, `.github/workflows/create-release.yml:19` e `.github/workflows/update.yml:17`.

### Ciclos e órfãos

Não há ciclo estático entre os módulos Python próprios: `main.py` orquestra dependências e os módulos importados não importam `main.py`, conforme as arestas listadas acima. O arquivo `ConfiaLeanAuditor/Basic.lean` é candidato confirmado a scaffold sem consumidor semântico: ele só é importado pelo agregador `ConfiaLeanAuditor.lean:1` e contém apenas `def hello := "world"` em `ConfiaLeanAuditor/Basic.lean:1`. `README.md` é scaffold de GitHub gerado, com instrução de remoção em `README.md:13`. Os artefatos em `artifacts/runs/**` são saídas versionadas por acidente operacional: `main.py` escreve esses caminhos em `app/confia_lean_auditor/main.py:123`, `app/confia_lean_auditor/main.py:128` e `app/confia_lean_auditor/main.py:129`, e há instâncias versionadas como `artifacts/runs/20260703T144140_097860/audit.json:1`, `artifacts/runs/20260703T144140_097860/claims.json:1` e `artifacts/runs/20260703T144140_097860/solution.txt:1`.

## 4. Pontos de entrada e saída consolidados

Entradas: `GET /health` em `app/confia_lean_auditor/main.py:27`; `POST /audit` com `AuditRequest` em `app/confia_lean_auditor/main.py:36` e `app/confia_lean_auditor/core/schemas.py:8`; CLI `run_lean.py` em `app/confia_lean_auditor/lean/run_lean.py:131` e `app/confia_lean_auditor/lean/run_lean.py:141`; Lake default target em `lakefile.toml:4`; CI em `.github/workflows/lean_action_ci.yml:3`, `.github/workflows/create-release.yml:3` e `.github/workflows/update.yml:3`.

Saídas: resposta HTTP `AuditResponse` em `app/confia_lean_auditor/core/schemas.py:100` e `app/confia_lean_auditor/main.py:109`; `artifacts/runs/{run_id}/audit.json` em `app/confia_lean_auditor/main.py:123`; `solution.txt` em `app/confia_lean_auditor/main.py:128`; `claims.json` em `app/confia_lean_auditor/main.py:129`; `Attempt.lean` em `app/confia_lean_auditor/lean/build_attempt.py:127`; `formal_steps/*.lean` em `app/confia_lean_auditor/lean/formal_step_evaluator.py:62`; JSON stdout da CLI em `app/confia_lean_auditor/lean/run_lean.py:138`; documentação Pages no CI por `docgen-action` em `.github/workflows/lean_action_ci.yml:21`.

Contratos produtor/consumidor: `ClaimExtraction.formal_steps` é produzido em `app/confia_lean_auditor/claims/extract_claims.py:207` e consumido em `app/confia_lean_auditor/lean/formal_step_evaluator.py:60`; `FormalStepResult.status` é produzido em `app/confia_lean_auditor/lean/formal_step_evaluator.py:67` e consumido para liberar teorema de área em `app/confia_lean_auditor/lean/build_attempt.py:93` e `app/confia_lean_auditor/lean/build_attempt.py:113`; `generated_theorems` é produzido em `app/confia_lean_auditor/lean/build_attempt.py:107`, `app/confia_lean_auditor/lean/build_attempt.py:111`, `app/confia_lean_auditor/lean/build_attempt.py:115`, `app/confia_lean_auditor/lean/build_attempt.py:119` e `app/confia_lean_auditor/lean/build_attempt.py:123`, depois consumido em `app/confia_lean_auditor/lean/microclaim_evaluator.py:55` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:74`; `required_microclaim_ids` vem de `problems/ITA2025Q1/rubric.json:10`, `problems/ITA2025Q1/rubric.json:17`, `problems/ITA2025Q1/rubric.json:24`, `problems/ITA2025Q1/rubric.json:31` e `problems/ITA2025Q1/rubric.json:38`, e é consumido em `app/confia_lean_auditor/rubric/rubric_evaluator.py:49` e `app/confia_lean_auditor/rubric/rubric_evaluator.py:54`.

## 5. Análise módulo a módulo

### Lote 1: arquivos 1-10

#### Analisado 1 de 87 — .github/workflows/create-release.yml
Responsabilidade: cria tag/release Lean quando `lean-toolchain` muda nos branches `main` ou `master`, conforme `.github/workflows/create-release.yml:3`, `.github/workflows/create-release.yml:5` e `.github/workflows/create-release.yml:9`.
Fluxo de dados: consome evento de push e `GITHUB_TOKEN`, chama ação externa em `.github/workflows/create-release.yml:18` e `.github/workflows/create-release.yml:19`.
Entradas/saídas: entrada é push em `lean-toolchain`; saída é release/tag pela action com `do-release: true` em `.github/workflows/create-release.yml:21`.
Padrões: workflow declarativo de automação CI.
Anti-padrões e smells: permissão `contents: write` concede escrita ao job em `.github/workflows/create-release.yml:16`; ação externa é fixada só por major `@v1` em `.github/workflows/create-release.yml:19`.
Risco de refatoração: MÉDIO, por escrever no repositório via token.
<file-analyzed/>

#### Analisado 2 de 87 — .github/workflows/lean_action_ci.yml
Responsabilidade: executa build Lean e geração de documentação em push, pull request e dispatch em `.github/workflows/lean_action_ci.yml:3`, `.github/workflows/lean_action_ci.yml:4`, `.github/workflows/lean_action_ci.yml:5` e `.github/workflows/lean_action_ci.yml:6`.
Fluxo de dados: checkout do repositório, Lean Action e docgen em `.github/workflows/lean_action_ci.yml:19`, `.github/workflows/lean_action_ci.yml:20` e `.github/workflows/lean_action_ci.yml:21`.
Entradas/saídas: entrada é evento GitHub; saída é build e possível Pages/docgen com permissões em `.github/workflows/lean_action_ci.yml:9`, `.github/workflows/lean_action_ci.yml:11` e `.github/workflows/lean_action_ci.yml:12`.
Padrões: CI declarativo.
Anti-padrões e smells: `actions/checkout@v5`, `lean-action@v1` e `docgen-action@v1` são referências por major, não por SHA, em `.github/workflows/lean_action_ci.yml:19`, `.github/workflows/lean_action_ci.yml:20` e `.github/workflows/lean_action_ci.yml:21`.
Risco de refatoração: MÉDIO, por impactar validação Lean e publicação de docs.
<file-analyzed/>

#### Analisado 3 de 87 — .github/workflows/update.yml
Responsabilidade: workflow manual para procurar e aplicar updates de mathlib em `.github/workflows/update.yml:1`, `.github/workflows/update.yml:6`, `.github/workflows/update.yml:17` e `.github/workflows/update.yml:35`.
Fluxo de dados: job `check-for-updates` produz outputs em `.github/workflows/update.yml:11`, `.github/workflows/update.yml:12` e `.github/workflows/update.yml:13`; job `do-update` consome matriz de tags em `.github/workflows/update.yml:30` e `.github/workflows/update.yml:31`.
Entradas/saídas: entrada manual; saídas são PR ou issue em `.github/workflows/update.yml:39` e `.github/workflows/update.yml:40`.
Padrões: pipeline de atualização com job dependente.
Anti-padrões e smells: schedule comentado deixa atualização automática inativa em `.github/workflows/update.yml:4`; permissões de escrita para contents, issues e pull-requests aparecem em `.github/workflows/update.yml:23`, `.github/workflows/update.yml:24` e `.github/workflows/update.yml:25`.
Risco de refatoração: MÉDIO, por automatizar mudanças em dependência central.
<file-analyzed/>

#### Analisado 4 de 87 — .gitignore
Responsabilidade: ignora somente diretório Lake local em `.gitignore:1`.
Fluxo de dados: afeta rastreamento Git.
Entradas/saídas: entrada é padrão `/.lake`; saída é exclusão desse cache.
Padrões: configuração de VCS.
Anti-padrões e smells: `.venv/` não é ignorado enquanto `.venv/pyvenv.cfg` existe em `.venv/pyvenv.cfg:1`, `.venv/pyvenv.cfg:2` e `.venv/pyvenv.cfg:3`.
Risco de refatoração: ALTO, porque a omissão está associada a 1870 arquivos de ambiente rastreados no Git.
<file-analyzed/>

#### Analisado 5 de 87 — AUDITORIA_REPOSITORIO.md
Responsabilidade: relatório de auditoria atual, iniciado pelo título em `AUDITORIA_REPOSITORIO.md:1`.
Fluxo de dados: sintetiza leitura de código, manifestos, workflows, contratos JSON e artefatos.
Entradas/saídas: entrada é o repositório; saída é este documento.
Padrões: documentação diagnóstica.
Anti-padrões e smells: por ser documento gerado, não participa do runtime; sua presença no inventário cria auto-referência documental em `AUDITORIA_REPOSITORIO.md:1`.
Risco de refatoração: BAIXO, por não ser consumido pelo código.
<file-analyzed/>

#### Analisado 6 de 87 — ConfiaLeanAuditor.lean
Responsabilidade: módulo agregador Lean que importa `Basic` e statement do problema em `ConfiaLeanAuditor.lean:1` e `ConfiaLeanAuditor.lean:2`.
Fluxo de dados: alimenta o alvo Lake `ConfiaLeanAuditor` declarado em `lakefile.toml:18`.
Entradas/saídas: exporta o conjunto de imports Lean para o build.
Padrões: módulo raiz agregador.
Anti-padrões e smells: importa scaffold `Basic` cuja única definição é `hello` em `ConfiaLeanAuditor/Basic.lean:1`.
Risco de refatoração: BAIXO, mas qualquer mudança altera o alvo padrão de Lake.
<file-analyzed/>

#### Analisado 7 de 87 — ConfiaLeanAuditor/Basic.lean
Responsabilidade: contém apenas `def hello := "world"` em `ConfiaLeanAuditor/Basic.lean:1`.
Fluxo de dados: é importado pelo agregador em `ConfiaLeanAuditor.lean:1`.
Entradas/saídas: exporta símbolo `hello`.
Padrões: scaffold Lean.
Anti-padrões e smells: boilerplate de scaffold presente em `ConfiaLeanAuditor/Basic.lean:1`.
Risco de refatoração: BAIXO, porque não há consumidor semântico observado além do agregador.
<file-analyzed/>

#### Analisado 8 de 87 — ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean
Responsabilidade: define funções e proposições formais do problema ITA2025Q1 em `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:7`, `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:10`, `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:13`, `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:18`, `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:22` e `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:28`.
Fluxo de dados: é consumido pelo agregador, certificado e geradores em `ConfiaLeanAuditor.lean:2`, `problems/ITA2025Q1/certificate/Statement.lean:1`, `app/confia_lean_auditor/lean/build_attempt.py:10` e `app/confia_lean_auditor/lean/formal_step_evaluator.py:23`.
Entradas/saídas: entrada é Mathlib em `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:1`; saída são definições no namespace em `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:3`.
Padrões: especificação formal.
Anti-padrões e smells: fórmula `triangleArea` depende de `signedDoubleArea` por valor absoluto em `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:10` e `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:11`; consumidores gerados reimplementam helper de área em string em `app/confia_lean_auditor/lean/build_attempt.py:18`.
Risco de refatoração: ALTO, por ser contrato formal central.
<file-analyzed/>

#### Analisado 9 de 87 — README.md
Responsabilidade: README de setup GitHub, com título em `README.md:1`.
Fluxo de dados: não é consumido pelo runtime observado.
Entradas/saídas: documentação manual.
Padrões: scaffold de repositório.
Anti-padrões e smells: texto instrui remover a seção depois do setup em `README.md:13`, indicando boilerplate de scaffold ainda presente.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 10 de 87 — app/confia_lean_auditor.egg-info/PKG-INFO
Responsabilidade: metadata gerado do pacote, com nome, versão e dependências em `app/confia_lean_auditor.egg-info/PKG-INFO:2`, `app/confia_lean_auditor.egg-info/PKG-INFO:3`, `app/confia_lean_auditor.egg-info/PKG-INFO:6`, `app/confia_lean_auditor.egg-info/PKG-INFO:7`, `app/confia_lean_auditor.egg-info/PKG-INFO:8` e `app/confia_lean_auditor.egg-info/PKG-INFO:9`.
Fluxo de dados: deriva de `pyproject.toml` em `pyproject.toml:5` a `pyproject.toml:15`.
Entradas/saídas: artefato de empacotamento.
Padrões: egg-info gerado.
Anti-padrões e smells: saída de build/metadata versionada; `SOURCES.txt` inclui o próprio egg-info em `app/confia_lean_auditor.egg-info/SOURCES.txt:4` e `app/confia_lean_auditor.egg-info/SOURCES.txt:5`.
Risco de refatoração: BAIXO para runtime, MÉDIO para distribuição.
<file-analyzed/>

### Lote 2: arquivos 11-20

#### Analisado 11 de 87 — app/confia_lean_auditor.egg-info/SOURCES.txt
Responsabilidade: lista fontes incluídas no pacote em `app/confia_lean_auditor.egg-info/SOURCES.txt:1` a `app/confia_lean_auditor.egg-info/SOURCES.txt:12`.
Fluxo de dados: reflete empacotamento setuptools configurado em `pyproject.toml:17`, `pyproject.toml:18`, `pyproject.toml:20` e `pyproject.toml:21`.
Entradas/saídas: artefato gerado de distribuição.
Padrões: manifest de build.
Anti-padrões e smells: omite vários módulos Python atuais, como `app/confia_lean_auditor/main.py`, embora o código importe esse módulo como API em `app/confia_lean_auditor/main.py:20`; isso indica metadata desatualizada.
Risco de refatoração: MÉDIO, por poder enganar diagnóstico de distribuição.
<file-analyzed/>

#### Analisado 12 de 87 — app/confia_lean_auditor.egg-info/dependency_links.txt
Responsabilidade: arquivo egg-info vazio, sem links de dependência.
Fluxo de dados: artefato de build sem conteúdo.
Entradas/saídas: nenhuma entrada runtime observada.
Padrões: metadata gerado.
Anti-padrões e smells: arquivo gerado versionado aparece em `app/confia_lean_auditor.egg-info/SOURCES.txt:6`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 13 de 87 — app/confia_lean_auditor.egg-info/requires.txt
Responsabilidade: registra dependências Python em `app/confia_lean_auditor.egg-info/requires.txt:1`, `app/confia_lean_auditor.egg-info/requires.txt:2`, `app/confia_lean_auditor.egg-info/requires.txt:3` e `app/confia_lean_auditor.egg-info/requires.txt:4`.
Fluxo de dados: duplica `pyproject.toml:11`, `pyproject.toml:12`, `pyproject.toml:13` e `pyproject.toml:14`.
Entradas/saídas: metadata de pacote.
Padrões: arquivo gerado.
Anti-padrões e smells: dependência `pytest` é declarada como runtime em `pyproject.toml:14`, mas não há diretório de testes próprio no inventário operacional; o uso observado de `pytest` está em `.venv/bin/pytest`, não no código do projeto.
Risco de refatoração: BAIXO para código, MÉDIO para empacotamento.
<file-analyzed/>

#### Analisado 14 de 87 — app/confia_lean_auditor.egg-info/top_level.txt
Responsabilidade: declara pacote top-level `confia_lean_auditor` em `app/confia_lean_auditor.egg-info/top_level.txt:1`.
Fluxo de dados: usado por ferramentas de empacotamento.
Entradas/saídas: metadata de distribuição.
Padrões: arquivo gerado.
Anti-padrões e smells: artefato de build versionado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 15 de 87 — app/confia_lean_auditor/__init__.py
Responsabilidade: marcador de pacote; não possui linhas de código e o pacote é identificado em `app/confia_lean_auditor.egg-info/top_level.txt:1`.
Fluxo de dados: habilita imports `confia_lean_auditor.*` usados em `app/confia_lean_auditor/main.py:9`.
Entradas/saídas: não exporta API própria.
Padrões: pacote Python.
Anti-padrões e smells: nenhum comportamento próprio observado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 16 de 87 — app/confia_lean_auditor/claims/__init__.py
Responsabilidade: marcador do subpacote `claims`, consumido pelo import absoluto em `app/confia_lean_auditor/main.py:9`.
Fluxo de dados: não transforma dados.
Entradas/saídas: não exporta nomes próprios.
Padrões: pacote Python.
Anti-padrões e smells: nenhum comportamento próprio observado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 17 de 87 — app/confia_lean_auditor/claims/extract_claims.py
Responsabilidade: normaliza texto, detecta claims do problema ITA2025Q1 e extrai passo formal de determinante em `app/confia_lean_auditor/claims/extract_claims.py:14`, `app/confia_lean_auditor/claims/extract_claims.py:72`, `app/confia_lean_auditor/claims/extract_claims.py:117` e `app/confia_lean_auditor/claims/extract_claims.py:214`.
Fluxo de dados: recebe `solution`, produz `ClaimExtraction` com `claims` e `formal_steps` em `app/confia_lean_auditor/claims/extract_claims.py:207`, `app/confia_lean_auditor/claims/extract_claims.py:208`, `app/confia_lean_auditor/claims/extract_claims.py:209` e `app/confia_lean_auditor/claims/extract_claims.py:210`.
Entradas/saídas: exporta `extract_claims`; chama `extract_claims_ita2025q1` só quando `problem_id == "ITA2025Q1"` em `app/confia_lean_auditor/claims/extract_claims.py:215`.
Padrões: parser heurístico por regex/string.
Anti-padrões e smells: strings mágicas de problema e claim types aparecem em `app/confia_lean_auditor/claims/extract_claims.py:100`, `app/confia_lean_auditor/claims/extract_claims.py:132`, `app/confia_lean_auditor/claims/extract_claims.py:147`, `app/confia_lean_auditor/claims/extract_claims.py:165`, `app/confia_lean_auditor/claims/extract_claims.py:180`, `app/confia_lean_auditor/claims/extract_claims.py:199` e `app/confia_lean_auditor/claims/extract_claims.py:215`; fallback para problema desconhecido retorna claims vazios em `app/confia_lean_auditor/claims/extract_claims.py:218`.
Risco de refatoração: ALTO, por definir a fronteira textual que alimenta rubrica e Lean.
<file-analyzed/>

#### Analisado 18 de 87 — app/confia_lean_auditor/core/__init__.py
Responsabilidade: marcador do subpacote `core`, usado por imports em `app/confia_lean_auditor/main.py:10` e `app/confia_lean_auditor/main.py:11`.
Fluxo de dados: não transforma dados.
Entradas/saídas: não exporta nomes próprios.
Padrões: pacote Python.
Anti-padrões e smells: nenhum comportamento próprio observado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 19 de 87 — app/confia_lean_auditor/core/paths.py
Responsabilidade: resolve raiz do repositório e valida/monta diretório de problema em `app/confia_lean_auditor/core/paths.py:15`, `app/confia_lean_auditor/core/paths.py:25` e `app/confia_lean_auditor/core/paths.py:34`.
Fluxo de dados: lê env var `CONFIA_LEAN_AUDITOR_ROOT` em `app/confia_lean_auditor/core/paths.py:16`, senão deriva a raiz de `__file__` em `app/confia_lean_auditor/core/paths.py:20`, `app/confia_lean_auditor/core/paths.py:21` e `app/confia_lean_auditor/core/paths.py:22`.
Entradas/saídas: exporta `InvalidProblemId`, `get_repo_root`, `validate_problem_id` e `get_problem_dir`.
Padrões: utilitário de paths com validação.
Anti-padrões e smells: caminho de raiz depende da profundidade fixa `parents[3]` em `app/confia_lean_auditor/core/paths.py:22`.
Risco de refatoração: ALTO, por ser usado por API, rubrica, microclaims e CLI.
<file-analyzed/>

#### Analisado 20 de 87 — app/confia_lean_auditor/core/schemas.py
Responsabilidade: define modelos Pydantic de request, claims, rubrica, certificado Lean, microclaims e response em `app/confia_lean_auditor/core/schemas.py:8`, `app/confia_lean_auditor/core/schemas.py:13`, `app/confia_lean_auditor/core/schemas.py:25`, `app/confia_lean_auditor/core/schemas.py:43`, `app/confia_lean_auditor/core/schemas.py:52`, `app/confia_lean_auditor/core/schemas.py:58`, `app/confia_lean_auditor/core/schemas.py:68`, `app/confia_lean_auditor/core/schemas.py:74`, `app/confia_lean_auditor/core/schemas.py:86` e `app/confia_lean_auditor/core/schemas.py:100`.
Fluxo de dados: os modelos tipam a resposta HTTP em `app/confia_lean_auditor/main.py:36` e a persistência JSON em `app/confia_lean_auditor/main.py:124`.
Entradas/saídas: exporta classes de contrato interno.
Padrões: DTOs Pydantic.
Anti-padrões e smells: status de Lean e strings de resultado são campos livres `str` em `app/confia_lean_auditor/core/schemas.py:75`, `app/confia_lean_auditor/core/schemas.py:96` e `app/confia_lean_auditor/core/schemas.py:104`.
Risco de refatoração: ALTO, por ser contrato compartilhado.
<file-analyzed/>

### Lote 3: arquivos 21-30

#### Analisado 21 de 87 — app/confia_lean_auditor/lean/__init__.py
Responsabilidade: marcador do subpacote `lean`, usado por imports em `app/confia_lean_auditor/main.py:12`, `app/confia_lean_auditor/main.py:13`, `app/confia_lean_auditor/main.py:14` e `app/confia_lean_auditor/main.py:15`.
Fluxo de dados: não transforma dados.
Entradas/saídas: não exporta nomes próprios.
Padrões: pacote Python.
Anti-padrões e smells: nenhum comportamento próprio observado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 22 de 87 — app/confia_lean_auditor/lean/build_attempt.py
Responsabilidade: monta código Lean completo a partir das claims e dos passos formais verificados em `app/confia_lean_auditor/lean/build_attempt.py:98`, `app/confia_lean_auditor/lean/build_attempt.py:103`, `app/confia_lean_auditor/lean/build_attempt.py:104` e `app/confia_lean_auditor/lean/build_attempt.py:106`.
Fluxo de dados: recebe `ClaimExtraction`, `artifact_dir` e `formal_step_results`; escreve `Attempt.lean` em `app/confia_lean_auditor/lean/build_attempt.py:127` e `app/confia_lean_auditor/lean/build_attempt.py:128`; retorna caminho e teoremas em `app/confia_lean_auditor/lean/build_attempt.py:130`, `app/confia_lean_auditor/lean/build_attempt.py:131` e `app/confia_lean_auditor/lean/build_attempt.py:132`.
Entradas/saídas: exporta `build_attempt`.
Padrões: gerador de código por templates string.
Anti-padrões e smells: strings Lean grandes embutidas em Python em `app/confia_lean_auditor/lean/build_attempt.py:9`, `app/confia_lean_auditor/lean/build_attempt.py:36`, `app/confia_lean_auditor/lean/build_attempt.py:44`, `app/confia_lean_auditor/lean/build_attempt.py:52` e `app/confia_lean_auditor/lean/build_attempt.py:70`; `problem_id` desconhecido levanta `NotImplementedError` em `app/confia_lean_auditor/lean/build_attempt.py:150`.
Risco de refatoração: ALTO, por acoplar texto extraído, teoremas, Lean e artefatos.
<file-analyzed/>

#### Analisado 23 de 87 — app/confia_lean_auditor/lean/formal_step_evaluator.py
Responsabilidade: renderiza e verifica passos formais extraídos da solução em arquivos Lean individuais em `app/confia_lean_auditor/lean/formal_step_evaluator.py:19` e `app/confia_lean_auditor/lean/formal_step_evaluator.py:49`.
Fluxo de dados: cria `formal_steps/`, escreve `{step.id}.lean`, executa Lean e transforma resultado em `FormalStepResult` em `app/confia_lean_auditor/lean/formal_step_evaluator.py:55`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:62`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:63`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:65` e `app/confia_lean_auditor/lean/formal_step_evaluator.py:70`.
Entradas/saídas: exporta `evaluate_formal_steps`.
Padrões: gerador e executor de verificação por item.
Anti-padrões e smells: `step.lhs`, `step.rhs` e `step.lean_method` entram diretamente no template Lean em `app/confia_lean_auditor/lean/formal_step_evaluator.py:31`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:32`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:33` e `app/confia_lean_auditor/lean/formal_step_evaluator.py:34`; `problem_id` desconhecido levanta `NotImplementedError` em `app/confia_lean_auditor/lean/formal_step_evaluator.py:46`.
Risco de refatoração: ALTO, por aceitar texto derivado da solução dentro de código Lean gerado.
<file-analyzed/>

#### Analisado 24 de 87 — app/confia_lean_auditor/lean/microclaim_evaluator.py
Responsabilidade: cruza evidência textual, teoremas gerados, status Lean e dependências de microclaims em `app/confia_lean_auditor/lean/microclaim_evaluator.py:38`.
Fluxo de dados: lê `microclaims.json`, computa `present_claim_types`, `generated` e `verified_step_types`, produz lista de `MicroclaimResult` em `app/confia_lean_auditor/lean/microclaim_evaluator.py:52`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:54`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:55`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:56` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:121`.
Entradas/saídas: exporta `evaluate_microclaims`.
Padrões: avaliador de grafo simples de dependências.
Anti-padrões e smells: status são strings montadas dinamicamente em `app/confia_lean_auditor/lean/microclaim_evaluator.py:82`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:84`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:86`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:88`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:90` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:119`.
Risco de refatoração: ALTO, por mediar rubrica e certificado.
<file-analyzed/>

#### Analisado 25 de 87 — app/confia_lean_auditor/lean/run_lean.py
Responsabilidade: detecta tokens proibidos, classifica saída Lean, executa Lean por subprocess e oferece CLI em `app/confia_lean_auditor/lean/run_lean.py:21`, `app/confia_lean_auditor/lean/run_lean.py:27`, `app/confia_lean_auditor/lean/run_lean.py:38`, `app/confia_lean_auditor/lean/run_lean.py:65`, `app/confia_lean_auditor/lean/run_lean.py:101` e `app/confia_lean_auditor/lean/run_lean.py:131`.
Fluxo de dados: lê arquivo Lean em `app/confia_lean_auditor/lean/run_lean.py:66`, chama `lake env lean` em `app/confia_lean_auditor/lean/run_lean.py:69`, captura stdout/stderr em `app/confia_lean_auditor/lean/run_lean.py:75`, `app/confia_lean_auditor/lean/run_lean.py:76`, `app/confia_lean_auditor/lean/run_lean.py:81` e `app/confia_lean_auditor/lean/run_lean.py:82`.
Entradas/saídas: exporta `run_lean_file`, `run_problem` e CLI.
Padrões: adapter de subprocess.
Anti-padrões e smells: mensagens de classificação dependem de substrings de stderr/stdout em `app/confia_lean_auditor/lean/run_lean.py:44`, `app/confia_lean_auditor/lean/run_lean.py:50`, `app/confia_lean_auditor/lean/run_lean.py:53`, `app/confia_lean_auditor/lean/run_lean.py:56` e `app/confia_lean_auditor/lean/run_lean.py:59`.
Risco de refatoração: ALTO, por fronteira externa com Lake/Lean.
<file-analyzed/>

#### Analisado 26 de 87 — app/confia_lean_auditor/main.py
Responsabilidade: orquestra API FastAPI, valida problema, executa pipeline de claims, Lean, microclaims, rubrica, feedback e persistência em `app/confia_lean_auditor/main.py:20`, `app/confia_lean_auditor/main.py:27` e `app/confia_lean_auditor/main.py:36`.
Fluxo de dados: request `AuditRequest` entra em `app/confia_lean_auditor/main.py:37`; resposta `AuditResponse` sai em `app/confia_lean_auditor/main.py:109` e `app/confia_lean_auditor/main.py:134`; artefatos são gravados em `app/confia_lean_auditor/main.py:123`, `app/confia_lean_auditor/main.py:128` e `app/confia_lean_auditor/main.py:129`.
Entradas/saídas: rotas HTTP `/health` e `/audit`.
Padrões: controller/orquestrador.
Anti-padrões e smells: versão da API `0.4.0` diverge da versão do pacote `0.1.0` em `app/confia_lean_auditor/main.py:20`, `app/confia_lean_auditor/main.py:32` e `pyproject.toml:7`; exceções de arquivo viram 500/404 conforme origem em `app/confia_lean_auditor/main.py:93`, `app/confia_lean_auditor/main.py:94`, `app/confia_lean_auditor/main.py:103` e `app/confia_lean_auditor/main.py:104`.
Risco de refatoração: ALTO, por concentrar o fluxo completo.
<file-analyzed/>

#### Analisado 27 de 87 — app/confia_lean_auditor/reports/__init__.py
Responsabilidade: marcador do subpacote `reports`, usado pelo import em `app/confia_lean_auditor/main.py:16`.
Fluxo de dados: não transforma dados.
Entradas/saídas: não exporta nomes próprios.
Padrões: pacote Python.
Anti-padrões e smells: nenhum comportamento próprio observado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 28 de 87 — app/confia_lean_auditor/reports/report_builder.py
Responsabilidade: converte rubrica, certificado Lean e microclaims em veredito e feedback textual em `app/confia_lean_auditor/reports/report_builder.py:19` e `app/confia_lean_auditor/reports/report_builder.py:31`.
Fluxo de dados: consome `RubricAssessment`, `LeanCertificate` e lista de `MicroclaimResult`; retorna string em `app/confia_lean_auditor/reports/report_builder.py:31`, `app/confia_lean_auditor/reports/report_builder.py:32`, `app/confia_lean_auditor/reports/report_builder.py:33`, `app/confia_lean_auditor/reports/report_builder.py:34` e `app/confia_lean_auditor/reports/report_builder.py:75`.
Entradas/saídas: exporta `verdict_from_score` e `build_feedback`.
Padrões: builder de apresentação textual.
Anti-padrões e smells: limiares de veredito são números mágicos em `app/confia_lean_auditor/reports/report_builder.py:22`, `app/confia_lean_auditor/reports/report_builder.py:24` e `app/confia_lean_auditor/reports/report_builder.py:26`; strings de status são acopladas a `verified_by_lean` e `verified` em `app/confia_lean_auditor/reports/report_builder.py:42` e `app/confia_lean_auditor/reports/report_builder.py:68`.
Risco de refatoração: MÉDIO, por afetar saída ao usuário.
<file-analyzed/>

#### Analisado 29 de 87 — app/confia_lean_auditor/rubric/__init__.py
Responsabilidade: marcador do subpacote `rubric`, usado pelo import em `app/confia_lean_auditor/main.py:17`.
Fluxo de dados: não transforma dados.
Entradas/saídas: não exporta nomes próprios.
Padrões: pacote Python.
Anti-padrões e smells: nenhum comportamento próprio observado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 30 de 87 — app/confia_lean_auditor/rubric/rubric_evaluator.py
Responsabilidade: avalia itens de rubrica a partir de claims e microclaims verificados em `app/confia_lean_auditor/rubric/rubric_evaluator.py:16`.
Fluxo de dados: lê `rubric.json` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:23` e `app/confia_lean_auditor/rubric/rubric_evaluator.py:28`; acumula score em `app/confia_lean_auditor/rubric/rubric_evaluator.py:43` e `app/confia_lean_auditor/rubric/rubric_evaluator.py:63`; retorna `RubricAssessment` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:84`.
Entradas/saídas: exporta `evaluate_rubric`.
Padrões: avaliador orientado por configuração JSON.
Anti-padrões e smells: acesso a `data["items"]`, `item["points"]`, `item["id"]` e `data["max_score"]` não valida schema antes de usar em `app/confia_lean_auditor/rubric/rubric_evaluator.py:45`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:62`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:74` e `app/confia_lean_auditor/rubric/rubric_evaluator.py:86`.
Risco de refatoração: ALTO, por definir pontuação.
<file-analyzed/>

### Lote 4: arquivos 31-40

#### Analisado 31 de 87 — artifacts/runs/20260702T181631_332331/audit.json
Responsabilidade: saída versionada de auditoria para `ITA2025Q1`, com score 10 em `artifacts/runs/20260702T181631_332331/audit.json:2`, `artifacts/runs/20260702T181631_332331/audit.json:3` e `artifacts/runs/20260702T181631_332331/audit.json:5`.
Fluxo de dados: corresponde ao tipo de saída gravado por `main.py` em `app/confia_lean_auditor/main.py:123`.
Entradas/saídas: artefato final, consumido por humanos ou inspeção.
Padrões: snapshot JSON.
Anti-padrões e smells: saída de execução versionada.
Risco de refatoração: BAIXO para código, MÉDIO para higiene de repositório.
<file-analyzed/>

#### Analisado 32 de 87 — artifacts/runs/20260702T181631_332331/solution.txt
Responsabilidade: solução correta usada como entrada de execução, com resposta final em `artifacts/runs/20260702T181631_332331/solution.txt:23`.
Fluxo de dados: corresponde à saída `solution.txt` gravada por `main.py` em `app/confia_lean_auditor/main.py:128`.
Entradas/saídas: fixture/snapshot de entrada.
Padrões: texto de exemplo versionado em artefatos.
Anti-padrões e smells: duplica `problems/ITA2025Q1/examples/correct_solution.txt:1` a `problems/ITA2025Q1/examples/correct_solution.txt:23`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 33 de 87 — artifacts/runs/20260702T235936_589547/audit.json
Responsabilidade: saída de auditoria correta, com `extracted_claims` em `artifacts/runs/20260702T235936_589547/audit.json:6` e score 10 em `artifacts/runs/20260702T235936_589547/audit.json:3`.
Fluxo de dados: snapshot de `AuditResponse`.
Entradas/saídas: artefato gerado.
Padrões: snapshot JSON.
Anti-padrões e smells: saída de execução versionada por acidente; contém schema antigo/atual misturado ao longo dos runs, visível pela presença de `extracted_claims` aqui em `artifacts/runs/20260702T235936_589547/audit.json:6` e sua ausência inicial no run anterior até `artifacts/runs/20260702T181631_332331/audit.json:6`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 34 de 87 — artifacts/runs/20260702T235936_589547/claims.json
Responsabilidade: claims extraídas para solução correta, com cinco claims em `artifacts/runs/20260702T235936_589547/claims.json:5`, `artifacts/runs/20260702T235936_589547/claims.json:16`, `artifacts/runs/20260702T235936_589547/claims.json:26`, `artifacts/runs/20260702T235936_589547/claims.json:36` e `artifacts/runs/20260702T235936_589547/claims.json:46`.
Fluxo de dados: saída de `extract_claims`, produzida por `main.py` em `app/confia_lean_auditor/main.py:129`.
Entradas/saídas: artefato intermediário.
Padrões: snapshot JSON.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 35 de 87 — artifacts/runs/20260702T235936_589547/solution.txt
Responsabilidade: solução correta, com determinante em `artifacts/runs/20260702T235936_589547/solution.txt:12` e resposta em `artifacts/runs/20260702T235936_589547/solution.txt:23`.
Fluxo de dados: snapshot de input.
Entradas/saídas: texto de solução.
Padrões: fixture operacional.
Anti-padrões e smells: duplicata literal de exemplo correto visível pela mesma abertura em `problems/ITA2025Q1/examples/correct_solution.txt:1` e `artifacts/runs/20260702T235936_589547/solution.txt:1`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 36 de 87 — artifacts/runs/20260703T005732_426318/Attempt.lean
Responsabilidade: tentativa Lean gerada com definições próprias de área e teoremas em `artifacts/runs/20260703T005732_426318/Attempt.lean:8`, `artifacts/runs/20260703T005732_426318/Attempt.lean:14`, `artifacts/runs/20260703T005732_426318/Attempt.lean:19`, `artifacts/runs/20260703T005732_426318/Attempt.lean:32`, `artifacts/runs/20260703T005732_426318/Attempt.lean:37` e `artifacts/runs/20260703T005732_426318/Attempt.lean:55`.
Fluxo de dados: artefato gerado por versão anterior do gerador, pois o gerador atual importa statement em `app/confia_lean_auditor/lean/build_attempt.py:10`.
Entradas/saídas: entrada para `lake env lean`.
Padrões: código gerado.
Anti-padrões e smells: arquivo gerado versionado; diverge do template atual que abre namespace do statement em `app/confia_lean_auditor/lean/build_attempt.py:14`.
Risco de refatoração: BAIXO para código fonte, MÉDIO como evidência histórica.
<file-analyzed/>

#### Analisado 37 de 87 — artifacts/runs/20260703T005732_426318/audit.json
Responsabilidade: auditoria gerada com score 10 e claims completas em `artifacts/runs/20260703T005732_426318/audit.json:3` e `artifacts/runs/20260703T005732_426318/audit.json:6`.
Fluxo de dados: snapshot de `AuditResponse`.
Entradas/saídas: artefato final.
Padrões: JSON de saída.
Anti-padrões e smells: saída versionada por acidente.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 38 de 87 — artifacts/runs/20260703T005732_426318/claims.json
Responsabilidade: claims completas geradas para solução correta em `artifacts/runs/20260703T005732_426318/claims.json:2` e `artifacts/runs/20260703T005732_426318/claims.json:3`.
Fluxo de dados: saída intermediária de claims.
Entradas/saídas: artefato JSON.
Padrões: snapshot.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 39 de 87 — artifacts/runs/20260703T005732_426318/solution.txt
Responsabilidade: solução correta duplicada, com determinante correto em `artifacts/runs/20260703T005732_426318/solution.txt:12`.
Fluxo de dados: input persistido.
Entradas/saídas: texto de solução.
Padrões: fixture operacional.
Anti-padrões e smells: duplicata de `problems/ITA2025Q1/examples/correct_solution.txt:12`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 40 de 87 — artifacts/runs/20260703T005858_740365/Attempt.lean
Responsabilidade: tentativa Lean gerada apenas com `answer_check` em `artifacts/runs/20260703T005858_740365/Attempt.lean:32`.
Fluxo de dados: corresponde a solução com resposta isolada em `artifacts/runs/20260703T005858_740365/solution.txt:1`.
Entradas/saídas: entrada para Lean.
Padrões: código gerado condicional por claims.
Anti-padrões e smells: versão antiga do gerador reimplementa `triangleArea` em `artifacts/runs/20260703T005858_740365/Attempt.lean:8` e `artifacts/runs/20260703T005858_740365/Attempt.lean:11`.
Risco de refatoração: BAIXO.
<file-analyzed/>

### Lote 5: arquivos 41-50

#### Analisado 41 de 87 — artifacts/runs/20260703T005858_740365/audit.json
Responsabilidade: auditoria de resposta apenas, com score 1 e veredito insuficiente em `artifacts/runs/20260703T005858_740365/audit.json:3` e `artifacts/runs/20260703T005858_740365/audit.json:5`.
Fluxo de dados: snapshot de avaliação.
Entradas/saídas: artefato final.
Padrões: JSON de saída.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 42 de 87 — artifacts/runs/20260703T005858_740365/claims.json
Responsabilidade: claims de resposta apenas, com `final_answer` em `artifacts/runs/20260703T005858_740365/claims.json:5` e `artifacts/runs/20260703T005858_740365/claims.json:6`.
Fluxo de dados: saída intermediária de extrator.
Entradas/saídas: JSON gerado.
Padrões: snapshot.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 43 de 87 — artifacts/runs/20260703T005858_740365/solution.txt
Responsabilidade: input mínimo com resposta final em `artifacts/runs/20260703T005858_740365/solution.txt:1`.
Fluxo de dados: corresponde a `problems/ITA2025Q1/examples/answer_only.txt:1`.
Entradas/saídas: texto de solução.
Padrões: fixture operacional.
Anti-padrões e smells: duplicata de exemplo versionado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 44 de 87 — artifacts/runs/20260703T011235_219542/Attempt.lean
Responsabilidade: tentativa Lean com teorema de coordenadas em `artifacts/runs/20260703T011235_219542/Attempt.lean:32`.
Fluxo de dados: código gerado de execução parcial.
Entradas/saídas: entrada Lean.
Padrões: código gerado.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 45 de 87 — artifacts/runs/20260703T011235_219542/audit.json
Responsabilidade: auditoria parcial com score 7 em `artifacts/runs/20260703T011235_219542/audit.json:3`.
Fluxo de dados: snapshot de avaliação parcial.
Entradas/saídas: artefato final.
Padrões: JSON de saída.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 46 de 87 — artifacts/runs/20260703T011235_219542/claims.json
Responsabilidade: claims parciais para solução sem raiz positiva, com `problem_id` em `artifacts/runs/20260703T011235_219542/claims.json:2`.
Fluxo de dados: saída intermediária de claims.
Entradas/saídas: JSON gerado.
Padrões: snapshot.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 47 de 87 — artifacts/runs/20260703T011235_219542/solution.txt
Responsabilidade: solução parcial, semelhante ao exemplo `partial_no_positive_root`, com equação em `artifacts/runs/20260703T011235_219542/solution.txt:8` e fatoração em `artifacts/runs/20260703T011235_219542/solution.txt:10`.
Fluxo de dados: input persistido.
Entradas/saídas: texto de solução.
Padrões: fixture operacional.
Anti-padrões e smells: duplicata de exemplo em `problems/ITA2025Q1/examples/partial_no_positive_root.txt:1`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 48 de 87 — artifacts/runs/20260703T011304_967627/Attempt.lean
Responsabilidade: tentativa Lean mínima com helper de área e sem teoremas de claims em `artifacts/runs/20260703T011304_967627/Attempt.lean:14`.
Fluxo de dados: código gerado para solução errada.
Entradas/saídas: entrada Lean.
Padrões: código gerado.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 49 de 87 — artifacts/runs/20260703T011304_967627/audit.json
Responsabilidade: auditoria de solução errada, com score 0 em `artifacts/runs/20260703T011304_967627/audit.json:3`.
Fluxo de dados: snapshot final.
Entradas/saídas: JSON gerado.
Padrões: saída de execução.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 50 de 87 — artifacts/runs/20260703T011304_967627/claims.json
Responsabilidade: claims vazias para `ITA2025Q1`, com `claims` vazio em `artifacts/runs/20260703T011304_967627/claims.json:2` e `artifacts/runs/20260703T011304_967627/claims.json:3`.
Fluxo de dados: saída do extrator sem detecção.
Entradas/saídas: JSON intermediário.
Padrões: snapshot.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

### Lote 6: arquivos 51-60

#### Analisado 51 de 87 — artifacts/runs/20260703T011304_967627/solution.txt
Responsabilidade: solução errada com área `2a + 5` e resposta `97,5` em `artifacts/runs/20260703T011304_967627/solution.txt:1` e `artifacts/runs/20260703T011304_967627/solution.txt:2`.
Fluxo de dados: input persistido.
Entradas/saídas: texto de solução.
Padrões: fixture operacional.
Anti-padrões e smells: duplicata de `problems/ITA2025Q1/examples/wrong_solution.txt:1` e `problems/ITA2025Q1/examples/wrong_solution.txt:2`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 52 de 87 — artifacts/runs/20260703T013701_387917/Attempt.lean
Responsabilidade: tentativa Lean completa de versão antiga, com namespace gerado em `artifacts/runs/20260703T013701_387917/Attempt.lean:4`.
Fluxo de dados: código gerado.
Entradas/saídas: entrada Lean.
Padrões: snapshot de código gerado.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 53 de 87 — artifacts/runs/20260703T013701_387917/audit.json
Responsabilidade: auditoria correta com score 10 em `artifacts/runs/20260703T013701_387917/audit.json:3`.
Fluxo de dados: snapshot final.
Entradas/saídas: JSON gerado.
Padrões: saída de execução.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 54 de 87 — artifacts/runs/20260703T013701_387917/claims.json
Responsabilidade: claims completas para solução correta, com `problem_id` em `artifacts/runs/20260703T013701_387917/claims.json:2`.
Fluxo de dados: saída intermediária.
Entradas/saídas: JSON gerado.
Padrões: snapshot.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 55 de 87 — artifacts/runs/20260703T013701_387917/solution.txt
Responsabilidade: solução correta duplicada, com resposta em `artifacts/runs/20260703T013701_387917/solution.txt:23`.
Fluxo de dados: input persistido.
Entradas/saídas: texto de solução.
Padrões: fixture operacional.
Anti-padrões e smells: duplicata de `problems/ITA2025Q1/examples/correct_solution.txt:23`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 56 de 87 — artifacts/runs/20260703T032116_301877/Attempt.lean
Responsabilidade: tentativa Lean completa, com import do statement em `artifacts/runs/20260703T032116_301877/Attempt.lean:2`.
Fluxo de dados: código gerado.
Entradas/saídas: entrada Lean.
Padrões: snapshot de código gerado.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 57 de 87 — artifacts/runs/20260703T032116_301877/audit.json
Responsabilidade: auditoria correta com score 10 em `artifacts/runs/20260703T032116_301877/audit.json:3`.
Fluxo de dados: snapshot final.
Entradas/saídas: JSON gerado.
Padrões: saída de execução.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 58 de 87 — artifacts/runs/20260703T032116_301877/claims.json
Responsabilidade: claims completas para `ITA2025Q1`, com `problem_id` em `artifacts/runs/20260703T032116_301877/claims.json:2`.
Fluxo de dados: saída intermediária.
Entradas/saídas: JSON gerado.
Padrões: snapshot.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 59 de 87 — artifacts/runs/20260703T032116_301877/solution.txt
Responsabilidade: solução correta duplicada, com determinante em `artifacts/runs/20260703T032116_301877/solution.txt:12`.
Fluxo de dados: input persistido.
Entradas/saídas: texto de solução.
Padrões: fixture operacional.
Anti-padrões e smells: duplicata de `problems/ITA2025Q1/examples/correct_solution.txt:12`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 60 de 87 — artifacts/runs/20260703T034756_205958/Attempt.lean
Responsabilidade: tentativa Lean atual com import do statement e teoremas gerados em `artifacts/runs/20260703T034756_205958/Attempt.lean:2`, `artifacts/runs/20260703T034756_205958/Attempt.lean:27`, `artifacts/runs/20260703T034756_205958/Attempt.lean:33`, `artifacts/runs/20260703T034756_205958/Attempt.lean:39` e `artifacts/runs/20260703T034756_205958/Attempt.lean:55`.
Fluxo de dados: artefato produzido pelo gerador atual.
Entradas/saídas: entrada Lean.
Padrões: código gerado.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

### Lote 7: arquivos 61-70

#### Analisado 61 de 87 — artifacts/runs/20260703T034756_205958/audit.json
Responsabilidade: auditoria correta com formal steps e score 10 em `artifacts/runs/20260703T034756_205958/audit.json:3`, `artifacts/runs/20260703T034756_205958/audit.json:61` e `artifacts/runs/20260703T034756_205958/audit.json:79`.
Fluxo de dados: snapshot final.
Entradas/saídas: JSON gerado.
Padrões: saída de execução.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 62 de 87 — artifacts/runs/20260703T034756_205958/claims.json
Responsabilidade: claims completas com `formal_steps` em `artifacts/runs/20260703T034756_205958/claims.json:56` e passo `q1_s1_determinant_expansion` em `artifacts/runs/20260703T034756_205958/claims.json:58`.
Fluxo de dados: saída de extração.
Entradas/saídas: JSON intermediário.
Padrões: snapshot.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 63 de 87 — artifacts/runs/20260703T034756_205958/formal_steps/q1_s1_determinant_expansion.lean
Responsabilidade: teorema Lean individual do passo de determinante, importando statement em `artifacts/runs/20260703T034756_205958/formal_steps/q1_s1_determinant_expansion.lean:2`.
Fluxo de dados: produzido por `formal_step_evaluator.py` em `app/confia_lean_auditor/lean/formal_step_evaluator.py:62` e `app/confia_lean_auditor/lean/formal_step_evaluator.py:63`.
Entradas/saídas: entrada para Lean.
Padrões: código gerado por item.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 64 de 87 — artifacts/runs/20260703T034756_205958/solution.txt
Responsabilidade: solução correta duplicada, com resposta em `artifacts/runs/20260703T034756_205958/solution.txt:23`.
Fluxo de dados: input persistido.
Entradas/saídas: texto.
Padrões: fixture operacional.
Anti-padrões e smells: duplicata de `problems/ITA2025Q1/examples/correct_solution.txt:23`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 65 de 87 — artifacts/runs/20260703T035633_483787/Attempt.lean
Responsabilidade: tentativa Lean para solução com determinante errado, sem teorema `triangleArea_formula`, com `z_squared_coordinates`, `answer_unique` e `answer_check` em `artifacts/runs/20260703T035633_483787/Attempt.lean:27`, `artifacts/runs/20260703T035633_483787/Attempt.lean:33` e `artifacts/runs/20260703T035633_483787/Attempt.lean:49`.
Fluxo de dados: gerado após formal step não verificado, pois `build_attempt.py` só adiciona `TRIANGLE_AREA_FORMULA` se `determinant_expansion` está verificado em `app/confia_lean_auditor/lean/build_attempt.py:113`.
Entradas/saídas: entrada Lean.
Padrões: código gerado condicional.
Anti-padrões e smells: `answer_unique` é gerado sem o microclaim de área formalizado no arquivo, evidência de acoplamento por claim types em `app/confia_lean_auditor/lean/build_attempt.py:117` e `app/confia_lean_auditor/lean/build_attempt.py:118`.
Risco de refatoração: MÉDIO.
<file-analyzed/>

#### Analisado 66 de 87 — artifacts/runs/20260703T035633_483787/audit.json
Responsabilidade: auditoria parcial com score 7, erro de formal step e `formal_steps_not_verified` em `artifacts/runs/20260703T035633_483787/audit.json:3`, `artifacts/runs/20260703T035633_483787/audit.json:98`, `artifacts/runs/20260703T035633_483787/audit.json:194` e `artifacts/runs/20260703T035633_483787/audit.json:196`.
Fluxo de dados: evidencia divergência entre claim textual de área e passo formal.
Entradas/saídas: JSON final.
Padrões: snapshot diagnóstico.
Anti-padrões e smells: stdout com caminho absoluto local aparece em `artifacts/runs/20260703T035633_483787/audit.json:98`.
Risco de refatoração: BAIXO para runtime, MÉDIO para privacidade de artefatos.
<file-analyzed/>

#### Analisado 67 de 87 — artifacts/runs/20260703T035633_483787/claims.json
Responsabilidade: claims completas com formal step extraído para solução de determinante errado em `artifacts/runs/20260703T035633_483787/claims.json:56`, `artifacts/runs/20260703T035633_483787/claims.json:58` e `artifacts/runs/20260703T035633_483787/claims.json:59`.
Fluxo de dados: saída intermediária.
Entradas/saídas: JSON de claims.
Padrões: snapshot.
Anti-padrões e smells: evidencia que a heurística textual detecta `area_formula` mesmo quando a linha de determinante contém coeficiente errado em `artifacts/runs/20260703T035633_483787/solution.txt:6` e `artifacts/runs/20260703T035633_483787/claims.json:16`.
Risco de refatoração: MÉDIO.
<file-analyzed/>

#### Analisado 68 de 87 — artifacts/runs/20260703T035633_483787/formal_steps/q1_s1_determinant_expansion.lean
Responsabilidade: teorema Lean gerado para passo de determinante em solução errada, com import em `artifacts/runs/20260703T035633_483787/formal_steps/q1_s1_determinant_expansion.lean:2`.
Fluxo de dados: entrada para Lean que gerou erro registrado em `artifacts/runs/20260703T035633_483787/audit.json:98`.
Entradas/saídas: código gerado.
Padrões: formal step.
Anti-padrões e smells: saída gerada versionada com erro associado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 69 de 87 — artifacts/runs/20260703T035633_483787/solution.txt
Responsabilidade: solução com determinante errado, linha `(a-1)4a - 2(a^2-5) = 2a^2 - 2a + 10` em `artifacts/runs/20260703T035633_483787/solution.txt:6`.
Fluxo de dados: input persistido.
Entradas/saídas: texto.
Padrões: fixture operacional.
Anti-padrões e smells: duplica `problems/ITA2025Q1/examples/wrong_determinant_step.txt:6`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 70 de 87 — artifacts/runs/20260703T144140_097860/Attempt.lean
Responsabilidade: tentativa Lean para solução com determinante errado, com import do statement em `artifacts/runs/20260703T144140_097860/Attempt.lean:2`.
Fluxo de dados: código gerado condicional.
Entradas/saídas: entrada Lean.
Padrões: snapshot de código gerado.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

### Lote 8: arquivos 71-80

#### Analisado 71 de 87 — artifacts/runs/20260703T144140_097860/audit.json
Responsabilidade: auditoria com score 3 e falha formal registrada em `artifacts/runs/20260703T144140_097860/audit.json:3`, `artifacts/runs/20260703T144140_097860/audit.json:98` e `artifacts/runs/20260703T144140_097860/audit.json:200`.
Fluxo de dados: snapshot final de execução.
Entradas/saídas: JSON final.
Padrões: diagnóstico persistido.
Anti-padrões e smells: stdout inclui caminho absoluto local em `artifacts/runs/20260703T144140_097860/audit.json:98`.
Risco de refatoração: BAIXO para código, MÉDIO para exposição de ambiente.
<file-analyzed/>

#### Analisado 72 de 87 — artifacts/runs/20260703T144140_097860/claims.json
Responsabilidade: claims completas com formal step para solução errada em `artifacts/runs/20260703T144140_097860/claims.json:56` e `artifacts/runs/20260703T144140_097860/claims.json:58`.
Fluxo de dados: saída intermediária.
Entradas/saídas: JSON de claims.
Padrões: snapshot.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 73 de 87 — artifacts/runs/20260703T144140_097860/formal_steps/q1_s1_determinant_expansion.lean
Responsabilidade: formal step Lean de determinante, importando statement em `artifacts/runs/20260703T144140_097860/formal_steps/q1_s1_determinant_expansion.lean:2`.
Fluxo de dados: entrada Lean para erro capturado em `artifacts/runs/20260703T144140_097860/audit.json:98`.
Entradas/saídas: código gerado.
Padrões: formal step gerado.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 74 de 87 — artifacts/runs/20260703T144140_097860/solution.txt
Responsabilidade: solução com determinante errado, linha incorreta em `artifacts/runs/20260703T144140_097860/solution.txt:6`.
Fluxo de dados: input persistido.
Entradas/saídas: texto.
Padrões: fixture operacional.
Anti-padrões e smells: duplicata de `problems/ITA2025Q1/examples/wrong_determinant_step.txt:6`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 75 de 87 — lake-manifest.json
Responsabilidade: lock de dependências Lake, com `mathlib` e dependências herdadas em `lake-manifest.json:4`, `lake-manifest.json:9`, `lake-manifest.json:14`, `lake-manifest.json:24`, `lake-manifest.json:34`, `lake-manifest.json:44`, `lake-manifest.json:54`, `lake-manifest.json:64`, `lake-manifest.json:74` e `lake-manifest.json:84`.
Fluxo de dados: Lake usa o lock para materializar `.lake/packages`, cujo diretório está configurado em `lake-manifest.json:2`.
Entradas/saídas: manifesto de resolução.
Padrões: lockfile.
Anti-padrões e smells: dependências herdadas usam `inputRev` como `main` ou `master` em `lake-manifest.json:21`, `lake-manifest.json:31`, `lake-manifest.json:41`, `lake-manifest.json:61`, `lake-manifest.json:71` e `lake-manifest.json:81`, ainda que o lock trave hashes.
Risco de refatoração: MÉDIO, por afetar build Lean.
<file-analyzed/>

#### Analisado 76 de 87 — lakefile.toml
Responsabilidade: define pacote Lake, opções Lean, dependência mathlib e biblioteca em `lakefile.toml:1`, `lakefile.toml:4`, `lakefile.toml:6`, `lakefile.toml:12` e `lakefile.toml:17`.
Fluxo de dados: controla build Lean usado por CI e subprocess.
Entradas/saídas: entrada para Lake; saída é biblioteca `ConfiaLeanAuditor`.
Padrões: manifesto Lake.
Anti-padrões e smells: opções e dependência centralizadas; nenhum smell funcional além do acoplamento a `ConfiaLeanAuditor` em `lakefile.toml:18`.
Risco de refatoração: ALTO, por reger build formal.
<file-analyzed/>

#### Analisado 77 de 87 — lean-toolchain
Responsabilidade: fixa toolchain Lean em `lean-toolchain:1`.
Fluxo de dados: consumido por Lake/Lean Action.
Entradas/saídas: runtime Lean.
Padrões: pin de toolchain.
Anti-padrões e smells: sem smell observado; release workflow observa este arquivo em `.github/workflows/create-release.yml:9`.
Risco de refatoração: ALTO, por trocar compilador e mathlib.
<file-analyzed/>

#### Analisado 78 de 87 — problems/ITA2025Q1/certificate/Statement.lean
Responsabilidade: certificado Lean mínimo que importa statement do problema em `problems/ITA2025Q1/certificate/Statement.lean:1`.
Fluxo de dados: é alvo do CLI `run_problem` em `app/confia_lean_auditor/lean/run_lean.py:115`.
Entradas/saídas: entrada para `lake env lean`.
Padrões: certificado manual.
Anti-padrões e smells: arquivo não declara teoremas próprios, só import; isso torna o CLI uma checagem de import, não de prova específica, conforme `problems/ITA2025Q1/certificate/Statement.lean:1`.
Risco de refatoração: MÉDIO.
<file-analyzed/>

#### Analisado 79 de 87 — problems/ITA2025Q1/examples/answer_only.txt
Responsabilidade: exemplo de solução só com resposta em `problems/ITA2025Q1/examples/answer_only.txt:1`.
Fluxo de dados: fixture textual; não há consumidor automático observado no código.
Entradas/saídas: input humano/teste manual.
Padrões: fixture.
Anti-padrões e smells: fixture sem teste automatizado associado no inventário operacional.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 80 de 87 — problems/ITA2025Q1/examples/correct_solution.txt
Responsabilidade: exemplo de solução correta completa em `problems/ITA2025Q1/examples/correct_solution.txt:1`, com resposta em `problems/ITA2025Q1/examples/correct_solution.txt:23`.
Fluxo de dados: fixture textual.
Entradas/saídas: input manual.
Padrões: fixture de caso feliz.
Anti-padrões e smells: não há teste automatizado próprio no inventário que consuma este arquivo.
Risco de refatoração: BAIXO.
<file-analyzed/>

### Lote 9: arquivos 81-87

#### Analisado 81 de 87 — problems/ITA2025Q1/examples/partial_no_positive_root.txt
Responsabilidade: exemplo parcial sem descarte explícito da raiz negativa, com fatoração em `problems/ITA2025Q1/examples/partial_no_positive_root.txt:10`.
Fluxo de dados: fixture textual.
Entradas/saídas: input manual.
Padrões: fixture negativa/parcial.
Anti-padrões e smells: sem consumidor automatizado observado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 82 de 87 — problems/ITA2025Q1/examples/wrong_determinant_step.txt
Responsabilidade: exemplo com passo de determinante incorreto em `problems/ITA2025Q1/examples/wrong_determinant_step.txt:6`.
Fluxo de dados: fixture que evidencia divergência formal capturada nos artefatos em `artifacts/runs/20260703T144140_097860/audit.json:98`.
Entradas/saídas: input manual.
Padrões: fixture de erro sutil.
Anti-padrões e smells: sem teste automatizado observado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 83 de 87 — problems/ITA2025Q1/examples/wrong_solution.txt
Responsabilidade: exemplo errado simples, com área `2a + 5` e resposta `97,5` em `problems/ITA2025Q1/examples/wrong_solution.txt:1` e `problems/ITA2025Q1/examples/wrong_solution.txt:2`.
Fluxo de dados: fixture textual.
Entradas/saídas: input manual.
Padrões: fixture negativa.
Anti-padrões e smells: sem teste automatizado observado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 84 de 87 — problems/ITA2025Q1/microclaims.json
Responsabilidade: contrato de microclaims para ITA2025Q1 em `problems/ITA2025Q1/microclaims.json:2` e `problems/ITA2025Q1/microclaims.json:3`.
Fluxo de dados: consumido por `microclaim_evaluator.py` em `app/confia_lean_auditor/lean/microclaim_evaluator.py:47` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:52`.
Entradas/saídas: define ids, teoremas, claim types, dependências e supports em `problems/ITA2025Q1/microclaims.json:5`, `problems/ITA2025Q1/microclaims.json:7`, `problems/ITA2025Q1/microclaims.json:8`, `problems/ITA2025Q1/microclaims.json:16`, `problems/ITA2025Q1/microclaims.json:24` e `problems/ITA2025Q1/microclaims.json:25`.
Padrões: configuração de grafo de validação.
Anti-padrões e smells: não há validação de schema antes de `data["microclaims"]` em `app/confia_lean_auditor/lean/microclaim_evaluator.py:62`.
Risco de refatoração: ALTO, por acoplar rubrica, claims e teoremas.
<file-analyzed/>

#### Analisado 85 de 87 — problems/ITA2025Q1/problem.json
Responsabilidade: metadata do problema, com id, enunciado, resposta e pontuação em `problems/ITA2025Q1/problem.json:2`, `problems/ITA2025Q1/problem.json:4`, `problems/ITA2025Q1/problem.json:6` e `problems/ITA2025Q1/problem.json:7`.
Fluxo de dados: o código atual verifica existência do diretório do problema em `app/confia_lean_auditor/main.py:45`, mas não lê `problem.json` no fluxo auditado.
Entradas/saídas: contrato documental do problema.
Padrões: metadata JSON.
Anti-padrões e smells: arquivo órfão funcional no runtime atual, pois buscas por `problem.json` não aparecem nos imports/acoplamentos do código próprio.
Risco de refatoração: MÉDIO, por conter enunciado e resposta oficial fora do fluxo de validação.
<file-analyzed/>

#### Analisado 86 de 87 — problems/ITA2025Q1/rubric.json
Responsabilidade: rubrica de pontuação com max score e itens em `problems/ITA2025Q1/rubric.json:2`, `problems/ITA2025Q1/rubric.json:3` e `problems/ITA2025Q1/rubric.json:4`.
Fluxo de dados: consumido por `rubric_evaluator.py` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:23` e `app/confia_lean_auditor/rubric/rubric_evaluator.py:28`.
Entradas/saídas: define ids de rubrica, claim types e microclaims obrigatórios em `problems/ITA2025Q1/rubric.json:6`, `problems/ITA2025Q1/rubric.json:9`, `problems/ITA2025Q1/rubric.json:10`, `problems/ITA2025Q1/rubric.json:16`, `problems/ITA2025Q1/rubric.json:17`, `problems/ITA2025Q1/rubric.json:23`, `problems/ITA2025Q1/rubric.json:24`, `problems/ITA2025Q1/rubric.json:30`, `problems/ITA2025Q1/rubric.json:31`, `problems/ITA2025Q1/rubric.json:37` e `problems/ITA2025Q1/rubric.json:38`.
Padrões: configuração declarativa.
Anti-padrões e smells: schema não é validado antes do uso em `app/confia_lean_auditor/rubric/rubric_evaluator.py:45`.
Risco de refatoração: ALTO, por reger score e feedback.
<file-analyzed/>

#### Analisado 87 de 87 — pyproject.toml
Responsabilidade: manifesto Python, build backend setuptools, metadados e dependências em `pyproject.toml:1`, `pyproject.toml:3`, `pyproject.toml:5`, `pyproject.toml:6`, `pyproject.toml:7`, `pyproject.toml:9` e `pyproject.toml:10`.
Fluxo de dados: configura pacote a partir de `app` em `pyproject.toml:17`, `pyproject.toml:18`, `pyproject.toml:20` e `pyproject.toml:21`.
Entradas/saídas: entrada para build Python.
Padrões: PEP 621 com setuptools.
Anti-padrões e smells: `pytest` está em dependências runtime em `pyproject.toml:14`, e não há testes próprios observados no inventário operacional.
Risco de refatoração: MÉDIO, por afetar instalação e distribuição.
<file-analyzed/>

## 6. Preocupações transversais

Roteamento entre pipelines: há dois caminhos Lean. O HTTP gera `Attempt.lean` e `formal_steps/*.lean` em `app/confia_lean_auditor/lean/build_attempt.py:127`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:62` e `app/confia_lean_auditor/main.py:78`; a CLI verifica `problems/{problem_id}/certificate/Statement.lean` em `app/confia_lean_auditor/lean/run_lean.py:115`. Esses caminhos validam alvos diferentes.

Configuração: a raiz pode vir de `CONFIA_LEAN_AUDITOR_ROOT` em `app/confia_lean_auditor/core/paths.py:16`; não há `.env.example` no inventário operacional. A versão do app diverge da versão do pacote em `app/confia_lean_auditor/main.py:20`, `app/confia_lean_auditor/main.py:32` e `pyproject.toml:7`.

Logging e diagnóstico: não há logger estruturado no código próprio; a CLI imprime JSON com `print` em `app/confia_lean_auditor/lean/run_lean.py:138`. Saídas Lean inteiras entram em resposta/artefatos por `stdout` e `stderr` em `app/confia_lean_auditor/core/schemas.py:80`, `app/confia_lean_auditor/core/schemas.py:81`, `app/confia_lean_auditor/core/schemas.py:39` e `app/confia_lean_auditor/core/schemas.py:40`.

Tratamento de erro: `main.py` converte `InvalidProblemId` para 400 em `app/confia_lean_auditor/main.py:40`, `app/confia_lean_auditor/main.py:42` e `app/confia_lean_auditor/main.py:43`; problema inexistente vira 404 em `app/confia_lean_auditor/main.py:45` e `app/confia_lean_auditor/main.py:46`; `NotImplementedError` de geradores vira 501 em `app/confia_lean_auditor/main.py:61`, `app/confia_lean_auditor/main.py:62`, `app/confia_lean_auditor/main.py:72` e `app/confia_lean_auditor/main.py:73`; falta de microclaims vira 500 em `app/confia_lean_auditor/main.py:93` e `app/confia_lean_auditor/main.py:94`.

Segurança: `problem_id` tem regex e checagem de `relative_to` em `app/confia_lean_auditor/core/paths.py:8`, `app/confia_lean_auditor/core/paths.py:26`, `app/confia_lean_auditor/core/paths.py:40` e `app/confia_lean_auditor/core/paths.py:41`. O código Lean gerado insere `step.lhs`, `step.rhs` e `step.lean_method` vindos da extração em `app/confia_lean_auditor/lean/formal_step_evaluator.py:31`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:32`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:33` e `app/confia_lean_auditor/lean/formal_step_evaluator.py:34`; tokens proibidos são filtrados por regex em `app/confia_lean_auditor/lean/run_lean.py:13` a `app/confia_lean_auditor/lean/run_lean.py:18` e `app/confia_lean_auditor/lean/run_lean.py:27`.

Testes: `pytest` é declarado em `pyproject.toml:14`, mas não há arquivo de teste próprio no inventário operacional. Os exemplos em `problems/ITA2025Q1/examples/` não são referenciados pelo código de runtime; buscas por seus caminhos não aparecem fora dos próprios arquivos e artefatos.

Idioma e branding: nome do pacote usa `confia-lean-auditor` em `pyproject.toml:6`, Lake usa `confia_lean_auditor` em `lakefile.toml:1`, descrição usa `ConfIA Lean Auditor` em `pyproject.toml:8`, API expõe `ConfIA Lean Auditor` em `app/confia_lean_auditor/main.py:20` e `README.md` usa `confia_lean_auditor` em `README.md:1`.

Código morto e artefatos: `ConfiaLeanAuditor/Basic.lean` contém scaffold em `ConfiaLeanAuditor/Basic.lean:1`; `README.md` contém scaffold removível em `README.md:13`; `app/confia_lean_auditor.egg-info/*` são metadata gerada em `app/confia_lean_auditor.egg-info/PKG-INFO:1`; `artifacts/runs/**` são saídas produzidas pelo runtime em `app/confia_lean_auditor/main.py:123`, `app/confia_lean_auditor/main.py:128` e `app/confia_lean_auditor/main.py:129`; `.venv/` está rastreado apesar de não estar ignorado em `.gitignore:1`.

## 7. Tabela de risco

| Arquivo | Risco | Razão principal |
|---|---:|---|
| .github/workflows/create-release.yml | MÉDIO | Escreve release/tag com `contents: write` em `.github/workflows/create-release.yml:16`. |
| .github/workflows/lean_action_ci.yml | MÉDIO | Define validação Lean e docgen em `.github/workflows/lean_action_ci.yml:20` e `.github/workflows/lean_action_ci.yml:21`. |
| .github/workflows/update.yml | MÉDIO | Atualiza mathlib por action externa em `.github/workflows/update.yml:17` e `.github/workflows/update.yml:35`. |
| .gitignore | ALTO | Não ignora `.venv/`, enquanto só ignora `/.lake` em `.gitignore:1`. |
| AUDITORIA_REPOSITORIO.md | BAIXO | Documento diagnóstico, sem consumo runtime em `AUDITORIA_REPOSITORIO.md:1`. |
| ConfiaLeanAuditor.lean | BAIXO | Agregador Lean em `ConfiaLeanAuditor.lean:1` e `ConfiaLeanAuditor.lean:2`. |
| ConfiaLeanAuditor/Basic.lean | BAIXO | Scaffold `hello` em `ConfiaLeanAuditor/Basic.lean:1`. |
| ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean | ALTO | Contrato formal central em `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:7` a `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:28`. |
| README.md | BAIXO | Scaffold documental em `README.md:13`. |
| app/confia_lean_auditor.egg-info/PKG-INFO | BAIXO | Metadata gerada em `app/confia_lean_auditor.egg-info/PKG-INFO:1`. |
| app/confia_lean_auditor.egg-info/SOURCES.txt | MÉDIO | Metadata desatualizada não lista `main.py`, embora liste fontes em `app/confia_lean_auditor.egg-info/SOURCES.txt:1`. |
| app/confia_lean_auditor.egg-info/dependency_links.txt | BAIXO | Metadata vazia referida em `app/confia_lean_auditor.egg-info/SOURCES.txt:6`. |
| app/confia_lean_auditor.egg-info/requires.txt | MÉDIO | Duplica dependências e inclui `pytest` em `app/confia_lean_auditor.egg-info/requires.txt:4`. |
| app/confia_lean_auditor.egg-info/top_level.txt | BAIXO | Metadata top-level em `app/confia_lean_auditor.egg-info/top_level.txt:1`. |
| app/confia_lean_auditor/__init__.py | BAIXO | Marcador de pacote consumido por imports como `app/confia_lean_auditor/main.py:9`. |
| app/confia_lean_auditor/claims/__init__.py | BAIXO | Marcador de subpacote consumido por `app/confia_lean_auditor/main.py:9`. |
| app/confia_lean_auditor/claims/extract_claims.py | ALTO | Extrai claims que alimentam rubrica e Lean em `app/confia_lean_auditor/claims/extract_claims.py:117`. |
| app/confia_lean_auditor/core/__init__.py | BAIXO | Marcador de subpacote core. |
| app/confia_lean_auditor/core/paths.py | ALTO | Resolve raiz e problema em `app/confia_lean_auditor/core/paths.py:15` e `app/confia_lean_auditor/core/paths.py:34`. |
| app/confia_lean_auditor/core/schemas.py | ALTO | Contratos Pydantic compartilhados em `app/confia_lean_auditor/core/schemas.py:100`. |
| app/confia_lean_auditor/lean/__init__.py | BAIXO | Marcador de subpacote Lean. |
| app/confia_lean_auditor/lean/build_attempt.py | ALTO | Gera `Attempt.lean` em `app/confia_lean_auditor/lean/build_attempt.py:127`. |
| app/confia_lean_auditor/lean/formal_step_evaluator.py | ALTO | Insere formal steps em Lean gerado em `app/confia_lean_auditor/lean/formal_step_evaluator.py:31`. |
| app/confia_lean_auditor/lean/microclaim_evaluator.py | ALTO | Cruza microclaims e teoremas em `app/confia_lean_auditor/lean/microclaim_evaluator.py:62`. |
| app/confia_lean_auditor/lean/run_lean.py | ALTO | Executa subprocess Lean em `app/confia_lean_auditor/lean/run_lean.py:72`. |
| app/confia_lean_auditor/main.py | ALTO | Orquestra rota `/audit` em `app/confia_lean_auditor/main.py:36`. |
| app/confia_lean_auditor/reports/__init__.py | BAIXO | Marcador de subpacote reports. |
| app/confia_lean_auditor/reports/report_builder.py | MÉDIO | Define vereditos e feedback em `app/confia_lean_auditor/reports/report_builder.py:19` e `app/confia_lean_auditor/reports/report_builder.py:31`. |
| app/confia_lean_auditor/rubric/__init__.py | BAIXO | Marcador de subpacote rubric. |
| app/confia_lean_auditor/rubric/rubric_evaluator.py | ALTO | Calcula score em `app/confia_lean_auditor/rubric/rubric_evaluator.py:62` e `app/confia_lean_auditor/rubric/rubric_evaluator.py:63`. |
| artifacts/runs/** | BAIXO | Saídas geradas pelo runtime em `app/confia_lean_auditor/main.py:123`, `app/confia_lean_auditor/main.py:128` e `app/confia_lean_auditor/main.py:129`; risco de higiene/privacidade MÉDIO quando stdout inclui caminho absoluto em `artifacts/runs/20260703T144140_097860/audit.json:98`. |
| lake-manifest.json | MÉDIO | Lock de dependências Lean em `lake-manifest.json:4` a `lake-manifest.json:93`. |
| lakefile.toml | ALTO | Configura build Lean em `lakefile.toml:4`, `lakefile.toml:13` e `lakefile.toml:18`. |
| lean-toolchain | ALTO | Fixa compilador Lean em `lean-toolchain:1`. |
| problems/ITA2025Q1/certificate/Statement.lean | MÉDIO | CLI valida este arquivo em `app/confia_lean_auditor/lean/run_lean.py:115`. |
| problems/ITA2025Q1/examples/*.txt | BAIXO | Fixtures sem consumidor automatizado observado; exemplo correto começa em `problems/ITA2025Q1/examples/correct_solution.txt:1`. |
| problems/ITA2025Q1/microclaims.json | ALTO | Contrato de microclaims em `problems/ITA2025Q1/microclaims.json:3`. |
| problems/ITA2025Q1/problem.json | MÉDIO | Metadata oficial não lida no runtime auditado em `problems/ITA2025Q1/problem.json:2`. |
| problems/ITA2025Q1/rubric.json | ALTO | Contrato de pontuação em `problems/ITA2025Q1/rubric.json:4`. |
| pyproject.toml | MÉDIO | Define instalação e dependências em `pyproject.toml:10`. |

## 8. Ordem recomendada de investigação

1. Investigar artefatos gerados e metadata de build: `artifacts/runs/**`, `app/confia_lean_auditor.egg-info/*`, `README.md` e `ConfiaLeanAuditor/Basic.lean`, pois são baixo acoplamento runtime, mas revelam higiene e scaffold em `app/confia_lean_auditor/main.py:123`, `app/confia_lean_auditor.egg-info/PKG-INFO:1`, `README.md:13` e `ConfiaLeanAuditor/Basic.lean:1`.
2. Investigar fixtures e contratos de problema: `problems/ITA2025Q1/examples/*.txt`, `problem.json`, `rubric.json` e `microclaims.json`, porque fixtures não têm consumidor automatizado observado e os contratos JSON são lidos sem validação em `app/confia_lean_auditor/rubric/rubric_evaluator.py:45` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:62`.
3. Investigar fronteira de paths e empacotamento: `.gitignore`, `.venv/`, `pyproject.toml`, `core/paths.py` e egg-info, porque `.venv` aparece rastreado enquanto `.gitignore:1` ignora só `.lake`, e `get_repo_root` depende de `parents[3]` em `app/confia_lean_auditor/core/paths.py:22`.
4. Investigar extração textual e contratos Pydantic: `extract_claims.py` e `schemas.py`, porque `ClaimExtraction` alimenta formal steps, rubrica e microclaims em `app/confia_lean_auditor/claims/extract_claims.py:207`.
5. Investigar pipeline Lean: `formal_step_evaluator.py`, `build_attempt.py`, `run_lean.py` e `Statement.lean`, porque há geração de código, subprocess e classificação por string em `app/confia_lean_auditor/lean/formal_step_evaluator.py:31`, `app/confia_lean_auditor/lean/build_attempt.py:127`, `app/confia_lean_auditor/lean/run_lean.py:69` e `app/confia_lean_auditor/lean/run_lean.py:50`.
6. Investigar orquestração HTTP e decisões de produto: `main.py`, `rubric_evaluator.py`, `microclaim_evaluator.py` e `report_builder.py`, porque a partir daqui as decisões deixam de ser locais e afetam score, veredito, status público e contrato de API em `app/confia_lean_auditor/main.py:36`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:60`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:81` e `app/confia_lean_auditor/reports/report_builder.py:19`.
7. Investigar CI e toolchain por último quando a semântica local estiver entendida: `lakefile.toml`, `lean-toolchain`, `lake-manifest.json` e `.github/workflows/*`, porque mudanças aqui afetam build e release em `lakefile.toml:18`, `lean-toolchain:1`, `lake-manifest.json:4` e `.github/workflows/create-release.yml:19`.

## 9. Diário de revisão

- Hipótese inicial: `formal_step_evaluator.py` parecia órfão por ser arquivo novo não listado no egg-info; foi refutada porque `main.py` o importa em `app/confia_lean_auditor/main.py:13` e o chama em `app/confia_lean_auditor/main.py:55`.
- Hipótese inicial: `problems/ITA2025Q1/examples/*.txt` poderiam ser fixtures de teste; após busca, não há consumidor automatizado no código próprio, enquanto os runs duplicam os textos em `artifacts/runs/20260703T005858_740365/solution.txt:1`, `artifacts/runs/20260703T035633_483787/solution.txt:6` e `problems/ITA2025Q1/examples/wrong_determinant_step.txt:6`.
- Hipótese inicial: `problem.json` seria contrato runtime do problema; foi rebaixado a órfão funcional porque o fluxo valida apenas o diretório em `app/confia_lean_auditor/main.py:45` e os consumidores leem `rubric.json` e `microclaims.json` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:23` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:47`.
- Hipótese inicial: `ConfiaLeanAuditor/Basic.lean` seria módulo útil por ser importado em `ConfiaLeanAuditor.lean:1`; o conteúdo refutou uso semântico, pois a única definição é `def hello := "world"` em `ConfiaLeanAuditor/Basic.lean:1`.
- Hipótese inicial: artefatos em `artifacts/runs` seriam apenas exemplos manuais; a refutação mostrou que são saídas do próprio runtime, pois `main.py` grava `audit.json`, `solution.txt` e `claims.json` em `app/confia_lean_auditor/main.py:123`, `app/confia_lean_auditor/main.py:128` e `app/confia_lean_auditor/main.py:129`.
- Hipótese inicial: o contrato de área dependia apenas de claim textual; a Fase 4 mostrou o encontro com formal steps: `microclaims.json` exige `determinant_expansion` em `problems/ITA2025Q1/microclaims.json:16`, `formal_step_evaluator.py` marca status em `app/confia_lean_auditor/lean/formal_step_evaluator.py:67`, e runs com determinante errado registram `formal_steps_not_verified` em `artifacts/runs/20260703T144140_097860/audit.json:200`.
- Hipótese inicial: o inventário poderia ser apenas os 87 arquivos de primeira parte; a checagem com Git mostrou `.venv/` versionado com Python `3.9.6` em `.venv/pyvenv.cfg:3` e `.gitignore` sem regra para `.venv` em `.gitignore:1`, alterando o diagnóstico para incluir um achado transversal de dependências materializadas.
