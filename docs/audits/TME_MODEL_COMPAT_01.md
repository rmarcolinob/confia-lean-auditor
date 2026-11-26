# TME_MODEL_COMPAT_01

Compatibilidade de transporte implementada e validada localmente. **Zero inferências. HOLDOUT processadas: 0/100.** Não houve execução de modelos sobre DEV, alteração de notas persistidas, otimização do candidato ou commit.

## Motivo e diferença necessária

O preflight anterior confirmou disponibilidade dos dois modelos, mas encontrou `temperature=0` fixado nas duas chamadas. Esse parâmetro não é compatível com o contrato de reasoning ativo do Sol. A preparação anterior permaneceu preservada como histórico.

**Os parâmetros de geração não são literalmente idênticos porque os modelos possuem contratos de API diferentes. Cada braço utiliza a configuração válida previamente especificada, mantendo constantes todas as camadas semânticas e matemáticas do experimento.**

Essa declaração também é gravada pelo runner no preflight e no status de execução A/B, inclusive em dry-run.

| Parâmetro, nas duas etapas | A: gpt-4o-mini-2024-07-18 | B: gpt-6.1-sol |
|---|---|---|
| temperature | 0, histórico | Omitido |
| reasoning | Sem configuração específica | `{"effort":"medium"}` |
| top_p / top_logprobs | Não enviados pelo componente atual | Removidos, se presentes |
| store | false | false |
| max_output_tokens | 16000 | 16000 |
| timeout | 180 s | 180 s |
| retries | 0 | 0 |

Não existe opção de escolher outro effort nesta política. Não foram testados low, high, xhigh ou max. Não foi adicionado outro mecanismo de sampling.

## Implementação limitada ao transporte

Novo arquivo `app/confia_lean_auditor/student_claims/model_transport.py`:

- `build_request` copia os parâmetros e aplica somente a regra explícita do Sol. Remove `temperature`, `top_p`, `top_logprobs`, `logprobs` e a inclusão de `message.output_text.logprobs`, se presentes; fixa `reasoning.effort=medium`.
- Input, prompt, schema, limite de saída e armazenamento permanecem inalterados.
- `transport_configuration` registra separadamente os parâmetros de cliente/modelo, com política `tme-model-transport.v1`.
- Modelos não listados preservam o comportamento legado; o builder não afirma compatibilidade de modelos não verificados.

Os arquivos `hybrid_semantic.py` e `semantic_sufficiency.py` receberam somente um ponto opcional de construção de request nas funções de transporte. Não houve mudança em prompts, schemas, payloads, julgamentos, validações ou regras do evaluator/gate. O runner injeta o builder nos providers padrão das duas etapas; os pontos de injeção de providers de teste continuam funcionando.

**Fora do runner experimental, chamadas sem builder conservam exatamente o request anterior.** `configuration()` também continua idêntica, com mini e temperatura zero. Não houve reconfiguração global ou alteração temporária de módulos na execução real.

O runner `scripts/evaluation/evaluate_tme_model_ablation.py` agora registra configurações efetivas e hashes de transporte por braço. Nenhum segundo cliente OpenAI foi criado. `tests/test_tme_model_ablation.py` foi ajustado para os novos metadados, e `tests/test_tme_model_compat.py` foi adicionado.

## Preservação semântica e matemática

Comparação antes/depois confirmou:

- defaults legados idênticos;
- prompts byte a byte idênticos;
- cinco payloads e schemas iniciais do smoke idênticos aos anteriores;
- contrato Structured Output de suficiência idêntico;
- mesma árvore sintática dos componentes, excluindo apenas as funções de transporte alteradas;
- código matemático, regras, dados e demais arquivos preexistentes preservados, exceto os quatro arquivos de infraestrutura/teste declarados acima.

Hashes dos prompts, iguais em A e B:

- SemanticRubricEvaluator: `590349b9a1ea613ed8e930cb275e019cc4e6fa287b6d5c2a5b9eb79cd7aa7d6e`.
- SemanticSufficiencyGate: `b7cb54d3f32afa16f3f8e112f0c8a07df5d7defd2d140f45b6b72285bcc5173c`.

Cada braço registra `semantic_layer_hashes` para obligations, evidence units, regras de suficiência, política/reconciliação e pauta. Esses hashes são iguais entre A e B. `model_transport_configuration` e `model_transport_sha256` registram a diferença inevitável de transporte separadamente.

O schema de suficiência enumera candidatos e evidence IDs do primeiro avaliador. Seu contrato/gerador permanece igual; as instanciações poderão diferir quando os modelos produzirem seleções diferentes. A igualdade do request semântico e do schema concreto para a mesma entrada foi verificada nas duas etapas com cliente simulado. O dry-run não inventa respostas do primeiro avaliador.

PautaEngine, HybridEvidencePolicy, EvidenceReconciler, evidence units, grounding, context gates, obligations, regras de suficiência, pautas P1–P5, checkers, Lean, canonicalização, scoring e DEV/HOLDOUT não foram alterados.

## Dry-run e preflight local

Executado sem API key:

```bash
env -u OPENAI_API_KEY PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app \
  .venv/bin/python scripts/evaluation/evaluate_tme_model_ablation.py \
  --model-a gpt-4o-mini-2024-07-18 \
  --model-b gpt-6.1-sol \
  --split smoke --shadow --dry-run \
  --output artifacts/evaluations/tme_model_compat_01/dry_run
```

Resultado: os mesmos cinco casos P1_06, P2_01, P3_02, P4_13 e P5_09; dois braços; duas etapas por braço. Dez chamadas iniciais e até dez de suficiência seriam planejadas. **Nenhuma foi realizada.** O output mostra explicitamente temperatura zero no mini e somente reasoning medium no Sol, sem os parâmetros incompatíveis.

A guarda DEV não mudou: IDs desconhecidos ou fora da lista congelada são rejeitados antes do provider; os hashes da lista e das fontes são conferidos. Nenhum texto HOLDOUT foi lido ou usado em fixture.

Foi reutilizada a consulta segura de disponibilidade via `GET /v1/models/{model}`: HTTP 200 para ambos. Foram duas consultas de metadados, sem textos DEV e sem inferência; nenhum secret foi impresso ou persistido. Isso confirma acesso ao registro dos modelos, não equivale a uma validação de geração LIVE. Os requests de geração foram validados somente por construção local e captura no SDK simulado.

## Testes

Os 30 testes de ablação e compatibilidade passaram, incluindo:

- default legado e parâmetros históricos do mini;
- ausência de parâmetros incompatíveis e effort medium no Sol;
- model ID correto em ambas as etapas;
- igualdade de prompt, input e schema nos requests capturados;
- injeção do builder pelos providers padrão do runner;
- ausência de mutação da entrada pelo builder;
- hashes semânticos iguais e hashes de transporte distintos;
- bloqueio de HOLDOUT e dry-run sem chave/rede.

O detector de rede dos testes também verifica tentativas capturadas por exceções: um acesso inadvertido não fica escondido pelo tratamento de erro dos providers.

A regressão solicitada passou integralmente: **843 testes aprovados em 198,59 segundos, sem falhas, erros ou skips**, em 13 arquivos. Inclui model ablation, compatibilidade, hybrid semantic, sufficiency, evidence IDs, PautaEngine, bridges P1–P5, integração TME e obligation semantic. O manifesto e o JUnit estão nos artefatos desta tarefa. `git diff --check` também passou.

Não foram calculadas métricas de qualidade, cobertura ou ganho de nenhum modelo. Falhas semânticas históricas não foram reclassificadas por esta mudança de transporte.

## Artefatos e estado final

Diretório `artifacts/evaluations/tme_model_compat_01/`: snapshot anterior, `preservation.json`, `model_availability.json`, testes/JUnit, manifesto de regressão e `dry_run/` com requests iniciais, schemas, configurações efetivas e hashes separados.

SHA base: `6bb2bf3d7deb0cffe591a16db520a0e81db2d6c6`. As alterações permanecem sem commit. O próximo experimento LIVE deverá usar o código revisado em um novo estado limpo e congelado; nenhuma execução LIVE foi iniciada nesta tarefa.

**Zero inferências; HOLDOUT processadas: 0/100.**
