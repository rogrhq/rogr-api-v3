#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
export PYTHONPATH="${PYTHONPATH:-.}:."
export API_PORT="${API_PORT:-8000}"
export API_WORKERS="${API_WORKERS:-1}"
bash scripts/kill_port.sh "${API_PORT}" || true
(uvicorn main:app --host 0.0.0.0 --port "${API_PORT}" --workers "${API_WORKERS}" & echo $! > .api_pid)