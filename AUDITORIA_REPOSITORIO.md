# Auditoria descritiva do repositório

## 1. Visão geral do projeto

O projeto se identifica como `confia-lean-auditor`, versão Python `0.1.0`, com descrição "corretor matemático com rubrica e certificados Lean" em `pyproject.toml:6`, `pyproject.toml:7` e `pyproject.toml:8`. O runtime Python exige `>=3.9` e declara `fastapi`, `uvicorn`, `pydantic>=2` e `pytest` em `pyproject.toml:9`, `pyproject.toml:11`, `pyproject.toml:12`, `pyproject.toml:13` e `pyproject.toml:14`. O runtime Lean é fixado em `leanprover/lean4:v4.28.0` em `lean-toolchain:1`, e Lake declara o pacote `confia_lean_auditor` com alvo padrão `ConfiaLeanAuditor` em `lakefile.toml:1` e `lakefile.toml:4`. A dependência Lean direta é `mathlib` em `lakefile.toml:12`, `lakefile.toml:13` e `lakefile.toml:15`, com lock expandido em `lake-manifest.json:4`, `lake-manifest.json:9` e `lake-manifest.json:11`.

O padrão arquitetural observado é um monolito pequeno em camadas, com API FastAPI como entrada, heurística textual de claims, avaliação de rubrica, geração de arquivo Lean, execução de `lake env lean` e persistência de artefatos no filesystem. A API é criada em `app/confia_lean_auditor/main.py:18`, expõe `/health` em `app/confia_lean_auditor/main.py:25` e `/audit` em `app/confia_lean_auditor/main.py:34`. A CLI Lean paralela vive em `app/confia_lean_auditor/lean/run_lean.py:116`, recebe `--problem-id` e `--repo-root` em `app/confia_lean_auditor/lean/run_lean.py:118` e `app/confia_lean_auditor/lean/run_lean.py:119`, e imprime JSON em `app/confia_lean_auditor/lean/run_lean.py:123`.

Inventário cru auditado: 59 arquivos de primeira parte na árvore de trabalho, excluindo `.git`, `.venv` e `.lake` como dependências/cache materializados. Essa exclusão de escopo fica registrada porque `.gitignore` só ignora `/.lake` em `.gitignore:1`, enquanto o manifesto Python e os artefatos de execução aparecem na árvore do projeto em `app/confia_lean_auditor.egg-info/SOURCES.txt:4`, `app/confia_lean_auditor.egg-info/SOURCES.txt:5`, `app/confia_lean_auditor/main.py:43`, `app/confia_lean_auditor/main.py:96`, `app/confia_lean_auditor/main.py:101` e `app/confia_lean_auditor/main.py:102`.

Módulos em uma linha: `main.py` orquestra a requisição HTTP em `app/confia_lean_auditor/main.py:34`; `schemas.py` define contratos Pydantic em `app/confia_lean_auditor/core/schemas.py:8`; `extract_claims.py` extrai claims heurísticas para `ITA2025Q1` em `app/confia_lean_auditor/claims/extract_claims.py:140`; `rubric_evaluator.py` lê `rubric.json` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:27`; `build_attempt.py` gera `Attempt.lean` em `app/confia_lean_auditor/lean/build_attempt.py:115`; `run_lean.py` executa Lean por subprocess em `app/confia_lean_auditor/lean/run_lean.py:67`; `microclaim_evaluator.py` cruza microclaims, claims e teoremas em `app/confia_lean_auditor/lean/microclaim_evaluator.py:32`; `report_builder.py` monta feedback textual em `app/confia_lean_auditor/reports/report_builder.py:31`; `problems/ITA2025Q1/*.json` são contratos de problema, rubrica e microclaims em `problems/ITA2025Q1/problem.json:2`, `problems/ITA2025Q1/rubric.json:4` e `problems/ITA2025Q1/microclaims.json:3`; `ConfiaLeanAuditor.lean` só importa `Basic` em `ConfiaLeanAuditor.lean:1`, e `Basic.lean` contém scaffold `hello` em `ConfiaLeanAuditor/Basic.lean:1`.

## 2. Diagrama de arquitetura textual

```
Cliente HTTP
  -> FastAPI app /audit
     -> AuditRequest(Pydantic)
     -> problems/{problem_id}/ existe?
     -> extract_claims(problem_id, solution)
     -> problems/{problem_id}/rubric.json
     -> evaluate_rubric(...)
     -> build_attempt(...): artifacts/runs/{run_id}/Attempt.lean
     -> run_lean_file(...): lake env lean Attempt.lean
     -> LeanCertificate(Pydantic)
     -> problems/{problem_id}/microclaims.json
     -> evaluate_microclaims(...)
     -> verdict_from_score + build_feedback
     -> AuditResponse(Pydantic)
     -> artifacts/runs/{run_id}/audit.json, solution.txt, claims.json

CLI Python
  -> python app/confia_lean_auditor/lean/run_lean.py --problem-id X
     -> problems/{problem_id}/certificate/Statement.lean
     -> lake env lean Statement.lean
     -> JSON em stdout

CI Lean
  -> GitHub Actions
     -> checkout
     -> leanprover/lean-action
     -> docgen-action
```

O fluxo HTTP deriva `problem_dir` de `req.problem_id` em `app/confia_lean_auditor/main.py:37`, cria `artifact_dir` em `app/confia_lean_auditor/main.py:43` e `app/confia_lean_auditor/main.py:44`, e grava três saídas persistentes em `app/confia_lean_auditor/main.py:96`, `app/confia_lean_auditor/main.py:101` e `app/confia_lean_auditor/main.py:102`. O fluxo CLI usa outro ponto de entrada de certificado, `Statement.lean`, em `app/confia_lean_auditor/lean/run_lean.py:99` e `app/confia_lean_auditor/lean/run_lean.py:100`.

## 3. Grafo de dependências

### Python: imports estáticos

- `app/confia_lean_auditor/main.py` importa FastAPI e HTTPException em `app/confia_lean_auditor/main.py:7`; importa `extract_claims` em `app/confia_lean_auditor/main.py:9`; importa schemas em `app/confia_lean_auditor/main.py:10`; importa `build_attempt` em `app/confia_lean_auditor/main.py:11`; importa `evaluate_microclaims` em `app/confia_lean_auditor/main.py:12`; importa `run_lean_file` em `app/confia_lean_auditor/main.py:13`; importa report builder em `app/confia_lean_auditor/main.py:14`; importa rubric evaluator em `app/confia_lean_auditor/main.py:15`.
- `app/confia_lean_auditor/claims/extract_claims.py` importa regex, Unicode e tipos em `app/confia_lean_auditor/claims/extract_claims.py:3`, `app/confia_lean_auditor/claims/extract_claims.py:4` e `app/confia_lean_auditor/claims/extract_claims.py:5`; importa `ClaimExtraction` e `ExtractedClaim` em `app/confia_lean_auditor/claims/extract_claims.py:7`.
- `app/confia_lean_auditor/rubric/rubric_evaluator.py` importa JSON e `Path` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:3` e `app/confia_lean_auditor/rubric/rubric_evaluator.py:4`; importa schemas em `app/confia_lean_auditor/rubric/rubric_evaluator.py:7`.
- `app/confia_lean_auditor/lean/build_attempt.py` importa `Path` e tipos em `app/confia_lean_auditor/lean/build_attempt.py:3` e `app/confia_lean_auditor/lean/build_attempt.py:4`; importa `ClaimExtraction` em `app/confia_lean_auditor/lean/build_attempt.py:6`.
- `app/confia_lean_auditor/lean/run_lean.py` importa `argparse`, `json`, `re`, `subprocess`, `Path` e tipos em `app/confia_lean_auditor/lean/run_lean.py:3`, `app/confia_lean_auditor/lean/run_lean.py:4`, `app/confia_lean_auditor/lean/run_lean.py:5`, `app/confia_lean_auditor/lean/run_lean.py:6`, `app/confia_lean_auditor/lean/run_lean.py:7` e `app/confia_lean_auditor/lean/run_lean.py:8`.
- `app/confia_lean_auditor/lean/microclaim_evaluator.py` importa JSON, `Path`, tipos e schemas em `app/confia_lean_auditor/lean/microclaim_evaluator.py:3`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:4`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:5` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:7`.
- `app/confia_lean_auditor/reports/report_builder.py` importa tipos e schemas em `app/confia_lean_auditor/reports/report_builder.py:3` e `app/confia_lean_auditor/reports/report_builder.py:5`.

### Python: imports inversos

- `core/schemas.py` é consumido por `extract_claims.py`, `rubric_evaluator.py`, `build_attempt.py`, `microclaim_evaluator.py`, `report_builder.py` e `main.py`, conforme `app/confia_lean_auditor/claims/extract_claims.py:7`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:7`, `app/confia_lean_auditor/lean/build_attempt.py:6`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:7`, `app/confia_lean_auditor/reports/report_builder.py:5` e `app/confia_lean_auditor/main.py:10`.
- `claims/extract_claims.py`, `lean/build_attempt.py`, `lean/microclaim_evaluator.py`, `lean/run_lean.py`, `reports/report_builder.py` e `rubric/rubric_evaluator.py` são consumidos por `main.py` em `app/confia_lean_auditor/main.py:9`, `app/confia_lean_auditor/main.py:11`, `app/confia_lean_auditor/main.py:12`, `app/confia_lean_auditor/main.py:13`, `app/confia_lean_auditor/main.py:14` e `app/confia_lean_auditor/main.py:15`.
- Os arquivos `__init__.py` estão vazios e não exportam nomes, evidenciados por contagem zero em `app/confia_lean_auditor/__init__.py:0`, `app/confia_lean_auditor/claims/__init__.py:0`, `app/confia_lean_auditor/core/__init__.py:0`, `app/confia_lean_auditor/lean/__init__.py:0`, `app/confia_lean_auditor/reports/__init__.py:0` e `app/confia_lean_auditor/rubric/__init__.py:0`.

### Lean: imports estáticos e inversos

- `ConfiaLeanAuditor.lean` importa `ConfiaLeanAuditor.Basic` em `ConfiaLeanAuditor.lean:1`.
- `ConfiaLeanAuditor/Basic.lean` define apenas `hello` em `ConfiaLeanAuditor/Basic.lean:1`.
- `problems/ITA2025Q1/certificate/Statement.lean` importa `Mathlib` em `problems/ITA2025Q1/certificate/Statement.lean:1` e define a namespace do certificado em `problems/ITA2025Q1/certificate/Statement.lean:3`.
- Os `Attempt.lean` versionados ou não rastreados importam `Mathlib`, por exemplo `artifacts/runs/20260703T005732_426318/Attempt.lean:2`, `artifacts/runs/20260703T005858_740365/Attempt.lean:2`, `artifacts/runs/20260703T011235_219542/Attempt.lean:2` e `artifacts/runs/20260703T011304_967627/Attempt.lean:2`.

### Acoplamento dinâmico

- `main.py` acopla `problem_id` a `problems/{problem_id}` por caminho montado em runtime em `app/confia_lean_auditor/main.py:37`.
- `rubric_evaluator.py` acopla `problem_id` a `problems/{problem_id}/rubric.json` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:27`.
- `microclaim_evaluator.py` acopla `problem_id` a `problems/{problem_id}/microclaims.json` em `app/confia_lean_auditor/lean/microclaim_evaluator.py:21`.
- `build_attempt.py` acopla claims textuais a teoremas gerados por strings em `app/confia_lean_auditor/lean/build_attempt.py:96`, `app/confia_lean_auditor/lean/build_attempt.py:100`, `app/confia_lean_auditor/lean/build_attempt.py:105` e `app/confia_lean_auditor/lean/build_attempt.py:109`.
- `run_lean.py` acopla o sistema ao executável externo `lake env lean` em `app/confia_lean_auditor/lean/run_lean.py:67` e ao diretório de trabalho `repo_root` em `app/confia_lean_auditor/lean/run_lean.py:72`.
- `main.py` grava `audit.json`, `solution.txt` e `claims.json`, tornando o filesystem um contrato entre execução e artefatos versionados em `app/confia_lean_auditor/main.py:96`, `app/confia_lean_auditor/main.py:101` e `app/confia_lean_auditor/main.py:102`.
- GitHub Actions executa ações Lean externas em `.github/workflows/lean_action_ci.yml:19`, `.github/workflows/lean_action_ci.yml:20` e `.github/workflows/lean_action_ci.yml:21`, e o workflow de update usa `mathlib-update-action` em `.github/workflows/update.yml:17` e `.github/workflows/update.yml:35`.

### Ciclos e órfãos

Não há ciclo estático entre os módulos Python listados; `main.py` depende dos serviços, e os serviços dependem dos schemas. O módulo Lean `ConfiaLeanAuditor/Basic.lean` é importado por `ConfiaLeanAuditor.lean` em `ConfiaLeanAuditor.lean:1`, mas seu conteúdo é scaffold em `ConfiaLeanAuditor/Basic.lean:1`. O certificado fixo `Statement.lean` não é usado pelo endpoint `/audit`, que chama `build_attempt` em `app/confia_lean_auditor/main.py:54` e depois `run_lean_file` sobre `attempt_path` em `app/confia_lean_auditor/main.py:63` e `app/confia_lean_auditor/main.py:66`; ele é usado pelo fluxo CLI `run_problem` em `app/confia_lean_auditor/lean/run_lean.py:99` e `app/confia_lean_auditor/lean/run_lean.py:113`.

## 4. Pontos de entrada e de saída consolidados

Entradas: `GET /health` retorna status fixo em `app/confia_lean_auditor/main.py:25`, `app/confia_lean_auditor/main.py:27` e `app/confia_lean_auditor/main.py:30`; `POST /audit` recebe `AuditRequest` em `app/confia_lean_auditor/main.py:34` e `app/confia_lean_auditor/core/schemas.py:8`; a CLI `run_lean.py` recebe `--problem-id` e `--repo-root` em `app/confia_lean_auditor/lean/run_lean.py:118` e `app/confia_lean_auditor/lean/run_lean.py:119`; CI executa em push, pull request e dispatch em `.github/workflows/lean_action_ci.yml:3`, `.github/workflows/lean_action_ci.yml:4`, `.github/workflows/lean_action_ci.yml:5` e `.github/workflows/lean_action_ci.yml:6`.

Saídas: `AuditResponse` inclui score, verdict, claims, rubrica, certificado Lean, microclaims, feedback e artifact_dir em `app/confia_lean_auditor/core/schemas.py:65` a `app/confia_lean_auditor/core/schemas.py:75`; `audit.json` é produzido por `main.py` em `app/confia_lean_auditor/main.py:96`; `solution.txt` é produzido por `main.py` em `app/confia_lean_auditor/main.py:101`; `claims.json` é produzido por `main.py` em `app/confia_lean_auditor/main.py:102`; `Attempt.lean` é produzido por `build_attempt.py` em `app/confia_lean_auditor/lean/build_attempt.py:115` e `app/confia_lean_auditor/lean/build_attempt.py:116`; a CLI imprime JSON em stdout em `app/confia_lean_auditor/lean/run_lean.py:123`.

## 5. Análise módulo a módulo

### Lote 1: arquivos 1-10 de 59

#### Analisado 1 de 59 — .github/workflows/create-release.yml
Responsabilidade: cria release/tag Lean quando `lean-toolchain` muda em push para `main` ou `master`, conforme `.github/workflows/create-release.yml:3`, `.github/workflows/create-release.yml:5`, `.github/workflows/create-release.yml:7` e `.github/workflows/create-release.yml:9`.
Fluxo de dados: consome `lean-toolchain` como filtro de path em `.github/workflows/create-release.yml:8` e `.github/workflows/create-release.yml:9`; usa `GITHUB_TOKEN` em `.github/workflows/create-release.yml:22`.
Entradas/saídas: entrada é push em `.github/workflows/create-release.yml:4`; saída é ação `lean-release-tag` com `do-release: true` em `.github/workflows/create-release.yml:18`, `.github/workflows/create-release.yml:19` e `.github/workflows/create-release.yml:21`.
Padrões: workflow declarativo de release.
Anti-padrões e smells: permissão `contents: write` fica no job em `.github/workflows/create-release.yml:15` e `.github/workflows/create-release.yml:16`; isso é superfície de escrita em CI.
Risco de refatoração: MÉDIO, porque altera publicação/release.
<file-analyzed/>

#### Analisado 2 de 59 — .github/workflows/lean_action_ci.yml
Responsabilidade: roda CI Lean e documentação em push, pull request e dispatch em `.github/workflows/lean_action_ci.yml:3` a `.github/workflows/lean_action_ci.yml:6`.
Fluxo de dados: faz checkout e executa `lean-action` e `docgen-action` em `.github/workflows/lean_action_ci.yml:19`, `.github/workflows/lean_action_ci.yml:20` e `.github/workflows/lean_action_ci.yml:21`.
Entradas/saídas: entrada são eventos GitHub; saída inclui build Lean e Pages/docgen com permissões em `.github/workflows/lean_action_ci.yml:9`, `.github/workflows/lean_action_ci.yml:11` e `.github/workflows/lean_action_ci.yml:12`.
Padrões: pipeline CI declarativo.
Anti-padrões e smells: CI cobre Lean, mas não executa pytest nem API Python; o arquivo só possui `leanprover/lean-action` e `docgen-action` em `.github/workflows/lean_action_ci.yml:20` e `.github/workflows/lean_action_ci.yml:21`.
Risco de refatoração: MÉDIO, porque é o único CI ativo de build.
<file-analyzed/>

#### Analisado 3 de 59 — .github/workflows/update.yml
Responsabilidade: checa e aplica updates de mathlib manualmente em `.github/workflows/update.yml:1`, `.github/workflows/update.yml:6` e `.github/workflows/update.yml:17`.
Fluxo de dados: `check-for-updates` emite `is-update-available` e `new-tags` em `.github/workflows/update.yml:11`, `.github/workflows/update.yml:12` e `.github/workflows/update.yml:13`; `do-update` consome esses outputs em `.github/workflows/update.yml:26`, `.github/workflows/update.yml:27` e `.github/workflows/update.yml:31`.
Entradas/saídas: entrada é `workflow_dispatch` em `.github/workflows/update.yml:6`; saída é PR ou issue em `.github/workflows/update.yml:39` e `.github/workflows/update.yml:40`.
Padrões: automação de atualização com job gateado por output.
Anti-padrões e smells: schedule está comentado em `.github/workflows/update.yml:4` e `.github/workflows/update.yml:5`, então não há atualização periódica efetiva.
Risco de refatoração: MÉDIO, porque afeta cadeia de dependências Lean.
<file-analyzed/>

#### Analisado 4 de 59 — .gitignore
Responsabilidade: ignora apenas Lake local em `.gitignore:1`.
Fluxo de dados: afeta versionamento de `/.lake` em `.gitignore:1`.
Entradas/saídas: sem execução.
Padrões: configuração mínima de Git.
Anti-padrões e smells: `.venv`, `artifacts/` e `*.egg-info` não aparecem no ignore; a única regra é `/.lake` em `.gitignore:1`.
Risco de refatoração: BAIXO, mas tem impacto transversal de versionamento.
<file-analyzed/>

#### Analisado 5 de 59 — ConfiaLeanAuditor.lean
Responsabilidade: módulo raiz Lean que importa `ConfiaLeanAuditor.Basic` em `ConfiaLeanAuditor.lean:1`.
Fluxo de dados: sem dados; define inclusão de módulo no alvo Lake por import.
Entradas/saídas: exporta transitivamente o conteúdo de `Basic`.
Padrões: arquivo raiz de biblioteca Lean.
Anti-padrões e smells: depende de `Basic`, cujo conteúdo é scaffold `hello` em `ConfiaLeanAuditor/Basic.lean:1`.
Risco de refatoração: BAIXO, porque tem uma linha e baixo acoplamento.
<file-analyzed/>

#### Analisado 6 de 59 — ConfiaLeanAuditor/Basic.lean
Responsabilidade: define `hello := "world"` em `ConfiaLeanAuditor/Basic.lean:1`.
Fluxo de dados: sem entrada ou saída.
Entradas/saídas: exporta o símbolo `hello`.
Padrões: scaffold de Lake.
Anti-padrões e smells: boilerplate de scaffold presente em `ConfiaLeanAuditor/Basic.lean:1`.
Risco de refatoração: BAIXO, porque não aparece no fluxo Python/API.
<file-analyzed/>

#### Analisado 7 de 59 — README.md
Responsabilidade: contém instrução genérica de setup GitHub em `README.md:3` a `README.md:12`.
Fluxo de dados: sem execução.
Entradas/saídas: documento para mantenedores.
Padrões: README de scaffold.
Anti-padrões e smells: o texto diz que a seção pode ser removida depois do setup em `README.md:13`, indicando boilerplate remanescente.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 8 de 59 — app/confia_lean_auditor.egg-info/PKG-INFO
Responsabilidade: metadata de pacote gerada com nome, versão, resumo e dependências em `app/confia_lean_auditor.egg-info/PKG-INFO:2` a `app/confia_lean_auditor.egg-info/PKG-INFO:9`.
Fluxo de dados: reflete `pyproject.toml`, não executa lógica.
Entradas/saídas: consumido por ferramentas de packaging.
Padrões: artefato de build Python.
Anti-padrões e smells: arquivo gerado versionado, categoria saída de execução/build, com metadata derivada em `app/confia_lean_auditor.egg-info/PKG-INFO:1`.
Risco de refatoração: BAIXO para produto, MÉDIO para packaging.
<file-analyzed/>

#### Analisado 9 de 59 — app/confia_lean_auditor.egg-info/SOURCES.txt
Responsabilidade: lista fontes empacotadas em `app/confia_lean_auditor.egg-info/SOURCES.txt:1` a `app/confia_lean_auditor.egg-info/SOURCES.txt:12`.
Fluxo de dados: informa packaging.
Entradas/saídas: consumido por setuptools.
Padrões: manifesto gerado.
Anti-padrões e smells: a lista inclui `core`, `lean`, `reports` e `rubric` em `app/confia_lean_auditor.egg-info/SOURCES.txt:9` a `app/confia_lean_auditor.egg-info/SOURCES.txt:12`, mas não lista `claims/extract_claims.py` nem `main.py`; isso diverge da árvore de código usada por `main.py` em `app/confia_lean_auditor/main.py:9` e `app/confia_lean_auditor/main.py:18`.
Risco de refatoração: MÉDIO, porque sinaliza metadata de distribuição defasada.
<file-analyzed/>

#### Analisado 10 de 59 — app/confia_lean_auditor.egg-info/dependency_links.txt
Responsabilidade: arquivo gerado vazio de links de dependência.
Fluxo de dados: sem conteúdo operacional.
Entradas/saídas: consumido por tooling legado de packaging.
Padrões: artefato de build.
Anti-padrões e smells: arquivo gerado versionado e vazio em `app/confia_lean_auditor.egg-info/dependency_links.txt:1`.
Risco de refatoração: BAIXO.
<file-analyzed/>

### Lote 2: arquivos 11-20 de 59

#### Analisado 11 de 59 — app/confia_lean_auditor.egg-info/requires.txt
Responsabilidade: declara dependências instaladas `fastapi`, `uvicorn`, `pydantic>=2` e `pytest` em `app/confia_lean_auditor.egg-info/requires.txt:1` a `app/confia_lean_auditor.egg-info/requires.txt:4`.
Fluxo de dados: metadata de instalação.
Entradas/saídas: consumido por packaging.
Padrões: arquivo gerado.
Anti-padrões e smells: `pytest` aparece como dependência runtime em `app/confia_lean_auditor.egg-info/requires.txt:4` e em `pyproject.toml:14`, mas não há workflow que execute pytest em `.github/workflows/lean_action_ci.yml:19` a `.github/workflows/lean_action_ci.yml:21`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 12 de 59 — app/confia_lean_auditor.egg-info/top_level.txt
Responsabilidade: declara pacote top-level `confia_lean_auditor` em `app/confia_lean_auditor.egg-info/top_level.txt:1`.
Fluxo de dados: metadata de import.
Entradas/saídas: consumido por packaging.
Padrões: arquivo gerado.
Anti-padrões e smells: artefato de build versionado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 13 de 59 — app/confia_lean_auditor/__init__.py
Responsabilidade: marca pacote Python; vazio em `app/confia_lean_auditor/__init__.py:0`.
Fluxo de dados: sem entrada/saída.
Entradas/saídas: habilita import de pacote.
Padrões: marcador de pacote.
Anti-padrões e smells: nenhum conteúdo.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 14 de 59 — app/confia_lean_auditor/claims/__init__.py
Responsabilidade: marca subpacote `claims`; vazio em `app/confia_lean_auditor/claims/__init__.py:0`.
Fluxo de dados: sem entrada/saída.
Entradas/saídas: habilita import de `claims`.
Padrões: marcador de pacote.
Anti-padrões e smells: nenhum conteúdo.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 15 de 59 — app/confia_lean_auditor/claims/extract_claims.py
Responsabilidade: normaliza texto e extrai claims para `ITA2025Q1`, com dispatch por `problem_id` em `app/confia_lean_auditor/claims/extract_claims.py:140` a `app/confia_lean_auditor/claims/extract_claims.py:144`.
Fluxo de dados: recebe `solution`, normaliza em `app/confia_lean_auditor/claims/extract_claims.py:10` a `app/confia_lean_auditor/claims/extract_claims.py:17`, e retorna `ClaimExtraction` em `app/confia_lean_auditor/claims/extract_claims.py:137`.
Entradas/saídas: exporta `extract_claims`, `extract_claims_ita2025q1`, `normalize` e `make_claim`; produz `ExtractedClaim` com id, type, text, evidence e normalized em `app/confia_lean_auditor/claims/extract_claims.py:28` a `app/confia_lean_auditor/claims/extract_claims.py:35`.
Padrões: parser heurístico baseado em padrões.
Anti-padrões e smells: strings mágicas de claim types e padrões textuais aparecem em `app/confia_lean_auditor/claims/extract_claims.py:52`, `app/confia_lean_auditor/claims/extract_claims.py:71`, `app/confia_lean_auditor/claims/extract_claims.py:92`, `app/confia_lean_auditor/claims/extract_claims.py:108` e `app/confia_lean_auditor/claims/extract_claims.py:128`; o problema suportado é hardcoded em `app/confia_lean_auditor/claims/extract_claims.py:141`.
Risco de refatoração: ALTO, porque seus `claim_type` alimentam rubrica, microclaims e geração Lean.
<file-analyzed/>

#### Analisado 16 de 59 — app/confia_lean_auditor/core/__init__.py
Responsabilidade: marca subpacote `core`; vazio em `app/confia_lean_auditor/core/__init__.py:0`.
Fluxo de dados: sem entrada/saída.
Entradas/saídas: habilita import de schemas.
Padrões: marcador de pacote.
Anti-padrões e smells: nenhum conteúdo.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 17 de 59 — app/confia_lean_auditor/core/schemas.py
Responsabilidade: define todos os contratos Pydantic de requisição, resposta, rubrica, Lean e microclaims em `app/confia_lean_auditor/core/schemas.py:8`, `app/confia_lean_auditor/core/schemas.py:13`, `app/confia_lean_auditor/core/schemas.py:22`, `app/confia_lean_auditor/core/schemas.py:27`, `app/confia_lean_auditor/core/schemas.py:37`, `app/confia_lean_auditor/core/schemas.py:43`, `app/confia_lean_auditor/core/schemas.py:55` e `app/confia_lean_auditor/core/schemas.py:65`.
Fluxo de dados: recebe dados externos via `AuditRequest` em `app/confia_lean_auditor/core/schemas.py:8`; estrutura resposta final em `AuditResponse` em `app/confia_lean_auditor/core/schemas.py:65`.
Entradas/saídas: exporta classes Pydantic.
Padrões: DTO/schema central.
Anti-padrões e smells: `problem_id` e `solution` não têm validação além de tipo em `app/confia_lean_auditor/core/schemas.py:9` e `app/confia_lean_auditor/core/schemas.py:10`; campos de erro/stdout/stderr Lean são retornáveis no contrato em `app/confia_lean_auditor/core/schemas.py:49` e `app/confia_lean_auditor/core/schemas.py:50`.
Risco de refatoração: ALTO, porque é contrato compartilhado por todos os módulos.
<file-analyzed/>

#### Analisado 18 de 59 — app/confia_lean_auditor/lean/__init__.py
Responsabilidade: marca subpacote `lean`; vazio em `app/confia_lean_auditor/lean/__init__.py:0`.
Fluxo de dados: sem entrada/saída.
Entradas/saídas: habilita import de módulos Lean.
Padrões: marcador de pacote.
Anti-padrões e smells: nenhum conteúdo.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 19 de 59 — app/confia_lean_auditor/lean/build_attempt.py
Responsabilidade: monta código Lean gerado por claims e grava `Attempt.lean` em `app/confia_lean_auditor/lean/build_attempt.py:115` e `app/confia_lean_auditor/lean/build_attempt.py:116`.
Fluxo de dados: recebe `ClaimExtraction`, calcula `types` em `app/confia_lean_auditor/lean/build_attempt.py:91`, adiciona teoremas conforme tipos em `app/confia_lean_auditor/lean/build_attempt.py:96`, `app/confia_lean_auditor/lean/build_attempt.py:100`, `app/confia_lean_auditor/lean/build_attempt.py:105` e `app/confia_lean_auditor/lean/build_attempt.py:109`, e retorna path + teoremas em `app/confia_lean_auditor/lean/build_attempt.py:118` a `app/confia_lean_auditor/lean/build_attempt.py:121`.
Entradas/saídas: exporta `build_attempt`; saída é arquivo Lean e lista `generated_theorems`.
Padrões: gerador de código por templates.
Anti-padrões e smells: o parâmetro `repo_root` é recebido em `app/confia_lean_auditor/lean/build_attempt.py:125`, mas não é usado no corpo de dispatch em `app/confia_lean_auditor/lean/build_attempt.py:130` a `app/confia_lean_auditor/lean/build_attempt.py:133`; há strings de teoremas duplicadas entre código e JSON em `app/confia_lean_auditor/lean/build_attempt.py:98`, `app/confia_lean_auditor/lean/build_attempt.py:103`, `app/confia_lean_auditor/lean/build_attempt.py:107`, `app/confia_lean_auditor/lean/build_attempt.py:111` e `problems/ITA2025Q1/microclaims.json:7`.
Risco de refatoração: ALTO, porque é ponte entre texto e certificado Lean.
<file-analyzed/>

#### Analisado 20 de 59 — app/confia_lean_auditor/lean/microclaim_evaluator.py
Responsabilidade: avalia microclaims a partir de JSON, claims extraídas, teoremas gerados e status Lean em `app/confia_lean_auditor/lean/microclaim_evaluator.py:14` a `app/confia_lean_auditor/lean/microclaim_evaluator.py:20`.
Fluxo de dados: lê `microclaims.json` em `app/confia_lean_auditor/lean/microclaim_evaluator.py:21` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:26`; compara `claim_types` e `generated_theorems` em `app/confia_lean_auditor/lean/microclaim_evaluator.py:27`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:28`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:36` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:42`.
Entradas/saídas: retorna lista de `MicroclaimResult` em `app/confia_lean_auditor/lean/microclaim_evaluator.py:53` a `app/confia_lean_auditor/lean/microclaim_evaluator.py:63`.
Padrões: validador de contrato por tabela.
Anti-padrões e smells: se `microclaims.json` não existe, retorna lista vazia em `app/confia_lean_auditor/lean/microclaim_evaluator.py:23` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:24`, fallback que mascara ausência de contrato.
Risco de refatoração: ALTO, porque cruza JSON, claims e Lean.
<file-analyzed/>

### Lote 3: arquivos 21-30 de 59

#### Analisado 21 de 59 — app/confia_lean_auditor/lean/run_lean.py
Responsabilidade: detecta tokens proibidos, executa Lean via Lake e classifica o resultado em `app/confia_lean_auditor/lean/run_lean.py:25`, `app/confia_lean_auditor/lean/run_lean.py:36` e `app/confia_lean_auditor/lean/run_lean.py:63`.
Fluxo de dados: lê arquivo Lean em `app/confia_lean_auditor/lean/run_lean.py:64`; executa `lake env lean` em `app/confia_lean_auditor/lean/run_lean.py:67` a `app/confia_lean_auditor/lean/run_lean.py:77`; retorna dict com status, compiled, exit_code, stdout e stderr em `app/confia_lean_auditor/lean/run_lean.py:88` a `app/confia_lean_auditor/lean/run_lean.py:96`.
Entradas/saídas: exporta `run_lean_file`, `run_problem` e CLI `main`; imprime JSON em `app/confia_lean_auditor/lean/run_lean.py:123`.
Padrões: adapter de subprocess.
Anti-padrões e smells: classifica por substrings em stderr/stdout em `app/confia_lean_auditor/lean/run_lean.py:42`, `app/confia_lean_auditor/lean/run_lean.py:48`, `app/confia_lean_auditor/lean/run_lean.py:51`, `app/confia_lean_auditor/lean/run_lean.py:54` e `app/confia_lean_auditor/lean/run_lean.py:57`; expõe stdout/stderr no contrato em `app/confia_lean_auditor/lean/run_lean.py:94` e `app/confia_lean_auditor/lean/run_lean.py:95`.
Risco de refatoração: ALTO, porque encapsula processo externo e status semântico.
<file-analyzed/>

#### Analisado 22 de 59 — app/confia_lean_auditor/main.py
Responsabilidade: define API FastAPI, healthcheck e orquestra a auditoria completa em `app/confia_lean_auditor/main.py:18`, `app/confia_lean_auditor/main.py:25` e `app/confia_lean_auditor/main.py:34`.
Fluxo de dados: `AuditRequest` entra em `app/confia_lean_auditor/main.py:34`; passa por extração, rubrica, geração Lean, execução Lean, microclaims e feedback em `app/confia_lean_auditor/main.py:46`, `app/confia_lean_auditor/main.py:49`, `app/confia_lean_auditor/main.py:54`, `app/confia_lean_auditor/main.py:66`, `app/confia_lean_auditor/main.py:72`, `app/confia_lean_auditor/main.py:80` e `app/confia_lean_auditor/main.py:81`.
Entradas/saídas: retorna `AuditResponse` em `app/confia_lean_auditor/main.py:83` a `app/confia_lean_auditor/main.py:94`; grava artefatos em `app/confia_lean_auditor/main.py:96`, `app/confia_lean_auditor/main.py:101` e `app/confia_lean_auditor/main.py:102`.
Padrões: controller/orquestrador.
Anti-padrões e smells: `repo_root()` usa `parents[2]` em `app/confia_lean_auditor/main.py:22`, que resolve para `app`, não para a raiz do repositório que contém `problems/`; em seguida `problem_dir` é montado como `root / "problems"` em `app/confia_lean_auditor/main.py:36` e `app/confia_lean_auditor/main.py:37`. O endpoint aceita `problem_id` como parte de caminho sem normalização em `app/confia_lean_auditor/main.py:37`.
Risco de refatoração: ALTO, porque concentra o fluxo ponta a ponta.
<file-analyzed/>

#### Analisado 23 de 59 — app/confia_lean_auditor/reports/__init__.py
Responsabilidade: marca subpacote `reports`; vazio em `app/confia_lean_auditor/reports/__init__.py:0`.
Fluxo de dados: sem entrada/saída.
Entradas/saídas: habilita import de report builder.
Padrões: marcador de pacote.
Anti-padrões e smells: nenhum conteúdo.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 24 de 59 — app/confia_lean_auditor/reports/report_builder.py
Responsabilidade: transforma avaliação de rubrica, certificado Lean e microclaims em veredito e feedback textual em `app/confia_lean_auditor/reports/report_builder.py:19` e `app/confia_lean_auditor/reports/report_builder.py:31`.
Fluxo de dados: calcula ratio em `app/confia_lean_auditor/reports/report_builder.py:20`; separa itens detectados e ausentes em `app/confia_lean_auditor/reports/report_builder.py:36` e `app/confia_lean_auditor/reports/report_builder.py:37`; adiciona status Lean quando não verificado em `app/confia_lean_auditor/reports/report_builder.py:68`.
Entradas/saídas: exporta `verdict_from_score` e `build_feedback`; saída é string em `app/confia_lean_auditor/reports/report_builder.py:75`.
Padrões: presenter/formatter.
Anti-padrões e smells: thresholds mágicos de 0.9 e 0.5 em `app/confia_lean_auditor/reports/report_builder.py:22` e `app/confia_lean_auditor/reports/report_builder.py:24`; mensagens fixas em português dentro do código em `app/confia_lean_auditor/reports/report_builder.py:49`, `app/confia_lean_auditor/reports/report_builder.py:56`, `app/confia_lean_auditor/reports/report_builder.py:63` e `app/confia_lean_auditor/reports/report_builder.py:70`.
Risco de refatoração: MÉDIO, porque afeta contrato textual de saída.
<file-analyzed/>

#### Analisado 25 de 59 — app/confia_lean_auditor/rubric/__init__.py
Responsabilidade: marca subpacote `rubric`; vazio em `app/confia_lean_auditor/rubric/__init__.py:0`.
Fluxo de dados: sem entrada/saída.
Entradas/saídas: habilita import de rubric evaluator.
Padrões: marcador de pacote.
Anti-padrões e smells: nenhum conteúdo.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 26 de 59 — app/confia_lean_auditor/rubric/rubric_evaluator.py
Responsabilidade: lê rubrica JSON, cruza itens com claims extraídas e soma pontos em `app/confia_lean_auditor/rubric/rubric_evaluator.py:22` a `app/confia_lean_auditor/rubric/rubric_evaluator.py:61`.
Fluxo de dados: lê `rubric.json` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:27` e `app/confia_lean_auditor/rubric/rubric_evaluator.py:32`; procura claim por tipo em `app/confia_lean_auditor/rubric/rubric_evaluator.py:15` a `app/confia_lean_auditor/rubric/rubric_evaluator.py:19`; produz `RubricAssessment` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:57` a `app/confia_lean_auditor/rubric/rubric_evaluator.py:60`.
Entradas/saídas: exporta `evaluate_rubric`.
Padrões: evaluator por configuração.
Anti-padrões e smells: não valida schema antes de acessar `rubric["items"]`, `item["claim_type"]` e `rubric["max_score"]` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:37`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:38` e `app/confia_lean_auditor/rubric/rubric_evaluator.py:59`.
Risco de refatoração: ALTO, porque define score.
<file-analyzed/>

#### Analisado 27 de 59 — artifacts/runs/20260702T181631_332331/audit.json
Responsabilidade: saída versionada de execução de auditoria, com `problem_id`, score e rubrica em `artifacts/runs/20260702T181631_332331/audit.json:2`, `artifacts/runs/20260702T181631_332331/audit.json:3` e `artifacts/runs/20260702T181631_332331/audit.json:6`.
Fluxo de dados: representa resposta persistida pelo produtor `main.py` em `app/confia_lean_auditor/main.py:96`.
Entradas/saídas: consumível como registro histórico; sem consumidor interno identificado.
Padrões: artefato de execução.
Anti-padrões e smells: saída de execução versionada por acidente, categoria reforçada pela existência de escrita programática em `app/confia_lean_auditor/main.py:96`.
Risco de refatoração: BAIXO para código, MÉDIO para reprodutibilidade de dados.
<file-analyzed/>

#### Analisado 28 de 59 — artifacts/runs/20260702T181631_332331/solution.txt
Responsabilidade: snapshot da solução de entrada, com texto de resolução e resposta em `artifacts/runs/20260702T181631_332331/solution.txt:1` e `artifacts/runs/20260702T181631_332331/solution.txt:23`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:101`.
Entradas/saídas: artefato sem consumidor interno.
Padrões: log de execução.
Anti-padrões e smells: dado de entrada versionado como artefato; produtor grava toda solução em `app/confia_lean_auditor/main.py:101`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 29 de 59 — artifacts/runs/20260702T235936_589547/audit.json
Responsabilidade: resposta persistida de auditoria com rubrica, certificado e microclaims em `artifacts/runs/20260702T235936_589547/audit.json:62` e `artifacts/runs/20260702T235936_589547/audit.json:122`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:96`.
Entradas/saídas: registro de execução; sem consumidor interno.
Padrões: artefato JSON.
Anti-padrões e smells: contém `artifact_dir` absoluto em `artifacts/runs/20260702T235936_589547/audit.json:167`, que acopla o artefato ao path local.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 30 de 59 — artifacts/runs/20260702T235936_589547/claims.json
Responsabilidade: claims extraídas persistidas em `artifacts/runs/20260702T235936_589547/claims.json:1` e lista de claims em `artifacts/runs/20260702T235936_589547/claims.json:3`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:102`.
Entradas/saídas: espelha `ClaimExtraction` de `schemas.py` em `app/confia_lean_auditor/core/schemas.py:22`.
Padrões: artefato JSON.
Anti-padrões e smells: saída de execução versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

### Lote 4: arquivos 31-40 de 59

#### Analisado 31 de 59 — artifacts/runs/20260702T235936_589547/solution.txt
Responsabilidade: snapshot textual de solução correta em `artifacts/runs/20260702T235936_589547/solution.txt:1` e `artifacts/runs/20260702T235936_589547/solution.txt:23`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:101`.
Entradas/saídas: dado histórico.
Padrões: artefato de entrada.
Anti-padrões e smells: duplicata de exemplo correto, com mesmo conteúdo estrutural de `problems/ITA2025Q1/examples/correct_solution.txt:1` a `problems/ITA2025Q1/examples/correct_solution.txt:23`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 32 de 59 — artifacts/runs/20260703T005732_426318/Attempt.lean
Responsabilidade: código Lean gerado para execução específica, importando `Mathlib` em `artifacts/runs/20260703T005732_426318/Attempt.lean:2`.
Fluxo de dados: produzido por `build_attempt.py` em `app/confia_lean_auditor/lean/build_attempt.py:115` e `app/confia_lean_auditor/lean/build_attempt.py:116`; consumido por `run_lean_file` em `app/confia_lean_auditor/main.py:66`.
Entradas/saídas: contém teoremas gerados conforme claims.
Padrões: código gerado.
Anti-padrões e smells: saída gerada versionada; o produtor usa timestamp em `app/confia_lean_auditor/main.py:42` e path de artefato em `app/confia_lean_auditor/main.py:43`.
Risco de refatoração: BAIXO para lógica, MÉDIO para contratos de auditoria histórica.
<file-analyzed/>

#### Analisado 33 de 59 — artifacts/runs/20260703T005732_426318/audit.json
Responsabilidade: resposta persistida com `lean_file` absoluto e `artifact_dir` absoluto em `artifacts/runs/20260703T005732_426318/audit.json:121` e `artifacts/runs/20260703T005732_426318/audit.json:187`.
Fluxo de dados: saída de `AuditResponse` em `app/confia_lean_auditor/main.py:83` a `app/confia_lean_auditor/main.py:94`.
Entradas/saídas: registro histórico.
Padrões: artefato JSON.
Anti-padrões e smells: path absoluto local exposto em artefato de produção em `artifacts/runs/20260703T005732_426318/audit.json:121`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 34 de 59 — artifacts/runs/20260703T005732_426318/claims.json
Responsabilidade: persistência de claims extraídas, com estrutura compatível com `ClaimExtraction` em `app/confia_lean_auditor/core/schemas.py:22`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:102`.
Entradas/saídas: contém `claims` consumíveis externamente; sem consumidor interno.
Padrões: artefato JSON.
Anti-padrões e smells: saída de execução versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 35 de 59 — artifacts/runs/20260703T005732_426318/solution.txt
Responsabilidade: snapshot textual de solução, com linhas de solução longa em `artifacts/runs/20260703T005732_426318/solution.txt:1` e `artifacts/runs/20260703T005732_426318/solution.txt:23`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:101`.
Entradas/saídas: dado histórico.
Padrões: artefato de execução.
Anti-padrões e smells: saída versionada de input do usuário.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 36 de 59 — artifacts/runs/20260703T005858_740365/Attempt.lean
Responsabilidade: código Lean gerado, importando `Mathlib` em `artifacts/runs/20260703T005858_740365/Attempt.lean:2`.
Fluxo de dados: produzido por `build_attempt.py` em `app/confia_lean_auditor/lean/build_attempt.py:116`.
Entradas/saídas: tentativa Lean de uma execução.
Padrões: código gerado.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 37 de 59 — artifacts/runs/20260703T005858_740365/audit.json
Responsabilidade: resposta persistida de auditoria, com rubrica em `artifacts/runs/20260703T005858_740365/audit.json:21`, microclaims em `artifacts/runs/20260703T005858_740365/audit.json:85` e artifact_dir em `artifacts/runs/20260703T005858_740365/audit.json:143`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:96`.
Entradas/saídas: histórico de execução.
Padrões: artefato JSON.
Anti-padrões e smells: path absoluto local em `artifacts/runs/20260703T005858_740365/audit.json:143`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 38 de 59 — artifacts/runs/20260703T005858_740365/claims.json
Responsabilidade: claims de uma solução curta, com baixa contagem de linhas e estrutura de `ClaimExtraction`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:102`.
Entradas/saídas: artefato JSON.
Padrões: saída persistida.
Anti-padrões e smells: saída de execução versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 39 de 59 — artifacts/runs/20260703T005858_740365/solution.txt
Responsabilidade: solução de uma linha em `artifacts/runs/20260703T005858_740365/solution.txt:1`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:101`.
Entradas/saídas: dado histórico.
Padrões: artefato de entrada.
Anti-padrões e smells: dado de execução versionado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 40 de 59 — artifacts/runs/20260703T011235_219542/Attempt.lean
Responsabilidade: tentativa Lean gerada, importando `Mathlib` em `artifacts/runs/20260703T011235_219542/Attempt.lean:2`.
Fluxo de dados: produzido por `build_attempt.py` em `app/confia_lean_auditor/lean/build_attempt.py:116`.
Entradas/saídas: arquivo consumido por `run_lean_file` no fluxo HTTP em `app/confia_lean_auditor/main.py:66`.
Padrões: código gerado.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

### Lote 5: arquivos 41-50 de 59

#### Analisado 41 de 59 — artifacts/runs/20260703T011235_219542/audit.json
Responsabilidade: resposta persistida com rubrica em `artifacts/runs/20260703T011235_219542/audit.json:42`, microclaims em `artifacts/runs/20260703T011235_219542/audit.json:107` e artifact_dir em `artifacts/runs/20260703T011235_219542/audit.json:165`.
Fluxo de dados: saída de `main.py` em `app/confia_lean_auditor/main.py:96`.
Entradas/saídas: registro histórico.
Padrões: artefato JSON.
Anti-padrões e smells: path absoluto local em `artifacts/runs/20260703T011235_219542/audit.json:165`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 42 de 59 — artifacts/runs/20260703T011235_219542/claims.json
Responsabilidade: claims persistidas de execução, alinhadas ao schema `ClaimExtraction` em `app/confia_lean_auditor/core/schemas.py:22` a `app/confia_lean_auditor/core/schemas.py:24`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:102`.
Entradas/saídas: artefato JSON.
Padrões: saída persistida.
Anti-padrões e smells: saída de execução versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 43 de 59 — artifacts/runs/20260703T011235_219542/solution.txt
Responsabilidade: solução parcial de dez linhas, com equação final em `artifacts/runs/20260703T011235_219542/solution.txt:10`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:101`.
Entradas/saídas: dado histórico.
Padrões: artefato de entrada.
Anti-padrões e smells: provável duplicata de fixture parcial, pois `problems/ITA2025Q1/examples/partial_no_positive_root.txt:1` a `problems/ITA2025Q1/examples/partial_no_positive_root.txt:10` modela o mesmo caso.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 44 de 59 — artifacts/runs/20260703T011304_967627/Attempt.lean
Responsabilidade: tentativa Lean gerada, importando `Mathlib` em `artifacts/runs/20260703T011304_967627/Attempt.lean:2`.
Fluxo de dados: produzido por `build_attempt.py` em `app/confia_lean_auditor/lean/build_attempt.py:116`.
Entradas/saídas: arquivo Lean de execução.
Padrões: código gerado.
Anti-padrões e smells: saída gerada versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 45 de 59 — artifacts/runs/20260703T011304_967627/audit.json
Responsabilidade: resposta persistida com rubrica em `artifacts/runs/20260703T011304_967627/audit.json:10`, microclaims em `artifacts/runs/20260703T011304_967627/audit.json:72` e artifact_dir em `artifacts/runs/20260703T011304_967627/audit.json:130`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:96`.
Entradas/saídas: histórico de execução.
Padrões: artefato JSON.
Anti-padrões e smells: path absoluto local em `artifacts/runs/20260703T011304_967627/audit.json:130`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 46 de 59 — artifacts/runs/20260703T011304_967627/claims.json
Responsabilidade: claims persistidas; o arquivo tem estrutura mínima de três linhas, com lista de claims vazia ou curta.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:102`.
Entradas/saídas: artefato JSON.
Padrões: saída persistida.
Anti-padrões e smells: saída de execução versionada.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 47 de 59 — artifacts/runs/20260703T011304_967627/solution.txt
Responsabilidade: solução errada curta em `artifacts/runs/20260703T011304_967627/solution.txt:1` e `artifacts/runs/20260703T011304_967627/solution.txt:2`.
Fluxo de dados: produzido por `main.py` em `app/confia_lean_auditor/main.py:101`.
Entradas/saídas: dado histórico.
Padrões: artefato de entrada.
Anti-padrões e smells: provável duplicata de fixture errada, pois `problems/ITA2025Q1/examples/wrong_solution.txt:1` e `problems/ITA2025Q1/examples/wrong_solution.txt:2` modelam o mesmo caso.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 48 de 59 — lake-manifest.json
Responsabilidade: lockfile Lake com pacote raiz e dependências Lean em `lake-manifest.json:1`, `lake-manifest.json:3` e `lake-manifest.json:94`.
Fluxo de dados: Lake consome o lock para baixar/resolver dependências em `.lake/packages`, configurado em `lake-manifest.json:2`.
Entradas/saídas: entrada para build Lean.
Padrões: lockfile.
Anti-padrões e smells: inclui dependências herdadas numerosas, como `plausible`, `LeanSearchClient`, `importGraph`, `proofwidgets`, `aesop`, `Qq`, `batteries` e `Cli` em `lake-manifest.json:19`, `lake-manifest.json:29`, `lake-manifest.json:39`, `lake-manifest.json:49`, `lake-manifest.json:59`, `lake-manifest.json:69`, `lake-manifest.json:79` e `lake-manifest.json:89`; isso amplia superfície de build além do import direto `Mathlib` em `lakefile.toml:13`.
Risco de refatoração: MÉDIO.
<file-analyzed/>

#### Analisado 49 de 59 — lakefile.toml
Responsabilidade: define projeto Lake, alvo padrão, opções Lean, dependência `mathlib` e lib `ConfiaLeanAuditor` em `lakefile.toml:1`, `lakefile.toml:4`, `lakefile.toml:6`, `lakefile.toml:12` e `lakefile.toml:17`.
Fluxo de dados: consumido por Lake em build e por `lake env lean` chamado em `app/confia_lean_auditor/lean/run_lean.py:67`.
Entradas/saídas: configura build Lean.
Padrões: manifesto de build.
Anti-padrões e smells: alvo default aponta biblioteca scaffold em `lakefile.toml:4` e `ConfiaLeanAuditor/Basic.lean:1`.
Risco de refatoração: MÉDIO.
<file-analyzed/>

#### Analisado 50 de 59 — lean-toolchain
Responsabilidade: fixa toolchain Lean em `lean-toolchain:1`.
Fluxo de dados: consumido por Lake/Lean e por workflows de release em `.github/workflows/create-release.yml:8` e `.github/workflows/create-release.yml:9`.
Entradas/saídas: entrada de toolchain.
Padrões: pin de runtime.
Anti-padrões e smells: sem smell local; é contrato central.
Risco de refatoração: MÉDIO, porque altera compilação e CI.
<file-analyzed/>

### Lote 6: arquivos 51-59 de 59

#### Analisado 51 de 59 — problems/ITA2025Q1/certificate/Statement.lean
Responsabilidade: certificado Lean fixo para o problema ITA2025Q1, com área e resposta em `problems/ITA2025Q1/certificate/Statement.lean:7`, `problems/ITA2025Q1/certificate/Statement.lean:10`, `problems/ITA2025Q1/certificate/Statement.lean:30` e `problems/ITA2025Q1/certificate/Statement.lean:47`.
Fluxo de dados: consumido pela CLI `run_problem` em `app/confia_lean_auditor/lean/run_lean.py:99` e `app/confia_lean_auditor/lean/run_lean.py:113`.
Entradas/saídas: exporta teoremas dentro da namespace `ConfIA.LeanAuditor.ITA2025Q1` em `problems/ITA2025Q1/certificate/Statement.lean:3`.
Padrões: certificado formal estático.
Anti-padrões e smells: há duplicação quase literal entre teoremas fixos e templates gerados em `problems/ITA2025Q1/certificate/Statement.lean:7` a `problems/ITA2025Q1/certificate/Statement.lean:50` e `app/confia_lean_auditor/lean/build_attempt.py:16` a `app/confia_lean_auditor/lean/build_attempt.py:72`.
Risco de refatoração: MÉDIO, porque é entrada da CLI e referência matemática.
<file-analyzed/>

#### Analisado 52 de 59 — problems/ITA2025Q1/examples/answer_only.txt
Responsabilidade: fixture de solução só com resposta em `problems/ITA2025Q1/examples/answer_only.txt:1`.
Fluxo de dados: não há consumidor interno referenciado; serve como exemplo/manual.
Entradas/saídas: entrada textual potencial para `/audit`.
Padrões: fixture.
Anti-padrões e smells: fixture sem consumidor de teste identificado; CI não roda testes Python em `.github/workflows/lean_action_ci.yml:19` a `.github/workflows/lean_action_ci.yml:21`.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 53 de 59 — problems/ITA2025Q1/examples/correct_solution.txt
Responsabilidade: fixture de solução completa, com coordenadas em `problems/ITA2025Q1/examples/correct_solution.txt:1` a `problems/ITA2025Q1/examples/correct_solution.txt:6`, área em `problems/ITA2025Q1/examples/correct_solution.txt:8` a `problems/ITA2025Q1/examples/correct_solution.txt:14` e resposta em `problems/ITA2025Q1/examples/correct_solution.txt:21` a `problems/ITA2025Q1/examples/correct_solution.txt:23`.
Fluxo de dados: potencial entrada para `/audit`; sem consumidor automatizado identificado.
Entradas/saídas: texto de exemplo.
Padrões: fixture.
Anti-padrões e smells: fixture sem teste automatizado associado na CI.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 54 de 59 — problems/ITA2025Q1/examples/partial_no_positive_root.txt
Responsabilidade: fixture parcial sem descarte da raiz positiva, com equação em `problems/ITA2025Q1/examples/partial_no_positive_root.txt:7` a `problems/ITA2025Q1/examples/partial_no_positive_root.txt:10`.
Fluxo de dados: potencial entrada para `/audit`.
Entradas/saídas: texto de exemplo.
Padrões: fixture negativa/parcial.
Anti-padrões e smells: fixture sem consumidor automatizado identificado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 55 de 59 — problems/ITA2025Q1/examples/wrong_solution.txt
Responsabilidade: fixture de solução errada em `problems/ITA2025Q1/examples/wrong_solution.txt:1` e `problems/ITA2025Q1/examples/wrong_solution.txt:2`.
Fluxo de dados: potencial entrada para `/audit`.
Entradas/saídas: texto de exemplo.
Padrões: fixture negativa.
Anti-padrões e smells: fixture sem consumidor automatizado identificado.
Risco de refatoração: BAIXO.
<file-analyzed/>

#### Analisado 56 de 59 — problems/ITA2025Q1/microclaims.json
Responsabilidade: define quatro microclaims, seus teoremas Lean, claim types e itens de rubrica suportados em `problems/ITA2025Q1/microclaims.json:3`, `problems/ITA2025Q1/microclaims.json:7`, `problems/ITA2025Q1/microclaims.json:14`, `problems/ITA2025Q1/microclaims.json:21` e `problems/ITA2025Q1/microclaims.json:28`.
Fluxo de dados: consumido por `evaluate_microclaims` em `app/confia_lean_auditor/lean/microclaim_evaluator.py:21`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:32`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:33`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:34` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:61`.
Entradas/saídas: contrato JSON de microclaim.
Padrões: tabela declarativa.
Anti-padrões e smells: strings de teorema duplicam strings geradas por `build_attempt.py`, por exemplo `problems/ITA2025Q1/microclaims.json:7` com `app/confia_lean_auditor/lean/build_attempt.py:98` e `problems/ITA2025Q1/microclaims.json:28` com `app/confia_lean_auditor/lean/build_attempt.py:111`.
Risco de refatoração: ALTO, porque conecta rubrica, extração e Lean.
<file-analyzed/>

#### Analisado 57 de 59 — problems/ITA2025Q1/problem.json
Responsabilidade: descreve problema, enunciado, tipo de resposta, resposta correta e pontuação máxima em `problems/ITA2025Q1/problem.json:2` a `problems/ITA2025Q1/problem.json:7`.
Fluxo de dados: o endpoint só verifica a existência do diretório do problema em `app/confia_lean_auditor/main.py:37` e `app/confia_lean_auditor/main.py:39`; este arquivo não é lido por nenhum módulo auditado.
Entradas/saídas: contrato de domínio potencial.
Padrões: metadata de problema.
Anti-padrões e smells: arquivo sem consumidor interno identificado; `correct_answer` em `problems/ITA2025Q1/problem.json:6` não é usado na avaliação, que depende de claims e rubrica em `app/confia_lean_auditor/main.py:46` e `app/confia_lean_auditor/main.py:49`.
Risco de refatoração: MÉDIO, porque é metadata de domínio não integrada ao fluxo.
<file-analyzed/>

#### Analisado 58 de 59 — problems/ITA2025Q1/rubric.json
Responsabilidade: define rubrica de 10 pontos e cinco itens por `claim_type` em `problems/ITA2025Q1/rubric.json:2`, `problems/ITA2025Q1/rubric.json:3`, `problems/ITA2025Q1/rubric.json:4`, `problems/ITA2025Q1/rubric.json:9`, `problems/ITA2025Q1/rubric.json:15`, `problems/ITA2025Q1/rubric.json:21`, `problems/ITA2025Q1/rubric.json:27` e `problems/ITA2025Q1/rubric.json:33`.
Fluxo de dados: consumido por `evaluate_rubric` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:27`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:32`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:37`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:38` e `app/confia_lean_auditor/rubric/rubric_evaluator.py:59`.
Entradas/saídas: contrato JSON de pontuação.
Padrões: rubrica declarativa.
Anti-padrões e smells: `claim_type` é contrato por string com o extrator em `problems/ITA2025Q1/rubric.json:9` e `app/confia_lean_auditor/claims/extract_claims.py:53`; não há validação explícita do schema antes do consumo em `app/confia_lean_auditor/rubric/rubric_evaluator.py:37`.
Risco de refatoração: ALTO, porque define score e contrato com claims.
<file-analyzed/>

#### Analisado 59 de 59 — pyproject.toml
Responsabilidade: configura build Python, metadata e descoberta de pacote em `pyproject.toml:1`, `pyproject.toml:5`, `pyproject.toml:17` e `pyproject.toml:20`.
Fluxo de dados: setuptools usa `app` como package-dir em `pyproject.toml:17` e `pyproject.toml:18`; dependências são declaradas em `pyproject.toml:10` a `pyproject.toml:15`.
Entradas/saídas: manifesto de build Python.
Padrões: configuração PEP 621.
Anti-padrões e smells: `pytest` declarado em dependências runtime em `pyproject.toml:14`; não há entrypoint de console ou ASGI declarado, apesar de `main.py` expor `app` em `app/confia_lean_auditor/main.py:18`.
Risco de refatoração: MÉDIO.
<file-analyzed/>

## 6. Preocupações transversais

Roteamento e pipelines paralelos: existem dois caminhos Lean. A API gera `Attempt.lean` em `app/confia_lean_auditor/lean/build_attempt.py:115` e executa esse arquivo em `app/confia_lean_auditor/main.py:66`; a CLI usa `Statement.lean` fixo em `app/confia_lean_auditor/lean/run_lean.py:99` e `app/confia_lean_auditor/lean/run_lean.py:113`. O certificado fixo e o template gerado duplicam definições de área e resposta em `problems/ITA2025Q1/certificate/Statement.lean:7` a `problems/ITA2025Q1/certificate/Statement.lean:50` e `app/confia_lean_auditor/lean/build_attempt.py:16` a `app/confia_lean_auditor/lean/build_attempt.py:72`.

Configuração e env vars: não há leitura de env var nos módulos auditados; o path raiz da API é inferido por `Path(__file__).resolve().parents[2]` em `app/confia_lean_auditor/main.py:22`. O diretório `problems` é montado abaixo desse root em `app/confia_lean_auditor/main.py:37`, enquanto `pyproject.toml` declara `package-dir = {"" = "app"}` em `pyproject.toml:18`, criando divergência entre raiz do pacote e raiz do repositório.

Logging e diagnóstico: a CLI imprime JSON com `print` em `app/confia_lean_auditor/lean/run_lean.py:123`; a API retorna e persiste stdout/stderr Lean no contrato `LeanCertificate` em `app/confia_lean_auditor/core/schemas.py:49` e `app/confia_lean_auditor/core/schemas.py:50`, preenchidos por `run_lean.py` em `app/confia_lean_auditor/lean/run_lean.py:94` e `app/confia_lean_auditor/lean/run_lean.py:95`.

Tratamento de erro: `main.py` transforma problema inexistente em 404 em `app/confia_lean_auditor/main.py:39` e `app/confia_lean_auditor/main.py:40`, `FileNotFoundError` de rubrica em 404 em `app/confia_lean_auditor/main.py:48` a `app/confia_lean_auditor/main.py:51`, e builder ausente em 501 em `app/confia_lean_auditor/main.py:53` a `app/confia_lean_auditor/main.py:61`. `microclaim_evaluator.py` retorna `[]` quando o arquivo não existe em `app/confia_lean_auditor/lean/microclaim_evaluator.py:23` e `app/confia_lean_auditor/lean/microclaim_evaluator.py:24`, distinguindo menos esse caso do que a rubrica ausente.

Segurança: `problem_id` participa da montagem de path em `app/confia_lean_auditor/main.py:37`, `app/confia_lean_auditor/rubric/rubric_evaluator.py:27`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:21` e `app/confia_lean_auditor/lean/run_lean.py:100`. O subprocess Lean tem timeout de 30 segundos por padrão em `app/confia_lean_auditor/lean/run_lean.py:63` e passa `timeout=timeout_seconds` em `app/confia_lean_auditor/lean/run_lean.py:76`. Não há autenticação, rate-limit ou CORS configurado no arquivo da API; a aplicação é criada sem middlewares em `app/confia_lean_auditor/main.py:18`.

Testes: `pytest` é declarado em `pyproject.toml:14` e `app/confia_lean_auditor.egg-info/requires.txt:4`, mas a CI Lean não executa testes Python em `.github/workflows/lean_action_ci.yml:19` a `.github/workflows/lean_action_ci.yml:21`. Os exemplos em `problems/ITA2025Q1/examples/correct_solution.txt:1`, `problems/ITA2025Q1/examples/partial_no_positive_root.txt:1`, `problems/ITA2025Q1/examples/wrong_solution.txt:1` e `problems/ITA2025Q1/examples/answer_only.txt:1` não aparecem como entradas de teste automatizado nos arquivos auditados.

Idioma e identidade: o produto mistura nome `ConfIA` em `pyproject.toml:8`, `app/confia_lean_auditor/main.py:18` e `app/confia_lean_auditor/main.py:29` com README genérico `confia_lean_auditor` e instruções em inglês em `README.md:1`, `README.md:3` e `README.md:5`.

Código morto e artefatos: `ConfiaLeanAuditor/Basic.lean` é scaffold em `ConfiaLeanAuditor/Basic.lean:1`; `README.md` conserva boilerplate em `README.md:13`; `app/confia_lean_auditor.egg-info/*` são artefatos gerados em `app/confia_lean_auditor.egg-info/PKG-INFO:1`; `artifacts/runs/*` são saídas de execução produzidas por `main.py` em `app/confia_lean_auditor/main.py:96`, `app/confia_lean_auditor/main.py:101` e `app/confia_lean_auditor/main.py:102`.

## 7. Tabela de risco

| Arquivo | Risco | Razão principal |
|---|---:|---|
| `.github/workflows/create-release.yml` | MÉDIO | Publica release/tag com permissão de escrita em `.github/workflows/create-release.yml:16`. |
| `.github/workflows/lean_action_ci.yml` | MÉDIO | Único CI ativo cobre Lean e docgen em `.github/workflows/lean_action_ci.yml:20` e `.github/workflows/lean_action_ci.yml:21`. |
| `.github/workflows/update.yml` | MÉDIO | Atualiza dependências Lean por ação externa em `.github/workflows/update.yml:17` e `.github/workflows/update.yml:35`. |
| `.gitignore` | BAIXO | Só ignora `/.lake` em `.gitignore:1`. |
| `ConfiaLeanAuditor.lean` | BAIXO | Apenas importa `Basic` em `ConfiaLeanAuditor.lean:1`. |
| `ConfiaLeanAuditor/Basic.lean` | BAIXO | Scaffold `hello := "world"` em `ConfiaLeanAuditor/Basic.lean:1`. |
| `README.md` | BAIXO | Boilerplate declarado removível em `README.md:13`. |
| `app/confia_lean_auditor.egg-info/PKG-INFO` | BAIXO | Metadata gerada em `app/confia_lean_auditor.egg-info/PKG-INFO:1`. |
| `app/confia_lean_auditor.egg-info/SOURCES.txt` | MÉDIO | Manifesto gerado não lista módulos usados por `main.py`, enquanto lista fontes em `app/confia_lean_auditor.egg-info/SOURCES.txt:1` a `app/confia_lean_auditor.egg-info/SOURCES.txt:12`. |
| `app/confia_lean_auditor.egg-info/dependency_links.txt` | BAIXO | Arquivo gerado vazio em `app/confia_lean_auditor.egg-info/dependency_links.txt:1`. |
| `app/confia_lean_auditor.egg-info/requires.txt` | BAIXO | Metadata derivada de dependências em `app/confia_lean_auditor.egg-info/requires.txt:1` a `app/confia_lean_auditor.egg-info/requires.txt:4`. |
| `app/confia_lean_auditor.egg-info/top_level.txt` | BAIXO | Metadata top-level em `app/confia_lean_auditor.egg-info/top_level.txt:1`. |
| `app/confia_lean_auditor/__init__.py` | BAIXO | Marcador vazio em `app/confia_lean_auditor/__init__.py:0`. |
| `app/confia_lean_auditor/claims/__init__.py` | BAIXO | Marcador vazio em `app/confia_lean_auditor/claims/__init__.py:0`. |
| `app/confia_lean_auditor/claims/extract_claims.py` | ALTO | Produz `claim_type` consumido por rubrica e Lean em `app/confia_lean_auditor/claims/extract_claims.py:53`. |
| `app/confia_lean_auditor/core/__init__.py` | BAIXO | Marcador vazio em `app/confia_lean_auditor/core/__init__.py:0`. |
| `app/confia_lean_auditor/core/schemas.py` | ALTO | Define contrato de resposta e certificado em `app/confia_lean_auditor/core/schemas.py:43` e `app/confia_lean_auditor/core/schemas.py:65`. |
| `app/confia_lean_auditor/lean/__init__.py` | BAIXO | Marcador vazio em `app/confia_lean_auditor/lean/__init__.py:0`. |
| `app/confia_lean_auditor/lean/build_attempt.py` | ALTO | Gera `Attempt.lean` e lista de teoremas em `app/confia_lean_auditor/lean/build_attempt.py:115` a `app/confia_lean_auditor/lean/build_attempt.py:120`. |
| `app/confia_lean_auditor/lean/microclaim_evaluator.py` | ALTO | Cruza JSON, claims e status Lean em `app/confia_lean_auditor/lean/microclaim_evaluator.py:32` a `app/confia_lean_auditor/lean/microclaim_evaluator.py:51`. |
| `app/confia_lean_auditor/lean/run_lean.py` | ALTO | Executa subprocess externo em `app/confia_lean_auditor/lean/run_lean.py:70` a `app/confia_lean_auditor/lean/run_lean.py:77`. |
| `app/confia_lean_auditor/main.py` | ALTO | Orquestra `/audit` e grava artefatos em `app/confia_lean_auditor/main.py:34` e `app/confia_lean_auditor/main.py:96`. |
| `app/confia_lean_auditor/reports/__init__.py` | BAIXO | Marcador vazio em `app/confia_lean_auditor/reports/__init__.py:0`. |
| `app/confia_lean_auditor/reports/report_builder.py` | MÉDIO | Define vereditos e feedback em `app/confia_lean_auditor/reports/report_builder.py:19` e `app/confia_lean_auditor/reports/report_builder.py:31`. |
| `app/confia_lean_auditor/rubric/__init__.py` | BAIXO | Marcador vazio em `app/confia_lean_auditor/rubric/__init__.py:0`. |
| `app/confia_lean_auditor/rubric/rubric_evaluator.py` | ALTO | Calcula score por rubrica em `app/confia_lean_auditor/rubric/rubric_evaluator.py:37` a `app/confia_lean_auditor/rubric/rubric_evaluator.py:60`. |
| `artifacts/runs/20260702T181631_332331/audit.json` | BAIXO | Artefato produzido por `main.py` em `app/confia_lean_auditor/main.py:96`. |
| `artifacts/runs/20260702T181631_332331/solution.txt` | BAIXO | Artefato produzido por `main.py` em `app/confia_lean_auditor/main.py:101`. |
| `artifacts/runs/20260702T235936_589547/audit.json` | BAIXO | Artefato com path absoluto em `artifacts/runs/20260702T235936_589547/audit.json:167`. |
| `artifacts/runs/20260702T235936_589547/claims.json` | BAIXO | Artefato produzido por `main.py` em `app/confia_lean_auditor/main.py:102`. |
| `artifacts/runs/20260702T235936_589547/solution.txt` | BAIXO | Artefato de entrada persistido em `artifacts/runs/20260702T235936_589547/solution.txt:1`. |
| `artifacts/runs/20260703T005732_426318/Attempt.lean` | BAIXO | Código gerado por `build_attempt.py` em `app/confia_lean_auditor/lean/build_attempt.py:116`. |
| `artifacts/runs/20260703T005732_426318/audit.json` | BAIXO | Artefato com path absoluto em `artifacts/runs/20260703T005732_426318/audit.json:121`. |
| `artifacts/runs/20260703T005732_426318/claims.json` | BAIXO | Saída de claims em `app/confia_lean_auditor/main.py:102`. |
| `artifacts/runs/20260703T005732_426318/solution.txt` | BAIXO | Entrada persistida em `app/confia_lean_auditor/main.py:101`. |
| `artifacts/runs/20260703T005858_740365/Attempt.lean` | BAIXO | Código gerado em `app/confia_lean_auditor/lean/build_attempt.py:116`. |
| `artifacts/runs/20260703T005858_740365/audit.json` | BAIXO | Artefato com `artifact_dir` em `artifacts/runs/20260703T005858_740365/audit.json:143`. |
| `artifacts/runs/20260703T005858_740365/claims.json` | BAIXO | Saída de claims em `app/confia_lean_auditor/main.py:102`. |
| `artifacts/runs/20260703T005858_740365/solution.txt` | BAIXO | Entrada de uma linha em `artifacts/runs/20260703T005858_740365/solution.txt:1`. |
| `artifacts/runs/20260703T011235_219542/Attempt.lean` | BAIXO | Código gerado em `app/confia_lean_auditor/lean/build_attempt.py:116`. |
| `artifacts/runs/20260703T011235_219542/audit.json` | BAIXO | Artefato com `artifact_dir` em `artifacts/runs/20260703T011235_219542/audit.json:165`. |
| `artifacts/runs/20260703T011235_219542/claims.json` | BAIXO | Saída de claims em `app/confia_lean_auditor/main.py:102`. |
| `artifacts/runs/20260703T011235_219542/solution.txt` | BAIXO | Entrada persistida em `app/confia_lean_auditor/main.py:101`. |
| `artifacts/runs/20260703T011304_967627/Attempt.lean` | BAIXO | Código gerado em `app/confia_lean_auditor/lean/build_attempt.py:116`. |
| `artifacts/runs/20260703T011304_967627/audit.json` | BAIXO | Artefato com `artifact_dir` em `artifacts/runs/20260703T011304_967627/audit.json:130`. |
| `artifacts/runs/20260703T011304_967627/claims.json` | BAIXO | Saída de claims em `app/confia_lean_auditor/main.py:102`. |
| `artifacts/runs/20260703T011304_967627/solution.txt` | BAIXO | Entrada errada persistida em `artifacts/runs/20260703T011304_967627/solution.txt:1`. |
| `lake-manifest.json` | MÉDIO | Lockfile Lean controla dependências em `lake-manifest.json:3`. |
| `lakefile.toml` | MÉDIO | Define lib e mathlib em `lakefile.toml:13` e `lakefile.toml:17`. |
| `lean-toolchain` | MÉDIO | Fixa toolchain em `lean-toolchain:1`. |
| `problems/ITA2025Q1/certificate/Statement.lean` | MÉDIO | Certificado estático usado pela CLI em `app/confia_lean_auditor/lean/run_lean.py:100`. |
| `problems/ITA2025Q1/examples/answer_only.txt` | BAIXO | Fixture sem consumidor automatizado identificado em `problems/ITA2025Q1/examples/answer_only.txt:1`. |
| `problems/ITA2025Q1/examples/correct_solution.txt` | BAIXO | Fixture completa em `problems/ITA2025Q1/examples/correct_solution.txt:1`. |
| `problems/ITA2025Q1/examples/partial_no_positive_root.txt` | BAIXO | Fixture parcial em `problems/ITA2025Q1/examples/partial_no_positive_root.txt:1`. |
| `problems/ITA2025Q1/examples/wrong_solution.txt` | BAIXO | Fixture negativa em `problems/ITA2025Q1/examples/wrong_solution.txt:1`. |
| `problems/ITA2025Q1/microclaims.json` | ALTO | Contrato de teoremas e rubrica em `problems/ITA2025Q1/microclaims.json:7` e `problems/ITA2025Q1/microclaims.json:9`. |
| `problems/ITA2025Q1/problem.json` | MÉDIO | Metadata não lida pelo fluxo, apesar de definir resposta correta em `problems/ITA2025Q1/problem.json:6`. |
| `problems/ITA2025Q1/rubric.json` | ALTO | Contrato de score por claim_type em `problems/ITA2025Q1/rubric.json:9`. |
| `pyproject.toml` | MÉDIO | Define packaging Python e dependências em `pyproject.toml:10` a `pyproject.toml:21`. |

## 8. Ordem recomendada de investigação

1. Arquivos de scaffold e documentação: `README.md`, `ConfiaLeanAuditor/Basic.lean`, `ConfiaLeanAuditor.lean` e `app/confia_lean_auditor.egg-info/*`, porque o acoplamento é baixo e os sinais de boilerplate/geração estão em `README.md:13`, `ConfiaLeanAuditor/Basic.lean:1` e `app/confia_lean_auditor.egg-info/PKG-INFO:1`.
2. Artefatos de execução em `artifacts/runs/*`, porque são produzidos por `main.py` em `app/confia_lean_auditor/main.py:96`, `app/confia_lean_auditor/main.py:101` e `app/confia_lean_auditor/main.py:102`, e não têm consumidor interno identificado.
3. Fixtures em `problems/ITA2025Q1/examples/*`, porque documentam casos de entrada em `problems/ITA2025Q1/examples/correct_solution.txt:1`, `problems/ITA2025Q1/examples/partial_no_positive_root.txt:1`, `problems/ITA2025Q1/examples/wrong_solution.txt:1` e `problems/ITA2025Q1/examples/answer_only.txt:1`, mas não aparecem em testes automatizados.
4. Configuração de build e CI: `.gitignore`, `pyproject.toml`, `lakefile.toml`, `lake-manifest.json`, `lean-toolchain` e workflows, porque definem ambiente e execução em `.gitignore:1`, `pyproject.toml:18`, `lakefile.toml:15`, `lake-manifest.json:2`, `lean-toolchain:1` e `.github/workflows/lean_action_ci.yml:20`.
5. Contratos declarativos do problema: `problem.json`, `rubric.json` e `microclaims.json`, porque a avaliação depende de strings compartilhadas em `problems/ITA2025Q1/rubric.json:9`, `problems/ITA2025Q1/microclaims.json:7` e `app/confia_lean_auditor/claims/extract_claims.py:53`.
6. Fluxos Lean: `Statement.lean`, `build_attempt.py` e `run_lean.py`, porque há dois caminhos formais paralelos em `app/confia_lean_auditor/main.py:66` e `app/confia_lean_auditor/lean/run_lean.py:100`.
7. Núcleo de avaliação: `schemas.py`, `extract_claims.py`, `rubric_evaluator.py`, `microclaim_evaluator.py`, `report_builder.py` e `main.py`, porque decisões deixam de ser locais a partir daqui: `AuditResponse` é contrato externo em `app/confia_lean_auditor/core/schemas.py:65`, `/audit` é entrada pública em `app/confia_lean_auditor/main.py:34`, e score/feedback dependem de múltiplos contratos em `app/confia_lean_auditor/rubric/rubric_evaluator.py:57`, `app/confia_lean_auditor/lean/microclaim_evaluator.py:53` e `app/confia_lean_auditor/reports/report_builder.py:75`.

## 9. Diário de revisão

- Hipótese inicial: `app/confia_lean_auditor/lean/build_attempt.py` parecia candidato a órfão por estar não rastreado no status local. Revisão: `main.py` o importa em `app/confia_lean_auditor/main.py:11` e o chama em `app/confia_lean_auditor/main.py:54`, então ele é ativo no fluxo HTTP.
- Hipótese inicial: `problems/ITA2025Q1/certificate/Statement.lean` parecia o certificado central do sistema porque contém os teoremas do problema em `problems/ITA2025Q1/certificate/Statement.lean:30` e `problems/ITA2025Q1/certificate/Statement.lean:47`. Revisão: a API gera `Attempt.lean` em `app/confia_lean_auditor/lean/build_attempt.py:115` e o executa em `app/confia_lean_auditor/main.py:66`; `Statement.lean` fica no caminho CLI em `app/confia_lean_auditor/lean/run_lean.py:99`.
- Hipótese inicial: os arquivos `artifacts/runs/*/Attempt.lean` poderiam ser fontes manuais de prova. Revisão: `build_attempt.py` grava `Attempt.lean` programaticamente em `app/confia_lean_auditor/lean/build_attempt.py:115` e `app/confia_lean_auditor/lean/build_attempt.py:116`, e `main.py` usa timestamp para criar diretórios de execução em `app/confia_lean_auditor/main.py:42` e `app/confia_lean_auditor/main.py:43`; eles são saídas de execução.
- Hipótese inicial: `problem.json` seria consumido para validar resposta correta. Revisão: o fluxo auditado só verifica existência do diretório em `app/confia_lean_auditor/main.py:37` e `app/confia_lean_auditor/main.py:39`; a pontuação vem de `rubric.json` em `app/confia_lean_auditor/rubric/rubric_evaluator.py:27` e claims em `app/confia_lean_auditor/rubric/rubric_evaluator.py:39`.
- Hipótese inicial: `microclaims.json` e `rubric.json` batiam apenas por semântica humana. Revisão: há contrato explícito por strings: `supports_rubric_items` em `problems/ITA2025Q1/microclaims.json:9`, `problems/ITA2025Q1/microclaims.json:16`, `problems/ITA2025Q1/microclaims.json:23` e `problems/ITA2025Q1/microclaims.json:30`, e ids de rubrica em `problems/ITA2025Q1/rubric.json:6`, `problems/ITA2025Q1/rubric.json:12`, `problems/ITA2025Q1/rubric.json:18`, `problems/ITA2025Q1/rubric.json:24` e `problems/ITA2025Q1/rubric.json:30`.
