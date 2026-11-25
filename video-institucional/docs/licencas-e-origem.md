# Origem dos materiais

- Identidade ConfIA: reprodução dos elementos HTML/CSS já existentes no repositório, com referências e hashes em `asset-manifest.json`. Nenhum direito sobre as marcas institucionais é reivindicado.
- UFPI, FAPEPI, SIA: somente nomes em texto. Logomarcas oficiais não estavam disponíveis no repositório ou com o usuário.
- Ilustrações e traços de caneta: SVG e geometria originais criados para este vídeo. Ícones simples seguem a linguagem linear do piloto.
- Trilha: composição e síntese originais em `scripts/audio.py`, sem samples de terceiros. O código e a composição são disponibilizados ao projeto ConfIA sob CC0-1.0, na extensão dos direitos que possam ser concedidos sobre esta contribuição. Essa declaração não se aplica às marcas, ao sintetizador vocal nem às dependências.
- Voz: saída do sintetizador local Apple/macOS, voz Luciana pt-BR, sem clonagem de pessoa real. Não é atribuído caráter CC0 ao software ou à voz do fornecedor; seu uso segue os termos do macOS instalado. O roteiro e as faixas separadas permitem regravar a voz.
- Tipografia: fontes de sistema do computador; nenhum arquivo de fonte proprietário foi copiado ou redistribuído.
- Remotion, React, TypeScript e dependências: versões fixadas em `package-lock.json`; licenças nos respectivos pacotes. Consulte as condições de uso de Remotion para o contexto organizacional antes de novas utilizações. Não foi adicionada dependência ao aplicativo principal.

Referências técnicas consultadas: [Remotion — áudio](https://www.remotion.dev/docs/media/audio), [Remotion — bundle](https://www.remotion.dev/docs/terminology/bundle), [Remotion — renderMedia](https://www.remotion.dev/docs/renderer/render-media). A implementação usa bundler/renderer local e `staticFile` para áudio; não envia a solução matemática a serviços externos.
