#!/usr/bin/env bash
set -euo pipefail
: "${AUTH_JWT_SECRET:=dev-secret-$(date +%s)}"
PY="$(bash scripts/_python_bin.sh)"
# Single worker to keep in-memory job state consistent during tests
("$PY" -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 & echo $! > .api_pid)