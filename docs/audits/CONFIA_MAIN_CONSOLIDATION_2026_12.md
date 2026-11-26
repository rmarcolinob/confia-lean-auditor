# Consolidação da plataforma para a main — 26/11/2026

## Estado e alcance

Integração preparada em `codex/main-consolidation-dec10`, criada a partir da `main` `8fde840d95fa4df0553b915d7b60301c9892aa65`. O merge na main depende da aprovação humana do pull request. Este relatório não declara que a main já foi atualizada.

A base funcional é `codex/dynamic-development` em `fc6f271ab4f484f48609ddde67faa84b0ac690ca`. A comparação considerou ancestralidade, conteúdo e alterações não registradas, não a data dos nomes das branches. O código de aplicação difere dessa base em três arquivos de navegação (`static/index.html`, `static/login.html` e `static/login.js`) e na classificação diagnóstica em `core/public_audit.py`. Não houve alteração matemática, de rubrica, regras de autorização, persistência ou estruturas dos contratos; o adaptador restaura um código de erro de integridade já previsto pelo contrato existente.

## Integrações rastreáveis

| Origem | Conteúdo incorporado | Registro na integração |
| --- | --- | --- |
| `codex/dynamic-development` / `fc6f271` | SPECIALIZED, diagnósticos, I1–I6B, interface dos três módulos, captura, atividades, TutorIA e colaboração | Merge `bace9da` |
| `codex/interface-review` / `03cba8b` | Marca estática no cabeçalho compartilhado de Aluno/Gestão; documento de estado da interface | Merge `a0836cf` |
| Diff aprovado não registrado do worktree de interface | Entrada direta após login conforme papel devolvido pelo servidor, recarregando o shell autenticado; regressões de papéis | Commit `94c9feb` |
| Preparação DYNAMIC-RC1 não registrada no worktree DYNAMIC | 18 arquivos preservados byte a byte, manifesto, evidências, plano e guardas do smoke; verificador histórico adicional | Commit `8ee1830` |
| Regressão global de reconhecimento | Schema JSON derivado do benchmark sincronizado com o contrato multipágina existente; sem mudança no modelo de execução | Commit `001c5c9` |
| Política permanente e instalação | Main/PRs/tags científicas, instruções autenticadas, constraints na instalação e regressões JavaScript no CI | Commit `727d5ce` |
| Regressão global de integridade | Restabelecida a categoria pública de fonte corrompida rejeitada antes do roteador, preservando HTTP 409 e bloqueio do motor | Commit `d868c05` |
| Regressão estática do caderno | Teste distingue controles sticky TME do workspace geral do aluno; CSS preservado | Commit `dd61720` |

I1 `87f7416`, I2 `54a9a96`, I3 `2684741`, I4 `57517f3`, I5 `d40a7b0`, I6/6B `a8692e5` e sua documentação `fc6f271` permanecem na ancestralidade, sem squash ou reescrita. A linha DYNAMIC já contém os commits das integrações de dezembro, dos módulos institucionais e do caderno. As outras branches não foram movidas. Alterações não registradas nos worktrees de origem foram preservadas.

## Funcionalidades presentes

| Área | Implementação efetiva | Limites da evidência |
| --- | --- | --- |
| SPECIALIZED | ITA/TME², Semantic B, verificações determinísticas/Lean, fallback mínimo, PautaEngine, AuditService e diagnóstico de revisão | RC1 experimental; Lean parcial; gold independente pendente |
| DYNAMIC Professor | Problemas novos, rubricas versionadas/aprovadas, níveis de crédito/dependências, Grader/Reviewer/Reconciliation, adjudicação e relatório | Providers simulados nesta validação; não é validação matemática independente |
| Aluno institucional | Publicações fixadas, matrícula, tentativas, texto/fotografias, confirmação de leitura e divulgação docente | Preserva políticas de prova/lista e isolamento |
| Estudo autônomo | Problema próprio/catálogo, critérios provisórios, histórico e feedback progressivo sem nota | API pública sem pontuação interna; OCR/LLM reais ainda dependem de smoke autorizado |
| Captura | Escrita digital, imagens/PDF, originais, segmentação, transcrições e confirmações versionadas | Qualidade de OCR e dispositivos físicos ainda precisa de validação |
| TutorIA | Navegação, catálogo, prática, caderno e assistente existentes | Conteúdos, trilhas, progresso e parte do feedback continuam explicitamente demonstrativos |
| Gestão | Indicadores persistidos e filtros institucionais existentes | `management/router.py` consulta `teacher_decisions`; não agrega automaticamente todas as decisões de `tme/human_decisions.py` |
| Navegação/autenticação | Login direto, sessão preservada, marca compartilhada sem link/foco, retorno pelo menu, links diretos e controle de papéis | A escolha visual de módulo não amplia permissões |

## Linhas que permanecem separadas

- `origin/luis_ocr` (`0e44685`): 11 arquivos/1.216 linhas para GLM-OCR/Ollama, uploads e testes. `uploads/router.py::upload_and_audit` chama `execute_audit` diretamente sobre OCR não conferido, acessível a professor/aluno; o aviso `AUTOMATIC_AUDIT_OF_UNREVIEWED_OCR` é explícito. `uploads/service.py::recognize_upload` retorna leitura/hashes, mas não cria o vínculo de originais, transcrição aceita e AuditRun utilizado pelas intervenções I4–I6B. Não há integração com `study_service` nem as políticas públicas de feedback sem nota. A busca de PRs abertos/fechados por `head:luis_ocr` no remoto não retornou PR para essa linha. O adaptador pode ser reaproveitado por Luis, mas incorporar os endpoints inteiros ampliaria uma via de correção sem a conferência exigida. Requer PR próprio e regressões de captura, proveniência e divulgação; nenhuma alteração foi descartada.
- `experiment/*`, `archive/research-artifacts-2026-11` e alterações locais de pesquisa: experimentos matemáticos ou evidências de pesquisa, sem aprovação identificada para substituir a linha de produto. Permanecem intactos e fora desta consolidação.
- `codex/tme-semantic-understanding-01`: o commit já é ancestral da base; alterações locais adicionais em parsers/checkers não foram importadas.
- `feat/dynamic-correction`: base antiga já ancestral da linha atual. As alterações locais antigas não sobrescrevem I1–I6B; há registro histórico em `CONFIA_DYNAMIC_R1_REGRESSION_ATTRIBUTION_01.md` e seu arquivo de referência.
- `harden-v5-1`: commit antigo divergente. A validação estrita de assets já está no conteúdo atual; as dependências são recalculadas no segundo passo de `evaluate_microclaims`. Seu antigo teste textual proibindo toda ocorrência de `dependencies_verified=True` não representa o contrato atual e não justifica regredir o avaliador.
- `codex/interface-video`: projeto de vídeo separado, sem dependência do frontend da aplicação.

## Versões científicas

SPECIALIZED-TME2-RC1 permanece no commit `c03403fe5b83d9db9df172882bd69af3dfa2d027`, objeto de tag `0c64e318a26e21f71fe3097c66ee17a5206dd8a3`, fingerprint `tme-integration.v1:2da7a5bd4d0cd615fd06993b9e7e45fa86c27b6778476724882d65342526b9da`. Verificador executado no worktree congelado com ambiente: **754 arquivos, 65 membros, aprovado**, zero auditorias. Bundle externo não incorporado; recuperação e hash em [RC1_RECORD](../collaboration/RC1_RECORD.md).

A candidata DYNAMIC conserva a referência `fc6f271` e o fingerprint `dynamic-candidate-content.v1:6e1c846b198e1fdceb374db1eed90a4024ba6019c83a09cfc69ce487bfa741a5`. As alterações de frontend e a classificação de erro mudam o conteúdo de `app/`; portanto o fingerprint da candidata **não identifica o checkout integrado**. `verify_dynamic_rc1_reference.py` verifica 684 arquivos de código pelo Git no commit original e 20 arquivos de preparação preservados no checkout atual. Não declara equivalência de ambiente nem executa auditoria. O verificador original continua apropriado ao checkout de origem; nesta integração ele foi conferido e recusou corretamente `static/index.html` por hash diferente, em vez de atestar identidade falsa. Uma futura DYNAMIC-RC1 precisará escolher e manifestar sua base aprovada; nenhuma tag foi criada.

## Verificação no navegador

Servidor localhost isolado, contas/atividade sintéticas de `test_core_auth`, `test_dynamic_school` e `test_dynamic_self_study`, serviços reais e providers simulados. Nenhuma conta institucional real ou fotografia de aluno foi usada. HTTP externo bloqueado no harness temporário; nenhum harness foi incorporado ao produto.

- Login por Enter: Professor → `/#teacher/home`; Aluno → `/#student/home`; Gestão → `/#management/home`, sem segundo clique no módulo. Reload preservou sessão.
- Professor → DYNAMIC → atividade ativa com três rubricas aprovadas → tentativa → relatório 2 + 1,5 + 0 = 3,5/6. Resultado derivado de pareceres simulados; decisão docente separada; justificativas/citações e comparação dos pareceres acessíveis.
- Professor → SPECIALIZED → fila → fixture estruturada P4 → análise e relatório **20/20 (4+6+10)**. AuditRun local sintético `aud_2cf13bbda90f9e0c6db5b92deffba23e0e7aff1ebc7672af031bdc50367a6011`, `COMPLETED`, sem provider semântico. Nove certificados Lean de relações algébricas foram produzidos, sem alegar prova euclidiana global. Flags legadas de revisão por caminhos alternativos permanecem; não são reinterpretadas como falha matemática. O reconhecimento digital automático indisponível nesse harness exibiu aviso técnico separado; a transcrição textual preparada e aceita permitiu a auditoria. Isso não valida OCR real.
- Aluno → atividade institucional → enunciados/tentativas e retenção do resultado até divulgação docente.
- Aluno → estudo autônomo → histórico e feedback de desenvolvimento incompleto, sem nota; pista de nível 2 sobre preservar igualdade, sem revelar o resultado.
- Aluno → TutorIA → prática → caderno com enunciado e ferramentas acessíveis; sem redesenho funcional.
- Gestão → indicadores → filtro `class-a`; contagens reais do armazenamento sintético, sem métricas inventadas. A limitação do contador legado de decisões está descrita acima.
- Menu dos três perfis → Tab/Enter → início da plataforma. Módulos não autorizados permanecem desabilitados; marca compartilhada apresentada como texto.

Capturas renderizadas dos quatro espaços (dados sintéticos, desktop 1440 px; percursos também exercitados em tela estreita):

![Entrada, Professor, Aluno e Gestão](assets/main-consolidation/interfaces.jpg)

## Testes e reprodução

| Execução | Resultado observado |
| --- | --- |
| Suíte Python global inicial, 3.644 coletados | **3.586 aprovados, 4 falhas, 53 skips, 1 xfail**, em 5.505,50 s (1h31m45s) |
| Correção do schema derivado | **100 aprovados**, em 6,15 s |
| Correção do diagnóstico de integridade; autorização e DYNAMIC | **146 aprovados, 1 deselecionado**, em 158,01 s; motivo abaixo |
| Correção do teste de escopo CSS; interface | **45 aprovados**, em 3,37 s |
| JavaScript completo, após a correção do adaptador | **620 aprovados**, zero falhas/skips, em 2,98 s |

As quatro falhas da primeira execução foram corrigidas e seus conjuntos pertinentes passaram nos retestes. Não se declara que a execução global inicial foi verde nem se somam retestes sobrepostos. O processo global iniciou em `8ee1830`; as correções foram registradas separadamente. Não houve repetição integral de 1h31m de verificações matemáticas após ajustes no schema derivado, classificação de erro e expectativa estática de CSS. O CI deve executar o snapshot final e ser revisado antes do merge.

O [registro de validação](assets/main-consolidation/validation.json) identifica o commit do código validado, os resultados e hashes dos logs/capturas; o [log global integral](assets/main-consolidation/python-global-initial.txt) mantém as falhas iniciais e todos os motivos de skip. Apenas espaços finais de linhas de terminal foram normalizados; o SHA-256 do log bruto também está registrado.

A execução global encontrou uma divergência no snapshot `benchmarks/handwriting_recognition/sample.schema.json`: `RecognitionSegment.page_index.exclusiveMaximum` ainda era 3, embora `recognition/schemas.py` já utilizasse `MAX_SOURCE_PAGES=50` desde `d23ebf5` (workspace multipágina). O teste de igualdade do schema falhou corretamente. A correção de uma linha atualizou somente a exportação derivada, sem modificar o contrato de execução, imagens, transcrições, amostras ou matemática. Revalidação de `test_handwriting_recognition_benchmark.py`, `test_recognition_invariants.py` e `test_recognition.py`: **100 aprovados em 6,15 s**. A falha original permanece no registro da primeira execução; não foi omitida nem convertida em skip.

Dois outros casos falharam em `test_original_corruption_blocks_before_engine_and_run`, para `receipt.json` e `submission.json`. Desde `a8692e5`, `_legacy_private_source_guard` rejeita metadados inválidos antes da entrada no roteador de auditoria. O bloqueio HTTP 409 já funcionava, mas `audit_exception_response` convertia a mensagem fixa de integridade em `AUDIT_OPERATION_FAILED`. A correção em `core/public_audit.py` reconhece exclusivamente HTTP 409 com a mensagem fixa `Integridade da submissão inválida.` e restaura `SOURCE_INTEGRITY_MISMATCH`, com diagnóstico público constante. Não muda o guard, os papéis, o acesso, a persistência ou a execução matemática; detalhes desconhecidos continuam genéricos, sem exposição de dados.

Revalidação posterior em `test_public_audit_boundary.py`, `test_submission_audits.py`, `test_core_auth.py`, `test_core_institutional.py`, `test_dynamic_self_study.py`, `test_dynamic_self_study_feedback_policy.py`, `test_dynamic_school.py` e `test_dynamic_handwriting.py`: **146 aprovados, 1 deselecionado em 158,01 s**. O deselecionado foi somente `test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`, já executado na suíte global, para não repetir o custo Lean sem alteração no motor. As quatro novas regressões cobrem classificação exata, status 403 preservado e detalhes textuais/estruturados que não podem ser expostos. Os testes de corrupção confirmam zero chamadas ao motor e nenhum AuditRun criado.

Comando da regressão completa (ambiente validado Python 3.9.6):

```sh
env -u OPENAI_API_KEY -u CONFIA_MATHPIX_APP_ID -u CONFIA_MATHPIX_APP_KEY \
  CONFIA_DYNAMIC_LLM_ENABLED=0 CONFIA_SEMANTIC_LLM_ENABLED=0 \
  CONFIA_ENABLE_LLM_FORMAL_STEPS=0 PYTHONPATH=app PYTHONDONTWRITEBYTECODE=1 \
  python -m pytest -q -rs --tb=short -p no:cacheprovider tests
node --test tests/js/*.cjs
python scripts/evaluation/verify_dynamic_rc1_reference.py
```

A quarta falha era uma asserção estática antiga que proibia `position: sticky` em todo o texto após o comentário `Embedded mode`, incluindo o modo TME adicionado em `0c2dc72`. O CSS existente restringe essa regra a `body[data-embedded="true"][data-tme="true"]`; o workspace geral mantém seus controles no pai. O teste agora verifica os seletores e essa separação, sem alterar CSS ou JavaScript. As **45 regressões Python de interface passaram**. O caderno e seus controles também haviam sido exercitados no navegador e nos 620 testes JavaScript.

Os **53 skips** se distribuem em: **1** smoke real de paridade Lean não comparável; **12** dependências de artefatos locais/piloto/corpus sintético; **19** dependências de pacotes/saídas DEV congelados; **21** testes cujo gate independente ainda não foi executado. Não se substituiu nenhum conjunto reservado por outro dataset.

O skip `test_cap04_parity.py::test_real_engine_smoke[ITA2025F2Q1-correct_solution.txt]` ocorreu **depois de executar** os caminhos textual e de transcrição aceita. `compare_pair` só admite essa classificação após verificar mesmas entradas/obrigações e uma diferença de cobertura acompanhada de falha de runtime observada; invariantes individuais passaram, mas **a paridade real não foi aprovada nessa rodada**. O log resumido não conserva o recibo detalhado dos subprocessos; não se atribui uma causa operacional mais específica nem se afirma resolução. É limitação aberta para reprodução formal, distinta de divergência matemática comprovada e da ocorrência P3 anterior. Não foi alterado o Lean para contorná-la.

Os dois skips DEV previamente documentados e a ocorrência intermitente P3 anterior permanecem no [relatório I6+6B](CONFIA_DYNAMIC_INTERVENCOES_6_6B_CONSOLIDACAO.md). Aprovações posteriores não demonstram a causa da intermitência. O clone público não contém os pacotes controlados.

O conjunto global também contém limites anteriores à consolidação: `test_f2q6_correct_solution_includes_strong_certificate` declarou o `xfail` já previsto para a formulação legada que não extrai `maximizers_identification`. O teste confirmou subtotal 8/8, nota global pendente e verificações disponíveis, sem concessão artificial dos pontos restantes. Isso limita a cobertura operacional daquele texto no caminho legado ITA; não foi corrigido nem apresentado como aprovação matemática nesta integração.

Clone novo em diretório temporário, ambiente virtual separado e dependências instaladas com `python-constraints.txt`: **instalação aprovada; 21 testes de autenticação, isolamento institucional e orçamento aprovados**, com `pip check` sem dependências quebradas. O pip 21.2.4 do Python fornecido pelo macOS não suporta o editable de pyproject usado aqui; atualizar pip resolveu a instalação, e o README foi corrigido. Servidor Uvicorn iniciado a partir desse clone; entrada e scripts servidos, APIs protegidas retornando 401 sem sessão. Não foi reconstruído o cache Mathlib do zero nesse clone; os testes Lean da integração usaram o cache local provisionado. Não confundir instalação do aplicativo com reprodução integral do bundle científico privado.

O clone foi atualizado por fast-forward com a correção do schema e a política de integração (`727d5ce`); os **15 testes do benchmark também passaram nesse ambiente novo**, em 0,29 s. Após o fast-forward até `d868c05`, passaram também os **8 testes de corrupção e classificação segura**, em 1,82 s, no Python próprio do clone.

Para outro computador: seguir [README](../../README.md) e [ambiente autenticado](../collaboration/README.md#dynamic-com-sessão-autenticada), criando contas sintéticas locais com senha escolhida pelo operador. Após aprovação/merge, partir de `main`; antes disso, usar a branch do PR. Provisionar Lean conforme `lean-toolchain` e dependências de `lake-manifest.json`, sem `lake update` para reproduzir um snapshot. Providers permanecem desabilitados até configuração segura e autorização próprias.

## Segurança e revisão do histórico

Remoto confirmado `rmarcolinob/confia-lean-auditor`, público, permissão de push disponível. Na conferência anterior ao commit final deste relatório, foram revisados 1.406 blobs novos em relação à main e 11 arquivos novos ainda não rastreados, além do complemento de instalação. Busca de chaves privadas/tokens/URLs com credenciais: os sinais corresponderam somente a `https://user:password@example.com` na fixture de sanitização `test_secondary_live_contract.py` e à sua menção neste relatório, sem credencial real. Nenhum arquivo `.env`, store de usuários/sessões, banco ou chave privada foi selecionado. O arquivo histórico R1 foi inspecionado sem extração, sem caminhos sensíveis/chaves. Figuras e capturas históricas foram conferidas como diagramas e ensaios sintéticos; o bundle científico e os runtimes continuam fora do Git. Essa revisão não representa garantia de detector universal de segredos.

`git diff --check fc6f271` passou para as adições desta consolidação. A comparação integral contra a main antiga aponta **1.137 avisos de whitespace já presentes na base DYNAMIC**, principalmente logs/patches/CSV históricos; o número e o conteúdo são os mesmos na base e na integração. Não foram reformatadas evidências históricas ou arquivos matemáticos para eliminar esses avisos.

## Pendências para 10/12

1. Revisão/aprovação do PR, execução/consulta dos checks remotos e merge normal, sem force. Só depois confirmar o SHA final da main e orientar novas branches a partir dela.
2. Configurar dados e contas da apresentação em armazenamento separado; não distribuir runtimes ou credenciais.
3. Smoke OCR/LLM real com autorização, teto financeiro e amostras sintéticas; o plano da candidata permanece não executado.
4. Integrar GLM-OCR de Luis ao contrato compartilhado por PR próprio, preservando originais e conferência humana; revisar cobertura de indicadores das decisões DYNAMIC em outra tarefa. Investigar a disponibilidade técnica do smoke de paridade Lean com recibos persistidos, sem declarar sua paridade aprovada.
5. Preservar limitações demonstrativas do TutorIA e realizar avaliação matemática/pedagógica independente. O sistema não está certificado para correção escolar autônoma.

## Inventário dos worktrees e refs

Inventário somente de leitura após criar o worktree de integração: 21 registros de worktree e 94 refs locais/remotas. Um registro antigo é prunable; não foi removido. Contagens representam entradas de `git status --porcelain`, não número de arquivos recursivos.

| Worktree | Branch / HEAD | Pendências preexistentes ou em integração |
| --- | --- | --- |
| `confia-lean-auditor` | `feat/tme-dual-input` · `1b3daea` | 47 entradas; 0 rastreadas |
| `confia-r1-attribution-baseline-5aa7344` | `detached` · `5aa7344` | diretório ausente |
| `confia-lean-auditor-dynamic` | `feat/dynamic-correction` · `5aa7344` | 12 entradas; 2 rastreadas |
| `confia-lean-auditor-leanstrong-aug` | `detached` · `8f50835` | 1 entradas; 0 rastreadas |
| `confia-lean-auditor-research-archive` | `archive/research-artifacts-2026-11` · `18538f6` | 0 entradas; 0 rastreadas |
| `confia-lean-auditor-semantic-formal-b` | `experiment/semantic-formal-b` · `47ed3c0` | 0 entradas; 0 rastreadas |
| `confia-lean-auditor-semantic-formal-b-f2-complete` | `experiment/semantic-formal-b-f2-complete` · `47ed3c0` | 15 entradas; 7 rastreadas |
| `confia-lean-auditor-semantic-formal-b-f2-policy-ab-01` | `experiment/semantic-formal-b-f2-policy-ab-01` · `47ed3c0` | 21 entradas; 7 rastreadas |
| `confia-lean-auditor-specialized-math-assessment-c1` | `experiment/specialized-math-assessment-c1` · `47ed3c0` | 32 entradas; 7 rastreadas |
| `confia-lean-auditor-specialized-semantic-c2` | `experiment/specialized-semantic-providers-c2` · `47ed3c0` | 57 entradas; 7 rastreadas |
| `confia-lean-auditor-tme-december-integration` | `feat/tme-december-integration` · `cb1df6e` | 0 entradas; 0 rastreadas |
| `confia-lean-auditor-tme-semantic-formal-c1` | `experiment/tme-semantic-formal-c1` · `34732d4` | 0 entradas; 0 rastreadas |
| `confia-lean-auditor-tme-semantic-formal-p2` | `experiment/tme-semantic-formal-p2` · `1165dbf` | 0 entradas; 0 rastreadas |
| `confia-lean-auditor-tme-semantic-formal-p3` | `experiment/tme-semantic-formal-p3` · `f979416` | 0 entradas; 0 rastreadas |
| `confia-collaboration` | `codex/collaboration-handoff` · `9eb8d09` | 0 entradas; 0 rastreadas |
| `confia-dec10-integration` | `codex/dec10-functional-integration` · `c03403f` | 0 entradas; 0 rastreadas |
| `confia-dynamic-development` | `codex/dynamic-development` · `fc6f271` | 6 entradas; 0 rastreadas |
| `confia-interface-review` | `codex/interface-review` · `03cba8b` | 3 entradas; 3 rastreadas |
| `confia-interface-video` | `codex/interface-video` · `7a6366f` | 0 entradas; 0 rastreadas |
| `confia-main-consolidation` | `codex/main-consolidation-dec10` · `8ee1830` | 6 entradas; 6 rastreadas |
| `tme-semantic-understanding-01` | `codex/tme-semantic-understanding-01` · `30260b3` | 11 entradas; 5 rastreadas |

<details><summary>Refs examinadas e ancestralidade na integração</summary>

| Ref | Commit | Ancestral da integração |
| --- | --- | --- |
| `add-f2q8-student-claim-checks` | `00dce19` | sim |
| `add-ita2025f2q1` | `7ed6f11` | sim |
| `add-ita2025f2q5` | `ee86f3a` | sim |
| `add-ita2025f2q6` | `de7e069` | sim |
| `add-ita2025f2q8-strong` | `d9820a8` | sim |
| `add-ita2025q3` | `33e5a5e` | sim |
| `add-ita2025q5` | `21a0b8e` | sim |
| `add-ita2025q8` | `b08a6c3` | sim |
| `archive/leanstrong-aug` | `8f50835` | sim |
| `archive/research-artifacts-2026-11` | `18538f6` | não; tratamento descrito acima |
| `benchmark-f2-strong-suite` | `9fc5465` | sim |
| `codex/collaboration-handoff` | `9eb8d09` | sim |
| `codex/dec10-functional-integration` | `c03403f` | sim |
| `codex/dynamic-development` | `fc6f271` | sim |
| `codex/interface-review` | `03cba8b` | sim |
| `codex/interface-video` | `7a6366f` | não; tratamento descrito acima |
| `codex/main-consolidation-dec10` | `8ee1830` | sim |
| `codex/tme-semantic-understanding-01` | `30260b3` | sim |
| `experiment/semantic-formal-b` | `47ed3c0` | não; tratamento descrito acima |
| `experiment/semantic-formal-b-f2-complete` | `47ed3c0` | não; tratamento descrito acima |
| `experiment/semantic-formal-b-f2-policy-ab-01` | `47ed3c0` | não; tratamento descrito acima |
| `experiment/specialized-math-assessment-c1` | `47ed3c0` | não; tratamento descrito acima |
| `experiment/specialized-semantic-providers-c2` | `47ed3c0` | não; tratamento descrito acima |
| `experiment/tme-semantic-formal-c1` | `34732d4` | não; tratamento descrito acima |
| `experiment/tme-semantic-formal-p2` | `1165dbf` | não; tratamento descrito acima |
| `experiment/tme-semantic-formal-p3` | `f979416` | não; tratamento descrito acima |
| `feat/core-auth-rbac` | `04a2011` | sim |
| `feat/core-institutional-hierarchy` | `110967b` | sim |
| `feat/dynamic-correction` | `5aa7344` | sim |
| `feat/gov-01-audit-reproducibility` | `8f3c122` | sim |
| `feat/p2-assessments` | `33fa747` | sim |
| `feat/p2-cap-01-tablet` | `5166cad` | sim |
| `feat/p2-cap-02-submissions` | `44fbcd5` | sim |
| `feat/p2-cap-03-transcription` | `60d895c` | sim |
| `feat/p2-cap-03b-recognition` | `e3a885f` | sim |
| `feat/p2-cap-04-audit-bridge` | `d73fbf9` | sim |
| `feat/p2-hmer-mathpix-strokes` | `25c1c7b` | sim |
| `feat/p2-teacher-decisions` | `8fde840` | sim |
| `feat/tme-december-integration` | `cb1df6e` | sim |
| `feat/tme-dual-input` | `1b3daea` | sim |
| `feat/ui-01-shell-design-system` | `e658352` | sim |
| `feat/ui-02-student-resolution-workspace` | `52d7817` | sim |
| `feat/ui-03-teacher-workflow` | `fb20bc0` | sim |
| `feat/ui-p0-professionalization` | `7c634a7` | sim |
| `fix/ci-assessment-contracts` | `f270e3d` | sim |
| `harden-v5-1` | `a52163f` | não; tratamento descrito acima |
| `harden-v5-2` | `ee86f3a` | sim |
| `main` | `8fde840` | sim |
| `modularize-problem-modules` | `c103a4f` | sim |
| `standardize-student-claim-pattern` | `c847464` | sim |
| `strengthen-ita2025f2q3` | `1c8204b` | sim |
| `strengthen-ita2025f2q5` | `9f4b13e` | sim |
| `strengthen-ita2025f2q6` | `f6d38cd` | sim |
| `origin` | `8fde840` | sim |
| `origin/add-f2q8-student-claim-checks` | `00dce19` | sim |
| `origin/add-ita2025f2q1` | `7ed6f11` | sim |
| `origin/add-ita2025f2q5` | `ee86f3a` | sim |
| `origin/add-ita2025f2q6` | `de7e069` | sim |
| `origin/add-ita2025f2q8-strong` | `d9820a8` | sim |
| `origin/add-ita2025q3` | `33e5a5e` | sim |
| `origin/add-ita2025q5` | `21a0b8e` | sim |
| `origin/add-ita2025q8` | `b08a6c3` | sim |
| `origin/archive/leanstrong-aug` | `8f50835` | sim |
| `origin/archive/research-artifacts-2026-11` | `18538f6` | não; tratamento descrito acima |
| `origin/benchmark-f2-strong-suite` | `9fc5465` | sim |
| `origin/codex/collaboration-handoff` | `9eb8d09` | sim |
| `origin/codex/dec10-functional-integration` | `c03403f` | sim |
| `origin/codex/dynamic-development` | `fc6f271` | sim |
| `origin/codex/interface-review` | `03cba8b` | sim |
| `origin/codex/interface-video` | `7a6366f` | não; tratamento descrito acima |
| `origin/codex/tme-semantic-understanding-01` | `30260b3` | sim |
| `origin/experiment/semantic-formal-b` | `47ed3c0` | não; tratamento descrito acima |
| `origin/experiment/tme-semantic-formal-c1` | `34732d4` | não; tratamento descrito acima |
| `origin/experiment/tme-semantic-formal-p2` | `1165dbf` | não; tratamento descrito acima |
| `origin/experiment/tme-semantic-formal-p3` | `f979416` | não; tratamento descrito acima |
| `origin/feat/core-auth-rbac` | `04a2011` | sim |
| `origin/feat/core-institutional-hierarchy` | `110967b` | sim |
| `origin/feat/dynamic-correction` | `5aa7344` | sim |
| `origin/feat/gov-01-audit-reproducibility` | `8f3c122` | sim |
| `origin/feat/p2-assessments` | `33fa747` | sim |
| `origin/feat/p2-hmer-mathpix-strokes` | `25c1c7b` | sim |
| `origin/feat/p2-teacher-decisions` | `8fde840` | sim |
| `origin/feat/tme-december-integration` | `cb1df6e` | sim |
| `origin/feat/tme-dual-input` | `1b3daea` | sim |
| `origin/fix/ci-assessment-contracts` | `f270e3d` | sim |
| `origin/harden-v5-1` | `a52163f` | não; tratamento descrito acima |
| `origin/harden-v5-2` | `0cc61c5` | sim |
| `origin/luis_ocr` | `0e44685` | não; tratamento descrito acima |
| `origin/main` | `8fde840` | sim |
| `origin/modularize-problem-modules` | `c103a4f` | sim |
| `origin/standardize-student-claim-pattern` | `c847464` | sim |
| `origin/strengthen-ita2025f2q3` | `1c8204b` | sim |
| `origin/strengthen-ita2025f2q5` | `9f4b13e` | sim |
| `origin/strengthen-ita2025f2q6` | `f6d38cd` | sim |

</details>
