# C1 — correções da ponte e revalidação P1 (FIX 01)

Data: 2026-11-04. HEAD preservado: `6fe808fa693b7e0d662dd49c498e6b575dd9d47f`.
Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1`.

## Resultado

As três causas forenses foram corrigidas na ponte experimental. Testes direcionados com as interpretações JSON já observadas recuperam b=5 em `b_complete`, `b_equivalent_algebra` e no item b do caso composto; recuperam a identificação de `a_only_inverse`; e preservam identificação/montagem quando a sugestão de `a_complete` é FORMAL. A integração real do caso composto retorna **20 pontos (3+5+6+6)**, com as duas obrigações formais provadas pelo Lean existente.

**598 testes distintos aprovados, 0 falhas, 0 skipped.** Nenhum piloto foi executado nesta tarefa. Estes resultados são de testes direcionados com providers de extração injetados, não evidência de nova amostragem de respostas do LLM. A confirmação de desempenho do extractor após as correções depende do piloto `_02` ainda não executado.

## 1. Mudanças e vínculo com a causa forense

| Arquivo alterado | Causa | Mudança |
|---|---|---|
| `claim_router.py` | FORMAL sugerido apagava obrigações determinísticas | Remove a rejeição da evidência pela sugestão incompatível. O registry e o tipo de claim determinam a rota efetiva; apenas duas obrigações podem ir ao Lean. |
| `obligation_mapper.py` | Sugestão de rota impeditiva; 137 associado ao resultado | Registra suggested_route, effective_route e route_override_reason=obligation_registry. Corrige o papel de resposta literal isolada do item a, mantendo suggested_obligation_candidates e mapping_override_reason. |
| `verification.py` | Cadeias opacas; UNPROVED sem execução | Projeta igualdades adjacentes já escritas com a gramática existente; preserva pai, segmentos, ordem e offsets. Introduz FORMAL_NOT_ATTEMPTED e evidência de execução formal. |
| `engine.py` | Rastreabilidade epistemológica no wrapper | Encaminha formal_attempted também nos resultados estruturais de Current/fallback. Não modifica o assessment nem o pipeline Current. |
| `scripts/evaluation/run_tme_semantic_formal_c1.py` | Métricas confundiam rota com execução | Acrescenta formal_not_attempted, formal_attempts e formal_execution_unknown com definições explícitas. |
| `tests/test_tme_semantic_formal_c1.py` | Contratos antigos de router/status | Atualiza expectativas para sugestão sobrescrita e ausência de tentativa. |
| `tests/test_tme_semantic_formal_c1_lean.py` | Revalidação formal sem mocks de prova | Exercita sugestão FORMAL compartilhada e acrescenta o caso composto real de 20 pontos. |

Os quatro primeiros arquivos ficam em `app/confia_lean_auditor/experimental/tme_semantic_formal/`.

Arquivos novos desta tarefa:

- `tests/test_tme_semantic_formal_c1_fix.py`: 45 testes parametrizados/direcionados, incluindo os 21 casos para equivalência integral do wrapper Current.
- `tests/fixtures/tme_semantic_formal_c1/fix_replay_claims.json`: nove interpretações já registradas, contendo apenas case_id/evidence; sem notas, gold ou resultados de corretor. As fontes vêm da fixture source-only original, preservada.
- `docs/audits/TME_P1_CHECKER_COVERAGE_01.md`: matriz de 21 obrigações.
- `docs/audits/TME_SEMANTIC_FORMAL_C1_FIX_01.md`: este relatório.

O relatório forense anterior já estava não versionado e permaneceu intacto. Não houve alteração de checker matemático, SemanticSufficiencyGate, registry/estrutura das 21 obrigações, pauta/pontos, Statement Lean, teorema, ScoreClosurePolicy, prompt ou transporte do extractor.

### 1.1 Cadeias escritas de b

Para `A=B=C`, a projeção reaproveita `generic_math.candidate_spans` e entrega os candidatos **A=B** e **B=C**, nessa ordem. Não cria A=C nem calcula uma versão correta. A ativação é limitada ao item b, claim expression, múltiplas igualdades escritas e compatibilidade textual de fonte/normalização. A gramática e os checkers existentes validam cada segmento.

Cada evento de projeção conserva `evidence_id`, `parent_source_span`, `parent_normalized_claim`, `derived_source_span`, `derived_expression`, `original_source_start/end`, `segment_index/count` e `derivation=written_adjacent_equality`. As evidências derivadas apontam para o mesmo claim pai; os registros têm identidades e slices próprios, revalidados pelo checker. O trecho-fonte original não é substituído.

Dois negativos testam a cadeia `(100a+10b+c)-(100c+10b+a)=98a-98c=97(a-c)`: fiel ao texto ela não satisfaz cancelamento/fatoração; com uma normalização artificialmente corrigida a projeção não aceita a alteração. Em ambos, score=0 para esses critérios. Pode existir suporte ao fato sintático de que uma subtração foi escrita; sem cancelamento válido isso não paga o bloco de 2 pontos. Não se transforma a cadeia incorreta em uma demonstração correta.

### 1.2 Sugestão de rota

A sugestão não possui veto. Uma expressão candidata a uma obrigação determinística recebe a rota DETERMINISTIC mesmo que o LLM sugira FORMAL. O registro conserva, por exemplo:

```json
{
  "suggested_route": "FORMAL",
  "effective_route": "DETERMINISTIC",
  "route_override_reason": "obligation_registry"
}
```

O mesmo claim pode apoiar obrigações de rotas diferentes. O tipo de claim, o contexto, a fonte e o checker continuam obrigatórios. Não foi criada uma rota formal para b nem fallback automático que converta falhas matemáticas em suporte semântico.

### 1.3 Literal 137

A recuperação exige simultaneamente: tipo expression; representação de literal inteiro pelo parser existente; normalização idêntica ao valor escrito; **o trecho ocupando todo o item a**; sugestões de item compatíveis; papel de resposta isolada correspondente à identificação do invertido no contrato P1; e aprovação posterior dos gates de contexto/atribuição e do checker `_check_a`.

A lista efetiva passa a conter somente `a.identifies_137`; a sugestão original `a.result_594` permanece no trace. Isso seleciona uma obrigação e **não concede ponto**. O fato `a.inverted_number_137` precisa ser verificado e validado pela ponte antes do AwardGate. Não se mapeiam montagem ou resultado a partir desse literal.

Negativos incluem 1137, 594, `731-594=137`, “Resultado: 137”, hipótese, abandono posterior, item b, falta de atribuição e cálculo lateral. Não ativam a recuperação ou não atravessam o gate de contexto. Essa correção é deliberadamente estreita; não tenta resolver genericamente papéis matemáticos em toda prosa.

## 2. Status epistemológicos

| Status / campo | Semântica |
|---|---|
| FORMAL_VERIFIED | Resultado positivo do checker Lean executado, com validação de identidade/grounding pela ponte. |
| FORMAL_REFUTED | Negação provada pelo checker existente; não basta a prova positiva falhar. |
| FORMAL_UNPROVED | Tentativa formal confirmada pelo contrato de execução, sem prova nem refutação atribuível. |
| FORMAL_NOT_ATTEMPTED | Nenhuma execução formal confirmada no caminho normal: payload/representação insuficiente, pré-requisito ausente, ausência de fato ou Lean desabilitado. Não é refutação. |
| FORMAL_ERROR | Falha técnica, preservada como incerteza, inclusive quando o processo nem chegou a iniciar. |
| formal_attempted | true/false quando o contrato existente permite confirmar execução/ausência; null em falhas técnicas ambíguas. |
| formal_execution_unknown | Conta erros técnicos PROCESS_ERROR/INVALID_PROOF cujo contrato legado não permite afirmar se o subprocesso foi iniciado. |

A confirmação usa o retorno do checker existente: proposição, arquivo e caminho de status/failure_category. Apenas uma rota FORMAL ou um objeto sem arquivo/proposição não confirma tentativa. Não foi necessário alterar os checkers para gerar novo campo de execução. `FORMAL_NOT_ATTEMPTED` não pertence ao conjunto de statuses positivos do AwardGate.

As métricas novas são aditivas: `formal_not_attempted` conta o status; `formal_attempts` conta resultados com execução confirmada; `formal_execution_unknown` evita tratar um erro pré-processo como tentativa conhecida. `formal_routes` continua contando linhas com rota, não execuções. Os artefatos `_01` não foram reclassificados em disco.

### Os cinco resultados antigos

| Caso | Antigo resultado | Resultado nos testes direcionados após a correção | Causa preservada |
|---|---|---|---|
| a_only_inverse | a.result_594 / FORMAL_UNPROVED | a.identifies_137 / DETERMINISTIC_VERIFIED; score 1; nenhuma rota formal | Mapping corrigido; o vínculo formal errado deixa de existir. |
| a_only_result | a.result_594 / FORMAL_UNPROVED | FORMAL_NOT_ATTEMPTED | Literal 594 não é igualdade escrita. |
| a_wrong_setup | a.result_594 / FORMAL_UNPROVED | FORMAL_NOT_ATTEMPTED | Montagem 731−173 não é a montagem contratada por a.result_594. |
| d_later_error | d.total_thirty / FORMAL_UNPROVED | FORMAL_NOT_ATTEMPTED | Pares/escolhas incorretos e produto 3×9, fora do contrato da obrigação. |
| d_only_difference_then_error | d.total_thirty / FORMAL_UNPROVED | FORMAL_NOT_ATTEMPTED | Literal 30, pares incorretos e escolhas/produto ausentes. |

Os quatro últimos testes habilitam use_lean=True, mas instalam um sentinela que falha se o checker Lean for chamado; todos passam, confirmando ausência de chamada. Separadamente, os testes Lean reais abaixo não instalam esse sentinela nem mocks de prova. Não se publicou um summary de piloto `_02` a partir desses testes.

## 3. Testes

Contagem distinta final, sem somar execuções intermediárias:

| Grupo | Passed | Failed | Skipped |
|---|---:|---:|---:|
| Contratos C1 existentes, atualizados | 77 | 0 | 0 |
| Novos testes de correção | 45 | 0 | 0 |
| C1 com Lean real (inclui caso composto) | 4 | 0 | 0 |
| Checker Lean aritmético compartilhado existente | 1 | 0 | 0 |
| Regressões existentes selecionadas | 471 | 0 | 0 |
| **Total** | **598** | **0** | **0** |

A seleção ampla inicialmente deixou 10 testes de fora; o teste Lean aritmético compartilhado foi executado isoladamente na suíte final, restando 9 fora da seleção. Não são skips. Não se afirma execução de toda a suíte do repositório.

As 471 regressões incluem `test_tme2_p1_pauta_bridge.py` (74 casos), `test_pauta_engine.py`, `test_student_proof_semantics.py`, `test_semantic_sufficiency.py`, `test_evidence_id_semantic.py`, `test_tme_hybrid_grader.py`, `test_semantic_claims.py` e `test_obligation_semantic.py`. Rede foi bloqueada e OPENAI_API_KEY removida somente do processo de regressões; não houve alteração do ambiente persistente nem chamada LLM real.

Resultado final da suíte C1 + Lean compartilhado: **127 passed in 75.83s**. Regressões: **471 passed, 10 deselected in 8.27s**. Logs em `/private/tmp/confia-c1-fix/final.log` e `/private/tmp/confia-c1-fix/regressions.log`.

Comando final executado:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0 \
  /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python \
  -m pytest -q -s -p no:cacheprovider \
  --basetemp=/private/tmp/confia-c1-fix/final-tests \
  tests/test_tme_semantic_formal_c1.py \
  tests/test_tme_semantic_formal_c1_fix.py \
  tests/test_tme_semantic_formal_c1_lean.py \
  tests/test_student_proof_semantics.py::test_real_arithmetic_negation_and_verified_claim \
  > /private/tmp/confia-c1-fix/final.log 2>&1
```

Os testes verificam os 21 IDs fechados, retorno numérico, ausência de crédito quando a extração está vazia, trace de checker para os awards, preservação dos 21 assessments/bridges Current, contexto, cadeias falsas, rotas, statuses e os casos reais. A fixture de replay não contém notas; expectativas nos testes expressam os contratos de pauta/checker já conhecidos, não consulta a gold.

### Lean real

Lean **4.28.0**, commit `7e01a1bf5c70fc6167d49c345d3bf80596e9a79b`.
Mathlib **`8f9d9cff6bd728b17a24e163c9402775d9e6a365`**.
`lake build` já estava preparado; não foi repetido nem houve download.

| Teste | Resultado | Evidência |
|---|---|---|
| test_real_p1_a_positive_and_refutation — 731−137=594 | PASS / FORMAL_VERIFIED | compiled=true; sugestão FORMAL preserva também obrigações D; score 3. |
| test_real_p1_a_positive_and_refutation — 731−137=584 | PASS / FORMAL_REFUTED | refutation_verified=true; sem crédito ao resultado; score 2 pela faixa de erro aritmético. |
| test_real_p1_d_counting_equality | PASS / FORMAL_VERIFIED | 3×10=30 compilado; pares e escolhas vinculados; score 4 sem exigir d.solve. |
| test_real_p1_complete_after_bridge_fixes | PASS | score 20; a.result_594 e d.total_thirty compilados; b=5; nenhum conflito/erro técnico. |
| test_real_arithmetic_negation_and_verified_claim (existente) | PASS | Verificação e refutação pelo checker compartilhado. |

Não há mocks de Lean/checker nos testes reais. O extractor é injetado com conteúdo conhecido; as provas executam o Lean do worktree. Nos positivos, stdout/stderr vazios. Para 731−137=584, a tentativa positiva registra `unsolved goals / ⊢ False`, e a negação compila com streams vazios: refutação esperada, não erro técnico. Certificados são gerados pelos templates existentes em `artifacts/student_claim_checks/`; nenhum teorema-fonte foi criado ou alterado manualmente. JSON integrais dos testes reais estão sob `/private/tmp/confia-c1-fix/final-tests/`, em `real-result.json`.

## 4. Checker Coverage

A matriz completa das 21 obrigações está em `docs/audits/TME_P1_CHECKER_COVERAGE_01.md`.

| Tipo primário exclusivo | Quantidade |
|---|---:|
| FORMAL_STRONG | 2 |
| DETERMINISTIC_STRONG | 19 |
| SEMANTIC_CHECKER | 0 primários; 19 rotas secundárias |
| CHECKER_GAP por obrigação sem checker | 0 |

Há limites de representação explícitos: literais sem igualdade nas rotas formais, notação não suportada, coleções não enumeradas e ausência de avaliação real da rota semântica. Zero gaps por obrigação não significa cobertura universal da linguagem natural. Nenhum desses limites autoriza crédito sem verificador. O relatório de cobertura distingue dependências lógicas, pedagógicas e de crédito.

## 5. Baseline preservado

Os módulos de TME_CURRENT, checkers, pauta e inputs de versionamento do auditor continuam inalterados. Os testes comparam **integralmente** `current_assessment` e `current_bridge` com `primary_audit` para cada um dos mesmos 21 textos, sob use_lean=False: igualdade de estrutura/conteúdo, não apenas de nota. O caminho matemático atual não foi substituído. As verificações Lean são exercitadas separadamente pelos testes reais.

A visão estrutural experimental do baseline/fallback ganhou apenas o campo de tentativa e as novas métricas. Isso não altera pontuação, fatos, assessment nem o comportamento de produção Current. Config hashes diferem naturalmente porque o código experimental mudou; não se afirma igualdade byte-a-byte de artefatos completos com latência, UUID e novos campos.

Os 46 JSON dos pilotos `_01`, a fixture original de 21 fontes, os IDs/manifest do piloto, o relatório forense e os módulos reutilizados foram conferidos por hashes e permaneceram intactos. Nenhum gold foi lido, nenhum holdout foi acessado e não houve expansão C1 para P2.

## 6. Piloto _02 preparado, não executado

São os mesmos 21 casos e os mesmos arquivos source-only/IDs. Os destinos `pilot_current_02` e `pilot_semantic_formal_02` foram verificados livres. **Não foram pré-criados**, porque o runner exige diretório novo com `exist_ok=False`; serão criados pelos comandos abaixo na execução autorizada. Nenhum `_01` será sobrescrito. Mantém-se modelo/esforço dos pilotos anteriores para comparabilidade, ambos configuráveis.

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1
export PYTHONPATH="$PWD/app"
export PYTHONDONTWRITEBYTECODE=1
C1_PYTHON=/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python
C1_MODEL=gpt-6.1-sol
C1_EFFORT=medium

"$C1_PYTHON" -m scripts.evaluation.run_tme_semantic_formal_c1 \
  --mode tme_current \
  --dataset tests/fixtures/tme_semantic_formal_c1/pilot_sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_c1/pilot_ids.json \
  --output-dir artifacts/evaluations/tme_semantic_formal_c1/pilot_current_02 \
  --model "$C1_MODEL" --reasoning-effort "$C1_EFFORT"

"$C1_PYTHON" -m scripts.evaluation.run_tme_semantic_formal_c1 \
  --mode tme_semantic_formal \
  --dataset tests/fixtures/tme_semantic_formal_c1/pilot_sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_c1/pilot_ids.json \
  --output-dir artifacts/evaluations/tme_semantic_formal_c1/pilot_semantic_formal_02 \
  --model "$C1_MODEL" --reasoning-effort "$C1_EFFORT"
```

## 7. Git e arquivos não commitados

SHA: `6fe808fa693b7e0d662dd49c498e6b575dd9d47f`.
Sem staging, commit ou push. O diagnóstico forense listado abaixo é anterior a esta correção e não foi editado.

```text
 M app/confia_lean_auditor/experimental/tme_semantic_formal/claim_router.py
 M app/confia_lean_auditor/experimental/tme_semantic_formal/engine.py
 M app/confia_lean_auditor/experimental/tme_semantic_formal/obligation_mapper.py
 M app/confia_lean_auditor/experimental/tme_semantic_formal/verification.py
 M scripts/evaluation/run_tme_semantic_formal_c1.py
 M tests/test_tme_semantic_formal_c1.py
 M tests/test_tme_semantic_formal_c1_lean.py
?? docs/audits/TME_P1_CHECKER_COVERAGE_01.md
?? docs/audits/TME_SEMANTIC_FORMAL_C1_FIX_01.md
?? docs/audits/TME_SEMANTIC_FORMAL_C1_FORENSIC_01.md
?? tests/fixtures/tme_semantic_formal_c1/fix_replay_claims.json
?? tests/test_tme_semantic_formal_c1_fix.py
```

## Limites da conclusão

Os testes demonstram a recuperação das representações/vínculos observados e a preservação dos controles existentes. Não demonstram que toda futura saída do extractor será compatível, nem que SEMANTIC terá qualidade suficiente em prosa livre. O próximo passo continua sendo o piloto P1 autorizado, sem expansão para P2. Esta tarefa termina com os comandos preparados.

Documentos relacionados: [auditoria forense](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/docs/audits/TME_SEMANTIC_FORMAL_C1_FORENSIC_01.md); [matriz de cobertura](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1/docs/audits/TME_P1_CHECKER_COVERAGE_01.md).
