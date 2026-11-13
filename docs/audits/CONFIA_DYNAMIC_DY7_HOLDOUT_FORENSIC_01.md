# ConfIA Dynamic — DY7 HOLDOUT FORENSIC 01

Análise forense de artefatos persistidos, 12/11/2026. **Veredito: ROOT_CAUSES_IDENTIFIED.** Identificados os mecanismos que explicam os 12/24 critérios com subcrédito, equivalentes a 34 pontos por perfil. Dois desses critérios têm também tensão interpretativa entre gold e rubrica. Isso limita a recomendação pedagógica, sem impedir a explicação do resultado computacional.

Nenhum fix, tuning, mudança de gold, reclassificação histórica, chamada de provider ou nova execução de grader/Lean foi feito. Os resultados continuam sendo um piloto sintético em `SHADOW_EVALUATION`, sem evidência de eficácia geral ou prontidão para produção.

## 1. Frozen DY7 SHA

Commit DY7: `e0975898bb2449c05595c5b75236a9690c51b8b1`, branch `feat/dynamic-correction`, worktree exclusivo `~/Documents/confia-lean-auditor-dynamic`.

O run original registra `caa5da88bc7a1f21ab7bd0a17a35e28c33af1cf8` com `git_dirty=true`: era a base DY6 mais a implementação DY7 ainda não commitada. Preservamos essa proveniência. A aplicação atual coincide com o hash congelado do run: `a55f5f0fd58257e1fe926c4c5e6367f71d5664712f85ddeda9c9cc1fa0c17cd6`. O commit posterior não é apresentado como o SHA originalmente gravado no run.

Versões: `dynamic-grader.v1`, `source-grammar.v1`, `dynamic-exact-polynomial.v1`, `exact-rubric-language.v1`, `dynamic-reviewer.v1`, schema `dynamic-reconciliation.v1`, policy `dynamic-safe-automation.v1`. Os hashes dos arquivos de implementação e os hashes específicos de proveniência estão no manifesto e JSON.

## 2. Benchmark manifest

| Perfil | Run ID | Dataset ID |
| --- | --- | --- |
| FORMATIVE_LIST | `run_e0ed0913d8d7532b8431337b99e5635217695b18c3a8f56be854685a744dbe0a` | `dataset_009c314562343fe870a4894e83c0dc9fe2552b7daf602bd343a82a59bfc1902e` |
| SCHOOL_EXAM | `run_ef21bfce69c02f052e635453d3991c88dfe40aa110ac591b7f0e6d1d3ea149df` | `dataset_6bbf774e6ced994f4459c853229342f19343a8eb45f0590d98327528bb90528b` |

Dataset version `dy7-pilot-01`; protocolo `dy7-controlled-protocol.v1`; gold v1, source `dy7-controlled-protocol`, `SYNTHETIC_FIXTURE`, `SINGLE_RATER`, não cego. Os rótulos foram fixados antes dos outputs, mas não são estudo humano independente. Questões repetidas entre splits avaliam respostas novas, não generalização a problemas inéditos.

**Unidade de análise: 8 tentativas lógicas e 24 critérios por perfil**. São quatro participantes sintéticos × duas questões; os mesmos exemplos reaparecem em FORMATIVE_LIST e SCHOOL_EXAM com IDs distintos. Há 16 registros físicos e 48 linhas de critério no arquivo completo; não são N=16 independente. Igualdade de pontuação, classificação causal e bloqueios foi verificada entre pares. `input_text_sha256` é o hash da string em JSON canônico; não deve ser comparado ao SHA de bytes UTF-8 sem serialização. O JSON forense inclui também o hash UTF-8 e confirma o contrato original.

A anotação nova é **HOLDOUT_V1_FROZEN_ANALYZED**, com `eligible_as_independent_post_fix_holdout=false`. O split original continua `HOLDOUT`; nenhum artefato histórico foi editado. Não se pode usar V1 para alegar validação independente de mudanças informadas por esta análise.

Entregáveis relativos a este relatório:

- [Manifesto de congelamento](assets/confia-dynamic-dy7-forensic/freeze_manifest.json): IDs, versões, hashes de gold/rubricas/transcrições/contexto/estágios e inventário de 2227 arquivos históricos.
- [Análise estruturada](assets/confia-dynamic-dy7-forensic/dy7_holdout_forensic.json): matriz dos dois perfis, probes e contexto completo.
- [24 critérios canônicos](assets/confia-dynamic-dy7-forensic/criteria.csv), [48 registros pareados](assets/confia-dynamic-dy7-forensic/criteria_all_profiles.csv), [causas primárias](assets/confia-dynamic-dy7-forensic/root_causes.csv), [8 casos](assets/confia-dynamic-dy7-forensic/cases.csv).
- [Snapshots da evidência](assets/confia-dynamic-dy7-forensic/evidence_snapshots.json): cópias exatas dos registros selecionados, com caminhos e hashes das fontes originais; não dependem de reler texto deste relatório.
- [Verificação de integridade](assets/confia-dynamic-dy7-forensic/integrity_check.json): hashes antes/depois e checks de consistência.

## 3. Cases

Qy: `Resolva no conjunto dos reais: 2*y^2-14*y+24=0.`; raízes 3 e 4. Qz: `Resolva no conjunto dos reais: 1*z^2-1*z+-2=0.`; raízes −1 e 2. Domínio: equações quadráticas reais, álgebra elementar. IDs abaixo são FORMATIVE_LIST; o JSON faz o vínculo integral com SCHOOL_EXAM e HumanDecision.

| Caso lógico / case_id | Tipo | Gold | G0 | G1 bruto / validado | G2 | HD sintética | Máx. | Revisão / automação / falhas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SYN-009-Qy / `case_7c0af2663b8a81ccfb097c40bf26bc70` | local_error | 7.0 | 1.5 | 10.0 / null | 1.5 | 7.0 | 10.0 | sim / REVIEW_ONLY / 0 |
| SYN-009-Qz / `case_489927cb5c52173dd9912c07bc9cd1fb` | local_error | 7.0 | 1.5 | 10.0 / null | 1.5 | 7.0 | 10.0 | sim / REVIEW_ONLY / 0 |
| SYN-010-Qy / `case_05f52e32fb9763c20da9d9c23cb5919e` | correct_standard | 10.0 | 3.0 | 10.0 / null | 3.0 | 10.0 | 10.0 | sim / REVIEW_ONLY / 0 |
| SYN-010-Qz / `case_83187b16e77122e3ecf4a49f89693074` | correct_standard | 10.0 | 3.0 | 10.0 / null | 3.0 | 10.0 | 10.0 | sim / REVIEW_ONLY / 0 |
| SYN-011-Qy / `case_0e3a11d802773f759ffb73e9d8215e4d` | partial | 4.5 | 3.0 | 10.0 / null | 3.0 | 4.5 | 10.0 | sim / REVIEW_ONLY / 0 |
| SYN-011-Qz / `case_a3d7eaf27195d183495c6bca961f3f72` | partial | 4.5 | 3.0 | 10.0 / null | 3.0 | 4.5 | 10.0 | sim / REVIEW_ONLY / 0 |
| SYN-012-Qy / `case_e2ceb12f3705717d27d0da666f167449` | correct_alternative | 10.0 | 7.0 | 10.0 / null | 7.0 | 10.0 | 10.0 | sim / REVIEW_ONLY / 0 |
| SYN-012-Qz / `case_cec960e9e62d34a1ec083c52179e8b83` | correct_alternative | 10.0 | 7.0 | 10.0 / null | 7.0 | 10.0 | 10.0 | sim / REVIEW_ONLY / 0 |

HD significa HumanDecision operacional **sintética, predeclarada**, igual ao gold por construção. Não demonstra benefício de revisão humana real. `G1=null` é abstenção após validação; não é zero nem aprovação da proposta bruta de 10.

## 4. Criterion matrix

Todos os 24 critérios têm `review_required=true` e `automation=REVIEW_ONLY` em G2. FC/MC significam sobrecrédito/subcrédito versus gold. A coluna checker é a evidência vinculada pelo G0; `NO_BOUND_CLAIM` não significa indisponibilidade do verificador. Em todos os oito `check`, a fonte tem aritmética VERIFIED, mas nenhuma claim SUBSTITUTION vinculada. O CSV inclui deltas brutos de G1, IDs de claims, bindings, status de fonte, limites e avisos.

| Caso | Critério (máx.) | Gold | G0 | G1 bruto / válido | G2 | ΔG0 / ΔG1 / ΔG2 | FC / MC | Checker G0 | Primeira falha |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SYN-009-Qy | method (4.0) | 4.0 | 0.0 | 4.0 / null | 0.0 | -4.0 / null / -4.0 | 0 / 1 | VERIFIED | SUFFICIENCY |
| SYN-009-Qy | roots (3.0) | 1.5 | 1.5 | 3.0 / null | 1.5 | 0.0 / null / 0.0 | 0 / 0 | REFUTED | — |
| SYN-009-Qy | check (3.0) | 1.5 | 0.0 | 3.0 / null | 0.0 | -1.5 / null / -1.5 | 0 / 1 | NO_BOUND_CLAIM | CLAIM_EXTRACTION |
| SYN-009-Qz | method (4.0) | 4.0 | 0.0 | 4.0 / null | 0.0 | -4.0 / null / -4.0 | 0 / 1 | VERIFIED | SUFFICIENCY |
| SYN-009-Qz | roots (3.0) | 1.5 | 1.5 | 3.0 / null | 1.5 | 0.0 / null / 0.0 | 0 / 0 | REFUTED | — |
| SYN-009-Qz | check (3.0) | 1.5 | 0.0 | 3.0 / null | 0.0 | -1.5 / null / -1.5 | 0 / 1 | NO_BOUND_CLAIM | CLAIM_EXTRACTION |
| SYN-010-Qy | method (4.0) | 4.0 | 0.0 | 4.0 / null | 0.0 | -4.0 / null / -4.0 | 0 / 1 | VERIFIED; VERIFIED | SUFFICIENCY |
| SYN-010-Qy | roots (3.0) | 3.0 | 3.0 | 3.0 / null | 3.0 | 0.0 / null / 0.0 | 0 / 0 | VERIFIED; VERIFIED; VERIFIED | — |
| SYN-010-Qy | check (3.0) | 3.0 | 0.0 | 3.0 / null | 0.0 | -3.0 / null / -3.0 | 0 / 1 | NO_BOUND_CLAIM | CLAIM_EXTRACTION |
| SYN-010-Qz | method (4.0) | 4.0 | 0.0 | 4.0 / null | 0.0 | -4.0 / null / -4.0 | 0 / 1 | VERIFIED; VERIFIED | SUFFICIENCY |
| SYN-010-Qz | roots (3.0) | 3.0 | 3.0 | 3.0 / null | 3.0 | 0.0 / null / 0.0 | 0 / 0 | VERIFIED; VERIFIED; VERIFIED | — |
| SYN-010-Qz | check (3.0) | 3.0 | 0.0 | 3.0 / null | 0.0 | -3.0 / null / -3.0 | 0 / 1 | NO_BOUND_CLAIM | CLAIM_EXTRACTION |
| SYN-011-Qy | method (4.0) | 0.0 | 0.0 | 4.0 / null | 0.0 | 0.0 / null / 0.0 | 0 / 0 | NO_BOUND_CLAIM | — |
| SYN-011-Qy | roots (3.0) | 3.0 | 3.0 | 3.0 / null | 3.0 | 0.0 / null / 0.0 | 0 / 0 | VERIFIED | — |
| SYN-011-Qy | check (3.0) | 1.5 | 0.0 | 3.0 / null | 0.0 | -1.5 / null / -1.5 | 0 / 1 | NO_BOUND_CLAIM | CLAIM_EXTRACTION |
| SYN-011-Qz | method (4.0) | 0.0 | 0.0 | 4.0 / null | 0.0 | 0.0 / null / 0.0 | 0 / 0 | NO_BOUND_CLAIM | — |
| SYN-011-Qz | roots (3.0) | 3.0 | 3.0 | 3.0 / null | 3.0 | 0.0 / null / 0.0 | 0 / 0 | VERIFIED | — |
| SYN-011-Qz | check (3.0) | 1.5 | 0.0 | 3.0 / null | 0.0 | -1.5 / null / -1.5 | 0 / 1 | NO_BOUND_CLAIM | CLAIM_EXTRACTION |
| SYN-012-Qy | method (4.0) | 4.0 | 4.0 | 4.0 / null | 4.0 | 0.0 / null / 0.0 | 0 / 0 | VERIFIED; VERIFIED | — |
| SYN-012-Qy | roots (3.0) | 3.0 | 3.0 | 3.0 / null | 3.0 | 0.0 / null / 0.0 | 0 / 0 | VERIFIED; VERIFIED; VERIFIED | — |
| SYN-012-Qy | check (3.0) | 3.0 | 0.0 | 3.0 / null | 0.0 | -3.0 / null / -3.0 | 0 / 1 | NO_BOUND_CLAIM | CLAIM_EXTRACTION |
| SYN-012-Qz | method (4.0) | 4.0 | 4.0 | 4.0 / null | 4.0 | 0.0 / null / 0.0 | 0 / 0 | VERIFIED; VERIFIED | — |
| SYN-012-Qz | roots (3.0) | 3.0 | 3.0 | 3.0 / null | 3.0 | 0.0 / null / 0.0 | 0 / 0 | VERIFIED; VERIFIED; VERIFIED | — |
| SYN-012-Qz | check (3.0) | 3.0 | 0.0 | 3.0 / null | 0.0 | -3.0 / null / -3.0 | 0 / 1 | NO_BOUND_CLAIM | CLAIM_EXTRACTION |

## 5. G0 / G1 / G2

| Perfil | Gold | G0 | G1 bruto | G1 validado | G2 | Subcrédito | Sobrecrédito G2 | Sobrecrédito G1 bruto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FORMATIVE_LIST | 63.0 | 29.0 | 80.0 | indefinido (24 null) | 29.0 | 34.0 | 0.0 | 17.0 |
| SCHOOL_EXAM | 63.0 | 29.0 | 80.0 | indefinido (24 null) | 29.0 | 34.0 | 0.0 | 17.0 |

Máximo 80 pontos por perfil. MAE G0=G2=4,25/10. G1 validado não tem total nem MAE numérico definido: 24/24 propostas são null. A soma bruta de 80 é diagnóstico da fixture; não é nota autorizada.

| Transição / unidade | Corrigiu erro G0 | Preservou erro G0 | Introduziu erro de nota | Observação |
| --- | --- | --- | --- | --- |
| G0 → G1 validado, 24 critérios | 0 | 12 não recuperados | não estimável como nota: 24 abstenções | Proposta máxima não constitui recuperação |
| G0 → G1 bruto, 24 critérios | 8 coincidências com gold nos MC | 4 erros mudam de subcrédito para sobrecrédito | 4 novos erros; 8 sobrecréditos brutos no total, 17 pontos | Nenhuma proposta bruta foi validada |
| G0 → G2, 24 critérios | 0 | 12 | 0 | Todos os pontos G0 preservados |
| G1 validado → G2 | 0 créditos validados recuperados | 12 erros G0 continuam | 0 | Não houve proposta válida suprimida |

G2 não removeu pontos nem criou subcrédito adicional. Também não reparou o subcrédito existente.

## 6. Root-cause taxonomy

Contagens abaixo são por perfil; categorias secundárias se sobrepõem e **não se somam** ao total primário de 12.

| Código / categoria | Evidência neste HOLDOUT |
| --- | --- |
| A PREPARATION_FAILURE | Não demonstrada como causa das perdas; preparação prevê fatoração e fórmula |
| B CLAIM_EXTRACTION_MISS | Primária em 8 check: falta papel semântico SUBSTITUTION; texto e claim aritmética foram preservados |
| C CLAIM_EXTRACTION_DISTORTION | Não demonstrada: não houve alteração do conteúdo matemático das substituições |
| D DISCOURSE_ERROR | Não demonstrada; sem casos de retratação/hipótese neste recorte |
| E FIDELITY_TOO_WEAK | Delta aparece UNSUPPORTED em 2 casos e bloqueia automação; não explica pontos perdidos |
| F RUBRIC_BINDING_MISS | Sintoma em 8 check, derivado de B; nenhuma claim SUBSTITUTION chegou ao binder |
| G RUBRIC_BINDING_WRONG | Reviewer fixture cita todas as claims em todos os 24 critérios; 20 limites rejeitam binding/fidelity |
| H CHECKER_COVERAGE_GAP | Nenhum dos 12 MC demonstrado por checker indisponível; Delta mostra limite de representação, sem prova de ausência de capacidade matemática |
| I CHECKER_FALSE_NEGATIVE | 0 comprovados; raízes incorretas foram corretamente REFUTED |
| J SUFFICIENCY_TOO_STRICT | Primária operacional em 4 method: transformações vinculadas e VERIFIED, mas regra de completude rejeita; 2 têm também Q |
| K SUFFICIENCY_CORRECT | Controle: 2 method de partial corretamente zerados. Não é divergência nem prova de gold errado nos casos com Q |
| L GRADER_DECISION_ERROR | Não há erro aritmético de atribuição após sufficiency; zeros seguem a política implementada |
| M REVIEWER_FAILED_TO_RECOVER | Sintoma nos 12 MC; fixture máxima e validação sem proposta útil |
| N RECONCILIATION_FAILED_TO_RECOVER | Não atribuída: nenhuma recuperação validada chegou ao reconciliador |
| O POLICY_OVER_CONSERVATIVE | Não demonstrada como causa independente: gates recebem proposals inválidas; não há caso seguro barrado apenas pelo perfil |
| P TECHNICAL_FAILURE | 0 neste HOLDOUT; ambiente Lean é questão separada |
| Q GOLD/RUBRIC_AMBIGUITY | 2 method de local_error: crédito de método independente de conclusão errada não está explicitado |
| R UNKNOWN | 0 mecanismos computacionais sem explicação; adjudicação pedagógica de Q permanece pendente |

J é relativo à leitura do gold congelado. Nos dois casos local_error, não se afirma que relaxar a exigência seja pedagogicamente correto sem adjudicação. Registrar a tensão preserva a distinção entre explicar o software e validar a interpretação do gold.

## 7. First-failure analysis

| Causa primária | Primeira falha | Critérios | Pontos perdidos | Referências |
| --- | --- | --- | --- | --- |
| CLAIM_EXTRACTION_MISS | CLAIM_EXTRACTION | 8 | 18.0 | SYN-009-Qy/check, SYN-009-Qz/check, SYN-010-Qy/check, SYN-010-Qz/check, SYN-011-Qy/check, SYN-011-Qz/check, SYN-012-Qy/check, SYN-012-Qz/check |
| SUFFICIENCY_TOO_STRICT | SUFFICIENCY | 4 | 16.0 | SYN-009-Qy/method, SYN-009-Qz/method, SYN-010-Qy/method, SYN-010-Qz/method |

**Substituição (8):** fonte intacta → ARITHMETIC fiel e verificada → papel SUBSTITUTION não reconhecido → binding vazio → sufficiency insuficiente → zero. Primeira falha: `CLAIM_EXTRACTION`, especificamente reconhecimento semântico. O checker verificou igualdade numérica, não emitiu uma refutação falsa.

**Método (4):** fonte intacta → TRANSFORMATION fiel → binding correto a method → identidade/equivalência VERIFIED → completude rejeitada. Primeira falha da obrigação de crédito: `SUFFICIENCY`. Antes disso há um fator contribuinte: o reconhecedor de estratégia não marca fatoração com parênteses internos. Isso é perda de metadado de estratégia, não ausência da claim de transformação, e não se conta como uma quinta/sexta causa.

A regra para method aceita fórmula com ambas as raízes ou fatoração reconhecida com conjunto final completo, além do caso linear. Não aceita simplesmente uma transformação quadrática equivalente validada. Nos dois correct_standard as raízes completas estão explícitas, mas o tag `factorization` falta. Nos dois local_error o conjunto final tem uma raiz errada: reconhecer o tag, sozinho, ainda não satisfaria a regra. Portanto **16 pontos é perda observada, não ganho garantido por um fix de regex**.

## 8. Propagation

Não se contam extração, binding, reviewer e reconciliação como quatro causas independentes da mesma perda.

| Raiz / origem | Consequência no G0 | Reviewer | Reconciliação / policy |
| --- | --- | --- | --- |
| Papel SUBSTITUTION ausente | Evidência não vinculada; 8 zeros | Extração fresca usa a mesma gramática; fixture não adiciona claims | Preserva zero; REVIEW_ONLY |
| Regra de completude e tag de fatoração | 4 method INSUFFICIENT apesar de transformações VERIFIED | Regra independente compartilha linguagem e matemática; proposta não passa | Preserva zero; REVIEW_ONLY |
| Fixture maximalista, problema experimental próprio | Não altera G0 | Claims de todos os tipos em todos os critérios; 24 abstenções | Nenhuma base validada para ajuste |
| Delta não representado | Não tira método da fórmula, que recebe 4 | Unsupported incluído em todas as citações | Unresolved source e fidelity bloqueiam 2 casos |

Independência de acesso ao G0 não equivale a diversidade de representação: reviewer reextrai da fonte, mas compartilha `extract` e a linguagem exata de rubrica. Logo pode repetir os mesmos limites sem estar copiando a decisão G0.

## 9. Missed credit

12/24 critérios (50%), 34/63 pontos do gold ausentes (53,97%). Por mecanismo: substituição 8 critérios / 18 pontos (52,94% dos pontos perdidos); método 4 / 16 (47,06%). Zero perda em roots. A anotação secundária Q envolve 2 critérios / 8 pontos já incluídos nos 16, nunca somados novamente.

| Tipo | N | Gold | G2 | Critérios MC | Pontos perdidos | MAE / 10 |
| --- | --- | --- | --- | --- | --- | --- |
| correct_standard | 2 | 20.0 | 6.0 | 4 | 14.0 | 7.0 |
| correct_alternative | 2 | 20.0 | 14.0 | 2 | 6.0 | 3.0 |
| partial | 2 | 9.0 | 6.0 | 2 | 3.0 | 1.5 |
| local_error | 2 | 14.0 | 3.0 | 4 | 11.0 | 5.5 |

Final-answer-only, contraditória, autocorreção e ambígua têm **N=0 neste HOLDOUT**, não taxa de erro zero. Todos os oito exemplos são do mesmo domínio; funções e outros domínios têm N=0. Qy e Qz têm quatro casos cada e 17 pontos perdidos cada. Não há inferência estatística entre domínios.

Não há suporte para dizer que métodos alternativos foram os mais prejudicados: fórmula recebe 4/4 em ambos os casos e perde somente check. A solução padrão perde 7/10, contra 3/10 da alternativa. São dois exemplos por estrato, sem generalização.

## 10. False credit

G0/G2 têm 0/24 critérios com sobrecrédito, mas concedem pontuação positiva em apenas 10/24 critérios e deixam 14/24 em zero. Destes zeros, 12 divergem do gold e dois são corretos. Foram concedidos 29/63 pontos legítimos (46,03%); todos os 29 coincidem com o gold no montante concedido.

Há evidência local útil de checagem: roots preserva crédito parcial de 1,5 para uma raiz correta e refuta a outra nos dois local_error. Porém o zero de falso crédito também acompanha alto subcrédito e revisão de 100% dos casos. Não prova segurança geral.

G1 validado abstém-se em 24/24; G1 bruto superestima 8/24 critérios e 17 pontos. Automação efetiva é 0/8: **risco automático é indefinido (denominador zero), não 0%**. Os rótulos internos G0 `AUTO_AWARD` não substituem a decisão final de automação G2.

## 11. Automation = 0 analysis

Todos os casos têm proposal validada ausente, sufficiency independente INSUFFICIENT, flag de revisão e uncertainty. Na tabela, contagens sobrepostas descrevem gates; não são causas disjuntas nem ganhos aditivos de cobertura. Os diagnósticos executam somente `independent_limit` sobre claims persistidas e a rubrica original, sem nova extração ou grader.

| Bloqueador / sintoma sobreposto | Casos / 8 | Critérios / 24 |
| --- | --- | --- |
| reviewer_proposal_absent | 8 | 24 |
| independent_limit_absent | 8 | 20 |
| independent_sufficiency_insufficient | 8 | 24 |
| binding_incompatible | 8 | 20 |
| fidelity_failed | 2 | 6 |
| verification_unresolved | 2 | 6 |
| unresolved_source | 2 | 6 |
| reviewer_review_flag | 8 | 24 |
| reviewer_uncertainty | 8 | 24 |
| technical_failure | 0 | 0 |
| school_exam_incremental_veto | 0 | 0 |

Por caso: SYN-009 Qy/Qz tem binding incompatível nos três critérios; SYN-010 Qy/Qz e SYN-011 Qy/Qz têm binding incompatível em roots/check e método insuficiente; SYN-012 Qy/Qz tem binding/fidelity incompatível nos três, acrescido de Delta UNSUPPORTED/unresolved. O JSON registra os booleanos por critério e por caso. As contagens “unresolved_source” e “verification_unresolved” referem-se a claims sem verificação conclusiva, não a checker indisponível: são 0 falhas técnicas e nenhum checker indisponível demonstrado nos 12 MC.

`SCHOOL_EXAM` não explica um bloqueio adicional observável: `safe=false` já em ambos os perfis. Sua exigência de homologação de divergência material não chegou a ser o veto decisivo. Não foram simulados perfis alterados nem thresholds diferentes.

A recusa de automatizar **essas propostas** é coerente com a política de segurança. O 0% também revela que a configuração experimental nunca entregou proposta validada à política: a fixture maximalista e os limites compartilhados impedem medir capacidade de recuperação de um reviewer real. Não se conclui que a pipeline real quase nunca automatiza, nem que baixar thresholds resolveria o problema.

## 12. Reviewer value

| Medida descritiva | Resultado / interpretação |
| --- | --- |
| Missed credits G0 recuperados com proposta validada | 0/12 |
| Erros G0 não recuperados / sem diagnóstico específico útil da fixture | 12/12; avisos de validação são genéricos |
| Falsos créditos G0 detectados | 0 oportunidades, pois G0 tem 0; sensibilidade indefinida |
| Novos falsos créditos na proposta bruta | 8/24, 17 pontos; não aceitos |
| Abstenções após validação | 24/24 |
| Critérios G0 corretos escalados | 12/12 corretos escalados; diagnóstico de excesso de revisão, não prova de falsa acusação matemática |
| Falsos alarmes versus rótulo sintético de revisão (caso) | 6/8 escalados com gold requires_review=false; 2/8 com true; precision 25% |
| Transição numérica G0→G1 pareada | N=0, porque G1 validado é null; taxas de detecção numérica indefinidas |
| Recuperação de estratégia alternativa | 0 adicional; método já estava correto no G0 |

A fixture declara COMPLETE e máximo em todos os critérios, sem diagnosticar erro específico. Em 8 dos 12 MC a proposta bruta coincide com o gold; nos outros 4, ultrapassa o gold e troca subcrédito por sobrecrédito. As 8 coincidências são consequência da proposta máxima e não descoberta de evidência. O ganho observado é da **validação defensiva**, que impede usar propostas não sustentadas; não há exemplar de reviewer recuperando crédito legítimo.

“Falso alarme” depende da unidade: em critério, os 12 corretos são também escalados; em caso, todos os oito têm ao menos uma perda real, logo escalá-los não é um alarme inteiramente sem erro de nota. O alvo sintético de revisão marca apenas os dois local_error como true. Contra esse alvo, há 6 falsos alarmes de escalonamento em 8 casos (6/6 gold negativos; precision 2/8=25%). Isso não contradiz que todos os casos tenham erro de pontuação G0: são alvos diferentes. Esta contagem forense usa todos os oito rótulos persistidos, mesmo com G1 null; a métrica histórica de transição numérica G0→G1 tem N pareado=0 e não pode ser interpretada como detecção perfeita ou ausência de erros. O JSON preserva ambos os denominadores. Não há contagem de falso diagnóstico específico, pois a fixture não faz tal diagnóstico.

## 13. Reconciliation value

G0→G2: 0 erros corrigidos, 0 introduzidos; 0 pontos recuperados, 0 removidos; 12 MC preservados; 8/8 casos escalados, 24/24 critérios REVIEW_ONLY. Nenhuma proposta G1 validada foi suprimida. A reconciliação preserva inclusive os 1,5 pontos de roots nos local_error e os 4 pontos de method nas alternativas.

Não atribuir os 17 pontos brutos recusados somente ao reconciliador: a validação do reviewer já havia tornado as propostas null. A reconciliação revalida e conserva o baseline. Sua contribuição observável aqui é contenção de mudança sem suporte, não recuperação de crédito nem correção de falso crédito G0.

## 14. Rubric analysis

As rubricas estão no fluxo AI-generated aprovado, mas a geração e semantic review deste experimento são fixtures (`not-an-LLM`). O snapshot preserva origem `DRAFT_AI`, enquanto o pacote aprovado vincula sua versão. Isso não autoriza afirmar que houve avaliação pedagógica independente por professor.

| Critério | Texto aprovado | Evidência esperada / gold | Interpretação implementada / diagnóstico |
| --- | --- | --- | --- |
| method, 4 | Justificar a resolução por transformações equivalentes. | Transformações/fatoração válidas ou fórmula; gold separa erro local final | Mapeia para policy method: fórmula completa ou fatoração reconhecida com raízes completas. Mais restrito que “transformações equivalentes”; completude e dependência de roots não estão explícitas |
| roots, 3 | Obter todas as raízes reais. Crédito parcial proporcional às raízes corretas. | Conjunto completo ou proporção correta | Regra e resultados compatíveis com gold nos 8 casos; linguagem relativamente clara |
| check, 3 | Verificar as raízes por substituição. Crédito parcial proporcional às raízes corretas. | Uma/duas substituições corretas: 1,5/3 | Só SUBSTITUTION qualifica; ARITHMETIC verdadeiro não basta. Obrigação clara, reconhecimento estrutural frágil |

Para cada divergência, o CSV registra texto, leitura do gold, bindings, status e sufficiency. Em method, a rubrica é procedimental e pouco explícita sobre o desenvolvimento mínimo e separação da conclusão; requer adjudicação futura dos dois local_error. Check pede procedimento específico justificadamente; não há necessidade demonstrada de afrouxá-lo. Não há evidência de que as rubricas estejam matematicamente impossíveis.

O gerador registra `NO_CRITERION_BINDING` nos três critérios: `evidence=null`, sem ligação matemática explícita no artefato da rubrica. O runtime reconstrói o vínculo pela linguagem do critério. Esse aviso é um contribuinte arquitetural à fragilidade, não prova isolada de que a preparação causou os 12 erros. A semantic review fixture diz ausência de vagueza; a inspeção forense revela a tensão que essa fixture não avaliou substancialmente.

## 15. Preparation analysis

Para cada problema/perfil, o snapshot preserva preparação v1, candidate solution por fatoração, conjunto completo de raízes e estratégias alternativas `factor` (“Fatoração ou produto nulo”) e `formula` (“Fórmula quadrática também é legítima.”). Plano de verificação: fatoração SYMBOLIC_ALGEBRA e roots DETERMINISTIC, ambos available e VERIFIED_WITHIN_SCOPE, sem certificação Lean.

| Solução observada | Cobertura prevista | Resultado relevante |
| --- | --- | --- |
| Fatoração em local_error / correct_standard | Sim, candidate por fatoração | Transformação é verificada; anotação de estratégia não reconhece parênteses internos e sufficiency rejeita |
| Fórmula em SYN-012 Qy | Sim, alternativa formula | Ambas as fórmulas VERIFIED; método 4; reviewer não adiciona recuperação |
| Fórmula em SYN-012 Qz | Sim, alternativa formula | Mesmo resultado; Delta escalar não representado |
| Substituições explícitas | Não são candidate checks separados no plano da preparação | Capacidade aritmética local é selecionada e executada; ligação à equação falha na representação |

A seleção de checkers é por forma da claim, e o plano DY2 é contexto. Não se demonstrou referência matemática incorreta, ausência de método legítimo no catálogo ou dependência da captura. O input textual versionado chega íntegro; OCR/captura não explica estas perdas.

## 16. Checker coverage

`checker_available=true` nos 24 critérios significa capacidade local para o tipo de obrigação deste problema, não que a evidência vinculada seja suficiente. Não transforma o requisito pedagógico em mera igualdade numérica. A coluna de sufficiency reflete G0 sobre evidência realmente vinculada.

| Caso | method: status / suficiente | roots: status / suficiente | check: status vinculado / suficiente; fonte |
| --- | --- | --- | --- |
| SYN-009-Qy | VERIFIED / não | REFUTED / sim | NO_BOUND_CLAIM / não; fonte aritmética VERIFIED |
| SYN-009-Qz | VERIFIED / não | REFUTED / sim | NO_BOUND_CLAIM / não; fonte aritmética VERIFIED |
| SYN-010-Qy | VERIFIED; VERIFIED / não | VERIFIED; VERIFIED; VERIFIED / sim | NO_BOUND_CLAIM / não; fonte aritmética VERIFIED |
| SYN-010-Qz | VERIFIED; VERIFIED / não | VERIFIED; VERIFIED; VERIFIED / sim | NO_BOUND_CLAIM / não; fonte aritmética VERIFIED |
| SYN-011-Qy | NO_BOUND_CLAIM / não | VERIFIED / sim | NO_BOUND_CLAIM / não; fonte aritmética VERIFIED |
| SYN-011-Qz | NO_BOUND_CLAIM / não | VERIFIED / sim | NO_BOUND_CLAIM / não; fonte aritmética VERIFIED |
| SYN-012-Qy | VERIFIED; VERIFIED / sim | VERIFIED; VERIFIED; VERIFIED / sim | NO_BOUND_CLAIM / não; fonte aritmética VERIFIED |
| SYN-012-Qz | VERIFIED; VERIFIED / sim | VERIFIED; VERIFIED; VERIFIED / sim | NO_BOUND_CLAIM / não; fonte aritmética VERIFIED |

| Família | Uso observado / limite |
| --- | --- |
| Deterministic | Raízes e aritmética exata; roots nos 8 critérios, crédito parcial corretamente preservado |
| Arithmetic | Substituições numéricas calculadas como ARITHMETIC VERIFIED em 8 check; fórmulas exatas em 2 method |
| Symbolic | Transformações/fatorações VERIFIED nos 4 method com MC; não satisfazem a regra de completude |
| Numerical aproximado | Não executado; não confundir aritmética exata com aproximação numérica |
| Finite | Nenhum checker de enumeração finita dedicado; enumeração exata de raízes pertence ao caminho determinístico |
| Lean | Não executado em nenhum dos 24 critérios |
| Semantic only | Sem crédito atribuído apenas por parecer semântico; fixture não serve como verificador |
| Review only | G2 24/24; G0 insufficiency em 14/24, dos quais 12 com MC e 2 controles sem método |

Checkers matemáticos disponíveis e corretos não implicam critério coberto: uma igualdade verdadeira precisa estar ligada à obrigação correta. Não há evidência de CHECKER_FALSE_NEGATIVE. `Delta=4/9` é bloqueado antes de uma proposição verificável ser formada; não foi provado que um checker adequado tentou e falhou, nem que faltava capacidade para calcular o discriminante.

## 17. Representative traces

### A — Extração semântica: SYN-011-Qy / check

Fonte: `S={3,4}; 2*(3)^2+(-14)*(3)+(24)=0`.

1. Texto e offsets preservados; `claim_2` contém a igualdade numérica.
2. Claim ARITHMETIC, ADOPTED, FAITHFUL, VERIFIED. Sua expressão vale zero.
3. `shape` da fonte: `2*3^2+-14*3+24`; forma esperada substituindo y=3 no enunciado: `2*3^2-14*3+24`. A comparação de strings não coincide.
4. Não nasce SUBSTITUTION; binder de check não aceita ARITHMETIC; nenhuma claim vinculada.
5. Gold 1,5; G0 0/INSUFFICIENT; fixture propõe 3 citando roots e aritmética, limite rejeita binding, G1 null; G2 0/REVIEW_ONLY.

O texto não desapareceu e não foi considerado matematicamente falso. Faltou representar a relação com a equação original.

### B — Sufficiency com binding correto: SYN-010-Qy / method

Fonte relevante: `y^2-7*y+(12)=0; (y-(3))*(y-(4))=0; y=3; y=4; S={3,4}`.

1. `claim_1` e `claim_2` TRANSFORMATION, FAITHFUL, VERIFIED e vinculadas a method.
2. A regex de fatoração não permite parênteses dentro de cada fator; `(y-(3))` não casa. `strategy_context=equivalent_transformations`.
3. Raízes completas aparecem e são VERIFIED, mas a regra method exige `factored` ou fórmula completa. Sufficiency INSUFFICIENT, G0 0 contra gold 4.
4. Reviewer cita todas as claims; método tem limite 0/INSUFFICIENT e aviso “Resposta final não supre justificativa ausente.”; proposta 4 vira null.
5. G2 preserva 0. Não há checker refutando a fatoração.

Nos local_error a mesma falta de tag existe, mas raízes finais incompletas são um segundo impedimento; adjudicar a independência de method antes de recomendar mudança.

### C — Checker coverage: exemplar causal solicitado não observado

Não existe, entre os 12 MC, perda comprovada por checker indisponível. Não se fabrica esse exemplar. O trace mais próximo é `Delta=4` em SYN-012-Qy (`Delta=9` em Qz): claim UNSUPPORTED/REVIEW_ONLY, fidelity UNSUPPORTED, gramática remove o cabeçalho e resta um único valor, sem igualdade verificável. Há limite de representação/cobertura do formato, mas **não perda de crédito de method**, que recebe 4 via fórmulas. Esse trecho bloqueia automação por unresolved source. Isso não prova impossibilidade matemática do checker nem é CHECKER_FALSE_NEGATIVE.

### D — Reviewer ajudou: recuperação validada não observada

Não há caso de crédito recuperado pelo reviewer neste HOLDOUT. Como efeito defensivo, SYN-009-Qy recebe proposta bruta roots=3 e check=3, acima do gold 1,5/1,5; a validação rejeita a proposta. Isso é utilidade do gate contra a fixture excessiva, **não evidência de reviewer inteligente identificando o erro**. Nenhuma das 24 propostas válidas tem valor numérico.

### E — Conservadorismo preservado: SYN-009-Qy

G0: method 0, roots 1,5, check 0; roots contém 3 correto e 5 refutado. G1 bruto=10, validado=null. Reconciliation não toma a concordância da fixture como prova; conserva 1,5 e solicita revisão nos três critérios. Mantém tanto o crédito parcial correto quanto o subcrédito pendente. Nenhum ponto é removido. Este é um caso de contenção, não de conclusão automática correta do exercício inteiro.

Snapshots completos, G0/G1/G2 e probes desses traces estão identificados por `FORMATIVE_LIST/SYN-xxx-Qy` no JSON; os pares SCHOOL_EXAM são preservados.

## 18. Lean environment

[Registro DY7 original](assets/confia-dynamic-dy7/formal-validation.json): `ENVIRONMENT_PENDING`. Quatro testes ambientais separados:

1. `tests/test_submission_audits.py::test_real_bridge_preserves_wrong_solution_and_runs_existing_lean_pipeline`
2. `tests/test_tme_accepted_integration.py::test_real_local_lean_status_certificates_preserved`
3. `tests/test_tme_hybrid_grader.py::test_wrong_reasoning_correct_final_is_refuted_by_real_lean`
4. `tests/test_tme_hybrid_grader.py::test_real_formal_verified_is_preserved_and_not_semantic`

Falharam com technical_error em lugar do resultado formal esperado. Revisão Mathlib solicitada `8f9d9cff6bd728b17a24e163c9402775d9e6a365`; checkout registrado `ab19bac90981b27f5380941f4b36617e738358c9`, 9490 staged deletions e 18 untracked entries. São evidências históricas, não nova inspeção/correção de dependências nesta tarefa.

Os 12 MC não têm erro técnico de checker nem Lean executado. Aritmética/transformações relevantes estão VERIFIED; perderam crédito por representação/sufficiency. Portanto não se rotula falha ambiental como erro do aluno nem se usa Lean para explicar indevidamente os 34 pontos ausentes. Nenhuma tentativa de reparar/reexecutar Lean foi feita.

## 19. Prioritized remediation backlog — Potential remediation, não aplicada

| Prioridade | Proposta futura / evidência | Risco de falso crédito e proteção | Generalidade / impacto |
| --- | --- | --- | --- |
| P0 | Predeclarar obrigações de método e adjudicar sua independência de roots; 2 critérios/8 pontos com Q | Relaxar completude pode premiar justificativa incompleta. Dupla avaliação cega e política explícita por rubrica | Contrato pedagógico; evitar mudar globalmente method para “qualquer igualdade” |
| P0 | Separar reviewer adversarial máximo de reviewer de recuperação; evidência por critério, controlar abstenção e IDs de fonte; 24/24 abstêm | Não aceitar mera proposta ou consenso. Manter gates e casos negativos de binding | Harness e observabilidade; medir capacidade real antes de alterar policy |
| P1 | Reconhecer substituição por estrutura e associação ao enunciado, mantendo offsets e valor substituído; 8 critérios/18 pontos | Igualdade verdadeira alheia ao problema não pode receber check. Validar variável, termo original, valor e resultado; negativos com aritmética incidental | Maior frequência e pontos; fronteira representação→binding, sem dependência de OCR |
| P1 | Reconhecer fatoração estrutural com parênteses internos e auditar regra de completude; 4 critérios/16 pontos observados, ganho não garantido | Transformação equivalente isolada pode não concluir solução. Distinguir transformação, produto nulo e raízes; preservar refutações | Generaliza além de regex literal; exige alinhamento à rubrica, não redução de threshold |
| P1 | Reviewer com seleção de evidência pertinente e caminhos de representação independentes, sob os mesmos checkers autorizados | Propostas adicionais devem corresponder a spans e verificar obrigação; testar citação excessiva, omissão e erro local | Reduz falhas correlacionadas; custo e diversidade medidos em DEV novo |
| P2 | Representar discriminante como proposição associada a a,b,c; 2 casos de automação bloqueada, 0 pontos perdidos atribuídos | Não aceitar Delta escalar sem contexto nem ignorá-lo quando incorreto | Cobertura de formato e rastreabilidade, não motivo para introduzir Lean neste piloto |
| P2 | Estudos curados em outros domínios, notações e raters reais | Não extrapolar amostra sintética; medir robustez e gold disagreement | Evidência de generalidade, sem acoplar motor à captura |

A ordem considera frequência, pontos, segurança, generalidade e impacto arquitetural. P0 são pré-condições de interpretação e desenho experimental; não sugerem que 24 abstenções sejam 24 perdas de pontos independentes. Nada recomenda “baixar review thresholds”.

## 20. DYNAMIC_DEV_V2 specification

**Somente especificação**, sem criar dataset/casos completos nem executar fixes. Usar novas famílias e valores; proibir cópia literal ou simples reapresentação dos oito exemplos V1. Registrar origem, família, seed, transformação de notação, versão de transcrição, rubrica, gold independente e critérios de inclusão antes dos resultados.

Proposta inicial: pelo menos 8 famílias × 8 tentativas = 64 tentativas, distribuídas entre pelo menos quatro enunciados inéditos por família; número definitivo pré-registrado antes de rodar. Variações do mesmo problema ficam agrupadas, não atravessam fronteiras de avaliação. Fixtures adversariais do reviewer constituem estrato experimental separado de chamadas reais.

| Família nova | Capacidade exercitada | Controles negativos obrigatórios |
| --- | --- | --- |
| Quadráticas com novos coeficientes/raízes racionais e escalas | Substituição com sinais, parênteses, frações e ordens equivalentes | Igualdade verdadeira sem relação com a equação; substituir variável/valor errado; resultado numérico falso |
| Produtos fatorados com profundidade sintática variada | Reconhecimento estrutural preservando fonte | Fator errado, constante multiplicativa zero, identidade que não resolve obrigação |
| Sequências de equivalências em novos problemas | Crédito de método separado de conclusão conforme rubrica | Passo não equivalente, divisão por zero, raiz extrínseca, método apenas alegado |
| Fórmula e discriminante contextualizados | Conectar Delta a coeficientes e a duas raízes | Delta correto de outra equação, Delta errado com raiz final coincidente |
| Soluções parciais e conclusão isolada | Partial credit por obrigação explícita | Final-answer-only não supre justificativa; evitar crédito duplo |
| Discurso em famílias inéditas | Hipótese, retratação, autocorreção e conclusão adotada | Recorte de trecho positivo de contexto negado; duas conclusões incompatíveis |
| Reviewer/evidence-binding | Recuperação fonte→claim→critério com subset relevante | Fixture all-claims/max, claim inventada, offset adulterado, gold ausente do input |
| Limites de cobertura e domínios curados | Distinguir unsupported, technical_error e refutação | Falhas injetadas e problemas fora do escopo jamais convertidos em erro do aluno |

Cada família precisa combinar acertos, erros locais e soluções incompletas; não só exemplos positivos que reproduzem o padrão descoberto. Não fixar novos enunciados do HOLDOUT_V2 junto a esses dados. Casos de captura real servem apenas à regressão de contrato; métricas matemáticas partem de TranscriptionVersion textual válida.

Métricas pré-declaradas, por perfil, estágio e família, com escala de pontuação congelada e abstenção explícita:

| Métrica | Definição antes de ver resultados |
| --- | --- |
| Criterion precision | TP/(TP+FP) para evento “algum crédito devido”: TP se score>0 e gold>0; FP se score>0 e gold=0. Reportar também sobrecrédito parcial, que essa precisão binária não capta |
| Criterion recall | TP/(TP+FN); FN inclui score=0 ou abstenção quando gold>0. Não remover abstenções do denominador |
| False-credit rate | Critérios com score>gold / todos os critérios elegíveis, com contagem e pontos excedentes; separar propostas brutas de validadas |
| Missed-credit rate | Critérios com score<gold / todos os critérios elegíveis; reportar separadamente abstenções e composite “sem crédito validado suficiente” |
| MAE | Média por tentativa de abs(score−gold), normalizada por max para /10; G1 null tem MAE indefinido, e cobertura de notas definida é reportada junto |
| Review rate | Casos/critério com revisão requerida sobre elegíveis; cruzar alvo gold de revisão e erro de nota, sem confundir os dois |
| Automation coverage | Casos totalmente automatizados / elegíveis, e cobertura por critério; REVIEW_ONLY não é automação |
| Unsafe automation | Casos automatizados que violam gold/obrigações ou contêm erro material / automatizados; separar sobrecrédito e subcrédito; sem automatizados, indefinido |

Reportar adicionalmente precision/recall de pontos: soma min(score,gold)/soma score e soma min(score,gold)/soma gold, sempre com tratamento explícito de null. Para composição, null recebe “nenhum crédito validado”, não uma nota factual zero. Congelar tolerância numérica e limiar de erro material (proposta: manter 1 ponto/10 do piloto até adjudicação prospectiva), cálculo de intervalos, agrupamento por participante/problema e regras de exclusão. Não selecionar métrica depois do resultado; não escolher threshold no HOLDOUT. DEV serve para desenvolver e comparar, não para proclamar validação independente.

## 21. HOLDOUT_V2 protocol

Após fixes baseados no DEV_V2, congelar código, prompts/modelos, rubricas, policies, checkers, critérios de inclusão, métricas e plano de análise. Curadoria independente deve produzir novos problemas e respostas, sem compartilhar famílias quase duplicadas, templates ou participantes com DEV. As famílias gerais de capacidade podem ser conhecidas; instâncias e gold ficam inacessíveis durante ajuste.

1. Dois avaliadores independentes, cegos aos outputs e entre si, atribuem gold por critério; divergências adjudicadas com justificativa, inclusive dependência method→roots e alvo de review.
2. Definir tamanho e estratos segundo precisão desejada, não repetir N=8 como prova suficiente. Registrar ausências de domínio e grupos; comparar Specialized×Dynamic somente onde haja elegibilidade comum.
3. Hash/manifest de enunciados, rubricas aprovadas, versões textuais, gold e splits; custodiar o gold separado. Classificar HOLDOUT_V2 antes dos resultados.
4. Executar uma avaliação predeclarada por versão. Falhas técnicas, abstenções e exclusões entram com motivo, sem exclusão oportunista; publicar denominadores e intervalos por unidade agrupada.
5. Repetições para corrigir execução só segundo regra operacional registrada, sem ajuste de motor a exemplos revelados. Se ocorrer análise para tuning, marcar V2 como analisado e exigir novo holdout para alegação independente posterior.
6. V1 pode ser regressão histórica identificada como conhecida; nunca novamente teste independente pós-fix. Manter originais e este relatório, incluindo os resultados ruins.

Nenhum caso completo de HOLDOUT_V2 foi criado nesta tarefa. A meta futura é maior cobertura segura e menor subcrédito com baixo falso crédito, não 100% de automação.

## 22. Conclusions

**ROOT_CAUSES_IDENTIFIED**: os 12 MC têm cadeia computacional localizada; 8 começam no reconhecimento semântico de substituição (18 pontos), 4 na sufficiency de método (16 pontos, com falta de tag de fatoração como contribuinte). Dois method também exigem adjudicação gold/rubrica. Essa ressalva impede tratar todo o delta como fix garantido.

O reviewer maximalista não entrega nenhuma proposta validada; G2 preserva G0 e mantém 100% em revisão. Isso explica o 0% de automação sem atribuí-lo ao perfil SCHOOL_EXAM ou a Lean. Não se demonstrou perda causada por checker indisponível, false negative matemático, recuperação validada suprimida ou desempenho de LLM reviewer.

Foram analisados 8 casos / 24 critérios por perfil; false credit 0/24, missed credit 12/24, MAE 4,25/10. Risco automático continua indefinido; Specialized×Dynamic N comparável continua 0. O estado experimental original `PILOT_METRICS_AVAILABLE` não é promovido a eficácia geral.

Validação desta tarefa: hashes dos 2227 arquivos históricos comparados antes/depois; aplicação coincide com o hash DY7; 24 linhas canônicas e 48 pareadas verificadas; totais, perdas e igualdade entre perfis conferidos. Apenas artefatos novos de forense foram escritos. Sem testes de produto adicionais, provider, rerun do benchmark, Lean, git add ou commit.
