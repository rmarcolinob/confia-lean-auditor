# Experimento B — contrato histórico e protocolo

Inspeção prévia à implementação, base `8f50835f939110105eb20b8ae6fd6a78bbaa2649`.
Fontes inspecionadas: `student_claims/schemas.py`, os três
`student_claims/extract_f2q*_student_claims.py`, `claims/extractors/ita2025f2q*.py`,
`lean/student_claim_checkers/ita2025f2q*.py`, seus registries,
`rubric/adjusters/ita2025f2q*.py`, `rubric/rubric_evaluator.py`,
`lean/{formal_step_evaluator,microclaim_evaluator,build_attempt,run_lean}.py`,
os três attempt builders e `problems/ITA2025F2Q*/{problem,rubric,microclaims}.json`.

## Tipos, payloads consumidos e mapeamento

Todos os campos abaixo são obrigatórios para o adaptador. Inteiros estritos;
nenhum texto livre é interpolado como expressão Lean. Campos descritivos `rhs`,
`formula_text`, `ratio_text` presentes em alguns extractors históricos não são
consumidos pelo checker e não são enviados pelo adaptador.

| claim_type (prefixo f2qX_student_) | Payload do checker | Item(s) |
| --- | --- | --- |
| f2q1_student_power_reduction | exponent:int, const:int, coeff:int; powRem exponent = (const,coeff) | power_reductions |
| f2q1_student_reduced_form | form_kind: enum abaixo | reduced_polynomial_form |
| f2q1_student_coefficient_system | sum_lhs: enum abaixo, sum_rhs:int, a_equation_kind:a ou neg_a, a_rhs:int | coefficient_system |
| f2q1_student_final_answer | a:int, b:int | final_answer |
| f2q5_student_log_power_decomposition | total_log_scaled:int, integer_part_scaled:int, mantissa_scaled:int | log_power_decomposition |
| f2q5_student_mantissa | mantissa_scaled:int | mantissa_identification |
| f2q5_student_digit_log_bounds | log5_scaled:int, log6_scaled:int | digit_log_bounds |
| f2q5_student_between_bounds | left_scaled:int, middle_scaled:int, right_scaled:int | mantissa_between_bounds |
| f2q5_student_final_digit | digit:int | final_digit |
| f2q6_student_probability_formula | formula_kind: enum abaixo | probability_formula |
| f2q6_student_ratio_formula | ratio_kind: enum abaixo | ratio_comparison, maximizers_identification |
| f2q6_student_final_answer | values:list[int] | final_answer |

F2Q1 form_kind: `correct`=(a+b)x-a; `wrong_const_sign`=(a+b)x+a;
`wrong_coeff_minus`=(a-b)x-a; `wrong_coeff_swapped_minus`=(b-a)x-a.
`sum_lhs` aceita somente `candidateA + candidateB` ou `candidateB + candidateA`,
as duas representações emitidas pelo extractor histórico. O checker original
aceita qualquer string aqui; o adaptador fecha essa entrada para impedir Lean arbitrário.
Expoentes do experimento: 57, 14, 7, exatamente os extraídos historicamente.

F2Q5: escala inteira 10000 (47,7100 → 477100, 0,7100 → 7100).
F2Q6 formula_kind: `correct`=C(n-1,3)/2^n;
`wrong_choose_n_3`=C(n,3)/2^n;
`correct_numerator_wrong_denominator_n_minus_1`=C(n-1,3)/2^(n-1).
ratio_kind: `correct`=n/(2n-6); `wrong_n_minus_1_over_2n`=(n-1)/(2n);
`wrong_n_minus_1_over_2n_minus_6`=(n-1)/(2n-6);
`wrong_n_over_2n`=n/(2n); `wrong_n_over_2n_minus_8`=n/(2n-8).
Os rótulos correct/wrong são identificadores históricos de formas sintáticas,
não pedidos de julgamento matemático ao LLM.

## Chamadas e limites formais

`extract_student_claims(problem_id, solution)` despacha para o extractor histórico;
`check_student_claims_for_problem(problem_id, claims, run_id)` despacha para
`check_f2qX_student_claims`, que chama `check_one_f2qX_student_claim` por claim.
Cada checker deriva statement/método internamente, gera um arquivo e executa
`lake env lean arquivo`, timeout 90s. Status: verified, failed, unsupported, error.
O adaptador experimental redireciona CHECK_DIR e ROOT_DIR apenas durante a chamada,
restaurando-os depois; não modifica os arquivos históricos. Execução serial.
Comentários Lean recebem representação JSON do trecho, com delimitadores de
comentários neutralizados; o source_span original permanece no registro de evidência.

A probabilidade F2Q6 é testada em n=6,7; a razão em n=4..9.
Esses checks não demonstram sozinhos a derivação probabilística ou máximo global.
O caminho comum dos dois modos usa os mesmos formal steps, builders, microclaims e
certificados históricos para verificar as obrigações exigidas pela pauta.
Não introduz novos tipos de StudentClaim nem teoremas.

## Dependências históricas

F2Q1: power_reductions → reduced_polynomial_form → coefficient_system → final_answer.
F2Q5: log_power_decomposition → mantissa_identification;
mantissa_identification + digit_log_bounds → mantissa_between_bounds → final_digit.
F2Q6: probability_formula → ratio_comparison → maximizers_identification → final_answer.
Os itens finais têm required_microclaim_ids vazio: resposta final verificada pode
receber seus pontos sem exigir a cadeia completa. Os demais seguem os microclaims.
O avaliador histórico de microclaims verifica dependências em duas passagens;
esta implementação preserva esse comportamento. Builders já impõem a cadeia.
Adjusters só zeram itens com failed; unsupported/error não reduzem automaticamente.
O mapa negativo da razão F2Q6 alcança também maximizers_identification.

## Política comum v2 — correção da assimetria

Esta revisão substitui a política inicial. O replay positivo de agosto permanece
como artefato histórico, mas NÃO define mais o score do braço FORMAL_OFFLINE.
Os artefatos da validação inicial permanecem intactos em
`artifacts/evaluations/semantic_formal_b_validation_01`.

A única variável experimental é a extração/contextualização. Depois dessa etapa:

```
Extractor histórico → conversão declarada ┐
                                        ├→ EvidenceUnit → adapt_claim → checkers históricos
SemanticExtractorV2 → validação textual ┘
→ evidence_bridge → mesmos formal steps/builders/Lean/microclaims
→ formal_award_gate → final_score
```

`EvidenceUnit` contém evidence_id, claim_type, normalized_payload, source_span
opcional, assertion_status, polarity, scope, hypothetical, abandoned,
context_policy, extractor_mode e metadados de provenance. Os dois conversores
retornam exatamente a classe EvidenceUnit, não subclasses, antes do adaptador.
O contrato de payload e os 12 tipos de StudentClaim continuam iguais nos dois modos.

No offline, o contexto é sempre declarado como asserted, positive, main_argument,
hypothetical=false, abandoned=false, context_policy=legacy_context_assumed.
Isso é uma hipótese operacional do extractor histórico, **não uma inferência**.
Se raw_text histórico não for substring literal, source_span=null e
provenance_limitations=[source_span_unavailable]. Não se inventa um trecho.
Essa ausência não participa de qualquer condição de crédito.

No semântico, SemanticStudentClaim é a fronteira de validação do LLM:
source_span é obrigatório, não vazio e substring literal. O cliente não pode
fornecer extractor_mode ou context_policy para contornar essa validação.
Os campos contextuais vêm do SemanticExtractorV2; o conversor apenas os preserva.

`evaluate_evidence` é o único fluxo após os conversores. Nenhum modo usa crédito
textual inicial, promoção positiva do replay, evaluate_rubric ou adjuster para
atribuir pontos. Os módulos históricos continuam sem alteração. Seus mapas
claim→item são usados por ambos os modos. O bloqueio por failed ocorre no gate
comum e no bridge comum, inclusive para evidência marcada como abandonada.

`formal_award_gate` não recebe modo. Usa exatamente as mesmas condições:
claim mapeado e ligado ao resultado do checker por ID/tipo/payload/problema;
status verified; asserted; positive; não hipotético nem abandonado;
main_argument/final_conclusion; nenhum failed conflitante; obrigação satisfeita.
Os pontos vêm somente de rubric_config. `final_score` soma cada item uma única vez
e rejeita IDs duplicados ou valores fora de [0,10]. Claims repetidos não multiplicam
pontos. `extractor_mode` e `context_policy` são copiados apenas para auditoria.

As obrigações também são comuns: power_reductions exige os três expoentes 57/14/7;
maximizers_identification exige razão e resposta final verificadas; os demais itens
seguem os microclaims/dependências históricos. Respostas finais continuam com
required_microclaim_ids vazio, conforme a pauta congelada. Ausência de source_span
não altera presença de claim, obrigação, checker ou gate.

## Auditoria e métricas

Cada decisão por item contém `evidence` (incluindo claim_type, extractor_mode,
context_policy, source_span e lean_status), `used_evidence_ids`, `gate_decision`,
`award`, `rejection_reason`, `conflicting_evidence`, `obligation_satisfied`,
limite de pontos e microclaims necessários. Nenhuma decisão lê gold ou nota antiga.

Por caso e agregadas no summary, inclusive por problema:

- claims_extracted: unidades produzidas pelo modo efetivo;
- claims_submitted_to_checker: unidades entregues aos checkers;
- claims_sent_to_lean: checks com arquivo Lean ou resultado verified/failed;
- verified e failed: status dos student claim checks;
- rubric_items_with_evidence: itens com ao menos uma unidade mapeada;
- items_scored: itens com award positivo;
- items_rejected_for_context: rejeição por contexto de evidência verificada;
- items_rejected_for_insufficiency: ausência de evidência, falta de verificação
  ou obrigação formal não satisfeita;
- items_rejected_for_conflict: rejeição por failed conflitante;
- fallbacks e numeric_scores.

A razão principal da rejeição segue precedência: conflito, ausência de evidência,
contexto/falta de verificação, obrigação. Uma evidência contextual excluída continua
visível mesmo quando outra evidência permite pontuar o item. Contadores se referem
à execução efetiva; chamadas de API malsucedidas permanecem no registro API.
Fallback reextrai com FORMAL_OFFLINE e usa a mesma cadeia/gate/score.
Falha técnica terminal produz zero numérico pelo mesmo gate com evidência vazia,
registrando o erro; não é classificada como execução limpa no comparador.

A comparação exige a política `common_evidence_formal_award.v2` em ambos os lados,
mesma população, hashes de texto e código. Não mistura validações da política antiga.
Fallbacks e erros técnicos são separados da comparação das extrações bem-sucedidas.

## Piloto 18 — somente execução manual

Seleção inalterada: 252 IDs congelados (84 por questão), seis por questão após
ordenar IDs e tomar floor(i*(N-1)/5), i=0..5. Nenhum gold consultado.
Os arquivos population_b.json, pilot18_ids.json e pilot18_manifest.json não mudam.

Novo comando, com destino novo e explícito para esta revisão:

```bash
CONFIA_B_OUTPUT=/Users/LinMarcolino/Documents/confia-lean-auditor-semantic-formal-b/artifacts/evaluations/semantic_formal_b_common_gate_pilot18_01 \
  bash /Users/LinMarcolino/Documents/confia-lean-auditor-semantic-formal-b/scripts/evaluation/run_pilot18_b.sh
```

São os mesmos 18 casos em dois modos (36 avaliações), seguidos da comparação.
O diretório deve ser inexistente. Sem override, o script cria destino com prefixo
semantic_formal_b_common_gate_pilot18 e timestamp. Usa Python de
`../confia-lean-auditor/.venv`, cache `../confia-lean-auditor-leanstrong-aug/.lake`,
dataset `/Users/LinMarcolino/Library/CloudStorage/Dropbox/envio_v2.0/solucoes_v2.0.csv`
e modelo padrão gpt-4o-mini. O cliente usa OPENAI_API_KEY; ausência/falha gera fallback.
Overrides opcionais: CONFIA_B_MODEL, CONFIA_B_REASONING_EFFORT, CONFIA_B_PYTHON,
CONFIA_B_DATASET, CONFIA_B_LEAN_CACHE e CONFIA_B_OUTPUT.

## Arquivos desta revisão e validação

Novos: `semantic/evidence_unit.py`, `evaluation/structural_metrics.py`,
`tests/test_common_award_gate_b.py`.
Alterados: `semantic/semantic_student_claim.py`, `semantic/semantic_claim_adapter.py`,
`evaluation/formal_award_gate.py`, `evaluation/semantic_formal_b.py`, os scripts
`run_ita_semantic_formal_b.py`, `compare_formal_vs_semantic_b.py`, `run_pilot18_b.sh`,
os testes `test_semantic_formal_b.py`, `test_semantic_formal_b_lean.py` e esta documentação.
O SemanticExtractorV2, os extractors históricos, checkers, Lean, rubricas e pesos
permanecem sem alteração.

Validação desta revisão em novo diretório exclusivo:
`artifacts/evaluations/semantic_formal_b_validation_02_common_gate`.
Os testes usam mocks de API e exemplos sintéticos, nunca casos do piloto.
O piloto e o benchmark de 252 casos NÃO foram executados.

### Resultados da validação v2

Suíte completa: **257 testes aprovados** (236 testes experimentais de schema,
adaptadores, gate, CLI e invariância; 15 regressões históricas dos adjusters;
6 integrações Lean). Relatório definitivo: `complete.xml`; resumo: `summary.json`
no novo diretório de validação. A primeira coleta revelou uma incompatibilidade
de anotação Optional com Python 3.9, corrigida sem adicionar dependências;
o relatório dessa coleta também foi preservado.

Comprovações Lean com dados sintéticos:

- Q1/Q5/Q6 completas: 10/10 nos dois modos, status verified;
- dígito errado: failed, sem crédito;
- falha de API simulada: fallback numérico igual ao offline, 2/10;
- apenas x^57=-1: check verified, mas score 0 nos dois modos por obrigação incompleta;
- hipótese sobre dígito 5: mesmo statement e status Lean verified nos dois modos;
  offline assume asserted e recebe 2; semântico marca hypothetical e recebe 0.
  Essa diferença é produzida exclusivamente pelo contexto extraído no mesmo gate.

Os testes de invariância cobrem os 12 tipos de claims, quatro status Lean e três
situações contextuais, trocando rótulos de modo/política e removendo o source_span
histórico sem alterar a decisão. Também verificam ausência de branch de modo no
gate e no fluxo compartilhado, igualdade dos pontos da pauta, ausência de acesso
a arquivos durante o gate, bloqueio de gold e prevenção de dupla contagem.

Comando usado para a suíte completa (apenas validação sintética; não é o piloto):

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-semantic-formal-b
CONFIA_B_LEAN_RUNTIME="$PWD/artifacts/evaluations/semantic_formal_b_validation_02_common_gate/execution" \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app \
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -B -m pytest \
  tests/test_semantic_formal_b.py tests/test_common_award_gate_b.py \
  tests/test_semantic_formal_b_lean.py tests/test_f2q1_rubric_adjustments.py \
  tests/test_f2q5_rubric_adjustments.py tests/test_f2q6_rubric_adjustments.py \
  -q -p no:cacheprovider
```

Uma nova execução de validação deve usar novo diretório para basetemp/JUnit,
sem sobrescrever os relatórios salvos. O diretório anterior foi conferido por
snapshot de metadados de 126.086 entradas e hashes dos artefatos fora do runtime;
os snapshots antes/depois confirmam preservação. O core histórico foi novamente
conferido contra os blobs do commit congelado. Nenhuma chamada de API, leitura
de gold, execução do piloto ou benchmark ocorreu nesta revisão.
