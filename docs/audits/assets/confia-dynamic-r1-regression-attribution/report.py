import collections,datetime,hashlib,json,pathlib,subprocess
R=pathlib.Path('/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic')
O=R/'docs/audits/assets/confia-dynamic-r1-regression-attribution'
P=R/'docs/audits/CONFIA_DYNAMIC_R1_REGRESSION_ATTRIBUTION_01.md'
def read(n):return json.loads((O/n).read_text())
def link(n):return f'[{n}](assets/confia-dynamic-r1-regression-attribution/{n})'
def counts(c):return f"{c.get('PASS',0)} passed, {c.get('FAIL',0)} failed, {c.get('SKIP',0)} skipped, {c.get('ERROR',0)} errors"
s=read('comparison-summary.json');i=read('integrity.json');c=read('contracts-comparison.json');f=read('formal-fingerprints.json');p=read('paired-comparison.json');env=read('baseline-environment-before.json')
assert i['all_checks_passed'], 'Do not publish clean attribution if preservation/environment checks fail'
assert s['formal_same_source_sequence']==s['formal_cases'], 'Review changed formal inputs before reporting'
verdict=s['provisional_verdict']
families=collections.Counter(r['cause'] for r in p['rows'])
files=collections.Counter(r['nodeid'].split('::')[0] for r in p['rows'])
first_formal=json.loads(next(l for l in (O/'baseline-lean.jsonl').read_text().splitlines() if json.loads(l).get('returncode')==1))
new_r1=c['r1_only']
lines=[
'# ConfIA Dynamic — R1 Regression Attribution 01',
'',
f"Data: {datetime.datetime.now(datetime.timezone.utc).date().isoformat()} (UTC). Atribuição pareada das 105 falhas reportadas na regressão R1; código de produto e expectativas preservados.",
'',
f"**NEW_R1_REGRESSIONS = {s['NEW_R1_REGRESSIONS']}**",
'',
f"**Veredito: {verdict}.** As contagens abaixo se referem às seleções executadas nesta auditoria. A regressão completa histórica permanece em **3009 passed, 47 skipped, 105 failed**; não foi reexecutada integralmente nem declarada verde.",
'',
'## 1. Baseline congelada e preservação',
'',
'Baseline imediatamente anterior ao R1: **`5aa7344e5904305a414688741f83aafc7d610200`**, commit `Analyze ConfIA Dynamic DY7 holdout root causes`. O commit anterior `e0975898bb2449c05595c5b75236a9690c51b8b1` contém a implementação DY7; a diferença até `5aa7344` consiste em nove documentos/artefatos forenses. A baseline desta auditoria é o SHA mais recente, não a cópia parcial de `app/` usada no experimento DEV anterior.',
'',
'Worktree oficial: `/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic`, branch `feat/dynamic-correction`. Worktree temporário destacado: `/private/tmp/confia-r1-attribution-baseline-5aa7344`. Este foi criado especificamente a partir do SHA congelado e permanece disponível para inspeção, sem diferenças em arquivos versionados; seu único item não versionado é o enlace de ambiente `.lake` descrito abaixo. Não se utilizaram fontes ou ambientes dos worktrees de dezembro/P3.',
'',
f"Antes dos testes foram preservados **{i['original_files_checked']} hashes** e uma cópia dos **{i['dirty_backup_files_checked']} arquivos R1 alterados/novos**. Ao término: zero mudanças nesses arquivos, patch R1 idêntico, HEAD e branch preservados, índice sem alterações e **{i['historical_protected_files_checked']} arquivos históricos protegidos** com os mesmos hashes. Evidências: {link('source-preservation.json')}, {link('r1-before.tar.gz')}, {link('r1-before.patch')}, {link('integrity.json')}.",
'',
'## 2. Método e equivalência do ambiente',
'',
f"Os 105 node IDs foram extraídos da seção `FAILED` do log original, sem exclusões: {link('failure-nodeids.json')} e {link('original-inventory.json')}. Cada traceback original está vinculado ao node ID e ao hash da fonte. Os arquivos dos testes selecionados, `tests/conftest.py`, toolchain e manifestos Lake são idênticos nos dois códigos: {link('baseline-setup.json')}.",
'',
'As duas execuções usaram processos separados, a mesma ordem de node IDs, o Python absoluto do `.venv` oficial, os mesmos pacotes, PATH e `PYTHONHASHSEED=0`. O `sys.path` seleciona explicitamente o `app/` de cada worktree; o caminho e o SHA do grader efetivamente importado são registrados. `CONFIA_LEAN_AUDITOR_ROOT` foi removido em ambos para que cada código utilize seu próprio diretório. O conftest existente isola stores e remove a chave OpenAI nos testes.',
'',
f"Python 3.9.6; pytest 8.4.2; Pydantic 2.13.5; FastAPI 0.128.8. A `.lake` da baseline aponta para a `.lake` oficial, garantindo a mesma instalação Lean/Mathlib. As execuções foram **sequenciais**, sem disputa concorrente desse diretório. HEAD, status e diff de Mathlib, pacotes e configuração permaneceram iguais em todas as dez fotografias antes/depois das quatro execuções principais e da repetição diagnóstica. Mathlib observado: `{env['mathlib_head']}`; revisão solicitada pelo manifesto: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`.",
'',
f"O observador {link('runner.py')} registra setup/call/teardown, tracebacks e chamadas reais de Lean/Lake, passando argumentos, retornos e exceções sem alteração. Não foram substituídos verificadores nem resultados. Pytest: `-vv --tb=long -p no:cacheprovider`; seleção de contratos em {link('baseline-contract-selection.json')} e {link('r1-contract-selection.json')}.",
'',
'A enumeração bruta de `importlib.metadata` repetiu os metadados locais de `confia-lean-auditor` conforme entradas de `sys.path` (2, 3 ou 7 ocorrências). O conjunto de nomes/versões e a lista completa de dependências de terceiros são idênticos. As listas brutas e a comparação dessa multiplicidade permanecem em `integrity.json`; não houve instalação ou troca de dependências. A identidade do código da aplicação é aferida separadamente por caminho e hash.',
'',
'Uma tentativa inicial do executor R1 terminou antes da coleta porque um script desta auditoria chamado `queue.py` colidiu com o módulo padrão homônimo. O script foi renomeado para `run_sequence.py`; o incidente está preservado em `r1-startup-error.log` e não representa falha de teste ou de produto. Não houve mudança no observador entre as execuções válidas.',
'',
'## 3. Contagens e classificações pareadas',
'',
'| Seleção | Baseline | R1 |',
'| --- | --- | --- |',
f"| 105 falhas originais | {counts(s['baseline_counts'])} | {counts(s['r1_counts'])} |",
f"| Dynamic existente + contratos compartilhados; R1 inclui novos testes | {counts(c['baseline_counts'])} | {counts(c['r1_counts'])} |",
'',
'| Classificação dos 105 pares | N |',
'| --- | ---: |',
*[f"| `{name}` | {s['paired_counts'].get(name,0)} |" for name in ['FAIL_BOTH_SAME_FINGERPRINT','FAIL_BOTH_DIFFERENT_FINGERPRINT','PASS_BASELINE_FAIL_R1','FAIL_BASELINE_PASS_R1','PASS_BOTH','NOT_COMPARABLE']],
'',
f"`PASS_BASELINE_FAIL_R1 = {len(s['PASS_BASELINE_FAIL_R1'])}`. Lista explícita: `{json.dumps(s['PASS_BASELINE_FAIL_R1'])}`. Casos não resolvidos: `{json.dumps(s['unresolved'])}`. Não há inferência baseada apenas na proximidade do nome de arquivo: cada uma das 105 falhas tem reprodução pareada.",
'',
f"Inventário com causa por node ID: {link('failure-inventory.json')} / {link('failure-inventory.csv')}. Comparação pareada: {link('paired-comparison.json')} / {link('paired-comparison.csv')}. Resultados e logs completos: {link('baseline-results.json')}, {link('r1-results.json')}, {link('baseline.log')}, {link('r1.log')}.",
'',
'## 4. Fingerprints e atribuição causal',
'',
f"**{s['same_traceback']}/105** tracebacks têm o mesmo fingerprint estrito após a normalização básica do observador; **{s['same_attribution_traceback']}/105** têm o mesmo fingerprint integral de atribuição após a normalização adicional de metadados de execução. Os fingerprints estritos diferentes são preservados, não substituídos. As regras adicionais se limitam ao diretório temporal de student claims, `manifest_id`, `generated_at`, `manifest_sha256`, UUID de diretório TME P4 e renomeação consistente dos tokens de verificação derivados de `solution_id` aleatório (preservando o grafo de referências). A origem dos tokens está em `tme/registry.py:28` e `claims/common/fact_results.py:18`; o diretório aleatório é criado em `lean/student_claim_checkers/tme2_p4.py:91`. Esses fontes são idênticos nos dois códigos. A revisão específica está em `normalization-review.json`. Não removem asserções, valores matemáticos, pontuações, status ou conteúdo de fontes Lean. Regras: {link('fingerprint-normalization.json')}; diferenças estritas: {link('traceback-differences.diff')}; implementação: {link('compare.py')}.",
'',
f"**102 falhas formais preexistentes/ambientais:** todos os 102 testes executaram Lean real em ambos os códigos. Houve **{s['formal_baseline_verification_calls']} chamadas de verificação na baseline e {s['formal_r1_verification_calls']} no R1**, excluindo consultas `--version`. Todos retornaram exit code 1 e o mesmo stderr abaixo. As sequências de hashes dos fontes Lean são idênticas nos **{s['formal_same_source_sequence']}/102 pares**. Portanto, esta execução não demonstra refutação matemática: a verificação parou no checkout da dependência, com efeitos posteriores como `lean_error`, score indefinido e `ADJUDICATOR_UNAVAILABLE`.",
'',
'```text',
first_formal['stderr'].strip(),
'```',
'',
f"Fingerprint ambiental SHA-256: `{first_formal['environment_fingerprint']}`. Fonte e stderr de cada chamada: {link('baseline-lean.jsonl')} e {link('r1-lean.jsonl')}. Vinculação de fingerprints, fontes e contagens por node ID: {link('formal-fingerprints.json')}. Lean 4.28.0 e Lake 5.0.0-src+7e01a1b responderam às consultas de versão; a falha está nas chamadas de verificação via Lake.",
'',
'**Três falhas de contratos preexistentes, independentes do R1:**',
'',
'| Node ID | Causa reproduzida nos dois códigos |',
'| --- | --- |',
'| `tests/test_handwriting_recognition_benchmark.py::test_loader_schema_artificial_samples_and_optional_strokes` | O schema JSON salvo declara `RecognitionSegment.page_index.exclusiveMaximum=3`; o modelo gerado declara 50, via `MAX_SOURCE_PAGES`. Essa é a única diferença de schema encontrada. |',
'| `tests/test_ui_01_shell.py::test_central_product_vocabulary_is_preserved_without_contract_renames` | A frase exigida `Verificação formal com Lean` está ausente dos três assets concatenados pelo teste. |',
'| `tests/test_ui_02_workspace.py::test_parent_statement_is_compact_and_sticky_through_notebook_and_submission` | Existe uma ocorrência de `position: sticky` depois de `/* Embedded mode`, na regra dos controles TME em `tablet.css:442`; o teste exige ausência. |',
'',
f"Os schemas e assets implicados são byte a byte iguais entre baseline e R1; a sondagem dos dois modelos/arquivos também é igual: {link('nonformal-evidence.json')}. Não se atribui a divergência 3 versus 50 a uma mudança de Pydantic sem evidência; ela é uma incompatibilidade preexistente entre schema salvo e modelo compartilhado. Nenhum desses contratos foi corrigido nesta tarefa.",
'',
'Uma repetição adicional dos dois testes semânticos na **mesma baseline**, sem mudar código, voltou a produzir fingerprints estritos diferentes e fingerprints normalizados iguais. Isso confirma que esses IDs variam independentemente de R1. A sondagem está em `baseline-semantic-repeat-results.json` e não aumenta o denominador dos 105 pares.',
'',
'## 5. Regressão Dynamic R1 e contratos compartilhados',
'',
f"Dynamic DY1–DY7 + R1 no código atual: **{counts(c['dynamic_r1_counts'])}**. Há **{len(new_r1)} testes novos exclusivos do R1**, com resultados `{json.dumps(s['contracts']['r1_only_counts'])}`. Contratos compartilhados no R1: **{counts(c['shared_r1_counts'])}**.",
'',
'Os 16 módulos compartilhados cobrem Assessment, Submission, TranscriptionVersion, bridge de auditoria, decisões do professor, compatibilidade dos modelos, prova multiquestão, auditoria por questão, reanálise, confirmação humana, finalização, grader híbrido, integração aceita, certificação e leitura do workspace/auditoria. São os contratos existentes, sem novas expectativas ou fixtures de captura.',
'',
f"Foram comparados **{c['common_node_count']} node IDs comuns** das seleções de contratos, com classificações `{json.dumps(c['paired_counts'],sort_keys=True)}`. Os novos testes R1 não foram artificialmente copiados para a baseline. Os pares formais já presentes nos 105 não são contados duas vezes como novas regressões. Evidências: {link('contracts-comparison.json')}, {link('baseline-contracts-results.json')}, {link('r1-contracts-results.json')}.",
'',
'Os dois skips correspondem a `test_real_smoke_dry_run_separates_semantic_hashes_from_transport` e `test_transport_builder_does_not_weaken_holdout_guard`, ambos em `test_tme_model_compat.py`. O motivo existente é `Frozen local DEV pack unavailable`: os dois arquivos DEV requeridos não existem em nenhum dos worktrees. Evidência: `skip-evidence.json`. Os hashes dos 23 módulos comuns são idênticos (`contracts-inputs.json`). Skips não contam como passes nem como validação executada.',
'',
'## 6. Limites e estado final',
'',
'A atribuição responde à origem observável das 105 falhas e aos contratos reexecutados. Preexistente significa reproduzida no código anterior ao R1 sob o ambiente desta auditoria; não se inferiu a data histórica em que a falha começou. Não transforma a suíte completa em verde e não garante ausência de defeitos em caminhos bloqueados por Mathlib indisponível. A comparação inclui a mesma falha, o mesmo ponto de asserção, os mesmos dados de erro e os mesmos fontes Lean; não é uma validação formal bem-sucedida.',
'',
'HOLDOUT_V2 não foi iniciado. Não houve correção de Mathlib, captura, UI, expectations ou código de produto; tampouco `git add`, commit, reset ou checkout destrutivo. O worktree temporário destacado foi criado conforme a autorização desta tarefa. Os relatórios e evidências históricos permanecem intactos.',
'',
f"`git status --short` ao fechamento (também em {link('status-final.txt')}):",
'',
'```text',i['status_final'].rstrip(),'```',
'',
f"Resumo estruturado: {link('summary.json')}. Manifesto de integridade dos entregáveis: {link('artifact-manifest.json')}.",
'',
f"NEW_R1_REGRESSIONS = {s['NEW_R1_REGRESSIONS']}",
'',verdict,
]
P.write_text('\n'.join(lines)+'\n')
summary={**s,'verdict':verdict,'baseline_sha':i['head_before'],'product_code_preserved':True,'holdout_v2_started':False,'integrity_checks_passed':i['all_checks_passed'],'report':str(P),'original_full_suite_counts':{'passed':3009,'skipped':47,'failed':105}}
(O/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
files=sorted(p for p in O.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact-manifest.json')
manifest={'schema':'r1-attribution-artifacts.v1','files':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files+[P]}}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'report':str(P),'verdict':verdict,'NEW_R1_REGRESSIONS':s['NEW_R1_REGRESSIONS'],'artifacts':len(manifest['files'])}))
