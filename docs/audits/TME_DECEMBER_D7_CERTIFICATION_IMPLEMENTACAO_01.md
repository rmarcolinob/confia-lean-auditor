# D7 — certificação e avaliação paralela

## 1. SHA inicial

Worktree: `~/Documents/confia-lean-auditor-tme-december-integration`.
Branch: `feat/tme-december-integration`.
SHA inicial: `5de838563ab3ae21c04c675b7edbd446ff844a79`, D6 commitado, worktree inicialmente limpo.
Implementação e validação em 11/11/2026. Sem `git add` e sem commit.

## 2. Event model

`certification-event.v1` consolida IDs existentes de D2–D6 e observações derivadas dos artefatos D1/D3. Campos: `event_id`, `event_type`, `timestamp`, `timestamp_basis`, assessment, participant pseudônimo, submission, question attempt, transcription version, audit run, human decision, final correction, engine mode/version, problem, rubric item, checker type/status, correlation ID, aliases e payload permitido. Campos não aplicáveis ficam nulos.

| Etapa | Observação exportada | Fonte |
| --- | --- | --- |
| Captura | capture_received, page_created | Manifest imutável e timestamp da captura |
| Associação | page_question_associated / disassociated | Diferença entre versões persistidas do mapeamento |
| Transcrição | transcription_created, transcription_human_corrected, transcription_activated | Revisões imutáveis; IDs preservados |
| Auditoria | audit_started / completed / failed, reanalysis e score_changed | Eventos D3/D4 persistidos |
| Claims | claim_extracted, claim_mapped | Records/facts persistidos pelo auditor |
| Pauta | obligation_mapped, rubric_item_decided | Obligations e decisões persistidas |
| Checker | checker_completed / failed | Mesmo ID de checker_result_recorded; tipo original em source_event_type |
| Award | alias award_decided | Mesma observação de rubric_item_decided, sem segundo evento |
| Score | suggested_score_created | Score disponível e hash do resultado |
| Humano | suggestion_accepted, score_adjusted, question_confirmed, question_reopened, invalidações | Ledger HumanDecision |
| Finalização | correction_finalized, correction_reopened e demais transições D6 | Ledger de fechamento |

Deduplicação por event_id; conteúdo conflitante causa 409. Não gravamos eventos em GET. Observações de claims/obligations/score usam tempo do registro de auditoria, não tempos medidos de execução. `checker_started` e `claim_rejected` estão explicitamente indisponíveis em `event_coverage`: não há timestamps individuais de início nem candidatos rejeitados persistidos. Claim refutado pelo checker não é uma rejeição de extração. Essa limitação é exposta, sem inventar eventos.

## 3. Certification records

Modelo `certification-record.v1`, uma projeção sem substituir os dados originais. Inclui IDs de assessment, participant, submissão da prova e submissão fonte, item/questão/tentativa, leitura, auditoria, decisão humana, fechamento e gold; scores separados; ajuste; erros assinado/absoluto; máximos; flags de review/technical; contagens por status de checker; decisões de rubric de primeiro nível; timestamps e hashes.

`selection=finalized` é o padrão: somente fechamentos atualmente vigentes, com o AuditRun/HumanDecision congelado por questão. Fechamentos anteriores permanecem no histórico, sem duplicar observações na comparação. `selection=current` usa o último run da leitura atual por modo de motor; sem run atual, score é nulo. Uma decisão humana só acompanha o run exato que homologou. O gold associa assessment + participant pseudônimo + assessment_item_id; novas tentativas desse mesmo vínculo compartilham o gold. A unidade de análise é registro/tentativa, não pessoa independente.

## 4. HumanGold

HumanGold externo é separado de HumanDecision e de `gold_rows` legado de D6. Importá-lo não altera AuditRun, transcrição, HumanDecision, FinalCorrection, nota oficial ou definição da avaliação. `source_id`/`dataset_version` são referências opacas; não certificam por si a origem oficial de um arquivo.

Histórico append-only em `CONFIA_TME_EXAMS_DIR/.certification/{assessment_id}/gold_000001.json`, etc. Cada versão é um snapshot completo, selado por hash, com previous_sha256, request_sha256, records_sha256, imported_at e imported_by interno. O export remove o identificador do importador. Repetição exata da requisição é idempotente; reutilização da versão de dataset com conteúdo diferente ou expected_version obsoleto gera 409. Teste concorrente confirma apenas um vencedor.

## 5. Import

Habilitar `CONFIA_TME_CERTIFICATION_ENABLED=1` no ambiente desejado. CSV UTF-8 (BOM aceito), exatamente cinco colunas:

```csv
assessment_id,participant_code,question_id,gold_score,max_score
asmt_1aa1e2e33e614db69856412dc6c93efa,D6-REAL-ENGINE,TME2026P1,20,20
```

POST com `Content-Type: text/csv`; query `source_id`, `dataset_version`, `expected_version`. JSON usa envelope:

```json
{
  "source_id": "independent-reference",
  "dataset_version": "v1",
  "expected_version": 0,
  "rows": [{
    "assessment_id": "asmt_1aa1e2e33e614db69856412dc6c93efa",
    "participant_code": "D6-REAL-ENGINE",
    "question_id": "TME2026P1",
    "gold_score": "20",
    "max_score": "20",
    "rubric_gold": [],
    "scorer_reference": "reference-01"
  }]
}
```

Na UI, fonte/versão ficam em campos separados e o textarea JSON recebe apenas a lista `rows`. `rubric_gold` opcional contém `{rubric_item_id, gold_points, max_points}`. IDs/máximos precisam corresponder a rubric observado em auditoria persistida; não inferimos itens. CSV não aceita rubric; usar JSON para essa granularidade. Scorer reference é opaco e omitido dos exports.

Preferir `assessment_item_id` como question_id; problem_id só é aceito quando identifica um único item. Participant code deve resolver um único participante EXTERNAL_PSEUDONYM da avaliação. Duplicatas após normalização, desconhecidos, máximos incompatíveis, negativos, NaN, valores acima do máximo e campos extras são rejeitados antes da escrita. Limites: 2 MiB, 10.000 linhas e 100 itens de rubric por linha. Cada nova versão substitui integralmente o dataset ativo e preserva o anterior.

## 6. Export

CSV: uma linha por CertificationRecord, notas ConfIA/HumanDecision/HumanGold, erro absoluto/assinado, ajuste, flags, motor, leitura e todos os IDs/hashes de proveniência. Metadados de export, seleção e contagens repetidos por linha. Identificadores textuais iniciados por caracteres de fórmula recebem prefixo de escape para planilha; números negativos permanecem números.

JSON: manifest, records, eventos normalizados, cobertura/limitações, métricas, histórico de versões gold, histórico de auditorias, leituras e fechamentos. É um pacote analítico completo de certificação; não contém o texto integral de artefatos originais. O manifest JSON também existe para coortes vazias; CSV vazio contém somente cabeçalho.

Downloads reais: [CSV](assets/tme-december-d7/certification.csv), [JSON](assets/tme-december-d7/certification.json). Ambos são evidências locais com dados de demonstração, não publicação de dataset de estudantes.

## 7. Metrics

Cálculo no backend, usando Decimal (precisão padrão 28; frações periódicas são representadas com essa precisão). Três pares: ConfIA × HumanGold, ConfIA × HumanDecision, HumanDecision × HumanGold. Cada par usa apenas scores não nulos e informa seu próprio N. Ausência de gold gera N=0 e taxas/MAE/bias nulos, nunca zero fictício.

Erro assinado = predição − referência. Exact = igualdade de score; MAE = média de |erro|; bias = média do erro. Within 1/2 usam pontos absolutos da escala original. Under/over e casos zero/positivo são contagens. Não há normalização automática de escalas. Os nomes zero_when_gold_positive/positive_when_gold_zero são mantidos no contrato de comparação; nos pares contra HumanDecision, a referência é aquela decisão.

Rubric: presença de award >0, somente pares de primeiro nível explicitamente fornecidos no gold, com máximo igual. Calculamos TP/FP/FN, precision, recall, false positive awards e missed awards. Item ausente no gold não vira rótulo negativo. Sem labels independentes por obligation, precision/recall de obligations ficam nulos com motivo explícito.

Etapas: transcrições corrigidas / questões com leitura; auditorias completed/all, failed, review/completed e technical/all; ajustes não zero / decisões homologadas, magnitude absoluta média e direção; questões reanalisadas; mudanças de score entre auditorias consecutivas do mesmo modo em versões distintas, quando a nova leitura é revisão humana. N de pares é explícito. Retries na mesma leitura não contam como mudança após correção. Histórico de auditorias é limitado à coorte selecionada; staleness posterior não aumenta retrospectivamente a taxa de review do run original.

`by_engine_mode` mantém comparações separadas. O agregado usa todas as linhas; não é uma estimativa de amostras independentes nem teste de significância. Eventos permitem localizar registros das etapas, mas não provar que uma etapa causou o erro. Nenhuma inferência causal.

## 8. Shadow mode

`SHADOW_EVALUATION`, `official_correction_affected=false` no manifest e aviso visível na UI. Configuração lateral selada por assessment é persistida na primeira importação, sem alterar o hash da definição D1. Antes de gold, a política é a mesma; GET não cria configuração ou dados. A flag de ambiente é opt-in e vem desabilitada por padrão.

## 9. Provenance

Percurso: assessment definition hash → exam submission → source submission → transcription version → AuditRun source/result hashes → HumanDecision → FinalCorrection → HumanGold record/version/hash. IDs permitem consultar as fontes originais com a autorização já existente. Métricas derivam apenas da projeção dessas fontes validadas; não de valores da UI.

Manifest contém git SHA, dirty flag, hash dos arquivos da aplicação (incluindo módulos ainda untracked), engine versions, gold selecionado, timestamp UTC, filtros, contagens e hashes dos records/eventos. Os exports desta implementação registram o SHA inicial + dirty=true; não representam um commit D7 inexistente. Histórico gold completo preserva versões anteriores; filtros podem fixar gold_version para reprodução.

## 10. Privacy

Export por allowlist. Sem nomes, CPF, e-mail, texto de resposta/transcrição, evidências textuais, motivos livres de ajuste, caminhos locais, metadados arbitrários ou identificadores dos avaliadores. Participant ID/code são os pseudônimos do modelo EXTERNAL_PSEUDONYM. Código pseudônimo e source_id devem ser preenchidos como códigos opacos: o sistema não consegue detectar se alguém usou indevidamente um identificador civil num campo de código. Não implementamos anonimização irreversível; os dados continuam vinculáveis por seus pseudônimos no sistema autorizado.

Verificação dos downloads: [export-verification.json](assets/tme-december-d7/export-verification.json). Guard de fórmula CSV e testes contra campos extras/e-mail na importação. Endpoints no-store e autorização do avaliador, com ownership de assessment.

## 11. API

Prefixo `/tme/assessments/{assessment_id}/certification`:

| Método/sufixo | Resultado |
| --- | --- |
| GET vazio | Summary, métricas e records por questão, eventos e manifest |
| GET /export.json | Mesmo pacote de certificação para download |
| GET /export.csv | Linhas por questão com proveniência |
| GET /gold | Dataset selecionado e histórico de metadados; `version` opcional |
| POST /gold | Importação CSV/JSON independente, versionada |

Consultas de certificação/export: `selection=finalized|current`, `engine_mode` opcional, `gold_version` opcional. Autorização `require_tme_evaluator`, ownership e flag em todas as rotas. Não há endpoint público de importação; o demo só funciona com o modo demo explicitamente configurado, conforme D1–D6. Respostas 404 (desabilitado/versão inexistente), 403 (owner), 409 (integridade/conflito), 413 (tamanho), 415 (tipo) e 422 (formato/dados). Lock order exam → submissions; gold também serializa versões no lock de exam.

## 12. UI

Botão Certificação no resumo de correção quando disponível. Reutiliza Page, queue, card, inputs e botões existentes, sem CSS/identidade visual nova. Mostra coorte da avaliação inteira, provas/questões/registros, disponibilidade e versão gold, N/MAE/exact, review/adjustment e os três pares. Estado explícito “Gold humano ainda não importado”. Filtros de seleção, versão e motor; links CSV/JSON preservam filtros. Importação por texto CSV/JSON e erro de concorrência sem apagar conteúdo.

Nenhum score é calculado no frontend; somente formatação das métricas. Motor vazio inclui todos. O produtor atual continua `TME_CURRENT`; o contrato D7 e agrupamentos aceitam strings como SPECIALIZED/DYNAMIC. Nenhum agente Dynamic foi implementado; habilitar futuros produtores exigirá seu próprio adaptador/schema de AuditRun, fora de D7.

## 13. Tests Python

D7 focado: **23 PASS em 13,97 s**. [Log](assets/tme-december-d7/python-focused.txt).

Cobertura dos 22 tópicos pedidos: CSV, JSON, duplicatas, bounds/NaN/máximo, unknown participant/question, versões e replay; records reais, exact/MAE/bias/within1/2/under/over/zero; adjustment e reanalysis real; CSV/JSON; provenance; pseudonym only; SHADOW; múltiplos modos; no gold. Adicionais: hash tampering, concorrência, access scope, payload size, filtros, rubric parcial e idempotência dos eventos. Os testes de integração usam auditorias reais do motor estável; os exemplos numéricos e modos futuros são fixtures apenas de contrato/métrica, sem motor simulado na demonstração.

## 14. Tests JS

Baseline D6 executado antes das alterações: **515 PASS / 0 FAIL**.
Suíte completa final: **519 PASS / 0 FAIL**, 2.084 ms. Quatro testes novos cobrem área opt-in/retorno, sem gold, gold disponível, métricas recebidas, filtros e links, CSV/JSON, conflito, ausência de campos de identidade civil e indicador SHADOW. [Baseline](assets/tme-december-d7/js-baseline.txt), [suíte final](assets/tme-december-d7/js-tests.txt).

## 15. Regressions

**886 PASS, 2 FAIL preexistentes, 1 SKIP em 286,13 s**, em 27 arquivos. Recorte D1–D7, assessments, submissions/transcriptions, recognition, TME, decisões, autenticação, submission_audits, Pauta e bridges estáveis. Nenhuma falha nova. O skip preexistente depende de artefato local V2. [Log completo](assets/tme-december-d7/python-regression.txt).

As duas falhas Lean foram reproduzidas em extração limpa do SHA inicial, sem código D7: **2 FAIL em 2,60 s**:

- `test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved`
- `test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`

Os artefatos dessa execução registram tentativa de clone Mathlib e `external command 'git' exited with code 128`; os checks retornam technical_error em vez dos resultados esperados. [Reprodução limpa](assets/tme-december-d7/lean-baseline.txt), [diagnóstico](assets/tme-december-d7/lean-diagnostic.txt). Sem alteração de matemática, PautaEngine, Lean/checkers, Semantic Formal, benchmarks ou P4/P5.

## 16. Browser validation

Servidor local 127.0.0.1:8765, cópia isolada do store da demonstração D6 em `/private/tmp/confia-d7-browser`. Prova pseudônima D6-REAL-ENGINE, avaliação asmt_1aa1e2e33e614db69856412dc6c93efa, três questões reais TME2026P1–P3, fechamento v2. Não usamos dados oficiais de estudantes.

1. Abrimos prova finalizada: ConfIA 55/60, HumanDecision 56/60.
2. Certificação sem gold: N=0, MAE/exact ausentes e aviso SHADOW.
3. Importamos pelo formulário [test-gold.csv](assets/tme-december-d7/test-gold.csv), fonte `synthetic-independent-demo`, dataset `d7-test-v1`. É gold sintético de teste, não correção oficial TME.
4. UI exibiu N=3, MAE=1,333, exact=33,3%, review=33,3%, adjustment=100%.
5. Baixamos CSV e JSON pelos links reais do navegador; conferimos arquivos, IDs, hashes, campos e separação dos scores.

| Questão | ConfIA | HumanDecision | Gold de teste | Erro ConfIA − gold |
| --- | ---: | ---: | ---: | ---: |
| P1 | 20 | 19 | 20 | 0 |
| P2 | 15 | 18 | 18 | −3 |
| P3 | 20 | 19 | 19 | +1 |

MAE ConfIA/gold=4/3; bias=−2/3; exact=1/3; within1=within2=2/3; under=1, over=1. HumanDecision/gold MAE=1/3. ConfIA/HumanDecision MAE=5/3. Export possui 3 records, 3 runs e 282 eventos sem IDs duplicados. [Verificação dos exports](assets/tme-december-d7/export-verification.json).

## 17. Screenshots

Viewport padrão do navegador, sem mudança cosmética de dimensões:

- [01 — prova finalizada](assets/tme-december-d7/01-finalized.jpg)
- [02 — sem gold](assets/tme-december-d7/02-no-gold.jpg)
- [03 — gold importado e métricas](assets/tme-december-d7/03-gold-metrics.jpg)

Inspeção visual confirmou aviso SHADOW, valores reais, filtros, downloads e formulário utilizáveis no layout existente.

## 18. Modified files

- `app/confia_lean_auditor/tme/certification.py`: records, projeção, manifest e CSV.
- `app/confia_lean_auditor/tme/certification_events.py`: eventos normalizados e cobertura.
- `app/confia_lean_auditor/tme/certification_gold.py`: import, validação e histórico separado.
- `app/confia_lean_auditor/tme/certification_metrics.py`: métricas e denominadores.
- `app/confia_lean_auditor/tme/certification_router.py`: endpoints opt-in.
- `app/confia_lean_auditor/tme/exam_router.py`: registro de rotas e disponibilidade no resumo.
- `app/confia_lean_auditor/static/tme/full-exam.js`: área mínima de certificação.
- `app/confia_lean_auditor/static/tme/index.html`: versão do script.
- `tests/test_tme_certification.py` e `tests/js/test_certification.cjs`.
- Este relatório e `docs/audits/assets/tme-december-d7/`.

## 19. Risks

Não observamos rejeições de extração nem início individual de checker; não exportamos tempos inventados. Rubric gold não equivale a gold de obligations. Observações atuais permitem rastrear etapas, mas não calcular accuracy por etapa sem rótulos independentes apropriados. Métricas descritivas pequenas não constituem estudo estatístico nem certificação matemática.

Gold é snapshot integral: a UI avisa que nova importação substitui o conjunto ativo, preservando versões. Códigos externos precisam ser pseudônimos e únicos na avaliação. Múltiplas tentativas/motores podem compartilhar o mesmo gold; usar agrupamentos/coorte explicitamente. A implementação lê stores locais sob locks e percorre auditorias: adequada à demonstração, sem indexação/paginação para grandes datasets. Falhas Lean ambientais permanecem visíveis; não foram “corrigidas” por conversão de technical_error em sucesso.

## 20. Commands

```sh
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_certification.py
/usr/local/bin/node --test tests/js/test_*.cjs
```

Regressão ampla:

```sh
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_certification.py tests/test_tme_finalization.py tests/test_tme_human_confirmation.py tests/test_tme_reanalysis.py tests/test_tme_question_audit.py tests/test_tme_review_workspace.py tests/test_tme_full_exam.py tests/test_submissions.py tests/test_transcriptions.py tests/test_recognition.py tests/test_recognition_invariants.py tests/test_mathpix_strokes.py tests/test_tme_pilot.py tests/test_tme_photo_errors.py tests/test_tme_home_summary.py tests/test_tme_demo_auth.py tests/test_assessments.py tests/test_teacher_decisions.py tests/test_core_auth.py tests/test_core_institutional.py tests/test_tme_accepted_integration.py tests/test_submission_audits.py tests/test_pauta_engine.py tests/test_tme2_p1_pauta_bridge.py tests/test_tme2_p2_pauta_bridge.py tests/test_rubric_bridge.py tests/test_public_audit_boundary.py
```

Reprodução limpa:

```sh
mkdir -p /private/tmp/confia-d7-baseline
git archive 5de838563ab3ae21c04c675b7edbd446ff844a79 | tar -x -C /private/tmp/confia-d7-baseline
cd /private/tmp/confia-d7-baseline
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline
```

Servidor de validação (store isolado e flags demo/opt-in definidos em `/tmp/confia-d7-environment.py`):

```sh
PYTHONPATH=app /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python /tmp/confia-d7-serve.py
git diff --check
git status --short
```

`git diff --check` sem erros. Git permanece com alterações locais, sem staging ou commit.

DECEMBER_DEMO_FUNCTIONALLY_COMPLETE
