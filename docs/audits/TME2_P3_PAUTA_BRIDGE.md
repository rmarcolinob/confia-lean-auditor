# TME² P3 — ponte de evidências e pauta opt-in

## Estado inicial e fonte do problema

Baseline: `092b8e5` (`feat/tme-dual-input`). O commit já continha a pauta e a
ponte P1. Cinco arquivos de suporte P1 ainda estavam não versionados:
`core/math_canonical/syntax.py`, `lean/student_claim_checkers/tme2_p1.py`,
`student_claims/digital_literals.py`, `student_claims/tme2_p1_digital.py`, sob
`app/confia_lean_auditor/`, e `scripts/evaluation/run_tme2_p1_pauta_pilot.py`.
Eles foram preservados; não houve reset, limpeza, staging ou commit.

O TME operacional existente usava `core.problem_catalog.CATALOG` (ITA). Não
existia registry próprio para auditoria matemática dos pilotos de pauta.

A pauta P3 foi transcrita da especificação fornecida nesta tarefa. A figura
não estava no anexo nem no repositório. O [portal oficial da SEDUC](https://seduc.pi.gov.br/projetos/seducolimpica/tme)
publica links da segunda fase, mas o download do PDF retornou HTTP 403.
**Não se afirma que a figura desse PDF foi inspecionada.** O estado abaixo foi
confirmado explicitamente pelo usuário nesta tarefa, de baixo para cima:

| Compartimento | Pilha, da bola inferior para a superior |
|---|---|
| 1 | branca, preta, branca, cinza, preta |
| 2 | branca, cinza, preta |
| 3 | cinza, preta |
| 4 | preta, preta |
| 5 | cinza, preta |
| 6 | preta, branca, cinza, preta |

Asset versionável: `examples/pautas/tme2_problem3.machine.v1.json`, com fonte
registrada. Nenhuma cor foi escolhida para ajustar uma resposta esperada.

## Arquitetura reutilizada

Fluxo preservado:

`texto digital por item → StudentClaim/MathClaimRecord + grounding/canonicalização
→ verificação → FactResult → PautaEvidence → PautaEngine → pontos sugeridos`.

- `PautaEngine`, seus modelos, estratégias e pesos P1 não foram alterados.
- A coleta genérica já presente no P1 foi extraída para
  `student_claims/digital_items.py`. A entrada P1 permanece um wrapper com o
  mesmo contrato; seus extratores e suas regras matemáticas continuam iguais.
- A montagem de resultados/links/fingerprints foi extraída de `_Checks` para
  `claims/common/fact_results.py::FactResultsBuilder`. O checker P1 herda essa
  implementação, mantendo sua lógica matemática e seu caminho Lean original.
- `rubric/pauta/bridge.py::bridge_facts` reutiliza os mesmos gates P1 de origem,
  atribuição, hash, source binding, conflito, erro técnico e identidade formal.
  O wrapper P1 conserva seu mapa; o P3 fornece outro mapa explícito.
- Não foi criada outra representação de claim. Os produtores de notação usam
  o canal `native` já previsto por `MathClaimRecord`, com `CanonicalForm`,
  `SourceBinding`, `Provenance` e `VerificationLink` existentes.
- A bridge continua sem parsing matemático, pontos, chamadas Lean ou LLM.
  O PautaEngine continua recebendo somente evidências já avaliadas.

Essa extração de infraestrutura alterou três arquivos existentes: a bridge
compartilhada, o wrapper de coleta P1 e a montagem de fatos dentro do checker
P1. Portanto, não se alega identidade byte a byte desses três arquivos.
As **20 saídas P1 completas**, incluindo records, fingerprints, evidências,
traces e pontuação, foram comparadas antes/depois e são idênticas.

## Registro e uso

`tme/registry.py` registra somente `TME2_P1_PILOT` e `TME2026P3` no novo registry
matemático opt-in. Não modifica o catálogo ITA, `/audit`, as rotas operacionais
TME, HMER ou frontend. Nenhum P2/P4/P5 foi registrado.

```python
from confia_lean_auditor.tme.registry import audit_tme

bridge, assessment = audit_tme(
    problem_id="TME2026P3",
    solution={"a": "inferiores_brancas: 2\nprimeira_branca: 2/6=1/3"},
    solution_id="exemplo-digital",
    use_lean=False,  # True por padrão; executa somente Lean local quando aplicável.
)
assert assessment.items[0].points_awarded == 4
```

Como no piloto P1, os itens são fornecidos explicitamente em um mapping de
texto. Não há interpretação automática de um caderno inteiro ou de cabeçalhos
livres. Os spans usam o documento composto com os marcadores `[a]`, `[b]`, `[c]`.

## Produtores e notação digital suportada

`student_claims/named_math.py` implementa uma gramática opt-in reutilizável:
`quantidade declarada: valor`. O contrato P3 declara os nomes e tipos em
`student_claims/tme2_p3_digital.py`. Isso não é classificação de prosa por frases
dos testes. A matemática é analisada pela canonicalização existente; as cores
e conjuntos têm tipos explícitos. Labels desconhecidos não ganham significado
por coincidência numérica. A extração existente de `Resposta:` também conserva
seu conceito semântico: `resto: 11/36` não é resposta probabilística.

| Item | Quantidades declaradas |
|---|---|
| a | `inferiores_brancas`, `primeira_branca` |
| b | `pares_ordenados`, `favoraveis_distintos`, `repeticao_branca`, `segunda_branca` |
| b, alternativa | `ramo_1` a `ramo_6`, `arvore_total` |
| c | `continuar`, `estrategia_1`, `contagem_1`, `estrategia_2`, `contagem_2`, `condicional_1`, `condicional_2`, `total` |

São aceitos espaços no lugar de underscores, normalização de acentos e caixa;
por exemplo, `favoráveis distintos: 2*5=10`. Cores podem ser `preta`, `cinza`,
`branca` e seus aliases explicitamente declarados. Conjuntos usam sintaxe
completa, como `{1,2}` e `{6}`. Não há expansão de reticências.

Respostas matemáticas isoladas são tratadas conforme o item. Uma expressão
sob um label desconhecido não é promovida automaticamente a resposta final.
Hipóteses, negações, citações e tentativas rejeitadas conservam os gates de
atribuição/contexto existentes. Anotações, canonical forms e roteamento são
reconstruídos da fonte antes da verificação, impedindo sobrescrita posterior.

## Estado e verificação matemática

`tme/p3_machine.py` é uma estrutura imutável de seis pilhas, com operações
restritas às duas retiradas do problema. Enumera 36 pares ordenados, sem Monte
Carlo e sem probabilidades aproximadas. A lei uniforme dos acionamentos é uma
premissa explícita do problema, não uma conclusão perceptual do Lean.

O estado confirmado produz:

- inferiores iniciais: branca, branca, cinza, preta, cinza, preta;
- dez pares favoráveis com compartimentos diferentes e somente `(6,6)` na diagonal;
- probabilidades condicionais da segunda branca, por primeiro compartimento:
  `1/6, 1/6, 1/3, 1/3, 1/3, 1/2`;
- após retirar do 1: três pretas, duas cinzas e uma branca;
- após retirar do 2: três cinzas, duas pretas e uma branca.

`lean/student_claim_checkers/tme2_p3.py` compara afirmações atribuídas com esse
estado e produz fatos sem pontos. Campos `student_asserted` referenciam os
claims escritos; `engine_derived` identifica enumerações, contagens, pesos e
normalizações feitas pelo verificador. Fonte e hash da máquina acompanham os
resultados. Nenhum claim intermediário do aluno é criado a partir desses
resultados derivados: a ausência de B1/B2/B3, por exemplo, continua indeterminada
quando só existe `11/36`.

`core/math_canonical/rational.py` reutiliza o parser e o lexer existentes para
racionais fechados e sua estrutura escrita. `2/6` e `1/3`, `(10+1)/36` e
`11/36`, `3/6` e `1/2` são comparados exatamente. `0.333` vale exatamente
`333/1000`; não é arredondado para `1/3`. `0.333...` não é interpretado nesta
versão. Todas as igualdades escritas precisam ser válidas; um último número
correto não salva uma igualdade anterior falsa.

## Pauta declarativa e decisões editoriais explícitas

Asset: `examples/pautas/tme2_problem3.v1.json`, total 20, política `withhold`
como no piloto P1. Erro técnico relevante continua pendente, sem virar refutação.

| Item | Estrutura | Pontos |
|---|---|---:|
| a | adição: contagem de brancas + probabilidade | 2 + 2 |
| b, oficial | adição: espaço amostral + diferentes + repetição + conclusão | 2 + 2 + 2 + 2 |
| b, alternativo | obrigação de método alternativo completo | 8 |
| b, seleção | `max_of` entre os dois caminhos; nunca soma os caminhos | máximo 8 |
| c | continuação + estratégia caso 1 + estratégia caso 2 + condicionais + probabilidade global | 1 + 2 + 2 + 1 + 2 |

- **a:** somente `1/3` concede os dois pontos de probabilidade, sem inventar
  identificação de duas bolas brancas. A exceção consta da decomposição da pauta.
- **b:** `11/36` isolado concede somente os dois pontos de B4 (conclusão), sem
  espaço amostral, contagens ou método alternativo inventados.
- **c:** a estratégia de cada caso exige a cor escolhida e a contagem afirmada.
  As condicionais precisam do contexto das estratégias verificadas. C5 exige
  desenvolvimento global escrito e seus contextos de continuação, estratégia e
  condicionais; `1/6` isolado concede zero. Uma identidade aritmética verdadeira
  sob estratégia ausente/incorreta não é certificação da probabilidade de ganhar.

Essas dependências de contexto constam de `obligation_ids` na própria pauta e
também são verificadas pelo producer antes de atribuir um certificado numérico
a uma afirmação probabilística contextual. Não se implementou carry-forward
de uma estratégia errada, pois a especificação não o autoriza.

## Método alternativo de b

O caso alternativo declara seis probabilidades condicionais, uma para cada
primeiro compartimento, e a soma ponderada pelos seis pesos `1/6`. Cada ramo é
comparado com a transição da máquina; a decomposição escrita deve cobrir os seis
ramos. É aceita soma de produtos ou fator comum multiplicando a soma.

Isso satisfaz `b.alternative_complete` e seleciona `b.alternative` com 8/8,
mesmo sem B1/B2/B3. A palavra “árvore”, o resultado isolado, uma árvore
incompleta ou um ramo errado não satisfazem a obrigação integral.

No item c, também se aceita a decomposição condicional equivalente
`(2/6)*(3/6)=1/6`, quando os dois contextos estratégicos estão comprovados.
Isso não confunde os pesos condicionados à primeira branca com os pesos
incondicionais do primeiro acionamento.

## Lean e fidelidade da proposição

O novo checker opt-in `rational_equality.py` usa o ciclo existente
`evaluate_student_proof`: prova direta, prova separada da negação, classificação
de erro técnico e source binding. Somente a renderização de aritmética fechada
em **ℚ** foi acrescentada. Cada literal é tipado; fonte bruta, variáveis,
funções arbitrárias e táticas do usuário não são injetadas em Lean.

A projeção formal também é um `MathClaimRecord` nativo, com o payload exato
`StudentClaim`/`StudentClaimCheck` e `number_domain="Q"`. O mecanismo legado de
projeção rejeita esse registro nativo, impedindo seu encaminhamento acidental
ao checker de divisão inteira. O checker inteiro ITA/P1 não foi modificado.

Replay seletivo real: seis verificações, cinco provas e uma refutação:

- `2/6=1/3`;
- negação de `2/6=1/2`;
- `(10+1)/36=11/36`;
- `3/6=1/2`, uma para cada contexto do item c;
- `(1/6)(1/2)+(1/6)(1/2)=1/6`.

Os certificados estão referenciados nos artifacts. Lean comprova a igualdade
racional escrita; cores, transições, equiprobabilidade e escolhas ótimas são
verificações distintas. Não foram criados teoremas perceptuais ou formalização
genérica de árvores para aumentar artificialmente a cobertura.

## Casos controlados e coverage

Fixture versionável: `tests/fixtures/tme2_p3_digital/cases.json`.

| Caso | Pontos | Caminho, quando aplicável |
|---|---:|---|
| a completo | 4/4 | — |
| a só resposta 1/3 | 2/4 | — |
| a só contagem | 2/4 | — |
| a probabilidade errada, contagem correta | 2/4 | — |
| a irrelevante | 0/4 | — |
| a resposta equivalente 2/6 | 2/4 | — |
| a decimal finito 0.333 | 0/4 | — |
| a dízima não suportada | 0/4 | — |
| b oficial completo | 8/8 | counting |
| b faltando B3 | 6/8 | counting |
| b só resposta 11/36 | 2/8 | counting |
| b árvore completa | 8/8 | alternative |
| b 36 correto, favoráveis errados | 2/8 | counting |
| b palavra árvore sem demonstração | 0/8 | nenhum |
| b árvore incompleta | 2/8 | counting, somente conclusão |
| b ramo errado | 2/8 | counting, somente conclusão |
| b ambos os métodos completos | 8/8 | counting no empate; sem soma |
| c completo | 8/8 | — |
| c sem probabilidade total | 6/8 | — |
| c só resposta 1/6 | 0/8 | — |
| c segundo caso errado | 3/8 | — |
| c probabilidade total errada | 6/8 | — |
| c condicional equivalente | 8/8 | — |
| c aritmética sem estratégia | 0/8 | — |
| c sem continuação afirmada | 5/8 | — |

Resultado: **25/25**, com **13/13 obrigações** supported em pelo menos um caso.
O teste composto dos três itens completos, usando o caminho alternativo de b,
atinge 20/20 sem revisão pendente.

Observações de obrigações apenas dos itens exercitados: **53 supported,
6 refuted, 50 indeterminate, 0 technical_error** (109 observações).
Incluindo os itens não submetidos em cada caso: 325 observações, com as mesmas
53 supported e 6 refuted, mais 266 indeterminate. Ausência não é erro matemático.

Foram produzidos 66 resultados de verificação: **39 deterministic,
21 canonical_equivalence, 6 student_lean, 0 outras**. Seus estados são 54
verified, 6 refuted e 6 unverified. Esses números não são contagens de pontos:
dois métodos podem confirmar a mesma conclusão sem duplicar uma obrigação.
Nenhuma chamada OpenAI, Mathpix ou secondary foi feita pelo replay.

## Validação e preservação

- **244 passed**: 70 testes novos P3, 100 do PautaEngine e 74 da bridge P1.
- **702 passed**: grounding/fidelity, canonicalização, MathClaimRecord, rubric
  bridge, scoring e contratos dos verificadores existentes. Seleções sem
  sobreposição: **946 testes distintos**, sem falhas nas seleções executadas.
- As 20 saídas completas P1 antes/depois são idênticas; os snapshots estão nos
  artifacts. Pauta, pesos, verificação matemática e comportamento P1 preservados.
- PautaEngine e seus modelos, fluxo/catálogo ITA, HMER, UI, secondary e política
  de pontuação ITA permanecem byte a byte iguais ao início desta tarefa.
- Não se executou benchmark grande nem a suíte inteira de frontend/HMER.

Comandos dos testes:

```sh
.venv/bin/python -m pytest -q tests/test_tme2_p3_pauta_bridge.py \
  tests/test_pauta_engine.py tests/test_tme2_p1_pauta_bridge.py

.venv/bin/python -m pytest -q tests/test_claim_fidelity.py tests/test_math_canonical.py \
  tests/test_common_math_claims.py tests/test_audit_math_canonicalization.py \
  tests/test_rubric_bridge.py tests/test_positive_credit_evidence.py \
  tests/test_student_proof_semantics.py tests/test_score_policy.py tests/test_score_policy_api.py \
  tests/test_generic_student_math.py tests/test_claim_alignment_obligations.py
```

Replay pequeno reproduzível (usar um novo diretório de saída):

```sh
.venv/bin/python -m scripts.evaluation.run_tme_pauta_cases --problem TME2026P3 \
  --output artifacts/evaluations/tme2_p3_novo_replay \
  --lean-cases a_complete,a_wrong_probability,b_official,c_complete
```

Artifacts desta tarefa: `artifacts/evaluations/tme2_p3_pauta_bridge/`:
`baseline.json`, `p1_before.json`, `p1_after.json`, `validation_summary.json`,
logs de testes e `replay_final/` com `replay_summary.json` e os 25 traces completos.
Um recheck determinístico após o último ajuste compara novamente pontos, estados
e caminhos dos 25 casos com esse replay seletivo, sem reexecutar provas inalteradas.

## Novos arquivos e limites

Novos módulos, sob `app/confia_lean_auditor/`:

- `claims/common/fact_results.py`;
- `core/math_canonical/rational.py`;
- `student_claims/digital_items.py`, `named_math.py`, `tme2_p3_digital.py`;
- `lean/student_claim_checkers/rational_equality.py`, `tme2_p3.py`;
- `rubric/pauta/tme2_p3.py`;
- `tme/p3_machine.py`, `tme/registry.py`.

Novos assets/testes: as duas configurações `examples/pautas/tme2_problem3*.json`,
`tests/fixtures/tme2_p3_digital/cases.json`, `tests/test_tme2_p3_pauta_bridge.py`,
`scripts/evaluation/run_tme_pauta_cases.py` e este relatório.

Limitações: a coverage é deste contrato digital explícito, não acurácia geral
em prosa, fotografias ou desenhos. Uma árvore visual precisa ser transcrita em
ramos matemáticos; não há reconhecimento de diagramas. Métodos alternativos
fora das formas verificáveis implementadas permanecem indeterminados, mesmo
que sejam matematicamente corretos. Não existe aproximação frouxa, preenchimento
semântico, inferência de estratégias ausentes ou fallback secondary.

O bundle é uma interface interna de resultados confiáveis, não um endpoint
para aceitar flags de prova fornecidas por alunos. Hashes detectam alterações
de conteúdo; não são assinaturas criptográficas. A nota continua sendo sugestão
ConfIA, sem escrever decisão final do avaliador.

`git diff --check`: **OK**, com whitespace dos arquivos novos verificado
separadamente. Estado completo do Git registrado em `validation_summary.json`.
Sem staging, commit ou push.
