# TME P3 — Multi-layer Semantic Safety Architecture 01

## 1. Decisão, escopo e base de evidência

Este documento propõe sete camadas de segurança semântica para P3, preservando matemática, pauta e política central de veto. A implementação só poderá ser considerada segura depois de implementar e verificar os contratos aqui definidos. Prontidão arquitetural não significa correção implementada ou desempenho validado.

Princípio: **Formal verification is only as trustworthy as the proposition submitted to the verifier.** Uma prova matemática não certifica tradução, autoria, adoção atual, contexto ou vínculo pedagógico.

Worktree examinado: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3`. HEAD desta inspeção: `8c85ea67f2ba07b68e433e0dbf6ddf0668390958`. A execução Safety03 examinou `6fb07d4d15626e27b7c759a4e32f9cb3b415d2ea`; a implementação unificada está no pai `a6ab3d2c173ee801e1bc5a27d155215c054e007d`. Não confundir SHA do relatório atual com SHA avaliado.

Fontes: [Safety03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_SEMANTIC_SAFETY_03.md), [forense Safety03](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_SEMANTIC_SAFETY_03_FORENSIC.md), [arquitetura anterior](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_UNIFIED_DISCOURSE_VETO_ARCHITECTURE_01.md), [implementação unificada](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_UNIFIED_DISCOURSE_VETO_IMPLEMENTACAO_01.md) e artefatos gravados. As previsões deste documento são contrafactuais de projeto, não resultados de reexecução.

O forense estabeleceu `MULTI_LAYER_ROOT_CAUSE` e `MULTI_LAYER_FIX_REQUIRED`: A05 ganhou 2 pontos indevidos; cinco falsos vetos atingiram 9 pontos legítimos; os checkers matemáticos examinados estavam corretos. Não houve award sem checker, award produzido por guard nem bypass da política central. Isso localiza o defeito antes da autoridade matemática e na composição de suas premissas semânticas.

Prioridade institucional, nesta ordem: evitar falso crédito automático; evitar retirada indevida de crédito; aumentar recall somente dentro da fronteira segura. MAE ou ganho agregado não compensam violação de autoridade. Não se propõe zero global, revisão global ou retenção por qualquer palavra desconhecida para melhorar a primeira métrica.

Nesta tarefa foi produzido somente este Markdown. Não foram executados extractor, modos de avaliação, Lean ou testes de pipeline; não foram criados casos Safety04, alterados código/prompt/checkers/pauta/fixtures/expectations, acessados holdout/gold externo, feitos stage ou commit.

## 2. Arquitetura atual e gaps

Fluxo efetivamente implementado:

```text
EvidenceUnits do extractor + registros nativos
 → clause_view / adapt_payload / literal_property
 → DiscourseStateResolver + snapshot/ledger
 → projeções de evidência
 → mapper → verify / StrongP3Checks / matemática
 → produtores positivo, native_checker, atomic_guard, structural_guard
 → VetoEligibilityPolicy → reconcile
 → award → evidências de obrigação → PautaEngine → score numérico
```

O segundo `native_checker` verifica views do mesmo snapshot, inclusive IDs semânticos. Sua concordância não constitui validação independente da interpretação discursiva. O fallback Semantic usa o caminho unificado; o comparador TME_CURRENT é legacy separado.

| Camada atual / referência | Proteção existente | Gap demonstrado / mudança necessária |
| --- | --- | --- |
| [source_adapter.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/source_adapter.py) | Hash, envelope, ocorrência única de asserted_content, adaptação conservadora | `clause_view` usa quebra `\n\|(?<!\d)[.!?](?!\d)`; período depois de fração pode não separar sentenças. Ordem usa contexto expandido; faltam segmentos e relações temporais próprios |
| [discourse.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/discourse.py) | Ledger, quatro estados, relações de revisão, revisão hash, fonte local | `literal_property` participa da adoção; ausência de representação vira AMBIGUOUS. Seleção de predecessor exige início de source_range menor. Revisão depende de novo payload reconhecido. Gramática limitada de revisão/atribuição |
| [mapper.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/mapper.py) | Fonte, tipos, subjects, representação e rota do registry | Rejeição booleana mistura diferentes causas; não há certificado explícito de fidelidade nem binding claim↔obligation com relação tipada. Receipt discursivo evita nova checagem local de contexto |
| [unified.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/unified.py) e [conflict_guard.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/conflict_guard.py) | Um snapshot para produtores; guards sem award; consulta de membership já existe | Reconhecedores de membership estreitos; A05 não produz átomo negativo. Ausência de guard não prova consistência; fonte `unmapped` não pode desaparecer da auditoria |
| [verification.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/verification.py) / [StrongP3Checks](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_p3_checker_first/engine.py) | Resultados matemáticos e sufficiency; separação resultado/método | Verificar corretamente um payload não valida sua tradução/adoção; sufficiency não é certificado universal de integridade do discurso |
| [veto_policy.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/veto_policy.py) | Única autoridade negativa, recibos autênticos, estado/binding/refutação/scope/dependências | Recebe estados semânticos errados mas internamente válidos. `binding_valid` não separa localização, significado e vínculo pedagógico |
| [engine.py](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/app/confia_lean_auditor/experimental/tme_semantic_formal_p3/engine.py) | Witness positivo verificado, suficiente, atual; conflitos autenticados | `review_recommended=true` não governa autoridade. Falta fronteira comum explícita por candidato e obrigação, sem veto oculto de review |

A pauta permanece a existente: 13 obrigações, 20 pontos (a=4, b=8, c=8), composição `all_of`/soma/alternativas. Não criar requisito argumentativo para resultados que já recebem crédito isolado; por exemplo, a primeira probabilidade e o resultado de b têm seus contratos próprios. A arquitetura valida a autoria e a fidelidade do que foi escrito, sem aumentar a exigência pedagógica.

## 3. Fluxo proposto e contratos comuns

```text
Fonte imutável + propostas de extração (sem autoridade)
 → 1. DiscourseSegment / ClaimEpisode / grafo temporal validado
 → 2. RepresentationReceipt + átomos matemáticos tipados
 → 3. DiscourseReceipt (adoção, revisão, atribuição)
 → 4. BindingReceipt por claim–obligation–papel
 → 5a. AutomationEligibilityPolicy: admissão semântica ao checker
 → 6. checker existente + receipt matemático + sufficiency existente
 → 5b. candidato de award / candidato de veto / REVIEW_ONLY
 → 7. política central negativa + reconciliação determinística
 → decisão final AUTO_AWARD / AUTO_VETO / REVIEW_ONLY
 → PautaEngine inalterado → score numérico + diagnóstico de review
```

As sete camadas são responsabilidades, não uma exigência de sete serviços. A camada 5 tem duas fases; a decisão final depende da camada 6 e da política central da 7. Não há circularidade: a admissão não consulta o score ou o resultado matemático; o candidato negativo não é veto autorizado até a política central emitir receipt; o award só é finalizado depois dos vetos autenticados.

Todos os contratos abaixo são **propostos**, não descrições de schemas já disponíveis. Identidades são derivadas de conteúdo e revisão, nunca de posição em lista ou case_id. Campos de confiança são exclusivamente diagnósticos.

| Estrutura | Campos mínimos e responsabilidade |
| --- | --- |
| `SourceSnapshot` | source_sha256, texto imutável, item_ranges, versão do parser, coordinate_system=`unicode_codepoint_half_open`; byte offsets opcionais distintos |
| `DiscourseSegment` | segment_id, envelope_ranges originais, clause_range, assertion_ranges, paragraph_id, block_id, item_id, ordinal, previous/next, scope_parent, segmentation_status, receipt da segmentação |
| `ClaimEpisode` | episode_id, ordered_segment_ids, speaker, item, property/case/condition quando validados, scope, relações com episódios vizinhos; pode conter várias assertivas e revisões |
| `ClaimAtom` | claim_id, origin_evidence_ids, assertion_ranges, predicate, arguments, quantifier/exhaustivity, polarity, conditions, subject, original_payload, normalized_payload, representation_receipt_ref; nunca substituir o original |
| `DiscourseRelationReceipt` | relation_id, tipo (replaces/withdraws/quotes/hypothesizes/adopts/adds/changes_subject), from/to, marker_ranges, target_property, direção, scope, validator_version, VALIDATED/AMBIGUOUS/REJECTED, reasons |
| `RepresentationReceipt` | claim_id, source refs/hash, proposition_digest, representation_fidelity, covered/uncovered ranges, token-to-field map, normalization_steps, completeness_for_assertion, validator/rule/version, reasons |
| `DiscourseReceipt` | claim_id, discourse_state, speaker/adoption, relation refs, scope, state_reason, source refs, discourse_revision; sem booleano que confunda ACTIVE com representável |
| `BindingReceipt` | claim_id, obligation_id, item_compatibility, subject_compatibility, case/condition compatibility, semantic_relation, representation_fidelity e receipt_ref, binding_confidence_diagnostic, binding_status, validator/rule/version, source refs |
| `ObligationSupportBundle` | obligation_id, witness candidates, premise edges exigidas pela pauta, relações de incompatibilidade validadas, review refs separados, dependency paths, snapshot_revision; não contém nova regra de pontuação |
| `CheckerInputReceipt` / `CheckerResultReceipt` | input digest, atom refs, binding refs, contexto/modelo matemático e hashes, checker/version/route, output/status, proof/artifact refs, attempted, refutation flag com razão, componentes e technical_uncertainty |
| `AutomationDecisionReceipt` | decision_id, obligation_id, candidate/witness IDs, authority positiva/negativa/review, eligibility, razões, semantic receipt refs, checker/sufficiency refs, veto_policy_ref quando aplicável, source/graph/registry/policy/machine/pauta revisions |

Receipts de relações entre dois claims contêm ambos os spans, estados e bindings. Hashes autenticam integridade/revisão, não demonstram correção semântica. Reutilização com fonte, proposição, máquina, binding ou política diferente exige revalidação da cadeia correspondente.

## 4. Camada 1 — segmentação temporal e discursiva

**EvidenceUnit isolado é insuficiente.** Ele continua sendo o registro original da extração. `DiscourseSegment` representa a posição local; `ClaimEpisode` mantém continuidade e mudanças de speaker, item, propriedade e condição. Um envelope pode incluir várias frases sem transformar todos os claims em simultâneos.

1. Validar offsets contra a fonte original e localizar assertivas; uma ocorrência duplicada sem desambiguação não é escolhida por conveniência. Preservar envelope, cláusula e assertiva em campos diferentes.
2. Identificar limites por gramática lexical: decimal, fração, pontuação terminal, abreviação, newline e fronteira de item. Um ponto depois de dígito não é automaticamente decimal; registrar decisão e ambiguidade quando necessário.
3. Ordenar atos pelo assertion_range/segment ordinal validado, não pelo início do envelope expandido. Sobreposição de asserted_content deve ser decomposta em átomos com spans próprios se a decomposição for validável; caso contrário, revisão temporal fica ambígua, nunca “último objeto vence”.
4. Construir relações com evidência de marcador, alvo, direção e scope. Correção pode atravessar segmento, mas não atravessa item/subject/caso por proximidade. Adição, conclusão e mudança de assunto não são substituição. Uma tentativa não é NON_ADOPTED sem fonte que determine seu papel; hipótese pode ser adotada posteriormente por relação explícita.
5. Replacements são acíclicos e avançam no tempo da fonte. A→B→C validado torna A/B SUPERSEDED, mesmo se C for falso. Retirada sem substituto produz NON_ADOPTED com motivo próprio. Citação preserva speaker e eventual adesão posterior.
6. “Na verdade” pode validar autocorreção local com alvo e incompatibilidade escritos; não exigir universalmente uma fórmula específica de retratação. Sem alvo seguro, não escolher a propriedade que maximiza score. Outros atos de revisão têm validação por construção linguística completa, não apenas lista de palavras soltas.

O reconhecedor discursivo pode aceitar um ato de retirada mesmo sem payload matemático executável do substituto, desde que alvo e ato estejam validados. Isso remove o acoplamento que prejudicou B08. Se o alvo não for validável, AMBIGUOUS é legítimo; não converter o valor antigo em ACTIVE por default apenas porque o novo parser falhou.

## 5. Camada 2 — representation_fidelity

A pergunta é sobre **equivalência entre a assertiva escrita e a proposição submetida**, incluindo predicado, argumentos, polaridade, quantificação e condições. Não mede verdade matemática, adoção nem completude de uma obrigação pedagógica.

| Estado | Critério objetivo | Uso automático |
| --- | --- | --- |
| EXACT | Todos os campos semânticos do átomo correspondem diretamente a spans identificados; nada relevante omitido ou acrescentado | Pode seguir, sujeito às demais camadas |
| SUPPORTED_NORMALIZATION | Transformações sem perda, declaradas e conferíveis por regra versionada, preservam a proposição integral | Pode seguir; guardar forma original e passos |
| PARTIAL | Só uma parte de uma assertiva materialmente mais ampla foi representada, sem demonstrar equivalência do todo | Próprio candidato REVIEW_ONLY |
| AMBIGUOUS | Existem leituras semanticamente distintas que a fonte/validador não resolve | Próprio candidato REVIEW_ONLY |
| UNSUPPORTED | Campo ou relação não sustentado pela fonte, contradição texto–payload, ou representação sem validador adequado | Próprio candidato REVIEW_ONLY; registrar se erro de tradução ou limitação do validador |

Uma inclusão pode ser EXACT como inclusão e insuficiente para um conjunto exaustivo. Não chamá-la de PARTIAL apenas porque não satisfaz a obrigação positiva inteira. Já extrair só um membro de um conjunto completo escrito, omitindo os demais, é PARTIAL/UNSUPPORTED conforme a transformação. Essa distinção é essencial para F1/F2 e para recuperar negativos legítimos sem promover membership a resposta completa.

| Tipo | Regra de fidelidade mínima | Transformação proibida |
| --- | --- | --- |
| Número/quantidade | Número por extenso ↔ numeral por léxico exato; preservar sinal, unidade, objeto contado e posição sintática antes ou depois do predicado | Encontrar 2 em qualquer lugar e atribuí-lo a brancas inferiores |
| Conjunto | Preservar todos os membros, identidade do universo e declaração de exaustividade. Ordenação/deduplicação só quando a fonte é conjunto, não lista com multiplicidade | Remover membro errado; completar usando máquina; promover lista de exemplos a conjunto completo |
| Membership | Átomo `member(index, property, condition)` com spans para índice, evento/propriedade e contexto | Converter “3 dá branca ao repetir” em conjunto exato `{3}` ou em `{6}` |
| Igualdade | Preservar todos os lados, operadores, domínio e encadeamento escrito; normalizações tipográficas não apagam trecho falso | Truncar cadeia em igualdade verdadeira ou inventar `2/6=1/3` a partir de `1/3` |
| Probabilidade | Vincular evento, retirada/caso, condicionamento e expressão. Valor simples continua valor simples | Trocar probabilidade condicional por global; completar denominador/evento por resposta canônica |
| Cores | Enum escrito ou normalização lexical inequívoca, preso ao evento/compartimento/caso | Selecionar cor ótima porque o modelo finito a conhece |
| Compartimentos | Distinguir índice, cardinalidade, ordinal, escolha repetida/distinta, ordem das retiradas | Tratar “três bolas” como compartimento 3; substituir primeira por segunda retirada |
| Estratégia | Átomos separados de escolha de cor, contagem e caso, com relação de composição validada | Importar cor/contagem de outro caso/episódio; converter número correto em estratégia escrita |
| Relação combinatória | Preservar fatores e seus papéis, independência/distinção, produto/soma e justificativa efetivamente escritos | Transformar `36` em duas escolhas de seis, ou `10` em `2×5` com justificativa inventada |

Normalização de igualdade não depende de ela ser verdadeira. Um payload perfeitamente fiel pode ser refutado. Em contraposição, uma igualdade verdadeira montada pelo extractor pode ser UNSUPPORTED. Nenhum resultado do checker promove fidelity; ele só verifica o input identificado pelo digest.

## 6. Camada 3 — adoção e autoridade distintas

`discourse_state` continua ACTIVE/SUPERSEDED/NON_ADOPTED/AMBIGUOUS. AMBIGUOUS aqui é dúvida de adoção/atribuição/revisão; ambiguidade representacional fica em `representation_fidelity`. A mesma palavra em campos diferentes exige reasons e receipts diferentes.

| Estado | Interpretação | authority_for_positive_credit | authority_for_hard_veto | authority_for_review_only |
| --- | --- | --- | --- | --- |
| ACTIVE | Assertiva própria atualmente adotada, validada na fonte | Candidata; ainda exige fidelidade, binding, checker e sufficiency | Candidata; ainda exige refutação e política central | Sim se qualquer requisito não estiver resolvido |
| SUPERSEDED | Afirmação substituída por relação validada | Não | Não | Sim, com disposition histórica; não reabrir por matemática |
| NON_ADOPTED | Citação/hipótese/retirada sem adoção atual confirmada | Não | Não | Sim, com disposition de arquivo; não implica revisão humana obrigatória |
| AMBIGUOUS | Não se pode decidir adoção/atribuição/revisão com segurança | Não | Não | Sim, pendência explícita |

Os três campos de autoridade são resultados de política, não flags gravados pelo LLM. ACTIVE com representação UNSUPPORTED permanece ACTIVE, mas sem autoridade automática. SUPERSEDED fiel e matematicamente falso permanece sem veto. Um modelo dizer `abandoned=true` não retira autoridade por si só; dizer `attributed_to_student=true` não a concede. Preservar os sinais originais, sem sobrescrevê-los como se a projeção fosse a fonte.

Quando uma revisão é conhecida mas seu alvo é incerto, distinguir candidatos de relação e o que de fato ficou indeterminado. Não colocar todo o item em review e não declarar todos os valores ACTIVE por falta de marcador reconhecido. O estado deve apoiar-se em receipts positivos de fonte, não na ausência de correspondência de regex.

## 7. Camada 4 — BindingReceipt claim ↔ obligation

O binding valida para qual obrigação e **em qual papel** a proposição é relevante. Campos mínimos: claim_id, obligation_id, subject_compatibility, item_compatibility, case/condition_compatibility, semantic_relation, representation_fidelity com receipt_ref, binding_confidence_diagnostic, binding_status, source refs, rule/version.

`semantic_relation` distingue resultado, justificativa, premissa, membership relevante como contraevidência, conjunto exaustivo e incompatibilidade entre assertivas. O papel não declara verdade ou refutação: isso pertence ao checker. Um binding exato de membership pode permitir análise negativa sem satisfazer a obrigação positiva do conjunto completo.

| Binding status | Critério | Efeito |
| --- | --- | --- |
| EXACT_BINDING | Fonte/átomo identificam inequivocamente item, propriedade, condição e relação prevista no registry | Admissível nas funções autorizadas pelo contrato |
| VALID_EQUIVALENT_BINDING | Equivalência de nomenclatura/relação demonstrada por regra local versionada, com mesmos scope e requisitos | Admissível com receipt de equivalência |
| PARTIAL_BINDING | Falta componente necessário do vínculo, não apenas conteúdo adicional para pontuar | REVIEW_ONLY desse candidato |
| AMBIGUOUS_BINDING | Mais de um alvo/condição plausível sem decisão validada | REVIEW_ONLY desse candidato |
| INVALID_BINDING | Item/subject/condição incompatível ou ausência de relação autorizada | REVIEW_ONLY/rejeitado, sem authority |

A confiança sugerida pelo LLM é preservada para diagnóstico; não desempata bindings, não cria equivalência e não altera eligibility. Uma proposição igual em dois itens não autoriza copiar crédito entre eles. Um mesmo átomo pode ter receipts separados para papéis realmente previstos; toda propagação negativa segue apenas o grafo contratual existente.

## 8. Camada 5 — AutomationEligibilityPolicy e fronteira segura

### 8.1 Admissão e decisão em duas fases

Admissão exige fonte íntegra, segmento/átomo localizados, fidelity EXACT ou SUPPORTED_NORMALIZATION e binding EXACT_BINDING ou VALID_EQUIVALENT_BINDING. Matemática pode ser examinada para diagnóstico de registros históricos, mas o receipt deve marcar `diagnostic_only` e nunca ressuscitar autoridade.

Após checker e sufficiency, um candidato positivo só pode chegar a AUTO_AWARD quando:

- todas as premissas materiais do witness são ACTIVE, fonte/receipts atuais e compatíveis;
- representação de cada premissa é admissível; bindings são válidos para seus papéis e para a obrigação;
- rota está no registry; checker foi executado sobre exatamente o digest admitido e retornou status positivo autorizado;
- sufficiency existente está satisfeita; o candidato não é guard nem usa guard como justificativa;
- não existe AUTO_VETO autenticado aplicável à obrigação no snapshot final.

Um candidato negativo só pode chegar a AUTO_VETO quando:

- todas as premissas da refutação/contradição têm adoção atual autorizada, fidelity e bindings admissíveis;
- checker independente certifica refutação matemática ou incompatibilidade estrutural entre assertivas escritas; receipt contém premissas e tipo da contradição;
- a **VetoEligibilityPolicy central** valida a decisão e seus targets/dependency paths, emitindo receipt autêntico ligado ao mesmo snapshot.

FORMAL_UNPROVED/FORMAL_NOT_ATTEMPTED/FORMAL_ERROR, falha técnica, COMPOSITE_INCOMPLETE e ausência de prova não satisfazem refutação. COMPOSITE_FAILED só entra como negativo se o receipt demonstrar qual componente material refutou qual proposição e mantiver `mathematical_refutation=true` validado; o nome FAILED isolado não basta. Status semântico não substitui o checker matemático contratado.

Tudo o que não obtém autoridade final fica REVIEW_ONLY, com razões e disposition (pending, historical, rejected ou no_positive_witness). Essa classificação não exige intervenção humana para cada ausência e não muda a nota para None. O agregador distingue ausência de testemunho, review de candidato e veto efetivamente aplicado.

### 8.2 Granularidade: candidatos, obrigação e independência

A decisão é registrada por candidato/obrigação/papel; depois há redução por obrigação. Um candidato REVIEW_ONLY pode coexistir com outro AUTO_AWARD válido para a mesma obrigação. “Há review” não é condição global de bloqueio.

`ObligationSupportBundle` permite examinar premissas, duplicatas e relações validadas antes de finalizar o score. **Não introduz um requisito de resolução de todo texto desconhecido para conceder cada ponto.** Se o próprio witness depende de trecho mal representado, ele não é suficiente para automatizar; isso difere de usar um candidato ambíguo independente como contraevidência.

Independência é avaliada por grafo de premissas/condições e regras da pauta, não por distância textual ou confiança: uma contagem de a não depende de membership em b; dois candidates com mesmo obligation_id não são automaticamente duas versões incompatíveis. Só uma relação validada, com premissas e checker, pode produzir incompatibilidade autorizada. REVIEW_ONLY não cria essa relação nem aresta negativa.

Regras operacionais:

1. Se não há witness positivo admissível, não há award; registrar qual premissa própria faltou. Não chamar isso refutação.
2. Se há witness independente admissível e só review concorrente, preservar o award e registrar review.
3. Se há refutação ACTIVE/fiel/bound com veto central válido, aplicar o veto local e dependências existentes; não é ação de REVIEW_ONLY.
4. Se uma relação/payload não puder ser validada, registrar limitação de cobertura. Não obter artificialmente zero transformando qualquer incógnita em bloqueio.
5. Se um checker composto exige premissas conjuntas, todas devem ser compatíveis/atuais; não montar resposta com cor de episódio retirado e contagem final.

A hipótese do forense de “reter b.same por contexto não fechado” não é adotada como regra genérica. Sob F8/F9 e I6, reter um witness válido só porque há claim não representado seria veto disfarçado. A solução de A05 exige representar e verificar a inclusão real; fronteira sozinha não garante eliminá-lo. Se a implementação futura não conseguir fazê-lo, falha no aceite de cobertura, mesmo que todos os receipts internos estejam consistentes.

### 8.3 Score e custo de menor automação

O score é o número produzido pelo PautaEngine a partir de awards autorizados; zero automático não significa demonstração de que o aluno errou tudo. A saída inclui pontos concedidos, parcelas sem witness, parcelas com veto, reviews por razão e parcelas independentes preservadas. Incerteza representacional/discursiva não é automaticamente technical uncertainty; falha de execução é marcada separadamente.

A fronteira pode reduzir recall ao rejeitar traduções não demonstradas. Isso é aceitável como limitação explícita, mas perdas legítimas precisam ser contadas, inclusive retenções indevidas rotuladas review. Não se reivindica segurança total para linguagem fora da cobertura. Expandir cobertura requer validadores e testes gerais, não confiança LLM maior, MAE menor ou escolher o número canônico.

## 9. Camada 6 — integração com matemática preservada

Preservar integralmente StrongP3Checks, máquina finita, Lean, arithmetic checkers, composite checkers, constantes/modelos, regras de sufficiency e distinção resultado/método. Não trocar prova por interpretação, adicionar fato canônico ausente à resposta ou relaxar componente para aumentar score.

A integração muda a admissão dos inputs e a rastreabilidade dos outputs. Um adapter semântico aprovado constrói o mesmo tipo matemático esperado; o receipt liga cada campo à fonte. Para relações de inclusão, usar a consulta de membership já existente, não forçar o checker de conjunto exaustivo. `membership_result` consulta o certificado finito para o evento `(i,i)`; `structural_candidates` já contempla incompatibilidade conjunto exato–membro. A expansão necessária é de reconhecimento e vinculação de átomos, preservando esses significados matemáticos.

O checker responde apenas se a proposição recebida é matematicamente correta nas hipóteses declaradas. Ele não decide adoção, binding ou segurança de automação. Componentes atuais que recebem contexto, como `source_consistency`, devem receber projeções de receipts semanticamente admitidos; seu resultado não deve ser usado como prova de que o parser compreendeu todo o texto. Wrappers preservam o algoritmo matemático e expõem todas as premissas/condições no receipt.

Estados epistêmicos permanecem distintos: FORMAL_VERIFIED, FORMAL_REFUTED, FORMAL_UNPROVED, FORMAL_NOT_ATTEMPTED, FORMAL_ERROR; DETERMINISTIC_VERIFIED/FAILED e erros/incompletudes próprios; COMPOSITE_VERIFIED/FAILED/INCOMPLETE; SEMANTIC_SUPPORTED/INSUFFICIENT quando houver contrato pertinente. Não se cria rota de crédito semântico genérico em P3. CONTEXT_REJECTED é rejeição de admissão, não refutação matemática. Valor determinístico verificado não é FORMAL_VERIFIED sem igualdade realmente executada em Lean.

Uma execução diagnóstica sobre payload sem admissão pode produzir VERIFIED/REFUTED, mas continua sem autoridade e com fidelity original. Resultados históricos/cache precisam de identidade completa de input, checker e modelo; identidade textual do número não basta.

## 10. Camada 7 — reconciliação e veto

A reconciliação recebe bundles anotados com discourse_state, representation_fidelity, binding_status, automation eligibility, checker result, sufficiency e receipts de relações/política. Não lê prosa para decidir quem corrigiu quem, qual cor foi escolhida ou a qual item pertence um número.

A `VetoEligibilityPolicy` continua sendo a única emissora de veto. A nova AutomationEligibilityPolicy acrescenta requisitos de admissão comuns; não cria um canal alternativo negativo. Reconciliation autentica revisão/targets, deduplica e aplica decisões; award consome somente witnesses positivos finalizados e vetos autenticados. Duplicatas de produtores compartilham identidade semântica validada, preservando todas as origens no trace. Proximidade de spans não basta para deduplicar estados diferentes.

Preservar os targets atuais, sem propagação global:

| Origem negativa autorizada | Dependências existentes além da própria obrigação |
| --- | --- |
| b.ordered_pairs, b.different_favorable, b.same_compartment | b.second_white_probability |
| c.strategy_case_1 | c.conditional_success_1 e c.total_win_probability |
| c.strategy_case_2 | c.conditional_success_2 e c.total_win_probability |
| c.continue_compartments | c.total_win_probability |
| c.conditional_success_1 ou c.conditional_success_2 | c.total_win_probability |

Esses efeitos não declaram que toda conclusão dependente é matematicamente falsa: registram perda de suporte contextual segundo o contrato existente. As dependências positivas e `all_of`/soma/`max_of` continuam na pauta. Review não percorre esse grafo como se fosse refutação. Guards continuam sem preencher premissas positivas, mesmo quando verificam uma inclusão verdadeira.

Fallback Semantic deve percorrer os mesmos sete contratos com extração nativa e flag de fallback explícito. Fonte não interpretável não recebe estado inventado. TME_CURRENT comparador permanece inalterado e identificado como legacy; não se alegam garantias novas para ele.

## 11. A05 — reconstrução e intervenção arquitetural

### 11.1 Fonte e cadeia gravada

Fonte integral, confirmada no [artefato Semantic de A05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/tme_semantic_formal/p3_s03_a05.json):

> b) Minha lista fechada de compartimentos que dão branca ao repetir é {6}. Acrescento uma afirmação que também considero válida: repetir o compartimento 3 dá branca.

SHA-256 da fonte: `db8aa4d74053445f7a37a73b08b4571fea1841bbe294c98d481af99a2eda7ff5`.

| Campo | Conjunto positivo | Inclusão adicional |
| --- | --- | --- |
| Evidence ID | `E002:p3:1a9b2549534ea20bd788` | `E002:p3:962f452cebaf26ae3f12` |
| Envelope original | `[3,164)` | `[3,164)` |
| Assertiva/cláusula adaptada | `[3,73)` | `[74,164)`; predicado matemático literal `[128,163)` |
| normalized_claim real | `{6}` | `repetir o compartimento 3 dá branca.` |
| subject / claim_type | repeticao_branca / integer_set | unmapped / qualitative |
| Suggestion de obrigação/rota | b.same_compartment / DETERMINISTIC | b.same_compartment / SEMANTIC |
| Sinais do modelo | Asserted, positiva, main_argument, attributed, não abandonada | Asserted, positiva, main_argument, attributed, não abandonada; confidence .92 |
| Decisão de discurso real | ACTIVE, literal_own_assertion | AMBIGUOUS, unresolved_property_binding |
| Mapping | Aceito | Rejeitado: discourse_ambiguous |
| Checker / status | `tme2-p3-check.v1:2c145837f30d65f13a1d`, DETERMINISTIC_VERIFIED | CONTEXT_REJECTED; nenhum checker matemático executado para a inclusão |
| Sufficiency / efeito | true → b.same = 2 | false; sem guard, candidato negativo ou veto |

[A auditoria completa](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_a05.json) e o forense preservam os envelopes, receipts e IDs. A proposição efetivamente conferida foi a igualdade entre o conjunto escrito `{6}` e o conjunto derivado pela máquina `same_compartment_favorable=[6]`. O receipt é determinístico, sem subchecks, FORMAL_NOT_ATTEMPTED. Não houve Lean provando a inclusão de 3, nem conversão do falso 3 em verdadeiro 6.

O conjunto positivo é **fiel, verdadeiro e corretamente vinculado**. A05 não é exemplo de payload positivo fortalecido artificialmente. A segunda assertiva também foi extraída como texto; perdeu subject e representação executável. O modelo não disse que ela fora abandonada. A adoção está escrita em “também considero válida”. A matemática da máquina indica segunda bola preta no evento repetido 3; portanto a inclusão é falsa.

### 11.2 Cadeia proposta que impede os dois pontos

1. **Segmentação:** dois segmentos sucessivos no mesmo item, episódio e propriedade; relação `adds`, não `replaces`. Ranges diferentes, apesar do envelope comum.
2. **Representação:** manter o primeiro átomo `exact_set(repeated_second_white,{6})` com fidelity EXACT. Construir do segundo um átomo `member(3,repeated_second_white)` com fidelity EXACT, preservando índice, repetição e cor. Sua representação antiga qualitative/unmapped não recebe autorização matemática; um adapter validado produz novo receipt, sem apagar o original.
3. **Discurso:** ambos ACTIVE por fonte; não misturar desconhecimento do parser com incerteza de adoção. O marcador de adição não retira o primeiro claim.
4. **Binding:** primeiro EXACT_BINDING como conjunto completo; segundo EXACT_BINDING como membership relevante à mesma b.same_compartment e mesmo evento. A inclusão não é witness positivo suficiente do conjunto completo.
5. **Checker:** conjunto continua VERIFIED. O átomo de inclusão é encaminhado a `membership_result(3, machine)` existente, que certifica DETERMINISTIC_FAILED. Alternativamente, um receipt estrutural certificado demonstra que o conjunto exaustivo escrito exclui o membro também afirmado. Essa segunda via exige validar exaustividade na fonte, não apenas ver chaves sugeridas pelo modelo.
6. **Automação/política central:** o negativo agora tem fonte exata, adoção atual, fidelity suficiente, binding válido e refutação verificada. A política central pode emitir AUTO_VETO para b.same_compartment e suas dependências contratadas. O witness positivo permanece matematicamente VERIFIED, mas não pode ser finalizado como AUTO_AWARD naquela obrigação conflitante.
7. **Reconciliação/pauta:** b.same recebe zero por veto legítimo autenticado; outros créditos independentes não são alterados. Guard nunca gera award.

**Onde interromper AUTO_AWARD:** no fechamento da camada 5b/7, após recuperar nas camadas 1–4 a inclusão fiel e seu vínculo e obter a refutação na camada 6. Não seria correto reprovar a fidelidade ou o binding do `{6}` para fabricar esse resultado. A camada nova de representação torna o negativo verificável; a nova fronteira só lhe dá autoridade depois dos requisitos completos.

As regras são sobre inclusão, exaustividade, adoção e mesma propriedade, não A05, seu texto integral ou o índice 3. Devem tratar qualquer índice válido, predicado coberto, combinação de conjuntos e estados, inclusive inclusão verdadeira, negada, hipotética, citada ou retirada. A seleção matemática não usa expectation.

**Limite obrigatório:** se o validador não conseguir representar/vincular a inclusão, ela fica REVIEW_ONLY e não pode bloquear o positivo. Acrescentar somente um flag de fidelity/binding, sem essa cobertura, não soluciona A05. A futura implementação só passa o aceite se validar a inclusão/contradição geral; não se aceita obter zero por “unmapped ⇒ veto”, nem por exigir que toda evidência ambígua esteja resolvida. Isso preserva I6 e F8/F9 e torna testável o ponto de intervenção.

## 12. Cinco falsos vetos — classes, cadeia e correção proposta

Fontes integrais e receipts estão no [forense](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/docs/audits/TME_P3_SEMANTIC_SAFETY_03_FORENSIC.md). A tabela distingue fatos observados de efeitos previstos. Os cinco casos tinham score Semantic 0. Quatro têm testemunho final suficiente nos artefatos; B08 não tem.

| Caso / classe | Representação e estado reais | Binding / checker real | Veto e pontos afetados | Intervenção geral nas novas camadas |
| --- | --- | --- | --- | --- |
| [B02](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b02.json): perda de direção temporal por envelope | 1/2 antigo e `2/6=1/3` final fiéis; ambos ACTIVE. Assertivas `[3,55)` e `[56,124)`; source_range final expandido `[3,124)` | Primeira probabilidade bem identificada; 1/2 DETERMINISTIC_FAILED; final FORMAL_VERIFIED/sufficient=true | a.probability, 2 pontos. Antigo refutado ganhou autoridade corrente | Camada 1 ordena assertivas apesar do contexto comum; relação de substituição validada dá SUPERSEDED ao antigo. Camadas 3/5 removem autoridade negativa histórica; final mantém prova e sufficiency. Se alvo não for validável, negativo não recebe autoridade presumida: review local |
| [B04](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b04.json): revisão não reconhecida | `{1,4}` antigo e `{1,2}` final fiéis, ranges separados `[3,51)` e `[52,143)`; ambos ACTIVE apesar de “Retifico” | Vínculo continuar correto; antigo refutado, final verificado e suficiente | c.continue, 1 ponto; policy também aponta dependência c.total, sem crédito total escrito neste caso | Camadas 1/3 validam ato de retificação, alvo e conclusão definitiva; antigo SUPERSEDED. Não basta ampliar regex por case_id; testar construções de revisão versus adição/mudança de assunto |
| [B05](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b05.json): sobreposição temporal + invalidação | 7/36 antigo e 11/36 final fiéis; ranges de contexto ambos `[3,159)`; assertivas `[3,112)` e `[115,159)`; ambos ACTIVE | segunda_branca correta; antigo COMPOSITE_FAILED, final COMPOSITE_VERIFIED/sufficient=true. Result_credit_contract autoriza resultado isolado | b.conclusion, 2 pontos | Camada 1 decompõe afirmação antiga e ato de invalidação com seus spans; camadas 3/4 validam o alvo de “invalido esse valor”. Segmentar sozinho não basta: gramática atual também não cobre esse ato. Remover veto histórico preserva crédito de resultado sem criar argumento |
| [B08](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_b08.json): quantity binding acoplado à revisão | “quatro”→4 e “duas”→2 corretos; antigo `[3,40)`, final assertiva `[82,137)`, cláusula `[41,137)`; ambos ACTIVE | Novo rejeitado por white_count_not_bound_to_written_quantity; parser exige valor antes da quantidade. Resolver pula revisão sem nova propriedade reconhecida. Antigo DETERMINISTIC_FAILED; final CONTEXT_REJECTED | a.count, 2 pontos, com falta simultânea de witness positivo | Camada 3 resolve retirada da contagem sem exigir payload executável novo. Camadas 2/4 validam quantidade após predicado, com vínculo às brancas inferiores. Só então novo passa checker e sufficiency. Review/remover veto sozinho não recupera esses 2 pontos |
| [E01](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/artifacts/evaluations/tme_p3_semantic_safety_03/audits/p3_s03_e01.json): atribuição e não adesão | 7/12 da colega e 1/3 próprio fiéis; modelo marcou terceiro quoted/attributed=false, mas ambos ficaram ACTIVE | Propriedade primeira_branca correta; 7/12 DETERMINISTIC_FAILED; 1/3 DETERMINISTIC_VERIFIED/sufficient=true | a.probability, 2 pontos. Outra perda a.count=2 é representacional, fora dos nove pontos de falso veto | Camadas 1/3 mantêm speaker e scope de “colega dizia… transcrevo sem concordar”; terceiro NON_ADOPTED. Final próprio ACTIVE com binding válido. Rejeitar veto de citação preserva probabilidade; a contagem exige reparo próprio nas camadas 2/4 |

Detalhes necessários à causalidade:

- **B02:** a regex de fronteira ignora o ponto final depois de `1/2`; a igualdade de inícios impede selecionar predecessor antes de analisar “substituo”. Não reduzir o defeito a marcador desconhecido. O Lean histórico realmente compilou `((2 : ℚ) / (6 : ℚ)) = ((1 : ℚ) / (3 : ℚ))`, com norm_num; isso prova aritmética, não supersessão.
- **B05:** o marcador de invalidação aparece dentro de um asserted_content amplo. A contagem de relações temporais deve usar átomos/atos, não recortar cegamente por unidade de extração. `source_consistency` do composite examina três famílias de contagem de b, não constitui prova de ausência de probabilidade concorrente.
- **B08:** a fonte explicita “retiro o quatro”; a nova quantidade vem depois do substantivo. Não é erro de conversão de numeral nem simples ordem textual errada. Separar adoção de executabilidade é condição de recuperação.
- **E01:** o wrapper de não adesão já estava no contexto `[3,78)`; não basta ampliá-lo. Falhou sua interpretação. Recusar veto do terceiro não autoriza emprestar seu número à resposta própria.

Em todos, os payloads numéricos podem ter EXACT/SUPPORTED_NORMALIZATION e ainda não ter autoridade negativa. A solução não é enfraquecer o checker que corretamente refuta 1/2, `{1,4}`, 7/36, 4 ou 7/12. É não usar a refutação histórica/citada para bloquear posição atual.

Quando a nova validação não resolver o estado/binding, REVIEW_ONLY é o resultado do candidato incerto. Isso não promete recuperação de pontos: exige witness final independente e suficiente. Potencial de recuperação diretamente sustentado pelos receipts finais: B02(2)+B04(1)+B05(2)+E01 probabilidade(2)=7; B08 exige representação positiva adicional(2). Nenhuma dessas previsões foi executada nesta tarefa.

## 13. Invariantes preservados e novos

### 13.1 I1–I20 continuam normativos

A tabela resume os invariantes da arquitetura anterior, preservando sua finalidade. Em especial, I6 não é revogado por um “context completeness gate”.

| ID | Obrigação preservada |
| --- | --- |
| I1 | Guard nunca produz award nem preenche premissa positiva |
| I2 | NON_ADOPTED não produz hard veto |
| I3 | model_abandoned isolado não concede autoridade de veto nem apaga negativo adotado |
| I4 | SUPERSEDED não bloqueia a correção |
| I5 | AMBIGUOUS não gera witness positivo |
| I6 | AMBIGUOUS não derrota witness ACTIVE válido e independente; review não é veto disfarçado |
| I7 | ACTIVE refutado pode bloquear award incompatível em scope compatível, após política |
| I8 | Efeitos locais e apenas dependências existentes; preservar parcelas independentes |
| I9 | Todo bloqueio automático tem provenance, verificador e policy receipt; ausência não vira refutação |
| I10 | Permutar ordem de processamento preserva resultado do mesmo grafo temporal |
| I11 | Envelopes equivalentes preservam assertion identity, estado e autoridade |
| I12 | Nenhum produtor tem canal de autoridade negativa fora da política central |
| I13 | Deduplicação e idempotência de reconciliação |
| I14 | Supersessão independe da correção matemática da nova posição |
| I15 | Conservar conteúdo, polaridade e scope; não truncar igualdade ou remover membros |
| I16 | Mesma dependência negativa por origem/produtor |
| I17 | Preservar estados epistêmicos; UNPROVED/NOT_ATTEMPTED/ERROR não são REFUTED |
| I18 | Fallback Semantic segue a fronteira declarada; Current permanece comparador legacy |
| I19 | Receipts ligados à revisão; stale/mutated não chegam a award/veto |
| I20 | Composição usa premissas atuais de contexto/episódio compatíveis |

### 13.2 F1–F10 obrigatórios

| ID | Invariante | Critério de aceite |
| --- | --- | --- |
| F1 | Nenhum AUTO_AWARD com fidelity PARTIAL/AMBIGUOUS/UNSUPPORTED | Injetar cada estado em qualquer premissa positiva exclui apenas aquele witness |
| F2 | Nenhum AUTO_VETO com essas fidelities | Mesmo checker refutado não concede veto ao candidato |
| F3 | Nenhum AUTO_AWARD com binding ambíguo | Confidence alta ou resultado correto não contorna o binding |
| F4 | Nenhum AUTO_VETO com binding ambíguo | Refutação ou produtor nativo não contornam o binding |
| F5 | Checker VERIFIED não eleva fidelity | Receipt de representação permanece idêntico antes/depois |
| F6 | Checker REFUTED não eleva fidelity | Igual exigência para negativos e guards |
| F7 | LLM confidence não altera eligibility diretamente | Variar só confidence conserva decisões e score |
| F8 | REVIEW_ONLY nunca gera award ou hard veto | Injetar review não cria targets, blocked, witness ou dependency propagation |
| F9 | REVIEW_ONLY não elimina créditos independentes | Incluir review, inclusive na mesma obrigação ao lado de witness independente, preserva esse award |
| F10 | Toda AUTO_AWARD/AUTO_VETO tem provenance completa | Percurso até spans, revisões, binding, checker, sufficiency/policy, regra de pauta e pontos |

### 13.3 Invariantes adicionais propostos

| ID | Invariante e teste associado |
| --- | --- |
| F11 | Executabilidade não determina adoção: payload não suportado pode ser ACTIVE; literal falso retirado continua SUPERSEDED |
| F12 | Membership exato não vira conjunto exaustivo; inclusão verdadeira sozinha não ganha b.same; inclusão falsa elegível pode vetar |
| F13 | Número/cor/caso não são completados pela máquina; adapter recebe fonte/contrato, não expectation/score/valor canônico |
| F14 | Binding exato de contraevidência não é binding de suficiência positiva; papéis são conferidos separadamente |
| F15 | Ordem dos atos deriva da fonte/segmentos, nunca de envelope ou ordem de objetos; limites numéricos/decimais devem preservar relações |
| F16 | Revisão não depende de checker do substituto; uma posição final falsa pode retirar uma anterior verdadeira |
| F17 | Toda incompatibilidade estrutural preserva as duas proposições completas, adoções e condições; não comparar trechos de contextos diferentes |
| F18 | Digest do input matemático coincide com átomos admitidos; qualquer adaptação posterior invalida receipts e exige revalidação |
| F19 | Review não transita como negativo e não pode ser escondido como ausência de witness quando witness independente existe |
| F20 | Toda perda de pontos é auditável como falta de suporte, veto autorizado ou falha de admissão própria; medir retenção indevida mesmo sem rótulo veto |
| F21 | Duplicar interpretação em produtor nativo não aumenta certeza semântica nem número de efeitos; aliases exigem mesma proposição/scope/estado |
| F22 | Mudança de fidelity/binding exige novo receipt com regra e fonte, nunca promoção por confiança, acerto do número ou score esperado |
| F23 | Uma obrigação com review e witness suficiente continua distinguível de uma obrigação com veto; score numérico não apaga essa diferença |
| F24 | Reconciliação funciona com receipts fechados sem interpretar source_text; ausência de receipt não é substituída por heurística no reconciler |

## 14. Migração mínima proposta, sem implementação

| Ordem | Integração futura | Entrega/aceite antes de avançar |
| --- | --- | --- |
| 1 | Schemas/receipts versionados ao lado de evidence.py; SourceSnapshot e inventário de proveniência | Contratos e enumerações, hash/revisões, serialização; nenhum consumidor aceita defaults permissivos para campos novos |
| 2 | source_adapter.py: DiscourseSegment, ClaimEpisode, offsets e átomos | Separar envelope/cláusula/assertiva; cobrir pontuação numérica e múltiplos atos; conservar originais |
| 3 | discourse.py: relações e adoção sem dependência de payload executável | Target/speaker/scope validados, retraction graph, ACTIVE ≠ representável; invariantes I2–I6/I14 e F11/F16 |
| 4 | mapper/source adapters: RepresentationReceipt e BindingReceipt | Quantidades nas ordens sintáticas admitidas, conjunto/membership, evento/condição; ampliar cobertura geral sem trocar matemática |
| 5 | verification/unified wrappers + AutomationEligibilityPolicy | Admitir somente inputs fiéis, digest completo, sufficiency atual, negativos preparados sem autoridade autônoma |
| 6 | veto_policy/reconciliation/award | Acrescentar requisitos de fidelity/binding; única autoridade negativa; bundles sem bloqueio por review; numeric closure e fallback preservados |
| 7 | Trace/diagnósticos e gates de aceitação | F1–F24/I1–I20, regressão observada, nenhuma perda oculta; nova implementação congelada antes de Safety04 |

É uma migração de contratos e adapters, não alteração de pauta ou enfraquecimento de StrongP3Checks. Nomes/arquivos novos são sugestões de localização, não arquivos criados aqui. Modo de comparação offline pode emitir receipts novos em shadow sem pontuar; ativação futura exige não misturar receipts antigos sem campos obrigatórios com decisões novas. Um único snapshot por avaliação evita meio pipeline usando autoridade antiga e outro usando nova.

Semântica ou construção fora de cobertura deve produzir motivo explícito. Não é aceitável corrigir só os seis textos, adicionar case IDs ao runtime, usar expectativas na admissão ou retunar o prompt para fabricar payloads mais convenientes. A implementação futura deve preservar interfaces matemáticas e comprovar que diferenças vêm da fonte/autoridade, não da resposta de referência.

## 15. Testes necessários e cobertura atual

Há testes existentes de [discurso](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_discourse_state.py), [política de veto](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_veto_policy.py), [reconciliação unificada](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_unified_reconciliation.py), [abandonment safety](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_abandonment_safety.py), [preservação de conflitos](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_conflict_preservation.py), [checker-first](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_checker_first.py), [Semantic P3](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_semantic_formal_p3.py) e [ponte de pauta](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme2_p3_pauta_bridge.py). Integrações Lean têm arquivos [checker-first Lean](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_checker_first_lean.py), [Semantic Lean](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_semantic_formal_p3_lean.py) e [unified Lean](/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p3/tests/test_tme_p3_unified_lean.py). Não foram rodados nesta tarefa.

Os testes atuais já nomeiam invariantes, por exemplo `test_I6_ambiguous_does_not_defeat_independent_active_witness`, `test_I11_overlapping_envelope_does_not_change_retraction`, `test_I17_no_refutation_from_unproved_incomplete_or_error` e `test_na_verdade_adjacent_bound_correction_is_supported`. Safety03 demonstrou que validade interna desses invariantes e cobertura linguística real são dimensões distintas; novos testes não podem só espelhar booleans do resolver.

Plano de testes antes da nova avaliação:

| Grupo | Verificações necessárias |
| --- | --- |
| Segmentação | Ponto terminal após inteiro/fração versus decimal; asserted_content com mais de um ato; envelopes sobrepostos; offsets Unicode/normalização; duplicação de ocorrência; item/parágrafo/citação e mudança de subject |
| Discurso | Revisão explícita e implícita local; retirada sem substituto; correção falsa; adição compatível/incompatível; citação com/sem adoção; alvo indefinido; tentativas/hipóteses; estratégia com revisão parcial |
| Fidelidade | Igualdade inteira, conjunto sem truncamento, membership não exaustivo, palavra/numeral, quantidade antes/depois do predicado, evento/condição, cor/contagem e caso; transformações sem conteúdo adicional |
| Binding | Mesmo número em outra propriedade; condição distinta; rota sugerida inválida; membership como contraevidência sem crédito de conjunto; equivalência comprovada versus confidence |
| Fronteira | Produto cruzado dos quatro estados discursivos, cinco fidelities e cinco bindings, com statuses matemáticos positivos/negativos/incompletos; esperar decisões por contrato, não pelo runtime sob teste |
| Review e independência | Mesmo obligation_id com review concorrente e witness independente; outro item; premissa própria incompleta versus negativo ambíguo; review não bloqueia nem propaga; verificar pontos e receipts |
| Adoção negativa | Inclusão falsa ACTIVE → veto central; inclusão verdadeira guard → nenhum award; mesma inclusão retirada/citada/ambígua → sem veto; conjunto completo legítimo preservado quando independente |
| Receipts/produtores | Tamper/stale/input digest; alias nativo-semântico; permutação de processamento; dedup/idempotência; todos os produtores passando política; nenhuma interpretação de texto na reconciliação |
| Matemática e pauta | Mesmos inputs admitidos dão mesmos resultados matemáticos; result-only continua permitido onde previsto; guard não inventa método; all_of/max_of/pesos inalterados; prova Lean real em integração autorizada futura |
| Fallback | Falha do extractor declarada; mesmo contrato de autoridade no native fallback; Current unchanged; não confundir erro técnico com refutação |

Usar artefatos observados para regressão offline sem nova API quando possível, preservando saídas históricas. Esperados devem derivar da fonte/pauta/contrato e das classificações forenses registradas, nunca ser recalibrados depois do novo score. A05 e os cinco falsos vetos são regressões conhecidas, não demonstração de generalização. Testes estruturais devem verificar o caminho que produz a decisão, não só a nota final.

Aceite para avançar: nenhum falso award material, nenhum veto sem autoridade, A05 resolvido pelo átomo/contradição real, negativos retirados/citados sem veto, créditos independentes preservados, perdas representacionais explicitadas e regressões I/F satisfeitas. Retenção via review conta como erro quando retira crédito independente; não pode melhorar artificialmente a métrica de falsos vetos.

## 16. Plano de Safety04 — futuro, independente, não criado

Safety03 é **OBSERVED FAILURE / REGRESSION DATASET**. DEV01/02, robustness01, Safety02 e demais conjuntos já observados também não validam independentemente a próxima mudança. A referência histórica da arquitetura anterior a Safety03 “ainda não criado” pertence àquela data; a próxima avaliação inédita será Safety04.

1. Após implementação e testes, congelar SHA, prompt, adapters, policy, registry, máquina, pauta, toolchain e configuração de execução. Registrar o protocolo antes de avaliar.
2. Construir fontes inéditas por classes de risco e variação linguística/temporal, sem copiar ou fazer paráfrases triviais dos textos observados. Neste documento não se escreve caso, fonte, fixture, expectation nem número fechado de casos Safety04.
3. Revisar previamente spans, estados, fidelity, binding, obrigações, relações e parcelas por fonte/pauta/modelo; examinar ambiguidades reais e relações cor–contagem. Não validar apenas o valor canônico. Usar revisão independente quando disponível e declarar suas limitações; não alegar gold externo.
4. Congelar por hashes fontes, IDs, expectations, receipts de construção e manifest antes de qualquer execução. Destinar ao extractor somente entradas autorizadas, sem expectations/rationales/receipts. Documentar independência e acesso aos dados.
5. Execução futura requer sua autorização e configuração predefinida de modelo/effort/timeout/tokens/retries; uma execução por modo segundo protocolo, sem tentativas escolhidas pela nota. Separar ALL, Semantic-success, fallback e technical uncertainty. Nenhuma execução foi iniciada aqui.
6. Auditar por obrigação todas as cadeias de concessão/veto e amostrar corretamente revisões sem efeito: source → segmento → átomo → fidelity → estado → binding → checker → sufficiency/policy → decisão → regra/pontos. Confirmar autoridade substantiva, não só receipt autêntico.
7. Métricas prioritárias: casos/obrigações/pontos de falso crédito; falsos vetos e retenções indevidas por review; resgates legítimos e missed credit; cobertura de classes, fidelity/binding/discourse errors; dependências/independência; fallbacks/erros técnicos. Ganho de score/MAE são auxiliares e não compensam falha de segurança.
8. Aceite independente exige ausência de falso crédito material, ausência de retirada indevida material por autoridade ou review, preservação de independência e cobertura suficiente das classes pré-registradas. Falta de cobertura ou erro técnico que impeça observar classe relevante limita o veredito. Após execução, Safety04 também vira observado; não mudar expectativas ou reutilizá-lo como avaliação independente de novo fix.

## 17. Integridade e veredito arquitetural

A proposta separa o que hoje está acoplado: posição temporal, tradução matemática, adoção, vínculo pedagógico e autorização automática. Define uma fronteira positiva e negativa comum, preservando o único emissor de veto, os checkers e a pauta. A05 requer cobertura de membership fiel; os cinco falsos vetos requerem correção de discurso/segmentação/binding. Uma boundary isolada não resolve ambas as classes.

READY significa que há contratos, pontos de integração, tratamento das tensões entre review e veto, critérios de aceite e plano de validação. Não significa código corrigido, pontos recuperados experimentalmente ou segurança universal para linguagem livre. Nenhum resultado novo de avaliação foi produzido.

Inventário de preservação desta tarefa: 990 arquivos existentes, incluindo os artefatos e fixtures Safety03, conferidos por SHA-256 antes/depois; zero alteração de bytes. HEAD permaneceu `8c85ea67f2ba07b68e433e0dbf6ddf0668390958`. O forense anterior já estava não rastreado no início e foi preservado. A única criação no worktree nesta tarefa é este documento. Sem stage/commit.

MULTI_LAYER_ARCHITECTURE_READY
