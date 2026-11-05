# TME P2 — crédito parcial — diagnóstico forense 01

Data: 2026-11-05. Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2`. SHA inspecionado: **`05c75f4c64ddfec288c96e3519dca01a94e6464f`**. Estado inicial do Git: limpo.

**Veredito: `PAUTA_AMBIGUOUS` — inconsistência entre o contrato operacional de crédito e a política separada de suficiência.** O cálculo de TME_CURRENT não é ambíguo: os cinco pontos vêm exatamente de **2 + 2 + 1**, conforme a pauta JSON e os checkers originais. Entretanto, a política interna de sufficiency exige justificativa nas duas primeiras obrigações, o que não é exigido pelo produtor de fatos usado pelo baseline. Não é correto decidir que os quatro pontos são sobrecrédito apenas observando `COMPOSITE_INCOMPLETE`, nem ocultar essa política ao dizer que todo o contrato é exclusivamente de valores.

Há uma conclusão independente dessa inconsistência: **`total: 384` tem crédito explícito de 1 ponto, sem exigir igualdade escrita ou Lean**. O Semantic Formal é excessivamente restritivo nesse ponto. Corrigir somente essa exigência levaria o caso de 0 a 1 no modo fortalecido, sem justificar automaticamente os outros quatro pontos.

Não houve alteração de código, pauta, checkers, testes ou documentos anteriores, nem acesso a gold/holdout. Foi executado somente o replay local da fonte fornecida e controles locais de isolamento, sem API LLM e sem executar um piloto/dataset. Nenhum processo Lean foi necessário para os três literais, mesmo com `use_lean=True` no replay principal. Somente este relatório foi criado no repositório.

## 1. Reconstrução dos cinco pontos

Fonte fornecida pelo usuário:

```text
c) pair_permutations: 24
pair_orientations: 16
total: 384
```

Execução: `experimental.tme_semantic_formal_p2.engine.evaluate`, com `case_id='p2_dev_partial'`, `mode='tme_current'`, `use_lean=True`. A entrada chamou `primary_audit`, não o extractor nem os checkers compostos fortalecidos. Resultado observado:

```text
requested_mode = TME_CURRENT
effective_mode = TME_CURRENT
fallback_used = false
extractor.status = not_requested
extractor.api_calls = 0
score = 5.0
```

A reconstrução abaixo usa `current_bridge.auditor.facts`, registros de origem, decisões de `current_assessment` e `credits`. Não foi deduzida somente do score.

| item → caminho → regra | obrigação/fato | evidência literal | checker e decisão observada | pontos |
|---|---|---|---|---:|
| c → c.counting → c.factorized_count_path → **c.distributions** | `c.pair_permutations` | `pair_permutations: 24` | `P2Checks.counting('pair_permutations',24)`; `rational_value('24') == 24`; fato `verified`; bridge `supported`; folha `SUPPORTED` | **2** |
| c → c.counting → c.factorized_count_path → **c.orientations** | `c.pair_orientations` | `pair_orientations: 16` | `P2Checks.counting('pair_orientations',16)`; `rational_value('16') == 16`; fato `verified`; bridge `supported`; folha `SUPPORTED` | **2** |
| c → c.counting → c.factorized_count_path → **c.conclusion** | `c.total` | `total: 384` | `P2Checks.counting('total',384)`; `rational_value('384') == 384`; fato `verified`; bridge `supported`; folha `SUPPORTED` | **1** |

Em todos os três fatos: `verification_source=canonical_equivalence`, `student_check=null`, atribuição ao estudante verdadeira, grounding `grounded` e ausência de contexto condicional. Não houve prova Lean executada. A verificação efetiva aqui é a avaliação racional exata da expressão fechada e a comparação com o valor da quantidade tipada; não uma prova da justificativa combinatória.

### Vínculos concretos do replay

| obrigação | source_claim_id | referência de verificação |
|---|---|---|
| c.pair_permutations | `native:digital-quantity.v1:4:25` | `check:f4be4f584dd68d032e9e` |
| c.pair_orientations | `native:digital-quantity.v1:26:47` | `check:2205c9863156b8d5f209` |
| c.total | `native:digital-quantity.v1:48:58` | `check:d1eb5256549fb41a8304` |

Os offsets são intervalos do framing digital existente (`[c]\n...`), não da string original iniciada por `c) `. O hash desse contêiner registrado nos fatos é `5fc4e2f357283785ccb8920281c92eaad4f3f0706956147e8fa9bf26a2d12d3d`. Cada registro mantém o trecho literal, subject e vínculo ao item c. Os IDs/referências acima correspondem ao replay desta tarefa, não a um artefato de API/piloto anterior.

### Árvore de decisão efetivamente observada

```text
c                                      additive, máximo 8 → 5
├── c.maximum                          all_of → 0
├── c.max_pairs                        all_of → 0
└── c.counting                         max_of, máximo 5 → 5
    ├── c.factorized_count_path         additive → 5  [selecionado]
    │   ├── c.distributions             all_of(c.pair_permutations) → 2
    │   ├── c.orientations              all_of(c.pair_orientations) → 2
    │   └── c.conclusion                all_of(c.total) → 1
    └── c.direct_product_path           all_of(c.counting_product) → 0
```

`selected_method_path='c.factorized_count_path'`; motivo `BEST_EVIDENCED_PATH`. As três folhas creditadas têm motivo `SUPPORTED`; o caminho fatorado tem `CAPPED_SUM`. `c.counting_product` está `indeterminate`, com motivo `NO_EXISTING_FACT`: **o baseline não inferiu nem creditou um produto 24×16 ausente**. O nome `factorized_count_path` é um agrupador aditivo; não contém um predicado adicional exigindo fatoração escrita.

`c.max_center`, `c.max_sum` e `c.pairs` também estão sem fatos. Logo, máximo e enumeração de pares não contribuíram. O item c ficou com 5 pontos conhecidos de um máximo de 8; suas outras regras continuam indeterminadas. A política `withhold` explica o zero nos créditos ausentes, não os três créditos positivos.

Fontes: [orquestração current](../../app/confia_lean_auditor/experimental/tme_semantic_formal_p2/engine.py), linhas 95–118; [primary_audit](../../app/confia_lean_auditor/tme/obligation_experiment.py), linha 21; [checker P2](../../app/confia_lean_auditor/lean/student_claim_checkers/tme2_p2.py), linhas 199–223; [bridge](../../app/confia_lean_auditor/rubric/pauta/bridge.py), linhas 181–216; [PautaEngine](../../app/confia_lean_auditor/rubric/pauta/engine.py), linhas 66–87, 119–131 e 154–182.

## 2. Pauta exata do item c

Autoridade de pontuação executada: [tme2_problem2.v1.json](../../examples/pautas/tme2_problem2.v1.json). As quatro declarações aceitam origens **`deterministic` e `student_lean`**. Não exigem exclusivamente Lean.

| obrigação | descrição literal na pauta | regra e pontos |
|---|---|---|
| c.pair_permutations | “24 distribuições dos quatro pares nas quatro linhas distintas.” | `c.distributions`: máximo 2, `all_of` contendo somente esse ID |
| c.pair_orientations | “16 orientações independentes dos quatro pares.” | `c.orientations`: máximo 2, `all_of` contendo somente esse ID |
| c.total | “Total de 384 preenchimentos.” | `c.conclusion`: máximo 1, `all_of` contendo somente esse ID |
| c.counting_product | “Contagem equivalente explícita como produto 24×16.” | `c.direct_product_path`: máximo 5, `all_of` contendo somente esse ID |

As declarações estão nas linhas 161–190; as regras de contagem nas linhas 313–356. As três primeiras folhas são somadas em `c.factorized_count_path`, limitado a 5. `c.counting` escolhe, por `max_of`, esse caminho ou o produto direto, também limitado a 5. Não se somam os dois métodos.

### Resultado, conta e justificativa: requisitos por camada

| obrigação | contrato executável atual: valor isolado tipado basta? | conta/igualdade escrita obrigatória? | justificativa combinatória no checker original? | política separada de sufficiency |
|---|---|---|---|---|
| c.pair_permutations | **sim, 24 recebe 2** | não; se houver igualdade, seus membros são verificados | não; identifica o subject e valida o valor, sem provar que o aluno justificou a cardinalidade | JUSTIFICATION: conclusão isolada não basta |
| c.pair_orientations | **sim, 16 recebe 2** | não | não; o literal não passa por um teste da independência argumentada | JUSTIFICATION: conclusão isolada não basta |
| c.total | **sim, 384 recebe 1** | **não** | não é exigida para esta conclusão | FINAL_ANSWER: conclusão explícita correta e com objeto correto |
| c.counting_product | não basta apenas 384 | exige produto explícito pertinente; **não exige sinal de igualdade** | original exige estrutura multiplicativa com fatores de valores 24 e 16; não verifica bijeção completa | JUSTIFICATION; checker fortalecido verifica também certificado e relação |

**Crédito parcial:** não há subdivisão interna dos 2 pontos de distribuições ou dos 2 de orientações entre “valor” e “justificativa”. Cada folha atômica concede seu máximo se a obrigação chega como `supported`. No caminho original, o número correto tipado basta para os 2 pontos integrais daquela folha. Isso é crédito parcial em relação aos 8 pontos do item c/20 da prova, mas não uma faixa especial de “metade por número”. O total tem sua parcela independente de 1. Não há bônus adicional separado de justificativa no JSON atual.

### Dependências reais

- Os três `all_of` do caminho fatorado são unitários: cada um exige apenas sua própria obrigação apoiada por fonte válida.
- Distribuições não depende de orientações; orientações não depende de distribuições; total não depende de nenhuma delas para seu ponto.
- Não há pré-requisito de `c.maximum`, `c.pairs` ou de crédito nos itens a/b para essas quatro regras.
- O produto direto não exige as três obrigações do caminho fatorado: tem seu próprio checker/fato e compete com esse caminho via `max_of`.
- A atribuição ao estudante, a origem aceita e a validação do bridge permanecem obrigatórias. Um número incidental ou sem subject não é equivalente a esses claims tipados.

## 3. Respostas diretas e controles de isolamento

Foram executados controles locais com `primary_audit(..., use_lean=False)`, usando somente os textos abaixo, sem chamar modelo:

| fonte exclusiva do item c | fato observado | pontuação observada |
|---|---|---:|
| `pair_permutations: 24` | c.pair_permutations verified/supported | **2** |
| `pair_orientations: 16` | c.pair_orientations verified/supported | **2** |
| `total: 384` | c.total verified/supported | **1** |
| `384` | nenhum fato pertinente | **0** |
| `counting_product: 24*16` | c.counting_product verified/supported | **5** |

Portanto, **sim**, cada uma das três primeiras linhas sozinha satisfaz uma obrigação pontuável **no contrato operacional vigente do baseline**. Isso não demonstra que as duas primeiras contêm justificativa combinatória: os dados registrados comprovam o valor atribuído à quantidade, não o argumento.

O [relatório original da ponte P2](TME2_P2_PAUTA_BRIDGE.md), seção “C — oito pontos”, descreve distribuição24=2, orientações16=2 e total384=1, e explicita que `total: 384` prova somente a conclusão de um ponto. Os testes de regressão [cases.json](../../tests/fixtures/tme2_p2_digital/cases.json), casos `c_bare_384` e `c_named_total` nas linhas 757–767, distinguem 0 para numeral solto e 1 para total tipado. Esses são contratos/testes internos de desenvolvimento, não gold consultado nesta tarefa.

## 4. Total e Lean: causa exata da perda de um ponto

`factorial_form` aceita uma expressão com **um só membro**; `original_parts` e `expanded_parts` de `384` são `['384']`. Em `P2Checks.counting`, o valor racional coincide com o alvo e produz `verified`. A variável `formal` continua `None`, porque a construção Lean exige **`len(values)>1`**, além das outras guardas.

`observe` usa, nesse caso, `mechanism='canonical_equivalence'`; não chama Lean. O bridge converte essa origem para `deterministic`, preservando o mecanismo em `verification_source`. Essa origem é expressamente aceita pela declaração de `c.total`. O PautaEngine vê `supported` e atribui o máximo da folha `c.conclusion`: 1.

Assim, o crédito não decorre de provar artificialmente `384=384`, nem de gerar a multiplicação ausente. Decorre de verificar exatamente o valor final escrito, com seu objeto, e usar a regra independente de conclusão.

No Semantic Formal, a registry herdada classifica c.total como FORMAL_STRONG e a registry nova transforma isso em rota exclusivamente FORMAL com policy `executed_lean_verified_and_existing_dependencies`. O adaptador [verification.py](../../app/confia_lean_auditor/experimental/tme_semantic_formal_p2/verification.py), linhas 60–71, força `FORMAL_NOT_ATTEMPTED` quando `student_check` está ausente; a sufficiency fica falsa. O gate exige status positivo e rota coincidente. **Capacidade de executar Lean foi transformada em requisito obrigatório de crédito**, requisito inexistente na pauta dessa conclusão.

O teste [test_unrendered_formal_claim_is_not_attempted_and_not_credited](../../tests/test_tme_semantic_formal_p2_lean.py), linha 48, cristalizou essa política nova ao esperar zero. Passar nesse teste demonstra consistência com a implementação nova, não fidelidade à parcela de conclusão da pauta. A documentação de implementação já reconhecia a diferença. Nenhum desses fatos muda o contrato de 1 ponto do baseline.

A proposição `24*16=384` é uma possível igualdade verificável, não a única entrada de `c.total` e não seu pré-requisito de crédito. `counting_product: 24*16` é ainda outro contrato: método direto de 5, mesmo sem `=384` escrito, verificado deterministicamente.

## 5. Origem da inconsistência e veredito

Há duas decisões distintas no trajeto **5 → 1 → 0**:

| camada | situação dos três claims | score |
|---|---|---:|
| TME_CURRENT, reproduzido nesta tarefa | três valores tipados verificados, folhas 2+2+1 | **5** |
| checker-first fortalecido, reproduzido nesta tarefa | dois argumentos incompletos; total ainda verificado | **1** |
| Semantic Formal, comportamento informado pelo usuário e confirmado pela leitura do adaptador | dois COMPOSITE_INCOMPLETE; total barrado por FORMAL_NOT_ATTEMPTED | **0** |

Não foi feita nova chamada ao extractor para reproduzir o terceiro caso. Não é necessário atribuir esse delta a erro do LLM: os gates de elegibilidade descritos explicam o zero mesmo com extração correta e completa das três linhas.

### Por que não declarar simplesmente sobrecrédito ou uma nota única “corrigida”

[sufficiency_requirements.py](../../app/confia_lean_auditor/student_claims/sufficiency_requirements.py) se apresenta como requisitos sem pontos, separados das pautas imutáveis. Nas linhas 27–30, c.total é FINAL_ANSWER e distribuições/orientações são JUSTIFICATION; a linha 75 exige argumento e diz que conclusão isolada não basta. Isso é **código interno explícito**, não opinião pedagógica externa, e fundamenta o comportamento dos checkers compostos fortalecidos.

Por outro lado, essa política não é um predicado aplicado pelo PautaEngine nem pelo checker original do caminho current. O JSON não contém a subdivisão valor/justificativa, e o checker original admite os valores isolados. Portanto:

- **5 é coerente com pauta + checker + bridge operacionais de TME_CURRENT.** Não há erro de soma, escolha indevida do produto direto ou duplicação.
- **5 não satisfaz a exigência de argumento da política separada JUSTIFICATION** para os primeiros quatro pontos.
- **0 é excessivo em c.total em ambas as leituras**: a parcela de conclusão aceita origem determinística e a política FINAL_ANSWER não exige igualdade Lean.
- **1 é o resultado coerente com a política fortalecida de justificativa mais a parcela independente de resultado**, já observado no checker-first. Adotá-lo como nota normativa única exige tornar explícita a precedência dessa política sobre a aceitação dos valores pelo caminho original.

**Classificação escolhida: `PAUTA_AMBIGUOUS`.** A ambiguidade é a incompatibilidade entre contratos internos de suficiência, não a aritmética do scoring nem o direito a 1 ponto por total tipado. `BASELINE_OVER_CREDIT` para os quatro pontos seria uma conclusão condicionada à autoridade da política JUSTIFICATION; `SEMANTIC_FORMAL_TOO_STRICT` é inequivocamente verdadeiro para a perda do ponto de total, mas sozinho não resolve os dois contratos de 2 pontos. `MIXED_PARTIAL_CREDIT_REQUIRED`, entendido como fixar 1 para o caso, descreve a solução sob a política fortalecida, não uma subdivisão atualmente escrita no JSON.

## 6. Recomendação arquitetural mínima — sem implementação

### Correção inequívoca para c.total

Separar capacidade formal de obrigatoriedade formal. Reutilizar a verificação exata já existente para o **valor explicitamente escrito**, com fonte/subject/contexto, e permitir sua origem `deterministic` no gate de c.total, como a pauta já permite. Registrar, por exemplo, `DETERMINISTIC_VERIFIED` com `verification_kind='written_final_value'`; manter `formal_status=FORMAL_NOT_ATTEMPTED` em campo separado. Esse é um contrato proposto, não uma alteração aplicada.

`FORMAL_VERIFIED` deve continuar reservado à igualdade realmente executada e provada por Lean. Não sintetizar uma igualdade que o aluno não escreveu. Essa correção restitui somente **1 ponto** no caso atual, mantendo os compostos incompletos e os quatro pontos restantes bloqueados no caminho fortalecido.

### Separação dos dois resultados intermediários e suas justificativas

**Não enfraquecer `argument_relation`, a enumeração/bijeção nem o combinador composto.** Manter para cada claim dois resultados independentes:

- valor da quantidade escrito e verificado: válido/inválido/indeterminado;
- justificativa combinatória apresentada: completa/incompleta/falsa, com seus subchecks e procedência.

O gate de pontuação deve consumir apenas o resultado exigido pelo contrato de crédito explicitamente aprovado. Com o contrato operacional original, os valores satisfazem as folhas existentes de 2 e 2; o status da justificativa continua incompleto e não pode ser promovido a COMPOSITE_VERIFIED. Com a política JUSTIFICATION como exigência de crédito, as mesmas folhas exigem o composto, e valores isolados não obtêm esses quatro pontos.

**A pauta atual não prevê uma fração menor por valor isolado nessas duas folhas nem um bônus adicional por justificativa.** Não há base para inventar “1 pelo valor +1 pela justificativa”, “meio ponto por resultado” ou acrescentar pontos além dos máximos atuais. Se se desejar essa separação em parcelas distintas, ela deve ser definida e versionada no contrato de pauta antes de implementação. O produto direto continua uma alternativa de até 5 via `max_of`, nunca um bônus somado ao caminho fatorado.

Antes de qualquer correção dos quatro pontos, documentar qual política de suficiência rege cada folha e alinhar ambos os modos a ela. Isso evita usar `COMPOSITE_INCOMPLETE` como sinônimo de “nenhum resultado matemático válido”, assim como evita usar valor correto como sinônimo de “argumento demonstrado”. Os checkers matemáticos e os status epistemológicos podem permanecer fortes e separados.

## 7. Reprodução e estado final

Comando mínimo para reconstruir o replay principal e identificar as folhas creditadas, sem API e sem gravar código:

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0 \
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python - <<'PY'
from confia_lean_auditor.experimental.tme_semantic_formal_p2.engine import evaluate
text = 'c) pair_permutations: 24\npair_orientations: 16\ntotal: 384'
r = evaluate('p2_dev_partial', 'TME2026P2', text,
             mode='tme_current', use_lean=True)
print(r['score'], r['extractor'])
for credit in r['credits']:
    print(credit['rule_id'], credit['points'],
          [o['obligation_id'] for o in credit['obligations']])
for fact in r['current_bridge']['auditor']['facts']:
    print(fact['fact_id'], fact['source_claim_ids'],
          fact['verification']['status'], fact['verification_source'],
          fact['student_check'])
PY
```

Nesta tarefa também foram inspecionados os registros completos, as decisões de todas as regras c e os cinco controles de isolamento da seção 3. As execuções terminaram com sucesso; não houve teste de compilação Lean, erro técnico ou chamada LLM nesses replays. Não se repetiu o piloto.

SHA preservado: `05c75f4c64ddfec288c96e3519dca01a94e6464f`. `git diff` e `git diff --cached` permanecem vazios para arquivos rastreados. Estado esperado/verificado após a criação deste documento:

```text
?? docs/audits/TME_P2_PARTIAL_CREDIT_FORENSIC_01.md
```

Nenhuma correção foi implementada e nenhum commit foi feito.
