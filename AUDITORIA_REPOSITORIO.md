# Auditoria descritiva do repositório

## 1. Visão geral do projeto

O projeto se identifica como `confia-lean-auditor`, versão `0.1.0`, com descrição de corretor matemático com rubrica e certificados Lean em `pyproject.toml:6`, `pyproject.toml:7` e `pyproject.toml:8`. O pacote Python exige `>=3.9` e declara `fastapi`, `uvicorn`, `pydantic>=2`, `pytest`, `httpx` e `openai>=1.0.0` em `pyproject.toml:9` a `pyproject.toml:17`. O runtime Lean fixado é `leanprover/lean4:v4.28.0` em `lean-toolchain:1`, e Lake aponta `defaultTargets = ["ConfiaLeanAuditor"]`, mathlib `v4.28.0` e biblioteca `ConfiaLeanAuditor` em `lakefile.toml:4`, `lakefile.toml:12` a `lakefile.toml:18`.

Terreno detectado: monolito em camadas com API FastAPI, extratores heurísticos por problema, contratos JSON em `problems/`, statements Lean em `ConfiaLeanAuditor/Problems/`, geração de artefatos em `artifacts/`, verificação por `lake env lean` e CI em GitHub Actions. A versão pública da API é `0.4.0` no app FastAPI e no `/health`, embora o pacote Python e Lake permaneçam em `0.1.0`, como mostram `app/confia_lean_auditor/main.py:26`, `app/confia_lean_auditor/main.py:33` a `app/confia_lean_auditor/main.py:39`, `pyproject.toml:7` e `lakefile.toml:2`.

Fase 0, inventário cru: `git ls-files` retornou 203 arquivos versionados. `rg --files` retornou 202 arquivos visíveis fora dos diretórios ignorados; a diferença inclui arquivos não versionados em `benchmarks/f2_suite_level1_v2/` e `benchmarks/q_suite_level1_v2/`, confirmados por `git status --short` como caminhos `??`. Diretórios runtime e locais são ignorados por `.gitignore`: `.venv/` em `.gitignore:2`, `.pytest_cache/` em `.gitignore:5`, `artifacts/runs/` em `.gitignore:10`, `.env` em `.gitignore:13` a `.gitignore:14`, `.lake/` em `.gitignore:24`, `Scratch/` em `.gitignore:27`, `artifacts/` em `.gitignore:28` e `benchmarks/**/reports/` em `.gitignore:29`.

Inventário versionado completo:

- `.github/workflows/create-release.yml`
- `.github/workflows/lean_action_ci.yml`
- `.github/workflows/python_tests.yml`
- `.github/workflows/update.yml`
- `.gitignore`
- `AUDITORIA_REPOSITORIO.md`
- `ConfiaLeanAuditor.lean`
- `ConfiaLeanAuditor/Basic.lean`
- `ConfiaLeanAuditor/Problems/ITA2025F2Q1/Statement.lean`
- `ConfiaLeanAuditor/Problems/ITA2025F2Q3/Statement.lean`
- `ConfiaLeanAuditor/Problems/ITA2025F2Q5/Statement.lean`
- `ConfiaLeanAuditor/Problems/ITA2025F2Q6/Statement.lean`
- `ConfiaLeanAuditor/Problems/ITA2025F2Q8/Statement.lean`
- `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean`
- `ConfiaLeanAuditor/Problems/ITA2025Q3/Statement.lean`
- `ConfiaLeanAuditor/Problems/ITA2025Q4/Statement.lean`
- `ConfiaLeanAuditor/Problems/ITA2025Q5/Statement.lean`
- `ConfiaLeanAuditor/Problems/ITA2025Q8/Statement.lean`
- `MILESTONE_ITA2025F2.md`
- `README.md`
- `app/confia_lean_auditor/__init__.py`
- `app/confia_lean_auditor/claims/__init__.py`
- `app/confia_lean_auditor/claims/extract_claims.py`
- `app/confia_lean_auditor/claims/extractors/__init__.py`
- `app/confia_lean_auditor/claims/extractors/ita2025f2q1.py`
- `app/confia_lean_auditor/claims/extractors/ita2025f2q3.py`
- `app/confia_lean_auditor/claims/extractors/ita2025f2q5.py`
- `app/confia_lean_auditor/claims/extractors/ita2025f2q6.py`
- `app/confia_lean_auditor/claims/extractors/ita2025f2q8.py`
- `app/confia_lean_auditor/claims/extractors/ita2025q1.py`
- `app/confia_lean_auditor/claims/extractors/ita2025q3.py`
- `app/confia_lean_auditor/claims/extractors/ita2025q4.py`
- `app/confia_lean_auditor/claims/extractors/ita2025q5.py`
- `app/confia_lean_auditor/claims/extractors/ita2025q8.py`
- `app/confia_lean_auditor/core/__init__.py`
- `app/confia_lean_auditor/core/paths.py`
- `app/confia_lean_auditor/core/problem_assets.py`
- `app/confia_lean_auditor/core/schemas.py`
- `app/confia_lean_auditor/lean/__init__.py`
- `app/confia_lean_auditor/lean/attempt_builders/__init__.py`
- `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q1.py`
- `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q3.py`
- `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q5.py`
- `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q6.py`
- `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q8.py`
- `app/confia_lean_auditor/lean/attempt_builders/ita2025q1.py`
- `app/confia_lean_auditor/lean/attempt_builders/ita2025q3.py`
- `app/confia_lean_auditor/lean/attempt_builders/ita2025q4.py`
- `app/confia_lean_auditor/lean/attempt_builders/ita2025q5.py`
- `app/confia_lean_auditor/lean/attempt_builders/ita2025q8.py`
- `app/confia_lean_auditor/lean/build_attempt.py`
- `app/confia_lean_auditor/lean/formal_step_evaluator.py`
- `app/confia_lean_auditor/lean/microclaim_evaluator.py`
- `app/confia_lean_auditor/lean/run_lean.py`
- `app/confia_lean_auditor/lean/safe_formal_step.py`
- `app/confia_lean_auditor/lean/student_claim_checker.py`
- `app/confia_lean_auditor/lean/student_claim_checkers/__init__.py`
- `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q1.py`
- `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q3.py`
- `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q5.py`
- `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q6.py`
- `app/confia_lean_auditor/lean/student_claim_checkers/registry.py`
- `app/confia_lean_auditor/llm/__init__.py`
- `app/confia_lean_auditor/llm/formal_step_extractor.py`
- `app/confia_lean_auditor/main.py`
- `app/confia_lean_auditor/reports/__init__.py`
- `app/confia_lean_auditor/reports/report_builder.py`
- `app/confia_lean_auditor/rubric/__init__.py`
- `app/confia_lean_auditor/rubric/adjusters/__init__.py`
- `app/confia_lean_auditor/rubric/adjusters/ita2025f2q1.py`
- `app/confia_lean_auditor/rubric/adjusters/ita2025f2q3.py`
- `app/confia_lean_auditor/rubric/adjusters/ita2025f2q5.py`
- `app/confia_lean_auditor/rubric/adjusters/ita2025f2q6.py`
- `app/confia_lean_auditor/rubric/adjusters/ita2025f2q8.py`
- `app/confia_lean_auditor/rubric/adjusters/registry.py`
- `app/confia_lean_auditor/rubric/rubric_evaluator.py`
- `app/confia_lean_auditor/student_claims/__init__.py`
- `app/confia_lean_auditor/student_claims/extract_f2q1_student_claims.py`
- `app/confia_lean_auditor/student_claims/extract_f2q3_student_claims.py`
- `app/confia_lean_auditor/student_claims/extract_f2q5_student_claims.py`
- `app/confia_lean_auditor/student_claims/extract_f2q6_student_claims.py`
- `app/confia_lean_auditor/student_claims/extract_f2q8_student_claims.py`
- `app/confia_lean_auditor/student_claims/registry.py`
- `app/confia_lean_auditor/student_claims/schemas.py`
- `benchmarks/f2_suite_level1_2/gerar_tabelas_level1_f2_suite.py`
- `benchmarks/f2_suite_level1_2/gold_500.csv`
- `benchmarks/f2_suite_level1_2/make_gold_500_f2_suite.py`
- `benchmarks/f2_suite_level1_2/reports/RELATORIO_TECNICO_LEVEL1_F2_SUITE.md`
- `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py`
- `benchmarks/stage1_4/ita2025f2q8/gerar_relatorio_completo_benchmark_f2q8.py`
- `benchmarks/stage1_4/ita2025f2q8/gerar_relatorio_detalhado_sem_resumo_f2q8.py`
- `benchmarks/stage1_4/ita2025f2q8/gold_100.csv`
- `benchmarks/stage1_4/ita2025f2q8/make_gold_100_f2q8.py`
- `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py`
- `docs/lean_security_whitelist.md`
- `lake-manifest.json`
- `lakefile.toml`
- `lean-toolchain`
- `problems/ITA2025F2Q1/examples/answer_only.txt`
- `problems/ITA2025F2Q1/examples/correct_solution.txt`
- `problems/ITA2025F2Q1/examples/missing_reduced_form.txt`
- `problems/ITA2025F2Q1/examples/wrong_answer.txt`
- `problems/ITA2025F2Q1/microclaims.json`
- `problems/ITA2025F2Q1/problem.json`
- `problems/ITA2025F2Q1/rubric.json`
- `problems/ITA2025F2Q3/examples/answer_only.txt`
- `problems/ITA2025F2Q3/examples/correct_solution.txt`
- `problems/ITA2025F2Q3/examples/partial_beta_difference.txt`
- `problems/ITA2025F2Q3/examples/wrong_answer.txt`
- `problems/ITA2025F2Q3/microclaims.json`
- `problems/ITA2025F2Q3/problem.json`
- `problems/ITA2025F2Q3/rubric.json`
- `problems/ITA2025F2Q5/examples/answer_only.txt`
- `problems/ITA2025F2Q5/examples/correct_solution.txt`
- `problems/ITA2025F2Q5/examples/missing_bounds.txt`
- `problems/ITA2025F2Q5/examples/wrong_digit.txt`
- `problems/ITA2025F2Q5/microclaims.json`
- `problems/ITA2025F2Q5/problem.json`
- `problems/ITA2025F2Q5/rubric.json`
- `problems/ITA2025F2Q6/examples/answer_only.txt`
- `problems/ITA2025F2Q6/examples/correct_solution.txt`
- `problems/ITA2025F2Q6/examples/missing_ratio.txt`
- `problems/ITA2025F2Q6/examples/wrong_answer.txt`
- `problems/ITA2025F2Q6/microclaims.json`
- `problems/ITA2025F2Q6/problem.json`
- `problems/ITA2025F2Q6/rubric.json`
- `problems/ITA2025F2Q8/examples/answer_only.txt`
- `problems/ITA2025F2Q8/examples/correct_solution.txt`
- `problems/ITA2025F2Q8/examples/missing_determinant_formula.txt`
- `problems/ITA2025F2Q8/examples/wrong_answer.txt`
- `problems/ITA2025F2Q8/microclaims.json`
- `problems/ITA2025F2Q8/problem.json`
- `problems/ITA2025F2Q8/rubric.json`
- `problems/ITA2025Q1/certificate/Statement.lean`
- `problems/ITA2025Q1/examples/answer_only.txt`
- `problems/ITA2025Q1/examples/correct_solution.txt`
- `problems/ITA2025Q1/examples/injection_attempt.txt`
- `problems/ITA2025Q1/examples/partial_no_positive_root.txt`
- `problems/ITA2025Q1/examples/wrong_determinant_step.txt`
- `problems/ITA2025Q1/examples/wrong_solution.txt`
- `problems/ITA2025Q1/microclaims.json`
- `problems/ITA2025Q1/problem.json`
- `problems/ITA2025Q1/rubric.json`
- `problems/ITA2025Q3/examples/answer_only.txt`
- `problems/ITA2025Q3/examples/correct_solution.txt`
- `problems/ITA2025Q3/examples/missing_parity.txt`
- `problems/ITA2025Q3/examples/wrong_coefficient.txt`
- `problems/ITA2025Q3/microclaims.json`
- `problems/ITA2025Q3/problem.json`
- `problems/ITA2025Q3/rubric.json`
- `problems/ITA2025Q4/examples/answer_only.txt`
- `problems/ITA2025Q4/examples/correct_solution.txt`
- `problems/ITA2025Q4/examples/missing_distinct_inputs.txt`
- `problems/ITA2025Q4/examples/wrong_target.txt`
- `problems/ITA2025Q4/examples/wrong_witnesses.txt`
- `problems/ITA2025Q4/microclaims.json`
- `problems/ITA2025Q4/problem.json`
- `problems/ITA2025Q4/rubric.json`
- `problems/ITA2025Q5/examples/answer_only.txt`
- `problems/ITA2025Q5/examples/correct_solution.txt`
- `problems/ITA2025Q5/examples/missing_difference_relation.txt`
- `problems/ITA2025Q5/examples/missing_factorization.txt`
- `problems/ITA2025Q5/examples/wrong_direction.txt`
- `problems/ITA2025Q5/microclaims.json`
- `problems/ITA2025Q5/problem.json`
- `problems/ITA2025Q5/rubric.json`
- `problems/ITA2025Q8/examples/answer_only.txt`
- `problems/ITA2025Q8/examples/correct_solution.txt`
- `problems/ITA2025Q8/examples/missing_sign_analysis.txt`
- `problems/ITA2025Q8/examples/wrong_interval.txt`
- `problems/ITA2025Q8/microclaims.json`
- `problems/ITA2025Q8/problem.json`
- `problems/ITA2025Q8/rubric.json`
- `pyproject.toml`
- `tests/test_evaluator_architecture.py`
- `tests/test_f2q1_rubric_adjustments.py`
- `tests/test_f2q1_strong_certificate.py`
- `tests/test_f2q1_student_claim_checks.py`
- `tests/test_f2q3_rubric_adjustments.py`
- `tests/test_f2q3_strong_certificate.py`
- `tests/test_f2q3_student_claim_checks.py`
- `tests/test_f2q5_rubric_adjustments.py`
- `tests/test_f2q5_strong_certificate.py`
- `tests/test_f2q5_student_claim_checks.py`
- `tests/test_f2q6_rubric_adjustments.py`
- `tests/test_f2q6_strong_certificate.py`
- `tests/test_f2q6_student_claim_checks.py`
- `tests/test_f2q8_student_claim_checks.py`
- `tests/test_ita2025f2q1_level1.py`
- `tests/test_ita2025f2q3_level1.py`
- `tests/test_ita2025f2q5_level1.py`
- `tests/test_ita2025f2q6_level1.py`
- `tests/test_ita2025f2q8_level1.py`
- `tests/test_ita2025q1_level2.py`
- `tests/test_ita2025q3_level1.py`
- `tests/test_ita2025q4_level1.py`
- `tests/test_ita2025q4_level2.py`
- `tests/test_ita2025q5_level1.py`
- `tests/test_ita2025q8_level1.py`
- `tests/test_level1_f2_suite_regressions.py`
- `tests/test_problem_assets_contracts.py`
- `tests/test_problem_assets_validation.py`
- `tests/test_problem_router_coverage.py`

Arquivos visíveis não versionados detectados nesta auditoria:

- `benchmarks/f2_suite_level1_v2/gold_500_v2.csv`
- `benchmarks/f2_suite_level1_v2/run_level1_f2_suite_v2.py`
- `benchmarks/q_suite_level1_v2/gold_500.csv`
- `benchmarks/q_suite_level1_v2/make_gold_500_q_suite_v2.py`
- `benchmarks/q_suite_level1_v2/run_level1_q_suite_v2.py`

Módulos em uma linha: `main.py` expõe `/health` e `/audit` em `app/confia_lean_auditor/main.py:33` e `app/confia_lean_auditor/main.py:42`; `schemas.py` define `AuditRequest`, `FormalStep`, `LeanCertificate`, `MicroclaimResult` e `AuditResponse` em `app/confia_lean_auditor/core/schemas.py:8`, `app/confia_lean_auditor/core/schemas.py:13`, `app/confia_lean_auditor/core/schemas.py:76`, `app/confia_lean_auditor/core/schemas.py:88` e `app/confia_lean_auditor/core/schemas.py:102`; `problem_assets.py` valida os três JSON obrigatórios em `app/confia_lean_auditor/core/problem_assets.py:103`, `app/confia_lean_auditor/core/problem_assets.py:115`, `app/confia_lean_auditor/core/problem_assets.py:127` e `app/confia_lean_auditor/core/problem_assets.py:154`; `extract_claims.py` roteia dez problemas em `app/confia_lean_auditor/claims/extract_claims.py:41` a `app/confia_lean_auditor/claims/extract_claims.py:75`; `build_attempt.py` roteia builders Lean em `app/confia_lean_auditor/lean/build_attempt.py:44` a `app/confia_lean_auditor/lean/build_attempt.py:123`; `formal_step_evaluator.py` roteia renderizadores em `app/confia_lean_auditor/lean/formal_step_evaluator.py:411` a `app/confia_lean_auditor/lean/formal_step_evaluator.py:441`; `student_claims/registry.py`, `student_claim_checkers/registry.py` e `rubric/adjusters/registry.py` compõem o pipeline F2 em `app/confia_lean_auditor/student_claims/registry.py:23` a `app/confia_lean_auditor/student_claims/registry.py:39`, `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:23` a `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:62` e `app/confia_lean_auditor/rubric/adjusters/registry.py:26` a `app/confia_lean_auditor/rubric/adjusters/registry.py:45`; `run_lean.py` executa `lake env lean` em `app/confia_lean_auditor/lean/run_lean.py:65` a `app/confia_lean_auditor/lean/run_lean.py:98`; `ConfiaLeanAuditor.lean` agrega dez statements Lean em `ConfiaLeanAuditor.lean:1` a `ConfiaLeanAuditor.lean:11`.

## 2. Diagrama de arquitetura textual

```text
Cliente HTTP
  -> FastAPI app em app/confia_lean_auditor/main.py
     -> GET /health
     -> POST /audit: AuditRequest(problem_id, solution)
        -> get_repo_root / get_problem_dir
        -> validate_problem_assets: problem.json + rubric.json + microclaims.json
        -> extract_claims: dispatcher por problem_id
        -> evaluate_formal_steps: formal_steps/*.lean -> lake env lean
        -> build_attempt: Attempt.lean
        -> run_lean_file: lake env lean Attempt.lean
        -> evaluate_microclaims: claim types + formal steps + generated_theorems
        -> extract_student_claims: somente família F2 retorna claims concretos
        -> check_student_claims_for_problem: Lean dinâmico por claim F2
        -> evaluate_rubric
        -> apply_student_claim_adjustments
        -> verdict_from_score + build_feedback
        -> AuditResponse
        -> audit.json, solution.txt, claims.json, student_claims.json, student_claim_checks.json

CLI Python
  -> app/confia_lean_auditor/lean/run_lean.py --problem-id X --repo-root .
     -> problems/{problem_id}/certificate/Statement.lean
     -> lake env lean
     -> JSON em stdout

Lake / Lean
  -> lakefile.toml defaultTargets ["ConfiaLeanAuditor"]
     -> ConfiaLeanAuditor.lean
        -> Basic + Statements ITA2025Q* + ITA2025F2Q*

Benchmarks
  -> benchmarks/*/*.py
     -> CSV gold
     -> extract_claims
     -> JSON/CSV/Markdown em reports ignorados

GitHub Actions
  -> python_tests.yml: Lean + Python 3.11 + pip install -e . + pytest
  -> lean_action_ci.yml: lake build + pytest
  -> create-release.yml: release quando lean-toolchain muda
  -> update.yml: mathlib-update-action manual
```

O fluxo HTTP cria `artifact_dir` em `app/confia_lean_auditor/main.py:59` a `app/confia_lean_auditor/main.py:61`, extrai claims em `app/confia_lean_auditor/main.py:63` a `app/confia_lean_auditor/main.py:66`, avalia formal steps em `app/confia_lean_auditor/main.py:68` a `app/confia_lean_auditor/main.py:76`, constrói e executa Lean em `app/confia_lean_auditor/main.py:78` a `app/confia_lean_auditor/main.py:96`, calcula microclaims em `app/confia_lean_auditor/main.py:98` a `app/confia_lean_auditor/main.py:109`, executa student claims em `app/confia_lean_auditor/main.py:112` a `app/confia_lean_auditor/main.py:120`, avalia e ajusta rubrica em `app/confia_lean_auditor/main.py:122` a `app/confia_lean_auditor/main.py:137`, monta resposta em `app/confia_lean_auditor/main.py:143` a `app/confia_lean_auditor/main.py:157`, e grava cinco saídas em `app/confia_lean_auditor/main.py:159` a `app/confia_lean_auditor/main.py:178`.

## 3. Grafo de dependências

### Python: imports estáticos

- `app/confia_lean_auditor/main.py` importa FastAPI e todos os módulos de orquestração, incluindo registries de student claims e adjusters, em `app/confia_lean_auditor/main.py:8` a `app/confia_lean_auditor/main.py:23`.
- `claims/extract_claims.py` importa os extratores Q1/Q3/Q4/Q5/Q8 e F2Q1/F2Q3/F2Q5/F2Q6/F2Q8 em `app/confia_lean_auditor/claims/extract_claims.py:3` a `app/confia_lean_auditor/claims/extract_claims.py:39`, e o dispatcher cobre esses IDs em `app/confia_lean_auditor/claims/extract_claims.py:41` a `app/confia_lean_auditor/claims/extract_claims.py:70`.
- `lean/build_attempt.py` importa os builders dos mesmos dez problemas em `app/confia_lean_auditor/lean/build_attempt.py:6` a `app/confia_lean_auditor/lean/build_attempt.py:42`, e lança `NotImplementedError` para problema sem builder em `app/confia_lean_auditor/lean/build_attempt.py:123`.
- `formal_step_evaluator.py` depende de schemas, runner Lean e whitelist em `app/confia_lean_auditor/lean/formal_step_evaluator.py:6` a `app/confia_lean_auditor/lean/formal_step_evaluator.py:15`, renderiza formal steps por problema em `app/confia_lean_auditor/lean/formal_step_evaluator.py:23` a `app/confia_lean_auditor/lean/formal_step_evaluator.py:441`, e escreve arquivos Lean por step em `app/confia_lean_auditor/lean/formal_step_evaluator.py:444` a `app/confia_lean_auditor/lean/formal_step_evaluator.py:493`.
- O pipeline F2 de claims concretos usa `student_claims/registry.py` para extração em `app/confia_lean_auditor/student_claims/registry.py:5` a `app/confia_lean_auditor/student_claims/registry.py:39`, usa `lean/student_claim_checkers/registry.py` para verificação dinâmica em `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:5` a `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:62`, e usa `rubric/adjusters/registry.py` para ajustes em `app/confia_lean_auditor/rubric/adjusters/registry.py:5` a `app/confia_lean_auditor/rubric/adjusters/registry.py:45`.
- Benchmarks importam o dispatcher de claims em `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py:9` e `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py:9`, e escrevem relatórios em `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py:172` a `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py:273` e `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py:85` a `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py:242`.

### Python: imports inversos

- `core/schemas.py` é contrato central: consumido por `main.py`, `problem_assets.py`, `microclaim_evaluator.py`, `rubric_evaluator.py`, builders e adjusters, com campos de resposta expandidos para `student_claims` e `student_claim_checks` em `app/confia_lean_auditor/core/schemas.py:102` a `app/confia_lean_auditor/core/schemas.py:116`.
- `core/paths.py` é usado por API, validação, runner e testes: `main.py` chama `get_problem_dir` e `get_repo_root` em `app/confia_lean_auditor/main.py:11`, `run_lean.py` usa `get_problem_dir` em `app/confia_lean_auditor/lean/run_lean.py:10`, e testes de assets importam os helpers em `tests/test_problem_assets_validation.py:7`.
- `main.py` é consumido por testes via `TestClient`, como em `tests/test_ita2025q1_level2.py:7` e `tests/test_ita2025q8_level1.py:5`, enquanto os testes F2 de student claims exercitam diretamente os checkers e extratores em `tests/test_f2q8_student_claim_checks.py:7` a `tests/test_f2q8_student_claim_checks.py:13` e `tests/test_f2q6_student_claim_checks.py:11` a `tests/test_f2q6_student_claim_checks.py:23`.

### Lean: imports estáticos e inversos

- `ConfiaLeanAuditor.lean` importa `Basic`, cinco statements Q e cinco statements F2 em `ConfiaLeanAuditor.lean:1` a `ConfiaLeanAuditor.lean:11`.
- Cada statement Lean de problema importa `Mathlib`; exemplos F2 estão em `ConfiaLeanAuditor/Problems/ITA2025F2Q3/Statement.lean:1` e `ConfiaLeanAuditor/Problems/ITA2025F2Q5/Statement.lean:1`.
- Os builders geram imports Lean em strings Python, como `ConfiaLeanAuditor.Problems.ITA2025Q1.Statement` em `app/confia_lean_auditor/lean/attempt_builders/ita2025q1.py:10` e `ConfiaLeanAuditor.Problems.ITA2025F2Q8.Statement` em `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q8.py:10`.
- O CLI genérico de `run_lean.py` ainda procura `problems/{problem_id}/certificate/Statement.lean` em `app/confia_lean_auditor/lean/run_lean.py:101` a `app/confia_lean_auditor/lean/run_lean.py:128`; no inventário versionado, esse padrão aparece apenas para Q1 em `problems/ITA2025Q1/certificate/Statement.lean:1`.

### Acoplamento dinâmico, ciclos e órfãos

Não há ciclo estático interno observado entre módulos Python de produção: a direção principal é `main.py` -> dispatchers/avaliadores -> schemas/assets/runner, e os testes importam a API sem serem importados por ela, conforme `app/confia_lean_auditor/main.py:8` a `app/confia_lean_auditor/main.py:23` e `tests/test_ita2025q1_level2.py:7`. O acoplamento dinâmico inclui env var de raiz em `app/confia_lean_auditor/core/paths.py:15` a `app/confia_lean_auditor/core/paths.py:22`, leitura de JSON fixos em `app/confia_lean_auditor/core/problem_assets.py:103` a `app/confia_lean_auditor/core/problem_assets.py:132`, subprocess Lean com timeout em `app/confia_lean_auditor/lean/run_lean.py:65` a `app/confia_lean_auditor/lean/run_lean.py:98`, artefatos HTTP em `app/confia_lean_auditor/main.py:159` a `app/confia_lean_auditor/main.py:178`, artefatos de student checks em `app/confia_lean_auditor/lean/student_claim_checker.py:12` a `app/confia_lean_auditor/lean/student_claim_checker.py:25`, e LLM condicionado por env var em `app/confia_lean_auditor/llm/formal_step_extractor.py:52` a `app/confia_lean_auditor/llm/formal_step_extractor.py:53`.

Candidatos refutados: os extratores F2 não são órfãos porque `extract_claims.py` os importa e roteia em `app/confia_lean_auditor/claims/extract_claims.py:23` a `app/confia_lean_auditor/claims/extract_claims.py:70`; os builders F2 não são órfãos porque `build_attempt.py` os importa e roteia em `app/confia_lean_auditor/lean/build_attempt.py:26` a `app/confia_lean_auditor/lean/build_attempt.py:121`; os problemas implementados são cobrados por teste textual de roteamento em `tests/test_problem_router_coverage.py:12` a `tests/test_problem_router_coverage.py:58`. Confirmados como scaffold/baixo uso semântico: `ConfiaLeanAuditor/Basic.lean` só define `hello` em `ConfiaLeanAuditor/Basic.lean:1` e é importado pelo agregador em `ConfiaLeanAuditor.lean:1`; `README.md` mantém instrução de remover seção de configuração GitHub em `README.md:13`.

## 4. Pontos de entrada e saída consolidados

Entradas: rota `GET /health` em `app/confia_lean_auditor/main.py:33`; rota `POST /audit` em `app/confia_lean_auditor/main.py:42`; CLI `run_lean.py` em `app/confia_lean_auditor/lean/run_lean.py:131` a `app/confia_lean_auditor/lean/run_lean.py:142`; alvo Lake em `lakefile.toml:4`; workflows CI em `.github/workflows/python_tests.yml:3` a `.github/workflows/python_tests.yml:32` e `.github/workflows/lean_action_ci.yml:3` a `.github/workflows/lean_action_ci.yml:37`; release por `lean-toolchain` em `.github/workflows/create-release.yml:3` a `.github/workflows/create-release.yml:22`; update manual em `.github/workflows/update.yml:3` a `.github/workflows/update.yml:41`; scripts de benchmark com `main()` em `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py:155` e `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py:68`.

Saídas: `AuditResponse` em `app/confia_lean_auditor/core/schemas.py:102` a `app/confia_lean_auditor/core/schemas.py:116`; `audit.json`, `solution.txt`, `claims.json`, `student_claims.json` e `student_claim_checks.json` em `app/confia_lean_auditor/main.py:159` a `app/confia_lean_auditor/main.py:178`; `formal_steps/*.lean` e `.rejected.txt` em `app/confia_lean_auditor/lean/formal_step_evaluator.py:450` a `app/confia_lean_auditor/lean/formal_step_evaluator.py:493`; `Attempt.lean` por builder, como `app/confia_lean_auditor/lean/attempt_builders/ita2025q1.py:132`, `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q1.py:134`, `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q8.py:129`; JSON no stdout do CLI em `app/confia_lean_auditor/lean/run_lean.py:137` a `app/confia_lean_auditor/lean/run_lean.py:138`; relatórios de benchmark em `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py:273` e `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py:242`.

Contratos que batem: `ProblemConfig`, `RubricConfig`, `MicroclaimConfig`, `MicroclaimsConfig` e `ProblemAssets` proíbem campos extras em `app/confia_lean_auditor/core/problem_assets.py:14` a `app/confia_lean_auditor/core/problem_assets.py:69`; `validate_problem_assets` cruza IDs, referências de microclaims, dependências e soma de pontos em `app/confia_lean_auditor/core/problem_assets.py:154` a `app/confia_lean_auditor/core/problem_assets.py:219`; há teste para contratos sem parsing JSON direto em avaliadores em `tests/test_evaluator_architecture.py:4` a `tests/test_evaluator_architecture.py:14`; há teste de cobertura dos roteadores por inventário de `problems/ITA2025*/problem.json` em `tests/test_problem_router_coverage.py:12` a `tests/test_problem_router_coverage.py:58`.

Contratos que divergem por desenho ou risco de sincronização: `AuditResponse` inclui `student_claims` e `student_claim_checks` em `app/confia_lean_auditor/core/schemas.py:113` a `app/confia_lean_auditor/core/schemas.py:114`, mas esses dados são produzidos por dataclasses em `app/confia_lean_auditor/student_claims/schemas.py:41` a `app/confia_lean_auditor/student_claims/schemas.py:68` e serializados via `asdict` em `app/confia_lean_auditor/main.py:119` a `app/confia_lean_auditor/main.py:120`; F2 tem adjusters registrados apenas para F2Q1/F2Q3/F2Q5/F2Q6/F2Q8 em `app/confia_lean_auditor/rubric/adjusters/registry.py:26` a `app/confia_lean_auditor/rubric/adjusters/registry.py:32`, enquanto problemas Q retornam lista vazia de student claims em `app/confia_lean_auditor/student_claims/registry.py:23` a `app/confia_lean_auditor/student_claims/registry.py:39`.

## 5. Análise módulo a módulo

Formato desta seção: cada linha cobre um arquivo versionado do inventário; arquivos vazios de pacote usam como evidência a linha de import ou consumo mais próxima. Risco: ALTO para contratos runtime, geração/verificação Lean e assets formais; MÉDIO para CI, testes, benchmarks e configurações; BAIXO para documentação, fixtures e scaffolds.

#### Analisado 1 de 203 — `.github/workflows/create-release.yml`
**Responsabilidade:** workflow GitHub Actions de CI, release ou atualização. Evidência: `.github/workflows/create-release.yml:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 2 de 203 — `.github/workflows/lean_action_ci.yml`
**Responsabilidade:** workflow GitHub Actions de CI, release ou atualização. Evidência: `.github/workflows/lean_action_ci.yml:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 3 de 203 — `.github/workflows/python_tests.yml`
**Responsabilidade:** workflow GitHub Actions de CI, release ou atualização. Evidência: `.github/workflows/python_tests.yml:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 4 de 203 — `.github/workflows/update.yml`
**Responsabilidade:** workflow GitHub Actions de CI, release ou atualização. Evidência: `.github/workflows/update.yml:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 5 de 203 — `.gitignore`
**Responsabilidade:** configuração de exclusões Git para ambientes, artefatos e caches. Evidência: `.gitignore:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 6 de 203 — `AUDITORIA_REPOSITORIO.md`
**Responsabilidade:** documentação técnica. Evidência: `AUDITORIA_REPOSITORIO.md:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 7 de 203 — `ConfiaLeanAuditor.lean`
**Responsabilidade:** módulo raiz Lean que agrega statements. Evidência: `ConfiaLeanAuditor.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 8 de 203 — `ConfiaLeanAuditor/Basic.lean`
**Responsabilidade:** scaffold Lean mínimo com definição hello. Evidência: `ConfiaLeanAuditor/Basic.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** scaffold confirmado, pois só define `hello`.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 9 de 203 — `ConfiaLeanAuditor/Problems/ITA2025F2Q1/Statement.lean`
**Responsabilidade:** statement Lean de problema. Evidência: `ConfiaLeanAuditor/Problems/ITA2025F2Q1/Statement.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 10 de 203 — `ConfiaLeanAuditor/Problems/ITA2025F2Q3/Statement.lean`
**Responsabilidade:** statement Lean de problema. Evidência: `ConfiaLeanAuditor/Problems/ITA2025F2Q3/Statement.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 11 de 203 — `ConfiaLeanAuditor/Problems/ITA2025F2Q5/Statement.lean`
**Responsabilidade:** statement Lean de problema. Evidência: `ConfiaLeanAuditor/Problems/ITA2025F2Q5/Statement.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 12 de 203 — `ConfiaLeanAuditor/Problems/ITA2025F2Q6/Statement.lean`
**Responsabilidade:** statement Lean de problema. Evidência: `ConfiaLeanAuditor/Problems/ITA2025F2Q6/Statement.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 13 de 203 — `ConfiaLeanAuditor/Problems/ITA2025F2Q8/Statement.lean`
**Responsabilidade:** statement Lean de problema. Evidência: `ConfiaLeanAuditor/Problems/ITA2025F2Q8/Statement.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 14 de 203 — `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean`
**Responsabilidade:** statement Lean de problema. Evidência: `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 15 de 203 — `ConfiaLeanAuditor/Problems/ITA2025Q3/Statement.lean`
**Responsabilidade:** statement Lean de problema. Evidência: `ConfiaLeanAuditor/Problems/ITA2025Q3/Statement.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 16 de 203 — `ConfiaLeanAuditor/Problems/ITA2025Q4/Statement.lean`
**Responsabilidade:** statement Lean de problema. Evidência: `ConfiaLeanAuditor/Problems/ITA2025Q4/Statement.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 17 de 203 — `ConfiaLeanAuditor/Problems/ITA2025Q5/Statement.lean`
**Responsabilidade:** statement Lean de problema. Evidência: `ConfiaLeanAuditor/Problems/ITA2025Q5/Statement.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 18 de 203 — `ConfiaLeanAuditor/Problems/ITA2025Q8/Statement.lean`
**Responsabilidade:** statement Lean de problema. Evidência: `ConfiaLeanAuditor/Problems/ITA2025Q8/Statement.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 19 de 203 — `MILESTONE_ITA2025F2.md`
**Responsabilidade:** documentação técnica. Evidência: `MILESTONE_ITA2025F2.md:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 20 de 203 — `README.md`
**Responsabilidade:** documentação técnica. Evidência: `README.md:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** README ainda contém texto de setup removível.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 21 de 203 — `app/confia_lean_auditor/__init__.py`
**Responsabilidade:** marcador de pacote Python. Evidência: `app/confia_lean_auditor/main.py:10`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 22 de 203 — `app/confia_lean_auditor/claims/__init__.py`
**Responsabilidade:** marcador de pacote Python. Evidência: `app/confia_lean_auditor/main.py:10`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 23 de 203 — `app/confia_lean_auditor/claims/extract_claims.py`
**Responsabilidade:** dispatcher de extração por problem_id. Evidência: `app/confia_lean_auditor/claims/extract_claims.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 24 de 203 — `app/confia_lean_auditor/claims/extractors/__init__.py`
**Responsabilidade:** extrator heurístico de claims por problema. Evidência: `app/confia_lean_auditor/claims/extract_claims.py:4`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** heurísticas locais por strings/regex e acoplamento por problem_id.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 25 de 203 — `app/confia_lean_auditor/claims/extractors/ita2025f2q1.py`
**Responsabilidade:** extrator heurístico de claims por problema. Evidência: `app/confia_lean_auditor/claims/extractors/ita2025f2q1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** heurísticas locais por strings/regex e acoplamento por problem_id.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 26 de 203 — `app/confia_lean_auditor/claims/extractors/ita2025f2q3.py`
**Responsabilidade:** extrator heurístico de claims por problema. Evidência: `app/confia_lean_auditor/claims/extractors/ita2025f2q3.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** heurísticas locais por strings/regex e acoplamento por problem_id.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 27 de 203 — `app/confia_lean_auditor/claims/extractors/ita2025f2q5.py`
**Responsabilidade:** extrator heurístico de claims por problema. Evidência: `app/confia_lean_auditor/claims/extractors/ita2025f2q5.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** heurísticas locais por strings/regex e acoplamento por problem_id.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 28 de 203 — `app/confia_lean_auditor/claims/extractors/ita2025f2q6.py`
**Responsabilidade:** extrator heurístico de claims por problema. Evidência: `app/confia_lean_auditor/claims/extractors/ita2025f2q6.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** heurísticas locais por strings/regex e acoplamento por problem_id.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 29 de 203 — `app/confia_lean_auditor/claims/extractors/ita2025f2q8.py`
**Responsabilidade:** extrator heurístico de claims por problema. Evidência: `app/confia_lean_auditor/claims/extractors/ita2025f2q8.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** heurísticas locais por strings/regex e acoplamento por problem_id.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 30 de 203 — `app/confia_lean_auditor/claims/extractors/ita2025q1.py`
**Responsabilidade:** extrator heurístico de claims por problema. Evidência: `app/confia_lean_auditor/claims/extractors/ita2025q1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** heurísticas locais por strings/regex e acoplamento por problem_id.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 31 de 203 — `app/confia_lean_auditor/claims/extractors/ita2025q3.py`
**Responsabilidade:** extrator heurístico de claims por problema. Evidência: `app/confia_lean_auditor/claims/extractors/ita2025q3.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** heurísticas locais por strings/regex e acoplamento por problem_id.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 32 de 203 — `app/confia_lean_auditor/claims/extractors/ita2025q4.py`
**Responsabilidade:** extrator heurístico de claims por problema. Evidência: `app/confia_lean_auditor/claims/extractors/ita2025q4.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** heurísticas locais por strings/regex e acoplamento por problem_id.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 33 de 203 — `app/confia_lean_auditor/claims/extractors/ita2025q5.py`
**Responsabilidade:** extrator heurístico de claims por problema. Evidência: `app/confia_lean_auditor/claims/extractors/ita2025q5.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** heurísticas locais por strings/regex e acoplamento por problem_id.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 34 de 203 — `app/confia_lean_auditor/claims/extractors/ita2025q8.py`
**Responsabilidade:** extrator heurístico de claims por problema. Evidência: `app/confia_lean_auditor/claims/extractors/ita2025q8.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** heurísticas locais por strings/regex e acoplamento por problem_id.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 35 de 203 — `app/confia_lean_auditor/core/__init__.py`
**Responsabilidade:** marcador de pacote Python. Evidência: `app/confia_lean_auditor/main.py:11`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 36 de 203 — `app/confia_lean_auditor/core/paths.py`
**Responsabilidade:** resolução de raiz e problem_id. Evidência: `app/confia_lean_auditor/core/paths.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 37 de 203 — `app/confia_lean_auditor/core/problem_assets.py`
**Responsabilidade:** validação de assets de problema. Evidência: `app/confia_lean_auditor/core/problem_assets.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 38 de 203 — `app/confia_lean_auditor/core/schemas.py`
**Responsabilidade:** schemas Pydantic ou dataclasses de contratos internos. Evidência: `app/confia_lean_auditor/core/schemas.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 39 de 203 — `app/confia_lean_auditor/lean/__init__.py`
**Responsabilidade:** marcador de pacote Python. Evidência: `app/confia_lean_auditor/main.py:14`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 40 de 203 — `app/confia_lean_auditor/lean/attempt_builders/__init__.py`
**Responsabilidade:** builder de Attempt.lean por problema. Evidência: `app/confia_lean_auditor/lean/build_attempt.py:7`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** strings Lean embutidas no Python e acoplamento com statement Lean específico.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 41 de 203 — `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q1.py`
**Responsabilidade:** builder de Attempt.lean por problema. Evidência: `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** strings Lean embutidas no Python e acoplamento com statement Lean específico.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 42 de 203 — `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q3.py`
**Responsabilidade:** builder de Attempt.lean por problema. Evidência: `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q3.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** strings Lean embutidas no Python e acoplamento com statement Lean específico.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 43 de 203 — `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q5.py`
**Responsabilidade:** builder de Attempt.lean por problema. Evidência: `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q5.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** strings Lean embutidas no Python e acoplamento com statement Lean específico.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 44 de 203 — `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q6.py`
**Responsabilidade:** builder de Attempt.lean por problema. Evidência: `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q6.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** strings Lean embutidas no Python e acoplamento com statement Lean específico.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 45 de 203 — `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q8.py`
**Responsabilidade:** builder de Attempt.lean por problema. Evidência: `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q8.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** strings Lean embutidas no Python e acoplamento com statement Lean específico.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 46 de 203 — `app/confia_lean_auditor/lean/attempt_builders/ita2025q1.py`
**Responsabilidade:** builder de Attempt.lean por problema. Evidência: `app/confia_lean_auditor/lean/attempt_builders/ita2025q1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** strings Lean embutidas no Python e acoplamento com statement Lean específico.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 47 de 203 — `app/confia_lean_auditor/lean/attempt_builders/ita2025q3.py`
**Responsabilidade:** builder de Attempt.lean por problema. Evidência: `app/confia_lean_auditor/lean/attempt_builders/ita2025q3.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** strings Lean embutidas no Python e acoplamento com statement Lean específico.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 48 de 203 — `app/confia_lean_auditor/lean/attempt_builders/ita2025q4.py`
**Responsabilidade:** builder de Attempt.lean por problema. Evidência: `app/confia_lean_auditor/lean/attempt_builders/ita2025q4.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** strings Lean embutidas no Python e acoplamento com statement Lean específico.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 49 de 203 — `app/confia_lean_auditor/lean/attempt_builders/ita2025q5.py`
**Responsabilidade:** builder de Attempt.lean por problema. Evidência: `app/confia_lean_auditor/lean/attempt_builders/ita2025q5.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** strings Lean embutidas no Python e acoplamento com statement Lean específico.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 50 de 203 — `app/confia_lean_auditor/lean/attempt_builders/ita2025q8.py`
**Responsabilidade:** builder de Attempt.lean por problema. Evidência: `app/confia_lean_auditor/lean/attempt_builders/ita2025q8.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** strings Lean embutidas no Python e acoplamento com statement Lean específico.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 51 de 203 — `app/confia_lean_auditor/lean/build_attempt.py`
**Responsabilidade:** dispatcher de builders Lean por problem_id. Evidência: `app/confia_lean_auditor/lean/build_attempt.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 52 de 203 — `app/confia_lean_auditor/lean/formal_step_evaluator.py`
**Responsabilidade:** renderizador e avaliador de formal steps Lean. Evidência: `app/confia_lean_auditor/lean/formal_step_evaluator.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 53 de 203 — `app/confia_lean_auditor/lean/microclaim_evaluator.py`
**Responsabilidade:** avaliador de microclaims. Evidência: `app/confia_lean_auditor/lean/microclaim_evaluator.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 54 de 203 — `app/confia_lean_auditor/lean/run_lean.py`
**Responsabilidade:** runner Lean e CLI por subprocess. Evidência: `app/confia_lean_auditor/lean/run_lean.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 55 de 203 — `app/confia_lean_auditor/lean/safe_formal_step.py`
**Responsabilidade:** arquivo versionado do projeto. Evidência: `app/confia_lean_auditor/lean/safe_formal_step.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 56 de 203 — `app/confia_lean_auditor/lean/student_claim_checker.py`
**Responsabilidade:** verificador Lean legado de student claims F2Q8. Evidência: `app/confia_lean_auditor/lean/student_claim_checker.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 57 de 203 — `app/confia_lean_auditor/lean/student_claim_checkers/__init__.py`
**Responsabilidade:** verificador Lean de student claims por problema F2. Evidência: `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:9`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 58 de 203 — `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q1.py`
**Responsabilidade:** verificador Lean de student claims por problema F2. Evidência: `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 59 de 203 — `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q3.py`
**Responsabilidade:** verificador Lean de student claims por problema F2. Evidência: `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q3.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 60 de 203 — `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q5.py`
**Responsabilidade:** verificador Lean de student claims por problema F2. Evidência: `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q5.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 61 de 203 — `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q6.py`
**Responsabilidade:** verificador Lean de student claims por problema F2. Evidência: `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q6.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 62 de 203 — `app/confia_lean_auditor/lean/student_claim_checkers/registry.py`
**Responsabilidade:** verificador Lean de student claims por problema F2. Evidência: `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 63 de 203 — `app/confia_lean_auditor/llm/__init__.py`
**Responsabilidade:** marcador de pacote Python. Evidência: `app/confia_lean_auditor/main.py:21`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 64 de 203 — `app/confia_lean_auditor/llm/formal_step_extractor.py`
**Responsabilidade:** fallback opcional de extração por LLM. Evidência: `app/confia_lean_auditor/llm/formal_step_extractor.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 65 de 203 — `app/confia_lean_auditor/main.py`
**Responsabilidade:** API FastAPI e orquestrador ponta a ponta. Evidência: `app/confia_lean_auditor/main.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 66 de 203 — `app/confia_lean_auditor/reports/__init__.py`
**Responsabilidade:** marcador de pacote Python. Evidência: `app/confia_lean_auditor/main.py:18`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 67 de 203 — `app/confia_lean_auditor/reports/report_builder.py`
**Responsabilidade:** montagem de verdict e feedback textual. Evidência: `app/confia_lean_auditor/reports/report_builder.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 68 de 203 — `app/confia_lean_auditor/rubric/__init__.py`
**Responsabilidade:** marcador de pacote Python. Evidência: `app/confia_lean_auditor/main.py:19`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 69 de 203 — `app/confia_lean_auditor/rubric/adjusters/__init__.py`
**Responsabilidade:** ajustador de rubrica por student_claim_checks. Evidência: `app/confia_lean_auditor/rubric/adjusters/registry.py:6`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 70 de 203 — `app/confia_lean_auditor/rubric/adjusters/ita2025f2q1.py`
**Responsabilidade:** ajustador de rubrica por student_claim_checks. Evidência: `app/confia_lean_auditor/rubric/adjusters/ita2025f2q1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 71 de 203 — `app/confia_lean_auditor/rubric/adjusters/ita2025f2q3.py`
**Responsabilidade:** ajustador de rubrica por student_claim_checks. Evidência: `app/confia_lean_auditor/rubric/adjusters/ita2025f2q3.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 72 de 203 — `app/confia_lean_auditor/rubric/adjusters/ita2025f2q5.py`
**Responsabilidade:** ajustador de rubrica por student_claim_checks. Evidência: `app/confia_lean_auditor/rubric/adjusters/ita2025f2q5.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 73 de 203 — `app/confia_lean_auditor/rubric/adjusters/ita2025f2q6.py`
**Responsabilidade:** ajustador de rubrica por student_claim_checks. Evidência: `app/confia_lean_auditor/rubric/adjusters/ita2025f2q6.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 74 de 203 — `app/confia_lean_auditor/rubric/adjusters/ita2025f2q8.py`
**Responsabilidade:** ajustador de rubrica por student_claim_checks. Evidência: `app/confia_lean_auditor/rubric/adjusters/ita2025f2q8.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 75 de 203 — `app/confia_lean_auditor/rubric/adjusters/registry.py`
**Responsabilidade:** ajustador de rubrica por student_claim_checks. Evidência: `app/confia_lean_auditor/rubric/adjusters/registry.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 76 de 203 — `app/confia_lean_auditor/rubric/rubric_evaluator.py`
**Responsabilidade:** avaliador de rubrica por claims e microclaims. Evidência: `app/confia_lean_auditor/rubric/rubric_evaluator.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 77 de 203 — `app/confia_lean_auditor/student_claims/__init__.py`
**Responsabilidade:** schema, extrator ou registry de student claims. Evidência: `app/confia_lean_auditor/main.py:23`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 78 de 203 — `app/confia_lean_auditor/student_claims/extract_f2q1_student_claims.py`
**Responsabilidade:** schema, extrator ou registry de student claims. Evidência: `app/confia_lean_auditor/student_claims/extract_f2q1_student_claims.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 79 de 203 — `app/confia_lean_auditor/student_claims/extract_f2q3_student_claims.py`
**Responsabilidade:** schema, extrator ou registry de student claims. Evidência: `app/confia_lean_auditor/student_claims/extract_f2q3_student_claims.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 80 de 203 — `app/confia_lean_auditor/student_claims/extract_f2q5_student_claims.py`
**Responsabilidade:** schema, extrator ou registry de student claims. Evidência: `app/confia_lean_auditor/student_claims/extract_f2q5_student_claims.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 81 de 203 — `app/confia_lean_auditor/student_claims/extract_f2q6_student_claims.py`
**Responsabilidade:** schema, extrator ou registry de student claims. Evidência: `app/confia_lean_auditor/student_claims/extract_f2q6_student_claims.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 82 de 203 — `app/confia_lean_auditor/student_claims/extract_f2q8_student_claims.py`
**Responsabilidade:** schema, extrator ou registry de student claims. Evidência: `app/confia_lean_auditor/student_claims/extract_f2q8_student_claims.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 83 de 203 — `app/confia_lean_auditor/student_claims/registry.py`
**Responsabilidade:** schema, extrator ou registry de student claims. Evidência: `app/confia_lean_auditor/student_claims/registry.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 84 de 203 — `app/confia_lean_auditor/student_claims/schemas.py`
**Responsabilidade:** schema, extrator ou registry de student claims. Evidência: `app/confia_lean_auditor/student_claims/schemas.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 85 de 203 — `benchmarks/f2_suite_level1_2/gerar_tabelas_level1_f2_suite.py`
**Responsabilidade:** script de geração, execução ou relatório de benchmark. Evidência: `benchmarks/f2_suite_level1_2/gerar_tabelas_level1_f2_suite.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** script escreve relatórios em diretórios ignorados, portanto é harness auxiliar e não runtime HTTP.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 86 de 203 — `benchmarks/f2_suite_level1_2/gold_500.csv`
**Responsabilidade:** massa gold/resultado de benchmark em CSV. Evidência: `benchmarks/f2_suite_level1_2/gold_500.csv:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 87 de 203 — `benchmarks/f2_suite_level1_2/make_gold_500_f2_suite.py`
**Responsabilidade:** script de geração, execução ou relatório de benchmark. Evidência: `benchmarks/f2_suite_level1_2/make_gold_500_f2_suite.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** script escreve relatórios em diretórios ignorados, portanto é harness auxiliar e não runtime HTTP.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 88 de 203 — `benchmarks/f2_suite_level1_2/reports/RELATORIO_TECNICO_LEVEL1_F2_SUITE.md`
**Responsabilidade:** documentação técnica. Evidência: `benchmarks/f2_suite_level1_2/reports/RELATORIO_TECNICO_LEVEL1_F2_SUITE.md:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 89 de 203 — `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py`
**Responsabilidade:** script de geração, execução ou relatório de benchmark. Evidência: `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** script escreve relatórios em diretórios ignorados, portanto é harness auxiliar e não runtime HTTP.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 90 de 203 — `benchmarks/stage1_4/ita2025f2q8/gerar_relatorio_completo_benchmark_f2q8.py`
**Responsabilidade:** script de geração, execução ou relatório de benchmark. Evidência: `benchmarks/stage1_4/ita2025f2q8/gerar_relatorio_completo_benchmark_f2q8.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** script escreve relatórios em diretórios ignorados, portanto é harness auxiliar e não runtime HTTP.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 91 de 203 — `benchmarks/stage1_4/ita2025f2q8/gerar_relatorio_detalhado_sem_resumo_f2q8.py`
**Responsabilidade:** script de geração, execução ou relatório de benchmark. Evidência: `benchmarks/stage1_4/ita2025f2q8/gerar_relatorio_detalhado_sem_resumo_f2q8.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** script escreve relatórios em diretórios ignorados, portanto é harness auxiliar e não runtime HTTP.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 92 de 203 — `benchmarks/stage1_4/ita2025f2q8/gold_100.csv`
**Responsabilidade:** massa gold/resultado de benchmark em CSV. Evidência: `benchmarks/stage1_4/ita2025f2q8/gold_100.csv:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 93 de 203 — `benchmarks/stage1_4/ita2025f2q8/make_gold_100_f2q8.py`
**Responsabilidade:** script de geração, execução ou relatório de benchmark. Evidência: `benchmarks/stage1_4/ita2025f2q8/make_gold_100_f2q8.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** script escreve relatórios em diretórios ignorados, portanto é harness auxiliar e não runtime HTTP.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 94 de 203 — `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py`
**Responsabilidade:** script de geração, execução ou relatório de benchmark. Evidência: `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** script escreve relatórios em diretórios ignorados, portanto é harness auxiliar e não runtime HTTP.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 95 de 203 — `docs/lean_security_whitelist.md`
**Responsabilidade:** documentação técnica. Evidência: `docs/lean_security_whitelist.md:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 96 de 203 — `lake-manifest.json`
**Responsabilidade:** manifesto Lean/Lake ou toolchain. Evidência: `lake-manifest.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 97 de 203 — `lakefile.toml`
**Responsabilidade:** manifesto Lean/Lake ou toolchain. Evidência: `lakefile.toml:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 98 de 203 — `lean-toolchain`
**Responsabilidade:** manifesto Lean/Lake ou toolchain. Evidência: `lean-toolchain:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 99 de 203 — `problems/ITA2025F2Q1/examples/answer_only.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q1/examples/answer_only.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 100 de 203 — `problems/ITA2025F2Q1/examples/correct_solution.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q1/examples/correct_solution.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 101 de 203 — `problems/ITA2025F2Q1/examples/missing_reduced_form.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q1/examples/missing_reduced_form.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 102 de 203 — `problems/ITA2025F2Q1/examples/wrong_answer.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q1/examples/wrong_answer.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 103 de 203 — `problems/ITA2025F2Q1/microclaims.json`
**Responsabilidade:** contrato JSON de microclaims e dependências. Evidência: `problems/ITA2025F2Q1/microclaims.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 104 de 203 — `problems/ITA2025F2Q1/problem.json`
**Responsabilidade:** contrato JSON de enunciado e resposta esperada. Evidência: `problems/ITA2025F2Q1/problem.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 105 de 203 — `problems/ITA2025F2Q1/rubric.json`
**Responsabilidade:** contrato JSON de rubrica pontuada. Evidência: `problems/ITA2025F2Q1/rubric.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 106 de 203 — `problems/ITA2025F2Q3/examples/answer_only.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q3/examples/answer_only.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 107 de 203 — `problems/ITA2025F2Q3/examples/correct_solution.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q3/examples/correct_solution.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 108 de 203 — `problems/ITA2025F2Q3/examples/partial_beta_difference.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q3/examples/partial_beta_difference.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 109 de 203 — `problems/ITA2025F2Q3/examples/wrong_answer.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q3/examples/wrong_answer.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 110 de 203 — `problems/ITA2025F2Q3/microclaims.json`
**Responsabilidade:** contrato JSON de microclaims e dependências. Evidência: `problems/ITA2025F2Q3/microclaims.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 111 de 203 — `problems/ITA2025F2Q3/problem.json`
**Responsabilidade:** contrato JSON de enunciado e resposta esperada. Evidência: `problems/ITA2025F2Q3/problem.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 112 de 203 — `problems/ITA2025F2Q3/rubric.json`
**Responsabilidade:** contrato JSON de rubrica pontuada. Evidência: `problems/ITA2025F2Q3/rubric.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 113 de 203 — `problems/ITA2025F2Q5/examples/answer_only.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q5/examples/answer_only.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 114 de 203 — `problems/ITA2025F2Q5/examples/correct_solution.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q5/examples/correct_solution.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 115 de 203 — `problems/ITA2025F2Q5/examples/missing_bounds.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q5/examples/missing_bounds.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 116 de 203 — `problems/ITA2025F2Q5/examples/wrong_digit.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q5/examples/wrong_digit.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 117 de 203 — `problems/ITA2025F2Q5/microclaims.json`
**Responsabilidade:** contrato JSON de microclaims e dependências. Evidência: `problems/ITA2025F2Q5/microclaims.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 118 de 203 — `problems/ITA2025F2Q5/problem.json`
**Responsabilidade:** contrato JSON de enunciado e resposta esperada. Evidência: `problems/ITA2025F2Q5/problem.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 119 de 203 — `problems/ITA2025F2Q5/rubric.json`
**Responsabilidade:** contrato JSON de rubrica pontuada. Evidência: `problems/ITA2025F2Q5/rubric.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 120 de 203 — `problems/ITA2025F2Q6/examples/answer_only.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q6/examples/answer_only.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 121 de 203 — `problems/ITA2025F2Q6/examples/correct_solution.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q6/examples/correct_solution.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 122 de 203 — `problems/ITA2025F2Q6/examples/missing_ratio.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q6/examples/missing_ratio.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 123 de 203 — `problems/ITA2025F2Q6/examples/wrong_answer.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q6/examples/wrong_answer.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 124 de 203 — `problems/ITA2025F2Q6/microclaims.json`
**Responsabilidade:** contrato JSON de microclaims e dependências. Evidência: `problems/ITA2025F2Q6/microclaims.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 125 de 203 — `problems/ITA2025F2Q6/problem.json`
**Responsabilidade:** contrato JSON de enunciado e resposta esperada. Evidência: `problems/ITA2025F2Q6/problem.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 126 de 203 — `problems/ITA2025F2Q6/rubric.json`
**Responsabilidade:** contrato JSON de rubrica pontuada. Evidência: `problems/ITA2025F2Q6/rubric.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 127 de 203 — `problems/ITA2025F2Q8/examples/answer_only.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q8/examples/answer_only.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 128 de 203 — `problems/ITA2025F2Q8/examples/correct_solution.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q8/examples/correct_solution.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 129 de 203 — `problems/ITA2025F2Q8/examples/missing_determinant_formula.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q8/examples/missing_determinant_formula.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 130 de 203 — `problems/ITA2025F2Q8/examples/wrong_answer.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025F2Q8/examples/wrong_answer.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 131 de 203 — `problems/ITA2025F2Q8/microclaims.json`
**Responsabilidade:** contrato JSON de microclaims e dependências. Evidência: `problems/ITA2025F2Q8/microclaims.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 132 de 203 — `problems/ITA2025F2Q8/problem.json`
**Responsabilidade:** contrato JSON de enunciado e resposta esperada. Evidência: `problems/ITA2025F2Q8/problem.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 133 de 203 — `problems/ITA2025F2Q8/rubric.json`
**Responsabilidade:** contrato JSON de rubrica pontuada. Evidência: `problems/ITA2025F2Q8/rubric.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 134 de 203 — `problems/ITA2025Q1/certificate/Statement.lean`
**Responsabilidade:** arquivo versionado do projeto. Evidência: `problems/ITA2025Q1/certificate/Statement.lean:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 135 de 203 — `problems/ITA2025Q1/examples/answer_only.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q1/examples/answer_only.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 136 de 203 — `problems/ITA2025Q1/examples/correct_solution.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q1/examples/correct_solution.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 137 de 203 — `problems/ITA2025Q1/examples/injection_attempt.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q1/examples/injection_attempt.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 138 de 203 — `problems/ITA2025Q1/examples/partial_no_positive_root.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q1/examples/partial_no_positive_root.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 139 de 203 — `problems/ITA2025Q1/examples/wrong_determinant_step.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q1/examples/wrong_determinant_step.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 140 de 203 — `problems/ITA2025Q1/examples/wrong_solution.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q1/examples/wrong_solution.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 141 de 203 — `problems/ITA2025Q1/microclaims.json`
**Responsabilidade:** contrato JSON de microclaims e dependências. Evidência: `problems/ITA2025Q1/microclaims.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 142 de 203 — `problems/ITA2025Q1/problem.json`
**Responsabilidade:** contrato JSON de enunciado e resposta esperada. Evidência: `problems/ITA2025Q1/problem.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 143 de 203 — `problems/ITA2025Q1/rubric.json`
**Responsabilidade:** contrato JSON de rubrica pontuada. Evidência: `problems/ITA2025Q1/rubric.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 144 de 203 — `problems/ITA2025Q3/examples/answer_only.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q3/examples/answer_only.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 145 de 203 — `problems/ITA2025Q3/examples/correct_solution.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q3/examples/correct_solution.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 146 de 203 — `problems/ITA2025Q3/examples/missing_parity.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q3/examples/missing_parity.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 147 de 203 — `problems/ITA2025Q3/examples/wrong_coefficient.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q3/examples/wrong_coefficient.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 148 de 203 — `problems/ITA2025Q3/microclaims.json`
**Responsabilidade:** contrato JSON de microclaims e dependências. Evidência: `problems/ITA2025Q3/microclaims.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 149 de 203 — `problems/ITA2025Q3/problem.json`
**Responsabilidade:** contrato JSON de enunciado e resposta esperada. Evidência: `problems/ITA2025Q3/problem.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 150 de 203 — `problems/ITA2025Q3/rubric.json`
**Responsabilidade:** contrato JSON de rubrica pontuada. Evidência: `problems/ITA2025Q3/rubric.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 151 de 203 — `problems/ITA2025Q4/examples/answer_only.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q4/examples/answer_only.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 152 de 203 — `problems/ITA2025Q4/examples/correct_solution.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q4/examples/correct_solution.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 153 de 203 — `problems/ITA2025Q4/examples/missing_distinct_inputs.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q4/examples/missing_distinct_inputs.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 154 de 203 — `problems/ITA2025Q4/examples/wrong_target.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q4/examples/wrong_target.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 155 de 203 — `problems/ITA2025Q4/examples/wrong_witnesses.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q4/examples/wrong_witnesses.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 156 de 203 — `problems/ITA2025Q4/microclaims.json`
**Responsabilidade:** contrato JSON de microclaims e dependências. Evidência: `problems/ITA2025Q4/microclaims.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 157 de 203 — `problems/ITA2025Q4/problem.json`
**Responsabilidade:** contrato JSON de enunciado e resposta esperada. Evidência: `problems/ITA2025Q4/problem.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 158 de 203 — `problems/ITA2025Q4/rubric.json`
**Responsabilidade:** contrato JSON de rubrica pontuada. Evidência: `problems/ITA2025Q4/rubric.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 159 de 203 — `problems/ITA2025Q5/examples/answer_only.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q5/examples/answer_only.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 160 de 203 — `problems/ITA2025Q5/examples/correct_solution.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q5/examples/correct_solution.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 161 de 203 — `problems/ITA2025Q5/examples/missing_difference_relation.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q5/examples/missing_difference_relation.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 162 de 203 — `problems/ITA2025Q5/examples/missing_factorization.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q5/examples/missing_factorization.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 163 de 203 — `problems/ITA2025Q5/examples/wrong_direction.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q5/examples/wrong_direction.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 164 de 203 — `problems/ITA2025Q5/microclaims.json`
**Responsabilidade:** contrato JSON de microclaims e dependências. Evidência: `problems/ITA2025Q5/microclaims.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 165 de 203 — `problems/ITA2025Q5/problem.json`
**Responsabilidade:** contrato JSON de enunciado e resposta esperada. Evidência: `problems/ITA2025Q5/problem.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 166 de 203 — `problems/ITA2025Q5/rubric.json`
**Responsabilidade:** contrato JSON de rubrica pontuada. Evidência: `problems/ITA2025Q5/rubric.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 167 de 203 — `problems/ITA2025Q8/examples/answer_only.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q8/examples/answer_only.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 168 de 203 — `problems/ITA2025Q8/examples/correct_solution.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q8/examples/correct_solution.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 169 de 203 — `problems/ITA2025Q8/examples/missing_sign_analysis.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q8/examples/missing_sign_analysis.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 170 de 203 — `problems/ITA2025Q8/examples/wrong_interval.txt`
**Responsabilidade:** fixture textual de solução. Evidência: `problems/ITA2025Q8/examples/wrong_interval.txt:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** BAIXO.
<file-analyzed/>
#### Analisado 171 de 203 — `problems/ITA2025Q8/microclaims.json`
**Responsabilidade:** contrato JSON de microclaims e dependências. Evidência: `problems/ITA2025Q8/microclaims.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 172 de 203 — `problems/ITA2025Q8/problem.json`
**Responsabilidade:** contrato JSON de enunciado e resposta esperada. Evidência: `problems/ITA2025Q8/problem.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 173 de 203 — `problems/ITA2025Q8/rubric.json`
**Responsabilidade:** contrato JSON de rubrica pontuada. Evidência: `problems/ITA2025Q8/rubric.json:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** ALTO.
<file-analyzed/>
#### Analisado 174 de 203 — `pyproject.toml`
**Responsabilidade:** manifesto Python do pacote e dependências. Evidência: `pyproject.toml:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 175 de 203 — `tests/test_evaluator_architecture.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_evaluator_architecture.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 176 de 203 — `tests/test_f2q1_rubric_adjustments.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q1_rubric_adjustments.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 177 de 203 — `tests/test_f2q1_strong_certificate.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q1_strong_certificate.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 178 de 203 — `tests/test_f2q1_student_claim_checks.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q1_student_claim_checks.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 179 de 203 — `tests/test_f2q3_rubric_adjustments.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q3_rubric_adjustments.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 180 de 203 — `tests/test_f2q3_strong_certificate.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q3_strong_certificate.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 181 de 203 — `tests/test_f2q3_student_claim_checks.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q3_student_claim_checks.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 182 de 203 — `tests/test_f2q5_rubric_adjustments.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q5_rubric_adjustments.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 183 de 203 — `tests/test_f2q5_strong_certificate.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q5_strong_certificate.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 184 de 203 — `tests/test_f2q5_student_claim_checks.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q5_student_claim_checks.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 185 de 203 — `tests/test_f2q6_rubric_adjustments.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q6_rubric_adjustments.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 186 de 203 — `tests/test_f2q6_strong_certificate.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q6_strong_certificate.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 187 de 203 — `tests/test_f2q6_student_claim_checks.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q6_student_claim_checks.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 188 de 203 — `tests/test_f2q8_student_claim_checks.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_f2q8_student_claim_checks.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 189 de 203 — `tests/test_ita2025f2q1_level1.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_ita2025f2q1_level1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 190 de 203 — `tests/test_ita2025f2q3_level1.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_ita2025f2q3_level1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 191 de 203 — `tests/test_ita2025f2q5_level1.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_ita2025f2q5_level1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 192 de 203 — `tests/test_ita2025f2q6_level1.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_ita2025f2q6_level1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 193 de 203 — `tests/test_ita2025f2q8_level1.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_ita2025f2q8_level1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 194 de 203 — `tests/test_ita2025q1_level2.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_ita2025q1_level2.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 195 de 203 — `tests/test_ita2025q3_level1.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_ita2025q3_level1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 196 de 203 — `tests/test_ita2025q4_level1.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_ita2025q4_level1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 197 de 203 — `tests/test_ita2025q4_level2.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_ita2025q4_level2.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 198 de 203 — `tests/test_ita2025q5_level1.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_ita2025q5_level1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 199 de 203 — `tests/test_ita2025q8_level1.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_ita2025q8_level1.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 200 de 203 — `tests/test_level1_f2_suite_regressions.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_level1_f2_suite_regressions.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 201 de 203 — `tests/test_problem_assets_contracts.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_problem_assets_contracts.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 202 de 203 — `tests/test_problem_assets_validation.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_problem_assets_validation.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>
#### Analisado 203 de 203 — `tests/test_problem_router_coverage.py`
**Responsabilidade:** teste pytest de API, contratos, regressão ou verificação Lean. Evidência: `tests/test_problem_router_coverage.py:1`.
**Fluxo de dados:** participa do fluxo descrito nas seções 2 a 4 quando importado, executado por CLI/CI/teste ou lido por filesystem; quando é fixture/documento, atua como entrada de teste, benchmark ou referência documental.
**Entradas/saídas:** entradas e saídas consolidadas aparecem na seção 4; arquivos de problema entram via `validate_problem_assets`, scripts de benchmark entram por CSV/CLI, e módulos runtime entram pela rota `/audit`.
**Anti-padrões e smells:** sem smell isolado confirmado além dos transversais citados nas seções 6 e 9.
**Risco de refatoração:** MÉDIO.
<file-analyzed/>

## 6. Preocupações transversais

Roteamento paralelo por problema ocorre em três planos obrigatórios: extração em `app/confia_lean_auditor/claims/extract_claims.py:41` a `app/confia_lean_auditor/claims/extract_claims.py:75`, builders em `app/confia_lean_auditor/lean/build_attempt.py:44` a `app/confia_lean_auditor/lean/build_attempt.py:123`, e renderização de formal steps em `app/confia_lean_auditor/lean/formal_step_evaluator.py:411` a `app/confia_lean_auditor/lean/formal_step_evaluator.py:441`. Para a família F2 há ainda três planos adicionais: extração de student claims em `app/confia_lean_auditor/student_claims/registry.py:23` a `app/confia_lean_auditor/student_claims/registry.py:39`, verificação Lean dessas claims em `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:23` a `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:62`, e ajuste de rubrica em `app/confia_lean_auditor/rubric/adjusters/registry.py:26` a `app/confia_lean_auditor/rubric/adjusters/registry.py:45`.

Configuração e ambiente: `CONFIA_LEAN_AUDITOR_ROOT` altera a raiz em `app/confia_lean_auditor/core/paths.py:15` a `app/confia_lean_auditor/core/paths.py:22`; `CONFIA_ENABLE_LLM_FORMAL_STEPS` ativa LLM em `app/confia_lean_auditor/llm/formal_step_extractor.py:52` a `app/confia_lean_auditor/llm/formal_step_extractor.py:53`; `CONFIA_LLM_MODEL` escolhe modelo em `app/confia_lean_auditor/llm/formal_step_extractor.py:238`; CI desativa LLM com `CONFIA_ENABLE_LLM_FORMAL_STEPS: "0"` em `.github/workflows/python_tests.yml:11` a `.github/workflows/python_tests.yml:12` e `.github/workflows/lean_action_ci.yml:11` a `.github/workflows/lean_action_ci.yml:12`; `.env` é ignorado em `.gitignore:13` a `.gitignore:14`.

Logging e diagnóstico: não há logger estruturado no app; o runner Lean retorna `stdout` e `stderr` em `app/confia_lean_auditor/lean/run_lean.py:90` a `app/confia_lean_auditor/lean/run_lean.py:98`, e esses campos entram em `LeanCertificate` em `app/confia_lean_auditor/core/schemas.py:76` a `app/confia_lean_auditor/core/schemas.py:85`. Student claims também preservam `stdout` e `stderr` em dataclass própria em `app/confia_lean_auditor/student_claims/schemas.py:54` a `app/confia_lean_auditor/student_claims/schemas.py:68`.

Segurança: `problem_id` é validado por regex em `app/confia_lean_auditor/core/paths.py:8` e confinado por `relative_to` em `app/confia_lean_auditor/core/paths.py:34` a `app/confia_lean_auditor/core/paths.py:45`; tokens Lean proibidos incluem `sorry`, `admit`, `unsafe` e `axiom` em `app/confia_lean_auditor/lean/run_lean.py:13` a `app/confia_lean_auditor/lean/run_lean.py:18`; subprocess Lean usa timeout em `app/confia_lean_auditor/lean/run_lean.py:65` a `app/confia_lean_auditor/lean/run_lean.py:88`; formal steps são validados antes da escrita em `app/confia_lean_auditor/lean/formal_step_evaluator.py:455` a `app/confia_lean_auditor/lean/formal_step_evaluator.py:493`. Autenticação, autorização, rate-limit e CORS não aparecem na criação simples de `FastAPI` em `app/confia_lean_auditor/main.py:8` a `app/confia_lean_auditor/main.py:26`.

Testes e efeitos colaterais: os testes de API usam `TestClient` e podem acionar a escrita de artefatos pela rota `/audit`, pois `main.py` sempre cria `artifact_dir` em `app/confia_lean_auditor/main.py:59` a `app/confia_lean_auditor/main.py:61`; os testes de assets alteram cópias temporárias via `tmp_path`, não a árvore original, em `tests/test_problem_assets_validation.py:14` a `tests/test_problem_assets_validation.py:55`; os testes de router são textuais e leem arquivos fonte em `tests/test_problem_router_coverage.py:34` a `tests/test_problem_router_coverage.py:58`. Não executei a suíte nesta auditoria para respeitar a restrição de não criar artefatos runtime; essa decisão é ancorada no comportamento de escrita de `app/confia_lean_auditor/main.py:159` a `app/confia_lean_auditor/main.py:178` e `app/confia_lean_auditor/lean/student_claim_checker.py:168` a `app/confia_lean_auditor/lean/student_claim_checker.py:193`.

## 7. Tabela de risco

| arquivo | risco | razão principal |
|---|---:|---|
| `.github/workflows/create-release.yml` | MÉDIO | workflow GitHub Actions de CI, release ou atualização; evidência `.github/workflows/create-release.yml:1`. |
| `.github/workflows/lean_action_ci.yml` | MÉDIO | workflow GitHub Actions de CI, release ou atualização; evidência `.github/workflows/lean_action_ci.yml:1`. |
| `.github/workflows/python_tests.yml` | MÉDIO | workflow GitHub Actions de CI, release ou atualização; evidência `.github/workflows/python_tests.yml:1`. |
| `.github/workflows/update.yml` | MÉDIO | workflow GitHub Actions de CI, release ou atualização; evidência `.github/workflows/update.yml:1`. |
| `.gitignore` | BAIXO | configuração de exclusões Git para ambientes, artefatos e caches; evidência `.gitignore:1`. |
| `AUDITORIA_REPOSITORIO.md` | BAIXO | documentação técnica; evidência `AUDITORIA_REPOSITORIO.md:1`. |
| `ConfiaLeanAuditor.lean` | BAIXO | módulo raiz Lean que agrega statements; evidência `ConfiaLeanAuditor.lean:1`. |
| `ConfiaLeanAuditor/Basic.lean` | BAIXO | scaffold Lean mínimo com definição hello; evidência `ConfiaLeanAuditor/Basic.lean:1`. |
| `ConfiaLeanAuditor/Problems/ITA2025F2Q1/Statement.lean` | ALTO | statement Lean de problema; evidência `ConfiaLeanAuditor/Problems/ITA2025F2Q1/Statement.lean:1`. |
| `ConfiaLeanAuditor/Problems/ITA2025F2Q3/Statement.lean` | ALTO | statement Lean de problema; evidência `ConfiaLeanAuditor/Problems/ITA2025F2Q3/Statement.lean:1`. |
| `ConfiaLeanAuditor/Problems/ITA2025F2Q5/Statement.lean` | ALTO | statement Lean de problema; evidência `ConfiaLeanAuditor/Problems/ITA2025F2Q5/Statement.lean:1`. |
| `ConfiaLeanAuditor/Problems/ITA2025F2Q6/Statement.lean` | ALTO | statement Lean de problema; evidência `ConfiaLeanAuditor/Problems/ITA2025F2Q6/Statement.lean:1`. |
| `ConfiaLeanAuditor/Problems/ITA2025F2Q8/Statement.lean` | ALTO | statement Lean de problema; evidência `ConfiaLeanAuditor/Problems/ITA2025F2Q8/Statement.lean:1`. |
| `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean` | ALTO | statement Lean de problema; evidência `ConfiaLeanAuditor/Problems/ITA2025Q1/Statement.lean:1`. |
| `ConfiaLeanAuditor/Problems/ITA2025Q3/Statement.lean` | ALTO | statement Lean de problema; evidência `ConfiaLeanAuditor/Problems/ITA2025Q3/Statement.lean:1`. |
| `ConfiaLeanAuditor/Problems/ITA2025Q4/Statement.lean` | ALTO | statement Lean de problema; evidência `ConfiaLeanAuditor/Problems/ITA2025Q4/Statement.lean:1`. |
| `ConfiaLeanAuditor/Problems/ITA2025Q5/Statement.lean` | ALTO | statement Lean de problema; evidência `ConfiaLeanAuditor/Problems/ITA2025Q5/Statement.lean:1`. |
| `ConfiaLeanAuditor/Problems/ITA2025Q8/Statement.lean` | ALTO | statement Lean de problema; evidência `ConfiaLeanAuditor/Problems/ITA2025Q8/Statement.lean:1`. |
| `MILESTONE_ITA2025F2.md` | BAIXO | documentação técnica; evidência `MILESTONE_ITA2025F2.md:1`. |
| `README.md` | BAIXO | documentação técnica; evidência `README.md:1`. |
| `app/confia_lean_auditor/__init__.py` | BAIXO | marcador de pacote Python; evidência `app/confia_lean_auditor/main.py:10`. |
| `app/confia_lean_auditor/claims/__init__.py` | BAIXO | marcador de pacote Python; evidência `app/confia_lean_auditor/main.py:10`. |
| `app/confia_lean_auditor/claims/extract_claims.py` | BAIXO | dispatcher de extração por problem_id; evidência `app/confia_lean_auditor/claims/extract_claims.py:1`. |
| `app/confia_lean_auditor/claims/extractors/__init__.py` | ALTO | extrator heurístico de claims por problema; evidência `app/confia_lean_auditor/claims/extract_claims.py:4`. |
| `app/confia_lean_auditor/claims/extractors/ita2025f2q1.py` | ALTO | extrator heurístico de claims por problema; evidência `app/confia_lean_auditor/claims/extractors/ita2025f2q1.py:1`. |
| `app/confia_lean_auditor/claims/extractors/ita2025f2q3.py` | ALTO | extrator heurístico de claims por problema; evidência `app/confia_lean_auditor/claims/extractors/ita2025f2q3.py:1`. |
| `app/confia_lean_auditor/claims/extractors/ita2025f2q5.py` | ALTO | extrator heurístico de claims por problema; evidência `app/confia_lean_auditor/claims/extractors/ita2025f2q5.py:1`. |
| `app/confia_lean_auditor/claims/extractors/ita2025f2q6.py` | ALTO | extrator heurístico de claims por problema; evidência `app/confia_lean_auditor/claims/extractors/ita2025f2q6.py:1`. |
| `app/confia_lean_auditor/claims/extractors/ita2025f2q8.py` | ALTO | extrator heurístico de claims por problema; evidência `app/confia_lean_auditor/claims/extractors/ita2025f2q8.py:1`. |
| `app/confia_lean_auditor/claims/extractors/ita2025q1.py` | ALTO | extrator heurístico de claims por problema; evidência `app/confia_lean_auditor/claims/extractors/ita2025q1.py:1`. |
| `app/confia_lean_auditor/claims/extractors/ita2025q3.py` | ALTO | extrator heurístico de claims por problema; evidência `app/confia_lean_auditor/claims/extractors/ita2025q3.py:1`. |
| `app/confia_lean_auditor/claims/extractors/ita2025q4.py` | ALTO | extrator heurístico de claims por problema; evidência `app/confia_lean_auditor/claims/extractors/ita2025q4.py:1`. |
| `app/confia_lean_auditor/claims/extractors/ita2025q5.py` | ALTO | extrator heurístico de claims por problema; evidência `app/confia_lean_auditor/claims/extractors/ita2025q5.py:1`. |
| `app/confia_lean_auditor/claims/extractors/ita2025q8.py` | ALTO | extrator heurístico de claims por problema; evidência `app/confia_lean_auditor/claims/extractors/ita2025q8.py:1`. |
| `app/confia_lean_auditor/core/__init__.py` | BAIXO | marcador de pacote Python; evidência `app/confia_lean_auditor/main.py:11`. |
| `app/confia_lean_auditor/core/paths.py` | BAIXO | resolução de raiz e problem_id; evidência `app/confia_lean_auditor/core/paths.py:1`. |
| `app/confia_lean_auditor/core/problem_assets.py` | ALTO | validação de assets de problema; evidência `app/confia_lean_auditor/core/problem_assets.py:1`. |
| `app/confia_lean_auditor/core/schemas.py` | ALTO | schemas Pydantic ou dataclasses de contratos internos; evidência `app/confia_lean_auditor/core/schemas.py:1`. |
| `app/confia_lean_auditor/lean/__init__.py` | BAIXO | marcador de pacote Python; evidência `app/confia_lean_auditor/main.py:14`. |
| `app/confia_lean_auditor/lean/attempt_builders/__init__.py` | BAIXO | builder de Attempt.lean por problema; evidência `app/confia_lean_auditor/lean/build_attempt.py:7`. |
| `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q1.py` | ALTO | builder de Attempt.lean por problema; evidência `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q1.py:1`. |
| `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q3.py` | ALTO | builder de Attempt.lean por problema; evidência `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q3.py:1`. |
| `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q5.py` | ALTO | builder de Attempt.lean por problema; evidência `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q5.py:1`. |
| `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q6.py` | ALTO | builder de Attempt.lean por problema; evidência `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q6.py:1`. |
| `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q8.py` | ALTO | builder de Attempt.lean por problema; evidência `app/confia_lean_auditor/lean/attempt_builders/ita2025f2q8.py:1`. |
| `app/confia_lean_auditor/lean/attempt_builders/ita2025q1.py` | ALTO | builder de Attempt.lean por problema; evidência `app/confia_lean_auditor/lean/attempt_builders/ita2025q1.py:1`. |
| `app/confia_lean_auditor/lean/attempt_builders/ita2025q3.py` | ALTO | builder de Attempt.lean por problema; evidência `app/confia_lean_auditor/lean/attempt_builders/ita2025q3.py:1`. |
| `app/confia_lean_auditor/lean/attempt_builders/ita2025q4.py` | ALTO | builder de Attempt.lean por problema; evidência `app/confia_lean_auditor/lean/attempt_builders/ita2025q4.py:1`. |
| `app/confia_lean_auditor/lean/attempt_builders/ita2025q5.py` | ALTO | builder de Attempt.lean por problema; evidência `app/confia_lean_auditor/lean/attempt_builders/ita2025q5.py:1`. |
| `app/confia_lean_auditor/lean/attempt_builders/ita2025q8.py` | ALTO | builder de Attempt.lean por problema; evidência `app/confia_lean_auditor/lean/attempt_builders/ita2025q8.py:1`. |
| `app/confia_lean_auditor/lean/build_attempt.py` | ALTO | dispatcher de builders Lean por problem_id; evidência `app/confia_lean_auditor/lean/build_attempt.py:1`. |
| `app/confia_lean_auditor/lean/formal_step_evaluator.py` | ALTO | renderizador e avaliador de formal steps Lean; evidência `app/confia_lean_auditor/lean/formal_step_evaluator.py:1`. |
| `app/confia_lean_auditor/lean/microclaim_evaluator.py` | ALTO | avaliador de microclaims; evidência `app/confia_lean_auditor/lean/microclaim_evaluator.py:1`. |
| `app/confia_lean_auditor/lean/run_lean.py` | ALTO | runner Lean e CLI por subprocess; evidência `app/confia_lean_auditor/lean/run_lean.py:1`. |
| `app/confia_lean_auditor/lean/safe_formal_step.py` | ALTO | arquivo versionado do projeto; evidência `app/confia_lean_auditor/lean/safe_formal_step.py:1`. |
| `app/confia_lean_auditor/lean/student_claim_checker.py` | ALTO | verificador Lean legado de student claims F2Q8; evidência `app/confia_lean_auditor/lean/student_claim_checker.py:1`. |
| `app/confia_lean_auditor/lean/student_claim_checkers/__init__.py` | BAIXO | verificador Lean de student claims por problema F2; evidência `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:9`. |
| `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q1.py` | ALTO | verificador Lean de student claims por problema F2; evidência `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q1.py:1`. |
| `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q3.py` | ALTO | verificador Lean de student claims por problema F2; evidência `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q3.py:1`. |
| `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q5.py` | ALTO | verificador Lean de student claims por problema F2; evidência `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q5.py:1`. |
| `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q6.py` | ALTO | verificador Lean de student claims por problema F2; evidência `app/confia_lean_auditor/lean/student_claim_checkers/ita2025f2q6.py:1`. |
| `app/confia_lean_auditor/lean/student_claim_checkers/registry.py` | ALTO | verificador Lean de student claims por problema F2; evidência `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:1`. |
| `app/confia_lean_auditor/llm/__init__.py` | BAIXO | marcador de pacote Python; evidência `app/confia_lean_auditor/main.py:21`. |
| `app/confia_lean_auditor/llm/formal_step_extractor.py` | BAIXO | fallback opcional de extração por LLM; evidência `app/confia_lean_auditor/llm/formal_step_extractor.py:1`. |
| `app/confia_lean_auditor/main.py` | ALTO | API FastAPI e orquestrador ponta a ponta; evidência `app/confia_lean_auditor/main.py:1`. |
| `app/confia_lean_auditor/reports/__init__.py` | BAIXO | marcador de pacote Python; evidência `app/confia_lean_auditor/main.py:18`. |
| `app/confia_lean_auditor/reports/report_builder.py` | BAIXO | montagem de verdict e feedback textual; evidência `app/confia_lean_auditor/reports/report_builder.py:1`. |
| `app/confia_lean_auditor/rubric/__init__.py` | BAIXO | marcador de pacote Python; evidência `app/confia_lean_auditor/main.py:19`. |
| `app/confia_lean_auditor/rubric/adjusters/__init__.py` | BAIXO | ajustador de rubrica por student_claim_checks; evidência `app/confia_lean_auditor/rubric/adjusters/registry.py:6`. |
| `app/confia_lean_auditor/rubric/adjusters/ita2025f2q1.py` | BAIXO | ajustador de rubrica por student_claim_checks; evidência `app/confia_lean_auditor/rubric/adjusters/ita2025f2q1.py:1`. |
| `app/confia_lean_auditor/rubric/adjusters/ita2025f2q3.py` | BAIXO | ajustador de rubrica por student_claim_checks; evidência `app/confia_lean_auditor/rubric/adjusters/ita2025f2q3.py:1`. |
| `app/confia_lean_auditor/rubric/adjusters/ita2025f2q5.py` | BAIXO | ajustador de rubrica por student_claim_checks; evidência `app/confia_lean_auditor/rubric/adjusters/ita2025f2q5.py:1`. |
| `app/confia_lean_auditor/rubric/adjusters/ita2025f2q6.py` | BAIXO | ajustador de rubrica por student_claim_checks; evidência `app/confia_lean_auditor/rubric/adjusters/ita2025f2q6.py:1`. |
| `app/confia_lean_auditor/rubric/adjusters/ita2025f2q8.py` | BAIXO | ajustador de rubrica por student_claim_checks; evidência `app/confia_lean_auditor/rubric/adjusters/ita2025f2q8.py:1`. |
| `app/confia_lean_auditor/rubric/adjusters/registry.py` | BAIXO | ajustador de rubrica por student_claim_checks; evidência `app/confia_lean_auditor/rubric/adjusters/registry.py:1`. |
| `app/confia_lean_auditor/rubric/rubric_evaluator.py` | BAIXO | avaliador de rubrica por claims e microclaims; evidência `app/confia_lean_auditor/rubric/rubric_evaluator.py:1`. |
| `app/confia_lean_auditor/student_claims/__init__.py` | BAIXO | schema, extrator ou registry de student claims; evidência `app/confia_lean_auditor/main.py:23`. |
| `app/confia_lean_auditor/student_claims/extract_f2q1_student_claims.py` | BAIXO | schema, extrator ou registry de student claims; evidência `app/confia_lean_auditor/student_claims/extract_f2q1_student_claims.py:1`. |
| `app/confia_lean_auditor/student_claims/extract_f2q3_student_claims.py` | BAIXO | schema, extrator ou registry de student claims; evidência `app/confia_lean_auditor/student_claims/extract_f2q3_student_claims.py:1`. |
| `app/confia_lean_auditor/student_claims/extract_f2q5_student_claims.py` | BAIXO | schema, extrator ou registry de student claims; evidência `app/confia_lean_auditor/student_claims/extract_f2q5_student_claims.py:1`. |
| `app/confia_lean_auditor/student_claims/extract_f2q6_student_claims.py` | BAIXO | schema, extrator ou registry de student claims; evidência `app/confia_lean_auditor/student_claims/extract_f2q6_student_claims.py:1`. |
| `app/confia_lean_auditor/student_claims/extract_f2q8_student_claims.py` | BAIXO | schema, extrator ou registry de student claims; evidência `app/confia_lean_auditor/student_claims/extract_f2q8_student_claims.py:1`. |
| `app/confia_lean_auditor/student_claims/registry.py` | BAIXO | schema, extrator ou registry de student claims; evidência `app/confia_lean_auditor/student_claims/registry.py:1`. |
| `app/confia_lean_auditor/student_claims/schemas.py` | ALTO | schema, extrator ou registry de student claims; evidência `app/confia_lean_auditor/student_claims/schemas.py:1`. |
| `benchmarks/f2_suite_level1_2/gerar_tabelas_level1_f2_suite.py` | MÉDIO | script de geração, execução ou relatório de benchmark; evidência `benchmarks/f2_suite_level1_2/gerar_tabelas_level1_f2_suite.py:1`. |
| `benchmarks/f2_suite_level1_2/gold_500.csv` | MÉDIO | massa gold/resultado de benchmark em CSV; evidência `benchmarks/f2_suite_level1_2/gold_500.csv:1`. |
| `benchmarks/f2_suite_level1_2/make_gold_500_f2_suite.py` | MÉDIO | script de geração, execução ou relatório de benchmark; evidência `benchmarks/f2_suite_level1_2/make_gold_500_f2_suite.py:1`. |
| `benchmarks/f2_suite_level1_2/reports/RELATORIO_TECNICO_LEVEL1_F2_SUITE.md` | MÉDIO | documentação técnica; evidência `benchmarks/f2_suite_level1_2/reports/RELATORIO_TECNICO_LEVEL1_F2_SUITE.md:1`. |
| `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py` | MÉDIO | script de geração, execução ou relatório de benchmark; evidência `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py:1`. |
| `benchmarks/stage1_4/ita2025f2q8/gerar_relatorio_completo_benchmark_f2q8.py` | MÉDIO | script de geração, execução ou relatório de benchmark; evidência `benchmarks/stage1_4/ita2025f2q8/gerar_relatorio_completo_benchmark_f2q8.py:1`. |
| `benchmarks/stage1_4/ita2025f2q8/gerar_relatorio_detalhado_sem_resumo_f2q8.py` | MÉDIO | script de geração, execução ou relatório de benchmark; evidência `benchmarks/stage1_4/ita2025f2q8/gerar_relatorio_detalhado_sem_resumo_f2q8.py:1`. |
| `benchmarks/stage1_4/ita2025f2q8/gold_100.csv` | MÉDIO | massa gold/resultado de benchmark em CSV; evidência `benchmarks/stage1_4/ita2025f2q8/gold_100.csv:1`. |
| `benchmarks/stage1_4/ita2025f2q8/make_gold_100_f2q8.py` | MÉDIO | script de geração, execução ou relatório de benchmark; evidência `benchmarks/stage1_4/ita2025f2q8/make_gold_100_f2q8.py:1`. |
| `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py` | MÉDIO | script de geração, execução ou relatório de benchmark; evidência `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py:1`. |
| `docs/lean_security_whitelist.md` | BAIXO | documentação técnica; evidência `docs/lean_security_whitelist.md:1`. |
| `lake-manifest.json` | MÉDIO | manifesto Lean/Lake ou toolchain; evidência `lake-manifest.json:1`. |
| `lakefile.toml` | MÉDIO | manifesto Lean/Lake ou toolchain; evidência `lakefile.toml:1`. |
| `lean-toolchain` | MÉDIO | manifesto Lean/Lake ou toolchain; evidência `lean-toolchain:1`. |
| `problems/ITA2025F2Q1/examples/answer_only.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q1/examples/answer_only.txt:1`. |
| `problems/ITA2025F2Q1/examples/correct_solution.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q1/examples/correct_solution.txt:1`. |
| `problems/ITA2025F2Q1/examples/missing_reduced_form.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q1/examples/missing_reduced_form.txt:1`. |
| `problems/ITA2025F2Q1/examples/wrong_answer.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q1/examples/wrong_answer.txt:1`. |
| `problems/ITA2025F2Q1/microclaims.json` | ALTO | contrato JSON de microclaims e dependências; evidência `problems/ITA2025F2Q1/microclaims.json:1`. |
| `problems/ITA2025F2Q1/problem.json` | MÉDIO | contrato JSON de enunciado e resposta esperada; evidência `problems/ITA2025F2Q1/problem.json:1`. |
| `problems/ITA2025F2Q1/rubric.json` | ALTO | contrato JSON de rubrica pontuada; evidência `problems/ITA2025F2Q1/rubric.json:1`. |
| `problems/ITA2025F2Q3/examples/answer_only.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q3/examples/answer_only.txt:1`. |
| `problems/ITA2025F2Q3/examples/correct_solution.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q3/examples/correct_solution.txt:1`. |
| `problems/ITA2025F2Q3/examples/partial_beta_difference.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q3/examples/partial_beta_difference.txt:1`. |
| `problems/ITA2025F2Q3/examples/wrong_answer.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q3/examples/wrong_answer.txt:1`. |
| `problems/ITA2025F2Q3/microclaims.json` | ALTO | contrato JSON de microclaims e dependências; evidência `problems/ITA2025F2Q3/microclaims.json:1`. |
| `problems/ITA2025F2Q3/problem.json` | MÉDIO | contrato JSON de enunciado e resposta esperada; evidência `problems/ITA2025F2Q3/problem.json:1`. |
| `problems/ITA2025F2Q3/rubric.json` | ALTO | contrato JSON de rubrica pontuada; evidência `problems/ITA2025F2Q3/rubric.json:1`. |
| `problems/ITA2025F2Q5/examples/answer_only.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q5/examples/answer_only.txt:1`. |
| `problems/ITA2025F2Q5/examples/correct_solution.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q5/examples/correct_solution.txt:1`. |
| `problems/ITA2025F2Q5/examples/missing_bounds.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q5/examples/missing_bounds.txt:1`. |
| `problems/ITA2025F2Q5/examples/wrong_digit.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q5/examples/wrong_digit.txt:1`. |
| `problems/ITA2025F2Q5/microclaims.json` | ALTO | contrato JSON de microclaims e dependências; evidência `problems/ITA2025F2Q5/microclaims.json:1`. |
| `problems/ITA2025F2Q5/problem.json` | MÉDIO | contrato JSON de enunciado e resposta esperada; evidência `problems/ITA2025F2Q5/problem.json:1`. |
| `problems/ITA2025F2Q5/rubric.json` | ALTO | contrato JSON de rubrica pontuada; evidência `problems/ITA2025F2Q5/rubric.json:1`. |
| `problems/ITA2025F2Q6/examples/answer_only.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q6/examples/answer_only.txt:1`. |
| `problems/ITA2025F2Q6/examples/correct_solution.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q6/examples/correct_solution.txt:1`. |
| `problems/ITA2025F2Q6/examples/missing_ratio.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q6/examples/missing_ratio.txt:1`. |
| `problems/ITA2025F2Q6/examples/wrong_answer.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q6/examples/wrong_answer.txt:1`. |
| `problems/ITA2025F2Q6/microclaims.json` | ALTO | contrato JSON de microclaims e dependências; evidência `problems/ITA2025F2Q6/microclaims.json:1`. |
| `problems/ITA2025F2Q6/problem.json` | MÉDIO | contrato JSON de enunciado e resposta esperada; evidência `problems/ITA2025F2Q6/problem.json:1`. |
| `problems/ITA2025F2Q6/rubric.json` | ALTO | contrato JSON de rubrica pontuada; evidência `problems/ITA2025F2Q6/rubric.json:1`. |
| `problems/ITA2025F2Q8/examples/answer_only.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q8/examples/answer_only.txt:1`. |
| `problems/ITA2025F2Q8/examples/correct_solution.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q8/examples/correct_solution.txt:1`. |
| `problems/ITA2025F2Q8/examples/missing_determinant_formula.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q8/examples/missing_determinant_formula.txt:1`. |
| `problems/ITA2025F2Q8/examples/wrong_answer.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025F2Q8/examples/wrong_answer.txt:1`. |
| `problems/ITA2025F2Q8/microclaims.json` | ALTO | contrato JSON de microclaims e dependências; evidência `problems/ITA2025F2Q8/microclaims.json:1`. |
| `problems/ITA2025F2Q8/problem.json` | MÉDIO | contrato JSON de enunciado e resposta esperada; evidência `problems/ITA2025F2Q8/problem.json:1`. |
| `problems/ITA2025F2Q8/rubric.json` | ALTO | contrato JSON de rubrica pontuada; evidência `problems/ITA2025F2Q8/rubric.json:1`. |
| `problems/ITA2025Q1/certificate/Statement.lean` | BAIXO | arquivo versionado do projeto; evidência `problems/ITA2025Q1/certificate/Statement.lean:1`. |
| `problems/ITA2025Q1/examples/answer_only.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q1/examples/answer_only.txt:1`. |
| `problems/ITA2025Q1/examples/correct_solution.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q1/examples/correct_solution.txt:1`. |
| `problems/ITA2025Q1/examples/injection_attempt.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q1/examples/injection_attempt.txt:1`. |
| `problems/ITA2025Q1/examples/partial_no_positive_root.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q1/examples/partial_no_positive_root.txt:1`. |
| `problems/ITA2025Q1/examples/wrong_determinant_step.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q1/examples/wrong_determinant_step.txt:1`. |
| `problems/ITA2025Q1/examples/wrong_solution.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q1/examples/wrong_solution.txt:1`. |
| `problems/ITA2025Q1/microclaims.json` | ALTO | contrato JSON de microclaims e dependências; evidência `problems/ITA2025Q1/microclaims.json:1`. |
| `problems/ITA2025Q1/problem.json` | MÉDIO | contrato JSON de enunciado e resposta esperada; evidência `problems/ITA2025Q1/problem.json:1`. |
| `problems/ITA2025Q1/rubric.json` | ALTO | contrato JSON de rubrica pontuada; evidência `problems/ITA2025Q1/rubric.json:1`. |
| `problems/ITA2025Q3/examples/answer_only.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q3/examples/answer_only.txt:1`. |
| `problems/ITA2025Q3/examples/correct_solution.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q3/examples/correct_solution.txt:1`. |
| `problems/ITA2025Q3/examples/missing_parity.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q3/examples/missing_parity.txt:1`. |
| `problems/ITA2025Q3/examples/wrong_coefficient.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q3/examples/wrong_coefficient.txt:1`. |
| `problems/ITA2025Q3/microclaims.json` | ALTO | contrato JSON de microclaims e dependências; evidência `problems/ITA2025Q3/microclaims.json:1`. |
| `problems/ITA2025Q3/problem.json` | MÉDIO | contrato JSON de enunciado e resposta esperada; evidência `problems/ITA2025Q3/problem.json:1`. |
| `problems/ITA2025Q3/rubric.json` | ALTO | contrato JSON de rubrica pontuada; evidência `problems/ITA2025Q3/rubric.json:1`. |
| `problems/ITA2025Q4/examples/answer_only.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q4/examples/answer_only.txt:1`. |
| `problems/ITA2025Q4/examples/correct_solution.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q4/examples/correct_solution.txt:1`. |
| `problems/ITA2025Q4/examples/missing_distinct_inputs.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q4/examples/missing_distinct_inputs.txt:1`. |
| `problems/ITA2025Q4/examples/wrong_target.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q4/examples/wrong_target.txt:1`. |
| `problems/ITA2025Q4/examples/wrong_witnesses.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q4/examples/wrong_witnesses.txt:1`. |
| `problems/ITA2025Q4/microclaims.json` | ALTO | contrato JSON de microclaims e dependências; evidência `problems/ITA2025Q4/microclaims.json:1`. |
| `problems/ITA2025Q4/problem.json` | MÉDIO | contrato JSON de enunciado e resposta esperada; evidência `problems/ITA2025Q4/problem.json:1`. |
| `problems/ITA2025Q4/rubric.json` | ALTO | contrato JSON de rubrica pontuada; evidência `problems/ITA2025Q4/rubric.json:1`. |
| `problems/ITA2025Q5/examples/answer_only.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q5/examples/answer_only.txt:1`. |
| `problems/ITA2025Q5/examples/correct_solution.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q5/examples/correct_solution.txt:1`. |
| `problems/ITA2025Q5/examples/missing_difference_relation.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q5/examples/missing_difference_relation.txt:1`. |
| `problems/ITA2025Q5/examples/missing_factorization.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q5/examples/missing_factorization.txt:1`. |
| `problems/ITA2025Q5/examples/wrong_direction.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q5/examples/wrong_direction.txt:1`. |
| `problems/ITA2025Q5/microclaims.json` | ALTO | contrato JSON de microclaims e dependências; evidência `problems/ITA2025Q5/microclaims.json:1`. |
| `problems/ITA2025Q5/problem.json` | MÉDIO | contrato JSON de enunciado e resposta esperada; evidência `problems/ITA2025Q5/problem.json:1`. |
| `problems/ITA2025Q5/rubric.json` | ALTO | contrato JSON de rubrica pontuada; evidência `problems/ITA2025Q5/rubric.json:1`. |
| `problems/ITA2025Q8/examples/answer_only.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q8/examples/answer_only.txt:1`. |
| `problems/ITA2025Q8/examples/correct_solution.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q8/examples/correct_solution.txt:1`. |
| `problems/ITA2025Q8/examples/missing_sign_analysis.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q8/examples/missing_sign_analysis.txt:1`. |
| `problems/ITA2025Q8/examples/wrong_interval.txt` | BAIXO | fixture textual de solução; evidência `problems/ITA2025Q8/examples/wrong_interval.txt:1`. |
| `problems/ITA2025Q8/microclaims.json` | ALTO | contrato JSON de microclaims e dependências; evidência `problems/ITA2025Q8/microclaims.json:1`. |
| `problems/ITA2025Q8/problem.json` | MÉDIO | contrato JSON de enunciado e resposta esperada; evidência `problems/ITA2025Q8/problem.json:1`. |
| `problems/ITA2025Q8/rubric.json` | ALTO | contrato JSON de rubrica pontuada; evidência `problems/ITA2025Q8/rubric.json:1`. |
| `pyproject.toml` | MÉDIO | manifesto Python do pacote e dependências; evidência `pyproject.toml:1`. |
| `tests/test_evaluator_architecture.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_evaluator_architecture.py:1`. |
| `tests/test_f2q1_rubric_adjustments.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q1_rubric_adjustments.py:1`. |
| `tests/test_f2q1_strong_certificate.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q1_strong_certificate.py:1`. |
| `tests/test_f2q1_student_claim_checks.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q1_student_claim_checks.py:1`. |
| `tests/test_f2q3_rubric_adjustments.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q3_rubric_adjustments.py:1`. |
| `tests/test_f2q3_strong_certificate.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q3_strong_certificate.py:1`. |
| `tests/test_f2q3_student_claim_checks.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q3_student_claim_checks.py:1`. |
| `tests/test_f2q5_rubric_adjustments.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q5_rubric_adjustments.py:1`. |
| `tests/test_f2q5_strong_certificate.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q5_strong_certificate.py:1`. |
| `tests/test_f2q5_student_claim_checks.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q5_student_claim_checks.py:1`. |
| `tests/test_f2q6_rubric_adjustments.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q6_rubric_adjustments.py:1`. |
| `tests/test_f2q6_strong_certificate.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q6_strong_certificate.py:1`. |
| `tests/test_f2q6_student_claim_checks.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q6_student_claim_checks.py:1`. |
| `tests/test_f2q8_student_claim_checks.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_f2q8_student_claim_checks.py:1`. |
| `tests/test_ita2025f2q1_level1.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_ita2025f2q1_level1.py:1`. |
| `tests/test_ita2025f2q3_level1.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_ita2025f2q3_level1.py:1`. |
| `tests/test_ita2025f2q5_level1.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_ita2025f2q5_level1.py:1`. |
| `tests/test_ita2025f2q6_level1.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_ita2025f2q6_level1.py:1`. |
| `tests/test_ita2025f2q8_level1.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_ita2025f2q8_level1.py:1`. |
| `tests/test_ita2025q1_level2.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_ita2025q1_level2.py:1`. |
| `tests/test_ita2025q3_level1.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_ita2025q3_level1.py:1`. |
| `tests/test_ita2025q4_level1.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_ita2025q4_level1.py:1`. |
| `tests/test_ita2025q4_level2.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_ita2025q4_level2.py:1`. |
| `tests/test_ita2025q5_level1.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_ita2025q5_level1.py:1`. |
| `tests/test_ita2025q8_level1.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_ita2025q8_level1.py:1`. |
| `tests/test_level1_f2_suite_regressions.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_level1_f2_suite_regressions.py:1`. |
| `tests/test_problem_assets_contracts.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_problem_assets_contracts.py:1`. |
| `tests/test_problem_assets_validation.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_problem_assets_validation.py:1`. |
| `tests/test_problem_router_coverage.py` | MÉDIO | teste pytest de API, contratos, regressão ou verificação Lean; evidência `tests/test_problem_router_coverage.py:1`. |

## 8. Código morto, duplicado ou suspeito

- `ConfiaLeanAuditor/Basic.lean` é scaffold confirmado: só contém `def hello := "world"` em `ConfiaLeanAuditor/Basic.lean:1`, e o único consumo detectado é o import agregador em `ConfiaLeanAuditor.lean:1`.
- `README.md` permanece como scaffold de configuração GitHub, com instrução explícita de remoção da seção em `README.md:13`.
- O CLI `run_problem` procura certificados em `problems/{problem_id}/certificate/Statement.lean` em `app/confia_lean_auditor/lean/run_lean.py:101` a `app/confia_lean_auditor/lean/run_lean.py:128`, mas o inventário versionado contém certificado nesse formato apenas em `problems/ITA2025Q1/certificate/Statement.lean:1`; para os demais problemas, o caminho normal da API é `Attempt.lean` gerado por builders em `app/confia_lean_auditor/main.py:78` a `app/confia_lean_auditor/main.py:96`.
- Existem scripts de benchmark não versionados em `benchmarks/f2_suite_level1_v2/` e `benchmarks/q_suite_level1_v2/`, detectados por `git status --short` como `??`; o runner F2 v2 escreve saídas em `benchmarks/f2_suite_level1_v2/reports` e gold em `benchmarks/f2_suite_level1_v2/gold_500_v2.csv` em `benchmarks/f2_suite_level1_v2/run_level1_f2_suite_v2.py:15` a `benchmarks/f2_suite_level1_v2/run_level1_f2_suite_v2.py:16`.
- Há duplicação estrutural por problema em extratores, builders, renderizadores, student checkers e adjusters: as rotas repetidas aparecem em `app/confia_lean_auditor/claims/extract_claims.py:41` a `app/confia_lean_auditor/claims/extract_claims.py:75`, `app/confia_lean_auditor/lean/build_attempt.py:44` a `app/confia_lean_auditor/lean/build_attempt.py:123`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:411` a `app/confia_lean_auditor/lean/formal_step_evaluator.py:441`, `app/confia_lean_auditor/student_claims/registry.py:23` a `app/confia_lean_auditor/student_claims/registry.py:39`, `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:23` a `app/confia_lean_auditor/lean/student_claim_checkers/registry.py:62` e `app/confia_lean_auditor/rubric/adjusters/registry.py:26` a `app/confia_lean_auditor/rubric/adjusters/registry.py:45`.
- A versão do pacote e a versão da API divergem: `pyproject.toml` e `lakefile.toml` indicam `0.1.0` em `pyproject.toml:7` e `lakefile.toml:2`, enquanto `main.py` expõe `0.4.0` em `app/confia_lean_auditor/main.py:26` e `app/confia_lean_auditor/main.py:38`.
- `MILESTONE_ITA2025F2.md` declara estado operacional e validação recente em `MILESTONE_ITA2025F2.md:25` a `MILESTONE_ITA2025F2.md:31`, mas esta auditoria não executou `pytest` nem `lake build`; portanto essas afirmações ficam registradas como documentação existente, não como resultado desta execução.

## 9. Ordem recomendada de investigação

1. Mapear divergência de versão entre pacote/Lake e API: evidências em `pyproject.toml:7`, `lakefile.toml:2`, `app/confia_lean_auditor/main.py:26` e `app/confia_lean_auditor/main.py:38`.
2. Auditar sincronização dos dez `problem_id` entre assets, extratores, builders, renderizadores, statements Lean, student claims F2 e adjusters: evidências em `tests/test_problem_router_coverage.py:12` a `tests/test_problem_router_coverage.py:58`, `app/confia_lean_auditor/claims/extract_claims.py:41` a `app/confia_lean_auditor/claims/extract_claims.py:75`, `app/confia_lean_auditor/lean/build_attempt.py:44` a `app/confia_lean_auditor/lean/build_attempt.py:123` e `app/confia_lean_auditor/lean/formal_step_evaluator.py:411` a `app/confia_lean_auditor/lean/formal_step_evaluator.py:441`.
3. Investigar a fronteira entre microclaims formais e `student_claim_checks`, porque a pontuação primeiro usa `evaluate_rubric` e depois aplica adjusters F2 em `app/confia_lean_auditor/main.py:122` a `app/confia_lean_auditor/main.py:137`, enquanto `RubricItemResult` carrega flags de ajuste em `app/confia_lean_auditor/core/schemas.py:58` a `app/confia_lean_auditor/core/schemas.py:68`.
4. Auditar a escrita de artefatos em rotas e checkers, incluindo retenção e isolamento por `run_id`: evidências em `app/confia_lean_auditor/main.py:59` a `app/confia_lean_auditor/main.py:61`, `app/confia_lean_auditor/main.py:159` a `app/confia_lean_auditor/main.py:178`, `app/confia_lean_auditor/lean/student_claim_checker.py:168` a `app/confia_lean_auditor/lean/student_claim_checker.py:193` e `.gitignore:9` a `.gitignore:29`.
5. Auditar superfície Lean dinâmica e whitelists: evidências em `app/confia_lean_auditor/lean/run_lean.py:13` a `app/confia_lean_auditor/lean/run_lean.py:35`, `app/confia_lean_auditor/lean/run_lean.py:65` a `app/confia_lean_auditor/lean/run_lean.py:98`, `app/confia_lean_auditor/lean/formal_step_evaluator.py:455` a `app/confia_lean_auditor/lean/formal_step_evaluator.py:493` e `app/confia_lean_auditor/lean/student_claim_checker.py:145` a `app/confia_lean_auditor/lean/student_claim_checker.py:159`.
6. Separar documentação/scaffold e superfície operacional: evidências em `README.md:13`, `ConfiaLeanAuditor/Basic.lean:1`, `MILESTONE_ITA2025F2.md:25` a `MILESTONE_ITA2025F2.md:31` e `ConfiaLeanAuditor.lean:1`.
7. Auditar benchmarks como ferramentas auxiliares e não como runtime: evidências em `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py:155` a `benchmarks/f2_suite_level1_2/run_level1_f2_suite.py:273`, `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py:68` a `benchmarks/stage1_4/ita2025f2q8/run_stage1_4_f2q8.py:242`, e arquivos não versionados listados por `git status --short` sob `benchmarks/f2_suite_level1_v2/` e `benchmarks/q_suite_level1_v2/`.

Fim da auditoria descritiva. Não foram executados comandos de teste/build que acionassem o pipeline da aplicação, e nenhum arquivo do projeto foi alterado além deste `AUDITORIA_REPOSITORIO.md`, conforme permitido pela solicitação.
