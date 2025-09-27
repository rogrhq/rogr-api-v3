#!/usr/bin/env bash
set -euo pipefail
# One-shot: install deps, start API, wait ready, quick ping.
export PY="$(bash scripts/_python_bin.sh)"
bash scripts/_install_deps.sh
bash scripts/_start_api_bg.sh || true
bash scripts/_wait_ready.sh
curl -sS "${BASE:-http://localhost:8000}/health/ready"
echo