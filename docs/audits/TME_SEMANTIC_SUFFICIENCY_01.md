# TME_SEMANTIC_SUFFICIENCY_01

Decisão: **NO_GO_FOR_HOLDOUT**. ACTIVE DEV não executado. Nenhuma das 100 HOLDOUT foi aberta, lida ou enviada. Nenhuma nota persistida foi alterada.

O gate independente eliminou **6/15 falsos créditos** e **2/6 vínculos incorretos** conhecidos. Restam 9 falsos créditos e 4 vínculos incorretos. A revisão também confirmou 3 novos falsos créditos e 2 novas atribuições incorretas entre os 52 suportes novos. A cobertura de 264/409 (64,5%) não compensa essa falta de especificidade.

## Escopo e congelamento

Foram usadas exclusivamente as mesmas 25 DEV do Hybrid01. Os 543 julgamentos válidos do primeiro avaliador, dos quais 471 positivos, foram reutilizados dos artefatos congelados; não houve nova chamada ao primeiro avaliador. As quatro respostas previamente inválidas continuaram inválidas. Resultados determinísticos/formais da auditoria seletiva anterior foram reutilizados para as mesmas fontes e candidatos, com hashes verificados; não foram reconstruídos por inferência semântica.

Antes da execução externa, foram congelados código, prompt, configuração, 21 fixtures de erros conhecidos, payloads, schemas, fontes e resultados anteriores em `experiment_freeze.json`. Não houve ajuste de código, prompt, categorias ou parâmetros depois de observar as respostas. A autorização explícita do usuário cobriu as 20 chamadas do novo gate; a tentativa anterior barrada pela revisão automática não executou chamadas.

Modelo único: `gpt-4o-mini-2024-07-18`; temperatura 0; `store=false`; timeout 180 segundos; limite de saída 16.000 tokens; zero retries. Foram realizadas exatamente 20 chamadas: 19 respostas válidas e uma inválida, sem reparo ou repetição. Cinco casos dispensaram chamada: quatro sem primeiro julgamento válido e um com todos os positivos barrados localmente. Consumo registrado: 238.312 tokens de entrada e 27.776 de saída. Não houve comparação de modelos.

## Implementação

Arquivos novos:

- `student_claims/sufficiency_requirements.py`: declara o requisito sem pontos de todas as 146 obrigações, separado das pautas.
- `student_claims/sufficiency_context.py`: delimitação determinística dos itens, trechos literais autorizados e contexto de revisão/rejeição.
- `student_claims/semantic_sufficiency.py`: `SemanticSufficiencyGate`, contrato estrito, chamada independente e validação da resposta.
- `tme/sufficiency_experiment.py`: reconciliação experimental com precedência da auditoria existente e avaliação potencial pelo mesmo PautaEngine.
- `scripts/evaluation/evaluate_tme_semantic_sufficiency.py`: preparação, congelamento, shadow, replay local, gate DEV e ativação condicionada.
- `tests/test_semantic_sufficiency.py`, `tests/test_sufficiency_dev_regressions.py` e fixture DEV correspondente.

Os tipos são `FINAL_ANSWER`, `FACT`, `INTERMEDIATE_STEP`, `JUSTIFICATION`, `COMPLETE_METHOD`, `ENUMERATION` e `STRATEGY`. Eles descrevem evidência exigida, sem peso ou pontuação. Conclusão isolada não comprova justificativa; nome do método não comprova seu desenvolvimento; enumeração exige conferir completude e multiplicidades.

O payload contém enunciado, obrigação sem pesos, tipo de requisito, IDs selecionados, seus trechos exatos, contexto local e revisões posteriores. O enunciado fornece os objetos matemáticos; o contexto pode interpretar ou vetar evidência, mas não completar uma prova ausente. Não contém rationale, confiança ou extrações do primeiro avaliador, resolução oficial, notas, rótulos sintéticos ou TeacherDecision.

A resposta possui exclusivamente `obligation_id`, `sufficiency`, `evidence_ids`, `reason_code` e `concise_rationale`, dentro de um mapa fechado de obrigações. IDs devem existir e pertencer à seleção. Um positivo não pode retirar IDs selecionados para eliminar uma evidência problemática. Schema inválido invalida o lote inteiro: foi o caso de P2_10, por `positive_changed_selected_evidence`. Seus 23 alvos receberam incerteza técnica; dois resultados já auditados permaneceram protegidos.

### Vínculo e contexto

As unidades mantêm seus IDs originais. Quando uma unidade abrange vários itens, são registrados `multiple_items`, os intervalos literais e o item de cada parte; somente as partes autorizadas seguem como evidência positiva ao gate. O parser distingue marcadores de itens de parênteses algébricos e referências como “pelo item (b)”. Cabeçalho sozinho não satisfaz obrigação.

A regra padrão impede evidência de outro item. Exceções registram a autorização por referência textual explícita ou obrigação declaradamente cross-item. Carry-forward continua dependente da auditoria e do vínculo preexistentes. Item indeterminado não recebe confiança alta automaticamente. Contextos de negação, hipótese, citação, tentativa abandonada e correção posterior são verificados, inclusive além do item selecionado.

`SEMANTIC_SUPPORTED` exige primeiro julgamento positivo, IDs reais, contexto válido, vínculo válido e suficiência positiva, sem refutação automática correspondente. Insuficiência não vira refutação matemática; incerteza permanece indeterminada; contradição sem prova automática vira conflito. Resultados automáticos estabelecidos têm precedência. Não foi criado scorer: os pontos potenciais e seu contrafactual semântico usam o mesmo PautaEngine e a política experimental já existente no Hybrid01.

## Resultados shadow

| Medida | Resultado |
|---|---:|
| Candidatos positivos do primeiro avaliador | 471 |
| Bloqueios locais anteriores à chamada | 25 |
| Obrigações enviadas ao gate | 446 |
| Sufficient | 330 |
| Insufficient | 118 (25 locais + 93 do modelo) |
| Uncertain | 23 (lote tecnicamente inválido) |
| Contradictory | 0 |
| DETERMINISTIC_VERIFIED | 35 |
| FORMAL_VERIFIED | 6 |
| SEMANTIC_SUPPORTED | 293 |
| SEMANTIC_NOT_SUPPORTED | 182 |
| FORMAL_REFUTED | 1 |
| CONFLICT | 1 |
| INDETERMINATE, como tier | 6 |
| TECHNICAL_ERROR | 206 |
| Suportes reconciliados totais | 334 |
| Suportes dentro das 409 obrigações aparentemente satisfeitas | 264 |
| Suportes fora desse conjunto | 70 |
| Estado final indeterminate | 188 |
| Estado final refuted | 2 |
| Casos needs_review | 18/25 |

Os 330 julgamentos suficientes não equivalem a 330 novos suportes semânticos: há resultados auditados que têm precedência e obrigações de carry-forward que continuam exigindo vínculo auditado. Dos 206 erros técnicos, 185 decorrem dos quatro primeiros lotes inválidos herdados e 21 do novo lote inválido, após preservar os resultados auditados.

Todos os 41 suportes automáticos e as duas refutações anteriores foram preservados. Uma refutação aparece no tier CONFLICT por discordância do candidato semântico. O conhecido conflito de extração em P1_12, relacionado ao trecho `a−c=594÷99=6`, permanece herdado; este experimento não alterou o checker nem o corrige por interpretação semântica.

### Cobertura comparável

O numerador comparável é a interseção entre suporte reconciliado e as mesmas 409 obrigações aparentemente satisfeitas, não o total de 334 suportes.

| Problema | Denominador | Hybrid01 | Sufficiency01 | Variação |
|---|---:|---:|---:|---:|
| P1 | 77 | 62 | 72 | +10 |
| P2 | 91 | 90 | 70 | −20 |
| P3 | 50 | 27 | 27 | 0 |
| P4 | 97 | 87 | 73 | −14 |
| P5 | 94 | 2 | 22 | +20 |
| Total | 409 | 268 (65,5%) | 264 (64,5%) | −4 |

Há ganho em **2/5 problemas frente ao Hybrid01**, abaixo de 4/5. A política congelada do runner também mantém o comparador histórico anterior ao Hybrid01, com ganho em 5/5; esse resultado não deve ser confundido com melhora frente ao híbrido anterior. Ambos são registrados. A conclusão NO_GO independe dessa distinção, pois os controles de especificidade falharam.

Pontos conhecidos potenciais: 308; contrafactual apenas auditado: 49; incremento exclusivamente semântico: 259 (84,1% dos pontos conhecidos). Esses valores são diagnósticos shadow, não notas reais nem prova de correção.

## Erros conhecidos e revisão de novos suportes

As 21 fixtures DEV classificam os erros por resultado escrito incorreto, igualdade inválida, ramo de método ausente, nome do método sem passos, cabeçalho isolado e evidência localizada fora da seleção. Não foram criadas regex por solução.

| Controle | Exigido | Eliminado | Remanescente |
|---|---:|---:|---:|
| Falso crédito conhecido | 15/15 | 6/15 | 9/15 (60%) |
| Vínculo incorreto conhecido | 6/6 | 2/6 | 4/6 (66,7%) |

Essas taxas se referem aos erros conhecidos, não à precisão global. Exemplos persistentes:

- P1_06: texto escreve `3*10=20`, mas o gate valida a obrigação de total 30.
- P1_13: valida total 30 a partir de conclusão 27 e chega a mencionar 27 como conclusão correta no rationale.
- P2_01/P2_18: atribui realizações de centros a trechos selecionados que não apresentam as configurações necessárias.
- P4_16: aceita o conjunto de soluções apesar de faltar uma raiz escrita.
- P4_21: aceita exclusão de uma hipótese pelo simples nome do método e conclusões.

A revisão abrangeu os 21 controles conhecidos, cinco casos completos (P1_06, P2_01, P3_02, P4_13, P5_09) e os 52 suportes novos. Não é certificação exaustiva de precisão. Foram confirmados:

| Caso/obrigação | Novo problema |
|---|---|
| P4_19 `c.exclude_12` | Justificativa aceita apesar da expansão falsa `(6−x)^2=36−x^2`. |
| P5_22 `c.no_ones` | Transformação válida para n≥5 usada indevidamente para excluir 1. |
| P5_22 `d.uniqueness` | Listagem de duas formas tratada como prova de exclusividade. |
| P5_22 `a.domain` | Exclusão de parcelas ≥5 atribuída a trecho sem esse argumento. |
| P5_09 `c.twos_count` | Resto 4 tratado como evidência de dois 2; um único 4 também é compatível. |

Corrigir fronteiras de itens restaurou evidências legítimas, mas também expôs erros que o parser anterior barrava acidentalmente. A ausência de rationale anterior e resolução oficial não impediu o mesmo modelo de completar provas e corrigir mentalmente respostas erradas. Nenhuma resposta recebeu `contradictory`, apesar de contradições escritas nesses controles.

## Métricas sintéticas auxiliares

Comparação pareada nos 20 casos com nota potencial numérica nas duas versões; os demais não foram imputados como zero. Escala original das pautas, sem normalização adicional.

| Métrica | Hybrid01 | Sufficiency01 |
|---|---:|---:|
| MAE | 4,90 | 3,05 |
| Bias | −2,00 | −1,65 |
| Exact | 4/20 | 5/20 |
| ±1 | 7/20 | 9/20 |
| ±2 | 9/20 | 13/20 |

A melhora dessas métricas não autoriza promoção diante dos falsos créditos e vínculos incorretos.

## Testes e preservação

Os 36 testes novos de protocolo e contexto passaram, incluindo schema, independência, seleção literal, fronteiras, exceções, negação/hipótese/rejeição/citação, precedência automática e carry-forward. A validação estrutural das 21 fixtures também passou. Depois da execução real, os 21 testes de eliminação dos erros conhecidos tiveram 8 passes e **13 falhas**, preservadas como resultado do experimento, sem flexibilização das expectativas.

A bateria geral de 26 arquivos terminou com **1.550 passes e uma falha** em `test_common_catalog_preserves_real_pipeline_credit_and_attribution[True]`: a execução offline retornou nota nula com `ADJUDICATOR_UNAVAILABLE`, em vez de 10. Os testes removem a chave da API por fixture; não houve chamada externa nessa bateria. A repetição isolada do mesmo teste passou em 75,46 segundos, com nota 10 e verificações formais aprovadas. A causa da falha inicial não foi estabelecida. Não se declara a bateria combinada inteiramente verde: `regression_summary.json` mantém `passed=false` conservadoramente. A falha original permanece em `regression.xml` e `regression.log`, e a repetição em `regression_isolated.xml`.

`preservation_before.json` e `preservation_after.json` comparam os hashes dos arquivos preexistentes e do experimento Hybrid01. A alteração em `rubric/pauta/engine.py` que já aparecia no Git antes desta tarefa pertence à tarefa anterior: seu conteúdo foi preservado nesta tarefa. Pautas, pesos, checkers, Lean, carry-forward, TeacherDecision, UI e OCR/HMER permaneceram inalterados. Sem commit automático.

## Artefatos e reprodução

Diretório: `artifacts/evaluations/tme_semantic_sufficiency_01/`.

Os oito artefatos solicitados estão presentes: `semantic_candidates.jsonl`, `sufficiency_decisions.jsonl`, `item_linkage.jsonl`, `shadow_results.jsonl`, `false_credit_regressions.json`, `coverage_before_after.json`, `summary_by_problem.json`, `GO_NO_GO.json`.

Payloads, schemas, respostas brutas, decisões, exceções de item, trechos literais, hashes e revisão manual permanecem disponíveis no mesmo diretório. `active_dev_results.jsonl` está vazio. Os rótulos sintéticos só entram na análise auxiliar posterior.

O modo `replay` recompõe o shadow local a partir das respostas já gravadas, verifica o congelamento e não chama a API. Em seguida, o modo `gate` aplica os controles de promoção e a revisão registrada. Não executar novamente `shadow`; ele recusa repetir chamadas já presentes. O modo `activate` permanece bloqueado pela decisão negativa.

A camada foi implementada e avaliada, mas não alcançou especificidade suficiente. **NO_GO_FOR_HOLDOUT**; manter ACTIVE DEV desativado e HOLDOUT fechado.
