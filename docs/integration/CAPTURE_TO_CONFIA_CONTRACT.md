# Captura → ConfIA: contrato de integração DY6

Este documento orienta a integração de Rian/Luis. Captura não foi implementada no DY6. O motor consome texto versionado; não recebe arquivos, tokens OCR ou coordenadas como requisitos matemáticos.

```text
Arquivo / Foto / Tablet
        ↓
Capture / OCR / HTR (upstream)
        ↓
ExamSubmission → ExamPage (quando houver páginas)
        ↓
QuestionAttempt (CorrectionCase associado a AssessmentItem)
        ↓
TranscriptionVersion (TranscriptionRecord + TranscriptionRevision + aceite)
        ↓
──────── CONTRACT BOUNDARY ────────
        ↓
Dynamic Grader → Independent Reviewer → Reconciliation
        ↓
HumanDecision → FinalCorrection
```

## Responsabilidades e entidades reais

Captura preserva originais, produz texto, identifica questão e informa qualidade. ConfIA interpreta a matemática, verifica claims, aplica rubrica/política, reconcilia e oferece decisão docente. Lean pertence à verificação downstream.

Não existe entidade duplicada `TranscriptionVersion`: a identidade canônica é `transcription_id:revision_number`. `QuestionAttempt` reutiliza `CorrectionCase`. AssessmentItem fixa problema, enunciado, preparação, rubrica e pontos na publicação. ExamSubmission vincula avaliação publicada, participante pseudônimo e tentativas. ExamPage e o mapeamento existente permitem N páginas e N questões; texto nativo usa zero páginas, com original textual preservado na fonte de cada tentativa.

Campos necessários são obtidos dos contratos compartilhados, sem o cliente repetir contexto confiável:

| Informação | Campo/fonte |
|---|---|
| Tentativa/questão | `case_id`, `problem_id`, `assessment_item_id` |
| Avaliação/participante | `ExamSubmission.assessment_id`, `participant_id` |
| Versão/texto | `transcription_id`, `revision_number`, `segments[].text/latex` |
| Estado/aceite | `status`, `TranscriptionAcceptance.acceptance_id` |
| Origem | `source=manual/automatic/capture`, `provenance` ou `capture_origin` |
| Autor/data/motivo | `reviewer_reference`, `created_at`, `based_on_revision_number`, `change_reason` |
| Original | artefatos da fonte; `ExamPage.original_asset_id`; referências em `AuditSource.provenance` |
| Qualidade | `segments[].confidence`, `source_region`, `input_issues[]` |

## Fluxo REST existente

Todas as rotas abaixo exigem a autorização de avaliador existente. O contrato não cria IAM de serviços externos; a autenticação de um futuro worker é uma decisão ainda aberta. IDs devem vir das respostas, nunca ser inventados.

1. `POST /tme/exam-submissions` recebe `ExamCapturePackage`: `assessment_identifier`, `external_participant_code`, `external_namespace`, `idempotency_key`, `original_documents` (MIME e base64), `capture_metadata` e hints opcionais `pages`. Retorna ExamSubmission, ExamPages e QuestionAttempts. Mantém captura D1 existente.
2. `PUT /tme/exam-submissions/{exam_id}/page-mapping` recebe `expected_version` e `bindings`, cada um com `question_attempt_id`, `exam_page_id`, `order`. A associação deve estar definida e conferida. Não há classificação automática no Dynamic.
3. `POST /tme/cases/{case_id}/transcriptions` recebe o schema `CreateQuestionTranscription` abaixo. `origin=capture` importa somente candidatos já persistidos nos hints, com produtor/versão e páginas de origem. `origin=manual` recebe segmentos explícitos. Apenas a primeira transcrição pode ser criada por essa rota.

```json
{
  "origin": "manual",
  "expected_mapping_version": 1,
  "segments": [
    {"segment_id": "s1", "page_index": 0, "order": 0, "kind": "text", "text": "3z=-6; z=-2"}
  ]
}
```

4. Conferir em `GET /tme/question-attempts/{case_id}/workspace`, com Original / Transcrição / Comparar existentes. `POST /tme/cases/{case_id}/transcriptions/{transcription_id}/accept` recebe `{"revision_number":1}`. O servidor atribui o avaliador; aceite significa fidelidade da leitura, nunca verdade matemática.
5. A aplicação de correção usa `POST /tme/cases/{case_id}/audits` com `transcription_id`, `revision_number`, `acceptance_id`, `execution_key`. A camada de captura encerra sua responsabilidade antes dessa operação: não precisa chamar grader, reviewer ou reconciliation.

Para texto controlado, `POST /tme/exam-submissions/text` é o adaptador mínimo DY6. Recebe `assessment_identifier`, `external_participant_code`, `idempotency_key` e `solutions` (um texto não vazio por item, na ordem publicada). Cria originais textuais e revisões NEEDS_REVIEW. Não renderiza imagens nem simula OCR. Exemplo de conteúdo: `{"external_participant_code":"PSEUDO-01","idempotency_key":"lote-01-aluno-01","solutions":["S={3,4}","z=-2"]}` acompanhado do ID real da avaliação publicada.

## Versões, concorrência e prioridade humana

`POST /tme/cases/{case_id}/transcriptions/{transcription_id}/revisions` recebe `based_on_revision_number`, `change_type=reading_correction`, `change_reason`, `segments` e opcionalmente `input_issues`. Uma revisão concorrente recebe conflito 409. Atualizações nunca alteram o texto de uma auditoria anterior. Não reenviar como nova transcrição para contornar o controle de versão. Publicação automática inicial não pode substituir uma leitura existente da questão.

Estados existentes são reutilizados: DRAFT, NEEDS_REVIEW e ACCEPTED; corrente/histórica é projeção do encadeamento. Não foram criados RAW/MACHINE_TRANSCRIBED/SUPERSEDED redundantes. Origem de máquina é metadata (`automatic` ou `capture`), distinta do estado. Correção humana mantém provenance upstream e registra autor, data, predecessor e motivo; o workspace identifica a revisão humana. Aceitar uma versão antiga não a torna corrente.

D4/D5 tornam auditoria, revisão, reconciliação e decisão humana anteriores não correntes após nova leitura. Histórico e hashes permanecem. Nova versão exige novo aceite e nova análise. Prova finalizada exige reabertura explícita D6 antes de mudanças.

## Qualidade, erros e falha segura

`TranscriptionRevision.input_issues` é aditivo e opcional; ausência mantém hashes históricos. Cada item possui `code`, `message`, `segment_id` opcional e `requires_review` (default true). Códigos: UNREADABLE_SPAN, AMBIGUOUS_SYMBOL, INCOMPLETE_TEXT, MISSING_PAGE, UNCERTAIN_ASSOCIATION, PARTIALLY_REVIEWED. São problemas de **entrada**, distintos da incerteza matemática e de divergência grader/reviewer.

Uma revisão humana deve registrar nova versão resolvendo/removendo os problemas antes de analisar. Questão ausente/incompatível, versão inexistente, texto vazio, segmentos desconhecidos/sem texto ou issues pendentes não produzem nota. A API de análise retorna conflito com código `INPUT_REQUIRES_REVIEW` para qualidade insuficiente. Erros de integridade e de aceite mantêm categorias próprias. Análise matemática falha usa o contrato de auditoria; discordância de avaliação usa reconciliação.

Confiança global pode permanecer upstream; confiança por segmento e região já têm campos. Confidence nunca vale como prova matemática, nem vira zero automaticamente. Sem informação upstream, o sistema não detecta que uma frase aparentemente válida foi truncada ou atribuída à questão errada: o adaptador deve informar isso e exigir revisão.

## Preservação textual, spans e provenance

Texto e LaTeX são preservados na revisão; a conversão concatena segmentos sem normalização destrutiva. Unicode e LaTeX simples são aceitos como texto, mas nem toda notação é suportada pelo interpretador matemático. Nenhuma entrada Lean é exigida. Claims retêm offsets no texto convertido; `AuditSource` preserva revisão completa, hashes, segmentos, regiões e referências ao original. Não se inventam coordenadas onde elas não existem.

## Idempotência e eventos

Reenvio da mesma submissão com a mesma chave/conteúdo retorna os mesmos IDs; conteúdo diferente conflita. Mapeamento e revisões usam revisão esperada. Repetir criação inicial de transcrição conflita em vez de duplicar; após resposta perdida, consultar workspace antes de repetir. Aceite e auditoria têm recibos/chaves existentes. Não há fila distribuída nova.

Eventos observáveis da leitura incluem `transcription_created`, `transcription_revised`, `transcription_human_corrected`, `transcription_accepted`, `transcription_superseded`, `transcription_requires_review` e invalidação da auditoria. São projeções estáveis de registros imutáveis, não um barramento. Recebimento de submission/page/attempt é observável pelo manifesto e timestamps; não foram criados workers ou processamento pesado.

## Testes esperados e checklist

Fixtures cobrem texto manual versus provenance de máquina com o mesmo comportamento matemático, nova revisão humana com histórico preservado, controle de concorrência, bloqueio de entrada inválida e múltiplas questões/participantes. A regressão da captura existente é separada da validação matemática.

- [ ] Original preservado e referência recuperável quando existir.
- [ ] Submission e páginas criadas; texto nativo não exige páginas fictícias.
- [ ] QuestionAttempt associado explicitamente à questão publicada correta.
- [ ] Versão textual criada com provenance, autor/data e qualidade.
- [ ] Versão corrente e estado de revisão conferidos; aceite explícito.
- [ ] Dynamic consome a versão sem conhecer OCR/HTR.
- [ ] Mudança cria revisão com predecessor e motivo; concorrência é verificada.
- [ ] Retry não duplica entidades nem reativa leitura automática antiga.
- [ ] Auditorias, originais e decisões históricas continuam recuperáveis.

## Pontos abertos

Futuro endpoint de publicação por serviço externo (além dos hints da captura atual), credenciais de worker, confiança global, mapping claim→região visual e idempotência por job externo serão definidos pela frente de captura. `input_issues` está disponível no modelo e na API de revisão; importação inicial de hints ainda transmite confiança por segmento, não todo esse conjunto de issues. Um futuro adaptador pode publicar o mesmo modelo compartilhado, respeitando validação/lock/CAS, sem alteração dos motores DY3–DY5. Não foram implementados OCR/HTR, reconhecimento de fórmulas em imagens, câmera, segmentação, storage novo ou batch de captura.

## Validação DY6

Os 14 testes DY6 passaram, incluindo manual/máquina, várias questões/alunos, revisão humana, bloqueio de entrada e preservação histórica. O contrato está `CAPTURE_INTEGRATION_READY` dentro dos limites e pontos abertos acima; isso não declara captura, OCR ou autenticação de worker implementados. Evidência: `tests/test_dynamic_dy6.py` e relatório DY6.
