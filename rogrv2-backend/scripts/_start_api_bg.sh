#!/usr/bin/env bash
set -euo pipefail
# Load test env if present, then set safe defaults
[ -f ".env.test" ] && set -a && . ./.env.test && set +a
: "${AUTH_JWT_SECRET:=dev-secret-$(date +%s)}"
: "${DATABASE_URL:=sqlite+aiosqlite:///$PWD/rogr_dev.db}"
export AUTH_JWT_SECRET
export DATABASE_URL
PY="$(bash scripts/_python_bin.sh)"
DBURL="${DATABASE_URL:-}"
if [[ "$DBURL" == sqlite+aiosqlite* ]]; then
  WORKERS=1
else
  WORKERS="${APP_WORKERS:-2}"
fi
("$PY" -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers "${WORKERS}" & echo $! > .api_pid)