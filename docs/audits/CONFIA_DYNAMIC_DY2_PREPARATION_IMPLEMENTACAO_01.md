# ConfIA Dynamic — DY2: preparação matemática e sugestão de rubrica

## 1. Base e escopo

- Worktree exclusivo: `/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic`.
- Branch: `feat/dynamic-correction`.
- SHA inicial: `c2985d211ccbe29e9ce45ca1ec25b62e5fcec32a`; estado inicial limpo, DY1 já commitado.
- Linha baseada em `cb1df6e381fd0214092f33afe554ce506da68c78`.
- Não foram acessados nem usados ambientes, caches, launchers ou arquivos de outros worktrees.
- Sem `git add` ou commit nesta implementação.

DY2 prepara texto de problemas inéditos e gera rubricas para revisão docente. Não corrige soluções de alunos, atribui notas, cria AuditRun Dynamic, implementa reviewer/reconciliation de correção ou certifica Dynamic.

## 2. Arquitetura e infraestrutura reutilizada

O agregado DY1 permanece a fonte única de problema, enunciados, rubricas, pacotes, aprovações e eventos. `PreparationService` acrescenta evidências de preparação ao mesmo histórico append-only, usando `DynamicStore`, locks de `AssessmentStore`, escrita atômica de `SubmissionStore`, hashes canônicos e autenticação docente existentes. As chamadas ao provider ficam fora do lock; publicações conferem novamente identidade/versão.

Não há segundo cadastro de problemas/rubricas, registry por problema, novo banco de eventos, engine de correção ou caminho alternativo D1–D7. `CorrectionMode` e os defaults Specialized não foram alterados. As únicas modificações fora de `dynamic/` são assets da UI Dynamic, seus links de cache no HTML e testes Dynamic.

Novos módulos:

| Módulo | Responsabilidade |
|---|---|
| `dynamic/preparation_models.py` | Interpretação, candidatos, claims, estratégias, verificações, proveniência e estados. |
| `dynamic/provider.py` | Provider real OpenAI Responses, saída estruturada, configuração explícita e falhas fechadas. |
| `dynamic/verification.py` | Seleção de capacidades, aritmética/polinômios exatos limitados e consistência. |
| `dynamic/preparation.py` | Ciclo de preparação, geração/revisão semântica da rubrica e publicação no DY1. |

## 3. Preparation model e vínculo imutável

`PreparationRecord` registra ID opaco, versão sequencial global do problema, problema, pacote de origem, versão/hash do enunciado, solicitante, motivo opcional, timestamps, status, proposta, análise e proveniência. Cada mudança de estado acrescenta um registro; não reescreve o anterior.

A relação é acíclica: preparação referencia pacote de origem e enunciado; um novo pacote preparado referencia o hash da preparação terminal. A rubrica derivada referencia essa mesma preparação; o pacote que contém a rubrica agrega ambos os hashes. Aprovação continua a selar pacote/rubrica exatos.

Campos opcionais DY2 usam serialização/hashing `exclude_unset=True` no agregado Dynamic. Isso conserva os bytes conceituais que participavam dos hashes DY1 quando esses campos não existiam. Um teste valida os hashes da aprovação real preservada na evidência commitada de DY1; não há migração/regravação de snapshots antigos.

## 4. Status lifecycle

`PENDING → RUNNING → READY_FOR_REVIEW | REVIEW_REQUIRED | FAILED`.

- PENDING/RUNNING ficam persistidos antes da chamada externa e podem ser consultados por outro request.
- READY_FOR_REVIEW significa evidência disponível para revisão dentro do escopo; não significa verdade matemática ou autorização de correção automática.
- REVIEW_REQUIRED conserva hipóteses inferidas, ambiguidades, conflitos e lacunas.
- FAILED conserva código de falha e, quando houve resposta, saída/proveniência do provider.
- SUPERSEDED é projeção histórica: nova preparação ou novo enunciado não altera bytes anteriores.
- Execução interrompida por mais de 180 segundos pode ser marcada FAILED em uma nova tentativa, preservando sua história.

Não há fila durável externa nesta etapa: o POST realiza a execução de forma síncrona em worker HTTP, com timeout de 90 segundos por chamada e sem retry automático. A UI apresenta loading e permite recarregar os estados persistidos.

## 5. Interpretação e ambiguidade

O provider propõe domínio, dados, problema normalizado, objetos/variáveis, restrições, hipóteses EXPLICIT/INFERRED, objetivo, expectativas de unicidade, warnings e uncertainties. O enunciado é tratado como dado, não como instrução operacional. Nenhuma ferramenta ou código gerado pelo modelo é executado.

Hipóteses inferidas e incertezas relevantes forçam REVIEW_REQUIRED. O prompt solicita detecção de domínio ausente, notação ambígua, dados insuficientes, inconsistência e múltiplas interpretações. Essa detecção semântica não é completa nem garantida; a UI e a análise declaram o limite. Não existe pontuação de confiança usada como autoridade.

## 6. Soluções candidatas e claims

Cada `CandidateSolution` possui estratégia, claims ordenados, resultado final estruturado, IDs de suporte e incertezas. Claims têm texto, forma normalizada, tipo, dependências, objetos, verificador proposto, motivo, candidatura a formalização e `CheckSpec` declarativo. Validações rejeitam IDs duplicados, referências ausentes e dependências para claims não anteriores.

A proveniência da geração é compartilhada pela preparação imutável à qual todos os candidatos/claims pertencem. Resultados de verificação ficam em `PreparationAnalysis`, separados da proposta do modelo. O provider não pode enviar um campo de verificação aprovada para atribuir autoridade a si mesmo.

`CandidateCheck` distingue VERIFIED_WITHIN_SCOPE, PARTIALLY_VERIFIED, CONTRADICTED e UNRESOLVED; o resultado final precisa corresponder aos claims de suporte checados. Mesmo VERIFIED_WITHIN_SCOPE não certifica a interpretação do enunciado inteiro.

## 7. Estratégias alternativas

Estratégias têm ID, descrição e IDs de claims esperados. `StrategyCheck` informa a cobertura desses claims e explicita seu limite. São permitidos métodos alternativos sem inventar uma multiplicidade obrigatória. A rubrica usa `accepted_alternative_strategies`, objetivos e claims relacionados, preparando o consumo no DY3 sem impor um checker especializado.

## 8. Auditoria e plano de verificadores

Foram inspecionados os componentes genéricos existentes:

- `core/math_canonical/parser.py`: gramática limitada, AST matemático tipado, sem `eval`, despacho arbitrário ou execução de código.
- `core/math_canonical/rational.py:rational_value`: avaliação racional exata reutilizada. O helper contextual `weighted_sum_matches` não foi incorporado ao Dynamic.
- `core/math_canonical/equivalence.py`: comparação conservadora, com resultado desconhecido fora da cobertura.
- `student_claims/generic_math.py`: extração de spans de solução de aluno; não foi importado para preparar problemas.
- Checkers/registries TME/ITA e o pipeline formal Specialized não são importados pelo novo código.

A extensão matemática nova converte o AST genérico em polinômio univariado racional com grau máximo 12 e coeficientes de até 512 bits. Aritmética fechada usa Fraction e o parser existente. Identidades comparam coeficientes exatos. ROOT_SET exige divisões exatas, incluindo multiplicidades, e nenhum fator restante: testar apenas substituições não bastaria para afirmar completude. Funções, divisão por variável, múltiplas variáveis e expansões além do limite permanecem não verificadas.

Capacidades planejáveis: EXACT_ARITHMETIC, SYMBOLIC_ALGEBRA, NUMERICAL, FINITE_ENUMERATION, DETERMINISTIC, LEAN_CANDIDATE, SEMANTIC_RESIDUAL e REVIEW_ONLY. A escolha executável pertence ao servidor a partir do CheckSpec; o rótulo sugerido pelo LLM não despacha ferramentas. Cada resultado registra disponibilidade, necessidade de informação, razão, status, escopo e versão. Verificadores numéricos, enumeração genérica e Lean não são executados nesta etapa.

## 9. Consistência matemática

A camada determinística sinaliza claims contraditos, resultado final sem suporte verificado, resultados candidatos incompatíveis, candidatos ausentes, hipóteses inferidas, indeterminação, expectativas de unicidade incompatíveis e incertezas. Não escolhe a primeira solução para resolver conflito.

A normalização textual e a correspondência semântica entre enunciado e expressão declarada continuam sujeitos a revisão. Uma identidade falsa no CheckSpec pode representar erro de formalização da proposta, e não necessariamente falsidade de toda a solução em linguagem natural. Os resultados são apresentados com esse escopo.

## 10. Lean

A candidatura à formalização é armazenada por claim. Todos os resultados DY2 desta implementação registram `FORMAL_NOT_ATTEMPTED`. Não há caminho que produza `FORMAL_VERIFIED` nem declaração de problema integralmente formalizado. Lean não é requisito de READY_FOR_REVIEW.

## 11. Rubric Assistant

O botão de sugestão agora chama um provider real. Entrada: enunciado exato, preparação, candidatos/estratégias, análise, total, rubrica anterior e motivo opcional. A saída reutiliza `RubricContent`/`RubricCriterion`; não existe outro cadastro de rubricas.

Após validação determinística e uma segunda chamada de revisão semântica, publica uma nova `RubricVersion` como **DRAFT_AI**, com autoria AI e preparação exata. Nunca aprova nem ativa automaticamente. Regenerar mantém a versão anterior e registra predecessor, motivo e duas proveniências (geração e revisão).

## 12. Validação da rubrica

São reutilizadas as invariantes DY1: soma Decimal exata, pontos não negativos, máximo configurado, critérios não vazios na geração, IDs únicos, ordem contígua e dependências acíclicas válidas. Também são rejeitados vínculos inexistentes e descrições evidentemente duplicadas. IDs/estratégias referenciados precisam existir na preparação.

Critérios podem carregar objetivo matemático, claims relacionados, métodos aceitos, hints de verificadores e avisos. Dependência de claim não verificado gera warning.

`SemanticReview` registra sobreposição, vagueza, dependência impossível, informação ausente e exigência indevida de método único. Warnings permanecem visíveis; o parecer completo pode ser expandido. Um parecer LLM não é certificado matemático.

Durante a integração real, referências de claims em texto livre foram rejeitadas. O schema passou a usar `expected_key_claim_ids`. Também foi observada saída incompleta ao usar a expressão regular permissiva de Decimal no schema externo; a representação de transporte foi limitada a uma string decimal curta, enquanto a validação Decimal DY1 continua sendo a autoridade no servidor. Falhas anteriores permaneceram registradas no runtime de sondagem, sem conteúdo fictício substituto; [resumo das sondagens](assets/confia-dynamic-dy2/provider-probe-summary.json).

## 13. Revisão e aprovação docente

A UI oferece preparar/regenerar, inspecionar evidências, gerar/rejeitar e regenerar sugestão, editar, fornecer rubrica própria e aprovar. A edição cria TEACHER_EDITED, mantendo a origem da sugestão no histórico. Substituição integral por rubrica própria registra autoria docente e predecessor sem declarar a nova rubrica como geração AI.

Avisos relevantes bloqueiam a aprovação até reconhecimento explícito (`acknowledge_warnings`). O registro `Approval` preserva esse reconhecimento. Aprovar não transforma REVIEW_REQUIRED em READY, não remove contradições e não altera `automatic_correction_allowed=False`.

## 14. Proveniência e confiança

São persistidos provider, modelo solicitado/retornado, reasoning effort quando configurado, versões de prompt/schema, timestamps, hashes de input/output, resposta estruturada bruta, response ID, limite de output, SHA Git e hash do conteúdo dos módulos Dynamic. O hash de código representa também alterações ainda não commitadas. As verificações possuem versão própria.

Nenhuma chave/token é gravada. Erros externos são convertidos em códigos locais; mensagens arbitrárias de exceções não são expostas. O provider usa `store=False` e nenhuma ferramenta executável. O contrato segue a [documentação oficial de Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

Estados de confiança: CHECKED_WITHIN_SCOPE, HUMAN_REVIEW_REQUIRED, UNAVAILABLE. Em DY2 nenhum deles habilita correção automática. A consulta `/current` devolve a preparação do pacote aprovado exato e separa a preparação mais recente, impedindo mistura silenciosa após regeneração.

## 15. APIs e configuração

| Método/rota sob `/dynamic/problems/{problem_id}` | Comportamento |
|---|---|
| POST `/preparations` | Inicia nova preparação; exige expected_revision e aceita motivo. |
| GET `/preparations` | Lista versões e status efetivo/histórico. |
| GET `/preparations/{preparation_id}` | Interpretação, candidatos, estratégias, plano/resultados e proveniência. |
| POST `/rubric-suggestion` | Gera nova DRAFT_AI a partir da preparação atual especificada. |
| POST `/rubrics`, PATCH `/rubrics/{rubric_id}` | Rubrica docente/edição versionada DY1; admite substituição integral docente. |
| POST `/rubrics/{rubric_id}/approve` | Aprovação explícita com reconhecimento de avisos quando necessário. |
| GET `/current` | Pacote/rubrica/preparação aprovados exatos; latest_preparation separado. |
| POST `/statements` | Nova versão; preparação anterior histórica, pacote ativo removido. |
| POST `/corrections` | Continua 501: dynamic correction engine not yet implemented. |

Todas reutilizam autorização/ownership docente e optimistic concurrency. Sem acesso a problemas de outro professor; sem fallback Specialized. Endpoint inválido/versão stale não pode disparar uma geração sobre fonte diferente.

Provider: `CONFIA_DYNAMIC_LLM_ENABLED=1` e `OPENAI_API_KEY` no ambiente. Modelo default `gpt-4.1`, substituível por `CONFIA_DYNAMIC_MODEL`; `CONFIA_DYNAMIC_REASONING_EFFORT` é opcional e deve ser compatível com o modelo escolhido. Não há fallback para mock. Sem configuração, a UI conserva rubrica manual e declara indisponibilidade; tentativa de preparação registra FAILED/PROVIDER_NOT_CONFIGURED.

Para demonstração técnica local, usam-se as mesmas flags explícitas DY1 (`CONFIA_DYNAMIC_DEMO_ENABLED=1`, ambiente development, auth desabilitada). Isso não inventa identidade pessoal nem habilita demo em produção. Testes unitários injetam provider controlado por código; não existe uma flag de mock de produção.

## 16. UI

A mesma área `#teacher/dynamic` apresenta enunciado atual, domínio, hipóteses, candidatos, alternativas, warnings, plano/resultados e origem. Exibe loading durante chamadas reais, falha com retry explícito e histórico após reload/reinício. A rubrica apresenta critérios/pontos, vínculos da sugestão original, parecer semântico e ação de aprovação separada.

Conteúdo externo usa textContent. A UI não executa HTML ou código de saída do modelo. Os únicos ajustes visuais são estilos scoped ao painel existente e cache version dos assets. Não houve redesenho do produto ou mudança do frontend de correção.

## 17. Testes automatizados

Resultados finais e [comandos reproduzíveis](assets/confia-dynamic-dy2/validation-commands.txt) estão nas evidências anexas; [ambiente local](assets/confia-dynamic-dy2/environment.json): Python 3.9.6, sem dependência de outro worktree. A suíte Dynamic cobre lifecycle, binding, hashes DY1 preservados, claims/alternativas, aritmética e raízes em equações distintas, ambiguidade, conflito de candidatos, plano indisponível, limites de expansão, provider inválido/ausente, recuperação de interrupção, regeneração, autoria, aprovação explícita, autorização e corrida com mudança do enunciado.

Os testes do adapter simulam Responses sem rede, conferindo schema, ausência de ferramentas, configuração de timeout/retries, hashes e ausência de segredo na proveniência. Testes reais foram separados da regressão unitária e usados somente na validação manual.

Os testes JS cobrem os fluxos DY1 e DY2, loading, avisos, reconhecimento antes da aprovação, geração/regeneração, autoria docente, falha sem draft fictício e histórico SUPERSEDED.

## 18. Regressões e ambiente formal

- DY1/DY2 Python: **68 passed** (21 DY1 + 47 DY2), 11,51 s. Resultado em [python-dynamic.txt](assets/confia-dynamic-dy2/python-dynamic.txt).
- Plataforma compartilhada/TME/D1–D7: **407 passed, 2 failed**, 153,59 s. [Log](assets/confia-dynamic-dy2/python-platform.txt).
- Contratos matemáticos/assets/catálogo/fronteira pública: **375 passed, 2 skipped**, 6,98 s. [Log](assets/confia-dynamic-dy2/python-contracts.txt).
- JavaScript completo: **530 passed**, incluindo **11 testes Dynamic** (5 DY1 + 6 DY2). Resultado em [js-regression.txt](assets/confia-dynamic-dy2/js-regression.txt); recorte Dynamic em [js-dynamic.txt](assets/confia-dynamic-dy2/js-dynamic.txt).

As duas falhas formais são:

1. `test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`.
2. `test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved`.

Ambas foram reproduzidas com o composition root de HEAD carregado em memória excluindo somente o import/include Dynamic; arquivos Specialized permaneceram inalterados. [Reprodução](assets/confia-dynamic-dy2/python-formal-baseline.txt), [script](assets/confia-dynamic-dy2/baseline-probe.txt).

`lake build` falhou no checkout local do Mathlib `8f9d9cff6bd728b17a24e163c9402775d9e6a365`: `external command 'git' exited with code 1`. [Log](assets/confia-dynamic-dy2/lean-build.txt). Não foi corrigida mediante dependência de outro worktree nem alteração de expectativas. A validação formal não está verde. Não foi executada a suíte Python integral; foram executados os recortes relevantes documentados.

## 19. Validação real no navegador

Validação em `http://127.0.0.1:8767/#teacher/dynamic`, com identidade `TECHNICAL_DEMO`, provider real OpenAI, modelo retornado `gpt-4.1-2025-04-14`. Não foram usados mocks nem respostas preparadas por problema no servidor de demonstração.

1. **Equação quadrática:** `Resolva x² - 5x + 6 = 0`. Preparação retornou fatoração e fórmula quadrática, raízes 2/3 corroboradas por checagens exatas e alerta de domínio inferido. Rubrica DRAFT_AI foi editada (TEACHER_EDITED), avisos reconhecidos e aprovação explícita registrada. Trust permaneceu HUMAN_REVIEW_REQUIRED. [Aprovação/histórico](assets/confia-dynamic-dy2/01-approved.jpg).
2. **Ambiguidade:** `Um retângulo tem perímetro 20 cm. Qual é sua área?`. REVIEW_REQUIRED; falta de dados, não unicidade e hipótese de quadrado não fornecida ficaram visíveis. A sugestão DRAFT_AI manteve os avisos e a aprovação bloqueada até revisão explícita; não foi aprovada. [Evidência](assets/confia-dynamic-dy2/02-ambiguity.jpg).
3. **Métodos alternativos:** `Resolva, em R, 2y² - 14y + 24 = 0, por um método de sua escolha.` READY_FOR_REVIEW, raízes 3/4, fórmula quadrática e fatoração. Sugestão DRAFT_AI com pontos 3/3/4, aceitando S1/S2 em todos os critérios; a revisão semântica sinalizou possível sobreposição/vagueza, visível antes da aprovação. Não foi aprovada. [Fluxo completo](assets/confia-dynamic-dy2/03-alternative-methods.jpg), [detalhe legível](assets/confia-dynamic-dy2/03-alternative-methods-detail.jpg).
4. **Mudança posterior do primeiro enunciado:** versão 2 exige nova preparação; preparação V1 e rubrica aprovada V2 ficaram SUPERSEDED, sem pacote ativo, inclusive após recarga. A aprovação histórica permanece registrada. [Histórico após reload](assets/confia-dynamic-dy2/04-superseded-after-reload.jpg).

O console após recarga não apresentou erros. O servidor local foi encerrado ao final. O registro estruturado final conserva snapshots, hashes e observações dos três cenários: [browser-validation.json](assets/confia-dynamic-dy2/browser-validation.json). Saídas de modelos são candidatas; inclusive propostas com problemas matemáticos/semânticos ficam sinalizadas, sem serem promovidas a verdade confiável.

## 20. Limitações e arquivos alterados

Limitações: preparação textual; detecção semântica por LLM não exaustiva; parser e verificadores deliberadamente limitados; não há CAS geral, solver universal, checagem de diagramas, verificação numérica/enumeração genérica executada ou Lean executado. Correspondência entre linguagem natural e CheckSpec exige revisão. Revisão semântica usa o mesmo provider e não constitui independent reviewer de correção.

As gerações podem falhar por timeout, recusa, saída incompleta ou invalidade de referências/pontos. Não são reparadas silenciosamente. Um request interrompido não dispõe de worker durável; uma nova tentativa recupera seu estado após o prazo. Armazenamento continua baseado em snapshots completos, adequado ao vertical slice, sem pretensão de escala ilimitada. Rubricas docentes avançadas ainda dependem de API para alguns campos; a UI inspeciona os vínculos gerados.

Arquivos existentes alterados: `dynamic/models.py`, `dynamic/store.py`, `dynamic/router.py`, `static/dynamic.js`, `static/dynamic.css`, `static/index.html`, testes DY1 Python/JS somente para a disponibilidade agora real de sugestão. Novos: quatro módulos listados na seção 2, `tests/test_dynamic_dy2.py`, `tests/js/test_dynamic_dy2.cjs`, este relatório e suas evidências.

Main, CorrectionEngine, AuditService/AuditRun, PautaEngine, registries, checkers, toolchain/manifesto Lean, fixtures Specialized, benchmarks e relatórios anteriores não foram alterados.

## 21. Próximo DY3 e veredito

DY3 deverá consumir referências imutáveis de pacote/enunciado/rubrica/preparação, validar aprovação e trust state, separar claims de aluno das referências candidatas e respeitar métodos equivalentes. A presença de rubrica aprovada não autoriza transformar preparação incerta em correção automática. O adapter de correção e sua integração AuditRun permanecem fora de DY2.

O escopo DY2 foi implementado: preparação automática real, verificações limitadas explícitas, sugestão versionada, revisão semântica, aprovação docente e evidência histórica. A limitação formal de ambiente está documentada separadamente.

READY_FOR_DYNAMIC_DY3
