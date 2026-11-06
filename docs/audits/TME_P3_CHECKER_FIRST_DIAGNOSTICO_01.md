# TME P3 — Checker-First / Lean-Strong Diagnostic 01

Data: 2026-11-05. Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3`. Branch: `experiment/tme-semantic-formal-p3`. SHA congelado: **`1165dbf62f854d6d40c0cc5f2bb6fcb02ca381e9`**.

**Veredito: CHECKER_STRENGTHENING_REQUIRED.** Há produtores para as 13 obrigações e um modelo finito real da máquina. Não falta a infraestrutura matemática central. O principal déficit é separar verdade do valor, relação argumentativa e suficiência em três parcelas de (b), além de corrigir futuramente limites de representação/epistemologia. Nenhum Semantic Formal P3 foi implementado nesta tarefa.

A validação termina com **176 testes pytest distintos aprovados**, **25/25 casos existentes aprovados no replay** e Lean real em cinco IDs de obrigação. Os três erros iniciais de pytest eram permissão de escrita de artefatos; foram reexecutados sem alteração de código/expectativas. Não foram usados gold externo, holdout ou chamadas a modelos.

## 1. Fontes, estado inicial e alcance

Estado inicial: `git status --short` vazio; HEAD/branch acima. A referência pedagógica é a pauta fornecida pelo usuário nesta solicitação. O contrato operacional é o JSON versionado; onde ele não explicita a mesma condição pedagógica, a divergência é registrada, não resolvida por opinião externa.

| fonte | função |
| --- | --- |
| [problem.json](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/problems/TME2026P3/problem.json) | Enunciado, regra uniforme a cada acionamento, figura/alt e proveniência; páginas 7–8 do documento de referência. |
| [figura local](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/static/problem-assets/TME2026P3/compartimentos.png) | Inspecionada visualmente nesta tarefa; compatível com as pilhas codificadas. |
| [estado da máquina](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/examples/pautas/tme2_problem3.machine.v1.json) | Pilhas imutáveis bottom-first; origem registrada como confirmação do usuário em 2026-10-31. |
| [pauta operacional](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/examples/pautas/tme2_problem3.v1.json) | 13 IDs; 4+8+8 pontos; all_of/additive/max_of. |
| [auditoria histórica](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME2_P3_PAUTA_BRIDGE.md) | Histórico da transcrição, confirmação do estado e criação da ponte. Não substitui inspeção do código atual. |

O relatório histórico dizia que a figura não estava disponível naquele momento e que o PDF retornara 403. **Na base atual a figura local e seu alt existem**. O catálogo registra o SHA do PDF de origem, mas não se afirma ter baixado/reinspecionado esse PDF nesta tarefa. Nenhuma cor foi inventada para obter as respostas. A referência de solução local não foi usada como gold de respostas de alunos.

## 2. Arquitetura real

```text
texto separado por item a/b/c
→ collect_tme2_p3_digital / collect_digital_items
→ MathClaimRecord nativo/genérico, canonicalização, spans e atribuição
→ verify_tme2_p3_digital: reconstrói a extração e valida identidade
→ P3Checks._a/_b/_c + P3Machine + aritmética exata
→ numerical → check_rational_record → evaluate_student_proof → lake env lean (quando elegível)
→ FactResultsBuilder: FactResult + VerificationLink + fingerprints
→ bridge_tme2_p3 → bridge_facts: origem, fonte, vínculo formal e conflitos
→ PautaEvidence
→ PautaEngine: regras, dependências e limites
→ decisão e pontos
```

A regra da pauta não chama o checker. Ela consome evidência já validada. O mapa `TME2_P3_OBLIGATIONS` é identidade fact_id→obligation_id, não heurística de pontuação. O PautaEngine não interpreta texto nem executa Lean.

| componente real | responsabilidade / limite |
| --- | --- |
| [registry](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/tme/registry.py) | audit_tme registra TME2026P3, carrega pauta e machine asset; não é o catálogo ITA. |
| [primary_audit](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/tme/obligation_experiment.py) | Caminho baseline/TME_CURRENT com supplement_scope(deterministic_only). Impede suplemento LLM no caminho primário. |
| [collector P3](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/student_claims/tme2_p3_digital.py) | VOCABULARY de quantidades math, conjuntos e cores enum; literal_extractors + extração genérica. Não é SemanticExtractor P3. |
| [named_math](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/student_claims/named_math.py) | Gramática quantidade: representação, labels normalizados, binding literal. Não verifica a verdade. |
| [checker P3](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/lean/student_claim_checkers/tme2_p3.py) | Enumeração de estado, valor exato, estratégia e guardas de contexto matemático. |
| [bridge](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/rubric/pauta/bridge.py) | Rejeita fingerprint/fonte adulterados, ausência de atribuição, origem não habilitada e resultado formal não vinculado; conflito supported+refuted→indeterminate. |
| [PautaEngine](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/rubric/pauta/engine.py) | Pontuação pura, Decimal, unresolved_policy=withhold; technical_error não vira falsidade matemática. |

`digital_items` chama o mecanismo legado `supplement`, mas ele é substituído pelo scope determinístico em `primary_audit`; nos testes/replay a variável CONFIA_TME_SEMANTIC_ENABLED=0 também ficou explícita. Não existe nesta base pacote `experimental/tme_semantic_formal_p3`, registry Semantic Formal P3 ou AwardGate P3 novo. Não confundir o registry matemático existente com um adaptador ainda não implementado.

### Rotas semânticas antigas — separadas do Current

`tme/hybrid_grader.py::EvidenceReconciler` e `student_claims/semantic_sufficiency.py::SemanticSufficiencyGate` existem para experimentos gerais. O primeiro pode promover `SEMANTIC_SUPPORTED` quando não há auditoria resolvida e há julgamento contextual; `tme/sufficiency_experiment.py` acrescenta um segundo gate semântico e usa uma evidence_policy que aceita essa origem. **Essas rotas não participam de primary_audit nem do replay executado.** Copiá-las como autoridade positiva para P3 violaria o novo requisito NO CHECKER → NO AUTOMATIC CREDIT. Seus gates locais podem ser úteis como veto; parecer semântico não substitui a matemática do estado.

## 3. Obrigações reais, pauta e dependências

| regra | pontos | condição operacional |
| --- | --- | --- |
| a.count | 2 | a.bottom_white_count |
| a.probability | 2 | a.first_white_probability; independente da contagem |
| b.space | 2 | b.ordered_pairs |
| b.different | 2 | b.different_favorable |
| b.same | 2 | b.same_compartment |
| b.conclusion | 2 | b.second_white_probability; sem dependências das três etapas |
| b.alternative | 8 | b.alternative_complete; alternativa ao caminho de contagem |
| c.continue | 1 | c.continue_compartments |
| c.first_strategy | 2 | c.strategy_case_1 |
| c.second_strategy | 2 | c.strategy_case_2 |
| c.conditionals | 1 | all_of(conditional_success_1, conditional_success_2, strategy_case_1, strategy_case_2) |
| c.total | 2 | all_of(total_win_probability, continue_compartments, duas strategies, duas conditionals) |

Item a soma duas parcelas (máximo 4). Item b é **max_of** entre soma das quatro parcelas e método alternativo completo (máximo 8); anexar árvore não soma mais 8. Item c soma cinco parcelas (máximo 8). As duas obrigações condicionais compartilham **1 ponto conjunto**, não 1 ponto cada nem 0,5 automático. Total máximo 20.

As dependências dos produtores são adicionais às regras: cada conditional só é verificável quando estratégia+contagem do seu caso são corretas; total de c requer continuação, ambas as estratégias e ambas as condicionais válidas, além da forma de desenvolvimento aceita. Estratégias podem pontuar sem continuar; a fixture c_missing_continuation vale 5, não 8.

## 4. Estado finito da máquina

`P3Machine` valida seis pilhas, ao menos duas bolas por pilha, cores conhecidas e referência de fonte não vazia. Guarda todas as pilhas, mas sua API de transição é especializada em **duas retiradas**: after_first(i) devolve as seis cores inferiores após a primeira retirada, não um simulador de duração arbitrária.

| compartimento | pilha inferior→superior |
| --- | --- |
| 1 | branca, preta, branca, cinza, preta |
| 2 | branca, cinza, preta |
| 3 | cinza, preta |
| 4 | preta, preta |
| 5 | cinza, preta |
| 6 | preta, branca, cinza, preta |

| primeira escolha | cores inferiores após retirada | cores ótimas / contagem | empate |
| --- | --- | --- | --- |
| 1 | preta, branca, cinza, preta, cinza, preta | preta / 3 | False |
| 2 | branca, cinza, cinza, preta, cinza, preta | cinza / 3 | False |
| 3 | branca, branca, preta, preta, cinza, preta | preta / 3 | False |
| 4 | branca, branca, cinza, preta, cinza, preta | preta, cinza, branca / 2 | True |
| 5 | branca, branca, cinza, preta, preta, preta | preta / 3 | False |
| 6 | branca, branca, cinza, preta, cinza, branca | branca / 3 | False |

Inicialmente há branca em {1,2}. Depois do 1, preta ocorre 3 vezes; depois do 2, cinza ocorre 3 vezes. Esses dois ótimos são únicos. Há empate entre três cores após o compartimento 4, mas essa primeira bola é preta e o jogo já terminou; não muda a estratégia de c. Um controle sintético separado também confirmou detecção de empate, sem substituir o asset oficial.

A regra de seleção uniforme é premissa explícita do enunciado. O modelo usa exatamente seis escolhas e pesos Fraction(1,6). O fato uniform_ordered_pairs=True é metadado; não é uma prova Lean nem evidência de argumento escrito pelo estudante. Um certificado de medida explícito por evento é uma melhoria de auditabilidade, não um estado ausente.

### Enumeração independente executada

Um script diagnóstico temporário copiou as pilhas em memória, aplicou pop(0) e enumerou todos os 36 pares (i,j), confrontando as saídas com P3Machine. Os pares favoráveis à segunda branca foram (1,2), (2,1), (3,1), (3,2), (4,1), (4,2), (5,1), (5,2), (6,1), (6,2), (6,6): dez distintos e apenas o repetido (6,6). Cada evento tem peso 1/36 sob a regra do problema. Probabilidade = 11/36.

Os seis ramos condicionais para branca na segunda retirada são 1/6, 1/6, 1/3, 1/3, 1/3, 1/2. No jogo, só os ramos iniciais 1 e 2 continuam: (1/6)(3/6)+(1/6)(3/6)=1/6. O cálculo ótimo enumera todas as cores e não compara com respostas hardcoded preta/cinza. Certificado completo: `finite_certificate.json` nos artefatos. Não há gap de infraestrutura da figura/estado para este P3.

## 5. Checker Coverage Matrix — 13 obrigações

Classificação abaixo é da **obrigação completa no contrato digital tipado**, não da mera existência de um parser, de um nome de arquivo ou de um certificado aritmético. CHECKER_GAP pode significar lacuna de suficiência embora já exista um produtor de valor. COMPOSITE_STRONG descreve conjunções explícitas já implementadas; o P3 atual não emite um enum com esse nome.

| obligation_id | item | pontos | requisito pedagógico | checker atual | tipo | valida verdade matemática? | valida suficiência? | Lean candidate? | gap/limite? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a.bottom_white_count | a | 2 | Identificar as duas brancas inferiores | _a + bottom_colors.count | DETERMINISTIC_STRONG | Sim; deriva 2 das pilhas | Sim para contagem explicitamente atribuída; não exige listar bolas | Opcional: cardinalidade finita; baixo ganho | Não no contrato tipado |
| a.first_white_probability | a | 2 | Valor correto; isolado autorizado | numerical + Fraction(white,6) | DETERMINISTIC_STRONG | Sim, valor exato; igualdade pode ir ao Lean | Sim para resultado; não fornece a.count | Já executado 2/6=1/3; rota FORMAL forte para essa igualdade | Não; manter valor determinístico sem exigir Lean |
| b.ordered_pairs | b | 2 | 6×6 pares ordenados equiprováveis | _b + len(ordered_pairs) + value_status | CHECKER_GAP | Cardinalidade sim; uniformidade vem da premissa, flag não prova argumento | Não exige produto, pares explícitos ou relação de equiprobabilidade escrita | 6*6=36; card(Fin6×Fin6)=36 opcionais | Relação amostral/justificação não validada |
| b.different_favorable | b | 2 | Contagem 2×5 dos pares distintos | _b + second_white_pairs filtrado i≠j | CHECKER_GAP | Sim; enumera os dez eventos | Não exige vínculo escrito entre duas escolhas brancas e cinco primeiras escolhas | 2*5=10 como subcheck, não prova evento | Valor 10 rotulado/tautologia recebe 2 |
| b.same_compartment | b | 2 | Somente repetição do sexto é favorável | _b + asserted_set == diagonal branca | DETERMINISTIC_STRONG | Sim; deriva diagonal {6} das segundas bolas | Sim para exclusividade explicitamente afirmada pelo conjunto | Possível prova finita; enumeração é suficiente | Não no contrato de conjunto explícito |
| b.second_white_probability | b | 2 | Reunir casos e concluir 11/36 | numerical + len(white_pairs)/36 | CHECKER_GAP | Sim para valor/igualdade; evento vem do modelo | 11/36 isolado recebe 2 sem reunir casos | Já executado (10+1)/36=11/36 | Contrato de crédito isolado não explicitado na pauta pedagógica fornecida |
| b.alternative_complete | b | 8 alternativos | Árvore equivalente completa | seis ramo_i + weighted_sum_matches + total | COMPOSITE_STRONG | Sim; cada ramo comparado ao estado e pesos verificados | Sim no formato aceito; não basta palavra árvore | Aritmética do total já via b.second; árvore inteira não é Lean | Limites de representação e refuted para shape ausente; ver seção 9 |
| c.continue_compartments | c | 1 | Continuar apenas após branca do 1 ou 2 | asserted_set == continue_compartments | DETERMINISTIC_STRONG | Sim, branco inicial no estado | Sim para conjunto de continuação explicitamente atribuído | Possível finito; baixo benefício | Não no contrato tipado |
| c.strategy_case_1 | c | 2 | Caso 1: preta, três de seis, ótima | estrategia_1 × contagem_1 + best_choices(1) | COMPOSITE_STRONG | Sim; transição, contagem e máximo de cores calculados | Exige cor e número no caso 1; não exige que aluno escreva todo novo estado | Otimização finita preferível; Lean eventual certificado do modelo | Falta schema para estados intermediários do aluno, fora do domínio atual |
| c.strategy_case_2 | c | 2 | Caso 2: cinza, três de seis, ótima | estrategia_2 × contagem_2 + best_choices(2) | COMPOSITE_STRONG | Sim, sem lookup da cor esperada | Exige cor e número no caso 2 | Como caso 1 | Mesma limitação de representação |
| c.conditional_success_1 | c | 1 conjunto | Probabilidade 1/2 no caso 1 | strategy_valid[1] + numerical(maximum/6) | COMPOSITE_STRONG | Sim, condicionada à estratégia validada | Depende do caso correto; ponto exige também caso 2 | Já executado 3/6=1/2 | Não no formato aceito; valor sem estratégia não basta |
| c.conditional_success_2 | c | mesmo 1 | Probabilidade 1/2 no caso 2 | strategy_valid[2] + numerical(maximum/6) | COMPOSITE_STRONG | Sim | Mesmo all_of das duas condicionais/estratégias | Já executado 3/6=1/2 | Não no formato aceito |
| c.total_win_probability | c | 2 | Probabilidade global desde primeira retirada | contexto completo + weighted_sum/combined + numerical | COMPOSITE_STRONG | Sim; calcula ótimo global do modelo e verifica expressão | Sim no desenvolvimento admitido; 1/6 isolado não basta | Já executada soma dos dois ramos e produto combinado | Exige exatamente dois membros; limites algébricos podem subpontuar |

Síntese estrita: **4 DETERMINISTIC_STRONG, 6 COMPOSITE_STRONG, 3 CHECKER_GAP**, todos com produtores existentes. Os 3 gaps dizem respeito ao contrato pedagógico integral de b, não a ausência de comparação matemática. Não se marca FORMAL_STRONG como classificação primária de uma probabilidade completa só porque norm_num provou uma igualdade fechada; há **cinco IDs com rota Lean real**, descritos a seguir. Prosa livre, imagens de respostas e estados intermediários fora do schema não estão cobertos por esta contagem de força.

## 6. Lean real: infraestrutura, guardas e alcance

Lean confirmado: `Lean (version 4.28.0, arm64-apple-darwin24.6.0, commit 7e01a1bf5c70fc6167d49c345d3bf80596e9a79b, Release)`. Mathlib: v4.28.0, revisão **8f9d9cff6bd728b17a24e163c9402775d9e6a365**. Manifest SHA-256 `670c704b256c73ce48046b838bf9562b92bf128a2f0239f521e2f9ec404f6219`.

O worktree começou sem .lake. Um lake build iniciou clone de Mathlib; o download foi interrompido deliberadamente (exit 143), não por falha de prova. Para evitar download completo, foram comparados os bytes de lean-toolchain/lake-manifest com P2 e todas as revisões Git das dependências. Uma cópia independente por clone APFS de .lake/packages foi criada no P3; o clone parcial foi preservado em /private/tmp. **O lake build subsequente terminou com sucesso: 8038 jobs.** Nenhum manifest, toolchain ou arquivo de produção mudou.

`check_rational_record` renderiza aritmética fechada em **ℚ**, com casts explícitos e import Mathlib; norm_num é usado para prova e negação. A forma nativa rational evita encaminhar racionais ao checker legado de divisão inteira. Não usa Lean para parsing: o parser exato valida a entrada antes da proposição. Não há Statement.lean TME P3 no projeto; são teoremas temporários ligados ao claim realmente escrito, não prova de referência atribuída ao aluno.

Guardas efetivas: use_lean=True; igualdade com exatamente dois membros; lado esquerdo tem o valor esperado da obrigação; fonte atribuível e binding válido; renderer fechado suportado. O checker preserva operandos/resultados errados. Valor isolado, cadeia com três membros ou uma igualdade verdadeira sobre valor errado não é falsamente apresentada como prova formal da resposta. Falha técnica permanece técnica, sem fallback automático de prova para crédito de valor.

Em c, estratégia/contexto são verificados antes da aritmética. O Lean prova a igualdade escrita, não percebe a figura nem prova sozinho a estratégia ótima. A prova da negação é executada separadamente antes de classificar refutação.

| estado epistemológico normalizado neste relatório | ocorrência / interpretação |
| --- | --- |
| FORMAL_VERIFIED | 12 |
| FORMAL_REFUTED | 2 |
| FORMAL_UNPROVED | 0 |
| FORMAL_ERROR | 0 |
| FORMAL_NOT_ATTEMPTED | Valores isolados e guardas sem contexto; exemplificados por a_answer_only, b_answer_only, c_answer_only e c_arithmetic_without_strategy. Não é erro nem refutação. |

O P3 legado guarda status verified/refuted/unverified/technical_error e student_check opcional. A tabela normaliza esses recibos para a terminologia solicitada; não inventa novos status nativos. verified determinístico com student_check ausente continua determinístico, jamais FORMAL_VERIFIED. UNPROVED e ERROR não ocorreram nas execuções Lean reais desta tarefa; testes com mock não são usados para alegar que ocorreram.

| caso existente | obrigação | status formal | proposição realmente enviada ao Lean |
| --- | --- | --- | --- |
| a_complete | a.first_white_probability | FORMAL_VERIFIED | ((2 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (3 : ℚ)) |
| a_wrong_probability | a.first_white_probability | FORMAL_REFUTED | ((2 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (2 : ℚ)) |
| b_official | b.second_white_probability | FORMAL_VERIFIED | (((10 : ℚ) + (1 : ℚ)) / (36 : ℚ)) = ((11 : ℚ) / (36 : ℚ)) |
| b_tree | b.second_white_probability | FORMAL_VERIFIED | (((1 : ℚ) / (6 : ℚ)) * (((((((1 : ℚ) / (6 : ℚ)) + ((1 : ℚ) / (6 : ℚ))) + ((2 : ℚ) / (6 : ℚ))) + ((2 : ℚ) / (6 : ℚ))) + ((2 : ℚ) / (6 : ℚ))) + ((3 : ℚ) / (6 : ℚ)))) = ((11 : ℚ) / (36 : ℚ)) |
| c_complete | c.conditional_success_1 | FORMAL_VERIFIED | ((3 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (2 : ℚ)) |
| c_complete | c.conditional_success_2 | FORMAL_VERIFIED | ((3 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (2 : ℚ)) |
| c_complete | c.total_win_probability | FORMAL_VERIFIED | ((((1 : ℚ) / (6 : ℚ)) * ((1 : ℚ) / (2 : ℚ))) + (((1 : ℚ) / (6 : ℚ)) * ((1 : ℚ) / (2 : ℚ)))) = ((1 : ℚ) / (6 : ℚ)) |
| c_conditional_equivalent | c.conditional_success_1 | FORMAL_VERIFIED | ((2 : ℚ) / (4 : ℚ)) = ((1 : ℚ) / (2 : ℚ)) |
| c_conditional_equivalent | c.conditional_success_2 | FORMAL_VERIFIED | ((2 : ℚ) / (4 : ℚ)) = ((1 : ℚ) / (2 : ℚ)) |
| c_conditional_equivalent | c.total_win_probability | FORMAL_VERIFIED | (((2 : ℚ) / (6 : ℚ)) * ((3 : ℚ) / (6 : ℚ))) = ((1 : ℚ) / (6 : ℚ)) |
| c_wrong_second | c.conditional_success_1 | FORMAL_VERIFIED | ((3 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (2 : ℚ)) |
| c_wrong_total | c.conditional_success_1 | FORMAL_VERIFIED | ((3 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (2 : ℚ)) |
| c_wrong_total | c.conditional_success_2 | FORMAL_VERIFIED | ((3 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (2 : ℚ)) |
| c_wrong_total | c.total_win_probability | FORMAL_REFUTED | ((((1 : ℚ) / (6 : ℚ)) * ((1 : ℚ) / (2 : ℚ))) + (((1 : ℚ) / (6 : ℚ)) * ((1 : ℚ) / (2 : ℚ)))) = ((1 : ℚ) / (5 : ℚ)) |

stdout/stderr completos, compiled, refutation_verified, caminhos e proposições estão em `formal_receipts.json`. Provas positivas tiveram stdout/stderr vazios. Nas refutações, a tentativa positiva falhou com diagnóstico Lean; a negação compilou com sucesso. Não se concluiu falsidade apenas a partir de unsolved goals.

## 7. Candidatos Lean-Strong: utilidade e custo

| claim | inputs / hipóteses | rota atual | candidato e benefício |
| --- | --- | --- | --- |
| 2/6=1/3 | Expressão original; evento da primeira branca derivado do estado | Lean já executado em a.first_white_probability | Baixo custo, norm_num sobre ℚ; certifica simplificação. Valor 1/3 deve continuar elegível deterministicamente. |
| 6*6=36 | Dois sorteios uniformes de seis compartimentos; objeto pares ordenados | Determinística em b.ordered_pairs, mesmo quando há igualdade | norm_num para igualdade; opcional cardinalidade de Fin6×Fin6. Aritmética não valida escrita da equiprobabilidade. |
| 2*5=10 | Objeto segunda branca com i≠j; partição j∈{1,2}, cinco i por j | Determinística em b.different_favorable | norm_num barato; usar como componente de uma relação/evento já validada, não substituto dela. |
| 10+1=11 | Partições distintas e diagonal, disjuntas e exaustivas | Sem obrigação/claim dedicado; valor global vem da enumeração | Candidato aritmético barato; mais útil certificar também a reunião disjunta das duas partes. |
| (10+1)/36=11/36 | Expressão literal e contagem total do estado | Lean já executado via b.second_white_probability | Baixo custo; não demonstra que o estudante forneceu as partes 10 e 1. |
| 3/6=1/2 | Cor e contagem ótima do caso 1 ou 2 já validadas | Lean já executado nas duas conditionals | Baixo custo; escopo racional, dependência de estratégia preservada. |
| (1/6)*(1/2)+(1/6)*(1/2)=1/6 | Continuação, estratégias, condicionais e estrutura ponderada escritas | Lean já executado em c.total_win_probability | Baixo custo; prova aritmética forte dentro de um checker composto. |
| Estado, evento, ótimo e empates | Pilhas verificadas; índices 1..6, cores finitas; regra uniforme | Enumeração finita exata existente | Lean viável com Fin/Finset/Fintype e dados finitos, custo de modelagem médio/alto; menor benefício imediato que expor certificado determinístico reproduzível. |

Dependência efetivamente usada: import Mathlib e norm_num, domínio ℚ. Não se propõe nova dependência de biblioteca para as sete contas. Proposições de cardinalidade, transição ou ótimo seriam trabalhos futuros, não provas executadas nesta tarefa. A adequação de Lean para o modelo inteiro é matemática, mas a rota determinística finita é mais simples e já verifica todos os estados relevantes.

## 8. Composite candidates e certificados existentes

Para c.strategy_case_i, os quatro componentes sugeridos já têm análogos reais: after_first(i), counts_after_first(i), best_choices(i), e a ligação tipada estrategia_i+contagem_i. A extração deve preservar essa ligação; apenas reconhecer a palavra preta/cinza não aciona o checker. Proposta mínima: expor recibos separados state_transition_verified, color_count_verified, optimality_verified e case_binding_verified, sem trocar a matemática por decisão LLM.

Para b, os certificados de espaço amostral e eventos já existem, mas a evidência do aluno não é obrigada a relacioná-los. O composto recomendado associa: cardinalidade/medida uniforme; partição distintos/repetidos; relação escrita da contagem; aritmética. b.alternative_complete já é uma conjunção matemática dos seis ramos com soma ponderada. c.total já combina contexto e aritmética. Não é necessário formalizar a figura em Lean para corrigir essas fronteiras de evidência.

## 9. Gaps e diferenças pedagógico-operacionais

| gap | evidência no código/execução | fortalecimento mínimo proposto |
| --- | --- | --- |
| G1 — b.ordered_pairs | pares_ordenados: 36 ou 36=36 satisfaz o produtor; não há certificado escrito de duas escolhas/equiprobabilidade | Preservar checker exato de cardinalidade; acrescentar relação de espaço amostral a um composto. Decidir/documentar se identificação tipada por si só basta aos 2 pontos. |
| G2 — b.different_favorable | favoraveis_distintos: 10 ou 10=10 recebe 2; a partição 2×5 é calculada pelo motor, não escrita pelo aluno | Componente de relação entre segundo compartimento branco e cinco primeiras escolhas diferentes; aceitar enumeração/árvore equivalente com certificado. |
| G3 — b.second_white_probability | 11/36 isolado e total correto sem as partes valem 2; b.conclusion é independente | Contrato de evidência antes de implementar: pauta fornecida pede reunir casos, não declara concessão isolada como em a. Se resultado isolado for permitido, manter result checker e não confundi-lo com método; se não, acrescentar gate autorizado sem inventar pesos. |
| G4 — suficiência versus falsidade em árvore | Seis ramos corretos + soma ponderada sem =11/36 produz b.alternative_complete=refuted e só 2 pontos | Separar unsupported/missing presentation de refutação matemática. Falta de shape não deve ser apresentada como prova de que os ramos/soma são falsos. |
| G5 — representação de estado do aluno | Machine deriva estados, mas VOCABULARY não tem payload para uma lista explícita de novas cores/estado, nem árvore visual | Schema de estado/ramo vinculado à fonte, se necessário; verificar transição deterministicamente. Argumento fora da representação permanece sem validação automática. |
| G6 — rigidez do total de c | Com contexto completo, valor isolado ou soma ponderada sem igualdade deixam o item em 6; forma simplificada pode não preservar o shape exigido | Especificar evidência mínima de desenvolvimento e equivalências aceitas. Não liberar 1/6 isolado por analogia com P2, pois a pauta P3 exige cálculo global. |
| G7 — rotas semânticas legadas | Hybrid/Sufficiency podem produzir origem semantic positiva sem checker matemático resolvido, fora do Current | Novo adaptador P3 deve manter interpretação separada e gate checker-first; não reutilizar promoção semântica genérica como substituta de checker. |

G1/G2 são gaps conservadores de **suficiência pedagógica**, não acusações de erro na enumeração: a verdade dos números é validada. G3 é uma divergência contratual a resolver explicitamente; o diagnóstico não afirma que a pauta autoriza zero ou dois para 11/36 isolado sem uma decisão adicional. Nenhum desses pontos autoriza alterar pesos, PautaEngine ou expectativas nesta etapa.

### Resultado versus justificativa

| parcela | resultado isolado / mínimo atual | compatibilidade e parcial |
| --- | --- | --- |
| a.contagem (2) | inferiores_brancas:2 identifica a contagem; literal 2 sem objeto não equivale a esse claim | Compatível com identificação; não entrega outros pontos. |
| a.probabilidade (2) | 1/3 ou 2/6 isolado: 2, sem Lean obrigatório | Autorização pedagógica explícita. Contagem adicional é necessária aos outros 2. |
| b.espaço (2) | 36 rotulado aceito; tautologia também | Valor verdadeiro, suficiência da equiprobabilidade/relação não exigida: G1. |
| b.distintos (2) | 10 rotulado aceito; tautologia também | Valor verdadeiro, argumento 2×5 ausente: G2. |
| b.repetidos (2) | repeticao_branca:{6} | Afirma exclusividade e é comparado à diagonal do estado; não precisa nova prova Lean. |
| b.conclusão (2) | 11/36 isolado aceito | Operacional inequívoco; compatibilidade com requisito reunir casos não explicitada pedagogicamente: G3. |
| b.árvore (8 alternativos) | Seis condicionais corretas + soma ponderada em igualdade | Método equivalente real; palavra árvore ou total isolado não vale 8. Forma sem igualdade é limite G4. |
| c.continuação (1) | continuar:{1,2} | Conjunto explícito correto. |
| c.estratégias (2+2) | Cor ótima + contagem3 para cada caso; cor sozinha não basta | Resultado parcial independente de continuar; contexto caso1/caso2 precisa estar vinculado. |
| c.condicionais (1 conjunto) | Ambas corretas, com estratégias; fração equivalente aceita | Não há meia parcela prevista para só um caso. |
| c.global (2) | Forma de dois ramos ou produto combinado, igualdade, todo contexto | 1/6 isolado vale zero; com demais passos e somente valor final, item fica6. Não transportar a autorização específica de a. |

## 10. Riscos concretos de falso crédito e subpontuação

**Falso crédito de método:** em b, apenas quatro campos com valores 36,10,{6},11/36 já chegam a 8. As duas tautologias 36=36 e 10=10 chegam a 4. Há verificação de verdade, mas ela não comprova que foi apresentado o argumento exigido. Outra rota de risco seria copiar a promoção SEMANTIC_SUPPORTED do reconciliador legado; ela não foi utilizada nesta tarefa.

**Subpontuação:** prosa correta sem a notação suportada; árvores visuais não transcritas; soma ponderada correta sem igualdade; representação de estratégia/estado não declarada; omissão de uma dependência textual que é exigida pelo contrato operacional. Uma sondagem em a com “Há duas bolas brancas entre as seis inferiores. A probabilidade é 2/6=1/3.” recebeu zero porque nenhum fato foi produzido, não porque a matemática foi refutada.

**Epistemologia:** métodos fora do shape aceito podem receber refuted na observação booleana de b.alternative_complete. Isso é diferente de FORMAL_REFUTED e deve ser corrigido no fortalecimento futuro. Conflitos matemáticos sobre a mesma obrigação são bloqueados pela bridge; b com 11/36 e 1/2 simultâneos ficou indeterminate e zero.

| sondagem temporária | score observado | fatos/estados |
| --- | --- | --- |
| a_bare | 2.0 | a.first_white_probability=verified |
| b_bare | 2.0 | b.second_white_probability=verified |
| c_bare | 0.0 | nenhum fato |
| b_labels_only | 8.0 | b.ordered_pairs=verified; b.different_favorable=verified; b.same_compartment=verified; b.second_white_probability=verified |
| b_tautologies | 4.0 | b.ordered_pairs=verified; b.different_favorable=verified |
| b_total_without_parts | 2.0 | b.second_white_probability=verified |
| b_complete_tree_no_equal | 2.0 | b.second_white_probability=verified; b.alternative_complete=refuted |
| b_complete_tree_tautology | 2.0 | b.second_white_probability=verified; b.alternative_complete=refuted |
| c_color_without_count | 0.0 | nenhum fato |
| c_strategies_no_previous | 4.0 | c.strategy_case_1=verified; c.strategy_case_2=verified |
| c_complete_value_total | 6.0 | c.continue_compartments=verified; c.strategy_case_1=verified; c.conditional_success_1=verified; c.strategy_case_2=verified; c.conditional_success_2=verified |
| c_complete_no_equal | 6.0 | c.continue_compartments=verified; c.strategy_case_1=verified; c.conditional_success_1=verified; c.strategy_case_2=verified; c.conditional_success_2=verified |
| a_explicit_natural | 0.0 | nenhum fato |
| b_conflict | 0.0 | b.second_white_probability=verified; b.second_white_probability=refuted |

As 14 sondagens ficaram em script/artefatos temporários; não foram adicionadas a fixtures nem transformadas em expectativas de teste. São observações do contrato congelado, não um novo benchmark.

## 11. Testes e regressões executados

| seleção | testes distintos | resultado |
| --- | --- | --- |
| tests/test_tme2_p3_pauta_bridge.py | 70 | 67 passaram na primeira execução; 3 falharam apenas por PermissionError ao criar artifacts. Os mesmos 3 passaram ao permitir escrita. |
| tests/test_pauta_engine.py | 100 | 100 PASS |
| Seleção -k TME2026P3 em test_semantic_claims, test_tme_hybrid_grader, test_scope_boundary | 6 | 6 PASS; 132 deselected |
| Total pytest distinto | 176 | 176 PASS finais; 0 falhas residuais, 0 errors, 0 skips |
| Replay das fixtures P3 | 25 | 25 PASS; 13/13 IDs de obrigação exercitados positivamente |
| Sondagens diagnósticas | 14 | Resultados preservados; sem asserção de nota externa |
| Enumeração independente do estado | 36 | 36 eventos; 11 favoráveis; ótimo global1/6; empates detectados |

A suíte P3 contém 25 casos parametrizados, testes de fonte/adulteração, estado finito, inversão do sexto, notação racional, contexto, árvores, parcial, teto20 e isolamento do registry. Três testes parametrizados de contrato formal fazem mock de evaluate_student_proof; outro instala um veto para garantir que contexto ausente não chama Lean. **Esses quatro testes não são evidência de prova formal.** A evidência formal real é o replay abaixo, sem mock.

A seleção relacionada exercita três proteções de conceito errado no projetor semântico, dois controles P3 parametrizados do reconciliador e uma fronteira de escopo. Nenhum provider real foi chamado. Os 25 casos de replay são os mesmos casos já cobertos por testes parametrizados, não 25 novos textos independentes.

| caso existente | pontos | PASS |
| --- | --- | --- |
| a_complete | 4 | True |
| a_answer_only | 2 | True |
| a_count_only | 2 | True |
| a_wrong_probability | 2 | True |
| a_irrelevant | 0 | True |
| a_equivalent_answer | 2 | True |
| a_finite_decimal | 0 | True |
| a_repeating_decimal | 0 | True |
| b_official | 8 | True |
| b_missing_same | 6 | True |
| b_answer_only | 2 | True |
| b_tree | 8 | True |
| b_wrong_favorable | 2 | True |
| b_keyword_only | 0 | True |
| b_incomplete_tree | 2 | True |
| b_wrong_branch | 2 | True |
| b_both_methods | 8 | True |
| c_complete | 8 | True |
| c_no_total | 6 | True |
| c_answer_only | 0 | True |
| c_wrong_second | 3 | True |
| c_wrong_total | 6 | True |
| c_conditional_equivalent | 8 | True |
| c_arithmetic_without_strategy | 0 | True |
| c_missing_continuation | 5 | True |

Lacunas de regressão: não há teste P3 permanente de Lean real neste arquivo principal; os casos formais unitários são mockados. Faltam testes permanentes para a política de valor/método em b, estado intermediário escrito pelo aluno, distinção shape ausente/falso, formatos verbais equivalentes e total ponderado sem igualdade. Empates foram sondados agora, mas não devem ser confundidos com cobertura pré-existente da suíte. Não se alteraram expectativas para eliminar essas lacunas.

## 12. Comandos e evidência de execução

No worktree P3, Python existente `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`; todos os comandos pytest/replay com PYTHONDONTWRITEBYTECODE=1, PYTHONPATH="$PWD/app", CONFIA_TME_SEMANTIC_ENABLED=0.

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0
P3_PYTHON=/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python

"$P3_PYTHON" -m pytest tests/test_tme2_p3_pauta_bridge.py tests/test_pauta_engine.py \
  -q -p no:cacheprovider --basetemp=/private/tmp/p3-checker-diagnostic-01/pytest \
  --junitxml=/private/tmp/p3-checker-diagnostic-01/pytest.xml

"$P3_PYTHON" -m pytest tests/test_tme2_p3_pauta_bridge.py \
  -k rational_formal_result_contract_and_tamper_rejection -q -p no:cacheprovider \
  --basetemp=/private/tmp/p3-checker-diagnostic-01/permission-retry \
  --junitxml=/private/tmp/p3-checker-diagnostic-01/permission-retry.xml

"$P3_PYTHON" -m pytest tests/test_semantic_claims.py tests/test_tme_hybrid_grader.py tests/test_scope_boundary.py \
  -k TME2026P3 -q -p no:cacheprovider --basetemp=/private/tmp/p3-checker-diagnostic-01/related \
  --junitxml=/private/tmp/p3-checker-diagnostic-01/related.xml

lake build
# Clone inicial interrompido; cache copiado de P2 após comparar toolchain/manifest/revisões.
lake build
lake env lean --version

"$P3_PYTHON" -m scripts.evaluation.run_tme_pauta_cases --problem TME2026P3 \
  --output artifacts/evaluations/tme_p3_checker_first_diagnostico_01/replay \
  --lean-cases a_complete,a_wrong_probability,b_official,b_tree,c_complete,c_wrong_total,c_conditional_equivalent,c_wrong_second,c_arithmetic_without_strategy,a_answer_only,b_answer_only,c_answer_only

"$P3_PYTHON" /private/tmp/p3-checker-diagnostic-01/probes.py
```

Os comandos capturaram stdout/stderr combinados nos logs correspondentes. A criação do diretório de artefatos no P3 exigiu permissão da ferramenta por estar fora da raiz inicialmente gravável da sessão; isso não foi defeito dos testes. O build inicial terminou143 por interrupção deliberada; o build final e replay terminaram0.

Artefatos: [/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_checker_first_diagnostico_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_checker_first_diagnostico_01). Incluem logs/JUnit, before_hashes, probes.json, finite_certificate.json, formal_receipts.json, recibo de execução e replay completo. Os arquivos Lean gerados permanecem em artifacts/student_claim_checks, com caminhos registrados nos recibos. Nenhum theorem de produção foi adicionado.

## 13. Proposta mínima de fortalecimento — sem implementação

1. **Fechar o contrato de b antes do extractor.** Explicitar o que vale pelos resultados 36,10,11/36 sem desenvolvimento, preservando os pesos existentes. Registrar que a autorização inequívoca de resultado isolado é a de a:1/3. Não usar tuning para definir esse contrato.
2. **Expor o certificado finito existente.** Estado inicial hashado, transição por índice, PMF uniforme dos36 pares, partição 10+1, cores/contagens e argmax com empates. Não reconstruir o estado da figura por LLM.
3. **Separar resultado e relação em b.** Manter aritmética exata; acrescentar verificadores determinísticos de relações/enumerações/árvores vinculados às afirmações do aluno. Não resolver um gap de justificativa apenas com norm_num.
4. **Explicitar os compostos c e árvore.** Reutilizar gates já presentes; emitir recibos de componentes e distinguir falta de representação, insuficiência, contradição e erro técnico.
5. **Preservar/fortalecer Lean de modo seletivo.** Manter as cinco rotas existentes; adicionar aritmética de contagem apenas se ajudar a rastrear uma igualdade efetivamente escrita. Não impor Lean ao valor1/3 ou ao estado finito já decidível.
6. **Regressões antes de expansão semântica.** Tornar permanentes controles Lean reais de prova/refutação, crédito parcial, conflitos, método incompleto e equivalências com estado. Só depois considerar um extractor P3 que interprete, sem autoridade positiva para obrigações sem checker.

É viável chegar a cobertura matemática independente sem LLM como juiz: o domínio é pequeno e a máquina já está codificada. O trabalho restante é principalmente de contrato, representação e suficiência, não descoberta da configuração nem formalização ampla em Lean. Nenhum novo checker foi implementado.

## 14. Preservação e estado final

789 arquivos preexistentes monitorados mantiveram exatamente seus hashes, incluindo código, prompt, pauta, máquina, datasets, toolchain e manifest. O conjunto monitorado excluiu caminhos de gold/holdout, que não foram lidos. Foram criados apenas o relatório solicitado e artefatos locais ignorados; a infraestrutura .lake foi preparada. Sem stage/commit.

```text
SHA: 1165dbf62f854d6d40c0cc5f2bb6fcb02ca381e9
branch: experiment/tme-semantic-formal-p3
git status --short:
?? docs/audits/TME_P3_CHECKER_FIRST_DIAGNOSTICO_01.md
```

## 15. Veredito

**CHECKER_STRENGTHENING_REQUIRED**. O P3 possui modelo finito verificável e cobertura de produtores13/13, com Lean real funcional. Ainda não se deve declarar cobertura forte integral: faltam contratos explícitos e validação de relação/suficiência em parcelas de b, e há fronteiras de representação/epistemologia a tratar. Isso não configura ARCHITECTURAL_GAP de estado da máquina e não justifica implementar agora o SemanticExtractor P3.
