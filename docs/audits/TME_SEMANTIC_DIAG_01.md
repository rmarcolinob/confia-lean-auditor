# TME_SEMANTIC_DIAG_01 — diagnóstico forense dos 25 DEV

Data: 2026-11-02. Diagnóstico por leitura e reconciliação dos traces congelados; **nenhuma alteração de código, nova auditoria, chamada de modelo, execução Lean, commit ou acesso a textos/resultados individuais HOLDOUT**.

A principal perda ocorre antes da verificação: entrada mal roteada, representação sem papel matemático e contexto excessivamente abrangente. Não há evidência, nestes DEV, de fatos verificados perdidos pela bridge. **Recomendação única: B — substituir o contrato de extração por semantic extraction orientada às obrigações matemáticas, sem pontos**, em futuro experimento DEV. Isso não basta, sozinho, para resolver a maior parte das perdas; não muda o NO_GO atual.

## Escopo, fontes e limites

Foram lidas integralmente as 25 revisões aceitas DEV, cinco por problema. Os IDs foram filtrados antes de abrir as revisões; o arquivo geral de dataset não foi aberto. A reconstrução das fontes mapeadas confere, caso a caso, com o `source_sha256` dos resultados congelados. A classificação matemática não usou `synthetic_expected_score`. MAE aparece apenas como métrica agregada já publicada, não como verdade de correção.

A pauta de referência é a transcrição versionada no repositório (`examples/pautas/tme2_problem{1..5}.v1.json`), confrontada com os producers/checkers e descrições locais dos problemas. O PDF oficial não foi novamente consultado. P3 usa a configuração da máquina já registrada no experimento; o próprio trace identifica sua origem como figura confirmada pelo usuário. Esta é uma revisão matemática manual de um analista, não uma segunda correção humana independente nem uma validação externa da transcrição da pauta. “Aparentemente satisfeita” conserva essa limitação.

P1 usa internamente `TME2_P1_PILOT`. O diagnóstico preserva os IDs públicos DEV e registra os IDs reais de facts/records. Há ingredientes auxiliares, métodos alternativos e obrigações dependentes: as 730 linhas **não são 730 oportunidades independentes de ganhar pontos**. DEV também está enriquecido com os cinco erros técnicos de P1; não se extrapolam percentuais para as 100 HOLDOUT.

Fontes principais: [resultado final](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_understanding_01/dev_after_results.json), [baseline](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_understanding_01/dev_baseline_results.json), [candidatos e eventos](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_understanding_01/semantic_candidates.jsonl), [comparação das três fases](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_understanding_01/dev_summary.json), [manifesto de acesso DEV](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_diag_01/source_access_manifest.json).

## Como ler as dez etapas

Cada solução tem uma linha por obrigação em `cases_analysis.json`, com trecho literal e offsets na solução, referências para MathClaimRecord/candidate, FactResult, PautaEvidence, resultado baseline e decisão final. O catálogo de cada caso conserva as formas canônicas, fontes, status, eventos, fingerprints dos facts e referências de verificação. Os offsets dos records/candidates referem-se a `mapped_text`; os offsets das citações manuais referem-se a `solution_text`.

1. **Texto:** `evidence_present_in_solution` distingue presença, ausência e incerteza; `apparently_satisfied` distingue evidência correta de tentativa errada. São 438 presenças claras (409 aparentemente corretas + 29 tentativas que não satisfazem), 257 ausências e 35 incertezas.
2. **Extração determinística:** existe fragmento relacionado, identificado por record real. Fragmento capturado pode ser incompleto ou recortado incorretamente; “encontrada” não certifica fidelidade.
3. **Candidato semântico:** existe candidato relacionado, mesmo que tenha papel/item/tipo errado. Um candidato pode interessar a várias obrigações; os totais por obrigação não são os 158 candidatos brutos.
4. **Grounding:** preserva o status final do trace, distinguindo também vínculo literal, grounding semântico e grounding por qualquer rota. `representation_miss` frequentemente vira `unresolved` apesar de o trecho ser literal.
5. **Contexto:** lista os estados observados nas rotas relacionadas; `null`/`context_applicable=false` significa que nenhuma decisão foi tentada. Os traces frequentemente registram papel `unknown` e atribuibilidade falsa; isso é reportado como `rejected`, sem inventar se o modelo entendeu “hypothetical” ou “negated”.
6. **Canonicalização:** `parsed` só significa que existe uma forma canônica; não valida origem, atribuição, verdade ou completude. Status bruto `ambiguous` está preservado no catálogo e agregado como `unsupported`.
7. **FactResult:** exige fact real, não um ID esperado no placeholder da bridge. Projeções internas de checker não são contadas como extração determinística original.
8. **Verificação:** mecanismo e resultado são campos separados. `canonical`/`deterministic` podem refutar; Lean só aparece quando o trace indica `student_lean`. Nenhuma prova foi reexecutada.
9. **Bridge:** exige `source_claim_ids`, não apenas uma das 730 entradas `PautaEvidence`. Placeholder `NO_EXISTING_FACT` não é evidência recebida.
10. **Decisão e crédito:** `supported` é distinto de `contributed_to_awarded_credit`. Crédito percorre somente bandas/caminhos selecionados e folhas com `known_points>0`; em `any_of`, o testemunho efetivamente selecionado. Não atribuí frações de pontos às obrigações nem contei alternativas derrotadas.

A causa principal é a primeira quebra relevante da rota capaz de transportar aquela evidência. Ausência de detector determinístico, por si só, não é falha quando a rota semântica deveria tratar prosa. Quando um fact composto falha por dependência, a causa é herdada do primeiro ingrediente ausente/mal representado; não é automaticamente falta de checker. O diagnóstico por causa é uma atribuição manual sustentada pelos traces, não um experimento contrafactual de reparo. Cada miss confirmado tem exatamente uma causa; bloqueios adicionais permanecem no catálogo e nas notas.

## Funil geral e por problema


| Etapa | Todas as obrigações | Somente aparentemente satisfeitas |
| --- | --- | --- |
| Obrigações | 730 | 409 |
| Fragmento determinístico relacionado | 207 | 176 |
| Candidato semântico relacionado | 239 | 197 |
| Candidato com trecho literal vinculado | 231 | 189 |
| Grounded semântico | 114 | 90 |
| Atribuível semântico após gates | 61 | 48 |
| Canônico semântico, antes dos gates | 167 | 140 |
| Grounded em alguma rota | 255 | 214 |
| Canônico em alguma rota | 264 | 222 |
| FactResult | 57 | 50 |
| Fact verificado | 43 | 43 |
| Fact refutado | 6 | 1 |
| Fact não verificado | 8 | 6 |
| Evidência real na bridge | 57 | 50 |
| Participa do crédito concedido | 33 | 33 |


As colunas acima são contagens por etapa, **não um funil cumulativo**: a rota determinística dispensa candidato semântico, e o parser roda antes dos gates. Decisão final: **43 supported, 6 refuted, 681 indeterminate**. São 57 facts: 43 verificados, 6 refutados e 8 não verificados; todos os 57 têm evidência na bridge. Verificados por mecanismo: 22 determinísticos, 13 por equivalência canônica e 8 por Lean. Uma das seis refutações corresponde a evidência correta recortada incorretamente em P1_12; as outras cinco não pertencem à coorte de misses confirmados.

O funil **cumulativo semântico**, limitado às obrigações aparentemente satisfeitas, exige candidato relacionado, grounding, canônico e depois provenance semântica real no fact:

`409 texto → 197 candidato → 90 grounded → 72 canonical → 24 FactResult → 19 verified → 19 PautaEvidence → 19 supported → 12 participantes do crédito`.

As sete deduplicações são preservadas nos eventos, mas não são novas conversões semânticas. As 24 conversões nesta coorte não se confundem com os 30 facts de provenance semântica em todas as obrigações, que também incluem erros do aluno e fatos compostos sem justificativa completa.

| Problema | Examinadas | Aparentemente sim | Det.¹ | Sem.¹ | Grounded sem.¹ | Facts¹ | Verificadas¹ | Bridge¹ | Crédito¹ | Misses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | 105 | 77 | 42 | 47 | 30 | 30 | 29 | 30 | 22 | 48 |
| P2 | 115 | 91 | 49 | 56 | 32 | 7 | 7 | 7 | 7 | 84 |
| P3 | 65 | 50 | 27 | 20 | 1 | 5 | 4 | 5 | 4 | 46 |
| P4 | 155 | 97 | 13 | 14 | 1 | 1 | 1 | 1 | 0 | 96 |
| P5 | 290 | 94 | 45 | 60 | 26 | 7 | 2 | 7 | 0 | 92 |


¹ Colunas intermediárias limitadas às aparentemente satisfeitas; não são cumulativas.


| Problema | Texto | Candidato | Grounded | Canônico | Fact | Verified | PautaEvidence | Supported | Crédito |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | 77 | 47 | 30 | 26 | 9 | 9 | 9 | 9 | 5 |
| P2 | 91 | 56 | 32 | 25 | 7 | 7 | 7 | 7 | 7 |
| P3 | 50 | 20 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| P4 | 97 | 14 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |
| P5 | 94 | 60 | 26 | 19 | 7 | 2 | 2 | 2 | 0 |


Os **158 candidatos brutos** têm 148 vínculos literais exatos após relocação, 64 status finais `grounded`, 110 canônicos e somente 30 atribuíveis após todos os gates. Há 76 flags de rejeição de contexto. Os motivos finais, mutuamente exclusivos, são: 10 `grounding_miss`, 52 `representation_miss`, 45 `unsupported_representation`, 5 `item_binding_miss`, 16 `context_gate`, 23 `unique_literal_relocation` e 7 `deduplicated`. Flags de contexto podem coexistir com falhas posteriores de representação: não se somam 76 com esses motivos. Isso também impede chamar todos os 94 não-grounded de “citação não encontrada”.

**Supported sem contribuição ao crédito (10):** P1_12 `a.constructs_subtraction`, `d.equation`; P1_13 `d.difference_six`; P1_15 e P1_17 `c.several_correct`/`c.some_correct`; P4_16 `b.apqr`; P5_02 `c.max_product`; P5_24 `a.normal_list`. Os quatro claims de listas parciais foram superados pela banda completa. Os outros dependem de ingredientes faltantes ou são auxiliares sem crédito isolado. Isso não demonstra defeito da pauta. Os 33 participantes do crédito sustentam **44 pontos totais em 500 possíveis**: P1=26, P2=10, P3=8, P4=0, P5=0; não são 33 pontos.

## Primeira falha: 366 misses confirmados


| Causa principal | Quantidade | % dos 366 |
| --- | --- | --- |
| DETERMINISTIC_EXTRACTION_MISS | 8 | 2.19% |
| SEMANTIC_EXTRACTION_MISS | 68 | 18.58% |
| SEMANTIC_SCHEMA_TOO_GENERIC | 28 | 7.65% |
| GROUNDING_MISS | 16 | 4.37% |
| CONTEXT_GATE_OVERBLOCK | 93 | 25.41% |
| CANONICALIZATION_MISS | 21 | 5.74% |
| FACT_MAPPING_MISS | 27 | 7.38% |
| CHECKER_GAP | 4 | 1.09% |
| LEAN_GAP | 0 | 0.00% |
| PAUTA_BRIDGE_GAP | 0 | 0.00% |
| PAUTA_MODEL_GAP | 0 | 0.00% |
| EVIDENCE_NOT_ACTUALLY_PRESENT | 0 | 0.00% |
| SYNTHETIC_LABEL_DISPUTABLE | 0 | 0.00% |
| OTHER | 101 | 27.60% |


`OTHER=101` contém **100 perdas anteriores/relativas ao roteamento de entrada** e **1 vínculo entre itens não produzido** (P2_01, realização do centro 5 escrita em a e necessária em b). Quatro fontes mapeadas são inteiramente vazias: **P3_13, P4_13, P4_19, P4_21**, afetando 76 obrigações aparentemente satisfeitas. Além delas, P2_15 perde a parte anterior a (c), P2_10 perde a introdução e P5_09 atribui todo o texto inline a a; são mais 24 obrigações. Um extractor que recebe somente `mapped_text` não pode recuperar texto que nunca recebeu. O comportamento é rastreável a `split_accepted_items`: aceita metadados explícitos ou cabeçalhos isolados; não interpreta marcadores inline.

As 35 incertezas e as 286 obrigações não satisfeitas ficam fora dos 366. Nas 286 há 257 ausências e 29 tentativas erradas. `EVIDENCE_NOT_ACTUALLY_PRESENT` é usado para esse conjunto, não para aumentar artificialmente o número de misses. `SYNTHETIC_LABEL_DISPUTABLE=0` na tabela significa que nenhuma classificação foi derivada do label; não certifica os labels. Exemplos como o total 192 em P2 e a conclusão `2^1013` em P5 mostram por que MAE sintético não pode arbitrar presença/correção.

As quatro ocorrências `CHECKER_GAP` estão em P1: reconhecimento restrito do caso de erro aritmético isolado e da subtração/cancelamento em forma já expandida. Há checker, mas falta cobertura da forma equivalente relevante. Nenhum miss confirmado teve Lean ou bridge como primeira quebra. `PAUTA_MODEL_GAP=0` significa que esta inspeção não demonstrou um defeito do modelo de pontuação; não é uma validação de equivalência com toda a pauta oficial externa.

| Causa | P1 | P2 | P3 | P4 | P5 |
| --- | --- | --- | --- | --- | --- |
| DETERMINISTIC_EXTRACTION_MISS | 5 | 2 | 1 | 0 | 0 |
| SEMANTIC_EXTRACTION_MISS | 13 | 11 | 14 | 13 | 17 |
| SEMANTIC_SCHEMA_TOO_GENERIC | 0 | 10 | 3 | 2 | 13 |
| GROUNDING_MISS | 10 | 1 | 0 | 5 | 0 |
| CONTEXT_GATE_OVERBLOCK | 5 | 36 | 14 | 11 | 27 |
| CANONICALIZATION_MISS | 5 | 5 | 0 | 0 | 11 |
| FACT_MAPPING_MISS | 6 | 6 | 1 | 2 | 12 |
| CHECKER_GAP | 4 | 0 | 0 | 0 | 0 |
| OTHER | 0 | 13 | 13 | 63 | 12 |


## Respostas específicas sobre o interpretador

**A — deixa de reconhecer matemática:** 76 primeiras perdas na família de extração (68 semânticas e 8 determinísticas). Isso inclui omissão de limites, pares, estratégias e multiplicidades; não significa que o LLM “não sabe resolver” o problema. Entre as 409 aparentemente satisfeitas, 212 não têm candidato relacionado; parte delas nunca chegou ao interpretador por perda de entrada. Portanto 212 não é uma contagem de falhas intrínsecas do modelo.

**B — reconhece, mas não representa o papel necessário:** 55 primeiras perdas (28 `SEMANTIC_SCHEMA_TOO_GENERIC` + 27 `FACT_MAPPING_MISS`). A primeira categoria inclui tipo/subject/item incorretos, payload mutilado e prosa no lugar de estrutura; o nome da classe não prova que o JSON Schema é incapaz. Exemplos: quantidade de bolas rotulada como probabilidade, `normal_list` em vez de `candidate`, produto sem o resultado escrito, contagens de listas rotuladas como contagem de três. Nas 27 falhas de mapping há fragmentos matemáticos extraídos, mas falta a ligação ao conceito que o producer consome. Reproduzir a expressão não basta.

**C — candidatos/evidências barrados por grounding/contexto:** 109 primeiras perdas (16 de grounding/vínculo representacional e 93 de contexto). O conjunto inclui a rota determinística, não apenas candidatos LLM; em vários casos há também tipo semântico errado. “Se” em prova por casos, “por exemplo” em uma configuração válida e “não têm a mesma quantidade” são afirmações matemáticas com escopo diferente de dúvida ou rejeição. P4_23 tem, por outro lado, ressalvas reais (“se não me engano”): esses pontos estão entre as incertezas, não foram automaticamente contados como overblock. Os 10 `grounding_miss` brutos do modelo são falhas de vínculo literal; os 16 da classificação por obrigação incluem também gates representacionais, com essa distinção registrada.

**D — fact existe, mas não há checker:** **0 de 57**. Todos têm checker e resultado de verificação. Os oito `unverified` são: P3_02 `c.total_win_probability` (contexto do jogo não verificado); P5_02 `b.increase`, `b.new_contribution`, `b.comparison` (domínio/contribuições não constituídos como facts), `c.general_complete` (certificado geral incompleto); P5_18 e P5_24 `a.product` (payload sem igualdade com 54); P5_24 `a.structural_max` (certificado estrutural não fornecido). Não é correto traduzir esses oito casos por “precisamos de Lean”.

**E — fact verificado não chega à obrigação:** **0 de 43**. Todos os 43 verificados chegam como `supported`; dez não participam do crédito pelos motivos explicitados acima. Não há evidência que sustente escolher bridge/pauta como próximo investimento principal.

A/B/C somam 240 misses; restam 21 de canonicalização, quatro de cobertura do checker e 101 `OTHER`, totalizando 366. D/E são auditorias sobre facts, com denominadores próprios, e não parcelas adicionais desse total.

## Arquitetura orientada às obrigações — contrafactual conceitual

O interpretador atual **já recebe uma ontologia/enum de subjects e instruções sobre os tipos**. Não é um extrator completamente genérico. A mudança relevante seria fornecer significado matemático de cada obrigação, item, forma de evidência e dependências; apenas acrescentar nomes de campos ou IDs não resolve a lacuna observada. As descrições de P5 que repetem o próprio ID também não bastariam.

Um contrato orientado às obrigações poderia representar, por exemplo, “domínio n≥5”, “soma preservada”, “contribuição antes/depois”, “caso condicionado à primeira bola branca” e “multiplicidade 674 de 3” como claims separados e ligados aos trechos correspondentes. O papel do modelo continuaria limitado à interpretação: não decidir correção, nota, completude global, nem inventar contas ausentes. Hipóteses locais, autocorreções, negações matemáticas, autoria e dependências entre itens precisariam permanecer explícitas. Qualquer representação proposta abaixo continua sujeita aos verificadores existentes e à origem literal.

Classificação por miss confirmado, sem execução de uma nova arquitetura:

| Problema | Provavelmente ajuda | Não ajuda sozinha | Incerto |
| --- | --- | --- | --- |
| P1 | 19 | 4 | 25 |
| P2 | 25 | 16 | 43 |
| P3 | 18 | 13 | 15 |
| P4 | 17 | 63 | 16 |
| P5 | 42 | 12 | 38 |
| Total | 121 | 108 | 137 |


**121/366 (33,06%) provavelmente ajuda; 108/366 (29,51%) não ajuda sozinha; 137/366 (37,43%) incerto.** “Provavelmente ajuda” significa produzir evidência estruturada mais adequada, não 121 novas obrigações verificadas e muito menos 121 novos pontos. A classificação é conservadora quanto a contexto/grounding/canonicalização: mudar o prompt não amplia automaticamente a gramática, recupera a entrada perdida, altera um gate ou fornece um checker.

A opção B é recomendada porque trata explicitamente a omissão e a confusão de papéis que persistem apesar da ontologia atual. C isoladamente deixaria claims omitidos e mal tipados; D/E não correspondem aos gargalos observados; F não é sustentada pelos 19 facts semânticos verificados. Não há base para promoção do experimento atual nem para abrir HOLDOUT agora. Os 100 misses de entrada e 93 de contexto continuam sendo condicionantes operacionais de qualquer teste futuro, sem serem corrigidos nesta tarefa.

## Quinze casos exemplares

As representações abaixo são descrições conceituais do conteúdo escrito, não patches, novas execuções ou evidência inserida no sistema. IDs completos e payloads estão no catálogo do respectivo caso.


### 1. TME2026P1_06 — `b.reversed_number`

**Trecho do aluno:**

> o invertido vale 100c + 10b + a

↓ **Significado matemático:** Define a representação decimal e desenvolve a diferença entre o número e seu reverso. O “se” fixa variáveis, não declara uma tentativa duvidosa.

↓ **Extração observada:** A definição invertida aparece no registro determinístico; sua fonte é não atribuível. O candidato de b ainda funde etapas não contíguas numa citação.

↓ **Quebra:** Contexto sobre o parágrafo bloqueia a definição; para a subtração, o primeiro problema do candidato é vínculo literal.

↓ **Representação adequada:** Definições vinculadas aos dígitos a,b,c, seguidas da subtração com dois operandos, cancelamento e fatoração; cada etapa com seu próprio trecho e escopo.

Rastro focal: `student:generic_math_256_270_expression`; fact `não produzido`; decisão `indeterminate`.


### 2. TME2026P1_12 — `d.difference_six`

**Trecho do aluno:**

> a − c = 594 ÷ 99 = 6

↓ **Significado matemático:** Divide 594 por 99 para obter a diferença dos algarismos, corretamente.

↓ **Extração observada:** Dois recortes determinísticos: a−c=594 e 99=6. O primeiro produz d.difference_six refutado por equivalência canônica.

↓ **Quebra:** DETERMINISTIC_EXTRACTION_MISS: corrupção anterior à verificação, não falha de prova Lean.

↓ **Representação adequada:** Cadeia com membros a−c, 594/99 e 6; a igualdade verificada deve preservar a divisão escrita. O original não afirma a−c=594.

Rastro focal: `student:generic_math_1549_1560_relation`, `student:generic_math_1563_1569_relation`; fact `d.difference_six`; decisão `refuted`.


### 3. TME2026P1_15 — `c.difference_domain`

**Trecho do aluno:**

> a − c = 1 → 99

↓ **Significado matemático:** Enumera os oito valores do domínio e seus resultados, fornecendo uma tabela do padrão 99k.

↓ **Extração observada:** Há relações fragmentárias para as oito linhas e um candidato de coleção de resultados; este último alcança a banda de lista completa.

↓ **Quebra:** FACT_MAPPING_MISS no domínio/padrão: linhas não se consolidam em domínio tipado. Já a lista chega à pauta; os claims de listas parciais não somam pontos adicionais.

↓ **Representação adequada:** Tabela k→99k para k=1,…,8, distinta da coleção {99,198,…,792}; manter limites e conteúdo demonstrados, sem inventar prova dos limites.

Rastro focal: `student:generic_math_196_201_relation`, `student:generic_math_203_208_relation`, `student:generic_math_231_240_relation`, `student:generic_math_247_256_relation`, `student:generic_math_264_273_relation`, `student:generic_math_281_290_relation`, `student:generic_math_297_306_relation`, `student:generic_math_314_323_relation`, `student:generic_math_331_340_relation`, `student:generic_math_348_357_relation`; fact `não produzido`; decisão `indeterminate`.


### 4. TME2026P2_08 — `a.placement`

**Trecho do aluno:**

> A=1 e E=9, B=2 e F=8, C=3 e G=7, D=4 e H=6.

↓ **Significado matemático:** Fornece uma configuração textual válida, que é justamente uma testemunha aceitável para a existência.

↓ **Extração observada:** As oito atribuições são capturadas; o parágrafo com “Por exemplo” não é atribuível. Em c há também a conta falsa 2^4=8 e total 192.

↓ **Quebra:** CONTEXT_GATE_OVERBLOCK na configuração. A conta errada de c não é miss de uma resposta 384.

↓ **Representação adequada:** Mapa textual A→1,E→9,…,H→6, com referências às oito posições e checagem das linhas; não fabricar DiagramState ou corrigir o produto do aluno.

Rastro focal: `student:generic_math_213_216_relation`, `student:generic_math_219_222_relation`, `student:generic_math_224_227_relation`, `student:generic_math_230_233_relation`, `student:generic_math_235_238_relation`, `student:generic_math_241_244_relation`, `student:generic_math_246_249_relation`, `student:generic_math_252_255_relation`; fact `não produzido`; decisão `indeterminate`.


### 5. TME2026P2_10 — `c.total`

**Trecho do aluno:**

> O total é então 24 . 16 = 384.

↓ **Significado matemático:** Combina 24 permutações dos pares e 16 orientações, chegando corretamente a 384.

↓ **Extração observada:** Candidato total384 gerado, mas contexto não atribuível; o determinístico recorta 16=384 no ponto de multiplicação.

↓ **Quebra:** CONTEXT_GATE_OVERBLOCK na rota semântica, contaminada por “pergunta”/“enunciado”; há falha adicional de recorte na outra rota.

↓ **Representação adequada:** Produto de contagem com fatores 24 e 16, seus papéis e igualdade final 384; citar o trecho final e as justificativas independentes.

Rastro focal: `student:generic_math_2202_2210_relation`, `11:c5`; fact `não produzido`; decisão `indeterminate`.


### 6. TME2026P2_18 — `c.total`

**Trecho do aluno:**

> Total = 4!·2^4 = 24·16 = 384.

↓ **Significado matemático:** Explicita contagem, avaliação dos fatores e resposta numérica.

↓ **Extração observada:** Payload total contém cadeia de três membros, não suportada pelo tipo; há igualdade binária determinística que não é consumida como quantidade nomeada.

↓ **Quebra:** CANONICALIZATION_MISS na rota semântica; mapping permanece como barreira secundária.

↓ **Representação adequada:** Cadeia de igualdades preservada, ou passos separados com papel counting_product/total e dependência em permutações/orientações; sem substituir a expressão por resposta inferida.

Rastro focal: `student:generic_math_725_736_relation`, `7:c`; fact `não produzido`; decisão `indeterminate`.


### 7. TME2026P3_02 — `c.total_win_probability`

**Trecho do aluno:**

> (1/6)·(1/2) + (1/6)·(1/2) = 1/6

↓ **Significado matemático:** Combina os dois ramos em que a primeira bola permite continuar, com sucesso condicional 1/2 em cada ramo.

↓ **Extração observada:** A soma escrita chega a FactResult c.total_win_probability, mas status unverified, reason GAME_CONTEXT_NOT_VERIFIED. Quantidade de bolas/probabilidades também são confundidas em candidatos.

↓ **Quebra:** Falta a representação verificada de continuação, estratégia e contagem dos ramos; o checker existe e exige esses pré-requisitos.

↓ **Representação adequada:** Ramos 1 e 2, cor ótima preta/cinza, contagem 3/6 e probabilidade 1/2 em cada um, ligados à soma ponderada escrita. Verificar estado da máquina separadamente.

Rastro focal: `student:generic_math_426_457_relation`, `student:generic_math_465_468_expression`, `2:c`; fact `c.total_win_probability`; decisão `indeterminate`.


### 8. TME2026P3_13 — `b.second_white_probability`

**Trecho do aluno:**

> Total de favoraveis 11 em 36, probabilidade 11/36.

↓ **Significado matemático:** Apresenta contagem de pares e uma alternativa por condicionamento, além da estratégia de c.

↓ **Extração observada:** Nenhum record/candidato/fact: fonte mapeada vazia.

↓ **Quebra:** OTHER/input_mapping antes do interpretador: prosa sem cabeçalhos isolados aceitos.

↓ **Representação adequada:** Trechos de a,b,c associados aos itens por fronteiras de origem; em b, 36 pares, 10 distintos favoráveis e uma repetição favorável. Não basta mudar o prompt posterior.

Rastro focal: nenhum record/candidato; fact `não produzido`; decisão `indeterminate`.


### 9. TME2026P3_22 — `c.strategy_case_1`

**Trecho do aluno:**

> Palpite preta: acerta em 3 dos 6 pares, probabilidade 3/6 = 1/2.

↓ **Significado matemático:** Distingue a estratégia depois da primeira retirada; a melhor cor depende do compartimento inicial.

↓ **Extração observada:** Igualdade numérica extraída, mas não atribuível; candidatos não constituem o par estratégia+contagem por ramo.

↓ **Quebra:** CONTEXT_GATE_OVERBLOCK sobre condicionais matemáticas; o subject_binding também restringe ramos.

↓ **Representação adequada:** Caso “primeira retirada no 1”: cor preta, contagem 3 de 6, probabilidade 1/2; caso 2 separado com cinza. Em b, não ignorar a identificação errada da branca remanescente só porque11/36 está correto.

Rastro focal: `student:generic_math_1358_1367_relation`, `8:c2`, `10:c4`; fact `não produzido`; decisão `indeterminate`.


### 10. TME2026P4_13 — `c.h_plus_c`

**Trecho do aluno:**

> h + c = 18 e h^2 = c^2 + 144

↓ **Significado matemático:** Relaciona os perímetros sombreados e aplica Pitágoras, obtendo h=13, c=5 e raízes 5/3, 13/3.

↓ **Extração observada:** Nenhum registro/candidato: todo o texto foi perdido no mapeamento.

↓ **Quebra:** OTHER/input_mapping, antes da extração.

↓ **Representação adequada:** Relações h+c=18 e h²=c²+144 com definição de h/c; valores 13/5, correspondência com 3x e3(6−x), conjunto de raízes; prova separada de exclusão da hipotenusa 12.

Rastro focal: nenhum record/candidato; fact `não produzido`; decisão `indeterminate`.


### 11. TME2026P4_16 — `b.perimeter_apqr`

**Trecho do aluno:**

> 2*(6-x +x)=12

↓ **Significado matemático:** Usa que APQR é paralelogramo e calcula o dobro da soma de dois lados adjacentes.

↓ **Extração observada:** APQR paralelogramo vira fact verificado; igualdade de perímetro determinística é parsed e atribuível. Candidato perimeter_apqr=12 perde a ligação ao nome APQR fora de seu trecho.

↓ **Quebra:** FACT_MAPPING_MISS: expressão correta sem papel de perímetro. b.apqr supported isolado concede 0. Triângulos equiláteros também sofrem rejeição representacional pelo plural.

↓ **Representação adequada:** Tipo APQR=paralelogramo e perímetro APQR com desenvolvimento2((6−x)+x)=12, vinculados a trechos distintos do mesmo argumento.

Rastro focal: `student:generic_math_130_143_relation`, `3:b2`; fact `não produzido`; decisão `indeterminate`.


### 12. TME2026P4_19 — `c.exclude_12`

**Trecho do aluno:**

> (6-x)^2 = 36 - x^2

↓ **Significado matemático:** Tenta excluir 12 como hipotenusa, mas expande incorretamente o quadrado. Depois resolve corretamente h+c/h−c e verifica5-12-13.

↓ **Extração observada:** Entrada inteira sem mapping; não há claims para nenhuma dessas partes.

↓ **Quebra:** A prova específica de exclusão não satisfaz a obrigação: EVIDENCE_NOT_ACTUALLY_PRESENT. Para as relações e respostas corretas posteriores, a primeira falha é OTHER/input_mapping.

↓ **Representação adequada:** Conservar o passo errado como afirmação refutável; separar os passos corretos posteriores. Não transformar a conclusão correta “12 não é hipotenusa” numa prova que o aluno não escreveu.

Rastro focal: nenhum record/candidato; fact `não produzido`; decisão `indeterminate`.


### 13. TME2026P5_02 — `b.increase`

**Trecho do aluno:**

> Como n ≥ 5, temos 2n - 9 ≥ 2(5) - 9 = 1 > 0. Logo 3(n - 3) > n

↓ **Significado matemático:** Justifica aumento do produto sob domínio n≥5; a soma é preservada.

↓ **Extração observada:** Domínio aparece como expressão anônima; new_contribution/increase são candidatos e facts unverified. comparison também depende da contribuição antiga, não representada.

↓ **Quebra:** FACT_MAPPING_MISS do domínio para aumento; SEMANTIC_EXTRACTION_MISS da contribuição antiga para a comparação. Não é ausência de checker.

↓ **Representação adequada:** Hipótese n∈Z,n≥5; contribuição antiga n e nova3(n−3); diferença2n−9 positiva; cada afirmação com origem e dependência, preservando a soma separadamente.

Rastro focal: `student:generic_math_607_626_relation`, `student:generic_math_633_638_relation`, `student:generic_math_646_671_relation`, `student:generic_math_678_690_relation`, `4:b`, `5:b`; fact `b.increase`; decisão `indeterminate`.


### 14. TME2026P5_18 — `d.sizes`

**Trecho do aluno:**

> caso 1: 674+1 = 675
> caso 2: 674+2 = 676

↓ **Significado matemático:** Conta os elementos das duas listas de mesma soma/produto máximo, uma com 4 e outra com dois 2.

↓ **Extração observada:** Duas igualdades determinísticas parsed, não atribuíveis; semântica as rotula threes_count. As duas listas são fundidas em um payload list_four com reticências.

↓ **Quebra:** CONTEXT_GATE_OVERBLOCK para as contagens, por “não têm mesma quantidade”; tipo e canonicalização também falham nas listas.

↓ **Representação adequada:** Multiconjuntos {3:674,4:1} e {3:674,2:2}, tamanhos 675/676 e desigualdade de tamanhos. Multiplicidades vêm de c e das contas de d, com referência explícita entre trechos.

Rastro focal: `student:generic_math_448_459_relation`, `student:generic_math_468_479_relation`, `12:d`, `13:d`; fact `não produzido`; decisão `indeterminate`.


### 15. TME2026P5_24 — `a.product`

**Trecho do aluno:**

> 3 * 3 * 3 * 2 = 54

↓ **Significado matemático:** Calcula corretamente o produto da lista de soma 11. Isso não torna corretas as conclusões posteriores para 2026.

↓ **Extração observada:** Candidato product contém apenas 3*3*3*2; fact unverified. normal_list é verificado, mas a.candidate não é produzido. Em c/d a resposta final é 2^1013 e lista única de 1013 dois.

↓ **Quebra:** SEMANTIC_SCHEMA_TOO_GENERIC/payload mutilado em a. Em c/d o resultado final é errado e não deve ser resgatado por escolher um rascunho intermediário correto.

↓ **Representação adequada:** Produto com igualdade completa e candidate(2,3,3,3), separados de normal_list/certificado de maximalidade. Preservar a conclusão falsa de c como afirmação do aluno, sem trocar por 4·3^674.

Rastro focal: `student:generic_math_59_77_relation`, `1:a`; fact `a.product`; decisão `indeterminate`.


## Unicode: melhoria técnica independente

A sequência correta das fases é:

| Fase | Supported | Refuted | Technical errors | Cobertura decidida | Scores numéricos | MAE sintético |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline bruto | 20 | 1 | 5 | 21/730 = 2,88% | 20/25 | 15,70 (20 casos) |
| Só normalização Unicode | 24 | 2 | 0 | 26/730 = 3,56% | 25/25 | 15,68 (25 casos) |
| Unicode + semântica | 43 | 6 | 0 | 49/730 = 6,71% | 25/25 | 14,88 (25 casos) |


Portanto **3,56% não é o baseline bruto e 6,71% não é o efeito Unicode isolado**. A normalização resolveu os cinco `score=null` conhecidos de P1 sem interpretador semântico: é melhoria técnica autônoma. O ganho semântico deve ser comparado com a fase Unicode: +19 supported, +4 refuted, +23 decisões, **+3,15 pontos percentuais** de cobertura; MAE 15,68→14,88 nos mesmos 25 casos. Todos continuam `needs_review`.

U+2212 é normalizado na vista matemática, preservando fonte/offsets. O ajuste adicional de en dash foi isolado no experimento anterior e não altera estes25 DEV. A falha de recorte de `÷` em P1_12 permanece distinta da correção Unicode já validada. O baseline bruto tem denominador diferente no MAE; comparar15,70 com14,88 sem essa ressalva seria incorreto. Nenhum novo teste foi executado neste diagnóstico: a independência da normalização é sustentada pelos resultados congelados das três fases e pelo relatório anterior.

## HOLDOUT e preservação

**Nenhum texto das 100 HOLDOUT foi lido nesta tarefa; nenhum resultado individual HOLDOUT foi inspecionado; nenhuma HOLDOUT foi executada.** Somente metadados de importação/IDs foram usados para selecionar DEV. Hashes dos artefatos anteriores foram conferidos sem interpretação de resultados HOLDOUT. O conjunto continua fechado e utilizável para futura avaliação, sujeito à separação DEV/HOLDOUT já estabelecida. Nenhuma conclusão desta análise foi ajustada a resultados HOLDOUT.

O snapshot inicial registra 688 arquivos preexistentes do repositório e 57 artefatos do experimento anterior. A conferência final, registrada em `validation.json`, verifica preservação byte a byte, HEAD, hashes das fontes DEV, cardinalidades, IDs, offsets e correspondência facts→bridge→decisão. Scripts de análise ficaram temporários em `/tmp`; o repositório recebe apenas este relatório e novos artefatos diagnósticos. Nenhum arquivo de implementação, prompt, checker, bridge, pauta ou teste foi alterado. As mudanças que já existiam na árvore de trabalho permanecem preservadas.

## Entregáveis

- [funnel.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_diag_01/funnel.json)
- [failure_classes.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_diag_01/failure_classes.json)
- [cases_analysis.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_diag_01/cases_analysis.json)
- [summary_by_problem.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_diag_01/summary_by_problem.json)
- [source_access_manifest.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_diag_01/source_access_manifest.json)
- [preservation_before.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_diag_01/preservation_before.json)
- [validation.json](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_semantic_diag_01/validation.json)


A recomendação B é uma direção para a próxima hipótese experimental, não uma autorização técnica de promoção. Os dados dos 25 DEV sustentam melhorar o vínculo entre evidência escrita e obrigação matemática; não sustentam ampliar Lean ou modificar pontuação para compensar evidência que não chegou aos verificadores.
