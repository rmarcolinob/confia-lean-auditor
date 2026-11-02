# TME_MODEL_ABLATION_LIVE_01

**MODEL_ABLATION_NO_GO — BLOCKED_PREFLIGHT.** Ambos os modelos estão acessíveis pela API, mas o transporte congelado envia um parâmetro incompatível com o comportamento documentado do candidato. Smoke e DEV 25 não foram executados. Esta é uma decisão operacional, sem avaliação de qualidade dos modelos.

**HOLDOUT processadas: 0/100.**

## Preflight e congelamento

- Branch: `feat/tme-dual-input`.
- SHA completo: `6bb2bf3d7deb0cffe591a16db520a0e81db2d6c6`.
- `git status --short` vazio antes das consultas externas.
- Runner: `scripts/evaluation/evaluate_tme_model_ablation.py`, idêntico ao validado em TME_MODEL_ABLATION_PREP_01.
- Casos smoke: `TME2026P1_06`, `TME2026P2_01`, `TME2026P3_02`, `TME2026P4_13`, `TME2026P5_09`.
- Ordem congelada: A seguido de B para cada caso.
- Braço A: `gpt-4o-mini-2024-07-18`; braço B: `gpt-6.1-sol`.
- Configurações diferem somente no identificador do modelo. Ambas enviariam temperatura 0, `store=false`, limite de 16.000 tokens, timeout de 180 segundos e zero retries. Nenhum override de reasoning.

O dry-run local confirmou 5 casos, 2 braços, duas etapas, 10 chamadas iniciais e até 10 chamadas de suficiência. Foram conferidos os hashes de 232 arquivos protegidos, sem divergências frente ao PREP. Não foram alterados código, prompts, schemas, evidence units, gates, reconciliadores, políticas, pautas, checkers, Lean ou scoring.

Hashes dos prompts, iguais entre A e B:

- Primeiro avaliador: `590349b9a1ea613ed8e930cb275e019cc4e6fa287b6d5c2a5b9eb79cd7aa7d6e`.
- Suficiência: `b7cb54d3f32afa16f3f8e112f0c8a07df5d7defd2d140f45b6b72285bcc5173c`.

Payloads e schemas iniciais A/B são idênticos. O contrato e o gerador do schema de suficiência também são idênticos. A instanciação desse segundo schema depende dos candidatos/IDs da primeira etapa; não há hashes concretos A/B dessa etapa sem novas respostas. Nenhum julgamento histórico foi usado como resultado contemporâneo.

## Disponibilidade e incompatibilidade

Foram feitas somente duas consultas autenticadas de metadados, pelo endpoint oficial `GET /v1/models/{model}`, sem textos de estudantes:

| Modelo | HTTP | Identificador retornado | Latência da consulta |
|---|---:|---|---:|
| A | 200 | `gpt-4o-mini-2024-07-18` | 1,378 s |
| B | 200 | `gpt-6.1-sol` | 0,825 s |

A chave foi usada somente pelo cliente, sem impressão ou persistência de secrets. HTTP 200 confirma acesso ao registro do modelo; não demonstra que qualquer combinação de parâmetros será aceita por Responses.

O bloqueio é concreto na configuração: `hybrid_semantic.py:176` e `semantic_sufficiency.py:138` enviam `temperature=0` incondicionalmente. A documentação de GPT-6.1 Sol informa reasoning padrão `medium` e não oferece `none`. O guia de parâmetros exige omitir `temperature` quando reasoning não é `none`. [Modelo GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [compatibilidade de parâmetros](https://developers.openai.com/api/docs/guides/latest-model).

**Não foi observado nem alegado um HTTP 400 de inferência.** A incompatibilidade foi identificada pelo código congelado e pela documentação oficial antes de enviar os payloads. Não se gastaram chamadas para repetir uma configuração documentada como incompatível. Também não se omitiu silenciosamente o parâmetro, não se alterou reasoning e não se injetou outro transporte: isso mudaria a configuração/código preparado nesta execução congelada.

A autorização de chamadas foi recebida. O bloqueio não é falta de autorização nem indisponibilidade de modelo.

## Gate e comparação

O gate do smoke não foi avaliado: não existem respostas contemporâneas para revisar falsos créditos, vínculos, atribuições, cobertura ou controles semânticos. Consequentemente, a condição para executar as 25 DEV não foi satisfeita. Nenhum caso persistido foi alterado e ACTIVE DEV não foi executado.

| Métrica principal | A | B |
|---|---|---|
| Respostas válidas | Não medido | Não medido |
| Cobertura sobre 409 | Não medido | Não medido |
| Falsos créditos | Não medido | Não medido |
| Novos falsos créditos | Não medido | Não medido |
| Vínculos incorretos | Não medido | Não medido |
| Falsas atribuições | Não medido | Não medido |
| FORMAL_VERIFIED | Não medido | Não medido |
| DETERMINISTIC_VERIFIED | Não medido | Não medido |
| SEMANTIC_SUPPORTED | Não medido | Não medido |
| Indeterminate | Não medido | Não medido |
| Conflicts | Não medido | Não medido |
| Needs_review potencial | Não medido | Não medido |
| Exact / ±1 / ±2 | Não medido | Não medido |
| MAE / bias | Não medido | Não medido |

Os campos não medidos estão nulos nos artefatos, sem imputação como zero e sem comparação com números históricos. Não há afirmação de acurácia humana nem inferência sobre superioridade de A ou B.

## Custos e artefatos

| Medida | A | B |
|---|---:|---:|
| Consultas de metadados | 1 | 1 |
| Chamadas de inferência | 0 | 0 |
| Tokens de entrada | 0 | 0 |
| Tokens de saída | 0 | 0 |
| Latência de inferência | Não executada | Não executada |
| Custo estimado de inferência | US$ 0 | US$ 0 |

A latência das consultas de disponibilidade não é latência de geração dos modelos. O custo zero decorre da ausência de inferência.

Diretório: `artifacts/evaluations/tme_model_ablation_live_01/`.

Contém `preflight.json`, `model_availability.json`, `parameter_compatibility.json`, `smoke_cases.json`, política do gate registrada antes da inferência, `smoke_comparison.json`, `model_comparison.json`, `false_credit_comparison.json`, `disagreement_analysis.json`, `summary_by_problem.json`, `cost_summary.json`, `preservation.json` e `GO_NO_GO.json`. Os quatro JSONL smoke/DEV de A/B estão vazios; as comparações registram `NOT_RUN`. `preflight_dry_run/` preserva o plano e os cinco payloads/schemas locais.

## Condição para retomar

É necessário preparar e validar uma política de parâmetros compatível com os dois modelos, registrando qualquer diferença inevitável, e congelar novamente código/configuração em um SHA limpo antes de retomar o smoke. Isso não foi feito nesta execução. O bloqueio não justifica acrescentar gates matemáticos nem concluir que o modelo candidato ou a arquitetura de correção falharam.

Sem commit. **HOLDOUT processadas: 0/100.**
