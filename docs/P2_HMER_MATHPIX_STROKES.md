# P2 HMER: Mathpix digital ink

Este primeiro slice lê os strokes do `CaptureSnapshot` recebido pelo servidor. O fluxo é `CaptureSnapshot → RecognitionInput → MathpixRecognitionProvider → RecognitionRun/RecognitionResult → revisão inicial NEEDS_REVIEW → prévia no caderno`. A auditoria, o Lean e a aceitação humana permanecem fluxos separados.

## Arquitetura e contrato

O adapter `mathpix` é registrado no `RecognizerRegistry` existente quando `CONFIA_MATHPIX_APP_ID` e `CONFIA_MATHPIX_APP_KEY` estão definidos no **backend**. `fake_test` continua restrito a desenvolvimento/teste. Sem as duas credenciais, Mathpix não aparece em `/submissions/recognition-providers` e uma solicitação recebe erro configuracional seguro. `httpx` já é dependência do projeto.

Para cada página com strokes ativos, o adapter envia uma chamada a `POST https://api.mathpix.com/v3/strokes`. A conversão usa `strokes.strokes.x` e `strokes.strokes.y`, preservando a ordem dos strokes e dos pontos. Timestamps e pressão continuam no snapshot original, mas não são campos do payload Mathpix. `metadata.improve_mathpix=false` é enviado para desabilitar uso do request para melhoria do serviço. Páginas vazias são ignoradas; conteúdo de páginas diferentes nunca é concatenado antes do reconhecimento. O request tem limite de 512 KiB, conforme a [referência oficial do endpoint](https://docs.mathpix.com/reference/post-v3-strokes) e a [política de privacidade](https://docs.mathpix.com/concepts/privacy).

Uma resposta por página gera um `RecognitionSegment` com `page_index`. `text` e `latex_styled` são copiados sem correção matemática; `confidence` só é gravado se vier válido de 0 a 1. `page_metadata` guarda, quando retornados, `is_handwritten`, `version` e `request_id` por página. O campo agregado `provider_version` só é preenchido se a versão for igual em todas as páginas; `provider_request_id` agregado só é preenchido para uma página. O modelo atual não tem vínculo exato entre saída e strokes: `source_stroke_refs` e `source_region` ficam nulos, e o aviso dessa limitação acompanha o resultado. A proveniência existente guarda `submission_id`, `snapshot_id`, hashes e referência do snapshot, provider, endpoint, modo `strokes`, versão do adapter, `recognizer_run_id` e horário UTC. Não grava headers ou credenciais.

O serviço CAP-03B controla idempotência, locks, integridade, prazo total (padrão 30 s), publicação atômica e estado. Uma chave de idempotência repetida reutiliza o run, inclusive `FAILED`; para uma nova tentativa depois de falha terminal use outra chave. Falhas HTTP, timeout, JSON inválido, resposta incompleta ou acima do limite de 256 KiB não geram revisão. O adapter registra somente categoria de falha, status HTTP, duração e contagens, sem payload nem resposta integral. O timeout da chamada HTTP usa até 5 s para conexão, até 15 s para leitura e o tempo restante do deadline do CAP-03B; não há retry HTTP automático.

## Uso e teste manual

Configure as variáveis no processo do servidor, sem incluí-las em arquivos versionados:

```sh
export CONFIA_MATHPIX_APP_ID='...'
export CONFIA_MATHPIX_APP_KEY='...'
python -m uvicorn confia_lean_auditor.main:app --app-dir app
```

Abra o caderno no modo **Solução para envio**, escreva com a caneta, prepare a versão, envie e aguarde o recibo. Toque em **Reconhecer escrita**. A prévia mostra `text` e/ou LaTeX por página e a orientação **“Confira se o reconhecimento corresponde ao que foi escrito.”** A revisão inicial é sempre `NEEDS_REVIEW`. A UI não chama o provider enquanto a caneta se move. O controle funciona após o envio confirmado na sessão atual; a prévia em memória do navegador não é restaurada automaticamente após recarregar a página, mas o run fica disponível pelos endpoints de reconhecimento e transcrição.

Faça a validação manual nesta ordem, registrando somente observações técnicas e sem salvar payloads/respostas privadas no repositório:

1. `x² + 2x + 1`
2. `(a+b)² = a² + 2ab + b²`
3. `Como x² = 4, temos x = 2.`
4. Uma solução curta da ITA2025F2Q8.

Não há garantia de fidelidade da leitura: compare sempre com o manuscrito antes de qualquer aceitação humana. Este slice não implementa MyScript, benchmark científico, PNG como entrada, reconhecimento contínuo, correção automática nem integração automática com `/audit`. MyScript e um benchmark de fidelidade ficam para etapa futura.
