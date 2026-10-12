# GOV-01 — manifesto de reprodutibilidade das execuções

GOV-01 melhora rastreabilidade e reprodutibilidade observável. Não garante
reprodução bit a bit. Não substitui assinatura digital, attestation ou controle
de acesso. A mensagem institucional é **“Metadados da execução registrados.”**

## Arquitetura e momento da captura

`reproducibility/collector.py` coleta uma vez por `execute_audit`, antes de carregar
os assets validados e iniciar o pipeline. A mesma execução atende `POST /audit`
e a Audit Bridge; routers, interface, claims e checkers não coletam metadados.
O snapshot contém bytes do inventário Python e o manifesto tipado. Não inclui a
solução do aluno, nem altera claims, rubricas, verificações ou relatório.

`reproducibility/service.py` publica os arquivos no `artifact_dir`. Reutiliza
`SubmissionStore._write_atomic_new`: arquivo temporário, flush/fsync, hard link
sem substituição e fsync do diretório. Dependências e manifesto são publicados
antes de `audit.json`, que passa a ser o marcador final de publicação do resultado.
A Bridge publica seu AuditRun somente após verificar todos os arquivos exigidos.
Não há transação de diretório: interrupções podem deixar arquivos órfãos sem um
resultado/AuditRun publicado. Esses arquivos não são evidência de conclusão.

O snapshot histórico nunca é recalculado na leitura. Alterações posteriores de
código, assets ou dependências não modificam registros antigos. A captura não
bloqueia edições concorrentes entre leitura dos arquivos e execução; essa
limitação está expressa em cada manifesto. O ambiente do piloto deve ser imutável.

## Contratos e integridade

Todos os contratos novos usam Pydantic 2, `extra="forbid"` e rejeição de NaN.

- `AuditReproducibilityManifest`, schema `1.0`: UUID, data UTC, problema,
  identidade do código/aplicação, assets, configuração efetiva allowlisted,
  ambiente Python, ambiente formal e limitações.
- `AssetFingerprint`: nome lógico, caminho relativo controlado, SHA-256, tamanho,
  obrigatoriedade, disponibilidade e motivo sanitizado. Arquivos ausentes e links
  simbólicos não recebem um hash fictício.
- `ReproducibilityManifestRecord`: manifesto, hash canônico, filename fixo e tamanho.
- `ReproducibilityMetadata`: `recorded`, `unavailable` ou `legacy_unversioned`,
  com record ou categoria de falha coerente com o estado.

A representação canônica é JSON UTF-8, `ensure_ascii=False`, chaves ordenadas,
separadores `,` e `:`, sem NaN. Datetimes exigem timezone, são convertidos para
UTC e serializados com seis casas de microssegundos e sufixo `Z`. O hash cobre
somente o manifesto, sem o próprio hash. O arquivo é publicado nesses bytes.
O inventário Python tem hash dos bytes UTF-8, linhas ordenadas e newline final.
O record valida hash e tamanho canônicos; a leitura valida também os arquivos.

SHA-256 fornece integridade técnica interna. SHA-256 não é assinatura digital
nem prova de autoria. Quem puder reescrever dados e todos os hashes pode forjar
um conjunto internamente consistente. Controle de acesso e âncora externa de
confiança permanecem fora deste incremento.

## Fontes e precedência

| Informação | Fonte real e tratamento |
| --- | --- |
| Commit | `CONFIA_BUILD_COMMIT`, senão Git local quando há `.git` no root, senão indisponível |
| Dirty | `CONFIA_BUILD_DIRTY`, senão Git local, senão desconhecido |
| Build | `CONFIA_BUILD_ID`, senão indisponível |
| Projeto | Versão literal de `[project]` em `pyproject.toml`; fallback `importlib.metadata` |
| API | `versions.API_VERSION`, compartilhada por FastAPI e `/health`, preservando `0.4.0` |
| Bridge | `null`, `not_versioned`: o projeto não tinha versão independente da Bridge |
| Conversão | Default real de `AuditProvenance.conversion_version` (`segments-v1`) |
| Capture | `capture.schemas.SCHEMA_VERSION` |
| Python | `sys.version`, implementation, major/minor/micro, OS/release/machine |
| Dependências Python | `importlib.metadata.distributions()`, apenas Name/Version |
| Toolchain | Conteúdo validado de `lean-toolchain` |
| Lean/Lake | `--version` do binário já instalado do toolchain declarado, com timeout de 3 s |
| Mathlib e pacotes Lean | Revisões declaradas em `lake-manifest.json`, sem acessar Git dos pacotes |

Cada identidade registra sua fonte (`environment`, `git`, `project`, `package`,
`command`, `lake-manifest`, `unavailable`) ou motivo de indisponibilidade.
Os subprocessos são somente leitura; stdout/stderr de erro não são publicados.
Não são executados `lake update`, builds, downloads ou instalação por elan.
As consultas de versões usam diretamente binários instalados, somente quando
PATH corresponde ao shim padrão ou ao binário esperado. PATH customizado,
`ELAN_TOOLCHAIN`, overrides declarados em settings do elan e toolchains ausentes
deixam versões indisponíveis. O campo toolchain é a configuração do projeto,
não uma atestação de seleção efetiva nem do compilador que produziu um artefato.

Valores de build presentes e inválidos ficam indisponíveis, sem copiar o valor
rejeitado e sem ocultar a configuração inválida com fallback Git. Commit exige
40 ou 64 caracteres hexadecimais; dirty aceita exatamente `true`, `false`, `1`,
`0`; build ID aceita até 80 caracteres alfanuméricos, ponto, hífen e underscore,
começando por alfanumérico. Não colocar dados pessoais ou segredos em build IDs.

Exemplo de configuração de build:

```sh
CONFIA_BUILD_COMMIT=<commit-completo>
CONFIA_BUILD_DIRTY=false
CONFIA_BUILD_ID=pilot-2026-10-12
```

Build metadata é uma declaração do processo de build, não sua autenticação.
Worktree dirty recebe limitação explícita: o commit não identifica todo o código
executado. Não há fingerprint de arquivos modificados neste MVP. Git consulta
estado atual e não publica paths, nomes de arquivos ou conteúdo de diffs.

## Assets e configurações

São registrados os três JSONs do problema (`problem`, `rubric`, `microclaims`) e
`ConfiaLeanAuditor/Problems/<problem_id>/Statement.lean`, importado pelo builder.
A cópia histórica `problems/ITA2025Q1/certificate/Statement.lean` não é importada
pelo pipeline e não é incluída. Assets JSON obrigatórios ausentes continuam
rejeitados pela validação existente; o coletor não contorna essa validação.

Configurações registradas: `pyproject.toml`, `lean-toolchain`, `lakefile.toml` e
`lake-manifest.json`. Todos os paths são relativos ao projeto, sem travessia ou
links simbólicos. Prompts e templates formais reais estão no Python e são
representados pela identidade do código; não se inventam arquivos de templates.
`CONFIA_ENABLE_LLM_FORMAL_STEPS` e o modelo validado de `CONFIA_LLM_MODEL` são a
allowlist de configuração operacional. O default do modelo vem do extrator
existente. Habilitar LLM acrescenta limitação de serviço externo não determinístico.

## Ambiente Python e eficiência

`python_dependencies.txt` contém `nome-normalizado==versão`, ordenado por nome
e versão, sem duplicatas exatas. Nomes seguem normalização de hífen, underscore,
ponto e caixa; versões e nomes são validados. Não há `pip freeze`, caminhos de
instalação, `direct_url`, hostname, username, home ou `sys.path` no inventário.
Hash, tamanho, nome fixo e contagem ficam no manifesto.

Não há cache de processo neste MVP. Coleta, enumeração de dependências e no máximo
duas consultas Git e duas consultas de versões ocorrem uma vez por execução, nunca
por claim ou formal step. Assim dirty, assets e dependências são recapturados e
worktrees não compartilham estado obsoleto. Funções recebem root, ambiente e
distribuições injetáveis; testes substituem comandos sem limpar cache global.

## Integração textual, Bridge e consulta

`AuditResponse.reproducibility` é uma extensão opcional. Quando registrado,
contém status, record, manifesto e referência lógica, sem novos paths absolutos.
O motor textual publica os dois arquivos no artifact_dir interno. A resposta HTTP
passa pela projeção pública descrita abaixo. Não foi criado endpoint global de runs textuais.

AuditRun persiste também `reproducibility_status`, `reproducibility_manifest_filename`
e `reproducibility_manifest_sha256`, coerentes com o mesmo record do motor.
Manifesto e dependências integram `required_artifacts`, além dos artefatos formais
existentes. GET, listagem, consulta de metadados e retry verificam os arquivos e
retornam conflito de integridade se forem removidos, alterados ou substituídos
por links. Nenhum original do aluno é modificado.

`GET /submission-audits/{audit_run_id}/reproducibility` retorna
`PublicReproducibilityMetadata` tipado, com `Cache-Control: no-store`. O serviço
valida ID, vínculos, hashes e arquivos internos antes da projeção. ID
inválido/inexistente retorna 404; conflito retorna 409.
O retorno não inclui paths do servidor nem conteúdo da transcrição.

### Fronteira pública e integridade interna

`core/public_audit.py` concentra a projeção das respostas de `/audit`, execução/retry,
detalhe, listagem e endpoint GOV-01 da Bridge, incluindo erros e warnings.
Os modelos internos continuam sendo validados antes
da projeção e persistidos com seus paths operacionais. A API entrega `artifact_dir:
null`, `artifact_ref: audit-run:<id>` na Bridge e arquivos relativos ao artifact root,
como `formal_steps/step.lean`. A referência textual é null, pois não há um ID público
de AuditRun para esse endpoint. Subdiretórios são preservados, sem usar basename.
A existência física dos artefatos deve ser validada no domínio interno, usando o
registro persistido e seu artifact root autorizado. Referências públicas são
lógicas/relativas e não devem ser resolvidas contra o diretório de trabalho (cwd).

O arquivo precisa existir dentro do root autorizado tanto pela referência lexical
quanto após resolver symlinks. Referências externas, escapes e arquivos ausentes
viram null com `ARTIFACT_REFERENCE_UNAVAILABLE` em `public_warnings`. Os nomes,
relation IDs e hashes do manifest permanecem vinculados aos mesmos arquivos.
stdout/stderr são omitidos, com `COMPILER_DIAGNOSTICS_WITHHELD`; strings derivadas
com referências locais são ocultadas com `LOCAL_REFERENCE_WITHHELD`.

`integrity_scope: persisted_internal_record` explicita que `source_hash`,
`result_sha256`, `manifest_sha256` e `artifact_manifest_sha256` validam os registros internos. Não são
hashes do JSON público projetado; clientes não devem recalculá-los sobre essa
representação. A transformação não modifica o objeto interno nem recalcula hashes.
O endpoint específico GOV-01 usa um DTO público distinto, também presente no
resultado público de `/audit` e da Bridge. Seu `integrity_scope` é explícito em
todos os estados. O hash e `size_bytes` continuam descrevendo os bytes canônicos
internos, enquanto `record.manifest` contém a projeção sanitizada. O DTO público
não executa o validador de digest do manifesto interno sobre esses bytes diferentes.
O validador interno, a publicação, os arquivos e os hashes não foram alterados.
As respostas públicas projetadas são objetos JSON; não devem ser desserializadas
como AuditRun interno, cujos validadores exigem a representação persistida.

`sanitize_public_text` reconhece separadamente URI file, drives Windows, UNC e
paths POSIX, inclusive dentro de colchetes, parênteses, aspas, listas e mensagens
key=value. Quando identifica um path, substitui o valor textual inteiro por
`[local path hidden]`, evitando sobras de nomes com espaços. Texto arbitrário
nunca é convertido em referência de artefato. `sanitize_public_payload` percorre
dicts (inclusive chaves), listas, tuplas e contratos serializados sem modificar
as entradas. Versões e referências relativas legítimas são preservadas.

O endpoint GOV-01 aplica essa mesma sanitização também a campos livres de
plataforma, como `python_environment.release`, e sinaliza redactions em
`public_warnings`. A projeção é consistente com a metadata embutida nas outras
rotas. A UI mantém renderização por texto e explica que o JSON público pode ter
bytes diferentes do registro interno.

### Erros de domínio e UI

Erros de `/audit` são mapeados na fronteira HTTP. Asset obrigatório ausente retorna
400, `REQUIRED_PROBLEM_ASSET_MISSING` e “Um arquivo obrigatório da questão não está
disponível.”; asset inválido retorna `INVALID_PROBLEM_ASSET`. Falha de extração
formal retorna 503 e `FORMAL_EXTRACTION_UNAVAILABLE`. Requisições inválidas são
tratadas antes da entrada no endpoint sem ecoar o input. Exceções não mapeadas
retornam mensagem genérica, nunca `str(exception)`. As respostas incluem
`error_code` e `message`, mantendo `detail` para compatibilidade; o log registra
somente status e categoria fixa, sem payload, segredo, path ou traceback.
Os handlers de validação/HTTP adicionais se aplicam somente às rotas de auditoria.

Os 409 da Bridge retornam `detail` seguro e `error_code`, sem input de validação,
paths, hash esperado ou stack trace. Categorias:

| Código | Situação |
| --- | --- |
| `TRANSCRIPTION_NOT_ACCEPTED` | Transcrição não conferida |
| `SOURCE_INTEGRITY_MISMATCH` | Original, revisão ou aceite inválido |
| `RESULT_INTEGRITY_MISMATCH` | Resultado ou artefatos do resultado divergentes |
| `REPRODUCIBILITY_INTEGRITY_MISMATCH` | Manifesto, dependências ou vínculo GOV-01 divergentes |
| `REVISION_CONFLICT` | Revisão solicitada incompatível com o aceite |
| `AUDIT_RUN_CONFLICT` | Identidade ou armazenamento do run/retry incompatível |

A UI usa mensagens próprias: “A transcrição precisa ser conferida antes da análise.”,
“A fonte desta análise não passou na verificação de integridade.” e “Não foi possível
validar os metadados desta análise.”. Run stale continua exibindo “Esta análise
corresponde a uma versão anterior.”. O código fica em disclosure, e os logs do
fluxo docente contêm somente categoria/status, sem diagnósticos brutos.

`IdentifiedValue` rejeita strings vazias ou compostas somente de espaços. Null exige
source unavailable e motivo; valores válidos não são normalizados, preservando seus
bytes e os hashes dos manifestos históricos válidos.

## Runs legados e política de falha

Resultados sem `reproducibility` mantêm sua serialização original para validar
hashes históricos. Não recebem campos extras no objeto hasheado, retrohash,
manifesto reconstruído nem escrita na consulta. São apresentados como
`legacy_unversioned`; listagens seguras continuam funcionando. Retry sem nova
execution key continua retornando o registro histórico com esse estado explícito,
sem promovê-lo a execução com evidências capturadas. Uma nova execução exige a
ação existente “Executar novamente”, que envia uma nova execution key.

Falha não crítica de coleta/publicação retorna `unavailable` e categoria
`METADATA_COLLECTION_FAILED` ou `METADATA_PUBLICATION_FAILED`. O resultado
matemático é preservado, inclusive score null e veredito inconclusivo quando
determinado pelo auditor. A Bridge pode publicar COMPLETED nesse estado, sem
record nem hash declarado. Arquivos parciais não recebem referência de integridade.

Se um record já declarado registrado estiver corrompido antes da publicação
da Bridge, a execução é FAILED com `METADATA_INTEGRITY_FAILED`, nunca um erro
matemático atribuído ao aluno nem COMPLETED. Os arquivos do motor não são
apagados, mas o resultado inconsistente não é exposto como um run válido.
Uma falha do próprio motor resulta em metadados indisponíveis (`AUDIT_NOT_COMPLETED`),
sem classificar uma execução nova como legada. Corrupção após publicação bloqueia
consulta/retry com 409, sem reescrever o histórico.

## Interface, segurança e piloto

“Ambiente da análise” é um disclosure fechado no renderer compartilhado pelo
professor e demonstração textual. Mostra código/build, clean/dirty/desconhecido,
versões, ambiente formal e contagem de assets. Hashes, referências e inventários
detalhados do manifesto ficam em “Detalhes técnicos”. A lista completa de pacotes
Python permanece no arquivo de artefato; não há download público novo.
Legados exibem “Metadados de reprodutibilidade não registrados nesta execução.”

Não são coletadas variáveis arbitrárias, `.env`, headers, cookies, credenciais,
tokens, usernames ou hostname. Erros de coleta/publicação não são logados com
diagnósticos brutos. Testes injetam segredos falsos e verificam arquivos, API e
logs; testes DOM verificam renderização como texto e ocultação de paths.

Antes de um piloto institucional, o operador deve exigir metadata registrada e
completa, build identificado, ambiente sem alterações, assets disponíveis e
dependências fixadas; preservar os artefatos e restringir o acesso à API/storage.
Isso é uma política operacional documentada, não um novo gate matemático ou
mecanismo de autenticação. Versões declaradas, dependências instaladas e hashes
internos não substituem lockfiles completos, imagens imutáveis ou assinatura.

## Verificação

Testes permanentes em `tests/test_reproducibility.py` e
`tests/js/test_reproducibility.cjs` cobrem contrato, canonicalização, fontes,
determinismo, mudanças reais, captura única, integridade, privacidade, falhas,
legados, endpoint e disclosure. Regressões de semântica comparam o resultado
matemático separadamente dos metadados de execução naturalmente variáveis.
Não executar o benchmark de 500 casos para validar este incremento.


## Isolamento da auditoria e arquivos temporários anteriores

O teste `test_ui_can_load_example_and_audit_with_pedagogical_report` agora substitui
o motor por resposta controlada, proíbe subprocessos e verifica que os arquivos
reais de `artifacts/` e `.lake` não foram criados nem modificados. Os demais testes
de pipeline usados nesta revisão operam em diretórios temporários com compilador
controlado; os smokes Lean reais são explicitamente excluídos.
Os quatro casos de smoke Lean real (dois de paridade, um da Bridge e um de
semântica de provas do aluno) devem obrigatoriamente ser executados em ambiente
provisionado com Mathlib e build antes do piloto institucional. A validação
controlada não substitui essa execução real.

A auditoria anterior produziu artefatos temporários ignorados em
`artifacts/runs/20261012T134110_111446` e
`artifacts/student_claim_checks/20261012T134110_111446_student_claims`.
Esses arquivos foram preservados. Nenhuma limpeza ou alteração de `.lake` faz
parte desta correção; limpeza futura depende de autorização separada.

As regressões adicionais de privacidade e erros ficam em
`tests/test_gov01_public_api.py`; os testes CAP-04 continuam verificando hashes e
artefatos sobre o registro interno, além de comparar a projeção pública e a
semântica matemática. Não se executam benchmark de 500 casos nem instalação.

`tests/public_privacy.py` é o detector recursivo independente usado como oráculo
nos contratos HTTP. `tests/test_public_audit_boundary.py` injeta paths embutidos
em diferentes campos, testa as seis rotas, erros de assets e exceções, o DTO
publicado no OpenAPI e a preservação de todos os arquivos e hashes internos após
GET/listagem/retry. Um payload HTTP projetado também é entregue ao renderer
docente em memória para verificar o DOM, sem criar arquivo intermediário.
