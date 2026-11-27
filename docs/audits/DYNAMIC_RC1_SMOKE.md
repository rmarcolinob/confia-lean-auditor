# DYNAMIC-RC1 — plano de smoke real, ainda não autorizado

Data da preparação e consulta das tarifas: 26/11/2026. Base de código: `fc6f271ab4f484f48609ddde67faa84b0ac690ca`. **Nenhuma chamada paga foi executada.** Este documento prepara uma futura autorização específica, não constitui a autorização.

## Amostras e finalidade

[Arquivo de amostras](assets/dynamic-rc1/smoke/samples.json): dois problemas sintéticos do 8º ano, sem nomes, turmas ou dados de estudantes. S1 é uma solução textual de proporcionalidade; S2 é uma resolução de área/perímetro em [imagem sintética](assets/dynamic-rc1/smoke/geometry-synthetic.png), com desenvolvimento a examinar. O PNG contém texto impresso gerado localmente, **não caligrafia humana**: comprova o percurso de imagem, mas não valida captura manuscrita real. O texto literal da imagem serve apenas à conferência da transcrição; não é gold matemático nem nota-alvo.

Os dois casos usam SELF_STUDY para incluir rubrica provisória, Grader, Reviewer, reconciliação e feedback sem nota. Os contextos docente e institucional são cobertos offline nesta preparação; este smoke pequeno não é validação real dos três contextos nem substitui uma rodada institucional posterior.

Enviar somente enunciado, resolução, rubrica provisória e contexto necessários. Não carregar gold humano, avaliação independente, resultado desejado, arquivos de outras atividades ou históricos de estudantes no processo servidor. Referências eventualmente geradas pelo próprio DYNAMIC não equivalem ao gold independente. Não corrigir a resolução do aluno para coincidir com a resposta matemática esperada.

## Orçamento proposto

Providers/modelos solicitados: OpenAI `gpt-4.1` para preparação/rubrica/pista, OpenAI `gpt-6.1-sol` com `medium` para Grader/Reviewer semânticos e Mathpix `mathpix_image`, `/v3/text`, para uma página. A versão interna do modelo OCR pode não ser informada; registrar desconhecida, mantendo adapter/recibo e versão retornada quando disponível. Registrar também o modelo OpenAI **retornado**, não apenas o solicitado.

Tarifas de referência Standard, por milhão de tokens: GPT-4.1 entrada US$ 2 / saída US$ 8 ([documentação oficial](https://developers.openai.com/api/docs/models/gpt-4.1)); GPT-6.1 Sol entrada US$ 2 / saída US$ 10 ([tabela oficial](https://developers.openai.com/api/docs/pricing)). OCR de imagem: US$ 0,002 na faixa inicial ([Mathpix](https://mathpix.com/pricing/api)). Reservar US$ 0,01 para essa chamada. Descontos de cache não são usados para aumentar o orçamento. Reconfirmar tarifas, modalidade, disponibilidade e condições da conta imediatamente antes da autorização; o catálogo consultado marca GPT-4.1 como deprecated. Não substituir silenciosamente um modelo indisponível: isso exige atualizar o plano e sua identificação.

| Operação | Máximo de chamadas | Máximo de saída por chamada | Reserva por chamada | Reserva do grupo |
| --- | ---: | ---: | ---: | ---: |
| Preparação de enunciado | 2 | 10.000 tokens | US$ 0,28 | US$ 0,56 |
| Rubrica provisória | 2 | 10.000 tokens | US$ 0,28 | US$ 0,56 |
| Grader, até quatro critérios por caso | 8 | 4.000 tokens | US$ 0,24 | US$ 1,92 |
| Reviewer independente | 8 | 4.000 tokens | US$ 0,24 | US$ 1,92 |
| Uma pista de nível 2, somente S2 | 1 | 10.000 tokens | US$ 0,28 | US$ 0,28 |
| OCR de uma página sintética | 1 | Não aplicável | US$ 0,01 | US$ 0,01 |
| **Total** | **22 (21 LLM + 1 OCR)** | | | **US$ 5,25** |

**Teto a autorizar: US$ 6,00 de consumo incremental das APIs**, sem impostos, câmbio, aquisição de créditos ou mensalidades. Não criar assinatura/comprar crédito nesta autorização. Cada chamada LLM reserva antecipadamente 100.000 tokens de entrada; o gate recusa JSON maior que 64 KiB, opções extras, ferramentas e envelopes diferentes das duas mensagens esperadas. A reserva de entrada é deliberadamente conservadora (bytes do pedido mais margem para envelope/tokenização); não é uma medição exata dos tokens. O recibo é confrontado com essa hipótese e interrompe o smoke se divergir. A garantia é do limite local de reservas e chamadas, não um teto contratual da fatura do fornecedor. Tarifas, impostos ou processamento inesperado invalidam a estimativa e impedem continuar.

`dynamic_rc1_smoke.py` faz somente impressão do plano por padrão. Quando explicitamente habilitado em etapa posterior, envolve o transporte HTTP existente; não muda modelos, prompts, respostas, decisões ou rubricas. Reserva antes do envio, limita grupos e soma financeira, permite apenas os dois endpoints, desabilita redirects, registra latência/uso/modelo/recibo e mantém a reserva em falhas/timeouts. Não libera saldo para repetir chamadas; ledger existente impede reinício automático. O código vigente usa transporte HTTP síncrono interceptado pelo gate; isso não é um sandbox genérico de rede para outros programas.

## Comandos seguros nesta preparação

Usar o interpretador validado; no worktree atual ele está no `.venv` do repositório principal. Em clone próprio, substituir pelo `.venv/bin/python` correspondente.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/evaluation/dynamic_rc1_manifest.py --environment
.venv/bin/python scripts/evaluation/dynamic_rc1_smoke.py
```

O segundo comando retorna `PLAN_ONLY`, `api_calls=0` e o orçamento. Não inicia servidor nem consulta disponibilidade remota de modelos.

## Comandos reservados à autorização posterior

Antes de executar, rever o manifesto, as tarifas, os nove controles de prontidão e a autorização expressa de US$ 6,00. As credenciais devem ser injetadas por configuração segura do operador no processo, nunca digitadas em scripts, commitadas, copiadas em relatório ou exibidas por `env`/logs. Não montar diretório de gold no ambiente do servidor.

Preparar identidades sintéticas e diretório novo, sem credenciais de provider necessárias nesta preparação local:

```sh
export CONFIA_AUTH_DIR="$PWD/runtime/dynamic-rc1-smoke/auth"
export CONFIA_INSTITUTIONAL_DIR="$PWD/runtime/dynamic-rc1-smoke/institutional"
.venv/bin/python scripts/create_demo_users.py
# Senhas escolhidas pelo operador, sem eco; não existe senha padrão a publicar.
```

Somente após autorização e injeção segura das três credenciais de provider:

```sh
export CONFIA_AUTH_ENABLED=1
export CONFIA_DYNAMIC_LLM_ENABLED=1 CONFIA_SEMANTIC_LLM_ENABLED=1
export CONFIA_DYNAMIC_MODEL=gpt-4.1 CONFIA_SEMANTIC_MODEL=gpt-6.1-sol
export CONFIA_SEMANTIC_REASONING_EFFORT=medium
unset CONFIA_DYNAMIC_REASONING_EFFORT
.venv/bin/python scripts/evaluation/dynamic_rc1_smoke.py \
  --serve-after-authorization --authorized-budget-usd 6.00 \
  --data-dir "$PWD/runtime/dynamic-rc1-smoke" --port 8026
```

Esse servidor é exclusivo de localhost, uma instância e um operador. Usa armazenamento isolado e autenticação; não usar o launcher demo sem autenticação. A interface está em `http://127.0.0.1:8026/#student/study`. O operador entra na conta sintética de aluno; essa conferência é registrada como STUDENT, não como aprovação docente de rubrica.

## Procedimento supervisionado e interrupção

1. Registrar hashes do manifesto e das amostras, configuração sem segredos, autorização, data e operador no diretório privado da execução. Não usar o próprio texto de avaliação humana como prompt.
2. S1: inserir o enunciado literal do arquivo, conferir leitura, preparar uma única vez e conferir interpretação. Inspecionar o pacote privado: critérios provisórios, no máximo quatro. Se houver ambiguidade, mais critérios ou falha, parar; não editar pesos/critério nem regenerar para caber no limite. Confirmar a interpretação, inserir a solução textual, conferir leitura e analisar uma única vez.
3. Conferir recibos do Grader e Reviewer, citações/offsets, decisões exatas versus semânticas e reconciliação. Registrar abstenções e falhas distintamente. Não forçar atendimento/nota ou concordância. Nenhuma resposta esperada foi programada.
4. S2: repetir preparação/inspeção com o segundo enunciado; enviar somente o PNG fornecido. Acionar OCR uma vez. Comparar com a imagem, salvar correções **somente de transcrição**, resolver ambiguidades e confirmar explicitamente a versão usada. Registrar revisão/hash/autoria e manter o original. Não alterar o erro matemático escrito na imagem.
5. Analisar S2 uma única vez e solicitar no máximo uma pista de nível 2. Conferir se erros e partes aproveitáveis aparecem sem divulgar pontos; histórico e GET devem preservar a mesma política. Uma pista incompatível deve gerar orientação segura, não publicação da mensagem rejeitada. Nenhum nível 3/4 está orçado.
6. Copiar relatórios públicos e recibos privados autorizados para o registro local, preservando seu contexto. Registrar quantidade real de chamadas por etapa, tokens, latências, modelos retornados e estimativa/consumo da conta. Se não houver abstenção real, registrar zero; os testes offline cobrem esse cenário, mas não inventar um caso histórico ou chamada adicional.
7. Encerrar o servidor. Não publicar ledger, respostas brutas, runtime ou credenciais. Uma síntese anonimizada posterior pode registrar os hashes, resultados e limitações.

Parar imediatamente por 401/403/429, timeout, falha de integridade, uso/recibo ausente, modelo/modalidade inesperada, leitura ambígua, rubrica fora do escopo, vazamento de pontos/solução precoce ou suspeita de crédito injustificado. Não repetir automaticamente. O gate interrompe novas chamadas após falha de transporte/contrato/orçamento; avaliação humana continua necessária para defeitos matemáticos ou pedagógicos em respostas HTTP válidas.

Interrupção manual: criar `runtime/dynamic-rc1-smoke/smoke-control/STOP` e encerrar o servidor com Ctrl-C. Isso impede chamadas seguintes, mas **não desfaz cobrança nem cancela processamento remoto já aceito**. Depois de timeout, aguardar/reconciliar consumo; não reiniciar para zerar o contador. Um novo ledger/diretório requer nova revisão e autorização, não é continuação gratuita.

## Critérios de aceitação e recibos

- Ambos os percursos concluem com feedback fundamentado ou pendência explicitamente justificada, sem nota em SELF_STUDY e sem falha técnica apresentada como erro matemático.
- Ao menos uma avaliação semântica real do Grader e uma do Reviewer são comprovadas por recibos. Concordância não é certificação formal. Não há Lean no caminho.
- Original, OCR, leitura corrigida/conferida e texto efetivamente avaliado mantêm hashes e autoria coerentes. A imagem sintética não mede robustez de manuscritos reais.
- Revisor humano avalia pertinência dos critérios e evidências, falsos erros, omissões e antecipação indevida de resposta. Não há nota-alvo de aceite.
- Uso real de tokens, ID/modelo retornado, custo calculável e latência por chamada constam no ledger. A preparação padrão não persiste uso de tokens por si só; o recibo externo complementa essa lacuna sem alterar contratos históricos. Mathpix pode não fornecer modelo/custo unitário no recibo: manter desconhecido e conferir consumo na conta.
- Limites de grupos, 22 chamadas, reservas de US$ 5,25 e teto de US$ 6,00 respeitados; nenhuma leitura do gold e nenhum dado real de estudante enviado.

Um erro matemático relevante ou vazamento reprova o smoke e bloqueia congelamento operacional até diagnóstico. Uma abstenção fundamentada não é defeito automaticamente, mas torna aquela capacidade ainda não demonstrada. Este smoke mínimo não estima acurácia, generalidade, aprendizagem ou segurança de uso escolar autônomo.
