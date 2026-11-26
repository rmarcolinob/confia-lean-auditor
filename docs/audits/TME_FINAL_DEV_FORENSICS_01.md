# TME_FINAL_DEV_FORENSICS_01

**Recomendação: `GENERIC_FIX_BEFORE_HOLDOUT`.**

P5_02/c.four_product é principalmente **`SYSTEM_SCOPE_ERROR`**: uma referência a “(c)” dentro de (d) altera deterministicamente a seção de origem dos trechos. A fronteira incorreta permite promover evidência de (d) para uma obrigação de (c), sem autorização dessa direção. A seleção do modelo contribui, mas o defeito geral está no cálculo das fronteiras e metadados de escopo. O efeito chega à pauta; não é apenas uma referência de apresentação.

Os três pipelines Sol inválidos falharam de modo seguro: dois por divergência entre o contrato JSON permitido e a validação adicional de preservação de IDs; um por timeout. Nenhum deles produziu crédito semântico de substituição. Não há indicação de que seja necessário mudar prompts ou julgamento matemático para corrigir o defeito de fronteira.

**Zero chamadas externas nesta tarefa. HOLDOUT processadas: 0/100. Nenhum resultado matemático alterado. Nenhum código, prompt, schema, parâmetro, pauta ou anotação foi modificado. Nenhum retry, novo experimento ou commit foi realizado.** Este relatório é o único arquivo criado nesta tarefa.

## 1. Escopo e fontes

Foram usados exclusivamente os artefatos existentes em `artifacts/evaluations/tme_model_ablation_dev25_live_01/`, incluindo a cópia congelada de código em `execution/`. Não foi consultado o código atual fora desse snapshot, banco de dados, serviço externo ou conjunto HOLDOUT. SHA registrado no experimento: `ea3ae12b0c62f7f266a1cd91da795e32dc43f326`.

Fontes primárias: [P5_02 — registro Sol](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/model_b.jsonl:21); [P1_12 — registro Sol](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/model_b.jsonl:2); [P2_10 — registro Sol](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/model_b.jsonl:8); [P4_19 — registro Sol](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/model_b.jsonl:18). As respostas completas estão no campo `sufficiency_provider.raw_output`; o request do gate está em `sufficiency_payload`. As conclusões abaixo distinguem resultado armazenado, reprodução local determinística e inferência sobre risco geral.

A checagem dos 233 arquivos protegidos do snapshot confirmou seus hashes contra `preflight.json`. Reproduções locais usaram funções puras desse snapshot para segmentação, vínculo, geração de schema e validação de respostas armazenadas. Não foi chamado o runner, provedor, checker, Lean ou PautaEngine para produzir novas avaliações. Não houve reescoragem, nem mesmo contrafactual.

## 2. P5_02 / c.four_product: cadeia completa

### Obrigação e evidência selecionada

- Obrigação: `c.four_product`.
- Item alvo: `c`.
- Descrição: “Igualdade de produtos na troca de quatro por dois dois.”
- Requisito: `INTERMEDIATE_STEP` — passo efetivamente desenvolvido; a resposta final não permite inventar passos.
- `authorized_source_items=[]`: nenhuma permissão declarada para importar (d).
- Sol selecionou **E013 e E016**; a expressão extraída `2 · 2 = 4` aponta especificamente para **E016**.

| ID | Texto integral da unidade | Origem textual real |
|---|---|---|
| E013 | Como 2026 = 3 · 674 + 4 e 4 = 2 + 2, a melhor decomposição é 674 números 3 mais dois 2's. | (c) |
| E016 | Os dois 2's que aparecem em (c) podem ser escritos separados ou reunidos em um 4, já que 2 + 2 = 4 e 2 · 2 = 4. | (d), imediatamente após E015 = `(d)` |

E016 ocupa `[1133,1244)` no texto original, em offsets de caracteres. O `(c)` na posição 1161 é uma **referência interna da frase**, não um cabeçalho. E013 fornece a decomposição e a igualdade de somas; a igualdade de produtos usada na seleção vem de E016.

Há evidência matemática no próprio item (c): E014 diz “A pontuação máxima é 3^674 · 2 · 2 = 4 · 3^674.” Ela **não foi selecionada**. Sua existência explica por que a revisão anterior registrou vínculo incorreto, em vez de inventar um falso crédito matemático. Não se corrigiu a seleção retroativamente com E014.

### Metadados e fronteira incorreta

Na entrada da etapa semântica, E016 tem `item_hint=["c","d"]`. O gerador de hints reconhece marcadores inline sem distinguir referência de seção. No gate, há um segundo cálculo de fronteiras; ele também erra, por uma condição mais específica.

A reprodução local de `sufficiency_context.item_regions` retornou:

```text
a: [0,455)
b: [455,706)
c: [706,1129)
d: [1129,1161)
c: [1161,1460)  <- referência interna promovida a nova seção
```

Em `item_regions`, a condição `topical` aceita um marcador quando o texto anterior termina em `para` ou `em`. A frase “Os dois 2's que aparecem em (c)” satisfaz esse teste. O código não exige que “em” inicie uma transição de seção. [sufficiency_context.py](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/execution/app/confia_lean_auditor/student_claims/sufficiency_context.py:12); [geração de item_hint](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/execution/app/confia_lean_auditor/student_claims/hybrid_semantic.py:105).

O resultado armazenado de E016 é:

```text
item_id=null; multiple_items=true
item_slices:
  d [1133,1161): "Os dois 2's que aparecem em "
  c [1161,1244): "(c) podem ser escritos separados ou reunidos em um 4, já que 2 + 2 = 4 e 2 · 2 = 4."
```

`link_evidence` autoriza a segunda fatia como se ela pertencesse a (c). Registra `valid=true`, `exceptions=[]`, `rejected=[]`, `unassigned_item=false`. Portanto, não houve uma autorização explícita e auditável de (d)→(c): houve **reclassificação equivocada da origem**. O contexto local de (c) também incorpora o restante de (d). E017/E018 passam a ser rotulados como (c), com potencial para bloquear apoios legítimos em (d).

O request do gate contém E016 já cortado para o trecho que começa em “(c) podem...”, com `item_ids=["c"]`. A parte da frase que revelava a referência a outro item foi retirada. Reproduzir `link_evidence` sobre a mesma fonte, requisito e IDs devolve novamente `valid=true` e essas mesmas fatias. [link_evidence](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/execution/app/confia_lean_auditor/student_claims/sufficiency_context.py:52).

### Julgamento, gate, reconciliador e pauta

| Camada | Resultado armazenado |
|---|---|
| SemanticRubricEvaluator | `satisfied`, `asserted`, confiança `high`, `method_path=c.normal_counts`, IDs E013/E016 |
| Rationale semântico | “Em (d), o estudante retoma explicitamente os dois 2 de (c) e explica que sua reunião em 4 preserva também o produto.” O próprio parecer reconhece a origem em (d). |
| Context gate | `valid=true`, `asserted_with_global_revision_check` |
| Sufficiency | `sufficient`, `adequate_evidence`, E013/E016; rationale: “E016 escreve 2 · 2 = 4 e associa essa igualdade à reunião ou separação das parcelas.” |
| Auditoria primária e seletiva dessa obrigação | Ambas `indeterminate`, `NO_EXISTING_FACT`; não há verificação determinística/Lean sustentando esta promoção |
| Reconciliação efetivamente usada | `supported`, `SEMANTIC_SUPPORTED`, `conflict=false`, `independent_sufficiency_and_context_passed` |
| Evidence entregue à pauta | `origin=semantic`, `grounding_status=grounded`, `attributable_to_student=true`, `context_valid=true`, confiança `high`, refs E013/E016 |
| HybridEvidencePolicy / observação da pauta | Aceita a evidência; `input_status=supported`, `effective_status=supported`, `reason=UPSTREAM_STATUS` |
| c.normal_counts | `all_of`, **2/2 pontos**, `fully_satisfied=true`, `needs_review=false`, `reason=SUPPORTED` |
| Item (c) | **4/6 pontos**, caminho `c.official_replacement_path`, `needs_review=true` |
| Avaliação shadow total | **11/20**, `known_points=11`, `possible_points=20`, `needs_review=true` |

O reconciliador base mantém precedência das auditorias; como ambas são indeterminadas nesta obrigação, a promoção é feita por `reconcile_sufficiency`, após confiar em gate e vínculo. A policy e o engine recebem esses estados já afirmativos e não reinterpretam as fronteiras da fonte. [reconciliação de sufficiency](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/execution/app/confia_lean_auditor/tme/sufficiency_experiment.py:31); [HybridEvidencePolicy](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/execution/app/confia_lean_auditor/rubric/pauta/evidence_policy.py:6); [PautaEngine.observe](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/execution/app/confia_lean_auditor/rubric/pauta/engine.py:62).

`c.four_product` é um dos seis requisitos do bloco `c.normal_counts`: `c.four_sum`, `c.four_product`, `c.twos_sum`, `c.twos_gain`, `c.threes_count`, `c.twos_count`. Os **2 pontos são do bloco**, não dois pontos independentes exclusivos de `c.four_product`. O vínculo defeituoso participou efetivamente de sua habilitação. Não se conclui que os 2 pontos sejam matematicamente indevidos nesta solução, pois E014 contém a relação pertinente; conclui-se que a cadeia de autorização usada para concedê-los é defeituosa. [pauta congelada de P5](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/execution/examples/pautas/tme2_problem5.v1.json).

### Atribuição causal

| Camada | Diagnóstico |
|---|---|
| Seleção semântica | Contribui: escolhe (d) para obrigação de (c), explicitando isso no rationale. Há componente de `MODEL_SELECTION_ERROR`. |
| Evidence-unit metadata | Texto, IDs e offsets estão íntegros; `item_hint` e `item_slices` confundem referência com origem. |
| Item/context boundary | **Causa determinística principal:** aceita “aparecem em (c)” como mudança de seção. |
| Sufficiency | Aprova uma igualdade verdadeira sobre fatias apresentadas incorretamente como (c); não protege contra essa origem já corrompida. |
| Reconciliador | Propaga os certificados positivos de escopo e suficiência; não há fabricação por fallback. |
| Policy | Confia nos metadados de reconciliação; aceita conforme o contrato atual. |
| PautaEngine | Aplica corretamente `all_of` aos estados recebidos. Não é defeito de soma ou estratégia de scoring. |

**Classificação principal: `SYSTEM_SCOPE_ERROR`, com contribuição da seleção semântica. Não é `TRACEABILITY_ONLY`.** O erro entra na decisão de apoio e no bloco de pontos, embora não esteja demonstrado excesso matemático de nota neste caso particular.

### Generalidade P1–P5

O mecanismo é compartilhado por todos os problemas: `item_regions`, `annotated_units` e `link_evidence` não recebem problem_id e não contêm regra por caso. Os requisitos de P1–P5 passam pelo mesmo gate. Qualquer seção que contenha referência interna com a forma aceita pode ter parte de seu texto atribuída à seção mencionada. O alcance potencial inclui falso apoio e perda de cobertura por relabelagem de trechos posteriores.

Isso é uma conclusão da estrutura do código e da reprodução do texto real, **não uma afirmação de que o mesmo dano já foi observado nos cinco problemas**. A varredura dos 25 textos existentes encontrou P5_02 como o exemplo inequívoco dessa referência interna; também há transições legítimas com “Em/Para”, como P4_21. Uma correção não pode simplesmente proibir todo marcador inline ou toda expressão “em (x)”.

## 3. Os três pipelines Sol não válidos

Todos falharam na **etapa 2 — SemanticSufficiencyGate**. A etapa 1 estava válida nos três casos. Não houve retry nem aproveitamento parcial dos mapas rejeitados.

### Schema e contrato esperados

O schema de Structured Outputs é gerado pelo snapshot de `response_schema(payload)` e enviado com `strict=true`. Exige objeto raiz com somente `decisions`; esse mapa exige todas as obrigações solicitadas, sem chaves extras. Cada decisão exige `obligation_id`, `sufficiency`, `evidence_ids`, `reason_code` e `concise_rationale`. O ID da obrigação tem enum unitário; cada evidence_id deve pertencer ao enum de IDs selecionados para ela; a lista admite até 40 elementos; rationale até 900 caracteres. As quatro classes de suficiência são `sufficient/insufficient/contradictory/uncertain`.

**O schema permite subconjuntos de IDs.** Não exige que uma resposta `sufficient` repita o conjunto inteiro. Já o validador Python exige essa igualdade de conjuntos, além de unicidade e coerência do reason_code. Essa checagem adicional evita que o gate “conserte” uma seleção problemática descartando um ID. A rejeição é deliberada; a diferença entre os dois contratos é real. [schema e validação](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/execution/app/confia_lean_auditor/student_claims/semantic_sufficiency.py:77).

| Caso | Obrigações requeridas no gate | SHA256 do schema esperado |
|---|---:|---|
| TME2026P1_12 | 19 | `7a2b2662b827cbeac6dd449277f0a0d0050cc933830dce6a8d962209b5f4ebed` |
| TME2026P2_10 | 21 | `918369ae2fc280e34f215ff8d4f29b08ddc39c5ba7774cf5dc34ee8e9e79f8e9` |
| TME2026P4_19 | 26 | `d20fb5f5a59cd6253b972a0f6e7408df50fada526837e013615f5b04a9ba1bbc` |

Os três hashes foram reconstruídos e conferidos com a serialização canônica do runner (`ensure_ascii=false`, chaves ordenadas, separadores compactos). O payload armazenado fornece todas as obrigações e enums de evidência, permitindo reconstruir o schema completo sem API. Para as duas respostas existentes, uma checagem local das restrições efetivamente declaradas no schema passou; o validador de domínio congelado rejeitou ambas com o erro original.

### TME2026P1_12

- Recebida resposta JSON completa, com **19/19 decisões**; `response_status=completed`.
- Response ID: `resp_0fdf2eeae7c62487016ae8f33736c087d28060df839b039948`.
- Única decisão com redução indevida de IDs: `d.equation`.
- Esperado: `E011,E025,E026`; recebido: `E025,E026`.
- E011: `abc − cba = 99(a − c),`; E025: `Se a máquina produziu o resultado 594, então, pelo item (b),`; E026: `99(a − c) = 594,`.

Trecho exato da resposta:

```json
{"obligation_id":"d.equation","sufficiency":"sufficient","evidence_ids":["E025","E026"],"reason_code":"adequate_evidence","concise_rationale":"Os trechos do item d vinculam o resultado informado à equação explícita 99(a − c) = 594."}
```

Rejeição: `ValueError: positive_changed_selected_evidence`. Não é falha de leitura do JSON, não faltam obrigações e não houve timeout. O conjunto foi reduzido, embora os IDs restantes sejam permitidos pelo schema. A remoção pode parecer redundante matematicamente, mas viola o contrato de preservação da seleção; isso não foi reparado.

Usage do gate: **11.352 input / 2.064 output / 332 reasoning**, sendo reasoning parte do output; total 13.416 tokens. Latência 27,309 s. Limite configurado de output: 16.000. Resposta completa e JSON íntegro, sem sinal de truncamento ou token limit.

**Classificação: `SCHEMA_CONTRACT_FAILURE`** — resposta aceita pelo contrato JSON, rejeitada pelo contrato adicional de IDs. Comportamento do modelo: redução do conjunto selecionado. Não há evidência de `PARSER_FAILURE` ou `TOKEN_LIMIT_FAILURE`. A rejeição é integralmente reproduzível offline com raw_output + payload + validador congelado; não se afirma que uma nova geração repetiria o erro.

### TME2026P4_19

- Recebida resposta JSON completa, com **26/26 decisões**; `response_status=completed`.
- Response ID: `resp_0247644615227fc9016ae8fc4b8f9c87d196cbada8def0b8d1`.
- Três decisões `sufficient` reduzem o conjunto selecionado:

| Obrigação | Esperado | Recebido | ID retirado |
|---|---|---|---|
| b.qr | E001,E002 | E002 | E001 |
| b.pq | E001,E002 | E002 | E001 |
| c.h_plus_c | E001,E003,E004 | E001,E004 | E003 |

Trechos exatos da resposta:

```json
{"obligation_id":"b.qr","sufficiency":"sufficient","evidence_ids":["E002"],"reason_code":"adequate_evidence","concise_rationale":"A lista ordenada dos lados AP, PQ, QR e RA identifica QR=6-x."}
{"obligation_id":"b.pq","sufficiency":"sufficient","evidence_ids":["E002"],"reason_code":"adequate_evidence","concise_rationale":"A lista dos lados identifica PQ=x, valor também utilizado no cálculo do perímetro."}
{"obligation_id":"c.h_plus_c","sufficiency":"sufficient","evidence_ids":["E001","E004"],"reason_code":"adequate_evidence","concise_rationale":"E004 escreve e utiliza h+c=18, retomando a soma efetivamente desenvolvida em E001 para os dois perímetros sombreados."}
```

A primeira rejeição, na ordem do payload, ocorre em **b.qr**, com `ValueError: positive_changed_selected_evidence`; as outras duas violações foram identificadas pela inspeção do mapa completo, sem modificar a resposta. E003 contém a exclusão algébrica defeituosa de 12; sua retirada de `c.h_plus_c` ilustra por que a regra de preservação dos IDs não deve ser removida apenas para aumentar validade. Não se atribui intenção ao modelo nem se reavalia o julgamento matemático anterior.

Usage do gate: **18.405 input / 3.139 output / 907 reasoning**, total 21.544 tokens. Latência 45,061 s. Output abaixo do limite de 16.000, resposta completa, sem sinal de truncamento. Não houve timeout/API error.

**Classificação: `SCHEMA_CONTRACT_FAILURE`**, pelo mesmo motivo de P1_12. JSON e estrutura declarada íntegros; violação do contrato adicional. Rejeição reproduzida offline. Não é falha do parser de JSON, não é omissão de obrigação e não há evidência de token limit.

### TME2026P2_10

- Etapa 2 preparada para **21 obrigações**.
- `status=unavailable`, `reason=APITimeoutError`, `api_calls=1`, `retries=0`.
- Latência **180,162 s**, com timeout configurado de **180 s**.
- Sem `raw_output`, response ID, response status ou token usage registrados para o gate; `status_code=null`, `provider_error={}`.
- Não existe resposta para testar contra o schema. Não é possível determinar se o serviço concluiu alguma geração depois do timeout, se houve consumo ou se haveria truncamento.

**Classificação operacional: `API_TRANSIENT_FAILURE` (timeout de transporte).** A causa remota e a transitoriedade efetiva permanecem desconhecidas; o nome da categoria não prova que um retry resolveria. O registro do timeout e o comportamento de fallback são verificáveis localmente; **o timeout real não é reproduzível apenas pelos artefatos**. Não há evidência para `MODEL_STRUCTURAL_FAILURE`, `SCHEMA_CONTRACT_FAILURE`, `PARSER_FAILURE` ou `TOKEN_LIMIT_FAILURE` neste caso.

### Identificação das respostas completas

O conteúdo integral permanece nos registros Sol vinculados na seção 1. SHA256 de `raw_output` em UTF-8:

- TME2026P1_12: `8ef2137a1c3c1483c2d900cad49a8b69ec65953be2850897fd507eaf92ce2322` (6256 bytes UTF-8).
- TME2026P4_19: `cc2beabdab815d08d7a72095e12d4eb2ad990f5f1500426c7329d7c2782b270b` (7734 bytes UTF-8).

Não foram alteradas as classes históricas `INVALID_RESPONSE`/`API_ERROR` em `validity.json`. As classificações causais deste relatório apenas explicam esses registros.

## 4. Segurança observada

O provider valida o mapa completo antes de devolver decisões. Em erro, devolve nenhuma decisão remota utilizável. O runner impede que provider falho forneça decisões. O caminho shadow substitui as decisões remotas por `uncertain`, `reason_code=provider_error`, `evidence_ids=[]`; o reconciliador mantém estados técnicos ou indeterminados, salvo auditoria matemática independente já estabelecida. [fallback do gate](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/execution/app/confia_lean_auditor/tme/sufficiency_experiment.py:87); [runner congelado](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_model_ablation_dev25_live_01/execution/scripts/evaluation/evaluate_tme_model_ablation.py:185).

| Caso | Supported independentes | Refuted | Technical error | Indeterminate | Known points | Score | needs_review | Pontos semânticos adicionais |
|---|---:|---:|---:|---:|---:|---|---|---:|
| P1_12 | 3 | 2 | 15 | 1 | 1 | null | true | 0 |
| P2_10 | 1 | 0 | 20 | 2 | 1 | null | true | 0 |
| P4_19 | 0 | 0 | 26 | 5 | 0 | null | true | 0 |

Os três apoios preservados de P1_12 são `a.identifies_137`, `a.constructs_subtraction` e `d.equation`; o de P2_10 é `a.pair_sum`. Todos são `DETERMINISTIC_VERIFIED`, com `existing_mathematical_evidence_precedence`. Não surgiram da resposta rejeitada nem do timeout. Os known points coincidem com os do assessment audit-only.

**Confirmação:** nos três pipelines inválidos, não ocorreu fabricação automática de crédito. O estado literal não é exclusivamente `indeterminate`: o sistema usa também `technical_error`, preserva auditorias independentes e termina com `score=null / needs_review=true`. Não mascara falha técnica como nota zero ou decisão concluída.

**Limite da confirmação:** P5_02 é diferente. O erro de fronteira passa como vínculo válido, portanto não aciona o fallback. Pode habilitar crédito baseado em seção não autorizada; o `needs_review=true` geral não impede crédito parcial em um bloco individual `decided`. É possível que outra solução não contenha a igualdade em (c), ao contrário deste caso, e ainda assim o mesmo erro permita importar (d). Esse é risco geral inferido do mecanismo, não um novo resultado de avaliação.

## 5. Recomendação antes do congelamento

**`GENERIC_FIX_BEFORE_HOLDOUT`.**

Não recomendar `FREEZE_AS_IS`: há defeito determinístico de escopo com efeito na concessão de crédito, reproduzido sem modelo. Também não há base nesta investigação para declarar uma falha matemática sistêmica que exija redesenhar o avaliador; o defeito identificado tem fronteira técnica delimitada.

A correção futura deve ser genérica e restrita à proveniência:

1. Distinguir cabeçalho/transição de seção de referência interna; mencionar “em (c)” dentro de uma frase não pode alterar a seção de origem.
2. Manter separados **item de origem** e **item mencionado**. Autorizações entre itens devem ser explícitas no vínculo, nunca simuladas por relabelagem da fonte.
3. Usar interpretação consistente de fronteiras nos hints e nas fatias autorizadas, preservando texto, IDs e offsets das evidence units. Ambiguidade de fronteira não deve virar autorização positiva silenciosa.
4. Validar localmente contra os textos DEV existentes: referência interna de P5_02; cabeçalhos inline legítimos de P4_21; referências autorizadas entre itens; unidades mistas; propagação para unidades subsequentes. Não criar exceção para P5_02, para um nome de problema ou para seus números.
5. Preservar o fail-closed dos contratos e do timeout. Não relaxar `positive_changed_selected_evidence`, completar respostas, elevar limites ou adicionar retries para aproveitar esta rodada.

Esses pontos especificam uma mudança futura, **não implementada nem validada como correção nesta tarefa**. Não exigem editar prompts, schemas, julgamento matemático, pauta, checkers ou Lean. A diferença entre schema JSON e contrato de IDs fica documentada como questão de confiabilidade; por falhar com segurança, ela sozinha não justifica relaxar o contrato antes da HOLDOUT.

O `MODEL_ABLATION_GO` anterior permanece intacto como resultado comparativo dos modelos. Ele não equivale a `FREEZE_AS_IS` do pipeline. Qualquer correção posterior precisará de versão/hashes próprios e validação local antes de um novo congelamento; esta tarefa não autoriza nova inferência nem abertura da HOLDOUT.

**Encerramento: zero chamadas externas; HOLDOUT processadas: 0/100; nenhum resultado matemático ou nota persistida alterado; código inalterado. Recomendação final: `GENERIC_FIX_BEFORE_HOLDOUT`.**
