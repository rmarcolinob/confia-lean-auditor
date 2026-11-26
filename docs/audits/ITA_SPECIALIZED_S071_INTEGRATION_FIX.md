# SPECIALIZED–ITA: replay e correção pontual de S071

Auditoria investigada: `artifacts/runs/20261125T003359_219972/`, questão
`ITA2025F2Q1`, solução `ITA2025F2Q1_S071_L04`, política `semantic-b-minimal.v1`.
Branch: `codex/dec10-functional-integration`. Nenhuma chamada paga foi realizada.
Os artefatos originais não foram reescritos.

## Causa comprovada

O total original **não ficou nulo por rejeição dos dois `not_met`**. Os dois
pareceres passaram pela validação de formato/citações e produziram
`suggested_points=0`. O agregador somava esses valores, mas o vetor completo era
`[0, null, 0, 2]`: o critério `reduced_polynomial_form` não foi enviado ao provider.

Há dois defeitos no adaptador `semantic_policy/ita.py`:

1. A elegibilidade só usava claims estruturados e checks relacionados. O extrator
   de F2Q1 reconhece um conjunto finito de formas de resto; `(a+b)x+(a+2)` não
   pertence a esse conjunto. O extrator genérico registrou apenas um fragmento
   sem vínculo com o critério. Entretanto, `secondary_context.prepare_payload`
   já fornecia contexto literal relevante em `candidate_evidence`, que o
   adaptador ignorava. Resultado: `review / no_eligible_evidence`, sem chamada.
2. Depois de um parecer conclusivo, o adaptador atualizava apenas
   `suggested_points`, mantendo `points=null`, `mathematical_status=indeterminate`
   e a avaliação parcial. Isso deixava a decisão por critério incoerente com a
   sugestão já aceita, mesmo nos dois critérios efetivamente avaliados.

O caminho reproduzido é `execute_audit` → extração real → resultados externos
Lean gravados → avaliação real dos microclaims → `RubricClaimContext` →
`evaluate_rubric` → ajustes existentes → `apply_scoring_policy` → adaptador ITA →
validação original `obtain_review` → agregação, relatório e publicação reais.

## Ajuste mínimo

Somente `app/confia_lean_auditor/semantic_policy/ita.py` mudou em produção:

- Quando faltam claims/checks elegíveis, usa os candidatos de contexto relevante
  ou evidência do critério **já produzidos pela infraestrutura existente**.
  Valida intervalo, texto literal e escopo; contexto genérico sem vínculo,
  hipóteses, citações e tentativas rejeitadas não abrem essa alternativa.
  Recuperar um trecho não atribui pontos: o provider ainda precisa avaliá-lo.
- Parecer válido `met` decide o crédito previsto pela rubrica; `not_met` decide
  zero. Ambos preenchem `points`, `suggested_points` e o estado matemático.
  A origem permanece `semantic_fallback`, sem certificação formal.
- `review` e resposta inválida/falha técnica continuam pendentes. Nenhuma ausência
  de extração, timeout ou indisponibilidade é convertida automaticamente em zero.
- Recalcula subtotal, máximo avaliado, estado da avaliação e soma final com
  `refresh_assessment`. O total só existe quando todos os critérios têm decisão.
- `verified_points` e `coverage` continuam representando a primeira passagem;
  `estimated_points` identifica os pontos semânticos. Decisões anteriores e seus
  rastros são preservados, inclusive ao reaplicar a política ao mesmo resultado.

Não mudaram prompt, schema, validação do fallback, rubrica, extração, checkers,
Lean, Semantic B, PautaEngine, DYNAMIC, interface, persistência ou contratos.
O fallback antigo continua mutuamente exclusivo com a política ativa.

## Conferência matemática e resposta final

Módulo `x²-x+1`, temos `x²=x-1`, `x³=-1`, `x⁶=1`. Assim,
`x⁵⁷=-1`, `x¹⁴=x-1`, `x⁷=x`, e o resto geral é `(a+b)x-a`.
O aluno usa a fatoração falsa de `x³-1`, reduz `x⁵⁷` a `1` e escreve
`a(x-1)=ax+a`. Obtém `(a+b)x+(a+2)`, que não é a identidade correta em `a,b`.
A comparação usa esse resto incorreto. A coincidência dos valores finais não
valida retroativamente as duas deduções anteriores, conforme o prompt vigente.

| Critério da rubrica executada | Decisão | Pontos |
| --- | --- | ---: |
| `power_reductions` | `not_met` gravado na chamada real | 0/3 |
| `reduced_polynomial_form` | `not_met` simulado offline, justificado acima | 0/3 |
| `coefficient_system` | `not_met` gravado na chamada real | 0/2 |
| `final_answer` | Primeira passagem preservada | 2/2 |
| Total | Todos os critérios decididos | **2/10** |

O critério final pede explicitamente a conclusão `a=-1, b=3`. Ela está no trecho
original `[342:403]`, vinculada a `student:student_claim_3`, com checker próprio
verificado. A evidência registra `reference_dependencies=[]`; as referências
esperadas servem à comparação, não como escrita atribuída ao aluno. Substituir
`a=-1,b=3` no resto correto produz `2x+1`. Um teste remove a conclusão da fonte
mantendo referências/checks antigos e verifica que eles não concedem crédito.

O timeout ocorreu em `f2q1_s3_coefficient_solution`, uma etapa de referência
gerada: `lean_timeout`, saída `124`. O `Attempt.lean` principal terminou com
saída `0`, mas sem teoremas gerados; não certifica o desenvolvimento do aluno.
O replay conserva o timeout e `verification_status=technical_error` no sistema
de coeficientes. Isso não impede uma decisão semântica independente. A nota
continua marcada para revisão docente, sem alegação de certificação Lean.

### Conferência histórica

O texto coincide byte a byte com
`experiments/semantic_b_plus/offline/cases/ITA2025F2Q1_S071_L04.json` no checkout
original. SHA-256 da fonte:
`abfd6160505dd7a7f5cc483d474e94960ce9f27c2446394dbf3f0f135533f016`.

A pauta histórica em `dataset_1000_v1.2/questoes/ITA2025F2Q1/pauta.yaml` tem
**cinco critérios de um ponto**, separando as reduções de `x⁷`, `x¹⁴` e `x⁵⁷`.
Sob essa pauta, P1, P2, P3 e P5 estão presentes e P4 não: **4/5**. A ficha
`ITA2025F2Q1_S071_L04.b.yaml` também registra 4/5, com revisão humana não amostrada.
Isso é diferente da rubrica operacional de quatro critérios (3+3+2+2) gravada
no request real e preservada em `problems/ITA2025F2Q1/rubric.json`.
Não houve conversão de escala nem migração de pauta nesta correção; **2/10 é o
resultado da rubrica que a auditoria efetivamente executou**.

## Reprodução e evidências

`tests/fixtures/ita_s071_real_run/` conserva cópias integrais de `audit.json`,
da solução e dos três arquivos Lean de checks verificados; um manifesto registra
os hashes. O audit contém os claims, checks, microclaims e pareceres reais.
O teste também verifica o `math_claims.json` publicado pelo replay.

```sh
PYTHONPATH=app python -m pytest tests/test_ita_real_fallback_replay.py -q
```

O teste não invoca Lean nem GPT: injeta os resultados Lean gravados e as duas
respostas GPT reais, passando-as novamente pelo validador original. O parecer
do resto é um provider simulado explicitamente identificado. Não se afirma que
essa terceira resposta tenha sido obtida numa chamada real. Os testes de
variação de `met/review/erro` são controles de integração, não pareceres
matemáticos alternativos sobre a solução.

A suíte cobre crédito, zero, pendência, erro técnico, resposta inválida, ausência
de evidência elegível, limites de escopo, preservação de decisões anteriores,
soma correta, ausência de dupla adjudicação, vínculo da resposta final e
publicação/round-trip do resultado.

Resultado da regressão: **366 aprovados, 3 ignorados, zero falhas**, em 385,21 s.
Os três casos ignorados dependem de artefatos locais opcionais dos testes
`test_score_policy.py`, `test_positive_credit_evidence.py` e `test_rubric_bridge.py`.
Os testes de relatório incluíram verificações Lean reais, que também passaram.
Não foram executadas as 252 soluções históricas.

```sh
PYTHONPATH=app python -m pytest \
  tests/test_ita_real_fallback_replay.py tests/test_dec10_specialized.py \
  tests/test_dec10_integration.py tests/test_score_policy.py \
  tests/test_score_policy_api.py tests/test_positive_credit_evidence.py \
  tests/test_rubric_bridge.py tests/test_rubric_bridge_pipeline.py \
  tests/test_f2q1_rubric_adjustments.py tests/test_student_proof_semantics.py \
  tests/test_pedagogical_report.py tests/test_secondary_evidence_ids.py \
  tests/test_secondary_false_credit.py -q
```

Log local: `artifacts/integration-checks/ita-s071-regression.log`.
Replay completo publicado:
`artifacts/integration-checks/ita-s071-replay-validation/test_real_replay_decides_zero_0/artifacts/runs/20261125T004330_367554/audit.json`.

Arquivos modificados: o adaptador ITA indicado acima,
`tests/test_dec10_specialized.py`, o novo
`tests/test_ita_real_fallback_replay.py`, os seis arquivos da fixture
`tests/fixtures/ita_s071_real_run/` e este relatório. Nenhum outro arquivo de
produção foi alterado.

## Prontidão

O defeito de integração está corrigido e o replay é operacional. O SPECIALIZED–ITA
está pronto para uma nova execução real controlada com a mesma política, após
carregar o código atualizado no processo do piloto. Não se iniciou essa execução
nem se habilitou provider pago. A nova chamada ainda pode retornar `review` ou
falhar tecnicamente, situações em que a pendência deve ser preservada. O timeout
Lean permanece uma limitação de verificação formal registrada, não foi ocultado
nem desativado.
