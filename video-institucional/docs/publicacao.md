# Preservação das fontes para colaboração

Branch `codex/interface-video`, baseada em `1b3daea41ba4ce31c0cfd35dd07907da3d03669f`, a revisão exata referenciada em `asset-manifest.json`. Os 30 arquivos anteriormente não rastreados foram copiados byte a byte do worktree principal, sem alterar seus originais. Este documento é o único acréscimo à entrega audiovisual.

Esta branch é separada da aplicação integrada e da tag `SPECIALIZED-TME2-RC1`. Não fazer merge integral sobre a RC1 para transportar o vídeo: revisar a pasta audiovisual em PR próprio. Os hashes em `scripts/check.mjs` conferem referências da base original; não trocar esses hashes apenas para aceitar outra interface.

Foram revisados código, dependências declaradas, roteiro, origem dos materiais e storyboard. O exemplo matemático é ilustrativo e não contém avaliação de aluno real. Não há chamada a LLM, OCR ou Lean. Nenhuma credencial foi identificada nas fontes. Renderizações, áudios gerados, cache npm e `node_modules` permanecem fora do Git.

`npm run check` foi executado no ambiente original com dependências já instaladas; a verificação de timeline e hashes também foi executada nesta cópia. A instalação em clone novo exige `npm ci` e os pré-requisitos documentados no README. Não houve nova renderização nem nova medição de áudio nesta organização. Os resultados de renderização anteriores são históricos, não revalidados nesta etapa.

Roteiros, fontes e ferramentas permitem gerar os materiais. A voz depende do sintetizador local indicado e de seus termos; para outras plataformas, usar uma locução autorizada. MP4s e faixas locais não foram publicados no repositório.
