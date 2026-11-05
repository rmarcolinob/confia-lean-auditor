# C1 — implementação paralela de TME Semantic Formal, somente P1

Base e HEAD: `1b3daea41ba4ce31c0cfd35dd07907da3d03669f`. Data: 2026-11-04.
Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1`.

## Arquitetura e preservação do baseline

A entrada explícita é `confia_lean_auditor.experimental.tme_semantic_formal.engine.evaluate`.
O runner é `scripts/evaluation/run_tme_semantic_formal_c1.py`. Ambos rejeitam problemas diferentes de `TME2026P1`/`TME2_P1_PILOT`.

```text
texto integral e fronteiras de itens
→ SemanticExtractorTME (interpretação JSON, sem pontos ou julgamento de verdade)
→ TMEEvidenceUnit (span literal, IDs/offsets/identidade calculados localmente)
→ ObligationMapper (tipo, item, contexto, atribuição e compatibilidade)
→ ClaimRouter (rota efetiva controlada pelo registro P1)
→ checkers P1 existentes / Lean existente / SemanticSufficiencyGate
→ EvidenceReconciler existente + conflito bloqueante C1
→ AwardGate → PautaEngine existente → ScoreClosurePolicy
→ resultado numérico com rastreabilidade
```

O pacote novo fica em `app/confia_lean_auditor/experimental/`, fora das árvores que `accepted_audit.audit_context` percorre para versionar o auditor atual. Nenhum dispatcher, endpoint, variável global de ativação, checker, pauta ou módulo preexistente foi modificado. O diagnóstico anterior também permaneceu intacto.

O perfil `tme_current` do runner é a composição existente `primary_audit`: extração local, suplemento semântico desabilitado pelo `supplement_scope` já existente, `use_lean=True`, ponte P1 e pauta atuais. Essa definição explícita evita depender de uma variável de ambiente e evita uma segunda chamada de interpretação durante fallback. Não é o experimento híbrido antigo. O resultado original fica em `current_assessment`/`current_bridge`; o wrapper experimental fornece sua visão numérica sem modificar esses objetos ou o comportamento da aplicação.

Componentes reutilizados:

- `evidence_units`, `SourceBinding`, `MathClaimRecord`, projeção/grounding semânticos e `supplement_scope`;
- parser de fronteiras corrigido, `link_evidence`, `context_gate` e requisitos por obrigação;
- `collect_tme2_p1_digital`, `verify_tme2_p1_digital`, canonicalização e checker aritmético Lean;
- `FactResult`, `AuditorFactBundle`, validação da ponte e `bridge_tme2_p1`;
- `SemanticSufficiencyGate`, validação de seu retorno e transporte configurável;
- precedência/traces de `EvidenceReconciler`, `HybridEvidencePolicy` e `PautaEngine`.

Componentes novos: contrato C1, extractor, registro das 21 obrigações, mapper, router, adaptadores de verificação, conflito bloqueante, AwardGate, ScoreClosurePolicy, composição e runner.

## Contratos e decisões

### Extração e identidade

O extractor recebe somente enunciado, solução integral, tipos fechados, catálogo matemático das 21 obrigações, schemas de payload dos verificadores e unidades de fonte. Não recebe pontos, gold, solução oficial, resultado do baseline ou decisão de outro corretor. O schema é fechado; retorno inválido e falha de API produzem fallback identificado.

`TMEEvidenceUnit` contém todos os campos pedidos. O modelo seleciona `source_evidence_ids` existentes e copia o envelope literal correspondente. O sistema verifica o slice, calcula offsets Unicode `[start,end)` e gera identidade `E###:claim:<digest>`. Os IDs de unidade originais continuam em `source_evidence_ids`; vários claims podem compartilhar uma unidade. Duplicatas idênticas são removidas; interpretações contextuais divergentes do mesmo claim geram conflito bloqueante. A identidade inclui hash da fonte e não é confundida com um ID global entre casos.

Campos de pontuação, verificação formal e offsets calculados pelo modelo são rejeitados. Claims qualitativos conservam argumento literal. Uma expressão/coleção reconhecida localmente não pode escapar do checker simplesmente recebendo a etiqueta `qualitative`.

### Contexto, mapeamento e verificadores

O contexto exige atribuição, asserção positiva, ausência de hipótese/abandono e escopo principal ou conclusão final. As declarações do extractor não bastam: os controles locais leem a fonte e o contexto completo/revisões. Sugestões de obrigação precisam pertencer ao registro, corresponder ao item e ao tipo permitido e, para crédito matemático, resultar no fato efetivamente emitido pelo checker daquela obrigação.

O adaptador matemático entrega aos checkers somente registros derivados dos candidatos elegíveis. Mantém a revalidação de origem pelo checker. Uma auditoria local adicional da fonte integral funciona apenas como veto por contradição: evidência positiva omitida pelo extractor não concede crédito C1 silenciosamente.

Dois requisitos dependem também da fonte completa: `a.arithmetic_error_only` exige que o diagnóstico original do item confirme erro único; selecionar uma igualdade e omitir outro erro não basta. Representações por símbolo novo, como `R=100c+10b+a`, também são confrontadas com outras definições escritas desse símbolo. Definições incompatíveis omitidas pelo extractor geram conflito bloqueante, com seus IDs de fonte registrados.

As duas obrigações formais não têm promoção semântica nem substituição determinística no C1. Se não existir igualdade inteira suportada ou se Lean estiver desabilitado em um teste, o resultado fica `FORMAL_UNPROVED`. O runner público executa Lean. O resultado isolado `594` não é transformado em uma igualdade inventada.

Verificação semântica só ocorre em obrigações que a permitem e exige o gate independente. O valor `satisfied` usado internamente para chamar `prepare()` é apenas a adaptação ao protocolo existente, nunca uma conclusão do extractor nem autorização de crédito. O gate recebe a evidência literal, sem rationale/confiança do primeiro estágio. Suporte semântico mantém status e origem semânticos.

Dependências lógicas, pedagógicas e de crédito estão separadas no registro. Não se exige toda a solução oficial: por exemplo, `b.reversed_number` pode conceder seu crédito sem fatoração; `d.total_thirty` exige os pares e escolhas necessários ao checker, mas não exige que os passos de `d.solve` tenham sido escritos.

### Conflitos e pontuação

Suporte contra refutação, contradição semântica, fatos conflitantes na fonte integral ou contexto contraditório do extractor bloqueiam a obrigação. O relatório conserva IDs dos claims e das unidades de contraevidência, inclusive unidades omitidas pelo extractor, mais spans e coordenadas originais.

Não há resolução automática nesta versão. O utilitário de resolução só admite a regra explícita `same_bound_claim_formal_over_semantic`, com vínculo idêntico e resultado formal conclusivo; resultados formais incompatíveis não podem ser resolvidos por confiança, ordem ou nota preferida. AwardGate rejeita `resolved=true` sem regra e sem resultado correspondente à regra executada. A rota padrão conserva conflitos sem resolução e não concede crédito nessa obrigação.

`FORMAL_UNPROVED`, `FORMAL_ERROR` e `FORMAL_REFUTED` permanecem distintos. `DETERMINISTIC_FAILED` inclui falta de fato suficiente; o campo `mathematical_refutation` diferencia essa ausência de uma refutação local efetiva. Um erro técnico não é um erro matemático.

Pontos pertencem às regras/faixas da pauta, não aos claims. `credits` percorre somente faixas/caminhos selecionados e conta cada regra paga uma vez. Todos os testemunhos de um `all_of` compartilham o valor daquele bloco. `formal_awards`, `deterministic_awards` e `semantic_awards` particionam os créditos sem somá-los em duplicidade; blocos mistos mantêm `routes` e todos os testemunhos. A classificação do bloco prioriza semântico quando presente, depois formal, depois determinístico; não significa que todo testemunho daquele bloco tenha a mesma origem.

`ScoreClosurePolicy` usa `known_points` quando o assessment original tem `score=None`, conserva demais créditos válidos e registra `technical_uncertainty`/`review_recommended`. O assessment original, intervalo e erros permanecem no artefato. Fallback registra `requested_mode=TME_SEMANTIC_FORMAL`, `effective_mode=TME_CURRENT_FALLBACK`, `fallback_used=true` e motivo. Falha do gate de suficiência é local à obrigação e não apaga crédito independente.

## Registro das 21 obrigações

Fonte executável: `app/confia_lean_auditor/experimental/tme_semantic_formal/obligation_registry.py`.
Na tabela, **D/S** significa `DETERMINISTIC` para representação suportada e `SEMANTIC` para prosa elegível com sufficiency independente. “Gate” refere-se a `SemanticSufficiencyGate`; não implica novo checker matemático.

Os checkers `_check_a`…`_check_d` ficam em `lean/student_claim_checkers/tme2_p1.py`. **Aritmético Lean** é `_Checks.arithmetic → lean/student_claim_checker.check_one_student_claim`.

| obligation_id | rubric_item | route | checker | sufficiency_policy | award_type |
|---|---|---|---|---|---|
| `a.identifies_137` | a | D/S | `_check_a` / Gate | inverso explícito | determinístico/semântico |
| `a.constructs_subtraction` | a | D/S | `_check_a` / Gate | subtração escrita e ordenada | determinístico/semântico |
| `a.result_594` | a | FORMAL | `_check_a` + aritmético Lean | igualdade inteira escrita e provada | formal |
| `a.arithmetic_error_only` | a | D/S | `_check_a` / Gate | diagnóstico de erro único na montagem correta | determinístico/semântico |
| `b.reversed_number` | b | D/S | `_check_b` / Gate | representação do invertido | determinístico/semântico |
| `b.subtraction` | b | D/S | `_check_b` / Gate | diferença das expansões posicionais | determinístico/semântico |
| `b.middle_cancellation` | b | D/S | `_check_b` / Gate | cancelamento desenvolvido | determinístico/semântico |
| `b.factorization` | b | D/S | `_check_b` / Gate | expansão para fatoração, sem tautologia | determinístico/semântico |
| `c.uses_expression` | c | D/S | `_check_c` / Gate | uso explícito da expressão | determinístico/semântico |
| `c.difference_domain` | c | D/S | `_check_c` / Gate | limites e domínio inteiro explícitos | determinístico/semântico |
| `c.complete_list` | c | D/S | `_check_c` / Gate | enumeração sem omissões | determinístico/semântico |
| `c.no_extraneous_values` | c | D/S | `_check_c` / Gate | enumeração sem extras | determinístico/semântico |
| `c.single_list_error` | c | D/S | `_check_c` / Gate | exatamente um erro na lista | determinístico/semântico |
| `c.several_correct` | c | D/S | `_check_c` / Gate | dois valores distintos corretos | determinístico/semântico |
| `c.pattern_recognized` | c | D/S | `_check_c` / Gate | fórmula ligada à lista | determinístico/semântico |
| `c.some_correct` | c | D/S | `_check_c` / Gate | pelo menos um valor correto | determinístico/semântico |
| `d.equation` | d | D/S | `_check_d` / Gate | equação escrita | determinístico/semântico |
| `d.difference_six` | d | D/S | `_check_d` / Gate | diferença entre dígitos escrita | determinístico/semântico |
| `d.digit_pairs` | d | D/S | `_check_d` / Gate | pares ordenados exatos | determinístico/semântico |
| `d.middle_choices` | d | D/S | `_check_d` / Gate | escolhas do dígito central | determinístico/semântico |
| `d.total_thirty` | d | FORMAL | `_check_d` + aritmético Lean | pares, escolhas e produto escrito provado | formal |

## Arquivos

Criados nesta implementação:

```text
app/confia_lean_auditor/experimental/__init__.py
app/confia_lean_auditor/experimental/tme_semantic_formal/__init__.py
app/confia_lean_auditor/experimental/tme_semantic_formal/evidence_unit.py
app/confia_lean_auditor/experimental/tme_semantic_formal/semantic_extractor.py
app/confia_lean_auditor/experimental/tme_semantic_formal/obligation_registry.py
app/confia_lean_auditor/experimental/tme_semantic_formal/obligation_mapper.py
app/confia_lean_auditor/experimental/tme_semantic_formal/claim_router.py
app/confia_lean_auditor/experimental/tme_semantic_formal/verification.py
app/confia_lean_auditor/experimental/tme_semantic_formal/reconciliation.py
app/confia_lean_auditor/experimental/tme_semantic_formal/award_gate.py
app/confia_lean_auditor/experimental/tme_semantic_formal/score_closure.py
app/confia_lean_auditor/experimental/tme_semantic_formal/engine.py
scripts/evaluation/run_tme_semantic_formal_c1.py
tests/test_tme_semantic_formal_c1.py
tests/test_tme_semantic_formal_c1_lean.py
tests/fixtures/tme_semantic_formal_c1/pilot_sources.json
tests/fixtures/tme_semantic_formal_c1/pilot_ids.json
tests/fixtures/tme_semantic_formal_c1/pilot_manifest.json
docs/audits/TME_SEMANTIC_FORMAL_C1_IMPLEMENTACAO_01.md
```

Arquivos preexistentes modificados: **nenhum**. O diagnóstico `TME_SEMANTIC_FORMAL_C1_DIAGNOSTICO_01.md` já estava não versionado antes desta tarefa e não foi editado. Certificados automáticos dos checkers ficaram na pasta ignorada `artifacts/student_claim_checks/`; logs e snapshots de validação em `/private/tmp/confia-c1-implementation/`.

## Runner e piloto preparado

O input do runner é uma lista JSON fechada de `{case_id, problem_id, solution_text}` e um arquivo JSON de IDs. Campos extras, incluindo gold/notas, IDs repetidos/desconhecidos, outros problemas e paths identificados como holdout selado são rejeitados. Os caminhos são resolvidos e verificados antes da leitura. O output exige diretório novo.

Cada caso conserva os campos solicitados, fonte/hash, resultados dos verificadores, vínculos, decisão de suficiência/conflito/award, árvore da pauta e créditos com pontos. Configuração inclui SHA Git e hashes dos módulos experimentais, código reutilizado, runner, registro, pauta, transporte, toolchain e manifesto Lake. Isso distingue o código novo não commitado do SHA-base. O summary contém todas as métricas estruturais pedidas; as definições das contagens acompanham o JSON. No baseline/fallback, os resultados de verificação vêm dos fatos originais; extração e mapeamento C1 ficam vazios.

**Preparado, não executado:** 20 entradas digitais conhecidas de P1 e o caso composto já existente na regressão. A preparação projetou somente `id`, `item`, `text` da fixture antiga; nenhuma expectativa de pontos foi copiada, comparada ou enviada ao runtime C1. As expectativas das regressões antigas permanecem apenas em seus próprios testes.

Manifesto: `tests/fixtures/tme_semantic_formal_c1/pilot_manifest.json`.

```text
a_complete, a_single_arithmetic_error, a_only_inverse, a_only_result,
a_no_evidence, a_wrong_setup, b_complete, b_no_factorization,
b_only_expression, b_equivalent_algebra, c_complete, c_one_omission,
c_one_extraneous, c_several_with_pattern, c_few_results, c_no_evidence,
d_complete, d_no_count, d_later_error, d_only_difference_then_error,
p1_complete_regression
```

Comandos exatos preparados, **não executados**:

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1
export PYTHONPATH="$PWD/app"
export PYTHONDONTWRITEBYTECODE=1
C1_PYTHON=/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python
C1_MODEL=gpt-4o-mini-2024-07-18
C1_EFFORT=none

"$C1_PYTHON" -m scripts.evaluation.run_tme_semantic_formal_c1 \
  --mode tme_current \
  --dataset tests/fixtures/tme_semantic_formal_c1/pilot_sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_c1/pilot_ids.json \
  --output-dir artifacts/evaluations/tme_semantic_formal_c1/pilot_current_01 \
  --model "$C1_MODEL" --reasoning-effort "$C1_EFFORT"

"$C1_PYTHON" -m scripts.evaluation.run_tme_semantic_formal_c1 \
  --mode tme_semantic_formal \
  --dataset tests/fixtures/tme_semantic_formal_c1/pilot_sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_c1/pilot_ids.json \
  --output-dir artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_01 \
  --model "$C1_MODEL" --reasoning-effort "$C1_EFFORT"
```

Modelo e esforço são configuráveis; `none` omite o parâmetro de reasoning. Não há troca automática de modelo ou busca de parâmetros. A disponibilidade/compatibilidade de cada modelo será determinada pela API na execução autorizada e eventual falha será registrada como fallback. O caminho Python acima reutiliza o ambiente instalado; `PYTHONPATH` importa o código deste worktree.

## Testes e regressões

Contagem consolidada sem somar reexecuções intermediárias: **632 casos selecionados, 631 aprovados, 0 falhas, 1 skipped**. A seleção de regressões inicialmente excluiu 10 testes; um deles (aritmética Lean compartilhada) foi executado separadamente na suíte final, restando 9 não selecionados, fora da validação específica de P1.

| Grupo | Aprovados | Falhas | Skipped |
|---|---:|---:|---:|
| Regressões preexistentes | 550 | 0 | 1 |
| C1 unitário/contratos/adversarial | 77 | 0 | 0 |
| C1 integração Lean real P1 | 3 | 0 | 0 |
| Checker aritmético Lean real compartilhado preexistente | 1 | 0 | 0 |

A regressão cobre `test_tme2_p1_pauta_bridge.py` (74 casos), `test_pauta_engine.py`, `test_student_proof_semantics.py`, `test_semantic_sufficiency.py`, `test_scope_boundary.py`, `test_evidence_id_semantic.py`, `test_tme_hybrid_grader.py`, `test_semantic_claims.py`, `test_obligation_semantic.py` e `test_tme_accepted_integration.py`. Resultado: `550 passed, 1 skipped, 10 deselected in 73.11s`. Log: `/private/tmp/confia-c1-implementation/regressions.log`. O skip é o DEV congelado ausente em `test_scope_boundary.py`; nenhum outro dataset foi usado para substituí-lo. As expectativas preexistentes passaram sem alterações. Testes compartilhados podem validar rotinas de outros problemas já existentes; isso não representa implementação C1 para outros problemas.

Os testes novos cobrem os 23 requisitos da solicitação, contexto/revisões, IDs/offsets, promoção de rota, conflitos e precedência, crédito sem duplicação, conservação de pontos sob falha técnica, fallback, schema do runner, métricas, preservação de fonte e igualdade com o baseline. O teste de CLI usa um avaliador injetado e uma entrada sintética temporária; não executa o piloto preparado.

Comando final executado, exit code 0, resultado **81 passed in 54.94s**:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0 \
  /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python \
  -m pytest -q -s -p no:cacheprovider \
  --basetemp=/private/tmp/confia-c1-implementation/final-tests-v2 \
  tests/test_tme_semantic_formal_c1.py \
  tests/test_tme_semantic_formal_c1_lean.py \
  tests/test_student_proof_semantics.py::test_real_arithmetic_negation_and_verified_claim \
  > /private/tmp/confia-c1-implementation/c1-final-v2.log 2>&1
```

## Validação Lean real

`lake build` já havia sido concluído pelo usuário; não foi necessário repeti-lo ou baixar dependências. Ambiente confirmado nesta tarefa:

```text
Lean 4.28.0, arm64-apple-darwin24.6.0
Lean commit: 7e01a1bf5c70fc6167d49c345d3bf80596e9a79b
Mathlib HEAD: 8f9d9cff6bd728b17a24e163c9402775d9e6a365
```

Arquivo: `tests/test_tme_semantic_formal_c1_lean.py`. Os providers de extração são injetados; o checker, os subprocessos Lean e as provas não são mockados. Os certificados são produzidos pelos templates existentes.

| Teste | Proposição escrita | Resultado C1 | Resultado Lean |
|---|---|---|---|
| `test_real_p1_a_positive_and_refutation[731-137=594-FORMAL_VERIFIED-3]` | `((731 : ℤ)-137) = ((594 : ℤ))` | PASS / `FORMAL_VERIFIED` | `compiled=true`, `formal_status=verified` |
| `test_real_p1_a_positive_and_refutation[731-137=584-FORMAL_REFUTED-2]` | `((731 : ℤ)-137) = ((584 : ℤ))` | PASS / `FORMAL_REFUTED` | proposição falsa não compila; negação compila, `refutation_verified=true` |
| `test_real_p1_d_counting_equality` | `((3 : ℤ)*10) = ((30 : ℤ))` | PASS / `FORMAL_VERIFIED` | `compiled=true`, `formal_status=verified`; pares/escolhas vinculados |

Todos usam `norm_num`. Nos positivos, stdout/stderr vazios. Na igualdade falsa, stdout da tentativa positiva contém `error: unsolved goals` / `⊢ False`; stderr vazio. A prova de negação tem stdout/stderr vazios. Isso é refutação matemática esperada, não erro técnico: `failure_category=null`, nenhuma incerteza técnica nos três casos. O crédito de `a.result_594` é bloqueado no caso falso; os dois pontos remanescentes vêm dos critérios independentes da pauta.

Log completo, com status, streams, vínculos e caminhos dos certificados: `/private/tmp/confia-c1-implementation/c1-final-v2.log`. Os artefatos JSON integrais dos três testes estão sob `/private/tmp/confia-c1-implementation/final-tests-v2/`, em `real-result.json`.

## Estado Git e integridade

HEAD preservado: `1b3daea41ba4ce31c0cfd35dd07907da3d03669f`.
Nenhum arquivo preexistente foi alterado: conferência SHA-256 dos 732 arquivos versionados e do diagnóstico anterior, total de 733 arquivos. Os 19 arquivos novos permanecem não versionados; não houve staging nem commit. `git diff --check` sem erros.

`git status --short`:

```text
?? app/confia_lean_auditor/experimental/
?? docs/audits/TME_SEMANTIC_FORMAL_C1_DIAGNOSTICO_01.md
?? docs/audits/TME_SEMANTIC_FORMAL_C1_IMPLEMENTACAO_01.md
?? scripts/evaluation/run_tme_semantic_formal_c1.py
?? tests/fixtures/tme_semantic_formal_c1/
?? tests/test_tme_semantic_formal_c1.py
?? tests/test_tme_semantic_formal_c1_lean.py
```

## Limites explícitos

- Nenhum piloto, benchmark de acurácia ou chamada LLM real foi executado nesta implementação. Providers foram injetados nos testes; os testes Lean identificados como reais não usam mocks de prova.
- O input preparado usa cabeçalhos `(a)`…`(d)`. O parser reutilizado também reconhece as transições que já suporta. Não há inferência livre de itens; fonte sem fronteira reconhecida não autoriza crédito. Cabeçalhos repetidos exigem revisão explícita.
- Mantêm-se os limites de representação existentes, envelopes de até 2.048 caracteres e no máximo 160 claims por extração. Não foi criado CAS, checker Lean novo ou interpretação de reticências.
- A suficiência semântica continua sendo julgamento de modelo sob controles independentes; nunca é apresentada como certificação Lean. Evidência matemática não representável não recebe status formal por aproximação.
- Nenhum dado do `tme_holdout_eval_01` foi aberto ou executado. Não houve implementação P2–P5, staging, commit ou push.
