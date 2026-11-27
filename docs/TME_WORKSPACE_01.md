# CONFIA-TME-WORKSPACE-01

## Arquitetura

O workspace continua no shell `/tme`, no fluxo de `CorrectionCase`. A Home, a fila e “Corrigir próxima” chamam o mesmo `openCase`. O link `/tme?case_id=…` abre diretamente o caso; o botão Voltar retorna à fila. Nenhuma rota de API foi criada.

| Camada | Implementação |
| --- | --- |
| Tema compartilhado | `static/tme/tme-theme.css`: tokens `--confia-*` extraídos literalmente da Home; aliases semânticos `--status-*` |
| Contexto e questões | `correction-workspace.js`: `CorrectionHeader`, `QuestionNavigator`, `ProblemStatement` |
| Original | `layoutOriginal` e `attachPan`, com as páginas preservadas, zoom, rotação e paginação |
| Solução e estado | `tme.js`: abas Original/Transcrição/Comparar, cache por caso, revisão e ações existentes |
| Análise | `workspace-report.js`: sugestão, cobertura, critérios, claims, evidências, verificação e detalhes técnicos |
| Decisão | `decisionPanel`, `ensureAcceptance`, `nextCorrection` e barra contextual em `tme.js` |
| Splitter | `workspace-controls.js`: ponteiro, teclado, reset e preferência em localStorage |
| Layout | `correction-workspace.css`: estilos restritos a `data-view="workspace"` |

Os rascunhos, a aba, a página, o zoom, a rotação e a expansão dos critérios ficam no cache da sessão por caso. Somente a preferência de divisão dos painéis é persistida em localStorage. Não se gravam soluções ou notas no armazenamento local.

## Contratos reutilizados

Todos os caminhos abaixo mantêm a autorização TME existente.

| Dados / ação | Endpoint existente |
| --- | --- |
| Caso e questões da mesma prova | `GET /tme/cases/{case_id}`, `GET /tme/cases` |
| Enunciado | `GET /tme/problems` |
| Submission e referências das páginas | `GET /tme/cases/{case_id}/submission` |
| Foto/scan original e fallback normalizado | `GET /tme/cases/{case_id}/originals/{page_index}`, `GET /tme/cases/{case_id}/pages/{page_index}` |
| Escrita digital preservada | `GET /tme/cases/{case_id}/pages/{page_index}` |
| TranscriptionRevision e histórico | `GET /tme/cases/{case_id}/transcriptions`, `GET /tme/cases/{case_id}/transcriptions/{transcription_id}` |
| Reconhecimento e retorno operacional | `POST /tme/cases/{case_id}/recognize`, `GET /tme/cases/{case_id}/recognition-status` |
| Nova revisão excepcional | `POST /tme/cases/{case_id}/transcriptions/{transcription_id}/revisions` |
| Vinculação à revisão exata | `POST /tme/cases/{case_id}/transcriptions/{transcription_id}/accept` |
| AuditRun | `GET/POST /tme/cases/{case_id}/audits` |
| Decisão TME | `GET/POST /tme/cases/{case_id}/decision` |
| Próxima correção | `GET /tme/home-summary?period=all` |

RecognitionRun permanece no fluxo existente; a interface consome seu status seguro e a provenance da transcrição. Não é necessário carregar outra cópia completa do RecognitionRun para renderizar a tela. Detalhes técnicos preservam as informações disponibilizadas pelos contratos, com a filtragem pública existente.

A escrita digital usa a imagem já renderizada dos strokes e preservada na Submission. O contrato TME de leitura atual não fornece o snapshot vetorial; não se recriam strokes nem se usa a API escolar para contornar esse limite.

## Fluxo e apresentação

- Mobile: contexto compacto, questões reais, etapas informativas, enunciado de duas linhas expansível, solução e análise empilhadas. Comparar permanece vertical. Bottom navigation e ação contextual têm áreas separadas, incluindo safe area.
- Tablet (768–1099): análise abaixo da solução, navegação superior, ação no rodapé.
- Desktop (≥1100): solução/análise em 60/40, com rolagem independente e decisão sticky. O splitter permite solução entre 45% e 70% do espaço útil dos painéis, garantindo análise ≥30%; Home/End e setas são suportados.
- As questões são agrupadas pelo código pseudônimo da prova e família do problem_id. Só existem botões para casos reais, sem fabricar Q1…Q5. Casos ainda não carregados são “Disponível”; não se infere status de análise.
- A transcrição usa o renderer matemático existente. Editar publica nova revisão; não altera a anterior. Abas e controles do original não fazem novas requisições de transcrição, análise ou imagem.
- Pontuação nula continua “Pontuação não determinada”; zero válido permanece zero. Critérios e claims mantêm seus estados reais. Falha técnica usa cinza/azul, sem representar refutação matemática.
- Cobertura não é confiança estatística. Só há rótulo de claim formalmente verificado com execução compilada e artefato registrado. A verificação de claims parciais não é apresentada como prova da solução completa.
- Evidências vêm dos campos reais do retorno. Sem evidência, a interface informa isso. O callback de seleção mantém `mapping: null` quando não existem offsets confiáveis; não inventa highlights.

## Decisão e continuidade

A decisão humana permanece disponível com sugestão nula. “Usar sugestão” preenche a pontuação; “Ajustar” revela os campos e leva o foco à nota. A justificativa de divergência segue a elegibilidade já definida por `audit_snapshot`, inclusive suas exceções para falhas técnicas; o backend permanece autoridade final da validação.

A vinculação automática à revisão exata reutiliza o recibo existente, sempre com `reviewer_identity_verified: false`. Não existe gate de conferência humana obrigatório. A decisão é enviada pelo endpoint TME já existente, sem alterar `TeacherDecision` escolar, GOV-01, score policy ou lifecycle.

Após registrar, a tela mostra “Correção registrada”, “Corrigir próxima” e “Voltar para fila”. A próxima correção é escolhida pela ordem do agregado do servidor. Uma fila vazia retorna à fila com mensagem explícita.

## Validação

- JS: `node --test tests/js/test_*.cjs`: **392 aprovados, 0 falhas, 0 ignorados**, incluindo 17 testes específicos novos.
- Python rápido: `.venv/bin/python -m pytest -q tests/test_tme_home_summary.py tests/test_tme_demo_auth.py tests/test_tme_audit_view.py tests/test_tme_pilot.py tests/test_tme_photo_errors.py`: **70 aprovados, 0 falhas**.
- Testes novos em `tests/js/test_tme_workspace_01.cjs`; testes anteriores mantidos e adaptados aos rótulos, tokens extraídos e novos limites do splitter.
- Screenshots de dados reais e fixtures isoladas: `/private/tmp/confia-workspace01/`. Fixtures de decisão existem apenas no servidor temporário de QA, sem gravar notas nos casos reais.
- Matriz: 390×844, 393×852, 430×932, 768×1024 e 1440×900.
- O ambiente valida Chromium. Safari iOS, teclado virtual e safe area física precisam de validação em aparelho; não são declarados certificados aqui.

Nenhum motor matemático, extractor, rubrica, Lean, Mathlib, OCR/HMER, Mathpix, modelo ou endpoint Python foi alterado nesta tarefa.
