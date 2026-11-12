# Dynamic — resultado experimental

SHADOW_EVALUATION · Sem alteração da correção oficial.

Run: `run_e0ed0913d8d7532b8431337b99e5635217695b18c3a8f56be854685a744dbe0a`; dataset: `dataset_009c314562343fe870a4894e83c0dc9fe2552b7daf602bd343a82a59bfc1902e`.
Git SHA: `caa5da88bc7a1f21ab7bd0a17a35e28c33af1cf8`; aplicação SHA256: `a55f5f0fd58257e1fe926c4c5e6367f71d5664712f85ddeda9c9cc1fa0c17cd6`.

| Perfil | Split | Origem | Estágio | N | MAE | False credit | Missed credit | Automação | Risco automático |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| FORMATIVE_LIST | DEV | SYNTHETIC | G0 | 8 | 4.875 | 0 | 0.5 | 0 | — |
| FORMATIVE_LIST | DEV | SYNTHETIC | G1 | 0 | — | — | — | 0 | — |
| FORMATIVE_LIST | DEV | SYNTHETIC | G2 | 8 | 4.875 | 0 | 0.5 | 0 | — |
| FORMATIVE_LIST | DEV | SYNTHETIC | G3 | 8 | 0.0 | — | — | 0 | — |

Exclusões: `{}`. Falhas técnicas: 0.
Incerteza: `PILOT_SMALL_SAMPLE`; grupos independentes: 4.

| FORMATIVE_LIST | HOLDOUT | SYNTHETIC | G0 | 8 | 4.25 | 0 | 0.5 | 0 | — |
| FORMATIVE_LIST | HOLDOUT | SYNTHETIC | G1 | 0 | — | — | — | 0 | — |
| FORMATIVE_LIST | HOLDOUT | SYNTHETIC | G2 | 8 | 4.25 | 0 | 0.5 | 0 | — |
| FORMATIVE_LIST | HOLDOUT | SYNTHETIC | G3 | 8 | 0.0 | — | — | 0 | — |

Exclusões: `{}`. Falhas técnicas: 0.
Incerteza: `PILOT_SMALL_SAMPLE`; grupos independentes: 4.

| FORMATIVE_LIST | VALIDATION | SYNTHETIC | G0 | 8 | 3.5 | 0 | 0.3333333333333333333333333333 | 0 | — |
| FORMATIVE_LIST | VALIDATION | SYNTHETIC | G1 | 0 | — | 0 | 0 | 0 | — |
| FORMATIVE_LIST | VALIDATION | SYNTHETIC | G2 | 8 | 3.5 | 0 | 0.3333333333333333333333333333 | 0 | — |
| FORMATIVE_LIST | VALIDATION | SYNTHETIC | G3 | 8 | 0.0 | — | — | 0 | — |

Exclusões: `{}`. Falhas técnicas: 0.
Incerteza: `PILOT_SMALL_SAMPLE`; grupos independentes: 4.

Amostras pequenas são pilotos descritivos. Concordância entre agentes não é verdade. Gold sintético não demonstra eficácia em alunos reais.

Veredito experimental: **PILOT_METRICS_AVAILABLE**.
