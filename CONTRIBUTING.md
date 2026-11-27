# Desenvolvimento colaborativo

Comece pelo [guia](docs/collaboration/README.md) e pelo [inventário](docs/collaboration/INVENTORY.md). O remoto é público. Não incluir credenciais, `.env`, imagens de avaliações reais, identidades de estudantes, runtime operacional ou gold humano reservado, nem em commits que serão removidos depois: o histórico também é publicado.

1. Atualize a `main` com `git pull --ff-only` em um worktree limpo e crie `codex/<tarefa>` a partir dela. A `main` é a referência integrada e testada para Rian, Luis e os demais colaboradores. Branches de desenvolvimento existentes podem continuar, mas alterações aprovadas devem retornar regularmente à `main` por PRs rastreáveis. Mudanças independentes devem ter commits separados.
2. Registre o defeito ou objetivo, as evidências, o escopo e os testes. Diferencie fixtures, providers simulados, replay arquivado e inferência real.
3. Preserve a tag `SPECIALIZED-TME2-RC1`, seu commit e a branch congelada `codex/dec10-functional-integration`. Correções posteriores exigem nova branch e, se necessário, nova candidata; não mover a tag nem fazer amend/rebase do snapshot.
4. Execute os testes pertinentes offline. Chamadas pagas precisam de autorização e orçamento próprios. Não ajustar pautas, pontuações ou gold para fazer um teste passar.
5. Revise `git diff`, `git diff --cached` e os arquivos novos; use caminhos explícitos em `git add`. Revise também o histórico novo antes de publicar. Não usar `git push --all`, `--mirror` ou force push neste fluxo.
6. Abra PR contra `main`, com comportamento anterior/posterior, validação e limitações. A integração depende de revisão humana e testes aprovados; não fazer merge com conflitos ou regressões bloqueantes. Não mover tags científicas para acompanhar a `main`. Não usar force push.

Não transportar runtimes entre ambientes como se fossem código. Armazenamentos do piloto, instituições e testes devem ser distintos. Alterações de UI preservam autorização do servidor, isolamento por caso e espaço do caderno. Ausência de sessão, erro técnico e ausência de evidência matemática são estados diferentes.

O gold independente deve ficar fora do repositório e inacessível ao processo corretor. Resultados devem registrar commit, fingerprint, política, rubrica, configuração do provider, custo, latência e modalidade da evidência. Concordância entre agentes não equivale a prova formal.

## Verificações obrigatórias para integração

- `git diff --check`; revisão do diff e de todo histórico novo destinado ao remoto público.
- Regressão Python pertinente, incluindo autorização, isolamento, persistência e contratos compartilhados; para consolidações, `python -m pytest -q -rs tests`.
- `node --test tests/js/*.cjs`; para mudanças de interface, percursos reais no navegador e teclado, incluindo login, sessão e retornos.
- Providers pagos desabilitados e credenciais ausentes dos processos de teste. Informar separadamente mocks, execuções reais, skips e dados externos indisponíveis; não ocultar falhas.
- Alterações em contratos de captura, transcrição, AuditService, rubricas, revisão ou divulgação exigem revisão explícita do impacto em SPECIALIZED e nos três contextos DYNAMIC, compatibilidade de registros antigos e regressões dos dois caminhos. Não reescrever dados históricos.

Tags científicas identificam snapshots congelados e reproduzíveis; não são rótulos móveis de desenvolvimento. A tag `SPECIALIZED-TME2-RC1` permanece intacta. A preparação DYNAMIC-RC1 ainda não é uma tag nem validação independente. Smoke com providers reais requer autorização e orçamento próprios.
