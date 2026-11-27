# TME_MODEL_ABLATION_01

**MODEL_ABLATION_NO_GO — BLOCKED_PREFLIGHT.** A comparação não foi executada. Esta decisão é operacional; não representa reprovação da qualidade de `gpt-6.1-sol`, falha do smoke ou evidência de superioridade de qualquer modelo.

## Baseline registrado antes de qualquer chamada

- Branch: `feat/tme-dual-input`.
- SHA completo: `827b1cedc050ffbdcb6686ee8cd144837e925fa7`.
- `git status --short`: vazio no preflight.
- Modelos solicitados: A `gpt-4o-mini-2024-07-18`; B `gpt-6.1-sol`.
- Hashes dos prompts, configurações, código protegido, fontes DEV e schemas do primeiro avaliador registrados em `preflight.json`.
- O schema de suficiência depende dos candidatos da primeira etapa. Seu gerador está congelado por hash, mas nenhum schema A/B efetivamente utilizado existe, pois não houve primeira etapa contemporânea.

## Motivo da parada

A instrução do usuário determina: “Se qualquer mudança de código/prompt/schema for necessária: PARAR.”

O modelo está fixado em `hybrid_semantic.configuration()` (linha 163) e `semantic_sufficiency.configuration()` (linha 66). As funções de chamada usam esse valor sem opção existente de modelo por argumento ou ambiente. O runner atual de suficiência declara `first_evaluator='reuse_frozen_Hybrid01'` e reutiliza julgamentos e auditorias anteriores no replay. Isso não realiza a comparação contemporânea exigida.

Existem pontos de injeção de `provider` nos componentes, mas não um runner A/B configurável já implementado. Usá-los para esta comparação exigiria escrever outro provider/orquestrador ou modificar funções em memória. Nenhuma dessas alterações foi feita sob a regra de congelamento. Os runners anteriores também escrevem em seus diretórios históricos; eles não foram executados ou sobrescritos.

A autorização externa foi recebida e não é o bloqueio. Nenhuma chamada de inferência, consulta autenticada de modelos ou leitura de segredo foi realizada. A documentação oficial identifica `gpt-6.1-sol`, Structured Outputs e reasoning padrão `medium`; acesso da conta e compatibilidade exata de todos os parâmetros não foram testados. Não se afirma que o modelo seja indisponível. [Documentação oficial consultada](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

## Smoke planejado, não executado

Lista fixa e ordenada registrada antes de qualquer chamada: P1_06, P2_01, P3_02, P4_13 e P5_09, todos das mesmas 25 DEV. A ordem prevista é pipeline A seguido de pipeline B para cada caso. As razões de seleção e hashes estão em `smoke_cases.json`. Não houve revisão manual comparativa A/B, pois não existem respostas contemporâneas.

## Resultados e custos

Smoke A/B: não executado. DEV completo A/B: não executado. Respostas válidas, cobertura, falsos créditos, vínculos, tiers, divergências e métricas sintéticas: **não medidos**. Não foram importados números históricos como se fossem resultados desta comparação.

Chamadas por modelo: 0. Tokens de entrada/saída: 0. Custo de inferência: US$ 0, por ausência de execução. Nenhuma nota real foi modificada; ACTIVE DEV não executado.

**HOLDOUT processadas: 0/100**. Nenhum texto HOLDOUT foi lido, enviado ou usado para criar fixtures.

## Artefatos

Os arquivos solicitados estão em `artifacts/evaluations/tme_model_ablation_01/`. Os quatro JSONL de execução estão vazios. Os JSON de comparação registram `NOT_RUN` e métricas nulas; `GO_NO_GO.json` distingue bloqueio de preflight de avaliação de qualidade. Foram criados somente os artefatos solicitados e este relatório; nenhum arquivo preexistente de código, prompt, schema, pauta, policy, checker ou Lean foi alterado. Nenhum commit foi feito.

## Condição para retomar

Preparar em uma tarefa separada a seleção explícita de modelo para as duas etapas e a execução contemporânea completa, preservando todos os componentes matemáticos. Depois validar e congelar um novo SHA limpo antes de começar a ablação. Essa preparação não foi realizada aqui. O bloqueio atual não justifica adicionar gates nem concluir que a arquitetura ou o modelo candidato precisam ser substituídos.
