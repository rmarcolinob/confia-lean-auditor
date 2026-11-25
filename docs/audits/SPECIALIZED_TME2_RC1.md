# SPECIALIZED-TME2-RC1

Versão candidata experimental do corretor SPECIALIZED–TME², preparada em
25 de novembro de 2026 para avaliação independente com gold humano. A candidata
identifica código, pautas, ambiente e evidências; não autoriza correção oficial
do torneio. Não houve mudança matemática nesta preparação.

## Escopo e resultado da verificação

O commit base é `afa82c38b26132c9ba90b74bf6984a9867bd9623`, na branch
`codex/dec10-functional-integration`. A candidata inclui mudanças ainda não
commitadas da projeção `tme-review-diagnostics.v1`; o commit base sozinho não
reproduz a RC1. Nenhum commit ou tag foi criado nesta etapa.

O fingerprint do auditor é
`tme-integration.v1:2da7a5bd4d0cd615fd06993b9e7e45fa86c27b6778476724882d65342526b9da`.
A política é `semantic-b-minimal.v1`. O manifesto registra também os hashes de
arquivos que não entram nesse fingerprint, incluindo pautas, enunciados,
configuração Lake, testes e protocolo experimental.

O teste `test_real_local_lean_status_certificates_preserved` havia sido excluído
por seleção explícita (`-k 'not real_local_lean_status_certificates_preserved'`),
para restringir a rodada anterior. Não era um skip por incompatibilidade nem
uma falha conhecida. Sua execução isolada passou: **1 teste em 33,55 segundos**.
O teste usa um caso sintético temporário de P2, comprova `4! = 24`, refuta
`2^4 = 8`, conserva dois certificados e confirma que a adulteração de uma cópia
temporária impede a leitura. Não altera os certificados históricos.

Os 971 testes da rodada anterior permanecem evidência dessa rodada, não uma
nova execução integral. Nesta preparação, a verificação dirigida passou com
**55 testes em 23,15 segundos**, cobrindo replay, projeção, autorização,
isolamento e fechamento de prova. As consultas HTTP sobre os cinco registros
históricos retornaram 200; as consultas por outro caso retornaram 404 e as
institucionais sem sessão retornaram 401, sem mudar os 65 arquivos de referência.
Os resultados estão nos logs e no manifesto. Todos os providers dos testes são simulados,
indisponíveis ou respostas arquivadas; o teste isolado usa Lean local real.

| Evidência | Nota | Alcance |
| --- | ---: | --- |
| P1 original persistido | `null` | Falha histórica conservada; `d.middle_choices` bloqueia a nota. |
| P1 replay offline | 17/20 | Reutiliza 13 respostas GPT reais arquivadas, sem nova inferência. |
| P2 integrado | 20/20 | Fixture estruturada; alternativas não bloqueantes. |
| P3 integrado | 20/20 | Fixture estruturada; alternativa não bloqueante. |
| P4 integrado | 20/20 | Fixture estruturada; auditoria técnica posterior. |
| P5 integrado | 20/20 | Fixture estruturada; alternativas e carry-forward inaplicável. |

A projeção separa nota determinada, incerteza relevante, alternativas
dispensáveis, revisão de evidências semânticas e exigência humana explícita.
Ela não altera `needs_review`, `verdict`, pontos ou dados persistidos. As consultas
`GET /submission-audits/{audit_run_id}/diagnostics` e
`GET /tme/cases/{case_id}/audits/{audit_run_id}/diagnostics` preservam os controles
de acesso existentes. A segunda exige vínculo entre caso e submissão; o piloto
não obtém acesso institucional por selecionar um módulo.

## Limites científicos

- A correção de soluções independentes ainda não foi validada.
- A captura manuscrita, o reconhecimento e a cadeia imagem–transcrição–nota
  ainda não foram validados nesta bateria.
- P1 é replay de respostas reais, não nova execução integrada com GPT.
- P2–P5 são execuções integradas sobre fixtures estruturadas. Seus 20/20 não
  estimam acurácia sobre a população de participantes.
- Lean verifica proposições locais. Não há formalização global dos cinco
  problemas; relações aceitas pelo contrato preparado não viram teoremas Lean
  por associação com uma etapa verificada.
- `gpt-6.1-sol` é o identificador solicitado/retornado disponível. Não há
  snapshot remoto imutável registrado nem garantia de resposta idêntica em uma
  chamada futura. O replay das respostas arquivadas é uma modalidade distinta.
- `human_review.required=null` significa desconhecido. Em provas com vínculo
  explícito, a regra atual exige confirmação; seu cumprimento depende do
  histórico de HumanDecision, que não é inferido do AuditRun.

## Manifesto e materiais

O [manifesto técnico](assets/specialized-tme2-rc1/manifest.json) e seu
[checksum](assets/specialized-tme2-rc1/manifest.sha256) identificam:

1. Commit base, estado do worktree e diferenças anteriores ao registro em Git.
2. Fingerprint, política, prompt, schema do provider e projeção diagnóstica.
3. Pautas P1–P5, alias interno de P1, máquina auxiliar de P3 e hashes dos assets.
4. Python e pacotes observados, Lean, Lake, Mathlib e demais dependências Lake.
5. Configuração efetiva do provider, limites de chamada e metadados históricos.
   Segredos não são serializados; presença de credencial não comprova
   disponibilidade remota. O provider está desabilitado nesta preparação.
6. Inventário de código/testes/documentos, logs, registros e artefatos de referência.

`python-environment.txt` contém versões observadas dos pacotes, sem URLs privadas,
tokens ou caminhos de instalações editáveis. É um inventário fixado por versão,
não um lock de wheels com hashes. A reprodução estrita do ambiente observado é
macOS/arm64 e Python 3.9.6; outra plataforma exige nova verificação explícita.

Os nove repositórios de dependências Lake locais estão limpos e correspondem
ao `lake-manifest.json`. Mathlib está em
`8f9d9cff6bd728b17a24e163c9402775d9e6a365`, tag solicitada `v4.28.0`.
O manifesto registra Lean 4.28.0 e Lake 5.0.0-src+7e01a1b, inclusive suas
identificações de build.

O arquivo local
`artifacts/releases/SPECIALIZED-TME2-RC1/references.tar.gz` conserva cópias exatas
dos 65 arquivos de referência, com nomes relativos e inventário SHA-256. Não
inclui credenciais, diretórios completos de runtime ou gold futuro. O bundle
é um artefato separado e ignorado pelo Git: quem recebe somente o repositório
não recebe essas referências. Deve acompanhar a candidata em armazenamento
controlado, com o checksum registrado no manifesto.

Os JSONs históricos mantêm seus caminhos internos originais. O verificador
valida os bytes dentro do bundle sem extraí-los ou reescrever os JSONs; não
promete que esses registros possam ser importados como um runtime operacional
em outro caminho. O conteúdo matemático pode ser lido pelos modelos existentes
e inspecionado offline, preservando a identidade histórica.

## Reprodução offline

Em um checkout com os arquivos da candidata e o bundle no caminho informado:

```sh
PYTHONPATH=app .venv/bin/python scripts/evaluation/verify_specialized_tme2_rc1.py --environment
env -u OPENAI_API_KEY CONFIA_SEMANTIC_LLM_ENABLED=0 PYTHONPATH=app .venv/bin/python -m pytest -q tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved
env -u OPENAI_API_KEY CONFIA_SEMANTIC_LLM_ENABLED=0 PYTHONPATH=app .venv/bin/python -m pytest -q tests/test_tme_review_diagnostics.py tests/test_tme_archived_quote_scope.py tests/test_core_auth.py tests/test_tme_demo_auth.py tests/test_tme_finalization.py::test_unconfirmed_question_blocker_and_completion
```

O verificador não extrai o bundle, não corrige soluções e não chama providers.
Valida código, evidências, fingerprint e, com `--environment`, as versões
locais. Os testes locais P2–P5 requerem o runtime original e podem ser pulados
em outro checkout; o manifesto e o bundle permitem verificar suas evidências
mesmo nesse caso. O replay P1 portátil está em `tests/fixtures`.

Para preparar outro ambiente, instalar a versão de Python indicada e criar
`.venv`; instalar as dependências observadas do arquivo `python-environment.txt`
e o projeto local com `pip install --no-deps -e .`. Provisionar o toolchain
fixado em `lean-toolchain`, os commits de `lake-manifest.json` e seus artefatos
compilados; não executar `lake update`, pois isso pode mudar dependências.
Instalações/downloads não foram executados nesta preparação. Se pacotes ou
builds não estiverem disponíveis, registrar a divergência e não afirmar
reprodução estrita. Guardar wheels/cache de build com hashes é um passo
adicional para reprodução independente de disponibilidade dos servidores.

Para uma futura avaliação com inferência, usar explicitamente a política,
modelo e esforço de raciocínio registrados. Habilitar o provider e fornecer
credencial por mecanismo externo somente na execução posteriormente autorizada.
Não incluir credenciais na candidata. `scripts/pilot_dec10.py` configura um
piloto local de demonstração e não habilita inferência paga; não é um perfil
institucional de produção. O protocolo gold define o isolamento da avaliação.

## Registro posterior em Git

Os comandos abaixo são proposta para execução posterior. Não foram executados.
Usar a raiz do worktree de integração; conferir que não surgiram alterações
alheias e que a tag ainda não existe. Não usar `git add .`.

```sh
git switch codex/dec10-functional-integration
git status --short
git diff --check
PYTHONPATH=app .venv/bin/python scripts/evaluation/verify_specialized_tme2_rc1.py --environment
git add app/confia_lean_auditor/tme/review_diagnostics.py app/confia_lean_auditor/submission_audits/router.py app/confia_lean_auditor/tme/router.py
git add tests/test_tme_review_diagnostics.py tests/test_core_auth.py tests/test_tme_demo_auth.py tests/test_tme_finalization.py
git add scripts/evaluation/verify_specialized_tme2_rc1.py docs/audits/SPECIALIZED_TME2_RC1.md docs/audits/SPECIALIZED_TME2_RC1_GOLD_PROTOCOL.md docs/audits/assets/specialized-tme2-rc1/
git diff --cached --stat
git diff --cached --check
git diff --cached
git commit -m "Prepare SPECIALIZED-TME2-RC1 experimental evaluation candidate"
git tag -a SPECIALIZED-TME2-RC1 -m "Experimental TME2 candidate; independent solutions and handwriting not validated"
git rev-parse HEAD
git rev-parse SPECIALIZED-TME2-RC1^{commit}
git status --short
```

Antes de executar `commit`, a revisão do diff deve confirmar exatamente os
arquivos autorizados. Os hashes do manifesto referem-se ao conteúdo candidato;
o campo `base_commit` e o estado dirty são deliberadamente anteriores ao commit.
Não reescrever o manifesto para fazê-lo conter o hash do commit que o inclui:
isso criaria uma dependência circular. A tag aponta para o commit final; registrar
esse hash em recibo externo de congelamento, juntamente com o SHA-256 do
manifesto e do bundle. Nunca mover a tag para corrigir a candidata; usar RC2.
Nenhum comando de push é necessário nesta etapa.

## Parecer de prontidão

Não foi identificado bloqueio técnico para registrar a candidata experimental.
A falha histórica P1 permanece identificada, e seu replay corrigido continua
separado do registro original. A nota matemática e os estados de revisão têm
projeção diagnóstica consultável, com autorização e isolamento preservados.

O congelamento ainda depende do registro posterior em Git e da preservação do
bundle externo. A realização da avaliação depende de amostra independente,
gold adjudicado e isolado, configuração final do provider e orçamento definido
antes de qualquer chamada paga. Esses preparativos não constituem evidência de
acurácia. O desenho está no [protocolo inicial](SPECIALIZED_TME2_RC1_GOLD_PROTOCOL.md).
