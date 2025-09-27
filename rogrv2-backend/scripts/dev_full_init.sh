#!/usr/bin/env bash
set -euo pipefail
bash scripts/_stop_api_bg.sh || true
bash scripts/_start_api_bg.sh
echo -n "Health: "
curl -fsS "http://localhost:${API_PORT:-8000}/health/ready"
echo
[ -x scripts/check_live_keys.sh ] && bash scripts/check_live_keys.sh || true