# ConfIA DYNAMIC — consolidação I6 e 6B

Data: 26/11/2026. Branch exclusiva: `codex/dynamic-development`. Base anterior: `d40a7b08ff5eef60b012f382e64fa82a604c05fc` (I5). Escopo: revisão e publicação do código existente, regressões e atualização documental; nenhuma funcionalidade nova, modificação matemática ou chamada paga.

## Decisão de organização

Os 24 arquivos pendentes foram atribuídos à I6, sua revisão e à 6B: 21 arquivos de código/testes e três relatórios históricos. A 6B modifica arquivos introduzidos pela I6. O código final é registrado conjuntamente em `feat(dynamic): consolidate I6 and I6B self-study with restricted feedback`; não se reconstrói um commit intermediário com vazamento conhecido. A documentação de colaboração e este relatório ficam em `docs(dynamic): document I6 I6B consolidation and experimental readiness`. Os relatórios originais da [I6](CONFIA_DYNAMIC_INTERVENCAO_6_ESTUDO_AUTONOMO.md), [revisão](CONFIA_DYNAMIC_INTERVENCAO_6_REVISAO.md) e [6B](CONFIA_DYNAMIC_INTERVENCAO_6B_FEEDBACK.md) permanecem literais e descrevem o estado de suas respectivas etapas, inclusive quando registram que ainda não havia publicação.

Commit do código I6+6B: `a8692e54e3ccda8435bb7fb3aa40687f8df27503`.

Os hashes definitivos dos commits são consultáveis pelo histórico e pelo relatório final da operação; o documento não contém o próprio hash autorreferente. Identificação posterior:

```sh
git log -2 --format='%H %s' codex/dynamic-development
git ls-remote origin refs/heads/codex/dynamic-development
```

## Revisão do conjunto

| Requisito | Evidência no código e nos testes | Resultado |
| --- | --- | --- |
| Sem nota no estudo autônomo | `study_service.view`, `study_feedback.public_report`, IDs opacos e rótulos locais; `no_grades` recursivo e testes R1/R2 | API, interface e histórico próprios não expõem pontuação interna; não há exportação SELF_STUDY. Futuras exportações precisam usar a mesma projeção. |
| Níveis de ajuda | `ControlledHelpProposal`, `validate_help`, `render_help`, `public_help`; testes de prosa indevida, citações, níveis e consentimento | Níveis 2–3 não aceitam texto livre/etapas do provider. Nível 4 exige solicitação e estado suficiente. Falha gera orientação segura, sem novo julgamento. |
| Parcialidade e erro | `study_feedback.project`, achado separado de atendimento; testes R3 nos dois sentidos de discordância | Crédito parcial interno preservado; erro apoiado por evidências continua explícito. Discordância fica pendente, sem transformar incompletude em erro. |
| Núcleo matemático | `study_service.evaluate` chama Grader, revisão independente, comparação e reconciliação existentes | Nenhum diff em Grader, Reviewer, Reconciliation, política semântica, PautaEngine, pautas, checkers ou Lean. |
| Isolamento e autorização | `study_service.session/folder/history`, guards de fontes privadas, rotas com sessão e CSRF existente | Outro aluno e papéis docentes não acessam estudo privado. Modo demo legado não abre esses registros. |
| Versões e rastreabilidade | Hashes do pacote/leitura, autoria da confirmação, registros selados e tentativas imutáveis | Nova leitura exige nova confirmação; tentativa analisada é preservada. Histórico reprojetado sem reescrita dos artefatos. |
| Três contextos | `test_dynamic_school.py` e regressões de reconciliação por perfil | Lista formativa, prova com divulgação docente e SELF_STUDY continuam distintos, compartilhando o núcleo. |
| Contratos TME² | Captura, transcrição, finalização, auditoria de questão, confirmação humana e compatibilidade de modelos | Incluídos na regressão ampliada; cobertura ausente explicitada abaixo. |

Não se promete que um modelo real sempre escolherá o conceito pedagógico pertinente. As expressões do nível 4 passam por restrição lexical, não por verificação matemática. Evidência literal da fonte mantém números e frações; não se apagam números matemáticos para esconder notas. Os pareceres e pontos internos continuam privados, inclusive conteúdo rejeitado disponível na proveniência.

## Testes desta consolidação

| Verificação | Resultado nesta consolidação |
| --- | --- |
| Python ampliado, três contextos, autorização/isolamento, captura e contratos TME² | **769 aprovados, 2 skips em 375,89 s** |
| JavaScript completo | **614 aprovados, zero falhas/skips em 2,59 s** |
| `git diff --check` | Aprovado |
| Links locais e caminhos de serviços/testes da documentação atualizada | Conferidos |
| Revisão dos 28 arquivos e scan de padrões de tokens/chaves privadas | Nenhuma correspondência de segredo; fontes, testes sintéticos e Markdown |

A ocorrência anterior da P3 não se repetiu nesta rodada; sua causa continua indeterminada. Logs desta consolidação: `artifacts/qa/dynamic-intervention6-consolidation/{python,javascript}.log`, ignorados pelo Git. Os 24 arquivos da I6+6B são preservados como revisados; quatro documentos foram acrescentados/atualizados para a consolidação.

Comandos executados na raiz do worktree, com o Python 3.9.6 já validado em `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python` (use o equivalente do seu ambiente):

```sh
env -u OPENAI_API_KEY CONFIA_DYNAMIC_LLM_ENABLED=0 CONFIA_SEMANTIC_LLM_ENABLED=0 PYTHONPATH=app PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -rs --tb=short -p no:cacheprovider tests/test_dynamic*.py tests/test_submissions.py tests/test_transcriptions.py tests/test_recognition*.py tests/test_core_auth.py tests/test_core_institutional.py tests/test_assessments.py tests/test_capture_contracts.py tests/test_capture_static.py tests/test_tme_full_exam.py tests/test_tme_finalization.py tests/test_tme_question_audit.py tests/test_tme_human_confirmation.py tests/test_tme_model_compat.py
node --test tests/js/*.cjs
git diff --check
```

São testes com providers simulados e dados sintéticos, não novas auditorias reais. Os 30 casos permanentes da política pública estão incluídos na suíte Python, sem dupla contagem. A evidência de navegador/teclado e histórico é a execução da 6B, documentada no relatório correspondente; não houve alteração de interface nesta consolidação nem nova demonstração visual.

Os dois skips em `tests/test_tme_model_compat.py` são:

- `test_real_smoke_dry_run_separates_semantic_hashes_from_transport`.
- `test_transport_builder_does_not_weaken_holdout_guard`.

Motivo: `Frozen local DEV pack unavailable`. Não são deseleções nem falhas do estudo autônomo. Limitam a comprovação do plano sobre o pacote DEV controlado e sua proteção de holdout nesse checkout. Não se inventa um pacote substituto. O teste Lean isolado aprovado em etapa anterior é distinto e não foi reexecutado nesta consolidação.

A falha intermitente P3 anterior continua aberta: `test_stale_invalidated_failed_and_new_audit_block_closure` encontrou `FAILED/AUDITOR_FAILED`, seguido de HTTP 409 que bloqueou corretamente a confirmação. A exceção originária não ficou registrada. Aprovações posteriores não demonstram sua causa. Evidência local histórica: `artifacts/qa/dynamic-intervention6/regression-initial.log`; descrição versionada nos relatórios I6/revisão. Não alterar testes ou matemática para ocultar essa ocorrência.

## Conteúdo e publicação

Remoto verificado: `https://github.com/rmarcolinob/confia-lean-auditor.git`, público, com permissão de push confirmada. Antes da publicação, branch remota e HEAD local coincidiam na base I5. A publicação deve ser somente `HEAD:refs/heads/codex/dynamic-development`, sem force, tags ou integração automática.

O conjunto contém fontes, testes sintéticos e Markdown. Não inclui `.env`, credenciais, contas operacionais, imagens, manuscritos, transcrições de estudantes, runtime, logs privados ou bundles. Os artefatos locais da revisão permanecem ignorados; os testes permanentes e as conclusões necessárias estão no repositório. O scan de segredos é complementar à revisão manual, não prova universal de ausência. Como não existem commits locais adicionais à base remota, o histórico novo a enviar é exatamente o conjunto desses dois commits, a conferir novamente antes do push.

Referências a preservar localmente e no remoto:

- `main`: `8fde840d95fa4df0553b915d7b60301c9892aa65`.
- Objeto anotado `SPECIALIZED-TME2-RC1`: `0c64e318a26e21f71fe3097c66ee17a5206dd8a3`.
- Commit RC1: `c03403fe5b83d9db9df172882bd69af3dfa2d027`.

O snapshot e seu bundle externo não fazem parte desta intervenção. Não se criam pacotes de transferência ou branches novas. Os demais worktrees não são modificados.

## Documentação para colaboração

O [README principal](../../README.md) aponta para a branch DYNAMIC e distingue launcher demo de execução autenticada. O [guia de Rian e Luis](../collaboration/README.md) fornece caminhos de serviços, APIs, contratos de captura/reconhecimento/transcrição, instalação e execução local autenticada. O [estado DYNAMIC](../collaboration/DYNAMIC_STATUS.md) organiza os três contextos e as pendências. Esses documentos referenciam os contratos e auditorias existentes, sem duplicar suas especificações.

Rian pode começar pelos routers/serviços `assessment`, `school` e `study` e seus módulos JavaScript. Luis pode começar por `recognition/schemas.py`, `RecognitionService`, `SubmissionStore`, `tme/exam_capture.py` e `study_capture.py`, preservando originais, versões, autoria e confirmação explícita. O ambiente normal sem credenciais não oferece inferência simulada automaticamente: a simulação está nos testes. Nenhum colaborador precisa receber um pacote paralelo ao GitHub.

## Prontidão e pendências classificadas

| Categoria | Situação comprovada e pendência | Consequência |
| --- | --- | --- |
| Defeitos bloqueantes no núcleo/pedagogia | R1–R3 corrigidos com regressões permanentes. Nenhum outro bloqueio reproduzido nesta revisão. A ocorrência P3 tem causa indeterminada. | Pode consolidar o desenvolvimento; manter P3 aberta e capturar a exceção se reaparecer. Não apresentar ausência de defeitos reproduzidos como correção matemática garantida. |
| OCR e interface | Integração de fotos/PDF, leitura versionada e conferência simulada existe. OCR real de sinais, frações, expoentes, diagramas e várias páginas ainda exige avaliação. Notação/explicações do nível 4 e repertório 2–3 são limitados. | Piloto local supervisionado; conferência das leituras e avaliação pedagógica antes de uso com alunos. |
| Operação e infraestrutura | Execução síncrona, chamadas por critério, retomada por nova tentativa em falhas do estudo, armazenamento local e acesso autenticado de desenvolvimento. Não há benchmark representativo de custo, latência ou escala. Dois testes dependem de DEV controlado ausente. | Fixar ambiente/configuração e limites de custo/tempo, política de dados, backup e instrumentação segura. Exposição institucional demanda revisão operacional própria. |
| Validação científica | Não há gold independente representativo nem avaliação de aprendizagem/adequação por idade para os três contextos. Concordância dos agentes não é prova formal. | Separar qualidade de transcrição, rubrica, decisões por critério, erros/abstenções e feedback. Gold humano inacessível ao corretor. |

**Recomendação:** o código consolidado é base técnica para preparar `DYNAMIC-RC1` experimental destinada a testes supervisionados; não se declara a candidata congelada nesta tarefa. Antes de criar a tag, registrar manifesto próprio com commit, dependências, schemas/políticas/prompts/configurações e hashes; definir protocolo, amostra e orçamento; realizar smoke autorizado com OCR/LLM reais, documentando falhas e revisão humana. A avaliação científica permanece posterior e separada. Não está validado para correção autônoma de avaliações escolares.
