# TME_MODEL_ABLATION_PREP_01

Preparação da infraestrutura A/B, somente offline. **Nenhuma chamada externa foi realizada. HOLDOUT processadas: 0/100.** Não há conclusão sobre a qualidade de qualquer modelo.

## Bloqueio anterior e escopo

O runner anterior fixava `gpt-4o-mini-2024-07-18` nas duas configurações e reutilizava julgamentos/auditorias históricos. Por isso, `TME_MODEL_ABLATION_01` foi interrompido antes da inferência. Seus artefatos e relatório foram preservados.

Base desta preparação: branch `feat/tme-dual-input`, SHA `827b1cedc050ffbdcb6686ee8cd144837e925fa7`. O relatório anterior já estava como arquivo não rastreado ao iniciar esta tarefa. Não foi feito commit. O próximo LIVE precisa de um novo estado limpo e congelado; o dry-run atual registra também os hashes dos arquivos de trabalho, pois o SHA base sozinho não identifica estas alterações.

Foram modificados apenas dois arquivos preexistentes:

- `app/confia_lean_auditor/student_claims/hybrid_semantic.py`: `configuration` e `request_judgments` aceitam `model` opcional, somente por palavra-chave.
- `app/confia_lean_auditor/student_claims/semantic_sufficiency.py`: `configuration` e `request_sufficiency` aceitam o mesmo argumento. A avaliação adiada das anotações mantém a assinatura compatível com o Python 3.9 do ambiente.

Foram adicionados o runner `scripts/evaluation/evaluate_tme_model_ablation.py`, os testes `tests/test_tme_model_ablation.py` e este relatório.

## Model override e compatibilidade

`configuration()` e `configuration(model=None)` retornam exatamente as configurações anteriores. `configuration(model="MODEL_X")` troca somente o identificador do modelo. O override não muda prompt, schema, temperatura, timeout, limite de tokens, retries ou armazenamento.

As funções de chamada encaminham esse valor ao cliente OpenAI já existente. O runner usa `functools.partial` nos pontos de injeção de provider para vincular o mesmo modelo às duas etapas de cada braço. Não há novo cliente, monkeypatch de módulo na execução real, troca de arquivo em disco ou ajuste específico para `gpt-6.1-sol`.

Permanecem temperatura 0, `store=false`, timeout de 180 segundos, limite de 16.000 tokens de saída e zero retries. Nenhum parâmetro de reasoning é enviado. A aceitação desses parâmetros por uma conta/modelo será verificada em um preflight LIVE posterior; não foi testada nesta tarefa.

Os dois prompts permanecem byte a byte iguais, com SHA-256:

- SemanticRubricEvaluator: `590349b9a1ea613ed8e930cb275e019cc4e6fa287b6d5c2a5b9eb79cd7aa7d6e`.
- SemanticSufficiencyGate: `b7cb54d3f32afa16f3f8e112f0c8a07df5d7defd2d140f45b6b72285bcc5173c`.

PautaEngine, EvidenceReconciler, HybridEvidencePolicy, pautas, pesos, evidências, grounding, contexto, requisitos, canonicalização, checkers, Lean, carry-forward e rótulos sintéticos não foram alterados.

## Runner contemporâneo

A ordem é determinística: para cada caso selecionado, braço A completo e depois braço B completo. Cada braço obtém novos julgamentos do primeiro avaliador e constrói a entrada de suficiência a partir desses julgamentos. O segundo braço não recebe os resultados do primeiro.

Após as duas etapas semânticas, o runner invoca as funções atuais de auditoria primária e seletiva sobre as fontes/extrações do próprio braço, com Lean habilitado na CLI LIVE. Injeta somente a resposta de suficiência recém-obtida em `run_sufficiency_shadow`, reutilizando sua reconciliação e avaliação sem nova chamada ao gate. Essa injeção local não reutiliza resultados históricos.

Se o primeiro avaliador falha ou todos os candidatos são barrados pelas regras existentes, o gate pode dispensar chamada. Resultados inválidos continuam sujeitos aos validadores existentes. O runner produz somente assessments shadow e não publica resultados em casos persistidos.

A CLI exige `--model-a`, `--model-b`, `--split smoke|dev`, `--shadow`, `--output` e uma escolha explícita entre `--dry-run` e `--live`. O diretório de saída deve ser novo; resultados anteriores não são sobrescritos. LIVE recusa checkout sujo. Essas guardas são operacionais e não acrescentam critérios matemáticos de crédito.

## Proteção das DEV e HOLDOUT

O único conjunto aceito é a lista congelada de 25 DEV em `tme_semantic_understanding_01/dev_ids.json`. Seu hash e o hash do arquivo DEV de fontes são fixados no runner. Não há opção de carregar outro dataset nem textos fornecidos pelo chamador na CLI.

A seleção inteira é validada antes de carregar os textos e antes de chamar providers: IDs ausentes da lista, duplicados, smoke sem cinco problemas distintos ou DEV incompleto são rejeitados. Alterar a própria lista também é rejeitado pelo hash. O plano completo é revalidado antes da execução.

O loader existente lê somente `dev_ids.json` e o arquivo DEV `tme_semantic_diag_01/cases_analysis.json`; não acessa datasets HOLDOUT. Rótulos presentes no diagnóstico local não entram no payload do modelo. Os testes usam um ID com formato válido fora da lista e um identificador fictício de HOLDOUT, sem ler qualquer texto HOLDOUT.

## Hashes e schemas

O preflight registra por braço: SHA Git, modelo, configurações e seus hashes, hashes dos dois prompts, payloads e schemas do primeiro avaliador por caso, contrato/gerador do schema de suficiência, implementação de evidence units e código protegido. As configurações diferem somente no campo `model`; os hashes das configurações completas, portanto, diferem intencionalmente.

Há uma distinção necessária: o schema concreto de suficiência enumera as obrigações e evidence IDs escolhidos pelo primeiro avaliador. Em um experimento contemporâneo, A e B podem escolher candidatos diferentes. O contrato e o gerador do schema são idênticos; suas instanciações poderão diferir em consequência dessas respostas. O dry-run não inventa candidatos para declarar igualdade de schemas ainda inexistentes. Os hashes concretos são registrados por braço/caso após a primeira etapa em uma futura execução LIVE.

## Dry-run final

Executado sem `OPENAI_API_KEY`:

```bash
env -u OPENAI_API_KEY PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app \
  .venv/bin/python scripts/evaluation/evaluate_tme_model_ablation.py \
  --model-a gpt-4o-mini-2024-07-18 \
  --model-b gpt-6.1-sol \
  --split smoke --shadow --dry-run \
  --output artifacts/evaluations/tme_model_ablation_prep_01/dry_run
```

Resultado:

- 5 casos: P1_06, P2_01, P3_02, P4_13 e P5_09, a mesma seleção registrada no preflight anterior.
- 2 braços; duas etapas semânticas por braço.
- 10 chamadas planejadas ao primeiro avaliador e de 0 a 10 ao gate: **até 20 chamadas**, sem contar retries, que permanecem desabilitados.
- **0 chamadas realizadas**, nenhum cliente/API key necessário e **HOLDOUT 0/100**.
- Payloads iniciais, prompts, schemas iniciais e contrato/gerador de suficiência iguais entre braços.
- Payload de suficiência marcado como dependente do primeiro julgamento novo; não foi substituído pelo resultado histórico.

Também foi testado, offline, o plano de 25 DEV: 50 chamadas iniciais e até 50 de suficiência. Esse teste não executa modelos.

## Validação

Os 22 testes novos passaram. Cobrem defaults exatos, override somente de modelo, igualdade dos argumentos efetivamente entregues ao SDK simulado, passagem do modelo às duas etapas, independência A/B, estados sem candidatos/falha do primeiro provider, seleção DEV, rejeição de lista adulterada, plano modificado, dry-run sem chave/rede e bloqueio LIVE com checkout sujo. Os providers e clientes usados nesses testes são locais; não são avaliações dos modelos.

Uma comparação adicional com o snapshot anterior confirmou as configurações e prompts idênticos, os 25 schemas do primeiro avaliador idênticos e o contrato de suficiência idêntico. O replay offline das respostas já gravadas nas 25 DEV produziu exatamente as mesmas evidências, reconciliações, assessments e schemas concretos de suficiência. Esse replay foi somente uma verificação de compatibilidade: o novo runner A/B não lê esses julgamentos históricos.

A bateria ampla passou integralmente: **1.573 testes aprovados em 626,87 segundos, sem falhas ou skips**, em 27 arquivos. Inclui hybrid semantic, semantic sufficiency, evidence IDs, PautaEngine, bridges P1–P5, integração experimental, canonicalização, fidelidade/atribuição, semântica formal e a regressão anterior. O manifesto está em `regression_manifest.json` e os resultados em `regression.xml`/`regression.log`. Os 22 testes novos também foram executados separadamente na versão final, todos aprovados.

A verificação de preservação confirmou 393 arquivos preexistentes idênticos, além dos dois arquivos de transporte/configuração com as alterações descritas acima. A comparação da árvore sintática fora dessas funções também permaneceu idêntica. `git diff --check` passou.

As falhas de qualidade conhecidas do experimento anterior não foram “corrigidas” por esta tarefa. O replay idêntico confirma também sua preservação; não se afirma que os 21 controles de falsos créditos/vínculos tenham passado.

## Artefatos

Em `artifacts/evaluations/tme_model_ablation_prep_01/`: snapshot anterior, testes/JUnit, manifesto da regressão, replay de compatibilidade, hashes de preservação, e `dry_run/` com preflight, cinco payloads/schemas e status de execução.

A preparação permite uma futura execução contemporânea com modelo explícito nas duas etapas. Compatibilidade real do provider, qualidade, custos e decisão de promoção A/B permanecem não avaliados. **Sem LIVE, sem HOLDOUT e sem commit automático nesta tarefa.**
