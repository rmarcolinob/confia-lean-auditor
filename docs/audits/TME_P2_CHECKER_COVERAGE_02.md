# TME P2 — Checker Coverage Matrix 02

Data: 2026-11-05. Base: `34732d445ff1e885a7156278ad4bb81c1fed25b2`. Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2`.

**Cobertura do entry point opt-in `audit_p2_checker_first`: 6 FORMAL_STRONG, 14 DETERMINISTIC_STRONG, 3 COMPOSITE_STRONG, 0 SEMANTIC_CHECKER e 0 CHECKER_GAP.** Versão: `p2-checker-first.v1`. O contrato cobre as representações tipadas atuais de P2 e diagramas confirmados. Não afirma cobertura de prosa livre, OCR ou de um futuro SemanticExtractor.

`TME_CURRENT` permanece intacto, inclusive os limites registrados no [diagnóstico 01](TME_P2_CHECKER_FIRST_DIAGNOSTICO_01.md). A cobertura nova não deve ser atribuída ao caminho legado. A nova entrada é explícita, não está instalada no registry global nem na interface de transcrição aceita. Isso permite validar o substrato sem alterar a execução de referência.

## Contrato e legenda

A pauta continua `examples/pautas/tme2_problem2.v1.json`, máximo 20 (a=5, b=7, c=8). Há 23 IDs, 19 diretamente usados pelas regras pontuáveis e quatro auxiliares. Nenhum peso, regra `max_of`/`all_of`/`any_of`, dependência da pauta ou checker das 19 obrigações anteriores foi modificado.

- **N/kind**: claim type `math_named_quantity`, canonical family `named_quantity`, com `value_kind=kind`, subject exato da obrigação e item correto. O coletor, a seleção por atribuição e a revalidação da fonte são os existentes.
- **Dg**: `diagram_state` com vínculo estruturado, `confirmed=True`, `origin=student`. Reconhecimento de imagem não é implícito.
- **D**: verificação determinística exata. **L**: ciclo Lean real via `check_real_record`, somente com `use_lean=True` e proposição renderizável sob as guardas existentes. Classificação FORMAL_STRONG não significa que toda execução chamou Lean.
- **C**: checker composto; D verifica objetos/argumento e D ou L verifica a aritmética escrita. O resultado composto é `deterministic`, com a origem de cada componente registrada. Não é uma prova Lean de toda a justificativa.
- Condições comuns: fonte atribuível e grounded; forma tipada aceita; fato verificado; bridge valida proveniência e reconcilia evidências; somente evidência `supported` participa da pauta. Ausência, erro técnico e argumento insuficiente não viram crédito por confiança de LLM.

## Matriz completa

| obligation_id | rubric_item | claim types | checker primário | checker secundário | rota | status da cobertura | condição para crédito | dependências pedagógicas | subclaims necessários | risco de representação |
|---|---|---|---|---|---|---|---|---|---|---|
| `a.pair_sum` | a | N/math, N/integer_pairs, N/integer_mapping, Dg | `P2Checks.value`, `pair_facts`, `configuration` | racional exato / `inspect_pairs` | D | DETERMINISTIC_STRONG | soma dos extremos 10; compartilha 1 ponto com line_sum | nenhuma etapa pré-creditada | centro 5; soma de cada par escrito ou valor tipado | quatro pares que somam 10 não provam uso único dos dígitos; não concedem pairs automaticamente |
| `a.line_sum` | a | N/math | `P2Checks.value` | `rational_value` | D | DETERMINISTIC_STRONG | soma comum 15; mesmo bloco de 1 | nenhuma | valor de S no caso centro 5 | expressão genérica sem subject não é evidência desta obrigação |
| `a.pairs` | a | N/integer_pairs, N/integer_mapping, Dg | `P2Checks.pair_facts` / `configuration` | `inspect_pairs` | D | DETERMINISTIC_STRONG | quatro pares, externos exatos, soma de linha 15; 2 pontos | nenhuma colocação exigida para enumeração | dígitos 1–9 uma vez com centro 5; quatro somas iguais | pares sem posições não provam placement; orientação/ordem irrelevantes |
| `a.placement` | a | N/integer_mapping, Dg | `P2Checks.configuration` | `inspect_diagram` | D | DETERMINISTIC_STRONG | preenchimento completo válido com centro 5; 2 no caminho parcial | posições explicitadas/confirmadas | nove dígitos exatos; quatro linhas rotuladas; soma igual | parser textual e confirmação limitam a cobertura; desconhecido não é falso |
| `a.complete_configuration` | a | N/integer_mapping, Dg | `P2Checks.configuration` | `inspect_diagram` | D | DETERMINISTIC_STRONG | mesmo estado completo válido; caminho alternativo de 5 | não exige explicação textual | domínio, unicidade e linhas do diagrama | não tratar lista de pares como preenchimento; max_of evita acumular caminhos |
| `b.balance_relation` | b | N/relation | `P2Checks.b` / `compare` | equivalência canônica | D | DETERMINISTIC_STRONG | relação equivalente a 4S=45+3x; 2 | nenhuma | soma dos nove dígitos 45; centro contado quatro vezes | origem geométrica é contexto do problema; não é prova formal de toda a configuração |
| `b.sum_formula` | b | N/math | `P2Checks.b` | `compare` / `check_real_record` | D; L com B1 verificado | FORMAL_STRONG | S=(45+3x)/4 equivalente; 1 | B1 para Lean; não é requisito do ponto determinístico | RHS somente em x; isolamento real da relação | S=S não é fórmula; não trocar divisão real por inteira |
| `b.integral_sum` | b | N/enum | **`check_integrality`**, via `StrongP2Checks.observe` | schema `IntegralInput`; racional exato / fechamento inteiro | D | **DETERMINISTIC_STRONG** | afirmação tipada de S inteiro + domínio e fechamento verificados; 0 direto | pode habilitar centers com relação/fórmula | S=left+center+right; três dígitos inteiros; soma em Z | nomes simbólicos vêm do domínio do problema, não são extraídos da prosa; enum sozinho não é o checker |
| `b.modular_condition` | b | N/congruence | `P2Checks.b` / `modular_candidates` | enumeração do domínio 1–9 | D | DETERMINISTIC_STRONG | conjunto de soluções exato {1,5,9}; 0 direto | base alternativa para centers | congruência afim; módulo válido; equivalência no domínio | não generalizar equivalência finita para todos os inteiros |
| `b.centers` | b | N/integer_set | `P2Checks.b` | conjunto exato + `check_real_record` | D; L após base verificada | FORMAL_STRONG | {1,5,9} e base justificada; 2 | modular OU integral_sum e balance_relation/sum_formula verificados | necessidade aritmética; lista completa; base explícita | Lean atual prova necessidade; existência espacial permanece separada |
| `b.admissible_center` | b | N/math | `P2Checks.b` | pertinência / existência ou refutação Lean | D/L | FORMAL_STRONG | centro n satisfaz ∃S inteiro, 1≤n≤9, 4S=45+3n; 0 direto | nenhuma lista pré-creditada | limite e admissibilidade de n | um centro não prova lista completa nem desenho realizável |
| `b.center_sums` | b | N/integer_pairs | `P2Checks.b` | comparação exata / três implicações Lean | D; L com três centros 1,5,9 | FORMAL_STRONG | exatamente (1,12),(5,15),(9,18); 1 | não exige B1 creditado | relação implica cada soma para seu centro | ordem dentro do par importa; ordem dos três pares não; lista não é realização |
| `b.sum_at_five` | b | N/math | `P2Checks.b` | valor exato / implicação Lean | D/L | FORMAL_STRONG | 4S=60 implica S=15; 0 direto | nenhuma | associação do valor ao centro 5 | numeral sem subject não é associação |
| `b.realizable_1` | b | N/integer_pairs, Dg | `P2Checks.b` / `configuration` | `inspect_pairs` / `inspect_diagram` | D | DETERMINISTIC_STRONG | pares/estado válidos, centro 1, soma 12 | os três realizable juntos dão 1 ponto | testemunho com todos os dígitos e quatro linhas | admissibilidade aritmética sozinha não prova existência espacial |
| `b.realizable_5` | b | N/integer_pairs, Dg | `P2Checks.b` / `configuration` | `inspect_pairs` / `inspect_diagram` | D | DETERMINISTIC_STRONG | pares/estado válidos, centro 5, soma 15 | mesmo bloco; não importa a silenciosamente | testemunho construtivo explícito em b | não presumir reuso de a sem vínculo aceito |
| `b.realizable_9` | b | N/integer_pairs, Dg | `P2Checks.b` / `configuration` | `inspect_pairs` / `inspect_diagram` | D | DETERMINISTIC_STRONG | pares/estado válidos, centro 9, soma 18 | mesmo bloco; sem fração por um só testemunho | externos exatos e quatro somas | repetição de dígito invalida testemunho, mesmo com somas corretas |
| `c.max_center` | c | N/math, Dg | `P2Checks.value` / `configuration` | racional exato / métricas do diagrama | D | DETERMINISTIC_STRONG | valor 9; junto com max_sum dá 1 | sem pré-crédito de b | conclusão sobre centro máximo | mantém contrato de conclusão; não prova monotonicidade; ramo de diagrama não exige valid global |
| `c.max_sum` | c | N/math, Dg | `P2Checks.value` / `configuration` | racional exato / soma comum | D | DETERMINISTIC_STRONG | valor 18; mesmo bloco de 1 | junto com max_center | conclusão sobre soma máxima | soma 18 isolada não certifica todo o desenho nem a contagem |
| `c.pairs` | c | N/integer_pairs, Dg | `P2Checks.pair_facts` / `configuration` | `inspect_pairs` | D | DETERMINISTIC_STRONG | (1,8),(2,7),(3,6),(4,5), ordem livre; 2 | sem pré-crédito de maximum | oito externos exatos, soma 9 em cada par | enumeração correta não é argumento para contar disposições |
| `c.pair_permutations` | c | N/combinatorial_math | **família `P2CompositeCountingChecker` em `StrongP2Checks.observe`** | aritmética existente; `finite_certificate`; `argument_relation` | C = D + D/L | **COMPOSITE_STRONG** | aritmética correta + 24 bijeções verificadas + estrutura 4! ou fatores 4,3,2,1; 2 | não exige c.pairs pré-creditado | quatro pares distintos; quatro linhas distintas; permutações completas | literal 24 ou 24=24 é só resultado; equivalências fora da gramática podem ficar insuficientes |
| `c.pair_orientations` | c | N/combinatorial_math | **mesma família, ramo específico pair_orientations** | aritmética existente; `finite_certificate`; `argument_relation` | C = D + D/L | **COMPOSITE_STRONG** | aritmética correta + 16 vetores verificados + estrutura 2^4 ou quatro fatores 2; 2 | não exige distribuições pré-creditadas | extremos distintos; duas escolhas por cada um dos quatro pares; independência | literal 16 não justifica independência; prosa livre não é interpretada |
| `c.total` | c | N/combinatorial_math | `P2Checks.counting` | racional exato / igualdade escrita Lean | D; L condicional | FORMAL_STRONG | total explicitamente tipado 384; 1 | nenhuma etapa prévia obrigatória | conclusão numérica; aritmética quando escrita | preservado FINAL_ANSWER: não promove o numeral a justificativa de 5 pontos |
| `c.counting_product` | c | N/combinatorial_math | **mesma família, ramo específico counting_product** | aritmética existente; enumeração independente/inversa; `argument_relation` | C = D + D/L | **COMPOSITE_STRONG** | produto explícito das etapas 24 e 16, aritmética e bijeção verificados; 5 | caminho direto independente; max_of com fatorado | A=permutações, B=orientações; injeção, sobrejeção, inversa; total 384 | 12*32=384 é aritmética correta sem relação suficiente; 24*16 é método tipado existente; não há quotient por simetrias |

## Escopo dos novos certificados

Integralidade: o adaptador vincula o `integral_sum` do item b à soma de três dígitos inteiros da linha de P2. O checker faz validação estrita do envelope e do domínio, conserva os termos e verifica fechamento exato. No contrato concreto de teste, um termo fora de 1–9 reprova a conjunção **domínio + integralidade** mesmo quando a soma é inteira; isso é identificado por `non_digit_term`, não falsamente por `nonintegral_sum`. Termos desconhecidos/incompletos não são refutação.

Combinatória: o certificado deriva centro 9 e soma 18 dos candidatos inteiros do problema, constrói quatro pares complementares, enumera 24 permutações e 16 orientações, verifica ausência de colisão, e compara o resultado com a enumeração independente dos 8! estados externos. A inversa é reconstruída a partir dos extremos, não consultada no gerador. Resultado: 384 estados, com linhas rotuladas. O certificado registra origem no problema e hash do conjunto; não inventa source_span do aluno.

A suficiência escrita é separada: fatoriais/fatores para distribuições, quatro escolhas binárias para orientações e produto dos dois estágios para método direto. O último mantém `24*16` e `16*24`, já admitidos pela pauta/casos existentes; não exige os dois argumentos isolados previamente creditados. Um número correto com rótulo irrelevante, fonte hipotética, negação, citação ou tentativa descartada não fornece esse vínculo.

## Política de crédito e evidência

```text
fonte tipada atribuível
  → checker matemático por obrigação
  → componentes e status epistemológicos
  → suficiência estrutural do argumento (quando JUSTIFICATION)
  → FactResult e bridge existente (atribuição, conflitos, supported)
  → PautaEngine existente
```

`FORMAL_REFUTED` ou `DETERMINISTIC_FAILED` com `mathematical_refutation=True` impede aceitação. Falha de reconhecimento do argumento tem `mathematical_refutation=False`: é insuficiência, não falsidade. `FORMAL_UNPROVED`, `FORMAL_NOT_ATTEMPTED` e `FORMAL_ERROR` permanecem distintos. Uma rota D positiva pode sustentar crédito sem tentativa Lean, mas nunca se apresenta como FORMAL_VERIFIED.

Não há checker semântico nestes quatro IDs: são decidíveis exatamente no contrato adotado. `semantic_decision` no combinador é apenas entrada adversarial/compatibilidade ignorada, testada contra sobreposição; não chama modelo nem confere autoridade. `SEMANTIC_SUPPORTED`/`SEMANTIC_INSUFFICIENT` não são sintetizados como prova matemática. A expansão para prosa exige contrato próprio e fica fora desta entrega.

## Referências e validação

Implementação: [engine.py](../../app/confia_lean_auditor/experimental/tme_p2_checker_first/engine.py), [components.py](../../app/confia_lean_auditor/experimental/tme_p2_checker_first/components.py), [registry.py](../../app/confia_lean_auditor/experimental/tme_p2_checker_first/registry.py). A registry nova apenas declara cobertura; não troca o roteamento global.

Contratos preservados: [P2Checks](../../app/confia_lean_auditor/lean/student_claim_checkers/tme2_p2.py), [coletor P2](../../app/confia_lean_auditor/student_claims/tme2_p2_digital.py), [bridge P2](../../app/confia_lean_auditor/rubric/pauta/tme2_p2.py), [pauta](../../examples/pautas/tme2_problem2.v1.json).

Testes e recibos de Lean real, preservação dos 55 casos existentes e estado Git: [relatório de fortalecimento](TME_P2_CHECKER_STRENGTHENING_01.md).
