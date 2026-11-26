# ConfIA DYNAMIC — Intervenção 6B: feedback formativo restrito

Data: 26/11/2026. Branch: `codex/dynamic-development`. Base Git: `d40a7b08ff5eef60b012f382e64fa82a604c05fc`, com a Intervenção 6 e seu relatório de revisão ainda pendentes. Nenhum commit, push ou merge foi realizado.

## Resultado e causas

A correção fica na projeção pedagógica SELF_STUDY. Grader, Reviewer, Reconciliation, rubricas, pontuações, verificadores e registros matemáticos históricos não foram modificados. A projeção passou a usar `self-study-feedback.v2`; uma resposta do provider não é mais um texto automaticamente autorizado para divulgação.

| Bloqueio | Causa anterior | Correção |
| --- | --- | --- |
| R1: pontos em títulos públicos | Título interno da rubrica copiado diretamente para objetivos e relatório; os testes verificavam nomes de campos, não seu texto. | Rótulos públicos locais `Objetivo n`, IDs públicos derivados e opacos; títulos, descrições, pontos, níveis e pareceres completos permanecem privados. |
| R2: nota/resolução completa no nível 2 | O validador verificava citações e IDs, mas aceitava qualquer mensagem do provider. | Contrato fechado de seleção de orientação; prosa livre e etapas de resolução nos níveis 2–3 são rejeitadas. Rejeições geram registro privado e orientação segura. O histórico é novamente projetado/validado a cada consulta. |
| R3: erro desaparecia no parcial | O ramo `PARTIAL` descartava o tipo de achado matemático. | `mathematical_finding` separado de `state`; parcial com erro continua parcial e sinaliza o erro, com citação. Divergência sobre existência de erro vira incerteza pública, sem mudar a pontuação interna. |

## Inventário e arquivos alterados nesta etapa

O inventário inicial registrou hashes dos 22 arquivos pendentes da I6/revisão em `artifacts/qa/dynamic-intervention6b/baseline.json`, ignorado pelo Git. As alterações próprias da 6B são:

| Arquivo relativo à raiz do worktree | Responsabilidade |
| --- | --- |
| `app/confia_lean_auditor/dynamic/study_models.py` | Contrato de ajuda controlada, etapas estruturadas e campo diagnóstico aditivo para o achado matemático. |
| `app/confia_lean_auditor/dynamic/study_feedback.py` | Projeção pública, rótulos, distinção de erros, repertório de pistas/conceitos, validação e renderização segura, reconsulta histórica. |
| `app/confia_lean_auditor/dynamic/study_service.py` | Vínculo entre análise privada e projeção pública, registro de rejeições, fallback, confirmação da interpretação e histórico sem reescrita. |
| `app/confia_lean_auditor/dynamic/provider.py` | Prompts exclusivos do estudo, schema estruturado de ajuda e identificação de sua versão. Os prompts institucionais existentes não foram alterados. |
| `app/confia_lean_auditor/static/dynamic-self-study.js` | Identifica a orientação segura substitutiva na interface. |
| `tests/test_dynamic_self_study.py` | Provider simulado compatível com o novo contrato; expectativa de fallback após rejeição. |
| `tests/test_dynamic_self_study_feedback_policy.py` | Regressões adversariais permanentes de R1–R3, divulgação, histórico, expressão matemática e isolamento. |
| `tests/js/test_dynamic_self_study.cjs` | Exibição explícita de erro com parcialidade e identificação da orientação segura. |
| Este relatório | Causas, contratos, evidências, validação e limites. |

As demais alterações pendentes da I6 foram preservadas. Não há nova implementação de OCR, avaliador matemático ou engine de pontuação.

## Contratos e fronteira pública

`self-study-report.v1` continua legível e recebe o campo aditivo `mathematical_finding`, com default conservador `UNCERTAIN`. A regra de projeção é versionada como `self-study-feedback.v2`. A definição histórica de `HelpProposal` permanece disponível; o novo provider usa `ControlledHelpProposal`, com discriminador `self-study-help.v2` e campos extras proibidos.

Separação efetiva:

- **Auditoria privada:** rubrica integral, máximos e níveis internos, decisões, claims, reconciliação, respostas e proveniência dos providers, conteúdo rejeitado quando disponibilizado pelo transporte.
- **Evidência pública:** trecho literal da resolução do aluno, offsets e hash de origem; números, frações, expoentes e operações da fonte não são removidos.
- **Diagnóstico público:** atendimento qualitativo, tipo de achado, incertezas e comparação de tentativas.
- **Texto público gerado:** renderização local a partir de enums e contratos fechados, nunca cópia indiscriminada de justificativa ou título interno.

Identificadores de critério também são derivados para que um ID escolhido pelo provider não funcione como outro campo de divulgação. O número em `Objetivo n` é ordem de apresentação, não peso ou nota. Não há boletim, percentual de aproveitamento, ranking, `FinalCorrection` ou nota oficial no contexto.

A preparação também deixa de publicar livremente `normalized_problem`, advertências ou incertezas textuais do provider. A interpretação pública precisa coincidir com o enunciado conferido, admitindo apenas normalização de espaços; alterações ou acréscimos exigem esclarecimento. O prompt solicita cópia fiel. A análise estruturada completa permanece privada. Essa decisão impede que a preparação antecipe resposta ou pontuação por um campo fora das pistas, com o custo deliberado de não aceitar paráfrases automáticas nesta etapa.

Não existe exportação própria de SELF_STUDY. GET, reabertura de histórico e interface consomem a mesma projeção restrita. Uma futura exportação deverá reutilizá-la. Trechos da fonte do aluno são mostrados como evidência da fonte, não convertidos em nota emitida pelo ConfIA.

## Divulgação por nível

| Nível | Conteúdo autorizado | Validação antes de divulgar |
| --- | --- | --- |
| 1 | Situação do objetivo, tipo de achado e citação da solução; mensagem local. | Projeção dos registros do núcleo; não publica parecer livre nem solução de referência. |
| 2 | Uma pista escolhida de um repertório de conceitos: igualdade, fatoração, proporcionalidade, funções, geometria, condições ou explicação de passo. | Schema fechado, conceito enumerado, critério conhecido e citações vinculadas. `steps` precisa estar vazio. Nenhuma mensagem livre é aceita. |
| 3 | Explicação conceitual local do mesmo repertório, mantendo o raciocínio com o aluno. | Mesmas restrições; sem etapas ou resultado novo específicos do problema. Não recebe soluções de referência. |
| 4 | Desenvolvimento proposto, após solicitação explícita, em etapas com regra enumerada e expressão matemática. | Consentimento, sequência, evidências e estado não inconclusivo; expressões passam por uma restrição lexical de sintaxe. Não aceita prosa, rótulos de nota, HTML, identificadores arbitrários ou certificação. |

O contrato não elimina números com regex. Nos níveis 2–3 não há canal de prosa livre do provider a ser censurado; o servidor renderiza textos conhecidos. No nível 4, a restrição lexical admite números, frações, variáveis de uma letra, operadores usuais e funções delimitadas (`sqrt`, `sin`, `cos`, `tan`, `log`, `ln`, `abs`). Ela restringe o formato de divulgação, **não verifica a verdade matemática da expressão**. O desenvolvimento é identificado como proposta a conferir, nunca certificado em Lean. Fórmulas da solução original não passam por essa restrição: são preservadas literalmente.

Resposta fora do contrato, citação inventada, nota em campo extra, prosa em expressão, passos prematuros ou falha técnica geram `help_failures` privado. A solicitação recebe `SAFE_FALLBACK`: texto local que orienta retomar o trecho e explicar a regra, sem novo julgamento matemático. Não se transforma a falha da pista em erro da solução. A solicitação é idempotente; repeti-la não repete a chamada. O estudante pode avançar na sequência após receber a orientação substitutiva, mas o nível 4 continua exigindo consentimento e fundamento suficiente.

## Parcialidade e erros

`state=PARTIAL` e `mathematical_finding=MATHEMATICAL_ERROR` podem coexistir. A mensagem reconhece desenvolvimento aproveitável e explicita o possível erro no trecho citado. A pontuação parcial interna continua exatamente a produzida pela rubrica e pelo núcleo.

Parcialidade sem erro identificado é projetada como desenvolvimento incompleto; não se inventa erro algébrico ou conceitual. Se um avaliador aponta erro e o outro não, a projeção informa a divergência e usa `UNCERTAIN`/`REVIEW_PENDING`. A reconciliação interna e seus pontos não são reescritos. Falha técnica e evidência insuficiente continuam distintas de erro matemático. Falta de dados históricos suficientes para reprojetar resulta conservadoramente em indisponibilidade técnica, não em parecer favorável.

## Histórico e integridade

A consulta reconstrói o relatório público a partir dos registros privados existentes. Relatórios antigos, títulos internos e orientações livres não são devolvidos literalmente. Ajuda histórica v1 aparece como orientação segura, sem expor a mensagem antiga; registros privados permanecem inalterados. Ajuda v2 é validada novamente antes da divulgação, incluindo vínculo ao hash da análise e consentimento do nível 4.

A comparação de tentativas usa as projeções derivadas e o mesmo pacote fixado. A existência de erro é preservada mesmo quando o atendimento anterior foi parcial. Não há inferência de evolução entre rubricas diferentes nem transformação do histórico em nota escolar. Testes verificam igualdade dos bytes dos artefatos antes/depois das consultas e das rejeições.

## Validação

Providers, reconhecimento e soluções usados nesta etapa são simulados/sintéticos. Os testes permanentes cobrem títulos com pontos, nota em mensagem/justificativa, resposta final com citação válida, passos completos no nível errado, números e frações legítimos, parcialidade com erro, parcialidade incompleta, discordância, inconclusão, falha técnica, histórico antigo, reconsulta após rejeição e acesso a dados privados/de outro aluno.

| Verificação | Resultado |
| --- | --- |
| Python ampliado: DYNAMIC, três contextos, captura, autorização, isolamento, persistência e contratos TME² | **769 aprovados, 2 skips em 379,43 s** |
| JavaScript completo | **614 aprovados, zero falhas ou skips em 2,05 s** |
| Reprodução dos três contraexemplos arquivados, com helper de serialização compatível | **3 aprovados em 6,65 s** |
| Verificação dirigida inicial, antes dos seis últimos casos | **38 aprovados em 69,05 s**; os seis casos adicionais passaram na suíte ampliada |
| `git diff --check` | Aprovado |
| Navegação, teclado, análise parcial e histórico no navegador | Aprovados com provider e conta sintéticos |

Os 30 casos novos permanentes estão incluídos nos 769; os totais não devem ser somados como testes distintos. Os dois skips são `test_real_smoke_dry_run_separates_semantic_hashes_from_transport` e `test_transport_builder_does_not_weaken_holdout_guard`, ambos em `tests/test_tme_model_compat.py`, pelo motivo `Frozen local DEV pack unavailable`. Não houve deseleção. Os logs desta etapa estão em `artifacts/qa/dynamic-intervention6b/`, fora do Git.

Os três contraexemplos reproduzidos passaram: **3 aprovados em 6,65 s**. R1 mantém o título com pontos somente no registro privado; R2 rejeita a nota/solução apesar da citação válida; R3 preserva o erro no feedback parcial.

Os três contraexemplos da revisão foram preservados em `artifacts/qa/dynamic-intervention6-review/`. A reprodução 6B usa uma cópia em `artifacts/qa/dynamic-intervention6b/test_original_counterexamples.py`, ajustando somente a serialização do provider simulado para `model_dump(mode='json')` antes de `json.dumps` (compatibilidade com Decimal), sem mudar as respostas adversariais nem as asserções. A primeira tentativa com o helper antigo encontrou essa falha de serialização; não foi tratada como regressão matemática nem escondida alterando a aplicação.

Comandos principais, na raiz do worktree:

```sh
env -u OPENAI_API_KEY CONFIA_DYNAMIC_LLM_ENABLED=0 CONFIA_SEMANTIC_LLM_ENABLED=0 PYTHONPATH=app PYTHONDONTWRITEBYTECODE=1 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q -rs --tb=short -p no:cacheprovider tests/test_dynamic*.py tests/test_submissions.py tests/test_transcriptions.py tests/test_recognition*.py tests/test_core_auth.py tests/test_core_institutional.py tests/test_assessments.py tests/test_capture_contracts.py tests/test_capture_static.py tests/test_tme_full_exam.py tests/test_tme_finalization.py tests/test_tme_question_audit.py tests/test_tme_human_confirmation.py tests/test_tme_model_compat.py
node --test tests/js/*.cjs
env -u OPENAI_API_KEY CONFIA_DYNAMIC_LLM_ENABLED=0 CONFIA_SEMANTIC_LLM_ENABLED=0 PYTHONPATH=app PYTHONDONTWRITEBYTECODE=1 /Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python -m pytest -q --tb=short -p no:cacheprovider artifacts/qa/dynamic-intervention6b/test_original_counterexamples.py
git diff --check
```

### Três contextos e integridade do Git

A regressão inclui `test_summative_guidance_is_rejected_and_formative_feedback_is_bounded`: prova somativa rejeita orientação antecipada; lista formativa disponibiliza orientação limitada sem rubrica interna ou pontuação sugerida. Inclui também `test_disagreement_adjudication_release_and_attempt_quota`: nota e feedback institucionais dependem da liberação docente. As restrições de SELF_STUDY não substituem essas políticas institucionais.

A comparação com o inventário inicial encontrou exatamente sete arquivos preexistentes alterados pela 6B e dois arquivos novos (testes e este relatório). Os demais quinze arquivos pendentes ficaram com os mesmos hashes. O index continua vazio. A busca por padrões de chaves privadas/tokens nos arquivos próprios da 6B não encontrou correspondências; os dados de teste são sintéticos.

- HEAD preservado: `d40a7b08ff5eef60b012f382e64fa82a604c05fc`.
- Main preservada: `8fde840d95fa4df0553b915d7b60301c9892aa65`.
- Objeto da tag anotada RC1 preservado: `0c64e318a26e21f71fe3097c66ee17a5206dd8a3`.
- Commit RC1 preservado: `c03403fe5b83d9db9df172882bd69af3dfa2d027`.

Nenhum commit, push ou merge foi realizado. Nenhuma alteração no Grader, Reviewer, Reconciliation, Semantic B ou implementação TME² foi identificada nesta etapa.

### Navegador

Servidor isolado em localhost, encerrado após o teste. Conta sintética autenticada, acesso à área do aluno e Estudo via teclado. Foi criado um enunciado novo, confirmadas leitura/interpretação, registrada a solução `Subtraio 6 dos dois membros: 2x=12. Depois divido: x=7.` e solicitada análise com pareceres simulados de parcialidade e erro.

A tela mostrou simultaneamente desenvolvimento aproveitável e possível erro matemático com citação. O provider simulado tentou incluir nota e solução completa no nível 2; a interface exibiu `Nível 2 · orientação segura`, sem divulgar o conteúdo. O percurso voltou ao histórico e reabriu a análise, preservando o bloqueio. A captura está em `artifacts/qa/dynamic-intervention6b/safe-history.jpg`, ignorada pelo Git. Nenhum dado real ou API paga foi utilizado.

## Limitações e recomendação

- As pistas dos níveis 2–3 são mais restritas que uma conversa aberta. O provider ainda pode escolher um conceito pouco pertinente; isso requer avaliação pedagógica real. As mensagens não são adaptadas linguisticamente a cada idade dentro da Educação Básica; o ano é informado ao provider, e o repertório usa linguagem escolar comum.
- Rótulos públicos são genéricos, ancorados nas evidências; o detalhe da rubrica fica privado. Uma evolução futura pode oferecer rótulos pedagógicos mais específicos sob o mesmo controle de divulgação, sem republicar os títulos internos.
- Reescrita/paráfrase da interpretação exige esclarecimento, mesmo quando poderia ser matematicamente equivalente. Isso é uma restrição conservadora da apresentação, não um teste de equivalência matemática.
- O nível 4 suporta desenvolvimento estruturado, não toda demonstração discursiva, notação avançada ou diagrama. Não há garantia de correção matemática das etapas propostas por um LLM. Conteúdo fora do formato não é liberado; ausência de etapas permite somente orientação conceitual.
- Uma expressão sintaticamente admissível pode estar matematicamente errada. Restrição de formato não é validação científica, prova Lean nem segundo engine. Nenhuma nota é produzida a partir dessas orientações.
- OCR/LLM reais, custo, latência, adequação à idade e aprendizagem continuam sem validação independente nesta etapa. O piloto deve permanecer supervisionado e separar qualidade de transcrição, rubrica, julgamento e explicação.
- Os dois skips históricos por pacote DEV congelado ausente continuam documentados na revisão I6. Não foram substituídos por dados inventados. A falha intermitente anterior da P3 permanece registrada, sem causa atribuída por esta correção.

Os três bloqueios reproduzidos foram corrigidos e suas regressões passaram. A recomendação é submeter a I6+6B à revisão destes contratos restritos e, se aceita essa política pedagógica conservadora, consolidar tecnicamente em etapa autorizada. Não publicar automaticamente nesta tarefa nem declarar `DYNAMIC-RC1` cientificamente validada. A main e a tag `SPECIALIZED-TME2-RC1` devem permanecer intactas.
