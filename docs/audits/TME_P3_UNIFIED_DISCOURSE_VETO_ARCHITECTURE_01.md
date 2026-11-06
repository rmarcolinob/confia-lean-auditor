# TME P3 — Arquitetura unificada de estado discursivo e veto

## 1. Decisão e limites

**ARCHITECTURE_READY_FOR_IMPLEMENTATION.** O desenho propõe um ledger único de claims vinculados à fonte, um resolver central de estado discursivo e uma única política de autoridade para vetos. Os produtores existentes podem continuar a verificar matemática, mas seus flags, conflitos agregados e resultados negativos deixam de ser autorização autônoma para bloquear score.

Pronto para implementação significa contratos, fronteiras e critérios de aceite definidos; **não** significa fix implementado, Safety 02 resolvido ou segurança revalidada. Não foi executado código de avaliação, teste, Lean ou API nesta tarefa. Nenhum prompt, fixture, expectation ou código foi alterado. Foi criado somente este documento; não houve commit.

Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3`. HEAD inspecionado: `1dea197ab5e3ee40597acc3d35af3cb8dcc4d4c3`, inicialmente limpo. Implementação avaliada pelos recibos: `89cda1cab89648d3888775bbcead42ea85bd4861`; commits posteriores registram os relatórios/fixtures, sem mudança da implementação. Data: 06/11/2026, America/Fortaleza.

O forense mantém **MULTIPLE_ROOT_CAUSES**: perda de representação ativa; reconhecimento de retratação dependente de envelope/marcador/adjacência; refutação sem propagação de dependência; segundo veto determinístico alheio à retratação; variação de payload. Um campo `discourse_state` isolado não corrige esses mecanismos.

Referências observadas: [TME_P3_SEMANTIC_SAFETY_02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_SEMANTIC_SAFETY_02.md), [TME_P3_SEMANTIC_SAFETY_02_FORENSIC](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_SEMANTIC_SAFETY_02_FORENSIC.md), [TME_P3_ABANDONMENT_SAFETY_FIX_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_ABANDONMENT_SAFETY_FIX_01.md), [TME_P3_CONFLICT_PRESERVATION_FIX_01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_CONFLICT_PRESERVATION_FIX_01.md).

## 2. Mapa de todos os caminhos atuais relevantes a P3

Escopo: fechamento transitivo do entry point `tme_semantic_formal_p3.engine.evaluate`, incluindo leitura nativa, guard_bridge, fallback/Current e entrega à pauta. Validadores de baixo nível são agrupados pelo ponto em que sua falha chega a esse fluxo; não se inventam caminhos de outras experiências.

Distinções: **rejeição de candidato** impede que aquele registro prove algo; **insuficiência** indica falta de prova/contexto requerido; **hard veto** derrota um award por evidência contrária; **erro técnico** não é refutação. Atualmente essas situações podem terminar sob rótulos comuns. A tabela não as equipara.

| ID | Arquivo / função | Input | Condição | Output |
| --- | --- | --- | --- | --- |
| V00 | [experimental/tme_semantic_formal_p3/mapper.py:9](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:9)<br>SourceDocument.parse / require_p3; collect_digital_items | Texto/problem_id/itens | Problema/item inválido, framing/tamanho inválido; fonte fora dos limites | Exceção/nenhum documento ou registros; falha de entrada, não veto matemático |
| V01 | [experimental/tme_semantic_formal_p3/extractor.py:68](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/extractor.py:68)<br>SemanticExtractorP3.extract + bind_evidence | Resposta API/provider e fonte | Não completed, schema/IDs/span/asserted_content inválidos | unavailable → fallback; nenhum claim útil se binding falhar |
| V02 | [experimental/tme_semantic_formal_p3/mapper.py:117](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:117)<br>ObligationMapper.map: identidade/interpretações | EvidenceUnits | Fonte/hash mudou, obligation desconhecida, owner/item divergente; interpretações diferentes no mesmo (start,end,subject) | accepted=false; conflicting_extractor_interpretation gera CONFLICTING_EVIDENCE mesmo sem checker |
| V03 | [experimental/tme_semantic_formal_p3/mapper.py:133](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:133)<br>ObligationMapper.map: flags | EvidenceUnit | Não asserted/positive/atribuído; hypothetical ou abandoned; scope não permitido | nonasserted_or_unattributed_context; fora da projeção positiva e normalmente negativa |
| V04 | [experimental/tme_semantic_formal_p3/mapper.py:25](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:25)<br>local_context / _anchor / source_view | Span, prefixo do parágrafo, subject | Negação/citação/hipótese/tentativa/qualificador; ausência de vínculo local único; reset de afirmação | source_context_rejected ou rejeição de representação; não avalia verdade |
| V05 | [experimental/tme_semantic_formal_p3/mapper.py:69](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:69)<br>representation + named_math/literal parser | Payload, tipo, subject e fonte | Gramática inválida; payload alterado/truncado; membros incompletos; número incidental; cor/contagem sem vínculo; tipo incompatível | Rejeição de representação; pode remover negativo ativo (S2_03/S2_06), ou positivo (A08/E08) |
| V06 | [experimental/tme_semantic_formal_p3/verification.py:25](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py:25)<br>ClaimProjection | Units + mappings | Somente IDs accepted; tradução de offsets obrigatória; records regenerados | Apenas aceitos chegam a _a/_b/_c; descartados recebem recibo sem checker |
| V07 | [lean/student_claim_checkers/tme2_p3.py:53](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/lean/student_claim_checkers/tme2_p3.py:53)<br>assertions_in_item / standalone_math | DigitalItemClaims | Mesmo item, source.attributable, grounded; matemática isolada exige linha completa e papel permitido | Filtro pré-checker, ausência de fato se nenhum registro elegível |
| V08 | [lean/student_claim_checkers/tme2_p3.py:74](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/lean/student_claim_checkers/tme2_p3.py:74)<br>P3Checks / value_status / _a / _b / _c / rational equality | Registros admitidos + máquina | Valor/conjunto/cor/conta contra regra; Lean somente quando elegível; identidade de fonte da projeção | FactResult verified/refuted/unverified/technical_error; Lean unproved/error não vira refutação |
| V09 | [lean/student_claim_checkers/tme2_p3.py:127](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/lean/student_claim_checkers/tme2_p3.py:127)<br>_b alternativa; _c condicionais/global | Conjuntos de fatos/contextos escritos | Árvore exige seis ramos e soma; estratégia exige cor+contagem; condicionais exigem estratégia; total exige forma e contexto completos | Fato ausente/unverified/refuted ou dependente; STRATEGY_CONTEXT_NOT_VERIFIED / GAME_CONTEXT_NOT_VERIFIED |
| V10 | [experimental/tme_p3_checker_first/engine.py:45](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_p3_checker_first/engine.py:45)<br>StrongP3Checks + components.combine | Aritmética/modelo/relação/contexto | Algum false → refuted; erro → technical_error; CONFLICTING_EVIDENCE ou falta → incomplete; todos verificados → verified | COMPOSITE_FAILED/ERROR/INCOMPLETE/VERIFIED; impede sufficiency |
| V11 | [experimental/tme_p3_checker_first/engine.py:81](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_p3_checker_first/engine.py:81)<br>source_consistency / tree_relation | pending de b; ramos escritos | Negativo ou erro em b.ordered_pairs/different_favorable/same_compartment; árvore com ramo falso/incompleto | Componente veto_only source_consistency ou written_relation; conclusão não suficiente, antes dos guards |
| V12 | [rubric/pauta/bridge.py:97](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/rubric/pauta/bridge.py:97)<br>_formal_result_matches / _validated_status | FactResult, records, hashes, links | Fonte/atribuição/role/origem inválida; fingerprint/link alterado; prova/refutação Lean não vinculada | indeterminate com motivo, ou status validado; nenhum status do modelo basta |
| V13 | [rubric/pauta/bridge.py:166](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/rubric/pauta/bridge.py:166)<br>bridge_facts | Todos os fatos por obrigação | supported+refuted; contextos condicionais diferentes; qualquer indeterminate/technical_error; ausência de fatos | CONFLICTING_FACT_RESULTS / CONFLICTING_CONDITIONAL_CONTEXTS / indeterminate / technical_error |
| V14 | [experimental/tme_semantic_formal_p3/verification.py:51](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py:51)<br>IsolatedChecks / verify / formal_state | Fatos/projeção/bridge/mapping | Exceção local; resultado sem primary mapping aceito; validação não supported; rota formal não provada; nenhum fato | Resultados com sufficient=false, CONTEXT_REJECTED ou CONFLICTING_EVIDENCE; erro contido por obrigação |
| V15 | [experimental/tme_semantic_formal_p3/abandonment.py:36](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/abandonment.py:36)<br>abandonment_support / conflict_visibility | Units com abandoned ou assertion_status=abandoned | Suporte textual interior/tail/adjacente; contexto restante; se sem suporte, reativa cópia asserted/main_argument | Visão de segurança ou supressão; pode retirar negativo ou reativar superseded |
| V16 | [experimental/tme_semantic_formal_p3/abandonment.py:108](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/abandonment.py:108)<br>regular_safety_checks | Visão recuperada + mapping novo | Só se recovered não vazio; verify use_lean=false; fatos que envolvem recovered | abandonment_guard_results; refutação candidata, guard_only/sem award |
| V17 | [experimental/tme_semantic_formal_p3/conflict_guard.py:29](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py:29)<br>_bound_context / conflict_guards / membership_result | Unit rejeitada por formato, b.same | Fonte/item/subject/contexto/flags válidos; gramática de membership parcial; certificado finito | Guard atômico VERIFIED/FAILED; mathematical_refutation só negativo; nunca crédito |
| V18 | [student_claims/digital_items.py:17](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/student_claims/digital_items.py:17)<br>Leitura nativa: collect_digital_items + contextual_role + merge_candidates | Fonte original em frames [a]/[b]/[c] | Parsers tipados/genéricos, atribuição textual/roles; sobreposição em literal descarta genérico; owner único; ambiguidade de assignments | Registros nativos atribuídos/não atribuídos/ambíguos; pode omitir prosa ou manter duas versões retiradas |
| V19 | [experimental/tme_p3_checker_first/engine.py:136](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_p3_checker_first/engine.py:136)<br>audit_p3_checker_first — SEGUNDO VETO DETERMINÍSTICO | document.items original, deterministic_only | Checks/bridge sobre fonte inteira; conflitos agregados ou conflicting_source_evidence | guard_bridge.conflicts, status refuted, records/facts; NÃO recebe abandonment_decisions |
| V20 | [experimental/tme_semantic_formal_p3/engine.py:35](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:35)<br>reconcile | Resultados + math_bridge + guard_bridge + dois guards | Sete famílias de condições listadas abaixo | Lista de conflitos não resolvidos por obrigação; qualquer condição aceita já bloqueia award |
| V21 | [experimental/tme_semantic_formal_p3/engine.py:60](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:60)<br>award: admissão positiva | Units/mappings/results/conflicts | Status positivo, rota admitida, sufficient, verification_id/original_fact, binding primário, todos refs aceitos/asserted/positive/atribuídos e não hypothetical/abandoned | Nenhum chosen → no_sufficient_checker_result; também veto por blocked |
| V22 | [experimental/tme_semantic_formal_p3/engine.py:74](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:74)<br>award: negativo direto | Resultados da obrigação | Qualquer mathematical_refutation em rows, mesmo sem conflito explícito | chosen=None; bypass negativo adicional à lista de reconcile |
| V23 | [rubric/pauta/engine.py:61](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/rubric/pauta/engine.py:61)<br>_Evaluation.observe/atomic/rule | ObligationEvidence final e pauta | Origem/atribuição/contexto condicional; all_of, additive, max_of; obrigação insuficiente/refutada | Pontuação conforme regra; withhold sobre indeterminado; não lê EvidenceUnit/LLM/abandoned |
| V24 | [experimental/tme_semantic_formal/score_closure.py:8](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal/score_closure.py:8)<br>ScoreClosurePolicy.close | Assessment | score ausente → known_points; faixa/número inválido → erro; erro técnico/review preservados | Score numérico ou erro de integridade; não cria nem resolve veto |
| V25 | [experimental/tme_semantic_formal_p3/engine.py:106](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py:106)<br>evaluate Current/fallback → primary_audit | Fonte; extractor não completed ou modo Current | Rota legacy deterministic_only, P3Checks, bridge, PautaEngine | Pontua sem reconcile/guards experimentais; caminho alternativo de autoridade atual |
| V26 | [experimental/tme_semantic_formal/award_gate.py:64](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal/award_gate.py:64)<br>credited_rules + assert de fechamento no engine | Assessment/awards | Extrai regras pontuadas/selecionadas; soma diferente de known_points → ValueError | Trace ou erro de integridade; não é checker/veto semântico |

### 2.1 Consultas e autoridade de cada caminho

Legenda: **D** = consulta direta; **I** = herda decisão/record previamente filtrado; **T** = examina texto/semantic_role, não o flag do LLM; **N** = não consulta. Checker **D** executa; **I** somente consome resultado. “Bloqueio direto” distingue rejeição de candidato de veto sobre outro positivo. Chegar à reconciliação não implica que a evidência original sobreviveu nela.

| ID | Contexto | abandoned | hypothetical | Attribution | Checker | Reconciliation | Bloqueio direto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V00 | N | N | N | N | N | não | erro de entrada |
| V01 | D | I | I | I | N | só se completar | fallback global na falha |
| V02 | D | D* | D* | D* | N | sim, rejeição/conflito | conflito por interpretação, via V20 |
| V03 | D | D | D | D | N | sim, rejeição | retira candidato |
| V04 | D | T | T | T | N | sim, rejeição | retira candidato |
| V05 | D | N | N | N | N | sim, rejeição | retira candidato |
| V06 | I | I | I | I | N | sim | retira não aceitos da matemática |
| V07 | D | T | T | D | N | via facts/bridge | retira candidato |
| V08 | I | I | I | I | D | sim | refuta, não pontua diretamente |
| V09 | D | I | I | I | D | sim | impede fato/contexto suficiente |
| V10 | I | I | I | I | D | sim | impede sufficient positivo |
| V11 | D | I | I | I | D | sim | impede sufficient da conclusão |
| V12 | D | T | T | D | I | sim | invalida suporte, não nova refutação |
| V13 | D | I | I | I | I | sim | agrega conflito/status insuficiente |
| V14 | I | I | I | I | D/I | sim | sufficient=false ou erro |
| V15 | D | D | D | D | N | via V16/V17 | define recuperação/supressão, não pontos |
| V16 | I | I | I | I | D | sim | via refutação recuperada |
| V17 | D | D | D | D | D | sim | via negativo atômico |
| V18 | T | T | T | D/T | N | via V19/V25 | retira/seleciona registros |
| V19 | T/I | T/I | T/I | D/I | D | sim no Semantic; não no próprio assessment | conflito/status com autoridade em V20 |
| V20 | I | N | N | N | I | é o consumidor | sim, lista blocked |
| V21 | I | D | D | D | I | consome | sim, admissão e blocked |
| V22 | N | N | N | N | I | bypass após reconcile | sim, qualquer refutação |
| V23 | D | N | N | D | I | depois ou fallback sem ela | sim, exclusivamente regras existentes |
| V24 | N | N | N | N | N | depois | não veto; erro numérico possível |
| V25 | T/I | T/I | T/I | I | D | não experimental | sim, assessment legacy |
| V26 | N | N | N | N | I | depois | não veto; erro de trace possível |

`D*` em V02: os campos participam da chave de interpretações concorrentes; isso não é validação discursiva. V01 valida estrutura do schema, não confirma semanticamente cada flag. Nos caminhos nativos, “T” não significa leitura de `model_abandoned`: são heurísticas textuais e semantic_role independentes do resolver experimental.

Sete famílias da condição OR atual em V20, todas sem consultar discourse_state final:

1. Guard atômico ou guard regular com refutação na mesma obrigação.
2. Positivo e negativo entre verification_results.
3. Qualquer resultado `CONFLICTING_EVIDENCE` (inclusive interpretação conflitante no mesmo envelope).
4. Componente/decisão `conflicting_source_evidence`.
5. math_bridge com `CONFLICTING_FACT_RESULTS` ou `CONFLICTING_CONDITIONAL_CONTEXTS`.
6. Obrigação em `guard_bridge.conflicts` da fonte determinística.
7. Positivo semântico acompanhado de `guard_bridge` status refuted.

V22 ainda bloqueia por `mathematical_refutation` diretamente, sem precisar de V20. Centralizar só atomic guard deixaria V13, V19, V20 e V22 com decisões independentes.

### 2.2 Grafo textual por caminho

```text
V00 source/problem → framing/limites → documento ou erro de entrada
V01 source → extractor → schema/bind_evidence → EvidenceUnits OU V25 fallback
V02 EvidenceUnit → integridade/owner/interpretações → mapping rejeitado/conflito → V14 → V20 → V21
V03 EvidenceUnit → flags/scope → mapping rejeitado → V06 omite → V14 CONTEXT_REJECTED
V04 EvidenceUnit + parágrafo → local_context/anchor → rejeição → V06/V14
V05 EvidenceUnit → representation → rejeição de payload → V06 omite negativo/positivo → V14
V06 EvidenceUnit aceita → ClaimProjection → MathClaimRecord → V07–V14
V07 MathClaimRecord → filtro de item/atribuição/grounding → _a/_b/_c OU nenhum fato
V08 registro admitido → matemática/modelo/Lean → FactResult → V12/V13 → V14/V20/V21
V09 registros/contexto → estratégia/ramos/forma requerida → fato incompleto/ausente → V14 → sem award
V10 fatos/componentes → combine → COMPOSITE_* → V14 sufficiency → V21
V11 negativos pending de b → source_consistency → conclusão incomplete/error → V14/V20/V21
V12 FactResult + vínculo/prova → _validated_status → status válido OU indeterminate → V13/V14
V13 fatos de uma obrigação → bridge_facts → conflito/status agregado → V20 OU V23
V14 mapping/fatos → verify/IsolatedChecks → status + sufficiency → V20/V21/V22
V15 EvidenceUnit abandoned → suporte local → cópia visível OU suprimida → V16/V17
V16 cópia recuperada → novo mapping/verify(use_lean=false) → guard regular → V20 → V21
V17 EvidenceUnit parcial → _bound_context + átomo literal → certificado → atomic guard → V20 → V21
V18 source original → parsers nativos/contextual_role/merge → records → V19 ou V25
V19 source original → audit_p3_checker_first → checks/bridge → conflitos/refuted → V20 → V21
V20 resultados + math_bridge + guard_bridge + guards → OR de conflitos → blocked → V21
V21 resultados positivos + mappings + flags → chosen OU sem suporte/blocked → ObligationEvidence → V23
V22 resultado negativo bruto → chosen=None (sem decisão de veto própria) → V23
V23 ObligationEvidence → gates + all_of/additive/max_of da pauta → assessment
V24 assessment → score/known_points → faixa numérica/review; nenhum novo crédito/veto
V25 source → primary_audit(deterministic_only) → native/checkers/bridge → PautaEngine → V24 (fora V20)
V26 assessment + awards → credited_rules → soma/trace consistente OU erro de integridade
```

O segundo caminho determinístico V19 é comprovado em S1_02/S1_07/S4_07: guard_evidence=indeterminate, reason=CONFLICTING_FACT_RESULTS, registros nativos antigo refuted e novo supported. Nenhuma decisão de abandono é fornecida a essa leitura. Retirar o guard regular não elimina esse caminho.

Não estão no caminho P3: a classe C1 `AwardGate` e seu resolved_winners, o reconciliation de P1/C1 e `HybridEvidencePolicy` como autoridade semântica. P3 importa do módulo compartilhado apenas `credited_rules`; chama sua própria função award e `PautaEngine.evaluate` sem evidence_policy. A ausência de `SemanticSufficiencyGate` nominal não significa ausência de gates: V09–V14 e V21 exercem essas funções.

Referências auxiliares da leitura nativa: [student_claims/generic_math.py:231](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/student_claims/generic_math.py:231), [student_claims/generic_math.py:250](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/student_claims/generic_math.py:250), [student_claims/named_math.py:25](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/student_claims/named_math.py:25), [student_claims/digital_literals.py:78](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/student_claims/digital_literals.py:78), [rubric/positive_evidence.py:154](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/rubric/positive_evidence.py:154), [tme/obligation_experiment.py:21](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/tme/obligation_experiment.py:21). As rotinas gerais de pontuação de positive_evidence não são chamadas por este fluxo; são usados seus helpers textuais via contextual_role.

## 3. Contrato único de evidência e estado discursivo

### 3.1 Ledger imutável e identidade

Todo claim potencial entra no mesmo **EvidenceLedger P3**, originado do extractor ou do coletor nativo. IDs originais/aliases permanecem auditáveis. Identidade canônica inclui hash da fonte, ranges da cláusula, propriedade, item, caso/condição, objeto/índice, quantificador/exaustividade e polaridade. Mesmo texto em lugares diferentes não é deduplicado por string. Duas descrições do mesmo span não são automaticamente duas afirmações do aluno.

Guardar separadamente: envelope de proveniência; ranges de asserted_content; ranges de marcador; objeto/valor literal; contexto de atribuição; sugestões do modelo; source relation receipts; estado resolvido; representabilidade positiva/negativa; resultados dos checkers. Source hashes e traduções de coordenadas entre `a)` e frames `[a]` são obrigatórios. Registros nativos só convergem quando identidade e tradução forem verificadas, nunca por busca aproximada ou igualdade do número.

Nenhum raw EvidenceUnit ou FactResult histórico é mutado para “fingir” asserted. A nova visão usada para verificação cita o original e a decisão local que autoriza seu uso. Mudança de fonte, versão do resolver ou conjunto de claims invalida decisões/checagens dependentes; um token antigo não pode autorizar score de um ledger diferente.

### 3.2 Estados finais

| Estado | Definição normativa | Prova local requerida / fronteira |
| --- | --- | --- |
| ACTIVE | Afirmação atualmente adotada pelo aluno, sobre uma propriedade/contexto identificados | Assertiva própria ou adoção explícita validada na fonte; nenhuma substituição/rejeição final válida. Pode ser matematicamente falsa, não executável ou negativa |
| SUPERSEDED | Afirmação anterior substituída por posição posterior adotada no mesmo escopo, com vínculo de revisão validado | Receipt direcionado old→new, alvos/escopo identificados. Não depende de a nova posição ser verdadeira |
| NON_ADOPTED | Conteúdo presente, mas não adotado como posição atual: hipótese exploratória, terceiro/citação não adotados, exemplo rejeitado ou tentativa explicitamente descartada | Wrapper/atribuição/rejeição literal com escopo conferido. Retirada sem substituto conhecido pode ser NON_ADOPTED, não exige inventar new_claim |
| AMBIGUOUS | A fonte/validação local não permite escolher com segurança entre os três estados anteriores | Receipt de pendência com candidatos e motivo; não resolve por confiança LLM, última frase ou valor correto |

Invalid source binding é uma condição de integridade anterior e ortogonal: candidato inválido fica em diagnóstico, sem crédito ou veto. Não é promovido a ACTIVE nem usado para refutar outro claim. `UNREPRESENTABLE` não é quinto estado discursivo; é atributo do payload. Um claim ACTIVE pode não ter checker executável, e um claim SUPERSEDED pode ter matemática verificável historicamente.

`model_abandoned`, assertion_status, hypothetical, scope e attributed_to_student são sinais propostos, não o estado final. A ausência de marcador, isoladamente, não prova ACTIVE: é preciso confirmação local de assertiva própria. Por outro lado, uma assertiva própria literal sem suporte à retirada não vira SUPERSEDED só porque o modelo disse abandoned. Falta de validação da atribuição ou do alvo da revisão leva a AMBIGUOUS.

Condição matemática de caso não é hipótese exploratória; negação matemática adotada não é automaticamente NON_ADOPTED. Ambas podem ser ACTIVE se o predicado e seu papel forem validados. Se a gramática do checker não suporta a negação, isso afeta executabilidade, não autorização para apagar o conteúdo.

### 3.3 Resolver central

`DiscourseResolver` é nome proposto, não classe existente. Recebe fonte/ledger/sugestões e produz decisões versionadas com source receipts. Ordem lógica: validar binding → determinar contextos e atribuição → reconhecer proposições/roles → validar relações de adoção/revisão → resolver grafo temporal → publicar snapshot imutável de estados. Modelos não recebem pauta para escolher estados por score.

O grafo de substituição é acíclico e direcionado por ordem da fonte, não ordem de chegada dos objetos. Em cadeia A→B→C validada, A/B ficam SUPERSEDED, C ACTIVE; se C é falso, seu checker refuta C, sem ressuscitar A. Uma correção parcial afeta apenas o atributo/claim cujo alvo está validado. Ciclos, dois alvos indistinguíveis ou escopos concorrentes ficam AMBIGUOUS. Condições de caso diferentes não conflitam só por compartilhar obligation_id.

## 4. Matriz de autoridade

Mantém-se a matriz proposta, sem conceder hard veto automático a AMBIGUOUS:

| discourse_state | positive_credit_eligibility | conflict_visibility | hard_veto_eligibility |
| --- | --- | --- | --- |
| ACTIVE | Candidato, condicionado a binding, payload, rota, checker e sufficiency | Sim | Somente com contradição/refutação validada, contexto compatível e decisão central |
| SUPERSEDED | Não para o antigo | Histórico/audit; não como posição atual | Não |
| NON_ADOPTED | Não | Audit; não como posição atual | Não |
| AMBIGUOUS | Não para o próprio claim | Sim, para diagnóstico/review | Não automático nesta versão |

`positive_credit_eligibility` não é award: é licença para entrar na verificação positiva. Uma prova/verificação histórica de claim não ativo continua histórica. Guard matematicamente VERIFIED não é licença positiva e não completa método ou conjunto.

**Ambiguidade não é veto disfarçado.** Uma evidência AMBIGUOUS isolada não retira um award que possua suporte ACTIVE verificado e independente; acrescenta review. Se não houver qualquer testemunho positivo elegível — por exemplo, duas interpretações incompatíveis do mesmo span cuja adoção não se resolve — o resultado é `NO_POSITIVE_WITNESS`, não HARD_VETO. Esse motivo não pode aparecer quando já existe testemunho válido independente e o único obstáculo é uma evidência AMBIGUOUS. É um teste obrigatório de não equivalência entre “visível” e “bloqueante”.

Isso é deliberadamente diferente de manter uma suspeita como refutação. Não se promete zero falso crédito em todo texto que a validação não consegue interpretar: incerteza residual é registrada e medida, não ocultada por veto automático. Fechar S2_03 exige validar sua assertiva e sua incompatibilidade; classificá-la como AMBIGUOUS e bloquear o conjunto correto violaria esta matriz.

Ausência de checker/prova continua sem crédito para o candidato. Falha técnica continua technical uncertainty, não refutação. A política central registra a decisão de admissão, o resultado de sufficiency e o potencial veto; nenhum produtor escreve diretamente score/blocked.

## 5. Política geral de retratação

### 5.1 Receipt de substituição

Para marcar old como SUPERSEDED, requer-se uma relação validada com todos os seguintes elementos:

1. Old e new são claims com fonte literal íntegra e cláusulas identificadas. O marcador pode estar dentro de ambos os envelopes; o envelope não é a unidade de decisão temporal.
2. Há direção temporal de revisão: old precede new no discurso relevante. Ordem de processamento não participa. Referência explícita retrospectiva pode identificar old sem exigir vizinhança de bytes; associação “última afirmação” sem alvo não basta.
3. Mesmo objeto semântico/subject e contexto compatível: item, propriedade, índice de caso e obrigação/família de verificação devem coincidir por regra de mapeamento local. Igualdade de obligation_candidates do LLM sozinha não demonstra esse vínculo.
4. Existe ato de revisão/substituição/rejeição com alvo suficientemente determinado e nova posição adotada. Proximidade é evidência auxiliar; texto interveniente de outro subject não elimina uma referência explícita ao alvo, nem permite atravessar escopos arbitrariamente.
5. O novo conteúdo substitui a propriedade antiga. Para revisão implícita por contraste (“na verdade”), exige-se incompatibilidade semântica verificável da mesma propriedade. Para substituição explícita, a mudança pode apenas reafirmar um valor equivalente; pode ser colapsada como reformulação, sem criar conflito. Não se exige que toda contagem/cor do enunciado mude.
6. Há unicidade de alvo e de escopo; wrappers de hipótese/citação não adotada não fornecem correção atual. A correção do aluno pode ser falsa e ainda assim revogar a anterior.

O receipt deve guardar rule/version, ranges de old/new/marker, property_key, incompatibility/replacement witness, direction, scope, razões das alternativas rejeitadas e IDs canônicos. Um score nunca é input. Nenhuma lista de case_id ou regex específica dos textos observados pode compor essa regra.

### 5.2 “Na verdade” e incompatibilidade

`o quinto também. Na verdade, somente o sexto.` pode sustentar old→new: a relação é a mesma, os índices estão escritos e uma exclusão completa do quinto é incompatível com sua inclusão. A incompatibilidade é entre proposições do aluno; não vem de consultar qual compartimento é correto na resposta esperada.

`o quinto também. Na verdade, a probabilidade é 11/36.` não substitui necessariamente membership: subject/propriedade são diferentes. Sem referência explícita que retire o primeiro claim, ele permanece ACTIVE se sua adoção for confirmada; se a referência for incerta, AMBIGUOUS. Não marcar SUPERSEDED pelo marcador isolado.

Compatibilidade/incompatibilidade exige contrato tipado: duas igualdades da mesma quantidade com valores distintos, inclusão versus exclusão do mesmo membro, conjunto exaustivo versus inclusão externa, escolhas mutuamente exclusivas no mesmo caso. Dizer somente “texto diferente” não basta. Valores equivalentes não são contraditórios; duas cores podem ser simultaneamente ótimas em outro estado, logo o tipo de exclusividade precisa ser escrito/contratado, não presumido por nome de campo.

### 5.3 Autoridade do LLM

Pode sugerir assertion_status, abandoned, relação entre spans e candidate_discourse_state. Pode propor subspans e payload tipado, desde que os tokens e a transformação sejam conferidos localmente. Não decide sozinho SUPERSEDED, NON_ADOPTED com efeito em score, ACTIVE com autoridade positiva/negativa, hard veto, verdade matemática ou award.

O resolver deve validar os campos usados; confiança alta ou duas chamadas concordantes não substituem receipt. Uma relação não coberta pelos validadores locais permanece pendente. A menor migração reutiliza sugestões/campos atuais e análise da fonte; não exige trocar modelo, tuning nem alterar prompt nesta etapa arquitetural.

## 6. Política unificada de veto e reconciliação

### 6.1 Fluxo proposto

```text
source
  → semantic extractor (sugestões) ─┐
  → native source records ─────────┴→ SourceBindingAdapter → EvidenceLedger
  → DiscourseResolver → snapshot de estados e relações
  → PositiveEligibility (admissão; sem pontos)
  → ConflictVisibility (audit/active/review; sem bloqueio)
  → produtores matemáticos congelados + validadores estruturais de fonte
       ├─ verificação positiva / componentes / bridge por fato
       ├─ atomic guard (somente candidato negativo)
       ├─ safety regular (somente candidato negativo)
       └─ guard_bridge nativo (fatos desagregados; agregado só diagnóstico)
  → VetoCandidateAdapter + DependencyContract
  → VetoEligibilityPolicy (única autoridade negativa)
  → Reconciliation (consome decisões; não reabre raw flags/negativos)
  → AwardDecision com testemunho positivo + decisões centrais
  → PautaEvidence → PautaEngine inalterado → ScoreClosure inalterado
```

Não é necessário destruir produtores existentes; é necessário retirar sua autoridade paralela. Uma decisão central negativa é necessária para retirar suporte por contradição. Validações estruturais ainda podem impedir execução de um candidato inválido, mas só produzem diagnósticos/eligibilidade: não contaminam um positivo de outra evidência antes da política.

### 6.2 Contrato conceitual de PotentialVeto / VetoDecision

Campos mínimos, todos auditáveis:

| Campo | Semântica |
| --- | --- |
| candidate_id / policy_version / ledger_revision | Identidade estável por conteúdo e versão, não ordem de processamento |
| evidence_id / evidence_ids | Claim autor e eventuais premissas/contrapartes; aliases de EvidenceUnit/record nativo |
| obligation_id / target_obligation_ids | Obrigação de origem e alvos explicitamente alcançados pelo contrato; não um item inteiro |
| property_key / context_key | Propriedade, caso, quantificador, método/contexto condicional e polaridade |
| discourse_state / discourse_decision_ref | Estado do autor e de cada premissa, com receipt local |
| checker_status / checker_ref / checker_components | Status original, origem, versão, hash de input/modelo e scope da verificação |
| mathematical_contradiction | true/false/unknown; nunca deduzido só de formato, erro técnico ou abandoned |
| contradiction_witness / incompatible_award_predicate | Refutação da propriedade ou incompatibilidade tipada entre afirmações atuais |
| provenance | Produtor, source hash/ranges, literal tokens, binding receipt, histórico; guard_only |
| veto_reason / dependency_path | Motivo tipado e caminho permitido quando alvo difere da origem |
| hard_veto_eligible / policy_decision | boolean e decisão central; produtores não o autorizam |
| reconciliation_status | APPLIED / NOT_APPLICABLE / AUDIT_ONLY / REVIEW_ONLY / REJECTED_BINDING / TECHNICAL_PENDING |

Os nomes são contratos propostos, não campos supostamente presentes hoje. Nenhum candidato pode chegar a APPLIED com provenance faltante ou ledger_revision incompatível. A política usa a interseção dos requisitos, não um OR de todos os motivos atuais.

### 6.3 Predicado de hard veto

Hard veto requer cumulativamente:

- binding válido e resolvido para todos os claims que sustentam a contradição;
- adoção ACTIVE validada para essas premissas; não basta flag do LLM;
- checker matemático/validador de incompatibilidade com prova local suficiente, no escopo correto;
- contradição real com a obrigação/award candidato, e não somente evidência incompleta ou uso de outra condição;
- alvo na mesma propriedade/contexto ou em dependência negativa já contratada;
- receipt atual, com status epistêmico preservado e sem uso de guard como suporte positivo.

Refutação histórica de SUPERSEDED e erro sobre NON_ADOPTED ficam AUDIT_ONLY. AMBIGUOUS fica REVIEW_ONLY, hard_veto_eligible=false, mesmo se sua proposição hipoteticamente fosse matematicamente falsa. UNKNOWN/UNPROVED/ERROR não são prova de falsidade. Uma interpretação conflitante do mesmo envelope vira resolução/ambiguidade de candidato; não é automaticamente duas afirmações ACTIVE.

`CONFLICTING_FACT_RESULTS` é um agregado, não uma autorização. O adapter recupera fatos/records/proveniência e decide quais premissas são atuais. `CONFLICTING_CONDITIONAL_CONTEXTS` exige comparar contextos: casos diferentes podem coexistir sem contradição. Um agregado sem premissas recuperáveis fica diagnóstico/review, nunca hard veto por seu nome.

### 6.4 Convergência do atomic guard, safety regular e segundo veto nativo

O atomic guard mantém seu checker de membership e retorna candidato com evidência literal, sem authority final. A cópia de abandono não pode reativar campo/scope como decisão autônoma; passa a ser uma visão derivada do resolver, mantendo o original imutável. O guard_bridge nativo permanece disponível para detectar evidência que o LLM omitiu, mas é desagregado e vinculado ao **mesmo ledger/discourse snapshot** antes de qualquer veto.

Para S1_02/S1_07/S4_07, o registro nativo da versão antiga é vinculado ao mesmo claim SUPERSEDED já reconhecido no canal semântico. Nenhum caminho pode recolocá-lo como ACTIVE por ter record_id diferente. Sem tradução inequívoca de offsets/property/context, a associação fica AMBIGUOUS e sem hard veto; não se silenciam negativos ativos por proximidade textual aproximada.

Registros coletados diretamente da fonte podem originar candidatos positivos próprios após admissão e verificação positiva normal; isso não é promover o resultado de um guard. Um receipt guard_only, inclusive VERIFIED, nunca é reutilizado como certificado de award. A mesma proposição precisaria de uma cadeia positiva independente e autorizada desde a fonte, preservando I1.

Os checkers recebem uma projeção congelada de claims atuais compatíveis antes da composição. Assim, não se mistura cor antiga retirada com contagem final, nem se deixa um fato superseded tornar source_consistency incompleto. Results originais permanecem no trace como históricos. As mesmas rotinas matemáticas podem verificar a projeção admissível; não se reescreve um resultado FAILED como VERIFIED.

Um COMPOSITE_FAILED/INCOMPLETE que depende de source_consistency não pode ser “consertado” por trocar o status no adapter. Primeiro valida-se a atualidade das premissas de entrada; se a projeção foi alterada por retratação validada, os mesmos checkers verificam a projeção admissível e produzem novo recibo. Refutações atuais recuperadas fora dela geram candidato de veto pela dependência explícita. Assim, o componente matemático/contextual continua exigido e nenhuma retirada de suporte causada por produtor bruto dispensa a decisão central.

Durante migração, o audit nativo completo pode continuar rodando para diagnóstico, mas seu assessment, conflitos agregados e status refuted não são consumidos como comandos de bloqueio. Autoridade deriva somente dos fatos vinculados e aprovados pela política. `award()` perde o bypass V22 e a leitura direta de listas blocked sem policy receipt.

### 6.5 S2_03 e compatibilidade estrutural sem alterar matemática P3

A normalização negativa deve admitir **membership parcial tipado**, sem convertê-lo em conjunto completo. A mesma propriedade pode aparecer como `exact_set(S)` e `member(x,S)`. Um novo validador estrutural de relações escritas, na camada experimental, confere predicate/item/caso/índice/exaustividade e retorna receipt de incompatibilidade quando x não pertence ao conjunto explicitamente exaustivo. Esse validador é parte nova da arquitetura e não é alegado como já existente.

No caso observado, a primeira afirmação tem conjunto completo verificado pelo checker P3 existente; a segunda é uma inclusão própria explícita. A incompatibilidade escrita pode ser validada sem pedir ao LLM a verdade, sem criar {1,2,4} como fala do aluno e sem reutilizar o guard b.same para continuação em c. Seu receipt é negativo somente; nunca preenche uma obrigação positiva. A matemática/modelo/Lean já existentes não precisam mudar: a nova validação trata binding e relação entre proposições escritas, usando igualdade/pertencimento tipados, sem novo valor de referência ou teorema de P3.

Se a extração estrutural do predicado não puder ser conferida, o sistema não pode declarar contradição. Isso fica revisão/limitação de cobertura. O aceite da implementação exigirá que as classes de predicado especificadas tenham cobertura geral, incluindo as observadas; não é permitido “resolver” o caso por um veto da palavra unmapped, por case_id ou por hard veto de AMBIGUOUS.

Para A08/E08, um adapter de payload pode selecionar/normalizar somente a expressão ou enumeração **literalmente escrita**, com receipt de transformação conservadora. Não pode apagar lados falsos de uma igualdade, trocar operação, completar membros ausentes ou fabricar conta a partir de valor final. Ausência de payload validado continua sem positive witness; discourse_state sozinho não resolve isso.

### 6.6 Dependências negativas e positivas existentes

Manter três relações distintas: dependência matemática do checker; pré-requisito de crédito da pauta; propagação de refutação atual por contrato. Nenhuma cria pontos. Grafo permitido:

| Origem / requisito | Destino | Natureza e fundamento congelado |
| --- | --- | --- |
| b.ordered_pairs, b.different_favorable, b.same_compartment negativos atuais | b.second_white_probability | Veto de source_consistency já existente; não exige que as três estejam positivamente provadas |
| c.strategy_case_1 | c.conditional_success_1 | Context gate matemático; ausência não é refutação, falso atual pode invalidar o contexto |
| c.strategy_case_2 | c.conditional_success_2 | Mesmo contrato para o caso 2 |
| continuação, duas estratégias, duas condicionais | c.total_win_probability / regra c.total | Contexto exigido por _c e all_of da pauta; não propagar ao item a/b |
| duas estratégias e duas condicionais | regra c.conditionals | all_of da pauta, sem criar nova obrigação |
| seis ramos + soma ponderada escrita | b.alternative_complete | Testemunho composto já exigido pelo checker; falta é insuficiência, não hard veto |

Para source_consistency, a refutação atual do guard recebe o mesmo tratamento da refutação oriunda da projeção positiva, antes da decisão final de award. Erro técnico nessa dependência mantém TECHNICAL_PENDING conforme contrato, sem mathematical_contradiction=true. Ausência de qualquer uma das três contagens não veta resposta isolada de b. Um claim AMBIGUOUS não herda um veto técnico/matemático que só existiria se fosse ACTIVE.

Os demais requisitos de all_of/additive/max_of permanecem exclusivamente na pauta. I8 protege obrigações independentes **fora** desse grafo e das regras compostas; não promete preservar uma conclusão que já depende pedagogicamente de premissa refutada. Aplicação de dependências é por fechamento determinístico sobre snapshot, sem depender de quem rodou primeiro e sem declarar a conclusão matematicamente falsa se apenas seu contexto perdeu suporte.

### 6.7 Ausência de crédito, erros e I9

Decisões finais distintas: `ELIGIBLE_POSITIVE`, `NO_POSITIVE_WITNESS`, `INSUFFICIENT_METHOD`, `HARD_VETO`, `REVIEW_ONLY`, `TECHNICAL_PENDING`, `INVALID_BINDING`. Admissões negativas estruturais também passam pelo registro central; não são veto contra outra evidência. Falta de prova tem checker_status=NOT_ATTEMPTED/UNPROVED, não se inventa uma refutação para satisfazer auditoria.

I9 deve cobrir todo bloqueio automático: veto exige span + checker/validador + policy receipt. Quando simplesmente não há evidência na fonte, o receipt usa documento/item/obrigação e status de ausência do verificador, sem inventar source_span de um claim inexistente. Esse é diagnóstico de cobertura, não counterevidence nem hard veto. Um positivo previamente válido não pode ser retirado sob essa exceção. Gates de integridade da pauta continuam de defesa final e não recebem novos estados discursivos.

### 6.8 Fallback e Current

O modo comparador TME_CURRENT permanece explicitamente legacy e inalterado; seus resultados não são alegados como decisões da nova política. Já o **fallback do modo Semantic unificado** não deve continuar um bypass oculto V25: em falha de extractor, utiliza os registros nativos com resolver local, mesma política e decisão final. A falta de modelo não autoriza estados inventados; o que não é validável fica AMBIGUOUS/sem testemunho próprio.

Essa mudança é de orquestração experimental, não de checker/PautaEngine/ScoreClosure. O assessment legacy, se calculado para diagnóstico, não será o score final experimental. O effective_mode deve declarar fallback nativo sob a política unificada; não rotulá-lo TME_CURRENT_FALLBACK se deixar de ser equivalente ao Current. Preservam-se a contagem de falha de extractor, ausência de retry automático novo e separação de métricas. O contrato de fallback e sua diferença de comportamento precisam ser testados antes de ativar a arquitetura; não se altera o fallback histórico nem seus recibos.

## 7. Invariantes verificáveis

| ID | Invariante | Teste/asserção mínima futura |
| --- | --- | --- |
| I1 | Nenhum guard gera award | Guard VERIFIED/FAILED isolado → zero positive witness/award; não pode preencher método/dependência positiva |
| I2 | NON_ADOPTED não produz hard veto | Mesma proposição falsa em citação/hipótese não adotada → AUDIT_ONLY; positivo independente mantido |
| I3 | model_abandoned sozinho não produz hard veto | Variar somente flag não autoriza veto; exigir adoção local e refutação independente; nunca apagar negativo só pelo flag |
| I4 | SUPERSEDED não bloqueia a correção | Antigo falso em canal semântico, regular, atomic e nativo → todos sem hard veto; final ainda passa seu checker |
| I5 | AMBIGUOUS não gera positive credit | Claim ambíguo único/como premissa não entra em witness positivo |
| I6 | AMBIGUOUS não produz hard veto automático | Adicionar claim ambíguo a solução com witness ACTIVE válido → score desse witness inalterado, review=true; não usar no_positive_witness como atalho |
| I7 | ACTIVE + refutado pode bloquear award incompatível na mesma obrigação | Mesma propriedade/contexto + receipt negativo → APPLIED; outro contexto compatível não é bloqueado |
| I8 | Independência preservada | Conflito em família X só afeta X e dependências existentes; outra parcela fica idêntica |
| I9 | Todo bloqueio automático rastreável | APPLIED exige source spans/checker/policy/provenance; ausência documentada conforme §6.7, sem falso checker/refutation |
| I10 | Ordem de processamento não altera decisão para o mesmo estado final | Permutar listas de units/results/guards; mesmo ledger/discourse graph → mesmos awards/vetos; não permutar semântica temporal da fonte |
| I11 | Invariância a envelopes equivalentes | Expandir envelope sem mudar cláusulas/asserted_content/relação → mesmo estado e autoridade; S1/E02 como regressão observada, mais casos novos |
| I12 | Sem caminhos paralelos de autoridade | Injete negativos brutos em cada produtor sem policy receipt → nenhum blocked; todos os tipos passam pela mesma policy |
| I13 | Deduplicação e idempotência | Mesmo fato pelos canais nativo/semântico → um efeito, sem duplicar crédito/veto; repetir reconciliação não altera decisão |
| I14 | Substituição independe de correção matemática | Nova posição falsa validamente adotada supersede anterior; nova refutada, antiga não ressuscita |
| I15 | Conservação de informação e de escopo | Nenhum payload trunca igualdade, remove membro ou mistura propriedades; binder inválido não autoriza score/veto |
| I16 | Dependência negativa consistente por origem | Mesmo negativo pelo checker normal/atomic/regular/nativo → mesma aplicabilidade contratada, sem propagação global |
| I17 | Estado epistêmico preservado | UNPROVED/NOT_ATTEMPTED/ERROR não viram REFUTED; composite incompleto não vira falso por nome |
| I18 | Fallback também tem fronteira declarada | Semantic native fallback sem API usa mesma policy; Current comparador não é silenciosamente alterado |
| I19 | Recibo ligado à revisão | Alterar fonte/ledger/state invalida decisão anterior; sem policy token obsoleto no award |
| I20 | Compatibilidade de composição | Fatos compostos só usam premissas atuais do mesmo contexto/versão discursiva; nada de cor retirada + contagem final |

Os testes de I6 são condição de aceite, não mera nomenclatura: proíbe-se reter uma parcela já sustentada somente por existir AMBIGUOUS. Ordem textual pode mudar adoção e, portanto, score; I10 exige invariância **quando o estado semântico final é o mesmo**, não uma regra de “ordem nunca importa”.

## 8. Casos observados: contrafactuais de desenho, não novos resultados

Nenhuma expectativa foi alterada. As previsões abaixo dependem da implementação cumprir os contratos de parsing/estado/autoridade; não são scores medidos. A matriz de estados, sozinha, não garante que a representação necessária será reconhecida.

| Caso | Arquitetura atual → resultado/falha | Política proposta → estado/autoridade esperados | Parcelas/expectativa preservadas |
| --- | --- | --- | --- |
| S2_03 | Inclusão ativa de 4 vira unmapped/CONTEXT_REJECTED; conjunto {1,2} pontua 1 | Duas assertivas ACTIVE; conjunto completo e membership parcial tipados; incompatibilidade validada → veto central em c.continue. Se parser falhar, review e falha de cobertura, nunca “sucesso” por veto de AMBIGUOUS | Esperado 0; eliminar 1 indevido exige adapter estrutural |
| S2_06 | Guard refuta membership de 3, mas b.conclusion recebe 2; total 4 | Membership ACTIVE refutado; hard veto same + dependência source_consistency alcança conclusão. Different permanece independente | Esperado 2: b.different=2; b.conclusion=0 |
| S1_02 | Guard regular e guard_bridge nativo tratam 30 como atual; score 0 | Antigo SUPERSEDED por revisão vinculada apesar de envelopes sobrepostos; ambos canais AUDIT_ONLY; 36 ACTIVE verificado | b.space=2 |
| S1_03 | Cor retirada reativada e combinada com contagem final; 0 | Cor/contagem retiradas SUPERSEDED; composição final gray/3 ACTIVE; guard não usa antigo | c.second_strategy=2 |
| S1_07 | Substituição explícita sobreposta ignorada; dois vetos; 0 | {2,3} SUPERSEDED, {1,2} ACTIVE; identity bridge aplica estado também ao registro nativo | c.continue=1 |
| S4_07 | Probabilidade interposta impede vínculo de correção da contagem; dois vetos; 0 | Contagem 5 SUPERSEDED, contagem 2 ACTIVE; probabilidade 5/6 continua ACTIVE refutada, sem contaminar a.count | a.count=2; a.probability=0 |
| E02 replay | LLM abandoned correto, envelope antigo inclui correção; guard reativa quinto; 2 | Old membership SUPERSEDED, new exclusivo ACTIVE; validar relação entre cláusulas e não entre bordas; sexto passa checker | Esperado esclarecido 4: a.count=2 + b.same=2; fixture histórica intacta |
| E04 | Sexto e quinto permanecem adotados; guard bloqueia b.same; 2 | Ambos ACTIVE, sem marcador de retirada; refutação/incompatibilidade na mesma propriedade mantém veto; a.count independente | Preservar 2, não aplicar política “último vence” |
| A08 | Payload com prosa impede checker do total; 8→6 | ACTIVE sem retratação. Adapter fonte→expressão escrita preserva igualdade inteira; checker composto existente decide. Sem adapter válido continua sem witness, não culpa de discourse state | Expected 8; restauração dos 2 depende da representação validada e demais requisitos |
| E08 | Citação corretamente rejeitada; payload próprio em prosa não executa; 2→0 | Citação NON_ADOPTED; exclusividade própria ACTIVE. Adapter extrai membros explicitamente enumerados sem completar conjunto; checker original valida | Expected 2; não endurecer/relaxar contexto por nome da pessoa |
| S1_02/S1_07/S4_07 — segundo veto | guard_bridge.CONFLICTING_FACT_RESULTS suficiente mesmo sem guard regular | Desagregar fatos, vincular aliases e suprimir autoridade atual do superseded também no canal nativo | Nenhum veto residual por record_id/producer diferente |

Safety 02 permanece 2 falsos créditos/3 pontos na execução congelada; a tabela não recalcula essa história. Os quatro guard FPs somam 7 pontos perdidos, com sobreposição de produtores em três casos, sem multiplicar a perda. A08/E08 exigem solução de representação distinta da autoridade de veto. O único fallback safety_02 não vira medida de qualidade do extractor nem “caso corrigido” por este desenho.

## 9. Migração mínima e arquivos

Os nomes de novos módulos abaixo são propostas locais sob `experimental/tme_semantic_formal_p3`; não há exigência de modificar contratos públicos comuns nem P1/P2. Preservar reconciliação significa preservar sua função de reunir evidências e emitir decisão auditável, **não** manter intactas as condições OR que hoje autorizam vetos paralelos.

| Etapa | Trabalho futuro mínimo | Arquivos candidatos | Critério antes de avançar |
| --- | --- | --- | --- |
| 1 | Introduzir tipos imutáveis DiscourseState/decisions/ledger revision | novo discourse.py (ou módulo equivalente), evidence.py para associação sem mudar raw response | Serialização/proveniência; sem efeito em score inicialmente |
| 2 | Resolver central e receipts de adoção/revisão; identidade source/native | novo discourse_resolver.py, source_adapter.py; integrar evidence.py/mapper.py | Estados validados, equivalência de envelopes, source coordinates, casos sem modelo; não usar confiança como autoridade |
| 3 | Separar admissão positiva de contexto/representação | mapper.py e verification.py | PositiveEligibility explícita; rejeição de payload não apaga visibilidade |
| 4 | Visibilidade e contratos de payload/átomos estruturais | novo evidence_policy.py/source_adapter.py; registry.py se necessário para metadata de propriedade | AMBIGUOUS sem veto; partial membership não vira set completo; A08/E08 com transformações fonte-verificáveis |
| 5 | Política central e receipts de veto/dependência | novo veto_policy.py + metadata de dependências em registry.py | I1–I20 e grafo contratual; nenhuma inferência de regra por score |
| 6 | Fazer todos os produtores convergirem, inclusive guard_bridge e negativos diretos | engine.py, abandonment.py, conflict_guard.py, verification.py; novo adapters.py se útil | V13/V19/V20/V22 não autorizam bloqueio por fora; raw producer output é só dado |
| 7 | Reconciliação/award/fallback experimentais consomem só decisões centrais | engine.py; funções reconcile/award/evaluate; checker wrappers de projeção | Um snapshot por execução, order independence, native fallback explícito, Current preservado |
| 8 | Deprecar branches antigos após equivalência e auditoria de chamadas | mesmos módulos experimentais; testes focais novos | Nenhum consumidor restante de raw abandoned/negative/conflict para score; remover autoridade duplicada antes de ativar |

Etapas 1–5 podem rodar como diagnóstico sem efeitos; ativar score somente quando a convergência de 6–8 estiver completa. Não ligar uma mistura “metade policy nova, metade guard antigo”. Configuração/versionamento deve identificar a arquitetura única usada; não deixar caminhos legados como fallback silencioso de autoridade.

Checkers/produtores podem ser invocados por wrappers experimentais com uma projeção validada. Não alterar `P3Checks`, `StrongP3Checks`, componentes matemáticos, finite_certificate, máquina/asset, Lean ou `bridge_facts`. O adapter consome validações por fato e não trata o agregado histórico como estado atual. Registros novos devem ser verificados de fato; não remapear um receipt antigo de payload modificado.

**Não requer mudança** de PautaEngine, pesos, score closure, expected labels, fixtures, P1/P2 ou TME_CURRENT. A validação estrutural fonte/relação é nova lógica experimental necessária à política, não alteração das proposições/cálculos matemáticos de P3. Ela deve ter testes próprios e receipts; não pode ser introduzida como pós-processamento não auditado. Não foi identificada necessidade inevitável de alterar qualquer componente protegido. Se a implementação encontrar uma dependência que exija isso, deve interromper a ampliação de escopo e justificar antes, sem adaptar expectativa observada.

Testes candidatos novos: `test_tme_p3_discourse_state.py`, `test_tme_p3_veto_policy.py`, `test_tme_p3_source_adapter.py`, `test_tme_p3_unified_reconciliation.py` (nomes propostos). Revisar testes existentes de abandonment/conflict apenas pelo contrato geral aprovado; não reescrever fixtures observadas para esconder regressão. Nenhum arquivo citado foi alterado nesta tarefa.

## 10. Estratégia de validação futura

### Etapa A0 — contratos e invariantes, sem modelo

Testes locais gerados por propriedade/combinação: estados × origem nativa/semântica × matemática verified/refuted/unproved/error × mesmo/outro subject × mesmo/outro contexto; pares exaustivo/membership; substituição com/sem marcador/alvo; revisão falsa; relações encadeadas; mesmo envelope com claims distintos; igualdade com vários lados; caso condicional legítimo versus hipótese; negação adotada; citação com/sem adoção explícita. Nenhum teste usa case_id para decidir lógica.

Testes metamórficos obrigatórios: permutar processamento; duplicar candidato em dois produtores; variar envelope sem mudar asserted_content; reordenar formatação preservando relação; manter texto e alterar só flags do modelo; retirar policy receipt; introduzir estado NON_ADOPTED/SUPERSEDED/AMBIGUOUS negativo ao lado de um positivo independente. Falhas devem indicar exatamente qual premissa/decisão autorizou o efeito.

Executar integrações matemáticas/Lean existentes pertinentes para demonstrar preservação, não para reestimar benchmarks. Comparar resultados de checkers sobre as mesmas entradas válidas, hashes de pauta/máquina/toolchain e score closure. Testar fallback experimental e Current separadamente. Nenhum erro técnico pode virar falsa prova ou refutação.

### Etapa A1 — regressão observada

Usar DEV01/DEV02, semantic_robustness_01 e semantic_safety_02 exclusivamente como observados. Preservar fontes, expectativas e recibos históricos; resultados novos em diretórios/versionamento separados. Primeiro replay com respostas gravadas para isolar política/normalização de variação de extração. Replays são testes novos, não alteração dos registros. Comparar também o binding gerado pelo raw_output, não apenas score final.

O controle E02 esclarecido de 4 deve permanecer em contrato/sidecar explícito, sem editar expected=2 do arquivo histórico. Para casos DEV sem gold independente, usar classificação forense registrada antes da nova execução; não inventar labels ajustados à nota. Um eventual rerun real dos observados é só regressão de integração, com protocolo e autorização próprios; não é avaliação independente nem pode substituir falha do replay. Fallbacks sempre separados.

Métricas de regressão: falsos awards/pontos; superseded/NON_ADOPTED usados como veto; hard veto de AMBIGUOUS; aceitação de retratação legítima; cobertura de negativos ativos; fechamento de dependência; preservação de parcelas independentes; awards de guard=0; invariância entre produtores; fallback/technical uncertainty; exact/MAE e precision/recall secundários. Mesmo score não garante ausência de falso crédito compensado por perda de outra parcela.

### Etapa B — semantic_safety_03 novo e independente

Somente após congelar implementação e protocolo, construir um conjunto inteiramente novo, sem copiar ou parafrasear trivialmente casos/expectativas observados. Cobrir autocorreção, conflito, abandono, ambiguidade, citação, hipóteses, ordem textual e subjects distintos; cruzar com envelope sobreposto, versão nativa duplicada, resultado isolado versus método e dependência negativa. Incluir casos em que a correção final é falsa e em que a frase ambígua não deve vetar outro positivo válido.

Congelar fontes, IDs, expectativas por construção, receipts de discourse states/relations/authority e hashes antes das execuções; extractor recebe somente o contrato de interpretação/fonte. Publicar SHA/configuração, regras de aceitação e budget de execução/retry antes de observar resultados. Uma rodada por modo conforme protocolo; erro operacional e fallback registrados, não substituídos por nova amostra escolhida. Não decidir tamanho amostral por quantos casos passam; dimensionar a matriz de cobertura antes de rodar.

O aceite independente exige zero falso crédito material, zero award de guard, zero hard veto de SUPERSEDED/NON_ADOPTED/AMBIGUOUS, nenhum veto nativo residual e rastreabilidade completa dos bloqueios. Cobertura insuficiente de classe obrigatória, retratações legítimas sistematicamente perdidas ou falha técnica que impeça observar um estrato limitam o veredito; não declarar sucesso apenas porque os negativos receberam zero. Separar ALL e Semantic-success, e não usar gold externo/holdout TME.

**Somente semantic_safety_03 pode validar independentemente a futura correção.** Regressões observadas explicam o desenho e detectam perdas, mas não demonstram generalização. Safety 03 ainda não foi criado nem executado.

## 11. Integridade e conclusão arquitetural

Foram inspecionados o fluxo P3, seus validadores/bridges/checkers alcançáveis, os quatro relatórios e os contratos de pauta. O conjunto de 376 arquivos inventariados de código experimental, fixtures P3 e artefatos relevantes permaneceu byte a byte igual. Nenhum teste, API, piloto ou benchmark foi executado. Nenhum relatório anterior ou expectativa foi editado.

Estado final previsto e conferido ao encerrar:

```text
?? docs/audits/TME_P3_UNIFIED_DISCOURSE_VETO_ARCHITECTURE_01.md
```

HEAD: `1dea197ab5e3ee40597acc3d35af3cb8dcc4d4c3`; sem stage/commit. O resultado desta tarefa é projeto de arquitetura, não alteração de status de segurança P3. O código continua com o comportamento congelado diagnosticado como P3_SAFETY_FAILURE.

A autoridade única fica na política central sobre estados e receipts; matemática permanece nos checkers, pontos permanecem na pauta, e hipótese/retratação/ambiguidade não são usadas como sinônimos de falsidade. A sequência de implementação e os critérios de aceite acima são suficientes para iniciar trabalho futuro dentro do escopo, com os limites de parsing/independência explicitados.

**ARCHITECTURE_READY_FOR_IMPLEMENTATION**
