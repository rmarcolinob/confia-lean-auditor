# TME P3 — Checker Coverage 02

Data: 2026-11-05. Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3`. Base preservada: `1165dbf62f854d6d40c0cc5f2bb6fcb02ca381e9`; branch `experiment/tme-semantic-formal-p3`.

**CHECKER_COVERAGE_COMPLETE: 13/13 obrigações com checker forte no contrato digital tipado da rota experimental P3_CHECKER_FIRST.** São 4 DETERMINISTIC_STRONG e 9 COMPOSITE_STRONG; CHECKER_GAP = 0. Nenhuma obrigação foi classificada como SEMANTIC_STRONG. Nenhum SemanticExtractor P3 foi implementado.

Este resultado se aplica à entrada explícita `audit_p3_checker_first`, que fortalece exclusivamente os três gaps de P3(b). O registry histórico/TME_CURRENT continua intacto e conserva o comportamento anterior. Cobertura não significa compreensão universal de prosa, imagens ou representações fora do contrato atual.

## 1. Matriz final

As funções `_a`, `_b`, `_c` pertencem ao checker histórico `lean/student_claim_checkers/tme2_p3.py`. O novo `StrongP3Checks` reutiliza essas funções e especializa somente os três IDs indicados. A classificação é da obrigação completa; provar sua aritmética não transforma automaticamente a justificativa em FORMAL_VERIFIED.

| obligation_id | Regra / pontos | Checker efetivo e evidência mínima | Classificação | Dependências / suficiência | Lean |
| --- | --- | --- | --- | --- | --- |
| a.bottom_white_count | a.count / 2 | `_a`: quantidade `inferiores_brancas`, comparada às cores inferiores da máquina | DETERMINISTIC_STRONG | Contagem explicitamente atribuída; não fornece a probabilidade | Não necessário |
| a.first_white_probability | a.probability / 2 | `_a` + `P3Checks.numerical`: razão branca/6, equivalência racional exata | DETERMINISTIC_STRONG | Resultado isolado autorizado; independente da contagem | Igualdade elegível pode ter prova real |
| b.ordered_pairs | b.space / 2 | `StrongP3Checks.observe`: aritmética + certificado dos 36 eventos + produto 6×6 ou potência 6² escrito e atribuído a pares ordenados | COMPOSITE_STRONG | Duas escolhas uniformes são a premissa do enunciado; 36 e 36=36 não estabelecem a relação | Enumeração/exatidão determinística; sem Lean artificial |
| b.different_favorable | b.different / 2 | `StrongP3Checks.observe`: aritmética + eventos favoráveis i≠j + produto 2×5 escrito e atribuído ao caso | COMPOSITE_STRONG | Fatores derivados dos segundos compartimentos inicialmente brancos e primeiras escolhas distintas; 10 e 10=10 insuficientes | Determinístico |
| b.same_compartment | b.same / 2 | `_b`: conjunto `repeticao_branca:{6}` confrontado com a diagonal branca do estado | DETERMINISTIC_STRONG | Conjunto afirma exclusividade; não depende dos dois créditos anteriores | Determinístico |
| b.second_white_probability | b.conclusion / 2 | `StrongP3Checks.numerical`: aritmética, certificado independente, consistência e relação escrita; ou rota explícita `result_value` | COMPOSITE_STRONG | Partição (10+1)/36, soma 10/36+1/36 ou árvore completa; valor isolado vale somente esta parcela pelo contrato operacional existente. Contexto falso não é ignorado | Lean preservado para igualdade elegível; valor sem igualdade é determinístico |
| b.alternative_complete | b.alternative / 8 alternativos | `_b`: seis ramos corretos derivados do estado + igualdade com soma ponderada completa | COMPOSITE_STRONG | Método completo; max_of com b.counting, sem dupla pontuação | Total aritmético pode ter Lean via b.second_white_probability |
| c.continue_compartments | c.continue / 1 | `_c`: conjunto continuar={1,2} comparado às brancas iniciais | DETERMINISTIC_STRONG | Identificação explícita da continuação | Determinístico |
| c.strategy_case_1 | c.first_strategy / 2 | `_c`: cor e contagem, após primeira retirada do 1, comparadas ao máximo de cores | COMPOSITE_STRONG | Estratégia preta e contagem 3 vinculadas ao caso 1; não exige crédito de continuação | Enumeração finita |
| c.strategy_case_2 | c.second_strategy / 2 | `_c`: cor e contagem, após primeira retirada do 2, comparadas ao máximo de cores | COMPOSITE_STRONG | Estratégia cinza e contagem 3 vinculadas ao caso 2 | Enumeração finita |
| c.conditional_success_1 | c.conditionals / 1 conjunto | `_c`: estratégia válida do caso 1 + probabilidade exata 1/2 | COMPOSITE_STRONG | Regra all_of exige também conditional_success_2 e as duas estratégias | Igualdade elegível pode ter Lean |
| c.conditional_success_2 | mesma parcela conjunta | `_c`: estratégia válida do caso 2 + probabilidade exata 1/2 | COMPOSITE_STRONG | Não há 1 ponto por conditional nem meio ponto automático | Igualdade elegível pode ter Lean |
| c.total_win_probability | c.total / 2 | `_c`: desenvolvimento ponderado/produto combinado, contexto e valor global 1/6 | COMPOSITE_STRONG | Continuação + duas estratégias + duas condicionais; 1/6 isolado não basta | Igualdade elegível pode ter Lean |

A pauta permanece 4+8+8, teto 20. Item b usa max_of entre quatro parcelas de 2 e alternativa completa de 8. As duas condicionais de c dividem uma única regra de 1 ponto. Nenhum peso, dependência ou origem aceita da pauta foi alterado.

## 2. Contrato explícito dos três gaps

O novo módulo não aceita a conclusão de um LLM como premissa. Ele recebe a máquina versionada, reconstrói os registros com o collector existente, enumera as duas retiradas e compara as expressões escritas com relações limitadas e auditáveis. O parâmetro `machine` é uma entrada confiável do problema, não um campo de resposta de aluno; por padrão carrega o asset existente.

| ID | Verdade matemática independente | Suficiência de representação |
| --- | --- | --- |
| b.ordered_pairs | Todos os pares, estados após duas retiradas, medida 1/36 por evento e massa total 1 | `pares_ordenados:6*6=36`, `6^2=36`, produto sem igualdade ou equivalente nos fatores; sem promoção por mera presença de 36 |
| b.different_favorable | Subconjunto i≠j e segunda cor branca; duas classes pelo segundo índice, cinco eventos em cada | `favoraveis_distintos:2*5=10`, ordem inversa ou `2*(6-1)`; não basta confirmar 10=10 |
| b.second_white_probability | União disjunta de 10 diferentes e 1 repetido; razão 11/36; seis condicionais para a rota árvore | Desenvolvimento reconhecido é validado como desenvolvimento. Resultado puro tem rota própria, não recebe selo de argumento |

`b.conclusion` depende somente de `b.second_white_probability` no JSON, e a fixture histórica `b_answer_only` prevê 2 pontos. A solicitação atual permite preservar crédito explícito do contrato operacional. Por isso `11/36` isolado mantém 2, com `result_credit_only=true`, `argument_satisfied=false` e `FORMAL_NOT_ATTEMPTED`. Isso resolve G3 pela separação valor/argumento, sem inventar crédito nem afirmar que a pauta pedagógica exige apenas um número. Nenhum dos outros 6 pontos de b é produzido pelo valor isolado.

Para G1/G2, o fortalecimento é intencional: os produtores antigos checavam o valor, mas não a relação. A nova rota exige a relação no vocabulário tipado e usa a uniformidade dada pelo enunciado; não exige uma frase adicional sobre uniformidade nem afirma ter compreendido uma explicação livre.

## 3. Estados e política de crédito

```text
texto com atribuição e fonte
→ collector determinístico existente
→ checker exato + certificado finito + relação/contrato de valor
→ COMPOSITE_VERIFIED / FAILED / INCOMPLETE / ERROR
→ FactResult e VerificationLink
→ bridge existente: fonte, fingerprint, conflito
→ evidência elegível
→ PautaEngine existente
```

O composto exige todos os componentes aplicáveis. Resultado falso produz refuted/COMPOSITE_FAILED; forma ausente/não reconhecida produz unverified/COMPOSITE_INCOMPLETE; erro de certificado produz technical_error/COMPOSITE_ERROR. Divergência explícita entre contagens/repetição e total correto bloqueia a conclusão e recomenda revisão. Evidências positiva e negativa da mesma obrigação permanecem sujeitas à reconciliação da bridge; não se escolhe silenciosamente a positiva.

`FORMAL_VERIFIED`, `FORMAL_REFUTED`, `FORMAL_UNPROVED`, `FORMAL_ERROR` e `FORMAL_NOT_ATTEMPTED` ficam observáveis no componente aritmético quando ele existe. `DETERMINISTIC_VERIFIED`, `DETERMINISTIC_FAILED`, `DETERMINISTIC_INCOMPLETE` e `DETERMINISTIC_ERROR` descrevem os checks locais. Ausência de relação não é refutação matemática. A origem do composto é determinística; o recibo Lean e a proposição original ficam anexados ao componente, sem apresentar uma prova aritmética como prova Lean da máquina inteira.

## 4. Evidência de cobertura e limites

Validação final: **274 testes pytest distintos aprovados** (176 anteriores + 90 novos de contrato/regressão + 8 novos com Lean real), replay TME_CURRENT **25/25**, e exercício positivo das 13 obrigações na rota fortalecida. Lean real: 12 provas e 2 refutações no replay histórico; 5 provas e 3 refutações nos novos testes. Zero FORMAL_UNPROVED e zero FORMAL_ERROR nas execuções reais. Resultados detalhados no [relatório de fortalecimento](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_CHECKER_STRENGTHENING_01.md).

O veredito não abrange prosa livre, árvore visual, novos estados escritos pelo estudante ou todas as expressões algebricamente equivalentes. `check_event_set` verifica conjuntos tipados contra enumeração própria, mas é API matemática de baixo nível: não concede crédito e ainda não é uma nova gramática de extração. Os limites históricos G4–G7 do diagnóstico permanecem documentados: em especial o checker antigo de b.alternative_complete ainda pode marcar shape ausente como refuted não formal, e o total de c conserva suas restrições. Esses produtores estão fora dos três gaps autorizados; a classificação forte mantém o mesmo domínio limitado do diagnóstico e não declara corrigidos esses limites.

## 5. Veredito

**CHECKER_COVERAGE_COMPLETE.** Os três CHECKER_GAP originais possuem agora checkers compostos explícitos; 13/13 obrigações cobertas na rota experimental, com resultado isolado separado da justificativa. O TME_CURRENT continua preservado. Esta entrega termina antes de implementar Semantic Formal/Extractor P3.
