# Demonstração sintética TME

O seed usa o fluxo de transcrições aceitas do piloto e o motor atual, com Lean habilitado. Não chama OCR/Mathpix nem fabrica desenhos. Não altera regras matemáticas.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/evaluation/seed_tme_synthetic_demo.py --seed --audit
```

O dataset local é `datasets/solucoes_tme2026/solucoes_tme2026.jsonl`: exatamente 125 soluções únicas, 25 por problema P1–P5. A execução registra branch, SHA, estado do worktree, hashes do motor e do dataset. Para conferir um congelamento anterior, usar `--freeze-manifest caminho/engine_freeze.json`. Os resultados ficam em `artifacts/evaluations/tme_synthetic_demo_<timestamp>/`, ignorados pelo Git.

Cada solução tem um CorrectionCase com `data_origin=synthetic_demo`, `demo_seed=seed_tme_synthetic_demo.v1` e `solution_id` original. O contrato de Submission digital exige um PNG: o seed fornece apenas um envelope branco 1×1, sem traços. A transcrição aceita preserva todos os caracteres do texto. Metadados de item vêm exclusivamente de rótulos explícitos, sem deduzir itens de números, conteúdo matemático ou notas. Nenhum DiagramState é criado. A interface abre a transcrição para os casos sintéticos.

`synthetic_expected_score` fica apenas em `demo-metadata.json` e nos relatórios de avaliação. Não entra na revisão, no AuditSource nem na chamada a `audit_tme`. O auditor usa seu ID matemático derivado do conteúdo, conforme o adaptador existente; o ID original permanece no caso e nos artefatos da avaliação. As comparações são calculadas após concluir todas as tentativas de auditoria. Notas null não viram zero e ficam fora do denominador das métricas de diferença.

Para navegar localmente:

```sh
CONFIA_TME_DEMO_NO_AUTH=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m uvicorn confia_lean_auditor.main:app --app-dir app --host 127.0.0.1 --port 8000
```

- `/tme?view=queue&origin=synthetic_demo`: todas as soluções, com filtro por questão e busca por solution_id.
- `/tme?view=queue&origin=synthetic_demo&sample=selected`: amostra visual de 25 casos distintos.
- `/tme?view=queue&origin=real`: casos reais.

O avaliador padrão é `tme-demo-evaluator`, já usado pelo modo de demonstração local. `--evaluator-id` permite indicar um avaliador existente. As permissões por proprietário permanecem em vigor. A marca de aceitação indica fidelidade de importação, não conferência humana. A decisão humana continua separada.

O seed pode ser repetido e recupera importações parciais sem duplicar casos, submissões ou transcrições. Auditorias repetidas usam a idempotência do AuditService; revisões e versões diferentes do auditor não são silenciosamente substituídas. Mudanças manuais nos textos importados exigem inspeção e não são sobrescritas.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/evaluation/seed_tme_synthetic_demo.py --clean-demo
```

A limpeza valida primeiro todo o plano: identidade determinística, marca do seed, metadado, proprietário, vínculos da submissão e caminhos dos artefatos. Remove apenas casos deste seed e seus dados vinculados; não seleciona por prefixo textual, não segue links simbólicos e recusa vínculos compartilhados. Preserva os relatórios de avaliação e não remove artefatos globais do motor. Execute sem edição concorrente dos mesmos casos.

A amostra registra déficits quando uma categoria não tem cinco casos elegíveis. Completa 25 casos únicos com a marca explícita de complemento; não inventa concordâncias ou verificações formais. Alta indeterminação significa pelo menos 50% das obrigações indeterminadas/com erro técnico. Diferenças grandes são de pelo menos três pontos.

Os rótulos de referência são sintéticos e não substituem avaliação humana.
