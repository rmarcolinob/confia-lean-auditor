# TME P2 — CHECKER-FIRST / LEAN-STRONG — diagnóstico 01

Data: 2026-11-05 (America/Fortaleza). Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2`. Branch: `experiment/tme-semantic-formal-p2`. SHA inspecionado: **`34732d445ff1e885a7156278ad4bb81c1fed25b2`**. Estado inicial de `git status --short`: vazio.

**Veredito: CHECKER_STRENGTHENING_REQUIRED.** Há produtores/checkers para os 23 IDs de P2, uma ponte com validação de proveniência e provas Lean de escopo limitado. Isso não basta para declarar cobertura forte de todas as obrigações pedagógicas: há um reconhecimento de integralidade promovido diretamente a fato, três obrigações de contagem cuja verificação aritmética não valida toda a justificativa combinatória, e rotas híbridas antigas que admitem crédito sem auditoria matemática independente.

Este documento resulta de **inspeção estática** do código, pauta, contratos e testes existentes. Nenhum teste, replay, avaliação LLM, compilação Lean ou piloto foi executado nesta etapa. Exemplos adversariais abaixo são consequências da leitura do código, não resultados de execuções novas. Nenhum gold ou holdout foi consultado. Nenhum componente foi implementado ou alterado; nenhum commit foi feito. Os valores esperados discutidos vêm da pauta e dos checkers, não de rótulos de avaliação externos.

## 1. Pauta P2

### 1.1. Escopo matemático e fluxo real

O contrato implementado usa nove posições: centro `x` e extremos A–H. As quatro linhas **rotuladas** são A–centro–E, B–centro–F, C–centro–G e D–centro–H. Uma configuração válida usa os inteiros 1–9 exatamente uma vez e tem as quatro somas iguais a `S`. Não se identifica disposição por semelhança com uma figura-modelo e não se divide a contagem por rotações/reflexões. Essa é a semântica verificável de [p2_diagram.py][diagram], corroborada pelas permutações dos testes.

O caminho primário é:

```text
transcrição aceita / itens digitais explícitos a,b,c
  → split_p2_input
  → collect_tme2_p2_text / MathClaimRecord
  → verify_tme2_p2 / P2Checks + diagramas confirmados
  → FactResult com status, mecanismo e vínculos
  → bridge_tme2_p2 / bridge_facts
  → PautaEvidence
  → PautaEngine
```

[registry.audit_tme][registry] carrega a pauta e chama [audit_tme2_p2][orchestration]. A integração de transcrição aceita chama esse mesmo entry point; [accepted_audit.py][accepted] separa apenas itens explícitos, exige confirmação/origem estudante para diagramas e conserva avisos de desenho não reconhecido. **SemanticSufficiencyGate e EvidenceReconciler não estão nessa cadeia primária.** Também não há AwardGate C1 de P2: o [registry experimental C1][c1registry] restringe a execução a P1.

Extração e representação atuais:

| componente | contrato observado | limite relevante |
|---|---|---|
| `split_p2_input` | dict de a/b/c; cada item é texto ou `{text, diagrams}`; até 8 diagramas/item | não infere item ou topologia a partir de imagem |
| `collect_digital_items` | enquadra itens, mantém offsets/hash, extrai literais e claims genéricos, atribui dono e permite suplemento opt-in | limite de 20.000 caracteres; a ordem de execução dos checkers não é a ordem textual |
| `extract_p2_quantities` / `extract_named_math` | notação tipada `nome: valor`; introdução adicional `Os pares são …` | gramática por linha; reticências e nomes não suportados são rejeitados |
| `math_named_quantity` / `named_quantity` | tipos `math`, `relation`, `integer_pairs`, `integer_set`, `integer_mapping`, `enum`, `congruence`, `combinatorial_math` | `P2Checks.select` exige esse contrato, item exato, forma canônica e fonte atribuível/grounded |
| extractor matemático genérico | reconhece expressões/relações e conserva registros genéricos | um registro genérico não recebe automaticamente o subject tipado esperado por `P2Checks.select` |
| `diagram_state` | `TME2P2DiagramState` e `StructuredSourceBinding`; centro/posições inteiros estritos, desconhecidos preservados | só `confirmed=True` e `origin=student` autorizam atribuição; confiança OCR sozinha não basta |
| `native-real-projection.v1` | projeta um registro tipado em `math_relation` para o ciclo Lean e valida novamente a fonte | não é reconhecimento de imagem nem prova de toda a interpretação pedagógica |
| suplemento legado `semantic.py` | opt-in `CONFIA_TME_SEMANTIC_ENABLED=1` (default no código: 0); propõe payloads que passam pelos checkers | exclui `placement` do vocabulário LLM; fonte literal, subject, números, contexto e representação são filtrados |
| `obligation_semantic` / `evidence_id_semantic` | rotas experimentais de candidatos por obrigação e IDs de evidência; podem projetar para checkers existentes | não equivalem a um SemanticExtractor C1 de P2; configurações espaciais ficam `unmapped`/qualitative |

Fontes: [coletor P2][collector], [coletor compartilhado][digital], [parser tipado][named], [suplemento legado][legacy], [catálogo matemático][catalog]. O caminho `primary_audit` desabilita explicitamente o suplemento via contexto; o caminho normal `audit_tme` conserva a configuração opt-in existente. Nenhuma flag foi alterada neste diagnóstico.

### 1.2. Pesos e regras completas

A [pauta versionada][pauta] tem máximo 20: **a=5, b=7, c=8**; política `withhold`; origens aceitas em todas as declarações: `deterministic` e `student_lean`. São **23 obrigações declaradas; 19 aparecem diretamente em regras pontuáveis e 4 são auxiliares**. Não há 23 parcelas de pontos independentes.

| regra da pauta | estratégia | obrigações / filhos | pontos máximos |
|---|---|---|---:|
| `a` | max_of | configuração completa OU caminho parcial | 5 |
| `a.complete_configuration_path` | all_of | `a.complete_configuration` | 5 |
| `a.obligation_path` | additive | três regras abaixo | 5 |
| `a.rule` | any_of | `a.pair_sum` OU `a.line_sum` | 1 |
| `a.four_pairs` | all_of | `a.pairs` | 2 |
| `a.placed_pairs` | all_of | `a.placement` | 2 |
| `b` | additive | cinco regras abaixo | 7 |
| `b.relation` | all_of | `b.balance_relation` | 2 |
| `b.formula` | all_of | `b.sum_formula` | 1 |
| `b.integral_centers` | all_of | `b.centers` | 2 |
| `b.sums` | all_of | `b.center_sums` | 1 |
| `b.realizability` | all_of | `b.realizable_1`, `b.realizable_5`, `b.realizable_9` juntos | 1 |
| `c` | additive | máximo + pares + contagem | 8 |
| `c.maximum` | all_of | `c.max_center` e `c.max_sum` juntos | 1 |
| `c.max_pairs` | all_of | `c.pairs` | 2 |
| `c.counting` | max_of | caminho fatorado OU produto direto | 5 |
| `c.factorized_count_path` | additive | distribuições + orientações + conclusão | 5 |
| `c.distributions` | all_of | `c.pair_permutations` | 2 |
| `c.orientations` | all_of | `c.pair_orientations` | 2 |
| `c.conclusion` | all_of | `c.total` | 1 |
| `c.direct_product_path` | all_of | `c.counting_product` | 5 |

Tabela completa das obrigações; papéis da evidência vêm de [sufficiency_requirements.py][requirements]. Nas descrições genéricas da pauta, o conteúdo é explicitado pelo checker/catálogo, sem criar obrigação nova.

| obligation_id | item | descrição pedagógica / claim esperado | papel atual | peso e vínculo |
|---|---|---|---|---|
| `a.pair_sum` | a | extremos de uma linha somam 10, centro 5 | FACT | compartilha 1 com `a.line_sum` por any_of |
| `a.line_sum` | a | soma comum 15 no caso centro 5 | FACT | mesmo bloco de 1; não acumula |
| `a.pairs` | a | quatro pares opostos corretos usando os oito externos uma vez | ENUMERATION | 2 no caminho parcial |
| `a.placement` | a | colocação explícita completa e válida com centro 5 | COMPLETE_METHOD | 2 no caminho parcial |
| `a.complete_configuration` | a | preenchimento completo válido, suficiente sem explicação | COMPLETE_METHOD | 5 no caminho alternativo |
| `b.balance_relation` | b | relação de contagem `4S=45+3x` | INTERMEDIATE_STEP | 2 |
| `b.sum_formula` | b | `S=(45+3x)/4` | INTERMEDIATE_STEP | 1 |
| `b.integral_sum` | b | afirmação de que S é inteiro | FACT | auxiliar, 0 direto; pode habilitar centros |
| `b.modular_condition` | b | congruência cujo conjunto de soluções em 1–9 é `{1,5,9}` | JUSTIFICATION | auxiliar, 0 direto; pode habilitar centros |
| `b.centers` | b | conjunto exato `{1,5,9}`, com base de integralidade/congruência | JUSTIFICATION | 2 |
| `b.admissible_center` | b | admissibilidade de um centro explicitamente indicado | FACT | controle auxiliar, 0 direto |
| `b.center_sums` | b | associações `(1,12),(5,15),(9,18)` | ENUMERATION | 1 |
| `b.sum_at_five` | b | soma 15 para centro 5 | FACT | controle auxiliar, 0 direto |
| `b.realizable_1` | b | quatro pares/diagrama que realizam centro 1, soma 12 | ENUMERATION | participa do bloco conjunto de 1 |
| `b.realizable_5` | b | quatro pares/diagrama que realizam centro 5, soma 15 | ENUMERATION | participa do mesmo bloco |
| `b.realizable_9` | b | quatro pares/diagrama que realizam centro 9, soma 18 | ENUMERATION | participa do mesmo bloco |
| `c.max_center` | c | centro que maximiza a soma: 9 | FACT | junto com `c.max_sum`: 1 |
| `c.max_sum` | c | maior soma comum: 18 | FINAL_ANSWER | mesmo bloco de 1 |
| `c.pairs` | c | pares `(1,8),(2,7),(3,6),(4,5)` | ENUMERATION | 2 |
| `c.pair_permutations` | c | 24 distribuições dos quatro pares nas linhas distintas | JUSTIFICATION | 2 no caminho fatorado |
| `c.pair_orientations` | c | 16 orientações independentes dos quatro pares | JUSTIFICATION | 2 no caminho fatorado |
| `c.total` | c | total explícito de 384 preenchimentos | FINAL_ANSWER | 1 no caminho fatorado |
| `c.counting_product` | c | produto explícito das contagens 24 e 16, com desenvolvimento | JUSTIFICATION | 5 no caminho direto |

### 1.3. Dependências efetivamente implementadas

- **A:** `max_of` impede duplicar os dois caminhos. `a.rule` é OU, não exige ambos os fatos. A configuração válida também produz fatos parciais; isso não multiplica a nota. Pares sem posições não geram placement. Pares repetidos podem demonstrar apenas soma 10, sem satisfazer a enumeração completa.
- **B2:** a pauta não exige `b.balance_relation` para o ponto de `b.sum_formula`. O checker valida a fórmula por equivalência mesmo sem B1; a execução Lean de B2 exige B1 verificado. Não confundir requisito da prova Lean com dependência de crédito da pauta.
- **B3:** o checker exige conjunto exato e uma base: `b.modular_condition` verificada **OU** `b.integral_sum` verificada junto de `b.balance_relation` verificada, ou, se esta não estiver verificada, `b.sum_formula` verificada. Lista isolada não basta. Se a via modular está verificada, ela é escolhida como base. As refs dessa base ficam em metadata (`argument_refs` / contexto formal); não são, todas, `source_claim_ids` da prova do conjunto.
- **B4:** `b.center_sums` verifica a lista exata; a prova Lean usa a relação do problema como hipótese, sem exigir B1/B2 creditados previamente. B5 exige os três centros juntos; um centro realizável sozinho não paga a fração de 1/3.
- **C:** a pauta não condiciona a contagem ao crédito prévio de `c.maximum`, `c.pairs` ou dos itens a/b. `c.total` pode dar 1 isoladamente, quando tipado como total; a regressão `c_named_total` preserva esse comportamento. O produto direto não pode inventar C1/C2 nem somar seus 5 pontos aos 5 do caminho fatorado.
- **Itens anteriores:** os checkers primários selecionam o próprio item, sem transporte automático a→b→c. O reconciliador híbrido antigo tem permissões amplas b←a e c←a,b, ainda exigindo evidência do destino. O gate independente tem permissões específicas: `b.realizable_5←a` e `c.pairs←b`, além das regras explícitas de ligação contextual. Nenhuma dessas permissões cria dependências novas na pauta.

O futuro reforço deve separar **premissa matemática**, **evidência de que o estudante apresentou o passo** e **pré-requisito de pontuação**. Provar uma consequência do enunciado não demonstra que o estudante a escreveu.

## 2. Checker Coverage Matrix

Critério de classificação usado nesta auditoria:

- **FORMAL_STRONG:** existe checker Lean com proposição vinculada ao claim e escopo matemático adequado à conclusão indicada; pode haver guardas e caminho determinístico alternativo. Não significa que todo input daquele ID execute Lean, nem que todas as dependências pedagógicas estejam formalizadas.
- **DETERMINISTIC_STRONG:** há verificação exata suficiente para o fato/lista/configuração tipados; um teorema Lean não é necessário para cada entrada. Os limites de atribuição/contexto continuam obrigatórios.
- **SEMANTIC_CHECKER:** seria necessário um verificador dedicado para evidência que não admita verificação matemática adequada. Nenhuma das 23 obrigações exige essa rota como primária nesta representação finita de P2.
- **CHECKER_GAP:** há produtor de fato, mas falta uma validação independente de parte essencial do papel pedagógico declarado. Não quer dizer que inexiste qualquer função com aquele ID. Aqui há 4 gaps de força: integralidade e três justificativas combinatórias.

Rota atual abaixo é a do **checker primário**. `D` abrange `deterministic` e `canonical_equivalence`; `L` é `student_lean`, somente quando os guardas de construção/projeção permitem. “D suficiente?” avalia a viabilidade de um checker determinístico explícito, incluindo o reforço proposto; não certifica automaticamente a implementação atual.

| obligation_id | rubric_item | descrição pedagógica | claim matemático esperado | representação mínima necessária | checker existente | rota atual | Lean formalizável? | D suficiente? | semântico necessário? | dependências para crédito | risco de representação | classificação |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `a.pair_sum` | a | soma dos extremos | soma 10 | valor tipado ou quatro pares explícitos | `value`; `pair_facts`; `configuration` | D | sim | sim | não | any_of com line_sum, bloco 1 | numeral avulso não nomeia quantidade; duplicatas só autorizam a regra parcial | DETERMINISTIC_STRONG |
| `a.line_sum` | a | soma da linha | 15 | valor/igualdade tipados | `value` | D | sim | sim | não | mesmo bloco 1 | não é produzido como fato separado pelo diagrama; 15 avulso não basta | DETERMINISTIC_STRONG |
| `a.pairs` | a | enumeração dos externos | quatro pares de soma 10, externos exatos | lista de pares inteiros ou estado completo | `inspect_pairs`; `configuration` | D | sim, sobre estado transcrito | sim | não | bloco próprio 2 | não confundir lista de pares com posições; multiplicidade importa | DETERMINISTIC_STRONG |
| `a.placement` | a | colocação válida | bijeção dos dígitos e quatro somas 15 | mapping centro/A–H ou DiagramState confirmado | `configuration` / `inspect_diagram` | D | parcial: estado sim, pixels não | sim | não | 2 no caminho parcial | imagem sem transcrição não é estado; desconhecidos não completam o desenho | DETERMINISTIC_STRONG |
| `a.complete_configuration` | a | preenchimento suficiente | mesma configuração válida, centro 5 | estado completo com proveniência | `configuration` / `inspect_diagram` | D | parcial: estado sim, pixels não | sim | não | caminho completo 5, max_of | cópia/figura de referência não é resposta atribuível | DETERMINISTIC_STRONG |
| `b.balance_relation` | b | relação de contagem | `4S=45+3x` | relação tipada equivalente, x e S preservados | `compare` em `b()` | D | sim | sim para a relação explícita | não | 2; sem B2 obrigatório | contexto da multiplicidade é metadata do engine, não derivação formal do diagrama | DETERMINISTIC_STRONG |
| `b.sum_formula` | b | isolamento de S | `S=(45+3x)/4` | RHS em x, opcional igualdade com S | `compare`; `check_real_record` | D / L com B1 verificado | sim | sim | não | 1 independente; B1 só para Lean atual | S no RHS e tautologia S=S não são fórmula; divisão real, não inteira | FORMAL_STRONG |
| `b.integral_sum` | b | integralidade de S | `S∈ℤ` por soma de dígitos inteiros | enum tipado `integer/inteiro/z` atualmente | seleção + `observe(..., True)` | D declarado | sim | sim, com regra de domínio explícita | não | 0 direto; habilita B3 | reconhecimento do enum é promovido a validação; sujeito/tipo precisam de contrato | CHECKER_GAP |
| `b.modular_condition` | b | divisibilidade pertinente | condição equivalente a x≡1 mod4 no domínio 1–9 | congruência afim em x, módulo inteiro 1–1000 | `modular_candidates` e igualdade de conjuntos | D | sim | sim | não | 0 direto; alternativa de base para B3 | congruência não afim/racional não suportada; equivalência apenas no domínio declarado | DETERMINISTIC_STRONG |
| `b.centers` | b | alternativas completas justificadas | exatamente `{1,5,9}` | conjunto inteiro e base B3 explícita | igualdade exata + `state` + teorema inteiro | D / L se estado prévio verified | sim | sim | não | 2; base modular OU integral+relação/fórmula | Lean prova necessidade, não sozinho completude/existência; via integral herda G1 | FORMAL_STRONG |
| `b.admissible_center` | b | centro individual admissível | ∃S inteiro, 1≤x≤9 e 4S=45+3x | inteiro explícito com limite de magnitude | teste de pertinência + existência/refutação Lean | D / L | sim | sim | não | 0 direto | centro isolado não equivale à lista completa nem à realização espacial | FORMAL_STRONG |
| `b.center_sums` | b | associações exatas | `(1,12),(5,15),(9,18)` | exatamente três pares centro/soma | comparação exata + três implicações Lean | D / L com centros 1,5,9 | sim | sim | não | 1; sem B1 obrigatório | troca da ordem dentro do par altera sentido; igualdade de lista não é desenho | FORMAL_STRONG |
| `b.sum_at_five` | b | controle da soma em 5 | `4S=60 → S=15` | inteiro tipado | `value==15` + implicação Lean | D / L | sim | sim | não | 0 direto | valor sem objeto não prova a associação | FORMAL_STRONG |
| `b.realizable_1` | b | testemunho construtivo | centro1, soma12, externos exatos | quatro pares ou estado completo confirmado | `inspect_pairs`; `configuration` | D | sim, para testemunho discreto | sim | não | junto dos outros dois, bloco 1 | condição necessária de centro não prova existência | DETERMINISTIC_STRONG |
| `b.realizable_5` | b | testemunho construtivo | centro5, soma15, externos exatos | quatro pares ou estado completo confirmado | `inspect_pairs`; `configuration` | D | sim, para testemunho discreto | sim | não | mesmo bloco 1; primário não importa a | reuso de a exige vínculo explícito, não transferência silenciosa | DETERMINISTIC_STRONG |
| `b.realizable_9` | b | testemunho construtivo | centro9, soma18, externos exatos | quatro pares ou estado completo confirmado | `inspect_pairs`; `configuration` | D | sim, para testemunho discreto | sim | não | mesmo bloco 1 | orientação/ordem dos pares irrelevantes; dígitos repetidos não | DETERMINISTIC_STRONG |
| `c.max_center` | c | conclusão sobre máximo | 9 | valor tipado ou centro de estado completo | `value`; `configuration` | D | sim | sim para conclusão exata | não | junto de max_sum, bloco 1 | checker do valor não prova monotonicidade; ramo diagramático não exige valid global | DETERMINISTIC_STRONG |
| `c.max_sum` | c | valor máximo | 18 | valor tipado ou soma comum em estado completo | `value`; `configuration` | D | sim | sim para conclusão exata | não | mesmo bloco 1 | estado balanceado com repetição pode informar 18; não certifica todo o desenho | DETERMINISTIC_STRONG |
| `c.pairs` | c | enumeração correta | `(1,8),(2,7),(3,6),(4,5)` | quatro pares / estado centro9 | `inspect_pairs`; `configuration` | D | sim | sim | não | 2 independente | lista não equivale a justificar a contagem de todas as colocações | DETERMINISTIC_STRONG |
| `c.pair_permutations` | c | contagem das distribuições | cardinalidade de bijeções entre 4 pares e 4 linhas =24 | quantidade tipada; fatoriais/igualdade quando escritos | `counting(…,24)` | D / L aritmético condicional | sim | sim, com checker estrutural | não | 2, sem c.pairs pré-creditado | aceita qualquer expressão fechada de valor24; cálculo não prova que conta distribuições | CHECKER_GAP |
| `c.pair_orientations` | c | escolhas internas independentes | cardinalidade das 4 escolhas binárias =16 | quantidade tipada; potência/igualdade quando escrita | `counting(…,16)` | D / L aritmético condicional | sim | sim, com checker estrutural | não | 2 independente | valor16 não valida independência nem interpretação das pontas | CHECKER_GAP |
| `c.total` | c | conclusão final | total384 | `total: 384` ou igualdade fechada pertinente | `counting(…,384)` | D / L aritmético condicional | sim | sim para FINAL_ANSWER | não | 1; não exigir retroativamente as etapas anteriores | numeral solto não pontua; prova aritmética não prova completude combinatória | FORMAL_STRONG |
| `c.counting_product` | c | método de produto completo | distribuições×orientações=384 | produto explícito com fatores de valores24 e16 | `two_count_factors`, valores e igualdade Lean | D / L aritmético condicional | sim | sim, com produto/bijeção explícitos | não | caminho direto 5; não soma ao fatorado | raízes sintáticas e valores dos fatores não certificam sua origem combinatória | CHECKER_GAP |

Contagem da matriz: **6 FORMAL_STRONG, 13 DETERMINISTIC_STRONG, 0 SEMANTIC_CHECKER, 4 CHECKER_GAP**. Há **9 IDs com construção Lean existente**: os 6 classificados FORMAL_STRONG e os 3 de contagem classificados como gaps. Nos últimos três, a prova existente é da aritmética escrita, não da justificativa inteira. Todos os 23 têm algum produtor de fatos; “23/23 exercitados” não significa “23/23 suficientemente fortes para o novo contrato”.

## 3. Lean candidates

### 3.1. O que Lean já verifica

[P2Checks.observe][checker] só tenta Lean quando `use_lean` é verdadeiro e recebeu uma tupla formal. [check_real_record][real] reextrai a fonte, verifica identidade/atribuição, vincula domínio, proposição e contexto, gera `import Mathlib` e usa o ciclo [evaluate_student_proof][proof].

| obrigação | proposição atualmente construída / guardas | alcance real |
|---|---|---|
| `b.sum_formula` | `∀ x S : ℝ, 4*S=45+3*x → S=rhs_escrito`; RHS só em x, fórmula verificável e B1 verified | isolamento algébrico; `linarith`; não demonstra origem geométrica de B1 |
| `b.centers` | `∀ x S : ℤ, 1≤x → x≤9 → 4*S=45+3*x → (x=1 ∨ x=5 ∨ x=9)`; somente após base e conjunto exato | necessidade por `omega`; lista exata e existência são controles separados |
| `b.admissible_center` | `∃ S : ℤ, (1≤n ∧ n≤9) ∧ 4*S=45+3*n` | admissibilidade aritmética do n escrito; não realiza o desenho |
| `b.center_sums` | sob `4*S=45+3*x`, conjunção das três implicações centro→soma escritas | mantém valores errados; tentativa de refutação usa centros 1,5,9 |
| `b.sum_at_five` | `∀ S : ℤ, 4*S=60 → S=n_escrito` | controle individual |
| `c.pair_permutations`, `c.pair_orientations`, `c.total` | conjunção das igualdades adjacentes realmente escritas; há ≥2 partes, alvo entre os valores e todas renderizáveis | `norm_num`, com `Nat.factorial`, potência e casts em ℤ; não prova interpretação combinatória |
| `c.counting_product` | igualdades escritas, condicionadas à forma de produto cujo primeiro membro tem fatores24/16 | prova a aritmética do produto; sem igualdade, fica determinístico |

O renderer de álgebra restringe variáveis, potências pequenas e divisores constantes não nulos em ℝ; divisão em ℤ não é aceita nessa via. O renderer combinatório aceita literais, operações limitadas, fatoriais até12 e potência renderizável até12; não transforma um `/` não renderizável em prova. Um teorema que não foi construído/executado não pode ser contabilizado como FORMAL_VERIFIED.

### 3.2. Modelo compartilhado proposto — ainda inexistente

Usar um estado discreto com centro `x` e duas funções de extremos sobre quatro linhas rotuladas. Definir, **em implementação futura**, um predicado equivalente ao contrato atual: os nove valores são exatamente 1–9, sem repetição, e cada linha tem soma S. `ValidConfig` abaixo é apenas abreviação matemática neste documento, **não símbolo já existente no repositório**.

Essa formalização deve separar três objetos: (i) o estado transcrito, (ii) o predicado matemático sobre esse estado, (iii) o vínculo da transcrição à fonte do estudante. Lean pode provar (ii); não autentica pixels, autoria, confirmação humana ou se o aluno apresentou um passo.

### 3.3. Avaliação explícita de todas as famílias de claims

As linhas agrupam obrigações que compartilham a mesma proposição/infraestrutura; todas as 23 aparecem. “Custo” é estimativa qualitativa de implementação, não medição. Nenhum nome de novo checker ou lema é contrato aprovado.

| obrigações | proposição a verificar | inputs e hipóteses necessários | Mathlib / técnicas | custo | benefício e decisão |
|---|---|---|---|---|---|
| `a.pair_sum`, `a.line_sum` | para configuração válida com x=5, S=15 e extremos de cada linha somam10; ou igualdade aritmética literal do aluno | dígitos inteiros, soma45, quatro linhas iguais; valor/expressão realmente escrito | `import Mathlib`, `norm_num`, `omega`/`linarith` | baixo após o modelo | viável; D exato basta por entrada. Lema compartilhado evita simplesmente postular os alvos10/15 |
| `a.pairs`, `c.pairs` | lista contém quatro pares, externos sem repetição, soma de cada par igual a S−x | pares do aluno, centro5/9 e soma15/18, multiconjunto1–9 | listas/Finset, aritmética inteira e decisão finita | baixo–médio | viável, mas D atual já verifica essas invariantes; formalização opcional, sem comparar com ordem-modelo |
| `a.placement`, `a.complete_configuration` | `ValidConfig(d)` e centro5 | nove leituras confirmadas, linhas A–E etc., domínio e ausência de repetição | `Fin`, listas/Finset, decidibilidade, `norm_num` | médio | útil como certificado do estado; prioridade abaixo dos gaps. Não converter reconhecimento visual em teorema |
| `b.balance_relation` | `ValidConfig(d) → 4*S=45+3*x` | somar as quatro equações de linha; nove números somam45; centro aparece quatro vezes | soma finita, `ring`/`linarith`, `norm_num` | médio inicial; baixo por instância | alto valor como fundação reutilizável; hoje a relação é comparada com alvo, e sua origem é metadata |
| `b.sum_formula` | relação implica fórmula escrita; ou equivalência entre fórmula e relação | x,S reais; denominador4≠0; referência à premissa apropriada | `linarith`, `ring`/`field_simp` se necessário | baixo; já existe a implicação | manter a prova atual e o vínculo exato; não introduzir divisão inteira por acidente |
| `b.integral_sum` | soma de três dígitos inteiros é inteira; se S é modelado em ℝ, ∃z:ℤ, S=(z:ℝ) | termos inteiros da linha e definição de S; a afirmação do estudante continua necessária | ℤ, casts, fechamento de soma; `norm_num`/`simp` | baixo | fechar G1 com regra tipada determinística; um lema Lean de fechamento pode certificá-la. Não provar tautologicamente S inteiro apenas declarando S:ℤ sem justificar a representação |
| `b.modular_condition` | no domínio1–9, a condição escrita é equivalente a `(45+3*x)%4=0` / `x≡1 mod4` | AST afim, módulo positivo e domínio; condição realmente escrita | `%`/divisibilidade sobre ℤ, `omega`; enumeração finita verificável | baixo–médio | D atual enumera exatamente9 valores e basta. Lean útil para forma simbólica e vínculo com a relação, sem exigir mesma sintaxe |
| `b.centers` | necessidade e, se adotado certificado mais forte, equivalência aritmética: `(∃S:ℤ, 4*S=45+3*x) ↔ x∈{1,5,9}` sob domínio | domínio1–9; argumento do aluno; conjunto explícito exato; witnesses12/15/18 | `omega`, `norm_num`, conjuntos finitos | baixo–médio | fortalecer o alcance da prova existente. Equivalência aritmética ainda não substitui realizabilidade diagramática |
| `b.admissible_center` | existência de S inteiro para n escrito, e n no domínio | n literal, bound, relação | `omega`, witness explícito, `norm_num` | baixo; existente | manter como controle; zero ponto direto |
| `b.center_sums`, `b.sum_at_five` | as associações escritas seguem da relação, inclusive refutação de falsas | pares/valor do aluno e relação; em B4 exatamente três centros | `omega`, `norm_num` | baixo; existente | manter preservação do erro e contraexemplo real; não substituir lista falsa pela esperada |
| `b.realizable_1`, `b.realizable_5`, `b.realizable_9` | os pares/estado fornecidos dão testemunho de configuração válida | quatro pares externos exatos, centro e soma; escolha canônica de distribuição só como witness do engine | tipo finito de posições, construção explícita, Finset/listas | médio | viável e útil como suficiência formal; D exato já basta. Witness gerado não pode ser atribuído ao estudante como placement ausente |
| `c.max_center`, `c.max_sum` | toda configuração válida tem S≤18; x=9 atinge18; monotonicidade da fórmula no domínio | relação global, x≤9, witness válido de centro9 para atingimento | `omega`/`linarith` + witness discreto | médio após modelo | alto benefício para fundamentar “máximo”, mantendo o contrato de conclusão parcial da pauta. Não criar obrigação de o aluno repetir toda essa prova |
| `c.pair_permutations` | cardinalidade das bijeções dos quatro pares às quatro linhas =4!=24 | quatro objetos distintos, linhas rotuladas, um por linha; interpretação do claim selecionado | `Equiv.Perm (Fin 4)`, `Fintype.card`, fatoriais, ou enumeração certificada | médio | fecha G2; prova estrutural é mais forte que provar apenas4!=24 |
| `c.pair_orientations` | cardinalidade das funções de quatro pares a duas orientações =2^4=16 | extremos distintos e escolhas independentes, uma por par | `Fin 4 → Bool`, `Fintype.card`, potência | médio | fecha G3; evita tratar igualdade16=16 como argumento de independência |
| `c.total` | igualdade literal de total quando há cálculo; modelo global tem384 configurações no máximo | conclusão tipada; para certificado combinatório, modelo e bijeção abaixo | `norm_num` para aritmética; Fintype/cardinalidade para modelo | baixo aritmético / médio–alto estrutural | manter conclusão isolada de1 ponto. Certificado global não inventa os passos do estudante |
| `c.counting_product` | bijeção entre configurações válidas com centro9 e `Perm(Fin4) × (Fin4→Bool)`; cardinalidade24×16=384 | pares complementares únicos, linhas distintas, inversa de codificação, escolhas independentes; produto escrito do aluno | equivalências, cardinalidade de produto/função/permutação, `Fintype.card_congr`, `norm_num` | médio–alto, maior novo componente | fecha G4; provar injetividade/sobrejetividade evita sobrecontagem/omissão. Não dividir por simetrias que a pauta não identifica |

Dependências verificadas no projeto: `lean-toolchain` fixa Lean4.28.0; `lakefile.toml` pede Mathlib v4.28.0; `lake-manifest.json` fixa Mathlib no commit `8f9d9cff6bd728b17a24e163c9402775d9e6a365`. O wrapper atual importa `Mathlib` inteiro. Para futura modularização, os módulos de cardinalidade `Mathlib.Data.Fintype.Card`, `Mathlib.Data.Finset.Card` e infraestrutura de permutações existem na cópia local do repositório principal; `Fintype.card_congr` foi localizado nessa fonte. A compilação de imports/lemmas específicos do novo modelo ainda precisa de validação futura; nenhum novo teorema foi criado aqui.

No worktree P2, `.lake/packages/mathlib/Mathlib.lean` não foi encontrado durante a inspeção. Isso é **estado de infraestrutura não validado**, não um teste Lean FAIL. Não foi executado `lake build` nesta etapa documental.

## 4. Checker gaps

### 4.1. Os quatro CHECKER_GAP da matriz

| gap | obrigação / evidência da lacuna | alternativa Lean | alternativa determinística | alternativa semântica dedicada | recomendação |
|---|---|---|---|---|---|
| G1 | `b.integral_sum`: linha150 de `P2Checks.b` observa True para todo enum selecionado, sem predicado próprio | fechamento da soma de dígitos inteiros; se S real, witness inteiro vinculado à definição | checker explícito de domínio/sujeito: S é soma dos três números inteiros da linha, com fonte e premissas do problema registradas | julgar apenas se a prosa afirma integralidade do S correto; não provar a integralidade por opinião LLM | regra determinística tipada, idealmente apoiada no lema de domínio; baixa complexidade |
| G2 | `c.pair_permutations`: `counting` valida valor24/igualdade, mas não cardinalidade do espaço de distribuições | cardinalidade de permutações/bijeções entre quatro pares e quatro linhas | enumerar24 bijeções e validar correspondência e contexto de linhas distintas | checar suficiência da explicação verbal da distribuição, com contrato fechado, após validação matemática | certificado Lean estrutural + checker de pertinência/suficiência; preservar a regra de2 pontos |
| G3 | `c.pair_orientations`: valor16/potência não certifica quatro escolhas independentes | cardinalidade das funções `Fin4→Bool` | enumerar16 vetores binários e validar extremos distintos/independência | examinar se a explicação estabelece duas orientações por par e independência, sem substituir o cálculo | certificado Lean estrutural + ligação explícita ao claim; preservar2 pontos |
| G4 | `c.counting_product`: `two_count_factors` exige valores16/24 nos operandos; metadata afirma significado, sem prova de bijeção | bijeção completa e cardinalidade do produto | enumerar as384 codificações, verificar inversa/ausência de colisões e cobertura do espaço pertinente | avaliar apenas suficiência de prosa alternativa com especificação própria; não aceitar LLM como prova da contagem | Lean para bijeção, D para payload e pertinência; usar SEMANTIC_CHECKER só se um formato futuro realmente o exigir |

G2–G4 são gaps de **força e suficiência**, não ausência de verificação aritmética. `4!=24` e `2^4=16` são bons subclaims formais. Entretanto, `counting('pair_permutations',24)` também aceita um literal24 ou outra expressão fechada de valor24; `counting('pair_orientations',16)` faz o análogo. O código não discrimina argumento completo, resultado tipado isolado e cálculo alheio cuja saída coincida.

A política futura não deve transformar essa constatação em exigências novas de sintaxe ou de pré-crédito. Os casos de regressão e a separação FINAL_ANSWER/JUSTIFICATION devem orientar o contrato de suficiência antes de implementação. Se exigir uma justificativa adicional mudar a interpretação atualmente aceita de um caso, isso precisa ser explicitado como fortalecimento de contrato, não escondido como ajuste de parser; a pauta e seus pesos continuam congelados.

### 4.2. Gaps transversais, sem criar novas obrigações

| gap | estado real | ação recomendada para fase futura |
|---|---|---|
| T1 — autorização de rota | não há registro C1 P2 por obrigação; há checkers P2 legados e promoção híbrida genérica | inventariar rotas explícitas permitidas, checker/version/suficiência e bloqueio de crédito quando nenhum checker aplicável existir |
| T2 — estados formais | P2 usa verified/refuted/unverified/technical_error; não expõe todos os nove estados solicitados | adaptador com execução confirmada e motivo de não tentativa; não reaproveitar tier_for como se já fosse suficiente |
| T3 — contexto/proveniência formal | provas B2/B3 guardam refs de premissas em metadata; hipótese fixa pode vir do modelo do problema | distinguir premissa do problema de passo do aluno e testar integridade dos vínculos; evitar atribuir desenvolvimento ausente |
| T4 — diagramas em rotas híbridas textuais | `EvidenceReconciler.audit_trace` usa `r.source.raw_text.strip()`, mas StructuredSourceBinding tem raw_text=None | proteger/segregar o caminho estruturado antes de qualquer futura integração; risco estático de AttributeError quando houver registro diagramático e evidência textual selecionada; não reproduzido aqui |
| T5 — ligação imagem→estado | reconhecimento arbitrário lança NotImplementedError; confirmação é autoridade upstream | revisão/adapter de percepção separado, com desconhecidos preservados; fora da implementação de checkers matemáticos |
| T6 — identidade de certificados | diretório/hash/ref vincula o resultado; origin e status por si não bastam | preservar verificação de fingerprint, proposição, contexto, domínio, stdout/stderr, execução e refutação ao integrar P2 |

## 5. Riscos de crédito

### 5.1. Onde há e onde não há validação independente

A ponte primária exige fatos, fingerprints, refs, fonte atribuível, registro de verificação e coerência de `student_check` para Lean. Ela rejeita `semantic` como mecanismo de FactResult primário e limita os fatos estruturados a uma allowlist de10 IDs. É uma defesa real contra “claim extraído → pontos”. Porém, **a ponte não reavalia a força matemática do produtor que escreveu verified**; G1 e G2–G4 continuam passando por ela quando seus produtores retornam positivo.

[PautaEngine][engine] é deliberadamente puro: aceita decisões por obrigação, aplica origens/autoria/regras/limites, sem ler expressões ou chamar checkers. `supported` upstream não é reprovado matematicamente pelo engine. Isso é uma fronteira de confiança, não um defeito que deva ser corrigido colocando LLM ou Lean dentro da pauta.

| caso de risco | consequência observável no código | interpretação para CHECKER-FIRST |
|---|---|---|
| `integral_sum: integer` | enum→True; auxilia a habilitar2 pontos de `b.centers` quando há a outra base exigida | não há falso valor numérico inferido; falta tornar explícita a validação de domínio, em vez de confundi-la com reconhecimento |
| `pair_permutations: 24` ou expressão fechada equivalente | pode satisfazer a obrigação de2 pontos sem validar argumento de distribuição | número correto não é, sozinho, prova combinatória; reforçar suficiência sem inventar passo |
| `pair_orientations: 16` ou expressão equivalente | pode satisfazer2 pontos sem teste da interpretação das escolhas | mesmo risco para independência |
| `counting_product: 24*16=384` | pode satisfazer caminho direto de5 pontos; comportamento explicitamente conhecido em regressão | produto escrito é necessário e previsto pela pauta; o reforço é certificar o significado do produto, sem exigir crédito anterior de C1/C2 |
| B1 isolado | equivalência com `4*S=45+3*x` dá2; contexto “centro aparece4 vezes” é metadata | apropriado ao passo explícito da pauta, mas não anunciar prova Lean do balanço global; candidato ao lema estrutural |
| `total: 384` | pode dar1 de conclusão sem decomposição | **permitido**, não gap automático: FINAL_ANSWER e regra independente. `384` sem rótulo não inventa o objeto total |
| `max_center: 9` + `max_sum: 18` | dão o bloco de1 por valores corretos; não provam a desigualdade universal de máximo | conclusão parcial permitida; futuro certificado de maximalidade não deve criar requisito de prova do estudante ausente da pauta |
| diagrama C completo e balanceado com duplicatas | `configuration('c')` não exige result.valid para max_center/max_sum; ex.: centro9 e os quatro pares4,5 repetidos têm soma18, mas não usam1–9 | risco de a conclusão parcial parecer certificado global. c.pairs permanece refutado; não afirmar que tal desenho completo é válido. Caso futuro de teste/contexto, não execução nova |
| resultado formal sem igualdade submetida | entradas unitárias/guardas falhos permanecem no caminho D ou sem fato | nunca rotular como FORMAL_VERIFIED só por `use_lean=True` |

### 5.2. Rotas semânticas antigas

[EvidenceReconciler][reconciler], linhas145–151, promove `semantic_judgment=satisfied` com contexto válido a `SEMANTIC_SUPPORTED` quando a auditoria não resolveu a obrigação. Não exige FactResult, checker dedicado ou uma segunda decisão de suficiência nesse ramo. A [HybridEvidencePolicy][policy] aceita confiança high/medium/low; confiança menor pode pedir revisão, mas não é um bloqueio universal de pontos.

Isso afeta potencialmente qualquer obrigação pontuável não resolvida no modo híbrido autorizado. Não é o comportamento padrão do PautaEngine sem policy, nem do caminho primário `audit_tme`. `run_hybrid_shadow` calcula nota potencial com essa policy; ativação é explícita e separada. Nenhuma dessas rotas foi ativada aqui. O comportamento de promoção sem FactResult é inclusive testado em teste compartilhado; não deve ser importado silenciosamente como política de P2 CHECKER-FIRST.

[SemanticSufficiencyGate][sufficiency] é uma avaliação independente dos trechos selecionados: recebe requisitos sem pontos, evidência literal, contexto/revisões apenas para veto; não recebe a justificativa/confiança do primeiro avaliador. O gate valida IDs, contexto e consistência da resposta. Em [reconcile_sufficiency][suffexp], `sufficient` com vínculo/contexto válidos pode promover uma obrigação ainda não resolvida a suporte semântico. Auditoria supported/refuted e erro técnico têm precedência.

Essa independência melhora o gate antigo, mas **não cria um checker matemático dedicado por obrigação**. Não há allowlist de P2 que impeça usar a suficiência LLM para matemática que pode ser checada exatamente. Na política-alvo, um candidato sem representação adequada continua sem crédito automático até passar por checker autorizado; “duas avaliações LLM concordaram” não substitui um checker matemático disponível.

### 5.3. Política-alvo e estados epistêmicos

```text
claim com fonte, sujeito, domínio e contexto
  → checker explícito autorizado para a obrigação
  → status matemático + evidência de execução + artefato
  → sufficiency (o resultado cobre o papel pedagógico exigido?)
  → award (eligibilidade, conflitos, dependências e atribuição)
  → PautaEngine (somente regras/pontos existentes)

NO CHECKER → NO AUTOMATIC CREDIT
```

O futuro award de P2 pode reutilizar conceitos do C1, mas não existe hoje como implementação P2. Os estados abaixo são **contrato-alvo preservado**, não nomes que já estejam todos disponíveis no pipeline legado:

| status obrigatório | evidência necessária / significado | semântica atual e cuidado de integração |
|---|---|---|
| FORMAL_VERIFIED | proposição vinculada compilou, sem sorry, execução confirmada | `student_lean`, verified, compiled=True; ponte valida correspondência |
| FORMAL_REFUTED | a negação da MESMA proposição compilou | exige refutation_verified e arquivo da refutação; erro de compilação não basta |
| FORMAL_UNPROVED | prova tentada, nem proposição nem negação estabelecidas | unverified por unsolved goals/tática inconclusiva; não negar crédito por falsidade inventada |
| FORMAL_NOT_ATTEMPTED | Lean não foi executado: guarda, fonte, representação ou opção impediu | P2 não tem rótulo separado; precisa instrumentar motivo, sem promover fallback D a prova formal |
| FORMAL_ERROR | falha técnica: módulo, processo, timeout, unknown identifier, elaboração | technical_error; preservar stdout/stderr e incerteza de execução; não confundir com refutação |
| DETERMINISTIC_VERIFIED | regra exata independente confirmou o claim pertinente | verified via deterministic/canonical_equivalence; distinguir G1 até reforçá-lo |
| DETERMINISTIC_FAILED | checker não produziu suporte | conservar submotivo refuted versus unverified/unsupported; esse rótulo não deve apagar a diferença |
| SEMANTIC_SUPPORTED | checker semântico dedicado autorizado concluiu suficiência, com fonte e contexto | não aceitar automaticamente o rótulo homônimo do juiz global antigo |
| SEMANTIC_INSUFFICIENT | checker dedicado não sustenta a obrigação | não é refutação matemática; erro de provider requer anotação técnica separada |

O ciclo formal atual já separa provas inconclusivas de erros técnicos e só refuta com negação compilada. O reconciliador legado reduz casos a INDETERMINATE/TECHNICAL_ERROR e usa DETERMINISTIC_REFUTED; não implementa sozinho os nove estados. A ponte também agrega mecanismos mistos em `deterministic`; uma expansão deve conservar detalhes de cada verificação, evitando perder certificados formais na telemetria agregada.

No PautaEngine, `withhold` pode reter crédito desconhecido sem dizer que o claim é falso. Um erro técnico relevante pode deixar points_awarded/score indefinidos, preservando known_points. Não atribuir ao P2 o fechamento numérico específico já implementado no C1 P1.

## 6. Plano Lean-Strong P2

Ordem recomendada para uma próxima etapa, **não executada neste diagnóstico**:

1. **Fechar o contrato de autorização e evidência.** Registrar os23 IDs existentes, rotas permitidas, checker/version, suficiência e dependências da seção1. Impedir que promoção híbrida genérica seja a saída de um checker ausente. Preservar ausência de crédito sem validação, os nove estados e os limites de cada prova. Nenhuma nova obrigação/peso.
2. **Resolver G1 e separar interpretação de validação.** Checker tipado de integralidade ligado à soma de inteiros e ao sujeito S. Conservar as duas bases de B3 e os papéis FACT/JUSTIFICATION, sem exigir que o aluno demonstre fatos elementares que o contrato aceita como afirmação.
3. **Formalizar a fundação discreta reutilizável.** Estado finito rotulado, uso exato1–9 e somas iguais; provar soma45 e balanço4S=45+3x. Implementar equivalência entre o validador determinístico do estado e o predicado formal apenas quando isso trouxer benefício mensurável. Nunca formalizar pixels.
4. **Consolidar B e máximo de C.** Preservar B2/B4 e controles já existentes; fortalecer necessidade/completude aritmética de B3; testemunhos de realizabilidade separados; provar limite S≤18 e atingimento. Respeitar crédito parcial independente previsto na pauta.
5. **Fechar G2, G3 e G4.** Certificados estruturais de24 distribuições,16 orientações e bijeção dos384 estados. Checker de pertinência/suficiência liga o que foi escrito ao objeto contado. Mantenha aritmética literal, inclusive valores errados, no checker Lean atual; não substitua igualdade errada por constante correta.
6. **Validar fronteiras e regressões antes de qualquer extractor P2.** Entradas tipadas e diagramas confirmados; mutações de premissas, argumentos ausentes, contagens alheias verdadeiras, conflitos, estados epistêmicos e preservação da pauta. Depois, em tarefa própria, preparar Mathlib neste worktree e executar provas reais com recibos completos.

Critérios para concluir essa fase futura: matriz sem gap de força não tratado; cobertura negativa por obrigação/papel; nenhuma promoção sem checker; casos de conclusão parcial preservados; prova Lean vinculada ao claim exato e às hipóteses corretas; status de execução/refutação verificáveis; nenhum ajuste de pauta para acomodar falhas. Implementar SemanticExtractor P2 permanece fora desta fase.

## 7. Testes existentes

### 7.1. Evidência disponível nesta revisão

O arquivo [test_tme2_p2_pauta_bridge.py][tests] contém **23 funções de teste**, equivalentes a **125 instâncias parametrizadas** pela contagem estática das listas atuais. A fixture de regressão P2 contém55 casos: a=22, b=17, c=16. Seus textos/contratos foram inspecionados para compreender a cobertura; não houve replay nem uso de resultados externos como oracle.

| teste / grupo existente | cobertura lida no código | limite para esta fase |
|---|---|---|
| `test_controlled_cases_and_full_source_chain` |55 casos, pontos, FactResult, fingerprints, fonte/offsets, verificação diagramática | usa use_lean=False; não é prova de integração Lean real |
| `test_full_problem_with_both_modalities_and_counting_paths` |9 combinações texto/diagrama e contagem alternativa; total20 | valida caminhos conhecidos, não suficiência geral da contagem |
| `test_all_384_labelled_balanced_configurations_are_accepted` |3 centros;4!×2^4 configurações/centro,1152 no total | enumera construções válidas; não prova que todo estado válido está nessa enumeração |
| métricas, dados inválidos, posição ausente | repetição, soma errada, centro errado, tipos estritos, desconhecidos | não há controle equivalente explícito de máximo de C sobre diagrama balanceado duplicado |
| proveniência/forma estruturada | fonte confirmada, regiões/confiança, mutações, proibição de relabel Lean, separação P1/P2 | não autentica pixels ou autoria; reconhecimento de imagem é deliberadamente ausente |
| `test_nonasserted_text_never_receives_credit` |12 contextos/item: negação, hipótese, abandono, citação | gramática controlada; não mede robustez linguística irrestrita |
| fatoriais/renderização/produtos | fatoriais/potências suportados, rejeição de gramática perigosa,4 produtos equivalentes e3 produtos inadequados | não há certificado combinatório das funções/permutação/bijeção |
| `test_completeness_and_hypothesis_gates_are_not_overridden_by_true_formal_implications` | conjunto de centros com extra, lista isolada e S=S; preserva guardas | monkeypatch do checker; não valida Lean/Mathlib reais |
| `test_factorial_formal_binding_and_failure_semantics` |4 estados; expressão escrita, Nat.factorial/domínio, mutação de payload, erro técnico | runner Lean simulado; até verified artificial serve para testar transporte, não verdade matemática |
| `test_digital_projection_mutation_is_rejected` | detecta mudança da fonte/projeção | não substitui testes de todas as premissas compartilhadas |
| `test_registry_all_obligations_and_native_diagram_projection` | exige algum supported para cada um dos23 IDs e limites de projeção | cobertura positiva por ID não certifica força do checker |
| `test_p2_diagram_and_missing_diagram` em integração aceita | desenho confirmado versus pares sem placement; identidade/proveniência | integração offline, não leitura visual nem nova prova formal |
| testes compartilhados de PautaEngine | origens, autoria, conflitos/estados, any/all/max_of, limites, erros técnicos | motor pontua estados; não valida a matemática de P2 |
| testes compartilhados de SemanticSufficiencyGate, catálogo e reconciliador | requisitos fechados para P2, IDs, contexto, independência, precedência e falha de provider | não equivalem a checker matemático dedicado de P2; exemplos de promoção usam outros problemas |
| `test_student_proof_semantics` | separação de falha, timeout e negação compilada; controles reais de aritmética compartilhada | não constitui suíte Lean real específica de P2 |
| testes C1 P1 | guardas explicitamente rejeitam TME2026P2 | confirma que o C1 atual ainda não é entry point de P2 |

A [auditoria histórica P2][history] relata55/55 casos,125 testes P2,1152 configurações e26 proposições Lean distintas (19 verificadas,7 refutadas), com um episódio anterior inconclusivo preservado. Isso é **evidência documental histórica**, não uma execução certificada por esta tarefa. O arquivo de resultados citado por ela, `artifacts/evaluations/tme2_p2_pauta_bridge/validation_summary.json`, não está presente neste novo worktree. Não se transferiu ou reexecutou esse replay.

`test_sufficiency_dev_regressions.py` depende de artefatos DEV previamente congelados e pula a checagem live quando faltam; portanto mera presença dessa suíte não prova execução de um gate independente neste worktree. Esses artefatos não foram acessados.

### 7.2. Lacunas de teste para implementação futura

- Por cada gap G1–G4: caso positivo, ausência, fonte/objeto incorreto, argumento insuficiente, verdade aritmética irrelevante e conflito explícito. Distinguir expressão válida de demonstração de contagem.
- B2/B3/B4: proposição exata, domínio real/inteiro, premissa do problema versus premissa apresentada, conjuntos extras/omitidos, testemunhos e refs adulteradas. Prova de necessidade não paga automaticamente realizabilidade.
- Contagem: linhas rotuladas, extremos distintos, bijeção e inversa, nenhum estado duplicado/omitido; comparação com enumeração independente do espaço finito. Não limitar completude ao gerador de casos positivos.
- C máximo: conclusão tipada preservada, contraditórios/duplicatas em desenhos e distinção entre valor correto parcial e configuração válida. Não penalizar simplesmente ausência de demonstração quando a pauta aceita conclusão.
- Cada uma das9 obrigações com construção Lean: verified real, negação real, prova inconclusiva e erro técnico; casos sem tentativa e fallback D devem ser observáveis separadamente. Os guardas precisam impedir provar enunciado enfraquecido no lugar do claim.
- Rotas: `NO CHECKER → NO AUTOMATIC CREDIT` com juiz/suficiência hostis; sem promover genericamente matemática representável por LLM; diagrama confirmado nunca usa offsets textuais fictícios.
- Reuso entre itens: distinguir permissões de contexto do gate, dependências de checker e regras de pontuação. A sequência da apresentação não pode virar dependência pedagógica artificial.

Nenhum desses testes foi criado ou executado agora. Não há resultado PASS/FAIL novo a reportar.

## 8. Veredito

**CHECKER_STRENGTHENING_REQUIRED.**

P2 tem base matemática operacional desenhada e cobertura nominal de todos os IDs; não requer reconstrução integral nem LLM genérico para preencher lacunas matemáticas. O trabalho necessário se concentra na integralidade tipada, na interpretação/validação estrutural da contagem, no controle das rotas semânticas antigas e na preservação explícita dos estados formais. O balanço global, a maximalidade e a bijeção de contagem são os candidatos de maior valor a Lean-Strong; listas e configurações discretas já têm bons verificadores determinísticos e não precisam virar Lean por obrigação.

Este veredito não certifica infraestrutura ou desempenho novo. As tabelas documentam o SHA inspecionado, capacidades existentes, riscos estáticos e propostas; nenhuma proposta foi tratada como implementação disponível.

### Integridade e estado final

Somente este arquivo diagnóstico foi adicionado. Nenhuma mudança em código, pauta, registry, prompts, checkers, testes, fixtures ou pipeline; nenhuma chamada LLM, acesso a gold/holdout ou expansão funcional para outro problema. Nenhum commit.

```text
git rev-parse HEAD
34732d445ff1e885a7156278ad4bb81c1fed25b2

git status --short
?? docs/audits/TME_P2_CHECKER_FIRST_DIAGNOSTICO_01.md
```

Hashes SHA-256 dos principais contratos inspecionados, para comparação em etapa futura:

| arquivo | SHA-256 |
|---|---|
| `examples/pautas/tme2_problem2.v1.json` | `694886b93c81f18942148adda2d9340d1054309c65f215ca1edaeff949f89c54` |
| `lean/student_claim_checkers/tme2_p2.py` | `d3624f15b5cbdecf13260fecd37139561b373c572f7f76a6d09360af3218a369` |
| `rubric/pauta/tme2_p2.py` | `9f18b1858eae84cdaa0d9871ba5bd538d4a7e13c693c9048b47772748160e6d2` |
| `student_claims/tme2_p2_digital.py` | `42edb42f46bae4aeabf82977cac02798b7e529a2cafb97fbf5cb1e694b67c493` |
| `tme/p2_diagram.py` | `e321155ee3af76d3e03771b8bcd61372e14c3551cb19525be332b06962a6c467` |
| `tme/hybrid_grader.py` | `8f0f5736bb9a844fccee08f0c77a9c9102fa2d8a281545ef43fa7dc3b4392f6d` |
| `student_claims/semantic_sufficiency.py` | `085c43aba0a151f4658c2e9653dbe38c6c062480ae4dc5ce0837917e1e667743` |
| `rubric/pauta/engine.py` | `ebf5449a12bc729685baf7227282132434370578a4abf0f0d071c29193ac07c6` |
| `tests/test_tme2_p2_pauta_bridge.py` | `089552658640f3befa4ebd5fb45c8c63d5ba683ae51ea92315f700ba53fedae5` |

Os caminhos abreviados de módulos nesta tabela são relativos a `app/confia_lean_auditor/`; links completos para navegação estão nas referências abaixo.

[pauta]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/examples/pautas/tme2_problem2.v1.json
[registry]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/tme/registry.py:18
[orchestration]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/rubric/pauta/tme2_p2.py:45
[accepted]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/tme/accepted_audit.py:95
[collector]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/student_claims/tme2_p2_digital.py
[digital]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/student_claims/digital_items.py:18
[named]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/student_claims/named_math.py:26
[legacy]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/student_claims/semantic.py:419
[catalog]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/student_claims/obligation_catalog.py
[requirements]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/student_claims/sufficiency_requirements.py:26
[checker]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/lean/student_claim_checkers/tme2_p2.py:48
[diagram]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/tme/p2_diagram.py:52
[real]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/lean/student_claim_checkers/real_algebra.py:48
[proof]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/lean/student_proof.py:44
[engine]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/rubric/pauta/engine.py:37
[reconciler]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/tme/hybrid_grader.py:115
[policy]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/rubric/pauta/evidence_policy.py:9
[sufficiency]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/student_claims/semantic_sufficiency.py:107
[suffexp]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/tme/sufficiency_experiment.py:31
[c1registry]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/app/confia_lean_auditor/experimental/tme_semantic_formal/obligation_registry.py:68
[tests]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/tests/test_tme2_p2_pauta_bridge.py:34
[history]: /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2/docs/audits/TME2_P2_PAUTA_BRIDGE.md
