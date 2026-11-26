# DYNAMIC-RC1 — manifesto candidato e parecer de prontidão

Data: 26/11/2026. Base: `fc6f271ab4f484f48609ddde67faa84b0ac690ca`, branch `codex/dynamic-development`, limpa no início. **Preparação experimental, sem tag, commit, push ou merge nesta etapa.** Nenhuma funcionalidade matemática, rubrica aprovada, checker, política de crédito ou decisão histórica foi modificada.

## Identificação e reprodução

O [manifesto JSON](assets/dynamic-rc1/manifest.json) e seu [SHA-256](assets/dynamic-rc1/manifest.sha256) registram inventário/hash dos arquivos do código base, testes, ambiente, prompts, schemas, amostras e documentação desta preparação. O fingerprint `dynamic-candidate-content.v1:<sha256>` deriva do JSON canônico dos caminhos rastreados em `app/` e hashes de seus bytes. Abrange backend, integrações e frontend; **é uma identificação documental nova**, não uma alteração de `AuditRun.auditor_version`. Este último continua `dynamic-grader.r1` no caminho institucional. Não se reescrevem auditorias para inserir o fingerprint.

Fingerprint calculado para esta base: `dynamic-candidate-content.v1:6e1c846b198e1fdceb374db1eed90a4024ba6019c83a09cfc69ce487bfa741a5`. O verificador do manifesto passou com conferência de ambiente; uma alteração simulada no hash de arquivo foi rejeitada, sem alterar arquivos reais.

A preparação tem arquivos novos não registrados em Git. O manifesto os relaciona separadamente do código publicado. Manifesto e seu checksum excluem a si próprios do inventário para evitar autorreferência. Scripts, dados e documentação de preparação entram no inventário separado. Após registro futuro, commits apenas documentais descendentes da base podem ser verificados; mudança de código/dependências exige nova identificação e regressão, não atualização silenciosa do checksum.

Artefatos:

- [Ambiente observado](assets/dynamic-rc1/environment.json): Python/pacotes, Node, Lean/Lake/Mathlib e allowlist de configuração; não lê `.env` nem registra segredos.
- [Constraints Python](assets/dynamic-rc1/python-constraints.txt): versões observadas. Instalar o projeto com `--no-deps` após provisionar dependências correspondentes. Constraints não contêm hashes de wheels, não são um lock multiplataforma nem garantem reprodução bit a bit de bibliotecas nativas.
- [Prompts](assets/dynamic-rc1/prompts.json) e [schemas](assets/dynamic-rc1/schemas.json): conteúdo e hashes, incluindo schemas de transporte estritos. Títulos/versões isolados não substituem esses hashes.
- [Resultados de testes](assets/dynamic-rc1/test-results.json) e logs sintéticos sanitizados incluídos no inventário.
- [Plano de smoke](DYNAMIC_RC1_SMOKE.md): amostras, gate de chamadas/orçamento, roteiro e critérios de interrupção. Não foi executado com providers reais.

Verificação offline, usando o Python validado (no Mac atual, `/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python`; em clone próprio, o `.venv/bin/python` equivalente):

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/evaluation/dynamic_rc1_manifest.py --environment
.venv/bin/python scripts/evaluation/dynamic_rc1_smoke.py
```

O primeiro verifica hashes, fingerprint, ancestralidade da base, referências SPECIALIZED e ambiente. O segundo deve retornar `PLAN_ONLY` e zero chamadas. Para regenerar uma preparação intencionalmente revisada ainda sobre esta base, existe `--write`; não utilizá-lo para mascarar divergências. A geração importa somente contratos/prompts, não inicia avaliação. O `.lake` e pacotes Python não acompanham o repositório: provisionar versões do manifesto sem `lake update`.

## Caminho efetivo de avaliação

`dynamic-semantic.v1` conserva verificações exatas locais de escopo limitado e encaminha pendências ao provider com texto/evidências e rubrica. Crédito parcial é discreto e autorizado (`dynamic-credit.v1`); dependências usam `dynamic-dependencies.v1`. Grader e Reviewer usam o provider semântico compartilhado; o Reviewer recebe entrada independente via `blind_input` e `semantic.review_phase`, sem a decisão do Grader. `semantic.reconcile` compara decisões e pontos, preservando precedência exata e incertezas. Reconciliação não acrescenta chamada LLM.

O adapter legado `OpenAIIndependentReviewProvider` e seu prompt `dynamic-dy4-blind.v2` continuam inventariados, mas não são o caminho de `dynamic-semantic.v1`; configurar somente `CONFIA_DYNAMIC_REVIEWER_MODEL` não troca o modelo do Reviewer semântico atual. O manifesto diferencia defaults, variáveis observadas e versões efetivamente retornadas em futuras execuções. Identificador disponível na configuração não comprova disponibilidade remota.

Preparação/rubrica/pistas usam o transporte DYNAMIC com limite de 10.000 tokens, timeout 90 s e zero retries; avaliação semântica usa 4.000 tokens, timeout 60 s e zero retries. Defaults: `gpt-4.1` (preparação), `gpt-6.1-sol`/`medium` (semântica). Opt-in e credenciais são necessários. Proveniência registra modelo/recibo conhecido, sem inventar metadados ausentes; uso/token e latência de preparação não são completos no contrato legado, por isso o smoke terá recibo externo de transporte.

**Lean não foi executado pelo caminho DYNAMIC inspecionado.** Lean 4.28.0, Lake 5.0.0-src+7e01a1b e Mathlib `8f9d9cff6bd728b17a24e163c9402775d9e6a365` são dependências compartilhadas instaladas, não provas globais dos problemas DYNAMIC. O PautaEngine pertence ao caminho preparado SPECIALIZED; o DYNAMIC usa suas rubricas e mecanismos existentes. Os resultados exatos locais, pareceres semânticos e decisões docentes têm naturezas distintas.

## Nove controles de prontidão e três contextos

| Controle | Caminho/evidência | Parecer |
| --- | --- | --- |
| Sem pontos públicos em SELF_STUDY | `study_feedback.public_report/public_help`, `study_service.view`, testes adversariais R1/R2 e JS | Projeção restrita na API e histórico; sem exportação própria. Trechos originais preservam números matemáticos. |
| Rubrica institucional versionada/aprovada | `dynamic/grading_context.py`, ativação/publicação escolar, `test_dynamic_school.py` | Pacote aprovado fixado; novas versões não substituem silenciosamente tentativas antigas. |
| Rubrica autônoma provisória | `StudyRubric`, `PROVISIONAL_FORMATIVE`, `study_service.prepare` | Conferência do aluno não equivale a aprovação docente; não cria nota escolar. |
| Parcial, dependências e abstenções | `test_dynamic_credit_dependencies.py`, `test_dynamic_semantic_consistency.py`, R3 | Níveis autorizados, revisão em incerteza; parcial não elimina erro com evidência. Falha técnica não vira zero. |
| Proveniência dos três agentes/serviços | `semantic_provenance`, recibos por critério, revisão independente e reconciliação | Fonte/hash/modelo conhecido e decisões rastreáveis; concordância não é prova formal. |
| Decisão docente separada | `test_dynamic_human_adjudication.py`, decisão/finalização/divulgação institucional | Sugestão automática não é decisão final do professor. |
| Originais e conferência | `test_dynamic_handwriting.py`, testes foto/PDF de SELF_STUDY, contratos de reconhecimento/transcrição | OCR automático, revisão vinculada e confirmação explícita são estados distintos. |
| Isolamento | Testes de escola/turma/aluno, sources privados e auth legado | Outro aluno/instituição não ganha acesso por selecionar módulo ou alterar IDs. |
| SPECIALIZED RC1 | Verificador existente aplicado ao worktree congelado, com `--environment` | 754 arquivos, 65 membros históricos, fingerprint e ambiente aprovados; zero auditorias/API. |

Professor: preparação, rubrica aprovada, originais/conferência, correção, reconciliação e adjudicação. Aluno institucional: versões e tentativas fixadas, políticas formativas/somativas e liberação docente. Aluno autônomo: enunciado próprio/catálogo, leitura conferida, critérios provisórios, histórico e feedback sem nota. Os três reutilizam o núcleo; a análise autônoma fica em armazenamento privado de tentativa e não produz um AuditRun institucional/nota escolar por outro nome.

A política pública `self-study-feedback.v2` usa orientação local no nível 1; nos níveis 2–3, seleção de conceito e evidência em contrato fechado; no nível 4, solicitação explícita e expressões estruturadas. É uma proteção de divulgação, não certificação da pertinência do conceito nem da verdade de cada expressão proposta. Rejeição gera orientação segura e registro privado, inclusive na reconsulta histórica.

## Regressões e cobertura ausente

| Verificação nesta preparação | Resultado |
| --- | --- |
| Regressão ampliada Python: DYNAMIC, captura, autorização e contratos TME² | **769 aprovados, 2 skips em 369,33 s** |
| JavaScript completo | **614 aprovados em 2,50 s** |
| Gate de orçamento: reserva, limites, falha, recibo, reinício e STOP | **10 aprovados em 0,10 s**, transporte simulado |
| Integridade SPECIALIZED RC1, incluindo ambiente | **754 arquivos e 65 membros históricos aprovados** |

O conjunto Python é o mesmo comando completo do [relatório de consolidação](CONFIA_DYNAMIC_INTERVENCOES_6_6B_CONSOLIDACAO.md). A instrumentação adicional foi executada separadamente com `python -m pytest -q -p no:cacheprovider tests/test_rc1_smoke_budget.py`. JavaScript: `node --test tests/js/*.cjs`. As dez regressões do gate não estão incluídas nas 769 e não representam avaliações matemáticas adicionais.

Os testes são offline, com providers simulados e dados sintéticos, sem envio aos providers. O conjunto automatizado comprova comportamento/contratos, não acurácia populacional nem benefício pedagógico. A validação de navegador/teclado da 6B continua como evidência anterior, com relatório versionado; não houve nova reconstrução de interface ou nova demonstração de browser nesta preparação.

Os skips são `test_real_smoke_dry_run_separates_semantic_hashes_from_transport` e `test_transport_builder_does_not_weaken_holdout_guard`, ambos em `test_tme_model_compat.py`: `Frozen local DEV pack unavailable`. Limitam a comprovação sobre aquele pacote controlado; não são deseleções, falhas do percurso aluno ou substitutos da validação Lean.

A ocorrência P3 anterior continua aberta: `FAILED/AUDITOR_FAILED` em `test_stale_invalidated_failed_and_new_audit_block_closure`, seguido de HTTP 409 legítimo que impediu confirmar execução falha. A exceção inicial não foi preservada pelo serviço histórico. Repetições aprovadas não esclarecem sua causa. O [relatório I6](CONFIA_DYNAMIC_INTERVENCAO_6_ESTUDO_AUTONOMO.md) e a [revisão](CONFIA_DYNAMIC_INTERVENCAO_6_REVISAO.md) mantêm o registro; o log bruto local ignorado é `artifacts/qa/dynamic-intervention6/regression-initial.log`.

## Pendências, responsabilidades e recomendação

| Categoria | Impeditivo? | Ação necessária |
| --- | --- | --- |
| Defeito matemático/pedagógico reproduzido nesta preparação | Não identificado além dos bloqueios já corrigidos R1–R3 | Não interpretar isso como ausência universal de erros; manter testes adversariais e revisão humana. |
| Smoke real ainda não executado | Impede afirmar prontidão operacional com providers reais; não impede identificar esta candidata documental | Autorizar separadamente orçamento/modelos, executar o plano, registrar recibos e avaliar justificativas/abstenções. Falha relevante exige diagnóstico antes de congelar. |
| Manifesto ainda não registrado/tagueado | Impede chamar esta preparação de versão congelada | Revisar os arquivos, decidir sobre limitações, registrar snapshot/recibo e tag somente mediante autorização posterior. |
| Dois skips DEV e ocorrência P3 | Limitações abertas, não causa demonstrada de defeito no DYNAMIC | Recuperar DEV em armazenamento controlado quando cabível; capturar exceção da P3 se reaparecer. Aceitação explícita dessas lacunas no recibo de congelamento. |
| OCR/caligráfica e pedagogia real | Impede validação de uso escolar autônomo | Avaliar manuscritos consentidos/anônimos, notação, ambiguidades, idade e aprendizagem; a imagem impressa do smoke não cobre isso. |
| Infraestrutura/escala | Aceitável para localhost supervisionado; não para implantação institucional | Fixar ambiente, gestão de segredos/contas, retenção, backup, logs seguros, limites, custo/latência e capacidade antes da expansão. |

**Rian:** manter APIs/gateways dos três contextos, experiência de revisão/divulgação, estados de falha e integração autenticada. Revisar o comportamento com providers reais sem transportar pontos privados para a UI. **Luis:** reconhecimento/captura, originais, mapeamento por página/questão, conferência versionada, qualidade OCR e tratamento de ilegíveis. O [guia compartilhado](../collaboration/README.md) aponta contratos e serviços; não há pacote paralelo de transferência.

Para o piloto escolar de 2027, preparar avaliação independente estratificada por tema/ano/contexto: corretas, parciais, incorretas, alternativas e insuficientes. Gold humano separado do processo corretor, pelo menos duas avaliações independentes e adjudicação. Medir falso crédito, subcrédito, erros não detectados, falsos apontamentos, abstenção, concordância por critério/item e adequação das explicações; separar OCR, qualidade da rubrica e julgamento. Medir também exposição precoce de resposta, utilidade de pistas, custo, latência e taxas de revisão. Um smoke de duas amostras não estima essas métricas com validade científica.

**Parecer:** manifesto candidato e instrumentação offline permitem preparar um congelamento experimental rastreável, sem bloqueio novo reproduzido no núcleo. Recomenda-se concluir o smoke supervisionado autorizado e rever seus resultados antes de efetivar `DYNAMIC-RC1` como referência operacional. Nenhuma tag é criada agora. A futura candidata será explicitamente experimental e não validada para correção autônoma de avaliações escolares.
