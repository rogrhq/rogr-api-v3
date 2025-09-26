#!/usr/bin/env bash
set -euo pipefail
# Load test env if present, then set safe defaults
[ -f ".env.test" ] && set -a && . ./.env.test && set +a
: "${AUTH_JWT_SECRET:=dev-secret-$(date +%s)}"
: "${DATABASE_URL:=sqlite+aiosqlite:///$PWD/rogr_dev.db}"
export AUTH_JWT_SECRET
export DATABASE_URL
PY="$(bash scripts/_python_bin.sh)"
# Single worker to keep in-memory job state consistent during tests
("$PY" -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 & echo $! > .api_pid)