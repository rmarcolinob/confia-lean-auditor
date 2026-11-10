# P2-UPLOAD — upload de arquivo → GLM-OCR → resposta do aluno

Caminho paralelo à captura no tablet. Um arquivo (foto ou PDF) da folha do aluno é
transcrito pelo GLM-OCR, o enunciado impresso é removido e sobra **só a resposta do
aluno**. Opcionalmente, essa resposta segue direto para o mesmo motor do `POST /audit`
(claims → formalização → Lean → rubrica → relatório).

Não há persistência: o upload não cria `Submission`, não grava a imagem e não entra no
fluxo de revisão/aceite 03A. O único efeito em disco é o da correção, quando chamada
(`execute_audit` grava `artifacts/runs/<run_id>/`, comportamento já existente).

## Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `app/confia_lean_auditor/recognition/glm_ocr.py` | Cliente HTTP do GLM-OCR no Ollama. Único módulo que conhece a API externa |
| `app/confia_lean_auditor/uploads/__init__.py` | Descrição do pacote |
| `app/confia_lean_auditor/uploads/images.py` | Arquivo enviado → páginas PNG normalizadas (tipo pelos bytes, EXIF, redimensionamento, PDF) |
| `app/confia_lean_auditor/uploads/answer_extraction.py` | Função pura: separa enunciado impresso e resposta no texto do OCR |
| `app/confia_lean_auditor/uploads/schemas.py` | Contratos Pydantic de entrada e saída e limites de tamanho |
| `app/confia_lean_auditor/uploads/service.py` | Orquestração: valida questão e configuração, decodifica, chama o OCR com prazo, monta a resposta |
| `app/confia_lean_auditor/uploads/router.py` | Rotas FastAPI, leitura limitada do corpo, encadeamento com `execute_audit` |
| `app/confia_lean_auditor/main.py` | +2 linhas: import e `app.include_router(uploads_router)` |
| `pyproject.toml` | Extra opcional `ocr = ["pillow", "pypdfium2"]` |
| `tests/test_upload_answers.py` | 16 testes herméticos (sem Ollama, Lean nem rede) |
| `docs/P2_UPLOAD_GLM_OCR.md` | Este documento |

Dependência entre módulos (setas = "importa"):

```
router ──► service ──► images
   │          ├─────► answer_extraction
   │          ├─────► recognition/glm_ocr ──► recognition/execution (ProviderDeadline)
   │          ├─────► recognition/execution (start_provider)
   │          └─────► core.problem_assets / core.paths / core.problem_catalog
   └──(na hora da chamada)──► main.execute_audit, core.public_audit
```

`router` importa `main.execute_audit` dentro da função, não no topo do módulo: `main`
importa `router`, e o import no topo criaria um ciclo. É o mesmo padrão de
`submission_audits/router.py` (`engine()`).

## Fluxo de uma requisição

```
POST /uploads/answers  ou  POST /uploads/audits
 │
 1. router._read_json_body      Content-Type JSON, Content-Length e leitura em partes ≤ MAX_REQUEST_BYTES
 2. UploadAnswersRequest        validação Pydantic (extra="forbid")
 3. service.problem_statement   problem_id ∈ CATALOG; lê problems/<id>/problem.json → statement
 4. GlmOcrClient().base_url     sem CONFIA_GLM_OCR_URL → 503 antes de qualquer processamento
 5. service.decode_files        base64 estrito, ≤ MAX_FILE_BYTES por arquivo
 6. images.prepare_pages        tipo pelos bytes → PNG RGB, lado maior ≤ 1600 px, ≤ 3 páginas
 7. start_provider(...)         thread com prazo total; uma chamada ao Ollama por página
 8. answer_extraction           localiza o enunciado, corta, devolve resposta + texto removido
 9. UploadAnswersResponse       status NEEDS_REVIEW
 │
 └─ só em /uploads/audits:
10. execute_audit(AuditRequest(problem_id, solution=answer_text))
11. sanitize_public_payload(public_audit_data(...))   mesma projeção pública do POST /audit
```

As etapas 1 a 6 rejeitam a requisição **antes** de chamar o OCR: arquivo inválido nunca
consome tempo de GPU.

## Configuração

| Variável | Padrão | Uso |
|---|---|---|
| `CONFIA_GLM_OCR_URL` | vazia | Base do Ollama, por exemplo `http://localhost:11434`. Vazia → 503 `PROVIDER_NOT_CONFIGURED` |
| `CONFIA_GLM_OCR_MODEL` | `glm-ocr` | Nome do modelo no Ollama |
| `CONFIA_UPLOAD_OCR_TIMEOUT_SECONDS` | `300` | Prazo total do OCR, somando todas as páginas. Valor finito, positivo e ≤ `threading.TIMEOUT_MAX` |

Subida local:

```bash
ollama pull glm-ocr                  # ~2,7 GB em disco; ~3 GB de memória em uso
pip install -e '.[ocr]'
CONFIA_GLM_OCR_URL=http://localhost:11434 uvicorn confia_lean_auditor.main:app --port 8000
```

Sem o extra `ocr`, a app sobe normalmente e só estas rotas respondem 503
`OCR_DEPENDENCIES_MISSING`: Pillow e pypdfium2 são importados dentro de `images.py`.

## API

Autorização nas três rotas: `require_any_role(Role.STUDENT, Role.TEACHER)`. Com
autenticação ligada, valem também o cookie de sessão e o middleware de mesma origem
de `main.py` para métodos de escrita. Todas as respostas usam `Cache-Control: no-store`.

### `GET /uploads/status`

Não chama o provedor.

```json
{"provider": "glm_ocr", "configured": true,
 "accepted_media_types": ["image/png", "image/jpeg", "application/pdf"], "max_pages": 3}
```

### `POST /uploads/answers`

Entrada (`Content-Type: application/json`):

```json
{"problem_id": "ITA2025F2Q1",
 "files": [{"filename": "folha.jpg", "data_base64": "<bytes do arquivo em base64>"}]}
```

| Campo | Regra |
|---|---|
| `problem_id` | `Identifier` do projeto; precisa estar em `core.problem_catalog.CATALOG` |
| `files` | 1 a 3 itens, na ordem das páginas |
| `files[].filename` | opcional, ≤ 200 caracteres; só é ecoado na resposta |
| `files[].data_base64` | base64 estrito; arquivo decodificado ≤ 15 MiB; PNG, JPEG ou PDF |

O tipo é detectado pela assinatura dos bytes (`\x89PNG`, `\xff\xd8\xff`, `%PDF-`);
nome e tipo declarados pelo cliente são ignorados. Todas as páginas de todos os arquivos
somam no máximo 3.

Saída `200` (`UploadAnswersResponse`):

```json
{
  "upload_id": "upl_<32 hex>",
  "problem_id": "ITA2025F2Q1",
  "status": "NEEDS_REVIEW",
  "answer_text": "Como x^2 - x + 1 = 0, temos x^2 = x - 1.\nLogo x^3 = -1 e x^6 = 1.\n…",
  "statement_found": true,
  "statement_match": 1.0,
  "pages": [{
    "page_index": 0, "source_file_index": 0, "source_filename": "folha.jpg",
    "source_media_type": "image/jpeg", "page_in_source": 0,
    "sha256": "<SHA-256 do PNG enviado ao OCR>", "width": 1131, "height": 1600,
    "latency_ms": 40210.5, "truncated": false, "answer_text": "…"
  }],
  "removed": [
    {"kind": "before_statement", "page_index": 0, "text": "ITA 2025 — 2ª fase — Matemática\nQuestão 1"},
    {"kind": "statement", "page_index": 0, "text": "Encontre os valores reais a e b …"}
  ],
  "warnings": ["Texto de OCR: o GLM-OCR pode trocar dígitos ou omitir trechos …"],
  "provider": "glm_ocr",
  "adapter": "confia_glm_ocr_ollama",
  "adapter_version": "1.0.0",
  "parameters": {"model": "glm-ocr", "prompt": "Text Recognition:", "temperature": 0,
                 "max_output_tokens": 4096, "max_side_px": 1600},
  "created_at": "2026-11-06T…Z"
}
```

| Campo | Significado |
|---|---|
| `upload_id` | `upl_` + 32 primeiros hex de `sha256(problem_id + ":" + sha256 de cada PNG)`. Determinístico: o mesmo arquivo para a mesma questão gera o mesmo id. Não é chave de armazenamento, porque nada é salvo |
| `status` | Sempre `NEEDS_REVIEW`: texto de OCR não conferido |
| `answer_text` | Só a resposta. É o valor a enviar como `solution` em `POST /audit` |
| `statement_found` / `statement_match` | Se o enunciado foi localizado e a semelhança da melhor janela (0 a 1) |
| `pages[].answer_text` | A parte da resposta em cada página |
| `pages[].truncated` | O OCR atingiu o limite de saída; em geral, laço de repetição |
| `removed` | Texto cortado, por página: `before_statement` (cabeçalho, nome, instruções) e `statement` |
| `warnings` | Ver "Avisos" |
| `parameters` | Parâmetros públicos do OCR, para rastreabilidade. Nunca incluem credenciais |

### `POST /uploads/audits`

Mesma entrada. Saída `200`:

```json
{
  "ocr": { …UploadAnswersResponse… },
  "audit": { …mesmo payload público do POST /audit… } | null,
  "audit_error": null | {"status": 501, "error_code": "AUDIT_OPERATION_UNAVAILABLE", "detail": "…"},
  "warnings": ["AUTOMATIC_AUDIT_OF_UNREVIEWED_OCR: …"]
}
```

- Se o OCR falhar, a rota responde com o erro do OCR (tabela abaixo), igual a `/uploads/answers`.
- Se o OCR der certo e a correção falhar, a resposta continua `200`: `ocr` preenchido,
  `audit: null` e o motivo em `audit_error`. O OCR leva minutos e não é descartado.
- `answer_text` vazio: o motor não é chamado; `audit_error.error_code = "EMPTY_ANSWER"` (status 422 dentro do objeto).
- `audit_error` vem de `core.public_audit.audit_exception_response`: os mesmos códigos fixos
  do `/audit`, sem texto de exceção.
- O motor roda no threadpool do Starlette (`run_in_threadpool`), de forma síncrona.

### Erros (`/uploads/answers` e etapa de OCR do `/uploads/audits`)

Formato: `{"detail": "<CÓDIGO>"}`. O corpo da requisição nunca é ecoado, porque contém a
imagem do aluno.

| HTTP | `detail` | Causa |
|---|---|---|
| 400 | `Content-Length inválido.` | Cabeçalho não numérico |
| 413 | `Payload acima do limite permitido.` | Corpo > `MAX_REQUEST_BYTES` (~60 MiB) |
| 413 | `FILE_TOO_LARGE` | Arquivo decodificado > 15 MiB |
| 415 | `Use application/json.` | `Content-Type` diferente de JSON |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | Arquivo não é PNG, JPEG nem PDF |
| 422 | `INVALID_REQUEST` | JSON fora do schema |
| 422 | `UNKNOWN_PROBLEM` | `problem_id` fora do catálogo ou `problem.json` inválido |
| 422 | `INVALID_BASE64` | base64 inválido |
| 422 | `INVALID_UPLOAD:<motivo>` | `empty_file`, `too_many_pages`, `invalid_image`, `image_too_large`, `invalid_pdf`, `empty_pdf` |
| 502 | `PROVIDER_FAILED` | Falha do Ollama: HTTP 4xx/5xx, rede, JSON inválido ou resposta > 1 MiB |
| 503 | `PROVIDER_NOT_CONFIGURED` | `CONFIA_GLM_OCR_URL` vazia |
| 503 | `OCR_DEPENDENCIES_MISSING` | Pillow ou pypdfium2 não instalados |
| 503 | `PROVIDER_BUSY` | Os 4 slots de provedor do processo estão ocupados |
| 504 | `PROVIDER_TIMEOUT` | Prazo total excedido |

Ordem de validação: questão → configuração → base64 → arquivos → OCR. Um
`problem_id` inválido responde 422 mesmo com o OCR desconfigurado.

### Avisos (`warnings`)

| Prefixo | Quando |
|---|---|
| `STATEMENT_NOT_FOUND` | Enunciado não localizado; `answer_text` é o texto inteiro |
| `CONTENT_BEFORE_STATEMENT` | Há contas (dígito seguido de `=`, `+` ou `-`) no texto antes do enunciado, provável anotação de margem. Confira `removed` |
| `EMPTY_ANSWER` | Nada depois do enunciado |
| `OCR_TRUNCATED` | Alguma página atingiu o limite de saída |
| `Texto de OCR: …` | Sempre presente: o GLM-OCR pode trocar dígitos sem sinal de dúvida |
| `AUTOMATIC_AUDIT_OF_UNREVIEWED_OCR` | Só em `/uploads/audits`: correção feita sobre texto não conferido |

## Componentes em detalhe

### `recognition/glm_ocr.py`

`GlmOcrClient.transcribe(image_png: bytes, deadline: ProviderDeadline | None) -> GlmOcrPage`

Requisição `POST {base_url}/api/generate`:

```json
{"model": "glm-ocr", "prompt": "Text Recognition:", "images": ["<PNG em base64>"],
 "stream": false, "options": {"temperature": 0, "num_ctx": 16384, "num_predict": 4096}}
```

- `Text Recognition:` é o prompt oficial do GLM-OCR para texto de página. A saída vem em
  Markdown, com LaTeX inline `$…$`, e tabelas em Markdown.
- Timeouts `httpx`: total = tempo restante do `deadline`; conexão ≤ 5 s; escrita ≤ 30 s.
  O prazo é verificado de novo a cada bloco lido da resposta.
- `trust_env=False`: ignora proxies do ambiente, como o adaptador do Mathpix.
- Resposta limitada a 1 MiB, lida em streaming.
- `GlmOcrPage`: `text` (sem espaços nas bordas), `latency_ms`, `output_tokens`
  (`eval_count` do Ollama) e `truncated` (`done_reason == "length"` ou tokens ≥ 4096).
- Falhas viram `GlmOcrError` com categoria fixa (`http_4xx`, `http_5xx`, `transport_error`,
  `invalid_json`, `incomplete_response`, `response_too_large`) ou `TimeoutError`. Nunca
  carregam corpo HTTP.
- Log `glm_ocr_page`: provedor, status, código HTTP, categoria e duração. Nenhum conteúdo do aluno.
- `transport` injetável (`httpx.MockTransport` nos testes).

### `uploads/images.py`

`prepare_pages(files: list[bytes]) -> list[PreparedPage]`

- `PreparedPage`: `source_index`, `source_media_type`, `page_in_source`, `png`, `width`, `height`.
- Imagem: `Image.verify()` numa primeira abertura e decodificação numa segunda (o `verify`
  invalida o objeto); `ImageOps.exif_transpose` corrige a rotação de fotos de celular;
  conversão para RGB; `thumbnail` com LANCZOS até o lado maior ter `MAX_SIDE = 1600` px;
  PNG com `optimize=True`. Imagens menores não são ampliadas.
- PDF: `pypdfium2`, escala `1600 / max(largura_pt, altura_pt)` por página, depois o mesmo
  `_to_png`. O número de páginas é checado contra o orçamento restante antes de renderizar.
- `Image.MAX_IMAGE_PIXELS = 50_000_000`. O Pillow só **lança** `DecompressionBombError`
  acima do dobro desse valor (100 MP); entre 50 e 100 MP ele emite um aviso e decodifica.
- 1600 px é o tamanho validado nos testes com provas reais: o GLM-OCR leu bem e manteve
  latência de 40 a 80 s por página num M1 com 8 GB.

### `uploads/answer_extraction.py`

`extract_answer(page_texts: list[str], statement: str, threshold=0.75) -> AnswerExtraction`

Função pura, sem I/O. Algoritmo:

1. Cada página vira uma lista de linhas não vazias.
2. `match_key()` normaliza para comparação: remove comandos LaTeX comuns (`\frac`,
   `\sqrt`, `\cdot`, `\times`, `\left`, `\right`, `\mathrm`, `\text`, `\mathbb`), passa
   para minúsculas, remove acentos e mantém só `[a-z0-9]`. Assim
   `$p(x)=x^{57}+a x^{14}$` e `p(x) = x^57 + a x^14` geram a mesma chave.
3. `_best_window()` testa toda janela de linhas consecutivas (até 30 linhas, parando
   quando a janela passa de `2·len(enunciado) + 40` caracteres) em todas as páginas e
   calcula `difflib.SequenceMatcher(None, enunciado, janela, autojunk=False).ratio()`.
   `real_quick_ratio` e `quick_ratio` descartam cedo as janelas que não podem superar a melhor.
4. Melhor janela com semelhança ≥ 0,75:
   - páginas anteriores e linhas antes da janela → `removed`, `before_statement`;
   - a janela → `removed`, `statement`;
   - linhas depois da janela e páginas seguintes → resposta.
5. Semelhança < 0,75 → texto inteiro como resposta e `STATEMENT_NOT_FOUND`.
6. `answer_text` = respostas das páginas unidas por linha em branco. Linhas vazias
   internas são descartadas no passo 1.

Por que o enunciado e não marcadores `a)`, `b)`: as questões ITA do catálogo têm
enunciado único, sem itens. Nos testes com a OBMEP, a busca pelo texto da pergunta achou
todos os itens, inclusive numa página em que o scan cortou os marcadores.

### `uploads/service.py`

`recognize_upload(request, client=None) -> UploadAnswersResponse`

- `client` injetável. Nos testes, `service.GlmOcrClient` é substituído por um falso.
- OCR dentro de `recognition.execution.start_provider`, o mesmo mecanismo das demais
  chamadas de reconhecimento: uma thread daemon e um semáforo de **4 slots por processo**,
  compartilhado com `/submissions/{id}/recognitions`. Prazo total em `ProviderDeadline`.
- Como no restante do módulo `recognition`, o timeout **não cancela** a thread: ela segue
  até o Ollama responder e só então libera o slot.
- O Ollama processa por padrão uma requisição por vez (`OLLAMA_NUM_PARALLEL`); envios
  simultâneos ficam em fila no próprio Ollama, dentro do prazo de cada requisição.
- `UploadError(code, status)` carrega só código fixo e status HTTP.

### `uploads/router.py`

- `_read_json_body`: mesmo padrão de `POST /submissions`, com checagem de `Content-Type`,
  `Content-Length` e leitura em partes contra `MAX_REQUEST_BYTES`.
- Erros de validação Pydantic viram `INVALID_REQUEST` sem detalhes, para não ecoar o corpo.
- `_audit`: importa `execute_audit` na chamada; se o `answer_text` vier vazio, não chama o
  motor; converte qualquer exceção com `audit_exception_response` e lê o `JSONResponse`
  para devolver `status`, `error_code` e `detail`.

### `uploads/schemas.py`

- `MAX_FILE_BYTES = 15 MiB`, `MAX_FILES = 3`; `MAX_FILE_BASE64` é o tamanho em base64
  correspondente; `MAX_REQUEST_BYTES = 3 · MAX_FILE_BASE64 + 64 KiB`.
- `extra="forbid"` em todos os modelos, como em `submissions.schemas`.
- `Union[...]` em vez de `X | Y`: o projeto declara `requires-python >= 3.9`.

## Testes (`tests/test_upload_answers.py`)

```bash
pip install -e '.[ocr]'
pytest tests/test_upload_answers.py
```

| Teste | O que garante |
|---|---|
| `test_statement_and_header_are_removed_and_kept_for_review` | Enunciado em LaTeX localizado; cabeçalho e enunciado vão para `removed` |
| `test_missing_statement_returns_everything_with_warning` | Sem enunciado, nada é cortado e há `STATEMENT_NOT_FOUND` |
| `test_answer_continues_on_following_pages` | A resposta continua nas páginas seguintes |
| `test_upload_png_returns_only_student_answer` | Rota completa com PNG; o OCR recebe PNG |
| `test_large_photo_is_reduced_before_ocr` | 4000×3000 vira lado maior 1600 |
| `test_pdf_pages_are_rendered_in_order` | PDF de 2 páginas, na ordem |
| `test_invalid_uploads_are_rejected_before_ocr` | GIF (415), questão inexistente, PDF com 4 páginas e base64 inválido (422), sem chamar o OCR |
| `test_not_configured_is_503` | Sem `CONFIA_GLM_OCR_URL` |
| `test_status_reports_configuration` | `GET /uploads/status` |
| `test_audit_route_sends_answer_to_the_existing_engine` | `/uploads/audits` chama `execute_audit` com `solution = answer_text`; falha do motor vira `audit_error` |
| `test_audit_route_skips_engine_when_answer_is_empty` | Resposta vazia não chama o motor |
| `test_glm_client_calls_ollama_with_official_prompt` | Corpo da requisição ao Ollama |
| `test_glm_client_flags_truncation_and_hides_http_errors` | `truncated` e erro HTTP sem vazar o corpo |

A suíte completa do projeto tinha 91 falhas antes desta mudança, todas por falta de
`lake` (Lean) e `node` no ambiente; continua com as mesmas 91.

## Execução real verificada (Mac M1, 8 GB, Ollama local)

| Entrada | Resultado |
|---|---|
| Folha manuscrita real da OBMEP enviada como `ITA2025F2Q1` | 77 s; manuscrito lido; `STATEMENT_NOT_FOUND`, correto porque é outra questão |
| Página com o enunciado real de `ITA2025F2Q1` e a resolução em fonte cursiva | 41 a 47 s; `statement_match = 1.0`; cabeçalho e enunciado em `removed`; resposta sem erros de leitura |
| A mesma página em `/uploads/audits` | 4 claims extraídas (`power_reductions`, `reduced_polynomial_form`, `coefficient_system`, `final_answer`); Lean `lean_error` por falta do binário; veredito `inconclusivo` |

A segunda página é sintética (texto em fonte cursiva), não manuscrito real.

## Limitações e próximos passos

- **Chamada síncrona e longa.** 40 a 80 s por página, até ~4 min com 3 páginas. Atrás de
  um proxy com timeout curto, a requisição é cortada. Para produção: job assíncrono
  (`POST` devolve um id, `GET` consulta o resultado).
- **Sem persistência.** O resultado se perde se o cliente cair, e não entra no fluxo
  03A (revisão, conferência e aceite) nem na ponte `POST /submissions/{id}/audits`. Para
  isso, o upload precisaria virar uma `Submission` com `source: "upload"`, o que muda
  contratos de `submissions.schemas` e seus testes.
- **Uma questão por envio.** Texto de outra questão depois da resposta entra em `answer_text`.
- **Só questões cadastradas.** O corte depende de `problems/<id>/problem.json`. Itens
  a/b/c, como na OBMEP, precisariam de âncoras por item.
- **Correção sem conferência em `/uploads/audits`.** O GLM-OCR já leu `2⁵ = 32` como
  `2³ = 32` e `z = y + 21` como `z = y + 27` sem sinal de dúvida.
- **Extratores de claims por regras.** Uma resolução com notação diferente da esperada
  (por exemplo, `w` em vez de `x` em `ITA2025F2Q1`) gera zero claims com o OCR correto.
- **Lean.** Sem `lake build`, toda correção termina `inconclusivo`.
- **Ollama sem autenticação.** Manter em `localhost` ou atrás de rede privada; nunca exposto.
