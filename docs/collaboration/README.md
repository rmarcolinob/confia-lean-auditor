# Guia para Rian, Luis e colaboradores

A política vigente está em [CONTRIBUTING.md](../../CONTRIBUTING.md): `main` integrada, branches de trabalho e PRs revisados. O [relatório de consolidação](../audits/CONFIA_MAIN_CONSOLIDATION_2026_12.md) registra a transição; números de validações anteriores abaixo permanecem históricos.

## Código e responsabilidades

| Local | Responsabilidade |
| --- | --- |
| `app/confia_lean_auditor/main.py` | Aplicação FastAPI e composição das rotas |
| `app/confia_lean_auditor/submission_audits/` | AuditService, execução, persistência de AuditRuns e acesso autorizado |
| `app/confia_lean_auditor/tme/` | Integração TME², fluxo de prova e projeção diagnóstica de revisão |
| `app/confia_lean_auditor/semantic_policy/` | Avaliação semântica e fallback mínimo compartilhado |
| `app/confia_lean_auditor/rubric/pauta.py` | PautaEngine: regras compostas e pontuação preparada |
| `app/confia_lean_auditor/dynamic/` | Problemas/rubricas versionados, preparação, Grader, Reviewer, Reconciliation e decisões docentes |
| `app/confia_lean_auditor/static/` | Frontend e componentes compartilhados; `tme/` contém a referência visual |
| `ConfiaLeanAuditor/`, `lean-toolchain`, `lake-manifest.json` | Formalizações e dependências Lean fixadas |
| `tests/`, `tests/js/` | Regressões Python e JavaScript; fixtures não estimam acurácia populacional |
| `docs/audits/`, `scripts/evaluation/` | Evidências históricas, protocolos e verificadores |

SPECIALIZED atende muitas soluções de poucas questões preparadas. Checkers e Lean produzem evidências quando possível; Semantic B com fallback mínimo avalia critérios elegíveis inconclusivos usando texto e pauta. O provider decide atendimento e apresenta citações; os pontos continuam definidos pelo mecanismo de pontuação. A projeção `tme-review-diagnostics.v1` é derivada e não reescreve pontuação, `needs_review`, `verdict` ou AuditRuns antigos.

DYNAMIC atende questões inéditas sem exigir microclaims, checker individual ou Lean preparado por nossa equipe. Há entrada manual de rubrica e geração opcional, aprovação docente, publicação da atividade e correção pelo fluxo compartilhado. Isso é implementação funcional de piloto, não validação geral da matemática. O plano específico está em `docs/collaboration/DYNAMIC_STATUS.md` neste repositório.

## Onde começar por frente

- **Rian — serviços, APIs e interface:** [estado do DYNAMIC](DYNAMIC_STATUS.md), `dynamic/{router,school_router,study_router}.py`, `dynamic/{assessment_service,school_service,study_service}.py` e `static/{dynamic-assessment,dynamic-student,dynamic-self-study}.js`. Consulte `/docs` no servidor local para os schemas efetivos. A [I5](../audits/CONFIA_DYNAMIC_INTERVENCAO_5_ALUNO.md) documenta publicação, tentativas e divulgação docente; a [I6](../audits/CONFIA_DYNAMIC_INTERVENCAO_6_ESTUDO_AUTONOMO.md) documenta o fluxo autônomo, atualizado pela [6B](../audits/CONFIA_DYNAMIC_INTERVENCAO_6B_FEEDBACK.md).
- **Luis — reconhecimento, transcrição e captura:** [contrato de captura](../integration/CAPTURE_TO_CONFIA_CONTRACT.md), [transcrições versionadas](../P2_CAP_03A_TRANSCRIPTION.md), [contratos e limites de reconhecimento](../../app/confia_lean_auditor/recognition/README.md), `recognition/{schemas,service,registry,mathpix_image}.py`, `submissions/{schemas,store}.py`, `tme/exam_capture.py` e `dynamic/study_capture.py`. A variante `self-study-source.v1` está em `dynamic/study_models.py`. Originais e hashes permanecem separados da leitura; OCR automático nunca constitui conferência humana. Confirmações do aluno e do professor têm contextos distintos.
- **Ambos:** as rotas próprias preservam autoria, versões e vínculos. Não usar endpoints genéricos para contornar os gateways de atividade/estudo, nem inferir aceitação humana de `ensureAcceptance()`. Os testes de integração relevantes são `test_dynamic_handwriting.py`, `test_dynamic_school.py`, `test_dynamic_self_study.py` e `test_dynamic_self_study_feedback_policy.py`.

Os documentos de cada intervenção são registros históricos. Para a política de divulgação vigente, prevalece `self-study-feedback.v2`, descrita na 6B; a revisão I6 registra os bloqueios anteriores e não deve ser lida como estado final.

## Ambiente local

Python mínimo declarado: 3.9. Ambiente observado da RC1: Python 3.9.6, macOS/arm64; versões dos pacotes em `docs/audits/assets/specialized-tme2-rc1/python-environment.txt`. O `pip install -e .` do README instala uma configuração de desenvolvimento; **não garante reprodução estrita**. Para esta, siga o manifesto, instale as versões registradas e o projeto com `--no-deps`.

Lean: 4.28.0; Lake: 5.0.0-src+7e01a1b; Mathlib: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`. Provisionar o toolchain e as dependências dos manifests. Não executar `lake update` para reproduzir RC1. O cache `.lake` não acompanha o Git; falha de instalação não é refutação matemática. Node foi validado em v24.15.0. O frontend principal é estático, sem instalação do projeto de vídeo.

Com o gerenciador `elan` instalado, na raiz do clone, prepare as verificações formais do SPECIALIZED:

```sh
elan toolchain install leanprover/lean4:v4.28.0
lake exe cache get
lake build
git diff --exit-code -- lean-toolchain lakefile.toml lake-manifest.json
```

Esses comandos podem baixar dependências e consumir tempo de compilação; não chamam providers de correção. Preserve os manifests rastreados. O servidor pode iniciar antes desse provisionamento, mas isso não comprova disponibilidade das verificações Lean. A validação do clone nesta consolidação instalou o Python e iniciou o servidor; a regressão formal usou o cache local já provisionado, sem reconstrução integral da Mathlib nesse clone.

O piloto usa `runtime/pilot-dec10`; `--data-dir CAMINHO` permite isolamento adicional. O launcher é local, demonstrativo, sem autenticação institucional. Consultar os documentos de autenticação em `docs/` antes do provisionamento institucional; não publicar o launcher de demonstração na rede. Os controles existentes continuam no servidor.

Providers são opt-in. Preparação automática DYNAMIC: `CONFIA_DYNAMIC_LLM_ENABLED`, `CONFIA_DYNAMIC_MODEL` (padrão configurado `gpt-4.1`), `CONFIA_DYNAMIC_REASONING_EFFORT`. Avaliação semântica compartilhada: `CONFIA_SEMANTIC_LLM_ENABLED`, `CONFIA_SEMANTIC_MODEL` (padrão configurado `gpt-6.1-sol`), `CONFIA_SEMANTIC_REASONING_EFFORT` (padrão `medium`). Identificadores configurados não garantem disponibilidade nem imutabilidade remota. Fornecer credenciais por mecanismo externo, nunca pelo Git.

### DYNAMIC com sessão autenticada

Na raiz de um clone próprio da `main` integrada (ou da branch do PR durante a revisão), após instalar o ambiente do README, execute em um mesmo terminal:

```sh
export CONFIA_ENV=development CONFIA_AUTH_ENABLED=1 CONFIA_COOKIE_SECURE=0
export CONFIA_DYNAMIC_LLM_ENABLED=0 CONFIA_SEMANTIC_LLM_ENABLED=0
export CONFIA_TME_DEMO_NO_AUTH=0 CONFIA_DYNAMIC_DEMO_ENABLED=0
export CONFIA_LEAN_AUDITOR_ROOT="$PWD"
unset OPENAI_API_KEY CONFIA_MATHPIX_APP_ID CONFIA_MATHPIX_APP_KEY
for store_name in AUTH INSTITUTIONAL ASSESSMENTS ASSESSMENT_PARTICIPANTS TME_EXAMS TME_CASES SUBMISSIONS SUBMISSION_AUDITS DYNAMIC TEACHER_DECISIONS SELF_STUDY; do
  export "CONFIA_${store_name}_DIR=$PWD/runtime/collaboration/${store_name}"
done
.venv/bin/python scripts/create_demo_users.py
.venv/bin/python scripts/create_demo_institutional_data.py
.venv/bin/python -m uvicorn confia_lean_auditor.main:app --app-dir app --host 127.0.0.1 --port 8000
```

Os scripts criam somente identidades e vínculos sintéticos locais; solicitam senhas sem eco e preservam contas existentes. Não há senha padrão a distribuir. Não execute o seed sobre armazenamento institucional. Use `http://127.0.0.1:8000/`, `/#teacher/home`, `/#student/exams` e `/#student/study`, com a conta do papel correspondente. Os arquivos de `runtime/` não entram no Git. `CONFIA_COOKIE_SECURE=0` é exclusivo de HTTP em localhost; ver [autenticação](../CORE_AUTH_01.md) e [vínculos institucionais](../CORE_INST_01.md).

Esse comando não habilita OCR/LLM reais. Preparação e análise que exigem inferência permanecerão indisponíveis/pendentes; os testes abaixo usam providers simulados. O percurso com mocks é evidência de integração, não um serviço de inferência embutido no servidor normal. Habilitar providers reais requer configuração e autorização próprias.

## Testes offline

Na raiz da branch, usando o Python do ambiente preparado:

```sh
env -u OPENAI_API_KEY CONFIA_SEMANTIC_LLM_ENABLED=0 CONFIA_DYNAMIC_LLM_ENABLED=0 \
  PYTHONPATH=app python -m pytest -q tests/test_dec10_integration.py tests/test_dynamic_r1.py \
  tests/test_tme_review_diagnostics.py tests/test_core_auth.py tests/test_tme_demo_auth.py
node --test tests/js/test_platform_navigation.cjs tests/js/test_teacher_presentation.cjs \
  tests/js/test_platform_presentation.cjs tests/js/test_ui_02_workspace.cjs tests/js/test_auth_login.cjs
```

Rodada de organização: **152 testes Python e 45 JavaScript aprovados**. O verificador da RC1 passou novamente (754 arquivos, 65 membros de referência, ambiente conferido). Isso complementa os registros anteriores de 971 testes principais, 55 dirigidos e um teste Lean isolado; não representa nova execução desses conjuntos completos. Testes de registros locais podem ser pulados em outro checkout sem o runtime original; o bundle permite conferir os bytes históricos separadamente.

## Primeiras tarefas

Para a consolidação I6+6B, consulte os comandos e resultados atuais no [relatório](../audits/CONFIA_DYNAMIC_INTERVENCOES_6_6B_CONSOLIDACAO.md). Os números da rodada de organização acima são históricos. Os testes específicos dos feedbacks são `tests/test_dynamic_self_study_feedback_policy.py` e `tests/js/test_dynamic_self_study.cjs`; a suíte ampliada inclui os contratos TME². Permanecem dois skips por pacote DEV controlado ausente e uma ocorrência P3 intermitente sem causa identificada, preservados no relatório.

Rian pode clonar o remoto, ler este guia e os três históricos de interface (`a5d2461`, `1545955`, `8c17274`), executar a regressão offline e abrir uma branch a partir da `main` integrada. O código atual das duas frentes já tem ancestralidade comum na RC1; as novas branches separam **trabalho futuro**, não apagam o histórico compartilhado.

Prioridades DYNAMIC: avaliação independente por domínio e critério; comportamento fora do parser exato; qualidade de rubricas e citações; divergências e revisão humana; custo/latência; integração de captura sem confundir OCR e correção matemática. Prioridades de interface: revisão desktop/mobile e acessibilidade, preservando caderno, TutorIA, dados reais de gestão e permissões. Não há nova implementação dessas tarefas nesta organização.
