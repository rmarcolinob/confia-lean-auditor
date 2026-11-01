# TME Integration 01 — transcrição aceita, auditoria e workspace

## Baseline e escopo

Antes de qualquer escrita, foi confirmado `git status --short` vazio, branch `feat/tme-dual-input`, commit `c4f5bc1c5af07a871bc31bbb163d151e35eb32a2`. O registro está em `artifacts/evaluations/tme_integration_01/baseline.json`. Não houve staging, commit, push, reversão ou atualização de snapshots para acomodar diferenças.

Esta tarefa conecta os cinco problemas ao fluxo existente. Nenhuma pauta, peso, regra do PautaEngine, producer matemático, checker ou gramática matemática foi alterada. O registry ganhou somente o alias público `TME2026P1` para o identificador histórico `TME2_P1_PILOT`. Seus IDs internos e hashes matemáticos continuam preservados; os quatro outros problemas já usavam os nomes públicos esperados.

## Arquitetura real encontrada

O piloto já tinha:

1. `CorrectionCase` (`tme/models.py`), com questão, origem `DIGITAL_INK`/`IMAGE_SCAN`, avaliador e submissão vinculada.
2. `SubmissionRecord`, `CaptureSnapshot`/`ScanSnapshot` e `SubmissionStore`, preservando original, páginas, hashes e vínculo ao caso.
3. `RecognitionService`, `RecognitionRun`, adapters existentes de reconhecimento e uma primeira `TranscriptionRevision` ainda `NEEDS_REVIEW`.
4. `TranscriptionRevision`, `TranscriptionAcceptance` e `TranscriptionAcceptanceReceipt`. O aceite atesta fidelidade da leitura, não correção matemática. O histórico projeta `ACCEPTED`, mas a cópia persistida da revisão mantém o status original; o recibo imutável é o vínculo de aceitação.
5. `AuditService`, `AuditSource`, `AuditRun` e `AuditRunView`, com locks, verificação da origem/recibo, persistência imutável, deduplicação e estado derivado `stale`.
6. Rotas `/tme/cases/{case_id}/audits`, serviços compartilhados de submission audits e workspace `static/tme/tme.js` + `workspace-report.js`.
7. `EvaluatorDecision`/`CaseStore.decide`, equivalente já existente de decisão humana do piloto. O fluxo institucional `TeacherDecision` utiliza o mesmo helper de snapshot da sugestão.

Antes da integração, a rota do piloto chamava `AuditService.execute`, que encaminhava todo texto ao `EngineRequest`/`execute_audit` do fluxo ITA. Ela ainda não chamava o registry opt-in TME.

Fluxo final:

```text
CorrectionCase + SubmissionRecord (digital ou scan multipágina)
  → RecognitionService / RecognitionRun ou transcrição manual
  → TranscriptionRevision revisada
  → TranscriptionAcceptance + TranscriptionAcceptanceReceipt
  → AuditService._validated_source
  → AuditSource com cópia da revisão aceita e TMEAuditContext
  → audit_accepted_tme_transcription
  → audit_tme → producers → bridge → PautaEngine
  → TMEAuditResult dentro do mesmo AuditRun
  → mesma API e workspace → EvaluatorDecision separado
```

Não foram criadas entidades paralelas de submissão, caso, revisão, auditoria ou decisão humana. `TMEAuditResult` é a variante tipada do conteúdo de resultado do AuditRun, não outro sistema de persistência ou scoring.

## Ponto exato do aceite e seleção da questão

`AuditService._validated_source` continua validando integridade da submissão, revisão, aceite, recibo, páginas e vínculo entre IDs. Só depois disso constrói `AuditSource`. Para IDs TME, anexa `TMEAuditContext`; `AuditService.execute` usa esse contexto para chamar `tme/accepted_audit.py::audit_accepted_tme_transcription`.

O `problem_id` vem exclusivamente de `SubmissionRecord.problem_id`, conferido contra `CorrectionCase` pelas rotas atuais. A requisição de auditoria não aceita texto substituto nem um override do problema. São admitidos no adapter os cinco IDs `TME2026P1` a `TME2026P5`. Questão ausente é rejeitada na criação; TME não suportado é rejeitado sem inferência/fallback. `pauta_for` retorna a categoria `TME_PROBLEM_NOT_SUPPORTED` quando chamado com ID inválido, inclusive não TME.

Compatibilidade: casos ITA que já utilizavam o piloto continuam no caminho ITA existente; não foram migrados nem reinterpretados. Isso é dispatch explícito pelo contexto previamente atribuído, não fallback quando um problema TME falha. O adapter TME não invoca o auditor ITA, OpenAI ou secondary adjudicator.

Os gates de entrada digital, scan e preview existente passaram a reconhecer os cinco IDs TME, sem modificar o catálogo matemático ITA nem o comportamento dos adapters Mathpix. `/tme/problems` inclui esses problemas. Não se inventou um enunciado oficial: os novos rótulos orientam a consultar a prova e identificar os itens na transcrição.

## Transcrição aceita e identificação dos itens

`TranscriptionSegment` ganhou dois campos opcionais:

- `tme_item_id`: item explicitamente atribuído (`a`, `b`, `c`, `d`, conforme a pauta).
- `tme_diagrams`: representações P2 já confirmadas, usando `DiagramSubmission` existente.

Esses campos integram a própria revisão e seu hash de aceite, não um payload lateral mutável da auditoria. Quando ausentes, a serialização histórica é preservada: não se adicionam defaults nulos a revisões/aceites legados. O mesmo cuidado foi aplicado ao novo contexto opcional de `AuditSource`.

Alternativamente, o texto aceito pode conter cabeçalhos isolados `[a]`, `(a)`, `a)` ou `Item (a)`, igualmente para os demais itens. A separação segue apenas esses marcadores ou o campo explícito. Não procura a questão ou o item pelo resultado, palavras matemáticas ou resposta esperada. Cabeçalhos conflitantes e itens inexistentes falham de forma fechada. Um trecho sem item explícito é preservado na revisão, gera aviso e não recebe atribuição automática; obrigações sem evidência permanecem indeterminadas. O workspace apresenta uma orientação curta sobre cabeçalhos, mantendo o editor/layout existente.

`solution.txt` preserva a conversão já existente dos segmentos aceitos. `accepted_revision.json` preserva a revisão exata com seus campos originais. `input_mapping.json` registra a entrada efetivamente entregue ao registry e os segmentos/páginas associados. A conversão para itens separa cabeçalhos, mantém fronteiras entre segmentos e remove terminadores de linha externos do bloco; não reescreve matemática. Os offsets de MathClaimRecord se referem ao documento enquadrado por itens dos collectors existentes, não a offsets inventados sobre uma foto. A UI consulta o trecho textual associado sem prometer highlight pixel a pixel.

## Resultado e persistência

`AuditRun.result` admite `AuditResponse` histórico ou `TMEAuditResult` (`tme-audit-result.v1`). O resultado TME inclui:

- ID público da questão, referência `transcription_id:revision_number` e hash da revisão aceita;
- `TMEAuditContext`: versão do adapter/código, schema da pauta, hash da pauta e modo de verificação Lean;
- cópia tipada da pauta usada, `PautaBridgeResult` completo e `PautaAssessment` completo;
- `score`, `max_score`, `needs_review` projetados diretamente de PautaAssessment, sem recalcular a pontuação;
- avisos de identificação de itens/desenhos;
- decisões recursivas por item/critério, intervalos de pontos, método/banda selecionados, carry-forward, evidence refs, source claim IDs, grounding, fontes de verificação, indeterminações, refutações e erros técnicos;
- status e referências das verificações Lean locais quando executadas.

A leitura valida a projeção dos campos de score, a correspondência da avaliação com a pauta/evidência persistidas, o vínculo à revisão/contexto e os hashes existentes do resultado e manifest. Origem de entrada, aceite, timestamps e artefatos originais permanecem em `AuditRun.source.provenance`. A própria evidência diagramática aceita permanece nessa revisão.

Exports obrigatórios: `audit.json`, `solution.txt`, `accepted_revision.json`, `input_mapping.json`. Certificados reais de provas/refutações positivas são copiados para a pasta de artefatos do run e entram no manifest obrigatório. A leitura verifica presença, tamanho, hash e ausência de symlinks. As referências originais dentro dos resultados matemáticos não são reescritas; o manifest relaciona cada fato/check à cópia durável. Uma alteração no certificado copiado é detectada no teste de integração.

A fronteira pública existente continua ocultando paths locais e diagnósticos de compilador. A API preserva o status formal e o manifest público da cópia; os detalhes internos completos continuam persistidos, não expostos como rótulos de produto.

O contexto TME versionado não finge ser um manifest GOV-01 do auditor ITA. O campo legado de reproducibility permanece `legacy_unversioned` na ausência desse manifest específico; a rastreabilidade TME está explicitamente em `context`, `auditor_version`, hashes da pauta/fonte/resultado e manifest de artefatos.

## Idempotência e histórico

A identidade existente do run inclui submissão, transcrição, revisão, aceite, hash da origem e `execution_key`. Para TME, o hash da origem inclui o contexto de execução. A versão do auditor contém um digest do código de integração, producers/checkers e infraestrutura matemática, além dos arquivos de toolchain/dependências declaradas. O hash separado da pauta identifica seu conteúdo, mesmo mantendo o schema `pauta.v1`.

Mesma revisão aceita, mesma pauta/código/modo Lean e mesma execution key reutilizam o run sob o lock existente. Uma nova revisão aceita, mudança de versão ou nova execution key gera identidade distinta. Runs anteriores são lidos com seu contexto/configuração persistidos, não reidentificados pela versão atual. Uma edição posterior altera somente a projeção `stale`; não modifica os bytes da auditoria antiga. Uma mudança de origem durante a execução impede publicação.

O digest do código não substitui captura completa do ambiente Python/Lean instalado. Uma mudança externa de toolchain não refletida nos arquivos declarados deve usar nova execution key/versionamento operacional; esse limite é documentado, não uma promessa de reprodutibilidade irrestrita.

## P2, indeterminação e falhas

`DiagramSubmission` é recebido somente como metadado confirmado de uma revisão aceita. Origem deve ser estudante, confirmação explícita e página consistente quando declarada. P2 usa o mesmo producer/checker diagramático existente. Não há reconhecimento novo, inferência de coordenadas ou LLM para olhar imagens.

Segmento `diagram` sem estado estruturado é preservado e gera aviso. Texto seguro continua auditável; colocação/configuração não estabelecida fica `indeterminate`. Um controle mantém A1=1 com a soma textual, enquanto A3 e configuração completa ficam pendentes. Não se cria um claim diagramático para preencher a lacuna.

`indeterminate` continua distinto de `refuted`. Prosa não suportada não recebe fallback. `technical_error` material mantém a semântica de pontuação pendente do PautaEngine; falha geral de execução persiste `FAILED`, `result=null`, sem inventar score zero. Se um método alternativo completo torna um erro técnico irrelevante, a sugestão numérica decidida pelo próprio PautaEngine é preservada — não há veto adicional à nota.

As pautas atuais podem usar `withhold`: um subtotal confirmado, inclusive zero, pode coexistir com `needs_review=true`. A integração preserva esse contrato, sem transformar ausência de evidência em falsidade matemática ou nota final automática. A UI identifica a sugestão como provisória e a decisão permanece humana. Não foi introduzida outra política de abstention.

## Workspace e decisão humana

O renderer existente reconhece a variante TME e usa as mesmas classes/layout para:

- sugestão ConfIA e máxima, com indicação de revisão;
- itens, pontos confirmados/possíveis e critérios da pauta;
- atendido, afirmação refutada, indeterminado e erro técnico;
- citações da transcrição/evidência diagramática confirmada;
- caminho selecionado e continuidade do raciocínio sem somar alternativas;
- “Verificação formal com Lean: confirmada (etapa local)” apenas com status/compilação/certificado adequados;
- “Verificação formal: afirmação incompatível (etapa local)” apenas com refutação verificada.

P5 possuía descrições iguais aos IDs internos na pauta. Foram acrescentados rótulos pedagógicos somente na apresentação, sem alterar a pauta. MathClaimRecord, FactResult, PautaEvidence, nomes de checkers e IDs de claims ficam nos detalhes técnicos. Não se afirma que a solução inteira foi provada em Lean.

`EvaluatorDecision.suggested_points` guarda o snapshot da sugestão; `final_points` guarda a decisão final. Ajuste exige justificativa quando diverge de sugestão numérica disponível. O helper existente `audit_snapshot` reconhece o resultado TME e preserva a decisão do PautaEngine. `TeacherDecision` institucional conserva seus campos próprios. Nenhum ajuste humano regrava AuditRun; isso é conferido byte a byte no teste.

## Validação

| Conjunto | Resultado |
|---|---:|
| PautaEngine, cinco problemas, submissões/transcrições/auditorias, API/workspace e decisões | 861 passed |
| Grounding, canonicalização, MathClaimRecord, fidelidade, crédito, scoring/alinhamentos e ITA | 703 passed |
| Novos testes de integração Python, distintos | 47 passed |
| Interface/DOM Node (incluindo três novos) | 136 passed |
| Saídas matemáticas comparadas ao baseline | 190/190 idênticas |
| Total Python distinto na seleção | 1611 passed |

Zero falhas nos conjuntos executados. Os 47 testes de integração foram validados em uma passagem de 43 e controles adicionais (5 + 1 execuções, com duas repetições); a coleta final confirma 47 testes. Logs iniciais e repetições não são somados novamente. A regressão compartilhada inclui o teste offline real ITA, além dos contratos de grounding/scoring.

| Problema | Solução completa pelo fluxo integrado | Casos matemáticos preservados |
|---|---:|---:|
| P1 | 20/20 | 20 |
| P2 | 20/20 | 55 |
| P3 | 20/20 | 25 |
| P4 | 20/20 | 38 |
| P5 | 20/20 | 52 |

Os cinco controles de equivalência digital/foto passaram. As duas verificações Lean reais no serviço terminaram com uma prova e uma refutação, ambas com cópia persistida do certificado. `git diff --check`: OK; índice vazio e HEAD/branch preservados.


Os testes de integração percorrem os cinco problemas com solução completa, parcial, falsa verificável e material indeterminado. Há comparação integral do JSON matemático com chamada direta ao registry, não apenas da nota. A matriz contém cinco controles digital/foto com bridge e assessment idênticos; adicionalmente, o teste do adapter Mathpix usa `httpx.MockTransport`, corrige uma leitura falsa e só depois aceita/audita. O texto bruto não aceito é rejeitado.

Controles adicionais: ausência de aceite; questão inválida/ausente/não TME no adapter; idempotência; nova revisão; nova versão; leitura de auditoria histórica; decisão humana separada; P2 com/sem estado; fronteiras entre segmentos; conteúdo sem item explícito; falha geral; indeterminate; technical_error material/irrelevante; carry-forward P5; métodos alternativos P3/P4/P5; status/certificado Lean e detecção de certificado alterado.

Os testes Lean locais executam `4! = 24` e refutam `2^4 = 8` pelo caminho integrado, copiando os certificados. Não houve chamadas externas em testes nem benchmark grande. A avaliação de interface foi feita por testes DOM/Node, sem alegar ensaio visual em dispositivos reais.

Comandos e logs, a lista de arquivos e a comparação dos 190 resultados estão em `artifacts/evaluations/tme_integration_01/validation_summary.json` e arquivos adjacentes. A suíte executada é a seleção de regressão descrita, não toda a suíte do repositório.

## Limitações remanescentes

- Reconhecimento manuscrito geral e reconhecimento topológico do diagrama P2 continuam não resolvidos.
- Compreensão irrestrita de prosa matemática livre continua não resolvida; a integração mede a lacuna, não a oculta com LLM/secondary.
- Acurácia em soluções humanas inéditas não foi medida nesta tarefa.
- É necessário identificar os itens explicitamente na revisão aceita. Não há inferência pelo conteúdo, nem novo editor visual para montar DiagramState.
- A confirmação estruturada upstream é uma declaração do avaliador/caller autorizado; o motor não autentica pixels nem verifica por visão a transcrição confirmada.
- Certificados/IDs de execução podem ter referências próprias de cada run; o invariante digital/foto diz respeito à matemática, pontuação e evidências de mesma transcrição, não a timestamps ou paths físicos de execução.
- Novos enunciados/imagens oficiais e implantação em ambiente real não fazem parte desta alteração.

## Arquivos e Git

Alterados (13):

- `app/confia_lean_auditor/recognition/preview.py`
- `app/confia_lean_auditor/static/tme/correction-workspace.js`
- `app/confia_lean_auditor/static/tme/tme.js`
- `app/confia_lean_auditor/static/tme/workspace-report.js`
- `app/confia_lean_auditor/submission_audits/artifacts.py`
- `app/confia_lean_auditor/submission_audits/schemas.py`
- `app/confia_lean_auditor/submission_audits/service.py`
- `app/confia_lean_auditor/submissions/schemas.py`
- `app/confia_lean_auditor/submissions/store.py`
- `app/confia_lean_auditor/teacher_decisions/service.py`
- `app/confia_lean_auditor/tme/registry.py`
- `app/confia_lean_auditor/tme/router.py`
- `app/confia_lean_auditor/tme/store.py`

Novos (6):

- `app/confia_lean_auditor/tme/accepted_audit.py`
- `app/confia_lean_auditor/tme/audit_artifacts.py`
- `app/confia_lean_auditor/tme/audit_models.py`
- `docs/audits/TME_INTEGRATION_01.md`
- `tests/js/test_tme_accepted_integration.cjs`
- `tests/test_tme_accepted_integration.py`

`implementation.diff` é o diff incremental contra o baseline limpo obrigatório; inclui arquivos novos, sem staging. `git_status.txt`, `git_diff_check.txt` e `scope_check.json` registram a verificação final. Os hashes de todas as cinco pautas, PautaEngine e producers/checkers matemáticos foram preservados.
