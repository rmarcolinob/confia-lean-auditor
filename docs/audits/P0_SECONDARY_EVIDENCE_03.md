# P0-SECONDARY-EVIDENCE-03

## Resultado

**COMPLETE.** As três adjudicações reais passaram na primeira tentativa: 3/3 válidas, 0 inválidas, 0 retries. Houve 6 awards e 6 denies entre 12 critérios pendentes. O modelo deixou de gerar texto de evidence; selecionou IDs de trechos reais. Foram executados somente os mesmos três casos de P0-SECONDARY-LIVE-02, sem batch 18/502/1000 e sem staging, commit ou push.

Validade contratual não equivale a acurácia matemática. As notas continuam sugestões do ConfIA, com review e cobertura primária preservados. O resultado não autoriza uma rodada maior automaticamente.

## Estado inicial e objetivo

P0-SECONDARY-LIVE-02 confirmou Structured Outputs e HTTP 200, mas permaneceu em 1/3 adjudicações válidas porque duas respostas copiavam ou parafraseavam trechos fora do texto literal. A validação rejeitava corretamente. Esta tarefa preservou esse trabalho e todos os artifacts anteriores; mudou a interface do adjudicador para seleção de evidência, sem ampliar o matcher de citações.

## Modelo de candidatos e seleção

O novo módulo secondary_candidates.py constrói no máximo **8 candidatos e 2400 caracteres por critério**, com no máximo 800 caracteres por span. Cada candidato tem evidence_id, source_text, source_start, source_end, source_kind e grounding_status. Quando disponíveis, os artifacts locais preservam claim_id, math_claim_record_id, semantic_role e verification_status. Offsets são índices de caracteres, zero-based e com fim exclusivo, sobre a solução original recebida.

Ordem de preferência: checks/claims grounded e relevantes já aceitos pelo gate de origem; MathClaimRecords relevantes e atribuíveis; evidência literal já associada ao critério e contexto local. A recuperação local usa parágrafos e sentenças/linhas, ranqueados por sobreposição lexical com descrição e requisitos existentes. Não faz matching semântico para aceitar uma resposta do modelo. Um único contexto curto pode ser usado para respostas breves quando não há outra evidência. Trechos longos sem limite natural podem ficar sem candidato.

Cada span é validado por igualdade exata com solution[source_start:source_end]. O texto não é reescrito. Spans duplicados no mesmo critério são eliminados; textos sensíveis são excluídos antes do envio. IDs são determinísticos no conjunto de critérios pendentes e restritos ao catálogo daquele critério. Grounded aqui atesta origem textual, não verdade matemática nem prova Lean.

A solução integral permanece local para validação. A API recebe somente candidatos do critério, enunciado e contexto mínimo da pauta. Paths, hashes, IDs internos de claims/MathClaimRecord e artifacts técnicos não são enviados. As verificações HTTP confirmaram a ausência de solution_text nas três chamadas. Há 3, 8 e 10 spans distintos, respectivamente, nos três casos; reaproveitamento entre critérios não equivale a fragmentar o documento em centenas de IDs.

## Contrato externo

Versão: **secondary-evidence-ids-v1**; prompt: **secondary-evidence-selection-v1**. O objeto raiz continua indexado pelos IDs exatos dos critérios pendentes. Cada decisão tem decision, suggested_points, evidence_ids, reason_code e rationale. Não existe campo evidence de texto livre na resposta exigida do modelo.

| Decisão / reason_code | Pontos | IDs |
|---|---:|---|
| award / SATISFIES_CRITERION | max_points | 1 a 3 IDs reais |
| deny / INSUFFICIENT_EVIDENCE | 0 | 0 a 3 IDs; vazio permitido |
| deny / CONTRADICTS_CRITERION | 0 | 1 a 3 IDs reais |
| deny / INCOMPLETE_FOR_CRITERION | 0 | 1 a 3 IDs reais |

Structured Outputs usa anyOf por critério para restringir conjuntamente decisão, pontos, reason_code, rationale e cardinalidade de IDs. Cada ID é enum dos candidatos daquele critério. Campos são obrigatórios e extras são proibidos. Se não houver candidatos, o schema permite apenas deny + INSUFFICIENT_EVIDENCE com array vazio; não inventa ID sentinela. Duplicatas são rejeitadas localmente.

Rationale permanece em um vocabulário curto e fechado derivado da pauta. Não é permitido exigir “conclusão formal”, prova extra ou qualquer requisito novo. Para insuficiência, a justificativa se refere explicitamente aos candidatos disponíveis, não a uma suposta demonstração de ausência no documento inteiro.

## Validação e fronteira com a score policy

validate_selections é a única porta de entrada para o output atual do modelo. Ela valida IDs de critérios, decisão, allowed_points, razão coerente, IDs únicos/existentes, origem literal de todos os candidatos, award com evidência e rationale autorizada. Não compara texto gerado com a fonte e não chama fuzzy matching ou o normalizador textual histórico. Há teste que proíbe explicitamente a chamada do matcher textual no contrato por IDs.

resolve_selections materializa evidence a partir dos source_text locais. Esse campo interno não é redigido pelo modelo: é uma cópia dos spans apontados. validate_decisions verifica de novo que o texto resolvido corresponde exatamente aos IDs antes de entregá-lo à **score_policy.py inalterada**. Isso preserva a interface de persistência/UI e permite evidence=[] somente no retorno moderno com reason_code adequado.

Deny não transforma indeterminate em refuted. Os 12 critérios secundários continuam com points=None, mathematical_status=indeterminate e scoring_basis=secondary_adjudication; somente suggested_points muda. Critérios supported/refuted permanecem fora do conjunto solicitado. Fórmulas de score, coverage, estimated_points e needs_review não foram modificadas.

## Persistência e compatibilidade histórica

Por critério, secondary_adjudication.json e rubric_assessment.secondary_adjudication preservam candidate_evidence, selected_evidence_ids, resolved_evidence_text, decision, suggested_points, reason_code, rationale, validation_status e retry_count. As respostas e corpos HTTP redigidos são mantidos, sem headers de autenticação. criterion_traces.json consolida os 12 critérios desta rodada.

A leitura de artifacts históricos permanece textual: validate_decisions e legacy_text_schema mantêm o contrato anterior para compatibilidade/offline. O módulo antigo de normalização textual não foi ampliado e não é usado na seleção de IDs. Os testes passam envelopes reais antigos pelo SDK em transporte simulado e validam a interpretação histórica. Um teste separado confirma que o endpoint atual rejeita outputs antigos com evidence livre; não há fallback silencioso para o contrato obsoleto.

Os metadados históricos mantêm suas versões e não recebem IDs fabricados. Os fixtures antigos não foram sobrescritos. Os três envelopes HTTP novos estão em tests/fixtures/secondary_evidence_03/ e são reexecutados apenas offline pelo SDK real.

## Resultados dos três casos

| Caso | LIVE-02 | Agora | Primário | Coverage | Estimados | Review |
|---|---|---|---|---|---|
| ITA2025Q1_S001_L04 | accepted; score=10.0 | accepted; score=10.0 | 3.0 | 30% | 7.0 | True |
| ITA2025Q1_S016_L01 | rejected; score=None | accepted; score=2.0 | 0.0 | 0% | 2.0 | True |
| ITA2025Q4_S003_L04 | rejected; score=None | accepted; score=5.0 | 1.0 | 10% | 4.0 | True |

| Caso | Critério | Candidatos | IDs selecionados | Decisão | Pontos | Reason |
|---|---|---:|---|---|---:|---|
| ITA2025Q1_S001_L04 | area_formula | 1 | E1_1 | award | 3 | SATISFIES_CRITERION |
| ITA2025Q1_S001_L04 | equation | 3 | E2_1, E2_2, E2_3 | award | 2 | SATISFIES_CRITERION |
| ITA2025Q1_S001_L04 | positive_root | 1 | E3_1 | award | 2 | SATISFIES_CRITERION |
| ITA2025Q1_S016_L01 | coordinates | 3 | E1_1, E1_2, E1_3 | deny | 0 | INSUFFICIENT_EVIDENCE |
| ITA2025Q1_S016_L01 | area_formula | 6 | E2_1, E2_2, E2_3 | deny | 0 | INSUFFICIENT_EVIDENCE |
| ITA2025Q1_S016_L01 | equation | 6 | E3_1, E3_2, E3_3 | deny | 0 | INSUFFICIENT_EVIDENCE |
| ITA2025Q1_S016_L01 | positive_root | 2 | E4_1, E4_2 | award | 2 | SATISFIES_CRITERION |
| ITA2025Q1_S016_L01 | final_answer | 1 | E5_1 | deny | 0 | INSUFFICIENT_EVIDENCE |
| ITA2025Q4_S003_L04 | positive_witnesses | 3 | E1_1 | award | 2 | SATISFIES_CRITERION |
| ITA2025Q4_S003_L04 | same_f_argument | 5 | E2_1, E2_2, E2_3 | deny | 0 | INSUFFICIENT_EVIDENCE |
| ITA2025Q4_S003_L04 | distinct_g_inputs | 8 | E3_1 | award | 2 | SATISFIES_CRITERION |
| ITA2025Q4_S003_L04 | equal_g_values | 3 | E4_1, E4_2, E4_3 | deny | 0 | INSUFFICIENT_EVIDENCE |

Todos os IDs selecionados existem no catálogo correto e resolvem para texto original. Os seis denies reais usam INSUFFICIENT_EVIDENCE e podem retornar []; nenhum foi convertido em refutação matemática. Os critérios supported/refuted dos três casos são idênticos aos da rodada LIVE-02.

As notas 10, 2 e 5 demonstram produção de decisões válidas, não comparação de qualidade com labels sintéticos. Nos casos com poucos candidatos úteis, um deny pode refletir a recuperação limitada ou julgamento do modelo. A seleção de um trecho real ainda pode ser matematicamente inadequada para o critério; a enumeração de IDs resolve atribuição textual, não certifica todo o raciocínio do adjudicador.

## Evidência da execução real

Foram três requisições e três respostas HTTP 200, sem retry. Modelo solicitado: gpt-4o-mini; resolvido: gpt-4o-mini-2024-07-18. O SDK leu output_text e aplicou o parser JSON com proteção contra chaves duplicadas. Os schemas retornados nos envelopes coincidem com os schemas enviados, incluindo os enums de IDs e as quatro alternativas. Não houve alteração de código entre o início e o final dos três casos; live_source_hashes.json comprova esse estado.

A instrumentação verificou endpoint, critérios pendentes, limites do catálogo e cada span antes de enviar. A execução parou após o terceiro caso. Não houve OpenAI para outro caso ou Mathpix.

## Testes offline

**176 testes passaram, incluindo 35 novos.** Antes do live: 173 passaram; depois foram acrescentados três replays dos envelopes reais, todos com transporte MockTransport e sockets externos bloqueados. Sete módulos cobrem contrato, integração com score policy/API, ponte de rubrica, compatibilidade histórica e o modelo de candidatos.

Cobertura nova: award com ID válido; award vazio/inventado; deny com IDs; deny vazio com insufficient; reason incorreto; IDs duplicados ou de outro critério; critério errado; pontos inválidos; rationale com requisito inventado; adulteração de offsets/texto/status de origem; ausência de candidatos; limites e determinismo; ausência de envio de solução integral/secrets; independência do matcher textual; preservação de supported/refuted e indeterminate; artifacts antigos; três respostas HTTP reais.

Na primeira rodada ampla, dois testes de API ainda enviavam evidence textual e falharam corretamente no novo contrato. Os mocks foram migrados explicitamente para evidence_ids, mantendo asserções de rejeição, persistência e isolamento da primeira passagem. Os logs iniciais foram preservados. Não se converteu automaticamente uma resposta antiga em IDs para fazê-la passar.

A suíte histórica inteira não foi executada. Falhas conhecidas HMER, UI vocabulary, tablet sticky e xfail F2Q6 não foram corrigidas nem declaradas revalidadas. Não houve regressões nos 176 testes executados.

## Arquivos e preservação

- `app/confia_lean_auditor/rubric/secondary_adjudicator.py`
- `app/confia_lean_auditor/rubric/secondary_context.py`
- `tests/test_secondary_adjudicator_contract.py`
- `tests/test_secondary_live_contract.py`
- `tests/test_score_policy_api.py`
- `app/confia_lean_auditor/rubric/secondary_candidates.py`
- `tests/secondary_selection_helpers.py`
- `tests/test_secondary_evidence_ids.py`
- `tests/fixtures/secondary_evidence_03/ITA2025Q1_S001_L04.json`
- `tests/fixtures/secondary_evidence_03/ITA2025Q1_S016_L01.json`
- `tests/fixtures/secondary_evidence_03/ITA2025Q4_S003_L04.json`
- `docs/audits/P0_SECONDARY_EVIDENCE_03.md`

Foram preservados 661 arquivos históricos por SHA-256. Somente os cinco arquivos preexistentes listados foram alterados. Claims, rubricas de problemas, Lean, canonicalização, score policy, UI e textos do dataset permaneceram idênticos ao snapshot. HEAD e índice Git preservados; staged vazio. git diff --check: OK. O status completo está em git_status_short.txt.

Artifacts obrigatórios em artifacts/evaluations/ita1000_v1_2/p0_secondary_evidence_03/: implementation.diff, validation_summary.json e three_case_results.json. O diff é incremental contra o estado inicial desta tarefa, incluindo as alterações já existentes como baseline; não é um diff acumulado contra HEAD.
