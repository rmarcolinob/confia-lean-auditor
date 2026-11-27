# Fase 5 — smoke semântico textual, ainda não executado

**BLOQUEADO para execução paga até autorização específica.** Preparação offline concluída. Não é pedido para executar agora. Nenhum LLM/OCR foi chamado, nenhum gold independente foi processado e os 21 casos históricos continuam pendentes.

Este plano reduz o [smoke candidato anterior](../audits/DYNAMIC_RC1_SMOKE.md) ao texto. Não executa OCR nem requer credenciais Mathpix. O helper existente ganhou somente a opção `--text-only`, com limite de OCR igual a zero antes de qualquer transporte. O fluxo antigo permanece disponível, sem mudanças de seus limites. Não foi modificado nenhum serviço matemático.

## Corpus e escopo da autorização futura

[Duas amostras sintéticas](evidence/dynamic/text-smoke-samples.json), 1ª série do Ensino Médio: função afim e juros compostos. O arquivo contém somente ID, etapa escolar, enunciado e resolução; não contém pontuação esperada, classificação de acerto ou avaliação independente. Não enviar `tests/fixtures/dynamic_highschool_topics.json` inteiro: seus rótulos são dados de teste, não entrada do corretor.

O primeiro smoke usa SELF_STUDY nos dois casos para exercitar preparação, rubrica provisória, Grader, Reviewer, reconciliação e feedback sem nota. A integração escolar/docente já testada offline precisará de uma rodada real posterior própria; este smoke não a substitui. A avaliação humana deve ocorrer em arquivo/ambiente separado, inacessível ao servidor/providers. Não montar o gold no diretório da aplicação.

## Limites verificáveis

Configuração herdada do plano existente, **a reconfirmar antes de autorizar**: OpenAI `gpt-4.1` para preparação/rubrica/pista e `gpt-6.1-sol`, esforço `medium`, para Grader/Reviewer. Não se consultou disponibilidade de modelos nesta preparação. Não substituir silenciosamente modelo indisponível. Tarifas embutidas no helper são a referência documentada em 26/11/2026, não uma confirmação atual de preços ou garantia contratual de fatura.

| Grupo | Máximo de chamadas | Reserva máxima herdada |
|---|---:|---:|
| Preparação | 2 | US$ 0,56 |
| Rubrica provisória | 2 | US$ 0,56 |
| Grader, no máximo quatro critérios por amostra | 8 | US$ 1,92 |
| Reviewer | 8 | US$ 1,92 |
| Uma pista, nível 2 | 1 | US$ 0,28 |
| OCR | **0** | **0** |
| Total | **21 LLM** | **US$ 5,24** |

Teto local a autorizar: **US$ 6,00 incrementais**, sem impostos/câmbio/assinaturas. Reconfirmar tarifas e condições de cobrança antes do primeiro envio; se divergirem, revisar reservas antes de autorizar. O gate reserva cada chamada antecipadamente, limita entrada a 64 KiB com reserva de 100 mil tokens e saída a 10 mil tokens (preparação/rubrica/pista) ou 4 mil (semântica). Não reutiliza saldo após falha. Impede recomeçar com ledger existente e bloqueia nova chamada por STOP, falha, envelope, modelo, modalidade ou quantidade incompatíveis.

## Comandos

Comando seguro executado nesta intervenção, sem servidor ou rede:

```sh
python scripts/evaluation/dynamic_rc1_smoke.py --text-only
```

Resultado: `PLAN_ONLY`, `api_calls=0`, `max_calls=21`, `limits.ocr=0`, `maximum_reserved_usd=5.24`, autorização posterior exigida.

Após autorização, em ambiente isolado e com identidades sintéticas criadas pelo procedimento do plano anterior, injetar a chave OpenAI por configuração segura, nunca em comando, arquivo versionado ou relatório. Não disponibilizar credenciais OCR. Selecionar o interpretador validado do projeto e registrar seu caminho/versão. Comando reservado à autorização:

```sh
export CONFIA_AUTH_ENABLED=1
export CONFIA_DYNAMIC_LLM_ENABLED=1 CONFIA_SEMANTIC_LLM_ENABLED=1
export CONFIA_DYNAMIC_MODEL=gpt-4.1 CONFIA_SEMANTIC_MODEL=gpt-6.1-sol
export CONFIA_SEMANTIC_REASONING_EFFORT=medium
unset CONFIA_DYNAMIC_REASONING_EFFORT
python scripts/evaluation/dynamic_rc1_smoke.py --text-only \
  --serve-after-authorization --authorized-budget-usd 6.00 \
  --data-dir "$PWD/runtime/dynamic-text-smoke" --port 8026
```

1. Registrar commit, hashes do corpus/script, configuração sem segredos, autorização e responsável. Entrar como aluno sintético em `http://127.0.0.1:8026/#student/study`.
2. Para cada amostra, inserir o enunciado literal, conferir leitura, preparar uma vez e confirmar interpretação. A rubrica deve ser provisória/formativa e ter até quatro critérios; se não, parar, sem ajustar critérios para caber no orçamento.
3. Inserir a resolução literal, conferir leitura e analisar uma vez. Não corrigir o erro do aluno na transcrição nem enviar avaliação humana como instrução.
4. Inspecionar evidências por critério, erros, acertos, abstenções e divergências em registros privados. Na segunda amostra, solicitar no máximo uma pista de nível 2. Conferir ausência de pontos em interface, API e histórico e ausência de revelação prematura da resposta.
5. Preservar recibos, modelos retornados, uso, latência e custo estimado/consumo observado. Comparar depois com avaliação humana separada. Não publicar respostas privadas brutas ou credenciais.

Parar por falha de transporte/contrato, 401/403/429, timeout, uso ausente, modelo divergente, perda de vínculo, crédito injustificado ou vazamento. Não repetir automaticamente. Criar `runtime/dynamic-text-smoke/smoke-control/STOP` e encerrar o servidor; isso impede envios seguintes, mas não cancela processamento já aceito pelo provider. Não zerar o ledger para continuar.

## Aceitação

Exigir pelo menos uma avaliação semântica real de Grader e Reviewer comprovada por recibos; justificativas vinculadas à solução/rubrica; erro técnico distinto de erro matemático; pontuação interna não divulgada; pistas coerentes com nível; versões/originais íntegros; 21 chamadas e teto respeitados. Abstenção justificada não é erro por si só, mas mantém a capacidade não demonstrada. Registrar taxas de abstenção/divergência, latências por etapa, tokens, modelos retornados e custos.

Mesmo aprovado, o smoke não mede acurácia geral, robustez pedagógica ou segurança de uso escolar autônomo. O próximo gate científico exige soluções independentes corretas/parciais/incorretas/alternativas, julgamento humano cego por critério, falsos créditos/erros, qualidade das evidências e feedback. Não encerrar os 21 casos históricos por aprovação dos dois novos exemplos.
