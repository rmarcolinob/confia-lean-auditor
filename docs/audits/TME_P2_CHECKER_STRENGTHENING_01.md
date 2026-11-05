# TME P2 — Checker Strengthening 01

Data: 2026-11-05 (America/Fortaleza). Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2`. Branch: `experiment/tme-semantic-formal-p2`. Base e HEAD ao término: **`34732d445ff1e885a7156278ad4bb81c1fed25b2`**.

**Veredito: `P2_CHECKER_COVERAGE_COMPLETE` para o substrato opt-in `P2_CHECKER_FIRST`, versão `p2-checker-first.v1`, dentro do contrato tipado atual de P2.** Os quatro gaps receberam verificação matemática independente e controle explícito de suficiência. Foram aprovados **1.202 testes: 125 novos determinísticos/de integração, 9 novos controles de integração Lean e 1.068 regressões existentes; zero falhas, erros de teste ou skips**.

O caminho `TME_CURRENT` permanece inalterado. A declaração de cobertura completa aplica-se à nova entrada, não às rotas híbridas legadas nem a interpretação de prosa livre. Não foi implementado SemanticExtractor P2, modelo de extração geral ou checker semântico; não houve alteração de pauta, pesos ou regras de scoring, tuning, expansão de implementação para P3, uso de gold/holdout ou commit.

## 1. Antes e depois

| classificação | diagnóstico 01 | entrada nova |
|---|---:|---:|
| FORMAL_STRONG | 6 | 6 |
| DETERMINISTIC_STRONG | 13 | 14 |
| COMPOSITE_STRONG | 0 | 3 |
| SEMANTIC_CHECKER | 0 | 0 |
| CHECKER_GAP | 4 | **0** |
| total | 23 | 23 |

A [matriz 02](TME_P2_CHECKER_COVERAGE_02.md) registra as 23 obrigações, claim types, produtores, rotas, subclaims, dependências e riscos. São 19 IDs diretamente referidos por regras pontuáveis e quatro auxiliares; não há 23 parcelas de pontos.

## 2. Arquitetura e isolamento

A implementação adiciona `experimental/tme_p2_checker_first`, sem editar módulos existentes. `StrongP2Checks` herda `P2Checks` e substitui a produção de evidência somente para `b.integral_sum`, `c.pair_permutations`, `c.pair_orientations` e `c.counting_product`. Os outros 19 produtores continuam executando o mesmo código, assim como os diagramas, a revalidação da fonte, o bridge e `PautaEngine`.

A entrada explícita é:

```python
from confia_lean_auditor.experimental.tme_p2_checker_first.engine import audit_p2_checker_first

result = audit_p2_checker_first(
    {"c": "pair_permutations: 4!=24\npair_orientations: 2^4=16\ncounting_product: 24*16=384"},
    solution_id="p2-checker-first-example",
    use_lean=True,
)
```

Ela não troca o registry global. Usa o coletor tipado existente, no contexto `deterministic_only`, inclusive se a flag de suplemento semântico estiver ligada no ambiente. Não há chamada a provedor LLM. `checks` expõe componentes e suas origens; `awards` expõe as decisões por obrigação do bridge, sem atribuir novos pesos; `assessment` é o resultado original do PautaEngine.

Para manter `score` numérico mesmo em erro técnico, reutiliza-se a **ScoreClosurePolicy já existente em C1**: a vista numérica mostra somente pontos conhecidos; `assessment.score` continua `None` quando essa é a decisão do engine, e `technical_uncertainty`, `review_recommended` e `score_closure` conservam a incerteza. Não há nova fórmula de nota nem promoção de erro a zero definitivo sem sinalização.

## 3. Os quatro gaps

### G1 — `b.integral_sum`

**Antes:** o produtor selecionava o enum de integralidade e observava `True`; o reconhecimento era promovido a validação sem checker próprio.

**Agora:** `check_integrality` valida um `IntegralInput` estrito, com subject `S`, exatamente três termos e nenhum campo extra. O adaptador aceita o registro tipado existente `integral_sum: integer` (incluindo aliases canonizados) e vincula a propriedade à definição de S como soma dos três dígitos da linha. O certificado registra explicitamente que os termos simbólicos `left`, `center`, `right` são inteiros do domínio 1–9 do problema, não dados adivinhados ou passos atribuídos ao estudante.

Proposição: se S é a soma dos três dígitos inteiros da linha, então S é inteiro. Subclaims: sujeito correto; três termos; domínio inteiro dos termos; fechamento da soma. A API do checker também permite termos racionais concretos para verificação exata e controles negativos. Nenhum arredondamento ou opinião semântica é usado.

Rota: **DETERMINISTIC_STRONG**. A regra de domínio e o cálculo racional exato decidem esta propriedade sem perda de rigor; não foi introduzido um lema Lean que simplesmente declarasse S inteiro por escolha do tipo. O aluno ainda precisa afirmar a integralidade em fonte atribuível; a propriedade do problema não cria automaticamente essa evidência.

| entrada do checker | resultado | significado |
|---|---|---|
| `('left','center','right')`, `('1','5','9')`, `('2/2','5','9')` | DETERMINISTIC_VERIFIED | domínio e fechamento confirmados |
| `('1','2','1/2')` | DETERMINISTIC_FAILED; refutação matemática | soma não integral / domínio incompatível |
| `('0','2','3')` | DETERMINISTIC_FAILED; `non_digit_term` | viola domínio de dígito; **não** afirma que a soma 5 seja fracionária |
| dois termos ou símbolo desconhecido | DETERMINISTIC_NOT_ATTEMPTED | representação incompleta/não suportada; não é falsa |
| subject errado, bool ou campo extra | DETERMINISTIC_ERROR | payload inválido; não é refutação |

Testes: dez controles diretos, integração com a dependência de centers, enum desconhecido e quatro contextos não atribuíveis. A via balance_relation + integral_sum + centers continua dando 4 pontos; centers isolado continua insuficiente. Nenhum ponto direto novo para integralidade.

### G2 — `c.pair_permutations`

**Antes:** o valor 24 ou uma igualdade aritmética correta bastava, sem certificar a contagem das distribuições.

**Agora:** a família explícita de checkers compostos, identificada em metadata por `P2CompositeCountingChecker`, verifica separadamente:

1. aritmética escrita, pelo mecanismo existente D ou Lean;
2. quatro pares complementares distintos e quatro linhas rotuladas; enumeração das 24 bijeções;
3. estrutura escrita de permutação, como `4!`, `4!=24`, `4*3!=24` ou produto dos fatores 4,3,2,1.

Literal `24`, `24=24` e cálculo alheio `2^3*3=24` não estabelecem a justificativa, mesmo com aritmética verdadeira. Esses casos são insuficientes, não uma refutação da igualdade. Rota: **COMPOSITE_STRONG**, com origem D/L explicitada por componente. Crédito preservado: 2 pontos, sem exigir c.pairs pré-creditado.

### G3 — `c.pair_orientations`

**Antes:** atingir 16 aritmeticamente não certificava duas orientações por par nem independência.

**Agora:** verifica extremos distintos, as quatro escolhas binárias (16 vetores completos), sua combinação sem colisão no modelo de configurações, a aritmética escrita e a estrutura de quatro fatores 2, incluindo `2^4` e `2*2*2*2`. Literal `16` ou `4+12=16` não demonstra essa relação. Rota: **COMPOSITE_STRONG**. Crédito preservado: 2 pontos, independente do pré-crédito de distribuições.

### G4 — `c.counting_product`

**Antes:** a forma do produto e os valores 24 e 16 não certificavam que os fatores contavam os objetos certos nem a ausência de duplicação/omissão.

**Agora:** verifica os conjuntos A (24 permutações) e B (16 orientações), a codificação A×B em configurações válidas, injetividade, sobrejetividade, inversa, aritmética e produto escrito das duas etapas. O certificado não se limita a contar a saída de seu próprio gerador: compara as 384 codificações com um conjunto obtido de forma independente, filtrando todas as **8! = 40.320 permutações dos dígitos externos** pelas quatro somas de linha.

Resultado: centro 9, soma 18, pares `(1,8),(2,7),(3,6),(4,5)`, 24 distribuições, 16 orientações e 384 estados rotulados. Hash SHA-256 do conjunto ordenado de estados:

```text
99515ea1ea47b7126fbe97d99f5a357f6509a11358ef5b398d44d44f41e70bd4
```

A inversa é reconstruída dos pares observados em cada linha, não obtida consultando a tabela do gerador. O cache interno é serializado; cada consumidor recebe uma cópia nova, impedindo alteração acidental do certificado compartilhado.

Mantém-se o método tipado direto `24*16=384`, `16*24=384` e formas estruturais equivalentes aceitas, sem exigir os dois itens anteriores. `12*32=384` tem aritmética verdadeira, mas relação combinatória insuficiente. `24*16=364` é efetivamente falso. Rota: **COMPOSITE_STRONG**. Os 5 pontos do método direto continuam alternativos ao caminho fatorado pelo `max_of` original: ambos presentes não duplicam a nota.

### Certificado matemático versus argumento do estudante

O certificado finito é identificado como matemática do **problema**, não prova fornecida pelo estudante. O componente `relation` verifica uma gramática limitada de argumento tipado, vinculada ao subject, item e trecho atribuível. Aritmética correta não basta. No resultado composto aparecem, independentemente:

```text
COMBINATORIAL_JUSTIFICATION_SUPPORTED
counting_components_verified = true
arithmetic_verified = true
relation_supported = true
```

A classificação acima exige todos os componentes positivos. A origem, status, expressão, source_span, checker_result e arquivos de prova/refutação ficam disponíveis na trilha. O conjunto não é rotulado `student_lean`: somente o componente efetivamente provado usa FORMAL_VERIFIED.

A mudança de contrato é explícita: números isolados nas três obrigações JUSTIFICATION deixam de bastar na entrada nova. A conclusão `total: 384` permanece FINAL_ANSWER de 1 ponto, conforme a pauta e os 19 checkers preservados. Não foi exigida repetição de etapas anteriores. Formas discursivas ou estruturas fora da gramática podem ficar insuficientes e requerer revisão; zero gap de checker não significa recall completo de linguagem natural.

## 4. Lean real

**Novos teoremas/checkers Lean estruturais: nenhum.** O certificado de estrutura combinatória é determinístico exato. Para este domínio fixo, a enumeração independente e a inversa verificadas fornecem uma decisão finita completa, com custo pequeno, sem depender de novos lemas de cardinalidade/bijeção. Uma formalização Lean dessa estrutura permanece possível, mas não foi apresentada como realizada.

Reutilizou-se o ciclo real dos subclaims aritméticos já existentes e testou-se sua composição com os novos certificados. Os testes usam processos Lean reais, sem mocks de compilador ou stdout. O controle sem igualdade confirma justamente a ausência de tentativa, não uma execução fictícia.

Infraestrutura do worktree preparada durante esta tarefa: `lake exe cache get` concluiu usando o cache local (7.604 arquivos descomprimidos), seguido de `lake build` bem-sucedido, **8.038 jobs**. Uma primeira compilação integral foi interrompida para aproveitar o cache; não foi contabilizada como build concluído ou falha de checker. Nenhum arquivo de toolchain/manifest foi alterado.

- Lean: **4.28.0**, `arm64-apple-darwin24.6.0`, commit `7e01a1bf5c70fc6167d49c345d3bf80596e9a79b`, Release.
- Mathlib: **v4.28.0**, revisão **`8f9d9cff6bd728b17a24e163c9402775d9e6a365`**, conforme manifest preservado.
- Import efetivo do wrapper existente: `Mathlib`.

Arquivo: [test_tme_p2_checker_first_lean.py](../../tests/test_tme_p2_checker_first_lean.py).

| teste / entrada | status do componente | prova efetiva / diagnóstico | pontos | teste |
|---|---|---|---:|---|
| `test_real_composite_arithmetic_and_refutation`, `4!=24` | FORMAL_VERIFIED | igualdade compilou | 2 | PASS |
| mesma função, `2^4=16` | FORMAL_VERIFIED | igualdade compilou | 2 | PASS |
| mesma função, `24*16=384` | FORMAL_VERIFIED | igualdade compilou | 5 | PASS |
| mesma função, `4!=20` | FORMAL_REFUTED | prova positiva falhou; negação compilou | 0 | PASS |
| mesma função, `2^4=8` | FORMAL_REFUTED | prova positiva falhou; negação compilou | 0 | PASS |
| mesma função, `24*16=364` | FORMAL_REFUTED | prova positiva falhou; negação compilou | 0 | PASS |
| `test_no_equality_is_formal_not_attempted_not_refuted`, `4!` | FORMAL_NOT_ATTEMPTED; DETERMINISTIC_VERIFIED | sem igualdade a renderizar; rota D sustenta o claim | 2 | PASS |
| `test_real_lean_inconclusive_and_technical_diagnostics`, tática `skip` | FORMAL_UNPROVED | `UNSOLVED_GOALS`; nenhuma prova nem refutação compilou | n/a | PASS |
| mesma função, identificador deliberadamente inexistente | FORMAL_ERROR | `UNKNOWN_IDENTIFIER`; erro real no processo Lean | n/a | PASS |

Os últimos dois são controles intencionais da classificação de falhas do ciclo existente, usando a proposição aritmética real de P2. Não são falhas encontradas na prova válida nem erros de infraestrutura ocultados.

Stdout relevante: provas verdadeiras e negações bem-sucedidas retornaram vazio; as tentativas positivas dos claims falsos registraram `error: unsolved goals` e `⊢ False`, seguidas de `refutation_verified=True`. O controle inconclusivo registrou o objetivo `↑(Nat.factorial 4) = 24`; o controle técnico registrou `Unknown identifier p2_intentionally_missing_identifier`. **Stderr vazio** em todos esses processos, inclusive as refutações; Lean emitiu os diagnósticos no stdout. Recibos JSON completos e cópias dos arquivos Lean gerados estão nos artefatos indicados abaixo.

## 5. Segurança epistemológica

Ordem explícita no combinador:

1. `FORMAL_REFUTED` ou `mathematical_refutation=True` → `refuted`;
2. sem refutação, `FORMAL_ERROR`/`DETERMINISTIC_ERROR` → `technical_error`;
3. componentes obrigatórios presentes, nomes únicos e todos matematicamente verificados → `verified`;
4. demais casos → `unverified`.

`DETERMINISTIC_FAILED` com falsidade matemática não pode ser sobreposto por semântica. Quando o mesmo status expressa somente ausência de uma estrutura argumentativa reconhecida, o marcador é falso e o agregado é insuficiente, não refutado. O motivo fica registrado.

`FORMAL_VERIFIED`, `FORMAL_REFUTED`, `FORMAL_UNPROVED`, `FORMAL_NOT_ATTEMPTED` e `FORMAL_ERROR` não são intercambiáveis. Sem subprocesso comprovadamente iniciado, o adaptador não inventa execução formal: `PROCESS_ERROR` mantém tentativa indeterminada; fonte não grounded permanece não tentada. A aritmética exata pode ter `DETERMINISTIC_VERIFIED` e, simultaneamente, `formal_status=FORMAL_NOT_ATTEMPTED`.

Não há autoridade semântica habilitada: uma `semantic_decision` artificial é ignorada pelo combinador e não fornece componentes ausentes nem reverte erro/refutação. `SEMANTIC_SUPPORTED` e `SEMANTIC_INSUFFICIENT` não são promovidos a verificação formal/determinística. Nenhuma implementação de LLM substitui checker matemático.

A política efetiva é `claim → checker → status → sufficiency → decisão de evidência/award → PautaEngine`. A suficiência nova é o componente estrutural dedicado; não foi ativado um gate semântico legado. A seleção original continua rejeitando fonte hipotética, negada, citada ou descartada antes do crédito.

## 6. Testes e regressões

| conjunto | total | passed | failed | errors | skipped |
|---|---:|---:|---:|---:|---:|
| `tests/test_tme_p2_checker_first.py` | 125 | 125 | 0 | 0 | 0 |
| `tests/test_tme_p2_checker_first_lean.py` | 9 | 9 | 0 | 0 | 0 |
| regressões existentes selecionadas abaixo | 1.068 | 1.068 | 0 | 0 | 0 |
| **total sem duplicar reruns** | **1.202** | **1.202** | **0** | **0** | **0** |

A suíte nova determinística foi repetida após o último ajuste de metadata; o total conta somente a execução final (4,85 s). Integração Lean: 77,38 s. Regressões: 281,44 s. Contagens extraídas dos JUnit XML, não inferidas da quantidade de funções.

Cada uma das três justificativas tem nove variantes: completa, numeral isolado, parcial, subclaim falso, aritmética verdadeira com argumento errado, forma equivalente, texto com rótulo irrelevante, hipótese e negação. Há ainda testes de quatro contextos não atribuíveis nos quatro gaps, precedência semântica adversarial, componente ausente, estados de execução, cache protegido contra mutação, max_of contra dupla contagem, score numérico com erro visível, suplemento LLM impedido e cobertura 6/14/3.

Preservação: os **55 casos P2 existentes** passam também pela entrada nova com as mesmas notas esperadas. Em cada caso, as evidências das **19 obrigações não alteradas** são comparadas integralmente com o caminho original. Além disso, snapshots anteriores à implementação e posteriores são **iguais para bridge e assessment completos de TME_CURRENT** nos 55 casos. Os **550 arquivos rastreados monitorados** de código/testes/pauta/configuração conservaram seus hashes. `git diff` e `git diff --cached` estão vazios.

Comandos de reprodução da seleção executada (usar novos diretórios temporários para não substituir recibos):

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/app"
export CONFIA_TME_SEMANTIC_ENABLED=0
P2_PYTHON=/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python

"$P2_PYTHON" -m pytest tests/test_tme_p2_checker_first.py \
  -q -p no:cacheprovider --basetemp=/private/tmp/p2-checker-strengthening/pytest-unit-final \
  --junitxml=/private/tmp/p2-checker-strengthening/unit-final.xml

"$P2_PYTHON" -m pytest tests/test_tme_p2_checker_first_lean.py \
  -q -s -p no:cacheprovider --basetemp=/private/tmp/p2-checker-strengthening/pytest-lean \
  --junitxml=/private/tmp/p2-checker-strengthening/lean.xml

"$P2_PYTHON" -m pytest \
  tests/test_pauta_engine.py \
  tests/test_tme2_p1_pauta_bridge.py tests/test_tme2_p2_pauta_bridge.py \
  tests/test_tme2_p3_pauta_bridge.py tests/test_tme2_p4_pauta_bridge.py tests/test_tme2_p5_pauta_bridge.py \
  tests/test_tme_semantic_formal_c1.py tests/test_tme_semantic_formal_c1_fix.py tests/test_tme_semantic_formal_c1_lean.py \
  tests/test_tme_accepted_integration.py tests/test_tme_hybrid_grader.py tests/test_semantic_claims.py \
  tests/test_obligation_semantic.py tests/test_evidence_id_semantic.py tests/test_semantic_sufficiency.py \
  tests/test_student_proof_semantics.py \
  -q -p no:cacheprovider --basetemp=/private/tmp/p2-checker-strengthening/pytest-regression \
  --junitxml=/private/tmp/p2-checker-strengthening/regression.xml
```

Os testes existentes de P3–P5 apenas verificam não regressão de componentes compartilhados; não houve expansão funcional para esses problemas. A seleção usa fixtures de desenvolvimento existentes e casos sintéticos novos, sem leitura ou execução de holdout, gold ou piloto. Não foi executada a suíte inteira indiscriminadamente.

Artefatos locais ignorados pelo Git: [summary.json](../../artifacts/evaluations/tme_p2_checker_strengthening_01/summary.json), logs e JUnit das três suítes no mesmo diretório; `lean_receipts/` contém os nove recibos, com arquivos Lean de prova/refutação quando houve execução. Também foram preservados `p2_current_before.json`, `p2_current_after.json`, `before_hashes.json`, `integrity.json`, logs de build/cache. As referências originais dos checkers apontam para `artifacts/student_claim_checks/` e foram conservadas; as cópias permitem inspecionar os novos testes em conjunto. Esses artefatos não serão incluídos implicitamente em futuro commit.

## 7. Estado Git e arquivos

SHA final: **`34732d445ff1e885a7156278ad4bb81c1fed25b2`**. Nenhum commit, stage ou alteração em arquivo rastreado preexistente.

Arquivos criados nesta implementação:

- `app/confia_lean_auditor/experimental/tme_p2_checker_first/__init__.py`
- `app/confia_lean_auditor/experimental/tme_p2_checker_first/components.py`
- `app/confia_lean_auditor/experimental/tme_p2_checker_first/engine.py`
- `app/confia_lean_auditor/experimental/tme_p2_checker_first/registry.py`
- `tests/test_tme_p2_checker_first.py`
- `tests/test_tme_p2_checker_first_lean.py`
- `docs/audits/TME_P2_CHECKER_COVERAGE_02.md`
- `docs/audits/TME_P2_CHECKER_STRENGTHENING_01.md`

Arquivos preexistentes modificados: **nenhum**. O diagnóstico 01 já estava untracked no início desta tarefa e foi preservado. Estado `git status --short` ao final:

```text
?? app/confia_lean_auditor/experimental/tme_p2_checker_first/
?? docs/audits/TME_P2_CHECKER_COVERAGE_02.md
?? docs/audits/TME_P2_CHECKER_FIRST_DIAGNOSTICO_01.md
?? docs/audits/TME_P2_CHECKER_STRENGTHENING_01.md
?? tests/test_tme_p2_checker_first.py
?? tests/test_tme_p2_checker_first_lean.py
```

## 8. Veredito e limite da entrega

**`P2_CHECKER_COVERAGE_COMPLETE`**: os quatro gaps foram fechados na nova entrada tipada, preservando os 19 checkers anteriores. Cada obrigação possui checker explícito; nenhuma recebe crédito por identificação de LLM. As três justificativas exigem matemática e relação estrutural verificadas, com procedência separada.

Este veredito não certifica interpretação geral de linguagem natural, não migra TME_CURRENT e não transforma o modelo finito em teorema Lean estrutural. A eventual entrada futura de candidatos semânticos deve consumir estes checkers, preservar os vínculos de fonte e continuar obedecendo `NO CHECKER → NO AUTOMATIC CREDIT`. Nenhum SemanticExtractor foi iniciado nesta entrega.
