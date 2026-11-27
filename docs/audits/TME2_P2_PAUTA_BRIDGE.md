# TME² P2 — pauta, texto e diagrama estruturado

## Escopo e estado inicial

Implementação opt-in de `TME2026P2`, com pauta de 20 pontos (A=5, B=7, C=8), no registry existente. Base: `f22b18e9cbf0542e8a5d52c34c83e799a939dc38`, branch `feat/tme-dual-input`. O diretório já continha trabalho não commitado de P4/P5; o snapshot `baseline.json`, `preexisting.diff` e as cópias `baseline_sources/` distinguem esse trabalho das alterações incrementais de P2. Nenhum staging, commit, push ou reversão foi realizado.

O identificador efetivo de P1 no repositório continua sendo `TME2_P1_PILOT`; não foi renomeado para `TME2026P1`. P2 é a quinta entrada do registry. Não houve alteração do PautaEngine, do fluxo ITA, de frontend, HMER global ou secondary adjudicator. Nenhuma chamada externa, OCR, OpenAI ou benchmark de dataset foi executado.

## Arquitetura e entrada

Fluxo reutilizado: `MathClaimRecord → FactResult → PautaEvidence → PautaEngine`. O producer/checker não atribui pontos. A configuração versionada `examples/pautas/tme2_problem2.v1.json` determina critérios, máximos e métodos alternativos. A ponte apenas valida e converte fatos.

Componentes principais:

- `student_claims/tme2_p2_digital.py`: `split_p2_input`, `collect_tme2_p2_text`, `extract_p2_quantities`.
- `tme/p2_diagram.py`: tipos estruturados, `inspect_diagram`, `diagram_record`, `admissible_cases`, `feasible_pairs` e interface upstream de imagem.
- `lean/student_claim_checkers/tme2_p2.py`: `P2Checks` e `verify_tme2_p2`, sem pontuação.
- `rubric/pauta/tme2_p2.py`: mapa de 23 obrigações, allowlist diagramática e orquestração.
- `core/math_canonical/combinatorial.py`: gramática limitada de fatoriais e produtos, reutilizando a canonicalização matemática existente.

Exemplo executável, sem Lean e sem reconhecimento de imagem implícito:

```python
from confia_lean_auditor.tme.registry import audit_tme
bridge, assessment = audit_tme(
    problem_id="TME2026P2",
    solution={"a": {"text": "", "diagrams": [{
        "state": {"center": 5, "positions": {
            "A": 1, "B": 2, "C": 3, "D": 4,
            "E": 9, "F": 8, "G": 7, "H": 6}},
        "source": {"source_ref": "reviewed-transcription:example",
                   "confirmed": True, "origin": "student"}
    }]}},
    solution_id="example", use_lean=False,
)
# Item a: 5/5; itens b/c sem evidência não recebem pontos.
```

Itens aceitam texto ou `{text, diagrams}`; no máximo oito diagramas por item. A entrada não interpreta coordenadas OCR. Campos desconhecidos, posições fora de A–H, bools/strings/floats como números do diagrama são rejeitados. Centro/posições ausentes permanecem desconhecidos, sem preenchimento automático.

## Diagrama, equivalência e proveniência

`TME2P2DiagramState` representa centro e posições A–H. `inspect_diagram` calcula números usados, duplicatas, uso exato de 1–9, pares A–E/B–F/C–G/D–H e somas A–centro–E, B–centro–F, C–centro–G, D–centro–H. Verifica igualdade das quatro somas e centro exigido. Não compara com uma disposição-modelo. Há 4!·2^4=384 disposições distintas de pares para cada centro admissível; testes percorrem todas as 1152 disposições dos centros 1, 5 e 9.

`StructuredSourceBinding` é uma variante separada de `SourceBinding`: o contrato textual antigo não foi relaxado. Diagramas mantêm `source_ref`, `image_ref`, página, regiões, confiança global/por posição e origem quando disponíveis. `raw_text`, `source_start` e `source_end` são nulos: não há offsets fictícios. Payload e forma canônica devem coincidir, com SHA-256 do payload estruturado. `source_sha256` identifica o contêiner textual do bundle, **não os pixels da imagem**. A ligação gráfica adicional é dada pela referência e pelo hash do estado; isso não autentica o conteúdo de uma foto.

Atribuição exige transcrição confirmada e origem estudante. Confiança alta sozinha não autoriza crédito. Uma transcrição manual confirmada pode conservar baixa confiança do OCR original; confirmação é uma decisão explícita upstream. Origem referência ou transcrição não confirmada não gera fatos positivos atribuídos.

A ponte aceita evidência estruturada somente por verificação determinística e somente nos fatos diagramáticos explicitamente habilitados em P2. Tentativas de usar diagrama para provar contagem C5, tratá-lo como Lean/canonical equivalence ou injetá-lo na ponte P1 ficam indeterminadas. Registros textuais mantêm raw text, spans, grounding e forma canônica; a reextração do documento é validada antes dos checks.

## Pauta e semântica

### A — cinco pontos

Dois caminhos com máximo compartilhado: configuração completa válida =5; ou A1=1 (pares somam10/linhas somam15), A2=2 (quatro pares corretos), A3=2 (colocação explícita válida). O diagrama correto sem explicação basta. Texto e diagrama não somam duas vezes. A frase “Os pares são (1,9), (2,8), (3,7), (4,6).” recebe3, sem fabricar posições. Um mapeamento textual explícito completo também pode provar A3. Diagrama incompleto não vira configuração válida. Um desenho com duplicatas pode demonstrar apenas a soma dos pares, sem obter A2/A3.

### B — sete pontos

B1 reconhece `4*S=45+3*x` e o contexto combinatório de contar o centro quatro vezes. B2 reconhece a fórmula equivalente de S. B3 exige desenvolvimento: integralidade de S junto com B1/B2, ou congruência equivalente que selecione exatamente {1,5,9} no domínio1–9. Uma lista isolada não basta; uma lista com centro extra não é validada por uma implicação formal mais fraca. B4 verifica as três associações de soma. B5 exige os três casos realizáveis; aceita quatro pares de cada caso ou diagramas estruturados. Os pares construtivos não fingem ser uma colocação específica. Diagramas B isolados provam realizabilidade, não o desenvolvimento algébrico ausente.

`admissible_center` e `sum_at_five` são fatos auxiliares de controle sem pontuação própria.

### C — oito pontos

Centro9 e soma18 (juntos) =1; pares (1,8),(2,7),(3,6),(4,5) =2; distribuição24 =2; orientações16 =2; total384 =1. Caminho alternativo explícito de produto24·16,16·24 ou4!·2^4 vale os cinco pontos de contagem, sem inventar C1/C2. `384` isolado não produz uma argumentação. `total: 384` prova somente a conclusão de um ponto. Produtos sem a decomposição combinatória, como12·32, não recebem o crédito do método alternativo.

A gramática digital é deliberadamente limitada: nomes de quantidades/contextos explícitos, conjuntos, pares, mapeamentos, congruências afins e expressões fechadas de contagem. Não se afirma compreensão irrestrita de prosa. No campo combinatório, `4!=20` significa `4! = 20`, como no controle solicitado, não o operador de desigualdade de linguagens de programação. Negação, hipótese e rejeição passam pelos filtros semânticos existentes; testes confirmam ausência de claims positivos nesses contextos.

## Lean e limites de formalização

Verificações locais reais, sem mock no replay formal:

- B2: isolamento de S sobre ℝ sob a hipótese `4*S=45+3*x`, usando a expressão realmente escrita.
- B3: implicação inteira, com `1≤x≤9`, para `x=1 ∨ x=5 ∨ x=9`. Igualdade exata do conjunto e realizabilidade continuam checks separados; não confundir necessidade com existência geométrica.
- B4: as três implicações centro/soma sobre ℤ, incluindo contraexemplos de associações falsas.
- Controles de admissibilidade de um centro e soma no centro5.
- C: aritmética escrita com `Nat.factorial`, potência e produto, inclusive refutação dos valores20,8,364.

Não formalizado em Lean: reconhecimento visual, interpretação de regiões, configuração geométrica global, enumeração dos diagramas ou justificativa combinatória em linguagem natural. Estes componentes são identificados como checks determinísticos, não certificados visuais. O campo `verification_source` usa `deterministic`; o metadado `verification_kind=deterministic_diagram` distingue as configurações gráficas. Fatos aritméticos sem execução Lean usam canonical equivalence/checks determinísticos; isso não é apresentado como prova Lean.

Na primeira passagem formal, `b_wrong_association` ficou `unverified`: a alternativa de tática aceitava o primeiro refinamento com meta não resolvida, sem tentar o contraexemplo no centro5. A busca passou a exigir fechamento com `solve`; o replay final registra a refutação efetiva. Não se deduziu falsidade de simples falha de compilação. Os artifacts originais foram preservados para rastreabilidade.

## Validação

- **55/55 casos**: A=22, B=17, C=16; **23/23 obrigações** exercitadas como supported.
- **125 testes novos de P2**; **588 testes** de PautaEngine/P1/P3/P4/P5/P2 e **703 testes compartilhados** passaram: **1291 testes distintos**, zero falhas. Os 125 de P2 foram repetidos após o ajuste da tática e passaram novamente.
- **135 saídas anteriores byte a byte idênticas**: P1=20, P3=25, P4=38, P5=52. O recheck final também preservou as 55 saídas determinísticas de P2.
- **26 proposições formais distintas**: 19 verificadas e 7 refutadas no resultado final; zero unverified/technical_error. Houve 29 execuções formais no total, pois o caso com associação falsa repetiu três checks após o ajuste. O resultado inicial unverified continua preservado nos artifacts.
- **1152 configurações equivalentes** verificadas nos testes puros, além dos 55 casos ponta a ponta.
- Replay determinístico: 121 ocorrências de fatos deterministic, 72 canonical_equivalence; 165 verified, 24 refuted, 4 unverified.
- Replay formal consolidado: 121 deterministic, 46 canonical_equivalence, 26 student_lean; 165 verified, 24 refuted, 4 unverified. Os quatro unverified são fatos de entradas incompletas/sem fundamento no replay geral, não falhas das 26 provas formais.
- Regressões detectadas: nenhuma no escopo executado. Zero chamadas externas. `git diff --check`: OK; índice vazio; HEAD preservado.

Refutações formais finais:

| Caso | Fato refutado |
|---|---|
| b_false_center | admissibilidade de x=3 |
| b_false_sum | S=14 para centro5 |
| b_wrong_association | associação (5,14) dentro da lista de pares centro/soma |
| b_wrong_formula | fórmula de S incorreta |
| c_wrong_permutations | 4! = 20 |
| c_wrong_orientations | 2^4 = 8 |
| c_wrong_total | 24·16 = 364 |


Os comandos e resultados completos estão em `artifacts/evaluations/tme2_p2_pauta_bridge/validation_summary.json`, com logs locais. A comparação final usa saídas completas de bridge e assessment, incluindo hashes, evidências e pontos, não apenas totais. Não houve atualização de snapshots para acomodar diferenças.

A rastreabilidade por caso está nos JSONs de replay: item → obrigação → fact/source_claim_ids → evidência → mecanismo/artefato Lean → pontos. A tabela completa de casos e os status de obrigações estão em `replay_summary.json`; inclui corretos, parciais, duplicados, omissões, centro errado, não atribuídos, negados e falsos refutáveis.

Os testes compartilhados cobrem grounding, canonicalização, MathClaimRecord, fidelidade, gates de crédito, alinhamentos e scoring ITA. A suíte selecionada inclui o pipeline offline ITA; não é alegação de execução de toda a suíte do repositório. Falhas UI conhecidas e benchmark grande estão fora desta tarefa.

## Limitações e próximo passo

**diagram reasoning supported**: cálculo e correção da representação explícita, inclusive suas permutações, estão implementados.

**diagram recognition from arbitrary handwriting not yet supported**: a camada atual de recognition/HMER oferece texto/LaTeX, regiões e confiança, mas não o contrato topológico A–H. `recognize_p2_diagram_from_image` lança `NotImplementedError` deliberadamente. Os image refs dos controles são sintéticos, não fotos reconhecidas. Não foi criado adapter que adivinhe posições por regex.

Próximo passo: um adapter opt-in upstream deverá produzir posições e centro com regiões vinculadas à imagem, confiança por leitura, ambiguidades e confirmação/revisão. Avaliar esse adapter com imagens anotadas independentes, preservando desconhecidos e sem usar a pauta como fonte dos números. Só então ligar imagem manuscrita a `DiagramSubmission`. A API atual trata a confirmação como autoridade do caller; não comprova por si a autoria da imagem. Expressões/prosas fora da gramática suportada permanecem sem crédito automático.

## Arquivos, integridade e Git

Alterados em relação ao início desta tarefa (9):

- `app/confia_lean_auditor/claims/common/schemas.py`
- `app/confia_lean_auditor/lean/student_claim_checkers/real_algebra.py`
- `app/confia_lean_auditor/rubric/pauta/bridge.py`
- `app/confia_lean_auditor/student_claims/named_math.py`
- `app/confia_lean_auditor/tme/registry.py`
- `scripts/evaluation/run_tme_pauta_cases.py`
- `tests/test_tme2_p3_pauta_bridge.py`
- `tests/test_tme2_p4_pauta_bridge.py`
- `tests/test_tme2_p5_pauta_bridge.py`

Novos nesta tarefa (9):

- `app/confia_lean_auditor/core/math_canonical/combinatorial.py`
- `app/confia_lean_auditor/lean/student_claim_checkers/tme2_p2.py`
- `app/confia_lean_auditor/rubric/pauta/tme2_p2.py`
- `app/confia_lean_auditor/student_claims/tme2_p2_digital.py`
- `app/confia_lean_auditor/tme/p2_diagram.py`
- `docs/audits/TME2_P2_PAUTA_BRIDGE.md`
- `examples/pautas/tme2_problem2.v1.json`
- `tests/fixtures/tme2_p2_digital/cases.json`
- `tests/test_tme2_p2_pauta_bridge.py`

Os testes antigos de P3/P4/P5 só ajustam o registry esperado e trocam o identificador usado para testar problema não suportado de P2 para P6. Não foram alteradas expectativas matemáticas desses problemas. O helper Lean comum apenas admite o símbolo `S` quando solicitado explicitamente por P2. As gramáticas novas são opt-in; os defaults de P3/P4/P5 permanecem preservados.

O diff em `artifacts/evaluations/tme2_p2_pauta_bridge/implementation.diff` é incremental ao estado inicial desta tarefa, inclusive arquivos P4/P5 ainda não versionados que foram estendidos. Não corresponde ao diff integral contra HEAD. `scope_check.json` verifica preservação dos demais arquivos iniciais. `git_status.txt` registra o estado completo, incluindo trabalho anterior. `git_diff_check.txt` registra whitespace; `validation_summary.json` registra HEAD e índice. Sem staging/commit/push.
