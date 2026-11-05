# C1 — arqueologia do pipeline TME e diagnóstico de P1

Data: 2026-11-04. Base examinada e HEAD: `1b3daea41ba4ce31c0cfd35dd07907da3d03669f`.
Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-c1`.

Esta entrega conclui a etapa solicitada **antes da implementação**. O C1 não foi implementado nem executado. Nenhum arquivo preexistente do pipeline foi editado. As referências abaixo derivam do código desta base; relatórios históricos não foram tratados como prova de execução atual.

## 1. Diagnóstico principal

O repositório não tem um único encadeamento chamado “TME atual”. Há um caminho integrado à aplicação, um suplemento de extração semântica habilitado por ambiente e entradas experimentais separadas para extração por obrigação, Evidence IDs, julgamento híbrido e sufficiency.

P1 já possui **21 obrigações**, verificadores determinísticos, duas integrações específicas de igualdade aritmética com Lean, uma ponte que valida proveniência e um PautaEngine independente. Já existe crédito positivo originado em `student_lean`. O trabalho de C1 é compor e restringir esses mecanismos com um novo contrato de evidência, não criar outro corretor matemático ou outra pauta.

Há cinco diferenças materiais entre o contrato pedido e o comportamento atual:

1. `PautaEngine` pode devolver `score=None` em erro técnico; `withhold` não elimina essa possibilidade.
2. O julgamento híbrido existente decide `satisfied`/`contradicted` por obrigação e recebe uma solução oficial. Ele não é o extractor de claims sem autoridade matemática descrito no C1.
3. O reconciliador pode preservar suporte auditado mesmo ao registrar conflito. A policy não é um veto universal a crédito formal/determinístico em conflito.
4. Os contratos atuais não contêm, juntos, `polarity`, `scope`, `hypothetical`, `abandoned`, rota e todos os estados epistemológicos pedidos.
5. Texto completo e documento digital composto têm coordenadas diferentes. Reutilizar IDs exige preservar essa distinção, além das fronteiras entre itens corrigidas no commit-base.

## 2. Localização real dos componentes

Os caminhos desta tabela são relativos à raiz do repositório. Sob `app/confia_lean_auditor/`:

| Responsabilidade | Arquivo e símbolo reais |
|---|---|
| Entrada HTTP TME | `tme/router.py`, endpoint `POST /tme/cases/{case_id}/audits` (linha 213) |
| Serviço de auditoria aceita | `submission_audits/service.py`, desvio TME em `execute` |
| Adaptação de transcrição aceita | `tme/accepted_audit.py`: `split_accepted_items` (42), `audit_accepted_tme_transcription` (95) |
| Dispatcher matemático TME | `tme/registry.py`: `audit_tme` (18) |
| Composição P1 | `rubric/pauta/tme2_p1.py`: `audit_tme2_p1_digital` |
| Entrada de extração P1 | `student_claims/tme2_p1_digital.py`: `collect_tme2_p1_digital` |
| Montagem e roteamento por item | `student_claims/digital_items.py`: `DigitalItemClaims`, `collect_digital_items` |
| Extração local | `student_claims/registry.py`, `generic_math.py`, `digital_literals.py` |
| Claims e fonte comuns | `claims/common/schemas.py`, `claims/common/adapters.py` |
| Suplemento semântico original | `student_claims/semantic.py`: `supplement`, `supplement_scope`, `convert_candidate` |
| Interpretação por obrigação | `student_claims/obligation_semantic.py`: `ProjectionSession`; `tme/obligation_experiment.py` |
| Evidence IDs | `student_claims/evidence_units.py`; `student_claims/evidence_id_semantic.py`; `tme/evidence_id_experiment.py` |
| Avaliação semântica global | `student_claims/hybrid_semantic.py`: `request_judgments`, `SemanticObligationJudgment` |
| Auditoria seletiva e reconciliação | `tme/hybrid_grader.py`: `selective_audit` (73), `EvidenceReconciler` (115) |
| Sufficiency | `student_claims/semantic_sufficiency.py`: `SemanticSufficiencyGate` (107) |
| Contexto e requisitos de sufficiency | `student_claims/sufficiency_context.py`, `student_claims/sufficiency_requirements.py` |
| Composição de sufficiency | `tme/sufficiency_experiment.py`: `reconcile_sufficiency`, `run_sufficiency_shadow` |
| Checkers P1 | `lean/student_claim_checkers/tme2_p1.py`: `verify_tme2_p1_digital` (305) |
| Montagem de fatos | `claims/common/fact_results.py`: `FactResultsBuilder` |
| Ponte para pauta | `rubric/pauta/bridge.py`: `FactResult`, `AuditorFactBundle`, `bridge_tme2_p1`, `bridge_facts` |
| Policy semântica opt-in | `rubric/pauta/evidence_policy.py`: `HybridEvidencePolicy` |
| Contratos e pontuação | `rubric/pauta/models.py`; `rubric/pauta/engine.py`: `PautaEngine` (37) |
| Checker Lean aritmético | `lean/student_claim_checker.py`: `check_one_student_claim` |
| Semântica de prova/refutação | `lean/student_proof.py`: `evaluate_student_proof`, `grounded_checker` |
| Canonicalização e sintaxe | `core/math_canonical/`, especialmente `syntax.py` |

Fora dessa raiz de módulos:

- Enunciado público: `problems/TME2026P1/problem.json`.
- Pauta: `examples/pautas/tme2_problem1.v1.json`.
- Fixture digital P1: `tests/fixtures/tme2_p1_digital/cases.json`.
- Runner digital histórico: `scripts/evaluation/run_tme2_p1_pauta_pilot.py`.
- Runner semântico com duas etapas novas por modelo: `scripts/evaluation/evaluate_tme_model_ablation.py`, `_run_arm` (167).
- Infraestrutura Lean: `lean-toolchain`, `lakefile.toml`, `lake-manifest.json`.

**Nomes não encontrados como componentes implementados de C1:** `TMEEvidenceUnit`, `SemanticExtractorTME`, `ObligationMapper`, `ClaimRouter`, `TME_SEMANTIC_FORMAL`. Também não há classe chamada `SemanticRubricEvaluator`: esse nome arquitetural corresponde funcionalmente a `hybrid_semantic.py`. Não confundir os mecanismos de award do pipeline ITA com um AwardGate C1 já existente.

## 3. Fluxo integrado real de P1

```text
entrada digital ou imagem → revisão/transcrição aceita
→ AuditService.execute
→ audit_accepted_tme_transcription
→ split_accepted_items
→ audit_tme("TME2026P1", {item: texto}, use_lean=...)
→ alias interno "TME2_P1_PILOT" + carregamento da pauta
→ audit_tme2_p1_digital
  → collect_tme2_p1_digital → collect_digital_items
  → verify_tme2_p1_digital → AuditorFactBundle
  → bridge_tme2_p1 → PautaEvidence
  → PautaEngine.evaluate → PautaAssessment
→ TMEAuditResult + artefatos de auditoria e certificados
```

O adaptador aceita metadados explícitos `tme_item_id` ou cabeçalhos isolados como `[a]`, `(a)`, `a)`, `Item (a)`. Texto sem item produz aviso e não é atribuído por inferência matemática. O recibo e o hash da revisão aceita são validados antes da auditoria.

`collect_digital_items` monta um novo documento com `[a]\n`, conteúdo do item e separadores. Seus offsets e `source_sha256` pertencem a esse documento composto, não diretamente à transcrição original. Limite de entrada: 20.000 caracteres. Os registros são atribuídos a um item apenas quando seu span cabe integralmente na região dele.

A extração junta literais digitais e claims genéricos; os extractors específicos do registry são ITA, portanto P1 depende da extração genérica/literal e do suplemento opt-in. Fragmentos contidos em uma coleção literal já reconhecida são removidos da extração genérica para evitar duplicação.

Ao final da coleta, `semantic.supplement` é chamado. Por padrão `CONFIA_TME_SEMANTIC_ENABLED=0`: apenas os registros locais permanecem. Com a variável em `1`, candidatos LLM passam por grounding, atribuição, contexto e representação antes de virar `MathClaimRecord`. Um `ContextVar` via `supplement_scope` permite aos experimentos substituir essa etapa por uma projeção controlada e reproduzível.

Logo, `audit_tme` não garante sozinho “sem API”: isso também depende da configuração/override da extração. `primary_audit`, em `tme/obligation_experiment.py`, força o suplemento `deterministic_only` e fornece uma entrada reutilizável para baseline local. O flag `use_lean` continua independente.

## 4. Rotas semânticas existentes e SemanticRubricEvaluator

Há uma evolução de experimentos paralelos, não uma sequência obrigatória de todas as versões:

| Rota | Entrada e comportamento |
|---|---|
| Suplemento original | `semantic.py`: LLM interpreta claims; verificadores locais decidem fatos; erros do provider deixam os registros determinísticos |
| Por obrigação | `obligation_experiment.run_shadow`: auditoria primária, obrigações não resolvidas, candidatos com spans, projeção, mesmos checkers/ponte |
| Por Evidence IDs | `evidence_id_experiment.run_shadow`: seleção de unidades reais, projeção validada, auditoria e controle de preservação dos suportes primários |
| Híbrida | `hybrid_grader.run_hybrid_shadow`: julgamento global, auditoria seletiva das expressões, reconciliação, PautaEngine com policy opt-in |
| Híbrida com sufficiency | `sufficiency_experiment.run_sufficiency_shadow`: segundo julgamento independente de suficiência, vínculo/contexto, reconciliação e pauta |

O avaliador funcionalmente chamado SemanticRubricEvaluator é `hybrid_semantic.request_judgments`. O payload contém enunciado completo, `official_reference`, catálogo de obrigações, árvore de métodos sem pontos, solução completa e unidades `E###`. A referência vem de `tme/references/hybrid_official.json`; **solução oficial não é gold score**, mas é informação adicional ausente da entrada desejada para o extractor C1.

O retorno é `SemanticObligationJudgment`: obrigação, `satisfied/not_satisfied/uncertain/contradicted`, IDs, método, assertion mode, confiança, rationale e extrações matemáticas opcionais. O schema é fechado; a validação exige exatamente as obrigações declaradas, sem duplicatas, e IDs de fonte existentes. Não aceita pontos nem nota. Entretanto, decide satisfação matemática, o que impede seu uso direto como o novo extractor C1 sem separar responsabilidades.

`selective_audit` encaminha somente representações compatíveis com `mathematical_obligations`; ignora representação `qualitative`. `EvidenceProjectionSession` reaproveita os checkers, sem transformar um julgamento positivo do LLM em `FactResult`. O runner de ablação faz primeiro as duas chamadas semânticas e depois as auditorias; não é chamado automaticamente pelo fluxo HTTP de P1.

## 5. Evidence IDs, unidades e contratos reutilizáveis

`SemanticEvidenceUnit` contém `evidence_id`, `exact_text`, `source_start`, `source_end`, `unit_kind`, `context_ids`. A função `evidence_units` preserva linhas físicas completas, separa alguns marcadores de item e numera `E001`, `E002`, etc. Os offsets são de caracteres Python Unicode, com intervalo `[start,end)`. `exact_text` é obtido por slice da fonte, sem cálculo de offset pelo LLM.

Esses IDs são estáveis para a mesma fonte e implementação, **não globalmente únicos entre soluções**; inserir uma linha pode renumerar as unidades. A identidade auditável precisa incluir caso/documento e hash da fonte. Uma unidade pode conter vários claims e uma obrigação pode precisar de várias unidades; o C1 não deve presumir bijeção `evidence_id ↔ claim`.

`EvidenceProjectionSession` mantém os IDs selecionados e seus bindings. Para unidades não contíguas, constrói o envelope literal entre o primeiro e o último span, conservando o texto intermediário como contexto. O payload matemático precisa estar nos trechos selecionados; o envelope não autoriza inventar passos. Envelopes acima de 2.048 caracteres não são projetados. `ProjectionSession` traduz coordenadas para o documento digital e recusa mapeamento ambíguo ou evidência fora do item.

Contratos já disponíveis:

- `SourceBinding`: texto literal, offsets, hash, grounding e atribuição; coerência estrutural não substitui revalidar o slice contra a fonte.
- `MathClaimRecord`: proveniência, tipo, forma canônica, papel semântico, payload legado, resultados de verificação e vínculos à rubrica.
- `StudentClaim`/`StudentClaimCheck`: entrada e resultado do checker, com arquivos Lean, prova da negação, grounding e estado formal.
- `FactResult`: resultado vinculado a IDs e fingerprints de registros, mecanismo e `VerificationLink`; não é outra representação de claim.
- `ObligationEvidence`/`PautaEvidence`: estados por obrigação, origem, atribuição, referências, metadata; rejeitam obrigações duplicadas.

O futuro `TMEEvidenceUnit` deve acrescentar contexto e roteamento sem substituir esses contratos. Faltam campos explícitos para `normalized_claim`, `polarity`, `scope`, flags de hipótese/abandono, candidatos de rubrica/obrigação, modelo e metadata de extração. Os enums existentes usam `rejected` e `uncertain`, enquanto C1 pede `abandoned` e `unclear`; será necessário um mapeamento explícito, sem equiparar conclusão assumida a tentativa ou hipótese.

## 6. SemanticSufficiencyGate e contexto

`SemanticSufficiencyGate.prepare` considera os julgamentos `satisfied`, aplica `link_evidence` e `context_gate` e rejeita localmente cabeçalhos vazios, vínculo inválido e contextos não afirmados. O provider recebe apenas obrigações elegíveis, requisitos de evidência, slices autorizados, enunciado e contexto/revisões para veto. Não recebe solução oficial, confiança, rationale nem julgamento do primeiro avaliador.

Estados: `sufficient`, `insufficient`, `contradictory`, `uncertain`. A resposta não pode introduzir obrigação/ID; para `sufficient`, deve preservar o conjunto inteiro de IDs selecionados. Falha de API ou contrato não é refutação: a composição registra `provider_error`/erro técnico.

`sufficiency_requirements.py` classifica as 21 obrigações P1 em `FINAL_ANSWER`, `FACT`, `INTERMEDIATE_STEP`, `JUSTIFICATION`, `ENUMERATION`. A exceção declarada entre itens de P1 é `c.uses_expression ← b`. Referências textuais explícitas podem autorizar vínculos adicionais; isso fica registrado em `exceptions`.

O commit-base corrigiu `sufficiency_context.item_regions`: “obtidos em (b)” dentro de uma frase não inicia nova seção. **A versão antiga de `hybrid_semantic.item_regions` permanece no código**, reconhecendo marcadores inline indiscriminadamente para hints/contexto da rota híbrida antiga. `reconcile_sufficiency` chama o reconciliador base sem julgamentos semânticos justamente para que esse parser antigo não promova evidência nessa etapa. Reutilizar o gate atualizado é diferente de chamar diretamente `run_hybrid_shadow`.

Há ainda diferença entre cabeçalhos `[a]` do documento digital e os marcadores `(a)`/`a)` reconhecidos pelo parser de sufficiency. C1 deve conservar texto original, mapeamento de itens e coordenadas, em vez de assumir que todos esses parsers têm o mesmo contrato.

## 7. EvidenceReconciler, policy e fronteira de crédito

`EvidenceReconciler.reconcile` dá precedência a suporte/refutação auditados e atribuídos ao aluno: primeiro baseline, depois auditoria seletiva. Pode registrar conflito entre auditorias ou entre auditoria e julgamento semântico. Erro técnico permanece erro técnico. Na rota híbrida antiga, um julgamento `satisfied` com contexto aprovado e sem auditoria conclusiva pode virar `SEMANTIC_SUPPORTED` sem gate independente.

`reconcile_sufficiency` reutiliza a precedência matemática do reconciliador e só promove evidência semântica quando vínculo, contexto e sufficiency passam. Registra separadamente a decisão do gate. Não promove automaticamente carry-forward. Para fronteiras desconhecidas, reduz a confiança a `medium`.

`HybridEvidencePolicy.accepts` permite `origin=semantic` sob contrato explícito: suporte, atribuição, grounding, refs, versão da reconciliação, tier `SEMANTIC_SUPPORTED`, contexto válido e ausência de conflito. Confiança `high/medium/low` é aceita; confiança não alta implica revisão. A policy **não executa nem exige por si só o gate de sufficiency**: confia na evidência upstream.

O ponto crítico para C1 é que conflitos formais/determinísticos podem manter `status=supported` com `metadata.conflict=true`. Como essas origens já são aceitas na pauta, `PautaEngine.observe` não passa por `policy.accepts` para vetá-las; a policy pode apenas marcar revisão. Portanto, o AwardGate C1 deve decidir quais conflitos impedem crédito antes de fornecer a visão de evidências à pauta, preservando os resultados e o conflito no relatório.

## 8. PautaEngine e score

`PautaEngine` é puro: recebe configuração e evidências, não interpreta texto nem chama LLM/Lean. Valida IDs, problema, origem e atribuição. Suporta `all_of`, `any_of`, `additive`, `banded`, `max_of`, `carry_forward`. Usa `Decimal`, caps e hashes de configuração/evidência; transporta refs e metadata nas decisões.

Na pauta P1, `unresolved_policy=withhold` faz evidência ausente/indeterminada resultar em zero concedido, preservando `known_points`, `possible_points` e revisão. Porém, `engine.py`, método `decision`, mantém `points_awarded=None` quando há incerteza técnica relevante; `evaluate` então pode produzir `score=None`. Há testes que exigem esse comportamento atual.

Para o C1, não basta retornar diretamente `assessment.score` no caminho principal ou fallback. Uma adaptação exclusivamente experimental deve produzir o número conservador exigido, por exemplo a partir dos pontos efetivamente autorizados/`known_points`, conservando assessment original, erro, revisão e motivo da normalização. Não se deve alterar globalmente a semântica de erro técnico da pauta nem chamar erro de refutação.

As faixas já evitam somar alternativas do mesmo item e `PautaEvidence` rejeita obrigação duplicada. Isso não é uma política global de deduplicação por evidence ID: uma mesma conta pode legitimamente satisfazer identificação, montagem e resultado. C1 deve impedir crédito repetido para a mesma regra/obrigação, sem proibir reutilização matemática legítima em requisitos distintos.

## 9. P1: obrigações, verificadores e rotas reais

Pauta interna `TME2_P1_PILOT`, alias público `TME2026P1`, máximo **20**. A tabela descreve a cobertura atual, não uma implementação C1 já feita. Todas as 21 obrigações têm rota determinística no vocabulário digital suportado; duas também têm rota Lean específica. A via semântica pode tratar prosa/argumentos fora da representação suportada nos experimentos, sem receber rótulo formal.

| Obrigação | Verificação existente e limite |
|---|---|
| `a.identifies_137` | Literal 137 ou operando correto da subtração; determinística |
| `a.constructs_subtraction` | AST exige subtração escrita `731-137`, na ordem correta |
| `a.result_594` | Literal/valor constante por comparação exata; **Lean** quando há igualdade inteira escrita `731-137=...` |
| `a.arithmetic_error_only` | Diagnóstico local: operação binária única, operandos corretos, resultado literal incorreto, um claim e nenhum conteúdo adicional não analisado |
| `b.reversed_number` | Equivalência afim com `100c+10b+a`; definição nova sem contradição |
| `b.subtraction` | Estrutura escrita da diferença entre as expansões posicionais |
| `b.middle_cancellation` | Igualdade válida partindo dessa subtração, com eliminação de `b` no lado direito |
| `b.factorization` | Expansão escrita para produto com fator 99; rejeita tautologias e produto trivial por 1 |
| `c.uses_expression` | Representação escrita equivalente a `99(a-c)` |
| `c.difference_domain` | Condições `1<=c`, `a<=9`, `a>c` e coleção explícita de `a-c` igual a 1…8 |
| `c.complete_list` | Nenhum valor esperado ausente em `{99*k: k=1,…,8}` |
| `c.no_extraneous_values` | Nenhum valor fora do conjunto esperado |
| `c.single_list_error` | Exatamente uma omissão ou um extra |
| `c.several_correct` | Pelo menos dois valores distintos corretos |
| `c.pattern_recognized` | Fórmula e lista vinculadas, com valores corretos |
| `c.some_correct` | Pelo menos um valor correto; duplicatas não multiplicam cobertura |
| `d.equation` | Igualdade escrita `99(a-c)=594`, comparada sob o contexto do problema |
| `d.difference_six` | Diferença escrita `a-c=6`, com comparação do resultado constante |
| `d.digit_pairs` | Enumeração finita exata de `(a,c)={(7,1),(8,2),(9,3)}` |
| `d.middle_choices` | Coleção explícita `b∈{0,…,9}` |
| `d.total_thirty` | Exige pares e escolhas anteriores e multiplicação escrita de 3 por 10; **Lean** na igualdade inteira, ou comparação determinística se desabilitado |

Pontuação aplicada pela pauta, nunca pelos checkers:

- **a, 3 pontos:** maior faixa satisfeita entre solução completa (3), diagnóstico de erro aritmético único (2), identificação (1).
- **b, 5 pontos:** invertido (2), subtração e cancelamento juntos (2), fatoração (1).
- **c, 6 pontos:** expressão (1), domínio (1), uma faixa de lista: completa sem extras (4), um erro (3), vários corretos com padrão (2), algum correto (1).
- **d, 6 pontos:** equação e diferença juntas (2), pares (2), escolhas e total juntos (2).

O mapa de fatos para obrigações fica em `bridge.py:TME2_P1_OBLIGATIONS`. Três nomes diferem: `a.inverted_number_137 → a.identifies_137`, `a.subtraction_731_137 → a.constructs_subtraction`, `a.single_arithmetic_error → a.arithmetic_error_only`. Os demais são identidades. A ponte exige correspondência exata com a pauta e não aceita fatos desconhecidos.

## 10. Integração Lean e distinção dos estados

`_Checks.arithmetic`, no checker P1, aceita somente igualdades com lados inteiros e sintaxe restrita (`+`, `-`, `*`, sinais e constantes). Gera `StudentClaim(claim_type="arithmetic_equality")`, payload `left_expr/right_expr`, grounding e projeção comum, e chama `check_one_student_claim` diretamente. Não passa pelo dispatcher ITA. A tática padrão é `norm_num`; a execução é `lake env lean`, com Mathlib, diretório exclusivo por chamada e prova vinculada ao span original.

`evaluate_student_proof` distingue:

| Resultado existente | Significado para o futuro C1 |
|---|---|
| `verified` com compilação válida | `FORMAL_VERIFIED` |
| `refuted` com prova compilada da negação | `FORMAL_REFUTED` |
| `unverified` ou resultado legado inconclusivo | `FORMAL_UNPROVED` quando houve rota formal; não refutação |
| `technical_error` | `FORMAL_ERROR` quando o erro pertence à rota formal |
| Verificação local positiva/negativa | `DETERMINISTIC_VERIFIED` / `DETERMINISTIC_FAILED`, preservando a razão |
| Apoio semântico suficiente | `SEMANTIC_SUPPORTED`, nunca formal |
| Falta de suficiência, contexto rejeitado, conflito | Estados C1 próprios; hoje aparecem distribuídos em status, tier, reasons e metadata |

Falha de tática não prova falsidade. Ausência de módulo, timeout e erro de processo são técnicos. A ponte exige vínculo exato entre resultado Lean, payload, origem, span, hashes e arquivos de prova/refutação. `reference_lean`, `secondary` e `semantic` não entram como prova do aluno pela ponte P1.

Não há prova Lean atual de toda a solução, domínio dos dígitos, completude dos pares ou justificativa verbal. Em `d.total_thirty`, Lean verifica a igualdade aritmética; os pré-requisitos de contagem são verificados deterministicamente e preservados em metadata. Estender essa cobertura seria trabalho adicional, não simples ativação de um checker já existente.

## 11. Testes e regressões encontrados; validação desta inspeção

| Arquivo | Cobertura relevante |
|---|---|
| `tests/test_tme2_p1_pauta_bridge.py` | 74 testes: 20 casos digitais, cobertura das 21 obrigações, 20/20 composto, contexto, fonte/routing adulterados, conflitos, tautologias, coleções, contrato de resultados formais |
| `tests/test_pauta_engine.py` | Faixas e pesos P1, caps, origens, duplicatas, carry-forward, estados de incerteza/erro |
| `tests/test_student_proof_semantics.py` | Falha de compilação não é refutação, timeout, prova da negação, compatibilidade dos checkers |
| `tests/test_semantic_claims.py` | Schema sem pontos, grounding, contexto, representação, revalidação semântica antes do checker P1 |
| `tests/test_obligation_semantic.py` | Obrigações fechadas, ausência, projeção, deduplicação, isolamento shadow |
| `tests/test_evidence_id_semantic.py` | IDs/spans exatos, contexto, envelope, schema, projeção, preservação da auditoria primária |
| `tests/test_tme_hybrid_grader.py` | Julgamento sem pontos, precedência, origem semântica distinta, conflitos, falha de provider |
| `tests/test_semantic_sufficiency.py` | Contrato independente, vínculo de item, contexto de veto, estados do gate, falha técnica |
| `tests/test_scope_boundary.py` | Correção do commit-base para referências internas e cabeçalhos reais |
| `tests/test_scope_boundary_replay.py` | Replay de respostas DEV congeladas; inclui P1_12 e preservação da falha de contrato |
| `tests/test_sufficiency_dev_regressions.py` | Regressões DEV anotadas; dependem de artefatos congelados para assertions de resultados |
| `tests/test_tme_accepted_integration.py` | Alias público P1, revisão aceita, ponte/engine, persistência e API |

Foram executados os sete arquivos `test_tme2_p1_pauta_bridge`, `test_pauta_engine`, `test_student_proof_semantics`, `test_semantic_sufficiency`, `test_scope_boundary`, `test_evidence_id_semantic`, `test_tme_hybrid_grader`.

**Resultado observado: 424 passed, 1 failed, 1 skipped, 4 deselected, em 7,85 s.** Os 74 testes da ponte P1 passaram. O teste ignorado requer o artefato DEV congelado de P5_02, ausente neste worktree. Foram deselecionados dois casos de `written_method_reaches_real_lean`, `wrong_reasoning_correct_final_is_refuted_by_real_lean` e `real_formal_verified_is_preserved_and_not_semantic`.

A seleção ainda incluiu `test_student_proof_semantics.py::test_real_arithmetic_negation_and_verified_claim`; ele tentou executar Lean real e falhou porque obteve `technical_error` em vez de `refuted`. O worktree não dispõe de `.lake/packages/mathlib`; o toolchain `leanprover/lean4:v4.28.0` está instalado. A ausência das dependências é uma limitação observada do ambiente; o log pytest não identifica com precisão o diagnóstico interno completo do subprocesso. Portanto **a integração Lean real não foi certificada nesta inspeção**. Não se atribui essa falha a regressão de código nem se contabilizam mocks como provas reais.

O Python padrão não tem pytest. Foi usado o ambiente preexistente de `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`, com `PYTHONPATH` apontando explicitamente para `app` deste worktree; o caminho importado foi verificado. Não foram instalados pacotes ou alterados ambientes. Credencial OpenAI removida do processo, suplemento semântico desabilitado, bytecode/cache pytest desabilitados e conexões socket Python bloqueadas. Esse bloqueio não se estende a subprocessos Lake/Git; o teste Lean tentou inicializar sua infraestrutura local. Não houve chamada de inferência LLM.

Log: `/private/tmp/confia-c1-archaeology-20261104/baseline-tests.log`.
Coleta confirmando 74 testes P1: `/private/tmp/confia-c1-archaeology-20261104/p1-collection.log`.

Para reproduzir a seleção funcional sem o teste Lean que falhou por ambiente:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0 \
  /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_tme2_p1_pauta_bridge.py tests/test_pauta_engine.py \
  tests/test_student_proof_semantics.py tests/test_semantic_sufficiency.py \
  tests/test_scope_boundary.py tests/test_evidence_id_semantic.py tests/test_tme_hybrid_grader.py \
  -k 'not written_method_reaches_real_lean and not wrong_reasoning_correct_final_is_refuted_by_real_lean and not real_formal_verified_is_preserved_and_not_semantic and not real_arithmetic_negation_and_verified_claim'
```

Esse é um comando de regressão, não um piloto C1, e não foi reexecutado para substituir o resultado inicial. Os testes usam expectativas fixas de regressão em assertions; nenhum runner C1 ou avaliação com gold foi executado. O conjunto `tme_holdout_eval_01` não foi aberto, usado para tuning ou reexecutado.

## 12. Consequências para a implementação paralela

Estas são recomendações derivadas da inspeção, ainda não implementadas:

1. Manter o alias/IDs P1 e a pauta atual; expor C1 por entrada separada e restrita a P1. Definir no runner qual composição significa `tme_current`: produção com suplemento configurável e experimento híbrido com sufficiency não são sinônimos. Para fallback previsível sem nova dependência da API, a composição `primary_audit` já permite reutilizar o TME local com suplemento desabilitado e `use_lean` registrado.
2. Criar o contrato C1 como envelope de evidência/contexto com ligação explícita aos `MathClaimRecord` existentes. Reutilizar IDs e spans calculados localmente; distinguir IDs de unidade, claim, fato e obrigação. Manter correspondência entre texto original e documento digital.
3. Fazer o extractor retornar interpretação/payload/contexto, com IDs de obrigação fechados e sem pontos ou decisões de verdade. Reutilizar transporte/schema onde compatível, sem enviar o payload completo do avaliador global como se fosse o contrato C1.
4. Usar o mapa P1 e as representações `expression`, `collection` e `unmapped/qualitative` como base para a lista fechada. `StudentClaimType` é um contrato compartilhado ITA/genérico, não uma lista pronta de tipos específicos P1; `MathClaimRecord` também admite tipos nativos como `math_literal` e `math_finite_collection`.
5. Roteamento inicial: Lean nas igualdades suportadas de `a.result_594` e `d.total_thirty`; verificadores locais nas demais representações suportadas; gate semântico nos argumentos fora dessa linguagem. Uma prova formal não dispensa contexto, vínculo e suficiência da obrigação. Falha/inconclusão formal não autoriza promoção silenciosa pelo LLM.
6. Reutilizar a precedência e traces do reconciliador, acrescentando o AwardGate C1 para contexto explícito, conflito impeditivo, suficiência e deduplicação. Não presumir que `HybridEvidencePolicy` implemente sozinho essas exigências.
7. Manter intacto o PautaEngine. Gerar score numérico no envelope C1/fallback com política explícita de zero para evidência insuficiente, preservando os estados originais. Registrar `requested_mode`, `effective_mode`, `fallback_used` e motivo; falhas atuais não produzem automaticamente esse contrato.
8. Registrar créditos pela árvore de regras selecionadas. Pontos pertencem a regras/faixas: um bloco `all_of` de 2 pontos não equivale a 2 pontos por obrigação. A decomposição em formal/semântico pode ser mista e não deve duplicar o valor do bloco.
9. Preparar uma entrada DEV P1 contendo apenas IDs, problema e texto. A fixture digital atual também contém expectativas de pontos; o runner histórico as lê e compara. Não reutilizar esse runner diretamente como executor C1 sem gold. Uma preparação separada pode remover expectativas antes de qualquer execução experimental.
10. Atenção ao isolamento por arquivos novos: `accepted_audit.audit_context` calcula versão com `rglob('*.py')` em várias pastas, inclusive `tme`, `student_claims`, `lean`, `claims` e `rubric/pauta`. Adicionar módulos C1 ali mudaria a identidade da auditoria atual mesmo sem editar seus arquivos. Para preservar também essa identidade, preferir um pacote irmão experimental fora dessas árvores, sem import automático pelo caminho atual.

## 13. Estado da entrega

- Arquivo criado no repositório: somente este diagnóstico, `docs/audits/TME_SEMANTIC_FORMAL_C1_DIAGNOSTICO_01.md`.
- Arquivos preexistentes modificados: nenhum. Snapshot de hashes dos 732 arquivos versionados em `/private/tmp/confia-c1-archaeology-20261104/tracked-before.json`; verificação final registrada em `integrity-after.json` na mesma pasta.
- Logs e arquivos temporários de teste ficaram em `/private/tmp/confia-c1-archaeology-20261104/`; o teste Lean também criou diretório ignorado `.lake/` neste worktree. Nenhuma dependência foi preparada manualmente, nenhum arquivo de pipeline foi substituído.
- Pipeline atual preservado; sem staging, commit ou push. SHA do código continua `1b3daea41ba4ce31c0cfd35dd07907da3d03669f`.
- Nenhum piloto executado; nenhum runner C1 criado. Ainda não existe comando executável de piloto C1 a fornecer. O comando exato e os 15 testes novos pedidos pertencem à etapa posterior de implementação.
- Nenhuma expansão de implementação para P2–P5. Testes compartilhados já existentes desses problemas apareceram na seleção de regressão dos componentes comuns.

O fluxo real de P1 está identificado. A implementação paralela pode ser delimitada pelos contratos acima, preservando a diferença entre interpretação, verificação matemática, suficiência e concessão de pontos.
