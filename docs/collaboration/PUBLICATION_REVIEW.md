# Revisão para publicação

Escopo inicial: histórico alcançável da RC1, DYNAMIC e quatro branches UI históricas. Foram lidos **140 commits, 3843 blobs e o objeto da tag**, totalizando 95.419.612 bytes. A revisão incluiu arquivos apagados do HEAD, metadados, padrões de chaves/tokens/credenciais, correspondência com segredos ativos conhecidos e nomes de arquivos sensíveis. Nenhum arquivo `.env` foi encontrado nesse conjunto.

Os 23 apontamentos de padrões são valores artificiais de testes de autenticação/redação de segredos e exemplos de bibliotecas Python antigas. Não foram identificadas credenciais operacionais. O arquivo histórico `r1-before.tar.gz` foi aberto em memória: 38 membros de código, benchmarks controlados e relatórios; nenhum candidato a segredo encontrado. Ele é diferente do bundle externo da RC1, que não está no Git.

Foram examinadas as 106 imagens alcançáveis: figuras preparadas de problemas, uma imagem artificial vazia e capturas de interface de ensaios documentados. Os PDFs de demonstração identificam dados sintéticos; `invalido.pdf` é o teste deliberado de PDF inválido. Os relatórios DY3–DY7 documentam soluções/participantes sintéticos; as capturas mostram códigos de demonstração e não imagens de avaliações reais identificáveis. Os registros iniciais do auditor contêm exercícios/claims de teste. Não foi encontrado material pessoal de estudantes nesse conjunto revisado.

A análise por padrões e a revisão de proveniência não constituem prova absoluta de ausência de dados sensíveis. Não autorizam publicação futura de runtimes, gold reservado ou novas capturas. O escopo de evidência científica também não se amplia por publicar o código.

Há arquivos `.venv/` e `artifacts/runs/` em commits antigos já alcançáveis por referências remotas, embora removidos da árvore atual. Os candidatos de credencial nesses arquivos são exemplos de dependências. Essa dívida de higiene do histórico fica registrada; não foi feita reescrita que alterasse a identidade da RC1.

O remoto GitHub foi confirmado público, com permissão de push da conta proprietária. O mantenedor determinou conservar a visibilidade anterior. A publicação é limitada às referências explicitamente revisadas; não inclui o bundle externo, os diretórios operacionais ou os experimentos brutos não rastreados. Os novos commits de colaboração só acrescentam documentação; o vídeo fica em branch separada e passa por revisão específica antes do envio.

Os detalhes locais (OIDs, candidatos sem seus valores, inventário por worktree e material de inspeção) estão em `artifacts/collaboration-publication-20261125/`, ignorado pelo Git. A seleção final de refs é verificada novamente por `git ls-remote`; nenhuma alteração na visibilidade, force push ou merge na `main` faz parte da operação.
