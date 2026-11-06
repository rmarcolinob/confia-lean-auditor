# TME P3 — Implementação da arquitetura unificada de discurso e veto

## 1. Base, escopo e resultado

**READY_FOR_P3_UNIFIED_REGRESSION.** Implementados o ledger auditável, o resolver central, a separação de admissão positiva/visibilidade e a autoridade única de veto. A prontidão refere-se à regressão integrada futura; não constitui validação independente de segurança ou generalização.

SHA inicial e final de HEAD: `f29547e65905c25bfc5ec873fa51a2c2b069b78f`. Worktree P3 inicialmente limpo. Código entregue **sem commit**, portanto esse SHA identifica a base, não um novo commit da implementação. A revisão executável é identificada também pelos hashes dos arquivos ao final deste documento. Versão local: `tme-semantic-formal-p3.v2-unified`.

Especificação: `docs/audits/TME_P3_UNIFIED_DISCOURSE_VETO_ARCHITECTURE_01.md`. Não houve mudança de política incompatível nem necessidade de tocar componentes protegidos. Houve atualização de testes unitários legados que exigiam autoridade direta de flags do modelo, fallback Current ou veto sem propagação já contratada. Isso é uma migração explícita de contrato, não revisão de expectativas de benchmark.

Nenhuma chamada real ao SemanticExtractor/OpenAI foi executada. Replays usaram `raw_output` gravado, provider local e cliente OpenAI proibido. Nenhum gold externo, holdout, Safety 03, tuning de prompt ou commit. A redação usa “regressão observada” deliberadamente.

## 2. Componentes implementados

- `source_adapter.py`: cláusula/asserted_content dentro do envelope, normalização conservadora, distinção member/exact_set e ponte de coordenadas nativas.
- `discourse.py`: estados, decisões imutáveis, snapshot com hash e resolver de relações locais/temporais.
- `veto_policy.py`: candidatos, contrato de dependências negativas, decisão central e reconciliação autenticada pela instância/snapshot.
- `unified.py`: coleta nativa, ledger conjunto, projeções, produtores, política e trace completo.
- `engine.py`, `mapper.py`, `abandonment.py`, `conflict_guard.py`: integração e retirada das antigas autoridades paralelas. `__init__.py` versiona o pipeline.

Fluxo efetivo:

```text
fonte + interpretação gravada/provider
  → registros nativos + EvidenceUnits originais
  → ledger / cláusulas / source binding
  → DiscourseStateResolver / snapshot
  → admissão positiva + visibilidade
  → checkers congelados / atomic guard / relação estrutural
  → VetoEligibilityPolicy / receipts por evidência
  → reconcile(policy, receipts)
  → award(witness, snapshot, receipts)
  → PautaEngine → ScoreClosure
```

## 3. Mapa antigo → novo dos 27 caminhos

| ID | Caminho antigo | Destino e autoridade nova |
| --- | --- | --- |
| V00 | Framing/limites | SourceDocument preservado; entrada inválida é erro, nunca refutação. |
| V01 | Extractor/schema/binding | Contrato/prompt intactos; indisponibilidade leva ao fallback nativo unificado. |
| V02 | Identidade/interpretações | Binding + canonical_id + resolver; conflito de flags não autoriza veto. |
| V03 | Flags/scope do modelo | Sinais originais no ledger; projeção admite somente estado ACTIVE validado. |
| V04 | Contexto local/anchor | Resolver valida cláusula, cabeçalhos e atribuição; normalização de payload continua exigida. |
| V05 | Representação | Adapter conservador + mapper; rejeição de payload não apaga claim do ledger. |
| V06 | ClaimProjection | Somente mapping elegível; offsets originais e projetados permanecem conferidos. |
| V07 | Filtros matemáticos | Assertions/roles existentes recebem projeção admissível; sem mudança no checker. |
| V08 | P3Checks/Lean | Matemática congelada produz receipts; refutação é candidato da política. |
| V09 | Dependências matemáticas | Composição só com claims atuais; contexto insuficiente não é refutação. |
| V10 | StrongP3Checks/combine | Inalterado; nenhuma conversão de FAILED para VERIFIED no adapter. |
| V11 | source_consistency | Mesmo componente; negativos recuperados alcançam conclusão por DependencyContract explícito. |
| V12 | Validação de fato/Lean | _validated_status preservado; resultado sem vínculo não ganha autoridade. |
| V13 | Agregados do bridge | Agregados mantidos no trace, sem comando de veto; policy recebe resultados por fato. |
| V14 | verify/IsolatedChecks | Recebe projeção por estado; erros continuam técnicos, sem falsa refutação. |
| V15 | abandonment/conflict_visibility | Branch autônomo removido; API de compatibilidade delega ao resolver. |
| V16 | Safety regular | Resultados verificáveis guard_only; mesma política, sem award de guard. |
| V17 | Atomic membership | Checker finito preservado; somente candidato negativo, não decide blocked. |
| V18 | Leitura nativa | Inventário original + tradução de coordenadas + EvidenceUnits nativas no mesmo snapshot. |
| V19 | Segundo veto determinístico | Substituído por verify sobre projeção nativa resolvida, com os mesmos StrongP3Checks; não consome score/conflito bruto como veto. |
| V20 | Reconciliação | reconcile(policy, decisions) aceita somente decisões emitidas pela instância/revisão corrente. |
| V21 | Admissão de award | Witness de checker suficiente + estado ACTIVE + binding/revisão + rota; guard proibido. |
| V22 | Negativo direto no award | Bypass removido; bloqueio exige receipt autêntico e alvo correspondente. |
| V23 | PautaEngine | Inalterado; recebe ObligationEvidence produzido após política e reconciliação. |
| V24 | ScoreClosure | Inalterado; não inventa prova nem altera veto. |
| V25 | Current/fallback | Current mantém caminho legado; Semantic fallback identifica TME_SEMANTIC_FORMAL_NATIVE_FALLBACK e atravessa o resolver/policy. |
| V26 | credited_rules/fechamento | Inalterado; soma de créditos deve continuar igual a known_points. |

A tabela distingue rejeição de candidato, falta de witness, erro técnico e veto contra outra evidência. Nem todo caminho que resulta em zero é um hard veto. `award` registra ausência de witness sem fabricar checker, evidência negativa ou refutação; candidatos inválidos não contaminam positivos independentes.

## 4. Estados discursivos

| Estado | Admissão positiva | Visibilidade | Autoridade negativa |
| --- | --- | --- | --- |
| ACTIVE | Candidato sujeito a representação/checker/sufficiency | Atual | Somente com receipt de contradição validado |
| SUPERSEDED | Não | Histórica | Nenhuma |
| NON_ADOPTED | Não | Auditoria | Nenhuma |
| AMBIGUOUS | Não | Review/reconciliação | Nenhum hard veto automático |

Estado discursivo e estado matemático são dimensões diferentes. Uma correção falsa pode retirar uma posição anterior correta; seu próprio checker refuta a posição atual. Não se ressuscita a anterior. Uma negação adotada pode ser ACTIVE e continuar sem representação executável; isso não a transforma em afirmação positiva nem em hipótese descartada.

## 5. Resolver, ledger e retratação

Originais são mantidos em `discourse_ledger.original`; projeções derivadas ficam em `adapted`. O snapshot recebe fonte, ranges, propriedade/caso, sinais originais e decisões, sem input de score ou verdade esperada. Cada decisão contém evidence_id, canonical_id, estado, razão, binding, ranges de envelope/cláusula/asserted_content, supporting_spans, supersedes/superseded_by e original_model_signals.

O resolver localiza `asserted_content` literalmente e usa sua cláusula, não as bordas do envelope como ordem temporal. Envelopes equivalentes preservam a identidade de proposição; registros nativos traduzem `[item]` para coordenadas da fonte original. Aliases da mesma proposição participam do mesmo grafo.

A revisão exige mesma propriedade/caso, direção temporal e relação textual validada. “Na verdade” precisa de adjacência local e incompatibilidade escrita. Correção explícita pode reafirmar um valor equivalente. Texto intermediário de outra propriedade impede inferência genérica de alvo; revisão distante exige alvo nomeado. Revisão conjunta de cor/contagem permite somente companheiros vinculados ao mesmo caso. Retirada explícita sem substituto gera NON_ADOPTED, sem inventar claim posterior.

Ranges dos marcadores são traduzidos da representação normalizada para a fonte original: letras gregas, radicais e expoentes podem alterar comprimento. O receipt guarda o trecho literal que fundamenta a relação. Cabeçalhos de hipótese, citação, transcrição/enunciado e atribuição a terceiros são herdados dentro do parágrafo até reset explícito.

`abandoned`, `hypothetical`, `assertion_status`, polarity, scope, attribution e confidence do modelo são preservados como sinais. Flags isolados não apagam uma assertiva própria validada, não criam revisão e não autorizam veto. `abandonment.py` tornou-se camada de compatibilidade do resolver; não possui política autônoma de reativação.

## 6. Positive-credit policy

O mapping da projeção exige estado ACTIVE, vínculo íntegro, item/propriedade/tipo compatíveis e representação conferida. `award` exige resultado matemático positivo, sufficiency, rota registrada, verification_id, original_fact e referências aceitas na mesma revisão/fonte. Nenhum guard_only é witness.

O adapter pode extrair a única igualdade literalmente escrita de payload em prosa ou a enumeração exclusiva escrita. Não repara payload já parseável que tenha truncado uma igualdade ou omitido membro. Inclusão parcial não se transforma em conjunto completo. Os originais e a transformação ficam no trace.

AMBIGUOUS não impede um witness ACTIVE independente. Sem witness, há ausência de prova; com contradição atual validada, há decisão negativa central. O teste de I6 impede usar ausência como veto disfarçado.

## 7. Conflict-visibility policy

ACTIVE participa de conflitos; AMBIGUOUS permanece visível para revisão; SUPERSEDED e NON_ADOPTED permanecem históricos. Evidências rejeitadas pelo mapper continuam no ledger e podem sustentar um candidato estrutural se o predicado escrito puder ser validado independentemente. Caso contrário, não adquirem autoridade negativa por serem `unmapped`.

O inventário nativo original também retém registros sem forma canônica. Esses registros são audit-only e não causam exceção nem recebem status falso de refutação. Não há promoção automática de um registro não representável para prova.

## 8. VetoEligibilityPolicy e reconciliação

Recebe IDs de evidência/premissas, obrigação, resultado original do checker, status, checker_ref, tipo de contradição e produtor. Consulta os estados e propriedades no snapshot. Produz policy_version, ledger_revision, source_sha256, source_ranges, discourse_decision_refs, checker_result, provenance, conflict_visible, hard_veto_eligible, veto_reason, invariant, dependency_paths e reconciliation_status.

Hard veto exige todos os vínculos válidos, premissas ACTIVE, status de refutação aceito e receipt verificável, além de propriedade/item compatíveis e alvo autorizado. Boolean isolado de produtor não basta. UNPROVED, NOT_ATTEMPTED, ERROR, INCOMPLETE e resultados sem checker não viram refutação.

Reconciliação aceita somente decisões emitidas pela instância de política corrente, intactas e ligadas ao snapshot. Duplicação é idempotente. `award` também confere que a obrigação bloqueada consta nos targets do receipt; um receipt autêntico de (b) não pode ser reapresentado sob (a). Não usa confiança, ordem da lista ou preferência pelo positivo.

Dependências negativas implementadas, sem criar novos pesos/regras:

- b.ordered_pairs / b.different_favorable / b.same_compartment → b.second_white_probability, conforme source_consistency existente;
- c.strategy_case_i → c.conditional_success_i;
- continuação, estratégias e condicionais → c.total_win_probability.

Demais all_of/max_of e dependências positivas permanecem nos checkers/pauta. Erros de produtor atômico ficam técnicos, não negativos. Agregados CONFLICTING_FACT_RESULTS/CONFLICTING_CONDITIONAL_CONTEXTS são diagnóstico, não senha para veto.

## 9. Atomic guard e incompatibilidade estrutural

O checker finito de membership continua intacto; somente sua lista de rejeições representacionais passou a incluir `partial_membership_not_complete_set`. O guard emite resultado, literal, evento/modelo e receipt; nunca award.

O novo checker estrutural verifica a incompatibilidade entre `exact_set(S)` e `member(x,S)` escritos na mesma propriedade. A conclusão é negativa e guard_only. Ele não inventa `{1,2,4}`, não consulta a nota e não reaproveita o checker de repetição de (b) como matemática de continuação de (c). A política exige que ambas as proposições sejam atuais antes de aplicar a incompatibilidade.

## 10. Segundo veto determinístico

A leitura nativa não foi eliminada. Seus registros entram no mesmo ledger e são verificados por uma segunda projeção com os StrongP3Checks existentes. Fatos são consumidos individualmente pela política; o assessment/agregado bruto deixou de bloquear score.

Nos três casos observados com dois produtores de veto, a versão antiga é SUPERSEDED tanto no alias semântico quanto no nativo. A projeção anterior à composição impede a mistura de cor retirada com contagem final. Negativos nativos omitidos pelo extractor continuam alcançando a política quando representáveis e ACTIVE.

Current continua no caminho legado. Fallback do Semantic usa registros nativos como candidatos positivos próprios, resolve discurso, executa checkers e consome a política. Seu modo efetivo é explícito; não é apresentado como Current nem como sucesso do extractor.

## 11. Vinte invariantes e testes diretos

| Invariante | Teste direto |
| --- | --- |
| I1 | [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) — `test_I1_guard_never_awards_even_when_true` |
| I2 | [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) — `test_I2_nonadopted_checked_false_has_no_authority` |
| I3 | [tests/test_tme_p3_discourse_state.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_discourse_state.py) — `test_I3_model_abandoned_is_not_discourse_or_veto_authority` |
| I4 | [tests/test_tme_p3_discourse_state.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_discourse_state.py) — `test_I4_superseded_native_and_semantic_cannot_block_correction` |
| I5 | [tests/test_tme_p3_discourse_state.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_discourse_state.py) — `test_I5_ambiguous_cannot_be_positive_witness` |
| I6 | [tests/test_tme_p3_discourse_state.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_discourse_state.py) — `test_I6_ambiguous_does_not_defeat_independent_active_witness` |
| I7 | [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) — `test_I7_active_checked_refutation_is_eligible_only_in_compatible_scope` |
| I8 | [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) — `test_I8_local_conflict_only_reaches_contracted_dependency` |
| I9 | [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) — `test_I9_every_automatic_veto_has_current_source_checker_policy_receipt` |
| I10 | [tests/test_tme_p3_discourse_state.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_discourse_state.py) — `test_I10_processing_order_cannot_change_graph_or_awards` |
| I11 | [tests/test_tme_p3_discourse_state.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_discourse_state.py) — `test_I11_overlapping_envelope_does_not_change_retraction` |
| I12 | [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) — `test_I12_producer_cannot_bypass_central_receipt` |
| I13 | [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) — `test_I13_deduplication_and_reconciliation_idempotence` |
| I14 | [tests/test_tme_p3_discourse_state.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_discourse_state.py) — `test_I14_incorrect_correction_does_not_resurrect_true_prior` |
| I15 | [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) — `test_I15_source_payload_cannot_drop_false_side_or_member` |
| I16 | [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) — `test_I16_negative_dependency_does_not_depend_on_producer` |
| I17 | [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) — `test_I17_no_refutation_from_unproved_incomplete_or_error` |
| I18 | [tests/test_tme_p3_discourse_state.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_discourse_state.py) — `test_I18_native_fallback_uses_policy_current_stays_legacy` |
| I19 | [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) — `test_I19_stale_or_mutated_receipt_cannot_reach_award` |
| I20 | [tests/test_tme_p3_discourse_state.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_discourse_state.py) — `test_I20_composite_never_mixes_withdrawn_color_and_final_count` |

Além desses testes: escopo de cabeçalhos, retirada sem substituto, negação adotada, correção de assunto diferente, alvo distante indeterminado, cadeias de revisão, envelope sobreposto, offsets após normalização, rejeição de receipt redirecionado e replays gravados. Não há teste baseado apenas em verificar que a implementação contém um nome de estado.

## 12. Regressões observadas, sem API

### Prioridades da arquitetura

| Caso | Score no replay local | Verificação material |
| --- | ---: | --- |
| S2_03 | 0 | Inclusão ativa externa ao conjunto escrito → incompatibilidade estrutural → veto central |
| S2_06 | 2 | Refutação de membership alcança b.conclusion; b.different permanece |
| S1_02 | 2 | Contagem antiga retirada, inclusive alias nativo |
| S1_03 | 2 | Cor/contagem retiradas não entram na composição final |
| S1_07 | 1 | Conjunto antigo retirado nos dois canais |
| S4_07 | 2 | Contagem corrigida mantida; probabilidade falsa não contamina a.count |
| E02 | 4 | Autocorreção local, inclusive envelope antigo sobreposto |
| E04 | 2 | Sem retratação: conflito permanece; a.count independente |
| A08 | 8 | Igualdade escrita recuperada conservadoramente; checkers de contexto mantidos |
| E08 | 2 | Terceiro não adotado; enumeração exclusiva própria verificada |

E02=4 segue autorização prévia/sidecar e arquitetura aprovada. A fixture histórica que registrava 2 não foi alterada. Os casos são observados, não novos testes independentes.

### Inventário ampliado

| Conjunto histórico | Artefatos | Respostas reaproveitáveis | Sem resposta gravada |
| --- | ---: | ---: | ---: |
| DEV01 | 8 | 7 | 1 |
| DEV02 | 8 | 8 | 0 |
| robustness_01 original | 48 | 47 | 1 |
| safety_02 new32 | 32 | 31 | 1 |
| safety_02 observed_regression | 48 | 48 | 0 |
| Total de registros históricos, com repetições de fonte | 144 | 141 | 3 |

Excluídos por falta de raw_output: DEV01/p3_dev_isolated_answer, robustness_01/p3_rob_f08 e safety_02/p3_safe_s2_05. Não se fabricou resposta nem se chamou o modelo para preenchê-los. Fallback é testado separadamente com provider controlado.

Nos 141 replays: API=0, fallback novo=0, technical uncertainty=0 e veto com estado não ACTIVE=0. Comparação por obrigação com as expectativas observadas disponíveis não encontrou award extra; E02 usa o ajuste previamente autorizado. Isso não é uma estimativa de acurácia ou prova de segurança geral.

O inventário ampliado roda com `use_lean=False` para isolar estado/representação. Consequentemente B01 e S1_08, que exigem prova formal de (a), ficam sem esses pontos nessa rodada; não são refutações nem regressões matemáticas. Lean real é verificado separadamente abaixo. Persistem perdas de representação em A01/A02/A06/A07, S1_05 e S3_07, já não resolvidas pela execução anterior: o contrato não promete interpretar toda formulação natural.

O replay ampliado detectou durante o desenvolvimento duas falhas gerais: perda de wrapper ao estreitar cláusula e referência indevida de correção distante. Foram corrigidas na política de escopo/alvo e cobertas por testes próprios, sem branch por case_id ou mudança de expectativa. Esses mesmos casos continuam DEV observado.

Resultados completos locais: `/private/tmp/p3-unified-implementation/all-recorded/summary.json`, com um `result.json` por replay. Entradas observadas não foram sobrescritas. O script local usado está em `/private/tmp/p3-unified-implementation/all_recorded.py`.

## 13. Suítes e totais

| Grupo | Resultado final |
| --- | --- |
| Novos discourse/veto/reconciliation + semantic P3 + abandonment/conflict | 261 PASS |
| checker-first P3 + bridge P3 + PautaEngine + rubric bridge/pipeline | 283 PASS; 1 SKIP histórico não P3 |
| semantic P3 Lean + checker-first P3 Lean | 21 PASS |
| Novas integrações Lean de retratação unificada | 2 PASS |
| semantic_claims / tme_hybrid_grader / scope_boundary selecionados para TME2026P3 | 6 PASS |
| Testes distintos, sem contar repetições de depuração | **573 PASS; 1 SKIP** |

O skip é `test_saved_f2q1_v2_proof_replay_recovers_only_the_final_criterion`: artefato V2 local não disponível; sua regressão portátil executou. A seleção relacionada teve 132 deselected, não falhas.

A primeira rodada de bridge teve quatro falhas de permissão para gravar artefatos de teste no worktree fora do sandbox. As suítes afetadas foram repetidas com autorização de sandbox e passaram (71 testes). Não houve correção de código protegido para resolver essas falhas.

A rodada final conjunta de aceite contém 263 PASS (261 contratos + 2 Lean de retratação). XML/logs: `acceptance.xml`, `acceptance.log`, `mathematics.xml`, `bridge-retry.xml`, `formal.xml`, `final-formal.xml`, `related.xml`, sob `/private/tmp/p3-unified-implementation/`. `mathematics.xml` preserva também a falha inicial de permissão; o resultado final das suítes afetadas está em `bridge-retry.xml`.

## 14. Lean real

`lake env lean --version` retornou Lean 4.28.0, arm64-apple-darwin24.6.0, commit `7e01a1bf5c70fc6167d49c345d3bf80596e9a79b`.

As integrações reais confirmaram os cinco IDs Lean-capable, igualdade verdadeira, refutação de igualdade falsa, igualdade verdadeira com partição falsa sem crédito e preservação das parcelas independentes. Os testes controlados de `skip` e identificador inexistente confirmaram FORMAL_UNPROVED e FORMAL_ERROR distintos de FORMAL_REFUTED; eles provocam falhas esperadas e o teste passa ao conferir sua classificação.

Na nova integração de retratação, `primeira_branca: 1/2` é retirada antes de `2/6=1/3`: Lean realmente compila a igualdade final e concede 2; na variante final `2/6=1/2`, a negação é provada, `refutation_verified=true` e score=0. Em ambas, o alias nativo antigo fica SUPERSEDED. O extractor é provider local, API=0.

Nenhuma proposição ou fonte de checker Lean foi editada. Arquivos de prova gerados pelas rotinas existentes são artefatos de execução. Receipts completos das novas integrações: diretórios `acceptance/test_real_lean_after_validated*/result.json`.

## 15. Arquivos modificados e novos

- Modificado: [app/confia_lean_auditor/experimental/tme_semantic_formal_p3/__init__.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/__init__.py)
- Modificado: [app/confia_lean_auditor/experimental/tme_semantic_formal_p3/abandonment.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/abandonment.py)
- Modificado: [app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py)
- Modificado: [app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py)
- Modificado: [app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py)
- Modificado: [tests/test_tme_p3_abandonment_safety.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_abandonment_safety.py)
- Modificado: [tests/test_tme_p3_conflict_preservation.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_conflict_preservation.py)
- Modificado: [tests/test_tme_semantic_formal_p3.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_semantic_formal_p3.py)
- Novo: [app/confia_lean_auditor/experimental/tme_semantic_formal_p3/discourse.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/discourse.py)
- Novo: [app/confia_lean_auditor/experimental/tme_semantic_formal_p3/source_adapter.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/source_adapter.py)
- Novo: [app/confia_lean_auditor/experimental/tme_semantic_formal_p3/unified.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/unified.py)
- Novo: [app/confia_lean_auditor/experimental/tme_semantic_formal_p3/veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/veto_policy.py)
- Novo: [tests/test_tme_p3_discourse_state.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_discourse_state.py)
- Novo: [tests/test_tme_p3_unified_lean.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_unified_lean.py)
- Novo: [tests/test_tme_p3_unified_reconciliation.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_unified_reconciliation.py)
- Novo: [tests/test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py)
- Novo: [docs/audits/TME_P3_UNIFIED_DISCOURSE_VETO_IMPLEMENTACAO_01.md](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_UNIFIED_DISCOURSE_VETO_IMPLEMENTACAO_01.md)

## 16. Preservação e integridade

Inventário anterior: 787 arquivos de app, testes, pautas/máquina e artefatos Safety 02. Oito arquivos existentes mudaram: cinco locais do Semantic P3 e três testes unitários. Os outros 779 permanecem byte a byte iguais. Arquivos novos são módulos/testes experimentais e este relatório.

Preservados: prompt/schema/extractor.py, pauta e pesos, PautaEngine, bridge, StrongP3Checks, componentes/modelo finito, checkers Lean e suas proposições, score closure, fixtures e expectations de DEV/robustness/safety, código P1/P2 e histórico de artefatos. Nenhum arquivo existente de benchmark foi editado. VERSION mudou a identificação de execução/configuração; não mudou o texto enviado ao modelo.

`git diff --check` passou. HEAD permaneceu na base; nada foi staged e nenhum commit foi criado. Manifesto anterior: `/private/tmp/p3-unified-implementation/before.json`. Hashes da entrega estão abaixo; o relatório não se auto-hasheia.

| Arquivo implementado/testado | SHA-256 |
| --- | --- |
| `app/confia_lean_auditor/experimental/tme_semantic_formal_p3/__init__.py` | `6e542fe2cad55afc283ee7c447f3fd3e7a01e2d3984e0494418bcef3a9ac2cec` |
| `app/confia_lean_auditor/experimental/tme_semantic_formal_p3/abandonment.py` | `7840bb41ebaf849b8187230069543a8729135eccafd722c3faf67e3abb07cae9` |
| `app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py` | `8250d80ad1ad505eb0b285a593d89f27d638abad908d9f110257ba576fe5d4b9` |
| `app/confia_lean_auditor/experimental/tme_semantic_formal_p3/discourse.py` | `d347f780b597a3139851ce521d7fcaa41a813a7b98d7b9ad08ebc5c3c6e75132` |
| `app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py` | `136a8913b47b2520572466a189a6b5e49d7dc29bb0385386e8b595323385382b` |
| `app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py` | `e8476948d3748f8b77381b2a5c50a90a71706866731102de44f6327a16bb8ad6` |
| `app/confia_lean_auditor/experimental/tme_semantic_formal_p3/source_adapter.py` | `69b2efd384bcff20131874d449476a1006de037e8e5803a2bcb563634eb72a5e` |
| `app/confia_lean_auditor/experimental/tme_semantic_formal_p3/unified.py` | `5abc897aa72262eaaff36fc265b3340b201907fb8bf84ebbdb294709f00ef4ce` |
| `app/confia_lean_auditor/experimental/tme_semantic_formal_p3/veto_policy.py` | `1d8aa977cd5cbcc95ff31b2ea53454eb7e30bfb66bb6f730253137090f3f14d7` |
| `tests/test_tme_p3_abandonment_safety.py` | `d220da3ceef1602660bc8cf4a58262a389af0db0131c7cd452d6a6d3c7725f51` |
| `tests/test_tme_p3_conflict_preservation.py` | `b6748975f84ba93b7c50d2a698668cafeea7c06fd201603153fac8cd1492cd5f` |
| `tests/test_tme_p3_discourse_state.py` | `0f797f540532282121e334a32890d735668a9c0da837c3dd5cd5a002e0e56036` |
| `tests/test_tme_p3_unified_lean.py` | `0be75fca8374c442d852d69c243ef8417d6d0e75cbcb75215643d64dea81e8df` |
| `tests/test_tme_p3_unified_reconciliation.py` | `cd5917c7cbdd0cf2d654cc335afb8fe60ff605658aa92a4cf7c61671f2f8e32a` |
| `tests/test_tme_p3_veto_policy.py` | `a8957d2fba6f2f2e3a821d66cefcaf04b0a5b5eb67cccce0c2dadd3b07b8774a` |
| `tests/test_tme_semantic_formal_p3.py` | `7c9f403e115a0caa64df934045c21402109667539eb18b9599c9943e99f9f2af` |

## 17. Limitações e interpretação do veredito

- Validação textual é deliberadamente limitada às gramáticas implementadas. Retração retrospectiva fora do alvo reconhecido, payload não executável e adoção ambígua permanecem sem prova automática, com trace/review. Isso não autoriza hard veto de AMBIGUOUS.
- Os replays reutilizam interpretações históricas; não medem estabilidade do extractor nem seu desempenho em fontes novas. Três falhas históricas sem raw_output não são recuperáveis como sucesso sem nova chamada, que não foi feita.
- Os 141 replays amplos não executam Lean; integração formal foi exercitada por suítes dedicadas e pelas novas retratações reais. Scores sem prova formal não são tratados como refutação nem comparados como “acurácia”.
- A segurança global depende também da cobertura de representação. Ausência de falso award na regressão observada não garante ausência em linguagem não coberta.
- Toda execução real futura deve congelar a implementação e seu protocolo. Os conjuntos anteriores continuam DEV observado. Safety 03 não foi criado e é a etapa independente futura, se autorizada.

## 18. Comandos de reprodução e comandos futuros

Comandos locais usados (paths de logs/basetemp diferentes preservam rodadas):

```bash
cd ~/Documents/confia-lean-auditor-tme-semantic-formal-p3
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app:$PWD" CONFIA_TME_SEMANTIC_ENABLED=0
P3_PYTHON=/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python

"$P3_PYTHON" -m pytest tests/test_tme_p3_discourse_state.py tests/test_tme_p3_veto_policy.py tests/test_tme_p3_unified_reconciliation.py tests/test_tme_semantic_formal_p3.py tests/test_tme_p3_abandonment_safety.py tests/test_tme_p3_conflict_preservation.py tests/test_tme_p3_unified_lean.py -q -p no:cacheprovider --basetemp=/private/tmp/p3-unified-implementation/acceptance --junitxml=/private/tmp/p3-unified-implementation/acceptance.xml --tb=short

"$P3_PYTHON" -m pytest tests/test_tme_p3_checker_first.py tests/test_tme2_p3_pauta_bridge.py tests/test_pauta_engine.py tests/test_rubric_bridge.py tests/test_rubric_bridge_pipeline.py -q -p no:cacheprovider --basetemp=/private/tmp/p3-unified-implementation/mathematics --junitxml=/private/tmp/p3-unified-implementation/mathematics.xml --tb=short

"$P3_PYTHON" -m pytest tests/test_tme2_p3_pauta_bridge.py tests/test_rubric_bridge_pipeline.py -q -p no:cacheprovider --basetemp=/private/tmp/p3-unified-implementation/bridge-retry --junitxml=/private/tmp/p3-unified-implementation/bridge-retry.xml --tb=short

"$P3_PYTHON" -m pytest tests/test_tme_semantic_formal_p3_lean.py tests/test_tme_p3_checker_first_lean.py -q -p no:cacheprovider --basetemp=/private/tmp/p3-unified-implementation/formal --junitxml=/private/tmp/p3-unified-implementation/formal.xml --tb=short

"$P3_PYTHON" -m pytest tests/test_tme_semantic_formal_p3_lean.py -q -p no:cacheprovider --basetemp=/private/tmp/p3-unified-implementation/final-formal --junitxml=/private/tmp/p3-unified-implementation/final-formal.xml --tb=short

"$P3_PYTHON" -m pytest tests/test_semantic_claims.py tests/test_tme_hybrid_grader.py tests/test_scope_boundary.py -k TME2026P3 -q -p no:cacheprovider --basetemp=/private/tmp/p3-unified-implementation/related --junitxml=/private/tmp/p3-unified-implementation/related.xml --tb=short

"$P3_PYTHON" /private/tmp/p3-unified-implementation/all_recorded.py
lake env lean --version
git status --short
git rev-parse HEAD
```

Exemplo **futuro, não executado**, de regressão observada via API, somente depois de congelar revisão/protocolo e receber autorização específica. Não constitui criação de Safety 03:

```bash
"$P3_PYTHON" scripts/evaluation/run_tme_semantic_formal_p3.py   --mode tme_semantic_formal   --dataset tests/fixtures/tme_semantic_formal_p3/dev_sources.json   --ids-file tests/fixtures/tme_semantic_formal_p3/dev_ids.json   --output-dir artifacts/evaluations/p3_unified_future_observed_regression   --model gpt-6.1-sol --reasoning-effort medium
```

**READY_FOR_P3_UNIFIED_REGRESSION**
