# ConfIA Dynamic — DY7 — implementação de certificação 01

12/11/2026. Implementação experimental em `SHADOW_EVALUATION`; resultado científico separado no [benchmark 01](CONFIA_DYNAMIC_DY7_BENCHMARK_01.md). Nenhuma declaração de certificação geral ou produção.

## 1. Frozen base SHA

Worktree exclusivo `/Users/LinMarcolino/Documents/confia-lean-auditor-dynamic`, branch `feat/dynamic-correction`. Base limpa ao iniciar: `caa5da88bc7a1f21ab7bd0a17a35e28c33af1cf8` (DY6), descendente da base oficial `cb1df6e381fd0214092f33afe554ce506da68c78`. O HEAD foi preservado. Não houve `git add`, commit, outro worktree ou subagente.

Código da aplicação no benchmark: `a55f5f0fd58257e1fe926c4c5e6367f71d5664712f85ddeda9c9cc1fa0c17cd6`. `git_dirty=true` é explícito. [Manifesto e hashes](assets/confia-dynamic-dy7/frozen-source-manifest.json), snapshot dos arquivos modificados/novos e patch dos arquivos rastreados permitem recuperar o código experimental sem confundi-lo com o SHA da base.

## 2. Arquitetura de certificação

Estende `tme/certification_gold.py`, `certification.py` e o router D7. Reutiliza ownership, opt-in, cadeia selada de gold, projeção de auditorias, eventos, CSV/JSON, HumanDecision e FinalCorrection. Os módulos `certification_dynamic`, `certification_experiment_metrics`, `certification_models`, `certification_runs` e `certification_paired` são adaptadores dentro da certificação compartilhada; não constituem outro sistema de gold.

D7 antes fornecia export de estado corrente, sem protocolo congelado ou run experimental persistido. O DY7 acrescenta datasets e runs imutáveis no mesmo diretório `.certification` por Assessment. A execução identifica código, ambiente, gold e dataset. Não publica notas oficiais.

## 3. HumanGold

A mesma cadeia D7 registra versões, source_id, dataset_version, importador/data, predecessor e hashes. Dynamic exige binding explícito de QuestionAttempt, TranscriptionVersion, enunciado e rubrica, além de avaliador, timestamp e referência humana/sintética. Assessment, participante pseudônimo, questão, máximo e score continuam no registro compartilhado.

Gold por critério, quando informado, cobre toda a rubrica aprovada, com IDs, máximos, pontos e soma coerentes. Comentário/adjudication status são opcionais. Ratings A/B independentes e adjudicação cabem no modelo; múltiplos avaliadores não são exigidos para fixtures. O gold final é informado, nunca inferido de HumanDecision. Campos adicionais ausentes são omitidos na serialização, preservando os hashes dos datasets legados.

## 4. Blind evaluation

Importação pode ocorrer antes da primeira auditoria: a validação lê a rubrica aprovada e não exige score observado. O registro exige `blind` e `blindness_note`; ratings também informam cegamento/independência. A consulta à área Resultados expõe scores e deve ser declarada pelo avaliador. Não se afirma controle institucional de cegamento pela aplicação.

O piloto usa `SYNTHETIC_FIXTURE`, sem avaliador humano independente, `blind=false`; o autor conhecia a definição das fixtures. O reviewer recebe o payload cego DY4 existente, sem G0, gold ou split.

## 5. Dataset splits

DEV, VALIDATION e HOLDOUT por caso. Metadata inclui group_id, origem, domínio, dificuldade e base dessa dificuldade, tipo de solução. Grupos/participantes não atravessam splits; respostas textuais idênticas ao mesmo enunciado não podem atravessá-los. Reuso de tentativa/holdout já registrado é rejeitado.

HOLDOUT é congelado antes de auditorias, com gold fixo. Run confere cronologia, transcrição, contexto, hash da aplicação, configuração dos providers, dependências Python e hashes de manifests/toolchain. O protocolo do harness registra também hash do dataset textual e do próprio script. Existe uma única execução por dataset; alterações exigem novo protocolo/dataset. Não houve tuning após observar o HOLDOUT 01.

## 6. Grader metrics

G0 usa o AuditRun original; não substitui seu score pelo G2. Métricas: N comparável, MAE, RMSE, bias, exata, tolerâncias inclusivas ±1/±2 e erro absoluto normalizado. Casos sem gold válido, sem score ou com falha técnica não entram silenciosamente nas médias. Artefatos originais permanecem inalterados.

## 7. Reviewer metrics

G1 é a proposta independente após checagens DY4, com ID/hash, versão, provider/model/config e prompt/schema. Critérios conhecidos podem ser avaliados mesmo quando o total permanece indeterminado. Comparações de valor G0×G1 exigem pares com scores determinados; N é exposto. Erros sinalizados, false alarms, missed errors, alternativas melhoradas e acordo errado usam a definição operacional documentada.

No HOLDOUT deste piloto, G1 ficou indeterminado; N de pares G0×G1 foi zero. Seus contadores não demonstram melhoria nem ausência de erros. A infraestrutura mede os casos disponíveis, não fabrica um score para preencher a tabela.

## 8. Reconciliation metrics

G2 é lido do artefato DY5 associado ao reviewer corrente, mantendo G0 e G1 separados. Calcula erros corrigidos/introduzidos, falso crédito removido, crédito legítimo recuperado e pontos removidos/recuperados. Acordo de agentes não é truth label: o gold continua independente, inclusive no teste de totais iguais com critérios errados.

No HOLDOUT, G0 e G2 mantiveram o mesmo desempenho. Não se declarou benefício da reconciliação apenas porque o pipeline concluiu.

## 9. False credit

Compara pontos no mesmo critério: previsão maior que gold, inclusive excesso parcial. Exporta contagem, taxa sobre todos os pares comparáveis, pontos excedentes, severidade normalizada e primeiro estágio observado com excesso. Não reutiliza a métrica binária de presença de crédito D7 como substituta dessa definição.

## 10. Missed credit

Definição simétrica: previsão menor que gold. Reporta critérios afetados, taxa, pontos perdidos e recuperação entre estágios. O piloto encontrou perda relevante de crédito; os dados permaneceram intactos, sem heurística adicionada para melhorar o HOLDOUT.

## 11. Automation coverage

Scores disponíveis, sem revisão e sem falha técnica, divididos por todos os casos registrados. Falhas continuam reduzindo a cobertura operacional. A homologação oficial permanece humana; “automático” aqui descreve a fronteira de sugestão DY5, não publicação automática de nota.

## 12. Selective risk

Métricas globais do estrato, de automáticos e de revisados permanecem separadas. Unsafe automation exige gold comparável e erro total ou por critério maior que o limiar experimental do protocolo (>1 ponto neste piloto). Não há estimativa de risco quando nenhum caso foi automatizado.

Review precision usa labels independentes explícitos de necessidade de revisão. Review usefulness compara G3 e G2 com gold nos casos revisados; não é inferência causal. As limitações dos labels sintéticos e da decisão G3 pré-declarada estão detalhadas no benchmark.

## 13. Profiles

FORMATIVE_LIST e SCHOOL_EXAM permanecem separados, inclusive nos gates. Os mesmos casos sintéticos foram avaliados nos dois perfis, sem tratá-los como observações independentes adicionais. Origem SYNTHETIC/CURATED/REAL_STUDENT também não é agregada em um único número. Estratificação por domínio, dificuldade/basis, tipo de solução e checker está nos exports.

## 14. Human override

Taxa G3≠G2, média assinada do delta, ajustes para cima/baixo e presença de justificativa. A decisão não vira gold e override não prova erro do sistema. G3 não recebe uma distribuição inventada por critério. No piloto, decisões G3 são sintéticas e coincidem com os rótulos por construção; não se mediu comportamento real de professores.

## 15. Technical failures

Falhas de provider/checker, códigos originais de erro e incerteza técnica são separadas de erro matemático. Estágio ausente permanece UNAVAILABLE; score ausente permanece nulo. Erro de persistência impede publicação do run. Exclusões e contagens operacionais permanecem disponíveis.

O benchmark local e o DEV real concluíram sem falha técnica. As quatro falhas Lean da regressão continuam registradas separadamente. O bloqueio inicial do teste externo pela revisão automática foi resolvido por autorização específica do usuário; a chamada só foi executada depois dela.

## 16. Version fidelity

Gold é ligado à transcrição, enunciado e rubrica. Divergências são exclusões estruturadas e retiradas também das métricas D7 genéricas, evitando comparação silenciosa com gold incompatível. Nova versão de gold não altera run já publicado. Código/configuração alterados após freeze bloqueiam um novo run daquele protocolo. Retry não substitui conteúdo; tampering quebra o selo e é rejeitado.

## 17. Specialized × Dynamic

Harness pareado lê auditorias reais, valida ownership, braço Specialized legítimo, mesmo texto, enunciado catalogado, máximo e referência. Mantém outputs/provenance separados e não fornece internals Specialized ao Dynamic. END_TO_END e COMMON_RUBRIC são distintos; pauta comum exige equivalência explícita e verificável. Métricas por critério exigem alinhamento completo justificado; sem isso, ficam indisponíveis.

Métricas pareadas e rejeição de caso real incompatível foram testadas. **N comparável observado no benchmark = 0**: os problemas novos não possuem configuração Specialized legítima. Não foi fabricada uma comparação nem alegada superioridade.

## 18. Statistical methods

Comparações Decimal; bootstrap de MAE com 1.000 reamostragens por grupo e semente persistida, apenas quando há pelo menos 20 grupos. Abaixo disso, N e PILOT_SMALL_SAMPLE. O mínimo é convenção prudencial de relatório, não certificado de validade. Sem teste de superioridade. Inter-rater: N de pares independentes, acordo exato e MAE; ICC/kappa não foram adicionados sem necessidade metodológica.

## 19. Exports

JSON versionado inclui estágios, critérios, provenance, contexto, hashes, métricas/estratos, exclusões, eventos D7, FinalCorrection e ambiente. CSV por estágio inclui critérios/checkers serializados, IDs, versões, origem/split, código e scores; proteção contra fórmulas CSV é preservada. Relatório Markdown separado do relatório de implementação.

[Protocolo operacional e APIs](../integration/DYNAMIC_CERTIFICATION_PROTOCOL.md), [resultados completos](CONFIA_DYNAMIC_DY7_BENCHMARK_01.md), [FORMATIVE_LIST JSON](assets/confia-dynamic-dy7/benchmark/FORMATIVE_LIST.json), [SCHOOL_EXAM JSON](assets/confia-dynamic-dy7/benchmark/SCHOOL_EXAM.json), [DEV real JSON](assets/confia-dynamic-dy7/live-dev/FORMATIVE_LIST.json).

## 20. UI

Reutiliza a área Certificação: G0–G3, N, MAE, exata, falso/crédito perdido, revisão, cobertura, risco, override e falhas. Histórico de execuções imutáveis oferece JSON, CSV e Markdown, com status shadow e estratos visíveis. Não há dashboard corretivo novo. Gold Dynamic pede JSON com bindings/evaluation; o fluxo D7 Specialized permanece disponível.

Validação no navegador em dados DEV: prova → resumo → Certificação → Estado atual → Execuções experimentais → métricas da execução. Ausência de score não aparece como zero, e a origem sintética é explícita. [Registro de QA](assets/confia-dynamic-dy7/browser-qa.md). O servidor foi encerrado.

## 21. Tests

- **20 testes DY7**, incluídos na última validação de **43 testes DY7 + D7 compartilhado**, todos aprovados. Cobrem gold, cegamento declarado, múltiplos raters, métricas, separação de estágios, critérios parciais, acordo errado, limites de gates, splits, congelamento, configuração, adulteração, exclusões, exports, comparação pareada e preservação histórica. [Log final](assets/confia-dynamic-dy7/python-integrity-final.txt).
- **564 testes JavaScript aprovados**, incluindo UI DY7 e regressão Specialized. [Log](assets/confia-dynamic-dy7/javascript-full.txt).
- Harness local: 48 tentativas, 24 FinalCorrections, dois runs congelados, exports completos. Aprovação técnica sintética é identificada; nenhuma captura real/OCR foi necessária.
- Provider real: uma amostra DEV autorizada, `gpt-4.1-2025-04-14`, preparação/reviewer reais, configuração/provenance persistidas, sem falha técnica. Não é requisito dos testes unitários e não integra o HOLDOUT local.

## 22. Regression

Regressão serial em 36 arquivos: **1.167 passaram, 14 skips e quatro falhas Lean/Mathlib**. Abrange DY1–DY7, D1–D7, Specialized/TME, correction engine, certification e contratos compartilhados. [Lista](assets/confia-dynamic-dy7/regression-files.json), [log](assets/confia-dynamic-dy7/python-regression.txt).

A execução ampla antecedeu os últimos refinamentos de metadados/eventos e fingerprint de ambiente. A validação final de 43 testes cobre esses refinamentos. Resultados de execuções diferentes não foram somados. Nenhuma expectativa Specialized foi alterada. `git diff --check` passou.

## 23. Lean/Mathlib status

Classificação dos quatro testes: **environment failure** observada; a regressão matemática formal permanece não avaliada até o ambiente funcionar.

| Teste | Observação DY7 |
|---|---|
| `tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline` | technical_error no lugar do resultado formal |
| `tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved` | status formal esperado não produzido |
| `tests/test_tme_hybrid_grader.py::test_wrong_reasoning_correct_final_is_refuted_by_real_lean` | technical_error no lugar de refuted |
| `tests/test_tme_hybrid_grader.py::test_real_formal_verified_is_preserved_and_not_semantic` | technical_error no lugar de FORMAL_VERIFIED |

O diagnóstico detalhado preservado do DY6 registra falha de checkout de `8f9d9cff6bd728b17a24e163c9402775d9e6a365`. A inspeção atual encontrou HEAD Mathlib `ab19bac90981b27f5380941f4b36617e738358c9`, 9.490 exclusões staged e 18 entradas não rastreadas na dependência. Esse estado foi preservado; não houve reset/checkout destrutivo, migração de dependências ou mudança de produto para deixar testes verdes. A causa específica de cada alteração local não foi inferida.

[Classificação atual](assets/confia-dynamic-dy7/formal-validation.json), [stderr detalhado preservado do DY6](assets/confia-dynamic-dy7/formal-evidence-from-dy6.json). Repetir os quatro node IDs acima quando o ambiente for reparado; não interpretar esta entrega como validação Lean aprovada.

## 24. Limitations

Piloto sintético pequeno, uma família matemática, dificuldade estimada, sem respostas reais ou raters humanos independentes. HOLDOUT de respostas em questões repetidas. Sem inferência estatística, equivalência causal, comprovação de ganho do reviewer, automação segura ou comparação empírica Specialized × Dynamic. O teste live tem N=1 e pauta fixada pelo protocolo.

Os controles de freeze ajudam a impedir reuso silencioso, mas não substituem governança científica ou isolamento institucional de HOLDOUT. Comparações de valor do reviewer exigem scores comparáveis; abstenções são expostas como ausência, sem métricas de melhora fabricadas. Gates são configuráveis e pré-declarados, sem thresholds institucionais inventados. Captura permanece `CAPTURE_INTEGRATION_READY`; OCR/HTR, storage, segmentação e IAM não foram desenvolvidos.

## 25. Next-step recommendation

Usar a infraestrutura em shadow. Investigar a perda de crédito em um conjunto DEV novo, reunir referências humanas cegas e adjudicadas, escolher um subconjunto realmente comparável para Specialized e pré-registrar gates científicos. Qualquer ajuste deverá ter nova versão e novo HOLDOUT; o resultado 01 fica congelado. Reparar o ambiente Lean/Mathlib preservando alterações locais e repetir a validação formal.

Veredito experimental: **PILOT_METRICS_AVAILABLE**, com MAE G2 4,25/10 e 0% de automação no HOLDOUT de cada perfil. Isso não sustenta implantação automática. Estado Git final: [git status --short](assets/confia-dynamic-dy7/git-status.txt).

DYNAMIC_DY7_FUNCTIONALLY_COMPLETE_SHADOW_VALIDATION_READY
