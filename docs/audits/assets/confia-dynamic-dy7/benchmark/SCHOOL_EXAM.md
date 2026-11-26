# Dynamic — resultado experimental

SHADOW_EVALUATION · Sem alteração da correção oficial.

Run: `run_ef21bfce69c02f052e635453d3991c88dfe40aa110ac591b7f0e6d1d3ea149df`; dataset: `dataset_6bbf774e6ced994f4459c853229342f19343a8eb45f0590d98327528bb90528b`.
Git SHA: `caa5da88bc7a1f21ab7bd0a17a35e28c33af1cf8`; aplicação SHA256: `a55f5f0fd58257e1fe926c4c5e6367f71d5664712f85ddeda9c9cc1fa0c17cd6`.

| Perfil | Split | Origem | Estágio | N | MAE | False credit | Missed credit | Automação | Risco automático |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| SCHOOL_EXAM | DEV | SYNTHETIC | G0 | 8 | 4.875 | 0 | 0.5 | 0 | — |
| SCHOOL_EXAM | DEV | SYNTHETIC | G1 | 0 | — | — | — | 0 | — |
| SCHOOL_EXAM | DEV | SYNTHETIC | G2 | 8 | 4.875 | 0 | 0.5 | 0 | — |
| SCHOOL_EXAM | DEV | SYNTHETIC | G3 | 8 | 0.0 | — | — | 0 | — |

Exclusões: `{}`. Falhas técnicas: 0.
Incerteza: `PILOT_SMALL_SAMPLE`; grupos independentes: 4.

| SCHOOL_EXAM | HOLDOUT | SYNTHETIC | G0 | 8 | 4.25 | 0 | 0.5 | 0 | — |
| SCHOOL_EXAM | HOLDOUT | SYNTHETIC | G1 | 0 | — | — | — | 0 | — |
| SCHOOL_EXAM | HOLDOUT | SYNTHETIC | G2 | 8 | 4.25 | 0 | 0.5 | 0 | — |
| SCHOOL_EXAM | HOLDOUT | SYNTHETIC | G3 | 8 | 0.0 | — | — | 0 | — |

Exclusões: `{}`. Falhas técnicas: 0.
Incerteza: `PILOT_SMALL_SAMPLE`; grupos independentes: 4.

| SCHOOL_EXAM | VALIDATION | SYNTHETIC | G0 | 8 | 3.5 | 0 | 0.3333333333333333333333333333 | 0 | — |
| SCHOOL_EXAM | VALIDATION | SYNTHETIC | G1 | 0 | — | 0 | 0 | 0 | — |
| SCHOOL_EXAM | VALIDATION | SYNTHETIC | G2 | 8 | 3.5 | 0 | 0.3333333333333333333333333333 | 0 | — |
| SCHOOL_EXAM | VALIDATION | SYNTHETIC | G3 | 8 | 0.0 | — | — | 0 | — |

Exclusões: `{}`. Falhas técnicas: 0.
Incerteza: `PILOT_SMALL_SAMPLE`; grupos independentes: 4.

Amostras pequenas são pilotos descritivos. Concordância entre agentes não é verdade. Gold sintético não demonstra eficácia em alunos reais.

Veredito experimental: **PILOT_METRICS_AVAILABLE**.
