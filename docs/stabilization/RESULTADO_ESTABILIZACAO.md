# Estabilização do ConfIA — resultado da intervenção

27/11/2026. Base de todas as frentes: `923bf3acbd9994af9662bcdff6b18eac1b6d4df9`. Diagnóstico de origem: [PR #6](https://github.com/rmarcolinob/confia-lean-auditor/pull/6), sem reescrita de seus resultados históricos.

| Fase | Estado local | Evidência e entrega |
|---|---|---|
| 1. Técnica | **APROVADO COM LIMITAÇÕES** | [PR #7](https://github.com/rmarcolinob/confia-lean-auditor/pull/7): timeout de canonização por pausa do escalonador reproduzido em P3/P4; orçamento por CPU da thread e diagnóstico seguro. 905 Python, 631 JS, build Lean e certificados reais aprovados. Não prova a causa individual das falhas históricas cujos logs perderam a exceção |
| 2. SPECIALIZED | **APROVADO COM LIMITAÇÕES** | [PR #8](https://github.com/rmarcolinob/confia-lean-auditor/pull/8): RHS de cadeia de igualdades atribuído corretamente no ITA; citações/hipóteses/rejeições e Lean preservados. 668 Python aprovados em três baterias, quatro skips por artefatos locais ausentes. F2Q6 já encaminha maximização à semântica na política atual; sem provider permanece pendente |
| 3. DYNAMIC | **APROVADO COM LIMITAÇÕES** | [Relatório](FASE3_DYNAMIC.md): 16 temas, 112 casos novos dentro de 840 regressões aprovadas; dois skips DEV. 13 testes do gate de smoke. Sem alterações no núcleo; sem alegação de validação semântica real |
| 4. Plataforma | **APROVADO COM LIMITAÇÕES** | [PR #9](https://github.com/rmarcolinob/confia-lean-auditor/pull/9): decisões escolares TME/DYNAMIC na Gestão e catálogo por perfil. 140 Python e 631 JS; HTTP institucional completo, retomada em processos novos e navegador com dados sintéticos |
| 5. Semântica real e avaliação independente | **BLOQUEADO PARA CONCLUSÃO CIENTÍFICA** | [Smoke textual preparado](SMOKE_TEXTUAL_POSTERIOR.md), não executado. Requer autorização de modelos, corpus, chamadas e orçamento; gold humano separado. **21 casos históricos ainda pendentes** |

As contagens acima são por bateria e têm sobreposição entre PRs; não são um total de testes únicos. Nenhum skip/xfail novo foi criado para contornar falhas. O xfail legado da extração lexical F2Q6 permanece identificado; sua limitação não foi escondida por um certificado de referência.

## O que foi e não foi comprovado

- **Determinístico real:** parsing, proveniência literal, estruturas matemáticas suportadas, PautaEngine, estados, hashes, versões, idempotência e permissões. Soluções e dados são sintéticos ou fixtures já versionadas.
- **Lean real:** build e certificados delimitados no SPECIALIZED, inclusive prova/refutação e detecção de certificado adulterado. Isso não é formalização global das questões. **Nenhuma execução Lean atribuída ao DYNAMIC.**
- **Integração simulada:** avaliações Grader/Reviewer e estados fornecidos por providers de teste verificam aplicação de rubrica/reconciliação/feedback. Não medem a capacidade do modelo de compreender as soluções.
- **Fluxo HTTP real sem provider:** atividade digitada institucional, adjudicação humana explícita, divulgação e consulta do aluno. A nota humana não é apresentada como nota automaticamente obtida pelo motor.
- **Replay arquivado:** P1 continua 17/20, com respostas reais antigas; não é nova execução de provider. TME P1–P5 permanecem cobertos por fixtures e regressões, não por gold novo independente.
- **Semântica atual real e gold independente:** não executados nesta intervenção. Não declarar o SPECIALIZED/DYNAMIC universalmente corretos, cientificamente validados ou prontos para correção escolar autônoma.

## Pendências reais para entrega operacional

1. **Prioridade P1 / validação bloqueante:** confirmar o comportamento real do fallback e do Grader/Reviewer nas soluções independentes. Não é possível substituir essa evidência por mais mocks. O smoke textual controla no máximo 21 chamadas LLM, zero OCR e reserva herdada de US$ 5,24, com teto proposto de US$ 6,00 e tarifas/modelos a reconfirmar antes da autorização.
2. **Prioridade P1 / investigação histórica:** P3/P4 não têm causa retrospectiva definitivamente demonstrada. A regressão do mecanismo reproduzido e os novos logs reduzem o risco e tornam recorrências diagnosticáveis; acompanhar CI sem apagar o histórico anterior.
3. **Prioridade P2 / operação:** indicadores legados de execução não são indicadores de reconciliação matemática final; agregação lê históricos e ainda não foi testada em carga. Estudo autônomo depende de provider para preparar problemas, e sua mensagem genérica de ambiguidade pode aparecer junto de falha técnica. TutorIA mantém áreas demonstrativas explicitamente identificadas.
4. **Responsabilidade de Luis:** OCR, reconhecimento manuscrito e segmentação avançada fora do escopo. Entrada mínima, armazenamento, transcrição e integridade preservados, sem arquitetura paralela.
5. **Integração por Rian/equipe:** revisar os PRs independentes e os workflows de seus commits. Não houve merge; main continua a base original. Só após revisão integrar as correções e executar o smoke autorizado. Melhorias de escala e UX não substituem o gate científico.

## Proteções

Sem chamadas pagas, dados reais de estudantes, alteração de pautas/pesos/políticas/PautaEngine, novos verificadores por amostra, commits na main ou merges. A tag anotada `SPECIALIZED-TME2-RC1` continua no objeto `0c64e318a26e21f71fe3097c66ee17a5206dd8a3`, apontando para `c03403fe5b83d9db9df172882bd69af3dfa2d027`. Artefatos operacionais temporários ficaram fora do Git; apenas corpus e capturas sintéticas, hashes e relatórios foram publicados.

Os workflows completos dos PRs são uma condição adicional de integração. Os estados locais desta tabela não antecipam seu resultado. Preservar a main até a revisão e não congelar uma nova versão científica com pendências tratadas como validação concluída.
