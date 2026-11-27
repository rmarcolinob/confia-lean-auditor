# Fase 1 — estabilidade de execução (27/11/2026)

Base: `923bf3acbd9994af9662bcdff6b18eac1b6d4df9`. Branch: `codex/stabilize-technical-pre10dez`.
Diagnóstico histórico preservado: [PR #6](https://github.com/rmarcolinob/confia-lean-auditor/pull/6).

**APROVADO COM LIMITAÇÕES na validação local.** Há um defeito técnico reproduzido e corrigido; a causa individual das ocorrências históricas não pode ser estabelecida retrospectivamente, pois suas exceções internas foram descartadas. Aprovação de integração depende também dos workflows do commit deste PR. Não houve merge.

## Reprodução e causa

O [Python CI da main](https://github.com/rmarcolinob/confia-lean-auditor/actions/runs/46015125270), job `140560173779`, registrou `test_digital_photo_equal_accepted_math[4]`: `AUDITOR_FAILED`, 3596 aprovados, 52 skips e 1 xfail. O teste usa transcrições aceitas sintéticas, com Lean e providers desativados. Não executa OCR.

Vinte processos locais com `PYTHONHASHSEED=1..20` passaram no teste original. Isso não resolve nem explica a intermitência histórica.

Uma pausa controlada de 100 ms durante a reextração de uma evidência P4 reproduziu a exceção `ValueError: Literal source projection is inconsistent` em `student_claims/digital_items.py`, seguida de `FAILED/AUDITOR_FAILED` no serviço. O parser limitava a análise a 50 ms de **tempo decorrido**, incluindo pausas do escalonador. A reconstrução obrigatória da mesma fonte podia, portanto, produzir registros diferentes sem qualquer alteração de texto, cânone ou atribuição. O mesmo mecanismo foi reproduzido para P3.

As regressões permanentes simulam avanço do relógio de parede durante reextrações reais; não simulam a resposta matemática. Contra o parser original: **6 falhas e 1 aprovado**. Depois: **7 aprovados**. Separadamente, a reprodução com pausa real foi registrada localmente; não depende de dados pessoais ou providers.

O mecanismo demonstrado é compatível com as falhas históricas P3/P4, mas não prova que ambas tiveram essa causa. O registro anterior da P3 permanece aberto quanto à atribuição causal histórica.

## Alteração mínima

- `core/math_canonical/parser.py`: orçamento passa a usar `time.thread_time()`. Mantidos os 50 ms de CPU, limites de tamanho, profundidade, nós, coeficientes e expoentes, gramática e resultados matemáticos. Não se inclui CPU de outras requisições. Não há espera/I/O dentro desse parser; limites estruturais continuam indispensáveis.
- `submission_audits/service.py`: registra somente etapa, classe da exceção e localização relativa no código. Não registra mensagem, traceback textual, variáveis locais, conteúdo do aluno ou caminho absoluto. `FAILED`, `AUDITOR_FAILED`, resultado ausente e idempotência permanecem iguais. AuditRuns antigos não são reescritos e nenhum campo de contrato foi acrescentado.
- `tests/test_digital_extraction_stability.py`: P3/P4, reextração sob pausa, execução/consulta/retry imutável, expiração inicial sem fato matemático suportado, orçamento real de CPU e exclusão de tempo de desescalonamento.
- `tests/test_submission_audits.py`: diagnóstico das etapas de engine, manifesto, integridade e hash; falha técnica não vira zero; mensagens privadas permanecem fora dos logs e do registro.
- `tests/test_math_canonical.py`: o teste existente de esgotamento injeta o relógio de CPU utilizado pelo orçamento; conserva a asserção de rejeição.

As reconstruções e verificações de origem foram mantidas, inclusive as proteções contra adulteração. Nenhum checker, pauta, política, formalização Lean, PautaEngine ou pontuação esperada foi modificado.

## Validação local

Ambiente: Python 3.9.6 do `.venv` validado do projeto; constraints versionadas. CI usa Python 3.11, a ser conferido no PR. Lean 4.28.0; cache local copiado para o worktree isolado, sem compartilhar diretório de build mutável.

| Verificação | Resultado |
|---|---|
| Novas regressões contra o parser original | 6 falhas, 1 aprovado |
| Dirigidos novos + P1–P5 digital/transcrição + ocorrência P3 | 13 aprovados |
| Diagnósticos de falha e integridade | 11 aprovados |
| Bateria ampliada Python | **905 aprovados, 6 skips**, 304,28 s |
| JavaScript completo | **631 aprovados**, nenhum skip/falha |
| `lake build` | Aprovado, 8038 jobs |
| Certificados Lean na integração aceita | Incluídos e aprovados na bateria Python: prova de `4!=24`, refutação de `2^4=8`, detecção de certificado alterado |
| Replay portátil P1 e diagnósticos | Incluídos: P1 continua **17/20**, respostas arquivadas; sem nova auditoria real |
| `git diff --check` | Aprovado |

Os seis skips preexistentes: cinco AuditRuns locais do piloto P1–P5 ausentes neste worktree e um artefato histórico local de canonização ausente. Não foram criados skips, xfails nem reduzidas as asserções para acomodar a correção. A matriz preparada de P1–P5 continua testando soluções completas, parciais, incorretas e alternativas; isso não equivale a gold humano independente.

Comandos (na raiz do worktree, Python do ambiente validado):

```sh
python -m pytest -q tests/test_math_canonical.py tests/test_digital_extraction_stability.py tests/test_submission_audits.py tests/test_tme_accepted_integration.py tests/test_tme_finalization.py tests/test_tme_review_diagnostics.py tests/test_core_auth.py tests/test_cap04_integrity_regressions.py tests/test_tme2_p1_pauta_bridge.py tests/test_tme2_p2_pauta_bridge.py tests/test_tme2_p3_pauta_bridge.py tests/test_tme2_p4_pauta_bridge.py tests/test_tme2_p5_pauta_bridge.py tests/test_pauta_engine.py
node --test tests/js/*.cjs
lake build
git diff --check
```

## Limites e impacto

O canonizador é compartilhado por SPECIALIZED e DYNAMIC; o ajuste afeta contabilização de recursos, não a matemática. A instrumentação cobre erros de ambos os motores. Falhas genuínas continuam pendentes/falhas, nunca viram notas zero. Não se afirma ausência universal de intermitências; os novos logs permitirão identificar exceções futuras sem expor soluções.

Não foram executados providers reais, OCR ou avaliações humanas independentes. Os **21 casos históricos do gate sem validação independente permanecem pendentes**. Nenhuma capacidade semântica foi validada por esses testes determinísticos. A tag `SPECIALIZED-TME2-RC1` continua apontando para `c03403fe5b83d9db9df172882bd69af3dfa2d027`; a main e as evidências do PR #6 foram preservadas.
