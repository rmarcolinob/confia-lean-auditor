# Registro de validação audiovisual

## Antes da renderização completa

1. Identidade examinada no código existente e documentada em `identidade-visual.md`; hashes das referências em `asset-manifest.json`.
2. TypeScript compilado sem emissão e verificações de timeline, falas, aritmética e fontes executadas com `npm run check`.
3. Vinte quadros das sete cenas renderizados a 1920 × 1080. Inspeção de escrita, fórmulas, marca, texto, estados de maturidade, diferenciação IA/Lean e legendas.
4. Uma sobreposição entre avisos da auditoria foi detectada em 112s e corrigida. O quadro foi renderizado novamente e inspecionado.
5. Amostra de seis segundos (51–57s) renderizada antes do filme: 180 quadros, H.264, 1920 × 1080, 30 fps, áudio AAC. Folha de contato confirma evolução dos traços e movimento da mão.
6. Prévia de 30s renderizada. A quinta fala foi antecipada em 0,7s para terminar dentro da prévia sem cortar uma palavra. O filme final usa esse ajuste; a prévia final foi extraída do mesmo filme.

## Áudio

26 falas / 340 palavras, voz sintética Luciana pt-BR do macOS. Janelas em `src/narration.json`; duração efetiva e fator de ajuste em `qa/audio-report.json`. Nenhuma fala ultrapassou sua janela. Trilha original de síntese, sem samples de terceiros.

Medições FFmpeg do mix WAV final:

- Loudness integrado: **−18,2 LUFS**.
- Faixa de loudness: **3,5 LU**.
- Pico verdadeiro: **−8,2 dBFS**, sem clipping.
- Nível médio da voz isolada: **−18,2 dB**.
- Nível médio da trilha isolada: **−42,8 dB**.

A voz fica aproximadamente 24,6 dB acima da música em média. As medições são técnicas; não representam avaliação humana da interpretação vocal. A locução pode ser substituída mantendo os stems e as janelas.

## Integridade e reprodutibilidade

Todos os arquivos criados estão dentro de `video-institucional/`. Os arquivos do aplicativo principal permaneceram intactos. As dependências e o cache npm foram instalados somente nesta pasta. Chrome local e serviço `say` precisaram de acesso fora do sandbox para executar; nenhum módulo do ConfIA foi iniciado ou modificado.

Comandos principais executados: `npm install --cache ./.npm-cache --no-audit --no-fund`, `python3 scripts/audio.py`, `npm run check`, `npm run qa`, `npm run sample`, `npm run preview`, `npm run render`. FFmpeg gerou folhas de contato e medições; FFprobe examinou codecs e quadros.

Resultados finais de duração, contagem de quadros e decodificação ficam em `qa/verification.json`, gerado por `python3 scripts/verify.py` após a conclusão dos MP4s. Não confundir o progresso do renderizador com esse teste do arquivo final.

## Limitações declaradas

- Não há arquivos oficiais das logomarcas UFPI, FAPEPI e SIA. O usuário confirmou a indisponibilidade; os nomes aparecem em texto.
- A marca ConfIA é a composição tipográfica/monograma encontrada no frontend.
- A voz é sintética local. A revisão visual foi feita por quadros e folhas de contato, não por uma sessão humana de exibição integral.
- A demonstração não executa OCR, LLM, backend, auditoria ou Lean. A imagem do código Lean é ilustrativa e não afirma verificação executada.
- “Implementado” significa presença no código analisado; não comprova implantação, validação de impacto ou disponibilidade em produção.

## Resultado final

Validação concluída: os três MP4s passaram em FFprobe e decodificação integral com FFmpeg (`-xerror`).

| Arquivo | Duração do contêiner | Quadros | Resultado |
|---|---:|---:|---|
| `qa/amostra-6s.mp4` | 6.016 s | 180 | Aprovado tecnicamente |
| `output/confia-previa-30s.mp4` | 30.016 s | 900 | Aprovado tecnicamente |
| `output/confia-institucional-180s.mp4` | 180.011 s | 5400 | Aprovado tecnicamente |

O fluxo de vídeo completo tem exatamente 180 segundos / 5.400 quadros. Pequena extensão do contêiner decorre do empacotamento AAC. A prévia foi limitada a 900 quadros para impedir quadros extras de reordenação H.264. Não houve erro de decodificação.
