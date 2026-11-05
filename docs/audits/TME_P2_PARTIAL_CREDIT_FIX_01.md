# TME P2 — correção mínima do crédito final — 01

Data: 2026-11-05. Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2`. Branch: `experiment/tme-semantic-formal-p2`. Base/HEAD preservado: **`05c75f4c64ddfec288c96e3519dca01a94e6464f`**.

**c.total agora admite valor final determinístico ou igualdade formal realmente verificada, conforme a representação escrita.** Os três checkers compostos permanecem intactos. Em teste local com extração controlada das três linhas de `p2_dev_partial`, o modo semântico recuperou **somente 1 ponto**, enquanto TME_CURRENT continuou em **5**. Nenhum rerun/piloto real foi executado.

## 1. Mudança implementada

A correção está exclusivamente no adaptador experimental P2, sem alterar o SemanticExtractor, seus prompts/schemas, o runner, a pauta, pesos, datasets ou checkers matemáticos:

- **registry.py:** `allowed_routes` explicita as rotas de cada obrigação. Só c.total recebe duas: FORMAL e DETERMINISTIC. `route_for_expression` usa a gramática já existente para distinguir valor fechado sem igualdade de igualdade escrita; não decide a verdade matemática. O campo de capacidade/default `route` continua FORMAL, preservando a informação que o extractor já recebe; a rota efetiva é decidida localmente.
- **mapper.py:** após validar binding, contexto, subject e representação, seleciona a rota efetiva por esse contrato; conserva a sugestão do modelo e registra override quando necessário.
- **verification.py:** reutiliza `P2Checks.counting('total',384)` e seus resultados. Uma expressão fechada sem igualdade pode retornar DETERMINISTIC_VERIFIED; uma igualdade mantém a rota FORMAL e depende do checker Lean original. Para c.total, registra também `formal_status` e `verification_kind`.
- **engine.py:** o award gate aceita a allowlist, exige coincidência com a rota aprovada para aquela evidence e registra a origem/rota realmente usada. Reconciliação, política de falsidade, seleção de regras, pesos e ScoreClosurePolicy não foram alterados.

Não há novo checker de aritmética. A avaliação exata do valor continua sendo a do checker congelado. Não existe fallback de igualdade refutada, inconclusiva, não renderizável ou não executada para um veredito determinístico sobre a mesma igualdade.

### Exemplos de saída

| representação vinculada ao total | rota | status suficiente | diagnóstico formal | ponto final |
|---|---|---|---|---:|
| `total: 384` | DETERMINISTIC | DETERMINISTIC_VERIFIED | FORMAL_NOT_ATTEMPTED; attempted=false | 1 |
| `O total de preenchimentos é 384.` → payload literal 384 | DETERMINISTIC | DETERMINISTIC_VERIFIED | mesma ausência formal | 1 |
| `total: 24*16=384` | FORMAL | FORMAL_VERIFIED, compiled=true | execução Lean real | 1 |
| `total: 385` | DETERMINISTIC | DETERMINISTIC_FAILED | nenhuma prova inventada | 0 |
| `total: 24*16=364` | FORMAL | FORMAL_REFUTED, refutation_verified=true | negação compilada | 0 |
| valor correto + igualdade falsa | resultados distintos preservados | CONFLICTING_EVIDENCE na reconciliação | refutação permanece visível | 0 enquanto conflito não resolvido |

O caminho de valor também aceita uma expressão fechada como `384/1` ou `24*16`, sem igualdade, quando ela foi realmente escrita como total e o checker exato confirma seu valor. Isso não fornece uma prova Lean nem os 5 pontos do método direto. Uma igualdade não renderizável, como `384/1=384` pelo renderer atual, permanece na rota formal sem crédito se não houve prova; ela não é convertida silenciosamente em valor isolado.

Os resultados determinísticos de valor usam `verification_kind='written_total_value'`, `formal_status='FORMAL_NOT_ATTEMPTED'` e `formal_attempted=false`. Igualdades usam `verification_kind='written_total_equality'` e conservam os estados epistemológicos originais. Nenhuma igualdade ausente é sintetizada.

## 2. Contrato de evidência e checkers compostos

Foi criado [TME_P2_RUBRIC_EVIDENCE_CONTRACT_01.md](TME_P2_RUBRIC_EVIDENCE_CONTRACT_01.md), com as sete obrigações de c, objetivo, evidência mínima, exemplos suficientes/insuficientes, checker, rotas, status e dependências de crédito.

A solicitação atual resolve explicitamente o alcance da correção após o [diagnóstico forense](TME_P2_PARTIAL_CREDIT_FORENSIC_01.md): os dois critérios de 2 pontos continuam exigindo a relação combinatória do checker fortalecido; o ponto de conclusão aceita verificação determinística do total. Não se alterou o histórico de TME_CURRENT para fazê-lo aplicar retroativamente essa exigência.

`c.pair_permutations`, `c.pair_orientations` e `c.counting_product` continuam na rota COMPOSITE, exigindo `arithmetic`, `counting_components` e `relation`. Um rótulo pertinente torna a evidência candidata; não transforma 24/16 isolados em justificativa completa. O certificado finito, a enumeração/bijeção e `argument_relation` não foram modificados. Também não se criaram novas parcelas de pontos por valor/justificativa, nem bônus além do `max_of` existente.

## 3. Validação de p2_dev_partial

Fonte usada no teste local, sem ler/modificar o dataset para ajustar a resposta:

```text
c) pair_permutations: 24
pair_orientations: 16
total: 384
```

| obrigação | resultado observado com extração controlada | crédito |
|---|---|---:|
| c.pair_permutations | COMPOSITE_INCOMPLETE; relation=argument_not_established | 0 |
| c.pair_orientations | COMPOSITE_INCOMPLETE; relation=argument_not_established | 0 |
| c.total | DETERMINISTIC_VERIFIED; FORMAL_NOT_ATTEMPTED como diagnóstico | 1 |

A lista de créditos contém exatamente `('c.conclusion',1.0)`. O teste chama TME_CURRENT antes e depois e compara bridge e assessment completos: ambos são iguais, com score 5. O score semântico é 1.0 e permanece numérico.

**Previsão para o rerun real: 1 ponto se o extractor entregar as três evidências válidas equivalentes.** Não é resultado de uma nova execução de `gpt-6.1-sol`. O modelo ainda pode omitir/rejeitar evidência ou falhar; fallback continua explicitamente marcado e pode retornar a nota do baseline. Não houve tuning por caso/ID ou alteração do dataset antigo.

## 4. Testes executados

| seleção | total | passed | failed/errors/skipped |
|---|---:|---:|---|
| Semantic Formal P2 existente (154), checker-first determinístico (125), novos testes locais (25) | 304 | 304 | 0/0/0 |
| PautaEngine e ponte P2 originais | 225 | 225 | 0/0/0 |
| integração Lean Semantic Formal (17), checker-first (9), novos testes reais (6) | 32 | 32 | 0/0/0 |
| **total distinto nesta tarefa** | **561** | **561** | **0/0/0** |

Foram adicionados 31 testes parametrizados: 25 locais e seis reais. Um teste anterior que exigia zero para `total:384` foi atualizado para o contrato autorizado: DETERMINISTIC_VERIFIED, ausência de execução formal e 1 ponto. Não se alteraram expectativas para os checkers compostos ou o baseline.

Cobertura nova: valor correto/errado e expressões equivalentes; frase inequivocamente ligada ao total; número sem sujeito e subject inadequado; override de todas as sugestões de rota; igualdade sem execução formal sem fallback de valor; allowlist restrita a c.total; 24/16/384 isolados insuficientes nos três compostos; compostos completos preservados; caso parcial 5 versus 1; gate rejeitando mismatch entre rota de mapping e resultado; prova verdadeira; refutação; dois resultados positivos sem duplicação; conflito nas duas ordens entre valor correto e igualdade falsa; valor errado com igualdade verdadeira também conflitante; score numérico.

As regressões reexecutadas incluem os 55 casos P2 e a comparação das 19 obrigações antes preservadas no checker-first, além dos 39 casos textuais de TME_CURRENT do adaptador. Esta é a seleção desta correção, não uma alegação de reexecução integral dos 1.373 testes da etapa anterior.

Comandos executados, no worktree P2 e com o Python `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/app"
export CONFIA_TME_SEMANTIC_ENABLED=0
P2_FIX_PYTHON=/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python

"$P2_FIX_PYTHON" -m pytest \
  tests/test_tme_semantic_formal_p2.py tests/test_tme_p2_partial_credit_fix.py \
  tests/test_tme_p2_checker_first.py \
  -q -p no:cacheprovider --basetemp=/private/tmp/p2-partial-fix/unit \
  --junitxml=/private/tmp/p2-partial-fix/unit.xml

"$P2_FIX_PYTHON" -m pytest tests/test_pauta_engine.py tests/test_tme2_p2_pauta_bridge.py \
  -q -p no:cacheprovider --basetemp=/private/tmp/p2-partial-fix/regression \
  --junitxml=/private/tmp/p2-partial-fix/regression.xml

"$P2_FIX_PYTHON" -m pytest \
  tests/test_tme_semantic_formal_p2_lean.py tests/test_tme_p2_partial_credit_fix_lean.py \
  tests/test_tme_p2_checker_first_lean.py \
  -q -s -p no:cacheprovider --basetemp=/private/tmp/p2-partial-fix/lean \
  --junitxml=/private/tmp/p2-partial-fix/lean.xml
```

Os providers dos testes são controlados; não houve chamada real ao extractor. Os processos Lean dos casos formais são reais, sem mock do compilador/stdout ou do resultado. Os controles anteriores de tática inadequada continuam reais e separados das provas de produção.

## 5. Lean real e conflitos

Lean **4.28.0**; Mathlib **v4.28.0**, revisão `8f9d9cff6bd728b17a24e163c9402775d9e6a365`. Toolchain e manifest preservados. Nenhum novo teorema/checker de produção foi criado; os testes executam as proposições do checker existente.

Nos seis testes novos reais:

- `24*16=384`: FORMAL_VERIFIED; `compiled=true`; score 1.
- `24*16=364`: FORMAL_REFUTED; `refutation_verified=true`; score 0.
- `384` + `24*16=384`: ambas as verificações preservadas, sem conflito, uma única folha de 1 ponto.
- `384` + `24*16=364`, nas duas ordens: DETERMINISTIC_VERIFIED e FORMAL_REFUTED preservados; CONFLICTING_EVIDENCE não resolvido, revisão recomendada, score 0.
- `385` + `24*16=384`: conflito entre falsidade determinística e prova da igualdade; score 0, sem escolher silenciosamente o resultado positivo.

O valor determinístico não sobrepõe refutação. Prova inconclusiva, não tentativa e erro formal continuam distintos nos testes anteriores reexecutados. O componente de relação dos compostos continua capaz de ficar incompleto mesmo com aritmética correta.

Os recibos JSON dos seis casos novos, arquivos Lean gerados, logs/JUnit e o resultado local de p2_dev_partial estão em `artifacts/evaluations/tme_p2_partial_credit_fix_01/`. Os artefatos são ignorados pelo Git e identificam hashes dos arquivos/configuração usados. Não são resultados do rerun DEV.

## 6. Preservação e arquivos

O snapshot inicial monitorou 567 arquivos preexistentes. Somente cinco mudaram: os quatro módulos de adaptação enumerados na seção 1 e o teste de integração cujo contrato anterior foi revogado. Os **562 restantes** permaneceram com os mesmos hashes, incluindo SemanticExtractor, checkers matemáticos originais/fortalecidos, pauta, PautaEngine, runner e datasets.

Hashes SHA-256 dos inputs DEV preservados:

```text
dev_sources.json  1ab444dc90e3fff0a535cc71e5c1e92304348cee9245bf212a41baef85a43158
dev_ids.json      e16dec89186d295b150bbf68b2bed1c1bc1f09961bf47344324e23ecdacf806c
```

Novos arquivos da tarefa:

- `tests/test_tme_p2_partial_credit_fix.py`
- `tests/test_tme_p2_partial_credit_fix_lean.py`
- `docs/audits/TME_P2_RUBRIC_EVIDENCE_CONTRACT_01.md`
- `docs/audits/TME_P2_PARTIAL_CREDIT_FIX_01.md`

O relatório forense 01 já estava untracked no início e permaneceu intacto. Os relatórios de implementação/coverage anteriores permanecem como registros históricos; as regras atuais de c.total estão documentadas neste relatório e no contrato novo.

## 7. Rerun 02 preparado — não executado

Mesmo runner, mesmos oito IDs e mesmos textos. Configuração: **gpt-6.1-sol, reasoning medium**. Não se criaram novos resultados nos diretórios abaixo. O runner os criará somente quando os comandos forem explicitamente executados, exigindo diretório de saída novo.

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0 \
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python \
  scripts/evaluation/run_tme_semantic_formal_p2.py \
  --mode tme_current \
  --dataset tests/fixtures/tme_semantic_formal_p2/dev_sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_p2/dev_ids.json \
  --output-dir artifacts/evaluations/tme_p2_semantic_formal_dev_02/current \
  --model gpt-6.1-sol --reasoning-effort medium

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0 \
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python \
  scripts/evaluation/run_tme_semantic_formal_p2.py \
  --mode tme_semantic_formal \
  --dataset tests/fixtures/tme_semantic_formal_p2/dev_sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_p2/dev_ids.json \
  --output-dir artifacts/evaluations/tme_p2_semantic_formal_dev_02/semantic_formal \
  --model gpt-6.1-sol --reasoning-effort medium
```

Esses comandos não foram executados. Nenhum gold ou holdout foi usado e nenhum commit foi feito.

## 8. SHA e Git

SHA preservado: **`05c75f4c64ddfec288c96e3519dca01a94e6464f`**. Índice sem alterações; nenhuma operação de stage/commit. Estado final:

```text
 M app/confia_lean_auditor/experimental/tme_semantic_formal_p2/engine.py
 M app/confia_lean_auditor/experimental/tme_semantic_formal_p2/mapper.py
 M app/confia_lean_auditor/experimental/tme_semantic_formal_p2/registry.py
 M app/confia_lean_auditor/experimental/tme_semantic_formal_p2/verification.py
 M tests/test_tme_semantic_formal_p2_lean.py
?? docs/audits/TME_P2_PARTIAL_CREDIT_FIX_01.md
?? docs/audits/TME_P2_PARTIAL_CREDIT_FORENSIC_01.md
?? docs/audits/TME_P2_RUBRIC_EVIDENCE_CONTRACT_01.md
?? tests/test_tme_p2_partial_credit_fix.py
?? tests/test_tme_p2_partial_credit_fix_lean.py
```

A correção não altera o contrato de suficiência dos compostos. Apenas distingue a verificação de um valor final permitido pela pauta da prova formal de uma igualdade efetivamente escrita.
