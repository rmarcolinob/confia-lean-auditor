# Guia para Rian e colaboradores

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

DYNAMIC atende questões inéditas sem exigir microclaims, checker individual ou Lean preparado por nossa equipe. Há entrada manual de rubrica e geração opcional, aprovação docente, publicação da atividade e correção pelo fluxo compartilhado. Isso é implementação funcional de piloto, não validação geral da matemática. O plano específico está em `docs/collaboration/DYNAMIC_STATUS.md` na branch `codex/dynamic-development`.

## Ambiente local

Python mínimo declarado: 3.9. Ambiente observado da RC1: Python 3.9.6, macOS/arm64; versões dos pacotes em `docs/audits/assets/specialized-tme2-rc1/python-environment.txt`. O `pip install -e .` do README instala uma configuração de desenvolvimento; **não garante reprodução estrita**. Para esta, siga o manifesto, instale as versões registradas e o projeto com `--no-deps`.

Lean: 4.28.0; Lake: 5.0.0-src+7e01a1b; Mathlib: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`. Provisionar o toolchain e as dependências dos manifests. Não executar `lake update` para reproduzir RC1. O cache `.lake` não acompanha o Git; falha de instalação não é refutação matemática. Node foi validado em v24.15.0. O frontend principal é estático, sem instalação do projeto de vídeo.

O piloto usa `runtime/pilot-dec10`; `--data-dir CAMINHO` permite isolamento adicional. O launcher é local, demonstrativo, sem autenticação institucional. Consultar os documentos de autenticação em `docs/` antes do provisionamento institucional; não publicar o launcher de demonstração na rede. Os controles existentes continuam no servidor.

Providers são opt-in. Preparação automática DYNAMIC: `CONFIA_DYNAMIC_LLM_ENABLED`, `CONFIA_DYNAMIC_MODEL` (padrão configurado `gpt-4.1`), `CONFIA_DYNAMIC_REASONING_EFFORT`. Avaliação semântica compartilhada: `CONFIA_SEMANTIC_LLM_ENABLED`, `CONFIA_SEMANTIC_MODEL` (padrão configurado `gpt-6.1-sol`), `CONFIA_SEMANTIC_REASONING_EFFORT` (padrão `medium`). Identificadores configurados não garantem disponibilidade nem imutabilidade remota. Fornecer credenciais por mecanismo externo, nunca pelo Git.

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

Rian pode clonar o remoto, ler este guia e os três históricos de interface (`a5d2461`, `1545955`, `8c17274`), executar a regressão offline e abrir uma branch da frente escolhida. O código atual das duas frentes já tem ancestralidade comum na RC1; as novas branches separam **trabalho futuro**, não apagam o histórico compartilhado.

Prioridades DYNAMIC: avaliação independente por domínio e critério; comportamento fora do parser exato; qualidade de rubricas e citações; divergências e revisão humana; custo/latência; integração de captura sem confundir OCR e correção matemática. Prioridades de interface: revisão desktop/mobile e acessibilidade, preservando caderno, TutorIA, dados reais de gestão e permissões. Não há nova implementação dessas tarefas nesta organização.
