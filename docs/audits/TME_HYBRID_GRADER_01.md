# TME_HYBRID_GRADER_01

**Decisão: NO_GO_FOR_HOLDOUT.** A arquitetura opt-in foi implementada, congelada e executada nas 25 DEV com `gpt-4o-mini-2024-07-18`. A cobertura aparente subiu de **43/409 (10,5%)** no histórico genérico para **268/409 (65,5%)**, com ganho em **4/5 problemas**, mas a revisão encontrou falso crédito e vínculos semânticos incorretos. **Active DEV não executado. HOLDOUT permanece fechada.**

A primeira tentativa externa foi bloqueada pela revisão automática por causa da preferência anterior de análise local. Após a resposta explícita do usuário **“Autorizar as 25 DEV”**, foram realizadas exatamente **25 chamadas**, com `store=false`, **zero retries**, **21 respostas válidas e quatro inválidas**. O snapshot retornado pelo provider foi exatamente o solicitado. Código, prompt, pautas, modelo e payloads não foram ajustados após observar os resultados.

## Resultado do shadow

| Métrica | Resultado |
|---|---:|
| Obrigações do DEV | 730 |
| Julgamentos válidos / semanticamente satisfeitos | 543 / 471 |
| Supported reconciliadas, em todas as obrigações | 360 |
| Supported entre as 409 aparentemente satisfeitas | **268 (65,5%)** |
| Baseline determinístico / histórico genérico, entre 409 | 24 / 43 |
| FORMAL_VERIFIED / DETERMINISTIC_VERIFIED | 6 / 35 |
| SEMANTIC_SUPPORTED | 319 |
| FORMAL_REFUTED / DETERMINISTIC_REFUTED como tier final | 1 / 0 |
| CONFLICT (refutação determinística preservada) | 1 |
| INDETERMINATE / SEMANTIC_NOT_SUPPORTED | 113 / 70 |
| TECHNICAL_ERROR | 185 |
| Casos com needs_review | 13/25 |
| Pontos potenciais conhecidos | 319 |
| Pontos audit-only / participação | 49 / 15,36% |
| Semantic-only potential points / participação marginal | **270 / 84,64%** |
| Suporte baseline perdido | **0** |

As quatro respostas inválidas deixam 187 obrigações sem julgamento utilizável; duas conservam evidência auditada anterior, restando 185 erros técnicos. Falha de protocolo não foi convertida em erro matemático ou nota zero. Há 21 notas potenciais numéricas; os outros quatro casos conservam nota potencial global `null`.

| Problema | Aparentemente satisfeitas | Histórico supported | Hybrid supported dentro desse conjunto | Hybrid supported total |
|---|---:|---:|---:|---:|
| P1 | 77 | 29 | 62 | 83 |
| P2 | 91 | 7 | 90 | 113 |
| P3 | 50 | 4 | 27 | 28 |
| P4 | 97 | 1 | 87 | 134 |
| P5 | 94 | 2 | 2 | 2 |

O critério numérico de cobertura (mínimo 205/409) e o ganho em quatro problemas passaram. A exigência pré-declarada de 25 respostas válidas não passou. A segurança também não passou, independentemente dessa exigência: os créditos incorretos impedem a promoção mesmo se a validade de 21/25 fosse aceita. Os **92 supported fora das 409** foram triados separadamente; estar fora desse conjunto não demonstra automaticamente um erro. A inspeção anterior é um indicador de cobertura, não um gold completo de correção matemática.

Na comparação auxiliar pareada dos mesmos 21 casos com nota potencial numérica: baseline determinístico MAE **15,95**, histórico genérico **15,00**, shadow híbrido **4,67**, bias híbrido **−1,90**; exact **5/21**, ±1 **8/21**, ±2 **10/21**. Essas são métricas da **nota potencial shadow**, não active. A melhora sintética não compensa falso crédito.

## Revisão e falhas observadas

Foram inspecionadas integralmente cinco soluções, uma por problema, e triadas as 92 obrigações supported fora do conjunto aparentemente satisfeito, além do conflito auditado. P5_02 fazia parte da amostra inicial, mas sua resposta inteira foi rejeitada; foi usado o primeiro sucessor válido, P5_09. Os achados conservadores são **15 obrigações com falso crédito, seis outros suportes de critério incorretos e seis atribuições a trechos inadequados**, todos sobrevivendo à reconciliação. Não é uma estimativa exaustiva de precisão.

| Caso | Fonte real e falha | Consequência observada |
|---|---|---|
| P1_06 | O aluno escreve `3·10=20` e conclui 20; o modelo certifica conclusão 30 | `d.total_thirty` recebe SEMANTIC_SUPPORTED |
| P1_13 | O aluno conta nove valores para b e conclui 27; o modelo certifica dez e 30 | Nota potencial 20, sem review automático |
| P2_01 | `2^4=8`, total 192; o modelo substitui por 16 e 384 | Critérios de orientação/produto/total apoiados; nota potencial 20 sem review |
| P2_08 | O modelo reconhece total 192 incorreto, mas aprova o produto alternativo `24×16`, que não foi escrito | `max_of` recebe um caminho indevidamente apoiado e a nota potencial permanece 20 sem review |
| P4_16 | Só foi resolvido o caso com raiz 13/3 | Modelo também certifica segundo caso e raiz 5/3 ausentes |
| P4_21 | O item apenas nomeia Pitágoras e fornece as raízes | Equações e exclusão da hipotenusa 12 ausentes recebem suporte; nota potencial 20 sem review |
| P5_09 e P5_22 | `E001` contém apenas `(a)`; a lista está em E002 | A obrigação da lista recebe suporte com vínculo insuficiente, dois pontos por caso |

Um contrafactual diagnóstico, que apenas retira suportes semanticamente incorretos confirmados e recalcula pelo **mesmo PautaEngine**, reduz os pontos conhecidos em **18**. Retirar também vínculos incorretos reduz em **22**. Não foram substituídos os resultados originais nem produzidas notas “corrigidas”; esses valores são contribuições marginais conservadoras, respeitando caminhos alternativos e limites. Os quatro pontos adicionais de P5 são falha de atribuição, não prova de que a lista matemática existente em outro trecho esteja errada.

Os controles locais passaram, mas não anteciparam esses erros live. `false_credit_controls.json` separa os **29 controles adversariais híbridos e 87 testes dos protocolos anteriores aprovados** dos exemplos negativos reais do DEV que falharam. O gate geral de segurança está marcado como **FAILED**. No P4_19, a justificativa usa a identidade falsa `(6−x)^2=36−x^2`; o modelo a aprova, mas a reconciliação não a promove. Essa retenção ocorreu no gate de contexto e não deve ser apresentada como refutação formal da conta.

Três limitações foram identificadas sem retuning:

1. **Fidelidade semântica à fonte:** IDs válidos e confiança alta não impedem substituir respostas erradas do estudante pela resposta da referência. Extrações matemáticas rejeitadas por representação/grounding ainda podem cair no caminho de suporte semântico. Falta distinguir ausência de verificador de evidência de que o conteúdo atribuído não está no trecho.
2. **Contexto e fronteiras:** uma unidade física com vários itens pode ser rejeitada por conter itens alheios ao alvo. Além disso, o detector experimental de marcadores reconhece `a)`/`c)` no fechamento de expressões algébricas como itens, deslocando o contexto. P1_06 perde passos corretos de (b) por esse problema. Foram 114 julgamentos positivos com contexto rejeitado. Não foi corrigido o código congelado depois da execução.
3. **Protocolo global:** P3_22 e P5_24 referenciaram extrações fora dos IDs selecionados; P5_02 omitiu as seis obrigações de (b); P5_18 declarou 37 obrigações satisfied sem IDs. As respostas brutas e erros foram preservados, sem reparo pós-hoc.

O conflito único, P1_12 `d.difference_six`, evidencia também um problema **pré-existente**: o extrator auditado recortou `a−c=594` da expressão completa `a−c=594÷99=6`, gerando refutação para uma proposição truncada. A reconciliação preservou a evidência anterior conforme o contrato e forçou revisão. O conflito não demonstra que o raciocínio completo do estudante seja falso. A trilha em `reconciliation.jsonl` contém o record e a fonte completa para revisão.

## Implementação

Fluxo opt-in: solução integral → avaliador semântico global (protocolo em `hybrid_semantic.py`) → julgamentos por obrigação com evidence IDs → auditoria seletiva pelos collectors/checkers/Lean existentes → `EvidenceReconciler` → `PautaEngine`.

Não há integração automática com HTTP, transcrições aceitas, UI ou casos persistidos. `run_hybrid_shadow` devolve o assessment baseline separado do potencial. A ativação exige gate explícito e o runner grava apenas artefatos DEV isolados.

| Componente | Função |
|---|---|
| `app/confia_lean_auditor/student_claims/hybrid_semantic.py` | Schema fechado, enunciado integral, referência, pauta sem pesos, métodos, fonte integral, IDs; uma chamada por solução |
| `app/confia_lean_auditor/tme/hybrid_grader.py` | Contexto global, decisões cross-item, auditoria seletiva, reconciliação e rota shadow |
| `app/confia_lean_auditor/rubric/pauta/evidence_policy.py` | Aceitação e revisão semânticas somente mediante política opt-in |
| `app/confia_lean_auditor/rubric/pauta/engine.py` | Parâmetro opcional de política; aritmética, combinadores, limites e carry-forward preservados |
| `app/confia_lean_auditor/tme/references/hybrid_official.json` | Resolução oficial normalizada e conferida visualmente, sem tabela de pontuação |
| `scripts/evaluation/evaluate_tme_hybrid_grader.py` | Prepare/freeze → shadow → revisão/gate → active, restrito à lista congelada de 25 DEV |
| `tests/test_tme_hybrid_grader.py` | Contratos, precedência, grounding, contexto, revisão, isolamento, Lean real e carry-forward |

O novo protocolo não chama o carregador antigo `semantic.statement_for`: ele retorna vazio para o catálogo TME atual. O enunciado é carregado por allowlist de `statement_blocks` e descrições das figuras em `problems/TME2026P1`–`P5/problem.json`, sem o campo `max_score`.

A referência oficial é o PDF local `Segunda Fase TME² - Gabarito com pauta.pdf`, SHA-256 `a2660f1c0761738a8b9232dc179feaea9538efb45102e1b2a9b991a3dd2ac384`. Foram conferidas as páginas 2, 4–5, 7–8, 10–11 e 13–14. A transcrição normaliza fórmulas e tabelas matemáticas; exclui as tabelas de correção. A referência é âncora e não impõe um método: paralelogramo e maximização geral por 3s/2s são explicitamente aceitos pelo prompt quando válidos e sustentados pela fonte.

## Contratos e limites

`SemanticObligationJudgment` contém obrigação, julgamento (`satisfied`, `not_satisfied`, `uncertain`, `contradicted`), IDs, caminho, modo assertivo, confiança, razão e extrações matemáticas opcionais. O modelo não recebe pesos, notas baseline ou synthetic labels; não emite nota, decisões do engine, spans ou offsets. IDs desconhecidos, obrigações ausentes/duplicadas e suporte sem evidência invalidam a resposta. Falha do provider permanece erro técnico.

A fonte e os evidence IDs atuais são preservados. Hints adicionais reconhecem marcadores inline, mas não resegmentam nem truncam a fonte. Reuso entre itens exige uma dependência declarada e evidência do item destino. Cada decisão registra itens de origem, destino, permissão ou rejeição. Texto sem marcadores permanece disponível ao julgamento global.

Os context gates preservam negações, hipóteses, citações, rejeições e conflitos presentes no contexto não selecionado. Há guardas de conteúdo necessário para evitar conclusão isolada como justificativa e nome de método como demonstração de consequências. Essas guardas não constituem um verificador matemático universal: a validade de prosa depende do julgamento semântico e precisa ser medida na revisão live. Os gates conservadores podem rejeitar demonstrações válidas por hipótese/contradição ou correções textuais; isto é limitação de cobertura, não validação de todo o raciocínio.

As extrações matemáticas que cabem nas representações existentes passam pelo `EvidenceProjectionSession`, preservando `MathClaimRecord`, canonicalização, grounding, FactResult, checkers e Lean. Ausência de representação, fronteira rígida da projeção ou falta de verificador **não bloqueiam por si sós** o caminho semântico válido. As limitações antigas continuam registradas no ramo de auditoria seletiva, sem serem transformadas em ausência de compreensão semântica.

**Lean é auditor formal seletivo, não requisito universal de pontuação.** Uma justificativa verbal válida pode produzir `SEMANTIC_SUPPORTED` sem FactResult. Uma igualdade auditável pode produzir `FORMAL_VERIFIED`; uma enumeração confirmada pode produzir `DETERMINISTIC_VERIFIED`. A evidência semântica mantém `origin=semantic` e `verification_source=semantic`, sem ser rotulada como prova matemática automática.

O reconciliador não calcula pontos. Evidência formal/determinística existente tem precedência. Discordâncias conservam o estado auditado, registram `CONFLICT` e forçam revisão; a trilha distingue conflito sobre trecho coincidente de discordância no nível da obrigação. Falha técnica não vira refutação. Julgamento semântico negativo recebe tier `SEMANTIC_NOT_SUPPORTED` e status de engine `indeterminate`: ausência ou inadequação de demonstração não é fabricada como refutação formal. A política `withhold` existente aplica sua regra normal.

Carry-forward semântico novo não inventa vínculos condicionais: adoção, dependência e coerência continuam exigindo o contrato auditado existente e a referência exata ao resultado anterior. A evidência de erro anterior não é reescrita como correta. O teste específico confirma preservação do crédito condicional existente.

A mudança no PautaEngine limita-se à aceitação de origem e política de revisão. Sem `evidence_policy`, comportamento legado permanece. Com a política experimental, suporte semântico grounded de confiança alta não exige revisão automaticamente; confiança medium/low e conflitos exigem. Outras incertezas da pauta ainda podem exigir revisão do caso inteiro. `additive`, `banded`, `max_of`, `all_of`, `any_of` e carry-forward mantêm a mesma aritmética.

`semantic_only_points` é a diferença entre `known_points` com toda evidência reconciliada e com somente evidência auditada, ambos calculados pelo PautaEngine. É uma contribuição marginal que inclui dependências e seleção de caminhos; não é soma artificial de pesos por obrigação. A participação formal/determinística é reportada conjuntamente pelo contrafactual audit-only. Semântica e auditoria podem contribuir para o mesmo conjunto de requisitos, portanto não se afirma uma partição aditiva única entre fatos.

## Congelamento e promoção

Artefatos: `artifacts/evaluations/tme_hybrid_grader_01/`.

- `experiment_freeze.json`: hashes de código, testes, referências, pautas, enunciados, fontes DEV, schemas e payloads.
- `prepared_payloads/`, `evidence_units/`, `schemas/`: 25 entradas prontas e revisáveis, 730 julgamentos esperados e 335 evidence units preservadas.
- Modelo congelado: `gpt-4o-mini-2024-07-18`, temperatura 0, `store=false`, endpoint `https://api.openai.com/v1`, sem retry automático, limite de saída 16000.
- As 25 respostas do provider identificam o snapshot `gpt-4o-mini-2024-07-18`.
- Gate pré-declarado: 25 respostas válidas; pelo menos 205 das 409 obrigações aparentemente satisfeitas reconciliadas como supported; ganho em pelo menos 4/5 problemas frente ao baseline genérico histórico; zero falso crédito/atribuição conhecidos; controles e regressões aprovados; revisão amostral live plausível.
- Shadow precede active. Active reusa os mesmos julgamentos e hashes, sem nova inferência ou alteração de código/prompt. Casos reais permanecem intactos.

O baseline determinístico congelado contém 24 obrigações supported; o histórico genérico contém 43. A inspeção anterior identificou 409 aparentemente satisfeitas. Synthetic labels foram consultados somente na agregação posterior ao shadow, nunca enviados ao modelo nem utilizados para ajustar os julgamentos.

Todos os artefatos solicitados existem. `semantic_judgments.jsonl` tem 543 julgamentos válidos, `reconciliation.jsonl` tem 730 decisões e `shadow_results.jsonl` tem 25 resultados. `active_dev_results.jsonl` está vazio porque o gate falhou. `before_after.json` conserva baseline, histórico, nota potencial, synthetic expected score e active não executado. `confirmed_review_findings.json`, `review_counterfactuals.json`, `outside_apparent_review.json`, `api_calls_summary.json` e `promotion_gate_details.json` documentam revisão e decisão. O histórico de autorização permanece em `external_execution_status.json`.

## Validação local

Os 55 testes novos passaram, incluindo Lean real para igualdade verdadeira e falsa, prosa sem FactResult, fonte/IDs, ausência de pesos, default isolado, confiança alta/média/baixa, carry-forward preservado, max_of sem dupla contagem e falha técnica sem zero matemático.

A bateria core cobre P1–P5, PautaEngine, grounding, canonicalização, checkers/Lean, integration, evidence IDs e os controles dos experimentos anteriores. A seleção ITA cobre semântica global, integridade de transcrição aceita, ITA Q4 level2 e F2Q6 level1; não foi repetida a suíte ITA integral de longa duração, pois a alteração compartilhada é a política opt-in do PautaEngine e não o pipeline ITA.

**Resultados:** core **1428 passed** (433,77 s); ITA selecionado **85 passed** (151,62 s); suíte híbrida final **55 passed** (21,94 s). São **1515 testes únicos aprovados**, com repetição intencional dos testes híbridos para validar o código final. Não houve falha nem skip nessas execuções.

Resultados completos e controles são registrados em `regression_summary.json`, `false_credit_controls.json` e nos XML/logs por suíte. A revisão live identificou as falhas acima; regressões aprovadas não comprovam a qualidade de novos julgamentos do modelo.

## Preservação e próximo passo

`preservation_check.json` confirma que o único arquivo pré-existente alterado é `rubric/pauta/engine.py`, para a política opt-in descrita. Os novos componentes são aditivos. Pautas/pontos, producers, TeacherDecision, UI, OCR/HMER, artefatos anteriores e synthetic labels não foram alterados. Nenhum commit foi criado.

Não executar active nem HOLDOUT com esta versão. O runner verifica os hashes congelados e exige gate aprovado para active. Uma próxima iteração deve corrigir a atribuição semântica e a distinção entre verificador inaplicável e extração infiel, os marcadores/contextos de itens e as invariantes do protocolo. A falha pré-existente de truncamento auditado merece correção própria e regressão. Essas mudanças exigem um novo congelamento e nova medição DEV; não devem ser retroaplicadas aos resultados deste experimento. Comparação de modelos permanece fora deste estudo.
