#!/usr/bin/env bash
set -euo pipefail
: "${AUTH_JWT_SECRET:=dev-secret-$(date +%s)}"
PY="$(bash scripts/_python_bin.sh)"
("$PY" -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 & echo $! > .api_pid)