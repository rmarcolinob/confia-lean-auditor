# Desenvolvimento colaborativo

Comece pelo [guia](docs/collaboration/README.md) e pelo [inventário](docs/collaboration/INVENTORY.md). O remoto é público. Não incluir credenciais, `.env`, imagens de avaliações reais, identidades de estudantes, runtime operacional ou gold humano reservado, nem em commits que serão removidos depois: o histórico também é publicado.

1. Escolha a frente: `codex/dynamic-development`, `codex/interface-review` ou `codex/interface-video`. Crie sua própria branch `codex/<tarefa>` a partir dela. Mudanças independentes devem ter commits e PRs separados.
2. Registre o defeito ou objetivo, as evidências, o escopo e os testes. Diferencie fixtures, providers simulados, replay arquivado e inferência real.
3. Preserve a tag `SPECIALIZED-TME2-RC1`, seu commit e a branch congelada `codex/dec10-functional-integration`. Correções posteriores exigem nova branch e, se necessário, nova candidata; não mover a tag nem fazer amend/rebase do snapshot.
4. Execute os testes pertinentes offline. Chamadas pagas precisam de autorização e orçamento próprios. Não ajustar pautas, pontuações ou gold para fazer um teste passar.
5. Revise `git diff`, `git diff --cached` e os arquivos novos; use caminhos explícitos em `git add`. Revise também o histórico novo antes de publicar. Não usar `git push --all`, `--mirror` ou force push neste fluxo.
6. Abra PR contra a frente acordada, com comportamento anterior/posterior, validação e limitações. A integração na `main` depende de revisão humana. Não fazer merge automático.

Não transportar runtimes entre ambientes como se fossem código. Armazenamentos do piloto, instituições e testes devem ser distintos. Alterações de UI preservam autorização do servidor, isolamento por caso e espaço do caderno. Ausência de sessão, erro técnico e ausência de evidência matemática são estados diferentes.

O gold independente deve ficar fora do repositório e inacessível ao processo corretor. Resultados devem registrar commit, fingerprint, política, rubrica, configuração do provider, custo, latência e modalidade da evidência. Concordância entre agentes não equivale a prova formal.
