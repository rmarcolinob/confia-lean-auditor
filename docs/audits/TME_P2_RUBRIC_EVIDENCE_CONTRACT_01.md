# TME P2 — contrato de evidência da pauta 01

Data: 2026-11-05. Base: `05c75f4c64ddfec288c96e3519dca01a94e6464f`. Escopo: **item c no modo TME_SEMANTIC_FORMAL P2**, após a correção mínima de c.total. Este contrato registra a decisão expressa do usuário nesta etapa: preservar os três checkers compostos e admitir valor final determinístico para a conclusão. Não altera a pauta JSON nem o baseline histórico.

A pauta P2(c) informada nesta solicitação prevê: máximo/soma e centro, juntos, 1 ponto; pares das extremidades, 2; distribuição dos quatro pares, 2; duas posições por par, 2; conclusão da contagem, 1. O caminho direto de produto é a alternativa interna existente, limitada aos mesmos 5 pontos de contagem, não uma parcela adicional.

## Requisitos comuns

`NO CHECKER → NO AUTOMATIC CREDIT`. Cada evidência positiva precisa ter trecho literal e binding válidos, atribuição ao estudante, contexto assertivo/positivo, item e subject compatíveis, verificação independente suficiente e ausência de conflito impeditivo. Hipótese, negação, citação, abandono, fonte incerta ou número incidental não são convertidos em crédito. A sugestão de rota do extractor não tem autoridade.

Os valores abaixo são objetivos matemáticos do contrato, não dados de avaliação/gold. Todos os exemplos supõem que foram escritos no item c e passaram pelos requisitos comuns.

## Obrigações do item c

| obligation_id | texto/objetivo e pontos | evidência mínima suficiente | exemplos suficientes | exemplos insuficientes | checker preservado | rotas aceitáveis | status para crédito |
|---|---|---|---|---|---|---|---|
| `c.max_center` | centro 9 no caso de maior soma; compartilha bloco de 1 com max_sum | valor 9 atribuído ao centro máximo, ou fato de configuração admitido pelo produtor existente | `max_center: 9` | número 9 sem objeto; centro 8; somente soma 18 | `P2Checks.value` / `configuration` | DETERMINISTIC | DETERMINISTIC_VERIFIED; o ponto da regra exige também max_sum supported |
| `c.max_sum` | maior soma 18; mesmo bloco conjunto de 1 | valor 18 atribuído à maior soma | `max_sum: 18` | 18 incidental; soma 17; somente centro 9 | `P2Checks.value` / `configuration` | DETERMINISTIC | DETERMINISTIC_VERIFIED; exige também max_center supported para o ponto |
| `c.pairs` | pares das extremidades para o máximo; 2 | quatro pares complementares, todos os externos usados uma vez, soma 9 por par | `pairs: {(1,8),(2,7),(3,6),(4,5)}`; permutação/orientação equivalentes | três pares; repetição de dígito; lista sem associação às extremidades | `P2Checks.pair_facts`, `inspect_pairs` / configuração admitida | DETERMINISTIC | DETERMINISTIC_VERIFIED |
| `c.pair_permutations` | contar distribuições dos quatro pares nas quatro linhas: 4!=24; 2 | aritmética correta, componentes de contagem certificados e relação escrita suficiente de permutação | `pair_permutations: 4!=24`; `As distribuições dos pares são 4!=24.`; forma equivalente aceita `4*3!=24` | literal 24; `pair_permutations: 24`; igualdade alheia `2^3*3=24`; afirmação de 24 distribuições sem estrutura argumentativa reconhecida | `StrongP2Checks.observe` → aritmética existente + `finite_certificate` + `argument_relation('pair_permutations',…)` | COMPOSITE; subcheck aritmético DETERMINISTIC ou FORMAL | COMPOSITE_VERIFIED; três componentes suficientes |
| `c.pair_orientations` | duas posições por cada um dos quatro pares: 2^4=16; 2 | aritmética correta, quatro escolhas binárias certificadas e vínculo escrito às orientações | `pair_orientations: 2^4=16`; `As orientações são 2*2*2*2=16.` | literal 16; `pair_orientations: 16`; `4+12=16`; afirmação de 16 orientações sem relação suficiente | mesma família, `argument_relation('pair_orientations',…)` | COMPOSITE; aritmética DETERMINISTIC ou FORMAL | COMPOSITE_VERIFIED |
| `c.total` | conclusão total de 384 preenchimentos; 1 | **A:** igualdade realmente escrita e provada, com alvo total; **B:** valor total explicitamente escrito, verificado exatamente, sem igualdade inventada | `total: 384`; `O total de preenchimentos é 384.`; `total: 24*16=384` | 385; 384 sem vínculo aceito ao total; `total: 24*16=364`; representação não verificável; conflito não resolvido | `P2Checks.counting('total',384)`; `rational_value`; ciclo `check_real_record` quando há igualdade sob as guardas originais | **FORMAL ou DETERMINISTIC, conforme representação** | FORMAL_VERIFIED no caminho A; DETERMINISTIC_VERIFIED no B |
| `c.counting_product` | método equivalente explícito de produto; alternativa de até 5 | produto das etapas distribuição/orientação, aritmética correta, enumeração/bijeção e relação suficientes | `counting_product: 24*16=384`; `counting_product: 4!*2^4=384`; forma inversa equivalente aceita | 384; `12*32=384`; fatores/resultado falsos; produto sem relação reconhecida | mesma família, `argument_relation('counting_product',…)`, enumeração independente/inversa | COMPOSITE; aritmética DETERMINISTIC ou FORMAL | COMPOSITE_VERIFIED |

O adaptador semântico atual é textual. As referências a configuração na tabela descrevem capacidades preservadas do checker, não uma nova capacidade do extractor de criar DiagramState ou interpretar imagem. Fonte estruturada só pode entrar por contrato autorizado existente; prosa não inventa posições.

## Resultados intermediários versus argumento

Para `c.pair_permutations`:

1. `24` isolado, inclusive normalizado como valor da quantidade, não estabelece o argumento.
2. Uma afirmação explicitamente ligada ao número de distribuições é **candidata** a essa obrigação. A pertinência não substitui a avaliação da relação combinatória. Se a projeção contém apenas `24`, o checker atual mantém `argument_not_established` e COMPOSITE_INCOMPLETE.
3. `4!=24` ligado à distribuição dos quatro pares é suficiente quando o binding/contexto, a aritmética e os componentes certificados também são válidos.

Para `c.pair_orientations`:

1. `16` isolado é insuficiente como justificativa.
2. “Existem 16 orientações” é candidata pertinente, mas o número e o rótulo não demonstram as quatro escolhas binárias para o checker composto.
3. `2^4=16` ou produto equivalente dos quatro fatores 2, ligado às orientações, é suficiente se os demais componentes forem válidos.

Prosa equivalente continua limitada às representações já admitidas pelo mapper/checker. Esta correção não ensina o modelo a completar uma fórmula não escrita nem torna qualquer explicação verbal automaticamente suficiente. `relation FAILED` com `mathematical_refutation=false` significa argumento não estabelecido, não falsidade do número 24 ou 16.

## Dois caminhos de c.total

### Valor final sem igualdade

A seleção determinística ocorre para uma expressão fechada de total com **um só membro**, conforme a gramática combinatória existente. Inclui o literal 384 e expressões fechadas que denotam esse valor, como `384/1` ou `24*16`, quando explicitamente vinculadas ao total. Não é um checker novo de cálculo: o valor continua decidido por `P2Checks.counting`/`rational_value`.

Saída elegível:

```text
route = DETERMINISTIC
status = DETERMINISTIC_VERIFIED
verification_kind = written_total_value
formal_status = FORMAL_NOT_ATTEMPTED
formal_attempted = false
```

A ausência de prova formal não invalida esse resultado determinístico. Um número sem vínculo aceito pelo mapper ao objeto “total de preenchimentos” continua insuficiente; não há autorização para reclassificar número incidental como conclusão.

### Igualdade escrita

Se há dois ou mais membros, a rota permanece FORMAL. As guardas/renderização e o ciclo Lean são os originais. `24*16=384`, quando verificado, recebe FORMAL_VERIFIED e o mesmo ponto final. O resultado não se torna determinístico depois de uma tentativa frustrada. Igualdade não renderizável ou sem execução formal conserva o diagnóstico correspondente e não recebe crédito por essa rota.

FORMAL_REFUTED, FORMAL_UNPROVED, FORMAL_ERROR e FORMAL_NOT_ATTEMPTED permanecem distintos. Não se cria `384=384` para um estudante que só escreveu o valor, nem se recorta o lado correto de uma igualdade falsa.

### Duplicação e conflito

Valor 384 e igualdade verdadeira podem ambos ser registrados; a obrigação c.total e a folha c.conclusion são creditadas **uma única vez**, em 1 ponto. Valor correto + igualdade formal falsa entram na reconciliação existente; conflito não resolvido bloqueia o crédito e recomenda revisão. Uma refutação formal nunca é apagada pelo resultado determinístico. O gate também exige que a rota de cada verificação coincida com o mapping aprovado daquela evidence, além de pertencer à allowlist da obrigação.

## Pontuação e alcance da decisão

- `c.maximum`: all_of(max_center,max_sum), máximo 1.
- `c.max_pairs`: all_of(pairs), máximo 2.
- `c.factorized_count_path`: soma distribuições 2 + orientações 2 + conclusão 1.
- `c.counting`: max_of(caminho fatorado, produto direto), máximo 5.
- Item c: máximo 8; total da prova: máximo 20.

Não existe bônus por anexar o método direto ao caminho fatorado. Não foram criadas frações de ponto para números 24/16 isolados nem subdivisões dos critérios de 2 pontos. A decisão atual mantém esses critérios compostos e corrige somente a elegibilidade do resultado final.

Para a fonte `pair_permutations: 24; pair_orientations: 16; total: 384`, a previsão do modo semântico é **1 ponto**, com os dois compostos incompletos. O TME_CURRENT permanece em 5 por seu contrato histórico. Esta diferença é agora uma decisão explícita de suficiência para as duas etapas de 2 pontos, conforme a solicitação atual; não foi feito tuning para imitar o baseline.

Referências: [pauta congelada](../../examples/pautas/tme2_problem2.v1.json), [checkers P2 originais](../../app/confia_lean_auditor/lean/student_claim_checkers/tme2_p2.py), [checkers fortalecidos](../../app/confia_lean_auditor/experimental/tme_p2_checker_first/components.py), [registry de rotas](../../app/confia_lean_auditor/experimental/tme_semantic_formal_p2/registry.py), [diagnóstico histórico](TME_P2_PARTIAL_CREDIT_FORENSIC_01.md) e [relatório da correção](TME_P2_PARTIAL_CREDIT_FIX_01.md).
