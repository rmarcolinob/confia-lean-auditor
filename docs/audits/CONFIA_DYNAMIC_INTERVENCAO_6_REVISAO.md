# ConfIA DYNAMIC — Revisão da Intervenção 6

Data: 26/11/2026. Worktree: `artifacts/worktrees/confia-dynamic-development`. Branch: `codex/dynamic-development`. HEAD inicial: `d40a7b08ff5eef60b012f382e64fa82a604c05fc`.

**Decisão: não publicar a Intervenção 6 nesta revisão.** Foram reproduzidos três defeitos na projeção pedagógica. Ausência de campos numéricos de nota não garante ausência de pontuação nos textos públicos. Citações válidas também não garantem que uma pista respeite o nível solicitado. O núcleo DYNAMIC é efetivamente reutilizado, mas essas saídas precisam de correção antes da consolidação.

Os contraexemplos abaixo são respostas simuladas deliberadamente inadequadas, válidas quanto ao schema e com evidências literais. Não são incidentes de um provider real nem estimativas de sua frequência. Demonstram caminhos atualmente aceitos pelo servidor e persistidos no histórico. Nenhum dado real de estudante ou chamada paga foi usado.

## Achados que impedem publicação

### R1 — Pontos internos podem aparecer nos títulos públicos

Prioridade P1. Em `dynamic/study_service.py:281`, `view()` copia diretamente `rubric.criteria[].title` para `packages[].objectives[].title`. `study_feedback.project()` também copia esse título para `findings[].objective` (`study_feedback.py:30`). A interface renderiza ambos (`static/dynamic-self-study.js:46` e `:70`).

Reprodução: o provider de rubrica simulado devolveu o título `Desenvolvimento: máximo 3 pontos; etapa inicial 1,5 pontos`, coerente com o máximo e o nível interno dessa rubrica de teste. A preparação aceitou o pacote e a consulta GET retornou o texto com os pontos. Não foi necessário acessar um campo privado nem um endpoint docente.

O teste existente `no_grades()` verifica nomes de campos recursivamente; não verifica texto livre. O prompt pede títulos neutros, mas o servidor não impõe essa propriedade. Portanto, a garantia anterior deve ser limitada: **os campos estruturados de pontuação estão excluídos; a divulgação textual de pesos/pontos ainda é possível**. Não há evidência de criação de uma nota oficial neste caso.

Correção mínima proposta: separar os rótulos pedagógicos públicos dos textos internos da rubrica, validar as saídas geradas antes de expô-las e manter como indisponível/substituir por rótulo neutro uma descrição que declare nota, máximo ou faixa de pontos. Aplicar a mesma fronteira na preparação, no relatório e na consulta do histórico. Não remover números de enunciados ou evidências matemáticas do aluno. Não modificar pesos ou decisões do engine.

### R2 — Pista de nível 2 aceita nota e resolução completa

Prioridade P1. `study_feedback.generate_help()` (`study_feedback.py:58`) verifica schema, IDs e citações. Não verifica o conteúdo de `message`/`limitations` contra a política do nível. `study_service.help_level()` (`study_service.py:247`) protege a ordem das solicitações e exige consentimento no nível 4, mas publica integralmente o conteúdo aceito do provider no nível 2.

Reprodução: para `2x+6=18`, com solução parcial e uma citação literal válida, o provider simulado devolveu no nível 2: `Sua nota é 1,5/3. Solução completa: 2x+6=18; 2x=12; x=6. Resposta final: x=6.` A requisição foi aceita e uma consulta GET posterior retornou o mesmo texto em `attempts[].help[].content.items[].message`. A interface renderiza o conteúdo em `dynamic-self-study.js:49`.

A pontuação dessa mensagem é produzida pelo provider simulado; não foi lida de um campo público do engine. O defeito é aceitar uma nota textual e uma resolução antecipada num contexto que proíbe ambas. A inexistência de soluções de referência no payload dos níveis 2–3 não impede o modelo de produzir sua própria resolução completa.

Correção mínima proposta: validar a resposta pedagógica antes de persistir/publicar, incluindo mensagem, limitações e títulos; bloquear declarações de nota e conteúdo incompatível com o nível. Usar uma orientação conservadora quando a validação não puder estabelecer o escopo, ou manter a pista indisponível. Não basta reforçar o prompt ou esconder o texto no frontend. Uma checagem lexical isolada não prova ausência de resolução antecipada; começar com formatos delimitados para as pistas, exemplos negativos e revisão supervisionada da adequação. Manter o nível 4 explicitamente solicitado e sem nota, inclusive no histórico e em futuras exportações.

### R3 — Erro matemático com crédito parcial é reduzido a incompletude

Prioridade P1 pedagógica. Em `study_feedback.project()` (`study_feedback.py:22`), `sufficiency=PARTIAL` sempre vira `state=PARTIAL` com a mensagem de completar/explicar. O `finding=MATHEMATICAL_ERROR` só é usado no ramo `NOT_SATISFIED`. Isso perde uma distinção já produzida pelo núcleo.

Reprodução: ambos os avaliadores simulados apontaram crédito parcial autorizado com erro matemático no trecho `Subtraio 6: 2x=12. Depois divido: x=7.`. A saída pública foi apenas `Há desenvolvimento aproveitável, mas este objetivo ainda precisa ser completado ou explicado.`. A projeção não sinalizou o erro identificado.

Correção mínima proposta: preservar separadamente o desenvolvimento aproveitável e o tipo de achado matemático, com evidência e mensagem breve. Um critério pode ser parcialmente atendido e conter erro; não o converter em zero nem apagar o crédito parcial. Acrescentar um campo diagnóstico compatível/default para relatórios antigos, se necessário, e usar esse achado na comparação das tentativas e nas pistas. Não publicar indiscriminadamente a justificativa longa do provider, pois ela pode conter a solução completa.

## Revisão funcional e integração dos contextos

| Requisito | Evidência e resultado |
| --- | --- |
| Problema escolar ou próprio | `study_service.CATALOG`, `create()` e seletor em `dynamic-self-study.js`; cinco temas escolares e entrada livre. |
| Texto, fotografia e PDF | `study_capture.receive()` usa a captura existente; originais, páginas e transcrições ficam preservados. Testes de fotografia, PDF com duas páginas e quatro originais. |
| Conferência | `confirmed()`, `confirm_reading()` e `confirm_package()` exigem versão/hash e manifestação explícita. OCR não é confirmação humana. |
| Rubrica formativa | `StudyRubric.status=PROVISIONAL_FORMATIVE`; confirmação do aluno é da interpretação, sem aprovação docente artificial. |
| Reutilização matemática | `evaluate()` chama `DynamicSolutionGrader.grade`, `blind_input`, `review_phase`, `compare_review` e `reconcile_criteria`; não há outro motor. |
| Nota oficial | O contexto não cria `FinalCorrection`, nota escolar ou adjudicação docente. Campos estruturados de pontuação ficam privados; R1/R2 impedem afirmar ausência completa de notas na saída textual. |
| Evidências e incertezas | Offsets/texto/hash e estados `UNCERTAIN`/`TECHNICAL_ERROR` estão presentes. R3 perde o erro quando há crédito parcial. |
| Progressividade | Há sequência 2→3→4 e consentimento adicional; R2 demonstra que a política do conteúdo não é imposta. |
| Histórico | Tentativa analisada não é editada pelo gateway; pacote e revisão são fixados. Novo enunciado exige preparação nova; comparações apenas entre o mesmo pacote. |
| Isolamento | Sessão de aluno ativa, autoria de estudo e fontes, bloqueio de professor/outro aluno, proteção inclusive no modo legado. Não foi encontrada abertura de dados de outro estudante nos testes executados. |
| Exportação | Não existe exportação própria de relatório SELF_STUDY. Originais têm endpoint protegido. A API GET já é suficiente para reproduzir os vazamentos textuais; uma exportação futura deve reutilizar a mesma projeção corrigida. |

Os três contextos mantêm políticas distintas:

| Contexto | Entrada e orquestração | Núcleo e política de saída |
| --- | --- | --- |
| Professor corrigindo atividade | Routers DYNAMIC/TME, `AuditService`, `DynamicReviewService`, `ReconciliationService` | Grader, revisão independente e reconciliação; rubrica aprovada, créditos/dependências e decisão humana quando exigida. |
| Aluno em atividade institucional | `school_service.submit` e versões da atividade | Mesmos serviços; tentativas, divulgação de nota e feedback respeitam política docente e liberação vinculada à correção. |
| Aluno em estudo autônomo | `study_service.evaluate`, com pacote privado provisório | Mesmas funções matemáticas; armazenamento privado por tentativa e projeção qualitativa, sem simular privilégio docente ou criar nota oficial. |

O autônomo reutiliza as funções do núcleo diretamente; não é o mesmo envelope institucional de AuditRun/finalização. Essa distinção é explícita e não constitui outro motor matemático. Não houve execução Lean no estudo autônomo; `formal_verification_performed=False`. Concordância de pareceres não é prova formal nem validação científica.

## Contratos e cobertura ausente

Os contratos novos são `self-study-source.v1`, `self-study-report.v1` e `self-study-feedback.v1`. As extensões compartilhadas são o tipo de fonte `self_study`, referências de PDF/múltiplos originais, limites de recebimento e autorização. Leitura de fontes históricas, rubricas e cálculo matemático permanecem sob as regressões existentes. A revisão não alterou código de produção, regras matemáticas, fixtures históricas ou persistência.

Os dois testes indisponíveis são skips em `tests/test_tme_model_compat.py`, não deseleções:

- `test_real_smoke_dry_run_separates_semantic_hashes_from_transport`: compara hashes semânticos e de transporte sobre o pacote DEV congelado, em dry-run sem API.
- `test_transport_builder_does_not_weaken_holdout_guard`: verifica que o plano rejeita IDs fora do conjunto DEV congelado.

Arquivos exigidos, ausentes neste worktree:

- `artifacts/evaluations/tme_semantic_understanding_01/dev_ids.json`, SHA-256 esperado `d6ae59f0a2d766f9c7541b2d8341fb6aa56ee8c1fdf55200131c842087d1d140`.
- `artifacts/evaluations/tme_semantic_diag_01/cases_analysis.json`, SHA-256 esperado `a3432c6aa1fff0f68018e609989a26b23b7b6f5d8e86e5c586801f2445d0fe79`.

As expectativas são de `scripts/evaluation/evaluate_tme_model_ablation.py:34`. Não recriei o pacote, não o substituí por fixture inventada e não procurei/copiei dados experimentais para o Git. A lacuna limita a reprodução daquela ablação histórica; não demonstra falha do estudo autônomo. Os testes de transporte com doubles locais continuam disponíveis. O teste Lean anteriormente deselecionado é outro caso, com aprovação isolada documentada na I5; não foi repetido nesta revisão.

A ocorrência intermitente da P3 permanece aberta: a auditoria sintética terminou `FAILED/AUDITOR_FAILED` e o HTTP 409 posterior impediu a confirmação. A exceção inicial não foi preservada pelo serviço histórico. Repetições que passam não estabelecem sua causa e não apagam o registro anterior, preservado em `artifacts/qa/dynamic-intervention6/regression-initial.log` e no relatório da I6.

## Testes desta revisão

| Conjunto executado | Resultado |
| --- | --- |
| Regressão Python ampliada dos três contextos, segurança, captura e contratos TME² | **739 aprovados, 2 skips, 321,62 s** |
| JavaScript completo, incluindo navegação, consentimento e histórico | **613 aprovados, 2,47 s** |
| Provas adicionais de isolamento, origem, autoria e integridade | **3 aprovadas, 6,96 s** |
| Contraexemplos pedagógicos R1–R3 | **3 falhas reproduzidas, 6,73 s** |
| `git diff --check` | Aprovado |

A regressão ampliada inclui o teste `test_stale_invalidated_failed_and_new_audit_block_closure`, que passou nesta execução. Isso não determina a causa da ocorrência anterior da P3. Os dois skips foram novamente confirmados, exatamente nos casos de pacote DEV ausente descritos acima.

As provas adicionais bloquearam consulta/análise/pista de outro aluno, acesso genérico ao snapshot de outro autor, leitura docente do estudo privado, autoria forjada, mutação com origem diferente e leitura de análise adulterada. A consulta legítima conserva `Cache-Control: no-store`. Script: `artifacts/qa/dynamic-intervention6-review/test_review_security.py`.

Os três contraexemplos de R1–R3 falham nas asserções do comportamento exigido; são evidência de defeito, não testes aprovados. Script reproduzível: `artifacts/qa/dynamic-intervention6-review/test_review_probes.py`. Os testes usam as fixtures de autenticação e providers simulados existentes, sem alterar fixtures versionadas ou usar dados de estudantes.

Comandos executados a partir deste worktree, usando o interpretador validado Python 3.9.6:

```sh
env -u OPENAI_API_KEY CONFIA_DYNAMIC_LLM_ENABLED=0 CONFIA_SEMANTIC_LLM_ENABLED=0 PYTHONPATH=app PYTHONDONTWRITEBYTECODE=1 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q -rs --tb=short -p no:cacheprovider tests/test_dynamic*.py tests/test_submissions.py tests/test_transcriptions.py tests/test_recognition*.py tests/test_core_auth.py tests/test_core_institutional.py tests/test_assessments.py tests/test_capture_contracts.py tests/test_capture_static.py tests/test_tme_full_exam.py tests/test_tme_finalization.py tests/test_tme_question_audit.py tests/test_tme_human_confirmation.py tests/test_tme_model_compat.py
node --test tests/js/*.cjs
env -u OPENAI_API_KEY CONFIA_DYNAMIC_LLM_ENABLED=0 CONFIA_SEMANTIC_LLM_ENABLED=0 PYTHONPATH=app PYTHONDONTWRITEBYTECODE=1 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider artifacts/qa/dynamic-intervention6-review/test_review_probes.py artifacts/qa/dynamic-intervention6-review/test_review_security.py
git diff --check
```

Logs completos em `artifacts/qa/dynamic-intervention6-review/{regression,probes,security,javascript}.log`, ignorados pelo Git.

Os testes JavaScript incluem navegação, apresentação dos módulos, fluxo institucional, progressão/consentimento e leituras editadas não salvas. A demonstração visual anterior permanece válida como evidência do percurso com mocks; não houve nova validação visual nesta revisão. Passar nos testes existentes não cobre as respostas semanticamente inadequadas dos três novos contraexemplos.

## Arquivos e estado do Git

Esta revisão acrescenta apenas este relatório e evidências sintéticas locais em `artifacts/qa/dynamic-intervention6-review/` (ignoradas pelo Git). Não corrigi o código dos defeitos R1–R3, de acordo com a orientação de documentar e propor antes de publicar uma intervenção com bloqueios.

Continuam pendentes os 21 arquivos da I6 já inventariados no relatório `CONFIA_DYNAMIC_INTERVENCAO_6_ESTUDO_AUTONOMO.md`: `dynamic/study_{models,capture,service,feedback,router}.py`, `dynamic/provider.py`, autorização, reconhecimento, contratos/armazenamento/limites de submissões, registro do router, interface e testes. A lista detalhada por arquivo está nesse relatório. Nenhuma alteração de origem desconhecida apareceu no inventário.

Nenhum commit ou push foi executado nesta revisão. O último commit local continua sendo a I5 `d40a7b08ff5eef60b012f382e64fa82a604c05fc`; não constitui publicação da I6. A main permanece em `8fde840d95fa4df0553b915d7b60301c9892aa65`. A tag anotada `SPECIALIZED-TME2-RC1` permanece com objeto `0c64e318a26e21f71fe3097c66ee17a5206dd8a3`, apontando para `c03403fe5b83d9db9df172882bd69af3dfa2d027`.

## Correção mínima e primeiro piloto

A próxima intervenção deve limitar-se à fronteira pedagógica pública: corrigir R1–R3, acrescentar os contraexemplos como regressões permanentes, testar consulta de histórico e retomada, e repetir a matriz dos três contextos. Manter pontuações, rubricas, dependências, verificadores, reconciliação matemática e dados históricos intactos. Não é necessário redesenhar o DYNAMIC.

Depois dessas correções e de sua revisão, preparar um piloto supervisionado com autorização explícita de uso dos providers e limite de custo. Começar com um pequeno conjunto de problemas independentes da Educação Básica, anonimizados, incluindo respostas corretas, parciais, incorretas, métodos alternativos e evidência insuficiente. Manter o gold inacessível ao corretor.

Uma amostra inicial operacional pode conter 25 soluções: cinco temas escolares, cada um com uma solução correta, parcial, incorreta, alternativa e inconclusiva. Isso é um smoke supervisionado, não uma amostra suficiente para estimar validade científica. Dois avaliadores humanos devem registrar suas análises independentemente e resolver discordâncias fora do ambiente do corretor. Comparar a versão digitada com a fotografia da mesma solução ajuda a distinguir erro de OCR de erro de julgamento.

Separar as medições: fidelidade da transcrição (incluindo sinais, expoentes, frações e diagramas), qualidade dos critérios provisórios, decisão por critério, adequação da explicação à idade, revelação antecipada de resposta, classificação de incerteza, custo e latência por etapa. Registrar também divergências por critério, falsos apontamentos de erro, abstenções e taxa de pistas rejeitadas. Professor deve conferir originais/transcrições e revisar as primeiras saídas antes da exposição aos estudantes. Estudo autônomo não recebe nota escolar; atividade institucional mantém suas políticas próprias.

Critérios para preparar `DYNAMIC-RC1`: corrigir os três bloqueios com regressões; registrar código/configuração/modelos/prompts e hashes; manter isolamentos e versões; executar um smoke supervisionado autorizado de OCR/LLM reais; documentar os resultados e limites, os skips de cobertura e a ocorrência P3 ainda sem causa determinada. Um smoke real não valida cientificamente a correção: a avaliação independente e a avaliação pedagógica devem continuar separadas do congelamento técnico. **A I6 ainda não está pronta para consolidar a candidata na forma atual.**
