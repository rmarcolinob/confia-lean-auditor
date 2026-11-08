# TME P3 — Multi-layer Semantic Safety Implementação 01

## 1. Base, escopo e resultado

SHA inicial: `f9e23b954756ea292429885abc5073125dcc8ada`; worktree inicialmente limpo. Especificação: [arquitetura aprovada](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_MULTI_LAYER_SEMANTIC_SAFETY_ARCHITECTURE_01.md). Motivação: [forense Safety03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_SEMANTIC_SAFETY_03_FORENSIC.md). A implementação não foi commitada; os hashes dos arquivos efetivamente executados estão no manifest do replay. O SHA inicial sozinho não identifica o código modificado desta tarefa.

Foi implementada a fronteira comum de admissão e autoridade no módulo experimental P3. O score permanece numérico. A matemática e a pauta permanecem congeladas. Resultados desta tarefa são regressões observadas e testes controlados; não alteram retrospectivamente `P3_SAFETY_FAILURE` nem constituem avaliação independente.

**1178 testes PASS; zero FAIL/ERROR/SKIP.** Replay de 184 registros históricos, com Lean real, zero chamadas à API e zero technical uncertainty. A05 ficou em 0; os cinco falsos vetos prioritários foram eliminados, recuperando seus 9 pontos. A contagem independente de E01 recuperou mais 2 pontos. Nenhum suporte legítimo anteriormente premiado foi perdido na comparação por obrigação com os contratos observados.

## 2. Módulos novos e modificados

| Arquivo | Alteração |
| --- | --- |
| [segmentation.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/segmentation.py), novo | DiscourseSegment/ClaimEpisode, limites de sentença que preservam decimais, offsets de envelope/cláusula/assertiva, ordem, vizinhança, bloco, item, propriedade e atos discursivos |
| [semantic_contracts.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/semantic_contracts.py), novo | RepresentationReceipt, BindingReceipt e identidade das premissas submetidas ao checker |
| [automation.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/automation.py), novo | AutomationEligibilityPolicy; admissão, AUTO_AWARD/AUTO_VETO/REVIEW_ONLY e provenance |
| [source_adapter.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/source_adapter.py) | Segmentação numérica, membership literal, conjunto fechado, vínculo de quantidade e conservação de payload original |
| [discourse.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/discourse.py) | Ordem por assertiva, relações de revisão, adoção/atribuição, contratos e segmentos no snapshot imutável |
| [mapper.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py) | Admissão por fidelity/binding; isolamento de campos tipados; quantidade após predicado; inclusão não é conjunto exaustivo |
| [verification.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py) | Revalidação da representação antes da projeção; referências/digests das proposições no trace, sem mudança de matemática |
| [conflict_guard.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py) | Adapter de átomos certificados para a consulta finita existente; token literal e offsets preservados |
| [veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/veto_policy.py) | Exige admissão semântica e identidade do input; autoriza veto central e autentica sua decisão de automação |
| [unified.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/unified.py), [engine.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py) | Integração das camadas, traces, bundles de suporte e awards filtrados pela fronteira |
| [test_tme_p3_multilayer.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_multilayer.py), novo | Matriz de admissão, invariantes F, regressões causais gravadas, igualdade B02 em Lean real e tentativas de alteração de receipts |
| [test_tme_p3_veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py) | O stub de checker passou a emitir o receipt de input exigido; expectativas/asserts anteriores preservados |
| [replay_tme_p3_multilayer.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/scripts/evaluation/replay_tme_p3_multilayer.py), novo | Replay local com providers gravados, cliente API bloqueado, Lean real, saída nova e hashes antes/depois |

## 3. Fluxo final

```text
source + EvidenceUnits originais/nativos
 → clause_view + DiscourseSegment/ClaimEpisode
 → propriedades/átomos e relações discursivas vinculadas à fonte
 → RepresentationReceipt + DiscourseReceipt + BindingReceipt no snapshot
 → mapper/admissão semântica
 → projeção revalidada → checkers existentes
 → checker-input receipts → AutomationEligibilityPolicy
 → VetoEligibilityPolicy → reconciliação autenticada
 → AUTO_AWARD admissível / AUTO_VETO autorizado / REVIEW_ONLY
 → PautaEngine inalterado → score numérico
```

As fases de representação e discurso compartilham adapters de fonte, mas não usam resultado matemático ou score. O snapshot fecha antes de executar matemática. A política negativa usa a mesma admissão da positiva e permanece a única autoridade de hard veto. O fallback Semantic percorre esse caminho; TME_CURRENT continua legacy.

## 4. Segmentação temporal/discursiva

`DiscourseSegment` registra offsets half-open em codepoints Unicode, envelope, cláusula, assertiva, ordinal, anterior/posterior, parágrafo/bloco, item, propriedade, episódio, atos e mudança de tópico. Envelopes equivalentes não movem a assertiva. Decimais não são quebrados como frases; pontuação depois de inteiro/fração pode terminar a sentença.

`ClaimEpisode` agrega segmentos e relations receipts; speaker/scope de segmento são diagnósticos e não concedem autoridade. Estado e relações de adoção permanecem no receipt discursivo. Correções são dirigidas pela posição da assertiva e pelo marcador/alvo local; conteúdo matemático diferente sozinho não substitui claim.

A revisão pode começar dentro de um asserted_content amplo. Nesse caso, a posição do payload literal único permite examinar o marcador posterior, preservando o conteúdo original. Em caso de múltiplas ocorrências/ambiguidade não se escolhe a ocorrência que melhora a nota.

## 5. Representation fidelity

Implementados EXACT, SUPPORTED_NORMALIZATION, PARTIAL, AMBIGUOUS e UNSUPPORTED. Receipt contém proposição tipada, digest, conteúdo afirmado, spans, payload original/normalizado, cobertura, regra/razão e passos de normalização. A classificação vem da fonte antes do checker.

Números por extenso e notação suportada são normalizados sem obter valores da máquina. Igualdades não são truncadas; conjuntos não perdem membros nem são completados; membership não vira conjunto exaustivo. Campo tipado pode ser isolado pela sua própria assertiva para não transportar quantidade de outra oração. Quantidade posterior ao predicado é admitida somente com vínculo textual verificável.

Negação sem representação explícita preservadora de polaridade fica sem admissão matemática; não se prova a versão positiva como se fosse a frase escrita. RepresentationReceipt incompleto/ambíguo/não suportado não autoriza award nem veto. VERIFIED/REFUTED não alteram esse receipt.

## 6. Discourse state e relações

ACTIVE, SUPERSEDED, NON_ADOPTED e AMBIGUOUS foram preservados. ACTIVE não equivale a representável: uma assertiva própria reconhecida pode ficar ACTIVE/UNSUPPORTED. Motivos, spans e supersedes/superseded_by continuam explícitos; o ledger retém sinais originais do modelo.

O resolver reconhece relações locais de retificação/invalidação, retirada e substituição sem consultar o acerto matemático do substituto. A cadeia temporal não usa o início do envelope como ordem dos atos. Citação sem adesão recebe NON_ADOPTED. Flags do modelo, inclusive abandoned e confidence, não concedem nem removem autoridade sozinhas.

Foi corrigido também um defeito incidental em `literal_property`: um fallback referia variáveis indefinidas `r`/`item`. A leitura agora usa o valor efetivamente disponível; nenhum valor matemático foi alterado.

## 7. Binding claim ↔ obligation

BindingReceipt é independente do estado discursivo: claim_id, obligation_id, compatibilidade de item/subject/caso, semantic_relation, fidelity e receipt_ref, binding_status, diagnósticos e confiança apenas diagnóstica. A identidade do receipt exclui confidence.

A obrigação sugerida seleciona candidatos; só fonte validada e registry determinam vínculo autorizado. EXACT_BINDING/VALID_EQUIVALENT_BINDING são admissíveis; PARTIAL_BINDING/AMBIGUOUS_BINDING/INVALID_BINDING não. O ordinal do evento deve estar ligado a bola/retirada/sorteio, nunca ser obtido do numerador de uma fração. Referências misturadas a localizações ou casos não são transportadas para um subject por mera presença lexical. Um membership fiel pode ter binding válido para contraevidência, sem binding suficiente para satisfazer positivamente um conjunto completo.

Índices de membership vêm da assertiva específica; múltiplos índices não resolvidos ficam sem admissão, e o artigo indefinido “um compartimento” não vira índice 1. Elipse exige antecedente literal adjacente da mesma propriedade, com source receipt; `O quinto também` isolado não recebe subject apenas porque o modelo sugeriu repeticao_branca. A consulta finita não participa dessa decisão.

## 8. AutomationEligibilityPolicy

Admissão confere snapshot atual, fonte, adoção ACTIVE, fidelity suficiente e binding adequado de cada premissa. No positivo, ainda exige rota do registry, receipt matemático, fato positivo, status verificado, sufficiency, ausência de guard e de veto central aplicável. No negativo, ainda exige refutação/contradição independente e receipt autenticado da VetoEligibilityPolicy.

Cada decisão registra autoridades positiva/negativa/review separadas, reasons, revisão, fonte, checker input, checker status, sufficiency, contexto matemático, registry revision e referência à política negativa. Confidence não é limiar.

Não há passagem direta de candidato de veto para score: a política central autentica, a automação confirma AUTO_VETO e a reconciliação aplica somente esse receipt. Divergência entre flags do candidato e resultado original do checker é rejeitada.

## 9. Fronteira dos checkers

StrongP3Checks, finite-state machine, arithmetic/deterministic/composite checkers, Lean, Mathlib e proposições formais não foram alterados. A função matemática `membership_result` manteve sua AST original; mudou somente o adapter que lhe fornece inclusões certificadas.

`ClaimProjection` recalcula o certificado da representação antes da chamada matemática e rejeita mutação após admissão. O trace da projeção registra digest da proposição e referências de representação/segmento; resultados carregam receipt das premissas e snapshot. Um resultado matemático não valida adoção ou tradução.

FORMAL_UNPROVED/NOT_ATTEMPTED/ERROR e COMPOSITE_INCOMPLETE não viram refutação. COMPOSITE_FAILED só tem autoridade negativa com refutação explicitamente certificada, contexto e premissas admitidos. Uma igualdade Lean verdadeira não substitui componente combinatório ausente ou falso.

## 10. Veto e reconciliação

A VetoEligibilityPolicy preserva o grafo de dependências existente e autenticação de receipts. Nenhum produtor ganhou autoridade paralela. Atomic/structural/native/positive producers fornecem resultados; todos passam pela admissão e política central.

Reconciliação consome receipts anotados, sem reler o texto para decidir adoção ou propriedade. Atua somente sobre decisões autênticas AUTO_VETO. Awards finais passam pela automação e pelos controles anteriores de proveniência/rota/sufficiency. Deduplicação/idempotência e localidade continuam testadas.

## 11. REVIEW_ONLY e numeric closure

REVIEW_ONLY não gera witness, target de veto ou propagação negativa. Pode coexistir com AUTO_AWARD independente para a mesma obrigação. `ObligationSupportBundle` registra witnesses, reviews e vetos separadamente; não introduz “qualquer review ⇒ zero”. O score permanece float e fecha com a soma das parcelas da pauta.

Ausência de witness próprio, rejeição de representação e veto autorizado são motivos distintos no trace. Um claim não interpretável não refuta outro. Preservar essa regra significa admitir limitações de cobertura; não usar review como retirada disfarçada de ponto.

## 12. Invariantes e testes

I1–I20 continuam cobertos pelos testes de discurso/veto/reconciliação existentes. F1–F6 recebem uma matriz de 4 estados discursivos × 5 fidelities × 5 bindings, com resultados matemáticos positivos e negativos. A mudança de status do checker não altera os receipts semânticos.

| Invariantes | Verificação |
| --- | --- |
| F1–F6 | Produto cruzado de admissão; ausência de promoção por VERIFIED/FAILED |
| F7 | Variação isolada de confidence conserva autoridades e score |
| F8/F9/F19/F23 | Review concorrente na mesma obrigação e em outra preserva witness independente; nenhum target negativo |
| F10/F18 | Proveniência completa e rejeição de input digest/payload alterado após admissão |
| F11 | ACTIVE com payload não representável permanece sem autoridade automática |
| F12/F14 | Membership nos seis índices é contraevidência, nunca conjunto positivo completo |
| F13/F22 | Truncamento de igualdade, fortalecimento de inclusão e normalização sem suporte são rejeitados |
| F15/F16 | Pontuação depois de fração versus decimal; correção final falsa não ressuscita anterior verdadeira |
| F17/F20/F21/F24 | Scope, receipts, idempotência, ausência de efeitos duplicados, rastreio das perdas e reconciliação sem parsing do texto; complementados pelos testes I8/I9/I13/I20 |

Testes adicionais cobrem negados sem representação de polaridade, candidato negativo divergente do checker, mutation antes da projeção, A05 e as cinco classes causais com respostas gravadas. Os replays localizaram duas regressões intermediárias: término prematuro do claim antigo ao localizar seu número e perda do efeito de texto riscado ao estreitar campo tipado. A versão final só estreita o fim para marcador de revisão realmente embutido e registra strikethrough como retirada não adotada. Os testes observados S1_04/S1_06 preservam os 2 pontos já previstos historicamente. Não foi alterada expectativa histórica para produzir um PASS. O único teste existente modificado passou a fornecer o novo receipt no stub, mantendo seus asserts.

## 13. A05 — regressão observada

Fonte: `Minha lista fechada de compartimentos que dão branca ao repetir é {6}. Acrescento uma afirmação que também considero válida: repetir o compartimento 3 dá branca.`

O conjunto `{6}` continua fiel e matematicamente correto. A inclusão adicional agora vira átomo literal `member(3, repeated_second_white)`, com ACTIVE, fidelity EXACT e binding de contraevidência para b.same_compartment. A consulta finita existente refuta a inclusão; a política central autoriza AUTO_VETO. Não se inventou erro de fidelidade no conjunto positivo nem justificativa não escrita.

Resultado final: **0 pontos**, sem fallback ou technical uncertainty. O negativo possui status `DETERMINISTIC_FAILED`, fonte e receipts completos. [Cadeias dos seis casos prioritários](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_regression_01/causal_cases.json). O bloqueio ocorre na automação/reconciliação depois da refutação da inclusão; não por REVIEW_ONLY nem por rebaixar artificialmente o conjunto correto.

## 14. Cinco falsos vetos

| Caso | Final | Caminho de autoridade |
| --- | ---: | --- |
| p3_s03_b02 | 2 | Antigo SUPERSEDED; igualdade final ACTIVE e FORMAL_VERIFIED |
| p3_s03_b04 | 1 | Conjunto antigo SUPERSEDED; conjunto final verificado |
| p3_s03_b05 | 2 | Resultado antigo SUPERSEDED; resultado final COMPOSITE_VERIFIED |
| p3_s03_b08 | 2 | Contagem antiga SUPERSEDED; quantidade final vinculada e verificada |
| p3_s03_e01 | 4 | Citação NON_ADOPTED; probabilidade e contagem próprias verificadas |

B03 também preservou seus 2 pontos: o vínculo tipado passou a reconhecer a afirmação antiga; a relação escrita de apagamento precisava então retirar sua autoridade. A regra geral `apago esse/este/o valor/resultado/...`, com alvo e direção locais, resolve essa revisão. Marcador negado não produz supersessão. Essa regressão adicional foi incluída nos testes sem modificar a expectativa histórica.

B02 tem a igualdade realmente executada em Lean; a revisão não decorre do acerto dessa igualdade. B05 preserva o crédito de resultado isolado previsto pela pauta. B08 exige tanto retirar a autoridade do 4 quanto representar positivamente o 2. E01 distingue a probabilidade própria da citação; a contagem independente tem seu próprio binding, sem herdar autoridade do valor probabilístico.

Esses casos são regressões observadas. Recuperação não é evidência independente de generalização.

## 15. Replays observados

A tabela compara o score Semantic gravado com o replay Semantic atual de cada registro.

| Conjunto / registros históricos | Quantidade | Score gravado | Score replay final | Fallbacks herdados | Technical uncertainty |
| --- | ---: | ---: | ---: | ---: | ---: |
| tme_p3_semantic_formal_dev_01 | 8 | 32 | 30 | 1 | 0 |
| tme_p3_semantic_formal_dev_02 | 8 | 30 | 30 | 0 | 0 |
| tme_p3_semantic_robustness_01 | 48 | 67 | 71 | 1 | 0 |
| tme_p3_semantic_safety_02 | 80 | 88 | 104 | 1 | 0 |
| tme_p3_semantic_safety_03 | 40 | 34 | 49 | 3 | 0 |

São **184 registros de execução e 128 case_ids distintos**, com repetições entre rodadas históricas; não são 184 casos independentes. Safety02 inclui 32 casos próprios e 48 registros de regressão observada. Os 6 registros fallback ficam separados das 178 respostas históricas concluídas. Isso não mede sucesso de um extractor executado agora.

[Resumo caso a caso](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_regression_01/summary.json), [manifest e hashes da implementação](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_regression_01/run_manifest.json), [comparação por obrigação](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_regression_01/comparison.json), [índice dos traces completos comprimidos](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_regression_01/archive_manifest.json). Compressão gzip é sem perda; o índice contém hash dos bytes JSON e do arquivo comprimido.

Não houve award para obrigação marcada como não satisfeita nas expectativas observadas, ressalvada a política de E02 previamente corrigida pelo usuário: mantém 4 pontos e a expectativa histórica permanece intacta. Não houve perda frente ao replay unificado anterior, nem perda de obrigação previamente premiada e marcada como legítima nos contratos observados. Essas conferências são contra contratos DEV conhecidos, não acurácia geral/gold externo; não substituem auditoria independente.

O runner usa somente o raw_output gravado como resposta do provider. Se a extração histórica não foi concluída ou não há raw_output, não inventa uma resposta: registra fallback nativo unificado. O cliente OpenAI fica bloqueado por patch; api_calls do replay é zero. Expectations e receipts de construção não são enviados ao provider. Inputs históricos foram verificados por hash e permanecem intactos.

Rodadas exploratórias foram interrompidas ou substituídas para incorporar falhas de integração encontradas pelos testes/replay; seus outputs intermediários permaneceram em /private/tmp e não são apresentados como resultado final. O manifest final fixa os bytes da implementação antes/depois do replay completo.

## 16. Testes totais e comandos executados

Rodada final única de aceite dos bytes entregues: **1178 PASS, 0 FAIL, 0 ERROR, 0 SKIP**, sem somar repetições de depuração. [JUnit](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_regression_01/acceptance.xml), [stdout/stderr pytest](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_regression_01/acceptance.log), [log de replay](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_regression_01/replay.log).

Comandos executados no worktree P3 (saídas também redirecionadas aos logs correspondentes em /private/tmp/p3-multilayer-impl):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app \
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest \
-q -p no:cacheprovider tests/test_tme_p3*.py tests/test_tme_semantic_formal_p3*.py \
tests/test_pauta_engine.py tests/test_tme2_p3_pauta_bridge.py \
tests/test_tme_semantic_formal_c1.py tests/test_tme_semantic_formal_c1_fix.py \
tests/test_tme_semantic_formal_p2.py tests/test_tme_p2_partial_credit_fix.py \
tests/test_tme2_p1_pauta_bridge.py tests/test_tme2_p2_pauta_bridge.py \
--tb=short --basetemp=/private/tmp/p3-multilayer-impl/pytest-complete \
--junitxml=/private/tmp/p3-multilayer-impl/tests-complete.xml

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app \
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python \
scripts/evaluation/replay_tme_p3_multilayer.py \
--output /private/tmp/p3-multilayer-impl/replay-complete
```

A suíte inclui segmentação/fidelity/binding/automação, discurso, veto, reconciliação, conflict guard, abandonment, Semantic Formal P3, checker-first P3, PautaEngine, bridges P1/P2/P3 e regressões relevantes P1/P2. Não houve mudança compartilhada em P1/P2; testes desses módulos verificam a preservação.

Na primeira tentativa restrita, o teste Lean B02 produziu PermissionError ao criar artefatos temporários no worktree P3, fora das raízes graváveis da sessão. Essa falha de ambiente foi resolvida executando o teste autorizado com a permissão de filesystem necessária; nenhum checker/proposição foi corrigido para contorná-la.

## 17. Lean real

**24 testes nas integrações Lean P3 e no B02 gravado passaram**, cobrindo provas, refutações, UNPROVED, erro técnico injetado e preservação de créditos independentes. Os replays também usaram `use_lean=True`.

B02: `((2 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (3 : ℚ))`; checker status `verified`, epistemic status `FORMAL_VERIFIED`, compiled=`true`, score=2. stdout e stderr vazios. Isso é compilação/prova real da igualdade, não status inferido do LLM. A relação de supersessão foi determinada antes da prova. Os casos de falha injetada mantêm distinção entre ausência de prova, erro e refutação.

## 18. Preservação

Inventário inicial: **858 arquivos rastreados**. Somente 9 arquivos existentes foram modificados: oito módulos experimentais P3 e o helper do teste de veto. Os outros **849** arquivos mantiveram SHA-256. Prompt/schema, registry, StrongP3Checks, máquina, checkers matemáticos, Lean/Mathlib/proposições, pauta/pesos, P1/P2, documentação aprovada e fixtures/expectations ficaram intactos. A AST de `membership_result` é idêntica à original. Além do inventário rastreado, o manifest do replay confere os hashes dos 184 artefatos históricos de entrada antes/depois; os resultados novos usam outro diretório. [Recibo de preservação](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_multi_layer_regression_01/preservation.json).

Os novos módulos/teste/runner, este relatório e os artefatos de aceite estão fora desse conjunto de arquivos preexistentes. HEAD final permanece `f9e23b954756ea292429885abc5073125dcc8ada`; sem commit.

Não foram criados casos Safety04 nem alteradas fixtures/expectations observadas. Não houve tuning de prompt, uso de gold externo/holdout, extractor real/API, stage ou commit. Artefatos novos de regressão têm destino separado. A cópia de logs/manifests não substitui histórico anterior.

## 19. Limitações e diferenças de integração

A cobertura linguística continua deliberadamente limitada a construções verificáveis. FULL/EXACT descreve fidelidade do átomo, não entendimento universal do texto; um trecho sem representação continua review. Não se promete recall completo nem aceitação de toda paráfrase. PARTIAL/AMBIGUOUS/UNSUPPORTED nunca se tornam refutação automática.

Os contratos usam dicts serializáveis e snapshots dataclass em vez de sete serviços; relações e episódios são integrados ao resolver existente. Admissão usa a representação de fonte anterior ao checker e depois os outputs matemáticos, sem acoplar verdade ao estado discursivo. O registry e sua política pedagógica não foram ampliados.

Replays observados não substituem Safety04 independente. Fallbacks históricos não medem sucesso do extractor. Ganho de pontos não demonstra correção por si só; os casos causais foram auditados por receipt e as demais diferenças estão registradas por parcela. Revisão humana e avaliação inédita continuam necessárias antes de alegar segurança do P3 em geral.

## 20. Comandos futuros e conclusão

Para repetir a validação local sem API, a partir do worktree P3:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app \
  /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest \
  -q -p no:cacheprovider tests/test_tme_p3*.py tests/test_tme_semantic_formal_p3*.py \
  tests/test_pauta_engine.py tests/test_tme2_p3_pauta_bridge.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app \
  /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python \
  scripts/evaluation/replay_tme_p3_multilayer.py \
  --output /private/tmp/p3-multilayer-replay-NOVO
```

O diretório de replay deve ser novo. Nenhum comando acima chama extractor real; o replay usa respostas gravadas e bloqueia OpenAI. Criar/executar Safety04 ou usar API não faz parte desta entrega.

READY_FOR_P3_MULTI_LAYER_REGRESSION
