# Benchmark de reconhecimento manuscrito — estrutura inicial

Dataset e runner independentes dos benchmarks matemáticos do repositório.
Não chama auditoria, Lean, Mathpix ou modelos externos. Não contém dados pessoais.

- `schema.py` / `sample.schema.json`: contrato de amostra e exportação JSON Schema.
- `loader.py`: valida amostras, IDs/posições únicos, caminhos internos sem symlinks,
  SHA-256 dos artefatos, estrutura PNG e CaptureDocument opcional.
- `runner.py`: replay offline de saídas segmentadas ou adapter local via registry.
- `metrics.py`: comparações literais determinísticas e componentes MMER-v0.
- `fixtures/`: cinco casos artificiais A–E, PNG branco 16×16 e snapshot sem strokes.

**Os artefatos dos fixtures são placeholders de transporte, não imagens das
fórmulas gold.** Os pares gold/recognized exercitam métricas; não medem capacidade
OCR nem acurácia em manuscritos reais. O resultado com `fake_test` é igualmente
artificial e constante. O campo `artificial` identifica dados sintéticos; qualquer
futuro dataset exigirá revisão de origem/privacidade antes de ser versionado.

Cada amostra tem ID, descrição, PNG com hash, strokes opcionais com hash, gold
segmentado e saída reconhecida opcional para replay. Segmentos têm página, ordem,
kind, texto/LaTeX e mapeamentos opcionais; valores desconhecidos permanecem `null`.
O PNG corresponde à página 0 no runner inicial (uma imagem por amostra). As posições
`(page_index, order)` são a chave de alinhamento; não há alinhamento semântico.

Execução na raiz do repositório:

```sh
.venv/bin/python -m benchmarks.handwriting_recognition.runner benchmarks/handwriting_recognition/fixtures/samples.json
CONFIA_ENV=test .venv/bin/python -m benchmarks.handwriting_recognition.runner benchmarks/handwriting_recognition/fixtures/samples.json --provider fake_test
.venv/bin/python -m pytest -q tests/test_handwriting_recognition_benchmark.py
```

O relatório JSON declara `fixture_replay` ou `adapter`, provider, amostras e métricas
individuais. Não executa outros benchmarks e não produz score global opaco.

## Métricas e denominadores

- **CER**: distância Levenshtein em caracteres / caracteres gold. Texto e LaTeX são
  comparados separadamente, preservando espaços e Unicode. Somam-se numeradores e
  denominadores por amostra. Segmentos ausentes contam deleções; extras, inserções.
  Referência vazia: zero se ambas vazias, `null` se existem inserções. CER pode > 1.
- **Exact segment match**: igualdade de kind, texto e LaTeX na mesma posição /
  segmentos gold. Confiança e metadados não entram na fidelidade textual.
- **Math symbol mismatch**: número de segmentos gold cujo fluxo de tokens matemáticos
  difere. Usa LaTeX quando disponível, senão texto math/mixed. Tokenização literal
  de comandos, caracteres/dígitos e símbolos; ignora whitespace. Não é equivalência
  algébrica, nem contagem de símbolos substituídos.
- **Critical sign mismatch (+/-)**: número de segmentos gold com sequência diferente
  de `+`, `-`, `−`, `\pm`, `\mp`. Não distingue menos unário de subtração; não detecta
  toda mudança de posição que mantenha a mesma sequência de sinais.
- **Exponent mismatch / subscript mismatch**: número de segmentos gold com diferença
  de marcador, base local e argumento de `^` / `_`. Reconhece grupos sem chaves aninhadas,
  comandos e argumentos simples. Para a notação manuscrita, dígitos contíguos sem
  chaves são um argumento: `x^57` difere de `x^5 7`. Essa convenção operacional não
  é a gramática estrita TeX; grupos aninhados e estruturas complexas ficam limitados.
- **Missing segment**: posições gold ausentes. Extras são contados separadamente.

As contagens de componentes são **por segmento**, não por ocorrência. O relatório
inclui componentes e posição de cada segmento, edições CER e denominadores.
Os componentes podem se sobrepor e não são somados como se fossem independentes.

## Mathematical Meaning Error Rate — MMER-v0 operacional

**Não há validação científica nem avaliação semântica matemática nesta etapa.**
MMER-v0 é uma aproximação estrutural transparente para iniciar investigação.
Para cada segmento gold, `mmer_flagged` é verdadeiro quando falta o segmento ou
quando existe math symbol mismatch, critical sign mismatch, exponent mismatch ou
subscript mismatch. `reference_error_rate` é a união de segmentos marcados dividida
pelo número de segmentos gold. O relatório expõe todos os componentes, numerador,
denominador e segmentos extras em separado; não oculta pesos nem combina extras
em um score arbitrário. Erros de prosa e diferenças só de espaço afetam CER/exact
match, mas não necessariamente esta aproximação matemática.

A medida pode ter falsos positivos (LaTeX equivalente) e falsos negativos
(alterações semânticas não cobertas). Mudanças de segmentação podem desalinhá-la.
Ela não determina se a matemática do aluno está correta.

Casos obrigatórios: A preserva `2 + 2 = 5`; B troca o `+ 6` por `- 6`; C separa o
expoente `57`; D perde `_n`; E omite um segmento. A tem erro zero: corrigir o
resultado matemático do aluno seria erro de reconhecimento, não melhoria.
