# TME P3 — Conflict Preservation Fix 01

Data: 2026-11-05, America/Fortaleza. Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3`. Branch: `experiment/tme-semantic-formal-p3`.

**SHA inicial desta tarefa: `fdc97ebe7dec91509acda7ca3f99c02b5a912fb7`**, worktree inicialmente limpo. A implementação que produziu DEV01 continua sendo `e4dc1e94b0e8e22a16489fcdcc3eb14e1abfd4ab`. Entre esse SHA e o HEAD inicial há somente a inclusão do relatório forense; não havia outra mudança de implementação a incorporar.

**READY_FOR_P3_DEV02.** A perda de evidência contraditória de `b.same_compartment` foi corrigida por um caminho separado, somente de guard/veto. No controle com o conteúdo e a resposta de extração já observados, o score é **2**, exclusivamente por `a.count`; os conflitos de repetição e probabilidade ficam observáveis. **DEV01 e DEV02 não foram executados nesta tarefa. Nenhuma chamada real ao SemanticExtractor foi feita.**

## 1. Causa raiz e caminho exato

O [relatório forense](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_SEMANTIC_FORMAL_DEV01_FORENSIC.md) identificou um falso crédito material de 2 pontos na regra `b.same`, cujo obligation_id é `b.same_compartment`.

A fonte trazia “somente o sexto” e “o quinto também”. O primeiro claim foi normalizado como `{6}` e verificado. O segundo foi extraído como subject `repeticao_branca`, claim_type `integer_set`, mas com normalized_claim em prosa. A cadeia anterior era:

1. [mapper.py:69](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py:69): `representation` não consegue transformar essa string no payload do checker positivo; retorna `unsupported_checker_payload`.
2. [verification.py:28](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py:28): somente mapeamentos accepted entram na projeção, logo o claim do quinto não chegava à máquina.
3. [verification.py:108](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py:108): a rejeição de formato era exibida como CONTEXT_REJECTED, sem mathematical_refutation.
4. `engine.reconcile` não encontrava negativo verificável em `b.same_compartment`; o positivo `{6}` chegava ao award. O guard digital antigo também não reconhecia essa prosa.

Não houve erro no cálculo da máquina. A falha estava em tratar ausência de representação adequada ao **award positivo** como ausência de efeito sobre **conflitos**. A correção aplica `unsupported-for-positive-award ≠ invisible-to-conflict-detection`, sem tornar um claim incompleto suficiente para ganhar pontos.

## 2. Alteração mínima

| Arquivo | Mudança |
| --- | --- |
| [conflict_guard.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py) | Novo adaptador local de pertencimento, consulta à enumeração congelada e recibo somente de guard |
| [engine.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py) | Único arquivo preexistente alterado: chama o guard, passa negativos à reconciliação e expõe seus resultados |
| [test_tme_p3_conflict_preservation.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_conflict_preservation.py) | Nova suíte focal, 43 testes |
| Este relatório | Documentação da correção e validação |

O diff de engine.py tem 9 linhas adicionadas e 4 removidas. `award`, PautaEngine, ScoreClosurePolicy, mapper, verification, extractor, registry e checkers matemáticos não foram editados. A chamada do novo guard ocorre apenas no ramo experimental semantic, após verificação e antes da reconciliação. O modo Current e o fallback não chamam esse guard e não recebem o campo novo de resultados.

## 3. Representação atômica e rastreabilidade

O adaptador não produz `{5}`, `{5,6}` ou qualquer conjunto supostamente escrito pelo aluno. Ele reconhece, na fonte literal, uma afirmação de inclusão no evento de repetição branca:

```text
source_span
→ membership_claim(compartment=5, relation=same_compartment_second_white)
→ finite_certificate da máquina congelada
→ consulta ao evento (5,5)
→ DETERMINISTIC_FAILED / mathematical_refutation=true
→ mesma família b.same_compartment
→ CONFLICTING_EVIDENCE
→ award bloqueado
```

O evento preserva EvidenceUnit, item, subject, source_span, offsets, hash da fonte, assertion_status, polarity, scope, hypothetical, abandoned e attributed_to_student. O índice é derivado do token escrito, não do normalized_claim do LLM. Para o controle observado:

```json
{
  "kind": "membership_claim",
  "compartment": 5,
  "relation": "same_compartment_second_white",
  "literal_token": "quinto",
  "literal_start": 138,
  "literal_end": 144
}
```

O payload numérico 5 é a normalização rastreável de “quinto”. O normalized_claim em prosa que causou a rejeição original permanece armazenado como proveniência; ele não determina o índice nem a falsidade. Um teste fornece normalized_claim reparado para o sexto enquanto a fonte diz quinto: o guard continua consultando o quinto.

O caminho positivo continua rejeitado exatamente como antes. `conflict_guard_results` é um canal separado. O CONTEXT_REJECTED anterior não foi apagado ou reinterpretado como prova de falsidade; o recibo novo explica a verificação independente que agora participa da reconciliação.

## 4. Autoridade matemática preservada

`membership_result` chama o `finite_certificate` já existente e consulta se `(i,i)` pertence a `same_white`. Não há novo cálculo de cores, tabela de respostas nem condição especial para 5, 6 ou o case_id DEV.

Na máquina congelada:

- O quinto tem cinza na primeira posição e preta na segunda. No evento (5,5), a segunda bola é preta; o pertencimento alegado é falso.
- A enumeração produz `same_white=[[6,6]]`. Esse conjunto é saída do modelo, não conjunto sintetizado como afirmação do aluno.
- Todos os seis índices foram testados: somente o evento (6,6) satisfaz a propriedade.
- Controle com máquina alterada apenas em memória, colocando branca na segunda posição do quinto, faz a mesma consulta ao índice 5 retornar VERIFIED e deriva os eventos (5,5) e (6,6). Isso comprova que a decisão depende do estado, não de um veto hardcoded ao número 5. O asset oficial não foi alterado.

O recibo guarda origem/hash da máquina, estados e cores do evento após as duas retiradas e os pares diagonais favoráveis derivados. Nenhuma prova Lean da máquina foi introduzida.

## 5. Por que não cria crédito

Cada evento novo registra:

```text
guard_only=true
award_eligible=false
sufficiency_decision.sufficient=false
sufficiency_decision.basis=guard_cannot_award
formal_status=FORMAL_NOT_ATTEMPTED
formal_attempted=false
```

Os eventos não entram na projeção positiva, não viram FactResult positivo, não são passados como candidatos ao `award` e não completam conjunto, justificativa ou dependência. A reconciliação recebe somente os membros refutados como razão adicional de bloqueio da **mesma família**. O `award` original continua usando a lista de obrigações bloqueadas.

Uma afirmação atômica verdadeira sobre o sexto retorna DETERMINISTIC_VERIFIED no guard e ainda assim não concede ponto algum. Uma falsa sobre o quinto também não concede crédito. Ambas as situações foram testadas isoladamente. A extensão só pode reter crédito existente; não possui rota para aumentar score. Outras famílias/obrigações não recebem veto novo por esse evento.

## 6. Contexto e ordem textual

O guard exige item b, subject repeticao_branca, candidato b.same_compartment, fonte/offset/hash íntegros, asserted, positive, atribuição ao aluno, ausência de hypothetical/abandoned e scope main_argument ou final_conclusion. Reutiliza `local_context` congelado. Só recupera rejeições de representação admissíveis; rejeições por item, sujeito, contexto ou interpretação conflitante não são promovidas a eventos matemáticos.

A gramática é limitada a membros escritos como ordinais ou `compartimento N`, com “também” e a propriedade de liberar/produzir/fornecer branca. Uma elipse como “o quinto também” precisa de referência explícita à repetição branca em evidência da mesma família e contexto válido. Essa referência pode vir antes ou depois; fornece o objeto da afirmação, não um membro nem sua verdade. Um ordinal isolado sem relação ancorada não é suficiente.

| Controle contextual | Resultado |
| --- | --- |
| “somente o sexto” sem contradição | b.same mantém 2 |
| “talvez”, hipótese não adotada | Nenhum guard negativo; crédito válido independente preservado |
| “Beatriz disse que…” sem adoção | Nenhum veto |
| “pensei que fosse…” / tentativa descartada | Nenhum veto |
| Flags hypothetical, abandoned, quoted, polarity negativa, atribuição ausente | Nenhum veto |
| Scope exploration/side_calculation/unknown | Nenhum veto |
| Número 5 em outra obrigação/subject, outra propriedade ou outro item | Nenhum veto de b.same |
| Fonte adulterada ou número correto apenas no payload do LLM | Não se usa como fato da fonte |

Foram testadas as duas ordens:

1. “somente o sexto” seguido de “o quinto também”; b.same bloqueado.
2. “o quinto também” seguido de “Na verdade, … somente o sexto”; b.same bloqueado.

Não foi criada precedência de “última afirmação vence”. O contrato congelado não define essa expressão como revogação automática do outro span; ambos continuam asserted/adotados. A evidência independente de a permanece pontuada nas duas ordens.

Limite: este é um adaptador de conflito parcial da família de repetição, com gramática verificável. Não é um novo extractor geral de prosa nem uma garantia de detecção universal de toda contradição P3. Contextos ambíguos ou propriedades não reconhecidas não são arbitrariamente transformados em falsidade.

## 7. Controle do conteúdo observado de partial_conflict

Foram usados dois controles sem rede: o teste permanente com as cinco interpretações observadas e uma avaliação local com **o raw_output exato salvo no JSON DEV01**. O segundo chamou `evaluate` com um provider que devolve somente essa resposta já capturada; não instanciou OpenAI nem executou o runner DEV. O case_id de avaliação foi `controlled-recorded-p3-source`, diferente do ID DEV, para deixar explícito que a nota não é imposta por ID.

A fonte foi a original integral, byte a byte preservada. `use_lean=True` foi mantido no controle com raw_output, mas não há igualdade elegível nessa fonte e nenhum Lean foi necessário para a correção.

| Parcela / evento | Resultado controlado |
| --- | --- |
| a.count / a.bottom_white_count | DETERMINISTIC_VERIFIED; elegível; **2 pontos** |
| Afirmação do sexto | Verificação positiva anterior preservada |
| Afirmação atômica do quinto | DETERMINISTIC_FAILED pelo modelo; guard somente de veto |
| b.same / b.same_compartment | CONFLICTING_EVIDENCE, unresolved; award=false; **0** |
| b.conclusion / b.second_white_probability | Conflito anterior 11/36 versus 12/36 preservado; award=false; **0** |
| Score | **2.0**, emergente das obrigações e da pauta |
| fallback / technical_uncertainty | false / false |
| review_recommended | true |
| Chamadas reais à API | **0** |

Esses 2 pontos são exatamente os independentes confirmados pela perícia e pelo checker de brancas inferiores. Nenhuma outra parcela foi criada ou zerada por regra especial de caso. O resultado original DEV01 continua 4 no seu artefato, intacto; o controle pós-fix foi salvo em outra pasta de auditoria.

## 8. Testes e regressões

| Seleção | Resultado final |
| --- | --- |
| Nova suíte test_tme_p3_conflict_preservation.py | **43 PASS** |
| test_tme_semantic_formal_p3.py | 132 PASS |
| test_tme2_p3_pauta_bridge.py | 70 PASS |
| test_pauta_engine.py | 100 PASS |
| test_tme_p3_checker_first.py | 90 PASS |
| test_tme_semantic_formal_p3_lean.py + test_tme_p3_checker_first_lean.py | **21 PASS** |
| Seleção relacionada P3 em semantic_claims, tme_hybrid_grader, scope_boundary | **6 PASS**, 132 deselected |
| Total distinto | **462 PASS = 419 regressões + 43 novos** |

A suíte focal cobre os doze requisitos solicitados, todos os seis índices, variação do estado da máquina em memória, origem literal do membro, ordem inversa, efeitos de contexto, impossibilidade de award pelo guard e preservação dos créditos independentes. O primeiro teste focal teve um erro no helper ao passar subject duas vezes; o helper do teste novo foi corrigido e a seleção final passou. Não houve alteração de testes/expectativas históricos.

TME_CURRENT: teste focal compara os dumps completos da bridge e assessment antes/depois da chamada experimental; o modo Current continua igual ao primary_audit. As 25 fixtures históricas já cobertas pelas regressões mantêm notas e verificações. Não se afirma identidade do JSON inteiro entre versões, porque hashes da implementação experimental mudam legitimamente; os produtores, contratos, evidência e pontuação do baseline foram preservados.

## 9. Lean real

Os arquivos dos checkers Lean, táticas e contratos não foram modificados. Foram executadas as 21 integrações existentes, com os providers controlados já previstos nos testes; nenhum SemanticExtractor real foi chamado.

A suíte preserva os cinco IDs com aritmética Lean, prova/refutação, igualdade verdadeira com estrutura falsa, conflitos, ausência de dupla pontuação e fechamento numérico. Controles deliberados com `skip` e identificador inexistente exercitam FORMAL_UNPROVED e FORMAL_ERROR usando o compilador real; não são falhas residuais do fix. O controle de exceção anterior ao compilador continua FORMAL_NOT_ATTEMPTED, sem confundir isso com ausência de prova após execução.

Ambiente: Lean **4.28.0**; Mathlib **`8f9d9cff6bd728b17a24e163c9402775d9e6a365`**. A nova consulta de pertencimento permanece determinística; nenhuma contradição foi movida artificialmente para Lean.

## 10. Preservação e fallback

Comparação de hashes de 832 caminhos preexistentes monitorados: **somente engine.py mudou; os outros 831 permaneceram idênticos**. A lista inclui os arquivos rastreados relevantes e os JSON do DEV01; caminhos gold/holdout foram excluídos e não lidos.

Preservados integralmente: pauta/pesos, PautaEngine, ScoreClosurePolicy, máquina, checker-first P3, checkers Lean, mapper/verification/extractor/registry anteriores, prompt, timeout=180, max_retries=0, model=gpt-6.1-sol, effort=medium, store=False, política de fallback, P1/P2, datasets/testes históricos e artefatos do DEV01.

```text
dev_sources.json SHA-256: d12a77cd87f0e5197db7e3cdafaedf78a130dd7dc3b1b59fa5d029a702e375cc
dev_ids.json SHA-256:     a7ab3a65f60e1284b119c8974a47e3eea0c037f58c96963bff8c7372ebcaab0a
```

O InternalServerError de p3_dev_isolated_answer permanece apenas documentado no DEV01; não foi corrigido, reexecutado ou usado para mudar retries/fallback. Não houve execução de DEV02 ou tuning dos textos.

## 11. Comandos de validação

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app:$PWD" CONFIA_TME_SEMANTIC_ENABLED=0
P3_PYTHON=/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python

"$P3_PYTHON" -m pytest tests/test_tme_p3_conflict_preservation.py -q -p no:cacheprovider \
  --basetemp=/private/tmp/p3-conflict-fix-01/focal-final \
  --junitxml=/private/tmp/p3-conflict-fix-01/focal-final.xml
"$P3_PYTHON" -m pytest tests/test_tme_semantic_formal_p3.py tests/test_tme2_p3_pauta_bridge.py \
  tests/test_pauta_engine.py tests/test_tme_p3_checker_first.py -q -p no:cacheprovider \
  --basetemp=/private/tmp/p3-conflict-fix-01/regression \
  --junitxml=/private/tmp/p3-conflict-fix-01/regression.xml
"$P3_PYTHON" -m pytest tests/test_tme_semantic_formal_p3_lean.py tests/test_tme_p3_checker_first_lean.py \
  -q -s -p no:cacheprovider --basetemp=/private/tmp/p3-conflict-fix-01/formal \
  --junitxml=/private/tmp/p3-conflict-fix-01/formal.xml
"$P3_PYTHON" -m pytest tests/test_semantic_claims.py tests/test_tme_hybrid_grader.py \
  tests/test_scope_boundary.py -k TME2026P3 -q -p no:cacheprovider \
  --basetemp=/private/tmp/p3-conflict-fix-01/related \
  --junitxml=/private/tmp/p3-conflict-fix-01/related.xml
git diff --check
git status --short
git rev-parse HEAD
```

Logs/JUnit, comandos integrais, snapshots de preservação e resultado do provider gravado: [artefatos do fix](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_conflict_preservation_fix_01). Os arquivos Lean executados ficam nos caminhos registrados pelos recibos. Esses artefatos são locais/ignorados; os artefatos DEV01 não foram sobrescritos.

## 12. Git e veredito

SHA inicial e final, sem commit: **`fdc97ebe7dec91509acda7ca3f99c02b5a912fb7`**.

```text
 M app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py
?? app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py
?? docs/audits/TME_P3_CONFLICT_PRESERVATION_FIX_01.md
?? tests/test_tme_p3_conflict_preservation.py
```

O falso crédito de b.same desapareceu no controle observado, por verificação independente e reconciliação, mantendo a.count. A correção fica restrita ao guard dessa família e conserva os contratos positivos. O próximo passo pode ser o DEV02, que **não foi executado nesta entrega**. Sem stage ou commit automático.

**READY_FOR_P3_DEV02**
