#!/usr/bin/env bash
# Run only when the user explicitly invokes this script.
set -euo pipefail
confia_b_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
confia_b_python="${CONFIA_B_PYTHON:-$confia_b_root/../confia-lean-auditor/.venv/bin/python}"
confia_b_dataset="${CONFIA_B_DATASET:-/Users/LinMarcolino/Library/CloudStorage/Dropbox/envio_v2.0/solucoes_v2.0.csv}"
confia_b_cache="${CONFIA_B_LEAN_CACHE:-$confia_b_root/../confia-lean-auditor-leanstrong-aug/.lake}"
confia_b_model="${CONFIA_B_MODEL:-gpt-4o-mini}"
confia_b_output="${CONFIA_B_OUTPUT:-$confia_b_root/artifacts/evaluations/semantic_formal_b_common_gate_pilot18_$(date -u +%Y%m%dT%H%M%SZ)_$$}"
confia_b_model_args=(--model "$confia_b_model")
if [[ -n "${CONFIA_B_REASONING_EFFORT:-}" ]]; then
  confia_b_model_args+=(--reasoning-effort "$CONFIA_B_REASONING_EFFORT")
fi
mkdir -p "$(dirname "$confia_b_output")"
mkdir "$confia_b_output"
export PYTHONDONTWRITEBYTECODE=1
for confia_b_mode in formal_offline semantic_formal; do
  "$confia_b_python" -B "$confia_b_root/scripts/evaluation/run_ita_semantic_formal_b.py" \
    --dataset "$confia_b_dataset" \
    --mode "$confia_b_mode" \
    --ids-file "$confia_b_root/scripts/evaluation/fixtures/pilot18_ids.json" \
    --output-dir "$confia_b_output/$confia_b_mode" \
    --lean-cache "$confia_b_cache" \
    "${confia_b_model_args[@]}"
done
"$confia_b_python" -B "$confia_b_root/scripts/evaluation/compare_formal_vs_semantic_b.py" \
  --formal "$confia_b_output/formal_offline/results.jsonl" \
  --semantic "$confia_b_output/semantic_formal/results.jsonl" \
  --output-dir "$confia_b_output/comparison"
printf 'Resultados: %s\n' "$confia_b_output"
