#!/bin/sh
set -eu
DEMO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DEMO_PYTHON=${CONFIA_DEMO_PYTHON:-/Users/LinMarcolino/Documents/confia-lean-auditor/.venv/bin/python}
if [ ! -x "$DEMO_PYTHON" ]; then
  echo 'Venv indisponível. Defina CONFIA_DEMO_PYTHON para o Python da aplicação.' >&2
  exit 1
fi
export PATH="$HOME/.elan/bin:$PATH"
export PYTHONPATH="$DEMO_ROOT/app"
cd "$DEMO_ROOT"
exec "$DEMO_PYTHON" "$DEMO_ROOT/scripts/demo_december.py" "$@"
