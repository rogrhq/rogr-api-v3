#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1
export PYTHONPATH="${PYTHONPATH:-.}"
PY="$(bash scripts/_python_bin.sh)"
PORT="${API_PORT:-8000}"
# single worker, no reload, log-level=debug to dump import errors
exec "$PY" -m uvicorn main:app --host 0.0.0.0 --port "$PORT" --workers 1 --log-level debug