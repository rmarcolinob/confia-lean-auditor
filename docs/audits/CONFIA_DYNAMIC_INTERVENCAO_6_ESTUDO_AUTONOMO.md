# ConfIA DYNAMIC — Intervenção 6: estudo autônomo sem nota

Data: 26/11/2026. Branch: `codex/dynamic-development`.

## Resultado e delimitação

O módulo do aluno passa a oferecer `/#student/study`: problema do catálogo escolar ou enunciado próprio, texto/fotografias/PDF, confirmação explícita das leituras e da interpretação, critérios provisórios, análise qualitativa, pistas progressivas e novas tentativas. O percurso foi demonstrado com texto e fotografia sintética, reconhecimento e pareceres simulados. Isto valida integração e contratos; não valida a correção científica dos pareceres nem a qualidade pedagógica com estudantes reais.

O contexto `SELF_STUDY` não cria boletim, `FinalCorrection`, decisão docente ou nota institucional. A ausência de pontuação é uma propriedade da projeção pública do servidor, testada recursivamente, e não somente do frontend. Os julgamentos e pesos internos ficam nos artefatos privados da tentativa.

A Intervenção 5 foi consolidada separadamente no commit `d40a7b08ff5eef60b012f382e64fa82a604c05fc`, publicado exclusivamente em `origin/codex/dynamic-development`. O `ls-remote` confirmou esse mesmo commit. **Nenhuma alteração da Intervenção 6 foi commitada ou publicada.**

A tag anotada `SPECIALIZED-TME2-RC1` continua com objeto `0c64e318a26e21f71fe3097c66ee17a5206dd8a3`, apontando para `c03403fe5b83d9db9df172882bd69af3dfa2d027`, tanto localmente quanto no remoto. Não houve alteração de pauta, política matemática, PautaEngine, checkers ou Lean; não houve merge na main.

## Arquivos e responsabilidades

Todos os caminhos abaixo são relativos à raiz deste worktree.

| Arquivo | Alteração e justificativa |
| --- | --- |
| `app/confia_lean_auditor/dynamic/study_models.py` | Contratos específicos de leitura, pacote provisório, tentativa e relatório qualitativo; reutiliza critérios e níveis de crédito existentes. |
| `app/confia_lean_auditor/dynamic/study_capture.py` | Adaptador de fonte para armazenamento original, renderização PDF/imagens e transcrições existentes. Não implementa OCR. |
| `app/confia_lean_auditor/dynamic/study_service.py` | Autoria, versões, confirmações, execução dos componentes DYNAMIC, persistência privada e histórico. |
| `app/confia_lean_auditor/dynamic/study_feedback.py` | Projeção qualitativa e comparação de tentativas; valida vínculo literal das evidências e das pistas. |
| `app/confia_lean_auditor/dynamic/study_router.py` | Gateway autenticado do aluno, projeções sem notas, originais protegidos e erros próprios do contexto. |
| `app/confia_lean_auditor/dynamic/provider.py` | Prompts adicionais para interpretação, critérios provisórios e feedback progressivo, pelo transporte existente. |
| `app/confia_lean_auditor/auth/dependencies.py` | Protege fontes privadas contra outros alunos, professores e acessos genéricos do modo legado; impede escrita fora do gateway. |
| `app/confia_lean_auditor/submissions/{schemas.py,store.py,body_limit.py}` | Tipo de origem aditivo `self_study`, referências de PDF/múltiplos originais, validação de integridade e limites de upload; preserva leitura dos contratos anteriores. |
| `app/confia_lean_auditor/recognition/service.py` | Reconhece a nova origem usando o mesmo adaptador de imagens existente. |
| `app/confia_lean_auditor/main.py` | Registra o novo router. |
| `app/confia_lean_auditor/static/dynamic-self-study.js` | Interface de estudo, confirmação, originais, histórico e feedback, sem renderização de notas. |
| `app/confia_lean_auditor/static/{index.html,shell.js,platform-presentation.js,styles.css}` | Entrada e rota do aluno; estilos locais reaproveitam cards, controles e navegação existentes. |
| `tests/test_dynamic_self_study.py` | Exercita os engines reais com providers explicitamente simulados. |
| `tests/js/test_dynamic_self_study.cjs` | Sem notas na apresentação, progressão explícita, consentimento e proteção contra descarte de leitura editada. |
| `tests/js/test_platform_presentation.cjs` | Atualiza a expectativa de cards para incluir Estudo sem remover funcionalidades anteriores. |

## Arquitetura e contratos

`POST /dynamic/self-study` cria estudo privado do aluno autenticado, com etapa escolar do 6º ano do Fundamental à 3ª série do Médio. O catálogo contém cinco enunciados de matemática escolar, sem regras ou verificadores próprios por questão. Novo enunciado é permitido.

Os gateways `/reading`, `/recognize` e `/confirm-reading` existem para o enunciado e para cada tentativa. O recebimento usa a captura multipágina existente, preserva arquivos originais e páginas derivadas, e registra fonte `self_study` com `self-study-source.v1`. Textos originais também são preservados. A conferência usa autor, número de revisão e hash; reconhecimento automático nunca equivale à confirmação humana. Trecho explicitamente ilegível bloqueia o prosseguimento.

`/prepare` reutiliza a preparação e a análise determinística DYNAMIC, gerando um pacote versionado. O aluno confirma a interpretação por `/confirm-interpretation`; isso não equivale a aprovação institucional de rubrica. Critérios são `PROVISIONAL_FORMATIVE`, com níveis/dependências do contrato atual. A normalização interna usa máximo 3 exclusivamente para compatibilidade com o engine; não é publicada como nota. Ambiguidades declaradas, hipóteses inferidas e falhas técnicas mantêm preparação pendente.

`/attempts/{id}/analyze` usa efetivamente:

1. `DynamicSolutionGrader.grade` — análise de claims, verificações disponíveis e avaliação semântica existente.
2. `blind_input` e `semantic.review_phase` — Reviewer independente.
3. `compare_review` — comparação por critério.
4. `reconcile_criteria`, perfil `FORMATIVE_LIST` — mesma reconciliação e precedência matemática existentes.
5. `study_feedback.project` — projeção qualitativa posterior, sem alterar crédito ou decisões do engine.

Não há acesso a endpoints docentes, usuário docente artificial ou motor matemático paralelo. Este gateway persiste a análise e os artefatos do engine em diretório próprio da tentativa, sem criar uma correção oficial no registro institucional de AuditRuns. Proveniência integral, análises, comparação e reconciliação ficam preservadas nesse armazenamento privado.

`self-study-report.v1` expõe objetivos, estados qualitativos, evidências com offsets/hash, orientações, incertezas e comparação. Estados: `SUPPORTED`, `PARTIAL`, `MATHEMATICAL_ERROR`, `NEEDS_EXPLANATION`, `UNCERTAIN`, `TECHNICAL_ERROR`. Não atendimento sem erro identificado não é convertido em erro matemático; falha técnica não gera zero. Concordância semântica não é certificação formal. `formal_verification_performed` é explicitamente falso: o novo fluxo não executa Lean.

Fontes têm dono, integridade e vínculo ao estudo. Dados privados permanecem protegidos inclusive quando o modo de demonstração legado está habilitado. Leituras genéricas não permitem a professores ou a outro estudante acessar o estudo; escritas genéricas não podem contornar o controle de versões. Endpoints próprios exigem sessão de estudante ativa mesmo quando autenticação institucional está desabilitada para outras rotas de demonstração.

## Política pedagógica e histórico

`self-study-feedback.v1`:

- Nível 1: projeção conservadora do objetivo que exige atenção, com citação da solução; não publica justificativas longas do provider nem resolução de referência.
- Nível 2: pista matemática solicitada pelo estudante.
- Nível 3: explicação do conceito/procedimento, após a pista.
- Nível 4: desenvolvimento orientado ou resolução, após os níveis anteriores e solicitação explícita adicional.

Níveis 2–4 usam o provider existente; cada orientação deve identificar critério e citar literalmente evidência vinculada. Falhas/citações inventadas não são apresentadas como orientação válida. Os níveis 2–3 não recebem soluções de referência. A instrução para não antecipar a resposta é política de geração, **não uma garantia formal sobre o conteúdo de um LLM real**.

Cada tentativa fixa versão/hash do pacote e da leitura. Tentativas analisadas são imutáveis; revisões produzem uma nova tentativa. Mudança do enunciado exige nova preparação antes de novas análises, preservando pacotes e relatórios antigos. Comparações são qualitativas, apenas entre tentativas com o mesmo pacote: erro revisto, objetivo ainda pendente, evidência diferente ou inalterada. Não há média, percentual, ranking ou progresso convertido em nota. A comparação descreve análises automáticas e não certifica aprendizagem.

## Demonstração no navegador

Servidor local isolado, com usuários de teste e dados sintéticos, sem credenciais de produção e sem rede de providers. Percurso `/#student/study`:

1. Enunciado independente `2x + 6 = 18`, leitura e interpretação explicitamente confirmadas.
2. Tentativa textual parcial: feedback qualitativo e evidência literal.
3. Pistas nos níveis 2 e 3; nível 4 bloqueado sem consentimento, disponível após solicitação.
4. Nova tentativa com desenvolvimento completo: comparação qualitativa e preservação da anterior.
5. Terceira tentativa por PNG sintético: reconhecimento simulado, edição, salvamento e confirmação da leitura, consulta de original e feedback sem nota.
6. Reabertura do histórico após recarregar a página; acionamento dos controles por teclado (Enter) e foco visível no botão de pista.

Capturas locais ignoradas pelo Git: `artifacts/qa/dynamic-intervention6/photo-feedback.jpg` e `history.jpg`. A demonstração não utilizou imagens identificáveis, PDF real ou OCR/LLM real.

## Validação

A consolidação da Intervenção 5 passou por 51 testes Python e 610 JavaScript. Os dois casos antes chamados de deselecionados eram skips por ausência do pacote DEV local congelado: `test_real_smoke_dry_run_separates_semantic_hashes_from_transport` e `test_transport_builder_does_not_weaken_holdout_guard`, em `test_tme_model_compat.py`. Não são testes do percurso autônomo; cobrem plano de transporte entre modelos e proteção do holdout. O teste Lean anteriormente deselecionado é distinto e tem aprovação isolada documentada no relatório I5.

A Intervenção 6 possui testes para equações quadráticas, sistemas lineares, proporcionalidade, funções e geometria; incluem respostas corretas, parciais, incorretas, alternativa por completar quadrado e inconclusivas. Pareceres são simulados e identificados como tal. Não foram configurados verificadores por problema nem ajustadas notas-alvo.

A primeira execução ampliada registrou 701 aprovações e uma falha em `test_stale_invalidated_failed_and_new_audit_block_closure`. Os artefatos sintéticos foram preservados: auditoria P3 terminou `FAILED/AUDITOR_FAILED`, e o HTTP 409 subsequente impediu corretamente confirmar uma execução falha. O serviço histórico não preservou a exceção originária. Cinco repetições isoladas instrumentadas passaram; isso não demonstra a causa da ocorrência inicial. Nenhuma condição de aprovação foi relaxada e nenhum componente matemático TME² foi alterado para contornar o caso. A repetição ampliada passou pelo mesmo teste TME² e registrou 701 aprovações e duas falhas de compatibilidade HTTP em consultas de reconhecimento com metadados corrompidos. Essas falhas foram corrigidas preservando o status legado 422 nas consultas e 409 nas escritas; o isolamento de estudos privados permanece. A revalidação específica comprovou a correção dessas duas regressões.

O teste adicional de PDF identificou outra falha técnica do novo adaptador: `ArtifactReference` não admitia MIME PDF e limitava os nomes de originais a três imagens. A extensão é aditiva, incluindo PDF e nomes de originais multipágina. As restrições dos fluxos legados permanecem nos modelos de captura. Foram acrescentados testes de PDF com duas páginas, quatro fotografias, trecho ilegível e preservação da tentativa/pacote após alteração do enunciado.

Não houve mudança incompatível de contrato nem migração de registros. Os contratos novos são próprios do estudo; os modelos compartilhados receberam variantes aditivas.

## Resultados finais e reprodução

| Conjunto | Resultado |
| --- | --- |
| Etapa 0 / I5: Python dirigido | 51 aprovados, 2 skips documentados |
| Etapa 0 / I5: JavaScript | 610 aprovados |
| I6: primeira regressão ampliada | 701 aprovados, 1 falha TME² não reproduzida posteriormente |
| I6: repetição ampliada instrumentada | 701 aprovados, 2 falhas HTTP depois corrigidas |
| I6: revalidação final de estudo, autenticação, submissões, transcrições, reconhecimento, prova/finalização TME² e preparação DYNAMIC | **290 aprovados, sem falhas, 88,29 s** |
| Contratos e apresentação da captura existente | **27 aprovados, sem falhas, 1,63 s** |
| JavaScript completo após as alterações | **613 aprovados, sem falhas, 2,92 s** |
| Teste TME² inicialmente falho, repetido isoladamente com instrumentação temporária | 5 aprovados, 19,99 s |
| `git diff --check` | Aprovado |

Os conjuntos se sobrepõem; os números não devem ser somados como testes distintos. A última revalidação inclui os 14 casos de estudo autônomo, as duas regressões HTTP corrigidas e o teste TME² que falhou originalmente. A suíte ampliada inteira não foi repetida novamente depois da última extensão de referências PDF; foram repetidos os contratos e consumidores afetados. Não se declara uma execução ampliada integral sem falhas que não tenha ocorrido.

Interpretador validado: `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python` (Python 3.9.6). Executar na raiz do worktree DYNAMIC:

```sh
env -u OPENAI_API_KEY CONFIA_DYNAMIC_LLM_ENABLED=0 CONFIA_SEMANTIC_LLM_ENABLED=0 PYTHONPATH=app PYTHONDONTWRITEBYTECODE=1 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/test_dynamic_self_study.py tests/test_core_auth.py tests/test_submissions.py tests/test_transcriptions.py tests/test_recognition*.py tests/test_tme_full_exam.py tests/test_tme_finalization.py tests/test_dynamic_dy2.py
env -u OPENAI_API_KEY CONFIA_DYNAMIC_LLM_ENABLED=0 CONFIA_SEMANTIC_LLM_ENABLED=0 PYTHONPATH=app PYTHONDONTWRITEBYTECODE=1 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/test_capture_contracts.py tests/test_capture_static.py
node --test tests/js/*.cjs
git diff --check
```

Logs e capturas estão em `artifacts/qa/dynamic-intervention6/`, ignorado pelo Git. O servidor temporário de demonstração foi encerrado. A aplicação real não recebeu providers simulados nem alteração de credenciais. Para uso real, os providers continuam sujeitos à configuração explícita já existente; nenhuma chamada paga foi realizada.

A inspeção dos arquivos novos/alterados não identificou credenciais reais ou dados de estudantes. `CONFIA_MATHPIX_APP_KEY=test` aparece somente no provider simulado do teste. O índice Git permanece vazio: 12 arquivos rastreados modificados e 9 arquivos novos (incluindo este relatório), todos da I6, aguardam revisão. HEAD e remoto permanecem no commit I5 indicado acima.

## Limitações e próxima validação

- O percurso experimental está integrado com mocks. Qualidade matemática, OCR real, rubricas provisórias, explicações, custo, latência e estabilidade sob carga ainda exigem avaliação independente.
- Critérios autogerados podem estar errados ou incompletos. A confirmação da interpretação pelo aluno não substitui validação matemática. Detectar ambiguidades depende também do que o provider declara.
- A projeção inicial é deliberadamente conservadora e usa mensagens gerais. Orientações contextualizadas dependem do provider; validação de citações não prova que a explicação é correta ou adequada à idade. Uma mensagem pode antecipar resposta apesar do prompt; avaliar esse risco antes de disponibilizar amplamente a estudantes.
- O caderno digital existente foi preservado. Seus traços não são ligados diretamente à tentativa autônoma; esta etapa oferece texto, imagens e PDF pela infraestrutura compartilhada.
- Uma tentativa trata um problema. Não há segmentação automática de múltiplos problemas numa fotografia; o estudante deve conferir o enunciado e a resolução correspondentes.
- Avaliação e preparação são síncronas; falhas são explícitas e preservam originais. Uma tentativa analisada com erro técnico permanece no histórico; nova tentativa é o caminho de repetição. Não foi criado sistema de filas ou retomada automática.
- Comparações não cruzam rubricas diferentes; isso evita inferir evolução a partir de critérios alterados.
- Armazenamento padrão: `runtime/self_study`, configurável por `CONFIA_SELF_STUDY_DIR`, além do repositório de submissões já existente. Não publicar dados desse diretório, imagens, logs ou transcrições.

Próxima etapa recomendada: revisão desta intervenção; depois, protocolo controlado com problemas e resoluções independentes da Educação Básica, gold inacessível ao corretor, avaliação humana por critério e da adequação pedagógica das pistas. Separar fidelidade da transcrição, qualidade da rubrica e correção do parecer. Medir erros/abstenções, exposição precoce de respostas, compreensão do aluno, custo e latência. Autorizar explicitamente o uso de providers reais apenas nessa etapa posterior. Não considerar este trabalho validação para atribuição oficial de notas.
