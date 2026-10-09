# P2-CAP-04 — fonte conferida e Análise ConfIA

Somente uma revisão persistida associada ao seu aceite humano pode entrar na ponte. O aceite indica fidelidade ao manuscrito; não valida a matemática. A ponte não cria decisão docente, nota oficial ou devolutiva ao aluno.

## Contrato e fonte

`POST /submissions/{submission_id}/audits` recebe apenas `transcription_id`, `revision_number`, `acceptance_id` e, opcionalmente, `execution_key`. Campos como `solution`, `segments` e `problem_id` são rejeitados. Não há análise automática ao abrir, salvar, aceitar ou navegar.

`AuditSource` contém esses vínculos, `problem_id`, `accepted_at`, `source_hash`, `solution_text`, avisos e proveniência. A proveniência inclui a revisão completa, seu aceite completo e os hashes/referências do snapshot e de todas as imagens originais. A origem artificial de reconhecimento, quando existente, continua explícita na revisão, inclusive após o aceite humano.

## Integridade do aceite

O aceite registra `accepted_revision_sha256`, SHA-256 do JSON canônico da revisão persistida completa: serialização JSON do contrato, UTF-8, chaves ordenadas, separadores compactos e sem valores não finitos. Inclui metadados, segmentos, espaços, matemática e o estado original DRAFT/NEEDS_REVIEW. O estado ACCEPTED continua sendo uma projeção do histórico; não modifica o arquivo da revisão. AuditSource incorpora a revisão persistida original e o evento que comprova seu aceite.

Um `TranscriptionAcceptanceReceipt` separado em `acceptance_receipts/acceptance_NNNNNN.json` registra `acceptance_id`, `acceptance_sha256`, `accepted_revision_sha256` e `created_at`. O recibo cobre todos os campos do aceite, inclusive professor, nota de conferência e data. Recibo e aceite usam publicação exclusiva, sem sobrescrita; o recibo é publicado primeiro e o aceite por último. Leituras validam o par antes de projetar ACCEPTED. Revisão, aceite e recibo divergentes impedem a análise antes do motor e também são revalidados antes da publicação do run.

Isto fornece integridade referencial interna; não é assinatura digital nem garantia contra adulteração coordenada de todo o filesystem. Não se inventa hash para um aceite anterior. Eventos legados sem hash/recibo permanecem legíveis como histórico, sem projetar ACCEPTED nem autorizar análise; a UI informa a necessidade de nova revisão e conferência humana. Uma tentativa de analisar ou reaceitar diretamente o evento legado é bloqueada por integridade. Se uma interrupção publicar somente o recibo, nenhum aceite é projetado; uma repetição não repara nem sobrescreve esse evento. Uma nova revisão pode receber um novo aceite após conferência humana.

## Conversão `segments-v1`

1. Ordenar por `(page_index, order)`. Os identificadores e segmentos completos permanecem na proveniência.
2. Para `text`, `math` e `mixed`, encaminhar cada string armazenada, primeiro `text` e depois `latex`, separadas por `\n`. Ausência (`null`) não produz string. Quando ambos existem, ambos são preservados, inclusive se forem iguais; a ponte não escolhe qual representação é correta.
3. Não aparar espaços, normalizar símbolos, renderizar LaTeX, corrigir cálculos, completar argumentos ou inferir informações. `2 + 2 = 5` continua exatamente assim.
4. `unknown` recebe `[Segmento não identificado: ID]`, seguido das strings disponíveis, e aviso `UNKNOWN_SEGMENT`.
5. `diagram` recebe somente `[Diagrama não analisado: ID; página N]` e aviso `DIAGRAM_NOT_ANALYZED`. Suas strings, regiões, traços e imagem permanecem na fonte; não entram como descrição matemática no auditor textual. Nenhuma interpretação visual é inventada.
6. Segmento textual sem strings recebe `[Segmento sem conteúdo: ID]` e aviso `EMPTY_SEGMENT`.
7. Concatenar os segmentos convertidos com `\n`, sem acrescentar enunciado ou uma segunda solução.

`source_hash` é SHA-256 do JSON UTF-8 de todos os campos do `AuditSource`, exceto o próprio hash: chaves ordenadas, `ensure_ascii=False`, separadores compactos `(',', ':')`, sem valores não finitos. Inclui versão da conversão, vínculos, aceite, revisão, originais, texto derivado e avisos. Datas usam a serialização JSON do contrato Pydantic. Pedidos repetidos da mesma fonte produzem o mesmo hash.

## Validação e motor

Sob o lock do store de submissões, a ponte chama `assert_submission_integrity`, valida o histórico existente e a proveniência de reconhecimento, rejeita arquivos de revisão/aceite/recibo simbólicos ou inconsistentes e confere submissão, transcrição, revisão, aceite, páginas, datas e hashes. O estado `ACCEPTED` é projetado somente depois da validação do recibo e da revisão.

A entrada do motor continua `AuditRequest(problem_id, solution)`. A rota textual `/audit` e a ponte chamam a mesma função interna `main.execute_audit`. Extração, formalização, Lean, microclaims, student checks, rubrica, relatório e `artifacts/runs` permanecem no pipeline existente. Não há HTTP para a própria aplicação nem pipeline paralelo.

Após esperar outro pedido e após executar o motor, a fonte exata é novamente validada. Divergências impedem publicação de `AuditRun`. A revisão original aceita continua válida se uma revisão nova for criada durante a análise.

## Persistência, repetição e versões

`runtime/submission_audits/` guarda um JSON imutável por execução, separado de `runtime/submissions/`. `CONFIA_SUBMISSION_AUDITS_DIR` permite armazenamento isolado. O registro guarda `AuditSource`, vínculos, hash, início da execução (`created_at`), status terminal, resultado completo, `result_sha256` e referência ao diretório existente de artefatos. O hash canônico do resultado é validado na leitura e inclui score, rubrica, evidências, relatório e referências; alterações nesses campos bloqueiam recuperação/retry, sem executar novamente ou reparar o resultado. Runs antigos sem os novos vínculos/hashes não recebem migração automática.

O motor real sempre exporta `audit.json`, `solution.txt`, `claims.json`, `student_claims.json`, `student_claim_checks.json` e uma tentativa Lean referenciada no certificado. Um run COMPLETED da ponte exige essas referências, os witnesses de passos verificados e as provas positivas/refutações declaradas pelos student checks. Os witnesses obrigatórios dos student checks são copiados para o diretório da execução antes de exportar o resultado; as tentativas originais continuam como diagnósticos. Todos os arquivos obrigatórios devem ser regulares, ficar dentro do diretório absoluto do run e não atravessar symlinks. `required_artifacts` registra tipo, relação, arquivo, SHA-256 e tamanho; `artifact_manifest_sha256` cobre o manifesto completo. Leituras exigem correspondência exata entre o manifesto e as referências obrigatórias do resultado, além de conferir bytes/hash/tamanho. Não se recalcula nem repara o manifesto na leitura. Passos não verificados/textuais/incompletos não exigem witness.

Retorno do motor com artefatos ausentes/inválidos produz FAILED, sem resultado publicado como sucesso. Remoção ou adulteração posterior bloqueia GET/listagem/retry com conflito de integridade; não muda score nem responsabiliza o aluno. Runs antigos sem manifesto também não recebem migração automática. O fluxo textual de `/audit` continua independente de aceite, compartilhando o mesmo motor e a semântica de avaliação incompleta.

`auditor_version=null`: as versões declaradas para API/pacote não identificam de forma inequívoca a versão do motor. Antes do piloto institucional, registrar por run identificação imutável do código/build, hashes dos assets/templates e manifests/versões de Python, Lean e Mathlib. Este campo continua como follow-up; não é inventada uma versão.

Identidade `aud_` + SHA-256 de `{submission_id, transcription_id, revision_number, acceptance_id, source_hash, execution_key}` em JSON canônico. Sem chave, retries e duplo clique reutilizam a mesma execução. Com uma nova chave, a reexecução é explícita; repetir essa chave reutiliza o resultado. A UI oferece “Executar novamente” e conserva a chave quando há falha de transporte.

Um lock de arquivo por identidade serializa pedidos concorrentes entre threads/processos. O pipeline roda fora do lock geral de submissões. A publicação usa arquivo temporário, fsync e link exclusivo: não sobrescreve um run existente nem publica JSON parcial. Arquivos de lock permanecem para preservar a identidade do inode.

Erros de pré-condição não criam run. Falha do motor publica apenas `FAILED`, `error_code=AUDITOR_FAILED`, resultado e referência de artefatos nulos, sem diagnóstico privado ou sucesso fictício. Retry dessa execução devolve a falha; “Executar novamente” cria uma tentativa explícita. HTTP 200 representa consulta/registro terminal bem-sucedido; o cliente precisa consultar `status`, não tratá-lo como análise concluída.

`GET /submissions/{submission_id}/audits` lista execuções; `GET /submission-audits/{audit_run_id}` recupera uma. `stale` é calculado na leitura quando há revisão posterior da mesma transcrição ou outra transcrição mais recente para a submissão; não é persistido nem altera o run antigo. A UI também compara o vínculo com a transcrição selecionada. Nova revisão aceita gera fonte/hash/run próprios e mantém o histórico anterior.

## UI e Lean

O botão “Executar Análise ConfIA” exige revisão conferida, aceite vinculado, originais íntegros, consulta de análises disponível e editor sem alterações pendentes. Durante a operação, a UI anuncia “Analisando solução...” e bloqueia trocas incompatíveis. Resultado, histórico, fonte e avisos permanecem no mesmo fluxo do original.

“Concluída” exige uma execução válida para a revisão aceita selecionada. Uma análise de outra revisão aparece como versão anterior. Após HTTP 409, o estado corrente passa a conflito na tela, na fila e nas etapas; o relatório previamente carregado sai da apresentação e seu registro permanece somente no histórico, identificado como versão anterior. A UI pede atualizar/reabrir a solução antes de outra execução. Falha de transporte usa estado de falha separado e conserva a chave para retry; uma execução válida posterior restaura o estado concluído. Nenhum resultado ou run é fabricado ou reescrito por essas transições.

O renderer existente é compartilhado por `ConfIAReport.render`: síntese, evidências, critérios e pontos de atenção. “Verificações formais” explica o escopo seletivo de Lean e abre os resultados de claims/passos em detalhes. Nota e resultado são sugestões; a avaliação docente permanece em desenvolvimento.

## Semântica dos student checks

### Extensão mínima para avaliação incompleta (P1 global)

O contrato anterior exige `score` e `points` numéricos e não representa um critério indecidível. A correção permite `null` nesses campos, preservando números e nomes para avaliações completas. Critérios recebem `mathematical_status` (`supported`, `refuted`, `indeterminate`) e `verification_status` (`available`, `partial`, `technical_error`), separados. A rubrica expõe `assessment_status`, `evaluated_score` e `evaluated_max_score`: subtotal e capacidade somente dos critérios decididos, sem reescalar para dez. Havendo critério pendente, a nota global é `null` e o veredito é `inconclusivo`; a UI mostra “Avaliação incompleta”. Ausência de texto reconhecido também não comprova erro matemático. Clientes que calculam com score precisam tratar `null`; resultados completos conservam o contrato numérico anterior.

Provas positivas disponíveis continuam utilizáveis dentro de seu escopo, inclusive witnesses independentes dos passos formais quando a tentativa principal não conclui. Uma refutação formal pertinente permite zero no critério correspondente. Falhas técnicas e tentativas não conclusivas não são refutações, não dão pontos e não retiram pontos já sustentados.

Os consumidores legados do MVP e dos onze módulos de questões agora verificam explicitamente esse contrato: avaliação completa numérica; avaliação incompleta com score nulo e veredito inconclusivo; subtotal e capacidade iguais à soma somente dos critérios decididos. Respostas parciais, respostas finais isoladas e entradas adversariais conservam suas expectativas específicas. Critérios refutados com zero também entram na capacidade decidida: o exemplo `partial_beta_difference.txt` de F2Q3 mantém o comportamento existente de subtotal 2/4, com witness da refutação exigido pelo teste e score global nulo. A suíte forte F2 também exige os subtotais conhecidos dos exemplos incorretos, sem aceitar alternativamente qualquer score.

Serializadores, ponte, relatórios e renderer compartilhado preservam null. Os benchmarks versionados de nível 1 medem extração, sem consumir notas; os limites numéricos do gerador gold continuam sendo expectativas de fixtures. O runner auxiliar local `Scratch/run_level2_f2_suite.py` (ignorado pelo Git e fora do patch versionado) distingue `GLOBAL_SCORE_INCOMPLETE` de `SCORE_MISSING`, mantém subtotal separado e exclui avaliações incompletas das médias e comparações de notas. Não usa outro score/subtotal como fallback para um score explicitamente nulo; relatórios históricos não são migrados.

As regressões permanentes adulteram separadamente evidence_items, student_claim_checks, formal_steps, score, subtotal, verdict e rubric_assessment, além de feedback e attention_points. Cada alteração diverge de result_sha256 e bloqueia GET, listagem e retry sem executar novamente ou reparar bytes. As alterações de kind, order, page_index, text e latex da revisão aceita também divergem de accepted_revision_sha256 e bloqueiam antes do motor. A UI possui regressões de conflito com relatório em cache e de score nulo para aluno e professor, sem zero artificial nem subtotal apresentado como nota final.

O resumo usa as evidências efetivas, nunca apenas score/verdict, e explicita verificação parcial ou indisponível. O manifesto de artefatos obrigatórios da ponte registra tipo, vínculo, caminho controlado, SHA-256 e tamanho; é coberto por um hash próprio persistido no run. Inclui exports, tentativa principal, passos verificados, provas positivas e refutações. A ausência/adulteração bloqueia publicação ou leitura íntegra, sem julgamento matemático.

Débito P2 preexistente: o extrator F2Q6 pode omitir `maximizers_identification` na formulação do teste específico de certificado forte. A omissão foi reproduzida no HEAD anterior; extrator, assets e teoremas deste caso não serão corrigidos neste patch. Com critérios pendentes explícitos, a execução pode permanecer incompleta em vez de produzir a antiga pontuação reduzida. GOV-01 continua fora do escopo.

Todos os checkers de afirmações do aluno usam os mesmos quatro resultados: `verified`, `refuted`, `unverified` e `technical_error`; `unsupported` identifica conteúdo fora da cobertura. Uma prova da afirmação compilada sem recursos proibidos produz verified. Uma tentativa de prova malsucedida jamais estabelece falsidade. Missing module/import, unknown identifier, erros de elaboração/processo e timeout são técnicos; unsolved goals, tactic failed e limitações de síntese são não conclusivos.

Para tentativas não conclusivas, o checker pode gerar um segundo arquivo com um teorema da negação exata da proposição selecionada. Somente a compilação bem-sucedida desse teorema permite refuted; o resultado guarda `refutation_lean_file`, `refutation_verified` e os diagnósticos da tentativa. Definições e contraexemplos usados vêm dos checkers existentes. A verificação positiva e a negativa compartilham o orçamento de timeout existente. Se nenhuma delas comprovar seu resultado, a afirmação fica não verificada ou indisponível.

O report builder reserva “incorreta” para refutação com evidência formal. Para unverified informa “Não foi possível verificar formalmente esta afirmação”; para technical_error informa “A verificação formal deste trecho ficou indisponível nesta execução”. Estados antigos failed/error são inconclusivos. Todos os cinco ajustadores de rubrica só reduzem pontos por refuted acompanhado de evidência da negação; unverified/technical_error não descontam pontos por si só. Outros mecanismos determinísticos da rubrica continuam aplicáveis.

Na UI, os detalhes distinguem “Erro matemático identificado”, “Não foi possível verificar formalmente” e “Verificação formal indisponível”, mantendo a advertência de cobertura seletiva. Essa semântica vale igualmente para `/audit` e a ponte, pois ambos chamam `execute_audit`.

## Limites operacionais

Não há fila assíncrona, cancelamento, timeout novo, autenticação ou isolamento por usuário. Vale o comportamento de duração e dependências do pipeline existente. Se o processo encerrar após gerar artefatos e antes de publicar o run, uma tentativa posterior poderá executar novamente; arquivos completos de run deduplicam retries, mas não garantem execução única após interrupção do processo. Artefatos incompletos do motor podem permanecer em `artifacts/runs` após falha ou divergência de fonte; não são vinculados como sucesso.

A análise cobre o texto derivado e os claims suportados pelo auditor existente. Diagramas e trechos ausentes exigem avaliação humana. O hash indica vínculo e integridade técnica, sem comprovar autoria. A validação no navegador usa mouse de teste; não substitui teste físico de caneta/palma no tablet.

## Estratégia de paridade CAP-04

`test_real_engine_textual_bridge_parity_and_formal_witness_integrity` foi separado em responsabilidades independentes em `tests/test_cap04_parity.py`. A comparação incondicional de duas execuções reais misturava paridade da ponte, disponibilidade do executor e integridade dos artefatos. A exigência de equivalência matemática permanece quando a cobertura formal é equivalente.

| Nível | Execução | Exigências obrigatórias |
| --- | --- | --- |
| A — Bridge Contract Parity | `execute_audit` controlado, sem Lean | Ambas as rotas chamam a mesma função exatamente uma vez por pedido, com o mesmo `problem_id`, texto, bytes UTF-8 e SHA-256. O resultado exposto por cada rota é exatamente o devolvido pelo motor, incluindo score nulo e numérico, rubrica, subtotal, veredito e relatório. Fonte, hashes, manifesto e recuperação íntegra do AuditRun também são conferidos. |
| B — Controlled Engine Semantic Parity | Pipeline real, subprocesso Lean determinístico | Cenários VERIFIED, REFUTED, UNVERIFIED e TECHNICAL_ERROR; falha de módulo e de processo têm casos próprios. REFUTED exige witness da negação exata e sucesso controlado da compilação negativa. Claims extraídos, claims/checks do aluno, passos, microclaims/dependências, itens, subtotais, score, veredito e relatório devem ser exatamente equivalentes, removendo somente caminhos e diagnósticos operacionais. O teste não atribui a uma simulação a validação matemática de Lean real. |
| C — Real Engine Smoke | Lean real, sem LLM, chamadas sequenciais e sem retries | Cada execução exige HTTP 200, fonte exata, score contract, manifesto íntegro e coerência das evidências; a ponte exige COMPLETED e GET íntegro. Technical_error não constitui refutação; indisponibilidade não justifica zero/incorreto. Cobertura equivalente exige `central(textual) == central(bridge)`. |
| Integridade independente | AuditRun do pipeline com executor controlado | GET inicialmente 200. Remoção e adulteração de witness de formal step, witness de refutação e certificado obrigatório bloqueiam GET, listagem e retry com 409. O motor não é chamado novamente. Esta verificação não depende da comparação entre rotas. |

A assinatura de cobertura identifica cada obrigação por tipo/id e inclui status, compiled, exit_code, failure_category e refutation_verified, além dos teoremas gerados e das dependências/estados relevantes dos microclaims. A comparação central conserva todos os campos matemáticos; somente diretório, referências de arquivos e stdout/stderr são excluídos.

Uma diferença de cobertura só pode produzir `NOT_COMPARABLE_TECHNICAL_AVAILABILITY` se houver falha operacional observada no subprocesso da obrigação afetada: timeout, erro de processo ou indisponibilidade de módulo/arquivo. Diferenças de proposição, obrigação, fonte Lean ou resultados não conclusivos/refutados sem essa evidência falham. Erro de identificador também não recebe dispensa automática por ser classificado como técnico pelo checker.

Mesmo nessa rodada não comparável, todos os invariantes individuais continuam obrigatórios. As decisões derivadas do perfil formal efetivamente observado são conferidas, sem outra chamada ao Lean, para impedir que timeout encubra alterações independentes em rubrica, relatório ou feedback. Uma rodada não comparável é registrada como **skip após essas verificações**, com classificação, assinatura das duas coberturas e rastros dos subprocessos no JUnit; não aprova paridade matemática. Com cobertura equivalente, qualquer diferença central continua sendo falha. Regressões específicas exercitam esses dois caminhos e rejeitam alterações alheias ao timeout.

Nenhum timeout foi aumentado e não há retry até sucesso. Artefatos dos testes ficam em armazenamento temporário isolado; cwd, comando `lake env lean` e limites originais de 30 segundos para passos/certificado e 90 segundos compartilhados pelos checks positivos/negativos permanecem.

### ENG-LEAN-01 — estabilidade/observabilidade do executor Lean

A investigação anterior de F2Q1 confirmou entradas idênticas: 487 bytes UTF-8 / 482 caracteres, SHA-256 `121558291e4b28600f9a8431084411cb89a1d17a0fe83fe264ef390f982dbda1`, mesmo `execute_audit`, configuração e fontes Lean. Nos dez pares alternados, nove tiveram cobertura equivalente e igualdade central exata; um ficou não comparável por timeout de `f2q1_s1_power_reductions` na primeira execução absoluta, textual, com duração de aproximadamente 30 segundos. As execuções seguintes desse passo ficaram aproximadamente entre 7 e 9 segundos, inclusive nove sucessos na própria rota textual. Um par adicional em processo novo teve cobertura e resultados centrais iguais.

Essa amostra sustenta o diagnóstico operacional **runtime variability**, sem evidência de bug associado à rota; não estabelece distribuição, causalidade ou conclusão estatística. ENG-LEAN-01 permanece aberto para estabilidade e observabilidade do executor. Este patch modifica somente testes/documentação e não corrige esse débito. F2Q6 conserva o xfail P2 conhecido; GOV-01 permanece P1 obrigatório antes do piloto, com a exceção aceita para o commit do CAP-04.

## Revalidação da estratégia de paridade — 2026-10-07

A bateria selecionada executou 296 casos Python distintos: **294 aprovados, uma rodada não comparável no smoke real e um xfail P2 conhecido de F2Q6**, sem falhas. A consolidação usa a rechecagem determinística dos seis guards cuja simulação foi reforçada para também exportar a decisão adulterada em `audit.json`; esses casos passaram antes e depois do reforço e não são contados duas vezes. JavaScript: **202/202 aprovados**. Nenhuma execução real foi repetida para obter cobertura equivalente.

Contrato: 2/2; semântica controlada: 6/6; integridade independente: 6/6; guards de comparação: 11/11. Regressão: student checks F2 29/29, ajustes de rubrica F2 26/26, suíte forte 10/10, relatórios 4/4, certificados específicos 11 aprovados + 1 xfail conhecido, Audit Bridge 31/31, semântica global CAP-04 51/51, student proofs 79/79 e integridade CAP-04 27/27.

No smoke Q1, S1 textual levou 30,044 s e terminou com timeout/exit 124; S1 via Bridge levou 7,221 s e terminou com exit 0. Os invariantes individuais das duas execuções passaram; a rodada foi registrada como `NOT_COMPARABLE_TECHNICAL_AVAILABILITY`, sem aprovação de paridade matemática. Q8 incorreto teve cobertura equivalente e igualdade central exata. Nenhuma diferença central apareceu com cobertura equivalente. A posterior aprovação de Q1 na suíte forte não reclassifica a rodada não comparável do smoke.

Execuções reais foram sequenciais, sem LLM, com armazenamento isolado e limites originais. O harness produziu um aviso `PytestAssertRewriteWarning` porque `anyio` já estava importado ao iniciar o pytest. O log completo, JUnit com assinaturas/rastros e consolidação estão em `/Users/LinMarcolino/.codex/visualizations/2026/10/05/01a10d38-379a-7502-8ce5-5181293dea8b/p2-cap-04-tests/` (`regression.log`, `regression.xml`, `guards-final.xml`, `javascript.log`, `results.json`).

## Validação anterior às mudanças de estratégia de paridade

Após as correções dos três P1 finais, a bateria executou 587 casos Python distintos: 586 aprovados e somente o xfail explícito do P2 preexistente `test_f2q6_correct_solution_includes_strong_certificate`. JavaScript: 202/202 aprovados. Não restou falha nova. As execuções usaram armazenamento isolado em `/private/tmp`, sem caches do pytest nem artefatos de análise no checkout, com até dois processos de Lean real simultâneos.

| Grupo | Aprovados | Pendência conhecida |
| --- | ---: | ---: |
| Student checks dos cinco F2 | 29 | 0 |
| Rubric adjustments dos cinco F2 | 26 | 0 |
| Strong Lean suite | 10 | 0 |
| Certificados específicos | 11 | 1 xfail P2 preexistente |
| Reports reais | 4 | 0 |
| Audit Bridge (`test_submission_audits.py`) | 31 | 0 |
| Regressões P1 globais novas (A–M, exceções, paths e integração real) | 53 | 0 |
| Semântica dos student proofs | 79 | 0 |
| Integridade CAP-04 | 27 | 0 |
| Contratos legados das questões | 45 | 0 |
| Contrato MVP das dez questões | 30 | 0 |
| Demais contratos, catálogo e interface | 241 | 0 |

A execução inicial da segunda bateria registrou duas expectativas a ajustar: a marcação de F2Q6 havia sido coletada antes de seu último ajuste; no teste parcial de F2Q3, a capacidade decidida precisava incluir o critério já refutado com zero. Após corrigir somente essas expectativas, ambos foram reexecutados com Lean real: F2Q6 resultou no xfail documentado e F2Q3 passou. O último teste real da UI também passou. O resultado acima consolida o último resultado de cada caso, sem contar reexecuções duas vezes. Logs completos: `/private/tmp/cap04-correction-fast.log`, `cap04-correction-real-a.log`, `cap04-correction-real-b.log`, `cap04-correction-extra.log` e `cap04-correction-js.log`; a consolidação está em `/private/tmp/cap04-correction-results.json`.

Os 53 casos novos incluem as soluções corretas F2Q3/Q8 sob indisponibilidade do Lean, os quatro modos de falha em todos os cinco F2 e nas duas rotas, score alto sem evidência positiva, evidência parcial, witnesses removidos/adulterados e fora do diretório, ausência de witness em passos não verificados e preservação da exigência de refutação. As rotas reais foram comparadas para Q1 correto e Q8 incorreto; remover um witness formal real de Q1 bloqueou a recuperação com HTTP 409. A leitura persistida dos probes Q3/Q8 conservou `score=null`, veredito inconclusivo e limitação técnica, sem reexecutar o motor.

No exemplo específico F2Q6, certificado e três student checks estão verificados, mas `maximizers_identification` permanece ausente. Subtotal: 8/8 nos critérios decididos; score global `null` e veredito inconclusivo. O extrator é byte a byte idêntico ao HEAD anterior e produz a mesma omissão. O teste agora declara xfail somente depois de confirmar exatamente esse comportamento conhecido, incluindo certificado, três checks e ausência do certificado forte específico; qualquer outra divergência falha normalmente. A expectativa original de 10 pontos permanece no teste para quando o extrator reconhecer a formulação. GOV-01 permanece P1 antes do piloto institucional e exceção aceita para o commit do CAP-04, sem implementação neste patch.

Os registros de navegador abaixo documentam a validação anterior às correções P1 globais e ao manifesto. Não representam uma nova validação de navegador nem substituem as regressões permanentes da versão atual.

- Testes de contrato cobrem DRAFT/NEEDS_REVIEW bloqueados, aceite exato, proveniência artificial, divergências e symlinks, conversão sem correção, hash, persistência, concorrência, retry/reexecução, fonte alterada durante execução, versões posteriores, falha terminal e `/audit` textual. Regressões permanentes cobrem adulteração de text/math/metadados da revisão, professor/nota/hash do aceite, recibo ausente/adulterado, resultado adulterado, referências inválidas e equivalência entre as duas rotas sob falha formal. A integração real verifica a negação de `2 + 2 = 5` e afirmações verificadas; os testes dos problemas preservam refutações matemáticas com evidência formal.
- No navegador: captura por mouse de teste de `2 + 2 = 5` e `a=1, b=1`, preparação, envio, abertura do PNG, transcrição manual, aceite e execução explícita. O renderer exibiu a afirmação `a=1, b=1` como incorreta, sugestão 0/10, critérios, atenção e verificações formais. A expressão `2 + 2 = 5` foi preservada na entrada; não se afirma que o extrator específico do problema a verificou.
- Submissão de teste `sub_b96075494d49432496b32b8826e55a77`; run `aud_525e47a677bb95fe11d4561505b772f54ce4f14d45ae0bde9a939939febd15c0`; fonte SHA-256 `9da4f2d007ce2ddc9faab34fe0686aadb364a1ca550a7c81014a9ec1ac59646a`. Artifacts reais: `artifacts/runs/20261005T183824_236970` (referência também no JSON do run em `/private/tmp/confia-cap04-manual/audits/`).
- Os sete arquivos existentes na fonte após o aceite permaneceram byte a byte idênticos depois da análise. Após recarregar a página, o resultado persistido foi recuperado sem nova execução. Uma revisão 2 posterior passou a exibir “Esta análise corresponde a uma transcrição anterior.” e bloqueou nova análise até sua conferência; o run da revisão 1 continuou preservado.
- Viewports de desktop, tablet (768 px) e celular (390 px): controles utilizáveis, avisos visíveis, um único fluxo empilhado no celular e largura de conteúdo igual à viewport, sem overflow horizontal. Evidências visuais em `artifacts/p2-cap-04/teacher-analysis-desktop.png` e `teacher-analysis-mobile.png` (artefatos locais ignorados pelo Git).
