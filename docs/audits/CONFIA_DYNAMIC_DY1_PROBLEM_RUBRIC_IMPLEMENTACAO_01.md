# ConfIA Dynamic — DY1: problema e rubrica

Data: 2026-11-11. Implementação limitada à preparação docente e aos contratos futuros.

## 1. Base e escopo

- Worktree: `/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic`.
- Branch: `feat/dynamic-correction`.
- SHA inicial: `3bbed6bfdfc3880afd358800d843e1dd5b2908c3` (`Define ConfIA Dynamic architecture`).
- Base matemática herdada: `cb1df6e381fd0214092f33afe554ce506da68c78`.
- Diagnóstico seguido: `docs/audits/CONFIA_DYNAMIC_ARCHITECTURE_DIAGNOSTIC_01.md`, READY_FOR_DYNAMIC_DY1.
- Estado inicial: worktree limpo. Nenhum outro worktree consultado ou utilizado para runtime, código, venv ou cache.

DY1 cadastra problemas inéditos e suas versões, rubricas manuais, aprovação explícita, pacotes e histórico. Não prepara matematicamente o problema, gera referências, corrige soluções, executa reviewer/reconciliation ou produz certificação Dynamic.

## 2. Infraestrutura reutilizada

| Infraestrutura real | Reuso |
|---|---|
| `auth/dependencies.py`, `auth/models.py` | Sessão e role TEACHER; ator vem do servidor, nunca do body. |
| `assessments/store.py`: `AssessmentStore._locked` | Lock de repositório com flock; o novo store herda o mecanismo existente. |
| `assessments/store.py`: `assessment_store` | Referência opcional a avaliação existente, com conferência do professor criador. Não cria outro Assessment. |
| `submissions/store.py`: `SubmissionStore._write_atomic_new` | Publicação atômica de arquivo novo, sem substituir histórico. |
| `submissions/integrity.py`: `model_sha256`, `canonical_sha256` | Hashes canônicos de conteúdo, pacote e cadeia. |
| `submissions/schemas.py`: `SubmissionModel`, `Sha256` | Contratos fechados e validação de finitude/digest. |
| `teacher_decisions/models.py`: `Points` | Decimal não negativo, máximo 1000, até duas casas decimais. |
| `core/paths.py`: `get_repo_root` | Runtime local da aplicação, com override específico Dynamic. |
| `static/index.html`, `static/shell.js`, design system existente | Nova entrada na área do professor e formulário no mesmo shell. |

O código não possui um barramento genérico central de eventos de domínio. D5/D6/D7 usam eventos estruturados junto dos registros persistidos. DY1 reutiliza esse padrão e as primitivas existentes: evento e alteração são publicados no mesmo snapshot atômico. Não foi criada outra infraestrutura de AuditRun, Submission, Participant, HumanDecision, FinalCorrection ou Certification.

## 3. Modelos novos

Em `app/confia_lean_auditor/dynamic/models.py`:

- `DynamicProblem`: identidade da questão, modo DYNAMIC, criador, data e contexto opcional de assessment.
- `StatementVersion`: texto/título/total de uma revisão, ator e proveniência.
- `RubricCriterion`, `RubricContent`, `RubricVersion`: critérios e revisões independentes do enunciado.
- `DynamicProblemPackage`: binding imutável entre revisão do enunciado e revisão da rubrica, quando houver.
- `Approval`: ato docente com pacote/rubrica, hashes, data e ator.
- `DynamicEvent`: evento estruturado e vínculos de versão.
- `DynamicDocument`: agregado versionado que valida referências cruzadas e contém o histórico.
- `Actor`, `AssessmentReference`, `Provenance`, `FuturePreparation`: contratos auxiliares limitados a essa preparação.

As classes de conteúdo são frozen, usam tuplas para coleções e são revalidadas na publicação, inclusive quando construídas por model_copy. O status atual é uma projeção de conteúdo e lifecycle, não uma regravação de bytes aprovados.

## 4. CorrectionMode e roteamento

`core/correction_mode.py` define `CorrectionMode.SPECIALIZED` e `CorrectionMode.DYNAMIC`, `CorrectionConfiguration`, `PackageReference` e `DynamicAuditProvenance`.

`configured_mode(None)` mantém SPECIALIZED. Um valor inválido, como False, é rejeitado. Configuração DYNAMIC exige referência exata de pacote; SPECIALIZED não aceita essa referência. Criar problema pela API exige `correction_mode: DYNAMIC` explícito.

Não foram adicionados campos aos documentos de avaliações antigas e não foram alterados seus hashes. O teste de assessment verifica que cadastrar um problema com referência contextual deixa o arquivo da avaliação byte a byte igual.

Conforme o diagnóstico, o orchestrator de execução continua para DY3: DY1 entrega configuração e binding, sem mexer no dispatch de AuditService/CorrectionEngine. O endpoint Dynamic de tentativa de correção responde HTTP 501 com `DYNAMIC_ENGINE_NOT_IMPLEMENTED` e `dynamic correction engine not yet implemented`. Não chama Specialized como fallback nem cria resultado/AuditRun fictício. TME_CURRENT continua com o contrato e comportamento anteriores.

## 5. DynamicProblemPackage

Cada pacote tem ID, `problem_id` como referência estável da questão, referência opcional a assessment, `package_version`, statement_version/hash, rubric_id/version/hash opcionais, criador, timestamp e proveniência.

`preparation_status` é sempre `NOT_PREPARED` em DY1, inclusive quando a rubrica está aprovada. Aprovação pedagógica não é preparação ou certificação matemática.

O contrato reserva normalização/interpretação, domínio/hipóteses, referências candidatas, alternativas, verifier plan e model provenance. Esses campos permanecem null; o schema DY1 rejeita preenchimento automático fictício. Não há solução de referência inventada.

Pacotes são criados a cada nova combinação de conteúdo: problema inicial sem rubrica, draft de rubrica, edição e novo enunciado. Por isso a numeração do pacote pode diferir da numeração do enunciado/rubrica. Aprovar um pacote não muda seu conteúdo nem seu hash; gera Approval e ativação.

`packages[].status` informa se aquele pacote já foi aprovado; `is_current` distingue o ativo do histórico. `current_configuration` só é disponibilizada para um pacote aprovado do enunciado atual.

## 6. Enunciados versionados

O enunciado inclui título opcional, texto e valor total. Cada gravação de uma nova versão adiciona um `StatementVersion`; as versões anteriores permanecem intactas.

Alterar enunciado ou total:

1. adiciona nova revisão de enunciado e pacote sem rubrica;
2. registra `rubric_superseded` para a rubrica ativa anterior, se existir;
3. zera `current_package_id`/`current_configuration`;
4. exige rubrica nova vinculada à nova versão;
5. mantém Approval, hashes e conteúdo anteriores acessíveis.

O sistema rejeita edição/aprovação de uma rubrica vinculada ao enunciado antigo para uso corrente. A rubrica anterior não é copiada automaticamente.

## 7. Rubricas versionadas

`RubricVersion` registra ID próprio, número sequencial independente, problem_id, versão/hash do enunciado, pontos/critérios, draft_status, criador/data/proveniência e `supersedes_id` quando deriva de edição.

Toda edição, inclusive de draft, produz nova revisão e novo pacote. Assim não há operação de atualização destrutiva nem exceção para editar uma versão aprovada. Criterion IDs existentes são preservados pela UI; ao remover e criar outro critério, a UI evita reutilizar IDs já presentes no histórico. A API permite ao professor manter IDs estáveis e rejeita duplicatas na mesma revisão.

Campos opcionais de critério: dependências, notas e orientação docente. Não se exige checker, claim type ou plano de verificação. A UI preserva esses campos quando edita uma rubrica obtida da API; a edição visual avançada deles não faz parte desta área mínima.

## 8. Lifecycle

Estados expostos:

| Estado | Uso em DY1 |
|---|---|
| DRAFT_TEACHER | Rubrica inicialmente fornecida pelo professor. |
| TEACHER_EDITED | Nova revisão criada pela edição de uma rubrica existente. |
| DRAFT_AI | Contrato reservado; nenhuma API DY1 gera esse conteúdo. |
| APPROVED | Rubrica aprovada e corrente para o problema. |
| SUPERSEDED | Rubrica anteriormente aprovada que deixou de ser corrente. |

`draft_status` é conteúdo imutável de origem. `status`, `approved_at`, `approved_by` e `is_current` são projetados no retorno da API a partir de Approval e do pacote corrente. SUPERSEDED não destrói a aprovação histórica nem modifica seu hash.

Salvar um novo draft do mesmo enunciado não desativa a aprovação anterior. A substituição ocorre na aprovação da revisão nova, atomicamente. Mudança de enunciado desativa imediatamente o uso corrente anterior. Apenas um pacote/rubrica pode ser corrente por problema. Drafts anteriores continuam históricos com seu estado de origem e não podem ser aprovados fora da última revisão do enunciado atual.

## 9. Invariantes e persistência

Validações implementadas:

- Pontos Decimal >= 0, total > 0, finitude, máximo e precisão do tipo Points existente.
- Para rubrica não vazia, soma exata dos critérios igual ao total do enunciado/rubrica.
- IDs de critérios únicos, ordem contígua de 1 a N e no máximo 100 critérios.
- Dependências existentes, sem duplicação nem ciclos, inclusive autodependência.
- Títulos/descrições não vazios.
- Draft vazio pode ser salvo como trabalho inicial, mas não aprovado.
- Rubrica pertence à versão/hash exatos do enunciado, com mesmo total.
- Pacote pertence ao mesmo problema e corresponde aos hashes/versões de conteúdo.
- Approval exige critérios, ator dono e hashes do pacote/rubrica.
- Pacote corrente precisa estar aprovado e ligado ao enunciado atual.
- `expected_revision` obrigatório nas mutações; edição/aprovação concorrente obsoleta retorna 409.
- Caminhos com IDs inválidos ou symlinks são recusados; hashes/cadeia/histórico são verificados na leitura.

`DynamicStore` grava `runtime/dynamic/<problem_id>/revision_NNNNNN.json`, ou `CONFIA_DYNAMIC_DIR`. Cada registro contém snapshot completo, `previous_sha256` e seu hash. A leitura confere numeração, digest, identidade e que listas históricas anteriores são prefixos imutáveis do snapshot seguinte. O snapshot inclui eventos e alterações, evitando publicação parcial entre eles.

Essa implementação local segue a escala dos stores existentes. O custo de leitura/escrita cresce com o histórico; não é uma alegação de armazenamento otimizado para alta escala. Não há migração de storage Specialized.

## 10. Aprovação docente e autorização

Todas as APIs usam o role TEACHER e o ator derivado da sessão. Listagem e leitura filtram pelo dono/tenant; outro professor recebe 404 no problema, estudantes recebem 403 e ausência de sessão recebe 401. O body não aceita `created_by` ou `approved_by` forjados. O middleware same-origin existente continua protegendo mutações autenticadas.

Em desenvolvimento sem auth, há um opt-in separado: `CONFIA_DYNAMIC_DEMO_ENABLED=1`, com `CONFIA_ENV=development` ou `test`. O ator é `technical-demo:dynamic`, tipo `TECHNICAL_DEMO`; não há nome de pessoa inventado. A UI mostra que se trata de identidade técnica. Sem flag, as APIs exigem autenticação. Não se habilita esse caminho em staging/produção.

A aprovação registra quem/quando/quais versões e hashes. O teste concorrente comprova um único vencedor e rejeição da segunda aprovação obsoleta. Nenhum modelo/IA aprova automaticamente.

## 11. APIs

Todos os caminhos abaixo têm prefixo `/dynamic`. As mutações de versões recebem `expected_revision` retornado pelo GET anterior. Conteúdo adicional inesperado é rejeitado pelo schema.

| Método/caminho | Resultado |
|---|---|
| POST `/problems` | Cria problema/enunciado V1/pacote inicial; 201. |
| GET `/problems` | Lista somente problemas do ator. |
| GET `/problems/{problem_id}` | Agregado atual com conteúdo, histórico, eventos e configurações. |
| GET `/problems/{problem_id}/versions` | Mesmo histórico completo, incluindo revisões de statement/rubric/package. |
| POST `/problems/{problem_id}/statements` | Nova revisão, desativação da configuração antiga; 201. |
| POST `/problems/{problem_id}/rubrics` | Primeira rubrica manual para o enunciado atual; 201. |
| PATCH `/problems/{problem_id}/rubrics/{rubric_id}` | Edição da última rubrica cria outra revisão, não sobrescreve o alvo. |
| POST `/problems/{problem_id}/rubrics/{rubric_id}/approve` | Aprova e ativa pacote; supersede anterior quando necessário. |
| GET `/problems/{problem_id}/current` | Rubrica aprovada corrente e configuração exata, ou null; nunca usa draft. |
| POST `/problems/{problem_id}/rubric-suggestion` | 501, `DYNAMIC_SUGGESTION_NOT_IMPLEMENTED`. Nenhuma gravação. |
| POST `/problems/{problem_id}/corrections` | 501, `DYNAMIC_ENGINE_NOT_IMPLEMENTED`. Nenhuma gravação. |

Superseding é consequência transacional da nova aprovação ou mudança de statement. Não existe endpoint que remova versões históricas ou marque arbitrariamente uma revisão como aprovada.

A referência opcional a assessment é contextual, validada contra avaliação pertencente ao professor. Não vincula ainda um AssessmentItem executável, não publica uma lista/prova Dynamic e não altera o catálogo Specialized. Essa integração pertence à composição posterior prevista no diagnóstico.

## 12. UI mínima

Nova entrada `Dynamic · Problemas e rubricas` em `#teacher/dynamic`, dentro do shell existente. Usa os componentes/estilos base; CSS adicional é restrito a `#teacher-dynamic`.

Permite criar enunciado/título/total, reabrir problema, adicionar/remover critérios, editar texto/pontos, conferir total, salvar draft, aprovar e consultar histórico/versão ativa. O botão de aprovação fica desabilitado para draft vazio ou edição ainda não salva. Editar a versão aprovada informa que será criada outra versão.

O botão `Sugerir rubrica por IA` está desabilitado com a indicação de próxima etapa. Não há fetch de sugestão ou conteúdo mock em produção. Textos do professor são inseridos por textContent/values, sem interpretar HTML.

Não foi alterada a interface de correção TME, seus relatórios, regras, checkers ou workspace D1–D7. O único ajuste da navegação antiga é reconhecer o destino novo e esconder os painéis de outras atividades quando ele está selecionado.

## 13. Eventos

Eventos produzidos: dynamic_problem_created, problem_statement_version_created, rubric_draft_created, rubric_edited, rubric_approved, rubric_superseded e dynamic_problem_package_activated.

Cada evento possui event_id, problem_id, ator, timestamp, package_id/version, statement_version e rubric_id/version quando aplicável. Os eventos de substituição apontam à versão que saiu de uso, com razão STATEMENT_CHANGED ou RUBRIC_REPLACED. Eventos e aprovação são parte do mesmo snapshot validado/selado. GET não grava eventos.

## 14. Proveniência futura de auditoria

`PackageReference` contém problem_id, package_id/version/hash, statement_version/hash e rubric_id/version/hash. `DynamicAuditProvenance` acrescenta engine_version e exige configuração DYNAMIC. Assim não existe contrato futuro baseado apenas em “rubrica atual”.

A implementação não modifica `AuditRun` nem lhe adiciona resultados. DY3 deverá validar a referência contra o release aprovado, estender o contexto/resultado discriminado e manter a separação entre fonte aceita, configuração e versão do engine. `current_configuration` é uma proposta de binding para esse uso futuro; não significa que a preparação matemática já ocorreu ou que o engine está disponível.

## 15. Testes DY1

`tests/test_dynamic_dy1.py`: **21 passed**. Inclui criação, edição, aprovação, reload de store, histórico em bytes, mudança de enunciado, substituição, IDs/ordem/somas/pontos inválidos, ciclo de dependências, draft vazio, aprovação concorrente, optimistic concurrency, tampering/symlink, modo explícito/default, rejeição de preparação falsa, API, isolamento docente, same-origin, referência a assessment sem modificá-lo e identidade técnica opt-in.

`tests/js/test_dynamic_dy1.cjs`: **5 passed**. Inclui criação com modo explícito, ausência de request AI, edição e total 3/3/4, bloqueio de aprovação de edição não salva, aprovação com revisão exata, histórico após alteração do enunciado, total inválido, remoção, texto seguro e não reutilização de IDs removidos.

Logs: [backend DY1](assets/confia-dynamic-dy1/python-dy1.txt), [UI DY1](assets/confia-dynamic-dy1/js-dy1.txt).

## 16. Regressões e limitação formal reproduzida

| Execução | Resultado |
|---|---|
| Plataforma compartilhada, TME e D1–D7 | **407 passed, 2 failed**, 278,59 s. |
| Contratos matemáticos/catálogos/fronteira pública | **375 passed, 2 skipped**, 7,23 s. |
| Toda a suíte JavaScript, incluindo novos testes | **524 passed**, 0 failed. |
| `lake build` | Falha no checkout local da revisão Mathlib fixada. |
| Dois testes formais com `main.py` original do HEAD em memória | Os mesmos **2 failed**, 6,67 s; sem router Dynamic. |

A regressão compartilhada executou: test_assessments, test_submissions, test_transcriptions, test_submission_audits, test_tme_accepted_integration, test_tme_full_exam, test_tme_review_workspace, test_tme_question_audit, test_tme_reanalysis, test_tme_human_confirmation, test_tme_finalization, test_tme_certification, test_tme_demo_auth, test_demo_december_operations, test_core_auth e test_pauta_engine.

A regressão de contratos executou: test_math_canonical, test_generic_student_math, test_claim_alignment_obligations, test_problem_assets_validation, test_problem_assets_contracts, test_tme_problem_catalog e test_public_audit_boundary. Os skips são os previstos pelas suítes existentes, não testes Dynamic removidos.

As duas falhas são:

1. `tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`.
2. `tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved`.

Elas esperavam provas/refutações compiladas e receberam indisponibilidade/technical_error. O ambiente iniciou sem .venv e sem .lake preparados; foi criada uma .venv própria e tentado o build local. O stderr formal registra:

```text
info: mathlib: checking out revision '8f9d9cff6bd728b17a24e163c9402775d9e6a365'
error: external command 'git' exited with code 1
```

Para isolar regressão, o `main.py` original foi lido por `git show HEAD:app/confia_lean_auditor/main.py` e carregado em memória com o mesmo caminho de módulo/raiz; os demais módulos Specialized não foram alterados. As rotas Dynamic estavam ausentes nesse processo. Ambos os testes falharam novamente com o mesmo erro do ambiente. Nenhum arquivo do checkout foi revertido para essa verificação.

Isso demonstra que as duas falhas também ocorrem sem a integração DY1 neste ambiente; não equivale a um build formal aprovado nem permite declarar a suíte completa verde. Não se mudaram toolchain/manifest, expectativas ou fixtures, e não se copiou cache/venv de outro worktree. A preparação formal local continua pendente para uma futura validação Lean completa.

Evidências: [plataforma](assets/confia-dynamic-dy1/python-platform.txt), [contratos](assets/confia-dynamic-dy1/python-contracts.txt), [JavaScript](assets/confia-dynamic-dy1/js-regression.txt), [build Lean](assets/confia-dynamic-dy1/lean-build.txt), [baseline formal](assets/confia-dynamic-dy1/python-formal-baseline.txt), [procedimento de baseline](assets/confia-dynamic-dy1/baseline-probe.txt), [ambiente](assets/confia-dynamic-dy1/environment.json).

Python local 3.9.6; a CI declara Python 3.11. Essa diferença foi registrada, sem alterar pyproject/CI. Não foi executada toda a suíte Python do repositório, nem benchmarks ou chamadas live a modelos/Mathpix.

## 17. Validação no navegador

Aplicação executada em `127.0.0.1:8766`, identidade técnica explicitamente configurada, dados isolados em `runtime/dy1-browser`. Servidor encerrado após a validação.

Cenário realizado pela UI:

1. Abertura da área Dynamic do professor.
2. Criação de `Resolva x² - 5x + 6 = 0`, título DY1 · Equação quadrática e total 10.
3. Critérios: fatoração/estrutura 3, raízes 3, conclusão/justificativa 4.
4. Salvamento de rubrica V1 em DRAFT_TEACHER.
5. Edição da descrição do primeiro critério e salvamento da rubrica V2 em TEACHER_EDITED.
6. Aprovação explícita: rubrica V2 APPROVED, pacote V3 ativo, enunciado V1.
7. Alteração do enunciado para explicitar números reais e justificativa.
8. Enunciado V2/pacote V4 sem rubrica; configuração corrente null; rubrica V2 SUPERSEDED e Approval preservada.
9. Recarga da página, reabertura do problema e expansão da rubrica histórica: dados e aprovação preservados.

Estado persistido: revisão de agregado 5; 2 enunciados, 2 rubricas, 4 pacotes, 1 aprovação; oito eventos. Nenhum erro de console observado após a recarga. O snapshot do store confirma os mesmos vínculos e current_configuration null.

Evidências: [draft](assets/confia-dynamic-dy1/01-draft.jpg), [aprovação](assets/confia-dynamic-dy1/02-approved.jpg), [histórico após recarga](assets/confia-dynamic-dy1/03-history-after-reload.jpg), [registro estruturado](assets/confia-dynamic-dy1/browser-validation.json). As duas primeiras capturas precedem o ajuste visual que reduziu a altura dos textareas; a última registra o layout ajustado e o histórico recarregado.

## 18. Arquivos alterados e preservação

Arquivos existentes alterados:

- `app/confia_lean_auditor/main.py`: somente import/include do novo router.
- `app/confia_lean_auditor/static/index.html`: link, painel e assets Dynamic.
- `app/confia_lean_auditor/static/shell.js`: destino de navegação Dynamic e visibilidade dos painéis.

Arquivos novos:

- `app/confia_lean_auditor/core/correction_mode.py`.
- `app/confia_lean_auditor/dynamic/__init__.py`, `models.py`, `store.py`, `router.py`.
- `app/confia_lean_auditor/static/dynamic.js`, `dynamic.css`.
- `tests/test_dynamic_dy1.py`, `tests/js/test_dynamic_dy1.cjs`.
- Este relatório e `docs/audits/assets/confia-dynamic-dy1/`.

CorrectionEngine, AuditService/AuditRun, PautaEngine, registries, Lean/checkers, assets Specialized, benchmarks, fixtures e demais rotas atuais não foram modificados. O diagnóstico arquitetural anterior foi preservado. Runtime/venv/artefatos de teste permanecem locais e ignorados pelo Git. Não houve git add nem commit.

## 19. Limitações deliberadas

- Não há preparação automática, referência automática, DynamicSolutionGrader, extração Dynamic de claims, reviewer, reconciliation, safe automation ou benchmark.
- DRAFT_AI e os campos futuros são contratos, não geração implementada; sugestão retorna 501.
- A aprovação cria um pacote de conteúdo docente, com NOT_PREPARED matemático.
- Referência a assessment é contextual; integração executável com itens, publicação de listas/provas e escolha oficial/shadow ainda não foram implementadas.
- Não há exclusão de histórico ou reativação silenciosa de versão antiga.
- A UI mínima não edita dependências/notas/orientações avançadas, embora o contrato as aceite e valide.
- Não há correção nem certificação Dynamic nesta etapa. D1–D7 foram exercitados como regressão da infraestrutura existente.
- A validação formal completa depende de preparar corretamente o Mathlib local. Os dois testes formais falham também sem o router Dynamic.

## 20. Próximo DY2 e veredito

DY2 pode consumir os contratos imutáveis para interpretação matemática, referências candidatas, checagens de consistência, alternativas, proposta de rubrica e verifier planning. Deve versionar a extensão de FuturePreparation, preservar autoria AI distinta de aprovação docente e manter incertezas/escopo de verificação explícitos. O binding de execução com AuditRun continua para DY3.

O escopo funcional DY1 está implementado e validado por testes e cenário real de navegador. A pendência do ambiente formal está documentada com reprodução no baseline, sem alterar o Specialized.

READY_FOR_DYNAMIC_DY2
