# P0-SECONDARY-LIVE-02

## Resultado

**INCOMPLETE: o critério de aceitação de 3/3 decisões válidas não foi atingido.** A correção do schema eliminou arrays de evidência vazios na execução real, mas dois casos continuam rejeitados por citações não localizadas. Foram executados somente os três IDs selecionados, uma vez cada, sequencialmente. O retry interno permaneceu limitado a um. Não houve Smoke V4, batch 18/502/1000, staging, commit ou push.

## Seleção e comparação

| Caso | V3: score / tentativas / estado | Após: score / tentativas / estado | Critérios primários preservados |
|---|---|---|---|
| ITA2025Q1_S001_L04 | 10.0 / 2 / accepted | 10.0 / 1 / accepted | True |
| ITA2025Q1_S016_L01 | None / 2 / rejected | None / 2 / rejected | True |
| ITA2025Q4_S003_L04 | None / 2 / rejected | None / 2 / rejected | True |

Q1_S001_L04 foi o único caso numérico do V3. Q1_S016_L01 representa evidence=[]; Q4_S003_L04 representa citações não literais. A seleção foi registrada antes de editar o motor. As três requisições anteriores foram reconstruídas offline a partir dos artifacts e seus hashes coincidem exatamente com request_sha256 do V3. Nenhuma chamada externa foi feita para recriar a fase anterior.

## Causa raiz e primeira divergência

Das 35 tentativas inválidas do V3: **29 SCHEMA_MISMATCH** (arrays vazios permitidos no schema enviado, proibidos localmente) e **6 EVIDENCE_NOT_FOUND** (citação não literal ou diagnóstico parcialmente redigido). A taxonomia completa está em diagnosis.json. Não há evidência de STRUCTURED_OUTPUT_NOT_APPLIED, PARSER_MISMATCH, INVALID_POINTS, INVALID_CRITERION_ID, EXTRA_REQUIREMENT, MISSING_FIELD ou API_RESPONSE_SHAPE como primeira causa nesses registros. A classificação não demonstra que cada campo posterior ao primeiro erro foi validado no V3.

O primeiro desvio observável em relação à resposta aceita está no conteúdo de evidence produzido pelo modelo. O parse JSON conclui; o contrato estrutural antigo admite []; o validador de origem rejeita. Portanto, API e parser não eram a causa dos arrays vazios: o schema enviado era mais permissivo que a validação local. Para citações reescritas, a validação rejeita corretamente mudanças que não são meramente apresentação.

As seis tentativas dos três casos anteriores estão em three_case_before.json; o diagnóstico inicial, payload e request reconstruídos estão em before_requests/. O V3 não armazenou o envelope HTTP nem todas as respostas completas. Esses dados históricos permanecem indisponíveis e não foram fabricados.

## Trajeto real API → parser → validação

1. A pauta seleciona somente itens com points=None e mathematical_status=indeterminate. IDs internos dos critérios são as chaves exatas do objeto de retorno; não há alias/display name.
2. secondary_context.prepare_payload fornece solução, enunciado, critérios pendentes, allowed_points e evidências/checks relevantes. Esse módulo não foi alterado.
3. OpenAI.responses.create envia text.format={type:json_schema, strict:true, schema:...}, temperatura 0, limite 4000 tokens, store=false, timeout 45s, sem retry de transporte. Modelo solicitado: gpt-4o-mini; modelo resolvido observado: gpt-4o-mini-2024-07-18.
4. As **cinco requisições reais** desta tarefa retornaram HTTP 200. As cinco respostas ecoam o mesmo schema enviado, incluindo minItems/maxItems. Não houve wrapper Markdown extra.
5. O SDK retorna objeto Response; output contém mensagem com content de tipo output_text. O conteúdo útil é TEXTO JSON, não o objeto de decisões já validado. O código lê response.output_text.
6. parse_response executa json.loads manual com rejeição de chaves duplicadas e constantes não finitas.
7. validate_decisions verifica estrutura, valores permitidos, coerência decisão/pontos, evidências e rationale. Não existe modelo Pydantic de decisão como fonte do schema; RubricItemResult é modelo de persistência e admite campos nulos antes da adjudicação.
8. Apenas o lote inteiramente válido é aplicado pela score policy inalterada. Critérios supported/refuted não são enviados nem sobrescritos.

A documentação oficial confirma o formato para Responses e suporte do modelo a Structured Outputs: [guia](https://developers.openai.com/api/docs/guides/structured-outputs) e [GPT-4o mini](https://developers.openai.com/api/docs/models/gpt-4o-mini). A confirmação operacional desta tarefa vem dos corpos HTTP capturados, não de mocks.

## Schema local versus enviado

| Campo | Antes | Correção / condição atual |
|---|---|---|
| required / additionalProperties | Quatro campos obrigatórios; extras proibidos | Preservados na raiz e em cada critério |
| criterion_id | Chaves da raiz iguais aos IDs pendentes | Preservado; nenhum alias |
| suggested_points | number com enum [0,max_points] | Preservado; local rejeita bool/não finito e impõe award=max, deny=0 |
| evidence | array de strings sem cardinalidade/comprimento | minItems=1, maxItems=3; strings 1..800, pattern não vazio; origem ainda validada localmente |
| rationale | Enum fechado por critério | Preservado; local exige opção correspondente a award/deny |
| decision | enum award/deny | Preservado |
| nullable | Nenhum dos quatro campos aceita null | Preservado; nullable na persistência não define o contrato externo |

A associação evidence→fonte e a correspondência rationale→decision são restrições semânticas adicionais. Elas não foram declaradas como garantias da API. Nenhum valor intermediário de pontuação foi permitido para fabricar uma decisão válida.

## Correção implementada

- secondary_adjudicator.response_schema: alinha a cardinalidade/comprimento de evidence ao contrato local.
- secondary_evidence.source_quote / resolve_evidence: recupera spans da fonte após equivalência Unicode canônica (NFD), colapso de whitespace e remoção de um par externo balanceado de aspas. Retorna sempre texto original, com verificação de round-trip e limite de tamanho. Não usa matching aproximado para aprovar.
- validate_decisions: só substitui citações por spans originais depois que todo o lote passa; preserva rejeição de valores, negação, pontuação e operadores alterados.
- retry_feedback: informa criterion_id, campo, categoria e motivo concreto; reforça 1..3 citações também em deny, sem modificar a pauta.
- response_trace / diagnostic: preserva resposta redigida, candidato parseado, erro, critério, allowed_points, retry, modelo, versão de schema e tipo de resposta. Corrige a redação que confundia escapes de newline em JSON com caminhos Windows.

Não houve modificação em claims, canonicalização matemática, rubricas de problemas, Lean, score policy ou UI. A normalização de citação é local ao adjudicador e não cria equivalência matemática. As versões agora são secondary-criterion-v3 e secondary-schema-v3.

## Evidence: aceitação e limites

Unicode composto/decomposto, CR/LF, tabs, NBSP e whitespace repetido podem representar a mesma sequência textual. Um par de aspas delimitadoras pode ser apresentação. Maiúsculas/minúsculas não são dobradas indiscriminadamente: A e a podem ser variáveis distintas. Operadores, sinais, expoentes, números, palavras, negação, pontuação e LaTeX algébrico não são reescritos. Não se converte automaticamente x² em x^2 nem <= em comando LaTeX. Isso conserva um limite que ainda rejeita algumas paráfrases equivalentes.

Nas cinco respostas: 22 citações exatas, 14 recuperáveis apenas por apresentação e 11 não encontradas. São ocorrências de citações, inclusive em lotes rejeitados; não são pontos concedidos. A checagem independente de todos os critérios encontra 10 objetos com quote_not_found. O motor registra o primeiro erro de cada lote; os demais ficam em criterion_validation.json.

Após a correção, Q1_S016_L01 repete a mesma citação não encontrada no critério coordinates em ambas as tentativas. Em Q4_S003_L04, o primeiro erro aparece em distinct_g_inputs; no retry, em positive_witnesses. Neste último, a comparação diagnóstica identifica alteração de maiúscula inicial (E versus e). Não houve erro de newline escapado nessas quatro primeiras violações. As diferenças completas estão em source_differences.json; o alinhamento aproximado desse arquivo é apenas diagnóstico e nunca aprova evidence.

## Rationale e retry

Rationale permanece restrita às opções da pauta; não foi relaxada para aceitar “conclusão formal”, prova extra ou requisito inventado. Nenhuma tentativa desta rodada teve rationale como primeira causa da rejeição. A adesão ao vocabulário fechado não comprova que a decisão matemática seja correta.

No V3 os 18 lotes usaram retry; 17 continuaram inválidos e um recuperou. Nesta tarefa o caso originalmente bem-sucedido passou na primeira tentativa, enquanto os outros dois usaram um retry e permaneceram inválidos. Portanto, há melhora no defeito estrutural e na observabilidade, mas o feedback mais específico **não resolveu a geração de citações** nesses dois casos. Nenhum retry adicional foi executado.

## Resultados observados após a correção

| Caso | Tentativa | HTTP | Primeiro critério inválido | Motivo |
|---|---|---|---|---|
| ITA2025Q1_S001_L04 | 1 | 200 | — | accepted |
| ITA2025Q1_S016_L01 | 1 | 200 | coordinates | quote_not_found |
| ITA2025Q1_S016_L01 | 2 | 200 | coordinates | quote_not_found |
| ITA2025Q4_S003_L04 | 1 | 200 | distinct_g_inputs | quote_not_found |
| ITA2025Q4_S003_L04 | 2 | 200 | positive_witnesses | quote_not_found |

Resultado operacional: **1/3 válido antes → 1/3 válido depois**. Scores: Q1_S001_L04=10; Q1_S016_L01=null; Q4_S003_L04=null. As duas notas nulas não foram convertidas artificialmente em zero. As notas permanecem sugestões do ConfIA; não há decisão final de avaliador humano nesta tarefa.

## Mocks, fixtures e testes

Mocks antigos construíam evidence preenchida a partir da própria solução; os negativos comprovavam que o validador rejeitava [], sem comprovar que o schema enviado impedia []. Havia teste com o SDK e transporte simulado, porém a resposta era fabricada com valores válidos. A nova cobertura usa os excertos efetivamente salvos no V3 e os cinco envelopes HTTP reais desta rodada. O replay passa pelo SDK OpenAI real usando httpx.MockTransport, sem rede.

**141 testes focados passaram, incluindo 29 novos.** Módulos: secondary_live_contract, secondary_adjudicator_contract, score_policy, score_policy_api, rubric_bridge e rubric_bridge_pipeline. Os dois fixtures reais ainda inválidos são esperados como rejeições de provenance; o teste passar não os transforma em casos operacionalmente válidos. Os testes novos incluem normalizações seguras, recusas adversariais, cardinalidade de evidence, ausência de mutação parcial, feedback específico e redação de dados.

A primeira execução de testes novos encontrou uma dependência opcional ausente (jsonschema); não foi instalada ou adicionada ao projeto. Os testes foram ajustados para asserções sem dependências e confirmação do schema pelo retorno real. Uma classificação inicial de fixture foi corrigida para observar o critério que falhou, sem confundir um [] posterior com a primeira violação. Logs dessas execuções permanecem preservados.

A suíte histórica completa não foi reexecutada; as falhas conhecidas HMER/UI/tablet e o xfail F2Q6 não foram corrigidos nem apresentados como revalidados. Nenhuma regressão foi observada nos 141 testes executados.

## Persistência e privacidade

http/<id>/<tentativa>.json contém request_body, status_code e response_body redigidos. Headers, API keys e autenticação não são registrados. As hooks verificam endpoint api.openai.com/v1/responses, texto idêntico ao caso autorizado e conjunto exato de critérios pendentes. Cada retorno foi salvo imediatamente; nenhum dos outros 15 casos foi chamado.

Os artifacts por caso também incluem audit.json e secondary_adjudication.json. raw_response_redacted é uma representação JSON redigida (pode ser reserializada), com ordem/chaves duplicadas preservadas; parsed_candidate conserva o objeto antes da recuperação de spans. A redação ocorre antes de codificar strings novamente. Excertos mantêm limite de 1200 caracteres; o texto diagnóstico completo tem teto de 65536 e marca truncamento. As cinco respostas desta rodada foram preservadas sem truncar esse texto completo. Segredos conhecidos foram checados localmente sem imprimi-los.

## Limitação pendente e próximo passo recomendado

**A tarefa não satisfaz o aceite 3/3.** A causa estrutural de [] foi corrigida; a dependência de o modelo copiar citações continua frágil. Recomenda-se, em tarefa separada, avaliar referências a spans previamente fornecidos com IDs/offsets e validação determinística de origem, ou um tratamento rigorosamente delimitado de apresentação textual. Isso evitaria depender de reescrita livre sem aceitar evidência inventada. Nenhuma dessas ampliações foi implementada após os três testes. Novo teste externo requer nova autorização; não foi feito Smoke V4.

## Arquivos e preservação

- `app/confia_lean_auditor/rubric/secondary_adjudicator.py`
- `app/confia_lean_auditor/rubric/secondary_evidence.py`
- `tests/test_secondary_live_contract.py`
- `tests/fixtures/secondary_live_02/v3_observed.json`
- `tests/fixtures/secondary_live_02/ITA2025Q1_S001_L04.json`
- `tests/fixtures/secondary_live_02/ITA2025Q1_S016_L01.json`
- `tests/fixtures/secondary_live_02/ITA2025Q4_S003_L04.json`
- `docs/audits/P0_SECONDARY_LIVE_02.md`

V3: 350 arquivos preservados por SHA-256. Todos os arquivos preexistentes fora do adjudicador permanecem idênticos ao snapshot inicial. HEAD e índice preservados; staged vazio. git diff --check: exit 0. Status completo em git_status_short.txt.

Artifacts obrigatórios: diagnosis.json, three_case_before.json, three_case_after.json, implementation.diff e validation_summary.json em artifacts/evaluations/ita1000_v1_2/p0_secondary_live_02/. O diff é incremental contra o snapshot desta tarefa, não contra HEAD: preserva as alterações anteriores do usuário.
