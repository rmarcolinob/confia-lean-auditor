# ConfIA Dynamic — protocolo experimental DY7

A certificação usa o armazenamento D7 compartilhado e permanece `SHADOW_EVALUATION`. Nenhuma rota abaixo cria nota oficial, altera HumanDecision ou finaliza correções. O harness sintético exercita essas operações separadamente, identificadas como demonstração técnica.

## Artefatos e responsabilidades

`Assessment + QuestionAttempt + TranscriptionVersion aceita` → `HumanGold independente/versionado` → `dataset congelado` → `G0/DY3` → `G1/DY4` → `G2/DY5` → `G3/HumanDecision opcional` → `CertificationRun imutável`.

- HumanDecision é a decisão operacional; nunca é copiada automaticamente para HumanGold.
- HumanGold mantém a cadeia `gold_*.json` de D7. A importação registra fonte, versão, avaliador, data, vínculo de versões, critérios, cegamento declarado e adjudicação. Raters independentes ficam no mesmo registro; adjudicação exige dois ou mais ratings e justificativa. O gold final é informado explicitamente.
- A fronteira permanece textual. O benchmark não conhece OCR, HTR, páginas ou tecnologia de captura.
- Gold pode ser importado antes de qualquer auditoria. A validação usa a rubrica aprovada, sem exigir ou mostrar a sugestão do agente. A área Resultados mostra resultados: quem a consultou deve declarar a exposição e não afirmar cegamento. Cegamento é metadado declarado, não uma garantia de isolamento institucional do avaliador.
- Os registros do piloto têm `reference_kind=SYNTHETIC_FIXTURE`, `blind=false`. Eles não são avaliações científicas feitas por humanos independentes. `HUMAN` é reservado a referências humanas reais.

## API real

Requer o avaliador titular da avaliação e `CONFIA_TME_CERTIFICATION_ENABLED=1`. Prefixo: `/tme/assessments/{assessment_id}/certification`.

1. `POST /gold`: contrato D7 `GoldImport`, JSON. `GET /gold?version=N` recupera referência/histórico.
2. `POST /datasets`: congela versão do dataset, gold, protocolo, código da aplicação, tentativas, transcrições, contextos, grupos, split, origem, domínio, dificuldade e tipo de solução. `protocol_sha256` é `canonical_sha256(protocol)`. `GET /datasets/{id}` recupera o protocolo congelado.
3. Executar as rotas DY6 existentes de aceite, auditoria, revisão e reconciliação. Captura não chama diretamente o motor.
4. `POST /runs` com `{"dataset_id":"dataset_<64 hex>"}` cria uma única fotografia do experimento. Retry idêntico retorna o mesmo resultado; parâmetros diferentes não substituem uma execução.
5. `GET /runs`, `GET /runs/{id}`, `/runs/{id}/export.json`, `/runs/{id}/export.csv`, `/runs/{id}/report.md`.
6. A projeção D7 atual continua em `GET ?selection=current`; não é um benchmark congelado. `selection=finalized` preserva a seleção D6 existente.
7. `POST /comparisons` cria comparação persistida a partir de um run Dynamic e de auditorias Specialized reais. `GET /comparisons/{id}` recupera o resultado.

O JSON de importação Dynamic estende cada linha D7 com:

```json
{
  "binding": {
    "question_attempt_id": "case_<32 hex>",
    "transcription_version_id": "tr_<32 hex>:1",
    "statement_version": 1,
    "statement_sha256": "<64 hex>",
    "rubric_id": "drub_<32 hex>",
    "rubric_version": 1,
    "rubric_sha256": "<64 hex>"
  },
  "evaluation": {
    "evaluator_id": "rater-A",
    "evaluated_at": "2026-11-12T12:00:00Z",
    "blind": true,
    "blindness_note": "Avaliador não consultou sugestões do agente.",
    "reference_kind": "HUMAN",
    "adjudication_status": "SINGLE_RATER",
    "requires_review": true,
    "review_reason": "Conclusões adotadas em conflito."
  }
}
```

Os marcadores acima devem ser substituídos pelos IDs/hashes reais da tentativa, transcrição e contexto publicado. Também são obrigatórios os campos D7 `assessment_id`, `participant_code`, `question_id`, `gold_score` e `max_score`. `rubric_gold` é opcional; quando informado para Dynamic deve cobrir integralmente a rubrica e somar o score. Cada critério contém `rubric_item_id`, `gold_points`, `max_points`, comentário/status opcionais. Ratings opcionais registram `rater_id`, `score`, `criterion_points`, `blind`, `independent` e `evaluated_at`.

CSV simples de cinco colunas continua válido para o D7 legado; **não basta para importar gold Dynamic**, que exige os vínculos e a provenance do JSON.

## Congelamento e HOLDOUT

DEV, VALIDATION e HOLDOUT são explícitos em cada caso. `group_id` e participante não podem cruzar splits dentro de um dataset. Respostas textuais idênticas ao mesmo enunciado não podem atravessar splits. Tentativas já registradas não podem ser recicladas em outro dataset; a mesma resposta registrada não pode ser reutilizada como HOLDOUT no mesmo Assessment.

HOLDOUT exige ausência de auditorias anteriores no congelamento. A execução verifica a cronologia do AuditRun, hash do gold, hash da aplicação, versões do contexto/transcrição, configuração dos providers, versões de dependências Python e hashes de toolchain/manifests. O protocolo inclui o hash do arquivo de casos e do harness. Gates também são declarados no congelamento, antes de observar resultados. A execução é única por dataset: alterações posteriores exigem novo dataset e novas tentativas/holdout. Isso não impede uso indevido fora deste serviço; a equipe ainda deve controlar acesso aos dados e registrar decisões de pesquisa.

O piloto mantém questões repetidas entre splits e respostas distintas: mede holdout de respostas, **não generalização para problemas inéditos**. A preparação continua independente de problem IDs específicos, mas esta limitação experimental não deve ser omitida.

## Métricas e denominadores

- G0: grader original persistido. G1: proposta independente após os gates de evidência DY4; não o score cru do fornecedor. G2: sugestão reconciliada. G3: nota total da decisão humana. GOLD: referência D7 separada.
- N de score: estágio com score disponível, gold comparável e sem falha técnica. Ausência/erro não vira zero. G1 pode ter critérios válidos e total indeterminado; os critérios continuam mensuráveis.
- MAE = média de `abs(pred−gold)`; RMSE = raiz da média de quadrados; bias = média de `pred−gold`; exata usa igualdade Decimal; tolerâncias ±1/±2 incluem a borda. Erro normalizado = média de `abs(pred−gold)/max_score`.
- False credit: `pred_points > gold_points` no mesmo critério e máximo. Missed credit: `<`. As taxas usam **todos os pares de critérios comparáveis** como denominador; não apenas os positivos. Over/under credit são somas dos excessos/faltas de pontos. Severidade é a diferença absoluta dividida pelo máximo do critério. Não se confunde presença binária de crédito com excesso parcial.
- G3 não inventa distribuição por critério quando HumanDecision só registra nota total. Nessas condições, N por critério é zero.
- Review rate: estágios concluídos que exigem revisão / estágios concluídos, inclusive os de score indeterminado. Automation coverage: scores disponíveis, sem revisão e sem falha técnica / todos os casos registrados. Falhas e exclusões continuam nos totais operacionais.
- Unsafe automation: casos automáticos com gold comparável e erro total **ou por critério** maior que o limiar experimental declarado. O denominador é o número de automáticos com gold comparável; não se assume risco zero quando ele é zero. O piloto usa >1 ponto como definição experimental, não limite institucional.
- Review precision: entre encaminhamentos com label independente `requires_review`, a fração cujo label é verdadeiro. Encaminhamento desnecessário e revisão perdida usam esse label. Sem label, a métrica não é fabricada.
- Review usefulness: fração dos casos revisados com G3 e gold comparável em que o erro absoluto de G3 é menor que o de G2. Não demonstra efeito causal da revisão.
- Reviewer value: erros de G0 sinalizados por mudança de nota/critério ou flag de revisão; false alarms são sinais quando G0 coincide com gold; missed errors são erros não sinalizados. É uma definição operacional de sinal, separada da precisão de encaminhamento baseada em labels.
- Reconciliation value: erros corrigidos/introduzidos entre G0 e G2, critérios de falso crédito removidos, crédito perdido recuperado e pontos recuperados/removidos. Acordo errado inclui desacordo com gold por critério mesmo quando o total coincide. A trilha registra o primeiro estágio observado com excesso de crédito por critério.
- Human override: G3−G2, taxa não zero, média assinada, ajustes para cima/baixo. Override não é automaticamente erro de G2; a comparação científica usa gold.
- Feedback coverage: decisão corrente com política AFTER_CONFIRMATION, conforme contrato DY6. Significa elegibilidade, não entrega real de feedback ao aluno.

## Estratos, incerteza e falhas

Não se agrega precisão de SYNTHETIC, CURATED e REAL_STUDENT em um único número. Perfis e splits também permanecem separados; cada estrato permite domínio, tipo de solução, dificuldade declarada/basis e presença/resultado de checker. Essas associações não são inferência causal.

Bootstrap de MAE G2: 1.000 reamostragens por cluster `group_id`, semente registrada, percentis 2,5%/97,5%. Só é apresentado a partir de 20 grupos; abaixo disso aparece N e `PILOT_SMALL_SAMPLE`. Esse mínimo é uma convenção prudencial de relatório, não garantia de validade estatística. Não há teste de superioridade. Acordo humano usa diferenças de score de pares de raters declarados independentes: N, exata e MAE; não se inventam ICC/kappa para este piloto.

Exclusões: gold ausente, vínculo ausente, transcrição/rubrica/enunciado divergentes, gold não adjudicado e tentativa inválida. Falhas técnicas são separadas por estágio; provider, checker e incerteza técnica de reconciliação não são convertidos em erros matemáticos. Ausência de um estágio aparece como UNAVAILABLE com N explícito. Problemas de persistência impedem publicação do run em vez de produzir um resultado parcial silencioso.

DY3 não executa Lean nesta fronteira; exporta proposições verificadas, versão do checker e `lean_executed=false`. Verificação determinística/simbólica não recebe rótulo Lean. A validação Lean real da infraestrutura existente continua separada e com a pendência Mathlib do DY6.

## Comparação Specialized × Dynamic

`END_TO_END` usa cada preparação natural, com diferenças declaradas. `COMMON_RUBRIC` exige alinhamento completo, mesmos máximos e obrigações literalmente idênticas; condições não comprovadas são excluídas. Ambos os braços são lidos de auditorias reais e mantidos separados. O adapter verifica autorização, origem do audit, texto idêntico, enunciado do catálogo Specialized, máximo de score e fidelidade do gold Dynamic. Não encaminha claims/checkers/soluções curadas Specialized ao Dynamic.

Totais pareados usam o mesmo registro de gold, com identificação/hash. Métricas por critério exigem alinhamento explícito e justificado. Sem alinhamento, não se inventam diferenças de falso/missed credit. Os resultados mostram Dynamic better, Specialized better, tie e delta de erro absoluto (Dynamic−Specialized), além de review rate. Não há comparação empírica legítima neste piloto de problemas novos: N comparável será reportado como zero, sem alegar superioridade.

## Execução e reprodução

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app .venv/bin/python \
  scripts/evaluation/run_dynamic_certification.py \
  --dataset benchmarks/dynamic/dy7/controlled_01.json \
  --storage /caminho/novo/isolado \
  --output /caminho/resultados
```

O armazenamento deve estar vazio. O harness usa problemas novos e IDs gerados, preparação DY2, sugestão de rubrica, aprovação técnica explícita, contratos DY6 e D7 reais. Providers sintéticos recebem somente o payload do estágio e não recebem gold, split ou respostas G0. O reviewer fixture é deliberadamente maximalista; os gates reais avaliam suas propostas. Não representa uma segunda IA real.

`--live` é uma execução separada, exige os providers configurados e autorização para envio externo. O gold e a rubrica do protocolo continuam fixos; a rubrica sugerida por provider é preservada e editada explicitamente para o contrato pré-declarado antes da aprovação técnica. Não é validação humana de uma rubrica gerada automaticamente. Nunca use a execução live para ajustar o HOLDOUT já observado.

## Vereditos

Sem gates: `PILOT_METRICS_AVAILABLE` ou `INSUFFICIENT_EVIDENCE`. Com gates pré-declarados: `GATE_NOT_MET`, `INSUFFICIENT_EVIDENCE` ou `GATE_MET_FOR_DEFINED_PROFILE`. Nenhum implica produção, correção oficial, superioridade estatística ou certificação geral do Dynamic.
