# P2-CAP-03B-1 — reconhecimento automático

`Recognizer` é o protocolo independente de fornecedor. Recebe `RecognitionInput`
com tupla de artefatos e bytes imutáveis, além de `ProviderDeadline` nas chamadas
do serviço, e retorna `ProviderOutput` segmentado.
O adapter declara provider, nome/versão do adapter, modo (`strokes`, `image` ou
`strokes_and_image`) e uma allowlist de parâmetros públicos. Factories registradas
explicitamente no `RecognizerRegistry` isolam configuração e implementação.
Os nomes `mathpix_strokes`, `mathpix_image` e `vision_model` podem ser registrados
futuramente, mas não têm implementações nesta etapa. Factories futuras poderão
ler configuração por variáveis de ambiente internamente; credenciais não fazem
parte dos contratos, da proveniência ou das respostas ao frontend.

Somente `fake_test` existe. Para habilitar API e UI, configure `CONFIA_ENV=test`
ou `CONFIA_ENV=development`. Ausência dessa variável, `production` e qualquer
outro valor desabilitam o provider. `CONFIA_SUBMISSIONS_DIR` conserva o significado
existente. Não há configuração de credenciais, SDK nem chamada externa nova.

O reconhecedor de teste devolve **sempre `2 + 2 = 5` por página**, independentemente
do conteúdo manuscrito. É um fixture determinístico para a arquitetura, não OCR.
Confiança, região, referências de strokes, versão e request ID do provider
ficam `null`. A versão conhecida é exclusivamente a do adapter.

## Operação e contratos

`POST /submissions/{submission_id}/recognitions`, JSON:

```json
{"provider": "fake_test", "idempotency_key": "opcional-acao-01"}
```

A operação chama `assert_submission_integrity` antes do adapter, copia e verifica
os bytes realmente usados, valida o resultado e mapeamentos opcionais, e revalida
a submissão antes de publicar. Nada escreve `submission.json`, `receipt.json`,
`snapshot.json` ou os PNGs originais. Strokes precisam pertencer à página e estar
ativos; regiões precisam caber na página original.

`RecognitionResult` registra run/submission/provider, versão do provider opcional,
versão do adapter, modo, horário UTC, latência medida, request ID opcional,
segmentos, warnings e hashes. `RecognitionProvenance` registra artefatos e seus
hashes/tamanhos/índices, adapter, versão, provider, parâmetros públicos e horário.
`input_hash` é SHA-256 do JSON canônico do modo e referências dos artefatos usados;
`output_hash` é SHA-256 do `ProviderOutput` normalizado, incluindo `null`, warnings
e metadados opcionais. Canonização: UTF-8, chaves ordenadas, sem espaços separadores,
Unicode literal, sem NaN. IDs e horário do run não entram no output hash.

A resposta resumida contém `recognizer_run_id`, `status`, `transcription_id`,
`revision_number`, `error_code` e proveniência. `201` significa novo run (inclusive
falha registrada), `200` significa replay. Falhas de provider retornam `FAILED`,
sem transcrição, com código `PROVIDER_FAILED`; saída inválida retorna
`INVALID_PROVIDER_OUTPUT`. Duração excedida retorna `PROVIDER_TIMEOUT`; capacidade
de workers esgotada retorna `PROVIDER_BUSY`. Mensagens brutas de exceções nunca são persistidas,
logadas ou devolvidas. Nenhum conteúdo manuscrito é logado pelo módulo.

`GET /submissions/recognition-providers` informa providers disponíveis e rótulos.
`GET /submissions/{id}/recognitions` lista runs completos;
`GET /submissions/{id}/recognitions/{run_id}` recupera um run persistido.
Todas essas respostas usam `Cache-Control: no-store`. Escritas têm o limite
existente de 8 MiB e erros de validação sanitizados.

## Persistência e revisão

Um sucesso usa exatamente o versionamento 03A:

```
{submission}/transcriptions/tr_{run_hex}/
  transcription.json
  recognition.json
  revisions/revision_000001.json
  acceptances/
```

Resultado, proveniência e revisão inicial são publicados em um único diretório
atômico, usando o mesmo helper de publicação da transcrição manual. O helper
revalida os contratos mesmo para chamadas internas: manual proíbe run/proveniência;
automatic exige run, revisão inicial NEEDS_REVIEW e igualdade exata dos vínculos,
proveniência e segmentos normalizados. Nenhuma revisão inicial persistida pode ser
ACCEPTED e nenhum helper de reconhecimento escreve aceite. Falhas sem
transcrição ficam em `{submission}/recognitions/run_{run_hex}.json`, com escrita
atômica imutável. Leitura valida IDs, contratos, hashes, referências à Submission
e o par entre run, transcription.json e revision_000001.json. O histórico automático
também exige o run correspondente; ausência ou divergência falha sem reparo.
Revisões humanas posteriores e seus aceites continuam usando o fluxo 03A.

A revisão inicial tem `source=automatic`, `status=NEEDS_REVIEW`, provider, run e
proveniência. A referência `automatic:pending-human-review` é um marcador de
sistema, não um revisor humano. O adapter não controla status, IDs nem aceite.
Revisões humanas subsequentes herdam a origem/proveniência e usam o endpoint 03A;
`ACCEPTED` continua sendo projetado exclusivamente do registro de aceite humano
existente, sem avaliar validade matemática. O evento de reconhecimento permanece
`NEEDS_REVIEW` mesmo após um aceite humano posterior.

Uma nova ação cria uma nova transcrição, preservando todas as anteriores. Com
chave de idempotência, retries devolvem o mesmo run, sem executar o adapter
novamente. A chave é local à submissão; mudança de provider/adapter/versão/modo/
parâmetros ou limite de duração conflita. Um run falho com a mesma chave também é replay; nova tentativa
real exige nova chave. Sem chave, cada POST é uma nova ação. O run ID deriva da
submissão/chave, que não é persistida em claro. Integridade é verificada mesmo em
replay. O ambiente precisa continuar habilitando o provider.

## Concorrência e duração

O serviço usa três fases: (1) lock compartilhado curto para integridade, idempotência
e cópia dos inputs; (2) chamada do provider sem lock global; (3) lock exclusivo
curto para revalidar fonte/idempotência e publicar atomicamente. Antes de esperar
a coordenação por request, um resultado já publicado pode ser devolvido diretamente.

Cada run tem um lock de arquivo independente em `.recognition-locks/run_*.lock`,
coordenando threads, instâncias de store e processos que usam a mesma raiz. A mesma
chave não dispara duas chamadas simultâneas; chaves diferentes não se bloqueiam.
Arquivos de lock permanecem no disco para não criar corridas entre inodes diferentes.
O lock global nunca é mantido durante a espera pelo request ou durante o provider.

`CONFIA_RECOGNITION_TIMEOUT_SECONDS` configura o limite total da chamada e validação
da saída; padrão 30 segundos, valor finito positivo dentro de `threading.TIMEOUT_MAX`.
O limite é persistido como
parâmetro público reservado `confia_total_timeout_seconds`. O adapter recebe um
deadline monotônico com duração e tempo restante; relógio monotônico não é persistido.

A espera pelo provider é limitada. Um timeout registra FAILED sem revisão; uma
saída tardia é descartada. **Isso não cancela nem interrompe a thread do adapter.**
A execução usa threads daemon e no máximo quatro providers ativos por processo;
se todos estiverem ocupados, novos requests falham sanitizados como PROVIDER_BUSY.
Threads permanentemente travadas continuam ocupando capacidade até reinício do
processo. Não mantêm o store global bloqueado.

O lock estreito do request permanece até o worker terminar, inclusive se falhar a
persistência do timeout, impedindo nova chamada concorrente com a mesma chave.
Se FAILED já foi publicado, callers em espera e retries podem recuperá-lo sem
esperar o worker tardio. Sem registro final, um retry da mesma chave precisa esperar
o worker existente; operações não relacionadas continuam disponíveis.

**Requisito para futuros adapters HTTP:** aplicar connect timeout, read timeout e
um total timeout respeitando o deadline restante, incluindo tentativas/retries e
consumo de resposta. Factories só devem construir/configurar adapters, sem I/O remoto.
A thread daemon limita espera local e não garante cancelamento de requests já
aceitos pelo servidor externo. Providers futuros deverão usar também sua própria
idempotência quando disponível. Reinício antes da publicação não assegura exatamente
uma execução remota: o lock local é liberado ao terminar o processo.

## Limites desta etapa

Há somente adapter fake local; não há credenciais ou chamadas remotas novas.
Os contratos e a validação não autenticam autoria, provider ou professor. Não há
OCR real, StructuredSolution, extração de claims, rubrica, nota, feedback, auditoria
matemática, execução Lean ou autenticação.
