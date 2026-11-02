# TME Semantic Understanding 01

Resultado: **NO_GO para HOLDOUT**. A implementação experimental permanece opt-in (`CONFIA_TME_SEMANTIC_ENABLED=1`, desligada por padrão). As 100 HOLDOUT não foram executadas nem seus textos inspecionados nesta tarefa. Nenhum commit foi criado.

## Baseline e separação

A árvore original tinha alterações não commitadas do benchmark anterior. Elas foram preservadas. Antes de editar fontes, foi criado um worktree limpo na branch `codex/tme-semantic-understanding-01`, SHA `30260b398dd8b5b5b3e52bb97bece37c3100a448`. `baseline_freeze.json` registra branch, SHA completo, status vazio inicial, estado original, hashes das fontes, dataset e artifacts anteriores. Os arquivos novos foram posteriormente integrados na árvore original somente após verificar ausência de sobreposição; `integration_manifest.json` registra o procedimento. A branch original permaneceu `feat/tme-dual-input`.

DEV contém cinco casos por problema. P1 contém os cinco null conhecidos (`06`, `12`, `13`, `15`, `17`) para reproduzir a regressão Unicode. Para P2–P5, a ordenação por SHA-256 de `tme-semantic-understanding-01:<id>` definiu os cinco primeiros de cada problema, sem leitura de textos/labels. As outras 100 são HOLDOUT. Isso enriquece DEV com falhas técnicas e impede tratar DEV como amostra aleatória representativa. IDs registrados nos dois diretórios solicitados.

Os 25 resultados anteriores foram reproduzidos, inclusive os cinco null, antes da correção (`baseline_reproduction.log`, `dev_baseline_results.json`). O baseline histórico de 125 casos permanece intacto: 120 notas numéricas, cinco null, 125 needs_review, MAE sintético 14,475. Seus artifacts não foram sobrescritos.

## Arquitetura e fronteiras

`collect_digital_items` mantém a extração determinística e chama o suplemento semântico depois do roteamento por item. O suplemento utiliza o modelo já configurado (`CONFIA_LLM_MODEL`, default `gpt-4o-mini`; respostas finais identificaram `gpt-4o-mini-2024-07-18`), Responses API, temperatura zero, `store=false`, schema estrito, timeout 90 s e sem retries automáticos. A forma do request segue a [documentação oficial de Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs). Prompt, schema por problema, ontologia e parâmetros possuem hashes.

O único payload de dados enviado contém `problem_id`, enunciado, solução mapeada e ontologia conceitual/tipos. Não há notas anteriores, synthetic_expected_score, pontos, pesos, decisão humana, rubrica ou status de crédito. Labels são lidos pelo avaliador apenas depois de todas as interpretações e auditorias. O secondary adjudicator não é usado.

`SemanticClaimCandidate` é transitório. Seus campos são candidate_id, claim_kind, source_text, source_start/end, normalized_payload e assertion_mode. Os objetos rejeitam campos adicionais, os campos são obrigatórios e `subject` é limitado aos conceitos do problema ou marcadores sem representação suportada. IDs locais do modelo recebem prefixo ordinal determinístico para rastreabilidade.

O adapter preserva `MathClaimRecord`, source literal, offsets, hash do texto, provenance `semantic-claims.v1`, papel contextual e forma canônica. Não existe novo scorer. Candidatos qualitativos sem representação suportada são retidos sem autoridade de verificação. Registros e FactResults persistidos continuam sendo os formatos existentes; o JSONL de candidatos é um artifact de observabilidade do experimento.

Grounding exige igualdade literal no intervalo ou localização única do mesmo trecho literal. Não se usa fuzzy matching. Offset errado com trecho repetido, texto inventado, números/signos inventados, item incorreto ou associação conceitual insuficiente ficam unresolved/não atribuíveis. Os gates existentes de contexto continuam obrigatórios, com bloqueios adicionais para atribuição a terceiros, incerteza, conflitos e conceitos mal associados. Uma probabilidade não pode ser atribuída como contagem só porque seus números aparecem no texto. Conflitos entre quantidades semânticas não são resolvidos por escolha do modelo.

Canonicalização reaproveita parsers existentes sobre uma vista de notação; ela nunca substitui o trecho original. Fórmulas completas não são inventadas, simplificadas nem completadas para produzir evidência. Apenas um subconjunto conservador de relações da ontologia possui associação textual habilitada. DiagramState continua exigindo evidência estruturada: o modelo não produz posições de diagrama.

Deduplicação preserva os registros determinísticos. Uma cache de respostas em memória, limitada a 256 entradas e vinculada a texto/configuração, evita nova interpretação durante a revalidação dos checkers. As observações também são limitadas. Falha de API/schema mantém somente os extratores determinísticos. O verificador de P1 recebeu apenas suporte para revalidar o novo formato de fonte e acessar sua expressão; suas regras matemáticas não mudaram.

**O LLM apenas interpreta; grounding continua obrigatório; Lean/checkers continuam validando; PautaEngine continua aplicando pontos.** Geometria permanece validada pelo checker geométrico determinístico. Lean prova identidades/consequências algébricas, não uma formalização da geometria inteira. Os testes demonstram afirmação semântica correta verificada por Lean e afirmação falsa refutada, sem crédito.

## Unicode

A normalização foi isolada na camada matemática. U+2212 (`−`) vira `-` somente na vista de parsing/verificação; en dash (`–`) é aceito junto a sintaxe numérica/operadores inequívoca. `prova – tentativa` e `x – y` não são reinterpretados como subtração. O texto original e seus offsets permanecem intactos. Todos os cinco null reproduzidos passaram a notas numéricas. A extração genérica também preserva o en dash matemático como parte do fragmento completo, impedindo recorte indevido da cauda da igualdade. Essa última correção não é acionada por nenhum dos 25 DEV (`final_unicode_dev_impact.json`), portanto não modifica seus resultados; recebeu regressões adicionais.

## DEV antes/depois

Foram preservadas três iterações: `dev_run_01` identificou nomes fora da ontologia e três respostas indisponíveis; `dev_run_02` restringiu os conceitos no schema e obteve 21 respostas válidas; `dev_run_03` reaplicou os gates finais às mesmas respostas salvas, sem novas chamadas. A revisão DEV detectou associações semânticas falsas nas versões intermediárias e adicionou testes/gates antes de fechar a versão final. Nenhuma regra foi derivada do HOLDOUT.

| Métrica DEV | Baseline | Só Unicode | Unicode + semântica |
|---|---:|---:|---:|
| Notas numéricas | 20 | 25 | 25 |
| Notas null | 5 | 0 | 0 |
| Obrigações supported | 20 | 24 | 43 |
| Obrigações indeterminate | 704 | 704 | 681 |
| Cobertura primária | 2.88% | 3.56% | 6.71% |
| needs_review | 25 | 25 | 25 |
| MAE sintético | 15.70 | 15.68 | 14.88 |
| Bias sintético | -15.70 | -15.68 | -14.88 |
| Exact match | 0.00% | 0.00% | 0.00% |
| ±1 | 0.00% | 0.00% | 0.00% |

Cobertura primária = obrigações supported ou refuted / 730 obrigações, excluindo technical_error e incluindo caminhos alternativos; é cobertura de decisão, não porcentagem de soluções corretas. Há 19 obrigações supported vinculadas a registros semânticos; cobertura semântica 2.60%. Os rótulos são **sintéticos, não gold humano**. MAE/agreements usam apenas notas numéricas: denominador baseline 20 e depois 25. Na comparação pareada dos mesmos 20 casos, MAE 15.70 → 15.20; não atribuir ao LLM a recuperação técnica dos cinco null.

| Problema | Supported antes → depois | Indeterminate antes → depois | MAE depois |
|---|---:|---:|---:|
| TME2026P1 | 16 → 29 | 83 → 72 | 13.60 |
| TME2026P2 | 0 → 7 | 115 → 107 | 16.00 |
| TME2026P3 | 4 → 4 | 61 → 60 | 15.40 |
| TME2026P4 | 0 → 1 | 155 → 154 | 15.60 |
| TME2026P5 | 0 → 2 | 290 → 288 | 13.80 |

Observabilidade final: 158 candidatos, 64 com status grounded após gates de representação, 76 bloqueados por contexto, 110 canonicalizados e 128 não atribuíveis. 30 FactResults referenciam registros semânticos: 19 verified e 4 refuted. Os demais não verificaram a obrigação; canonicalização/grounding isolados não concedem pontos. Há 27 FactResults exclusivamente determinísticos. Os valores verified/refuted contam FactResults, não julgamentos do LLM.

`dev_before_after.json` registra obrigações newly supported, perdidas, ainda indeterminate, notas e provenance agregado por caso. `semantic_candidates.jsonl` contém todos os candidatos/eventos finais. `dev_after_results.json` contém MathClaimRecord, FactResult, PautaEvidence e decisões completas. `semantic_evidence_trace.json` liga obrigações supported a spans literais, forma canônica, mecanismo/checker, artefato Lean quando existente e decisão do item. A comparação de newly supported contra baseline também inclui o efeito técnico de Unicode; as obrigações com provenance semântica são discriminadas separadamente.

## Diagnóstico e decisão de GO

Antes dos scores DEV, `promotion_policy.json` fixou materialidade em pelo menos 10% de redução relativa de indeterminate **e** 5 pontos percentuais de aumento da cobertura primária, comparados com normalização isolada. A versão final atingiu 3.27% de redução e 3.15 pontos percentuais de ganho. Portanto, **NO_GO**. Os controles de falso crédito passaram, os fixtures anteriores passaram e não restou atribuição falsa conhecida entre os candidatos finais admitidos na revisão DEV. Isso não é garantia de segurança sobre entradas inéditas.

Quatro casos DEV têm entrada mapeada vazia (`P3_13`, `P4_13`, `P4_19`, `P4_21`); outros apresentam perda de segmentação, como vários itens numa única linha. A integração de transcrição aceita foi preservada por restrição de escopo. O interpretador recebe somente o texto que essa integração entrega; não se alimentou uma entrada paralela com o texto completo para melhorar artificialmente o benchmark.

Outros gargalos observados: o modelo ainda omite/reformula trechos; várias enumerações e fórmulas têm representação não suportada; gates de parágrafo rejeitam conclusões junto de hipóteses/negações; relações indexadas de probabilidades exigem ligação contextual mais forte; P2 não pode ganhar evidência de diagrama inventada; P5 qualitativo carece de certificado matemático explícito em muitos casos. Os gates não foram afrouxados para perseguir o label.

Nos exemplos-chave, chamadas reais com a configuração final produziram APQR/paralelogramo e perímetro 12, bem como large_parts_are_improvable, optimal_decomposition_prefers_threes e twos_count=2, todos vinculados a trechos reais (`key_examples_final.json`). Em P4, o checker atual exige desenvolvimento escrito do perímetro para completar o caminho: a frase simples gera os candidatos e o fato geométrico, mas não os seis pontos. Um teste separado com `2*((6-x)+x)=12` explicitamente escrito percorre Lean e recebe os seis pontos pela pauta existente. Em P5, candidatos qualitativos permanecem sem autoridade; a contagem do exemplo também é bloqueada pelo gate contextual conservador. Não foram inventados passos de prova para contornar essas lacunas.

`holdout_results.jsonl` está vazio intencionalmente. `holdout_summary.json` e `holdout_by_problem.json` declaram NOT_RUN_NO_GO, sem métricas fictícias. Não há freeze/promessa de validação externa aprovado, nem inspeção individual do HOLDOUT. `disagreements.json` contém apenas diagnóstico DEV e informa que divergências HOLDOUT não foram calculadas.

## Regressões e preservação

- `regression_tests.log`: 1012 passed, 2 skipped in 361.01s (0:06:01)
- `regression_integration_ita.log`: 150 passed, 1 skipped in 660.00s (0:10:59)
- `semantic_tests.log`: 47 passed in 24.40s
- `integrated_tests.log`: 83 passed in 38.92s
- `final_unicode_regression.log`: 314 passed, 2 skipped in 129.23s (0:02:09)
- `historical_artifact_tests.log`: 3 passed in 0.42s

Os skips do worktree correspondem a três testes de artifacts históricos locais ausentes nessa cópia; esses mesmos três testes foram executados separadamente na árvore original, sem reduzir cobertura. As suítes cobrem interpretação semântica, grounding, MathClaimRecord, canonicalização, FactResult/PautaEvidence, checkers, Lean, PautaEngine, P1–P5, integração TME e regressões ITA relevantes. Os controles incluem negação, hipótese, tentativa rejeitada, citação, contradição, número incidental, grounding adulterado, multiplicidade inventada, associação conceitual falsa, falha de provider e preservação da extração determinística.

171 arquivos protegidos no worktree continuam com os hashes do baseline. PautaEngine, rubricas/pontos, carry-forward, max_of, scoring, TeacherDecision, UI, OCR/Mathpix/HMER, catálogo e integração de transcrição aceita não foram alterados por esta tarefa. `preservation_checks.json` confirma dataset e artifacts históricos intactos. As alterações de UI já existentes na árvore original pertencem à tarefa anterior.

## Reprodução

No repositório principal, após ativar seu ambiente Python:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app python -m pytest -q -p no:cacheprovider tests/test_semantic_claims.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app python scripts/evaluation/evaluate_tme_semantic_dev.py --data-root "$PWD" --output /tmp/tme-semantic-dev-replay --replay artifacts/evaluations/tme_semantic_understanding_01/dev_run_02/dev_provider_responses.json
```

O replay não usa a API, mas exige Lean/lake/Mathlib disponíveis como no benchmark. O runner é deliberadamente DEV-only e rejeita configuração de replay diferente do prompt/modelo/schema atual. Para futuras chamadas reais, omitir `--replay`; nenhuma execução HOLDOUT está implícita. O snapshot final de fontes e configuração está em `delivery_freeze.json`, sem commit automático. Esta entrega é um experimento conservador com ganho insuficiente para promoção, não uma melhoria validada de acurácia humana.
