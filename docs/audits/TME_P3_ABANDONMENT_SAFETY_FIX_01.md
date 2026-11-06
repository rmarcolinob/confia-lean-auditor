# TME P3 — Abandonment Safety Fix 01

## 1. Escopo, base e definição confirmada

Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3`. SHA inicial e final, sem commit: **`f335760e9424fb122f24afab6b459f784491aa32`**.

O estado inicial já continha, não rastreados, o relatório `TME_P3_SEMANTIC_ROBUSTNESS_01.md` e o diretório de fixtures `semantic_robustness_01/`. Ambos foram preservados. Esta tarefa não executou extractor real, não rerodou o benchmark, não criou nova avaliação independente e não usou holdout/gold externo.

Havia uma incompatibilidade entre exigir E02 bloqueado e considerar “Na verdade” seguido de correção incompatível uma retratação legítima. O usuário esclareceu expressamente:

> Não: aceitar E02 como autocorreção; revisar a expectativa controlada.

Essa definição orienta este fix. **A expectativa do controle pós-fix de E02 é 4 pontos**, e não 2: a.count=2 e b.same=2, com a afirmação anterior retratada. Não foram modificadas as expectativas, métricas ou classificações históricas do benchmark observado; seu E02 permanece com expected=2 e resultado=4 no arquivo congelado. Não foi recalculada a bateria sob a política nova.

**READY_FOR_P3_SAFETY_REVALIDATION.** A falha genérica de confiar em abandono apenas inferido foi corrigida no caminho de segurança. E02 agora serve de controle de retratação aceita pela definição esclarecida; os controles sem suporte textual demonstram a recuperação para veto.

## 2. Forense E02 × E04

Fontes: [E02 observado](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_e02.json) e [E04 observado](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_robustness_01/tme_semantic_formal/p3_rob_e04.json).

Ambos têm a evidência independente “Há duas bolas brancas embaixo.”, verificada pela máquina e responsável por a.count=2.

| Etapa | E02, no benchmark | E04, no benchmark |
| --- | --- | --- |
| source_span contraditório | “Ao repetir o mesmo compartimento, o quinto também libera branca.” | Envelope “Ao repetir o mesmo compartimento, somente o sexto libera branca.\nO quinto também.” |
| Ordem / contexto posterior | Em seguida: “Na verdade, ao repetir o mesmo compartimento, somente o sexto libera branca.” | Sexto antes da elipse do quinto; nenhuma retratação |
| normalized_claim | “Ao repetir o mesmo compartimento, o 5 também libera branca.” | `{5, 6}` |
| assertion_status / polarity | abandoned / positive | asserted / positive |
| hypothetical / abandoned | false / true | false / false |
| attributed_to_student / scope | true / main_argument | true / main_argument |
| Mapper | Rejeita nonasserted_or_unattributed_context | Rejeita set_members_not_written |
| Guard anterior | Invisível: rejeição de contexto não é recuperável; flags também barram _bound_context | Rejeição de representação recuperável, com contexto válido |
| Checker da evidência negativa | Nenhum | frozen_finite_certificate_same_white_membership |
| Status negativo | CONTEXT_REJECTED, sem refutação matemática | DETERMINISTIC_FAILED no guard; membro 5 |
| Reconciliação | Sem conflito de b.same | CONFLICTING_EVIDENCE em b.same |
| Award final | a.count=2 e b.same=2 | Somente a.count=2 |

O payload `{5,6}` de E04 não foi usado como conjunto completo para conceder crédito. O guard anterior recuperou apenas o token literal “quinto”, derivou membership_claim(compartment=5) e consultou a máquina. A segunda bola do evento (5,5) é preta; a diagonal favorável derivada é somente (6,6).

### Ponto exato da perda anterior

1. [mapper.py:133](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:133): exige asserted e not abandoned; E02 recebe `nonasserted_or_unattributed_context`.
2. [verification.py:28](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py:28): somente mapeamentos accepted são projetados para checkers. O quinto deixa de participar da verificação matemática normal.
3. [conflict_guard.py:37](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py:37): `_bound_context` exige asserted/not abandoned; além disso, `REPRESENTATION_REJECTIONS` não admite a rejeição contextual. O guard também não examina o quinto.
4. [verification.py:108](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py:108): o recibo permanece CONTEXT_REJECTED e mathematical_refutation=false.
5. A reconciliação recebia somente o positivo do sexto, sem uma refutação ou evento negativo da mesma família.

A vulnerabilidade era confiar no flag do modelo como autorização suficiente para retirar evidência da segurança. Segundo a definição nova, E02 possui suporte textual real e pode ser suprimido; uma afirmação equivalente marcada abandoned sem esse suporte não pode.

## 3. Política anterior e política nova

Antes, o mesmo filtro contextual excluía a evidência do crédito positivo e do conflito, sem validar textualmente o abandono.

Agora, `abandoned=true` ou `assertion_status=abandoned` provoca uma decisão determinística local e auditável:

- **Retratação textual sustentada:** mantém a inelegibilidade da afirmação anterior e autoriza sua supressão do caminho de conflito.
- **Abandono inferido ou ambíguo, sem outro veto contextual válido:** preserva a evidência em uma cópia usada somente para segurança.
- **Outro contexto não adotado, fonte inválida, hipótese, citação, atribuição ausente ou polaridade inválida:** não cria uma posição matemática atual do aluno.

O validador reconhece marcadores explícitos no span, rejeição deítica imediatamente posterior (“Isso está errado”, “corrigindo minha afirmação anterior”, “desconsidere a minha afirmação anterior”, “não, o correto é”), ou correção adjacente introduzida por “Na verdade”/“Corrigindo”. Neste último caminho exige mesmo item, mesmo subject/família, correção adotada e dois conteúdos diferentes vinculados à fonte. Não procura a última frase arbitrariamente nem atravessa outra afirmação para revogar a primeira.

Para E02, o vínculo é: membro escrito 5 → correção adjacente do mesmo subject `repeticao_branca` → exclusividade escrita de 6. O comparador de conteúdo não decide a verdade matemática; a correção positiva continua sendo validada pelos checkers originais.

A validação não usa score, case_id, expectativas, resultados do benchmark ou verdade matemática pré-fixada. O fallback textual para pertencimento lê ordinais/índices da fonte e não cria um conjunto para crédito.

## 4. Implementação e separação dos caminhos

| Arquivo | Alteração |
| --- | --- |
| [abandonment.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/abandonment.py) | Novo validador local, decisões de visibilidade e verificação regular somente para segurança |
| [engine.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py) | Integra cópia de segurança, recibos e refutações na reconciliação |
| [conflict_guard.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py) | Uma linha para anexar a decisão de abandono ao recibo atômico |
| [test_tme_p3_abandonment_safety.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_abandonment_safety.py) | 30 testes novos, incluindo respostas gravadas equivalentes a E02/E04 |
| [test_tme_p3_conflict_preservation.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_conflict_preservation.py) | Retira duas expectativas antigas de supressão por flag isolado; passam a ser cobertas pelo novo contrato |
| Este relatório | Diagnóstico, política esclarecida, validação e limites |

O mapper, verification, extractor/prompt, registry, checkers matemáticos, pauta/pesos, máquina, ScoreClosurePolicy e P1/P2 permanecem byte a byte iguais.

Os EvidenceUnits originais e seu mapeamento positivo permanecem intactos. Quando um abandono não é sustentado, uma cópia conserva IDs, spans, hashes e conteúdo, mas normaliza apenas os campos necessários para entrar no caminho de segurança. O scope original fica no recibo; um scope exploration/unknown associado ao abandono inferido não basta, por si só, para apagar a evidência, desde que os demais vetos contextuais estejam ausentes.

Há dois caminhos de recuperação:

```text
abandono sem suporte → cópia de segurança → mapper existente
  ├─ representação compatível → verify/checkers existentes, use_lean=False
  └─ pertencimento parcial incompatível → atomic conflict guard existente
→ refutação independente → reconciliação da mesma obrigação → award bloqueado
```

A checagem regular adicional permite cobrir também formatos válidos e outras famílias, como probabilidades contraditórias, sem depender da palavra “também”. Ela só é executada quando existe evidência recuperada. Não produz observações pontuáveis.

Cada recibo de segurança registra `guard_only=true`, `award_eligible=false`, `sufficiency_decision.sufficient=false`. Resultados verdadeiros também são inelegíveis. Somente `mathematical_refutation=true` acrescenta veto à reconciliação. Não se promove um resultado do guard a `award`, nem se confunde ausência de prova com refutação.

## 5. Rastreabilidade

As novas `abandonment_decisions` preservam:

- evidence_id, source_span, offsets, source_sha256, item e subject;
- model_abandoned, model_assertion_status e model_scope;
- abandonment_textually_supported, abandonment_reason e retraction_source_span;
- other_context_valid, effective_conflict_visibility e positive_credit_eligible=false.

O canal `abandonment_guard_results` conserva os recibos dos checkers regulares usados somente para segurança. O guard atômico recebe `abandonment_decision` quando aplicável. O CONTEXT_REJECTED original continua visível e não é convertido em crédito positivo.

## 6. Resultados controlados, sem API

| Controle | Score | Visibilidade da evidência anterior | Resultado |
| --- | --- | --- | --- |
| Resposta gravada equivalente a E02 | **4** | false; adjacent_same_subject_correction | Autocorreção aceita conforme esclarecimento; a.count=2 e b.same=2 |
| Resposta gravada equivalente a E04 | **2** | Guard atômico como antes | Quinto refutado; b.same bloqueado; a.count preservado |
| Quinto adotado, mas modelo marca abandoned, sem retratação escrita | **2** | true; no_unambiguous_local_retraction | Refutação preservada; conflito em b.same; somente a.count |
| “Isso está errado” imediatamente após o quinto, seguido do sexto | **4** | false; immediate_explicit_retraction | Afirmação inicial registrada, solução corrigida aceita |
| Evidência verdadeira recuperada somente no guard, sem positivo elegível | **0** | true | Nenhum award pode nascer do guard |
| 12/36 marcado abandoned sem retratação, junto de 11/36 | **0** | true | Checker regular refuta; conflito em b.second_white_probability |

Todos os controles mantêm score numérico, sem fallback ou chamada real à API. Os controles E02/E04 usam o conteúdo completo das respostas já gravadas, incluindo flags e source_evidence_ids; não são nova extração nem rerun dos 48 casos.

**Não se afirma que o fix reduziu o score de E02.** Ele continua 4, agora considerado legítimo pela definição expressamente confirmada pelo usuário. A demonstração da correção de segurança está nos controles de abandono sem suporte textual, que preservam a contradição para veto.

Recibos e logs: [artefatos do fix](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_abandonment_safety_fix_01).

## 7. Testes e regressões

| Seleção | Resultado |
| --- | --- |
| Nova suíte abandonment safety | 30 PASS |
| Conflict preservation, contrato atualizado | 41 PASS |
| Semantic Formal P3 | 132 PASS |
| Bridge P3 | 70 PASS |
| PautaEngine | 100 PASS |
| Checker-first P3 | 90 PASS |
| Integrações Lean P3 (Semantic + checker-first) | 21 PASS |
| Relacionados P3 (semantic_claims, hybrid_grader, scope_boundary) | 6 PASS; 132 deselected |
| **Total distinto** | **490 PASS** |

As 462 verificações anteriores tinham duas parametrizações que afirmavam que `abandoned` isolado deveria suprimir o guard. Essa expectativa é incompatível com o princípio solicitado. Elas foram substituídas por testes explícitos de recuperação, não mantidas como supressão silenciosa. Portanto: **419 regressões anteriores + 41 de conflito mantidas + 30 novas = 490**. Nenhum teste ou expectativa de fixture DEV foi alterado.

Cobertura nova: flags isolados e combinados, scopes inferidos, payload válido e prosa, duas ordens sem retratação, quatro marcadores explícitos, “Na verdade” adjacente, texto interveniente/terceiro que não revoga, hipóteses/abandono real, guard verdadeiro sem crédito, refutação probabilística regular, integridade da fonte, créditos independentes, score numérico e baseline preservado.

TME_CURRENT foi comparado antes/depois da chamada experimental por bridge, assessment, awards, credits, conflitos e score. Seu caminho não usa a nova camada. Não se afirma identidade byte a byte do JSON inteiro, pois hashes da implementação experimental mudaram legitimamente.

### Comandos

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app:$PWD" CONFIA_TME_SEMANTIC_ENABLED=0
P3_PYTHON=/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python

"$P3_PYTHON" -m pytest tests/test_tme_p3_abandonment_safety.py tests/test_tme_p3_conflict_preservation.py -q -p no:cacheprovider --basetemp=/private/tmp/p3-abandonment-fix-01/focal --junitxml=/private/tmp/p3-abandonment-fix-01/focal.xml
"$P3_PYTHON" -m pytest tests/test_tme_semantic_formal_p3.py tests/test_tme2_p3_pauta_bridge.py tests/test_pauta_engine.py tests/test_tme_p3_checker_first.py -q -p no:cacheprovider --basetemp=/private/tmp/p3-abandonment-fix-01/regression --junitxml=/private/tmp/p3-abandonment-fix-01/regression.xml
"$P3_PYTHON" -m pytest tests/test_tme_semantic_formal_p3_lean.py tests/test_tme_p3_checker_first_lean.py -q -p no:cacheprovider --basetemp=/private/tmp/p3-abandonment-fix-01/formal --junitxml=/private/tmp/p3-abandonment-fix-01/formal.xml
"$P3_PYTHON" -m pytest tests/test_semantic_claims.py tests/test_tme_hybrid_grader.py tests/test_scope_boundary.py -k TME2026P3 -q -p no:cacheprovider --basetemp=/private/tmp/p3-abandonment-fix-01/related --junitxml=/private/tmp/p3-abandonment-fix-01/related.xml
```

## 8. Lean e preservação matemática

As 21 integrações formais executaram a infraestrutura Lean real existente e passaram em 274,33 s. Nenhum arquivo de checker Lean ou tática foi alterado. Os controles formais deliberados de erro/ausência de prova continuam separados de refutação; o sucesso da suíte não significa que cada proposição de teste foi provada.

A nova consulta regular de segurança usa os mesmos checkers com `use_lean=False`, apoiando-se na verificação determinística já disponível. Não cria `FORMAL_VERIFIED` para esse caminho. A consulta de pertencimento continua usando o certificado finito congelado. As rotas Lean positivas anteriores e seus statuses foram preservados.

## 9. Preservação do dataset observado e limites

`semantic_robustness_01` é **DEV observado**. Pode servir posteriormente a regressão pós-fix, mas não a avaliação independente desta correção. Os cinco arquivos, seus hashes, os resultados do benchmark e seu relatório anterior permanecem intactos. Nenhuma expectativa foi ajustada retroativamente.

A camada é deliberadamente limitada à validação de sinais de abandono existentes. Não é um novo extractor geral de retratações; se o modelo mantiver dois claims como asserted, a reconciliação original continua aplicável. Os testes de duas afirmações adotadas continuam distintos dos controles em que o modelo propõe abandono e a fonte o sustenta. Não se promete reconhecimento universal de autocorreções em linguagem natural.

Quando o suporte textual é ambíguo, a afirmação marcada como abandonada permanece candidata à checagem de segurança. Isso não garante representação executável para toda prosa: aplicam-se os contratos/gramáticas existentes. Outros flags de contexto (hipótese, atribuição, polaridade), os limites de fonte e os checkers não foram globalmente redesenhados.

O próximo passo recomendado é um conjunto inédito `semantic_safety_02`, com a política de retratação explicitamente congelada antes da execução: conflitos, retratações, autocorreções, hipóteses, abandono, atribuição e ordens textuais. Esse benchmark **não foi criado nem executado nesta tarefa**.

## 10. Git e veredito

Comparação com o snapshot inicial de 988 caminhos: somente três arquivos preexistentes foram alterados — engine.py, conflict_guard.py e o teste de conflito. Os demais 985, incluindo fixtures/resultados/relatório do benchmark observado, foram preservados. Adicionados: abandonment.py, teste novo e este relatório.

Estado final esperado, conferido ao encerrar:

```text
 M app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py
 M app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py
 M tests/test_tme_p3_conflict_preservation.py
?? app/confia_lean_auditor/experimental/tme_semantic_formal_p3/abandonment.py
?? docs/audits/TME_P3_ABANDONMENT_SAFETY_FIX_01.md
?? docs/audits/TME_P3_SEMANTIC_ROBUSTNESS_01.md
?? tests/fixtures/tme_semantic_formal_p3/semantic_robustness_01/
?? tests/test_tme_p3_abandonment_safety.py
```

Os dois caminhos de robustness já estavam não rastreados no início. SHA inalterado: `f335760e9424fb122f24afab6b459f784491aa32`. Sem stage ou commit automático.

**READY_FOR_P3_SAFETY_REVALIDATION**

