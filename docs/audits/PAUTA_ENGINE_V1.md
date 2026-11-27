# PautaEngine v1

## Diagnóstico anterior à implementação

Baseline: `f547476e5bb9ddf42f04ca6c792ffa9a9f8fd90a`, branch
`feat/tme-dual-input`, working tree inicialmente limpo.

- `core/problem_assets.py`: `RubricConfig` contém uma lista plana de
  `RubricItemConfig` (`id`, descrição, peso, tipo de claim e microclaims exigidos).
  A validação exige que os pesos somem exatamente `max_score`.
- `rubric/rubric_evaluator.py`: a primeira passagem concede o peso integral
  quando os requisitos e a atribuição positiva são satisfeitos; caso contrário,
  conserva `points=None`. Os adjusters podem registrar refutação e zero.
- `rubric/assessment.py`: soma critérios decididos; o total fica pendente quando
  existem critérios sem pontuação. `scoring_policy.py` preserva essa passagem e
  soma `suggested_points` após a adjudicação dos critérios pendentes.
- `positive_evidence.py`, o rubric bridge e os gates do secondary distinguem
  conteúdo atribuído ao aluno de prova de referência. Grounding sozinho não é
  comprovação matemática. O secondary oferece somente zero ou peso integral por
  critério (`allowed_points`), não faixas ou caminhos alternativos.
- Os assets ITA inspecionados e seus contratos são aditivos. Não há árvore
  declarativa de faixas, exclusão entre caminhos ou carry-forward.

Compatibilidade: a nova camada será opt-in, com entrada de evidência estruturada,
sem substituir `evaluate_rubric`, `apply_scoring_policy`, modelos históricos,
assets ITA ou seus gates. Não é necessário adapter de migração nesta versão.
O piloto será uma configuração de exemplo, fora do catálogo de problemas do
pipeline, para não anunciar suporte upstream inexistente.

## Arquitetura implementada

Arquivos novos:

- `app/confia_lean_auditor/rubric/pauta/models.py`: contratos Pydantic fechados,
  imutáveis, com versões `pauta.v1`, `pauta-evidence.v1` e `pauta-decision.v1`.
  `PautaConfig` declara obrigações e itens; `PautaRule` representa uma árvore;
  `PautaEvidence` identifica problema e solução; `PautaDecision` explica cada nó;
  `PautaAssessment` reúne os itens, intervalo e nota sugerida.
- `app/confia_lean_auditor/rubric/pauta/engine.py`: `PautaEngine.evaluate`, função
  sem estado compartilhado sobre configuração e evidências já avaliadas.
- `app/confia_lean_auditor/rubric/pauta/__init__.py`: API pública e `load_pauta`.
  O loader rejeita chaves JSON repetidas, campos desconhecidos e versões não
  suportadas. Ler o JSON é responsabilidade do loader, não do avaliador.
- `examples/pautas/tme2_problem1.v1.json`: pauta-piloto, fora de `problems/`.
- `tests/test_pauta_engine.py`: testes offline de pauta e contratos.
- Este relatório.

O motor não importa extração, grounding, canonicalização, alignment, checkers,
Lean, secondary, recognition ou frontend. Não recebe texto de solução, não
interpreta as descrições da pauta, não gera texto pedagógico, não lê artifacts
de execução e não chama API. Os IDs de obrigações são a interface entre os
produtores de evidência e a pauta. A entrada identifica uma única solução; a
conferência desse vínculo e das referências reais cabe ao integrador upstream.

Não foi conectado automaticamente a `execute_audit`: esta é uma API opt-in para
evidências estruturadas. Nenhum modelo ou caminho ITA existente foi modificado.
Um adapter futuro precisará preservar a diferença entre evidência primária,
sugestão secundária e decisão humana. Um adapter que só copie pesos não resolve
essas diferenças e não foi introduzido nesta tarefa.

## Contrato de evidência

Cada `ObligationEvidence` contém `obligation_id`, `status`, `origin`, referências
existentes em `evidence_refs`, atribuição ao estudante e, quando necessário,
contexto condicional. Os estados são `supported`, `refuted`, `indeterminate` e
`technical_error`; ausência de registro produz indeterminação explícita.

`supported` e `refuted` exigem referências não vazias e únicas. Para efetivar uma
decisão matemática, a origem precisa estar autorizada na obrigação e a evidência
precisa ser atribuível ao aluno. A ausência dessas condições produz estado
efetivo indeterminado, mantendo estado original, origem, referências e motivo.
Obrigações duplicadas/conflitantes são rejeitadas, sem escolher silenciosamente
a última versão. IDs não declarados e problema divergente também são rejeitados.

As origens possíveis são `deterministic`, `student_lean`, `reference_lean`,
`secondary`, `semantic` e `diagram`. O padrão admite somente as duas primeiras.
Prova de referência isolada não pode ser autorizada como conquista do aluno.
Ela pode ser preservada como observação, mas não concede crédito direto. Se uma
validação upstream comprovar atribuição e dependências, deve fornecer a evidência
derivada com a origem real dessa validação e referências às fontes necessárias.

Origens `secondary`, `semantic` e `diagram` podem ser autorizadas explicitamente
por obrigação e sempre preservam `needs_review`. Uma negação secundária não pode
ser codificada como refutação matemática. A autorização no schema **não executa
nem substitui** os gates existentes: o integrador deve aceitar somente evidência
já aprovada por esses gates. IDs e flags sintéticos não são prova criptográfica de
correção, grounding ou existência de um registro. Esta interface é interna e
confiável, não um endpoint para aceitar afirmações de pontuação do estudante.

## Semântica de pontuação

| Estratégia | Regra |
|---|---|
| `all_of` | Exige suporte para todas as obrigações; uma refutação basta para negar o componente. |
| `any_of` | Um suporte aceito basta; só fica negada quando todas as alternativas são refutadas. |
| `additive` | Soma pontos dos filhos, limitada ao teto declarado. |
| `banded` | Escolhe uma única faixa, a maior integralmente satisfeita. Cada faixa é um predicado `all_of`, `any_of` ou `carry_forward`. |
| `max_of` | Escolhe um único caminho com maior pontuação comprovada, inclusive parcialidade explicitamente decomposta nesse caminho. |
| `carry_forward` | Executa somente o contrato condicional descrito abaixo. |

Empates usam a ordem declarada dos filhos. Faixas não podem conter subtotais
parciais como se fossem condições integralmente satisfeitas. Caminhos de
`max_of` podem conter árvores de pontuação. `all_of` e `any_of` nesta versão
operam sobre IDs de obrigações; não inferem equivalência entre expressões.
Independência dos componentes aditivos e eventual reaproveitamento legítimo de
uma obrigação entre itens são decisões editoriais da pauta, não inferências do
motor.

Cada nó conserva `known_points` e `possible_points`. O segundo é um **limite
condicional de pontuação**, não crédito concedido nem afirmação de viabilidade
matemática conjunta. Se uma faixa maior ainda está indeterminada, a faixa menor
comprovada aparece como `selected_band`, mas o intervalo permanece aberto.
Analogamente, um método já comprovado pode ser selecionado sem afirmar que outro
caminho pendente não obteria mais pontos. Os filhos permanecem no relatório.

Há duas políticas explícitas:

- `defer` (padrão): uma incerteza relevante para a pontuação mantém
  `points_awarded=None` e, portanto, `score=None`. O subtotal conhecido continua
  disponível.
- `withhold`: concede somente os pontos conhecidos quando há evidência ausente
  ou indeterminada. O estado continua indeterminado, o intervalo é preservado e
  `needs_review=True`. Isso é uma convenção de pontuação declarada, não um zero
  matemático inferido. O piloto usa esta política para seu “0 caso contrário”.

Erro técnico relevante mantém a pontuação pendente mesmo sob `withhold`. Uma
alternativa integralmente comprovada ou um teto já alcançado pode tornar a
incerteza irrelevante para o score; o erro técnico continua registrado e sinaliza
revisão. Uma refutação decisiva de um requisito de `all_of` também pode fixar zero
sem converter os demais requisitos desconhecidos em refutações.

Pontos usam `Decimal`: somas, limites e comparações são exatos, sem arredondamento
heurístico. Na serialização JSON do Pydantic, decimais são strings, por exemplo
`"3"` e `"0.3"`. Consumidores devem preservar esse contrato. O score é uma
sugestão ConfIA, não decisão final do avaliador humano; a nova camada não escreve
nenhum registro de avaliação humana.

## Carry-forward

`CarryForwardContract` declara quatro obrigações distintas: resultado anterior,
adoção desse resultado, dependência do passo posterior e coerência matemática do
desenvolvimento condicionado. Esta versão exige erro anterior comprovado
(`refuted`), não presume erro a partir da ausência de prova.

As três evidências posteriores devem ser aceitas, atribuídas e vinculadas ao
mesmo `ConditionalContext`: ID da regra, ID da obrigação anterior e referência
do resultado adotado. Essa referência precisa constar tanto da evidência do
resultado anterior quanto da adoção. Vínculos ausentes ou divergentes não
autorizam crédito. Coerência condicionada refutada não concede pontos.

O contrato positivo concede os pontos do passo posterior mantendo o erro
anterior e sua penalização originais. Evidência condicional não pode ser
reutilizada como conclusão absoluta em uma regra comum. Um caminho ordinário e
um caminho carry-forward podem coexistir sob `max_of`, sem soma duplicada.

Não há automação de extração dessa relação nesta versão. Os testes fornecem
evidência estruturada sintética; o motor não decide se o desenvolvimento é
coerente, apenas exige que essa conclusão já tenha sido estabelecida upstream.
Não foi habilitado carry-forward no piloto TME² sem uma regra editorial e sem
evidências específicas para isso.

## Piloto TME² — Problema 1

A configuração traduz os requisitos fornecidos neste pedido, não uma leitura
independente de um documento oficial externo.

| Item | Teto | Representação |
|---|---:|---|
| a | 3 | `banded`: 3 pela identificação de 137, montagem e conclusão 594; 2 pela identificação, montagem e evidência explícita de erro somente aritmético; 1 pela identificação; caso contrário, 0 sob `withhold`. |
| b | 5 | `additive`: invertido (2), subtração **e** cancelamento (2), fatoração justificada (1). |
| c | 6 | `additive`: uso da expressão (1), domínio de a−c justificado (1), lista em faixa única 4/3/2/1/0 (máximo 4). |
| d | 6 | `additive`: equação **e** diferença 6 (2), pares exatos (2), dez escolhas de b **e** total justificado 30 (2). |

Total: 20. A resposta isolada 594 não comprova a construção e recebe zero no
item a. Montagem sem conclusão não demonstra, por si, “somente erro aritmético”
e não obtém automaticamente a faixa 2. Uma ocorrência de `99(a-c)` no item c não
comprova os componentes do item b; mesmo a fatoração justificada vale somente
seu ponto nesse item.

As qualificações da lista (“completa”, “exatamente uma falha”, “padrão
reconhecido”) são obrigações estruturadas a serem avaliadas upstream. O motor não
conta números no texto nem cria classificações por regex. A faixa 3 exige uma
omissão **ou** um valor indevido, sem outra falha. A faixa 2 exige simultaneamente
vários valores corretos e padrão reconhecido.

Uso offline mínimo, a partir da raiz do repositório:

```python
from pathlib import Path
from confia_lean_auditor.rubric.pauta import (
    PautaEngine, PautaEvidence, ObligationEvidence, load_pauta,
)

pauta = load_pauta(Path("examples/pautas/tme2_problem1.v1.json"))
evidencia = PautaEvidence(
    problem_id=pauta.problem_id,
    solution_id="exemplo-estruturado",
    obligations=(ObligationEvidence(
        obligation_id="a.identifies_137", status="supported",
        origin="deterministic", attributable_to_student=True,
        evidence_refs=("registro-upstream-ja-validado",),
    ),),
)
resultado = PautaEngine().evaluate(pauta, evidencia)
assert resultado.items[0].points_awarded == 1
assert resultado.needs_review  # as outras obrigações continuam desconhecidas
```

O identificador do exemplo ilustra a interface; em integração real, deve apontar
para evidência existente e validada. O motor nunca cria esse registro.

## Explicabilidade e invariantes

Cada decisão inclui item, estratégia, teto, pontos, intervalo, estado,
obrigações satisfeitas/refutadas/indeterminadas/com erro técnico, faixa ou método
selecionado, carry-forward, referências observadas e referências efetivamente
usadas para crédito, motivo estável e filhos. Os motivos são códigos de decisão,
não texto pedagógico. Estados são locais à regra; o mesmo registro condicional
pode ser válido no caminho carry-forward e inadmissível fora daquele contexto.

O resultado identifica problema, solução e versões, além de SHA-256 da
configuração e da evidência normalizadas. Esses hashes identificam entradas;
não autenticam sua origem nem comprovam matemática.

O schema e o avaliador garantem limites finitos não negativos, tetos coerentes,
IDs únicos e declarados, ausência de predicados vazios que fabriquem crédito,
ausência de soma entre faixas/métodos, soma dos itens limitada a `max_score`,
pontuação concedida igual ao subtotal comprovado, referências de crédito
existentes na evidência observada e preservação de pontuação pendente. Nenhum
ponto potencial pode ser promovido a concedido. As entradas não são mutadas.

## Lacunas e riscos residuais

- Diagramas: há origem e política de aceitação explícitas, mas nenhuma visão
  computacional ou interpretação geométrica nova. A qualidade da evidência
  continua a cargo de produtores confiáveis upstream.
- Carry-forward automático: faltam produtores que estabeleçam a adoção, a
  dependência e a coerência condicionada com referências reais. Não há tolerância
  automática a resultado errado, nem propagação heurística entre itens.
- Métodos semanticamente livres: `max_of` representa caminhos declarados ou
  obrigações equivalentes já validadas upstream; não descobre métodos novos nem
  decide equivalência matemática. Uma nova família de métodos precisa de
  configuração ou de evidência upstream correspondente.
- As obrigações não resolvem contradições semânticas entre IDs distintos. A
  produção/validação upstream deve resolver conflitos antes de afirmar suporte.
- Erros editoriais de decomposição, pesos, independência ou classificação de
  faixa podem produzir uma pauta inadequada, mesmo válida estruturalmente.
  O piloto deve ser revisado editorialmente antes de uso avaliativo real.
- A compatibilidade ITA é preservada por isolamento. Isso não constitui uma
  migração validada de todo o pipeline para o novo motor.

## Validação

**PASS: 464 testes distintos**, sendo **100 novos** e **364 existentes**. Nenhuma
falha de teste ou regressão observada no escopo validado.

A execução combinada passou em 460 testes (96 novos existentes no momento da
coleta + 364 legados), em 75,22 s. Após concluir quatro regressões adicionais e
fortalecer os invariantes da nova camada, a execução final isolada passou nos
100 novos testes, em 0,30 s. Não se somam as duas execuções como 560 testes
independentes. As alterações posteriores à execução combinada ficaram somente
na camada nova e em seus testes.

Comandos:

```sh
.venv/bin/python -m pytest -q tests/test_pauta_engine.py

.venv/bin/python -m pytest -q \
  tests/test_pauta_engine.py \
  tests/test_score_policy.py tests/test_score_policy_api.py \
  tests/test_rubric_bridge.py tests/test_rubric_bridge_pipeline.py \
  tests/test_positive_credit_evidence.py \
  tests/test_secondary_adjudicator_contract.py tests/test_secondary_evidence_ids.py \
  tests/test_secondary_false_credit.py tests/test_secondary_live_contract.py \
  tests/test_f2q1_rubric_adjustments.py tests/test_f2q3_rubric_adjustments.py \
  tests/test_f2q5_rubric_adjustments.py tests/test_f2q6_rubric_adjustments.py \
  tests/test_f2q8_rubric_adjustments.py \
  tests/test_problem_assets_contracts.py tests/test_problem_assets_validation.py

git diff --check
git status --short --untracked-files=all
```

A primeira tentativa de invocar o executável `.venv/bin/pytest` diretamente
falhou na coleta de cinco módulos legados que importam `tests.*`, por não ter a
raiz no caminho de imports. `python -m pytest` resolveu a invocação sem qualquer
alteração desses testes ou do projeto. O log inicial foi preservado junto aos
logs das execuções aprovadas.

O piloto completo também foi avaliado com evidência estruturada sintética sem
asserções de erro aritmético nem evidência de faixas inferiores: resultado
**a=3, b=5, c=6, d=6, total=20**. O JSON de decisão preserva toda a árvore e os
hashes de entrada. Isso demonstra o contrato de pontuação, não extração automática
nem auditoria live de uma resposta TME².

Artifacts locais (ignorados pelo Git): `artifacts/evaluations/pauta_engine_v1_20261031T161430Z/`:

- `validation_summary.json`, `new_tests.log`, `related_tests.log` e
  `initial_collection.log`;
- `pilot_evidence.synthetic.json` e `pilot_decision.synthetic.json`;
- `pauta_schema.v1.json`, gerado dos modelos.

`git diff --check`: **OK**. Como os seis arquivos novos ainda não estão no
índice, foi feita também uma checagem explícita de whitespace nesses arquivos.
`git diff --name-only` e `git diff --cached --name-only`: vazios. Todos os arquivos
legados rastreados, incluindo rubricas ITA, scoring e gates, estão intactos.
`git status --short --untracked-files=all` lista somente os seis arquivos novos
indicados neste relatório. Não houve staging, commit ou push.

Os novos testes não dependem de artifacts locais, extractor, Lean ou API. Os
contratos existentes foram executados offline; os testes de secondary usam
providers/transportes de teste. Não houve chamada externa, benchmark integral,
modificação de UI ou tentativa de corrigir outras tarefas.
