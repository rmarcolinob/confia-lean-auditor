# TME P2 — Semantic Formal — implementação 01

Data: 2026-11-05 (America/Fortaleza). Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2`. Branch: `experiment/tme-semantic-formal-p2`. Base e HEAD: **`6dfab47d88c83c528b84a62b0a3877a8eda47105`**.

**Implementado o modo opt-in `TME_SEMANTIC_FORMAL` para P2**, versão `p2-semantic-formal.v1`, reutilizando os checkers fortalecidos e a pauta sem modificações. O modelo interpreta; o mapper valida fonte, contexto e compatibilidade; os checkers decidem matemática/suficiência; o PautaEngine existente calcula os pontos. O piloto DEV foi preparado e **não foi executado**. Não houve chamada real ao extractor, acesso a gold/holdout, implementação P3 ou commit.

Regra aplicada: `NO CHECKER → NO AUTOMATIC CREDIT`.

## 1. Arquitetura

```text
solução integral com itens a), b), c)
  → EvidenceUnits literais, com IDs e offsets locais
  → SemanticExtractorP2 (interpretação estruturada, sem dados de nota)
  → bind_evidence (schema fechado + ancoragem exata)
  → ObligationMapper (fonte, contexto, item, subject e tipo compatíveis)
  → registry (rota efetiva; override da sugestão do modelo)
  → ClaimProjection (mesma fonte; payload canônico reextraível)
  → StrongP2Checks congelado (checkers originais + quatro fortalecimentos)
  → validação de proveniência e suficiência
  → conflitos / award gate
  → PautaEngine congelado
  → ScoreClosurePolicy de P1
```

Pacote novo: `app/confia_lean_auditor/experimental/tme_semantic_formal_p2`. A entrada `engine.evaluate(case_id, 'TME2026P2', solution_text, ...)` aceita os modos `tme_current` e `tme_semantic_formal`. Não foi trocado o registry global, a aplicação de transcrição aceita ou o caminho legado. A seleção do novo modo é explícita.

### Extractor e EvidenceUnit

Configuração padrão: **`gpt-6.1-sol`, reasoning `medium`**, timeout 180 s, nenhuma repetição automática, `store=False`. O transporte é o construtor de compatibilidade já usado em P1. A disponibilidade real desse modelo na API não foi exercitada nesta entrega; falhas de serviço não geram interpretação simulada.

O payload contém somente enunciado integral (incluindo a descrição textual das posições/linhas), solução integral, unidades literais, lista fechada de tipos/subjects, IDs e descrições das 23 obrigações, schemas dos formatos canônicos e rotas sugeríveis. Não contém pontos, gold, nota histórica, score de baseline ou decisões anteriores. O schema proíbe campos extras, incluindo decisões de verificação e pontuação. O modelo não fornece código Lean.

Tipos fechados: `math`, `relation`, `integer_pairs`, `integer_set`, `integer_mapping`, `enum`, `congruence`, `combinatorial_math` e `qualitative`. Esses são tipos de interpretação para o `value_kind` dos checkers atuais; a projeção conserva o claim type nativo `math_named_quantity`. Qualitative preserva a evidência sem conceder crédito ou criar um checker novo.

Cada EvidenceUnit registra `evidence_id`, `source_evidence_ids`, `source_span`, `source_start`, `source_end`, `normalized_claim`, `subject`, `claim_type`, `assertion_status`, `polarity`, `scope`, `hypothetical`, `abandoned`, `attributed_to_student`, `obligation_candidates`, `route_candidate`, `extractor_model` e `metadata`. Identidade, offsets e metadata de binding são determinados localmente. O span precisa coincidir exatamente com o envelope das unidades selecionadas; IDs inexistentes, duplicados e citações fabricadas invalidam a resposta. Repetições idênticas da mesma evidence são deduplicadas; interpretações conflitantes são preservadas e bloqueadas.

### Mapper, contexto e projeção

A sugestão de obrigação não tem autoridade isolada. O mapper verifica hash/fatia literal, item proprietário, estado assertivo, polaridade, atribuição, escopo, tipo, subject permitido e representação realmente escrita. Reutiliza os gates de contexto existentes; uma classificação `asserted` produzida pelo modelo não sobrepõe hipótese, negação, citação ou abandono detectável na fonte. Items incorretos ou ausentes não são inferidos.

O payload passa pelos canonicalizadores existentes. O adaptador aceita notação literal e os vínculos de prosa delimitados no mapper. Não completa listas, posições, contas ou relações. Há proteção contra truncar `4!=20` para `4!`, inclusive em prosa e com parênteses. Ajuste de espaços em uma expressão escrita não é mudança matemática. Posições só entram por um mapping textual explicitamente escrito; não foi implementado OCR, reconstrução de DiagramState ou interpretação de geometria espacial pelo modelo.

A fonte original nunca é reescrita em texto do aluno. A projeção guarda coordenadas originais e coordenadas do framing digital existente. A coleta é repetível; o checker Lean reextrai e compara o registro antes da execução. O bridge valida fingerprints, vínculo da verificação, origem e hash da fonte. Só os registros selecionados e aprovados entram como evidência positiva; uma auditoria local do texto completo atua **apenas como veto de conflito**, sem preencher omissões positivas do extractor.

### Roteamento e suficiência

A matriz [Checker Coverage 02](TME_P2_CHECKER_COVERAGE_02.md) é materializada em um registry imutável de 23 IDs: 6 FORMAL, 14 DETERMINISTIC e 3 COMPOSITE. A sugestão de rota do modelo é conservada; se divergir da rota registrada, `route_override_reason=obligation_registry`. Não existe rota semântica de crédito. Rotas/IDs fora do schema fechado causam falha de validação do extractor e fallback explícito; sugestões válidas mas incompatíveis são sobrescritas sem apagar a evidence.

Na categoria FORMAL, o novo award gate exige **Lean realmente executado e verificado**. O checker congelado pode conservar uma decisão determinística interna quando não há proposição renderizável; o adaptador registra `FORMAL_NOT_ATTEMPTED` e não concede crédito formal. Exemplo deliberado: `total: 384` continua valendo 1 no baseline, mas não dá crédito na rota FORMAL nova sem igualdade escrita; `total: 384=384` permite a execução existente. O extractor é proibido de inventar essa igualdade. Isso é uma diferença explícita de elegibilidade da rota formal exigida nesta fase, não mudança de pauta/checker ou tuning por notas.

Para DETERMINISTIC, exige-se resultado local validado. Para COMPOSITE, preservam-se separadamente `arithmetic`, `counting_components` e `relation`, incluindo o resultado Lean quando executado e o certificado finito de enumeração/bijeção do checker anterior. Nenhum desses componentes é substituído por opinião do modelo.

### Conflitos, score e fallback

Conflitos entre evidências selecionadas, interpretações incompatíveis do mesmo trecho e contraevidência tipada detectada pelo baseline bloqueiam a obrigação. O veto conserva registros e resultados que o sustentam; não resolve contradições por confiança, ordem ou preferência pelo resultado correto. O veto local não promete encontrar prosa contraditória que o extractor omitiu e que os parsers locais não representam: esse é um limite de extração a avaliar futuramente em DEV.

O gate exige contexto elegível, checker efetivo, proveniência, status positivo, suficiência e ausência de conflito/refutação. O PautaEngine original continua responsável pelas regras e pelo `max_of`; métodos fatorado e direto não acumulam crédito duplicado. `credits` fecha exatamente com `known_points` e é registrado também no modo current/fallback.

A ScoreClosurePolicy existente de P1 mantém score numérico; uma obrigação com falha técnica não recebe crédito sem resolução, e créditos independentes permanecem. `technical_uncertainty=true` e `review_recommended=true` preservam a ocorrência. O `assessment.score=None` original continua disponível; a vista numérica usa pontos conhecidos e não declara certeza sobre o item com erro.

API indisponível, resposta incompleta ou schema/binding inválido resultam em `requested_mode=TME_SEMANTIC_FORMAL`, `effective_mode=TME_CURRENT_FALLBACK`, `fallback_used=true` e motivo explícito. O fallback executa o baseline determinístico local existente com a flag de suplemento desabilitada; não faz uma segunda chamada ao extractor. Uma extração válida vazia não ativa fallback nem recebe automaticamente os créditos positivos do baseline.

## 2. Arquivos novos e modificados

Arquivos novos:

- `app/confia_lean_auditor/experimental/tme_semantic_formal_p2/__init__.py`
- `app/confia_lean_auditor/experimental/tme_semantic_formal_p2/registry.py`
- `app/confia_lean_auditor/experimental/tme_semantic_formal_p2/evidence.py`
- `app/confia_lean_auditor/experimental/tme_semantic_formal_p2/extractor.py`
- `app/confia_lean_auditor/experimental/tme_semantic_formal_p2/mapper.py`
- `app/confia_lean_auditor/experimental/tme_semantic_formal_p2/verification.py`
- `app/confia_lean_auditor/experimental/tme_semantic_formal_p2/engine.py`
- `scripts/evaluation/run_tme_semantic_formal_p2.py`
- `tests/test_tme_semantic_formal_p2.py`
- `tests/test_tme_semantic_formal_p2_lean.py`
- `tests/fixtures/tme_semantic_formal_p2/dev_sources.json`
- `tests/fixtures/tme_semantic_formal_p2/dev_ids.json`
- este relatório.

**Arquivos preexistentes modificados: nenhum.** Os novos arquivos foram ajustados durante a implementação; nenhum arquivo rastreado da base foi alterado. Os recibos locais de testes são artefatos ignorados, não uma execução do piloto.

## 3. Preservação do baseline e dos checkers

Foram comparados hashes de **557 arquivos preexistentes** monitorados: código, checkers, testes, pautas, toolchain/manifest e runner de P1. Todos permaneceram iguais. A suíte anterior de 1.202 testes foi reexecutada, incluindo os 55 casos P2 do checker-first e a comparação das 19 obrigações preservadas. Outros 39 casos textuais P2 comparam integralmente bridge e assessment entre o wrapper current novo e `primary_audit`; o modo current não chama extractor.

A pauta continua com máximo 20, a=5, b=7, c=8, estratégias e dependências originais. O fortalecimento das quatro obrigações do commit base não foi reimplementado: `StrongP2Checks` é importado diretamente. Gates de atribuição/representação e elegibilidade formal vivem no adaptador novo; não mudam o comportamento de TME_CURRENT.

## 4. Tabela das 23 obrigações

A rota abaixo é decisão do registry, não do LLM. Checkers herdados são executados dentro de `StrongP2Checks`; o certificado composto e o checker de integralidade são os do commit base.

| obrigação | cobertura | rota efetiva | subjects aceitos | checker primário |
|---|---|---|---|---|
| `a.pair_sum` | DETERMINISTIC_STRONG | DETERMINISTIC | `pair_sum`, `pairs`, `placement` | `P2Checks.a` |
| `a.line_sum` | DETERMINISTIC_STRONG | DETERMINISTIC | `line_sum` | `P2Checks.a` |
| `a.pairs` | DETERMINISTIC_STRONG | DETERMINISTIC | `pairs`, `placement` | `P2Checks.a` |
| `a.placement` | DETERMINISTIC_STRONG | DETERMINISTIC | `placement` | `P2Checks.a` |
| `a.complete_configuration` | DETERMINISTIC_STRONG | DETERMINISTIC | `placement` | `P2Checks.a` |
| `b.balance_relation` | DETERMINISTIC_STRONG | DETERMINISTIC | `balance_relation` | `P2Checks.b` |
| `b.sum_formula` | FORMAL_STRONG | FORMAL | `sum_formula` | `P2Checks.b` |
| `b.integral_sum` | DETERMINISTIC_STRONG | DETERMINISTIC | `integral_sum` | `check_integrality` |
| `b.modular_condition` | DETERMINISTIC_STRONG | DETERMINISTIC | `modular_condition` | `P2Checks.b` |
| `b.centers` | FORMAL_STRONG | FORMAL | `centers` | `P2Checks.b` |
| `b.admissible_center` | FORMAL_STRONG | FORMAL | `admissible_center` | `P2Checks.b` |
| `b.center_sums` | FORMAL_STRONG | FORMAL | `center_sums` | `P2Checks.b` |
| `b.sum_at_five` | FORMAL_STRONG | FORMAL | `sum_at_five` | `P2Checks.b` |
| `b.realizable_1` | DETERMINISTIC_STRONG | DETERMINISTIC | `realizable_1` | `P2Checks.b` |
| `b.realizable_5` | DETERMINISTIC_STRONG | DETERMINISTIC | `realizable_5` | `P2Checks.b` |
| `b.realizable_9` | DETERMINISTIC_STRONG | DETERMINISTIC | `realizable_9` | `P2Checks.b` |
| `c.max_center` | DETERMINISTIC_STRONG | DETERMINISTIC | `max_center` | `P2Checks.c` |
| `c.max_sum` | DETERMINISTIC_STRONG | DETERMINISTIC | `max_sum` | `P2Checks.c` |
| `c.pairs` | DETERMINISTIC_STRONG | DETERMINISTIC | `pairs` | `P2Checks.c` |
| `c.pair_permutations` | COMPOSITE_STRONG | COMPOSITE | `pair_permutations` | `P2CompositeCountingChecker` |
| `c.pair_orientations` | COMPOSITE_STRONG | COMPOSITE | `pair_orientations` | `P2CompositeCountingChecker` |
| `c.total` | FORMAL_STRONG | FORMAL | `total` | `P2Checks.c` |
| `c.counting_product` | COMPOSITE_STRONG | COMPOSITE | `counting_product` | `P2CompositeCountingChecker` |

Os seis FORMAL_STRONG preservam as guardas de construção Lean anteriores; não há tentativa fictícia quando uma delas não é satisfeita. As dependências matemáticas/pedagógicas continuam nos checkers congelados (por exemplo, base modular ou integralidade + relação/fórmula para centers). Não se exige pré-crédito de c.pairs/maximum para os checkers de contagem. As três categorias de cobertura são as da matriz base; “FORMAL” no registry não é por si só status de prova.

## 5. Testes

A tabela abaixo vem dos JUnit XML das execuções finais, sem contar reruns de desenvolvimento:

| suíte | total | passed | failed | errors | skipped |
|---|---:|---:|---:|---:|---:|
| novos testes locais `test_tme_semantic_formal_p2.py` | 154 | 154 | 0 | 0 | 0 |
| novos testes reais `test_tme_semantic_formal_p2_lean.py` | 17 | 17 | 0 | 0 | 0 |
| regressões/checkers anteriores | 1.202 | 1.202 | 0 | 0 | 0 |
| **total** | **1.373** | **1.373** | **0** | **0** | **0** |

Cobertura local: todos os 23 IDs com checker real determinístico/composto ou diagnóstico de ausência formal; registry/route override; schema sem dados de nota; spans e offsets locais; IDs inventados; mutação da fonte; seis estados de contexto; mentira do modelo sobre contexto; tipo/subject incompatíveis; prosa vinculada à notação; preservação de resultado errado; argumento combinatório insuficiente versus falso; evidence omitida sem crédito; ausência de checker; conflito incluído e omitido pelo extractor; interpretações contraditórias; duplicação de fonte; max_of; score numérico com preservação de crédito independente em falha técnica; fallback idêntico ao current; baseline sem chamada de modelo; runner source-only e recusa de caminhos selados/rotulados antes de abrir arquivos.

Nos testes do extractor, o provider é controlado e fornece candidatos estruturados; **a matemática não é mockada**. Um teste local injeta falha do certificado finito para validar isolamento da incerteza. Dois testes Lean injetam táticas inadequadas em memória, mas executam o processo Lean real; nenhum resultado, stdout ou compilador é simulado. Os checkers no disco não são alterados.

Seleção de regressões: os mesmos módulos de pauta, bridges P1–P5, C1, integração aceita, semantic claims/sufficiency, semântica por obrigação/ID, student proof semantics e os dois módulos P2 checker-first da validação anterior. P3–P5 são apenas regressões preexistentes de infraestrutura compartilhada; nenhuma funcionalidade nova foi criada para eles. Não se executou a suíte inteira indiscriminadamente.

Comandos de testes usados (com ambiente `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH="$PWD/app"`, `CONFIA_TME_SEMANTIC_ENABLED=0` e Python `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`):

```bash
python -m pytest tests/test_tme_semantic_formal_p2.py \
  -q -p no:cacheprovider \
  --basetemp=/private/tmp/p2-semantic-formal/unit-final-2 \
  --junitxml=/private/tmp/p2-semantic-formal/unit-final-2.xml

python -m pytest tests/test_tme_semantic_formal_p2_lean.py \
  -q -s -p no:cacheprovider \
  --basetemp=/private/tmp/p2-semantic-formal/lean-final \
  --junitxml=/private/tmp/p2-semantic-formal/lean-final.xml

python -m pytest \
  tests/test_pauta_engine.py \
  tests/test_tme2_p1_pauta_bridge.py tests/test_tme2_p2_pauta_bridge.py \
  tests/test_tme2_p3_pauta_bridge.py tests/test_tme2_p4_pauta_bridge.py tests/test_tme2_p5_pauta_bridge.py \
  tests/test_tme_semantic_formal_c1.py tests/test_tme_semantic_formal_c1_fix.py tests/test_tme_semantic_formal_c1_lean.py \
  tests/test_tme_accepted_integration.py tests/test_tme_hybrid_grader.py tests/test_semantic_claims.py \
  tests/test_obligation_semantic.py tests/test_evidence_id_semantic.py tests/test_semantic_sufficiency.py \
  tests/test_student_proof_semantics.py tests/test_tme_p2_checker_first.py tests/test_tme_p2_checker_first_lean.py \
  -q -p no:cacheprovider \
  --basetemp=/private/tmp/p2-semantic-formal/regression \
  --junitxml=/private/tmp/p2-semantic-formal/regression.xml
```

Os comandos integrais, com executável, ambiente e redirecionamento de logs, estão em `commands.json` nos recibos locais. Novas reproduções devem usar diretórios temporários diferentes para preservar os recibos desta entrega.

## 6. Lean real e estados epistemológicos

- Lean **4.28.0**, plataforma `arm64-apple-darwin24.6.0`, commit `7e01a1bf5c70fc6167d49c345d3bf80596e9a79b`, Release.
- Mathlib **v4.28.0**, revisão **`8f9d9cff6bd728b17a24e163c9402775d9e6a365`**, manifest original.
- Imports, renderers, táticas de produção e ciclo de prova/refutação são os existentes. Não foi criado checker ou teorema de produção novo nesta fase.

| grupo de teste novo | casos | resultado observado |
|---|---:|---|
| `test_all_six_formal_routes_compile_the_bound_claim` | 6 | FORMAL_VERIFIED com compiled=true para sum_formula, centers, admissible_center, center_sums, sum_at_five e total |
| `test_three_composites_real_arithmetic_and_refutation` | 6 | três COMPOSITE_VERIFIED com aritmética FORMAL_VERIFIED; três COMPOSITE_FAILED com aritmética FORMAL_REFUTED e negação compilada |
| `test_false_formal_claim_is_refuted_not_unknown` | 2 | centro 2 e soma 14 para centro 5: FORMAL_REFUTED, sem crédito |
| `test_unrendered_formal_claim_is_not_attempted_and_not_credited` | 1 | total:384 sem igualdade: FORMAL_NOT_ATTEMPTED, nenhum subprocesso formal para esse claim |
| `test_real_failure_diagnostics_survive_projection` | 2 | FORMAL_UNPROVED/UNSOLVED_GOALS com skip; FORMAL_ERROR/UNKNOWN_IDENTIFIER com identificador deliberadamente inexistente |

Os 17 casos passaram; 16 casos exercitam processos Lean reais, enquanto o caso sem igualdade verifica precisamente a ausência de tentativa. As provas verdadeiras registraram compilação; os claims falsos registraram prova da negação, não mera ausência de prova positiva. A igualdade/formalização exata, fonte e offsets constam dos recibos `checker_result` e das cópias `.lean`.

Stdout de provas bem-sucedidas: vazio. Tentativas positivas dos claims falsos: diagnóstico de goals não resolvidos, seguido da refutação compilada. Controle inconclusivo: `UNSOLVED_GOALS`, sem prova e sem refutação. Controle técnico: `Unknown identifier p2_semantic_test_missing_identifier`; não foi classificado como falsidade matemática. Stderr dos novos processos Lean: vazio; os diagnósticos vieram no stdout.

Estados preservados na saída: FORMAL_VERIFIED, FORMAL_REFUTED, FORMAL_UNPROVED, FORMAL_NOT_ATTEMPTED, FORMAL_ERROR; DETERMINISTIC_VERIFIED, DETERMINISTIC_FAILED; COMPOSITE_VERIFIED, COMPOSITE_INCOMPLETE, COMPOSITE_FAILED; CONTEXT_REJECTED e CONFLICTING_EVIDENCE. `mathematical_refutation` distingue falsidade de insuficiência/representação. Erro de subchecker composto conserva seu status interno e `technical_uncertainty`, sem inventar uma refutação do composto.

## 7. Três checkers compostos

| obrigação | caso matematicamente e estruturalmente suficiente | aritmética verdadeira mas argumento insuficiente | caso falso com Lean real |
|---|---|---|---|
| c.pair_permutations | 4!=24 | 24; 2^3*3=24 | 4!=20 |
| c.pair_orientations | 2^4=16 | 16; 4+12=16 | 2^4=8 |
| c.counting_product | 24*16=384 | 384; 12*32=384 | 24*16=364 |

Os três recebem a mesma família de checkers fortalecidos do commit base. `subchecks` conserva aritmética/formalização, certificado de enumeração e bijeção (24 × 16 = 384 estados entre 40.320 candidatos), e relação estrutural escrita. Nenhum novo certificado matemático foi gerado pelo modelo. Insuficiência não sobrepõe falsidade nem permite crédito por mera coincidência numérica. Os 125 testes checker-first e os nove controles Lean anteriores também foram reexecutados dentro das 1.202 regressões.

## 8. Piloto DEV preparado — não executado

Foram preparados oito casos sintéticos source-only, sem notas, rótulos de correção, baseline histórico ou gold. A seleção cobre pares, integralidade, fórmula, contagem, erro escrito, contexto, conflito e argumento parcial. A preparação/teste de carregamento não chama `evaluate` sobre esse dataset nem o provedor real. Não há resultados de piloto nesta entrega.

Comandos exatos para execução futura, a partir do worktree P2:

```bash
cd /Users/LinMarcolino/Documents/confia-lean-auditor-tme-semantic-formal-p2

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0 \
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python \
  scripts/evaluation/run_tme_semantic_formal_p2.py \
  --mode tme_current \
  --dataset tests/fixtures/tme_semantic_formal_p2/dev_sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_p2/dev_ids.json \
  --output-dir artifacts/evaluations/tme_p2_semantic_formal_dev_01/current \
  --model gpt-6.1-sol --reasoning-effort medium

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/app" CONFIA_TME_SEMANTIC_ENABLED=0 \
/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python \
  scripts/evaluation/run_tme_semantic_formal_p2.py \
  --mode tme_semantic_formal \
  --dataset tests/fixtures/tme_semantic_formal_p2/dev_sources.json \
  --ids-file tests/fixtures/tme_semantic_formal_p2/dev_ids.json \
  --output-dir artifacts/evaluations/tme_p2_semantic_formal_dev_01/semantic_formal \
  --model gpt-6.1-sol --reasoning-effort medium
```

O runner requer saída nova (`exist_ok=False`), rejeita caminhos com gold/holdout antes de leitura e valida um schema de entrada estritamente source-only. Ambos os modos usam Lean habilitado; current não faz chamada ao extractor. A execução futura do modo semântico usará a configuração de credenciais existente, sem copiar credenciais para artefatos.

Cada caso salva extracted evidence, mapping, rota sugerida/efetiva e override, checker result, subchecks, awards/credits, rejected evidence, conflicts, score e assessment, fallback, incerteza técnica, model/reasoning, SHA Git e hashes do código experimental/congelado, registry, pauta, configuração do extractor, runner, toolchain, manifest e inputs. O extractor também registra hashes de payload/schema e uso de tokens quando houver resposta real. O SHA por si só não substitui os hashes de arquivos ainda não commitados.

## 9. Evidências e SHA

Base e HEAD ao término: **`6dfab47d88c83c528b84a62b0a3877a8eda47105`**. As evidências locais de validação ficam em [summary.json](../../artifacts/evaluations/tme_p2_semantic_formal_implementation_01/summary.json), com logs/JUnit das três suítes, comandos completos, hashes de preservação e 17 recibos novos Lean no mesmo diretório. Arquivos `.lean` de prova/refutação foram copiados junto dos recibos, sem remover suas referências originais. Esses artefatos são ignorados pelo Git.

Não houve commit ou stage. Os documentos anteriores permanecem como registros históricos da fase checker-first; não foram reescritos para atribuir-lhes esta implementação.

## 10. Git status e limite da conclusão

`git status --short` final:

```text
?? app/confia_lean_auditor/experimental/tme_semantic_formal_p2/
?? docs/audits/TME_P2_SEMANTIC_FORMAL_IMPLEMENTACAO_01.md
?? scripts/evaluation/run_tme_semantic_formal_p2.py
?? tests/fixtures/tme_semantic_formal_p2/
?? tests/test_tme_semantic_formal_p2.py
?? tests/test_tme_semantic_formal_p2_lean.py
```

`git diff` e `git diff --cached` vazios para arquivos preexistentes. Checkers matemáticos, pauta, pesos, P1 e TME_CURRENT preservados.

A implementação está validada estruturalmente com providers de extração controlados e verificadores reais. Qualidade/recall da interpretação por `gpt-6.1-sol` ainda não foram medidos: dependem do piloto autorizado em etapa posterior. O modo é textual e conservador diante de representações não suportadas; preserva rejeições e incerteza em vez de atribuir crédito diretamente ao LLM. **O piloto permanece não executado.**
