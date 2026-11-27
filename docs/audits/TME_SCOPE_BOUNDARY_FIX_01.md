# TME_SCOPE_BOUNDARY_FIX_01

**Decisão: `SCOPE_FIX_GO`.** A fronteira estrutural de P5_02 foi corrigida; o replay Sol remove o vínculo indevido de `c.four_product`, reduz `c.normal_counts` de **2 para 0 pontos** e a nota shadow de **11 para 9**. Nenhum novo apoio, falso crédito ou vínculo incorreto foi introduzido; nenhum apoio legítimo anterior foi perdido.

**Zero chamadas externas. HOLDOUT processadas: 0/100. Sem commit. Notas persistidas e artefatos LIVE originais não modificados.**

Testes: **893 aprovados, 13 falhas históricas preexistentes, 0 falhas novas, 0 skips**, em 906 testes da suíte ampla. As mesmas 13 falhas foram reproduzidas com o código congelado anterior. O GO é da correção de escopo, não uma afirmação de que toda a suíte histórica está verde.

## Causa raiz e implementação mínima

O detector aceitava um marcador precedido por qualquer final de frase parcial `em` ou `para`. Assim, dentro do item (d), “Os dois 2's que aparecem em (c)” abria uma falsa seção (c), relabelando a parte final de E016 e as unidades seguintes.

A única alteração de comportamento no código do produto está em [sufficiency_context.py](/Users/LinMarcolino/Documents/confia-lean-auditor/app/confia_lean_auditor/student_claims/sufficiency_context.py), no reconhecimento de uma transição tópica:

```python
# Antes
r'\b(?:para|em)\s*$'
# Depois
r'(?:^|[.!?;:])\s*(?:para|em)\s*$'
```

A expressão agora exige posição de início de linha ou sentença para o prefixo de transição. Continua aceitando cabeçalhos no início de linha, marcadores estruturais inline após pontuação e transições existentes como “Em (b), … Em (c), …” e “Para (c): …”. Uma referência lexical interna, como “os valores calculados em (b)”, não altera o contexto atual. Os guardas já existentes para expressões algébricas, referências `item (x)`, cabeçalhos vazios e unidades mistas foram preservados.

Não há lista de soluções, caso especial para P5_02, números matemáticos hardcodados ou mudança em regras de crédito. A correção usa posição estrutural, não uma lista de frases proibidas. Texto sem marcador estrutural reconhecido mantém a região anterior ou a região não atribuída já prevista no sistema.

**Escopo deliberado:** o `SemanticRubricEvaluator`, seus prompts, schemas e hints lexicais de entrada não foram editados. Os hints antigos continuam sendo informação consultiva; a autorização efetiva usa `item_slices`/`link_evidence` do gate estrutural corrigido. Não houve mudança no código do `SemanticSufficiencyGate`, reconciliadores, `HybridEvidencePolicy`, `PautaEngine`, pautas, carry-forward, checkers ou Lean. Os 232 demais arquivos protegidos do experimento continuaram com seus hashes originais. O contrato/schema é constante; os candidatos e metadados derivados da fonte podem mudar por consequência da fronteira corrigida.

- HEAD de base, sem novo commit: `d31652db0b81ef27367fad6f1e7d5ec686b77c4a`.
- SHA da rodada LIVE usada no replay: `ea3ae12b0c62f7f266a1cd91da795e32dc43f326`.
- Hash anterior do detector: `400b2ba6cdfc6d227add58e82da14dfb2d691242182dd69814b13d2cd3cad33d`.
- Hash corrigido: `47881c3029e0d7ad77c32de7795911b59129cbc1d3984df2d7af8fb842f91c03`.

## Testes estruturais e preservação

[Testes de fronteira](/Users/LinMarcolino/Documents/confia-lean-auditor/tests/test_scope_boundary.py) cobre `(a)`–`(d)`, maiúsculas, espaços, tabs, linhas vazias, CRLF, marcadores inline e transições tópicas já suportadas. Os negativos incluem `em (c)`, `como em (c)`, `resultado de (c)`, `pelo item (c)`, `usando (c)`, `de (d)` e referências em prosa matemática. Verifica também a manutenção da seção nas unidades posteriores, a próxima seção legítima e a autorização textual explícita entre itens sem relabelar a origem.

Há testes de rejeição de evidência de outro item para cada problema P1–P5, usando seus requisitos reais. O teste específico de P5_02 lê apenas a fonte congelada existente, confere todos os IDs/textos e demonstra E016–E018 pertencendo a (d).

[Testes de replay](/Users/LinMarcolino/Documents/confia-lean-auditor/tests/test_scope_boundary_replay.py) verifica o crédito removido, os apoios legítimos de (d) preservados, a ausência de promoção quando falta gate remoto, a rejeição de reutilização quando um trecho físico foi removido/deslocado/alterado e os três pipelines Sol que já falhavam.

## Replay DEV25 sem API

O script [replay_tme_scope_boundary.py](/Users/LinMarcolino/Documents/confia-lean-auditor/scripts/evaluation/replay_tme_scope_boundary.py) usa exclusivamente os 25 IDs autorizados de `tme_model_ablation_dev25_live_01/preflight.json`, os textos congelados, ambos os JSONL, as respostas brutas, as auditorias previamente calculadas e a revisão manual já registrada. Não seleciona outra divisão de dados, não chama providers e não reexecuta checkers/Lean para avaliar DEV. Acesso de rede fica bloqueado durante o comando.

Antes de aplicar a fronteira corrigida, a reconciliação/pauta anterior foi reconstruída sobre os dados originais e conferida **exatamente nos 50 registros**, incluindo a evidência e a avaliação. Isso valida que a comparação não mistura outra implementação de scoring ou outro resultado de auditoria.

Protocolo conservador do replay:

1. Validar cada resposta remota existente contra **seu payload original**. Uma resposta originalmente inválida não é consertada nem parcialmente aproveitada.
2. Refazer apenas fronteiras, vínculos e vetos locais com a implementação corrigida.
3. Reutilizar uma decisão remota armazenada somente se os mesmos IDs e **todos os spans físicos de evidência anteriormente julgados continuarem autorizados**, sem trocar texto ou offsets. O contexto passa novamente pelo gate local. Um prefixo recuperado pode ampliar a visão, mas conteúdo novo não pode substituir um span antigo perdido.
4. Para obrigações antes bloqueadas localmente, sem resposta remota armazenada, manter `uncertain/indeterminate`. Corrigir a seção não inventa suficiência matemática. Falhas remotas existentes continuam como `provider_error`.
5. Reconciliar com as auditorias congeladas e aplicar o mesmo `HybridEvidencePolicy`/`PautaEngine` em shadow.

Este é um **replay condicionado aos julgamentos já produzidos**, não uma nova avaliação do modelo nem previsão de como ele responderia ao contexto corrigido. A revisão matemática, incluindo incertezas e anotações anteriores, não foi relabelada.

Comando:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=app .venv/bin/python scripts/evaluation/replay_tme_scope_boundary.py
```

### Diferenças antes/depois

**3 evidence units únicas tiveram metadados de seção alterados**, todas em P5_02: E016, E017 e E018. IDs, texto literal, offsets, tipo e context_ids permaneceram idênticos em todas as 25 soluções. Como a fonte é comum aos braços, não se contam as mesmas três unidades duas vezes.

| Métrica | Mini | Sol |
|---|---:|---:|
| Obrigações avaliadas | 730 | 730 |
| Mudança de estado da obrigação | 10 | 1 |
| Mudança de estado/tier/motivo | 10 | 7 |
| Mudança no vínculo/contexto registrado | 20 | 24 |
| Scores diferentes | 0 | 1 |
| Falsos créditos matemáticos removidos¹ | 0 | 0 |
| Vínculos incorretos removidos | 0 | 1 |
| Apoios legítimos perdidos | 0 | 0 |
| Novos apoios concedidos | 0 | 0 |
| Novos falsos créditos | 0 | 0 |
| Novos vínculos incorretos | 0 | 0 |

¹ Na taxonomia da revisão anterior, P5_02/c.four_product era **vínculo incorreto**, não falso crédito matemático: existe uma igualdade apropriada em E014 do item (c), mas ela não foi selecionada. Portanto, o total estrito de falsos créditos matemáticos removidos é **0**; foi removido **1 apoio indevido por vínculo**, que habilitava um bloco de **2 pontos**. Não se mudou a classificação antiga para inflar a métrica.

Ao todo, 11 estados de obrigação mudaram nos 1.460 pares braço–solução–obrigação. Considerando também tier/motivo, são 17 registros alterados, referentes a 11 obrigações únicas. Há 44 registros de vínculo/contexto alterados, referentes a 26 obrigações únicas. Todas essas mudanças estão em P5_02; mudança de metadado não implica mudança de decisão ou nota.

No Mini, 10 obrigações de (d) deixam o bloqueio de seção e passam de `indeterminate` para `technical_error`, porque o gate histórico desse caso era inválido. A nota continua `null`; não há crédito novo ou perdido. No Sol, apenas `c.four_product` muda de apoio para indeterminação. Seis outras obrigações de (d) permanecem indeterminadas, agora por ausência de uma decisão remota reutilizável, em vez de seção incorreta.

Os **48 registros fora de P5_02 preservam exatamente a reconciliação e a avaliação completas**. São **49 scores iguais e 1 diferente**, contando `null` como indisponível, sem imputar zero. Os apoios legítimos confirmados permanecem **266 no Mini e 334 no Sol**. O total de apoios do Sol cai de 349 para 348 por remoção do vínculo indevido.

Não surgem novos apoios. Nos dois apoios positivos com visão ampliada (`d.four_sum` e `d.four_product`), todos os spans originais permanecem autorizados, na mesma unidade e posição, e o gate local atual passa. A revisão anterior já os classificava como legítimos. Essa verificação sustenta o zero de novos vínculos incorretos; não se presumiu que qualquer mudança de metadado fosse automaticamente segura.

## P5_02 em detalhe

| Etapa | Antes | Depois |
|---|---|---|
| E016 | `multiple_items=true`, fatias (d)/(c) | somente (d), texto integral preservado |
| E017/E018 | atribuídos a (c) | atribuídos a (d) |
| Seleção Sol para c.four_product | E013/E016 | E013/E016, sem trocar seleção |
| Autorização de E016 para (c) | aceita fatia incorretamente rotulada (c) | `wrong_item`; fonte (d) não autorizada |
| Reconciliação de c.four_product | `supported / SEMANTIC_SUPPORTED` | `indeterminate / SEMANTIC_NOT_SUPPORTED`, `invalid_item_linkage` |
| c.normal_counts | 2/2 pontos | 0/2 pontos, pendente de revisão |
| Item (c) | 4/6 pontos | 2/6 pontos |
| Nota shadow Sol | 11/20 | 9/20 |
| needs_review | true | true |
| d.four_sum e d.four_product | supported | supported |

Os 2 pontos pertencem ao bloco `all_of`, não à obrigação isolada. A correção remove o crédito concedido por aquela cadeia de autorização; não inventa uma nova seleção de E014 para recuperar a nota. Os resultados originais LIVE continuam intactos em seu diretório; os resultados acima estão apenas nos novos artefatos de replay.

## Falhas conhecidas preservadas

- **P1_12:** resposta positiva sem E011 continua rejeitada por `positive_changed_selected_evidence`; nenhuma correção silenciosa.
- **P4_19:** remoções de IDs nas decisões positivas continuam rejeitadas pelo mesmo contrato.
- **P2_10:** permanece `APITimeoutError`; não há retry especial, alteração de timeout ou nova chamada.

Nos três casos Sol, o replay mantém a avaliação original, `score=null`, `needs_review=true` e nenhum apoio `SEMANTIC_SUPPORTED`. Auditorias determinísticas independentes já estabelecidas são preservadas. Configurações de transporte, retries, modelo e reasoning não mudaram.

## Regressão e testes executados

| Arquivo de testes | Aprovados | Falhas |
|---|---:|---:|
| `test_scope_boundary` | 33 | 0 |
| `test_scope_boundary_replay` | 5 | 0 |
| `test_evidence_id_semantic` | 53 | 0 |
| `test_tme_hybrid_grader` | 55 | 0 |
| `test_semantic_sufficiency` | 36 | 0 |
| `test_tme_model_ablation` | 22 | 0 |
| `test_tme_model_compat` | 8 | 0 |
| `test_pauta_engine` | 100 | 0 |
| `test_tme2_p1_pauta_bridge` | 74 | 0 |
| `test_tme2_p2_pauta_bridge` | 125 | 0 |
| `test_tme2_p3_pauta_bridge` | 70 | 0 |
| `test_tme2_p4_pauta_bridge` | 89 | 0 |
| `test_tme2_p5_pauta_bridge` | 130 | 0 |
| `test_obligation_semantic` | 34 | 0 |
| `test_semantic_claims` | 50 | 0 |
| `test_sufficiency_dev_regressions` | 9 | 13 |

**Total da execução ampla: 893 aprovados, 13 falhas preexistentes, 0 skips, em 185,12 s.** Os 38 testes novos passaram. A execução bloqueou rede e registrou **0 tentativas de rede / 0 chamadas externas**. Provas auxiliares dos testes foram direcionadas ao diretório novo `test_proofs`; não houve reexecução de auditoria sobre os 25 textos DEV.

Os 5 testes de replay também passaram novamente após a conferência de preservação literal dos fallbacks; essa repetição não foi somada ao total de 893 testes da suíte ampla.

### As 13 falhas históricas

O arquivo `test_sufficiency_dev_regressions.py` lê resultados antigos em `artifacts/evaluations/tme_semantic_sufficiency_01/shadow/` e afirma que certos erros já deveriam estar eliminados. Ele não executa o detector corrigido nem o replay desta tarefa. Foi executado novamente usando `PYTHONPATH` do snapshot anterior; apresentou **as mesmas 13 falhas e 9 aprovações**. Nenhum resultado histórico foi alterado para fazê-lo passar.

- `TME2026P1_06:d.total_thirty`
- `TME2026P1_13:d.middle_choices`
- `TME2026P1_13:d.total_thirty`
- `TME2026P2_01:b.realizable_5`
- `TME2026P2_01:b.realizable_9`
- `TME2026P2_01:c.counting_product`
- `TME2026P2_01:c.pair_orientations`
- `TME2026P2_08:c.counting_product`
- `TME2026P2_08:c.pair_orientations`
- `TME2026P2_18:b.realizable_5`
- `TME2026P2_18:b.realizable_9`
- `TME2026P4_16:c.x_candidates`
- `TME2026P4_21:c.exclude_12`

Há **0 falhas novas** na comparação de IDs de testes. Isso não elimina a dívida da suíte histórica: o resultado integral permanece com exit code 1. O GO da correção é sustentado pelos testes estruturais/matemáticos atuais, pela reprodução dos 50 baselines e pelo replay sem regressão material, não por ocultar essas falhas.

Artefatos: [resumo do replay](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_scope_boundary_fix_01/summary.json), [mudanças de unidades](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_scope_boundary_fix_01/unit_changes.json), [mudanças de obrigações](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_scope_boundary_fix_01/obligation_changes.json), [scores antes/depois](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_scope_boundary_fix_01/score_comparison.json), [log dos testes](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_scope_boundary_fix_01/tests.log), [comparação das falhas históricas](/Users/LinMarcolino/Documents/confia-lean-auditor/artifacts/evaluations/tme_scope_boundary_fix_01/test_comparison.json) e `replay_a.jsonl`/`replay_b.jsonl` no mesmo diretório.

## Decisão e limites

**`SCOPE_FIX_GO`**: P5_02 corrigido; 2 pontos retirados no replay Sol; zero novos falsos créditos, zero novos vínculos incorretos e zero perda de apoio legítimo; comportamento matemático fora do defeito estável. A confirmação é local, sobre testes e outputs congelados. Não equivale a nova avaliação LIVE nem remove a necessidade de julgar futuramente os gates antes bloqueados.

**Zero chamadas externas. HOLDOUT processadas: 0/100. Nenhum commit automático. Nenhuma nota persistida alterada.**
