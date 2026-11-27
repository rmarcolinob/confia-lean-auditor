# Recibo do congelamento experimental

Este documento registra o estado posterior à preparação descrita em `docs/audits/SPECIALIZED_TME2_RC1.md`, sem editar o snapshot congelado.

| Identificação | Valor |
| --- | --- |
| Commit | `c03403fe5b83d9db9df172882bd69af3dfa2d027` |
| Tag anotada | `SPECIALIZED-TME2-RC1` |
| Objeto da tag | `0c64e318a26e21f71fe3097c66ee17a5206dd8a3` |
| Branch congelada | `codex/dec10-functional-integration` |
| Fingerprint | `tme-integration.v1:2da7a5bd4d0cd615fd06993b9e7e45fa86c27b6778476724882d65342526b9da` |
| Política | `semantic-b-minimal.v1` |
| Diagnóstico | `tme-review-diagnostics.v1` |
| SHA-256 do manifesto | `02ce578d99a62981706e40b961fa0a83c5f68dae561176f29bc86ce52530978b` |
| SHA-256 do bundle | `e9d5801d5b77dbcc2673bb371addee727b72906d9895080a79523502812a9ff3` |

O manifesto está em `docs/audits/assets/specialized-tme2-rc1/manifest.json`. O bundle tem 383195 bytes e 65 membros, em `artifacts/releases/SPECIALIZED-TME2-RC1/references.tar.gz` no worktree original de integração. Está ignorado e fora do histórico Git. Nenhum push deste trabalho inclui esse bundle.

## Recuperação controlada

Solicitar ao mantenedor a cópia exata do bundle por canal de armazenamento controlado. Ainda não há URL de distribuição controlada registrada; o clone público sozinho não recupera essas referências. Não anexar o bundle a issues, PRs ou releases públicos. O mantenedor deve conservar cópia de segurança externa; a existência e a recuperação dessa cópia não foram atestadas nesta tarefa.

Conferir o SHA-256 antes de colocar o arquivo no caminho acima de um checkout dedicado da tag. Não extrair por cima de runtime existente. Os JSONs conservam caminhos históricos internos; verificar bytes não equivale a importar um runtime operacional em outro computador.

```sh
git worktree add --detach ../confia-rc1 SPECIALIZED-TME2-RC1
cd ../confia-rc1
git rev-parse HEAD
shasum -a 256 artifacts/releases/SPECIALIZED-TME2-RC1/references.tar.gz
PYTHONPATH=app python scripts/evaluation/verify_specialized_tme2_rc1.py --environment
```

Usar o interpretador e dependências do manifesto; `python` acima representa esse ambiente, não o Python arbitrário do sistema. No host de preparação foi usado o `.venv/bin/python` do repositório principal. Verificador aprovado novamente em 25/11/2026: 754 arquivos, 65 membros, fingerprint idêntico, ambiente conferido, zero auditorias e zero chamadas de API.

P1 original permanece `null`; replay arquivado produz 17/20. P2–P5 preservam 20/20 nas fixtures integradas. Gold humano independente, resoluções independentes e captura manuscrita continuam sem validação. A cobertura Lean é parcial. A candidata não está aprovada para correção oficial do torneio.
