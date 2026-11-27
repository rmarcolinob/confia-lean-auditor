# ConfIA Dynamic — diagnóstico arquitetural 01

Data: 2026-11-11. Escopo: diagnóstico e proposta; nenhuma implementação.

## 1. Base, método e conclusão executiva

| Verificação | Resultado observado |
|---|---|
| Worktree exclusivo | `/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic` |
| Branch | `feat/dynamic-correction` |
| HEAD | `cb1df6e381fd0214092f33afe554ce506da68c78` |
| Tag `december-demo-rc1^{commit}` | `cb1df6e381fd0214092f33afe554ce506da68c78` |
| Merge-base de HEAD com a base solicitada | O mesmo SHA |
| Estado inicial | `git status --short` vazio |
| Instruções locais | Nenhum `AGENTS.md` encontrado na árvore consultada ou nos diretórios ancestrais consultados |

A inspeção foi estática: leitura de implementações, validadores, dependências, pontos de chamada, testes e configuração de CI deste worktree. Nomes de arquivos não foram usados como prova de generalidade. Documentos herdados foram tratados como contexto histórico, não como resultado de testes executados nesta sessão. Não foram acessados os worktrees de dezembro ou P3, usados seus ambientes, copiados seus módulos ou executados seus launchers.

**Conclusão:** há uma base forte para compartilhar o ciclo operacional, a pontuação declarativa e os contratos de evidência. Não existe ainda um engine genérico intercambiável, um catálogo de problemas docentes ou uma rubrica com aprovação versionada. O Dynamic requer extensões aditivas nos limites de catálogo, configuração, resultado e proveniência; não requer reescrever o Specialized ou duplicar D1–D7.

O nome `CorrectionEngine` hoje identifica um adapter concreto TME, não um `Protocol`/ABC com dois engines registrados. A compatibilidade do Dynamic deve preservar o contrato público `question-audit.v1` e ampliar os contratos persistidos sem reinterpretar registros antigos. As propostas abaixo permitem iniciar DY1; não significam que o Dynamic já esteja pronto para corrigir.

### Convenções do inventário

Os caminhos da seção 2 são relativos a `app/confia_lean_auditor/`, salvo indicação explícita de caminho na raiz. Símbolos indicam o trecho de implementação que fundamenta a conclusão.

- **SHARED:** comportamento já independente do método matemático no recorte indicado.
- **SPECIALIZED_ONLY:** preparação, catálogo ou regra vinculados aos problemas atuais; preservar.
- **DYNAMIC_CANDIDATE:** primitiva aproveitável após validar cobertura e adaptação; não constitui um Dynamic pronto.
- **REQUIRES_ABSTRACTION:** responsabilidade compartilhável com acoplamento concreto que impede uso direto.

Um arquivo misto pode ter recortes classificados separadamente. A classificação não autoriza mover arquivos.

## 2. Arquitetura real e dependências

### 2.1 Plataforma, entrada e persistência

| Componente / arquivo real / evidência | Responsabilidade e dependências observadas | Classe e consequência |
|---|---|---|
| `main.py`: `app`, `execute_audit` | FastAPI, montagem de estáticos e routers; `/audit` usa assets, extração por problema, Lean, microclaims, rubric, adjusters, scoring policy e relatório. | **REQUIRES_ABSTRACTION** no composition root; `execute_audit` é **SPECIALIZED_ONLY**. Não transformar esse pipeline em Dynamic. |
| `assessments/models.py`: `Assessment`, `AssessmentItem`, `AssessmentDocument` | Avaliação DRAFT/PUBLISHED/CLOSED, itens com `problem_id`, ordem e pontos; instituição ou escopo TME; valida unicidade e período. Não tem modo, pacote ou rubrica por versão. | **SHARED** para identidade/ciclo; **REQUIRES_ABSTRACTION** para binding de correção versionado. |
| `assessments/store.py`: `AssessmentStore`, `definition_hash` | JSON em runtime configurável, `flock`, integridade da definição publicada; hash inclui itens. | **SHARED** para persistência. Nova configuração deverá entrar no hash novo sem alterar o cálculo dos documentos legados. |
| `assessments/participants.py`: `ParticipantStore`; `assessments/models.py`: `AssessmentParticipant` | Participante registrado ou pseudônimo externo, separado da identidade de autenticação; depende de assessments e escrita atômica de submissions. | **SHARED**. Não criar um participante Dynamic paralelo. |
| `assessments/router.py`: `_catalog_ids`, `add_item`, `publish_assessment` | Autorização institucional, CRUD e publicação; catálogo vem de `list_problem_catalog`, atualmente ITA. | **REQUIRES_ABSTRACTION**: resolver problemas autorizados por origem/configuração, preservando as permissões existentes. |
| `auth/models.py`, `auth/store.py`, `auth/dependencies.py`, `auth/router.py` | Usuários, sessões, roles e acesso a submissões; dependências validam escopo institucional ou caso TME. | **SHARED** para autenticação; regra de acesso ao futuro pacote deve ser explícita. Dynamic não implica ativar demo sem auth. |
| `institutional/models.py`, `institutional/store.py`, `institutional/router.py`; `management/router.py` | Redes, escolas, turmas e escopo docente; management compõe consultas operacionais. | **SHARED**, independente da prova matemática. |
| `capture/schemas.py`; `submissions/schemas.py` | Captura, artefatos, segmentos, submissão e referências de origem; contratos fechados. | **SHARED** para representação. Não são modelos de correção. |
| `submissions/store.py`: validação de snapshot, `SubmissionStore`; `submissions/router.py` | Armazena originais, transcrições e aceitações; integridade, deduplicação e acesso. Há validações `CATALOG.keys() | PUBLIC_PROBLEMS.keys()` na entrada. | **REQUIRES_ABSTRACTION** na resolução de problema; mecanismos de storage e integridade são **SHARED**. |
| `submissions/integrity.py`, `submissions/body_limit.py`, `submissions/png.py` | Hash canônico, limites de payload e validação de imagem; usados por stores e routers. | **SHARED**. |
| `submissions/schemas.py`: `TranscriptionRecord`, `TranscriptionRevision`, `TranscriptionAcceptance`, `TranscriptionAcceptanceReceipt`; `submissions/store.py` | Revisões e recibos preservam a fonte aceita. `mathematical_validity_assessed=False`: aceitar transcrição não certifica matemática. | **SHARED**. A entidade conceitual TranscriptionVersion corresponde ao par `transcription_id:revision_number`, não a uma nova classe a criar. |
| `recognition/service.py`: `RecognitionService`; `registry.py`, `schemas.py`, `execution.py`, `validation.py` no mesmo diretório | Provider pluggable, prazo, idempotência, mapping de páginas/strokes e publicação em transcrição existente; depende de SubmissionStore. | **SHARED** no serviço. Reconhecimento não deve atribuir pontos. |
| `recognition/mathpix.py`, `recognition/mathpix_image.py`, `recognition/fake.py`; `recognition/preview.py` | Adapters de reconhecimento; preview valida IDs dos catálogos atuais. | Adapters **SHARED**; preview **REQUIRES_ABSTRACTION** no catálogo. Não presumir cobertura de diagramas matemáticos. |
| `core/paths.py`: `get_repo_root`, `get_problem_dir` | Resolve raiz via ambiente ou localização do módulo; diretório de problema validado. | **SHARED** como utilitário; não usar `get_problem_dir` para impor assets ITA a todo problema Dynamic. |

### 2.2 Ciclo D1–D7 e contrato operacional

| Componente / arquivo / evidência | Responsabilidade e dependências | Classe e consequência |
|---|---|---|
| `tme/exam_models.py`: `ExamSubmission`, `ExamPage`, `PageMapping`, `QuestionAttemptView`; `tme/models.py`: `CorrectionCase` | Prova completa, páginas, associação e visão de questão. A tentativa é persistida como `CorrectionCase`, com vínculos de assessment/item/exam. | **SHARED** como entidades conceituais; não criar outro `QuestionAttempt` persistente apenas para renomeá-las. |
| `tme/exam_store.py`: `ExamStore`, `tme_assessment`; `tme/store.py`: criação de caso | Captura, mapping, detalhes, casos; acesso exige assessment TME; CaseStore restringe catálogo. | **REQUIRES_ABSTRACTION** no escopo de acesso e resolução de problemas. Reutilizar a cadeia de armazenamento. |
| `tme/exam_capture.py`, `tme/exam_router.py` | Recepção de PDF/imagens, endpoints de avaliações/provas/questões; criação permite os catálogos ITA/TME conhecidos. | **REQUIRES_ABSTRACTION** na admissão de problema e política; infraestrutura de captura é reutilizável. |
| `tme/review_models.py`, `tme/question_review.py`: `freeze_source`, `workspace`, `revise` | Snapshot da questão, revisão/aceitação, histórico e estados; depende de exam/case/submission stores, audit service e projector TME. | **REQUIRES_ABSTRACTION** na dependência do projector; preservar mapping congelado e integridade. |
| `tme/correction_engine.py`: `CorrectionEngine.audit_question` | Lock por questão, ownership, editabilidade, versão atual, execution key, contexto e execução; configura Lean TME via ambiente. | **REQUIRES_ABSTRACTION**. Já faz parte da orquestração, mas só conhece a integração atual. |
| `tme/correction_engine.py`: `project_audit`, `project_result`, `audit_events` | Projeção `question-audit.v1`: nota, itens, evidências, checks, review, comparação e eventos. `project_result` navega `result.bridge`, `pauta`, `assessment` e `split_accepted_items`. | Contrato de produto **SHARED**; implementação do projector **REQUIRES_ABSTRACTION**. |
| `submission_audits/schemas.py`: `AuditRequest`, `AuditSource`, `QuestionAuditContext`, `AuditRun` | Fonte aceita, hashes, resultado, manifesto, execution key, eventos; `engine_mode` literal TME_CURRENT; resultado Union de TMEAuditResult e AuditResponse. | **REQUIRES_ABSTRACTION**. `AuditRun` continua a entidade única; necessita novo tipo de resultado/contexto. |
| `submission_audits/service.py`: `AuditService.execute`, `_identity`, `_read`, `view` | Valida fonte/aceitação, deduplica por hash, executa engine, registra falha/resultado e revalida artefatos; `startswith('TME')` escolhe contexto especializado e execução TME. `stale` deriva da transcrição. | Storage e invariantes **SHARED**; dispatch por prefixo e fonte/resultados **REQUIRES_ABSTRACTION**. |
| `submission_audits/router.py`: `service`, `engine`; `source.py`, `artifacts.py` | Injeta `main.execute_audit`, converte segmentos e exige manifesto; `artifacts.required_references` diferencia TME de ITA e no ITA exige certificado principal. | **REQUIRES_ABSTRACTION** no adapter/manifesto. Dynamic sem Lean não pode cair no ramo ITA. |
| `tme/human_decisions.py`: `HumanDecision`, `decide`, `project` | D5: confirmação/ajuste, versões, trilha append-only e locks; persiste engine_mode/version e snapshot de review; depende da projeção de auditoria. | **SHARED** no modelo e ciclo; integração **REQUIRES_ABSTRACTION**. Exige sugestão não nula para confirmar. |
| `teacher_decisions/models.py`, `service.py`, `store.py`, `router.py` | Fluxo institucional prévio TeacherDecision/StudentResult, finalizar/liberar; usa submissions, audits, assessments e auth. | **REQUIRES_ABSTRACTION** na integração; não confundir com a cadeia D5 nem criar um terceiro fluxo Dynamic. |
| `tme/finalization.py`: `FinalCorrection`, `ConfirmedQuestion`, `finalize`, `reopen` | D6: fechamento com todos os itens confirmados, totais e snapshot; invalidação/reabertura versionada. | **SHARED** no contrato; acesso indireto ao fluxo TME deve ser generalizado sem mudar as regras atuais. |
| `tme/home_summary.py` | Índice operacional alimentado por submissões/análises; inicializado no lifespan. | **REQUIRES_ABSTRACTION** de projeção/contexto, não fonte de verdade nem outro storage Dynamic. |
| `tme/certification.py`, `certification_gold.py`, `certification_metrics.py`, `certification_events.py`, `certification_router.py` | D7: gold independente/versionado, seleção current/finalized, export CSV/JSON, métricas e eventos; acesso ainda TME. | Métricas e registros **SHARED**; escopo, projector, catálogo de rubrica e pareamento **REQUIRES_ABSTRACTION**. Ver seção 16. |
| `core/public_audit.py`: `public_projection`; `reproducibility/canonical.py`, `schemas.py`, `service.py`, `collector.py` | Sanitização pública; proveniência e verificação de manifests. Collector captura assets/ambiente do pipeline atual. | Sanitização/hash **SHARED**; collector de preparação Dynamic **REQUIRES_ABSTRACTION**, sem substituir a trilha existente. |
| `reports/report_builder.py`; `static/tme/workspace-report.js` | Relatório pedagógico ITA lê tipos específicos; relatório do workspace apresenta dados operacionais. | Builder matemático **REQUIRES_ABSTRACTION**; apresentação do contrato de produto é reutilizável. Não duplicar exports D7. |

### 2.3 Preparação, matemática e agentes

| Componente / arquivo / evidência | Responsabilidade e dependências | Classe e consequência |
|---|---|---|
| `core/problem_assets.py`: `ProblemConfig`, `RubricConfig`, `MicroclaimsConfig`, `validate_problem_assets` | Exige assets curados, `correct_answer`, rubric e microclaims; não tem aprovação, múltiplas referências verificadas ou preparação automática. | **SPECIALIZED_ONLY** no contrato de pacote atual. Não adicionar exigência de microclaims manuais ao Dynamic. |
| `core/problem_catalog.py`: `CATALOG`, `list_tme_problem_catalog`; raiz `problems/` | ITA enumerado; TME exige correspondência exata com registry, pauta e figuras; TME content tem máximo literal 20. | **SPECIALIZED_ONLY** para esses catálogos; futura composição de catálogo **REQUIRES_ABSTRACTION**. |
| `tme/registry.py`: `TME_PROBLEMS`, `audit_tme`; `tme/accepted_audit.py`; `tme/audit_models.py` | Dispatch P1–P5, alias de P1, pautas fixas; entrada aceita por itens a–d; TMEAuditResult revalida problema e PautaEngine. | **SPECIALIZED_ONLY**. Não usar IDs TME fictícios para problemas novos. |
| `claims/extract_claims.py`, `claims/extractors/`; `lean/build_attempt.py`, `lean/attempt_builders/` | Extração e construção de proposições de referência por problema. | **SPECIALIZED_ONLY**. Formalização de referência não equivale a prova do aluno. |
| `student_claims/registry.py`, `extract_f2q*_student_claims.py`, `tme2_p*_digital.py`; `lean/student_claim_checkers/registry.py`, `ita2025f2q*.py`, `tme2_p*.py` | Extração e verificação com representações, IDs e requisitos preparados. | **SPECIALIZED_ONLY**, incluindo os checkers P1/P2/P3 já presentes neste checkout. |
| `rubric/adjusters/`, `rubric/positive_rules.py`; raiz `ConfiaLeanAuditor/Problems/*/Statement.lean`, `examples/pautas/` | Ajustes, regras, proposições e estruturas de referência específicas. | **SPECIALIZED_ONLY**; preservar valores, fixtures e benchmarks. |
| `claims/common/schemas.py`: `MathClaimRecord`, `SourceBinding`, `SemanticRole`, `VerificationLink` | Origem, span/hash, papel semântico e ligação a resultado; alinhamento não é prova. | **DYNAMIC_CANDIDATE**: reutilizar a representação, revisar enums/validação para claims novos. |
| `claims/common/adapters.py`, `catalog.py`, `alignment.py`, `expected.py`, `rubric_bridge.py`, `compatibility.py` | Converte contratos legados, monta catálogo/alinhamento e expected obligations da preparação existente. | **REQUIRES_ABSTRACTION**; não reaproveitar automaticamente expected payloads como requisitos de questão inédita. |
| `claims/common/fact_results.py`: `FactResultsBuilder`; `rubric/pauta/bridge.py`: `FactResult`, `AuditorFactBundle`, `bridge_facts` | Liga verificações a fingerprints e obrigações declaradas; rejeita atribuição inválida/conflito. Bridge contém também mapa fixo P1 e políticas do piloto. | Builder **DYNAMIC_CANDIDATE**; bridge **REQUIRES_ABSTRACTION** por recorte. Mapa P1 **SPECIALIZED_ONLY**. |
| `student_claims/generic_math.py`: `extract_generic_math`, `source_is_valid`, `contextual_role` | Detecção limitada de matemática literal, valida fonte e contexto; não usa gabarito para detectar. | **DYNAMIC_CANDIDATE**, não grader completo. `main.execute_audit` exclui `math_*` da rota de checkers legados. |
| `core/math_canonical/`: `parser.py`, `equivalence.py`, `rational.py`, `development.py`, `combinatorial.py`, `integer_structures.py` | Parser limitado, racionais exatos, equivalência afim, construções aditivas e estruturas inteiras/combinatórias. | **DYNAMIC_CANDIDATE** por capacidade suportada. Não é CAS geral. |
| `student_claims/grounding.py`, `evidence_units.py`; `rubric/secondary_candidates.py`, `secondary_evidence.py`, `secondary_award_gate.py` | Spans, hashes, IDs de evidência, vinculação e gates objetivos de crédito; gates de discurso limitados. | **DYNAMIC_CANDIDATE**; descolar dependências de catálogo e não prometer compreensão geral de discurso. |
| `rubric/pauta/models.py`, `engine.py`: `PautaConfig`, `PautaEngine.evaluate` | Pontos Decimal, somas, caps, additive/banded/max_of/all_of/any_of/carry_forward; recebe evidência, não texto nem LLM. | **SHARED** no scoring declarativo. `schema_version='pauta.v1'` é versão do schema, não revisão/aprovação docente. |
| `rubric/pauta/tme2_p*.py`; `tme/p3_machine.py`, `p2_diagram.py`, `p4_geometry.py`, `p5_integer_break.py` | Bridges, máquina, geometria, enumerações e estruturas específicas. | **SPECIALIZED_ONLY**. Podem inspirar capacidades, sem importá-los como preparação Dynamic. |
| `llm/formal_step_extractor.py`; `student_claims/semantic.py`, `obligation_semantic.py`, `evidence_id_semantic.py`, `hybrid_semantic.py`, `semantic_sufficiency.py` | Clientes/prompts e schemas distribuídos; várias chamadas OpenAI dentro dos módulos; vocabulários/obrigações preparados. | **REQUIRES_ABSTRACTION** para transporte/proveniência; prompts e catálogos atuais são **SPECIALIZED_ONLY**. Não há serviço único genérico de preparação. |
| `student_claims/model_transport.py` | Copia parâmetros para compatibilidade de um experimento de ablação; não possui cliente, prompt ou interpretação. | **DYNAMIC_CANDIDATE** como exemplo de separação. Não é um LLM gateway existente. |
| `rubric/secondary_adjudicator.py`, `secondary_context.py`; `rubric/scoring_policy.py` | Adjudicação limitada a critérios pendentes, com contexto do primeiro pipeline e pontos permitidos; não é correção cega completa. | **SPECIALIZED_ONLY** na aplicação atual; padrões de validação **DYNAMIC_CANDIDATE**. Não renomear para IndependentReviewer. |
| `tme/hybrid_grader.py`: `EvidenceReconciler`, `run_hybrid_shadow`; `tme/sufficiency_experiment.py`, `obligation_experiment.py`, `evidence_id_experiment.py` | Shadow e reconciliação explícita entre semântica e auditor; dependências/obrigações TME, gates de ativação. | **REQUIRES_ABSTRACTION** como padrão experimental; pipelines concretos **SPECIALIZED_ONLY**. |
| `lean/student_proof.py`, `run_lean.py`, `safe_formal_step.py`; `lean/student_claim_checkers/rational_equality.py`, `real_algebra.py` | Ciclo de prova/refutação, runner, gramática/táticas restritas, projeções exatas de racionais/álgebra. | **DYNAMIC_CANDIDATE**, sujeito a representação fiel e domínio limitado. `real_algebra` exige coletor/contexto confiável fornecido pelo chamador. |

### 2.4 Frontend e composição do fluxo

| Arquivo real | Papel e dependências observados | Classificação |
|---|---|---|
| `static/assessments.js`, `static/index.html`, `static/shell.js` | Gestão/listagem institucional e formulário por seleção do catálogo; chama APIs de assessments. | **REQUIRES_ABSTRACTION** para entrada docente de enunciado e preparação. |
| `static/tme/tme.js`, `static/tme/full-exam.js`, `static/tme/home.js` | Fila, avaliação/prova, páginas, fechamento e certificação; depende de APIs TME e contexto de casos. | **REQUIRES_ABSTRACTION** em acesso/contexto; preservar experiência operacional. |
| `static/tme/correction-workspace.js`, `workspace-controls.js`, `workspace-report.js` | Navegação, Original/Transcrição/Comparar, análise, confirmação e relatório. Há fallback de família por ID e allowlist de figuras TME. | **SHARED** no contrato de apresentação; **REQUIRES_ABSTRACTION** para catálogo/conteúdo novo, sem lógica matemática Dynamic na UI. |
| `static/audit-view.js`, `static/recognition-view.js`, `static/submissions/teacher.js`, `decisions.js` | Auditoria, reconhecimento e fluxo docente existente. | **SHARED** nos componentes de exibição; revisar diferenças entre fluxo institucional e D1–D7 antes de conectá-los. |
| `static/capture/` | Escrita digital, persistência local, envio e renderização matemática. | **SHARED** no mecanismo de captura; resolver problema/versionamento via backend. |

Fluxo efetivo D1–D7: assessment/participant → ExamSubmission/ExamPage → CorrectionCase e mapping → snapshot/TranscriptionRevision aceita → CorrectionEngine → AuditService → integração TME → AuditRun persistido → projeção de questão → HumanDecision → FinalCorrection → CertificationRecord/gold/exports. O pipeline ITA `/audit` também existe e não deve ser confundido com esse fluxo de questão completa.

Não foram localizadas classes literalmente chamadas `DynamicProblemPackage`, `CorrectionOrchestrator`, `CorrectionMode`, `TranscriptionVersion`, `RubricDecision` ou `HumanGold`. Os equivalentes atuais são explicitados acima: versão de transcrição, `PautaDecision`/`HumanRubricDecision`, `GoldRow`/registros selados e `CertificationRecord`. Não duplicá-los por diferença de nomenclatura.

## 3. CorrectionOrchestrator e seleção explícita

Proposta conceitual, sem fixar novos diretórios:

1. Resolver configuração persistida da questão, com herança explícita do assessment quando não houver override.
2. Validar autorização, definição publicada, origem aceita, pacote/rubrica e versão da transcrição.
3. Congelar um contexto de execução com modo, implementação, versões/hashes e policy.
4. Encaminhar ao adapter Specialized ou Dynamic.
5. Persistir pelo ciclo único AuditService/AuditRun e projetar o resultado no contrato de produto existente.

`CorrectionMode` deve ter `SPECIALIZED` e `DYNAMIC`. Separar **metodologia** de **implementação**: TME_CURRENT é a implementação Specialized hoje exposta no contrato. Documentos antigos continuam com esse valor e os mesmos hashes; uma normalização de leitura pode associá-lo à família SPECIALIZED, sem regravação. Novos Dynamic publicam `engine_mode=DYNAMIC`. Não renomear retroativamente TME_CURRENT em eventos/gold.

Novas avaliações Dynamic exigem configuração explícita. Ausência de modo em registros legados mantém a rota histórica; ausência em criação nova deve ser validada. Não escolher pelo conteúdo do enunciado, confiança do LLM, disponibilidade de Lean ou prefixo do ID. Falha do Dynamic não deve cair silenciosamente no Specialized, nem vice-versa.

A fronteira adequada está entre validação/aceitação da fonte e dispatch do `AuditService`, em coordenação com `CorrectionEngine.audit_question`. Preservar locks, execution key, conferência pós-execução e publicação atômica. Não executar dois motores por baixo de uma mesma identidade de run. Comparações shadow exigem execuções separadas, explicitamente configuradas, e nunca substituem a execução oficial escolhida para D5/D6.

DY1 deve especificar esse binding e sua compatibilidade. A troca efetiva de dispatch ocorre com o adapter DY3, não com uma reescrita antecipada de `main.py`.

## 4. DynamicProblemPackage e versionamento

`ProblemConfig` exige resposta preparada; `PautaConfig` descreve scoring; `AssessmentItem` referencia somente ID/pontos. Nenhum representa preparação automática aprovada. Recomenda-se um agregado novo de preparação que **referencie** esses contratos compartilháveis, sem incluir cópias de Assessment, Submission ou AuditRun.

| Grupo proposto | Conteúdo mínimo | Invariante |
|---|---|---|
| Identidade | package_id/revision, problem_id, schema_version, owner/scope, predecessor, hash | IDs opacos; revisão imutável após aprovação; sem colisão com catálogos curados. |
| Enunciado | original, versão/hash, normalizado, assets opcionais e relação com o original | Normalização não altera hipótese silenciosamente; edição cria versão nova. |
| Interpretação | domínio, variáveis, unidades, hipóteses explícitas/inferidas, ambiguidades | Hipótese inferida fica identificada e requer resolução docente quando afeta a correção. |
| Referências | lista de candidate solutions, estratégias e subclaims, IDs/versões | Não impor solução canônica única; cada referência tem origem, status e escopo de verificação. |
| Rubrica | rubric_revision_id, content hash, payload PautaConfig quando expressível, registro de aprovação | Nenhuma execução nova sem a revisão aprovada exata. |
| Verifier plan | versão/hash, capabilities, claims/obrigações alvo, domínios, limites, timeouts, precondições | Planejamento não é resultado de execução; só checkers permitidos. |
| Checks preparados | especificações declarativas, casos de consistência, expected outcomes e proveniência | Não executar código arbitrário produzido por modelo. Não confundir teste contra referência com prova. |
| Formalização seletiva | claims formalizáveis, representação, pressupostos, ferramenta e artefato se houver | Descrição natural não tem status formal_verified. |
| Estado | preparação PENDING/PREPARING/NEEDS_REVIEW/READY/FAILED, uncertainties, warnings | Estado de preparação separado do lifecycle da rubrica. READY não certifica todos os passos. |
| Proveniência | timestamps UTC, approved_at/actor, modelo solicitado e retornado, prompt/schema versions, request/response hashes, checker versions | Guardar artefatos necessários em storage controlado, sem segredos na projeção pública. |

A relação pacote↔rubrica deve ser acíclica para hashing: revisão de rubrica aponta ao problem/statement e aos artefatos de preparação, e o release imutável do pacote agrega o hash da rubrica. O selo final do pacote não é embutido no próprio conteúdo que ele hasheia.

Também versionar engine, policy, plano de verificadores e referências. `AuditRun` deverá guardar o manifesto congelado e referências verificáveis aos bytes usados; apontar apenas para “latest” é insuficiente. Guardar respostas LLM permite replay da decisão registrada; repetir uma chamada externa não garante a mesma saída.

## 5. Rubric lifecycle e Rubric Assistant

Estados propostos: `DRAFT_AI`, `TEACHER_EDITED`, `APPROVED`, `SUPERSEDED`. Uma rubrica fornecida integralmente pelo professor entra como revisão docente, sem inventar autoria AI. Guardar `origin=TEACHER|AI` separado do estado.

Transições: sugestão AI → DRAFT_AI → edição opcional TEACHER_EDITED → aprovação explícita APPROVED. Rubrica própria → TEACHER_EDITED → APPROVED. Aceitar sem editar ainda exige evento de aprovação. Editar uma APPROVED cria nova revisão; a anterior permanece disponível para seus runs. SUPERSEDED deve ser um evento/estado de lifecycle fora dos bytes imutáveis da revisão aprovada, preservando seu hash.

A execução exige comprovação de que a revisão vinculada foi aprovada e não pode consultar a rubrica corrente para pontuar um run antigo. Um assessment publicado permanece vinculado à revisão aprovada escolhida, mesmo quando ela é substituída para novos usos. Reanálise histórica pode usar esse binding explicitamente; migrar uma avaliação para nova rubrica é uma operação nova e rastreável, não um efeito colateral da edição global.

O Rubric Assistant sugere critérios, pontos, dependências, caminhos alternativos e crédito parcial. Validação determinística verifica IDs únicos, soma Decimal, caps, referências, ciclos de dependência e consistência de intervalos. Análise LLM sinaliza critérios vagos, redundantes, incompatíveis ou excessivamente dependentes de método; esses alertas não se tornam decisões matemáticas. O professor resolve ambiguidades e aprova critérios/pesos.

Usar `PautaConfig`/`PautaEngine` para a parcela expressível. A definição existente já verifica soma dos itens e referências declaradas e oferece `max_of` e `carry_forward`. Um detector geral de ciclos/redundância e lifecycle docente são capacidades novas. Não ampliar silenciosamente os requisitos da pauta durante a correção.

## 6. Preparação automática e referências

| Etapa | LLM | Verificação matemática/determinística | Professor |
|---|---|---|---|
| Recepção/normalização | Pode sugerir redação normalizada | Valida schema, encoding, versão e hash; compara alterações | Confirma alterações semânticas necessárias |
| Interpretação/domínio | Propõe variáveis, domínio e hipóteses | Verifica consistência de tipos, restrições e unidades no escopo suportado | Resolve enunciado ambíguo/incompleto |
| Soluções candidatas | Produz uma ou mais derivações e alternativas | Checa afirmações locais, substituições, limites e contradições aplicáveis | Revisa lacunas relevantes |
| Consistência | Explica divergências como hipótese | Detecta referências incompatíveis; distingue verificado/contradito/desconhecido/erro técnico | Escolhe reformulação ou preparação em revisão |
| Estratégias alternativas | Propõe métodos adicionais | Testa claims de cada método e condições de validade | Aceita diversidade de método e exceções pedagógicas |
| Rubrica | Propõe critérios e parcialidade | Valida pontos, caps, bindings e dependências | Edita/aprova a revisão exata |
| Verifier plan | Sugere capacidades úteis | Resolver de capabilities valida cobertura, domínio, custo e precondições | Visualiza cobertura e limitações |
| Release de preparação | Não autoaprova | Congela pacote/rubrica/plano e checa integridade | Aprova o uso pedagógico; não declara formalização inexistente |

Cada referência deve ter `CANDIDATE`, `PARTIALLY_VERIFIED`, `VERIFIED_WITHIN_SCOPE`, `CONTRADICTED` ou `UNRESOLVED`, com status por claim, evidências, ferramenta e assumptions. Esses nomes são propostos, não enums existentes. “VERIFIED_WITHIN_SCOPE” não significa formalização Lean de toda a solução.

Uma referência contradita impede a preparação de se tornar apta à automação dependente dela. É possível registrar um pacote limitado para revisão humana, com lacunas explícitas; não esconder essas lacunas com aprovação docente. A primeira preparação deve operar sobre texto, evitando inferir geometria a partir de figura não representada.

## 7. Dynamic Solution Grader e crédito parcial

Pipeline proposto: solução aceita → segmentação semântica → extração de claims → ligação claim↔critério → verificadores → suficiência → pontuação parcial → explicação → proposta de nota.

- Segmentação mantém IDs, spans e hash do texto original, item/página quando comprovados. LLM pode sugerir segmentos; o backend valida cada referência. Não criar coordenadas de página a partir de offsets de texto normalizado.
- Claims distinguem afirmação, hipótese, citação, conclusão e tentativa abandonada. Reutilizar `MathClaimRecord` quando couber; guardar transformação fiel do texto em payload matemático.
- Mapping usa a **rubrica aprovada**, sem consultar registries P1–P5 para inventar obrigações. Preservar dependências entre critérios e a origem de cada premissa.
- Verificadores recebem payload limitado e contexto/assumptions, retornando status, escopo e artefato. Verificação local correta não demonstra automaticamente suficiência do argumento completo.
- O julgamento de suficiência examina se as evidências satisfazem o critério. Resíduo semântico fica rotulado e revisável, não promovido a fato determinístico.
- Pontos derivam de regras declaradas, preferencialmente pelo PautaEngine. Preservar `known_points`/`possible_points`, limites e não duplicação de crédito entre alternativas. Uma falha de cálculo pode permitir carry-forward somente quando dependência, adoção e coerência estiverem comprovadas.
- A explicação de cada critério cita evidências e razões estruturadas, informa pontos e limitações, e não expõe raciocínio interno privado de modelo. A proposta nunca é HumanDecision ou FinalCorrection.

Nenhuma regra de “resposta igual ao gabarito = solução correta”. Um critério explicitamente conclusion-only pode aceitar resposta direta; um critério de justificativa exige os passos correspondentes. Não penalizar a mesma falha várias vezes sem regra docente explícita.

## 8. Estratégias alternativas

Referências são auxiliares, não whitelist de métodos. O grader pode identificar uma estratégia fora das candidatas e criar um registro de estratégia observada, ligado à solução, sem reescrever a rubrica aprovada.

1. Mapear o objetivo matemático de cada critério e suas exigências reais.
2. Verificar claims locais, domínio e encadeamento do método observado.
3. Conceder crédito elegível quando as mesmas exigências forem satisfeitas, mesmo com passos diferentes das referências.
4. Se a estratégia depende de matemática não coberta ou de interpretação ambígua, retornar REVIEW_ONLY com evidências e lacuna específica.
5. Se a própria rubrica exclui involuntariamente métodos válidos, registrar problema da rubrica e pedir decisão humana; eventual nova versão não altera o passado.

`max_of` já evita soma indevida entre caminhos alternativos preparados. Descobrir e validar caminhos inéditos é uma capacidade nova; `ClaimAlignment` sozinho não demonstra validade nem suficiência.

## 9. Verificadores matemáticos e Lean SELECTIVE

| Categoria | Evidência existente | Reuso e limite proposto |
|---|---|---|
| Arithmetic | `core/math_canonical/rational.py`, parser; checker `rational_equality.py` | Racionais exatos com Fraction/gramática limitada; separar avaliação determinística de certificado Lean. Domínio não suportado retorna desconhecido. |
| Algebraic | `equivalence.py`, `development.py`, checker `real_algebra.py` | Equivalência afim exata e projeções limitadas. Variáveis/domínio/divisores devem estar declarados; não ampliar cobertura por similaridade textual. |
| Numerical | Avaliações exatas e rotinas específicas nos checkers atuais | Não localizado solver numérico geral. Amostragem futura só evidencia casos testados; precisão/tolerância e domínio devem ser explícitos. Não prova identidade universal. |
| Symbolic | `parser.py`, `syntax.py`, `normalization.py`, `equivalence.py` | Canonicalização e comparação trivalente; árvores iguais podem provar equivalência representacional, não validade de todo argumento. |
| Deterministic | `FactResultsBuilder`, `bridge_facts`, verificações de domínio/estrutura | Reutilizar contrato e fingerprints; executar capacidades registradas, não código livre do LLM. |
| Finite enumeration | `tme/p3_machine.py`, `tme/p5_integer_break.py` e checkers TME | Implementações específicas permanecem Specialized. Novo verificador parametrizado só prova conjunto finito com limites e exaustividade demonstrados. |
| CAS-like | Primitivas limitadas em `core/math_canonical/`; não há dependência CAS em `pyproject.toml` | Não afirmar CAS geral existente. Introdução futura exige contrato de domínio, limites e evidência própria; fora do primeiro slice. |
| Lean | `lean/student_proof.py`, `run_lean.py`, renderers restritos de racionais/álgebra | SELECTIVE. Executar apenas claims representáveis, com timeout e artefato verificável; falha de compilação não prova falsidade. |
| Semantic residual | `hybrid_semantic.py`, `semantic_sufficiency.py`, adjudicator | Evidência semântica e suficiência, dependentes de contexto e modelo; nunca status formal por descrição natural. |

O plano define capabilities por tipo/domínio e precondições, não por `problem_id`. Os checkers existentes por problema mantêm sua rota. Para checks “gerados”, gerar inicialmente especificações declarativas/AST restrita a operações registradas; não executar Python/Lean arbitrário emitido por modelo.

Um certificado formal exige proposição concreta, versão de ferramenta, código compilado, artefato íntegro e vínculo fonte→representação→claim. Prova de referência não prova que o aluno fez aquele passo. `technical_error`, `indeterminate`, `refuted` e “não elegível à automação” são estados diferentes.

## 10. Safe automation e limites dos aprendizados P3

Esta base contém máquina/checkers TME P3 e experimentos semânticos. Não foi consultada uma linha P3 externa, e não foi localizada uma API geral com os enums AUTO_AWARD/AUTO_VETO/REVIEW_ONLY. Portanto, o diagnóstico não afirma que uma implementação posterior de segurança P3 está disponível aqui.

Há fundamentos reutilizáveis nesta base:

| Fundamento | Evidência | Generalização necessária |
|---|---|---|
| Representation fidelity | TranscriptionAcceptance/receipt; `grounding.source_matches`; gates de representação em `semantic.py` | Separar fidelidade da leitura, fidelidade da formalização e validade matemática. |
| Discourse state | `SemanticRole`, `generic_math.contextual_role`, `secondary_award_gate._scope_issue`, `sufficiency_context.py` | Gates atuais são limitados e alguns usam itens a–d. Criar contrato geral de papel/escopo/retificação, mantendo uncertainty. |
| Claim↔rubric binding | `rubric_links`, `ExpectedObligation`, `FactResult` fingerprints, `bridge_facts` | Binding versionado proveniente do pacote aprovado, sem mapas preparados P1–P5. |
| Automation eligibility | `can_secondary_award`, políticas de evidência e precedência do reconciler | Gate próprio por critério e versão de policy; necessário, mas insuficiente para provar a matemática. |
| Revisão | `needs_review`, `review_required`, motivos, shadow | Projeção comum de REVIEW_ONLY e rastreabilidade da razão específica. |

Política inicial conservadora por critério:

- **AUTO_AWARD:** fonte atribuível, representação fiel, premissas válidas, critérios/obrigações satisfeitos, verificação suficiente e ausência de conflito. Concordância de dois LLMs sozinha não satisfaz o gate.
- **AUTO_VETO:** veto ao crédito daquele critério por refutação pertinente e validada, sob as mesmas hipóteses, ou outra condição negativa explicitamente aprovada. Veto não significa nota zero da questão inteira; considerar alternativas e carry-forward.
- **REVIEW_ONLY:** ambiguidade, claim não atribuível, método não coberto, resíduo semântico insuficiente, conflito, erro técnico ou evidência incompleta. Ausência de extração não autoriza refutação.

Não herdar a aceitação de semântica “high confidence” do experimento híbrido como política default Dynamic. Confiança autorrelatada não é calibração. Toda policy é versionada; os dados de certificação determinarão se alguma classe pode ampliar automação.

## 11. Independent Reviewer

O secondary adjudicator atual avalia pendências e recebe contexto do pipeline primário; o sufficiency gate também trabalha sobre seleção anterior. São úteis, mas não satisfazem revisão independente integral.

Contrato proposto do reviewer: enunciado e assumptions congelados, rubrica aprovada, solução aceita completa, originais/referências de página quando disponíveis e evidências neutras com proveniência. Na primeira passagem, não enviar nota, decisões, explicações ou seleção exclusiva do grader; o reviewer faz seu próprio mapping e juízo por critério. Candidate references ficam opcionais e rotuladas, preferencialmente disponíveis após o juízo inicial para evitar ancoragem comum.

Uma segunda passagem pode receber resultados de verificadores e pedidos de revisão pontuais, sempre registrando o que foi revelado. Guardar julgamento cego original e revisão posterior separados. Se só foram usados claims escolhidos pelo grader, registrar independência limitada; o reviewer deve poder pedir novos checks.

Usar sessões/payloads distintos e registrar modelo/prompt/configuração. Modelos diferentes podem reduzir alguns erros correlacionados, mas não garantem independência estatística. Reutilizar um resultado determinístico íntegro é permitido; isso é evidência compartilhada, não uma segunda descoberta independente.

Falha/timeout do reviewer deixa a revisão pendente. Para o primeiro slice, revisão independente é obrigatória para todas as três soluções; indisponibilidade não pode ser escondida como acordo.

## 12. Reconciliação

A reconciliação compara decisões **por critério e claim**, incluindo diferenças de domínio, hipóteses, fonte e método. Ela produz evidência reconciliada e motivos; o scoring aplica a rubrica. Não calcula média de duas notas.

| Estado proposto | Regra |
|---|---|
| AGREEMENT | Grader e reviewer concordam sobre requisitos/evidência, sem conflito de verificação. Ainda depende do gate de automação. |
| REVIEWER_DISAGREEMENT | Divergência de suficiência, mapping, método ou pontos: guardar ambas as avaliações e localizar a diferença. |
| MATHEMATICAL_CONFLICT | Verificador contradiz claim relevante ou há resultados incompatíveis para o mesmo claim/contexto; revisar inclusive representação e premissas. |
| INSUFFICIENT_EVIDENCE | Falta evidência para decidir, sem inferir erro do aluno. |
| REVIEW_REQUIRED | Estado agregado da questão quando qualquer pendência material impede automação segura. |

Uma refutação íntegra de um passo tem precedência sobre apoio semântico ao **mesmo passo**, mas não invalida automaticamente outro caminho correto. Um conflito em nível de obrigação sem identidade de claim não autoriza veto irrestrito. Uma prova local válida também não demonstra conclusão global sem os vínculos de dependência.

Persistir entradas/saídas independentes, checks, regras aplicadas e decisão por critério. Definir limites de tentativas e de chamadas; evitar um ciclo de agentes até obter concordância. Uma arbitragem humana permanece possível e auditável.

## 13. Contrato do engine e adapter Dynamic

### Contrato atual observado

- Entrada de produto: `audit_question(case_id, request: AuditRequest, user)`; request contém transcription_id, revision_number, acceptance_id e execution_key.
- Contexto: assessment_id, participant_id, exam_submission_id, question_attempt_id, max_score, `engine_mode='TME_CURRENT'`, adapter_version.
- Execução/persistência: `AuditService` produz `AuditRun` COMPLETED ou FAILED; RUNNING não é um estado persistido desse modelo.
- Resultado aceito: `TMEAuditResult | AuditResponse`. Para contexto de questão, `AuditRun.coherent` exige completion e `source.tme_context`.
- Projeção: `question-audit.v1`, suggested_score/max_score, rubric_items, evidences, checker_summary, review_required/reasons, warnings, technical_uncertainty, engine_version/config, trace_reference, eventos e comparação.

### Extensão proposta

Criar resultado/contexto Dynamic discriminado por schema, mantendo todos os desserializadores legados e o AuditRun único. Evitar falsificar um `TMEAuditResult` ou encher campos ITA de certificados vazios. O adapter converte o resultado interno Dynamic para a mesma projeção pública de questão.

| Saída desejada | Projeção/reuso | Adição necessária |
|---|---|---|
| engine_mode, engine_version | Campos de produto já existentes | Literal DYNAMIC/contexto genérico; metadata de família Specialized sem reescrever TME_CURRENT |
| suggested_score, max_score | Mesmo significado público, null permitido na sugestão | Validação Decimal/invariantes internas; máximo deve coincidir com assessment e rubrica |
| rubric decisions | `rubric_items`, árvore de critérios, reason, known/possible points | Mapear IDs da revisão aprovada, incluindo review por critério |
| evidences | IDs, texto, spans, grounding e referência de página | Mapa fonte normalizada→original validado; não inventar páginas |
| checker statuses | `checker_summary` | Distinguir mecanismo, escopo e status; preservar prova/refutação/erro |
| review/technical uncertainty | Campos atuais | Motivos estáveis de Dynamic/reviewer/reconciliation; falha nunca vira nota zero |
| trace/provenance | audit_run_id, source/result hashes, required_artifacts | Manifesto package/rubric/plan/policy/prompt/model/version e traces separados |

Pontos de extensão obrigatórios: schemas; dispatch de AuditService; digest/identidade da fonte e configuração; captura/verificação do manifesto de artefatos; projector por tipo de resultado; seleção de run oficial versus shadow. `AuditService._identity` usa source_hash e execution_key: o hash novo deve incorporar contexto congelado ou uma identidade de execução adicional versionada, para que modos/pacotes diferentes nunca dedupliquem entre si. Preservar fórmula antiga para leitura de runs legados.

**Limite D5/D6:** hoje `HumanDecision` e confirmação exigem suggested_score não nulo. Não inventar uma nota para contornar isso. No slice, casos resolvidos têm sugestão e seguem D5/D6; casos REVIEW_ONLY com nota nula aparecem em D3/D4, preservam AuditRun e ficam bloqueados para fechamento. Uma futura decisão humana sem sugestão exige extensão explícita/testada do contrato compartilhado, fora de DY1. “Compatível com D1–D7” inclui respeitar esse bloqueio.

## 14. UI docente e listas versus provas

A futura área de preparação deve se conectar ao formulário existente de avaliações: criar questão, colar várias questões e, depois, importar documento. Para cada questão, mostrar enunciado, status da preparação, alertas, referências candidatas, proposta/própria rubrica, edição e aprovação com versão visível.

Após aprovação, reutilizar Original / Transcrição / Comparar → AuditRun → HumanDecision → FinalCorrection. D1–D7 recebem a projeção comum; não interpretam modelos, prompts ou verifier plans para calcular decisões. UI de preparação é nova capacidade, não redesenho do workspace de correção.

A implementação atual exige atenção a endpoints TME, seleção por catálogo, allowlist de figuras e navegação de casos legados. No slice, preferir questões textuais e contexto real assessment/item/exam; não codificar Dynamic em nomes fictícios de questões TME. Expandir assets seguros depois. Acesso institucional ao workflow D1–D7 é um gap de autorização/composição, não motivo para usar demo sem auth.

| Policy versionada | LISTA | PROVA |
|---|---|---|
| Objetivo | Feedback formativo e progresso por critério | Pontuação auditável e homologação |
| Automação | Ampliável apenas em capabilities avaliadas como seguras | Gates mais conservadores e maior uso de REVIEW_ONLY |
| Reviewer | Obrigatório no experimento inicial; futura redução só por política avaliada | Obrigatório; falta do reviewer bloqueia automação |
| Publicação | Feedback conforme política explícita; não confundir com nota final | Finalização humana pelo ciclo existente |
| Conflito/incerteza | Feedback limitado e encaminhamento | Revisão obrigatória e fechamento bloqueado quando não houver decisão válida |
| Lean | SELECTIVE | SELECTIVE, nunca obrigatório por ser prova |

Ambas usam o mesmo engine Dynamic, com policy congelada no run. Até haver evidência de certificação, não habilitar finalização automática em nenhuma modalidade.

## 15. Reprodutibilidade e invalidação

Versionar independentemente: statement, preparação, candidate references, rubric content/approval, verifier plan/capabilities, engine e policy. Identificar também normalizador, prompt/schema e configuração efetiva dos modelos. Guardar inputs/outputs, tempos, hashes e falhas sem segredos.

O run deve permitir reconstruir as **entradas e decisões registradas** por leitura dos artefatos, sem chamar novamente um modelo e sem depender do checkout original de dezembro/P3. Reproduzir computacionalmente uma execução futura é uma capacidade distinta e deve declarar dependências disponíveis.

O stale atual só detecta transcrição posterior. Uma mudança de configuração do assessment exige um estado derivado adicional de incompatibilidade de binding, ou extensão versionada desse cálculo. Nunca recalcular silenciosamente um run com rubrica/plano novos. Ao mudar o binding oficial, invalidar confirmação derivada pertinente e exigir nova análise/decisão, preservando histórico; avaliação finalizada deve ser reaberta pelo ciclo D6 antes de mudança operacional.

Nova revisão global de rubrica não invalida automaticamente avaliações que continuam pinadas à anterior. A revisão vigente para novas avaliações e a revisão usada por um run são conceitos distintos.

## 16. Certificação D7 e comparações

Já disponíveis em `CertificationRecord`: assessment/participant/question/attempt IDs, problem_id, transcription_version, audit_run_id, source/result hashes, engine_mode/version, suggested_score, human_decision_score, human_gold_score, max_score, IDs de decisão/finalização/gold, gold_version/source/dataset/hash, review, technical uncertainty, checker_counts, rubric_decisions, rubric_gold e timestamps.

`certification_metrics.py` calcula MAE, viés, concordância exata, tolerâncias de 1/2 ponto, contagens de sobre/subpontuação, presença de crédito por critério, taxas de revisão/erro e ajustes humanos; agrupa por engine_mode. Não fornece gold por obrigação: o código declara essa indisponibilidade. Tolerâncias absolutas precisam ser interpretadas em função da escala; comparar máximos diferentes sem normalização é inadequado.

`certification.build(selection='current')` seleciona o run da leitura atual por modo; `finalized` usa o run congelado no fechamento. Há estrutura para ambos os modos, mas hoje a criação de contexto só aceita TME_CURRENT. Gold é independente e versionado; a configuração exige SHADOW_EVALUATION e `official_correction_affected=False`. Rotas/ownership e storage de certificação ainda estão no escopo TME.

Extensões necessárias, sem criar outra certificação:

1. Incluir family/mode normalizado, package/rubric/plan/policy hashes e identificação do experimento nos registros novos.
2. Permitir explicitamente os dois adapters e manter execução oficial separada da shadow, sem que a “última execução” troque a sugestão confirmável.
3. Adicionar pareamento SPECIALIZED×DYNAMIC por assessment item, participante, mesma fonte/transcrição, statement e rubrica/escala comparáveis; usar run IDs congelados, não só seleção latest.
4. Se rubricas diferirem, registrar o mapeamento humano e limitar conclusões; igualdade de máximo não garante comparabilidade. Excluir pares não comparáveis com denominador/motivo explícitos.
5. Reusar gold independente para DYNAMIC×HUMAN GOLD e SPECIALIZED×HUMAN GOLD. HumanDecision não substitui gold cego.
6. Manter ausências/abstenções/falhas na cobertura e denominadores. Reportar erro entre automatizados e taxa de cobertura; não melhorar MAE artificialmente excluindo casos difíceis.

Não é possível exigir comparação Specialized em todo problema inédito sem preparar novos assets especializados. Para a comparação entre motores, usar subconjunto de problemas **já suportados** pelo Specialized, dando ao Dynamic apenas o enunciado e rubrica aprovados. Benchmark de inéditos mede Dynamic×gold separadamente. Não criar checkers Specialized novos nesta tarefa para tornar o desenho experimental possível.

## 17. Matriz de gaps e riscos

| Capacidade | Já existe | Reutilizável | Novo módulo/capacidade conceitual | Risco principal |
|---|---|---|---|---|
| Problem creation | Catálogos curados, AssessmentItem | Assessment/auth/publicação | Registro/versionamento docente e resolver de problemas | Contornar catálogo/ownership ou misturar versões |
| Preparation | Assets manuais e referências TME/ITA | Schemas de evidência e primitives | Preparador de pacote e release | Referência gerada falsa tratada como verdade |
| Rubric suggestion | Pauta declarativa | PautaConfig, validação de somas | Rubric Assistant | Rubrica vaga, redundância ou método único |
| Rubric versioning | Schema/hash, arquivos de pauta | Hash/atomicidade/lifecycle patterns | Revisões, aprovação e binding | Rubrica latest mudar nota antiga |
| Verifier planning | Checkers preparados | Parser/grounding/proof lifecycle | Capability resolver e plano congelado | Código arbitrário ou domínio incorreto |
| Dynamic grading | Extratores e graders especializados | Claim/evidence/PautaEngine | Grader de problema inédito | Confundir plausibilidade com suficiência |
| Reviewer | Adjudicator e sufficiency gate | Transporte/schema/evidências | Reviewer cego com trilha de independência | Ancoragem/erros correlacionados |
| Reconciliation | Experimento TME híbrido | Padrão de precedência/conflito | Reconciler por claim/critério do pacote | Média de notas ou veto fora de escopo |
| Safe automation | Gates parciais e needs_review | Source fidelity e estados comuns | Eligibility/policy por critério | AUTO_AWARD sem cobertura real |
| Engine adapter | CorrectionEngine/projeção de questão | AuditRun, locks, eventos | Contexto/resultado Dynamic e dispatch explícito | Colisão de run, perda de hashes, fallback silencioso |
| UI | Gestão, captura, workspace D1–D7 | Componentes e contrato de produto | Preparação/rubrica e conexão de escopo | Duplicar fluxo ou afrouxar autorização |
| Certification | Gold/versionamento/exports/métricas por modo | D7 | Pareamento, contexto Dynamic e métricas de cobertura | Comparar fontes/rubricas diferentes |
| Human closure sem sugestão | D5 exige sugestão não nula | Cadeia D5/D6 | Extensão futura específica, se necessária | Fabricar zero para habilitar confirmação |

Riscos transversais: mudanças no hash legado tornam histórico ilegível; `accepted_audit.audit_context` hasheia amplamente arquivos de diretórios e mudanças aditivas podem alterar a versão TME de novas execuções mesmo sem alterar scoring; nova versão técnica não deve ser confundida com regressão matemática. Catálogo fixo aparece em múltiplas fronteiras, então liberar apenas a UI não basta. Rubricas e soluções recebidas são dados não confiáveis; instruções embutidas não devem mudar o contrato. Limites de payload/custo/timeout e invariantes da fonte permanecem obrigatórios.

Não usar um comentário “genérico” como justificativa para reutilizar toda a implementação: `bridge.py` mistura contratos gerais e mapa P1; `real_algebra.py` depende de representação/collect confiáveis; o reconciler híbrido contém dependências por problema.

## 18. Primeiro dataset experimental proposto

Não criado nesta tarefa. Proposta: oito problemas de ensino básico/médio, com versões de enunciado e rubricas humanas congeladas antes da avaliação.

| Problemas | Cobertura | Variações necessárias |
|---|---|---|
| 1–2 | Aritmética racional e proporcionalidade | Fração/decimal equivalente, conta incorreta, resposta sem desenvolvimento quando exigido |
| 3 | Equação linear e domínio | Caminhos por equivalência ou operações inversas; passo inválido seguido de resposta correta |
| 4 | Álgebra/fatoração | Expansão e fatoração alternativas, divisão proibida ou perda de solução |
| 5 | Função afim | Interpretação de coeficientes e cálculo por estratégias diferentes |
| 6 | Combinatória finita simples | Enumeração completa versus fórmula, duplicatas/omissões |
| 7 | Probabilidade elementar | Enumeração ou árvore; espaço amostral e condicionamento explícitos |
| 8 | Geometria textual simples | Relações declaradas, duas derivações; evitar leitura automática de diagrama no primeiro benchmark |

Para cada problema: rubrica humana, pelo menos duas corretas (uma alternativa), duas parciais e duas incorretas. Planejamento inicial: 48 soluções, ainda sem produção dos dados. Acrescentar casos de retificação, hipótese, citação, resposta ambígua, prompt injection e falha de ferramenta em conjunto de robustez identificado separadamente.

Separar desenvolvimento e holdout por problema/família; não ajustar prompts aos casos finais. Dois avaliadores humanos independentes e adjudicação de divergências devem produzir gold com evidência por critério. Coorte Specialized×Dynamic utiliza problemas suportados já existentes, como controle separado, mantendo benchmarks P1/P2/P3 imutáveis.

## 19. Plano incremental e critérios de aceite

Os nomes abaixo são responsabilidades propostas, não diretórios aprovados ou criados. Ordem principal DY1→DY2→DY3→DY4→DY5→DY6→DY7; desenhar interfaces de UI e certificação desde DY1, sem antecipar implementação.

| Etapa | Entregável | Testes necessários | Critério de aceite | Regressão Specialized |
|---|---|---|---|---|
| DY1 — Package + Rubric lifecycle | Contratos/revisões imutáveis, autoria/approval, configuração explícita assessment/item e manifesto; resolver de problema documentado | Transições, acesso por dono, soma/caps/IDs, concorrência de aprovação, hashes, reload e pins; leitura de documentos antigos | Rubrica própria e sugerida podem ser editadas/aprovadas sem alterar revisão anterior; pacote resolve revisão exata; nenhuma execução usa draft | Assessments/auth/integridade/contratos D1–D7 e pauta; nenhum dispatch matemático mudado |
| DY2 — Automatic preparation | Preparação de texto, múltiplas referências candidatas, consistency checks, sugestão e plano declarativo | Modelo fake gravado, referência falsa, ambiguidade, domínio não suportado, timeout, alteração pós-aprovação | Professor vê incertezas e aprova release; nenhuma referência ganha status de prova por vir do LLM | Core math/claims/pauta/recognition; catálogos e assets Specialized intactos |
| DY3 — Dynamic grader + adapter | Grader por critério, resolver autorizado, contexto/resultado Dynamic e AuditRun real pela infraestrutura existente | Fonte aceita, idempotência por modo/pacote, hash/manifesto, parcialidade, método alternativo, null/erro; contratos de projeção | Três classes de solução geram runs persistidos e recarregáveis, com nota/intervalo/razão e rastreabilidade; D3/D4 exibem sem lógica matemática nova | Suítes de submission audits, accepted TME, D1–D7, ITA/TME; parity de resultados e hashes legados |
| DY4 — Independent reviewer | Avaliação cega e revisão pós-check separadas | Spy de payload impede nota/conclusão do grader; descoberta de evidência própria; timeout/discordância | Julgamento por critério independente da conclusão inicial, com status de independência verificável | Secondary/semantic/model-compat existentes sem alteração de prompts/expectativas |
| DY5 — Reconciliation + safe automation | Estados, eligibility e policies LISTA/PROVA; isolamento shadow/oficial | Confiança sem prova, refutação local, duas estratégias, conflito de assumptions, abstenção, carry-forward | AUTO_AWARD/AUTO_VETO apenas nos gates definidos; demais REVIEW_ONLY; nenhuma média; shadow não muda D5/D6 | Bridges P1–P5, scope/fidelity, scoring policies e confirmações/finalização |
| DY6 — Professor UI | Criação textual, preparação, fornecer/sugerir/editar/aprovar rubrica e acesso ao workspace existente | JS/DOM e jornada real com auth, versão concorrente, warnings, três soluções, reanálise/fechamento | Professor conclui preparação e correção usando D1–D7; exibe revisão usada; original/transcrição permanecem fiéis | Todas as suítes JS TME, assessments, teacher workflow, acessibilidade e D1–D7 |
| DY7 — Certification experiment | Benchmark congelado, gold independente, pareamento por modo e exports D7 | Denominadores, ausências, rubricas/versões incompatíveis, current/finalized, reimport/restart | Resultados por motor e cobertura reconstruíveis; compara motores somente nos pares elegíveis; nenhum efeito na correção oficial | Certification, finalization, reproducibility, exports e benchmark Specialized inalterado |

Não há motivo para adiar todas as abstrações ao DY6: o resolver/contexto/adapter são necessários já em DY3 para um AuditRun válido. Tampouco há motivo para mover o Specialized em DY1. Generalizar escopo institucional e autorização do ciclo existente deve acompanhar o primeiro uso Dynamic autenticado, com critérios de acesso testados.

### Primeiro vertical slice de ponta a ponta

Escolher **um problema textual novo de equação linear**, com resposta e desenvolvimento verificáveis por aritmética/álgebra limitada. A autoria do enunciado é do professor; o sistema prepara e sugere rubrica; o professor a vê, aceita ou edita, e aprova uma revisão. Nenhum asset/checker manual por problema novo é necessário para executar esse slice.

Receber três soluções diferentes, cobrindo correta, parcial e incorreta. Uma correta por método diferente da referência pode ser a própria solução correta do trio; incluir uma quarta alternativa se necessário para testar os dois caminhos. O professor mantém gold independente. Para cada solução: critérios/pontos/razões, fonte aceita, verificação seletiva, revisão independente, reconciliação e AuditRun com manifesto completo.

Aceite integrado:

1. Problema não pertence aos registries ITA/TME e usa modo DYNAMIC explícito.
2. Preparação automática produz referências candidatas e rubrica; aprovação docente é necessária e registrada.
3. Os casos resolvidos recebem pontuação coerente com a rubrica humana, incluindo crédito parcial real, sem soma indevida de métodos.
4. Cada decisão aponta a evidências reais e checks; alternativa correta não perde ponto só por método.
5. O reviewer não recebe a nota/conclusão inicial; divergência e falha forçadas ficam visíveis em testes.
6. Os runs persistem após reload e distinguem pacote/rubrica/policy/engine. Edição da rubrica não altera resultados anteriores.
7. D3/D4 mostram a projeção comum; sugestões numéricas confirmáveis seguem D5/D6; D7 exporta o experimento. Caso sem sugestão fica explicitamente bloqueado para fechamento, conforme contrato atual.
8. Lean pode estar desabilitado por política explícita SELECTIVE sem invalidar o slice; não se anuncia formalização dos passos não formalizados.
9. O resultado Specialized permanece igual nas regressões pertinentes. Nenhuma mudança no frontend ou engine é realizada por este diagnóstico.

O slice integrado se completa com DY1–DY6 e um recorte de validação D7; DY7 amplia para o benchmark, não transforma a criação do dataset em pré-requisito de DY1.

## 20. Plano de testes, preservação e encerramento

### Suítes existentes identificadas

| Grupo | Arquivos de teste reais | Quando exigir |
|---|---|---|
| Assessments/auth/storage | `tests/test_assessments.py`, `test_core_auth.py`, `test_core_institutional.py`, `test_submissions.py`, `test_transcriptions.py`, `test_teacher_decisions.py` (todos sob `tests/`) | Toda etapa que toca contratos, dados ou entrada |
| AuditRun/integração | `tests/test_submission_audits.py`, `tests/test_tme_accepted_integration.py`, `tests/test_cap04_parity.py`, `tests/test_cap04_integrity_regressions.py`, `tests/test_cap04_global_semantics.py` | DY1 contratos e DY3–DY7 integração |
| D1–D7 | `tests/test_tme_full_exam.py`, `tests/test_tme_review_workspace.py`, `tests/test_tme_question_audit.py`, `tests/test_tme_reanalysis.py`, `tests/test_tme_human_confirmation.py`, `tests/test_tme_finalization.py`, `tests/test_tme_certification.py` | Baseline de integração em cada etapa |
| Operação/demo | `tests/test_demo_december_operations.py`, `tests/test_tme_demo_auth.py`, `tests/test_tme_home_summary.py`, `tests/test_tme_navigation.py` | Mudanças em composição, rotas, storage ou UI; nunca iniciar a demo antiga por conveniência |
| Catálogos/pauta | `tests/test_problem_assets_validation.py`, `tests/test_problem_assets_contracts.py`, `tests/test_problem_router_coverage.py`, `tests/test_tme_problem_catalog.py`, `tests/test_pauta_engine.py`, `tests/test_tme2_p1_pauta_bridge.py` até `tests/test_tme2_p5_pauta_bridge.py` | Toda alteração de resolver, rubrica, evidence ou scoring |
| Claims/verificação | `tests/test_claim_fidelity.py`, `tests/test_common_claim_pipeline.py`, `tests/test_claim_alignment_obligations.py`, `tests/test_math_canonical.py`, `tests/test_math_canonical_pipeline.py`, `tests/test_generic_student_math.py`, `tests/test_generic_student_math_pipeline.py`, `tests/test_student_proof_semantics.py` | DY2/DY3/DY5 e qualquer mudança de primitivas compartilhadas |
| Semântica/segurança | `tests/test_secondary_adjudicator_contract.py`, `tests/test_secondary_false_credit.py`, `tests/test_secondary_evidence_ids.py`, `tests/test_scope_boundary.py`, `tests/test_scope_boundary_replay.py`, `tests/test_semantic_sufficiency.py`, `tests/test_sufficiency_dev_regressions.py`, `tests/test_tme_hybrid_grader.py`, `tests/test_tme_model_compat.py` | DY3–DY5 e mudanças em transporte/prompts/gates compartilhados |
| Reconhecimento | `tests/test_recognition.py`, `tests/test_recognition_invariants.py`, `tests/test_recognition_preview_auth.py`, `tests/test_official_mathpix_flow.py`, `tests/test_hmer_audit_parity.py` | Entrada/preview/transcrição e DY6; mocks não demonstram acurácia live |
| Reports/proveniência | `tests/test_pedagogical_report.py`, `tests/test_public_audit_boundary.py`, `tests/test_gov01_public_api.py`, `tests/test_reproducibility.py` | Adapter, output, manifest e export |
| Specialized matemático | `tests/test_mvp_ita_10_questions.py`, `tests/test_level1_f2_suite_regressions.py`, `tests/test_f2_strong_lean_suite.py`, famílias `tests/test_f2q*_student_claim_checks.py`, `tests/test_f2q*_strong_certificate.py`, `tests/test_f2q*_rubric_adjustments.py`, `tests/test_ita2025*.py`, bridges TME P1–P5 | Em integração/release de cada etapa; foco adicional nas dependências alteradas |
| Frontend D1–D7 | `tests/js/test_full_exam.cjs`, `test_review_workspace.cjs`, `test_question_audit.cjs`, `test_question_reanalysis.cjs`, `test_human_confirmation.cjs`, `test_finalization.cjs`, `test_certification.cjs` (todos sob `tests/js/`) | Integração de contrato e DY6/DY7 |
| Frontend demais | `tests/js/test_assessments_ui.cjs`, `tests/js/test_correction_workspace.cjs`, `tests/js/test_teacher_transcription_view.cjs`, `tests/js/test_tme_accepted_integration.cjs`; demais `tests/js/test_*.cjs` | Mudança em componentes compartilhados e release |

Não foi encontrado `tests/test_correction_engine.py`; a cobertura real do adapter está principalmente em `test_tme_question_audit.py`, `test_tme_reanalysis.py` e testes de integração/human confirmation. Não inventar uma suíte pelo nome conceitual.

A CI atual usa Python 3.11 e `python -m pytest -q`, com `CONFIA_ENABLE_LLM_FORMAL_STEPS=0`; `.github/workflows/lean_action_ci.yml` também executa `lake build`. O plano é preparar um ambiente **próprio deste worktree**, respeitando `lean-toolchain` e `lake-manifest.json`, e executar:

```sh
# No worktree Dynamic, com ambiente local já preparado e sem flags apontando a outros worktrees.
CONFIA_ENABLE_LLM_FORMAL_STEPS=0 PYTHONPATH=app python -m pytest -q
node --test tests/js/test_*.cjs
lake build
```

Comandos são plano futuro, não resultados desta auditoria. `tests/conftest.py` remove OPENAI_API_KEY em testes e há testes que dependem de Lean/Mathlib preparados. Não copiar venv/cache dos worktrees proibidos. `scripts/demo_december.sh` possui default de Python absoluto para outro checkout; não foi executado. Qualquer uso futuro requer override local explícito e isolamento de runtime/roots.

Para cada etapa: executar os testes novos da capacidade e os grupos afetados durante desenvolvimento; antes de aceitar a etapa integrada, executar regressão Python/JS e build Lean no ambiente local preparado. Registrar falhas ambientais separadas de regressões, sem alterar expectativas, fixtures ou versões para obter verde. Não chamar LLMs pagos/live como parte implícita de regressão. Benchmarks curados continuam congelados; novos casos Dynamic pertencem a uma coorte identificada, sem sobrescrever P1/P2/P3.

### Resultado desta tarefa

Foram verificados branch, HEAD, tag, merge-base, estado inicial e código necessário ao mapeamento. Foi produzido somente este diagnóstico no diretório `docs/audits` já existente. Nenhuma suíte de aplicação, build Lean, benchmark ou chamada de modelo/reconhecimento foi executada: esta tarefa é documental, sem mudança de runtime. Isso não constitui certificação de regressão em execução.

Preservar integralmente Specialized, TME e December RC; não simplificar pipelines, mover checkers, alterar frontend, exigir Lean para questão arbitrária, duplicar D1–D7 ou depender de outro worktree. Nenhum `git add` ou commit integra esta tarefa.

Os gaps encontrados têm encaminhamento conservador suficiente para começar DY1: pacote/revisões/aprovação e binding explícito, mantendo a rota atual. A confirmação humana sem sugestão, automação de resíduo semântico, CAS geral e pareamento entre rubricas diferentes permanecem fora do aceite de DY1 e devem ter decisões específicas antes de serem implementados. Não bloqueiam o desenho do lifecycle solicitado.

READY_FOR_DYNAMIC_DY1
