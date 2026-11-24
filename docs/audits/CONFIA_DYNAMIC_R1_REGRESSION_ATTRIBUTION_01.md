# ConfIA Dynamic — R1 Regression Attribution 01

Data: 2026-11-13 (UTC). Atribuição pareada das 105 falhas reportadas na regressão R1; código de produto e expectativas preservados.

**NEW_R1_REGRESSIONS = 0**

**Veredito: R1_REGRESSION_ATTRIBUTION_CLEAN.** As contagens abaixo se referem às seleções executadas nesta auditoria. A regressão completa histórica permanece em **3009 passed, 47 skipped, 105 failed**; não foi reexecutada integralmente nem declarada verde.

## 1. Baseline congelada e preservação

Baseline imediatamente anterior ao R1: **`5aa7344e5904305a414688741f83aafc7d610200`**, commit `Analyze ConfIA Dynamic DY7 holdout root causes`. O commit anterior `e0975898bb2449c05595c5b75236a9690c51b8b1` contém a implementação DY7; a diferença até `5aa7344` consiste em nove documentos/artefatos forenses. A baseline desta auditoria é o SHA mais recente, não a cópia parcial de `app/` usada no experimento DEV anterior.

Worktree oficial: `/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic`, branch `feat/dynamic-correction`. Worktree temporário destacado: `/private/tmp/confia-r1-attribution-baseline-5aa7344`. Este foi criado especificamente a partir do SHA congelado e permanece disponível para inspeção, sem diferenças em arquivos versionados; seu único item não versionado é o enlace de ambiente `.lake` descrito abaixo. Não se utilizaram fontes ou ambientes dos worktrees de dezembro/P3.

Antes dos testes foram preservados **1222 hashes** e uma cópia dos **38 arquivos R1 alterados/novos**. Ao término: zero mudanças nesses arquivos, patch R1 idêntico, HEAD e branch preservados, índice sem alterações e **1100 arquivos históricos protegidos** com os mesmos hashes. Evidências: [source-preservation.json](assets/confia-dynamic-r1-regression-attribution/source-preservation.json), [r1-before.tar.gz](assets/confia-dynamic-r1-regression-attribution/r1-before.tar.gz), [r1-before.patch](assets/confia-dynamic-r1-regression-attribution/r1-before.patch), [integrity.json](assets/confia-dynamic-r1-regression-attribution/integrity.json).

## 2. Método e equivalência do ambiente

Os 105 node IDs foram extraídos da seção `FAILED` do log original, sem exclusões: [failure-nodeids.json](assets/confia-dynamic-r1-regression-attribution/failure-nodeids.json) e [original-inventory.json](assets/confia-dynamic-r1-regression-attribution/original-inventory.json). Cada traceback original está vinculado ao node ID e ao hash da fonte. Os arquivos dos testes selecionados, `tests/conftest.py`, toolchain e manifestos Lake são idênticos nos dois códigos: [baseline-setup.json](assets/confia-dynamic-r1-regression-attribution/baseline-setup.json).

As duas execuções usaram processos separados, a mesma ordem de node IDs, o Python absoluto do `.venv` oficial, os mesmos pacotes, PATH e `PYTHONHASHSEED=0`. O `sys.path` seleciona explicitamente o `app/` de cada worktree; o caminho e o SHA do grader efetivamente importado são registrados. `CONFIA_LEAN_AUDITOR_ROOT` foi removido em ambos para que cada código utilize seu próprio diretório. O conftest existente isola stores e remove a chave OpenAI nos testes.

Python 3.9.6; pytest 8.4.2; Pydantic 2.13.5; FastAPI 0.128.8. A `.lake` da baseline aponta para a `.lake` oficial, garantindo a mesma instalação Lean/Mathlib. As execuções foram **sequenciais**, sem disputa concorrente desse diretório. HEAD, status e diff de Mathlib, pacotes e configuração permaneceram iguais em todas as dez fotografias antes/depois das quatro execuções principais e da repetição diagnóstica. Mathlib observado: `ab19bac90981b27f5380941f4b36617e738358c9`; revisão solicitada pelo manifesto: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`.

O observador [runner.py](assets/confia-dynamic-r1-regression-attribution/runner.py) registra setup/call/teardown, tracebacks e chamadas reais de Lean/Lake, passando argumentos, retornos e exceções sem alteração. Não foram substituídos verificadores nem resultados. Pytest: `-vv --tb=long -p no:cacheprovider`; seleção de contratos em [baseline-contract-selection.json](assets/confia-dynamic-r1-regression-attribution/baseline-contract-selection.json) e [r1-contract-selection.json](assets/confia-dynamic-r1-regression-attribution/r1-contract-selection.json).

A enumeração bruta de `importlib.metadata` repetiu os metadados locais de `confia-lean-auditor` conforme entradas de `sys.path` (2, 3 ou 7 ocorrências). O conjunto de nomes/versões e a lista completa de dependências de terceiros são idênticos. As listas brutas e a comparação dessa multiplicidade permanecem em `integrity.json`; não houve instalação ou troca de dependências. A identidade do código da aplicação é aferida separadamente por caminho e hash.

Uma tentativa inicial do executor R1 terminou antes da coleta porque um script desta auditoria chamado `queue.py` colidiu com o módulo padrão homônimo. O script foi renomeado para `run_sequence.py`; o incidente está preservado em `r1-startup-error.log` e não representa falha de teste ou de produto. Não houve mudança no observador entre as execuções válidas.

## 3. Contagens e classificações pareadas

| Seleção | Baseline | R1 |
| --- | --- | --- |
| 105 falhas originais | 0 passed, 105 failed, 0 skipped, 0 errors | 0 passed, 105 failed, 0 skipped, 0 errors |
| Dynamic existente + contratos compartilhados; R1 inclui novos testes | 613 passed, 4 failed, 2 skipped, 0 errors | 705 passed, 4 failed, 2 skipped, 0 errors |

| Classificação dos 105 pares | N |
| --- | ---: |
| `FAIL_BOTH_SAME_FINGERPRINT` | 105 |
| `FAIL_BOTH_DIFFERENT_FINGERPRINT` | 0 |
| `PASS_BASELINE_FAIL_R1` | 0 |
| `FAIL_BASELINE_PASS_R1` | 0 |
| `PASS_BOTH` | 0 |
| `NOT_COMPARABLE` | 0 |

`PASS_BASELINE_FAIL_R1 = 0`. Lista explícita: `[]`. Casos não resolvidos: `[]`. Não há inferência baseada apenas na proximidade do nome de arquivo: cada uma das 105 falhas tem reprodução pareada.

Inventário com causa por node ID: [failure-inventory.json](assets/confia-dynamic-r1-regression-attribution/failure-inventory.json) / [failure-inventory.csv](assets/confia-dynamic-r1-regression-attribution/failure-inventory.csv). Comparação pareada: [paired-comparison.json](assets/confia-dynamic-r1-regression-attribution/paired-comparison.json) / [paired-comparison.csv](assets/confia-dynamic-r1-regression-attribution/paired-comparison.csv). Resultados e logs completos: [baseline-results.json](assets/confia-dynamic-r1-regression-attribution/baseline-results.json), [r1-results.json](assets/confia-dynamic-r1-regression-attribution/r1-results.json), [baseline.log](assets/confia-dynamic-r1-regression-attribution/baseline.log), [r1.log](assets/confia-dynamic-r1-regression-attribution/r1.log).

## 4. Fingerprints e atribuição causal

**101/105** tracebacks têm o mesmo fingerprint estrito após a normalização básica do observador; **105/105** têm o mesmo fingerprint integral de atribuição após a normalização adicional de metadados de execução. Os fingerprints estritos diferentes são preservados, não substituídos. As regras adicionais se limitam ao diretório temporal de student claims, `manifest_id`, `generated_at`, `manifest_sha256`, UUID de diretório TME P4 e renomeação consistente dos tokens de verificação derivados de `solution_id` aleatório (preservando o grafo de referências). A origem dos tokens está em `tme/registry.py:28` e `claims/common/fact_results.py:18`; o diretório aleatório é criado em `lean/student_claim_checkers/tme2_p4.py:91`. Esses fontes são idênticos nos dois códigos. A revisão específica está em `normalization-review.json`. Não removem asserções, valores matemáticos, pontuações, status ou conteúdo de fontes Lean. Regras: [fingerprint-normalization.json](assets/confia-dynamic-r1-regression-attribution/fingerprint-normalization.json); diferenças estritas: [traceback-differences.diff](assets/confia-dynamic-r1-regression-attribution/traceback-differences.diff); implementação: [compare.py](assets/confia-dynamic-r1-regression-attribution/compare.py).

**102 falhas formais preexistentes/ambientais:** todos os 102 testes executaram Lean real em ambos os códigos. Houve **435 chamadas de verificação na baseline e 435 no R1**, excluindo consultas `--version`. Todos retornaram exit code 1 e o mesmo stderr abaixo. As sequências de hashes dos fontes Lean são idênticas nos **102/102 pares**. Portanto, esta execução não demonstra refutação matemática: a verificação parou no checkout da dependência, com efeitos posteriores como `lean_error`, score indefinido e `ADJUDICATOR_UNAVAILABLE`.

```text
info: mathlib: checking out revision '8f9d9cff6bd728b17a24e163c9402775d9e6a365'
error: external command 'git' exited with code 1
```

Fingerprint ambiental SHA-256: `3980f91b6258aa9738dd3e4ad200e6f15bbefef5061d3d0281185074994b873b`. Fonte e stderr de cada chamada: [baseline-lean.jsonl](assets/confia-dynamic-r1-regression-attribution/baseline-lean.jsonl) e [r1-lean.jsonl](assets/confia-dynamic-r1-regression-attribution/r1-lean.jsonl). Vinculação de fingerprints, fontes e contagens por node ID: [formal-fingerprints.json](assets/confia-dynamic-r1-regression-attribution/formal-fingerprints.json). Lean 4.28.0 e Lake 5.0.0-src+7e01a1b responderam às consultas de versão; a falha está nas chamadas de verificação via Lake.

**Três falhas de contratos preexistentes, independentes do R1:**

| Node ID | Causa reproduzida nos dois códigos |
| --- | --- |
| `tests/test_handwriting_recognition_benchmark.py::test_loader_schema_artificial_samples_and_optional_strokes` | O schema JSON salvo declara `RecognitionSegment.page_index.exclusiveMaximum=3`; o modelo gerado declara 50, via `MAX_SOURCE_PAGES`. Essa é a única diferença de schema encontrada. |
| `tests/test_ui_01_shell.py::test_central_product_vocabulary_is_preserved_without_contract_renames` | A frase exigida `Verificação formal com Lean` está ausente dos três assets concatenados pelo teste. |
| `tests/test_ui_02_workspace.py::test_parent_statement_is_compact_and_sticky_through_notebook_and_submission` | Existe uma ocorrência de `position: sticky` depois de `/* Embedded mode`, na regra dos controles TME em `tablet.css:442`; o teste exige ausência. |

Os schemas e assets implicados são byte a byte iguais entre baseline e R1; a sondagem dos dois modelos/arquivos também é igual: [nonformal-evidence.json](assets/confia-dynamic-r1-regression-attribution/nonformal-evidence.json). Não se atribui a divergência 3 versus 50 a uma mudança de Pydantic sem evidência; ela é uma incompatibilidade preexistente entre schema salvo e modelo compartilhado. Nenhum desses contratos foi corrigido nesta tarefa.

Uma repetição adicional dos dois testes semânticos na **mesma baseline**, sem mudar código, voltou a produzir fingerprints estritos diferentes e fingerprints normalizados iguais. Isso confirma que esses IDs variam independentemente de R1. A sondagem está em `baseline-semantic-repeat-results.json` e não aumenta o denominador dos 105 pares.

## 5. Regressão Dynamic R1 e contratos compartilhados

Dynamic DY1–DY7 + R1 no código atual: **306 passed, 0 failed, 0 skipped, 0 errors**. Há **92 testes novos exclusivos do R1**, com resultados `{"PASS": 92}`. Contratos compartilhados no R1: **399 passed, 4 failed, 2 skipped, 0 errors**.

Os 16 módulos compartilhados cobrem Assessment, Submission, TranscriptionVersion, bridge de auditoria, decisões do professor, compatibilidade dos modelos, prova multiquestão, auditoria por questão, reanálise, confirmação humana, finalização, grader híbrido, integração aceita, certificação e leitura do workspace/auditoria. São os contratos existentes, sem novas expectativas ou fixtures de captura.

Foram comparados **619 node IDs comuns** das seleções de contratos, com classificações `{"FAIL_BOTH_SAME_FINGERPRINT": 4, "PASS_BOTH": 613, "SKIP_BOTH_NOT_EXECUTED": 2}`. Os novos testes R1 não foram artificialmente copiados para a baseline. Os pares formais já presentes nos 105 não são contados duas vezes como novas regressões. Evidências: [contracts-comparison.json](assets/confia-dynamic-r1-regression-attribution/contracts-comparison.json), [baseline-contracts-results.json](assets/confia-dynamic-r1-regression-attribution/baseline-contracts-results.json), [r1-contracts-results.json](assets/confia-dynamic-r1-regression-attribution/r1-contracts-results.json).

Os dois skips correspondem a `test_real_smoke_dry_run_separates_semantic_hashes_from_transport` e `test_transport_builder_does_not_weaken_holdout_guard`, ambos em `test_tme_model_compat.py`. O motivo existente é `Frozen local DEV pack unavailable`: os dois arquivos DEV requeridos não existem em nenhum dos worktrees. Evidência: `skip-evidence.json`. Os hashes dos 23 módulos comuns são idênticos (`contracts-inputs.json`). Skips não contam como passes nem como validação executada.

## 6. Limites e estado final

A atribuição responde à origem observável das 105 falhas e aos contratos reexecutados. Preexistente significa reproduzida no código anterior ao R1 sob o ambiente desta auditoria; não se inferiu a data histórica em que a falha começou. Não transforma a suíte completa em verde e não garante ausência de defeitos em caminhos bloqueados por Mathlib indisponível. A comparação inclui a mesma falha, o mesmo ponto de asserção, os mesmos dados de erro e os mesmos fontes Lean; não é uma validação formal bem-sucedida.

HOLDOUT_V2 não foi iniciado. Não houve correção de Mathlib, captura, UI, expectations ou código de produto; tampouco `git add`, commit, reset ou checkout destrutivo. O worktree temporário destacado foi criado conforme a autorização desta tarefa. Os relatórios e evidências históricos permanecem intactos.

`git status --short` ao fechamento (também em [status-final.txt](assets/confia-dynamic-r1-regression-attribution/status-final.txt)):

```text
 M app/confia_lean_auditor/dynamic/grader.py
 M app/confia_lean_auditor/dynamic/grading_models.py
?? app/confia_lean_auditor/dynamic/method_sufficiency.py
?? app/confia_lean_auditor/dynamic/substitution.py
?? app/confia_lean_auditor/dynamic/versions.py
?? benchmarks/dynamic/dev_v2/
?? docs/audits/CONFIA_DYNAMIC_R1_DEV_V2_IMPLEMENTACAO_01.md
?? docs/audits/CONFIA_DYNAMIC_R1_REGRESSION_ATTRIBUTION_01.md
?? docs/audits/assets/confia-dynamic-r1-dev-v2/
?? docs/audits/assets/confia-dynamic-r1-regression-attribution/
?? scripts/evaluation/run_dynamic_dev_v2.py
?? tests/test_dynamic_r1.py
```

Resumo estruturado: [summary.json](assets/confia-dynamic-r1-regression-attribution/summary.json). Manifesto de integridade dos entregáveis: [artifact-manifest.json](assets/confia-dynamic-r1-regression-attribution/artifact-manifest.json).

NEW_R1_REGRESSIONS = 0

R1_REGRESSION_ATTRIBUTION_CLEAN
