# P2-CAP-03A — transcrição versionada

Este incremento cobre somente a representação textual/matemática do manuscrito recebido e sua revisão humana.

## Limite semântico

`ACCEPTED` significa: **a revisão foi aceita como representação fiel do manuscrito original**.

`ACCEPTED` não significa que a solução está matematicamente correta. O fluxo não produz nota, `score`, `verdict`, rubrica, feedback, claims ou execução Lean. Uma afirmação falsa no manuscrito, como `2 + 2 = 5`, deve permanecer falsa na transcrição.

## Persistência e versionamento

Cada transcrição pertence a uma `submission_id` exata e é persistida separadamente:

```text
runtime/submissions/<submission_id>/
  submission.json
  snapshot.json
  page_*.png
  receipt.json
  transcriptions/<transcription_id>/
    transcription.json
    revisions/revision_000001.json
    revisions/revision_000002.json
    acceptances/acceptance_000002.json
```

Revisões são snapshots completos e imutáveis de segmentos. Uma nova leitura corrigida cria o próximo arquivo de revisão, com referência à revisão anterior, momento, referência não verificada do revisor, tipo e motivo opcional. O aceite é um evento separado e imutável; ele não reescreve a revisão nem os artefatos da Submission.

Não existe autenticação neste incremento. `reviewer_reference` é declarada pelo cliente e `reviewer_identity_verified` permanece sempre `false`.

## API

- `POST /submissions/{submission_id}/transcriptions` cria a transcrição manual e a revisão 1.
- `GET /submissions/{submission_id}/transcriptions` lista as transcrições e suas revisões mais recentes.
- `GET /transcriptions/{transcription_id}` consulta revisões e eventos de aceite.
- `POST /transcriptions/{transcription_id}/revisions` salva uma nova revisão sem sobrescrever a anterior.
- `POST /transcriptions/{transcription_id}/accept` aceita a fidelidade de uma revisão ao manuscrito.

Somente `source="manual"` pode ser criado agora. O contrato central reserva `mathpix_strokes`, `mathpix_image` e `vision_model` para integrações futuras, sem atribuir reconhecedor ou confiança à origem manual.

## Integridade da fonte e limites de transporte

Antes de criar transcrição, criar revisão ou aceitar uma revisão, o store executa
`assert_submission_integrity` dentro do lock exclusivo. A verificação confere
SHA-256 e tamanho de `snapshot.json` e de todos os PNGs esperados, a consistência
entre `submission.json` e `receipt.json`, o contrato do snapshot e a correspondência
das referências de página com o snapshot. Artefatos ausentes, divergentes ou uma
estrutura inconsistente retornam **HTTP 409**, coerente com o conflito de integridade
já usado pela API. Nenhum arquivo de transcrição, revisão ou aceite é publicado
nesses casos, e os originais não são reparados. Submissões inexistentes continuam
retornando 404; falhas de acesso ao armazenamento retornam 503.

As consultas continuam disponíveis para diagnóstico: `/submissions/{id}` expõe os
hashes esperados, atuais e `matches` para artefatos; metadados inválidos são sinalizados
como erro. O histórico existente permanece consultável quando há divergência de
snapshot/PNG, mas qualquer mutação fica bloqueada.

Os três endpoints POST de transcrição possuem limite total de **8 MiB (8.388.608
bytes)**, inclusive JSON, whitespace, metadados e escapes UTF-8. Esse teto comporta
os segmentos manuais de até três páginas do MVP e mantém o consumo de memória de
cada body limitado. Os limites individuais continuam vigentes: até 2.000 segmentos,
20.000 caracteres por `text` e 20.000 por `latex`; a combinação de todos os máximos
individuais não garante que o body caiba no limite total.

O middleware ASGI conta os bytes efetivamente recebidos antes de entrar no FastAPI,
sem confiar em `Content-Length`. Até exatamente 8 MiB é permitido; acima disso a
leitura é interrompida e retorna **HTTP 413**, sem chamar o store nem publicar
arquivos. O limite não altera o transporte original das submissões.

## Roteiro de validação manual

1. No tablet, envie um manuscrito que contenha propositalmente `2 + 2 = 5`.
2. Na Área do Professor, abra **Manuscritos recebidos**.
3. Navegue até a página e crie um segmento matemático com `2 + 2 = 5`.
4. Salve a primeira revisão.
5. Altere somente um erro fictício de leitura em outro segmento, informe o motivo e salve uma nova revisão.
6. Abra o histórico e confira que as duas revisões continuam disponíveis.
7. Aceite a revisão final como fiel ao manuscrito.
8. Confirme que a tela explica a semântica de `ACCEPTED` e não mostra nota ou veredito.
9. Confira que `snapshot.json` e `page_*.png` mantêm os hashes anteriores.
