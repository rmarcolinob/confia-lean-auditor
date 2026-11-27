# Fase 3 — DYNAMIC, cobertura e limites (27/11/2026)

Base `923bf3acbd9994af9662bcdff6b18eac1b6d4df9`, branch `codex/validate-dynamic-pre10dez`. **APROVADO COM LIMITAÇÕES para integração offline; julgamento semântico real ainda não validado.** Nenhum motor, checker, política, peso, rubrica aprovada ou contrato de produção foi alterado neste PR. O corpus sintético testa os serviços existentes, não adiciona regras específicas para obter notas.

## Caminho efetivamente existente

| Componente | Contrato e participação efetiva | Limite |
|---|---|---|
| `dynamic/store.py`, `models.py` | Enunciado novo, critérios, pesos e níveis aprovados → versões imutáveis, hashes, pacote de correção | Aprovação manual disponível sem IA; autorização e revisão esperada continuam exigidas |
| `preparation.py::PreparationService.start/suggest` | Enunciado versionado → proposta, análise delimitada, sugestão/revisão de rubrica com proveniência | Depende de provider para gerar propostas; falha permanece `FAILED`, sem proposta inventada. Geração docente também revisa a rubrica; não é aprovação automática |
| `grader.py::DynamicSolutionGrader.grade` | Solução, pacote/rubrica fixados, contexto → claims, evidências, verificações, decisões e pontuação provisória | Extração determinística é limitada; a solução integral fica disponível à avaliação semântica |
| `semantic.py::augment` e `review_phase` | Critério + solução/rubrica/evidências → decisão estruturada, citações e nível autorizado | LLM não escolhe peso livre. Metadados ausentes não são inventados. Providers simulados são identificados como tal |
| `reviewer.py::IndependentDynamicReviewer.analyze` | Primeira passagem independente, evidências e critérios → parecer por critério | Parecer de LLM não é prova formal; independência de entrada não implica independência estatística entre modelos |
| `semantic.py::reconcile`, `reconciliation_service.py::ReconciliationService.execute` | Grader + Reviewer + versões → concordância/divergência, pendências, pontuação conciliada e eventos | Divergência não vira concordância por arredondamento nem ajuste artificial. Erro técnico não vira erro matemático |
| `semantic_credit.py`, `dependencies.py`, adjudicação e serviços escolares existentes | Níveis autorizados/dependências → limites de crédito e decisão docente vinculada | Crédito parcial não elimina erro declarado; dependência ambígua preserva revisão; confirmação humana permanece separada |

As regressões existentes cobrem preparação, aprovação, fontes/versionamento, crédito parcial, dependências, divergência 5/10 versus 10/10, falhas, abstenções, preservação de verificações exatas, adjudicação e privacidade nos três contextos. Nenhum caminho paralelo foi criado.

## Onde termina a verificação exata

`verification.py` verifica estruturas polinomiais univariadas com coeficientes racionais e limites explícitos, incluindo identidades e conjuntos de raízes quando o contrato permite. Há limites de grau e tamanho dos coeficientes. Isso não certifica o significado global de um problema discursivo.

`grader.py::problem_equation` exige enunciado de equação real em formato delimitado, sem condições extras descartadas, e trata graus 1/2 com raízes racionais. Raízes irracionais, restrições adicionais, redação não suportada ou outro tipo de problema saem desse caminho. `criterion_policy` só aplica a correspondência determinística aos critérios expressamente reconhecidos; notas/orientações adicionais impedem presumir equivalência. Não ampliar essas regras por palavra-chave evita conceder crédito incompatível com a rubrica.

Conjuntos, intervalos, argumentos sobre funções, juros, geometria e trigonometria discursiva normalmente dependem do Grader/Reviewer semânticos. Essa dependência é arquitetural e não exige programação individual, mas sua confiabilidade precisa de teste real. **O caminho DYNAMIC inspecionado não executa Lean: `FORMAL_NOT_ATTEMPTED`.** Não se transfere para ele a certificação Lean parcial do SPECIALIZED.

## Matriz curricular sintética

`tests/fixtures/dynamic_highschool_topics.json`: 16 enunciados inéditos para os serviços, cada um com solução correta, parcial, incorreta e alternativa. Abrange conjuntos, intervalos, porcentagem, razão, proporção, funções afim/quadrática/modular/exponencial/logarítmica, equação, inequação, juros simples/compostos, área e trigonometria retangular. A escolha do ano escolar é de escopo inicial, não uma alegação de cobertura curricular completa.

`tests/test_dynamic_highschool_topics.py` cria problemas e rubricas pelo serviço ordinário, sem registrar checker ou teorema. Usa um critério genérico com nível parcial explicitamente aprovado: 2 integral, 1 inicial, 0 não atendido, pendente em `review`/falha. **Esses valores vêm dos pareceres simulados do teste e dos níveis da rubrica; não demonstram que um LLM reconhece a matemática das amostras.** As quatro classificações do corpus foram redigidas nesta intervenção e não são gold humano independente.

- **96 integrações com provider explicitamente simulado**: seis estados/variantes × 16 temas. Verificam chamadas reais aos serviços, solução integral, rubrica vinculada, Grader/Reviewer/Reconciliation, nota e proveniência. Os rótulos `correct/incorrect` e respostas-alvo não são campos enviados ao provider.
- **16 execuções com provider realmente desabilitado**: raciocínio novo não verificável permanece pendente, com incerteza técnica e sem `llm_used=true`. `AuditRun.COMPLETED` significa que a execução técnica produziu um registro, não que existe nota final. Não se afirma que todas as questões inéditas sempre dependem de IA: a rubrica de raciocínio desses testes deliberadamente requer avaliação semântica.
- **840 aprovados, 2 skips**, 374,53 s: todos `test_dynamic*.py`, integração de dezembro, TME mínimo e compatibilidade de transporte. Os 112 testes novos estão incluídos, não devem ser somados novamente.
- Gate de orçamento: **13 aprovados**, transporte exclusivamente local. A opção adicional `--text-only` bloqueia OCR antes do transporte e dispensa suas credenciais; o plano antigo permanece inalterado por padrão.

[Resumo estruturado](evidence/dynamic/offline-results.json). Comandos:

```sh
PYTHONPATH=app:tests python -m pytest -q tests/test_dynamic*.py tests/test_dec10_integration.py tests/test_tme_minimal_functional.py tests/test_tme_model_compat.py
PYTHONPATH=app python -m pytest -q tests/test_rc1_smoke_budget.py
python scripts/evaluation/dynamic_rc1_smoke.py --text-only
git diff --check
```

Os dois skips preexistentes de `test_tme_model_compat.py` exigem o pacote DEV congelado local ausente: dry-run dos hashes de transporte e proteção de IDs do holdout. Não há teste pago implicitamente aprovado nem skip novo. A ocorrência histórica intermitente P3 continua registrada; a correção técnica separada reproduz um mecanismo compatível, sem atribuir retrospectivamente uma causa que os logs antigos não preservaram.

## Pendências e recomendação

1. **Bloqueia declaração de corretor semântico plenamente validado:** não houve LLM real, gold humano independente nem medição real de custo/latência. Os **21 casos históricos permanecem pendentes**. Executar primeiro o [smoke textual controlado](SMOKE_TEXTUAL_POSTERIOR.md), somente após autorização específica; depois corpus independente e métricas por critério.
2. Limitação operacional: providers indisponíveis impedem a geração autônoma de rubrica e a resolução de critérios fora do verificador exato. A alternativa docente manual e a adjudicação continuam disponíveis; não são substitutos ocultos de um LLM real.
3. Limitação científica: concordância entre Grader/Reviewer não mede verdade matemática; alternativas válidas, justificativas insuficientes, erros sutis e dependências precisam de avaliação humana cega. Não programar verificadores por amostra nem ajustar notas às referências.
4. Luis mantém responsabilidade por OCR/reconhecimento/segmentação. Esta intervenção não usa imagens nem altera captura, transcrição, armazenamento ou seus contratos. Rian recebe serviços existentes e evidências de integração, não uma nova arquitetura.

A etapa pode ser revisada como estabilização experimental. Não autoriza uso escolar autônomo nem afirma cobertura matemática universal. Main, SPECIALIZED-TME2-RC1 e dados históricos permanecem intactos.
