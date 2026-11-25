# ConfIA — vídeo institucional animado

Projeto audiovisual isolado em Remotion + React + TypeScript + SVG. **1920 × 1080, 30 fps, 180 segundos, sete cenas.** O aplicativo ConfIA não é importado nem alterado; referências visuais foram copiadas e documentadas.

## Arquivos de entrega

- `output/confia-institucional-180s.mp4`: filme completo, H.264/AAC, legendas abertas em português.
- `output/confia-previa-30s.mp4`: primeiros 30 segundos do filme, com narração e trilha.
- `qa/amostra-6s.mp4`: amostra de escrita/fórmulas (51–57s), renderizada e revisada antes do filme.
- `output/legendas-pt-BR.srt` e `.vtt`: legendas externas do filme completo.
- `docs/storyboard.md`: storyboard das sete cenas.
- `docs/narracao.md`: roteiro completo com tempos.
- `docs/identidade-visual.md`: referências, paleta, tipografia, marca e maturidade funcional.
- `docs/licencas-e-origem.md`: origem da identidade, voz, trilha e dependências.
- `qa/`: quadros de revisão, relatórios de áudio e metadados dos vídeos.

## Executar

Todos os comandos devem partir desta pasta. Node.js 22+ (validado em 24), npm, Python 3, FFmpeg/FFprobe e Chrome/Chromium são necessários. A síntese de voz fornecida usa `say` no macOS com Luciana pt-BR. A renderização usa o Chrome instalado; defina `CHROME_EXECUTABLE` em outros ambientes.

```sh
cd /Users/LinMarcolino/Documents/confia-lean-auditor/video-institucional
npm ci --cache ./.npm-cache --no-audit --no-fund
npm run audio
npm run check
npm run qa
npm run sample
npm run preview
npm run render
```

`npm run render` também atualiza a prévia copiando os primeiros 30s do filme final, sem recompressão de imagem.

`npm run studio` abre a edição interativa do Remotion. A composição se chama `ConfIA`. Alterações de roteiro e timing: `src/narration.json` e `src/timeline.json`. Execute novamente `npm run audio` após alterar a narração. Para checar apenas quadros específicos: `QA_TIMES=5,112 npm run qa`.

A instalação usa dependências fixadas em `package-lock.json`. O cache fica nesta pasta. `node_modules`, cache, áudios gerados e renderizações não entram no Git por padrão, mas estão presentes nesta entrega local. Copie a pasta inteira ou gere um pacote de entrega incluindo os arquivos `output/` e `public/audio/` quando for transferir o vídeo.

## Áudio e legenda

A voz é sintética (Luciana, instalada no macOS), não uma locução humana. São 26 falas independentes, normalizadas e posicionadas em janelas sem acumular deriva. O script recusa compressão de fala superior a 1,35×. `public/audio/narracao.wav` e `trilha-original.wav` são as faixas separadas; `mix.wav` é a mixagem estéreo de 180s.

A trilha ambiente é original e sintetizada pelo próprio script, sem samples externos. O nível é reduzido durante as falas; o mix tem controle de picos. As legendas são renderizadas no vídeo e também exportadas para SRT/VTT. Não ative as externas se desejar evitar texto duplicado em um player que já mostra as abertas.

Para voz humana ou outro sintetizador: mantenha as janelas em `src/narration.json`, grave uma faixa de 180 segundos com silêncio entre falas e substitua `public/audio/narracao.wav`. Faça a mixagem abaixo; `mix.wav` é a única entrada de áudio exigida pelo renderizador.

```sh
ffmpeg -y -i public/audio/narracao.wav -i public/audio/trilha-original.wav \
  -filter_complex '[0:a][1:a]amix=inputs=2:normalize=0,alimiter=limit=0.89:level=false,apad,atrim=duration=180' \
  -ar 48000 -ac 2 public/audio/mix.wav
```

Em outro sistema operacional, use as faixas já entregues ou gere a locução externamente. Não é necessário instalar um serviço pago para renderizar. Sem locução disponível, o roteiro temporalizado continua completo; não substitua o áudio por silêncio sem identificar a versão como sem narração.

## Identidade e limites da demonstração

A marca tipográfica ConfIA e o monograma C/IA reproduzem a implementação HTML/CSS do projeto. Não foram encontrados arquivos oficiais de logos UFPI, FAPEPI ou SIA; o usuário confirmou que não os tinha disponíveis. Por isso, o encerramento traz os nomes das instituições. Para inserir logos depois, copie os arquivos oficiais para `public/assets/` e preencha `institutionAssets` em `src/Film.tsx`, preservando as proporções.

Todo o exemplo é ilustrativo, incluindo a devolutiva. Nenhuma auditoria, chamada de IA/OCR ou execução do Lean acontece no filme. A análise matemática, a formalização e a verificação são identificadas separadamente; proposição não verificada não é tratada como falsa. A sequência inicial é intencionalmente incorreta: a passagem elimina `/2`; a correção resulta em 210. O vídeo distingue recursos implementados, demonstrações e desenvolvimento, com evidência no documento de identidade.

## Validação

`npm run check` verifica TypeScript, cobertura contínua das sete cenas, duração, janelas da narração, aritmética, temporização dos áudios e hashes dos arquivos visuais de origem. `npm run qa` renderiza 20 quadros para inspeção visual; `npm run sample` valida movimento e áudio antes do filme completo. `scripts/verify.py` inspeciona os MP4s via FFprobe, contagem de quadros e decodificação integral.

```sh
python3 scripts/verify.py
```

A configuração principal, módulos, dependências e componentes do ConfIA não foram modificados. Os três arquivos não rastreados já existentes fora desta pasta foram preservados.
