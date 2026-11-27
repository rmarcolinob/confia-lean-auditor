# ConfIA Dynamic — DY7 — benchmark 01

12/11/2026. **Piloto sintético de infraestrutura, não certificação de eficácia.** A implementação está descrita em documento separado.

## Protocolo congelado

Base Git: `caa5da88bc7a1f21ab7bd0a17a35e28c33af1cf8`. Aplicação SHA256: `a55f5f0fd58257e1fe926c4c5e6367f71d5664712f85ddeda9c9cc1fa0c17cd6`. O código estava sem commit; snapshot exato preservado nos assets.
Dataset SHA256: `6800e3d9b268a2a075efa68fcfcfb80c96df0ac9515192397515fa6719342aa7`. Harness SHA256: `fa44df4abfe508a353b879a7d54a9c187afb825ef29c378aa67d67712f8638a2`. Congelamento externo: `2026-11-12T21:04:01.840057+00:00`.

12 participantes pseudônimos × duas equações × dois perfis = 48 tentativas. Em cada perfil: DEV N=8, VALIDATION N=8 e HOLDOUT N=8. O HOLDOUT contém quatro grupos de participantes e respostas distintas das outras partições. As questões se repetem: não é teste de generalização para problemas inéditos.

Os dois perfis usam as mesmas respostas sintéticas. Portanto, os dois HOLDOUTs não equivalem a 16 observações independentes. Origem de todos os casos: SYNTHETIC. Dificuldade: estimada; domínio: equações reais. Incluem soluções corretas, alternativas, parciais, erro local/estrutural, resposta final isolada, ambiguidade, conflito e autocorreção.

Gold: rótulos sintéticos pré-declarados, `blind=false`, sem raters humanos independentes. G3: decisões operacionais sintéticas pré-declaradas, que coincidem com o gold por construção; MAE G3=0 não demonstra benefício real da intervenção docente. Nenhum HumanDecision virou gold automaticamente.

Preparação e reviewer locais são fixtures explícitos, sem API externa. O reviewer propõe crédito máximo a partir do inventário independente; DY4/DY5 aplicam os gates reais. Não representa qualidade de um modelo de linguagem. O subconjunto DEV com provider real está separado adiante.

Os dois datasets foram congelados antes da primeira auditoria. Houve uma execução única por perfil, sem alteração de grader, prompts, política, thresholds ou rubrica após observar o HOLDOUT. As 24 submissões chegaram à FinalCorrection compartilhada.

## Resultados por estágio e split

Notas em escala 0–10. Taxas são frações; critérios e scores possuem denominadores distintos. “—” indica ausência de estimativa, nunca zero.

| Perfil | Split | Estágio | N score | MAE | RMSE | Exata | N critérios | False credit | Missed credit |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| FORMATIVE_LIST | DEV | G0 | 8 | 4.875 | 5.662 | 0.25 | 24 | 0 | 0.5 |
| FORMATIVE_LIST | DEV | G1 | 0 | — | — | — | 0 | — | — |
| FORMATIVE_LIST | DEV | G2 | 8 | 4.875 | 5.662 | 0.25 | 24 | 0 | 0.5 |
| FORMATIVE_LIST | DEV | G3 | 8 | 0 | 0 | 1 | 0 | — | — |
| FORMATIVE_LIST | HOLDOUT | G0 | 8 | 4.25 | 4.757 | 0 | 24 | 0 | 0.5 |
| FORMATIVE_LIST | HOLDOUT | G1 | 0 | — | — | — | 0 | — | — |
| FORMATIVE_LIST | HOLDOUT | G2 | 8 | 4.25 | 4.757 | 0 | 24 | 0 | 0.5 |
| FORMATIVE_LIST | HOLDOUT | G3 | 8 | 0 | 0 | 1 | 0 | — | — |
| FORMATIVE_LIST | VALIDATION | G0 | 8 | 3.5 | 4.95 | 0.5 | 24 | 0 | 0.333 |
| FORMATIVE_LIST | VALIDATION | G1 | 0 | — | — | — | 2 | 0 | 0 |
| FORMATIVE_LIST | VALIDATION | G2 | 8 | 3.5 | 4.95 | 0.5 | 24 | 0 | 0.333 |
| FORMATIVE_LIST | VALIDATION | G3 | 8 | 0 | 0 | 1 | 0 | — | — |
| SCHOOL_EXAM | DEV | G0 | 8 | 4.875 | 5.662 | 0.25 | 24 | 0 | 0.5 |
| SCHOOL_EXAM | DEV | G1 | 0 | — | — | — | 0 | — | — |
| SCHOOL_EXAM | DEV | G2 | 8 | 4.875 | 5.662 | 0.25 | 24 | 0 | 0.5 |
| SCHOOL_EXAM | DEV | G3 | 8 | 0 | 0 | 1 | 0 | — | — |
| SCHOOL_EXAM | HOLDOUT | G0 | 8 | 4.25 | 4.757 | 0 | 24 | 0 | 0.5 |
| SCHOOL_EXAM | HOLDOUT | G1 | 0 | — | — | — | 0 | — | — |
| SCHOOL_EXAM | HOLDOUT | G2 | 8 | 4.25 | 4.757 | 0 | 24 | 0 | 0.5 |
| SCHOOL_EXAM | HOLDOUT | G3 | 8 | 0 | 0 | 1 | 0 | — | — |
| SCHOOL_EXAM | VALIDATION | G0 | 8 | 3.5 | 4.95 | 0.5 | 24 | 0 | 0.333 |
| SCHOOL_EXAM | VALIDATION | G1 | 0 | — | — | — | 2 | 0 | 0 |
| SCHOOL_EXAM | VALIDATION | G2 | 8 | 3.5 | 4.95 | 0.5 | 24 | 0 | 0.333 |
| SCHOOL_EXAM | VALIDATION | G3 | 8 | 0 | 0 | 1 | 0 | — | — |

## HOLDOUT: cobertura e risco

| Perfil | N G2 | MAE G2 | Falso crédito | Crédito perdido | Pontos perdidos | Revisão | Automação | Risco automático | Override sintético |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FORMATIVE_LIST | 8 | 4.25 | 0/24 | 12/24 | 34 | 1 | 0 | — | 1 |
| SCHOOL_EXAM | 8 | 4.25 | 0/24 | 12/24 | 34 | 1 | 0 | — | 1 |

Em cada perfil, G0 e G2 tiveram MAE 4,25, bias −4,25 e erro absoluto normalizado 0,425. Houve 34 pontos de crédito legítimo perdido no conjunto de oito questões. A reconciliação não corrigiu nem introduziu erros de score nesse HOLDOUT; preservou sugestões provisórias e encaminhou todos os casos à revisão.

**0% de falso crédito com 0% de automação não demonstra segurança de automação.** Não houve caso automatizado; o risco condicionado à automação é indefinido. Também não se demonstrou aumento de cobertura ou recuperação de crédito por DY4/DY5 neste piloto.

G1 não produziu scores totais nem pares de critério determinados no HOLDOUT. Assim, comparações G0×G1 possuem N=0: contadores zero nessa seção não significam ausência de erros detectados ou superioridade do reviewer. São evidência insuficiente para essas comparações.

O label pré-declarado de necessidade pedagógica de revisão estava positivo em 2/8 casos; a precisão baseada nesse label é 25%. Isso descreve a convenção do protocolo. Os oito scores G2 apresentaram erro material e foram escalados; portanto, os seis casos sem esse label intrínseco não devem ser interpretados como revisões dispensáveis diante do erro efetivamente observado.

Zero falhas técnicas e zero exclusões de fidelidade nos dois HOLDOUTs. Essa taxa corresponde ao ambiente local com fixtures, não à confiabilidade de providers reais. Falhas Lean/Mathlib da regressão são reportadas separadamente e não foram apagadas ou convertidas em erro matemático do aluno.

## Reviewer, checker e acordo humano

Os exports preservam G0, G1, G2 e G3, claims/proposições, versão/resultado do checker, contexto aprovado, hashes dos artefatos e provenance de preparação/review/reconciliation. Não houve execução Lean neste benchmark Dynamic. Verificação determinística/simbólica não foi rotulada como Lean.

Não há múltiplos raters humanos neste piloto; acordo inter-rater é indisponível. Com quatro grupos por HOLDOUT, não há intervalo bootstrap. Os resultados têm status PILOT_SMALL_SAMPLE. Não foi realizado teste de significância nem inferência causal.

## Specialized × Dynamic

**N comparável = 0; experimento não executado.** Os dois problemas novos não têm configuração Specialized legítima no catálogo. O harness pareado foi implementado e testado com métricas controladas e rejeição de braço real incompatível; isso não constitui comparação empírica entre produtos. Experimentos END_TO_END e COMMON_RUBRIC permanecem separados. Não se enviaram claims, checkers específicos ou referência curada Specialized ao Dynamic.

## DEV separado com provider real

Após autorização explícita para a API da OpenAI, executou-se uma questão DEV sintética. Run: `run_6e2b21c1a4796e7f3b8c5012ba5bf8edb0f37116a7526988d3c7ab5697f4096b`. Modelo solicitado: `gpt-4.1`; modelo retornado na preparação e revisão: `gpt-4.1-2025-04-14`. Prompts `dynamic-dy2.v1:prepare` e `dynamic-dy4-blind.v2`; schemas e configuração constam no JSON.

A preparação sugeriu uma rubrica, preservada no histórico. O protocolo aplicou a rubrica sintética previamente definida como edição técnica antes da aprovação; não se afirma validação humana da pauta gerada. G0=3/10, G1 indeterminado, G2=3/10 e G3 sintético=10/10. MAE G2=7, N=1, sem falha técnica. O resultado não foi agregado ao benchmark local nem usado para ajustar seu HOLDOUT.

O envio havia sido bloqueado pela revisão automática; após autorização específica do usuário para o destino, dados e modelo, a execução foi permitida e concluída. Não houve envio antes dessa autorização.

## Artefatos e reprodução

- [Protocolo e definições operacionais](../integration/DYNAMIC_CERTIFICATION_PROTOCOL.md).
- [Congelamento](assets/confia-dynamic-dy7/benchmark/protocol-freeze.json).
- [FORMATIVE_LIST JSON](assets/confia-dynamic-dy7/benchmark/FORMATIVE_LIST.json) · [CSV](assets/confia-dynamic-dy7/benchmark/FORMATIVE_LIST.csv).
- [SCHOOL_EXAM JSON](assets/confia-dynamic-dy7/benchmark/SCHOOL_EXAM.json) · [CSV](assets/confia-dynamic-dy7/benchmark/SCHOOL_EXAM.csv).
- [DEV real JSON](assets/confia-dynamic-dy7/live-dev/FORMATIVE_LIST.json) · [CSV](assets/confia-dynamic-dy7/live-dev/FORMATIVE_LIST.csv).
- [Manifesto do código congelado](assets/confia-dynamic-dy7/frozen-source-manifest.json).

Os artefatos brutos permanecem em `artifacts/dynamic_dy7/controlled_01` e `artifacts/dynamic_dy7/live_dev_01` no worktree oficial. Os diretórios são ignorados pelo Git; os exports auditáveis e o snapshot de código estão em docs/audits/assets. Reproduções futuras exigem armazenamento novo e devem ser identificadas como replicação, não como um novo holdout independente.

## Veredito experimental

**PILOT_METRICS_AVAILABLE**. Infraestrutura exercitada, com forte perda de crédito e nenhuma automação no protocolo observado. Evidência insuficiente para certificar eficácia, segurança automática, superioridade ou prontidão de produção. Próxima investigação deve usar DEV novo, avaliadores humanos independentes e um HOLDOUT novo antes de qualquer avaliação posterior.
