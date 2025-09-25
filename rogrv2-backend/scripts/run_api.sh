#!/usr/bin/env bash
set -euo pipefail
PY="$(bash scripts/_python_bin.sh)"
"$PY" -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2