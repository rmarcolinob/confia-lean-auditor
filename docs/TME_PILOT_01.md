# TME-PILOT-01 — Correção ConfIA com dupla entrada

## Objetivo e acesso

`GET /tme` oferece uma shell exclusiva para avaliadores: Correções, Nova correção e Resultados. O piloto não altera os módulos escolares. A lista de questões vem do catálogo real da instalação; incluir questões oficiais do TME e suas rubricas no catálogo é uma etapa operacional posterior. O piloto não integra SSO, cadastro de participantes, ranking nem publicação de notas.

### Modo autenticado (padrão)

Com `CONFIA_TME_DEMO_NO_AUTH` ausente, `0` ou `false`, `/tme` e suas APIs exigem uma sessão válida de avaliador `TEACHER`. A identidade autenticada permanece na proveniência. O switch legado `CONFIA_AUTH_ENABLED=0` não habilita a demonstração TME.

### Modo demonstração local

Para piloto/apresentação local, inicie a aplicação com:

```sh
CONFIA_ENV=development CONFIA_AUTH_ENABLED=1 CONFIA_TME_DEMO_NO_AUTH=1 \
  .venv/bin/uvicorn confia_lean_auditor.main:app --app-dir app --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000/tme`. A experiência começa diretamente em **ConfIA — Confiabilidade e Explicabilidade**, com a identificação discreta **PILOTO ConfIA**, sem login ou seleção de perfis. TME permanece apenas nos identificadores internos e rotas. `true` também ativa a flag; valores inválidos falham na configuração. **NO_AUTH existe somente para piloto/demo local.** Com `CONFIA_ENV=production` e a flag ativa, o startup falha explicitamente antes de servir requisições.

A dependência `require_tme_evaluator()` usa um principal `TMEEvaluator`, sem role escolar e sem criar `AuthUser`, conta ou sessão. Sem sessão, sua identidade estável é `tme-demo-evaluator`. Se houver sessão válida de professor, prevalece a identidade desse usuário; uma sessão de outro perfil continua recebendo 403. Casos autenticados e casos demo mantêm escopos de criador separados. Todos os visitantes anônimos do mesmo demo compartilham esse principal e seus casos; não há isolamento entre participantes da apresentação.

`created_by_user_id`, `submitted_by_user_id`, `reviewer_reference` das revisões/aceites e `decided_by_user_id` registram o principal no servidor. A referência enviada pelo navegador não substitui a identidade do avaliador. A auditoria preserva essa proveniência no aceite vinculado à fonte. Não se usa login do participante nem se exige escola, turma, Enrollment ou TeacherAssignment no fluxo TME.

O escopo público com a flag ativa é `/tme`, `/tme/problems` (catálogo necessário à correção) e as operações sob `/tme/cases/{case_id}`: caderno, captura/upload, reconhecimento, páginas, transcrições, revisões, aceite, auditorias e decisão. Cada operação valida o criador e os vínculos entre caso, submissão e artefatos. O caderno incorporado também usa essas rotas. As APIs escolares `/submissions`, `/transcriptions`, `/submission-audits`, `/assessments`, `/institutional`, `/management/*`, `/capture`, `/problems` e `/audit` mantêm sua autenticação e RBAC; `/` mantém o login normal. A flag não concede papel de professor fora do TME. Mutações continuam sujeitas à proteção same-origin.

## Apresentação e escrita digital

A shell reutiliza `/static/design-system.css` e seus tokens de azul institucional, azul forte, branco e superfícies neutras; não define uma nova paleta. O menu contém somente Nova correção, Correções e Resultados. O layout mostra manuscrito e transcrição lado a lado em telas largas e empilha as colunas em telas estreitas, com controles de toque de pelo menos 44 px.

O caderno incorporado é o mesmo usado pela captura existente. O modo piloto mostra o enunciado da questão selecionada inicialmente expandido e fixo durante a rolagem. A toolbar mantém Caneta, Escrever, Borracha, Desfazer e Refazer logo abaixo. Um `ResizeObserver`, com atualização também ao redimensionar e expandir/recolher, mede a altura real do enunciado e atualiza o offset da toolbar. Os controles de página ficam fora da faixa fixa e a recuperação do rascunho fica depois do caderno para priorizar a escrita. Não há uma segunda implementação de canvas, strokes, S Pen, autosave, undo/redo, snapshot ou preview.

## Envelope e fontes

`CorrectionCase` registra `case_id`, `external_candidate_ref` pseudônimo, `problem_id`, `source_mode`, criador, data, status e `submission_id`. Ele não duplica a solução. A decisão humana TME é um registro próprio porque `TeacherDecision` exige `Assessment`, item e vínculo escolar; seus cálculos de sugestão e política inconclusiva são reutilizados. O TME não atribui uma matrícula fictícia ou o participante ao avaliador.

`Submission` permanece o objeto comum e imutável para as duas fontes. `source=tablet` mantém a captura atual, strokes, páginas, autosave, preview e Mathpix `/v3/strokes`. `source=image_scan` acrescenta um manifesto `ScanSnapshot`, originais `original_N.bin` preservados byte a byte, e `page_N.png` derivados para OCR. O manifesto registra ordem, MIME, horário de captura, rotação, dimensões e transformação. Referências registram SHA256 e tamanho. Os campos novos são opcionais para registros históricos; revisões, aceites e fontes de auditoria antigas preservam seus hashes. A integridade dos originais e derivados é verificada antes de reconhecer, transcrever ou auditar.

O navegador aceita JPEG, PNG, WebP e HEIC/HEIF quando consegue decodificar. A prévia permite confirmar, repetir, remover, reordenar e girar 90°. O arquivo original nunca é modificado. A derivação é desenhada em canvas com orientação efetiva, limitada a 2048 pixels no maior lado e exportada em PNG. Um formato não decodificável recebe mensagem clara. O limite é três páginas, como na captura digital existente, e 8 MiB por arquivo. Não há detecção automática de borda ou deskew.

## Reconhecimento e transcrição

O provider `mathpix` continua exclusivo para strokes. `mathpix_image` usa os mesmos segredos apenas no backend e envia cada PNG derivado a `POST /v3/text` como `multipart/form-data`, com `file` e `options_json`. As opções incluem `formats=["text"]`, `enable_document_layout=true`, `include_line_data=true`, `rm_spaces=false` e `metadata.improve_mathpix=false`. `text` (Mathpix Markdown) é a representação principal da página; `latex_styled` só entra quando `text` estiver ausente. Assim, texto e LaTeX equivalentes não duplicam a vista ou o texto auditado. O adapter retorna `ProviderOutput` com segmentos ordenados por `page_index`, metadados e categorias de erro sem credenciais.

As duas entradas publicam `RecognitionRun` e `TranscriptionRevision` pelo mesmo `RecognitionService`. A interface mostra manuscrito e uma única transcrição legível. A edição cria outra revisão imutável pelo serviço existente, acessado pela rota vinculada ao caso TME. No workspace CORR-WORKSPACE-01 a conferência humana deixou de ser uma etapa obrigatória. Ao solicitar a análise, a interface obtém o vínculo da revisão pelo endpoint de aceite existente, registrando em `acceptance_note` que a vinculação é automática e não exige conferência humana. O contrato legado do aceite mantém o campo de fidelidade de representação; sua existência, neste fluxo, não deve ser interpretada como prova de revisão humana. Nenhuma validade matemática é declarada por esse vínculo. Se o OCR falhar, os arquivos persistem e o avaliador pode tentar novamente. Para teste físico do OCR são necessárias credenciais Mathpix ativas; a suíte usa transporte simulado.

### Diagnóstico e configuração do reconhecimento por foto

Na investigação da falha local, `CONFIA_MATHPIX_APP_ID` e `CONFIA_MATHPIX_APP_KEY` estavam ausentes no processo que servia a aplicação. Sem ambas, `configured_registry` não registra `mathpix_image`; a rota retorna 503 antes de chamar o Mathpix. A submissão da foto tinha original e PNG derivado íntegros, com SHA256 correspondente, e nenhum `RecognitionRun`. Portanto, a falha observada era de configuração, não uma rejeição de MIME ou de payload pelo serviço externo.

Para habilitar OCR real, disponibilize essas duas variáveis no ambiente do **processo servidor** e reinicie a aplicação. Defini-las em outro terminal depois do startup não altera o processo já em execução. Não coloque credenciais em JavaScript, arquivos versionados, mensagens de erro ou documentação. A demonstração sem login não dispensa a configuração do provider. O provider de strokes permanece separado e inalterado.

O adapter de imagem mantém `POST /v3/text`, upload multipart com PNG e `options_json`, limite de tempo e validação de `ProviderOutput`. Ele classifica falhas HTTP e também erros de aplicação retornados com HTTP 200. Apenas códigos e mensagens fixas são publicados; corpo do provider, conteúdo sensível e credenciais não são refletidos.

| Situação | Código público |
| --- | --- |
| Configuração ausente (503 local, sem chamada ao provider) | `PROVIDER_NOT_CONFIGURED` |
| Credencial recusada / HTTP 401 | `PROVIDER_UNAUTHORIZED` |
| Acesso recusado / HTTP 403 | `PROVIDER_FORBIDDEN` |
| Limite de uso / HTTP 429 | `PROVIDER_RATE_LIMITED` |
| HTTP 5xx | `PROVIDER_UNAVAILABLE` |
| Timeout | `PROVIDER_TIMEOUT` |
| Falha de conexão | `PROVIDER_TRANSPORT_ERROR` |
| Resposta malformada | `INVALID_PROVIDER_RESPONSE` |
| Falha ao validar o resultado convertido | `INVALID_PROVIDER_OUTPUT` |
| Imagem recusada, inválida ou sem conteúdo legível | `INVALID_IMAGE` |

`GET /tme/cases/{case_id}/recognition-status` oferece o estado persistido e a mensagem segura. Na tela, os estados são **Aguardando reconhecimento**, **Reconhecendo**, **Reconhecida** e **Falha de reconhecimento**. Durante a chamada, os botões de nova tentativa ficam desabilitados. A indisponibilidade de configuração mostra “Reconhecimento por foto indisponível neste ambiente.”; limites, credenciais, timeout e demais falhas têm orientações específicas, sempre preservando as páginas.

As ações **Tentar novamente** e **Voltar e ajustar páginas** ficam disponíveis após a falha. Uma nova tentativa usa a mesma fonte imutável e gera outro run. O ajuste recupera os originais pelo manifesto protegido `GET /tme/cases/{case_id}/scan-manifest`, mantendo bytes, MIME, ordem, horário e rotação; os arquivos existentes não são sobrescritos. Ao confirmar páginas ajustadas, cria-se outra correção com uma nova fonte, preservando a correção anterior e todo seu histórico. A interface informa essa criação antes de continuar.

## Convergência, auditoria e decisão

Tablet e scan terminam em uma transcrição aceita. `AuditService._validated_source`, `build_source` e `AuditService.execute` são compartilhados. A origem física não altera claims, rubrica, Lean, política inconclusiva ou GOV-01. A fonte de auditoria do scan lista os originais como evidência e inclui a proveniência dos PNGs usados no OCR dentro da revisão. Um teste de paridade confirma que a mesma transcrição aceita nas duas entradas alcança o mesmo serviço central de auditoria.

Na decisão TME, ConfIA sugere e o avaliador define pontos finais. Uma divergência da sugestão exige motivo. Uma análise inconclusiva ou com erro técnico não gera sugestão. A decisão registra vínculos de hash com a fonte e o resultado da análise quando disponíveis. O piloto não publica nota no sistema TME.

## Análise explicável compartilhada

A regressão de apresentação do piloto estava em `static/tme/tme.js`: depois de receber a resposta da auditoria, a tela exibia apenas `score / max_score`, inclusive quando `score` era `null`. O backend já persistia e devolvia o `AuditRun` completo. As rotas de piloto e Professor usam o mesmo `AuditService` e a mesma projeção pública, que remove caminhos locais e diagnósticos sensíveis sem descartar os critérios e evidências.

O renderer antes acoplado a `static/app.js` foi extraído para `static/audit-view.js`. O Professor e o piloto passam `run.result` e o próprio `AuditRun` a `ConfIAReport.render`; os estilos compartilhados estão em `audit-view.css`. A navegação e os formulários de decisão continuam próprios de cada contexto. Não existe relatório matemático alternativo para foto ou para o piloto.

A análise mostra:

- Resultado sugerido, pontuação numérica quando existente e **Não determinada** quando nula.
- Resumo pedagógico existente (ou `feedback` quando não há resumo), evidências e pontos de atenção.
- Todos os critérios, descrição, máximo, pontos decididos, status matemático, evidência e justificativa registrada. `indeterminate` não vira zero; falha técnica não vira refutação.
- Claims extraídos e claims do participante, suas afirmações, evidências e verificações correspondentes. A ausência de claims é indicada explicitamente.
- Verificação matemática seletiva: claims/passos verificados, não formalizados, não verificados e verificações não concluídas. Refutação formal exige o vínculo de refutação existente; nenhuma indicação afirma que toda a solução foi formalizada.
- Motivo da inconclusividade e contagem de critérios decididos. A soma exibida como **Pontos decididos** é apenas uma explicação dos itens resolvidos, sem substituir a pontuação global nula ou a decisão humana.
- Observações de conversão da fonte e limitações das verificações.
- **Detalhes técnicos da análise**, inicialmente recolhidos, com o run, provenance, hashes, referências dos artefatos e o ambiente GOV-01 existente. Metadados históricos continuam explicitamente não versionados quando aplicável.

A decisão do avaliador aparece abaixo da análise completa, inclusive ao reabrir uma decisão registrada. A pontuação sugerida e a pontuação final têm rótulos distintos; uma análise inconclusiva continua permitindo decisão manual. O motor, extractors, projeção pública, rubricas, arquivos Lean, política de pontuação, modelos de domínio e hashes persistidos não foram alterados neste ajuste.

Os testes comparam a árvore semântica produzida pelo Professor e pelo piloto para o mesmo run, tanto em foto quanto em escrita digital. Os contratos HTTP verificam os campos completos e a integridade do run antes/depois das leituras e da decisão. As fixtures de apresentação são sintéticas e não constituem novas avaliações matemáticas.

Validação deste ajuste: **134 testes Python** (piloto, autenticação, payload completo, fronteira pública, GOV-01 e workflow Professor) e **356 testes JavaScript** passaram. A inspeção no navegador confirmou a análise completa nas duas entradas, incluindo pontuação nula, critérios, evidências, claims e decisão manual disponível, com dados sintéticos em servidor isolado.

## Privacidade, limites e operação

O código pseudônimo fica no `CorrectionCase` e não vai ao Mathpix. O provider envia só o PNG necessário ao OCR, nunca o identificador do participante. Credenciais não aparecem no frontend, erros públicos ou logs do adapter. O modo autenticado exige `TEACHER`; acesso a casos e suas submissões é limitado ao criador. A origem de mutações segue a proteção same-origin da aplicação. O diretório de runtime deve ser protegido por permissões do processo.

O scan mantém até três páginas e depende da capacidade do navegador de decodificar a foto antes de gerar o PNG. O endpoint `/v3/text` ignora orientação EXIF; por isso a orientação visual é aplicada nos pixels derivados. Em dispositivos que não renderizam HEIC, a revisão mostra o PNG derivado, enquanto o original continua acessível e preservado. As rubricas atuais do catálogo são de questões ITA; questões TME só devem ser incluídas com seus próprios ativos matemáticos validados.

## Benchmark futuro

`benchmarks/tme_input_modes/` define uma futura comparação pareada de strokes, scan e transcrição de referência. Não há medições ou amostras fictícias no piloto.

## Verificação do ajuste visual e de reconhecimento

A suíte selecionada de backend passou com **194 testes**, cobrindo o piloto, demo/autorização escolar, provider de imagem, erros seguros, timeout, retry, integridade dos originais, revisão/aceite, paridade de auditoria, contratos de captura e regressões de strokes/preview. A suíte JavaScript completa passou com **346 testes**, incluindo os cinco controles do caderno, offset do enunciado, estados de reconhecimento e recuperação das páginas preservadas.

A inspeção no navegador usou um servidor isolado com dados sintéticos e transporte Mathpix simulado: confirmou enunciado/toolbar durante rolagem e expansão, falha HTTP 429, ajuste de páginas e retry até a transcrição. Isso não equivale à validação de OCR externo com credenciais reais nem ao teste físico de S Pen; ambos dependem do ambiente/dispositivo operacional.

Referências: [Mathpix v3/text](https://docs.mathpix.com/reference/post-v3-text), [erros Mathpix](https://docs.mathpix.com/reference/error-handling) e [privacidade Mathpix](https://docs.mathpix.com/concepts/privacy).


## CORR-WORKSPACE-02 — estação profissional de correção

`/tme` mantém as rotas e os objetos existentes. A interface usa uma sidebar
de 220 px, recolhível para 72 px, com Correções, Nova correção, Resultados e
fila recente de casos com indicadores de status. O contexto compacto inclui o indicador
Entrada → Transcrição → Análise → Decisão. O indicador não é um wizard.

A solução ocupa aproximadamente 60% da área útil no desktop e a análise 40%.
Original, Transcrição e Comparar lado a lado alternam a visibilidade dos mesmos
nós; página, zoom e rotação não alteram os originais. A análise pode ser recolhida.
O divisor pode ser arrastado ou ajustado com setas, Home e End; duplo clique
restaura 60/40. O limite de ajuste é 40–75% para a solução.
Desktop (a partir de 1200 px) usa split view; tablet (768–1199 px) abre a análise
em drawer não modal, com fechamento por Escape e retorno de foco; celular
(abaixo de 768 px) apresenta os painéis sequencialmente.
Os controles possuem texto, labels, estados ARIA, foco visível e região de status.

A transcrição é gerada após o envio da foto ou do caderno. No caderno TME a prévia
é opcional; o fluxo escolar conserva seu comportamento. O iframe só é substituído
após a notificação de término do reconhecimento. A ação **Analisar com ConfIA**
vincula a revisão corrente automaticamente pelo contrato existente e executa a
análise, sem botão obrigatório de conferência. `reviewer_identity_verified=false`
e a nota de vinculação permanecem no recibo. Não foi feita migração de backend.
**Editar** continua gerando uma nova revisão imutável.

O renderer compartilhado `ConfIAReport` recebe o AuditRun completo. A opção
`workspace` delega ao componente `ConfiaWorkspaceReport`: resultado compacto,
cobertura, critérios expansíveis, mapa selecionável de passos e resumo da
verificação matemática. Evidências e detalhes técnicos ficam em disclosures.
Cobertura conta critérios decididos e claims formalmente verificados; não é
probabilidade de acerto. O mapa mantém a evidência original e oferece um callback
`onEvidenceSelection({claimId, mapping:null})` para um futuro vínculo preciso.
Não são inferidos offsets nem destacados trechos por semelhança textual. Pontuação nula continua não determinada;
falhas técnicas não viram refutação matemática. A formalização é seletiva.
A barra sticky inferior mantém sugestão, pontuação final, **Usar sugestão** e
**Finalizar correção** acessíveis. Observação, justificativa e pontuação máxima
ficam recolhidas. **Usar sugestão** copia a nota exata, inclusive zero, e permanece
desabilitado para `null`. A decisão usa o endpoint existente, admite nota humana
sem sugestão numérica e
preserva os rascunhos durante trocas de abas, recolhimento e navegação da sessão.
Página, zoom, rotação, tab, rascunho de decisão, edição, critério expandido, passo
selecionado e filtros das filas são mantidos na memória da sessão durante a
navegação. Somente largura do split e preferência da sidebar são salvas em
`localStorage`; não são armazenadas transcrições ou decisões nesse storage.
Recarregar o navegador descarta rascunhos ainda não enviados.

A fila consulta as APIs existentes com até quatro casos simultâneos, reaproveita
o cache da sessão e oferece atualização explícita. Busca por código e filtros
por questão, origem e status não fazem novas requisições. Não há nova API agregada.

O componente `ConfiaWorkspaceControls` concentra resize e persistência da
largura. `tme.js` coordena os painéis e usa as mesmas APIs; `workspace-report.js`
compõe a análise a partir dos helpers do renderer compartilhado. Nenhum motor,
modelo ou contrato de backend foi alterado neste redesign. Skeletons discretos
apresentam reconhecimento ou análise/verificações; o frontend não simula
subetapas que a API não informa. A paleta de comandos opcional não foi incluída.

Validação: suíte JavaScript, contratos estáticos Python de TME e inspeção em
navegador com fixture sintética em desktop, tablet e celular. A prévia não chama
Mathpix nem executa uma correção real.

## CONFIA-TME-HOME-01 — Home do avaliador

A entrada `/tme` abre a Home. Início, Fila, Nova e Resultados usam a navegação
existente, sem novas rotas de backend. No celular, a sidebar inteira fica oculta,
a navegação inferior é fixa e respeita a safe area. A fila tem cards no mobile;
a tabela existente continua disponível no desktop. O workspace de correção não
foi redesenhado nesta tarefa: somente sua navegação externa e os offsets
necessários para evitar sobreposição com a barra inferior foram adaptados.

`home.js` concentra `TmeHome`, `HomeHeader`, `PrimaryCorrectionCTA`, `QuickActions`,
`OverviewMetrics`, `PriorityQueue`, `ExamProgress`, `MobileBottomNav`, `StatusPill`,
`MetricCard`, `PriorityCaseRow` e `ExamProgressCard`. `home.css` define tokens de
cores, espaçamentos, raios e sombras para reutilização futura, sem trocar o
stylesheet interno do workspace. Não há framework, fonte ou pacote de ícones novo.

### Dados e limites originais de HOME-01 (substituídos por HOME-03)

A Home faz uma consulta a `GET /tme/cases`, já limitada pelo servidor ao avaliador,
além da identificação de sessão existente. Requisições simultâneas à lista são
compartilhadas. Não consulta imagens, transcrições, RecognitionRuns, AuditRuns,
decisões individuais ou artefatos Lean. As prévias renderizam no máximo três casos
e duas provas, inclusive com milhares de registros na lista. A API atual ainda
retorna todos os metadados em uma resposta, sem paginação; a Home não altera esse
contrato nem a estratégia de carregamento da tela Fila.

- `IDENTIFIED`: Pendente.
- `SOURCE_READY`: Em andamento (solução enviada; não significa processamento ativo).
- `DECIDED`: Finalizada.
- Inconclusivas: `—` e indicação de indisponibilidade, pois a lista atual não
  informa esse resultado. Em um conjunto vazio, a contagem é zero.
- **Hoje**: estado atual dos casos **criados hoje**, no dia local do navegador.
  Não é uma contagem de decisões tomadas hoje; o endpoint não fornece essa data.
  **Todo o período** usa a lista inteira.

**Corrigir próxima** usa apenas a fila autorizada: exclui `DECIDED`, prioriza
`SOURCE_READY` e depois os demais casos, preservando a ordem recebida no desempate.
Não existe endpoint de próxima correção, atribuição independente do criador,
reserva concorrente, nem metadado resumido de “aguardando decisão”/“inconclusiva”.
Essas prioridades não são inferidas a partir de matemática ou de dados ausentes.

O progresso agrupa por `external_candidate_ref`, distingue questões pelo
`problem_id` e usa o caso mais recente de cada questão quando há reenvios. O
numerador conta questões com esse caso finalizado; o denominador conta apenas
questões conhecidas. Empates de data preservam a ordem da API. Não se presume
que existam cinco questões. “Ver todas” abre a fila existente, que permite buscar
o código da prova.

Loading, sucesso, fila vazia e falha de carregamento possuem apresentações
próprias. Os atalhos continuam acessíveis durante a carga. Dados pessoais e
conteúdo matemático não são escritos no armazenamento do navegador pela Home.
A validação visual usa uma prévia local isolada com fixtures sintéticas, sem
inserir exemplos na aplicação ou nos dados reais.

### CONFIA-TME-HOME-02 — refinamento visual

Refinamento da composição existente com base nas referências mobile e desktop:

- Mobile até 767 px: header de 82 px, CTA de 118 px, atalhos de aproximadamente
  154–162 px, quatro métricas na mesma linha, três linhas de fila de 82 px,
  dois progressos lado a lado de 112 px e bottom navigation de 74 px + safe area.
- Tablet entre 768 e 1099 px: composição intermediária com hero/CTA lado a lado
  e área operacional adaptada à largura disponível.
- Desktop a partir de 1100 px: container de até 1280 px, hero em 46/36/18,
  atalhos horizontais de 94 px, métricas horizontais de 96 px e painéis inferiores
  em 60/40. Os três casos e os dois progressos cabem juntos em 1440×900.
- SVG decorativo local com curvas verde/amarela/vermelha, superfície azul clara,
  documento reto e check verde. É `aria-hidden`, sem interação e sem downloads.
- Ícones outline consistentes, acentos azul/verde/amarelo, círculos tonais,
  divisórias leves, foco visível, transições de 160 ms e suporte a reduced motion.

Apenas a composição visual mudou. Métricas, seleção da próxima correção,
agrupamento de provas, fontes de dados e APIs permanecem iguais ao HOME-01.
Os números, status e totais ilustrativos das referências não são copiados.

## CONFIA-TME-HOME-03 — resumo operacional vigente

Esta seção substitui os limites de dados descritos em HOME-01. O layout,
stylesheet, ilustração e shell aprovados em HOME-02 foram preservados.

### Contrato e escopo

`GET /tme/home-summary?period=today` usa `require_tme_evaluator`, filtra pelo
criador do `CorrectionCase` e responde com `Cache-Control: no-store`:

- `period`: `today` (padrão), `7d`, `30d` ou `all`;
- `counts`: `pending`, `inconclusive`, `finalized`, `in_progress`;
- `priority_cases`: até **3** itens com apenas `case_id`, `exam_code`,
  `problem_id`, `question_label`, `source_mode`, `operational_status`, `updated_at`;
- `exam_progress`: até **2** provas com `exam_code`, `completed_items`,
  `known_items`, `percent`, `latest_update`;
- `generated_at`: instante UTC da consulta.

A Home faz uma chamada ao resumo, além da identificação de sessão existente.
Não busca `/tme/cases` nem faz requests individuais. Ao abrir uma correção,
a tela correspondente mantém suas verificações de acesso e integridade.
Não há conteúdo de solução, transcrição, imagem, resultado completo, artefatos,
saída Lean ou hashes na resposta do resumo.

### Estados e fontes exatos

As quatro métricas são mutuamente exclusivas e contam **casos**, não execuções:

| Métrica | Regra, em ordem de precedência | Fonte |
| --- | --- | --- |
| Finalizada | Decisão TME persistida, ou `CorrectionCase.status == DECIDED` | `EvaluatorDecision` / `CorrectionCase` |
| Inconclusiva | Sem decisão final; último AuditRun concluído da transcrição/revisão vigente está `COMPLETED` e tem `result.score is None` **ou** `result.verdict == "inconclusivo"` | Regra de apresentação já existente do relatório ConfIA |
| Em andamento | Sem decisão final nem análise vigente inconclusiva; caso possui fonte vinculada (`SOURCE_READY`) | `CorrectionCase.submission_id` / `Submission` |
| Pendente | Caso identificado, ainda sem fonte vinculada | `CorrectionCase` |

**Em andamento conserva a semântica de HOME-01/02:** o fluxo foi iniciado com
uma fonte enviada; não afirma que um worker esteja executando naquele instante.
`RecognitionRun` persiste `FAILED` ou `NEEDS_REVIEW`; `AuditRun` persiste `FAILED`
ou `COMPLETED`. Os indicadores transitórios “Reconhecendo”/“Analisando” da tela
de correção são locais ao browser, sem estado durável de execução para a Home.
Uma falha técnica isolada permanece em andamento, sem virar inconclusiva.
Se há uma análise concluída vigente anterior, uma tentativa técnica falha não
invalida esse resultado, seguindo `runFor` do workspace existente.
Uma análise numérica, inclusive **nota zero**, permanece em andamento até decisão.
**Inconclusiva não significa resposta errada.** Não há cálculo novo de nota.

A projeção acompanha o RecognitionRun mais recente e a transcrição mais recente
por `TranscriptionRecord.created_at`, usando sua última revisão. Uma revisão
nova ou nova transcrição descarta o indicador da análise anterior. Somente
análises dessa transcrição/revisão podem compor a métrica. Entre elas vale a
última concluída por `AuditRun.created_at`, com a mesma preferência por
`COMPLETED` de `runFor`; na ausência de concluída, considera a última falha
sem atribuir veredito a ela. Uma execução antiga recebida tardiamente não
substitui uma conclusão mais recente. IDs fornecem desempate determinístico de datas iguais.
Aceitar novamente uma revisão histórica não a torna vigente. Nenhum histórico
é regravado. A decisão final prevalece sobre reconhecimento e análise.

`TeacherDecision` pertence aos Assessments escolares e não entra no resumo
TME. Seus estados `DRAFT`, `FINALIZED` e `RELEASED` e suas regras permanecem
inalterados. A finalização TME vem exclusivamente do seu próprio envelope.

### Período, progresso e próxima correção

O período filtra **a criação dos casos da Visão geral**, mantendo a semântica
anterior: mostra seu estado atual, não a quantidade de decisões tomadas no dia.
Hoje começa à meia-noite em `America/Fortaleza`; 7 e 30 dias incluem o dia atual
e os 6 ou 29 dias anteriores, respectivamente. O corte superior é o instante
da consulta. O fuso é explícito e não depende do SO do servidor ou do navegador.
Todas as quatro opções do seletor consultam o servidor e funcionam.

Fila e progresso consideram todo o histórico autorizado, independentemente do
período da Visão geral, para não esconder correções antigas ainda pendentes.
O progresso agrupa o código pseudônimo exato (`external_candidate_ref`) e conta
`problem_id` distintos. No reenvio, usa o caso criado mais recentemente da mesma
questão, com desempate por ID. Numerador: questões cujo caso escolhido está
finalizado. Denominador: **questões conhecidas**. Percentual: `100 × concluídas /
conhecidas`, arredondado a duas casas. Não foi criada configuração de cinco itens
porque o contexto atual não fornece um total esperado confiável.
`latest_update` é a maior atualização dos casos vigentes dessa prova. A Home
mostra as duas provas mais recentemente atualizadas, com desempate pelo código.

Foi preservada a prioridade explícita de HOME-01/02: excluir finalizados,
priorizar casos com fonte vinculada, depois ordenar por criação decrescente;
`case_id` desempata. Não há ordem aleatória nem reserva concorrente de trabalho.
**Corrigir próxima** abre `priority_cases[0]`; não foi necessário criar outra
rota `/cases/next`. O badge da fila indica a quantidade exibida (até três).
“Ver fila completa” / “Ver todas” abrem a fila existente.

### Projeção, desempenho e recuperação

Não existia índice operacional nos stores filesystem. O novo arquivo derivado
`CONFIA_TME_CASES_DIR/.home-summary.json` mantém metadados compactos por caso:
identificação, vínculo, datas, estado final e somente referências/estados do
último reconhecimento, transcrição/revisão e análise relevante. Não contém
texto ou artefatos; não é fonte de autorização, integridade ou pontuação.

A publicação de caso, vínculo e decisão atualiza a projeção. Pequenos hooks
após a publicação nos stores compartilhados acompanham transcrição, revisão,
aceite, reconhecimento e auditoria **somente se `tme_case_id` estiver presente**.
Eles usam modelos já disponíveis em memória, sem listar auditorias por caso.
Isso cobre também operações autorizadas feitas pelas rotas compartilhadas.
Não modificam os modelos imutáveis, OCR/providers, matemática, score ou GOV-01.

Na consulta: uma leitura JSON do índice, agregação em memória, zero consultas
por caso e resposta limitada a três correções e duas provas. Espaço do índice
é O(C), independente do número de revisões/runs históricos; agregação é O(C)
com ordenação O(C log C), e a publicação regrava atomicamente O(C) metadados.
C é o número total de casos armazenados. O desenho elimina N+1 e tráfego pesado;
não promete custo constante nem resolve a paginação da tela Fila existente.
Os testes de 5.000 e 25.000 casos verificam uma leitura de arquivo, nenhuma chamada aos
serviços de domínio e resposta abaixo de 2 KB.

Escritas usam lock entre processos, arquivo temporário privado, fsync e rename
atômico. Um marcador de projeção incompleta impede publicar indicadores antigos
quando a atualização falha. A publicação principal continua com seu resultado
original; a Home retorna 503 até reconstrução. A projeção é reconstruível.

No startup, os casos existentes são migrados/revalidados **fora do GET da Home**:
leitura dos stores e uma única varredura do diretório de auditorias, sem executar
novamente OCR ou Lean. Essa reconstrução lê/valida históricos e artefatos pelos
serviços existentes; o custo de inicialização depende do volume histórico.
Os arquivos históricos permanecem intactos. Uma atualização concorrente impede
sobrescrever o índice com uma reconstrução antiga; o startup tenta novamente.

Recuperação manual, usando o mesmo ambiente/diretórios da aplicação e
preferencialmente sem operações de escrita concorrentes:

```bash
PYTHONPATH=app .venv/bin/python -m confia_lean_auditor.tme.home_summary
```

Reiniciar também reconstrói o índice. Alterações externas aos stores exigem
reconstrução. Não há fallback da Home para leitura de resultados completos.
Índice ausente, inválido ou incompleto produz o estado de erro:
**“Não foi possível carregar os indicadores.”**, com retry. Shell e atalhos
continuam disponíveis. Loading, zeros e lista vazia permanecem distintos.

### Validação HOME-03

- Backend: `tests/test_tme_home_summary.py` cobre zero, escopo, pendentes,
  reconhecimento/retry, inconclusiva real, nota zero, falha técnica, decisão,
  múltiplas análises/revisões/transcrições, reenvio, progresso, prioridade,
  períodos/fuso, reconstrução sem alterar históricos, concorrência, falha da
  projeção, autenticação e até 25.000 casos sem N+1.
- JavaScript: `tests/js/test_tme_home.cjs` cobre consulta única, contagens do
  servidor, ordem do CTA, labels, denominadores reais, períodos, loading,
  vazio, erro/retry e navegação existente.
- Regressão focada: TME/auth/relatório, stores de transcrição/auditoria e
  reconhecimento, workspace e fluxo de fotos. Sem mudanças no design HOME-02.
