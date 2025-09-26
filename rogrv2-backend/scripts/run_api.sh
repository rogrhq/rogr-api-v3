#!/usr/bin/env bash
set -euo pipefail
PY="$(bash scripts/_python_bin.sh)"
DBURL="${DATABASE_URL:-}"
if [[ "$DBURL" == sqlite+aiosqlite* ]]; then
  WORKERS=1
else
  WORKERS="${APP_WORKERS:-2}"
fi
"$PY" -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers "${WORKERS}"