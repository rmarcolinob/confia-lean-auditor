# P0-SECONDARY-ADJUDICATOR-01

## Resultado e limite da conclusão

O secondary adjudicator passou a ter um contrato fechado de justificativas, validação local de evidência e pontos, retry exclusivo para resposta inválida e diagnóstico persistente. A seleção dos critérios e as regras numéricas de SCORE-POLICY-02 foram preservadas. Nenhuma chamada externa, chamada real OpenAI/Mathpix ou reexecução do Smoke V2 foi realizada.

O diagnóstico histórico encontrou **17 respostas rejeitadas sem raw response preservado**. Não é possível recuperar se cada rejeição decorreu de JSON, campo, valor, evidência ou rationale. A causa comprovada do apagamento dessa informação é o tratamento genérico de exceções; não se apresenta uma hipótese como causa confirmada das 17 respostas. A integração já usava Structured Outputs antes desta tarefa. Portanto, a falha histórica não pode ser atribuída simplesmente à ausência desse recurso.

O caso numérico histórico confirmou uma negação por exigir “conclusão formal”, embora o próprio rationale reconhecesse os valores finais corretos. Essa exigência não consta do critério final de F2Q1. A nova validação rejeita essa classe de resposta e também impede que uma decisão deny use uma justificativa que reconhece o critério como satisfeito. Não há regra local que invente pontos para corrigir uma decisão inválida.

## Estado encontrado e diagnóstico antes da edição

O trabalho anterior de alignment estava completo. Seu código, canonicalização, extração, gates P0 e artifacts foram preservados. O snapshot desta tarefa inclui o estado não commitado, não apenas HEAD: `before.json` e `baseline_sources.tar.gz`, no diretório de artifacts desta auditoria. O diff incremental compara exclusivamente esta tarefa com esse snapshot.

O diagnóstico foi concluído antes da edição do motor. Foram inspecionados os 211 JSONs do Smoke V2, os nomes/tipos dos demais arquivos e o ledger JSONL de 18 entradas. Os arquivos de texto são soluções, dependências e estado Git; o ledger não contém resposta bruta ou erro detalhado de validação. O código anterior confirma que nenhum raw inválido era persistido.

`invalid_response_taxonomy.json` registra individualmente os 17 casos, seus critérios pendentes e allowed_points. Cada dimensão não recuperável está marcada como `not_observable`, em vez de receber uma classificação especulativa: JSON parse failure, schema failure, invalid points/evidence, missing rationale, wrong criterion ID, extra/missing fields, enum e outros motivos.

No código anterior, `secondary_adjudicator.adjudicate` capturava `ValueError`/`AdjudicationError`; na segunda tentativa substituía a causa específica por `ADJUDICATOR_INVALID_RESPONSE`. `apply_scoring_policy` conservava apenas esse código. O caso numérico histórico é ITA2025F2Q1_S003_L02; seu rationale está preservado na taxonomia. Nenhum dataset_id foi usado na implementação ou no teste da classe de erro.

## Contrato de saída

O objeto continua indexado pelo ID de cada critério pendente, preservando a forma já usada no projeto. Essa chave exerce o papel de criterion_id, sem duplicar um campo que não seria necessário. Cada decisão possui exatamente quatro campos obrigatórios:

| Campo | Contrato |
|---|---|
| suggested_points | Número do domínio `[0, max_points]`; bool, NaN, infinito e valores intermediários são inválidos. |
| decision | `award` ou `deny`; award exige max_points e deny exige zero. |
| evidence | Uma a três citações literais não vazias, de até 800 caracteres cada, presentes no texto da solução. |
| rationale | Uma justificativa autorizada para aquele critério e aquela decisão, derivada da descrição oficial ou de requisito codificado existente. |

Campos extras, campos ausentes, IDs inesperados, enums inválidos e chaves JSON duplicadas são rejeitados. Prosa livre e blocos Markdown não são “consertados” para parecerem JSON válido. A aplicação só recebe pontos depois que a resposta inteira passa na validação; uma decisão válida isolada não é aplicada quando outra falha.

`response_schema` mantém `text.format.type=json_schema`, `strict=true`, propriedades fechadas e campos obrigatórios. As restrições de domínio de pontos, decisão e rationale também aparecem no schema. Citações reais, tamanho e coerência entre campos são verificados localmente; Structured Outputs não é tratado como prova dessas propriedades semânticas.

Não foi adicionada dependência. O SDK instalado é OpenAI 2.44.0; seus tipos locais foram inspecionados. Um teste com o SDK real e `httpx.MockTransport`, apontado para `offline.invalid`, verifica a serialização do contrato e a leitura da resposta sem conexão de rede. A aceitação e a qualidade em produção ainda dependem de uma futura execução separadamente autorizada.

## Justificativas limitadas à pauta

`rationale_options` constrói um vocabulário fechado por critério. Award declara que a evidência satisfaz a descrição oficial. Deny identifica ausência ou não satisfação de uma condição explicitamente declarada na descrição ou nas regras codificadas. O modelo deve copiar uma dessas opções; não pode acrescentar “conclusão formal”, “prova completa” ou outro passo inexistente.

Isso é mais forte do que procurar palavras proibidas: qualquer explicação externa ao conjunto autorizado é inválida, inclusive paráfrases. As citações da solução acompanham a condição selecionada. A contrapartida é uma explicação limitada a esses motivos estruturados, em vez de uma dissertação livre do modelo.

**Limite importante:** o contrato impede novos requisitos no rationale retornado, mas não prova a correção matemática do julgamento do modelo, nem torna observável seu raciocínio interno. Um motivo permitido ainda pode ser escolhido incorretamente. Essa incerteza permanece visível por `secondary_adjudication`, status matemático inalterado e `needs_review=true`. Não há promessa de eliminar todo falso positivo ou falso negativo sem uma avaliação posterior.

## Prompt e contexto mínimo

O prompt explicita a autoridade da pauta, a proibição de novas exigências, a obrigação de evidência literal, a aceitação de métodos equivalentes e a distinção entre sugestão de pontos e matemática verificada. Falha técnica ou ausência de extração não justificam zero por si só. Para conteúdo ausente, o modelo deve citar a resposta disponível e identificar uma condição autorizada ausente. Não precisa de prova formal da negação para sugerir zero.

`secondary_context.prepare_payload` envia somente o enunciado, a solução e os critérios pendentes. Para cada critério, inclui descrição, pontos permitidos, estado da primeira passagem, regras relevantes já codificadas, microclaims requeridos e evidência disponível. Microclaims declarados sem resultado permanecem representados como `unavailable`; resultados de referência são marcados como insuficientes para provar autoria do estudante.

Quando o contexto comum de claims está disponível, são incluídos apenas claims grounded e atribuíveis relevantes ao critério, com texto/span, papel semântico, forma canônica e resultado de alignment. Checks são ligados por identidade, conteúdo e fonte usando os mecanismos P0 existentes. Há limite de 12 claims/checks auxiliares por critério e contagem dos claims omitidos. A solução integral permanece disponível para avaliar ausência e métodos alternativos.

Não são enviados todos os artifacts, a rubrica inteira, todas as claims heurísticas, a resposta esperada global, arquivos Lean ou seu conteúdo, paths, hashes ou IDs de registros internos. Bindings esperados específicos de um contrato existente podem aparecer como contexto matemático, sem regra “encontrou o número, ganhou pontos”. Os únicos IDs usados como chave de decisão são os IDs dos critérios necessários ao contrato.

## Primeira passagem, pontuação e revisão

Critérios já decididos, inclusive supported e refuted, continuam fora do fallback. Os testes de integração usam a extração e a ponte reais para verificar que as conclusões apoiadas de F2Q1 e F2Q5 não são readjudicadas. Estados inconsistentes, como supported/refuted com points=None, falham antes de chamar o provedor; não são convertidos em nova oportunidade de avaliação.

O estado legado sem mathematical_status e sem pontos permanece elegível como antes, explicitamente identificado como `legacy_undecided`. `technical_error` permanece no resultado da primeira passagem. O adjudicador pode sugerir pontos nesse caso, mas não remove o erro ou a necessidade de revisão.

`scoring_policy.py` recebeu somente a montagem do contexto e a persistência dos diagnósticos. Foram preservados o cálculo de score, o subtotal primário, o denominador de coverage, estimated_points, a atribuição de verified_points/suggested_points e a regra de needs_review. Uma comparação isolada do app atual com o snapshot anterior verificou **108 combinações** de supported/refuted/indeterminate, award/deny e erro técnico, com invariantes idênticos (`policy_parity.json`).

Após adjudicação, points e verified_points continuam sendo da primeira passagem. O status matemático continua indeterminate quando não foi decidido. Apenas suggested_points, scoring_basis=`secondary_adjudication`, scoring_evidence e scoring_rationale recebem o resultado validado. Zero adjudicado não é refutação formal.

O teste 8 pontos primários + 2 adjudicados mantém score=10, coverage=0.8, estimated_points=2 e needs_review=true. A cobertura não incorpora pontos estimados. Se qualquer critério pendente falhar definitivamente, score e estimated_points permanecem nulos com motivo explícito; pontos primários não são apagados ou substituídos.

## Retry e falhas

Há no máximo um retry, exclusivamente após JSON/contrato/evidência inválidos. A segunda chamada conserva solução, critérios e schema; apenas acrescenta uma instrução de correção com a categoria estável do erro. A resposta inválida não é inserida integralmente no prompt seguinte.

Retries automáticos de transporte do SDK foram desativados (`max_retries=0`), tornando o limite efetivo de chamadas previsível. Timeout, erro de conexão, autorização, rate limit, resposta incompleta, recusa explícita do modelo e outros erros operacionais falham sem repetição. Recusa é registrada como `model_refusal`, não disfarçada de erro de JSON.

Após duas respostas inválidas, o motivo público permanece `ADJUDICATOR_INVALID_RESPONSE`. A categoria específica e os detalhes limitados das tentativas ficam preservados para diagnóstico. Nenhuma pontuação local é fabricada para atingir a meta de nota numérica.

## Observabilidade, privacidade e reprodução

Cada execução do motor grava `secondary_adjudication.json`, inclusive quando não foi necessário adjudicar. O artifact identifica critérios não chamados, o estado de entrada, allowed_points, decisão, pontos sugeridos, evidência, rationale, validação e retry_count. A metadata existente em rubric.secondary_adjudication conserva o resumo das tentativas quando houve solicitação ou falha.

Falhas de validação registram código/categoria/campo, criterion_id conhecido, allowed_points, adjudicator_version e excerpt redigido de no máximo 1.200 caracteres por tentativa. Não se despeja o response inteiro em logs principais. Exceções de transporte não têm seu corpo ou mensagem arbitrária copiados para o artifact.

A redação remove credenciais de variáveis de ambiente reconhecidas, formatos de chave/token/password, credenciais em URLs, hashes e paths conhecidos. O payload externo usa whitelist, e a evidência precisa ser válida tanto no contexto enviado quanto na solução original; texto redigido não é convertido artificialmente em citação original. Os testes incluem segredos em JSON e URL e verificam ausência nos excerpts e nas chamadas simuladas.

São registrados modelo solicitado, modelo resolvido, versão de prompt/schema, limite de tokens, temperature=0, timeout, store=false, tentativas e configuração de retry. Hashes de reprodução ficam apenas na metadata local, nunca no contexto enviado. Temperatura zero e schema estrito não são apresentados como garantia de decisões semânticas determinísticas ou corretas.

## Validação offline

Foram adicionados testes de contrato com respostas simuladas e integração local: JSON válido/inválido, valores proibidos, bool/NaN/infinito, IDs, evidência inexistente, rationale ausente, campos extras, enums, chaves duplicadas, requisito inventado, award/deny, retry e falha final. Há casos de pauta real para F2Q1, F2Q5, Q3 e Q4, além do SDK com transporte simulado e persistência do artifact pelo motor.

Os testes focados finais passaram com **589 casos**. Reruns focados não são somados novamente ao total único da suíte. Os testes de longa duração usam Lean local; nenhum provedor externo é acionado. O runner remove chaves de provedores e bloqueia sockets IP.

A primeira rodada ampla revelou quatro diferenças de metadata no teste de paridade controlada. Sua reconstrução ainda não repassava o claim_context já reconstruído, ao contrário do motor atual. O helper foi corrigido mantendo a asserção de igualdade integral. Os seis perfis controlados passaram; a guarda de paridade do pipeline, que havia importado o helper anterior, também passou na revalidação. Os logs iniciais permanecem disponíveis e o `revalidation_manifest.json` identifica exatamente os nós revalidados, sem ocultar falhas ou duplicar contagens.

Três testes acrescentados durante a primeira coleta têm um grupo suplementar disjunto. `collection_final.log` e `groups.json` permitem conferir a cobertura de todos os casos únicos. O teste de imutabilidade roda isolado ao final, sem escritores concorrentes de artifacts e com stdout em /tmp.

<!-- FINAL_VALIDATION_START -->
Resultado final: **1633 testes únicos — 1629 passed, 3 falhas preexistentes, 1 xfailed esperado**. Nenhuma regressão nova permanece.

| Grupo | Passed | Failed | Xfailed |
|---|---:|---:|---:|
| reference_pipeline | 75 | 0 | 0 |
| proof_pipeline | 149 | 0 | 1 |
| broad | 1401 | 3 | 0 |
| immutability | 1 | 0 | 0 |
| supplemental | 3 | 0 | 0 |

São 59 testes novos: 58 no módulo de contrato e um teste de persistência no módulo API. Os perfis revalidados substituem os resultados anteriores dos mesmos nós, sem dupla contagem.

As três falhas conhecidas são HMER (`test_projection_preserves_falsehoods_signs_and_general_fractions`), UI vocabulary (`test_central_product_vocabulary_is_preserved_without_contract_renames`) e tablet sticky (`test_parent_statement_is_compact_and_sticky_through_notebook_and_submission`). O xfail F2Q6 foi mantido; essas falhas não foram corrigidas.

Preservação: 321 arquivos históricos Smoke V2 idênticos por SHA-256; 3085 arquivos preexistentes idênticos. Somente os seis arquivos preexistentes previstos foram modificados, além dos três novos arquivos da tarefa. HEAD e índice idênticos; nenhum staged. `git diff --check`: OK.

O estado Git completo está em `git_status_short.txt`; contagens por status: {' M': 55, '??': 43}.
<!-- FINAL_VALIDATION_END -->

## Arquivos e limites de escopo

Alterações de produção: `rubric/secondary_adjudicator.py`, novo `rubric/secondary_context.py`, wiring/diagnósticos em `rubric/scoring_policy.py` e persistência/contexto em `main.py`, todos sob `app/confia_lean_auditor/`. Testes: novo `test_secondary_adjudicator_contract.py`, atualização dos testes de score policy/API e do helper de reconstrução em `test_cap04_parity.py`. O conjunto exato está em `incremental_stat.json`.

Não foram alterados claims/extractors, canonicalização, checkers, Lean, UI, arquivos de problemas ou a política numérica. Nenhum trabalho anterior foi revertido. Não houve staging, commit, push, reset, restore ou clean.

Artifacts desta tarefa: `artifacts/evaluations/ita1000_v1_2/p0_secondary_adjudicator_01/`. Os arquivos obrigatórios são `implementation.diff`, `validation_summary.json` e `invalid_response_taxonomy.json`; também há snapshot, comparação da política, grupos/coleta da suíte, logs e verificações Git. O estado Git completo é salvo em `git_status_short.txt`, incluindo alterações anteriores que não pertencem a esta tarefa.

O próximo passo externo, fora desta entrega, é a reexecução separadamente autorizada dos mesmos 18 casos. Somente ela poderá medir a taxa real de respostas válidas e a qualidade dos julgamentos. O histórico atual não permite reconstruir os 17 raws perdidos, e esta auditoria não afirma ter recuperado essa informação.
