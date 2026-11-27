# Fase 2 — proveniência ITA e limites do SPECIALIZED

Base `923bf3acbd9994af9662bcdff6b18eac1b6d4df9`; branch `codex/stabilize-specialized-pre10dez`. PR técnico independente, sem merge e sem alteração da tag científica. O diagnóstico do [PR #6](https://github.com/rmarcolinob/confia-lean-auditor/pull/6) permanece histórico.

**APROVADO COM LIMITAÇÕES** nas regressões offline executadas. Não representa validação de GPT real, gold humano, cobertura universal ou liberação para correção escolar autônoma.

## Defeito corrigido

Em F2Q1, `Assim p(x) ≡ -1+a(x-1)+bx+1 = (a+b)x-a.` continha explicitamente a forma reduzida. `_math_fragment` rejeitava o sinal `=` imediatamente anterior. A extração local, portanto, não obtinha grounding; o fallback também podia perder essa evidência quando a recuperação lexical não encontrava palavras em comum com a rubrica.

O ajuste em `student_claims/grounding.py` permite o lado direito **completo** de uma igualdade exclusivamente para a representação de forma reduzida já suportada. O comportamento padrão dos outros tipos de claim não muda. Prefixos `<=`, `>=`, `!=`, expressões parciais e continuações algébricas não são aceitos como essa forma. Citações, hipóteses, negações e tentativas rejeitadas continuam barradas pelas camadas de atribuição existentes.

Não foi criada uma regra de pontuação. Tanto `(a+b)x-a` quanto `(a-b)x-a` agora são corretamente atribuídos ao texto quando escritos como RHS. O checker Lean existente verifica a primeira forma e refuta a segunda. Grounding não equivale a verdade; nenhuma inferência Lean foi acrescentada.

Antes: 9 falhas / 13 aprovados nos novos testes de sintaxe, atribuição e roteamento. Depois: 22 aprovados; mais duas regressões executam Lean real. O teste de roteamento usa uma resposta explicitamente simulada `review`, confirma que o avaliador recebe a fonte integral e preserva pontuação pendente.

## F2Q6: política atual examinada antes de alterar

Reexecutou-se somente o exemplo sintético do teste histórico de certificado forte, com `semantic-b-minimal.v1`, Lean real e provider desativado. Os três checks existentes (fórmula, razão e resposta final) retornaram `verified`; seus contratos não formalizam globalmente a modelagem probabilística nem toda a justificativa do máximo.

O detector legado continua sem produzir `maximizers_identification` nessa formulação. Contudo, a política atual **já encaminha** `probability_formula`, `ratio_comparison` e `maximizers_identification` ao avaliador semântico. Este recebe a solução integral, incluindo as comparações para `n<6`, `n=6` e `n>6`; as âncoras de evidência são literais, vinculadas à razão escrita. Com provider desativado, os critérios permanecem pendentes e a nota é `null`, com falha de provider explícita. Isso não é nota zero nem uma execução semântica concluída.

Aplicar opiniões `met` **simuladas e identificadas** à cópia em memória da mesma avaliação produz 3+3+2+2=10, exclusivamente pelos pesos originais. Isso comprova o encaminhamento e a aplicação da política, não o julgamento de GPT real. O artefato resumido é [evidence/f2q6-current-policy.json](evidence/f2q6-current-policy.json); não houve alteração do AuditRun gerado nem de registros anteriores.

Não se ampliou o detector legado nem se passou a emitir um certificado forte de referência apenas para obter 10. O xfail histórico permanece explícito no caminho `legacy`; a política atual tem regressões adicionais para `met`, `not_met`, `review` e falha técnica. A limitação funcional remanescente nessa redação é a dependência semântica, cuja execução real está fora da autorização atual.

## Testes e impacto

- **55 aprovados**: novos casos RHS com Lean real, replay ITA arquivado, integração Semantic B, checkers e ajustes F2Q1 (266,46 s).
- **609 aprovados / 4 skips preexistentes**: fidelidade, evidências positivas, crédito indevido, representação comum, extração genérica, citações arquivadas TME e fluxo mínimo P1–P5 (130,99 s).
- **4 aprovados**: F2Q6 na política atual, com provider simulado (1,64 s).
- Total dessas execuções: **668 aprovados, 4 skips**. Skips: artefatos históricos locais ausentes em fidelidade, evidências positivas, claims comuns e extração genérica. Nenhum skip/xfail novo.
- `git diff --check` aprovado. Checkers, Lean, rubricas, PautaEngine e política semântica não modificados. Os 21 casos históricos ainda sem validação independente continuam pendentes.

Comandos:

```sh
python -m pytest -q tests/test_ita_equality_chain_grounding.py tests/test_ita_real_fallback_replay.py tests/test_dec10_specialized.py tests/test_f2q1_student_claim_checks.py tests/test_f2q1_rubric_adjustments.py
python -m pytest -q tests/test_claim_fidelity.py tests/test_positive_credit_evidence.py tests/test_secondary_false_credit.py tests/test_common_math_claims.py tests/test_generic_student_math.py tests/test_tme_archived_quote_scope.py tests/test_tme_minimal_functional.py
python -m pytest -q tests/test_f2q6_current_semantic_routing.py
```

O efeito esperado sobre TME/DYNAMIC é nulo: o novo modo de fronteira é solicitado apenas pelo claim F2Q1 preparado. As regressões compartilhadas foram executadas; o CI do PR complementa essa verificação. O ajuste técnico do orçamento de canonização é um PR separado.
