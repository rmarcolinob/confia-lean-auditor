# ConfIA — Captura manuscrita para o Produto 2

Versão da proposta: 1.0 · 30/09/2026
Status: especificação proposta; não é relatório de implementação no repositório.
Base interna: sugestão de tablet enviada pelo usuário, decisões desta conversa e arquivo “Auditoria do Estado Atual — ConfIA-Lean-Auditor”. A auditoria é um registro histórico, não uma inspeção ao vivo do Git.

## 1. Objetivo e limite

Acrescentar entrada manuscrita rastreável ao Produto 2 — Avaliação Assistida, preservando o auditor existente. A atividade complementar e a avaliação formal compartilham o motor, mas têm políticas próprias de entrega, assistência e revisão. Lean não passa a fazer parte do Produto 1.

A primeira implementação é um caderno experimental de captura. Não é uma avaliação escolar pronta, não atribui nota, não reconhece escrita e não autentica autoria. Sua finalidade é produzir fontes digitais reproduzíveis para os próximos componentes.

## 2. Arquitetura-alvo

```text
Texto digitado ───────────────┐
Papel/foto → original ────────┼→ CaptureSnapshot recebido pelo backend
Tablet → traços + PNG ────────┘               │
                                    TranscriptionRevision
                                      automática ou manual
                                               │
                                     revisão de fidelidade
                                               │
                                      NormalizedSolution
                                   texto + matemática + mapa
                                               │
                                   adaptador do AuditRequest
                                               │
                                   /audit existente, completo
                                               │
                                  evidências + sugestão docente
                                               │
                                     TeacherDecision registrada
```

Não ligar o reconhecedor diretamente a um extrator interno. A auditoria fornecida registra a sequência extract_claims → evaluate_formal_steps → build_attempt → run_lean_file → evaluate_microclaims → student claims/checks → rubrica/ajustes → relatórios. O novo canal deve passar pelo mesmo fluxo completo, sem reimplementar a rubrica na captura.

## 3. Regras de fidelidade

O transcritor deve preservar inclusive erros matemáticos. Se o aluno escreveu `2025 - 1012 = 1014`, esse é o conteúdo a transcrever; `1013` seria uma alteração, não uma melhoria da transcrição.

O normalizador pode uniformizar codificação e representação, mas não resolver contas, completar hipóteses, inserir lemas ou reparar argumentos. Preservar texto natural, negações, domínio, quantificadores, ordem de leitura e relações entre linhas. Toda transformação deve ter regra versionada e teste de preservação.

A ordem temporal dos traços não determina, sozinha, a ordem lógica da solução. Apagamentos e desfazer não devem reaparecer no PNG nem na entrada do reconhecedor. Desenhos não suportados continuam preservados como imagem e são sinalizados; nunca são silenciosamente descartados.

Não selecionar uma transcrição porque ela faz Lean aceitar a proposição. Fidelidade ao original e correção matemática são avaliações diferentes.

## 4. Fonte e revisões

- CaptureDraft: editável, salvo localmente; não significa entrega.
- SnapshotCandidate: cópia local congelada pela aplicação; ainda não é prova de integridade nem recibo institucional.
- CaptureSnapshot: versão recebida e validada pelo servidor, com identificador, horário de recebimento, hashes e referências aos artefatos.
- TranscriptionRevision: nova versão do texto reconhecido ou transcrito manualmente, sempre vinculada a um snapshot.
- ReviewDecision: decisão sobre a fidelidade de uma versão específica da transcrição, não sobre acerto matemático.
- NormalizedSolution: representação compatível com o auditor, com mapeamento até a fonte.

Um hash pode apoiar a detecção de alterações nos artefatos; não prova identidade do autor, ausência de ajuda ou autoria intelectual.

Para avaliações formais no primeiro piloto, proponho que o professor ou revisor autorizado confirme a transcrição. Confirmação pelo aluno é opcional e não substitui a política de aceite. Em atividades complementares, o aluno pode sugerir correções de leitura, sem substituir o manuscrito entregue. Uma nova resolução exige nova tentativa prevista pela atividade.

Se a transcrição for alterada após uma auditoria, o resultado anterior permanece associado à versão antiga. A nova versão precisa de nova auditoria; não atualizar texto embaixo de uma nota já produzida.

## 5. Contratos propostos

Os nomes abaixo são novos contratos propostos, não classes cuja existência foi confirmada.

| Objeto | Conteúdo essencial |
|---|---|
| CaptureDraft / SnapshotCandidate | schema_version, identificador local, problem_id, input_mode, páginas, dimensões lógicas, traços, operações mínimas, estado visível, configuração do renderizador |
| CaptureSnapshot | snapshot_id, receipt_id, vínculo com submission/attempt, horário do servidor, referências internas dos artefatos, hashes, versão do renderizador |
| TranscriptionRevision | revision_id, snapshot_id, provedor, versão informada ou null, versão do adaptador, resposta bruta, segmentos, incertezas |
| Segment | segment_id, tipo text/math/mixed/diagram/unknown, conteúdo, ordem revisada, página, bbox e/ou stroke_ids quando disponíveis, confidence_raw nullable, origem do escore |
| ReviewDecision | revision_id, ator autorizado, resultado, justificativa, horário, alterações propostas/aceitas/rejeitadas |
| NormalizedSolution | revision_id, normalizer_version, audit_text, source_map, pendências bloqueantes |
| AuditRun | run_id, submission_id, snapshot_id, revision_id, hash do texto enviado, versões do auditor/assets, resultado original |
| TeacherDecision | audit_run_id, docente, nota/parecer aprovado ou ajustado, justificativa, horário, liberação da devolutiva |

`strokes_uri` não é obrigatório para fotos. Referências devem ser IDs controlados pelo servidor, não caminhos de arquivos ou URLs arbitrárias aceitas do navegador. Papel mantém o original fotográfico; tablet mantém o documento de traços e a derivação visual.

Identidade, turma e permissões vêm da sessão autenticada e da atividade no servidor. Não confiar em `teacher_id`, `student_id`, `approved` ou `audit_ready` declarados livremente pelo cliente.

Os contratos devem usar a versão de Pydantic já instalada, proibir campos inesperados, validar números finitos, IDs/referências, limites de tamanho e cardinalidade. Não atualizar o ambiente apenas para copiar um exemplo de schema.

## 6. Adaptador do auditor

Preservar inicialmente o contrato legado `problem_id + solution`. O adaptador produz `solution = NormalizedSolution.audit_text` e armazena a proveniência em registro auxiliar vinculado à execução.

Comparar a saída do auditor para uma solução digitada de referência com a saída para a mesma solução recuperada da transcrição. Diferenças de formatação não devem alterar o raciocínio nem, sem motivo documentado, as evidências e a rubrica.

A correspondência claim → região só deve ser exibida quando realmente recuperável. Não inventar bbox, offsets ou confiança. Se o vínculo for ambíguo, registrar `unresolved` e permitir conferência humana.

## 7. Políticas de estados

```text
DRAFT_LOCAL
→ SNAPSHOT_LOCAL
→ RECEIVED_SERVER
→ TRANSCRIPTION_PENDING
→ TRANSCRIBED
→ REVIEW_REQUIRED
→ TRANSCRIPTION_ACCEPTED
→ AUDIT_QUEUED
→ AUDITED
→ TEACHER_REVIEWED
→ FEEDBACK_RELEASED
```

Ramos de erro devem distinguir armazenamento, transcrição, configuração, timeout e problemas matemáticos. Ausência de reconhecimento ou ilegibilidade não é nota zero. No MVP, pendência crítica de leitura bloqueia a auditoria automática e encaminha para revisão manual. Uma avaliação humana pode prosseguir sem uma auditoria automática bem-sucedida, com isso registrado.

`student_confirmed=true` não autoriza sozinho a mudança de estado. Transições de entrega/revisão/decisão precisam ser aplicadas pelo backend.

## 8. Captura web

Usar Pointer Events com detecção de capacidades. Caneta como entrada principal; mouse em modo de teste explícito; toque no canvas não desenha no modo caneta. Tratar `pointercancel`, perda de captura, redimensionamento e rotação. Testar palma em dispositivos reais, sem prometer compatibilidade universal.

Guardar os pontos recebidos antes de suavização. Se perfect-freehand for utilizado, manter versão/opções do renderizador e preservar o valor de pressão reportado pelo navegador sem tratá-lo como medição calibrada. Nunca converter pressão simulada em dado de sensor.

Não incluir eventos preditos na fonte persistida. A geometria deve estar em coordenadas lógicas da página, independentemente da resolução do canvas e de devicePixelRatio.

Borracha de traço inteiro no primeiro incremento. O PNG representa somente a escrita ativa. Fundo quadriculado é um auxílio visual; exportação de reconhecimento em fundo branco, sem grade, com a mesma geometria e traços.

Salvar rascunhos em IndexedDB; exibir separadamente salvamento local e recibo do servidor. Falha/quota de armazenamento deve gerar mensagem, não falsa confirmação. Em tablet compartilhado, restauração nunca pode abrir silenciosamente o rascunho de outra pessoa; isolamento autenticado entra antes do piloto escolar. Não apagar a única cópia em falhas de envio.

## 9. Transcrição desacoplada

Começar com provedor manual, claramente identificado, para testar o fluxo sem depender de OCR. Em paralelo comparar Mathpix por traços, Mathpix por PNG e, quando houver credenciais autorizadas, um modelo de visão.

A documentação consultada confirma `POST /v3/strokes`, entrada em arrays x/y e limite de corpo JSON de 512 KB. O adaptador deve lidar com o limite por página/região ou encaminhar para alternativa; não destruir a fonte original para caber no limite. O endpoint admite opções de saída de `/v3/text`; validar os campos efetivamente retornados. Não prometer bbox e confiança por linha em todos os casos.

Confiança do provedor é metadado bruto. Não inventar valores ausentes, não comparar diretamente escores de fornecedores distintos como se fossem probabilidades calibradas e não usá-los como nota ou cobertura Lean.

O transcritor não recebe gabarito, rubrica ou solução canônica para completar escrita. Para modelo de visão, conteúdo manuscrito é dado, não instrução executável. Não usar ferramentas autônomas a pedido de texto encontrado na imagem.

KaTeX serve para renderização, não para validar matemática. MathLive pode ser acrescentado depois que o fluxo de revisão estiver estabilizado. Aplicar renderização segura, conteúdo escapado e limites de entrada.

## 10. Requisitos antes do piloto avaliativo

O relatório histórico registra ajustes que zeram itens quando student check tem `failed`. Antes de usar notas, examinar se o status separa proposição refutada de falha de prova/execução. Uma tática falhar não constitui prova da negação. Não converter automaticamente timeout, erro de sintaxe, falta de lema ou transcrição incerta em erro do aluno.

Também não apresentar `compiled=true` de um arquivo como prova de toda a solução. A interface deve separar leitura confirmada, proposições efetivamente verificadas e decisão docente.

Permissões: aluno acessa somente seus registros; professor somente submissões das turmas atribuídas; direção recebe indicadores conforme escopo institucional, sem acesso irrestrito automático a manuscritos/conversas. Validar cada leitura e escrita no backend. Dados de teste inicialmente fictícios ou de adultos autorizados.

Provedores externos: credenciais no servidor, política de minimização/retenção definida e configuração registrada. Para os endpoints Mathpix de imagem/traços, a documentação informa efeitos de `metadata.improve_mathpix: false`; isso não substitui a avaliação institucional do fornecedor e nem elimina metadados de faturamento.

## 11. Implementação por incrementos, não por calendário

| Incremento | Entrega | Critério de aceite |
|---|---|---|
| P2-CAP-01 | Caderno local, contrato de captura, PNG e testes | Escrever, apagar, restaurar e exportar sem perda silenciosa; /audit inalterado |
| P2-CAP-02 | Recebimento persistente, recibo, vínculos e visualização docente | Reabrir no servidor; acesso testado; revisão manual versionada |
| P2-CAP-03 | Normalizador/adaptador, auditoria e decisão docente | Comparação com texto de referência; rastreio completo; falhas não viram nota |
| P2-CAP-04 | Reconhecedor automatizado intercambiável | Mesmo contrato; erros preservados; ambiguidades sinalizadas; revisão não burlada |
| P2-CAP-05 | Piloto integrado e regressão | Testes de caneta/tablets, papéis, falhas, revisão, latência e validade do relatório |

P2-CAP-04 pode avançar em paralelo pela equipe de imagem, usando os artefatos de P2-CAP-01 e os contratos acordados. Não depende de ampliar o banco de problemas nem de redesenhar a interface inteira.

## 12. Validação

Selecionar dois problemas com cobertura auditável confirmada. Pela auditoria histórica, F2Q1 e F2Q8 são candidatos por possuírem student claim checking; não assumir que qualquer questão formalizada tem a mesma cobertura.

Comparar, para cada solução: original visual; transcrição literal humana revisada; saída de cada reconhecedor; saída normalizada; auditoria do texto de referência; auditoria da transcrição aceita. Incluir soluções certas, falsas, incompletas, rasuradas, ilegíveis e com símbolos críticos.

Medir separadamente: perda de traços; discrepância entre PNG e estado visível; alterações de significado na transcrição; omissões de hipóteses; esforço de revisão; desacordo da auditoria provocado pela captura; falhas/timeout; latência. Uma demonstração curada não estima desempenho de rede de ensino. Cache de reserva deve ser rotulado como resultado previamente processado.

## 13. Referências técnicas consultadas em 30/09/2026

- W3C, Pointer Events: https://www.w3.org/TR/pointerevents3/
- perfect-freehand, repositório oficial: https://github.com/steveruizok/perfect-freehand
- MDN, IndexedDB: https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API
- Mathpix, Process Strokes: https://docs.mathpix.com/reference/post-v3-strokes
- Mathpix, Process Images: https://docs.mathpix.com/reference/post-v3-text
- Mathpix, Data Retention: https://docs.mathpix.com/concepts/data-retention
- KaTeX, Security: https://katex.org/docs/security.html
- Lean, Tactics: https://lean-lang.org/theorem_proving_in_lean4/Tactics/
